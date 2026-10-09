'use strict';
// Read-only, explicit source-region comparison. Does not run browser code.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const older='C:/Users/theis/Documents/Codex/startup-cloud-hotfix-20261007/h8/startup-v45-negative-source/index.html';
const oldBytes=fs.readFileSync(older),newBytes=fs.readFileSync(path.join(root,'index.html'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const requiredOld='c9579ac9aa9d158cc4ad0ce4288781f3ff3db40afdc4820510203e6e64c80a7a',requiredNew='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee';
if(hash(oldBytes)!==requiredOld||hash(newBytes)!==requiredNew)throw Error('Source identity mismatch');
const old=oldBytes.toString('utf8').replace(/\r\n/g,'\n'),now=newBytes.toString('utf8').replace(/\r\n/g,'\n');
function region(src,start,end){const a=src.indexOf(start),b=src.indexOf(end,a+start.length);if(a<0||b<=a)throw Error('Missing region '+start);return {text:src.slice(a,b),startLine:src.slice(0,a).split('\n').length,endLine:src.slice(0,b).split('\n').length-1};}
const defs=[
 ['motion-policy','const MOTIONFULL =','// ---- helpers'],
 ['cloud-generator-motion','// ---- CLOUD ENGINE:','// ---- ATMOSPHERE STATE'],
 ['request-owner','function cacheKey(){','// Read only the selected legacy main-format envelope.'],
 ['weather-admission-acquisition-decision-header','// ---- weather (Open-Meteo:','// ---- accurate Moon position'],
 ['model-and-radar-gate','const _PRECIP_MIN=','// ---- CLOUD ENGINE:'],
 ['weather-atmosphere-consumer','function atmosphere(M){','// paint(A)'],
 ['cloud-per-use-consumer','function applyCloudState(A){','// Size the present-prayer name'],
 ['weather-qa-consumer','window.qaState=function(){','// debugMotion telemetry']
];
const regions=defs.map(([id,start,end])=>{const a=region(old,start,end),b=region(now,start,end);return {id,startAnchor:start,endAnchor:end,
 old:{sha256:hash(a.text),startLine:a.startLine,endLine:a.endLine,bytes:Buffer.byteLength(a.text)},
 current:{sha256:hash(b.text),startLine:b.startLine,endLine:b.endLine,bytes:Buffer.byteLength(b.text)},equal:a.text===b.text};});
const h8='C:/Users/theis/Documents/Codex/startup-cloud-hotfix-20261007/h8';
const resultsPath=path.join(h8,'joined-v45-chromium-current-boundaries/results.json');
const results=JSON.parse(fs.readFileSync(resultsPath,'utf8'));
const cases=JSON.parse(fs.readFileSync(path.join(h8,'joined-v45-chromium-current-boundaries/current-boundaries.json'),'utf8'));
const reuseFiles=['v45-v46-reuse.json','v46-v47-reuse.json','v47-v48-reuse.json','v48-v49-reuse.json'];
const reuse=reuseFiles.map(name=>{const p=path.join(h8,name),data=JSON.parse(fs.readFileSync(p,'utf8'));return {name,sha256:hash(fs.readFileSync(p)),from:data.from||data.previous,to:data.to||data.current,
 changed:data.changed||data.changedRuntimeFiles,scope:data.scope||data.reuse||data.authoredChange};});
const availabilityPath=path.join(h8,'joined-v45-chromium-availability/results.json');
const availability=JSON.parse(fs.readFileSync(availabilityPath,'utf8'));
const inspectedCrops=['frame-00000.png','frame-00008.png','frame-00135.png'].map(name=>{
 const p=path.join(h8,'joined-v45-chromium-availability',name);return {name,sha256:hash(fs.readFileSync(p)),inspection:'C viewed actual pixels: initial rain/header24; expired dash/empty temperature/no rain; recovered rain/header24. Card/footer readable. Day scenes do not establish all-phase Moon opacity or M0.'};});
const report={schema:'rlgwo-historical-browser-source-equivalence-v1',target:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',
 oldSource:{path:older,sha256:requiredOld},currentSource:{path:path.join(root,'index.html'),sha256:requiredNew},
 normalization:'Only CRLF to LF before explicit region comparison; complete file byte hashes retained',regions,
 retainedBrowser:{resultsPath,resultsSha256:hash(fs.readFileSync(resultsPath)),status:results.status,runtime:results.runtime.treeSha256,
  index:results.runtime.files['index.html'].sha256,harness:results.harness,browser:results.browser,runtimeUnchanged:results.runtimeUnchanged,
  cases:cases.map(c=>({family:c.family,checks:c.checks,source:c.state.weather.selected?.src,temp:c.state.header.temp,visibleParticles:c.state.visibleParticles,
   currentPrecip:c.responses[0]?.payload.current?.precipitation,requests:c.responses.length}))},
 retainedAvailability:{path:availabilityPath,sha256:hash(fs.readFileSync(availabilityPath)),status:availability.status,
  runtime:availability.runtime.treeSha256,index:availability.runtime.files['index.html'].sha256,checks:availability.checks,
  wallSeconds:availability.wallSeconds,frames:availability.frames,firstUnavailable:availability.firstUnavailable,failureConsumedAt:availability.failureConsumedAt,
  recoveryAt:availability.recoveryAt,providerFailures:availability.providerFailures,errors:availability.errors,runtimeUnchanged:availability.runtimeUnchanged,inspectedCrops},reuse,
 permittedConclusion:'The executed V45 browser current-model wet, numeric-zero-precipitation and missing-precipitation controls are retained evidence for byte-equivalent policy/admission/header regions plus explicitly scoped unchanged-policy reuse. They are not fresh final-runtime pixels.',
 gaps:'V45 does not contain temperature null/absent/genuine0 or malformed precip string, combined actual0dBZ acquisition, or zero-axis requests. Those inputs remain unverified by this browser packet. Changed unrelated presentation/integration regions do not blanket-invalidate equivalent weather policy.'};
fs.writeFileSync(path.join(__dirname,'historical-source-equivalence.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({equal:regions.filter(r=>r.equal).map(r=>r.id),different:regions.filter(r=>!r.equal).map(r=>r.id),browserCases:cases.length,
 runtime:results.runtime.treeSha256,currentPrecipControl:report.retainedBrowser.cases.filter(c=>c.family==='partial-rain'||c.family==='contradictory-rain'||c.family==='rain')},null,2));
