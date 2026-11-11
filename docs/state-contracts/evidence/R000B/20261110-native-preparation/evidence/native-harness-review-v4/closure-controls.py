"""Independent bounded HR1/HR2 closure: actual Python predicates, static JS source only."""
from pathlib import Path
from copy import deepcopy
import ast
import datetime
import difflib
import hashlib
import json
import math
import re
import runpy
import subprocess
import sys

ROOT=Path('/workspace/scratch/15b8fb6ac4c2')
REPO=ROOT/'r000b-work'
OLD=ROOT/'evidence/native-harness-review-v3/frozen-inputs'
V2=ROOT/'evidence/native-harness-v2'
OUT=ROOT/'evidence/native-harness-review-v4'
FROZEN={
 'tools/qa/run_r000b_withdrawal.py':'1eeb84e2800231ef74349af2152be5b85df807232403199afa3566e804edfb2c',
 'tests/weather-no-timetable-native-oracles.test.py':'25ee18492a84ca4646d7695b26d81799afe56ba059ddfed3901707f3351af3d4',
 'tests/rlgwo/r000b-no-timetable-fixture.html':'5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c',
 'src/native/index.html':'b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f',
}
def sha(data):return hashlib.sha256(data).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
identities=[]
for rel,expected in FROZEN.items():
 b=(REPO/rel).read_bytes();actual=sha(b);assert actual==expected
 identities.append({'path':str(REPO/rel),'bytes':len(b),'sha256':actual,'expectedSha256':expected})
old_driver_path=OLD/'tools/qa/run_r000b_withdrawal.py'
assert sha(old_driver_path.read_bytes())=='9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e'
assert sha((ROOT/'reviews/native-harness-review-v3.md').read_bytes())=='000756008c67be0595ec914a7ded40a1934d7f08b2e3a6a1e1964d64ffa53dce'
save('input-identities.json',identities)

new_driver=(REPO/'tools/qa/run_r000b_withdrawal.py').read_text(); old_driver=old_driver_path.read_text()
new_tests=(REPO/'tests/weather-no-timetable-native-oracles.test.py').read_text()
old_tests=(OLD/'tests/weather-no-timetable-native-oracles.test.py').read_text()
new_ast=ast.parse(new_driver); old_ast=ast.parse(old_driver)
compile(new_ast,'frozen-v4-driver','exec'); compile(ast.parse(new_tests),'frozen-v4-tests','exec')
def defs(source,kind):return {n.name:n for n in ast.parse(source).body if isinstance(n,kind)}
def identical(a,source_a,b,source_b):return ast.dump(a)==ast.dump(b) and ast.get_source_segment(source_a,a)==ast.get_source_segment(source_b,b)
old_f,new_f=defs(old_driver,ast.FunctionDef),defs(new_driver,ast.FunctionDef)
changed=[name for name,n in old_f.items() if name!='main' and not identical(n,old_driver,new_f[name],new_driver)]
assert set(changed)=={'healthy_refresh_record','_healthy_refresh_request','_healthy_refresh_sample','healthy_refresh_pair','healthy_refresh_evidence'}
v2_driver=(V2/'tools/qa/run_r000b_withdrawal.py').read_text()
v2_functions=defs(v2_driver,ast.FunctionDef)
preserved_v2=[name for name,n in v2_functions.items() if name!='main' and identical(n,v2_driver,new_f[name],new_driver)]
assert len(preserved_v2)==23
v2_tests=(V2/'tests/weather-no-timetable-native-oracles.test.py').read_text()
old_classes,new_classes=defs(v2_tests,ast.ClassDef),defs(new_tests,ast.ClassDef)
preserved_classes=[name for name,n in old_classes.items() if identical(n,v2_tests,new_classes[name],new_tests)]
assert len(preserved_classes)==4
watch_start="            watch = {'stage': 'recovered',"
watch_end='\n            # R000B_F01_REQUIRED_ORDINARY_HEALTHY_REFRESH_V1'
old_watch=old_driver[old_driver.index(watch_start):old_driver.index(watch_end)].rstrip()
new_watch=new_driver[new_driver.index(watch_start):new_driver.index(watch_end)].rstrip()
assert old_watch==new_watch
assert (REPO/'tests/rlgwo/r000b-no-timetable-fixture.html').read_bytes()==(OLD/'tests/rlgwo/r000b-no-timetable-fixture.html').read_bytes()
# Compare actual call-site AST to prove the observed origin is not lost on the
# reused-watch, extra-capture, or final evidence paths. This executes no main.
main=new_f['main']
origin_calls=[]
for n in ast.walk(main):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'healthy_refresh_pair','healthy_refresh_evidence'}:
  origin_calls.append({'function':n.func.id,'line':n.lineno,'lastArgument':ast.unparse(n.args[-1])})
