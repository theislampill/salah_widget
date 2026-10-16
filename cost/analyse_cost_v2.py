"""Fail-closed, predeclared elapsed callback analysis; never CPU self-time."""
import collections, hashlib, json, math, statistics
from pathlib import Path

COLUMNS=['scopeId','startMs','inclusiveMs','exclusiveElapsedMs','depth','exception','directChildren']
SEQUENCE=[(b,o,s) for b in range(4) for o,s in enumerate('ABBA')]
WINDOW_MS=5000
LATENESS_MS=250
MOON_GEOMETRY=['size','outSize','diameter','basis','earth','distance','extent','mode','tilt','phaseQuantumRadians','phaseDisplayDiameter']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def p95(v): return sorted(v)[math.ceil(.95*len(v))-1]
def summary(v):
 return {'n':len(v),'medianMs':statistics.median(v),'p95Ms':p95(v),'totalMs':sum(v),'maxMs':max(v)} if v else {'n':0}

def validate_state(s,required=('moon','moonDetail','sky')):
 assert s['visibility']=='visible' and s['dpr']==1 and s['fonts']=='loaded','Visibility/DPR/fonts'
 assert s['card']=={'width':325,'height':530} and s['viewport']=={'width':390,'height':600},'Card/viewport geometry'
 assert s['civilZone']=='America/New_York' and s['civilDate'].startswith('2026-09-25T02:'),'Civil fixture'
 for family in ['Fraunces','Inter']:
  assert s['fontChecks'][family] and any(f['family'].strip('"\'')==family and f['status']=='loaded' for f in s['fontFaces']),'Loaded font '+family
 assert not any(f['status']=='error' for f in s['fontFaces']),'Failed font face'
 assert s['native']['timeScale']==1 and s['native']['paused'] is False,'Actual clock'
 assert s['native']['lat']==28.5383 and s['native']['lon']==-81.3792 and s['native']['tz']=='America/New_York','Actual target/zone'
 assert s['moon']['current'] and s['moon']['visibleSource']=='refined-terrain' and not s['moon']['pending'],'Moon acquisition/refinement'
 assert s['sky']['status']=='ready','Actual sky ready'
 assert s['provider']['pending']==0,'Provider request pending'
 assert set(required)<=set(s['owners']),'Missing required owner'
 for name,v in s['owners'].items():
  assert not v.get('error') and not v['inventory']['truncated'] and v['instanceCount']==1,'Owner coverage/duplicate '+name
 names=collections.Counter(v['name'] for v in s['pendingRAF'])
 assert names['loop']==1 and names['animate']==1 and names['tick']<=1 and all(v==1 for v in names.values()),'Native and optional RAF owners'
 assert set(names)<=set(['loop','animate','tick']),'Unclassified RAF owner'
 assert s['moon']['accepted']['scene']['profile']['mode']=='calendar','Calendar profile'
 for field in MOON_GEOMETRY: assert field in s['moon']['accepted']['scene'],'Missing Moon geometry '+field
 assert s['sky']['last']['view']=={'type':'camera','width':325,'height':530,'azDeg':180,'altDeg':45,'fovYDeg':90,'rollDeg':0},'Sky view'
 detail_fields=['table','calendarTable','surface','prepared']+(['projected'] if 'moonInitial' in required else [])
 for owner,fields in [('moonDetail',detail_fields),('moonInitial',['material','coverage','records','indices','rule'])]:
  if owner in required: assert set(fields)<=set(s['owners'][owner]['fields']),'Retained fields '+owner

def geometry(s):
 return {name:sorted((v['path'],v['width'],v['height']) for v in s['owners'][name]['inventory']['arraysAndCanvases'] if v['type']=='canvas') for name in ['moon','moonDetail','sky']}

