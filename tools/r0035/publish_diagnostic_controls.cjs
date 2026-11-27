'use strict';
// Execute the complete pinned lab and its real local dependencies. Only browser
// surfaces and worker delivery are controlled; no native or timing claim follows.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createHash}=require('node:crypto'),{pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'../..'),helperPath=path.join(__dirname,'publish_diagnostic.mjs');
const original=fs.readFileSync(path.join(__dirname,'live_lab.mjs'));
const plain=value=>JSON.parse(JSON.stringify(value));
const sha=value=>createHash('sha256').update(value).digest('hex');
const terms=['rasterReference','canvasReference','discKey','glassBounds','cloudPixels','moonPixels','maskPixels'];
async function helper(){
  assert.ok(fs.existsSync(helperPath),'publish diagnostic source helper has not been implemented');
  return import(pathToFileURL(helperPath).href);
}
function stable(value){
  if(ArrayBuffer.isView(value))return {type:value.constructor.name,length:value.length,
    sha256:sha(Buffer.from(value.buffer,value.byteOffset,value.byteLength))};
  if(Array.isArray(value))return value.map(stable);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,stable(v)]));
  return value;
}
async function lab(code,{trace=true}={}){
  let now=100,utc=1000,worker,clockCalls=0,discOn=false,boxCount=0,failAfter=false;
  const calls=[],listeners={},nominal=new Uint8ClampedArray(325*530*4);
  const log=(...row)=>{if(trace)calls.push(row);};
  class Worker{
    constructor(){worker=this;this.messages=[];}
    postMessage(message){const copied=structuredClone(message);this.messages.push(copied);log('post',stable(copied));}
    terminate(){log('terminate');}
  }
  const overlay={style:{},setAttribute(){},getContext(){return {putImageData(image,...args){log('write',stable(image.data),...args);}};},
    remove(){log('remove');}};
  const disc={classList:{contains:()=>true},getScreenCTM:()=>({a:1,b:0,c:0,d:1,e:0,f:0}),getAttribute:()=>20};
  const parent={classList:{contains:key=>key==='real-sky-composed'},querySelector:()=>discOn?disc:null,
    querySelectorAll:()=>Array.from({length:boxCount},()=>({getBoundingClientRect:()=>({left:1,top:2,width:3,height:4})}))};
  function canvas(){return {parentElement:parent,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530}),
    after(){log('after');if(failAfter)throw new Error('original after failure');},
    getContext:()=>({getImageData(...args){log('readback',...args);return {data:nominal};}})};}
  const snapshot=()=>({utcMs:utc,lat:24,lon:39,heightM:0,sceneIdentity:'bounded',generation:1,
    camera:{azDeg:0,altDeg:30,fovYDeg:90,rollDeg:0},weather:null,lp:0,reducedMotion:false,
    allowEstimates:true,units:'c',tz:'UTC',timeScale:1,paused:false});
  const window={SalahNativeSkyHost:{capture(){log('capture');return snapshot();},cloudsCurrent:()=>true},
    addEventListener(name,fn){listeners[name]=fn;},matchMedia:()=>({addEventListener(){}})};
  const context=vm.createContext({performance:{now(){clockCalls++;log('clock',now);return now;}},window,
    document:{createElement:()=>overlay,addEventListener(name,fn){listeners[name]=fn;}},Worker,URL,
    structuredClone,Uint32Array,Uint8Array,Uint8ClampedArray,Float64Array,
    ImageData:class{constructor(data,width,height){this.data=data;this.width=width;this.height=height;}},
    getComputedStyle:()=>({opacity:'1'})});
  const cache=new Map();
  async function load(filename,override){
    filename=path.resolve(filename);if(cache.has(filename))return cache.get(filename);
    assert.ok(filename.startsWith(root+path.sep),'fixture import outside source tree');
    const m=new vm.SourceTextModule(override??fs.readFileSync(filename,'utf8'),{context,identifier:filename,
      initializeImportMeta:meta=>{meta.url=pathToFileURL(filename).href;}});cache.set(filename,m);
    await m.link(spec=>load(path.resolve(path.dirname(filename),spec)));return m;
  }
  const m=await load(path.join(__dirname,'live_lab.mjs'),code.toString());await m.evaluate();
  const contract=cache.get(path.join(root,'real-sky/native-contract.mjs')).namespace;
  const api=m.namespace.installLab({arm:'full',tile:16,multiplier:1,scope:'all',margin:0,glassFactor:1,guard:false});
  const initialCanvas=canvas(),job=contract.nativeJob(snapshot()),capture={cloudAuthority:{revision:1},cloudRGBA:null,moonRGBA:null};
  const initialFrame={status:'complete',sources:[],catalogue:{},raster:{width:325,height:530}};
  const args=['refined',initialCanvas,job,initialFrame,capture,null];
  const ready=(epoch,op='ready')=>worker.onmessage({data:{op,epoch,sources:1,census:{},contributingCenters:1,
    variablePixels:1,reason:'original preparation failure'}});
  const sample=epoch=>worker.onmessage({data:{op:'sample',epoch,utcMs:utc,signal:new Uint32Array([1]),rgba:nominal,sample:null}});
  return {api,args,calls,worker,canvas,capture,ready,sample,log,listeners,
    publish(next=args){api.publish(...next);},
    setDisc(value){discOn=value;},setBoxes(value){boxCount=value;},failAfter(){failAfter=true;},
    advance(){now+=16;utc+=16;},clockCalls:()=>clockCalls,
    result(){return {calls:stable(calls),state:plain(api.observe()),messages:stable(worker.messages),clockCalls};}};
}
function withoutDiagnostic(trial){
  const copied=plain(trial);for(const event of copied.events)delete event.r0035Publish;return copied;
}
async function pair(action,options){
  const h=await helper(),derived=h.derivePublishDiagnostic(original),results=[];
  for(const code of [original,derived]){
    const x=await lab(code,options);const extra=await action(x,code===derived,h);
    results.push({...x.result(),extra});
  }
  assert.deepEqual(results[0],results[1]);return results[1];
}

