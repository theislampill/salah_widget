'use strict';
// Actual original/diagnostic module bodies, with explicit bounded dependencies.
// These synthetic clocks, pixels and workers are never native qualification.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const vm=require('node:vm'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'../../..');
const source={live:fs.readFileSync(path.join(root,'tools/r0035/live_lab.mjs'),'utf8'),worker:fs.readFileSync(path.join(root,'tools/r0035/lab_worker.mjs'),'utf8')};
const prepared=spawnSync(process.env.PYTHON||'python3',['-B','-c',
  "import json,pathlib,runpy; m=runpy.run_path('tools/qa/hosted-native/r0035_stage_materialize.py'); print(json.dumps({k:m['transform'](n,pathlib.Path(n).read_bytes())[0].decode() for k,n in [('live',m['LIVE']),('worker',m['WORKER'])]}))"],
  {cwd:root,encoding:'utf8'});
assert.equal(prepared.status,0,prepared.stderr);const modified=JSON.parse(prepared.stdout);

async function moduleFor(code,context,dependencies){
  const mod=new vm.SourceTextModule(code,{context,initializeImportMeta:meta=>{meta.url='file:///bounded/tools/r0035/module.mjs';}});
  await mod.link(specifier=>{const values=dependencies[path.basename(specifier)];assert.ok(values,'unexpected dependency '+specifier);
    return new vm.SyntheticModule(Object.keys(values),function(){for(const [k,v]of Object.entries(values))this.setExport(k,v);},{context});});
  await mod.evaluate();return mod;
}
const plain=value=>JSON.parse(JSON.stringify(value));
function workerTrace(epoch){return {protocol:'r0035-worker-stages/1',clockDomain:'worker-performance-now-ms',epoch,
  marks:[{kind:'received',at:900000},{kind:'catalogue-start',at:900001},{kind:'catalogue-ready',at:900003},{kind:'source-verified',at:900004},
    {kind:'stars-prepared',at:900006},{kind:'replay-prepared',at:900010},{kind:'nominal-verified',at:900011},{kind:'census-complete',at:900012},{kind:'candidate-returned',at:900012},{kind:'ready-post',at:900013}]};}

async function lab(code){
  let now=100,utc=1000,worker;const calls=[];
  class Worker {constructor(){worker=this;this.messages=[];}
    postMessage(message,transfers){this.messages.push({message,transfers:transfers?.length??0});calls.push(['post',message.op,message.epoch]);}
    terminate(){calls.push(['terminate']);}}
  class Guard {constructor(enabled){this.enabled=enabled;this.retryAt=0;calls.push(['guard-created',enabled]);}
    reset(){calls.push(['guard-reset']);}observe(t){calls.push(['guard-observe',t]);}nextGain(){calls.push(['gain']);return 1;}}
  class Writer {invalidate(){calls.push(['invalidate']);}publish(image){calls.push(['write',...image.data]);return {writes:1,pixels:1};}}
  class History {reset(){calls.push(['history-reset']);}add(...args){calls.push(['history-add',...args]);}line(){return '';}}
  const overlay={style:{},setAttribute(){},getContext(){return {};},remove(){calls.push(['overlay-remove']);}};
  const parent={classList:{contains:kind=>kind==='real-sky-composed'},querySelectorAll:()=>[],querySelector:()=>null};
  const canvas={parentElement:parent,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530}),after(){calls.push(['overlay-attached']);},
    getContext:()=>({getImageData(...args){calls.push(['getImageData',...args]);return {data:new Uint8ClampedArray([0,0,0,255])};}})};
  const window={SalahNativeSkyHost:{capture:()=>({paused:false,reducedMotion:false,timeScale:1,utcMs:utc}),cloudsCurrent:()=>true},
    addEventListener(){},matchMedia:()=>({addEventListener(){}})};
  const context=vm.createContext({performance:{now:()=>now},window,document:{createElement:()=>overlay,addEventListener(){}},Worker,URL,
    structuredClone,Uint32Array,Uint8ClampedArray,Float64Array,ImageData:class{constructor(data){this.data=data;}},getComputedStyle:()=>({opacity:'0'})});
  const mod=await moduleFor(code,context,{'native-contract.mjs':{nativeDiscMask:()=>null,nativeResultCurrent:()=>true},
    'sample_history.mjs':{SampleHistory:History},'frame_guard.mjs':{FrameGuard:Guard},'changed_rectangles.mjs':{PresentationWriter:Writer}});
  const config={arm:'full',tile:16,multiplier:1,scope:'all',margin:0,glassFactor:1,guard:false};
  const api=mod.namespace.installLab(config),job={native:{identity:'bounded-owner'}},capture={cloudAuthority:{revision:1},cloudRGBA:null,moonRGBA:null};
  const frame=()=>({raster:{width:1,height:1},sources:[],catalogue:{}});
  function ready(epoch,op='ready'){worker.onmessage({data:{op,epoch,sources:1,census:{},contributingCenters:1,variablePixels:1,r0035Stages:workerTrace(epoch),reason:'bounded failed preparation'}});}
  function sample(epoch,value=1){worker.onmessage({data:{op:'sample',epoch,utcMs:utc,signal:new Uint32Array([value]),rgba:new Uint8ClampedArray([value,0,0,255]),sample:{id:'bounded',factor:1,centerDelta:[value,0,0]}}});}
  return {api,worker,calls,frame,publish:f=>api.publish('refined',canvas,job,f,capture,null),ready,sample,
    advance(ms=16){now+=ms;utc+=ms;},setClock(value){now=value;utc=value+900;}};
}