def match_state(reference,s,required=('moon','moonDetail','sky')):
 validate_state(s,required)
 for key in ['lat','lon','timeScale','paused','weather','tz','camera']:
  assert s['native'][key]==reference['native'][key],'Matched native '+key
 assert s['moon']['accepted']['profile']==reference['moon']['accepted']['profile'],'Matched Moon profile'
 scene=s['moon']['accepted']['scene'];other=reference['moon']['accepted']['scene']
 for key in MOON_GEOMETRY+['waxing']:
  assert scene[key]==other[key],'Matched Moon '+key
 assert geometry(s)==geometry(reference),'Matched named canvas geometry'
 assert all(geometry(s).values()),'Absent named canvas geometry'
 assert s['sky']['last']['catalogue']==reference['sky']['last']['catalogue'],'Matched catalogue'
 for key in ['zone','currentKey','nextKey','timetableDate','nextDate']:
  assert s['prayer']['render'][key]==reference['prayer']['render'][key],'Matched prayer '+key
 phase_error=scene['phaseDisplayDiameter']/2*abs(math.acos(2*s['moon']['currentNativeFraction']-1)-math.acos(2*reference['moon']['currentNativeFraction']-1))
 assert phase_error<=.0416,'Matched phase displacement beyond .0416 device px'
 return {'phasePositionDifferencePx':phase_error,'utcDifferenceMs':s['native']['utcMs']-reference['native']['utcMs']}

def no_moon_work(before,after):
 a,b=before['owners']['moon'],after['owners']['moon']
 assert a['scalars']['serial']==b['scalars']['serial'] and a['workerId']==b['workerId'],'Moon job serial/worker changed'
 aw=next(w for w in before['workers'] if w['id']==a['workerId'])
 bw=next(w for w in after['workers'] if w['id']==b['workerId'])
 assert (aw['out'],aw['in'])==(bw['out'],bw['in']),'Transient Moon worker activity'

def compare(av,bv,u):
 allowance=max(.25,.1*av);delta=bv-av
 verdict='PASS' if delta+u<=allowance else 'FAIL' if delta-u>allowance else 'INCOMPLETE'
 return {'deltaMs':delta,'allowanceMs':allowance,'observerUncertaintyMs':u,'verdict':verdict}

