"""Presented startup pixels + genuine HTTP cache-warm reload (Windows engines).

Test-only service worker intercepts remote provider/font fixtures. Local runtime
requests pass through unmodified. There are NO Playwright routes (those disable
HTTP caching). A binary clock outside the unchanged iframe timestamps the video.
"""
import argparse, asyncio, base64, hashlib, http.server, io, json, os, shutil, subprocess, sys, threading, time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit,parse_qs
from PIL import Image,ImageStat,ImageDraw
from playwright.async_api import async_playwright
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity
from daylight_startup_check import SNAP,SCENES

SCENES.update(rain=('2026-10-07T15:09:00Z',63,85),fog=('2026-10-07T15:09:00Z',45,100))
TIMER=r"""(()=>{if(window!==top)return;document.addEventListener('DOMContentLoaded',()=>{const el=document.createElement('canvas');el.width=344;el.height=20;el.style='position:fixed;left:0;top:566px;width:344px;height:20px;z-index:2147483647;pointer-events:none';document.body.append(el);const c=el.getContext('2d');function tick(){const n=Math.floor(performance.now());c.fillStyle='#ff00ff';c.fillRect(0,0,344,20);for(let i=0;i<16;i++){c.fillStyle=(n>>i)&1?'white':'black';c.fillRect(8+i*20,0,20,20);}requestAnimationFrame(tick);}tick();},{once:true});})();"""
TRACE=r"""()=>{const q=window.qaState?.(),s=(SNAP)();return {...s,absolute:performance.timeOrigin+performance.now(),render:q?.render,wxTruth:q?.wxTruth,weatherHeader:q?.weatherHeader,header:{icon:document.querySelector('#wi')?.textContent,temp:document.querySelector('#wt')?.textContent,title:document.querySelector('#wi')?.title},rows:[...document.querySelectorAll('.times .p')].map(e=>({key:e.querySelector('b')?.textContent,cls:e.className,time:e.querySelector('.tm')?.textContent})),countdown:document.querySelector('.left')?.textContent};}""".replace('SNAP',SNAP)

