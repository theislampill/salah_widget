'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {run}=require('../tools/qa/r002f-transaction/experiment.cjs');
let receipt;
const results=()=>receipt??=run();
const sinks=s=>[s.bg,s.disc,s.mask,s.frame,s.receipt];
const rgba=s=>[s.bg,s.disc];
const find=(rows,name)=>{const row=rows.find(x=>x.name===name);assert(row,name);return row;};

test('existing detail-first fault mixes generations; staged normal output matches the independent real-owner result',async()=>{
 const {actualOwnerControl:red,actualOwnerSuccess:normal,arms,established}=await results();
 assert.equal(red.after.bg,red.before.bg);
 assert.equal(red.after.disc,normal.after.disc);
 assert.notEqual(red.after.disc,red.before.disc);
 assert.equal(red.after.mask,red.before.mask);
 assert.equal(red.after.receipt,red.before.receipt);
 assert.equal(red.after.retained,true);
 assert.notEqual(normal.after.bg,red.before.bg);
 for(const rows of [arms,established]){
  const good=find(rows,'success');
  assert(good.after.visible&&good.after.bg&&good.after.disc);
  assert.deepEqual(rgba(good.after),rgba(normal.after));
  assert.notEqual(good.after.bg,good.before.bg);
  assert.notEqual(good.after.disc,good.before.disc);
  assert.notEqual(good.after.mask,good.before.mask);
  assert.notEqual(good.after.receipt,good.before.receipt);
  assert.equal(good.after.frame,good.after.receipt);
  for(const e of good.events)assert.deepEqual(sinks(e),sinks(e.event==='after-select'?good.after:good.before),e.event);
 }
});

test('every preselector failure preserves all four sinks; a postselector throw retains the complete successor',async()=>{
 const {arms,established}=await results();
 for(const rows of [arms,established]){
  const normal=find(rows,'success');
  for(const name of ['background-upload','detail-upload','style-attach','background-attach','detail-attach','before-select']){
   const a=find(rows,name);assert(a.after.visible&&a.after.retained);
   assert.deepEqual(sinks(a.after),sinks(a.before),name);
   assert.equal(a.after.id,a.before.id,name);
   assert(a.events.some(e=>e.event===name));
   for(const e of a.events)assert.deepEqual(sinks(e),sinks(a.before),name+' / '+e.event);
   assert.equal(a.legacyReadsInUpdate,0);
  }
  const committed=find(rows,'after-select');
  assert.deepEqual(committed.after,normal.after);
  assert.deepEqual(sinks(committed.events.at(-1)),sinks(normal.after));
 }
});

test('superseded attempts cannot select, retain an expired generation or erase the reentrant winner',async()=>{
 const {arms,established}=await results();
 for(const rows of [arms,established]){
  for(const name of ['cloud','weather','epoch','adoption','geometry','expiry']){
   const a=find(rows,name);
   assert.equal(a.after.id,null,name+' must use existing withdrawal/successor route');
   assert.equal(a.after.retained,false,name);
   assert.notEqual(a.after.receipt,a.before.receipt,name);
   assert(!a.events.some(e=>e.event==='after-select'),name);
   assert(a.legacyReadsInUpdate>0,name+' must exercise the ordinary successor');
  }
  const refined=find(rows,'refined');
  assert(refined.after.refined&&!refined.after.visible);
  assert.deepEqual(rgba(refined.after),[null,null]);
  assert(!refined.events.some(e=>e.event==='after-select'));
  const nested=find(rows,'nested'),commits=nested.events.filter(e=>e.event==='after-select');
  assert.equal(commits.length,1);
  assert.deepEqual(sinks(commits[0]),sinks(nested.after));
  assert.equal(nested.after.receipt,rows===arms?22000:42500);
  assert.equal(nested.after.retained,false);
  const reentered=find(rows,'after-select-nested');
  assert.equal(reentered.events.filter(e=>e.event==='after-select').length,2);
  assert.equal(reentered.after.receipt,rows===arms?42500:62600);assert.equal(reentered.after.connectedSheets,1);
  const failedInner=find(rows,'after-select-inner-fails');
  assert.equal(failedInner.events.filter(e=>e.event==='after-select').length,1);
  assert.deepEqual(sinks(failedInner.after),sinks(find(rows,'success').after));
  assert.equal(failedInner.after.retained,true);assert.equal(failedInner.after.connectedSheets,1);
  for(const a of rows)assert.equal(a.diagnosticExtraReads,0);
 }
});

test('real lunar presenter guards already adopted material across epoch, replacement and hide without publishing on reads',async()=>{
 const {runtimeAdmission:r}=await results();
 assert.equal(r.current,true);
 assert.deepEqual(r.before,r.after);
 assert.equal(r.revoked,false);assert.equal(r.denied,true);
 assert.equal(r.reused,false);assert(r.replacement>r.oldToken);
 assert.equal(r.hiddenLease,true);
});

test('combined hidden reuse grants only the re-admitted record a transaction lease over the original material',async()=>{
 const {combinedCustody:good,missingCombinedBinding:control}=await results();
 for(const a of [good,control]){
  assert.equal(a.reuses,1);assert.equal(a.extraInitial,0);
  assert.equal(a.hidden,false);assert.equal(a.oldCurrent,false);
 }
 assert(good.restoredCurrent&&good.restoredToken>good.originalToken);
 assert.equal(good.seen.length,2);
 assert.deepEqual(good.seen[0],good.seen[1]);
 assert.equal(good.seen[1].same,true);
 assert.deepEqual(good.seen[1].values,[.125,.0625,.75]);
 assert.equal(control.restoredToken,null);
 assert.equal(control.restoredCurrent,false);
});

test('selected authority revokes before the 100 ms throttle and in the actual owning producer task',async()=>{
 const {revocations}=await results();
 for(const a of revocations){
  assert(a.before.id&&a.before.ready&&a.before.disc);
  if(a.name.endsWith('cleanupSuccessor')){
   assert(a.after.id&&a.after.id!==a.before.id&&a.after.ready);
   assert.equal(a.after.retained,false);assert.equal(a.after.receipt,62700);continue;
  }
  if(a.name.includes('-owner-')){
   assert.equal(a.afterProducer.id,null,a.name);
   assert.equal(a.afterProducer.ready,false,a.name);
  }
  assert.equal(a.after.id,null,a.name);
  assert.equal(a.after.ready,false,a.name);
  assert.equal(a.after.retained,false,a.name);
  assert.equal(a.after.frame,null,a.name);
  assert.equal(a.after.svgRouteExposed,true,a.name);
  assert.equal(a.after.ordinaryBackground,'hidden');assert.equal(a.after.ordinaryDisc,'hidden');
  if(a.name.endsWith('pending'))assert(a.pending>0,a.name);
 }
});

test('leased replacement obtains the same actual solar anchor without an adopting Moon surface read',async()=>{
 const {runtimeAdmission:r,arms}=await results();
 const {stagedAnchor,ordinaryAnchor,stagedWrites,ordinaryWrites}=r.actualAnchor;
 assert.deepEqual({...stagedAnchor},{...ordinaryAnchor});
 assert.equal(stagedAnchor.x,25);assert.equal(stagedAnchor.y,36);
 assert.equal(stagedWrites,0);assert.equal(ordinaryWrites,1);
 assert.deepEqual(find(arms,'success').solarAnchorReadModes,[false]);
});