def analyse(out,record):
 out=Path(out);slots=record.get('slots',[])
 result={'schema':'r0021-passive-cost-analysis/v2','metric':'exclusive elapsed; raw/inclusive retained; not CPU self-time','status':'INCOMPLETE','scopes':{},'globalReasons':[],
  'wholeCostGate':'OPEN: startup/entry, sparse owners, source allocation and independent structural review remain required',
  'startupPresentation':'OPEN; no presentation evidence in this acquisition',
  'uninstrumentedStartup':['receiver base64/compact decode and createInitialMoon admission outside head.prepareNativeFirstPaint','worker computations and asynchronous continuations'],
  'sequenceComplete':[(s.get('block'),s.get('order'),s.get('side')) for s in slots]==SEQUENCE}
 reasons=result['globalReasons']
 def require(ok,why):
  if not ok:reasons.append(why)
 require(result['sequenceComplete'],'Four ABBA rounds not completed')
 require(record.get('status')=='RAW_BATCH_RETURNED','Batch acquisition incomplete')
 require(record.get('runtimeUnchanged')=={'A':True,'B':True},'Runtime post-state missing/changed')
 require(record.get('inputsUnchanged') is True,'Input/overlay/helper/font post-state missing/changed')
 require(record.get('runtimeExpectedMatched') is True and record.get('servedIdentityVerified') is True,'Expected runtime/served-file identity missing/changed')
 require(record.get('browserClosed') is True,'Owned browser cleanup unverified')
 require(record.get('playwrightStopped') is True,'Playwright shutdown unverified')
 require(record.get('ownedCleanup',{}).get('verified') is True and record.get('ownedCleanup',{}).get('remaining')==[],'Owned process cleanup missing/failed')
 try:
  assert record['inputs'] and all(Path(p).is_file() and sha(Path(p))==h for p,h in record['inputs'].items()),'Pinned dependency bytes changed'
  for side in 'AB':
   expected_runtime=json.loads(Path(record['expectedRuntimeFiles'][side]).read_text())
   assert record['runtime'][side]==expected_runtime,'Initial runtime differs from pinned manifest'
   root=Path(record['runtimeRoots'][side])
   assert all((root/p).is_file() and sha(root/p)==v['sha256'] for p,v in expected_runtime['files'].items()),'Runtime file bytes changed'
 except (AssertionError,KeyError,OSError,ValueError,TypeError) as e:reasons.append('Independent custody readback: '+str(e))
 expected=record.get('expectedScopes',{})
 require(set(expected)=={'A','B'} and all(expected.values()),'Source-map scope union absent')
 values=collections.defaultdict(lambda:{'A':[],'B':[]});incs=collections.defaultdict(lambda:{'A':[],'B':[]})
 blocks=collections.defaultdict(lambda:{s:collections.defaultdict(list) for s in 'AB'})
 children=collections.defaultdict(lambda:{'A':[],'B':[]});per_slot={};startup={};controls={'A':[],'B':[]}
 for slot in slots:
  sid=slot.get('id','unknown');side=slot.get('side')
  try:
   assert side in 'AB' and slot['status']=='RAW_SLOT_RETURNED' and slot['contextClosed'] is True,'Slot state/cleanup'
   assert not slot['errors'] and slot['networkSettled'] is True and not slot['networkViolations'],'Native/network error'
   for phase in ['readyState','startState','endState']:match_state(record['referenceState'],slot[phase],record['expectedOwners'][side])
   no_moon_work(slot['readyState'],slot['startState']);no_moon_work(slot['startState'],slot['endState'])
   assert WINDOW_MS<=slot['warmEnd']['at']-slot['warmStart']['at']<=WINDOW_MS+LATENESS_MS,'Warmup boundary lateness'
   assert WINDOW_MS<=slot['end']['at']-slot['start']['at']<=WINDOW_MS+LATENESS_MS,'Observation boundary lateness'
   for mark in ['warmStart','warmEnd','start','end']:
    assert not slot[mark]['invalid'] and slot[mark]['depth']==0,'Mark observer state'
   for name in ['overheadBefore','overheadAfter']:
    control=slot[name];steps=control['clockPositiveStepsMs']
    assert steps and all(math.isfinite(x) and x>0 for x in steps) and min(steps)<=.25,'Clock capability'
    assert control['emptyObservedMs'] and control['nestedObservedMs'],'Observer controls absent'
    assert all(math.isfinite(x) and x>=0 for key in ['emptyObservedMs','nestedObservedMs'] for x in control[key]),'Invalid observer controls'
    controls[side].append(control)
   rawpath=(out/slot['rawFile']).resolve();assert rawpath.is_relative_to(out.resolve()),'Raw path outside batch'
   assert sha(rawpath)==slot['callsSha256'],'Raw digest mismatch'
   raw=json.loads(rawpath.read_text());assert raw['columns']==COLUMNS and not raw['invalid'] and not raw['errors'],'Raw observer failure'
   names=raw['names'];assert len(names)==len(set(names)) and len(raw['raw'])%7==0,'Raw shape'
   assert set(n for n in names if not n.startswith('probe.'))<=set(expected[side]),'Unexpected scope'
   assert all(isinstance(x,(int,float)) and math.isfinite(x) for x in raw['raw']),'Nonfinite raw data'
   rows=[raw['raw'][i:i+7] for i in range(0,len(raw['raw']),7)]
   assert len(rows)<=raw['capacity'],'Capacity overflow'
   assert all(r[0]==int(r[0]) and 0<=r[0]<len(names) and r[1]>=0 and 0<=r[3]<=r[2]+1e-6 and r[4]==int(r[4]) and 0<=r[4]<128 and r[5]==0 and r[6]==int(r[6]) and 0<=r[6] for r in rows),'Invalid raw row'
   startup[sid]={};per_slot[sid]={}
   for name in set(expected[side]):
    own=[r for r in rows if names[int(r[0])]==name]
    early=[r for r in own if r[1]<slot['warmStart']['at']]
    startup[sid][name]={'exclusive':summary([r[3] for r in early]),'inclusive':summary([r[2] for r in early])}
    steady=[r for r in own if slot['start']['at']<=r[1]<slot['start']['at']+WINDOW_MS]
    ex=[r[3] for r in steady];inc=[r[2] for r in steady]
    values[name][side].extend(ex);incs[name][side].extend(inc);blocks[name][side][slot['block']].extend(ex);children[name][side].extend(r[6] for r in steady)
    per_slot[sid][name]={'exclusive':summary(ex),'inclusive':summary(inc),'callsPerSecond':len(ex)/5,'endCrossingCallsIncluded':sum(r[1]+r[2]>slot['start']['at']+WINDOW_MS for r in steady)}
  except (AssertionError,KeyError,ValueError,TypeError,OSError,StopIteration) as e: reasons.append(sid+': '+str(e))
 result.update(startupCallbacks=startup,perSlot=per_slot)
 observer={}
 for side,c in controls.items():
  if c:observer[side]={'clockStepMs':max(min(x['clockPositiveStepsMs']) for x in c),'maximumEmptyMs':max(v for x in c for v in x['emptyObservedMs']),'maximumNestedMs':max(v for x in c for v in x['nestedObservedMs'])}
 result['observer']={'sides':observer,'bound':'sum per side of (2+2*N)*clockStep + (1+N)*max(maximumEmpty, maximumNested); N=maximum actual direct children for that owner; empirical conservative envelope, not a formal CPU bound; never subtracted'}
 for name in sorted(set(expected.get('A',[]))|set(expected.get('B',[]))):
  sides=values[name]
  row={'status':'INCOMPLETE','A':summary(sides['A']),'B':summary(sides['B']),'sourcePresence':{s:name in expected.get(s,[]) for s in 'AB'},'inclusive':{s:summary(v) for s,v in incs[name].items()},'blocks':{s:{str(b):summary(v) for b,v in m.items()} for s,m in blocks[name].items()},'reasons':[]}
  result['scopes'][name]=row
  if any(len(v)<20 for v in sides.values()) or any(set(blocks[name][s])!={0,1,2,3} or not all(blocks[name][s].values()) for s in 'AB'):
   row['reasons'].append('Absent/startup-only/sparse: need 20 steady calls per side and each side in every round');continue
  if reasons or set(observer)!={'A','B'}:row['reasons'].append('Global integrity/state/acquisition/observer failure');continue
  multiplicity={s:max(children[name][s]) for s in 'AB'}
  u=sum((2+2*multiplicity[s])*observer[s]['clockStepMs']+(1+multiplicity[s])*max(observer[s]['maximumEmptyMs'],observer[s]['maximumNestedMs']) for s in 'AB')
  row['observerUncertaintyMs']=u;row['maximumDirectChildren']=multiplicity
  verdicts=[];noise=False
  for metric in ['medianMs','p95Ms']:
   pooled=compare(row['A'][metric],row['B'][metric],u)
   paired={str(b):compare(row['blocks']['A'][str(b)][metric],row['blocks']['B'][str(b)][metric],u) for b in range(4)}
   spread={s:max(x[metric] for x in row['blocks'][s].values())-min(x[metric] for x in row['blocks'][s].values()) for s in 'AB'}
   all_verdicts=[pooled['verdict']]+[p['verdict'] for p in paired.values()]
   noisy=any(v>pooled['allowanceMs'] for v in spread.values());noise=noise or noisy
   verdict='INCOMPLETE' if noisy else 'FAIL' if 'FAIL' in all_verdicts else 'INCOMPLETE' if 'INCOMPLETE' in all_verdicts else 'PASS'
   row[metric]={'pooled':pooled,'pairedRounds':paired,'sameSideBlockSpreadMs':spread,'verdict':verdict};verdicts.append(verdict)
  row['roundCallRates']={str(b):{s:row['blocks'][s][str(b)]['n']/10 for s in 'AB'} for b in range(4)}
  rate_change=any(abs(v['B']-v['A'])>max(.2,.1*v['A']) for v in row['roundCallRates'].values())
  if rate_change:row['reasons'].append('Call-rate difference exceeds max(0.2 Hz, 10% baseline); callback work/frequency attribution remains incomplete')
  if noise:row['reasons'].append('Unexplained same-side round spread exceeds allowance; descriptive breaches retained without definitive owner verdict')
  row['status']='INCOMPLETE' if noise else 'FAIL' if 'FAIL' in verdicts else 'INCOMPLETE' if 'INCOMPLETE' in verdicts or rate_change else 'PASS'
 result['status']='BOUNDED_OWNER_RESULTS' if result['scopes'] and not reasons else 'INCOMPLETE'
 return result
