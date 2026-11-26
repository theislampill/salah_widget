'use strict';
// Synthetic execution of the actual pinned original main/sampler expressions.
// No browser, native namespace, source preparation or timing claim.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.resolve(__dirname,'../r0040/capture.cjs'));
const S=require('./r0040_passive_sampler.cjs');
const helper=()=>require('./r0040_mechanism_bracket.cjs');
const plain=value=>JSON.parse(JSON.stringify(value));

function fixture({instrument=true,times=[[10,20],[30,40],[50,60]],failSample=null,clockFault=false,eventStamp=(_,i)=>100+i}={}){
  const B=helper(),original=B.originalExpressions(source),queue=[],events=[],clock={now:0,reads:0};
  const box={getBoundingClientRect(){return {x:0,y:0,width:325,height:530};},dataset:{precip:'on'}};
  const listeners=[];
  const bus={textContent:'',addEventListener(type,fn){assert.equal(type,'r0040-read');listeners.push(fn);},
    dispatchEvent(event){events.push(['dispatch',event.type]);for(const fn of listeners)Reflect.apply(fn,bus,[event]);return true;}};
  const document={createElement(){return bus;},body:{appendChild(v){assert.equal(v,bus);}},
    querySelector(q){return q==='#r0040-audit'?bus:box;},querySelectorAll(){return [box];}};
  const main=vm.createContext({document,performance:{timeOrigin:1000,now(){clock.reads++;if(clockFault&&clock.reads===1)throw Error('synthetic clock failure');return clock.now;}},
    Date:{now(){return 10000+Math.floor(clock.now);}},getComputedStyle(){return {backdropFilter:'blur(1px)'};},
    selectedWeather(){if(failSample)throw failSample;return {code:63,precip:1.25,currentIntervalSec:900};},
    __PM:{last:{t:3,model:'M1',policy:'immediate',G:100,T:1/60,R:5}},
    __R0040_DATE_ONLY__:{protocol:'r0040-date-only-installed/1',utcMs:10000,anchorPerformanceMs:0,timeOriginMs:1000}});
  vm.runInContext('globalThis.window=globalThis',main);
  const code=instrument?B.instrumentMain(original.main).expression:original.main;
  vm.runInContext('('+code+')({utc:10000,rectRecipe:"[]"})',main);
  // This original direct geometry call must not increment a dispatch ordinal.
  if(!failSample)vm.runInContext('__r0040Sample()',main);
  let emitted=0;
  const isolated=vm.createContext({document,Event:class{constructor(type){this.type=type;this.timeStamp=eventStamp(clock.now,emitted++);}},
    performance:{timeOrigin:2000,now:()=>clock.now},requestAnimationFrame(fn){events.push(['rAF']);queue.push(fn);return queue.length;}});
  const passive=S.instrumentStart(original.isolated);
  vm.runInContext(instrument?B.instrumentIsolated(passive.expression).expression:passive.expression,isolated);
  let primary=null;
  for(const [stamp,entry]of times){clock.now=entry;try{queue.shift()(stamp);}catch(error){primary=error;break;}}
  const stop=vm.runInContext('globalThis.active=false; globalThis.samples',isolated);
  const rawStop=Buffer.from(JSON.stringify({result:{value:stop}}));
  return {B,main,isolated,bus,listeners,primary,events,rawStop,samples:plain(stop),
    mainRaw:instrument?plain(vm.runInContext('('+B.snapshotMain.toString()+')()',main)):null,
    joinRaw:instrument?plain(vm.runInContext(B.READ_JOIN,isolated)):null,
    passiveRaw:plain(vm.runInContext('globalThis.__R0040_PASSIVE_SAMPLER__',isolated)),
    proof:{utcMs:10000,anchorPerformanceMs:0,timeOriginMs:1000}};
}

