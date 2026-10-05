#!/usr/bin/env python3
"""Run inherited native contracts, including important suites outside *.test.cjs.

No live-provider/platform claim: each fixture retains its own stated scope.
Results/logs are external when qualifying a sealed extraction.
"""
from pathlib import Path
import argparse,json,subprocess,time,sys,re
ROOT=Path(__file__).resolve().parents[2]
NAMED=['r0001-date-sinks.cjs','r0007-countdown.cjs','r0008-timezone.cjs','r0009-date-selection.cjs',
 'r000f-intent.cjs','r000f-reset.cjs','r0010-preferences.cjs','r0011-storage.cjs',
 'r0012-clipboard.cjs','r0012-effects.cjs','r0017-cloud-visibility.cjs','r0017-contract.cjs',
 'r0017-transport.cjs','r0017-weather.cjs','r0018-appearance.cjs','r0018-timetable-contrast.cjs',
 'r0019-date-disclosure.cjs','r001a-radio.cjs','r001d-lifecycle.cjs','r001f-deadline.cjs',
 'r0020-clock.cjs','r0021-reveal.cjs','r0022-baseline-balance.cjs','r0022-lunar-consumers.cjs',
 'r0023-metadata.cjs','r0025-continuity.cjs','r0025-lifecycle.cjs']
HISTORICAL={
 'r0018-timetable-contrast.cjs':'Requires unsupplied historical commit fd2972ba64225fe9d6848e92497e6d0ed20ea624; current pinned-baseline preservation is checked separately.',
 'r0022-baseline-balance.cjs':'Requires unsupplied historical commits fd2972ba64225fe9d6848e92497e6d0ed20ea624 and 8b83df029966c203a503ab217d121c48b8ee6e8a; CP8 does not reacquire or substitute them.'}
SNAPSHOT_ONLY={'r0021-reveal.cjs','r0022-lunar-consumers.cjs','r0023-metadata.cjs'}
def run(root,out):
 out.mkdir(parents=True,exist_ok=True);records=[]
 commands=[('native-test-glob',['node','--test','--test-concurrency=1',*map(str,sorted((root/'tests').glob('*.test.cjs')))])]
 commands += [(Path(n).stem,['node','tests/'+n]+(['--cp8-snapshot-only'] if n in SNAPSHOT_ONLY else [])) for n in NAMED if n not in HISTORICAL]
 for name,cmd in commands:
  start=time.monotonic();log=out/(name+'.log')
  try:
   with log.open('w') as f:r=subprocess.run(cmd,cwd=root/'.',stdout=f,stderr=subprocess.STDOUT,timeout=180)
   code=r.returncode
  except subprocess.TimeoutExpired:code=124
  text=log.read_text(encoding='utf-8');counts={}
  for field in ['tests','pass','fail','cancelled','skipped','todo']:
   m=re.search(r'^# '+field+r' (\d+)$',text,re.M)
   if m:counts[field]=int(m.group(1))
  if not counts:
   counts={'passLines':len(re.findall(r'^PASS\b',text,re.M)),'failLines':len(re.findall(r'^FAIL\b',text,re.M))}
   if counts=={'passLines':0,'failLines':0}:
    try:
     start=text.find('\n{');j=json.loads(text if text.lstrip().startswith('{') else text[start+1:]);items=j.get('results',[])
     counts={'passCases':sum(x.get('status',x.get('result'))=='PASS' for x in items),'failCases':sum(x.get('status',x.get('result'))=='FAIL' for x in items)}
    except (ValueError,TypeError):counts['unparsedOutput']=True
  exclusions=re.findall(r'^SKIP_(?:HISTORICAL|SUPERSEDED|EXPLICIT) .+$',text,re.M)
  records.append({'name':name,'command':cmd,'exitCode':code,'seconds':time.monotonic()-start,'counts':counts,'log':log.name,'explicitExclusions':exclusions})
  (out/'results.json').write_text(json.dumps({'status':'RUNNING','commands':records},indent=2));print(name,code,counts,flush=True)
 status='PASS' if all(x['exitCode']==0 for x in records) else 'FAIL'
 result={'status':status,'commands':records,'notRunHistorical':HISTORICAL,'scope':'Applicable current-snapshot native regression gates. Historical Git comparisons and removed synthetic-array producers are explicitly excluded, not reported passed.'};(out/'results.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();sys.exit(0 if run(x.root.resolve(),x.output)['status']=='PASS' else 1)
