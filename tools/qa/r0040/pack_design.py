"""Declared inventories and independent fixture oracle for each experiment."""
import itertools
import json
from pathlib import Path
BLOCKS=("bday","bwind","btwi","bmoon","bdark")
CONDITIONS={"dry":(3,0),"drizzle":(53,.08),"light":(61,.3),"moderate":(63,1.25),"heavy":(65,3),"showers":(81,.75)}
ENGINES=("chromium","firefox","webkit")
DESIGNS={"historical":[(m,"historical") for m in ("current","M1","M2","M3","M4","M5")],
         "revised":[("current","common"),("M1","common"),("M2","common"),("M2","diameter"),("M3","common")]}
EFFECTIVE={p['name']:p['value'] for p in json.loads(Path(__file__).with_name("parameter-ledger.json").read_bytes())}
PROFILE={k:EFFECTIVE[k] for k in ("enforceDeclaredGain","G","T","frustumK","sunKernel","moonKernel","tile","render")}

def treatments(design,engines):
    return {(e,b,c,m,t) for e,b,c in itertools.product(engines,BLOCKS,CONDITIONS) for m,t in DESIGNS[design]}

def expected_held(block):
    windy=block=="bwind"
    return dict(cloud=85,low=75,mid=60,high=40,temp=60,hum=92,dew=55,vis=20000,
                wind=8 if windy else .3,wdir=270 if windy else 225,gust=9 if windy else .5)
