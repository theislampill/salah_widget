"""First-seconds control: unchanged runtime/CSS, real 1x, disposable cache/profile.

No Playwright routing (it disables HTTP cache). Only external fetch transport and
the accepted wall-clock anchor are fixtures. Visual runs never poll app getters.
Instrumentation is an explicit separate run, never timing proof for visual runs.
"""
import argparse, asyncio, hashlib, http.server, json, math, os, platform, sys, threading, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.async_api import async_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_runtime import launch_browser, browser_identity, browser_options
from runtime_identity import runtime_identity

# This clock is outside the card (and outside the iframe). It reads no app state.
# This marker is an external rAF clock, not a presentation timestamp: it can
# freeze when the shared main thread is busy. Native source-frame receipts retain
# browser timestamps and wall-time receipt bounds. The driver's frameSwapWallTime
# name alone does not prove presentation; reconcile compositor feedback separately.
# Never infer elapsed presentation time from screenshot request labels.
TIMER = r"""(()=>{if(window!==top)return;const install=()=>{
 if(!document.body)return false;const el=document.createElement('canvas');el.width=344;el.height=20;el.style='position:fixed;left:0;top:566px;width:344px;height:20px;z-index:2147483647;pointer-events:none';document.body.append(el);const c=el.getContext('2d');
 function tick(){const n=Math.floor(performance.now());c.fillStyle='#ff00ff';c.fillRect(0,0,344,20);for(let i=0;i<16;i++){c.fillStyle=(n>>i)&1?'white':'black';c.fillRect(8+i*20,0,20,20);}requestAnimationFrame(tick);}tick();return true;};
 if(!install()){const observer=new MutationObserver(()=>{if(install())observer.disconnect();});observer.observe(document,{childList:true,subtree:true});}})();"""

TRACE = r"""(()=>{
 const log=(stage,extra={})=>(window.__celestialTrace??=[]).push({stage,at:performance.now(),...extra});
 new PerformanceObserver(l=>{for(const e of l.getEntries())log(e.entryType,{name:e.name,start:e.startTime,duration:e.duration});}).observe({entryTypes:['paint','longtask']});
 const B=Blob;window.Blob=class extends B{constructor(parts,options){
  if(options?.type==='text/javascript'&&parts.some(p=>typeof p==='string'&&p.includes('class MoonEngine{'))){parts=[...parts,`\n;(()=>{
   const log=(stage,extra={})=>console.info('__CELESTIAL_WORKER__'+JSON.stringify({stage,absolute:performance.timeOrigin+performance.now(),...extra}));
   const read0=read;read=async(...a)=>{log('asset-start',{url:String(a[0])});const t=performance.now(),v=await read0(...a);log('asset-end',{url:String(a[0]),bytes:v.length,ms:performance.now()-t});return v;};
   const dec0=decodeAsset;decodeAsset=async(...a)=>{const t=performance.now();log('decode-start',{path:a[1].path});const v=await dec0(...a);log('decode-end',{path:a[1].path,ms:performance.now()-t});return v;};
   const create0=MoonEngine.create;MoonEngine.create=async(...a)=>{const t=performance.now();log('engine-start');const v=await create0.apply(MoonEngine,a);log('engine-ready',{ms:performance.now()-t});return v;};
   const render0=MoonEngine.prototype.render;MoonEngine.prototype.render=async function(...a){const t=performance.now();log('pass-start',{size:a[0].size,radial:a[1]?.radial,azimuth:a[1]?.azimuth});const v=await render0.apply(this,a);log('pass-end',{ms:performance.now()-t,diagnostics:v.diagnostics});return v;};
  })();`];window.__celestialWorkerSource=parts.join('');}super(parts,options);}};
 const W=Worker;let n=0;window.Worker=class extends W{constructor(...args){super(...args);this.__traceId=++n;log('worker-create',{worker:this.__traceId});this.addEventListener('message',e=>{const m=e.data;if(m.kind!=='progress')log('worker-message',{worker:this.__traceId,kind:m.kind,id:m.id,diagnostics:m.diagnostics});});}postMessage(m,...rest){log('worker-send',{worker:this.__traceId,kind:m.kind,id:m.id});if(m.workerSource&&window.__celestialWorkerSource)m={...m,workerSource:window.__celestialWorkerSource};return super.postMessage(m,...rest);}};
 let host;Object.defineProperty(window,'SalahMoonHost',{configurable:true,get:()=>host,set(value){host={...value,publish(...args){log('moon-publish');return value.publish(...args);}};}});
 let initial;Object.defineProperty(window,'SalahMoonInitial',{configurable:true,get:()=>initial,set(value){log('initial-data-admitted');initial={...value,render(...args){log('initial-start');const v=value.render(...args);log('initial-end',{diagnostics:v.diagnostics});return v;}};}});
 let startPreview;Object.defineProperty(window,'SalahStartSkyPreview',{configurable:true,get:()=>startPreview,set(value){startPreview=(...args)=>{log('preview-host-start');const v=value(...args);log('preview-host-end');return v;};}});
 let preview;Object.defineProperty(window,'SalahSkyPreview',{configurable:true,get:()=>preview,set(value){preview=value;const original=value.admitCatalogue;value.admitCatalogue=function(...args){log('catalogue-admit-start',{nonnull:!!args[0]});const p=original.apply(this,args);p?.then(()=>log('catalogue-admit-end',{nonnull:!!args[0]}));return p;};}});
 const observe=()=>new MutationObserver(list=>{for(const m of list)if(m.type==='attributes'&&m.target.matches?.('.c'))log('card-classes',{classes:m.target.className});}).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:['class']});
 if(document.documentElement)observe();else document.addEventListener('DOMContentLoaded',observe,{once:true});
})();"""

