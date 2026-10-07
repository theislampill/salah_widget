#!/usr/bin/env python3
"""Exercise the adapted donor dirty-input optimisation in the actual widget."""
from pathlib import Path
import argparse,json,traceback,hashlib
from browser_runtime import launch_browser,browser_identity
from playwright.sync_api import sync_playwright
from native_lifecycle_check import Widget,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);ident=browser_identity(b);w=Widget(b,root,out,'presentation');error=None
  try:
   w.ready();w.page.wait_for_timeout(1000);w.page.evaluate('()=>SalahRealSky.compose()');before=w.page.evaluate('realSkyState()')
   w.page.evaluate('()=>{for(let i=0;i<6;i++)SalahRealSky.compose();}');stable=w.page.evaluate('realSkyState()');w.check(stable['presentationSkips']-before['presentationSkips']>=6,'Six identical snapshots skip only redundant presentation work')
   w.page.evaluate('()=>{let c=document.querySelector(".cloudcanvas");window.__savedCloudVisibility=[c.style.getPropertyValue("visibility"),c.style.getPropertyPriority("visibility")];c.style.setProperty("visibility","collapse","important");SalahRealSky.compose();}')
   freshmeta=w.page.evaluate('realSkyState()');w.check(freshmeta['composition']['cloudSource']=='collapse' if 'composition' in freshmeta else freshmeta['last']['composition']['cloudSource']=='collapse','Capture diagnostics stay fresh when pixel bytes are unchanged')
   w.page.evaluate('()=>{let c=document.querySelector(".cloudcanvas");c.style.removeProperty("visibility");if(__savedCloudVisibility[0])c.style.setProperty("visibility",...__savedCloudVisibility);SalahRealSky.compose();}')
   w.page.evaluate('()=>{const c=SalahNativeSkyHost.lunarSurface();window.__moonSaved=c.getContext("2d").getImageData(0,0,c.width,c.height);const x=c.getContext("2d");x.fillStyle="rgba(200,40,20,1)";x.fillRect(130,130,30,30);SalahRealSky.compose();}')
   moon=w.page.evaluate('realSkyState()');w.check(moon['presentationDraws']>stable['presentationDraws'],'Native PBR byte change forces repaint');w.page.evaluate('()=>{SalahNativeSkyHost.lunarSurface().getContext("2d").putImageData(__moonSaved,0,0);SalahRealSky.compose();}')
   before=w.page.evaluate('realSkyState()');w.page.evaluate('()=>{let d=document.querySelector(".moon-mask-disc");window.__savedRadius=d.getAttribute("r");d.setAttribute("r",Number(__savedRadius)+10);SalahRealSky.compose();}');geometry=w.page.evaluate('realSkyState()');w.check(geometry['presentationDraws']>before['presentationDraws'],'Calendar geometry change forces repaint even when cloud/PBR bytes match');w.page.evaluate('()=>{document.querySelector(".moon-mask-disc").setAttribute("r",__savedRadius);SalahRealSky.compose();}')
   before=w.page.evaluate('realSkyState()');w.page.evaluate('()=>{let c=document.querySelector(".cloudcanvas"),x=c.getContext("2d");window.__cloudSaved=x.getImageData(0,0,c.width,c.height);x.fillStyle="rgba(80,70,60,0.8)";x.fillRect(20,20,50,40);SalahRealSky.compose();}');cloud=w.page.evaluate('realSkyState()');w.check(cloud['presentationDraws']>before['presentationDraws'],'Cloud colour/opacity change forces repaint');w.page.evaluate('()=>{document.querySelector(".cloudcanvas").getContext("2d").putImageData(__cloudSaved,0,0);SalahRealSky.compose();}')
   before=w.page.evaluate('realSkyState()');w.request();w.wait('realSkyState().renders>'+str(before['renders']));fresh=w.page.evaluate('realSkyState()');w.check(fresh['presentationDraws']>before['presentationDraws'],'A new worker frame is not skipped for matching foreground bytes');w.proof_ui();w.snap('restored-normal')
  except Exception:error=traceback.format_exc();print(error,flush=True)
  report=w.finish(error);report.update(status='PASS' if report['passed'] else 'FAIL',browser=ident,runtimeSha256=hashlib.sha256((root/'real-sky/native-sky.js').read_bytes()).hexdigest(),scope='Actual widget. Temporary native backing-canvas and mask mutations are controlled tests, restored before final screenshot; not product artwork. All previous currentness gates remain ahead of the exact unchanged-input guard.');b.close()
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output)['status']=='PASS' else 1)
