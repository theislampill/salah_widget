'use strict';
// Bounded public CDP observation only. No paused targets, routes, cache changes,
// response-body reads, worker consumers, private Playwright IDs or native waits.
const {isDeepStrictEqual}=require('node:util');
const LIMITS=Object.freeze({workers:16,pages:4,requests:16,requestIds:256,events:4096,bytes:2*1024*1024,
  stackFrames:8,text:1024,issues:32,messageBytes:256*1024});
const LIFECYCLE_EVENTS=new Set(['target-created','target-info','target-destroyed','session-detached']);
const need=(ok,message)=>{if(!ok)throw Error(message);};
const own=(object,key)=>{const d=object&&Object.getOwnPropertyDescriptor(object,key);return d&&Object.hasOwn(d,'value')?d.value:undefined;};
const finite=x=>typeof x==='number'&&Number.isFinite(x),integer=x=>Number.isSafeInteger(x)&&x>=0;
const bytes=value=>Buffer.byteLength(JSON.stringify(value));
const errorText=error=>String(error?.message??error).slice(0,1024);
function assetUrls(base){const u=new URL(base);need(u.protocol==='http:'&&['127.0.0.1','localhost','[::1]'].includes(u.hostname)&&
  u.origin===base&&!u.username&&!u.password,'exact loopback capture origin required');
  return new Set(['dem.bin.gz','colour.bin.gz'].map(name=>base+'/moon/assets/'+name));}
const monotonicMs=()=>Number(process.hrtime.bigint())/1e6;
async function deadline(operation,end,label){
  const remaining=end-monotonicMs();need(remaining>0,label+' deadline exhausted before command');
  let timer;try{return await Promise.race([Promise.resolve().then(operation),new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(Error(label+' timed out')),remaining);})]);}finally{clearTimeout(timer);}
}