test('actual source pair is exact, reversible and rejects drift and copied identities',async()=>{
  const h=await helper(),before=Buffer.from(original),derived=h.derivePublishDiagnostic(original);
  assert.notDeepEqual(derived,original);assert.deepEqual(original,before);
  assert.deepEqual(h.restorePublishDiagnostic(derived),original);
  const identity=h.publishDiagnosticIdentity(original,derived);
  assert.equal(identity.protocol,'r0035-publish-diagnostic-source/1');
  assert.equal(identity.reference.sha256,sha(original));assert.equal(identity.derived.sha256,sha(derived));
  assert.equal(identity.nativeObservation,'NOT_RUN');assert.equal(identity.speed,'NOT_ESTABLISHED');
  for(const value of [original.toString(),new Uint8Array(original),null])assert.throws(()=>h.derivePublishDiagnostic(value));
  assert.throws(()=>h.derivePublishDiagnostic(Buffer.concat([original,Buffer.from('\n')])));
  assert.throws(()=>h.restorePublishDiagnostic(Buffer.concat([derived,Buffer.from('\n')])));
  const changed=Buffer.from(derived);changed[changed.length-3]^=1;
  assert.throws(()=>h.publishDiagnosticIdentity(original,changed));
});

test('first acquisition records source absence at replacement with later comparisons unexecuted',async()=>{
  await pair((x,diagnostic,h)=>{
    x.api.beginTrial();x.publish();const trial=x.api.endTrial();
    if(diagnostic){const owner=trial.events.find(e=>e.kind==='owner');
      const d=h.decodePublishDecision(owner.r0035Publish,owner.epoch);
      assert.equal(d.kind,'SOURCE_ABSENT_AT_REPLACEMENT');assert.equal(d.decisiveTerm,'rasterReference');
      assert.deepEqual(d.terms.map(x=>x.outcome),['DIFFERENT',...Array(6).fill('NOT_EVALUATED')]);
      assert.deepEqual(d.activity,{wasPrepared:false,samplePending:false,preparingEpoch:null,latestQueued:false});}
    return withoutDiagnostic(trial);
  });
});

