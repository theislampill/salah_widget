"""Native-marker elapsed callback analysis. Contrary data and incomplete scopes remain explicit."""
from pathlib import Path
import collections,hashlib,json,math
from analyse_cost_v3 import no_moon_work,summary,SEQUENCE
from cost_state_v5 import match_state
from window_wait_v5 import validate_wait
from network_evidence_v4 import ASSET_PINS,validate_network
from native_profile_v5 import read_marks,decode,select_export_prefix,validate_boundaries

ENDPOINT_ERROR_MS=.005
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def interval(value,overhead,clock):return {'lowerMs':max(0,value-overhead-clock),'upperMs':value+clock,'overheadEnvelopeMs':overhead,'clockErrorMs':clock}
def compare(a,b):
 pass_limit=a['lowerMs']+max(.25,.1*a['lowerMs']);fail_limit=a['upperMs']+max(.25,.1*a['upperMs'])
 verdict='PASS'if b['upperMs']<=pass_limit else'FAIL'if b['lowerMs']>fail_limit else'INCOMPLETE'
 return {'A':a,'B':b,'passLimitMs':pass_limit,'failLimitMs':fail_limit,'verdict':verdict}

def metric_verdict(outcomes,noisy):
 return 'INCOMPLETE'if noisy else'FAIL'if'FAIL'in outcomes else'INCOMPLETE'if'INCOMPLETE'in outcomes else'PASS'

def combine_windows(first,full):
 result={'first5':first['status'],'full15':full['status'],'status':'INCOMPLETE','basis':'Both windows retain their own raw data and reasons.'}
 if 'GLOBAL'in first['reasonCodes']or'GLOBAL'in full['reasonCodes']:return result
 if 'FAIL'in [first['status'],full['status']]:result.update(status='FAIL',basis='Valid contrary breach in either window is retained.');return result
 if first['status']=='PASS'and full['status']=='PASS':result.update(status='PASS',basis='Both original5s and fixed15s comparisons pass.');return result
 if first['status']=='INCOMPLETE'and first['reasonCodes']==['SPARSE']and full['status']=='PASS':result.update(status='PASS',basis='Only predeclared first5s sparsity supplemented by fixed15s; original5s remains INCOMPLETE.')
 return result

