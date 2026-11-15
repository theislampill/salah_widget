'use strict';
// Precipitation-presentation evaluation (research only, 2026-11-15): controlled native clips of the widget's rain.
//   node tools/qa/precip_eval_capture.cjs --pw <playwright package dir> --root <generated tree> --out <bulk dir>
//        [--engine chromium|firefox|webkit] [--only <regex on cell id>] [--variant base|L1|L2|L2c|L3|L4|L5|combo|comboc]
//        [--mode stepped|realtime] [--secs 10] [--fps 15] [--headed 1] [--reduced 1 (OS reduced motion, no motion=full)] [--list 1]
// stepped : mocked PAUSED clock advanced 1/fps per frame with clock.runFor; every CSS animation (drops, flash, stars,
//           fog) is paused and its currentTime advanced by the same step, so frames are exact and repeatable. Per frame
//           two lossless screenshots: the card, and the card with the streak layer hidden (the difference isolates the
//           rain), plus the geometry of every visible streak (DOM .drop boxes, or the experiment overlay's record).
// realtime: mocked clock RUNNING at wall rate (install + resume) and Playwright recordVideo for --secs: a real-time
//           clip in which CSS animations, rAF cloud motion and the overlay run unassisted (optionally headed).
// Card 325x530, DPR 1, forced time zone, every provider stubbed in precip_eval_lib.cjs; the run FAILS if any request
// other than loopback/data/blob was continued (log.continuedExternal) — requests are only fulfilled or aborted.
// --variant other than base injects tools/qa/precip_eval_levers.js (evaluation overlay; never product code).
const L=require('./precip_eval_lib.cjs');const fs=L.fs,path=L.path;
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const engine=a.engine||'chromium',mode=(a.mode||'stepped'),RM=a.reduced==='1'?'-reduced':'',variant=a.variant||'base',secs=+(a.secs||10),fps=+(a.fps||15);
const VARIANTS={base:null,L1:{levers:['L1']},L2:{levers:['L2'],sign:'map'},L2c:{levers:['L2'],sign:'cloud'},L3:{levers:['L3']},L4:{levers:['L4']},L5:{levers:['L5']},
  ctrl:{levers:[]},combo:{levers:['L1','L2','L3','L4','L5'],sign:'map'},comboc:{levers:['L1','L2','L3','L4','L5'],sign:'cloud'}};
// ---- fixture conditions (Open-Meteo current record; wind m/s; temperature degF; precip = 15-min current amount, mm) ----
const RAINDECK={cloud:98,low:95,mid:80,high:50,temp:60,hum:90,vis:10000};
const INT={
  'drizzle':{code:53,precip:0.2,rain:0.2,...RAINDECK},
  'rain-light':{code:61,precip:0.4,rain:0.4,...RAINDECK},
  'rain-moderate':{code:63,precip:1.2,rain:1.2,...RAINDECK},
  'rain-heavy':{code:65,precip:4,rain:4,...RAINDECK},
  'showers-violent':{code:82,precip:8,showers:8,...RAINDECK,cloud:90,low:85,mid:70,high:40},
  'showers-scattered':{code:80,precip:0.5,showers:0.5,cloud:40,low:30,mid:20,high:10,temp:66,hum:70,vis:15000},
  'thunder':{code:95,precip:3,rain:3,...RAINDECK,cloud:100,mid:90,high:70},
  'snow':{code:73,precip:0.6,snow:0.6,cloud:95,low:85,mid:70,high:40,temp:28,hum:90,dew:26,vis:3000},
  'overcast-dry':{code:3,precip:0,...RAINDECK},
  'rain-noev':{code:63,precip:0,rain:0,...RAINDECK},
};
const TIMES={noon:'solar-noon',golden:'golden-pm',dusk:'dusk',night:'night-early'};
function cells(){const out=[],site=L.SITES.madinah,date=L.DATES.equinox,st=L.sceneTimes(site,date);
  const at=sc=>Math.floor(st[sc]/900000)*900000+6*60000;
  const add=(id,ik,tk,w,extra)=>out.push({id,ik,tk,utcMs:at(TIMES[tk]),wx:{...INT[ik],wind:4,wdir:225,...(w||{})},...(extra||{})});
  for(const ik of Object.keys(INT))for(const tk of Object.keys(TIMES))add(`T-${ik}-${tk}`,ik,tk);           // intensity x time
  for(const ik of ['drizzle','rain-moderate','rain-heavy','snow']){add(`W-${ik}-calm`,ik,'noon',{wind:0.3,gust:0.6});
    for(const s of [5,10,20])for(const d of [90,270])add(`W-${ik}-${s}from${d}`,ik,'noon',{wind:s,wdir:d,gust:s*1.15});}
  for(const g of [[8,8.5],[8,22]])add(`G-rain-moderate-8from270-gust${g[1]}`,'rain-moderate','noon',{wind:g[0],wdir:270,gust:g[1]});
  add('G-rain-heavy-dusk-10from270-gust24','rain-heavy','dusk',{wind:10,wdir:270,gust:24});
  // sim twins (lightning is only permitted on the explicit preview path)
  for(const tk of ['noon','dusk','night']){const t=L.hhmm(st[TIMES[tk]],site.tz);
    out.push({id:`S-thunder-${tk}`,sim:`&simTime=${t}&simWx=95&simPrecip=5&simWind=6&simWindDir=270`,utcMs:L.localToUtc(date,'12:00',site.tz)});
    out.push({id:`S-rain-p0-${tk}`,sim:`&simTime=${t}&simWx=63&simPrecip=0`,utcMs:L.localToUtc(date,'12:00',site.tz)});}
  // evaluation matrix for the levers (light/moderate/heavy/scattered/storm x noon/dusk x calm/windy)
  for(const ik of ['rain-light','rain-moderate','rain-heavy','showers-scattered','thunder'])for(const tk of ['noon','dusk'])
    for(const [wn,w] of [['calm',{wind:0.3,gust:0.6}],['windy',{wind:10,wdir:270,gust:18}]])add(`E-${ik}-${tk}-${wn}`,ik,tk,w);
  return out;}
