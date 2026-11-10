"""Predeclared TA2 mapping: actual inclusive moon.poll, main.paint and main.render.
Reuse the r76 native intervals/calibration. No new acquisition or tolerance.
Count all nested probe descendants, retaining original overhead/clock/noise/rate
rules and both windows. No startup/rare/changed-weather/resource PASS is inferred.
"""
from pathlib import Path
import collections,hashlib,json,sys
from analyse_cost_v5 import interval,compare,metric_verdict,combine_windows,summary,ENDPOINT_ERROR_MS
from native_profile_v5 import read_marks,decode,select_export_prefix
O=Path(__file__).resolve().parents[1];source=O/'cost/runs/chromium-native-v5-r76'
dest=O/'cost/inclusive-r110';assert not dest.exists();dest.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'ANALYSIS.json')=='3e1d12ecc2f911e6fdcad7c5784fd957c78aa0b733815bcf1d303eac7129a9ef'
old=json.loads((source/'ANALYSIS.json').read_bytes());record=json.loads((source/'RESULTS.json').read_bytes())
assert old['status']=='BOUNDED_OWNER_RESULTS'and not old['globalReasons']and old['sequenceComplete']
owners=['moon.poll','main.paint','main.render']
result={'schema':'r0021-inclusive-cost-derivation/v1','mapping':__doc__,'scriptSha256':sha(Path(__file__)),'originalAnalysisSha256':sha(source/'ANALYSIS.json'),'originalResultsSha256':sha(source/'RESULTS.json'),'engine':record['engine'],'runtime':{s:record['runtime'][s]['treeSha256']for s in 'AB'},'controls':{},'slots':{},'windows':{},'unchangedHistoricalOwners':old['combinedOwners'],'limits':['Original acquisition and contrary variability retained. This is offline inclusive reanalysis, not final whole-cost certification.','Firefox submillisecond cost remains UNVERIFIED—OWNER-APPROVED EVIDENCE EXCEPTION.','Other startup/rare events, changed weather/mask cost and final candidate delta need their actual owner disposition.']}
controlMax={s:max(c['summary']['maxMs']for slot in record['slots']if slot['side']==s for c in old['calibration'][slot['id']]['controls'].values())for s in 'AB'}
result['controls']={'fullEmpiricalMaxMs':controlMax,'endpointErrorMs':ENDPOINT_ERROR_MS,'multiplicity':'all owned nested probe descendants, not just direct children'}
decoded={}
for slot in record['slots']:
 raw=source/slot['rawFile'];profile=source/slot['nativeProfileFile']
 assert sha(raw)==slot['callsSha256']and sha(profile)==slot['nativeProfileSha256']
 metadata=json.loads(raw.read_bytes());native=json.loads(profile.read_bytes())
 marks=read_marks(native,record['engine']);marks,document,excluded=select_export_prefix(marks,metadata,slot['documentReadback'],slot['documentMarkerLabel'],'CrRendererMain')
 index,calls=decode(marks,metadata,document['documentId'],'CrRendererMain')
 bounds={k:index[slot[k]['name']]['at']for k in ['warmStart','warmEnd','start','end']}
 assert bounds==old['calibration'][slot['id']]['boundariesNativeMs']
 descendants=collections.Counter();nested=collections.defaultdict(collections.Counter)
 for c in calls:
  parent=c['parent']
  while parent is not None:
   descendants[parent]+=1;nested[parent][c['scope']]+=1;parent=calls[parent]['parent']
 chosen=[{**{k:c[k]for k in ['token','scope','startMs','endMs','inclusiveMs','exclusiveMs','children']},'descendants':descendants[c['token']],'nestedScopes':dict(nested[c['token']])}for c in calls if c['scope']in owners and bounds['start']<=c['startMs']<bounds['start']+15000]
 decoded[slot['id']]=(slot,chosen,bounds)
 result['slots'][slot['id']]={'side':slot['side'],'block':slot['block'],'bounds':bounds,'originalCallsSha256':sha(raw),'originalProfileSha256':sha(profile),'decodedIntervals':len(calls),'selectedCalls':chosen}
 print(slot['id'],len(calls),flush=True)
for seconds in [5,15]:
 window={'durationSeconds':seconds,'scopes':{}};result['windows'][str(seconds)]=window
 for scope in owners:
  selected={s:[(slot,c)for slot,calls,b in decoded.values()if slot['side']==s for c in calls if c['scope']==scope and c['startMs']<b['start']+seconds*1000]for s in 'AB'}
  row={'metric':'inclusiveMs','A':summary([c['inclusiveMs']for _,c in selected['A']]),'B':summary([c['inclusiveMs']for _,c in selected['B']]),'blocks':{s:{str(i):summary([c['inclusiveMs']for slot,c in selected[s]if slot['block']==i])for i in range(4)}for s in 'AB'},'reasons':[],'reasonCodes':[]};window['scopes'][scope]=row
  assert all(row[s]['n']>=20 and all(row['blocks'][s][str(i)]['n']for i in range(4))for s in 'AB')
  counts={s:max(c['descendants']for _,c in selected[s])for s in 'AB'}
  overhead={s:(1+counts[s])*controlMax[s]for s in 'AB'};clock={s:(2+2*counts[s])*ENDPOINT_ERROR_MS for s in 'AB'}
  row.update(maximumProbeDescendants=counts,fullMaximumOverheadMs=overhead,clockErrorMs=clock)
  verdicts=[];noise=False
  for metric in ['medianMs','p95Ms']:
   pooled=compare(*(interval(row[s][metric],overhead[s],clock[s])for s in 'AB'))
   paired={str(i):compare(*(interval(row['blocks'][s][str(i)][metric],overhead[s],clock[s])for s in 'AB'))for i in range(4)}
   spread={s:max(v[metric]for v in row['blocks'][s].values())-min(v[metric]for v in row['blocks'][s].values())for s in 'AB'}
   noisy=any(v>max(.25,.1*row['A'][metric])for v in spread.values());noise|=noisy
   verdict=metric_verdict([pooled['verdict']]+[p['verdict']for p in paired.values()],noisy);verdicts.append(verdict)
   row[metric]={'pooled':pooled,'pairedRounds':paired,'sameSideBlockSpreadMs':spread,'verdict':verdict}
  row['roundCallRates']={str(i):{s:row['blocks'][s][str(i)]['n']/(2*seconds)for s in 'AB'}for i in range(4)}
  rate=any(abs(v['B']-v['A'])>max(.2,.1*v['A'])for v in row['roundCallRates'].values())
  if rate:row['reasonCodes'].append('RATE')
  if noise:row['reasonCodes'].append('NOISE')
  if 'INCOMPLETE'in verdicts and not noise:row['reasonCodes'].append('UNCERTAINTY')
  row['status']='INCOMPLETE'if noise else'FAIL'if 'FAIL'in verdicts else'INCOMPLETE'if rate or 'INCOMPLETE'in verdicts else'PASS'
result['combinedOwners']={scope:combine_windows(result['windows']['5']['scopes'][scope],result['windows']['15']['scopes'][scope])for scope in owners}
(dest/'RESULT.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps(result['combinedOwners']))
