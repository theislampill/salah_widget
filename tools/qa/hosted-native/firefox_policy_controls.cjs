'use strict';
// All installations, policies, processes and browser pages below are synthetic.
// These controls do not launch a browser or constitute native policy evidence.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {EventEmitter}=require('node:events');
const {spawnSync}=require('node:child_process');
const vm=require('node:vm');
const S=require('./firefox_policy_source.cjs');
const P=require('./firefox_policy_probe.cjs');
const copy=value=>structuredClone(value);
function fixture(t){
  const task=fs.mkdtempSync(path.join(os.tmpdir(),'firefox-policy-source-'));t.after(()=>fs.rmSync(task,{recursive:true,force:true}));
  const write=(name,value)=>{const p=path.join(task,name);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,typeof value==='string'?value:JSON.stringify(value));return p;};
  const modules=path.join(task,'node/node_modules'),runtime={node:process.execPath,python:'/synthetic/python',modules,playwright:path.join(modules,'playwright'),pngjs:path.join(modules,'pngjs'),engine:'firefox'};
  const versions={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'};
  for(const name of ['node/package.json','node/package-lock.json'])write(name,fs.readFileSync(path.join(__dirname,name),'utf8'));
  for(const [name,version] of Object.entries(versions))write('node/node_modules/'+name+'/package.json',{name,version});
  const descriptor={browsers:[{name:'firefox',revision:'987654',browserVersion:'synthetic',installByDefault:true}]};
  const descriptorFile=write('node/node_modules/playwright-core/browsers.json',descriptor);
  const relative='node-browsers/firefox-987654/firefox/firefox';
  const executable=write(relative,'SYNTHETIC: this file is never executable or launched\n');
  const acquisition={protocol:'salah-hosted-native-acquisition/1',runtime,nodePackages:versions,
    browserDescriptors:{node:{sha256:S.record(descriptorFile).sha256,body:descriptor}},
    browserExecutables:{[relative]:{size:S.record(executable).bytes,sha256:S.record(executable).sha256}},
    locks:Object.fromEntries(['node/package.json','node/package-lock.json'].map(name=>[name,S.record(path.join(__dirname,name)).sha256]))};
  write('runtime.json',runtime);write('capture/acquisition-identity.json',acquisition);
  return {task,write,runtime,acquisition,executable,relative,admit:()=>S.admitAcquisition(task,process.execPath)};
}
function dom(){return {protocol:'firefox-effective-policy-dom/1',url:'about:policies',readyState:'complete',activeTables:1,errorTables:1,
  activeRows:[['DisableAppUpdate','true']],errorRows:[],activeCount:1,errorCount:0,inactiveVisible:false,noPoliciesVisible:false,overflow:false};}
function host(){return {uid:1200,gid:1200,uids:[1200,1200,1200,1200],gids:[1200,1200,1200,1200],groups:[],netns:'net:[31]',pidns:'pid:[32]',
  status:{CapInh:'00000000',CapPrm:'00000000',CapEff:'00000000',CapBnd:'00000000',CapAmb:'00000000',NoNewPrivs:'1'}};}
function isolation(){const h=host(),browser={protocol:'salah-hosted-browser-boundary/1',passed:true,chromiumSandbox:true,uid:h.uid,netns:h.netns,
  postNegativePage:'fresh-page-same-browser',loopbackRequests:2,externalNavigationError:'net::ERR_NETWORK_UNREACHABLE',
  processes:[{exe:'/synthetic/acquired/chrome',sha256:'a'.repeat(64),cmdline:['/synthetic/acquired/chrome']}]};
  return {protocol:'salah-hosted-native-isolation/1',passed:true,uid:h.uid,netns:h.netns,outerNetns:'net:[30]',
    kernel:{uids:[h.uid,h.uid,h.uid],gids:[h.gid,h.gid,h.gid],groups:[],netns:h.netns,links:[{ifname:'lo',flags:['LOOPBACK','UP']}],
      routes4:[{dev:'lo',dst:'127.0.0.0/8'}],routes6:[{dev:'lo',dst:'::1/128'},{dev:'lo',dst:'ff00::/8'}],status:h.status,externalSocketErrno:101},
    browserProcess:{returncode:0,timedOut:false},browserControl:browser};}
