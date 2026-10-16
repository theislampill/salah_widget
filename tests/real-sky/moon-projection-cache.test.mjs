// Executes both actual startMoonDetail modules. Only DOM/canvas transport is
// simulated; surface sampling, atmospheric join, cloud transfer and encoding
// execute their source owners. No native/performance qualification is claimed.
import fs from 'node:fs';import vm from 'node:vm';import crypto from 'node:crypto';import assert from 'node:assert/strict';import {pathToFileURL,fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../..',import.meta.url));
const {nativeCloudChannel,validateNativeRGBA}=await import(pathToFileURL(root+'/real-sky/native-cloud-transfer.mjs'));
const {encodeNativeDisplay}=await import(pathToFileURL(root+'/real-sky/native-host.mjs'));
const original=fs.readFileSync(new URL('../fixtures/moon-detail-pre-cache.mjs',import.meta.url),'utf8');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function surface(level=1,calendar=true){
 const size=32,linear=new Float64Array(size*size*3),coverage=new Float64Array(size*size),calendarLinear=new Float64Array(linear.length);
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){const i=y*size+x,a=Math.max(0,Math.min(1,15-Math.hypot(x-15.5,y-15.5)));coverage[i]=a;
  for(let k=0;k<3;k++){linear[3*i+k]=a*level*(.03+.5*(x+2*y+k)/100);calendarLinear[3*i+k]=a*(.005+.03*(x+y+k)/65);}}
 return {identity:'same-material-label',size,extent:1,linear,coverage,...(calendar?{calendarLinear}:{})};
}
function frame(level=1,exposure=12){
 const width=16,height=20,N=width*height*3;const field=(s)=>Float64Array.from({length:N},(_,i)=>s*(1+(i%31)/31));
 return {preview:false,current:()=>true,raster:{width,height,effectiveExposure:exposure,skyBackgroundLinear:field(.005*level),stellarLinear:field(.002*level),diffusePhysicalLinear:field(.001*level)}};
}
function instance(source){
 const s={x:240.25,y:42.5,w:62,h:62,dpr:1,opacity:1,up:1,rect:{left:0,top:0,width:325,height:530},cloud:null,adopted:null,calls:0,publishes:[],canvases:[]};
 const classes=new Set(['moon-ready','real-sky-composed','real-sky-preview-ready']);const sky={after(cv){cv.previousSibling=sky;cv.isConnected=true;}};
 const card={clientLeft:0,clientTop:0,offsetWidth:325,offsetHeight:530,classList:{contains:x=>classes.has(x)},getBoundingClientRect:()=>({left:0,top:0,width:325,height:530}),querySelector:()=>sky,prepend(cv){cv.isConnected=true;}};
 const photo={getScreenCTM:()=>({a:1,b:0,c:0,d:1,e:0,f:0}),getAttribute:n=>({x:s.x,y:s.y,width:s.w,height:s.h})[n]};
 const group={kind:'group'},features={kind:'features'},disc={kind:'disc',classList:{contains:()=>true}},base={getBoundingClientRect:()=>s.rect},cloud={kind:'cloud',getBoundingClientRect:()=>({...s.rect,bottom:s.rect.top+s.rect.height})};
 const nodes={'.c':card,'.mphoto':photo,'.moon':group,'.mfeatures':features,'.moon-mask-disc':disc,'.real-sky-canvas':base,'.real-sky-preview':base};
 const document={querySelector:n=>n==='.cloudcanvas'?(s.cloud?cloud:null):nodes[n],createElement(tag){assert.equal(tag,'canvas');const cv={width:0,height:0,style:{},setAttribute(){},remove(){this.isConnected=false;},getContext(){return ctx;}};
  const ctx={resetTransform(){},clearRect(){},drawImage(){},createLinearGradient(){return {addColorStop(){}};},fillRect(){},getImageData(x,y,w,h){const data=new Uint8ClampedArray(w*h*4);if(s.cloud)for(let i=0;i<w*h;i++)data.set(s.cloud,4*i);return {data};},putImageData(im){s.publishes.push({w:im.width,h:im.height,bytes:Buffer.from(im.data),style:cv.style});}};s.canvases.push(cv);return cv;}};
 const context={document,window:{SalahMoonRuntime:{surface:()=>s.adopted,get presentationUp(){return s.up;}}},getComputedStyle:n=>({opacity:n===group?s.opacity:1,filter:'none'}),performance,Float64Array,Uint8Array,Uint8ClampedArray,ImageData:class{constructor(data,width,height){Object.assign(this,{data,width,height});}},nativeCloudChannel,validateNativeRGBA,__count:()=>s.calls++,get devicePixelRatio(){return s.dpr;}};
 const instrumented=source.replace('function boxSurface(p,x0,y0,x1,y1){','function boxSurface(p,x0,y0,x1,y1){__count();');assert.notEqual(instrumented,source);
 const api=vm.runInNewContext(instrumented+'\nstartMoonDetail();',context);const adopt=v=>{s.adopted=v;api.adopt(v);};
 const compose=f=>{const before=s.calls,p=s.publishes.length;api.compose(f,encodeNativeDisplay);return {samples:s.calls-before,publishes:s.publishes.length-p,visible:api.state.visible,hash:s.publishes.length?sha(s.publishes.at(-1).bytes):null,pixels:s.publishes.at(-1)?.w*s.publishes.at(-1)?.h};};
 return {s,api,adopt,compose};
}
assert.equal(sha(original),'3cfa1498918706adf21a5f8462f27f9919bed9402f179b03ae3e932500c5cba0');
const candidate=fs.readFileSync(root+'/moon/src/moon-detail.mjs','utf8');
const a=instance(original),b=instance(candidate),records=[];let priorHash;
function run(name,f,{changed=false,reuse=false,rebuild=false}={}){
 const old=a.compose(f),next=b.compose(f);assert.deepEqual({hash:next.hash,publishes:next.publishes,visible:next.visible},{hash:old.hash,publishes:old.publishes,visible:old.visible},name+' full encoded output/publication differs');
 if(changed)assert.notEqual(next.hash,priorHash,name+' must respond to current input');
 if(reuse){assert(old.samples>0,name+' old code did not execute sampler');assert.equal(next.samples,0,name+' repeats unchanged material projection');}
 if(rebuild)assert(next.samples>0,name+' failed to invalidate projection');
 records.push({name,old,next});priorHash=next.hash;
}
function set(k,v){a.s[k]=v;b.s[k]=v;}
function adopt(v){a.adopt(v);b.adopt(v);}
adopt(surface());run('cold',frame(),{rebuild:true});
run('same projection/new current atmosphere',frame(2),{changed:true,reuse:true});
run('current exposure',frame(2,30),{changed:true,reuse:true});
set('opacity',.4);run('live calendar opacity',frame(2,30),{changed:true,reuse:true});
set('cloud',[80,100,130,120]);run('live cloud transfer',frame(2,30),{changed:true,reuse:true});
set('rect',{left:.3,top:.7,width:320,height:525});run('current base sky projection',frame(2,30),{changed:true,reuse:true});
set('cloud',null);set('opacity',1);
for(const up of [0,.375,1]){set('up',up);run('presentation up '+up,frame(),{rebuild:true});}
for(const [k,v]of [['x',240.6],['y',42.7],['w',63.2],['h',61.8],['dpr',2],['dpr',1]]){set(k,v);run('geometry '+k+' '+v,frame(),{rebuild:true});}
adopt(surface(.5));run('same identity changed adoption',frame(),{changed:true,rebuild:true});
adopt(surface(.8,false));run('calendar absent',frame(),{changed:true,rebuild:true});
for(const x of [120.3,240.6]){set('x',x);run('A B A single entry '+x,frame(),{rebuild:true});}
a.api.clear();b.api.clear();run('clear rebuild',frame(),{rebuild:true});
let stale=frame();stale.preview=true;stale.current=()=>false;run('stale preview publication rejected',stale);
assert.equal(b.api.state.visible,false);run('after stale clear',frame(),{rebuild:true});
const same=frame();run('same frame first call',same);run('same frame same cloud skip',same);assert.equal(records.at(-1).next.publishes,0);
// Surface-derived alpha still distinguishes transparent outside and opaque body.
const bytes=b.s.publishes.at(-1).bytes,alphas=[];for(let i=3;i<bytes.length;i+=4)alphas.push(bytes[i]);assert(alphas.includes(0)&&alphas.includes(255));
// Bad adoption must fail closed without allowing a mixed old/new prefix cache.
const bad=surface();bad.calendarLinear[0]=NaN;assert.throws(()=>b.adopt(bad));assert.equal(b.api.state.visible,false);assert.equal(b.api.available,false);b.compose(frame());assert.equal(b.api.state.visible,false);
b.adopt(surface());b.compose(frame());b.api.dispose();assert.equal(b.api.available,false);const disposed=b.compose(frame());assert.equal(disposed.publishes,0);assert.equal(disposed.visible,false);
console.log(JSON.stringify({status:'PASS_SOURCE_CONTROLS_ONLY',originalSha256:sha(original),candidateSha256:sha(candidate),records,retentionBytesPerPixel:33,maximumObservedPixels:Math.max(...records.map(r=>r.next.pixels||0)),limitations:'DOM/canvas transport fixture. No native V5 visual, temporal, cost or product acceptance.'},null,2));
