"""Restricted original-main regression comparator; never candidate F2 admission.

The unchanged first-admission normalizer remains UNKNOWN for this old product.
Only a fresh capture of the exact retained original runtime may use this helper.
Association and callback intervals do not prove native acquisition or appearance.
"""
from startup_timing import (InvalidTiming, MissingTiming, artifact, number, text,
    validate_clock_custody, validate_frame_custody, _raw_json_artifact, _serialized_equal)

BASELINE_TREE='f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
BASELINE_ENTRY='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'

def validate_baseline_capture(results):
    if not isinstance(results,dict) or results.get('schema')!='celestial-startup/1':
        raise InvalidTiming('invalid baseline capture schema')
    runtime=results.get('runtime') or {}
    if runtime.get('treeSha256')!=BASELINE_TREE or (runtime.get('files') or {}).get('index.html',{}).get('sha256')!=BASELINE_ENTRY:
        raise InvalidTiming('baseline requires exact retained original-main runtime')
    expected={'scene':'clear','stamp':'2026-09-25T02:00:00Z','dpr':1.0,'entry':'iframe',
        'instrumented':False,'syntheticWeather':{'code':0,'cloud':0,'precipMm':0},
        'hold':None,'holdSeconds':0,'missing':False,'acquiring':False,'prayerDelaySeconds':0,
        'recoverAfterSeconds':None,'cpuProfile':False,'fontDelaySeconds':0,
        'fontRouteDisablesCache':False,'videoOnlyFirstSeconds':True,
        'captureTrace':False,'cdpFilmstrip':False,'errors':[],'runtimeUnchanged':True}
    for key,value in expected.items():
        if key not in results or results[key]!=value:
            raise InvalidTiming('baseline ordinary capture prerequisite differs: '+key)
    if (results.get('browser') or {}).get('family') not in ['chromium','firefox']:
        raise InvalidTiming('baseline browser family absent/unsupported')
    if not isinstance(results.get('runs'),list) or not results['runs']:
        raise MissingTiming('baseline capture records absent')

def retained_baseline_capture(comparison):
    if not isinstance(comparison,dict) or comparison.get('schema')!='salah-startup-comparison/1':
        raise InvalidTiming('invalid baseline comparison schema')
    raw=_raw_json_artifact(comparison.get('observerArtifact'),'original-main baseline results')
    validate_baseline_capture(raw)
    capture=comparison.get('captureClock')
    if not isinstance(capture,dict) or capture.get('kind')!='python-monotonic' or capture.get('unit')!='ms':
        raise InvalidTiming('baseline capture monotonic domain mismatch')
    if not text(capture.get('id'),'baseline capture ID').startswith('capture:'):
        raise InvalidTiming('baseline capture namespace mismatch')
    navigation=comparison.get('navigation')
    if not isinstance(navigation,dict) or navigation.get('kind')!='navigation-request' or navigation.get('clockId')!=capture['id']:
        raise InvalidTiming('baseline original navigation domain mismatch')
    reference=artifact(navigation.get('artifact'))
    selected=[run for run in raw['runs'] if isinstance(run,dict) and isinstance(run.get('captureTiming'),dict)
        and (run['captureTiming'].get('navigation') or {}).get('artifact')==reference]
    if len(selected)!=1:
        raise InvalidTiming('baseline navigation/capture selection absent or ambiguous')
    run=selected[0]
    if run.get('mode') not in ['cold','warm-reload','new-tab']:
        raise InvalidTiming('baseline capture mode unknown')
    for key in ['captureClock','navigation','bridges','observer']:
        if key not in run['captureTiming']:
            raise MissingTiming('retained baseline '+key+' absent')
        _serialized_equal(comparison.get(key),run['captureTiming'][key],'baseline '+key)
    observer=run['captureTiming']['observer']
    if not isinstance(observer,dict) or observer.get('schema')!='salah-startup-timing/1':
        raise MissingTiming('baseline capture-only observer/clock absent')
    empty={'firstValidAdmission':None,'admissions':[],'events':[],'rejected':[],
        'presentedMarker':None,'overflow':False}
    for key,value in empty.items():
        if key not in observer or observer[key]!=value:
            raise InvalidTiming('baseline cannot replace first-admission attribution: '+key)
    return run

def baseline_clock_bounds(event, comparison, source_kind):
    """Original interval math with a strictly scoped baseline capture association."""
    validate_clock_custody(comparison,require_navigation=True)
    retained_baseline_capture(comparison)
    if not isinstance(event,dict):
        raise MissingTiming('missing timed baseline callback')
    clock_id=text(event.get('clockId'),'event clock ID')
    at=number(event.get('atMs'),'event timestamp',0)
    target=comparison['captureClock']['id']
    if clock_id==target:
        if source_kind!='python-monotonic':
            raise InvalidTiming('source clock mislabeled as capture domain')
        return [at,at]
    samples=[b for b in comparison.get('bridges',[]) if b.get('sourceClockId')==clock_id]
    if not samples:
        raise MissingTiming('missing monotonic bridge for '+clock_id)
    offsets=[]
    for sample in samples:
        if sample.get('kind')!='bracketed-clock-sample' or sample.get('targetClockId')!=target or sample.get('sourceKind')!=source_kind:
            raise InvalidTiming('wrong clock bridge identity/kind')
        artifact(sample.get('artifact'))
        text(sample.get('sampleId'),'clock sample ID')
        source=number(sample.get('sourceAtMs'),'clock sample source',0)
        before=number(sample.get('targetBeforeMs'),'clock bracket before',0)
        after=number(sample.get('targetAfterMs'),'clock bracket after',0)
        if after<before:
            raise InvalidTiming('reversed clock bracket')
        offsets.append([before-source,after-source])
    lower,upper=max(x[0] for x in offsets),min(x[1] for x in offsets)
    if lower>upper:
        raise InvalidTiming('inconsistent monotonic clock brackets')
    return [at+lower,at+upper]

def baseline_frame_custody(row, pixel_artifact, receipt_artifact, comparison):
    run=retained_baseline_capture(comparison)
    source={'kind':'native-source-receipt','eventId':row['sourceEventId'],
        'clockId':row['receiptClock']['id'],'atMs':row['receiptMonotonicMs'],
        'rawProtocolTimeSeconds':row['sourceTimeSeconds'],
        'artifact':pixel_artifact,'receiptArtifact':receipt_artifact}
    presented={'kind':'presented-pixels-receipt-upper-bound','eventId':row['presentedReceiptEventId'],
        'sourceEventId':row['sourceEventId'],'clockId':row['receiptClock']['id'],
        'atMs':row['receiptMonotonicMs'],'artifact':pixel_artifact,'receiptArtifact':receipt_artifact}
    return validate_frame_custody(source,presented,run)
