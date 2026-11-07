#!/usr/bin/env node
'use strict';
// Exercise the real orchestration caller with explicit simulated boundaries.
// No native process, HTTP server, network request or qualification credit.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),crypto=require('node:crypto');
const file=path.join(__dirname,'r0017-phase2-controls.cjs'),source=fs.readFileSync(file,'utf8'),root=path.resolve(__dirname,'../..');
const requested=['chromium-matching-tomorrow','chromium-public-healthy-no-preference','chromium-public-healthy-reduce','firefox-public-healthy-reduce'];
const results=[];
async function check(name,fn){try{results.push({name,passed:true,detail:await fn()??null});}catch(e){results.push({name,passed:false,error:String(e.stack||e)});}}
async function execute(options){
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'r0017-selection-')),launches=[],writes=new Map(),localProcess={platform:'win32',exitCode:0};let identified=0;
 const module={exports:{}};
 const context={require,module,exports:module.exports,Buffer,URL,URLSearchParams,performance,console,process:localProcess,WebSocket:function(){},__filename:file,__dirname};
 vm.runInNewContext(source+`\nvariantServer=async()=>({origin:'http://simulated.invalid/',close:async()=>{}});
 collectProbe=async(api,server,p,engine)=>{api.testLaunch({name:engine+'-'+p.id,engines:p.engines,group:p.group});return true;};
 collectPublic=async(api,engine,preference)=>{api.testLaunch({name:engine+'-public-healthy-'+preference,group:'public'});return true;};
 observedPublicReadback=async()=>({passed:true,simulated:true});`,context,{filename:file});
 const api={ROOT:root,OUT:out,EXPECTED:'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b',result:{cases:[]},sha:b=>crypto.createHash('sha256').update(b).digest('hex'),
  write:(p,v)=>writes.set(path.relative(out,p),JSON.parse(JSON.stringify(v))),identify:()=>{identified++;},remainingBudgetMs:()=>960000,operationTimeout:n=>n,launchBlock:()=>null,publicReadback:async()=>({simulated:true}),
  notAttempted:(p,reason)=>api.result.cases.push({...p,status:'NOT_ATTEMPTED',reason}),
  testLaunch:p=>{launches.push(JSON.parse(JSON.stringify(p)));api.result.cases.push({name:p.name,status:'SIMULATED_BOUNDARY_ONLY'});}};
 try{await module.exports.run(api,options);return {result:JSON.parse(JSON.stringify(api.result)),launches,identified,exitCode:localProcess.exitCode,plan:writes.get('phase2-plan.json')};}
 catch(error){error.identified=identified;error.launches=launches;throw error;}
 finally{fs.rmSync(out,{recursive:true,force:true});}
}
async function rejected(options){let observed;try{await execute(options);}catch(e){observed=e;}assert(observed,'Invalid explicit selection must throw');assert.equal(observed.identified,0);assert.deepEqual(observed.launches,[]);return String(observed.message);}
(async()=>{
 await check('actual caller dispatches only the four explicitly selected sessions',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.deepEqual(x.launches.map(r=>r.name),requested);assert.equal(x.result.plannedCount,4);assert.equal(x.result.attemptedCount,4);assert.equal(x.result.notAttemptedCount,0);assert.equal(x.exitCode,0);assert.deepEqual(x.plan.plans.map(p=>({id:p.id,engines:p.engines})),[{id:'matching-tomorrow',engines:['chromium']}]);assert.equal(x.plan.publicContexts.length,3);return {nativeExecutions:0,simulatedLaunches:x.launches};});
 await check('document count includes only the selected no-preference baseline',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.equal(x.result.documentPlan.nativeSessions,4);assert.equal(x.result.documentPlan.topLevelNavigations,5);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,1);assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,0);assert.equal(x.result.documentPlan.calendarTargetDocuments,0);});
 await check('unselected group members are explicit and receive no attempt or PASS',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.equal(x.result.selection.notSelected.length,30);assert(x.result.selection.notSelected.includes('firefox-public-healthy-no-preference'));assert(x.result.selection.notSelected.every(n=>!x.result.cases.some(r=>r.name===n)));assert.deepEqual(x.result.selection.requestedCaseNames,requested);});
 await check('explicit argument order cannot silently reorder the reviewed population',async()=>{const x=await execute({groups:'current,public',cases:requested.slice().reverse().join(',')});assert.deepEqual(x.launches.map(r=>r.name),requested);});
 await check('omitting selection preserves the original 36-session population',async()=>{const x=await execute({groups:'current,public,calendar-diagnostics'});assert.equal(x.launches.length,36);assert.equal(x.result.documentPlan.topLevelNavigations,38);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,2);assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,2);assert.equal(x.result.documentPlan.calendarTargetDocuments,2);});
 await check('current obligation allocation launches only the two Chromium public preferences',async()=>{const names=requested.slice(1,3),x=await execute({groups:'public',cases:names.join(',')});assert.deepEqual(x.launches.map(r=>r.name),names);assert.equal(x.result.plannedCount,2);assert.equal(x.result.attemptedCount,2);assert.equal(x.result.notAttemptedCount,0);assert.equal(x.result.documentPlan.topLevelNavigations,3);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,1);assert.deepEqual(x.plan.plans,[]);assert.deepEqual(x.result.selection.notSelected,['firefox-public-healthy-no-preference','firefox-public-healthy-reduce']);return {nativeExecutions:0,simulatedLaunches:x.launches};});
 await check('duplicate case is refused before source setup or launch',()=>rejected({groups:'current,public',cases:requested[0]+','+requested[0]}));
 await check('unknown case is refused before source setup or launch',()=>rejected({groups:'current,public',cases:'chromium-not-a-case'}));
 await check('empty explicit selection is refused before source setup or launch',()=>rejected({groups:'current,public',cases:''}));
 await check('empty token is refused before source setup or launch',()=>rejected({groups:'current,public',cases:requested[0]+','}));
 await check('case outside selected groups is refused before source setup or launch',()=>rejected({groups:'current',cases:'firefox-public-healthy-reduce'}));
 console.log(JSON.stringify({schema:'r0017-phase2-selection-controls/v1',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),nativeExecutions:0,passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results},null,2));process.exitCode=results.every(x=>x.passed)?0:1;
})().catch(e=>{console.error(e);process.exitCode=1;});
