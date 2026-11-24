'use strict';
// R0041 (issue 143) preview-clear route, diagnostic recipe (NOT part of the node glob). Chromium headed, synthetic
// fixtures through iso.cjs (loopback only). Per clear: card classes, Moon-detail visibility/owner and SVG Moon visibility
// before SalahSkyPreview.clear, in the same task after it, and in the next 8 animation frames (SalahRealSky.invalidate
// 1.5 s earlier, as swp.cjs flag preview). Usage: node tools/qa/r0041/pc-probe.cjs <root> <dpr> <clears>
const path=require('node:path');
const [root,dprArg,nArg]=process.argv.slice(2);const DPR=+dprArg||2,N=+nArg||3;
const {createEnv,launch}=require('./iso.cjs');
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1&motion=full';
const startMs=Date.parse('2026-11-18T16:30:00Z');
const shift=ms=>`(()=>{const ND=Date,sys=ND.now.bind(ND),off=${ms}-sys();window.__sysNow=sys;class D extends ND{constructor(...a){super(...(a.length?a:[sys()+off]));}static now(){return sys()+off;}}window.Date=D;})();`;
(async()=>{
 const env=await createEnv({root});
 const L=await launch(env,{engine:'chromium',mode:'route',headless:false,deviceScaleFactor:DPR,reducedMotion:'no-preference',extraArgs:DPR>1?['--force-device-scale-factor='+DPR]:[]});
 const out=[];
 try{
  await L.context.addInitScript(shift(startMs));
  const page=await L.context.newPage();
  await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'load',timeout:120000});
  await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:240000,polling:250});
  await page.waitForTimeout(3000);
  for(let k=0;k<N;k++){
   await page.evaluate(()=>window.SalahRealSky?.invalidate('probe'));
   await page.waitForTimeout(1500);
   const r=await page.evaluate(()=>new Promise(res=>{
    const st=()=>{const c=document.querySelector('.c'),d=window.SalahMoonDetail?.state,cv=document.querySelector('.moon-detail-canvas'),m=document.querySelector('.mphoto'),pv=document.querySelector('.real-sky-preview'),rs=document.querySelector('.real-sky-canvas');
     return {t:Math.round(performance.now()),composed:c.classList.contains('real-sky-composed'),ready:c.classList.contains('real-sky-preview-ready'),detailVis:d?.visible,owner:d?.skyOwner,renders:d?.renders,mphoto:m&&getComputedStyle(m).visibility,mphotoHref:!!(m&&(m.getAttribute('href')||m.getAttribute('xlink:href'))),moonReady:c.classList.contains('moon-ready'),pv:pv&&pv.style.visibility,rs:rs&&rs.style.visibility,previewStatus:window.SalahSkyPreview?.state?.status,detailEnabled:null,presentable:window.SalahMoonRuntime?.presentable};};
    const log=[{phase:'before',...st()}];window.SalahSkyPreview.clear('probe');log.push({phase:'sync-after',...st()});
    let n=0;const f=()=>{log.push({phase:'raf'+n,...st()});if(++n<8)requestAnimationFrame(f);else res(log);};requestAnimationFrame(f);}));
   out.push(r);
   await page.waitForTimeout(5000);
  }
 }finally{await L.close().catch(()=>{});}
 const iso=env.finish();
 console.log(JSON.stringify({allowedExternal:iso.allowedExternal,out},null,0));
})().catch(e=>{console.error(e);process.exit(1);});
