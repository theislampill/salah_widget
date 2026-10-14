"""Retain observed failures; no numerical or coverage threshold changes."""
import collections, hashlib, json, pathlib, sys
R=pathlib.Path(__file__).resolve().parent
W=pathlib.Path(r'C:\Users\theis\.codex\worktrees\pr43-review-revision\salah_widget')
E=R/'evidence/PR43-review/R1-complete-scene-02'
BASE=R/'evidence/PR43-review/R1-complete-scene-01'
sys.path.insert(0,str(W/'tools/cp9'))
from first_complete_scene import first_complete_scene, BUDGETS
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for engine in ['chromium','firefox']:
    old={x['mode']:x for x in json.loads((BASE/f'{engine}-baseline/native-frame-review/timing.json').read_text())}
    d=E/f'{engine}-candidate'
    for item in json.loads((d/'native-frame-review/timing.json').read_text()):
        frames=json.loads((d/f'native-frame-review/{item["mode"]}-frames.json').read_text())
        first={key:item['first'][key]['msUpper'] for key in ['scene','moon','stars']}
        complete=max(first.values()); early=[x for x in frames if x['msUpper']<=complete]
        times=[0]+[x['msUpper'] for x in early];gap=max(b-a for a,b in zip(times,times[1:]))
        baseline=old[item['mode']]['first']['scene']['msUpper']; accepted=item['acceptedMs'];b=BUDGETS[engine]
        receipt={'browser':engine,'observerKnown':True,'evidenceKind':'presented-pixels','frames':[x['file'] for x in early],
                 'maximumUncoveredMs':gap,'sceneMs':first['scene'],'moonMs':first['moon'],'starsMs':first['stars'],
                 'moonWarranted':True,'starsWarranted':True,'acceptedMs':accepted,'baselineSceneMs':baseline}
        rows.append({'engine':engine,'mode':item['mode'],'runtime':'040192b555fa0db2fad760470ec020a06d86d3e0c7615153062ec5e76c50a2d5',
                     'rawReceiptSha256':sha(d/'results.json'),'firstReceiptBoundsMs':first,'completeMs':complete,
                     'baselineSceneMs':baseline,'addedStartupMs':first['scene']-baseline,'acceptedMs':accepted,
                     'acceptedToCompleteMs':complete-accepted,'maximumUncoveredMs':gap,'receipt':receipt,
                     'strictAcceptance':first_complete_scene(receipt),'separateTimingChecks':{
                         'navigation':complete<=b['navigationMs'],'acceptedScene':0<=complete-accepted<=b['acceptedMs'],
                         'coherentCapturedContent':complete-first['scene']<=b['frameGapMs'],'addedStartup':first['scene']-baseline<=b['regressionMs']}})
out={'scope':'Native source-frame receipt upper bounds; ordinary unchanged actual entry, original observer/provider fixture, actual HTTP cache. Frame co-occurrence is not exhaustive presentation or physical-monitor photon evidence. Retained original scripts/thresholds.',
     'baselineReuse':{'path':str(BASE),'receiptSha256':sha(BASE/'receipt.json'),'status':'previous exact-main observation, not fresh matched pair'},'rows':rows,'baselineAnnotationRejection':{'case':'firefox-baseline/cold','automaticMoonMs':3889.18115234375,
       'status':'REJECTED_BY_ORIGINAL_PIXEL_REVIEW','evidence':'firefox-baseline/native-frame-review/cold-moon.png',
       'reason':'A white horizontal source-capture band crosses the Moon test crop; no lunar body is present. The original automated annotation is retained but cannot support baseline first-Moon timing. Baseline scene time and candidate co-captured scene are separate observations.'}}
(E/'ASSESSMENT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
