"""Compact city-bound actual-entry supplement to H8; no long solver campaign.

Prayer data are captured Aladhan calendar records selected without relabelling.
Weather is explicitly synthetic, with IANA-local timestamps generated via Intl.
Paused trajectory stills do not substitute for ordinary live weather acceptance.
"""
import argparse, hashlib, json, math, shutil, sys
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlsplit, parse_qs
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
import hotfix_stress_check as h
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def digest(data):return hashlib.sha256(data).hexdigest()

def prayer_checks(s,days,phase,date):
 record=days[date];clock=phase['localClock'];keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];timings={k:record['timings'][k].split()[0] for k in keys}
 following=next((k for k in keys if timings[k]>clock),None);next_date=date if following else (datetime.strptime(date,'%d-%m-%Y')+timedelta(days=1)).strftime('%d-%m-%Y');following=following or 'Fajr'
 next_time=days[next_date]['timings'][following].split()[0];display={**timings,following:next_time};render=s['render']
 return {'prayerRecord':all(r['time']==display[r['key']] for r in s['rows']),
         'sourceTimetable':render['timetableDate']==date and all(render['timetable'][k].split()[0]==timings[k] for k in keys),
         'nextSourceRecord':render['nextKey']==following and render['nextDate']==next_date and render['nextTime'].split()[0]==next_time}

def weather_checks(s,native,fixture,day=None):
 selected=s['weather']['selected'] or {};target=selected.get('target',{});current=fixture['payload']['current'];header=s['weather']['header'] or {};truth=s['weather']['truth'] or {}
 fields={'code':'weather_code','temp':'temperature_2m','feels':'apparent_temperature','rh':'relative_humidity_2m','dew':'dew_point_2m','wind':'wind_speed_10m','cloud':'cloud_cover','precip':'precipitation','vis':'visibility'}
 same=lambda a,b:isinstance(a,(int,float)) and isinstance(b,(int,float)) and abs(a-b)<1e-9
 category={'clear':'clear','partial':'cloud','overcast':'overcast','haze':'cloud','rain':'rain'}[fixture['weatherFamily']]
 icons={'clear':['☀️','🌙'] if day is None else ['☀️' if day else '🌙'],'cloud':['⛅','☁️'] if day is None else ['⛅' if day else '☁️'],'overcast':['☁️'],'rain':['🌧️']}[category]
 return {'weatherTarget':all(target.get(k)==native[k] for k in ['lat','lon','generation']),
         'weatherFields':all(same(selected.get(k),current[v]) for k,v in fields.items()) and selected.get('units')=='c',
         'weatherLane':selected.get('src')=='forecast' and selected.get('provider')=='Open-Meteo' and truth.get('lane')=='preview' and truth.get('observedPresent') is False,
         'headerSnapshot':header.get('generation')==native['generation'] and header.get('target')=={k:native[k] for k in ['lat','lon']} and header.get('code')==current['weather_code'] and same(header.get('temperature'),selected.get('temp')) and s['header']['temp']==str(round(current['temperature_2m']))+'°',
         'weatherPresentation':s['fx']==category and s['header']['icon'] in icons and 'preview' in s['header']['label'].lower(),
         'supportedParticles':(s['precip']=='on' and s['visibleParticles']>0) if category=='rain' else s['precip']=='off'}

