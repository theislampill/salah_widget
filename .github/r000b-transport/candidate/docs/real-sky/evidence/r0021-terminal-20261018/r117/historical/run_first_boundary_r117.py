"""One serial Chromium cold/direct pair, unchanged r105 harness, no profiler."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
prior=json.loads((O/'native/chromium-arc-samples-r105/EXECUTION.json').read_bytes())
pins=prior['harnessInputSha256']
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in pins.items()),'Harness drift'
sys.path.insert(0,str(R/'tools/cp9'))
from runtime_identity import runtime_identity
exe=r'${ISOLATED_CHROMIUM}'
assert Path(exe).is_file()
env=dict(os.environ,SALAH_BROWSER='chromium',SALAH_BROWSER_EXECUTABLE=exe,SALAH_CAPTURE_NATIVE_FRAMES='1')
record={'schema':'r0021-first-boundary-pair/v1','purpose':__doc__,'harnessInputSha256':pins,'cases':[],'status':'PREPARED','noRepeat':True,'scope':'First exposed celestial scene/principal content, original accepted clock, and matched baseline. Existing source gaps stay UNOBSERVED; no blanket S1 or performance claim.'}
arms=[('baseline','baseline-18ff','f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'),('candidate','integrated-r29-lunar-rule','70bb508176c976167d783a5c7c7bd09ab20d02f69669dce5d36af5c634b1c55e')]
identities={}
for name,build,expected in arms:
    identities[name]=runtime_identity(O/'builds'/build)
    assert identities[name]['treeSha256']==expected,'Frozen runtime drift'
custody=json.loads((O/'builds/baseline-18ff/BASELINE-CUSTODY.json').read_bytes())
assert custody['commit']=='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
assert custody['indexSha256']==identities['baseline']['files']['index.html']['sha256']
record['baselineCustody']=custody
record['baselineCustodySupplement']=json.loads((O/'builds/baseline-18ff/BASELINE-CUSTODY-SUPPLEMENT.json').read_bytes())
dest=O/'native/first-boundary-r117';assert not dest.exists()
lock=O/'native-resource.lock'
with lock.open('x') as f:f.write(dest.name)
normal=False
try:
    dest.mkdir()
    for name,build,expected in arms:
        root=O/'builds'/build;out=dest/name
        runtime=identities[name]
        cmd=[r'${PLAYWRIGHT_PYTHON}','-I','-B',str(R/'tools/cp9/celestial_startup_check.py'),'--root',str(root),'--out',str(out),'--driver-cli',str(O/'capture-driver/cli.js'),'--driver-node',r'${DRIVER_NODE24}','--video-only','--compositor-marker','--modes','cold','--duration','20','--entry','direct','--persistent-profile','--restore-render-document']
        case={'name':name,'build':build,'runtime':runtime['treeSha256'],'command':cmd,'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED'};record['cases'].append(case)
        (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
        with (dest/(name+'-RUN-LOG.txt')).open('wb') as log:
            p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);case['pid']=p.pid
            try:case['exitCode']=p.wait(timeout=90)
            except BaseException as e:
                case.update(status='INTERRUPTED_TERMINATION_UNVERIFIED',error=repr(e))
                try:
                    killed=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20);case['ownedTreeTerminationExit']=killed.returncode;p.wait(timeout=20)
                except BaseException as cleanup:case['cleanupError']=repr(cleanup)
                raise
        case.update(status='RETURNED',returnedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        if case['exitCode']!=0:raise RuntimeError('Acquisition failed; no second arm or repeat')
        print(json.dumps({'completed':name,'runtime':case['runtime']}),flush=True)
    normal=True;record['status']='RETURNED'
finally:
    record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['harnessUnchanged']=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in pins.items())
    record['runtimeUnchanged']={name:identities[name]==runtime_identity(O/'builds'/build) for name,build,expected in arms}
    record['leaseReleased']=normal
    (dest/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
    if normal:
        assert lock.read_text()==dest.name;lock.unlink()
print(json.dumps({'status':record['status'],'leaseReleased':normal}))
