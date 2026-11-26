'use strict';
// Synthetic Firefox failure-only controls. No browser or namespace is launched.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {EventEmitter}=require('node:events');
const S=require('./firefox_policy_source.cjs'),P=require('./firefox_policy_probe.cjs');
const F=require('./firefox_failure_diagnostic.cjs'),crypto=require('node:crypto'),vm=require('node:vm');
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
function fakeObservation(t,changes={}){
  const f=fixture(t),acquired=f.admit(),out=path.join(f.task,'capture/firefox-policy');fs.mkdirSync(out);
  const admission={acquired,source:{fixture:'source-only double'},isolation:{host:host(),receipt:{fixture:'source-only boundary'}}};
  const original=require('../r0033_isolation.cjs'),browser=new EventEmitter(),context=new EventEmitter(),page=new EventEmitter();
  let connected=true,closed=false,clock=0n,scans=0,reads=0,closeAttempted=false;const nodeState={installed:false,refused:[],allowed:0,proxyVarsRemoved:[]};
  const ledger=original.newLedger(),root={...host(),pid:87654321,ppid:process.pid,startTicks:'1',exe:f.executable,argv:[f.executable],binary:acquired.binary};
  const mainFrame={url:()=>page.url()};
  Object.assign(page,{url:()=>changes.url||'about:policies',mainFrame:()=>mainFrame,isClosed:()=>closed,waitForFunction:async()=>{if(changes.readiness)throw Error('synthetic readiness failure');},
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
  return {f,out,admission,dependencies,ledger,nodeState,page,browser,context,root,mainFrame,tick:ms=>{clock+=BigInt(ms)*1000000n;},run:()=>P.observe({out},admission,dependencies),state:()=>({reads,closeAttempted})};
}

test('failure-only: complete synthetic original success has no failure output fields',async t=>{
  const f=fakeObservation(t),r=await f.run();assert.equal(r.exitCode,0);assert.equal(f.state().reads,2);
  for(const name of ['failureDiagnostic','cleanupProcesses'])assert.equal(Object.hasOwn(r.report,name),false);
});
test('failure-only: navigation rejection retains original error plus one diagnostic DOM read',async t=>{
  const f=fakeObservation(t,{goto:true}),r=await f.run();assert.equal(r.exitCode,2);assert.match(r.report.error.message,/synthetic goto failure/);
  assert.equal(r.report.initial,undefined);assert.equal(r.report.final,undefined);assert.equal(r.report.finalProcesses,undefined);assert.equal(r.report.dwell,undefined);
  assert.equal(f.state().reads,1,'one failure-only read of the existing DOM evaluator');
  assert.equal(r.report.failureDiagnostic.failedPhase,'NAVIGATION');assert.equal(r.report.failureDiagnostic.readback.status,'CAPTURED');
  assert.deepEqual(r.report.failureDiagnostic.readback.dom,dom());assert.equal(r.report.cleanupProcesses.status,'COLLECTED');
});
test('failure-only: original goto arguments and main/subframe event ownership are retained',async t=>{
  const f=fakeObservation(t);let calls=0;
  f.page.goto=async(url,options)=>{calls++;assert.equal(url,'about:policies');assert.deepEqual(options,{waitUntil:'load',timeout:20000});
    f.page.emit('framenavigated',{url:()=> 'https://synthetic.invalid/subframe'});f.page.emit('framenavigated',f.mainFrame);
    f.page.emit('domcontentloaded');f.page.emit('load');throw Error('synthetic navigation timeout');};
  const r=await f.run();assert.equal(r.exitCode,2);assert.equal(calls,1);const n=r.report.failureDiagnostic.navigation;
  assert.equal(n.subframeEvents,1);assert.deepEqual(n.events.map(x=>x.event),['framenavigated','domcontentloaded','load']);
  assert.ok(n.events.every(x=>x.mainFrame===true));assert.deepEqual(n.snapshots.map(x=>x.phase),['before-attempt','on-rejection','before-cleanup']);
});
test('failure-only: missing final success census refuses distinctly from proven liveness',()=>{
  const code=P.supervise.toString(),line=code.split('\n').find(x=>x.includes('report.processes?.observed?.every'));
  assert.ok(line,'the original liveness predicate remains in the real parent');
  const run=new Function('report','S','need','F',line),report={processes:{observed:[{pid:19,startTicks:'1'}]}};
  let actual;try{run(report,{sameLive:()=>false},S.need,{cleanupPredicateMessage:r=>r.finalProcesses?'a tracked Firefox process remains live':'missing required success-path process census; tracked liveness is not established by this absence'});}catch(e){actual=e;}
  assert.match(actual?.message||'',/missing required success-path process census/);
});

test('failure-only: original success performs no diagnostic DOM or process read',async t=>{
  const f=fakeObservation(t);let attempts=0;
  f.dependencies.failureProcessIo={readText(){attempts++;throw Error('must not read proc on success');},readLink(){attempts++;throw Error('must not read proc on success');}};
  const r=await f.run();assert.equal(r.exitCode,0);assert.equal(attempts,0);assert.equal(f.state().reads,2);
  assert.equal(fs.existsSync(path.join(f.out,'failure-diagnostic.json')),false);assert.equal(fs.existsSync(path.join(f.out,'cleanup-processes.json')),false);
});
test('failure-only: blank URL and absent navigation events do not imply a cause',async t=>{
  const f=fakeObservation(t,{goto:true,url:'about:blank'}),r=await f.run(),n=r.report.failureDiagnostic.navigation;
  assert.deepEqual(n.events,[]);assert.ok(n.snapshots.every(x=>x.url==='about:blank'));
  assert.equal(r.report.failureDiagnostic.cause,undefined);assert.equal(r.exitCode,2);
});
test('failure-only: the existing evaluator is passed once without a readiness wait',async t=>{
  const f=fakeObservation(t,{goto:true});let calls=0,waits=0;
  f.page.evaluate=async evaluator=>{assert.equal(evaluator,S.readPoliciesDom);calls++;return dom();};
  f.page.waitForFunction=async()=>{waits++;throw Error('no readiness wait on rejection');};
  const r=await f.run();assert.equal(r.exitCode,2);assert.equal(calls,1);assert.equal(waits,0);assert.equal(f.state().closeAttempted,true);
});
test('failure-only: a readiness failure after successful goto does not request an extra evaluation',async t=>{
  const f=fakeObservation(t,{readiness:true}),r=await f.run();assert.equal(r.exitCode,2);assert.equal(f.state().reads,1);
  assert.equal(r.report.failureDiagnostic.failedPhase,'INITIAL_READBACK');assert.equal(r.report.failureDiagnostic.readback.status,'NOT_ATTEMPTED');
});
test('failure-only: evaluation rejection preserves original error and cleanup',async t=>{
  const f=fakeObservation(t,{goto:true});f.page.evaluate=async()=>{throw Error('privileged DOM unavailable');};
  const r=await f.run();assert.equal(r.exitCode,2);assert.match(r.report.error.message,/synthetic goto failure/);
  assert.equal(r.report.failureDiagnostic.readback.status,'ERROR');assert.match(r.report.failureDiagnostic.readback.error.message,/unavailable/);assert.equal(f.state().closeAttempted,true);
});
test('failure-only: a closed page is explicitly unavailable and never evaluated',async t=>{
  const f=fakeObservation(t,{goto:true});f.page.isClosed=()=>true;const r=await f.run();
  assert.equal(r.report.failureDiagnostic.readback.status,'UNAVAILABLE');assert.equal(f.state().reads,0);assert.equal(r.exitCode,2);assert.equal(f.state().closeAttempted,true);
});
test('failure-only: page crash stays a fault despite a valid failure DOM record',async t=>{
  const f=fakeObservation(t);f.page.goto=async()=>{f.page.emit('crash');throw Error('crashed navigation');};
  const r=await f.run();assert.equal(r.exitCode,2);assert.equal(r.report.failureDiagnostic.readback.status,'CAPTURED');
  assert.ok(r.report.lifecycle.find(x=>x.kind==='page').faults.some(x=>x.event==='page-crash'));
});
test('failure-only: uncancelled late evaluation cannot modify frozen failure or delay cleanup',async t=>{
  const f=fakeObservation(t,{goto:true});let complete,calls=0;
  f.page.evaluate=()=>{calls++;return new Promise(resolve=>{complete=resolve;});};
  const started=process.hrtime.bigint(),r=await f.run(),elapsed=Number(process.hrtime.bigint()-started)/1e6;
  assert.equal(calls,1);assert.equal(r.exitCode,2);assert.equal(r.report.failureDiagnostic.readback.status,'TIMED_OUT');
  assert.equal(r.report.failureDiagnostic.readback.capMs,1000);assert.equal(f.state().closeAttempted,true);assert.ok(elapsed<5000);
  const bytes=fs.readFileSync(path.join(f.out,'result.json')),snapshot=JSON.stringify(r.report);
  complete(dom());await new Promise(resolve=>setImmediate(resolve));
  assert.equal(JSON.stringify(r.report),snapshot);assert.deepEqual(fs.readFileSync(path.join(f.out,'result.json')),bytes);
  assert.equal(r.report.initial,undefined);assert.ok(Object.isFrozen(r.report.failureDiagnostic.readback));
});
test('failure-only: early source failure reports unknown PID population',async t=>{
  const f=fakeObservation(t);f.dependencies.census=()=>({...census(),rootError:{code:'EACCES'}});
  const r=await f.run();assert.equal(r.exitCode,2);assert.equal(r.report.failureDiagnostic.failedPhase,'SOURCE_AND_POLICY');
  assert.equal(r.report.cleanupProcesses.status,'NO_OBSERVED_IDENTITIES');assert.deepEqual(r.report.cleanupProcesses.identities,[]);
});
test('failure-only: absolute cleanup deadline includes original cleanup and currentness time',async t=>{
  const f=fakeObservation(t,{goto:true});let reads=0;
  f.dependencies.current=()=>{f.tick(30000);return f.admission;};
  f.dependencies.failureProcessIo={readText(){reads++;throw Error('deadline exhausted');}};
  const r=await f.run();assert.equal(r.exitCode,2);assert.equal(reads,0);assert.equal(r.report.cleanupProcesses.status,'BUDGET_EXHAUSTED');
  assert.equal(r.report.cleanupProcesses.deadlineNs,'30000000000');
});
test('failure-only: original network refusal retains precedence over new diagnostic records',async t=>{
  const f=fakeObservation(t,{goto:true,refusal:true}),r=await f.run();assert.equal(r.exitCode,86);
  assert.equal(r.report.status,'ISOLATION_FAIL');assert.equal(r.report.failureDiagnostic.readback.status,'CAPTURED');
  assert.equal(P.outerDisposition({returncode:86,timedOut:false},r.report).stopAll,true);
});

function navigationFixture(){
  const page=new EventEmitter(),main={url:()=>page.url()};
  Object.assign(page,{url:()=> 'about:policies',mainFrame:()=>main,isClosed:()=>false});
  const browser={isConnected:()=>true};let clock=0n;
  return {page,main,browser,collector:F.navigation(page,browser,{now:()=>clock++})};
}
test('failure-only navigation: subframe payloads are never attributed to the main frame',()=>{
  const f=navigationFixture();f.page.emit('framenavigated',{url:()=>{throw Error('subframe URL must not be read');}});
  const n=f.collector.finish();assert.equal(n.subframeEvents,1);assert.deepEqual(n.events,[]);assert.deepEqual(n.faults,[]);
});
test('failure-only navigation: event cap and URL truncation are explicit',()=>{
  const f=navigationFixture();f.page.url=()=> 'x'.repeat(F.LIMITS.urlChars+1);
  for(let i=0;i<F.LIMITS.events+5;i++)f.page.emit('load');
  const n=f.collector.finish();assert.equal(n.events.length,F.LIMITS.events);assert.equal(n.mainFrameEvents,F.LIMITS.events+5);
  assert.equal(n.overflow,true);assert.equal(n.collectionComplete,false);assert.ok(n.events.every(x=>x.url.length===F.LIMITS.urlChars&&x.urlTruncated));
});
test('failure-only navigation: ownership drift and failing cached methods are bounded faults',()=>{
  const f=navigationFixture();f.page.mainFrame=()=>({});f.page.url=()=>{throw Error('cached url failed');};
  for(let i=0;i<F.LIMITS.faults+2;i++)f.page.emit('load');f.collector.snapshot('before-attempt');
  const n=f.collector.finish();assert.equal(n.faults.length,F.LIMITS.faults);assert.equal(n.overflow,true);assert.equal(n.events.length,0);
  assert.match(n.snapshots[0].urlError.message,/failed/);
});
test('failure-only navigation: collection freezes before later events and detaches only its listeners',()=>{
  const f=navigationFixture();let original=0;f.page.on('load',()=>original++);
  f.page.emit('load');const n=f.collector.finish(),bytes=JSON.stringify(n);f.page.emit('load');
  assert.equal(original,2);assert.equal(JSON.stringify(n),bytes);assert.equal(f.page.listenerCount('load'),1);assert.equal(f.collector.finish(),n);
  assert.throws(()=>n.events.push({}),TypeError);
});
test('failure-only navigation: duplicate snapshot phase is explicit rather than overwritten',()=>{
  const f=navigationFixture();f.collector.snapshot('before-attempt');f.page.url=()=> 'about:blank';f.collector.snapshot('before-attempt');
  const n=f.collector.finish();assert.equal(n.snapshots.length,1);assert.equal(n.snapshots[0].url,'about:policies');assert.equal(n.collectionComplete,false);
});
test('failure-only navigation: attach or detach failure cannot throw into original execution',()=>{
  const f=navigationFixture();f.collector.finish();f.page.on=()=>{throw Error('attach failed');};
  const c=F.navigation(f.page,f.browser);assert.equal(c.finish().faults.length,3);
  const other=navigationFixture();other.page.off=()=>{throw Error('detach failed');};assert.equal(other.collector.finish().faults.length,3);
});

test('failure-only DOM: exact payload is copied and frozen without policy admission',async()=>{
  const value={...dom(),readyState:'loading',activeRows:[],activeCount:0};let calls=0;
  const row=await F.failureDom({isClosed:()=>false,evaluate:async fn=>{assert.equal(fn,S.readPoliciesDom);calls++;return value;}},S.readPoliciesDom,{deadlineNs:10000000000n,now:()=>0n});
  assert.equal(row.status,'CAPTURED');assert.equal(calls,1);assert.deepEqual(row.dom,value);assert.throws(()=>S.admitPolicyDom(row.dom));
  value.activeRows.push(['later']);assert.deepEqual(row.dom.activeRows,[]);assert.ok(Object.isFrozen(row.dom));
});
test('failure-only DOM: original collector overflow and additional retention truncation remain explicit',async()=>{
  const value={...dom(),url:'x'.repeat(F.LIMITS.urlChars+1),activeRows:Array.from({length:17},()=>Array(5).fill('z'.repeat(1025))),activeCount:17,overflow:true};
  const r=await F.failureDom({isClosed:()=>false,evaluate:async()=>value},S.readPoliciesDom,{deadlineNs:10000000000n,now:()=>0n});
  assert.equal(r.status,'CAPTURED');assert.equal(r.collectionOverflow,true);assert.equal(r.retentionTruncated,true);
  assert.equal(r.dom.activeRows.length,16);assert.equal(r.dom.activeRows[0].length,4);assert.equal(r.dom.activeRows[0][0].length,1024);assert.equal(r.dom.activeCount,17);
});
test('failure-only DOM: malformed return is an explicit diagnostic error',async()=>{
  for(const value of [null,[],{}, {...dom(),activeCount:true},{...dom(),activeRows:[['x',null]]},{...dom(),extra:'foreign'}]){
    const r=await F.failureDom({isClosed:()=>false,evaluate:async()=>value},S.readPoliciesDom,{deadlineNs:10000000000n,now:()=>0n});
    assert.equal(r.status,'ERROR');assert.equal(r.dom,undefined);
  }
});
test('failure-only DOM: unused allocation limits the await and no retry occurs',async()=>{
  let calls=0;const started=process.hrtime.bigint();
  const r=await F.failureDom({isClosed:()=>false,evaluate:()=>{calls++;return new Promise(()=>{});}},S.readPoliciesDom,{deadlineNs:started+30000000n});
  assert.equal(r.status,'TIMED_OUT');assert.equal(calls,1);assert.ok(r.capMs<=30&&r.capMs>0);assert.equal(r.evaluationCancelled,false);
});
test('failure-only DOM: exhausted or missing absolute allocation cannot evaluate',async()=>{
  let calls=0;const page={isClosed:()=>false,evaluate:()=>{calls++;return dom();}};
  assert.equal((await F.failureDom(page,S.readPoliciesDom,{deadlineNs:0n,now:()=>0n})).status,'NOT_ATTEMPTED');
  assert.equal((await F.failureDom(page,S.readPoliciesDom,{now:()=>0n})).status,'ERROR');assert.equal(calls,0);
});
test('failure-only DOM: return after the same-clock cap is still timeout even before timer callback',async()=>{
  let clock=0n;const r=await F.failureDom({isClosed:()=>false,evaluate:async()=>{clock=1000000000n;return dom();}},S.readPoliciesDom,{deadlineNs:10000000000n,now:()=>clock});
  assert.equal(r.status,'TIMED_OUT');assert.equal(r.dom,undefined);
});
test('failure-only DOM: backwards injected clock cannot produce a captured duration',async()=>{
  let clock=10n;const r=await F.failureDom({isClosed:()=>false,evaluate:async()=>{clock=9n;return dom();}},S.readPoliciesDom,{deadlineNs:10000000000n,now:()=>clock});
  assert.equal(r.status,'ERROR');assert.equal(r.dom,undefined);
});
test('failure-only DOM: late rejection is handled without mutation or unhandled rejection',async()=>{
  let reject;const r=await F.failureDom({isClosed:()=>false,evaluate:()=>new Promise((_,r)=>{reject=r;})},S.readPoliciesDom,{deadlineNs:process.hrtime.bigint()+20000000n});
  const bytes=JSON.stringify(r);reject(Error('late rejection'));await new Promise(resolve=>setImmediate(resolve));assert.equal(JSON.stringify(r),bytes);assert.equal(r.status,'TIMED_OUT');
});
test('failure-only DOM: unchanged original evaluator retains its own row and text caps',()=>{
  const table={children:Array.from({length:17},()=>({tagName:'TR',children:Array.from({length:5},()=>({textContent:'z'.repeat(1025)}))}))};
  const context={document:{readyState:'loading',querySelectorAll:selector=>selector==='#activeContent'?[table]:selector==='#errorsContent'?[{children:[]}]:[]},location:{href:'about:policies'},getComputedStyle:()=>({display:'block',visibility:'visible'})};
  const value=JSON.parse(JSON.stringify(vm.runInNewContext('('+S.readPoliciesDom.toString()+')()',context)));
  assert.equal(value.overflow,true);assert.equal(value.activeCount,17);assert.equal(value.activeRows.length,16);assert.equal(value.activeRows[0][0].length,1024);
});

function stat(pid,ticks='10',state='S',ppid=1){const fields=Array(20).fill('0');fields[0]=state;fields[1]=String(ppid);fields[19]=ticks;return pid+' (synthetic (process)) '+fields.join(' ')+'\n';}
function procIo({before='10',after=before,state='S',afterState=state,fail={},advance=()=>{}}={}){
  const counts=new Map(),calls=[];
  return {calls,readText(pid,name){calls.push([pid,name]);advance(name);if(fail[name])throw Object.assign(Error('synthetic '+fail[name]),{code:fail[name]});
    if(name==='stat'){const n=counts.get(pid)||0;counts.set(pid,n+1);return stat(pid,n?after:before,n?afterState:state);}return '/synthetic/firefox\0-contentproc\0';},
    readLink(pid,name){calls.push([pid,name]);advance(name);if(fail[name])throw Object.assign(Error('synthetic '+fail[name]),{code:fail[name]});return name==='exe'?'/synthetic/firefox':name==='ns/net'?'net:[31]':'pid:[32]';}};
}
function snapshot(io,rows=[{pid:19,startTicks:'10'}],extra={}){return F.cleanupProcesses(rows,{now:()=>0n,deadlineNs:30000000000n,io,...extra});}
test('failure-only cleanup: same PID/start ticks and raw stat brackets are retained separately from liveness',()=>{
  const io=procIo(),r=snapshot(io),row=r.identities[0];assert.equal(r.status,'COLLECTED');assert.equal(row.identityStatus,'SAME_INCARNATION');assert.equal(row.observedState,'PRESENT');
  assert.equal(row.reads.statBefore.raw,stat(19));assert.equal(row.reads.statAfter.raw,stat(19));assert.equal(io.calls.length,6);assert.equal(r.allStopped,undefined);
});
test('failure-only cleanup: duplicate original identities are read only once',()=>{
  const io=procIo(),r=snapshot(io,[{pid:19,startTicks:'10'},{pid:19,startTicks:'10'}]);assert.equal(r.inputCount,2);assert.equal(r.uniqueIdentities,1);assert.equal(io.calls.length,6);
});
test('failure-only cleanup: different start ticks at the same PID are a different incarnation',()=>{
  const r=snapshot(procIo({before:'11'}));assert.equal(r.identities[0].identityStatus,'DIFFERENT_INCARNATION');assert.equal(r.identities[0].expected.startTicks,'10');
});
test('failure-only cleanup: absence at both stat reads is not a reaping history',()=>{
  const r=snapshot(procIo({fail:{stat:'ENOENT'}}));assert.equal(r.status,'COLLECTED');assert.equal(r.identities[0].identityStatus,'ABSENT_AT_BOTH_STAT_READS');
  assert.equal(r.identities[0].reaped,undefined);assert.equal(r.identities[0].reads.exe,undefined);
});
test('failure-only cleanup: zombie with missing executable remains an observed incarnation',()=>{
  const r=snapshot(procIo({state:'Z',fail:{exe:'ENOENT'}})),row=r.identities[0];assert.equal(r.status,'PARTIAL');assert.equal(row.identityStatus,'SAME_INCARNATION');
  assert.equal(row.observedState,'ZOMBIE');assert.equal(row.reads.exe.error.code,'ENOENT');assert.equal(row.reaped,undefined);
});
test('failure-only cleanup: exited process state is distinct from absence',()=>{
  for(const state of ['X','x']){const row=snapshot(procIo({state})).identities[0];assert.equal(row.identityStatus,'SAME_INCARNATION');assert.equal(row.observedState,'EXITED_STATE');}
});
test('failure-only cleanup: missing executable with sleeping stat cannot imply absence',()=>{
  const row=snapshot(procIo({fail:{exe:'ENOENT'}})).identities[0];assert.equal(row.identityStatus,'SAME_INCARNATION');assert.equal(row.observedState,'PRESENT');assert.equal(row.fieldStatus,'PARTIAL');
});
test('failure-only cleanup: identity changing across fields cannot form a joined identity',()=>{
  const row=snapshot(procIo({before:'10',after:'11'})).identities[0];assert.equal(row.identityStatus,'CHANGED_DURING_READ');assert.equal(row.observedState,undefined);
  assert.equal(row.statBefore.startTicks,'10');assert.equal(row.statAfter.startTicks,'11');
});
test('failure-only cleanup: absent then present and present then absent remain read races',()=>{
  for(const firstAbsent of [true,false]){let reads=0;const io=procIo(),original=io.readText;io.readText=(pid,name)=>{
    if(name==='stat'){reads++;if((reads===1)===firstAbsent)throw Object.assign(Error('synthetic vanished'),{code:'ESRCH'});}return original(pid,name);};
    const row=snapshot(io).identities[0];assert.equal(row.identityStatus,'CHANGED_DURING_READ');assert.equal(row.observedState,undefined);
  }
});
test('failure-only cleanup: stat permission error stays unreadable rather than absent',()=>{
  const r=snapshot(procIo({fail:{stat:'EACCES'}}));assert.equal(r.status,'PARTIAL');assert.equal(r.identities[0].identityStatus,'UNKNOWN');assert.equal(r.identities[0].reads.statBefore.error.code,'EACCES');
});
test('failure-only cleanup: readable stat cannot hide an auxiliary permission error',()=>{
  const r=snapshot(procIo({fail:{'ns/net':'EACCES'}}));assert.equal(r.status,'PARTIAL');assert.equal(r.identities[0].identityStatus,'SAME_INCARNATION');assert.equal(r.identities[0].reads['ns/net'].error.code,'EACCES');
});
test('failure-only cleanup: no original identities is unknown, never an empty stopped-process success',()=>{
  const io=procIo(),r=snapshot(io,[]);assert.equal(r.status,'NO_OBSERVED_IDENTITIES');assert.equal(io.calls.length,0);assert.equal(r.allStopped,undefined);
});
test('failure-only cleanup: malformed identity and stat are explicit bounded unknowns',()=>{
  const r=snapshot(procIo(),[{pid:'19',startTicks:'10'}]);assert.equal(r.status,'NO_OBSERVED_IDENTITIES');assert.equal(r.inputErrors.length,1);
  const io=procIo();io.readText=()=> 'malformed stat';const row=snapshot(io).identities[0];assert.equal(row.identityStatus,'UNKNOWN');assert.match(row.statBeforeError.message,/malformed/);
});
test('failure-only cleanup: absolute exhausted budget performs no proc reads',()=>{
  const io=procIo(),r=snapshot(io,undefined,{now:()=>30000000000n});assert.equal(io.calls.length,0);assert.equal(r.status,'BUDGET_EXHAUSTED');assert.equal(r.identities.length,0);
});
test('failure-only cleanup: deadline consumed during a read stops remaining reads and discloses partial data',()=>{
  let clock=0n;const io=procIo({advance:()=>{clock+=15000000000n;}}),r=snapshot(io,undefined,{now:()=>clock});
  assert.equal(r.status,'BUDGET_EXHAUSTED');assert.equal(io.calls.length,2);assert.equal(r.identities[0].identityStatus,'UNKNOWN');
  assert.equal(r.identities[0].reads.cmdline.afterDeadline,true);assert.equal(r.identities[0].reads.statAfter.status,'BUDGET_EXHAUSTED');
});
test('failure-only cleanup: final snapshot completion rechecks the same absolute cutoff',()=>{
  const io=procIo(),read=io.readText;let statReads=0,finishing=false,finalClockReads=0;
  io.readText=(pid,name)=>{const value=read(pid,name);if(name==='stat'&&++statReads===2)finishing=true;return value;};
  const now=()=>finishing?(++finalClockReads===1?29999999999n:30000000000n):0n;
  const r=snapshot(io,undefined,{now});assert.equal(r.endedNs,'30000000000');assert.equal(r.status,'BUDGET_EXHAUSTED');assert.equal(r.budgetExpired,true);
});
test('failure-only cleanup: bounded retained fields disclose oversized values',()=>{
  const io=procIo();io.readLink=()=> 'x'.repeat(F.LIMITS.exeBytes+1);const r=snapshot(io);
  assert.equal(r.overflow,true);assert.equal(r.status,'PARTIAL');assert.equal(r.identities[0].reads.exe.raw.length,F.LIMITS.exeBytes);assert.equal(r.identities[0].reads.exe.truncated,true);
});
test('failure-only cleanup: identity population and input-error bounds remain explicit',()=>{
  const rows=Array.from({length:F.LIMITS.identities+1},(_,i)=>({pid:100+i,startTicks:'10'})),r=snapshot(procIo(),rows);
  assert.equal(r.overflow,true);assert.equal(r.identities.length,F.LIMITS.identities);assert.equal(r.uniqueIdentities,F.LIMITS.identities+1);assert.equal(r.status,'PARTIAL');
  const bad=snapshot(procIo(),Array(F.LIMITS.inputIdentities+1).fill(null));assert.equal(bad.overflow,true);assert.equal(bad.inputErrors.length,F.LIMITS.faults);
});
test('failure-only cleanup: state changes within the same incarnation stay bracketed observations',()=>{
  const row=snapshot(procIo({state:'R',afterState:'S'})).identities[0];assert.equal(row.identityStatus,'SAME_INCARNATION');assert.equal(row.stateChanged,true);assert.equal(row.statBefore.state,'R');
});
test('failure-only parent: old liveness expression and calls preserve strict refusal and success behavior',()=>{
  const line=P.supervise.toString().split('\n').find(x=>x.includes('report.processes?.observed?.every'));
  assert.ok(line.includes('report.processes?.observed?.every(row=>!S.sameLive(row))&&report.finalProcesses?.observed?.every(row=>!S.sameLive(row))'));
  const run=new Function('report','S','need','F',line);let calls=0;
  const rows={processes:{observed:[{pid:1}]},finalProcesses:{observed:[{pid:1}]}};
  run(rows,{sameLive:()=>{calls++;return false;}},S.need,F);assert.equal(calls,2);
  calls=0;assert.throws(()=>run(rows,{sameLive:()=>{calls++;return true;}},S.need,F),/remains live/);assert.equal(calls,1);
  assert.throws(()=>run({processes:rows.processes},{sameLive:()=>false},S.need,F),/missing required success-path process census/);
});
test('failure-only source: unchanged original scientific, custody, readback and hard-bound functions',()=>{
  const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
  const expected={resultCode:'988d4728f1a1d6e56b5436b00e26fe739b0e028f5ffed3123f755b538425d76e',readPoliciesDom:'44ef285475fed79f1b8b4618ef1e572344668cec092be56750a9a1f584e01398',
    sameLive:'65769580b050fe7fcd78baf726bdf5c33a7577d7c60182fbff436c90c9ebd25f',ownedProcesses:'54673184274a9f70b2c505cd249ffbe2eb4e991f88c6f45c007502be18fd6f8a',validateIsolation:'6a6f010882952ee6154f88a6bd83ec2c1e7d7e0453b124be1e62fe5bee174c09',
    readback:'d11c894143daf1872917c10ccc6eee362e4e2d1467788de0eca6ecd1aeaaca2c',runChild:'1bbf006a59d7db1038f9e24d0e986499d294fe9bba198f7d2a091d37766a1859',outerDisposition:'0cac02ef77461e61a24e2c7f55f086d3b080e1e92e2775b5b0d70dcf244ed7da',
    preflight:'665b818c5fb635b7ee4d30809e7016180ff8605134f22cf42c09df2360d526ca',environment:'a71ec5b3f848bb706c5075ad0668d9b5b445f80f31dac67d1e8d76766ef2a418'};
  for(const [name,digest] of Object.entries(expected))assert.equal(sha((S[name]||P[name]).toString()),digest,name);
  assert.equal(sha(JSON.stringify(S.BUDGET)),'e6e5342cdec74eaa2373d3d96de170ed15fab588dc1a979e131a78c49468f1ea');
});
test('failure-only source: both new leaves are required and any changed leaf is refused',t=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'firefox-failure-closure-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const names=['tools/qa/hosted-native/firefox_failure_diagnostic.cjs','tools/qa/hosted-native/firefox_failure_controls.cjs'];
  for(const name of names)assert.ok(S.FILES.includes(name));
  for(const name of [...S.FILES,'tools/qa/hosted-native/firefox-policy-pins.json']){
    const target=path.join(root,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(S.ROOT,name),target);
  }
  const source=require(path.join(root,'tools/qa/hosted-native/firefox_policy_source.cjs')),digest=S.record(path.join(root,'tools/qa/hosted-native/firefox-policy-pins.json')).sha256;
  source.packet(digest);
  for(const name of names){const target=path.join(root,name),original=fs.readFileSync(target);fs.appendFileSync(target,'\n// synthetic mutation\n');
    assert.throws(()=>source.packet(digest),error=>error.message==='source drift: '+name);fs.writeFileSync(target,original);
  }
});
