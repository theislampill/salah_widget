from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, urllib.request

R=Path(__file__).resolve().parent
W=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
p=json.loads((R/'evidence-publication-01.json').read_text())
sha=p['commit']; prefix='docs/rlgwo-audit/20261008'
tree=subprocess.check_output(['git','rev-parse',f'{sha}:{prefix}'],cwd=W,text=True).strip()
remote=json.loads(subprocess.check_output(['gh','api',f'repos/theislampill/salah_widget/git/trees/{tree}?recursive=1'],text=True,encoding='utf-8'))
assert remote.get('truncated') is False
remote_blobs={x['path']:x['sha'] for x in remote['tree'] if x['type']=='blob'}
local={}
for line in subprocess.check_output(['git','ls-tree','-r',tree],cwd=W,text=True,encoding='utf-8').splitlines():
    meta,path=line.split('\t',1);local[path]=meta.split()[2]
assert local==remote_blobs and len(local)==p['files']
samples=['EVIDENCE_MANIFEST.json','release.json','primary-reconciliation.json','workers/E/retained-install/final-r0014-ps51.txt',
         'workers/D/native-three-primary/15-settings-display-close-session.png','primary-native-F2-firefox/mobile-focus.png']
def fetch(path):
    url=f'https://raw.githubusercontent.com/theislampill/salah_widget/{sha}/{prefix}/{path}'
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Salah-Authorized-RLGWO-Audit'}),timeout=60) as h:
        raw=h.read();status=h.status
    expected=(R/'public-evidence-03'/prefix/path).read_bytes()
    assert raw==expected
    return {'path':path,'url':url,'status':status,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'exact':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(fetch,samples))
report={'commit':sha,'subtree':tree,'allPublishedBlobIdentitiesVerified':len(local),'rawSamples':rows,'status':'PASS'}
(R/'public-evidence-readback.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':sha,'verifiedBlobs':len(local),'raw200ExactSamples':len(rows)}))
