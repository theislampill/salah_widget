const test=require('node:test'), assert=require('node:assert/strict');
const load=async()=>({
  ...await import('../tools/r0035/stellar_replay.mjs'),...await import('../tools/r0035/prepared_replay.mjs'),
  ...await import('../tools/r0035/changed_rectangles.mjs'),...await import('../real-sky/core/src/renderer.mjs'),
  ...await import('../real-sky/native-composition.mjs'),...await import('../real-sky/native-cloud-transfer.mjs')
});
test('dirty presenter covers sparse corners, alpha, disappearance, reuse and recovery after partial writes',async()=>{
  const {PresentationWriter}=await load(),width=35,height=19;
  const pixels=new Uint8ClampedArray(width*height*4),image={width,height,data:pixels.slice()};
  let calls=0,fail=Infinity;
  const context={putImageData(im,dx,dy,x=0,y=0,w=width,h=height){
    if(++calls===fail)throw new Error('deliberate upload failure');
    for(let row=y;row<y+h;row++){const start=4*(row*width+x);pixels.set(im.data.subarray(start,start+4*w),start);}
  }};
  const writer=new PresentationWriter(context,'changed',8);
  assert.equal(writer.publish(image).pixels,width*height);
  assert.equal(writer.publish(image).writes,0);
  image.data[3]=7;image.data[4*(width*height-1)+2]=1;
  const changes=writer.publish(image);assert.deepEqual(changes,{writes:2,pixels:2});assert.deepEqual(pixels,image.data);
  image.data.fill(0);fail=calls+2;
  assert.throws(()=>writer.publish(image),/deliberate/);assert.notDeepEqual(pixels,image.data);
  assert.equal(writer.publish(image).pixels,width*height);assert.deepEqual(pixels,image.data);
});
test('periodic-worker and synchronization controls differ from the independently seeded presentation series',async()=>{
  const {starModes,starOffset}=await load(),utc=1794182400000;
  const star={id:'hyg:17',modes:starModes('hyg:17'),detectable:true,altDeg:3};
  const other={...star,modes:starModes('hyg:117')};
  const sample=(s,t,m={})=>starOffset(s,t,2,m);
  for(const gate of [{paused:true},{hidden:true},{reduced:true}])assert.equal(sample(star,utc,gate),0);
  assert.equal(sample({...star,altDeg:0},utc),0);assert.equal(sample({...star,detectable:false},utc),0);
  assert.notEqual(sample(star,utc,{reduced:true,full:true}),0);
  const values=Array.from({length:3600},(_,i)=>sample(star,utc+1000*i/60));
  assert.ok(Math.abs(values.reduce((s,x)=>s+x,0)/values.length)<.0005);
  assert.ok(Math.max(...values.map(Math.abs))<.08);
  assert.ok(values.every((v,i)=>v===sample({...star,modes:starModes(star.id)},utc+1000*i/60)));
  assert.ok(values.some((v,i)=>Math.abs(v-sample(other,utc+1000*i/60))>.01));
  const consecutive=a=>a.slice(1).filter((x,i)=>x!==a[i]).length;
  assert.equal(consecutive(values),3599);
  assert.equal(consecutive(values.map((x,i)=>values[Math.floor(i/240)*240])),14);
});
test('overlapping complete PSFs, opaque edge, cloud transfer and clipped-edge writer agree with independent full-star rerenders',async()=>{
 const {preparePatch,prepareReplay,stellarOverlay,replayFrame,renderStars,encodeFrame,nativeForeground,
   nativeCalendarRegion,starOffset,nativeCloudDisplayFrame}=await load();
 const width=16,height=11,n=width*height,E=11;
 const sources=[{id:'hyg:6',x:.4,y:.8,altDeg:9,vmag:1},{id:'hyg:7',x:7.3,y:5.4,altDeg:31,vmag:3},
   {id:'hyg:8',x:7.7,y:5.2,altDeg:43,vmag:5},{id:'hyg:19',x:14.9,y:10.1,altDeg:6,vmag:2}].map(s=>({...s,detectable:true}));
 const fluxes=[[.52,.31,.06],[.28,.25,.31],[.05,.04,.02],[.13,.26,.4]], map=new Map(sources.map((s,i)=>[s.id,fluxes[i]]));
 const patches=sources.map(s=>preparePatch(s,{rgb:map.get(s.id)},width,height));
 const gas=Float64Array.from({length:3*n},(_,i)=>.0005+.00001*(i%11)), diffuse=new Float64Array(3*n).fill(.0002);
 const stars=renderStars(sources,{width,height,fluxAt:s=>({rgb:map.get(s.id)})}).linear;
 const raster={width,height,effectiveExposure:E,linear:gas.map((v,i)=>v+stars[i]+diffuse[i]),stellarLinear:stars,skyBackgroundLinear:gas,diffusePhysicalLinear:diffuse};
 const cloud=new Uint8ClampedArray(4*n),moon=cloud.slice(),mask=new Float64Array(n);
 for(let p=0;p<n;p++){mask[p]=p%width<6?0:p%width===6?.4:1;
   cloud.set([94,130,163,[0,127,255][Math.floor(p/width)%3]],4*p);moon.set([25,54,90,mask[p]===0?235:0],4*p);}
 const fg={mask,cloudRGBA:cloud,moonRGBA:moon,glass:[{x:4,y:2,width:4,height:4}]};
 const t0=1794182400000;
 for(const preview of [false,true])for(const scope of ['all','preview-members'])for(const glassFactor of [0,.5,1]){
   const config={scope,multiplier:2,glassFactor,margin:0},r={...raster,starPreview:preview};
   const prepared=prepareReplay(r,patches,config,fg);let any=false;
   for(let i=0;i<12;i++){
     const t=t0+i*1000/60,got=prepared.present(t).rgba;
     const scaled=renderStars(sources,{width,height,fluxAt:s=>{
       const k=sources.indexOf(s),selected=scope==='all'||s.vmag<=4.5;
       const glass=s.x>=4&&s.x<8&&s.y>=2&&s.y<6?glassFactor:1;
       const factor=1+(selected?starOffset(patches[k],t,2,{})*glass:0);
       return {rgb:map.get(s.id).map(v=>v*factor)};
     }}).linear;
     const base=nativeCalendarRegion({...r,stellarLinear:scaled},mask);
     const expected=preview?nativeCloudDisplayFrame(encodeFrame(base,E),cloud,moon):
       encodeFrame(nativeForeground(base,{cloudRGBA:cloud,moonRGBA:moon,atmosphereLinear:gas,exposure:E}).linear,E);
     assert.deepEqual(got,expected);
     const overlay=stellarOverlay(prepared,got);
     const composited=prepared.nominal.slice();
     for(let p=0;p<n;p++)if(overlay[4*p+3]){
       assert.equal(overlay[4*p+3],255);composited.set(overlay.subarray(4*p,4*p+4),4*p);
     }
     assert.deepEqual(composited,got);assert.deepEqual(got,replayFrame(r,patches,t,config,fg).rgba);
     for(let p=0;p<n;p++){const d=got[4*p]!==prepared.nominal[4*p];any||=d;if(mask[p]===0||cloud[4*p+3]===255)assert.equal(d,false);}
   }
   assert.ok(any);assert.deepEqual(prepared.present(t0,{paused:true}).rgba,prepared.nominal);
 }
});
test('whole native-frame tails suspend/retry with bounded gain, disabled control keeps running',async()=>{
 const {FrameGuard}=await import('../tools/r0035/frame_guard.mjs');
 const guard=new FrameGuard(true),control=new FrameGuard(false);
 let t=0,previous=0;
 for(let i=0;i<160;i++){
   guard.observe(t);control.observe(t);
   const value=guard.nextGain(t);assert.ok(Math.abs(value-previous)<=.10000001);previous=value;
   assert.equal(control.nextGain(t),1);
   t+=i%4?16:85;
 }
 assert.equal(guard.gain,0);assert.ok(guard.retryAt>t);
 for(;t<guard.retryAt;t+=16){guard.observe(t);assert.equal(guard.nextGain(t),0);}
 guard.observe(t);assert.equal(guard.nextGain(t),.1);
});
test('live bridge rejects stale jobs, coalesces replacements, measures the actual written source, withdraws on failure',async()=>{
 const {installLab}=await import('../tools/r0035/live_lab.mjs'),{nativeJob}=await import('../real-sky/native-contract.mjs');
 const {replayObserver}=await import('../tools/r0035/qualification_scene.mjs');
 const saved=new Map(['window','document','Worker','ImageData'].map(k=>[k,global[k]]));
 let latestWorker,overlay,lastImage,failWrite=false,now=1794182400000;
 class Worker {constructor(){latestWorker=this;this.sent=[];}postMessage(msg){this.sent.push(msg);}terminate(){this.dead=true;}}
 let authority=null;const snap=()=>({...replayObserver,utcMs:now,timeScale:1,paused:false});
 const context={putImageData(image){if(failWrite)throw Error('deliberate paint fault');lastImage=image.data.slice();}};
 try{
  global.Worker=Worker;global.ImageData=class {constructor(data,width,height){Object.assign(this,{data,width,height});}};
  global.document={addEventListener(){},createElement(){overlay={style:{},setAttribute(){},getContext(){return context;},remove(){}};return overlay;}};
  global.window={addEventListener(){},matchMedia(){return {addEventListener(){}};},SalahNativeSkyHost:{capture:snap,cloudsCurrent:a=>authority===null||a===authority}};
  const lab=installLab({arm:'changed',scope:'all',multiplier:1,glassFactor:1,margin:0,guard:false});
  const rgba=new Uint8ClampedArray(325*530*4);
  const canvas={getContext(){return {getImageData(){return {data:rgba};}};},after(){},getBoundingClientRect(){return {width:325,height:530};},
   parentElement:{querySelectorAll(){return [];},classList:{contains(s){return s==='real-sky-composed';}}}};
  let lastJob,lastFrame;
  const publish=()=>{lastJob=nativeJob(snap(),true);lastFrame={status:'ready',raster:{width:325,height:530},sources:[]};
    lab.publish('refined',canvas,lastJob,lastFrame,{cloudAuthority:{}},null);};
  const reply=data=>latestWorker.onmessage({data});
  publish();publish();publish();assert.equal(latestWorker.sent.length,1,'one in flight, one latest');
  const first=latestWorker.sent[0].epoch;reply({op:'ready',epoch:first,sources:5,variablePixels:2});
  assert.equal(latestWorker.sent.length,2);const epoch=latestWorker.sent[1].epoch;assert.equal(epoch,first+2);
  reply({op:'ready',epoch,sources:1,variablePixels:1,contributingCenters:1});lab.present();
  assert.equal(latestWorker.sent.at(-1).op,'sample');
  const sample={id:'hyg:6',factor:1.01,centerDelta:[1,0,0]};
  rgba[3]=255;reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});
  assert.equal(overlay.style.visibility,'visible');assert.deepEqual(lab.observe().sample,sample);
  const copy=lab.observe();copy.sample.factor=99;assert.equal(lab.observe().sample.factor,1.01);
  const snapshot=JSON.stringify(lab.observe()),n=latestWorker.sent.length;for(let i=0;i<25;i++)lab.observe();
  assert.equal(snapshot,JSON.stringify(lab.observe()));assert.equal(latestWorker.sent.length,n);
  const accepted=latestWorker.sent.find(m=>m.epoch===epoch).job;
  const wrong={};authority=wrong;lab.renew(canvas,accepted,{raster:{}},{cloudAuthority:wrong});lab.present();
  assert.equal(overlay.style.visibility,'hidden','foreign signal cannot renew a frame');
  lab.renew(canvas,lastJob,lastFrame,{cloudAuthority:wrong});lab.beginTrial();lab.present();reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});
  assert.equal(overlay.style.visibility,'visible','matching equal-byte renewal immediately admits a new sample');
  lab.present();reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});
  lab.present();reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(254)});
  const receipts=lab.endTrial().events.filter(e=>e.kind==='publication');assert.deepEqual(receipts.map(e=>e.changed),[false,false,true]);
  authority=null;const beforeWithdrawal=latestWorker.sent.length;
  lab.present();
  lab.publish('preview',canvas,nativeJob(snap()),{raster:{}},{},null);
  reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});lab.present();
  assert.equal(overlay.style.visibility,'hidden','background-only owner revokes pending and completed samples');
  assert.equal(lab.observe().sourceCount,0);assert.equal(lab.observe().variablePixels,0);
  assert.equal(latestWorker.sent.length,beforeWithdrawal+1);
  publish();const live=latestWorker.sent.at(-1).epoch;
  const {preparePatch,prepareReplay,stellarOverlay,renderStars}=await load();
  const width=13,height=13,star={id:'hyg:6',x:6.2,y:6.3,vmag:1,altDeg:18,detectable:true};
  const flux={rgb:[.8,.65,.4]},patch=preparePatch(star,flux,width,height);
  const stellar=renderStars([star],{width,height,fluxAt:()=>flux}).linear,gas=new Float64Array(stellar.length).fill(.001);
  const raster={width,height,effectiveExposure:12,stellarLinear:stellar,skyBackgroundLinear:gas,diffusePhysicalLinear:new Float64Array(stellar.length)};
  const mask=new Float64Array(width*height).fill(1);mask[6*width+6]=0;
  const candidate=prepareReplay(raster,[patch],{scope:'all',glassFactor:1,margin:0,multiplier:2},{glass:[],mask});
  const result=candidate.present(now),small=stellarOverlay(candidate,result.rgba),wings=new Uint8ClampedArray(rgba.length);
  for(let y=0;y<height;y++)wings.set(small.subarray(4*y*width,4*(y+1)*width),4*y*325);
  const signal=Uint32Array.from(candidate.indices,p=>new Uint32Array(small.buffer)[p]);
  assert.equal(result.sample,null);assert.equal(candidate.contributingCenters,0);assert.equal(wings[4*(6*325+6)+3],0);
  assert.equal(signal.filter(v=>v).length,17,'masked center with exposed quantized PSF wings');
  reply({op:'ready',epoch:live,sources:1,variablePixels:signal.length,contributingCenters:0});
  lab.beginTrial();lab.present();reply({op:'sample',epoch:live,utcMs:now,rgba:wings,sample:null,signal});
  assert.equal(overlay.style.visibility,'visible','exposed wings paint without a center diagnostic');
  assert.deepEqual(lastImage,wings);assert.equal(lab.observe().sample,null);assert.match(lab.debugLine(),/10s — 60s —/);
  const blank=new Uint8ClampedArray(rgba.length),silent=new Uint32Array(signal.length);
  for(let i=0;i<2;i++){
    now+=16;lab.present();reply({op:'sample',epoch:live,utcMs:now,rgba:blank,sample:null,signal:silent});
    assert.equal(lab.observe().status,'active');assert.deepEqual(lastImage,blank);
  }
  const measured=lab.endTrial().events.filter(e=>e.kind==='publication');
  assert.deepEqual(measured.map(e=>[e.nonempty,e.changed,e.id]),[[true,false,null],[false,true,null],[false,false,null]]);
  assert.ok(measured[1].writes>0);assert.equal(measured[2].writes,0);
  now+=16;lab.present();reply({op:'sample',epoch:live,utcMs:now-16,rgba:wings,sample:null,signal});
  assert.equal(overlay.style.visibility,'hidden');assert.equal(lab.observe().status,'sample timestamp mismatch');
  now+=16;lab.present();reply({op:'sample',epoch:live,utcMs:now,rgba:wings,sample:null,signal});
  now+=31000;lab.present();assert.equal(overlay.style.visibility,'hidden');
  lab.clear(canvas);reply({op:'sample',epoch,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});assert.equal(overlay.style.visibility,'hidden');
  publish();const next=latestWorker.sent.at(-1).epoch;
  reply({op:'ready',epoch:next,sources:1,variablePixels:1});lab.present();failWrite=true;
  reply({op:'sample',epoch:next,utcMs:now,rgba,sample,signal:Uint32Array.of(255)});assert.equal(overlay.style.visibility,'hidden');
  assert.match(lab.observe().status,/deliberate paint fault/);assert.ok(latestWorker.dead);
 }finally{for(const [k,v] of saved){if(v===undefined)delete global[k];else global[k]=v;}}
});

