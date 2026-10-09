"""First-paint daylight and preview/refined continuity in the actual widget.

Controlled native inputs and provider/font fixtures; no assertion of live weather.
Also records the rejected startup head and frozen V1 as explicit comparisons.
"""
import argparse, hashlib, http.server, json, shutil, sys, threading, time
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image, ImageDraw, ImageStat
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity

SCENES={'clear':('2026-10-07T15:09:00Z',0,0),'partial':('2026-10-07T15:09:00Z',2,60),'heavy':('2026-10-07T15:09:00Z',3,100),'twilight':('2026-10-07T23:10:00Z',2,35),'night':('2026-10-08T03:30:00Z',2,30)}
SNAP="""()=>{const c=document.querySelector('.c'),cv=document.querySelector('.real-sky-canvas'),pv=document.querySelector('.real-sky-preview'),s=window.realSkyState?.(),q=window.qaState?.(),h=window.SalahNativeSkyHost?.capture(),bar=document.querySelector('.bar>i');const st=e=>e?{visibility:getComputedStyle(e).visibility,opacity:getComputedStyle(e).opacity,display:getComputedStyle(e).display,width:e.width,height:e.height}:null;return {t:performance.now(),utcMs:h?.utcMs??Date.now(),accepted:h??null,solarAltitudeNative:q?.sunEl,weather:h?.weather??q?.wx,host:s,preview:window.SalahSkyPreview?.state??null,background:c&&getComputedStyle(c).background,classes:c?.className,canvas:st(cv),previewCanvas:st(pv),cloudCanvas:st(document.querySelector('.cloudcanvas')),grain:st(document.querySelector('.grain')),prayerReady:q?.cache?.prayerLoaded,bar:{width:bar?.style.width,actual:bar?.getBoundingClientRect().width,total:bar?.parentElement.getBoundingClientRect().width},moon:window.SalahMoonRuntime?.state?.status};}"""

