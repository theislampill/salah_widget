'use strict';
// R0036 (issue 103) machine DIAG-READ: a diagnostic read observes without acting (docs/state-contracts/R0036.md).
// Whole inline runtime in the r001d VM harness; storage, DOM, canvas and clock are recorded doubles. No browser,
// no provider: the harness fetch denies every non-prayer host. R0036_ROOT selects another tree's product files
// (the RED run at the baseline); by default this tree's generated index.html and authored sources are read.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {load}=require('./r001d-harness.cjs');
const ROOT=process.env.R0036_ROOT||path.resolve(__dirname,'..');
const read=f=>fs.readFileSync(path.join(ROOT,f),'utf8');
const SITE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1';
const boot=(extra='&simTime=22:00')=>{const h=load({source:read('index.html'),hash:SITE+extra});h.run('render()');return h;};

// Recorder over the harness storage double: every write and every removal, by key.
function recordStorage(h){
  const ops=[],ls=h.ctx.localStorage,set=ls.setItem.bind(ls),remove=ls.removeItem.bind(ls);
  ls.setItem=(k,v)=>{ops.push(['set',k]);return set(k,v);};ls.removeItem=k=>{ops.push(['remove',k]);return remove(k);};
  return ops;
}
// Every observable DOM fact the doubles hold: style properties, attributes, classes, dataset, text, canvas puts/exports.
function domTrace(h){
  const out={};
  for(const [sel,el] of h.elements){
    const props={};for(const k of ['--stars','--mw','--airglow','--starblur'])props[k]=el.style.getPropertyValue(k);
    out[sel]={text:el.textContent,html:el._html,dataset:{...el.dataset},href:el.getAttribute('href'),title:el.getAttribute('title'),aria:el.getAttribute('aria-label'),
      ready:el.classList.contains('moon-ready'),display:el.style.display,props,puts:el.ctx.puts||0,exports:el.exports||0};
  }
  return JSON.stringify(out);
}
// A spy over a product function binding, restored by the caller's harness lifetime (each test owns its harness).
function spy(h,name){h.ctx.__r36calls=h.ctx.__r36calls||{};h.ctx.__r36calls[name]=0;
  h.run(`{const original=${name};${name}=function(...a){__r36calls.${name}++;return original.apply(this,a);};}`);return ()=>h.ctx.__r36calls[name];}

// ES36-02 / ES36-06(a) / N3: no diagnostic entry point writes storage or reaches cloud withdrawal or the header paint.
test('R36-01 I-D1/I-D4: 100 qaState() reads, the CP9 wrapper and the debugMotion overlay write no storage and reach no withdrawal or header paint',()=>{
  const h=boot();
  const withdraw=spy(h,'withdrawCloudState'),paint=spy(h,'paintWeatherHeader'),reconcile=spy(h,'reconcileCloudPublication');
  const ops=recordStorage(h);
  for(let i=0;i<100;i++)h.run('qaState()');
  assert.ok('moonRenderer' in h.run('qaState()'),'the generated runtime carries the CP9 wrapper over qaState');
  h.select('.dbgmotion');for(let i=0;i<5;i++)h.run("updateMotionDbg(60,30,document.querySelector('.c'))");
  assert.deepEqual(ops,[],'a diagnostic read performed storage operations: '+JSON.stringify(ops.slice(0,4)));
  assert.equal(withdraw(),0,'withdrawCloudState reached from a diagnostic read');
  assert.equal(paint(),0,'paintWeatherHeader reached from a diagnostic read');
  assert.equal(reconcile(),0,'reconcileCloudPublication reached from a diagnostic read');
});

// ES36-02 quota case and G2 = (a): the key keeps non-writing semantics plus its basis and the last real write outcome.
test('R36-02 G2(a): with every write throwing QuotaExceededError, readable storage is reported readable with the last write outcome',()=>{
  const h=boot(),ls=h.ctx.localStorage;
  ls.setItem=()=>{const e=new Error('quota');e.name='QuotaExceededError';throw e;};
  const c=h.run('qaState().config');
  assert.equal(c.storageAvailable,true,'reads still work, so the non-writing key is true');
  assert.equal(c.storage.readable,true);assert.equal(c.storage.reason,null);
  assert.match(c.storage.basis,/read-only access check.*no write probe/);
  assert.equal(c.storage.lastWrite,null);assert.equal(c.storage.lastWriteState,'not-attempted-in-this-document');
  // A blocked store (getItem throws SecurityError) is reported unreadable with its reason, still without a write.
  ls.getItem=()=>{const e=new Error('blocked');e.name='SecurityError';throw e;};
  const blocked=h.run('qaState().config');
  assert.equal(blocked.storageAvailable,false);assert.equal(blocked.storage.reason,'SecurityError');
  // After a real settings write failure (R0011's owner records it), the readout reports that outcome.
  h.run('_publishPersistence("save",{ok:false,error:"quota"})');
  const after=h.run('qaState().config');
  assert.deepEqual({...after.storage.lastWrite},{operation:'save',status:'session-only',error:'quota'});
  assert.equal(after.storage.lastWriteState,'attempted');
});

