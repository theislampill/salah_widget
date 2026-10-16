"""Bounded delivered-consumer readback, not repeated timing/visual qualification."""
from pathlib import Path
import ast,asyncio,datetime,hashlib,importlib.util,json,os,sys,time,types
from urllib.parse import urlsplit,parse_qs
from playwright.async_api import async_playwright
D=Path(__file__).resolve().parent;O=D.parent;R=Path('C:/Users/theis/.codex/worktrees/r0022-execution/salah_widget');M='f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de';URL='https://theislampill.github.io/salah_widget/'
sys.path.insert(0,str(R/'tools/cp9'));sys.path.insert(0,str(R/'tests'))
from browser_runtime import launch_browser,browser_identity
from v1_browser import fixture,SETTINGS,ROOT_KEY
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
READOUT=r'''()=>{
 const box=e=>{if(!e)return null;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,visibility:s.visibility,opacity:s.opacity};};
 const stats=a=>{if(!a)return null;let positive=0,sum=0,max=0,nonfinite=0;for(const v of a){if(!Number.isFinite(v))nonfinite++;if(v>0)positive++;sum+=v;max=Math.max(max,v);}return {length:a.length,positive,sum,max,nonfinite};};
 const per=r=>r?{physical:r.physicalState,exposure:r.effectiveExposure,lunar:r.lunarDisplayPresentation??null,raw:stats(r.lunarBackgroundLinear),mapped:stats(r.lunarNightDisplayLinear),rawSky:stats(r.physicalSkyBackgroundLinear),stellar:stats(r.stellarLinear),diffuse:stats(r.diffuseLinear),drawn:r.drawn}:null;
 const sky=window.realSkyState?.();return {url:location.href,at:performance.now(),date:Date.now(),native:window.SalahNativeSkyHost?.capture(false),sky,moon:window.SalahMoonRuntime?.state,qa:window.qaState?.(),display:{refined:per(window.realSkyFrame?.()?.raster),preview:per(window.SalahSkyPreview?.frame?.raster)},card:box(document.querySelector('.c')),detail:box(document.querySelector('.moon-detail-canvas')),prayerRows:[...document.querySelectorAll('.times .p')].map(e=>e.textContent),weatherInformation:document.querySelector('#weather-information')?.textContent,classes:document.querySelector('.c')?.className};
}'''
async def main():
 expected=read(O/'selected-r7/RUNTIME.json');served=read(D/'served-runtime.json');assert served['allMatch']and served['merge']==M
 review=read(D/'CONSUMER-METHOD-REVIEW.json');assert review['status']=='ACCEPTED_BOUNDED_DELIVERY_METHOD'and review['scriptSha256']==sha(Path(__file__))
 # Reuse the exact accepted provider function; product bytes are never fulfilled locally.
 adapter=O/'qualification/capture_qualified_r2.py';tree=ast.parse(adapter.read_text(encoding='utf-8'));provider_node=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='provider')
 out=D/'native';assert not out.exists();out.mkdir()
 assert read(O/'browser-lease.json')['status']=='FREE'and not(O/'native-resource.lock').exists()
 assert read(Path('C:/Users/theis/Documents/Codex/salah-rlgwo-execution-20261009/ACTIVE_LEDGER.json'))['resourceLeases']['heavy-browser']['status']=='FREE'
 assert read(Path('C:/Users/theis/.codex/work-products/r0024-execution-20261015/execution.json'))['heavyLease']['kind']=='FREE'
 lock=O/'native-resource.lock';lock.write_text('r0022-delivered-consumers',encoding='utf-8');write(O/'browser-lease.json',{'status':'ACTIVE','owner':'R0022 root','leaseId':'r0022-delivered-consumers','scope':'Three serial actual Pages consumer cells; no performance/new temporal acceptance','startedAtUtc':now()})
 result={'schema':'r0022-delivered-native-consumers/v1','startedAtUtc':now(),'merge':M,'runtime':expected['treeSha256'],'scriptSha256':sha(Path(__file__)),'providerSourceSha256':sha(adapter),'scope':'Actual public HTTPS product. Only external providers and anchored real1x clock/settings are controlled. External Playwright routes disable cache: no performance/startup timing credit. Unstripped original PNG observations and final native state; no recording repair/every-paint/M0 claim. Fresh isolated managed test browser contexts; no personal Firefox access.','cells':[],'cleanup':False}
 all_owned_closed=True
 try:
  for engine,dpr,scene,duration in [('chromium',1,'clear',30),('firefox',2,'rain',60),('chromium',1,'day',15)]:
   cell=out/(engine+'-'+scene);cell.mkdir();cap=read(Path('C:/Users/theis/.codex/work-products/r0024-execution-20261015/native')/engine/('resume-r2'if engine=='chromium'else'resume-r6')/'results.json')['capability'];driver=cap['driver']
   assert sha(Path(cap['executable']))==cap['executableSha256']and sha(Path(driver['node']))==driver['nodeSha256']and sha(Path(driver['cli']))==driver['files']['cli.js']
   import playwright._impl._transport as transport
   transport.compute_driver_executable=lambda:(driver['node'],driver['cli'])
   os.environ['SALAH_BROWSER']=engine;os.environ['SALAH_BROWSER_EXECUTABLE']=cap['executable'];os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
   stamp='2026-09-25T17:00:00Z'if scene=='day'else'2026-09-25T02:00:00Z';wx,cloud=(63,65)if scene=='rain'else(0,0)
   ns={'fixture':fixture,'urlsplit':urlsplit,'parse_qs':parse_qs,'datetime':datetime.datetime,'timedelta':datetime.timedelta,'timezone':datetime.timezone,'time':time,'a':types.SimpleNamespace(scene=scene,prayer_delay=0,acquiring=False),'stamp':stamp,'wx':wx,'cloud':cloud}
   exec(compile(ast.Module(body=[provider_node],type_ignores=[]),str(adapter),'exec'),ns);provider=ns['provider']
   row={'engine':engine,'dpr':dpr,'scene':scene,'anchor':stamp,'declaredSeconds':duration,'capability':cap,'frames':[],'providerFixtures':[],'productResponses':[],'requestFailures':[],'pageErrors':[],'observationErrors':[]};tasks=[];closed=False
   async with async_playwright()as pw:
    all_owned_closed=False;browser=await launch_browser(pw);row['browser']=browser_identity(browser)
    try:
     ctx=await browser.new_context(viewport={'width':375,'height':800},device_scale_factor=dpr,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference')
     async def external(route):
      u=route.request.url;value=provider(u);row['providerFixtures'].append({'url':u,'value':value});await route.fulfill(status=200,content_type='application/json',body=json.dumps(value))
     for host in ['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']:await ctx.route('https://'+host+'/**',external)
     settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
     await ctx.add_init_script('if(location.origin==="https://theislampill.github.io")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');')
     clock=time.time()*1000;await ctx.add_init_script('(()=>{const D=Date,s='+str(clock)+',t=D.parse('+json.dumps(stamp)+');window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();')
     async def observe(response):
      u=urlsplit(response.url)
      if u.hostname!='theislampill.github.io'or not u.path.startswith('/salah_widget/'):return
      path=u.path[len('/salah_widget/'):]or'index.html'
      if path not in expected['files']:return
      try:
       body=await response.body();want=expected['files'][path];got=hashlib.sha256(body).hexdigest();row['productResponses'].append({'url':response.url,'path':path,'status':response.status,'bytes':len(body),'sha256':got,'match':response.status==200 and len(body)==want['bytes']and got==want['sha256']})
      except Exception as e:row['observationErrors'].append({'path':path,'error':repr(e)})
     ctx.on('response',lambda r:tasks.append(asyncio.create_task(observe(r))));ctx.on('requestfailed',lambda r:row['requestFailures'].append({'url':r.url,'failure':r.failure}))
     page=await ctx.new_page();page.on('pageerror',lambda e:row['pageErrors'].append(str(e)));start=time.monotonic()
     await page.goto(URL+'?r0022_delivery='+M+'#local=1&motion=full',wait_until='domcontentloaded',timeout=60000)
     for index,target in enumerate([1,5,duration]):
      await asyncio.sleep(max(0,target-(time.monotonic()-start)));before=time.monotonic();p=cell/f'original-{index:02}.png';await page.screenshot(path=str(p),type='png',timeout=30000);row['frames'].append({'path':p.name,'requestedSeconds':target,'startSeconds':before-start,'endSeconds':time.monotonic()-start,'sha256':sha(p)})
     row['final']=await page.evaluate(READOUT)
     # Real settings route, read only: verify the delivered dialog retains usable fields.
     await page.locator('.buckle').click();await page.screenshot(path=str(cell/'settings.png'),type='png');row['settings']={'visibleInputs':await page.locator('input:visible,select:visible').count(),'closeVisible':await page.locator('#setClose').is_visible()};await page.locator('#setClose').click()
     await asyncio.gather(*tasks);await ctx.close();await asyncio.gather(*tasks)
    finally:await browser.close();closed=True;all_owned_closed=True
   row['cleanup']=closed;f=row['final'];card=f.get('card')or{};native=f.get('native')or{};sky=f.get('sky')or{};composition=(sky.get('last')or{}).get('composition')or{};qa=f.get('qa')or{};moon=f.get('moon')or{};ref=f.get('display',{}).get('refined')or{}
   checks={'actualPublicDocument':f['url'].startswith(URL),'card325x530':card.get('width')==325 and card.get('height')==530,'nativeTarget':native.get('lat')==28.5383 and native.get('lon')==-81.3792 and native.get('generation')==0,'clock1x':native.get('timeScale')==1,'camera':native.get('camera')=={'azDeg':180,'altDeg':45,'fovYDeg':90,'rollDeg':0},'prayerReady':native.get('prayerReady')is True and len(f.get('prayerRows',[]))>=5,'weatherInformation':bool(f.get('weatherInformation')),'settingsRoute':row['settings']['closeVisible']and row['settings']['visibleInputs']>0,'actualDocumentAndBundleBytes':{'index.html','real-sky/native-sky.js','moon/moon-host.js'}.issubset({r['path']for r in row['productResponses']if r['match']}),'allObservedProductBytes':bool(row['productResponses'])and all(r['match']for r in row['productResponses']),'singleCloudApplication':composition.get('cloudApplications')==1,'noPageErrors':not row['pageErrors']}
   if scene!='day':checks.update(currentV5=moon.get('current')is True and not moon.get('legacyFallback')and(qa.get('moonTruth')or{}).get('surface',{}).get('status')=='v5-terrain',rawLunarPositive=(ref.get('raw')or{}).get('positive',0)>0,mappedLunarPositive=(ref.get('mapped')or{}).get('positive',0)>0)
   if scene=='rain':checks['cloudsActuallyComposed']=composition.get('meanCloudAlpha',0)>0
   row['checks']=checks;row['status']='OBSERVATIONS_FOR_INDEPENDENT_REVIEW'if all(checks.values())else'FAILED_RETAINED';write(cell/'result.json',row);result['cells'].append({'path':str(cell.relative_to(D)),'resultSha256':sha(cell/'result.json'),'status':row['status'],'checks':checks});write(out/'summary.json',result);print(json.dumps({'cell':cell.name,'status':row['status'],'checks':checks}),flush=True)
   assert all(checks.values()),'Retain failed delivery cell and investigate exact predicate'
  result['cleanup']=True;result['completedAtUtc']=now();write(out/'summary.json',result)
 finally:
  # async context/finally closes only this runner's owned browsers.
  write(O/'browser-lease.json',{'status':'FREE'if all_owned_closed else'RECOVERY_REQUIRED','owner':None if all_owned_closed else'R0022 root','leaseId':'r0022-delivered-consumers','finishedAtUtc':now(),'scope':'Owned async browser contexts closed'if all_owned_closed else'Owned browser closure unresolved; do not release lease'})
  if all_owned_closed:assert lock.read_text(encoding='utf-8')=='r0022-delivered-consumers';lock.unlink()
if __name__=='__main__':asyncio.run(main())
