"""Serial issue-only wrapper: immutable per-attempt inputs, bounded child, no retries."""
import argparse, datetime, hashlib, importlib.metadata, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def seal(out,engine,command):
    files={}
    for p in sorted((BASE/'package').rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(BASE/'package');data=p.read_bytes();copy=out/'executed-fixture'/rel
        copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(data);files[rel.as_posix()]=sha(data)
    exe=Path(os.environ['SALAH_BROWSER_EXECUTABLE'])
    manifest=dict(atUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceCommit='06772824a159cd2bc42a1d9f79a3fb22fa46e49d',
       files=files,command=command,engine=engine,executable=str(exe),executableSha256=sha(exe.read_bytes()),python=sys.executable,
       playwright=importlib.metadata.version('playwright'),source={r:sha((ROOT/r).read_bytes()) for r in ['index.html','src/native/index.html','config.js','tools/cp9/browser_runtime.py']})
    dump(out/'execution-manifest.json',manifest)
def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,choices=['chromium','firefox']);p.add_argument('--select',nargs='+',required=True);p.add_argument('--revision',default='r1');a=p.parse_args()
    executable={'chromium':'chromium-1223/chrome-win64/chrome.exe','firefox':'firefox-1522/firefox/firefox.exe'}[a.engine]
    os.environ['SALAH_BROWSER_EXECUTABLE']=str(Path(os.environ['LOCALAPPDATA'])/'ms-playwright'/executable)
    for name in a.select:
        out=BASE/'native'/a.engine/(name+'-'+a.revision)
        if out.exists():raise RuntimeError('Never overwrite an attempt: '+str(out))
        # Driver owns fresh output creation; write input custody to a sibling first.
        inputs=out.with_name(out.name+'-input');inputs.mkdir(parents=True,exist_ok=False)
        cmd=[sys.executable,'-I','-B',str(BASE/'package/tools/qa/run_r000d_transport.py'),'--root',str(ROOT),'--out',str(out),
             '--expected-index',sha((ROOT/'index.html').read_bytes()),'--browser',a.engine,'--run','r000d-'+a.engine+'-'+name+'-'+a.revision]
        if name.startswith('D-'):cmd+=['--case',name]
        else:
            cmd+=['--stage',name]
            if not name.startswith('weather-'):cmd+=['--retry-clock','wall-offset']
        seal(inputs,a.engine,cmd)
        print(json.dumps({'starting':name,'engine':a.engine}),flush=True)
        try:
            result=subprocess.run(cmd,capture_output=True,timeout=300)
            (inputs/'stdout.txt').write_bytes(result.stdout);(inputs/'stderr.txt').write_bytes(result.stderr)
            dump(inputs/'process-result.json',dict(exitCode=result.returncode,completedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        except subprocess.TimeoutExpired as error:
            dump(inputs/'process-result.json',dict(status='OUTER_WATCHDOG',timeoutSeconds=300))
            raise
        print(result.stdout.decode(errors='replace').strip(),flush=True)
        if result.returncode:
            print(result.stderr.decode(errors='replace'),flush=True);return result.returncode
    return 0
if __name__=='__main__':raise SystemExit(main())