test('each of the seven original first-false comparisons is identified without new behavior',async()=>{
  const cases=[['rasterReference',1,0],['canvasReference',3,1],['discKey',7,3],['glassBounds',15,7],
    ['cloudPixels',31,15],['moonPixels',63,31],['maskPixels',127,63]];
  for(const [term,evaluated,equal] of cases)await pair((x,diagnostic,h)=>{
    x.publish();x.ready(1);x.api.beginTrial();const next=[...x.args];
    if(term==='rasterReference')next[3]={...next[3],raster:{...next[3].raster}};
    if(term==='canvasReference')next[1]=x.canvas();
    if(term==='discKey')x.setDisc(true);
    if(term==='glassBounds')x.setBoxes(1);
    if(term==='cloudPixels')next[4]={...next[4],cloudRGBA:new Uint8Array([1])};
    if(term==='moonPixels')next[4]={...next[4],moonRGBA:new Uint8Array([1])};
    if(term==='maskPixels')next[5]=new Float64Array([1]);
    x.publish(next);const trial=x.api.endTrial();
    if(diagnostic){const owner=trial.events.find(e=>e.kind==='owner'),d=owner.r0035Publish;
      assert.equal(d.evaluatedMask,evaluated);assert.equal(d.equalMask,equal);
      const decoded=h.decodePublishDecision(d,owner.epoch);assert.equal(decoded.decisiveTerm,term);
      assert.equal(decoded.kind,'SOURCE_PRESENT_AT_REPLACEMENT');assert.equal(decoded.activity.wasPrepared,true);
      assert.deepEqual(decoded.terms.map(t=>t.term),terms);}
    return withoutDiagnostic(trial);
  });
});

test('same-byte distinct arrays renew and in-place array changes preserve the original reference fast path',async()=>{
  await pair(x=>{
    x.args[4]={...x.args[4],cloudRGBA:new Uint8Array([1,2]),moonRGBA:new Uint8Array([3,4])};
    x.args[5]=new Float64Array([1,0]);x.publish();x.ready(1);x.api.beginTrial();
    const next=[...x.args];next[4]={...x.args[4],cloudRGBA:new Uint8Array([1,2]),moonRGBA:new Uint8Array([3,4])};
    next[5]=new Float64Array([1,0]);x.publish(next);
    // Existing source keeps the original arrays after renew; equality is not a
    // claim about historical contents of a mutable same-reference buffer.
    x.args[4].cloudRGBA[0]=9;x.publish(x.args);
    const trial=x.api.endTrial();assert.equal(trial.events.filter(e=>e.kind==='owner').length,0);
    assert.equal(x.worker.messages.length,1);return withoutDiagnostic(trial);
  });
});

test('short circuit does not read a later cloud or Moon operand before the original failing effect',async()=>{
  for(const field of ['cloudRGBA','moonRGBA'])await pair(x=>{
    x.publish();x.ready(1);x.api.beginTrial();x.failAfter();const next=[...x.args];
    next[4]={...x.args[4]};
    if(field==='cloudRGBA')x.setBoxes(1);
    else next[4].cloudRGBA=new Uint8Array([1]);
    Object.defineProperty(next[4],field,{get(){x.log('forbidden-read',field);throw new Error('later operand read');}});
    x.publish(next);assert.equal(x.api.observe().status,'Error: original after failure');
    assert.equal(x.calls.some(c=>c[0]==='forbidden-read'),false);
    return withoutDiagnostic(x.api.endTrial());
  });
});

test('every original operand access remains once in the same order and original predicate exceptions survive',async()=>{
  for(const throws of [false,true])await pair(x=>{
    x.publish();x.ready(1);x.api.beginTrial();const next=[...x.args];
    next[4]={cloudAuthority:{revision:2}};
    for(const name of ['cloudRGBA','moonRGBA'])Object.defineProperty(next[4],name,{get(){
      x.log('operand',name);if(throws&&name==='cloudRGBA')throw new Error('original operand failure');return null;}});
    x.publish(next);
    assert.deepEqual(x.calls.filter(c=>c[0]==='operand'),throws?[['operand','cloudRGBA']]:[['operand','cloudRGBA'],['operand','moonRGBA']]);
    if(throws)assert.equal(x.api.observe().status,'Error: original operand failure');
    return withoutDiagnostic(x.api.endTrial());
  });
});

