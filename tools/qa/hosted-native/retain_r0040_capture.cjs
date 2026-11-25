'use strict';
// Capture-specific host instrumentation. The pinned original bytes, arguments,
// report and CDP stream remain unchanged. This is not an option-oracle wrapper.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const Module=require('node:module'),{execFileSync}=require('node:child_process');
const {isDeepStrictEqual}=require('node:util');
const generic=path.join(__dirname,'retain_r0040.cjs');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
need(sha(fs.readFileSync(generic))==='5e4418ac9d5cda410404462d2f8051959eac53e59d4e7304ac68dc33e39d1328','retention guard source digest mismatch');
const {verifyIsolation,allowedContinuation}=require(generic);
const MANIFEST_SHA256='267f2fd8ac130c049430ffdaa0fd50b72457c60084b49360346748cc940f6b73';
const RECIPE_SHA256='9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730';
const DRIVER_SHA256='19a766ccacf0ac784f46961a5cd0079390f10a34d14825ef5ac7b28adbd33e26';
const errorData=error=>({name:error?.name,message:String(error?.message??error),stack:error?.stack});

class CaptureJournal {
  constructor(directory){this.directory=path.resolve(directory);this.sequence=0;
    fs.mkdirSync(this.directory,{mode:0o700});this.fd=fs.openSync(path.join(this.directory,'events.jsonl'),'wx',0o600);
    this.record('instrumentation',{protocol:'r0040-capture-retention/1',recipe:'R0040 capture',
      interpretation:'Supplemental final admission only; original capture.json, failures and partial PNGs remain unchanged.',
      overhead:'Host request/error/close serialization and fsync affect instrumented timing. No CDP frame listener, per-frame copy or per-frame fsync is added. PNG hashing occurs after the original process finishes.',
      nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING'});}
  record(event,value={}){const row={sequence:++this.sequence,atUtc:new Date().toISOString(),monotonicNs:process.hrtime.bigint().toString(),event,...value};
    fs.writeFileSync(this.fd,JSON.stringify(row)+'\n');fs.fsyncSync(this.fd);return row;}
  preserve(event,value){try{return this.record(event,value);}catch(error){this.retentionError||=error;}}
  publish(name,value){const pending=path.join(this.directory,name+'.pending'),target=path.join(this.directory,name);
    const fd=fs.openSync(pending,'wx',0o600);
    try{fs.writeFileSync(fd,JSON.stringify(value,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
    // Final publication is the last operation. Keep the pending hard link as
    // evidence; a failed write/fsync/close cannot publish an admitted receipt.
    fs.linkSync(pending,target);}
  close(){if(this.fd!==null){const fd=this.fd;this.fd=null;fs.closeSync(fd);}}
}

function readRegular(root,name){need(!path.isAbsolute(name)&&!name.split('/').includes('..'),'unsafe source path');
  let file=path.resolve(root);need(!fs.lstatSync(file).isSymbolicLink(),'symlink source root');
  for(const part of name.split('/')){file=path.join(file,part);need(!fs.lstatSync(file).isSymbolicLink(),'symlink source: '+name);}
  need(fs.statSync(file).isFile(),'regular source required: '+name);return fs.readFileSync(file);}
function verifySourceRows(root,rows){const result={};
  for(const [name,row]of Object.entries(rows)){const bytes=readRegular(root,name),actual={bytes:bytes.length,sha256:sha(bytes)};
    if(row.gitBlob)actual.gitBlob=crypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');
    need(Object.keys(actual).every(k=>actual[k]===row[k]),'source digest or size mismatch: '+name);result[name]=actual;}
  return result;}
function verifyDriver(driver){const source=fs.readFileSync(driver);need(sha(source)===DRIVER_SHA256,'original capture driver digest mismatch');return source;}
function git(root,...args){return execFileSync('git',['-C',root,...args],{encoding:'utf8',timeout:30000,
  env:{...process.env,GIT_NO_LAZY_FETCH:'1',GIT_TERMINAL_PROMPT:'0'}}).trim();}
function within(child,parent){const rel=path.relative(parent,child);return rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel));}
function verifyOutputs(out,evidence,inputs){
  function destination(name){const target=path.resolve(name);let exists=false;
    try{fs.lstatSync(target);exists=true;}catch(error){if(error.code!=='ENOENT')throw error;}
    need(!exists,'fresh capture and evidence outputs required');
    let parent=path.dirname(target);const suffix=[path.basename(target)];
    while(!fs.existsSync(parent)){suffix.unshift(path.basename(parent));const next=path.dirname(parent);need(next!==parent,'existing output ancestor required');parent=next;}
    need(fs.statSync(parent).isDirectory(),'output ancestor must be a directory');
    return path.join(fs.realpathSync(parent),...suffix);}
  const output=destination(out),privateEvidence=destination(evidence);
  need(!within(output,privateEvidence)&&!within(privateEvidence,output),'capture and evidence must be separate');
  for(const input of inputs){const actual=fs.realpathSync(input);
    need(!within(output,actual)&&!within(privateEvidence,actual),'capture and evidence must be outside source inputs');}
}
function verifySources(options,args){
  need(args.length===8,'eight unchanged original capture arguments required');
  const [pw,historical,main,out,engine,block,condition,model]=args.map(String);
  need([engine,block,condition,model].join('/')==='chromium/bday/moderate/M1','only the documented capture cell is admitted');
  need(process.env.R0040_DISPERSION==='common'&&!process.env.R0040_OPTIONS,'common dispersion and cleared R0040_OPTIONS required');
  need(path.isAbsolute(pw),'explicit absolute Playwright module path required');
  const driver=path.resolve(options.driver),research=path.resolve(path.dirname(driver),'../../..');
  verifyDriver(driver);const manifestBytes=fs.readFileSync(options.manifest);
  need(sha(manifestBytes)===MANIFEST_SHA256,'capture manifest digest mismatch');const manifest=JSON.parse(manifestBytes);
  need(manifest.protocol==='r0040-native-capture-preflight/1','capture manifest protocol mismatch');
  const processBytes=fs.readFileSync(options.preparationProcess),prepProcess=JSON.parse(processBytes);
  const preparedBytes=fs.readFileSync(options.prepared),prepared=JSON.parse(preparedBytes);
  need(prepProcess.protocol==='r0040-capture-preparation-process/1'&&prepProcess.status==='PREPARED'&&prepProcess.returncode===0&&
    prepProcess.timedOut===false&&prepProcess.nativeStatus==='NOT_RUN'&&prepProcess.outputPreexisted===false,'successful preparation process receipt required');
  need(prepProcess.manifestSha256===MANIFEST_SHA256&&prepProcess.recipeSourceSha256===RECIPE_SHA256&&
    prepProcess.wrapperSha256===sha(fs.readFileSync(path.join(__dirname,'r0040_capture_prepare.py'))),'preparation source custody mismatch');
  need(prepProcess.preparedReceipt?.path===path.resolve(options.prepared)&&prepProcess.preparedReceipt.sha256===sha(preparedBytes),'original preparation receipt custody mismatch');
  need(prepProcess.inputs?.research===research&&prepProcess.inputs.main===path.resolve(main)&&
    path.join(prepProcess.inputs.out,'historical')===path.resolve(historical)&&
    path.join(prepProcess.inputs.out,'receipts/prepared.json')===path.resolve(options.prepared),'preparation input paths mismatch');
  need(prepared.protocol==='r0040-capture-preparation/1'&&prepared.status==='PREPARED'&&prepared.nativeStatus==='NOT_RUN'&&
    prepared.manifestSha256===MANIFEST_SHA256&&prepared.mainHead===manifest.main.head&&prepared.historicalPath==='historical'&&
    isDeepStrictEqual(prepared.pins,manifest.pins)&&isDeepStrictEqual(prepared.stages,manifest.stages),'complete original preparation receipt required');
  need(prepProcess.completedStages===2&&isDeepStrictEqual(prepProcess.finalHistoricalFiles,manifest.stages.at(-1).files)&&
    isDeepStrictEqual(prepProcess.pins,manifest.pins),'complete six-file preparation stages required');
  need(git(research,'rev-parse','HEAD')===manifest.researchCommit,'immutable research head mismatch');
  need(git(main,'rev-parse','HEAD')===manifest.main.head&&!git(main,'status','--porcelain=v1','--untracked-files=all'),'genuine clean main required');
  const researchSources=verifySourceRows(research,manifest.researchInputs),historicalSources=verifySourceRows(historical,manifest.stages.at(-1).files);
  const actualFiles=[];function walk(root,relative=''){for(const e of fs.readdirSync(path.join(root,relative),{withFileTypes:true})){
    const name=path.posix.join(relative,e.name);if(e.isDirectory())walk(root,name);else actualFiles.push(name);}}
  walk(historical);need(isDeepStrictEqual(actualFiles.sort(),Object.keys(manifest.stages.at(-1).files).sort()),'exact six-file historical population required');
  const inventoryBytes=readRegular(main,'GENERATED.json');need(sha(inventoryBytes)===manifest.main.generatedInventorySha256,'main generated inventory mismatch');
  const inventory=JSON.parse(inventoryBytes);need(inventory.fileCount===manifest.main.generatedMembers&&Object.keys(inventory.files).length===inventory.fileCount,'main generated population mismatch');
  verifySourceRows(main,inventory.files);const mainSources=verifySourceRows(main,manifest.main.runtimeFiles);
  need(mainSources['index.html'].sha256===manifest.pins.productSha,'main product source pin mismatch');
  verifyOutputs(out,options.evidence,[research,historical,main]);
  return {manifest,research,sources:{research:researchSources,historical:historicalSources,main:mainSources},
    custody:{manifestSha256:MANIFEST_SHA256,recipeSourceSha256:RECIPE_SHA256,
      preparationProcess:{path:path.resolve(options.preparationProcess),sha256:sha(processBytes)},prepared:{path:path.resolve(options.prepared),sha256:sha(preparedBytes)},
      preparationOuterExit:'Coordinator must independently require the preparation entry actual exit zero.'}};
}

class CaptureRetention {
  constructor(directory,{out,expected,pins}){this.journal=new CaptureJournal(directory);this.out=path.resolve(out);this.expected=expected;this.pins=pins;
    this.requests=[];this.requestMap=new WeakMap();this.pages=[];this.pageMap=new WeakMap();this.rawPages=new WeakMap();
    this.errors=[];this.driverErrors=[];this.closes={context:{},browser:{},server:{}};this.scene=null;this.finalized=false;}
  record(event,value={}){return this.journal.preserve(event,value);}
  failure(event,error,fields={}){const value={...fields,error:errorData(error)};this.errors.push({event,...value});this.record(event,value);}
  requestRow(raw,source){let row=this.requestMap.get(raw);
    if(!row){row={id:this.requests.length+1,url:raw.url(),method:raw.method?.(),resourceType:raw.resourceType?.(),observedBy:[],actions:[]};
      this.requests.push(row);this.requestMap.set(raw,row);this.record('request-observed',{request:row});}
    if(!row.observedBy.includes(source))row.observedBy.push(source);return row;}
  wrapRoute(raw,row){return new Proxy(raw,{get:(target,key)=>{
    if(['continue','fulfill','abort'].includes(key))return async(...args)=>{
      const action={action:key,state:'pending'};row.actions.push(action);
      const destination=args[0]?.url||row.url;action.destination=destination;
      const refused=key==='continue'&&!allowedContinuation(destination,this.scene.base);
      action.refused=refused;this.record('request-action',{requestId:row.id,...action});
      if(refused){const error=Error('external continuation prevented by capture retention guard');this.continuationVeto=error;action.state='vetoed';
        this.failure('external-continuation-vetoed',error,{requestId:row.id,url:row.url,destination});
        const abort={action:'abort',guard:true,state:'pending'};row.actions.push(abort);
        try{await target.abort();abort.state='completed';this.record('request-action-completed',{requestId:row.id,...abort});}
        catch(abortError){abort.state='failed';abort.error=errorData(abortError);this.failure('request-action-failed',abortError,{requestId:row.id,...abort});}
        throw error;}
      try{const result=await target[key](...args);action.state='completed';this.record('request-action-completed',{requestId:row.id,...action});return result;}
      catch(error){action.state='failed';action.error=errorData(error);this.failure('request-action-failed',error,{requestId:row.id,...action});throw error;}
    };
    if(['fetch','fallback'].includes(key))return ()=>{const error=Error('unsupported route bypass refused by capture retention guard');
      this.failure('route-bypass-refused',error,{requestId:row.id,action:key});throw error;};
    const value=target[key];return typeof value==='function'?value.bind(target):value;
  }});}
  wrapPage(raw){if(this.pageMap.has(raw))return this.pageMap.get(raw);
    const state={id:this.pages.length+1,errors:[],closed:false};this.pages.push(state);
    raw.on('pageerror',error=>{state.errors.push(errorData(error));this.failure('pageerror',error,{pageId:state.id});});
    raw.on('crash',()=>{state.crashed=true;this.failure('page-crashed',Error('page crashed'),{pageId:state.id});});
    raw.on('close',()=>{state.closed=true;this.record('page-closed',{pageId:state.id});});
    const wrapped=new Proxy(raw,{get:(target,key)=>{
      if(['goto','evaluate','waitForFunction','waitForTimeout','addScriptTag','screenshot'].includes(key))return async(...args)=>{
        try{return await target[key](...args);}catch(error){this.failure('page-operation-threw',error,{pageId:state.id,operation:key});throw error;}};
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});this.pageMap.set(raw,wrapped);this.rawPages.set(wrapped,raw);this.record('page-created',{pageId:state.id});return wrapped;}
  wrapContext(raw){const close=this.closes.context;
    raw.on('close',()=>{close.event=true;this.record('context-close-event');});
    raw.on('page',page=>this.wrapPage(page));
    raw.on('request',request=>{this.requestRow(request,'context').browserState='requested';});
    for(const event of ['requestfinished','requestfailed'])raw.on(event,request=>{
      const row=this.requestRow(request,'context');row.browserState=event==='requestfailed'?'failed':'finished';
      if(event==='requestfailed')row.networkFailure=request.failure?.()??null;
      this.record(event,{requestId:row.id,failure:row.networkFailure??null});});
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='route')return async(pattern,handler,...rest)=>{
        need(pattern==='**/*','catch-all route required');
        await target.route(pattern,async(route,...args)=>{const row=this.requestRow(route.request(),'route');row.callbackState='pending';
          try{const result=await handler(this.wrapRoute(route,row),...args);row.callbackState='returned';this.record('route-handler-returned',{requestId:row.id});return result;}
          catch(error){row.callbackState='threw';row.callbackError=errorData(error);this.failure('route-handler-threw',error,{requestId:row.id});throw error;}},...rest);
        this.routeInstalled=true;this.record('route-installed',{pattern});};
      if(['unroute','unrouteAll'].includes(key))return ()=>{const error=Error('route removal refused during capture');this.failure('route-removal-refused',error);throw error;};
      if(key==='newPage')return async(...args)=>{need(this.routeInstalled,'install catch-all route before creating a page');return this.wrapPage(await target.newPage(...args));};
      // Return the raw session. No new callbacks, acknowledgements, copies,
      // hashing or fsync are inserted into the original screencast stream.
      if(key==='newCDPSession')return async(page,...rest)=>target.newCDPSession(this.rawPages.get(page)||page,...rest);
      if(key==='close')return async(...args)=>{close.called=true;this.record('context-close-started');
        try{const result=await target.close(...args);close.returned=true;this.record('context-close-returned');return result;}
        catch(error){close.error=errorData(error);this.failure('context-close-threw',error);throw error;}};
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});}
  wrapBrowser(raw){const close=this.closes.browser;close.disconnections=[];
    raw.on('disconnected',()=>{const duringClose=close.called===true;close.event=true;close.disconnections.push({duringClose});
      this.record('browser-disconnected',{duringClose});
      if(!duringClose)this.failure('browser-disconnected-unexpectedly',Error('browser disconnected before original close'));});
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='newContext')return async(...args)=>{need(this.scene,'context outside capture scene');need(args[0]?.serviceWorkers==='block','original service-worker block required');
        return this.wrapContext(await target.newContext(...args));};
      if(key==='close')return async(...args)=>{close.called=true;this.record('browser-close-started');
        try{const result=await target.close(...args);close.returned=true;this.record('browser-close-returned');return result;}
        catch(error){close.error=errorData(error);this.failure('browser-close-threw',error);throw error;}};
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});}
  wrapPlaywright(raw,engine){return new Proxy(raw,{get:(target,key)=>key===engine?new Proxy(target[key],{get:(type,name)=>{
    if(name==='launch')return async(...args)=>this.wrapBrowser(await type.launch(...args));const value=type[name];return typeof value==='function'?value.bind(type):value;
  }}):target[key]});}
  wrapHelper(raw){return new Proxy(raw,{get:(target,key)=>{
    if(key==='serve')return async(...args)=>{const result=await target.serve(...args),close=this.closes.server;
      result.srv.on('close',()=>{close.event=true;this.record('server-close-event');});
      const srv=new Proxy(result.srv,{get:(server,name)=>{
        if(name==='close')return (...values)=>{close.called=true;this.record('server-close-started');
          try{const value=server.close(...values);close.returned=true;this.record('server-close-returned');return value;}
          catch(error){close.error=errorData(error);this.failure('server-close-threw',error);throw error;}};
        const value=server[name];return typeof value==='function'?value.bind(server):value;
      }});return {...result,srv};};
    if(key==='openScene')return async(browser,base,ordinary,options)=>{need(!this.scene,'single capture scene required');this.scene={base,options};this.record('scene-started',{base,options});
      try{const scene=await target.openScene(browser,base,ordinary,options);this.scene.log=scene.log;this.scene.url=scene.url;this.record('scene-opened',{url:scene.url,log:scene.log});return scene;}
      catch(error){this.failure('scene-open-threw',error);throw error;}};
    if(key==='waitReady')return async(...args)=>{try{const result=await target.waitReady(...args);this.record('readiness-returned',{value:result});return result;}
      catch(error){this.failure('readiness-threw',error);throw error;}};
    return target[key];
  }});}
  inspectOriginal(){const file=path.join(this.out,'capture.json'),result={originalReport:null,originalPngs:[],reportIssues:[]};
    if(fs.existsSync(this.out))for(const name of fs.readdirSync(this.out).filter(n=>/^f\d+\.png$/.test(n)).sort()){
      const bytes=readRegular(this.out,name);result.originalPngs.push({file:name,bytes:bytes.length,sha256:sha(bytes)});}
    if(!fs.existsSync(file)){result.reportIssues.push('original capture.json absent');return result;}
    const bytes=readRegular(this.out,'capture.json');result.originalReport={file,bytes:bytes.length,sha256:sha(bytes)};
    const report=JSON.parse(bytes);
    for(const [key,value]of Object.entries(this.expected)){
      if(['source','effectiveRateMmPerHour'].includes(key))continue;
      if(!isDeepStrictEqual(report[key],value))result.reportIssues.push('original capture metadata mismatch: '+key);}
    for(const key of ['before','after'])if(!isDeepStrictEqual(report[key],this.expected.source))result.reportIssues.push('original source tuple mismatch: '+key);
    for(const [key,value]of Object.entries(this.pins))if(!isDeepStrictEqual(report[key],value))result.reportIssues.push('original capture pin mismatch: '+key);
    return result;}
  finalize(originalExitCode,stderr=console.error){if(this.finalized)return;this.finalized=true;
    let final;
    const status=()=>{if(this.continuationVeto)return 86;if(originalExitCode>0)return originalExitCode;
      return this.journal.retentionError||final?.issues.length?1:0;};
    const fail=error=>{this.journal.retentionError||=error;process.exitCode=status();
      try{stderr('R0040 capture retention finalization failed:',error);}catch(_){}
      this.journal.preserve('retention-finalization-failed',{exitCode:process.exitCode,error:errorData(error)});};
    try{
      const original=this.inspectOriginal(),issues=[...original.reportIssues];
      if(originalExitCode>0)issues.push('original driver exited nonzero');
      if(this.errors.length||this.driverErrors.length)issues.push('observed request, page, driver or cleanup error');
      if(!this.scene?.log)issues.push('complete scene log unavailable');
      if(this.scene?.log?.errors?.length)issues.push('final original scene log contains page errors');
      if(this.scene?.log?.continuedExternal?.length)issues.push('original scene log contains continuedExternal entries');
      for(const [key,close]of Object.entries(this.closes))if(!close.returned||!close.event)issues.push(key+' closure incomplete');
      for(const row of this.requests){
        const completed=row.actions.filter(a=>a.state==='completed'),last=completed.at(-1);
        if(row.callbackState!=='returned'||!last)issues.push('request '+row.id+' route did not complete');
        if(row.browserState==='failed'&&last?.action!=='abort')issues.push('request '+row.id+' network failed');
        if(row.observedBy.includes('context')&&!['finished','failed'].includes(row.browserState))issues.push('request '+row.id+' final browser state incomplete');}
      if(this.journal.retentionError)issues.push('supplemental retention failed');
      final={protocol:'r0040-capture-final-admission/1',status:'FAILED',originalExitCode,exitCode:0,
        continuationVetoed:Boolean(this.continuationVeto),continuationVetoReason:this.continuationVeto?.message??null,
        ...original,issues,requests:this.requests,pages:this.pages,scene:this.scene,closes:this.closes,errors:this.errors,driverErrors:this.driverErrors,
        retentionError:this.journal.retentionError?errorData(this.journal.retentionError):null,
        timingClass:'instrumented-host-retention',nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',
        interpretation:'Requires actual child exit zero, coordinator isolation receipt and unchanged offline lossless verifier. No cadence or pixel qualification is conferred.'};
      final.exitCode=status();process.exitCode=final.exitCode;
      final.status=this.continuationVeto?'CONTINUATION_VETOED':final.exitCode===0?'ADMITTED_FOR_OFFLINE_VERIFICATION':'FAILED';
      this.journal.record('driver-process-ended',final);
      this.journal.close();this.journal.publish('final-admission.json',final);
    }catch(error){fail(error);try{this.journal.close();}catch(closeError){fail(closeError);}}
    process.exitCode=status();
  }
}

