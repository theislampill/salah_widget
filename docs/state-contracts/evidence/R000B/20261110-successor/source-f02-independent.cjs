'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {execFileSync}=require('node:child_process'),{pathToFileURL}=require('node:url');
const root='/workspace/scratch/15b8fb6ac4c2/r000b-work';
const out='/workspace/scratch/d9a9ea2be931/recovery';
const {fixture,copy,sha}=require(path.join(root,'tests/weather-no-timetable-fixture.cjs'));
const source=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const oldSource=execFileSync('git',['-C',root,'show','d124f050ec68fa8608022b1ed5fead426d42dcb9:src/native/index.html'],{encoding:'utf8'});
assert.equal(sha(Buffer.from(source)),'fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327');
const hooks=fs.readFileSync(path.join(root,'real-sky/native-host-hooks.js'),'utf8');
const refinedSource=fs.readFileSync(path.join(root,'real-sky/native-host.mjs'),'utf8');
const previewSource=fs.readFileSync(path.join(root,'real-sky/native-preview-host.mjs'),'utf8');
const nativeURL=name=>pathToFileURL(path.join(root,'real-sky',name));
const records=[];
const make=options=>fixture({source,...options});
function present(h,{state='wet',type=state==='wet'?'rain':null,lease=1000,spatial=false}={}){
 const t=copy(h.run('currentWeatherTarget()')),now=h.clock.wall;
 h.ctx.__freshPresent={scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',
  target:{generation:t.generation,lat:t.lat,lon:t.lon},measurementAt:now,validFrom:now,validUntil:now+lease,retrievedAt:now,frameAt:now,issuedAt:now,
  units:'categorical',footprint:{kind:'point',lat:t.lat,lon:t.lon,coverage:'target'},
  quality:{status:'qualified',sampling:'direct',localObservationAt:now,operationalHealth:'operational'},
  present:{state,type,lightning:'unavailable',quantity:null},
  ...(spatial?{spatial:{state:'nearby-precipitation',observedAt:now-299500,distanceKm:[4,8]}}:{})};
 assert(h.run('(weatherSynthetic=admitWeatherFixture(__freshPresent,currentWeatherTarget(),Date.now())).ok'));
 return h.run('weatherDecision().present.evidence');
}
function state(h){return {...copy(h.run(`({model:!!model(),selected:!!selectedWeather(),code:weatherDecision().renderCode,
 present:weatherDecision().present.available,consumedCode:_cloudPublication.decision?.renderCode,
 cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],targets:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],
 ready:_cloudReady,density:_colDens?Math.max(..._colDens):0,population:_cloudMotion.population,phase:_cloudMotion.phase,
 life:_cloudMotion.life,wander:_cloudMotion.wander,receipt:cloudPublicationReceipt(),effects:_lastWeatherEffects?.receipt,
 header:_lastWeatherHeader?.code,fx:document.querySelector('.c').dataset.fx})`)),raster:{...h.raster}};}
function clear(h){const s=state(h);assert.deepEqual(s.cov,[0,0,0]);assert.deepEqual(s.targets,[0,0,0]);assert.equal(s.ready,false);assert.equal(s.density,0);assert.equal(s.raster.currentFills,0);return s;}
function axes(a,b){for(const k of ['population','phase','life','wander'])assert.deepEqual(a[k],b[k],k+' preserved at a held monotonic instant');}
function passive(h,receipt,expected){h.ctx.__checkedReceipt=receipt;const before=state(h),requests=h.calls.length;
 assert.equal(h.run('cloudPublicationCurrent(__checkedReceipt)'),expected);
 assert.deepEqual(state(h),before,'final guard is a passive read');assert.equal(h.calls.length,requests);}
