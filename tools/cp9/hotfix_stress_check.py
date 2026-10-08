"""H8 actual-entry weather/trajectory campaign; isolated profiles, real timers.

Modes remain distinct: identical current-response replay; settled samples;
continuous native timeScale playback. No claimed live weather in fixtures.
Use startup_video_check for genuinely cache-warm first-paint measurements.
"""
import argparse, hashlib, http.server, json, math, os, shutil, sys, threading, time, traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity

ROOT=Path(__file__).resolve().parents[2]
EDT=timezone(timedelta(hours=-4))
FAMILIES={
 'clear':(0,0,0,20000), 'partial':(2,50,0,20000), 'overcast':(3,100,0,12000),
 'fog':(45,100,0,500), 'haze':(2,35,0,4500), 'drizzle':(51,85,.2,9000),
 'light-rain':(61,85,.2,9000), 'rain':(63,90,2,7000), 'heavy-rain':(65,100,5,5000),
 'showers':(81,80,1,9000), 'snow':(73,95,1,6000), 'thunder':(95,100,3,6000),
 'contradictory-rain':(63,90,0,9000), 'partial-rain':(63,90,None,9000)}
MONITOR=r'''(()=>{
 const W=Worker;window.__h8={events:[],raf:0,gaps:[],longTasks:[],last:performance.now(),start:performance.now()};
 try{new PerformanceObserver(list=>{for(const e of list.getEntries())__h8.longTasks.push({at:e.startTime,ms:e.duration,name:e.name,attribution:e.attribution?.map(a=>({name:a.name,containerType:a.containerType,containerSrc:a.containerSrc}))});}).observe({type:'longtask',buffered:true});}catch{} // Firefox does not expose this optional metric.
 window.Worker=class extends W{constructor(u,o){super(u,o);let moon=false;const submitted=new Map(),post=this.postMessage.bind(this);
  this.postMessage=(m,t)=>{if(m.kind==='boot'){moon='offline' in m;if(moon)window.__h8MoonWorker=this;}if(m.kind==='render'||m.kind==='cancel'){const at=performance.now();if(m.kind==='render')submitted.set(m.id,at);__h8.events.push({direction:'submit',moon,at,kind:m.kind,id:m.id,utc:m.job?.observer?.utcMs,identity:m.job?.native?.identity??m.identity,phase:m.scene?.fraction,reason:m.reason??null});}return t?post(m,t):post(m);};
  this.addEventListener('message',e=>{const m=e.data,r=m.result??m,at=performance.now();if(moon&&m.kind==='result')window.__h8MoonSolved=m;if(['result','preview','error','cancelled','fatal','boot-error'].includes(m.kind))__h8.events.push({direction:'receive',moon,at,elapsed:submitted.has(m.id)?at-submitted.get(m.id):null,kind:m.kind,id:m.id,utc:r.utcMs,identity:r.native??m.identity,status:r.status,quality:r.diagnostics?.quality,acceptedNativeUtc:window.SalahNativeSkyHost?.capture()?.utcMs,error:m.error??null});if(m.kind==='result'||m.kind==='error')submitted.delete(m.id);});
 }};function tick(t){__h8.raf++;if(t-__h8.last>80)__h8.gaps.push({at:t,ms:t-__h8.last});__h8.last=t;requestAnimationFrame(tick);}requestAnimationFrame(tick);
})();'''
PAIRED_LUNAR_PROBE=r'''()=>{
 // Diagnostic pixels occupy only the unused iframe gutter (card is325px,
 // iframe330px). They copy the CURRENT underlying atmosphere/cloud sample at
 // the final document rAF, so its browser readback shares the screenshot's
 // presented frame. A prior evaluate() is not atomic with a later screenshot
 // during600x cloud motion. No widget pixel, clock or worker is changed.
 const probe=document.createElement('canvas');probe.width=3;probe.height=48;
 probe.style='position:fixed;left:326px;top:100px;width:3px;height:48px;pointer-events:none;z-index:2147483647';document.body.append(probe);const cx=probe.getContext('2d');window.__h8.presentedFrames=[];
 const fill=(at,v)=>{cx.fillStyle='rgb('+v.map(Math.round).join(',')+')';cx.fillRect(0,at,3,3);};
 function tick(){try{
  const card=document.querySelector('.c'),photo=document.querySelector('.mphoto'),shown=document.querySelector(card.classList.contains('real-sky-composed')?'.real-sky-canvas':'.real-sky-preview');
  const mr=photo.getBoundingClientRect(),cr=card.getBoundingClientRect(),br=shown.getBoundingClientRect(),leftLit=window.SalahMoonHost?.capture()?.waxing===false;
  const x=mr.x-cr.x+mr.width*(leftLit?.67:.33),y=mr.y-cr.y+mr.height*.57,px=Math.floor((x+cr.x-br.x)*shown.width/br.width),py=Math.floor((y+cr.y-br.y)*shown.height/br.height);
  if(px>2&&py>2&&px<shown.width-3&&py<shown.height-3){
   const a=shown.getContext('2d').getImageData(px-2,py-2,5,5).data,rgb=[0,0,0];for(let i=0;i<a.length;i+=4)for(let k=0;k<3;k++)rgb[k]+=a[i+k]/25;
   fill(0,rgb);fill(4,[Math.round(x)%256,Math.round(y)%256,Math.floor(Math.round(x)/256)+2*Math.floor(Math.round(y)/256)]);fill(8,[37,193,83]);
  }
  // This runs at the final document rAF after the canvas publishers. Pair age
  // to the PRESENTED framebuffer; the later qaState/DOM read can itself consume
  // >10 accepted seconds at600x. Keep that asynchronous sample separately.
  const refined=card.classList.contains('real-sky-composed'),preview=card.classList.contains('real-sky-preview-ready'),ps=refined?null:SalahSkyPreview.state,utc=simNow(),frameUtc=refined?realSkyState().displayed?.utcMs:ps.utcMs,age=Math.round(Math.abs(utc-frameUtc));
  const owner=refined?'refined':preview?'preview':'unavailable';
  fill(16,[age%256,Math.floor(age/256)%256,Math.floor(age/65536)%256]);fill(20,[37,193,83]);fill(24,[refined?55:preview?211:69,0,0]);
  const stamp=Math.round(utc),hi=Math.floor(stamp/16777216),at=Math.round(performance.now());
  fill(32,[stamp%256,Math.floor(stamp/256)%256,Math.floor(stamp/65536)%256]);fill(36,[hi%256,Math.floor(hi/256)%256,Math.floor(hi/65536)%256]);fill(40,[at%256,Math.floor(at/256)%256,Math.floor(at/65536)%256]);
  window.__h8.presentedFrames.push({at:performance.now(),utc,frameUtc,age,owner,reason:ps?.reason??null,publication:ps?.publication??null});
 }catch{}requestAnimationFrame(tick);}tick();
}'''
SNAP=r'''()=>{
 const c=document.querySelector('.c'),h=window.SalahNativeSkyHost?.capture(),s=window.realSkyState?.(),p=window.SalahSkyPreview?.state,q=window.qaState?.(),m=window.SalahMoonRuntime?.state,M=typeof model==='function'?model():null;
 const geom=e=>{if(!e)return null;const r=e.getBoundingClientRect(),b=c.getBoundingClientRect();return {x:r.x-b.x,y:r.y-b.y,w:r.width,h:r.height};};
 const st=e=>e?{display:getComputedStyle(e).display,visibility:getComputedStyle(e).visibility,opacity:+getComputedStyle(e).opacity}:null;
 const cv=document.querySelector('.real-sky-canvas'),pv=document.querySelector('.real-sky-preview'),shown=c.classList.contains('real-sky-composed')?cv:pv;
 let patches=[];try{const cx=shown?.getContext('2d');for(const [x,y] of [[280,205],[162,270],[55,290],[280,55]]){const a=cx.getImageData(x,y,12,12).data,v=[0,0,0];for(let i=0;i<a.length;i+=4)for(let k=0;k<3;k++)v[k]+=a[i+k]/144;patches.push({x,y,rgb:v});}}catch{}
 const rows=[...document.querySelectorAll('.times .p')].map(e=>({key:e.querySelector('b')?.textContent,cls:e.className,time:e.querySelector('.tm')?.textContent}));
 const rain=[...document.querySelectorAll('.drop,.flake')].map(e=>st(e));
 const sel=typeof selectedWeather==='function'?selectedWeather():null;
 let lunarAir=null;const photo=document.querySelector('.mphoto'),mr=photo?.getBoundingClientRect(),cr=c.getBoundingClientRect();
 if(mr&&shown&&mr.width>0){const leftLit=window.SalahMoonHost?.capture()?.waxing===false,x=mr.x-cr.x+mr.width*(leftLit ? .67 : .33),y=mr.y-cr.y+mr.height*.57;
  const br=shown.getBoundingClientRect(),px=Math.floor((x+cr.x-br.x)*shown.width/br.width),py=Math.floor((y+cr.y-br.y)*shown.height/br.height);
  if(px>2&&py>2&&px<shown.width-3&&py<shown.height-3){const a=shown.getContext('2d').getImageData(px-2,py-2,5,5).data,v=[0,0,0];for(let i=0;i<a.length;i+=4)for(let k=0;k<3;k++)v[k]+=a[i+k]/25;lunarAir={x,y,baseRGB:v,maskOpacity:+getComputedStyle(document.querySelector('.moon')).opacity};}}
 return {wall:Date.now(),at:performance.now(),utc:h?.utcMs??(typeof simNow==='function'?simNow():Date.now()),host:h,model:M&&{now:M.nowEpoch,current:M.currentKey,next:M.nextKey,nextEpoch:M.nextEpoch,nextTime:M.nextTime,progress:M.progress,date:M.dateStr},render:q?.render,
  weather:{selected:sel,eligibility:typeof weatherEligibility==='function'?weatherEligibility(weather):null,truth:q?.wxTruth,header:q?.weatherHeader,raw:typeof weather!=='undefined'?weather:null},
  header:{icon:document.querySelector('#wi')?.textContent,temp:document.querySelector('#wt')?.textContent,label:document.querySelector('#wi')?.title},fx:c.dataset.fx,precip:c.dataset.precip,lightning:c.dataset.lightning,rainOpacity:c.style.getPropertyValue('--rain-op'),visibleParticles:rain.filter(x=>x.display!=='none'&&x.visibility==='visible'&&x.opacity>.03).length,
  rows,countdown:document.querySelector('.left')?.textContent,nextMarkers:[...document.querySelectorAll('.dot.next')].map(e=>e.dataset.prayerKey),bar:document.querySelector('.bar>i')?.style.width,
  sky:s&&{status:s.status,renders:s.renders,rejections:s.rejections,displayed:s.displayed,age:s.displayed&&h?h.utcMs-s.displayed.utcMs:null,physical:s.last?.physicalState,composition:s.last?.composition,exposure:s.last?.exposure,availability:s.availability,lifecycle:s.lifecycle},
  preview:p,displayedOwner:c.classList.contains('real-sky-composed')?'refined':c.classList.contains('real-sky-preview-ready')?'preview':'unavailable',visible:{base:st(cv),preview:st(pv)},patches,lunarAir,cloudLighting:q?.clouds?.lighting,
  moonPresentation:{host:window.SalahMoonHost?.capture(),presentationUp:window.SalahMoonRuntime?.presentationUp,geometry:typeof moonSky!=='undefined'?moonSky:null,group:st(document.querySelector('.moon')),features:st(document.querySelector('.mfeatures')),photo:st(document.querySelector('.mphoto')),photoRect:geom(document.querySelector('.mphoto')),occluder:st(document.querySelector('.moccluder')),mask:st(document.querySelector('.moon-mask-disc')),detail:window.SalahMoonDetail?.state,solarParts:Object.fromEntries(['.suncorner','.suncorner .disc','.suncorner .corona','.sunbody','.sunbody .disc'].map(x=>[x,{...st(document.querySelector(x)),rect:geom(document.querySelector(x))}]))},moon:m&&{status:m.status,quality:m.quality,legacyFallback:m.legacyFallback,visibleSource:m.visibleSource,calendarProxyWeight:m.calendarProxyWeight,phasePrecision:m.phasePrecision,epoch:m.epoch,generation:m.generation,phase:m.currentNativeFraction,cancelled:m.cancelled,accepted:m.accepted?.identity,profile:m.accepted?.profile,scene:m.accepted?.scene,errors:m.errors},telemetry:window.__h8&&{raf:__h8.raf,events:__h8.events.length,gaps:__h8.gaps.length,document:__h8.documentCadence&&{frames:__h8.documentCadence.frames,start:__h8.documentCadence.start,last:__h8.documentCadence.last,gaps:__h8.documentCadence.gaps.length,nativeRenders:__h8.documentCadence.nativeRenders,cloudPaints:__h8.documentCadence.cloudPaints}},
  sun:{presentation:Object.fromEntries(["--sundisc","--sunamt","--sunbodyamt","--sunlow","--sunflat","--sunpulse"].map(k=>[k,getComputedStyle(c).getPropertyValue(k)])),x:c.style.getPropertyValue('--sunx2'),y:c.style.getPropertyValue('--sunlift'),vx:c.style.getPropertyValue('--sunvx'),vy:c.style.getPropertyValue('--sunvy'),nucleus:geom(document.querySelector('.suncorner')),nativeAltitude:q?.sunEl,physical:window.__h8Solar&&h?__h8Solar(h):null},card:geom(c),footer:geom(document.querySelector('.d')),memory:performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize}:null};}'''

def iso(ms,zone=EDT): return datetime.fromtimestamp(ms/1000,zone).strftime('%Y-%m-%dT%H:%M')
def sha(data):return hashlib.sha256(data).hexdigest()

def surface_replay_script(path):
 """Presentation-only reuse: exact numerical scene, fresh runtime envelope.

 Never an availability/worker-timing result. The saved result was computed by
 the unchanged terrain kernel; all admission/currentness checks still execute.
 """
 packed=json.loads(path.read_text(encoding='utf-8'))
 return r'''(()=>{const packed='''+json.dumps(packed,separators=(',',':'))+r''';
 const solved={...packed.metadata};for(const[k,v]of Object.entries(packed.arrays)){const s=atob(v.data),u=Uint8Array.from(s,c=>c.charCodeAt(0));solved[k]=new window[v.type](u.buffer);}
 const fields=['size','outSize','diameter','basis','sun','earth','distance','extent','profile','mode','fraction','waxing','tilt'];const physicalKey=s=>JSON.stringify(fields.map(k=>s[k]));const W=Worker,key=physicalKey(solved.scene);window.__surfaceReplay={matched:0,rejected:0,sourceIdentity:solved.physicalIdentity};
 window.Worker=class extends W{constructor(u,o){super(u,o);const post=this.postMessage.bind(this);this.postMessage=(m,t)=>{if(m.kind==='render'&&m.scene){if(physicalKey(m.scene)===key){__surfaceReplay.matched++;setTimeout(()=>this.dispatchEvent(new MessageEvent('message',{data:{...solved,scene:m.scene,id:m.id,identity:m.identity}})),0);return;}__surfaceReplay.rejected++;}return t?post(m,t):post(m);};}};
})();'''
def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def vertical_streak(diff):
 # Six contiguous changed pixels in a column distinguishes a rain stroke from
 # isolated rounding noise. Used below native cloud support, with CSS paused.
 longest=0
 for x in range(diff.width):
  run=0
  for y in range(diff.height):
   run=run+1 if max(diff.getpixel((x,y)))>3 else 0;longest=max(longest,run)
 return longest

