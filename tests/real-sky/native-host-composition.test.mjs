import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {encodeNativeDisplay,encodeNativeDisplayInto,sameNativeCloudAlpha} from '../../real-sky/native-host.mjs';
import {nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation,nativeSolarTransmission,NativeSolarMaskPublication} from '../../real-sky/native-composition.mjs';
import {NativeSkyLifecycle} from '../../real-sky/native-lifecycle.mjs';

// Execute the authored host's actual composition body, with real pixel operators.
// Only browser capture and framebuffer transport are replaced by owned arrays.
const source=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
const compose=source.slice(source.indexOf(' function compose(){'),source.indexOf('\n function accept('));
test('new worker acceptance cannot extend the original displayed job while its replacement mask is pending',()=>{
 const animate=source.split('\n').find(line=>line.startsWith(' function animate('));
 const state={utcMs:31000,paused:false,reducedMotion:false},clears=[];
 const s={disposed:false,frame:{},job:{utcMs:28000},paintedJob:{utcMs:0},lastCompose:0,solarPublication:{pending:{}},snapshot:()=>state,
  lifecycle:{current:(job,current)=>Math.abs(current.utcMs-job.utcMs)<=30000},clear(reason){clears.push(reason);s.frame=null;},failure(e){throw e;},requestAnimationFrame:()=>1};
 vm.createContext(s);vm.runInContext(compose+'\n'+animate+'\nanimate(31000)',s);
 assert.equal(clears.length,1,'the 31000 ms displayed job must be withdrawn despite a 3000 ms accepted successor');
});
function fixture(rows,{invalidAt=null,expire=false,maskError=false,deferMask=false,publication=null}={}){
 const width=325,height=530,n=width*height*3,sky=new Float64Array(n),stars=new Float64Array(n),diffuse=new Float64Array(n),linear=new Float64Array(n);
 for(let i=0;i<n;i++){sky[i]=.0001+(i%103)/10000;stars[i]=i%79===0?.02:0;diffuse[i]=(i%7)/100000;linear[i]=sky[i]+stars[i]+diffuse[i];}
 const raster={width,height,linear,skyBackgroundLinear:sky,stellarLinear:stars,diffusePhysicalLinear:diffuse,effectiveExposure:24};
 if(invalidAt!==null)linear[invalidAt]=NaN;
 const cloudRGBA=new Uint8ClampedArray(width*rows*4),moonRGBA=new Uint8ClampedArray(cloudRGBA.length),mask=new Float64Array(width*rows).fill(1);
 for(let p=0;p<mask.length;p++){
  const i=p*4;cloudRGBA.set([63,85,109,p%19===0?88:0],i);
  if(p%127===0){moonRGBA.set([101,120,135,255],i);mask[p]=0;}
 }
 const capture={cloudRGBA,moonRGBA,native:{}},base=nativeCalendarRegion(raster,mask,rows),joined=nativeForeground(base,{...capture,atmosphereLinear:sky.subarray(0,base.length),exposure:24});
 const expected=new Uint8ClampedArray(width*height*4);
 if(invalidAt===null){expected.set(encodeNativeFrame(linear,24));expected.set(encodeNativeFrame(joined.linear,24));}
 const pixels=new Uint8ClampedArray(expected.length).fill(29),draws=[],encoded=[],destinations=[],errors=[],maskCalls=[],pendingMasks=[];let checks=0;
 const s={frame:{raster},disposed:false,job:{observer:{utcMs:1},native:{identity:'accepted'}},pendingJob:null,paintedFrame:null,paintedJob:null,previousPresentation:null,previousSolarMask:null,previousMoonBottom:0,lastCompose:0,
  snapshot:()=>({}),lifecycle:{current:()=>!expire||++checks===1},clear:reason=>errors.push(reason),failure:e=>errors.push(String(e)),performance:{now:()=>1},window:{},
  foreground:{bottom:()=>rows-2,capture:()=>({...capture,cloudRGBA:cloudRGBA.slice(),moonRGBA:moonRGBA.slice()}),prepareSolarMask(rgba,count){maskCalls.push({rgba:rgba.slice(),rows:count,bytes:nativeSolarTransmission(rgba)});if(maskError)throw Error('invalid solar mask');return publication?'url("data:image/png;base64,mask-'+maskCalls.length+'")':'mask-'+maskCalls.length;}},calendarGeometry:()=>({key:'geometry',mask:()=>mask}),
  nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation,sameNativeCloudAlpha,
  solarPublication:publication??{pending:null,publish(mask,commit){if(deferMask){this.pending=commit;pendingMasks.push(commit);}else commit();},cancel(){this.pending=null;}},
  encodeNativeDisplay(a,E){encoded.push(a.length);return encodeNativeDisplay(a,E);},
  encodeNativeDisplayInto(a,E,b,offset){encoded.push(a.length);destinations.push({bytes:b,offset:offset??0,length:a.length});return encodeNativeDisplayInto(a,E,b,offset);},
  ImageData:class{constructor(data,w,h){assert.equal(data.length,w*h*4);this.data=data;this.width=w;this.height=h;}},Uint8ClampedArray,
  ctx:{putImageData(image,x,y){draws.push([image.width,image.height,x,y]);pixels.set(image.data,y*width*4);}},
  card:{style:{setProperty(){}},classList:{add(){}}},canvas:{style:{}},status:{last:{},presentationDraws:0,presentationSkips:0}};
 vm.createContext(s);vm.runInContext(compose+'\ncompose();',s);
 return {s,pixels,expected,encoded,destinations,draws,errors,capture,maskCalls,finishMask(){s.solarPublication.pending=null;return pendingMasks.shift()();},rerun(){vm.runInContext('compose();',s);}};
}
for(const rows of [183,284,530])test('refined host encodes each final pixel once and preserves composed bytes: '+rows,()=>{
 const h=fixture(rows);assert.deepEqual(h.errors,[]);assert.deepEqual(h.pixels,h.expected);
 assert.equal(h.encoded.reduce((a,b)=>a+b,0),325*530*3,'overwritten raw prefix must not be encoded twice');
 assert.equal(h.destinations.length,2);
 assert.equal(h.destinations[0].bytes,h.destinations[1].bytes,'prefix and tail share exactly one private destination');
 assert.equal(h.destinations[1].offset,325*rows*4);
 assert.equal(h.destinations[0].bytes.length,325*530*4);
 assert.equal(h.draws.length,1,'prepare the complete joined update before one publication');
 h.rerun();assert.equal(h.draws.length,1,'identical foreground retains the presentation guard');
 h.capture.cloudRGBA[3]=200;h.rerun();assert.equal(h.draws.at(-1)[1],rows,'same-frame foreground change remains regional');
 assert.equal(h.destinations.length,3);assert.equal(h.destinations[2].bytes.length,325*rows*4);
});
test('refined host never publishes an expired or failed prepared update',()=>{
 for(const options of [{expire:true},{maskError:true}]){const h=fixture(183,options);assert.equal(h.draws.length,0);assert(h.errors.length);assert(h.pixels.every(v=>v===29));}
});
test('skipped raw prefix and encoded tail retain nonfinite rejection',()=>{
 for(const invalidAt of [0,325*529*3]){const h=fixture(183,{invalidAt});assert.equal(h.draws.length,0);assert(h.errors.length);}
});