test('actual source transforms recover original whole expressions and reject drift',()=>{
  const B=helper(),o=B.originalExpressions(source),m=B.instrumentMain(o.main),p=S.instrumentStart(o.isolated),i=B.instrumentIsolated(p.expression);
  assert.equal(B.reverseMain(m.expression),o.main);assert.equal(B.reverseIsolated(i.expression),p.expression);
  assert.equal(S.reverseStart(B.reverseIsolated(i.expression)),o.isolated);
  assert.equal(m.identity.changedSeams,1);assert.equal(i.identity.changedSeams,1);
  for(const changed of [Buffer.concat([source,Buffer.from(' ')]),Buffer.from(source.toString().replace('phaseMs:Date.now()','phaseMs:0'))])
    assert.throws(()=>B.originalExpressions(changed),/source|digest/);
  for(const changed of [o.main+' ',o.main.replace('JSON.stringify','String')])assert.throws(()=>B.instrumentMain(changed));
  assert.throws(()=>B.reverseMain(m.expression+' '));assert.throws(()=>B.reverseIsolated(i.expression+' '));
});

test('actual original sample and stop payload, calls and scheduling survive the new listeners',()=>{
  const baseline=fixture({instrument:false}),observed=fixture();
  assert.deepEqual(observed.samples,baseline.samples);assert.deepEqual(observed.rawStop,baseline.rawStop);
  assert.deepEqual(observed.events,baseline.events);
  assert.equal(observed.mainRaw.calls,3);assert.equal(observed.joinRaw.calls,3);
  assert.deepEqual(observed.mainRaw.rows,[[0,100,20,20,'returned'],[1,101,40,40,'returned'],[2,102,60,60,'returned']]);
  assert.deepEqual(observed.joinRaw.rows,[[0,100],[1,101],[2,102]]);
  const result=observed.B.inspectBrackets(observed.mainRaw,observed.joinRaw,observed.passiveRaw,observed.rawStop,observed.proof);
  assert.equal(result.status,'OBSERVED');assert.equal(result.rows,3);assert.equal(result.clockBridge.status,'BOUNDED_CONDITIONAL_OFFSET');
  assert.equal(result.clockBridge.lowerMs,0);assert.equal(result.clockBridge.upperMs,0);
});

test('generic wrapper preserves actual receiver, argument identity, return and original throw',()=>{
  const B=helper(),calls=[],primary=Error('original callback failed'),receiver={original:true},payload={timeStamp:7};
  const context=vm.createContext({performance:{timeOrigin:1,now:()=>2},Date:{now:()=>9},
    __R0040_DATE_ONLY__:{protocol:'r0040-date-only-installed/1',utcMs:8,anchorPerformanceMs:1,timeOriginMs:1}});
  const original=function(...args){calls.push([this,args]);return payload;};context.original=original;
  const wrapped=vm.runInContext('('+B.installMainBracket.toString()+')(original)',context);
  assert.equal(Reflect.apply(wrapped,receiver,[payload,'extra']),payload);assert.equal(calls[0][0],receiver);
  assert.equal(calls[0][1][0],payload);assert.equal(calls[0][1][1],'extra');
  const failed=fixture({failSample:primary});assert.equal(failed.primary,primary);assert.equal(failed.samples.length,0);
  assert.equal(failed.mainRaw.rows[0][4],'threw');assert.equal(failed.joinRaw.rows.length,0);
});

test('observer clock fault retains original payload and reports incomplete diagnostics',()=>{
  const baseline=fixture({instrument:false}),failed=fixture({clockFault:true});
  assert.deepEqual(failed.rawStop,baseline.rawStop);assert.deepEqual(failed.events,baseline.events);assert.equal(failed.primary,null);
  assert.ok(failed.mainRaw.faults>0);
  assert.throws(()=>failed.B.inspectBrackets(failed.mainRaw,failed.joinRaw,failed.passiveRaw,failed.rawStop,failed.proof),/fault|clock|incomplete/);
});

test('missing reordered duplicated or forged event joins cannot claim complete ordinals',()=>{
  const f=fixture();
  for(const mutate of [x=>x.rows.pop(),x=>x.rows[1][0]=0,x=>x.rows.reverse(),x=>x.rows[1][1]=x.rows[0][1],x=>x.rows[1][1]=999,x=>x.calls++]){
    const j=plain(f.joinRaw);mutate(j);assert.throws(()=>f.B.inspectBrackets(f.mainRaw,j,f.passiveRaw,f.rawStop,f.proof));
  }
  const repeated=fixture({eventStamp:()=>0});
  assert.throws(()=>repeated.B.inspectBrackets(repeated.mainRaw,repeated.joinRaw,repeated.passiveRaw,repeated.rawStop,repeated.proof),/unique|stamp/);
});

