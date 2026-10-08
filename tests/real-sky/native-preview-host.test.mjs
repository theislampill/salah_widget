import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Exercise the actual host with deterministic stage costs. Foreground capture
// is presentation work, while the astronomical job must keep its original UTC.
const source=fs.readFileSync(new URL('../../real-sky/native-preview-host.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');
function host({foregroundMs=25,skyMs=30}={}){
 let now=0,raf=null,cancelled=0;const classes=new Set(),draws=[],rgba=new Uint8ClampedArray(325*530*4);for(let i=3;i<rgba.length;i+=4)rgba[i]=255;
 const ctx={putImageData(){draws.push(now);},drawImage(){},getImageData:()=>({data:rgba})};
 const canvas=()=>({style:{},setAttribute(){},getContext:()=>ctx,remove(){}});
 const card={prepend(){},style:{setProperty(){},removeProperty(){}},classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)}};
 const s={window:{},document:{querySelector:q=>q==='.c'?card:null,createElement:canvas},Uint8ClampedArray,Float64Array,structuredClone,performance:{now:()=>now},requestAnimationFrame:fn=>(raf=fn,1),cancelAnimationFrame(){cancelled++;},ImageData:class{constructor(data,w,h){this.data=data;this.width=w;this.height=h;}},
  nativeResultCurrent:(j,c)=>j.generation===c.generation&&Math.abs(c.utcMs-j.utcMs)<=30000,
  NativeForegroundCapture:class{bottom(){return 0;}capture(){now+=foregroundMs;return {cloudRGBA:new Uint8ClampedArray(rgba.length),moonRGBA:new Uint8ClampedArray(rgba.length),native:{}};}prepareSolarMask(){return 'test-mask';}},
  nativeForegroundRows:()=>530,nativeCloudDisplayFrame:x=>x,encodeNativeFrame:()=>rgba,
  renderNativeBackgroundPreview(c){now+=skyMs;return {job:{utcMs:c.utcMs,generation:c.generation},utcMs:c.utcMs,quality:'test',raster:{linear:new Float64Array(3),width:325,height:530,physicalState:{sun:{altDeg:30}}}};}};
 s.window.SalahNativeSkyHost={capture:()=>({utcMs:now*600,generation:1,timeScale:600,sceneIdentity:'A',lat:1,lon:2})};
 vm.createContext(s);vm.runInContext(source+'\nstartNativeSkyPreview();',s);
 return {s,classes,draws,get now(){return now;},get cancelled(){return cancelled;},get state(){return s.window.SalahSkyPreview.state;},tick(t,actual){now=actual;raf(t);},present(t,actual){now=actual;s.window.SalahSkyPreview.present(t);}};
}
test('foreground preparation cannot consume the new astronomical calculation age budget',()=>{
 const h=host();assert.equal(h.state.status,'ready');assert.ok(h.classes.has('real-sky-preview-ready'));
 assert.equal(h.state.utcMs,25*600,'job is captured after presentation-only preparation');
 assert.ok(h.now*600-h.state.utcMs<=30000);assert.ok(h.draws.length>0);
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
