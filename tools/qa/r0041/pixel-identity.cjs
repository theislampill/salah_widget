'use strict';
// R0041 (issue 143): healthy-path pixel identity between two trees. Native recipe; NOT part of the node glob.
// The page clock is FROZEN at <instantISO> (Date.now() returns a constant), so both trees compute the same ephemeris
// and scene; reduced motion; synthetic fixture (lat 24.47, lon 39.61); launch through iso.cjs (loopback only).
// For each tree: load, wait for the settled refined Moon, screenshot; then hide 1 s and show (synthetic visibility
// events, the same in both trees), wait for the refined Moon again, screenshot. The first tree is loaded TWICE, so the
// run-to-run noise floor of the comparison is measured, not assumed.
// Reports, per pair of screenshots: differing pixels and largest channel difference over the whole card and over the
// Moon slot (the .mphoto rectangle). Identity is claimed only for a pair with zero differing pixels.
// Usage: node pixel-identity.cjs <treeA> <treeB> <outJson> <engine> <instantISO> [label]
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [treeA,treeB,outFile,engine,instantISO,label]=process.argv.slice(2);
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const FREEZE=`(()=>{const ND=Date,at=${Date.parse(instantISO)};class D extends ND{constructor(...a){super(...(a.length?a:[at]));}static now(){return at;}}window.Date=D;})();`;
const HIDE=h=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>h});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>h?'hidden':'visible'});document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));};
async function capture(root){
  const env=await createEnv({root});const L=await launch(env,{engine,mode:'route',reducedMotion:'reduce'});const r={root:path.basename(root)};
  try{await L.context.addInitScript(FREEZE);const page=await L.context.newPage();
    await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'load'});
    const settled=()=>page.waitForFunction(()=>{const o=window.SalahMoonRuntime?.observe?.();return o?.current&&o.state.visibleSource==='refined-terrain'&&document.querySelector('.c')?.classList.contains('real-sky-composed');},null,{timeout:150000,polling:250});
    await settled();await page.waitForTimeout(8000);   // the first load keeps settling (reveal transitions) for some seconds
    r.rect=await page.evaluate(()=>{const b=document.querySelector('.mphoto').getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};});
    r.truth=await page.evaluate(()=>{const t=window.qaState().moonTruth;return {phaseFraction:t.phaseFraction,alt:t.moonAltitudeDeg,displayMode:t.displayMode,status:t.surface.status,moonlightOpacity:t.moonlightOpacity};});
    r.settled=decodePng(await page.screenshot({type:'png'}));
    await page.evaluate(HIDE,true);await page.waitForTimeout(1000);await page.evaluate(HIDE,false);
    await settled();await page.waitForTimeout(2500);r.resumed=decodePng(await page.screenshot({type:'png'}));
  }finally{await L.close().catch(()=>{});}
  r.allowedExternal=env.finish().allowedExternal;return r;
}
function compare(a,b,rect){
  const ch=a.data.length/(a.width*a.height),out={card:{pixels:a.width*a.height,differing:0,maxChannelDifference:0},moonSlot:{pixels:0,differing:0,maxChannelDifference:0}};
  if(a.width!==b.width||a.height!==b.height)return {error:'size'};
  const x0=Math.max(0,Math.floor(rect.x)),y0=Math.max(0,Math.floor(rect.y)),x1=Math.min(a.width,Math.ceil(rect.x+rect.w)),y1=Math.min(a.height,Math.ceil(rect.y+rect.h));
  for(let y=0;y<a.height;y++)for(let x=0;x<a.width;x++){let d=0;const i=ch*(y*a.width+x);for(let k=0;k<3;k++)d=Math.max(d,Math.abs(a.data[i+k]-b.data[i+k]));
    const slot=x>=x0&&x<x1&&y>=y0&&y<y1;if(slot)out.moonSlot.pixels++;
    if(d){out.card.differing++;out.card.maxChannelDifference=Math.max(out.card.maxChannelDifference,d);if(slot){out.moonSlot.differing++;out.moonSlot.maxChannelDifference=Math.max(out.moonSlot.maxChannelDifference,d);}}}
  return out;
}
(async()=>{
  const a1=await capture(treeA),a2=await capture(treeA),b=await capture(treeB);
  const out={schema:'r0041-pixel-identity/1',label:label??null,engine,instantISO,frozenClock:true,motion:'reduce',treeA:a1.root,treeB:b.root,truth:{A:a1.truth,B:b.truth},rect:a1.rect,
    allowedExternal:[a1.allowedExternal,a2.allowedExternal,b.allowedExternal],
    noiseFloor_A_vs_A:{settled:compare(a1.settled,a2.settled,a1.rect),afterHideAndShow:compare(a1.resumed,a2.resumed,a1.rect)},
    A_vs_B:{settled:compare(a1.settled,b.settled,a1.rect),afterHideAndShow:compare(a1.resumed,b.resumed,a1.rect)},
    withinTree:{A_settled_vs_afterHideAndShow:compare(a1.settled,a1.resumed,a1.rect),B_settled_vs_afterHideAndShow:compare(b.settled,b.resumed,b.rect)}};
  const z=c=>c.card.differing===0;
  out.identical={settled:z(out.A_vs_B.settled),afterHideAndShow:z(out.A_vs_B.afterHideAndShow)};
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));console.log(JSON.stringify({label,identical:out.identical,noise:out.noiseFloor_A_vs_A,AB:out.A_vs_B,truth:out.truth,allowed:out.allowedExternal}));
  if(out.allowedExternal.some(v=>v!==0))process.exit(1);
})().catch(e=>{console.error(e);process.exit(1);});
