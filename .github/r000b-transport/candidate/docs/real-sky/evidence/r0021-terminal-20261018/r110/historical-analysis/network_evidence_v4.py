"""Fail-closed source-based association, not a dedicated-worker initiator ID."""
import math
from urllib.parse import urlsplit

ASSET_PINS={
 'moon/assets/dem.bin.gz':{'bytes':20137935,'sha256':'ecd3a8e941edc7050e1e6c51e87f9084466e1ccfadf1eb57297302191de82960'},
 'moon/assets/colour.bin.gz':{'bytes':32272181,'sha256':'29948c38c12c4b9733789fa9ea1c13fb12b0b00035169876651f7a2ef3b6af34'}}

def eligible_startup_abort(row,origin):
 return row.get('failed') is True and row.get('failure')=='net::ERR_ABORTED' and row.get('method')=='GET' and row.get('type')=='fetch' and row.get('url') in {origin+'/salah_widget/'+p for p in ASSET_PINS}

def validate_network(slot,record):
 """Recompute from raw observations; never trusts the stored classification."""
 assert record['assetPins']==ASSET_PINS,'Pinned lunar asset identity'
 assert not slot['networkViolations'],'Unclassified network violation'
 origin=slot['origin'];u=urlsplit(origin)
 assert u.scheme=='http' and u.hostname=='127.0.0.1' and u.port and origin==f'http://127.0.0.1:{u.port}','Isolated exact origin'
 quiet=slot['quietStartMonotonic'];proof=slot['consumptionProvedAtMonotonic']
 assert all(isinstance(x,(float,int)) and math.isfinite(x) for x in [quiet,proof]) and 0<proof<quiet,'Consumption proof before quiet'
 rows=slot['network'];assert rows and len({r['id'] for r in rows})==len(rows),'Request identity/duplicate'
 for r in rows:
  start,end=r['startMonotonic'],r['endMonotonic']
  assert all(isinstance(x,(float,int)) and math.isfinite(x) for x in [start,end]) and 0<start<=end<quiet,'Network overlap/incomplete'
  assert r.get('failed') in [True,False],'Missing completion status'
  if r['failed']:assert eligible_startup_abort(r,origin),'Unexpected failed request'
  else:assert r.get('failure') is None,'Contradictory failure'
  assert r.get('responseStatus',0)<400,'HTTP error'
 failed=[r for r in rows if r['failed']]
 result={'association':'source-based unique asset consumer; no dedicated-worker network initiator ID','startupAbortsWithCurrentConsumption':[]}
 if not failed:return result
 assert record['engine']=='chromium','Abort classification is Chromium-only'
 s=slot['readyState'];moon=s['moon'];owner=s['owners']['moon']
 assert moon['current'] is True and moon['visibleSource']=='refined-terrain' and moon['pending'] is False and moon['workerAlive'] is True,'Current refined consumption'
 assert moon['retryCount']==0 and not moon['errors'],'Moon retry/error'
 assert owner['instanceCount']==1 and owner['workerPresent'] is True and owner['scalars']['ready'] is True and owner['scalars']['disposed'] is False,'Sole live ready Moon owner'
 matches=[w for w in s['workers'] if w['id']==owner['workerId']]
 assert len(matches)==1,'Current worker identity'
 w=matches[0];boot=w['boot'];job=owner['acceptedJob'];last=w['lastResult']
 assert w['reachable'] is True and w['terminated'] is False and not w['errors'],'Worker liveness/error'
 assert w['kinds']['boot']==1 and w['readyCount']==1,'Single completed boot'
 assert sum(1 for x in s['workers'] if (x.get('boot') or {}).get('base')==origin+'/salah_widget/moon/')==1,'Replaced/duplicate Moon boot'
 assert boot['base']==origin+'/salah_widget/moon/' and boot['offline'] is False and boot['embedded'] is False and boot['workerSourceLength']>0,'Exact native online source'
 assert 0<=boot['at']<=w['readyAt']<=last['at']<=s['at'],'Boot/ready/result observation order'
 assert job==last['identity'] and last['id']==job['id'] and job['epoch']==owner['scalars']['epoch'],'Current accepted job identity'
 assert isinstance(job['id'],int) and job['id']>0 and isinstance(job['key'],str) and job['key'],'Accepted job fields'
 # Both exact inputs must have one request/receipt for this sole boot. Source
 # boot waits for all owned shard validators (historical A:2, candidate B:4).
 for path,pin in ASSET_PINS.items():
  url=origin+'/salah_widget/'+path;observed=[r for r in rows if r['url']==url]
  assert len(observed)==1,'Missing/duplicate asset request'
  r=observed[0]
  assert r['method']=='GET' and r['responseStatus']==200 and r['responseBytes']==pin['bytes'],'Exact asset response'
  assert r['startMonotonic']<=r['responseAtMonotonic']<=r['endMonotonic']<proof,'Response/completion before consumption proof'
  receipts=[x for x in record['requests'] if x['slot']==slot['id'] and x['side']==slot['side'] and x['path']=='/salah_widget/'+path]
  assert len(receipts)==1,'Missing/duplicate server receipt'
  served=receipts[0]
  assert served['status']==200 and served['servedSha256']==pin['sha256'] and served['bytes']==pin['bytes'] and served['writeComplete'] is True and not served.get('clientDisconnected') and not served.get('error'),'Exact complete served bytes'
  assert r['startMonotonic']<=served['monotonic']<=served['writeEndedMonotonic']<proof,'Server delivery before consumption proof'
  if r['failed']:result['startupAbortsWithCurrentConsumption'].append({'requestId':r['id'],'url':url,'failure':r['failure'],'sha256':pin['sha256'],'bytes':pin['bytes'],'workerId':w['id'],'acceptedJob':job})
 return result
