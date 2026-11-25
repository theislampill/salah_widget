"""Verify each raw PNG against its capture, then sign a complete controlled pack. Keys stay external."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from PIL import Image
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


from pack_design import BLOCKS, CONDITIONS, DESIGNS, EFFECTIVE, ENGINES, PROFILE, expected_held, treatments
import bisect
import re


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()


def inspect(log_path, display_rate=True, pins=None, pixel_cache=None):
    log = json.loads(log_path.read_bytes())
    cell = tuple(log[k] for k in ("engine", "block", "condition", "model"))
    engine, block, condition, model = cell
    design=log.get("design");treatment=log.get("treatment")
    require(log.get("evidenceClass") in ("native-controlled-capture","synthetic-calibration"),"missing evidence class")
    require(design in DESIGNS and engine in ENGINES and block in BLOCKS and condition in CONDITIONS and
            (model,treatment) in DESIGNS[design] and log.get("dispersion")== (None if design=="historical" else treatment),"unknown or substituted treatment")
    for k in ("productSha","rendererSha","geometrySha"):
        require(isinstance(log.get(k),str) and re.fullmatch("[0-9a-f]{64}",log[k]),"invalid source digest "+k)
    require("options" in log,"missing option provenance")
    if pins is not None:
        for k in ("productSha","rendererSha","geometrySha","options","evidenceClass"):
            require(k in pins and pins[k]==log[k],"independent source/option pin mismatch: "+k)
    require(log["held"]==expected_held(block),"wrong held atmosphere or wind")
    require((engine=="chromium" and log["method"]=="compositor-png" and log["clock"]=="browser-native-epoch-ms") or
            (engine in ("firefox","webkit") and log["method"]=="bracketed-screen-png" and log["clock"]=="runner-monotonic-ms"),
            "wrong engine/method/timebase")
    cell=(*cell,treatment)
    code, amount = CONDITIONS[condition]
    state = dict(code=code, amount=amount, interval=900, source="current", permission="on" if amount else "off")
    require(log["before"] == state == log["after"], "admission or control mismatch")
    g=log["geometry"]
    boxes=[g.get("card"),g.get("header"),g.get("footer"),*g.get("rows",[])]
    require(len(g.get("rows",[]))==6 and isinstance(g.get("glass"),str) and g["glass"].strip() and
            all(isinstance(box,list) and len(box)==4 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in box)
                and box[2]>0 and box[3]>0 for box in boxes) and g["card"][2:]==[325,530],"card/header/footer/rows/glass geometry")
    require(log["wx"] == {**log["held"], "code": code, "precip": amount,
                          "rain": 0 if condition == "showers" else amount,
                          "showers": amount if condition == "showers" else 0}, "uncontrolled fixture")
    expectations={"bday":("solar-noon",1790154360000),"bwind":("solar-noon",1790154360000),
                  "btwi":("blue-hour",1790177760000),"bmoon":("night-early",1790181360000),
                  "bdark":("night-early",1789145460000)}
    require((log["scene"],log["utcMs"])==expectations[block],"wrong scene/clock for block")
    light=log["light"]
    require(all(isinstance(light[k],(float,int)) and math.isfinite(light[k]) for k in ("sun","moon","moonAltitude")),
            "missing measured illumination")
    require((block in ("bday","bwind") and light["sun"]>0) or
            (block=="btwi" and -12<light["sun"]<0) or
            (block=="bmoon" and light["sun"]< -12 and light["moonFresh"] and light["moonAltitude"]>0 and light["moon"]>0) or
            (block=="bdark" and light["sun"]< -12 and light["moonFresh"] and light["moon"]==0),
            "illumination contradicts block")
    audit=log["audit"]
    require(audit["clock"]==log["clock"] and audit["states"],"mismatched or empty audit clock")
    stamps=[s["at"] for s in audit["states"]]
    require(all(math.isfinite(v) for v in stamps) and all(a<b for a,b in zip(stamps,stamps[1:])),"audit timestamp order")
    for s in audit["states"]:
        require(s.get("treatment")==treatment and s.get("geometry")==log["geometry"] and
                all(isinstance(s.get(k),(float,int)) and math.isfinite(s[k]) for k in ("poseMs","phaseMs")),
                "runtime treatment, phase or geometry mismatch")
        raw, qty, interval, perm, active, policy, gain, exposure, rate = s["tuple"]
        require((raw,qty,interval,perm)==(code,amount,900,state["permission"]) and
                active==("off" if model=="current" else model) and policy=="immediate" and
                gain==100 and exposure==1/60 and rate==(None if model=="current" or not amount else amount*4),
                "source, authority or effective parameters changed during capture")
    phases=[s["phaseMs"] for s in audit["states"]]
    poses=[s["poseMs"] for s in audit["states"]]
    # The held scene is a fixed fixture evaluated at real speed, not a frozen
    # page clock. A frame/observer may execute up to two 60 Hz periods later
    # than its timestamp. This is a declared observation tolerance, not a
    # permission to synthesize frames or credit a paused renderer.
    tolerance=2*1000/60+2
    require(all(b>=a-1 for a,b in zip(phases,phases[1:])),"scene phase rewound")
    require(all(abs((phase-phases[0])-(at-stamps[0]))<=tolerance for phase,at in zip(phases,stamps)),
            "scene phase does not advance with capture time")
    if amount and model!="current":
        require(all(b>=a-1 for a,b in zip(poses,poses[1:])),"full-motion renderer pose rewound")
        require(all(abs((pose-poses[0])-(at-stamps[0]))<=tolerance for pose,at in zip(poses,stamps)),
                "full-motion renderer pose stale or frozen")
    p = log["effective"]
    require(p==EFFECTIVE and log["profile"]==PROFILE,"declared gain profile or physical parameters differ")
    require(p["enforceDeclaredGain"] is True and p["G"] == 100 and p["T"] == 1/60 and
            p["sunKernel"]["amp"] == p["moonKernel"]["amp"] == p["render"]["lineFloor"] == 0, "gain profile")
    require(all(p[k] == v for k, v in log["profile"].items()), "unapplied override")
    frames = log["frames"]
    times = [f["t"] for f in frames]
    require(times and all(math.isfinite(t) for t in times), "missing finite capture timestamps")
    require(all(a<b for a,b in zip(times,times[1:])),"frame order")
    used=set()
    for f in frames:
        t=f["t"]; idx=bisect.bisect_left(stamps,t)
        if log["method"]=="compositor-png":
            neighbors=[i for i in (idx-1,idx) if 0<=i<len(stamps)]
            i=min(neighbors,key=lambda j:abs(t-stamps[j]))
            require(abs(stamps[i]-t)<=8.5 and i not in used,"no unique temporally matched native frame audit")
            used.add(i)
            require(f["auditIndex"]==i,"incorrect audit association")
        else:
            i=f["auditIndex"]
            require(0<=i<len(stamps)-1 and stamps[i]<=t<=stamps[i+1] and all(0<=audit["states"][j].get("uncertaintyMs",-1)<=10 for j in (i,i+1)) and
                    abs((stamps[i+1]-stamps[i])-f["acquisitionMs"]-sum(audit["states"][j]["uncertaintyMs"] for j in (i,i+1)))<.1,
                    "unbracketed screenshot audit")
    if log["method"]=="compositor-png":
        require(0 in used and len(stamps)-1 in used,"unmatched audit window")
    if display_rate:
        require(len(times) >= 180 and all(math.isfinite(t) for t in times), "fewer than three seconds of frames")
        gaps = [b-a for a,b in zip(times,times[1:])]
        # One millisecond tolerance for compositor timestamp quantisation, never a substitute frame.
        require(all(0 < dt <= 1000/60+1 for dt in gaps), "dropped/out-of-order display frame")
        require(times[-1]-times[0] >= 3000-1000/60-1, "short capture")
        require(times[-1]-times[0] <= len(gaps)*1000/60+.1, "average below 60 fps")
    require({f["file"] for f in frames} == {p.name for p in log_path.parent.glob("*.png")}, "frame inventory")
    pixels = hashlib.sha256()
    for i,f in enumerate(frames):
        require(f["file"] == f"f{i:05}.png", "frame order")
        file = log_path.parent/f["file"]
        require(digest(file.read_bytes()) == f["sha256"], "capture bytes changed")
        frame_hash=f["sha256"]
        if pixel_cache is not None and frame_hash in pixel_cache:
            pixels.update(pixel_cache[frame_hash]);continue
        with Image.open(file) as im:
            require(im.format == "PNG" and im.size == (325,530) and im.n_frames == 1, "frame format")
            # Bind ordered decoded frame hashes without re-reading duplicate frames in a pack.
            decoded=hashlib.sha256(im.convert("RGBA").tobytes()).digest()
            pixels.update(decoded)
            if pixel_cache is not None and len(pixel_cache)<4096:pixel_cache[frame_hash]=decoded
    require(log["method"] in {"compositor-png","bracketed-screen-png"}, "unknown acquisition method")
    require(not display_rate or log["method"] == "compositor-png", "full-card lossless images available; display presentation timestamps unverified")
    return cell, log, {"log":digest(log_path.read_bytes()), "orderedRgbaHashes":pixels.hexdigest(), "n":len(times)}


def manifest(root, engines, design, pins):
    require(design in DESIGNS and pins is not None,"external pins and design required")
    cache={}
    cells, held, common = {}, {}, None
    for path in sorted(root.glob("*/capture.json")):
        cell, log, receipt = inspect(path,pins=pins,pixel_cache=cache)
        require(log["design"]==design,"mixed design")
        require(cell not in cells, "duplicate cell")
        cells[cell] = {"dir":path.parent.name, **receipt}
        metadata = [log["held"], log["utcMs"], log["scene"]]
        require(metadata == held.setdefault(cell[1],metadata), "scene confound")
        ids = [log[k] for k in ("productSha","rendererSha","geometrySha","effective","options","evidenceClass")]
        if common is None:
            common = ids
        require(common == ids, "source/parameters vary across pack")
    require(set(cells) == treatments(design,engines), "incomplete/extra cells in selected engine matrix")
    return {"schema":3,"evidenceClass":common[-1],"design":design,"pins":pins, "engines":list(engines), "parametersAndSources":common, "blocks":held,
            "cells":{"/".join(k):v for k,v in sorted(cells.items())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("cell","stills","sign","verify"))
    parser.add_argument("path",type=Path)
    parser.add_argument("--key",type=Path,help="separately retained Ed25519 private/public PEM for sign/verify")
    parser.add_argument("--engine", choices=ENGINES, help="sign/verify one named 180-cell engine pack; default requires all three")
    parser.add_argument("--design",choices=DESIGNS)
    parser.add_argument("--pins",type=Path,help="independent source and authored-option commitment, required for pack signing/verification")
    args = parser.parse_args()
    pins=json.loads(args.pins.read_bytes()) if args.pins else None
    if args.action in {"cell","stills"}:
        print(json.dumps({"evidence":args.action,"sourceAuthority":"external pins" if pins else "internal consistency only",**inspect(args.path,args.action=="cell",pins=pins)[2]}));return
    body = canonical(manifest(args.path,(args.engine,) if args.engine else ENGINES,args.design,pins))
    if args.action == "sign":
        key = serialization.load_pem_private_key(args.key.read_bytes(),password=None)
        require(isinstance(key,Ed25519PrivateKey),"Ed25519 private key required")
        with (args.path/"signed-manifest.json").open("x") as out:
            json.dump({"manifest":json.loads(body),"signature":key.sign(body).hex()},out,sort_keys=True)
    else:
        signed = json.loads((args.path/"signed-manifest.json").read_bytes())
        require(canonical(signed["manifest"]) == body,"published manifest differs from captures")
        key = serialization.load_pem_public_key(args.key.read_bytes())
        require(isinstance(key,Ed25519PublicKey),"Ed25519 public key required")
        key.verify(bytes.fromhex(signed["signature"]),body)
        print("Verified full pack and capture bytes against supplied public key.")


if __name__ == "__main__":
    main()