def analyse(out,record):
 out=Path(out);slots=record.get('slots',[]);reasons=[];expected=record.get('expectedScopes',{})
 result={'schema':'r0021-native-cost-analysis/v5','status':'INCOMPLETE','metric':'Actual synchronous exclusive elapsed; no CPU self-time claim.','globalReasons':reasons,'endpointErrorMs':ENDPOINT_ERROR_MS,'uncertaintyRule':'Nonnegative probe cost; interval lower=max(0,observed-full maximum empirical overhead-clock), upper=observed+clock. Every raw maximum retained. Not a formal scheduling or uninstrumented optimizer bound.','wholeCostGate':'OPEN until independent scope/structural/startup response evidence joins.','windows':{},'startupCallbacks':{},'calibration':{},'sequenceComplete':[(s.get('block'),s.get('order'),s.get('side'))for s in slots]==SEQUENCE}
 def require(condition,why):
  if not condition:reasons.append(why)
 require(result['sequenceComplete'],'Four ABBA rounds incomplete')
 require(record.get('status')=='RAW_BATCH_RETURNED','Incomplete acquisition')
 require(record.get('runtimeUnchanged')=={'A':True,'B':True},'Runtime poststate missing/changed')
 require(record.get('inputsUnchanged')is True,'Input poststate missing/changed')
 require(record.get('runtimeExpectedMatched')is True and record.get('servedIdentityVerified')is True,'Initial/served runtime mismatch')
 require(record.get('browserClosed')is True and record.get('playwrightStopped')is True,'Browser/driver shutdown unverified')
 require(record.get('ownedCleanup',{}).get('verified')is True and record.get('ownedCleanup',{}).get('remaining')==[],'Owned process cleanup incomplete')
 require(not record.get('nativeProfilerCloseError'),'Native profiler shutdown failure')
 require(record.get('nativeProfilerClose',{}).get('activeAtClose')is False,'Native profiler unexpectedly active at batch cleanup')
 try:
  assert record['inputs']and all(Path(p).is_file()and sha(Path(p))==h for p,h in record['inputs'].items()),'Pinned dependency changed'
  for side in 'AB':
   declared=json.loads(Path(record['expectedRuntimeFiles'][side]).read_bytes());assert declared==record['runtime'][side],'Declared runtime differs'
   root=Path(record['runtimeRoots'][side]);assert all((root/p).is_file()and sha(root/p)==v['sha256']for p,v in declared['files'].items()),'Runtime bytes changed'
   assert {p:{k:declared['files'][p][k]for k in['bytes','sha256']}for p in ASSET_PINS}==ASSET_PINS,'Asset pins changed'
 except(AssertionError,KeyError,OSError,TypeError,ValueError)as e:reasons.append('Custody: '+str(e))
 require(set(expected)=={'A','B'}and all(expected.values()),'Expected source scope union missing')
 decoded={};control_max={'A':[],'B':[]}
 for slot in slots:
  sid=slot.get('id','unknown')
  try:
   side=slot['side'];assert side in 'AB'and slot['status']=='RAW_SLOT_RETURNED'and slot['contextClosed'],'Slot/cleanup incomplete'
   assert not slot['errors']and slot['networkSettled']and not slot['networkViolations'],'Native/network failure'
   assert validate_network(slot,record)==slot['networkClassification'],'Network consumer join mismatch'
   for phase in ['readyState','startState','endState']:match_state(record['referenceState'],slot[phase],record['expectedOwners'][side],side)
   no_moon_work(slot['readyState'],slot['startState']);no_moon_work(slot['startState'],slot['endState'])
   rawpath=(out/slot['rawFile']).resolve();profilepath=(out/slot['nativeProfileFile']).resolve()
   assert rawpath.is_relative_to(out.resolve())and profilepath.is_relative_to(out.resolve()),'Path escapes batch'
   assert sha(rawpath)==slot['callsSha256']and sha(profilepath)==slot['nativeProfileSha256'],'Raw/native digest mismatch'
   raw=json.loads(rawpath.read_bytes());assert len(raw['records'])<=raw['capacity'],'Overflow'
   profile=json.loads(profilepath.read_bytes());all_marks=read_marks(profile,record['engine']);thread='CrRendererMain'if record['engine']=='chromium'else'GeckoMain'
   assert slot['documentReadback']['url']==slot['origin']+'/salah_widget/#local=1&motion=full','Unexpected page URL'
   marks,document,excluded=select_export_prefix(all_marks,raw,slot['documentReadback'],slot['documentMarkerLabel'],thread)
   index,calls=decode(marks,raw,document['documentId'],thread)
   assert set(c['scope']for c in calls if not c['scope'].startswith('probe.'))<=set(expected[side]),'Unexpected callback scope'
   if record['engine']=='chromium':assert slot['nativeProfileStop']['dataLossOccurred']is False,'Trace data loss unknown/true'
   else:assert slot['nativeProfileStop']['ok']and slot['nativeProfileStop']['stop']['active']is False,'Profiler not stopped'
   boundaries={}
   for key in ['warmStart','warmEnd','start','end']:
    m=slot[key];assert not m['invalid']and m['depth']==0;boundaries[key]=index[m['name']]['at']
   assert 5000<=boundaries['warmEnd']-boundaries['warmStart']<=5250,'Native warmup lateness'
   assert 15000<=boundaries['end']-boundaries['start']<=15250,'Native fixed window lateness'
   validate_wait(slot['warmWait'],5);validate_wait(slot['measureWait'],15)
   controls={};declared_controls=set()
   declared_marks=[slot['documentReadback']['mark'],slot['readyState']['timing'],slot['overheadBefore']['before'],slot['overheadBefore']['after'],slot['warmStart'],slot['warmEnd'],slot['startState']['timing'],slot['start'],slot['end'],slot['endState']['timing'],slot['overheadAfter']['before'],slot['overheadAfter']['after'],raw['cut']]
   for key in ['overheadBefore','overheadAfter']:
    c=slot[key];assert c['count']==200 and c['clockPositiveStepsMs'],'Incomplete exact recorder control'
    assert all(isinstance(v,(int,float))and math.isfinite(v)and v>0 for v in c['clockPositiveStepsMs']),'Invalid page clock observation'
    for edge in ['before','after']:assert c[edge]['depth']==0 and not c[edge]['invalid']and c[edge]['name']in index
    label=c['before']['name'].split(':',3)[3].removesuffix('.before')
    for kind in ['empty','nested']:
     declared_controls.update(f'r21:C:{label}:{kind}:{i}:{edge}'for i in range(200)for edge in['S','E'])
     values=[index[f'r21:C:{label}:{kind}:{i}:E']['at']-index[f'r21:C:{label}:{kind}:{i}:S']['at']for i in range(200)]
     assert all(math.isfinite(v)and v>=0 for v in values),'Invalid control elapsed'
     controls[key+'.'+kind]={'rawMs':values,'summary':summary(values)};control_max[side].append(max(values))
   validate_boundaries(marks,declared_marks)
   assert {m['name']for m in marks if m['name'].startswith('r21:C:')}==declared_controls,'Missing/foreign calibration endpoint'
   assert len(marks)==len(calls)*2+len(declared_controls)+len(declared_marks),'Native marker cardinality mismatch'
   result['calibration'][sid]={'markers':len(marks),'calls':len(calls),'endpointsComplete':True,'controls':controls,'boundariesNativeMs':boundaries,'nativeDocument':document,'excludedSuffix':excluded,'negativeExclusiveCorrections':[{'token':c['token'],'magnitudeMs':c['negativeExclusiveCorrectionMs']}for c in calls if c['negativeExclusiveCorrectionMs']],'pageClockSteps':{k:slot[k]['clockPositiveStepsMs']for k in['overheadBefore','overheadAfter']}}
   decoded[sid]=(slot,calls,boundaries)
   result['startupCallbacks'][sid]={scope:{metric:summary([c[metric]for c in calls if c['scope']==scope and c['startMs']<boundaries['warmStart']])for metric in ['inclusiveMs','exclusiveMs']}for scope in expected[side]}
  except(AssertionError,KeyError,ValueError,TypeError,OSError,IndexError,StopIteration)as e:reasons.append(sid+': '+str(e))
 for seconds in [5,15]:
  window={'durationSeconds':seconds,'scopes':{},'perSlot':{}};result['windows'][str(seconds)]=window
  values=collections.defaultdict(lambda:{'A':[],'B':[]});blocks=collections.defaultdict(lambda:{s:collections.defaultdict(list)for s in 'AB'});children=collections.defaultdict(lambda:{'A':[],'B':[]});inclusive=collections.defaultdict(lambda:{'A':[],'B':[]})
  for sid,(slot,calls,bounds)in decoded.items():
   side=slot['side'];window['perSlot'][sid]={}
   for scope in expected[side]:
    selected=[c for c in calls if c['scope']==scope and bounds['start']<=c['startMs']<bounds['start']+seconds*1000];ex=[c['exclusiveMs']for c in selected];inc=[c['inclusiveMs']for c in selected]
    values[scope][side]+=ex;inclusive[scope][side]+=inc;blocks[scope][side][slot['block']]+=ex;children[scope][side]+=[c['children']for c in selected]
    window['perSlot'][sid][scope]={'exclusive':summary(ex),'inclusive':summary(inc),'callsPerSecond':len(ex)/seconds,'endCrossingCallsIncluded':sum(c['endMs']>bounds['start']+seconds*1000 for c in selected)}
  for scope in sorted(set(expected.get('A',[]))|set(expected.get('B',[]))):
   row={'status':'INCOMPLETE','sourcePresence':{s:scope in expected.get(s,[])for s in'AB'},'A':summary(values[scope]['A']),'B':summary(values[scope]['B']),'inclusive':{s:summary(inclusive[scope][s])for s in'AB'},'blocks':{s:{str(b):summary(v)for b,v in blocks[scope][s].items()}for s in'AB'},'reasons':[],'reasonCodes':[]};window['scopes'][scope]=row
   if reasons or not all(control_max.values()):row['reasonCodes'].append('GLOBAL');row['reasons'].append('Global custody/state/native acquisition failure')
   if any(len(values[scope][s])<20 or set(blocks[scope][s])!={0,1,2,3}or not all(blocks[scope][s].values())for s in'AB'):
    row['reasonCodes'].append('SPARSE');row['reasons'].append('Absent/startup-only/sparse: need20steady calls/side and eachside/everyround');continue
   if 'GLOBAL'in row['reasonCodes']:continue
   multiplicity={s:max(children[scope][s])for s in'AB'};overhead={s:(1+multiplicity[s])*max(control_max[s])for s in'AB'};clock={s:(2+2*multiplicity[s])*ENDPOINT_ERROR_MS for s in'AB'}
   row.update(maximumDirectChildren=multiplicity,fullMaximumOverheadMs=overhead,clockErrorMs=clock)
   verdicts=[];noise=False
   for metric in ['medianMs','p95Ms']:
    pooled=compare(*(interval(row[s][metric],overhead[s],clock[s])for s in'AB'))
    paired={str(b):compare(*(interval(row['blocks'][s][str(b)][metric],overhead[s],clock[s])for s in'AB'))for b in range(4)}
    spread={s:max(v[metric]for v in row['blocks'][s].values())-min(v[metric]for v in row['blocks'][s].values())for s in'AB'}
    noisy=any(v>max(.25,.1*row['A'][metric])for v in spread.values());noise|=noisy
    outcomes=[pooled['verdict']]+[x['verdict']for x in paired.values()]
    verdict=metric_verdict(outcomes,noisy);verdicts.append(verdict)
    row[metric]={'pooled':pooled,'pairedRounds':paired,'sameSideBlockSpreadMs':spread,'verdict':verdict}
   row['roundCallRates']={str(b):{s:row['blocks'][s][str(b)]['n']/(2*seconds)for s in'AB'}for b in range(4)}
   rate=any(abs(v['B']-v['A'])>max(.2,.1*v['A'])for v in row['roundCallRates'].values())
   if rate:row['reasonCodes'].append('RATE');row['reasons'].append('Call-rate difference exceeds max0.2Hz/10%; work/frequency attribution required')
   if noise:row['reasonCodes'].append('NOISE');row['reasons'].append('Unexplained same-side spread exceeds original allowance; breaches retained')
   if 'INCOMPLETE'in verdicts and not noise:row['reasonCodes'].append('UNCERTAINTY')
   row['status']='INCOMPLETE'if noise else'FAIL'if'FAIL'in verdicts else'INCOMPLETE'if rate or'INCOMPLETE'in verdicts else'PASS'
 result['combinedOwners']={scope:combine_windows(result['windows']['5']['scopes'][scope],result['windows']['15']['scopes'][scope])for scope in result['windows']['15']['scopes']}
 result['uncovered']=['Current r17 sky pendingJob/solarPublication and preview pendingValue/prepared/foreground/decoded-image cache are absent from the inherited resource inventory.','Positive cloud-mask async decode/finish/commit callbacks are not separately timed by this clear-weather batch. Missing or nonexecuted callbacks are not zero cost.','Worker body, initial receiver base64/compact decode and whole-heap retention remain outside these synchronous owner intervals.']
 result['status']='BOUNDED_OWNER_RESULTS'if not reasons and decoded else'INCOMPLETE'
 return result
