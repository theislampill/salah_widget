'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const out=__dirname,base='https://github.com/theislampill/salah_widget/blob/AUDIT_EVIDENCE_COMMIT/docs/rlgwo-audit/20261008/';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=f=>JSON.parse(fs.readFileSync(path.join(out,f),'utf8'));
const save=(f,v)=>fs.writeFileSync(path.join(out,f),JSON.stringify(v,null,2)+'\n');
const ids=[11,12,13,14,30,36],summary=read('summary.json');
const esc=s=>String(s??'').replace(/\|/g,'\\|').replace(/\r?\n/g,'<br>');
const refs=rs=>rs.map(r=>r.url?'['+r.file+(r.start?':'+r.start+'–'+r.end:'')+']('+r.url+')':esc(r.description||r.file)).join('<br>');
const matrixRow=r=>'| '+r.id+' | '+esc(r.obligation)+' | '+refs([...r.authoredOwner,...r.deliveredConsumer])+' | '+esc(r.discriminator)+'; expected: '+esc(r.expected)+'<br>Observed: '+esc(r.observed)+'<br>'+refs(r.evidence)+' | **'+r.status.toUpperCase()+'** |';
for(const issue of ids){
 const a=read(issue+'-assessment.json');
 a.publication.status='PRIMARY_ASTRA_RECONCILED_APPROVED_TEXT; EXTERNAL EFFECTS HELD FOR IMMUTABLE EVIDENCE HASH VERIFICATION';
 a.publication.primaryDecision=issue===14||issue===30?'APPROVED CLOSE — SATISFIED':'APPROVED LEAVE OPEN WITH EXACT GAPS';
 a.publication.publicEvidenceBinding='AUDIT_EVIDENCE_COMMIT placeholder; primary exact SHA/per-file readback approval required';
 a.publication.githubWrites=false;
 a.reviewerReconciliation='Reviewer C proof and all final binding rows independently reconciled by primary Astra; primary approves recorded disposition. Posting/closure remain separate held effects pending immutable evidence commit and per-file hash approval.';
 if(a.substantiveClosureProof)a.substantiveClosureProof.approval='PRIMARY ASTRA APPROVED CLOSE — SATISFIED; GitHub comment/closure held until immutable evidence SHA and per-file hash verification';
 for(const r of a.requirementMatrix){
  for(const e of r.evidence)if(e.file?.startsWith('workers/C/'))e.url=base+e.file;
  if([14,30].includes(issue)&&['E13','1E12'].includes(r.id))r.observed=r.observed.replace('primary approval/publication precedes','primary Astra has independently reconciled; publication precedes').replace('ready for primary independent review, evidence binding and publication','independently reviewed and approved by primary Astra; exact evidence binding and publication remain');
  r.observed=r.observed.replace('Complete proposed evidence comment prepared; primary Astra has independently reconciled;','Complete evidence comment independently reconciled and approved by primary Astra;').replace('Complete proposed evidence comment is independently','Complete evidence comment is independently');
 }
 // Publication as a future effect is not the reason product qualification rows remain open.
 if(issue===11){const r=a.requirementMatrix.find(r=>r.id==='B18');r.observed='Delivered baseline verified with16 public cases and recorded client configuration. C and primary Astra independently reviewed the source/interface join. Qualification remains incomplete for the explicitly mapped hostile metadata/mutation/documentation rows; external evidence publication precedes any later manual closure.';}
 a.gaps=a.requirementMatrix.filter(r=>r.status==='unmet'||r.status==='unverified').map(r=>({obligation:r.id,status:r.status,gap:r.observed,limitation:r.limitations}));
 save(issue+'-assessment.json',a);
 let md=fs.readFileSync(path.join(out,issue+'-comment.md'),'utf8');
 md=md.replace('This is a proposed complete closure proof, awaiting primary independent challenge, immutable evidence binding and individual publication approval. It is not a posted comment or executed closure.','Primary Astra independently reconciled the complete issue-specific proof and approves **CLOSE — SATISFIED**. Posting and manual closure follow verification of the immutable evidence commit and per-file hashes; no external effect is claimed here.');
 md=md.replace('This is a proposed issue-specific audit, awaiting primary challenge/reconciliation and individual publication approval. It is not a posted closure or a new authorization to change production.','Primary Astra independently reconciled the issue-specific matrix and approves **LEAVE OPEN** for the exact gaps below. This audit is not a production-repair authorization or a closure; posting follows verification of the immutable evidence commit and per-file hashes.');
 md=md.replaceAll('primary approval/publication precedes','primary Astra has independently reconciled; publication precedes');
 md=md.replaceAll('ready for primary independent review, evidence binding and publication','independently reviewed and approved by primary Astra; exact evidence binding and publication remain');
 md=md.replace('Primary must independently approve this issue, publish the supplied receipts/crops under an immutable evidence ref and replace these relative evidence links before posting this proof and manually closing. C executed no external effect.','Primary Astra has independently read all final obligations and native consumer receipts, inspected the scoped pixels and approved this closure proof. Primary will verify the immutable evidence commit/per-file hashes, bind the evidence links, post this proof and then manually close. Those external effects are not claimed executed here; C performed none.');
 md=md.replaceAll('relative public evidence binding pending','immutable evidence commit placeholder pending verification');
 md=md.replace(/\]\((workers\/C\/[^)]+)\)/g,']('+base+'$1)');
 for(const r of a.requirementMatrix){const lines=md.split('\n'),index=lines.findIndex(s=>s.startsWith('| '+r.id+' |'));if(index<0)throw Error('Missing public row '+r.id);lines[index]=matrixRow(r);md=lines.join('\n');}
 const gapStart=md.indexOf('Current unmet or unverified obligations:'),gapEnd=md.indexOf('The four legacy WEATHER TODOs remain explicit.',gapStart);
 if(gapStart<0||gapEnd<gapStart)throw Error('Missing old gap block '+issue);
 const gaps=a.gaps.length?'Current unmet or unverified obligations:\n\n'+a.gaps.map(g=>'- **'+g.obligation+' — '+g.status+':** '+g.gap+(g.limitation?' '+g.limitation:'')).join('\n')+'\n\n':'All binding obligations are satisfied in this scope; no substantive closure gap remains. Primary Astra has independently approved the proof; immutable evidence hash verification precedes external effects.\n\n';
 md=md.slice(0,gapStart)+gaps+md.slice(gapEnd);
 if([14,30].includes(issue))md=md.replace('The browser/zero-axis/pixel placeholder is not silently promoted to PASS.','The original browser/zero-axis/pixel placeholder remains TODO as an old test; relevant #14/#30 obligations now have separately mapped actual-source native acquisition/crop and scoped preservation replacements. This does not convert a general legacy placeholder into an executed PASS.');
 if(issue===11){const r=a.requirementMatrix.find(r=>r.id==='B18');md=md.replace('Source tree/runtime identity verified locally; primary reports139 public hashes and scoped root Chrome smoke; individual closure/evidence publication remains held.',r.observed);}
 md=md.replaceAll('All six material weather regions match final delivered root bytes:','All eight material regions (six weather regions plus explicit motion policy/cloud generator) match final delivered root bytes:');
 fs.writeFileSync(path.join(out,issue+'-comment.md'),md);
 summary.results[issue].primaryReconciliation=a.publication.primaryDecision;
}
summary.publication={status:'PRIMARY_ASTRA_RECONCILED; HASH-BOUND EXTERNAL EFFECT HOLD',githubWritesByC:false,evidenceBasePlaceholder:base,
 preconditions:'Primary verify immutable evidence commit and per-file hashes, replace placeholder with exact SHA, then serialized comments and approved closures with live readback.'};
