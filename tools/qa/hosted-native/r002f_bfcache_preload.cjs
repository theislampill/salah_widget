'use strict';
// Explicit preload for the unchanged, pinned R0041 witness under the R002F diagnostic selector.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto'),cp=require('node:child_process');
const {EventEmitter}=require('node:events'),{PassThrough}=require('node:stream');
const S=require('./r002f_bfcache_source.cjs'),T=require('./r002f_tabhide.cjs'),R=require('./r002f_bfcache_replay.cjs'),{need}=S;
const ARGS=Object.freeze(['--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1 , EXCLUDE localhost','--disable-background-networking',
  '--dns-prefetch-disable','--no-pings','--force-webrtc-ip-handling-policy=disable_non_proxied_udp','--webrtc-ip-handling-policy=disable_non_proxied_udp',
  '--disable-component-update','--disable-domain-reliability','--disable-sync','--disable-features=NetworkPrediction,OptimizationHints,MediaRouter']);
const PHASES=Object.freeze({admission:30,display:15,listeners:15,launch:210,owner:15,before:180,experiment:600,
  contextClose:90,after:180,browserClose:60,serverDrain:15,decoder:120,judgment:60,failureCleanup:60,reserve:30});
const ENV_KEYS=new Set(['PATH','LANG','LC_ALL','TZ','TMPDIR','TMP','TEMP','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_RUNTIME_DIR',
  'PLAYWRIGHT_BROWSERS_PATH','PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','PLAYWRIGHT_PKG',
  'R002F_BFCACHE_CHILD','SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT','NODE_CHANNEL_FD','NODE_CHANNEL_SERIALIZATION_MODE','NODE_PATH',
  'GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0','GIT_CONFIG_KEY_1','GIT_CONFIG_VALUE_1']);
function cleanChildEnvironment(env){for(const key of Object.keys(env))need(ENV_KEYS.has(key),'unadmitted child environment: '+key);
  const browser={};for(const key of ['PATH','LANG','LC_ALL','TZ','TMPDIR','TMP','TEMP','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_RUNTIME_DIR'])if(Object.hasOwn(env,key))browser[key]=env[key];return browser;}
function expectedLaunch(proxy){return {headless:false,ignoreDefaultArgs:['--disable-back-forward-cache'],args:[...ARGS],proxy};}
function launchOptions(original,{proxy,executable,display,env}){need(S.same(original,expectedLaunch(proxy)),'original launch options differ');
  need(path.isAbsolute(executable)&&/^:\d+$/.test(display),'actual executable and owned display required');
  return {headless:original.headless,ignoreDefaultArgs:original.ignoreDefaultArgs,args:original.args,
    chromiumSandbox:true,executablePath:executable,env:{...env,DISPLAY:display}};}
async function guardBrowser(browser,expected,hooks){const rawContext=browser.newContext.bind(browser),rawPage=browser.newPage.bind(browser),rawClose=browser.close.bind(browser);
  const state={stage:'before',contexts:0,directContexts:{before:0,after:0},closeCalls:0,closed:false,afterComplete:false};let directOptions;
  browser.newPage=async options=>{need(['before','after'].includes(state.stage)&&!directOptions&&S.same(options,{serviceWorkers:'block'}),'unadmitted direct boundary context');
    directOptions=options;try{return await rawPage(options);}finally{directOptions=undefined;}};
  browser.newContext=async options=>{if(directOptions===options&&['before','after'].includes(state.stage)){
      need(S.same(options,{serviceWorkers:'block'})&&state.directContexts[state.stage]<2,'unexpected direct boundary context population');
      state.directContexts[state.stage]++;return rawContext(options);}
    need(state.stage==='experiment'&&state.contexts===0&&S.same(options,expected),'unexpected or altered original experiment context');
    state.contexts++;const context=await rawContext(options);await hooks.context(context);return context;};
  async function actualClose(){need(state.closeCalls===0,'browser close already attempted');state.closeCalls++;state.stage='browserClose';
    try{await hooks.closing?.();await rawClose();state.closed=!browser.isConnected();need(state.closed,'browser API remains connected');}
    finally{state.stage='closed';}}
  browser.close=async()=>{need(state.stage==='experiment'&&state.closeCalls===0,'browser close order differs');let failure;
    try{need(hooks.contextsClosed(),'experiment context/recorder did not close');state.stage='after';await hooks.after(browser);state.afterComplete=true;}
    catch(error){failure=error;hooks.fault(error);}finally{try{await actualClose();}catch(error){hooks.fault(error);failure=failure||error;}}
    if(failure)throw failure;};
  state.failureCleanup=async()=>{if(state.closeCalls===0)await actualClose();};
  try{await hooks.before(browser);state.stage='experiment';return state;}
  catch(error){hooks.fault(error);try{await state.failureCleanup();}catch(cleanup){hooks.fault(cleanup);}throw error;}}
