"""Bind actual Pages runtime and delivery routes to the admitted R0017 source."""
import concurrent.futures, datetime, hashlib, json, pathlib, subprocess, sys, urllib.request
B=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r'C:/Users/theis/.codex/worktrees/r0017-moon-readiness/salah_widget')
sys.path.insert(0,str(R/'tools/cp9'))
from runtime_identity import runtime_identity
runtime=runtime_identity(R)
assert runtime['treeSha256']=='5ff3fdf5a13cd3a798addfef972ed9a2c865f87cce531a23847015dcdc8a7d46'
files=set(runtime['files'])
files.update(['README.md','tests/smoke.html','tests/widget-fixture.html','v1/index.html','install.sh','install.ps1',
 'docs/V1_PRESERVATION.md','docs/rlgwo-execution/20261014/R000C/README.md','docs/rlgwo-execution/20261014/R0017_READINESS.md',
 'docs/rlgwo-execution/20261014/R0017_ACCEPTANCE.json','docs/rlgwo-execution/20261014/R0017_EVIDENCE_MANIFEST.json','docs/rlgwo-execution/20261014/R0017_REVIEW.json'])
files.update(p.relative_to(R).as_posix() for p in (R/'presets').rglob('*') if p.is_file())
root='https://theislampill.github.io/salah_widget/'
def fetch(name):
    expected=hashlib.sha256((R/name).read_bytes()).hexdigest()
    row={'path':name,'expectedSha256':expected,'url':root+name}
    try:
        request=urllib.request.Request(row['url'],headers={'Cache-Control':'no-cache','User-Agent':'R0017-delivery-readback'})
        with urllib.request.urlopen(request,timeout=60) as response:
            digest=hashlib.sha256();length=0
            while data:=response.read(1024*1024):digest.update(data);length+=len(data)
            row.update(status=response.status,finalUrl=response.url,bytes=length,sha256=digest.hexdigest(),headers=dict(response.headers))
            row['matches']=response.status==200 and row['sha256']==expected
    except Exception as error:row.update(matches=False,error=str(error))
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(fetch,sorted(files)))
actual={r['path']:r['sha256'] for r in results if r.get('matches') and r['path'] in runtime['files']}
actual_hash=hashlib.sha256(''.join(f'{sha}  {name}\n' for name,sha in sorted(actual.items())).encode()).hexdigest()
report={'schema':'r0017-complete-public-runtime-readback/v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
 'merge':json.loads((B/'merge.json').read_text()),'files':results,'runtimeFiles':len(actual),'runtimeSha256':actual_hash,
 'status':'PASS' if all(r['matches'] for r in results) and actual_hash==runtime['treeSha256'] else 'FAIL',
 'scope':'Actual public HTTP response bytes, all135 runtime files plus documentation/smoke/fixture/V1/installers/presets. No local response substitution.'}
(B/'public-source-readback.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'runtimeFiles':len(actual),'runtimeSha256':actual_hash,'routes':len(results),'failed':[r for r in results if not r['matches']]}))