test('new accepted frame with exact cloud alpha reuses only published solar mask',()=>{
 const h=fixture(183);assert.equal(h.maskCalls.length,1);const expected=h.pixels.slice(),prior=h.s.frame;
 h.s.frame={...prior};h.rerun();assert.equal(h.maskCalls.length,1);assert.equal(h.draws.length,2);assert.deepEqual(h.pixels,expected);
 h.capture.cloudRGBA[0]++;h.s.frame={...prior};h.rerun();assert.equal(h.maskCalls.length,1,'RGB changes do not alter solar obstruction');
 h.capture.cloudRGBA[3]++;h.s.frame={...prior};h.rerun();assert.equal(h.maskCalls.length,2,'alpha change must regenerate');
 assert.notDeepEqual(h.maskCalls[0].bytes,h.maskCalls[1].bytes);
 h.s.previousPresentation.rows++;h.s.frame={...prior};h.rerun();assert.equal(h.maskCalls.length,3,'row support change must regenerate');
 h.s.previousPresentation=null;h.s.previousSolarMask=null;h.s.frame={...prior};h.rerun();assert.equal(h.maskCalls.length,4,'withdrawn state cannot reuse mask');
});
test('failed publication leaves solar reuse state unpublished',()=>{
 const h=fixture(183,{expire:true});assert.equal(h.maskCalls.length,1);assert.equal(h.s.previousSolarMask,null);assert.equal(h.s.previousPresentation,null);assert.equal(h.draws.length,0);
});
test('refined publication keeps matching immutable foreground private until mask readiness',()=>{
 const h=fixture(183,{deferMask:true});assert.equal(h.draws.length,0);h.capture.cloudRGBA.fill(255);
 h.finishMask();assert.deepEqual(h.pixels,h.expected,'decode completion cannot recapture a different cloud frame');assert.equal(h.draws.length,1);
});
test('late mask readiness cannot publish over a newer accepted frame, changed target or disposal',()=>{
 for(const changed of ['frame','job','expired','disposed']){
  const h=fixture(183,{deferMask:true});
  if(changed==='frame')h.s.frame={...h.s.frame};
  if(changed==='job')h.s.job={...h.s.job};
  if(changed==='expired')h.s.lifecycle.current=()=>false;
  if(changed==='disposed')h.s.disposed=true;
  h.finishMask();assert.equal(h.draws.length,0,changed);assert(h.pixels.every(v=>v===29));
 }
});
test('solar mask comparator validates types, lengths and every alpha boundary',()=>{
 const a=new Uint8ClampedArray(325*183*4),b=a.slice();assert(sameNativeCloudAlpha(a,b));
 for(const i of [3,325*4-1,a.length-1]){b[i]=1;assert(!sameNativeCloudAlpha(a,b));b[i]=0;}
 for(const b of [new Uint8Array(a.length),new Uint8ClampedArray(a.length-1),new Uint8ClampedArray(a.length+4),null])assert(!sameNativeCloudAlpha(a,b));
});
test('actual host clear withdraws the mask cache along with the previous presentation',()=>{
 const h=fixture(183),s=h.s;
 s.card.classList.contains=()=>false;s.card.classList.remove=()=>{};s.card.style.removeProperty=()=>{};
 s.ctx.clearRect=()=>{};s.publish=()=>{};
 const clear=source.slice(source.indexOf(' function clear('),source.indexOf(' // Identity/age fences'));
 vm.runInContext(clear+"\nclear('source-control');",s);
 assert.equal(s.previousSolarMask,null);assert.equal(s.previousPresentation,null);assert.equal(s.frame,null);assert.equal(s.job,null);
});
test('ignoring the final alpha difference is killed by the same exact mask discriminator',()=>{
 const fragment=source.slice(source.indexOf('export function sameNativeCloudAlpha'),source.indexOf('/** DOM ownership adapter'));
 const mutant=fragment.replace('export function','function').replace('if(a[i]!==b[i])return false;',';');
 assert.notEqual(fragment.replace('export function','function'),mutant);
 const c={Uint8ClampedArray};vm.createContext(c);vm.runInContext(mutant,c);
 const a=new Uint8ClampedArray(325*183*4),b=a.slice();b[b.length-1]=1;
 assert(!sameNativeCloudAlpha(a,b));assert.throws(()=>assert.equal(c.sameNativeCloudAlpha(a,b),false),assert.AssertionError);
});

