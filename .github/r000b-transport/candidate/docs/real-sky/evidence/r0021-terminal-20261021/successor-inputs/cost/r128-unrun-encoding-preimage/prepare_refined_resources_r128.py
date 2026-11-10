"""Reuse the accepted observer and null-safe Firefox runner for missing Chromium owner only."""
from pathlib import Path
import ast,hashlib,json
C=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=C/'run_resources_r124.py';fixed=C/'run_resources_r124f.py'
def failure_condition(path):
 tree=ast.parse(path.read_text())
 nodes=[n.test for n in ast.walk(tree) if isinstance(n,ast.If) and "state.get('moon'" in ast.unparse(n.test) and "'unavailable'" in ast.unparse(n.test)]
 assert len(nodes)==1
 return compile(ast.Expression(nodes[0]),str(path),'eval')
bad=failure_condition(old);good=failure_condition(fixed)
controls=[]
for state,want in [({'moon':{},'sky':None},False),({'moon':None,'sky':None},False),({'moon':{'status':'unavailable'},'sky':None},True),({'moon':None,'sky':{'status':'unavailable'}},True),({'moon':{'status':'ready'},'sky':{'status':'ready'}},False)]:
 before=None
 try:before=eval(bad,{},dict(state=state))
 except AttributeError as e:before={'error':str(e)}
 after=eval(good,{},dict(state=state));assert after is want
 controls.append({'state':state,'prior':before,'corrected':after,'expectedFailure':want})
assert isinstance(controls[0]['prior'],dict)
out=C/'r128-NULL-OBSERVER-CONTROL.json';assert not out.exists()
out.write_text(json.dumps({'schema':'r0021-null-owner-observer-control/v1','scope':'Actual AST condition from retained runners; null remains pending, actual unavailable remains failure. No product/native qualification.','oldSha256':sha(old),'correctedSha256':sha(fixed),'controls':controls},indent=2)+'\n')

instrument=C/'instrument-r123.cjs';text=instrument.read_text()
for a,b in [('integrated-r30-owner-callbacks','integrated-r31-file-transport'),('instrumented-r123-reviewed','instrumented-r128')]:
 assert text.count(a)==1;text=text.replace(a,b)
p=C/'instrument-r128.cjs';assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')

text=fixed.read_text()
preview_start=text.index('        if resource:\n         await wait_for(')
preview_end=text.index('        await admitted_final()',preview_start)
preview=text[preview_start:preview_end]
assert 'previewCycles' in preview and 'previewDispose' in preview and 'release.set()' in preview
text=text[:preview_start]+"        if resource:slot['resources']['previewTransfer']='Accepted r124 preview; not repeated'\n"+text[preview_end:]
replacements={
 'First and only Firefox resource sequence; Chromium repeat is exhausted.':'Authorized successor: missing Chromium refined-owner sequence only.',
 'integrated-r30-owner-callbacks':'integrated-r31-file-transport',
 'instrumented-r123-reviewed':'instrumented-r128',
 "runs/resources-r124f'":"runs/resources-r128'",
 "for engine in ['firefox']:":"for engine in ['chromium']:",
 '3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821':'1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b',
 "if resource and urlsplit(u).path.endswith('/real-sky/native-sky.js'):await release.wait()":"# No module hold: only the missing refined owner is exercised.",
 "C/'instrument-r123.cjs'":"C/'instrument-r128.cjs'",
 'r124f-INPUTS.json':'r128-INPUTS.json','r124f-ADMISSION.json':'r128-ADMISSION.json',
 "f.write('resources-r124f')":"f.write('resources-r128')","lock.read_text()=='resources-r124f'":"lock.read_text()=='resources-r128'",
 'Only the original never-run Firefox resource row. Retain r123/r124 acquisition failures and completed Cpreview evidence. Null not-yet-loaded sky is pending, never product PASS/failure. No Chromium or ordinary-event rerun; no repeats remain.':'Only missing Chromium refined resource row. Null-safe predicate is independently controlled offline; accepted preview and both Firefox results transfer. No event campaign, new tolerance or changed decode semantics.'}
for a,b in replacements.items():
 assert a in text,a;text=text.replace(a,b)
text=text.replace("paths += [C/'resource-controls-r123.js'", "paths += [C/'r128-NULL-OBSERVER-CONTROL.json',C/'prepare_refined_resources_r128.py',C/'resource-controls-r123.js'")
ast.parse(text);p=C/'run_resources_r128.py';assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
(C/'r128-RUNNER-TRANSFER.json').write_text(json.dumps({'priorRunnerSha256':sha(fixed),'runnerSha256':sha(p),'priorInstrumenterSha256':sha(instrument),'instrumenterSha256':sha(C/'instrument-r128.cjs'),'nullControlSha256':sha(out),'changes':replacements,'removedPreviewBlockSha256':hashlib.sha256(preview.encode()).hexdigest(),'resourceControlsSha256':sha(C/'resource-controls-r124.js'),'scope':'Refined instance only; original three cycles, real decoder/cancellation/stale/settlement and terminal dispose controls unchanged.'},indent=2)+'\n')
print('r128 prepared; offline null controls passed; native not launched')
