"""Read exact retained candidate04 evidence. No runtime, shell, browser or build runs."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
EVID = RUN / 'evidence/PR43-review'
CAND = RUN / 'candidates/pr43-r1r2-04'
OLD = RUN / 'candidates/pr43-r1r2-02'
REV = Path('C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget')
TREE = '040192b555fa0db2fad760470ec020a06d86d3e0c7615153062ec5e76c50a2d5'
INDEX = '67e2ff84eb1e7422bfc390f98b641c8e3f93f76a77400401681be10676eb8d3d'
checks = []
inputs = {}

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path):
    raw = path.read_bytes()
    inputs[str(path)] = {'bytes':len(raw),'sha256':sha(raw)}
    return json.loads(raw)
def check(name, condition, **detail):
    checks.append({'name':name,'pass':bool(condition),**detail})
def inventory(root, inv):
    failures=[]
    for relative, pin in inv['files'].items():
        raw=(root/relative).read_bytes()
        if len(raw)!=pin['bytes'] or sha(raw)!=pin['sha256']:failures.append(relative)
    canonical=''.join(f"{inv['files'][k]['sha256']}  {k}\n" for k in sorted(inv['files']))
    check('runtime inventory '+str(root),not failures and sha(canonical.encode())==TREE,
          files=len(inv['files']),mismatches=failures,treeSha256=sha(canonical.encode()))
def state(s):
    s=s or {}
    moon=s.get('moon') or {}; head=s.get('headScene') or {}; sky=s.get('sky') or {}
    return {k:s.get(k) for k in ('at','mainDeclared','settings','settingsOpen','prayerRows','requests')} | {
        'headScene':head,'firstPaint':s.get('firstPaint'),
        'moon':{k:moon.get(k) for k in ('status','visibleSource','current','reason')},
        'sky':{k:sky.get(k) for k in ('status','quality','retained')},
        'moonDetailVisible':(s.get('moonDetail') or {}).get('visible')}

entry_root=EVID/'R1-entry-final-04'
entry_receipt=read(entry_root/'receipt.json')
check('12-case entry receipt complete',entry_receipt.get('complete') is True and len(entry_receipt['cases'])==12)
entry_rows=[]
runtime=None
for case in entry_receipt['cases']:
    name=case['name']; result=read(entry_root/name/'results.json')
    runtime=runtime or result['runtime']
    check('entry pins '+name,result['runtime']==runtime and result['runtime']['treeSha256']==TREE
          and result['entrySha256']==INDEX and result['harnessSha256']==entry_receipt['harnessSha256']
          and result['runtimeUnchanged'] is True and not result['pageErrors'] and not case['errors']
          and case['runtime']==TREE and case['entrySha256']==INDEX and case['exitCode']==0)
    held=result['mode'].startswith('held-')
    if held:
        check('held causal outcome '+name,result['causalPass'] is True and case['causalPass'] is True
              and case['expectedOutcomeObserved'] is True and all(result['controls'].values()))
    else:
        check('compressed observation not causal PASS '+name,result.get('causalPass') is None
              and result['controlledKiBPerSecond']==512)
    after=result['afterRelease']
    check('native consumer recovery '+name,after['mainDeclared'] is True and after['settings'] is True
          and len(after['prayerRows'])==6 and all('—' not in row for row in after['prayerRows'])
          and after['card']['width']==325 and after['card']['height']==530)
    if result['mode']=='held-tail':
        check('native consumers before refinement '+name,result['whileHeld']['mainDeclared'] is True
              and result['whileHeld']['settings'] is True and len(result['whileHeld']['prayerRows'])==6
              and result['heldSettingsInteraction']['open'] is True and result['heldSettingsClosed'] is True)
    if result['mode']=='held-core':
        check('core boundary does not masquerade as boot '+name,result['whileHeld']['mainDeclared'] is False
              and result['whileHeld']['settings'] is False)
    final=result.get('finalRefinement')
    if final:
        check('current full terrain '+name,final['moon']['current'] is True
              and final['moon']['visibleSource']=='refined-terrain' and final['settingsOpen'] is False
              and final['moonDetail']['visible'] is True)
    entry_rows.append({'case':name,'mode':result['mode'],'scene':result['scene'],
                       'boundaryKind':result['boundaryKind'],'heldDecodedBoundary':result['heldDecodedBoundary'],
                       'controls':result.get('controls'),'whileHeld':state(result.get('whileHeld')),
                       'afterRelease':state(after),'finalRefinement':state(final) if final else None})

inventory(CAND,runtime)
inventory(REV,runtime)
entry=(CAND/'index.html').read_bytes()
check('root entry exact',sha(entry)==INDEX and len(entry)==1544863 and len(gzip.compress(entry,mtime=0))==809338)
initial_start=entry.index(b'<script id="moon-initial-code">')
initial_close=entry.index(b'</script>',initial_start)+len(b'</script>')
refinement_start=entry.index(b'<script id="moon-refinement-code">')
refinement_close=entry.index(b'</script>',refinement_start)+len(b'</script>')
boot=entry.index(b'\nboot();\n</script>')
core_start=entry.rfind(b'<script>',initial_close,boot)
packed_match=re.search(rb'const text=atob\("([A-Za-z0-9+/=]+)"\)',entry[initial_start:initial_close])
packed=base64.b64decode(packed_match.group(1),validate=True)
check('compact bytes equal authored generated asset',packed==(CAND/'moon/assets/initial-compact.bin').read_bytes()
      and len(packed)==549170 and len(packed_match.group(1))==732228)
check('head precedes independent core and refinement',initial_close<core_start<boot<refinement_start
      and entry.count(b'<script id="moon-refinement-code">')==1)
for r in entry_rows:
    if r['mode']=='held-tail':
        check('actual tail cut beyond core '+r['case'],r['heldDecodedBoundary']==refinement_start+len(b'<script id="moon-refinement-code">')+128)
    if r['mode']=='held-core':check('actual core cut '+r['case'],r['heldDecodedBoundary']==boot)
source_pins={}
for relative in ('src/native/index.html','real-sky/native-first-paint.mjs','real-sky/native-preview.mjs',
                 'real-sky/native-encoding.mjs','moon/src/moon-detail.mjs','moon/src/surface_v5.mjs',
                 'moon/src/moon-initial.mjs','moon/src/moon-calendar.mjs','moon/src/moon-precision.mjs'):
    current=(CAND/relative).read_bytes();old=(OLD/relative).read_bytes()
    source_pins[relative]=sha(current)
    check('unchanged consumer '+relative,current==old and current==(REV/relative).read_bytes())
old_inventory=read(EVID/'pr43-r1r2-02/build/runtime-1.json')
changed=[p for p,pin in runtime['files'].items() if old_inventory['files'].get(p)!=pin]
check('02 to 04 runtime delta is exactly four existing products',changed==['index.html','moon/BUILD.json','moon/moon-host.js','offline.html'],files=changed)

ordinary_root=EVID/'R1-complete-scene-02'
ordinary_receipt=read(ordinary_root/'receipt.json')
assessment=read(ordinary_root/'ASSESSMENT.json')
baseline_root=EVID/'R1-complete-scene-01'
baseline_receipt=read(baseline_root/'receipt.json')
check('explicit unchanged baseline receipt reuse',sha((baseline_root/'receipt.json').read_bytes())==ordinary_receipt['comparisonBaseline']['receiptSha256']
      ==assessment['baselineReuse']['receiptSha256']
      and 'not a fresh matched pair' in ordinary_receipt['comparisonBaseline']['kind'])
check('six ordinary observations complete',ordinary_receipt['complete'] is True and len(ordinary_receipt['cases'])==2 and len(assessment['rows'])==6)
predicate_scope={}
predicate_source=REV/'tools/cp9/first_complete_scene.py'
predicate_raw=predicate_source.read_bytes()
inputs[str(predicate_source)]={'bytes':len(predicate_raw),'sha256':sha(predicate_raw)}
exec(compile(predicate_raw,str(predicate_source),'exec'),predicate_scope)
ordinary_rows=[]; images=[]
for case in ordinary_receipt['cases']:
    engine=case['case'].split('-')[0]; folder=ordinary_root/case['case']
    result=read(folder/'results.json')
    check('ordinary runtime and raw receipt '+engine,sha((folder/'results.json').read_bytes())==case['receiptSha256']
          and result['runtime']==runtime and result['runtimeUnchanged'] is True and not result['errors']
          and case['exit']==0 and case['runtime']==TREE and result['harnessSha256']==ordinary_receipt['harnessSha256'])
    timing=read(folder/'native-frame-review/timing.json')
    baseline_timing=read(baseline_root/(engine+'-baseline')/'native-frame-review/timing.json')
    base_by_mode={s['mode']:s for s in baseline_timing}
    run_by_mode={r['mode']:r for r in result['runs']}
    for t in timing:
        mode=t['mode']; row=next(r for r in assessment['rows'] if r['engine']==engine and r['mode']==mode)
        frames=read(folder/'native-frame-review'/f'{mode}-frames.json')
        first=t['first']['scene']; baseline=base_by_mode[mode]['first']['scene']['msUpper']
        gaps=[frames[0]['msUpper']]+[b['msUpper']-a['msUpper'] for a,b in zip(frames,frames[1:])
                                  if b['msUpper']<=first['msUpper']]
        original=Path(run_by_mode[mode]['video']+'.frames')/first['file']
        original_raw=original.read_bytes()
        check('original first co-captured scene '+engine+'/'+mode,first==t['first']['moon']==t['first']['stars']
              and first['scene'] is True and first['moon'] is True and first['stars'] is True
              and len(original_raw)==first['bytes'] and first in frames)
        check('ordinary timing arithmetic '+engine+'/'+mode,row['completeMs']==first['msUpper']
              and row['baselineSceneMs']==baseline and row['addedStartupMs']==first['msUpper']-baseline
              and row['acceptedToCompleteMs']==first['msUpper']-t['acceptedMs']
              and abs(row['maximumUncoveredMs']-max(gaps))<1e-6)
        evaluated=predicate_scope['first_complete_scene'](row['receipt'])
        check('fresh pure acceptance '+engine+'/'+mode,evaluated==row['strictAcceptance'])
        images.append({'kind':'ordinary-first-source-frame','engine':engine,'mode':mode,
                       'path':str(original),'bytes':len(original_raw),'sha256':sha(original_raw),
                       'receiptUpperMs':first['msUpper'],'seq':first['seq']})
        ordinary_rows.append({'engine':engine,'mode':mode,'completeMs':first['msUpper'],
                              'acceptedToCompleteMs':row['acceptedToCompleteMs'],
                              'addedStartupMs':row['addedStartupMs'],'maximumUncoveredMs':row['maximumUncoveredMs'],
                              'strict':evaluated,'separateTimingChecks':row['separateTimingChecks']})
check('five strict FAIL one Firefox new-tab PASS',sum(r['strict']['status']=='FAIL' for r in ordinary_rows)==5
      and [(r['engine'],r['mode']) for r in ordinary_rows if r['strict']['status']=='PASS']==[('firefox','new-tab')])
for folder in sorted(entry_root.iterdir()):
    if folder.is_dir():
        for name in ('while-held.png','after-release.png','final-refinement.png'):
            path=folder/name
            if path.exists():
                raw=path.read_bytes();images.append({'kind':'entry-retained-png','case':folder.name,
                                                     'path':str(path),'bytes':len(raw),'sha256':sha(raw)})
for relative in ('docs/real-sky/PR43_REVIEW_REVISION.md','docs/real-sky/pr43-review-evidence/README.md','tools/build_moon.py','tools/cp9/pr43_entry_stream.py'):
    path=REV/relative;raw=path.read_bytes();inputs[str(path)]={'bytes':len(raw),'sha256':sha(raw)}
check('executed entry harness live source pin',inputs[str(REV/'tools/cp9/pr43_entry_stream.py')]['sha256']==entry_receipt['harnessSha256'])
check('previous sealed consumer report preserved',sha((HERE.parent/'pr43-consumer-review/REPORT.json').read_bytes())=='e52b27809b13ec1bb4922264d91d1c11b9f4f77251e5b2a957e92202b58644c7')
result={'schema':'independent-pr43-current04-readback/1','scope':'source/captures/docs; no native browser/build/performance rerun',
        'status':'PASS_OFFLINE_BINDINGS_S1_PARTIAL_FONT_RERUN_PENDING' if all(c['pass'] for c in checks) else 'OFFLINE_CHECK_FAILURES',
        'runtime':TREE,'index':INDEX,'checks':checks,'inputs':inputs,'sourcePins':source_pins,'changedRuntimeFiles':changed,
        'entryRows':entry_rows,'ordinaryRows':ordinary_rows,'images':images,
        'boundaries':{'initialScriptStart':initial_start,'initialScriptEnd':initial_close,
                      'initialScriptBytes':initial_close-initial_start,'headEnd':entry.index(b'</head>')+len(b'</head>'),
                      'coreStart':core_start,'bootBoundary':boot,'refinementStart':refinement_start,
                      'refinementScriptBytes':refinement_close-refinement_start,'compactEncodedBytes':len(packed),
                      'base64Characters':len(packed_match.group(1))}}
(HERE/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],
                  'boundaries':result['boundaries'],'ordinaryRows':ordinary_rows},indent=2))
assert all(c['pass'] for c in checks)