function executeOriginal(driver,args,retain,load=Module.createRequire(path.resolve(driver))){
  need(args.length===8,'eight unchanged original capture arguments required');const source=verifyDriver(driver),filename=path.resolve(driver);
  const [pw,historical]=args,helper=path.resolve(historical,'tools/qa/precip_eval_lib.cjs'),engine=args[4];
  const mod=new Module(filename,module);mod.filename=filename;mod.paths=Module._nodeModulePaths(path.dirname(filename));
  mod.require=request=>request===helper?retain.wrapHelper(load(request)):request===pw?retain.wrapPlaywright(load(request),engine):load(request);
  const originalError=console.error;console.error=(...values)=>{const errors=values.map(errorData);retain.driverErrors.push(...errors);retain.record('driver-error-output',{errors});return originalError(...values);};
  // Monitor without installing a handler that would suppress Node's original
  // fatal-exception behavior (including an unhandled rejection made fatal).
  const fatal=(error,origin)=>retain.failure('uncaught-exception',error,{origin});
  process.on('uncaughtExceptionMonitor',fatal);
  // The original recipe sets exitCode in its catch. Exit runs after asynchronous
  // cleanup and server-close events; SIGTERM/SIGKILL instead leave only a prefix.
  process.once('exit',code=>{console.error=originalError;process.removeListener('uncaughtExceptionMonitor',fatal);retain.finalize(code,originalError);});
  process.argv=[process.argv[0],filename,...args];
  try{mod._compile(source.toString('utf8'),filename);}catch(error){retain.failure('driver-load-threw',error);throw error;}
  return retain;
}
function runDriver(options,args){
  // This must precede any original driver/helper or Playwright import.
  const isolation=verifyIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);
  const admission=verifySources(options,args);need(path.resolve(process.cwd())===admission.research,'immutable research cwd required');
  process.umask(0o077);const retain=new CaptureRetention(options.evidence,{out:args[3],expected:admission.manifest.plannedNativeCell.expectedCapture,pins:admission.manifest.pins});
  retain.record('sources',{isolation,...admission.custody,sources:admission.sources,originalArgv:args,
    wrapperSha256:sha(fs.readFileSync(__filename)),retentionGuardSha256:sha(fs.readFileSync(generic))});
  return executeOriginal(options.driver,args,retain);
}
if(require.main===module){const args=process.argv.slice(2),separator=args.indexOf('--');
  need(separator===10&&args[0]==='--driver'&&args[2]==='--manifest'&&args[4]==='--prepared'&&args[6]==='--preparation-process'&&args[8]==='--evidence',
    'usage: retain_r0040_capture.cjs --driver ORIGINAL --manifest MANIFEST --prepared ORIGINAL_RECEIPT --preparation-process PROCESS_RECEIPT --evidence NEW_PRIVATE_DIR -- PLAYWRIGHT HISTORICAL MAIN NEW_OUT chromium bday moderate M1');
  runDriver({driver:args[1],manifest:args[3],prepared:args[5],preparationProcess:args[7],evidence:args[9]},args.slice(separator+1));}
module.exports={CaptureRetention,CaptureJournal,verifyDriver,verifySourceRows,verifySources,verifyOutputs,verifyIsolation,executeOriginal,runDriver};
