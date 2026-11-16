'use strict';
// Moon-reuse audit, Job 2 (2026-11-16): what the wrong-way leading edge looks like and costs in the REAL product.
// Per cell: one engine, one DPR, the page wall clock shifted (init-script Date shift, real speed) to a chosen instant
// (a waxing-flag / phase-direction mismatch interval, or a matched control one day earlier), then for <seconds>:
//  - repeated Moon-rectangle screenshots as fast as the engine allows (timestamps on the page clock), decoded here;
//    per changed frame: pixels changed inside the disc (any channel), >3, >8 codes, max delta, mean |delta luma|;
//  - Moon worker jobs/results/previews/cancels (Worker postMessage/message wrapper, product unmodified);
//  - per animation frame: .c.moon-ready and .moon-mask-disc.mask-on (gate-D presence), counted at night;
//  - 1 Hz: SalahMoonRuntime.observe() tier and qaState().moonTruth (R0036 pure reads; &qa=1);
//  - browser process-tree CPU seconds: every descendant of THIS node process (Windows Win32_Process times; the node
//    process itself excluded), from t=60 s to the end. Other agents' browsers on the host are not descendants.
// Model frame analysis is NOT human perception. All traffic through iso.cjs; finish() throws on any allowed
// non-loopback request. Usage: node defect.cjs <repoRoot> <outJson> <cropDir> <engine> <dpr> <seconds> <label> <startISO>
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const [root,outFile,cropDir,engine,dpr,seconds,label,startISO]=process.argv.slice(2);
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const INSTR=`(()=>{window.__moonLog=[];const P=Worker.prototype.postMessage;Worker.prototype.postMessage=function(m,t){try{if(m&&(m.kind==='cancel'||(m.kind==='render'&&m.scene&&m.scene.fraction!=null)))window.__moonLog.push({dir:'out',kind:m.kind,t:performance.now(),fraction:m.scene&&m.scene.fraction});}catch(e){}return t?P.call(this,m,t):P.call(this,m);};
 const W=window.Worker;window.Worker=class extends W{constructor(u,o){super(u,o);this.addEventListener('message',e=>{const m=e.data;if(m&&(m.kind==='preview'||m.kind==='result')&&m.diagnostics&&m.diagnostics.quality&&m.surfaceSize)window.__moonLog.push({dir:'in',kind:m.kind,t:performance.now(),ms:m.diagnostics.quality.totalMs||null});});}};
 window.__gate={frames:0,notReady:0,maskOff:0,firstT:null,runs:[]};let run=0;
 const tick=()=>{const c=document.querySelector('.c'),m=document.querySelector('.moon-mask-disc');if(c&&m){const g=window.__gate;g.frames++;const r=c.classList.contains('moon-ready'),k=m.classList.contains('mask-on');if(!r)g.notReady++;if(!k)g.maskOff++;if(!r||!k){if(!run)g.runs.push({t:performance.now(),ready:r,mask:k,n:0});run=1;g.runs[g.runs.length-1].n++;}else run=0;}requestAnimationFrame(tick);};requestAnimationFrame(tick);
 window.__hrefs=[];document.addEventListener('DOMContentLoaded',()=>{const ph=document.querySelector('.mphoto');if(ph)new MutationObserver(()=>window.__hrefs.push(performance.now())).observe(ph,{attributes:true,attributeFilter:['href']});});})();`;
