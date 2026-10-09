from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, time, urllib.request

R=Path(__file__).resolve().parent
W=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
TARGET='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
def api(path): return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))
main=api('repos/theislampill/salah_widget/git/ref/heads/main')['object']['sha']
assert main==TARGET
pages=api('repos/theislampill/salah_widget/pages/builds/latest')
assert pages['commit']==TARGET and pages['status']=='built'
paths=['index.html','v1/index.html','v1/config.js','v1/VERSION.json','v1/MANIFEST.sha256']
nonce=str(time.time_ns())
def read(path):
    url='https://theislampill.github.io/salah_widget/'+path+'?audit_final='+nonce
    with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'Salah-Authorized-RLGWO-Audit'}),timeout=60) as h:
        raw=h.read();status=h.status;headers={k:h.headers.get(k) for k in ['ETag','Last-Modified','Age','Cache-Control']}
    expected=hashlib.sha256((W/path).read_bytes()).hexdigest();actual=hashlib.sha256(raw).hexdigest()
    assert expected==actual
    return {'path':path,'status':status,'url':url,'expectedSha256':expected,'actualSha256':actual,'headers':headers}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p: rows=list(p.map(read,paths))
report={'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main':main,'pagesBuild':pages,'files':rows,
        'status':'PASS','scope':'Final CDN/currentness guard only. Complete139-file and native browser evidence remains separately recorded; no additional product tests implied.'}
(R/'final-public-currentness.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','main':main,'publicExactFiles':len(rows),'pagesBuild':pages['url']}))
