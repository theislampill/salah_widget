'use strict';
// Admission and lossless retention for an opt-in diagnostic. No browser import.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const MODULES=Object.freeze(['r002f_probe.cjs','browser-control.cjs','r002f_tabhide_source.cjs',
  'r002f_tabhide_runtime.cjs','r002f_tabhide.cjs','r002f_focus_owner.cjs']);
const ASSETS=Object.freeze({
  'moon/assets/dem.bin.gz':{bytes:20137935,sha256:'ecd3a8e941edc7050e1e6c51e87f9084466e1ccfadf1eb57297302191de82960'},
  'moon/assets/colour.bin.gz':{bytes:32272181,sha256:'29948c38c12c4b9733789fa9ea1c13fb12b0b00035169876651f7a2ef3b6af34'},
  'moon/asset-manifest.json':{sha256:'3d4cb527489acda67082bbc97d984abbb28a11a40f0aec8b4030223fb15e9afa'}
});
const LIMITS=Object.freeze({frames:512,bytes:268435456,frameBytes:4194304,events:64,requests:2048});
const BUDGET=Object.freeze({protocol:'r002f-tabhide-budget/1',rows:4,setupWaitSeconds:180,settledWaitSeconds:120,
  evidenceWaitCeilingSeconds:4*(180+120),remainingAggregateAllowanceSeconds:600,laneSeconds:1800,namespaceAllowanceSeconds:75});
