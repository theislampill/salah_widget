"""One native delayed-body or actual file-atob control per engine, then one retry."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;H=O/'recovery-tools-r121-r122';root=O/'builds/integrated-r31-file-transport'
assert len(sys.argv)>=2 and sys.argv[1] in ['delayed-body','file-atob']
fault=sys.argv[1];assert fault=='file-atob','r127 covers only the affected file decoder';dest=O/'native'/('delayed-body-r121' if fault=='delayed-body' else 'file-atob-r127')
sys.path.insert(0,str(H/'tools/cp9'))
from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prep=json.loads((O/'intake/recovery-r121-r122-preparation.json').read_bytes());pins={p:x['afterSha256'] for p,x in prep['changes'].items()}
assert all(sha(H/p)==v for p,v in pins.items())
runtime=runtime_identity(root);assert runtime['treeSha256']=='1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b'
record={'schema':'r0021-bounded-native-recovery/v1','fault':fault,'runtime':runtime['treeSha256'],'preparationSha256':sha(O/'intake/recovery-r121-r122-preparation.json'),
 'harnessInputSha256':pins,'status':'PREPARED','cases':[],'noRepeat':True,
 'scope':'Functional failure/current-initial/UI/ownership and explicit-retry/final admission only; no S1, cost or continuous-display credit.',
 'observer':'Absolute540s asyncio deadline from firstnavigation; productasset120000ms/refinement240000ms unchanged. Outer600s process limit only for launch/ownedcleanup. PNG15s/failed/settings/final; existingChromiumvideo, noFirefoxrecorder.',
 'asset':{'demLength':(root/'moon/assets/dem.bin.gz').stat().st_size,'demSha256':sha(root/'moon/assets/dem.bin.gz'),'prefixSha256':hashlib.sha256((root/'moon/assets/dem.bin.gz').read_bytes()[:4096]).hexdigest()}}
assert record['asset']['demLength']==20137935
for family,exe in [('chromium',r'${BROWSER_CACHE}\chromium-1223\chrome-win64\chrome.exe'),('firefox',r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe')]:
 assert Path(exe).is_file()
 cmd=[r'${QA_TOOLCHAIN}\venv\Scripts\python.exe','-I','-B',str(H/'tools/cp9/celestial_startup_check.py'),'--root',str(root),'--out',str(dest/family),
  '--driver-cli',str(O/'capture-driver/cli.js'),'--driver-node',r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe',
  '--scene','clear','--entry','direct' if fault=='delayed-body' else 'file','--dpr','1','--modes','cold','--duration','540','--video-only','--persistent-profile']
 if family=='chromium':cmd+=['--restore-render-document']
 record['cases'].append({'browser':family,'executable':exe,'command':cmd,'status':'PREPARED'})
if '--prepare' in sys.argv:
 p=O/'intake'/(dest.name+'-commands.json');p.write_bytes((json.dumps(record,indent=2)+'\n').encode());print(json.dumps({'preparation':str(p),'sha256':sha(p)}));sys.exit()
assert '--execute' in sys.argv and not dest.exists(),'No repeat'
lock=O/'native-resource.lock'
with lock.open('x') as f:f.write(dest.name)
normal=False
try:
 dest.mkdir()
 for case in record['cases']:
  family=case['browser'];case.update(status='RUNNING',startedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (dest/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
  env=dict(os.environ,SALAH_BROWSER=family,SALAH_BROWSER_EXECUTABLE=case['executable'],SALAH_CAPTURE_NATIVE_FRAMES='0',SALAH_TERMINAL_FAULT=fault)
  with (dest/(family+'-RUN-LOG.txt')).open('wb') as log:
   p=subprocess.Popen(case['command'],env=env,stdout=log,stderr=subprocess.STDOUT);case['pid']=p.pid
   try:case['exitCode']=p.wait(timeout=600)
   except BaseException as e:
    case.update(status='INTERRUPTED_TERMINATION_UNVERIFIED',error=repr(e))
    try:
     kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20);case['ownedTreeTerminationExit']=kill.returncode;p.wait(timeout=20)
    except BaseException as cleanup:case['cleanupError']=repr(cleanup)
    raise
  case.update(status='RETURNED',returnedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  if case['exitCode']!=0:raise RuntimeError('Acquisition failed; preserve partial and reconcile ownedlease')
  result=json.loads((dest/family/'results.json').read_bytes());f=result.get('fault') or {};final=f.get('finalState') or {};moon=final.get('moon') or {}
  problems=[]
  runs=result.get('runs') or []
  if len(runs)!=1 or runs[0].get('mode')!='cold':problems.append('Expected one cold run')
  if result.get('errors'):problems.append({'unexpectedBrowserErrors':result['errors']})
  if not runs or (runs[0].get('recovery') or {}).get('retry',{}).get('moon') is not True:problems.append('One actual explicit Moon retry not observed')
  if not result.get('runtimeUnchanged') or result.get('runtime',{}).get('treeSha256')!=runtime['treeSha256']:problems.append('Runtime identity')
  if result.get('observerCeiling') or f.get('status')!='CURRENT_FINAL_RETURNED_FOR_REVIEW':problems.append('Missing final recovery')
  if not f.get('expectedFailureObserved') or not f.get('currentInitialAndCleanup'):problems.append('Failure/currentness/cleanup boundary incomplete')
  if fault=='delayed-body' and f.get('settingsRoute')!='ACTUAL_BUCKLE_OPEN_CLOSE':problems.append('Native settings route absent')
  quality=(moon.get('last') or {}).get('quality') or {}
  if not (moon.get('status')=='ready' and moon.get('current') is True and moon.get('visibleSource')=='refined-terrain' and moon.get('quality')=='empirical-adaptive' and quality.get('status')=='empirical-adaptive' and quality.get('projectedGate')==.5 and isinstance(quality.get('projectedMaximumCode'),(int,float)) and quality['projectedMaximumCode']<=.5 and quality.get('unsettled')==0):problems.append('Actual final quality/currentness gate not established')
  before=f.get('sourceObserverBeforeRecovery') or {};after=f.get('sourceObserverAfterRecovery') or {};failedAt=(f.get('failedState') or {}).get('at',-1)
  boots={e['worker'] for e in before.get('events',[]) if e.get('kind')=='worker-boot'}
  terminated={w['id'] for w in before.get('workers',[]) if w.get('terminatedAt') is not None and w['terminatedAt']<=failedAt}
  if not boots.intersection(terminated):problems.append('Failed primary termination not observed')
  if fault=='delayed-body':
   fired=[t for t in before.get('timers',[]) if t.get('delay')==120000 and t.get('firedAt') is not None and t['firedAt']<=failedAt]
   bodies=[r for run in runs for r in run.get('serverRequests',[]) if r.get('kind')=='controlled-open-body']
   if len(bodies)!=1 or bodies[0].get('declaredBytes')!=20137935 or bodies[0].get('sentBytes')!=4096 or bodies[0].get('prefixSha256')!=record['asset']['prefixSha256']:problems.append('Original declared length/prefix body boundary missing')
   if not fired or not bodies or not any(bodies[0].get('releasedAbsolute',0)>t['timeOrigin']+t['after']+120000 and bodies[0]['openedAbsolute']<t['timeOrigin']+t['before']+120000 for t in fired):problems.append('Body held beyond actual source timer and failure before restore unproved')
  else:
   injections=[e for e in before.get('events',[]) if e.get('kind')=='malformed-base64-injected']
   errors=[e for e in before.get('events',[]) if e.get('kind')=='worker-message' and e.get('messageKind')=='boot-error']
   restored=[e for e in after.get('events',[]) if e.get('kind')=='original-base64-delivered']
   if before.get('injections')!=1 or len(injections)!=1:problems.append('Exactly one native file transport injection unproved')
   elif not (injections[0]['worker'] in terminated and any(e['worker']==injections[0]['worker'] for e in errors) and any(e['worker']!=injections[0]['worker'] and all(e.get(k)==injections[0].get(k) for k in ['name','index','last','type','originalLength','originalPrefix','originalSuffix']) for e in restored)):problems.append('Native atob boot-error/terminated-primary/original-new-worker recovery chain unproved')
  case['postconditions']={'status':'INCOMPLETE_STOP' if problems else 'RETURNED_FOR_INDEPENDENT_REVIEW','problems':problems}
  (dest/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
  print(json.dumps({'completed':family,'fault':fault,'observationStatus':f.get('status'),'problems':problems}),flush=True)
  if problems:record['status']='INCOMPLETE_STOP';normal=True;break
 else:record['status']='RETURNED';normal=True
finally:
 record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['harnessUnchanged']=all(sha(H/p)==v for p,v in pins.items());record['runtimeUnchanged']=runtime==runtime_identity(root)
 if not record['harnessUnchanged'] or not record['runtimeUnchanged']:record['status']='INCOMPLETE_IDENTITY_DRIFT'
 record['leaseReleased']=normal;(dest/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
 if normal:assert lock.read_text()==dest.name;lock.unlink()
print(json.dumps({'status':record['status'],'leaseReleased':normal}))
