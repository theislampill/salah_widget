'use strict';
// R0041 (issue 143) row R41-PIX (pixel scope, LE-5) and the native half of G41-2. Native recipe; NOT part of the node
// glob. Byte comparison of the Moon rectangle (.mphoto) and of the whole card between two trees (A = main, B = the
// candidate) for crescent, half, gibbous, full and new Moon instants OUTSIDE the census intervals, one simMoon override
// scene (G41-2), and their START-UP SEQUENCES.
// Method: the page clock is FROZEN at the scene instant (Date.now() constant), so both trees compute the same ephemeris
// and scene; reduced motion; synthetic fixture (lat 24.47, lon 39.61, method 4); one headless browser per (tree,
// engine, DPR) through iso.cjs (loopback only; Chromium DPR 2 also --force-device-scale-factor=2). Each scene is loaded
// LOADS times per tree, each load in a fresh isolated context of that browser (R0033 found that the first load in a
// fresh browser can differ by load order, so repeat loads are compared and the noise floor A-vs-A is measured, not
// assumed). Per load: full-page screenshots from navigation until 6 s after the settled refined Moon; the START-UP
// SEQUENCE is the ordered list of distinct Moon-rectangle states (consecutive duplicates removed; a state is the
// SHA-256 of the rectangle's RGB bytes); the SETTLED state is the last screenshot (card and rectangle).
// Negative control: one extra load of B with a 1-code tint (an overlay of white at opacity 1/255 over the Moon
// rectangle) must FAIL the comparison.
// Usage: node pix.cjs <treeA> <treeB> <outJson> <engine> <dpr> [loads=3] [scene,...]
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [treeA,treeB,outFile,engine,dprArg,loadsArg,sceneArg]=process.argv.slice(2);
const DPR=+dprArg,LOADS=+(loadsArg||3);
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SCENES={crescent:{iso:'2026-11-12T15:30:00Z'},half:{iso:'2026-11-17T16:30:00Z'},gibbous:{iso:'2026-11-20T17:00:00Z'},full:{iso:'2026-11-23T16:30:00Z'},new:{iso:'2027-01-06T19:30:00Z'},
  simMoonCrescent:{iso:'2026-11-18T16:30:00Z',frag:'&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42'}};
