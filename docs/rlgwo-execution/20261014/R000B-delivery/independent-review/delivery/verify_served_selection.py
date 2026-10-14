"""Independent bounded R000B Pages readback. No browser or public writes."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, time, urllib.error, urllib.request
E=Path(r'C:\workspace\ai\r000b-execution-20261014')
R=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
O=E/'independent-review/delivery/served-selection'
H='573dc2b15af37b5d32faa4364f3e653b65431dfc'
B='16658749209e0c567f49a3fc9dc855f665afa6e4'
M='763a460e98dc23c7f0e95bf346274f1685b3c654'
T='3656edba44b79ab7216c8cbf3546f4fe085bee9a'
V='885348adc26f9db468b39b65ba2c07cf130d26ca'
U='https://theislampill.github.io/salah_widget/'
A='https://api.github.com/repos/theislampill/salah_widget'
sha=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())
def bind(path):
    b=path.read_bytes()
    return {'path':str(path),'bytes':len(b),'sha256':sha(b)}
assert not O.exists(),'Retain earlier readback before any retry.'
manifest_path=E/'public-projection/manifest.json'
assert sha(manifest_path.read_bytes())=='54d4272917e4e68fe42bc2e07ee2b3dee49552cbba6e559413e9d7ff6d593bc5'
manifest=json.loads(manifest_path.read_bytes())
candidate_path=E/'public-projection/recovery-handoff-source/flash-counterexample/candidate.json'
pin=next(x for x in manifest['files'] if x['path']=='recovery-handoff-source/flash-counterexample/candidate.json')
assert sha(candidate_path.read_bytes())==pin['sha256'] and candidate_path.stat().st_size==pin['bytes']
runtime=json.loads(candidate_path.read_bytes())['runtime']
review_path=E/'publication-review/public-head-review.json'
assert sha(review_path.read_bytes())=='aedec4cb0f977798c88d035cd815b28a7b68ba37db3b8bd8e33a8952a51bcdb3'
review=json.loads(review_path.read_bytes())
root_path=E/'delivery/source-docs-readback.json'
assert sha(root_path.read_bytes())=='8eab293e491b0266a7787433d61efdfeeb2b3d604db2c5af43b77cd6664581c9'
root=json.loads(root_path.read_bytes())
assert root['status']=='PASS' and root['mergeCommit']==M and root['tree']==T and root['approvedHead']==H and root['reviewedBase']==B
expected=dict(runtime['files'])
for row in review['sourceFiles']:
    if row['path'] in expected:
        assert expected[row['path']]['sha256']==row['sha256'] and expected[row['path']]['bytes']==row['bytes']
    expected[row['path']]={'sha256':row['sha256'],'bytes':row['bytes']}
v1=subprocess.run(['git','show',M+':v1/index.html'],cwd=R,capture_output=True,check=True).stdout
expected['v1/index.html']={'sha256':sha(v1),'bytes':len(v1)}
assert expected['v1/index.html']['sha256']=='99d930297deb2755205930c7850b89584e03f431ced0671638071162732ef766'
assert len(runtime['files'])==135 and runtime['treeSha256']=='c2753a21c337ff0bc09cea05f15bfc7729dcc2295a924c11284399fdab6e9ea2'
assert len(expected)==149 and len(root['httpFiles'])==149
assert {r['path'] for r in root['httpFiles']}==set(expected)
for r in root['httpFiles']:
    x=expected[r['path']]
    assert r['exact'] is True and r['httpStatus']==200 and r['url']==U+r['path'] and r['resolvedUrl']==r['url'],r
    assert r['expectedSha256']==r['sha256']==x['sha256'] and r['expectedBytes']==r['bytes']==x['bytes'],r
assert sum(r['bytes'] for r in root['httpFiles'])==root['totalBytesRead']==215200461
assert root['mainAfter']==M and root['pagesBuild']['commit']==M and root['pagesBuild']['status']=='built'
assert root['pagesWorkflow']['id']==38631069804 and root['pagesWorkflow']['head_sha']==M and root['pagesWorkflow']['conclusion']=='success'
O.mkdir()
report={'schema':'r000b-independent-served-source-selection/v1','status':'RUNNING','startedAtUtc':now(),
'mergeCommit':M,'sourceTree':T,'runtimeTreeSha256':runtime['treeSha256'],
'rootReceiptAudit':{'status':'PASS','uniquePaths':149,'allRuntimePaths':135,'allReviewedPrPaths':17,
'totalBytes':215200461,'missing':[],'unexpected':[],'mismatches':[],
'method':'All parent receipt entries reconciled to the immutable packet runtime manifest, independently reviewed 17-file pins and frozen V1 Git bytes; exact URL/status/count/hash checked.'},
'selection':[],'api':[],'bindings':[bind(p) for p in [root_path,manifest_path,candidate_path,review_path,E/'delivery/verify_public_delivery.py']],
'scope':'Fresh independent unauthenticated byte readback of 11 relevant served source/document files, plus public reference/deployment/issue state. Remaining 138 files are accepted from the fully reconciled parent 149-file acquisition receipt; no claim that this reviewer independently downloaded all149.',
'browserExecuted':False}
save(O/'receipt.json',report)
def acquire(key,url,relative):
    attempts=[]
    for attempt in range(1,3):
        row={'attempt':attempt,'url':url,'method':'GET','authorizationSent':False,'startedAtUtc':now()}
        try:
            req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity','User-Agent':'R000B-independent-delivery-readback','Accept':'application/vnd.github+json' if url.startswith(A) else '*/*'})
            with urllib.request.urlopen(req,timeout=30) as res:
                data=res.read()
                row.update(status=res.status,finalUrl=res.url,bytes=len(data),sha256=sha(data),headers=dict(res.headers),result='ACQUIRED')
            target=O/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            attempts.append(row)
            save(O/(relative+'.attempts.json'),attempts)
            return data,{'key':key,'url':url,'storedPath':str(target),'attempts':attempts}
        except Exception as exc:
            row.update(result='ACQUISITION_FAILURE',error=repr(exc),status=getattr(exc,'code',None))
            attempts.append(row);save(O/(relative+'.attempts.json'),attempts)
            if attempt==2:raise
            time.sleep(1)
def api(key,suffix):
    b,row=acquire(key,A+suffix,'api/'+key+'.json');report['api'].append(row);save(O/'receipt.json',report)
    return json.loads(b)
try:
    before=api('main-before','/git/ref/heads/main');assert before['object']['sha']==M
    pr=api('pr','/pulls/61');assert pr['merged'] and pr['head']['sha']==H and pr['merge_commit_sha']==M and not pr['draft']
    run=api('pages-run','/actions/runs/38631069804');assert run['head_sha']==M and run['status']=='completed' and run['conclusion']=='success'
    evidence=api('evidence-ref','/git/ref/heads/codex/r000b-evidence-20261014');assert evidence['object']['sha']==V
    issue=api('issue11','/issues/11');assert issue['state']=='open' and sha(issue['body'].encode())=='f83c4f3516b63a068dc768b16d64e14cb970cf41ea074e240e73dcffda6d0bcc'
    selected=['index.html','src/native/index.html','real-sky/native-host.mjs','real-sky/native-sky.js','config.js','README.md','DESIGN.md','HANDOFF.md','v1/index.html','docs/rlgwo-execution/20261014/R000B/README.md','docs/rlgwo-execution/20261014/R000B/reference.json']
    def read(path):
        b,row=acquire(path,U+path,'files/'+path)
        row.update(path=path,expected=expected[path],actual={'sha256':sha(b),'bytes':len(b)},
                   exact=len(b)==expected[path]['bytes'] and sha(b)==expected[path]['sha256'] and row['attempts'][-1]['status']==200 and row['attempts'][-1]['finalUrl']==U+path)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(read,selected):
            report['selection'].append(row);save(O/'receipt.json',report)
            assert row['exact'],row
    after=api('main-after','/git/ref/heads/main');assert after['object']['sha']==M
    report.update(status='PASS',completedAtUtc=now(),selectedFiles=len(selected),
        selectedBytes=sum(x['actual']['bytes'] for x in report['selection']),
        publicState={'mainBefore':M,'mainAfter':M,'prMerged':True,'sourceHead':H,'evidenceRef':V,'issue11':'open','pagesRun':38631069804,'pagesRunConclusion':'success'},
        totalAttempts=sum(len(x['attempts']) for x in report['api']+report['selection']),
        failedAcquisitions=sum(a['result']!='ACQUIRED' for x in report['api']+report['selection'] for a in x['attempts']))
except Exception as exc:
    report.update(status='FAIL',error=repr(exc),completedAtUtc=now());save(O/'receipt.json',report);raise
save(O/'receipt.json',report)
files=[]
for p in sorted(O.rglob('*')):
    if p.is_file():files.append(bind(p))
save(O.parent/'served-selection-files.json',{'files':files})
print(json.dumps({'status':report['status'],'selectedFiles':report['selectedFiles'],'selectedBytes':report['selectedBytes'],'totalAttempts':report['totalAttempts'],'failedAcquisitions':report['failedAcquisitions'],'receipt':bind(O/'receipt.json'),'filesManifest':bind(O.parent/'served-selection-files.json')}))