// ES36-05 I-D3: memo bindings are left exactly as found, and polled/unpolled product traces are identical.
test('R36-03 I-D3: qaState leaves the weather memos untouched and polling does not change the product trace',()=>{
  const h=boot();
  h.run('_wxDecisionCache=null;_wxTargetCache=null;_weatherInformationCache=null;_wxDowngrade="sentinel"');
  h.run('qaState()');
  assert.equal(h.run('_wxDecisionCache'),null,'qaState filled the decision memo');
  assert.equal(h.run('_wxTargetCache'),null,'qaState filled the target memo');
  assert.equal(h.run('_weatherInformationCache'),null,'qaState filled the information memo');
  assert.equal(h.run('_wxDowngrade'),'sentinel','qaState rewrote the downgrade side channel');
  // Differential: identical frame programme with and without a read before every frame.
  const run=poll=>{const x=boot();const ops=recordStorage(x);
    for(let i=0;i<12;i++){if(poll){x.run('qaState()');x.run('qaState()');}x.clock.now+=1000;x.clock.wall+=1000;x.run('render()');}
    return {dom:domTrace(x),ops:JSON.stringify(ops),render:JSON.stringify(x.run('_lastRender')),header:JSON.stringify(x.run('_lastWeatherHeader')),
      moon:JSON.stringify(x.run('_lastMoonPaint')),clouds:JSON.stringify(x.run('cloudPublicationReceipt()'))};};
  const quiet=run(false),polled=run(true);
  for(const k of Object.keys(quiet))assert.equal(polled[k],quiet[k],'product trace differs under polling: '+k);
});

// ES36-03 (VM): the native qaState and the CP9 wrapper read the non-adopting observation only.
test('R36-04 I-D2: qaState().moonTruth and the CP9 wrapper never read the adopting surface()/state/detailEnabled getters',()=>{
  const h=boot();
  h.run(`window.__r36moon={adopting:0,observe:0};window.SalahMoonRuntime={
    surface(){__r36moon.adopting++;return null;},get state(){__r36moon.adopting++;return {status:'ready'};},get detailEnabled(){__r36moon.adopting++;return false;},
    get presentable(){return false;},observe(){__r36moon.observe++;return {accepted:false,waitingPreview:true,current:false,wouldPresent:true,detailAvailable:false,surface:null,
      state:{status:'refining',quality:'pending',visibleSource:'awaiting-terrain',current:false,accepted:null,backend:'b',legacyFallback:false,errors:[]}};}};`);
  const t=h.run('qaState().moonTruth');
  const wrapped=h.run('qaState()');                                         // the generated runtime's CP9 wrapper
  const counts=h.run('({...__r36moon})');
  assert.equal(counts.adopting,0,'a diagnostic read used an adopting Moon getter');
  assert.ok(counts.observe>=2,'the observation is the diagnostic source');
  assert.deepEqual({...t.observation},{accepted:false,waitingPreview:true,current:false,wouldPresent:true,detailAvailable:false});
  assert.equal(t.surface.status,'refining');assert.equal(t.surface.visibleSource,'awaiting-terrain');
  assert.equal(wrapped.moonRenderer.status,'refining');
});

// N3 / ES36-03: the smoke instrument polls the observation, not the adopting getters.
// Executed, not grepped: the smoke stage's own Moon-read lines run against a runtime double that counts reads.
test('R36-05 I-D2: tests/smoke.html Moon reads use observe() when the runtime has it, never the adopting getters',()=>{
  const smoke=read('tests/smoke.html'),stage=smoke.slice(smoke.indexOf('async function calendarScene('),smoke.indexOf('trace.observation=s;'));
  assert.ok(stage.length>0);
  const lines=stage.split('\n').filter(l=>/^\s*const /.test(l)&&/api=ww\.SalahMoonRuntime|const runtime=observed|backing=|after=/.test(l)).join('\n');
  assert.ok(/api=ww\.SalahMoonRuntime/.test(lines),'smoke Moon-read lines located');
  const reads={adopting:0,observe:0},canvas={id:'backing'};
  const api={get state(){reads.adopting++;return {current:true};},surface(){reads.adopting++;return canvas;},get detailEnabled(){reads.adopting++;return false;},
    observe(){reads.observe++;return {state:{current:true},surface:canvas};}};
  const fr={getBoundingClientRect:()=>({})},doc={querySelector:()=>null};
  const ww={qaState:()=>({moonTruth:{surface:{}}}),SalahMoonRuntime:api,SalahMoonHost:{capture:()=>({})},SalahMoonDetail:{state:{}}};
  const out=new Function('ww','doc','fr',lines+'\nreturn {runtime,backing,after};')(ww,doc,fr);
  assert.equal(reads.adopting,0,'smoke used an adopting getter on a runtime that has observe()');
  assert.equal(reads.observe,2,'before and after observations');assert.equal(out.backing,canvas);assert.equal(out.after.current,true);
});

