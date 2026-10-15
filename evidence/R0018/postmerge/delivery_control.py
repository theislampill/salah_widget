"""Bounded authorised R0018 delivery; no qualification replay or desktop APIs."""
from pathlib import Path
import argparse, concurrent.futures, datetime, gzip, hashlib, json, re, subprocess, sys, urllib.request

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
PROD = Path('C:/Users/theis/.codex/worktrees/r0018-readability/salah_widget')
REPO = 'theislampill/salah_widget'
HEAD = '859bdf245ee5e9777a4bb7dd074a9eb3616c6a71'
BASE = 'ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d'
EVIDENCE = '698462f7a3ab69a5ac59ee4c1e61016ca56bb569'
REVIEW = 'eb0bbe44334f427ca6f7cf3917d27086356d6a39'
PUBLIC = 'https://theislampill.github.io/salah_widget/'
sys.path.insert(0, str(PROD / 'tools/cp9'))
from runtime_identity import runtime_identity

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def api(path): return json.loads(subprocess.check_output(['gh', 'api', 'repos/'+REPO+'/'+path]))
def git(*args): return subprocess.check_output(['git', *args], cwd=PROD)
def read(path): return json.loads((CORE/path).read_bytes())
def record(name, value):
    p = HERE/name
    if p.exists(): raise RuntimeError('Retain prior observation; refusing overwrite: '+name)
    p.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')
