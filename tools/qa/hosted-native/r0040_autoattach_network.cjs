'use strict';
// Separate observer-owned nonflat worker attachment. No browser driver, pause,
// resume, detach, body reader, manual worker fallback or original-path barrier.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const ORIGINAL_SHA256='77d40fa3519d0328fb3fcfda34f5c5001e0d82790b365801f989a5126a978af7';
const originalFile=path.join(__dirname,'r0040_mechanism_network.cjs');
const need=(ok,message)=>{if(!ok)throw Error(message);};
need(fs.lstatSync(originalFile).isFile()&&!fs.lstatSync(originalFile).isSymbolicLink()&&
  crypto.createHash('sha256').update(fs.readFileSync(originalFile)).digest('hex')===ORIGINAL_SHA256,'original network observer source differs');
const Original=require('./r0040_mechanism_network.cjs'),LIMITS=Original.LIMITS,assetUrls=Original.assetUrls;
const AUTO_LIMITS=Object.freeze({routes:20,routeDepth:17,logicalCommands:40,pendingResponses:680});
const POLICY=Object.freeze({autoAttach:true,waitForDebuggerOnStart:false,flatten:false,
  filter:Object.freeze([Object.freeze({type:'worker'}),Object.freeze({exclude:true})])});
const own=(object,key)=>{const d=object&&Object.getOwnPropertyDescriptor(object,key);return d&&Object.hasOwn(d,'value')?d.value:undefined;};
const finite=x=>typeof x==='number'&&Number.isFinite(x),integer=x=>Number.isSafeInteger(x)&&x>=0;
const bytes=value=>Buffer.byteLength(JSON.stringify(value)),clone=value=>JSON.parse(JSON.stringify(value));
const errorText=error=>String(error?.message??error).slice(0,1024),now=()=>Number(process.hrtime.bigint())/1e6;
const id=x=>typeof x==='string'&&x.length>0&&x.length<=128;
const routeKey=route=>JSON.stringify(route);
const responseKey=(route,n)=>routeKey(route)+':'+n;
const life=new Set(['target-created','target-info','target-destroyed','session-detached']);
async function deadline(operation,end,label){
  const left=end-now();need(left>0,label+' deadline exhausted before command');let timer;
  try{return await Promise.race([Promise.resolve().then(operation),new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(Error(label+' timed out')),left);})]);}finally{clearTimeout(timer);}
}
function identity(){return {protocol:'r0040-autoattach-policy/1',policy:clone(POLICY),limits:{...AUTO_LIMITS},
  originalNetworkSha256:ORIGINAL_SHA256,requestHistoryReplay:'NOT_PROMISED',runtimeNoninterference:'NOT_ESTABLISHED'};}

