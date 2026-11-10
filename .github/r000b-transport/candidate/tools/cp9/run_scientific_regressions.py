"""Run the retained scientific suites in a disposable copy, never mutate the oracle."""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'dist' not in p.relative_to(root).parts}
def run(root,out):
    out.mkdir(parents=True,exist_ok=True);source=root/'vendor/real-sky';before=hashes(source);rows=[]
    with tempfile.TemporaryDirectory(prefix='cp9-science-') as temp:
        t=Path(temp)/'science';shutil.copytree(source,t,ignore=shutil.ignore_patterns('__pycache__','dist'));(t/'dist').mkdir()
        commands=[('viewer-build',[sys.executable,'tools/build_cp75_viewer.py']),
                  ('scientific-js',['node','--test','--test-reporter=tap','--test-concurrency=1',*map(str,sorted((t/'tests').glob('*.test.mjs')))]),
                  ('scientific-python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py','-v'])]
        for name,cmd in commands:
            start=time.monotonic()
            with (out/(name+'.log')).open('w',encoding='utf-8') as f:
                p=subprocess.run(cmd,cwd=t,stdout=f,stderr=subprocess.STDOUT,timeout=600,env={**os.environ,'PYTHONUTF8':'1'})
            rows.append({'name':name,'command':cmd,'exitCode':p.returncode,'seconds':time.monotonic()-start});print(name,p.returncode,flush=True)
    unchanged=hashes(source)==before
    result={'status':'PASS' if unchanged and all(r['exitCode']==0 for r in rows) else 'FAIL','oracleUnchanged':unchanged,'commands':rows,'node':subprocess.check_output(['node','--version'],text=True).strip(),'python':sys.version,'scope':'Retained scientific tests and builders in an isolated copy. One documented seal test may skip when the historical checkpoint runtime is not supplied. No scientific source or threshold edits.'}
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if run(a.root,a.output)['status']=='PASS' else 1)