test('startup and warmup events survive the unchanged original trial buffer boundaries',async()=>{
  const results=[];
  for(const code of [source.live,modified.live]){const x=await lab(code),frame=x.frame();x.publish(frame);x.advance();x.ready(1);
    x.api.present();x.sample(1);x.advance();x.api.beginTrial();
    for(let i=0;i<12;i++){x.advance();x.api.present();x.sample(1,i+2);}
    const trial=x.api.endTrial(),state=x.api.observe();results.push({calls:plain(x.calls),trial:plain(trial),state:plain(state)});
    if(x.api.observeStages){const trace=x.api.observeStages();assert.equal(trace.events[0].kind,'installed');
      assert.ok(trace.events.find(e=>e.kind==='owner').at<trial.start);
      assert.ok(trace.events.find(e=>e.kind==='first-publication').at<trial.start);
      assert.equal(trace.events.filter(e=>e.kind==='first-publication').length,1);
      assert.equal(trace.events.filter(e=>e.kind==='first-sample-request').length,1);
      assert.equal('events' in state,false);assert.equal('stageLog' in state,false);
      assert.equal(trace.events.find(e=>e.kind==='prepare-reply').worker.marks[0].at,900000);
    }
  }
  assert.deepEqual(results[0],results[1]);assert.equal(results[0].calls.filter(x=>x[0]==='getImageData').length,1);
  assert.equal(results[0].calls.filter(x=>x[0]==='post'&&x[1]==='sample').length,13);
});

test('unchanged renewal creates no replacement and keeps original guard, image and write calls',async()=>{
  const results=[];
  for(const code of [source.live,modified.live]){const x=await lab(code),frame=x.frame();x.publish(frame);x.ready(1);x.publish(frame);x.api.present();x.sample(1);
    results.push(plain(x.calls));if(x.api.observeStages){const e=x.api.observeStages().events;assert.equal(e.filter(x=>x.kind==='owner').length,1);assert.equal(e.filter(x=>x.kind==='source-replacement').length,1);}}
  assert.deepEqual(...results);
});

for(const op of ['ready','failed'])test('stale '+op+' releases the original slot before dropping the reply and dispatches only the latest epoch',async()=>{
  const outputs=[];
  for(const code of [source.live,modified.live]){const x=await lab(code);x.publish(x.frame());x.advance();x.publish(x.frame());x.advance();x.publish(x.frame());
    assert.deepEqual(x.worker.messages.map(x=>x.message.epoch),[1]);x.advance();x.ready(1,op);
    assert.deepEqual(x.worker.messages.map(x=>x.message.epoch),[1,3]);x.advance();x.ready(3);x.api.present();x.sample(3);
    outputs.push({calls:plain(x.calls),state:plain(x.api.observe())});
    if(x.api.observeStages){const e=x.api.observeStages().events,reply=e.find(x=>x.kind==='prepare-reply'&&x.messageEpoch===1);
      assert.equal(reply.activeEpoch,3);assert.equal(reply.preparingEpoch,1);assert.equal(reply.latestQueued,true);
      assert.ok(e.indexOf(reply)<e.findIndex(x=>x.kind==='prepare-dispatch-start'&&x.messageEpoch===3));
      assert.equal(e.some(x=>x.kind==='prepare-dispatch-start'&&x.messageEpoch===2),false);
      assert.deepEqual(e.filter(x=>x.kind==='first-publication').map(x=>x.epoch),[3]);}}
  assert.deepEqual(...outputs);
});

test('bounded startup history marks overflow without changing original publication or guard behavior',async()=>{
  const results=[];
  for(const code of [source.live,modified.live]){const x=await lab(code);for(let i=0;i<1200;i++)x.publish(x.frame());
    if(x.api.observeStages){const trace=x.api.observeStages();assert.equal(trace.overflow,true);assert.equal(trace.events.length,2048);}
    assert.equal(x.worker.messages.length,1);assert.equal(x.api.observe().frames,0);results.push(plain(x.calls));}
  assert.deepEqual(...results);
});

