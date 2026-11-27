'use strict';
// Separately identified research diagnostic. The original capture driver and
// lossless verifier stay unchanged; one helper seam replaces its full clock.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),Module=require('node:module');
const {isDeepStrictEqual}=require('node:util');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const RETENTION_SHA256='d252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f';
const ORIGINAL_SHA256='a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7';
const PREPARER_SHA256='4ba6328ee9fe96aec4a96109c58d0d67e0d3e434756829fbe247816bcd001f68';
const ADMITTED='ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION';
need(sha(fs.readFileSync(path.join(__dirname,'retain_r0040_capture.cjs')))===RETENTION_SHA256,'capture retention source drift');
const R=require('./retain_r0040_capture.cjs');
const errorData=error=>({name:error?.name,message:String(error?.message??error),stack:error?.stack});

function installDateOnly({utcMs}){
  if(!Number.isSafeInteger(utcMs)||utcMs<=0||window.__R0040_DATE_ONLY__)throw Error('fresh finite Date-only epoch required');
  const NativeDate=Date,nativePerformance=performance,nativeNow=performance.now,timeOriginMs=performance.timeOrigin;
  const timers={setTimeout,clearTimeout,setInterval,clearInterval,requestAnimationFrame,cancelAnimationFrame,queueMicrotask};
  const anchorPerformanceMs=nativeNow.call(nativePerformance);
  const now=()=>Math.floor(utcMs+nativeNow.call(nativePerformance)-anchorPerformanceMs);
  const DateOnly=new Proxy(NativeDate,{
    apply(){return new NativeDate(now()).toString();},
    construct(target,args,newTarget){return Reflect.construct(target,args.length?args:[now()],newTarget);},
    get(target,key,receiver){return key==='now'?now:Reflect.get(target,key,receiver);}
  });
  const sample=()=>{
    const performanceBeforeMs=nativeNow.call(nativePerformance),dateNowMs=Date.now(),newDateMs=new Date().getTime();
    const performanceAfterMs=nativeNow.call(nativePerformance);
    return {performanceBeforeMs,performanceAfterMs,dateNowMs,newDateMs,timeOriginMs:performance.timeOrigin,
      preserved:{Date:Date===DateOnly,performance:performance===nativePerformance,performanceNow:performance.now===nativeNow,
        timeOrigin:performance.timeOrigin===timeOriginMs,...Object.fromEntries(Object.entries(timers).map(([key,value])=>[key,window[key]===value]))}};
  };
  window.Date=DateOnly;
  Object.defineProperty(window,'__R0040_DATE_ONLY__',{value:Object.freeze({protocol:'r0040-date-only-installed/1',utcMs,anchorPerformanceMs,timeOriginMs,sample}),
    configurable:false,writable:false});
}

// Two startup rAF callbacks and one timer demonstrate clock progress only.
// They finish before the unchanged native capture starts its CDP stream.
async function observeNativeClock(){
  const witness=window.__R0040_DATE_ONLY__;
  if(!witness||witness.protocol!=='r0040-date-only-installed/1')throw Error('Date-only installer witness missing');
  const proof={protocol:'r0040-date-only-clock-proof/1',status:'COLLECTING',utcMs:witness.utcMs,
    anchorPerformanceMs:witness.anchorPerformanceMs,timeOriginMs:witness.timeOriginMs,
    before:witness.sample(),timer:null,frames:[],after:null,error:null};
  return new Promise(resolve=>{
    let done=false,frameHandle,timerHandle,deadlineHandle;
    const finish=(error=null)=>{
      if(done)return;done=true;
      clearTimeout(timerHandle);clearTimeout(deadlineHandle);cancelAnimationFrame(frameHandle);
      try{proof.after=witness.sample();}catch(fault){error||=fault;}
      proof.status=error?'INCOMPLETE':'COMPLETE';proof.error=error?{name:error.name,message:String(error.message)}:null;resolve(proof);
    };
    const complete=()=>{if(proof.timer&&proof.frames.length===2)finish();};
    const frame=timestampMs=>{
      if(done)return;
      try{proof.frames.push({timestampMs,sample:witness.sample()});
        if(proof.frames.length<2)frameHandle=requestAnimationFrame(frame);complete();}
      catch(error){finish(error);}
    };
    deadlineHandle=setTimeout(()=>finish(Error('native clock startup proof timed out')),5000);
    timerHandle=setTimeout(()=>{if(done)return;try{proof.timer={requestedDelayMs:40,sample:witness.sample()};complete();}catch(error){finish(error);}},40);
    frameHandle=requestAnimationFrame(frame);
  });
}

