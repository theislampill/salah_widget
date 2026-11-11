import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const nativeURL=name=>new URL('real-sky/'+name,process.env.SALAH_WITHDRAWAL_NATIVE_ROOT?pathToFileURL(process.env.SALAH_WITHDRAWAL_NATIVE_ROOT+'/'):new URL('../../',import.meta.url));
const {NativeForegroundCapture,NativeSolarMaskPublication,nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation}=await import(nativeURL('native-composition.mjs'));
const {encodeNativeDisplay,encodeNativeDisplayInto,sameNativeCloudAlpha}=await import(nativeURL('native-host.mjs'));
const {encodeNativeFrame}=await import(nativeURL('native-encoding.mjs'));
const {nativeJob,nativeResultCurrent}=await import(nativeURL('native-contract.mjs'));
const {nativeCloudDisplayFrame}=await import(nativeURL('native-cloud-transfer.mjs'));
const require=createRequire(import.meta.url),{fixture,withdrawn}=require('../weather-no-timetable-fixture.cjs');
const hooks=fs.readFileSync(nativeURL('native-host-hooks.js'),'utf8');
const refinedSource=fs.readFileSync(nativeURL('native-host.mjs'),'utf8');
const refined=refinedSource.slice(refinedSource.indexOf(' function compositionFailed('),refinedSource.indexOf('\n function accept('));
const refinedClear=refinedSource.slice(refinedSource.indexOf(' function clear('),refinedSource.indexOf(' // Identity/age fences'));
const refinedFailure=refinedSource.slice(refinedSource.indexOf(' function failure('),refinedSource.indexOf('\n client=new ReferenceRenderClient'));
const preview=fs.readFileSync(nativeURL('native-preview-host.mjs'),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');

// Real admitted native owner, real hooks, real capture and publication owners.
// Canvas readback is a retained-alpha sentinel, not browser pixel qualification.
async function boundary(run,{freshnessRoom=false}={}){
 const h=await fixture(freshnessRoom?{fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?{ok:true,json:async()=>payload({time:'2026-09-08T23:46'})}:new Promise(()=>{})}:{});
 if(freshnessRoom){h.at(951000);h.run('render()');assert(h.read().selected);}
 h.run(hooks);const host=h.ctx.window.SalahNativeSkyHost,card=h.select('.c'),draws=[],images=[],errors=[];
 card.prepend=()=>{};const classes=card.classList;
 const makeCanvas=()=>{let alpha=0;const c={width:325,height:530,style:{},setAttribute(){},remove(){},getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
  const ctx={resetTransform(){},clearRect(){alpha=0;},createLinearGradient:()=>({addColorStop(){}}),fillRect(){},setTransform(){},
   drawImage(source){if(source===h.select('.cloudcanvas'))alpha=h.raster.currentFills?192:0;},
   getImageData(x,y,width,height){const data=new Uint8ClampedArray(width*height*4);data.set([80,90,100,alpha]);return {data};},
   putImageData(image){if(c===canvas||c.className==='real-sky-preview')draws.push({canvas:c,bytes:image.data.slice()});}};
  c.getContext=()=>ctx;c.toDataURL=()=> 'data:image/png;base64,cloud-'+alpha;return c;};
 const document={createElement:makeCanvas,querySelector:q=>q==='.c'?card:q==='.cloudcanvas'?h.select(q):null};
 const saved={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle,ImageData:globalThis.ImageData};
 const ImageData=class{constructor(data,width,height){assert.equal(data.length,width*height*4);this.data=data;this.width=width;this.height=height;}};
 const window={SalahNativeSkyHost:host,SalahMoonDetail:{clear(){},compose(){}},...{}};
 Object.assign(globalThis,{document,window,ImageData,getComputedStyle:()=>({filter:'none',visibility:'hidden',opacity:'1'})});
 class Publication extends NativeSolarMaskPublication{constructor(){super(()=>{const image={decode(){return new Promise((resolve,reject)=>{image.resolve=resolve;image.reject=reject;});}};images.push(image);return image;});}}
 const canvas=makeCanvas(),capture=new NativeForegroundCapture(canvas),flush=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
 const replace=async()=>{const before=h.run('weather');h.at(freshnessRoom?951000:900000);h.run('render()');await h.refresh({time:'2026-09-09T00:00'});assert.notEqual(h.run('weather'),before,'real acquisition must replace its previous record');assert.equal(h.read().model,false);};
 // A synchronous already-admitted replacement models a source publication
 // between capture and the final sink without granting freshness or authority.
 h.ctx.__r000bReplacement=h.payload().current;
 const replaceDuringDetail=({withoutModel=true}={})=>{
  const prior=h.run('weather');h.run('weather=admitWeatherRecord(__r000bReplacement,{units,zone:tz,retrievedAt:Date.now(),target:currentWeatherTarget()});');
  assert.notEqual(h.run('weather'),prior,'post-detail boundary admits a different real record');
  if(withoutModel)h.run('today=null;');
  assert.equal(!!h.run('model()'),!withoutModel,'negative boundary revokes the genuine model; healthy companion keeps it');
 };
 try{return await run({h,host,card,classes,document,window,ImageData,Publication,canvas,capture,draws,images,errors,flush,replace,replaceDuringDetail});}
 finally{for(const[key,value]of Object.entries(saved))if(value===undefined)delete globalThis[key];else globalThis[key]=value;}
}
function refinedHost(b){
 const linear=new Float64Array(325*530*3).fill(.02),frame={raster:{width:325,height:530,linear,skyBackgroundLinear:linear,stellarLinear:new Float64Array(linear.length),effectiveExposure:24}};
 const s={frame,job:nativeJob(b.host.capture(false),true),pendingJob:null,paintedFrame:null,paintedJob:null,previousPresentation:null,previousSolarMask:null,previousMoonBottom:0,lastCompose:0,disposed:false,
  foreground:b.capture,solarPublication:new b.Publication(),snapshot:()=>b.host.capture(false),lifecycle:{current:(job,state=b.host.capture(false))=>nativeResultCurrent(job,state)},
  publish(){},performance:{now:()=>b.h.clock.now},window:b.window,
  nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation,sameNativeCloudAlpha,encodeNativeDisplay,encodeNativeDisplayInto,
  calendarGeometry:()=>({key:null,mask:()=>null}),ImageData:b.ImageData,Uint8ClampedArray,ctx:b.canvas.getContext('2d'),card:b.card,canvas:b.canvas,status:{last:{},errors:b.errors,presentationDraws:0,presentationSkips:0,presentationRejections:0}};
 vm.createContext(s);vm.runInContext(refinedClear+'\n'+refined+'\n'+refinedFailure,s);s.compose();return s;
}
function previewHost(b){
 const s={window:b.window,document:b.document,Uint8ClampedArray,Float64Array,structuredClone,ImageData:b.ImageData,performance:{now:()=>b.h.clock.now},requestAnimationFrame:()=>1,cancelAnimationFrame(){},
  NativeForegroundCapture,NativeSolarMaskPublication:b.Publication,nativeForegroundRows,nativeCloudDisplayFrame,encodeNativeFrame,nativeResultCurrent,
  renderNativeBackgroundPreview(snapshot){const job=nativeJob(snapshot,true),linear=new Float64Array(325*530*3).fill(.02);return {job,utcMs:snapshot.utcMs,quality:'controlled independent numerical sky',raster:{width:325,height:530,linear,effectiveExposure:24,physicalState:{sun:{altDeg:-20}}}};}};
 vm.createContext(s);vm.runInContext(preview+'\nstartNativeSkyPreview();',s);return s.window.SalahSkyPreview;
}
const lastAlpha=owner=>owner.status?.last?.composition?.maxCloudAlpha??owner.state?.composition?.maxCloudAlpha;

test('actual foreground capture withdraws expired cloud state before reading raster when render and painter have not run',()=>boundary(async b=>{
 const first=b.capture.capture(183);assert(first.cloudRGBA[3]>0);b.h.at(900000);b.h.run('render()');b.h.at(900077);
 const cleared=b.capture.capture(183);withdrawn(b.h.read());assert.equal(cleared.cloudRGBA[3],0);assert.equal(cleared.native.maxCloudAlpha,0);
 assert.equal(cleared.native.meanCloudAlpha,0);assert.equal(cleared.native.cloudAuthority.state,'withdrawn-unavailable');
}));
test('captured authority is serializable and final-currentness read rejects expiry without repairing cloud state',()=>boundary(async b=>{
 const first=b.capture.capture(183);assert(first.cloudRGBA[3]>0);assert.equal(typeof b.host.cloudsCurrent,'function');
 assert.deepEqual(structuredClone(first.cloudAuthority),JSON.parse(JSON.stringify(first.cloudAuthority)));const before=b.h.read();b.h.at(900077);
 assert.equal(b.host.cloudsCurrent(first.cloudAuthority),false);assert.deepEqual(b.h.read().cov,before.cov);assert.equal(b.h.raster.currentFills,before.raster.currentFills);
 b.capture.capture(183);withdrawn(b.h.read());assert.equal(b.host.cloudsCurrent(first.cloudAuthority),false);
}));
for(const kind of ['refined','preview'])for(const path of ['next opportunity','decode completion'])test(kind+' rejects an old cloud capture and publishes clear successor at '+path,()=>boundary(async b=>{
 const owner=kind==='refined'?refinedHost(b):previewHost(b),job=kind==='refined'?owner.job:null;assert.equal(b.images.length,1);assert.equal(b.draws.length,0);
 await b.replace();if(job)assert(nativeResultCurrent(job,b.host.capture(false)),'identical numerical weather cannot hide record replacement');
 if(path==='next opportunity'){if(kind==='refined')owner.compose();else owner.update();}
 else{b.images[0].resolve();await b.flush();}
 assert.equal(lastAlpha(owner),0,'cleared successor must publish without awaiting obsolete cloud decode');assert(b.draws.length>0);withdrawn(b.h.read());
 const draws=b.draws.length;b.images[0].resolve();await b.flush();assert.equal(b.draws.length,draws,'obsolete completion cannot re-publish');assert.equal(b.images.length,1,'clear successor has no decode');
 assert.deepEqual(b.errors,[]);
},{freshnessRoom:true}));
for(const kind of ['refined','preview'])test(kind+' checks cloud authority again after detail composition',()=>boundary(async b=>{
 const owner=kind==='refined'?refinedHost(b):previewHost(b);let once=true;
 b.window.SalahMoonDetail.compose=()=>{if(once){once=false;b.replaceDuringDetail();}};
 b.images[0].resolve();await b.flush();assert.equal(lastAlpha(owner),0);assert(b.draws.length>0);withdrawn(b.h.read());
}));
for(const kind of ['refined','preview'])test(kind+' retains eligible consumed A through a healthy post-detail replacement',()=>boundary(async b=>{
 const owner=kind==='refined'?refinedHost(b):previewHost(b),authority=b.h.run('cloudPublicationReceipt()'),coverage=JSON.stringify(b.h.run('cloudState'));let once=true;
 b.window.SalahMoonDetail.compose=()=>{if(once){once=false;b.replaceDuringDetail({withoutModel:false});}};
 b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);assert(b.draws.length>0);
 assert.equal(b.h.run('cloudPublicationReceipt()'),authority);assert.equal(JSON.stringify(b.h.run('cloudState')),coverage);
 assert.equal(b.h.run('_cloudPublication.record===weather'),false);assert(b.host.cloudsCurrent(authority));
}));
test('same-byte refined reuse retains eligible A during a healthy replacement without an extra draw',()=>boundary(async b=>{
 const owner=refinedHost(b);b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);
 const authority=b.h.run('cloudPublicationReceipt()'),draws=b.draws.length;let once=true;
 b.window.SalahMoonDetail.compose=()=>{if(once){once=false;b.replaceDuringDetail({withoutModel:false});}};owner.compose();
 assert(lastAlpha(owner)>0);assert.equal(b.draws.length,draws);assert.equal(b.h.run('cloudPublicationReceipt()'),authority);assert(b.host.cloudsCurrent(authority));
}));
test('pending solar context is bounded and released without adding owner references to decoded cache',async()=>{
 const images=[],p=new NativeSolarMaskPublication(()=>{const image={decode:()=>new Promise(resolve=>image.resolve=resolve)};images.push(image);return image;}),context={cloudAuthority:{revision:1}};
 p.publish('url("data:image/png;base64,x")',()=>true,assert.fail,context);assert.equal(p.pendingContext,context);
 p.cancel();assert.equal(p.pendingContext,null);images[0].resolve();await Promise.resolve();assert.equal(p.decoded,null);
 p.publish('linear-gradient(#fff,#fff)',()=>true,assert.fail,{cloudAuthority:{revision:2}});assert.equal(p.pendingContext,null);
 for(const resource of [p.displayed,p.decoded])assert.deepEqual(Object.keys(resource).sort(),['image','mask']);
 p.dispose();assert.equal(p.pendingContext,null);
});

