'use strict';

// A single sequential, held-scene capture. Never overwrite a capture directory.
// Input: pinned historical research checkout with the declared-gain patch, generated product tree.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const [pwPath,research,tree,out,engine,block,condition,model] = process.argv.slice(2);
const conditions = {dry:[3,0],drizzle:[53,.08],light:[61,.3],moderate:[63,1.25],heavy:[65,3],showers:[81,.75]};
const blocks = {bday:['2026-09-23','solar-noon',.3],bwind:['2026-09-23','solar-noon',8],
  btwi:['2026-09-23','blue-hour',.3],bmoon:['2026-09-23','night-early',.3],bdark:['2026-09-11','night-early',.3]};
if(!blocks[block]||!conditions[condition]||!['chromium','webkit','firefox'].includes(engine)||!['current','M1','M2','M3','M4','M5'].includes(model))
  throw Error('usage: capture.cjs PLAYWRIGHT RESEARCH TREE NEW_DIR ENGINE BLOCK CONDITION MODEL');
const L = require(path.resolve(research,'tools/qa/precip_eval_lib.cjs'));
const sha = v=>crypto.createHash('sha256').update(v).digest('hex');
const source = name=>fs.readFileSync(path.resolve(research,'tools/qa',name));
async function run(){
  const [date,scene,wind]=blocks[block], [code,amount]=conditions[condition];
  const site=L.SITES.madinah, utcMs=Math.floor(L.sceneTimes(site,date)[scene]/900000)*900000+360000;
  const held={cloud:85,low:75,mid:60,high:40,temp:60,hum:92,dew:55,vis:20000,wind,wdir:wind===8?270:225,gust:wind===8?9:.5};
  const wx={...held,code,precip:amount,rain:condition==='showers'?0:amount,showers:condition==='showers'?amount:0};
  const profile=JSON.parse(source('precip_declared_gain.json'));
  if(!profile.enforceDeclaredGain)throw Error('apply declared-gain patch first');
  const geom=source('precip_models_geom.js'),renderer=source('precip_models.js');
  const ordinary=JSON.parse(fs.readFileSync(path.resolve(tree,'tests/r0002-ordinary.json')));
  fs.mkdirSync(out); const {srv,base}=await L.serve(tree);
  let browser,ctx;
  try{
    browser=await require(pwPath)[engine].launch();
    const options=process.env.R0040_OPTIONS?JSON.parse(fs.readFileSync(process.env.R0040_OPTIONS)):null;
    const target=options?{async newContext(args){const ctx=await browser.newContext(args);await ctx.addInitScript(o=>window.__R0040_OPTIONS__=o,options);return ctx;}}:browser;
    const s=await L.openScene(target,base,ordinary,{site,utcMs,wx,hash:'&motion=full',clock:'running'});ctx=s.ctx;
    const page=s.page;
    await L.waitReady(page,{maxMs:20000});
    await page.waitForFunction(()=>window.qaState?.().cache?.prayerLoaded&&window.qaState().clouds.ready);
    const sourceState=()=>page.evaluate(()=>{const w=selectedWeather();const c=document.querySelector('.c');return {code:w?.code,amount:w?.precip,interval:w?.currentIntervalSec,source:w?.src,permission:c.dataset.precip};});
    const before=await sourceState();
    const check=x=>x.source==='current'&&x.code===code&&x.amount===amount&&x.interval===900&&x.permission===(amount>0?'on':'off');
    if(!check(before))throw Error('unexpected admitted source '+JSON.stringify(before));
    const dispersion=process.env.R0040_DISPERSION||null;
    if(dispersion&&(!['current','M1','M2','M3'].includes(model)||!(dispersion==='common'||model==='M2'&&dispersion==='diameter')))
      throw Error('treatment outside the revised-study design');
    if(dispersion&&!renderer.includes('window.__R0040_STUDY'))throw Error('apply the layer study patch');
    await page.evaluate(([p,d])=>{window.__PM_PARAMS=p;if(d)window.__R0040_STUDY={dispersion:d}},[profile,dispersion]);
    await page.addScriptTag({content:geom.toString()+'\n'+renderer.toString()});
    const effective=await page.evaluate(m=>{
      window.__PM.set(m==='current'?'off':m,'flat',{policy:'immediate'});
      window.__PM.frame(performance.now());
      return window.__PM.params;
    },model);
    const light=await page.evaluate(()=>{const q=window.qaState();return {sun:q.sunEl,moon:q.moonTruth.moonlightOpacity,
      moonAltitude:q.moonTruth.moonAltitudeDeg,moonFresh:q.moonTruth.moonSkyFresh};});
    const clock=engine==='chromium'?'browser-native-epoch-ms':'runner-monotonic-ms';
    const rects=await page.evaluate(L.RECTS);
    await page.evaluate(({utc,rectRecipe})=>{
      // Publish the same source/geometry tuple synchronously when the native-clock sampler requests it.
      const bus=document.createElement('span');bus.id='r0040-audit';bus.hidden=true;document.body.appendChild(bus);
      const box=e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]};
      window.__r0040Sample=()=>{
        const card=document.querySelector('.c'),r=window.__PM.last,w=selectedWeather();
        return {phaseMs:Date.now()-utc,poseMs:r?.t,treatment:window.__PM.studyTreatment??'historical',tuple:[w?.code,w?.precip,w?.currentIntervalSec,card.dataset.precip,
          r?.model,r?.policy,r?.G,r?.T,r?.R??null],geometry:{card:box(card),header:box(document.querySelector('.h')),
          footer:box(document.querySelector('.d')),rows:[...document.querySelectorAll('.p')].map(box),
          glass:getComputedStyle(document.querySelector('.p')).backdropFilter},rects:eval(rectRecipe)};
      };
      bus.addEventListener('r0040-read',()=>{bus.textContent=JSON.stringify(window.__r0040Sample());});
    },{utc:utcMs,rectRecipe:L.RECTS});
    const geometry=(await page.evaluate(()=>window.__r0040Sample())).geometry;
    const frames=[],states=[];
    const record=(bytes,t,acquisitionMs=0)=>{const file='f'+String(frames.length).padStart(5,'0')+'.png';
      frames.push({file,t,acquisitionMs,sha256:sha(bytes)});fs.writeFileSync(path.join(out,file),bytes);};
    let method;
    if(engine==='chromium'){
      method='compositor-png';
      const cdp=await ctx.newCDPSession(page), {frameTree}=await cdp.send('Page.getFrameTree');
      const {executionContextId}=await cdp.send('Page.createIsolatedWorld',{frameId:frameTree.frame.id,worldName:'r0040-native-clock'});
      const isolated=async expression=>{
        const r=await cdp.send('Runtime.evaluate',{contextId:executionContextId,expression,returnByValue:true});
        if(r.exceptionDetails)throw Error('isolated clock acquisition failed');return r.result.value;};
      await isolated(`(()=>{globalThis.samples=[];globalThis.active=true;const bus=document.querySelector('#r0040-audit');
        const read=ts=>{if(!active)return;bus.dispatchEvent(new Event('r0040-read'));
          samples.push({...JSON.parse(bus.textContent),at:performance.timeOrigin+ts});requestAnimationFrame(read);};
        requestAnimationFrame(read);return true;})()`);
      cdp.on('Page.screencastFrame',f=>{void cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId}).catch(()=>{});
        record(Buffer.from(f.data,'base64'),1000*f.metadata.timestamp);});
      await cdp.send('Page.startScreencast',{format:'png',maxWidth:325,maxHeight:530,everyNthFrame:1});
      await page.waitForTimeout(3300);await cdp.send('Page.stopScreencast');
      states.push(...await isolated('globalThis.active=false; globalThis.samples'));await cdp.detach();
      if(!states.length||!frames.length)throw Error("empty compositor or native audit stream");
      for(const f of frames)f.auditIndex=states.reduce((best,x,i)=>Math.abs(x.at-f.t)<Math.abs(states[best].at-f.t)?i:best,0);
      const first=frames[0].auditIndex,last=frames.at(-1).auditIndex;
      states.splice(last+1);states.splice(0,first);
      for(const f of frames)f.auditIndex-=first;
    }else{
      method='bracketed-screen-png';
      const begin=performance.now();
      while(performance.now()-begin<3300){
        const preStart=performance.now(),prior=await page.evaluate(()=>window.__r0040Sample());const a=performance.now();
        const bytes=await page.screenshot({type:'png',animations:'allow'});const b=performance.now();
        const post=await page.evaluate(()=>window.__r0040Sample()),postEnd=performance.now();
        record(bytes,(a+b)/2,b-a);frames.at(-1).auditIndex=states.length;
        states.push({...prior,at:(preStart+a)/2,uncertaintyMs:(a-preStart)/2},
          {...post,at:(b+postEnd)/2,uncertaintyMs:(postEnd-b)/2});
      }
    }
    const audit={clock,states};
    const after=await sourceState();
    const cost={};
    if(model!=='current'){
      const measure=()=>page.evaluate(()=>{
        const samples=[];for(let i=0;i<120;i++){const start=performance.now();window.__PM.frame(start);samples.push(performance.now()-start);}
        samples.sort((a,b)=>a-b);return {n:samples.length,mean:samples.reduce((a,b)=>a+b)/samples.length,p95:samples[Math.ceil(.95*samples.length)-1],
          resolutionLimited:samples.every(v=>v===0)};
      });
      cost.normal=await measure();
      if(engine==='chromium'){const session=await ctx.newCDPSession(page);try{await session.send('Emulation.setCPUThrottlingRate',{rate:4});cost.throttle4=await measure();}
        finally{await session.send('Emulation.setCPUThrottlingRate',{rate:1});await session.detach();}}
    }
    if(!check(after)||s.log.errors?.length||s.log.continuedExternal.length)throw Error('unstable source, page error or network escape');
    const log={schema:3,evidenceClass:'native-controlled-capture',options,design:dispersion?"revised":"historical",treatment:dispersion||"historical",clock,engine,block,condition,model,method,scene,utcMs,held,wx,before,after,profile,effective,geometry,rects,light,audit,cost,dispersion,
      productSha:sha(fs.readFileSync(path.resolve(tree,'index.html'))),rendererSha:sha(renderer),geometrySha:sha(geom),frames};
    fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(log));
  }finally{try{await ctx?.close()}finally{try{await browser?.close()}finally{srv.close()}}}
}
run().catch(e=>{console.error(e);process.exitCode=1});
