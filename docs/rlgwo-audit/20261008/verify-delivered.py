from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,subprocess,json,hashlib,time,datetime,sys
R=Path(__file__).parent;W=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget');repo='theislampill/salah_widget'
release=json.loads((R/'release.json').read_text());merge=release['mergeCommit'];pin=json.loads((W/'docs/real-sky/evidence/startup-cloud-20261007/final-v49/CANDIDATE_RUNTIME.json').read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
builds=[]
for attempt in range(90):
 p=subprocess.run(['gh','api',f'repos/{repo}/pages/builds/latest'],capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stderr
 b=json.loads(p.stdout);builds.append({'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':b});save(R/'pages-poll.json',builds)
 if b['commit']==merge and b['status']=='built':break
 if b['commit']==merge and b['status']=='errored':raise RuntimeError(b)
 print('Pages',b['commit'],b['status'],flush=True);time.sleep(10)
else:raise RuntimeError('Exact Pages deployment did not finish in15minutes')
checks={k:v['sha256'] for k,v in pin['files'].items()}
checks.update({'v1/index.html':'99d930297deb2755205930c7850b89584e03f431ced0671638071162732ef766','v1/config.js':'f169d26ad015d3fcb6b5782fde43a83e0f31275bbbeb80c94c51a6c3bc4aa56d','v1/VERSION.json':'dda56a94c56ec6295e8eb9af890e6913878731385cc180c250fff3d532b2d330','v1/MANIFEST.sha256':'aa4bfcbc54f838e93d8ab41e58845efd753fcea80e8ebef3a784acf304e6a4cb'})
def verify(pair):
 path,expected=pair;url='https://theislampill.github.io/salah_widget/'+path;attempts=[]
 for n in range(3):
  q=requests.get(url,params={'pr42verify':merge,'retry':n},headers={'Cache-Control':'no-cache'},timeout=120);actual=hashlib.sha256(q.content).hexdigest();attempts.append({'status':q.status_code,'sha256':actual,'bytes':len(q.content),'date':q.headers.get('Date'),'age':q.headers.get('Age'),'etag':q.headers.get('ETag')})
  if q.status_code==200 and actual==expected:return {'path':path,'url':url,'expected':expected,'attempts':attempts,'passed':True}
  time.sleep(2)
 return {'path':path,'url':url,'expected':expected,'attempts':attempts,'passed':False}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(verify,checks.items()))
failed=[x for x in rows if not x['passed']];save(R/'public-runtime.json',{'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mergeCommit':merge,'pagesBuild':b,'runtime':pin,'checks':rows,'failures':failed})
assert not failed,failed
p=subprocess.run([sys.executable,'tools/verify_v1.py','--check-pages','--negative-control'],cwd=W,capture_output=True,text=True,encoding='utf-8');(R/'v1-verifier.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0
print('PUBLIC_BYTES_VERIFIED',len(rows),'exact files; Pages',b['url'],flush=True)