test('same-byte refined reuse still checks consumed cloud authority after detail',()=>boundary(async b=>{
 const owner=refinedHost(b);b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);const draws=b.draws.length;let once=true;
 b.window.SalahMoonDetail.compose=()=>{if(once){once=false;b.replaceDuringDetail();}};owner.compose();
 assert.equal(lastAlpha(owner),0);assert.equal(b.draws.length,draws+1);withdrawn(b.h.read());
}));
test('native failure handoff revokes the raw cloud raster before removing refined ownership',()=>boundary(async b=>{
 const owner=refinedHost(b);b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);await b.replace();
 owner.failure(Error('controlled replacement worker failure'));
 assert.equal(b.canvas.style.visibility,'hidden');assert.equal(b.classes.contains('real-sky-composed'),false);withdrawn(b.h.read());
},{freshnessRoom:true}));
for(const kind of ['refined','preview'])test(kind+' failed detail cannot retain revoked displayed cloud coverage',()=>boundary(async b=>{
 const owner=kind==='refined'?refinedHost(b):previewHost(b);b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);await b.replace();
 b.window.SalahMoonDetail.compose=()=>{throw Error('controlled detail failure after cloud revocation');};
 if(kind==='refined'){owner.compose();assert.equal(b.canvas.style.visibility,'hidden');assert.equal(b.classes.contains('real-sky-composed'),false);}
 else{owner.update();assert.equal(owner.state.status,'pending');assert.equal(b.classes.contains('real-sky-preview-ready'),false);}
 withdrawn(b.h.read());
},{freshnessRoom:true}));

test('preview direct withdrawal clears the revoked raw cloud raster before releasing its layer',()=>boundary(async b=>{
 const owner=previewHost(b);b.images[0].resolve();await b.flush();assert(lastAlpha(owner)>0);await b.replace();
 owner.clear('controlled preview handoff');assert.equal(b.classes.contains('real-sky-preview-ready'),false);withdrawn(b.h.read());
},{freshnessRoom:true}));
