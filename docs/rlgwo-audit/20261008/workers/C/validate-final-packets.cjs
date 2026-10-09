'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const out=__dirname,audit=path.dirname(path.dirname(out)),root='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be',issues=[11,12,13,14,30,36];
const legal=new Set(['satisfied','validly superseded','unmet','unverified']),checks=[];
function assert(ok,description){checks.push({description,passed:!!ok});if(!ok)throw Error(description);}
const summary=JSON.parse(fs.readFileSync(path.join(out,'summary.json'),'utf8'));
let rows=0,closable=0;
for(const issue of issues){
 const packet=JSON.parse(fs.readFileSync(path.join(audit,'issues',issue+'.json'),'utf8'));
 const a=JSON.parse(fs.readFileSync(path.join(out,issue+'-assessment.json'),'utf8'));
 const comment=fs.readFileSync(path.join(out,issue+'-comment.md'),'utf8');
 assert(a.issue===issue&&a.canonicalId===packet.contract.canonicalId,'Canonical issue '+issue);
 assert(a.contract.bodySha256===packet.contract.bodySha256&&sha(Buffer.from(packet.issue.body,'utf8'))===packet.contract.bodySha256,'Protected body hash '+issue);
 assert(a.target===SHA&&a.tree==='35208181eea714c17f5e77b2644e76434345db60','Target/tree '+issue);
 assert(new Set(a.requirementMatrix.map(r=>r.id)).size===a.requirementMatrix.length,'Unique row IDs '+issue);
 for(const r of a.requirementMatrix){
  assert(legal.has(r.status),'Legal status '+issue+'/'+r.id);
  assert(['id','obligation','discriminator','expected','observed'].every(k=>typeof r[k]==='string'&&r[k].length>0),'Mandatory claim/discriminator/state '+issue+'/'+r.id);
  assert(Array.isArray(r.authoredOwner)&&r.authoredOwner.length>0&&Array.isArray(r.deliveredConsumer)&&r.deliveredConsumer.length>0,'Owner and consumer '+issue+'/'+r.id);
  assert(Array.isArray(r.evidence)&&comment.includes('| '+r.id+' |'),'Evidence and public row '+issue+'/'+r.id);
 }
 rows+=a.requirementMatrix.length;
 const closes=a.verdict.startsWith('CLOSE');closable+=Number(closes);
 assert(!closes||a.requirementMatrix.every(r=>r.status==='satisfied'||r.status==='validly superseded'),'No false-green closure '+issue);
 assert(comment.includes('<!-- RLGWO-AUDIT:'+SHA+':'+a.canonicalId+':2026-10-08 -->'),'Stable marker '+issue);
 assert(closes?comment.startsWith('# RLGWO closure proof'):comment.includes('Next RLGWO increment required for closure'),'Correct comment contract '+issue);
 assert(Buffer.byteLength(comment,'utf8')<65535,'Comment under API size '+issue);
 assert(summary.results[issue].verdict===a.verdict,'Summary reconciliation '+issue);
}
assert(rows===101&&summary.totals.matrixRows===rows,'Complete 101-row matrices');
assert(closable===2&&summary.totals.closable===2&&summary.totals.leaveOpen===4,'Two proposals close, four open');
const model=JSON.parse(fs.readFileSync(path.join(out,'config-confirmation.json'),'utf8'));
assert(model.effective.model==='gpt-6.1-sol'&&model.effective.reasoningEffort==='max'&&model.effective.confirmation==='CONFIRMED RECORDED CLIENT TURN CONFIGURATION','Effective recorded client model');
const original=fs.readFileSync(path.join(out,'browser14-chromium-v2/results.json'));
const rec=JSON.parse(fs.readFileSync(path.join(out,'browser14-v2-semantic-reconciliation.json'),'utf8'));
assert(JSON.parse(original).status==='FAIL'&&sha(original)===rec.original.sha256&&rec.status==='MATCHES CORRECT QUANTITATIVE-EFFECT ORACLE','Original native FAIL immutable and semantic proof separate');
assert(sha(fs.readFileSync(path.join(root,'index.html')))==='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee','Delivered product index unchanged');
assert(sha(fs.readFileSync(path.join(root,'src/native/index.html')))==='19dd9ba814fdb426b75e4282aca2e3bf20569b5b55ef9764d13e786c84c7b012','Authored native owner unchanged');
const map=JSON.parse(fs.readFileSync(path.join(out,'evidence-publication-map.json'),'utf8'));
for(const item of map.files)assert(sha(fs.readFileSync(path.join(audit,item.relativePath)))===item.sha256,'Publication custody '+item.relativePath);
const prior=Array.isArray(summary.files)?summary.files:[];
summary.files=[...new Set([...prior,'followup-reconciliation.json','mutation-receipts.json','historical-source-equivalence.json','browser14-v2-semantic-reconciliation.json','browser-pixel-review.json','evidence-publication-map.json','browser-fixture-preparation-v2.json','run_weather_browser_v2.py','artifact-validation.json'])];
fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2)+'\n');
const result={schema:'rlgwo-C-final-artifact-validation-v1',status:'PASS',target:SHA,issues,rows,closable,leaveOpen:4,checks,
 browserLaunchByC:false,productionChangesByC:false,GitHubEffectsByC:false,
 publicationBinding:'Relative evidence links supplied; primary must bind an immutable evidence branch and approve individually before external effects.'};
fs.writeFileSync(path.join(out,'artifact-validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks:checks.length,rows,closable,leaveOpen:4}));
