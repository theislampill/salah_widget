import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {NativeSolarMaskPublication} from '../../real-sky/native-composition.mjs';

// R0034 (issue 101) ISM-SKY-017 / ISM-SKY-030: the REAL preview host with
// controlled DOM, foreground and astronomy. Counts every withdrawal side effect.
// Run: node --test tests/real-sky/native-preview-lifecycle.test.mjs
const source=fs.readFileSync(new URL('../../real-sky/native-preview-host.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');

function fixture({snapshot={utcMs:0,generation:1,timeScale:1,sceneIdentity:null,lat:null,lon:null}}={}){
 let now=0,raf=null,receipt={revision:1};const classes=new Set(),n={reconcile:0,cloudsCurrent:0,detailClear:0,headLookups:0,classWrites:0,styleWrites:0,renders:0,publishes:0,putImageData:0,canvasRemove:0};
 const ctx={putImageData(){n.putImageData++;},drawImage(){},getImageData:()=>({data:new Uint8ClampedArray(325*530*4)})};
 const canvas=()=>({style:{},setAttribute(){},getContext:()=>ctx,remove(){n.canvasRemove++;}});
 const card={prepend(){},style:{setProperty(){n.styleWrites++;},removeProperty(){n.styleWrites++;}},classList:{contains:x=>classes.has(x),add:x=>{n.classWrites++;classes.add(x);},remove:x=>{n.classWrites++;classes.delete(x);}}};
 class Publication extends NativeSolarMaskPublication{constructor(){super(()=>({decode:()=>({then(resolve){resolve();}})}));}publish(...a){n.publishes++;return super.publish(...a);}}
 const detail={state:{renders:0,visible:false},clear(){n.detailClear++;this.state={...this.state,visible:false};},compose(){}};
 const s={window:{SalahMoonDetail:detail},document:{querySelector:q=>q==='.c'?card:q==='#native-first-paint'?(n.headLookups++,null):null,createElement:canvas},
  Uint8ClampedArray,Float64Array,structuredClone,performance:{now:()=>now},requestAnimationFrame:fn=>(raf=fn,1),cancelAnimationFrame(){},
  ImageData:class{constructor(data,w,h){this.data=data;this.width=w;this.height=h;}},
  nativeResultCurrent:(j,c)=>j.generation===c.generation&&Math.abs(c.utcMs-j.utcMs)<=30000,
  NativeForegroundCapture:class{bottom(){return 0;}capture(){return {cloudRGBA:new Uint8ClampedArray(325*530*4),moonRGBA:new Uint8ClampedArray(325*530*4),native:{}};}prepareSolarMask(){return 'url("data:image/png;base64,fixture")';}},
  NativeSolarMaskPublication:Publication,nativeForegroundRows:()=>530,nativeCloudDisplayFrame:x=>x,encodeNativeFrame:()=>new Uint8ClampedArray(325*530*4),
  NativeStarPreview:class{},joinNativeStarPreview:x=>x,nativeStarPreviewRegion:()=>new Uint8ClampedArray(325*530*4),
  renderNativeBackgroundPreview(c){n.renders++;return {job:{utcMs:c.utcMs,generation:c.generation},utcMs:c.utcMs,quality:'test',raster:{linear:new Float64Array(3),width:325,height:530,physicalState:{sun:{altDeg:30}}}};}};
 let snap={...snapshot};
 s.window.SalahNativeSkyHost={reconcileClouds(){n.reconcile++;return receipt;},cloudsCurrent(r){n.cloudsCurrent++;return r===undefined||r===receipt;},capture:()=>({...snap,utcMs:now})};
 vm.createContext(s);vm.runInContext(source+'\nstartNativeSkyPreview();',s);
 return {s,n,classes,detail,get preview(){return s.window.SalahSkyPreview;},set(p){snap={...snap,...p};},frames(k){for(let i=0;i<k;i++){now+=16;raf(now);}},present(k){for(let i=0;i<k;i++){now+=16;s.window.SalahSkyPreview.present(now);}},publishClouds(){receipt={revision:receipt.revision+1};}};
}

test('ES34-08 awaiting-input runs its withdrawal once over 120 frames',()=>{
 const h=fixture();
 assert.ok(h.classes.has('real-sky-awaiting-input'));
 const entry={...h.n};h.frames(120);
 assert.equal(h.n.reconcile,entry.reconcile,'no per-frame cloud reconcile');
 assert.equal(h.n.detailClear,entry.detailClear,'no per-frame Moon-detail clear');
 assert.equal(h.n.headLookups,entry.headLookups,'no per-frame first-paint lookup');
 assert.equal(h.n.classWrites,entry.classWrites,'no per-frame class write');
 assert.equal(h.n.styleWrites,entry.styleWrites,'no per-frame style write');
 assert.equal(h.n.renders,0);assert.equal(h.preview.state.status,'pending');
});

test('ES34-08 a cloud publication or Moon-detail change during awaiting-input still gets its reconcile/clear',()=>{
 const h=fixture();h.frames(5);const before={...h.n};
 h.publishClouds();h.frames(5);
 assert.equal(h.n.reconcile,before.reconcile+1,'a new cloud publication is reconciled once');
 h.detail.state={renders:1,visible:true};h.frames(5);
 assert.equal(h.n.detailClear,before.detailClear+1,'a rendered Moon detail is cleared once');
 const replacement={state:{renders:0,visible:false},clear(){h.n.detailClear++;}};h.s.window.SalahMoonDetail=replacement;h.frames(5);
 assert.equal(h.n.detailClear,before.detailClear+2,'a replaced detail owner is cleared');
 h.s.window.SalahFirstPaint={error:'late head'};h.frames(2);
 assert.equal(h.s.window.SalahFirstPaint,null,'a head appearing during awaiting-input is retired');
});

test('ES34-08 leaving awaiting-input on coordinates restores normal preview; re-entry withdraws again',()=>{
 const h=fixture();h.frames(10);
 h.set({sceneIdentity:'A',lat:1,lon:2});h.frames(1);
 assert.equal(h.preview.state.status,'ready');assert.ok(!h.classes.has('real-sky-awaiting-input'));assert.ok(h.classes.has('real-sky-preview-ready'));
 const before={...h.n};h.set({lat:null});h.frames(10);// fixture currentness ignores coordinates; the 100 ms repaint reaches update()
 assert.equal(h.preview.state.status,'pending');assert.ok(h.classes.has('real-sky-awaiting-input'));assert.ok(!h.classes.has('real-sky-preview-ready'));
 assert.equal(h.n.detailClear,before.detailClear+1,'a fresh entry runs the full withdrawal');
});

test('ES34-10 no preview work while paused: 120 present calls cause zero renders and publishes',()=>{
 const h=fixture({snapshot:{utcMs:0,generation:1,timeScale:1,sceneIdentity:'A',lat:1,lon:2}});
 assert.equal(h.preview.state.status,'ready');const before={...h.n};
 h.set({paused:true});h.present(120);
 assert.equal(h.n.renders,before.renders);assert.equal(h.n.publishes,before.publishes);assert.equal(h.n.putImageData,before.putImageData);
 assert.equal(h.preview.state.status,'pending');
 assert.equal(h.n.detailClear,before.detailClear+1,'paused withdrawal ran once');
});

test('ES34-09 dispose releases its registry slot only while registered, is idempotent and never touches a successor',()=>{
 const h=fixture({snapshot:{utcMs:0,generation:1,timeScale:1,sceneIdentity:'A',lat:1,lon:2}});
 const a=h.preview;assert.ok(h.classes.has('real-sky-preview-ready'));
 a.dispose();
 assert.equal(h.s.window.SalahSkyPreview,undefined,'healthy dispose releases the slot');
 assert.ok(!h.classes.has('real-sky-preview-ready'));assert.equal(h.n.canvasRemove,1);
 const n={...h.n};assert.doesNotThrow(()=>a.dispose());assert.deepEqual(h.n,n,'second dispose is a no-op');
 // Successor: a disposed predecessor must not release the successor's slot or class.
 const g=fixture({snapshot:{utcMs:0,generation:1,timeScale:1,sceneIdentity:'A',lat:1,lon:2}});
 const old=g.preview,successor={};g.s.window.SalahSkyPreview=successor;
 old.dispose();
 assert.equal(g.s.window.SalahSkyPreview,successor);assert.ok(g.classes.has('real-sky-preview-ready'),'successor class untouched');
});

test('R0034 review: no consumer reads SalahFirstPaint.error; a refused first paint (record undefined) boots the preview normally',()=>{
 const files=['src/native/index.html','real-sky/native-preview-host.mjs','real-sky/native-host.mjs','real-sky/native-host-hooks.js',...fs.readdirSync(new URL('../../moon/src/',import.meta.url)).filter(f=>/\.(mjs|js)$/.test(f)).map(f=>'moon/src/'+f)];
 for(const f of files){const t=fs.readFileSync(new URL('../../'+f,import.meta.url),'utf8');assert.doesNotMatch(t,/SalahFirstPaint\??\.error/,f);}
 const h=fixture({snapshot:{utcMs:0,generation:1,timeScale:1,sceneIdentity:'A',lat:1,lon:2}});
 assert.equal(h.preview.state.status,'ready','the preview publishes without a first-paint record');assert.equal(h.s.window.SalahFirstPaint??null,null);
});