function processScan(executable){const result={protocol:'r002f-bfcache-owner-census/1',executable,rows:[],failures:[],complete:false};
  const ids=fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x)).map(Number).sort((a,b)=>a-b);need(ids.length<=4096,'process census bound exceeded');result.entries=ids.length;
  for(const pid of ids){let exe;try{exe=fs.readlinkSync('/proc/'+pid+'/exe');}catch(error){result.failures.push({pid,stage:'exe',code:error.code});continue;}
    if(exe!==executable)continue;try{result.rows.push(T.processInfo(pid));}catch(error){result.failures.push({pid,stage:'candidate',code:error.code});}}
  result.complete=result.failures.every(e=>['ENOENT','ESRCH'].includes(e.code));return result;}
function admitCensus(census,binary){need(census.protocol==='r002f-bfcache-owner-census/1'&&
    census.executable===binary.resolvedPath&&census.complete===true&&Array.isArray(census.rows)&&Number.isInteger(census.entries)&&
    census.entries>=census.rows.length&&census.entries<=4096&&Array.isArray(census.failures)&&census.failures.every(x=>['ENOENT','ESRCH'].includes(x.code)),
    'complete actual process scan required');return census;}
function owner(before,after,host,binary){for(const census of [before,after])admitCensus(census,binary);
  need(before.rows.length===0,'managed browser already alive before this arm');const main=after.rows.filter(row=>T.mainBrowserArgv(row.argv,binary.resolvedPath));
  need(main.length===1,'one actual managed main browser required');const p=main[0];
  need(Number.isInteger(p.pid)&&p.pid>0&&typeof p.startTicks==='string'&&/^[1-9]\d*$/.test(p.startTicks)&&
    p.uid===host.uid&&p.netns===host.netns&&p.pidns===host.pidns&&p.exe===binary.resolvedPath&&p.sha256===binary.sha256&&
    !p.argv.some(a=>a.startsWith('--no-sandbox')||a.startsWith('--headless')||a.startsWith('--remote-debugging-port')||a.startsWith('--proxy-server')||a.startsWith('--proxy-bypass-list'))&&p.argv.includes('--remote-debugging-pipe')&&
    p.argv.some(a=>a.startsWith('--user-data-dir='))&&ARGS.every(a=>p.argv.includes(a))&&!p.argv.includes('--disable-back-forward-cache'),'actual headed sandbox/argv/owner differs');return p;}
async function strictBoundary(browser,report,host){const marker=crypto.randomBytes(24).toString('hex'),before=new Set(browser.contexts());let hits=0,server;
  Object.assign(report,{protocol:'salah-hosted-browser-boundary/1',passed:false,headless:false,chromiumSandbox:true,uid:host.uid,netns:host.netns,
    browserPid:host.browserPid,executableSha256:host.executableSha256,contextsClosed:false});
  try{server=http.createServer((req,res)=>{hits++;res.end(marker);});await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    const origin='http://127.0.0.1:'+server.address().port,page=await browser.newPage({serviceWorkers:'block'});
    await page.goto(origin+'/before',{timeout:10000});need(await page.textContent('body')===marker,'headed loopback marker missing');
    await require('./browser-control.cjs').refuseExternalThenReadLoopback(browser,page,origin,marker,report);need(hits>=2,'post-negative marker missing');report.loopbackRequests=hits;report.passed=true;
  }catch(error){report.error=String(error.stack||error);throw Object.assign(error,{isolation:true});}
  finally{try{for(const context of browser.contexts())if(!before.has(context))await T.bounded(context.close(),10000,'boundary context cleanup');report.contextsClosed=true;}
    catch(error){report.passed=false;report.cleanupError=String(error);throw Object.assign(error,{isolation:true});}
    finally{if(server)try{await T.bounded(new Promise(resolve=>server.close(resolve)),5000,'boundary server cleanup');}catch(error){report.passed=false;report.serverCleanupError=String(error);throw Object.assign(error,{isolation:true});}}}}
