'use strict';
// Exact-expression diagnostic extension. Original samples, dispatch, rAF calls
// and their order stay in the original expression. No cadence gate is added.
const {createHash}=require('node:crypto');
const sha=value=>createHash('sha256').update(value).digest('hex');
const need=(condition,message)=>{if(!condition)throw Error(message);};
const ORIGINAL_SHA256='ae217210b954f8cf349cd2a85446437147947cd6bc50ec169b54f030f6d09e01';
const SEAM="const read=ts=>{if(!active)return;bus.dispatchEvent(new Event('r0040-read'));";

function installSamplerBuffer(){
  if(Object.hasOwn(globalThis,'__R0040_PASSIVE_SAMPLER__'))throw Error('fresh passive sampler witness required');
  const state={protocol:'r0040-passive-sampler/1',clockDomain:'isolated-performance',timeOriginMs:performance.timeOrigin,
    limit:4096,rows:[],dropped:0,faults:0};
  Object.defineProperty(globalThis,'__R0040_PASSIVE_SAMPLER__',{value:state,writable:false,configurable:false});
  return {
    enter(){try{return performance.now();}catch(_){state.faults++;return null;}},
    after(ordinal,timestamp,entry){
      try{
        const after=performance.now();
        if(state.rows.length<state.limit)state.rows.push([ordinal,timestamp,entry,after]);
        else state.dropped++;
      }catch(_){state.faults++;}
    }
  };
}

function extension(){
  return 'const passiveSampler=('+installSamplerBuffer.toString()+')();\n        '+
    "const read=ts=>{if(!active)return;const passiveEntry=passiveSampler.enter();bus.dispatchEvent(new Event('r0040-read'));"+
    'passiveSampler.after(samples.length,ts,passiveEntry);';
}

function reverseStart(expression){
  const added=extension();need(typeof expression==='string'&&expression.split(added).length===2,'unique passive sampler reversal required');
  const original=expression.replace(added,()=>SEAM);
  need(sha(original)===ORIGINAL_SHA256,'passive sampler reversal digest differs');return original;
}

function instrumentStart(expression){
  need(typeof expression==='string'&&sha(expression)===ORIGINAL_SHA256,'original sampler source digest differs');
  need(expression.split(SEAM).length===2,'unique original sampler seam required');
  const observed=expression.replace(SEAM,extension);
  need(reverseStart(observed)===expression,'original sampler source was not recovered exactly');
  return {expression:observed,identity:{protocol:'r0040-passive-sampler-extension/1',originalExpressionSha256:ORIGINAL_SHA256,
    instrumentedExpressionSha256:sha(observed),bufferInstallerSha256:sha(installSamplerBuffer.toString()),
    changedSeams:1,originalRecoveredExactly:true,limit:4096}};
}

function inspectSampler(raw){
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  need(raw&&typeof raw==='object'&&!Array.isArray(raw)&&
    Object.keys(raw).sort().join(',')==='clockDomain,dropped,faults,limit,protocol,rows,timeOriginMs',
    'complete passive sampler fields required');
  need(raw.protocol==='r0040-passive-sampler/1'&&raw.clockDomain==='isolated-performance'&&
    finite(raw.timeOriginMs)&&raw.timeOriginMs>0&&raw.limit===4096,'passive sampler clock or identity differs');
  need(Number.isSafeInteger(raw.dropped)&&raw.dropped>=0&&Number.isSafeInteger(raw.faults)&&raw.faults>=0,
    'invalid passive sampler fault counts');
  need(raw.dropped===0,'passive sampler overflow is incomplete');
  need(raw.faults===0,'passive sampler clock fault is incomplete');
  need(Array.isArray(raw.rows)&&raw.rows.length>0&&raw.rows.length<=raw.limit,'nonempty bounded passive sampler prefix required');
  const intervals=raw.rows.map((row,ordinal)=>{
    need(Array.isArray(row)&&row.length===4&&row[0]===ordinal&&row.every(finite)&&
      row[1]>=0&&row[2]>=0&&row[3]>=row[2],'passive sampler ordinal or finite same-clock interval differs');
    return {ordinal,callbackLagMs:row[2]-row[1],synchronousDispatchMs:row[3]-row[2]};
  });
  return {protocol:'r0040-passive-sampler-inspection/1',status:'OBSERVED',clockDomain:raw.clockDomain,
    timeOriginMs:raw.timeOriginMs,count:raw.rows.length,intervals,
    interpretation:'Same isolated-world callback and synchronous-dispatch intervals with uncalibrated instrumentation overhead; no cadence, frame association or product acceptance.'};
}

module.exports={ORIGINAL_SHA256,installSamplerBuffer,instrumentStart,reverseStart,inspectSampler};
