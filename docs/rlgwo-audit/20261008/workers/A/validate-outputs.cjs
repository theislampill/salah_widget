'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),cp=require('node:child_process'),crypto=require('node:crypto'),dir=__dirname;
const SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be',TREE='35208181eea714c17f5e77b2644e76434345db60',repo='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),summary=JSON.parse(fs.readFileSync(path.join(dir,'summary.json'),'utf8'));assert.equal(summary.results.length,6);
let rows=0,consumers=0,links=0;
for(const n of [2,3,4,5,6,7]){
 const key=String(n).padStart(2,'0'),a=JSON.parse(fs.readFileSync(path.join(dir,key+'-assessment.json'),'utf8')),comment=fs.readFileSync(path.join(dir,key+'-comment.md'),'utf8');
 assert.equal(a.issueNumber,n);assert.equal(a.canonicalId,'R000'+n);assert.equal(a.target.commit,SHA);assert.equal(a.target.tree,TREE);assert.equal(a.verdict,n===5?'CLOSE — SATISFIED':'LEAVE OPEN');assert(n===5?a.gaps.length===0:a.gaps.length>0);
 assert.equal(a.initialContract.completeBodyRead,true);assert.equal(a.initialContract.comments.length,0);assert.match(a.initialContract.bodySha256,/^[a-f0-9]{64}$/);
 assert(comment.startsWith(n===5?'# RLGWO closure proof — R0005 —':'# RLGWO closure audit — '+a.canonicalId+' — REMAINS OPEN'));
 assert(comment.includes(`<!-- RLGWO-AUDIT:${SHA}:${a.canonicalId}:2026-10-08 -->`));assert(n===5?comment.includes('CLOSE — SATISFIED'):comment.includes('Next RLGWO increment required for closure'));
 assert(comment.includes(a.initialContract.bodySha256));assert(!/\]\((?:undefined|null)\)/.test(comment));
 assert(comment.includes('Primary Astra independently reconciled'));
 assert(/https:\/\/github\.com\/theislampill\/salah_widget\/blob\/(?:AUDIT_EVIDENCE_COMMIT|[0-9a-f]{40})\/docs\/rlgwo-audit\/20261008\//.test(comment));
 assert(!/reviewer proposal|proposed assessment|must independently (?:challenge|inspect)\/reconcile/.test(comment));
 for(const r of a.requirementMatrix){assert.equal(r.mandatory,true);assert(['satisfied','validly superseded','unmet','unverified'].includes(r.status));assert(r.sourceOwners.length>0);assert(r.expected&&r.observed);assert(r.deliveredConsumer.some(c=>c.path==='index.html'));assert(r.deliveredConsumer.some(c=>c.path==='offline.html'));rows++;consumers+=r.deliveredConsumer.length;}
 links+=(comment.match(/https:\/\/github\.com\/theislampill\/salah_widget\/blob\/18ff14860ff41c084b1db5f396bb62aa9c22b1be\//g)||[]).length;
}
assert.equal(rows,94);
const equivalence=JSON.parse(fs.readFileSync(path.join(dir,'source-equivalence.json'),'utf8'));assert.equal(equivalence.ranges.length,18);
const transforms=equivalence.ranges.flatMap(r=>r.deliveredConsumers).filter(c=>c.checkedGeneratorTransformation);assert.equal(transforms.length,2);assert(transforms.every(c=>c.checkedGeneratorTransformation.kind==='documented additive CP9 elevation-custody hook'));
const status=cp.spawnSync('git',['status','--porcelain'],{cwd:repo,encoding:'utf8'});assert.equal(status.status,0);assert.equal(status.stdout.trim(),'');
const actualTree=cp.spawnSync('git',['rev-parse','HEAD^{tree}'],{cwd:repo,encoding:'utf8'});assert.equal(actualTree.stdout.trim(),TREE);
const allFiles=fs.readdirSync(dir).filter(f=>f.endsWith('.json'));for(const file of allFiles)JSON.parse(fs.readFileSync(path.join(dir,file),'utf8'));
assert.equal(summary.effectiveConfiguration.model,'gpt-6.1-sol');assert.equal(summary.effectiveConfiguration.reasoningEffort,'max');assert.equal(summary.deliveredBaseline.status,'DELIVERED_VERIFIED');assert.equal(summary.deliveredBaseline.passed,16);
const results={status:'PASS',targetCommit:SHA,targetTree:TREE,issues:6,mandatoryObligationRows:rows,generatedConsumerMappings:consumers,immutableBlobLinks:links,generatedOwnerRanges:18,declaredGeneratedHookMappings:transforms.length,allJsonParsed:true,proposalMarkersVerified:true,productionGitStatus:'clean',browserExecutedByWorker:false,githubWrites:false,effectiveWorkerModelConfirmation:summary.effectiveConfiguration,deliveredBaseline:summary.deliveredBaseline.status,nodeRuntime:{node:process.version,platform:process.platform,arch:process.arch,icu:process.versions.icu,tzdata:process.versions.tz}};
fs.writeFileSync(path.join(dir,'validation.json'),JSON.stringify(results,null,2)+'\n');
const files=fs.readdirSync(dir).filter(f=>f!=='OUTPUT_MANIFEST.json'&&fs.statSync(path.join(dir,f)).isFile()).sort().map(file=>{const bytes=fs.readFileSync(path.join(dir,file));return {file,bytes:bytes.length,sha256:hash(bytes)};});
fs.writeFileSync(path.join(dir,'OUTPUT_MANIFEST.json'),JSON.stringify({schema:'pr42-worker-output-manifest/1',worker:'A',targetCommit:SHA,scope:'Top-level owned workers/A audit proposals, fixture preparation and retained receipts; manifest does not hash itself or later primary-owned browser output subdirectories',files},null,2)+'\n');
console.log(JSON.stringify(results,null,2));
