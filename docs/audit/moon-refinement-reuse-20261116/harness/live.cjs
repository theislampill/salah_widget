'use strict';
// Moon-reuse feasibility audit (2026-11-16): steady-state refinement cadence in the REAL product (root index.html),
// observed through the side-effect-free R0036 observe() read (never the adopting getters), plus a count of the
// render jobs the host posts to its Moon worker (init-script wrapper on Worker.prototype.postMessage; the
// product is not modified). All browser traffic goes through iso.cjs; env.finish() throws on any allowed
// non-loopback request. Usage:
//   node live.cjs <repoRoot> <outJson> <engine> <dpr> <seconds> <fragmentExtra> <label> [startISO]
// startISO (optional): an init-script Date shift so the page's wall clock starts at that instant and then runs
// at real speed (performance.now and workers untouched). Used to reach a chosen lunar instant.
const fs=require('node:fs');
const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,engine,dpr,seconds,extra,label,startISO]=process.argv.slice(2);
const SHIFT=startISO?`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`:'';
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0'+(extra||'');
const INSTR=`(()=>{window.__moonLog=[];const P=Worker.prototype.postMessage;Worker.prototype.postMessage=function(m,t){try{if(m&&m.kind)window.__moonLog.push({dir:'out',kind:m.kind,id:m.id,t:performance.now(),fraction:m.scene&&m.scene.fraction,pd:m.scene&&m.scene.phaseDisplayDiameter});}catch(e){}return t?P.call(this,m,t):P.call(this,m);};
 const W=window.Worker;window.Worker=class extends W{constructor(u,o){super(u,o);this.addEventListener('message',e=>{const m=e.data;if(m&&m.kind&&m.kind!=='progress')window.__moonLog.push({dir:'in',kind:m.kind,id:m.id,t:performance.now(),q:m.diagnostics&&m.diagnostics.quality&&m.diagnostics.quality.status,ms:m.diagnostics&&m.diagnostics.quality&&m.diagnostics.quality.totalMs});});}};})();`;
// Per-frame reveal record: was the Moon slot revealed (.c.moon-ready) in each animation frame; plus every class
// mutation that removed moon-ready (synchronous toggles inside one task never reach a frame).
const FRAMES=`(()=>{window.__frames={n:0,notReady:0,notReadyRuns:[]};window.__mut={unready:0};let run=0;
 const tick=()=>{const c=document.querySelector('.c');if(c){window.__frames.n++;const r=c.classList.contains('moon-ready');if(!r){window.__frames.notReady++;run++;}else if(run){window.__frames.notReadyRuns.push(run);run=0;}}requestAnimationFrame(tick);};requestAnimationFrame(tick);
 document.addEventListener('DOMContentLoaded',()=>{const c=document.querySelector('.c');if(!c)return;let was=c.classList.contains('moon-ready');new MutationObserver(()=>{const r=c.classList.contains('moon-ready');if(was&&!r)window.__mut.unready++;was=r;}).observe(c,{attributes:true,attributeFilter:['class']});});
})();`;
(async()=>{
  const env=await createEnv({root});const out={engine,dpr:+dpr,seconds:+seconds,fragment:FRAG,label,samples:[],started:new Date().toISOString()};
  try{
    const L=await launch(env,{engine,mode:'route',deviceScaleFactor:+dpr});if(SHIFT)await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);await L.context.addInitScript(FRAMES);
    const page=await L.context.newPage();page.on('pageerror',e=>(out.pageErrors??=[]).push(String(e).slice(0,300)));
    await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'load',timeout:120000});
    await page.waitForFunction(()=>!!window.SalahMoonInitial,null,{timeout:60000}).catch(()=>{});
    await page.evaluate(()=>{const I=window.SalahMoonInitial;if(I&&typeof I.render==='function'){try{const f=I.render.bind(I);window.__initialRenders=0;I.render=g=>{window.__initialRenders++;return f(g);};}catch(e){window.__initialRenders='unwrappable:'+e.message;}}});
    const t0=Date.now();
    while(Date.now()-t0<seconds*1000){
      await page.waitForTimeout(1000);
      out.samples.push(await page.evaluate(()=>{const o=window.SalahMoonRuntime?.observe?.();const c=window.SalahMoonHost?.capture?.();const r=document.querySelector('.mphoto')?.getBoundingClientRect();const st=o&&o.state;
        return {t:performance.now(),status:st&&st.status,visibleSource:st&&st.visibleSource,current:o&&o.current,accepted:o&&o.accepted,waitingPreview:o&&o.waitingPreview,renders:st&&st.renders,cancelled:st&&st.cancelled,pending:st&&st.pending,
          scenePD:st&&st.accepted&&st.accepted.scene&&st.accepted.scene.phaseDisplayDiameter,sceneFraction:st&&st.accepted&&st.accepted.scene&&st.accepted.scene.fraction,
          fraction:c&&c.fraction,up:c&&c.up,dpr:c&&c.dpr,timeScale:c&&c.timeScale,utcMs:c&&c.utcMs,rectW:r&&r.width,rectH:r&&r.height,moonReady:document.querySelector('.c')?.classList.contains('moon-ready')};}));
    }
    out.workerLog=await page.evaluate(()=>window.__moonLog);out.frames=await page.evaluate(()=>({...window.__frames,notReadyRuns:window.__frames.notReadyRuns.slice(-200),mutationsRemovingMoonReady:window.__mut.unready,initialRenders:window.__initialRenders??null}));
    await L.close();
  }catch(e){out.error=String(e&&e.stack||e);}
  out.isolation=env.finish();out.finished=new Date().toISOString();
  const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[label]=out;fs.writeFileSync(outFile,JSON.stringify(all));
  const renders=out.workerLog?out.workerLog.filter(x=>x.dir==='out'&&x.kind==='render').length:null;
  console.log(label,'renders posted',renders,'samples',out.samples.length,'isolation',JSON.stringify(out.isolation.totalRequests),'allowed',out.isolation.allowedExternal,out.error||'');
})().catch(e=>{console.error(e);process.exit(1);});