test('reentrant source replacement keeps each invocation comparison mask separate',async()=>{
  await pair((x,diagnostic,h)=>{
    x.publish();x.ready(1);x.api.beginTrial();let entered=false;
    const inner=[...x.args];inner[3]={...inner[3],raster:{...inner[3].raster}};
    const outer=[...x.args],cloud=new Uint8Array([1]);
    outer[4]={...x.args[4]};Object.defineProperty(outer[4],'cloudRGBA',{get(){
      x.log('reentrant-read');if(!entered){entered=true;x.publish(inner);}return cloud;}});
    x.publish(outer);const trial=x.api.endTrial(),owners=trial.events.filter(e=>e.kind==='owner');
    assert.deepEqual(plain(owners.map(e=>e.epoch)),[2,3]);
    if(diagnostic){assert.deepEqual(plain(owners.map(e=>[e.r0035Publish.evaluatedMask,e.r0035Publish.equalMask])),[[1,0],[31,15]]);
      assert.deepEqual(plain(owners.map(e=>h.decodePublishDecision(e.r0035Publish,e.epoch).decisiveTerm)),['rasterReference','cloudPixels']);}
    return withoutDiagnostic(trial);
  });
});

test('reentrant clear keeps earlier comparisons independent of later source presence',async()=>{
  await pair((x,diagnostic,h)=>{
    x.publish();x.ready(1);x.api.beginTrial();let entered=false;
    const next=[...x.args],cloud=new Uint8Array([1]);next[4]={...x.args[4]};
    Object.defineProperty(next[4],'cloudRGBA',{get(){
      x.log('reentrant-clear-read');if(!entered){entered=true;x.api.clear(x.args[1]);}return cloud;}});
    x.publish(next);const trial=x.api.endTrial();
    if(diagnostic){
      const owner=trial.events.find(e=>e.kind==='owner'),facts=plain(owner.r0035Publish);
      assert.equal(owner.epoch,3);assert.equal(facts.previousEpoch,2);assert.equal(facts.hadSource,false);
      assert.equal(facts.evaluatedMask,31);assert.equal(facts.equalMask,15);
      const decoded=h.decodePublishDecision(facts,owner.epoch);
      assert.equal(decoded.decisiveTerm,'cloudPixels');assert.equal(decoded.kind,'SOURCE_ABSENT_AT_REPLACEMENT');
      assert.deepEqual(decoded.terms.map(row=>row.outcome),
        ['EQUAL','EQUAL','EQUAL','EQUAL','DIFFERENT','NOT_EVALUATED','NOT_EVALUATED']);
    }
    return withoutDiagnostic(trial);
  });
});

test('reentry after the snapshot keeps behavior but refuses an unbound outer owner record',async()=>{
  await pair((x,diagnostic,h)=>{
    x.publish();x.ready(1);x.api.beginTrial();let reads=0;
    const next=[...x.args],inner=[...x.args];inner[3]={...inner[3],raster:{...inner[3].raster}};
    next[4]={...x.args[4]};Object.defineProperty(next[4],'cloudRGBA',{get(){
      x.log('assignment-reentrant-read',++reads);if(reads===2)x.publish(inner);return new Uint8Array([1]);}});
    x.publish(next);const trial=x.api.endTrial();
    if(diagnostic){
      const owners=trial.events.filter(e=>e.kind==='owner');assert.deepEqual(plain(owners.map(e=>e.epoch)),[3,3]);
      assert.equal(h.decodePublishDecision(owners[0].r0035Publish,owners[0].epoch).decisiveTerm,'rasterReference');
      assert.equal(owners[1].r0035Publish.previousEpoch,1);
      assert.throws(()=>h.decodePublishDecision(owners[1].r0035Publish,owners[1].epoch),/owner epoch mismatch/);
    }
    return withoutDiagnostic(trial);
  });
});

test('queued replacements and stale completion retain the actual in-flight slot and latest-only dispatch',async()=>{
  for(const op of ['ready','failed'])await pair((x,diagnostic,h)=>{
    x.api.beginTrial();x.publish();x.advance();
    for(let i=0;i<2;i++){const next=[...x.args];next[3]={...next[3],raster:{...next[3].raster}};x.publish(next);}
    assert.deepEqual(x.worker.messages.map(m=>m.epoch),[1]);
    x.ready(1,op);assert.deepEqual(x.worker.messages.map(m=>m.epoch),[1,3]);
    x.ready(3);x.api.present();x.sample(3);
    const trial=x.api.endTrial(),owners=trial.events.filter(e=>e.kind==='owner');
    if(diagnostic){const facts=owners.map(e=>h.decodePublishDecision(e.r0035Publish,e.epoch).activity);
      assert.deepEqual(plain(facts),[
        {wasPrepared:false,samplePending:false,preparingEpoch:null,latestQueued:false},
        {wasPrepared:false,samplePending:false,preparingEpoch:1,latestQueued:false},
        {wasPrepared:false,samplePending:false,preparingEpoch:1,latestQueued:true}]);}
    return withoutDiagnostic(trial);
  });
});

