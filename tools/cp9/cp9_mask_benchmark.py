#!/usr/bin/env python3
"""Exact CP8.3 versus CP9 Moon masks using a real native SVG DOMMatrix."""
from pathlib import Path
import argparse,json,hashlib
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity
from native_lifecycle_check import Widget,ROOT

def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 old=(root/'tools/cp9/fixtures/native-disc-mask-cp83.mjs').read_text(encoding='utf-8');old=old[old.index('export function'):].replace('export function','function',1)
 new=(root/'real-sky/native-contract.mjs').read_text(encoding='utf-8');new=new[new.index('export function nativeDiscMask'):].replace('export function','function',1)
 with sync_playwright() as p:
  b=launch_browser(p);identity=browser_identity(b);w=Widget(b,root,out,'mask');w.ready();w.page.evaluate('()=>{window.__maskOld=('+old+');window.__maskNew=('+new+');}')
  result=w.page.evaluate('''()=>{const c=document.querySelector('.real-sky-canvas'),r=c.getBoundingClientRect(),el=document.querySelector('.moon-mask-disc'),m=el.getScreenCTM(),rows=realSkyState().last.composition.updatedRows,rect={left:r.left,top:r.top,width:r.width,height:r.height*rows/530},radius=Number(el.getAttribute('r')),cases=[];for(const variant of ['native','moved','sheared']){let matrix=variant==='native'?m:new DOMMatrix([m.a,m.b,m.c,m.d,m.e+23,m.f+11]);if(variant==='sheared'){matrix.b+=.2;matrix.c-=.15;}let old=[],next=[],max=0;for(let i=0;i<6;i++){let t=performance.now(),a=__maskOld(325,rows,rect,matrix,radius);old.push(performance.now()-t);t=performance.now();let z=__maskNew(325,rows,rect,matrix,radius);next.push(performance.now()-t);for(let j=0;j<a.length;j++)max=Math.max(max,Math.abs(a[j]-z[j]));}cases.push({variant,oldMs:old,newMs:next,maxMaskDifference:max,pixels:325*rows});}return {cases};}''')
  result.update(browser=identity,pageErrors=w.errors,status='PASS' if all(c['maxMaskDifference']==0 for c in result['cases']) and not w.errors else 'FAIL',scope='Same actual native SVG DOMMatrix and logical mask dimensions. Six paired calls each; no matrix/opacity/resolution/camera change. Numerical difference must be exactly zero. Per-call cost evidence, not whole-app stress-budget closure.');w.finish();b.close()
 (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output)['status']=='PASS' else 1)
