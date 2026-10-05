#!/usr/bin/env python3
"""Bounded actual cloud-pixel continuity observation, not a qaState hash claim."""
import argparse,json
from pathlib import Path
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(viewport={'width':400,'height':600},reduced_motion='no-preference');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&method=4&simTime=23:30&simWx=2&simCloud=65&simPrecip=0&motion=full&timeScale=1'")
  page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load');page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  page.screenshot(path=str(out/'start.png'))
  result=page.evaluate('''()=>new Promise(resolve=>{
   const start=performance.now(),samples=[],heartbeats=[],began=realSkyState().renders;let last=0,lastBeat=start;
   function hash(a,stride){let h=2166136261;for(let i=0;i<a.length;i+=stride){h=Math.imul(h^a[i],16777619);}return h>>>0;}
   function tick(t){heartbeats.push(t-lastBeat);lastBeat=t;if(t-last>50){last=t;
    const native=document.querySelector('.cloudcanvas'),painted=document.querySelector('.real-sky-canvas');
    const n=native.getContext('2d').getImageData(0,0,native.width,native.height).data,f=painted.getContext('2d').getImageData(0,0,325,183).data;
    let a=0,cy=0;for(let i=3;i<n.length;i+=4){a+=n[i];cy+=n[i]*Math.floor((i/4)/native.width);}
    samples.push({ms:t-start,nativePixelHash:hash(n,4),finalPixelHash:hash(f,16),nativeAlpha:a,centroidY:cy/a,compositionMs:realSkyState().last.composition.lastComposeMs});
   }if(t-start<8000)requestAnimationFrame(tick);else resolve({samples,heartbeatMs:heartbeats,renderJobs:realSkyState().renders-began,utcMs:realSkyState().last.utcMs,reducedMotion:SalahNativeSkyHost.capture().reducedMotion,source:'Actual native cloud backing pixels and final composed canvas pixels, sampled during normal rAF playback; sampling overhead included.'});}
   requestAnimationFrame(tick);
  })''')
  page.screenshot(path=str(out/'end.png'));b.close()
 result['nativeDistinct']=len({x['nativePixelHash'] for x in result['samples']});result['finalDistinct']=len({x['finalPixelHash'] for x in result['samples']});result['pageErrors']=errors
 (out/'results.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['samples','heartbeatMs']})
 assert not errors and result['nativeDistinct']>=12 and result['finalDistinct']>=12 and result['reducedMotion'] is False
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(ROOT));a.add_argument('--output',required=True);x=a.parse_args();run(Path(x.root),Path(x.output))
