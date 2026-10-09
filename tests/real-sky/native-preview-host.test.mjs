import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Exercise the actual host with deterministic stage costs. Foreground capture
// is presentation work, while the astronomical job must keep its original UTC.
const source=fs.readFileSync(new URL('../../real-sky/native-preview-host.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');
function host({foregroundMs=25,skyMs=30,timeScale=600,parseMs=0,starMs=0,detailMs=0,throwDetail=false}={}){
 let now=0,raf=null,cancelled=0,starRenders=0;const classes=new Set(),draws=[],rgba=new Uint8ClampedArray(325*530*4);for(let i=3;i<rgba.length;i+=4)rgba[i]=255;
 const ctx={putImageData(){draws.push(now);},drawImage(){},getImageData:()=>({data:rgba})};
 const canvas=()=>({style:{},setAttribute(){},getContext:()=>ctx,remove(){}});
 const card={prepend(){},style:{setProperty(){},removeProperty(){}},classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)}};
 const s={window:{},document:{querySelector:q=>q==='.c'?card:null,createElement:canvas},Uint8ClampedArray,Float64Array,structuredClone,performance:{now:()=>now},requestAnimationFrame:fn=>(raf=fn,1),cancelAnimationFrame(){cancelled++;},ImageData:class{constructor(data,w,h){this.data=data;this.width=w;this.height=h;}},
  nativeResultCurrent:(j,c)=>j.generation===c.generation&&Math.abs(c.utcMs-j.utcMs)<=30000,
  NativeForegroundCapture:class{bottom(){return 0;}capture(){now+=foregroundMs;return {cloudRGBA:new Uint8ClampedArray(rgba.length),moonRGBA:new Uint8ClampedArray(rgba.length),native:{}};}prepareSolarMask(){return 'test-mask';}},
  nativeForegroundRows:()=>530,nativeCloudDisplayFrame:x=>x,encodeNativeFrame:()=>rgba,
  NativeStarPreview:class{static async create(pack){if(pack.wait)await pack.wait;return new this(pack);}constructor(pack){now+=parseMs;if(pack.invalid)throw new Error('Invalid catalogue');this.identity={sha256:pack.sha256};}render(){now+=starMs;starRenders++;return {diagnostics:this.identity};}},
  joinNativeStarPreview:(next,bytes,stars)=>({...next,rgba:bytes,raster:{...next.raster,starPreview:stars.diagnostics}}),nativeStarPreviewRegion:()=>rgba,
  renderNativeBackgroundPreview(c){now+=Array.isArray(skyMs)?skyMs.shift()??30:skyMs;return {job:{utcMs:c.utcMs,generation:c.generation},utcMs:c.utcMs,quality:'test',raster:{linear:new Float64Array(3),width:325,height:530,physicalState:{sun:{altDeg:30}}}};}};
 s.window.SalahNativeSkyHost={capture:()=>({utcMs:now*timeScale,generation:1,timeScale,sceneIdentity:'A',lat:1,lon:2})};
 s.window.SalahMoonDetail={clear(){},compose(){now+=Array.isArray(detailMs)?detailMs.shift()??0:detailMs;if(Array.isArray(throwDetail)?throwDetail.shift():throwDetail)throw Error('controlled detail readback failure');}};
 vm.createContext(s);vm.runInContext(source+'\nstartNativeSkyPreview();',s);
 return {s,classes,draws,get now(){return now;},get starRenders(){return starRenders;},get cancelled(){return cancelled;},get state(){return s.window.SalahSkyPreview.state;},tick(t,actual){now=actual;raf(t);},present(t,actual){now=actual;s.window.SalahSkyPreview.present(t);}};
}
test('foreground preparation cannot consume the new astronomical calculation age budget',()=>{
 const h=host();assert.equal(h.state.status,'ready');assert.ok(h.classes.has('real-sky-preview-ready'));
 assert.equal(h.state.utcMs,25*600,'job is captured after presentation-only preparation');
 assert.ok(h.now*600-h.state.utcMs<=30000);assert.ok(h.draws.length>0);
});

test('a near-expiry preview cannot be published without consumer callback headroom',()=>{
 const h=host({foregroundMs:0,skyMs:[49.9,30],timeScale:600});
 assert.equal(h.state.status,'ready','a bounded fresh retry must recover from one transient overrun');
 assert.ok(h.state.utcMs>0,'recovery must use a new actual accepted UTC, never post-date the old calculation');
 assert.ok((h.now+.2)*600-h.state.utcMs<=30000,'observed0.2ms publication-to-consumer tail cannot expire the visible sky');
 assert.equal(h.state.publicationReserveMs,5,'wall-time headroom narrows admission; it does not increase the30s limit');
 assert.equal(h.state.deadlineRetries,1);
});

