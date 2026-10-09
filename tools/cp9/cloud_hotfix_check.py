"""Actual Pages-shaped hotfix checks. Use installed browsers; explicit controlled fixtures.

Captures startup ownership, first progress hydration, bounded cloud colour and
atomic foreground rejection in root/iframe modes; keeps before failures.
Moon refinement is separately qualified by combined_entry_check.py.
"""
import argparse, base64, hashlib, http.server, json, shutil, sys, threading, time, traceback
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--browser',default='chromium');p.add_argument('--dpr',type=float,default=1);p.add_argument('--offset',type=float,default=0);p.add_argument('--night',action='store_true');p.add_argument('--direct',action='store_true');p.add_argument('--fonts',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.root/'tests'));sys.path.insert(0,str(a.root/'tools/cp9'))
from v1_browser import fonts, fixture, FONT_CSS, ROOT_KEY, SETTINGS
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity
shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out)
settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':2,'units':'imperial'}
hashpart='#local=1&simWx=2&simCloud=60&simPrecip=0&motion=full'+('&simMoon=.5&simWax=0&simMoonAlt=20&simMoonH=42' if a.night else '')
wrapper='<!doctype html><meta charset="utf-8"><body style="margin:8px;background:#1a2335"><iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="/salah_widget/'+hashpart+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden;position:relative;left:'+str(a.offset)+'px" scrolling="no"></iframe>'
class Server(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*x):pass
 def translate_path(self,path):return str(a.root/urlsplit(path).path.removeprefix('/salah_widget/'))
 def do_GET(self):
  if self.path=='/iframe':
   b=wrapper.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:super().do_GET()
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),Server);threading.Thread(target=srv.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{srv.server_port}'
state="""()=>{const c=document.querySelector('.c'),s=window.realSkyState?.(),style=q=>{const e=document.querySelector(q);return e?{visibility:getComputedStyle(e).visibility,display:getComputedStyle(e).display,opacity:getComputedStyle(e).opacity}:null};return {t:performance.now(),classes:c?.className,background:c&&getComputedStyle(c).background,sky:s?.status,skyRenders:s?.renders,cloud:style('.cloudcanvas'),grain:style('.grain'),climate:style('.climate'),bar:document.querySelector('.bar>i')?.style.width,barComputed:document.querySelector('.bar>i')&&getComputedStyle(document.querySelector('.bar>i')).width,prayer:window.qaState?.().cache?.prayerLoaded,moon:window.SalahMoonRuntime?.state?.status};}"""
report={'browser':a.browser,'dpr':a.dpr,'offset':a.offset,'night':a.night,'direct':a.direct,'runtime':runtime_identity(a.root),'harnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixture':'Orlando substitute; controlled Oct7 time/providers/fonts; real timers, motion enabled; routed reload is NOT an HTTP-cache-warm timing claim','errors':[],'warnings':[],'assetFailures':[],'runs':[]}
def save():(a.out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
TEMPORAL="""async()=>{
 const transfer=HAS_TRANSFER?await import('./real-sky/native-cloud-transfer.mjs'):null;
 const reference=(b,c,a,E)=>{const s=c/255,d=s<=.04045?s/12.92:((s+.055)/1.055)**2.4,l=(-Math.expm1(-E*b))*(1-a)+d*a;return Math.round(255*(l<=.0031308?12.92*l:1.055*l**(1/2.4)-.055));};
 const E=12,encode=x=>{const l=-Math.expm1(-E*x);return Math.round(255*(l<=.0031308?12.92*l:1.055*l**(1/2.4)-.055));};
 let previous=null,oldStep=0,newStep=0,changedSamples=0,referenceError=0,samples=[];
 for(let n=0;n<32;n++){
  const c=__capture.capture(183).cloudRGBA,old=new Uint8ClampedArray(c.length),fixed=new Uint8ClampedArray(c.length);
  for(let i=0;i<c.length;i+=4){const a=c[i+3]/255;if(a===0||a>.08)continue;
   for(let k=0;k<3;k++){const base=.0002,oc=encode(base*(1-a)+__comp.nativeInverseCode(c[i+k],E)*a),nc=transfer?encode(transfer.nativeCloudChannel(base,c[i+k],a,E)):oc,rc=reference(base,c[i+k],a,E);old[i+k]=oc;fixed[i+k]=nc;referenceError=Math.max(referenceError,Math.abs(nc-rc));
    if(previous&&previous.cloud[i+3]>0&&previous.cloud[i+3]/255<=.08){oldStep=Math.max(oldStep,Math.abs(oc-previous.old[i+k]));newStep=Math.max(newStep,Math.abs(nc-previous.fixed[i+k]));if(c[i+k]!==previous.cloud[i+k]||c[i+3]!==previous.cloud[i+3])changedSamples++;}
   }
  }
  samples.push({t:performance.now(),alpha:c.reduce((s,x,i)=>s+(i%4===3?x:0),0)});previous={cloud:c,old,fixed};await new Promise(r=>setTimeout(r,500));
 }
 return {oldStep,newStep,changedSamples,referenceError,samples,scope:'Same live native cloud captures replayed over fixed dark background; old inverse-HDR vs corrected display transfer; <=8% alpha edge pixels, real 1x motion'};
}"""
TEMPORAL=TEMPORAL.replace('HAS_TRANSFER',str((a.root/'real-sky/native-cloud-transfer.mjs').is_file()).lower())
with sync_playwright() as pw:
 b=launch_browser(pw);report['browserIdentity']=browser_identity(b);assert report['browserIdentity']['family']==a.browser
 c=b.new_context(viewport={'width':390,'height':600},device_scale_factor=a.dpr,timezone_id='America/New_York',reduced_motion='no-preference')
 def route(r):
  u=r.request.url
  if u.startswith(origin):r.continue_()
  elif u in ff:r.fulfill(body=ff[u].read_bytes(),content_type='text/css' if u==FONT_CSS else 'font/woff2',headers={'Access-Control-Allow-Origin':'*'})
  else:
   v=fixture(u,a.night)
   if urlsplit(u).hostname=='api.aladhan.com':
    date=urlsplit(u).path.rstrip('/').split('/')[-1];d,m,y=date.split('-');v['data']['date']['gregorian'].update(date=date,day=d,month={'number':int(m)},year=y);v['data']['meta']['timezone']='America/New_York';v['data']['timings'].update(Fajr='06:21',Sunrise='07:26',Dhuhr='13:17',Asr='16:38',Maghrib='19:08',Sunset='19:08',Isha='20:13')
   r.fulfill(json=v,headers={'Access-Control-Allow-Origin':'*'})
 c.route('**/*',route)
 c.add_init_script("""(()=>{window.__startup=[];const start=performance.now();function sample(source='frame'){const card=document.querySelector('.c'),bar=document.querySelector('.bar>i');if(card){const cs=getComputedStyle(card),grain=document.querySelector('.grain'),weather=document.querySelector('.cloudcanvas');window.__startup.push({source,t:performance.now(),background:cs.backgroundImage,grain:grain&&getComputedStyle(grain).display,grainVisibility:grain&&getComputedStyle(grain).visibility,cloud:weather&&getComputedStyle(weather).visibility,sky:window.realSkyState?.().status,width:bar?.style.width,actual:bar?.getBoundingClientRect().width,total:bar?.parentElement.getBoundingClientRect().width});}if(source==='frame'&&performance.now()-start<10000)requestAnimationFrame(()=>sample('frame'));}requestAnimationFrame(()=>sample('frame'));document.addEventListener('DOMContentLoaded',()=>requestAnimationFrame(()=>sample('frame')),{once:true});const timer=setInterval(()=>{sample('timer');if(performance.now()-start>=10000)clearInterval(timer);},25);})();""")
 c.add_init_script('if(location.protocol==="http:")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
 c.add_init_script("(()=>{const D=Date,s=performance.now(),t=D.parse('"+('2026-10-08T03:30:00Z' if a.night else '2026-10-07T15:09:00Z')+"');window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+performance.now()-s]));}static now(){return t+performance.now()-s;}};})();")
 q=c.new_page();q.on('pageerror',lambda e:report['errors'].append(str(e)));q.on('console',lambda e:report['warnings'].append(e.text) if e.type in ['warning','error'] else None)
 q.on('response',lambda r:report['assetFailures'].append([r.url,r.status]) if r.url.startswith(origin) and r.status>=400 else None)
 for run in ['cold','warm']:
  t=time.monotonic();q.goto(origin+('/salah_widget/'+hashpart if a.direct else '/iframe'),wait_until='commit');f=q.main_frame if a.direct else q.frame_locator('iframe');seq=[]
  for target in [.1,.25,.5,1,1.5,2,3,4,6,8]:
   q.wait_for_timeout(max(1,(target-(time.monotonic()-t))*1000));frame=q.main_frame if a.direct else next((x for x in q.frames if '/salah_widget/' in x.url),None)
   if not frame:continue
   snap=frame.evaluate(state);snap['elapsed']=time.monotonic()-t;seq.append(snap);q.screenshot(path=a.out/f'{run}-{target}.png')
  report['runs'].append({'name':run,'timeline':seq,'paintTimeline':frame.evaluate('__startup')});save()
  if run=='warm':break
  q.goto('about:blank')
 f=q.main_frame if a.direct else q.frames[1];f.wait_for_function("realSkyState().status==='ready'",timeout=90000,polling=100)
 f.evaluate("async()=>{window.__comp=await import('./real-sky/native-composition.mjs');window.__contract=await import('./real-sky/native-contract.mjs');window.__capture=new __comp.NativeForegroundCapture(document.querySelector('.real-sky-canvas'));}")
 metrics=f.evaluate("""()=>{SalahRealSky.compose();const capture=__capture.capture(),rgba=capture.cloudRGBA,r=realSkyFrame().raster,E=r.effectiveExposure,cv=document.querySelector('.real-sky-canvas'),actual=cv.getContext('2d').getImageData(0,0,325,530).data;let low=0,sat=0,maxError=0,edges=[];const tmp=document.createElement('canvas');tmp.width=325;tmp.height=530;tmp.getContext('2d').putImageData(new ImageData(rgba,325,530),0,0);const image=tmp.toDataURL();const alt=new Uint8ClampedArray(actual),disc=document.querySelector('.moon-mask-disc'),mask=SalahMoonRuntime?.detailEnabled?null:(disc.classList.contains('mask-on')&&+getComputedStyle(disc).opacity!==0?__contract.nativeDiscMask(325,530,cv.getBoundingClientRect(),disc.getScreenCTM(),+disc.getAttribute('r')):null),base=__comp.nativeCalendarRegion(r,mask,530),inv=code=>{const s=code/255,l=s<=.04045?s/12.92:((s+.055)/1.055)**2.4;return -Math.log1p(-Math.min(1-1/131072,l))/E;};const linear=s=>s<=.04045?s/12.92:((s+.055)/1.055)**2.4,code=l=>Math.round(255*(l<=.0031308?12.92*l:1.055*l**(1/2.4)-.055));for(let i=0;i<325*530;i++){const alpha=rgba[4*i+3]/255;if(alpha>0&&alpha<.04){low++;if(Math.max(...rgba.slice(4*i,4*i+3))===255){sat++;if(edges.length<20)edges.push({xy:[i%325,Math.floor(i/325)],rgba:[...rgba.slice(4*i,4*i+4)],actual:[...actual.slice(4*i,4*i+4)]});}}for(let k=0;k<3;k++){const ma=capture.moonRGBA[4*i+3]/255,lunar=base[3*i+k]*(1-ma)+((r.skyBackgroundLinear??r.backgroundLinear)[3*i+k]+inv(capture.moonRGBA[4*i+k]))*ma,expected=code((-Math.expm1(-E*lunar))*(1-alpha)+linear(rgba[4*i+k]/255)*alpha);alt[4*i+k]=expected;if(alpha>0&&alpha<.04)maxError=Math.max(maxError,Math.abs(expected-actual[4*i+k]));}}tmp.getContext('2d').putImageData(new ImageData(alt,325,530),0,0);return {lowAlphaPixels:low,saturatedLowAlphaPixels:sat,maxEdgeDifferenceFromDisplayReference:maxError,edges,cloudPng:image,referencePng:tmp.toDataURL(),composition:realSkyState().last.composition,qa:qaState(),sky:realSkyState()};}""")
 for k in ['cloudPng','referencePng']:(a.out/(k+'.png')).write_bytes(base64.b64decode(metrics.pop(k).split(',')[1]))
 report['cloud']=metrics;save()
 # Actual time motion frames (not a cloud hash). Full screenshot plus raw composed canvas.
 motion=[]
 for i in range(16):
  q.screenshot(path=a.out/f'motion-{i:02}.png');data=f.evaluate("document.querySelector('.real-sky-canvas').toDataURL()");(a.out/f'canvas-{i:02}.png').write_bytes(base64.b64decode(data.split(',')[1]));motion.append(f.evaluate(state));q.wait_for_timeout(1000)
 report['motion']=motion
 report['cloudTemporal']=f.evaluate(TEMPORAL)
 # Transaction boundary: corrupt a captured foreground, not the worker/model.
 report['invalidCapture']=f.evaluate("""()=>{const cv=document.querySelector('.real-sky-canvas'),before=cv.toDataURL(),proto=CanvasRenderingContext2D.prototype,old=proto.getImageData,oldState=realSkyState();let injected=0;proto.getImageData=function(...a){if(!this.canvas.isConnected&&this.canvas.width===325){injected++;return {data:new Uint8ClampedArray(1)};}return old.apply(this,a);};try{SalahRealSky.compose();return {injected,retained:before===cv.toDataURL(),status:realSkyState().status,rejectionsBefore:oldState.presentationRejections??0,rejectionsAfter:realSkyState().presentationRejections??0};}finally{proto.getImageData=old;}}""")
 q.wait_for_timeout(600)
 report['checks']={
  # This only checks ownership, NOT first-paint appearance. H1 is qualified by
  # startup_video_check.py; the old background:none rule accepted a dark shell.
  'legacyLayersNotDuplicated':all((x['grain']=='none' or x['grainVisibility']=='hidden') and x['cloud']=='hidden' for run in report['runs'] for x in run['paintTimeline']),
  'progressHydratesWithoutLoadingSweep':all(abs(x['actual']-float(x['width'].strip('%'))/100*x['total'])<=1 for run in report['runs'] for x in run['paintTimeline'] if x['width']),
  'boundedCloudTransfer':metrics['maxEdgeDifferenceFromDisplayReference']<=1,
  'invalidCaptureRetainsGoodCurrentFrame':report['invalidCapture']['injected']>0 and report['invalidCapture']['retained'] and report['invalidCapture']['status']=='ready' and report['invalidCapture']['rejectionsAfter']>report['invalidCapture']['rejectionsBefore'],
  'recoversAfterBadCapture':f.evaluate("realSkyState().status==='ready'&&realSkyState().presentationDraws>0"),
  'noUnexpectedErrors':not report['errors'] and not report['assetFailures'],
  'runtimeUnchangedDuringTest':report['runtime']==runtime_identity(a.root),
 }
 # Firefox can throttle init-script rAF inside an iframe. Continuous DOM
 # observations plus actual compositor screenshots cover startup without
 # mistaking the harness callback count for a product rendering failure.
 report['checks']['startupObservationComplete']=all(len(run['paintTimeline'])>20 and run['paintTimeline'][-1]['t']-run['paintTimeline'][0]['t']>7000 and len(run['timeline'])>=6 and run['timeline'][0].get('sky')!='ready' for run in report['runs'])
 report['checks']['cloudMotion']=report['cloudTemporal']['changedSamples']>100
 report['checks']['edgeStability']=report['cloudTemporal']['newStep']<report['cloudTemporal']['oldStep']*.5 and report['cloudTemporal']['referenceError']<=1
 report['status']='PASS' if all(report['checks'].values()) else 'FAIL';save();c.close();b.close()
srv.shutdown()
names=[t for t in [.25,1,2,4,8] if (a.out/f'cold-{t}.png').exists()]
frames=[Image.open(a.out/f'cold-{t}.png').convert('RGB') for t in names]
sheet=Image.new('RGB',(390*len(frames),630),'#222222');d=ImageDraw.Draw(sheet)
for i,im in enumerate(frames):
 im=im.resize((390,600),Image.Resampling.LANCZOS);sheet.paste(im,(390*i,30));d.text((390*i+10,10),str(names[i])+' sec target (actual time in receipt)',fill='white')
sheet.save(a.out/'startup-sequence.png')
print(json.dumps({'out':str(a.out),'status':report['status'],'checks':report['checks'],'temporal':{k:v for k,v in report['cloudTemporal'].items() if k!='samples'}},indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
