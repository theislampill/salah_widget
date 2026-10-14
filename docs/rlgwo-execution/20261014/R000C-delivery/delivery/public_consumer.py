"""Bounded R000C delivered consumer readback using existing controlled ingress."""
from pathlib import Path
import datetime, hashlib, importlib.metadata, json, os, sys, time
from urllib.parse import urlencode
E=Path(__file__).resolve().parents[1];R=E.parent/'salah_widget';D=E/'delivery';O=D/'public-consumer'
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
sys.path.insert(0,str(R/'tools/qa'))
from playwright.sync_api import sync_playwright
from r000c_single_document import span
from run_r000c_native import tile_png
M='16658749209e0c567f49a3fc9dc855f665afa6e4'
U='https://theislampill.github.io/salah_widget/'
sha=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf8')
assert not O.exists(),'Retain prior consumer attempt; inspect before any repeat.'
assert json.loads((D/'source-docs-readback.json').read_bytes())['status']=='PASS'
packet=json.loads((R/'tests/rlgwo/R000C-cases.json').read_bytes())
selected=[next(c for c in packet['cases'] if c['id']==name) for name in ('R000C-null-temp','R000C-zero-temp','R000C-invalid-precip')]
source=(R/'index.html').read_bytes();wrapper_bytes=(R/'tests/rlgwo/weather-browser-fixture.html').read_bytes()
assert sha(source)==packet['sourceFiles']['index.html']
assert sha(wrapper_bytes)==packet['sourceFiles']['tests/rlgwo/weather-browser-fixture.html']
wrapper=wrapper_bytes.decode('utf8')
declarations=span(wrapper,'  const nativeFetch=','  // Serialized as a separate, labeled classic script')
shims=span(wrapper,'    // These hooks must exist before DOM parsing','    const doc=new DOMParser()')
preload=('(function(){\n"use strict";\n'+declarations+'\nreport.sourceSha256='+json.dumps(sha(source))+';\n'+shims+'\n'+
 'report.documentMode="actual-pages-ingress-preload";report.state="loading";\n'+
 'document.addEventListener("DOMContentLoaded",()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=="function")throw Error("Actual widget/config missing");if(!report.error)report.state="ready";}catch(e){failure(e);}},{once:true});\n})();')
assert 'installWeatherBridge' not in preload and 'qaState()' not in preload
tile=tile_png();O.mkdir();(O/'preload.js').write_text(preload,encoding='utf8');(O/'controlled-tile.png').write_bytes(tile)
dump(O/'case-inputs.json',selected)
report={'schema':'r000c-public-consumer/v1','status':'RUNNING','mergeCommit':M,'readAtUtc':now(),
 'playwrightVersion':importlib.metadata.version('playwright'),'procedureSha256':sha(Path(__file__).read_bytes()),
 'casePacketSha256':sha((R/'tests/rlgwo/R000C-cases.json').read_bytes()),'caseInputsSha256':sha((O/'case-inputs.json').read_bytes()),
 'wrapperSha256':sha(wrapper_bytes),'declarationSpanSha256':sha(declarations.encode()),'isolationSpanSha256':sha(shims.encode()),
 'preloadSha256':sha(preload.encode()),'controlledTileSha256':sha(tile),
 'productionResponseRewritten':False,'sourceObserverInserted':False,'qaStateCalled':False,
 'viewport':{'width':390,'height':600},'deviceScaleFactor':1,'browserTimezone':'Asia/Riyadh',
 'scope':'Actual Pages root, serial disposable headless Chromium/Firefox, three unchanged accepted day inputs (null temperature, genuine zero, invalid precipitation). Existing native Response ingress, private storage and fixed 2026-09-07T09:30Z fixture Date only. Native timers/performance/animation unchanged. Current and settled endpoints are delivered-consumer confirmation, not continuous-watch, first-frame, provider-health or new whole-scene qualification. All retained failed Firefox watches remain failed.',
 'results':[]}
