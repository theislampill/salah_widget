'use strict';
// R0041 (issue 143): the preview-host clear route (contract section 11.10). SalahRealSky.invalidate hands the sky to
// the atmospheric preview; within 1.5 s the refined sky composes again (.real-sky-composed, which hides the SVG Moon)
// and composes the device-resolution disc for its own frame. SalahSkyPreview.clear then used to hide that disc, so the
// slot showed bare sky and stars until the refined sky's next compose (Chromium real DPR 2: 48 of 72 clears on main).
// This drives the REAL preview host (real-sky/native-preview-host.mjs) against the REAL runtime-owned presenter handle
// (moon/src/moon-native.mjs, through the unmodified rig of moon/tests/host.test.cjs) and asserts the slot IN THE SAME
// TASK as clear(). RED on the pre-change sources: set R41_PC_PREVIEW_SOURCE and SALAH_MOON_SOURCE_DIR to them.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'..'),moonTests=path.join(root,'moon/tests');
const hostTest=fs.readFileSync(path.join(moonTests,'host.test.cjs'),'utf8');
const a=hostTest.indexOf('function rig('),b=hostTest.indexOf('\n}\n',a)+3;
const rig=new Function('require','__dirname','process','fs','vm','path','crypto','const src=process.env.SALAH_MOON_SOURCE_DIR||path.join(__dirname,"../src");'+hostTest.slice(a,b)+';return rig;')(require,moonTests,process,fs,vm,path,crypto);
const previewSource=fs.readFileSync(process.env.R41_PC_PREVIEW_SOURCE||path.join(root,'real-sky/native-preview-host.mjs'),'utf8')
 .replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview');

// One page: the Moon runtime with an accepted refined record, a stand-in for moon-detail.mjs's canvas state (visible,
// skyOwner, renders: the fields its state getter reports), and the preview host sharing the same window.
function page({composed=true,paused=false}={}){
 const r=rig();r.workers[0].emit({kind:'ready'});r.workers[0].emit(r.response());
 const inner=r.detail,st={visible:false,skyOwner:null,renders:0,frame:null};
 inner.clear=function(){st.visible=false;st.frame=null;this.available=false;};
 inner.compose=frame=>{st.visible=true;st.skyOwner=frame.preview?'atmospheric-preview':'refined-sky';st.renders++;st.frame=frame;};
 Object.defineProperty(inner,'state',{get:()=>({...st})});
 const classes=new Set(['moon-ready',...(composed?['real-sky-composed']:[])]);
 const card={prepend(){},style:{setProperty(){},removeProperty(){}},classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)}};
 const canvas=()=>({style:{},setAttribute(){},getContext:()=>({putImageData(){},drawImage(){},getImageData:()=>({data:new Uint8ClampedArray(4)})}),remove(){}});
 const sky={paused,sceneIdentity:'A',lat:24.47,lon:39.61,generation:1,utcMs:1000,timeScale:1};
 r.w.SalahNativeSkyHost={reconcileClouds:()=>({}),cloudsCurrent:()=>true,capture:()=>({...sky})};
 class Publication{publish(){}cancel(){}dispose(){}get pending(){return false;}}
 const s={window:r.w,document:{querySelector:q=>q==='.c'?card:null,createElement:canvas},performance:{now:()=>0},requestAnimationFrame:()=>1,cancelAnimationFrame(){},structuredClone,Uint8ClampedArray,ImageData:class{},
  nativeResultCurrent:()=>true,nativeDiscMask:()=>null,renderNativeBackgroundPreview(){throw Error('not reached while composed');},NativeForegroundCapture:class{},NativeSolarMaskPublication:Publication,
  nativeForegroundRows:()=>530,encodeNativeFrame:()=>new Uint8ClampedArray(4),nativeCloudDisplayFrame:x=>x,NativeStarPreview:class{},joinNativeStarPreview:x=>x,nativeStarPreviewRegion:x=>x};
 vm.createContext(s);vm.runInContext(previewSource+'\nstartNativeSkyPreview();',s);
 return {r,st,classes,sky,rt:r.w.SalahMoonRuntime,handle:r.w.SalahMoonDetail,preview:r.w.SalahSkyPreview};
}
const identity=rt=>{const o=rt.observe();return {current:o.current,wouldPresent:o.wouldPresent,generation:o.state.generation,epoch:o.state.epoch,accepted:JSON.stringify(o.state.accepted),source:o.state.visibleSource};};