async function workerModule(code,fault=null,deferred=false){
  let now=700000,resolveFetch;const messages=[],calls=[];
  const star={id:'s',hygId:1,hip:2,vmag:1,x:0,y:0,altDeg:10,azDeg:20,visible:true};
  const bytes=new TextEncoder().encode(JSON.stringify({stars:[star]}));
  const response={ok:true,async arrayBuffer(){return bytes.buffer;}};
  const context=vm.createContext({performance:{now:()=>now},self:{postMessage:(m,t)=>messages.push({message:m,transfers:t?.length??0})},
    URL,Uint8Array,Uint8ClampedArray,Uint32Array,TextDecoder,
    fetch:()=>deferred?new Promise(resolve=>{resolveFetch=()=>resolve(response);}):Promise.resolve(response)});
  const deps={
    'stellar_replay.mjs':{prepareStars(frame){calls.push('stars');now+=3;if(fault==='stars')throw Error('bounded stellar failure');return frame.sources;},preparePatch:()=>{},glassMembership:()=>false},
    'prepared_replay.mjs':{prepareReplay(raster,stars){calls.push('replay');now+=7;if(fault==='replay')throw Error('bounded replay failure');
      return {nominal:new Uint8ClampedArray([fault==='nominal'?1:0,0,0,255]),indices:[0],sourceCount:stars.length,contributingCenters:1,
        present(){calls.push('present');return {rgba:new Uint8ClampedArray([1,0,0,255]),sample:null};}};},stellarOverlay:(prepared,rgba)=>rgba},
    'sha256.mjs':{sha256Hex:()=> 'catalogue-digest'},'spectral.mjs':{spectralStarFlux:()=>({rgb:[1,1,1]})},
    'atmosphere.mjs':{directTransmission:()=>1,normaliseAtmosphere:x=>x},'projection.mjs':{projectPerspective:x=>x},
    'scene.mjs':{projectCatalogue(){calls.push('project');now+=2;return [{...star,x:fault==='source'?1:0}];},discOccults:()=>false},
    'visibility.mjs':{displayVisibility:()=>({detectable:true})},'photometry.mjs':{luminance:()=>1}};
  const mod=await moduleFor(code,context,deps);
  const message=epoch=>({op:'prepare',epoch,job:{observer:{},options:{view:{}}},frame:{sources:[star],catalogue:{sha256:fault==='catalogue'?'wrong':'catalogue-digest'},
    raster:{width:1,height:1,physicalState:{moon:{altDeg:-90}},sourceDiagnostics:[{id:'s',vmag:1,hip:2}]}},
    config:{scope:'all',margin:0,glassFactor:1},foreground:{glass:[]},nominal:new Uint8ClampedArray([0,0,0,255])});
  return {mod,context,messages,calls,message,send:m=>context.self.onmessage({data:m}),release:()=>resolveFetch(),setClock:n=>{now=n;}};
}

test('worker stages piggyback on original ready while original ready fields, sample messages and transfers stay identical',async()=>{
  const results=[];
  for(const code of [source.worker,modified.worker]){const w=await workerModule(code);await w.send(w.message(1));await w.send({op:'sample',epoch:1,utcMs:123,motion:{gain:1}});
    const data=plain(w.messages),ready=data[0].message,trace=ready.r0035Stages;delete ready.r0035Stages;
    if(trace){assert.equal(trace.clockDomain,'worker-performance-now-ms');assert.equal(trace.epoch,1);
      assert.deepEqual(trace.marks.map(x=>x.kind),['received','catalogue-start','catalogue-ready','source-verified','stars-prepared','replay-prepared','nominal-verified','census-complete','candidate-returned','ready-post']);
      assert.equal(trace.marks.find(x=>x.kind==='replay-prepared').at-trace.marks.find(x=>x.kind==='stars-prepared').at,7);}
    assert.equal(data[1].transfers,2);assert.equal('r0035Stages' in data[1].message,false);results.push({calls:w.calls,data});}
  assert.deepEqual(...results);
});

for(const [fault,last]of [['catalogue','catalogue-start'],['source','catalogue-ready'],['stars','source-verified'],['replay','stars-prepared'],['nominal','replay-prepared']]){
  test('original '+fault+' failure retains only completed worker stages and the same original error',async()=>{
    const outputs=[];
    for(const code of [source.worker,modified.worker]){const w=await workerModule(code,fault);await w.send(w.message(1));assert.equal(w.messages.length,1);
      const message=plain(w.messages[0].message),trace=message.r0035Stages;delete message.r0035Stages;
      if(trace){assert.equal(trace.marks.at(-1).kind,'failed');assert.equal(trace.marks.at(-2).kind,last);}
      outputs.push(message);}
    assert.deepEqual(...outputs);assert.equal(outputs[0].op,'failed');
  });
}

test('overlapping catalogue awaits use local traces and retain the original superseded no-reply behavior',async()=>{
  for(const code of [source.worker,modified.worker]){const w=await workerModule(code,null,true);
    const first=w.send(w.message(1));w.setClock(800000);const second=w.send(w.message(2));w.release();await Promise.all([first,second]);
    assert.equal(w.messages.length,1);assert.equal(w.messages[0].message.epoch,2);assert.deepEqual(w.calls,['project','stars','replay','project','stars','replay']);
    const trace=w.messages[0].message.r0035Stages;if(trace){assert.equal(trace.epoch,2);assert.equal(trace.marks[0].at,800000);assert.equal(trace.marks.filter(x=>x.kind==='received').length,1);}}
});