const HIDE='.wfx .drop,.wfx .flake,.pe-rain{visibility:hidden!important}';
const GEOM=`(()=>{const out=[];let di=-1;for(const d of document.querySelectorAll('.wfx .drop,.wfx .flake')){di++;const cs=getComputedStyle(d);if(cs.display==='none'||cs.visibility==='hidden')continue;
  const r=d.getBoundingClientRect();out.push([+r.x.toFixed(1),+r.y.toFixed(1),+r.width.toFixed(2),+r.height.toFixed(2),+(+cs.opacity).toFixed(3),d.className==='drop'?0:1,di]);}
  const c=document.querySelector('.c');return {dom:out,pe:window.__PE_LAST||null,data:{precip:c.dataset.precip,fx:c.dataset.fx,lightning:c.dataset.lightning},
  vars:{rainOp:c.style.getPropertyValue('--rain-op'),slant:c.style.getPropertyValue('--rain-slant'),snowSlant:c.style.getPropertyValue('--snow-slant')}};})()`;
const STEP_ANIM=`(dt)=>{window.__peA=window.__peA||new WeakMap();for(const an of document.getAnimations()){if(!window.__peA.has(an)){an.pause();window.__peA.set(an,{base:an.currentTime||0,k:0});}
  const s=window.__peA.get(an);s.k+=dt;an.currentTime=s.base+s.k;}}`;
