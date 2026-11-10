'use strict';
// Prospective C18 method. These dispositions account for emitted observations;
// they never supply an unobserved network terminal, worker death or body read.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const METHOD='passive-bidi-cdp/v2',SCHEMA='r0017-observed-record-accounting/v1';
const PUBLIC='https://theislampill.github.io/salah_widget/',COMMIT='eebba178172f96b3ffe5ab3845bc0fffd57c6e1b';
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const copy=value=>JSON.parse(JSON.stringify(value)),nonempty=value=>typeof value==='string'&&value.length>0;
function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
const PINNED_SOURCE=freeze(Object.fromEntries([
 ['index.html',1586459,'b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298'],
 ['config.js',23025,'91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81'],
 ['tests/smoke.html',49177,'8f332e35d8012feef103454ee230999d8786118a4699f685b671bfcafa192e4e'],
 ['tests/widget-fixture.html',15865,'2975111135aac3197dda912de7d06c2452e42d22e304736b82cf3c686a975ac6'],
 ['tests/native-script-contract.js',7046,'adde2470bba5f276ddae71f0c5a2fad9485854604bbd733c87723583e04b578a'],
 ['real-sky/native-sky.js',394836,'3e1b8db02c3762fb3d552e8c0c0f3b6f38b6a9e161ebe75288b88af0c0920fb6'],
 ['moon/moon-worker.js',88915,'62b8753d518d8047e268c86d378de76c70d4b4e33b4467283feab06e3f3bb42e'],
 ['real-sky/native-worker.js',168596,'30d3ca5b05cdf11ad5065551cb2d16e8b46ff1a82192fbc5a3337d12e108b745'],
 ['real-sky/native-data.js',9807339,'649d7ecc4fae05d655c934c4b2e69467427b9d215e0f1e6ae95701364e29167f']
].map(([file,bytes,sha256])=>[file,{bytes,sha256}])));
const PUBLIC_SOURCE=freeze(Object.keys(PINNED_SOURCE).filter(f=>!['moon/moon-worker.js','real-sky/native-worker.js'].includes(f)));
const PREREQUISITES=freeze([
 {role:'first-paint',sha256:'3591c4460aeb291e487ef1f750071b6b7436fa904b619fb3b54659c6fa4b83ed'},
 {role:'moon-initial',sha256:'837b77f23fffcb5fc24c3561632143733653d32918046dd1f65a17e227456a14'},
 {role:'moon-refinement',sha256:'d4f90ac35284f19e4675b6314ae60b0fc4ad441be54b1b78c74c173b1d80d7a4'}
]);
// A manifest label or a serialized former proof cannot bypass actual admission.
const localAdmissions=new WeakSet(),publicAdmissions=new WeakMap();
function admitSource(root,source){
 if(source?.commit!==COMMIT)throw Error('Accounting source commit differs from the reviewed payload');
 const files={};
 for(const [file,pin] of Object.entries(PINNED_SOURCE)){
  const bytes=fs.readFileSync(path.join(root,file)),actual={bytes:bytes.length,sha256:sha(bytes)};
  if(actual.bytes!==pin.bytes||actual.sha256!==pin.sha256||source.files?.[file]?.sha256!==pin.sha256||source.files[file].bytes!==pin.bytes)throw Error('Accounting source pin/manifest mismatch: '+file);
  files[file]=actual;
 }
 const proof=freeze({schema:'r0017-accounting-source/v1',status:'ADMITTED',commit:COMMIT,files,profile:'split-moon',windowProducers:['moon-refinement','native-sky'],nestedProducer:'moon-refinement',scope:'Exact public HTTPS generated fixture; embedded worker literals bound through index/native-sky plus independently pinned worker bytes'});
 localAdmissions.add(proof);return proof;
}
function admitPublicReadback(source,rows){
 if(!localAdmissions.has(source)||!Array.isArray(rows))throw Error('Public source admission needs the current actual local proof and readback');
 const selected=[];
 for(const file of PUBLIC_SOURCE){
  const matches=rows.filter(r=>r.file===file),pin=PINNED_SOURCE[file];
  if(matches.length!==1||matches[0].matches!==true||matches[0].status!==200||matches[0].sha256!==pin.sha256||matches[0].bytes!==pin.bytes||matches[0].url!==new URL(file,PUBLIC).href||matches[0].expectedSha256!==pin.sha256||!nonempty(matches[0].retrievedUtc)||!Number.isFinite(Date.parse(matches[0].retrievedUtc)))throw Error('Missing or changed served accounting source: '+file);
  selected.push(copy(matches[0]));
 }
 const proof=freeze({schema:'r0017-accounting-public-source/v1',status:'ADMITTED',rows:selected,scope:'Separate served source readback before acquisition; not browser response-body hashing'});
 publicAdmissions.set(proof,source);return proof;
}
function assertSourceAdmission(row){if(!localAdmissions.has(row.requestAccountingSource)||publicAdmissions.get(row.requestAccountingPublicSource)!==row.requestAccountingSource)throw Error('Actual local and served accounting source admission required before acquisition');}
function urlEvidence(value){
 if(typeof value==='string'&&value.startsWith('data:'))return {scheme:'data',metadata:value.slice(0,value.indexOf(',')<0?80:value.indexOf(',')),utf8Bytes:Buffer.byteLength(value),sha256:sha(value)};
 return value??null;
}
function sameURL(a,b){return JSON.stringify(urlEvidence(a))===JSON.stringify(urlEvidence(b));}
function defaultPolicy(raw){
 try{const u=new URL(raw),o=new URL(PUBLIC);
  if(u.protocol==='data:'&&/^data:image\/(?:png|jpe?g|gif|webp|svg\+xml)(?:[;,])/i.test(raw))return {allowed:true,classification:'allowed-embedded-image'};
  if(u.protocol==='blob:'&&u.origin===o.origin)return {allowed:true,classification:'allowed-embedded-blob'};
  if(raw==='https://theislampill.github.io/favicon.ico')return {allowed:true,classification:'allowed-normal-favicon'};
  if(u.origin===o.origin&&u.pathname.startsWith(o.pathname))return {allowed:true,classification:'allowed-public-prefix'};
  return {allowed:false,classification:u.origin===o.origin?'outside-public-prefix':'off-origin-or-provider'};
 }catch{return {allowed:false,classification:'invalid-url'};}
}
function processEnd(row){
 const c=row.cleanup,p=row.protocolFinalization,owned=c?.ownedProcesses;
 const valid=x=>Number.isInteger(x?.ProcessId)&&x.ProcessId>0&&nonempty(x.Name)&&nonempty(x.ExecutablePath)&&nonempty(x.CreationDate)&&Number.isFinite(Date.parse(x.CreationDate));
 const match=x=>valid(x)&&owned.filter(o=>o.ProcessId===x.ProcessId&&o.CreationDate===x.CreationDate&&o.Name===x.Name&&o.ExecutablePath===x.ExecutablePath&&o.ParentProcessId===x.ParentProcessId).length===1;
 const verified=Array.isArray(owned)&&owned.length>=2&&owned.every(valid)&&new Set(owned.map(x=>x.ProcessId)).size===owned.length&&match(row.driverProcess)&&match(row.nativeProcess)&&row.driverProcess.ProcessId===row.driverPid&&row.nativeProcess.ProcessId===row.browserPid&&row.nativeProcess.ParentProcessId===row.driverPid&&
  c.ok===true&&c.verifiedExited===true&&c.scopeKnown===true&&c.profileCleanup?.absent===true&&[c.remaining,c.unresolvedObserved,c.errors].every(a=>Array.isArray(a)&&a.length===0)&&Array.isArray(c.queries)&&c.queries.length>0&&Array.isArray(c.queries.at(-1)?.observed)&&c.queries.at(-1).observed.length===0&&
  p?.ok===true&&p.status==='SETTLED'&&p.socketClosed===true&&p.settledWithinDeadline===true&&p.pendingCommandCount===0&&p.pendingEventHandlerCount===0&&[p.pendingCommands,p.pendingEventHandlers,p.eventHandlerErrors].every(a=>Array.isArray(a)&&a.length===0);
 return {verified:!!verified,driver:copy(row.driverProcess??null),browser:copy(row.nativeProcess??null),ownedProcesses:copy(owned??null),cleanupFinishedUtc:c?.finishedUtc??null,scope:'Identity-safe owned process end and joined observer; no individual request terminal, cancellation or physical realm-death inference'};
}
function reconcile(row,policy=defaultPolicy){
 const s=row.network||{},connection=s.identity?.connectionId,records=[],captureProblems=[],orphans=[],observedErrors=[],policyViolations=[],dependencies=new Map();
 const issue=(kind,detail={})=>captureProblems.push({kind,...detail});
 function array(value,pointer){if(Array.isArray(value))return value;issue('MALFORMED_REQUIRED_ARRAY',{pointer,raw:copy(value??null)});return [];}
 const ref=(event,pointer)=>({pointer,eventReceiptId:event?.trace?.eventReceiptId??null,connectionId:event?.trace?.connectionId??null});
 const seenReceipts=new Set();
 function validReceipt(event,pointer){const r=ref(event,pointer),id=r.eventReceiptId;
  if(r.connectionId!==connection||!nonempty(connection)||!nonempty(id)||!id.startsWith(connection+':event:')||!/^[1-9]\d*$/.test(id.slice((connection+':event:').length))){issue('INVALID_RECEIPT_IDENTITY',{reference:r});return false;}
  if(seenReceipts.has(id)){issue('DUPLICATE_RECEIPT',{reference:r});return false;}seenReceipts.add(id);return true;
 }
 function dependency(raw,reference,kind){
  if(raw===undefined||raw===null)return;
  const url=urlEvidence(raw),key=JSON.stringify(url);let verdict;
  if(typeof raw==='string')verdict=policy(raw,PUBLIC);
  else verdict=raw?.scheme==='data'&&Number.isInteger(raw.utf8Bytes)&&/^[a-f0-9]{64}$/.test(raw.sha256||'')&&/^data:image\/(?:png|jpe?g|gif|webp|svg\+xml)(?:[;,])/i.test(raw.metadata||'')?{allowed:true,classification:'allowed-embedded-image-digest'}:{allowed:false,classification:'invalid-url-evidence'};
  if(!dependencies.has(key))dependencies.set(key,{url,policy:verdict,observations:[]});dependencies.get(key).observations.push({kind,reference});
  if(!verdict.allowed)policyViolations.push({url,...verdict,kind,reference});
 }
 const finalBoundary=s.finalBoundary,processScopeEnd=processEnd(row);
 if(s.method!==METHOD)issue('WRONG_ACCOUNTING_METHOD');
 if(!s.identity||connection!==row.bidiTrace?.connectionId||s.identity.case!==row.name||s.identity.engine!==row.engine||s.identity.runId!==row.bidiTrace?.runId||row.bidiTrace?.case!==row.name||row.bidiTrace?.engine!==row.engine)issue('CASE_CONNECTION_IDENTITY_MISMATCH');
 if(!finalBoundary||!Number.isInteger(finalBoundary.traceSequence)||finalBoundary.traceSequence<=0||!Array.isArray(finalBoundary.pendingProtocolCommands)||finalBoundary.pendingProtocolCommands.length)issue('MISSING_OR_UNJOINED_FINAL_CUT');
 if(!processScopeEnd.verified)issue('OWNED_PROCESS_OR_FINALIZER_UNVERIFIED');
 for(const field of ['protocolErrors','captureErrors','commandRefusals','observationErrors','lateReceipts']){
  if(!Array.isArray(s[field]))issue('MISSING_CAPTURE_ARRAY',{field});else for(const raw of s[field])issue('CAPTURE_'+field,{raw:copy(raw)});
 }
 if(!Array.isArray(row.bidiTrace?.writeErrors)||row.bidiTrace.writeErrors.length)issue('TRACE_WRITE_FAILURE');
 const localOK=localAdmissions.has(row.requestAccountingSource),publicOK=publicAdmissions.get(row.requestAccountingPublicSource)===row.requestAccountingSource&&localOK;
 if(!localOK)issue('ACTUAL_LOCAL_SOURCE_NOT_ADMITTED');if(!publicOK)issue('SERVED_EXECUTABLE_SOURCE_NOT_ADMITTED');
 const lifecycle=[],starts=[],attachments=[],bySessionId=new Map(),byRequestId=new Map(),groupedBidi=new Map();
 function add(map,key,value){if(!map.has(key))map.set(key,[]);map.get(key).push(value);}
 function record(id,session,start,url){const r={key:JSON.stringify([connection,session,id,records.length]),connectionId:connection,session,requestId:id,redirectCount:0,url:urlEvidence(url),starts:[],responses:[],terminals:[],bidi:null,cdp:null,outcome:'unobserved',sourceClass:null,reportedLifetime:{subjectRealmEnd:null,creatorRealmEnd:null,detach:null,physicalDeathProven:false},requiredConsumption:'Not inferred per request; see independent requiredConsumerEvidence'};if(start)r.starts.push(start);records.push(r);return r;}
 if(!Array.isArray(s.lifecycle))issue('MISSING_LIFECYCLE_ARRAY');
 for(const [i,e] of array(s.lifecycle,'/network/lifecycle').entries()){
  if(!e||typeof e!=='object'||Array.isArray(e)){issue('MALFORMED_LIFECYCLE_MEMBER',{pointer:'/network/lifecycle/'+i,raw:copy(e??null)});orphans.push({pointer:'/network/lifecycle/'+i,raw:copy(e??null)});continue;}
  const reference=ref(e,'/network/lifecycle/'+i),valid=validReceipt(e,reference.pointer),native=e.params?.params,session=e.params?.session;
  const item={e,p:native,session,index:i,reference,valid};lifecycle.push(item);
  if(!nonempty(e.method)||!e.params||typeof e.params!=='object'||Array.isArray(e.params)){issue('MALFORMED_LIFECYCLE_EVENT',{reference,raw:copy(e)});item.valid=false;}
  if(typeof e.method!=='string'||!e.method.startsWith('goog:cdp.'))continue;
  if(e.params?.event!==e.method.slice(9)||!nonempty(session)||!native||typeof native!=='object'||Array.isArray(native)){issue('INVALID_CDP_ENVELOPE',{reference});item.valid=false;}
  if(e.method==='goog:cdp.Target.attachedToTarget'){
   if(!nonempty(native?.sessionId)||!nonempty(native?.targetInfo?.targetId)){issue('INVALID_ATTACHMENT',{reference});continue;}if(item.valid)attachments.push(item);
  }
  if(e.method==='goog:cdp.Network.requestWillBeSent'){
   dependency(native?.request?.url,reference,'request');dependency(native?.redirectResponse?.url,reference,'redirect-response');
   const r=record(native?.requestId??null,session??null,reference,native?.request?.url);r.cdp={start:reference,session:session??null,requestId:native?.requestId??null,urlFragment:native?.request?.urlFragment??null};item.record=r;starts.push(item);
   if(!nonempty(native?.requestId)||!nonempty(native?.request?.url)){issue('INVALID_CDP_REQUEST_IDENTITY',{reference});item.valid=false;continue;}
   if(!item.valid)continue;
   add(bySessionId,JSON.stringify([session,native.requestId]),item);add(byRequestId,native.requestId,item);
   if(native.redirectResponse){issue('UNSUPPORTED_CDP_REDIRECT',{reference});if(Number.isFinite(native.redirectResponse.status)&&native.redirectResponse.status>=400)observedErrors.push({kind:'HTTP_ERROR',reference,status:native.redirectResponse.status,source:'redirectResponse'});}
  }
  if(e.method==='goog:cdp.Log.entryAdded'&&native?.entry?.level==='error')observedErrors.push({kind:'CONSOLE_OR_SECURITY_ERROR',reference,raw:copy(native)});
  if(e.method==='goog:cdp.Audits.issueAdded'&&native?.issue?.details?.contentSecurityPolicyIssueDetails?.isReportOnly===false)observedErrors.push({kind:'ENFORCED_CSP_ERROR',reference,raw:copy(native)});
 }
 for(const list of bySessionId.values())if(list.length!==1)issue('DUPLICATE_CDP_START',{references:list.map(x=>x.reference)});
 const childAttachments=new Map(),targetAttachments=new Map();
 for(const a of attachments){add(childAttachments,a.p.sessionId,a);add(targetAttachments,JSON.stringify([a.session,a.p.targetInfo.targetId]),a);}
 for(const list of [...childAttachments.values(),...targetAttachments.values()])if(list.length!==1)issue('AMBIGUOUS_ATTACHMENT',{references:list.map(x=>x.reference)});
 for(const item of lifecycle){const {e,p,session,reference}=item;
  if(!['goog:cdp.Network.responseReceived','goog:cdp.Network.loadingFinished','goog:cdp.Network.loadingFailed'].includes(e.method))continue;
  dependency(p?.response?.url,reference,'response');
  if(Number.isFinite(p?.response?.status)&&p.response.status>=400)observedErrors.push({kind:'HTTP_ERROR',reference,status:p.response.status});
  if(e.method==='goog:cdp.Network.loadingFailed')observedErrors.push({kind:'FETCH_ERROR',reference,raw:copy(p??null)});
  if(!item.valid){orphans.push({method:e.method,reference,raw:copy(p??null),invalidIdentity:true});continue;}
  let candidates=bySessionId.get(JSON.stringify([session,p?.requestId]))||[],join=null;
  if(candidates.length===0){const a=(childAttachments.get(session)||[]).filter(a=>a.p.targetInfo.targetId===p?.requestId&&a.index<item.index);
   if(a.length===1&&(targetAttachments.get(JSON.stringify([a[0].session,p.requestId]))||[]).length===1){candidates=bySessionId.get(JSON.stringify([a[0].session,p.requestId]))||[];if(candidates.length===1&&candidates[0].index<a[0].index)join={kind:'EXACT_BOOTSTRAP_PARENT_TARGET_CHILD',attachment:a[0].reference,parentSession:a[0].session,childSession:session,targetId:p.requestId};else candidates=[];}
  }
  if(!nonempty(p?.requestId)||candidates.length!==1){orphans.push({method:e.method,reference,raw:copy(p??null)});issue('ORPHAN_OR_AMBIGUOUS_CDP_EVENT',{method:e.method,reference});continue;}
  const target=candidates[0];if(target.index>=item.index)issue('CDP_EVENT_PRECEDES_START',{reference,start:target.reference});
  const observation={method:e.method,reference,join,raw:copy(p)};
  if(e.method==='goog:cdp.Network.responseReceived')target.record.responses.push(observation);else target.record.terminals.push(observation);
 }
 if(!Array.isArray(s.requests))issue('MISSING_BIDI_REQUEST_ARRAY');
 for(const [i,b] of array(s.requests,'/network/requests').entries()){
  if(!b||typeof b!=='object'||Array.isArray(b)){issue('MALFORMED_BIDI_RECORD',{pointer:'/network/requests/'+i,raw:copy(b??null)});orphans.push({pointer:'/network/requests/'+i,raw:copy(b??null)});continue;}
  const pointer='/network/requests/'+i,identity=nonempty(b.requestId)&&Number.isInteger(b.redirectCount)&&b.redirectCount===0&&b.connectionId===connection&&b.key===JSON.stringify([connection,b.requestId,b.redirectCount]);
  dependency(b.url,{pointer},'grouped-request');
  if(!identity)issue('INVALID_OR_UNSUPPORTED_BIDI_IDENTITY',{pointer,key:b.key??null});
  // CDP explicitly separates a Document request's fragment. Concatenating that
  // reported field is an exact identity comparison, not a fragment-blind join.
  const possible=byRequestId.get(b.requestId)||[],matches=possible.filter(x=>sameURL(x.p.request?.url+(x.p.request?.urlFragment||''),b.url)&&(b.context===null||!x.p.frameId||x.p.frameId===b.context));
  let r;
  if(identity&&possible.length===1&&matches.length===1&&!matches[0].record.bidi)r=matches[0].record;
  else{r=record(b.requestId,null,null,b.url);if(possible.length||records.some(x=>x!==r&&x.bidi?.key===b.key))issue('AMBIGUOUS_OR_MISMATCHED_BIDI_CDP_JOIN',{pointer,requestId:b.requestId});}
  r.bidi={key:b.key,pointer,url:copy(b.url??null),context:b.context,navigation:b.navigation,destination:b.beforeEvents?.[0]?.request?.destination??null};
  if(!Array.isArray(b.beforeEvents)||b.beforeEvents.length!==1)issue('BIDI_BEGIN_CARDINALITY',{pointer});
  if(!Array.isArray(b.terminalEvents)||b.terminalEvents.length>1)issue('BIDI_TERMINAL_CARDINALITY',{pointer});
  const methods={beforeEvents:['network.beforeRequestSent'],responseEvents:['network.responseStarted'],terminalEvents:['network.responseCompleted','network.fetchError']};
  for(const [field,kind] of [['beforeEvents','start'],['responseEvents','response'],['terminalEvents','terminal']])for(const [j,e]of array(b[field],pointer+'/'+field).entries()){
   const reference=ref(e,pointer+'/'+field+'/'+j);
   if(!e||typeof e!=='object'||Array.isArray(e)){issue('MALFORMED_BIDI_EVENT',{reference,raw:copy(e??null)});orphans.push({reference,raw:copy(e??null)});continue;}
   add(groupedBidi,reference.eventReceiptId,{event:e,reference});
   const valid=validReceipt(e,reference.pointer);dependency(e.request?.url,reference,'request');dependency(e.response?.url,reference,'response');
   if(e.method==='network.fetchError')observedErrors.push({kind:'FETCH_ERROR',reference,errorText:e.errorText??null});
   if(Number.isFinite(e.response?.status)&&e.response.status>=400)observedErrors.push({kind:'HTTP_ERROR',reference,status:e.response.status});
   const sameIdentity=identity&&e.request?.id===b.requestId&&sameURL(e.request?.url,b.url)&&e.redirectCount===b.redirectCount&&e.context===b.context&&e.navigation===b.navigation;
   if(!sameIdentity||!methods[field].includes(e.method)){issue('BIDI_EVENT_IDENTITY_OR_METHOD_MISMATCH',{reference,expectedMethods:methods[field]});orphans.push({reference,raw:copy(e)});continue;}
   if(!valid){orphans.push({reference,raw:copy(e),invalidIdentity:true});continue;}
   if(kind==='start'){if(!r.cdp)r.starts.push(reference);}else r[kind==='terminal'?'terminals':'responses'].push({method:e.method,reference,join:r.cdp?{kind:'UNIQUE_EXACT_REQUEST_ID_AND_URL',cdpStart:r.cdp.start}:null,raw:copy(e)});
  }
 }
 // V2 captures every raw network event before grouping. The grouping is an
 // index, not the denominator: malformed starts and authentication events must
 // still survive with their destinations even when they cannot enter that index.
 const rawBidiIds=new Set();
 for(const [i,e]of array(s.observedNetworkEvents,'/network/observedNetworkEvents').entries()){
  const reference=ref(e,'/network/observedNetworkEvents/'+i),id=reference.eventReceiptId;
  if(!e||typeof e!=='object'||Array.isArray(e)){issue('MALFORMED_RAW_BIDI_EVENT',{reference,raw:copy(e??null)});orphans.push({reference,raw:copy(e??null)});continue;}
  dependency(e.request?.url,reference,'raw-request');dependency(e.response?.url,reference,'raw-response');
  if(rawBidiIds.has(id))issue('DUPLICATE_RAW_BIDI_RECEIPT',{reference});rawBidiIds.add(id);
  const grouped=groupedBidi.get(id)||[];
  if(grouped.length===1&&JSON.stringify(grouped[0].event)===JSON.stringify(e))continue;
  if(grouped.length){issue('RAW_GROUPED_EVENT_MISMATCH',{reference,grouped:grouped.map(x=>x.reference)});orphans.push({reference,raw:copy(e)});continue;}
  validReceipt(e,reference.pointer);issue('UNGROUPED_BIDI_EVENT',{reference,method:e.method??null});orphans.push({reference,raw:copy(e)});
  if(e.method==='network.beforeRequestSent'){const r=record(e.request?.id??null,null,reference,e.request?.url);r.bidi={pointer:reference.pointer,unboundIdentity:true};}
  if(e.method==='network.fetchError')observedErrors.push({kind:'FETCH_ERROR',reference,errorText:e.errorText??null});
  if(Number.isFinite(e.response?.status)&&e.response.status>=400)observedErrors.push({kind:'HTTP_ERROR',reference,status:e.response.status});
 }
 for(const [id,events]of groupedBidi)if(!rawBidiIds.has(id))issue('GROUPED_BIDI_EVENT_NOT_CAPTURED',{eventReceiptId:id,references:events.map(x=>x.reference)});
 // Keep the capture owner's raw error surfaces, including failures whose invalid
 // identity prevented insertion into the legacy grouped-request structure.
 for(const field of ['httpErrors','fetchErrors','consoleErrors','policyViolations'])for(const [i,raw]of array(s[field],'/network/'+field).entries()){
  const reference=ref(raw,'/network/'+field+'/'+i);if(field==='policyViolations')reference.eventReceiptId=raw?.eventReceiptId??null;
  if(!raw||typeof raw!=='object'||Array.isArray(raw)){issue('MALFORMED_ERROR_RECORD',{reference,raw:copy(raw??null)});continue;}
  dependency(raw.request?.url??raw.url,reference,'retained-'+field);dependency(raw.response?.url,reference,'retained-response');
  if(field==='policyViolations'){policyViolations.push({source:'retained-policy-violation',reference,...copy(raw)});if(!seenReceipts.has(reference.eventReceiptId))issue('POLICY_WITHOUT_PRIMARY_RECEIPT',{reference});}
  else{const kind=field==='httpErrors'?'HTTP_ERROR':field==='fetchErrors'?'FETCH_ERROR':'CONSOLE_ERROR';if(!observedErrors.some(e=>e.kind===kind&&e.reference?.eventReceiptId===reference.eventReceiptId))observedErrors.push({kind,reference,raw:copy(raw)});if(field!=='consoleErrors'&&!seenReceipts.has(reference.eventReceiptId))issue('ERROR_WITHOUT_PRIMARY_RECEIPT',{reference});}
 }
 for(const r of records){const cdp=r.terminals.filter(t=>t.method.startsWith('goog:')),bidi=r.terminals.filter(t=>t.method.startsWith('network.'));
  if(cdp.length>1||bidi.length>1)issue('MULTIPLE_TERMINALS',{key:r.key,references:r.terminals.map(t=>t.reference)});
  if(r.responses.filter(t=>t.method.startsWith('goog:')).length>1||r.responses.filter(t=>t.method.startsWith('network.')).length>1)issue('MULTIPLE_RESPONSES_WITHOUT_SUPPORTED_REDIRECT',{key:r.key,references:r.responses.map(t=>t.reference)});
  for(const observation of [...r.responses,...r.terminals])if(observation.raw?.response?.url&&!sameURL(observation.raw.response.url,r.url)&&!sameURL(observation.raw.response.url,r.bidi?.url))issue('RESPONSE_URL_WITHOUT_SUPPORTED_REDIRECT',{key:r.key,reference:observation.reference});
  const kinds=new Set(r.terminals.map(t=>/loadingFailed|fetchError/.test(t.method)?'observed-error':'observed-completion'));
  if(kinds.size>1)issue('CONTRADICTORY_TERMINALS',{key:r.key});r.outcome=kinds.has('observed-error')?'observed-error':kinds.has('observed-completion')?'observed-completion':'unobserved';
 }
 // Source/consumer evidence comes from the original snapshot, independently of
 // network outcomes. Incomplete attempts may still have valid source identity.
 const smoke=row.snapshot?.smoke??row.smoke,consumers=[],consumerGaps=[];
 const indexHash=PINNED_SOURCE['index.html'].sha256;
 function profile(f){return !!f&&f.sourceSha256===indexHash&&/^[a-f0-9-]{36}$/.test(f.documentId||'')&&f.mode==='healthy'&&nonempty(f.run)&&Number.isInteger(f.attempt)&&f.attempt>0&&typeof f.hash==='string'&&f.scriptContract==='salah-native-script-adapter/1'&&f.scriptProfile==='split-moon'&&JSON.stringify(f.scriptPrerequisites)===JSON.stringify(PREREQUISITES)&&f.firstPaintSourceSha256===PREREQUISITES[0].sha256;}
 function consumed(f){return Array.isArray(f?.ledger)&&f.ledger.some(x=>{try{const u=new URL(x.url);return x.attempt===f.attempt&&u.origin==='https://api.aladhan.com'&&u.pathname==='/v1/timings/07-09-2026'&&x.jsonReads>0&&x.result==='json-consumed';}catch{return false;}});}
 for(const [i,a]of array(smoke?.fixture?.attempts,'/snapshot/smoke/fixture/attempts').entries()){
  if(!a||typeof a!=='object'){consumerGaps.push({kind:'MALFORMED_FIXTURE_ATTEMPT',index:i});continue;}
  const f=a.fixture,bound=profile(f)&&f.run===smoke.fixture.run&&f.attempt===a.attempt&&f.hash===a.hash&&a.mode==='healthy'&&(a.documentId===undefined||a.documentId===f.documentId)&&(a.sourceSha256===undefined||a.sourceSha256===f.sourceSha256);
  consumers.push({key:'smoke:'+a.attempt,fixture:f,bound,pointer:'/snapshot/smoke/fixture/attempts/'+i+'/fixture',result:a.result});
 }
 const b=row.nativeNoPreferenceBaseline;
 if((row.preferenceRequested==='no-preference'||row.plannedTopLevelDocuments===2)&&!b)consumerGaps.push({kind:'NATIVE_BASELINE_MISSING'});
 if(b){const f=b.data?.fixture,o=b.data?.owner,bound=profile(f)&&f.run===b.expectedRun&&f.attempt===b.expectedAttempt&&f.hash===b.expectedHash&&f.sourceSha256===b.expectedSourceSha256&&b.data.hash===f.hash&&b.data.url===b.url&&['run','attempt','documentId','sourceSha256'].every(k=>o?.[k]===f[k]);consumers.push({key:'baseline:'+b.expectedAttempt,fixture:f,bound,pointer:'/nativeNoPreferenceBaseline/data/fixture',result:b.status,expectedURL:b.url});}
 if(consumers.length===0)consumerGaps.push({kind:'NO_ACTUAL_FIXTURE_CONSUMER'});
 for(const c of consumers){if(!c.bound)consumerGaps.push({kind:'FIXTURE_SOURCE_OR_OWNER_UNBOUND',consumer:c.key});if(!consumed(c.fixture))consumerGaps.push({kind:'CURRENT_JSON_NOT_CONSUMED',consumer:c.key});}
 const requiredChecks=['originalDenominator','fullOriginalHealthy','exactHealthyLog','freshOwnedActualSources','terminalWithin120000ms','childPreference',...(b?['actualNativeNoPreferenceConsumer']:[])];
 for(const key of requiredChecks)if(row.checks?.[key]!==true)consumerGaps.push({kind:'ORIGINAL_REQUIRED_CHECK_NOT_PASSED',check:key});
 function fixtureFor(url){try{const u=new URL(url);if(u.origin!==new URL(PUBLIC).origin||u.pathname!==new URL('tests/widget-fixture.html',PUBLIC).pathname)return null;const list=consumers.filter(c=>c.bound&&u.searchParams.get('mode')===c.fixture.mode&&u.searchParams.get('run')===c.fixture.run&&u.searchParams.get('attempt')===String(c.fixture.attempt)&&u.hash.slice(1)===c.fixture.hash&&(!c.expectedURL||url===c.expectedURL));return list.length===1?list[0]:null;}catch{return null;}}
 const rootSession=s.securityProvenance?.session,topFrame=s.securityProvenance?.context;
 function documentFor(start){
  const p=start.p,c=fixtureFor(p.initiator?.url);if(!c||!nonempty(p.frameId)||p.initiator?.type!=='other')return null;
  const frames=lifecycle.filter(x=>x.valid&&x.e.method==='goog:cdp.Page.frameNavigated'&&x.session===rootSession&&x.p?.frame?.id===p.frameId&&x.p.frame.url+(x.p.frame.urlFragment||'')===p.initiator.url&&x.index<start.index);
  if(frames.length!==1)return null;const frame=frames[0],f=frame.p.frame;
  if(!nonempty(f.loaderId)||f.id!==topFrame&&f.parentId!==topFrame)return null;
  const next=lifecycle.find(x=>x.e.method==='goog:cdp.Page.frameNavigated'&&x.p?.frame?.id===f.id&&x.index>frame.index);
  if(next&&next.index<start.index)return null;
  const documents=starts.filter(x=>x.valid&&x.session===rootSession&&x.p.type==='Document'&&x.p.frameId===f.id&&x.p.loaderId===f.loaderId&&x.p.request.url+(x.p.request.urlFragment||'')===p.initiator.url&&x.index<frame.index);
  const opened=lifecycle.filter(x=>x.valid&&x.e.method==='goog:cdp.Page.documentOpened'&&x.session===rootSession&&x.p?.frame?.id===f.id&&x.p.frame.loaderId===f.loaderId&&x.p.frame.url+(x.p.frame.urlFragment||'')===p.initiator.url&&x.index>frame.index&&x.index<start.index);
  const runtimes=lifecycle.filter(x=>x.valid&&x.e.method==='goog:cdp.Runtime.executionContextCreated'&&x.session===rootSession&&x.p?.context?.auxData?.frameId===f.id&&x.p.context.auxData.isDefault===true&&x.p.context.auxData.type==='default'&&x.p.context.origin===new URL(PUBLIC).origin&&nonempty(x.p.context.uniqueId)&&x.index>frame.index&&x.index<start.index);
  if(documents.length!==1||opened.length!==1||runtimes.length!==1)return null;
  const realmId=runtimes[0].p.context.uniqueId,realms=lifecycle.filter(x=>x.valid&&x.e.method==='script.realmCreated'&&x.e.params?.realm===realmId&&x.e.params?.type==='window'&&x.e.params?.context===f.id&&x.e.params?.origin===new URL(PUBLIC).origin&&x.index>frame.index&&x.index<start.index);
  if(realms.length!==1||lifecycle.some(x=>x.e.method==='script.realmDestroyed'&&x.e.params?.realm===realmId&&x.index<start.index))return null;
  return {consumer:c.key,fixturePointer:c.pointer,documentId:c.fixture.documentId,sourceSha256:c.fixture.sourceSha256,frameId:f.id,loaderId:f.loaderId,documentRequest:documents[0].reference,frameNavigation:frame.reference,documentOpened:opened[0].reference,windowRuntime:runtimes[0].reference,windowRealm:{id:realmId,created:realms[0].reference},fixtureURL:p.initiator.url};
 }
 function bootstrap(start,visited=new Set()){
  if(!start?.valid||visited.has(start))return null;visited.add(start);const p=start.p,u=p.request?.url;
  if(p.type!=='Script'||p.request?.method!=='GET'||p.loaderId!==''||typeof u!=='string'||!u.startsWith('blob:'+new URL(PUBLIC).origin+'/')||p.documentURL!==u)return null;
  const document=documentFor(start);if(!document)return null;
  if(start.session===rootSession)return {kind:'PINNED_WINDOW_BLOB_PRODUCER_SET',exactProducer:null,possibleProducers:['moon-refinement','native-sky'],document,bootstrap:start.reference};
  const a=childAttachments.get(start.session)||[];if(a.length!==1||a[0].p.targetInfo.type!=='worker')return null;
  const parents=bySessionId.get(JSON.stringify([a[0].session,a[0].p.targetInfo.targetId]))||[];if(parents.length!==1)return null;
  const parent=parents[0],owner=bootstrap(parent,visited);if(!owner||owner.document.documentId!==document.documentId||!sameURL(a[0].p.targetInfo.url,parent.p.request.url))return null;
  const child=targetAttachments.get(JSON.stringify([start.session,p.requestId]))||[];
  if(child.length!==1||child[0].p.targetInfo.type!=='worker'||child[0].p.targetInfo.parentId!==parent.p.requestId||child[0].p.targetInfo.parentFrameId!==document.frameId)return null;
  if(!starts.some(x=>x.session===start.session&&moonAsset(x,a[0],parent)))return null;
  return {kind:'PINNED_MOON_SHARD_BOOTSTRAP',exactProducer:'moon-refinement',document,bootstrap:start.reference,creatorBootstrap:parent.reference,creatorAttachment:a[0].reference,childAttachment:child[0].reference};
 }
 function moonAsset(start,attachment,parent){const p=start.p,u=parent.p.request?.url,stack=p.initiator?.stack?.callFrames,want=[['read',609],['from',617],['boot',618],['self.onmessage',667]];
  return start.session===attachment.p.sessionId&&attachment.p.targetInfo.type==='worker'&&sameURL(attachment.p.targetInfo.url,u)&&p.request?.method==='GET'&&p.type==='Fetch'&&p.loaderId===''&&[PUBLIC+'moon/assets/dem.bin.gz',PUBLIC+'moon/assets/colour.bin.gz'].includes(p.request.url)&&p.documentURL===u&&p.initiator.type==='script'&&Array.isArray(stack)&&stack.length===4&&want.every(([fn,line],i)=>stack[i].functionName===fn&&stack[i].lineNumber===line&&stack[i].url===u);
 }
 function assetClass(start){if(!start?.valid)return null;const a=childAttachments.get(start.session)||[];if(a.length!==1)return null;const ps=bySessionId.get(JSON.stringify([a[0].session,a[0].p.targetInfo.targetId]))||[];if(ps.length!==1||!moonAsset(start,a[0],ps[0]))return null;const owner=bootstrap(ps[0]);return owner?{kind:'PINNED_MOON_ASSET',exactProducer:'moon-refinement',document:owner.document,creatorBootstrap:ps[0].reference,subjectAttachment:a[0].reference}:null;}
 function lifetime(start,r){
  let a;if(start.p.type==='Script')a=(targetAttachments.get(JSON.stringify([start.session,start.p.requestId]))||[]);else a=childAttachments.get(start.session)||[];
  if(a.length===1){const owner=a[0],runtime=lifecycle.filter(x=>x.e.method==='goog:cdp.Runtime.executionContextCreated'&&x.session===owner.p.sessionId&&nonempty(x.p?.context?.uniqueId));
   if(runtime.length===1){const realm=runtime[0].p.context.uniqueId,created=lifecycle.filter(x=>x.e.method==='script.realmCreated'&&x.e.params?.realm===realm),ended=lifecycle.filter(x=>x.e.method==='script.realmDestroyed'&&x.e.params?.realm===realm);
    if(created.length===1){r.reportedLifetime.subjectRealm={id:realm,created:created[0].reference,reportedOwners:copy(created[0].e.params?.owners??null)};if(ended.length===1)r.reportedLifetime.subjectRealmEnd=ended[0].reference;}}
   const ends=lifecycle.filter(x=>x.e.method==='goog:cdp.Target.detachedFromTarget'&&x.session===owner.session&&x.p?.sessionId===owner.p.sessionId&&x.p?.targetId===owner.p.targetInfo.targetId);if(ends.length===1)r.reportedLifetime.detach=ends[0].reference;
  }
 }
 const materialUnknowns=[];
 for(const r of records){const start=starts.find(x=>x.record===r);if(start?.valid)lifetime(start,r);
  r.sourceClass=start?(bootstrap(start)||assetClass(start)):null;
  const script=start?.p?.type==='Script'||r.bidi?.destination==='script',blob=typeof r.url==='string'&&r.url.startsWith('blob:');
  if(script){const executableURLs=[r.url,...r.responses.map(x=>x.raw?.response?.url).filter(Boolean)];
   const known=raw=>{try{const u=new URL(raw);return u.origin===new URL(PUBLIC).origin&&['config.js','tests/native-script-contract.js','real-sky/native-sky.js','real-sky/native-data.js'].some(p=>new URL(p,PUBLIC).pathname===u.pathname);}catch{return false;}};
   if(blob?!r.sourceClass:!executableURLs.every(known))materialUnknowns.push({key:r.key,url:r.url,kind:'UNREVIEWED_EXECUTABLE',requiredClaim:'The finite executable producer set cannot be enlarged by URL allowance or completion'});
  }
  if(r.outcome==='unobserved'&&!r.sourceClass)materialUnknowns.push({key:r.key,url:r.url,kind:'UNBOUND_UNKNOWN_RESOURCE',requiredClaim:'Bounded source/producer relevance and observed dependency identity'});
  if(!r.sourceClass&&r.outcome!=='unobserved')r.sourceClass={kind:'OBSERVED_OUTCOME',requiredConsumption:'No per-request consumer claim'};
  const realm=r.sourceClass?.document?.windowRealm?.id;
  if(realm){const end=lifecycle.filter(x=>x.valid&&x.e.method==='script.realmDestroyed'&&x.e.params?.realm===realm);if(end.length===1)r.reportedLifetime.creatorRealmEnd=end[0].reference;}
 }
 const sourceClaimsBound=localOK&&publicOK&&processScopeEnd.verified&&!!finalBoundary&&captureProblems.length===0&&materialUnknowns.length===0&&consumers.length>0&&consumers.every(c=>c.bound);
 return {schema:SCHEMA,method:METHOD,records,orphans,captureProblems,policyViolations,observedErrors,materialUnknowns,
  allObservedRecordsReconciled:records.length>0&&captureProblems.length===0,allNetworkOutcomesObserved:records.length>0&&records.every(r=>r.outcome!=='unobserved'),sourceClaimsBound,
  requiredConsumerEvidence:{satisfied:consumerGaps.length===0,gaps:consumerGaps,consumers:consumers.map(c=>({key:c.key,fixturePointer:c.pointer,sourceBound:c.bound,currentJSONConsumed:consumed(c.fixture),originalResult:c.result})),scope:'Actual fixture transport and original required checks; no protocol-ID linkage to resource consumption'},
  processScopeEnd,finalBoundaryTraceSequence:finalBoundary?.traceSequence??null,observedDependencies:[...dependencies.values()],
  counts:{records:records.length,completed:records.filter(r=>r.outcome==='observed-completion').length,error:records.filter(r=>r.outcome==='observed-error').length,unknown:records.filter(r=>r.outcome==='unobserved').length,crossSessionCompletions:records.filter(r=>r.outcome==='observed-completion'&&r.terminals.some(t=>t.join?.kind==='EXACT_BOOTSTRAP_PARENT_TARGET_CHILD')).length},
  limitations:['Emitted observed population only; no census of unreported traffic after detach','Reported realm disposal is not physical death','Separate public readback is not browser response-body hashing','Unknown outcomes remain unknown; process exit supplies no request terminal']};
}
function publicDependencies(accounting){if(accounting?.schema!==SCHEMA||accounting.method!==METHOD)throw Error('Final observed-record ledger required for public dependency readback');return copy(accounting.observedDependencies);}
module.exports={METHOD,SCHEMA,PINNED_SOURCE,PUBLIC_SOURCE,admitSource,admitPublicReadback,assertSourceAdmission,reconcile,publicDependencies};
