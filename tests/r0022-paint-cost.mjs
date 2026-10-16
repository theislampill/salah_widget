/** R0022 cost acquisition for an independently reviewed, ROOT-admitted fixture.
 * Callbacks must bind actual original/native and receiving admission functions.
 * This module launches nothing and changes no production controller or source.
 * A raw return is measurement data, never acceptance or effect authority.
 */
function nextFrame(signal){
 return new Promise((resolve,reject)=>{
  let frame,timer;
  const finish=error=>{cancelAnimationFrame(frame);clearTimeout(timer);signal?.removeEventListener('abort',abort);error?reject(error):resolve();};
  const abort=()=>finish(new Error('Root cost admission was interrupted'));
  if(signal?.aborted){reject(new Error('Root cost admission was interrupted'));return;}
  signal?.addEventListener('abort',abort,{once:true});
  timer=setTimeout(()=>finish(new Error('No native animation frame within the finite cost fixture watchdog')),10000);
  frame=requestAnimationFrame(()=>finish());
 });
}

export async function collectCostScope({name, A, B, adapterSha256, persist,signal,
 now=()=>performance.now(), pulse=()=>nextFrame(signal)}){
 if(typeof name!=='string'||!name||!/^[a-f0-9]{64}$/.test(adapterSha256??''))throw new TypeError('Exact scope/adapter binding required');
 for(const adapter of [A,B])if(typeof adapter?.run!=='function'||typeof adapter?.snapshot!=='function')throw new TypeError('Actual synchronous function and state inventory required');
 if(typeof persist!=='function')throw new TypeError('Raw custody sink required');
 const record={name,actualFunction:name,adapterSha256,warmMs:{},slots:[],status:'ACQUIRING'};
 const copy=state=>structuredClone(state);
 async function invoke(adapter, samples, overhead){
  if(signal?.aborted)throw new Error('Root cost admission was interrupted');
  const preparationStart=now();
  await adapter.prepare?.();
  if(overhead)overhead.preparationMs.push(now()-preparationStart);
  const start=now();
  try{
   const value=adapter.run();
   if(value&&typeof value.then==='function')throw new TypeError('Asynchronous work is outside synchronous self-time scope');
  }finally{
   const elapsed=now()-start;
   if(samples)samples.push(elapsed);
  }
  const verificationStart=now();
  await adapter.verify?.();
  if(overhead)overhead.verificationMs.push(now()-verificationStart);
 }
 try{
  for(const [side,adapter] of [['A',A],['B',B]]){
   const start=now();
   while(now()-start<5000){await pulse();await invoke(adapter);}
   record.warmMs[side]=now()-start;
  }
  await persist(copy(record));
  for(let block=0;block<4;block++)for(const [order,side] of [...'ABBA'].entries()){
   const adapter=side==='A'?A:B,slot={block,order,side,elapsedMs:0,durationsMs:[],exceptions:[],startState:null,endState:null,observer:{preparationMs:[],verificationMs:[]}};
   const start=now();
   slot.startedPerformanceMs=start;
   slot.startedAbsoluteMs=typeof performance!=='undefined'?performance.timeOrigin+performance.now():null;
   try{
    slot.startState=copy(adapter.snapshot());
    while(now()-start<5000){await pulse();await invoke(adapter,slot.durationsMs,slot.observer);}
   }catch(error){slot.exceptions.push(String(error?.stack??error));}
   finally{
    slot.elapsedMs=now()-start;
    slot.endedAbsoluteMs=typeof performance!=='undefined'?performance.timeOrigin+performance.now():null;
    try{slot.endState=copy(adapter.snapshot());}catch(error){slot.exceptions.push(String(error?.stack??error));}
    record.slots.push(slot);
    if(slot.exceptions.length)record.status='INCOMPLETE';
    await persist(copy(record));
   }
   if(record.status==='INCOMPLETE')return record;
  }
  record.status='RAW_BATCHES_RETURNED';
 }catch(error){
  record.status='INCOMPLETE';record.error=String(error?.stack??error);
 }
 await persist(copy(record));
 return record;
}

