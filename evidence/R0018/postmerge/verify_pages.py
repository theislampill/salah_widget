"""Actual Pages deployment and public byte identities, adapted from R000D."""
from pathlib import Path
import concurrent.futures, hashlib, json, sys, urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parent))
from delivery_control import CORE,HERE,PROD,HEAD,BASE,REPO,PUBLIC,api,git,read,record,now,sha,runtime_identity

def main():
    started=now(); merged=json.loads((HERE/'merge-verified.json').read_bytes()); merge=merged['mergeCommit']
    commit=api('git/commits/'+merge); ref=api('git/ref/heads/main'); pr=api('pulls/64')
    assert [p['sha'] for p in commit['parents']]==[BASE,HEAD]
    assert commit['tree']['sha']==read('candidate-identity.json')['tree']
    assert ref['object']['sha']==merge and pr['merged'] and pr['merge_commit_sha']==merge
    runtime=runtime_identity(PROD); assert runtime['treeSha256']==read('candidate-identity.json')['runtimeSha256']
    assert not git('status','--porcelain')
    pages=api('pages'); build=api('pages/builds/latest'); run=api('actions/runs/38725561959'); jobs=api('actions/runs/38725561959/jobs')
    assert pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy'
    assert build['commit']==merge and build['status']=='built' and not build['error']['message']
    assert run['head_sha']==merge and run['status']=='completed' and run['conclusion']=='success'
    assert jobs['jobs'] and all(j['conclusion']=='success' for j in jobs['jobs'])
    rows=[{'path':p,'url':PUBLIC+p,'kind':'Pages runtime','expectedBytes':v['bytes'],'expectedSha256':v['sha256']} for p,v in runtime['files'].items()]
    extra=['README.md','DESIGN.md','v1/MANIFEST.sha256','v1/index.html','v1/config.js','v1/VERSION.json','install.ps1','install.sh','presets/salah-widget.tablissng.json']
    for p in extra:
        data=(PROD/p).read_bytes();rows.append({'path':p,'url':PUBLIC+p,'kind':'Pages preserved interface or documentation','expectedBytes':len(data),'expectedSha256':sha(data)})
    for f in read('docs/compatibility.json')['interfaces']:
        rows.append({'path':f['path'],'url':'https://raw.githubusercontent.com/'+REPO+'/'+merge+'/'+f['path'],'kind':'Immutable merged compatibility interface','expectedBytes':f['bytes'],'expectedSha256':f['sha256']})
    for p in ('README.md','DESIGN.md'):
        data=(PROD/p).read_bytes();rows.append({'path':p,'url':'https://raw.githubusercontent.com/'+REPO+'/'+merge+'/'+p,'kind':'Immutable merged documentation','expectedBytes':len(data),'expectedSha256':sha(data)})
    def fetch(row):
        result=dict(row)
        try:
            request=urllib.request.Request(row['url'],headers={'Accept-Encoding':'identity','Cache-Control':'no-cache','User-Agent':'R0018-actual-Pages-byte-readback'})
            digest=hashlib.sha256();size=0
            with urllib.request.urlopen(request,timeout=45) as response:
                result.update(httpStatus=response.status,actualUrl=response.url)
                while True:
                    block=response.read(1024*1024)
                    if not block:break
                    digest.update(block);size+=len(block)
            result.update(actualBytes=size,actualSha256=digest.hexdigest())
            result['passed']=result['httpStatus']==200 and size==row['expectedBytes'] and digest.hexdigest()==row['expectedSha256']
        except Exception as exc:result.update(passed=False,error=repr(exc))
        return result
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch,rows):
            results.append(result)
            if len(results)%30==0:print(json.dumps({'read':len(results),'failed':sum(not r['passed'] for r in results)}),flush=True)
    issue=api('issues/24'); finalref=api('git/ref/heads/main')
    assert issue['state']=='open' and issue['closed_at'] is None and finalref['object']['sha']==merge
    report={'schema':'r0018-merged-pages-byte-delivery/v1','startedUtc':started,'finishedUtc':now(),
            'driverSha256':sha(Path(__file__).read_bytes()),'helperSha256':sha((HERE/'delivery_control.py').read_bytes()),
            'merge':merged,'runtimeFiles':len(runtime['files']),'runtimeSha256':runtime['treeSha256'],
            'changedRuntimeFiles':['index.html','offline.html'],'unchangedRuntimeFiles':133,
            'pages':{k:pages.get(k) for k in ('status','source','build_type','html_url')},'build':build,
            'actionsRun':{k:run[k] for k in ('id','head_sha','status','conclusion','html_url','created_at','updated_at')},
            'jobs':[{k:j[k] for k in ('id','name','conclusion','completed_at','html_url')} for j in jobs['jobs']],
            'results':results,'objectsRead':len(results),'passed':all(r['passed'] for r in results),'failed':[r['url'] for r in results if not r['passed']],
            'issueAtDelivery':{k:issue[k] for k in ('number','state','state_reason','closed_at')},
            'scope':'Actual HTTP bytes for all 135 runtime files, all three frozen V1 payloads plus manifest, public docs/install/preset, and 19 immutable compatibility interfaces. Native public timetable pixels are a separate obligation.'}
    record('merged-pages-readback.json',report)
    print(json.dumps({k:report[k] for k in ('objectsRead','passed','failed','runtimeFiles','runtimeSha256')}),flush=True)
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
