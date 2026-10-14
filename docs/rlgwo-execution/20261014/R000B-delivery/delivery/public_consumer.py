"""Bounded R000B actual-Pages consumer readback; reuse R000C ingress preload.

Default-motion endpoints in serial disposable Chromium/Firefox. This confirms
delivery; it does not repeat or replace the original B16 first-pixel/motion work.
"""
from pathlib import Path
import datetime, hashlib, importlib.metadata, json, os, sys, time
from urllib.parse import urlencode

E=Path(__file__).resolve().parents[1]
R=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
D=E/'delivery';O=D/'public-consumer'
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
sys.path.insert(0,str(R/'tools/qa'))
from playwright.sync_api import sync_playwright
from r000c_single_document import span
from run_r000c_native import tile_png, wait
M='763a460e98dc23c7f0e95bf346274f1685b3c654'
U='https://theislampill.github.io/salah_widget/'
sha=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(path,value):path.write_bytes((json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
assert not O.exists(),'Retain prior consumer attempt; inspect before any repeat.'
delivery=json.loads((D/'source-docs-readback.json').read_bytes())
assert delivery['status']=='PASS' and delivery['mergeCommit']==M
source=(R/'index.html').read_bytes();wrapper_bytes=(R/'tests/rlgwo/r000b-weather-fixture.html').read_bytes()
assert sha(source)=='d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f'
assert sha(wrapper_bytes)=='74f4b743a831760fae84dba5bb2e1dae8d6af901786876a46c9ce532854ccda5'
wrapper=wrapper_bytes.decode('utf8')
declarations=span(wrapper,'  const nativeFetch=','  // Serialized as a separate, labeled classic script')
shims=span(wrapper,'    // These hooks must exist before DOM parsing','    const doc=new DOMParser()')
preload=('(function(){\n"use strict";\n'+declarations+'\nreport.sourceSha256='+json.dumps(sha(source))+';\n'+shims+'\n'+
 'report.documentMode="actual-pages-ingress-preload";report.state="loading";\n'+
 'document.addEventListener("DOMContentLoaded",()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=="function")throw Error("Actual widget/config missing");if(!report.error)report.state="ready";}catch(e){failure(e);}},{once:true});\n})();')
assert 'installWeatherBridge' not in preload and 'qaState()' not in preload
tile=tile_png();O.mkdir();(O/'preload.js').write_bytes(preload.encode());(O/'controlled-tile.png').write_bytes(tile)
case={'id':'B16-night-expiry-recovery','startUtc':'2026-09-07T18:44:50Z','initialCurrentTime':'2026-09-07T21:30',
 'currentIntervalSeconds':900,'weatherCode':63,'temperature':24,'precipitationMm':2,'cloudPercent':70,
 'zone':'Asia/Riyadh','site':{'lat':24.47,'lon':39.61,'label':'Madinah'},'clock':'native-elapsed-1x',
 'motionPreference':'no-preference','moonForces':{'simMoon':.5,'simMoonAlt':20,'simMoonH':42},
 'ordinaryWeatherSequence':'initial current, source expiry, second response503, third eligible response through ordinary retry',
 'scope':'Delivered default-motion endpoints only; no new first-Moon or continuous-motion qualification.'}
dump(O/'case-input.json',case)
report={'schema':'r000b-public-consumer/v1','status':'RUNNING','mergeCommit':M,'startedAtUtc':now(),
 'playwrightVersion':importlib.metadata.version('playwright'),'procedureSha256':sha(Path(__file__).read_bytes()),
 'caseInputsSha256':sha((O/'case-input.json').read_bytes()),'wrapperSha256':sha(wrapper_bytes),
 'declarationSpanSha256':sha(declarations.encode()),'isolationSpanSha256':sha(shims.encode()),
 'preloadSha256':sha(preload.encode()),'storedPreloadSha256':sha((O/'preload.js').read_bytes()),'controlledTileSha256':sha(tile),
 'reusedSpanToolSha256':sha((R/'tools/qa/r000c_single_document.py').read_bytes()),
 'reusedRunnerToolSha256':sha((R/'tools/qa/run_r000c_native.py').read_bytes()),
 'productionResponseRewritten':False,'sourceObserverInserted':False,'qaStateCalled':False,
 'viewport':{'width':390,'height':600},'deviceScaleFactor':1,'browserTimezone':'Asia/Riyadh',
 'scope':'Actual Pages root, serial disposable headless Chromium/Firefox. Unchanged R000B fixture ingress supplies native Responses, private storage and advancing1x Date. Product HTTP bytes, native timers/performance/animation and ordinary retries are unchanged. DOM/cache/ledger endpoints and screenshots confirm delivered behavior; they do not replace original B16 continuous watches, establish between-capture pixels, or upgrade first-state Moon omissions or failed Firefox videos.',
 'results':[]}
assert report['playwrightVersion']=='1.60.0'
def save():dump(O/'readback.json',report)
read_dom="""() => {
 const q=s=>document.querySelector(s),c=q('.c'),r=c.getBoundingClientRect(),f=q('.d').getBoundingClientRect(),stores=[];
 for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i),raw=localStorage.getItem(key);try{stores.push({key,value:JSON.parse(raw)});}catch{stores.push({key,raw});}}
 const weather=stores.filter(s=>s.value?.w&&Object.prototype.hasOwnProperty.call(s.value.w,'temp')&&Object.prototype.hasOwnProperty.call(s.value.w,'precip'));
 return {temperature:q('#wt').textContent,icon:q('#wi').textContent,headerLabel:q('#wi').title,
 fx:c.dataset.fx,precip:c.dataset.precip,lightning:c.dataset.lightning,rainOpacity:+getComputedStyle(c).getPropertyValue('--rain-op'),
 visibleParticles:[...document.querySelectorAll('.drop,.flake')].filter(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;}).length,
 card:{width:r.width,height:r.height},footer:{top:f.top-r.top,bottom:f.bottom-r.top},rows:q('.times').children.length,
 times:q('.times').textContent,date:q('#ce').textContent,next:q('.nt').textContent,weatherCache:weather,storage:stores,
 browserTimezone:Intl.DateTimeFormat().resolvedOptions().timeZone,fixtureUtc:new Date().toISOString(),wallUtcMs:Date.now(),
 elapsedMs:performance.now()-__widgetFixture.started,fixture:__widgetFixture,
 productObserverPresent:typeof window.__smokeWeather!=='undefined'};
}"""
wet_ready="""() => {
 const f=window.__widgetFixture;if(f?.state==='error')throw Error(f.error);if(f?.state!=='ready')return false;
 const q=s=>document.querySelector(s);return q('.times')?.children.length===6&&q('#wt')?.textContent==='24°'&&q('.c')?.dataset.precip==='on'&&
 [...document.querySelectorAll('.drop,.flake')].some(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;});
}"""
dry_ready="""() => {const f=window.__widgetFixture;if(f?.state==='error')throw Error(f.error);const c=document.querySelector('.c');return f?.state==='ready'&&performance.now()-f.started>10000&&document.querySelector('#wt')?.textContent===''&&document.querySelector('#wi')?.textContent==='—'&&c?.dataset.precip==='off'&&
 ![...document.querySelectorAll('.drop,.flake')].some(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;});}"""
save()
try:
 with sync_playwright() as pw:
  for number,(family,relative,expected_exe) in enumerate([
   ('chromium','chromium-1223/chrome-win64/chrome.exe','290fa7018fda22c52ada5eddb0113baf3ebc41fd0fde6085eddb19793606c635'),
   ('firefox','firefox-1522/firefox/firefox.exe','960a9a013187e337fc03b685ec8bed803791033620985e99fa66438b4fcd6c80')],1):
   exe=Path(os.environ['LOCALAPPDATA'])/'ms-playwright'/relative;assert sha(exe.read_bytes())==expected_exe
   options={'executable_path':str(exe),'headless':True}
   if family=='chromium':options.update(args=['--disable-dev-shm-usage'],chromium_sandbox=True)
   browser=getattr(pw,family).launch(**options)
   context=browser.new_context(viewport=report['viewport'],device_scale_factor=1,timezone_id='Asia/Riyadh',reduced_motion='no-preference')
   errors=[];tile_requests=[];network_errors=[];page=context.new_page()
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.on('requestfailed',lambda request:network_errors.append({'url':request.url,'failure':request.failure}))
   def tile_response(route):
    tile_requests.append({'url':route.request.url,'sha256':sha(tile)});route.fulfill(status=200,content_type='image/png',body=tile)
   context.route('https://theislampill.github.io/tile/**',tile_response)
   item={'engine':family,'version':browser.version,'executable':exe.name,'executableSha256':expected_exe,
     'headless':True,'case':case,'states':[],'pageErrors':errors,'networkErrors':network_errors,'controlledTileRequests':tile_requests}
   report['results'].append(item)
   try:
    config={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','label':'Madinah','method':4,'school':0,'units':'c','seed':1,'qa':1,'simMoon':.5,'simMoonAlt':20,'simMoonH':42}
    query={'case':case['id'],'mode':'healthy','attempt':number,'run':'R000B-delivery-20261014','night':1}
    url=U+'?'+urlencode(query)+'#'+urlencode(config);item['url']=url
    page.add_init_script(preload)
    response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
    body=response.body();item.update(httpStatus=response.status,sourceSha256=sha(body),sourceExact=body==source)
    assert response.status==200 and item['sourceExact']
    def capture(stage,wet,expected_ordinal):
     observed=page.evaluate(read_dom);name=family+'-'+stage+'.png'
     capture_start=page.evaluate('() => ({wallUtcMs:Date.now(),elapsedMs:performance.now()-__widgetFixture.started})')
     page.screenshot(path=str(O/name))
     after=page.evaluate(read_dom)
     fixture=observed['fixture'];model=[r for r in fixture['ledger'] if 'weatherOrdinal' in r];radar=[r for r in fixture['ledger'] if 'radarOrdinal' in r]
     cache=observed['weatherCache'];w=cache[0]['value']['w'] if len(cache)==1 else {}
     source_age=observed['wallUtcMs']-w.get('currentValidAt',0);receipt_age=observed['wallUtcMs']-w.get('retrievedAt',0)
     checks={'exactServedSource':item['sourceExact'],'weatherRequestOrdinal':len(model)==expected_ordinal,
      'isolatedIngress':fixture['storageIsolated'] and fixture['clockIsolated'] and fixture['fetchIntercepted'] and fixture['initialStorageEntries']==0,
      'sourceMetadata':w.get('currentIntervalSec')==900 and w.get('currentZone')=='Asia/Riyadh' and w.get('temp')==24 and w.get('precip')==2,
      'sourceAndReceiptDistinct':w.get('retrievedAt',0)>w.get('currentValidAt',0),
      'sourceAgeSupportsPresentation':0<=source_age<=900000 and 0<=receipt_age<=900000 if wet else source_age>900000,
      'temperatureHeader':observed['temperature']==('24°' if wet else ''),'effectDataset':observed['precip']==('on' if wet else 'off'),
      'particles':observed['visibleParticles']>0 if wet else observed['visibleParticles']==0,
      'noLightning':observed['lightning']=='off','cardGeometry':observed['card']=={'width':325,'height':530},
      'footerFits':0<=observed['footer']['top']<observed['footer']['bottom']<=530.1,'sixPrayerRows':observed['rows']==6,
      'correctTimezone':observed['browserTimezone']=='Asia/Riyadh','noSourceObserver':not observed['productObserverPresent'],
      'clockPolicy':fixture['clockPolicy']=='advancing-1x','noUnexpectedFetch':not fixture['error'] and all(r['result']!='unexpected-request' for r in fixture['ledger']),
      'controlledRadarTileConsumed':bool(tile_requests),'radarInputsDistinct':len(radar)==1 and radar[0].get('parsedBody',{}).get('generated')==1788806670 and radar[0].get('parsedBody',{}).get('radar',{}).get('past',[{}])[0].get('time')==1788805500,
      'noPageError':not errors,'samePresentationAfterScreenshot':after['temperature']==observed['temperature'] and after['precip']==observed['precip']}
     if wet:
      checks['modelDisclosure']='current model estimate' in observed['headerLabel'] and 'direct local observation unavailable' in observed['headerLabel']
      checks['nativeResponseConsumed']=model[-1].get('jsonSettled') and model[-1]['jsonReads']==1
     else:checks['unavailable']=observed['icon']=='—' and observed['rainOpacity']==0 and observed['fx'] not in ('rain','thunder','snow')
     if stage=='current':checks['originalSource']=w.get('currentValidAt')==1788805800000 and observed['elapsedMs']<10000
     if stage in ('503','restored','settled'):checks['controlled503']=len(model)>=2 and model[1]['status']==503 and model[1]['jsonReads']==0
     item['states'].append({'stage':stage,'observed':observed,'checks':checks,'screenshot':name,'pngSha256':sha((O/name).read_bytes()),
       'captureStart':capture_start,'captureEnd':{'wallUtcMs':after['wallUtcMs'],'elapsedMs':after['elapsedMs']},'sourceAgeMs':source_age,'receiptAgeMs':receipt_age});save()
     assert all(checks.values()),{k:v for k,v in checks.items() if not v}
     print(json.dumps({'engine':family,'stage':stage,'status':'PASS_STATE_ASSERTIONS','elapsedMs':observed['elapsedMs']}),flush=True)
     return observed
    wait(page,wet_ready,15000);current=capture('current',True,1)
    wait(page,dry_ready,20000);expired=capture('expired',False,1)
    wait(page,"() => __widgetFixture.ledger.some(r=>r.weatherOrdinal===2&&r.status===503)",110000);failed=capture('503',False,2)
    wait(page,"() => __widgetFixture.ledger.some(r=>r.weatherOrdinal===3&&r.jsonSettled)",100000)
    wait(page,wet_ready,10000);restored=capture('restored',True,3)
    page.wait_for_timeout(2200);settled=capture('settled',True,3)
    weather=[r for r in settled['fixture']['ledger'] if 'weatherOrdinal' in r]
    checks={'ordinaryRetryIntervals':all(b['elapsedMs']-a['elapsedMs']>=60000 for a,b in zip(weather,weather[1:])),
      'retainedStaleCache':current['weatherCache'][0]['value']==expired['weatherCache'][0]['value']==failed['weatherCache'][0]['value'],
      'healthyNewSource':restored['weatherCache'][0]['value']['w']['currentValidAt']>current['weatherCache'][0]['value']['w']['currentValidAt'],
      'native1x':abs((settled['wallUtcMs']-current['wallUtcMs'])-(settled['elapsedMs']-current['elapsedMs']))<10,
      'settledInterval':settled['elapsedMs']-restored['elapsedMs']>=2200}
    item['sequenceChecks']=checks;assert all(checks.values()),checks
    item['status']='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW';save()
   except Exception:
    try:
     page.screenshot(path=str(O/(family+'-failure.png')))
     item['failureObservation']=page.evaluate(read_dom)
    except Exception as capture_error:item['failureCaptureError']=repr(capture_error)
    raise
   finally:context.close();browser.close()
 report['status']='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW';report['completedAtUtc']=now();save()
except Exception as error:
 report['status']='FAIL_POST_DELIVERY_PUBLIC_CONSUMER';report['error']=repr(error);save();raise
print(json.dumps({'status':report['status'],'mergeCommit':M,'engines':len(report['results']),'endpoints':sum(len(i['states']) for i in report['results'])}))
