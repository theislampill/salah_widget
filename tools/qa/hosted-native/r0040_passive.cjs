'use strict';
// Separately identified passive acquisition diagnostic. Original driver,
// Date-only adapter, product/worker, reports and lossless verifier stay intact.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const {errorMonitor}=require('node:events');
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const SOURCE_PINS={
  'r0040_dateonly.cjs':'214d4a3c6cb13dbfa69cf0330444aeb9f71d9816b43129091c93bb3121489c44',
  'retain_r0040_capture.cjs':'d252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f',
  'r0040_passive_sampler.cjs':'341d93e7ec2047133de8de80640963f8d9c476cbbad9361e57d23ececdb77fed',
  'r0040_passive_runtime.cjs':'ece35bfbf3a8dfa79e83b84579eb265f0e9a12448015c98ef7172d7a95e14d4c'
};
function verifyLeafSources(){for(const [name,digest]of Object.entries(SOURCE_PINS)){
  const file=path.join(__dirname,name);need(fs.lstatSync(file).isFile()&&!fs.lstatSync(file).isSymbolicLink()&&sha(fs.readFileSync(file))===digest,
    'passive dependency source drift: '+name);
}return {...SOURCE_PINS};}
verifyLeafSources();
const D=require('./r0040_dateonly.cjs'),R=require('./retain_r0040_capture.cjs');
const S=require('./r0040_passive_sampler.cjs'),U=require('./r0040_passive_runtime.cjs');
const ADMITTED='ADMITTED_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION';
const STOP='globalThis.active=false; globalThis.samples',READ='globalThis.__R0040_PASSIVE_SAMPLER__??null';
const primitive=value=>value===null||typeof value==='boolean'?value:typeof value==='string'?value.slice(0,512):
  typeof value==='number'&&Number.isFinite(value)?value:undefined;
const errorData=error=>({name:String(error?.name??'Error').slice(0,512),message:String(error?.message??error).slice(0,512)});
async function bounded(promise,milliseconds){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{
  timer=setTimeout(()=>reject(Error('passive observation evaluation timed out')),milliseconds);})]);}finally{clearTimeout(timer);}}

