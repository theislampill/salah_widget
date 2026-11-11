#!/usr/bin/env node
'use strict';
// Regression for the collector's native CSS-consumer admission. The clock
// representation comes from the unchanged application producer, not a second
// hand-authored timestamp convention. An optional retained-artifact argument
// re-evaluates observations without claiming another native execution.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const owner=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const moduleFile=process.argv[3]?path.resolve(process.argv[3]):path.join(__dirname,'r0017-phase2-controls.cjs');
const {review}=require(moduleFile);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const tests=[];
function check(name,fn){try{const detail=fn();tests.push({name,passed:true,detail:detail??null});}catch(error){tests.push({name,passed:false,error:String(error.stack||error)});}}
const start=owner.indexOf('function partsInTz(ms){'),end=owner.indexOf('// Strict Gregorian coordinate',start);
assert(start>=0&&end>start,'Exact application date producer must remain identifiable');
const clock={Intl,Date,tz:'Asia/Riyadh',_partsFormatter:null,_partsFormatterZone:null,pad:n=>String(n).padStart(2,'0')};
vm.createContext(clock);vm.runInContext(owner.slice(start,end)+';this.parts=partsInTz(1788773400000);',clock);
const qaOwner=owner.slice(owner.indexOf('window.qaState=function(){'));
const expression=/\bsim:(`[^`]+`)/.exec(qaOwner);
assert(expression,'Exact qaState.sim projection must remain identifiable');
clock.n=clock.parts;const sim=vm.runInContext(expression[1],clock);
function surface(){return {qa:{sim,sunEl:71.4},pulseRaw:'0.9682',pulse:0.9682,transforms:['.suncorner .corona','.suncorner .rays'].map(selector=>({selector,count:1,raw:'matrix(0.9682, 0, 0, 0.9682, -300, -300)',error:null,matrix:{is2D:true,m11:0.9682,m12:0,m21:0,m22:0.9682}}))};}
check('actual application producer is admitted',()=>{assert.equal(review.pulseConsumer(surface()),true);return {producerSim:sim,ownerSha256:sha(owner)};});
check('other date representation is not silently accepted',()=>{const s=surface();s.qa.sim='2026-09-07 12:30';assert.equal(review.pulseConsumer(s),false);});
check('different observation minute is rejected',()=>{const s=surface();s.qa.sim=sim.replace('12:30','12:31');assert.equal(review.pulseConsumer(s),false);});
check('missing CSS property is rejected',()=>{const s=surface();s.pulseRaw='';assert.equal(review.pulseConsumer(s),false);});
check('nonpositive pulse is rejected',()=>{const s=surface();s.pulseRaw='0';s.pulse=0;assert.equal(review.pulseConsumer(s),false);});
check('unconsumed numeric property is rejected',()=>{const s=surface();s.transforms[1].matrix.m11=1;assert.equal(review.pulseConsumer(s),false);});
check('missing real consumer is rejected',()=>{const s=surface();s.transforms.pop();assert.equal(review.pulseConsumer(s),false);});
check('duplicate real consumer is rejected',()=>{const s=surface();s.transforms[1].count=2;assert.equal(review.pulseConsumer(s),false);});
check('nonfinite DOM matrix is rejected',()=>{const s=surface();s.transforms[1].matrix.m22=NaN;assert.equal(review.pulseConsumer(s),false);});
check('three dimensional or rotated matrices are rejected',()=>{for(const key of ['is2D','m12']){const s=surface();s.transforms[0].matrix[key]=key==='is2D'?false:0.2;assert.equal(review.pulseConsumer(s),false);}});
check('native Firefox float precision is admitted within existing tolerance',()=>{const s=surface();for(const t of s.transforms)t.matrix.m11=t.matrix.m22=0.9682000279426575;assert.equal(review.pulseConsumer(s),true);});
if(process.argv[2]){
 const archive=path.resolve(process.argv[2]),summary=JSON.parse(fs.readFileSync(path.join(archive,'summary.json'),'utf8'));
 const retained=[];
 for(const row of summary.cases){
  if(row.kind==='motion'){const data=row.control?.data;for(const [name,s]of [['before',data?.before],['after',data?.after],...(data?.observations||[]).map((o,i)=>['callback-'+i,o.surface])])retained.push({case:row.name,point:name,surface:s});}
  if(row.nativeNoPreferenceBaseline?.data)retained.push({case:row.name,point:'public-native-no-preference',surface:row.nativeNoPreferenceBaseline.data});
 }
 check('all retained actual native motion surfaces satisfy the source-bound predicate',()=>{assert.equal(retained.length,50);const rejected=retained.filter(x=>!review.pulseConsumer(x.surface)).map(({case:c,point})=>({case:c,point}));assert.deepEqual(rejected,[]);return {runId:summary.runId,surfaces:retained.length,nativeExecutionsInThisCommand:0};});
 check('actual narrow oracle caller preserves every retained expected outcome',()=>{
  const plans=JSON.parse(fs.readFileSync(path.join(archive,'phase2-plan.json'),'utf8')).plans;
  const declared=JSON.parse(fs.readFileSync(path.join(archive,'denominator.json'),'utf8'));
  const rows=summary.cases.filter(r=>r.kind==='motion'),reanalysis=[];assert.equal(rows.length,12);
  for(const old of rows){const row=structuredClone(old),plan=plans.find(p=>p.id===row.name.slice(row.engine.length+1));assert(plan);review.oracle(plan,row.control,row,declared);const failed=Object.keys(row.checks).filter(k=>row.checks[k]===false);reanalysis.push({case:row.name,originalStatus:old.status,originalSmokeStatus:old.smoke.status,failedChecks:failed});}
  assert(reanalysis.every(r=>r.failedChecks.length===0),JSON.stringify(reanalysis));
  return {scope:'New local reanalysis of retained native observations through the actual oracle caller; original result bytes and statuses are unchanged',nativeExecutionsInThisCommand:0,rows:reanalysis};
 });
 check('exact public caller expression admits the retained no-preference consumers',()=>{
  const expression=/c\.actualNoonConsumer=([^;\n]+);/.exec(fs.readFileSync(moduleFile,'utf8'));assert(expression,'Exact public consumer expression must remain identifiable');
  const evaluate=new Function('x','pulseConsumer','return '+expression[1]);
  const rows=summary.cases.filter(r=>r.nativeNoPreferenceBaseline?.data);assert.equal(rows.length,2);
  const reanalysis=rows.map(r=>({case:r.name,originalStatus:r.status,originalBaselineStatus:r.nativeNoPreferenceBaseline.status,consumer:evaluate(r.nativeNoPreferenceBaseline.data,review.pulseConsumer),otherBaselineChecks:Object.entries(r.nativeNoPreferenceBaseline.checks).filter(([k])=>k!=='actualNoonConsumer').every(([,v])=>v===true)}));
  assert(reanalysis.every(r=>r.consumer&&r.otherBaselineChecks));
  return {scope:'Exact changed caller expression applied to already-captured native baseline data; no new browser/timing/screenshot claim',nativeExecutionsInThisCommand:0,rows:reanalysis};
 });
}
console.log(JSON.stringify({schema:'r0017-motion-consumer-controls/v1',moduleSha256:sha(fs.readFileSync(moduleFile)),producerSim:sim,passed:tests.filter(x=>x.passed).length,failed:tests.filter(x=>!x.passed).length,tests},null,2));
process.exitCode=tests.every(x=>x.passed)?0:1;
