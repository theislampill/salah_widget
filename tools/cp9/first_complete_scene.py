"""First valid shared-scene admission to byte-bound pixel receipt upper bounds.

The caller must retain the original navigation boundary and explicit monotonic
bridges. Missing first-event evidence is UNKNOWN; eventual adoption cannot fill it.
"""
import math
from startup_timing import normalize_startup_timing, interval_check

BUDGETS = {
 'chromium': {'navigationMs':1000,'acceptedMs':250,'frameGapMs':80,'regressionMs':250},
 'firefox': {'navigationMs':1500,'acceptedMs':400,'frameGapMs':80,'regressionMs':400},
}


def first_complete_scene(receipt):
 budget=BUDGETS[receipt['browser']]
 if receipt.get('observerKnown') is not True:
  return {'status':'SEPARATE_ACQUISITION_CASE','failures':['accepted observer is unavailable'],'budget':budget}
 components=['scene']
 if receipt.get('moonWarranted'):components.append('moon')
 if receipt.get('starsWarranted'):components.append('stars')
 timing=normalize_startup_timing(receipt.get('timingComparison'),components)
 if timing['status']!='BOUND':
  return {'status':'UNKNOWN' if timing['status']=='UNKNOWN' else 'FAIL',
   'failures':timing['failures'],'timing':timing,'budget':budget}
 failures=[]
 if receipt.get('evidenceKind')!='presented-pixels':failures.append('requires presented pixels')
 uncovered=receipt.get('maximumUncoveredMs')
 if (not receipt.get('frames') or isinstance(uncovered,bool) or not isinstance(uncovered,(int,float))
     or not math.isfinite(uncovered) or not 0<=uncovered<=budget['frameGapMs']):
  failures.append('incomplete early-frame coverage')
 baseline=receipt.get('baselineSceneMs')
 if isinstance(baseline,bool) or not isinstance(baseline,(int,float)) or not math.isfinite(baseline) or baseline<0:
  failures.append('missing/invalid baselineSceneMs')
 first=timing['firstAdmissionBoundsMs'];bounds=timing['componentBoundsMs']
 if 'acceptedEventId' in receipt and receipt['acceptedEventId']!=timing['firstAdmissionId']:
  failures.append('later adoption cannot replace first admission')
 if 'acceptedEventKind' in receipt and receipt['acceptedEventKind']!='valid-shared-scene-admission':
  failures.append('wrong admission endpoint kind')
 # Legacy scalar inputs can be diagnostics but cannot override a derived bound.
 for key,expected in [('acceptedMs',first)]+[(name+'Ms',bounds[name]) for name in components]:
  if key not in receipt:continue
  value=receipt[key]
  if (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)
      or not expected[0]<=value<=expected[1]):
   failures.append('endpoint substitution/invalid '+key)
 if failures:return {'status':'FAIL','failures':failures,'timing':timing,'budget':budget}
 complete=[max(bounds[k][i] for k in components) for i in [0,1]]
 scene=bounds['scene']
 intervals={
  'navigation':complete,
  'acceptedScene':[complete[0]-first[1],complete[1]-first[0]],
  'coherentFirstScene':[max(0,complete[0]-scene[1]),max(0,complete[1]-scene[0])],
  'noLoadingGateRegression':[scene[0]-baseline,scene[1]-baseline],
 }
 checks={
  'navigation':interval_check(intervals['navigation'],lower=0,upper=budget['navigationMs']),
  'acceptedScene':interval_check(intervals['acceptedScene'],lower=0,upper=budget['acceptedMs']),
  'coherentFirstScene':interval_check(intervals['coherentFirstScene'],upper=budget['frameGapMs']),
  'noLoadingGateRegression':interval_check(intervals['noLoadingGateRegression'],upper=budget['regressionMs']),
  'continuedPresence':not receipt.get('laterUnwarrantedGaps'),
 }
 status='FAIL' if False in checks.values() else 'UNKNOWN' if None in checks.values() else 'PASS'
 return {'status':status,'checks':checks,'failures':[k for k,v in checks.items() if v is False],
  'unknown':[k for k,v in checks.items() if v is None],'firstCompleteBoundsMs':complete,
  'intervalsMs':intervals,'timing':timing,'budget':budget}
