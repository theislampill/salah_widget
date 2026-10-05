#!/usr/bin/env python3
"""Matched native-baseline/CP9 interactive timings; explicit CPU throttling is a stress fixture, not a device claim."""
from pathlib import Path
import argparse,json,time,traceback,hashlib,statistics
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT
from cp9_responsiveness import MONITOR

def run(root,out,trials=2):
 out.mkdir(parents=True,exist_ok=True);cases=[]
 with sync_playwright() as p:
  browser=launch_browser(p)
  for baseline,throttle,reduced in [(True,1,False),(False,1,False),(False,1,True),(True,4,False),(False,4,False),(False,4,True)]:
   name=('baseline' if baseline else 'cp9')+f'-cpu{throttle}-'+('reduced' if reduced else 'motion');c=browser.new_context(viewport={'width':430,'height':640},reduced_motion='reduce' if reduced else 'no-preference');page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda route:route.abort());cdp=c.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':throttle});cdp.send('Performance.enable');entry={'name':name,'baseline':baseline,'cpuThrottle':throttle,'reducedMotion':reduced,'heartbeatBudgetMs':250}
   try:
    page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Performance&method=4&simTime=23:30&timeScale=1&simWx=2&simCloud=60&simPrecip=0&qa=1&motion="+('reduced' if reduced else 'full')+"'");page.evaluate(INIT)
    page.evaluate("()=>{window.__cold={long:[],t:performance.now()};new PerformanceObserver(l=>__cold.long.push(...l.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({type:'longtask',buffered:true});}")
    source=(root/('src/native/index.html' if baseline else 'offline.html')).read_text(encoding='utf-8')
    if baseline:source=source.replace('<script src="config.js"></script>','<script>'+(root/'src/native/config.js').read_text(encoding='utf-8').replace('</script','<\\/script')+'</script>')
    start=time.monotonic();page.set_content(source,wait_until='load',timeout=90000);page.wait_for_function("document.querySelectorAll('.p').length===6&&document.querySelector('.c').classList.contains('moon-ready')",timeout=90000)
    entry['prayerAndMoonSeconds']=time.monotonic()-start
    if not baseline:page.wait_for_function("realSkyState()?.status==='ready'",timeout=90000)
    entry['skyReadySeconds']=time.monotonic()-start;entry['coldLongTasks']=page.evaluate('__cold.long');page.wait_for_timeout(500)
    measurements=[]
    for trial in range(trials):
     page.evaluate(MONITOR)
     if not baseline:page.evaluate('()=>{SalahRealSky.request(true);}')
     page.wait_for_timeout(5000)
     r=page.evaluate('()=>{clearInterval(__cp9Timer);return {...__cp9Perf,rows:document.querySelectorAll(".p").length,sky:window.realSkyState?.()};}')
     sky=r.pop('sky',None);g=r['gaps'];lag=r['clickLags'];measurements.append({'trial':trial,'maxGapMs':max(g,default=0),'p95GapMs':sorted(g)[int(len(g)*.95)] if g else None,'medianGapMs':statistics.median(g) if g else None,'maxScheduledDialogLagMs':max(lag,default=0),'dialogs':r['dialogs'],'rows':r['rows'],'sampleCount':len(g),'execution':sky.get('last',{}).get('execution') if sky and sky.get('last') else None,'timings':sky.get('last',{}).get('timings') if sky and sky.get('last') else None,'composition':sky.get('last',{}).get('composition') if sky and sky.get('last') else None,'status':sky.get('status') if sky else None})
    entry['trials']=measurements;entry['loadedResponsive']=all(m['maxGapMs']<=250 and m['maxScheduledDialogLagMs']<=250 and m['dialogs']==8 and m['rows']==6 for m in measurements)
    entry['metrics']={m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics'] if m['name'] in ['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents','LayoutCount','TaskDuration']}
    if not baseline:entry['rasterBuffers']=page.evaluate("()=>{const seen=new Set();let total=0;function walk(x){if(!x||typeof x!=='object')return;if(ArrayBuffer.isView(x)){if(!seen.has(x.buffer)){seen.add(x.buffer);total+=x.buffer.byteLength;}return;}for(const v of Object.values(x))walk(v);}walk(realSkyFrame()?.raster);return {uniqueBytes:total,buffers:seen.size,scope:'Current retained CPU raster arrays only; excludes DOM, textures, worker heap and browser process memory'};}")
    page.locator('.c').screenshot(path=str(out/(name+'.png')))
   except Exception:entry['error']=traceback.format_exc();entry['loadedResponsive']=False;print(entry['error'],flush=True)
   entry['pageErrors']=errors;entry['sourceSha256']=hashlib.sha256((root/('src/native/index.html' if baseline else 'index.html')).read_bytes()).hexdigest();cases.append(entry);c.close();(out/'results.json').write_text(json.dumps({'status':'RUNNING','cases':cases},indent=2));print(name,entry.get('skyReadySeconds'),[m['maxGapMs'] for m in entry.get('trials',[])],entry['loadedResponsive'],flush=True)
  version=browser.version;browser.close()
 report={'status':'MEASURED','browser':version,'trialsPerCondition':trials,'candidateBudgetStatus':'PASS' if all(c['loadedResponsive'] for c in cases if not c['baseline']) else 'NOT_ALL_PASSED','baselineBudgetStatus':'PASS' if all(c['loadedResponsive'] for c in cases if c['baseline']) else 'NOT_ALL_PASSED','cases':cases,'budgetStatus':'PASS' if all(c['loadedResponsive'] for c in cases) else 'NOT_ALL_PASSED','scope':'Explicitly selected Chromium on the recorded execution host, explicit number of loaded trials per condition. CPU×4 is synthetic stress, not a Windows/mobile model. Baseline comparison separates existing native cost from optional joined cost. Main JS heap metrics exclude worker and GPU/process memory.'};(out/'results.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);a.add_argument('--trials',type=int,default=2,choices=range(1,21));x=a.parse_args();run(x.root,x.output,x.trials)
