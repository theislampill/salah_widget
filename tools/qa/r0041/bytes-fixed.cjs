'use strict';
// R0041 native byte check with FIXED scenes (recipe; NOT part of the node glob). A live clock gives each tree a slightly
// different utcMs, so live surfaces cannot be compared byte for byte. Here, in a real page of the served tree, the SAME
// scene objects (read from a JSON file, e.g. the scenes main produced at a control instant) are rendered by:
//   - the V5 initial receiver (window.SalahMoonInitial.render): rgba and calendarRgba digests;
//   - the product's own refinement worker (an extra render message on the live worker, after settle; the runtime rejects
//     the unexpected reply, which is harmless): rgba and calendarRgba digests;
// each without and with the R0041 field leadDirection (+1 and -1), so the same JSON also proves that field is inert.
// Run once per tree with the same scene file and compare. Every launch goes through iso.cjs.
// Usage: node bytes-fixed.cjs <repoRoot> <outJson> <label> <engine> <scenes.json>
const fs=require('node:fs');const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,label,engine,sceneFile]=process.argv.slice(2);
const scenes=JSON.parse(fs.readFileSync(sceneFile,'utf8'));
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const INSTR=`(()=>{window.__r41ws=[];const W=window.Worker;window.Worker=class extends W{constructor(u,o){super(u,o);window.__r41ws.push(this);}};})();`;
(async()=>{
 const env=await createEnv({root});const out={label,engine,renders:[]};
 try{
  const L=await launch(env,{engine,mode:'route',reducedMotion:'reduce'});await L.context.addInitScript(INSTR);
  const page=await L.context.newPage();
  await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'commit',timeout:120000});
  await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:300000,polling:250});
  await page.waitForTimeout(2000);
  out.renders=await page.evaluate(async scenes=>{
   const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
   const dig=async a=>a?hex(await crypto.subtle.digest('SHA-256',a.slice().buffer)):null;
   const moonWorker=()=>window.__r41ws.find(w=>w.__r41moon)??null;
   // The Moon worker is the one whose replies carry a lunar scene; tag it on the first such message.
   for(const w of window.__r41ws)w.addEventListener('message',e=>{if(e.data?.scene?.fraction!=null)w.__r41moon=true;});
   window.SalahMoonRuntime.refresh();await new Promise(r=>setTimeout(r,200));
   let n=900000;const work=s=>new Promise((res,rej)=>{const w=window.__r41ws.find(x=>x.__r41moon)??window.__r41ws.at(-1);const id=++n;
    const on=e=>{const m=e.data;if(m?.id!==id)return;if(m.kind==='result'){w.removeEventListener('message',on);res(m);}else if(m.kind==='error'){w.removeEventListener('message',on);rej(new Error(m.error));}};
    w.addEventListener('message',on);w.postMessage({kind:'render',id,identity:{id,key:'r0041-bytes',epoch:-1},scene:s});setTimeout(()=>rej(new Error('worker timeout')),240000);});
   const rows=[];
   for(const [name,base] of Object.entries(scenes)){
    for(const lead of [null,1,-1]){const s=structuredClone(base);if(lead!=null)s.leadDirection=lead;
     const row={name,lead};
     try{const m=window.SalahMoonInitial.render(structuredClone(s));row.initial={rgba:await dig(m.rgba),calendar:await dig(m.calendarRgba)};}catch(e){row.initialError=String(e.message??e);}
     if(base.mode==='calendar-canonical'&&s.size>2)try{const m=await work(s);row.worker={rgba:await dig(m.rgba),calendar:await dig(m.calendarRgba)};}catch(e){row.workerError=String(e.message??e);}
     rows.push(row);}
   }
   return rows;
  },scenes);
  await L.close();
 }catch(e){out.error=String(e&&e.stack||e);console.error(out.error);}
 out.isolation=env.finish();
 const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[[label,engine].join('|')]=out;fs.writeFileSync(outFile,JSON.stringify(all,null,1));
 console.log(label,engine,'rows',out.renders.length,'isolation allowed',out.isolation.allowedExternal,out.error??'');
})().catch(e=>{console.error(e);process.exit(1);});
