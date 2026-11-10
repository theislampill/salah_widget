#!/usr/bin/env python3
"""Actual native pixels vs an independently written full-frame composition equation.
The production row-restricted path is compared to this unoptimised full-frame oracle.
External provider/time controls belong only to this harness, never the delivered app.
"""
import argparse,json,re
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT
from native_pixel_probes import COMPOSITION_PROBE,install_composition_probe

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(viewport={'width':700,'height':720},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&method=4&simTime=23:30&simWx=2&simCloud=60&simPrecip=0'")
  page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load');page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  # Reuse only the capture and coordinate boundary; the pixel equation below is independent.
  install_composition_probe(page,root)
  check=COMPOSITION_PROBE
  result=page.evaluate(check);page.screenshot(path=str(out/'cloud-joined.png'))
  # Moving both native display geometries below the cloud band is a test fixture,
  # not a change of physical Moon ephemeris. Old support must clear after return.
  movement=[]
  for y in [340,64]:
   page.evaluate('y=>{for(const sel of [".moon",".moon-mask-geometry"]){const e=document.querySelector(sel);e.style.transition="none";e.setAttribute("transform",`translate(250 ${y}) scale(.62)`);}}',y)
   movement.append(page.evaluate(check))
  result['movingNativeGeometry']=movement;result['pageErrors']=errors
  b.close()
 (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['skyInputsUnchanged','movingNativeGeometry']},indent=2))
 assert not errors and result['maxCodeDifference']==0 and result['cloudOutsideDeclaredSupport']==0
 assert all(v>100 for v in result['mutations'].values())
 assert all(x['maxCodeDifference']==0 for x in movement)
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);args=a.parse_args();run(Path(args.root),Path(args.output))