function census(rows=[]){return {protocol:'firefox-process-census/1',hostNs:'1',scanned:rows.length,totalEntries:rows.length,
  candidates:rows.map(row=>({pid:row.pid,seenExecutable:row.exe,status:'IDENTIFIED',process:row})),readFailures:[],overflow:false};}
test('synthetic acquisition binds packages, descriptor, runtime and acquired executable',t=>{const f=fixture(t),a=f.admit();assert.equal(a.executable,f.executable);assert.equal(a.runtime.node,process.execPath);assert.equal(a.nativeExecution,undefined);});
test('copied runtime package path is not authority',t=>{const f=fixture(t);f.runtime.playwright='/synthetic/other';f.write('runtime.json',f.runtime);f.acquisition.runtime=f.runtime;f.write('capture/acquisition-identity.json',f.acquisition);assert.throws(f.admit,/runtime/);});
test('copied runtime executable differs from the actual invoking Node',t=>{const f=fixture(t);f.runtime.node='/synthetic/node';f.write('runtime.json',f.runtime);f.acquisition.runtime=f.runtime;f.write('capture/acquisition-identity.json',f.acquisition);assert.throws(f.admit,/Node/);});
test('changed acquired binary is refused',t=>{const f=fixture(t);fs.appendFileSync(f.executable,'drift');assert.throws(f.admit,/executable/);});
test('changed driver descriptor is refused',t=>{const f=fixture(t);f.write('node/node_modules/playwright-core/browsers.json',{browsers:[]});assert.throws(f.admit,/descriptor/);});
test('changed installed package version is refused',t=>{const f=fixture(t);f.write('node/node_modules/playwright/package.json',{version:'0.0.0'});assert.throws(f.admit,/package/);});
test('current package source population is retained and later module drift refuses policy preparation',t=>{const f=fixture(t);f.write('node/node_modules/playwright/synthetic-driver.cjs','source-only double');const a=f.admit();assert.ok(a.packages.playwright.currentFiles['synthetic-driver.cjs']);f.write('node/node_modules/playwright/synthetic-driver.cjs','changed');assert.throws(()=>S.preparePolicy(a,[]),/acquisition changed/);});
test('installed task package lock must match the original acquired lock',t=>{const f=fixture(t);f.write('node/package-lock.json','{}');assert.throws(f.admit,/lock/);});
test('symlink in task-owned installation is refused',t=>{const f=fixture(t);fs.renameSync(f.executable,f.executable+'.real');fs.symlinkSync(f.executable+'.real',f.executable);assert.throws(f.admit,/symlink/);});
test('policy is exclusive, exact, re-admitted and leaves other distribution files unchanged',t=>{const f=fixture(t),a=f.admit();const other=f.write(path.relative(f.task,path.join(path.dirname(a.executable),'distribution/other.txt')),'unchanged');
  const r=S.preparePolicy(a,[]);assert.equal(fs.readFileSync(r.policy.path,'utf8'),S.POLICY);assert.equal(fs.readFileSync(other,'utf8'),'unchanged');assert.deepEqual(S.admitPolicy(a,r),r);assert.throws(()=>S.preparePolicy(a,[]),/already exists/);});