test('a pending sample and ready source are recorded before original replacement clears them',async()=>{
  await pair((x,diagnostic,h)=>{
    x.publish();x.ready(1);x.api.present();x.api.beginTrial();
    const next=[...x.args];next[3]={...next[3],raster:{...next[3].raster}};x.publish(next);
    x.sample(1);x.ready(2);x.api.present();x.sample(2);
    const trial=x.api.endTrial();
    if(diagnostic){const owner=trial.events.find(e=>e.kind==='owner');
      assert.deepEqual(h.decodePublishDecision(owner.r0035Publish,owner.epoch).activity,
        {wasPrepared:true,samplePending:true,preparingEpoch:null,latestQueued:false});}
    return withoutDiagnostic(trial);
  });
});

test('no active trial adds no retained records and does not change presentation or disposal',async()=>{
  await pair(x=>{
    x.publish();x.ready(1);x.api.present();x.sample(1);assert.equal(x.api.endTrial(),null);
    x.api.beginTrial();x.api.clear(x.args[1]);x.publish();x.ready(3);x.api.dispose();
    return withoutDiagnostic(x.api.endTrial());
  });
});

test('original event cap, overflow and complete non-diagnostic event population stay exact',async()=>{
  await pair((x,diagnostic)=>{
    x.api.beginTrial();for(let i=0;i<16390;i++){
      const next=[...x.args];next[3]={...next[3],raster:{width:325,height:530}};x.publish(next);
    }
    const trial=x.api.endTrial();assert.equal(trial.events.length,16384);assert.equal(trial.overflow,true);
    assert.equal(x.worker.messages.length,1);
    if(diagnostic)assert.ok(trial.events.filter(e=>e.kind==='owner').every(e=>e.r0035Publish));
    return withoutDiagnostic(trial);
  },{trace:false});
});

test('decoder refuses missing, impossible, promoted or unbound decision records',async()=>{
  const h=await helper(),x=await lab(h.derivePublishDiagnostic(original));x.api.beginTrial();x.publish();
  const owner=x.api.endTrial().events.find(e=>e.kind==='owner'),valid=plain(owner.r0035Publish);
  const invalid=[null,{}, {...valid,protocol:'accepted'}, {...valid,other:1}, {...valid,evaluatedMask:5},
    {...valid,equalMask:1}, {...valid,hadSource:0},
    {...valid,wasPrepared:1}, {...valid,preparingEpoch:-1}, {...valid,preparingEpoch:1},
    {...valid,previousEpoch:1}, {...valid,latestQueued:null}];
  for(const value of invalid)assert.throws(()=>h.decodePublishDecision(value,owner.epoch));
  for(const epoch of [undefined,null,0,1.5,2])assert.throws(()=>h.decodePublishDecision(valid,epoch));
});

test('behavior controls detect eager comparison and extra clock mutants; identity rejects them',async()=>{
  const h=await helper(),derived=h.derivePublishDiagnostic(original);
  const eager=Buffer.from(derived.toString().replace('          &&publishCheck(16','          &publishCheck(16'));
  assert.notDeepEqual(eager,derived);assert.throws(()=>h.publishDiagnosticIdentity(original,eager));
  const clock=Buffer.from(derived.toString().replace("      event('owner',", "      performance.now();event('owner',"));
  assert.notDeepEqual(clock,derived);assert.throws(()=>h.publishDiagnosticIdentity(original,clock));
  const outcomes=[];
  for(const code of [original,eager,clock]){
    const x=await lab(code);x.publish();x.ready(1);x.api.beginTrial();x.setBoxes(1);x.failAfter();
    const next=[...x.args];next[4]={...x.args[4]};Object.defineProperty(next[4],'cloudRGBA',{get(){throw Error('eager operand');}});
    x.publish(next);outcomes.push({status:x.api.observe().status,clockCalls:x.clockCalls()});
  }
  assert.equal(outcomes[0].status,'Error: original after failure');
  assert.equal(outcomes[1].status,'Error: eager operand');
  assert.equal(outcomes[2].clockCalls,outcomes[0].clockCalls+1);
});
