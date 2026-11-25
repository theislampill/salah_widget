#!/usr/bin/env python3
"""Assemble owner-private, hash-checked P1 sheets and cross-cell measurements."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import math
from PIL import Image, ImageDraw

NAMES = ["B0", "B0-T", "B1c", "B1c-T", "B4", "B4-T", "B6", "B6-T"]
LABELS = NAMES + ["reference", "physical +20"]
TIERS = ("initial", "refined")


def read_images(directory, report):
    images = {}
    for key, capture in report["captures"].items():
        file = directory / (key + ".png")
        if file.parent != directory or hashlib.sha256(file.read_bytes()).hexdigest() != capture["sha256"]:
            raise ValueError("missing or mismatched capture " + str(file))
        images[key] = (file, capture)
    return images


def sheet(out, title, panels, scale, full=False):
    blocks, hashes = [], []
    for label, (image_path, meta) in panels:
        with Image.open(image_path) as source:
            im = source.convert("RGB")
        if not full:
            disc = meta["state"]["disc"]
            ratio = im.width / 325
            cx, cy, radius = (disc[k] * ratio for k in ("cx", "cy", "r"))
            box = tuple(round(n) for n in (cx - 1.08 * radius, cy - 1.08 * radius,
                                           cx + 1.08 * radius, cy + 1.08 * radius))
            im = im.crop(box)
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
        blocks.append((label, im))
        hashes.append({"label": label, "file": image_path.name, "sha256": meta["sha256"]})
    w = max(im.width for _, im in blocks)
    h = max(im.height for _, im in blocks)
    image = Image.new("RGB", (len(blocks) * w, h + 35), "#18202a")
    draw = ImageDraw.Draw(image)
    for j, (label, im) in enumerate(blocks):
        image.paste(im, (j * w + (w - im.width) // 2, 22))
        draw.text((j * w + 2, 4), label, fill="white")
    image.save(out / (title + ".png"))
    (out / (title + ".json")).write_text(json.dumps({"panels": hashes, "scale": scale,
        "sampling": "native device pixels; nearest-neighbour at 3x"}, indent=2) + "\n")
    return title


def adjudicate(rows, thresholds):
    """Preserve unmeasurable quantities and owner inputs independently."""
    floor, ceiling, margin = thresholds
    results, motion_pairs, tracks, repetitions, inhibited = [], {}, {}, [], []
    for key, (report, _) in rows.items():
        cell=report["cell"]
        pairs={p["label"]:p for p in report["pairs"]}
        if cell["group"]=="ineligible":
            inhibited.append({"cell":key,"treatments":NAMES,"forbiddenLightObserved":False})
        if cell["group"] in ("strap","buckle"):
            repetitions.append({"cell":key,"treatments":report["metrics"]})
        for sample in report["metrics"]:
            if "sequence" in sample:
                motion_pairs[(key[0],cell["fraction"],sample["name"],cell["motion"])]=sample
                results.append({"cell":key,"name":sample["name"],"DB3":sample["nativeDB3"],"controlledTimeDB3":sample["controlledDB3"]})
                continue
            if "tier" not in sample:
                continue
            if "metrics" not in sample:
                results.append({"cell":key,"name":sample["name"],"tier":sample["tier"],"status":"INCONCLUSIVE","reason":sample.get("reason")})
                continue
            m=sample["metrics"]
            f=cell["fraction"]
            l=m.get("deltaLitSkyL")
            d=m.get("deltaPhysicalCandidateL")
            q=sample["aperture"]
            stable=sample["repeatStable"]
            lit=q["lit"] and stable["lit"]
            dark_ok=q["dark"] and stable["dark"]
            sky=lit and q["sky"] and stable["sky"]
            candidate, ref, base=(sample["terrain"][s] for s in ("candidate","physical","base"))
            cv, refcv=candidate["litCV"],ref["litCV"]
            dark, basedark=candidate["darkSdL"],base["darkSdL"]
            term=sample.get("terminator")
            occ=sample.get("occlusion")
            ratio=occ["candidate"]["maxOverMedian"] if occ else None
            ref_ratio=occ["reference"]["maxOverMedian"] if occ else None
            # The reference supplies its range. Preserve values when the dark
            # mask/hidden star field cannot identify the comparison.
            frames=report["captures"]
            s=frames[sample["tag"]]["state"]
            no_outside=pairs[sample["pair"]]["outside"]==0
            repeated=pairs[sample["envelope"]]
            matched=bool(lit and dark_ok and term and term["matched"])
            complete=matched and not term["ambiguous"] and not term["missing"]
            crossing=False if matched and term["max"]>1 else (term["mean"]<=.25 if complete else None)
            verdict={"cell":key,"name":sample["name"],"tier":sample["tier"],
                 "legibilityFloorMet":l>=floor if floor is not None and f>=.04 and sky and l is not None else None,
                 "legibilityCeilingMet":l<=ceiling if ceiling is not None and f>=.04 and sky and l is not None else None,
                 "D2":d>=margin if margin is not None and f>.02 and lit and cell["alt"]<=-2 and d is not None else None,
                 "qualifiedApertures":{"lit":lit,"dark":dark_ok,"sky":sky},"referenceMaskIdentifiable":q["lit"] if f>.02 else None,
                 "F-INV-2-zeroOutside":no_outside if repeated.get("outside")==0 else None,
                 "F-INV-3": {"candidateMaxMedianRatio":ratio,"referenceMaxMedianRatio":ref_ratio,
                     "noCoincidentPeak":not occ["candidate"]["starCoincidences"] if dark_ok and occ and occ["candidate"]["hiddenPeaks"] and ratio is not None else None},
                 "F-INV-4-cv":abs(cv/refcv-1)<=.1 if lit and cv is not None and refcv is not None and refcv>0 else None,
                 "F-INV-4-darkStd":dark>=basedark if dark_ok and dark is not None and basedark is not None else None,
                 "F-INV-5-crossings":crossing,
                 "F-INV-5-observedMax":term["max"] if matched else None,
                 "F-INV-5-allRowMean":term["mean"] if complete else None,
                 "F-LEG-4-cloudBytesEqual":sample["cloudMatch"] if sample["cloudRepeatStable"] else None,
                 "DB1":sample.get("db1") if lit else None,"nativeUp":s.get("up"),"lightEligible":(s.get("light") or {}).get("eligible"),
                 "apertureDisposition":"qualified" if lit and dark_ok and sky else "inconclusive for affected aperture(s)"}
            results.append(verdict)
            if cell["group"]=="horizon" and sample["tier"]=="refined" and lit and m.get("litMeanY") is not None:
                y=m["litMeanY"]
                light=116*y**(1/3)-16 if y>216/24389 else 24389/27*y
                k=(key[0],key[1],f,sample["name"])
                tracks.setdefault(k,{})[cell["alt"]]=light
    transitions=[]
    for key,points in tracks.items():
        ordered=sorted(points.items())
        transitions.append({"cell":key,"count":len(points),"monotone":all(b[1]>=a[1] for a,b in zip(ordered,ordered[1:])) if len(points)==17 else None,
                            "minus2ToMinus1L":points[-1]-points[-2] if -2 in points and -1 in points else None})
    motion=[]
    for (engine,frac,name,mode),a in motion_pairs.items():
        if mode!="reduce":
            continue
        b=motion_pairs.get((engine,frac,name,"no-preference"))
        def geometry(s):
            # Replay verifies the actual producer instant, ramp and projected
            # footprint in every registration before these enter the assembler.
            return [v["registration"] for v in s["sequence"]]
        observed=a["observerGeometry"]
        counterpart=b["observerGeometry"] if b else []
        motion.append({"engine":engine,"fraction":frac,"name":name,
            "controlledReducedMotionSameGeometry":geometry(a)==geometry(b) if b else None,
            "observerRequestedMinutesMatch":[p["utcMs"]//60000 for p in observed]==[p["utcMs"]//60000 for p in counterpart] if b else None,
            "observerSameRenderedFootprints":all((p["transform"],p["disc"])==(q["transform"],q["disc"]) for p,q in zip(observed,counterpart,strict=True)) if b else None,
            "observerCommonInstantCount":sum(p["utcMs"]==q["utcMs"] for p,q in zip(observed,counterpart,strict=True)) if b else None})
    return {"cells":results,"horizon":transitions,"motionModes":motion,"repetitions":repetitions,"inhibited":inhibited}


def angle_controls(groups):
    arms={}
    for (engine,dpr,_),(r,_) in groups.items():
        c=r["cell"]
        if c["group"]!="strap" or c["mode"] not in ("hour-min","hour-max"):
            continue
        arms.setdefault((engine,dpr,c["weather"],c["fraction"]),{})[c["mode"]]=r
    results=[]
    for key,arm in arms.items():
        observed=[]
        if len(arm)==2:
            for tag,low in arm["hour-min"]["captures"].items():
                high=arm["hour-max"]["captures"][tag]
                for selector in (".moccluder",".moon-detail-canvas"):
                    a,b=(v["boxes"][selector] for v in (low,high))
                    observed.append(b["x"]-a["x"] if min(a["w"],a["h"],b["w"],b["h"])>0 else None)
        passed=bool(observed) and all(x is not None and abs(x-3)<1.1 for x in observed)
        results.append({"cell":key,"verified":passed,"pairedFootprintCount":len(observed),"minDx":min(observed) if observed and None not in observed else None,"maxDx":max(observed) if observed and None not in observed else None})
    return results


def collect(root, out, thresholds=(None,None,None)):
    out.mkdir(mode=0o700, exist_ok=False)
    groups, physical, by_scene, spread, missing, result = {}, {}, {}, {}, [], []
    build_pins = {}
    files=sorted(root.rglob("summary.json"))
    replay=Path(__file__).with_name("r003f_receipt.cjs")
    errors=json.loads(subprocess.run(["node",str(replay)],input=json.dumps([str(f.resolve()) for f in files]),
        text=True,capture_output=True,check=True).stdout)
    for file,error in zip(files,errors,strict=True):
        if error is not None:
            missing.append({"file":str(file.relative_to(root)),"reason":error})
            continue
        r=json.loads(file.read_text())
        c=r["cell"]
        for b in r["builds"]:
            if build_pins.setdefault(b["variant"], b) != b:
                raise ValueError("mixed candidate builds: " + b["variant"])
        key = (r["engine"], r["dpr"], c["id"])
        if c["group"] in ("strap","buckle","ineligible","motion"):
            images={}
            if c["mode"] in ("hour-min","hour-max"):
                r["captures"]={tag:{"boxes":{k:v["boxes"][k] for k in (".moon-detail-canvas",".moccluder")}} for tag,v in r["captures"].items()}
            else:
                r["captures"]={}
            r.pop("streams",None)
        else:
            for m in r["captures"].values():
                m["state"]={k:m["state"].get(k) for k in ("disc","up","light")}
                for field in ("after","document","boxes","admission"):
                    m.pop(field,None)
            images=read_images(file.parent,r)
        r.pop("artifacts",None)
        if key in groups:
            raise ValueError("duplicate cell " + str(key))
        groups[key] = (r, images)
        if c["group"] == "physical":
            physical[(r["engine"], r["dpr"], c["fraction"], c["waxing"])] = images
        for entry in r["metrics"]:
            if "tier" not in entry:
                continue
            m = entry["metrics"]
            coords = (c["id"], entry["tier"], entry["name"])
            if entry["aperture"]["sky"] and all(entry["repeatStable"][a] for a in ("lit","sky")):
                spread.setdefault(coords, []).append([r["engine"], r["dpr"], m["deltaLitSkyL"]])
                by_scene[(key, entry["name"], entry["tier"])] = m
    # Count wholly absent receipts as well as failed and partial runs.
    grid = Path(__file__).with_name("r003f_matrix.cjs")
    expected=set()
    expected_spreads={}
    for engine in ("chromium","firefox","webkit"):
        for dpr in (1,2):
            cells=json.loads(subprocess.check_output(["node",str(grid),"--list","--engine",engine,"--dpr",str(dpr)]))
            expected.update((engine,dpr,c["id"]) for c in cells)
            for c in cells:
                if c["group"] in ("ineligible","motion","buckle","strap") or c["fraction"]<=.02:
                    continue
                for tier in TIERS:
                    for name in NAMES:
                        expected_spreads.setdefault((c["id"],tier,name),[]).append((engine,dpr))
    absent=sorted(expected-set(groups))
    for key, (r, images) in groups.items():
        c = r["cell"]
        if c["group"] not in {"phase", "owner", "weather", "horizon"}:
            continue
        for tier in TIERS:
            pairs = []
            for name in NAMES:
                item = images.get(name + "-" + tier)
                if item:
                    pairs.append((name, item))
            p = physical.get((r["engine"], r["dpr"], c["fraction"], c["waxing"]), {})
            physical_name = "b0-" + tier
            if "reference" in images:
                pairs.append(("reference", images["reference"]))
            if c["group"]=="phase" and physical_name in p:
                pairs.append(("physical +20", p[physical_name]))
            labels=LABELS if c["group"]=="phase" else LABELS[:-1]
            if [x[0] for x in pairs] != labels:
                missing.append([*key, tier, "missing required build or reference"])
                continue
            title = "-".join(map(str, (*key, tier)))
            for multiplier in (1, 3):
                result.append(sheet(out, title + "-crop-" + str(multiplier) + "x", pairs, multiplier))
            if c["group"] in {"owner", "weather"}:
                result.append(sheet(out, title + "-cards", pairs, 1, full=True))
    # Include temporal altitude strips for each rule with phase order preserved.
    horizon = {}
    for key, (r, images) in groups.items():
        c = r["cell"]
        if c["group"] == "horizon":
            horizon.setdefault((key[0], key[1], c["fraction"], c["waxing"]), {})[c["alt"]] = images
    alts = [-30,-6,-4,-3,-2,-1.5,-1,-.5,0,1,2,3,4,6,10]
    for key, records in horizon.items():
        for name in NAMES:
            if not all(name + "-refined" in records.get(a, {}) for a in alts):
                missing.append([*key, name, "incomplete transition strip"])
                continue
            panels = [(str(a) + " deg", records[a][name + "-refined"]) for a in alts]
            result.append(sheet(out, "-".join(map(str, (*key, name, "transition"))), panels, 1))
    differences = []
    for key,(r,_) in groups.items():
        if r["cell"]["fraction"]<=.02 or r["cell"]["group"] in ("ineligible","motion","buckle","strap"):
            continue
        for name in NAMES:
            values=[by_scene.get((key,name,t),{}).get("deltaLitSkyL") for t in TIERS]
            delta=values[1]-values[0] if None not in values else None
            differences.append({"cell":key,"name":name,"refinedMinusInitialL":delta,
                                "withinHalfL":abs(delta)<=.5 if delta is not None else None})
    spreads=[]
    for key,participants in sorted(expected_spreads.items()):
        values=spread.get(key,[])
        if not values and not any((eng,dpr,key[0]) in groups for eng,dpr in participants):
            continue
        unavailable=sorted(set(participants)-{(v[0],v[1]) for v in values})
        spreads.append({"cell":key,"measurements":values,"unqualifiedOrAbsent":unavailable,
                        "complete":not unavailable,"min":min((i[2] for i in values),default=None),
                        "max":max((i[2] for i in values),default=None)})
    angles=angle_controls(groups)
    missing.extend(x for x in angles if not x["verified"])
    receipt = {"program":"R003F/private-sheets/2","G-F0":"OPEN — acquisition and row measurements only","hourAngleControls":angles, "measuredCellCount":len(groups), "builds":build_pins,
               "sheets":result, "thresholds":dict(zip(("F_L","F_U","M_D"),thresholds)), "adjudication":adjudicate(groups,thresholds), "absentCells":absent, "incomplete":missing, "tierDifferences":differences,
               "spreads":spreads}
    (out / "sheets.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    for flag in ("floor","ceiling","margin"):
        parser.add_argument("--"+flag,type=float,help="optional owner-recorded "+flag)
    args=parser.parse_args()
    if any(v is not None and not math.isfinite(v) for v in (args.floor,args.ceiling,args.margin)):
        parser.error("threshold must be finite")
    r=collect(args.reports.resolve(),args.out.resolve(),(args.floor,args.ceiling,args.margin))
    print(json.dumps({"sheets":len(r["sheets"]),"incompleteGroups":len(r["incomplete"])}))
    raise SystemExit(0 if r["sheets"] and not r["incomplete"] and not r["absentCells"] else 2)