function cpuOf(pid){
  try{const csv=execFileSync('powershell',['-NoProfile','-Command','Get-CimInstance Win32_Process | ForEach-Object { "$($_.ProcessId),$($_.ParentProcessId),$($_.UserModeTime),$($_.KernelModeTime)" }'],{encoding:'utf8',maxBuffer:1<<24});
    const rows=csv.trim().split(/\r?\n/).map(l=>l.split(',').map(Number)),kids=new Map();for(const [p,pp] of rows){if(!kids.has(pp))kids.set(pp,[]);kids.get(pp).push(p);}
    const set=new Set([pid]),st=[pid];while(st.length){for(const k of kids.get(st.pop())||[])if(!set.has(k)){set.add(k);st.push(k);}}
    set.delete(pid);let s=0;for(const [p,,u,k] of rows)if(set.has(p))s+=(u+k)/1e7;return {seconds:s,processes:set.size};}catch(e){return {error:String(e).slice(0,200)};}
}
(async()=>{
  const env=await createEnv({root});const out={engine,dpr:+dpr,seconds:+seconds,label,startISO,fragment:FRAG,frames:[],states:[],crops:[]};
  try{
    const L=await launch(env,{engine,mode:'route',deviceScaleFactor:+dpr,reducedMotion:'reduce'});
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(INSTR);
    const page=await L.context.newPage();page.on('pageerror',e=>(out.pageErrors??=[]).push(String(e).slice(0,300)));
    await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'load',timeout:120000});
    await page.waitForFunction(()=>{const r=document.querySelector('.mphoto')?.getBoundingClientRect();return r&&r.width>50;},null,{timeout:60000});
    const rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});out.rect=rect;
    const clip={x:Math.floor(rect.x),y:Math.floor(rect.y),width:Math.ceil(rect.w)+1,height:Math.ceil(rect.h)+1};
    const pid=process.pid;
    const t0=Date.now();let prev=null,prevBuf=null,cpu0=null,lastState=0,saved=0;
    while(Date.now()-t0<seconds*1000){
      if(!cpu0&&Date.now()-t0>60000&&pid){cpu0={...cpuOf(pid),at:Date.now()-t0};}
      if(Date.now()-lastState>=1000){lastState=Date.now();
        out.states.push(await page.evaluate(()=>{const o=window.SalahMoonRuntime?.observe?.(),st=o&&o.state;let mt=null;try{mt=window.qaState?.().moonTruth;}catch(e){}
          return {t:performance.now(),tier:st&&st.visibleSource,status:st&&st.status,current:o&&o.current,fraction:window.SalahMoonHost?.capture?.()?.fraction,
            displayMode:mt&&mt.displayMode,moonlightOpacity:mt&&mt.moonlightOpacity,moonSkyOpacity:mt&&mt.moonSkyOpacity,moonFeatureOpacity:mt&&mt.moonFeatureOpacity,
            physical:mt&&mt.physicalMoonVisible,calendar:mt&&mt.calendarMoonVisible,light:mt&&mt.lunarLight&&(mt.lunarLight.reason??mt.lunarLight.eligible??null),alt:mt&&mt.moonAltitudeDeg};}));}
      const ta=await page.evaluate(()=>performance.now());const buf=await page.screenshot({clip,scale:'device',animations:'allow',caret:'initial'});const tb=await page.evaluate(()=>performance.now());
      const img=decodePng(buf),W=img.width,H=img.height,cx=W/2,cy=H/2,R=0.47*Math.min(W,H);
      let lum=0,n=0;const px=[];for(let y=0;y<H;y++)for(let x=0;x<W;x++){if((x+.5-cx)**2+(y+.5-cy)**2>R*R)continue;const i=4*(y*W+x);px.push(i);lum+=.2126*img.data[i]+.7152*img.data[i+1]+.0722*img.data[i+2];n++;}
      const f={t:(ta+tb)/2,dt:tb-ta,meanLuma:lum/n};
      if(prev){let ch=0,c3=0,c8=0,mx=0,dl=0;for(const i of px){let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(img.data[i+k]-prev.data[i+k]));if(d){ch++;if(d>3)c3++;if(d>8)c8++;if(d>mx)mx=d;}
          dl+=Math.abs((.2126*img.data[i]+.7152*img.data[i+1]+.0722*img.data[i+2])-(.2126*prev.data[i]+.7152*prev.data[i+1]+.0722*prev.data[i+2]));}
        Object.assign(f,{changed:ch,over3:c3,over8:c8,maxDelta:mx,meanAbsDeltaLuma:dl/n,discPixels:n});
        if(c8>50&&saved<6&&+dpr===1){fs.mkdirSync(cropDir,{recursive:true});const a=`${label}-swap${saved}-before.png`,b=`${label}-swap${saved}-after.png`;fs.writeFileSync(path.join(cropDir,a),prevBuf);fs.writeFileSync(path.join(cropDir,b),buf);out.crops.push({t:f.t,before:a,after:b,over8:c8});saved+=2;}}
      out.frames.push(f);prev=img;prevBuf=buf;
    }
    if(cpu0&&pid){const c1={...cpuOf(pid),at:Date.now()-t0};out.cpu={from:cpu0,to:c1,browserTreeCpuSeconds:c1.seconds-cpu0.seconds,wallSeconds:(c1.at-cpu0.at)/1000};}
    out.workerLog=await page.evaluate(()=>window.__moonLog);out.gate=await page.evaluate(()=>({...window.__gate,runs:window.__gate.runs.slice(0,50)}));out.hrefs=await page.evaluate(()=>window.__hrefs);
    await L.close();
  }catch(e){out.error=String(e&&e.stack||e);}
  out.isolation=env.finish();
  // Keep only changed frames in the record (the full frame list is summarised).
  const fr=out.frames;out.frameSummary={count:fr.length,meanIntervalMs:fr.length>1?(fr.at(-1).t-fr[0].t)/(fr.length-1):null,meanCaptureMs:fr.reduce((a,b)=>a+b.dt,0)/Math.max(1,fr.length)};
  out.frames=fr.filter(x=>x.changed);
  const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[label]=out;fs.writeFileSync(outFile,JSON.stringify(all));
  const jobs=(out.workerLog||[]).filter(x=>x.kind==='render').length,res=(out.workerLog||[]).filter(x=>x.kind==='result').length;
  console.log(label,'jobs',jobs,'results',res,'frames',out.frameSummary.count,'fpsInterval',Math.round(out.frameSummary.meanIntervalMs),'cpu',out.cpu&&out.cpu.browserTreeCpuSeconds.toFixed(1),'allowed',out.isolation.allowedExternal,out.error?('ERR '+out.error.slice(0,200)):'');
})().catch(e=>{console.error(e);process.exit(1);});
