"""Derive only the diagnosed resource observer repeat; preserve all r123 bytes."""
from pathlib import Path
import ast,hashlib,json
C=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=C/'resource-controls-r123.js';new=C/'resource-controls-r124.js'
assert sha(old)=='eea8478a47153cd2ea1a29bba8835994793c4986cca88700ac77e2061082eb5e'
before='const imageRecord=image=>imageRecords.find(r=>r.id===imageId(image));'
after='const imageRecord=image=>{const id=imageId(image);return imageRecords.find(r=>r.id===id);};'
text=old.read_text(encoding='utf-8');assert text.count(before)==1 and not new.exists()
new.write_text(text.replace(before,after),encoding='utf-8',newline='\n')
original=C/'run_events_resources_r123.py';target=C/'run_resources_r124.py'
assert sha(original)=='8770295b1cf791d1c0fc9ad0926323d444501596588a193b1f3975db4fb5b2e5'
text=original.read_text(encoding='utf-8')
changes={
 '"""One finite Chromium actual-event group and one resource sequence per engine.':'"""One diagnosed Chromium resource repeat and first Firefox resource sequence.',
 "DEST=C/'runs/events-resources-r123'":"DEST=C/'runs/resources-r124'",
 "C/'resource-controls-r123.js'":"C/'resource-controls-r124.js'",
 "sequence=[(scene,side,False) for scene in SCENES for side in 'AB']+[('day','B',True)] if engine=='chromium' else [('day','B',True)]":"sequence=[('day','B',True)]",
 "len(record['slots'])==8":"len(record['slots'])==2",
 "r123-INPUTS.json":"r124-INPUTS.json",
 "r123-ADMISSION.json":"r124-ADMISSION.json",
 "events-resources-r123":"resources-r124",
 "Six ordinary Chromium night/twilight/day A/B events; separate one day B resource case per engine. One observation per slot; no steady ABBA. Resource interventions and observer-marked snapshot intervals are excluded from matched event comparisons. Minute/solar-geometry control is not a coordinate-target or DPR change.":"One Chromium day resource repeat after diagnosed first-image observer failure; first Firefox day resource case. No ordinary event repeats. Original per-owner cycles, native decode, limits and source remain unchanged. Single continuation acquisition-repeat allowance consumed at launch.",
}
for before,after in changes.items():
 assert before in text,before
 text=text.replace(before,after)
needle=" paths += [p for p in OVERLAY.rglob('*') if p.is_file()]"
assert text.count(needle)==1
text=text.replace(needle," paths += [C/'resource-controls-r123.js',C/'run_events_resources_r123.py',C/'resource-registration-r124.test.cjs',C/'r124-OBSERVER-CONTROL.json']\n"+needle)
ast.parse(text);assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'observer':sha(new),'runner':sha(target),'nativeExecuted':False}))
