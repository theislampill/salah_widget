"""Run only R0035's scoped test oracle against isolated mutated authored helpers."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[2]
mutants=[
 ('omit one dirty edge','changed_rectangles.mjs','maxX-minX+1','Math.max(0,maxX-minX)'),
 ('share temporal phase across stars','stellar_replay.mjs','for (const c of id)','for (const c of "shared")'),
 ('align every source crossfade','stellar_replay.mjs','utcMs-star.modes.offsetMs','utcMs'),
 ('ignore painted cloud alpha in the optimized join','prepared_replay.mjs','cloudRGBA:cloud,moonRGBA:moon,atmosphereLinear:gas','cloudRGBA:null,moonRGBA:moon,atmosphereLinear:gas'),
 ('bypass calendar mask in modulation','prepared_replay.mjs','delta[i]*(direct?.[Math.floor(i/3)]??1)','delta[i]'),
 ('omit stale-job fence','live_lab.mjs','&& nativeResultCurrent(source.job,snap)','&& true'),
 ('ignore long frame intervals','frame_guard.mjs','p95>50','p95>999999')]
with tempfile.TemporaryDirectory() as tmp:
    dest=Path(tmp)
    shutil.copytree(root/'tools/r0035',dest/'tools/r0035')
    shutil.copytree(root/'real-sky',dest/'real-sky')
    for relative in ['bright-stars.json','registered-starlight/runtime-manifest.json','registered-starlight/V-nside128.json']:
        asset=Path('vendor/real-sky/data')/relative
        (dest/asset).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy(root/asset,dest/asset)
    (dest/'tests').mkdir()
    test='tests/r0035-replay.test.cjs'
    shutil.copy(root/test,dest/test)
    def run():
        return subprocess.run(['node','--test','--test-reporter=tap',test],cwd=dest,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if run().returncode:
        raise RuntimeError('Unmodified control failed')
    cases=[]
    for label,name,old,new in mutants:
        path=dest/'tools/r0035'/name
        source=path.read_text()
        if source.count(old)!=1:
            raise ValueError(label+' anchor mismatch')
        path.write_text(source.replace(old,new))
        result=run()
        failing=[line for line in result.stdout.splitlines() if line.startswith('not ok ')]
        if result.returncode==0 or not failing:
            raise ValueError(label+' survived or lacked a behavioral failure')
        cases.append({'mutant':label,'failingTests':failing})
        path.write_text(source)
    if run().returncode:
        raise RuntimeError('Restored control failed')
    print(json.dumps({'baselinePassed':True,'mutants':cases,'restoredPassed':True},indent=2))