test('R41-PC-1: a preview clear leaves the refined sky\'s disc presented in the same task, same record and identity',()=>{
 const p=page();
 // The refined sky composes its frame through the presenter handle (native-host.mjs compose).
 const refinedFrame={raster:{}};p.handle.compose(refinedFrame,()=>{});p.classes.add('real-sky-preview-ready');
 assert.equal(p.st.visible,true);assert.equal(p.st.skyOwner,'refined-sky');
 const before=identity(p.rt),renders=p.st.renders;
 assert.equal(before.current,true);assert.equal(before.source,'refined-terrain');
 p.preview.clear('r41-pc');
 // The preview's own withdrawal happened...
 assert.equal(p.classes.has('real-sky-preview-ready'),false);assert.equal(p.preview.state.status,'pending');
 // ...and the slot still holds a presented Moon in this task: the detail the refined sky composed, unchanged.
 assert.equal(p.classes.has('real-sky-composed'),true,'the SVG Moon stays hidden under the refined sky, so the detail is the only Moon');
 assert.equal(p.st.visible,true,'empty Moon slot: the preview hid the refined sky\'s disc');
 assert.equal(p.st.frame,refinedFrame);assert.equal(p.st.renders,renders,'nothing re-rendered or substituted');
 assert.deepEqual(identity(p.rt),before,'record, epoch, generation and source unchanged by the preview clear');
});

test('R41-PC-2: the preview still withdraws the disc it composed itself',()=>{
 const p=page({composed:false});p.handle.compose({preview:true,raster:{},current:()=>true},()=>{});p.classes.add('real-sky-preview-ready');
 assert.equal(p.st.skyOwner,'atmospheric-preview');
 p.preview.clear('r41-pc');
 assert.equal(p.st.visible,false);assert.equal(p.classes.has('real-sky-preview-ready'),false,'the SVG Moon takes the slot as before');
});

test('R41-PC-3: a genuine Moon withdrawal still hides a refined-sky disc (nothing invalid is retained)',()=>{
 const p=page();p.handle.compose({raster:{}},()=>{});
 p.r.state.sceneIdentity='B';p.rt.request();          // identity change: the runtime clears and falls back
 assert.equal(p.st.visible,false);assert.equal(identity(p.rt).current,false);
 const q=page();q.handle.compose({raster:{}},()=>{});
 assert.equal(q.handle.clearFor('refined-sky'),true);assert.equal(q.st.visible,false,'the owner itself may withdraw');
});

test('R41-PC-4: awaiting input (no current sky owner) keeps the full withdrawal',()=>{
 const p=page();p.handle.compose({raster:{}},()=>{});p.classes.delete('real-sky-composed');p.sky.paused=true;
 p.preview.update();
 assert.equal(p.st.visible,false);assert.equal(p.classes.has('real-sky-awaiting-input'),true);
});

test('R41-PC-5: no await or deferral was added on the clear path',()=>{
 const src=fs.readFileSync(path.join(root,'real-sky/native-preview-host.mjs'),'utf8');
 const clear=src.slice(src.indexOf(' function clear('),src.indexOf('\n',src.indexOf(' function clear(')));
 assert.doesNotMatch(clear,/await|Promise|setTimeout|requestAnimationFrame/);
 const nat=fs.readFileSync(path.join(root,'moon/src/moon-native.mjs'),'utf8'),k=nat.indexOf('clearFor(owner){');
 assert.ok(k>0);assert.doesNotMatch(nat.slice(k,nat.indexOf('},',k)),/await|Promise|setTimeout|requestAnimationFrame|poll\(/);
});