def run(a):
 a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.root/'tests'));from v1_browser import fonts
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
 scenarios=read(a.fixtures/'A/scenarios.json')['scenarios'];weather=read(a.fixtures/'B/scenario-weather-fixtures.json')
 registry={};receipts=[];failures=[];rows=[];held=[];delay={'target':None}
 for scenario in scenarios:
  site=scenario['site'];name=site['name'];source=Path(scenario['calendarResponse']);source=source if source.is_absolute() else a.fixtures/source;assert digest(source.read_bytes())==scenario['calendarResponseSha256']
  calendar=read(source)['data'];days={r['date']['gregorian']['date']:r for r in calendar}
  w=next(r for r in weather['cases'] if r['city']==name and r['phase']=='dawn')
  assert w['target']['tz']==site['tz'] and w['target']['lat']==site['lat'] and w['target']['lon']==site['lon']
  registry[name]={'site':site,'days':days,'weather':w,'scenario':scenario}
 def route(r,e):
  u=urlsplit(r.request.url);q=parse_qs(u.query);lat=float(q['latitude'][0]);lon=float(q['longitude'][0])
  matches=[v for v in registry.values() if v['site']['lat']==lat and v['site']['lon']==lon]
  assert len(matches)==1,('Unknown exact request target',r.request.url)
  v=matches[0];site=v['site'];name=site['name']
  if u.hostname=='api.aladhan.com':
   assert int(q['method'][0])==site['method'];assert int(q.get('school',['0'])[0])==0
   day=u.path.rsplit('/',1)[-1];record=v['days'].get(day)
   if record is None:r.fulfill(status=404,body='No source-qualified timetable for this date');return
   assert record['meta']['timezone']==site['tz'] and record['meta']['latitude']==lat and record['meta']['longitude']==lon
   data=json.dumps({'code':200,'status':'OK','data':record},separators=(',',':')).encode()
   receipt={'provider':'Aladhan captured calendar record','target':name,'date':day,'request':r.request.url,'sha256':digest(data),'record':record,'transformation':'Exact calendar day object wrapped as timings endpoint; no changed date, target, policy or timing.'}
  else:
   assert q['timezone'][0]==site['tz'] and q['temperature_unit'][0]=='celsius' and q['wind_speed_unit'][0]=='ms'
   payload=v['weather']['payload'];data=json.dumps(payload,separators=(',',':')).encode()
   receipt={'provider':'Synthetic current/hourly model fixture','target':name,'request':r.request.url,'sha256':digest(data),'fixtureCase':v['weather']['caseId'],'weatherFamily':v['weather']['weatherFamily'],'mode':'Fixed input for paused geographical scene, not live weather or owner observation'}
  receipts.append(receipt)
  response={'body':data,'content_type':'application/json','headers':{'Access-Control-Allow-Origin':'*'}}
  if name==delay['target']:
   receipt['delayedOldGeneration']=True;held.append((r,response,receipt));return
  r.fulfill(**response)
 report={'status':'RUNNING','runtime':runtime_identity(a.root),'scope':__doc__,'scenariosSha256':digest((a.fixtures/'A/scenarios.json').read_bytes()),'weatherFixturesSha256':digest((a.fixtures/'B/scenario-weather-fixtures.json').read_bytes()),'cases':rows,'providerReceipts':receipts,'failures':failures}
 with sync_playwright() as pw:
  b=launch_browser(pw);report['browser']=browser_identity(b)
  for name,v in registry.items():
   site=v['site'];phases=v['scenario']['phases'];out=a.out/name;observer={**site,'method':str(site['method']),'label':name+' fixture'}
   e=h.Entry(b,a.root,out,ff,start=phases[0]['utc'],rate=0,observer=observer,provider_route=route)
   try:
    for phase in phases:
     utc=phase['utcMs'];e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',utc);e.ready();e.page.wait_for_timeout(500)
     s=e.snap(phase['phase']);native=e.frame.evaluate('()=>({lat,lon,tz,method,generation:_runtimeGeneration,label:document.querySelector("#loc")?.textContent})')
     sun=s['sun']['physical'];sel=s['weather']['selected'];record=v['days']['08-10-2026'];expected={k:record['timings'][k].split()[0] for k in ['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha']}
     checks=h.semantic(s)
     checks.update(target=all(native[k]==site[k] for k in ['lat','lon','tz']) and str(native['method'])==str(site['method']),label=native['label'].lower()==observer['label'].lower(),utc=s['utc']==utc,prayerRecord=all(r['time']==expected[r['key']] for r in s['rows']),weatherRecord=sel is not None and sel['code']==v['weather']['payload']['current']['weather_code'],finiteGeometry=all(math.isfinite(sun[k]) for k in ['altDeg','azDeg']),solarDirection=abs(sun['altDeg']-phase['physicalSun']['altDeg'])<.01 and abs((sun['azDeg']-phase['physicalSun']['azDeg']+180)%360-180)<.01)
     styles=s['sun']['presentation'];checks['noBodyBeforeHorizon']=sun['altDeg']>-1.5 or max(float(styles['--sunamt']),float(styles['--sunbodyamt']))==0
     # The next row deliberately promotes tomorrow's Fajr after Isha. Its
     # expected clock comes from the next source calendar record, not today.
     # Condition icons also retain their defined daytime/nighttime variants.
     date=datetime.strptime(v['scenario']['date'],'%Y-%m-%d').strftime('%d-%m-%Y')
     checks.update(prayer_checks(s,v['days'],phase,date))
     day=expected['Sunrise']<=phase['localClock']<expected['Maghrib']
     checks.update(weather_checks(s,native,v['weather'],day))
     row={'city':name,'phase':phase['phase'],'native':native,'state':s,'checks':checks,'weatherMode':'Declared synthetic paused forecast/model lane','prayerSource':v['scenario']['calendarResponseSha256']};rows.append(row)
     if not all(checks.values()):failures.append({'city':name,'phase':phase['phase'],'checks':checks})
     h.dump(a.out/'results.json',report);print(name,phase['phase'],checks,flush=True)
    if name=='CentralFlorida':
     # Real settings ingress, held B provider responses, then a new A epoch.
     # No private clock or reused A generation: the native applyConfig owner
     # performs its normal cancellation/admission work in the living iframe.
     e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',phases[2]['utcMs']);e.ready()
     a1=e.frame.evaluate('()=>_runtimeGeneration');delay['target']='Berlin'
     bsite=registry['Berlin']['site'];bcfg={**bsite,'method':str(bsite['method']),'label':'Berlin fixture'}
     e.frame.evaluate('cfg=>{void applyConfig({...CONFIG,...cfg},{save:false});}',bcfg)
     e.page.wait_for_timeout(600);bg=e.frame.evaluate('()=>_runtimeGeneration')
     b_pending=e.frame.evaluate('()=>({lat,lon,tz,generation:_runtimeGeneration,model:model()})')
     delay['target']=None
     e.frame.evaluate('cfg=>{void applyConfig({...CONFIG,...cfg},{save:false});}',observer)
     e.ready();e.page.wait_for_timeout(500);a2=e.frame.evaluate('()=>_runtimeGeneration')
     delayed_count=len(held)
     for request,response,receipt in held:
      # A harness fulfillment failure must fail this run. Native aborted
      # transports are recorded separately, never inferred from any exception.
      request.fulfill(**response);receipt['release']='fulfillment completed after A2';receipt['transportFailure']=request.request.failure
     held.clear();e.page.wait_for_timeout(1000)
     after=e.snap('A-B-A-after-late-B');identity=e.frame.evaluate('()=>({lat,lon,tz,generation:_runtimeGeneration,label:document.querySelector("#loc")?.textContent})')
     checks=h.semantic(after);checks.update(newEpoch=a1<bg<a2==identity['generation'],heldB=delayed_count>=2,returnedA=all(identity[k]==site[k] for k in ['lat','lon','tz']),headerA=identity['label'].lower()==observer['label'].lower(),weatherA=after['weather']['selected'] is not None and after['weather']['selected']['code']==v['weather']['payload']['current']['weather_code'],prayerA=all(r['time']==expected[r['key']] for r in after['rows']))
     # Applying settings rebinds the native clock from configuration. Compare
     # the actually accepted UTC after that rebind, not the earlier noon seek.
     civil=e.frame.evaluate('s=>{const p=Object.fromEntries(new Intl.DateTimeFormat("en-GB",{timeZone:s.zone,year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date(s.utc)).map(p=>[p.type,p.value]));return {date:p.day+"-"+p.month+"-"+p.year,localClock:p.hour+":"+p.minute};}',{'zone':site['tz'],'utc':after['utc']})
     checks['acceptedClock']=after['render']['sim']==civil['date']+' '+civil['localClock']
     checks.update(prayer_checks(after,v['days'],civil,civil['date']))
     checks.update(weather_checks(after,identity,v['weather'],expected['Sunrise']<=civil['localClock']<expected['Maghrib']))
     report['locationABA']={'generations':[a1,bg,a2],'pendingB':b_pending,'delayedResponses':delayed_count,'after':after,'identity':identity,'acceptedCivil':civil,'checks':checks,'scope':'Real request cancellation/currentness and final DOM. Configuration rebinds the accepted clock; its actual UTC is independently formatted through Intl. A cancelled transport is not claimed as a delivered late body; post-parse late-body generation rejection has separate scalar controls.'}
     if not all(checks.values()):failures.append({'case':'A-B-A','checks':checks})
     h.dump(a.out/'results.json',report);print('A-B-A',checks,flush=True)
    if e.errors:failures.append({'city':name,'errors':e.errors})
   finally:e.close()
  b.close()
 report['runtimeUnchanged']=runtime_identity(a.root)==report['runtime'];report['status']='PASS' if not failures and report['runtimeUnchanged'] else 'FAIL'
 sheet=Image.new('RGB',(5*330,6*558),'#101828');d=ImageDraw.Draw(sheet)
 for y,(name,v) in enumerate(registry.items()):
  for x,p in enumerate(v['scenario']['phases']):
   im=Image.open(a.out/name/(p['phase']+'.png'));sheet.paste(im,(x*330,y*558+24));d.text((x*330+2,y*558+3),name+' '+p['phase'],fill='white')
 sheet.save(a.out/'geography.png');h.dump(a.out/'results.json',report);return report['status']=='PASS'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=h.ROOT);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True)
 raise SystemExit(0 if run(p.parse_args()) else 1)
