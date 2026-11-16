'use strict';
// Precipitation MODEL comparison (research only, 2026-11-15): REAL-TIME native-size clips of the current product rain
// and the M1-M5 prototypes (tools/qa/precip_models.js) in one page per scene, same mocked start time and seed.
//   node tools/qa/precip_models_capture.cjs --pw <playwright package dir> --root <generated tree> --out <bulk dir>
//        --only <regex on scene id> [--secs 4] [--list 1] [--throttle 1] [--models M3,M4,M5 (subset re-capture)]
// Capture: Chromium, CDP Page.startScreencast (lossless PNG frames with compositor timestamps) while the mocked
// clock RUNS at wall rate, so CSS animation, rAF cloud motion and the overlay run unassisted. Card 325x530, DPR 1.
// Network: precip_eval_lib.cjs installs the catch-all route on the context before any page exists, continues only
// loopback and fails the run (exit 2) on any non-loopback continuation; every request is logged in meta.json.
// Scenes: day / twilight / night x regimes x wind; opposing winds x two camera azimuths; expiry policies; evidence
// semantics (amount unavailable); reduced-motion stills (screenshots). Per model: frames, overlay record, cost.
const L=require('./precip_eval_lib.cjs');const fs=L.fs,path=L.path;
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const SECS=+(a.secs||4);
const DATES={equinox:'2026-09-23',newmoon:'2026-09-11'};
// regime fixtures: amount = mm per 15-min interval (product converts x4 to mm/h); dew point sets the cloud base
const DECK={cloud:98,low:95,mid:80,high:50};
const RG={
  drizzle:{code:53,precip:0.08,rain:0.08,...DECK,temp:58,hum:96,dew:56.5,vis:3000},          // 0.32 mm/h, base ~100 m, mist vis 3 km
  light:{code:61,precip:0.3,rain:0.3,...DECK,temp:60,hum:92,dew:55,vis:20000},              // 1.2 mm/h
  moderate:{code:63,precip:1.25,rain:1.25,...DECK,temp:60,hum:93,dew:55,vis:20000},         // 5 mm/h
  heavy:{code:65,precip:3,rain:3,...DECK,cloud:100,temp:62,hum:95,dew:57.5,vis:20000},      // 12 mm/h (heavy-class interior)
  showers:{code:81,precip:0.75,showers:0.75,cloud:45,low:35,mid:25,high:10,temp:70,hum:70,dew:55.5,vis:20000},   // 3 mm/h cell-mean, base ~1 km
  dry:{code:3,precip:0,...DECK,temp:60,hum:85,dew:52,vis:20000},
  unavail:{code:63,precip:null,...DECK,temp:60,hum:93,dew:55,vis:20000},
};
const WIND={calm:{wind:0.3,wdir:225,gust:0.5},w8:{wind:8,wdir:270,gust:9},w8g:{wind:8,wdir:270,gust:20},
  e8:{wind:8,wdir:90,gust:9},n8:{wind:8,wdir:0,gust:9},s8:{wind:8,wdir:180,gust:9}};
const MODELS_ALL=['current','M1','M2','M3','M4','M5'];
function scenes(){const out=[],site=L.SITES.madinah;
  const at=(dk,sc)=>{const st=L.sceneTimes(site,DATES[dk]);return Math.floor(st[sc]/900000)*900000+6*60000;};
  const add=(id,dk,sc,rg,wd,extra)=>out.push({id,date:dk,scene:sc,utcMs:at(dk,sc),wx:{...RG[rg],...WIND[wd]},rg,wd,models:MODELS_ALL,...(extra||{})});
  for(const rg of ['drizzle','light','moderate','heavy','showers'])for(const wd of ['calm','w8','w8g'])add(`day-${rg}-${wd}`,'equinox','solar-noon',rg,wd);
  add('day-dry-calm','equinox','solar-noon','dry','calm');
  for(const rg of ['drizzle','light','moderate','heavy','showers']){
    add(`twi-${rg}-calm`,'equinox','blue-hour',rg,'calm');
    add(`nightmoon-${rg}-calm`,'equinox','night-early',rg,'calm');
    add(`nightdark-${rg}-calm`,'newmoon','night-early',rg,'calm');}
  // orientation: opposing winds x two camera azimuths; product rain, M1 parallel, M1 perspective (rigid), M2 parallel
  for(const wd of ['w8','e8','n8','s8'])for(const az of [180,90])
    add(`orient-moderate-${wd}-az${az}`,'equinox','solar-noon','moderate',wd,{hash:az===180?'':`&skyAz=${az}`,models:['current','M1','M1:rigid','M2']});
  for(const rg of ['light','moderate','heavy'])add(`tlong-${rg}-w8`,'equinox','solar-noon',rg,'w8',{models:['M1','M1~67','M2','M2~67']});
  for(const rg of ['drizzle','light','moderate','heavy','showers'])add(`gain-${rg}-calm`,'equinox','solar-noon',rg,'calm',{models:['current','M1','M1^400','M2','M2^400','M3^400']});
  add('frame-moderate-w8','equinox','solar-noon','moderate','w8',{models:['M1','M1:rigid','M2','M2:rigid','M5','M5:rigid']});
  // expiry: provider fails after the first record; clock jumped to boundary-3 s; 12 s real-time across expiry
  for(const rg of ['moderate','heavy'])for(const m of ['current','M1|immediate','M1|complete','M2|immediate','M2|complete','M5|complete'])
    add(`expiry-${rg}-${m.replace('|','-')}`,'equinox','solar-noon',rg,'w8',{models:[m],expiry:true});
  // evidence semantics: rain code, amount unavailable (product today; category-only minimum-rate depictions)
  add('evidence-unavailable','equinox','solar-noon','unavail','calm',{models:['current','M1+cat','M2+cat','M4+cat']});
  // reduced motion (OS reduce, no motion=full): screenshots of each model
  for(const rg of ['drizzle','light','moderate','heavy','showers'])add(`reduced-${rg}`,'equinox','solar-noon',rg,'w8',{reduced:true});
  return out;}
