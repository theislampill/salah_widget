"""Two serial actual-body interruption/retry functional controls, no profiling."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent
H=O/'body-tools-r118';root=O/'builds/integrated-r29-lunar-rule'
sys.path.insert(0,str(H/'tools/cp9'))
from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prep=json.loads((O/'intake/body-r118-preparation.json').read_bytes())
pins={p:x['afterSha256'] for p,x in prep['changes'].items()}
assert all(sha(H/p)==v for p,v in pins.items())
runtime=runtime_identity(root);assert runtime['treeSha256']=='70bb508176c976167d783a5c7c7bd09ab20d02f69669dce5d36af5c634b1c55e'
arms=[('chromium',r'${ISOLATED_CHROMIUM}'),('firefox',r'${ISOLATED_FIREFOX}')]
assert all(Path(exe).is_file() for _,exe in arms)
dest=O/'native/body-interruption-r118';assert not dest.exists()
record={'schema':'r0021-body-native-controls/v1','purpose':__doc__,'runtime':runtime['treeSha256'],'preparationSha256':sha(O/'intake/body-r118-preparation.json'),'harnessInputSha256':pins,'status':'PREPARED','cases':[],'noRepeat':True,'acquisitionLimit':'No first-scene/callback/continuous-display qualification;15s failed-state and final PNGs plus native Chromium video; no Firefox recorder experiment.'}
lock=O/'native-resource.lock'
with lock.open('x') as f:f.write(dest.name)
normal=False
try:
    dest.mkdir()
    for family,exe in arms:
        out=dest/family
        cmd=[r'${PLAYWRIGHT_PYTHON}','-I','-B',str(H/'tools/cp9/celestial_startup_check.py'),'--root',str(root),'--out',str(out),'--driver-cli',str(O/'capture-driver/cli.js'),'--driver-node',r'${DRIVER_NODE24}','--scene','clear','--entry','direct','--dpr','1','--modes','cold','--duration','120','--recover-at','15','--video-only','--persistent-profile']
        if family=='chromium':cmd+=['--restore-render-document']
        env=dict(os.environ,SALAH_BROWSER=family,SALAH_BROWSER_EXECUTABLE=exe,SALAH_CAPTURE_NATIVE_FRAMES='0',SALAH_R118_BODY_INTERRUPT='1')
        case={'browser':family,'executable':exe,'command':cmd,'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED'};record['cases'].append(case)
        (dest/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
        with (dest/(family+'-RUN-LOG.txt')).open('wb') as log:
            p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);case['pid']=p.pid
            try:case['exitCode']=p.wait(timeout=150)
            except BaseException as e:
                case.update(status='INTERRUPTED_TERMINATION_UNVERIFIED',error=repr(e))
                try:
                    kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20);case['ownedTreeTerminationExit']=kill.returncode;p.wait(timeout=20)
                except BaseException as cleanup:case['cleanupError']=repr(cleanup)
                raise
        case.update(status='RETURNED',returnedAtUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        print(json.dumps({'completed':family,'exitCode':case['exitCode']}),flush=True)
        if case['exitCode']!=0:raise RuntimeError('Acquisition failed; no further arm or repeat')
    normal=True;record['status']='RETURNED'
finally:
    record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['harnessUnchanged']=all(sha(H/p)==v for p,v in pins.items())
    record['runtimeUnchanged']=runtime==runtime_identity(root)
    record['leaseReleased']=normal
    (dest/'EXECUTION.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    if normal:
        assert lock.read_text()==dest.name;lock.unlink()
print(json.dumps({'status':record['status'],'leaseReleased':normal}))