function recorderArguments(output){return '-loglevel error -f matroska -fpsprobesize 0 -probesize 32 -analyzeduration 0 -i pipe:0 -y -an -r 25 -c:v vp8 -qmin 0 -qmax 50 -crf 8 -deadline realtime -speed 8 -b:v 1M -threads 1 -vf pad=326:530:0:0:gray,crop=326:530:0:0'.split(' ').concat(output);}
function deferredChild(wait,start){const proxy=new EventEmitter();proxy.stdout=new PassThrough();proxy.stderr=new PassThrough();let actual;
  Object.defineProperty(proxy,'pid',{get:()=>actual?.pid});proxy.kill=signal=>actual?.kill(signal);
  wait.then(()=>{actual=start();actual.stdout.pipe(proxy.stdout);actual.stderr.pipe(proxy.stderr);actual.on('error',e=>proxy.emit('error',e));actual.on('close',(c,s)=>proxy.emit('close',c,s));})
    .catch(error=>{proxy.stdout.end();proxy.stderr.end();proxy.emit('error',error);proxy.emit('close',null,null);});return proxy;}
function evaluationKind(fn,state){const source=fn.toString();
  const literal={rect:"()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};}",
    state:'()=>window.__rw.st()',hidden:'()=>document.title',back:'()=>{history.back();}',control:'()=>{window.__rw.control=true;window.__rw.paint();}',
    log:'()=>({ev:window.__rw.ev,frames:window.__rw.frames,c:window.__rw.c})',
    truth:"()=>{const t=window.qaState&&window.qaState().moonTruth;return t?{displayMode:t.displayMode,degraded:t.degraded===undefined?'(field absent)':t.degraded,limitation:t.limitation,slotState:t.slotState,surfaceStatus:t.surface&&t.surface.status,moonlightOpacity:t.moonlightOpacity}:null;}"};
  const kind=Object.keys(literal).find(k=>literal[k]===source);need(kind,'unexpected original evaluation source');
  if(kind==='state'){state.stateReads++;need(state.stateReads<=2,'extra original state read');return state.stateReads===1?'before':'after';}
  if(kind==='hidden'){state.hiddenReads++;need(state.hiddenReads<=3,'extra hidden document read');return ['hiddenone','hiddentwo','hiddenthree'][state.hiddenReads-1];}
  if(kind==='back'){state.restoration++;need(state.restoration<=3,'extra history restoration');return null;}
  if(kind==='control'){need(!state.control&&state.restoration===3,'control order differs');state.control=true;return null;}
  return kind;}
function admitChildSources(config,{currentRecords=S.currentRecords,generated,git}={}){
  need(config.sources?.root===S.REPO&&config.sources.clean===true&&/^[a-f0-9]{40}$/.test(config.sources.commit)&&/^[a-f0-9]{40}$/.test(config.sources.tree),
    'literal complete child source identity required');currentRecords(config.sources);
  const query=git||((args)=>cp.execFileSync('/usr/bin/git',['-C',S.REPO,...args],{encoding:'utf8',timeout:10000,maxBuffer:1024**2}).trim());
  need(query(['status','--porcelain'])===''&&query(['rev-parse','HEAD'])===config.sources.commit&&query(['rev-parse','HEAD^{tree}'])===config.sources.tree,
    'actual child Git source changed');
  const original=require('./r002f_tabhide_source.cjs'),P=original.owners(),index=config.label==='baseline'?P.BASE_INDEX:P.COMBINED_INDEX;
  need(S.same((generated||original.generated)(config.root,index),config.generated),'complete child generated population changed');return true;}