test('any existing policy is refused without replacement',t=>{const f=fixture(t),a=f.admit(),p=f.write(path.relative(f.task,path.join(path.dirname(a.executable),'distribution/policies.json')),'old policy');assert.throws(()=>S.preparePolicy(a,[]),/already exists/);assert.equal(fs.readFileSync(p,'utf8'),'old policy');});
test('existing live installation is refused before policy write',t=>{const f=fixture(t),a=f.admit();assert.throws(()=>S.preparePolicy(a,[{pid:19}]),/live/);assert.equal(fs.existsSync(path.join(path.dirname(a.executable),'distribution/policies.json')),false);});
test('policy symlink directory is refused',t=>{const f=fixture(t),a=f.admit();fs.symlinkSync(f.task,path.join(path.dirname(a.executable),'distribution'));assert.throws(()=>S.preparePolicy(a,[]),/symlink/);});
test('policy drift after preparation is refused',t=>{const f=fixture(t),a=f.admit(),r=S.preparePolicy(a,[]);fs.appendFileSync(r.policy.path,' ');assert.throws(()=>S.admitPolicy(a,r),/policy/);});
test('policy preparation cannot rebind its acquisition record',t=>{const f=fixture(t),a=f.admit(),r=S.preparePolicy(a,[]);r.acquisition.sha256='0'.repeat(64);assert.throws(()=>S.admitPolicy(a,r),/acquisition/);});
test('effective policy requires genuine DOM contract beyond a file assertion',()=>{assert.equal(S.admitPolicyDom(dom()),true);assert.throws(()=>S.admitPolicyDom({policies:{DisableAppUpdate:true}}),/DOM/);});
test('false effective policy is refused',()=>{const d=dom();d.activeRows[0][1]='false';assert.throws(()=>S.admitPolicyDom(d),/active/);});
test('unexpected managed policy is refused',()=>{const d=dom();d.activeRows.push(['DisableTelemetry','true']);d.activeCount=2;assert.throws(()=>S.admitPolicyDom(d),/active/);});
test('policy error rows are refused',()=>{const d=dom();d.errorRows=[['DisableAppUpdate','error']];d.errorCount=1;assert.throws(()=>S.admitPolicyDom(d),/error/);});
test('missing, wrong URL, inactive, incomplete and overflowing DOM records are refused',()=>{for(const change of [{activeTables:0},{url:'about:blank'},{inactiveVisible:true},{noPoliciesVisible:true},{readyState:'loading'},{overflow:true}])assert.throws(()=>S.admitPolicyDom({...dom(),...change}));});
test('strict current namespace receipt accepts the complete synthetic structure only',()=>{assert.equal(S.validateIsolation(isolation(),host()),true);assert.throws(()=>S.validateIsolation({passed:true,browserControl:{passed:true}},host()),/isolation/);});
test('current namespace and UID cannot be rebound',()=>{for(const change of [{uid:0},{netns:'net:[88]'}])assert.throws(()=>S.validateIsolation(isolation(),{...host(),...change}));});
test('capabilities, routes and boolean outer status cannot masquerade as clean isolation',()=>{for(const mutate of [r=>r.kernel.status.CapEff='1',r=>r.kernel.routes4.push({dev:'eth0',dst:'default'}),r=>r.browserProcess.returncode=false,r=>r.browserProcess.timedOut=0,r=>r.browserControl.chromiumSandbox=false]){const r=copy(isolation());mutate(r);assert.throws(()=>S.validateIsolation(r,host()));}});
test('same original browser boundary body is required from its retained sibling',t=>{const f=fixture(t),r=isolation(),file=f.write('isolation/receipt.json',r);f.write('isolation/browser.json',r.browserControl);f.write('isolation/browser.stdout','');f.write('isolation/browser.stderr','');assert.equal(S.readIsolation(file,host()).body.uid,1200);f.write('isolation/browser.json',{passed:true});assert.throws(()=>S.readIsolation(file,host()),/body/);});
test('unexpected close remains a late lifecycle fault after requested cleanup',()=>{const target=new EventEmitter();let open=true;const watch=S.watch(target,'page',()=>open);open=false;target.emit('close');watch.requestCleanup();assert.equal(watch.state.faults.length,2);});
test('late page crash and pageerror remain disqualifying',()=>{const target=new EventEmitter(),watch=S.watch(target,'page',()=>true);watch.requestCleanup();target.emit('crash');target.emit('pageerror',Error('late'));assert.equal(watch.state.faults.length,2);});
test('requested cleanup close is distinct from premature close',()=>{const target=new EventEmitter(),watch=S.watch(target,'browser',()=>true);watch.requestCleanup();target.emit('disconnected');assert.deepEqual(watch.state.faults,[]);assert.equal(watch.state.closed,true);});
test('bounded lifecycle records disclose overflow',()=>{const target=new EventEmitter(),watch=S.watch(target,'page',()=>true);for(let i=0;i<100;i++)target.emit('crash');assert.equal(watch.state.faults.length,S.LIMITS.faults);assert.equal(watch.state.overflow,true);});
test('strict original refusal takes precedence over later readback or cleanup failure',()=>{assert.equal(S.resultCode({network:{ok:false},error:{message:'other'},cleanup:{complete:false}}),86);assert.equal(S.resultCode({isolationError:{message:'bad'}}),86);});
test('success-shaped DOM alone cannot admit a completed native diagnostic',()=>{assert.equal(S.resultCode({initial:dom(),final:dom(),network:{ok:true}}),2);});
test('outer malformed, nonzero or timeout process cannot promote an inner success',()=>{const report={status:'OBSERVED_FIREFOX_POLICY'};for(const p of [{returncode:false,timedOut:false},{returncode:0,timedOut:0},{returncode:1,timedOut:false},{returncode:0,timedOut:true}])assert.equal(P.outerDisposition(p,report).status,'INCOMPLETE');});
test('outer isolation failure has precedence and stops subsequent work',()=>{assert.deepEqual(P.outerDisposition({returncode:86,timedOut:false},{status:'INCOMPLETE'}),{status:'ISOLATION_FAIL',exitCode:86,stopAll:true});});
test('CLI rejects alternate engine, dwell, package override, repeated arguments and child tokens',()=>{for(const args of [['--engine','chromium'],['--dwell','1'],['--playwright','/synthetic'],['--task','/x','--task','/y'],['--worker','1']])assert.throws(()=>P.parse(args));});
test('aggregate observation envelope preserves full evidence waits and bounded cleanup',()=>{assert.equal(S.BUDGET.dwellMs,60000);assert.ok(Object.values(S.BUDGET.phases).reduce((a,b)=>a+b,0)<=S.BUDGET.childSeconds);assert.ok(S.BUDGET.childSeconds+S.BUDGET.preflightSeconds+S.BUDGET.killGraceSeconds+S.BUDGET.intakeSeconds<=S.BUDGET.entrySeconds);});
function fakeObservation(t,changes={}){
  const f=fixture(t),acquired=f.admit(),out=path.join(f.task,'capture/firefox-policy');fs.mkdirSync(out);
  const admission={acquired,source:{fixture:'source-only double'},isolation:{host:host(),receipt:{fixture:'source-only boundary'}}};
  const original=require('../r0033_isolation.cjs'),browser=new EventEmitter(),context=new EventEmitter(),page=new EventEmitter();
  let connected=true,closed=false,clock=0n,scans=0,reads=0,closeAttempted=false;const nodeState={installed:false,refused:[],allowed:0,proxyVarsRemoved:[]};
  const ledger=original.newLedger(),root={...host(),pid:87654321,ppid:process.pid,startTicks:'1',exe:f.executable,argv:[f.executable],binary:acquired.binary};
  Object.assign(page,{isClosed:()=>closed,waitForFunction:async()=>{if(changes.readiness)throw Error('synthetic readiness failure');},
    evaluate:async()=>{reads++;return changes.badDom?{...dom(),activeRows:[['DisableAppUpdate','false']]}:dom();},
    goto:async()=>{if(changes.goto){ledger.requests.push({url:'about:policies',action:'continue',type:'document'});page.emit('pageerror',Error('synthetic page setup failure'));throw Error('synthetic goto failure');}}});
  Object.assign(context,{newPage:async()=>{context.emit('page',page);return page;}});
  Object.assign(browser,{isConnected:()=>connected,version:()=>'<synthetic browser double>',newContext:async()=>context,
    close:async()=>{closeAttempted=true;if(changes.lateCrash)page.emit('crash');if(changes.cleanup)throw Error('synthetic cleanup failure');closed=true;connected=false;page.emit('close');context.emit('close');browser.emit('disconnected');}});
  const isolationModule={FIREFOX_PREFS:original.FIREFOX_PREFS,launch:async launcher=>{
    if(changes.launch){nodeState.refused.push({kind:'dns',target:'synthetic.invalid'});throw Error('synthetic launch failure');}
    const b=await launcher.firefox.launch({headless:true,args:[],firefoxUserPrefs:original.FIREFOX_PREFS,proxy:{server:'http://127.0.0.1:12345',bypass:'127.0.0.1,localhost'}});
    return {browser:b,ledger,context:async()=>{const ctx=await b.newContext();if(changes.context)throw Error('synthetic route setup failure');return {context:ctx,newPage:()=>ctx.newPage()};},
      close:async()=>{if(changes.refusal)ledger.proxyRefused.push({target:'synthetic.invalid:443'});await b.close();},settle:async()=>{},verdict:()=>original.verdict(ledger,nodeState.refused)};
  }};
  const dependencies={isolationModule,playwright:{firefox:{executablePath:()=>f.executable,launch:async()=>{
      assert.equal(fs.readFileSync(path.join(path.dirname(f.executable),'distribution/policies.json'),'utf8'),S.POLICY,'policy precedes this synthetic launch');return browser;
    }}},
    guard:{state:nodeState,install(){nodeState.installed=true;}},census:()=>++scans===1?census():changes.censusFailure?{...census(),readFailures:[{pid:87654321,phase:'executable-link',code:'EACCES',message:'synthetic denied'}]}:census([root]),sameLive:()=>!!changes.liveAfter,
    sleep:async ms=>{clock+=BigInt(ms)*1000000n;if(changes.prematureClose){closed=true;page.emit('close');}},now:()=>clock,current:()=>admission};
  return {f,out,admission,dependencies,ledger,nodeState,run:()=>P.observe({out},admission,dependencies),state:()=>({reads,closeAttempted})};
}
test('complete synthetic browser double exercises the observed-only path and unchanged launch preferences',async t=>{
  const f=fakeObservation(t),result=await f.run();assert.equal(result.exitCode,0);assert.equal(result.report.status,'OBSERVED_FIREFOX_POLICY');assert.equal(f.state().reads,2);
  assert.equal(result.report.refinedCapture,'NOT_OBSERVED');assert.equal(result.report.historicalFirstStartup,'NOT_ESTABLISHED');assert.equal(P.outerDisposition({returncode:0,timedOut:false,signal:null},result.report).exitCode,0);
  assert.equal(result.report.launch.options.firefoxUserPrefs,require('../r0033_isolation.cjs').FIREFOX_PREFS);
});
test('foreign engine or native acceptance claims cannot be admitted by otherwise complete diagnostic evidence',async t=>{
  const {report}=await fakeObservation(t).run();
  for(const change of [{engine:'webkit'},{nativeProductAcceptance:'PASS'},{originalFailedObservation:'SUPERSEDED'},{refinedCapture:'OBSERVED'},{historicalFirstStartup:'PROVEN'}])assert.equal(S.resultCode({...report,...change}),2);
});
test('shortened or reordered driver-clock dwell remains incomplete',async t=>{
  const {report}=await fakeObservation(t).run();
  for(const change of [{endedNs:'1'},{startedNs:report.final.hostNs,endedNs:report.initial.hostNs}])assert.equal(S.resultCode({...report,dwell:{...report.dwell,...change}}),2);
});
test('failed navigation retains its acquired ledger, page faults and original error through cleanup',async t=>{
  const f=fakeObservation(t,{goto:true}),result=await f.run();assert.equal(result.exitCode,2);assert.match(result.report.error.message,/goto/);assert.equal(result.report.ledger.requests.length,1);
  assert.ok(result.report.lifecycle.find(r=>r.kind==='page').faults.some(r=>r.event==='pageerror'));assert.equal(f.state().closeAttempted,true);assert.ok(fs.existsSync(path.join(f.out,'network.json')));
});
test('failed guarded context setup retains its context owner and cleanup fault evidence',async t=>{
  const f=fakeObservation(t,{context:true,cleanup:true}),r=await f.run();assert.equal(r.exitCode,2);assert.match(r.report.error.message,/route setup/);
  assert.equal(r.report.lifecycle.filter(x=>x.kind==='context').length,1);assert.ok(r.report.errors.some(x=>x.phase==='cleanup'));
});
test('startup Node refusal survives missing original proxy/session handle',async t=>{
  const f=fakeObservation(t,{launch:true}),r=await f.run();assert.equal(r.exitCode,86);assert.equal(r.report.nodeGuard.refused.length,1);
  assert.ok(r.report.errors.some(x=>x.phase==='proxy-custody'));assert.equal(r.report.cleanup.complete,false);
});
test('late proxy refusal overrides effective policy, page faults and cleanup errors',async t=>{
  const f=fakeObservation(t,{refusal:true,lateCrash:true,cleanup:true}),r=await f.run();assert.equal(r.exitCode,86);assert.equal(r.report.network.ok,false);assert.equal(r.report.initial.dom.activeRows[0][1],'true');
});
test('late page crash after final readback cannot become an observed result',async t=>{const r=await fakeObservation(t,{lateCrash:true}).run();assert.equal(r.exitCode,2);assert.ok(r.report.final);});
test('premature context/page close cannot be excused by eventual requested cleanup',async t=>{const r=await fakeObservation(t,{prematureClose:true}).run();assert.equal(r.exitCode,2);assert.ok(r.report.lifecycle.find(x=>x.kind==='page').faults.length>0);});
test('a tracked live Firefox process makes complete DOM readback inadmissible',async t=>{const r=await fakeObservation(t,{liveAfter:true}).run();assert.equal(r.exitCode,2);assert.equal(r.report.cleanup.trackedProcessesStopped,false);});
test('failed effective policy does not skip available cleanup or turn into a source-only success',async t=>{const f=fakeObservation(t,{badDom:true}),r=await f.run();assert.equal(r.exitCode,2);assert.equal(f.state().closeAttempted,true);assert.equal(r.report.final,undefined);});
test('readiness timeout retains the obtained DOM without admitting a late valid-looking value',async t=>{const r=await fakeObservation(t,{readiness:true}).run();assert.equal(r.exitCode,2);assert.equal(r.report.initial.dom.activeRows[0][1],'true');assert.ok(r.report.initial.waitError);});
test('failed live process census retains candidate counts and actual read failures before owner admission',async t=>{
  const f=fakeObservation(t,{censusFailure:true}),r=await f.run();assert.equal(r.exitCode,2);assert.match(r.report.error.message,/read failure/);
  const retained=JSON.parse(fs.readFileSync(path.join(f.out,'process-census-started.json'),'utf8'));assert.equal(retained.candidates.length,0);assert.equal(retained.readFailures[0].code,'EACCES');assert.equal(f.state().closeAttempted,true);
});
test('bounded census retains executable-link and partially acquired candidate errors',t=>{
  const f=fixture(t),a=f.admit(),denied=()=>{throw Object.assign(Error('synthetic EACCES'),{code:'EACCES'});};
  const r=S.liveInstallation(a,{entries:()=>['17','19'],readExe:pid=>pid===17?denied():f.executable,processInfo:denied});
  assert.equal(r.scanned,2);assert.equal(r.candidates.length,1);assert.equal(r.candidates[0].seenExecutable,f.executable);assert.equal(r.readFailures.length,2);assert.equal(r.candidates[0].status,'INCOMPLETE');assert.throws(()=>S.censusRows(r),/read failure/);
});
test('zero or multiple process owners never admit; diagnostic candidate details remain available',()=>{
  assert.throws(()=>S.ownedProcesses(census(),host(),7),/no acquired/);
  const rows=[{...host(),pid:8,ppid:7,startTicks:'1'},{...host(),pid:9,ppid:7,startTicks:'2'}],r=census(rows);
  assert.throws(()=>S.ownedProcesses(r,host(),7),/one direct/);assert.equal(r.candidates.length,2);
});
test('process census bound is explicit rather than dropping excess entries silently',t=>{
  const f=fixture(t),r=S.liveInstallation(f.admit(),{entries:()=>Array.from({length:S.LIMITS.censusEntries+1},(_,i)=>String(i+1)),readExe:()=>'/synthetic/unrelated'});
  assert.equal(r.overflow,true);assert.equal(r.scanned,S.LIMITS.censusEntries);assert.throws(()=>S.censusRows(r),/overflowing/);
});
test('effective DOM collector records bounds and ignores messages hidden by an ancestor',()=>{
  const active={children:[{tagName:'TR',children:[{textContent:'DisableAppUpdate'},{textContent:'true'}]}]},errors={children:[]};
  const document={readyState:'complete',querySelectorAll:selector=>selector==='#activeContent'?[active]:selector==='#errorsContent'?[errors]:[{hidden:false,getClientRects:()=>[]}]};
  const context={document,location:{href:'about:policies'},getComputedStyle:()=>({display:'block',visibility:'visible'})};
  const read=()=>vm.runInNewContext('('+S.readPoliciesDom.toString()+')()',context);S.admitPolicyDom(JSON.parse(JSON.stringify(read())));
  active.children[0].children[1].textContent='x'.repeat(1025);assert.equal(read().overflow,true);
});
test('missing current isolation exits86 before creating output, policy or importing Playwright',t=>{
  const f=fixture(t),out=path.join(f.task,'capture/firefox-policy'),isolation=path.join(f.task,'capture/isolation/policy/receipt.json');
  const result=spawnSync(process.execPath,[path.join(__dirname,'firefox_policy_probe.cjs'),'--task',f.task,'--out',out,'--isolation',isolation,'--pins-sha256','0'.repeat(64)],{encoding:'utf8',timeout:5000,env:{...process.env,SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT:isolation}});
  assert.equal(result.status,86);assert.match(result.stderr,/ISOLATION_FAIL/);assert.equal(fs.existsSync(out),false);assert.equal(fs.existsSync(path.join(path.dirname(f.executable),'distribution')),false);
});
test('actual bounded source-only child process retains argv, cwd, exit and streams',async t=>{
  const out=fs.mkdtempSync(path.join(os.tmpdir(),'firefox-policy-child-'));t.after(()=>fs.rmSync(out,{recursive:true,force:true}));
  const argv=[process.execPath,'-e','process.stdout.write("synthetic child\\n");process.stderr.write("synthetic stderr\\n")'];const r=await P.runChild(argv,out,5);
  assert.equal(r.returncode,0);assert.equal(r.timedOut,false);assert.deepEqual(r.argv,argv);assert.equal(fs.readFileSync(r.stdout.path,'utf8'),'synthetic child\n');assert.equal(fs.readFileSync(r.stderr.path,'utf8'),'synthetic stderr\n');
});
test('actual bounded source-only child timeout cannot be promoted by a success-shaped report',async t=>{
  const out=fs.mkdtempSync(path.join(os.tmpdir(),'firefox-policy-timeout-'));t.after(()=>fs.rmSync(out,{recursive:true,force:true}));
  const r=await P.runChild([process.execPath,'-e','setInterval(()=>{},1000)'],out,.05);assert.equal(r.timedOut,true);assert.equal(P.outerDisposition(r,{status:'OBSERVED_FIREFOX_POLICY'}).status,'INCOMPLETE');
});
test('current source packet has the exact independently supplied ten-file closure',()=>{
  const file=path.join(__dirname,'firefox-policy-pins.json'),digest=S.record(file).sha256,admitted=S.packet(digest);
  assert.equal(Object.keys(admitted.files).length,10);assert.throws(()=>S.packet('0'.repeat(64)),/manifest digest/);
});
function copiedPacket(t){
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'firefox-policy-closure-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  for(const name of [...S.FILES,'tools/qa/hosted-native/firefox-policy-pins.json']){const out=path.join(root,name);fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(path.join(S.ROOT,name),out);}
  const source=require(path.join(root,'tools/qa/hosted-native/firefox_policy_source.cjs')),manifest=path.join(root,'tools/qa/hosted-native/firefox-policy-pins.json');
  return {root,source,manifest,digest:S.record(manifest).sha256};
}
test('source drift in an isolated packet copy is rejected without touching the authored tree',t=>{
  const f=copiedPacket(t);f.source.packet(f.digest);fs.appendFileSync(path.join(f.root,'tools/qa/r0033_isolation.cjs'),'\n// synthetic source drift\n');assert.throws(()=>f.source.packet(f.digest),/source drift/);
});
test('an extra manifest source member remains rejected even when its replacement digest is explicitly supplied',t=>{
  const f=copiedPacket(t),manifest=JSON.parse(fs.readFileSync(f.manifest,'utf8'));manifest.files['unreviewed.cjs']={bytes:0,sha256:'0'.repeat(64)};fs.writeFileSync(f.manifest,JSON.stringify(manifest));
  assert.throws(()=>f.source.packet(S.record(f.manifest).sha256),/population/);
});