class NetworkObserver{
  constructor({timeoutMs=5000,limits={}}={}){
    need(Number.isInteger(timeoutMs)&&timeoutMs>0&&timeoutMs<=5000,'bounded protocol setup/drain required');
    const bound={...LIMITS,...limits};for(const [key,value]of Object.entries(bound))need(Object.hasOwn(LIMITS,key)&&
      Number.isSafeInteger(value)&&value>0&&value<=LIMITS[key],'network collection limit differs');
    this.timeoutMs=timeoutMs;this.targets=new Map();this.sessions=new Map();this.ids=new Map();this.pending=new Set();this.responses=new Map();
    this.commandId=0;this.selectedCount=0;this.listeners=[];this.accepting=true;this.lifecycleVersion=0;this.drainEnd=null;
    this.raw={protocol:'r0040-mechanism-network/1',clockDomain:'cdp-network-monotonic',hostClockDomain:'node-hrtime',limits:bound,base:null,
      setup:{status:'NOT_STARTED',error:null},drain:{status:'NOT_STARTED',error:null,boundary:null},finalTargets:null,
      rows:[],observedEvents:0,observedMetadataBytes:0,retainedMetadataBytes:0,dropped:0,faults:0,truncatedFields:0,issues:[]};
  }
  issue(phase,error,extra={}){this.raw.faults++;if(this.raw.issues.length<this.raw.limits.issues)
    this.raw.issues.push({phase:String(phase).slice(0,128),message:errorText(error),...extra});}
  text(value,label,{required=false,limit=this.raw.limits.text}={}){
    if(typeof value!=='string'){if(required)this.issue('field',label+' unavailable');return null;}
    if(value.length>limit){this.raw.truncatedFields++;this.issue('field',label+' truncated',{originalCharacters:value.length});return value.slice(0,limit);}return value;
  }
  record(event,fields={}){
    if(!this.accepting)return;
    if(LIFECYCLE_EVENTS.has(event))this.lifecycleVersion++;
    const row=JSON.parse(JSON.stringify({ordinal:this.raw.rows.length,event,hostMonotonicNs:process.hrtime.bigint().toString(),...fields}));
    const length=bytes(row);this.raw.observedEvents++;this.raw.observedMetadataBytes+=length;
    // Leave room for the fixed header, bounded issues, final-target snapshot and counters.
    if(this.raw.rows.length>=this.raw.limits.events||this.raw.retainedMetadataBytes+length>Math.max(0,this.raw.limits.bytes-65536)){
      this.raw.dropped++;return;
    }
    this.raw.rows.push(row);this.raw.retainedMetadataBytes+=length;
  }
  safe(phase,fn){try{return fn();}catch(error){this.issue(phase,error);}}
  listen(event,fn){const wrapped=data=>this.safe(event,()=>fn(data));this.root.on(event,wrapped);this.listeners.push([event,wrapped]);}
  track(promise){let task;task=promise.catch(error=>this.issue('target-attachment',error)).finally(()=>this.pending.delete(task));
    this.pending.add(task);return task;}
  async start(browser,base){
    need(this.raw.setup.status==='NOT_STARTED','one public protocol observer setup required');this.raw.base=base;this.urls=assetUrls(base);
    this.raw.setup.status='INCOMPLETE';const end=monotonicMs()+this.timeoutMs;
    try{
      need(typeof browser?.newBrowserCDPSession==='function','public browser CDP session unavailable');
      this.root=await deadline(()=>browser.newBrowserCDPSession(),end,'browser protocol session');
      this.listen('Target.targetCreated',({targetInfo})=>this.target(targetInfo));
      this.listen('Target.targetInfoChanged',({targetInfo})=>this.target(targetInfo,true));
      this.listen('Target.targetDestroyed',({targetId})=>{if(this.targets.has(targetId)){this.targets.get(targetId).closed=true;this.record('target-destroyed',{targetId});}});
      this.listen('Target.detachedFromTarget',({sessionId,targetId})=>{if(this.sessions.has(sessionId))this.record('session-detached',{sessionId,targetId:targetId??this.sessions.get(sessionId)});});
      this.listen('Target.receivedMessageFromTarget',message=>this.message(message));
      await deadline(()=>this.root.send('Target.setDiscoverTargets',{discover:true,filter:[{type:'page'},{type:'worker'},{exclude:true}]}),end,'public Target discovery');
      const current=await deadline(()=>this.root.send('Target.getTargets',{}),end,'initial Target snapshot');
      need(Array.isArray(current.targetInfos),'public Target population unavailable');
      for(const info of current.targetInfos)this.target(info);
      this.raw.setup.status='OBSERVED';
    }catch(error){this.raw.setup.error=errorText(error);this.issue('setup',error);}
    return this.snapshot();
  }
  target(info,changed=false){
    if(!this.accepting||!['page','worker'].includes(own(info,'type')))return;
    const targetId=this.text(own(info,'targetId'),'target ID',{required:true,limit:128}),type=info.type;
    if(!targetId)return;
    const fields={targetId,type,url:this.text(own(info,'url'),'target URL',{required:true}),
      openerId:this.text(own(info,'openerId'),'opener ID',{limit:128}),browserContextId:this.text(own(info,'browserContextId'),'browser context ID',{limit:128})};
    if(this.targets.has(targetId)){
      const row=this.targets.get(targetId);if(changed){Object.assign(row,fields);this.record('target-info',fields);}return;
    }
    const limit=type==='worker'?this.raw.limits.workers:this.raw.limits.pages;
    if([...this.targets.values()].filter(t=>t.type===type).length>=limit){this.raw.dropped++;this.issue('target','bounded '+type+' target population exceeded');return;}
    this.targets.set(targetId,{...fields,closed:false});this.record('target-created',fields);
    this.track(this.attach(targetId));
  }
  async attach(targetId){
    // Late lifecycle events share the existing drain deadline; they cannot
    // start another setup/drain allocation while the final snapshot awaits.
    const end=Math.min(monotonicMs()+this.timeoutMs,this.drainEnd??Infinity);
    const attached=await deadline(()=>this.root.send('Target.attachToTarget',{targetId,flatten:false}),end,'public Target attachment');
    if(!this.accepting)return;
    const sessionId=this.text(attached?.sessionId,'session ID',{required:true,limit:128});need(sessionId&&!this.sessions.has(sessionId),'unique public target session required');
    this.sessions.set(sessionId,targetId);this.record('target-attached',{targetId,sessionId});
    this.record('network-enable-requested',{targetId,sessionId});
    await this.nested(sessionId,'Network.enable',{},end);
    if(this.accepting)this.record('network-enabled',{targetId,sessionId});
  }
  async nested(sessionId,method,params,end){
    need(method==='Network.enable','read-only network observer command required');
    const id=++this.commandId,key=sessionId+':'+id;
    let resolve,reject;const result=new Promise((yes,no)=>{resolve=yes;reject=no;});this.responses.set(key,{resolve,reject});
    // A nested error can arrive before the outer command acknowledgement.
    // Handle it immediately, while preserving the original rejection for await.
    result.catch(()=>{});
    try{
      await deadline(()=>this.root.send('Target.sendMessageToTarget',{sessionId,message:JSON.stringify({id,method,params})}),end,'public target message');
      return await deadline(()=>result,end,'Network.enable');
    }finally{this.responses.delete(key);}
  }
  message({sessionId,message}){
    if(!this.accepting||!this.sessions.has(sessionId))return;
    need(typeof message==='string','public target message string required');
    if(Buffer.byteLength(message)>this.raw.limits.messageBytes){this.raw.dropped++;this.issue('protocol-message','bounded protocol message exceeded',{observedBytes:Buffer.byteLength(message)});return;}
    const value=JSON.parse(message);
    if(Object.hasOwn(value,'id')){
      const pending=this.responses.get(sessionId+':'+value.id);
      if(pending){if(value.error)pending.reject(Error('Network.enable protocol error: '+JSON.stringify(value.error)));else pending.resolve(value.result);}return;
    }
    if(typeof value.method==='string')this.observe(sessionId,value.method,value.params??{});
  }
  initiator(value){
    const type=this.text(own(value,'type'),'initiator type',{required:true}),stack=own(value,'stack'),frames=own(stack,'callFrames');
    let callFrames=[];
    if(frames!==undefined){
      if(!Array.isArray(frames)){this.issue('initiator','stack frames unavailable');return {type,callFrames};}
      if(frames.length>this.raw.limits.stackFrames){this.raw.truncatedFields++;this.issue('initiator','initiator stack truncated',{originalFrames:frames.length});}
      callFrames=frames.slice(0,this.raw.limits.stackFrames).map(frame=>({
        functionName:this.text(own(frame,'functionName'),'initiator function'),scriptId:this.text(own(frame,'scriptId'),'initiator script',{limit:128}),
        url:this.text(own(frame,'url'),'initiator URL'),lineNumber:own(frame,'lineNumber'),columnNumber:own(frame,'columnNumber')}));
    }
    if(own(stack,'parent')||own(stack,'parentId')){this.raw.truncatedFields++;this.issue('initiator','async parent stack not retained');}
    return {type,callFrames};
  }
  observe(sessionId,method,p){return this.safe('network-event',()=>{
    if(!this.accepting||!method.startsWith('Network.'))return;
    if(!this.sessions.has(sessionId)){this.issue('network-event','unknown request session');return;}
    const id=own(p,'requestId');if(typeof id!=='string')return;
    const key=sessionId+':'+id;
    if(method==='Network.requestWillBeSent'){
      const request=own(p,'request'),url=own(request,'url'),selected=this.urls.has(url),prior=this.ids.get(key);
      if(prior){if(selected||prior.selected){this.issue('request','selected redirect or duplicate request identifier');this.record('request-redirect',{sessionId,requestId:id,url:this.text(url,'redirect URL'),timestamp:own(p,'timestamp')});}return;}
      if(this.ids.size>=this.raw.limits.requestIds){this.raw.dropped++;this.issue('request','bounded protocol request ID population exceeded');return;}
      this.ids.set(key,{selected,terminal:false});if(!selected)return;
      if(++this.selectedCount>this.raw.limits.requests){this.raw.dropped++;this.issue('request','bounded selected request population exceeded');return;}
      if(own(p,'redirectResponse'))this.issue('request','selected redirect response requires unresolved ownership');
      this.record('request-start',{sessionId,requestId:this.text(id,'request ID',{required:true,limit:128}),targetId:this.sessions.get(sessionId),
        url:this.text(url,'request URL',{required:true}),method:this.text(own(request,'method'),'request method',{required:true,limit:16}),
        type:this.text(own(p,'type'),'resource type',{limit:64}),loaderId:this.text(own(p,'loaderId'),'loader ID',{limit:128}),
        frameId:this.text(own(p,'frameId'),'frame ID',{limit:128}),timestamp:own(p,'timestamp'),initiator:this.initiator(own(p,'initiator'))});return;
    }
    let state=this.ids.get(key);
    if(!state&&method==='Network.responseReceived'&&this.urls.has(own(own(p,'response'),'url'))){
      this.issue('request','selected response has no request start');this.record('orphan-response',{sessionId,requestId:this.text(id,'request ID',{limit:128}),
        url:this.text(own(own(p,'response'),'url'),'response URL'),timestamp:own(p,'timestamp')});
    }
    if(!state){if(method==='Network.loadingFinished'||method==='Network.loadingFailed'){
      this.issue('request','orphan terminal request has no observed ownership');this.record('orphan-terminal',{sessionId,requestId:this.text(id,'request ID',{limit:128}),timestamp:own(p,'timestamp')});}return;}
    if(!state.selected)return;
    const fields={sessionId,requestId:this.text(id,'request ID',{required:true,limit:128}),timestamp:own(p,'timestamp')};
    if(state.terminal&&['Network.responseReceived','Network.dataReceived','Network.loadingFinished','Network.loadingFailed'].includes(method))this.issue('request','event after terminal or duplicate terminal');
    if(method==='Network.responseReceived'){
      const r=own(p,'response'),headers=own(r,'headers'),picked={};
      if(headers&&typeof headers==='object')for(const name of Object.keys(headers))if(['content-length','content-type','content-encoding','cache-control'].includes(name.toLowerCase()))
        picked[name.toLowerCase()]=this.text(own(headers,name),'response header');
      this.record('request-response',{...fields,url:this.text(own(r,'url'),'response URL',{required:true}),status:own(r,'status'),
        mimeType:this.text(own(r,'mimeType'),'response MIME'),fromDiskCache:own(r,'fromDiskCache')??null,
        fromServiceWorker:own(r,'fromServiceWorker')??null,fromPrefetchCache:own(r,'fromPrefetchCache')??null,headers:picked});
    }else if(method==='Network.dataReceived')this.record('request-data',{...fields,dataLength:own(p,'dataLength'),encodedDataLength:own(p,'encodedDataLength')});
    else if(method==='Network.loadingFinished'){state.terminal=true;this.record('request-finished',{...fields,encodedDataLength:own(p,'encodedDataLength')});}
    else if(method==='Network.loadingFailed'){state.terminal=true;const cors=own(p,'corsErrorStatus');this.record('request-failed',{...fields,
      errorText:this.text(own(p,'errorText'),'network error',{required:true}),canceled:own(p,'canceled')??null,
      blockedReason:this.text(own(p,'blockedReason'),'blocked reason'),corsErrorStatus:!cors?null:{corsError:this.text(own(cors,'corsError'),'CORS reason'),failedParameter:this.text(own(cors,'failedParameter'),'CORS parameter')}});}
  });}
  async settle(end=monotonicMs()+this.timeoutMs){
    try{while(this.pending.size)await deadline(()=>Promise.all([...this.pending]),end,'protocol target collection');}
    catch(error){this.issue('drain',error);}
  }
  async finish(){
    if(this.raw.drain.status!=='NOT_STARTED')return this.snapshot();
    this.raw.drain.status='INCOMPLETE';const end=monotonicMs()+this.timeoutMs;this.drainEnd=end;
    try{
      await this.settle(end);need(this.pending.size===0&&this.responses.size===0,'protocol target drain incomplete');
      need(this.root,'public protocol session unavailable at drain');
      const lifecycleBefore=this.lifecycleVersion;
      const final=await deadline(()=>this.root.send('Target.getTargets',{}),end,'final Target snapshot');
      // The awaited public snapshot can deliver new lifecycle events and start
      // attachments. Check synchronously before closing our listener boundary;
      // even already-completed late work is drift, not a complete population.
      const boundary=this.raw.drain.boundary={lifecycleBefore,lifecycleAfter:this.lifecycleVersion,
        pendingAttachments:this.pending.size,pendingResponses:this.responses.size};
      need(Array.isArray(final.targetInfos),'final target population unavailable');
      this.raw.finalTargets=final.targetInfos.filter(t=>this.targets.has(t.targetId)).map(t=>t.targetId).sort();
      need(this.raw.finalTargets.length<=this.raw.limits.workers+this.raw.limits.pages,'bounded final target population required');
      need(boundary.pendingAttachments===0&&boundary.pendingResponses===0,'protocol pending work at final snapshot boundary');
      need(boundary.lifecycleBefore===boundary.lifecycleAfter,'protocol lifecycle drift during final snapshot');
      this.raw.drain.status='OBSERVED';
    }catch(error){this.raw.drain.error=errorText(error);this.issue('drain',error);}
    this.accepting=false;
    if(this.root)for(const [event,fn]of this.listeners)this.root.removeListener(event,fn);
    return this.snapshot();
  }
  snapshot(){return JSON.parse(JSON.stringify(this.raw));}
}