function admitClockProof(proof,utcMs){
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  need(proof&&proof.protocol==='r0040-date-only-clock-proof/1'&&proof.status==='COMPLETE'&&proof.error===null,'complete native clock proof required');
  need(Number.isSafeInteger(utcMs)&&proof.utcMs===utcMs&&finite(proof.anchorPerformanceMs)&&proof.anchorPerformanceMs>=0&&
    finite(proof.timeOriginMs)&&proof.timeOriginMs>0,'Date-only clock anchor mismatch');
  const preserved=['Date','performance','performanceNow','timeOrigin','setTimeout','clearTimeout','setInterval','clearInterval',
    'requestAnimationFrame','cancelAnimationFrame','queueMicrotask'].sort();
  function snapshot(sample){
    need(sample&&['performanceBeforeMs','performanceAfterMs','dateNowMs','newDateMs','timeOriginMs'].every(key=>finite(sample[key])),
      'complete finite native clock sample required');
    need(sample.timeOriginMs===proof.timeOriginMs&&sample.performanceBeforeMs>=proof.anchorPerformanceMs&&
      sample.performanceAfterMs>=sample.performanceBeforeMs,'native clock domain or ordering differs');
    need(sample.preserved&&isDeepStrictEqual(Object.keys(sample.preserved).sort(),preserved)&&
      Object.values(sample.preserved).every(value=>value===true),'native timer rAF performance or installed Date identity changed');
    for(const name of ['dateNowMs','newDateMs']){
      need(Number.isSafeInteger(sample[name])&&sample[name]>=utcMs+sample.performanceBeforeMs-proof.anchorPerformanceMs-1&&
        sample[name]<=utcMs+sample.performanceAfterMs-proof.anchorPerformanceMs,'Date does not advance 1x from its native clock anchor');
    }
  }
  snapshot(proof.before);snapshot(proof.after);
  need(proof.after.performanceBeforeMs>proof.before.performanceAfterMs,'native clock did not advance');
  need(proof.timer&&proof.timer.requestedDelayMs===40,'native startup timer did not complete');snapshot(proof.timer.sample);
  need(Array.isArray(proof.frames)&&proof.frames.length===2,'two startup rAF observations required');
  let previous=-1;
  for(const frame of proof.frames){snapshot(frame.sample);
    need(finite(frame.timestampMs)&&frame.timestampMs>=0&&frame.timestampMs>previous&&
      frame.timestampMs<=frame.sample.performanceAfterMs,'native rAF clock did not advance in its own domain');previous=frame.timestampMs;
  }
  for(const sample of [proof.timer.sample,...proof.frames.map(frame=>frame.sample)])
    need(sample.performanceBeforeMs>=proof.before.performanceAfterMs&&sample.performanceAfterMs<=proof.after.performanceBeforeMs,
      'startup callback lies outside its same-document observation interval');
  return {protocol:'r0040-date-only-clock-admission/1',status:'OBSERVED_NATIVE_TIMERS',utcMs,
    nativeTimersUnchanged:true,dateAdvancesAtNativeRate:true,sameDocumentClock:true,timerCompleted:true,rafCallbacks:2,
    scope:'Startup identity and progress only; no cadence or pixel qualification.'};
}

const ORIGINAL_SEAM="  await page.clock.install({time:new Date(o.utcMs)});if(o.clock==='paused')await page.clock.pauseAt(new Date(o.utcMs+1000));else await page.clock.resume();\r\n";
const replacement=()=>"  if(o.clock!=='running')throw Error('Date-only diagnostic requires a running scene');\r\n"+
  '  await page.addInitScript('+installDateOnly.toString()+',{utcMs:o.utcMs});\r\n';
