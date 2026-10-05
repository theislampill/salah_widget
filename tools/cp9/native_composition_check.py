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

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  b=launch_browser(p);page=b.new_page(viewport={'width':700,'height':720},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://fonts.googleapis.com/**',lambda r:r.abort());page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  page.evaluate("location.hash='lat=24.47&lon=39.61&tz=Asia/Riyadh&method=4&simTime=23:30&simWx=2&simCloud=60&simPrecip=0'")
  page.evaluate(INIT);page.set_content((root/'offline.html').read_text(encoding='utf-8'),wait_until='load');page.wait_for_function("window.realSkyState?.().status==='ready'",timeout=90000)
  # Reuse only the capture and coordinate boundary; the pixel equation below is independent.
  helpers='\n'.join((root/'real-sky'/s).read_text(encoding='utf-8').replace('export ','') for s in ['native-composition.mjs','native-contract.mjs'])
  page.evaluate('(()=>{'+helpers+';window.__fullCapture=new NativeForegroundCapture(document.querySelector(".real-sky-canvas"));window.__mask=nativeDiscMask;})()')
  check=r'''()=>{
   const times=[];for(let n=0;n<6;n++){const t=performance.now();SalahRealSky.compose();times.push(performance.now()-t);}
   const target=document.querySelector('.real-sky-canvas'),actual=target.getContext('2d').getImageData(0,0,325,530).data,r=realSkyFrame().raster,E=r.effectiveExposure,C=__fullCapture.capture(),disc=document.querySelector('.moon-mask-disc'),matrix=disc.getScreenCTM();
   const mask=disc.classList.contains('mask-on')&&+getComputedStyle(disc).opacity!==0?__mask(325,530,target.getBoundingClientRect(),matrix,+disc.getAttribute('r')):null;
   const inv=Array.from({length:256},(_,i)=>{const q=i/255,s=q<=.04045?q/12.92:((q+.055)/1.055)**2.4;return -Math.log1p(-Math.min(1-1/131072,s))/E;});
   const code=L=>{const v=-Math.expm1(-E*Math.max(0,L));return Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055));};
   let max=0,changed=0,doubleT=0,doubleColour=0,wrongOrder=0,outsideCloud=0,cutDirectPixels=0,caSum=0;
   for(let p=0;p<325*530;p++){
    const a=C.cloudRGBA[p*4+3]/255,T=1-a,m=C.moonRGBA[p*4+3]/255,k=mask?mask[p]:1;caSum+=a;if(p>=325*183&&a)outsideCloud++;
    if(k<1)cutDirectPixels++;
    for(let c=0;c<3;c++){
     const i=p*3+c,j=p*4+c,sky=(r.skyBackgroundLinear??r.backgroundLinear)[i],direct=r.stellarLinear[i]+(r.diffusePhysicalLinear?.[i]??0),base=sky+direct*k;
     const moon=inv[C.moonRGBA[j]],cloud=inv[C.cloudRGBA[j]],withMoon=base*(1-m)+moon*m;
     const expected=code(withMoon*T+cloud*a),d=Math.abs(expected-actual[j]);max=Math.max(max,d);if(d)changed++;
     if(code(withMoon*T*T+cloud*a)!==expected)doubleT++;
     if(code(withMoon*T+cloud*a*a)!==expected)doubleColour++;
     if(code((base*T+cloud*a)*(1-m)+moon*m)!==expected)wrongOrder++;
    }
   }
   return {timesMs:times,maxCodeDifference:max,differentChannels:changed,cloudAlphaMean:caSum/(325*530),cloudOutsideDeclaredSupport:outsideCloud,calendarCutoutPixels:cutDirectPixels,mutations:{doubleTransmission:doubleT,doubleColourAlpha:doubleColour,moonAfterCloud:wrongOrder},composition:realSkyState().last.composition,exposure:E,skyInputsUnchanged:r.diffuseState,criterion:'All 325×530 encoded pixels exactly equal the full-frame reference equation; all three deliberately wrong equations must disagree.'};
  }'''
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