assert len(origin_calls)==3 and all(c['lastArgument']=='refresh_clock_origin' for c in origin_calls)
assert 'clockOrigin:{started:f.started,startUtc:f.startUtc}' in new_driver
assert "refresh_clock_origin = refresh_progress.get('clockOrigin')" in new_driver
assert "{'started': fixture.get('started'), 'startUtc': fixture.get('startUtc')} != refresh_clock_origin" in new_driver
save('preservation-and-propagation.json',{'prior23FunctionsUnchanged':preserved_v2,'prior4ClassesUnchanged':preserved_classes,
 'changedV3Functions':changed,'newFunctions':sorted(set(new_f)-set(old_f)),
 'originalWatchUnchanged':True,'watchSha256':sha(new_watch.encode()),'fixtureUnchanged':True,
 'acquisitionOriginCalls':origin_calls,'syntaxCompileOnly':True})
for name,a,b in [('driver-v3-v4.diff',old_driver,new_driver),('tests-v3-v4.diff',old_tests,new_tests)]:
 (OUT/name).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='frozen-v3',tofile='frozen-v4')))

command=[sys.executable,'-B',str(REPO/'tests/weather-no-timetable-native-oracles.test.py'),'HealthyRefreshTests','HealthyRefreshInterfaceTests','-v']
completed=subprocess.run(command,cwd=REPO,capture_output=True,text=True,check=False)
log=completed.stdout+completed.stderr;(OUT/'focused-tests.log').write_text(log)
count=re.search(r'Ran (\d+) tests?',log)
suite={'command':command,'exitCode':completed.returncode,'testsReported':int(count.group(1)) if count else None}
save('focused-tests.json',suite)
assert completed.returncode==0 and suite['testsReported']==27

# Source-derived representation/data controls. No JavaScript is evaluated.
source=(REPO/'src/native/index.html').read_text()
fixture=(REPO/'tests/rlgwo/r000b-no-timetable-fixture.html').read_text()
capture_source=source.split('function captureWeatherTarget(',1)[1].split('\nfunction weatherTargetSame',1)[0]
rich_literal=capture_source.split('return {',1)[1].rsplit('};',1)[0]
rich_keys=re.findall(r'(?:^|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?=:|,|$)',rich_literal)
projection_literal=source.split('const receipt=Object.freeze({revision:',1)[1].split('target:Object.freeze({',1)[1].split('})',1)[0]
projection_keys=re.findall(r'(?:^|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:',projection_literal)
budget=int(re.search(r'const _WX_BODY_WAIT=(\d+)',source).group(1))
start_iso=re.search(r'const startUtc=NativeDate.parse\("([^"]+)"\)',fixture).group(1)
start_utc=int(datetime.datetime.fromisoformat(start_iso.replace('Z','+00:00')).timestamp()*1000)
assert set(rich_keys)=={'generation','lat','lon','intent','source','accuracyM','acquiredAt','provider','area','bounds'}
assert projection_keys==['generation','lat','lon'] and budget==10000
assert 'deadlineAt:_RAFNOW()+timeoutMs' in source and '? performance.now() : Date.now()' in source
assert 'wall=()=>startUtc+Math.floor(elapsed())' in fixture
assert 'static now(){return wall();}' in fixture
assert 'elapsedRtMs:_cloudMotion.lastRt==null?null:_cloudMotion.lastRt-report.started' in fixture
save('source-interface-derivation.json',{'sourceSha256':FROZEN['src/native/index.html'],
 'fixtureSha256':FROZEN['tests/rlgwo/r000b-no-timetable-fixture.html'],'captureWeatherTargetKeys':rich_keys,
 'publicationTargetKeys':projection_keys,'weatherAttemptBudgetMs':budget,'fixtureStartIso':start_iso,
 'fixtureStartUtc':start_utc,'method':'Read exact authored JS declarations and extract data keys/constants only; no product function executed.'})

ns=runpy.run_path(str(REPO/'tests/weather-no-timetable-native-oracles.test.py'),run_name='independent_closure_data')
new=ns['ORACLE']; old=ns['load_oracles'](old_driver_path); make=ns['healthy_refresh_case']
probes=[]
def result(name,observed,expected,detail=None):
 probes.append({'id':name,'observed':observed,'expected':expected,'matched':observed==expected,'detail':detail})
 save('independent-controls.json',{'probes':probes,'noExceptionCredit':True,'scope':'Pure data through actual AST-extracted frozen predicates; no product/native execution.'})
 assert observed==expected,name

def source_case(mode='default',origin=3701.3125):
 c=make(mode=mode,performance_origin=origin)
 assert c['clock']['startUtc']==start_utc
 values={'generation':7,'lat':24.7136,'lon':46.6753,'intent':'unknown','source':'unknown'}
 rich={k:values.get(k) for k in rich_keys}; projection={k:rich[k] for k in projection_keys}
 for frame in c['full']:
  frame['target']=deepcopy(rich);frame['raw']['target']=deepcopy(rich)
  assert frame['actualCloud']['publication']['target']==projection
 for request in c['ledger']:
  # Real beginAttempt precedes interception; exercise a nonzero setup interval.
  request['nativeOwner']['deadlineAt']=origin+request['elapsedMs']-0.375+budget
  request['jsonElapsedMs']+=0.125
 return c

