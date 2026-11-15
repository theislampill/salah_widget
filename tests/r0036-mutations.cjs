'use strict';
// R0036 (issue 103) mutation controls (ES36-13, plus amendment R0036-A1 ES36-06(c)). Each mutant edits ONE exact
// anchor in a disposable copy of the product files under --work (default: a fresh OS temp directory, removed
// afterwards); nothing in the repository is written. A mutant is KILLED only when the suite exits 1 AND its named
// discriminator is among the failing tests (result PASS = killed, FAIL = survived); an anchor that does not occur
// exactly once, or a control suite failing on the unmutated copy, is INCOMPLETE (exit 2).
// Usage: node tests/r0036-mutations.cjs [--work <dir>] [--only <name>]
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const arg=n=>process.argv.includes(n)?process.argv[process.argv.indexOf(n)+1]:null;
const FILES=['index.html','config.js','tests/smoke.html','real-sky/native-composition.mjs','real-sky/native-cloud-transfer.mjs',
  ...fs.readdirSync(path.join(root,'moon/src')).map(f=>'moon/src/'+f)];
const T={purity:'tests/r0036-diagnostic-purity.test.cjs',outcome:'tests/r0036-outcome-records.test.cjs',flags:'tests/r0036-acquisition-flags.test.cjs',moon:'moon/tests/r0036-observe.test.cjs'};
const MUTANTS=[
  // Stage 5 list of the issue (§8 step 5) and the A1 mutant.
  ['storage-probe','index.html','return {storageAvailable:readable,','return {storageAvailable:(window.SalahConfig?SalahConfig.storageAvailable().ok:false),',T.purity,'R36-01'],
  ['observe-through-presentation','moon/src/moon-native.mjs','current=!!s&&matches(accepted,s),wouldPresent','current=!!s&&presentation(s),wouldPresent',T.moon,'R36-30'],
  ['drop-admission-write','index.html','if(j.error===true){ wxAdmission(op,a,"provider-error"); return; }','if(j.error===true){ return; }',T.outcome,'R36-10'],
  ['restore-simulated-predicate','index.html','return {simulated:on.length>0,','return {simulated:(SIM.wx!=null||SIM.time!=null||SIM.moon!=null),',T.purity,'R36-06'],
  ['remove-superseded-write','index.html','if(_autoDetectStatus==="pending") _autoDetectStatus="superseded"; ','',T.flags,'R36-20'],
  ['wrapper-reads-state','index.html','const m=window.SalahMoonRuntime?.observe?.()?.state??null;','const m=window.SalahMoonRuntime?.state;',T.purity,'R36-04'],
  ['delete-capture-reconcile','real-sky/native-composition.mjs','const cloudAuthority=window.SalahNativeSkyHost.reconcileClouds();','const cloudAuthority=null;',T.purity,'R36-07'],
  // Further controls, one per remaining fix.
  ['qa-reads-surface','index.html','observation=typeof runtime?.observe==="function"?runtime.observe():null,refined=!!observation?.surface,lunarState=observation?.state;',
    'observation=null,refined=!!runtime?.surface(),lunarState=runtime?.state;',T.purity,'R36-04'],
  ['no-memo-restore','index.html','finally{ if(memo){ _wxDecisionCache=memo[0];','finally{ if(false){ _wxDecisionCache=memo[0];',T.purity,'R36-03'],
  ['smoke-adopting-backing','tests/smoke.html','backing=observed?.surface??null','backing=api?.surface?.()',T.purity,'R36-05'],
  ['drop-zone-admission','index.html','"response timezone unavailable or contradicts captured request"); wxAdmission(op,a,"zone-rejected"); return;','"response timezone unavailable or contradicts captured request"); return;',T.outcome,'R36-10'],
  ['drop-superseded-label','index.html','  else if(admission==="superseded") wxAdmission(op,a,admission);','',T.outcome,'R36-11'],
  ['retained-as-admitted','index.html','miss?"early-renewal-miss":current?"retained-current":','miss?"early-renewal-miss":current?"admitted":',T.outcome,'R36-10'],
  ['radar-malformed-unlabelled','index.html','if(!Array.isArray(past)) wxAdmission(op,a,"malformed-manifest");','if(!Array.isArray(past)) wxAdmission(op,a,"no-frame");',T.outcome,'R36-12'],
  ['reset-detect-unsettled','index.html','  if(detect.status==="pending") Object.assign(detect,','  if(false) Object.assign(detect,',T.flags,'R36-21'],
  ['geo-error-forever-current','index.html','superseded:g.outcome==="superseded"||!_ownsSetLookup(g.owner)}','superseded:g.outcome==="superseded"}',T.flags,'R36-22'],
  ['storage-write-quota-false','index.html','ls.getItem("__sw_probe__"); readable=true;','ls.setItem("__sw_probe__","1"); ls.removeItem("__sw_probe__"); readable=true;',T.purity,'R36-01'],
];
const only=arg('--only'),work=arg('--work')||fs.mkdtempSync(path.join(os.tmpdir(),'r0036-mut-')),own=!arg('--work');
const {NODE_TEST_CONTEXT,...env}=process.env;
const results=[];let setup=0;
const copy=name=>{const dir=path.join(work,name);fs.rmSync(dir,{recursive:true,force:true});
  for(const f of FILES){fs.mkdirSync(path.dirname(path.join(dir,f)),{recursive:true});fs.copyFileSync(path.join(root,f),path.join(dir,f));}return dir;};
const runSuite=(suite,dir)=>{const r=spawnSync(process.execPath,['--test','--test-reporter=tap',path.join(root,suite)],{encoding:'utf8',cwd:root,
    env:{...env,R0036_ROOT:dir,SALAH_WEATHER_SOURCE:path.join(dir,'index.html'),SALAH_MOON_SOURCE_DIR:path.join(dir,'moon/src')}});
  return {r,failed:(r.stdout||'').split(/\r?\n/).filter(l=>/^\s*not ok \d+ - /.test(l)).map(l=>l.replace(/^\s*not ok \d+ - /,''))};};
// Control: every suite passes on the UNMUTATED copy, so a kill below is caused by its mutant, not by the copy.
if(!only){const dir=copy('control');for(const suite of Object.values(T)){const {r,failed}=runSuite(suite,dir);
  results.push({name:'control '+suite,result:r.status===0?'PASS':'INCOMPLETE',exitCode:r.status,failed});if(r.status!==0)setup++;}fs.rmSync(dir,{recursive:true,force:true});}
for(const [name,file,from,to,suite,discriminator] of MUTANTS){
  if(only&&only!==name)continue;
  const dir=copy(name);
  const target=path.join(dir,file),text=fs.readFileSync(target,'utf8'),n=text.split(from).length-1;
  if(n!==1){results.push({name,result:'INCOMPLETE',error:'anchor occurs '+n+' times in '+file});setup++;continue;}
  fs.writeFileSync(target,text.replace(from,()=>to));
  const {r,failed}=runSuite(suite,dir);
  const killed=r.status===1&&failed.some(t=>t.startsWith(discriminator));
  results.push({name,file,suite,discriminator,result:killed?'PASS':'FAIL',outcome:killed?'KILLED':'SURVIVED',exitCode:r.status,failed});
  fs.rmSync(dir,{recursive:true,force:true});
}
if(own)fs.rmSync(work,{recursive:true,force:true});
const killed=results.filter(r=>r.outcome==='KILLED').length,survived=results.filter(r=>r.outcome==='SURVIVED').length;
console.log(JSON.stringify({schema:'r0036-mutations/1',rows:results.length,killed,survived,setup,results},null,1));
process.exit(setup?2:survived?1:0);
