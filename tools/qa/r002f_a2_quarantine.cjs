'use strict';
// Opt-in architecture experiment against the real Moon lifecycle owner. This
// source transformer does not write or install a production runtime.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../..');
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
function once(source, from, to) {
  if (source.split(from).length !== 2) throw Error('expected unique quarantine source anchor: '+from.slice(0,90));
  return source.replace(from,()=>to);
}
function quarantineCandidate(source) {
  if(source.includes('let hiddenQuarantineResearch='))throw Error('quarantine research transform already applied');
  let out=once(source,' let initialHeadEligible=true,bootCache=', ` let hiddenQuarantineResearch=null,reusableResearch=null,preparingResearch=false,reusesResearch=0;
 let initialHeadEligible=true,bootCache=`);
  out=once(out,"const canvas=document.createElement('canvas');","let canvas=document.createElement('canvas');");
  out=once(out,'const detail=(inner=>','let activeDetailResearch=startMoonDetail();\n const detail=(()=>');
  const wrapper=out.slice(out.indexOf('const detail=(()=>'),out.indexOf(' let registered=null;'));
  out=once(out,wrapper,wrapper.replaceAll('inner.','activeDetailResearch.').replace('})(startMoonDetail());','})();'));
  out=once(out,'function fallback(reason){accepted=null;', 'function fallback(reason){reusableResearch=null;accepted=null;');
  out=once(out,'function withdrawAuthority(reason){accepted=null;', 'function withdrawAuthority(reason){reusableResearch=null;accepted=null;');
  out=once(out,' function clear(reason,initialDocument=false){\n',
    ' function clear(reason,initialDocument=false){\n  if(reason!=="document hidden")hiddenQuarantineResearch=null;\n');
  out=once(out,'  syncTexture(capture());status.lastAdoption=',`  reusableResearch=m.kind==='result'?narrowResearch(m,accepted):null;
  hiddenQuarantineResearch=null;
  syncTexture(capture());status.lastAdoption=`);
  const helper = `
 // Retain the five validated, dedicated views. Never keep the worker envelope or pooled intermediates.
 function narrowResearch(m,record){
  if(![m.physicalIdentity,m.profileIdentity].every(x=>typeof x==='string'&&x.trim())||
     m.physicalIdentity!==record.physicalIdentity||m.profileIdentity!==record.profileIdentity||
     JSON.stringify(record.scene.profile)!==JSON.stringify(profile()))return null;
  const {rgba,calendarRgba,surfaceLinear,calendarLinear,surfaceCoverage,width,height,surfaceSize,surfaceExtent}=m;
  const views=[rgba,calendarRgba,surfaceLinear,calendarLinear,surfaceCoverage];
  if(views.some(v=>v.byteOffset!==0||v.byteLength!==v.buffer.byteLength)||new Set(views.map(v=>v.buffer)).size!==5)return null;
  return {record,rgba,calendarRgba,surfaceLinear,calendarLinear,surfaceCoverage,width,height,surfaceSize,surfaceExtent,
    bytes:views.reduce((n,v)=>n+v.byteLength,0)};
 }
 function custodyCurrentResearch(saved,s){
  const r=saved.data.record,c=saved.clock;
  return !!s&&!disposed&&epoch===saved.resumeEpoch&&r.scope===scope(s)&&phaseError(r,s)<=PHASE_POSITION_BUDGET&&
   (s.timeScale??1)===c.rate&&Math.abs((s.utcMs-c.utcMs)-(performance.now()-c.now)*c.rate)<=1000&&
   s.presentationReady!==false&&s.initialWarranted!==false&&profileMode==='calendar'&&!referenceScene;
 }
 // Diagnostic observation keeps the original capture and empty-layout behavior.
 // Only production polling and the request's final presentation read consume custody.
 function lifecycleCaptureResearch(){
  const s=capture();
  if(hiddenQuarantineResearch&&!custodyCurrentResearch(hiddenQuarantineResearch,s))hiddenQuarantineResearch=null;
  return s;
 }
 function stashHiddenResearch(){
  const data=reusableResearch;
  if(!accepted||data?.record!==accepted||!clock){hiddenQuarantineResearch=null;return;}
  const saved={data,clock:{...clock},resumeEpoch:epoch};
  hiddenQuarantineResearch=custodyCurrentResearch(saved,capture())?{...saved,resumeEpoch:epoch+1}:null;
 }
 function readmitHiddenResearch(saved,s){
  const data=saved.data,original=data.record,began=performance.now();
  const authorized=state=>hiddenQuarantineResearch===saved&&!accepted&&custodyCurrentResearch(saved,state)&&!state.paused&&!document.hidden;
  let staged=null,previous=null,committed=null;
  preparingResearch=true;
  try{
   if(!authorized(s))return;
   // Stage on private owners. Reentrant preparation can publish a successor without the abandoned attempt touching its detail or canvas.
   staged=startMoonDetail();
   const prepared=staged.adopt({linear:data.surfaceLinear,calendarLinear:data.calendarLinear,coverage:data.surfaceCoverage,size:data.surfaceSize,extent:data.surfaceExtent,identity:original.physicalIdentity});
   if(prepared===false)throw Error('quarantine detail preparation declined');
   const prefixMs=performance.now()-began;
   const up=Math.max(0,Math.min(1,s.up)),next=document.createElement('canvas');
   next.width=data.width;next.height=data.height;
   const bytes=blendCalendarBytes(data.rgba,data.calendarRgba,up);
   next.getContext('2d',{willReadFrequently:true}).putImageData(new ImageData(bytes,next.width,next.height),0,0);
   const fresh=capture();
   if(!authorized(fresh)||Math.max(0,Math.min(1,fresh.up))!==up)return;
   previous=activeDetailResearch;activeDetailResearch=staged;staged=null;
   canvas=next;upperBytes=data.rgba;calendarBytes=data.calendarRgba;textureUp=up;
   accepted=committed={...original,token:++adoptions,epoch};publishedToken=committed.token;
   reusableResearch={...data,record:committed};hiddenQuarantineResearch=null;faultRecord=null;
   status.status='ready';status.quality='empirical-adaptive';status.visibleSource='refined-terrain';status.phase=original.scene.fraction;
   window.SalahMoonHost?.publish(canvas,false);
   if(accepted===committed){
    status.lastAdoption={at:began,prefixMs,totalMs:performance.now()-began,source:status.visibleSource};
    reusesResearch++;composeAdopted();
   }
  }catch(error){note(error);if(committed&&accepted===committed)fallback('quarantine publication failure');}
  finally{
   if(saved===hiddenQuarantineResearch)hiddenQuarantineResearch=null;
   if(staged&&staged!==activeDetailResearch)staged.dispose();
   if(previous&&previous!==activeDetailResearch)previous.dispose();
   preparingResearch=false;
  }
 }
`;
  out=once(out,' function poll(force=false){',helper+' function poll(force=false){');
  out=once(out,'if(disposed)return;const s=capture(),now=performance.now();recoverIfDue(now);',
    'if(disposed)return;const s=lifecycleCaptureResearch(),now=performance.now();recoverIfDue(now);');
  out=once(out,'poll();return presentation(capture());','poll();return presentation(lifecycleCaptureResearch());');
  out=once(out,'  if(s.paused){revokeInitialHead();','  if(document.hidden||s.paused){revokeInitialHead();');
  out=once(out,"  if((accepted&&!sameScope(accepted,s))",`  if(hiddenQuarantineResearch&&!preparingResearch){readmitHiddenResearch(hiddenQuarantineResearch,s);return poll(force);}
  if((accepted&&!sameScope(accepted,s))`);
  out=once(out,"const visibility=()=>{if(document.hidden){clear('document hidden');",
    "const visibility=()=>{if(document.hidden){stashHiddenResearch();clear('document hidden');");
  out=once(out,' window.SalahMoonRuntime={\n',
    ' window.SalahMoonRuntime={\n  get quarantineResearch(){return {records:hiddenQuarantineResearch?1:0,reuses:reusesResearch,bytes:hiddenQuarantineResearch?.data.bytes??0};},\n');
  return out;
}
// The original generator above remains reproducible for its archived receipts.
// This successor gives ordinary messages and re-admitted refined material the
// same publishing owner. Only preparation differs, and the restore path keeps
// its existing final authority fence and reentrant fault cleanup.
function canonicalQuarantineCandidate(source){
 let out=quarantineCandidate(source);
 const start=out.indexOf(' function adopt(m,record){'),assign=out.indexOf('  accepted={token:++adoptions',start);
 if(start<0||assign<0)throw Error('ordinary adoption owner missing');
 const material='{linear:m.surfaceLinear,calendarLinear:m.calendarLinear,coverage:m.surfaceCoverage,size:m.surfaceSize,extent:m.surfaceExtent,identity:m.physicalIdentity}';
 const ordinary=out.slice(start,assign);
 if(!ordinary.includes('calendarBytes=m.calendarRgba;textureUp=null;')||!ordinary.includes(material))throw Error('unexpected adopted texture owner');
 out=once(out,ordinary,` function adopt(m,record,preparedHandover=null){
  const began=performance.now();
  const researchAdoptedMaterial=${material};
  if(preparedHandover){
   activeDetailResearch=preparedHandover.detail;
   canvas=preparedHandover.canvas;
  }else{
   detail.adopt(researchAdoptedMaterial);
   canvas.width=m.width;canvas.height=m.height;
  }
  const prefixMs=preparedHandover?preparedHandover.prefixMs:performance.now()-began;
  upperBytes=m.rgba;calendarBytes=m.calendarRgba;textureUp=preparedHandover?preparedHandover.up:null;
`);
 // Both paths pass the same view installation and accepted-record construction
 // above, including any separately installed selector material association. The
 // privately prepared canvas already holds the blend. Do not re-enter syncTexture.
 out=once(out,'  status.quality=m.diagnostics.quality.status;', '  if(preparedHandover){publishedToken=accepted.token;return accepted;}\n  status.quality=m.diagnostics.quality.status;');
 const old=`   previous=activeDetailResearch;activeDetailResearch=staged;staged=null;
   canvas=next;upperBytes=data.rgba;calendarBytes=data.calendarRgba;textureUp=up;
   accepted=committed={...original,token:++adoptions,epoch};publishedToken=committed.token;`;
 const replacement=`   previous=activeDetailResearch;
   // The source is the one previously accepted refined message. No worker
   // result or physical identity is synthesized on return.
   const retained={...data,kind:'readmitted-refined',scene:original.scene,physicalIdentity:original.physicalIdentity,profileIdentity:original.profileIdentity};
   committed=adopt(retained,{id:original.id,key:original.key,scope:original.scope,epoch},{detail:staged,canvas:next,prefixMs,up});
   staged=null;`;
 return once(out,old,replacement);
}
function moonFixture(source,options={initial:true},probes=null) {
  const tests = path.join(repo,'moon/tests'), hostSource=fs.readFileSync(path.join(tests,'host.test.cjs'),'utf8');
  const start=hostSource.indexOf('function rig('),end=hostSource.indexOf('\n}\n',start)+3;
  if(start<0||end<start)throw Error('Moon source fixture owner missing');
  const shim={...fs,readFileSync(file,...args){return path.resolve(file)===path.join(repo,'moon/src/moon-native.mjs')?source:fs.readFileSync(file,...args);}};
  let fixture=hostSource.slice(start,end);
  if(probes){
    probes.retiredStages=0;
    fixture=once(fixture,'getContext:()=>({putImageData(){}})','getContext(){return {putImageData:image=>{this.pixels=image.data;}}}');
    fixture=once(fixture,'startMoonDetail:()=>detail,blendCalendarBytes:a=>a',`startMoonDetail:()=>{
      const owner={available:false,adopt(s){detail.adopt.call(this,s);this.identity=s.identity;probes.detail?.(s);},
        clear(){this.available=false;},dispose(){this.available=false;probes.retiredStages++;},
        get state(){return {identity:this.identity};}};
      probes.activeIdentity=()=>w.SalahMoonDetail?.state?.identity;
      return owner;
    },blendCalendarBytes:(a,b,up)=>{probes.blend?.(a,b);return blend(a,b,up);}`);
  }
  const calendar=fs.readFileSync(path.join(repo,'moon/src/moon-calendar.mjs'),'utf8');
  const blend=new Function(calendar+';return blendCalendarBytes;')();
  const rig=new Function('require','__dirname','process','fs','vm','path','crypto','probes','blend',
    'const src=path.join(__dirname,"../src");'+fixture+';return rig;')(require,tests,process,shim,vm,path,crypto,probes,blend);
  return rig(options);
}
function ready(source,probes=null,edit=()=>{}) {
  const r=moonFixture(source,{initial:true},probes);r.state.timeScale=1;
  r.workers[0].emit({kind:'ready'});const message=r.response();edit(message);r.workers[0].emit(message);r.flush();
  return {r,message,rt:r.w.SalahMoonRuntime};
}
function hide(f) {
  const before=f.r.fallbacks;
  f.r.doc.hidden=true;f.r.state.paused=true;f.r.events.get('visibilitychange')();
  return {hiddenPresentable:f.rt.presentable,hiddenDetailAvailable:f.r.detail.available,
    hiddenFallbacks:f.r.fallbacks-before,quarantinedRecords:f.rt.quarantineResearch?.records??0,
    quarantinedBytes:f.rt.quarantineResearch?.bytes??0};
}
function show(f) {
  f.r.advance(100);f.r.state.utcMs+=100;f.r.doc.hidden=false;f.r.state.paused=false;
  f.r.events.get('visibilitychange')();
}
function outcome(f,initialCount,renders,published) {
  const o=f.rt.observe();
  return {initialRecomputationsOnReturn:f.r.initialRenders-initialCount,currentAfterReturn:o.current,
    sourceAfterReturn:o.state.visibleSource,reuses:f.rt.quarantineResearch?.reuses??0,
    quarantinedAfterReturn:f.rt.quarantineResearch?.records??0,newWorkerRenders:f.r.workers[0].sent.filter(m=>m.kind==='render').length-renders,
    pendingTimersAfterReturn:f.r.jobs.size,publishesDuringReturn:f.r.published-published};
}
const fields=['rgba','calendarRgba','surfaceLinear','calendarLinear','surfaceCoverage'];
function payloadDigest(a){return sha(Buffer.from(a.buffer,a.byteOffset,a.byteLength));}
function custodyControls(source) {
  // This private observation hook exists only in the fixture. It reports fields,
  // object identity and content digests without exposing the proposal's payload API.
  const observed=once(source,'  const data=reusableResearch;','  const data=reusableResearch;window.__inspectCustody?.(data);');
  const probes={},r=moonFixture(observed,{initial:true},probes),rt=r.w.SalahMoonRuntime;
  r.state.timeScale=1;r.workers[0].emit({kind:'ready'});
  const m=r.response(),n=m.surfaceSize*m.surfaceSize;
  m.solar=new Float32Array(n*3);m.earth=new Float32Array(n*3);m.coverage=new Float64Array(n);
  for(let i=0;i<n;i++){
    m.surfaceCoverage[i]=(1+i%7)/8;
    for(let k=0;k<3;k++){m.surfaceLinear[3*i+k]=m.surfaceCoverage[i]*(k+1)/4;m.calendarLinear[3*i+k]=m.surfaceCoverage[i]*(k+1)/32;}
  }
  for(let i=0;i<m.rgba.length;i++){m.rgba[i]=i%4===3?255:80+i%110;m.calendarRgba[i]=i%4===3?255:3+i%34;}
  const originals=Object.fromEntries(fields.map(k=>[k,payloadDigest(m[k])]));
  const rows=[];
  r.w.__inspectCustody=data=>{
    if(!data)return;
    rows.push({keys:Object.keys(data).sort(),distinctViews:fields.every(k=>data[k]===m[k]),bytes:data.bytes,
      surplusReachable:Object.values(data).some(x=>x===m||x===m.solar||x===m.earth||x===m.coverage)});
  };
  const writes=[],details=[],blends=[];
  r.w.SalahMoonHost.publish=c=>writes.push({current:rt.observe().current,identity:rt.observe().state.accepted?.identity,
    profile:rt.observe().state.accepted?.profile,hash:payloadDigest(c.pixels)});
  probes.detail=s=>details.push({identity:s.identity,sameViews:s.linear===m.surfaceLinear&&s.coverage===m.surfaceCoverage&&s.calendarLinear===m.calendarLinear,
    surfaceLinear:payloadDigest(s.linear),calendarLinear:payloadDigest(s.calendarLinear),surfaceCoverage:payloadDigest(s.coverage)});
  probes.blend=(upper,lower)=>blends.push({sameViews:upper===m.rgba&&lower===m.calendarRgba,rgba:payloadDigest(upper),calendarRgba:payloadDigest(lower)});
  r.workers[0].emit(m);r.flush();
  const f={r,rt};hide(f);r.state.up=0;show(f);
  return {records:rows,detail:details,blends,writes,originals,originalIdentity:m.physicalIdentity,originalProfile:m.profileIdentity,
    reuses:rt.quarantineResearch.reuses,surplusBytes:m.solar.byteLength+m.earth.byteLength+m.coverage.byteLength};
}
function pairedShow(f) {
  const before=f.r.published;
  f.r.advance(100);f.r.state.utcMs+=100;f.r.doc.hidden=false;f.r.events.get('visibilitychange')();
  const paused={presentable:f.rt.presentable,records:f.rt.quarantineResearch.records,publishes:f.r.published,newWrites:f.r.published-before};
  // Execute the exact second listener. Its classList is the fixture's pause
  // capture; its actual request calls back into the Moon runtime above.
  const html=fs.readFileSync(path.join(repo,'src/native/index.html'),'utf8');
  const begin=html.indexOf('  function setVis(){'),end=html.indexOf('  if("IntersectionObserver"',begin);
  if(begin<0||end<0||html.indexOf('  function setVis(){',begin+1)>=0)throw Error('native setVis owner changed');
  const cEl={classList:{contains:key=>key==='paused'&&f.r.state.paused,toggle:(key,on)=>{if(key==='paused')f.r.state.paused=on;}}};
  const native={document:{addEventListener:(name,listener)=>{if(name==='visibilitychange')native.listener=listener;}},
    window:f.r.w,cEl,visible:()=>!f.r.doc.hidden,ADVANCING:false,rebaseCloudMotion(){},start(){},stop(){},updateSkySurface(){},recordRenderFault(stage,e){throw e;}};
  vm.runInNewContext(html.slice(begin,end),native);native.listener();
  return paused;
}
function roundTrips(source,only=null) {
  const changes={sceneIdentity:'B',generation:1,dpr:2,waxing:true,timeScale:2,utcMs:8000,fraction:.51,presentationReady:false,initialWarranted:false};
  return Object.entries(changes).filter(([key])=>!only||key===only).map(([key,value])=>{
    const f=ready(source);hide(f);
    const original=f.r.state[key],published=f.r.published;
    f.r.state[key]=value;f.rt.request();const first=f.rt.quarantineResearch.records;
    f.r.state[key]=original;f.rt.request();
    const second=f.rt.quarantineResearch.records,paused=pairedShow(f);
    return {key,first,second,hiddenOrPausedWrites:paused.publishes-published,pausedPresentable:paused.presentable,reuses:f.rt.quarantineResearch.reuses};
  });
}
function diagnosticRoundTrip(source,reads) {
  const f=ready(source,{},message=>{
    for(let i=0;i<message.rgba.length;i+=4){message.rgba[i]=121;message.rgba[i+3]=message.calendarRgba[i+3]=255;}
  });
  hide(f);
  f.r.state.sceneIdentity='B';
  const layouts=f.r.layoutReads,published=f.r.published;
  for(const read of reads){
    if(read==='observe'){if(f.rt.observe().current)throw Error('hidden observation claims current');}
    else if(f.rt.presentable)throw Error('hidden presence claims current');
  }
  const hiddenLayoutReads=f.r.layoutReads-layouts,hiddenWrites=f.r.published-published,recordsAfterReads=f.rt.quarantineResearch.records;
  f.r.state.sceneIdentity='A';pairedShow(f);
  const visible=f.rt.observe();
  return {hiddenLayoutReads,hiddenWrites,recordsAfterReads,current:visible.current,source:visible.state.visibleSource,
    reuses:f.rt.quarantineResearch.reuses,initialRenders:f.r.initialRenders,
    workerRenders:f.r.workers[0].sent.filter(m=>m.kind==='render').length,publishes:f.r.published,pendingTimers:f.r.jobs.size,
    finalDigest:payloadDigest(visible.surface.pixels),originalDigest:payloadDigest(f.message.rgba)};
}
function duringPreparation(source,change){
  const probes={},f=ready(source,probes);
  hide(f);
  const writes=[];
  f.r.w.SalahMoonHost.publish=c=>{
    const observed=f.rt.observe();writes.push({current:observed.current,source:observed.state.visibleSource,identity:observed.state.accepted?.identity,
      phase:observed.state.accepted?.scene.fraction,hash:payloadDigest(c.pixels)});
  };
  let successor=null;
  probes.detail=()=>{
    delete probes.detail;
    if(change==='phase')f.r.state.fraction=.51;
    else f.r.state.generation++;
    if(change==='successor'||change==='successor-then-throw'){
      f.rt.request();
      const o=f.rt.observe();
      successor={surface:o.surface,identity:o.state.accepted?.identity};
      if(change==='successor-then-throw')throw Error('injected after nested successor');
    }
  };
  pairedShow(f);
  const o=f.rt.observe();
  return {change,writes,reuses:f.rt.quarantineResearch.reuses,successorPreserved:successor?o.surface===successor.surface&&o.state.accepted?.identity===successor.identity:null,
    retiredStages:probes.retiredStages,activeDetailIdentity:probes.activeIdentity?.()};
}

