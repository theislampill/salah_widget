"""Admit separate bounded cost totals after the unchanged R0035 trial interval.

The reviewed original stage host executes in an isolated module namespace with
only explicit protocol/timing labels and its supplemental inspector changed.
Its original driver, isolation, route, extraction, cleanup and error paths remain
the same. Both adapter and base-host identities are recorded in the final proof.
"""
import json
import math
from pathlib import Path
import types

import r0035_cost_materialize as material
import observe_r0035_stages as stages

HERE=Path(__file__).resolve().parent
BASE_WRAPPER_SHA256='8c3838b2ba01d6a4114b5de0aa2401134bb0cea3918dcba4fe1237997e53c99b'
BUCKETS=('spectralFlux','psfRaster','calendarTransfer','nominalCompose','envelopeBounds',
         'lowerBoundCompose','upperBoundCompose','variableSelection','patchWeights','inputGathers',
         'centerWithdrawal','withdrawalCompose','centerRanking')
COUNTS=('fullInputSources','previewInputSources','spectralSources','transportSamples','patchCalls','drawnPatches',
        'referencePsfChannels','referenceGaussianCalls','patchPixelsRequested','replayInputSources',
        'replaySelectedSources','envelopePatchPixelsScheduled','variablePixels','variablePatchOffsets','inputGatherValues',
        'withdrawalCenters','fullComposeCalls','centerComposeCalls')
FAULTS=('clock','overlap','name','count','lifecycle')


def finite(value): return type(value) in (int,float) and math.isfinite(value)
def count(value): return type(value) is int and 0<=value<=9007199254740991
def same(left,right): return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)


def inspect_costs(cost,worker,durations,op):
    """Only same-worker sums and already-observed/declared-derived counts."""
    need=material.need
    need(isinstance(cost,dict) and set(cost)=={'protocol','clockDomain','epoch','status','startedAt','lastAt','endedAt','active','faults','buckets','counts'}, 'complete cost aggregate required')
    need(cost['protocol']=='r0035-worker-costs/1' and cost['clockDomain']==stages.WORKER_CLOCK
         and type(cost['epoch']) is int and cost['epoch']==worker['epoch'], 'cost clock or epoch differs')
    need(cost['status'] in ('COMPLETE','FAILED') and (op!='ready' or cost['status']=='COMPLETE')
         and cost['active'] is None, 'cost preparation prefix is not terminal')
    need(same(cost['faults'],dict.fromkeys(FAULTS,False)), 'cost collector faults remain')
    need(all(finite(cost[key]) and cost[key]>=0 for key in ('startedAt','lastAt','endedAt'))
         and cost['lastAt']==cost['endedAt'] and cost['startedAt']<=worker['marks'][0]['at']
         and cost['startedAt']<=cost['endedAt']<=worker['marks'][-1]['at'], 'cost worker interval differs')
    buckets=cost['buckets'];counts=cost['counts']
    need(isinstance(buckets,dict) and set(buckets)==set(BUCKETS)
         and isinstance(counts,dict) and set(counts)==set(COUNTS), 'fixed cost population required')
    need(all(count(value) for value in counts.values()), 'invalid cost operation count')
    failed=0
    for name,row in buckets.items():
        need(isinstance(row,dict) and set(row)=={'calls','completed','failed','ms'}, 'fixed cost bucket fields required')
        need(all(count(row[key]) for key in ('calls','completed','failed')) and row['calls']==row['completed']+row['failed']
             and finite(row['ms']) and row['ms']>=0 and (row['calls']>0 or row['ms']==0), 'inconsistent cost bucket')
        failed+=row['failed']
    need(failed<=1 and (cost['status']!='COMPLETE' or failed==0), 'failed cost work cannot be complete')
    need(counts['spectralSources']==buckets['spectralFlux']['calls'] and counts['patchCalls']==buckets['psfRaster']['calls'], 'cost call counts differ')
    need(counts['spectralSources']<=counts['fullInputSources']+counts['previewInputSources']
         and counts['patchCalls']<=counts['spectralSources'] and counts['drawnPatches']<=buckets['psfRaster']['completed'], 'cost source population differs')
    need(counts['referencePsfChannels']==3*counts['drawnPatches']
         and counts['referenceGaussianCalls']==6*counts['drawnPatches'], 'derived reference PSF counts differ')
    minimum=95*buckets['spectralFlux']['completed'];maximum=95*buckets['spectralFlux']['calls']
    need(minimum<=counts['transportSamples']<=maximum, '95-sample transport count differs')
    need(counts['replaySelectedSources']<=counts['replayInputSources']
         and counts['withdrawalCenters']<=counts['replaySelectedSources'], 'cost replay population differs')
    need(counts['fullComposeCalls']==sum(buckets[name]['completed'] for name in ('nominalCompose','lowerBoundCompose','upperBoundCompose'))
         and counts['centerComposeCalls']==buckets['withdrawalCompose']['completed'], 'cost composition counts differ')
    # These marks already carry the accepted population. Reuse them after the
    # trial; do not add another producer scan or measurement-time census.
    marks={row['kind']:row for row in worker['marks']}
    source=marks.get('source-verified');stars=marks.get('stars-prepared');prepared=marks.get('replay-prepared')
    if source is not None:
        need(count(source.get('projected')) and type(source.get('preview')) is bool, 'original source population is missing')
        visited='previewInputSources' if source['preview'] else 'fullInputSources'
        other='fullInputSources' if source['preview'] else 'previewInputSources'
        need(counts[other]==0 and counts[visited]<=source['projected'], 'cost source branch or population differs')
        if stars is not None and not source['preview']:
            need(counts[visited]==source['projected'], 'complete full source population differs')
    if stars is not None:
        need(count(stars.get('stars')) and buckets['psfRaster']['calls']==buckets['psfRaster']['completed']==stars['stars'],
             'cost patch population differs from original prepared stars')
        if buckets['calendarTransfer']['calls']:
            need(counts['replayInputSources']==stars['stars'], 'cost replay input differs from original prepared stars')
    if prepared is not None:
        need(count(prepared.get('sources')) and count(prepared.get('variablePixels'))
             and counts['replaySelectedSources']==prepared['sources'] and counts['variablePixels']==prepared['variablePixels'],
             'cost replay population differs from original prepared replay')
    replay_prefix=[i for i,name in enumerate(BUCKETS[2:]) if buckets[name]['calls']]
    need(replay_prefix==list(range(len(replay_prefix))), 'replay cost stages are not an executed prefix')
    for i in replay_prefix:
        row=buckets[BUCKETS[i+2]]
        need(row['calls']==1 and (i==replay_prefix[-1] or row['completed']==1), 'replay cost stage prefix is inconsistent')
    if cost['status']=='COMPLETE':
        need(all(buckets[name]['calls']==buckets[name]['completed']==1 for name in BUCKETS[2:]), 'complete replay cost stages required')
        need(counts['replayInputSources']==buckets['psfRaster']['completed']
             and counts['withdrawalCenters']==counts['replaySelectedSources'], 'complete cost source/center counts differ')
    stellar=sum(buckets[name]['ms'] for name in BUCKETS[:2]);replay=sum(buckets[name]['ms'] for name in BUCKETS[2:])
    # The tiny arithmetic allowance covers binary64 summation only; it is not a
    # cadence tolerance, clock calibration or product acceptance threshold.
    need(stellar+replay<=cost['endedAt']-cost['startedAt']+1e-6, 'aggregate cost exceeds its worker interval')
    for total,key in ((stellar,'stellarPreparation'),(replay,'replayPreparation')):
        parent=durations.get(key)
        if parent is not None: need(total<=parent+1e-6, 'cost aggregate exceeds original same-worker stage')
    return {'protocol':'r0035-cost-summary/1','status':cost['status'],'clockDomain':stages.WORKER_CLOCK,
            'buckets':buckets,'counts':counts,'stellarMeasuredMs':stellar,'replayMeasuredMs':replay,
            'measuredBucketTotalMs':stellar+replay,
            'referencePsfCountRule':'Three channels and two positive Gaussian parts per drawn patch in the unchanged default reference renderer; counts are derived from its returned drawn count.',
            'interpretation':'Aggregate elapsed work with uncalibrated marks/counting overhead; no cross-clock latency, cache benefit, cadence or product acceptance claim.'}