async function startDisplay(config,host,state,rawSpawn){const binary=config.tools.tools.xvfb;S.requireRecord(binary);
  const stdout=fs.openSync(path.join(config.out,'xvfb.stdout'),'wx',0o600),stderr=fs.openSync(path.join(config.out,'xvfb.stderr'),'wx',0o600);
  const args=['-displayfd','3','-screen','0','1024x768x24','-nolisten','tcp','-noreset','-ac'];let child;
  try{child=rawSpawn(binary.path,args,{stdio:['ignore',stdout,stderr,'pipe'],env:cleanChildEnvironment(process.env)});}finally{fs.closeSync(stdout);fs.closeSync(stderr);}
  const life=T.watchLifecycle(child,'display',()=>child.exitCode===null&&child.signalCode===null);
  state.display={argv:[binary.path,...args],binary,pid:child.pid,stopped:false,lifecycle:life.state};
  try{const display=await T.bounded(new Promise((resolve,reject)=>{let text='';child.once('error',reject);child.once('exit',()=>reject(Error('display exited during startup')));
      child.stdio[3].on('data',data=>{text+=data.toString('ascii');if(text.length>32)reject(Error('excessive display descriptor'));
        if(text.includes('\n')){if(!/^\d+\n$/.test(text))reject(Error('invalid display descriptor'));else resolve(':'+Number(text.trim()));}});}),10000,'owned display startup');
    const info=T.processInfo(child.pid);state.display.process=info;state.display.display=display;
    need(info.exe===binary.resolvedPath&&info.sha256===binary.sha256&&info.uid===host.uid&&info.netns===host.netns&&info.pidns===host.pidns,'display owner differs');
    return {child,info,display,life};
  }catch(error){life.requestCleanup();state.display.cleanup=await T.closeProcess(child,state.display.process);state.display.stopped=state.display.cleanup.stopped;throw error;}}
function eventJournal(file,{limit=1024**2,onFailure=()=>{}}={}){
  S.noSymlinks(path.dirname(file));const fd=fs.openSync(file,'wx',0o600),state={protocol:'r002f-bfcache-event-journal/1',
    limit,events:0,observedBytes:0,acknowledgedBytes:0,retainedBytes:null,closed:false,complete:false,error:null};let finished=false;
  // The failure callback records the fault directly; it must never append to this journal.
  function fail(error){if(!state.error){state.error=String(error.stack||error);onFailure(error);}state.complete=false;}
  function event(type,details){const row={type,hostNs:process.hrtime.bigint().toString(),...details};state.events++;
    try{const bytes=Buffer.from(JSON.stringify(row)+'\n');state.observedBytes+=bytes.length;
      if(finished)fail(Error('adapter event after journal finalization'));
      else if(state.observedBytes>limit)fail(Error('adapter event journal bound exceeded'));
      else if(!state.error){const written=S.writeOnce(fd,bytes);state.acknowledgedBytes+=written.acknowledgedBytes;if(written.error)fail(Error(written.error));}
    }catch(error){fail(error);}return row;}
  function finish(){if(finished)return state;finished=true;const final=S.finishFile(fd,file);state.closed=final.closed;state.identity=final.identity||null;
    state.retainedBytes=final.identity?.bytes??null;if(final.error)fail(Error(final.error));
    try{S.admitRetained(state.identity,state.observedBytes,state.acknowledgedBytes,state.retainedBytes,limit);}catch(error){fail(error);}
    state.complete=!state.error&&state.closed;return state;}
  return {event,finish,state};}
function admitJournal(row){need(row?.protocol==='r002f-bfcache-event-journal/1'&&row.complete===true&&row.closed===true&&!row.error&&
  row.limit===1024**2&&Number.isSafeInteger(row.events)&&row.events>0,'adapter event journal incomplete');
  S.admitRetained(row.identity,row.observedBytes,row.acknowledgedBytes,row.retainedBytes,row.limit);return true;}
