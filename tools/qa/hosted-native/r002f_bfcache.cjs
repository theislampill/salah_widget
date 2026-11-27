'use strict';
// One task-owned pair. Original witness bodies are never rewritten and a failed arm stops the pair.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const S=require('./r002f_bfcache_source.cjs'),A=require('./r002f_bfcache_preload.cjs'),R=require('./r002f_bfcache_replay.cjs'),T=require('./r002f_tabhide.cjs'),{need}=S;
const ID='r002f-bfcache-chromium-dpr1',RESULT='r002f-bfcache-pair/1';
const NORMAL_PHASES=Object.freeze(Object.keys(A.PHASES).filter(x=>!['failureCleanup','reserve'].includes(x)));
function childArgv(node,root,out,label){need(['baseline','candidate'].includes(label),'original arm label required');return [node,'--require',path.join(__dirname,'r002f_bfcache_preload.cjs'),
  path.join(S.ORIGINAL,'real-witness.cjs'),root,out,'chromium','bfcache',S.CLOCK,'3','--label='+label];}
async function runChild(argv,folder,label,seconds,env,{phases=false,streamBytes=1024**2}={}){
  need(seconds>0&&streamBytes>0&&/^[a-z0-9-]+$/.test(label),'bounded child arguments required');S.noSymlinks(folder);
  const started=process.hrtime.bigint(),state={protocol:'r002f-bfcache-actual-process/1',argv,cwd:__dirname,timeoutSeconds:seconds,
    returncode:null,timedOut:false,overflow:false,signals:[],phases:[],complete:false,streamLimit:streamBytes,
    observedBytes:{stdout:0,stderr:0},acknowledgedBytes:{stdout:0,stderr:0},retainedBytes:{stdout:null,stderr:null},retentionErrors:{},streamsClosed:{},streams:{}};
  const files={};for(const key of ['stdout','stderr'])files[key]=fs.openSync(path.join(folder,label+'.'+key),'wx',0o600);
  let child,overall,stage,killTimer,closed=false,phaseIndex=-1,stopping=false;
  function signal(sig){try{process.kill(-child.pid,sig);state.signals.push(sig);}catch(error){if(error.code!=='ESRCH')state.signalError=String(error);}}
  function stop(reason){state.error=state.error||reason;if(stopping||closed)return;stopping=true;signal('SIGTERM');killTimer=setTimeout(()=>signal('SIGKILL'),2000);}
  try{
    child=cp.spawn(argv[0],argv.slice(1),{cwd:__dirname,env,detached:true,stdio:['ignore','pipe','pipe',...(phases?['ipc']:[])]});state.pid=child.pid??null;
    overall=setTimeout(()=>{state.timedOut=true;stop('aggregate child deadline exceeded');},seconds*1000);
    if(phases)stage=setTimeout(()=>{state.timedOut=true;stop('preload admission phase deadline exceeded');},A.PHASES.admission*1000);
    child.on('message',message=>{try{need(message?.protocol==='r002f-bfcache-phase/1'&&typeof message.phase==='string'&&message.seconds===A.PHASES[message.phase],
        'unknown or altered phase message');const index=Object.keys(A.PHASES).indexOf(message.phase);need(index>phaseIndex,'repeated or reversed phase');phaseIndex=index;
      state.phases.push({...message,parentReceivedNs:process.hrtime.bigint().toString()});
      if(message.phase!=='admission'){clearTimeout(stage);stage=setTimeout(()=>{state.timedOut=true;stop('phase deadline exceeded: '+message.phase);},message.seconds*1000);}
    }catch(error){stop(String(error.message||error));}});
    for(const key of ['stdout','stderr'])child[key].on('data',data=>{const available=Math.max(0,streamBytes-state.acknowledgedBytes[key]);state.observedBytes[key]+=data.length;
      if(available&&!state.retentionErrors[key]){const written=S.writeOnce(files[key],data.subarray(0,available));state.acknowledgedBytes[key]+=written.acknowledgedBytes;
        if(written.error){state.retentionErrors[key]=written.error;stop('child '+key+' retention failed: '+written.error);}}
      if(data.length>available){state.overflow=true;stop('child stream retention bound exceeded');}});
    await new Promise(resolve=>{child.on('error',error=>{state.error=String(error.stack||error);});child.on('close',(code,signal)=>{state.returncode=code;state.signal=signal;closed=true;resolve();});});
    if(Number.isInteger(child.pid)&&child.pid>0){try{process.kill(-child.pid,0);state.survivingGroupAtReturn=true;signal('SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}
    if(state.survivingGroupAtReturn){await new Promise(resolve=>setTimeout(resolve,20));try{process.kill(-child.pid,0);state.groupStopped=false;}catch(error){state.groupStopped=error.code==='ESRCH';}}
    else state.groupStopped=true;}else state.groupStopped=null;
  }catch(error){state.error=state.error||String(error.stack||error);if(child&&!closed&&Number.isInteger(child.pid))signal('SIGKILL');}
  finally{clearTimeout(overall);clearTimeout(stage);clearTimeout(killTimer);
    for(const [key,fd] of Object.entries(files)){const final=S.finishFile(fd,path.join(folder,label+'.'+key));state.streamsClosed[key]=final.closed;
      if(final.identity){state.streams[key]=final.identity;state.retainedBytes[key]=final.identity.bytes;}
      if(final.error)state.retentionErrors[key]=state.retentionErrors[key]||final.error;
      try{S.admitRetained(final.identity,state.observedBytes[key],state.acknowledgedBytes[key],state.retainedBytes[key],streamBytes);}
      catch(error){state.retentionErrors[key]=state.retentionErrors[key]||String(error);}}
    state.elapsedSeconds=Number(process.hrtime.bigint()-started)/1e9;}
  if(Object.keys(state.retentionErrors).length)state.error=state.error||'child stream retention incomplete';
  state.complete=state.returncode===0&&!state.timedOut&&!state.overflow&&!state.error&&state.groupStopped===true&&!state.survivingGroupAtReturn&&Object.values(state.streamsClosed).every(x=>x===true);
  if(phases&&state.complete&&!S.same(state.phases.map(x=>x.phase),NORMAL_PHASES)){state.complete=false;state.error='complete original child phase population missing';}
  S.writeJson(path.join(folder,label+'-process.json'),state);return state;}
function admitProcessRetention(row,limit=1024**2){need(row?.protocol==='r002f-bfcache-actual-process/1'&&row.complete===true&&row.streamLimit===limit&&
  row.retentionErrors&&Object.keys(row.retentionErrors).length===0,'actual child stream retention incomplete');
  for(const key of ['stdout','stderr']){need(row.streamsClosed?.[key]===true,'actual child stream was not closed');
    S.admitRetained(row.streams?.[key],row.observedBytes?.[key],row.acknowledgedBytes?.[key],row.retainedBytes?.[key],limit);}return true;}
function population(folder){S.noSymlinks(folder);const files={};let png=0,video=0,metadata=0;
  function visit(relative){for(const name of fs.readdirSync(path.join(folder,relative)).sort()){const item=path.join(relative,name),file=path.join(folder,item),st=fs.lstatSync(file);need(!st.isSymbolicLink(),'symlink in retained arm');
      if(st.isDirectory()){need(!name.startsWith('.video-'),'original recorder directory survived cleanup');visit(item);}else{const row=S.record(file);files[item]=row;
        if(name.endsWith('.png')){S.pngInfo(fs.readFileSync(file));png+=row.bytes;}else if(name.endsWith('.webm'))video+=row.bytes;else metadata+=row.bytes;}}}
  visit('');need(Object.keys(files).length<=1024&&png<=S.LIMITS.pngPopulationBytes+5*S.LIMITS.pngBytes&&video<=S.LIMITS.videoBytes&&metadata<=S.LIMITS.metadataBytes,
    'complete retained arm storage population exceeds declared ceilings');return {files,bytes:{png,video,metadata,total:png+video+metadata}};}
function admitAdapter(adapter,tools,processRecord){need(adapter.protocol==='r002f-bfcache-adapter/1'&&adapter.status==='COMPLETE'&&adapter.errors?.length===0&&!adapter.errorOverflow&&!adapter.isolationFailure&&
  adapter.originalExitRequested===0&&adapter.host?.pid===processRecord.pid&&Object.values(adapter.cleanup||{}).length===6&&Object.values(adapter.cleanup).every(x=>x===true),'independent adapter closure incomplete');
  for(const [key,value] of Object.entries(S.DISCLOSURE))need(S.same(adapter[key],value),'adapter launch/timing disclosure differs');
  const binary=tools.acquired.managed.chromium,originalOwner=A.owner(adapter.beforeCensus,adapter.afterLaunchCensus,adapter.host,binary);need(S.same(originalOwner,adapter.owner),'actual browser owner differs');
  A.admitCensus(adapter.finalCensus,binary);need(adapter.finalCensus.rows.length===0,'managed browser survivor remains');
  function ownedProcess(row,tool){need(Number.isInteger(row?.pid)&&row.pid>0&&typeof row.startTicks==='string'&&/^[1-9]\d*$/.test(row.startTicks)&&
    row.exe===tool.resolvedPath&&row.sha256===tool.sha256&&row.uid===adapter.host.uid&&row.netns===adapter.host.netns&&row.pidns===adapter.host.pidns,
    'actual executable process owner identity differs');}
  function lifecycle(life,kind){need(life?.protocol==='r002f-process-lifecycle/1'&&life.kind===kind&&life.cleanupRequested===true&&life.closed===true&&life.faults?.length===0&&life.overflow===false,'prior lifecycle fault or incomplete close');}
  for(const key of ['browser','context','page'])lifecycle(adapter[key+'Lifecycle'],key);
  lifecycle(adapter.display?.lifecycle,'display');
  ownedProcess(adapter.display.process,tools.tools.xvfb);
  need(adapter.display?.stopped===true&&adapter.display.process?.sha256===tools.tools.xvfb.sha256&&adapter.display.process.uid===adapter.host.uid&&
    adapter.display.process.netns===adapter.host.netns&&adapter.display.process.pidns===adapter.host.pidns&&adapter.display.cleanup?.stopped===true,
    'actual display custody differs');
  const displayArgs=[tools.tools.xvfb.path,'-displayfd','3','-screen','0','1024x768x24','-nolisten','tcp','-noreset','-ac'];
  need(S.same(adapter.display.argv,displayArgs)&&S.same(adapter.display.process.argv,displayArgs),'actual display arguments differ');
  const proxy={server:'http://127.0.0.1:'+adapter.loopbackPorts?.proxy,bypass:'<-loopback>'};
  need(Number.isInteger(adapter.loopbackPorts?.proxy)&&S.same(adapter.originalLaunch,A.expectedLaunch(proxy))&&S.same(adapter.directContexts,{before:2,after:2}),
    'actual launch or direct boundary context population differs');
  const env={...adapter.adaptedLaunch?.env};delete env.DISPLAY;
  need(Object.keys(env).every(k=>['PATH','LANG','LC_ALL','TZ','TMPDIR','TMP','TEMP','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_RUNTIME_DIR'].includes(k))&&
    S.same(adapter.adaptedLaunch,A.launchOptions(adapter.originalLaunch,{proxy,executable:binary.path,display:adapter.display.display,env})),
    'actual adapted launch contract differs');
  const b={...adapter.host,browserPid:adapter.owner.pid,executableSha256:binary.sha256},original=require('./r002f_tabhide_source.cjs');original.boundary(adapter.boundaries?.before,b);original.boundary(adapter.boundaries?.after,b);
  need(adapter.recorders?.length===1&&adapter.recorders[0].closed===true&&adapter.recorders[0].returncode===0&&!adapter.recorders[0].error&&
    adapter.recorders[0].process?.sha256===tools.acquired.managed.recorder.sha256&&adapter.recorders[0].process.uid===adapter.host.uid&&
    adapter.recorders[0].process.netns===adapter.host.netns&&adapter.recorders[0].process.pidns===adapter.host.pidns,'actual recorder custody incomplete');
  lifecycle(adapter.recorders[0].lifecycle,'recorder');
  ownedProcess(adapter.recorders[0].process,tools.acquired.managed.recorder);
  const recorder=adapter.recorders[0],recordedArgv=[tools.acquired.managed.recorder.path,...A.recorderArguments(recorder.output)];
  need(S.same(recorder.argv,recordedArgv)&&S.same(recorder.process.argv,recordedArgv)&&recorder.pid===recorder.process.pid,'actual recorder arguments differ');
  const copy=adapter.recorderCopy;need(copy&&copy.original.sha256===copy.retained.sha256&&copy.original.bytes===copy.retained.bytes,'original recorder/final copy equality missing');
  S.requireRecord(copy.retained);S.requireRecord(adapter.config);S.requireRecord(adapter.tools);S.requireRecord(adapter.isolation);
  const config=S.readJson(adapter.config.path).value;A.admitJournal(adapter.journal);
  need(adapter.journal.identity.path===path.join(config.out,'adapter-events.jsonl'),'literal adapter event journal differs');
  const events=fs.readFileSync(adapter.journal.identity.path,'utf8').trimEnd().split('\n').map(line=>JSON.parse(line));
  need(events.length===adapter.journal.events&&S.same(events.filter(row=>row.type==='phase'),adapter.phases),'retained adapter journal event/phase population differs');
  need(adapter.label===config.label&&adapter.actualVideoPath===recorder.output&&copy.original.path===recorder.output&&
    path.dirname(recorder.output)===path.join(config.out,'.video-'+config.label)&&copy.retained.path===path.join(config.out,config.label+'.webm')&&
    S.same(adapter.phases.map(x=>({phase:x.phase,seconds:x.seconds})),processRecord.phases.map(x=>({phase:x.phase,seconds:x.seconds}))),
    'literal recorder, adapter configuration or phase population differs');
  original.owners().validateIsolation(S.readJson(adapter.isolation.path).value,adapter.host);return true;}
function admitArm(task,folder,label,tools,expected){
  const processRecord=S.readJson(path.join(folder,'witness-process.json')),p=processRecord.value;
  need(p.complete===true&&p.returncode===0&&p.timedOut===false&&p.timeoutSeconds===1680&&p.cwd===__dirname&&S.same(p.argv,childArgv(expected.runtime.node,expected.r002f.trees[label].root,folder,label))&&
    S.same(p.phases.map(x=>x.phase),NORMAL_PHASES),'actual original child completion or invocation differs');admitProcessRetention(p);
  const adapter=S.readJson(path.join(folder,'adapter.json'));admitAdapter(adapter.value,tools,p);
  const retained=R.population(folder,label),original=retained.body;need(original.valid===true&&original.void.length===0,'original witness is VOID');
  const decoded=S.readJson(path.join(folder,'original-decoder-process.json'));R.admitDecoded(decoded.value);
  const replay=S.readJson(path.join(folder,'replay/replay.json'));need(replay.value.protocol==='r002f-bfcache-replay/1'&&replay.value.status==='COMPLETE'&&
    replay.value.originalReport.sha256===retained.native.identity.sha256&&replay.value.retention.sha256===retained.retained.identity.sha256&&
    replay.value.valid===original.valid&&replay.value.verdict===original.verdict&&S.same(replay.value.judged,original.judged)&&
    replay.value.fullPopulation.screenshotReturns===retained.retained.value.received,'original full replay report differs');
  R.admitDecoded(replay.value.decoder);S.currentRecords(replay.value);
  const video=S.record(path.join(folder,label+'.webm'));
  need(S.same(decoded.value.input,video)&&decoded.value.timeoutSeconds===120&&decoded.value.frames===original.video.frames&&
    S.same(decoded.value.argv,[tools.tools.decoder.path,'-v','error','-i',video.path,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'])&&
    decoded.value.rgbSha256===replay.value.decoder.rgbSha256&&decoded.value.bytes===replay.value.decoder.bytes,
    'original/replayed complete RGB population or invocation differs');
  S.currentRecords(decoded.value.stderr);
  for(const label of ['current-before','current-after']){
    const currentProcess=S.readJson(path.join(folder,label+'-process.json')).value,currentFile=path.join(folder,label+'.json');
    need(currentProcess.complete===true&&currentProcess.returncode===0&&currentProcess.timedOut===false&&currentProcess.timeoutSeconds===60&&
      currentProcess.cwd===__dirname&&currentProcess.groupStopped===true&&!currentProcess.overflow&&!currentProcess.error&&
      S.same(currentProcess.argv,[expected.runtime.python,'-B',path.join(__dirname,'r002f_bfcache_central.py'),'admit','--task',task,'--native','--output',currentFile]),
      'actual per-arm currentness process differs');admitProcessRetention(currentProcess);
    need(S.same(S.readJson(currentFile).value,expected)&&S.same(JSON.parse(fs.readFileSync(currentProcess.streams.stdout.path)),expected),
      'actual per-arm source admission differs');}
  const replayProcess=S.readJson(path.join(folder,'replay-process.json')).value;
  need(replayProcess.complete===true&&replayProcess.returncode===0&&replayProcess.timedOut===false&&replayProcess.timeoutSeconds===210&&
    replayProcess.cwd===__dirname&&replayProcess.groupStopped===true&&!replayProcess.overflow&&!replayProcess.error&&
    S.same(replayProcess.argv,[expected.runtime.node,path.join(__dirname,'r002f_bfcache_replay.cjs'),folder,label,
      path.join(task,'capture/r002f-bfcache-tools/receipt.json'),path.join(folder,'replay')]),'actual full replay process differs');admitProcessRetention(replayProcess);
  const first=tag=>retained.retained.value.frames.find(row=>row.tag===tag);
  for(const [file,tag] of [[label+'-ref-present.png','ref-present'],[label+'-ref-absent.png','ref-absent'],...[1,2,3].map(k=>[label+'-restore'+k+'-first-shot.png','restore-'+k])]){
    const r=S.record(path.join(folder,file));need(r.sha256===first(tag)?.identity.sha256&&r.bytes===first(tag).identity.bytes,'original legacy retained PNG differs from returned population');}
  const config=S.readJson(adapter.value.config.path).value;need(config.task===task&&config.out===folder&&config.label===label&&config.root===expected.r002f.trees[label].root&&
    S.same(config.sources,expected.sources)&&S.same(config.generated,expected.generated[label])&&S.same(config.runtime,expected.runtime),'actual child configuration differs');
  return {label,status:'COMPLETE',originalValid:original.valid,originalVerdict:original.verdict,original:retained.native.identity,retention:retained.retained.identity,
    process:processRecord.identity,adapter:adapter.identity,decoder:decoded.identity,replay:replay.identity,population:population(folder)};}
function parse(argv){const admit=argv[0]==='--admit',args=admit?argv.slice(1):argv;
  need(args.length===4&&args[0]==='--task'&&args[2]==='--out','exact paired task/output arguments required');const task=args[1],out=args[3];
  need(path.isAbsolute(task)&&path.resolve(task)===task&&out===path.join(task,'capture/lanes',ID),'literal current task/output required');S.noSymlinks(task);return {admit,task,out};}
async function current(task,folder,label,runtime,native=true){const file=path.join(folder,label+'.json'),argv=[runtime.python,'-B',path.join(__dirname,'r002f_bfcache_central.py'),'admit','--task',task,...(native?['--native']:[]),'--output',file];
  const processRecord=await runChild(argv,folder,label,60,process.env);need(processRecord.complete,'actual current preparation refused');admitProcessRetention(processRecord);
  const admission=S.readJson(file);need(admission.value.status==='PASS'&&admission.value.native===true&&admission.value.task===task,'native complete preparation missing');return admission;}
function childEnvironment(runtime,config,isolation){const result={...process.env,PLAYWRIGHT_PKG:runtime.playwright,R002F_BFCACHE_CHILD:config,SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT:isolation};A.cleanChildEnvironment(result);return result;}
async function main(argv){const options=parse(argv);if(options.admit)return admitPair(options.task,options.out);
  const {task,out}=options,runtime=S.readJson(path.join(task,'runtime.json')).value,toolsPath=path.join(task,'capture/r002f-bfcache-tools/receipt.json'),toolRead=S.readJson(toolsPath),tools=toolRead.value;
  need(tools.protocol==='r002f-bfcache-tools/1'&&tools.status==='COMPLETE'&&S.same(runtime,tools.acquired.runtime)&&process.execPath===runtime.node,'actual acquired runtime/tool authority differs');S.currentRecords(tools);
  need(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT===path.join(task,'capture/isolation',ID,'receipt.json'),'actual lane isolation authority required');
  S.freshDirectory(out);const report={protocol:RESULT,status:'INCOMPLETE',...S.DISCLOSURE,nativeQualification:S.QUALIFICATION,humanAcceptance:'OUTSTANDING',
    task,tools:toolRead.identity,runtime,arms:[],errors:[],originalFailures:'UNCHANGED',budgets:{childSeconds:1680,armSeconds:2040,pairSeconds:4200},
    limitations:['Moon-only original persisted-return witness; no expiry/renewal or held-state policy decision.',
      'No performance equivalence, first physical frame, randomized causal arm comparison, independent display cadence or human acceptance.']};
  const begun=process.hrtime.bigint();
  try{for(const label of ['baseline','candidate']){need(Number(process.hrtime.bigint()-begun)/1e9<4080,'paired operational deadline exhausted');const started=process.hrtime.bigint(),folder=S.freshDirectory(path.join(out,label));
      const before=await current(task,folder,'current-before',runtime);const admission=before.value;
      if(report.sourceAdmission)need(S.same(report.sourceAdmission,admission),'pair source admission changed');else report.sourceAdmission=admission;
      const config={protocol:'r002f-bfcache-child-config/1',native:true,task,label,root:admission.r002f.trees[label].root,out:folder,runtime,
        toolsPath,isolationFile:process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT,sources:admission.sources,generated:admission.generated[label]};
      const configPath=path.join(folder,'child-config.json');S.writeJson(configPath,config);
      const child=await runChild(childArgv(runtime.node,config.root,folder,label),folder,'witness',1680,childEnvironment(runtime,configPath,config.isolationFile),{phases:true});
      const adapterFile=path.join(folder,'adapter.json'),adapter=fs.existsSync(adapterFile)?S.readJson(adapterFile):null;
      if(!child.complete){report.arms.push({label,status:'INCOMPLETE',process:S.record(path.join(folder,'witness-process.json')),...(adapter?{adapter:adapter.identity}:{})});
        throw Object.assign(Error('actual original arm did not complete: '+label),{isolation:adapter?.value.isolationFailure===true});}
      need(adapter,'independent adapter receipt missing');if(adapter.value.isolationFailure)throw Object.assign(Error('actual original arm isolation failed'),{isolation:true});admitAdapter(adapter.value,tools,child);
      const replayArgv=[runtime.node,path.join(__dirname,'r002f_bfcache_replay.cjs'),folder,label,toolsPath,path.join(folder,'replay')];
      const replay=await runChild(replayArgv,folder,'replay',210,process.env);need(replay.complete,'actual full original replay incomplete');
      const after=await current(task,folder,'current-after',runtime);need(S.same(after.value,admission),'source currentness changed after original arm');
      const arm=admitArm(task,folder,label,tools,admission);need(Number(process.hrtime.bigint()-started)/1e9<=2040,'per-arm operational ceiling exceeded');report.arms.push(arm);
    }
    need(report.arms.length===2&&Number(process.hrtime.bigint()-begun)/1e9<=4200,'complete sequential pair deadline differs');report.status=S.STATUS;
  }catch(error){report.errors.push(String(error.stack||error));if(error.isolation)report.status='ISOLATION_FAIL';}
  report.elapsedSeconds=Number(process.hrtime.bigint()-begun)/1e9;S.writeJson(path.join(out,'result.json'),report);
  console.log(JSON.stringify({protocol:RESULT,status:report.status,originalArms:report.arms.map(x=>({label:x.label,valid:x.originalValid,verdict:x.originalVerdict}))}));
  return {status:report.status,code:report.status===S.STATUS?0:report.status==='ISOLATION_FAIL'?86:2};}
function admitPair(task,out){const pair=S.readJson(path.join(out,'result.json')),body=pair.value,toolsRead=S.readJson(path.join(task,'capture/r002f-bfcache-tools/receipt.json')),tools=toolsRead.value;
  need(body.protocol===RESULT&&body.status===S.STATUS&&body.task===task&&body.errors?.length===0&&body.nativeQualification===S.QUALIFICATION&&body.humanAcceptance==='OUTSTANDING'&&
    body.elapsedSeconds>=0&&body.elapsedSeconds<=4200&&body.arms?.length===2&&S.same(body.arms.map(x=>x.label),['baseline','candidate']),'paired actual diagnostic incomplete');
  for(const [key,value] of Object.entries(S.DISCLOSURE))need(S.same(body[key],value),'pair disclosure differs');S.requireRecord(body.tools);S.currentRecords(tools);
  need(S.same(body.tools,toolsRead.identity)&&S.same(body.runtime,tools.acquired.runtime),'pair actual runtime/tool identity differs');
  need(body.sourceAdmission?.protocol==='r002f-bfcache-source-admission/1'&&body.sourceAdmission.status==='PASS'&&body.sourceAdmission.native===true&&
    body.sourceAdmission.task===task&&S.same(body.sourceAdmission.sources,tools.sources),'paired native source admission differs');
  for(const label of ['baseline','candidate'])A.admitChildSources({label,root:body.sourceAdmission.r002f.trees[label].root,
    sources:body.sourceAdmission.sources,generated:body.sourceAdmission.generated[label]});
  const arms=[];for(const label of ['baseline','candidate']){const actual=admitArm(task,path.join(out,label),label,tools,body.sourceAdmission);
    need(S.same(actual,body.arms.find(x=>x.label===label)),'complete retained arm population changed');arms.push({label,valid:actual.originalValid,verdict:actual.originalVerdict,populationFiles:Object.keys(actual.population.files).length});}
  return {protocol:'r002f-bfcache-final-intake/1',status:'COMPLETE',pair:pair.identity,arms,nativeQualification:S.QUALIFICATION,humanAcceptance:'OUTSTANDING'};}
module.exports={ID,RESULT,NORMAL_PHASES,childArgv,runChild,admitProcessRetention,population,admitAdapter,admitArm,parse,current,childEnvironment,main,admitPair};
if(require.main===module)main(process.argv.slice(2)).then(value=>{if(value.protocol)console.log(JSON.stringify(value));if(value.code)process.exitCode=value.code;})
  .catch(error=>{console.error(error.stack||error);process.exitCode=2;});
