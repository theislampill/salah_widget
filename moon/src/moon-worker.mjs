


let enginePromise=null,latest=null,running=false,serial=0,shardEngine=null,shardSerial=0;const offlineParts=new Map();
async function read(url,maxBytes){
 const r=await fetch(url,{cache:'force-cache'});if(!r.ok)throw new Error('Moon asset HTTP '+r.status);
 const reader=r.body.getReader(),data=new Uint8Array(maxBytes);let at=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;if(at+value.length>maxBytes)throw new Error('Moon asset size');data.set(value,at);at+=value.length;}}finally{await reader.cancel();}
 if(at!==maxBytes)throw new Error('Moon asset truncated');return data;
}
function unbase64(s){const b=atob(s),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a;}
async function boot(m){
 const manifest=MOON_ASSET_MANIFEST;
 const from=(name,max)=>m.offline?new Promise((resolve,reject)=>offlineParts.set(name,{resolve,reject,bytes:new Uint8Array(max),at:0,index:0})):m.embedded?Promise.resolve(unbase64(m.embedded[name])):read(new URL(name,m.base),max);
 const wasm=unbase64(MOON_WASM_BASE64),[dem,colour]=await Promise.all([from(manifest.assets.dem.path,manifest.assets.dem.bytes),from(manifest.assets.colour.path,manifest.assets.colour.bytes)]);
 return MoonPool.create({wasm,dem,colour,manifest},m.workerSource);
}
async function pump(){
 if(running||!latest||!enginePromise)return;running=true;
 try{
  const engine=await enginePromise;
  while(latest){
   const job=latest;latest=null;const token=serial;
   try{
    const post=(kind,result)=>{
     if(token!==serial)return;
     const r={...result,...nativeCalendarResult(engine,result)};delete r.receiverCodes;delete r.ambiguous;delete r.qualityImages;
     self.postMessage({kind,id:job.id,identity:job.identity,...r},[r.rgba.buffer,r.surfaceLinear.buffer,r.surfaceCoverage.buffer,r.calendarLinear.buffer,r.calendarRgba.buffer]);
    };
    const result=await adaptiveRender(engine,job.scene,{cancelled:()=>token!==serial,onProgress:p=>self.postMessage({kind:'progress',id:job.id,...p}),onPreview:r=>post('preview',r)});
    post('result',result);
   }catch(error){if(token===serial)self.postMessage({kind:'error',id:job.id,identity:job.identity,error:String(error.message??error)});}
  }
 }catch(error){latest=null;self.postMessage({kind:'boot-error',error:String(error.message??error)});}
 finally{running=false;if(latest)pump();}
}
self.onmessage=e=>{
 const m=e.data;
 // Nested workers execute only the original kernel/receiver work. Their parent
 // joins rows before global adaptive decisions or any display publication.
 if(m.kind==='shard-boot'){
  if(shardEngine){self.postMessage({kind:'shard-error',id:m.id,error:'Duplicate row boot'});return;}
  shardEngine=MoonEngine.create(m.assets);shardEngine.then(()=>self.postMessage({kind:'shard-ready',id:m.id,result:true})).catch(error=>self.postMessage({kind:'shard-error',id:m.id,error:String(error.message??error)}));return;
 }
 if(m.kind==='shard-cancel'){shardSerial++;return;}
 if(m.kind==='shard-render'){
  const token=shardSerial;
  (async()=>{
   if(!shardEngine)throw new Error('Moon row not booted');const engine=await shardEngine;
   const result=await engine.render(m.scene,{...m.options,diagnostic:'fields',qualityFields:true,cancelled:()=>token!==shardSerial,onProgress:progress=>self.postMessage({kind:'shard-progress',id:m.id,progress})});
   if(token!==shardSerial)throw new DOMException('Superseded Moon rows','AbortError');
   const N=m.scene.size,[lo,hi]=m.options.rowOwner;
   if(!Number.isInteger(lo)||!Number.isInteger(hi)||lo<0||hi>N||hi<=lo)throw new Error('Moon row range');
   const pix=new Float64Array(engine.e.memory.buffer,engine.e.get_pixels(),N*N*24);result.material=new Float32Array(N*N*3);let shadowed=0;
   for(let i=0;i<N*N;i++){for(let k=0;k<3;k++)result.material[3*i+k]=pix[24*i+6+k];if(i>=lo*N&&i<hi*N&&pix[24*i+14]>1e-8&&pix[24*i+12]<pix[24*i+14]*.01)shadowed++;}
   result.diagnostics.ownedShadowedFacingSamples=shadowed;
   delete result.rgba;delete result.qualityImages;delete result.displayLinear;
   const transfers=['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','material'].map(k=>result[k].buffer);
   self.postMessage({kind:'shard-result',id:m.id,result},transfers);
  })().catch(error=>self.postMessage({kind:'shard-error',id:m.id,error:String(error.message??error),name:error.name}));return;
 }
 if(m.kind==='boot'){
  if(enginePromise){self.postMessage({kind:'boot-error',error:'Duplicate Moon worker boot'});return;}
  enginePromise=boot(m);enginePromise.then(()=>{self.postMessage({kind:'ready'});pump();}).catch(error=>self.postMessage({kind:'boot-error',error:String(error.message??error)}));
 }else if(m.kind==='asset-chunk'){
  const a=offlineParts.get(m.name);
  try{
   if(!a||m.index!==a.index||typeof m.data!=='string'||m.data.length>1500000)throw new Error('Offline Moon chunk order/size');
   const data=unbase64(m.data);if(a.at+data.length>a.bytes.length)throw new Error('Offline Moon chunk overflow');a.bytes.set(data,a.at);a.at+=data.length;a.index++;
   if(m.last){if(a.at!==a.bytes.length)throw new Error('Offline Moon asset incomplete');a.resolve(a.bytes);offlineParts.delete(m.name);}
  }catch(error){if(a)a.reject(error);self.postMessage({kind:'boot-error',error:String(error.message??error)});}
 }else if(m.kind==='render'){serial++;latest=m;enginePromise?.then(engine=>engine.cancel?.()).catch(()=>{});pump();}
 else if(m.kind==='cancel'){serial++;latest=null;enginePromise?.then(engine=>engine.cancel?.()).catch(()=>{});}
};
self.addEventListener('unhandledrejection',e=>{self.postMessage({kind:'boot-error',error:String(e.reason)});});
