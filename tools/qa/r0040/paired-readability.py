"""P1: historical 95th/30th luminance ratios. G1/G2: exact paired geometry and dry pixels."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
from lossless_pack import inspect, require

NAMES={"bigclock"}|{f"row{i}-{part}" for i in range(6) for part in ("label","time")}


def boxes(rects):
    chosen=[r for r in rects if r["name"] in NAMES]
    result={r["name"]:tuple(r[k] for k in ("x","y","w","h")) for r in chosen}
    require(len(chosen)==len(result) and set(result)==NAMES,"missing or duplicate expected text regions")
    for x,y,w,h in result.values():
        require(all(math.isfinite(v) for v in (x,y,w,h)) and min(x,y)>=0 and min(w,h)>0 and
                x+w<=325 and y+h<=530,"invalid text rectangle")
    return result


def sample(log,frame):
    return log["audit"]["states"][frame["auditIndex"]]


def align(logs):
    reference=logs[0]
    for log in logs:
        require(all(log[k]==reference[k] for k in ("utcMs","held","clock","method","engine","block")),
                "different site/time/method/held scene")
        require(len(log["frames"])==len(reference["frames"])>0,"frame coverage mismatch")
        for f,r in zip(log["frames"],reference["frames"]):
            s=sample(log,f);t=sample(reference,r)
            require(abs(s["phaseMs"]-t["phaseMs"])<=1 and abs(s["poseMs"]-t["poseMs"])<=1,
                    "unmatched simulated scene or overlay phase")
            # Sequential screenshots have an uncertain capture phase; reject extended brackets.
            require(f["acquisitionMs"]+2*max(s.get("uncertaintyMs",0),t.get("uncertaintyMs",0))<=2,"capture bracket too broad to compare phases")
            require(s["geometry"]==t["geometry"],"header/footer/rows/glass changed")
            require(boxes(s["rects"])==boxes(t["rects"]),"shifted/missing text rectangle")


def ratios(path,log):
    samples={name:[] for name in NAMES}
    for f in log["frames"]:
        with Image.open(path.parent/f["file"]) as image:rgb=np.asarray(image.convert("RGB"))/255
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        luminance=linear@np.array([.2126,.7152,.0722])
        for key,(x,y,w,h) in boxes(sample(log,f)["rects"]).items():
            low,high=np.percentile(luminance[int(y):int(y+h)+1,int(x):int(x+w)+1],[30,95])
            samples[key].append(float((high+.05)/(low+.05)))
    return {k:{"mean":float(np.mean(v)),"min":min(v)} for k,v in samples.items()}


def paired(paths,action,baseline_pins=None):
    rec=[inspect(path,False) for path in paths]
    logs=[v[1] for v in rec];align(logs)
    if action in ("geometry","dry"):
        require(len(rec)==2 and baseline_pins is not None,"two cells and independently pinned current baseline required")
        inspect(paths[1],False,pins=baseline_pins)
        a,b=logs
        require(b["model"]=="current" and a["condition"]==b["condition"] and
                (a["model"]!="current" or a["productSha"]!=b["productSha"] or a["options"]!=b["options"]),
                "candidate and distinct current reference required")
        if action=="geometry":return {"matchedFrames":len(a["frames"]),"geometry":"identical"}
        require(a["condition"]=="dry","two dry cells required")
        require(rec[0][2]["orderedRgbaHashes"]==rec[1][2]["orderedRgbaHashes"],"dry full-card pixels changed")
        return {"matchedDryFrames":len(logs[0]["frames"]),"geometry":"identical","decodedPixels":"identical"}
    require(len(rec)==4,"candidate/current wet and dry cells required")
    wet,reference,dry,dry_reference=[v[0] for v in rec]
    e,b,c,m,t=wet
    baseline="historical" if logs[0]["design"]=="historical" else "common"
    require(c!="dry" and m!="current" and reference==(e,b,c,"current",baseline) and dry==(e,b,"dry",m,t) and
            dry_reference==(e,b,"dry","current",baseline),"wrong comparison treatments")
    for log in logs[1:]:
        require(all(log[k]==logs[0][k] for k in ("design","productSha","rendererSha","geometrySha","options","effective")),
                "unmatched parameters or source")
    a,b,c,d=[ratios(p,l) for p,l in zip(paths,logs)]
    return {"metric":"linear luminance (p95 + .05)/(p30 + .05), historical rectangle indexing; paired wet minus dry drift",
            "regions":{k:{q:(a[k][q]-b[k][q])-(c[k][q]-d[k][q]) for q in ("min","mean")} for k in sorted(NAMES)}}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("action",choices=("geometry","dry","readability"))
    parser.add_argument("--reference-pins",type=Path);parser.add_argument("logs",type=Path,nargs="+");args=parser.parse_args()
    print(json.dumps(paired(args.logs,args.action,json.loads(args.reference_pins.read_bytes()) if args.reference_pins else None),indent=2))