class NetworkObserver extends Original.NetworkObserver{
  constructor({autoLimits={},...options}={}){
    super(options);const bounds={...AUTO_LIMITS,...autoLimits};
    for(const [key,value]of Object.entries(bounds))need(Object.hasOwn(AUTO_LIMITS,key)&&Number.isSafeInteger(value)&&value>0&&value<=AUTO_LIMITS[key],
      'bounded automatic route limit required');
    this.raw.protocol='r0040-autoattach-network/1';this.raw.autoAttachLimits=bounds;this.raw.policy=clone(POLICY);
    this.routes=new Map();this.logical=new Map();this.operationId=0;this.version=0;
  }
  issue(phase,error,extra={}){if(!this.accepting)return;this.version++;return super.issue(phase,error,extra);}
  record(event,fields={}){
    if(!this.accepting)return;this.version++;
    const route=fields.sessionId&&this.routes.get(fields.sessionId)?.route;
    return super.record(event,route?{...fields,route:[...route]}:fields);
  }
  async start(browser,base){
    need(this.raw.setup.status==='NOT_STARTED','one public automatic observer setup required');this.raw.base=base;this.urls=assetUrls(base);
    this.raw.setup.status='INCOMPLETE';const end=now()+this.timeoutMs;
    try{
      need(typeof browser?.newBrowserCDPSession==='function','public browser CDP session unavailable');
      this.root=await deadline(()=>browser.newBrowserCDPSession(),end,'browser protocol session');
      this.listen('Target.targetCreated',({targetInfo})=>this.target(targetInfo,false,'discovery'));
      this.listen('Target.targetInfoChanged',({targetInfo})=>this.target(targetInfo,true,'discovery'));
      this.listen('Target.targetDestroyed',({targetId})=>{
        if(this.targets.has(targetId)){need(!this.targets.get(targetId).closed,'duplicate owned target destruction');
          this.targets.get(targetId).closed=true;this.record('target-destroyed',{targetId});}
      });
      this.listen('Target.detachedFromTarget',params=>this.detach([],params));
      this.listen('Target.receivedMessageFromTarget',params=>this.message(params));
      await deadline(()=>this.root.send('Target.setDiscoverTargets',{discover:true,filter:[{type:'page'},{type:'worker'},{exclude:true}]}),end,'public Target discovery');
      const current=await deadline(()=>this.root.send('Target.getTargets',{}),end,'initial Target snapshot');
      need(Array.isArray(current.targetInfos),'public Target population unavailable');
      for(const info of current.targetInfos)this.target(info,false,'snapshot');
      this.raw.setup.status='OBSERVED';
    }catch(error){this.raw.setup.error=errorText(error);this.issue('setup',error);}
    return this.snapshot();
  }
  fields(info){
    const fields={targetId:this.text(own(info,'targetId'),'target ID',{required:true,limit:128}),type:own(info,'type'),
      url:this.text(own(info,'url'),'target URL',{required:true}),openerId:this.text(own(info,'openerId'),'opener ID',{limit:128}),
      browserContextId:this.text(own(info,'browserContextId'),'browser context ID',{required:true,limit:128})};
    need(id(fields.targetId)&&['page','worker'].includes(fields.type)&&typeof fields.url==='string'&&id(fields.browserContextId),'complete bounded target identity required');
    return fields;
  }
  target(info,changed=false,origin='discovery'){
    if(!this.accepting||!['page','worker'].includes(own(info,'type')))return;
    const fields=this.fields(info),prior=this.targets.get(fields.targetId),discovered=origin!=='attachment';
    if(prior){
      need(prior.type===fields.type&&prior.browserContextId===fields.browserContextId,'target type or context changed');
      if(origin==='attachment'){Object.assign(prior,fields);this.record('target-info-from-attachment',fields);}
      else if(changed){Object.assign(prior,fields);this.record('target-info',fields);}
      else if(discovered&&!prior.discovered){prior.discovered=true;Object.assign(prior,fields);this.record('target-discovered',fields);}
      return prior;
    }
    const limit=fields.type==='worker'?this.raw.limits.workers:this.raw.limits.pages;
    need([...this.targets.values()].filter(t=>t.type===fields.type).length<limit,'bounded automatic target population exceeded');
    const row={...fields,closed:false,discovered,sessionId:null};this.targets.set(fields.targetId,row);
    this.record(origin==='attachment'?'target-observed-from-attachment':origin==='snapshot'?'target-observed-from-snapshot':'target-created',fields);
    if(fields.type==='page')this.track(this.attach(fields.targetId));
    return row;
  }
  route(sessionId,targetId,parent,waitingForDebugger){
    const route=[...parent,sessionId],target=this.targets.get(targetId);
    need(id(sessionId)&&!this.routes.has(sessionId)&&target&&!target.closed&&!target.sessionId,'unique live automatic target/session ownership required');
    need(this.routes.size<this.raw.autoAttachLimits.routes&&route.length<=this.raw.autoAttachLimits.routeDepth,'bounded automatic route ancestry required');
    need(new Set(route).size===route.length,'automatic route cycle');
    if(parent.length){const p=this.routes.get(parent.at(-1));need(p&&!p.detached&&isDeepStrictEqual(parent,p.route)&&
      !this.targets.get(p.targetId).closed&&this.targets.get(p.targetId).browserContextId===target.browserContextId,'live owned parent/context required');}
    const state={route,targetId,sessionId,detached:false,networkRequested:false,networkEnabled:false,policyRequested:false,policyEnabled:false};
    this.routes.set(sessionId,state);this.sessions.set(sessionId,targetId);target.sessionId=sessionId;
    this.record('target-attached',{targetId,sessionId,attachment:parent.length?'automatic':'manual-page',waitingForDebugger});
    return state;
  }
  async attach(targetId){
    need(this.targets.get(targetId)?.type==='page','manual worker fallback forbidden');
    const end=Math.min(now()+this.timeoutMs,this.drainEnd??Infinity);
    const attached=await deadline(()=>this.root.send('Target.attachToTarget',{targetId,flatten:false}),end,'public page attachment');
    if(!this.accepting)return;
    const state=this.route(attached?.sessionId,targetId,[],null);await this.initialize(state,end);
  }
  attached(parent,params){
    need(parent.length>0,'automatic attachment needs an owned parent');
    const p=this.routes.get(parent.at(-1));need(p&&!p.detached&&isDeepStrictEqual(p.route,parent),'automatic attachment parent differs');
    const info=own(params,'targetInfo');need(own(info,'type')==='worker','worker-only automatic attachment required');
    const target=this.target(info,false,'attachment');need(target,'automatic target identity unavailable');
    const state=this.route(own(params,'sessionId'),target.targetId,parent,own(params,'waitingForDebugger'));
    need(own(params,'waitingForDebugger')===false,'unexpected automatic waiting-for-debugger state; no resume permitted');
    const end=Math.min(now()+this.timeoutMs,this.drainEnd??Infinity);this.track(this.initialize(state,end));
  }
  async initialize(state,end){
    // Both commands are observation initialization on our session. No await is
    // inserted into original page creation, navigation, frame or worker code.
    const run=async(method)=>{
      const network=method==='Network.enable',prefix=network?'network-enable':'autoattach';
      state[network?'networkRequested':'policyRequested']=true;
      this.record(prefix+'-requested',{targetId:state.targetId,sessionId:state.sessionId});
      await this.command(state.route,method,network?{}:POLICY,end);
      if(this.accepting){state[network?'networkEnabled':'policyEnabled']=true;
        this.record(network?'network-enabled':'autoattach-enabled',{targetId:state.targetId,sessionId:state.sessionId});}
    };
    await Promise.all([run('Target.setAutoAttach'),run('Network.enable')]);
  }
  async command(route,method,params,end){
    need(this.accepting&&['Network.enable','Target.setAutoAttach'].includes(method)&&
      isDeepStrictEqual(params,method==='Network.enable'?{}:POLICY),'exact observer initialization command required');
    const state=this.routes.get(route.at(-1));need(state&&!state.detached&&isDeepStrictEqual(state.route,route),'owned command route required');
    need(this.logical.size<this.raw.autoAttachLimits.logicalCommands&&this.operationId<this.raw.autoAttachLimits.logicalCommands,
      'bounded automatic initialization population exceeded');
    need(this.responses.size+route.length<=this.raw.autoAttachLimits.pendingResponses,'bounded nested pending responses exceeded');
    const operationId=++this.operationId,ids=route.map(()=>++this.commandId),promises=[],keys=[];
    need(ids.every(Number.isSafeInteger),'safe public command IDs required');
    this.logical.set(operationId,{route,method});
    for(let i=0;i<route.length;i++){
      const prefix=route.slice(0,i+1),key=responseKey(prefix,ids[i]);let resolve,reject;
      const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});promise.catch(()=>{});promises.push(promise);keys.push(key);
      this.responses.set(key,{resolve,reject,done:false,operationId,route:prefix,method:i===route.length-1?method:'Target.sendMessageToTarget'});
    }
    this.record('command-requested',{sessionId:route.at(-1),operationId,method,params:clone(params),responseIds:ids});
    try{
      let message={id:ids.at(-1),method,params};
      for(let i=route.length-2;i>=0;i--){const serialized=JSON.stringify(message);need(Buffer.byteLength(serialized)<=this.raw.limits.messageBytes,'bounded outbound target message exceeded');
        message={id:ids[i],method:'Target.sendMessageToTarget',params:{sessionId:route[i+1],message:serialized}};}
      const serialized=JSON.stringify(message);need(Buffer.byteLength(serialized)<=this.raw.limits.messageBytes,'bounded outbound target message exceeded');
      // A route adds response identities, never independent layer timers or
      // new time allocations. One deadline covers the whole logical command.
      await deadline(()=>{
        const outer=Promise.resolve().then(()=>this.root.send('Target.sendMessageToTarget',{sessionId:route[0],message:serialized})).then(result=>{
          need(result&&typeof result==='object'&&!Array.isArray(result),'public target transport acknowledgement unavailable');
          if(this.accepting)this.record('command-transport-ack',{sessionId:route.at(-1),operationId});
        });
        return Promise.all([outer,...promises]);
      },end,method+' complete nested transport acknowledgement');
      if(this.accepting)this.record('command-completed',{sessionId:route.at(-1),operationId});
    }finally{for(const key of keys)this.responses.delete(key);this.logical.delete(operationId);}
  }
  detach(parent,params){
    const sid=own(params,'sessionId'),state=this.routes.get(sid);
    need(state&&!state.detached&&isDeepStrictEqual(parent,state.route.slice(0,-1))&&
      (own(params,'targetId')===undefined||own(params,'targetId')===state.targetId),'owned unique session detachment required');
    state.detached=true;this.record('session-detached',{sessionId:sid,targetId:state.targetId});
  }
  message(params){return this.receive([],params);}
  receive(parent,params){
    if(!this.accepting)return;
    need(parent.length<this.raw.autoAttachLimits.routeDepth,'bounded received route depth exceeded');
    const sid=own(params,'sessionId'),message=own(params,'message'),state=this.routes.get(sid),route=[...parent,sid];
    need(state&&isDeepStrictEqual(route,state.route),'foreign or unknown public target route');
    need(typeof message==='string'&&Buffer.byteLength(message)<=this.raw.limits.messageBytes,'bounded public target message required');
    const value=JSON.parse(message);need(value&&typeof value==='object'&&!Array.isArray(value),'protocol message object required');
    if(Object.hasOwn(value,'id')){
      need(Number.isSafeInteger(value.id)&&value.id>0&&!Object.hasOwn(value,'method'),'one bounded protocol response identity required');
      const pending=this.responses.get(responseKey(route,value.id));need(pending&&!pending.done,'unknown, wrong-route or duplicate protocol response');
      const error=own(value,'error'),result=own(value,'result');
      const hasError=Object.hasOwn(value,'error'),hasResult=Object.hasOwn(value,'result');
      need(hasError!==hasResult&&(hasError?error&&typeof error==='object'&&!Array.isArray(error)&&
        Number.isSafeInteger(own(error,'code'))&&typeof own(error,'message')==='string':
        result&&typeof result==='object'&&!Array.isArray(result)),'one complete protocol response result or error required');
      pending.done=true;
      this.record('command-response',{sessionId:sid,operationId:pending.operationId,responseId:value.id,method:pending.method,status:hasError?'ERROR':'ACK'});
      if(hasError)pending.reject(Error(pending.method+' protocol error: '+errorText(own(error,'message'))));
      else pending.resolve(result);
      return;
    }
    need(typeof value.method==='string'&&value.params&&typeof value.params==='object'&&!Array.isArray(value.params),'bounded protocol event required');
    if(value.method==='Target.receivedMessageFromTarget')return this.receive(route,value.params);
    if(value.method==='Target.attachedToTarget')return this.attached(route,value.params);
    if(value.method==='Target.detachedFromTarget')return this.detach(route,value.params);
    if(value.method.startsWith('Target.'))throw Error('unexpected target event on owned nonflat route');
    need(!state.detached,'network event after actual session detachment');
    if(value.method.startsWith('Network.')){need(state.networkRequested,'network event before enable request');return super.observe(sid,value.method,value.params);}
  }
  async finish(){
    if(this.raw.drain.status!=='NOT_STARTED')return this.snapshot();
    this.raw.drain.status='INCOMPLETE';const end=now()+this.timeoutMs;this.drainEnd=end;
    try{
      await this.settle(end);need(this.pending.size===0&&this.responses.size===0&&this.logical.size===0,'automatic protocol drain incomplete');
      need(this.root,'public protocol session unavailable at drain');
      const lifecycleBefore=this.lifecycleVersion,versionBefore=this.version;
      const final=await deadline(()=>this.root.send('Target.getTargets',{}),end,'final Target snapshot');
      const boundary=this.raw.drain.boundary={lifecycleBefore,lifecycleAfter:this.lifecycleVersion,versionBefore,versionAfter:this.version,
        pendingAttachments:this.pending.size,pendingResponses:this.responses.size,pendingLogical:this.logical.size};
      need(Array.isArray(final.targetInfos),'final target population unavailable');
      this.raw.finalTargets=final.targetInfos.filter(t=>this.targets.has(t.targetId)).map(t=>t.targetId).sort();
      need(this.raw.finalTargets.length<=this.raw.limits.workers+this.raw.limits.pages,'bounded final target population required');
      need(boundary.pendingAttachments===0&&boundary.pendingResponses===0&&boundary.pendingLogical===0,'automatic pending work at final snapshot');
      need(boundary.lifecycleBefore===boundary.lifecycleAfter&&boundary.versionBefore===boundary.versionAfter,'automatic route, fault or lifecycle drift during final snapshot');
      need([...this.targets.values()].every(t=>t.discovered&&t.closed&&t.sessionId),'discovered target closure or automatic coverage incomplete');
      need([...this.routes.values()].every(r=>r.detached&&r.networkEnabled&&r.policyEnabled),'actual owned session closure or initialization incomplete');
      this.raw.drain.status='OBSERVED';
    }catch(error){this.raw.drain.error=errorText(error);this.issue('drain',error);}
    this.accepting=false;if(this.root)for(const [event,fn]of this.listeners)this.root.removeListener(event,fn);
    return this.snapshot();
  }
}