function reverseHelper(source){
  const text=source.toString('utf8'),after=replacement();need(text.split(after).length===2,'unique Date-only reversal seam required');
  const original=Buffer.from(text.replace(after,()=>ORIGINAL_SEAM));need(sha(original)===ORIGINAL_SHA256,'Date-only reversal digest mismatch');return original;
}
function transformHelper(bytes){
  need(Buffer.isBuffer(bytes)&&bytes.length===17990&&sha(bytes)===ORIGINAL_SHA256,'original historical helper digest mismatch');
  const text=bytes.toString('utf8');need(text.split(ORIGINAL_SEAM).length===2,'unique original full-clock seam required');
  const source=Buffer.from(text.replace(ORIGINAL_SEAM,replacement));need(reverseHelper(source).equals(bytes),'historical helper did not reverse exactly');
  return {source,identity:{protocol:'r0040-date-only-helper/1',originalSha256:ORIGINAL_SHA256,transformedSha256:sha(source),
    installDateOnlySha256:sha(installDateOnly.toString()),originalRecoveredExactly:true,changedSeams:1,originalBytes:bytes.length,transformedBytes:source.length}};
}
function diagnosticIdentity(helper){
  return {protocol:'r0040-date-only-diagnostic/1',kind:'instrumented native-timer Date-only helper',entrySha256:sha(fs.readFileSync(__filename)),
    retentionSha256:RETENTION_SHA256,helper,originalDriverUnchanged:true,originalVerifierUnchanged:true,productAndRendererUnchanged:true,
    admissionScope:'Separate research diagnostic; original acquisition failure remains unchanged. The unchanged lossless verifier and all owner gates remain required.'};
}
function regular(file){
  const absolute=path.resolve(file);let current=absolute;
  while(true){need(!fs.lstatSync(current).isSymbolicLink(),'regular preparation custody path required');const parent=path.dirname(current);if(parent===current)break;current=parent;}
  need(fs.statSync(absolute).isFile(),'regular preparation custody file required');return fs.readFileSync(absolute);
}
function admitPreparationEntry(file,options,args){
  need(args.length===8,'eight unchanged capture arguments required');
  const bytes=regular(file),entry=JSON.parse(bytes),processBody=JSON.parse(regular(options.preparationProcess));
  need(entry.protocol==='r0040-capture-preparation-entry/1'&&Number.isInteger(entry.returncode)&&entry.returncode===0&&entry.timedOut===false&&
    (!Object.hasOwn(entry,'retentionError')||entry.retentionError===null),'successful actual outer preparation entry required');
  const preparer=path.join(__dirname,'r0040_capture_prepare.py');
  need(sha(regular(preparer))===PREPARER_SHA256&&entry.wrapperSha256===PREPARER_SHA256&&entry.timeoutSeconds===240&&entry.cwd===__dirname,
    'actual preparation entry source or cwd differs');
  const inputs=processBody.inputs,research=path.resolve(path.dirname(options.driver),'../../..');
  need(inputs&&inputs.manifest===path.resolve(options.manifest)&&inputs.research===research&&inputs.main===path.resolve(args[2])&&
    path.resolve(inputs.out,'historical')===path.resolve(args[1])&&path.resolve(inputs.out,'receipts/prepared.json')===path.resolve(options.prepared),
    'outer preparation inputs differ from actual capture');
  need(Array.isArray(entry.argv)&&typeof entry.argv[0]==='string'&&path.isAbsolute(entry.argv[0])&&
    isDeepStrictEqual(entry.argv,[entry.argv[0],preparer,'--manifest',inputs.manifest,'--research',inputs.research,
      '--historical',inputs.historical,'--main',inputs.main,'--out',inputs.out,'--receipts',path.dirname(path.resolve(options.preparationProcess))]),
    'actual preparation entry argv differs');
  return {path:path.resolve(file),sha256:sha(bytes),actualExitCode:0};
}

