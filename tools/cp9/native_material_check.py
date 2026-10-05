#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(reduced_motion='reduce')
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&method=4&simTime=23:30&simWx=0&simCloud=0&simPrecip=0'");page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load');page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  result=page.evaluate('''()=>{
   SalahRealSky.compose();
   const target=document.querySelector('.real-sky-canvas'),rect=target.getBoundingClientRect(),photo=document.querySelector('.mphoto'),t=photo.getScreenCTM(),c=document.createElement('canvas');c.width=325;c.height=530;const x=c.getContext('2d');const sx=325/rect.width,sy=530/rect.height;
   x.setTransform(t.a*sx,t.b*sy,t.c*sx,t.d*sy,(t.e-rect.left)*sx,(t.f-rect.top)*sy);x.drawImage(_moonCv,-48,-48,96,96);
   const expected=x.getImageData(0,0,325,530).data,actual=target.getContext('2d').getImageData(0,0,325,530).data;let count=0,max=0,sum=0;
   for(let i=0;i<expected.length;i+=4)if(expected[i+3]===255){count++;for(let k=0;k<3;k++){const d=Math.abs(expected[i+k]-actual[i+k]);max=Math.max(max,d);sum+=d;}}
   return {opaquePixels:count,maxCodeDifference:max,meanAbsoluteCodeDifference:sum/(count*3),nativeBacking:[_moonCv.width,_moonCv.height],composition:realSkyState().last.composition,criterion:'All fully opaque native lunar material samples at clear-cloud transmission must survive shared inverse/forward encoding to <=1 code value.'};
  }''');b.close()
 (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['opaquePixels']>5000 and result['maxCodeDifference']<=1
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);args=a.parse_args();run(Path(args.root),Path(args.output))
