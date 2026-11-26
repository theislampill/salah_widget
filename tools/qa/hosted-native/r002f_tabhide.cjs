'use strict';
// One headed browser driver, source-bound research trees, private output only.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {spawn,execFileSync}=require('node:child_process');
const S=require('./r002f_tabhide_source.cjs'),R=require('./r002f_tabhide_runtime.cjs');
const F=require('./r002f_focus_owner.cjs');
const {need,sha}=S,ORIGIN_UTC=Date.parse('2026-09-07T00:10:05Z');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function bounded(promise,ms,label){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{
  timer=setTimeout(()=>reject(Error(label+' deadline exceeded')),ms);
})]);}finally{clearTimeout(timer);}}
function watchLifecycle(target,kind,isOpen){
  const state={protocol:'r002f-process-lifecycle/1',kind,cleanupRequested:false,closed:false,faults:[],overflow:false};
  const fault=(event,detail='')=>{
    if(state.faults.length<32)state.faults.push({event,detail:String(detail),hostNs:process.hrtime.bigint().toString()});
    else state.overflow=true;
  };
  target.on(kind==='browser'?'disconnected':'close',()=>{
    state.closed=true;if(!state.cleanupRequested)fault('unexpected-'+(kind==='browser'?'disconnected':'close'));
  });
  if(kind==='page')target.on('crash',()=>fault('crash'));
  return {state,fault,requestCleanup(){
    // Detect a close already visible through the API even if its event is
    // still queued. A later cleanup request cannot erase that earlier fault.
    if(state.closed||!isOpen())fault('closed-before-cleanup-request');
    state.cleanupRequested=true;
  }};
}
function parse(argv){
  const options={engine:'chromium',dpr:1,rounds:1,section:'all',timeoutMs:180000};
  const allowed=new Set(['playwright','baseline','candidate','out','engine','dpr','rounds','section','timeout-ms']);
  const seen=new Set();for(let i=0;i<argv.length;i+=2){
    const key=argv[i]?.slice(2);need(argv[i]?.startsWith('--')&&allowed.has(key)&&!seen.has(key)&&argv[i+1]&&!argv[i+1].startsWith('--'),'unknown, repeated or missing argument');
    seen.add(key);options[key==='timeout-ms'?'timeoutMs':key]=['dpr','rounds','timeout-ms'].includes(key)?Number(argv[i+1]):argv[i+1];
  }
  need(options.engine==='chromium'&&options.dpr===1&&options.rounds===1&&options.section==='all'&&options.timeoutMs===180000,
    'headed route is one Chromium DPR1 pair with the reviewed 180000 ms maturity bound');
  for(const key of ['playwright','baseline','candidate','out']){need(typeof options[key]==='string','missing --'+key);options[key]=path.resolve(options[key]);}
  return options;
}
function processInfo(pid){
  const root='/proc/'+pid,status=fs.readFileSync(root+'/status','utf8'),stat=fs.readFileSync(root+'/stat','utf8');
  const fields=stat.slice(stat.lastIndexOf(')')+2).trim().split(/\s+/),exe=fs.readlinkSync(root+'/exe');
  return {pid,uid:Number(/^Uid:\s+(\d+)/m.exec(status)?.[1]),netns:fs.readlinkSync(root+'/ns/net'),
    pidns:fs.readlinkSync(root+'/ns/pid'),startTicks:fields[19],exe,sha256:S.identity(exe).sha256,
    argv:fs.readFileSync(root+'/cmdline','utf8').split('\0').filter(Boolean)};
}
function sameLive(info){try{const stat=fs.readFileSync('/proc/'+info.pid+'/stat','utf8');
  return stat.slice(stat.lastIndexOf(')')+2).trim().split(/\s+/)[19]===info.startTicks;}catch(e){if(e.code==='ENOENT')return false;throw e;}}