function inspectNetwork(raw,legacyRequests,workerEvents,expectedBase=raw?.base){
  need(raw?.protocol==='r0040-mechanism-network/1'&&raw.clockDomain==='cdp-network-monotonic'&&raw.hostClockDomain==='node-hrtime'&&
    raw.base===expectedBase&&isDeepStrictEqual(raw.limits,LIMITS),'network identity or limits differ');
  const urls=assetUrls(expectedBase);
  need(raw.setup?.status==='OBSERVED'&&raw.setup.error===null&&raw.drain?.status==='OBSERVED'&&raw.drain.error===null,
    'network setup or drain incomplete');
  const boundary=raw.drain.boundary;
  need(boundary&&integer(boundary.lifecycleBefore)&&integer(boundary.lifecycleAfter)&&
    boundary.lifecycleBefore===boundary.lifecycleAfter&&boundary.pendingAttachments===0&&boundary.pendingResponses===0,
    'network final lifecycle or pending boundary incomplete');
  need(integer(raw.dropped)&&raw.dropped===0&&integer(raw.faults)&&raw.faults===0&&integer(raw.truncatedFields)&&raw.truncatedFields===0&&
    Array.isArray(raw.issues)&&raw.issues.length===0,'network protocol prefix incomplete, truncated or overflowed');
  need(Array.isArray(raw.rows)&&raw.rows.length>0&&raw.rows.length<=LIMITS.events&&raw.observedEvents===raw.rows.length&&
    raw.retainedMetadataBytes===raw.rows.reduce((n,row)=>n+bytes(row),0)&&raw.observedMetadataBytes===raw.retainedMetadataBytes&&
    bytes(raw)<=LIMITS.bytes,'network event count or metadata byte identity differs');
  need(Array.isArray(raw.finalTargets)&&raw.finalTargets.length===0,'owned target lifecycle still active or incomplete');
  need(boundary.lifecycleAfter===raw.rows.filter(row=>LIFECYCLE_EVENTS.has(row.event)).length,
    'network lifecycle boundary count differs from retained rows');
  need(Array.isArray(legacyRequests)&&Array.isArray(workerEvents),'actual original request and worker records required');
  const legacy=legacyRequests.filter(r=>urls.has(r.url));
  need(legacy.length===2&&[...urls].every(url=>legacy.filter(r=>r.url===url&&r.method==='GET').length===1),
    'unique complete selected legacy request population required');
  const targets=new Map(),sessions=new Map(),requests=new Map();let previous=-1n;
  for(const [ordinal,row]of raw.rows.entries()){
    need(row.ordinal===ordinal&&typeof row.event==='string'&&typeof row.hostMonotonicNs==='string'&&/^\d+$/.test(row.hostMonotonicNs),
      'network event ordinal or host clock fields differ');
    const host=BigInt(row.hostMonotonicNs);need(host>=previous,'network host clock order differs');previous=host;
    if(row.event==='target-created'){
      need(typeof row.targetId==='string'&&row.targetId.length>0&&row.targetId.length<=128&&!targets.has(row.targetId)&&
        ['page','worker'].includes(row.type)&&typeof row.url==='string'&&row.url.length<=LIMITS.text,'unique bounded target creation required');
      need([...targets.values()].filter(t=>t.type===row.type).length<(row.type==='worker'?LIMITS.workers:LIMITS.pages),'target population overflow');
      targets.set(row.targetId,{...row,closed:false});continue;
    }
    if(row.event==='target-info'){
      need(targets.has(row.targetId)&&targets.get(row.targetId).type===row.type&&typeof row.url==='string'&&row.url.length<=LIMITS.text,'known target info required');
      Object.assign(targets.get(row.targetId),row);continue;
    }
    if(row.event==='target-destroyed'){need(targets.has(row.targetId)&&!targets.get(row.targetId).closed,'one known target destruction required');targets.get(row.targetId).closed=true;continue;}
    if(row.event==='target-attached'){
      need(targets.has(row.targetId)&&typeof row.sessionId==='string'&&row.sessionId.length>0&&row.sessionId.length<=128&&!sessions.has(row.sessionId),
        'unique target session ownership required');sessions.set(row.sessionId,{targetId:row.targetId,requested:false,enabled:false});continue;
    }
    const session=sessions.get(row.sessionId);need(session&&targets.has(session.targetId),'network event has no target/session owner');
    if(row.event==='network-enable-requested'){need(row.targetId===session.targetId&&!session.requested,'one network enable request required');session.requested=true;continue;}
    if(row.event==='network-enabled'){need(row.targetId===session.targetId&&session.requested&&!session.enabled,'one completed network enable required');session.enabled=true;continue;}
    if(row.event==='session-detached'){need(row.targetId===session.targetId,'detached session target differs');continue;}
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
  return {protocol:'r0040-mechanism-network-inspection/1',status:'OBSERVED',requests:result,
    javascriptReaderCompletion:'NOT_OBSERVED',readerCancellation:'NOT_OBSERVED',cause:'NOT_ESTABLISHED',originalFailureOverride:false,nativeQualification:'NOT_VERIFIED',
    interpretation:'Complete selected protocol ownership and loading terminals only. Browser loading completion is not JavaScript body consumption; cancellation does not identify its caller.'};
}

module.exports={LIMITS,assetUrls,NetworkObserver,inspectNetwork};