function inspectNetwork(raw,legacyRequests,workerEvents,expectedBase=raw?.base){
  need(raw?.protocol==='r0040-autoattach-network/1'&&raw.clockDomain==='cdp-network-monotonic'&&raw.hostClockDomain==='node-hrtime'&&
    raw.base===expectedBase&&isDeepStrictEqual(raw.limits,LIMITS)&&isDeepStrictEqual(raw.autoAttachLimits,AUTO_LIMITS)&&isDeepStrictEqual(raw.policy,POLICY),
    'automatic network identity or limits differ');
  const urls=assetUrls(expectedBase),boundary=raw.drain?.boundary;
  need(raw.setup?.status==='OBSERVED'&&raw.setup.error===null&&raw.drain?.status==='OBSERVED'&&raw.drain.error===null,'automatic network setup or drain incomplete');
  need(boundary&&integer(boundary.lifecycleBefore)&&boundary.lifecycleBefore===boundary.lifecycleAfter&&integer(boundary.versionBefore)&&
    boundary.versionBefore===boundary.versionAfter&&boundary.pendingAttachments===0&&boundary.pendingResponses===0&&boundary.pendingLogical===0,
    'automatic final lifecycle, route or pending boundary incomplete');
  need(raw.dropped===0&&raw.faults===0&&raw.truncatedFields===0&&Array.isArray(raw.issues)&&raw.issues.length===0,'automatic protocol prefix incomplete, truncated or overflowed');
  need(Array.isArray(raw.rows)&&raw.rows.length>0&&raw.rows.length<=LIMITS.events&&raw.observedEvents===raw.rows.length&&
    raw.retainedMetadataBytes===raw.rows.reduce((n,r)=>n+bytes(r),0)&&raw.observedMetadataBytes===raw.retainedMetadataBytes&&bytes(raw)<=LIMITS.bytes,
    'automatic event count or metadata bytes differ');
  need(Array.isArray(raw.finalTargets)&&raw.finalTargets.length===0&&boundary.lifecycleAfter===raw.rows.filter(r=>life.has(r.event)).length&&
    boundary.versionAfter===raw.rows.length,'automatic final population/version differs');
  need(Array.isArray(legacyRequests)&&Array.isArray(workerEvents),'actual original request and worker records required');
  const legacy=legacyRequests.filter(r=>urls.has(r.url));
  need(legacy.length===2&&[...urls].every(url=>legacy.filter(r=>r.url===url&&r.method==='GET').length===1),'unique complete selected legacy request population required');
  const targets=new Map(),sessions=new Map(),commands=new Map(),responseIds=new Set(),networkRows=[],requests=new Map();let previous=-1n;
  for(const [ordinal,row]of raw.rows.entries()){
    need(row.ordinal===ordinal&&typeof row.event==='string'&&typeof row.hostMonotonicNs==='string'&&/^\d+$/.test(row.hostMonotonicNs),'automatic event ordinal or host clock differs');
    const host=BigInt(row.hostMonotonicNs);need(host>=previous,'automatic host clock order differs');previous=host;
    if(['target-created','target-observed-from-snapshot','target-observed-from-attachment'].includes(row.event)){
      need(id(row.targetId)&&!targets.has(row.targetId)&&['page','worker'].includes(row.type)&&typeof row.url==='string'&&row.url.length<=LIMITS.text&&id(row.browserContextId),
        'one bounded observed target identity required');
      need([...targets.values()].filter(t=>t.type===row.type).length<(row.type==='worker'?LIMITS.workers:LIMITS.pages),'automatic target population exceeded');
      need(row.event!=='target-observed-from-attachment'||row.type==='worker','only actual workers arrive by automatic attachment');
      targets.set(row.targetId,{...row,closed:false,discovered:row.event!=='target-observed-from-attachment',sessionId:null,
        attachmentInfo:row.event==='target-observed-from-attachment'?ordinal:null});continue;
    }
    if(['target-info','target-discovered','target-info-from-attachment'].includes(row.event)){
      const t=targets.get(row.targetId);need(t&&t.type===row.type&&t.browserContextId===row.browserContextId&&typeof row.url==='string'&&row.url.length<=LIMITS.text,'owned target info required');
      if(row.event==='target-discovered'){need(!t.discovered,'one actual population reconciliation required');t.discovered=true;}
      if(row.event==='target-info-from-attachment'){need(t.type==='worker'&&!t.sessionId,'one worker attachment target info required');t.attachmentInfo=ordinal;}
      Object.assign(t,{url:row.url,openerId:row.openerId});continue;
    }
    if(row.event==='target-destroyed'){const t=targets.get(row.targetId);need(t&&!t.closed,'one actual target destruction required');t.closed=true;continue;}
    if(row.event==='target-attached'){
      const t=targets.get(row.targetId),route=row.route;need(t&&!t.closed&&!t.sessionId&&id(row.sessionId)&&!sessions.has(row.sessionId)&&
        Array.isArray(route)&&route.length>0&&route.length<=AUTO_LIMITS.routeDepth&&route.every(id)&&new Set(route).size===route.length&&route.at(-1)===row.sessionId,
        'unique bounded live target/session route required');
      need(sessions.size<AUTO_LIMITS.routes,'automatic route population exceeded');
      if(t.type==='page')need(route.length===1&&row.attachment==='manual-page'&&row.waitingForDebugger===null,'manual page route differs');
      else{const parent=sessions.get(route.at(-2));need(parent&&!parent.detached&&!targets.get(parent.targetId).closed&&
        isDeepStrictEqual(parent.route,route.slice(0,-1))&&targets.get(parent.targetId).browserContextId===t.browserContextId&&
        row.attachment==='automatic'&&row.waitingForDebugger===false&&t.attachmentInfo===ordinal-1,
        'complete non-pausing owned worker ancestry and actual attachment targetInfo required');}
      t.sessionId=row.sessionId;sessions.set(row.sessionId,{route,targetId:row.targetId,requested:false,enabled:false,policyRequested:false,policyEnabled:false,detached:false,networkCommand:null,policyCommand:null});continue;
    }
    const session=sessions.get(row.sessionId);need(session&&isDeepStrictEqual(row.route,session.route),'automatic row route has no session owner');
    if(row.event==='session-detached'){need(!session.detached&&row.targetId===session.targetId,'one corresponding actual session detach required');session.detached=true;continue;}
    if(row.event==='network-enable-requested'||row.event==='autoattach-requested'){
      const network=row.event==='network-enable-requested',key=network?'requested':'policyRequested';
      need(!session.detached&&!targets.get(session.targetId).closed&&row.targetId===session.targetId&&!session[key],'one live initialization request required');session[key]=true;continue;
    }
    if(row.event==='command-requested'){
      need(!session.detached&&integer(row.operationId)&&row.operationId>0&&!commands.has(row.operationId)&&commands.size<AUTO_LIMITS.logicalCommands&&
        ['Network.enable','Target.setAutoAttach'].includes(row.method)&&isDeepStrictEqual(row.params,row.method==='Network.enable'?{}:POLICY)&&
        Array.isArray(row.responseIds)&&row.responseIds.length===session.route.length&&row.responseIds.every(n=>integer(n)&&n>0&&!responseIds.has(n))&&
        new Set(row.responseIds).size===row.responseIds.length,'bounded exact command identity required');
      const network=row.method==='Network.enable',key=network?'networkCommand':'policyCommand';
      need(session[network?'requested':'policyRequested']&&!session[key],'one command per requested initialization required');session[key]=row.operationId;
      row.responseIds.forEach(n=>responseIds.add(n));need(responseIds.size<=AUTO_LIMITS.pendingResponses,'bounded command response population required');
      commands.set(row.operationId,{...row,acks:new Set(),outer:false,complete:false});continue;
    }
    if(['command-response','command-transport-ack','command-completed'].includes(row.event)){
      const command=commands.get(row.operationId);need(command&&!command.complete,'one pending command result required');
      if(row.event==='command-response'){
        const index=row.route.length-1;need(isDeepStrictEqual(row.route,command.route.slice(0,index+1))&&command.responseIds[index]===row.responseId&&
          !command.acks.has(row.responseId)&&row.status==='ACK'&&row.method===(index===command.route.length-1?command.method:'Target.sendMessageToTarget'),'exact nested response ownership/ack required');
        command.acks.add(row.responseId);
      }else{need(isDeepStrictEqual(row.route,command.route),'outer command route differs');
        if(row.event==='command-transport-ack'){need(!command.outer,'one outer transport acknowledgement required');command.outer=true;}
        else{need(command.outer&&command.acks.size===command.responseIds.length,'all actual nested and outer acknowledgements required');command.complete=true;}}
      continue;
    }
    if(row.event==='network-enabled'||row.event==='autoattach-enabled'){
      const network=row.event==='network-enabled',key=network?'enabled':'policyEnabled',command=commands.get(session[network?'networkCommand':'policyCommand']);
      need(row.targetId===session.targetId&&!session[key]&&command?.complete,'one fully acknowledged initialization required');session[key]=true;continue;
    }
    need(!session.detached&&session.requested,'request metadata requires an enabled-requested live route');networkRows.push(row);
  }
  need([...targets.values()].every(t=>t.discovered&&t.closed&&t.sessionId)&&[...sessions.values()].every(s=>s.detached&&s.enabled&&s.policyEnabled)&&
    commands.size===sessions.size*2&&[...commands.values()].every(c=>c.complete),'complete actual route policy, coverage and closure required');
  // The selected-request predicates below are copied from the pinned original
  // inspector, without a changed scientific/clock/ownership threshold.
  for(const row of networkRows){
    const session=sessions.get(row.sessionId);
    const key=row.sessionId+':'+row.requestId;
    need(typeof row.requestId==='string'&&row.requestId.length>0&&row.requestId.length<=128&&finite(row.timestamp)&&row.timestamp>=0,'network request ID or timestamp differs');
    if(row.event==='request-start'){
      need(session.requested&&row.targetId===session.targetId&&!requests.has(key)&&requests.size<LIMITS.requests&&urls.has(row.url)&&row.method==='GET',
        'unique selected request start ownership required');
      need(row.initiator&&typeof row.initiator.type==='string'&&Array.isArray(row.initiator.callFrames)&&row.initiator.callFrames.length<=LIMITS.stackFrames,
        'bounded request initiator required');
      for(const frame of row.initiator.callFrames)need(typeof frame.url==='string'&&frame.url.length<=LIMITS.text&&integer(frame.lineNumber)&&integer(frame.columnNumber),
        'complete bounded initiator frame required');
      requests.set(key,{...row,lastTimestamp:row.timestamp,response:null,terminal:null,receivedDataBytes:0,receivedEncodedBytes:0});continue;
    }
    const request=requests.get(key);need(request&&!request.terminal&&row.timestamp>=request.lastTimestamp,'request event before start, after terminal or outside clock order');request.lastTimestamp=row.timestamp;
    if(row.event==='request-response'){
      need(request.response===null&&row.url===request.url&&Number.isInteger(row.status)&&row.status>=100&&row.status<=599,'one matching response required');request.response=row;
    }else if(row.event==='request-data'){
      need(request.response&&integer(row.dataLength)&&integer(row.encodedDataLength),'data after a response with finite byte counts required');
      request.receivedDataBytes+=row.dataLength;request.receivedEncodedBytes+=row.encodedDataLength;
      need(integer(request.receivedDataBytes)&&integer(request.receivedEncodedBytes),'safe received byte totals required');
    }else if(row.event==='request-finished'){
      need(request.response&&integer(row.encodedDataLength),'network finish response and byte count required');request.terminal='finished';request.terminalRow=row;
    }else if(row.event==='request-failed'){
      need(typeof row.errorText==='string'&&row.errorText.length>0&&[true,false,null].includes(row.canceled),'network failure fields required');request.terminal='failed';request.terminalRow=row;
    }else throw Error('unsupported, orphan or redirected network event');
  }
  need(requests.size===legacy.length,'selected protocol/legacy request population differs');
  const result=[];
  for(const request of requests.values()){
    const session=sessions.get(request.sessionId),target=targets.get(session.targetId);
    need(session.enabled&&target.closed&&request.terminal&&request.response,'request target or terminal lifecycle incomplete');
    need([...requests.values()].filter(r=>r.url===request.url&&r.method===request.method).length===1,'ambiguous selected request ownership');
    const old=legacy.find(r=>r.url===request.url&&r.method===request.method);
    need(old&&Number.isSafeInteger(old.id)&&['finished','failed'].includes(old.browserState),'complete original request terminal required');
    const owners=workerEvents.filter(e=>e.event==='worker-constructed'&&e.url===target.url);
    need(target.type==='worker'&&owners.length===1&&Number.isSafeInteger(owners[0].workerId),'unique worker target owner required');
    result.push({legacyRequestId:old.id,sessionId:request.sessionId,requestId:request.requestId,targetId:session.targetId,workerId:owners[0].workerId,
      url:request.url,status:request.response.status,terminal:request.terminal,legacyBrowserState:old.browserState,
      agreesWithLegacyTerminal:old.browserState===request.terminal,receivedDataBytes:request.receivedDataBytes,receivedEncodedBytes:request.receivedEncodedBytes,
      canceled:request.terminalRow.canceled??null,errorText:request.terminalRow.errorText??null,initiator:request.initiator});
  }
  return {protocol:'r0040-autoattach-network-inspection/1',status:'OBSERVED',requests:result,
    javascriptReaderCompletion:'NOT_OBSERVED',readerCancellation:'NOT_OBSERVED',cause:'NOT_ESTABLISHED',originalFailureOverride:false,nativeQualification:'NOT_VERIFIED',
    interpretation:'Complete selected protocol ownership and loading terminals only. Browser loading completion is not JavaScript body consumption; cancellation does not identify its caller.'};
}

module.exports={LIMITS,AUTO_LIMITS,POLICY,ORIGINAL_SHA256,identity,assetUrls,NetworkObserver,inspectNetwork};
