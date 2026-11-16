'use strict';
// R0036 current-widget verification (owner decision 2026-11-16): mutation control of the independent root checks
// that replace the formally inapplicable root-vs-V1 assertions. Each mutant edits only the STAGED root copy inside the
// runner (--root-mutant; the repository is never written) and runs the root-current configuration on the block that
// holds the check; the mutant is KILLED when every named R-check is FAIL. The unmutated control is the ordinary
// root-current run (its R-checks PASS). Browser required; isolation as in tools/qa/r0036_v1_browser.cjs.
// Usage: node tools/qa/r0036_v1_root_mutants.cjs --work <dir> [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const work=path.resolve(a.work),runner=path.join(__dirname,'r0036_v1_browser.cjs');
const MUTANTS=[
  ['hide-card','scenes',['comparison-day-dpr1:R191','comparison-night-dpr1:R191','comparison-day-dpr2:R191']],   // a blank/invisible root card
  ['no-precise-adoption','geo',['root-geo-granted:R205']],                                                       // the root no longer adopts the fix
];
const results=[];
for(const [name,blocks,ids] of MUTANTS){
  const out=path.join(work,name);fs.rmSync(out,{recursive:true,force:true});
  const r=spawnSync(process.execPath,[runner,'--mode','verify','--config','root-current','--blocks',blocks,'--root-mutant',name,'--out',out,...(a.playwright?['--playwright',a.playwright]:[])],{encoding:'utf8',timeout:600000});
  let rows=[];try{rows=JSON.parse(fs.readFileSync(path.join(out,'v1-browser-results.json'),'utf8')).rows;}catch{}
  const got=Object.fromEntries(ids.map(id=>[id,(rows.find(x=>x.id===id)||{}).result||'ABSENT']));
  const killed=r.status===1&&ids.every(id=>got[id]==='FAIL');
  results.push({name,result:killed?'PASS':'FAIL',outcome:killed?'KILLED':'SURVIVED',exitCode:r.status,checks:got});
}
console.log(JSON.stringify({schema:'r0036-v1-root-mutants/1',results},null,1));
process.exit(results.some(r=>r.result==='FAIL')?1:0);