/** One finite batch. ROOT's existing admitted browser driver supplies the exact
 * bindings and custody sink; there is no new browser/server/queue controller.
 * Only the real browser clock is used here. Synthetic collector controls call
 * collectCostScope directly and never create native receipts through this API.
 */
export async function collectR0022PaintCost({binding,scopes,persist,signal}){
 if(typeof window==='undefined'||typeof requestAnimationFrame!=='function')throw new Error('Actual browser fixture required');
 if(!binding||!Array.isArray(scopes)||typeof persist!=='function')throw new TypeError('Exact binding/scopes/raw sink required');
 const names=scopes.map(s=>s.name),required=['atmosphere','paint','renderMoon',...(binding.changedScopes??[])];
 if(!binding.changedScopes?.length||new Set(names).size!==names.length||required.some(name=>!names.includes(name)))throw new TypeError('Original and changed admission/display scopes required once');
 const raw={...structuredClone(binding),schema:'r0022-paint-cost/v1',measurementKind:'actual-browser',status:'ACQUIRING',scopes:[]};
 await persist(structuredClone(raw));
 try{
  for(const scope of scopes){
   raw.scopes.push(null);
   const result=await collectCostScope({name:scope.name,A:scope.A,B:scope.B,adapterSha256:scope.adapterSha256,signal,
    persist:async partial=>{raw.scopes[raw.scopes.length-1]=partial;await persist(structuredClone(raw));}});
   raw.scopes[raw.scopes.length-1]=result;
   if(result.status!=='RAW_BATCHES_RETURNED'){raw.status='INCOMPLETE';break;}
  }
  if(raw.status!=='INCOMPLETE')raw.status='RAW_BATCHES_RETURNED';
 }catch(error){raw.status='INCOMPLETE';raw.error=String(error?.stack??error);}
 await persist(structuredClone(raw));
 return raw;
}

/** Obtain original functions once, outside timed calls. The admitted fixture
 * owns the finite scene, exact source pins, counters and provider quiescence.
 * prepare runs outside self time and refreshes the actual geometry/arguments.
 */
export function nativePaintCostAdapters(nativeWindow,snapshot){
 if(typeof snapshot!=='function')throw new TypeError('Actual inventory reader required');
 const read=expression=>nativeWindow.eval(expression),renderMoon=read('renderMoon'),
  atmosphere=read('atmosphere'),paint=read('paint'),model=read('model');
 if([renderMoon,atmosphere,paint,model].some(fn=>typeof fn!=='function'))throw new TypeError('Actual native consumers unavailable');
 let input,atmosphereState;
 return {
  atmosphere:{snapshot,prepare(){renderMoon();input=model();},run(){return atmosphere(input);}},
  paint:{snapshot,prepare(){renderMoon();atmosphereState=atmosphere(model());},run(){return paint(atmosphereState);}},
  renderMoon:{snapshot,run(){return renderMoon();}}
 };
}

/** The guarded disposable host bridge supplies the ORIGINAL accept closure and
 * pre-presentation raw result/request. No reconstructed/mirrored accept body,
 * display-transformed publicFrame, fake raster or currentness bypass is used.
 * This callback intentionally includes decomposition before compose/publish.
 */
export function admissionCostAdapter({accept,rawResult,request,snapshot,readState,current,clone=structuredClone}){
 if([accept,snapshot,readState,current].some(fn=>typeof fn!=='function')||!rawResult?.raster||!request)throw new TypeError('Actual raw admission, state and currentness callbacks required');
 let result,before;
 return {snapshot,prepare(){
  if(!current(request))throw new Error('Original admission currentness fence rejects the benchmark request');
  result=clone(rawResult);before=readState();
 },run(){return accept(result,request.id,request);},verify(){
  const after=readState();
  if(after.status!=='ready'||after.renders!==before.renders+1||after.presentationDraws!==before.presentationDraws+1||after.rejections!==before.rejections||after.presentationRejections!==before.presentationRejections||after.presentationUtcMs!==request.observer?.utcMs)throw new Error('Actual admission/presentation did not complete; retain this batch');
 }};
}
