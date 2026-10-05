#!/usr/bin/env python3
"""Actual-widget worker/URL/canvas lifetime across eight explicit asset restarts.
GC-sampled main heap is bounded evidence only; not total-browser or worker memory.
"""
from pathlib import Path
import argparse,json,hashlib
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity,browser_options
from native_browser_check import ROOT,INIT
TRACK=r'''()=>{const W=Worker;window.__resources={workers:0,created:0,terminated:0,urls:new Set()};window.Worker=class extends W{constructor(...args){super(...args);this.__counted=true;__resources.workers++;__resources.created++;}terminate(){if(this.__counted){this.__counted=false;__resources.workers--;__resources.terminated++;}return super.terminate();}};const create=URL.createObjectURL.bind(URL),revoke=URL.revokeObjectURL.bind(URL);URL.createObjectURL=x=>{const u=create(x);__resources.urls.add(u);return u;};URL.revokeObjectURL=u=>{__resources.urls.delete(u);return revoke(u);};}'''

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 if browser_options()[0]!='chromium':raise RuntimeError('GC/heap control requires explicitly selected Chromium CDP; no substitute engine.')
 with sync_playwright() as p:
  b=launch_browser(p);ident=browser_identity(b);c=b.new_context(viewport={'width':430,'height':640},reduced_motion='reduce');page=c.new_page();page.route('**/*',lambda r:r.abort());errors=[];page.on('pageerror',lambda e:errors.append(str(e)));cdp=c.new_cdp_session(page);cdp.send('Performance.enable')
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Resource-cycle&method=4&simTime=23:30&simWx=2&simCloud=60&simPrecip=0&qa=1'");page.evaluate(INIT);page.evaluate(TRACK);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load',timeout=90000);samples=[]
  for i in range(9):
   if i:page.evaluate('()=>SalahRealSkyAssets.retry()')
   page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000);page.wait_for_timeout(150);cdp.send('HeapProfiler.collectGarbage');metrics={m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics']};s=page.evaluate('()=>({generation:SalahRealSkyAssets.state.generation,workers:__resources.workers,created:__resources.created,terminated:__resources.terminated,urls:__resources.urls.size,canvases:document.querySelectorAll(".real-sky-canvas").length,prayerRows:document.querySelectorAll(".p").length,status:realSkyState().status})');s.update(cycle=i,mainHeapUsedBytes=metrics['JSHeapUsedSize']);samples.append(s);print(i,s,flush=True)
  page.evaluate('()=>SalahRealSkyAssets.dispose()');cdp.send('HeapProfiler.collectGarbage');disposed=page.evaluate('()=>({workers:__resources.workers,urls:__resources.urls.size,canvases:document.querySelectorAll(".real-sky-canvas").length,prayerRows:document.querySelectorAll(".p").length})');b.close()
 growth=samples[-1]['mainHeapUsedBytes']-samples[1]['mainHeapUsedBytes'];stable=all(s['workers']==1 and s['urls']==1 and s['canvases']==1 and s['prayerRows']==6 for s in samples) and disposed=={'workers':0,'urls':0,'canvases':0,'prayerRows':6}
 result={'status':'PASS' if stable and not errors and growth<=8*1024*1024 else 'FAIL','browser':ident,'samples':samples,'disposed':disposed,'mainHeapGrowthSinceFirstRestartBytes':growth,'growthBudgetBytes':8*1024*1024,'pageErrors':errors,'runtimeSha256':hashlib.sha256((root/'real-sky/native-sky.js').read_bytes()).hexdigest(),'scope':'One initial frame and eight restarts of the actual inline native widget. Tracked Worker/Blob-URL/canvas lifetime and CDP main-heap samples after forced GC. A bounded 8 MiB growth target, not a proof against all long-session leaks. Typed Array backing-store, worker/GPU/process memory are not JSHeapUsedSize.'};(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output)['status']=='PASS' else 1)
