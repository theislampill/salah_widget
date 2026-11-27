'use strict';
// Explicit opt-in extension of the byte-identical reviewed passive leaf.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const {isDeepStrictEqual}=require('node:util');
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const SOURCE_PINS={
  'r0040_passive.cjs':'7386366a391cb7e401d11a36da691771b1d88a09fa8c16584093184ebd8a7a5e',
  'r0040_mechanism_bracket.cjs':'b2a2e73433055ab90f4ae617f70268e0d5f02563e36c6a5ffc071ce0445c5757',
  'r0040_mechanism_network.cjs':'77d40fa3519d0328fb3fcfda34f5c5001e0d82790b365801f989a5126a978af7'
};
function verifySources(){for(const [name,digest]of Object.entries(SOURCE_PINS)){
  const file=path.join(__dirname,name);need(fs.lstatSync(file).isFile()&&!fs.lstatSync(file).isSymbolicLink()&&sha(fs.readFileSync(file))===digest,
    'mechanism dependency source drift: '+name);
}return {...SOURCE_PINS};}
verifySources();
const P=require('./r0040_passive.cjs'),D=require('./r0040_dateonly.cjs'),R=require('./retain_r0040_capture.cjs');
const B=require('./r0040_mechanism_bracket.cjs'),N=require('./r0040_mechanism_network.cjs');
const ADMITTED='ADMITTED_MECHANISM_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION';
const TIMING='instrumented-mechanism-passive-date-only',STOP='globalThis.active=false; globalThis.samples';
const ARTIFACT='mechanism-observation.json',ARTIFACT_BYTES=4*1024*1024;
const errorData=error=>({name:String(error?.name??'Error').slice(0,128),message:String(error?.message??error).slice(0,1024)});
async function bounded(promise,milliseconds){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{
  timer=setTimeout(()=>reject(Error('mechanism observation extraction timed out')),milliseconds);})]);}finally{clearTimeout(timer);}}

