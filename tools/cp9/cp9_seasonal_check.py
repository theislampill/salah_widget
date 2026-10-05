#!/usr/bin/env python3
"""Broader joined matrix: measured solar state, not clock-time labels inferred as darkness."""
from pathlib import Path
import argparse,json,hashlib,math
from native_browser_check import run as browser_run,ROOT

def scenes():
 sites=[('florida',28.5383,-81.3792,'America/New_York'),('madinah',24.47,39.61,'Asia/Riyadh'),('iceland',64.1466,-21.9426,'Atlantic/Reykjavik'),('sydney',-33.8688,151.2093,'Australia/Sydney')]
 rows=[]
 for name,lat,lon,tz in sites:
  for month in [1,4,7,10]:
   for time in ['00:30','12:30']:
    rows.append({'name':f'{name}-{month:02}-{time[:2]}','lat':lat,'lon':lon,'tz':tz,'time':time,'utcBase':f'2026-{month:02}-15T12:00:00Z','cloud':60 if month==4 else 0,'wx':2 if month==4 else 0})
 base={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','time':'23:30','cloud':60,'wx':2}
 for d in [1,1.37,2,3]:rows.append({**base,'name':f'joined-dpr-{d}','dpr':d})
 for name,lat,lon,extra in [('north-pole',89.9,0,'&skyAlt=89&skyFov=120'),('south-pole',-89.9,0,'&skyAlt=89&skyFov=120'),('horizon',0,0,'&skyAlt=0&skyFov=90'),('horizon-rolled',0,0,'&skyAlt=0&skyFov=90&skyRoll=90'),('az-wrap',0,180,'&skyAz=360&skyFov=150'),('narrow-field',24.47,39.61,'&skyFov=10'),('strict-horizon',0,0,'&skyAlt=5&skyEstimates=off')]:
  rows.append({**base,'name':name,'lat':lat,'lon':lon,'tz':'UTC','extra':extra,'cloud':0,'wx':0})
 return rows

def verify(rows):
 cases=[]
 for r in rows:
  s=r['state'];h=s.get('native') or {};sky=s.get('sky') or {};p=sky.get('last') or {};d=p.get('diffuseState') or {};a=p.get('atmosphere') or {};c=p.get('composition') or {};fail=[]
  def check(ok,msg):
   if not ok:fail.append(msg)
  check(not r['error'] and not r['pageErrors'],'browser readiness/errors')
  check(s['prayerRows']==6 and s['syntheticPoints']==0,'prayer and no synthetic population')
  check(sky.get('status')=='ready' and 'real-sky-composed' in s['classes'],'joined physical sky ready')
  check(s['qa']['moonTruth']['surface']['status']=='pbr','native PBR retained')
  check(p.get('utcMs')==h.get('utcMs') and p.get('observer',{}).get('latDeg')==r['scene']['lat'],'accepted observer/UTC')
  check(p.get('catalogue',{}).get('emitters')==8884,'exact emitting catalogue')
  check(d.get('sourceSha256')=='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446','admitted map identity')
  check(a.get('cloudTransmission')==1 and c.get('cloudApplications')==1,'once-only clouds')
  check(d.get('budget',{}).get('afterGas')==d.get('budget',{}).get('afterCloud'),'no hidden second gas/cloud multiplier')
  check(d.get('nightBudget',{}).get('mode')=='nonstellar-residual-replaces-legacy-floor','night accounting')
  check(p.get('view',{}).get('width')==325 and p.get('view',{}).get('height')==530,'declared physics raster remains fixed across display DPR')
  sun=p.get('physicalState',{}).get('sun',{}).get('altDeg');moon=p.get('physicalState',{}).get('moon',{})
  check(isinstance(sun,(float,int)) and math.isfinite(sun) and -90<=sun<=90,'finite solar geometry')
  if sun is not None and sun>20:check(p.get('detectableSources')==0,'day contrast, not source deletion')
  if r['scene']['name']=='strict-horizon':check(d.get('exposureComplete') is False and d.get('missingPixels',0)>0,'strict support not fabricated')
  cases.append({'name':r['scene']['name'],'status':'PASS' if not fail else 'FAIL','failures':fail,'sunAltitudeDeg':sun,'moonAltitudeDeg':moon.get('altDeg'),'moonFraction':moon.get('illuminatedFraction'),'detectableBeforeForeground':p.get('detectableSources'),'drawn':p.get('drawn'),'renderMs':p.get('timings',{}).get('renderMs'),'composeMs':c.get('lastComposeMs'),'secondsToReady':r['seconds'],'startupWithin15s':r['seconds']<=15,'estimatedPixels':d.get('estimatedPixels'),'missingPixels':d.get('missingPixels'),'physicsRaster':[325,530],'displayDpr':r['scene'].get('dpr',1)})
 return {'status':'PASS' if all(c['status']=='PASS' for c in cases) else 'FAIL','cases':cases,'sceneCount':len(rows),'startupBudgetSeconds':15,'startupBudgetExceeded':[c['name'] for c in cases if not c['startupWithin15s']],'scope':'Actual native widget, fixed provider/date fixtures; OS/engine identity is recorded on each scene. DPR values are display scaling of declared DPR-1 physics; no claim of native high-DPR optical resolution.'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);a.add_argument('--verify-only',action='store_true');x=a.parse_args();x.output.mkdir(parents=True,exist_ok=True)
 if not x.verify_only:rows=browser_run(x.root,x.output,scenes=scenes())
 else:rows=json.loads((x.output/'results.json').read_text(encoding='utf-8'))
 result=verify(rows);result['runtimeSha256']=hashlib.sha256((x.root/'real-sky/native-sky.js').read_bytes()).hexdigest();(x.output/'acceptance.json').write_text(json.dumps(result,indent=2));print('CP9 SEASONAL',result['status'],len(rows),flush=True);raise SystemExit(0 if result['status']=='PASS' else 1)
