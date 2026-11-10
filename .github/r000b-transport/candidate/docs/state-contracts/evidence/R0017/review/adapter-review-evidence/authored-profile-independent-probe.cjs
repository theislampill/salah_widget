'use strict';
// Read-only admission/compile review. No product script or browser is executed.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const vm=require('node:vm'),cp=require('node:child_process'),assert=require('node:assert/strict');
const root='/workspace/scratch/7a8daf93afaa/r0017-explicit-work';
const evidence='/workspace/scratch/7a8daf93afaa/adapter-review-evidence';
const authorEvidence='/workspace/scratch/7a8daf93afaa/adapter-evidence';
const sha=body=>crypto.createHash('sha256').update(body).digest('hex');
const previous=JSON.parse(fs.readFileSync(path.join(evidence,'final-profile-independent-probe.json'),'utf8'));
const paths=[...Object.keys(previous.filesAfter),'tests/hotfix-prayer-weather.test.cjs'];
const snapshot=()=>Object.fromEntries(paths.map(name=>{const body=fs.readFileSync(path.join(root,name));return [name,{sha256:sha(body),bytes:body.length}];}));
const git=args=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024,timeout:5000,env:{...process.env,GIT_NO_LAZY_FETCH:'1'}});
const started=process.hrtime.bigint(),observedAt=new Date().toISOString();
const filesBefore=snapshot(),headBefore=git(['rev-parse','HEAD']).trim();
const expectedAuthorHashes={
  'tests/native-script-contract.js':'adde2470bba5f276ddae71f0c5a2fad9485854604bbd733c87723583e04b578a',
  'tests/r0017-adapters.test.cjs':'ca4be8789b0beb127a2e3d226dd952face79ae8412f13d8b927f9236c9faaef8',
  'tests/hotfix-prayer-weather.test.cjs':'1b96aa5ec5ed88c5386eccaeabd38ea07a50f91461da412247b4ddd3e21f07d1',
  'src/native/index.html':'6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad'
};
const contract=require(path.join(root,'tests/native-script-contract.js'));
const {nativeInlineRuntime}=require(path.join(root,'tests/native-inline-runtime.cjs'));
const current=fs.readFileSync(path.join(root,'index.html'),'utf8');
const authored=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const tags=[...current.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
const once=(source,oldValue,newValue)=>{assert.equal(source.split(oldValue).length-1,1);return source.replace(oldValue,newValue);};
function remove(ids){
  let source=current;
  for(const id of ids){const found=tags.filter(tag=>tag[1].includes('id="'+id+'"'));assert.equal(found.length,1);source=once(source,found[0][0],'');}
  return source;
}
const pairMissing=remove(['moon-initial-code','moon-refinement-code']);
const allPrerequisitesMissing=remove(['native-first-paint-code','moon-initial-code','moon-refinement-code']);
const sky=tags.filter(tag=>tag[1].trim()==='src="real-sky/native-sky.js"');assert.equal(sky.length,1);
const lookalike=once(allPrerequisitesMissing,sky[0][0],'');
assert.deepEqual([...lookalike.matchAll(/<script\b([^>]*)>/gi)].map(tag=>tag[1].trim()),['src="config.js"','']);
const structural=once(pairMissing,'</body>','<script>if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;</script><script src="moon/moon-host.js"></script></body>');
assert.equal(sha(structural),'f6650909f7d2defc2edffa25c7510b4ae476fc3208d4a9625090107ff77de1de');
const inputs=[
  {name:'current generated source',source:current,admit:true,profile:'split-moon'},
  {name:'exact current authored source',source:authored,admit:true,profile:'current-authored-native'},
  {name:'unreviewed altered authored source',source:authored+'\n<!-- unreviewed authored input -->',admit:false},
  {name:'both Moon prerequisites removed',source:pairMissing,admit:false},
  {name:'first-paint and both Moon prerequisites removed',source:allPrerequisitesMissing,admit:false},
  {name:'generated config,native lookalike cannot impersonate authored source',source:lookalike,admit:false},
  {name:'pinned legacy structural fixture',source:structural,admit:true,profile:'retained-legacy-moon-structural-control'},
  {name:'current generated native semantic initializer mutation',source:once(current,'let _skyInitialDocument=true;','let _skyInitialDocument=false;'),admit:true,profile:'split-moon'}
];
for(const [commit,pin,profile] of [
  ['fd2972ba64225fe9d6848e92497e6d0ed20ea624','446453b522f56f5f1bc0afd1a3abd09b73756754fa58a6b3b0ff09ce953a2eec','retained-historical-native'],
  ['ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d','d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f','retained-historical-legacy-moon'],
  ['47c0fa0c6e32618f22b43b6a18717908b0de5f5e','bbe447167dcb751b9463b54ee29bcdcbbfeb0a521c4cd93f59b4bd429cca6b1e','retained-historical-native'],
  ['18ff14860ff41c084b1db5f396bb62aa9c22b1be','ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee','retained-historical-legacy-moon']
]){const source=git(['show',commit+':index.html']);assert.equal(sha(source),pin);inputs.push({name:commit+':index.html',source,admit:true,profile});}
const rows=inputs.map(input=>{
  const row={name:input.name,expectedAdmitted:input.admit,sourceSha256:sha(input.source),productExecuted:false};
  try{
    const runtime=nativeInlineRuntime(input.source),scripts=contract.parseScripts(input.source);
    const admitted=contract.admitScripts(input.source,scripts,scripts.map(script=>sha(script.body)),sha(input.source));
    const owner=scripts.filter(script=>!script.attributes.trim()&&script.body.includes('async function boot(){'));
    new vm.Script(runtime,{filename:input.name});
    Object.assign(row,{admitted:true,compiled:true,profile:admitted.profile,provenance:admitted.provenance,runtimeQualified:admitted.runtimeQualified,runtimeSha256:sha(runtime),extractedExactOwner:owner.length===1&&runtime===owner[0].body});
    row.asExpected=input.admit&&row.extractedExactOwner&&row.profile===input.profile&&row.runtimeQualified===false;
  }catch(error){Object.assign(row,{admitted:false,code:error.code??null,error:error.message});row.asExpected=!input.admit&&error.code==='SETUP_INCOMPLETE';}
  return row;
});
const receiptBytes=fs.readFileSync(path.join(authorEvidence,'authored-profile-verification.json'));
const authorReceipt=JSON.parse(receiptBytes.toString('utf8'));
const authorLogChecks=authorReceipt.commands.map(command=>{
  const data=fs.readFileSync(command.log),text=data.toString('utf8');
  const row={name:command.name,log:command.log,sha256:sha(data),receiptHashMatches:sha(data)===command.logSha256,reportedExitCode:command.exitCode};
  if(command.tapTotals){row.observedTapTotals=Object.fromEntries([...text.matchAll(/^# (tests|pass|fail|cancelled|skipped|todo) (\d+)$/gm)].map(match=>[match[1],Number(match[2])]));row.receiptTotalsMatch=JSON.stringify(row.observedTapTotals)===JSON.stringify(command.tapTotals);}
  if(command.resultCases){const parsed=JSON.parse(text);row.resultCount=parsed.results.length;row.allResultsPass=parsed.results.every(result=>(result.result??result.status)==='PASS');row.receiptResultsMatch=row.resultCount===command.resultCases&&row.allResultsPass;}
  if(command.input){const inputLine=text.split('\n').find(line=>line.startsWith('MUTANT_INPUT '));row.actualMutantInput=JSON.parse(inputLine.slice('MUTANT_INPUT '.length));const parsed=JSON.parse(text.slice(text.indexOf('\n')+1));row.actualFailCases=parsed.results.filter(result=>result.status==='FAIL').length;row.mutantReachesBehavior=Boolean(row.actualMutantInput.setupAdmitted&&row.actualFailCases===command.failCases&&!text.includes('SETUP_INCOMPLETE'));}
  return row;
});
const filesAfter=snapshot(),headAfter=git(['rev-parse','HEAD']).trim();
const allTrackedChanges=git(['diff','HEAD','--name-only']).trim().split('\n').filter(Boolean);
const changesSincePreviousReview=Object.keys(previous.filesAfter).filter(name=>previous.filesAfter[name].sha256!==filesBefore[name].sha256);
const sourceStable=JSON.stringify(filesBefore)===JSON.stringify(filesAfter);
const authorFreezeMatches=Object.entries(expectedAuthorHashes).every(([name,pin])=>filesBefore[name].sha256===pin);
const unchangedOtherReviewedFiles=changesSincePreviousReview.every(name=>['tests/native-script-contract.js','tests/r0017-adapters.test.cjs'].includes(name));
const allExpected=rows.every(row=>row.asExpected);
const authorEvidenceMatches=authorReceipt.contractSha256===filesBefore['tests/native-script-contract.js'].sha256&&authorReceipt.focusedTestSha256===filesBefore['tests/r0017-adapters.test.cjs'].sha256&&authorLogChecks.every(row=>row.receiptHashMatches&&row.receiptTotalsMatch!==false&&row.receiptResultsMatch!==false&&row.mutantReachesBehavior!==false);
const result={observedAt,kind:'independent authored profile follow-up; admission and compile only, no product execution',headBefore,headAfter,filesBefore,filesAfter,sourceStable,expectedAuthorHashes,authorFreezeMatches,changesSincePreviousReview,unchangedOtherReviewedFiles,allTrackedChanges,rows,allExpected,authorReceiptSha256:sha(receiptBytes),authorLogChecks,authorEvidenceMatches,seconds:Number(process.hrtime.bigint()-started)/1e9};
result.status=sourceStable&&authorFreezeMatches&&unchangedOtherReviewedFiles&&allExpected&&authorEvidenceMatches&&headBefore===headAfter?'PASS':'GAP-REVISE';
console.log(JSON.stringify(result,null,2));
process.exitCode=result.status==='PASS'?0:1;
