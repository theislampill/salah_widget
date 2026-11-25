"""Synthetic end-to-end calibration. No native or participant data; ephemeral keys and frames."""
import copy, importlib.util, io, json, os, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
import numpy as np
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from lossless_pack import canonical,digest,inspect,manifest
from pack_design import CONDITIONS,DESIGNS,EFFECTIVE,PROFILE,expected_held,treatments


def tool(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def rejected(fn,fragment):
    try:fn()
    except (ValueError,KeyError) as exc:
        assert fragment in str(exc),exc
    else:raise AssertionError("accepted "+fragment)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        pins={k:digest(("independent synthetic "+k).encode()) for k in ("productSha","rendererSha","geometrySha")}
        pins["options"]=None
        pins["evidenceClass"]="synthetic-calibration"
        pinfile=root/"pins.json";pinfile.write_bytes(canonical(pins))
        private=Ed25519PrivateKey.generate();sk=root/"private.pem";pk=root/"public.pem"
        sk.write_bytes(private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        pk.write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
        base=root/"reference.png";Image.new("RGB",(325,530)).save(base)
        stripe=root/"stripe.png";a=np.zeros((530,325,3),dtype="uint8");a[:,::2]=255;Image.fromarray(a).save(stripe)
        geometry={"card":[0,0,325,530],"header":[0,0,325,32],"footer":[0,503,325,27],
                  "rows":[[12,110+35*i,300,30] for i in range(6)],"glass":"blur(6px)"}
        rects=[{"name":n,"x":12,"y":12+20*i,"w":10,"h":8} for i,n in enumerate(sorted(tool("paired-readability").NAMES))]
        date={"bday":("solar-noon",1790154360000),"bwind":("solar-noon",1790154360000),"btwi":("blue-hour",1790177760000),
              "bmoon":("night-early",1790181360000),"bdark":("night-early",1789145460000)}
        def create(folder,design,block,condition,model,treatment,count=181,image=base):
            folder.mkdir();clock="browser-native-epoch-ms";epoch=1700000000000;code,amount=CONDITIONS[condition]
            state=dict(code=code,amount=amount,interval=900,source="current",permission="on" if amount else "off")
            tup=[code,amount,900,state["permission"],"off" if model=="current" else model,"immediate",100,1/60,
                 amount*4 if amount and model!="current" else None]
            frames=[];states=[];sha=digest(image.read_bytes());held=expected_held(block)
            for i in range(count):
                file=f"f{i:05}.png";os.link(image,folder/file);ts=epoch+i*1000/60
                frames.append(dict(file=file,t=ts,acquisitionMs=0,auditIndex=i,sha256=sha))
                states.append(dict(at=ts,phaseMs=i*1000/60,poseMs=i*1000/60,geometry=geometry,rects=rects,treatment=treatment,tuple=tup))
            scene,utc=date[block]
            log=dict(**pins,design=design,treatment=treatment,dispersion=None if design=="historical" else treatment,
                     engine="chromium",block=block,model=model,condition=condition,method="compositor-png",clock=clock,
                     utcMs=utc,scene=scene,held=held,wx={**held,"code":code,"precip":amount,"rain":0 if condition=="showers" else amount,
                     "showers":amount if condition=="showers" else 0},light=dict(sun=60 if block in ("bday","bwind") else -5 if block=="btwi" else -19,
                     moon=1 if block=="bmoon" else 0,moonAltitude=30 if block=="bmoon" else -30,moonFresh=True),
                     before=state,after=state,geometry=geometry,rects=rects,effective=EFFECTIVE,profile=PROFILE,
                     audit=dict(clock=clock,states=states),frames=frames)
            path=folder/"capture.json";path.write_bytes(canonical(log));return path
        control=create(root/"control","revised","bdark","dry","M2","diameter")
        original=json.loads(control.read_bytes());inspect(control,pins=pins)
        def changed(edit,reason):
            v=copy.deepcopy(original);edit(v);control.write_bytes(canonical(v));rejected(lambda:inspect(control,pins=pins),reason)
        for edit,reason in [
            (lambda v:(v["held"].update(wind=99),v["wx"].update(wind=99)),"held atmosphere"),
            (lambda v:v.update(held={}),"held atmosphere"),(lambda v:v.update(productSha="x"),"source digest"),
            (lambda v:v.update(rendererSha="0"*64),"source/option pin"),(lambda v:v.update(profile={}),"gain profile"),
            (lambda v:v.update(evidenceClass="native-controlled-capture"),"source/option pin"),
            (lambda v:v.update(engine="firefox"),"engine/method"),(lambda v:v["audit"].update(states=v["audit"]["states"][:1]),"temporally matched"),
            (lambda v:[x.update(at=x["at"]+500000) for x in v["audit"]["states"]],"temporally matched"),
            (lambda v:v["frames"][1].update(auditIndex=0),"audit association"),
            (lambda v:v["frames"][2].update(t=v["frames"][1]["t"]+22),"dropped"),
            (lambda v:v["light"].update(moon=.1),"illumination"),(lambda v:v["before"].update(amount=1),"admission"),
            (lambda v:v["audit"]["states"][2].update(treatment="common"),"runtime treatment"),
            (lambda v:[s.update(phaseMs=25) for s in v["audit"]["states"]],"scene phase does not advance"),
            (lambda v:v["audit"]["states"][90].update(phaseMs=0),"scene phase rewound"),
            (lambda v:v.update(utcMs=0),"scene/clock")]:
            changed(edit,reason)
        control.write_bytes(canonical(original));frame=control.parent/"f00000.png";frame.unlink();Image.new("RGB",(325,530)).save(frame,compress_level=1)
        rejected(lambda:inspect(control,pins=pins),"capture bytes changed");frame.unlink();os.link(base,frame)
        wet=create(root/"wet-motion","revised","bday","moderate","M1","common")
        wet_original=wet.read_bytes();inspect(wet,pins=pins)
        for edit,reason in [
            (lambda v:[s.update(poseMs=0) for s in v["audit"]["states"]],"pose stale or frozen"),
            (lambda v:v["audit"]["states"][90].update(poseMs=0),"pose rewound")]:
            v=json.loads(wet_original);edit(v);wet.write_bytes(canonical(v));rejected(lambda:inspect(wet,pins=pins),reason)
        wet.write_bytes(wet_original)
        # Real PNGs drive the paired G1/G2 and P1 analyses. One 95/30 ratio is 21, uniform scenes yield 1.
        pair=tool("paired-readability");paths=[]
        for i,(condition,model,image) in enumerate([("moderate","M2",stripe),("moderate","current",base),("dry","M2",base),("dry","current",base)]):
            paths.append(create(root/f"paired{i}","revised","bday",condition,model,"diameter" if model=="M2" else "common",3,image))
        result=pair.paired(paths,"readability");assert all(abs(x["mean"]-20)<1e-8 for x in result["regions"].values())
        assert pair.paired(paths[2:],"dry",pins)["matchedDryFrames"]==3
        assert pair.paired(paths[:2],"geometry",pins)["matchedFrames"]==3
        rejected(lambda:pair.paired([paths[3],paths[3]],"dry",pins),"distinct current reference")
        path=paths[3];old=path.read_bytes()
        def pairmut(edit,reason):
            v=json.loads(old);edit(v);path.write_bytes(canonical(v));rejected(lambda:pair.paired(paths,"readability"),reason)
        pairmut(lambda v:v["audit"]["states"][0]["rects"].pop(),"text regions")
        pairmut(lambda v:v["audit"]["states"][0]["rects"][0].update(x=24),"shifted")
        pairmut(lambda v:v["audit"]["states"][0].update(phaseMs=50),"scene phase rewound")
        pairmut(lambda v:v["audit"]["states"][1]["geometry"].update(glass="none"),"geometry mismatch")
        path.write_bytes(old)
        f=path.parent/"f00000.png";f.unlink();os.link(stripe,f);v=json.loads(old);v["frames"][0]["sha256"]=digest(stripe.read_bytes());path.write_bytes(canonical(v))
        rejected(lambda:pair.paired(paths[2:],"dry",pins),"dry full-card pixels changed")
        # Each complete inventory goes through the real signer, exporter and scorer; no mocked verifier.
        for design in DESIGNS:
            pack=root/design;pack.mkdir()
            for i,(_,b,c,m,t) in enumerate(sorted(treatments(design,("chromium",)))):create(pack/str(i),design,b,c,m,t)
            path=pack/"0"/"capture.json";original_path=path.with_suffix(".held");path.rename(original_path)
            rejected(lambda:manifest(pack,("chromium",),design,pins),"incomplete");original_path.rename(path)
            cmd=[sys.executable,str(Path(__file__).with_name("lossless_pack.py"))]
            common=[str(pack),"--engine","chromium","--design",design,"--pins",str(pinfile),"--key"]
            subprocess.run(cmd+["sign",*common,str(sk)],check=True)
            subprocess.run(cmd+["verify",*common,str(pk)],check=True)
            media=root/("media-"+design);sealed=root/("key-"+design)
            tool("blind-material").prepare(pack,"chromium",pk,media,sealed,design,pins,sk)
            key=json.loads((sealed/"key.json").read_bytes());signed=json.loads((pack/"signed-manifest.json").read_bytes())
            # Retain the exported commitment before fabricating the answer sheet.
            # Scoring cannot replace it with one supplied alongside a changed key.
            commitment=json.loads((media/"mapping-commitment.json").read_bytes())
            assert canonical(commitment)==(sealed/"mapping-commitment.json").read_bytes()
            rows=[dict(blindId=c["blindId"],participant=str(i),recognition="cannot tell",naturalness="3") for i in range(5) for c in key["cells"]]
            score=tool("score-blind").score
            result=score(key,rows,signed,private.public_key(),design,commitment)
            assert len(result)==5*len(key["cells"])
            assert {r["evidenceClass"] for r in result}=={"synthetic-calibration"}
            forged=copy.deepcopy(key)
            a=next(c for c in forged["cells"] if c["condition"]=="dry")
            b=next(c for c in forged["cells"] if c["condition"]=="drizzle" and c["block"]==a["block"] and c["model"]==a["model"] and c["treatment"]==a["treatment"])
            a["blindId"],b["blindId"]=b["blindId"],a["blindId"]
            rejected(lambda:score(forged,rows,signed,private.public_key(),design,commitment),"blind mapping")
            if design=="revised":
                forged=copy.deepcopy(key);next(c for c in forged["cells"] if c["treatment"]=="diameter")["treatment"]="common"
                rejected(lambda:score(forged,rows,signed,private.public_key(),design,commitment),"blind mapping")
                # Even a custodian-signed invalid mapping cannot substitute a receipt.
                invalid=copy.deepcopy(commitment);invalid["commitment"]["mappingSha"]=digest(canonical(forged))
                invalid["signature"]=private.sign(canonical(invalid["commitment"])).hex()
                rejected(lambda:score(forged,rows,signed,private.public_key(),design,invalid),"substituted")
            print(design,len(key["cells"]),"synthetic cells signed, exported and scored")
        print("PASS synthetic capture, inventory, treatment, provenance, paired geometry, dry pixels, contrast, advancing clocks, sealed mapping and scoring controls")


if __name__=="__main__":
    main()