FINAL = r"""()=>{
 const box=e=>{if(!e)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,visibility:s.visibility,opacity:s.opacity};};
 return {at:performance.now(),timeOrigin:performance.timeOrigin,trace:window.__celestialTrace??[],
 resources:performance.getEntriesByType('resource').map(e=>e.toJSON()),navigation:performance.getEntriesByType('navigation').map(e=>e.toJSON()),
 firstPaint:window.SalahFirstPaint?.preparedAt,moon:window.SalahMoonRuntime?.state,sky:window.realSkyState?.(),preview:window.SalahSkyPreview?.state,
 native:window.SalahNativeSkyHost?.capture(false),qa:window.qaState?.(),card:box(document.querySelector('.c')),photo:box(document.querySelector('.mphoto')),
 detail:box(document.querySelector('.moon-detail-canvas')),classes:document.querySelector('.c')?.className,
 settingsButton:!!document.querySelector('.buckle.interactive'),prayerRows:[...document.querySelectorAll('.times .p')].map(e=>e.textContent)};
}"""

async def run(a):
 a.out.mkdir(parents=True,exist_ok=True)
 if a.driver_cli:
  # Optional already-installed driver, e.g. newer Firefox screencast protocol.
  # No package install or owner browser profile mutation. Record both versions.
  import playwright._impl._transport as transport
  if not a.driver_node or not a.driver_cli.is_file() or not a.driver_node.is_file():raise ValueError('Explicit existing driver/node required')
  transport.compute_driver_executable=lambda:(str(a.driver_node),str(a.driver_cli))
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
 from v1_browser import fixture, SETTINGS, ROOT_KEY
 stamp='2026-09-25T02:00:00Z' if a.scene!='day' else '2026-09-25T17:00:00Z'
 wx,cloud={'clear':(0,0),'partial':(2,35),'rain':(63,65),'incident':(63,65),'day':(0,0),'moon-negative':(0,0),'dawn':(0,0)}[a.scene]
 if a.scene in ['incident','moon-negative']:stamp='2026-10-09T01:00:00Z'
 if a.scene=='dawn':stamp='2026-09-25T10:40:00Z'
 suffix='#local=1&motion=full'
 requests=[];errors=[];server_recovered=False
 clock_origin=time.time()*1000
 def provider(u):
  v=fixture(u,a.scene!='day');host=urlsplit(u).hostname
  if host=='api.aladhan.com':
   if a.prayer_delay:time.sleep(a.prayer_delay)
   d=urlsplit(u).path.rstrip('/').split('/')[-1];day,month,year=d.split('-')
   v['data']['date']['gregorian'].update(date=d,day=day,month={'number':int(month)},year=year)
   # Valid synthetic civil-calendar fixture, independent of celestial phase.
   # The inherited V1 fixture used Gregorian day+17, yielding impossible days
   # in September. Retained earlier captures cannot certify Hijri readiness.
   hd=11+(datetime(int(year),int(month),int(day))-datetime(2026,9,24)).days
   if not 1<=hd<=30:raise ValueError('Calendar fixture outside bounded capture dates')
   v['data']['date']['hijri'].update(day=str(hd),month={'number':4,'en':'Rabi al-Thani'},year='1448')
   v['data']['meta']['timezone']='America/New_York'
   v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  elif host=='api.open-meteo.com':
   local=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=-4)))
   query=parse_qs(urlsplit(u).query)
   v.update(latitude=float(query.get('latitude',['28.5383'])[0]),longitude=float(query.get('longitude',['-81.3792'])[0]),elevation=0,timezone='America/New_York',utc_offset_seconds=-14400)
   v['current'].update(time=local.strftime('%Y-%m-%dT%H:%M'),interval=900,weather_code=wx,cloud_cover=cloud,cloud_cover_low=cloud,cloud_cover_mid=0,cloud_cover_high=0,precipitation=2 if wx==63 else 0,rain=2 if wx==63 else 0,visibility=20000)
   fahrenheit=parse_qs(urlsplit(u).query).get('temperature_unit')==['fahrenheit']
   if fahrenheit:
    for field in ['temperature_2m','apparent_temperature','dew_point_2m']:
     if v['current'].get(field) is not None:v['current'][field]=v['current'][field]*9/5+32
   v['current_units']={'time':'iso8601','interval':'seconds','temperature_2m':'°F' if fahrenheit else '°C','apparent_temperature':'°F' if fahrenheit else '°C','dew_point_2m':'°F' if fahrenheit else '°C','wind_speed_10m':'m/s','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm'}
  elif host in ['get.geojs.io','ipinfo.io']:
   if a.acquiring:time.sleep(1.5)
   v={'latitude':'28.5383','longitude':'-81.3792','loc':'28.5383,-81.3792','city':'Orlando fixture','country':'United States','country_code':'US','timezone':'America/New_York'}
  return v
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,p):return str(a.root/urlsplit(p).path.removeprefix('/salah_widget/'))
  def send_response(self,code,message=None):self.response_status=code;super().send_response(code,message)
  def end_headers(self):self.send_header('Cache-Control','public,max-age=3600' if self.path.startswith('/salah_widget/') and self.response_status==200 else 'no-store');super().end_headers()
  def send(self,b,kind='text/html',status=200):
   self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  def do_GET(self):
   requests.append({'url':self.path,'absolute':time.time()*1000})
   try:
    if self.path=='/iframe':self.send(('<!doctype html><meta charset="utf-8"><body style="margin:8px;background:#1a2335"><iframe title="Prayer Times" src="/salah_widget/'+suffix+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden" scrolling="no"></iframe>').encode())
    elif self.path.startswith('/fixture?'):self.send(json.dumps(provider(parse_qs(urlsplit(self.path).query)['url'][0])).encode(),'application/json')
    elif self.path=='/favicon.ico':self.send(b'',status=204)
    elif a.hold and not server_recovered and (('native-data.js' in self.path and a.hold in ['sky','all']) or ('/moon/assets/' in self.path and a.hold in ['moon','all'])):
     if a.missing:self.send(b'controlled missing full asset','text/plain',503)
     else:time.sleep(a.delay);super().do_GET()
    else:super().do_GET()
   except (BrokenPipeError,ConnectionResetError):pass
   except Exception as e:errors.append(str(e));self.send(str(e).encode(),status=500)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 report={'schema':'celestial-startup/1','runtime':runtime_identity(a.root),'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'scene':a.scene,'stamp':stamp,'dpr':a.dpr,'entry':a.entry,'instrumented':a.trace,'syntheticWeather':{'code':wx,'cloud':cloud,'precipMm':2 if wx==63 else 0},
  'scope':'Isolated browser/profile; fixed accepted Orlando substitute; wall-clock progresses at real 1x. Normal CSS. Provider fetch transport only is substituted. No app getters read until first-seconds capture ends. No Playwright routes. Actual extension parent unavailable.',
  'fixtureRevision':2,'syntheticHijri':'civil fixture: 2026-09-24 = 1448-04-11; not a local religious-calendar assertion','cdpFilmstrip':a.cdp_filmstrip,
  'hold':a.hold,'holdSeconds':a.delay if a.hold else 0,'missing':a.missing,'acquiring':a.acquiring,'prayerDelaySeconds':a.prayer_delay,'recoverAfterSeconds':a.recover_at,'cpuProfile':a.cpu_profile,'fontDelaySeconds':a.font_delay,'fontRouteDisablesCache':bool(a.font_delay),'videoOnlyFirstSeconds':a.video_only,
  'driverOverride':{'cli':str(a.driver_cli),'node':str(a.driver_node)} if a.driver_cli else None,'runs':[],'errors':errors}
 def save():
  nonfinite=[]
  def safe(value,path=''):
   if isinstance(value,float) and not math.isfinite(value):nonfinite.append({'pointer':path,'value':str(value)});return None
   if isinstance(value,dict):return {k:safe(v,path+'/'+str(k)) for k,v in value.items()}
   if isinstance(value,list):return [safe(v,path+'/'+str(i)) for i,v in enumerate(value)]
   return value
  out=safe(report);out['nonfiniteDiagnostics']=nonfinite
  (a.out/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 async with async_playwright() as pw:
  video=os.environ.get('SALAH_BROWSER','chromium')=='chromium' or a.video
  recording={'record_video_dir':str(a.out/'video'),'record_video_size':{'width':390,'height':600}} if video else {}
  report['visualCapture']='25fps video plus PNG controls' if video else 'PNG sequence; installed Firefox lacks Browser.setVideoRecordingOptions; gaps recorded'
  context_options=dict(viewport={'width':390,'height':600},device_scale_factor=a.dpr,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference',**recording)
  if a.persistent_profile:
   family,options=browser_options()
   ctx=await getattr(pw,family).launch_persistent_context(str(a.out/'isolated-browser-profile'),**options,**context_options);browser=ctx.browser
  else:
   browser=await launch_browser(pw);ctx=await browser.new_context(**context_options)
  report['browser']=browser_identity(browser);report['persistentIsolatedProfile']=a.persistent_profile
  report['captureTrace']=a.capture_trace
  if a.font_delay:
   async def delay_font(route):
    await asyncio.sleep(a.font_delay);await route.continue_()
   await ctx.route('https://fonts.googleapis.com/**',delay_font)
  if a.capture_trace:
   if a.persistent_profile:raise ValueError('Capture trace requires a fresh context so recording and trace start before the first page')
   await ctx.tracing.start(screenshots=True,snapshots=False,sources=False)
  settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
  if not a.acquiring:await ctx.add_init_script('if(location.protocol==="http:"&&!localStorage.getItem('+json.dumps(ROOT_KEY)+'))localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
  await ctx.add_init_script("(()=>{const D=Date,s="+str(clock_origin)+",t=D.parse("+json.dumps(stamp)+");window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();")
  await ctx.add_init_script("{const original=window.fetch.bind(window);window.fetch=(input,init)=>{const u=new URL(typeof input==='string'?input:input.url,location.href);return original(u.origin!==location.origin&&['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io'].includes(u.hostname)?'"+origin+"/fixture?url='+encodeURIComponent(u.href):input,init);};}")
  if a.trace:await ctx.add_init_script(TRACE)
  await ctx.add_init_script(TIMER)
  page=None;video_file=None
  for mode in a.modes.split(','):
   mark=len(requests);frames=[];worker_events=[]
   if mode!='warm-reload' or page is None:
    # Reuse persistent launch's owned blank page for the cold navigation.
    # Create a fresh tab BEFORE closing its predecessor: Firefox closes its
    # last window otherwise. Each page then owns exactly one recording file.
    previous=page;startup=ctx.pages[0] if page is None and ctx.pages else None
    video_before=set() if startup else set((a.out/'video').glob('*.webm'))
    page=startup or await ctx.new_page()
    if previous:await previous.close()
    page.on('pageerror',lambda e:errors.append(str(e)))
    video_file=None
    page.on('console',lambda m:worker_events.append(json.loads(m.text.removeprefix('__CELESTIAL_WORKER__'))) if m.text.startswith('__CELESTIAL_WORKER__') else None)
   start=time.monotonic();absolute=time.time()*1000
   filmstrip=None;film_events=[];film_clock=[]
   if a.cdp_filmstrip:
    filmstrip=await ctx.new_cdp_session(page);await filmstrip.send('Performance.enable')
    filmstrip.on('Tracing.dataCollected',lambda event:film_events.extend(event['value']))
    before=time.time()*1000;metrics=await filmstrip.send('Performance.getMetrics');after=time.time()*1000
    film_clock=[before,after,next(m['value'] for m in metrics['metrics'] if m['name']=='Timestamp')]
    await filmstrip.send('Tracing.start',{'categories':'disabled-by-default-devtools.screenshot,devtools.timeline','options':'record-as-much-as-possible'})
   profiler=None
   if a.cpu_profile:
    profiler=await ctx.new_cdp_session(page);await profiler.send('Profiler.enable');await profiler.send('Profiler.start')
   url=origin+('/iframe' if a.entry=='iframe' else '/salah_widget/'+suffix)
   if a.entry in ['file','offline-file']:url=(a.root/('offline.html' if a.entry=='offline-file' else 'index.html')).as_uri()+'#lat=28.5383&lon=-81.3792&tz=America/New_York&units=c&method=2&label=CENTRAL%20FL&motion=full'
   start=time.monotonic();absolute=time.time()*1000
   nav=asyncio.create_task(page.reload(wait_until='commit') if mode=='warm-reload' else page.goto(url,wait_until='commit'))
   # A screenshot/recording starts before navigation completes; no app-ready wait.
   targets=[0,.1,.2,.3,.5,.75,1,1.5,2,3,5,8,12,15] if video else [i*.04 for i in range(76)]+[i*.2 for i in range(16,76)]
   if a.video_only:targets=[15]
   for index,t in enumerate(targets):
    await asyncio.sleep(max(0,t-(time.monotonic()-start)))
    began=time.monotonic();file=f'{mode}-{index:02}.png'
    await page.screenshot(path=str(a.out/file),timeout=30000)
    frames.append({'file':file,'requestedMs':t*1000,'captureStartMs':(began-start)*1000,'captureEndMs':(time.monotonic()-start)*1000})
    if profiler and t>=3:
     profile=await profiler.send('Profiler.stop');(a.out/(mode+'-cpu.json')).write_text(json.dumps(profile));await profiler.detach();profiler=None
   await nav
   if filmstrip:
    finished=asyncio.Event();filmstrip.on('Tracing.tracingComplete',lambda _:finished.set());await filmstrip.send('Tracing.end');await asyncio.wait_for(finished.wait(),30)
    (a.out/(mode+'-filmstrip.json')).write_text(json.dumps({'clock':film_clock,'events':film_events}));await filmstrip.detach()
   frame=page.main_frame if a.entry!='iframe' else next(f for f in page.frames if '/salah_widget/' in f.url)
   initial=await frame.evaluate(FINAL)
   if video and video_file is None:
    videos=set((a.out/'video').glob('*.webm'))-video_before
    if len(videos)!=1:raise RuntimeError('Recording file ownership ambiguous: '+str(videos))
    video_file=str(videos.pop())
   recovery=None
   if a.recover_at is not None:
    await asyncio.sleep(max(0,a.recover_at-(time.monotonic()-start)));server_recovered=True
    recovery={'atMs':(time.monotonic()-start)*1000,'retry':await frame.evaluate('async()=>({moon:window.SalahMoonRuntime?.retry(),sky:await window.SalahRealSkyAssets?.retry()})')}
   # Later getter use is explicitly separated from the uninstrumented first15s.
   final=initial
   while time.monotonic()-start<a.duration:
    if (final.get('moon') or {}).get('visibleSource')=='refined-terrain':break
    await asyncio.sleep(1)
    final=await frame.evaluate(FINAL)
   await page.screenshot(path=str(a.out/f'{mode}-final.png'),timeout=30000)
   lifecycle=None
   if a.lifecycle:
    from celestial_lifecycle_check import lifecycle_controls
    lifecycle=await lifecycle_controls(page,frame,a.out,mode)
   layers=None
   if a.layers:
    layers=await frame.evaluate(Path(__file__).with_name('celestial_layer_controls.js').read_text(encoding='utf-8'))
    for name in layers['cases']:
     await frame.evaluate('(name)=>window.__GlowControl.apply(name)',name)
     await page.screenshot(path=str(a.out/f'{mode}-diagnostic-{name}.png'),timeout=30000)
    await frame.evaluate('()=>window.__GlowControl.clear()')
    await page.screenshot(path=str(a.out/f'{mode}-restored-full.png'),timeout=30000)
   report['runs'].append({'mode':mode,'navigationAbsolute':absolute,'topTimeOrigin':await page.evaluate('performance.timeOrigin'),'elapsedMs':(time.monotonic()-start)*1000,'frames':frames,'at15s':initial,'final':final,'recovery':recovery,'lifecycleControls':lifecycle,'layerControls':layers,'workerEvents':worker_events,'serverRequests':requests[mark:],'video':video_file})
   save()
  if a.capture_trace:await ctx.tracing.stop(path=str(a.out/'capture-trace.zip'))
  await ctx.close();await browser.close()
 server.shutdown();report['runtimeUnchanged']=report['runtime']==runtime_identity(a.root);report['status']='OBSERVATIONS_REQUIRING_PIXEL_REVIEW';save()
 print(json.dumps({'out':str(a.out),'errors':errors,'runs':len(report['runs'])}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--scene',choices=['clear','partial','rain','incident','day','moon-negative','dawn'],default='clear');p.add_argument('--entry',choices=['direct','iframe','file','offline-file'],default='iframe')
 p.add_argument('--dpr',type=float,default=1);p.add_argument('--trace',action='store_true');p.add_argument('--duration',type=float,default=120)
 p.add_argument('--modes',default='cold,warm-reload,new-tab');p.add_argument('--hold',choices=['sky','moon','all']);p.add_argument('--delay',type=float,default=20);p.add_argument('--missing',action='store_true')
 p.add_argument('--persistent-profile',action='store_true',help='Disposable disk-cache profile under this evidence output; never an owner profile')
 p.add_argument('--driver-cli',type=Path);p.add_argument('--driver-node',type=Path);p.add_argument('--video',action='store_true')
 p.add_argument('--video-only',action='store_true',help='No PNG requests in the first 15 seconds; native video only, then normal diagnostic snapshot')
 p.add_argument('--cdp-filmstrip',action='store_true',help='Chromium compositor/timeline screenshot diagnostic with independently bracketed monotonic clock')
 p.add_argument('--capture-trace',action='store_true',help='Native screencast frame wall-time stamps; no application getter polling')
 p.add_argument('--cpu-profile',action='store_true',help='Explicit Chromium CPU diagnostic; never ordinary visual evidence')
 p.add_argument('--font-delay',type=float,default=0,help='Diagnostic remote-font hold; routing disables cache, so never a warm-cache proof')
 p.add_argument('--lifecycle',action='store_true',help='Explicit settings/A-B-A/seek/profile controls after ordinary startup')
 p.add_argument('--prayer-delay',type=float,default=0);p.add_argument('--acquiring',action='store_true');p.add_argument('--recover-at',type=float)
 p.add_argument('--layers',action='store_true',help='Labelled one-component controls after ordinary first-seconds and refinement capture')
 asyncio.run(run(p.parse_args()))
