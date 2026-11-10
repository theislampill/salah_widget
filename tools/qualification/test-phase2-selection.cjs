#!/usr/bin/env node
'use strict';
// Exercise the real orchestration caller with explicit simulated boundaries.
// No native process, HTTP server, network request or qualification credit.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),crypto=require('node:crypto');
const file=path.join(__dirname,'r0017-phase2-controls.cjs'),source=fs.readFileSync(file,'utf8'),root=path.resolve(__dirname,'../..');
const waningCase='chromium-diagnostic-calendar-waning-c12';
const requested=['chromium-matching-tomorrow','chromium-public-healthy-no-preference','chromium-public-healthy-reduce','firefox-public-healthy-reduce'];
const results=[];
async function check(name,fn){try{results.push({name,passed:true,detail:await fn()??null});}catch(e){results.push({name,passed:false,error:String(e.stack||e)});}}
async function execute(options,passiveOptions){
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'r0017-selection-')),launches=[],writes=new Map(),localProcess={platform:'win32',exitCode:0};let identified=0;
 const module={exports:{}};
 const context={require,module,exports:module.exports,Buffer,URL,URLSearchParams,performance,console,process:localProcess,WebSocket:function(){},__filename:file,__dirname};
 vm.runInNewContext(source+`\nvariantServer=async()=>({origin:'http://simulated.invalid/',close:async()=>{}});
 collectProbe=async(api,server,p,engine,declared)=>{api.testLaunch({name:engine+'-'+p.id,engine,engines:p.engines,group:p.group,kind:p.kind,preference:p.preference,history:p.history,responseOverrides:Object.keys(p.overrides),originalDenominator:{cases:declared.length,assertions:declared.reduce((n,x)=>n+x[1],0)}});return true;};
 collectPublic=async(api,engine,preference)=>{api.testLaunch({name:engine+'-public-healthy-'+preference,group:'public'});return true;};
 observedPublicReadback=async()=>({passed:true,simulated:true});`,context,{filename:file});
 const api={ROOT:root,OUT:out,EXPECTED:'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b',result:{cases:[]},sha:b=>crypto.createHash('sha256').update(b).digest('hex'),
  startSession:()=>{throw Error('Native session forbidden in selection control');},
  preload:()=>{throw Error('Preload execution forbidden in selection-only control');},
  write:(p,v)=>writes.set(path.relative(out,p),JSON.parse(JSON.stringify(v))),identify:()=>{identified++;},remainingBudgetMs:()=>960000,operationTimeout:n=>n,launchBlock:()=>null,publicReadback:async()=>({simulated:true}),
  notAttempted:(p,reason)=>api.result.cases.push({...p,status:'NOT_ATTEMPTED',reason}),
  testLaunch:p=>{launches.push(JSON.parse(JSON.stringify(p)));api.result.cases.push({name:p.name,status:'SIMULATED_BOUNDARY_ONLY'});}};
 if(passiveOptions)require('./r0017-windows-passive.cjs').configure(api,passiveOptions);
 try{await module.exports.run(api,options);return {result:JSON.parse(JSON.stringify(api.result)),launches,identified,exitCode:localProcess.exitCode,plan:writes.get('phase2-plan.json')};}
 catch(error){error.identified=identified;error.launches=launches;throw error;}
 finally{fs.rmSync(out,{recursive:true,force:true});}
}
async function rejected(options){let observed;try{await execute(options);}catch(e){observed=e;}assert(observed,'Invalid explicit selection must throw');assert.equal(observed.identified,0);assert.deepEqual(observed.launches,[]);return String(observed.message);}
// A simulated complete narrow-observation envelope reaches the real receipt
// consumer. These checks concern genealogy only and provide no native credit.
function diagnosticReceipt(id,attempted){
 const api=require(file),catalog=api.prepare({ROOT:root,sha:b=>crypto.createHash('sha256').update(b).digest('hex')}),p=catalog.plans.find(p=>p.id===id);
 assert(p,'The real selected diagnostic plan must exist');
 const reason='required scene readiness deadline exceeded',initialHash='lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&simWx=0&tz=Asia/Riyadh&qa=1',want=p.hash+'&tz=Asia/Riyadh&qa=1',run='simulated-genealogy-control';
 const attempt=(n,hash,ready)=>{const f={run,attempt:n,hash,mode:'healthy',documentId:n===1?'00000000-0000-0000-0000-000000000001':'00000000-0000-0000-0000-000000000002',sourceSha256:p.expectedIndexSha256,consoleErrors:[],state:'ready',error:null,storageIsolated:true,clockFixed:true,fetchIntercepted:true,bridgeSha256:'1'.repeat(64)};
  return {attempt:n,hash,mode:'healthy',result:ready?'ready':'timeout',reason:ready?null:reason,fixture:f,...(ready?{documentId:f.documentId,sourceSha256:p.expectedIndexSha256}:{})};};
 const list=[attempt(1,initialHash,attempted)];if(attempted){const last=attempt(2,want,false);last.calendarView={schema:'r0017-calendar-stage/v1',attempt:2,hash:want,budgetMs:8000,styleRestored:true};list.push(last);}
 const entries=catalog.declared.map(([name,expected])=>({name,expected,assertions:0,state:attempted&&name===p.caseName?'missing':'pending',reason:attempted&&name===p.caseName?reason:null}));
 const smoke={status:'INCOMPLETE',pass:0,fail:0,skip:attempted?1:0,required:{cases:entries,executed:0,failed:0,missing:entries.map(x=>x.name)},fixture:{mode:'healthy',run,attempts:list}};
 const data={targetAttempted:attempted,targetName:p.caseName,helperRestored:true,observerCalls:attempted?1:0,originalAttempts:list,
  prerequisite:{accepted:attempted,expectedSourceSha:p.expectedIndexSha256,originalAttempt:list[0],originalResult:{hasWindow:attempted,reason:attempted?null:reason}},
  boundaryReads:attempted?[{phase:'after-original-loadUntil-resolved-before-scene-continuation',observedCall:1,input:{hash:p.hash,boundMs:8000},expectedHash:want,sourceSha256:p.expectedIndexSha256,ownerAccepted:true,ownerStillExact:true,documentId:list[1].fixture.documentId,originalAttemptResult:'timeout',originalResult:{reason}}]:[]};
 const row={smoke,checks:{},snapshot:{assertionLog:attempted?'• MISSING  '+p.caseName+' — '+reason:''}};
 api.review.diagnosticOracle(p,{done:true,error:null,data},row,catalog.declared);
 assert.equal(row.accounting.passed,true,'The metadata control must reach a valid complete narrow accounting envelope');
 assert.equal(row.diagnosticTargetState,attempted?'missing':'not_executed');assert.equal(row.diagnosticProductOutcome.wholeInstrument,'INCOMPLETE');
 return {row,p};
}
(async()=>{
 for(const attempted of [true,false])await check('C13 receipt separates current target genealogy after '+(attempted?'target miss':'prerequisite miss'),()=>{
  const {row,p}=diagnosticReceipt('diagnostic-calendar-waning-c12',attempted),history=row.calendarDiagnostic;
  assert.deepEqual(history.diagnosticOf,{runId:'42426595933',fixtureAttempt:22,caseName:'chromium-public-healthy-no-preference'});
  assert.notEqual(history.diagnosticOf,p.history.diagnosticOf);assert.equal(history.recipeOriginFirstNativeRun,'42388898271');assert.equal(Object.hasOwn(history,'firstNativeRun'),false);
 });
 await check('legacy diagnostic receipts keep their original genealogy in both outcome branches',()=>{
  for(const id of ['diagnostic-calendar-newmoon','diagnostic-calendar-waning'])for(const attempted of [true,false]){
   const {row}=diagnosticReceipt(id,attempted),history=row.calendarDiagnostic;assert.equal(history.firstNativeRun,'42388898271');
   assert.equal(Object.hasOwn(history,'diagnosticOf'),false);assert.equal(Object.hasOwn(history,'recipeOriginFirstNativeRun'),false);
  }
 });
 await check('actual caller dispatches only the four explicitly selected sessions',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.deepEqual(x.launches.map(r=>r.name),requested);assert.equal(x.result.plannedCount,4);assert.equal(x.result.attemptedCount,4);assert.equal(x.result.notAttemptedCount,0);assert.equal(x.exitCode,0);assert.deepEqual(x.plan.plans.map(p=>({id:p.id,engines:p.engines})),[{id:'matching-tomorrow',engines:['chromium']}]);assert.equal(x.plan.publicContexts.length,3);return {nativeExecutions:0,simulatedLaunches:x.launches};});
 await check('document count includes only the selected no-preference baseline',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.equal(x.result.documentPlan.nativeSessions,4);assert.equal(x.result.documentPlan.topLevelNavigations,5);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,1);assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,0);assert.equal(x.result.documentPlan.calendarTargetDocuments,0);});
 await check('unselected group members are explicit and receive no attempt or PASS',async()=>{const x=await execute({groups:'current,public',cases:requested.join(',')});assert.equal(x.result.selection.notSelected.length,30);assert(x.result.selection.notSelected.includes('firefox-public-healthy-no-preference'));assert(x.result.selection.notSelected.every(n=>!x.result.cases.some(r=>r.name===n)));assert.deepEqual(x.result.selection.requestedCaseNames,requested);});
 await check('explicit argument order cannot silently reorder the reviewed population',async()=>{const x=await execute({groups:'current,public',cases:requested.slice().reverse().join(',')});assert.deepEqual(x.launches.map(r=>r.name),requested);});
 await check('omitting selection preserves the original 36-session population',async()=>{const x=await execute({});assert.equal(x.launches.length,36);assert(!x.launches.some(r=>r.name===waningCase));assert.deepEqual(x.result.groups,['current','public','calendar-diagnostics']);assert.equal(x.result.documentPlan.topLevelNavigations,38);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,2);assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,2);assert.equal(x.result.documentPlan.calendarTargetDocuments,2);});
 await check('current obligation allocation launches only the two Chromium public preferences',async()=>{const names=requested.slice(1,3),x=await execute({groups:'public',cases:names.join(',')});assert.deepEqual(x.launches.map(r=>r.name),names);assert.equal(x.result.plannedCount,2);assert.equal(x.result.attemptedCount,2);assert.equal(x.result.notAttemptedCount,0);assert.equal(x.result.documentPlan.topLevelNavigations,3);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,1);assert.deepEqual(x.plan.plans,[]);assert.deepEqual(x.result.selection.notSelected,['firefox-public-healthy-no-preference','firefox-public-healthy-reduce']);return {nativeExecutions:0,simulatedLaunches:x.launches};});
 await check('C13 actual caller selects one Chromium no-preference waning diagnostic',async()=>{
  const x=await execute({groups:'waning-diagnostic',cases:waningCase});
  assert.deepEqual(x.launches.map(r=>({name:r.name,engine:r.engine,engines:r.engines,group:r.group,kind:r.kind,preference:r.preference})),[{name:waningCase,engine:'chromium',engines:['chromium'],group:'waning-diagnostic',kind:'calendar-diagnostic',preference:'no-preference'}]);
  assert.equal(x.result.plannedCount,1);assert.equal(x.result.attemptedCount,1);assert.equal(x.result.notAttemptedCount,0);assert.equal(x.exitCode,0);
  assert.deepEqual(x.result.selection.notSelected,[]);assert.deepEqual(x.result.selection.requestedCaseNames,[waningCase]);assert.deepEqual(x.plan.publicContexts,[]);
  assert.equal(x.result.documentPlan.nativeSessions,1);assert.equal(x.result.documentPlan.topLevelNavigations,1);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,0);
  assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,1);assert.equal(x.result.documentPlan.calendarTargetDocuments,1);
  assert.equal(x.result.qualification,'PARTIAL');assert.deepEqual(x.launches[0].originalDenominator,{cases:30,assertions:141});
  assert.deepEqual(x.launches[0].history.diagnosticOf,{runId:'42426595933',fixtureAttempt:22,caseName:'chromium-public-healthy-no-preference'});assert.deepEqual(x.plan.plans[0].history,x.launches[0].history);
  return {nativeExecutions:0,simulatedLaunches:x.launches,documentPlan:x.result.documentPlan};
 });
 await check('C13 reuses exact original prerequisite, decoder, target and passive recipe bytes',async()=>{
  const x=await execute({groups:'waning-diagnostic',cases:waningCase}),p=x.plan.plans[0];
  assert.equal(x.plan.plans.length,1);assert.deepEqual(x.launches[0].responseOverrides,['tests/smoke.html']);assert.equal(p.mutations.length,1);assert.equal(p.mutations[0].file,'tests/smoke.html');
  assert.equal(x.plan.heldSmokeSha256,'0e09437cd4c3b8d81abc6e7ed8c9cec3348182bfdbfa5dfe2a19b6a5bdd47661');
  assert.equal(p.expectedIndexSha256,'b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298');
  assert.equal(p.expectedWrapperSha256,'2975111135aac3197dda912de7d06c2452e42d22e304736b82cf3c686a975ac6');
  assert.deepEqual(p.diagnosticSource,{targetCallSha256:'64a2846888bd6b222c300e5f9d652b4f525c1bdf5bc17f2b3b885b229e6db6dc',decoderSha256:'9768863e1c1d89592b786ed70cb879a4f9664ee7b6737f62ec12e764b5c459cf',prerequisiteCallSha256:'ac0dbef2970a48c8b213f28866475933adb8f41841a6e9a0bee2f3492feaf653',additionalReadRecipeSha256:'30949220ab5d58eb125e1676ad7213ebda9609692870cbedde7e4b4188e09a23'});
  assert.equal(p.scriptSha256,'6607815063d06699e86885ed19d0d0f20bfcf885cb067be8eba1118364524b40');
 });
 await check('legacy Firefox diagnostics retain both original dispatches and source identities',async()=>{
  const x=await execute({groups:'calendar-diagnostics'});
  assert.deepEqual(x.launches.map(r=>({name:r.name,engine:r.engine,engines:r.engines,preference:r.preference})),[{name:'firefox-diagnostic-calendar-newmoon',engine:'firefox',engines:['firefox'],preference:'no-preference'},{name:'firefox-diagnostic-calendar-waning',engine:'firefox',engines:['firefox'],preference:'no-preference'}]);
  assert(x.launches.every(r=>r.history.firstNativeRun==='42388898271'&&!r.history.diagnosticOf));
  assert.deepEqual(x.plan.plans.map(p=>p.scriptSha256),['fadd02e1aca4b80f793159bdf64931fe371f59322a5e6d348912f50d0979250c','6607815063d06699e86885ed19d0d0f20bfcf885cb067be8eba1118364524b40']);
  assert.equal(x.result.documentPlan.nativeSessions,2);assert.equal(x.result.documentPlan.topLevelNavigations,2);assert.equal(x.result.documentPlan.calendarPrerequisiteDocuments,2);assert.equal(x.result.documentPlan.calendarTargetDocuments,2);
 });
 await check('C13 case is refused by the actual default groups',()=>rejected({cases:waningCase}));
 await check('C13 case is refused by the legacy diagnostic group',()=>rejected({groups:'calendar-diagnostics',cases:waningCase}));
 await check('C14 workflow explicit passive caller selects only two public contexts and three meaningful documents',async()=>{
  const workflow=fs.readFileSync(path.join(root,'.github/workflows/r0017-windows-phase2.yml'),'utf8'),entry=require('./r0017-windows-passive.cjs');
  const commands=workflow.split('\n').filter(line=>line.trim().startsWith('node qualification/tools/qualification/'));assert.equal(commands.length,1);
  const tokens=commands[0].trim().split(/\s+/);assert.equal(tokens[1],'qualification/tools/qualification/r0017-windows-passive.cjs');
  const args=entry.parse(tokens.slice(2)),cases=['chromium-public-healthy-no-preference','chromium-public-healthy-reduce'];
  assert.equal(args['network-observation'],'passive');assert.equal(args.groups,'public');assert.equal(args.cases,cases.join(','));
  assert.equal(args['security-provenance'],'csp');assert.equal(args['image-assignment-provenance'],'src');
  const baseHash=crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'r0017-windows-proof.cjs'))).digest('hex');
  assert.equal(args['base-sha'],baseHash);assert.equal(entry.BOUND_BASE_SHA,baseHash);
  const x=await execute({groups:args.groups,cases:args.cases},args);
  assert.deepEqual(x.launches.map(r=>r.name),cases);assert.equal(x.plan.plans.length,0);assert.equal(x.plan.publicContexts.length,2);
  assert.equal(x.result.schema,'r0017-windows-passive/v1');assert.equal(x.result.networkObservation.method,'passive-bidi/v1');assert.equal(x.result.qualification,'PARTIAL');
  assert.equal(x.result.documentPlan.nativeSessions,2);assert.equal(x.result.documentPlan.topLevelNavigations,3);assert.equal(x.result.documentPlan.additionalPublicBaselineDocuments,1);assert.equal(x.result.documentPlan.initializationDocuments,2);
  const receiptCases=workflow.match(/^\s+plannedCases = @\(([^\n]+)\)$/m);assert(receiptCases);assert.equal(receiptCases[1],cases.map(s=>"'"+s+"'").join(', '));
  for(const [field,count] of [['plannedNativeSessions',2],['plannedTopLevelDocuments',3],['plannedInitializationDocuments',2],['plannedCalendarPrerequisiteDocuments',0],['plannedCalendarTargetDocuments',0]])assert.equal(Number(workflow.match(new RegExp('^\\s+'+field+' = (\\d+)$','m'))?.[1]),count,field);
  assert(workflow.includes("networkObservation = 'passive-bidi/v1'"));assert(workflow.includes("interception = 'NOT_REQUESTED_NO_INTERCEPTION_CREDIT'"));
  assert(workflow.includes('timeout-minutes: 20')&&workflow.includes('timeout-minutes: 17')&&workflow.includes('AddMinutes(16)'));
  return {nativeExecutions:0,simulatedLaunches:x.launches,documentPlan:x.result.documentPlan};
 });
 await check('C14 actual orchestration refuses expanded population before source setup or launch',async()=>{
  const args={groups:'public',cases:'chromium-public-healthy-no-preference,chromium-public-healthy-reduce','network-observation':'passive'};
  let observed;try{await execute({groups:'current,public',cases:args.cases},args);}catch(e){observed=e;}
  assert(observed);assert.equal(observed.identified,0);assert.deepEqual(observed.launches,[]);return String(observed.message);
 });
 await check('all exact base consumers remain bound to the actual revised source',()=>{
  const baseHash=crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'r0017-windows-proof.cjs'))).digest('hex');
  for(const [file,key] of [['r0017-windows-phase2.cjs','REVIEWED_BASE_SHA'],['r0017-driver-cleanup-probe.cjs','expectedBase']]){
   const text=fs.readFileSync(path.join(__dirname,file),'utf8');assert.equal(text.match(new RegExp("const "+key+"='([a-f0-9]{64})'"))?.[1],baseHash,file);
  }
 });
 await check('duplicate case is refused before source setup or launch',()=>rejected({groups:'current,public',cases:requested[0]+','+requested[0]}));
 await check('unknown case is refused before source setup or launch',()=>rejected({groups:'current,public',cases:'chromium-not-a-case'}));
 await check('empty explicit selection is refused before source setup or launch',()=>rejected({groups:'current,public',cases:''}));
 await check('empty token is refused before source setup or launch',()=>rejected({groups:'current,public',cases:requested[0]+','}));
 await check('case outside selected groups is refused before source setup or launch',()=>rejected({groups:'current',cases:'firefox-public-healthy-reduce'}));
 console.log(JSON.stringify({schema:'r0017-phase2-selection-controls/v1',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),nativeExecutions:0,passed:results.filter(x=>x.passed).length,failed:results.filter(x=>!x.passed).length,results},null,2));process.exitCode=results.every(x=>x.passed)?0:1;
})().catch(e=>{console.error(e);process.exitCode=1;});
