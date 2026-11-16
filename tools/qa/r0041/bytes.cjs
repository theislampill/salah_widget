'use strict';
// R0041 native byte check (recipe; NOT part of the node glob). In a real page of the served tree, at a chosen night
// (Date shifted, real speed), records SHA-256 digests of:
//   - every V5 initial-receiver render (rgba, calendarRgba) and its scene (minus the R0041 leadDirection field);
//   - every refined worker result (rgba, calendarRgba) and its scene (minus leadDirection);
//   - after settle: the presented runtime surface canvas and the device-resolution detail canvas;
//   - prayer independence: the prayer list text (.times) and the prayer markers' geometry (.arc circles' cx, cy).
// Run once per tree (main, candidate) with the same arguments and compare the JSON. Scenes are canonical (phase
// bucketed), so the same minute gives the same scene in both trees; a differing scene is reported, not hidden.
// Every launch goes through iso.cjs (catch-all route before navigation; finish() throws on an allowed external request).
// Usage: node bytes.cjs <repoRoot> <outJson> <label> <engine> <startISO>
const fs=require('node:fs'),path=require('node:path');const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,label,engine,startISO]=process.argv.slice(2);
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const INSTR=`(()=>{const rec=window.__r41b={initial:[],results:[]};const pend=[];window.__r41bPending=pend;
 const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
 const dig=a=>a?crypto.subtle.digest('SHA-256',a.slice().buffer).then(hex):Promise.resolve(null);
 const sc=s=>{if(!s)return null;const c={...s};delete c.leadDirection;return JSON.stringify(c);};
 const note=(list,m)=>{pend.push(Promise.all([dig(m.rgba),dig(m.calendarRgba)]).then(([r,c])=>list.push({at:Math.round(performance.now()),scene:sc(m.scene),rgba:r,calendar:c})));};
 let held;Object.defineProperty(window,'SalahMoonInitial',{configurable:true,get(){return held;},set(v){held=v&&typeof v.render==='function'?{...v,identity:v.identity,render(scene){const m=v.render(scene);try{note(rec.initial,m);}catch(e){}return m;}}:v;}});
 const W=window.Worker;window.Worker=class extends W{constructor(u,o){super(u,o);this.addEventListener('message',e=>{const m=e.data;if(m&&m.kind==='result'&&m.rgba&&m.scene&&m.scene.fraction!=null)note(rec.results,m);});}};})();`;
(async()=>{
 const env=await createEnv({root});const out={label,engine,startISO};
 try{
  const L=await launch(env,{engine,mode:'route',reducedMotion:'reduce'});await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);
  const page=await L.context.newPage();
  await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'commit',timeout:120000});
  await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:300000,polling:250});
  await page.waitForTimeout(3000);
  Object.assign(out,await page.evaluate(async()=>{
   await Promise.all(window.__r41bPending);
   const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
   const canvasDigest=async cv=>{if(!cv||!cv.width)return null;const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;return {w:cv.width,h:cv.height,sha:hex(await crypto.subtle.digest('SHA-256',d.slice().buffer))};};
   const st=window.SalahMoonRuntime.state;
   return {initial:window.__r41b.initial,results:window.__r41b.results,surface:await canvasDigest(window.SalahMoonRuntime.surface()),detail:await canvasDigest(document.querySelector('.moon-detail-canvas')),
    visibleSource:st.visibleSource,acceptedScene:(()=>{const c={...st.accepted?.scene};delete c.leadDirection;return JSON.stringify(c);})(),
    prayer:{times:[...document.querySelectorAll('.times .p')].map(p=>p.dataset.prayerKey+' '+p.querySelector('.tm')?.textContent),
     markers:[...document.querySelectorAll('.arc circle[data-prayer-key]')].map(c=>c.dataset.prayerKey+' '+c.getAttribute('cx')+' '+c.getAttribute('cy'))}};
  }));
  await L.close();
 }catch(e){out.error=String(e&&e.stack||e);console.error(out.error);}
 out.isolation=env.finish();
 const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[[label,engine,startISO].join('|')]=out;fs.writeFileSync(outFile,JSON.stringify(all,null,1));
 console.log(label,engine,startISO,'initial',out.initial?.length,'results',out.results?.length,'surface',out.surface?.sha?.slice(0,12),'detail',out.detail?.sha?.slice(0,12),'isolation allowed',out.isolation.allowedExternal);
})().catch(e=>{console.error(e);process.exit(1);});
