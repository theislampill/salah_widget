'use strict';
// Private Playwright 1.62.1 adapter. It removes an existing harness override on
// its original owning session; it never sets DOM visibility or emits lifecycle events.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const RUNTIME_PROTOCOL='r002f-playwright-owner-source/1',CHROMIUM_VERSION='151.0.7922.34';
const INPUT='Playwright focus emulation disabled on its original owning session; genuine visibility remains required';
const LIMITS=Object.freeze({callMs:2500,snapshots:7,visibilityEvents:32,setupPages:4,setupCommands:3});
const SOURCE_FILES=Object.freeze(Object.fromEntries(Object.entries({
  'playwright/package.json':{bytes:1416,sha256:'ca170ec143a88ed3043ac953eb3b2377b2b97304104f4e1e23316684ce2c35af'},
  'playwright/index.js':{bytes:648,sha256:'4e98f65f0a9d9bcab8cffc0c5cfdd87fd3f5b0be74fc494ff166a466b204cd44'},
  'playwright-core/package.json':{bytes:876,sha256:'07c47543631fef9508760365dee9fbe958c562093ec8d122543949ed231f233f'},
  'playwright-core/index.js':{bytes:697,sha256:'a58fb2cec4293e7dcf73c58a179898a4f3986666451a19da4e731fa3af63265b'},
  'playwright-core/lib/bootstrap.js':{bytes:3481,sha256:'4637f4dbfef9cfc01baeb5f5d2cb63fa0901522c96915ea2227290558d27123e'},
  'playwright-core/lib/coreBundle.js':{bytes:3425603,sha256:'9393fa79e1c67c74edc26b610d65a4f7ed73d345a762465cc88340a33a2454ac'}
}).map(([name,value])=>[name,Object.freeze(value)])));
const RUNTIMES=new WeakSet(),OWNERS=new WeakSet();
const need=(value,message)=>{if(!value)throw Error('focus owner: '+message);};
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const identifier=value=>typeof value==='string'&&/^[A-Za-z0-9_@-]{1,128}$/.test(value);
const ns=()=>process.hrtime.bigint().toString();
const ordered=(a,b)=>typeof a==='string'&&typeof b==='string'&&/^\d{1,24}$/.test(a)&&/^\d{1,24}$/.test(b)&&BigInt(a)<=BigInt(b);
async function limited(promise,label){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{
  timer=setTimeout(()=>reject(Object.assign(Error('focus owner: '+label+' deadline exceeded'),{timedOut:true})),LIMITS.callMs);
})]);}finally{clearTimeout(timer);}}
function regular(file){
  file=path.resolve(file);for(let p=file;;p=path.dirname(p)){
    need(!fs.lstatSync(p).isSymbolicLink(),'source path contains a symlink');if(path.dirname(p)===p)break;
  }need(fs.statSync(file).isFile(),'regular source file required');return file;
}
function validateRuntimeRecord(record){
  need(record?.protocol===RUNTIME_PROTOCOL&&record.version==='1.62.1'&&object(record.files),'runtime source receipt differs');
  need(typeof record.packageRoot==='string'&&path.isAbsolute(record.packageRoot)&&path.normalize(record.packageRoot)===record.packageRoot&&
    path.basename(record.packageRoot)==='playwright'&&record.coreRoot===path.join(path.dirname(record.packageRoot),'playwright-core'),'runtime package roots differ');
  need(Object.keys(record.files).sort().join('\n')===Object.keys(SOURCE_FILES).sort().join('\n'),'runtime source population differs');
  for(const [name,want] of Object.entries(SOURCE_FILES)){
    const got=record.files[name];need(got?.bytes===want.bytes&&got.sha256===want.sha256&&
      got.path===path.join(path.dirname(record.packageRoot),name),'runtime source identity differs: '+name);
  }return record;
}
function runtime(playwrightPath,playwright){
  const packageRoot=fs.realpathSync(playwrightPath),modules=path.dirname(packageRoot),coreRoot=path.join(modules,'playwright-core'),files={};
  need(path.basename(packageRoot)==='playwright','unexpected package root');
  for(const [name,want] of Object.entries(SOURCE_FILES)){
    const file=regular(path.join(modules,name));need(fs.statSync(file).size===want.bytes,'source byte count differs: '+name);
    const raw=fs.readFileSync(file);need(raw.length===want.bytes&&crypto.createHash('sha256').update(raw).digest('hex')===want.sha256,'source digest differs: '+name);
    files[name]=Object.freeze({path:file,...want});
  }
  need(require.resolve(packageRoot)===path.join(packageRoot,'index.js')&&require(packageRoot)===playwright&&
    require.resolve('playwright-core',{paths:[packageRoot]})===path.join(coreRoot,'index.js')&&require(coreRoot)===playwright,
    'loaded Playwright module differs from admitted source');
  const connection=playwright?._connection;
  need(connection&&connection._isRemote===false&&typeof connection.toImpl==='function'&&connection._objects instanceof Map,
    'supported in-process runtime connection is absent');
  const record=Object.freeze({protocol:RUNTIME_PROTOCOL,version:'1.62.1',packageRoot,coreRoot,files:Object.freeze(files)});
  validateRuntimeRecord(record);const value={connection,record};RUNTIMES.add(value);return value;
}
function bind(page,context,browser,runtime){
  need(RUNTIMES.has(runtime),'admitted runtime token is required');validateRuntimeRecord(runtime.record);
  const connection=runtime.connection;
  for(const [value,type] of [[page,'Page'],[context,'BrowserContext'],[browser,'Browser']])
    need(value?._connection===connection&&value._type===type&&identifier(value._guid)&&connection._objects.get(value._guid)===value,
      'client object or connection identity differs');
  need(page.context()===context&&context.browser()===browser&&!page.isClosed()&&browser.isConnected()&&browser.version()===CHROMIUM_VERSION,
    'live headed page/context/browser relationship differs');
  const serverPage=connection.toImpl(page),serverContext=connection.toImpl(context),serverBrowser=connection.toImpl(browser);
  const delegate=serverPage?.delegate,frame=delegate?._mainFrameSession,client=frame?._client;
  const targetId=delegate?._targetId,contextId=serverContext?._browserContextId,sessionId=client?._sessionId;
  need(serverPage?.browserContext===serverContext&&serverPage.isStorageStatePage===false&&serverContext?._browser===serverBrowser&&
    delegate?._page===serverPage&&delegate._browserContext===serverContext&&identifier(targetId)&&identifier(contextId)&&identifier(sessionId)&&
    serverBrowser?._contexts?.get(contextId)===serverContext&&serverBrowser._crPages?.get(targetId)===delegate,
    'server page/context/browser/target identity differs');
  need(frame?._page===serverPage&&frame._crPage===delegate&&frame._parentSession===null&&frame._targetId===targetId&&
    delegate._sessions?.get(targetId)===frame,'original main frame session differs');
  const protocol=serverBrowser._connection,root=serverBrowser._session;
  need(serverBrowser.options?.name==='chromium'&&serverBrowser.options.headful===true&&protocol?._closed===false&&
    root===protocol.rootSession&&root?._sessionId===''&&root._connection===protocol&&root._closed===false&&protocol._sessions?.get('')===root&&
    client?._connection===protocol&&client._parentSession===root&&client._closed===false&&client._crashed===false&&
    protocol._sessions?.get(sessionId)===client&&typeof client.send==='function'&&typeof root.send==='function',
    'original owning CDP session is missing, foreign or closed');
  return {page,context,browser,runtime,serverPage,serverContext,serverBrowser,delegate,frame,client,root,
    identity:{pageGuid:page._guid,contextGuid:context._guid,browserGuid:browser._guid,targetId,contextId,sessionId,browserVersion:CHROMIUM_VERSION}};
}
function fresh(owner){
  const next=bind(owner.page,owner.context,owner.browser,owner.runtime);
  for(const key of ['serverPage','serverContext','serverBrowser','delegate','frame','client','root'])need(next[key]===owner[key],'owning binding changed: '+key);
  need(JSON.stringify(next.identity)===JSON.stringify(owner.identity),'owning identity changed');return owner;
}
function target(result,identity){
  const value=result?.targetInfo;
  need(value?.type==='page'&&value.attached===true&&value.targetId===identity.targetId&&value.browserContextId===identity.contextId&&
    (!('subtype' in value)||value.subtype===''),'CDP target identity differs');
  return {targetId:value.targetId,type:value.type,browserContextId:value.browserContextId,attached:value.attached};
}
function windowInfo(result){
  need(Number.isSafeInteger(result?.windowId)&&result.windowId>=0&&object(result.bounds)&&
    ['normal','minimized','maximized','fullscreen'].includes(result.bounds.windowState),'CDP window identity differs');
  const bounds={windowState:result.bounds.windowState};
  for(const key of ['left','top','width','height'])if(key in result.bounds){need(Number.isSafeInteger(result.bounds[key]),'CDP window bound differs');bounds[key]=result.bounds[key];}
  return {windowId:result.windowId,bounds};
}
function preparation(role){need(['scene','cover'].includes(role),'unsupported page role');return {
  protocol:'r002f-focus-override-removal/1',role,harnessInput:INPUT,status:'STARTED',startedHostNs:ns(),command:null};}
