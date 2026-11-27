'use strict';
// Re-execute the exact pinned scientific body. Additional gates describe custody/completeness only.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process'),crypto=require('node:crypto'),{createRequire}=require('node:module');
const S=require('./r002f_bfcache_source.cjs'),{need}=S;
function judgment({out,shots,refs,videoPath,outDir,filesystem,spawn,decode}){
  const {text,rows}=S.originalText(),first=S.unique(text,'(async()=>{'),start=S.unique(text,'  try{\n    // ---- lifecycle validity'),
    end=S.unique(text,'  fs.rmSync(videoDir,{recursive:true,force:true});'),verdict=S.unique(text,'  out.valid=out.void.length===0;'),
    publish=S.unique(text,'  fs.writeFileSync(path.join(outDir,LABEL+\'.json\'),JSON.stringify(slim,null,1));');
  const originalRequire=createRequire(rows['real-witness.cjs'].path),requireControlled=name=>name==='node:fs'?filesystem:name==='node:child_process'?{spawn}:originalRequire(name);
  const context={require:requireControlled,process:{argv:['node',rows['real-witness.cjs'].path,'/retained-original-root',outDir,'chromium','bfcache',S.CLOCK,'3','--label='+out.label]},Buffer,Uint8Array,console};
  // The inner binding permits a disclosed source-only fixture. Native replay always invokes originalDecodeVideo.
  const code=text.slice(0,first)+'\nconst originalDecodeVideo=decodeVideo;\n(async function(out,shots,refs,videoPath,sourceOnlyDecode){\nconst decodeVideo=sourceOnlyDecode||originalDecodeVideo;\n'
    +text.slice(start,end)+text.slice(verdict,publish)+'\nreturn {full:out,slim};\n})';
  const fn=vm.runInNewContext(code,context,{filename:rows['real-witness.cjs'].path,timeout:1000});
  return fn(out,shots,refs,videoPath,decode);
}
async function sourceControl(input){need(input?.scope==='SOURCE_CONTROL_ONLY','synthetic fixture disclosure required');
  const out=structuredClone(input.out),dir='/source-control-output',videoPath=dir+'/baseline.webm',bytes=Buffer.from('synthetic-video-placeholder-not-native');
  const filesystem={existsSync:file=>file===videoPath,copyFileSync:(from,to)=>need(from===videoPath&&to===videoPath,'source fixture copy path differs'),
    statSync:file=>{need(file===videoPath,'source fixture stat path differs');return {size:bytes.length};},
    readFileSync:file=>{need(file===videoPath,'source fixture read path differs');return bytes;}};
  const result=await judgment({out,shots:input.shots,refs:input.refs,videoPath,outDir:dir,filesystem,spawn:()=>{throw Error('source fixture must not spawn decoder');},decode:async()=>input.video});
  return {...result,scope:'SOURCE_CONTROL_ONLY',nativeObservation:false};
}
function compareReport(actual,replayed){need(S.same(actual,replayed),'complete original report differs from exact-body replay');return true;}
function admitDecoded(row){need(Number.isInteger(row?.returncode)&&row.returncode===0&&row.timedOut===false&&!row.error&&
  Number.isSafeInteger(row.bytes)&&row.bytes>0&&row.bytes%S.LIMITS.frameRgbBytes===0&&row.frames===row.bytes/S.LIMITS.frameRgbBytes&&row.frames<=S.LIMITS.decodeFrames&&
  typeof row.rgbSha256==='string'&&/^[a-f0-9]{64}$/.test(row.rgbSha256)&&row.mappingsComplete===true&&row.stderrClosed===true&&!row.stderrRetentionError,
    'original decoder process, full RGB population or mapping custody incomplete');
  S.admitRetained(row.stderr,row.stderrBytes,row.stderrAcknowledgedBytes,row.stderrRetainedBytes,65536);return true;}
function mappedFiles(pid){const file='/proc/'+pid+'/maps',bytes=fs.readFileSync(file);need(bytes.length<=2*1024**2,'decoder mappings bound exceeded');const paths=new Set();
  for(const line of bytes.toString('utf8').trim().split('\n')){const m=/^[\da-f]+-[\da-f]+\s+\S+\s+[\da-f]+\s+[\da-f]+:[\da-f]+\s+(\d+)\s*(.*)$/.exec(line);need(m,'unrecognized decoder mapping');
    if(m[1]==='0'||!m[2]||m[2].startsWith('['))continue;const p=m[2].replace(/\\([0-7]{3})/g,(_,x)=>String.fromCharCode(parseInt(x,8)));need(path.isAbsolute(p)&&!p.endsWith(' (deleted)'),'unresolved decoder mapping');paths.add(p);}
  return [...paths].sort();}
