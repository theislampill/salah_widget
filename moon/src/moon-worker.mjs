


let enginePromise=null,latest=null,running=false,serial=0;const offlineParts=new Map();
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
 return MoonEngine.create({wasm,dem,colour,manifest});
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
 }else if(m.kind==='render'){serial++;latest=m;pump();}
 else if(m.kind==='cancel'){serial++;latest=null;}
};
self.addEventListener('unhandledrejection',e=>{self.postMessage({kind:'boot-error',error:String(e.reason)});});