async function prepare(page,context,browser,runtime,receipt){
  try{
    need(receipt?.protocol==='r002f-focus-override-removal/1'&&receipt.status==='STARTED','fresh preparation receipt required');
    const owner=bind(page,context,browser,runtime);receipt.runtime=runtime.record;receipt.binding=owner.identity;
    receipt.target=target(await limited(owner.client.send('Target.getTargetInfo',{}),'target identity'),owner.identity);fresh(owner);
    receipt.window=windowInfo(await limited(owner.root.send('Browser.getWindowForTarget',{targetId:owner.identity.targetId}),'window identity'));fresh(owner);
    const command=receipt.command={method:'Emulation.setFocusEmulationEnabled',params:{enabled:false},ownerSessionId:owner.identity.sessionId,
      requestedHostNs:ns(),acknowledged:false,timedOut:false};
    try{
      const response=await limited(owner.client.send(command.method,command.params),'focus removal');
      need(object(response)&&Object.keys(response).length===0,'focus removal acknowledgment differs');
      command.response={};command.acknowledged=true;command.acknowledgedHostNs=ns();fresh(owner);
    }catch(error){command.timedOut=error.timedOut===true;command.error=String(error.message);throw error;}
    receipt.endedHostNs=ns();receipt.status='ACKNOWLEDGED';owner.receipt=receipt;OWNERS.add(owner);return owner;
  }catch(error){receipt.status='INCOMPLETE';receipt.error=String(error.message);receipt.endedHostNs=ns();throw error;}
}
function diagnostics(scene){return {protocol:'r002f-native-visibility-diagnostics/1',harnessInput:INPUT,scene,cover:null,snapshots:[],
  screencastVisibility:{limit:LIMITS.visibilityEvents,events:[],overflow:false,errors:[]}};}