async function nativeBoundary(h,run){
 const comp=await import(nativeURL('native-composition.mjs')),hostModule=await import(nativeURL('native-host.mjs'));
 const contract=await import(nativeURL('native-contract.mjs')),encoding=await import(nativeURL('native-encoding.mjs')),transfer=await import(nativeURL('native-cloud-transfer.mjs'));
 h.run(hooks);const host=h.ctx.window.SalahNativeSkyHost,card=h.select('.c'),draws=[],images=[],errors=[];
 card.prepend=()=>{};
 const canvasFactory=()=>{let alpha=0;const canvas={width:325,height:530,style:{},setAttribute(){},remove(){},getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
  const context={resetTransform(){},clearRect(){alpha=0;},setTransform(){},fillRect(){},createLinearGradient:()=>({addColorStop(){}}),
   drawImage(input){if(input===h.select('.cloudcanvas'))alpha=h.raster.currentFills?192:0;},
   getImageData(x,y,width,height){const data=new Uint8ClampedArray(width*height*4);data.set([80,90,100,alpha]);return {data};},
   putImageData(image){draws.push({canvas,bytes:image.data.slice()});}};
  canvas.getContext=()=>context;canvas.toDataURL=()=> 'data:image/png;base64,alpha-'+alpha;return canvas;};
 const document={createElement:canvasFactory,querySelector:q=>q==='.c'?card:q==='.cloudcanvas'?h.select(q):null};
 const window={SalahNativeSkyHost:host,SalahMoonDetail:{clear(){},compose(){}}};
 const ImageData=class{constructor(data,width,height){assert.equal(data.length,width*height*4);Object.assign(this,{data,width,height});}};
 const saved={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle,ImageData:globalThis.ImageData};
 Object.assign(globalThis,{document,window,ImageData,getComputedStyle:()=>({filter:'none',visibility:'hidden',opacity:'1'})});
 class Publication extends comp.NativeSolarMaskPublication{constructor(){super(()=>{const image={decode:()=>new Promise((resolve,reject)=>Object.assign(image,{resolve,reject}))};images.push(image);return image;});}}
 const canvas=canvasFactory(),foreground=new comp.NativeForegroundCapture(canvas),flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 const b={h,host,card,window,document,ImageData,Publication,canvas,foreground,draws,images,errors,flush,comp,hostModule,contract,encoding,transfer};
 try{return await run(b);}finally{for(const[k,v]of Object.entries(saved))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
}
function nativeOwner(b,kind){
 if(kind==='refined'){
  const linear=new Float64Array(325*530*3).fill(.02),frame={raster:{width:325,height:530,linear,skyBackgroundLinear:linear,stellarLinear:new Float64Array(linear.length),effectiveExposure:24}};
  const s={frame,job:b.contract.nativeJob(b.host.capture(false),true),pendingJob:null,paintedFrame:null,paintedJob:null,previousPresentation:null,previousSolarMask:null,previousMoonBottom:0,lastCompose:0,disposed:false,
   foreground:b.foreground,solarPublication:new b.Publication(),snapshot:()=>b.host.capture(false),lifecycle:{current:(job,state=b.host.capture(false))=>b.contract.nativeResultCurrent(job,state)},
   publish(){},performance:{now:()=>b.h.clock.now},window:b.window,...b.comp,...b.hostModule,
   calendarGeometry:()=>({key:null,mask:()=>null}),ImageData:b.ImageData,Uint8ClampedArray,ctx:b.canvas.getContext('2d'),card:b.card,canvas:b.canvas,
   status:{last:{},errors:b.errors,presentationDraws:0,presentationSkips:0,presentationRejections:0}};
  const clear=refinedSource.slice(refinedSource.indexOf(' function clear('),refinedSource.indexOf(' // Identity/age fences'));
  const compose=refinedSource.slice(refinedSource.indexOf(' function compositionFailed('),refinedSource.indexOf('\n function accept('));
  const failure=refinedSource.slice(refinedSource.indexOf(' function failure('),refinedSource.indexOf('\n client=new ReferenceRenderClient'));
  assert(clear&&compose&&failure);vm.createContext(s);vm.runInContext(clear+'\n'+compose+'\n'+failure,s);s.compose();
  return {update:()=>s.compose(),read:()=>s.status.last?.composition,drawCount:()=>s.status.presentationDraws,skipCount:()=>s.status.presentationSkips,context:s};
 }
 const s={window:b.window,document:b.document,Uint8ClampedArray,Float64Array,structuredClone,ImageData:b.ImageData,performance:{now:()=>b.h.clock.now},requestAnimationFrame:()=>1,cancelAnimationFrame(){},
  ...b.comp,NativeSolarMaskPublication:b.Publication,...b.encoding,...b.contract,...b.transfer,
  renderNativeBackgroundPreview(snapshot){const job=b.contract.nativeJob(snapshot,true),linear=new Float64Array(325*530*3).fill(.02);return {job,utcMs:snapshot.utcMs,quality:'controlled independent numerical sky',raster:{width:325,height:530,linear,effectiveExposure:24,physicalState:{sun:{altDeg:-20}}}};}};
 const product=previewSource.replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');
 vm.createContext(s);vm.runInContext(product+'\nstartNativeSkyPreview();',s);
 return {update:()=>s.window.SalahSkyPreview.update(),read:()=>s.window.SalahSkyPreview.state.composition,drawCount:()=>s.window.SalahSkyPreview.state.draws,context:s};
}
async function originalExpiry(candidate=source){
 const h=await fixture({source:candidate,hash:'&simWx=0&simCloud=0'});const record=h.run('weather');present(h);
 h.run('render();paintClouds(simNow()/1000)');const receipt=h.run('cloudPublicationReceipt()'),before=state(h);assert.deepEqual(before.cov,[.9,.85,.3]);
 h.at(891000);assert.equal(h.run('weather'),record);assert.equal(h.run('weatherDecision().present.available'),false);h.ctx.__originalReceipt=receipt;
 assert.equal(h.run('cloudPublicationCurrent(__originalReceipt)'),false,'independent original expiry oracle: consumed evidence revoked');
 h.run('today=null;render();paintClouds(simNow()/1000)');const after=clear(h);assert.equal(after.code,0);assert.equal(after.population,before.population);
 return {before,after};
}
async function originalReplacement(candidate=source){
 const h=await fixture({source:candidate,hash:'&simWx=0&simCloud=0'});present(h);h.run('render();paintClouds(simNow()/1000)');
 const record=h.run('weather'),receipt=h.run('cloudPublicationReceipt()'),before=state(h),evidence=present(h,{state:'dry',lease:60000});
 h.run('render();paintClouds(simNow()/1000)');assert.equal(h.run('weather'),record);
 assert.notEqual(h.run('cloudPublicationReceipt()'),receipt,'independent original replacement oracle: new consumed evidence identity');
 assert.equal(h.run('_cloudPublication.decision.present.evidence'),evidence);assert.equal(h.run('_cloudPublication.decision.renderCode'),0);passive(h,receipt,false);
 const after=state(h);axes(after,before);after.cov.forEach((v,i)=>assert(Math.abs(v-before.cov[i]*.92)<1e-12));return {before,after};
}
async function run(name,fn){try{const evidence=await fn();records.push({name,status:'pass',evidence});console.log('PASS '+name);}catch(error){records.push({name,status:'fail',error:{name:error.name,message:error.message,stack:error.stack}});console.error('FAIL '+name+' '+error.message);throw error;}}
async function main(){
 await run('original same-record expiry scenario, corrected expectations',()=>originalExpiry());
 await run('original same-record dry replacement scenario, corrected expectations',()=>originalReplacement());
 for(const [name,fn,marker]of [['expiry',originalExpiry,'independent original expiry oracle:'],['replacement',originalReplacement,'independent original replacement oracle:']])
  await run('old frozen source discriminates original '+name,async()=>{let caught;try{await fn(oldSource);}catch(e){caught=e;}assert(caught instanceof assert.AssertionError);assert(caught.message.includes(marker));return {assertion:caught.message};});
 for(const elapsed of [999,1000,1001])for(const hasModel of [false,true])
  await run('same-record lease '+elapsed+'ms, model='+hasModel,async()=>{
   const h=await make({hash:'&simWx=0&simCloud=0'});present(h);h.run('render();paintClouds(simNow()/1000)');
   const record=h.run('weather'),receipt=h.run('cloudPublicationReceipt()'),before=state(h);h.at(890000+elapsed);if(!hasModel)h.run('today=null');
   assert.equal(h.run('weather'),record);passive(h,receipt,elapsed<1000);
   return nativeBoundary(h,async b=>{const captured=b.foreground.capture(183),after=state(h);assert.equal(captured.cloudRGBA[3]>0,elapsed<1000);
    if(elapsed>=1000)clear(h);else assert.deepEqual(after.cov,before.cov);assert.equal(after.population,before.population);assert.deepEqual(after.phase,before.phase);
    return {before,after,capturedAlpha:captured.cloudRGBA[3],receipt:captured.cloudAuthority};});
  });
 for(const order of ['capture-before-render','render-before-capture'])for(const hasModel of [false,true])
  await run('unchanged healthy evidence '+order+', model='+hasModel,async()=>{
   const h=await make({hash:'&simWx=0&simCloud=0'});present(h,{lease:60000});h.run('render();paintClouds(simNow()/1000)');
   const receipt=h.run('cloudPublicationReceipt()'),before=state(h);if(!hasModel)h.run('today=null');
   return nativeBoundary(h,async b=>{if(order==='render-before-capture')h.run('render()');const frame=b.foreground.capture(183);
    assert.equal(frame.cloudAuthority,receipt);assert.equal(frame.cloudRGBA[3],192);if(order==='capture-before-render')h.run('render()');
    assert.equal(h.run('cloudPublicationReceipt()'),receipt);const after=state(h);assert.deepEqual(after.cov,before.cov);axes(after,before);return {before,after};});
  });
 for(const order of ['capture-before-render','render-before-capture'])
  await run('unchanged model-only healthy A-to-B '+order,async()=>{
   const h=await make({fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?{ok:true,json:async()=>payload({time:'2026-09-08T23:46'})}:new Promise(()=>{})});
   h.at(951000);assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render();paintClouds(simNow()/1000)');
   const a=h.run('weather'),receipt=h.run('cloudPublicationReceipt()'),before=state(h);await h.refresh({time:'2026-09-09T00:00',cloud_cover_low:80,cloud_cover_mid:75,cloud_cover_high:50});
   assert.notEqual(h.run('weather'),a);passive(h,receipt,true);
   return nativeBoundary(h,async b=>{if(order==='render-before-capture')h.run('render()');const frame=b.foreground.capture(183);assert.equal(frame.cloudRGBA[3],192);
    if(order==='capture-before-render'){assert.equal(frame.cloudAuthority,receipt);assert.deepEqual(state(h).cov,before.cov);h.run('render()');}
    const after=state(h);after.cov.forEach((v,i)=>assert(Math.abs(v-(before.cov[i]+([.8,.75,.5][i]-before.cov[i])*.08))<1e-12));axes(after,before);passive(h,receipt,false);return {before,after};});
  });
 for(const newState of ['wet','dry'])for(const hasModel of [false,true])
  await run('fresh same-record '+newState+' publication, model='+hasModel,async()=>{
   const h=await make({hash:'&simWx=0&simCloud=0'});present(h,{lease:60000});h.run('render();paintClouds(simNow()/1000)');
   const record=h.run('weather'),old=h.run('cloudPublicationReceipt()'),before=state(h),evidence=present(h,{lease:60000,state:newState});
   if(!hasModel)h.run('today=null');passive(h,old,false);assert.equal(h.run('weather'),record);
   h.run('render();paintClouds(simNow()/1000)');
   if(!hasModel){clear(h);assert(h.run('adoptPrayerBundle(__fixturePrayer,"08-09-2026",null,true,false)'));h.run('render();paintClouds(simNow()/1000)');}
   assert.notEqual(h.run('cloudPublicationReceipt()'),old);assert.equal(h.run('_cloudPublication.decision.present.evidence'),evidence);passive(h,old,false);
   const current=h.run('cloudPublicationReceipt()'),after=state(h);axes(after,before);
   assert.deepEqual(after.targets,newState==='wet'?[.9,.85,.3]:[0,0,0]);
   if(hasModel)after.cov.forEach((v,i)=>assert(Math.abs(v-before.cov[i]*(newState==='wet'?1:.92))<1e-12));
   else assert.deepEqual(after.cov,newState==='wet'?[.9,.85,.3]:[0,0,0]);
   h.run('render();paintClouds(simNow()/1000)');assert.equal(h.run('cloudPublicationReceipt()'),current);return {before,after};
  });
 await run('ancillary spatial expiry changes decision without cloud receipt churn',async()=>{
  const h=await make({hash:'&simWx=0&simCloud=0'});present(h,{lease:60000,spatial:true});h.run('render();paintClouds(simNow()/1000)');
  const initialDecision=h.run('weatherDecision()'),receipt=h.run('cloudPublicationReceipt()'),evidence=h.run('weatherDecision().present.evidence');
  assert.equal(initialDecision.spatial.state,'nearby-precipitation');h.at(890501);h.clock.now=0;
  const candidate=h.run('weatherDecision()');assert.notEqual(candidate,initialDecision);assert.equal(candidate.spatial.state,'unavailable');assert.equal(candidate.present.evidence,evidence);
  const before=state(h);h.run('render();paintClouds(simNow()/1000)');assert.equal(h.run('cloudPublicationReceipt()'),receipt);passive(h,receipt,true);
  const after=state(h);assert.deepEqual(after.cov,before.cov);axes(after,before);return {oldSpatial:initialDecision.spatial,newSpatial:candidate.spatial,before,after};
 });
 await run('new forecast changes information without cloud receipt churn',async()=>{
  const h=await make({hash:'&simWx=3&simCloud=95'});const receipt=h.run('cloudPublicationReceipt()'),decision=h.run('weatherDecision()'),before=state(h);
  h.ctx.__hourly={time:['2026-09-09T00:00','2026-09-09T01:00'],temperature_2m:[20,22],weather_code:[3,0]};
  h.run('weatherTrack=admitWeatherTrack(__hourly,{units,zone:tz,retrievedAt:Date.now(),target:currentWeatherTarget()},null)');assert(h.run('weatherTrack'));assert.notEqual(h.run('weatherDecision()'),decision);assert(h.run('weatherDecision().forecast'));
  h.run('render();paintClouds(simNow()/1000)');assert.equal(h.run('cloudPublicationReceipt()'),receipt);const after=state(h);assert.deepEqual(after.cov,before.cov);axes(after,before);return {before,after};
 });
 for(const kind of ['preview','refined'])for(const action of ['unchanged-model','unchanged-no-model','expired-model','expired-no-model','fresh-wet-published','fresh-dry-published','fresh-no-model'])
  await run('actual '+kind+' pending decode, '+action,async()=>{
   const h=await make({hash:'&simWx=0&simCloud=0'});present(h,{lease:1000});h.run('render();paintClouds(simNow()/1000)');const old=h.run('cloudPublicationReceipt()');
   return nativeBoundary(h,async b=>{const owner=nativeOwner(b,kind);assert.equal(b.images.length,1);assert.equal(owner.drawCount(),0);
    if(action.includes('no-model'))h.run('today=null');
    if(action.startsWith('expired'))h.at(891000);
    if(action.startsWith('fresh')){present(h,{lease:60000,state:action==='fresh-dry-published'?'dry':'wet'});if(action.endsWith('published'))h.run('render();paintClouds(simNow()/1000)');}
    const unchanged=action.startsWith('unchanged'),clearSuccessor=action.startsWith('expired')||action==='fresh-no-model';
    passive(h,old,unchanged);b.images[0].resolve();await b.flush();
    assert(owner.drawCount()>0,'actual native source owner publishes a successor or still-valid capture');
    const composition=owner.read();assert(composition);assert.equal(composition.maxCloudAlpha>0,!clearSuccessor);
    if(clearSuccessor)clear(h);else assert(h.raster.currentFills>0);
    assert.deepEqual(copy(composition.cloudAuthority),copy(h.run('cloudPublicationReceipt()')),'native consumption names the current active receipt');
    if(unchanged)assert.equal(h.run('cloudPublicationReceipt()'),old);else assert.notEqual(h.run('cloudPublicationReceipt()'),old);
    const drawCount=owner.drawCount();b.images[0].resolve();await b.flush();assert.equal(owner.drawCount(),drawCount);assert.deepEqual(b.errors,[]);
    return {action,composition,draws:owner.drawCount(),images:b.images.length,state:state(h)};
   });
  });
 await run('actual refined same-byte reuse adopts fresh wet receipt without extra raster draw',async()=>{
  const h=await make({hash:'&simWx=0&simCloud=0'});present(h,{lease:60000});h.run('render();paintClouds(simNow()/1000)');
  return nativeBoundary(h,async b=>{const owner=nativeOwner(b,'refined');b.images[0].resolve();await b.flush();const old=h.run('cloudPublicationReceipt()'),draws=owner.drawCount();
   present(h,{lease:60000});h.run('render();paintClouds(simNow()/1000)');const current=h.run('cloudPublicationReceipt()');assert.notEqual(current,old);
   owner.update();assert.equal(owner.drawCount(),draws);assert(owner.skipCount()>0);assert.deepEqual(copy(owner.read().cloudAuthority),copy(current));passive(h,old,false);return {draws,skips:owner.skipCount(),composition:owner.read()};});
 });
}
main().catch(e=>{process.exitCode=1;}).finally(()=>{
 const result={sourceSha256:sha(Buffer.from(source)),oldSourceSha256:sha(Buffer.from(oldSource)),nativeSourceHashes:{hooks:sha(Buffer.from(hooks)),refined:sha(Buffer.from(refinedSource)),preview:sha(Buffer.from(previewSource))},
  boundary:'actual authored owners and native capture/mask/preview/refined publication source; controlled transport/time/DOM/canvas and numerical-sky fixture; no browser pixels',passed:records.filter(r=>r.status==='pass').length,failed:records.filter(r=>r.status==='fail').length,records};
 fs.writeFileSync(path.join(out,'source-f02-independent.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,failed:result.failed}));
});