class DateOnlyRetention extends R.CaptureRetention {
  constructor(directory,{diagnostic,proofTimeoutMs=15000,...options}){
    super(directory,options);this.diagnostic=diagnostic;this.clockProofs=[];this.proofTimeoutMs=proofTimeoutMs;
    const record=this.journal.record.bind(this.journal);
    this.journal.record=(event,value={})=>{
      if(event==='driver-process-ended'){
        value.diagnostic=this.diagnostic;value.clockProofs=this.clockProofs;value.timingClass='instrumented-date-only-clock';
        if(value.status==='ADMITTED_FOR_OFFLINE_VERIFICATION')value.status=ADMITTED;
      }
      return record(event,value);
    };
    this.record('date-only-instrumentation',{diagnostic,overhead:'Date reads use the native performance clock; one startup timer/two-rAF observation precedes capture. Existing host retention adds serialization/fsync. No added CDP frame listener, per-frame copies or per-frame fsync. Instrumented timing is not original performance.'});
  }
  wrapContext(raw){
    const context=super.wrapContext(raw);this.acquiredContext=context;return context;
  }
  wrapHelper(raw){
    const wrapped=super.wrapHelper(raw);
    return new Proxy(wrapped,{get:(target,key)=>{
      if(key!=='openScene')return target[key];
      return async(...args)=>{
        let scene,watchdog,observation;
        try{
          scene=await target.openScene(...args);
          let rawProof;
          try{
            rawProof=await Promise.race([scene.page.evaluate(observeNativeClock),new Promise((_,reject)=>{
              watchdog=setTimeout(()=>reject(Error('Date-only startup evaluation timed out')),this.proofTimeoutMs);})]);
          }finally{clearTimeout(watchdog);}
          observation={status:'INCOMPLETE',raw:rawProof,admission:null,error:null};this.clockProofs.push(observation);
          try{observation.admission=admitClockProof(rawProof,args[3].utcMs);observation.status='OBSERVED';}
          catch(error){observation.error=errorData(error);throw error;}
          finally{this.record('date-only-clock-proof',{proof:observation});}
          if(this.journal.retentionError)throw this.journal.retentionError;
          return scene;
        }catch(error){
          if(this.acquiredContext&&!observation){observation={status:'UNAVAILABLE',raw:null,admission:null,error:errorData(error)};this.clockProofs.push(observation);
            this.record('date-only-clock-proof',{proof:observation});}
          this.failure('date-only-open-threw',error);
          // capture.cjs assigns ctx only after openScene returns. A failure in
          // the added installer/proof must close the acquired context here.
          const context=scene?.ctx||this.acquiredContext;
          if(context&&!this.closes.context.called)try{await context.close();}
          catch(cleanupError){this.failure('date-only-context-cleanup-threw',cleanupError,{primary:errorData(error)});}
          throw error;
        }
      };
    }});
  }
  finalize(originalExitCode,stderr){
    if(!this.finalized)try{
      need(this.clockProofs.length===1&&this.clockProofs[0].status==='OBSERVED','complete Date-only startup proof required');
      need(isDeepStrictEqual(this.clockProofs[0].admission,admitClockProof(this.clockProofs[0].raw,this.expected.utcMs)),'clock admission differs from retained raw proof');
    }catch(error){this.failure('date-only-terminal-proof-failed',error);}
    return super.finalize(originalExitCode,stderr);
  }
}

function executeOriginal(driver,args,retain,load=Module.createRequire(path.resolve(driver))){
  const helper=path.resolve(args[1],'tools/qa/precip_eval_lib.cjs');
  return R.executeOriginal(driver,args,retain,request=>{
    if(request!==helper)return load(request);
    const transformed=transformHelper(regular(helper));need(isDeepStrictEqual(transformed.identity,retain.diagnostic.helper),'admitted Date-only helper identity differs');
    const mod=new Module(helper,module);mod.filename=helper;mod.paths=Module._nodeModulePaths(path.dirname(helper));mod.require=load;
    mod._compile(transformed.source.toString('utf8'),helper);return mod.exports;
  });
}
function runDriver(options,args){
  // The original helper/driver and browser module cannot import before these.
  const isolation=R.verifyIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);
  const admission=R.verifySources(options,args);need(path.resolve(process.cwd())===admission.research,'immutable research cwd required');
  const preparationEntry=admitPreparationEntry(options.preparationEntry,options,args);
  const transformed=transformHelper(regular(path.join(args[1],'tools/qa/precip_eval_lib.cjs'))),diagnostic=diagnosticIdentity(transformed.identity);
  process.umask(0o077);
  const retain=new DateOnlyRetention(options.evidence,{out:args[3],expected:admission.manifest.plannedNativeCell.expectedCapture,pins:admission.manifest.pins,diagnostic});
  retain.record('sources',{isolation,...admission.custody,preparationEntry,sources:admission.sources,originalArgv:args,diagnostic});
  if(retain.journal.retentionError)throw retain.journal.retentionError;
  return executeOriginal(options.driver,args,retain);
}
if(require.main===module){
  const args=process.argv.slice(2),separator=args.indexOf('--');
  need(separator===12&&args[0]==='--driver'&&args[2]==='--manifest'&&args[4]==='--prepared'&&args[6]==='--preparation-process'&&
    args[8]==='--preparation-entry'&&args[10]==='--evidence',
    'usage: r0040_dateonly.cjs --driver ORIGINAL --manifest MANIFEST --prepared ORIGINAL_RECEIPT --preparation-process PROCESS --preparation-entry ENTRY --evidence NEW_PRIVATE_DIR -- PLAYWRIGHT HISTORICAL MAIN NEW_OUT chromium bday moderate M1');
  runDriver({driver:args[1],manifest:args[3],prepared:args[5],preparationProcess:args[7],preparationEntry:args[9],evidence:args[11]},args.slice(separator+1));
}
module.exports={ORIGINAL_SHA256,ADMITTED,installDateOnly,observeNativeClock,admitClockProof,transformHelper,reverseHelper,diagnosticIdentity,
  admitPreparationEntry,DateOnlyRetention,executeOriginal,runDriver};