test('per-source packet staggering prevents a synchronized envelope in collective signal power',async()=>{
 const {populationEnvelope}=await import('../tools/r0035/signal_checks.mjs');
 const ids=Array.from({length:640},(_,i)=>'hyg:'+String(i+1)),time=1794182400000;
 assert.ok(populationEnvelope(ids,time).maximumToMinimumRms<1.05);
 assert.ok(populationEnvelope(ids,time,true).maximumToMinimumRms>1.3);
});
test('published real preview and refined frames pass the worker byte fence and preserve cross-tier source identity', async()=>{
 const {readFileSync}=require('node:fs'),path=require('node:path');
 const {prepareLiveFrame}=await import('../tools/r0035/lab_worker.mjs');
 const {nativeJob}=await import('../real-sky/native-contract.mjs'),{NativeSkyEngine}=await import('../real-sky/native-engine.mjs');
 const {NativeStarPreview,joinNativeStarPreview}=await import('../real-sky/native-star-preview.mjs');
 const {renderNativeBackgroundPreview}=await import('../real-sky/native-preview.mjs');
 const {nativeCalendarRegion}=await import('../real-sky/native-composition.mjs');
 const {encodeNativeDisplay}=await import('../real-sky/native-host.mjs');
 const {replayObserver}=await import('../tools/r0035/qualification_scene.mjs');
 const read=n=>readFileSync(path.join(__dirname,'../vendor/real-sky/data',n),'utf8');
 const pack={catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
   assetTexts:{128:read('registered-starlight/V-nside128.json')}};
 const snap={...replayObserver,utcMs:Date.parse('2026-11-09T00:00:00Z')},job=nativeJob(snap,true);
 const config={scope:'preview-members',multiplier:1,margin:4,glassFactor:0},foreground={glass:[{x:20,y:50,width:10,height:20}]};
 const background=renderNativeBackgroundPreview(snap),E=background.raster.effectiveExposure,bg=encodeNativeDisplay(background.raster.linear,E);
 const renderer=new NativeStarPreview(pack),layer=renderer.render(background.job,background.raster.physicalState,{background:bg,exposure:E});
 const joined=joinNativeStarPreview(background,bg,layer);
 const oldFetch=global.fetch,engine=new NativeSkyEngine(pack);
 global.fetch=async url=>{assert.ok(url.pathname.endsWith('/vendor/real-sky/data/bright-stars.json'));return new Response(pack.catalogueText);};
 try{
 const input={frame:{...joined,sources:layer.sources},job:background.job,nominal:joined.rgba,config,foreground};
 for(const bad of [[],[...layer.sources.slice(1),layer.sources[1]],layer.sources.map((s,i)=>i===0?{...s,x:layer.sources[1].x}:s)]){
   await assert.rejects(prepareLiveFrame({...input,frame:{...input.frame,sources:bad}}),/membership/);
 }
 const preview=await prepareLiveFrame({job:background.job,frame:{...joined,sources:layer.sources},nominal:joined.rgba,config,foreground});
 assert.equal(preview.census.detectable,169);assert.equal(preview.census.omittedByMagnitude.length,0);
 const frame=await engine.render(job),r=frame.raster,rows=183;
   const nominal=encodeNativeDisplay(r.linear,r.effectiveExposure);
   nominal.set(encodeNativeDisplay(nativeCalendarRegion(r,null,rows),r.effectiveExposure));
   const refined=await prepareLiveFrame({frame,job,nominal,config,foreground});
   assert.equal(refined.census.detectable,1404);assert.equal(refined.census.omittedByMagnitude.length,1235);
   const ids=a=>a.map(s=>s.id).sort(),sorted=a=>[...a].sort();
   const bright=frame.sources.filter(s=>s.vmag<=4.5),detected=r.sourceDiagnostics.filter(d=>d.detectable&&d.backgroundComplete!==false);
   assert.deepEqual(sorted(preview.census.projectedIds),ids(layer.sources));
   assert.deepEqual(sorted(refined.census.projectedIds),ids(frame.sources));
   assert.deepEqual(sorted(preview.census.projectedIds),ids(bright));
   assert.deepEqual(sorted(refined.census.detectableIds),ids(detected));
   assert.deepEqual(sorted(preview.census.detectableIds),ids(detected.filter(d=>d.vmag<=4.5)));
   assert.deepEqual(sorted(preview.census.scopedIds),sorted(refined.census.scopedIds));
   assert.deepEqual(sorted(refined.census.omittedByMagnitude),ids(detected.filter(d=>d.vmag>4.5)));
   for(const bad of [frame.sources.slice(1),[...frame.sources.slice(1),frame.sources[1]],
      frame.sources.map((s,i)=>i===0?{...s,altDeg:s.altDeg+1}:s)]){
     await assert.rejects(prepareLiveFrame({frame:{...frame,sources:bad},job,nominal,config,foreground}),/membership/);
   }
   await assert.rejects(prepareLiveFrame({frame:{...frame,raster:{...r,sourceDiagnostics:r.sourceDiagnostics.slice(1)}},job,nominal,config,foreground}),/diagnostics membership/);

   // Independently withdraw one real emitter from the native preview renderer.
   // Its delta across each channel and entire PSF support must equal the patch.
   const {livePreviewStars}=await import('../tools/r0035/lab_worker.mjs');
   const patches=livePreviewStars(joined.raster,layer.sources),star=patches.reduce((a,b)=>a.vmag<b.vmag?a:b);
   const without=Object.create(renderer);without.catalogue={...renderer.catalogue,stars:renderer.catalogue.stars.filter(s=>s.id!==star.id)};
   const withdrawn=without.render(background.job,background.raster.physicalState,{background:bg,exposure:E});
   const energy=[0,0,0];let outside=0;
   for(let y=0;y<530;y++)for(let x=0;x<325;x++)for(let k=0;k<3;k++){
     const i=3*(325*y+x)+k,delta=layer.linear[i]-withdrawn.linear[i];
     if(x<star.x0||y<star.y0||x>=star.x0+star.w||y>=star.y0+star.h){outside=Math.max(outside,Math.abs(delta));continue;}
     const want=star.linear[3*((y-star.y0)*star.w+x-star.x0)+k];
     assert.ok(Math.abs(want-delta)<1e-12);energy[k]+=delta;
   }
   assert.equal(outside,0);assert.ok(energy.every(v=>v>0));assert.equal(new Set(energy).size,3);
   assert.deepEqual(preview.census.addedMargin,refined.census.addedMargin);
   assert.deepEqual(preview.census.centerUnderGlass,refined.census.centerUnderGlass);
   const altered=joined.rgba.slice();altered[0]^=1;
   await assert.rejects(prepareLiveFrame({job:background.job,frame:{...joined,sources:layer.sources},nominal:altered,config,foreground}),/bytes mismatch/);
 }finally{global.fetch=oldFetch;engine.dispose();}
});
test('elapsed debug line requires continuous compatible accepted and monotonic clocks',async()=>{
  const {SampleHistory}=await import('../tools/r0035/sample_history.mjs');
  const h=new SampleHistory(),empty='factor Δ 10s — 60s —';
  const add=(t,u=t,id='a')=>h.add(t,u,{id,factor:1+t/100000},'scene');
  add(0);assert.equal(h.line(0),empty);
  for(let t=100;t<=10000;t+=100)add(t);
  assert.equal(h.line(10000),'factor Δ 10s 0.1000 60s —');
  for(let t=10100;t<=60000;t+=100)add(t);
  assert.equal(h.line(60000),'factor Δ 10s 0.1000 60s 0.6000');
  assert.equal(h.line(60500),empty);add(60500);assert.equal(h.line(60500),empty);
  for(let t=60600;t<=70600;t+=100)add(t);
  add(70700,1000);assert.equal(h.line(70700),empty);
  add(70800,1100,'b');assert.equal(h.line(70800),empty);
  h.reset();assert.equal(h.line(70800),empty);
});
test('ordinary-clock offset preserves Date construction, elapsed timers and simulation distinction',()=>{
  const {runInNewContext}=require('node:vm'),{readFileSync}=require('node:fs'),path=require('node:path');
  const script=readFileSync(path.join(__dirname,'../tools/r0035/trial_clock.js'),'utf8');
  runInNewContext(script+`
    const OldDate=Date,perf=performance,raf=requestAnimationFrame,expected=123456789;
    installTrialWallClock(expected);
    assert.ok(Math.abs(Date.now()-expected)<100);assert.ok(Math.abs(+new Date()-expected)<100);
    assert.equal(Date(0),new OldDate(expected).toString());assert.equal(+new Date(0),0);
    assert.equal(+new Date(2001,2,4),+new OldDate(2001,2,4));assert.equal(Date.UTC,OldDate.UTC);
    class D extends Date {};assert.ok(new D() instanceof D&&new Date() instanceof Date);
    assert.equal(perf,performance);assert.equal(raf,requestAnimationFrame);
  `,{window:{},performance,requestAnimationFrame(){},assert});
});
test('native interval verdict separates delivery from pixel changes and rejects replay, stalls and wrong scenes',()=>{
  const {execFileSync}=require('node:child_process');
  execFileSync('python',['tools/r0035/trial_admission_controls.py'],{cwd:require('node:path').join(__dirname,'..')});
});
test('disposable refined host renews equal-byte authority after both currentness checks',()=>{
  const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process');
  const root=path.join(__dirname,'..'),tmp=fs.mkdtempSync(path.join(os.tmpdir(),'r35-host-'));
  try{
    const rc='real-sky/native-host.mjs';fs.mkdirSync(path.join(tmp,'real-sky'));fs.copyFileSync(path.join(root,rc),path.join(tmp,rc));
    cp.execFileSync('python',['-c',"from pathlib import Path; import sys; sys.path.insert(0,'tools/r0035'); from materialize_lab import patch_refined; patch_refined(Path(sys.argv[1]),sys.argv[2])",tmp,rc],{cwd:root});
    const real=fs.readFileSync(path.join(tmp,rc),'utf8');
    const start=real.indexOf('if(sameNativePresentation(previousPresentation,presentation)){'),end=real.indexOf('const sampledMask=',start);
    assert.ok(start>=0&&end>start);
    const block=real.slice(start,end);
    for(const [cloud,jobCurrent,want] of [[false,true,['reschedule']],[true,false,['clear']],[true,true,['renew']]]){
      const calls=[],canvas={style:{}},job={},frame={},capture={cloudAuthority:{revision:2},native:{}};
      const env={window:{SalahNativeSkyHost:{cloudsCurrent:a=>a===capture.cloudAuthority&&cloud},
        R0035Lab:{renew:(...args)=>{assert.deepEqual(args,[canvas,job,frame,capture]);calls.push('renew');}}},
        sameNativePresentation:()=>true,previousPresentation:{},presentation:{},lifecycle:{current:()=>jobCurrent},snapshot:()=>({}),
        clear:()=>calls.push('clear'),compose:()=>calls.push('reschedule'),job,frame,canvas,capture,
        status:{presentationSkips:0,last:{composition:{}}},performance,lastCompose:0,started:0,card:{classList:{add(){}}}};
      vm.runInNewContext('(function(){'+block+'})()',env);assert.deepEqual(calls,want);
    }
  }finally{fs.rmSync(tmp,{recursive:true,force:true});}
});