// ES36-09 N2: every effective override is reported; a present but inert parameter is not "simulated".
test('R36-06 N2: cache.simulated is true for each effective override and lists it; real-time and inert parameters are not simulated',()=>{
  const cases=[['',false,[]],['&simWx=2',true,['simWx']],['&simWx=63&simCloud=40',true,['simWx','simCloud']],['&simTime=12:30',true,['simTime']],
    ['&simMoon=0.5',true,['simMoon']],['&simMoonAlt=20',true,['simMoonAlt']],['&simMoonAlt=20&simMoonH=42',true,['simMoonAlt','simMoonH']],
    ['&debugOptic=halo',true,['debugOptic']],['&debugOptic=lunarhalo',true,['debugOptic']],['&timeScale=60',true,['timeScale']],
    ['&simMoonH=42',false,[],['simMoonH']],['&simCloud=40',false,[],['simCloud']],['&debugOptic=bogus',false,[],['debugOptic']]];
  for(const [extra,simulated,overrides,inert=[]] of cases){
    const h=load({source:read('index.html'),hash:SITE+extra});const c=h.run('qaState().cache');
    assert.equal(c.simulated,simulated,'simulated for "'+extra+'"');
    assert.deepEqual([...(c.overrides||[])],overrides,'overrides for "'+extra+'"');
    assert.deepEqual([...(c.inertOverrides||[])],inert,'inert for "'+extra+'"');
  }
});

// Truthful Moon outcome record (moonTruth, MOON-003 diagnostic row): a recorded construction failure (R0033 DG-1 = B)
// is reported as that failure, never as "awaiting current terrain"; without the record the awaiting reason is unchanged.
test('R36-08 moonTruth reports a recorded Moon construction failure instead of "awaiting"',()=>{
  const h=boot();h.run('window.SalahMoonRuntime=null;');
  const awaiting=h.run('qaState().moonTruth');
  assert.equal(awaiting.reason,'awaiting current terrain; no legacy substitution');assert.equal(awaiting.surface.status,'pending');
  h.run('window.SalahMoonConstructionError="injected construction fault";');
  const t=h.run('qaState().moonTruth');
  assert.equal(t.surface.status,'construction-failed');assert.equal(t.constructionError,'injected construction fault');
  assert.match(t.reason,/construction failed.*no disc and no moonlight/);assert.equal(t.displayMode,'surface-unavailable');
});

// ES36-06(b), amendment R0036-A1: the capture-time reconcile is a deliberate R000B production step. This positive pin is
// green at the baseline by design (the one exempt test); a mutant deleting the call must fail it (ES36-06(c)).
test('R36-07 A1 pin: NativeForegroundCapture.capture() reconciles clouds exactly once, before the cloud canvas is read',async()=>{
  const url=require('node:url').pathToFileURL(path.join(ROOT,'real-sky/native-composition.mjs')).href+'?r36='+Date.now();
  const events=[],ctx2d={resetTransform(){},clearRect(){},setTransform(){},fillRect(){},createLinearGradient:()=>({addColorStop(){}}),
    drawImage(src){events.push(src&&src.__cloud?'draw-cloud':'draw');},getImageData:(x,y,w,h)=>({data:new Uint8ClampedArray(w*h*4)})};
  const canvas=()=>({width:325,height:530,getContext:()=>ctx2d,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})});
  const cloud={...canvas(),__cloud:true};
  const saved={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle};
  try{
    globalThis.document={createElement:canvas,querySelector:s=>{if(s==='.cloudcanvas'){events.push('select-cloud');return cloud;}return null;}};
    globalThis.window={SalahNativeSkyHost:{reconcileClouds(){events.push('reconcile');return {state:'eligible-published'};},lunarSurface:()=>null},SalahMoonRuntime:null};
    globalThis.getComputedStyle=()=>({filter:'none',visibility:'visible',opacity:'1'});
    const {NativeForegroundCapture}=await import(url);
    const out=new NativeForegroundCapture(canvas()).capture(530);
    assert.equal(events.filter(e=>e==='reconcile').length,1,'exactly one reconcile per capture: '+events.join(','));
    assert.ok(events.indexOf('reconcile')<events.indexOf('select-cloud')&&events.indexOf('select-cloud')<events.indexOf('draw-cloud'),'reconcile precedes the cloud read: '+events.join(','));
    assert.deepEqual({...out.cloudAuthority},{state:'eligible-published'});
  }finally{for(const [k,v] of Object.entries(saved))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
});
