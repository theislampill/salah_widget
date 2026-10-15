"""Bounded actual Pages delivery consumers. No source edits, host UI, or video."""
from pathlib import Path
import argparse, importlib.util, json, os, sys, time, traceback
from urllib.parse import urlsplit,parse_qs,unquote
sys.path.insert(0,str(Path(__file__).resolve().parent))
from close_r0024 import ROOT,RUN,POST,PAGES,HEAD,BASE,sha,read,record,now,api

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native=load('delivered_native_owner',ROOT/'tools/qa/run_r0024_native.py')
base=native.helper_module();oracle=load('delivered_info_oracle',ROOT/'tools/qa/info_contract.py');contract=load('delivered_effect_oracle',ROOT/'tools/qa/native_contract.py')
SELECT=['A-wet-rain','A-wet-snow','B-supported-dry','C-approach','C-no-trajectory','D-live-rain','D-live-snow','D-live-thunder','forecast-none','forecast-0']
EXPECTED=read(RUN/'publication/qualification/committed-candidate.json')['runtime']['files']

def write(p,x):
    with p.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def run(engine,attempt):
    assert read(POST/'pages-delivery.json')['status']=='EXACT_DELIVERED_RUNTIME_AND_PROTECTED_MERGE_TREE'
    assert api('git/ref/heads/main')['object']['sha']==read(POST/'merge-readback.json')['merge']
    out=POST/'native'/(engine+'-'+attempt);out.mkdir(parents=True,exist_ok=False)
    prior=read(RUN/('native/chromium/resume-r2/results.json'if engine=='chromium'else'native/firefox/resume-r6/results.json'))['capability']
    exe=Path(prior['executable']);driver=prior['driver'];assert sha(exe.read_bytes())==prior['executableSha256']
    import playwright._impl._transport as transport
    transport.compute_driver_executable=lambda:(driver['node'],driver['cli'])
    from playwright.sync_api import sync_playwright
    result={'schema':'r0024-delivered-native/v1','engine':engine,'attempt':attempt,'pythonExecutable':sys.executable,'startedUtc':now(),'sourceHead':HEAD,'merge':read(POST/'merge-readback.json')['merge'],'runtimeSha256':read(POST/'pages-delivery.json')['runtimeSha256'],'cases':[],
      'adapterSha256':sha(Path(__file__).read_bytes()),'inputs':native.input_manifest(ROOT),'scope':'Actual Pages bytes fetched and hash-verified before unchanged fulfillment into reviewed controlled provider/clock/storage/SIM wrapper. Separate direct unbridged ordinary Pages smoke. No original195-case replay, recorder or motion credit.',
      'capability':{k:prior[k]for k in ['executable','executableSha256','headless','playwrightVersion']},'driver':{k:driver[k]for k in ['version','node','cli','nodeSha256']},'status':'STARTED'}
    try:
      with sync_playwright()as pw:
        opts={'headless':True,'executable_path':str(exe)}
        if engine=='chromium':opts.update(chromium_sandbox=True,args=['--disable-dev-shm-usage'])
        browser=getattr(pw,engine).launch(**opts)
        try:
          result['browserVersion']=browser.version;delivered_cache={}
          for index,case_id in enumerate(SELECT,1):
            spec=next(x for x in native.cases()if x['id']==case_id);dest=out/case_id;dest.mkdir();rows=[];faults=[];context=None
            class Server:origin=PAGES.rstrip('/')
            helpers={'/actions.js':ROOT/'tests/weather-native/actions.js','/forecast.js':ROOT/'tests/weather-forecast-fixture.js','/native-controls.js':ROOT/'tests/weather-native/native-controls.js'}
            def route_handler(route):
              try:
                path=unquote(urlsplit(route.request.url).path)
                if path=='/salah_widget/fixture.html':data=(ROOT/'tests/weather-native/widget-fixture.html').read_bytes();mime='text/html; charset=utf-8'
                elif path in helpers:data=helpers[path].read_bytes();mime='text/javascript'
                elif path=='/case.json':
                  assert parse_qs(urlsplit(route.request.url).query)['case']==[case_id]
                  data=json.dumps(spec,ensure_ascii=False,allow_nan=False).encode();mime='application/json'
                elif path.startswith('/tile/v2/radar/'):
                  data=native.tile_png(spec.get('tile','zero-dbz'));mime='image/png'
                elif path.startswith('/product/'):
                  rel=path[len('/product/'):];assert rel in EXPECTED,rel
                  url=PAGES+rel;cached=rel in delivered_cache
                  if not cached:
                    response=route.fetch(url=url,headers={**route.request.headers,'accept-encoding':'identity','cache-control':'no-cache'},timeout=60000)
                    data=response.body();want=EXPECTED[rel];assert response.status==200 and len(data)==want['bytes']and sha(data)==want['sha256'],rel
                    headers={k:v for k,v in response.headers.items()if k not in ['content-encoding','content-length','transfer-encoding']}
                    delivered_cache[rel]=(data,headers);response.dispose()
                  data,headers=delivered_cache[rel]
                  rows.append({'requestUrl':route.request.url,'actualPagesUrl':url,'status':200,'bytes':len(data),'sha256':sha(data),'manifestMatch':True,'reusedExactHttpBytesWithinEngine':cached})
                  route.fulfill(status=200,headers=headers,body=data);return
                elif path.endswith('favicon.ico'):route.fulfill(status=204);return
                else:raise ValueError('Unexpected mapped URL '+route.request.url)
                rows.append({'requestUrl':route.request.url,'controlledFixture':True,'bytes':len(data),'sha256':sha(data)})
                route.fulfill(status=200,content_type=mime,body=data)
              except Exception:
                faults.append(traceback.format_exc());route.abort()
            # Install before the unchanged helper creates and navigates a new page.
            original_new=browser.new_context
            def new_context(**kwargs):
              c=original_new(**kwargs);c.route('https://theislampill.github.io/**',route_handler);return c
            browser.new_context=new_context
            row={'id':case_id,'input':spec,'startedUtc':now()}
            try:
              context,page,errors,network,url=base.open_case(browser,Server,spec,EXPECTED['index.html']['sha256'],'R0024-delivered-'+engine,index,dest)
              page.evaluate(native.approved_seed());actions=[]
              for n,action in enumerate(spec.get('actions',[])):
                r=page.evaluate('i=>__weatherCases.step(__weatherCases.identity(),i)',n);native.publication(page,base,action.get('checkpoint',{}));actions.append(r)
              expected={**spec['expect'],'group':'R0024'};native.publication(page,base,expected)
              page.wait_for_timeout(1200)
              state=page.evaluate('()=>__weatherCases.read(__weatherCases.identity())');observed=native.observation(page);ax=native.ax_read(page,base)
              checks=page.evaluate('e=>__weatherCases.checks(__weatherCases.read(__weatherCases.identity()),e)',expected)
              info=contract.info_applicability(oracle.info_checks(state,ax,spec),spec,engine);checks.update({'INFO:'+k:v for k,v in info['applicable'].items()})
              samples=[page.evaluate('()=>__weatherCases.strikeRead(__weatherCases.identity())')for _ in range(3)]
              checks.update(contract.effect_checks(state,samples,spec,observed['origins']));checks.update(contract.provenance_checks(state,spec))
              checks.update(noPageErrors=not errors,noMappedByteFailures=not faults,actualPagesEntrySeen=any(r.get('actualPagesUrl')==PAGES+'index.html'for r in rows),allActualNativeControls=all(x['passed']for x in observed['checks']))
              for selector,name in [('.c','card'),('.h','header'),('.d','footer')]:page.locator(selector).screenshot(path=str(dest/(name+'.png')))
              row.update(url=url,state=state,accessibility=ax,infoOracle=info,nativeObservation=observed,checks=checks,actions=actions,pageErrors=errors,network=network,fixture=page.evaluate('()=>({sourceSha256:__widgetFixture.sourceSha256,bridgeSha256:__widgetFixture.bridgeSha256,ledger:__widgetFixture.ledger})'))
              row['status']='CHECKS_PASS_PENDING_PIXEL_REVIEW'if all(checks.values())else'FAIL'
            except Exception:row.update(status='FAILED_CONSUMER_OR_HARNESS',exception=traceback.format_exc())
            finally:
              browser.new_context=original_new
              if context:context.close()
            row.update(actualPageBytes=rows,mappingFailures=faults,finishedUtc=now());write(dest/'receipt.json',row);result['cases'].append(row)
            print(json.dumps({'engine':engine,'case':case_id,'status':row['status'],'failedChecks':[k for k,v in row.get('checks',{}).items()if not v]}),flush=True)
            if row['status']!='CHECKS_PASS_PENDING_PIXEL_REVIEW':raise ValueError('Retain failing delivery case; stop this batch')
          dest=out/'ordinary-pages';dest.mkdir();context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='Asia/Riyadh');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
          url=PAGES+'index.html#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c'
          response=page.goto(url,wait_until='domcontentloaded',timeout=60000);body=response.body();assert response.status==200 and sha(body)==EXPECTED['index.html']['sha256']
          base.wait(page,"()=>document.querySelector('#weather-information')?.textContent.length>0",timeout=45000);page.wait_for_timeout(12000)
          observation=page.evaluate("""()=>{const card=document.querySelector('.c'),wi=document.querySelector('#wi'),d=document.querySelector('#weather-information'),b=document.querySelector('.buckle'),f=document.querySelector('.d'),box=card.getBoundingClientRect(),fb=f.getBoundingClientRect();return {description:d.textContent,title:wi.title,name:wi.getAttribute('aria-label'),describedBy:wi.getAttribute('aria-describedby'),buckle:{name:b.getAttribute('aria-label'),role:b.getAttribute('role'),tabIndex:b.tabIndex,describedBy:b.getAttribute('aria-describedby')},card:{width:box.width,height:box.height},footer:{top:fb.top-box.top,bottom:fb.bottom-box.top},fixtureAbsent:typeof window.__widgetFixture==='undefined'&&typeof window.__weatherCases==='undefined',qa:window.qaState(),rows:[...document.querySelectorAll('.row')].map(e=>({text:e.textContent,opacity:getComputedStyle(e).opacity})),informationClipped:d.getBoundingClientRect().width<=1&&d.getBoundingClientRect().height<=1};}""")
          ax=native.ax_read(page,base);checks={'entryExact':True,'noTestBridge':observation['fixtureAbsent'],'card325x530':observation['card']=={'width':325,'height':530},'footerFits':0<=observation['footer']['top']<observation['footer']['bottom']<=530,'descriptionInTitle':observation['description']in observation['title'],'descriptionBoundOnce':observation['describedBy'].split().count('weather-information')==1,'descriptionClipped':observation['informationClipped'],'ordinaryModelNotObserved':observation['qa']['wxTruth'].get('observedPresent')is False,'nativeDescriptionReachable':observation['description']in str(ax['rawAriaSnapshot']['#weather-information'])}
          for selector,name in [('.c','card'),('.h','header'),('.d','footer')]:page.locator(selector).screenshot(path=str(dest/(name+'.png')))
          ordinary={'url':url,'sourceSha256':sha(body),'responseStatus':response.status,'observation':observation,'accessibility':ax,'checks':checks,'pageErrors':errors,'status':'CHECKS_PASS_PENDING_PIXEL_REVIEW'if all(checks.values())else'FAIL','scope':'Direct real Pages navigation; no provider, source, clock or storage interception. External-provider availability is observed, not promised.'}
          write(dest/'receipt.json',ordinary);result['ordinaryPages']=ordinary;context.close();assert all(checks.values()),checks
        finally:browser.close()
      result['status']='DELIVERED_CONSUMERS_EXECUTED_PENDING_INDEPENDENT_PIXEL_REVIEW'
    except Exception:result.update(status='FAIL',exception=traceback.format_exc())
    result['finishedUtc']=now();write(out/'results.json',result);print(json.dumps({'engine':engine,'status':result['status'],'cases':len(result['cases'])}),flush=True)
    return 0 if result['status'].startswith('DELIVERED_')else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('engine',choices=['chromium','firefox']);parser.add_argument('--attempt',default='r1');args=parser.parse_args()
    lock=RUN/'native/native-resource.lock'
    with lock.open('x',encoding='utf-8')as f:json.dump({'pid':os.getpid(),'scope':'actual Pages delivery representative consumers','engine':args.engine,'atUtc':now()},f)
    try:code=run(args.engine,args.attempt)
    finally:lock.unlink()
    raise SystemExit(code)
