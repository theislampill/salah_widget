'use strict';
// Current scientific/calendar boundary and opacity faults. No terrain or browser.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const {load}=require(path.join(root,'tests/r001d-harness.cjs'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const detail=fs.readFileSync(path.join(root,'moon/src/moon-detail.mjs'),'utf8');
const extract=s=>Function(s+'\nreturn {joinLunarPixel};')().joinLunarPixel;
const healthy=extract(detail),wrong=extract(detail.replace('direct[k]*(1-a)','direct[k]*(1-a*opacity)'));
assert.equal(detail.split('direct[k]*(1-a)').length,2,'real join mutation matches exactly once');
let passed=0;const test=(name,f)=>{f();passed++;console.log('PASS '+name);};
(async()=>{
 const {nativeJob,nativeResultCurrent}=await import('file:///'+root+'/real-sky/native-contract.mjs');
 const {physicalSkyState}=await import('file:///'+root+'/real-sky/core/src/sky-state.mjs');
 const h=load();h.run('render()'); // Generated entry already executes the real native-host hooks.
 const before=h.run('SalahNativeSkyHost.capture(false)'),job=nativeJob(before,true),astronomy=physicalSkyState(job.observer);
 test('actual accepted host never promotes calendar phase/altitude to physical astronomical state',()=>{
  h.run('SIM.moon="0.01";SIM.moonAlt="-10";renderMoon();render()');const after=h.run('SalahNativeSkyHost.capture(false)');
  assert.deepEqual(nativeJob(after,true),job);assert.deepEqual(physicalSkyState(nativeJob(after,true).observer),astronomy);
  assert.equal(h.run('qaState().moonTruth.lunarLight.eligible'),false);assert.equal(h.run('qaState().moonTruth.lunarLight.beam'),0);
  assert.equal(+h.select('.c').style.getPropertyValue('--mhalo'),0);assert.equal(+h.select('.mglow').style.getPropertyValue('--mgo'),0);
  assert.equal(+h.select('.c').style.getPropertyValue('--moonocc'),1,'calendar occlusion survives native zero');
 });
 test('late physical source cannot remain current after accepted UTC/target changes',()=>{
  assert.equal(nativeResultCurrent(job,before),true);assert.equal(nativeResultCurrent(job,{...before,utcMs:before.utcMs+30001}),false);
  assert.equal(nativeResultCurrent(job,{...before,generation:before.generation+1}),false);assert.equal(nativeResultCurrent(job,{...before,lon:before.lon+.01}),false);
 });
 test('real local Moon join blocks direct starlight independent of calendar fade with outside positive',()=>{
  for(const opacity of [0,.25,.521,1]){
   const spec={gas:[.03,.05,.08],direct:[100,100,100],premult:[0,0,0],coverage:1,opacity,cloud:[0,0,0,0],exposure:12};
   assert.deepEqual(healthy(spec),spec.gas);assert.deepEqual(healthy({...spec,coverage:0}),[100.03,100.05,100.08]);
  }
 });
 test('restoring fade-scaled star leakage is detected by identical inside/outside probe',()=>{
  const spec={gas:[.03,.05,.08],direct:[100,100,100],premult:[0,0,0],coverage:1,opacity:.521,cloud:[0,0,0,0],exposure:12};
  assert.deepEqual(healthy(spec),spec.gas);assert.notDeepEqual(wrong(spec),spec.gas);assert.deepEqual(wrong({...spec,coverage:0}),healthy({...spec,coverage:0}));
 });
 console.log(JSON.stringify({sourceIndexSha256:sha(fs.readFileSync(path.join(root,'index.html'))),detailSha256:sha(Buffer.from(detail)),fixtureSha256:sha(fs.readFileSync(__filename)),passed,failed:0,limits:'Actual whole-source accepted host/native paint plus numerical astronomical and local join controls. Not a native hostile-star screenshot or phase campaign.'}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
