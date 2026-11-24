'use strict';
// R0041 (issue 143) row R41-LIM, native half: the lit side is unchanged at 30 instants in and around the census
// intervals. Native recipe; NOT part of the node glob. Chromium, headless, DPR 1, reduced motion, synthetic fixture,
// iso.cjs (loopback only). The page clock is FROZEN at each instant in both trees (A = main, B = candidate).
// Per instant and tree: the scene of the first refinement job posted to the Moon worker (sun-vector y sign = the lit
// limb, fraction, leadDirection) and the settled refined Moon rectangle, from which the LIT SIDE is read from pixels
// (mean luma of the disc's right half minus its left half) and the rectangle's bytes are compared with A.
// Discriminator (seeded "waxing from motion" mutant, tree C = the candidate with an init script that, on every render
// message whose leadDirection disagrees with the lit limb, flips the scene's sun-vector y sign as a waxing flag derived
// from the motion would): C must differ from A in lit side at the instants where the motion and the limb disagree.
// Usage: node lim.cjs <treeA> <treeB> <outJson>
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [treeA,treeB,outFile]=process.argv.slice(2);
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const INST=[];for(const [d,offs] of [['2026-11-24T15:55:00Z',[-60,-10,0,20,45,65,90,100,110,24*60]],['2026-12-08T23:18:00Z',[-30,0,15,30,39,60,-24*60]],['2027-01-07T19:04:00Z',[-30,0,20,40,60,85,95,-24*60]],['2026-12-24T01:17:00Z',[0,14,28,60,-24*60]]])for(const o of offs)INST.push(new Date(Date.parse(d)+o*60000).toISOString());
const FREEZE=ms=>`(()=>{const ND=Date,at=${ms};class D extends ND{constructor(...a){super(...(a.length?a:[at]));}static now(){return at;}}window.Date=D;})();`;
const HOOK=`(()=>{window.__lim=[];const P=Worker.prototype.postMessage;Worker.prototype.postMessage=function(m,...t){try{if(m&&m.kind==='render'&&m.scene&&Array.isArray(m.scene.sun)){
  if(window.__limMutant&&(m.scene.leadDirection===1||m.scene.leadDirection===-1)){const motionWaxing=m.scene.leadDirection===1;if(motionWaxing!==m.scene.waxing){m.scene.sun[1]=-m.scene.sun[1];m.scene.waxing=motionWaxing;}}
  window.__lim.push({sunY:m.scene.sun[1],fraction:m.scene.fraction,waxing:m.scene.waxing,lead:m.scene.leadDirection??null,mode:m.scene.mode});}}catch(e){}return P.call(this,m,...t);};})();`;
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
async function one(L,env,iso,mutant){
  const ctx=await L.newContext({});await ctx.addInitScript(FREEZE(Date.parse(iso)));if(mutant)await ctx.addInitScript('window.__limMutant=true;');await ctx.addInitScript(HOOK);
  const page=await ctx.newPage();await page.goto(env.origins.url('127.0.0.1','/index.html')+BASE,{waitUntil:'load',timeout:120000});
  const ok=await page.waitForFunction(()=>{const o=window.SalahMoonRuntime?.observe?.();return o?.current&&o.state.visibleSource==='refined-terrain'&&document.querySelector('.c')?.classList.contains('real-sky-composed');},null,{timeout:180000,polling:250}).then(()=>true).catch(()=>false);
  await page.waitForTimeout(4000);
  const rect=await page.evaluate(()=>{const b=document.querySelector('.mphoto').getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};});
  const img=decodePng(await page.screenshot({scale:'device'}));const jobs=await page.evaluate(()=>window.__lim);
  const truth=await page.evaluate(()=>{const t=window.qaState().moonTruth;return {phaseFraction:t.phaseFraction,alt:t.moonAltitudeDeg};});await ctx.close();
  const k=img.width/325,S=Math.min(rect.w,rect.h)*k,x0=rect.x*k,y0=rect.y*k,cx=x0+S/2,cy=y0+S/2;let l=0,ln=0,r=0,rn=0;const bytes=[];
  for(let y=Math.floor(y0);y<y0+S;y++)for(let x=Math.floor(x0);x<x0+S;x++){const i=4*(y*img.width+x);bytes.push(img.data[i],img.data[i+1],img.data[i+2]);if(Math.hypot(x+.5-cx,y+.5-cy)>.47*S)continue;const v=Y(img.data,i);if(x+.5<cx){l+=v;ln++;}else{r+=v;rn++;}}
  const b=Buffer.from(bytes);return {settled:ok,truth,firstJob:jobs[0]??null,jobs:jobs.length,litSide:r/rn-l/ln>0?'right':'left',rightMinusLeft:+(r/rn-l/ln).toFixed(2),hash:crypto.createHash('sha256').update(b).digest('hex').slice(0,16),bytes:b};
}
async function tree(root,mutant){const env=await createEnv({root});const L=await launch(env,{engine:'chromium',mode:'route',reducedMotion:'reduce'});const out={};
  try{for(let i=0;i<INST.length;i+=4){const part=INST.slice(i,i+4);const res=await Promise.all(part.map(t=>one(L,env,t,mutant)));part.forEach((t,j)=>out[t]=res[j]);}}finally{await L.close().catch(()=>{});}
  return {out,allowedExternal:env.finish().allowedExternal};}
const diffN=(a,b)=>{if(a.length!==b.length)return -1;let n=0;for(let i=0;i<a.length;i+=3)if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2])n++;return n;};
(async()=>{
  const A=await tree(treeA,false),B=await tree(treeB,false),C=await tree(treeB,true);
  const rows=INST.map(t=>{const a=A.out[t],b=B.out[t],c=C.out[t];return {instant:t,fraction:a.truth.phaseFraction,alt:a.truth.alt,settled:[a.settled,b.settled,c.settled],
    sunYSignA:Math.sign(a.firstJob?.sunY??0),sunYSignB:Math.sign(b.firstJob?.sunY??0),leadB:b.firstJob?.lead??null,litSideA:a.litSide,litSideB:b.litSide,litSideMutant:c.litSide,rightMinusLeft:[a.rightMinusLeft,b.rightMinusLeft,c.rightMinusLeft],
    moonRectDifferingPixelsAvsB:diffN(a.bytes,b.bytes),moonRectDifferingPixelsAvsMutant:diffN(a.bytes,c.bytes),
    pass:Math.sign(a.firstJob?.sunY??0)===Math.sign(b.firstJob?.sunY??0)&&a.litSide===b.litSide,mutantSunYFlipped:Math.sign(c.firstJob?.sunY??0)!==Math.sign(a.firstJob?.sunY??0)};});
  const out={schema:'r0041-lim/1',engine:'chromium',dpr:1,frozenClock:true,instants:rows.length,allowedExternal:[A.allowedExternal,B.allowedExternal,C.allowedExternal],
    pass:rows.every(r=>r.pass&&r.settled.every(Boolean)),identicalBytes:rows.filter(r=>r.moonRectDifferingPixelsAvsB===0).length,
    mutant:{instantsWithFlippedSunY:rows.filter(r=>r.mutantSunYFlipped).length,instantsWithLitSideChanged:rows.filter(r=>r.litSideMutant!==r.litSideA).length,failsRow:rows.some(r=>r.litSideMutant!==r.litSideA||r.mutantSunYFlipped)},rows};
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));console.log(JSON.stringify({pass:out.pass,identicalBytes:out.identicalBytes,mutant:out.mutant,allowed:out.allowedExternal}));
  if(out.allowedExternal.some(v=>v!==0))process.exit(2);
})().catch(e=>{console.error(e);process.exit(1);});
