"""Prepare only five missing ordinary watches and two parents with one overlap."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
rels=['tools/cp9/celestial_startup_check.py','tools/cp9/chromium_startup_defaults.py','tools/cp9/celestial_lifecycle_check.py','tools/cp9/celestial_layer_controls.js','tools/cp9/browser_runtime.py','tools/cp9/runtime_identity.py','tests/v1_browser.py']
derivations=[]
for base,name in [(R,'visual-tools-r126'),(O/'moon-tools-r108','visual-tools-r126-exact')]:
 dest=O/name;assert not dest.exists()
 for rel in rels:
  p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((base/rel).read_bytes())
 p=dest/rels[0];original=p.read_text(encoding='utf-8');text=original
 if base==R:
  old=" if a.scene=='dawn':stamp='2026-09-25T10:40:00Z'"
  assert old in text
  text=text.replace(old,old+"\n if a.scene=='partial':stamp='2026-09-24T14:00:00Z'\n if a.scene=='twilight':stamp='2026-09-24T10:58:00Z'")
  text=text.replace("'dawn':(0,0)}","'dawn':(0,0),'twilight':(0,0)}")
  text=text.replace("'moon-negative','dawn']","'moon-negative','dawn','twilight']")
 old="   while time.monotonic()-start<a.duration:\n"
 assert text.count(old)==1
 text=text.replace(old,old+"    if (final.get('moon') or {}).get('status')=='unavailable' or (final.get('sky') or {}).get('status')=='unavailable':break\n")
 old="    if (final.get('moon') or {}).get('visibleSource')=='refined-terrain' and (final.get('sky') or {}).get('status')=='ready':break"
 assert text.count(old)==1
 text=text.replace(old,"    if (final.get('moon') or {}).get('current') and not (final.get('moon') or {}).get('pending') and (final.get('moon') or {}).get('visibleSource')=='refined-terrain' and (final.get('sky') or {}).get('status')=='ready' and not ((final.get('sky') or {}).get('lifecycle') or {}).get('pending'):break")
 ast.parse(text);p.write_text(text,encoding='utf-8',newline='\n')
 derivations.append({'base':str(base),'output':str(p),'beforeSha256':hashlib.sha256(original.encode()).hexdigest(),'afterSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Saved acquisition unchanged; named fixture only, plus stop on unavailable and require current admitted final. No profiler/tracing.'})
# Existing actual Chromium parent also supplies the ordinary positive-cloud watch.
p=O/'parent-tools-r125/tools/cp9/celestial_startup_check.py';text=p.read_text(encoding='utf-8')
old=" if a.scene=='dawn':stamp='2026-09-25T10:40:00Z'";assert text.count(old)==1
text=text.replace(old,old+"\n if a.scene=='partial':stamp='2026-09-24T14:00:00Z'")
old="    if (final.get('moon') or {}).get('visibleSource')=='refined-terrain' and (final.get('sky') or {}).get('status')=='ready':break";assert text.count(old)==1
text=text.replace(old,"    if (final.get('moon') or {}).get('current') and not (final.get('moon') or {}).get('pending') and (final.get('moon') or {}).get('visibleSource')=='refined-terrain' and (final.get('sky') or {}).get('status')=='ready' and not ((final.get('sky') or {}).get('lifecycle') or {}).get('pending'):break")
ast.parse(text);p.write_text(text,encoding='utf-8',newline='\n')
p=O/'parent/parent_fixture_r125.py';text=p.read_text(encoding='utf-8');assert text.count("STAMP='2026-09-25T02:00:00Z'")==1;text=text.replace("STAMP='2026-09-25T02:00:00Z'","STAMP='2026-09-24T14:00:00Z'");p.write_text(text,encoding='utf-8',newline='\n')
p=O/'parent/firefox_actual_widget_r125.py';text=p.read_text(encoding='utf-8')
for field in ['moon','sky']:text=text.replace("value.get('"+field+"',{})","(value.get('"+field+"') or {})")
ast.parse(text);p.write_text(text,encoding='utf-8',newline='\n')
(O/'intake/visual-parent-r125-r126-derivation.json').write_text(json.dumps(derivations,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PREPARED_ONLY','ordinaryWatches':5,'parentSequences':2,'overlap':1}))
