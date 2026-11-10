#!/usr/bin/env python3
"""CP9 accepted-height handoff, reversible page lifecycle and viewport controls on the actual native app."""
from pathlib import Path
import argparse,json,time,traceback,hashlib
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_lifecycle_check import Widget,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True);results=[]
 with sync_playwright() as p:
  browser=launch_browser(p)
  def case(name,fn,**kw):
   w=Widget(browser,root,out,name,**kw);t=time.monotonic();error=None
   try:fn(w)
   except Exception:error=traceback.format_exc();print(error,flush=True)
   try:
    if error:w.snap('failure')
   except Exception:pass
   r=w.finish(error);r['seconds']=time.monotonic()-t;results.append(r);(out/'results.json').write_text(json.dumps({'status':'RUNNING','cases':results},indent=2));print(name,r['passed'],r['seconds'],flush=True)
  def page_return(w):
   w.ready();w.hold_job();old=w.page.evaluate('SalahRealSkyAssets.state.generation')
   w.page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
   s=w.snap('suspended');w.check(s['assets']['status']=='suspended' and s['canvasCount']==0,'Pagehide withdraws sky/worker');w.check(w.page.evaluate('__workerControl.instances.every(x=>x.terminated)'),'All previous workers terminated')
   w.release_job();w.page.wait_for_timeout(100);w.check(w.page.evaluate('realSkyFrame()===null'),'Late worker result cannot resurrect suspended frame');w.proof_ui()
   w.page.evaluate("()=>{_simBase+=3600000;render();window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));}");w.ready();s=w.snap('restored-current');w.check(s['assets']['generation']>old and s['canvasCount']==1,'Exactly one new generation and renderer');w.check(s['sky']['last']['utcMs']==s['host']['utcMs'],'Restored sky uses new native time')
   w.page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))");w.page.wait_for_timeout(100);w.check(w.page.evaluate('document.querySelectorAll(".real-sky-canvas").length===1'),'Repeated pageshow does not duplicate host')
   w.page.evaluate("()=>{SalahRealSkyAssets.dispose();window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));}");w.check(w.page.evaluate("SalahRealSkyAssets.state.status==='disposed'&&document.querySelectorAll('.real-sky-canvas').length===0"),'Explicit disposal remains terminal')
  case('pagehide-pageshow-inflight',page_return)
  def slow_return(w):
   w.wait("SalahRealSkyAssets.state.status==='loading'");w.page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))");w.release_asset();w.page.wait_for_timeout(100);s=w.snap('obsolete-asset-after-pagehide');w.check(s['assets']['status']=='suspended' and s['canvasCount']==0,'Late asset cannot create renderer while suspended');w.page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))");w.ready();w.proof_ui();w.snap('asset-restored')
  case('pagehide-pending-asset',slow_return,asset='slow')
  def height(w):
   w.ready();w.proof_ui()
   # A complete response enters the original wxFetchJson/admitWeatherRecord/attemptEligible path.
   w.page.evaluate(r'''async()=>{
    const original=fetch;window.__heightReply=900;
    window.fetch=async(u,o)=>{const x=new URL(typeof u==='string'?u:u.url);if(x.hostname!=='api.open-meteo.com')return original(u,o);return new Response(JSON.stringify({timezone:tz,elevation:__heightReply,current:{time:'2026-09-07T23:30',interval:900,weather_code:0,temperature_2m:20,relative_humidity_2m:40,visibility:20000,cloud_cover:0}}),{status:200,headers:{'Content-Type':'application/json'}});};
    SIM.wx=null;weather=null;weatherTrack=null;lastWxTry=0;await fetchWeather();render();SalahRealSky.request(true);
   }''')
   w.wait('SalahNativeSkyHost.capture().heightM===900');w.ready();s=w.snap('A-provider-height');w.check(s['sky']['last']['observer']['heightM']==900,'Actual native weather adoption reaches astronomy')
   gen=s['host']['generation'];w.target(-33.87,151.21,'Australia/Sydney','B');w.page.evaluate("()=>{SIM.wx=2;weather={src:'sim',vis:20000};render();SalahRealSky.request(true);}");w.ready();s=w.snap('B-no-bound-height');w.check(s['host']['heightM']==0,'Simulated B does not inherit A provider height');w.check('default zero' in s['host']['elevationSource'],'Unknown zero labelled')
   w.page.evaluate('(g)=>SalahNativeSkyHost.acceptedElevation(900,g,24.47,39.61)',gen);w.check(w.page.evaluate('SalahNativeSkyHost.capture().heightM===0'),'Late A handoff refused')
   w.page.evaluate('()=>{SalahNativeSkyHost.acceptedElevation(0,_runtimeGeneration,lat,lon);SalahRealSky.request(true);}');w.ready();s=w.snap('B-known-zero');w.check(s['host']['heightM']==0 and s['host']['elevationOwner'] is not None,'Known zero has explicit owner')
   w.page.evaluate('()=>{SalahNativeSkyHost.acceptedElevation(56,_runtimeGeneration,lat,lon);SalahRealSky.request(true);}');w.ready();s=w.snap('B-valid-height');w.check(s['sky']['last']['observer']['heightM']==56,'Valid B successor reaches physics');w.proof_ui()
   w.target(24.47,39.61,'Asia/Riyadh','A-return');w.ready();s=w.snap('A-return-default');w.check(s['host']['heightM']==0,'A return cannot revive previous generation height')
  case('native-elevation-adoption',height)
  def resize(w):
   w.ready();first=w.page.evaluate('realSkyState().last.utcMs')
   for width,height in [(350,620),(900,900),(430,640)]:
    w.page.set_viewport_size({'width':width,'height':height});w.page.wait_for_timeout(100);w.page.evaluate('()=>SalahRealSky.compose()');s=w.snap(f'resize-{width}');w.check(s['canvasCount']==1 and s['sky']['last']['utcMs']==first,'Resize does not create second clock/renderer');w.check(s['sky']['status']=='ready','Resize geometry remains drawable')
   w.proof_ui()
  case('resize-same-native-clock',resize)
  browser.close()
 report={'status':'PASS' if all(x['passed'] for x in results) else 'FAIL','cases':results,'assertions':sum(x['assertions'] for x in results),'runtimeSha256':hashlib.sha256((root/'real-sky/native-sky.js').read_bytes()).hexdigest(),'scope':'Actual widget, fixture provider response and controlled page transition events. Not a real navigation/BFCache or live weather provider certification.'};(out/'results.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output)['status']=='PASS' else 1)