def verdict(c):return new.healthy_refresh_evidence(c['before'],c['after'],c['passive'],c['full'],c['ledger'],c['mode'],c['clock'])
case=source_case()
record=new.healthy_refresh_record(case['after'])
old_record=old.healthy_refresh_record(case['after'])
result('C1-HR1-old-fails-new-selects',{'oldRecord':old_record is not None,'newRecord':record is not None,
 'oldFullSample':old._healthy_refresh_sample(case['after'],[case['old'],case['new']],full=True),
 'newFullSample':new._healthy_refresh_sample(case['after'],[case['old'],case['new']],full=True)},
 {'oldRecord':False,'newRecord':True,'oldFullSample':False,'newFullSample':True},
 {'sourceDerivedRichKeys':rich_keys,'sourceDerivedProjectionKeys':projection_keys})
# Each version receives its actual signature. An exception is never rejection credit.
old_match=old._healthy_refresh_request(record,case['after'],case['ledger'])
new_match=new._healthy_refresh_request(record,case['after'],case['ledger'],case['clock'])
result('C2-HR2-old-fails-new-matches',{'oldMatched':old_match is not None,'newMatched':new_match is not None,'fullEvidenceOk':verdict(case)['ok']},
 {'oldMatched':False,'newMatched':True,'fullEvidenceOk':True},new_match['timing'])
for mode in ['reduced','full']:
 c=source_case(mode=mode,origin=777.1875)
 result('C3-'+mode+'-source-shaped-positive',verdict(c)['ok'],True,{'origin':c['clock']['started']})

# Pure matcher interval probes leave all admitted times and candidate/publication
# identities internally consistent, and only move the tested receipt/deadline.
def receipt_match(receipt_elapsed,deadline_elapsed=190000,body_elapsed=180005.125):
 c=source_case(); receipt=deepcopy(c['new']);receipt['retrievedAt']=start_utc+receipt_elapsed;receipt['at']=receipt['retrievedAt']+1
 captured=c['frame'](205000,receipt)
 captured['target']=deepcopy(c['after']['target']);captured['raw']['target']=deepcopy(c['after']['target'])
 c['ledger'][-1]['nativeOwner']['deadlineAt']=c['clock']['started']+deadline_elapsed
 c['ledger'][-1]['jsonElapsedMs']=body_elapsed
 rec=new.healthy_refresh_record(captured)
 assert rec is not None
 return new._healthy_refresh_request(rec,captured,c['ledger'],c['clock'])
for label,receipt_elapsed,deadline_elapsed,body_elapsed,expected in [
 ('whole-interval-safe',189998,189999.625,180005.125,True),
 ('fractional-deadline-straddle',189999,189999.625,180005.125,False),
 ('exact-upper-contact',189999,190000,180005.125,False),
 ('receipt-at-deadline',190000,190000,180005.125,False),
 ('body-at-deadline',190000,190000,190000,False),
 ('body-after-deadline',190001,190000,190000.25,False)]:
 matched=receipt_match(receipt_elapsed,deadline_elapsed,body_elapsed)
 result('C4-'+label,matched is not None,expected,{'receiptElapsedMs':receipt_elapsed,'deadlineElapsedMs':deadline_elapsed,'jsonElapsedMs':body_elapsed})

wrong_domain=source_case();wrong_domain['ledger'][-1]['nativeOwner']['deadlineAt']=start_utc+192000
rec=new.healthy_refresh_record(wrong_domain['after'])
result('C5-epoch-deadline-old-accepts-new-rejects',{
 'oldMatched':old._healthy_refresh_request(rec,wrong_domain['after'],wrong_domain['ledger']) is not None,
 'newMatched':new._healthy_refresh_request(rec,wrong_domain['after'],wrong_domain['ledger'],wrong_domain['clock']) is not None},
 {'oldMatched':True,'newMatched':False})
for label,mutate in [
 ('missing-origin',lambda c:c.update(clock=None)),
 ('wrong-origin',lambda c:c['clock'].update(started=c['clock']['started']+0.001)),
 ('wrong-motion-origin',lambda c:c['after']['actualCloud']['motion'].update(lastRt=c['after']['actualCloud']['motion']['lastRt']+0.001)),
 ('raw-provenance-drift',lambda c:c['after']['raw']['target'].update(source='manual')),
 ('projected-identity-drift',lambda c:c['after']['actualCloud']['publication']['target'].update(lat=0))]:
 c=source_case();mutate(c);result('C6-'+label,verdict(c)['ok'],False)
save('summary.json',{'focusedTests':suite['testsReported'],'independentProbeRecords':len(probes),'allExpectedResults':all(p['matched'] for p in probes),
 'prior23FunctionsUnchanged':len(preserved_v2),'prior4ClassesUnchanged':len(preserved_classes),'watchUnchanged':True,'exceptionCreditedAsFault':False})
print(json.dumps({'focusedTests':suite['testsReported'],'independentProbeRecords':len(probes),'allExpectedResults':True,'prior23FunctionsUnchanged':23,'prior4ClassesUnchanged':4,'watchUnchanged':True}))