function readDOM(){return {hidden:document.hidden,visibility:document.visibilityState,hasFocus:document.hasFocus(),
  paused:!!document.querySelector('.c')?.classList.contains('paused'),at:performance.now()};}
function domInfo(value){
  need(object(value)&&typeof value.hidden==='boolean'&&['hidden','visible'].includes(value.visibility)&&
    value.hidden===(value.visibility==='hidden')&&typeof value.hasFocus==='boolean'&&typeof value.paused==='boolean'&&
    Number.isFinite(value.at)&&value.at>=0,'DOM visibility readback differs');
  return {hidden:value.hidden,visibility:value.visibility,hasFocus:value.hasFocus,paused:value.paused,at:value.at};
}
async function snapshot(owner,record,label,cover=null){
  need(record?.protocol==='r002f-native-visibility-diagnostics/1'&&Array.isArray(record.snapshots)&&record.snapshots.length<LIMITS.snapshots,
    'snapshot bound exceeded');
  need(['before-capture','after-capture-start','cover-front','hidden-confirmed','after-return-front','after-capture-stop','failure'].includes(label),'snapshot phase differs');
  const row={label,startedHostNs:ns(),status:'STARTED',pages:[]};record.snapshots.push(row);
  try{
    const owners=cover?[owner,cover]:[owner];
    const results=await Promise.allSettled(owners.map(async current=>{
      need(OWNERS.has(current),'acknowledged original owner is required');fresh(current);
      const page={role:current.receipt.role,binding:current.identity};row.pages.push(page);
      const calls=[['target',()=>current.client.send('Target.getTargetInfo',{}),x=>target(x,current.identity)],
        ['window',()=>current.root.send('Browser.getWindowForTarget',{targetId:current.identity.targetId}),windowInfo],
        ['dom',()=>current.page.evaluate(readDOM),domInfo]];
      const results=await Promise.allSettled(calls.map(async([key,call,admit])=>{page[key]=admit(await limited(call(),key+' readback'));}));
      const failed=results.find(x=>x.status==='rejected');if(failed)throw failed.reason;fresh(current);
    }));
    // A failed scene read must not return while its paired cover still writes
    // the retained record. Every peer settles within its own bounded calls.
    const failed=results.find(x=>x.status==='rejected');if(failed)throw failed.reason;
    row.status='OBSERVED';row.endedHostNs=ns();return row;
  }catch(error){row.status='INCOMPLETE';row.error=String(error.message);row.endedHostNs=ns();throw error;}
}
function listenScreencast(session,record,phase){
  const stream=record.screencastVisibility;
  const listener=value=>{
    if(stream.events.length>=LIMITS.visibilityEvents){stream.overflow=true;return;}
    if(typeof value?.visible!=='boolean'){
      if(stream.errors.length<8)stream.errors.push('invalid CDP screencast visibility payload');else stream.overflow=true;return;
    }
    stream.events.push({visible:value.visible,phase:phase(),hostNs:ns()});
  };session.on('Page.screencastVisibilityChanged',listener);return ()=>session.off('Page.screencastVisibilityChanged',listener);
}
function admitPreparation(value,role){
  need(value?.protocol==='r002f-focus-override-removal/1'&&value.role===role&&value.harnessInput===INPUT&&value.status==='ACKNOWLEDGED'&&
    ordered(value.startedHostNs,value.endedHostNs)&&!value.error,'focus removal preparation incomplete');validateRuntimeRecord(value.runtime);
  const id=value.binding;need(object(id)&&['pageGuid','contextGuid','browserGuid','targetId','contextId','sessionId'].every(k=>identifier(id[k]))&&
    id.browserVersion===CHROMIUM_VERSION,'retained owner identity differs');target({targetInfo:value.target},id);windowInfo(value.window);
  const command=value.command;need(command?.method==='Emulation.setFocusEmulationEnabled'&&object(command.params)&&
    Object.keys(command.params).length===1&&command.params.enabled===false&&command.ownerSessionId===id.sessionId&&command.acknowledged===true&&
    command.timedOut===false&&!command.error&&object(command.response)&&Object.keys(command.response).length===0&&
    ordered(value.startedHostNs,command.requestedHostNs)&&ordered(command.requestedHostNs,command.acknowledgedHostNs)&&
    ordered(command.acknowledgedHostNs,value.endedHostNs),'original-session acknowledgment incomplete');
}
function admitCover(scene,cover){
  admitPreparation(scene,'scene');admitPreparation(cover,'cover');
  need(cover.binding.pageGuid!==scene.binding.pageGuid&&cover.binding.targetId!==scene.binding.targetId&&
    cover.binding.sessionId!==scene.binding.sessionId&&cover.binding.contextId===scene.binding.contextId&&
    cover.binding.contextGuid===scene.binding.contextGuid&&cover.binding.browserGuid===scene.binding.browserGuid&&
    cover.window.windowId===scene.window.windowId&&JSON.stringify(cover.runtime)===JSON.stringify(scene.runtime),'cover topology differs');
}
function admitRowDiagnostics(row){
  const value=row.visibilityDiagnostics;need(value?.protocol==='r002f-native-visibility-diagnostics/1'&&value.harnessInput===INPUT,'visibility diagnostics missing');
  admitPreparation(value.scene,'scene');const hidden=row.mode==='tabhide';
  if(hidden)admitCover(value.scene,value.cover);
  else need(row.mode==='no-hide'&&value.cover===null,'unexpected cover population');
  const labels=hidden?['before-capture','after-capture-start','cover-front','hidden-confirmed','after-return-front','after-capture-stop']:
    ['before-capture','after-capture-start','after-return-front','after-capture-stop'];
  need(Array.isArray(value.snapshots)&&value.snapshots.map(x=>x.label).join(',')===labels.join(','),'visibility readback population incomplete');
  let prior=value.scene.endedHostNs;
  for(const snapshot of value.snapshots){
    const paired=hidden&&!['before-capture','after-capture-start'].includes(snapshot.label);
    need(snapshot.status==='OBSERVED'&&!snapshot.error&&ordered(prior,snapshot.startedHostNs)&&ordered(snapshot.startedHostNs,snapshot.endedHostNs)&&
      Array.isArray(snapshot.pages)&&snapshot.pages.map(x=>x.role).join(',')===(paired?'scene,cover':'scene'),'visibility readback incomplete');
    for(const page of snapshot.pages){const preparation=value[page.role];need(JSON.stringify(page.binding)===JSON.stringify(preparation.binding),'readback owner differs');
      target({targetInfo:page.target},preparation.binding);windowInfo(page.window);domInfo(page.dom);
      need(page.window.windowId===preparation.window.windowId,'readback window changed');}
    if(snapshot.label==='hidden-confirmed')need(snapshot.pages[0].dom.hidden===true&&snapshot.pages[0].dom.paused===true&&
      snapshot.pages[1].dom.hidden===false,'genuine hidden readback missing');
    if(paired)need(ordered(value.cover.endedHostNs,snapshot.startedHostNs),'cover readback precedes its preparation');
    prior=snapshot.endedHostNs;
  }
  const stream=value.screencastVisibility;need(stream?.limit===LIMITS.visibilityEvents&&stream.overflow===false&&Array.isArray(stream.errors)&&stream.errors.length===0&&
    Array.isArray(stream.events)&&stream.events.length>0&&stream.events.length<=LIMITS.visibilityEvents,'screencast visibility stream incomplete');
  let last='0';for(const event of stream.events){need(typeof event.visible==='boolean'&&
    ['before-action','hidden-requested','activation-requested'].includes(event.phase)&&ordered(last,event.hostNs),'screencast visibility record differs');last=event.hostNs;}
  return {status:'OBSERVED',scope:'explicit harness-input removal and native readbacks; original lifecycle and PNG admission remain required'};
}
module.exports={SOURCE_FILES,LIMITS,CHROMIUM_VERSION,RUNTIME_PROTOCOL,INPUT,runtime,validateRuntimeRecord,bind,preparation,prepare,diagnostics,snapshot,
  listenScreencast,admitPreparation,admitCover,admitRowDiagnostics};
