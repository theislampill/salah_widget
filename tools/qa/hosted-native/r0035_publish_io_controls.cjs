'use strict';
// Synthetic filesystem/history controls. No browser or original native capture.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const here=__dirname,root=path.resolve(here,'../../..');
const original=fs.readFileSync(path.join(root,'tools/r0035/live_lab.mjs'));
const clone=value=>JSON.parse(JSON.stringify(value));
async function module_(){
  const file=path.join(here,'r0035_publish_io.mjs');
  assert.ok(fs.existsSync(file),'publish file/history adapter not implemented');
  return import(pathToFileURL(file).href);
}
function fixture(){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r0035-publish-io-'));
  const base=path.join(dir,'base'),out=path.join(dir,'out');
  for(const p of [base,out]){fs.mkdirSync(path.join(p,'tools/r0035'),{recursive:true});fs.writeFileSync(path.join(p,'tools/r0035/live_lab.mjs'),original);}
  return {dir,base,out,live:path.join(out,'tools/r0035/live_lab.mjs'),close(){fs.rmSync(dir,{recursive:true,force:true});}};
}
function history(){
  return {start:100,end:200,initial:{status:'active',tier:'refined',identity:'prior'},overflow:false,
    events:[{at:110,kind:'status',epoch:2,tier:'refined',identity:'prior',reason:'preparing accepted frame'},
      {at:111,kind:'owner',epoch:2,tier:'refined',identity:'current',r0035Publish:{
        protocol:'r0035-publish-decision/1',previousEpoch:1,hadSource:true,evaluatedMask:31,equalMask:15,
        wasPrepared:true,samplePending:false,preparingEpoch:null,latestQueued:false}},
      {at:130,kind:'status',epoch:2,tier:'refined',identity:'current',reason:'prepared'},
      {at:140,kind:'publication',epoch:2,tier:'refined',identity:'current',utcMs:1,ageMs:0,changed:true,nonempty:true,writes:1,id:'s'}]};
}
function reports(){return ['main','unmodified','mitigated'].map(arm=>({arm,commit:'original-source',root:'/synthetic/'+arm,
  scope:'derived-r0035-publish-decision/1',trace:{publication:arm==='main'?null:history()}}));}

test('one exact file transformation is reversible and leaves original bytes intact',async()=>{
  const m=await module_(),f=fixture();try{
    const before=fs.readFileSync(path.join(f.base,'tools/r0035/live_lab.mjs'));
    const receipt=m.transformFiles('derive',f.base,f.out);
    assert.equal(receipt.protocol,'r0035-publish-file-transform/1');
    assert.equal(receipt.identity.reference.sha256,'11717de894a630f99b5d661ff35c4200b355f4486c533e0e31dbc39e67a6a02a');
    assert.equal(receipt.identity.derived.sha256,'a6ab675b9436d080836c82c1aa6d1d4bbcd28d4e4fac03b84712fed61e8a6672');
    assert.deepEqual(m.transformFiles('check',f.base,f.out),receipt);
    assert.deepEqual(fs.readFileSync(path.join(f.base,'tools/r0035/live_lab.mjs')),before);
    assert.throws(()=>m.transformFiles('derive',f.base,f.out));
  }finally{f.close();}
});

test('changed input or derived bytes refuse without copied identity authority',async()=>{
  const m=await module_();for(const phase of ['before','after']){const f=fixture();try{
    if(phase==='before')fs.appendFileSync(path.join(f.base,'tools/r0035/live_lab.mjs'),'\n');
    else {m.transformFiles('derive',f.base,f.out);fs.appendFileSync(f.live,'\n');}
    assert.throws(()=>m.transformFiles(phase==='before'?'derive':'check',f.base,f.out));
  }finally{f.close();}}
});

test('source aliases, output hardlinks and symlink ancestry refuse before any input write',async()=>{
  const m=await module_();for(const kind of ['same-root','hardlink','symlink','dotdot']){const f=fixture();try{
    const source=path.join(f.base,'tools/r0035/live_lab.mjs');let base=f.base,out=f.out;
    if(kind==='same-root')out=base;
    if(kind==='hardlink'){fs.unlinkSync(f.live);fs.linkSync(source,f.live);}
    if(kind==='symlink'){fs.unlinkSync(f.live);fs.symlinkSync(source,f.live);}
    if(kind==='dotdot')out=f.out+'/../out';
    assert.throws(()=>m.transformFiles('derive',base,out));assert.deepEqual(fs.readFileSync(source),original);
  }finally{f.close();}}
});

