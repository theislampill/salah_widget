from pathlib import Path
import sys,json,hashlib,collections,statistics,math,datetime,bisect
O=Path(r'${WORK_ROOT}');C=O/'cost';D=O/'independent-review';N=C/'runs/events-resources-r123'
sys.path.insert(0,str(C))
from native_profile_v5 import read_marks,select_export_prefix,decode,stats
from analyse_cost_v5 import interval,compare,ENDPOINT_ERROR_MS
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((N/'RESULTS.json').read_bytes())
selected=[s for s in source['slots'] if not s.get('resourceOnly')]
assert len(selected)==6 and [(s['scene'],s['side']) for s in selected]==[(sc,side) for sc in ['night','twilight','day'] for side in 'AB']
result={'schema':'r0021-independent-events-r123/v1','createdUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceResultsSha256':sha(N/'RESULTS.json'),'sourceMapSha256':sha(C/'instrumented-r123-reviewed/SOURCE-MAP.json'),'decoderSha256':sha(C/'native_profile_v5.py'),'budgetAnalysisSha256':sha(C/'analyse_cost_v5.py'),'scriptSha256':sha(Path(__file__)),'runtime':{s:source['runtime'][s]['treeSha256'] for s in 'AB'},'method':{'selection':'Six ordinary cases only; native export prefix and original LIFO endpoints. Every synchronous observer before/after envelope excluded with any overlapping entire callback, including nested/adopted work. Probe controls excluded from event populations. No new acquisition.','metrics':['inclusiveMs','exclusiveMs'],'inclusiveOverhead':'All nested probe descendants; full maximum empty/nested endpoint envelope, no outlier removal.','exclusiveOverhead':'Original direct-child multiplier, preserved for attribution only; inclusive remains actual owner cost.','endpointErrorMs':ENDPOINT_ERROR_MS,'budgets':'Median and p95 increase <= max(0.25 ms, 10% baseline).','limits':['One finite actual-event observation per scene/side; no invented warmed repetitions or same-side noise estimate.','A/B phase durations differ; rates retained descriptively, no elapsed-workload equivalence implied.','Sparse, unequal, observer-only and source-noncorresponding classes remain INCOMPLETE.','Native elapsed callback intervals are not worker CPU or hardware presentation.','Unchanged-weather control is a read, not a second accepted refresh.','TA5 does not waive actual events; historical moon.poll transfer remains narrow.']},'slots':{},'comparisons':{}}
allgroups={}
rare={'head.prepareNativeFirstPaint','sky.accept','sky.workerMessage','moon.adopt','moon.workerMessage','preview.prepareForeground','preview.publishPreview','preview.rejectPreview','preview.paintFailed','sky.publishComposition','sky.rejectComposition','sky.compositionFailed','mask.decodeFulfilled','mask.decodeRejected'}
for declared in selected:
 sid=declared['id'];sd=N/sid;slot=json.loads((sd/'SLOT.json').read_bytes());raw=json.loads((sd/'CALLS.json').read_bytes());profile=json.loads((sd/'PROFILE.json').read_bytes())
 assert slot['status']=='RETURNED_FOR_REVIEW' and slot['contextClosed'] and not slot['errors'] and not slot['profileStop'].get('dataLossOccurred',False)
 native=read_marks(profile,'chromium');del profile
 prefix,document,suffix=select_export_prefix(native,raw,slot['documentReadback'],'document/'+sid,'CrRendererMain')
 idx,calls=decode(prefix,raw,document['documentId'],'CrRendererMain');del native,raw
 m=[x for x in prefix if x['name'].startswith('r21:M:')]
 assert [int(x['name'].split(':',3)[2])for x in m]==list(range(len(m)))
 meta={}
 def collect(x):
  if isinstance(x,dict):
   if isinstance(x.get('name'),str) and x['name'].startswith('r21:M:'):meta[x['name']]=x
   for v in x.values():collect(v)
  elif isinstance(x,list):
   for v in x:collect(v)
 collect(slot)
 count=0;stack=[];matched=0
 for row in prefix:
  if row['name'].startswith('r21:S:'):count+=1;stack.append(int(row['name'].split(':')[2]))
  elif row['name'].startswith('r21:E:'):assert stack.pop()==int(row['name'].split(':')[2])
  elif row['name'].startswith('r21:M:'):
   assert not stack,'Boundary inside owned callback'
   if row['name'] in meta:
    x=meta[row['name']];assert x['count']==count and x['depth']==0 and not x['invalid'];matched+=1
 envelopes=[];opened=None
 for x in m:
  label=x['name'].split(':',3)[3]
  if label.startswith('observer.') and label.endswith('.before'):
   assert opened is None;opened=(label[:-7],x)
  elif label.startswith('observer.') and label.endswith('.after'):
   assert opened and opened[0]==label[:-6];envelopes.append({'label':opened[0],'before':opened[1]['name'],'after':x['name'],'startMs':opened[1]['at'],'endMs':x['at']});opened=None
 assert opened is None
 envends=[x['endMs']for x in envelopes]
 def observed(c):
  j=bisect.bisect_left(envends,c['startMs'])
  return j<len(envelopes) and envelopes[j]['startMs']<=c['endMs']
 desc=collections.Counter();nested=collections.defaultdict(collections.Counter)
 for c in calls:
  parent=c['parent']
  while parent is not None:
   desc[parent]+=1;nested[parent][c['scope']]+=1;parent=calls[parent]['parent']
 controls={}
 for kind in ['empty','nested']:
  values=[]
  for x in prefix:
   if x['name'].startswith('r21:C:') and x['name'].endswith(':S') and x['name'].split(':')[-3]==kind:
    end=idx[x['name'][:-1]+'E'];assert end['at']>=x['at'];values.append(end['at']-x['at'])
  assert len(values)==200;controls[kind]=stats(values)
 maximum=max(v['max']for v in controls.values())
 bounds={x['name'].split(':',3)[3]:x['at']for x in m if not x['name'].split(':',3)[3].startswith('observer.')}
 anchor=prefix[0]['at'];final=bounds['final.admitted'];minute=bounds['minute-geometry.before'];minuteend=bounds['minute-geometry.after']
 ranges={'startup-through-final':(anchor,final),'clock-minute-change':(minute,minuteend),'between-final-and-minute':(final,minute),'after-minute':(minuteend,prefix[-1]['at'])}
 groups=collections.defaultdict(list);parentgroups=collections.defaultdict(list);excluded=collections.Counter();rare_rows=[]
 for c in calls:
  if c['scope'].startswith('probe.'):continue
  if observed(c):excluded[c['scope']]+=1;continue
  phase=next((p for p,(a,b)in ranges.items() if a<=c['startMs'] and c['endMs']<=b),None)
  if not phase:excluded['phase-crossing:'+c['scope']]+=1;continue
  parent=calls[c['parent']]['scope'] if c['parent']is not None else '<root>'
  root=c
  while root['parent']is not None:root=calls[root['parent']]
  branch='all'
  if c['scope']=='mask.publish':branch='real-decode' if nested[c['token']]['image.decodeInitiation'] else 'synchronous-finish' if nested[c['token']]['mask.finish'] else 'without-finish-or-decode'
  elif c['scope'] in ['sky.compose','preview.paint']:branch='publication-attempt' if nested[c['token']]['mask.publish'] else 'no-publication'
  v={**c,'descendants':desc[c['token']],'parentScope':parent,'rootScope':root['scope'],'phase':phase,'branch':branch}
  groups[(phase,c['scope'],branch)].append(v);parentgroups[(phase,c['scope'],parent)].append(v)
  if c['scope']in rare:rare_rows.append({k:v[k]for k in ['token','scope','parentScope','rootScope','phase','startMs','endMs','inclusiveMs','exclusiveMs','children','descendants']}|{'relativeStartMs':c['startMs']-anchor,'nestedScopes':dict(nested[c['token']])})
 def summarise(rows,phase):
  a,b=ranges[phase];excludedtime=sum(max(0,min(b,e['endMs'])-max(a,e['startMs']))for e in envelopes)
  return {'count':len(rows),'inclusiveMs':stats([x['inclusiveMs']for x in rows]),'exclusiveMs':stats([x['exclusiveMs']for x in rows]),'inclusiveTotalMs':sum(x['inclusiveMs']for x in rows),'maximumChildren':max(x['children']for x in rows),'maximumDescendants':max(x['descendants']for x in rows),'phaseNativeDurationMs':b-a,'observerEnvelopeDurationMs':excludedtime,'countPerNaturalSecond':len(rows)/((b-a-excludedtime)/1000) if b-a-excludedtime>0 else None}
 allgroups[sid]={k:summarise(v,k[0])for k,v in groups.items()}
 result['slots'][sid]={'side':slot['side'],'scene':slot['scene'],'status':slot['status'],'rawHashes':{n:sha(sd/n)for n in ['SLOT.json','CALLS.json','PROFILE.json']},'document':document,'decodedCalls':len(calls),'nativeBoundaries':len(m),'pageMetadataBoundariesVerified':matched,'excludedSuffix':suffix,'controls':controls,'fullMaximumControlMs':maximum,'observerEnvelopes':envelopes,'excludedCallsByScope':dict(excluded),'phaseRanges':ranges,'groups':[{'phase':k[0],'scope':k[1],'branch':k[2],**v}for k,v in sorted(allgroups[sid].items())],'parentGroups':[{'phase':k[0],'scope':k[1],'parentScope':k[2],**summarise(v,k[0])}for k,v in sorted(parentgroups.items())],'rareNaturalCalls':rare_rows,'profileStop':slot['profileStop'],'contextClosed':slot['contextClosed']}
 print(sid,len(calls),'observer-excluded',sum(excluded.values()),'controlsMax',maximum,flush=True)