def save():dump(O/'readback.json',report)
read_dom="""() => {
 const q=s=>document.querySelector(s),c=q('.c'),r=c.getBoundingClientRect(),f=q('.d').getBoundingClientRect(),stores=[];
 for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i),raw=localStorage.getItem(key);try{stores.push({key,value:JSON.parse(raw)});}catch{stores.push({key,raw});}}
 const weather=stores.filter(s=>s.value?.w&&Object.prototype.hasOwnProperty.call(s.value.w,'temp')&&Object.prototype.hasOwnProperty.call(s.value.w,'precip'));
 return {temperature:q('#wt').textContent,icon:q('#wi').textContent,headerLabel:q('#wi').title,
 fx:c.dataset.fx,precip:c.dataset.precip,lightning:c.dataset.lightning,
 visibleParticles:[...document.querySelectorAll('.drop,.flake')].filter(e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;}).length,
 card:{width:r.width,height:r.height},footer:{top:f.top-r.top,bottom:f.bottom-r.top},rows:q('.times').children.length,
 times:q('.times').textContent,date:q('#ce').textContent,next:q('.nt').textContent,weatherCache:weather,storage:stores,
 browserTimezone:Intl.DateTimeFormat().resolvedOptions().timeZone,fixtureUtc:new Date().toISOString(),
 elapsedMs:performance.now()-__widgetFixture.started,fixture:__widgetFixture,
 productObserverPresent:typeof window.__smokeWeather!=='undefined'};
}"""
ready="""() => {
 const f=window.__widgetFixture;if(f?.state==='error')throw Error(f.error);if(f?.state!=='ready')return false;
 const q=s=>document.querySelector(s);if(q('.times')?.children.length!==6||!q('#wi')?.title.includes('current model estimate'))return false;
 return f.ledger.some(r=>r.url.includes('api.open-meteo.com/v1/forecast')&&r.jsonSettled&&r.jsonReads===1);
}"""
save()
try:
 with sync_playwright() as pw:
  for family,relative,expected_exe in [
   ('chromium','chromium-1223/chrome-win64/chrome.exe','290fa7018fda22c52ada5eddb0113baf3ebc41fd0fde6085eddb19793606c635'),
   ('firefox','firefox-1522/firefox/firefox.exe','960a9a013187e337fc03b685ec8bed803791033620985e99fa66438b4fcd6c80')]:
   exe=Path(os.environ['LOCALAPPDATA'])/'ms-playwright'/relative
   assert sha(exe.read_bytes())==expected_exe
   options={'executable_path':str(exe),'headless':True}
   if family=='chromium':options.update(args=['--disable-dev-shm-usage'],chromium_sandbox=True)
   for number,case in enumerate(selected,1):
    browser=getattr(pw,family).launch(**options)
    context=browser.new_context(viewport=report['viewport'],device_scale_factor=1,timezone_id='Asia/Riyadh',reduced_motion=case['motionPreference'])
    errors=[];tile_requests=[];network_errors=[];page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('requestfailed',lambda request:network_errors.append({'url':request.url,'failure':request.failure}))
    def tile_response(route):
     tile_requests.append({'url':route.request.url,'sha256':sha(tile)});route.fulfill(status=200,content_type='image/png',body=tile)
    context.route('https://theislampill.github.io/tile/**',tile_response)
    item={'engine':family,'version':browser.version,'executable':exe.name,'executableSha256':expected_exe,
      'headless':True,'caseId':case['id'],'case':case,'states':[],'pageErrors':errors,'networkErrors':network_errors,'controlledTileRequests':tile_requests}
    report['results'].append(item)
    try:
     config={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','label':'Madinah','method':4,'school':0,'units':'c','seed':1}
     query={'case':case['inputCase'],'attempt':number,'run':'R000C-delivery-20261014','night':0}
     url=U+'?'+urlencode(query)+'#'+urlencode(config);item['url']=url
     page.add_init_script(preload)
     response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
     body=response.body();item.update(httpStatus=response.status,sourceSha256=sha(body),sourceExact=body==source)
     assert response.status==200 and item['sourceExact']
     deadline=time.monotonic()+45
     while not page.evaluate(ready):
      assert time.monotonic()<deadline,'Delivered consumer did not reach its bounded endpoint'
      page.wait_for_timeout(200)
     wet=case['precip'] is not None and case['precip']>0
     while True:
      state=page.evaluate(read_dom)
      if state['fx']=='thunder' and state['precip']==('on' if wet else 'off') and (state['visibleParticles']>0 if wet else state['visibleParticles']==0):break
      assert time.monotonic()<deadline,'Delivered weather effects did not reach the expected endpoint'
      page.wait_for_timeout(200)
     def capture(stage):
      observed=page.evaluate(read_dom);name=family+'-'+case['id']+'-'+stage+'.png';page.screenshot(path=str(O/name))
      fixture=observed['fixture'];model=[r for r in fixture['ledger'] if 'api.open-meteo.com/v1/forecast' in r['url']]
      cache=observed['weatherCache'];w=cache[0]['value']['w'] if len(cache)==1 else {}
      checks={'exactServedSource':item['sourceExact'],'nativeResponseConsumed':len(model)==1 and model[0].get('jsonSettled') and model[0]['jsonReads']==1,
       'isolatedIngress':fixture['storageIsolated'] and fixture['clockIsolated'] and fixture['fetchIntercepted'] and fixture['initialStorageEntries']==0,
       'temperatureCached':len(cache)==1 and w.get('temp')==case['temp'],'precipitationCached':len(cache)==1 and w.get('precip')==case['precip'],
       'temperatureHeader':observed['temperature']==('' if case['temp'] is None else str(case['temp'])+'\u00b0'),
       'conditionRetained':observed['icon']=='\u26c8\ufe0f' and observed['fx']=='thunder',
       'modelDisclosure':'current model estimate' in observed['headerLabel'] and 'direct local observation unavailable' in observed['headerLabel'],
       'effectDataset':observed['precip']==('on' if wet else 'off'),'particles':observed['visibleParticles']>0 if wet else observed['visibleParticles']==0,
       'noLightning':observed['lightning']=='off','cardGeometry':observed['card']=={'width':325,'height':530},
       'footerFits':observed['footer']['top']>=0 and observed['footer']['bottom']<=530.1,
       'sixPrayerRows':observed['rows']==6,'exactFixedDate':observed['fixtureUtc']=='2026-09-07T09:30:00.000Z',
       'correctTimezone':observed['browserTimezone']=='Asia/Riyadh','noSourceObserver':not observed['productObserverPresent'],
       'noUnexpectedFetch':not fixture['error'] and all(r['result']=='json-consumed' for r in fixture['ledger']),
       'controlledRadarTileConsumed':bool(tile_requests),'noPageError':not errors}
      if case['precip'] is None:checks['invalidAmountReason']=w.get('admission',{}).get('precip')=='invalid measurement'
      item['states'].append({'stage':stage,'observed':observed,'checks':checks,'screenshot':name,'pngSha256':sha((O/name).read_bytes())});save()
      assert all(checks.values()),{k:v for k,v in checks.items() if not v}
      return observed
     current=capture('current');page.wait_for_timeout(2200);settled=capture('settled')
     assert settled['elapsedMs']-current['elapsedMs']>=2200
     item['status']='PASS_POST_DELIVERY_PUBLIC_CONSUMER';save()
     print(json.dumps({'engine':family,'case':case['id'],'status':item['status']}),flush=True)
    finally:
     context.close();browser.close()
 report['status']='PASS_POST_DELIVERY_PUBLIC_CONSUMER';report['completedAtUtc']=now();save()
except Exception as error:
 report['status']='FAIL_POST_DELIVERY_PUBLIC_CONSUMER';report['error']=repr(error);save();raise
print(json.dumps({'status':report['status'],'mergeCommit':M,'cases':len(report['results']),'endpoints':sum(len(i['states']) for i in report['results'])}))