const RECTS=L.RECTS;
(async()=>{let list=scenes();if(a.only)list=list.filter(s=>new RegExp(a.only).test(s.id));
  if(a.models){const want=a.models.split(',');list=list.map(s=>({...s,models:s.models.filter(m=>want.includes(m.split(/[|:~^+]/)[0]))})).filter(s=>s.models.length);}if(a.list){console.log(list.map(s=>s.id+' '+s.models.join(',')).join('\n'));return;}
  const pw=require(a.pw),root=path.resolve(a.root||'.'),out=path.resolve(a.out);
  const ordinary=JSON.parse(fs.readFileSync(L.ordinaryPath,'utf8'));const overlay=fs.readFileSync(path.join(__dirname,'precip_models_geom.js'),'utf8')+String.fromCharCode(10)+fs.readFileSync(path.join(__dirname,'precip_models.js'),'utf8');
  const {srv,base}=await L.serve(root);const browser=await pw.chromium.launch({headless:a.headed!=='1',args:['--ignore-gpu-blocklist']});let bad=0;
  try{for(const sc of list){const t0=Date.now(),site={...L.SITES.madinah},dir=path.join(out,sc.id);fs.mkdirSync(dir,{recursive:true});
    for(const f of fs.readdirSync(dir,{recursive:true}))if(/\.png$/.test(f))fs.rmSync(path.join(dir,f),{force:true});
    const s=await L.openScene(browser,base,ordinary,{site,utcMs:sc.utcMs,wx:sc.wx,hash:(sc.hash||'')+(sc.reduced?'':'&motion=full'),reduced:!!sc.reduced,clock:'running',wxFailAfter:sc.expiry?1:null});
    const meta={id:sc.id,scene:sc,url:s.url,mockedStartUtc:new Date(sc.utcMs).toISOString(),models:{}};
    try{
      meta.ready=await L.waitReady(s.page,{maxMs:16000});
      for(let i=0;i<40;i++){const st=await s.page.evaluate(L.STATE);if(st.header.wt&&st.qa&&st.qa.wxTruth&&st.qa.wxTruth.currentWeatherSource&&!/none|unavail/i.test(st.qa.wxTruth.currentWeatherSource))break;await s.page.waitForTimeout(250);}
      await s.page.waitForTimeout(2000);
      await s.page.addScriptTag({content:overlay});
      meta.state=await s.page.evaluate(L.STATE);meta.rects=await s.page.evaluate(RECTS);
      const GEO=`(()=>{const r=s=>{const e=document.querySelector(s);if(!e)return null;const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height].map(v=>+v.toFixed(2))};
        return {card:r('.c'),header:r('.h'),footer:r('.d'),rows:[...document.querySelectorAll('.p')].map(p=>{const b=p.getBoundingClientRect();return [b.x,b.y,b.width,b.height].map(v=>+v.toFixed(2))}),
        overlayParents:[...document.querySelectorAll('.pm-rain')].map(e=>e.parentElement.id),glass:getComputedStyle(document.querySelector('.p')).backdropFilter}})()`;
      meta.geomProduct=await s.page.evaluate(GEO);
      const cdp=await s.ctx.newCDPSession(s.page);
      for(const spec of sc.models){
        const [mf00,policyStr]=spec.split('|'),[mf0,Gx]=mf00.split('^'),[mf,Tms]=mf0.split('~'),[mname,frm]=mf.replace('+cat','').split(':'),cat=mf.includes('+cat');
        const mdir=path.join(dir,spec.replace(/[|:+~^]/g,'_'));fs.mkdirSync(mdir,{recursive:true});
        await s.page.evaluate(([m,f,p,c,tm,gx])=>window.__PM.set(m==='current'?'off':m,f||'flat',{policy:p||'immediate',categoryOnly:c,T:tm?tm/1000:null,G:gx}),[mname,frm,policyStr,cat,Tms?+Tms:null,Gx?+Gx:null]);
        await s.page.waitForTimeout(900);
        const rec={spec,frames:[],records:[]};
        if(sc.reduced){await s.page.waitForTimeout(600);await s.page.screenshot({path:path.join(mdir,'still.png')});rec.records.push(await s.page.evaluate(()=>window.__PM.last));}
        else{
          if(sc.expiry){ // jump to 3 s before the next quarter-hour boundary (record validity end), then real time
            const now=await s.page.evaluate(()=>Date.now()),B=Math.ceil((now+1)/900000)*900000;await s.page.clock.pauseAt(B-3000);await s.page.clock.resume();rec.boundaryUtc=B;}
          const frames=[];const onF=f=>{frames.push({ts:f.metadata.timestamp,data:f.data});cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId}).catch(()=>{});};
          cdp.on('Page.screencastFrame',onF);await cdp.send('Page.startScreencast',{format:'png',maxWidth:325,maxHeight:530,everyNthFrame:1});
          const dur=sc.expiry?12000:SECS*1000,tA=Date.now();
          while(Date.now()-tA<dur){await s.page.waitForTimeout(500);try{rec.records.push(await s.page.evaluate(()=>{const r=window.__PM.last;const c=document.querySelector('.c');return r?{...r,precip:c.dataset.precip,fx:c.dataset.fx,now:Date.now()}:{precip:c.dataset.precip,fx:c.dataset.fx,now:Date.now()};}));}catch(e){}}
          await cdp.send('Page.stopScreencast');cdp.off('Page.screencastFrame',onF);
          frames.forEach((f,i)=>{fs.writeFileSync(path.join(mdir,`f${String(i).padStart(4,'0')}.png`),Buffer.from(f.data,'base64'));rec.frames.push(f.ts);});
          if(sc.expiry)rec.completionBound=await s.page.evaluate(()=>window.__PM.completionBound());
        }
        rec.geom=await s.page.evaluate(GEO);
        if(mname!=='current'){rec.costMs=await s.page.evaluate(()=>window.__PM.cost(120));
          if(a.throttle==='1'){await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});rec.costMs4x=await s.page.evaluate(()=>window.__PM.cost(60));await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});}}
        meta.models[spec]=rec;
        console.log(`  ${sc.id} ${spec} frames=${rec.frames.length} fps=${rec.frames.length>1?((rec.frames.length-1)/(rec.frames[rec.frames.length-1]-rec.frames[0])).toFixed(1):'-'} cost=${rec.costMs!=null?rec.costMs.toFixed(3):'-'}${rec.costMs4x!=null?'/4x '+rec.costMs4x.toFixed(3):''}`);
      }
    }catch(e){meta.error=String(e&&e.message||e).slice(0,300);}
    meta.providerLog=s.log.requests;meta.aborted=[...new Set(s.log.aborted)];meta.continuedExternal=s.log.continuedExternal;meta.requestsSeen=s.log.all;meta.errors=s.log.errors||[];
    await s.ctx.close();if(meta.continuedExternal.length){bad++;meta.error='EXTERNAL REQUEST CONTINUED';}
    meta.wallMs=Date.now()-t0;fs.writeFileSync(path.join(dir,'meta.json'),JSON.stringify(meta));
    console.log(`${sc.id} ${meta.error?'ERROR '+meta.error:'ok'} ${meta.wallMs}ms precip=${meta.state&&meta.state.data.precip} fx=${meta.state&&meta.state.data.fx} requests=${meta.requestsSeen} ext=${meta.continuedExternal.length} aborted=${meta.aborted.join('|')}`);}
  }finally{await browser.close().catch(()=>{});srv.close();}
  if(bad){console.error('external requests continued:',bad);process.exit(2);}
})().catch(e=>{console.error(e);process.exit(1);});