for(const terminal of ['clear','dispose'])test('real refined publication retains coherent pixels and releases owned masks on '+terminal,async()=>{
 const images=[];
 class Image {constructor(){images.push(this);}decode(){return new Promise((resolve,reject)=>{this.resolve=resolve;this.reject=reject;});}}
 const publication=new NativeSolarMaskPublication(()=>new Image()),h=fixture(183,{publication}),s=h.s;
 const flush=async()=>{for(let i=0;i<4;i++)await Promise.resolve();};
 const roots=()=>new Set([publication.displayed,publication.decoded,publication.pending].filter(Boolean));
 assert.equal(h.draws.length,0);assert.equal(roots().size,1);
 images[0].resolve();await flush();const displayed=publication.displayed,original=h.pixels.slice();
 assert.equal(h.draws.length,1);assert.deepEqual(h.pixels,h.expected);assert.equal(roots().size,1);

 h.capture.cloudRGBA[3]++;s.frame={...s.frame};h.rerun();
 s.frame={...s.frame}; // The decoded B resource cannot authorize this new frame.
 images[1].resolve();await flush();
 assert.equal(publication.displayed,displayed);assert.notEqual(publication.decoded,displayed);
 assert.equal(roots().size,2);assert.equal(h.draws.length,1);assert.deepEqual(h.pixels,original);
 h.capture.cloudRGBA[3]++;h.rerun();assert.equal(roots().size,3);assert.equal(h.draws.length,1);
 const pending=publication.pending;assert.equal(pending.image,images[2]);

 s.card.classList.contains=()=>true;s.card.classList.remove=()=>{};s.card.style.removeProperty=()=>{};
 s.ctx.clearRect=()=>{};s.publish=()=>{};
 const clear=source.slice(source.indexOf(' function clear('),source.indexOf(' // Identity/age fences'));
 vm.runInContext(clear,s);
 if(terminal==='dispose'){
  // Execute the actual host disposal through its real lifecycle invalidation;
  // replacing that chain with only publication.dispose would miss owned jobs.
  s.lifecycle=new NativeSkyLifecycle({capture:()=>({}),execute:async()=>{},onInvalidate:reason=>s.clear(reason)});
  Object.assign(s,{request(){},timer:1,animationId:2,clearInterval(){},cancelAnimationFrame(){},document:{removeEventListener(){}},visibility(){},client:{dispose(){}},workerUrl:null,badge:{remove(){}}});
  s.canvas.remove=()=>{};
  const exported=source.split('\n').find(line=>line.startsWith(' window.SalahRealSky='));
  assert(exported);vm.runInContext(exported+'\nwindow.SalahRealSky.dispose();',s);
  assert.equal(s.lifecycle.state.disposed,true);assert.equal(publication.disposed,true);assert.equal(roots().size,0);
 }else{
  vm.runInContext("clear('controlled target withdrawal');",s);assert.equal(roots().size,1,'Only the completed decoded cache remains after cancellation');
 }
 assert.equal(pending.image.src,'');assert.equal(publication.pending,null);assert.equal(publication.displayed,null);
 for(const field of ['pendingJob','paintedFrame','paintedJob','frame','job','previousPresentation','previousSolarMask'])assert.equal(s[field],null,field);
 images[2].resolve();await flush();assert.equal(h.draws.length,1,'Late completion cannot restore the withdrawn Sun or framebuffer');
 assert.deepEqual(h.errors,[]);
 // These assertions cover direct owner roots. They do not certify native
 // decoder/Promise/GC lifetime or the browser's whole heap.
});