for scene in ['night','twilight','day']:
 a=result['slots']['chromium-'+scene+'-A'];b=result['slots']['chromium-'+scene+'-B'];aa=allgroups['chromium-'+scene+'-A'];bb=allgroups['chromium-'+scene+'-B'];rows=[]
 for key in sorted(set(aa)|set(bb)):
  phase,scope,branch=key
  if phase not in ['startup-through-final','clock-minute-change']:continue
  av,bv=aa.get(key),bb.get(key);r={'phase':phase,'scope':scope,'branch':branch,'A':av,'B':bv,'disposition':'INCOMPLETE_PENDING_SOURCE_EVENT_MAPPING'};rows.append(r)
  if av and bv:
   r['countsEqual']=av['count']==bv['count'];r['observedDeltaMs']={metric:{stat:bv[metric][stat]-av[metric][stat]for stat in ['median','p95']}for metric in ['inclusiveMs','exclusiveMs']};r['bounds']={}
   for metric in ['inclusiveMs','exclusiveMs']:
    sub='maximumDescendants' if metric=='inclusiveMs' else 'maximumChildren'
    r['bounds'][metric]={stat:compare(interval(av[metric][stat],(1+av[sub])*a['fullMaximumControlMs'],(2+2*av[sub])*ENDPOINT_ERROR_MS),interval(bv[metric][stat],(1+bv[sub])*b['fullMaximumControlMs'],(2+2*bv[sub])*ENDPOINT_ERROR_MS))for stat in ['median','p95']}
 result['comparisons'][scene]=rows
out=D/'events-r123-offline-analysis-r1.json'
with out.open('x',encoding='utf-8',newline='\n')as f:json.dump(result,f,indent=2);f.write('\n')
print('OUTPUT',str(out),'SHA256',sha(out),flush=True)
for scene,rows in result['comparisons'].items():
 for r in rows:
  if r['scope']in ['sky.accept','head.prepareNativeFirstPaint','moon.adopt','sky.workerMessage','preview.prepareForeground','mask.publish','image.decodeInitiation']:
   print(json.dumps({'scene':scene,**{k:r[k]for k in ['phase','scope','branch']},'counts':[r[s]['count']if r[s]else None for s in 'AB'],'inclusiveMedianP95':[[r[s]['inclusiveMs']['median'],r[s]['inclusiveMs']['p95']]if r[s]else None for s in 'AB'],'boundedVerdicts':{k:v['verdict']for k,v in r.get('bounds',{}).get('inclusiveMs',{}).items()}}),flush=True)