function install(configPath){
  const configRead=S.readJson(configPath),config=configRead.value;
  need(config.protocol==='r002f-bfcache-child-config/1'&&config.native===true&&['baseline','candidate'].includes(config.label),'explicit native child configuration required');
  need(process.execPath===config.runtime.node&&process.argv[1]===path.join(S.ORIGINAL,'real-witness.cjs')&&
    S.same(process.argv.slice(2),[config.root,config.out,'chromium','bfcache',S.CLOCK,'3','--label='+config.label])&&
    process.env.PLAYWRIGHT_PKG===config.runtime.playwright&&process.env.R002F_BFCACHE_CHILD===configRead.identity.path&&
    process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT===config.isolationFile,'literal original child invocation differs');
  const env=cleanChildEnvironment(process.env);S.originalSources();admitChildSources(config);
  const toolsRead=S.readJson(config.toolsPath);config.tools=toolsRead.value;
  need(config.tools.protocol==='r002f-bfcache-tools/1'&&config.tools.status==='COMPLETE'&&S.same(config.tools.acquired.runtime,config.runtime),'tool/runtime admission differs');S.currentRecords(config.tools);
  const protectedRoots=[config.root,S.REPO,config.runtime.modules];for(const root of protectedRoots)need(config.out!==root&&!config.out.startsWith(root+'/')&&!root.startsWith(config.out+'/'),'output overlaps protected source');
  S.noSymlinks(config.out);const videoDir=S.recorderScope(config.out,config.label,path.join(config.out,'.video-'+config.label)),sink=S.returnSink(path.join(config.out,'returns'));
  const host=T.processInfo(process.pid),isolation=S.readJson(config.isolationFile);require('./r002f_tabhide_source.cjs').owners().validateIsolation(isolation.value,host);
  const state={protocol:'r002f-bfcache-adapter/1',status:'INCOMPLETE',label:config.label,...S.DISCLOSURE,host,config:configRead.identity,tools:toolsRead.identity,isolation:isolation.identity,
    phases:[],errors:[],boundaries:{},cleanup:{context:false,browser:false,browserPidsGone:false,recorder:false,display:false,servers:false},recorders:[],originalExitRequested:null};
  const raw={spawn:cp.spawn,write:fs.writeFileSync,copy:fs.copyFileSync,rm:fs.rmSync,exit:process.exit},recorderWaits=[],recorderLives=[];let display,browser,browserLife,contextLife,pageLife,guard,experimentClosed=false,envObject,drain=Promise.resolve(),decoder,videoPath,initialRemoved=false,finalRemoved=false,published=false;
  function recordFault(error){if(error.isolation===true)state.isolationFailure=true;const text=String(error.stack||error).slice(0,2000);if(state.errors.length<32)state.errors.push(text);else state.errorOverflow=true;return text;}
  const journal=eventJournal(path.join(config.out,'adapter-events.jsonl'),{onFailure:recordFault}),event=journal.event;
  function phase(name){need(Object.hasOwn(PHASES,name)&&!state.phases.some(x=>x.phase===name),'unknown/repeated adapter phase');const row=event('phase',{phase:name,seconds:PHASES[name]});state.phases.push(row);if(process.send)process.send({protocol:'r002f-bfcache-phase/1',...row});}
  function fault(error){const text=recordFault(error);if(!journal.state.error&&!journal.state.closed)event('fault',{message:text});}
  function finishFiles(){if(published)return;published=true;try{if(!sink.state.stopped)sink.finish();S.writeJson(path.join(config.out,'retention.json'),sink.state);}catch(error){fault(error);}
    let ready=false;
    try{state.returnRetention={received:sink.state.received,attempted:sink.state.attempted,errors:sink.state.errors.length,overflow:sink.state.overflow};
      state.cleanup.context=experimentClosed;state.cleanup.recorder=state.recorders.length===1&&state.recorders.every(x=>x.closed&&x.returncode===0&&!x.error);
      state.cleanup.browser=!!guard?.closed;state.directContexts=guard?.directContexts;state.browserLifecycle=browserLife?.state;state.contextLifecycle=contextLife?.state;state.pageLifecycle=pageLife?.state;
      state.cleanup.display=!!state.display?.stopped;
      if(config.tools.acquired.managed.chromium){state.finalCensus=processScan(config.tools.acquired.managed.chromium.resolvedPath);state.cleanup.browserPidsGone=state.finalCensus.complete&&state.finalCensus.rows.length===0;}
      const lifecycle=[browserLife,contextLife,pageLife,display?.life,...recorderLives].every(x=>x?.state.closed===true&&x.state.cleanupRequested===true&&x.state.faults.length===0&&!x.state.overflow);
      if(state.errors.length===0&&!state.errorOverflow&&Object.values(state.cleanup).every(x=>x===true)&&guard?.afterComplete&&lifecycle&&
        finalRemoved&&state.originalExitRequested===0&&sink.state.errors.length===0&&!sink.state.overflow&&decoder){decoder.finish();ready=true;}
    }catch(error){fault(error);}
    state.journal=journal.finish();
    if(ready&&state.errors.length===0&&!state.errorOverflow&&state.journal.complete)state.status='COMPLETE';
    try{S.writeJson(path.join(config.out,'adapter.json'),state);}
    catch(error){state.status='INCOMPLETE';recordFault(error);if(!fs.existsSync(path.join(config.out,'adapter.json')))S.writeJson(path.join(config.out,'adapter.json'),state);}}
  process.once('exit',finishFiles);process.on('uncaughtExceptionMonitor',fault);phase('admission');
  cp.spawn=function(command,args,options){
    const recorder=config.tools.acquired.managed.recorder;
    if(command===recorder.path||command===recorder.resolvedPath){need(state.recorders.length===0&&args?.length&&path.dirname(args.at(-1))===videoDir&&S.same(args,recorderArguments(args.at(-1))),'unexpected managed recorder invocation');S.requireRecord(recorder);
      const row={argv:[command,...args],output:args.at(-1),closed:false,returncode:null};state.recorders.push(row);const child=raw.spawn(command,args,options);row.pid=child.pid;
      const life=T.watchLifecycle(child,'recorder',()=>child.exitCode===null&&child.signalCode===null);recorderLives.push(life);row.lifecycle=life.state;
      try{row.process=T.processInfo(child.pid);need(row.process.uid===host.uid&&row.process.netns===host.netns&&row.process.pidns===host.pidns&&row.process.sha256===recorder.sha256,'recorder owner differs');}catch(error){row.error=String(error);fault(error);child.kill('SIGKILL');}
      child.on('error',error=>{row.error=String(error);fault(error);});recorderWaits.push(new Promise(resolve=>child.on('close',(code,signal)=>{row.closed=true;row.returncode=code;row.signal=signal;event('recorder-close',{pid:row.pid,code,signal});resolve();})));return child;}
    if(command==='ffmpeg'){need(!decoder&&videoPath&&experimentClosed&&guard?.closed,'original decoder order/recording differs');
      decoder=R.decoderGuard(config.tools,path.join(config.out,config.label+'.webm'),config.out,'original-decoder',{execute:raw.spawn,onClose:()=>{phase('judgment');}});
      return deferredChild(drain,()=>{phase('decoder');return decoder.spawn(command,args,options);});}
    return raw.spawn(command,args,options);};
  fs.rmSync=function(file,options){if(file!==videoDir)return raw.rm(file,options);need(S.same(options,{recursive:true,force:true}),'original recorder cleanup options differ');
    if(!initialRemoved){need(!fs.existsSync(videoDir),'preexisting recording directory refused');initialRemoved=true;event('recorder-initial-absent',{});return raw.rm(file,options);}
    need(!finalRemoved&&initialRemoved,'repeated original recorder cleanup');finalRemoved=true;
    if(fs.existsSync(videoDir)){S.noSymlinks(videoDir);need(fs.statSync(videoDir).uid===host.uid,'recorder directory ownership differs');const names=fs.readdirSync(videoDir);need(names.length===1,'recorder population is missing or excessive');
      const source=path.join(videoDir,names[0]);need(state.recorders[0]?.output===source,'actual recorder argv and directory disagree');
      const final=path.join(config.out,config.label+'.webm');
      try{need(videoPath===source,'actual page video path is missing or disagrees');const actual=S.record(source,{limit:S.LIMITS.videoBytes});
        need(fs.existsSync(final),'original final recording missing');const retained=S.record(final,{limit:S.LIMITS.videoBytes});
        need(retained.sha256===actual.sha256&&retained.bytes===actual.bytes,'original final WebM copy differs');state.recorderCopy={original:actual,retained};}
      catch(error){state.recorderPrefix=S.recorderPrefix(videoDir,source,path.join(config.out,config.label+'-unfinished-prefix.webm'));fault(error);}
    }else fault(Error('original recorder directory missing at final cleanup'));
    if(!state.phases.some(x=>x.phase==='judgment'))phase('judgment');return raw.rm(file,options);};
  fs.copyFileSync=function(from,to,flags){if(path.dirname(String(from))===videoDir||to===path.join(config.out,config.label+'.webm')){
      need(from===videoPath&&to===path.join(config.out,config.label+'.webm')&&flags===undefined&&!fs.existsSync(to),'original final-copy scope or freshness differs');const original=S.record(from,{limit:S.LIMITS.videoBytes});
      const result=raw.copy(from,to,flags),copied=S.record(to,{limit:S.LIMITS.videoBytes});need(copied.sha256===original.sha256&&copied.bytes===original.bytes,'original recorder copy bytes differ');return result;}
    return raw.copy(from,to,flags);};
  const legacy=new Set([config.label+'.json',config.label+'-ref-present.png',config.label+'-ref-absent.png',...[1,2,3].map(k=>config.label+'-restore'+k+'-first-shot.png')]);
  fs.writeFileSync=function(file,data,options){if(typeof file==='string'&&path.dirname(file)===config.out&&legacy.has(path.basename(file))){need(!fs.existsSync(file),'preexisting original result refused');
      if(file.endsWith('.png'))S.pngInfo(data);else need(Buffer.byteLength(data)<=S.LIMITS.metadataBytes,'original report metadata bound');return raw.write(file,data,{...typeof options==='object'?options:{},flag:'wx',mode:0o600});}
    return raw.write(file,data,options);};
  const iso=require(path.join(S.ORIGINAL,'iso.cjs')),create=iso.createEnv,launch=iso.launch;
  iso.createEnv=async options=>{need(options.root===config.root&&!envObject,'original loopback environment root differs');phase('display');display=await startDisplay(config,host,state,raw.spawn);phase('listeners');
    envObject=await create(options);state.loopbackPorts={...envObject.origins.ports,proxy:envObject.proxy.port};const finish=envObject.finish;
    envObject.finish=()=>{phase('serverDrain');const servers=[...envObject.origins.servers,envObject.proxy.server];need(servers.length===3,'original three listeners required');
      drain=T.bounded(Promise.all(servers.map(server=>new Promise(resolve=>server.once('close',resolve)))),15000,'original server drain').then(()=>{state.cleanup.servers=true;event('servers-closed',{});}).catch(error=>{fault(error);throw error;});drain.catch(()=>{});
      try{const result=finish();sink.value('isolation',result);return result;}
      catch(error){if(String(error.message).startsWith('ISOLATION FAILURE:'))error.isolation=true;fault(error);throw error;}};return envObject;};
  iso.launch=async(environment,options)=>{need(environment===envObject&&S.same(options,{engine:'chromium',mode:'route',headless:false,reducedMotion:'reduce',recordVideo:{dir:videoDir,size:{width:326,height:530}},ignoreDefaultArgs:['--disable-back-forward-cache']}),'original witness launch recipe differs');
    const playwright=require(config.runtime.playwright),originalLaunch=playwright.chromium.launch.bind(playwright.chromium),binary=config.tools.acquired.managed.chromium;
    need(playwright.chromium.executablePath()===binary.path,'managed Chromium executable lookup differs');const before=processScan(binary.resolvedPath);state.beforeCensus=before;
    const proxy={server:'http://127.0.0.1:'+environment.proxy.port,bypass:'<-loopback>'},expected={viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'Asia/Riyadh',locale:'en-US',reducedMotion:'reduce',serviceWorkers:'block',proxy,recordVideo:{dir:videoDir,size:{width:326,height:530}}};
    playwright.chromium.launch=async original=>{state.originalLaunch=original;const adapted=launchOptions(original,{proxy,executable:binary.path,display:display.display,env});state.adaptedLaunch=adapted;phase('launch');
      browser=await originalLaunch(adapted);browserLife=T.watchLifecycle(browser,'browser',()=>browser.isConnected());phase('owner');state.afterLaunchCensus=processScan(binary.resolvedPath);
      state.owner=owner(before,state.afterLaunchCensus,host,binary);const boundaryHost={...host,browserPid:state.owner.pid,executableSha256:binary.sha256};
      guard=await guardBrowser(browser,expected,{before:async b=>{phase('before');await strictBoundary(b,state.boundaries.before={},boundaryHost);phase('experiment');},
        after:async b=>{phase('after');need(T.sameLive(state.owner),'browser identity changed before final boundary');await strictBoundary(b,state.boundaries.after={},boundaryHost);},
        contextsClosed:()=>experimentClosed&&state.recorders.length===1&&state.recorders.every(r=>r.closed&&r.returncode===0&&!r.error),fault,
        closing:async()=>{phase('browserClose');browserLife.requestCleanup();},
        context:async context=>{let closed=false;contextLife=T.watchLifecycle(context,'context',()=>!closed);context.on('close',()=>{closed=true;});const originalClose=context.close.bind(context),newPage=context.newPage.bind(context);let pages=0;
          context.setDefaultTimeout=()=>{throw Error('original default timeout mutation refused');};context.setDefaultNavigationTimeout=()=>{throw Error('original default navigation timeout mutation refused');};
          context.close=async()=>{phase('contextClose');contextLife.requestCleanup();pageLife?.requestCleanup();for(const life of recorderLives)life.requestCleanup();try{await originalClose();await T.bounded(Promise.all(recorderWaits),90000,'actual recorder process closure');experimentClosed=closed;need(closed,'context API did not close');}catch(error){fault(error);throw error;}};
          context.newPage=async()=>{need(pages++===0,'extra experiment page refused');const page=await newPage();pageLife=T.watchLifecycle(page,'page',()=>!page.isClosed());
            const evaluate=page.evaluate.bind(page),screenshot=page.screenshot.bind(page),video=page.video.bind(page),stage={stateReads:0,hiddenReads:0,restoration:0,control:false};
            page.evaluate=async(fn,...args)=>{const name=evaluationKind(fn,stage),value=await evaluate(fn,...args);return name?sink.value(name,value):value;};
            page.screenshot=async options=>{need(S.same(options,{type:'png'}),'original screenshot options differ');return sink.capture(screenshot,options,stage.control?'ref-absent':stage.restoration?'restore-'+stage.restoration:'ref-present');};
            page.video=()=>{const value=video();need(value,'original page has no actual recording');const originalPath=value.path.bind(value);value.path=async()=>{need(!videoPath,'original video path requested twice');videoPath=await originalPath();need(path.dirname(videoPath)===videoDir,'page recording escaped owned directory');state.actualVideoPath=videoPath;return videoPath;};return value;};
            page.setDefaultTimeout=()=>{throw Error('page default timeout mutation refused');};page.setDefaultNavigationTimeout=()=>{throw Error('page default navigation timeout mutation refused');};return page;}}});return browser;};
    let L;try{L=await launch(environment,options);}catch(error){fault(error);if(!state.phases.some(x=>x.phase==='failureCleanup'))phase('failureCleanup');
      if(browser)try{if(guard)await guard.failureCleanup();else{browserLife?.requestCleanup();await T.bounded(browser.close(),60000,'early actual browser cleanup');}}catch(cleanup){fault(cleanup);}
      if(display)try{display.life.requestCleanup();state.display.cleanup=await T.closeProcess(display.child,display.info);state.display.stopped=state.display.cleanup.stopped;}catch(cleanup){fault(cleanup);}throw error;}
    const close=L.close;
    L.close=async()=>{try{return await close();}catch(error){fault(error);if(guard&&!guard.closed)try{await guard.failureCleanup();}catch(cleanup){fault(cleanup);}throw error;}
      finally{if(display)try{display.life.requestCleanup();const closed=await T.closeProcess(display.child,display.info);state.display.cleanup=closed;state.display.stopped=closed.stopped;}catch(error){fault(error);}}};return L;};
  process.exit=function(code){state.originalExitRequested=code;Promise.resolve(drain).catch(fault).then(async()=>{try{if(display&&!state.display.stopped){display.life.requestCleanup();const closed=await T.closeProcess(display.child,display.info);state.display.cleanup=closed;state.display.stopped=closed.stopped;}
      if(browser&&!guard?.closed){if(!state.phases.some(x=>x.phase==='failureCleanup'))phase('failureCleanup');await guard?.failureCleanup();}S.requireRecord(configRead.identity);S.requireRecord(toolsRead.identity);
    }catch(error){fault(error);}finally{finishFiles();raw.exit(code);}});};
  return state;
}
module.exports={ARGS,PHASES,ENV_KEYS,cleanChildEnvironment,expectedLaunch,launchOptions,guardBrowser,processScan,admitCensus,owner,strictBoundary,recorderArguments,deferredChild,evaluationKind,admitChildSources,eventJournal,admitJournal,install};
if(process.env.R002F_BFCACHE_CHILD)install(process.env.R002F_BFCACHE_CHILD);
