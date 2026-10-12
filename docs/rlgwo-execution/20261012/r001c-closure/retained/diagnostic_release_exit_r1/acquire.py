"""Read-only R001C release review acquisition. Writes only this new private worker."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent
RUN = OUT.parent.parent
REV = Path('C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget')
ORIGINAL = Path('C:/Users/theis/Documents/Codex/celestial-startup-repair-20261008/planning-original-21e7a843/docs/rlgwo-execution/20261008')
HEAD = '50e46b7ecfde9c8bea9c0cf00b6017afaf27aab9'
EXPECTED = {
    'AGENTS.md': 'f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948',
    'DESIGN.md': 'f517f7174f5f3214265ace51c74713f57e392bb22312c1c32658b3f0d8b0f16a',
    'OPTICS.md': '8abd464e3d6115c554b0b4b5af719fe56b7ff87bf0acd08392a60d2ac8e4c669',
    'src/native/index.html': 'cbd5e37608dcb502b0824ea5c145cc9ba242d1970e512cd4f9572be414cd818b',
    'index.html': 'c773af444ed1071f9ba6b62b8e635c8d38b1b7f73de995c781ed23c0d307499a',
}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def ref(p):
    p = Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def write(relative, data):
    p = OUT / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists(), str(p)
    if not isinstance(data, bytes):
        data = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    p.write_bytes(data)
    return ref(p)

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

commands = []
def command(args, label):
    started = now()
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    x = subprocess.run(args, capture_output=True, env=env, timeout=45)
    r = {'command': args, 'startedAtUtc': started, 'finishedAtUtc': now(), 'exitCode': x.returncode,
         'stdout': write('raw/' + label + '.stdout', x.stdout), 'stderr': write('raw/' + label + '.stderr', x.stderr)}
    commands.append(r)
    assert x.returncode == 0, r
    return x.stdout

git = ['C:/Program Files/Git/cmd/git.exe', '-C', str(REV)]
started = now()
head = command(git + ['rev-parse', 'HEAD'], 'head').decode().strip()
assert head == HEAD, head
branch = command(git + ['branch', '--show-current'], 'branch').decode().strip()
remote = command(git + ['remote', 'get-url', 'origin'], 'remote').decode().strip()
parents = command(git + ['rev-list', '--parents', '-n', '1', 'HEAD'], 'parents').decode().strip()
status = command(git + ['status', '--porcelain=v1', '--untracked-files=normal'], 'dirty-status').decode()
diff = command(git + ['diff', '--no-ext-diff', '--no-color', '--binary', 'HEAD', '--', 'AGENTS.md', 'DESIGN.md', 'OPTICS.md'], 'documentation-diff')
write('documentation.diff', diff)
command(git + ['diff', '--cached', '--no-ext-diff', '--no-color', '--binary', 'HEAD', '--', 'AGENTS.md', 'DESIGN.md', 'OPTICS.md'], 'documentation-staged-diff')
identity = {'sourceRoot': str(REV), 'baseHead': head, 'branch': branch, 'origin': remote, 'headAndParents': parents,
            'kind': 'EXACT_DIRTY_DOCS_DIFF_ON_VERIFIED_BASE_HEAD', 'deliveredCandidate': False,
            'dirtyStatus': status, 'startedAtUtc': started, 'finishedAtUtc': now()}
write('GIT_IDENTITY.json', identity)
files = []
for f, h in EXPECTED.items():
    v = ref(REV / f)
    assert v['sha256'] == h, v
    v['expectedSha256'] = h
    files.append(v)
    if f != 'index.html':
        write('inputs/final/' + f, (REV / f).read_bytes())
    if f in ('AGENTS.md', 'DESIGN.md', 'OPTICS.md'):
        write('inputs/base/' + f, command(git + ['show', 'HEAD:' + f], 'base-' + f.replace('.', '-')))
write('FINAL_SOURCE_FREEZE.json', {'schema': 'r001c-release-source-freeze/1', 'atUtc': now(), 'identity': identity,
                                  'files': files, 'documentationDiff': ref(OUT / 'documentation.diff'),
                                  'freezeMeaning': 'Exact read bytes only; no commit/native/current07/public equivalence.'})
dag = ORIGINAL / 'CLOSURE_DAG.json'
assert ref(dag)['sha256'] == '9ac372cfcce4df94ee0e678b907e66c131fe49f72cc55106143aa35dbdb0a6e7'
node = next(n for n in load(dag)['nodes'] if n['id'] == 'R001C-RELEASE-REVIEW')
write('ORIGINAL_NODE.json', node)
write('inputs/R001C.md', (ORIGINAL / 'REMAINING_RLGWOs/R001C.md').read_bytes())
write('inputs/R001C.metadata.json', (ORIGINAL / 'metadata/R001C.json').read_bytes())
ledger_bytes = (RUN / 'ACTIVE_LEDGER.json').read_bytes()
write('inputs/ACTIVE_LEDGER.acquired.json', ledger_bytes)
ledger = json.loads(ledger_bytes.decode('utf-8-sig'))
write('R001C_LEDGER_READBACK.json', {'atUtc': now(), 'snapshot': ref(OUT / 'inputs/ACTIVE_LEDGER.acquired.json'),
      'nodes': [{k: n.get(k) for k in ('id','executionStatus','outputReceipts','independentReview','progress')}
                for n in ledger['nodes'] if n['id'].startswith('R001C')],
      'issues': [i for i in ledger['issues'] if i.get('number', i.get('issue')) == 28] if isinstance(ledger['issues'],list) else ledger['issues'].get('28')})

source = (REV / 'src/native/index.html').read_text(encoding='utf-8').splitlines(keepends=True)
ranges = {'parser': (672,672), 'flags-and-reduced-motion': (736,746), 'time-scale': (863,873),
          'lunar-permission': (2693,2708), 'physical-and-force-block': (2805,2840),
          'overlay-and-loop': (3338,3353), 'full-class-and-loop': (3547,3572)}
regions = []
for name, (a,b) in ranges.items():
    s = ''.join(source[a-1:b])
    regions.append({'id':name,'file':'src/native/index.html','startLine':a,'endLine':b,
                    'sha256':hashlib.sha256(s.encode()).hexdigest(),'text':s})
old_maps = [x for x in load(RUN/'workers/release_privacy_diagnostics/SOURCE_MAP.json') if x.get('node') == node['id']]
reassociation = []
for item in old_maps:
    for e in item['sources']:
        b = (REV/e['file']).read_bytes()
        old = e['excerpt'].encode('utf-8')
        count = b.count(old)
        reassociation.append({'old':e,'current':ref(REV/e['file']),'occurrences':count,
                              'exactSourceRegionReused':count == 1,
                              'wholeFileEqualityClaimed':False})
write('SOURCE_FACT_BINDINGS.json', {'source':ref(REV/'src/native/index.html'),'regions':regions,'priorSemanticOwnerReassociation':reassociation})

public = []
for label, endpoint in [('issue-28','repos/theislampill/salah_widget/issues/28'), ('pr-43','repos/theislampill/salah_widget/pulls/43')]:
    raw = command(['C:/Program Files/GitHub CLI/gh.exe','api','--method','GET',endpoint],label)
    obj = json.loads(raw)
    public.append({'kind':label,'method':'GET','endpoint':'https://api.github.com/'+endpoint,
                   'raw':commands[-1]['stdout'],'number':obj['number'],'state':obj['state'],
                   'htmlUrl':obj['html_url'],'updatedAt':obj['updated_at'],'closedAt':obj['closed_at'],
                   'head':obj.get('head',{}).get('sha'),'base':obj.get('base',{}).get('sha'),
                   'draft':obj.get('draft')})
assert public[0]['number'] == 28 and public[0]['state'] == 'open'
urls = [
 ('original-assessment','https://raw.githubusercontent.com/theislampill/salah_widget/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/28-assessment.json'),
 ('original-docs-contract','https://raw.githubusercontent.com/theislampill/salah_widget/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/docs-contract-primary.json'),
 ('original-native-source','https://raw.githubusercontent.com/theislampill/salah_widget/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html')]
urls.extend(('committed-base-'+f.replace('.','-'), 'https://raw.githubusercontent.com/theislampill/salah_widget/'+HEAD+'/'+f)
            for f in ('AGENTS.md','DESIGN.md','OPTICS.md'))
for label, url in urls:
    t = now()
    req = urllib.request.Request(url,headers={'User-Agent':'Codex-R001C-read-only-review'})
    with urllib.request.urlopen(req,timeout=40) as response:
        raw = response.read()
        status_code, actual_url = response.status, response.url
    v = write('public-readback/'+label,raw)
    p = {'kind':label,'method':'GET','url':url,'startedAtUtc':t,'finishedAtUtc':now(),
         'status':status_code,'actualUrl':actual_url,'raw':v}
    if label.startswith('committed-base-'):
        filename = {'committed-base-AGENTS-md':'AGENTS.md','committed-base-DESIGN-md':'DESIGN.md','committed-base-OPTICS-md':'OPTICS.md'}[label]
        p['matchesLocalGitBaseBytes'] = raw == (OUT/'inputs/base'/filename).read_bytes()
        assert p['matchesLocalGitBaseBytes'], p
    public.append(p)
write('PUBLIC_SCOPE_READBACK.json', {'schema':'r001c-read-only-public-evidence/1','atUtc':now(),'readbacks':public,
                                   'candidatePubliclyDelivered':False,'scope':'Existing issue/PR and immutable historical source/evidence only. Dirty docs are not published.'})
write('COMMANDS.json',commands)
write('ACQUISITION.json',{'schema':'r001c-release-review-acquisition/1','startedAtUtc':started,'finishedAtUtc':now(),
      'graph':ref(dag),'node':ref(OUT/'ORIGINAL_NODE.json'),'sourceFreeze':ref(OUT/'FINAL_SOURCE_FREEZE.json'),
      'sourceFacts':ref(OUT/'SOURCE_FACT_BINDINGS.json'),'publicScope':ref(OUT/'PUBLIC_SCOPE_READBACK.json'),
      'commands':ref(OUT/'COMMANDS.json'),'sharedWrites':0,'nativeBuildBrowserTests':0})
print(json.dumps({'acquired':ref(OUT/'ACQUISITION.json'),'head':head,'filesMatched':len(files),
                  'sourceReused':sum(x['exactSourceRegionReused'] for x in reassociation),
                  'publicReads':len(public),'issue28State':public[0]['state']}))
