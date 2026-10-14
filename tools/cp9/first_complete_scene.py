"""Acceptance over pixel-reviewed first-seconds receipts, never eventual-ready.

The caller must bind annotations to retained frames/video and record coverage.
This predicate cannot turn state getters or synthetic clocks into pixel evidence.
"""
BUDGETS = {
 'chromium': {'navigationMs':1000,'acceptedMs':250,'frameGapMs':80,'regressionMs':250},
 'firefox': {'navigationMs':1500,'acceptedMs':400,'frameGapMs':80,'regressionMs':400},
}

def first_complete_scene(receipt):
 import math
 budget=BUDGETS[receipt['browser']]
 failures=[]
 if receipt.get('observerKnown') is not True:
  return {'status':'SEPARATE_ACQUISITION_CASE','failures':['accepted observer is unavailable'],'budget':budget}
 if receipt.get('evidenceKind')!='presented-pixels':failures.append('requires presented pixels')
 uncovered=receipt.get('maximumUncoveredMs')
 if (not receipt.get('frames') or isinstance(uncovered,bool) or not isinstance(uncovered,(int,float))
     or not math.isfinite(uncovered) or not 0<=uncovered<=budget['frameGapMs']):
  failures.append('incomplete early-frame coverage')
 needed=['sceneMs','acceptedMs','baselineSceneMs']
 if receipt.get('moonWarranted'):needed.append('moonMs')
 if receipt.get('starsWarranted'):needed.append('starsMs')
 for key in needed:
  value=receipt.get(key)
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
   failures.append('missing/invalid '+key)
 if failures:return {'status':'FAIL','failures':failures,'budget':budget}
 complete=max(receipt[k] for k in needed if k not in ['acceptedMs','baselineSceneMs'])
 checks={
  'navigation':complete<=budget['navigationMs'],
  'acceptedScene':0<=complete-receipt['acceptedMs']<=budget['acceptedMs'],
  'coherentFirstScene':complete-receipt['sceneMs']<=budget['frameGapMs'],
  'noLoadingGateRegression':receipt['sceneMs']-receipt['baselineSceneMs']<=budget['regressionMs'],
  'continuedPresence':not receipt.get('laterUnwarrantedGaps'),
 }
 return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'failures':[k for k,v in checks.items() if not v],'firstCompleteMs':complete,'budget':budget}
