"""One direct Pages followup for the observed pending Firefox Moon surface."""
from pathlib import Path
import json,sys,time,traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from close_r0024 import ROOT,RUN,POST,PAGES,sha,read,now
from delivered_native import base,actual_ax
out=POST/'native/firefox-ordinary-ready';out.mkdir(exist_ok=False)
cap=read(RUN/'native/firefox/resume-r6/results.json')['capability']
import playwright._impl._transport as transport
transport.compute_driver_executable=lambda:(cap['driver']['node'],cap['driver']['cli'])
from playwright.sync_api import sync_playwright
lock=RUN/'native/native-resource.lock';f=lock.open('x');f.write('R0024 one direct Firefox maturity readback');f.close()
result={'schema':'r0024-direct-delivery-maturity/v1','sourceSha256':'402a8f247e1375c23e8877fc4219e2c4d254b60abee7b6f801d8c05ca801554c','merge':read(POST/'merge-readback.json')['merge'],'startedUtc':now(),'adapterSha256':sha(Path(__file__).read_bytes()),'observations':[],'scope':'Observed pending direct Firefox terrain acquisition followup only. No source/clock/provider/bridge substitution, no initial Moon-ready, continuous-video, performance or new scientific qualification claim.'}
try:
  with sync_playwright()as pw:
    browser=pw.firefox.launch(headless=True,executable_path=cap['executable'])
    try:
      context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='Asia/Riyadh');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
      url=PAGES+'index.html#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c';start=time.monotonic();r=page.goto(url,wait_until='domcontentloaded',timeout=60000);assert r.status==200 and sha(r.body())==result['sourceSha256']
      base.wait(page,"()=>typeof qaState==='function'&&document.querySelector('#weather-information')?.textContent.length>0",timeout=45000)
      while True:
        observation=page.evaluate("()=>({moon:qaState().moonTruth,description:document.querySelector('#weather-information').textContent,noBridge:typeof __widgetFixture==='undefined'})")
        observation['elapsedSec']=time.monotonic()-start;result['observations'].append(observation)
        if observation['moon']['calendarMoonVisible']or observation['moon']['physicalMoonVisible']:break
        if observation['elapsedSec']>=60:break
        page.wait_for_timeout(1000)
      for selector,name in [('.c','card'),('.h','header'),('.d','footer')]:page.locator(selector).screenshot(path=str(out/(name+'.png')))
      result.update(url=url,accessibility=actual_ax(page,'firefox'),pageErrors=errors,final=observation)
      result['status']='MATURE_SURFACE_CAPTURED_PENDING_PIXEL_REVIEW'if observation['moon']['calendarMoonVisible']or observation['moon']['physicalMoonVisible']else'RETAINED_PENDING_SURFACE_AFTER60S'
      context.close()
    finally:browser.close()
except Exception:result.update(status='FAIL',exception=traceback.format_exc())
finally:lock.unlink()
result['finishedUtc']=now();(out/'receipt.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'observedSec':result.get('final',{}).get('elapsedSec')}))
