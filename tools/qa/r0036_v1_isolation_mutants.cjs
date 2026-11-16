'use strict';
// R0036 V1 browser verification: mutation control of the isolation self-test (browser required; registered as a
// native recipe). Each mutant copies tools/qa/{r0036_v1_browser.cjs,v1_net_guard.cjs,v1_net_guard.py,
// v1_browser_helpers.py} to a disposable directory, removes ONE isolation layer, and runs `--mode selftest`; the
// mutant is KILLED when the self-test fails with the named check false. Safety while a layer is removed: the probes
// that remain active target 0.0.0.0 (refused by the OS locally) or a hostname the browser cannot resolve (the
// launch-level host-resolver rule), and name probes from Node/Python run only while their guard is proven installed.
// Usage: node tools/qa/r0036_v1_isolation_mutants.cjs --work <dir> [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const QA=__dirname,REPO=path.resolve(QA,'..','..'),work=path.resolve(a.work);
const FILES=['r0036_v1_browser.cjs','v1_net_guard.cjs','v1_net_guard.py','v1_browser_helpers.py'];
const MUTANTS=[
  ['no-browser-route','r0036_v1_browser.cjs',"await context.route('**/*',route=>{","await (async()=>{})(route=>{",'pageFetchRefusedByRoute'],
  ['no-websocket-route','r0036_v1_browser.cjs',"await context.routeWebSocket(/.*/,ws=>{","await (async()=>{})(ws=>{",'pageWebSocketRefusedByRoute'],
  ['no-node-guard','r0036_v1_browser.cjs',"const guard=require('./v1_net_guard.cjs');guard.install();","const guard=require('./v1_net_guard.cjs');",'nodeRefusedByGuard'],
  ['no-python-guard','v1_browser_helpers.py','v1_net_guard.install()\n','pass\n','pythonUrlopenRefusedByGuard'],
  // The refusing proxy is replaced by --no-proxy-server (never by a system proxy); the IP-literal probes then stay off.
  ['no-refusing-proxy','r0036_v1_browser.cjs',"['--proxy-server=http://127.0.0.1:'+PROXY_PORT,","['--no-proxy-server',",'redirectRefusedAtProxy'],
];
const results=[];
for(const [name,file,from,to,check] of [['control',null,null,null,null],...MUTANTS]){
  const dir=path.join(work,name);fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  for(const f of FILES)fs.copyFileSync(path.join(QA,f),path.join(dir,f));
  if(file){const p=path.join(dir,file),t=fs.readFileSync(p,'utf8');if(t.split(from).length!==2){results.push({name,result:'INCOMPLETE',error:'anchor'});continue;}fs.writeFileSync(p,t.replace(from,()=>to));}
  const r=spawnSync(process.execPath,[path.join(dir,'r0036_v1_browser.cjs'),'--mode','selftest','--root',REPO,'--out',path.join(dir,'out'),...(a.playwright?['--playwright',a.playwright]:[])],{encoding:'utf8',timeout:120000});
  let checks=null;try{checks=JSON.parse(fs.readFileSync(path.join(dir,'out','selftest.json'),'utf8')).selftest.checks;}catch{}
  if(!file)results.push({name,result:r.status===0&&checks&&Object.values(checks).every(Boolean)?'PASS':'INCOMPLETE',exitCode:r.status,checks});
  else{const killed=r.status!==0&&checks&&checks[check]===false;results.push({name,result:killed?'PASS':'FAIL',outcome:killed?'KILLED':'SURVIVED',check,exitCode:r.status,checks});}
}
console.log(JSON.stringify({schema:'r0036-v1-isolation-mutants/1',results},null,1));
process.exit(results.some(r=>r.result==='INCOMPLETE')?2:results.some(r=>r.result==='FAIL')?1:0);
