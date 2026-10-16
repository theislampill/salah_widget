import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {encodeNativeDisplay,encodeNativeDisplayInto,sameNativeCloudAlpha} from '../../real-sky/native-host.mjs';
import {nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation,nativeSolarTransmission} from '../../real-sky/native-composition.mjs';

// Execute the authored host's actual composition body, with real pixel operators.
// Only browser capture and framebuffer transport are replaced by owned arrays.
const source=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
const compose=source.slice(source.indexOf(' function compose(){'),source.indexOf('\n function accept('));
function fixture(rows,{invalidAt=null,expire=false,maskError=false}={}){
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
 const pixels=new Uint8ClampedArray(expected.length).fill(29),draws=[],encoded=[],destinations=[],errors=[],maskCalls=[];let checks=0;
 const s={frame:{raster},disposed:false,job:{observer:{utcMs:1},native:{identity:'accepted'}},paintedFrame:null,paintedJob:null,previousPresentation:null,previousSolarMask:null,previousMoonBottom:0,lastCompose:0,
  snapshot:()=>({}),lifecycle:{current:()=>!expire||++checks===1},clear:reason=>errors.push(reason),failure:e=>errors.push(String(e)),performance:{now:()=>1},window:{},
  foreground:{bottom:()=>rows-2,capture:()=>({...capture,cloudRGBA:cloudRGBA.slice(),moonRGBA:moonRGBA.slice()}),prepareSolarMask(rgba,count){maskCalls.push({rgba:rgba.slice(),rows:count,bytes:nativeSolarTransmission(rgba)});if(maskError)throw Error('invalid solar mask');return 'mask-'+maskCalls.length;}},calendarGeometry:()=>({key:'geometry',mask:()=>mask}),
  nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation,sameNativeCloudAlpha,
  encodeNativeDisplay(a,E){encoded.push(a.length);return encodeNativeDisplay(a,E);},
  encodeNativeDisplayInto(a,E,b,offset){encoded.push(a.length);destinations.push({bytes:b,offset:offset??0,length:a.length});return encodeNativeDisplayInto(a,E,b,offset);},
  ImageData:class{constructor(data,w,h){assert.equal(data.length,w*h*4);this.data=data;this.width=w;this.height=h;}},Uint8ClampedArray,
  ctx:{putImageData(image,x,y){draws.push([image.width,image.height,x,y]);pixels.set(image.data,y*width*4);}},
  card:{style:{setProperty(){}},classList:{add(){}}},canvas:{style:{}},status:{last:{},presentationDraws:0,presentationSkips:0}};
 vm.createContext(s);vm.runInContext(compose+'\ncompose();',s);
 return {s,pixels,expected,encoded,destinations,draws,errors,capture,maskCalls,rerun(){vm.runInContext('compose();',s);}};
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
