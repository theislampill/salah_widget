"""Bounded actual Pages root readback with unchanged R0017 controlled ingress spans.
No wrapping or rewriting served product bytes; no assertion/state injection.
This is prayer/layout delivery evidence, not Moon startup or normal-live M0 qualification.
"""
import os,sys,time,json,traceback
from pathlib import Path
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B))
from public_smoke import ROOT,OUTER,seeds,identity,sha,dump,sync_playwright,browser_options
sys.path.insert(0,str(ROOT/'tools/qa'))
from r000c_single_document import span
E=B/'normal-root-01';assert not E.exists();E.mkdir()
source=(ROOT/'index.html').read_bytes();wrapper=(ROOT/'tests/widget-fixture.html').read_text(encoding='utf-8')
declarations=span(wrapper,'  const nativeFetch=','  // Serialized as a separate, labeled classic script')
shims=span(wrapper,'    // These hooks must exist before DOM parsing','    const doc=new DOMParser()')
preload='(function(){if(window!==top)return;\n"use strict";\n'+declarations+'\nreport.sourceSha256='+json.dumps(sha(source))+';\n'+shims+'\nreport.documentMode="actual-pages-r0017-controlled-ingress";report.state="loading";\ndocument.addEventListener("DOMContentLoaded",()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=="function")throw Error("Actual widget/config missing");if(!report.error)report.state="ready";}catch(e){failure(e);}},{once:true});\n})();'
assert 'installWeatherBridge' not in preload and 'qaState()' not in preload
(E/'preload.js').write_bytes(preload.encode());(E/'driver.py').write_bytes(Path(__file__).read_bytes())
report={'schema':'r0017-normal-public-consumer/v1','scope':__doc__,'source':identity(),'declarationSha256':sha(declarations.encode()),'isolationSha256':sha(shims.encode()),'preloadSha256':sha(preload.encode()),'spanToolSha256':sha((ROOT/'tools/qa/r000c_single_document.py').read_bytes()),'results':[]}
with sync_playwright() as pw:
 for number,engine in enumerate(['chromium','firefox'],1):
  os.environ['SALAH_BROWSER']=engine;family,opts=browser_options();opts['executable_path']=getattr(pw,family).executable_path
  browser=getattr(pw,family).launch(**opts);c=browser.new_context(viewport={'width':375,'height':800},device_scale_factor=2,timezone_id='Asia/Riyadh',reduced_motion='no-preference',service_workers='block')
  c.add_init_script('('+OUTER+')('+json.dumps(seeds('valid'))+');');c.add_init_script(preload)
  p=c.new_page();r={'engine':engine,'browser':browser.version,'executableSha256':sha(Path(opts['executable_path']).read_bytes()),'headless':True,'viewport':{'width':375,'height':800},'dpr':2,'pageErrors':[],'networkFailures':[],'checks':{},'startedUtc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};report['results'].append(r)
  p.on('pageerror',lambda e:r['pageErrors'].append(str(e)));p.on('requestfailed',lambda q:r['networkFailures'].append({'url':q.url,'error':q.failure}))
  try:
   r['url']='https://theislampill.github.io/salah_widget/?mode=healthy&run=R0017-deployed-public-20261014&attempt='+str(number)+'#lat=24.47&lon=39.61&label=Madinah&method=4&school=0&tz=Asia/Riyadh&qa=1'
   start=time.monotonic();response=p.goto(r['url'],wait_until='domcontentloaded',timeout=30000);r['response']={'status':response.status,'sha256':sha(response.body())}
   p.wait_for_function('()=>__widgetFixture.state==="ready"&&qaState().cache.prayerLoaded&&qaState().cache.tomorrowLoaded&&document.querySelector(".left").textContent==="3h 0m left until Asr"',timeout=8000)
   r['elapsedSeconds']=time.monotonic()-start
   read='''()=>{const c=document.querySelector('.c'),b=c.getBoundingClientRect(),f=document.querySelector('.d').getBoundingClientRect();return {fixture:__widgetFixture,qa:qaState(),model:model(),date:new Date().toISOString(),
     dom:{current:document.querySelector('.cn').innerText,next:document.querySelector('.nt').innerText,countdown:document.querySelector('.left').innerText,times:document.querySelector('.times').innerText},
     card:{width:b.width,height:b.height},footer:{top:f.top-b.top,bottom:f.bottom-b.top},fontStatus:document.fonts.status,
     outer:{before:__r0017Outer.before,after:__r0017Outer.snapshot(),getterAccesses:__r0017Outer.getterAccesses},observerPresent:typeof __smokeWeather!=='undefined'};}'''
   r['before']=p.evaluate(read);p.screenshot(path=str(E/(engine+'.png')));r['after']=p.evaluate(read)
   v=r['after'];f=v['fixture'];q=v['qa'];ledger=[x for x in f['ledger'] if 'api.aladhan.com' in x['url']]
   r['checks']={'exactServedSource':r['response']=={'status':200,'sha256':sha(source)},'privateIngress':f['storageIsolated'] and f['clockFixed'] and f['fetchIntercepted'] and f['initialStorageEntries']==0 and f['error'] is None,
    'matchingJsonRequests':len(ledger)==2 and all(x['jsonReads']==1 and x['result']=='json-consumed' and x['attempt']==number for x in ledger) and '/07-09-2026?' in ledger[0]['url'] and '/08-09-2026?' in ledger[1]['url'],
    'realPrayerConsumer':q['cache']['prayerLoaded'] and q['cache']['tomorrowLoaded'] and q['render']['currentKey']=='Dhuhr' and q['render']['nextKey']=='Asr' and q['render']['leftMin']==180 and v['model']['nextTime']=='15:30',
    'actualCountdown':v['dom']['countdown']=='3h 0m left until Asr','stableAcrossCapture':r['before']['dom']==v['dom'],
    'cardAndFooter':v['card']=={'width':325,'height':530} and 0<=v['footer']['top']<v['footer']['bottom']<=530.1,
    'fixedRecipe':v['date']=='2026-09-07T09:30:00.000Z','noObserverInjection':not v['observerPresent'],
    'outerBytes':v['outer']['before']==v['outer']['after']==seeds('valid') and v['outer']['getterAccesses']==0,'noPageError':not r['pageErrors']}
   r['pngSha256']=sha((E/(engine+'.png')).read_bytes())
  except Exception:r['exception']=traceback.format_exc()
  finally:
   r['status']='PASS' if r['checks'] and all(r['checks'].values()) and not r.get('exception') else 'FAIL';r['finishedUtc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());c.close();browser.close();dump(E/'result.json',report);print(json.dumps({'engine':engine,'status':r['status'],'checks':r['checks'],'exception':r.get('exception')}),flush=True)
report['status']='PASS' if len(report['results'])==2 and all(r['status']=='PASS' for r in report['results']) else 'FAIL';dump(E/'result.json',report)
