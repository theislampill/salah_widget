"""One named native regression using the unchanged r108 acquisition harness."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
O=Path(__file__).resolve().parent
H=O/'moon-tools-r108'
root=O/'builds/integrated-r29-lunar-rule'
out=O/'native/firefox-lunar-rule-r115'
assert not out.exists()
assert json.loads((root/'RUNTIME.json').read_bytes())['treeSha256']==json.loads((O/'intake/moon-rule-r115-build.json').read_bytes())['runtime']
out.mkdir(parents=True)
dependencies=['tools/cp9/celestial_startup_check.py','tools/cp9/chromium_startup_defaults.py','tools/cp9/celestial_lifecycle_check.py','tools/cp9/celestial_layer_controls.js','tools/cp9/browser_runtime.py','tools/cp9/runtime_identity.py','tests/v1_browser.py']
pins={}
for rel in dependencies:
    data=(H/rel).read_bytes();target=out/'harness-source'/rel
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    pins[rel]=hashlib.sha256(data).hexdigest()
prior=json.loads((O/'native/firefox-retained-native-r108/EXECUTION.json').read_bytes())
assert pins==prior['harnessInputSha256'], 'Acquisition harness changed'
command=[r'${PLAYWRIGHT_PYTHON}','-I','-B',str(H/'tools/cp9/celestial_startup_check.py'),'--root',str(root),'--out',str(out),'--driver-cli',str(O/'capture-driver/cli.js'),'--driver-node',r'${DRIVER_NODE24}','--scene','clear','--entry','iframe','--dpr','2','--modes','new-tab','--duration','150','--persistent-profile','--trace']
exe=r'${ISOLATED_FIREFOX}'
env=dict(os.environ,SALAH_BROWSER='firefox',SALAH_BROWSER_EXECUTABLE=exe,SALAH_CAPTURE_NATIVE_FRAMES='1')
record={'schema':'r0021-named-native-r115/v1','command':command,'browser':exe,'harnessInputSha256':pins,'runtime':json.loads((root/'RUNTIME.json').read_bytes())['treeSha256'],'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED','deadlineSeconds':150,'outerTimeoutSeconds':240,'purpose':'Actual final refinement admission, retained scene and native pixels; not S1 timing or submillisecond cost evidence'}
lock=O/'native-resource.lock'
with lock.open('x') as f:f.write(out.name)
normal=False;p=None
try:
    (out/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
    with (out/'RUN-LOG.txt').open('wb') as log:
        p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        record['pid']=p.pid
        try:
            record['exitCode']=p.wait(timeout=240);normal=True
            record['status']='RETURNED'
        except BaseException as e:
            record.update(status='INTERRUPTED_TERMINATION_UNVERIFIED',error=repr(e))
            try:
                kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20)
                record['ownedTreeTerminationExit']=kill.returncode
                p.wait(timeout=20)
            except BaseException as cleanup:record['cleanupError']=repr(cleanup)
            raise
finally:
    record['returnedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['harnessUnchangedDuringRun']=all(hashlib.sha256((H/rel).read_bytes()).hexdigest()==pin for rel,pin in pins.items())
    record['leaseReleased']=normal
    (out/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
    if normal:
        assert lock.read_text()==out.name
        lock.unlink()
print(json.dumps(record))
sys.exit(record['exitCode'])
