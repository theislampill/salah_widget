"""Seal this bounded independent review after fresh offline verification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
check=read('CHECKS.json');font=read('FONT_READBACK.json');pub=read('PUBLICATION_BINDINGS.json')
base=read('BASELINE_BINDING.json');views=read('VIEWS.json')
assert all(x['pass'] for r in (check,font,pub) for x in r['checks'])
assert base['passed'] and views['count']==32
for d in pub['docs']:
    assert sha((HERE/d['reviewedCopy']).read_bytes())==d['sha256']
    assert sha(Path(d['path']).read_bytes())==d['sha256'],'Publication wording changed after review'
status='DRAFT_REVIEW_RETURNED_CURRENT04_R1_S1_PARTIAL_R2_PASS_SCOPED'
report={
    'schema':'independent-pr43-current04-supplement/1',
    'status':status,
    'atUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'Fresh current04 actual-entry/ordinary evidence and publication wording; newly returned current18 font metric/pixel binding. No repeat of the sealed broad candidate02 review.',
    'runtimeTreeSha256':check['runtime'],
    'sourceIndexSha256':check['index'],
    'candidate':'C:/Users/theis/Documents/Codex/salah-rlgwo-execution-20261009/candidates/pr43-r1r2-04',
    'rootRevision':'C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget',
    'previousReport':{'path':str(HERE.parent/'pr43-consumer-review/REPORT.json'),
                      'sha256':'e52b27809b13ec1bb4922264d91d1c11b9f4f77251e5b2a957e92202b58644c7',
                      'runtime':'d76eab2a27a00e23d786d40d2a2a7a6b57cc36e94921eda4344aa7ecba08b8ed',
                      'disposition':'UNCHANGED_SEALED; no retroactive current04 green'},
    'newActionableFindings':[],
    'retainedFindings':[
        {'id':'PR43-R1','severity':'P1','disposition':'BOUNDED_COMPACT_CORRECTION_ACCEPTABLE; CRITICAL_PATH_QUALIFICATION_PARTIAL',
         'source':'tools/build_moon.py','lines':[86,110],
         'mechanism':'549170 encoded compact bytes/732228 base64 characters in head still precede native core execution. Current held-tail control withholds independent refinement, not the compact head.',
         'ordinaryDisposition':'five strict FAIL, one Firefox new-tab focused predicate PASS; added startup and frame coverage remain material',
         'next':'Keep partial qualification in the Draft record. A root-owned qualified actual-parent/frame-coverage/callback-cost operation remains necessary for S1 acceptance; no additional run performed here.'},
        {'id':'R0022-L1/S10','disposition':'OPEN_UNCHANGED','mechanism':'Grey wash and left spotlight remain visible in first/head/final current04 night captures. Attribution already complete; no ablation/display adoption repeated.'}
    ],
    'specCompliance':{
        'actualEntry':'PASS_SCOPED eight day/night held/core causal controls; four compressed observations are not causal/performance PASS',
        'firstScenePreservation':'Night Moon/catalogue before core and current refined-terrain finals bound; placeholders at held core expected',
        'strictS1':'PARTIAL: five strict failures, single-mode focused Firefox new-tab pass, older main reused rather than fresh matched pair',
        'currentR2':'PASS_SCOPED_18_VARIANTS; returned PARTIAL_NATIVE_SCOPE excludes wider renderer/startup acceptance',
        'publicationWording':'PASS_SCOPED exact reviewed document copies disclose dependencies, failures, reuse and open boundaries'},
    'codeQuality':{
        'newConsumerRegression':'No new demonstrated defect within the current transport/font/pixel supplement',
        'nativeTypographyOwner':'Byte-identical to sealed candidate02; fresh current18 admission binds all six ordered scripts and canonical runtime',
        'decoderEquivalence':'Separate independent worker review; not duplicated or certified by this consumer supplement',
        'documentationScope':'No unsupported closure/current-execution claim found in exact reviewed versions'},
    'entry':{'receipt':str(HERE.parents[2]/'evidence/PR43-review/R1-entry-final-04/receipt.json'),
             'cases':12,'causalHeldPass':8,'compressedObservations':4,'pageErrors':0,
             'boundaries':check['boundaries'],
             'finalRefinementMs':{'chromium':26800.59999999404,'firefox':84769},
             'limits':'Held durations are not ordinary refinement latency; no compact-head withholding control or all-intermediate-frame proof'},
    'ordinaryRows':check['ordinaryRows'],
    'baselineReuse':base,
    'font':{'receipt':str(HERE.parents[2]/'evidence/PR43-review/R2-font-final-04/receipt.json'),
            'cases':18,'engines':['chromium','firefox'],'returnedStatus':'PARTIAL_NATIVE_SCOPE','driverSealSha256':font['driverSealSha256'],
            'stableVariants':16,'stableAdditionalMeasurements':0,'explicitAdditionalMeasurements':1,
            'maximumNaturalControlRangeBoxDelta':max(r['metric'].get('maximumNaturalControlRangeBoxDelta',0) for r in font['rows']),
            'splitFace':'Both reach two fits from one while held, before Inter finishes; Firefox already refit in arrival capture; no forced clear',
            'pixelScope':'Ten natural current04 original PNGs preserve relevant rail clearance, label baseline and hero alignment',
            'oldRed':'Original/intermediate failures remain earlier evidence, not rerun here',
            'cacheLimit':'Chromium cache events recorded; Firefox empty attribution does not prove font cache hit'},
    'reviewedDocs':pub['docs'],
    'checks':{'sourceCapture':len(check['checks']),'currentFont':len(font['checks']),'publicationCopy':len(pub['checks']),
              'allPass':True,'viewedOriginalImages':views['count'],'scopedPortableCopies':len(pub['scopedPortableCopies']),
              'kind':'Offline readback assertions, not extra product tests or independent browser executions',
              'helperAssumptionFailuresRetained':['CHECKS_INITIAL_HELPER_ASSUMPTIONS.json','FONT_READBACK_INITIAL_HELPER_ASSUMPTIONS.json']},
    'commands':[{'script':n,'runner':'Python311 -I -S -B','exitCode':0} for n in ('verify_current04.py','font_readback.py','publication_bindings.py')],
    'unverifiedGates':['strict S1 including missing frame coverage/callback costs/actual extension parent',
                       'latency distribution; one ordinary observation per mode only','all intermediate frames/motion/every opacity or phase/currentness boundary',
                       'L1/S10 appearance acceptance','native Mac/Apple Bash and broader platform gates','release/merge/issue closure'],
    'effects':{'onlyWriteDirectory':str(HERE),'browserRuns':0,'builds':0,'nativeInstallerRuns':0,'performanceOrTerrainReruns':0,
              'sourceOrSharedLedgerWrites':0,'GitHubEffects':0,'subagents':0},
    'next':'Root joins this exact supplement and separate decoder review for Draft publication, retaining R1/S1 PARTIAL and L1/S10 OPEN. Publication, merge and node closure remain distinct.'
}
(HERE/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
files={}
for p in sorted(HERE.iterdir()):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes();files[p.name]={'bytes':len(b),'sha256':sha(b)}
seal={'schema':'independent-pr43-current04-seal/1','atUtc':datetime.now(timezone.utc).isoformat(),
      'status':status,'files':files}
(HERE/'SEAL.json').write_text(json.dumps(seal,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':status,'reportMdSha256':files['REPORT.md']['sha256'],
                  'reportJsonSha256':files['REPORT.json']['sha256'],'sealSha256':sha((HERE/'SEAL.json').read_bytes()),
                  'sealedFiles':len(files)},indent=2))
