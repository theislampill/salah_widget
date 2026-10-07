#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT
from native_pixel_probes import MATERIAL_PROBE

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(reduced_motion='reduce')
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&method=4&simTime=23:30&simWx=0&simCloud=0&simPrecip=0'");page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load');page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  result=page.evaluate(MATERIAL_PROBE);b.close()
 (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['opaquePixels']>5000 and result['maxCodeDifference']<=1
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);args=a.parse_args();run(Path(args.root),Path(args.output))
