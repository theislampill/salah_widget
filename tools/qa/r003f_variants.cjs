'use strict';
// Issue 140 E.1. These are private test-server response transforms only.
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const hash = data => createHash('sha256').update(data).digest('hex');
const variants = ['B0','B0-T','B1c','B1c-T','B4','B4-T','B6','B6-T'];
const originalGain = ' const gain=total>0?Math.min(1,ceiling/total):0;';
const originalOutput = ' for(let i=0;i<out.length;i++)out[i]=refined[i]*gain;';
const ruleSource = {
  B0: originalGain,
  B1c: ' const gain=Math.max(g0,Math.min(0.6,2*g0));',
  B4: ` const yy=new Float64Array(coverage.length);
 for(let i=0;i<yy.length;i++)for(let k=0;k<3;k++)yy[i]+=Y[k]*refined[3*i+k];
 const sorted=yy.slice().sort(),rank=.995*(yy.length-1),lo=Math.floor(rank);
 const p=sorted[lo]+(rank-lo)*(sorted[Math.ceil(rank)]-sorted[lo]);
 let sum=0,n=0;
 for(let i=0;i<yy.length;i++)if(coverage[i]>.5&&yy[i]>=.25*p){sum+=yy[i]/coverage[i];n++;}
 const gain=n?Math.max(g0,Math.min(.5,.055/(sum/n))):g0;`,
  B6: ' const gain=Math.max(g0,Math.min(.6,Math.max(1.5*g0,.19)));'
};
const toneSource = ` const tint=[.94,1,1.10],ty=Y[0]*tint[0]+Y[1]*tint[1]+Y[2]*tint[2];
 for(let i=0;i<coverage.length;i++){
  const j=3*i,yl=Y[0]*(refined[j]*gain)+Y[1]*(refined[j+1]*gain)+Y[2]*(refined[j+2]*gain);
  for(let k=0;k<3;k++)out[j+k]=Math.max(0,.4*(refined[j+k]*gain)+.6*yl*tint[k]/ty);
 }`;
function exactly(source, oldText, next) {
  assert.equal(source.split(oldText).length,2,'missing or repeated calendar source anchor');
  return source.replace(oldText,()=>next);
}
function variantSource(source,name) {
  assert.ok(variants.includes(name),'unknown calendar variant');
  const [rule,tone]=name.split('-');
  if(rule!=='B0')source=exactly(source,originalGain,originalGain.replace('gain=','g0=')+'\n'+ruleSource[rule]);
  if(tone)source=exactly(source,originalOutput,toneSource);
  return source;
}
const pinPattern = /const MOON_WORKER_PIN=(\{[^\n]+?\});/g;
const workerPattern = /(window\.SalahMoonRuntime\?\.installWorkerSource\()("(?:[^"\\]|\\.)*")(\);)/g;
function unpack(html) {
  const workers=[...html.matchAll(workerPattern)], pins=[...html.matchAll(pinPattern)];
  assert.equal(workers.length,1,'worker install literal');
  assert.equal(pins.length,1,'worker pin');
  const worker=JSON.parse(workers[0][2]), pin=JSON.parse(pins[0][1]);
  assert.deepEqual(pin,{bytes:Buffer.byteLength(worker),sha256:hash(worker)},'worker pin drift');
  return {worker,pin};
}
function renderVariant(html,source,name) {
  const before=unpack(html), next=variantSource(source,name);
  const worker=exactly(before.worker,source,next);
  let output=exactly(html,source,next);
  // B0 must be bit-identical, including the builder's escaping conventions.
  if(name!=='B0'){
    output=output.replace(workerPattern,(_all,start,_literal,end)=>start+JSON.stringify(worker).replace(/<\/script/gi,'<\\/script')+end);
    output=output.replace(pinPattern,()=> 'const MOON_WORKER_PIN='+JSON.stringify({bytes:Buffer.byteLength(worker),sha256:hash(worker)})+';');
  }
  const checked=unpack(output);
  assert.equal(checked.worker,worker); assert.equal(checked.worker.split(next).length,2);
  assert.equal(output.split(next).length,2);
  return {html:output,identity:{variant:name,indexSha256:hash(output),sourceSha256:hash(next),worker:checked.pin}};
}
module.exports={variants,variantSource,renderVariant,unpack,hash};