async function closeProcess(child,info){
  if(!child)return {stopped:true};let exit;
  const ended=new Promise(resolve=>{child.once('close',(code,signal)=>{exit={code,signal};resolve();});});
  if(child.exitCode!==null||child.signalCode!==null)exit={code:child.exitCode,signal:child.signalCode};
  if(!exit){child.kill('SIGTERM');try{await bounded(ended,2000,'display termination');}
    catch{if(!info||sameLive(info))child.kill('SIGKILL');await bounded(ended,2000,'display kill/wait');}}
  return {stopped:!info||!sameLive(info),exit:exit??{code:child.exitCode,signal:child.signalCode}};
}
async function startDisplay(out,host){
  const executable=fs.realpathSync('/usr/bin/Xvfb');S.regular(executable);
  const packageText=execFileSync('/usr/bin/dpkg-query',['-W','-f=${Status}\t${Version}\n','xvfb'],{encoding:'utf8',timeout:5000,maxBuffer:4096}).trim();
  const [packageStatus,version]=packageText.split('\t');need(packageStatus==='install ok installed'&&version,'installed Xvfb package required');
  const stdout=fs.openSync(path.join(out,'xvfb.stdout'),'wx',0o600),stderr=fs.openSync(path.join(out,'xvfb.stderr'),'wx',0o600);
  let child,info;try{
    child=spawn(executable,['-displayfd','3','-screen','0','1024x768x24','-nolisten','tcp','-noreset','-ac'],
      {stdio:['ignore',stdout,stderr,'pipe'],env:{...process.env}});
  }finally{fs.closeSync(stdout);fs.closeSync(stderr);}
  try{
    const display=await bounded(new Promise((resolve,reject)=>{
      let data='';child.once('error',reject);child.once('exit',()=>reject(Error('display exited during startup')));
      child.stdio[3].on('data',bytes=>{data+=bytes.toString('ascii');if(data.length>32)reject(Error('excessive display descriptor'));
        if(data.includes('\n')){if(!/^\d+\n$/.test(data))reject(Error('invalid display descriptor'));else resolve(':'+Number(data.trim()));}});
    }),10000,'display startup');
    info=processInfo(child.pid);need(info.uid===host.uid&&info.netns===host.netns&&info.pidns===host.pidns&&info.exe===executable,
      'display process escaped current identity');
    return {child,record:{package:'xvfb',version,packageStatus,executable,display,process:info,stopped:false}};
  }catch(error){await closeProcess(child,info);throw error;}
}
function browserPids(executable){
  return fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x)).flatMap(value=>{
    try{return fs.readlinkSync('/proc/'+value+'/exe')===executable?[Number(value)]:[];}catch(e){if(['ENOENT','EACCES'].includes(e.code))return [];throw e;}
  });
}
function mainBrowserArgv(argv,executable){
  // Chromium children may flatten their title into argv[0]. Never reconstruct
  // that title as a main argv or split whitespace inside ordinary values.
  return Array.isArray(argv)&&typeof executable==='string'&&executable.length>0&&argv[0]===executable&&
    !argv.some(arg=>typeof arg!=='string'||arg==='--type'||arg.startsWith('--type='));
}
function processCensus(executable,io=fs){
  // Failure-only private diagnostics. Partial reads are retained as partial;
  // this snapshot never selects a PID or replaces the original owner guard.
  const limits={processes:256,cmdlineBytes:16384,statusBytes:4096,statBytes:4096,linkCharacters:4096,readOperations:64};
  const errorCode=error=>String(error?.code||'UNKNOWN').slice(0,64);
  const link=name=>{try{const value=io.readlinkSync(name);return {value:value.slice(0,limits.linkCharacters),truncated:value.length>limits.linkCharacters};}
    catch(error){return {errorCode:errorCode(error)};}};
  const read=(name,maximum)=>{
    const row={complete:false,eof:false,truncated:null,readCalls:0,bytesRead:0};let fd;
    const buffer=Buffer.alloc(maximum+1);
    try{fd=io.openSync(name,'r');
      while(row.bytesRead<buffer.length&&row.readCalls<limits.readOperations){
        row.readCalls++;
        const n=io.readSync(fd,buffer,row.bytesRead,buffer.length-row.bytesRead,row.bytesRead);
        if(!Number.isInteger(n)||n<0||n>buffer.length-row.bytesRead)
          throw Object.assign(Error('invalid proc read count'),{code:'INVALID_READ_COUNT'});
        if(n===0){row.eof=true;row.complete=true;row.truncated=false;break;}
        row.bytesRead+=n;
      }
      if(row.bytesRead>maximum)row.truncated=true;
      if(!row.eof&&row.truncated!==true&&row.readCalls===limits.readOperations)row.readLimitReached=true;
    }
    catch(error){row.errorCode=errorCode(error);}
    finally{if(fd!==undefined){
      row.value=buffer.subarray(0,Math.min(row.bytesRead,maximum)).toString('utf8');
      try{io.closeSync(fd);}catch(error){row.closeErrorCode=errorCode(error);}
    }}
    return row;
  };
  const result={protocol:'r002f-headed-process-census/1',authority:'diagnostic-only; does not select or admit a browser owner',
    expectedExecutable:executable,startedHostNs:process.hrtime.bigint().toString(),limits,
    observer:{pid:process.pid,uid:process.getuid?.()??null,netns:link('/proc/self/ns/net'),pidns:link('/proc/self/ns/pid')},rows:[]};
  try{
    const ids=io.readdirSync('/proc').filter(value=>/^\d+$/.test(value)).map(Number)
      .filter(value=>Number.isSafeInteger(value)&&value>0).sort((a,b)=>a-b);
    result.enumeration={numericEntries:ids.length,retainedEntries:Math.min(ids.length,limits.processes),truncated:ids.length>limits.processes};
    for(const pid of ids.slice(0,limits.processes)){
      const root='/proc/'+pid;result.rows.push({pid,exe:link(root+'/exe'),
        cmdline:read(root+'/cmdline',limits.cmdlineBytes),status:read(root+'/status',limits.statusBytes),
        stat:read(root+'/stat',limits.statBytes),netns:link(root+'/ns/net'),pidns:link(root+'/ns/pid')});
    }
  }catch(error){result.enumeration={errorCode:errorCode(error)};}
  result.endedHostNs=process.hrtime.bigint().toString();return result;
}
async function boundary(browser,report,host){
  const marker=crypto.randomBytes(24).toString('hex'),before=new Set(browser.contexts());let hits=0,server;
  Object.assign(report,{protocol:'salah-hosted-browser-boundary/1',passed:false,headless:false,chromiumSandbox:true,
    uid:host.uid,netns:host.netns,browserPid:host.browserPid,executableSha256:host.executableSha256,contextsClosed:false});
  try{
    server=http.createServer((req,res)=>{hits++;res.end(marker);});
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    const origin='http://127.0.0.1:'+server.address().port,page=await browser.newPage({serviceWorkers:'block'});
    await page.goto(origin+'/before',{timeout:10000});need(await page.textContent('body')===marker,'headed loopback marker missing');
    // This is the exact published negative-control body, with no route stubs.
    await require('./browser-control.cjs').refuseExternalThenReadLoopback(browser,page,origin,marker,report);
    need(hits>=2,'headed post-negative marker missing');report.loopbackRequests=hits;report.passed=true;
  }catch(error){report.error=String(error.stack||error);throw Object.assign(error,{isolation:true});}
  finally{
    try{for(const context of browser.contexts())if(!before.has(context))await bounded(context.close(),10000,'boundary context cleanup');report.contextsClosed=true;}
    catch(error){report.passed=false;throw Object.assign(error,{isolation:true});}
    finally{if(server)await bounded(new Promise(resolve=>server.close(resolve)),5000,'boundary server cleanup');}
  }
}
function ledger(){return {requests:[],unexpected:[],errors:[],overflow:false,veto:false};}
function record(log,key,row){if(log[key].length<S.LIMITS.requests)log[key].push(row);else log.overflow=true;}
async function continueLocal(route,origin,log){
  if(new URL(route.request().url()).origin!==origin){log.veto=true;throw Object.assign(Error('external continuation vetoed before continue'),{veto:true});}
  return route.continue();
}
async function serve(root,source,log){
  const allowed=new Set([...source.files.map(row=>'/'+row.path),...Object.keys(source.assets).map(name=>'/'+name)]);
  const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.wasm':'application/wasm'};
  const server=http.createServer((request,response)=>{
    try{
      const url=new URL(request.url,'http://127.0.0.1'),name=decodeURIComponent(url.pathname);need(allowed.has(name),'unadmitted static path');
      const file=S.regular(S.relative(root,name.slice(1)));record(log,'requests',{path:name,status:200});
      response.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});
      fs.createReadStream(file).on('error',()=>response.destroy()).pipe(response);
    }catch{record(log,'requests',{path:request.url,status:404});response.writeHead(404);response.end();}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  return {server,origin:'http://127.0.0.1:'+server.address().port};
}
async function openScene(browser,origin,P,focusRuntime,retain){
  const log=ledger(),started=process.hrtime.bigint(),utc=()=>ORIGIN_UTC+Number(process.hrtime.bigint()-started)/1e6;
  const context=await browser.newContext({viewport:{width:400,height:650},deviceScaleFactor:1,timezoneId:'UTC',reducedMotion:'no-preference',serviceWorkers:'block'});
  const scene={context,browser,focusRuntime,ledger:log,pageErrors:[],closed:false};
  // Publish the acquired context before any setup await. The arm owns cleanup
  // and retention even when navigation or observer installation never returns.
  retain(scene);context.on('close',()=>{scene.closed=true;});
  scene.contextLifecycle=watchLifecycle(context,'context',()=>!scene.closed);
    context.setDefaultTimeout(30000);await context.addInitScript(R.installClock,ORIGIN_UTC);
    await context.route('**/*',async route=>{
      const url=new URL(route.request().url());let action;
      const json=value=>route.fulfill({status:200,headers:{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},body:JSON.stringify(value)});
      try{
        if(url.origin===origin){action='loopback';await continueLocal(route,origin,log);}
        else if(url.protocol==='https:'&&url.hostname==='api.aladhan.com'&&/^\/v1\/timings\//.test(url.pathname)){
          const value=P.fixturePrayer(url);action=value?'prayer-fixture':'prayer-successor-unavailable';
          if(value)await json(value);else await route.fulfill({status:503,body:'disclosed fixture has no additional day'});
        }else if(url.protocol==='https:'&&url.hostname==='api.open-meteo.com'&&url.pathname==='/v1/forecast'){action='weather-fixture';await json(P.fixtureWeather(utc()));}
        else if(url.protocol==='https:'&&url.hostname==='api.rainviewer.com'&&url.pathname==='/public/weather-maps.json'){
          action='empty-radar-fixture';await json({version:'2.0',generated:Math.floor(utc()/1000),host:'https://tilecache.rainviewer.com',radar:{past:[],nowcast:[]}});
        }else if(url.protocol==='https:'&&['fonts.googleapis.com','fonts.gstatic.com'].includes(url.hostname)){
          action='optional-font-unavailable';await route.fulfill({status:200,contentType:'text/css',body:''});
        }else{action='unexpected-aborted';record(log,'unexpected',url.href);await route.abort('blockedbyclient');}
      }catch(error){action='route-error';record(log,'errors',String(error.message));if(error.veto)log.veto=true;try{await route.abort();}catch{}}
      record(log,'requests',{url:url.href,action});
    });
    need(typeof context.routeWebSocket==='function','WebSocket guard unavailable');
    await context.routeWebSocket('**/*',socket=>{record(log,'unexpected',socket.url());record(log,'requests',{url:socket.url(),action:'websocket-aborted'});socket.close();});
    const page=scene.page=await context.newPage();
    scene.pageLifecycle=watchLifecycle(page,'page',()=>!page.isClosed());
    page.on('pageerror',error=>{scene.pageLifecycle.fault('pageerror',error.stack||error);
      if(scene.pageErrors.length<32)scene.pageErrors.push(String(error.stack||error));});
    scene.focus=F.preparation('scene');
    scene.focusOwner=await F.prepare(page,context,browser,focusRuntime,scene.focus);
    const fragment='lat=24.47&lon=39.61&label=R002F%20research&method=4&school=0&tz=UTC&time=24&units=c&datefmt=YYYY-MM-DD';
    const response=await page.goto(origin+'/index.html#'+fragment,{waitUntil:'domcontentloaded',timeout:30000});
    need(response?.ok(),'generated document failed to load');scene.servedIndexSha256=sha(await response.body());scene.fragment=fragment;
    await page.evaluate(R.installObserver,P.readPrayerDom.toString());return scene;
}
async function waitMature(page,timeout){
  await page.waitForFunction(()=>{
    const m=window.SalahMoonRuntime?.observe(),s=window.realSkyState?.(),c=document.querySelector('.c');
    return !document.hidden&&!c?.classList.contains('paused')&&c?.classList.contains('real-sky-composed')&&s?.status==='ready'&&s.physical===true&&s.displayed?.identity&&
      s?.last?.physicalState?.sun?.altDeg<-12&&m?.current&&m.accepted&&m.state?.visibleSource==='refined-terrain'&&m.state.quality==='empirical-adaptive';
  },null,{timeout,polling:250});
}
async function still(page,folder,name,boundary){
  const raw=await page.screenshot({type:'png',animations:'allow',timeout:15000});
  const info=S.pngInfo(raw);S.writeBytes(path.join(folder,name),raw);return {file:name,boundary,...info};
}
async function schedule(scene,arm,mode,folder){
  fs.mkdirSync(folder,{mode:0o700});const page=scene.page;
  const row={protocol:'r002f-tabhide-row/1',arm,mode,route:'headed-chromium-bringToFront',completed:false,
    contextClosed:false,cleanupError:null,error:null,servedIndexSha256:scene.servedIndexSha256,fragment:scene.fragment,
    frameBoundary:'first CDP PNG packet received after activation request began; not first displayed frame',
    intendedHoldMs:250,clockDomains:{page:'performance.now milliseconds',host:'hrtime bigint nanoseconds',cdp:'raw screencast metadata timestamp; never subtracted from page clock'},
    visibilityDiagnostics:F.diagnostics(scene.focus)};
  let session,sink,phase='before-action',cover,coverOwner,removeVisibilityListener,recording=false;
  try{
    await page.bringToFront();await waitMature(page,180000);
    row.clockCheck=await page.evaluate(R.verifyClock);
    await page.evaluate(mode=>__r002fTabObserver.begin(mode),mode);row.before=await page.evaluate(()=>__r002fTabObserver.snapshot());S.mature(row.before);
    row.stills={setup:await still(page,folder,'setup.png','mature setup before this schedule')};
    await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'before-capture');
    session=await scene.context.newCDPSession(page);sink=S.frameSink(folder,id=>session.send('Page.screencastFrameAck',{sessionId:id}));
    session.on('Page.screencastFrame',event=>{void sink.accept(event,phase);});
    removeVisibilityListener=F.listenScreencast(session,row.visibilityDiagnostics,()=>phase);
    await session.send('Page.startScreencast',{format:'png',everyNthFrame:1});recording=true;
    await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'after-capture-start');
    await delay(250);await page.evaluate(()=>__r002fTabObserver.trigger());row.actionHostNs=process.hrtime.bigint().toString();
    if(mode==='tabhide'){
      // A real second tab becomes active. It is served by no network request.
      cover=await scene.context.newPage();row.visibilityDiagnostics.cover=F.preparation('cover');
      coverOwner=await F.prepare(cover,scene.context,scene.browser,scene.focusRuntime,row.visibilityDiagnostics.cover);
      F.admitCover(scene.focus,row.visibilityDiagnostics.cover);
      await cover.bringToFront();phase='hidden-requested';
      await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'cover-front',coverOwner);
      await page.waitForFunction(()=>document.hidden&&document.querySelector('.c')?.classList.contains('paused'),null,{timeout:10000,polling:50});
      await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'hidden-confirmed',coverOwner);
    }
    await delay(250);phase='activation-requested';row.activationHostNs=process.hrtime.bigint().toString();
    await page.bringToFront();
    await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'after-return-front',coverOwner);
    if(mode==='no-hide')await page.evaluate(()=>__r002fTabObserver.completeControl());
    await page.waitForFunction(()=>__r002fTabObserver.read()?.marks.some(x=>x.name==='raf-2'),null,{timeout:30000,polling:50});
    await delay(1200);await session.send('Page.stopScreencast');recording=false;
    await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'after-capture-stop',coverOwner);
    // Drain all received packets before detaching so acknowledgements remain
    // valid. Detachment closes this capture route before final retention ends.
    await sink.finish();await session.detach();session=null;
    row.capture=await sink.finish();row.firstCapturedFrame=row.capture.frames.find(x=>x.phase==='activation-requested')?.file??null;
    await waitMature(page,120000);row.settled=await page.evaluate(()=>__r002fTabObserver.settled());
    row.lifecycle=await page.evaluate(()=>__r002fTabObserver.read());
    row.stills.settled=await still(page,folder,'settled.png','later settled refined state; not first presented frame');row.completed=true;
  }catch(error){row.error=String(error.stack||error);
    try{await F.snapshot(scene.focusOwner,row.visibilityDiagnostics,'failure',coverOwner);}
    catch(diagnosticError){row.visibilityReadError=String(diagnosticError.stack||diagnosticError);}}
  finally{
    if(recording&&session)try{await session.send('Page.stopScreencast');}catch(error){row.captureStopError=String(error);row.completed=false;}
    removeVisibilityListener?.();
    try{if(!row.lifecycle)row.lifecycle=await page.evaluate(()=>__r002fTabObserver.read());}catch(error){row.lifecycleReadError=String(error);}
    if(cover)try{await bounded(cover.close(),10000,'cover cleanup');}catch(error){row.coverCleanupError=String(error);row.completed=false;}
    if(session)try{await session.detach();}catch(error){row.sessionCleanupError=String(error);row.completed=false;}
    if(sink){row.capture=await sink.finish();row.firstCapturedFrame=row.capture.frames.find(x=>x.phase==='activation-requested')?.file??null;}
    // The prefix exists before context/browser cleanup and survives a later
    // timeout. Its final admission is written separately, after that cleanup.
    S.writeJson(path.join(folder,'partial.json'),row);
  }
  return row;
}
async function arm(browser,site,name,out,P,focusRuntime){
  const rows=[];let scene,setupError=null,cleanupError=null;
  try{
    await openScene(browser,site.origin,P,focusRuntime,acquired=>{scene=acquired;});
    need(scene.servedIndexSha256===(name==='baseline'?P.BASE_INDEX:P.COMBINED_INDEX),'served source mismatch');
    for(const mode of ['no-hide','tabhide']){
      const row=await schedule(scene,name,mode,path.join(out,name+'-'+mode));rows.push(row);
      if(!row.completed)break;
    }
  }catch(error){setupError=String(error.stack||error);rows.push({protocol:'r002f-tabhide-row/1',arm:name,mode:'setup',error:setupError,completed:false,
    visibilityDiagnostics:scene?.focus?F.diagnostics(scene.focus):null});}
  finally{if(scene)try{scene.pageLifecycle?.requestCleanup();scene.contextLifecycle?.requestCleanup();
    await bounded(scene.context.close(),15000,'arm context cleanup');}catch(error){cleanupError=String(error);}}
  const entries=[];for(const row of rows){
    row.contextClosed=scene?.closed===true;row.cleanupError=cleanupError;row.ledger=scene?.ledger??ledger();row.pageErrors=scene?.pageErrors??[];
    row.lifecycleCustody={page:scene?.pageLifecycle?.state??null,context:scene?.contextLifecycle?.state??null};
    let verdict;try{verdict=S.admitRow(row);F.admitRowDiagnostics(row);}catch(error){verdict={status:'INCOMPLETE',reason:String(error.message)};}
    const name=row.arm+'-'+row.mode,file=name+'/row.json';
    if(!fs.existsSync(path.join(out,name)))fs.mkdirSync(path.join(out,name),{mode:0o700});
    S.writeJson(path.join(out,file),row);entries.push({arm:row.arm,mode:row.mode,file,sha256:S.identity(path.join(out,file)).sha256,verdict});
  }
  return {entries,closed:scene?.closed===true&&!cleanupError,veto:scene?.ledger.veto===true,
    lifecycleCustody:{arm:name,setupError,cleanupError,page:scene?.pageLifecycle?.state??null,context:scene?.contextLifecycle?.state??null,pageErrors:scene?.pageErrors??[]}};
}
function nativeIsolation(isolationFile,P){
  try{
    need(isolationFile,'native isolation receipt required before browser/display setup');
    const isolation=JSON.parse(S.body(isolationFile)),host={uid:process.getuid?.(),netns:fs.readlinkSync('/proc/self/ns/net'),pidns:fs.readlinkSync('/proc/self/ns/pid')};
    P.validateIsolation(isolation,host);return {isolationFile,host};
  }catch(error){error.isolation=true;throw error;}
}
function admitFinal(report,root,options){
  // The original lifecycle, isolation, source and lossless PNG oracle runs first.
  // Additional explicit harness-input receipts can only refuse, never substitute.
  const verdict=S.admitReport(report,root,options);F.validateRuntimeRecord(report.focusRuntime);
  for(const entry of report.rows){const row=JSON.parse(S.body(S.relative(root,entry.file)));
    F.admitRowDiagnostics(row);need(JSON.stringify(row.visibilityDiagnostics.scene.runtime)===JSON.stringify(report.focusRuntime),
      'row focus source differs from admitted runtime');}
  return verdict;
}
async function main(argv){
  if(argv[0]==='--verify-json'){
    need(argv.length===5,'offline verification needs report, baseline, candidate and current isolation receipt');
    const report=JSON.parse(S.body(argv[1]));console.log(JSON.stringify(admitFinal(report,path.dirname(path.resolve(argv[1])),
      {baseline:argv[2],candidate:argv[3],isolationFile:argv[4]})));return;
  }
  if(argv[0]==='--admit-generated'){
    need(argv.length===3,'generated admission needs two source roots');const P=S.owners();
    console.log(JSON.stringify({sourceManifest:S.admitSources(),sourceManifestSha256:S.identity(path.join(__dirname,'r002f-tabhide-pins.json')).sha256,
      baseline:S.generated(argv[1],P.BASE_INDEX),candidate:S.generated(argv[2],P.COMBINED_INDEX)}));return;
  }
  const options=parse(argv),manifest=S.admitSources(),P=S.owners();
  const {isolationFile,host}=nativeIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT,P);
  S.privateRoot(options.out,[options.baseline,options.candidate,options.playwright,path.resolve(__dirname,'../../..')]);
  const report={protocol:'r002f-tabhide-native/1',status:'INCOMPLETE',engine:'chromium',dpr:1,rounds:1,section:'all',route:'tabhide',headless:false,
    sourceManifest:manifest,sourceManifestSha256:S.identity(path.join(__dirname,'r002f-tabhide-pins.json')).sha256,
    host,isolation:{file:path.resolve(isolationFile),sha256:S.identity(isolationFile).sha256},errors:[],rows:[],boundaries:{},continuationVetoed:false,
    budget:S.BUDGET,armLifecycles:[],
    cleanup:{contexts:false,browser:false,servers:false,xvfb:false,browserPidsGone:false},
    nativeQualification:'LIFECYCLE_OBSERVATION_ONLY',humanAcceptance:'OUTSTANDING',
    limitations:['Synthetic disclosed UTC prayer/weather fixtures; original physical sky and lunar owners execute unchanged.',
      'The visible no-hide schedule precedes real hide in each same context; no randomized causal performance estimate.',
      'Translated Date runs at 1x. Native callbacks and performance remain unchanged; product 0.0416 px and 1000 ms fences remain unchanged.',
      'CDP PNG packets are retained losslessly in received order. First received after activation is not first displayed or a physical-device cadence.',
      F.INPUT+'. This private version/source-bound harness input is recorded separately; native hidden/visible transitions remain required.',
      'No bfcache, changed-scene/weather-expiry, memory/GC, owner-tier policy, human visual or full R002F acceptance claim.',
      'Original combined Moon result 244/248 and both RES/G8 policy conflicts remain unchanged.']};
  let display,browser,browserLifecycle,browserProcess,executable,prior,ownerAdmitted=false;const sites=[];
  try{
    report.sources={baseline:S.generated(options.baseline,P.BASE_INDEX),candidate:S.generated(options.candidate,P.COMBINED_INDEX)};
    const pkg=JSON.parse(S.body(path.join(options.playwright,'package.json')));need(pkg.version==='1.62.1','unexpected Playwright version');
    const playwright=require(options.playwright),focusRuntime=F.runtime(options.playwright,playwright);report.focusRuntime=focusRuntime.record;
    executable=fs.realpathSync(playwright.chromium.executablePath());
    report.playwright={version:pkg.version,executablePath:executable,executableSha256:S.identity(executable).sha256,headless:false,chromiumSandbox:true};
    display=await startDisplay(options.out,host);report.xvfb=display.record;
    prior=new Set(browserPids(executable));
    report.browserOwnerSelection={protocol:'r002f-headed-owner-selection/1',priorPids:[...prior],phase:'before-launch',admitted:false};
    browser=await playwright.chromium.launch({headless:false,chromiumSandbox:true,executablePath:executable,timeout:30000,
      env:{...process.env,DISPLAY:display.record.display}});
    browserLifecycle=watchLifecycle(browser,'browser',()=>browser.isConnected());report.browserLifecycle=browserLifecycle.state;
    const main=[];
    report.browserOwnerSelection.phase='postlaunch-enumeration';
    const observed=browserPids(executable);report.browserOwnerSelection.observedPids=observed;
    Object.assign(report.browserOwnerSelection,{mainPids:[],attemptedPids:[],candidateErrors:[],candidateScanComplete:false});
    for(const pid of observed)if(!prior.has(pid)){
      report.browserOwnerSelection.currentPid=pid;report.browserOwnerSelection.phase='candidate-cmdline';
      report.browserOwnerSelection.attemptedPids.push(pid);
      try{const argv=fs.readFileSync('/proc/'+pid+'/cmdline','utf8').split('\0');
        if(mainBrowserArgv(argv,executable)){
          report.browserOwnerSelection.phase='candidate-identity';main.push(processInfo(pid));
          report.browserOwnerSelection.mainPids.push(pid);
        }
      }catch(error){
        report.browserOwnerSelection.candidateErrors.push({pid,phase:report.browserOwnerSelection.phase,errorCode:String(error?.code||'UNKNOWN').slice(0,64)});
        if(error.code!=='ENOENT')throw error;
      }
    }
    report.browserOwnerSelection.candidateScanComplete=true;delete report.browserOwnerSelection.currentPid;
    report.browserOwnerSelection.phase='exact-one-owner';
    need(main.length===1,'one actual headed browser owner required');browserProcess=main[0];report.browserProcess=browserProcess;
    report.browserOwnerSelection.phase='owner-identity';
    need(browserProcess.exe===executable&&browserProcess.sha256===report.playwright.executableSha256&&
      mainBrowserArgv(browserProcess.argv,executable)&&
      browserProcess.uid===host.uid&&browserProcess.netns===host.netns&&browserProcess.pidns===host.pidns&&
      !browserProcess.argv.some(x=>x==='--no-sandbox'||x.startsWith('--headless')),'headed process identity differs');
    ownerAdmitted=true;report.browserOwnerSelection.admitted=true;report.browserOwnerSelection.phase='admitted';
    host.browserPid=browserProcess.pid;report.browserVersion=browser.version();
    const boundaryHost={...host,executableSha256:report.playwright.executableSha256};
    await boundary(browser,report.boundaries.before={},boundaryHost);
    let contexts=true;
    for(const name of ['baseline','candidate']){
      const staticLog=ledger(),site=await serve(options[name],report.sources[name],staticLog);sites.push(site);
      const result=await arm(browser,site,name,options.out,P,focusRuntime);report.rows.push(...result.entries);
      report.armLifecycles.push(result.lifecycleCustody);
      contexts=contexts&&result.closed;report.continuationVetoed=report.continuationVetoed||result.veto;
      S.writeJson(path.join(options.out,name+'-served.json'),staticLog);
      if(result.veto)break;
    }
    report.cleanup.contexts=contexts;
    await boundary(browser,report.boundaries.after={},boundaryHost);
    report.status=report.continuationVetoed?'EXTERNAL_CONTINUATION_VETOED':
      report.rows.length===4&&report.rows.every(row=>row.verdict.status==='OBSERVED')?S.STATUS:'INCOMPLETE';
  }catch(error){report.errors.push(String(error.stack||error));report.status=error.isolation?'ISOLATION_FAIL':'INCOMPLETE';
    if(browser&&!ownerAdmitted&&executable)try{report.ownerFailureProcessCensus=processCensus(executable);}
      catch(diagnosticError){report.ownerFailureProcessCensus={protocol:'r002f-headed-process-census/1',error:String(diagnosticError.stack||diagnosticError)};}
  }
  finally{
    if(browser)try{browserLifecycle.requestCleanup();await bounded(browser.close(),15000,'browser cleanup');report.cleanup.browser=!browser.isConnected();}
      catch(error){report.errors.push('browser cleanup: '+error);}
    if(browserProcess){
      const owned=()=>browserPids(executable).filter(pid=>!prior.has(pid));
      for(let i=0;i<100&&owned().length;i++)await delay(20);
      report.cleanup.browserPidsGone=owned().length===0;
    }
    try{for(const site of sites)await bounded(new Promise(resolve=>site.server.close(resolve)),5000,'server cleanup');report.cleanup.servers=true;}
      catch(error){report.errors.push('server cleanup: '+error);}
    if(display)try{const closed=await closeProcess(display.child,display.record.process);Object.assign(report.xvfb,closed);report.cleanup.xvfb=closed.stopped;}
      catch(error){report.errors.push('display cleanup: '+error);}
    if(report.ownerFailureProcessCensus&&executable)try{report.afterCleanupProcessCensus=processCensus(executable);}
      catch(diagnosticError){report.afterCleanupProcessCensus={protocol:'r002f-headed-process-census/1',error:String(diagnosticError.stack||diagnosticError)};}
    if(report.status===S.STATUS)try{admitFinal(report,options.out,{...options,isolationFile});}
      catch(error){report.errors.push('final admission: '+error);report.status='INCOMPLETE';}
    S.writeJson(path.join(options.out,'result.json'),report);
  }
  console.log('R002F_TABHIDE '+report.status);
  process.exitCode=report.status===S.STATUS?0:report.status==='FAIL'?1:
    ['ISOLATION_FAIL','EXTERNAL_CONTINUATION_VETOED'].includes(report.status)?86:2;
}
module.exports={parse,processInfo,sameLive,closeProcess,mainBrowserArgv,processCensus,continueLocal,record,ledger,bounded,watchLifecycle,arm,nativeIsolation,admitFinal,main};
if(require.main===module)main(process.argv.slice(2)).catch(error=>{
  console.error('R002F_TABHIDE '+(error.isolation?'ISOLATION_FAIL':'INCOMPLETE')+': '+error.message);process.exitCode=error.isolation?86:2;
});