def get(url):
    request = urllib.request.Request(url, headers={'Accept-Encoding':'identity', 'Cache-Control':'no-cache', 'User-Agent':'R0018-delivery-readback'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.status, response.url, response.read()

def live_target():
    pr=api('pulls/64'); branch=api('branches/main'); rules=api('rules/branches/main'); issue=api('issues/24')
    assert pr['head']['sha']==HEAD and pr['base']['sha']==BASE and branch['commit']['sha']==BASE, 'Approved refs drifted'
    assert pr['state']=='open' and not pr['merged'] and not pr['draft'] and pr['mergeable'] is True and pr['mergeable_state']=='clean'
    assert branch['protected'] is False and branch['protection']['enabled'] is False
    assert branch['protection']['required_status_checks']['enforcement_level']=='off' and not rules
    assert issue['state']=='open' and issue['closed_at'] is None
    checks=api('commits/'+HEAD+'/check-runs')['check_runs']; statuses=api('commits/'+HEAD+'/status')
    assert all(c['status']=='completed' and c['conclusion'] in ('success','neutral','skipped') for c in checks)
    assert all(s['state']=='success' for s in statuses['statuses'])
    assert len(checks)==1 and checks[0]['name']=='measure' and checks[0]['conclusion']=='skipped'
    assert '**SKIPPED**' in pr['body'] and 'Implements #24' in pr['body']
    commits=api('pulls/64/commits'); files=api('pulls/64/files')
    assert [c['sha'] for c in commits]==[HEAD]
    assert {f['filename'] for f in files}=={f['path'] for f in read('candidate-identity.json')['files']}
    closing=r'(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+(?:theislampill/salah_widget)?#24\b'
    assert not re.search(closing, pr['body']) and all(not re.search(closing,c['commit']['message']) for c in commits)
    return {'atUtc':now(),'pr':{k:pr[k] for k in ('number','state','draft','merged','mergeable','mergeable_state','html_url','body')},
            'head':HEAD,'base':BASE,'main':branch['commit']['sha'],'protection':branch['protection'],'activeRules':rules,
            'checks':[{'name':c['name'],'status':c['status'],'conclusion':c['conclusion'],'url':c['html_url']} for c in checks],
            'commitStatuses':statuses['statuses'],'files':[f['filename'] for f in files],
            'issue':{k:issue[k] for k in ('number','state','state_reason','closed_at')}}

def preflight():
    assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain')
    candidate=read('candidate-identity.json'); runtime=runtime_identity(PROD)
    assert candidate['head']==HEAD and candidate['base']==BASE and runtime['treeSha256']==candidate['runtimeSha256']
    for f in candidate['files']:
        data=(PROD/f['path']).read_bytes()
        assert len(data)==f['bytes'] and sha(data)==f['sha256'],f['path']
    identity=read('source-build-currentness.json')
    assert identity['changedRuntimeFiles']==['index.html','offline.html']
    q=read('qualification-index.json'); controls=read('source-tests/summary.json')
    assert len(q['cases'])==38 and len(q['mutants'])==6 and q['complete']
    assert all(c['candidateStatus']=='PASS_SCOPED' and c['opacity1'] and c['minIntendedContrast']>=4.5 for c in q['cases'])
    assert controls['passed']==78 and controls['failed']==0
    objects=[(EVIDENCE,'candidate-identity.json'),(EVIDENCE,'qualification-index.json'),(EVIDENCE,'review-identity.json'),
             (EVIDENCE,'review-packet.json.gz'),(EVIDENCE,'publication/payload-manifest.json'),(REVIEW,'reviews/exact-head-review.md')]
    receipts=[]
    for commit,path in objects:
        url='https://raw.githubusercontent.com/'+REPO+'/'+commit+'/evidence/R0018/'+path
        status,actual,body=get(url); local=(CORE/path).read_bytes()
        assert status==200 and body==local,path
        decoded=gzip.decompress(body) if path.endswith('.gz') else body
        receipts.append({'url':url,'status':status,'sha256':sha(body),'bytes':len(body),'decodedSha256':sha(decoded)})
    assert receipts[3]['decodedSha256']=='93db406f63bd56bf6190094b5a4c40b0a0ef39ed49377549df08128e92e3876d'
    assert receipts[-1]['sha256']=='ddfe0ed12cad9441530d486462ba252b875cb8febd6e77ec3438f4184866dee0'
    result=live_target()
    result.update(status='QUALIFIED_FOR_OWNER_AUTHORISED_NORMAL_MERGE',candidateIdentity=candidate,runtimeFiles=len(runtime['files']),
                  runtimeSha256=runtime['treeSha256'],nativeCases=38,reachedMutants=6,sourceControls=78,intendedMeasurements=912,
                  minimumIntendedContrast=q['minimumIntendedContrast'],publicEvidence=receipts,
                  independentReview='Existing original-scope PASS_SCOPED reaffirmed by the same reviewer at 2026-10-15 11:08 UTC; no replay.',
                  limitations='All original review limitations retained; historical PNGs unavailable, nine Firefox cross-load label offsets unresolved, optional V1 preflight baseline/candidate FAIL, no whole-sky/universal accessibility/additional motion claim.',
                  authority='Human approved exact HEAD/BASE normal merge and subsequent certificate-first delivery/closure in this chat. No automatic issue closure.')
    record('premerge.json',result)
    print(json.dumps({k:result[k] for k in ('status','head','base','runtimeFiles','nativeCases','reachedMutants','sourceControls')}))

def merge():
    pre=json.loads((HERE/'premerge.json').read_bytes())
    assert pre['status']=='QUALIFIED_FOR_OWNER_AUTHORISED_NORMAL_MERGE'
    assert not (HERE/'merge-attempt.json').exists(),'Inspect actual effect before any retry'
    fresh=live_target()
    request={'sha':HEAD,'merge_method':'merge','commit_title':'Merge PR #64: keep default prayer timetable text readable',
             'commit_message':'Deliver the owner-approved exact R0018 timetable CSS repair and canonical generated entries after independent qualification.\n\nImplements #24. Keep the issue open for public native readback and accepted CLOSE-R0018 certificate before intentional completed closure.\n\nCo-Authored-By: Codex <noreply@openai.com>'}
    record('merge-request.json',request)
    record('merge-attempt.json',{'atUtc':now(),'status':'REQUESTING_SINGLE_NORMAL_MERGE','preconditions':fresh,'request':request})
    done=subprocess.run(['gh','api','--method','PUT','repos/'+REPO+'/pulls/64/merge','--input',str(HERE/'merge-request.json')],capture_output=True)
    record('merge-response.json',{'atUtc':now(),'returncode':done.returncode,'stdout':done.stdout.decode('utf-8'),'stderr':done.stderr.decode('utf-8')})
    pr=api('pulls/64'); main=api('git/ref/heads/main'); issue=api('issues/24')
    assert pr['merged'] and pr['merge_commit_sha'], 'Merge not confirmed; inspect recorded attempt, never blind retry'
    m=api('git/commits/'+pr['merge_commit_sha'])
    assert [p['sha'] for p in m['parents']]==[BASE,HEAD], 'Unexpected merge parents'
    assert m['tree']['sha']==pre['candidateIdentity']['tree'] and main['object']['sha']==m['sha']
    assert issue['state']=='open' and issue['closed_at'] is None
    result={'atUtc':now(),'mergeCommit':m['sha'],'parents':[p['sha'] for p in m['parents']],'tree':m['tree']['sha'],
            'main':main['object']['sha'],'mergedAt':pr['merged_at'],'pr':pr['html_url'],'issueState':issue['state'],'passed':True}
    record('merge-verified.json',result);print(json.dumps(result))

if __name__=='__main__':
    command=argparse.ArgumentParser();command.add_argument('operation',choices=['preflight','merge']);args=command.parse_args()
    {'preflight':preflight,'merge':merge}[args.operation]()