function decoderGuard(tools,file,folder,label,{execute=cp.spawn,seconds=120,onClose=()=>{}}={}){
  S.currentRecords(tools);const input=S.record(file,{limit:S.LIMITS.videoBytes}),tool=tools.tools.decoder;S.requireRecord(tool);
  const wanted=['-v','error','-i',file,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'];
  const state={protocol:'r002f-bfcache-decoder/1',argv:[tool.path,...wanted],input,timeoutSeconds:seconds,returncode:null,timedOut:false,bytes:0,frames:0,
    mappingsComplete:false,mappingSnapshots:0,mappedPaths:[],mappingErrors:[],stderrBytes:0,stderrAcknowledgedBytes:0,stderrRetainedBytes:null,
    stderrClosed:false,stderrRetentionError:null,signals:[],scope:'actual sampled file-backed mappings plus resolved ELF closure'};
  let child,timer,poll,ended=false,stderrFd=null;const seen=new Set(),rgbHash=crypto.createHash('sha256');
  const allowed=new Map();for(const row of Object.values(tools.closure.files)){allowed.set(row.identity.resolvedPath,row.identity);for(const alias of row.aliases)allowed.set(alias.resolvedPath,alias);}
  for(const row of tools.mappingData||[])allowed.set(row.resolvedPath,row);
  const stop=why=>{state.error=state.error||why;if(child&&!ended){state.signals.push('SIGKILL');child.kill('SIGKILL');}};
  function snapshot(){if(!child||ended)return;try{const executable=fs.readlinkSync('/proc/'+child.pid+'/exe');if(executable!==tool.resolvedPath)return;
      const paths=mappedFiles(child.pid);need(paths.length>0,'empty decoder mapped-file population');state.mappingSnapshots++;
      for(const literal of paths){const resolved=S.systemPath(literal).resolvedPath;need(allowed.has(resolved),'unexpected mapped dependency: '+literal);seen.add(resolved);}
    }catch(error){if(!['ENOENT','ESRCH'].includes(error.code)){state.mappingErrors.push(String(error.message||error));stop('decoder mappings incomplete');}}}
  const spawn=(command,args,options)=>{need(!child&&command==='ffmpeg'&&S.same(args,wanted)&&S.same(options,{stdio:['ignore','pipe','pipe']}),'original decoder invocation differs');
    const errfile=path.join(folder,label+'.stderr');stderrFd=fs.openSync(errfile,'wx',0o600);
    child=execute(tool.path,args,{...options,env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8',TZ:'UTC'}});state.pid=child.pid;
    timer=setTimeout(()=>{state.timedOut=true;stop('decoder operational deadline');},seconds*1000);poll=setInterval(snapshot,10);snapshot();
    child.stdout.on('data',data=>{rgbHash.update(data);state.bytes+=data.length;state.frames=Math.floor(state.bytes/S.LIMITS.frameRgbBytes);if(state.bytes>S.LIMITS.decodeFrames*S.LIMITS.frameRgbBytes)stop('decoder frame ceiling exceeded');});
    child.stderr.on('data',data=>{const available=Math.max(0,65536-state.stderrAcknowledgedBytes);state.stderrBytes+=data.length;
      if(available&&!state.stderrRetentionError){const written=S.writeOnce(stderrFd,data.subarray(0,available));state.stderrAcknowledgedBytes+=written.acknowledgedBytes;
        if(written.error){state.stderrRetentionError=written.error;stop('decoder stderr retention failed: '+written.error);}}
      if(state.stderrBytes>65536)stop('decoder stderr bound exceeded');});
    child.on('error',error=>{state.error=String(error.stack||error);});
    child.on('close',(code,signal)=>{ended=true;clearTimeout(timer);clearInterval(poll);state.returncode=code;state.signal=signal;state.rgbSha256=rgbHash.digest('hex');
      const final=S.finishFile(stderrFd,errfile);stderrFd=null;state.stderrClosed=final.closed;state.stderr=final.identity||null;state.stderrRetainedBytes=final.identity?.bytes??null;
      if(final.error)state.stderrRetentionError=state.stderrRetentionError||final.error;
      try{S.admitRetained(state.stderr,state.stderrBytes,state.stderrAcknowledgedBytes,state.stderrRetainedBytes,65536);}
      catch(error){state.stderrRetentionError=state.stderrRetentionError||String(error);}
      if(state.stderrRetentionError)state.error=state.error||state.stderrRetentionError;
      try{state.mappedPaths=[...seen].sort();need(state.mappingSnapshots>0&&seen.size>0&&state.mappingErrors.length===0,'no complete actual decoder mapping snapshot');
        for(const resolved of seen)S.requireRecord(allowed.get(resolved));S.requireRecord(input);S.currentRecords(tools);state.mappingsComplete=true;
      }catch(error){state.error=state.error||String(error.stack||error);}
      try{onClose(state);}catch(error){state.error=state.error||String(error.stack||error);}
      try{S.writeJson(path.join(folder,label+'-process.json'),state);}catch(error){state.error=state.error||String(error.stack||error);}});
    return child;};
  return {spawn,state,finish(){need(ended,'decoder did not terminate');admitDecoded(state);return state;}};
}
async function probe(tools,file,folder){S.currentRecords(tools);const tool=tools.tools.probe;S.requireRecord(tool);const args=['-v','error','-show_entries',
  'stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,time_base:format=format_name,duration','-of','json',file];
  const row={argv:[tool.path,...args],timeoutSeconds:30,returncode:null,timedOut:false,stdoutBytes:0,stderrBytes:0};
  let stdout=[],stderr=[];const child=cp.spawn(tool.path,args,{stdio:['ignore','pipe','pipe'],env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8',TZ:'UTC'}});row.pid=child.pid;
  const timer=setTimeout(()=>{row.timedOut=true;child.kill('SIGKILL');},30000);
  for(const key of ['stdout','stderr'])child[key].on('data',bytes=>{row[key+'Bytes']+=bytes.length;if(row[key+'Bytes']>65536){row.overflow=true;child.kill('SIGKILL');}
    else(key==='stdout'?stdout:stderr).push(bytes);});
  await new Promise(resolve=>{child.on('error',error=>{row.error=String(error);});child.on('close',(code,signal)=>{row.returncode=code;row.signal=signal;clearTimeout(timer);resolve();});});
  row.stdout=S.writeBytes(path.join(folder,'metadata.stdout'),Buffer.concat(stdout));row.stderr=S.writeBytes(path.join(folder,'metadata.stderr'),Buffer.concat(stderr));
  S.writeJson(path.join(folder,'metadata-process.json'),row);need(row.returncode===0&&!row.timedOut&&!row.overflow&&!row.error,'actual stream metadata query incomplete');
  const value=JSON.parse(Buffer.concat(stdout)),streams=value.streams;need(Array.isArray(streams)&&streams.length===1,'exactly one actual video stream required');const stream=streams[0];
  for(const [key,want] of Object.entries({codec_type:'video',codec_name:'vp8',width:326,height:530,r_frame_rate:'25/1',avg_frame_rate:'25/1'}))need(stream[key]===want,'actual stream metadata differs: '+key);
  need(typeof stream.time_base==='string'&&stream.time_base&&Number.isFinite(Number(value.format?.duration))&&Number(value.format.duration)>0,'stream time base/duration missing');S.currentRecords(tools);return {row,value};
}
function population(folder,label){const retained=S.readJson(path.join(folder,'retention.json')),r=retained.value;
  need(r.protocol==='r002f-bfcache-returns/1'&&r.stopped===true&&!r.overflow&&r.errors?.length===0&&r.captureCallsAdded===0&&
    r.received===r.attempted&&r.received===r.frames?.length&&r.received<=S.LIMITS.returns,'complete original return population missing');
  S.currentRecords(r);const seen=new Set(),tags=[];let bytes=0,lastReturn=0n;
  for(let i=0;i<r.frames.length;i++){const row=r.frames[i];need(row.index===i+1&&row.file===String(i+1).padStart(4,'0')+'.png'&&row.identity.path===path.join(folder,'returns',row.file),'return record order/path differs');
    need(typeof row.calledNs==='string'&&typeof row.returnedNs==='string'&&/^\d+$/.test(row.calledNs)&&/^\d+$/.test(row.returnedNs)&&
      BigInt(row.calledNs)>=lastReturn&&BigInt(row.returnedNs)>=BigInt(row.calledNs),'actual screenshot call/return order differs');lastReturn=BigInt(row.returnedNs);
    need(!seen.has(row.identity.device+':'+row.identity.inode),'duplicate return descriptor');seen.add(row.identity.device+':'+row.identity.inode);bytes+=row.identity.bytes;tags.push(row.tag);}
  need(bytes===r.pngBytes&&bytes<=S.LIMITS.pngPopulationBytes&&tags[0]==='ref-present'&&tags.at(-1)==='ref-absent','return reference/order/byte population differs');
  let stage=1;for(const tag of tags.slice(1,-1)){const k=Number(tag.slice(8));need(tag==='restore-'+k&&k>=stage&&k<=3,'original burst order differs');stage=k;}
  const values={};for(const [name,row] of Object.entries(r.values)){need(row.path===path.join(folder,'returns','value-'+name+'.json'),'raw value path differs');values[name]=S.readJson(row.path).value;}
  need(['rect','before','after','log','truth','hiddenone','hiddentwo','hiddenthree','isolation'].every(k=>Object.hasOwn(values,k)),'missing original raw evaluation value');
  const native=S.readJson(path.join(folder,label+'.json')),body=native.value;
  need(body.label===label&&body.engine==='chromium'&&body.route==='bfcache'&&body.startISO===S.CLOCK&&body.events===3&&body.fault===false&&body.headed===true,'original witness invocation differs');
  for(const key of ['rect','before','after','truth'])need(S.same(values[key],body[key]),'raw original auxiliary value differs: '+key);
  need(S.same(body.isolation,{allowedExternal:values.isolation.allowedExternal,externalAttempts:values.isolation.externalAttempts,
    byLayerHostOutcome:values.isolation.externalByLayerHostOutcome}),'original full isolation summary differs');
  need(S.same([values.hiddenone,values.hiddentwo,values.hiddenthree],body.hiddenChecks),'hidden document returns differ');
  need(values.log&&Array.isArray(values.log.ev)&&Array.isArray(values.log.frames),'complete raw event/frame log missing');
  const original=S.originalFunctions(),refs={},shots=[];
  for(const row of r.frames){const data=fs.readFileSync(row.identity.path);need(S.same(S.pngInfo(data),row.info),'retained screenshot bytes differ');const image=original.decodePng(data),sample=original.sample(image.data,image.width,image.data.length/(image.width*image.height),body.rect);
    if(row.tag==='ref-present'||row.tag==='ref-absent'){const key=row.tag.slice(4);need(!refs[key],'duplicate reference return');refs[key]=sample;}
    else shots.push({k:Number(row.tag.slice(8)),tag:row.tag,...sample});}
  S.currentRecords(r);return {retained,native,body,values,refs,shots};}
async function replayArm(folder,label,toolsPath,output){S.freshDirectory(output);const toolsRead=S.readJson(toolsPath),tools=toolsRead.value;
  need(tools.protocol==='r002f-bfcache-tools/1'&&tools.status==='COMPLETE'&&tools.capability?.scope==='SOURCE_CONTROL_ONLY','selected hosted tool admission missing');
  const p=population(folder,label),file=path.join(folder,label+'.webm'),video=S.record(file,{limit:S.LIMITS.videoBytes});
  need(p.body.valid===true&&p.body.void?.length===0&&!p.body.error,'original VOID/error witness cannot become an observed diagnostic');
  const metadata=await probe(tools,file,output),decoder=decoderGuard(tools,file,output,'replay-decoder');
  const readonly={existsSync:literal=>literal===file&&fs.existsSync(file),copyFileSync:(from,to)=>{need(from===file&&to===file,'replay must not copy or replace original WebM');S.requireRecord(video);},
    statSync:literal=>{need(literal===file,'replay stat scope differs');return fs.statSync(file);},readFileSync:literal=>{need(literal===file,'replay read scope differs');return fs.readFileSync(file);}};
  const out={...structuredClone(p.body),void:[],log:p.values.log};
  const got=await judgment({out,shots:p.shots,refs:p.refs,videoPath:file,outDir:folder,filesystem:readonly,spawn:decoder.spawn});decoder.finish();compareReport(p.body,got.slim);
  S.currentRecords(p.retained.value);S.requireRecord(p.native.identity);S.requireRecord(video);S.requireRecord(toolsRead.identity);
  const result={protocol:'r002f-bfcache-replay/1',status:'COMPLETE',scope:'EXACT_ORIGINAL_REPLAY',originalReport:p.native.identity,retention:p.retained.identity,
    video,tools:toolsRead.identity,metadata,decoder:decoder.state,fullPopulation:{screenshotReturns:p.shots.length+2,videoFrames:got.full.video.frames,rawAnimationFrames:got.full.log.frames.length},
    valid:got.full.valid,verdict:got.full.verdict,judged:S.plain(got.full.judged),source:S.originalSources()};
  S.writeJson(path.join(output,'replay.json'),result);return result;}
module.exports={judgment,sourceControl,compareReport,admitDecoded,mappedFiles,decoderGuard,probe,population,replayArm};
if(require.main===module){const [folder,label,tools,output]=process.argv.slice(2);replayArm(folder,label,tools,output).then(r=>console.log(JSON.stringify({status:r.status,valid:r.valid,verdict:r.verdict}))).catch(error=>{console.error(error.stack||error);process.exitCode=2;});}