def run(a):
 a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.root/'tests'))
 from v1_browser import fonts,fixture,FONT_CSS,ROOT_KEY,V1_KEY,SETTINGS
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
 stamp,wx,cloud=SCENES[a.scene];suffix=('v1/' if a.v1 else '')+'#local=1&simWx='+str(wx)+'&simCloud='+str(cloud)+'&simPrecip=0&motion=full'
 wrapper='<!doctype html><meta charset="utf-8"><body style="margin:8px;background:#1a2335"><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="/salah_widget/'+suffix+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden" scrolling="no"></iframe>'
 class Server(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):return str(a.root/urlsplit(path).path.removeprefix('/salah_widget/'))
  def do_GET(self):
   if self.path=='/iframe':
    b=wrapper.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
   else:super().do_GET()
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Server);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 report={'scene':a.scene,'v1':a.v1,'direct':a.direct,'dpr':a.dpr,'runtime':runtime_identity(a.root),'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Controlled Orlando observer, native 1x clock anchored to '+stamp+', weather/providers/fonts; first available screenshot and actual timestamps, not assumed target times.','errors':[],'assetFailures':[],'runs':[]}
 def save():(a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 with sync_playwright() as pw:
  b=launch_browser(pw);report['browser']=browser_identity(b)
  ctx=b.new_context(viewport={'width':390,'height':600},device_scale_factor=a.dpr,timezone_id='America/New_York',reduced_motion='no-preference')
  def route(r):
   u=r.request.url
   if u.startswith(origin):r.continue_()
   elif u in ff:r.fulfill(body=ff[u].read_bytes(),content_type='text/css' if u==FONT_CSS else 'font/woff2',headers={'Access-Control-Allow-Origin':'*'})
   else:
    v=fixture(u,a.scene=='night')
    if urlsplit(u).hostname=='api.aladhan.com':
     date=urlsplit(u).path.rstrip('/').split('/')[-1];day,month,year=date.split('-');v['data']['date']['gregorian'].update(date=date,day=day,month={'number':int(month)},year=year);v['data']['meta']['timezone']='America/New_York';v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
    r.fulfill(json=v,headers={'Access-Control-Allow-Origin':'*'})
  ctx.route('**/*',route)
  settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':2,'units':'imperial'}
  ctx.add_init_script('if(location.protocol==="http:")localStorage.setItem('+json.dumps(V1_KEY if a.v1 else ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
  ctx.add_init_script("(()=>{const D=Date,s=performance.now(),t=D.parse("+json.dumps(stamp)+");window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+performance.now()-s]));}static now(){return t+performance.now()-s;}};})();")
  ctx.add_init_script("""(()=>{window.__firstPaint=[];window.__startupOwners=[];try{new PerformanceObserver(l=>__firstPaint.push(...l.getEntries().map(x=>({name:x.name,startTime:x.startTime})))).observe({type:'paint',buffered:true});}catch{}const t=setInterval(()=>{const c=document.querySelector('.c'),cv=document.querySelector('.real-sky-canvas'),p=window.SalahSkyPreview?.state;if(c)__startupOwners.push({t:performance.now(),background:getComputedStyle(c).background,classes:c.className,acceptedUtc:window.SalahNativeSkyHost?.capture()?.utcMs,preview:p?.status,previewUtc:p?.utcMs,canvasVisibility:cv&&getComputedStyle(cv).visibility,canvasOpacity:cv&&getComputedStyle(cv).opacity});if(performance.now()>10000)clearInterval(t);},25);})();""")
  page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['assetFailures'].append([r.url,r.status]) if r.url.startswith(origin) and r.status>=400 else None)
  for mode in ['cold','warm']:
   start=time.monotonic();page.goto(origin+('/salah_widget/'+suffix if a.direct else '/iframe'),wait_until='commit')
   if not a.direct:page.frame_locator('iframe').locator('.c').wait_for(state='attached');frame=next(x for x in page.frames if '/salah_widget/' in x.url)
   else:frame=page.main_frame
   frame.locator('.c').wait_for(state='attached');rows=[]
   for target in [0,.25,.5,1,2,4,8]:
    page.wait_for_timeout(max(1,(target-(time.monotonic()-start))*1000))
    state=frame.evaluate(SNAP);state['targetSeconds']=target;state['elapsedSeconds']=time.monotonic()-start
    shot=a.out/f'{mode}-{target}.png';(page if a.direct else page.locator('iframe')).screenshot(path=shot)
    # Open-sky patch clear of the Sun, lunar disc and text. Native cloud support
    # ends at y=180.2; use the lower strip and inspect full captures separately.
    im=Image.open(shot).convert('RGB');x0=0 if not a.direct else 0
    roi=im.crop(tuple(round(v*a.dpr) for v in (265,183,309,229)));rgb=ImageStat.Stat(roi).median
    state['openSkyPatch']={'medianRGB':rgb,'blueMinusRed':rgb[2]-rgb[0],'luma':sum(v*w for v,w in zip(rgb,[.2126,.7152,.0722])),'patchCss':[265,183,309,229]}
    rows.append(state);report['runs']=[*report['runs'][:(0 if mode=='cold' else 1)],{'name':mode,'frames':rows}];save()
   if not a.v1:frame.wait_for_function("window.realSkyState?.().status==='ready'",timeout=45000)
   final=frame.evaluate(SNAP);(page if a.direct else page.locator('iframe')).screenshot(path=a.out/f'{mode}-final.png')
   if a.layers and mode=='cold':
    selectors=['.atmo .suncorner','.atmo .sun','.atmo .scatter','.atmo .sunhalo','.atmo .sundogs','.atmo .sunpillar','.wfx .godray','.wfx .sunbody','.wfx .sunhaze','.wfx .veil','.wfx .fog','.climate','.grain','.scrim','.real-sky-canvas']
    audit=frame.evaluate("""ss=>({accepted:SalahNativeSkyHost.capture(),physical:realSkyState().last,terms:ss.map(s=>{const e=document.querySelector(s);if(!e)return {selector:s};const c=getComputedStyle(e),r=e.getBoundingClientRect(),p=document.querySelector('.c').getBoundingClientRect();return {selector:s,display:c.display,visibility:c.visibility,opacity:c.opacity,background:c.background,filter:c.filter,blend:c.mixBlendMode,transform:c.transform,z:c.zIndex,rect:{x:r.x-p.x,y:r.y-p.y,width:r.width,height:r.height}};})})""",selectors)
    (a.out/'glow-layer-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    for i,sel in enumerate(selectors):
     style=frame.add_style_tag(content=sel+'{visibility:hidden!important}')
     (page if a.direct else page.locator('iframe')).screenshot(path=a.out/f'glow-without-{i:02}.png')
     style.evaluate('(e)=>e.remove()')
    frame.evaluate("""async()=>{const f=realSkyFrame(),m=await import('./real-sky/native-encoding.mjs');const c=document.createElement('canvas');c.width=325;c.height=530;c.id='diagnostic-field';c.style='position:absolute;inset:0;z-index:1000;width:100%;height:100%';document.querySelector('.c').append(c);c.getContext('2d').putImageData(new ImageData(m.encodeNativeFrame(f.raster.skyBackgroundLinear,f.raster.effectiveExposure),325,530),0,0);} """)
    (page if a.direct else page.locator('iframe')).screenshot(path=a.out/'glow-physical-field.png')
    frame.locator('#diagnostic-field').evaluate('(e)=>e.remove()')
   run=report['runs'][-1];run['final']=final;run['ownerTrace']=frame.evaluate('__startupOwners');run['paintEvents']=frame.evaluate('__firstPaint')
   # Diagnostic reference is evaluated after capture, so it cannot delay startup.
   states=[{'utcMs':x['utcMs'],'latDeg':28.5383,'lonDeg':-81.3792,'heightM':0} for x in rows]
   alt=frame.evaluate("async s=>{const m=await import('/salah_widget/real-sky/core/src/sky-state.mjs');return s.map(o=>m.physicalSkyState(o).sun.altDeg);}",states)
   for x,h in zip(rows,alt):x['acceptedSolarAltitudeReference']=h
   save();page.goto('about:blank')
  report['checks']={'noPageErrors':not report['errors'],'noLocalAssetFailures':not report['assetFailures'],'prayerReady':all(r['final']['prayerReady'] for r in report['runs'])}
  if a.scene in ['clear','partial']:
   report['checks']['daylightEveryVisibleFrame']=all(x['openSkyPatch']['medianRGB'][2]>=150 and x['openSkyPatch']['blueMinusRed']>=40 for r in report['runs'] for x in r['frames'] if x.get('accepted') and x['accepted'].get('sceneIdentity'))
  elif a.scene=='heavy':report['checks']['daylightEveryVisibleFrame']=all(x['openSkyPatch']['luma']>=90 for r in report['runs'] for x in r['frames'] if x.get('accepted') and x['accepted'].get('sceneIdentity'))
  report['status']='REFERENCE' if a.v1 else 'PASS' if all(report['checks'].values()) else 'FAIL';save();ctx.close();b.close()
 server.shutdown()
 frames=[Image.open(a.out/f'cold-{x}.png').convert('RGB').resize((330,534),Image.Resampling.LANCZOS) for x in [0,.25,.5,1,2,4,8]]
 sheet=Image.new('RGB',(330*len(frames),564),'#1a2335');draw=ImageDraw.Draw(sheet)
 for i,(im,t) in enumerate(zip(frames,[0,.25,.5,1,2,4,8])):sheet.paste(im,(330*i,30));draw.text((330*i+8,8),str(t)+' s target; actual time in receipt',fill='white')
 sheet.save(a.out/'startup-sequence.png');print(json.dumps({'status':report['status'],'checks':report['checks'],'out':str(a.out)},indent=2));return 1 if report['status']=='FAIL' else 0

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--scene',choices=SCENES,default='partial');p.add_argument('--dpr',type=float,default=1);p.add_argument('--v1',action='store_true');p.add_argument('--direct',action='store_true');p.add_argument('--layers',action='store_true');raise SystemExit(run(p.parse_args()))
