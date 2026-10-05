#!/usr/bin/env python3
"""Actual-widget CP8 lifecycle/fault qualification, never a standalone sky viewer.

The browser loads the exact native index/bundles/assets as intercepted local
subresources. Only a <base> for their reserved test origin is inserted. Date,
provider, worker-fault and visibility controls are test instrumentation, not
product code. Every successful render is observed at the actual canvas sink.
"""
from pathlib import Path
import argparse,copy,hashlib,json,math,mimetypes,sys,time,traceback
from urllib.parse import urlparse
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT
def report_json(report):
 # Invalid-input controls can expose NaN prayer diagnostics through the browser
 # protocol. Preserve their location/value explicitly, without emitting invalid
 # JSON or changing the in-memory assertions or original acquired observation.
 nonfinite=[]
 def clean(value,path=''):
  if isinstance(value,dict):return {k:clean(v,path+'/'+str(k).replace('~','~0').replace('/','~1')) for k,v in value.items()}
  if isinstance(value,list):return [clean(v,path+'/'+str(i)) for i,v in enumerate(value)]
  if isinstance(value,float) and not math.isfinite(value):nonfinite.append({'pointer':path,'value':str(value)});return None
  return value
 result=clean(report)
 if nonfinite:result['serialization']={'nonFiniteObservations':nonfinite,'representation':'null at the original pointer; non-finite value retained here; assertions unchanged'}
 return json.dumps(result,indent=2,allow_nan=False)
