'use strict';
// Public synthetic source controls. No browser/display or native evidence is created.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),os=require('node:os');
const {createRequire}=require('node:module'),{EventEmitter}=require('node:events');
const file=path.join(__dirname,'r002f_focus_owner.cjs');
function controls(){
  const module={exports:{}};
  // The shim admits only a synthetic runtime object in this isolated source-control VM.
  // It is appended to unmodified source here, never exported by the production module.
  vm.runInNewContext(fs.readFileSync(file,'utf8')+'\nmodule.exports.controlRuntime=x=>{RUNTIMES.add(x);return x;};',
    {module,exports:module.exports,require:createRequire(file),__dirname,process,Buffer,setTimeout,clearTimeout,URL,Map,WeakSet,Promise});
  return module.exports;
}
const copy=x=>JSON.parse(JSON.stringify(x));
function graph(F){
  const calls=[],target='A'.repeat(32),contextId='B'.repeat(32),sessionId='C'.repeat(32);
  const connection={_objects:new Map(),toImpl:x=>implementations.get(x)};
  const browser={_guid:'browser-controlled',_connection:connection,_type:'Browser',isConnected:()=>true,version:()=>F.CHROMIUM_VERSION};
  const context={_guid:'context-controlled',_connection:connection,_type:'BrowserContext',browser:()=>browser};
  const page={_guid:'page-controlled',_connection:connection,_type:'Page',context:()=>context,isClosed:()=>false,
    evaluate:async()=>({hidden:false,visibility:'visible',hasFocus:true,paused:false,at:12})};
  for(const x of [browser,context,page])connection._objects.set(x._guid,x);
  const protocol={_sessions:new Map(),_closed:false};
  const root={_sessionId:'',_connection:protocol,_closed:false,send:async(method,params)=>{
    calls.push({owner:'root',method,params});return {windowId:7,bounds:{left:0,top:0,width:416,height:730,windowState:'normal'}};}};
  protocol.rootSession=root;protocol._sessions.set('',root);
  const serverBrowser={_connection:protocol,_session:root,_contexts:new Map(),_crPages:new Map(),options:{name:'chromium',headful:true}};
  const serverContext={_browser:serverBrowser,_browserContextId:contextId};
  const serverPage={browserContext:serverContext,isStorageStatePage:false};
  const client={_sessionId:sessionId,_connection:protocol,_parentSession:root,_closed:false,_crashed:false,
    send:async(method,params)=>{calls.push({owner:'original-page',method,params});
      if(method==='Target.getTargetInfo')return {targetInfo:{targetId:target,type:'page',browserContextId:contextId,attached:true}};
      if(method==='Emulation.setFocusEmulationEnabled')return {};
      throw Error('unexpected command in synthetic owner control');}};
  protocol._sessions.set(sessionId,client);
  const delegate={_page:serverPage,_browserContext:serverContext,_targetId:target,_sessions:new Map()};
  const frame={_page:serverPage,_crPage:delegate,_targetId:target,_parentSession:null,_client:client};
  delegate._mainFrameSession=frame;delegate._sessions.set(target,frame);serverPage.delegate=delegate;
  serverBrowser._crPages.set(target,delegate);serverBrowser._contexts.set(contextId,serverContext);
  const implementations=new Map([[browser,serverBrowser],[context,serverContext],[page,serverPage]]);
  const runtime=F.controlRuntime({connection,record:{protocol:F.RUNTIME_PROTOCOL,version:'1.62.1',
    packageRoot:'/synthetic/node_modules/playwright',coreRoot:'/synthetic/node_modules/playwright-core',
    files:Object.fromEntries(Object.entries(F.SOURCE_FILES).map(([name,v])=>[name,{...v,path:'/synthetic/node_modules/'+name}]))}});
  return {calls,page,context,browser,connection,runtime,protocol,root,client,serverBrowser,serverContext,serverPage,delegate,frame,target,contextId,sessionId};
}
async function prepared(F,g,role='scene'){
  const receipt=F.preparation(role);const owner=await F.prepare(g.page,g.context,g.browser,g.runtime,receipt);return {owner,receipt};
}
test('source pins identify exact unmodified 1.62.1 entry and owning-session bundle',()=>{
  const F=controls();assert.equal(F.SOURCE_FILES['playwright-core/lib/coreBundle.js'].sha256,'9393fa79e1c67c74edc26b610d65a4f7ed73d345a762465cc88340a33a2454ac');
  assert.equal(Object.keys(F.SOURCE_FILES).length,6);assert.equal(F.CHROMIUM_VERSION,'151.0.7922.34');
});
test('runtime rejects missing or changed package sources before any browser use',()=>{
  const F=controls();assert.throws(()=>F.runtime('/definitely-missing-r002f-package',{}));
  const bad={protocol:F.RUNTIME_PROTOCOL,version:'1.62.0',files:{}};assert.throws(()=>F.validateRuntimeRecord(bad));
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-source-mismatch-')),root=path.join(dir,'node_modules/playwright');
  try{fs.mkdirSync(root,{recursive:true});const first=path.join(root,'package.json');
    fs.writeFileSync(first,Buffer.alloc(F.SOURCE_FILES['playwright/package.json'].bytes));
    assert.throws(()=>F.runtime(root,{}),/source digest differs/);
    fs.rmSync(first);fs.writeFileSync(path.join(dir,'linked-source'),'controlled');fs.symlinkSync(path.join(dir,'linked-source'),first);
    assert.throws(()=>F.runtime(root,{}),/symlink/);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('binding requires an actually admitted runtime token',()=>{
  const F=controls(),g=graph(F);assert.throws(()=>F.bind(g.page,g.context,g.browser,{...g.runtime}),/runtime/);assert.equal(g.calls.length,0);
});
test('binding refuses client GUID spoofing and foreign connections before protocol send',()=>{
  for(const mutate of [g=>g.connection._objects.set(g.page._guid,{}),g=>g.page._connection={},g=>g.page._type='Frame',g=>g.page.context=()=>({})]){
    const F=controls(),g=graph(F);mutate(g);assert.throws(()=>F.bind(g.page,g.context,g.browser,g.runtime));assert.equal(g.calls.length,0);
  }
});
test('binding refuses foreign server page context browser and target map',()=>{
  for(const mutate of [g=>g.serverPage.browserContext={},g=>g.serverContext._browser={},g=>g.delegate._page={},
    g=>g.serverBrowser._crPages.set(g.target,{}),g=>g.serverBrowser._contexts.set(g.contextId,{})]){
    const F=controls(),g=graph(F);mutate(g);assert.throws(()=>F.bind(g.page,g.context,g.browser,g.runtime));assert.equal(g.calls.length,0);
  }
});
test('binding refuses alternate frame sessions and session registry substitution',()=>{
  for(const mutate of [g=>g.frame._parentSession={},g=>g.frame._targetId='D'.repeat(32),g=>g.delegate._sessions.set(g.target,{}),
    g=>g.protocol._sessions.set(g.sessionId,{}),g=>g.client._connection={},g=>g.client._parentSession={}]){
    const F=controls(),g=graph(F);mutate(g);assert.throws(()=>F.bind(g.page,g.context,g.browser,g.runtime));assert.equal(g.calls.length,0);
  }
});
test('binding refuses closed crashed headless or different-version browsers',()=>{
  for(const mutate of [g=>g.client._closed=true,g=>g.client._crashed=true,g=>g.protocol._closed=true,
    g=>g.page.isClosed=()=>true,g=>g.browser.isConnected=()=>false,g=>g.serverBrowser.options.headful=false,g=>g.browser.version=()=> 'other']){
    const F=controls(),g=graph(F);mutate(g);assert.throws(()=>F.bind(g.page,g.context,g.browser,g.runtime));assert.equal(g.calls.length,0);
  }
});
test('removal reads identity then sends false only on the exact original owning session',async()=>{
  const F=controls(),g=graph(F),{owner,receipt}=await prepared(F,g);
  assert.equal(owner.client,g.client);assert.equal(receipt.status,'ACKNOWLEDGED');assert.equal(receipt.binding.sessionId,g.sessionId);
  assert.deepEqual(g.calls.map(x=>x.method),['Target.getTargetInfo','Browser.getWindowForTarget','Emulation.setFocusEmulationEnabled']);
  assert.deepEqual(copy(g.calls.at(-1)),{owner:'original-page',method:'Emulation.setFocusEmulationEnabled',params:{enabled:false}});
  assert.equal(receipt.command.acknowledged,true);assert.equal(receipt.command.ownerSessionId,g.sessionId);
});
test('wrong target or context CDP readback prevents the focus command',async()=>{
  for(const field of ['targetId','browserContextId','type','attached']){
    const F=controls(),g=graph(F),send=g.client.send;g.client.send=async(method,params)=>{const value=await send(method,params);
      if(method==='Target.getTargetInfo')value.targetInfo[field]=field==='attached'?false:'foreign';return value;};
    const receipt=F.preparation('scene');await assert.rejects(F.prepare(g.page,g.context,g.browser,g.runtime,receipt));
    assert.equal(receipt.status,'INCOMPLETE');assert(!g.calls.some(x=>x.method==='Emulation.setFocusEmulationEnabled'));
  }
});
test('malformed window ownership prevents the focus command',async()=>{
  for(const value of [null,{}, {windowId:'7',bounds:{}},{windowId:7,bounds:{windowState:'unknown'}}]){
    const F=controls(),g=graph(F);g.root.send=async()=>value;const receipt=F.preparation('cover');
    await assert.rejects(F.prepare(g.page,g.context,g.browser,g.runtime,receipt));assert.equal(receipt.status,'INCOMPLETE');
    assert(!g.calls.some(x=>x.method==='Emulation.setFocusEmulationEnabled'));
  }
});
test('focus rejection malformed acknowledgment and post-ack identity change stay incomplete',async()=>{
  for(const kind of ['reject','malformed','substitute']){
    const F=controls(),g=graph(F),send=g.client.send;g.client.send=async(method,params)=>{
      if(method!=='Emulation.setFocusEmulationEnabled')return send(method,params);
      if(kind==='reject')throw Error('controlled CDP denial');if(kind==='malformed')return {unexpected:true};
      g.protocol._sessions.set(g.sessionId,{});return {};
    };
    const receipt=F.preparation('scene');await assert.rejects(F.prepare(g.page,g.context,g.browser,g.runtime,receipt));assert.equal(receipt.status,'INCOMPLETE');
  }
});
test('focus timeout retains pending request without inventing an acknowledgment',async()=>{
  const F=controls(),g=graph(F),send=g.client.send;g.client.send=async(method,params)=>method==='Emulation.setFocusEmulationEnabled'?new Promise(()=>{}):send(method,params);
  const receipt=F.preparation('scene');await assert.rejects(F.prepare(g.page,g.context,g.browser,g.runtime,receipt),/deadline/);
  assert.equal(receipt.status,'INCOMPLETE');assert.equal(receipt.command.acknowledged,false);assert.equal(receipt.command.timedOut,true);
});
test('visibility readback retains DOM values and real protocol identifiers without setting them',async()=>{
  const F=controls(),g=graph(F),{owner,receipt}=await prepared(F,g),record=F.diagnostics(receipt);
  await F.snapshot(owner,record,'before-capture');const got=record.snapshots[0];assert.equal(got.status,'OBSERVED');
  assert.equal(got.pages[0].dom.hidden,false);assert.equal(got.pages[0].dom.visibility,'visible');assert.equal(got.pages[0].dom.hasFocus,true);
  assert.equal(got.pages[0].target.targetId,g.target);assert.equal(got.pages[0].window.windowId,7);
  assert(!g.calls.some(x=>/setWebLifecycle|dispatch|setDocument/.test(x.method)));
});
test('readback failure and record overflow cannot become complete diagnostics',async()=>{
  const F=controls(),g=graph(F),{owner,receipt}=await prepared(F,g),record=F.diagnostics(receipt);
  g.page.evaluate=async()=>{throw Error('controlled read failure');};await assert.rejects(F.snapshot(owner,record,'before-capture'));
  assert.equal(record.snapshots[0].status,'INCOMPLETE');assert(record.snapshots[0].error.includes('controlled read failure'));
  record.snapshots=Array.from({length:F.LIMITS.snapshots},()=>({}));await assert.rejects(F.snapshot(owner,record,'before-capture'),/bound/);
});
test('a failed scene waits for its paired cover readback before finalizing the retained prefix',async()=>{
  const F=controls(),a=graph(F),b=graph(F),scene=await prepared(F,a),cover=await prepared(F,b,'cover'),record=F.diagnostics(scene.receipt);
  a.page.evaluate=async()=>{throw Error('controlled scene read failure');};let coverSettled=false;
  b.page.evaluate=()=>new Promise(resolve=>setTimeout(()=>{coverSettled=true;resolve({hidden:false,visibility:'visible',hasFocus:true,paused:false,at:15});},20));
  await assert.rejects(F.snapshot(scene.owner,record,'cover-front',cover.owner),/controlled scene read failure/);
  assert.equal(coverSettled,true);assert.equal(record.snapshots[0].pages[1].dom.at,15);
  assert.equal(record.snapshots[0].status,'INCOMPLETE');
});
test('screencast visibility stream is bounded and listener removal is explicit',()=>{
  const F=controls(),record=F.diagnostics({}),session=new EventEmitter();let phase='before-action';
  const remove=F.listenScreencast(session,record,()=>phase);
  session.emit('Page.screencastVisibilityChanged',{visible:true});phase='hidden-requested';
  session.emit('Page.screencastVisibilityChanged',{visible:false});assert.equal(record.screencastVisibility.events[1].phase,'hidden-requested');
  for(let i=0;i<F.LIMITS.visibilityEvents;i++)session.emit('Page.screencastVisibilityChanged',{visible:true});
  assert.equal(record.screencastVisibility.events.length,F.LIMITS.visibilityEvents);assert.equal(record.screencastVisibility.overflow,true);
  remove();assert.equal(session.listenerCount('Page.screencastVisibilityChanged'),0);
});
test('diagnostics never replace the original row lifecycle admission',()=>{
  const F=controls();assert.throws(()=>F.admitRowDiagnostics({mode:'tabhide'}));
  const S=require('./r002f_tabhide_source.cjs');assert.throws(()=>S.admitRow({protocol:'r002f-tabhide-row/1',visibilityDiagnostics:{status:'OBSERVED'}}),/completion/);
});
async function diagnosticRow(F,mode){
  // Declared synthetic receipts exercise only admission. They are never native output.
  const {receipt}=await prepared(F,graph(F)),record=copy(F.diagnostics(receipt));let tick=BigInt(receipt.endedHostNs);
  const stamp=()=>String(++tick),hidden=mode==='tabhide';
  if(hidden){record.cover=copy(receipt);Object.assign(record.cover,{role:'cover',startedHostNs:stamp(),endedHostNs:String(tick+3n)});
    Object.assign(record.cover.binding,{pageGuid:'page-cover-controlled',targetId:'D'.repeat(32),sessionId:'E'.repeat(32)});
    record.cover.target.targetId=record.cover.binding.targetId;
    Object.assign(record.cover.command,{ownerSessionId:record.cover.binding.sessionId,requestedHostNs:stamp(),acknowledgedHostNs:stamp()});stamp();}
  const labels=hidden?['before-capture','after-capture-start','cover-front','hidden-confirmed','after-return-front','after-capture-stop']:
    ['before-capture','after-capture-start','after-return-front','after-capture-stop'];
  for(const label of labels){const roles=hidden&&!['before-capture','after-capture-start'].includes(label)?['scene','cover']:['scene'];
    record.snapshots.push({label,startedHostNs:stamp(),endedHostNs:stamp(),status:'OBSERVED',pages:roles.map(role=>{
      const prep=record[role],isHidden=label==='hidden-confirmed'&&role==='scene';return {role,binding:copy(prep.binding),target:copy(prep.target),window:copy(prep.window),
        dom:{hidden:isHidden,visibility:isHidden?'hidden':'visible',hasFocus:!isHidden,paused:isHidden,at:Number(tick)}};})});}
  record.screencastVisibility.events.push({visible:true,phase:'before-action',hostNs:stamp()});return {mode,visibilityDiagnostics:record};
}
test('complete synthetic no-hide and tab-hide diagnostics require separate original admission',async()=>{
  const F=controls();for(const mode of ['no-hide','tabhide']){
    const row=await diagnosticRow(F,mode);assert.equal(F.admitRowDiagnostics(row).status,'OBSERVED');
    assert.throws(()=>require('./r002f_tabhide_source.cjs').admitRow(row));
  }
});
test('missing partial wrong-session or malformed focus acknowledgments are refused',async()=>{
  const F=controls(),row=await diagnosticRow(F,'tabhide');
  for(const mutate of [x=>delete x.scene,x=>x.scene.status='INCOMPLETE',x=>x.scene.command.acknowledged=false,
    x=>x.scene.command.ownerSessionId='foreign',x=>x.scene.command.params.enabled=true,x=>x.scene.command.response={unexpected:true},
    x=>x.scene.command.timedOut=true,x=>x.scene.command.requestedHostNs='1',x=>x.scene.runtime.files['playwright/index.js'].sha256='changed']){
    const bad=copy(row);mutate(bad.visibilityDiagnostics);assert.throws(()=>F.admitRowDiagnostics(bad));
  }
});
test('cover must have a distinct page and original session in the same context browser and window',async()=>{
  const F=controls(),row=await diagnosticRow(F,'tabhide');
  for(const mutate of [x=>x.cover=null,x=>x.cover.binding.pageGuid=x.scene.binding.pageGuid,
    x=>x.cover.binding.sessionId=x.scene.binding.sessionId,x=>x.cover.binding.targetId=x.scene.binding.targetId,
    x=>x.cover.binding.contextGuid='foreign',x=>x.cover.binding.browserGuid='foreign',x=>x.cover.window.windowId=8]){
    const bad=copy(row);mutate(bad.visibilityDiagnostics);assert.throws(()=>F.admitRowDiagnostics(bad));
  }
});
test('snapshot gaps phase reordering owner substitution and non-hidden readbacks are refused',async()=>{
  const F=controls(),row=await diagnosticRow(F,'tabhide');
  for(const mutate of [x=>x.snapshots.pop(),x=>x.snapshots.reverse(),x=>x.snapshots[2].status='STARTED',
    x=>x.snapshots[2].pages.pop(),x=>x.snapshots[2].pages[0].binding.sessionId='foreign',x=>x.snapshots[2].pages[0].window.windowId=8,
    x=>x.snapshots[3].pages[0].dom={hidden:false,visibility:'visible',hasFocus:true,paused:false,at:1},
    x=>x.snapshots[3].pages[0].dom.paused=false,x=>x.snapshots[3].pages[1].dom.visibility='hidden',
    x=>x.snapshots[3].startedHostNs='1']){
    const bad=copy(row);mutate(bad.visibilityDiagnostics);assert.throws(()=>F.admitRowDiagnostics(bad));
  }
});
test('missing overflowing malformed or unordered screencast visibility is refused',async()=>{
  const F=controls(),row=await diagnosticRow(F,'no-hide');
  for(const mutate of [x=>x.events=[],x=>x.overflow=true,x=>x.errors.push('retained error'),x=>x.events[0].visible=1,
    x=>x.events[0].phase='unknown',x=>x.events.push({...x.events[0],hostNs:'1'})]){
    const bad=copy(row);mutate(bad.visibilityDiagnostics.screencastVisibility);assert.throws(()=>F.admitRowDiagnostics(bad));
  }
});
test('driver final admission preserves the original oracle then refuses a different runtime receipt',async()=>{
  const F=controls(),row=await diagnosticRow(F,'no-hide'),D=require('./r002f_tabhide.cjs');let originalCalls=0;
  const report={focusRuntime:copy(row.visibilityDiagnostics.scene.runtime),rows:[{file:'controlled-row.json'}]},verdict={status:'original-oracle-verdict'};
  const scope={F,JSON,need:(ok,message)=>{if(!ok)throw Error(message);},S:{admitReport(){originalCalls++;return verdict;},
    body:()=>JSON.stringify(row),relative:(_root,file)=>file}};
  vm.createContext(scope);vm.runInContext('globalThis.admit='+D.admitFinal.toString(),scope);
  assert.equal(scope.admit(report,'/synthetic'),verdict);assert.equal(originalCalls,1);
  report.focusRuntime.packageRoot='/other/node_modules/playwright';report.focusRuntime.coreRoot='/other/node_modules/playwright-core';
  for(const [name,value] of Object.entries(report.focusRuntime.files))value.path='/other/node_modules/'+name;
  assert.throws(()=>scope.admit(report,'/synthetic'),/row focus source/);assert.equal(originalCalls,2);
  scope.S.admitReport=()=>{throw Error('original failed lifecycle evidence');};delete report.focusRuntime;
  assert.throws(()=>scope.admit(report,'/synthetic'),/original failed lifecycle evidence/);
});
test('driver retains unsupported owner setup and cleans its acquired context once',async()=>{
  const D=require('./r002f_tabhide.cjs'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-focus-failure-'));
  try{
    const page=new EventEmitter(),context=new EventEmitter();let closes=0,closed=false;
    context.setDefaultTimeout=()=>{};context.addInitScript=async()=>{};context.route=async()=>{};context.routeWebSocket=async()=>{};
    context.newPage=async()=>page;page.isClosed=()=>closed;
    context.close=async()=>{closes++;closed=true;page.emit('close');context.emit('close');};
    const result=await D.arm({newContext:async()=>context},{origin:'http://127.0.0.1:1'},'baseline',dir,{});
    assert.equal(closes,1);assert.equal(result.entries.length,1);assert.equal(result.entries[0].verdict.status,'INCOMPLETE');
    const row=JSON.parse(fs.readFileSync(path.join(dir,result.entries[0].file)));
    assert.equal(row.mode,'setup');assert.equal(row.visibilityDiagnostics.scene.status,'INCOMPLETE');
    assert.equal(row.visibilityDiagnostics.scene.command,null);assert.match(row.error,/admitted runtime token/);
    assert.equal(row.contextClosed,true);assert.equal(row.cleanupError,null);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