summary.nextAction='Primary bind AUDIT_EVIDENCE_COMMIT to verified immutable evidence SHA and approve per-file hashes before external posting/closure; C14/C30 close, C11/C12/C13/C36 remain open as reconciled.';
summary.requiredMissingChecks=ids.filter(i=>i!==14&&i!==30).map(issue=>{const a=read(issue+'-assessment.json');return {issue,gaps:a.gaps,preparedBrowser:issue===12?'run_weather_browser_v2.py --issue 12':null,disposition:a.verdict};});
save('summary.json',summary);
const final=read('followup-reconciliation.json');final.results=summary.results;final.primaryApproval='Primary Astra independently reconciled and approved all recorded dispositions';final.publication='HELD FOR IMMUTABLE EVIDENCE COMMIT/PER-FILE HASH VERIFICATION; no GitHub effects by C';save('followup-reconciliation.json',final);
const map=read('evidence-publication-map.json');map.evidenceBasePlaceholder=base;map.primaryReconciliation='Primary Astra approved C14/C30 CLOSE and C11/C12/C13/C36 OPEN; posting/closure require immutable hash approval';
for(const item of map.files){const local=path.join(out,item.relativePath.slice('workers/C/'.length)),bytes=fs.readFileSync(local);item.sha256=hash(bytes);item.bytes=bytes.length;item.urlPlaceholder=base+item.relativePath;}
save('evidence-publication-map.json',map);
console.log(JSON.stringify({status:summary.publication.status,approvedClose:[14,30],approvedOpen:[11,12,13,36],externalEffects:false}));
