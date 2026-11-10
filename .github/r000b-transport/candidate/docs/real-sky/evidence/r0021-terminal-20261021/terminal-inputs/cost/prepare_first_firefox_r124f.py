"""Prepare only the never-run Firefox resource row; no second Chromium repeat."""
from pathlib import Path
import ast,hashlib,json
C=Path(__file__).resolve().parent
source=C/'run_resources_r124.py';out=C/'run_resources_r124f.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='25d75adb471490bdd50f13a9117eaf543f2ca58bf6e0857e032c786058f0eb48'
text=source.read_text(encoding='utf-8')
for old,new in {
 "runs/resources-r124'":"runs/resources-r124f'",
 "for engine in ['chromium','firefox']:":"for engine in ['firefox']:",
 "state.get('moon',{}).get('status')":"(state.get('moon') or {}).get('status')",
 "state.get('sky',{}).get('status')":"(state.get('sky') or {}).get('status')",
 "state.get('moon',{}).get('errors')":"(state.get('moon') or {}).get('errors')",
 "state.get('sky',{}).get('errors')":"(state.get('sky') or {}).get('errors')",
 "len(record['slots'])==2":"len(record['slots'])==1",
 "r124-INPUTS.json":"r124f-INPUTS.json",
 "r124-ADMISSION.json":"r124f-ADMISSION.json",
 "f.write('resources-r124')":"f.write('resources-r124f')",
 "lock.read_text()=='resources-r124'":"lock.read_text()=='resources-r124f'",
 "One diagnosed Chromium resource repeat and first Firefox resource sequence.":"First and only Firefox resource sequence; Chromium repeat is exhausted.",
 "One Chromium day resource repeat after diagnosed first-image observer failure; first Firefox day resource case. No ordinary event repeats. Original per-owner cycles, native decode, limits and source remain unchanged. Single continuation acquisition-repeat allowance consumed at launch.":"Only the original never-run Firefox resource row. Retain r123/r124 acquisition failures and completed Cpreview evidence. Null not-yet-loaded sky is pending, never product PASS/failure. No Chromium or ordinary-event rerun; no repeats remain."
}.items():
 assert old in text,old
 text=text.replace(old,new)
ast.parse(text);assert not out.exists();out.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'status':'PREPARED_ONLY'}))
