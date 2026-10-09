"""Summarize retained startup receipts without converting publication into pixels.

Usage: python summarize_celestial_startup.py EVIDENCE_ROOT OUTPUT_DIRECTORY
The fixed case names identify this bounded #33 successor campaign. Original
receipts and source-frame annotations must already exist; nothing is recaptured.
"""
from pathlib import Path
import sys,json,hashlib
from first_complete_scene import first_complete_scene,BUDGETS
E,O=map(Path,sys.argv[1:]);O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
timings=[]
for browser in ['chromium','firefox']:
 before=E/f'ordinary-native-before-{browser}';after=E/f'ordinary-native-task-{browser}'
 old={r['mode']:r for r in read(before/'native-frame-review/timing.json')}
 for stage,d in [('baseline',before),('candidate',after)]:
  raw=read(d/'results.json')
  for r in read(d/'native-frame-review/timing.json'):
   frames=read(d/f'native-frame-review/{r["mode"]}-frames.json')
   first={k:r['first'][k]['msUpper'] for k in ['scene','moon','stars']}
   complete=max(first.values());early=[x for x in frames if x['msUpper']<=complete]
   times=[0]+[x['msUpper'] for x in early];gap=max(b-a for a,b in zip(times,times[1:]))
   receipt={'browser':browser,'observerKnown':True,'evidenceKind':'presented-pixels','frames':[x['file'] for x in early],
    'maximumUncoveredMs':gap,'sceneMs':first['scene'],'moonMs':first['moon'],'starsMs':first['stars'],'moonWarranted':True,'starsWarranted':True,
    'acceptedMs':r['acceptedMs'],'baselineSceneMs':old[r['mode']]['first']['scene']['msUpper']}
   b=BUDGETS[browser]
   row={'case':d.name,'stage':stage,'mode':r['mode'],'runtime':raw['runtime']['treeSha256'],'rawReceiptSha256':sha(d/'results.json'),
    'annotationSha256':sha(d/'native-frame-review/timing.json'),'firstReceiptBoundsMs':first,'acceptedMs':r['acceptedMs'],'publishedMs':r['publishedMs'],
    'firstCompleteUpperMs':complete,'sceneToCompleteObservedMs':complete-first['scene'],'addedStartupMs':first['scene']-receipt['baselineSceneMs'],
    'acceptedToCompleteUpperMs':None if r['acceptedMs'] is None else complete-r['acceptedMs'],'maximumUncoveredMs':gap,
    'receipt':receipt,'strictAcceptance':first_complete_scene(receipt),'timingChecksWithoutCoverage':{
      'navigation':complete<=b['navigationMs'],'acceptedScene':None if r['acceptedMs'] is None else complete-r['acceptedMs']<=b['acceptedMs'],
      'observedContentGap':complete-first['scene']<=b['frameGapMs'],'addedStartup':first['scene']-receipt['baselineSceneMs']<=b['regressionMs']}}
   timings.append(row)
(O/'TIMING.json').write_text(json.dumps({'clock':'native source-frame receipt upper bounds; no getter or PNG requests in the first 15s; no physical-monitor photon claim',
 'coverage':'uncovered intervals are not proof of unchanged displayed pixels; strict predicate is not passed by co-capture', 'rows':timings},indent=2))
stages=[]
for name in ['seal-chromium-lifecycle','seal-firefox-lifecycle','seal-firefox-delayed']:
 raw=read(E/name/'results.json');r=raw['runs'][0];nav=r['navigationAbsolute'];state=r['final'];origin=state['timeOrigin']
 worker=[{**x,'navigationMs':x['absolute']-nav} for x in r['workerEvents']]
 trace=[{**x,'navigationMs':origin+x['at']-nav} for x in state['trace'] if x['stage']!='card-classes']
 initial=r['at15s']['moon']['firstInitial'];resources=state['resources']
 stages.append({'case':name,'runtime':raw['runtime']['treeSha256'],'rawReceiptSha256':sha(E/name/'results.json'),
  'classification':'instrumented causal stages, not ordinary startup latency','firstInitial':initial,'workerEvents':worker,'trace':trace,
  'resources':[x for x in resources if any(t in x['name'] for t in ['native-data','moon/','fixture','fonts.'])],
  'firstPreviewMessageMs':next((x['navigationMs'] for x in trace if x['stage']=='worker-message' and x.get('kind')=='preview'),None),
  'firstResultMessageMs':next((x['navigationMs'] for x in trace if x['stage']=='worker-message' and x.get('kind')=='result' and (x.get('diagnostics') or {}).get('kernel')=='metric-radial-terrain-wasm-mb1'),None),
  'finalMoonApplicationPublicationMs':origin+state['moon']['lastAdoption']['at']+state['moon']['lastAdoption']['totalMs']-nav,
  'finalObservationMs':origin+state['at']-nav,'finalSource':state['moon']['visibleSource'],'currentFinal':state['moon']['current'],
  'lifecycle':r.get('lifecycleControls')})
(O/'STAGES.json').write_text(json.dumps(stages,indent=2))
print(json.dumps([{'browser':r['receipt']['browser'],'mode':r['mode'],'complete':r['firstCompleteUpperMs'],'acceptedGap':r['acceptedToCompleteUpperMs'],'coverageGap':r['maximumUncoveredMs'],'checks':r['timingChecksWithoutCoverage']} for r in timings if r['stage']=='candidate'],indent=2))
