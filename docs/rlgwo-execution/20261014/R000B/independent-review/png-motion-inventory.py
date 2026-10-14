from pathlib import Path
import hashlib,json,sys,struct
sys.path.insert(0,r'C:\Users\theis\AppData\Local\Programs\Python\Python311\Lib\site-packages')
import numpy as np
from PIL import Image
b=Path(r'C:\workspace\ai\r000b-execution-20261014');root=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
sha=lambda v:hashlib.sha256(v).hexdigest()
def bind(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
out={'schema':'r000b-independent-native-png-inventory/v1','limitation':'All original PNGs are hashed and inventoried. Region metrics only nominate visual review, never motion/readability acceptance. No images are modified.','cases':{}}
for case in ['firefox-reduced','firefox-full']:
 p=b/'native-motion-capture'/case;r=json.loads((p/'receipt.json').read_bytes());w=r['watches'][0];frames=w['frames'];rows=[];unique={};previous=None
 for n,f in enumerate(frames):
  assert f['ordinal']==n
  q=p/f['file'];blob=q.read_bytes();assert sha(blob)==f['sha256'];assert struct.unpack('>II',blob[16:24])==(390,600)
  a=np.asarray(Image.open(q).convert('RGB'));rgbsha=sha(a.tobytes());unique.setdefault(rgbsha,n)
  regions={'card':a[:530,:325],'header':a[16:43,60:220],'footer':a[500:525,20:305],'cloud':a[85:210,20:305],'moon':a[35:125,220:310]}
  stats={k:{'mean':float(v.mean()),'std':float(v.std())} for k,v in regions.items()}
  rows.append({**f,'bytes':len(blob),'decodedRgbSha256':rgbsha,'dimensions':[390,600],'suspect':stats['card']['std']<5 or stats['header']['std']<3 or stats['footer']['std']<3,'regions':stats,'previousCloudMae':None if previous is None else float(np.abs(regions['cloud'].astype(float)-previous).mean())})
  previous=regions['cloud'].astype(float)
 ri=w['reviewInterval'];gaps=[z['startHostMonotonic']-a['startHostMonotonic'] for a,z in zip(frames,frames[1:])];dur=[f['endHostMonotonic']-f['startHostMonotonic'] for f in frames]
 assert ri['startFixtureElapsedMs']==frames[0]['afterClock']['elapsedMs'] and ri['endFixtureElapsedMs']==ri['startFixtureElapsedMs']+30000
 assert ri['startHostMonotonic']==frames[0]['afterClockReceivedHostMonotonic'] and ri['endHostMonotonic']==ri['startHostMonotonic']+30
 checks={'frameCount':len(frames)>=240,'maxStartGap':max(gaps)<=.25,'maxCapture':max(dur)<=.25,'lastBeforeClockBracketsEnd':frames[-1]['beforeClock']['elapsedMs']>=ri['endFixtureElapsedMs'],'lastStartHostBracketsEnd':frames[-1]['startHostMonotonic']>=ri['endHostMonotonic'],'durationWithin30to60':30000<=frames[-1]['beforeClock']['elapsedMs']-frames[0]['afterClock']['elapsedMs']<=60000,'native1xEveryCapture':all(abs((f['afterClock']['wallUtcMs']-f['beforeClock']['wallUtcMs'])-(f['afterClock']['elapsedMs']-f['beforeClock']['elapsedMs']))<10 for f in frames),'captureBoundsOrdered':all(f['startHostMonotonic']<=f['endHostMonotonic']<=f['afterClockReceivedHostMonotonic'] and f['beforeClock']['elapsedMs']<=f['afterClock']['elapsedMs'] for f in frames)}
 drift=[]
 for rel,e in r['runtime']['files'].items():
  z=(root/rel).read_bytes()
  if len(z)!=e['bytes'] or sha(z)!=e['sha256']:drift.append(rel)
 stateBindings=[]
 for o in r['observations']:
  s=o['state'];a=o['afterScreenshotState'];assert all(a[k]==s[k] for k in ['card','rows','temperature','icon','modelEligible','cloudPopulation','clock']) and all(a['raw'].get(k)==s['raw'].get(k) for k in ['currentValidAt','currentIntervalSec','retrievedAt'])
  q=p/o['stateScreenshot']['file'];v=bind(q);assert v['sha256']==o['stateScreenshot']['sha256'];stateBindings.append(v)
 video=bind(p/r['video']['file']);assert video['sha256']==r['video']['sha256'];ix=p/'pixel-review/index.json';index=json.loads(ix.read_bytes());assert index['videoSha256']==video['sha256']
 obs=[{'stage':o['stage'],'hostMonotonic':o['hostMonotonic'],'elapsedMs':o['state']['elapsedMs'],'afterElapsedMs':o['afterScreenshotState']['elapsedMs'],'temperature':o['state']['temperature'],'icon':o['state']['icon'],'fx':o['state']['fx'],'precip':o['state']['precip'],'motion':o['state']['motion'],'moon':o['state']['qa']['moonTruth']['surface'],'cloudPopulation':o['state']['cloudPopulation']} for o in r['observations']]
 out['cases'][case]={'receipt':bind(p/'receipt.json'),'video':video,'videoIndex':bind(ix),'ancillaryVideoInventory':{'frameCount':index['frameCount'],'durationPts':index['durationPts'],'suspects':[s for s in index['samples'] if s['suspect']]},'driverSha256':r['driverSha256'],'sourceSha256':r['sourceSha256'],'wrapperSha256':r['wrapperSha256'],'runtimeSha256':r['runtime']['sha256'] if 'sha256' in r['runtime'] else None,'runtimeFilesVerified':len(r['runtime']['files']),'runtimeDrift':drift,'browser':r['browser'],'url':r['url'],'nativeChecks':r['checks'],'recomputedTimingChecks':checks,'reviewInterval':ri,'firstFrame':frames[0],'lastFrame':frames[-1],'maxStartGapSeconds':max(gaps),'maxCaptureSeconds':max(dur),'uniqueRgbCount':len(unique),'uniqueRgbFirstOrdinals':list(unique.values()),'nominatedFrames':[v['ordinal'] for v in rows if v['suspect']],'stateBindings':stateBindings,'observations':obs,'observerEvents':[{'action':v['action'],'at':v['at']} for v in r['fixture']['weatherEvents']],'rows':rows}
dest=b/'independent-review/png-motion-inventory.json';dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'inventory':bind(dest),'cases':{k:{kk:vv for kk,vv in v.items() if kk!='rows'} for k,v in out['cases'].items()}}))