CLOCK=INIT.replace("const NativeDate=Date,base=NativeDate.parse('2026-09-07T20:30:00Z');", "const NativeDate=Date;window.__testWall=NativeDate.parse('2026-09-07T20:30:00Z');")
CLOCK=CLOCK.replace('[base]','[window.__testWall]').replace('return base;','return window.__testWall;')
# Deliberately distinguish fixture calendar days; this is not an Islamic-calendar calculation.
CLOCK=CLOCK.replace("date:'25-03-1448',day:'25'", "date:String((+d%29)+1)+'-03-1448',day:String((+d%29)+1)")
INSTRUMENT=r'''(() => {
 window.__testHidden=false;
 Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__testHidden});
 Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>window.__testHidden?'hidden':'visible'});
 const ActualWorker=Worker;
 const ctl=window.__workerControl={mode:'normal',hold:false,held:[],instances:[],submissions:[],rawResults:0};
 window.Worker=class {
  constructor(url,options){
   if(ctl.mode==='constructor-failure')throw new Error('Controlled Worker constructor failure');
   const text='importScripts('+JSON.stringify(url)+');self.addEventListener("message",e=>{if(e.data.kind==="qa-uncaught-crash")setTimeout(()=>{throw new Error("Controlled actual worker exception")},0);});';
   this.testURL=URL.createObjectURL(new Blob([text],{type:'text/javascript'}));
   this.actual=new ActualWorker(this.testURL,options);this.terminated=false;ctl.instances.push(this);
   this.actual.onmessage=e=>{
    if(e.data?.kind==='ready'&&ctl.mode==='startup-hang')return;
    if(e.data?.kind==='result'){
     ctl.rawResults++;
     if(ctl.hold){ctl.held.push({owner:this,event:e});return;}
    }
    this.onmessage?.(e);
   };
   this.actual.onerror=e=>this.onerror?.(e);
   this.actual.onmessageerror=e=>this.onmessageerror?.(e);
  }
  postMessage(m){
   if(m.kind==='render'){
    ctl.submissions.push({utcMs:m.job.observer.utcMs,lat:m.job.observer.latDeg,generation:m.job.native.generation,epoch:m.job.native.lifecycleEpoch});
    if(ctl.mode==='post-failure')throw new Error('Controlled worker postMessage failure');
    if(ctl.mode==='render-hang')return;
   }
   this.actual.postMessage(m);
  }
  terminate(){this.terminated=true;this.actual.terminate();URL.revokeObjectURL(this.testURL);}
 };
 ctl.release=()=>{ctl.hold=false;const held=ctl.held.splice(0);for(const x of held)x.owner.onmessage?.(x.event);};
 ctl.crash=()=>ctl.instances.at(-1).actual.postMessage({kind:'qa-uncaught-crash'});
 ctl.messageError=()=>ctl.instances.at(-1).onmessageerror?.({});
 window.__skyPublishes=[];
 const put=CanvasRenderingContext2D.prototype.putImageData;
 let lastKey=null,nextCanvas=0;const canvasIds=new WeakMap();
 CanvasRenderingContext2D.prototype.putImageData=function(data,...rest){
  if(this.canvas.classList?.contains('real-sky-canvas')){
   if(!canvasIds.has(this.canvas))canvasIds.set(this.canvas,++nextCanvas);
   const canvasId=canvasIds.get(this.canvas),sky=window.realSkyState?.(),host=window.SalahNativeSkyHost?.capture(),key=canvasId+':'+sky?.renders+':'+sky?.last?.native?.lifecycleEpoch;
   if(sky?.status==='ready'&&key!==lastKey){
    lastKey=key;let hash=2166136261;for(let i=0;i<data.data.length;i++)hash=Math.imul(hash^data.data[i],16777619);
    window.__skyPublishes.push({canvasId,render:sky.renders,frame:sky.last?.utcMs,hostUTC:host.utcMs,frameLat:sky.last?.observer.latDeg,hostLat:host.lat,frameGeneration:sky.last?.native.generation,hostGeneration:host.generation,epoch:sky.last?.native.lifecycleEpoch,paused:host.paused,pixelHash:hash>>>0});
   }
  }
  return put.call(this,data,...rest);
 };
})();'''
SNAPSHOT=r'''() => {
 const s=window.realSkyState?.(),h=window.SalahNativeSkyHost?.capture(),q=window.qaState?.();
 return {sky:s?{status:s.status,reason:s.reason,renders:s.renders,errors:s.errors,lifecycle:s.lifecycle,last:s.last?{utcMs:s.last.utcMs,observer:s.last.observer,native:s.last.native,execution:s.last.execution,catalogue:s.last.catalogue,diffuseAsset:s.last.diffuseAsset,diffuseState:s.last.diffuseState,physicalState:s.last.physicalState,composition:s.last.composition}:null}:null,
 assets:window.SalahRealSkyAssets?.state,host:h,rows:document.querySelectorAll('.p').length,
 synthetic:document.querySelectorAll('.stars circle,.milkyway circle,.starglints line').length,
 visible:document.querySelector('.real-sky-canvas')?.style.visibility??'absent',canvasCount:document.querySelectorAll('.real-sky-canvas').length,
 pbr:document.querySelector('.mphoto')?.getAttribute('href')?.length??0,classes:document.querySelector('.c')?.className,
 next:document.querySelector('.nt')?.textContent,countdown:document.querySelector('.left')?.textContent,
 ce:document.querySelector('#ce')?.textContent,ah:document.querySelector('#ah')?.textContent,dateTruth:q?.dateTruth,
 prayerModel:typeof model==='function'?model():null,publishes:window.__skyPublishes,
 worker:{submissions:__workerControl.submissions,held:__workerControl.held.length,rawResults:__workerControl.rawResults,instances:__workerControl.instances.length}};
}'''
class Widget:
 def __init__(self,browser,root,out,name,asset='normal',worker='normal',live=False,wall=None,reduced='reduce',extra_hash=''):
  self.root=root;self.out=out;self.name=name;self.mode=asset;self.held=[];self.errors=[];self.requests=[];self.controls=[];self.checks=0
  self.context=browser.new_context(viewport={'width':430,'height':640},reduced_motion=reduced)
  self.page=self.context.new_page();self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.route('**/*',self.route)
  fragment='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simWx=2&simCloud=60&simPrecip=0&units=c&qa=1'
  fragment+=extra_hash
  if not live:fragment+='&simTime=23:30'
  self.page.evaluate('(s)=>location.hash=s',fragment);self.page.evaluate(CLOCK);self.page.evaluate(INSTRUMENT)
  if wall:self.page.evaluate('(t)=>window.__testWall=Date.parse(t)',wall)
  self.page.evaluate('(mode)=>__workerControl.mode=mode',worker)
  source=(root/'index.html').read_text(encoding='utf-8').replace('<head>','<head><base href="https://native.cp8.test/">',1)
  self.page.set_content(source,wait_until='domcontentloaded',timeout=60000)
 def route(self,r):
  u=urlparse(r.request.url);self.requests.append(r.request.url)
  # WebKit exposes local Blob-worker requests to this route; other engines do
  # not. They are the exact product/instrument bytes, not an external provider.
  # Aborting them as a foreign hostname fabricates a worker-startup failure.
  if u.scheme in ['blob','data']:r.continue_();return
  if u.hostname!='native.cp8.test':r.abort();return
  f=self.root/'.'/u.path.lstrip('/')
  if not f.is_file() or self.root.resolve() not in f.resolve().parents:r.fulfill(status=404,body='Missing fixture asset');return
  if u.path.endswith('native-data.js'):
   if self.mode=='slow':self.held.append(r);return
   if self.mode=='missing':r.fulfill(status=404,body='Controlled missing native data');return
   if self.mode=='empty':r.fulfill(status=200,content_type='text/javascript',body='/* controlled corrupt/no pack */');return
   if self.mode in ['catalogue-corrupt','manifest-corrupt','diffuse-corrupt','diffuse-missing']:
    text=f.read_text(encoding='utf-8');prefix='window.__SALAH_REAL_SKY_PACK__=';pack=json.loads(text[len(prefix):].strip().removesuffix(';'))
    if self.mode=='catalogue-corrupt':pack['catalogueText']=pack['catalogueText'].replace('"vmag":-1.44','"vmag":-1.45',1);assert pack['catalogueText']!=json.loads(text[len(prefix):].strip().removesuffix(';'))['catalogueText'],'Corruption must alter actual retained bytes'
    elif self.mode=='manifest-corrupt':pack['manifestText']=pack['manifestText']+' '
    elif self.mode=='diffuse-corrupt':pack['assetTexts']['128']=pack['assetTexts']['128']+' '
    else:pack['assetTexts']={}
    r.fulfill(content_type='text/javascript',body=prefix+json.dumps(pack,separators=(',',':'))+';');return
  r.fulfill(path=str(f),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
 def release_asset(self):
  routes=self.held[:];self.held.clear();self.mode='normal'
  for r in routes:
   try:r.fulfill(path=str(self.root/'real-sky/native-data.js'),content_type='text/javascript')
   except Exception:pass # Aborted obsolete request may already be closed; never treated as admission.
 def wait(self,expression,timeout=60000):self.page.wait_for_function(expression,timeout=timeout)
 def ready(self):self.wait("window.realSkyState?.().status==='ready'&&!!window.realSkyState().last")
 def proof_ui(self):
  self.wait("document.querySelectorAll('.p').length===6")
  self.page.locator('#ceDateButton').click();self.wait("document.querySelector('#dateDialog').open")
  self.page.locator('#dateClose').click();self.wait("!document.querySelector('#dateDialog').open");self.checks+=3
 def snap(self,label,screenshot=True):
  s=self.page.evaluate(SNAPSHOT);self.check(s['rows']==6,label+': six prayer rows');self.check(s['synthetic']==0,label+': no synthetic stars')
  for p in s['publishes']:
   self.check(p['frameLat']==p['hostLat'] and p['frameGeneration']==p['hostGeneration'] and abs(p['frame']-p['hostUTC'])<=30000 and not p['paused'],label+': sink is current')
  if screenshot:self.page.locator('.c').screenshot(path=str(self.out/(self.name+'--'+label+'.png')))
  self.controls.append({'name':label,**s});return s
 def check(self,condition,description):
  self.checks+=1
  if not condition:raise AssertionError(description)
 def request(self):self.page.evaluate('()=>{SalahRealSky.request(true);}')
 def hold_job(self):
  self.page.evaluate('()=>{__workerControl.hold=true;SalahRealSky.request(true);}')
  self.wait('__workerControl.held.length>0')
 def release_job(self):self.page.evaluate('()=>__workerControl.release()')
 def target(self,lat,lon,tz,label):
  self.page.evaluate("async (x)=>{window.__testTimezone=x.tz;await applyConfig({...CONFIG,...x},{save:false});SalahRealSky.request(true);}",{'lat':lat,'lon':lon,'tz':tz,'label':label})
 def finish(self,error=None):
  result={'name':self.name,'passed':error is None and not self.errors,'assertions':self.checks,'error':error,'pageErrors':self.errors,'controls':self.controls,'requests':self.requests}
  for route in self.held:
   try:route.abort()
   except Exception:pass
  self.held.clear();self.page.unroute_all(behavior='ignoreErrors');self.context.close();return result

def run(root,out,group='all'):
 out.mkdir(parents=True,exist_ok=True);results=[]
 runtime_files=['index.html','config.js','real-sky/native-sky.js','real-sky/native-worker.js','real-sky/native-data.js','real-sky/native-sky.css']
 runtime_hashes={n:hashlib.sha256((root/'.'/n).read_bytes()).hexdigest() for n in runtime_files}
 with sync_playwright() as p:
  browser=launch_browser(p)
  def case(name,body,**options):
   w=None;start=time.monotonic()
   try:
    w=Widget(browser,root,out,name,**options);body(w);result=w.finish()
   except Exception:
    error=traceback.format_exc()
    if w:
     try:w.snap('failure')
     except Exception:pass
     result=w.finish(error)
    else:result={'name':name,'passed':False,'error':error,'assertions':0,'pageErrors':[]}
   result['seconds']=time.monotonic()-start;results.append(result)
   (out/'results.json').write_text(report_json({'status':'RUNNING','cases':results}),encoding='utf-8');print(name,'PASS' if result['passed'] else 'FAIL',round(result['seconds'],2),'s',flush=True)
   if not result['passed']:print(result.get('error') or result['pageErrors'],flush=True)
  if group in ['all','assets']:
   def slow(w):
    w.wait("window.SalahRealSkyAssets?.state.status==='loading'");w.proof_ui();s=w.snap('loading-prayer-usable');w.check(s['visible']!='visible','No sky before bytes');w.release_asset();w.ready();w.snap('recovered')
   case('slow-assets',slow,asset='slow')
   def retry(w):
    w.wait("window.realSkyState?.().status==='unavailable'");w.proof_ui();s=w.snap('unavailable-prayer-usable');w.check(s['visible']!='visible','No failed source light');w.mode='normal';w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();s=w.snap('recovered');w.check(s['canvasCount']==1,'One renderer after retry');w.check(s['sky']['last']['catalogue']['emitters']==8884,'Recovered admitted catalogue')
   for mode in ['missing','empty','catalogue-corrupt','manifest-corrupt']:case(mode,retry,asset=mode)
   def diffuse(w):
    w.ready();w.proof_ui();s=w.snap('explicit-fallback');w.check(s['sky']['last']['diffuseAsset']['mode']=='cp6-fallback','Diffuse fault is explicitly labelled');w.check(s['sky']['last']['utcMs']==s['host']['utcMs'],'Fallback is fresh accepted UTC');w.mode='normal';w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();s=w.snap('recovered');w.check(s['sky']['last']['diffuseAsset']['mode']!='cp6-fallback','Real map restored')
   for mode in ['diffuse-missing','diffuse-corrupt']:case(mode,diffuse,asset=mode)
   def obsolete_asset(w):
    w.wait("window.SalahRealSkyAssets?.state.status==='loading'");w.proof_ui();w.mode='normal';w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();a=w.snap('new-load-ready');w.release_asset();w.page.wait_for_timeout(150);b=w.snap('obsolete-load-released');w.check(b['canvasCount']==1,'Obsolete script cannot install second renderer');w.check(b['assets']['generation']==a['assets']['generation'],'Obsolete completion does not replace current asset generation')
   case('obsolete-asset-completion',obsolete_asset,asset='slow')
   def timeout(w):
    w.proof_ui();w.wait("window.SalahRealSkyAssets?.state.status==='unavailable'",timeout=30000);s=w.snap('deadline');w.check('timeout' in s['assets']['error'].lower(),'Declared asset deadline fired');w.mode='normal';w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();w.snap('deadline-recovery')
   case('asset-timeout',timeout,asset='slow')
  if group in ['all','worker']:
   def fallback(w):
    w.proof_ui();w.wait("realSkyState()?.status==='unavailable'");s=w.snap('worker-unavailable');w.check(s['sky']['last'] is None and s['visible']!='visible','Worker loss withdraws light and frame authority');w.check(any('withdrawn to preserve prayer responsiveness' in e for e in s['sky']['errors']),'Explicit worker withdrawal reason retained');w.proof_ui();w.page.evaluate("()=>{__workerControl.mode='normal';SalahRealSkyAssets.retry();}");w.ready();s=w.snap('worker-restarted');w.check(s['sky']['last']['execution']['mode']=='worker','Explicit restart restores worker')
   for mode in ['constructor-failure','startup-hang','post-failure','render-hang']:case(mode,fallback,worker=mode)
   def crash(w):
    w.ready();w.hold_job();w.page.evaluate('()=>__workerControl.crash()');w.wait("realSkyState()?.status==='unavailable'");s=w.snap('actual-exception-withdrawal');w.check(s['sky']['last'] is None and s['visible']!='visible','Crash clears sky rather than synchronous rendering');count=s['sky']['renders'];w.release_job();w.page.wait_for_timeout(200);s=w.snap('obsolete-worker-message');w.check(s['sky']['renders']==count and s['sky']['last'] is None,'Terminated-worker late result ignored');w.proof_ui();w.page.evaluate("()=>{SalahRealSkyAssets.retry();}");w.ready();w.snap('actual-exception-restarted')
   case('actual-worker-crash',crash)
   def decode(w):
    w.ready();w.hold_job();w.page.evaluate('()=>__workerControl.messageError()');w.wait("realSkyState()?.status==='unavailable'");w.release_job();s=w.snap('message-error-withdrawal');w.check(s['sky']['last'] is None and s['visible']!='visible','Decode failure does not admit obsolete light');w.proof_ui();w.page.evaluate("()=>{SalahRealSkyAssets.retry();}");w.ready();w.snap('message-error-restarted')
   case('worker-message-error',decode)
  if group in ['all','temporal']:
   def temporal(w):
    w.ready();w.proof_ui();w.snap('initial')
    w.hold_job();w.target(28.5383,-81.3792,'America/New_York','Florida');s=w.snap('A-to-B-pending');w.check(s['visible']!='visible','A withdrawn while B pending');w.release_job();w.ready();s=w.snap('B-ready');w.check(s['sky']['last']['observer']['latDeg']==28.5383,'Accepted B')
    w.hold_job();w.target(24.47,39.61,'Asia/Riyadh','A-intermediate');w.target(28.5383,-81.3792,'America/New_York','B-return');gen=w.page.evaluate('_runtimeGeneration');w.release_job();w.ready();s=w.snap('B-to-A-to-B-ready');w.check(s['sky']['last']['native']['generation']==gen,'Only latest repeated location accepted')
    w.hold_job();before=w.page.evaluate('simNow()');w.page.evaluate('()=>{_simBase+=30000;render();SalahRealSky.request(true);}');s=w.snap('forward-seek-pending');w.check(s['visible']!='visible','Seek withdraws old sky');w.release_job();w.ready();s=w.snap('forward-seek-ready');w.check(s['sky']['last']['utcMs']==before+30000,'Small explicit seek exact')
    w.hold_job();w.page.evaluate('()=>{_simBase-=2*86400000;render();SalahRealSky.request(true);}');w.release_job();w.ready();w.snap('backward-two-day-seek')
    w.hold_job();w.target(28.5383,-81.3792,'UTC','Timezone-only');w.release_job();w.ready();s=w.snap('timezone-only');w.check(s['host']['tz']=='UTC','Accepted timezone');w.check('UTC' in s['sky']['last']['native']['sceneIdentity'],'Timezone joins accepted identity')
    w.hold_job();w.page.evaluate("()=>{__testHidden=true;document.dispatchEvent(new Event('visibilitychange'));SalahRealSky.request(true);}");w.release_job();w.wait("realSkyState().lifecycle.paused");s=w.snap('hidden-completion');w.check(s['visible']!='visible','Hidden completion does not paint');w.page.evaluate("()=>{_simBase+=3600000;__testHidden=false;document.dispatchEvent(new Event('visibilitychange'));}");w.ready();s=w.snap('visible-current');w.check(s['sky']['last']['utcMs']==s['host']['utcMs'],'Resume not previous-time wallpaper')
    w.hold_job();w.page.evaluate('()=>{window.__restoreLat=lat;lat=null;SalahRealSky.request(true);}');w.release_job();w.wait("realSkyState().status==='unavailable'");s=w.snap('invalid-late-completion');w.check(s['sky']['last'] is None and s['visible']!='visible','Invalid source clears diagnostics and light');w.page.evaluate('()=>{lat=__restoreLat;SalahRealSky.request(true);}');w.ready();w.snap('valid-again')
    w.hold_job();w.page.evaluate('()=>SalahRealSky.dispose()');w.release_job();w.page.wait_for_timeout(150);s=w.snap('disposed');w.check(s['canvasCount']==0 and s['sky']['status']=='disposed','Dispose cannot resurrect');w.proof_ui();w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();w.snap('explicit-restart')
   case('native-target-lifecycle',temporal)
   def wall(w):
    w.ready();w.hold_job();base=w.page.evaluate('__testWall');w.page.evaluate('()=>{__testWall+=120000;render();}');w.release_job();w.wait(f"realSkyState()?.last?.utcMs==={base+120000}");s=w.snap('wall-forward');w.check(s['sky']['last']['utcMs']==s['host']['utcMs'],'Wall correction uses current host UTC');w.hold_job();w.page.evaluate('()=>{__testWall-=30000;render();}');w.release_job();w.wait(f"realSkyState()?.last?.utcMs==={base+90000}");w.snap('wall-backward');w.proof_ui()
    w.page.emulate_media(reduced_motion='no-preference');w.page.evaluate('()=>{__testWall+=2000;render();SalahRealSky.request(true);}');w.wait("realSkyState()?.status==='ready'&&!SalahNativeSkyHost.capture().reducedMotion");a=w.snap('full-motion');w.page.emulate_media(reduced_motion='reduce');w.page.evaluate('()=>{__testWall+=2000;render();SalahRealSky.request(true);}');w.wait("realSkyState()?.status==='ready'&&SalahNativeSkyHost.capture().reducedMotion");b=w.snap('reduced-motion');w.check(b['sky']['last']['utcMs']>a['sky']['last']['utcMs'],'Reduced motion did not freeze astronomy')
   case('wall-clock-and-reduced-motion',wall,live=True)
  if group in ['all','prayer']:
   def calendar(w):
    w.ready();w.proof_ui()
    w.page.evaluate("()=>{_simBase=Date.parse('2026-09-07T15:32:59Z');render();SalahRealSky.request(true);}");w.ready()
    a=w.snap('before-maghrib');w.check(a['dateTruth']['beforeOrAfterMaghrib']=='before' and a['dateTruth']['selectedSource']=='today','Before sunset uses current provider calendar');w.check(a['prayerModel']['nextKey']=='Maghrib','Next prayer before Maghrib')
    w.page.evaluate('()=>{_simBase+=1000;render();SalahRealSky.request(true);}');w.ready();w.wait("qaState().dateTruth.maghribRollApplied")
    b=w.snap('at-maghrib');w.check(b['dateTruth']['selectedSource']=='tomorrow' and b['dateTruth']['selectedGregorianDay']=='08-09-2026','At Maghrib adopts next provider calendar');w.check(b['dateTruth']['gregorianText']==a['dateTruth']['gregorianText'] and b['dateTruth']['hijriText']!=a['dateTruth']['hijriText'],'Only selected Hijri source advances at sunset');w.check(b['prayerModel']['currentKey']=='Maghrib' and b['prayerModel']['nextKey']=='Isha','Prayer transition at Maghrib')
    remaining=b['prayerModel']['leftMin'];w.hold_job();w.page.evaluate('()=>{_simBase+=1000;render();SalahRealSky.request(true);}');c=w.snap('countdown-with-sky-pending');w.check(abs(c['prayerModel']['leftMin']-(remaining-1/60))<1e-8,'Countdown advances one second while sky execution is held');w.release_job();w.ready()
    w.page.evaluate("()=>{_simBase=Date.parse('2026-09-07T20:59:59Z');render();SalahRealSky.request(true);}");w.ready();d=w.snap('before-midnight');w.check(d['dateTruth']['requestedGregorianDay']=='07-09-2026','Current local day before midnight')
    w.hold_job();w.page.evaluate('()=>{_simBase+=2000;render();SalahRealSky.request(true);}');w.release_job();w.wait("qaState().dateTruth.loadedGregorianDay==='08-09-2026'&&qaState().dateTruth.requestedGregorianDay==='08-09-2026'");w.ready();e=w.snap('after-midnight');w.check(e['dateTruth']['gregorianText']=='2026-09-08','Native day rollover');w.check(e['dateTruth']['hijriText']==b['dateTruth']['hijriText'],'Midnight does not advance the Hijri day twice');w.check(e['sky']['last']['utcMs']==e['prayerModel']['nowEpoch'],'Sky and prayer use same accepted rollover UTC');w.proof_ui()
   case('native-prayer-calendar-clock',calendar)
   def settings(w):
    w.wait("window.realSkyState?.().status==='unavailable'");w.proof_ui();w.page.locator('.buckle').click();w.wait("document.querySelector('.c').classList.contains('settings-open')")
    w.page.locator('#set-units').select_option('f');w.page.locator('#set-method').select_option('2');w.page.locator('#set-appearance').select_option('contrast');w.page.locator('.c').screenshot(path=str(out/(w.name+'--settings.png')))
    w.page.locator('#setClose').click();w.wait("!document.querySelector('.c').classList.contains('settings-open')&&CONFIG.units==='f'&&CONFIG.method==='2'")
    w.proof_ui();a=w.snap('saved-with-sky-unavailable');saved=w.page.evaluate('()=>JSON.parse(localStorage.getItem(SalahConfig.KEY))');w.check(saved['units']=='f' and saved['method']=='2' and saved['appearance']=='contrast','Actual settings save independent of optional sky');w.check(a['sky']['status']=='unavailable','Failed asset remains explicit')
    generation=a['host']['generation'];w.mode='normal';w.page.evaluate('()=>{SalahRealSkyAssets.retry();}');w.ready();b=w.snap('sky-restored-after-settings');w.check(b['sky']['last']['native']['generation']==generation,'Restored sky uses current settings generation');w.check(b['host']['units']=='f' and b['rows']==6,'Restored units and prayer UI');w.proof_ui()
   case('native-settings-with-asset-failure',settings,asset='missing',extra_hash='&preferLocal=1')
  browser.close()
 assert runtime_hashes=={n:hashlib.sha256((root/'.'/n).read_bytes()).hexdigest() for n in runtime_files},'Runtime changed during browser qualification'
 result={'runtimeSha256':runtime_hashes,'testHarnessSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'PASS' if results and all(c['passed'] for c in results) else 'FAIL','group':group,'assertions':sum(c['assertions'] for c in results),'cases':results,'sourceSha256':hashlib.sha256((root/'index.html').read_bytes()).hexdigest(),'harness':'Actual native index, config, native bundle, local data and real Blob worker; reserved-origin intercepted subresources. Controlled prayer/calendar dates. Worker exception is actual worker-thread exception; held messages/messageerror and visibility are explicit fault/event controls. No live provider or OS/browser-hidden-state certification.'}
 (out/'results.json').write_text(report_json(result),encoding='utf-8');print('LIFECYCLE',result['status'],len(results),'cases',result['assertions'],'assertions',flush=True);return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);a.add_argument('--group',choices=['all','assets','worker','temporal','prayer'],default='all');x=a.parse_args();sys.exit(0 if run(x.root.resolve(),x.output,x.group)['status']=='PASS' else 1)
