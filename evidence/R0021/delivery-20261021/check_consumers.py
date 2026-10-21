"""Four serial delivered consumers; existing provider/readout/launcher owners, no timing claim."""
from pathlib import Path
import ast, asyncio, datetime, hashlib, json, os, sys, time, types
from urllib.parse import urlsplit, parse_qs

D=Path(__file__).resolve().parent; O=D.parent
R=Path(r'${REPO_ROOT}')
M='f71fef6ccf7e4efcb57b5a26688d2360461a3253'
URL='https://theislampill.github.io/salah_widget/'
RUNTIME='1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b'
NODE=Path(r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe')
EXES={'chromium':Path(r'${BROWSER_CACHE}\chromium-1223\chrome-win64\chrome.exe'),'firefox':Path(r'${BROWSER_CACHE}\firefox-1522\firefox\firefox.exe')}
BODY_PATHS={'index.html','config.js','real-sky/native-sky.css','real-sky/native-sky.js','real-sky/native-data.js','moon/moon-host.js'}
CASES=[('chromium-public-cloud','chromium','public','partial'),('firefox-public-night','firefox','public','clear'),('chromium-delivered-file','chromium','file','clear'),('firefox-delivered-offline','firefox','offline','clear')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,value):p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def pins():
 paths=[Path(__file__),R/'tools/cp9/celestial_startup_check.py',R/'tools/cp9/browser_runtime.py',R/'tools/cp9/chromium_startup_defaults.py',R/'tools/cp9/runtime_identity.py',R/'tests/v1_browser.py',O/'parent-tools-r129/tools/cp9/parent_controls_r125.py',O/'capture-driver/cli.js',O/'capture-driver/lib/coreBundle.js',NODE,*EXES.values()]
 return {str(p):sha(p) for p in paths}
def extract_provider():
 src=R/'tools/cp9/celestial_startup_check.py'
 return next(n for n in ast.walk(ast.parse(src.read_text(encoding='utf-8'))) if isinstance(n,ast.FunctionDef) and n.name=='provider')
def readout():
 src=O/'parent-tools-r129/tools/cp9/parent_controls_r125.py'
 node=next(n for n in ast.parse(src.read_text(encoding='utf-8')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STATE' for t in n.targets))
 return '()=>{'+ast.literal_eval(node.value)+'}'
def ready(s):
 moon=s.get('moon') or {}; sky=s.get('sky') or {};q=(moon.get('last') or {}).get('quality') or {}
 return moon.get('status')=='ready' and moon.get('current') is True and moon.get('visibleSource')=='refined-terrain' and not moon.get('pending') and sky.get('status')=='ready' and not (sky.get('lifecycle') or {}).get('pending') and q.get('status')=='empirical-adaptive' and q.get('projectedGate')==.5 and isinstance(q.get('projectedMaximumCode'),(int,float)) and q['projectedMaximumCode']<=.5 and q.get('unsettled')==0

async def main():
 from playwright.async_api import async_playwright
 import playwright._impl._transport as transport
 transport.compute_driver_executable=lambda:(str(NODE),str(O/'capture-driver/cli.js'))
 sys.path[:0]=[str(R/'tools/cp9'),str(R/'tests')]
 from browser_runtime import browser_options,browser_identity
 from chromium_startup_defaults import restore_options,verify_launch
 from runtime_identity import runtime_identity
 from v1_browser import fixture,SETTINGS,ROOT_KEY
 expected=json.loads((R/'docs/real-sky/evidence/r0021-terminal-20261021/r127/builds/integrated-r31-file-transport/RUNTIME.json').read_bytes())
 served=json.loads((D/'served-runtime.json').read_bytes())
 served_review=json.loads((D/'SERVED-RUNTIME-REVIEW.json').read_bytes())
 assert served_review['status']=='ACCEPTED_ACTUAL_142_FILE_RUNTIME_AND_PROTECTED_ENTRIES' and served_review['rawReceiptSha256']==sha(D/'served-runtime.json')
 assert served['merge']==M and served['observedRuntime']==RUNTIME and len(served['files'])==142 and all(x['match'] for x in served['files'])
 assert runtime_identity(D/'served')==expected
 method=json.loads((D/'CONSUMER-METHOD-REVIEW.json').read_bytes())
 assert method['status']=='ACCEPTED_BOUNDED_DELIVERY_CONSUMER_METHOD' and method['scriptSha256']==sha(Path(__file__))
 frozen=pins();assert method['inputPins']==frozen
 out=D/'native';assert not out.exists();out.mkdir()
 lock=O/'native-resource.lock'
 with lock.open('x',encoding='utf-8') as f:f.write('r0021-delivered-consumers')
 result={'schema':'r0021-delivered-native-consumers/v1','startedAtUtc':now(),'merge':M,'runtime':RUNTIME,'scope':'Delivered public HTTPS and exact downloaded file/offline bodies; only external providers and ordinary 1x clock anchor are controlled. Readout and PNG endpoints are not S1, cost, full-motion or uninterrupted-display proof. Actual-parent qualification transfers unchanged from r129; these are standalone delivery consumers. No personal browser/profile/desktop used.','inputPins':frozen,'cells':[],'cleanup':False}
 state_js=readout(); all_closed=True
 try:
  for name,engine,entry,scene in CASES:
   cell=out/name;cell.mkdir();tasks=[];browser=ctx=None;active=True;closed=False;response_listener=None
   row={'name':name,'engine':engine,'entry':entry,'scene':scene,'status':'ACQUIRING','errors':[],'pageErrors':[],'requestFailures':[],'productResponses':[],'productResponseMetadata':[],'observationErrors':[],'endpoints':{},'cleanup':{}}
   def record():save(cell/'result.json',row)
   stamp='2026-09-24T14:00:00Z' if scene=='partial' else '2026-09-25T02:00:00Z'
   wx,cloud=(2,35) if scene=='partial' else (0,0)
   ns={'fixture':fixture,'urlsplit':urlsplit,'parse_qs':parse_qs,'datetime':datetime.datetime,'timedelta':datetime.timedelta,'timezone':datetime.timezone,'time':time,'a':types.SimpleNamespace(scene='day' if scene=='partial' else 'clear',prayer_delay=0,acquiring=False),'stamp':stamp,'wx':wx,'cloud':cloud}
   exec(compile(ast.Module(body=[extract_provider()],type_ignores=[]),str(R/'tools/cp9/celestial_startup_check.py'),'exec'),ns);provider=ns['provider']
   settings={**SETTINGS,'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','label':'CENTRAL FL','method':'2','units':'c'}
   fragment='#local=1&lat=28.5383&lon=-81.3792&tz=America/New_York&label=CENTRAL%20FL&method=2&units=c&motion=full'
   url=URL+'?r0021_delivery='+M+fragment if entry=='public' else (D/'served'/('index.html' if entry=='file' else 'offline.html')).as_uri()+fragment
   row.update(url=url,anchor=stamp,syntheticWeather={'code':wx,'cloud':cloud},startedAtUtc=now());record()
   os.environ.update(SALAH_BROWSER=engine,SALAH_BROWSER_EXECUTABLE=str(EXES[engine]),PW_TEST_SCREENSHOT_NO_FONTS_READY='1')
   manager=async_playwright();entered=False;driver_exited=False;interrupted=False;all_closed=False
   try:
    pw=await asyncio.wait_for(manager.__aenter__(),timeout=30);entered=True
    try:
     async with asyncio.timeout(1800):
      all_closed=False
      family,options=browser_options()
      if engine=='chromium':options=restore_options(options)
      browser=await getattr(pw,family).launch(**options);row['browser']=browser_identity(browser)
      if engine=='chromium':
       cdp=await browser.new_browser_cdp_session()
       try:
        info=await cdp.send('SystemInfo.getInfo');verified=verify_launch(browser.version,info['commandLine']);row['renderDocumentDefault']={k:v for k,v in verified.items() if k!='commandLine'}
       finally:await cdp.detach()
      ctx=await browser.new_context(viewport={'width':390,'height':650},device_scale_factor=1,timezone_id='America/New_York',locale='en-US',reduced_motion='no-preference')
      async def external(route):
       value=provider(route.request.url)
       await route.fulfill(status=200,content_type='application/json',body=json.dumps(value),headers={'Access-Control-Allow-Origin':'*'})
      for host in ['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']:await ctx.route('https://'+host+'/**',external)
      await ctx.add_init_script('try{if(!localStorage.getItem('+json.dumps(ROOT_KEY)+'))localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(settings))+');}catch(e){}')
      clock=time.time()*1000
      await ctx.add_init_script('(()=>{const D=Date,s='+str(clock)+',t=D.parse('+json.dumps(stamp)+');window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();')
      async def observe(response):
       u=urlsplit(response.url)
       if u.hostname!='theislampill.github.io' or not u.path.startswith('/salah_widget/'):return
       path=u.path[len('/salah_widget/'):] or 'index.html'
       if path not in expected['files']:return
       meta={'path':path,'url':response.url,'status':response.status};row['productResponseMetadata'].append(meta)
       try:
        error=await response.finished();meta['finished']=error is None
        if error:raise RuntimeError(str(error))
        if path in BODY_PATHS:
         data=await response.body();want=expected['files'][path];got=hashlib.sha256(data).hexdigest()
         row['productResponses'].append({'path':path,'bytes':len(data),'sha256':got,'match':response.status==200 and len(data)==want['bytes'] and got==want['sha256']})
       except Exception as e:row['observationErrors'].append({'path':path,'error':repr(e)})
      if entry=='public':
       response_listener=lambda response:tasks.append(asyncio.create_task(observe(response)))
       ctx.on('response',response_listener)
      ctx.on('requestfailed',lambda request:row['requestFailures'].append({'url':request.url,'failure':request.failure}) if active else None)
      page=await ctx.new_page();page.on('pageerror',lambda e:row['pageErrors'].append(str(e)))
      await page.goto(url,wait_until='domcontentloaded',timeout=60000)
      async def endpoint(label,mode):
       deadline=time.monotonic()+360
       while time.monotonic()<deadline:
        if await page.locator('.c').count():
         state=await page.evaluate(state_js)
         if ready(state):break
         if (state.get('moon') or {}).get('status')=='unavailable' or (state.get('sky') or {}).get('status')=='unavailable':
          row['failedState']=state;raise RuntimeError('Delivered current refinement unavailable')
        await asyncio.sleep(1)
       else:raise TimeoutError('Delivered current refinement not admitted within360s observer ceiling')
       row['endpoints'][label]=state;record()
       assert state['mode']==mode and state['card']=={'width':325,'height':530} and len(state['rows'])==6
       assert state['native']['weather']['cloud']==cloud and state['weatherHeader']['temperature'] and state['weatherHeader']['icon'] not in ['', 'â€”']
       assert state['native']['lat']==28.5383 and state['native']['lon']==-81.3792
       await page.screenshot(path=str(cell/(label+'.png')),timeout=30000)
       return state
      first=await endpoint('glass-default','glass')
      if entry=='public':
       for mode in ['contrast','glass']:
        await page.locator('.buckle').click();await page.locator('#set-appearance').select_option(mode);await page.locator('#setClose').click();await asyncio.sleep(.3)
        state=await endpoint(mode+'-return',mode)
        assert all(state['native'][k]==first['native'][k] for k in ['lat','lon','tz','generation','weather']),'Mode changed unrelated native inputs'
       contrast=row['endpoints']['contrast-return'];glass=row['endpoints']['glass-return']
       assert any(a['opacity']!=b['opacity'] or a['background']!=b['background'] for a,b in zip(contrast['rows'],glass['rows'])),'Modes have identical effective row styles'
       await page.reload(wait_until='domcontentloaded');await endpoint('glass-reload','glass')
      if response_listener:ctx.remove_listener('response',response_listener)
      row['observationCutoffUtc']=now();frozen_tasks=tuple(tasks);row['observedResponseTasks']=len(frozen_tasks)
      if frozen_tasks:
       values=await asyncio.wait_for(asyncio.gather(*frozen_tasks,return_exceptions=True),timeout=30)
       for value in values:
        if isinstance(value,BaseException):row['observationErrors'].append({'error':repr(value)})
      relevant=[x for x in row['requestFailures'] if x['url'].startswith(URL)]
      assert not row['pageErrors'] and not row['observationErrors'] and not relevant
      if entry=='public':
       assert {'index.html','real-sky/native-sky.js','moon/moon-host.js'}.issubset({x['path'] for x in row['productResponses'] if x['match']})
       assert all(x['match'] for x in row['productResponses']) and all(x['status']==200 and x.get('finished') for x in row['productResponseMetadata'])
      row['status']='RETURNED_FOR_INDEPENDENT_REVIEW'
    except Exception as e:row['errors'].append({'atUtc':now(),'error':repr(e)});row['status']='FAILED_RETAINED'
    finally:
     active=False
     if ctx and response_listener:ctx.remove_listener('response',response_listener)
     for task in tasks:
      if not task.done():task.cancel()
     if tasks:
      try:await asyncio.wait_for(asyncio.gather(*tasks,return_exceptions=True),timeout=10)
      except BaseException as e:interrupted=True;row['cleanup']['observerDrainError']=repr(e)
     if ctx:
      try:await asyncio.wait_for(ctx.close(),timeout=30);row['cleanup']['contextClosed']=True
      except Exception as e:row['cleanup']['contextError']=repr(e)
     if browser:
      try:await asyncio.wait_for(browser.close(),timeout=30);row['cleanup']['browserClosed']=True;closed=True
      except Exception as e:row['cleanup']['browserError']=repr(e)
     # A failed launch without a returned browser handle leaves cleanup unknown.
     # Retain the lease for owned-process reconciliation rather than inventing closure.
     else:closed=False
   except BaseException as e:
    interrupted=True;row['errors'].append({'atUtc':now(),'outerError':repr(e)});row['status']='INTERRUPTED_RETAINED'
    raise
   finally:
    if entered:
     try:
      await asyncio.wait_for(manager.__aexit__(None,None,None),timeout=30);driver_exited=True;row['cleanup']['playwrightExited']=True
     except BaseException as e:interrupted=True;row['cleanup']['playwrightExitError']=repr(e)
    all_closed=closed and driver_exited and not interrupted
    row['cleanup']['verified']=all_closed
    row['retainedImages']=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(cell.glob('*.png'))]
    row['completedAtUtc']=now();record()
   result['cells'].append({'path':name,'status':row['status'],'resultSha256':sha(cell/'result.json')});save(out/'summary.json',result)
   print(json.dumps({'cell':name,'status':row['status'],'errors':row['errors']}),flush=True)
   if row['status']!='RETURNED_FOR_INDEPENDENT_REVIEW' or not all_closed:break
 finally:
  result.update(completedAtUtc=now(),cleanup=all_closed,inputsUnchanged=pins()==frozen,servedRuntimeUnchanged=runtime_identity(D/'served')==expected)
  if all_closed and lock.exists() and lock.read_text()=='r0021-delivered-consumers':lock.unlink()
  result['leaseAbsent']=not lock.exists();save(out/'summary.json',result)
 assert len(result['cells'])==4 and all(x['status']=='RETURNED_FOR_INDEPENDENT_REVIEW' for x in result['cells']) and result['cleanup'] and result['inputsUnchanged'] and result['servedRuntimeUnchanged'] and result['leaseAbsent']

if __name__=='__main__':
 if '--prepare' in sys.argv:save(D/'CONSUMER-INPUTS.json',{'scriptSha256':sha(Path(__file__)),'inputPins':pins(),'cases':CASES,'scope':'Four serial native delivery endpoints only; explicit current-refinement and real settings route; no S1/cost/full-motion/actual-parent replay.'});print('prepared')
 else:asyncio.run(main())
