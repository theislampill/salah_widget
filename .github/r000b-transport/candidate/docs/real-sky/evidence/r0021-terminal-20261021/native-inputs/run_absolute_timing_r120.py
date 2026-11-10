"""One observation of each missing original local-HTTP timing cell; no refinement wait."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
root=O/'builds/integrated-r30-owner-callbacks'
dest=O/'native/absolute-timing-r120'
expected='3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821'
pins=json.loads((O/'native/chromium-arc-samples-r105/EXECUTION.json').read_bytes())['harnessInputSha256']
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in pins.items()),'Harness drift'
sys.path.insert(0,str(R/'tools/cp9'))
from runtime_identity import runtime_identity
runtime=runtime_identity(root);assert runtime['treeSha256']==expected,'Frozen runtime drift'
executables={'chromium':r'${BROWSER_CACHE}\chromium-1223\chrome-win64\chrome.exe',
 'firefox':r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe'}
families=[('clear-iframe-dpr2','iframe',2,390,600),('direct-desktop-dpr2','direct',2,1100,900),
 ('direct-constrained-dpr1','direct',1,375,800),('iframe-constrained-dpr1','iframe',1,375,800)]
record={'schema':'r0021-absolute-timing-cells/v1','purpose':__doc__,'status':'PREPARED','runtime':expected,
 'harnessInputSha256':pins,'modes':['cold','warm-reload','new-tab'],'cellCeiling':24,'repeatAllowanceUsed':0,
 'observer':'Existing r105 native source/video with exterior compositor marker, video-only first15s, duration0. No tracing, profiling, new clock, final-refinement wait or matched baseline.',
 'thresholdsMs':{'chromium':{'navigation':1000,'originalAcceptedScene':250},'firefox':{'navigation':1500,'originalAcceptedScene':400}},
 'limitations':'Receipt upper bounds require independent whole-scene classification and original accepted clock. TA4 excepts only first-ever80ms and matched-baseline proof; gaps remain UNOBSERVED. Over-budget receipt alone is not demonstrated physical slowness.',
 'cases':[]}
for family,exe in executables.items():
    assert Path(exe).is_file()
    for name,entry,dpr,width,height in families:
        out=dest/(family+'-'+name)
        cmd=[r'${QA_TOOLCHAIN}\venv\Scripts\python.exe','-I','-B',str(R/'tools/cp9/celestial_startup_check.py'),
          '--root',str(root),'--out',str(out),'--driver-cli',str(O/'capture-driver/cli.js'),
          '--driver-node',r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe',
          '--video','--video-only','--compositor-marker','--modes','cold,warm-reload,new-tab','--duration','0',
          '--entry',entry,'--dpr',str(dpr),'--viewport',str(width),str(height),'--persistent-profile']
        if family=='chromium':cmd+=['--restore-render-document']
        record['cases'].append({'name':out.name,'engine':family,'entry':entry,'dpr':dpr,'viewport':[width,height],
          'executable':exe,'command':cmd,'status':'PREPARED','observerProcessCeilingSeconds':180})
if '--prepare' in sys.argv:
    p=O/'intake/absolute-timing-r120-preparation.json';p.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'preparation':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':8,'cells':24}));sys.exit()
assert '--execute' in sys.argv,'Specify --prepare or --execute'
assert not dest.exists(),'No repeated acquisition'
lock=O/'native-resource.lock'
with lock.open('x') as f:f.write(dest.name)
normal=False
try:
    dest.mkdir()
    for case in record['cases']:
        case.update(status='RUNNING',startedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
        env=dict(os.environ,SALAH_BROWSER=case['engine'],SALAH_BROWSER_EXECUTABLE=case['executable'],SALAH_CAPTURE_NATIVE_FRAMES='1')
        with (dest/(case['name']+'-RUN-LOG.txt')).open('wb') as log:
            p=subprocess.Popen(case['command'],env=env,stdout=log,stderr=subprocess.STDOUT);case['pid']=p.pid
            try:case['exitCode']=p.wait(timeout=case['observerProcessCeilingSeconds'])
            except BaseException as e:
                case.update(status='INTERRUPTED_TERMINATION_UNVERIFIED',error=repr(e))
                try:
                    killed=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20)
                    case['ownedTreeTerminationExit']=killed.returncode;p.wait(timeout=20)
                except BaseException as cleanup:case['cleanupError']=repr(cleanup)
                raise
        case.update(status='RETURNED',returnedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
        if case['exitCode']!=0:raise RuntimeError('Acquisition failed; retain partial and reconcile lease before independent rows')
        report=json.loads((dest/case['name']/'results.json').read_bytes())
        faults=[]
        if [r.get('mode') for r in report.get('runs',[])]!=record['modes']:faults.append('Missing or unexpected mode')
        if report.get('runtimeUnchanged') is not True or report.get('runtime',{}).get('treeSha256')!=expected:faults.append('Runtime identity failure')
        if report.get('errors'):faults.append({'browserErrors':report['errors']})
        for run in report.get('runs',[]):
            for edge in ['at15s','final']:
                state=run.get(edge) or {};moon=state.get('moon') or {};sky=state.get('sky') or {}
                if moon.get('status')=='unavailable' or moon.get('errors') or moon.get('initialError'):
                    faults.append({'mode':run['mode'],'edge':edge,'unexpectedMoonState':moon})
                if sky.get('status') in ['unavailable','error','failed']:
                    faults.append({'mode':run['mode'],'edge':edge,'unexpectedSkyState':sky})
        case['postconditions']={'faults':faults,'status':'INCOMPLETE_STOP' if faults else 'RETURNED_FOR_INDEPENDENT_PIXEL_TIMING_REVIEW'}
        (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
        if faults:
            record['status']='INCOMPLETE_STOP_UNEXPECTED_STATE';normal=True;break
        print(json.dumps({'completed':case['name'],'modes':3}),flush=True)
    else:record['status']='RETURNED';normal=True
finally:
    record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['harnessUnchanged']=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in pins.items())
    record['runtimeUnchanged']=runtime==runtime_identity(root)
    if not record['harnessUnchanged'] or not record['runtimeUnchanged']:record['status']='INCOMPLETE_STOP_IDENTITY_DRIFT'
    record['leaseReleased']=normal
    (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
    if normal:
        assert lock.read_text()==dest.name;lock.unlink()
print(json.dumps({'status':record['status'],'leaseReleased':normal}))