function quarantineExperiment(transform=quarantineCandidate) {
  const source=fs.readFileSync(path.join(repo,'moon/src/moon-native.mjs'),'utf8'),candidate=transform(source);
  function returnRow(text,change=()=>{}) {
    const f=ready(text),initialCount=f.r.initialRenders,renders=f.r.workers[0].sent.filter(m=>m.kind==='render').length;
    const hidden=hide(f);change(f);const published=f.r.published;show(f);
    return {...hidden,...outcome(f,initialCount,renders,published)};
  }
  const baseline=returnRow(source),continuous=returnRow(candidate);
  const mutations=[
    ['generation',f=>f.r.state.generation++],['scene',f=>f.r.state.sceneIdentity='other'],['ratio',f=>f.r.state.dpr=2],
    ['lit-limb',f=>f.r.state.waxing=true],['phase',f=>f.r.state.fraction=.51],['seek',f=>f.r.state.utcMs+=5000],
    ['clock-rate',f=>f.r.state.timeScale=2],['invalidation',f=>f.rt.invalidate('explicit hidden invalidation')],
    ['profile',f=>f.rt.setProfile('reference')],['not-ready',f=>f.r.state.presentationReady=false],
    ['not-warranted',f=>f.r.state.initialWarranted=false]
  ];
  const rejections=mutations.map(([name,fn])=>{
    const control=returnRow(source,fn),row=returnRow(candidate,fn);
    return {name,...row,baselinePublishesDuringReturn:control.publishesDuringReturn,
      extraPublicationsOverBaseline:row.publishesDuringReturn-control.publishesDuringReturn};
  });
  const d=ready(candidate);hide(d);d.rt.dispose();
  const disposed={presentable:d.rt.presentable,quarantined:d.rt.quarantineResearch.records,workerTerminated:d.r.workers[0].terminated};
  const late=ready(candidate);hide(late);const rejected=late.rt.observe().state.rejected;
  late.r.workers[0].emit(late.message);
  const lateReply={currentWhileHidden:late.rt.observe().current,rejectedDelta:late.rt.observe().state.rejected-rejected};
  show(late);lateReply.reusesAfterReturn=late.rt.quarantineResearch.reuses;
  const bad=ready(candidate);hide(bad);bad.r.detail.adopt=()=>{throw Error('quarantine adoption failure');};
  let threw=false;try{show(bad);}catch{threw=true;}
  const observation=bad.rt.observe();
  const adoptionFailure={threw,current:observation.current,reuses:bad.rt.quarantineResearch.reuses,errors:observation.state.errors};
  const paired=ready(candidate);hide(paired);const paused=pairedShow(paired);
  const invalidPayloads=[['empty-physical',m=>m.physicalIdentity=''],['blank-profile',m=>m.profileIdentity=' '],
    ['missing-profile',m=>delete m.profileIdentity],['oversize-backing',m=>{const view=new Uint8ClampedArray(m.rgba.length+4);m.rgba=view.subarray(4);}]]
    .map(([name,edit])=>{const f=ready(candidate,null,edit),hidden=hide(f);show(f);return {name,records:hidden.quarantinedRecords,reuses:f.rt.quarantineResearch.reuses};});
  const trips=roundTrips(candidate),preparation=['generation','phase','successor','successor-then-throw'].map(c=>duringPreparation(candidate,c));
  const finalFenceMutant=once(candidate,'if(!authorized(fresh)||Math.max(0,Math.min(1,fresh.up))!==up)return;','if(!fresh)return;');
  const skippedHiddenObservation=once(candidate,'if(hiddenQuarantineResearch&&!custodyCurrentResearch(hiddenQuarantineResearch,s))hiddenQuarantineResearch=null;','');
  const retainedEnvelope=once(candidate,'return {record,rgba,calendarRgba,','return {workerEnvelope:m,record,rgba,calendarRgba,');
  const diagnosticReads={none:[],observe:['observe'],presentable:['presentable'],repeated:['observe','presentable','observe']};
  const diagnosticRoundTrips=Object.fromEntries(Object.entries(diagnosticReads).map(([name,reads])=>[name,diagnosticRoundTrip(candidate,reads)]));
  const impure=once(candidate,'if(!withGeometry)return null;',
    'if(!withGeometry){if(hiddenQuarantineResearch)lifecycleCaptureResearch();return null;}');
  const controls={impureObservation:diagnosticRoundTrip(impure,['observe']),droppedFinalFence:duringPreparation(finalFenceMutant,'generation'),
    skippedHiddenObservation:roundTrips(skippedHiddenObservation,'sceneIdentity')[0],
    retainedEnvelope:custodyControls(retainedEnvelope).records};
  return {schema:'r002f-a2-quarantine/3',instrumentSha256:sha(fs.readFileSync(__filename)),
    nativeSetVisOwnerSha256:sha(fs.readFileSync(path.join(repo,'src/native/index.html'))),blendOwnerSha256:sha(fs.readFileSync(path.join(repo,'moon/src/moon-calendar.mjs'))),sourceSha256:sha(source),candidateSha256:sha(candidate),fixtureSha256:sha(fs.readFileSync(path.join(repo,'moon/tests/host.test.cjs'))),
    baseline,continuous,rejections,disposed,lateReply,adoptionFailure,trips,preparation,controls,invalidPayloads,diagnosticRoundTrips,payload:custodyControls(candidate),
    pairedReturn:{stillPaused:paused,reuses:paired.rt.quarantineResearch.reuses},
    scope:'real Moon runtime and source admission; receiver, worker, canvas, detail and host are explicit fixture doubles',
    limitations:['Not adopted production behavior. No browser/frame/dispatch performance result.',
      'Only five dedicated admitted views and required record metadata are kept by reference. Their byte sum is payload, not incremental reachability or native heap. The ordinary detail owner keeps surface/prefix data after clear(). Staged detail and canvas costs need native measurement.',
      'No old epoch reply is admitted. A re-admission retains the original geometry/physical/profile identities and receives a new epoch and adoption token.',
      'The existing hidden-presentation withdrawal and phase/currentness bounds remain active.']};
}
module.exports={quarantineCandidate,canonicalQuarantineCandidate,moonFixture,quarantineExperiment};
if(require.main===module){try{const file=process.argv[2];if(!file)throw Error('usage: node tools/qa/r002f_a2_quarantine.cjs <new-output.json>');const r=quarantineExperiment();fs.writeFileSync(path.resolve(file),JSON.stringify(r,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({baseline:r.baseline,continuous:r.continuous,rejections:r.rejections.map(x=>({name:x.name,reuses:x.reuses}))}));}catch(e){console.error('INCOMPLETE: '+e.stack);process.exitCode=2;}}
