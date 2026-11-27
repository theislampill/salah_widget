'use strict';
// Separate diagnostic entry. No campaign selects it until independent review.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const S=require('./firefox_policy_source.cjs');
const F=require('./firefox_failure_diagnostic.cjs');
const {need}=S;
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const errorRecord=error=>({name:String(error?.name||'Error'),message:String(error?.message??error).slice(0,8192)});
async function bounded(promise,ms,label){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(label+' deadline exceeded')),ms);})]);}finally{clearTimeout(timer);}}
function parse(argv){
  const out={},allowed=new Set(['task','out','isolation','pins-sha256']);
  need(argv.length===8,'four exact arguments are required');
  for(let i=0;i<argv.length;i+=2){const key=argv[i].slice(2);need(argv[i].startsWith('--')&&allowed.has(key)&&!(key in out)&&typeof argv[i+1]==='string'&&argv[i+1]&&!argv[i+1].startsWith('--'),'unknown, repeated or missing argument');out[key]=argv[i+1];}
  for(const key of ['task','out','isolation'])need(path.isAbsolute(out[key])&&path.normalize(out[key])===out[key],'absolute normalized '+key+' required');
  need(out.out===path.join(out.task,'capture/firefox-policy'),'one task-owned Firefox policy output path required');
  need(out.isolation.startsWith(path.join(out.task,'capture/isolation')+path.sep)&&path.basename(out.isolation)==='receipt.json','current task isolation receipt required');
  need(/^[0-9a-f]{64}$/.test(out['pins-sha256']),'reviewed source manifest digest required');return out;
}
function environment(options,acquired){
  need(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT===options.isolation,'explicit current isolation environment binding required');
  need(process.env.NODE_PATH===acquired.runtime.modules&&process.env.PLAYWRIGHT_BROWSERS_PATH===path.join(options.task,'node-browsers'),'acquired browser dependency environment differs');
  need(process.execArgv.length===0&&!process.env.NODE_OPTIONS&&!process.env.LD_PRELOAD&&!process.env.LD_LIBRARY_PATH,'unreviewed executable injection environment');
  need(!Object.keys(process.env).some(name=>/^MOZ_DISABLE_.*SANDBOX$/.test(name)),'Firefox sandbox disabling environment is forbidden');
}
function preflight(options){
  // An absent/mismatched current boundary is exit86 before output, policy or browser creation.
  let isolation;try{isolation=S.readIsolation(options.isolation);need(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT===options.isolation,'current isolation environment differs');}
  catch(error){error.isolation=true;throw error;}
  const source=S.packet(options['pins-sha256']),acquired=S.admitAcquisition(options.task,process.execPath);environment(options,acquired);
  return {isolation,source,acquired};
}
function retain(report,out,name,value){
  try{return S.write(path.join(out,name),value);}catch(error){report.retentionErrors.push({file:name,...errorRecord(error)});return null;}
}
function bindBrowser(browser,report,handles){
  handles.browser=browser;handles.browserWatch=S.watch(browser,'browser',()=>browser.isConnected());report.lifecycle.push(handles.browserWatch.state);
  const newContext=browser.newContext.bind(browser);
  browser.newContext=async(...args)=>{
    const context=await newContext(...args);
    need(!handles.context,'unexpected additional diagnostic context');handles.context=context;let open=true;
    context.on('close',()=>{open=false;});handles.contextWatch=S.watch(context,'context',()=>open);report.lifecycle.push(handles.contextWatch.state);
    const pages=new Set();context.on('page',page=>{
      if(pages.has(page))return;pages.add(page);
      const watch=S.watch(page,'page',()=>!page.isClosed());report.lifecycle.push(watch.state);
      if(handles.page)watch.fault('unexpected-additional-page');else {handles.page=page;handles.pageWatch=watch;}
    });return context;
  };
}
async function readback(page,report,out,label,now=()=>process.hrtime.bigint()){
  let waitError;
  try{await page.waitForFunction(()=>{
    const active=document.querySelector('#activeContent'),errors=document.querySelector('#errorsContent');
    return document.readyState==='complete'&&active&&errors&&(active.children.length>0||errors.children.length>0||
      [...document.querySelectorAll('.inactive-service-message,.no-specified-policies-message')].some(x=>x.getClientRects().length>0&&getComputedStyle(x).display!=='none'));
  },undefined,{timeout:9000});}catch(error){waitError=errorRecord(error);}
  const dom=await bounded(page.evaluate(S.readPoliciesDom),1000,'effective policy evaluation'),row={hostNs:now().toString(),dom};
  if(waitError)row.waitError=waitError;report[label]=row;retain(report,out,label+'-policy.json',row);
  need(!waitError,'effective policy DOM readiness deadline was not satisfied');S.admitPolicyDom(row.dom);return row;
}
function requestCleanup(handles){
  // Mark each acquired owner only when cleanup is actually requested. A close
  // already observed (including a queued API-visible close) stays a late fault.
  for(const name of ['pageWatch','contextWatch','browserWatch'])if(handles[name])handles[name].requestCleanup();
}
async function observe(options,admission,dependencies={}){
  const report={protocol:'firefox-policy-observation/1',status:'INCOMPLETE',phase:'STARTED',engine:'firefox',scope:'managed application-update policy and bounded strict-isolation diagnostic',
    nativeProductAcceptance:'NOT_EVALUATED',originalFailedObservation:'UNCHANGED',refinedCapture:'NOT_OBSERVED',historicalFirstStartup:'NOT_ESTABLISHED',
    budget:S.BUDGET,source:admission.source,acquired:admission.acquired,isolation:admission.isolation,processCensuses:{},lifecycle:[],errors:[],retentionErrors:[],cleanup:{complete:false,trackedProcessesStopped:false}};
  const handles={},acquired=admission.acquired,iso=dependencies.isolationModule||require('../r0033_isolation.cjs');let session;
  // Tests may supply bounded doubles. Production always uses real process census,
  // the unchanged original launcher and the acquired Playwright package.
  const census=dependencies.census||(()=>S.liveInstallation(acquired)),sleep=dependencies.sleep||delay;
  const now=dependencies.now||(()=>process.hrtime.bigint());
  let currentPhase='SOURCE_AND_POLICY',failedPhase=null,cleanupDeadlineNs,navigationEvidence;
  let failureReadback={status:'NOT_ATTEMPTED',reason:'original navigation did not reject before initial readback'};
  const diagnosticFaults=[];
  const diagnosticFault=(phase,error)=>{if(diagnosticFaults.length<F.LIMITS.faults)diagnosticFaults.push({phase,...F.errorRecord(error)});};
  try{
    report.processCensuses.before=census();retain(report,options.out,'process-census-before.json',report.processCensuses.before);
    report.policy=S.preparePolicy(acquired,S.censusRows(report.processCensuses.before));retain(report,options.out,'policy-preparation.json',report.policy);
    const guard=dependencies.guard||require('../v1_net_guard.cjs');guard.install();report.nodeGuard=guard.state;
    const PW=dependencies.playwright||require(acquired.runtime.playwright);
    need(PW.firefox.executablePath()===acquired.executable,'Playwright executable differs from acquired Firefox');
    const launch={firefox:{launch:async settings=>{
      need(settings.headless===true&&S.equal(settings.args,[])&&S.equal(settings.firefoxUserPrefs,iso.FIREFOX_PREFS)&&
        /^http:\/\/127\.0\.0\.1:\d+$/.test(settings.proxy?.server)&&settings.proxy.bypass==='127.0.0.1,localhost','original Firefox isolation launch settings differ');
      report.launch={options:{...settings,timeout:45000},startedNs:now().toString(),executable:acquired.binary};
      retain(report,options.out,'launch-request.json',report.launch);
      const browser=await PW.firefox.launch({...settings,timeout:45000});bindBrowser(browser,report,handles);return browser;
    }}};
    currentPhase='LAUNCH';handles.launchAttempted=true;session=await bounded(iso.launch(launch,'firefox'),45000,'Firefox launch');handles.session=session;
    report.ledger=session.ledger;report.nodeGuard=guard.state;
    currentPhase='STARTED_CENSUS';report.processCensuses.started=census();retain(report,options.out,'process-census-started.json',report.processCensuses.started);
    report.processes=S.ownedProcesses(report.processCensuses.started,admission.isolation.host,process.pid);report.browserVersion=session.browser.version();
    retain(report,options.out,'browser-start.json',{launch:report.launch,processes:report.processes,browserVersion:report.browserVersion});
    currentPhase='CONTEXT';const context=await bounded(session.context({viewport:{width:800,height:600},timezoneId:'UTC'},{}),10000,'guarded policy context');
    currentPhase='PAGE';const page=await bounded(context.newPage(),10000,'policy page');need(handles.page===page,'policy page lifecycle was not bound before use');
    try{handles.navigationDiagnostic=F.navigation(page,session.browser,{now});handles.navigationDiagnostic.snapshot('before-attempt');}
    catch(error){diagnosticFault('navigation-listeners',error);}
    currentPhase='NAVIGATION';
    await page.goto('about:policies',{waitUntil:'load',timeout:20000});
    currentPhase='INITIAL_READBACK';
    await bounded(readback(page,report,options.out,'initial',now),10000,'initial policy readback');
    currentPhase='DWELL';
    report.dwell={intendedMs:S.BUDGET.dwellMs,startedNs:now().toString()};
    await sleep(S.BUDGET.dwellMs);report.dwell.endedNs=now().toString();
    currentPhase='FINAL_READBACK';await bounded(readback(page,report,options.out,'final',now),10000,'final policy readback');
    currentPhase='FINAL_CENSUS';
    report.processCensuses.final=census();retain(report,options.out,'process-census-final.json',report.processCensuses.final);
    report.finalProcesses=S.ownedProcesses(report.processCensuses.final,admission.isolation.host,process.pid);
    need(report.finalProcesses.root.pid===report.processes.root.pid&&report.finalProcesses.root.startTicks===report.processes.root.startTicks,'Firefox process changed between readbacks');
  }catch(error){report.error=errorRecord(error);if(error.isolation)report.isolationError=errorRecord(error);
    failedPhase=currentPhase;
    if(currentPhase==='NAVIGATION'){
      try{handles.navigationDiagnostic?.snapshot('on-rejection');}catch(fault){diagnosticFault('rejection-snapshot',fault);}
      try{failureReadback=await F.failureDom(handles.page,S.readPoliciesDom,
        {now,deadlineNs:now()+BigInt(S.BUDGET.phases.initialReadback)*1000000000n});}
      catch(fault){failureReadback={status:'ERROR',attempted:false,error:F.errorRecord(fault)};}
    }
  }
  finally{
    cleanupDeadlineNs=now()+BigInt(S.BUDGET.phases.cleanup)*1000000000n;
    try{handles.navigationDiagnostic?.snapshot('before-cleanup');navigationEvidence=handles.navigationDiagnostic?.finish();}
    catch(error){diagnosticFault('navigation-finalization',error);}
    requestCleanup(handles);
    if(session){
      try{await bounded(session.close(),30000,'Firefox session/proxy cleanup');report.cleanup.complete=true;}
      catch(error){report.errors.push({phase:'cleanup',...errorRecord(error)});}
      try{await bounded(session.settle(),1000,'final request settlement');report.network=session.verdict();report.ledger=session.ledger;}
      catch(error){report.errors.push({phase:'network-verdict',...errorRecord(error)});}
    }else if(handles.launchAttempted){
      if(handles.browser)try{await bounded(handles.browser.close(),10000,'partial Firefox cleanup');}catch(error){report.errors.push({phase:'partial-cleanup',...errorRecord(error)});}
      report.errors.push({phase:'proxy-custody',message:'Original launcher did not return its proxy/session ledger; cleanup remains unconfirmed.'});
    }else report.cleanup.complete=true;
    report.cleanup.browserLaunchAttempted=handles.launchAttempted===true;
    if(report.nodeGuard?.refused?.length)report.isolationError={message:'The original Node guard retained a refused operation.'};
    try{
      const rows=[...(report.processes?.observed||[]),...(report.finalProcesses?.observed||[])];
      report.cleanup.trackedProcessesStopped=!handles.launchAttempted||(rows.length>0&&rows.every(row=>(dependencies.sameLive||S.sameLive)(row)===false));
      if(!report.cleanup.trackedProcessesStopped)report.errors.push({phase:'process-cleanup',message:'Tracked Firefox processes did not all cease, or no process identity was obtained.'});
    }catch(error){report.errors.push({phase:'process-cleanup',...errorRecord(error)});}
    try{
      const current=dependencies.current||preflight,currentAdmission=current(options);
      need(S.equal(currentAdmission.source,admission.source)&&S.equal(currentAdmission.acquired,acquired)&&
        S.equal(currentAdmission.isolation.receipt,admission.isolation.receipt),'source, acquired package/binary or namespace changed');
      S.admitPolicy(acquired,report.policy);report.currentVerified=true;
    }catch(error){if(error.isolation)report.isolationError=errorRecord(error);report.errors.push({phase:'currentness',...errorRecord(error)});}
    await new Promise(resolve=>setImmediate(resolve));
    retain(report,options.out,'network.json',{ledger:report.ledger??null,verdict:report.network??null,nodeGuard:report.nodeGuard??null});
    report.phase='FINALIZED';const code=S.resultCode(report);report.status=code===0?'OBSERVED_FIREFOX_POLICY':code===86?'ISOLATION_FAIL':'INCOMPLETE';
    if(code!==0){
      // The original result has already failed. These separate, immutable fields
      // cannot supply a success readback, dwell, final census or new verdict.
      report.failureDiagnostic=F.frozen({protocol:'firefox-failure-diagnostic/1',originalOutcome:'UNCHANGED',
        failedPhase:failedPhase||'FINALIZATION',navigation:navigationEvidence||{status:'NOT_STARTED'},
        readback:failureReadback,faults:diagnosticFaults});
      try{report.cleanupProcesses=F.cleanupProcesses([...(report.processes?.observed||[]),...(report.finalProcesses?.observed||[])],
        {now,deadlineNs:cleanupDeadlineNs,io:dependencies.failureProcessIo||{}});}
      catch(error){report.cleanupProcesses=F.frozen({protocol:'firefox-cleanup-process-diagnostic/1',status:'ERROR',error:F.errorRecord(error)});}
      retain(report,options.out,'failure-diagnostic.json',report.failureDiagnostic);
      retain(report,options.out,'cleanup-processes.json',report.cleanupProcesses);
    }
    retain(report,options.out,'result.json',report);
  }
  return {report,exitCode:S.resultCode(report)};
}
function outerDisposition(processRecord,report){
  if(processRecord?.returncode===86||report?.status==='ISOLATION_FAIL'||report?.network?.ok===false)return {status:'ISOLATION_FAIL',exitCode:86,stopAll:true};
  if(!Number.isInteger(processRecord?.returncode)||processRecord.returncode!==0||processRecord.timedOut!==false||processRecord.signal||
    report?.status!=='OBSERVED_FIREFOX_POLICY'||S.resultCode(report)!==0)return {status:'INCOMPLETE',exitCode:2,stopAll:false};
  return {status:'OBSERVED_FIREFOX_POLICY',exitCode:0,stopAll:false};
}
async function runChild(argv,out,seconds=S.BUDGET.childSeconds){
  const stdout=fs.openSync(path.join(out,'child.stdout'),'wx',0o600),stderr=fs.openSync(path.join(out,'child.stderr'),'wx',0o600);
  const started=process.hrtime.bigint();let child,timer,killTimer,forceTimer,timedOut=false,spawnError=null,killedGroup=false;
  const group=signal=>{if(child?.pid)try{process.kill(-child.pid,signal);killedGroup=true;}catch(error){if(error.code!=='ESRCH')throw error;}};
  try{
    child=spawn(argv[0],argv.slice(1),{cwd:__dirname,env:process.env,detached:true,stdio:['ignore',stdout,stderr]});
    const outcome=await new Promise(resolve=>{
      const finish=(code,signal)=>resolve({returncode:code,signal});
      child.once('error',error=>{spawnError=errorRecord(error);finish(null,null);});child.once('close',finish);
      timer=setTimeout(()=>{timedOut=true;group('SIGTERM');killTimer=setTimeout(()=>{group('SIGKILL');forceTimer=setTimeout(()=>finish(null,'UNCONFIRMED_AFTER_KILL'),2000);},2000);},seconds*1000);
    });
    if(timedOut)group('SIGKILL');
    return {protocol:'firefox-policy-child-process/1',argv,cwd:__dirname,pid:child.pid??null,timeoutSeconds:seconds,...outcome,timedOut,
      elapsedSeconds:Number(process.hrtime.bigint()-started)/1e9,groupTerminationRequested:killedGroup,error:spawnError,
      stdout:S.record(path.join(out,'child.stdout')),stderr:S.record(path.join(out,'child.stderr'))};
  }finally{clearTimeout(timer);clearTimeout(killTimer);clearTimeout(forceTimer);fs.closeSync(stdout);fs.closeSync(stderr);}
}
async function supervise(options,admission){
  S.safe(path.dirname(options.out),'directory');need(!fs.existsSync(options.out),'private diagnostic output must be fresh');fs.mkdirSync(options.out,{mode:0o700});
  S.write(path.join(options.out,'entry-input.json'),{protocol:'firefox-policy-entry-input/1',options,admission,budget:S.BUDGET,scope:'one future native diagnostic; no product acceptance'});
  const argv=[admission.acquired.runtime.node,__filename,'--internal-child',...Object.entries(options).flatMap(([k,v])=>['--'+k,v])];
  const actual=await runChild(argv,options.out);S.write(path.join(options.out,'process.json'),actual);
  let report=null,intakeError=null;
  try{
    report=S.read(path.join(options.out,'result.json'));
    const current=preflight(options);need(S.equal(current.source,admission.source)&&S.equal(current.acquired,admission.acquired)&&
      S.equal(report.acquired,current.acquired)&&S.equal(report.source,current.source)&&S.equal(report.isolation.receipt,current.isolation.receipt),'final source/acquisition/isolation evidence differs');
    S.admitPolicy(current.acquired,report.policy);
    const network=S.read(path.join(options.out,'network.json'));
    const original=require('../r0033_isolation.cjs').verdict(network.ledger,network.nodeGuard.refused);
    need(S.equal(original,network.verdict)&&S.equal(original,report.network)&&S.equal(network.ledger,report.ledger),'original strict network verdict differs');
    need(report.processes?.observed?.every(row=>!S.sameLive(row))&&report.finalProcesses?.observed?.every(row=>!S.sameLive(row)),F.cleanupPredicateMessage(report));
  }catch(error){intakeError=errorRecord(error);if(error.isolation)report={...report,status:'ISOLATION_FAIL'};}
  const disposition=outerDisposition(actual,report);if(intakeError&&disposition.exitCode!==86)Object.assign(disposition,{status:'INCOMPLETE',exitCode:2,stopAll:false});
  const result={protocol:'firefox-policy-entry/1',...disposition,process:S.record(path.join(options.out,'process.json')),report:fs.existsSync(path.join(options.out,'result.json'))?S.record(path.join(options.out,'result.json')):null,
    intakeError,source:admission.source,nativeProductAcceptance:'NOT_EVALUATED',originalFailedObservation:'UNCHANGED'};
  S.write(path.join(options.out,'entry-result.json'),result);return result;
}
async function main(argv){
  const child=argv[0]==='--internal-child',options=parse(child?argv.slice(1):argv),admission=preflight(options);
  if(child){S.safe(options.out,'directory');const result=await observe(options,admission);return result.exitCode;}
  return (await supervise(options,admission)).exitCode;
}
module.exports={parse,preflight,environment,bounded,readback,bindBrowser,observe,outerDisposition,runChild,supervise,main};
if(require.main===module)main(process.argv.slice(2)).then(code=>process.exit(code)).catch(error=>{
  const status=error.isolation?'ISOLATION_FAIL':'INCOMPLETE';process.stderr.write(JSON.stringify({protocol:'firefox-policy-entry-error/1',status,error:errorRecord(error)})+'\n');process.exit(error.isolation?86:2);
});