function passiveIdentity(driver){
  const source=R.verifyDriver(driver),matches=[...source.toString('utf8').matchAll(/await isolated\(`([\s\S]*?)`\);/g)];
  need(matches.length===1,'one original isolated sampler expression required');
  return {protocol:'r0040-passive-diagnostic/1',entrySha256:sha(fs.readFileSync(__filename)),sources:verifyLeafSources(),
    originalDriverSha256:sha(source),sampler:S.instrumentStart(matches[0][1]).identity,
    workerInstallerSha256:sha(U.installWorkerObserver.toString()),runtimeSnapshotSha256:sha(U.snapshotPassiveRuntime.toString()),
    originalDriverUnchanged:true,originalDateOnlyUnchanged:true,originalReportsUnchanged:true,productAndWorkerUnchanged:true,
    timingClass:'instrumented-passive-date-only',nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING'};
}

function inspectPassive(observation,identity){
  need(observation&&observation.protocol==='r0040-passive-observation/1'&&isDeepStrictEqual(observation.identity,identity),
    'passive observation source identity differs');
  const host=observation.host,count=value=>Number.isSafeInteger(value)&&value>=0;
  need(host&&host.protocol==='r0040-passive-host/1'&&host.clockDomain==='node-hrtime'&&host.limit===2048&&
    count(host.dropped)&&count(host.faults)&&host.dropped===0&&host.faults===0,'passive host prefix is incomplete');
  need(Array.isArray(host.rows)&&host.rows.length>0&&host.rows.length<=2048,'bounded passive host prefix required');
  need(host.rows[0].event==='observer-created'&&['playwright-page-closed','playwright-context-closed','server-closed'].every(
    event=>host.rows.filter(row=>row.event===event).length===1),'passive host startup or final closure prefix missing');
  for(const [i,row]of host.rows.entries())need(row.ordinal===i&&typeof row.event==='string'&&/^\d+$/.test(row.monotonicNs)&&
    Object.values(row).every(value=>primitive(value)!==undefined&&(typeof value!=='string'||value.length<=512)),
    'passive host fields or clock domain differ');
  need(Array.isArray(observation.errors)&&observation.errors.length===0,'passive observation collected errors');
  need(Array.isArray(observation.runtimes)&&observation.runtimes.length===2&&
    observation.runtimes[0].phase==='readiness-returned'&&observation.runtimes[1].phase==='before-context-close',
    'both bounded passive runtime phases required');
  for(const row of observation.runtimes)need(row.status==='OBSERVED'&&row.error===null&&
    isDeepStrictEqual(row.inspection,U.inspectRuntime(row.raw)),'passive runtime inspection differs from raw prefix');
  need(Array.isArray(observation.samplers)&&observation.samplers.length<=4,'bounded CDP session population required');
  const samplers=observation.samplers.filter(row=>row.start!==null);
  need(samplers.length===1,'one original sampler extension required');
  const sampler=samplers[0];
  need(isDeepStrictEqual(sampler.start,identity.sampler)&&Number.isInteger(sampler.contextId)&&sampler.contextId>0&&
    sampler.streamStarted===true&&sampler.streamStopped===true&&sampler.originalStopReturned===true&&sampler.detached===true,
    'complete original sampler and stream lifecycle required');
  need(sampler.extractions.length===1,'one completed post-stream extraction required');
  const extraction=sampler.extractions[0];
  need(extraction.phase==='after-original-stop'&&extraction.status==='OBSERVED'&&extraction.error===null&&
    Number.isSafeInteger(sampler.originalSampleCount)&&sampler.originalSampleCount>0&&extraction.raw?.rows?.length===sampler.originalSampleCount&&
    isDeepStrictEqual(extraction.inspection,S.inspectSampler(extraction.raw)),'passive sampler inspection differs from raw prefix');
  return {protocol:'r0040-passive-inspection/1',status:'OBSERVED',hostEvents:host.rows.length,runtimeSnapshots:2,
    samplerRows:extraction.raw.rows.length,clockDomains:['node-hrtime','main-performance','isolated-performance'],
    interpretation:'Separate instrumented diagnostic with same-domain intervals only; no cadence, frame association, worker health, visual or product acceptance.'};
}

function admitPassiveReceipt(receipt,baseBytes,identity,diagnostic,actualExitCode){
  need(Number.isInteger(actualExitCode)&&actualExitCode===0,'actual passive child exit zero required');
  const base=JSON.parse(baseBytes);
  need(receipt?.protocol==='r0040-passive-final-observation/1'&&receipt.status===ADMITTED&&receipt.exitCode===0&&
    receipt.originalExitCode===0&&receipt.continuationVetoed===false&&receipt.retentionError===null&&
    receipt.timingClass==='instrumented-passive-date-only'&&receipt.nativeQualification==='NOT_VERIFIED'&&receipt.humanAcceptance==='OUTSTANDING'&&
    receipt.issues.length===0&&receipt.baseAdmission?.sha256===sha(baseBytes)&&receipt.baseAdmission.bytes===baseBytes.length,
    'complete passive final receipt and original admission custody required');
  need(base.protocol==='r0040-capture-final-admission/1'&&base.status===D.ADMITTED&&base.exitCode===0&&base.originalExitCode===0&&
    base.continuationVetoed===false&&base.retentionError===null&&base.issues.length===0&&isDeepStrictEqual(base.diagnostic,diagnostic),
    'unchanged Date-only final admission required');
  need(base.clockProofs?.length===1&&base.clockProofs[0].status==='OBSERVED'&&isDeepStrictEqual(base.clockProofs[0].admission,
    D.admitClockProof(base.clockProofs[0].raw,base.clockProofs[0].raw.utcMs)),'Date-only clock proof differs');
  need(isDeepStrictEqual(receipt.inspection,inspectPassive(receipt.observation,identity)),'passive final inspection differs');
  return receipt.inspection;
}

class PassiveRetention extends D.DateOnlyRetention {
  constructor(directory,{passive,collectionTimeoutMs=5000,...options}){
    super(directory,options);this.collectionTimeoutMs=collectionTimeoutMs;
    this.passive={protocol:'r0040-passive-observation/1',identity:passive,
      host:{protocol:'r0040-passive-host/1',clockDomain:'node-hrtime',limit:2048,rows:[],dropped:0,faults:0},
      runtimes:[],samplers:[],errors:[]};
    this.passivePageMap=new WeakMap();this.installedPages=new WeakSet();this.sessions=[];this.workerSequence=0;this.serverSequence=0;
    const record=this.journal.record.bind(this.journal);
    this.journal.record=(event,value={})=>{
      const result=record(event,value);
      if(event==='driver-process-ended')record('passive-terminal-status',{protocol:'r0040-passive-terminal-status/1',
        originalExitCode:value.originalExitCode,dateOnlyAdmissionExitCode:value.exitCode,
        exitCode:value.exitCode||((this.passiveIssues.length||value.status!==D.ADMITTED)?1:0),
        continuationVetoed:Boolean(this.continuationVeto),issues:this.passiveIssues,
        scope:'Supplemental expected terminal status; external actual process result remains mandatory.'});
      return result;
    };
    const publish=this.journal.publish.bind(this.journal);
    this.journal.publish=(name,value)=>{
      const result=publish(name,value);
      if(name==='final-admission.json'){
        const bytes=fs.readFileSync(path.join(this.journal.directory,name)),issues=[...this.passiveIssues];
        const exitCode=value.exitCode||((issues.length||value.status!==D.ADMITTED)?1:0);
        publish('passive-observation.json',{protocol:'r0040-passive-final-observation/1',
          status:this.continuationVeto?'CONTINUATION_VETOED':exitCode===0?ADMITTED:issues.length&&value.exitCode===0?'INCOMPLETE':'FAILED',
          exitCode,originalExitCode:value.originalExitCode,continuationVetoed:Boolean(this.continuationVeto),retentionError:value.retentionError,
          baseAdmission:{file:name,sha256:sha(bytes),bytes:bytes.length},observation:this.passive,inspection:this.passiveInspection,issues,
          timingClass:'instrumented-passive-date-only',nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',
          interpretation:'Requires actual child exit zero, both final receipts, current isolation/source admission, the unchanged lossless verifier and human review. No cadence qualification.'});
      }
      return result;
    };
    this.host('observer-created');
    this.record('passive-instrumentation',{identity:passive,
      overhead:'Bounded in-memory Worker/response/server bookkeeping; two isolated-world clock reads and one numeric row per original sampler callback. Startup/readiness/cleanup evaluations and final serialization add uncalibrated overhead. No new screencast listener, PNG copy, ACK handling or per-frame fsync. Clock domains are separate.'});
  }
  passiveError(phase,error){if(this.passive.errors.length<32)this.passive.errors.push({phase,error:errorData(error)});
    else this.passive.host.faults++;}
  host(event,fields={}){try{
    const host=this.passive.host;if(host.rows.length===host.limit){host.dropped++;return;}
    const row={ordinal:host.rows.length,event,monotonicNs:process.hrtime.bigint().toString()};
    for(const [key,value]of Object.entries(fields)){const v=primitive(value);if(v!==undefined)row[key]=v;}
    host.rows.push(row);
  }catch(error){this.passive.host.faults++;this.passiveError('host-event',error);}}
  hostSafely(fn){try{fn();}catch(error){this.passive.host.faults++;this.passiveError('host-event',error);}}
  wrapPage(raw){
    const wrapped=super.wrapPage(raw);if(this.passivePageMap.has(raw))return wrapped;
    const pageId=this.pages.length;this.passivePageMap.set(raw,pageId);this.passivePage=wrapped;
    raw.on('worker',worker=>this.hostSafely(()=>{const workerId=++this.workerSequence;
      if(workerId>16){this.passive.host.dropped++;return;}
      this.host('playwright-worker-created',{pageId,workerId,url:worker.url()});
      worker.on('close',()=>this.host('playwright-worker-closed',{pageId,workerId}));}));
    raw.on('close',()=>this.host('playwright-page-closed',{pageId}));return wrapped;
  }
  async runtimeSnapshot(page,phase){
    if(this.passive.runtimes.length>=4){this.passiveError(phase,Error('bounded passive runtime phases exceeded'));return;}
    const row={phase,status:'UNAVAILABLE',raw:null,inspection:null,error:null};this.passive.runtimes.push(row);
    try{
      const raw=this.rawPages.get(page)||page;
      row.raw=await bounded(raw.evaluate(U.snapshotPassiveRuntime),this.collectionTimeoutMs);row.status='INCOMPLETE';
      row.inspection=U.inspectRuntime(row.raw);row.status='OBSERVED';
    }catch(error){row.error=errorData(error);this.passiveError(phase,error);}
    finally{this.record('passive-runtime-prefix',{observation:row,hostPrefix:this.passive.host});}
  }
  async samplerSnapshot(session,phase){
    const row={phase,status:'UNAVAILABLE',raw:null,inspection:null,error:null};session.record.extractions.push(row);
    try{
      const result=await bounded(session.raw.send('Runtime.evaluate',{contextId:session.record.contextId,expression:READ,returnByValue:true}),this.collectionTimeoutMs);
      need(!result.exceptionDetails,'passive isolated extraction returned exception details');
      row.raw=result.result?.value??null;row.status='INCOMPLETE';row.inspection=S.inspectSampler(row.raw);
      if(phase==='after-original-stop')row.status='OBSERVED';
    }catch(error){row.error=errorData(error);this.passiveError(phase,error);}
    finally{this.record('passive-sampler-prefix',{sessionId:session.record.id,observation:row});}
  }
  wrapCDP(raw){
    need(this.sessions.length<4,'bounded CDP session population exceeded');
    const record={id:this.sessions.length+1,contextId:null,start:null,streamStarted:false,streamStopped:false,originalStopReturned:false,
      originalSampleCount:null,detached:false,extractions:[]};
    const session={raw,record};this.sessions.push(session);this.passive.samplers.push(record);
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='send')return (method,params,...rest)=>{
        // Return the exact original ACK promise. No callback, observation,
        // serialization or fsync enters the original screencast ACK path.
        if(method==='Page.screencastFrameAck')return target.send(method,params,...rest);
        if(method==='Page.createIsolatedWorld'){
          need(params?.worldName==='r0040-native-clock'&&record.contextId===null,'original isolated sampler world required');
          return target.send(method,params,...rest).then(result=>{need(Number.isInteger(result.executionContextId)&&result.executionContextId>0,
            'original sampler context unavailable');record.contextId=result.executionContextId;return result;});
        }
        if(method==='Runtime.evaluate'){
          need(params?.contextId===record.contextId&&record.contextId!==null&&params.returnByValue===true,'original sampler context and return-by-value required');
          if(params.expression===STOP){
            need(record.start&&record.streamStopped&&!record.originalStopReturned,'original sampler stop ordering required');
            return target.send(method,params,...rest).then(async result=>{
              record.originalStopReturned=true;
              record.originalSampleCount=Array.isArray(result.result?.value)?result.result.value.length:null;
              await this.samplerSnapshot(session,'after-original-stop');return result;});
          }
          need(record.start===null,'one original sampler start expression required');
          const transformed=S.instrumentStart(params.expression);
          need(isDeepStrictEqual(transformed.identity,this.passive.identity.sampler),'sampler extension identity differs');
          record.start=transformed.identity;return target.send(method,{...params,expression:transformed.expression},...rest);
        }
        if(method==='Page.startScreencast')return target.send(method,params,...rest).then(result=>{record.streamStarted=true;return result;});
        if(method==='Page.stopScreencast')return target.send(method,params,...rest).then(result=>{record.streamStopped=true;return result;});
        return target.send(method,params,...rest);
      };
      if(key==='detach')return (...args)=>target.detach(...args).then(result=>{record.detached=true;return result;});
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  wrapContext(raw){
    const wrapped=super.wrapContext(raw);
    raw.on('response',response=>this.hostSafely(()=>{
      const request=response.request(),row=this.requestMap.get(request),headers=response.headers();
      const fields={requestId:row?.id??null,url:request.url(),status:response.status(),statusText:response.statusText(),fromServiceWorker:response.fromServiceWorker()};
      for(const key of ['content-type','content-length','content-encoding','cache-control'])fields[key]=headers[key];
      this.host('browser-response',fields);if(!row)this.passiveError('browser-response',Error('existing capture request ID unavailable'));
    }));
    raw.on('close',()=>this.host('playwright-context-closed'));
    const context=new Proxy(wrapped,{get:(target,key)=>{
      if(key==='newPage')return async(...args)=>{
        const page=await target.newPage(...args);
        if(!this.installedPages.has(page)){
          await bounded(page.addInitScript(U.installWorkerObserver),this.collectionTimeoutMs);this.installedPages.add(page);
          this.host('main-observer-installed-before-navigation');
        }return page;
      };
      if(key==='newCDPSession')return async(...args)=>this.wrapCDP(await target.newCDPSession(...args));
      if(key==='close')return async(...args)=>{
        try{
          if(this.passivePage)await this.runtimeSnapshot(this.passivePage,'before-context-close');
          for(const session of this.sessions)if(session.record.start&&!session.record.detached&&session.record.extractions.length===0)
            await this.samplerSnapshot(session,'before-context-close-incomplete-prefix');
        }catch(error){this.passiveError('before-context-close',error);}
        return target.close(...args);
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});this.acquiredContext=context;return context;
  }
  wrapHelper(raw){
    const wrapped=super.wrapHelper(raw);
    return new Proxy(wrapped,{get:(target,key)=>{
      if(key==='waitReady')return async(page,...args)=>{const result=await target.waitReady(page,...args);
        await this.runtimeSnapshot(page,'readiness-returned');return result;};
      if(key==='serve')return async(...args)=>{
        const result=await target.serve(...args);
        result.srv.on('request',(request,response)=>this.hostSafely(()=>{
          const serverRequestId=++this.serverSequence;this.host('server-request',{serverRequestId,url:request.url,method:request.method});
          request.on('aborted',()=>this.host('server-request-aborted',{serverRequestId}));
          // Node's errorMonitor observes the original error without turning
          // an unhandled error into a handled one or replacing its exception.
          request.on(errorMonitor,error=>this.hostSafely(()=>this.host('server-request-error',{serverRequestId,error:error.message})));
          for(const event of ['finish','close','error'])response.on(event==='error'?errorMonitor:event,error=>this.hostSafely(()=>{
            const fields={serverRequestId,status:response.statusCode,error:error?.message};
            for(const name of ['content-type','content-length','content-encoding'])fields[name]=response.getHeader(name);
            this.host('server-response-'+event,fields);
          }));
        }));
        result.srv.on(errorMonitor,error=>this.hostSafely(()=>this.host('server-error',{error:error.message})));
        result.srv.on('close',()=>this.host('server-closed'));return result;
      };
      return target[key];
    }});
  }
  finalize(originalExitCode,stderr){
    if(this.finalized)return;
    this.passiveIssues=[];this.passiveInspection=null;
    try{this.passiveInspection=inspectPassive(this.passive,this.passive.identity);}
    catch(error){this.passiveIssues.push(errorData(error));}
    this.record('passive-observation-ended',{observation:this.passive,inspection:this.passiveInspection,issues:this.passiveIssues});
    super.finalize(originalExitCode,stderr);
    // Base Date-only admission is retained verbatim. The supplemental receipt
    // and actual terminal status independently fail if its added collection is
    // incomplete. Veto and original nonzero status retain precedence.
    process.exitCode=this.continuationVeto?86:originalExitCode>0?originalExitCode:
      process.exitCode>0?process.exitCode:this.passiveIssues.length?1:0;
  }
}

function runDriver(options,args){
  // Original helper, driver and browser import only after all original gates.
  const isolation=R.verifyIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);
  verifyLeafSources();const admission=R.verifySources(options,args);
  need(path.resolve(process.cwd())===admission.research,'immutable research cwd required');
  const preparationEntry=D.admitPreparationEntry(options.preparationEntry,options,args);
  const helper=fs.readFileSync(path.join(args[1],'tools/qa/precip_eval_lib.cjs'));
  const diagnostic=D.diagnosticIdentity(D.transformHelper(helper).identity),passive=passiveIdentity(options.driver);
  process.umask(0o077);
  const retain=new PassiveRetention(options.evidence,{out:args[3],expected:admission.manifest.plannedNativeCell.expectedCapture,
    pins:admission.manifest.pins,diagnostic,passive});
  retain.record('sources',{isolation,...admission.custody,preparationEntry,sources:admission.sources,originalArgv:args,diagnostic,passive});
  if(retain.journal.retentionError)throw retain.journal.retentionError;
  return D.executeOriginal(options.driver,args,retain);
}
if(require.main===module){
  const args=process.argv.slice(2),separator=args.indexOf('--');
  need(separator===12&&args[0]==='--driver'&&args[2]==='--manifest'&&args[4]==='--prepared'&&args[6]==='--preparation-process'&&
    args[8]==='--preparation-entry'&&args[10]==='--evidence',
    'usage: r0040_passive.cjs --driver ORIGINAL --manifest MANIFEST --prepared ORIGINAL_RECEIPT --preparation-process PROCESS --preparation-entry ENTRY --evidence NEW_PRIVATE_DIR -- PLAYWRIGHT HISTORICAL MAIN NEW_OUT chromium bday moderate M1');
  runDriver({driver:args[1],manifest:args[3],prepared:args[5],preparationProcess:args[7],preparationEntry:args[9],evidence:args[11]},args.slice(separator+1));
}
module.exports={ADMITTED,SOURCE_PINS,verifyLeafSources,passiveIdentity,inspectPassive,admitPassiveReceipt,PassiveRetention,runDriver,executeOriginal:D.executeOriginal};