const STATUS='OBSERVED_TABHIDE_DIAGNOSTIC';
const CLOCK_UTC=Date.parse('2026-09-07T00:10:05Z');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const need=(v,m)=>{if(!v)throw Error(m);};
function regular(file){
  file=path.resolve(file);
  for(let p=file;;p=path.dirname(p)){
    need(!fs.lstatSync(p).isSymbolicLink(),'symlink in admitted path');
    if(path.dirname(p)===p)break;
  }
  need(fs.statSync(file).isFile(),'regular file required');return file;
}
function body(file){return fs.readFileSync(regular(file));}
function identity(file){
  const fd=fs.openSync(regular(file),'r'),hash=crypto.createHash('sha256'),buffer=Buffer.allocUnsafe(1048576);let bytes=0;
  try{for(;;){const n=fs.readSync(fd,buffer,0,buffer.length,null);if(!n)break;bytes+=n;hash.update(buffer.subarray(0,n));}}
  finally{fs.closeSync(fd);}
  return {bytes,sha256:hash.digest('hex')};
}
function relative(root,name){
  need(typeof name==='string' && name && !path.isAbsolute(name) && !name.split(/[\\/]/).some(x=>x==='..'||!x),
    'unsafe relative evidence path');
  const p=path.resolve(root,name);need(p.startsWith(path.resolve(root)+path.sep),'outside evidence root');return p;
}
function writeBytes(file,bytes){
  const fd=fs.openSync(file,'wx',0o600);
  try{let at=0;while(at<bytes.length)at+=fs.writeSync(fd,bytes,at,bytes.length-at);fs.fsyncSync(fd);}
  finally{fs.closeSync(fd);}
}
function writeJson(file,value){writeBytes(file,Buffer.from(JSON.stringify(value,null,2)+'\n'));}
function privateRoot(out,protectedRoots){
  out=path.resolve(out);
  need(!fs.existsSync(out),'output must be fresh');
  for(const input of protectedRoots){const root=path.resolve(input);
    need(out!==root&&!out.startsWith(root+path.sep),'private output must be outside source/dependencies');}
  for(let p=path.dirname(out);;p=path.dirname(p)){
    if(fs.existsSync(p))need(!fs.lstatSync(p).isSymbolicLink()&&fs.statSync(p).isDirectory(),'private output ancestor is not an unlinked directory');
    if(path.dirname(p)===p)break;
  }
  fs.mkdirSync(out,{recursive:true,mode:0o700});return out;
}
function admitSources(folder=__dirname){
  const manifest=JSON.parse(body(path.join(folder,'r002f-tabhide-pins.json')));
  need(manifest.protocol==='r002f-tabhide-source/1' && manifest.reconstructedFromPublicCommit===
    '890c7b6005228715b58b3d1d90847f39cf4698be','wrong source manifest provenance');
  need(Object.keys(manifest.modules||{}).sort().join('\n')===MODULES.slice().sort().join('\n'),'wrong source module population');
  for(const name of MODULES){const got=identity(path.join(folder,name)),want=manifest.modules[name];
    need(want.bytes===got.bytes && want.sha256===got.sha256,'source identity differs: '+name);}
  return manifest;
}
let original;
function owners(){admitSources();return original??=require('./r002f_probe.cjs');}
function generated(root,index){
  root=path.resolve(root);regular(path.join(root,'GENERATED.json'));
  const inventory=JSON.parse(body(path.join(root,'GENERATED.json')));
  for(const name of Object.keys(inventory.files||{}))regular(relative(root,name));
  const admitted=owners().builtIdentity(root,index);need(admitted.files.length===116,'wrong generated population');
  const assets={};for(const [name,want] of Object.entries(ASSETS)){
    const got=identity(relative(root,name));need(got.sha256===want.sha256 && (want.bytes===undefined||got.bytes===want.bytes),'external Moon asset drift');
    assets[name]=got;
  }
  return {root,...admitted,assets};
}
function crc32(bytes){let c=0xffffffff;for(const byte of bytes){c^=byte;for(let i=0;i<8;i++)c=c&1?(c>>>1)^0xedb88320:c>>>1;}return (c^0xffffffff)>>>0;}
function pngInfo(data){
  need(Buffer.isBuffer(data) && data.length>=45 && data.length<=LIMITS.frameBytes &&
    data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])),'invalid or excessive PNG');
  let at=8,width,height,channels,ended=false;const packed=[];let seenHeader=false;
  while(at<data.length){
    need(at+12<=data.length,'truncated PNG chunk');const n=data.readUInt32BE(at),type=data.toString('ascii',at+4,at+8);
    need(n<=LIMITS.frameBytes && at+12+n<=data.length,'truncated PNG payload');
    need(crc32(data.subarray(at+4,at+8+n))===data.readUInt32BE(at+8+n),'PNG checksum mismatch');
    const chunk=data.subarray(at+8,at+8+n);
    if(!seenHeader){
      need(type==='IHDR' && n===13,'PNG header must be first');seenHeader=true;
      width=chunk.readUInt32BE(0);height=chunk.readUInt32BE(4);channels=chunk[9]===2?3:chunk[9]===6?4:0;
      need(width===400 && height===650 && chunk[8]===8 && channels && chunk[10]===0 && chunk[11]===0 && chunk[12]===0,
        'PNG is not the declared lossless DPR1 viewport');
    }else need(type!=='IHDR','duplicate PNG header');
    if(type==='IDAT')packed.push(chunk);
    if(type==='IEND'){need(n===0 && at+12===data.length,'invalid PNG end or trailing bytes');ended=true;}
    at+=12+n;
  }
  need(ended && packed.length,'PNG lacks complete image data');
  const stride=1+width*channels,raw=zlib.inflateSync(Buffer.concat(packed),{maxOutputLength:height*stride});
  need(raw.length===height*stride,'PNG decoded population differs');
  for(let y=0;y<height;y++)need(raw[y*stride]<=4,'invalid PNG scanline filter');
  return {width,height,encoding:'lossless-png',bytes:data.length,sha256:sha(data)};
}
function frameSink(folder,ack,limits=LIMITS){
  const state={protocol:'r002f-tabhide-frames/1',limits:{frames:limits.frames,bytes:limits.bytes,frameBytes:limits.frameBytes},
    frames:[],received:0,bytes:0,overflow:false,errors:[],stopped:false};let pending=Promise.resolve();
  const error=e=>{if(state.errors.length<8)state.errors.push(String(e.message||e));};
  return {state,accept(event,phase){
    const sequence=++state.received,hostNs=process.hrtime.bigint().toString();
    // CDP delivers at most a bounded number of unacknowledged frames. Explicit
    // limits also guard a malformed or unusually active producer; skipped
    // packets make the complete diagnostic inadmissible, never silently pass.
    const excessive=state.stopped || sequence>limits.frames || typeof event.data!=='string' || event.data.length>Math.ceil(limits.frameBytes*4/3)+4;
    if(excessive)state.overflow=true;
    pending=pending.then(async()=>{
      try{
        need(!excessive,'frame retention bound exceeded');
        const raw=Buffer.from(event.data,'base64');need(raw.length<=limits.frameBytes,'frame byte bound exceeded');
        if(state.bytes+raw.length>limits.bytes){state.overflow=true;throw Error('aggregate frame byte bound exceeded');}
        const info=pngInfo(raw),file='frame-'+String(sequence).padStart(4,'0')+'.png';
        writeBytes(path.join(folder,file),raw);state.bytes+=raw.length;
        const row={sequence,file,phase,hostNs,metadata:event.metadata,sessionId:event.sessionId,...info,acked:false};
        state.frames.push(row);writeJson(path.join(folder,'frame-'+String(sequence).padStart(4,'0')+'.json'),
          {protocol:'r002f-tabhide-frame-journal/1',recordState:'RETAINED_BEFORE_ACK',...row});
        try{await ack(event.sessionId);row.acked=true;}catch(e){error(e);}
      }catch(e){error(e);try{await ack(event.sessionId);}catch(e2){error(e2);}}
    });return pending;
  },async finish(){await pending;state.stopped=true;return state;}};
}
function clock(sample){
  need(sample?.protocol==='r002f-translated-date/1' && sample.rate===1 && sample.nativeCallbacks===true &&
    Number.isFinite(sample.utc) && Number.isFinite(sample.perf) && Number.isFinite(sample.originUtc) &&
    Number.isFinite(sample.originPerf) && sample.perf>=sample.originPerf &&
    Math.abs((sample.utc-sample.originUtc)-(sample.perf-sample.originPerf))<=2,'Date/native clock identity or rate differs');
}
function mature(sample){
  need(sample && sample.hidden===false && sample.paused===false && sample.intersects===true && sample.dpr===1,
    'visible unpaused DPR1 setup missing');clock(sample.clock);
  need(sample.sky?.status==='ready' && sample.sky.physical===true && sample.sky.composed===true && sample.sky.displayed===true &&
    Number.isFinite(sample.sky.displayedUtcMs) && Math.abs(sample.clock.utc-sample.sky.displayedUtcMs)<=30000 && Number.isFinite(sample.sky.sunAltitude) &&
    sample.sky.sunAltitude<-12 && sample.moon?.current===true && sample.moon.accepted===true &&
    sample.moon.source==='refined-terrain' && sample.moon.quality==='empirical-adaptive' &&
    sample.moon.phasePositionBudget===0.0416 && typeof sample.moon.identity==='string' && sample.moon.identity,
    'mature physical refined sky/Moon setup missing');
}
function lifecycleCustody(record,kind){
  need(record?.protocol==='r002f-process-lifecycle/1' && record.kind===kind && record.cleanupRequested===true &&
    record.closed===true && record.overflow===false && Array.isArray(record.faults) && record.faults.length===0,
    kind+' lifecycle custody contains an unexpected close, crash or late fault');
}
function finalLifecycles(report){
  lifecycleCustody(report.browserLifecycle,'browser');
  need(Array.isArray(report.armLifecycles)&&report.armLifecycles.length===2&&
    report.armLifecycles.map(x=>x.arm).join(',')==='baseline,candidate','final arm lifecycle population differs');
  for(const arm of report.armLifecycles){
    need(arm.setupError===null&&arm.cleanupError===null,'arm setup or cleanup failed');
    lifecycleCustody(arm.page,'page');lifecycleCustody(arm.context,'context');
    need(Array.isArray(arm.pageErrors)&&arm.pageErrors.length===0,'late page error survived arm row retention');
  }
}
function admitRow(row){
  need(row?.protocol==='r002f-tabhide-row/1' && ['baseline','candidate'].includes(row.arm) &&
    ['no-hide','tabhide'].includes(row.mode) && row.contextClosed===true && row.cleanupError===null &&
    row.error===null && row.completed===true && Array.isArray(row.pageErrors) && row.pageErrors.length===0,'row completion or cleanup incomplete');
  lifecycleCustody(row.lifecycleCustody?.page,'page');lifecycleCustody(row.lifecycleCustody?.context,'context');
  need(row.servedIndexSha256===(row.arm==='baseline'?owners().BASE_INDEX:owners().COMBINED_INDEX),'served entry differs');
  mature(row.before);mature(row.settled);
  need(row.before.clock.originUtc===CLOCK_UTC && row.settled.clock.originUtc===CLOCK_UTC,'wrong disclosed UTC origin');
  need(row.clockCheck?.timerRan===true && row.clockCheck.rafRan===true && row.clockCheck.nativeCallbacks===true &&
    Number.isFinite(row.clockCheck.performanceDeltaMs) && row.clockCheck.performanceDeltaMs>=20 &&
    Math.abs(row.clockCheck.dateDeltaMs-row.clockCheck.performanceDeltaMs)<=2,'native clock callback check incomplete');
  const trace=row.lifecycle;
  need(trace?.protocol==='r002f-tabhide-lifecycle/1' && trace.clockDomain==='page-performance-now-ms' &&
    trace.mode===row.mode && trace.limit===LIMITS.events && trace.overflow===false && trace.triggered===true &&
    trace.controlComplete===(row.mode==='no-hide') &&
    Array.isArray(trace.events) && trace.events.length<=LIMITS.events && Array.isArray(trace.marks),'lifecycle trace incomplete');
  const visible=trace.events.filter(e=>e.type==='visibilitychange');
  need(visible.length===(row.mode==='tabhide'?2:0),'missing or duplicate visibility route');
  let last=-Infinity;for(const event of trace.events){
    need(event.trusted===true && Number.isFinite(event.at) && event.at>=last,'untrusted or reordered lifecycle event');last=event.at;
    need(event.type==='visibilitychange','navigation or unknown event is outside this tab-hide route');clock(event.sample.clock);
  }
  if(row.mode==='tabhide'){
    need(visible[0].sample.hidden===true && visible[0].sample.paused===true && visible[0].sample.intersects===true &&
      visible[1].sample.hidden===false && visible[1].sample.paused===false,'genuine tab hide/restore is unestablished');
    need(visible[0].sample.moon.accepted===false && visible[0].sample.moon.current===false,'hide did not withdraw lunar authority');
  }
  need(trace.marks.map(x=>x.name).join(',')==='begin,trigger,callback-microtask,raf-1,raf-2,settled','incomplete or duplicated callback sequence');
  last=-Infinity;for(const mark of trace.marks){
    need(Number.isFinite(mark.at) && mark.at>=last && mark.sample.hidden===false,'callback ordering/visibility differs');last=mark.at;
    clock(mark.sample.clock);
    // Invoke the unchanged complete-field structural checks. The returned
    // differences against this reference instant are deliberately not a
    // currentness verdict: this supplemental clock advances normally.
    owners().prayerDifferences(mark.sample.prayer,owners().SCENARIOS[2].after);
  }
  const samples=[row.before,row.settled,...trace.events.map(x=>x.sample),...trace.marks.map(x=>x.sample)];
  need(samples.every(s=>s.clock.originUtc===CLOCK_UTC && s.clock.originPerf===row.before.clock.originPerf),
    'mixed Date origin or native performance clock anchor');
  for(const item of [...trace.events,...trace.marks])need(item.sample.clock.perf>=item.at,'lifecycle sample precedes its same-clock event or mark');
  const [begin,trigger,callbackMicrotask,raf1,raf2,settled]=trace.marks;
  need(begin.at<=row.before.clock.perf && row.before.clock.perf<=trigger.at &&
    settled.at<=row.settled.clock.perf,'setup/settled snapshots are outside their same-clock marks');
  need(row.intendedHoldMs===250,'changed diagnostic hold');
  if(row.mode==='tabhide')need(trigger.at<=visible[0].at && visible[0].at<=visible[1].at && visible[1].at<=callbackMicrotask.at &&
    visible[1].at-visible[0].at>=row.intendedHoldMs,'hide/restore shared-clock ordering or held interval differs');
  else need(callbackMicrotask.at-trigger.at>=row.intendedHoldMs,'no-hide shared-clock held interval differs');
  need(callbackMicrotask.at<=raf1.at && raf1.at<=raf2.at && raf2.at<=settled.at,'restoration callback shared-clock order differs');
  need(row.route==='headed-chromium-bringToFront' && row.frameBoundary===
    'first CDP PNG packet received after activation request began; not first displayed frame','capture label or route differs');
  const frames=row.capture;
  need(frames?.protocol==='r002f-tabhide-frames/1' && frames.stopped===true && frames.overflow===false &&
    frames.errors?.length===0 && frames.frames.length>0 && frames.frames.length===frames.received &&
    JSON.stringify(frames.limits)===JSON.stringify({frames:LIMITS.frames,bytes:LIMITS.bytes,frameBytes:LIMITS.frameBytes}) &&
    frames.bytes===frames.frames.reduce((n,x)=>n+x.bytes,0),'partial or excessive frame retention');
  need(frames.frames.every((f,i)=>f.sequence===i+1 && f.acked===true && f.encoding==='lossless-png' &&
    f.width===400 && f.height===650 && Number.isFinite(f.metadata?.timestamp) && /^\d+$/.test(f.hostNs)),
    'frame sequence, protocol metadata or acknowledgements incomplete');
  const first=frames.frames.find(f=>f.phase==='activation-requested');
  need(first && row.firstCapturedFrame===first.file,'first captured return frame is not the recorded first packet');
  need(row.stills?.setup?.boundary==='mature setup before this schedule' &&
    row.stills?.settled?.boundary==='later settled refined state; not first presented frame','setup/settled stills missing');
  need(row.ledger?.overflow===false && Array.isArray(row.ledger.requests) && row.ledger.requests.length<=LIMITS.requests &&
    row.ledger.unexpected?.length===0 && row.ledger.errors?.length===0 &&
    !row.ledger.requests.some(x=>['route-error','unexpected-aborted','websocket-aborted'].includes(x.action)),
    'final request ledger is incomplete or contains an unexpected route');
  return {status:'OBSERVED',scope:'instrumented ordinary-clock lifecycle and captured pixels; no policy or first-display acceptance'};
}
function boundary(row,host){
  need(row?.protocol==='salah-hosted-browser-boundary/1' && row.passed===true && row.headless===false &&
    row.chromiumSandbox===true && row.uid===host.uid && row.netns===host.netns && row.browserPid===host.browserPid &&
    row.executableSha256===host.executableSha256 && row.loopbackRequests>=2 &&
    /ERR_(NETWORK|ADDRESS)_UNREACHABLE|ERR_INTERNET_DISCONNECTED/.test(row.externalNavigationError||'') &&
    row.postNegativePage==='fresh-page-same-browser' && row.contextsClosed===true,'headed browser boundary incomplete');
}
function admitReport(report,root,{baseline,candidate,isolationFile}={}){
  const manifest=admitSources(),P=owners();
  need(report?.protocol==='r002f-tabhide-native/1' && report.status===STATUS && report.engine==='chromium' && report.dpr===1 &&
    report.rounds===1 && report.section==='all' && report.route==='tabhide' && report.headless===false &&
    report.continuationVetoed===false && report.errors?.length===0 && report.cleanup?.contexts===true &&
    report.cleanup.browser===true && report.cleanup.servers===true && report.cleanup.xvfb===true &&
    report.cleanup.browserPidsGone===true,'report, population or cleanup incomplete');
  finalLifecycles(report);
  need(JSON.stringify(report.budget)===JSON.stringify(BUDGET),'reported aggregate budget differs');
  need(report.sourceManifestSha256===sha(body(path.join(__dirname,'r002f-tabhide-pins.json'))) &&
    JSON.stringify(report.sourceManifest)===JSON.stringify(manifest),'reported source closure differs');
  need(report.playwright?.version==='1.62.1' && report.playwright.headless===false && report.playwright.chromiumSandbox===true &&
    identity(report.playwright.executablePath).sha256===report.playwright.executableSha256,'headed executable identity differs');
  need(report.isolation?.file===path.resolve(isolationFile) && report.isolation.sha256===sha(body(isolationFile)),
    'current isolation receipt differs');
  const isolation=JSON.parse(body(isolationFile)),host=report.host;
  P.validateIsolation(isolation,host);
  P.validateIsolation(isolation,{uid:process.getuid?.(),netns:fs.readlinkSync('/proc/self/ns/net')});
  need(host.pidns && report.browserProcess?.pid===host.browserPid && report.browserProcess.uid===host.uid &&
    report.browserProcess.netns===host.netns && report.browserProcess.pidns===host.pidns &&
    report.browserProcess.sha256===report.playwright.executableSha256 &&
    !report.browserProcess.argv.some(x=>x==='--no-sandbox'||x.startsWith('--headless')),'headed process custody differs');
  need(report.xvfb?.package==='xvfb' && typeof report.xvfb.version==='string' && report.xvfb.version &&
    report.xvfb.packageStatus==='install ok installed' && report.xvfb.process.uid===host.uid &&
    report.xvfb.process.netns===host.netns && report.xvfb.process.pidns===host.pidns &&
    report.xvfb.process.sha256===identity(report.xvfb.executable).sha256 && report.xvfb.stopped===true &&
    report.xvfb.process.argv.includes('-nolisten') && report.xvfb.process.argv.includes('tcp'),'Xvfb custody/cleanup incomplete');
  const boundaryHost={...host,executableSha256:report.playwright.executableSha256};
  boundary(report.boundaries?.before,boundaryHost);boundary(report.boundaries?.after,boundaryHost);
  need(JSON.stringify(report.sources?.baseline)===JSON.stringify(generated(baseline,P.BASE_INDEX)) &&
    JSON.stringify(report.sources?.candidate)===JSON.stringify(generated(candidate,P.COMBINED_INDEX)),'generated/source population differs');
  need(Array.isArray(report.rows) && report.rows.length===4,'expected two arms and their no-hide controls');
  const seen=new Set();for(const entry of report.rows){
    const key=entry.arm+'/'+entry.mode;need(!seen.has(key),'duplicate diagnostic row');seen.add(key);
    need(['baseline/no-hide','baseline/tabhide','candidate/no-hide','candidate/tabhide'].includes(key),'unexpected diagnostic row');
    const rowPath=relative(root,entry.file),raw=body(rowPath);need(sha(raw)===entry.sha256,'row bytes differ');
    const row=JSON.parse(raw);need(row.arm===entry.arm && row.mode===entry.mode,'row identity differs');
    need(JSON.stringify(admitRow(row))===JSON.stringify(entry.verdict),'row admission differs');
    const dir=path.dirname(rowPath),images=[...row.capture.frames,...Object.values(row.stills)];
    for(const image of images){const png=pngInfo(body(relative(dir,image.file)));
      need(png.sha256===image.sha256 && png.bytes===image.bytes && png.width===image.width && png.height===image.height,'retained PNG differs');}
  }
  return {status:STATUS,nativeQualification:'LIFECYCLE_OBSERVATION_ONLY',humanAcceptance:'OUTSTANDING'};
}
module.exports={MODULES,ASSETS,LIMITS,BUDGET,STATUS,CLOCK_UTC,sha,need,regular,body,identity,relative,writeBytes,writeJson,privateRoot,
  admitSources,owners,generated,pngInfo,frameSink,clock,mature,lifecycleCustody,finalLifecycles,admitRow,boundary,admitReport};
