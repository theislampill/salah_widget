'use strict';
// R0036 (issue 103) I-D2 / ES36-03: the Moon runtime's diagnostic observation never adopts, syncs or publishes.
// The accepted host.test.cjs rig is reused unchanged (compiled from its own source, its tests not run), so the
// worker, host, detail and clock doubles are the reviewed ones. SALAH_MOON_SOURCE_DIR selects another moon/src.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const hostPath=path.join(__dirname,'host.test.cjs'),hostText=fs.readFileSync(hostPath,'utf8');
const start=hostText.indexOf('function rig('),end=hostText.indexOf('\ntest(',start);assert.ok(start>0&&end>start,'rig source boundary');
const m=new Module(hostPath,module);m.filename=hostPath;m.paths=Module._nodeModulePaths(__dirname);
m._compile(hostText.slice(0,hostText.indexOf('\n',hostText.indexOf("const src=")))+'\n'+hostText.slice(start,end)+'\nmodule.exports={rig};',hostPath);
const {rig}=m.exports;
// The accepted L94 setup: a valid preview is admitted while its immediate presentation is deferred.
function deferredPreview(){
  const r=rig();r.workers[0].emit({kind:'ready'});
  const preview=r.response('preview'),capture=r.w.SalahMoonHost.capture;let reads=0;
  r.w.SalahMoonHost.capture=()=>{const s=capture();return ++reads===2?{...s,paused:true}:s;};
  r.workers[0].emit(preview);r.w.SalahMoonHost.capture=capture;
  assert.equal(r.published,0);return r;
}

test('R36-30 observe() on a waiting preview reports it without adopting, publishing or enabling detail',()=>{
  const r=deferredPreview(),api=r.w.SalahMoonRuntime;
  for(let i=0;i<50;i++){
    const o=api.observe();
    assert.equal(o.accepted,false);assert.equal(o.waitingPreview,true);assert.equal(o.current,false);assert.equal(o.wouldPresent,true);
    assert.equal(o.detailAvailable,false);assert.equal(o.surface,null);
    assert.equal(o.state.visibleSource,'awaiting-terrain');assert.equal(o.state.current,false);
  }
  assert.equal(r.published,0,'an observation published a texture');assert.equal(r.detail.available,false,'an observation adopted detail');
  assert.equal(api.presentable,true,'R0033 presence predicate agrees');
  // Production reads keep read-time adoption (host.test.cjs L94 semantics): the next state read adopts once.
  assert.equal(api.state.visibleSource,'terrain-preview');assert.equal(r.published,1);
  const after=api.observe();assert.equal(after.current,true);assert.equal(after.accepted,true);assert.equal(after.waitingPreview,false);
  assert.ok(after.surface,'a presented surface returns its backing canvas');assert.equal(after.detailAvailable,true);
  assert.equal(r.published,1,'observing a presented surface does not re-publish');
});

test('R36-31 observe() reads no lunar layout without a candidate surface and reports a disposed runtime as not presentable',()=>{
  const r=rig(),api=r.w.SalahMoonRuntime,layout=r.layoutReads;
  const o=api.observe();assert.equal(o.current,false);assert.equal(o.wouldPresent,false);assert.equal(o.surface,null);
  assert.equal(r.layoutReads,layout,'empty observation forced lunar layout');
  api.dispose();const d=api.observe();assert.equal(d.wouldPresent,false);assert.equal(d.state.status,'disposed');
});

test('R36-32 a stale waiting preview is neither current nor would-present, and observation leaves it queued',()=>{
  const r=deferredPreview(),api=r.w.SalahMoonRuntime;r.state.generation++;r.state.sceneIdentity='B';
  const o=api.observe();assert.equal(o.waitingPreview,true);assert.equal(o.wouldPresent,false);assert.equal(o.current,false);
  assert.equal(r.published,0);
});
