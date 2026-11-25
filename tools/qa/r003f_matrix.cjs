'use strict';
require('./v1_net_guard.cjs').install();
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const iso=require('./r0033_isolation.cjs');
const {buildMasks,measure,inhibitedLightVerdict,compareCards}=require('./r003f_p1.cjs');
const {cells,fragment,weather}=require('./r003f_grid.cjs');
const {makeServer,prayerFixture,clearWeather,facts,readUiMask,checkPair,aperture}=require('./r003f_capture.cjs');
const {variants,renderVariant,hash}=require('./r003f_variants.cjs');
const {terrain,terminator,occultation,deltaE,buckleRate}=require('./r003f_diagnostics.cjs');
const {parseArgs}=require('node:util');
const {values:a}=parseArgs({options:{...Object.fromEntries(['root','out','engine','dpr','id','variant','raster-proof','playwright','pngjs','executable'].map(k=>[k,{type:'string'}])),
  list:{type:'boolean'}}});
const engine=a.engine||'chromium',dpr=Number(a.dpr||1);assert.ok(['chromium','firefox','webkit'].includes(engine)&&[1,2].includes(dpr));
const manifest=cells(engine,dpr);
if(a.list){fs.writeFileSync(1,JSON.stringify(manifest,null,2)+'\n');process.exit(0);}
const cell=manifest.find(c=>c.id===a.id);assert.ok(cell,'select a cell ID from --list');
const names=a.variant?[a.variant]:variants;assert.ok(names.every(n=>variants.includes(n)));
const out=path.resolve(a.out),root=fs.realpathSync(a.root),zone='America/New_York';
const index=fs.readFileSync(path.join(root,'index.html'),'utf8'),source=fs.readFileSync(path.join(root,'moon/src/moon-calendar.mjs'),'utf8').trimEnd();
const builds=new Map([...new Set(['B0',...names,...names.map(n=>n.split('-')[0])])].map(n=>[n,renderVariant(index,source,n)]));
const server=makeServer(root,n=>{assert.ok(builds.has(n));return builds.get(n).html;});
const prayer=prayerFixture(JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'))),zone);
const pw=require(a.playwright||'playwright'),{PNG}=require(a.pngjs||'pngjs');
function packageIdentity(request,name){
  const entry=fs.realpathSync(require.resolve(request));
  try{if(entry!==fs.realpathSync(require.resolve(name)))return null;}catch{return null;}
  let dir=path.dirname(entry);
  while(path.dirname(dir)!==dir){
    const file=path.join(dir,'package.json');
    if(fs.existsSync(file)){
      const meta=JSON.parse(fs.readFileSync(file));
      if(meta.name===name && fs.realpathSync(require.resolve(dir))===entry)
        return {name,version:meta.version,entrySha256:hash(fs.readFileSync(entry))};
    }
    dir=path.dirname(dir);
  }
  return null;
}
const driver=packageIdentity(a.playwright||'playwright','playwright'),decoder=packageIdentity(a.pngjs||'pngjs','pngjs');
const report={protocol:'R003F/P1/native-matrix/2',evidenceClass:driver&&decoder?'native':'injected-diagnostic',driver,decoder,archiveIndexSha256:hash(index),cell,engine,dpr,names,builds:[...builds.values()].map(b=>b.identity),captures:{},pairs:[],metrics:[]};
const write=(n,data)=>fs.writeFileSync(path.join(out,n),data);
const documents=new WeakMap();let serial=0;
let origin,context,session;
const fail=msg=>{const error=Error(msg);error.andon=true;throw error;};
function holdRefinement(){
  // Stop just the lunar publication messages arriving at the host. Other
  // workers (including sky) continue. Release in arrival order on this worker.
  const Original=window.Worker, queue=[];
  window.__releaseR003F=()=>{window.__r003fReleased=true;for(const [w,data] of queue.splice(0))w.dispatchEvent(new MessageEvent('message',{data}));};
  window.Worker=class extends Original{
    constructor(...args){super(...args);this.addEventListener('message',e=>{
      if(!window.__r003fReleased && ['result','preview'].includes(e.data?.kind)&&e.data?.calendarLinear instanceof Float32Array){
        e.stopImmediatePropagation();queue.push([this,e.data]);
      }
    });}
  };
}
async function open(name,offset=false,options={}){
  const c=options.cell||cell,p=await context.newPage();
  const epoch=options.epoch||c.epoch,d=new Date(epoch);
  const wall=new Intl.DateTimeFormat('sv-SE',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(d).replace(' ','T');
  await p.clock.setFixedTime(d);
  await p.addInitScript(clearWeather,{...weather[c.weather],is_day:c.mode==='daylight'?1:0,time:wall});
  if(c.mode==='unavailable')await p.addInitScript(()=>{
    // A genuine construction failure at the runtime install boundary also
    // withholds the head receiver. The product's own failure path owns the slot.
    Object.defineProperty(window,'SalahMoonRuntime',{configurable:false,get:()=>undefined,
      set(){throw Error('R003F controlled runtime construction failure');}});
  });
  if(options.hold!==false)await p.addInitScript(holdRefinement);
  const url=origin+'/index.html?variant='+name+fragment(c,offset);
  const response=await p.goto(url),expected=builds.get(name).identity.indexSha256;
  const responseSha256=response?.body?hash(await response.body()):null;
  if(report.evidenceClass==='native')assert.equal(responseSha256,expected,'served variant response identity');
  documents.set(p,{id:++serial,name,offset,url,responseSha256});
  if(c.mode==='no-backdrop')await p.addStyleTag({content:'.e,.wt{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'});
  if(c.mode==='away'){
    await p.waitForFunction(()=>document.querySelector('.c')?.classList.contains('moon-ready'));
    await p.waitForFunction(()=>window.SalahMoonDetail?.state.visible);
    const before=await p.locator('.moccluder').boundingBox(),detailBefore=await p.locator('.moon-detail-canvas').boundingBox();
    await p.addStyleTag({content:'.moon{translate:0 60px!important}'});
    const after=await p.locator('.moccluder').boundingBox();
    assert.ok(before&&after&&Math.abs(after.y-before.y-60)<1,'60 px Moon translation not observed');
    await p.waitForFunction(y=>{const d=document.querySelector('.moon-detail-canvas')?.getBoundingClientRect();return d&&Math.abs(d.y-y-60)<1.1;},detailBefore.y,{timeout:10000});
    documents.get(p).translation={before,after,detailBefore,detailAfter:await p.locator('.moon-detail-canvas').boundingBox()};
  }
  if(c.mode==='long-text'){
    await p.evaluate(()=>{const e=document.querySelector('.wt');const enforce=()=>{if(e.textContent!=='Controlled long weather description')e.textContent='Controlled long weather description';};enforce();new MutationObserver(enforce).observe(e,{subtree:true,childList:true,characterData:true});});
  }
  return p;
}
async function waitTier(p,tier,profile){
  await p.waitForFunction(({tier,profile})=>{
    const c=document.querySelector('.c'),s=window.SalahMoonRuntime?.observe()?.state;
    return c?.classList.contains('moon-ready')&&c.classList.contains('real-sky-composed')&&
      s?.visibleSource===(tier==='initial'?'initial-v5':'refined-terrain')&&s.quality===(tier==='initial'?'initial-v5':'empirical-adaptive')&&s.accepted?.scene?.profile?.profile_id===profile;
  },{tier,profile},{timeout:150000,polling:200});
}
async function shot(p,tag,tier,options={}){
  const profile=options.reference?'unboosted-v5-01':'calendar-neutral-v5-01';
  await waitTier(p,tier,profile);await p.waitForTimeout(2500);
  const state=await p.evaluate(facts);
  const image=await p.locator('.c').screenshot(),decoded=PNG.sync.read(image);
  const after=await p.evaluate(facts);
  const targetCell=options.cell||cell,admission={tier,offset:!!options.offset,reference:!!options.reference};
  try{checkPair(state,after,targetCell,admission);}catch(e){report.rejected={tag,state,after,reason:e.message};throw e;}
  assert.equal(decoded.width,325*dpr);assert.equal(decoded.height,530*dpr);
  write(tag+'.png',image);
  const cloud=await p.evaluate(()=>{
    const cv=document.querySelector('.cloudcanvas');
    if(!cv||cv.width<1||cv.height<1)return null;
    const g=cv.getContext('2d').getImageData(0,0,cv.width,cv.height),b=cv.getBoundingClientRect(),disc=document.querySelector('.moccluder').getBoundingClientRect();
    const data=[];let covered=0;
    for(let y=0;y<cv.height;y++)for(let x=0;x<cv.width;x++){
      const dx=b.left+(x+.5)*b.width/cv.width-disc.left-disc.width/2,dy=b.top+(y+.5)*b.height/cv.height-disc.top-disc.height/2;
      if(Math.hypot(dx,dy)>disc.width/2)continue;
      const i=(y*cv.width+x)*4;data.push(...g.data.subarray(i,i+4));if(g.data[i+3])covered++;
    }
    return {rgba:data,covered};
  });
  if(cloud)write(tag+'-cloud.rgba',Buffer.from(cloud.rgba));
  const cloudInfo=cloud&&{sha256:hash(Buffer.from(cloud.rgba)),pixels:cloud.rgba.length/4,nonzeroAlpha:cloud.covered};
  const boxes=await p.evaluate(()=>{const card=document.querySelector('.c').getBoundingClientRect();return Object.fromEntries(['.wt','.buckle','.e','.h','.moccluder','.moon-detail-canvas'].map(s=>{
    const e=document.querySelector(s),b=e.getBoundingClientRect();return [s,{x:b.x-card.x,y:b.y-card.y,w:b.width,h:b.height,filter:getComputedStyle(e).backdropFilter}];
  }));});
  if(cell.mode==='long-text')assert.ok(Math.abs(boxes['.wt'].w-128)<.5,'weather strap did not reach 128 px');
  if(cell.mode==='no-backdrop')assert.ok(['.wt','.e'].every(s=>['none',''].includes(boxes[s].filter)));
  report.captures[tag]={state,after,admission,document:documents.get(p),boxes,cloud:cloudInfo,sha256:hash(image)};
  return {tag,state,pixels:decoded.data,cloud:cloudInfo,boxes};
}
async function diff(p,b,c,label){
  assert.deepEqual(b.state.disc,c.state.disc,label+' geometry differs');
  for(const k of ['acceptedFraction','nativeFraction','waxing','up','light','weatherFields','source','quality','profile'])
    assert.deepEqual(b.state[k],c.state[k],label+' unmatched '+k);
  const d=compareCards(dpr,b.state.disc,b.pixels,c.pixels),rect=c.boxes['.buckle'];
  let buckle=0,buckleMax=0,outMax=0;
  for(let k=0;k<d.outside.length;k+=256){
    const points=d.outside.slice(k,k+256);
    const stacks=await p.evaluate(({points,dpr})=>{const card=document.querySelector('.c').getBoundingClientRect();return points.map(v=>document.elementsFromPoint(card.x+(v.x+.5)/dpr,card.y+(v.y+.5)/dpr).map(e=>[e.localName,e.id,e.className?.baseVal??e.className]));},{points,dpr});
    fs.appendFileSync(path.join(out,'outside.jsonl'),points.map((v,j)=>JSON.stringify({pair:label,...v,stack:stacks[j]})).join('\n')+'\n');
    for(const v of points){
      const x=(v.x+.5)/dpr,y=(v.y+.5)/dpr,max=Math.max(...v.delta.map(Math.abs));
      outMax=Math.max(outMax,max);
      if(x>=rect.x&&x<rect.x+rect.w&&y>=rect.y&&y<rect.y+rect.h){buckle++;buckleMax=Math.max(buckleMax,max);}
    }
  }
  const pair={label,base:b.tag,candidate:c.tag,changed:d.changedPixels,outside:d.outside.length,outMax,buckle,buckleMax,signature51x16:buckle===51&&buckleMax===16};
  report.pairs.push(pair);return pair;
}
async function hiddenFrame(p,frame,tier){
  if(!await p.evaluate(()=>window.SalahMoonRuntime.observe().detailAvailable&&window.SalahMoonDetail?.state.visible))return null;
  const style=await p.addStyleTag({content:'.moon,.moon-detail-canvas{visibility:hidden!important}'});
  try{
    const before=await p.evaluate(facts),png=await p.locator('.c').screenshot(),after=await p.evaluate(facts);
    const admission={tier,offset:false,reference:false,hidden:true};checkPair(before,after,cell,admission);
    assert.deepEqual(before.disc,frame.state.disc);const tag='hidden-'+tier;
    write(tag+'.png',png);report.captures[tag]={state:before,after,admission,document:documents.get(p),sha256:hash(png)};
    return PNG.sync.read(png).data;
  }finally{await style.evaluate(e=>e.remove());}
}
async function optionalRefinement(work,tag){
  try{return await work();}catch(e){
    if(e.andon||e.name!=='TimeoutError')throw e;
    (report.tierDisposition??={})[tag]={refined:'unavailable after timeout',reason:e.message};
    return null;
  }
}
async function twoTiers(p,tag,options={},onFrame){
  const initial=await shot(p,tag+'-initial','initial',options);
  if(onFrame)await onFrame(initial,'initial');
  await p.evaluate(()=>window.__releaseR003F());
  const refined=await optionalRefinement(()=>shot(p,tag+'-refined','refined',options),tag);
  if(refined&&onFrame)await onFrame(refined,'refined');
  return {initial,refined};
}
async function still(){
  const controls=await open('B0',true);
  let offsets;
  try{offsets=await twoTiers(controls,'offset',{offset:true});}finally{await controls.close();}
  const base=await open('B0'),hidden={},uiMasks={},masks={},envelopes={};
  const b0=await twoTiers(base,'b0',{},async(f,t)=>{
    const ui=await base.evaluate(readUiMask,{disc:f.state.disc,dpr});uiMasks[t]=ui;
    write('ui-'+t+'.json',JSON.stringify(ui));
    hidden[t]=await hiddenFrame(base,f,t);
  });
  await base.evaluate(()=>window.SalahMoonRuntime.setProfile('reference'));
  const reference=await optionalRefinement(()=>shot(base,'reference','refined',{reference:true}),'reference');
  const repeatPage=await open('B0');
  const repeats=await twoTiers(repeatPage,'baseline-repeat',{},async(f,t)=>{
    if(b0[t])envelopes[t]=await diff(repeatPage,b0[t],f,'baseline-envelope-'+t);
  });
  await repeatPage.close();
  for(const tier of ['initial','refined']){
    if(!reference||!offsets[tier]||!b0[tier])continue;
    const ui=uiMasks[tier],allowed=new Uint8Array(325*530*dpr*dpr);for(const i of ui.allowed)allowed[i]=1;
    for(const f of [b0[tier],offsets[tier]])assert.deepEqual(reference.state.disc,f.state.disc);
    for(const k of ['acceptedFraction','nativeFraction','waxing','up','light','weatherFields'])assert.deepEqual(reference.state[k],b0[tier].state[k],'reference mismatch '+k);
    masks[tier]=buildMasks({dpr,fraction:cell.fraction,disc:reference.state.disc,offsetDisc:offsets[tier].state.disc,newMoon:offsets[tier].pixels,reference:reference.pixels,
      headerRects:ui.headerRects,topIsSkyOrMoon:allowed});
    const m=masks[tier];write('masks-'+tier+'.json',JSON.stringify({lit:m.lit,dark:m.dark,sky:m.sky.map(p=>p.i),g0:m.g0,p95:m.p95,maskOverlapPixels:m.maskOverlapPixels}));
  }
  // Each horizon cell's DB1 lower endpoint must be sampled with that
  // cell's reference mask. Record which absolute device pixels are used.
  const lower=new Map();
  if(cell.group==='horizon'&&cell.alt>-2&&cell.alt<4){
    for(const name of names){
      const p=await open(name,false,{cell:{...cell,alt:-2},hold:false});
      try{
        const low=await optionalRefinement(()=>shot(p,name+'-minus2','refined',{cell:{...cell,alt:-2}}),name+'-minus2');
        if(masks.refined&&low)lower.set(name,measure(masks.refined,low.pixels).litMeanY);
      }finally{await p.close();}
    }
  }
  await base.close();
  const plain=new Map([['B0',b0]]);
  for(const name of [...new Set([...names.map(n=>n.split('-')[0]),...names])]){
    const p=await open(name);
    try{
      const frames=await twoTiers(p,name);
      if(!name.endsWith('-T'))plain.set(name,frames);
      for(const tier of ['initial','refined']){
        const f=frames[tier],m=masks[tier];
        if(!f||!b0[tier]){report.metrics.push({name,tier,status:'INCOMPLETE',reason:'missing same-tier capture or baseline'});continue;}
        const pair=await diff(p,b0[tier],f,name+'-'+tier);
        const cloudMatch=f.cloud&&b0[tier].cloud?f.cloud.sha256===b0[tier].cloud.sha256:null;
        const cloudRepeatStable=!!b0[tier].cloud&&b0[tier].cloud.sha256===repeats[tier]?.cloud?.sha256;
        if(cell.alt<=-2&&cloudRepeatStable&&cloudMatch===false)fail('candidate and B0 cloud RGBA differ with stable repeat');
        if(!m||!reference||!repeats[tier]){
          report.metrics.push({name,tier,tag:f.tag,pair:pair.label,cloudMatch,cloudRepeatStable,envelope:envelopes[tier]?.label??null,status:'INCONCLUSIVE',reason:'missing reference, offset or same-tier repeat'});continue;
        }
        const r=reference.pixels,b=b0[tier].pixels;
        const stats={name,tier,tag:f.tag,metrics:measure(m,f.pixels),base:measure(m,b),reference:measure(m,r),pair:pair.label,cloudMatch,
          terrain:{candidate:terrain(m,f.pixels),physical:terrain(m,r),base:terrain(m,b)},
          terminator:cell.fraction>=.15&&cell.fraction<=.85?terminator(m,f.pixels,r,cell.waxing):null,
          occlusion:hidden[tier]?{candidate:occultation(m,f.pixels,hidden[tier]),reference:occultation(m,r,hidden[tier])}:null,
          deltaE76:plain.get(name.split('-')[0])?.[tier]?deltaE(m,f.pixels,plain.get(name.split('-')[0])[tier].pixels):null};
        stats.aperture=aperture(stats.metrics);
        const same=ids=>ids.every(i=>[0,1,2,3].every(k=>b[4*i+k]===repeats[tier].pixels[4*i+k]));
        stats.repeatStable={lit:same(m.lit),dark:same(m.dark),sky:same(m.sky.map(p=>p.i))};
        stats.cloudRepeatStable=cloudRepeatStable;
        stats.repeat=measure(m,repeats[tier].pixels);stats.envelope=envelopes[tier].label;
        stats.inputs={candidate:f.tag,reference:'reference',offset:'offset-'+tier,base:'b0-'+tier,repeat:'baseline-repeat-'+tier,
          hidden:hidden[tier]?'hidden-'+tier:null,ui:'ui-'+tier+'.json',masks:'masks-'+tier+'.json'};
        if(tier==='refined'&&lower.has(name)&&stats.aperture.lit&&stats.repeatStable.lit){
          const L=require('./r003f_p1.cjs').lightness;
          const ys=[lower.get(name),stats.metrics.litMeanY,stats.reference.litMeanY];
          if(ys.every(Number.isFinite)){
            const [lo,mid,hi]=ys.map(L);stats.db1={minus2L:lo,litL:mid,referenceL:hi,
              convex:mid>=Math.min(lo,hi)-.5&&mid<=Math.max(lo,hi)+.5};
          }
        }
        report.metrics.push(stats);
        if(stats.aperture.dark&&stats.repeatStable.dark&&stats.occlusion?.candidate.starCoincidences?.length)fail('candidate dark-mask peak exceeds 3x median at hidden star-field peak; inspect captures');
      }
    }finally{await p.close();}
  }
}
async function ineligible(){
  for(const name of names){
    const p=await open(name,false,{hold:false});
    try{
      await p.waitForFunction(()=>window.qaState?.().cache.prayerLoaded && window.qaState?.().moonTruth?.lunarLight!=null,
        null,{timeout:150000});
      await p.waitForTimeout(2500);
      const f=await p.evaluate(facts);
      assert.ok(f.geometry.altitudeDeg>0 && f.motionReduced && f.prayerLoaded);
      if(cell.mode==='daylight')assert.ok(f.sunEl>=-3,'Sun did not reach the test regime');
      else assert.ok(!f.ready&&f.displayMode==='surface-unavailable'&&f.sunEl<-3,'missing-surface precondition');
      const v=inhibitedLightVerdict(f);
      if(v==='FAIL'||typeof f.beam==='string'&&f.beam.trim()&&Number.isFinite(Number(f.beam))&&Number(f.beam)!==0)fail('physical light with an inhibited source');
      assert.equal(v,'PASS');
      const png=await p.locator('.c').screenshot(),after=await p.evaluate(facts),admission={tier:'inhibited'};
      checkPair(f,after,cell,admission);write(name+'.png',png);report.captures[name]={state:f,after,admission,document:documents.get(p),sha256:hash(png)};
    }finally{await p.close();}
  }
}
async function repetitions(){
  for(const name of names){
    const counts={repeat:{any:0,signature:0,other:0},candidate:{any:0,signature:0,other:0}};
    for(let i=0;i<cell.repeats;i++){
      const order=i%2?['candidate','repeat']:['repeat','candidate'];
      for(const [position,kind] of order.entries()){
        const base=await open('B0',false,{hold:false}),target=await open(kind==='repeat'?'B0':name,false,{hold:false});
        try{
          const label=name+'-'+i+'-'+kind,b=await shot(base,label+'-base','refined');
          if(cell.mode==='header-toggle')await target.evaluate(async()=>{const e=document.querySelector('.h');e.style.setProperty('--r003f-noop','1');e.getBoundingClientRect();await new Promise(requestAnimationFrame);e.style.removeProperty('--r003f-noop');});
          const c=await shot(target,label+'-target','refined'),pair=await diff(target,b,c,label);
          Object.assign(pair,{round:i,arm:kind,position,name});
          if(pair.buckle){counts[kind].any++;counts[kind][pair.signature51x16?'signature':'other']++;}
        }finally{await target.close();await base.close();}
      }
    }
    report.metrics.push({name,counts,repeats:cell.repeats,tests:Object.fromEntries(['signature','other','any'].map(k=>
      [k,buckleRate(counts.repeat[k],counts.candidate[k],cell.repeats)]))});
  }
}
async function main(){
  fs.mkdirSync(out,{mode:0o700});write('outside.jsonl','');
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin='http://127.0.0.1:'+server.address().port;
  try{
    if(cell.gpu==='software'&&engine==='webkit'&&!a['raster-proof'])
      throw Error('WebKit CSS raster backend requires independent host evidence; supply --raster-proof with its underlying trace');
    const launcher={[engine]:{launch:opts=>pw[engine].launch({...opts,...(a.executable?{executablePath:a.executable}:{}),
      ...(cell.gpu==='software'&&engine==='firefox'?{firefoxUserPrefs:{...opts.firefoxUserPrefs,'gfx.webrender.software':true,'layers.acceleration.disabled':true}}:{}),
      ...(engine==='chromium'?{chromiumSandbox:true,args:[...opts.args,...(cell.gpu==='software'?['--disable-gpu-rasterization']:[])]}:{})})}};
    session=await iso.launch(launcher,engine);report.version=session.browser.version();
    context=await session.context({viewport:{width:325,height:530},deviceScaleFactor:dpr,locale:'en-US',timezoneId:zone,reducedMotion:cell.motion},{origin,fixture:prayer});
    if(cell.gpu==='software'&&engine==='chromium'){
      const cdp=await session.browser.newBrowserCDPSession(),gpu=(await cdp.send('SystemInfo.getInfo')).gpu;
      report.rasterization=gpu.featureStatus?.rasterization;
      assert.match(report.rasterization||'',/disabled|unavailable_software/,'software rasterizer is unconfirmed');
      await cdp.detach();
    }
    if(cell.gpu==='software'&&engine==='firefox'){
      const diagnostics=await context.newPage();
      try{
        await diagnostics.goto('about:support');
        await diagnostics.waitForFunction(()=>/WebRender \(Software\)/i.test(document.body.innerText),null,{timeout:15000});
        const snapshot=await diagnostics.locator('body').innerText();write('firefox-support.txt',snapshot);
        report.rasterization={source:'about:support',mode:'WebRender (Software)',sha256:hash(snapshot)};
      }finally{await diagnostics.close();}
    }
    if(cell.gpu==='software'&&engine==='webkit'){
      // Playwright does not expose CSS raster backend telemetry here. A WebGL
      // renderer name cannot qualify backdrop or buckle pixels. Retain the
      // independently collected same-host trace for the reviewer's decision.
      const proofPath=fs.realpathSync(a['raster-proof']),proof=JSON.parse(fs.readFileSync(proofPath));
      assert.equal(proof.engine,engine);assert.equal(proof.browserVersion,report.version);
      assert.equal(proof.platform,process.platform);assert.equal(proof.scope,'CSS rasterization');
      assert.equal(proof.mode,'software');assert.ok(proof.method&&proof.trace);
      const trace=fs.readFileSync(path.resolve(path.dirname(proofPath),proof.trace));
      assert.equal(hash(trace),proof.traceSha256);write('raster-trace.bin',trace);
      report.rasterization={...proof,status:'independent host evidence, reviewer verification pending'};
    }
    if(cell.group==='ineligible')await ineligible();
    else if(cell.group==='motion')await require('./r003f_motion.cjs').run({open,cell,names,out,report,PNG,waitTier,facts,readUiMask,dpr,zone,weather,documents});
    else if(['strap','buckle'].includes(cell.group))await repetitions();else await still();
    assert.ok(session.ledger.requests.some(r=>r.action==='fulfill'&&r.host==='api.aladhan.com'),'prayer fixture not consumed');
    const fixtureReads=[...Object.values(report.captures).map(c=>c.state.weatherFixtureReads),
      ...(report.streams||[]).flatMap(s=>s.frames.map(f=>f.before.weatherFixtureReads))];
    assert.ok(fixtureReads.some(n=>n>0),'no in-page weather fixture consumed');
    report.status=report.tierDisposition||report.motionDisposition?'PARTIAL':report.evidenceClass==='native'&&names.length===8?'ACQUIRED':'DIAGNOSTIC';
    if(report.status==='PARTIAL')process.exitCode=2;
  }catch(e){report.status=e.andon?'ANDON':'INCOMPLETE';report.reason=e.message;process.exitCode=e.andon?4:2;}
  finally{
    try{if(context)await context.context.close();if(session)await session.close();}
    finally{
      if(session){report.network=session.verdict();write('network.jsonl',session.ledger.requests.map(x=>JSON.stringify(x)).join('\n')+'\n');if(!report.network.ok){report.status='ISOLATION FAIL';process.exitCode=3;}}
      server.close();
      const files=fs.readdirSync(out,{recursive:true}).filter(f=>fs.statSync(path.join(out,f)).isFile());
      report.artifacts=Object.fromEntries(files.map(f=>{const b=fs.readFileSync(path.join(out,f));return [f.split(path.sep).join('/'),{sha256:hash(b),bytes:b.length}];}));
      write('summary.json',JSON.stringify(report,null,2)+'\n');
      console.log(JSON.stringify({cell:cell.id,status:report.status,reason:report.reason}));
      if(!session)process.exit(process.exitCode||2);
    }
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
