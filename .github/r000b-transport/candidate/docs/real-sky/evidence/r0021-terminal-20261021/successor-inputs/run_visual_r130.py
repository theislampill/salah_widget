"""One predeclared missing case at a time; no retries, source edits or personal profiles."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
import psutil
O=Path(__file__).resolve().parent;R=Path(r'${REPO_ROOT}')
ROOT=O/'builds/integrated-r31-file-transport';DEST=O/'native/visual-r130'
EXPECTED='1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b'
PY=r'${QA_TOOLCHAIN}\venv\Scripts\python.exe'
NODE=r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe'
EXES={'chromium':r'${BROWSER_CACHE}\chromium-1223\chrome-win64\chrome.exe','firefox':r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe'}
sys.path.insert(0,str(R/'tools/cp9'));from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def cases():
 result=[]
 for name,engine,scene,entry,dpr,mode,harness in [
  ('firefox-clear-exact','firefox','clear','iframe',2,'new-tab','visual-tools-r126-exact'),
  ('firefox-cloud','firefox','partial','direct',1,'cold','visual-tools-r126'),
  ('firefox-twilight','firefox','twilight','direct',1,'cold','visual-tools-r126')]:
  out=DEST/name;cmd=[PY,'-I','-B',str(O/harness/'tools/cp9/celestial_startup_check.py'),'--root',str(ROOT),'--out',str(out),'--driver-cli',str(O/'capture-driver-r130/cli.js'),'--driver-node',NODE,'--scene',scene,'--entry',entry,'--dpr',str(dpr),'--viewport','390','600','--modes',mode,'--duration','360','--persistent-profile','--video','--video-only','--compositor-marker']
  if engine=='chromium':cmd+=['--restore-render-document']
  if entry=='extension':
   at=cmd.index('--viewport');cmd[at+1:at+3]=['1100','900']
   cmd+=['--extension-dir',str(O/'parent/tabliss-chromium'),'--parent-preset',str(ROOT/'presets/salah-widget.tablissng.json')]
  result.append({'name':name,'engine':engine,'command':cmd,'out':str(out),'limitSeconds':840 if entry=='extension' else 420,'selfLease':False})
 return result
def inputs():
 fixture_controls=[O/'twilight_fixture_r126.cjs',O/'intake/twilight-fixture-r126.json']
 paths=[Path(__file__),O/'prepare_source_recorder_r130.py',O/'source_recorder_r130.test.cjs',O/'intake/source-recorder-r130.json',O/'intake/source-recorder-r130-tests.txt',O/'prepare_visual_r130.py',O/'capture-driver-r130/cli.js',O/'capture-driver-r130/lib/coreBundle.js',Path(NODE),*map(Path,EXES.values()),O/'parent/tabliss-firefox.xpi',O/'parent/firefox_actual_widget_r125.py',O/'parent/parent_fixture_r125.py',R/'tools/cp9/celestial_startup_check.py',R/'tests/v1_browser.py',R/'tools/cp9/runtime_identity.py',ROOT/'presets/salah-widget.tablissng.json']
 for root in [O/'visual-tools-r126',O/'visual-tools-r126-exact',O/'parent-tools-r125',O/'parent/tabliss-chromium']:
  paths.extend(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 return {str(p):sha(p) for p in sorted(set(paths+fixture_controls))}
if '--prepare' in sys.argv:
 save(O/'intake/visual-r130-INPUTS.json',{'schema':'r0021-missing-visual-parent/v1','status':'PREPARED_ONLY','inputs':inputs(),'cases':cases(),'runtime':EXPECTED,'repeatPolicy':'Authorized successor; one corrected source-sidecar sequence per missing Firefox condition. Cparent ordinary cloud watch precedes native settings. All endpoints/gaps explicitly limited; no profiler or cold-parent S1 claim.','sourceScope':'Firefox exact clear, cloud, twilight only. Original source timestamps/JPEG bytes preserved; no interpolation or inference across gaps. Old acquisition failure remains retained. Actual returned astronomy and original pixels govern.'});print('prepared');sys.exit()
name=sys.argv[sys.argv.index('--case')+1];case=next(c for c in cases() if c['name']==name)
packet=json.loads((O/'intake/visual-r130-INPUTS.json').read_bytes());admission=json.loads((O/'intake/visual-r130-ADMISSION.json').read_bytes())
assert admission['status']=='SUPPORTED_EXACT_FINITE_GROUP' and admission['inputs']==inputs()==packet['inputs']
runtime=runtime_identity(ROOT);assert runtime['treeSha256']==EXPECTED
out=Path(case['out']);receipt=DEST/(name+'-EXECUTION.json');assert not out.exists() and not receipt.exists(),'No repetition'
lock=O/'native-resource.lock';assert not lock.exists(),'Native lease occupied'
DEST.mkdir(parents=True,exist_ok=True)
if not case['selfLease']:
 with lock.open('x') as f:f.write(name)
record={**case,'status':'ACQUIRING','startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':EXPECTED,'inputPacketSha256':sha(O/'intake/visual-r130-INPUTS.json')};owned={};proc=None
def remember():
 if proc is None:return
 try:rows=[psutil.Process(proc.pid),*psutil.Process(proc.pid).children(recursive=True)]
 except psutil.Error:return
 for p in rows:
  try:owned[p.pid]={'pid':p.pid,'created':p.create_time(),'exe':p.exe()}
  except psutil.Error:pass
try:
 env=dict(os.environ,SALAH_BROWSER=case['engine'],SALAH_BROWSER_EXECUTABLE=EXES[case['engine']],SALAH_CAPTURE_NATIVE_FRAMES='1')
 with (DEST/(name+'-RUN-LOG.txt')).open('wb') as log:
  proc=subprocess.Popen(case['command'],env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);start=time.monotonic()
  while proc.poll() is None:
   remember()
   if time.monotonic()-start>case['limitSeconds']:raise TimeoutError('Finite observer ceiling')
   time.sleep(.25)
  record.update(exitCode=proc.returncode,status='RETURNED_FOR_REVIEW' if proc.returncode==0 else 'INCOMPLETE_ACQUISITION')
except BaseException as e:record.update(status='INCOMPLETE_INTERRUPTED',error=repr(e))
finally:
 remember();remaining=[]
 for row in reversed(list(owned.values())):
  try:
   p=psutil.Process(row['pid'])
   if p.create_time()==row['created'] and p.exe()==row['exe']:
    p.terminate()
    try:p.wait(timeout=5)
    except psutil.TimeoutExpired:p.kill();p.wait(timeout=5)
  except psutil.NoSuchProcess:pass
  except psutil.Error as e:remaining.append({**row,'error':str(e)})
 record.update(ownedProcesses=list(owned.values()),remainingOwnedProcesses=remaining,runtimeUnchanged=runtime_identity(ROOT)==runtime,inputsUnchanged=inputs()==packet['inputs'],returnedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if not case['selfLease'] and not remaining and lock.exists() and lock.read_text()==name:lock.unlink()
 record['leaseAbsent']=not lock.exists()
 if remaining or not record['leaseAbsent'] or not record['runtimeUnchanged'] or not record['inputsUnchanged']:record['status']='INCOMPLETE_CLEANUP_OR_IDENTITY'
 save(receipt,record)
print(json.dumps({k:record[k] for k in ['name','status','leaseAbsent','runtimeUnchanged','inputsUnchanged']}))
