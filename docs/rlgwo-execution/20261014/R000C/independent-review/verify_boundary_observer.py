"""Read-only identity and unchanged-oracle check for the observer-only pilot."""
from pathlib import Path
import ast,hashlib,json
OUT=Path(__file__).resolve().parent
EV=OUT.parent
ROOT=EV.parent/'salah_widget'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
old=EV/'fixture-v2/run_r000c_native.py'
new=ROOT/'tools/qa/run_r000c_native.py'
assert sha(old.read_bytes())=='c93c45cbde57704ee8a5f87ebd1b51d66dd0d33b0e232068b481a1ed7bcfc6d8'
assert sha(new.read_bytes())=='ed610a2ce09ebdfce661b563338d0cf31f89162676b9f03de40544f59e350737'
a,b=ast.parse(old.read_text(encoding='utf8')),ast.parse(new.read_text(encoding='utf8'))
def fn(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
def val(t,n):return next(x.value.value for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==n for y in x.targets))
for name in ['check','wait','tile_png','sha','dump']:
    assert ast.dump(fn(a,name),include_attributes=False)==ast.dump(fn(b,name),include_attributes=False),name
for name in ['READ','READY']:assert val(a,name)==val(b,name),name
passive=val(b,'RECOVERED_PASSIVE')
for prohibited in ['qaState','weatherDecision','atmosphere','model(','.surface(','.state','getImageData','fetchWeather']:
    assert prohibited not in passive,prohibited
for required in ['assertOwned(b.identity())','weather?.precip===2',".dataset.precip==='on'",'particles>0']:
    assert required in passive,required
assert 'full-diagnostic-boundaries-passive-recovery' in new.read_text(encoding='utf8')
for row in read(EV/'fixture-v2/manifest.json'):assert sha((EV/'fixture-v2'/row['copy']).read_bytes())==row['sha256']
previous=read(EV/'fixture-v2/R000C-cases.json');current=read(ROOT/'tests/rlgwo/R000C-cases.json')
previous['sourceFiles']['tools/qa/run_r000c_native.py']=current['sourceFiles']['tools/qa/run_r000c_native.py']
assert previous==current
for path,digest in current['sourceFiles'].items():assert sha((ROOT/path).read_bytes())==digest,path
report={'schema':'r000c-independent-observer-delta/v1','previousDriverSha256':sha(old.read_bytes()),'successorDriverSha256':sha(new.read_bytes()),'successorPacketSha256':sha((ROOT/'tests/rlgwo/R000C-cases.json').read_bytes()),'wrapperSha256':sha((ROOT/'tests/rlgwo/weather-browser-fixture.html').read_bytes()),'originalVersionPreserved':True,'checkAndReadyAstUnchanged':True,'casePacketOnlyDriverPinChanged':True,'allSourcePinsMatch':True,'passiveRecoveryExpression':passive,'review':'One unchanged Firefox night-default pilot justified; no native result, causal claim, visual PASS or authorization gate is granted by this source review. Full diagnostic predicates are unchanged at watch boundaries; within-watch full diagnostic cadence is removed and explicitly disclosed.'}
(OUT/'boundary-observer-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
