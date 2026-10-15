"""Exact merged tree, Pages deployment and actual published-byte readback."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request

BASE = Path(__file__).resolve().parent
ROOT = Path('C:/Users/theis/.codex/worktrees/r000d-docs/salah_widget')
M = 'ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d'
B = '06772824a159cd2bc42a1d9f79a3fb22fa46e49d'
H = '94b5ddf5d61feb4c166050bed1460c6940eb20ad'
REPO = 'theislampill/salah_widget'
PUBLIC = 'https://theislampill.github.io/salah_widget/'

def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+path]))

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    out=BASE/'delivery/merged-pages-readback.json'
    if out.exists(): raise RuntimeError('Existing delivery observation must not be overwritten')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert git('rev-parse','HEAD').decode().strip()==M and not git('status','--porcelain')
    commit=api('git/commits/'+M);main_ref=api('git/ref/heads/main');pr=api('pulls/63')
    assert [p['sha']for p in commit['parents']]==[B,H]
    assert commit['tree']['sha']==git('rev-parse',H+'^{tree}').decode().strip()
    assert main_ref['object']['sha']==M and pr['merged'] and pr['merge_commit_sha']==M
    diff=git('diff','--numstat',B,M).decode().splitlines()
    assert sorted(diff)==['7\t0\tREADME.md','9\t0\tDESIGN.md']
    assert not git('diff','--name-only',B,M,'--','v1','src','config.js','tests','index.html','offline.html')
    manifest=json.loads((BASE/'qualification/runtime-identity.json').read_text())
    for path,expected in manifest['files'].items():
        data=(ROOT/path).read_bytes()
        assert len(data)==expected['bytes'] and sha(data)==expected['sha256'],path
    pages=api('pages');build=api('pages/builds/latest');run=api('actions/runs/38673297933')
    assert pages['source']=={'branch':'main','path':'/'}
    assert build['commit']==M and build['status']=='built' and not build['error']['message']
    assert run['head_sha']==M and run['status']=='completed' and run['conclusion']=='success'
    jobs=api('actions/runs/38673297933/jobs')
    assert all(j['conclusion']=='success'for j in jobs['jobs'])
    rows=[{'path':path,'url':PUBLIC+path,'kind':'Pages runtime','expectedSha256':v['sha256'],'expectedBytes':v['bytes']}for path,v in manifest['files'].items()]
    for path in ('README.md','DESIGN.md','v1/index.html'):
        data=(ROOT/path).read_bytes()
        rows.append({'path':path,'url':PUBLIC+path,'kind':'Pages documentation'if path.endswith('.md')else'Pages frozen V1 representative','expectedSha256':sha(data),'expectedBytes':len(data)})
    for ref in (M,'main'):
        for path in ('README.md','DESIGN.md'):
            data=(ROOT/path).read_bytes()
            rows.append({'path':path,'url':'https://raw.githubusercontent.com/'+REPO+'/'+ref+'/'+path,'kind':'Published Git documentation '+ref,'expectedSha256':sha(data),'expectedBytes':len(data)})
    def read(row):
        result=dict(row)
        try:
            req=urllib.request.Request(row['url'],headers={'Cache-Control':'no-cache','Accept-Encoding':'identity','User-Agent':'R000D-postmerge-delivery-readback'})
            digest=hashlib.sha256();size=0
            with urllib.request.urlopen(req,timeout=60)as response:
                result.update(httpStatus=response.status,actualUrl=response.url)
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    digest.update(chunk);size+=len(chunk)
            result.update(actualBytes=size,actualSha256=digest.hexdigest())
            result['passed']=result['httpStatus']==200 and size==row['expectedBytes'] and digest.hexdigest()==row['expectedSha256']
        except Exception as exc:result.update(passed=False,error=repr(exc))
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(read,rows))
    issue=api('issues/13')
    report={'schema':'r000d-merged-pages-byte-delivery/v1','startedUtc':started,'finishedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'merge':{'sha':M,'parents':[p['sha']for p in commit['parents']],'tree':commit['tree']['sha'],'main':main_ref['object']['sha'],'mergedAt':pr['merged_at'],'diffNumstat':diff},
            'runtime':{'files':len(manifest['files']),'treeSha256':manifest['treeSha256'],'localMismatches':[],'authoredConfigurationTestsGeneratedAndFrozenV1Unchanged':True},
            'pages':pages,'build':build,'actionsRun':{'id':run['id'],'headSha':run['head_sha'],'status':run['status'],'conclusion':run['conclusion'],'url':run['html_url']},
            'jobs':[{'name':j['name'],'conclusion':j['conclusion'],'completedAt':j['completed_at'],'url':j['html_url']}for j in jobs['jobs']],
            'issueAtDelivery':{k:issue[k]for k in('number','state','state_reason','closed_at','comments')},'objectsRead':len(results),'results':results,
            'passed':all(r['passed']for r in results),'failed':[r['url']for r in results if not r['passed']],
            'scope':'Actual HTTP bytes, not merely commit/command status. Representative native public consumer remains separately required.'}
    out.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:report[k]for k in('objectsRead','passed','failed','merge','runtime')}))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