def decode(path,ffmpeg):
 p=subprocess.Popen([str(ffmpeg),'-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 index=0
 while True:
  data=p.stdout.read(390*600*3)
  if not data:break
  if len(data)!=390*600*3:raise RuntimeError('Truncated raw video')
  im=Image.frombytes('RGB',(390,600),data);r,g,b=im.getpixel((3,576))
  if r>170 and b>170 and g<90:
   ms=sum((1<<i) if sum(im.getpixel((18+i*20,576)))>400 else 0 for i in range(16))
   yield index,ms,im
  index+=1
 if p.wait():raise RuntimeError('Video decode failed')

async def run(a):
 a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.root/'tests'))
 from v1_browser import fonts,fixture,FONT_CSS,ROOT_KEY,V1_KEY,SETTINGS
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
 stamp,wx,cloud=SCENES[a.scene];suffix=('v1/' if a.v1 else '')+'#local=1&motion=full'
 wrapper='<!doctype html><meta charset="utf-8"><body style="margin:8px;background:#1a2335"><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="/salah_widget/'+suffix+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden;position:relative;left:'+str(a.offset)+'px" scrolling="no"></iframe>'
 requests=[];external=[];failures=[]
 def provider(u):
  v=fixture(u,a.scene=='night');host=urlsplit(u).hostname
  if host=='api.aladhan.com':
   date=urlsplit(u).path.rstrip('/').split('/')[-1];day,month,year=date.split('-');v['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year);v['data']['meta']['timezone']='America/New_York';v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
  if host=='api.open-meteo.com':
   if a.weather_delay:time.sleep(a.weather_delay)
   v.update(latitude=28.5383,longitude=-81.3792,elevation=25,timezone='America/New_York',utc_offset_seconds=-14400)
   # Requested timezone=auto: use local ISO current interval, not UTC.
   # This fixture is explicitly October EDT (UTC-4); preserve date rollover.
   local=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(timezone(timedelta(hours=-4)))
   local_interval=local.replace(minute=local.minute//15*15,second=0,microsecond=0).strftime('%Y-%m-%dT%H:%M')
   v['current'].update(time=local_interval,interval=900,weather_code=wx,cloud_cover=cloud,cloud_cover_low=cloud,cloud_cover_mid=0,cloud_cover_high=0,precipitation=2 if wx==63 else 0,rain=2 if wx==63 else 0,visibility=500 if wx==45 else 20000)
   # An acquiring (unsaved) widget keeps its configured Fahrenheit default.
   # Honour the actual request rather than serving contradictory Celsius
   # metadata, which the product correctly rejects as an invalid snapshot.
   fahrenheit=parse_qs(urlsplit(u).query).get('temperature_unit')==['fahrenheit']
   if fahrenheit:
    for field in ['temperature_2m','apparent_temperature','dew_point_2m']:
     if v['current'].get(field) is not None:v['current'][field]=v['current'][field]*9/5+32
   v['current_units']={'time':'iso8601','interval':'seconds','temperature_2m':'°F' if fahrenheit else '°C','apparent_temperature':'°F' if fahrenheit else '°C','dew_point_2m':'°F' if fahrenheit else '°C','wind_speed_10m':'m/s','precipitation':'mm','rain':'mm','showers':'mm','snowfall':'cm'}
  if host in ['get.geojs.io','ipinfo.io']:
   if a.acquiring:time.sleep(1.5)
   v={'latitude':'28.5383','longitude':'-81.3792','loc':'28.5383,-81.3792','city':'Orlando fixture','country':'United States','country_code':'US','timezone':'America/New_York'}
  return v
 sw="self.addEventListener('install',()=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));self.addEventListener('fetch',e=>{if(new URL(e.request.url).origin!==self.location.origin)e.respondWith(fetch('/_fixture?url='+encodeURIComponent(e.request.url)));});"
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):return str(a.root/urlsplit(path).path.removeprefix('/salah_widget/'))
  def end_headers(self):self.send_header('Cache-Control','public,max-age=3600' if self.path.startswith('/salah_widget/') else 'no-store');super().end_headers()
  def send(self,b,kind='text/html',status=200):
   self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  def do_GET(self):
   requests.append(self.path)
   try:
    if self.path=='/fixture-sw.js':self.send(sw.encode(),'text/javascript')
    elif self.path=='/setup':self.send(b'<!doctype html><title>Fixture setup</title><iframe src="/setup-child"></iframe>')
    elif self.path=='/setup-child':self.send(b'<!doctype html><title>Fixture frame setup</title>')
    elif self.path=='/iframe':self.send(wrapper.encode())
    elif self.path=='/favicon.ico':self.send(b'',status=204)
    elif self.path.startswith('/_fixture?'):
     u=parse_qs(urlsplit(self.path).query)['url'][0];external.append(u)
     if u in ff:self.send(ff[u].read_bytes(),'text/css' if u==FONT_CSS else 'font/woff2')
     else:self.send(json.dumps(provider(u)).encode(),'application/json')
    else:super().do_GET()
   except (BrokenPipeError,ConnectionResetError):pass
   except Exception as e:failures.append(str(e));self.send(str(e).encode(),status=500)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 report={'status':'RUNNING','scene':a.scene,'v1':a.v1,'direct':a.direct,'dpr':a.dpr,'offset':a.offset,'runtime':runtime_identity(a.root),'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Controlled Orlando substitute (28.5383,-81.3792), not claimed user location. Normal 1x from '+stamp+'. Provider/font fixtures through test service worker; ordinary current weather lane. No Playwright routing or local runtime modification.','errors':[],'assetFailures':[],'runs':[]}
 def save():(a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 with_video=os.environ.get('SALAH_BROWSER','chromium')!='firefox'
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 async with async_playwright() as pw:
  browser=await launch_browser(pw);report['browser']=browser_identity(browser)
  recording={'record_video_dir':str(a.out/'video'),'record_video_size':{'width':390,'height':600}} if with_video else {}
  ctx=await browser.new_context(viewport={'width':390,'height':600},**recording,device_scale_factor=a.dpr,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference')
  setup=await ctx.new_page();await setup.goto(origin+'/setup');
  for client in setup.frames:
   await client.evaluate("async()=>{await navigator.serviceWorker.register('/fixture-sw.js');await navigator.serviceWorker.ready;}");await client.wait_for_function('!!navigator.serviceWorker.controller')
  await setup.close()
  if not with_video:
   # This installed Firefox reports a controlling SW but bypasses its cross-
   # origin fetch handler. Use an explicit provider TRANSPORT fixture instead;
   # application fetch/admission/expiry code is unchanged, local requests remain
   # browser-cached. Do not mistake uncontrolled live responses for fixtures.
   await ctx.add_init_script("{const realFetch=window.fetch.bind(window);window.fetch=(input,init)=>{const u=new URL(typeof input==='string'?input:input.url,location.href);return realFetch(u.origin!==location.origin?'/\x5ffixture?url='+encodeURIComponent(u.href):input,init);};}")
   report['fixtureTransport']='Firefox window.fetch transport fixture; local HTTP cache enabled'
  else:report['fixtureTransport']='Chromium service-worker remote transport fixture; local HTTP cache enabled'
  # An adopted sheet wins over the external font declarations in both engines.
  # Font bytes are the retained, hashed fixture fonts; this does not rewrite any
  # runtime source or local asset, and cannot disable HTTP runtime caching.
  css=ff[FONT_CSS].read_text(encoding='utf-8')
  for u,p in ff.items():
   if u!=FONT_CSS:css=css.replace(u,'data:font/woff2;base64,'+base64.b64encode(p.read_bytes()).decode())
  await ctx.add_init_script('try{const fixtureFonts=new CSSStyleSheet();fixtureFonts.replaceSync('+json.dumps(css)+');document.adoptedStyleSheets=[...document.adoptedStyleSheets,fixtureFonts];}catch(e){window.__fixtureFontError=String(e);}')
  report['fontHashes']={u:hashlib.sha256(p.read_bytes()).hexdigest() for u,p in ff.items()}
  settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
  if not a.acquiring:await ctx.add_init_script('if(location.protocol==="http:"&&!localStorage.getItem('+json.dumps(V1_KEY if a.v1 else ROOT_KEY)+'))localStorage.setItem('+json.dumps(V1_KEY if a.v1 else ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
  # Keep one normal clock across both navigations; resetting UTC on reload would
  # incorrectly make the previous weather receipt appear to come from the future.
  clock_origin=time.time()*1000
  await ctx.add_init_script("(()=>{const D=Date,s="+str(clock_origin)+",t=D.parse("+json.dumps(stamp)+");window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();")
  await ctx.add_init_script(TIMER)
  await ctx.add_init_script('window.__startupOwners=[];window.__firstPaint=[];try{new PerformanceObserver(l=>__firstPaint.push(...l.getEntries().map(x=>({name:x.name,startTime:x.startTime})))).observe({type:"paint",buffered:true});}catch{}const _trace=setInterval(()=>{if(document.querySelector(".c"))__startupOwners.push(('+TRACE+')());if(performance.now()>14000)clearInterval(_trace);},100);')
  for mode in ['cold','warm']:
   mark=len(requests);page=await ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['assetFailures'].append([r.url,r.status]) if r.url.startswith(origin) and r.status>=400 else None)
   shot_frames=[];shot_done=False
   async def capture_firefox():
    # Windows Firefox's installed Juggler has no video recorder. Capture actual
    # framebuffer PNGs concurrently with navigation, retaining acquisition times.
    # These are explicitly sampled frames, not claimed continuous video or 0ms.
    while not shot_done:
     try:
      begin=time.monotonic();raw=await page.screenshot(timeout=3000);end=time.monotonic()
      im=Image.open(io.BytesIO(raw)).convert('RGB').resize((390,600),Image.Resampling.LANCZOS);r,g,b=im.getpixel((3,576))
      if r>170 and b>170 and g<90:
       ms=sum((1<<i) if sum(im.getpixel((18+i*20,576)))>400 else 0 for i in range(16));shot_frames.append((len(shot_frames),ms,im,end-begin))
     except Exception:pass
     await asyncio.sleep(.025)
   # Chrome's lossy WebM can move a near-threshold blue channel by a few codes.
   # Keep that movie for motion, but qualify lossless presented compositor PNGs.
   # This does not relax the daylight gate or redraw/copy the product equation.
   cdp=None;presented=[]
   if with_video:
    cdp=await ctx.new_cdp_session(page)
    def receive_frame(event):
     presented.append((event['data'],event['metadata'].get('timestamp')))
     asyncio.create_task(cdp.send('Page.screencastFrameAck',{'sessionId':event['sessionId']}))
    cdp.on('Page.screencastFrame',receive_frame)
    await cdp.send('Page.startScreencast',{'format':'png','everyNthFrame':1,'maxWidth':390,'maxHeight':600})
   collector=None if with_video else asyncio.create_task(capture_firefox())
   await page.goto(origin+('/salah_widget/'+suffix if a.direct else '/iframe'),wait_until='commit')
   if a.direct:frame=page.main_frame
   else:await page.frame_locator('iframe').locator('.c').wait_for(state='attached');frame=next(x for x in page.frames if '/salah_widget/' in x.url)
   await frame.locator('.c').wait_for(state='attached');await page.wait_for_timeout(max(1,10500-await page.evaluate('performance.now()')))
   if not a.v1:await frame.wait_for_function("window.realSkyState?.().status==='ready'",timeout=45000)
   shot_done=True
   if collector:await collector
   if cdp:await cdp.send('Page.stopScreencast')
   final=await frame.evaluate(TRACE);element=frame.locator('.c') if a.direct else page.locator('iframe');rect=await element.bounding_box();await element.screenshot(path=a.out/f'{mode}-final.png')
   run={'name':mode,'fixtureController':await frame.evaluate('navigator.serviceWorker.controller?.scriptURL'),'captureMethod':'Chromium video' if with_video else 'Firefox concurrent framebuffer PNG samples; native video API unavailable on this Windows build','final':final,'rect':rect,'ownerTrace':await frame.evaluate('__startupOwners'),'paintEvents':await frame.evaluate('__firstPaint'),'parentTimeOrigin':await page.evaluate('performance.timeOrigin'),'resources':await frame.evaluate("performance.getEntriesByType('resource').map(x=>({name:x.name,transferSize:x.transferSize,encodedBodySize:x.encodedBodySize,decodedBodySize:x.decodedBodySize,duration:x.duration}))"),'serverRequests':requests[mark:]}
   report['runs'].append(run);save();video=page.video;await page.close()
   if with_video:
    await video.save_as(a.out/f'{mode}.webm');frames=[]
    for raw,presentation_stamp in presented:
     im=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGB');r,g,b=im.getpixel((3,576))
     if r>170 and b>170 and g<90:
      ms=sum((1<<i) if sum(im.getpixel((18+i*20,576)))>400 else 0 for i in range(16));frames.append((len(frames),ms,im))
    run['captureMethod']='Chromium lossless compositor PNG events; WebM retained separately for motion, not threshold colour measurement'
    run['compositorTimestamps']=[t for _,t in presented]
    if frames:frames[0][2].save(a.out/f'{mode}-presented.webp',save_all=True,append_images=[x[2] for x in frames[1:]],duration=[max(10,frames[i+1][1]-x[1]) if i<len(frames)-1 else 100 for i,x in enumerate(frames)],lossless=True)
   else:
    frames=[(i,t,im) for i,t,im,_ in shot_frames];run['captureDurationsMs']=[d*1000 for _,_,_,d in shot_frames]
    if frames:frames[0][2].save(a.out/f'{mode}-sampled.webp',save_all=True,append_images=[x[2] for x in frames[1:]],duration=[max(25,frames[i+1][1]-x[1]) if i<len(frames)-1 else 100 for i,x in enumerate(frames)],lossless=True)
   run['presentedFrameCount']=len(frames)
   run['maximumPresentedGapMs']=max((b[1]-a[1] for a,b in zip(frames,frames[1:])),default=0)
   crop=(round(rect['x']),round(rect['y']),round(rect['x']+330),round(rect['y']+534))
   visible=[entry for entry in frames if ImageStat.Stat(entry[2].crop((crop[0]+40,crop[1]+25,crop[0]+270,crop[1]+60))).stddev[0]>9]
   def record(entry):
    i,t,im=entry;rgb=ImageStat.Stat(im.crop((crop[0]+265,crop[1]+183,crop[0]+309,crop[1]+229))).median
    state=min(run['ownerTrace'],key=lambda s:abs(s['absolute']-run['parentTimeOrigin']-t)) if run['ownerTrace'] else None
    return {'videoFrame':i,'actualPresentedMs':t,'nearestOwnerTraceMs':state['absolute']-run['parentTimeOrigin'] if state else None,'state':state,'patch':{'medianRGB':rgb,'blueMinusRed':rgb[2]-rgb[0],'luma':sum(v*w for v,w in zip(rgb,[.2126,.7152,.0722]))}}
   chosen=[('first-visible',visible[0])] if visible else []
   chosen += [(str(t),min(frames,key=lambda e:abs(e[1]-t))) for t in [250,500,1000,2000,4000,8000]] if frames else []
   captures=[]
   for label,entry in chosen:
    rec=record(entry);rec.update(requestedMs=None if label=='first-visible' else int(label),file=f'{mode}-{label}.png');entry[2].crop(crop).save(a.out/rec['file']);captures.append(rec)
   checked=[record(e) for e in visible if e[1]<=8500]
   if a.acquiring:
    run['acquisitionFrames']=[x for x in checked if not (x['state'] or {}).get('accepted') or x['state']['accepted'].get('lat') is None]
    # Unknown site is a separately declared acquisition state. Once a real
    # target is admitted, it must pass the same daylight test as saved sites.
    checked=[x for x in checked if (x['state'] or {}).get('accepted') and x['state']['accepted'].get('lat') is not None]
   # Predetermined display gate, outside Sun/UI and native cloud support:
   # clear/partial B>=150,B-R>=40; cloudy/fog daylight luminance>=90.
   # Retained f05 near-black startup and 68/80/100 settled sky FAIL this gate.
   if a.scene in ['clear','partial']:predicate=lambda x:x['patch']['medianRGB'][2]>=150 and x['patch']['blueMinusRed']>=40
   elif a.scene in ['heavy','fog','rain']:predicate=lambda x:x['patch']['luma']>=90
   else:predicate=lambda x:True
   run.update(captures=captures,firstVisibleMs=visible[0][1] if visible else None,daylightFramesChecked=len(checked),daylightFailures=[{'actualPresentedMs':x['actualPresentedMs'],'patch':x['patch']} for x in checked if not predicate(x)])
   run['cacheHits']=[x for x in run['resources'] if x['name'].startswith(origin+'/salah_widget/') and x['encodedBodySize']>0 and x['transferSize']==0]
   save();print(mode,'first visible',run['firstVisibleMs'],'ms; daylight failures',len(run['daylightFailures']),'cache hits',len(run['cacheHits']),flush=True)
  report['checks']={'noPageErrors':not report['errors'],'noLocalAssetFailures':not report['assetFailures'] and not failures,'prayerReady':all(r['final']['prayerReady'] for r in report['runs']),'visibleFramesCaptured':all(r['daylightFramesChecked']>0 for r in report['runs']),'daylightEveryVisibleFrame':all(not r['daylightFailures'] for r in report['runs']),'genuineWarmRuntimeCache':bool(report['runs'][1]['cacheHits'])}
  report['checks']['fixturesActuallyConsumed']=all((r['fixtureController'] or not with_video) and r['final']['render'] and r['final']['render']['nextTime']=='13:17' for r in report['runs']) if a.scene not in ['night','twilight'] and not a.v1 else bool(external)
  # The native header/accepted display snapshot rounds degrees (82.4F -> 82F).
  report['checks']['currentWeatherAdmitted']=all(r['final']['weatherHeader'] and r['final']['weatherHeader']['rawCode']==wx and r['final']['weatherHeader']['temperature']==(28 if r['final']['accepted']['units']=='c' else 82) and r['final']['accepted']['weather'] and r['final']['accepted']['weather']['cloud']==cloud and r['final']['accepted']['weather']['vis']==(500 if wx==45 else 20000) for r in report['runs']) if not a.v1 else True
  report['checks']['runtimeUnchanged']=report['runtime']==runtime_identity(a.root)
  report['acquiringLocation']=a.acquiring
  report.update(externalRequests=external,serverFailures=failures);report['status']='REFERENCE' if a.v1 else 'PASS' if all(report['checks'].values()) else 'FAIL';save();await ctx.close();await browser.close()
 server.shutdown();captures=report['runs'][0]['captures'];sheet=Image.new('RGB',(330*len(captures),564),'#1a2335');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(captures):sheet.paste(Image.open(a.out/r['file']),(330*i,30));draw.text((330*i+8,8),f"{r['actualPresentedMs']} ms actual ({r['requestedMs']})",fill='white')
 sheet.save(a.out/'startup-sequence.png');print(json.dumps({'status':report['status'],'checks':report['checks'],'out':str(a.out)},indent=2));return int(report['status']=='FAIL')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--scene',choices=SCENES,default='partial');p.add_argument('--dpr',type=float,default=1);p.add_argument('--offset',type=float,default=0);p.add_argument('--weather-delay',type=float,default=0);p.add_argument('--acquiring',action='store_true');p.add_argument('--v1',action='store_true');p.add_argument('--direct',action='store_true');p.add_argument('--ffmpeg',type=Path,default=shutil.which('ffmpeg'));raise SystemExit(asyncio.run(run(p.parse_args())))