def payload(stamp,family='rain',night=False,track=False,track_family=None):
 code,cloud,amount,vis=FAMILIES[family]
 fields={'temperature_2m':-2 if family=='snow' else 24,'apparent_temperature':24,'relative_humidity_2m':80,'dew_point_2m':20,'wind_speed_10m':3,'wind_direction_10m':225,'wind_gusts_10m':5,'cloud_cover':cloud,'cloud_cover_low':cloud,'cloud_cover_mid':0,'cloud_cover_high':0,'weather_code':code,'precipitation':amount,'rain':amount if family not in ['snow','partial-rain'] else None,'showers':0 if amount is not None else None,'snowfall':1 if family=='snow' else 0,'visibility':vis,'is_day':int(not night)}
 # Keep representative thermodynamic fields internally consistent too. These
 # are declared fixtures, never substituted for an owner's historical payload.
 if family=='snow':fields.update(apparent_temperature=-5,dew_point_2m=-5,relative_humidity_2m=80,rain=0)
 if family=='fog':fields.update(dew_point_2m=23.7,relative_humidity_2m=98)
 if family=='haze':fields.update(dew_point_2m=14.4,relative_humidity_2m=55)
 if family=='showers':fields.update(rain=0,showers=amount)
 units={'time':'iso8601','interval':'seconds','temperature_2m':'°C','apparent_temperature':'°C','relative_humidity_2m':'%','dew_point_2m':'°C','wind_speed_10m':'m/s','wind_direction_10m':'°','wind_gusts_10m':'m/s','cloud_cover':'%','cloud_cover_low':'%','cloud_cover_mid':'%','cloud_cover_high':'%','weather_code':'wmo code','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm','visibility':'m','is_day':''}
 # Provider interval endpoint and receipt UTC are separate. Quarter-hour source
 # timestamps evolve only when another response is requested, never per frame.
 current={'time':iso(stamp//900000*900000),'interval':900,**fields}
 result={'latitude':28.5383,'longitude':-81.3792,'timezone':'America/New_York','utc_offset_seconds':-14400,'elevation':25,'current':current,'current_units':units}
 if track:
  start=stamp//3600000*3600000-86400000;times=[start+i*3600000 for i in range(97)];sequence=['clear','partial','overcast','rain','partial','clear','drizzle','heavy-rain','clear','fog','clear','snow','thunder','clear']
  hourly={k:[] for k in fields};hourly['time']=[iso(t) for t in times]
  for i,t in enumerate(times):
   f=payload(t,track_family or sequence[(i//2)%len(sequence)],not 7<=datetime.fromtimestamp(t/1000,EDT).hour<19)['current']
   for k in fields:hourly[k].append(f[k])
  result.update(hourly=hourly,hourly_units=units)
 return result

class Entry:
 def __init__(self,browser,root,out,fonts,*,v1=False,rate=None,start='2026-10-07T15:09:00Z',family='rain',direct=False,dpr=1,offset=0,live=False,seed=1,steady=False,overrides='',observer=None,prayer_fixture=None,provider_route=None):
  self.root,self.out,self.family,self.live=root,out,family,live;out.mkdir(parents=True,exist_ok=True)
  self.anchor=datetime.fromisoformat(start.replace('Z','+00:00')).timestamp()*1000;self.started=time.monotonic();self.errors=[];self.requests=[];self.responses=[];self.failures=[];self.provider_failures=[];self.mode='healthy';self.frozen_response=None
  self.suffix=('v1/' if v1 else '')+'#local=1&motion=full&seed='+str(seed)+('' if rate is None else '&timeScale='+str(rate))+('&'+overrides if overrides else '')
  wrapper='<!doctype html><meta charset="utf-8"><body style="margin:8px;background:#1a2335"><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="/salah_widget/'+self.suffix+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden;position:relative;left:'+str(offset)+'px" scrolling="no"></iframe>'
  class Handler(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
   def translate_path(handler,p):return str(root/urlsplit(p).path.removeprefix('/salah_widget/'))
   def do_GET(handler):
    if handler.path=='/iframe':
     data=wrapper.encode();handler.send_response(200);handler.send_header('Content-Type','text/html');handler.send_header('Content-Length',str(len(data)));handler.end_headers();handler.wfile.write(data)
    elif handler.path=='/favicon.ico':handler.send_response(204);handler.end_headers()
    else:super().do_GET()
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start();self.origin=f'http://127.0.0.1:{self.server.server_port}'
  site=observer or {'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'Central Florida fixture'}
  self.context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=dpr,timezone_id=site['tz'],locale='en-US',reduced_motion='no-preference')
  self.context.add_init_script(MONITOR)
  sys.path.insert(0,str(ROOT/'tests'));from v1_browser import SETTINGS,ROOT_KEY,V1_KEY,FONT_CSS,fixture
  settings={**SETTINGS,'method':'2',**site,'units':'c','seed':seed}
  self.context.add_init_script('if(location.protocol==="http:")localStorage.setItem('+json.dumps(V1_KEY if v1 else ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
  if not live:self.context.add_init_script('(()=>{const D=Date,base='+str(self.anchor)+',start=D.now();window.Date=class extends D{constructor(...a){super(...(a.length?a:[base+D.now()-start]));}static now(){return base+D.now()-start;}};})();')
  def route(r):
   u=r.request.url;host=urlsplit(u).hostname;self.requests.append({'atWall':time.monotonic()-self.started,'url':u})
   if u.startswith(self.origin):r.continue_()
   elif u in fonts:r.fulfill(body=fonts[u].read_bytes(),content_type='text/css' if u==FONT_CSS else 'font/woff2',headers={'Access-Control-Allow-Origin':'*'})
   # Optional target/date-bound geography fixtures bypass the deliberately
   # fixed Florida timetable below. The callback must consume or reject each
   # provider request; it cannot silently fall through to relabelled timings.
   elif provider_route is not None and host in ['api.open-meteo.com','api.aladhan.com']:provider_route(r,self)
   elif live and host in ['api.open-meteo.com','api.aladhan.com']:r.continue_()
   elif host=='api.open-meteo.com':
    if self.mode=='failure':
     self.provider_failures.append({'atWall':time.monotonic()-self.started,'request':u,'status':503})
     r.fulfill(status=503,body='controlled temporary provider failure');return
    stamp=self.anchor+(time.monotonic()-self.started)*1000
    p=self.frozen_response or payload(stamp,self.family,not 7<=datetime.fromtimestamp(stamp/1000,EDT).hour<19,track=rate is not None,track_family=self.family if steady else None)
    if self.mode=='missing':p={**p,'current':None}
    data=json.dumps(p,separators=(',',':'));self.responses.append({'receivedWall':time.monotonic()-self.started,'request':u,'sha256':sha(data.encode()),'payload':p});r.fulfill(body=data,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
   elif host=='api.aladhan.com':
    p=json.loads(prayer_fixture.read_text(encoding='utf-8')) if prayer_fixture else fixture(u,False)
    date=urlsplit(u).path.rstrip('/').split('/')[-1];d,m,y=date.split('-');p['data']['date']['gregorian'].update(date=date,day=d,month={'number':int(m)},year=y);p['data']['meta'].update(timezone=site['tz'],latitude=site['lat'],longitude=site['lon'])
    if not prayer_fixture:p['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
    r.fulfill(json=p)
   elif host=='api.rainviewer.com':r.fulfill(json={'radar':{'past':[]}})
   else:r.abort()
  self.context.route('**/*',route)
  self.page=self.context.new_page();self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.on('response',lambda r:self.failures.append([r.url,r.status]) if r.url.startswith(self.origin) and r.status>=400 else None)
  self.page.goto(self.origin+('/salah_widget/'+self.suffix if direct else '/iframe'),wait_until='domcontentloaded');self.frame=self.page.main_frame if direct else self.page.frames[1];self.element=self.frame.locator('.c') if direct else self.page.locator('iframe')
  assert self.frame.evaluate('!!window.__h8'),'Worker/cadence instrumentation did not execute; do not start an uninstrumented campaign'
  try:self.frame.wait_for_function("window.qaState?.().cache.prayerLoaded",polling=100,timeout=45000)
  except Exception:
   dump(out/'entry-failure.json',{'frames':[f.url for f in self.page.frames],'errors':self.errors,'requests':self.requests,'responses':self.responses,'state':self.frame.evaluate('()=>({qa:window.qaState?.(),body:document.body?.innerText,ready:document.readyState})')})
   self.page.screenshot(path=out/'entry-failure.png');self.close();raise
  # Install only AFTER the iframe has navigated and the native script is ready.
  # Parent DOMContentLoaded may precede the iframe navigation in Firefox.
  # The init-script realm's rAF may stop after that navigation.
  # Measure cadence in the actual document realm, with an explicit start time;
  # retain early worker events. Startup first paint has its separate video gate.
  self.frame.add_script_tag(content='''(()=>{window.__h8.documentCadence={start:performance.now(),last:performance.now(),frames:0,gaps:[],nativeRenders:0,cloudPaints:0};
   const originalRender=render,originalCloud=paintClouds;
   render=function(...args){window.__h8.documentCadence.nativeRenders++;return originalRender(...args);};
   paintClouds=function(...args){window.__h8.documentCadence.cloudPaints++;return originalCloud(...args);};
   function tick(t){const c=window.__h8.documentCadence;c.frames++;if(t-c.last>80)c.gaps.push({at:t,ms:t-c.last});c.last=t;requestAnimationFrame(tick);}requestAnimationFrame(tick);
  })();''')
  if not v1:self.frame.evaluate("async()=>{const {physicalSkyState}=await import('/salah_widget/real-sky/core/src/sky-state.mjs'),{projectPerspective}=await import('/salah_widget/real-sky/core/src/projection.mjs');window.__h8Solar=h=>{const s=physicalSkyState({utcMs:h.utcMs,latDeg:h.lat,lonDeg:h.lon,heightM:h.heightM}).sun;return {...s,projection:projectPerspective(s,{width:325,height:530,...h.camera})};};}")
  self.paired_lunar=not v1 and not direct
  if self.paired_lunar:self.frame.evaluate(PAIRED_LUNAR_PROBE)
 def snap(self,name=None):
  s=self.frame.evaluate(SNAP)
  if name:
   target=self.out/(name+'.png');self.element.screenshot(path=target)
   if self.paired_lunar:
    paired=Image.open(target).convert('RGB');dpr=self.context.pages[0].evaluate('devicePixelRatio')
    marker=lambda at:paired.getpixel((round(327.5*dpr),round((101.5+at)*dpr)))
    if all(abs(a-b)<=1 for a,b in zip(marker(20),[37,193,83])):
     number=lambda at:sum(v*(256**k) for k,v in enumerate(marker(at)))
     kind=marker(24)[0];s['presentedFrame']={'ageMs':number(16),'utcMs':number(32)+16777216*number(36),'atMs':number(40),'owner':{55:'refined',211:'preview',69:'unavailable'}.get(kind,'invalid'),'scope':'same compositor capture; diagnostic bytes in unused iframe gutter'}
    else:raise AssertionError('Presented-frame age marker was not captured; no unpaired age PASS')
   air=s.get('lunarAir')
   if air:
    im=Image.open(target).convert('RGB');dpr=self.context.pages[0].evaluate('devicePixelRatio');x=round(air['x']*dpr);y=round(air['y']*dpr)
    if self.paired_lunar:
     def marker(at):return im.getpixel((round(327.5*dpr),round((101.5+at)*dpr)))
     if all(abs(a-b)<=1 for a,b in zip(marker(8),[37,193,83])):
      v=marker(4);x=round((v[0]+256*(v[2]%2))*dpr);y=round((v[1]+256*(v[2]//2))*dpr)
      air.update(evaluatedBaseRGB=air['baseRGB'],baseRGB=marker(0),pairedPresentedFrame=True)
    if 3<x<im.width-3 and 3<y<im.height-3:
     v=ImageStat.Stat(im.crop((x-2,y-2,x+3,y+3))).mean;lum=lambda a:sum(w*v for w,v in zip([.2126,.7152,.0722],a));air.update(browserRGB=v,browserMinusBaseLuma=lum(v)-lum(air['baseRGB']))
  return s
 def ready(self):self.frame.wait_for_function("window.realSkyState?.().status==='ready'",polling=100,timeout=90000)
 def close(self):
  dump(self.out/'entry-errors.json',{'pageErrors':self.errors,'failedLocalRequests':self.failures})
  self.context.close();self.server.shutdown()
  if self.errors or self.failures:raise RuntimeError('Unexpected page/local-asset errors: '+json.dumps([self.errors,self.failures]))

def displayed_sky_currentness(s):
 # A screenshot's paired marker is authoritative for its displayed owner.
 # The earlier DOM snapshot may describe a refined frame already replaced by
 # a current preview before that screenshot. Never qualify hidden metadata as
 # visible pixels; never exempt the owner actually captured from the age fence.
 presented=s.get('presentedFrame')
 if presented:
  owner=presented.get('owner');age=presented.get('ageMs')
  current=isinstance(age,(int,float)) and math.isfinite(age) and 0<=age<=30000
  return {'noStaleSky':owner!='refined' or current,
          'previewCurrent':owner!='preview' or current,
          'presentedOwnerKnown':owner in ['refined','preview','unavailable']}
 owner=s.get('displayedOwner')
 sky=s.get('sky') or {};preview=s.get('preview') or {}
 return {'noStaleSky':owner!='refined' or sky.get('age') is not None and abs(sky['age'])<=30000,
         'previewCurrent':owner!='preview' or preview.get('utcMs') is not None and abs(s['utc']-preview['utcMs'])<=30000}

def semantic(s):
 m=s.get('model');rows=s['rows'];on=[r['key'] for r in rows if 'on' in r['cls'].split()];now=[r['key'] for r in rows if 'now' in r['cls'].split()]
 # qa.render is the snapshot actually consumed by the DOM painter. Calling
 # model() later can cross an event during accelerated playback; retain both
 # timestamps, but do not manufacture mixed ownership from that sampling gap.
 painted=s.get('render');m={'current':painted['currentKey'],'next':painted['nextKey']} if painted else m
 pv=s.get('visible',{}).get('preview') or {};preview_visible=pv.get('display')!='none' and pv.get('visibility')=='visible'
 alt=(s.get('preview') or {}).get('solarAltitudeDeg') if preview_visible else ((s.get('sky') or {}).get('physical') or {}).get('sun',{}).get('altDeg');weather=s['weather'].get('selected');rgb=s['patches'][0]['rgb'] if s['patches'] else [0,0,0]
 day=alt is not None and alt>10;ordinary=weather and (weather.get('vis') or 0)>=15000 and (weather.get('cloud') or 0)<=60
 air=s.get('lunarAir') or {};baseY=sum(w*v for w,v in zip([.2126,.7152,.0722],air.get('baseRGB',[0,0,0])))
 # At twilight, opaque geometry may remove stars, but cannot remove the
 # intervening air. Sixteen display codes allow temporal capture/resampling
 # and the edge of the native top scrim. The old black cutout loses 79..123
 # codes in the retained dawn control. This is a regional pixel gate, not a
 # claim of measured atmospheric radiance or a whole-frame average.
 test_air=alt is not None and -14<alt<-3 and baseY>50 and air.get('maskOpacity',0)>.15 and 'browserMinusBaseLuma' in air
 return {'sixRows':len(rows)==6,'nextAgreement':not m or on==[m['next']] and m['next'] in s['countdown'] and s['nextMarkers']==[m['next']], 'currentAgreement':not m or now==([] if m['current']=='Forenoon' else [m['current']]),**displayed_sky_currentness(s),'daylightIdentity':not day or rgb[2]>=100 and (not ordinary or rgb[2]-rgb[0]>=10),'lunarForegroundAir':not test_air or air['browserMinusBaseLuma']>=-16,'geometry':s['card']['w']==325 and s['card']['h']==530,'noInventedLightning':s.get('lightning')!='on'}

def replay(a,browser,fonts):
 rows=[]
 for version,root,v1 in [('A-frozen-V1',a.root,True),('B-deployed-c1',a.deployed,False),('C-PR42',a.root,False)]:
  for family in ['rain','clear']:
   out=a.out/(version+'-'+family);e=Entry(browser,root,out,fonts,v1=v1,family=family)
   try:
    if not v1:e.ready()
    e.page.wait_for_timeout(3000);s=e.snap('widget');s['response']=e.responses;s['requests']=e.requests;s['errors']=e.errors
    # Pixel contribution control: pause CSS at its current time and remove only
    # particles. It is a diagnostic ablation, never a product fix.
    e.frame.add_style_tag(content='*{animation-play-state:paused!important;transition:none!important}')
    e.element.screenshot(path=out/'particles.png');style=e.frame.add_style_tag(content='.drop,.flake{visibility:hidden!important}');e.element.screenshot(path=out/'without-particles.png');style.evaluate('(e)=>e.remove()')
    x=Image.open(out/'particles.png').convert('RGB');y=Image.open(out/'without-particles.png').convert('RGB');diff=ImageChops.difference(x,y);lower=diff.crop((5,220,325,480));s['particlePixelDifference']={'nonzero':sum(1 for p in diff.getdata() if max(p)>3),'belowCloudSupport':sum(1 for p in lower.getdata() if max(p)>3),'max':max(v[1] for v in diff.getextrema()),'note':'Particle-only CSS ablation. Lower ROI y220..480 excludes cloud/Moon support; all CSS animation paused before BOTH captures. Frame identity retained separately; live cloud motion can contribute to the whole-frame count.'};diff.save(out/'particle-difference.png')
    s['particlePixelDifference']['longestVerticalStroke']=vertical_streak(lower)
    s['identity']={'index':sha((root/('v1/index.html' if v1 else 'index.html')).read_bytes()),'v1':v1};dump(out/'result.json',s);rows.append({'version':version,'family':family,'fx':s['fx'],'icon':s['header']['icon'],'particles':s['visibleParticles'],'particlePixels':s['particlePixelDifference']['belowCloudSupport'],'verticalStroke':s['particlePixelDifference']['longestVerticalStroke'],'snapshot':str(out/'result.json')})
   finally:e.close()
 expected=all(r['fx']==('rain' if r['family']=='rain' else 'clear') and (r['family']!='rain' or r['particles']>0 and r['verticalStroke']>=6) for r in rows if r['version']!='B-deployed-c1')
 control=any(r['family']=='rain' and r['fx']!='rain' and r['particles']==0 for r in rows if r['version']=='B-deployed-c1')
 return {'status':'PASS' if expected and control else 'FAIL','cases':rows,'oldFailsReplay':control,'historicalIncident':'Original owner provider payload/site/cache were not captured in the available incident screenshots. This is an explicitly substituted Orlando fixture, not a reconstruction or dispute of reported rain.'}

def playback_publication_failures(report):
 # Screenshot sampling can miss a brief withdrawal. The final-document rAF
 # observations are an additional gate, never a replacement for actual PNGs.
 p=report.get('presentedAge',{});failures=[]
 if not isinstance(p.get('samples'),int) or p['samples']<=0:failures.append({'check':'continuous presentation observations missing'})
 for key in ['expiredFrames','unavailableFrames']:
  if p.get(key)!=0:failures.append({'check':key,'observed':p.get(key)})
 age=p.get('maximumCurrentAgeMs')
 if not isinstance(age,(int,float)) or not math.isfinite(age) or age>30000:failures.append({'check':'current frame age bound','observed':age})
 return failures

def playback(a,browser,fonts):
 # The original 26h Central Florida window (05:00 -> next 07:00) ended
 # BEFORE the following sunrise. Retain those runs as partial-cycle evidence;
 # the full-cycle campaign runs at least 27h, without pausing or lowering rate.
 duration_hours=max(27,a.hours) if a.hours>=24 else a.hours
 e=Entry(browser,a.root,a.out,fonts,rate=a.rate,start=a.start,family=a.family,direct=a.direct,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=a.steady,overrides=a.overrides);rows=[];begin=time.monotonic();nextshot=begin;end=begin+duration_hours*3600/a.rate
 try:
  initial=e.snap('initial');report={'status':'RUNNING','clockMode':'actual continuous native timeScale; real rAF/workers/deadlines/Date receipts, no pause or awaited frame','requestedRate':a.rate,'requestedHours':a.hours,'campaignHours':duration_hours,'captureCadenceSeconds':a.cadence,'initial':initial}
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as file:
   while time.monotonic()<end:
    if time.monotonic()<nextshot:e.page.wait_for_timeout(max(1,(nextshot-time.monotonic())*1000))
    before=time.monotonic();s=e.snap(f'frame-{len(rows):05}');after=time.monotonic();s.update(wallElapsed=after-begin,captureMs=(after-before)*1000,checks=semantic(s))
    # An honest unavailable label cannot qualify a known-site dark shell.
    # Keep the historical full-tier throughput status separate from this
    # ordinary presentation requirement, including during accelerated motion.
    s['checks']['coherentCurrentSky']=s.get('presentedFrame',{}).get('owner',s['displayedOwner']) in ['preview','refined']
    rows.append(s);file.write(json.dumps(s)+'\n');file.flush();nextshot+=a.cadence
    if len(rows)%20==0:print('PLAY',a.rate,round(s['wallElapsed'],1),'s',len(rows),'frames',s.get('sky',{}).get('status'),flush=True)
   telemetry=e.frame.evaluate('__h8');dump(a.out/'worker-and-cadence.json',telemetry)
   cadence=telemetry.get('documentCadence',{})
   presented=telemetry.get('presentedFrames',[])
   report['presentedAge']={'samples':len(presented),'maximumCurrentAgeMs':max((r['age'] for r in presented if r['owner']!='unavailable'),default=None),'expiredFrames':sum(r['age']>30000 and r['owner']!='unavailable' for r in presented),'unavailableFrames':sum(r['owner']=='unavailable' for r in presented),'scope':'every final document rAF; separate screenshot-paired diagnostic also retained'}
   if not (cadence.get('frames',0)>10 and cadence.get('nativeRenders',0)>0 and cadence.get('cloudPaints',0)>0):
    raise RuntimeError('Native document cadence probe did not advance; exclude this run from playback qualification')
   report.update(status='MEASURED',wallSeconds=time.monotonic()-begin,simulatedSeconds=(rows[-1]['utc']-initial['utc'])/1000,frames=len(rows),maximumCaptureGap=max((b['wallElapsed']-a['wallElapsed'] for a,b in zip(rows,rows[1:])),default=0),failures=[{'frame':i,'checks':r['checks']} for i,r in enumerate(rows) if not all(r['checks'].values())],errors=e.errors,requests=e.requests,responses=e.responses)
   # Pair the same two accepted-UTC samples with their actual performance
   # timestamps. Screenshot startup/tail overhead belongs to capture coverage,
   # not an apparent reduction in the application's requested clock rate.
   report['clockSampleWallSeconds']=(rows[-1]['at']-initial['at'])/1000
   report['achievedRate']=report['simulatedSeconds']/report['clockSampleWallSeconds'];report['refinedFraction']=sum(r.get('displayedOwner')=='refined' for r in rows)/len(rows);report['previewFraction']=sum(r.get('displayedOwner')=='preview' for r in rows)/len(rows)
   return report
 finally:e.close()

def settled(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=0,start=a.start,family=a.family,direct=a.direct,dpr=a.dpr,offset=a.offset,seed=a.seed);rows=[]
 try:
  for minutes in range(0,round(a.hours*60)+1,a.step):
   target=e.anchor+minutes*60000
   e.frame.evaluate('t=>{_simBase=t;_rafT0=_RAFNOW();render();maintainPrayerDay();SalahRealSky?.request(true);}',target)
   e.frame.wait_for_function('t=>model()&&Math.abs(simNow()-t)<1',arg=target,timeout=30000);e.ready();e.page.wait_for_timeout(200)
   s=e.snap(f'settled-{minutes:04}');s.update(targetUtc=target,checks=semantic(s));rows.append(s)
   dump(a.out/'settled.json',rows);print('SETTLED',minutes,s['sky']['physical']['sun']['altDeg'],flush=True)
  return {'status':'MEASURED','clockMode':'awaited settled samples; NOT continuous playback','stepMinutes':a.step,'cases':len(rows),'failures':[{'i':i,'checks':r['checks']} for i,r in enumerate(rows) if not all(r['checks'].values())],'errors':e.errors,'responses':e.responses}
 finally:e.close()

def weather_sequence(a,browser,fonts):
 # One document, ordinary 1x and real current-provider admission. This fixture
 # omits the optional hourly track, so the native missing-track retry makes a
 # request about once a minute. We never change its cooldown or receipt clock.
 families=['clear','partial','overcast','rain','clear','drizzle','heavy-rain','clear','fog','clear','snow','thunder','clear']
 e=Entry(browser,a.root,a.out,fonts,start=a.start,family=families[0],direct=a.direct,dpr=a.dpr,offset=a.offset,seed=a.seed);rows=[];steps=[];begin=time.monotonic()
 try:
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as file:
   for family in families:
    previous=len(e.responses);e.family=family;deadline=time.monotonic()+100
    if not steps:previous-=1
    while True:
     before=time.monotonic();s=e.snap(f'frame-{len(rows):05}');s.update(wallElapsed=time.monotonic()-begin,captureMs=(time.monotonic()-before)*1000,checks=semantic(s),requestedFamily=family);rows.append(s);file.write(json.dumps(s)+'\n');file.flush()
     expected=FAMILIES[family][0]
     if len(e.responses)>previous and s['weather']['header'] and s['weather']['header']['rawCode']==expected:
      steps.append({'family':family,'frame':len(rows)-1,'wallElapsed':s['wallElapsed'],'response':len(e.responses)-1,'fx':s['fx'],'icon':s['header']['icon'],'particles':s['visibleParticles'],'observedPresent':s['weather']['truth']['observedPresent']});print('WEATHER',family,round(s['wallElapsed'],1),s['fx'],flush=True);break
     if time.monotonic()>deadline:raise TimeoutError('Native current-weather retry did not admit '+family)
     e.page.wait_for_timeout(max(1,1000-(time.monotonic()-before)*1000))
   e.page.wait_for_timeout(2000);s=e.snap('final');dump(a.out/'worker-and-cadence.json',e.frame.evaluate('__h8'))
   return {'status':'MEASURED','clockMode':'ordinary Date/rAF 1x; live current-weather lane; optional hourly fixture absent; native 60s retry unchanged','steps':steps,'wallSeconds':time.monotonic()-begin,'frames':len(rows),'final':s,'failures':[{'frame':i,'checks':r['checks']} for i,r in enumerate(rows) if not all(r['checks'].values())],'errors':e.errors,'requests':e.requests,'responses':e.responses}
 finally:e.close()

def controls(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,start=a.start,family='rain',dpr=a.dpr,offset=a.offset);rows=[];begin=time.monotonic();checks={}
 try:
  # Native setter changes the application clock. Worker timers and provider
  # source/receipt clocks continue at real 1x throughout this fault sequence.
  for name,control in [('10x',{'rate':10}),('60x',{'rate':60}),('pause',{'rate':0}),('600x',{'rate':600}),('forward',{'utcMs':e.anchor+86400000,'rate':10}),('backward',{'utcMs':e.anchor-86400000,'rate':10}),('live',{'live':True})]:
   e.frame.evaluate('x=>SalahClock.set(x)',control);e.page.wait_for_timeout(3000);s=e.snap(name);s['control']=name;rows.append(s);print('CONTROL',name,s['moon']['status'],flush=True)
  live=rows[-1];checks['liveClockRestored']=abs(live['utc']-live['wall'])<100 and live['host']['timeScale']==1
  checks['forecastNotLive']=live['weather']['selected'] is None or live['weather']['selected']['src']!='forecast'
  e.frame.evaluate('()=>{_enableSettingsAffordance();document.querySelector(".buckle").click();}')
  checks['settingsOpen']=e.frame.locator('.c').evaluate('(e)=>e.classList.contains("settings-open")');e.frame.locator('#setClose').click()
  end=time.monotonic()+300
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as file:
   while time.monotonic()<end:
    s=e.snap(f'frame-{len(rows):05}');s.update(wallElapsed=time.monotonic()-begin,checks=semantic(s));rows.append(s);file.write(json.dumps(s)+'\n');file.flush()
    if s['moon']['status']=='ready' and not s['moon']['legacyFallback'] and s['sky']['status']=='ready':break
    e.page.wait_for_timeout(1000)
  checks['refinementRecovered']=rows[-1]['moon']['status']=='ready' and not rows[-1]['moon']['legacyFallback']
  scene_checks=[r.get('checks',semantic(r)) for r in rows]
  checks['prayerAgreement']=all(all(c[k] for k in ['sixRows','nextAgreement','currentAgreement']) for c in scene_checks)
  checks['sceneAgreement']=all(all(c.values()) for c in scene_checks)
  dump(a.out/'states.json',rows);dump(a.out/'worker-and-cadence.json',e.frame.evaluate('__h8'))
  return {'status':'PASS' if all(checks.values()) and not e.errors else 'FAIL','checks':checks,'failures':[{'index':i,'control':rows[i].get('control'),'checks':c} for i,c in enumerate(scene_checks) if not all(c.values())],'recoveryWallSeconds':time.monotonic()-begin,'errors':e.errors,'requests':e.requests,'responses':e.responses}
 finally:e.close()

def availability(a,browser,fonts):
 # Start ten seconds before this valid quarter-hour source expires. Receipt,
 # expiry, failure/retry cooldown and worker elapsed time all remain real 1x.
 e=Entry(browser,a.root,a.out,fonts,start=a.start,family='rain',dpr=a.dpr,offset=a.offset);rows=[];begin=time.monotonic();e.mode='failure';failure_seen=None
 try:
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as file:
   while time.monotonic()-begin<240:
    elapsed=time.monotonic()-begin
    # The native 30s poll and 60s retry throttle can put the first request at
    # 90s. Restore only after the actual HTTP fault was consumed and captured;
    # an outage that ended at 80s never exercised transport recovery.
    if failure_seen is not None and elapsed-failure_seen>=5:e.mode='healthy'
    s=e.snap(f'frame-{len(rows):05}');s.update(wallElapsed=elapsed,checks=semantic(s));rows.append(s);file.write(json.dumps(s)+'\n');file.flush();e.page.wait_for_timeout(1000)
    if e.provider_failures and s['weather']['truth']['requests']['weather'].get('state')=='unavailable' and failure_seen is None:failure_seen=elapsed
    if failure_seen is not None and e.mode=='healthy' and s['fx']=='rain' and s['precip']=='on' and s['weather']['truth']['requests']['weather'].get('state')=='received':break
  wet=[r for r in rows if r['fx']=='rain' and r['precip']=='on'];unknown=[r for r in rows if r['fx']=='unavailable'];recovered=[r for r in wet if failure_seen is not None and r['wallElapsed']>failure_seen+5]
  checks={'initialWet':bool(wet and wet[0]['wallElapsed']<10),'expiredUnknown':bool(unknown),'coherentUnknown':all(r['header']['icon']=='—' and r['header']['temp']=='' and r['precip']=='off' for r in unknown),'recovery':bool(recovered),'noObservedClaim':all(not r['weather']['truth']['observedPresent'] for r in rows),'stateAgreement':all(all(r['checks'].values()) for r in rows),'providerFailureReached':any(r['weather']['truth']['requests']['weather'].get('state')=='unavailable' for r in rows if r['weather']['truth']['requests']['weather'])}
  dump(a.out/'worker-and-cadence.json',e.frame.evaluate('__h8'))
  checks['provider503Consumed']=bool(e.provider_failures and failure_seen is not None)
  return {'status':'PASS' if all(checks.values()) and not e.errors else 'FAIL','checks':checks,'wallSeconds':time.monotonic()-begin,'frames':len(rows),'firstUnavailable':unknown[0]['wallElapsed'] if unknown else None,'failureConsumedAt':failure_seen,'recoveryAt':recovered[0]['wallElapsed'] if recovered else None,'providerFailures':e.provider_failures,'requests':e.requests,'responses':e.responses,'errors':e.errors}
 finally:e.close()

def matrix(a,browser,fonts):
 rows=[]
 for family in ['clear','partial','overcast','fog','rain','drizzle','heavy-rain','showers','snow','thunder','haze','contradictory-rain','partial-rain']:
  e=Entry(browser,a.root,a.out/family,fonts,start='2026-10-07T15:09:00Z',family=family,rate=0,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=True)
  try:
   # Fixed admitted weather isolates solar evolution. These are awaited STILL
   # comparisons, not normal-clock/current-rain or continuous-playback proof.
   hours=[9.5,11.35,13,17.3,20,23,23.5,27] if family in ['clear','partial','overcast','fog','rain'] else [15,27]
   for hour in hours:
    target=datetime.fromisoformat('2026-10-07T00:00:00+00:00').timestamp()*1000+hour*3600000
    # Prayer readiness may precede optional sky-module initialization. Use
    # the supported clock boundary; it notifies an existing host and a later
    # host starts from that accepted target. Never dereference an absent host.
    e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',target);e.frame.wait_for_function('()=>!!window.model?.()',polling=100,timeout=30000);e.ready();e.page.wait_for_timeout(100)
    name=f'{hour:.2f}';s=e.snap(name);s.update(family=family,targetUtc=target,checks=semantic(s))
    s['checks']['requestedWeatherConsumed']=s['weather']['selected'] is not None and s['weather']['selected']['code']==FAMILIES[family][0] and s['weather']['selected']['cloud']==FAMILIES[family][1]
    s['checks']['declaredPreviewLane']=s['weather']['selected'] is not None and s['weather']['selected']['src']=='forecast' and s['weather']['truth']['lane']=='preview'
    rows.append(s);dump(a.out/'matrix.json',rows);print('MATRIX',family,hour,s['fx'],flush=True)
  finally:e.close()
 return {'status':'MEASURED','scope':'Awaited physical-sky stills with weather held fixed; NOT live weather chronology or continuous playback. Full Moon solves are qualified separately.','cases':len(rows),'failures':[{'case':i,'family':r['family'],'utc':r['utc'],'checks':r['checks']} for i,r in enumerate(rows) if not all(r['checks'].values())]}

def current_boundaries(a,browser,fonts):
 """Representative conditions through the ordinary current lane.

 Separate from matrix's explicit forecast-time preview. An absent or zero
 amount with a wet code retains the condition, but cannot manufacture particles.
 """
 rows=[]
 expected={
  'clear':('clear','☀️'), 'partial':('cloud','⛅'), 'overcast':('overcast','☁️'),
  'fog':('fog','🌫️'), 'haze':('cloud','⛅'), 'drizzle':('drizzle','🌦️'),
  'light-rain':('rain','🌧️'), 'rain':('rain','🌧️'), 'heavy-rain':('rain','🌧️'),
  'showers':('rain','🌦️'), 'snow':('snow','🌨️'), 'thunder':('thunder','⛈️'),
  'contradictory-rain':('rain','🌧️'), 'partial-rain':('rain','🌧️')}
 for family,(category,icon) in expected.items():
  e=Entry(browser,a.root,a.out/family,fonts,start='2026-10-07T15:09:00Z',family=family)
  try:
   code,cloud,amount,_=FAMILIES[family];effect=amount is not None and amount>0 and category in ['drizzle','rain','snow','thunder']
   e.ready();e.frame.wait_for_function("code=>window.qaState?.().weatherHeader?.rawCode===code",arg=code,timeout=30000)
   if effect:e.frame.wait_for_function("()=>[...document.querySelectorAll('.drop,.flake')].some(e=>{const s=getComputedStyle(e);return s.visibility==='visible'&&s.display!=='none'&&+s.opacity>.03;})",timeout=10000)
   s=e.snap('current-widget');truth=s['weather']['truth'];selected=s['weather']['selected'];checks=semantic(s)
   temp=-2 if family=='snow' else 24
   checks.update(currentLane=selected is not None and selected['src']=='current' and truth['lane']=='live',conditionRetained=s['fx']==category and s['weather']['header']['code']==code and s['header']['icon']==icon,temperatureCoherent=s['weather']['header']['temperature']==selected['temp']==temp and s['header']['temp']==str(temp)+'°',provenanceDisclosed='model estimate' in s['header']['label'],quantitativeEffect=(s['precip']=='on' and s['visibleParticles']>0) if effect else (s['precip']=='off' and s['visibleParticles']==0),noObservedClaim=truth['observedPresent'] is False,noFabricatedLightning=s['lightning']=='off')
   if family in ['contradictory-rain','partial-rain']:checks.update(uncertaintyDisclosed=bool(truth['visualPermissions']['quantitativeSupport']),noInventedEffect=not truth['visualPermissions']['rain'])
   rows.append({'family':family,'state':s,'checks':checks,'responses':e.responses});dump(a.out/'current-boundaries.json',rows)
  finally:e.close()
 return {'status':'PASS' if all(all(r['checks'].values()) for r in rows) else 'FAIL','scope':'Ordinary1x current-provider admission; no simWx, no forecast track, no application clock seek. WMO condition, temperature, disclosed model provenance and actual precipitation particles checked together. Contradictory and missing interval amounts do not fabricate rainfall. Not Moon refinement or continuous weather-motion evidence.','cases':len(rows),'failures':[{'family':r['family'],'checks':r['checks']} for r in rows if not all(r['checks'].values())]}


def cpu_pressure(a,browser,fonts):
 """Bounded Chromium CPU pressure after a fresh ordinary-clock terrain solve.

 The emulation affects only this isolated test browser. It is not a Firefox
 policy or a substitute for that engine's independently measured full solves.
 """
 if browser.browser_type.name!='chromium':raise ValueError('CDP CPU pressure requires Chromium; never substitute an engine')
 e=Entry(browser,a.root,a.out,fonts,start=a.start,family='partial');session=None;rows=[]
 try:
  e.ready();e.frame.wait_for_function("SalahMoonRuntime.state.status==='ready'&&SalahMoonDetail.state.visible",timeout=300000)
  initial=e.snap('initial-refined');session=e.context.new_cdp_session(e.page)
  session.send('Emulation.setCPUThrottlingRate',{'rate':2});begin=time.monotonic()
  e.frame.evaluate('()=>{_enableSettingsAffordance();document.querySelector(".buckle").click();}')
  settings=e.frame.locator('.c').evaluate('(e)=>e.classList.contains("settings-open")');e.frame.locator('#setClose').click()
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as f:
   while time.monotonic()-begin<35:
    at=time.monotonic();s=e.snap(f'frame-{len(rows):05}');s.update(wallElapsed=time.monotonic()-begin,checks=semantic(s));rows.append(s);f.write(json.dumps(s)+'\n');f.flush()
    e.page.wait_for_timeout(max(1,1000-(time.monotonic()-at)*1000))
  session.send('Emulation.setCPUThrottlingRate',{'rate':1});e.page.wait_for_timeout(1500);final=e.snap('recovered')
  telemetry=e.frame.evaluate('__h8');dump(a.out/'worker-and-cadence.json',telemetry)
  checks={'settingsUsable':settings,'ordinaryClock':final['host']['timeScale']==1,'clockAdvanced':final['utc']-initial['utc']>35000,'currentRefinedMoon':final['moon']['status']=='ready' and final['moon']['visibleSource']=='refined-terrain','sampledSemantics':all(all(r['checks'].values()) for r in rows)}
  return {'status':'PASS' if all(checks.values()) else 'FAIL','scope':'Isolated Chromium CDP2x CPU slowdown; ordinary1x application clock, fresh native terrain beforehand, current-provider fixture,35s real motion plus recovery. Not a thermal/OS-wide stress claim.','cpuRate':2,'frames':len(rows),'wallSeconds':time.monotonic()-begin,'checks':checks,'initial':initial,'final':final,'errors':e.errors}
 finally:
  if session:session.send('Emulation.setCPUThrottlingRate',{'rate':1})
  e.close()


def geometry_edges(a,browser,fonts):
 """Actual-entry stills supplement the independent 2900-direction sweep.

 Explicit clear simulation isolates geometry; not live-weather or Moon-quality
 evidence. Polar timetable fixtures retain adjusted events, never solar gates.
 """
 cases=[
  ('north-equinox',28.5383,-81.3792,'America/New_York','2026-03-20',[10,16,23],None),
  ('south-solstice',-33.8688,151.2093,'Australia/Sydney','2026-12-21',[1,8,11],None),
  ('equator-zenith',0,0,'UTC','2026-03-20',[11.9,12.1,12.3,18.1],None),
  ('arctic-summer',69.6492,18.9553,'Europe/Oslo','2026-06-21',[0,12,23],'summer'),
  ('arctic-winter',69.6492,18.9553,'Europe/Oslo','2026-12-21',[0,12,23],'winter'),
  ('antarctic-summer',-78.2232,15.6469,'UTC','2026-12-21',[0,12,23],None),
 ]
 rows=[]
 for name,lat,lon,zone,date,hours,polar in cases:
  observer={'lat':lat,'lon':lon,'tz':zone,'label':name+' fixture','method':'3' if polar else '2'}
  fixture=a.root/'tests'/('r0002-tromso-'+polar+'.json') if polar else None
  e=Entry(browser,a.root,a.out/name,fonts,start=date+'T00:00:00Z',rate=0,family='clear',observer=observer,prayer_fixture=fixture,overrides='simWx=0&simCloud=0&simPrecip=0')
  try:
   for hour in hours:
    target=e.anchor+hour*3600000;e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',target);e.ready();e.page.wait_for_timeout(500)
    s=e.snap(str(hour));sun=s['sun']['physical'];checks=semantic(s)
    checks['acceptedGeometry']=s['host']['lat']==lat and s['host']['lon']==lon and abs(s['utc']-target)<1
    checks['finiteSolarDirection']=all(math.isfinite(sun[k]) for k in ['altDeg','azDeg'])
    styles=e.frame.evaluate("()=>{const s=getComputedStyle(document.querySelector('.c'));return {body:+s.getPropertyValue('--sunbodyamt'),corner:+s.getPropertyValue('--sunamt')};}")
    checks['noBodyBelowHorizon']=sun['altDeg']>-1.5 or max(styles.values())==0
    if name in ['arctic-summer','antarctic-summer']:checks['polarDay']=sun['altDeg']>0
    if name=='arctic-winter':checks['polarNight']=sun['altDeg']<0
    rows.append({'case':name,'hour':hour,'state':s,'solarStyle':styles,'checks':checks});dump(a.out/'geometry.json',rows)
  finally:e.close()
 return {'status':'PASS' if all(all(r['checks'].values()) for r in rows) else 'FAIL','cases':len(rows),'failures':[{'case':r['case'],'hour':r['hour'],'checks':r['checks']} for r in rows if not all(r['checks'].values())],'scope':'Actual Pages-shaped iframe; explicit fixed clear weather, paused critical-time stills. Not live weather, continuous playback or lunar refinement. Captured polar timetable values remain adjusted prayer events, not asserted sunrises.'}

def boundaries(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,start='2026-10-07T15:09:00Z',family=a.family,dpr=a.dpr,offset=a.offset);rows=[]
 try:
  # Exact second-level DOM and pixel probes, with the native clock explicitly
  # paused. Separate from continuous playback; no claimed worker throughput.
  for name,at in [('Fajr','06:21'),('Sunrise','07:26'),('Forenoon','07:46'),('Dhuhr','13:17'),('Asr','16:38'),('Maghrib','19:08'),('Isha','20:13'),('midnight','00:00')]:
   day='2026-10-08' if name=='midnight' else '2026-10-07';t=datetime.fromisoformat(day+'T'+at+':00-04:00').timestamp()*1000
   for delta in [-1,0,1]:
    e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',t+delta*1000);e.frame.wait_for_function('!!model()',polling=100,timeout=30000);e.page.wait_for_timeout(300)
    s=e.snap(name+str(delta));s.update(event=name,secondOffset=delta,checks=semantic(s));rows.append(s);dump(a.out/'boundaries.json',rows)
  return {'status':'PASS' if all(all(r['checks'].values()) for r in rows) and not e.errors else 'FAIL','cases':len(rows),'errors':e.errors,'failures':[{'event':r['event'],'offset':r['secondOffset'],'checks':r['checks']} for r in rows if not all(r['checks'].values())]}
 finally:e.close()

def live_provider(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,live=True,family='clear',dpr=a.dpr,offset=a.offset);rows=[]
 try:
  e.ready()
  for i in range(16):
   s=e.snap(f'live-{i:02}');s['checks']=semantic(s);rows.append(s);e.page.wait_for_timeout(1000)
  dump(a.out/'live.json',rows)
  return {'status':'MEASURED','scope':'Current live providers at explicitly substituted Orlando fixture; not the historical owner incident or exact owner site. No weather response interception.','final':rows[-1],'errors':e.errors,'requests':e.requests,'failures':[{'frame':i,'checks':r['checks']} for i,r in enumerate(rows) if not all(r['checks'].values())]}
 finally:e.close()

PROFILE=r'''async()=>{
 const {renderNativeBackgroundPreview,nativeSkyPresentation}=await import('/salah_widget/real-sky/native-preview.mjs'),
 {nativeJob}=await import('/salah_widget/real-sky/native-contract.mjs'),
 {createSkyModel}=await import('/salah_widget/real-sky/core/src/sky-background.mjs'),
 {skyProjection}=await import('/salah_widget/real-sky/core/src/physical-sky-renderer.mjs'),
 {encodeNativeFrame}=await import('/salah_widget/real-sky/native-encoding.mjs'),
 {NativeForegroundCapture}=await import('/salah_widget/real-sky/native-composition.mjs');
 const h=SalahNativeSkyHost.capture(),r=realSkyFrame().raster,job=nativeJob(h,true),cv=document.querySelector('.real-sky-canvas'),capture=new NativeForegroundCapture(cv).capture(),cx=cv.getContext('2d');
 const image=(linear,w,ht,E)=>{const c=document.createElement('canvas');c.width=w;c.height=ht;c.getContext('2d').putImageData(new ImageData(encodeNativeFrame(linear,E),w,ht),0,0);return c.toDataURL();};
 const cases=[['refined',r,job.options.view],...[[60,45,90],[1,45,90],[60,55,90],[60,45,70]].map(([rate,altDeg,fovYDeg])=>{const p=renderNativeBackgroundPreview({...h,timeScale:rate,camera:{...h.camera,altDeg,fovYDeg}});return ['preview-'+rate+'-camera-'+altDeg+'-'+fovYDeg,p.raster,p.job.options.view];})];
 const results=cases.map(([name,f,view])=>{
  const camera={...view,width:f.width,height:f.height},projection=skyProjection(camera),sky=createSkyModel(f.physicalState,f.atmosphere??job.options.atmosphere,{residualNight:job.options.diffuse.residualNight}),single=createSkyModel(f.physicalState,{...(f.atmosphere??job.options.atmosphere),twilightScale:0},{residualNight:job.options.diffuse.residualNight}),source=f.physicalSkyBackgroundLinear??f.skyBackgroundLinear,rawCodes=encodeNativeFrame(source,f.effectiveExposure),mapped=encodeNativeFrame(f.skyBackgroundLinear,f.effectiveExposure),samples=[];
  for(const x of [35,162,285])for(const y of [100,180,240,280,318,355,389,423,457,491,512,520,528]){
   const px=Math.min(f.width-1,Math.floor(x*f.width/325)),py=Math.min(f.height-1,Math.floor(y*f.height/530)),i=py*f.width+px,direction=projection.unproject((x+.5)*f.width/325,(y+.5)*f.height/530),atmosphere=sky.sample(direction),ci=4*(y*325+x);
   const ss=single.sample(direction),neutral=atmosphere.moonLuminance+atmosphere.naturalLuminance+atmosphere.localLuminance;
   samples.push({x,y,direction,atmosphere,components:{solarRGB:atmosphere.rgb.map(v=>v-neutral),singleScatteredRGB:ss.rgb.map(v=>v-neutral),empiricalTwilightRGB:atmosphere.rgb.map((v,k)=>v-ss.rgb[k]),physicalMoonLuminance:atmosphere.moonLuminance,naturalResidualLuminance:atmosphere.naturalLuminance,artificialLocalLuminance:atmosphere.localLuminance},rawFlux:Array.from(source.subarray(3*i,3*i+3)),rawDisplay:Array.from(rawCodes.subarray(4*i,4*i+4)),mappedDisplay:Array.from(mapped.subarray(4*i,4*i+4)),cloudRGBA:Array.from(capture.cloudRGBA.subarray(ci,ci+4)),finalCanvas:Array.from(cx.getImageData(x,y,1,1).data)});
  }
  return {name,view:camera,normalizedAtmosphere:sky.atmosphere,display:f.displayPresentation,samples,rawImage:image(source,f.width,f.height,f.effectiveExposure),mappedImage:image(f.skyBackgroundLinear,f.width,f.height,f.effectiveExposure)};
 });
 const card=document.querySelector('.c').getBoundingClientRect(),rect=e=>{const t=e.getBoundingClientRect();return{x:t.x-card.x,y:t.y-card.y,w:t.width,h:t.height};};
 const layers=[...document.querySelector('.c').children,...document.querySelectorAll('.times .p')].map(e=>{const s=getComputedStyle(e);return{tag:e.tagName,cls:e.className,rect:rect(e),display:s.display,visibility:s.visibility,opacity:s.opacity,background:s.background,filter:s.filter,backdropFilter:s.backdropFilter,mixBlendMode:s.mixBlendMode,zIndex:s.zIndex};});
 return {host:h,physical:r.physicalState,results,layers};
}'''

def profile(a,browser,fonts):
 import base64
 e=Entry(browser,a.root,a.out,fonts,rate=0,start=a.start,family=a.family,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=True)
 try:
  # Freeze the supported native clock for an explicitly labelled layer
  # diagnostic. This is not continuous playback or a throughput measurement.
  e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',e.anchor);e.ready();e.page.wait_for_timeout(250)
  state=e.snap('widget');values=e.frame.evaluate(PROFILE)
  for item in values['results']:
   for kind in ['rawImage','mappedImage']:
    data=item.pop(kind);(a.out/(item['name']+'-'+kind+'.png')).write_bytes(base64.b64decode(data.split(',')[1]))
  # Isolate actual CSS contributions. No changes are made to product files.
  style=e.frame.add_style_tag(content='.c>*:not(.real-sky-canvas){visibility:hidden!important}.c .real-sky-canvas{visibility:visible!important}')
  e.element.screenshot(path=a.out/'canvas-only-browser.png');style.evaluate('(e)=>e.remove()')
  style=e.frame.add_style_tag(content='.times .p{background:transparent!important;backdrop-filter:none!important;box-shadow:none!important}')
  e.element.screenshot(path=a.out/'without-row-glass.png');style.evaluate('(e)=>e.remove()')
  pixels=Image.open(a.out/'widget.png').convert('RGBA');isolated=Image.open(a.out/'canvas-only-browser.png').convert('RGBA')
  for item in values['results']:
   for s in item['samples']:
    # Canvas is inside the one-CSS-pixel card border. Fractional/DPR positions
    # are retained in the case metadata; these probes use their device pixels.
    xy=(round((s['x']+1)*a.dpr),round((s['y']+1)*a.dpr));s['browserRGBA']=pixels.getpixel(xy);s['isolatedBrowserRGBA']=isolated.getpixel(xy)
  dump(a.out/'profiles.json',values);dump(a.out/'state.json',state)
  return {'status':'MEASURED','scope':'Frozen native-clock directional/layer diagnostic; not playback. Product camera remains unchanged. Alternate cameras exist only in detached diagnostic renders.','errors':e.errors,'checks':semantic(state),'identity':values['host']}
 finally:e.close()

AMBER_JOIN=r'''async()=>{
 const {nativeSkyPresentation}=await import('/salah_widget/real-sky/native-preview.mjs'),
 {nativeJob}=await import('/salah_widget/real-sky/native-contract.mjs'),
 {NativeForegroundCapture,nativeCalendarRegion,nativeForeground}=await import('/salah_widget/real-sky/native-composition.mjs'),
 {encodeNativeFrame}=await import('/salah_widget/real-sky/native-encoding.mjs');
 const frame=realSkyFrame(),r=frame.raster,h=SalahNativeSkyHost.capture(),j=nativeJob(h,true),surface=window.__amberAdopted;
 if(SalahMoonRuntime.state.status!=='ready'||SalahMoonRuntime.state.legacyFallback||!SalahMoonDetail.state.visible)throw Error('Current V5 terrain required');
 if(!(surface?.linear instanceof Float32Array)||surface.identity!==SalahMoonRuntime.state.accepted.identity)throw Error('Accepted V5 arrays were not observed; no material proof');
 const digest=async a=>a?Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer.slice(a.byteOffset,a.byteOffset+a.byteLength)))).map(x=>x.toString(16).padStart(2,'0')).join(''):null;
 const material={identity:surface.identity,size:surface.size,linear:await digest(surface.linear),calendarLinear:await digest(surface.calendarLinear),coverage:await digest(surface.coverage)};
 const binary=a=>{const u=new Uint8Array(a.buffer,a.byteOffset,a.byteLength);let t='';for(let i=0;i<u.length;i+=32768)t+=String.fromCharCode(...u.subarray(i,i+32768));return btoa(t);};
 const materialPayload={size:surface.size,extent:surface.extent,linear:binary(surface.linear),calendarLinear:binary(surface.calendarLinear),coverage:binary(surface.coverage)};
 const raw=r.physicalSkyBackgroundLinear,rawLinear=Float64Array.from(r.linear,(v,i)=>v-r.skyBackgroundLinear[i]+raw[i]);
 // Paired V32 counterfactual: omit ONLY the directional chroma reference.
 // The already present solar brightness shoulder stays active. Same radiance, exposure, colour policy, stars and terrain.
 // This is a declared pre-directional-chroma policy ablation, not historical runtime bytes.
 const before=nativeSkyPresentation({...r,linear:rawLinear,skyBackgroundLinear:raw,backgroundLinear:raw,twilightDisplay:{...r.twilightDisplay,referenceRGB:null}},j.options.view,h.solarAnchor);
 const base=document.querySelector('.real-sky-canvas'),capture=new NativeForegroundCapture(base).capture(),detail=document.querySelector('.moon-detail-canvas');
 const image=(linear)=>{const c=document.createElement('canvas');c.width=325;c.height=530;c.getContext('2d').putImageData(new ImageData(encodeNativeFrame(linear,r.effectiveExposure),325,530),0,0);return c.toDataURL();};
 const cases={};
 for(const [name,raster] of [['before',before],['after',r]]){
  const joined=nativeForeground(nativeCalendarRegion(raster),{...capture,atmosphereLinear:raster.skyBackgroundLinear,exposure:raster.effectiveExposure});
  SalahMoonDetail.compose({...frame,raster},encodeNativeFrame);
  cases[name]={atmosphere:image(raster.skyBackgroundLinear),base:image(joined.linear),detail:detail.toDataURL(),detailStyle:detail.getAttribute('style'),display:raster.displayPresentation};
 }
 SalahMoonDetail.compose(frame,encodeNativeFrame);
 const unchanged=material.linear===await digest(surface.linear)&&material.calendarLinear===await digest(surface.calendarLinear)&&material.coverage===await digest(surface.coverage);
 window.__amberPaired=cases;
 window.__amberShow=(name)=>{
  document.querySelectorAll('.amber-diagnostic,.amber-hide').forEach(e=>e.remove());
  if(!name)return;
  const style=document.createElement('style');style.className='amber-hide';style.textContent='.real-sky-canvas,.moon-detail-canvas{visibility:hidden!important}';document.head.append(style);
  const b=document.createElement('img');b.src=cases[name].base;b.className='amber-diagnostic';b.style='position:absolute;left:0;top:0;width:100%;height:100%;z-index:0;pointer-events:none';base.after(b);
  const d=document.createElement('img');d.src=cases[name].detail;d.className='amber-diagnostic';d.setAttribute('style',cases[name].detailStyle);b.after(d);
 };
 return {cases,material,materialPayload,unchanged,host:h,moon:SalahMoonRuntime.state,detail:SalahMoonDetail.state,composition:realSkyState().last.composition,physical:r.physicalState,scope:'Paired V32 display-policy ablation versus final runtime; same current fully refined V5 surface, raw sky, exposure policy, camera, weather and UTC. No material edits.'};
}'''

def amber_moon(a,browser,fonts):
 import base64
 e=Entry(browser,a.root,a.out,fonts,rate=0,start=a.start,family=a.family,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=True,overrides=a.overrides)
 try:
  e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',e.anchor);e.ready()
  e.frame.evaluate('()=>{const adopt=SalahMoonDetail.adopt;SalahMoonDetail.adopt=s=>{window.__amberAdopted=s;return adopt(s);};}')
  dump(a.out/'loading-state.json',e.snap('loading-diagnostic'))
  began=time.monotonic();states=[]
  while time.monotonic()-began<600:
   state=e.frame.evaluate('()=>({at:performance.now(),moon:SalahMoonRuntime.state,detail:SalahMoonDetail.state,sky:realSkyState().status})');states.append(state)
   if state['moon']['status']=='ready' and not state['moon']['legacyFallback'] and state['detail']['visible'] and state['sky']=='ready':break
   e.page.wait_for_timeout(1000)
  else:raise AssertionError('Current V5 terrain did not complete in600seconds')
  e.page.wait_for_timeout(250);current=e.snap('after-current-complete');require_weather(current,a.family)
  dump(a.out/'refined-state.json',current);dump(a.out/'refinement-timeline.json',states)
  pair=e.frame.evaluate(AMBER_JOIN)
  material=pair.pop('materialPayload')
  for key in ['linear','calendarLinear','coverage']:(a.out/('accepted-'+key+'.f32')).write_bytes(base64.b64decode(material.pop(key)))
  dump(a.out/'accepted-surface.json',{**material,**pair['material'],'scene':pair['moon']['accepted']['scene']})
  for name,case in pair['cases'].items():
   for kind in ['atmosphere','base','detail']:
    (a.out/(name+'-'+kind+'.png')).write_bytes(base64.b64decode(case.pop(kind).split(',')[1]))
   e.frame.evaluate('(name)=>__amberShow(name)',name);e.page.wait_for_timeout(50);e.element.screenshot(path=a.out/(name+'-paired-complete.png'))
  e.frame.evaluate('()=>__amberShow(null)');e.page.wait_for_timeout(100);dump(a.out/'final-state.json',e.snap('after-restored-complete'))
  # Poison only the legacy fallback store after a current refined result is
  # visible. Restore it unconditionally; this must not influence final pixels.
  e.frame.evaluate("()=>{const x=_moonCv.getContext('2d');window.__amberLegacy=x.getImageData(0,0,_moonCv.width,_moonCv.height);x.fillStyle='#ff00ff';x.fillRect(0,0,_moonCv.width,_moonCv.height);}")
  e.page.wait_for_timeout(150);e.element.screenshot(path=a.out/'legacy-poison-control.png')
  e.frame.evaluate("()=>_moonCv.getContext('2d').putImageData(__amberLegacy,0,0)")
  st=e.frame.add_style_tag(content='.moon-detail-canvas{visibility:hidden!important}');e.element.screenshot(path=a.out/'detail-hidden-control.png');st.evaluate('(e)=>e.remove()')
  rect=current['moonPresentation']['photoRect'];box=(round(rect['x']*a.dpr),round(rect['y']*a.dpr),round((rect['x']+rect['w'])*a.dpr),round((rect['y']+rect['h'])*a.dpr))
  ref=Image.open(a.out/'after-restored-complete.png').convert('RGB').crop(box)
  changed=lambda name:sum(max(p)>0 for p in ImageChops.difference(ref,Image.open(a.out/(name+'.png')).convert('RGB').crop(box)).getdata())
  layer_proof={'legacyPoisonChangedPixels':changed('legacy-poison-control'),'detailHiddenChangedPixels':changed('detail-hidden-control'),'cropDevicePixels':box}
  pair['layerProof']=layer_proof
  dump(a.out/'paired-receipt.json',pair)
  checks={'fullyRefinedV5':current['moon']['status']=='ready' and current['moon']['quality']=='empirical-adaptive' and not current['moon']['legacyFallback'],'detailVisible':current['moonPresentation']['detail']['visible'],'baseLegacyRemoved':pair['composition']['moonSurface']=='device-resolution-owned' and pair['composition']['moonPixels']==0,'materialUnchanged':pair['unchanged'],'sameExposure':pair['cases']['before']['display']['displayExposure']==pair['cases']['after']['display']['displayExposure']}
  checks['visiblePixelSource']=layer_proof['legacyPoisonChangedPixels']==0 and layer_proof['detailHiddenChangedPixels']>100
  return {'status':'PASS_SCOPED' if all(checks.values()) else 'FAIL','checks':checks,'waitSeconds':time.monotonic()-began,'current':current,'errors':e.errors,'responses':e.responses,'scope':pair['scope']}
 finally:e.close()

def twilight_joined(a,browser,fonts):
 """Fresh terrain, actual-camera comparisons, then exact-surface motion replay.

 The optional before source is a retained authored module, intercepted ONLY at
 a diagnostic URL. Its dependencies and physical inputs match the final runtime.
 No product file or safety timer changes. Motion reuse qualifies composition,
 not full terrain throughput; ordinary-clock availability is a separate mode.
 """
 import base64
 from PIL import ImageDraw
 e=Entry(browser,a.root,a.out,fonts,rate=0,start=a.start,family=a.family,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=True,overrides='simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42')
 rows=[];motion=[];started=time.monotonic()
 try:
  control=a.comparison_source.read_bytes()
  e.context.route(e.origin+'/salah_widget/real-sky/__h7_before.mjs',lambda r:r.fulfill(body=control,content_type='text/javascript'))
  e.frame.evaluate('t=>SalahClock.set({utcMs:t,rate:0})',e.anchor)
  e.frame.evaluate('()=>{const adopt=SalahMoonDetail.adopt;SalahMoonDetail.adopt=s=>{window.__amberAdopted=s;return adopt(s);};}')
  e.frame.wait_for_function("SalahMoonRuntime.state.status==='ready'&&SalahMoonRuntime.state.quality==='empirical-adaptive'&&SalahMoonDetail.state.visible&&realSkyState().status==='ready'",timeout=600000,polling=1000)
  refinement=time.monotonic()-started
  packed=e.frame.evaluate(r'''()=>{const arrays={},metadata={};for(const[k,v]of Object.entries(__h8MoonSolved)){if(ArrayBuffer.isView(v)){const u=new Uint8Array(v.buffer,v.byteOffset,v.byteLength);let t='';for(let i=0;i<u.length;i+=32768)t+=String.fromCharCode(...u.subarray(i,i+32768));arrays[k]={type:v.constructor.name,data:btoa(t)};}else metadata[k]=v;}return{metadata,arrays};}''')
  dump(a.out/'fresh-worker-result.json',packed)
  paired=AMBER_JOIN.replace('/real-sky/native-preview.mjs','/real-sky/__h7_before.mjs').replace('twilightDisplay:{...r.twilightDisplay,referenceRGB:null}','twilightDisplay:r.twilightDisplay')
  for az in [180,90,270,0]:
   e.frame.evaluate('az=>{q.set("skyAz",String(az));SalahRealSky.request(true);}',az)
   e.frame.wait_for_function('az=>realSkyState().status==="ready"&&realSkyState().last.view.azDeg===az&&SalahMoonDetail.state.visible',arg=az,timeout=90000)
   e.page.wait_for_timeout(150);name='az'+str(az);state=e.snap(name+'-current');require_weather(state,a.family)
   pair=e.frame.evaluate(paired);pair.pop('materialPayload')
   for version,c in pair['cases'].items():
    for kind in ['atmosphere','base','detail']:(a.out/(name+'-'+version+'-'+kind+'.png')).write_bytes(base64.b64decode(c.pop(kind).split(',')[1]))
    e.frame.evaluate('v=>__amberShow(v)',version);e.page.wait_for_timeout(50);e.element.screenshot(path=a.out/(name+'-'+version+'-complete.png'))
   e.frame.evaluate('()=>__amberShow(null)')
   pair['scope']='Retained pre-spatial-correction display versus current complete composition, same refined Moon/physical sky/weather/UTC/camera/exposure. Diagnostic overlays for the paired captures only.'
   dump(a.out/(name+'-pair.json'),pair);dump(a.out/(name+'-state.json'),state)
   rows.append({'heading':az,'sun':state['sun']['physical'],'checks':{**semantic(state),'refinedMoon':state['moon']['quality']=='empirical-adaptive' and state['moon']['visibleSource']=='refined-terrain' and state['moonPresentation']['detail']['visible'],'materialUnchanged':pair['unchanged'],'sameExposure':pair['cases']['before']['display']['displayExposure']==pair['cases']['after']['display']['displayExposure']}})
  sheet=Image.new('RGB',(4*330,4*558),(20,28,40));draw=ImageDraw.Draw(sheet)
  for y,kind in enumerate(['before-complete','after-complete','before-atmosphere','after-atmosphere']):
   for x,az in enumerate([180,90,270,0]):
    im=Image.open(a.out/('az'+str(az)+'-'+kind+'.png')).convert('RGB')
    # Sheet is a CSS-size overview; preserve original device-resolution files
    # for native/nearest inspection. Never crop high-DPR cards into 330px cells.
    if im.width>330:im=im.resize((330,round(im.height*330/im.width)),Image.Resampling.LANCZOS)
    sheet.paste(im,(x*330,y*558+24));draw.text((x*330+3,y*558+4),kind+' cam'+str(az),fill='white')
  sheet.save(a.out/'camera-comparison.png')
  # Source-bound reuse for presentation ONLY. Every numerical/profile/geometry
  # field must match byte-for-byte. Fresh request IDs/epochs still pass the real
  # admission fences. This is not availability evidence for accelerated solves.
  e.frame.evaluate(r'''()=>{const w=__h8MoonWorker,solved=__h8MoonSolved,send=w.postMessage.bind(w),key=JSON.stringify(solved.scene);window.__h7Reuse={count:0,scene:solved.scene,physicalIdentity:solved.physicalIdentity};w.postMessage=(m,t)=>{if(m.kind==='render'&&JSON.stringify(m.scene)===key){__h7Reuse.count++;setTimeout(()=>w.dispatchEvent(new MessageEvent('message',{data:{...solved,id:m.id,identity:m.identity}})),0);return;}return t?send(m,t):send(m);};}''')
  e.frame.evaluate('x=>{q.set("skyAz","180");SalahClock.set({utcMs:x,rate:60});}',e.anchor-50*60000)
  begin=time.monotonic();end=begin+a.hours*60;nextshot=begin
  with (a.out/'frames.jsonl').open('w',encoding='utf-8') as f:
   while time.monotonic()<end:
    if time.monotonic()<nextshot:e.page.wait_for_timeout(max(1,(nextshot-time.monotonic())*1000))
    s=e.snap('motion-'+str(len(motion)).zfill(5));s.update(wallElapsed=time.monotonic()-begin,checks=semantic(s));motion.append(s);f.write(json.dumps(s)+'\n');f.flush();nextshot+=a.cadence
    if len(motion)%30==0:print('TWILIGHT',len(motion),round(s['wallElapsed'],1),s['sun']['physical']['altDeg'],flush=True)
  dump(a.out/'motion-telemetry.json',e.frame.evaluate('({telemetry:__h8,reuse:__h7Reuse})'))
  return {'status':'MEASURED','refinementSeconds':refinement,'comparisonSourceSha256':sha(control),'cameras':rows,'frames':len(motion),'wallSeconds':time.monotonic()-begin,'failures':[r for r in rows if not all(r['checks'].values())]+[{'frame':i,'checks':s['checks']} for i,s in enumerate(motion) if not all(s['checks'].values())],'scope':'Fresh full terrain solve; paused actual-widget camera rotation/paired composition; then continuous60x application playback with an exact numerical scene replay of that same solve. Motion is composition evidence, not full-solver throughput. Sanitised fixture.'}
 finally:e.close()

def lunar_layers(a,browser,fonts):
 """Matched complete pixels and omissions; omissions are diagnostic only."""
 e=Entry(browser,a.root,a.out,fonts,rate=None if a.rate==1 else 0,start=a.start,family=a.family,dpr=a.dpr,offset=a.offset,seed=a.seed,steady=True,overrides=a.overrides or 'simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42')
 motion=[]
 try:
  if a.rate!=1:e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',e.anchor)
  e.frame.wait_for_function("SalahMoonRuntime.state.status==='ready'&&SalahMoonDetail.state.visible&&realSkyState().status==='ready'",timeout=600000,polling=1000)
  e.page.wait_for_timeout(1800);state=e.snap('complete');dump(a.out/'state.json',state)
  if not a.surface_replay:
   packed=e.frame.evaluate(r'''()=>{const arrays={},metadata={};for(const[k,v]of Object.entries(__h8MoonSolved)){if(ArrayBuffer.isView(v)){const u=new Uint8Array(v.buffer,v.byteOffset,v.byteLength);let t='';for(let i=0;i<u.length;i+=32768)t+=String.fromCharCode(...u.subarray(i,i+32768));arrays[k]={type:v.constructor.name,data:btoa(t)};}else metadata[k]=v;}return{metadata,arrays};}''')
   dump(a.out/'fresh-worker-result.json',packed)
  layers=e.frame.evaluate(r'''()=>{const c=document.querySelector('.c'),cs=getComputedStyle(c);return{runtime:SalahMoonRuntime.state,presentationUp:SalahMoonRuntime.presentationUp,physicalMoon:realSkyState().last.physicalState.moon,host:SalahMoonHost.capture(),domOrder:[...c.children].map(e=>({tag:e.tagName,cls:typeof e.className==='string'?e.className:null,z:getComputedStyle(e).zIndex})),optics:[...document.querySelectorAll('.mhalo,.mcorona,.mparhelia,.mglow,.mbeam')].map(e=>({cls:e.className.baseVal,opacity:getComputedStyle(e).opacity,visibility:getComputedStyle(e).visibility,fill:getComputedStyle(e).fill,filter:getComputedStyle(e).filter})),replay:window.__surfaceReplay??null};}''')
  layers['nativeOpticsBeforeTerrain']=e.frame.evaluate("!!(document.querySelector('.sky').compareDocumentPosition(document.querySelector('.moon-detail-canvas'))&Node.DOCUMENT_POSITION_FOLLOWING)")
  dump(a.out/'layers.json',layers)
  for name,css in [('without-corona','.mcorona{visibility:hidden!important}'),('without-all-native-lunar-optics','.mcorona,.mhalo,.mparhelia,.mglow,.mbeam{visibility:hidden!important}'),('detail-only','.sky{visibility:hidden!important}'),('atmosphere-only','.sky,.moon-detail-canvas{visibility:hidden!important}')]:
   style=e.frame.add_style_tag(content=css);e.page.wait_for_timeout(60);e.element.screenshot(path=a.out/(name+'.png'));style.evaluate('(e)=>e.remove()')
  # Test original semantic layer order: native optics were behind the opaque
  # SVG photo, but the new device canvas may be earlier than the whole SVG.
  e.frame.evaluate("()=>{window.__layerOldAfter=document.querySelector('.moon-detail-canvas').previousSibling;document.querySelector('.sky').after(document.querySelector('.moon-detail-canvas'));}")
  # Freeze only the diagnostic publisher during this single ordering ablation.
  e.frame.evaluate("()=>{window.__layerCompose=SalahMoonDetail.compose;SalahMoonDetail.compose=()=>{};document.querySelector('.sky').after(document.querySelector('.moon-detail-canvas'));}")
  e.page.wait_for_timeout(60);e.element.screenshot(path=a.out/'disc-after-native-optics.png')
  e.frame.evaluate("()=>{SalahMoonDetail.compose=__layerCompose;__layerOldAfter.after(document.querySelector('.moon-detail-canvas'));}")
  rect=state['moonPresentation']['photoRect'];box=tuple(round(v*a.dpr) for v in (rect['x'],rect['y'],rect['x']+rect['w'],rect['y']+rect['h']))
  # Include surrounding pixels to distinguish surface haze from atmospheric halo.
  box=(max(0,box[0]-8),max(0,box[1]-8),box[2]+8,box[3]+8)
  for name in ['complete','without-corona','without-all-native-lunar-optics','detail-only','atmosphere-only','disc-after-native-optics']:
   im=Image.open(a.out/(name+'.png'));im.crop(box).save(a.out/(name+'-moon.png'));im.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST).save(a.out/(name+'-moon-nearest.png'))
  if a.duration:
   if a.rate!=1:e.frame.evaluate('rate=>SalahClock.set({rate})',a.rate)
   begin=time.monotonic();nextshot=begin;motion=[]
   with (a.out/'frames.jsonl').open('w',encoding='utf-8') as f:
    while time.monotonic()-begin<a.duration:
     e.page.wait_for_timeout(max(1,(nextshot-time.monotonic())*1000));s=e.snap('motion-'+str(len(motion)).zfill(5));s.update(wallElapsed=time.monotonic()-begin,checks=semantic(s));motion.append(s);f.write(json.dumps(s)+'\n');f.flush();nextshot+=a.cadence
   dump(a.out/'motion-telemetry.json',e.frame.evaluate('__h8'))
  checks={**semantic(state),'nativeOpticsBeforeTerrain':layers['nativeOpticsBeforeTerrain'],'motionSemantics':all(all(s['checks'].values()) for s in motion)}
  return {'status':'MEASURED' if all(checks.values()) else 'FAIL','checks':checks,'motionFrames':len(motion),'requestedRate':a.rate,'durationSeconds':a.duration,'scope':'Identical accepted V5 surface and target; diagnostic removal/order captures, not proposed layer omissions. Any replay is presentation-only, never worker availability.','errors':e.errors,'responses':e.responses}
 finally:e.close()

def directional(a,browser,fonts):
 """Complete widget plus explicit layer ablations; physical target held fixed.

 Camera changes are diagnostic only. The product default remains180/45/90.
 No solar disc, glow, cloud, or lunar omission in an ablation is acceptance.
 """
 import base64
 rows=[]
 for stamp in ['2026-10-07T22:30:00Z','2026-10-07T23:15:00Z','2026-10-07T23:28:00Z']:
  for az in [90,180,270,0]:
   name=stamp[11:16].replace(':','')+'-az'+str(az);out=a.out/name
   e=Entry(browser,a.root,out,fonts,rate=0,start=stamp,family=a.family,dpr=a.dpr,offset=a.offset,steady=True,overrides='skyAz='+str(az)+'&simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42')
   try:
    # timeScale=0 alone does not select the explicit forecast-preview lane.
    # Use the supported clock setter; confirm the provider family was consumed.
    e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',e.anchor)
    e.ready();e.page.wait_for_timeout(250);state=e.snap('complete');require_weather(state,a.family);values=e.frame.evaluate(PROFILE)
    for item in values['results']:
     for kind in ['rawImage','mappedImage']:
      data=item.pop(kind);(out/(item['name']+'-'+kind+'.png')).write_bytes(base64.b64decode(data.split(',')[1]))
    style=e.frame.add_style_tag(content='.sunbody,.suncorner{visibility:hidden!important}')
    e.element.screenshot(path=out/'without-body-and-attached-glare.png');style.evaluate('(e)=>e.remove()')
    # Clear only the native cloud producer for this controlled diagnostic.
    # This is not hiding the final cloud canvas (it already has a single join).
    e.frame.evaluate('()=>{window.__savedPainter=paintClouds;paintClouds=()=>{const c=document.querySelector(".cloudcanvas");c.getContext("2d").clearRect(0,0,c.width,c.height);};paintClouds();SalahRealSky.compose();}')
    e.page.wait_for_timeout(150);e.element.screenshot(path=out/'without-clouds.png')
    style=e.frame.add_style_tag(content='.c>*:not(.real-sky-canvas){visibility:hidden!important}.c .real-sky-canvas{visibility:visible!important}')
    # The canvas still contains the lunar fallback/preview contribution. Raw
    # atmospheric-only buffers are the separately saved mappedImage files.
    e.element.screenshot(path=out/'canvas-without-ui-or-clouds.png');style.evaluate('(e)=>e.remove()')
    e.frame.evaluate('()=>{paintClouds=__savedPainter;paintClouds(performance.now());SalahRealSky.compose();}')
    dump(out/'layers.json',values);dump(out/'state.json',state);rows.append({'name':name,'cameraAz':az,'sun':state['sun']['physical'],'cloudLighting':state['cloudLighting'],'checks':semantic(state),'errors':e.errors})
   finally:e.close()
 dump(a.out/'cases.json',rows)
 for stamp in ['2230','2315','2328']:
  sheet=Image.new('RGB',(4*330,4*558),(20,28,40))
  from PIL import ImageDraw
  draw=ImageDraw.Draw(sheet)
  for y,kind in enumerate(['complete','without-body-and-attached-glare','without-clouds','canvas-without-ui-or-clouds']):
   for x,az in enumerate([90,180,270,0]):
    sheet.paste(Image.open(a.out/(stamp+'-az'+str(az))/(kind+'.png')).convert('RGB'),(330*x,558*y+24));draw.text((330*x+3,558*y+4),kind+' cam'+str(az),fill='white')
  sheet.save(a.out/(stamp+'-isolated.png'))
 return {'status':'MEASURED','cases':rows,'failures':[r for r in rows if not all(r['checks'].values())],'scope':'Complete actual widget first row; explicitly isolated diagnostic rows below. No new physical Sun/camera in product.'}

STAR_AUDIT=r'''async()=>{
 const {projectCatalogue}=await import('/salah_widget/real-sky/core/src/scene.mjs'),{projectPerspective}=await import('/salah_widget/real-sky/core/src/projection.mjs'),{nativeJob,nativeDiscMask}=await import('/salah_widget/real-sky/native-contract.mjs'),{NativeForegroundCapture,nativeCalendarRegion,nativeForeground}=await import('/salah_widget/real-sky/native-composition.mjs'),{encodeNativeFrame}=await import('/salah_widget/real-sky/native-encoding.mjs');
 const card=document.querySelector('.c'),preview=!card.classList.contains('real-sky-composed'),frame=preview?SalahSkyPreview.frame:realSkyFrame(),r=frame.raster,cv=document.querySelector(preview?'.real-sky-preview':'.real-sky-canvas'),h=SalahNativeSkyHost.capture(),j=nativeJob({...h,utcMs:r.physicalState.utcMs},true);
 if(r.width!==325||!r.stellarLinear?.some(x=>x>0))return {owner:preview?'preview':'refined',counts:{all:0,bright:0,unobscuredActual:0},reason:'no current catalogue contribution',sun:r.physicalState.sun,utc:r.physicalState.utcMs};
 const catalogue=window.__starAuditCatalogue??(window.__starAuditCatalogue=await(await fetch('/salah_widget/vendor/real-sky/data/bright-stars.json')).json());
 const sources=projectCatalogue(catalogue,j.observer,x=>projectPerspective(x,j.options.view)).filter(s=>s.visible&&s.emission?.enabled!==false),cap=new NativeForegroundCapture(cv).capture(),disc=document.querySelector('.moon-mask-disc'),matrix=disc?.getScreenCTM(),rect=cv.getBoundingClientRect();let mask=null;
 if(matrix&&disc.classList.contains('mask-on')&&+getComputedStyle(disc).opacity>0)mask=nativeDiscMask(325,530,rect,matrix,+disc.getAttribute('r'));
 const join=stellar=>encodeNativeFrame(nativeForeground(nativeCalendarRegion({...r,stellarLinear:stellar},mask),{...cap,atmosphereLinear:r.skyBackgroundLinear??r.backgroundLinear,exposure:r.effectiveExposure}).linear,r.effectiveExposure);
 const withStars=join(r.stellarLinear),without=join(new Float64Array(r.stellarLinear.length)),actual=cv.getContext('2d').getImageData(0,0,325,530).data,candidates=[];
 const mr=document.querySelector('.mphoto').getBoundingClientRect(),insideMoon=(x,y)=>x*rect.width/325+rect.left>=mr.left&&x*rect.width/325+rect.left<=mr.right&&y*rect.height/530+rect.top>=mr.top&&y*rect.height/530+rect.top<=mr.bottom;
 for(const s of sources){if(insideMoon(s.x,s.y))continue;let delta=0,actualDelta=0,alpha=0,error=0;
  for(let y=Math.max(0,Math.floor(s.y)-2);y<Math.min(530,Math.floor(s.y)+3);y++)for(let x=Math.max(0,Math.floor(s.x)-2);x<Math.min(325,Math.floor(s.x)+3);x++){const i=4*(y*325+x);alpha=Math.max(alpha,cap.cloudRGBA[i+3]/255);for(let k=0;k<3;k++){delta=Math.max(delta,withStars[i+k]-without[i+k]);actualDelta=Math.max(actualDelta,actual[i+k]-without[i+k]);error=Math.max(error,Math.abs(actual[i+k]-withStars[i+k]));}}
  candidates.push({id:s.id,name:s.properName??s.name,vmag:s.vmag,x:s.x,y:s.y,delta,actualDelta,cloudAlpha:alpha,compositorSamplingError:error});
 }
 return {owner:preview?'preview':'refined',utc:r.physicalState.utcMs,sun:r.physicalState.sun,physicalExposure:r.effectiveExposure,display:r.displayPresentation,previewTier:r.starPreview??null,counts:{all:candidates.filter(s=>s.delta>=2).length,bright:candidates.filter(s=>s.vmag<=4.5&&s.delta>=2).length,unobscuredActual:candidates.filter(s=>s.cloudAlpha===0&&s.actualDelta>=2&&s.compositorSamplingError<=1).length},candidates,scope:'Actual final canvas compared with a same-buffer star-only ablation; opaque Moon rectangle excluded; cloud-motion sampling error recorded. Visible browser pixels require the accompanying complete screenshot.'};
}'''

def require_weather(state,family):
 selected=state['weather']['selected'];code,cloud,amount,_=FAMILIES[family]
 if not selected or selected.get('code')!=code or selected.get('cloud')!=cloud or selected.get('precip')!=amount:
  raise AssertionError('Requested provider fixture not consumed: '+json.dumps({'family':family,'selected':selected,'eligibility':state['weather']['eligibility']}))
 return {'code':selected['code'],'cloud':selected['cloud'],'precip':selected['precip'],'source':selected['src'],'target':selected['target'],'label':state['header']['label']}

def evening_stars(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=0,start='2026-10-07T22:40:00Z',family=a.family,steady=True,overrides='simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42');rows=[]
 try:
  for i,stamp in enumerate(['2026-10-07T22:40:00Z','2026-10-07T23:05:00Z','2026-10-07T23:15:00Z','2026-10-07T23:25:00Z','2026-10-07T23:30:00Z','2026-10-07T23:40:00Z','2026-10-08T00:00:00Z','2026-10-08T00:20:00Z']):
   e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp()*1000);e.ready();e.page.wait_for_timeout(150)
   state=e.snap('star-'+str(i));consumed=require_weather(state,a.family);audit=e.frame.evaluate(STAR_AUDIT);rows.append({'state':state,'consumedWeather':consumed,'audit':audit,'checks':semantic(state)});dump(a.out/'star-timeline.json',rows)
  return {'status':'MEASURED','scope':'Settled exact-input star return and final-compositor ablation; not continuous playback or a fresh terrain qualification. Complete moving scenes are recorded separately.','family':a.family,'cases':len(rows),'counts':[{'sunAltitude':r['audit']['sun']['altDeg'],'counts':r['audit']['counts']} for r in rows],'failures':[r for r in rows if not all(r['checks'].values())],'errors':e.errors,'responses':e.responses}
 finally:e.close()

def star_preview_control(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=60,start='2026-10-08T00:00:00Z',family='clear',steady=True,overrides='simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42');rows=[]
 try:
  e.frame.wait_for_function("SalahSkyPreview.state.status==='ready'&&qaState().cache.prayerLoaded",polling=100,timeout=30000)
  for i in range(3):
   e.page.wait_for_timeout(1000);state=e.snap('preview-'+str(i));require_weather(state,'clear');audit=e.frame.evaluate(STAR_AUDIT);rows.append({'state':state,'audit':audit})
  checks={'currentCatalogueStarsVisible':all(r['audit']['owner']=='preview' and r['audit']['counts']['bright']>0 for r in rows),'currentPreview':all(r['state']['utc']-r['audit']['utc']<=30000 for r in rows)}
  dump(a.out/'preview-control.json',rows)
  return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'scope':'Discriminating actual-widget60x clear-night preview control. V19 has atmosphere only and must fail visible catalogue stars; no threshold/brightness changes or paused clock.','responses':e.responses,'errors':e.errors}
 finally:e.close()

def solar_size(a,browser,fonts):
 """Matched native elevations; size, coverage and glow are separate readings.

 Frozen samples are explicitly geometry/layer diagnostics, never motion proof.
 The full playback runs retain the actual transitions with CSS/clock running.
 """
 rows=[]
 versions=[('C-candidate',a.root,False)] if not a.deployed else [('A-V1',a.root,True),('B-control',a.deployed,False),('C-candidate',a.root,False)]
 for version,root,v1 in versions:
  out=a.out/version;e=Entry(browser,root,out,fonts,v1=v1,rate=0,start=a.start,family=a.family,dpr=a.dpr,offset=a.offset,steady=True)
  try:
   for descending in [False,True]:
    for elevation in [-2,-1.5,0,1,3,5.5,10,40]:
     # Both versions receive identical timetable/site/weather. Locate the
     # requested NATIVE presentation altitude without changing astronomy.
     minute=e.frame.evaluate('''({e,down})=>{const m=model();let l=down?m.noon:0,r=down?1440:m.noon;for(let i=0;i<40;i++){const x=(l+r)/2,v=solarElevationDeg(m,x);if((v<e)!==down)l=x;else r=x;}return (l+r)/2;}''',{'e':elevation,'down':descending})
     utc=e.anchor-e.anchor%86400000+4*3600000+minute*60000
     if v1:e.frame.evaluate('t=>{_simBase=t;_rafT0=_RAFNOW();render();}',utc)
     else:e.frame.evaluate('t=>SalahClock.set({utcMs:t,rate:0})',utc)
     e.page.wait_for_timeout(2600)
     name=('set' if descending else 'rise')+'-'+str(elevation);s=e.snap(name)
     s['solarStyle']=e.frame.evaluate('''()=>{const c=document.querySelector('.c'),s=getComputedStyle(c);return Object.fromEntries(['--sundisc','--sunamt','--sunbodyamt','--sunlow','--sunflat','--sunpulse','--sunlift','--sunx2','--suncore','--sunmid'].map(k=>[k,s.getPropertyValue(k)]));}''')
     style=e.frame.add_style_tag(content='.c{background:black!important;box-shadow:none!important}.c>*:not(.atmo):not(.wfx){visibility:hidden!important}.atmo>*:not(.suncorner):not(.sun-cloud-mask),.suncorner>*:not(.disc),.wfx>*:not(.sunbody):not(.sun-cloud-mask){visibility:hidden!important}')
     e.element.screenshot(path=out/(name+'-body-only.png'));style.evaluate('(e)=>e.remove()')
     im=Image.open(out/(name+'-body-only.png')).convert('RGB');pts=[(x,y) for y in range(2,im.height-4) for x in range(2,min(im.width-5,round(170*a.dpr))) if max(im.getpixel((x,y)))>128]
     # Ignore the card border; the high-code component is the nucleus/body,
     # while CSS geometry above records the full (partly clipped) diameter.
     pts=[(x,y) for x,y in pts if 8*a.dpr<y<520*a.dpr]
     extent=None if not pts else [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
     row={'version':version,'direction':'set' if descending else 'rise','targetAltitude':elevation,'minute':minute,'utc':utc,'style':s['solarStyle'],'bodyBrightExtent':extent,'physical':s['sun']['physical'],'parts':s['moonPresentation']['solarParts'],'shot':name+'.png'};rows.append(row)
   dump(out/'measurements.json',rows);dump(out/'requests.json',e.responses)
  finally:e.close()
 return {'status':'MEASURED','scope':'Matched native solar elevations; isolated body excludes corona/glow; requested fixture, not historical user site. Settled layer diagnostics, not continuous playback.','cases':rows}

def dawn_comparison(a,browser,fonts):
 """Complete, matched physical-elevation stills; no diagnostic layer omitted.

 The numerical solver has separate quadrature/reference tests. This compares
 product presentation, not a claim that a settled still proves moving quality.
 """
 from PIL import ImageDraw
 targets=[];rows=[]
 probe=Entry(browser,a.root,a.out/'geometry',fonts,rate=0,family=a.family,steady=True)
 try:
  targets=probe.frame.evaluate('''async()=>{
   const {physicalSkyState}=await import('/salah_widget/real-sky/core/src/sky-state.mjs');
   const observer={latDeg:28.5383,lonDeg:-81.3792,heightM:25,pressureHpa:0,temperatureC:24};
   const midnight=Date.parse('2026-10-07T00:00:00-04:00'),alt=m=>physicalSkyState({...observer,utcMs:midnight+m*60000}).sun.altDeg;
   let noon=0;for(let m=1;m<1440;m++)if(alt(m)>alt(noon))noon=m;
   return [false,true].flatMap(down=>[-8,-5,-2,0,1,3,5.5,10,40].map(e=>{
    let l=down?noon:0,r=down?1440:noon;for(let i=0;i<40;i++){const m=(l+r)/2;if((alt(m)<e)!==down)l=m;else r=m;}
    return {name:(down?'set':'rise')+'-'+e,elevation:e,utcMs:midnight+(l+r)*30000};
   }));
  }''')
 finally:probe.close()
 versions=[('revised',a.root,False)] if not a.deployed else [('V1',a.root,True),('before',a.deployed,False),('revised',a.root,False)]
 for label,root,v1 in versions:
  folder=a.out/label;e=Entry(browser,root,folder,fonts,rate=0,family=a.family,steady=True,v1=v1,dpr=a.dpr,offset=a.offset,overrides='simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42')
  try:
   for t in targets:
    e.frame.evaluate('t=>{_simBase=t;_rafT0=_RAFNOW();render();}' if v1 else 'utcMs=>SalahClock.set({utcMs,rate:0})',t['utcMs'])
    e.page.wait_for_timeout(3200);s=e.snap(t['name']);rows.append({'label':label,**t,'state':s,'runtime':runtime_identity(root)})
    dump(a.out/'measurements.json',rows);print('DAWN',label,t['name'],flush=True)
  finally:e.close()
 for direction in ['rise','set']:
  names=[t['name'] for t in targets if t['name'].startswith(direction)]
  sheet=Image.new('RGB',(330*len(names),558*len(versions)),'#1a2335');draw=ImageDraw.Draw(sheet)
  for j,(label,_,_) in enumerate(versions):
   for i,name in enumerate(names):
    im=Image.open(a.out/label/(name+'.png')).convert('RGB')
    if a.dpr!=1:im=im.resize((330,534),Image.Resampling.LANCZOS)
    sheet.paste(im,(330*i,558*j+24));draw.text((330*i+4,558*j+4),label+' COMPLETE '+name,fill='white')
  sheet.save(a.out/(direction+'-complete.png'))
 return {'status':'MEASURED','scope':'Same physical UTC/site/weather/camera/quarter Moon; all product layers retained. Quality recorded per screenshot; short seeks may still show lunar fallback. Separate normal-clock terrain acceptance and continuous replay are required.','targets':targets,'cases':len(rows)}

def preview_failure(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=600,start='2026-10-07T11:00:00Z',family='partial',steady=True)
 try:
  e.frame.wait_for_function("SalahSkyPreview?.state.status==='ready'",polling=25,timeout=30000)
  observations=e.frame.evaluate('''()=>{
   const saved=CanvasRenderingContext2D.prototype.getImageData,rows=[];
   for(const delay of [0,80]){
    SalahClock.set({rate:delay?600:1});
    SalahSkyPreview.update();let injected=false;
    CanvasRenderingContext2D.prototype.getImageData=function(...args){
     if(this.canvas.width===325&&this.canvas.height<530){injected=true;const until=performance.now()+delay;while(performance.now()<until){}throw Error('H8 controlled foreground readback failure');}
     return saved.apply(this,args);
    };
    try{SalahSkyPreview.update();const state=SalahSkyPreview.state,style=getComputedStyle(document.querySelector('.real-sky-preview'));
     rows.push({delayRealMs:delay,injected,state,visible:style.visibility==='visible'&&style.display!=='none',acceptedUtc:SalahNativeSkyHost.capture().utcMs});
    }finally{CanvasRenderingContext2D.prototype.getImageData=saved;}
   }
   SalahSkyPreview.update();const detail=SalahMoonDetail,compose=detail.compose;let injected=false;
   detail.compose=function(...args){const value=compose.apply(this,args);injected=true;const until=performance.now()+80;while(performance.now()<until){}return value;};
   try{SalahSkyPreview.update();const state=SalahSkyPreview.state,style=getComputedStyle(document.querySelector('.real-sky-preview'));rows.push({stage:'final-detail-join',delayRealMs:80,injected,state,visible:style.visibility==='visible'&&style.display!=='none',acceptedUtc:SalahNativeSkyHost.capture(false).utcMs});}
   finally{detail.compose=compose;}
   return rows;
  }''')
  e.page.wait_for_timeout(1000);recovered=e.snap('recovered');dump(a.out/'fault-observations.json',observations)
  checks={'injectedAtForeground':all(r['injected'] for r in observations),'currentFrameRetained':observations[0]['visible'] and observations[0]['state'].get('retained') is True,
   'expiredFrameWithdrawn':not observations[1]['visible'],'lateCompositionExpiredWithdrawn':not observations[2]['visible'],'previewRecovered':recovered['preview']['status']=='ready','currentness':all(semantic(recovered).values())}
  return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'observations':observations,'scope':'Actual preview receiving faults. Current retention at native1x;80ms real readback/final-join stalls at native600x exceed the unchanged30 accepted-second fence. The supported clock setter changes rates explicitly; no deadline is faked. Not a throughput measurement.'}
 finally:e.close()

def solar_cloud(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=0,start='2026-10-07T16:00:00Z',family='partial',dpr=a.dpr,offset=a.offset,steady=True)
 try:
  e.ready();e.frame.add_style_tag(content='*{animation-play-state:paused!important;transition:none!important}')
  # Explicit opaque-cloud fault/control through the REAL native painter
  # buffer and capture/composition. No provider observation is manufactured.
  e.frame.evaluate("()=>{window.__originalCloudPainter=paintClouds;paintClouds=()=>{const cv=document.querySelector('.cloudcanvas'),cx=cv.getContext('2d');cx.clearRect(0,0,cv.width,cv.height);cx.fillStyle='#788694';cx.fillRect(0,0,cv.width,cv.height);};paintClouds();SalahRealSky.compose();}")
  e.page.wait_for_timeout(500);s=e.snap('opaque-with-sun')
  sample=e.frame.evaluate("async()=>{const {NativeForegroundCapture}=await import('/salah_widget/real-sky/native-composition.mjs');const c=new NativeForegroundCapture(document.querySelector('.real-sky-canvas')).capture();return [...c.cloudRGBA.slice(4*(40*325+20),4*(40*325+20)+4)];}")
  e.frame.add_style_tag(content='.sunbody .disc,.suncorner .disc,.suncorner .corona,.suncorner .rays{visibility:hidden!important}')
  e.element.screenshot(path=a.out/'opaque-without-sun.png')
  x=Image.open(a.out/'opaque-with-sun.png').convert('RGB');y=Image.open(a.out/'opaque-without-sun.png').convert('RGB');diff=ImageChops.difference(x,y);diff.save(a.out/'opaque-sun-difference.png')
  patch=diff.crop(tuple(round(v*a.dpr) for v in (12,38,72,92)));maximum=max(v[1] for v in patch.getextrema());mean=max(ImageStat.Stat(patch).mean)
  checks={'opaqueCloudAdmitted':sample[3]==255,'solarBodyBlocked':maximum<=2,'noUnexpectedErrors':not e.errors}
  return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'maximumSolarDifferenceBehindOpaqueCloud':maximum,'meanDifference':mean,'cloudRGBA':sample,'state':s,'errors':e.errors,'scope':'Synthetic opaque foreground-buffer control, frozen accepted scene. Tests obstruction, not meteorological calibration.'}
 finally:e.close()

def solar_air(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=0,start='2026-10-07T11:31:00Z',family='clear',steady=True)
 try:
  e.ready();e.frame.add_style_tag(content='*{animation-play-state:paused!important;transition:none!important}.c>*:not(.real-sky-canvas):not(.atmo):not(.wfx){visibility:hidden!important}.atmo>*:not(.sun-cloud-mask),.suncorner,.wfx>*:not(.sun-cloud-mask){visibility:hidden!important}')
  e.element.screenshot(path=a.out/'body-over-air.png')
  e.frame.add_style_tag(content='.sunbody{visibility:hidden!important}')
  e.element.screenshot(path=a.out/'air-only.png')
  foreground=Image.open(a.out/'body-over-air.png').convert('RGB');air=Image.open(a.out/'air-only.png').convert('RGB')
  # A solar source adds light to intervening atmosphere. Its opaque CSS colour
  # must not replace that path radiance, especially with a low-Sun red spectrum.
  box=(32,120,100,168);x=ImageStat.Stat(foreground.crop(box)).mean;y=ImageStat.Stat(air.crop(box)).mean
  checks={'foregroundAirRetained':min(a-b for a,b in zip(x,y))>=-2,'bodyAddsLight':sum(x)-sum(y)>20,'noErrors':not e.errors}
  return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'bodyRGB':x,'airRGB':y,'scope':'Diagnostic ablation: UI, corona/rays and unrelated native effects hidden; physical background plus body remain. Full composition is captured separately.','state':e.snap(),'errors':e.errors}
 finally:e.close()

def row_contrast(a,browser,fonts):
 e=Entry(browser,a.root,a.out,fonts,rate=0,start=a.start,family=a.family,steady=True)
 try:
  e.ready();e.frame.add_style_tag(content='*{animation-play-state:paused!important;transition:none!important}')
  state=e.snap('complete-composition')
  rows=e.frame.evaluate("()=>{const card=document.querySelector('.c').getBoundingClientRect();return [...document.querySelectorAll('.p')].map(e=>{const r=e.getBoundingClientRect();return {key:e.querySelector('b').textContent,cls:e.className,color:getComputedStyle(e.querySelector('b')).color,x:r.x-card.x,y:r.y-card.y,w:r.width,h:r.height};});}")
  e.frame.add_style_tag(content='.p b,.p .tm{visibility:hidden!important}')
  e.element.screenshot(path=a.out/'row-backgrounds.png');im=Image.open(a.out/'row-backgrounds.png').convert('RGB')
  import re
  def luminance(rgb):
   return sum(w*(v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4) for v,w in zip(rgb,[.2126,.7152,.0722]))
  for r in rows:
   r['backgroundRGB']=ImageStat.Stat(im.crop((round(r['x']+25),round(r['y']+r['h']/2-2),round(r['x']+70),round(r['y']+r['h']/2+2)))).median
   rgb=[float(x) for x in re.findall(r'[\d.]+',r['color'])[:3]];lo,hi=sorted([luminance(rgb),luminance(r['backgroundRGB'])]);r['contrast']=(hi+.05)/(lo+.05)
  on=[r for r in rows if 'on' in r['cls'].split()]
  checks={'modelDOMAgreement':all(semantic(state).values()),'nextRowTextReadable':len(on)==1 and on[0]['contrast']>=4.5}
  return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'rows':rows,'state':state,'scope':'Next-row text/background contrast plus actual composition. 4.5:1 normal-size text criterion; visual distinction also requires inspection.'}
 finally:e.close()

def run(a):
 global MONITOR
 if a.surface_replay:MONITOR+=surface_replay_script(a.surface_replay)
 a.root=a.root.resolve();a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(ROOT/'tests'));from v1_browser import fonts
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
 report={'status':'RUNNING','runtime':runtime_identity(a.root),'harness':sha(Path(__file__).read_bytes()),'scope':'Isolated Windows profiles. Sanitised Orlando 28.5383,-81.3792 substitute; method 2, America/New_York, Celsius. Provider current and hourly model fixtures are labelled separately.'}
 if a.surface_replay:report['surfaceReplay']={'file':a.surface_replay.name,'sha256':sha(a.surface_replay.read_bytes()),'scope':'Exact numerical scene through new request envelopes; not worker availability'}
 shutil.copy2(Path(__file__),a.out/'harness.py')
 dump(a.out/'results.json',report)
 try:
  with sync_playwright() as pw:
   b=launch_browser(pw);report['browser']=browser_identity(b)
   modes={'replay':replay,'settled':settled,'playback':playback,'weather':weather_sequence,'controls':controls,'availability':availability,'matrix':matrix,'boundaries':boundaries,'live':live_provider,'profile':profile,'directional':directional,'evening-stars':evening_stars,'star-preview-control':star_preview_control,'solar':solar_size,'dawn':dawn_comparison,'preview-failure':preview_failure,'solar-cloud':solar_cloud,'solar-air':solar_air,'row-contrast':row_contrast}
   modes['current-boundaries']=current_boundaries;modes['cpu-pressure']=cpu_pressure;modes['geometry-edges']=geometry_edges;modes['amber-moon']=amber_moon;modes['twilight-joined']=twilight_joined;modes['lunar-layers']=lunar_layers
   report.update(modes[a.mode](a,b,ff));b.close()
 except Exception:report.update(status='FAIL',exception=traceback.format_exc())
 if a.mode=='playback':report['failures']=[*report.get('failures',[]),*playback_publication_failures(report)]
 if report.get('failures'):report['status']='FAIL'
 report['runtimeUnchanged']=report['runtime']==runtime_identity(a.root)
 if not report['runtimeUnchanged']:report.update(status='FAIL',runtimeFailure='Runtime changed during campaign; receipt excluded')
 dump(a.out/'results.json',report);print(json.dumps({k:report.get(k) for k in ['status','browser','wallSeconds','frames','failures','exception']},indent=2),flush=True);return report['status'] not in ['FAIL'] and not report.get('failures')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--deployed',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--mode',choices=['cpu-pressure','current-boundaries','geometry-edges','lunar-layers','twilight-joined','amber-moon','replay','playback','settled','weather','controls','availability','matrix','boundaries','live','profile','directional','evening-stars','star-preview-control','solar','dawn','preview-failure','solar-cloud','solar-air','row-contrast'],required=True);p.add_argument('--rate',type=float,default=600);p.add_argument('--hours',type=float,default=26);p.add_argument('--step',type=int,default=60);p.add_argument('--family',choices=FAMILIES,default='clear');p.add_argument('--cadence',type=float,default=2);p.add_argument('--start',default='2026-10-07T10:00:00Z');p.add_argument('--direct',action='store_true');p.add_argument('--dpr',type=float,default=1);p.add_argument('--offset',type=float,default=0);p.add_argument('--seed',type=int,default=1);p.add_argument('--steady',action='store_true');p.add_argument('--overrides',default='');p.add_argument('--comparison-source',type=Path);p.add_argument('--surface-replay',type=Path);p.add_argument('--duration',type=float,default=0);raise SystemExit(0 if run(p.parse_args()) else 1)