(async()=>{let list=cells();if(a.only)list=list.filter(c=>new RegExp(a.only).test(c.id));if(a.list){console.log(list.map(c=>c.id).join('\n'));return;}
  const pw=require(a.pw||'playwright'),root=path.resolve(a.root||'.'),out=path.resolve(a.out);
  const ordinary=JSON.parse(fs.readFileSync(L.ordinaryPath,'utf8'));const levers=fs.readFileSync(path.join(__dirname,'precip_eval_levers.js'),'utf8');
  const {srv,base}=await L.serve(root);const opts={headless:a.headed!=='1'};if(engine==='chromium')opts.args=['--ignore-gpu-blocklist'];
  const browser=await pw[engine].launch(opts);let bad=0;
  try{for(const c of list){const t0=Date.now(),site=L.SITES.madinah,id=`${c.id}--${variant}--${mode}${RM}`,dir=path.join(out,engine,id);
    fs.mkdirSync(dir,{recursive:true});for(const f of fs.readdirSync(dir))fs.unlinkSync(path.join(dir,f));
    const s=await L.openScene(browser,base,ordinary,{site,utcMs:c.utcMs,wx:c.sim?null:c.wx,hash:(c.sim||'')+(a.reduced==='1'?'':'&motion=full'),reduced:a.reduced==='1',clock:'running',video:mode==='realtime'?dir:null});
    const meta={id,cell:c,engine,mode,variant,secs,fps,url:s.url,mockedStartUtc:new Date(c.utcMs).toISOString(),headed:a.headed==='1'};
    try{
      meta.ready=await L.waitReady(s.page,{maxMs:16000});
      for(let i=0;i<40;i++){const st=await s.page.evaluate(L.STATE);if(st.header.wt&&(c.sim||(st.qa&&st.qa.wxTruth&&st.qa.wxTruth.currentWeatherSource&&!/none|unavail/i.test(st.qa.wxTruth.currentWeatherSource))))break;await s.page.waitForTimeout(250);}
      await s.page.waitForTimeout(2500);
      const V=VARIANTS[variant];
      if(V){await s.page.evaluate(cfg=>{window.__PE_CFG=cfg;},{...V,manual:mode==='stepped'});await s.page.addScriptTag({content:levers});}
      meta.state=await s.page.evaluate(L.STATE);meta.horizonY=await s.page.evaluate(()=>{const e=document.querySelector('.arc .horizon');if(!e)return null;const r=e.getBoundingClientRect();return r.y+r.height/2;});
      meta.dropCss=await s.page.evaluate(()=>[...document.querySelectorAll('.wfx .drop')].slice(0,3).map(d=>{const cs=getComputedStyle(d);return {dur:cs.animationDuration,display:cs.display,inline:d.style.animationDuration}}));
      if(mode==='realtime'){await s.page.waitForTimeout(secs*1000);meta.geomEnd=await s.page.evaluate(GEOM);}
      else{
        await L.freeze(s.page,50);const dt=1000/fps,n=Math.round(secs*fps);meta.frames=[];
        const hide=await s.page.addStyleTag({content:'/*pe*/'});
        for(let k=0;k<n;k++){await s.page.clock.runFor(dt);await s.page.evaluate(`(${STEP_ANIM})(${dt})`);
          if(V)await s.page.evaluate(t=>window.__peFrame(t),k*dt+5000);
          const f=String(k).padStart(4,'0');await s.page.screenshot({path:path.join(dir,`a${f}.png`)});
          await s.page.evaluate(css=>{let e=document.getElementById('pe-hide');if(!e){e=document.createElement('style');e.id='pe-hide';document.head.appendChild(e);}e.textContent=css;},HIDE);
          await s.page.screenshot({path:path.join(dir,`b${f}.png`)});
          await s.page.evaluate(()=>{document.getElementById('pe-hide').textContent='';});
          meta.frames.push({k,t:k*dt,geom:await s.page.evaluate(GEOM)});}
      }
      // perf probe (real time, own clock-independent counter): overlay frame cost
      if(V&&mode==='realtime')meta.perf=await s.page.evaluate(()=>{const t=performance.now();for(let i=0;i<300;i++)window.__peFrame(i*16+0.5);const tot=performance.now()-t;return {meanMsPerFrame:tot/300,frames:300,note:'mocked clock running at wall rate; 1 ms granularity averaged over 300 frames'};});
    }catch(e){meta.error=String(e&&e.message||e).slice(0,300);}
    meta.providerLog=s.log.requests;meta.aborted=[...new Set(s.log.aborted)];meta.continuedExternal=s.log.continuedExternal;meta.errors=s.log.errors||[];
    const vid=s.page.video();await s.ctx.close();
    if(vid){try{const p=await vid.path();fs.renameSync(p,path.join(dir,'clip.webm'));}catch(e){meta.videoError=String(e);}}
    if(meta.continuedExternal.length){bad++;meta.error='EXTERNAL REQUEST CONTINUED';}
    meta.wallMs=Date.now()-t0;fs.writeFileSync(path.join(dir,'meta.json'),JSON.stringify(meta));
    console.log(`${engine} ${id} ${meta.error?'ERROR '+meta.error:'ok'} ${meta.wallMs}ms precip=${meta.state&&meta.state.data&&meta.state.data.precip} fx=${meta.state&&meta.state.data&&meta.state.data.fx} op=${meta.state&&meta.state.vars['--rain-op']} ext=${meta.continuedExternal.length} aborted=${meta.aborted.join('|')}`);}
  }finally{await browser.close().catch(()=>{});srv.close();}
  if(bad){console.error('external requests continued:',bad);process.exit(2);}
})().catch(e=>{console.error(e);process.exit(1);});