def inspect(trace):
    result=stages.inspect(trace)
    result['protocol']='r0035-cost-intervals/1'
    for row in result['epochs']:
        replies=[e for e in trace['events'] if e['kind']=='prepare-reply' and e.get('messageEpoch')==row['epoch']]
        material.need(len(replies)<=1,'duplicate cost reply epoch')
        row['preparationCosts']=None
        if replies and replies[0].get('worker') is not None:
            worker=replies[0]['worker']
            row['preparationCosts']=inspect_costs(worker.get('costs'),worker,row['workerDurationsMs'],replies[0]['op'])
    return result


def entry_support():
    """Compose the pinned host without modifying its shared module or file."""
    path=HERE/'observe_r0035_stages.py';raw=path.read_bytes()
    material.need(material.digest(raw)==BASE_WRAPPER_SHA256,'reviewed stage host source changed')
    text=raw.decode();edits=[
        ('r0035-stage-trial/1','r0035-cost-trial/1',1),
        ('r0035-stage-driver/1','r0035-cost-driver/1',1),
        ('instrumented-stage-observation',material.TIMING,2),
        ("'wrapperSha256': material.digest(Path(__file__).read_bytes()),",
         "'wrapperSha256': material.digest(Path(__file__).read_bytes()), 'baseWrapperSha256': BASE_WRAPPER_SHA256, 'collectorSha256': material.HELPER_SHA256,",1),
    ]
    for old,new,total in edits:
        material.need(text.count(old)==total,'cost host composition seam changed');text=text.replace(old,new)
    restored=text
    for old,new,total in reversed(edits):
        material.need(restored.count(new)==total,'cost host reverse seam changed');restored=restored.replace(new,old)
    material.need(restored.encode()==raw,'cost host composition is not exactly reversible')
    module=types.ModuleType('r0035_cost_entry_support');module.__file__=str(Path(__file__).resolve())
    exec(compile(text,str(path),'exec'),module.__dict__)
    module.material=material;module.inspect=inspect;module.BASE_WRAPPER_SHA256=BASE_WRAPPER_SHA256
    return module


def main(argv=None): return entry_support().main(argv)


if __name__=='__main__':main()