test('history retains exact executed prefix and separate replacement activity',async()=>{
  const m=await module_(),pub=history(),copy=clone(pub),out=m.inspectPublication(pub);
  assert.deepEqual(pub,copy);assert.equal(out.ownerCount,1);assert.equal(out.eventCount,4);
  assert.equal(out.owners[0].eventIndex,1);assert.equal(out.owners[0].decision.decisiveTerm,'cloudPixels');
  assert.equal(out.owners[0].decision.kind,'SOURCE_PRESENT_AT_REPLACEMENT');
  assert.deepEqual(out.owners[0].decision.terms.map(row=>row.outcome),
    ['EQUAL','EQUAL','EQUAL','EQUAL','DIFFERENT','NOT_EVALUATED','NOT_EVALUATED']);
  assert.equal(out.cpuTiming,'NOT_MEASURED');assert.equal(out.speed,'NOT_ESTABLISHED');
});

test('reentrant clearing is decoded at its later boundary without earlier-owner inference',async()=>{
  const m=await module_(),pub=history();pub.events[1].r0035Publish.hadSource=false;
  const out=m.inspectPublication(pub);assert.equal(out.owners[0].decision.kind,'SOURCE_ABSENT_AT_REPLACEMENT');
  assert.equal(out.owners[0].decision.decisiveTerm,'cloudPixels');
});

test('late reentry is incomplete rather than reassigned to a convenient epoch',async()=>{
  const m=await module_(),pub=history();pub.events[1].r0035Publish.previousEpoch=0;
  const before=clone(pub);assert.throws(()=>m.inspectPublication(pub),/epoch/);assert.deepEqual(pub,before);
});

test('zero owner history remains explicit without inventing missing comparisons',async()=>{
  const m=await module_(),pub=history();pub.events=[];
  const out=m.inspectPublication(pub);assert.equal(out.ownerCount,0);assert.deepEqual(out.owners,[]);
  assert.equal(out.questionStatus,'NO_OWNER_EVENT_OBSERVED');
});

test('overflow, missing owner records and supplemental fields on another event refuse',async()=>{
  const m=await module_();for(const change of [p=>p.overflow=true,p=>delete p.events[1].r0035Publish,
    p=>p.events[0].r0035Publish=clone(p.events[1].r0035Publish),p=>p.events.length=16385]){
    const pub=history();change(pub);assert.throws(()=>m.inspectPublication(pub));
  }
  for(const pub of [null,{},[],{...history(),events:null}])assert.throws(()=>m.inspectPublication(pub));
});

test('event chronology, owner population and strict kind schema cannot be silently repaired',async()=>{
  const m=await module_();for(const change of [p=>p.events[1].at=99,p=>p.events[1].at=201,
    p=>p.events[1].at=109,p=>p.events[2].epoch=1,p=>p.events[1].epoch=1.5,
    p=>p.events[2].kind='unknown',p=>p.events.splice(2,0,clone(p.events[1])),p=>p.end=NaN]){
    const pub=history();change(pub);assert.throws(()=>m.inspectPublication(pub));
  }
});

test('complete three-arm history retains exact trial identity and baseline absence',async()=>{
  const m=await module_(),input=reports(),copy=clone(input),out=m.inspectReports(input);
  assert.deepEqual(input,copy);assert.equal(out.status,'COMPLETE');assert.equal(out.nativeQualification,'UNCHANGED_ORIGINAL_REPORT_ONLY');
  assert.deepEqual(out.arms.map(r=>r.arm),['main','unmodified','mitigated']);assert.equal(out.arms[0].status,'BASELINE_NO_LAB');
  assert.equal(out.arms[1].root,input[1].root);assert.equal(out.arms[1].scope,input[1].scope);
  assert.equal(out.totalOwners,2);assert.equal(out.speed,'NOT_ESTABLISHED');
  for(const change of [r=>r.pop(),r=>r.reverse(),r=>r[1].arm='main',r=>r[0].trace.publication=history(),
    r=>r[2].trace.publication=null,r=>r[1].scope='independent-reconstruction',r=>r[1].commit='',r=>delete r[1].root]){
    const bad=reports();change(bad);assert.throws(()=>m.inspectReports(bad));
  }
});
