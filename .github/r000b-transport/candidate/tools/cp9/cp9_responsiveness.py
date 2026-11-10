#!/usr/bin/env python3
"""Actual-widget loaded heartbeat and scheduled native dialog latency, not a physics-only benchmark."""
from pathlib import Path
import argparse,json,time,traceback,hashlib
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_lifecycle_check import Widget,ROOT
MONITOR=r'''() => {window.__cp9Perf={gaps:[],clickLags:[],dialogs:0,start:performance.now()};let prev=performance.now();window.__cp9Timer=setInterval(()=>{const now=performance.now();__cp9Perf.gaps.push(now-prev);prev=now;},16);for(let i=1;i<=8;i++){const due=performance.now()+i*150;setTimeout(()=>{__cp9Perf.clickLags.push(performance.now()-due);document.querySelector('#ceDateButton').click();if(document.querySelector('#dateDialog').open)__cp9Perf.dialogs++;document.querySelector('#dateClose').click();},i*150);}}'''
def run(root,out):
 out.mkdir(parents=True,exist_ok=True);results=[]
 with sync_playwright() as p:
  browser=launch_browser(p)
  for mode in ['normal','constructor-failure']:
   w=Widget(browser,root,out,mode,worker=mode);entry={'mode':mode,'loadedHeartbeatBudgetMs':250}
   try:
    w.wait("window.realSkyState && ['ready','unavailable'].includes(realSkyState().status)",90000)
    w.proof_ui();w.page.wait_for_timeout(300);w.page.evaluate(MONITOR);t=time.monotonic()
    w.page.evaluate('()=>{SalahRealSky.request(true);}');w.page.wait_for_timeout(4000)
    record=w.page.evaluate('()=>{clearInterval(__cp9Timer);return {...__cp9Perf,sky:realSkyState(),rows:document.querySelectorAll(".p").length};}')
    s=record.pop('sky');g=record['gaps'];lags=record['clickLags'];entry.update({'seconds':time.monotonic()-t,'measurement':record,'maxGapMs':max(g,default=0),'p95GapMs':sorted(g)[int(len(g)*.95)] if g else None,'maxScheduledDialogLagMs':max(lags,default=0),'sky':{'status':s['status'],'errors':s['errors'],'execution':s.get('last',{}).get('execution') if s.get('last') else None,'timings':s.get('last',{}).get('timings') if s.get('last') else None},'responsive':bool(g) and max(g)<=250 and len(lags)==8 and max(lags)<=250 and record['dialogs']==8})
    w.page.locator('.c').screenshot(path=str(out/(mode+'.png')))
   except Exception:entry['error']=traceback.format_exc();entry['responsive']=False
   entry['pageErrors']=w.errors;w.finish();results.append(entry);(out/'results.json').write_text(json.dumps({'cases':results,'status':'PASS' if all(r['responsive'] and not r['pageErrors'] for r in results) else 'FAIL','runtimeSha256':hashlib.sha256((root/'real-sky/native-sky.js').read_bytes()).hexdigest()},indent=2));print(mode,entry.get('maxGapMs'),entry.get('maxScheduledDialogLagMs'),entry.get('sky'),flush=True)
  browser.close()
 return all(r['responsive'] and not r['pageErrors'] for r in results)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output) else 1)
