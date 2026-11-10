'use strict';
// R0017-C14: one case/connection owns this ledger. The ordinary enforced
// interceptor does not use this module. See README.md's C14 contract map.
const path=require('node:path');
const METHOD='passive-bidi/v1',SCHEMA='r0017-passive-network/v1';
const PUBLIC='https://theislampill.github.io/salah_widget/';
const CASES=Object.freeze(['chromium-public-healthy-no-preference','chromium-public-healthy-reduce']);
// C15: documented BiDi+ event forwarding on this same connection, for diagnosis
// only. Raw session/target envelopes use the existing lifecycle capture path;
// they never synthesize a missing BiDi terminal or supply acceptance credit.
const CDP_EVENTS=Object.freeze(['Network.requestWillBeSent','Network.responseReceived','Network.loadingFinished','Network.loadingFailed','Target.attachedToTarget','Target.detachedFromTarget','Target.targetCreated','Target.targetDestroyed','Target.targetCrashed'].map(event=>'goog:cdp.'+event));
const SECURITY_EVENTS=Object.freeze(['Log.entryAdded','Audits.issueAdded','Page.frameNavigated','Page.frameDetached','Page.documentOpened','Runtime.executionContextCreated','Runtime.executionContextDestroyed','Runtime.executionContextsCleared'].map(event=>'goog:cdp.'+event));
const EVENTS=Object.freeze(['log.entryAdded','network.beforeRequestSent','network.responseStarted','network.responseCompleted','network.fetchError','network.authRequired','browsingContext.contextCreated','browsingContext.contextDestroyed','browsingContext.navigationStarted','browsingContext.domContentLoaded','browsingContext.load','script.realmCreated','script.realmDestroyed',...CDP_EVENTS]);
const copy=value=>JSON.parse(JSON.stringify(value));
const INVENTORY_PATH='C:\\Program Files\\PowerShell\\7\\pwsh.exe',INVENTORY_SHA='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233';
function freeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){for(const item of Object.values(value))freeze(item);Object.freeze(value);}return value;}
function admitInventoryHost(row,fs,sha){
 const host={schema:'r0017-passive-inventory-host/v1',executablePath:INVENTORY_PATH,sha256:INVENTORY_SHA,selection:'S0_QUALIFIED_INSTALLED_CORE_NO_FALLBACK',
  versionEvidence:{kind:'PRIOR_S0_OBSERVATION_BOUND_TO_IDENTICAL_EXECUTABLE',version:'7.6.9',executableSha256:INVENTORY_SHA,runId:'42433584408',attempt:1,qualifierCommit:'0b2d6809a2ab4d4f7672b32207b4ad5aa1b62e9c',artifact:'pwsh/inventory-probe.json',observedUtc:'2026-11-08T01:17:50.4339969+00:00',source:'S0 before-cim stderr marker from the bounded inventory query; no new version invocation'},
  runtimeReadback:{utc:new Date().toISOString(),sha256:null,status:'PENDING'},
  queryContract:{timeoutMs:5000,script:'Original owned-PID CIM query unchanged',helperScope:'Query handle outcome only; helper descendant exit is not independently witnessed',cleanupScope:'Existing strict driver/browser descendant identity and exit checks remain separate',warmup:false,fallback:false,installation:false}};
 row.inventoryHost=host;
 try{host.runtimeReadback.sha256=sha(fs.readFileSync(INVENTORY_PATH));if(host.runtimeReadback.sha256!==INVENTORY_SHA)throw Error('Installed Core inventory executable hash does not match the admitted S0 identity');host.runtimeReadback.status='ADMITTED_IDENTICAL_EXECUTABLE';return freeze(host);}
 catch(e){host.runtimeReadback.status='REFUSED';host.runtimeReadback.error=String(e);freeze(host);throw Error('Passive inventory host admission refused: '+String(e));}
}
function assertSelection(options){
 if(options?.['security-provenance']!==undefined&&options['security-provenance']!=='csp')throw Error('Security provenance requires the explicit csp diagnostic mode');
 if(options?.['network-observation']!=='passive'||options.groups!=='public'||options.cases!==CASES.join(','))throw Error('C14 passive observation requires the explicit public group and exactly the two commissioned Chromium cases in order');
}
function assertSession(engine,preference,viewport,dpr,row,origin){
 if(engine!=='chromium'||origin!==PUBLIC||!['no-preference','reduce'].includes(preference)||viewport?.width!==1100||viewport?.height!==900||dpr!==1||row.plannedTopLevelDocuments!==(preference==='no-preference'?2:1))throw Error('Passive observation scope is the commissioned Chromium public preference population only');
}
function policy(raw,origin){
 try{const u=new URL(raw),o=new URL(origin);
  if(u.protocol==='data:'&&/^data:image\/(?:png|jpe?g|gif|webp|svg\+xml)(?:[;,])/i.test(raw))return {allowed:true,classification:'allowed-embedded-image'};
  if(u.protocol==='blob:'&&u.origin===o.origin)return {allowed:true,classification:'allowed-embedded-blob'};
  if(raw==='https://theislampill.github.io/favicon.ico')return {allowed:true,classification:'allowed-normal-favicon'};
  if(u.origin===o.origin&&u.pathname.startsWith(o.pathname))return {allowed:true,classification:'allowed-public-prefix'};
  return {allowed:false,classification:u.origin===o.origin?'outside-public-prefix':'off-origin-or-provider'};
 }catch{return {allowed:false,classification:'invalid-url'};}
}
function withoutHash(raw){try{const u=new URL(raw);u.hash='';return u.href;}catch{return null;}}
function requestProblems(state){
 return {invalidRequestIdentities:state.observationErrors.filter(e=>['INVALID_REQUEST_IDENTITY','MISSING_OR_INCONSISTENT_REQUEST_IDENTITY'].includes(e.kind)).map(e=>e.eventReceiptId),pendingRequests:state.requests.filter(r=>r.beforeEvents.length>0&&r.terminalEvents.length===0).map(r=>r.key),unmatchedRequests:state.requests.filter(r=>r.beforeEvents.length===0).map(r=>r.key),ambiguousRequests:state.requests.filter(r=>r.beforeEvents.length>1||r.terminalEvents.length>1).map(r=>r.key)};
}
function create({row,dir,origin,record,networkRecord,urlEvidence}){
 if(row.network!==undefined)throw Error('Passive network owner already exists');
 const securityRequested=row.securityProvenanceRequest!==undefined;
 if(securityRequested&&(row.securityProvenanceRequest?.schema!=='r0017-security-provenance-request/v1'||row.securityProvenanceRequest.mode!=='csp'))throw Error('Invalid case-local security provenance request');
 const events=securityRequested?[...EVENTS,...SECURITY_EVENTS]:[...EVENTS];
 const state=row.network={schema:SCHEMA,method:METHOD,identity:null,subscription:{events:[...events],scope:'global session subscription; no contexts filter',issued:null,acknowledged:null},requests:[],lifecycle:[],connectionEvents:[],navigations:[],policyViolations:[],httpErrors:[],fetchErrors:[],consoleErrors:[],protocolErrors:[],captureErrors:[],commandRefusals:[],observationErrors:[],finalBoundary:null,lateReceipts:[],
  diagnosticProvenance:{schema:'r0017-cdp-provenance/v1',purpose:'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT',transport:'EXISTING_BIDI_CONNECTION_ONLY',events:[...CDP_EVENTS],support:'INSPECT_ACTUAL_SUBSCRIPTION_AND_RAW_RECEIPTS',joining:'UNCLASSIFIED_RAW_EVENTS_NO_TERMINAL_SYNTHESIS'},
  interception:{requested:false,verdict:'NOT_REQUESTED_NO_INTERCEPTION_CREDIT'},coverage:{source:'Installed driver BiDi event stream only',requests:'Only emitted request identities are accounted; absence is not proof of no background traffic',workers:'Raw emitted realm type/owners only; null context or missing owner is not reassigned to a page or worker',redirects:'Connection + request ID + reported redirect count; a new hop never fabricates a prior hop completion',timestamps:'BiDi source timestamp and Node process-local monotonic receipt milliseconds are separate clocks',normalFavicon:'Exact origin-root favicon URL is allowed as a location; its HTTP/fetch errors still fail',finalCut:'After the existing owned callback/socket join, without extending its 5000 ms deadline'}};
 const byKey=new Map(); // Index only: its values are the same objects in state.requests.
 const security=securityRequested?(state.securityProvenance={schema:'r0017-security-provenance/v1',mode:'csp',purpose:'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT',status:'PENDING',events:[...SECURITY_EVENTS],context:null,session:null,commands:[],coverage:'Log and Audits enabled only on resolved owned top-target session; Page and Runtime rely on existing mapper enablement. Global subscription is not global domain enablement.',attribution:'Raw sessions, source timestamps and receipt order only. Enable may replay stored events; data scheme and temporal proximity do not establish a request join. Absence is not proof of no violation.'}):null;
 let bidi=null,securityCommand=null;
 function error(kind,detail){state.observationErrors.push({kind,...copy(detail)});}
 function capture(file,value){try{record(path.join(dir,file),value);}catch(e){state.captureErrors.push({file,error:String(e),eventReceiptId:value.trace?.eventReceiptId??null});throw e;}}
 function onTrace(entry){
  const e=copy(entry);
  if(securityCommand&&e.command?.method===securityCommand.method){
   if(e.kind==='command-issued')securityCommand.issued=e;
   if(e.kind==='command-response'&&e.command.commandReceiptId===securityCommand.issued?.command?.commandReceiptId)securityCommand.response=e;
  }
  if(state.finalBoundary&&!(e.kind==='collector-boundary'&&e.stage==='case-final-cut'))state.lateReceipts.push({kind:e.kind,traceSequence:e.traceSequence,eventReceiptId:e.eventReceiptId??null});
  if(e.kind.startsWith('connection-'))state.connectionEvents.push(e);
  if(e.kind==='command-issued'&&e.command.method==='session.subscribe')state.subscription.issued=e;
  if(e.kind==='command-response'&&e.command?.method==='session.subscribe'&&e.protocol.type==='success'&&e.association==='pending')state.subscription.acknowledged=e;
  if(e.kind==='command-issued'&&e.command.method==='browsingContext.navigate')state.navigations.push({commandReceiptId:e.command.commandReceiptId,context:e.command.context,url:e.command.url,issued:e,response:null});
  if(e.kind==='command-response'&&e.command?.method==='browsingContext.navigate'){
   const nav=state.navigations.find(n=>n.commandReceiptId===e.command.commandReceiptId);if(nav)nav.response=e;
  }
  if(['connection-error','connection-deadline','unparsed-message','command-deadline','command-send-error','command-close-rejection','event-handler-error'].includes(e.kind)||e.kind==='command-response'&&(e.protocol.value?.type==='error'||e.association!=='pending'))state.protocolErrors.push(e);
  if(e.kind==='collector-boundary'&&e.stage==='case-final-cut'){
   if(state.finalBoundary){error('DUPLICATE_FINAL_CUT',{traceSequence:e.traceSequence});return;}
   state.finalBoundary={traceSequence:e.traceSequence,utc:e.utc,monotonicMs:e.monotonicMs,monotonicClock:e.monotonicClock,pendingProtocolCommands:e.pending,...requestProblems(state)};
  }
 }
 function refuse(method,reason){const receipt={method,reason,connectionId:state.identity?.connectionId??null};state.commandRefusals.push(receipt);if(bidi)bidi.trace('passive-command-refused',receipt);throw Error('Passive observation command refused: '+method+'; '+reason);}
 function attach(owner){
  if(bidi)throw Error('Passive connection already attached');bidi=owner;state.identity=copy(owner.identity);
  const trace=owner.trace.bind(owner);owner.trace=(kind,detail)=>{const receipt=trace(kind,detail);try{onTrace(receipt);}catch(e){state.captureErrors.push({file:'passive-ledger',error:String(e),traceSequence:receipt.traceSequence});}return receipt;};
  const call=owner.call.bind(owner);owner.call=async(method,params={},...args)=>{
   if(method.startsWith('goog:cdp.')&&(!securityCommand||method!==securityCommand.method||JSON.stringify(params)!==JSON.stringify(securityCommand.params)))return refuse(method,'only the bounded owned-session diagnostic setup may issue CDP commands');
   if(method.startsWith('network.')||method==='session.unsubscribe')return refuse(method,'network mutation or subscription withdrawal is forbidden in this method');
   if(method==='browsingContext.navigate'){
    if(security&&(security.status!=='ENABLED_BEFORE_MEANINGFUL_NAVIGATION'||params.context!==security.context))return refuse(method,'security diagnostic is not enabled for this owned top context');
    if(!state.subscription.acknowledged||state.finalBoundary||owner.closeRequested||owner.socketClosed)return refuse(method,'observation is not subscribed and live');
    const index=state.navigations.length,wrapper=row.plannedTopLevelDocuments===2&&index===0,expectedPath=wrapper?'tests/widget-fixture.html':'tests/smoke.html';let url;try{url=new URL(params.url);}catch{return refuse(method,'invalid navigation URL');}
    if(index>=row.plannedTopLevelDocuments||url.origin!==new URL(origin).origin||url.pathname!==new URL(expectedPath,origin).pathname||(wrapper?url.searchParams.get('mode')!=='healthy':url.searchParams.get('fixture')!=='healthy'))return refuse(method,'uncommissioned top-level document');
   }
   const result=await call(method,params,...args);
   if(security?.status==='ENABLED_BEFORE_MEANINGFUL_NAVIGATION'&&method==='browsingContext.getTree'&&(result?.contexts?.length!==1||result.contexts[0]?.context!==security.context))return refuse(method,'owned top context changed after diagnostic setup');
   return result;
  };
 }
 async function subscribe(){
  if(!bidi||state.subscription.issued||state.finalBoundary)throw Error('Passive subscription is single-use on its owned connection');
  await bidi.call('session.subscribe',{events:[...events]});
  if(!state.subscription.acknowledged)throw Error('Passive subscription has no correlated success receipt');
  if(security)await enableSecurity();
 }
 async function diagnosticCall(method,params){
  const command={method,params:copy(params),status:'PENDING',issued:null,response:null,result:null};security.commands.push(command);securityCommand=command;
  try{
   capture('security-setup.jsonl',{stage:'requested',method,params:copy(params),connectionId:state.identity.connectionId});
   const result=await bidi.call(method,params);
   if(!command.issued||command.response?.association!=='pending'||command.response.protocol.type!=='success')throw Error('Security setup command lacks a correlated success receipt');
   command.result=copy(result);command.status='SUCCEEDED';capture('security-setup.jsonl',{stage:'succeeded',...copy(command)});return result;
  }catch(e){command.status='FAILED';command.error=String(e);throw e;}
  finally{securityCommand=null;}
 }
 async function enableSecurity(){
  try{
   const tree=await diagnosticCall('browsingContext.getTree',{});
   if(!Array.isArray(tree?.contexts)||tree.contexts.length!==1||typeof tree.contexts[0]?.context!=='string'||!tree.contexts[0].context)throw Error('Security diagnostic requires exactly one owned top context');
   security.context=tree.contexts[0].context;
   const owned=await diagnosticCall('goog:cdp.getSession',{context:security.context});
   if(typeof owned?.session!=='string'||!owned.session)throw Error('Security diagnostic has no owned CDP session');
   security.session=owned.session;
   for(const method of ['Log.enable','Audits.enable']){
    const result=await diagnosticCall('goog:cdp.sendCommand',{method,params:{},session:security.session});
    if(result?.session!==security.session||!result.result||typeof result.result!=='object'||Array.isArray(result.result))throw Error('Security diagnostic response is not bound to the owned CDP session');
   }
   security.status='ENABLED_BEFORE_MEANINGFUL_NAVIGATION';
  }catch(e){security.status='FAILED';security.error=String(e);error('SECURITY_DIAGNOSTIC_SETUP_FAILED',{error:String(e)});throw e;}
 }
 function event(v,trace){
  const p=v.params||{},receipt={...copy(trace),connectionId:state.identity?.connectionId??null};
  if(state.finalBoundary)state.lateReceipts.push({kind:'event',eventReceiptId:trace.eventReceiptId,method:v.method});
  if(v.method==='log.entryAdded'){
   const log={utc:new Date().toISOString(),...p,trace:receipt};if(p.level==='error')state.consoleErrors.push(copy(log));capture('console.jsonl',log);return;
  }
  if(!v.method.startsWith('network.')){const item={method:v.method,params:copy(p),trace:receipt};state.lifecycle.push(item);capture('lifecycle.jsonl',item);return;}
  const item={...networkRecord(v,receipt),redirectCount:p.redirectCount??null};
  item.initiator=copy(p.initiator??null);item.request.destination=copy(p.request?.destination??null);
  if(!state.subscription.acknowledged)error('EVENT_BEFORE_SUBSCRIPTION_ACK',receipt);
  if(p.isBlocked===true)error('BLOCKED_REQUEST_OBSERVED_NO_CONTINUATION',receipt);
  if(v.method==='network.authRequired')error('AUTHENTICATION_REQUIRED_NO_RESPONSE',receipt);
  const requestId=p.request?.request,redirectCount=p.redirectCount,validIdentity=typeof requestId==='string'&&requestId.length>0&&Number.isInteger(redirectCount)&&redirectCount>=0;
  const key=validIdentity?JSON.stringify([state.identity.connectionId,requestId,redirectCount]):null;
  if(!validIdentity)error('INVALID_REQUEST_IDENTITY',{...receipt,rawEvent:copy(v)});
  else if(trace.requestKey!==key)error('MISSING_OR_INCONSISTENT_REQUEST_IDENTITY',{...receipt,rawEvent:copy(v)});
  else{
   let r=byKey.get(key);
   if(!r){r={key,connectionId:state.identity.connectionId,requestId,redirectCount,url:urlEvidence(p.request?.url??null),context:p.context??null,navigation:p.navigation??null,policy:policy(p.request?.url,origin),beforeEvents:[],responseEvents:[],terminalEvents:[]};state.requests.push(r);byKey.set(key,r);if(!r.policy.allowed)state.policyViolations.push({key,url:r.url,...r.policy,eventReceiptId:receipt.eventReceiptId});}
   if(JSON.stringify(r.url)!==JSON.stringify(urlEvidence(p.request?.url??null))||r.context!==(p.context??null)||r.navigation!==(p.navigation??null))error('REQUEST_METADATA_CHANGED_WITHIN_IDENTITY',receipt);
   if(v.method==='network.beforeRequestSent')r.beforeEvents.push(copy(item));
   else if(v.method==='network.responseStarted')r.responseEvents.push(copy(item));
   else if(v.method==='network.responseCompleted'||v.method==='network.fetchError'){
    if(r.beforeEvents.length===0)error('TERMINAL_WITHOUT_OBSERVED_BEGIN',receipt);r.terminalEvents.push(copy(item));
   }
   if(p.response?.url&&withoutHash(p.response.url)!==withoutHash(p.request?.url)&&!policy(p.response.url,origin).allowed)state.policyViolations.push({key,url:urlEvidence(p.response.url),...policy(p.response.url,origin),eventReceiptId:receipt.eventReceiptId});
  }
  if(Number.isFinite(p.response?.status)&&p.response.status>=400)state.httpErrors.push(copy(item));
  if(v.method==='network.fetchError')state.fetchErrors.push(copy(item));
  if(v.method==='network.responseCompleted'&&/^https?:/.test(p.request?.url||'')&&(!Number.isInteger(p.response?.status)||p.response.status<100||p.response.status>599))error('HTTP_COMPLETION_WITHOUT_VALID_STATUS',receipt);
  capture('network.jsonl',item);
 }
 return {attach,subscribe,event};
}
function checks(row,final=false){
 const s=row.network,valid=s?.schema===SCHEMA&&s.method===METHOD&&s.identity?.connectionId===row.bidiTrace?.connectionId;
 if(!valid)return {passiveMethodIdentified:false};
 const c={passiveMethodIdentified:true,passiveSubscriptionObserved:!!s.subscription.acknowledged&&s.subscription.acknowledged.association==='pending',passiveObservationClean:[s.httpErrors,s.fetchErrors,s.consoleErrors,s.protocolErrors,s.captureErrors,s.commandRefusals,s.observationErrors].every(a=>Array.isArray(a)&&a.length===0),noUnexpectedNetwork:s.policyViolations.length===0};
 if(final){const problems=requestProblems(s);
  c.passiveFinalBoundaryRecorded=!!s.finalBoundary&&s.finalBoundary.pendingProtocolCommands.length===0;
  c.passiveRequestsAccounted=s.requests.length>0&&Object.values(problems).every(a=>a.length===0)&&s.requests.every(r=>r.beforeEvents.length===1&&r.terminalEvents.length===1);
  c.passiveTopDocumentsObserved=s.navigations.length===row.plannedTopLevelDocuments&&s.navigations.every(n=>n.response?.protocol.type==='success'&&typeof n.response.protocol.navigation==='string'&&n.issued.traceSequence>s.subscription.acknowledged?.traceSequence&&s.requests.some(r=>r.context===n.context&&r.navigation===n.response.protocol.navigation&&withoutHash(r.url)===withoutHash(n.url)&&r.beforeEvents.length===1));
  c.passiveObservationIntegrity=c.passiveMethodIdentified&&c.passiveSubscriptionObserved&&c.passiveFinalBoundaryRecorded&&c.passiveRequestsAccounted&&c.passiveTopDocumentsObserved&&[s.protocolErrors,s.captureErrors,s.commandRefusals,s.observationErrors,s.lateReceipts].every(a=>a.length===0);
 }
 return c;
}
module.exports={METHOD,SCHEMA,CASES,EVENTS,assertSelection,assertSession,admitInventoryHost,create,checks};