test('wrong source clocks, Date binding, phase and original raw stop are refused',()=>{
  const f=fixture();
  for(const mutate of [x=>x.clockDomain='isolated-performance',x=>x.timeOriginMs++,x=>x.clockPreserved=false,
      x=>x.datePreserved=false,x=>x.anchor.anchorPerformanceMs++,x=>x.rows[0][2]=NaN,x=>x.rows[0][3]=-1]){
    const m=plain(f.mainRaw);mutate(m);assert.throws(()=>f.B.inspectBrackets(m,f.joinRaw,f.passiveRaw,f.rawStop,f.proof));
  }
  assert.throws(()=>f.B.inspectBrackets(f.mainRaw,f.joinRaw,f.passiveRaw,JSON.parse(f.rawStop),f.proof),/Buffer|bytes/);
  const stop=JSON.parse(f.rawStop);stop.result.value[0].phaseMs++;
  assert.throws(()=>f.B.inspectBrackets(f.mainRaw,f.joinRaw,f.passiveRaw,Buffer.from(JSON.stringify(stop)),f.proof),/phase|Date/);
});

test('bounded overflow keeps the actual original population while refusing the partial join',()=>{
  const times=Array.from({length:4098},(_,i)=>[i*10,i*10+2]),base=fixture({instrument:false,times}),f=fixture({times});
  assert.deepEqual(f.rawStop,base.rawStop);assert.equal(f.samples.length,4098);
  assert.equal(f.mainRaw.rows.length,4096);assert.equal(f.mainRaw.dropped,2);
  assert.equal(f.joinRaw.rows.length,4096);assert.equal(f.joinRaw.dropped,2);
  assert.throws(()=>f.B.inspectBrackets(f.mainRaw,f.joinRaw,f.passiveRaw,f.rawStop,f.proof),/overflow|bounded|incomplete/);
});

test('clock replacement during sampling cannot silently change the preserved clock semantics',()=>{
  const f=fixture(),old=plain(f.mainRaw);f.main.performance.now=()=>123;
  const replaced=plain(vm.runInContext('('+f.B.snapshotMain.toString()+')()',f.main));
  assert.equal(old.clockPreserved,true);assert.equal(replaced.clockPreserved,false);
  assert.throws(()=>f.B.inspectBrackets(replaced,f.joinRaw,f.passiveRaw,f.rawStop,f.proof),/clock|identity/);
});

test('same-world arithmetic distinguishes variable callback delay from constant delay',()=>{
  const B=helper(),constant=B.sameWorldArithmetic([[10,20,20],[30,40,40]],0),variable=B.sameWorldArithmetic([[10,40,40],[30,45,45]],0);
  assert.equal(constant.dateVersusRafResidualMs,0);assert.equal(constant.callbackLagChangeMs,0);
  assert.equal(variable.dateVersusRafResidualMs,-15);assert.equal(variable.callbackLagChangeMs,-15);
  const rounded=B.sameWorldArithmetic([[10,40.2,39],[30,45.8,45]],.4);
  assert.ok(Math.abs(rounded.dateVersusRafResidualMs-rounded.callbackLagChangeMs-rounded.roundingResidualChangeMs)<1e-9);
  assert.throws(()=>B.sameWorldArithmetic([[10,40,0],[30,45,1]],0),/Date|formula/);
});

test('complete brackets may honestly leave the conditional clock bridge unresolved',()=>{
  const f=fixture(),raw=plain(f.passiveRaw);raw.rows[1][2]+=5;raw.rows[1][3]+=5;
  const inspection=f.B.inspectBrackets(f.mainRaw,f.joinRaw,raw,f.rawStop,f.proof);
  assert.equal(inspection.status,'OBSERVED');assert.equal(inspection.clockBridge.status,'UNRESOLVED_CLOCK_BRIDGE');
  assert.equal(inspection.nativeQualification,'NOT_VERIFIED');
});