test('deadline recovery is bounded and cannot turn a persistently slow calculation into a current frame',()=>{
 const h=host({foregroundMs:0,skyMs:55,timeScale:600});
 assert.equal(h.state.status,'pending');assert.ok(!h.classes.has('real-sky-preview-ready'));
 assert.equal(h.now,110,'at most one retry per presentation opportunity');
});

test('a throwing detail compositor cannot bypass publication headroom through retained-frame recovery',()=>{
 const h=host({foregroundMs:0,skyMs:30,detailMs:[19.9,0],throwDetail:[true,false],timeScale:600});
 assert.equal(h.state.status,'ready');assert.ok(h.state.utcMs>0);
 assert.ok((h.now+.2)*600-h.state.utcMs<=30000);assert.equal(h.state.deadlineRetries,1);
});

test('a failed detail readback retains a sky only while its original owner has publication headroom',()=>{
 const h=host({foregroundMs:0,skyMs:30,detailMs:1,throwDetail:true,timeScale:600});
 assert.equal(h.state.status,'ready');assert.equal(h.state.retained,true);
 assert.equal(h.state.utcMs,0);assert.equal(h.state.deadlineRetries,0);
 assert.equal(h.state.publication.ageMs,h.now*600-h.state.utcMs,'retention receipt names the pixels still visible');
 assert.ok((h.now+5)*600-h.state.utcMs<=30000);
});
test('a delayed rAF timestamp never skips the accepted-clock expiry check',()=>{
 const h=host({foregroundMs:0,skyMs:30});const original=h.state.utcMs;
 // The browser rAF timestamp names the frame start; other callbacks can have
 // consumed real time before this callback. The accepted clock is authoritative.
 h.tick(40,51);assert.equal(h.state.status,'ready');assert.ok(h.state.utcMs>original);
 assert.ok(h.now*600-h.state.utcMs<=30000);
});
test('native presentation handoff stops the duplicate loop and timestamps after native painting',()=>{
 const h=host({foregroundMs:2,skyMs:20});assert.equal(typeof h.s.window.SalahSkyPreview.present,'function');
 h.present(32,50);assert.equal(h.cancelled,1);assert.equal(h.state.utcMs,52*600);
 assert.ok(h.now*600-h.state.utcMs<=30000);h.present(66,90);assert.equal(h.cancelled,1,'one permanent loop handoff');
 assert.equal(h.state.utcMs,92*600);
});

test('catalogue admission preserves the current atmosphere and defers first stellar paint to a separate native turn',async()=>{
 const h=host({foregroundMs:20,skyMs:30,timeScale:1,parseMs:125,starMs:41});
 const before=h.now,draws=h.draws.length,utc=h.state.utcMs;
 await h.s.window.SalahSkyPreview.admitCatalogue({sha256:'pinned'});
 assert.equal(h.now-before,125,'Parsing must not synchronously include sky, stars, foreground and detail publication');
 assert.equal(h.starRenders,0);assert.equal(h.draws.length,draws);
 assert.equal(h.state.status,'ready');assert.equal(h.state.utcMs,utc);assert.ok(h.classes.has('real-sky-preview-ready'));
 h.present(h.now+1,h.now+1);
 assert.equal(h.starRenders,1);assert.equal(h.state.catalogue.sha256,'pinned');assert.ok(h.draws.length>draws);
 await h.s.window.SalahSkyPreview.admitCatalogue(null);
 assert.equal(h.state.catalogue.sha256,'pinned','Diagnostics still identify the displayed frame until atomic replacement');
 h.present(h.now+1,h.now+1);assert.equal(h.state.catalogue,null);assert.equal(h.starRenders,1);
});

test('invalid catalogue cannot become the displayed identity or defer currentness validation',async()=>{
 const h=host({foregroundMs:0,skyMs:10,timeScale:1});
 await h.s.window.SalahSkyPreview.admitCatalogue({invalid:true});assert.match(h.state.catalogueError,/Invalid catalogue/);
 h.present(20,20);assert.equal(h.state.catalogue,null);assert.equal(h.starRenders,0);
 h.present(31000,31000);assert.ok(h.state.utcMs>30000,'Deferred admission does not retain an expired original sky');
});

test('late catalogue hash completion cannot resurrect a revoked asset admission',async()=>{
 const h=host({foregroundMs:0,skyMs:1,timeScale:1});let release;
 const late=h.s.window.SalahSkyPreview.admitCatalogue({sha256:'old',wait:new Promise(r=>release=r)});
 await h.s.window.SalahSkyPreview.admitCatalogue(null);release();await late;
 h.present(10,10);assert.equal(h.state.catalogue,null);assert.equal(h.starRenders,0);
});