const pick=sceneArg?sceneArg.split(','):Object.keys(SCENES);
const FREEZE=ms=>`(()=>{const ND=Date,at=${ms};class D extends ND{constructor(...a){super(...(a.length?a:[at]));}static now(){return at;}}window.Date=D;})();`;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex').slice(0,16);
function crop(img,rect){const k=img.width/325,x0=Math.floor(rect.x*k),y0=Math.floor(rect.y*k),x1=Math.ceil((rect.x+rect.w)*k),y1=Math.ceil((rect.y+rect.h)*k),w=x1-x0,h=y1-y0,o=Buffer.alloc(3*w*h);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const si=4*((y0+y)*img.width+x0+x),di=3*(y*w+x);o[di]=img.data[si];o[di+1]=img.data[si+1];o[di+2]=img.data[si+2];}return {w,h,rgb:o};}
const rgbAll=img=>{const n=img.width*img.height,o=Buffer.alloc(3*n);for(let i=0;i<n;i++){o[3*i]=img.data[4*i];o[3*i+1]=img.data[4*i+1];o[3*i+2]=img.data[4*i+2];}return o;};
function diff(a,b){if(a.length!==b.length)return {error:'size',a:a.length,b:b.length};let n=0,mx=0;for(let i=0;i<a.length;i+=3){let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(a[i+k]-b[i+k]));if(d){n++;mx=Math.max(mx,d);}}return {differingPixels:n,maxChannelDifference:mx};}
async function load(L,env,scene,tint){
  const ctx=await L.newContext({});await ctx.addInitScript(FREEZE(Date.parse(scene.iso)));const page=await ctx.newPage();const shots=[];let capturing=true;
  await page.goto(env.origins.url('127.0.0.1','/index.html')+BASE+(scene.frag||''),{waitUntil:'commit',timeout:120000});
  const loop=(async()=>{while(capturing){try{shots.push(await page.screenshot({scale:'device',animations:'allow',caret:'initial'}));}catch(e){await page.waitForTimeout(30);}}})();
  const ok=await page.waitForFunction(()=>{const o=window.SalahMoonRuntime?.observe?.();return o?.current&&o.state.visibleSource==='refined-terrain'&&document.querySelector('.c')?.classList.contains('real-sky-composed');},null,{timeout:180000,polling:250}).then(()=>true).catch(()=>false);
  await page.waitForTimeout(6000);
  const rect=await page.evaluate(()=>{const b=document.querySelector('.mphoto').getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};});
  if(tint){await page.evaluate(r=>{const d=document.createElement('div');d.style.cssText=`position:fixed;left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px;background:#fff;opacity:${1/255};z-index:2147483646;pointer-events:none`;document.body.appendChild(d);},rect);await page.waitForTimeout(800);}
  capturing=false;await loop;
  const final=decodePng(await page.screenshot({scale:'device',animations:'allow',caret:'initial'}));
  const truth=await page.evaluate(()=>{const t=window.qaState().moonTruth,o=window.SalahMoonRuntime.observe();return {phaseFraction:t.phaseFraction,alt:t.moonAltitudeDeg,displayMode:t.displayMode,moonlightOpacity:t.moonlightOpacity,source:o.state.visibleSource,leadDirection:o.state.accepted?.scene?.leadDirection??null};});
  await ctx.close();
  const seq=[];for(const p of shots){let img;try{img=decodePng(p);}catch(e){continue;}const h=sha(crop(img,rect).rgb);if(seq.at(-1)!==h)seq.push(h);}
  const c=crop(final,rect);return {settledToRefined:ok,rect,truth,shots:shots.length,sequence:seq,moon:c.rgb,moonHash:sha(c.rgb),card:rgbAll(final),cardHash:sha(rgbAll(final)),size:[final.width,final.height]};
}
async function tree(root,label,withTint){
  const env=await createEnv({root});const L=await launch(env,{engine,mode:'route',reducedMotion:'reduce',deviceScaleFactor:DPR,extraArgs:engine==='chromium'&&DPR>1?['--force-device-scale-factor='+DPR]:[]});
  const out={};try{for(const name of pick){const sc=SCENES[name];out[name]=[];
    const jobs=[];for(let i=0;i<LOADS;i++)jobs.push(load(L,env,sc,false));if(withTint)jobs.push(load(L,env,sc,true));
    const res=await Promise.all(jobs);out[name]=res.slice(0,LOADS);if(withTint)out[name].tint=res[LOADS];
    console.log(label,engine,DPR,name,res.map(r=>r.moonHash+'/'+r.cardHash+' seq'+r.sequence.length).join(' '));}}
  finally{await L.close().catch(()=>{});}
  const iso=env.finish();return {loads:out,allowedExternal:iso.allowedExternal,externalAttempts:iso.externalAttempts};
}
(async()=>{
  const A=await tree(treeA,'A',false),B=await tree(treeB,'B',true);
  const out={schema:'r0041-pix/1',engine,dpr:DPR,loads:LOADS,frozenClock:true,motion:'reduce',treeA:path.basename(path.resolve(treeA)),treeB:path.basename(path.resolve(treeB)),allowedExternal:[A.allowedExternal,B.allowedExternal],scenes:{}};
  for(const name of pick){const a=A.loads[name],b=B.loads[name],sc={instant:SCENES[name].iso,fragmentExtra:SCENES[name].frag||null,truthA:a[0].truth,truthB:b[0].truth,settledToRefined:[...a,...b].every(x=>x.settledToRefined)};
    const pairs=(X,Y,same)=>{const r=[];for(let i=0;i<X.length;i++)for(let j=same?i+1:0;j<Y.length;j++)r.push({i,j,moon:diff(X[i].moon,Y[j].moon),card:diff(X[i].card,Y[j].card),sequenceEqual:JSON.stringify(X[i].sequence)===JSON.stringify(Y[j].sequence)});return r;};
    sc.AvsA=pairs(a,a,true);sc.BvsB=pairs(b,b,true);sc.AvsB=pairs(a,b,false);
    sc.tint={vsB:b.map((x,j)=>({j,moon:diff(x.moon,b.tint.moon),card:diff(x.card,b.tint.card)})),truth:b.tint.truth};
    sc.sequences={A:a.map(x=>x.sequence),B:b.map(x=>x.sequence)};
    const z=p=>p.moon.differingPixels===0&&p.card.differingPixels===0;
    sc.verdict={mainVsMainZero:sc.AvsA.every(z),candVsCandZero:sc.BvsB.every(z),mainVsCandZero:sc.AvsB.every(z),mainVsCandZeroPairs:sc.AvsB.filter(z).length+'/'+sc.AvsB.length,
      startupSequencesEqual:sc.AvsB.every(p=>p.sequenceEqual),startupSequencesEqualPairs:sc.AvsB.filter(p=>p.sequenceEqual).length+'/'+sc.AvsB.length,mainSequencesEqual:sc.AvsA.every(p=>p.sequenceEqual),
      tintDetected:sc.tint.vsB.every(p=>p.moon.differingPixels>0)};
    out.scenes[name]=sc;console.log(name,JSON.stringify(sc.verdict));}
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));
  if(out.allowedExternal.some(v=>v!==0))process.exit(2);
})().catch(e=>{console.error(e);process.exit(1);});