function mechanismIdentity(driver){
  const source=R.verifyDriver(driver),expressions=B.originalExpressions(source),passive=P.passiveIdentity(driver);
  return {protocol:'r0040-mechanism-diagnostic/1',entrySha256:sha(fs.readFileSync(__filename)),sources:verifySources(),passive,
    main:B.instrumentMain(expressions.main).identity,isolated:B.instrumentIsolated(require('./r0040_passive_sampler.cjs').instrumentStart(expressions.isolated).expression).identity,
    mainSnapshotSha256:sha(B.snapshotMain.toString()),joinExpressionSha256:sha(B.READ_JOIN),networkLimits:N.LIMITS,
    originalSourceUnchanged:true,originalCallbackBodyUnchanged:true,originalSampleAndStopUnchanged:true,
    operationalDiagnosticExtended:true,originalVerifierUnchanged:true,productAndWorkerConsumersUnchanged:true,
    budgets:{childSeconds:240,setupSeconds:5,parallelExtractionSeconds:5,networkDrainSeconds:5,remainingRetentionReserveSeconds:25,finalReplaySeconds:30},
    timingClass:TIMING,nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING'};
}

function inspectMechanism(observation,identity,base,passive,originalStopBytes){
  need(observation?.protocol==='r0040-mechanism-observation/1'&&isDeepStrictEqual(observation.identity,identity),
    'mechanism observation source identity differs');
  const inspect=fn=>{try{return {status:'OBSERVED',inspection:fn(),error:null};}
    catch(error){return {status:'INCOMPLETE',inspection:null,error:errorData(error)};}};
  const bracket=inspect(()=>{
    need(isDeepStrictEqual(passive?.identity,identity.passive),'original passive identity differs');
    need(observation.mainInstall?.status==='INSTALLED'&&observation.mainInstall.error===null&&
      isDeepStrictEqual(observation.mainInstall.identity,identity.main)&&
      observation.isolatedInstall?.status==='INSTALLED'&&observation.isolatedInstall.error===null&&
      isDeepStrictEqual(observation.isolatedInstall.identity,identity.isolated),'complete exact main/isolated installations required');
    const collected=observation.bracket;
    need(collected?.phase==='after-original-stop'&&collected.main.status==='OBSERVED'&&collected.main.error===null&&
      collected.join.status==='OBSERVED'&&collected.join.error===null,'complete post-stop main/join extraction required');
    const samplers=passive.samplers.filter(row=>row.start!==null);need(samplers.length===1,'one original passive sampler required');
    const sampler=samplers[0],artifact=sampler.originalStopResponse?.artifact;
    need(Buffer.isBuffer(originalStopBytes)&&originalStopBytes.length>0&&originalStopBytes.length<=P.STOP_LIMITS.bytes&&
      artifact?.file==='passive-original-stop-'+sampler.id+'.json'&&artifact.bytes===originalStopBytes.length&&artifact.sha256===sha(originalStopBytes),
      'actual original stop Buffer identity required');
    need(sampler.streamStopped===true&&sampler.originalStopReturned===true&&sampler.originalStopResponse.status==='RETAINED'&&
      sampler.originalSampleCount===collected.main.raw?.calls&&sampler.extractions.length===1&&
      sampler.extractions[0].phase==='after-original-stop','original passive post-stop lifecycle required');
    need(base?.clockProofs?.length===1&&base.clockProofs[0].status==='OBSERVED','original main startup clock proof required');
    const proof=base.clockProofs[0].raw;D.admitClockProof(proof,proof.utcMs);
    return B.inspectBrackets(collected.main.raw,collected.join.raw,sampler.extractions[0].raw,originalStopBytes,proof);
  });
  const network=inspect(()=>{
    need(isDeepStrictEqual(passive?.identity,identity.passive),'original passive identity differs');
    const runtime=passive.runtimes?.find(row=>row.phase==='before-context-close');
    need(runtime?.status==='OBSERVED'&&runtime.error===null,'original bounded worker prefix required');
    return N.inspectNetwork(observation.network,base?.requests,runtime.raw?.observer?.events,base?.scene?.base);
  });
  return {protocol:'r0040-mechanism-inspection/1',status:bracket.status==='OBSERVED'&&network.status==='OBSERVED'?'OBSERVED':'INCOMPLETE',
    bracket,network,nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',cause:'NOT_ESTABLISHED',
    interpretation:'Independent diagnostic completeness only; original failures and actual process/namespace status retain precedence.'};
}

function admitMechanismReceipt(receipt,baseBytes,passiveBytes,identity,diagnostic,actualExitCode,originalStopBytes){
  need(Number.isInteger(actualExitCode)&&actualExitCode===0,'actual mechanism child exit zero required');
  need(Buffer.isBuffer(baseBytes)&&Buffer.isBuffer(passiveBytes)&&Buffer.isBuffer(originalStopBytes),'actual base/passive/stop Buffer bytes required');
  const base=JSON.parse(baseBytes),passive=JSON.parse(passiveBytes);
  const old=P.admitPassiveReceipt(passive,baseBytes,identity.passive,diagnostic,actualExitCode,originalStopBytes);
  need(receipt?.protocol==='r0040-mechanism-final-observation/1'&&receipt.status===ADMITTED&&receipt.exitCode===0&&receipt.originalExitCode===0&&
    receipt.continuationVetoed===false&&receipt.retentionError===null&&receipt.timingClass===TIMING&&
    receipt.nativeQualification==='NOT_VERIFIED'&&receipt.humanAcceptance==='OUTSTANDING'&&
    receipt.baseAdmission?.file==='final-admission.json'&&receipt.baseAdmission.sha256===sha(baseBytes)&&receipt.baseAdmission.bytes===baseBytes.length&&
    receipt.passiveAdmission?.file==='passive-observation.json'&&receipt.passiveAdmission.sha256===sha(passiveBytes)&&receipt.passiveAdmission.bytes===passiveBytes.length,
    'complete mechanism receipt and original admission custody required');
  const inspection=inspectMechanism(receipt.observation,identity,base,passive.observation,originalStopBytes);
  need(inspection.status==='OBSERVED'&&isDeepStrictEqual(receipt.inspection,inspection),'mechanism diagnostic incomplete or inspection differs');
  return {protocol:'r0040-mechanism-admission/1',status:'OBSERVED',passive:old,mechanism:inspection};
}

class MechanismRetention extends P.PassiveRetention{
  constructor(directory,{mechanism,networkTimeoutMs=5000,...options}){
    super(directory,options);this.mechanismPages=new WeakMap();this.mechanismPage=null;this.mechanismSessions=[];
    need(Number.isInteger(this.collectionTimeoutMs)&&this.collectionTimeoutMs>0&&this.collectionTimeoutMs<=5000,
      'bounded parallel mechanism extraction required');
    this.networkObserver=new N.NetworkObserver({timeoutMs:networkTimeoutMs});
    this.mechanism={protocol:'r0040-mechanism-observation/1',identity:mechanism,mainInstall:null,isolatedInstall:null,bracket:null,network:null};
    this.mechanismInspection=null;
    const publish=this.journal.publish.bind(this.journal);
    this.journal.publish=(name,value)=>{
      const result=publish(name,value);
      if(name==='final-admission.json'){
        const baseBytes=fs.readFileSync(path.join(this.journal.directory,name)),passiveBytes=fs.readFileSync(path.join(this.journal.directory,'passive-observation.json'));
        const old=JSON.parse(passiveBytes),exitCode=old.exitCode||(this.mechanismInspection?.status==='OBSERVED'?0:1);
        const receipt={protocol:'r0040-mechanism-final-observation/1',status:this.continuationVeto?'CONTINUATION_VETOED':
          exitCode===0?ADMITTED:old.exitCode?'FAILED':'INCOMPLETE',exitCode,originalExitCode:old.originalExitCode,
          continuationVetoed:Boolean(this.continuationVeto),retentionError:value.retentionError,
          baseAdmission:{file:name,bytes:baseBytes.length,sha256:sha(baseBytes)},
          passiveAdmission:{file:'passive-observation.json',bytes:passiveBytes.length,sha256:sha(passiveBytes)},
          observation:this.mechanism,inspection:this.mechanismInspection,timingClass:TIMING,nativeQualification:'NOT_VERIFIED',humanAcceptance:'OUTSTANDING',
          interpretation:'Independent bracket/network completeness never overrides original Date-only/passive failure, actual exit, namespace admission or unchanged verifier.'};
        need(Buffer.byteLength(JSON.stringify(receipt,null,2)+'\n')<=ARTIFACT_BYTES,'bounded mechanism receipt exceeded');publish(ARTIFACT,receipt);
      }
      return result;
    };
    this.record('mechanism-instrumentation',{identity:mechanism,
      overhead:'Explicit main callback brackets and read-only isolated event joins; separate non-pausing Target/Network metadata. Bounded setup, parallel post-stop extraction and shutdown use 15 seconds of the existing retention reserve. Uncalibrated instrumentation; original samples, stop, ACKs and waits are unchanged.'});
  }
  wrapPage(raw){
    if(this.mechanismPages?.has(raw))return this.mechanismPages.get(raw);
    const wrapped=super.wrapPage(raw);this.mechanismPage=raw;
    const extended=new Proxy(wrapped,{get:(target,key)=>{
      if(key==='evaluate')return (fn,...args)=>{
        if(typeof fn!=='function'||!fn.toString().includes('window.__r0040Sample=()=>'))return target.evaluate(fn,...args);
        need(this.mechanism.mainInstall===null,'one original main listener installation required');
        const transformed=B.instrumentMain(fn.toString());need(isDeepStrictEqual(transformed.identity,this.mechanism.identity.main),'main listener transform identity differs');
        const row={status:'INCOMPLETE',identity:transformed.identity,error:null};this.mechanism.mainInstall=row;
        const adapted=vm.runInNewContext('('+transformed.expression+')');
        return target.evaluate(adapted,...args).then(result=>{row.status='INSTALLED';return result;},error=>{row.error=errorData(error);throw error;});
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
    this.mechanismPages.set(raw,extended);this.rawPages.set(extended,raw);return extended;
  }
  wrapCDP(raw){
    let contextId=null;
    const inner=new Proxy(raw,{get:(target,key)=>{
      if(key==='send')return (method,params,...rest)=>{
        if(method==='Runtime.evaluate'&&typeof params?.expression==='string'&&params.expression.includes('const passiveSampler=')){
          need(this.mechanism.isolatedInstall===null,'one exact passive isolated extension required');
          const transformed=B.instrumentIsolated(params.expression);need(isDeepStrictEqual(transformed.identity,this.mechanism.identity.isolated),'isolated event-join transform identity differs');
          const row={status:'INCOMPLETE',identity:transformed.identity,error:null};this.mechanism.isolatedInstall=row;contextId=params.contextId;
          return target.send(method,{...params,expression:transformed.expression},...rest).then(result=>{
            row.status=!result.exceptionDetails&&result.result?.value===true?'INSTALLED':'INCOMPLETE';return result;
          },error=>{row.error=errorData(error);throw error;});
        }
        return target.send(method,params,...rest);
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
    const passive=super.wrapCDP(inner),session={raw,context:()=>contextId};this.mechanismSessions.push(session);
    return new Proxy(passive,{get:(target,key)=>{
      if(key==='send')return (method,params,...rest)=>{
        const result=target.send(method,params,...rest);
        if(method==='Runtime.evaluate'&&params?.expression===STOP)return result.then(async value=>{
          // The unchanged passive adapter has already retained the exact stop.
          await this.collectBrackets(session,'after-original-stop');return value;
        });
        return result;
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  async collectBrackets(session,phase){
    if(this.mechanism.bracket!==null)return;
    const row={phase,main:{status:'UNAVAILABLE',raw:null,error:null},join:{status:'UNAVAILABLE',raw:null,error:null}};this.mechanism.bracket=row;
    const collect=async(name,fn)=>{try{row[name].raw=await bounded(fn(),this.collectionTimeoutMs);row[name].status='OBSERVED';}
      catch(error){row[name].status='INCOMPLETE';row[name].error=errorData(error);}};
    await Promise.all([collect('main',()=>{need(this.mechanismPage,'original main page unavailable');return this.mechanismPage.evaluate(B.snapshotMain);}),
      collect('join',async()=>{need(session&&Number.isInteger(session.context())&&session.context()>0,'original isolated join context unavailable');
        const value=await session.raw.send('Runtime.evaluate',{contextId:session.context(),expression:B.READ_JOIN,returnByValue:true});
        need(!value.exceptionDetails,'isolated join extraction returned exception details');return value.result?.value??null;})]);
    this.record('mechanism-bracket-prefix',{observation:row});
  }
  async runtimeSnapshot(page,phase){
    const result=await super.runtimeSnapshot(page,phase);
    if(phase==='readiness-returned')this.record('mechanism-network-prefix',{phase,observation:this.networkObserver.snapshot()});
    return result;
  }
  wrapContext(raw){
    const wrapped=super.wrapContext(raw);
    return new Proxy(wrapped,{get:(target,key)=>{
      if(key==='close')return async(...args)=>{
        if(this.mechanism.bracket===null)await this.collectBrackets(this.mechanismSessions.find(s=>s.context()!==null),'before-context-close-incomplete-prefix');
        return target.close(...args);
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  wrapBrowser(raw){
    const wrapped=super.wrapBrowser(raw);
    return new Proxy(wrapped,{get:(target,key)=>{
      if(key==='newContext')return async(...args)=>{
        await this.networkObserver.start(raw,this.scene?.base);
        this.record('mechanism-network-prefix',{phase:'before-context-creation',observation:this.networkObserver.snapshot()});
        return target.newContext(...args);
      };
      if(key==='close')return async(...args)=>{
        this.mechanism.network=await this.networkObserver.finish();
        this.record('mechanism-network-prefix',{phase:'after-original-context-close',observation:this.mechanism.network});
        return target.close(...args);
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  finalize(originalExitCode,stderr){
    if(this.finalized)return;
    this.mechanism.network??=this.networkObserver.snapshot();let stop=null;
    try{stop=this.readOriginalStop();}catch(_){}
    this.mechanismInspection=inspectMechanism(this.mechanism,this.mechanism.identity,
      {requests:this.requests,scene:this.scene,clockProofs:this.clockProofs},this.passive,stop);
    this.record('mechanism-observation-ended',{observation:this.mechanism,inspection:this.mechanismInspection});
    super.finalize(originalExitCode,stderr);
    process.exitCode=this.continuationVeto?86:originalExitCode>0?originalExitCode:process.exitCode>0?process.exitCode:
      this.mechanismInspection.status==='OBSERVED'?0:1;
  }
}

function runDriver(options,args){
  const isolation=R.verifyIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);
  verifySources();P.verifyLeafSources();const admission=R.verifySources(options,args);
  need(path.resolve(process.cwd())===admission.research,'immutable research cwd required');
  const preparationEntry=D.admitPreparationEntry(options.preparationEntry,options,args);
  const helper=fs.readFileSync(path.join(args[1],'tools/qa/precip_eval_lib.cjs'));
  const diagnostic=D.diagnosticIdentity(D.transformHelper(helper).identity),passive=P.passiveIdentity(options.driver),mechanism=mechanismIdentity(options.driver);
  process.umask(0o077);
  const retain=new MechanismRetention(options.evidence,{out:args[3],expected:admission.manifest.plannedNativeCell.expectedCapture,
    pins:admission.manifest.pins,diagnostic,passive,mechanism});
  retain.record('sources',{isolation,...admission.custody,preparationEntry,sources:admission.sources,originalArgv:args,diagnostic,passive,mechanism});
  if(retain.journal.retentionError)throw retain.journal.retentionError;
  return D.executeOriginal(options.driver,args,retain);
}
if(require.main===module){
  const args=process.argv.slice(2),separator=args.indexOf('--');
  need(separator===12&&args[0]==='--driver'&&args[2]==='--manifest'&&args[4]==='--prepared'&&args[6]==='--preparation-process'&&
    args[8]==='--preparation-entry'&&args[10]==='--evidence',
    'usage: r0040_mechanism.cjs --driver ORIGINAL --manifest MANIFEST --prepared ORIGINAL_RECEIPT --preparation-process PROCESS --preparation-entry ENTRY --evidence NEW_PRIVATE_DIR -- PLAYWRIGHT HISTORICAL MAIN NEW_OUT chromium bday moderate M1');
  runDriver({driver:args[1],manifest:args[3],prepared:args[5],preparationProcess:args[7],preparationEntry:args[9],evidence:args[11]},args.slice(separator+1));
}
module.exports={ADMITTED,TIMING,ARTIFACT,ARTIFACT_BYTES,SOURCE_PINS,verifySources,mechanismIdentity,inspectMechanism,admitMechanismReceipt,
  MechanismRetention,runDriver};
