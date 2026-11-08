'use strict';
/* R0017 phase 2, ordinary executor support. No qualification/closure authority.
 * The controlled JS recipes below port the published October run_controls.py
 * and run_supplement.py. They preserve the actual 30-case instrument and use
 * its original required(), loadUntil(), scene(), motion and config callbacks.
 * Only explicit disposable HTTP responses and the held automatic invocation
 * vary. Neither the candidate tree nor the delivered public bytes are edited.
 */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {setTimeout:delay}=require('node:timers/promises');
const START='(async()=>{try{await run();}catch(e){line("fail","harness error: "+e.message);}finally{finalize();}})();';
const HASH='lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&simWx=0';
const MOTION_NAMES=['explicit reduced + full motion','motion=full overrides reduction'];
const MOTION_ANCHOR='const isMotionReduced = () => !MOTIONFULL && !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);';
const HISTORY=Object.freeze({archive:'R0017_EVIDENCE_20261014.zip',archiveSha256:'3544f2349137495e2b7b49beb38a46de52a480ffa6c5472a88f24284708c7d8c',
 controls:{member:'evidence/drivers/run_controls.py',sha256:'9b4a8fe6b1d29c98e63f8f40a26afc40f9816f877dfc1a958f21ad033340ef7f'},
 supplement:{member:'evidence/drivers/run_supplement.py',sha256:'5d8b32c3eefb21f465a5e58cfd96d7f8c99febc789e0cbd1e61663c38aa29adb'},
 boundaries:{member:'evidence/drivers/run_native_boundaries.py',sha256:'8d1b776170999d72b8a58cfdb8633c98d6cc840de6df002f8ca1d8b99ecb7993'},
 strict:{member:'evidence/drivers/qualify_control_records.py',sha256:'ef8875805f098d87f4e77bae1deb569ba814e4e5679e32beccfa0e59fb708937'}});
// Noon is above 40 degrees in the pinned Madinah scene. With heat in [0,1],
// the actual writer's 0.045+0.035*heat and 0.015 sine terms bound the rounded
// scale to [0.90495,1.09505]. A property alone is insufficient: both real CSS
// consumers must expose the same positive matrix scale.
const PULSE_RANGE=Object.freeze({minimum:0.90495,maximum:1.09505,roundingSlack:0.00005,source:'paintSolarPresentation --sunpulse; noon clamp=1; heat clamped to [0,1]'});
const READ=`w=>{const q=w.qaState(),m=w.model(),card=w.document.querySelector('.c'),raw=card?w.getComputedStyle(card).getPropertyValue('--sunpulse'):null;
 const pulse=typeof raw==='string'&&raw.trim()!==''?Number(raw):null;
 return {fixture:w.__widgetFixture,qa:q,model:m,nextTime:m.nextTime,url:w.location.href,hash:w.location.hash.slice(1),
 owner:w.__smokeWeather&&typeof w.__smokeWeather.identity==='function'?w.__smokeWeather.identity():null,
 dom:{times:w.document.querySelector('.times')?.innerText??null,next:w.document.querySelector('.nt')?.innerText??null,countdown:w.document.querySelector('.panel .left')?.innerText??null},
 pulseRaw:raw,pulse:Number.isFinite(pulse)?pulse:null,
 transforms:['.suncorner .corona','.suncorner .rays'].map(selector=>{const nodes=w.document.querySelectorAll(selector),value=nodes.length===1?w.getComputedStyle(nodes[0]).transform:null;let matrix=null,error=null;try{if(value&&value!=='none'){const a=new w.DOMMatrixReadOnly(value);matrix={is2D:a.is2D,m11:a.m11,m12:a.m12,m21:a.m21,m22:a.m22};}}catch(e){error=String(e);}return {selector,count:nodes.length,raw:value,matrix,error};}),
 rect:(()=>{if(!card)return null;const b=card.getBoundingClientRect();return {width:b.width,height:b.height};})(),
 motionFull:!!card&&card.classList.contains('motionfull'),nativeReduced:w.__r0017OriginalMatchMedia('(prefers-reduced-motion: reduce)').matches,
 originalMatchMediaRestored:w.matchMedia===w.__r0017OriginalMatchMedia};}`;
// The accepted per-frame finally observer now retains raw CSS and actual effect.
// Observation errors are recorded rather than replacing the original exception.
const OBSERVER=`const observations=[];const originalScene=scene;
scene=(hash,name,fn,ready)=>originalScene(hash,name,(ww,q,ok)=>{
 try{return fn(ww,q,ok);}finally{try{const surface=(${READ})(ww);observations.push({name,documentId:ww.__widgetFixture.documentId,
 exact:ww.matchMedia===ww.__r0017OriginalMatchMedia,nativeReduced:surface.nativeReduced,pulse:surface.pulse,pulseRaw:surface.pulseRaw,surface});}
 catch(error){observations.push({name,captureError:String(error&&error.stack||error)});}}
},ready);`;
// Accepted private-operation observer; no Storage.prototype/global clear.
const STORES=`const originalPrivateStorage=privateStorage,privateStores=[];
privateStorage=()=>{const s=originalPrivateStorage(),keys=['salah_widget:config:v1','__sw_probe__','private-unrelated'],events=[];
 s.setItem('__sw_probe__','private intentional probe');s.setItem('private-unrelated','private retained bytes Ω');
 const snapshot=()=>Object.fromEntries(keys.map(k=>[k,s.getItem(k)]));
 const r={initial:snapshot(),events,snapshot};privateStores.push(r);
 return {getItem(k){const v=s.getItem(k);events.push(['get',k,v]);return v;},
 setItem(k,v){events.push(['set',k,v]);s.setItem(k,v);},removeItem(k){events.push(['remove',k]);s.removeItem(k);}};
};`;
function once(s,a,b,label=a){if(s.split(a).length!==2)throw Error('Nonunique phase-2 mutation anchor: '+label);return s.replace(a,b);}
function between(s,a,b){if(s.split(a).length!==2||s.split(b).length!==2)throw Error('Ambiguous phase-2 extraction');const i=s.indexOf(a),j=s.indexOf(b,i);if(j<=i)throw Error('Reversed extraction');return s.slice(i,j);}
function allTrue(checks){return Object.keys(checks).length>0&&Object.values(checks).every(x=>x===true);}
function bodyReady(f){return !!f&&f.state==='ready'&&f.error===null&&f.storageIsolated===true&&f.clockFixed===true&&f.fetchIntercepted===true;}
function clone(v){return JSON.parse(JSON.stringify(v));}

const CALENDAR_DIAGNOSTIC_RECIPE_SHA256='30949220ab5d58eb125e1676ad7213ebda9609692870cbedde7e4b4188e09a23';
const calendarDiagnosticRecipe=function calendarDiagnosticRecipe({hash,sourceSha256}){
 if(typeof hash!=='string'||!hash.startsWith('lat=24.47&lon=39.61&label=Madinah&method=4&')||!/^[a-f0-9]{64}$/.test(sourceSha256))throw Error('Exact controlled hash and pinned payload SHA256 required');
 const wanted=hash+'&tz=Asia/Riyadh&qa=1';
 return {
  prefix:`
const r0017OriginalLoadUntil=loadUntil,r0017BoundaryReads=[];
let r0017ObservedCalls=0;
loadUntil=function(...parameters){
 const promise=r0017OriginalLoadUntil.apply(this,parameters);
 r0017ObservedCalls++;
 const observedCall=r0017ObservedCalls;
 // Attach before scene awaits the SAME original promise. No replacement promise,
 // delay, readiness retry, error conversion, or added successful-case inspection.
 promise.then(value=>{
  if(value&&value.w)return;
  const record={schema:'r0017-post-readiness-boundary/v1',phase:'after-original-loadUntil-resolved-before-scene-continuation',observedCall,
   input:{hash:parameters[0],boundMs:parameters[1]},expectedHash:${JSON.stringify(wanted)},sourceSha256:${JSON.stringify(sourceSha256)},
   observedParentMonotonicMs:performance.now(),originalResult:{error:value?.error??null,reason:value?.reason??null,hasWindow:!!value?.w},ownerAccepted:false};
  try{
   const row=attempts.at(-1),w=fr.contentWindow,f=w&&w.__widgetFixture;
   record.attempt=row?.attempt??null;record.documentId=f?.documentId??null;record.originalAttemptResult=row?.result??null;
   record.ownerAccepted=parameters[0]===${JSON.stringify(hash)}&&parameters[1]===8000&&document.getElementById('w')===fr&&fr.isConnected&&fr.ownerDocument===document&&
    !!row&&!!w&&!!f&&row.attempt===_r&&f.run===smokeRun&&f.attempt===row.attempt&&row.hash===${JSON.stringify(wanted)}&&f.hash===row.hash&&hashOf(w)===row.hash&&
    /^[a-f0-9-]{36}$/.test(f.documentId||'')&&f.sourceSha256===${JSON.stringify(sourceSha256)}&&row.fixture===f;
   if(record.ownerAccepted){
    const card=w.document.querySelector('.c');record.cardClassBefore=card?.className??null;
    const readState=name=>{try{const api=w[name];return api?{present:true,value:JSON.parse(JSON.stringify(api.state))}:{present:false,value:null};}catch(error){return {present:null,error:String(error?.stack||error)};}};
    record.states={assets:readState('SalahRealSkyAssets'),sky:readState('SalahRealSky'),preview:readState('SalahSkyPreview'),moonDetail:readState('SalahMoonDetail')};
    record.badges=[...w.document.querySelectorAll('.real-sky-status')].map(e=>({text:e.textContent,title:e.title,className:e.className}));
    // Do not add SalahMoonRuntime.state/surface(), host.capture(), realSkyFrame(),
    // request/compose/update/retry/invalidate. Some apparent getters can publish.
    record.runtimeEvidence='Use the original attempt.calendarView observation; no additional runtime getter';
    record.cardClassAfter=card?.className??null;
    record.ownerStillExact=fr.contentWindow===w&&w.__widgetFixture===f&&f.documentId===record.documentId&&f.attempt===row.attempt&&f.hash===row.hash&&f.sourceSha256===${JSON.stringify(sourceSha256)};
   }else record.captureRefused='Current child did not satisfy the exact original attempt/source ownership fence';
  }catch(error){record.captureError=String(error?.stack||error);}
  record.captureEndedParentMonotonicMs=performance.now();r0017BoundaryReads.push(record);
 },error=>{r0017BoundaryReads.push({schema:'r0017-post-readiness-boundary/v1',phase:'original-promise-rejected',observedCall,error:String(error?.stack||error)});});
 return promise;
};
`,
  restore:'loadUntil=r0017OriginalLoadUntil;',
  resultExpression:`({observerCalls:r0017ObservedCalls,helperRestored:loadUntil===r0017OriginalLoadUntil,boundaryReads:r0017BoundaryReads,originalAttempts:attempts,smoke:window.__smoke})`,
  limitations:[
   'This is a post-decision diagnostic, not proof of state throughout the original readiness interval.',
   'An observed failure remains missing/INCOMPLETE. A successful narrow invocation does not become a complete 30/141 smoke.',
   'The extra observer is declared; it does not explain the missing historical Linux result without matching evidence.'
  ]
 };
};

const CALENDAR_DIAGNOSTICS=Object.freeze([
 {id:'diagnostic-calendar-newmoon',group:'calendar-diagnostics',engines:['firefox'],mode:'newmoon',caseName:'new/below-horizon moon: opaque calendar disc, NO moonlight',hash:'lat=24.47&lon=39.61&label=Madinah&method=4&simTime=01:00&simWx=0&simMoon=0.01&simWax=1&simMoonAlt=-20'},
 {id:'diagnostic-calendar-waning',group:'calendar-diagnostics',engines:['firefox'],mode:'waning',caseName:'waning moon orientation',hash:'lat=24.47&lon=39.61&label=Madinah&method=4&simTime=02:00&simWx=0&simMoon=0.3&simWax=0&simMoonAlt=55&simMoonH=0'},
 // NONDEFAULT C13: one current Chromium discriminator, not a historical-cause replay.
 {id:'diagnostic-calendar-waning-c12',group:'waning-diagnostic',engines:['chromium'],mode:'waning',caseName:'waning moon orientation',hash:'lat=24.47&lon=39.61&label=Madinah&method=4&simTime=02:00&simWx=0&simMoon=0.3&simWax=0&simMoonAlt=55&simMoonH=0',
  history:{diagnosticOf:{runId:'42426595933',fixtureAttempt:22,caseName:'chromium-public-healthy-no-preference'},recipeSha256:CALENDAR_DIAGNOSTIC_RECIPE_SHA256,scope:'C12 Chromium/no-preference waning readiness failure. Success is nonreproduction only with zero healthy credit; full 30/141 smoke remains pending. No historical Linux-cause assignment or automatic repeat.'}}
]);
function prepare(api){
 const smoke=fs.readFileSync(path.join(api.ROOT,'tests/smoke.html'),'utf8'),wrapper=fs.readFileSync(path.join(api.ROOT,'tests/widget-fixture.html'),'utf8'),index=fs.readFileSync(path.join(api.ROOT,'index.html'),'utf8');
 if(api.sha(smoke)!=='8f332e35d8012feef103454ee230999d8786118a4699f685b671bfcafa192e4e')throw Error('Phase-2 original smoke lineage changed');
 const declared=JSON.parse(smoke.match(/const CASES=(\[[\s\S]*?\n\]);/)[1]);if(declared.length!==30||declared.reduce((n,x)=>n+x[1],0)!==141)throw Error('30/141 denominator changed');
 for(const x of ['),4000,name)','loadUntil(hash,8000,ready)','),3000,"PBR moon image decode"'])if(!smoke.includes(x))throw Error('Original instrument bound changed');
 const held=once(smoke,START,'window.__r0017HelpersReady=true;','automatic invocation');
 const media=between(smoke,'  const media=reduce=>','  await scene(base+"&simTime=12:30&simWx=0","explicit reduced');
 const motion=between(smoke,'  await scene(base+"&simTime=12:30&simWx=0","explicit reduced','  head("cloud continuity (bounded accelerated');
 const config=between(smoke,'  const SC=window.SalahConfig;','  head("actual fixture transport + weather gate")');
 const plans=[];
 function plan(id,group,extra={}){const p={id,group,preference:'reduce',storage:'valid',viewport:{width:1100,height:900},dpr:1,engines:['chromium','firefox'],history:HISTORY.controls,script:'',overrides:{'tests/smoke.html':Buffer.from(held)},mutations:[{file:'tests/smoke.html',scope:'held automatic invocation only; every original case/helper retained',fromSha256:api.sha(smoke),toSha256:api.sha(held),anchor:START,replacement:'window.__r0017HelpersReady=true;'}],...extra};plans.push(p);return p;}
 function mutate(p,file,from,to,label){const original=file==='index.html'?index:file==='tests/widget-fixture.html'?wrapper:smoke;const current=p.overrides[file]?.toString()||original;const changed=once(current,from,to,label);p.overrides[file]=Buffer.from(changed);p.mutations.push({file,scope:'disposable response only',label,anchor:from,replacement:to,fromSha256:api.sha(current),toSha256:api.sha(changed)});}
 for(const mode of ['native-reduce','ignore-reduction','ignore-full-override','assertion-throw','timeout-exception','actual-callback-timeout']){
  const p=plan('motion-'+mode,'current',{kind:'motion',mode});
  if(mode.startsWith('ignore-'))mutate(p,'index.html',MOTION_ANCHOR,mode==='ignore-reduction'?'const isMotionReduced = () => false;':MOTION_ANCHOR.replace('!MOTIONFULL && ',''),'motion semantic mutant');
  let setup='';
  if(['assertion-throw','timeout-exception'].includes(mode))setup=`const originalRequired=required;required=(name,fn)=>originalRequired(name,ok=>fn((label,cond,detail)=>{if(label==="reduce=true freezes sunpulse to 1"||label==="motion=full wins over reduce=true"){const e=new Error("controlled ${mode}");${mode==='timeout-exception'?'e.name="RequiredTimeout";':''}throw e;}return ok(label,cond,detail);}));`;
  if(mode==='actual-callback-timeout')setup='const originalRequired=required;required=(name,fn)=>originalRequired(name,async ok=>{await fn(ok);return new Promise(()=>{});});';
  p.script=`const positive=await loadUntil(${JSON.stringify(HASH)},8000,prayerReady);if(!positive.w)throw Object.assign(Error('Actual motion positive not ready: '+JSON.stringify(positive)),{code:'R0017_NATIVE_PRECONDITION'});const before=(${READ})(positive.w);
${OBSERVER}${setup}const controlStarted=performance.now();${media}${motion}
finalize();return {before,after:(${READ})(fr.contentWindow),observations,controlElapsedMs:performance.now()-controlStarted,smoke:__smoke,log:out.innerText};`;
 }
 for(const mode of ['body-pending','malformed-json','wrong-response-day','missing-timings','bypass-json','source-anchor','source-digest']){
  const p=plan('transport-'+mode,'current',{kind:'transport',mode,history:HISTORY.strict});
  if(mode==='body-pending')mutate(p,'tests/widget-fixture.html','const response=new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}),nativeJson=response.json.bind(response);','const response=new Response(row.url.includes("api.aladhan.com")?new ReadableStream({start(){}}):JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}}),nativeJson=response.json.bind(response);','native Response headers with pending body');
  if(mode==='malformed-json')mutate(p,'tests/widget-fixture.html','JSON.stringify(value),{status:200','(row.url.includes("api.aladhan.com")?"{malformed":JSON.stringify(value)),{status:200','native Response.json parser rejection');
  if(mode==='wrong-response-day')mutate(p,'tests/widget-fixture.html','return jsonResponse(prayerFixture(day),row);','return jsonResponse(prayerFixture(day==="07-09-2026"?"08-09-2026":"07-09-2026"),row);','native JSON returns the other calendar day; current consumer must not adopt');
  if(mode==='missing-timings')mutate(p,'tests/widget-fixture.html','return jsonResponse(prayerFixture(day),row);','const body=prayerFixture(day);delete body.data.timings.Asr;return jsonResponse(body,row);','native JSON lacks required Asr time; current consumer must not adopt');
  if(mode==='bypass-json')mutate(p,'tests/widget-fixture.html','response.json=()=>{row.jsonReads++;row.result="json-consumed";return nativeJson();};','response.json=()=>Promise.resolve(value);','actual rendered data without native JSON ledger');
  if(mode==='source-anchor')mutate(p,'index.html','<script src="config.js"></script>','<script src="other.js"></script>','shared helper rejects unknown config script anchor');
  if(mode==='source-digest'){const m=index.match(/id="native-first-paint-code"[^>]*data-sha256="([a-f0-9]{64})"/);if(!m)throw Error('Missing first-paint digest attribute');mutate(p,'index.html','data-sha256="'+m[1]+'"','data-sha256="'+'0'.repeat(64)+'"','shared helper rejects first-paint digest mismatch');}
  p.script=`const controlStarted=performance.now();let admitted=false;await scene(${JSON.stringify(HASH)},'weather gate availability',(w,q,ok)=>{admitted=true;ok('controlled unexpected admission reached',true);},prayerReady);const last=attempts[attempts.length-1],w=fr.contentWindow;return {admitted,error:['bootstrap-error','source-mismatch'].includes(last?.result)?last.reason:null,reason:last?.reason??null,attempts,fixture:w.__widgetFixture,qa:typeof w.qaState==='function'?w.qaState():null,controlElapsedMs:performance.now()-controlStarted};`;
 }
 for(const mode of ['matching-tomorrow','duplicate-current-day-tomorrow']){
  const p=plan(mode,'current',{kind:'tomorrow',mode,history:HISTORY.supplement,viewport:{width:375,height:800},dpr:2});
  if(mode==='duplicate-current-day-tomorrow')mutate(p,'tests/widget-fixture.html','return jsonResponse(prayerFixture(day),row);','return jsonResponse(prayerFixture("07-09-2026"),row);','current-day body supplied to distinct tomorrow request');
  const ready=mode==='matching-tomorrow'?'w.qaState().cache.tomorrowLoaded':"w.__widgetFixture.ledger.filter(r=>r.url.includes('/v1/timings/08-09-2026')&&r.jsonReads>0).length>=3";
  p.script=`const controlStarted=performance.now();const t=await loadUntil(${JSON.stringify(HASH)},8000,w=>prayerReady(w)&&${ready});if(!t.w)throw Object.assign(Error('Tomorrow control did not reach actual response consumer: '+JSON.stringify(t)),{code:'R0017_NATIVE_PRECONDITION'});return {consumer:(${READ})(t.w),controlElapsedMs:performance.now()-controlStarted};`;
 }
 // Original calendar callbacks for two retained Firefox diagnostics and one nondefault C12 Chromium diagnostic; no healthy claims.
 const newMoonCall=between(smoke,'  await calendarScene(base+"&simTime=01:00&simWx=0&simMoon=0.01&simWax=1&simMoonAlt=-20",','  await scene(base+"&simTime=01:00&simWx=0&simMoon=0.6&simWax=1&simMoonAlt=40&simMoonH=8",');
 const waningCall=between(smoke,'  await calendarScene(base+"&simTime=02:00&simWx=0&simMoon=0.3&simWax=0&simMoonAlt=55&simMoonH=0",','  head("explicit motion preferences (no assumption about restored OS preference)");');
 const moonDecoder=between(smoke,'  const moonReady=w=>','  await calendarScene(base+"&simTime=02:00&simWx=0&simMoon=0.3&simWax=1&simMoonAlt=55&simMoonH=0",');
 const prerequisiteCall='loadUntil(base+"&simTime=12:30&simWx=0",8000,w=>typeof w.gateWeatherCode==="function"&&typeof w.wxClass==="function")';
 if(!smoke.includes('const initial=await '+prerequisiteCall+';'))throw Error('Original calendar prerequisite anchor changed');
 for(const d of CALENDAR_DIAGNOSTICS){
  const call=d.mode==='newmoon'?newMoonCall:waningCall,recipe=calendarDiagnosticRecipe({hash:d.hash,sourceSha256:api.sha(index)});
  const p=plan(d.id,d.group,{...d,kind:'calendar-diagnostic',preference:'no-preference',history:d.history??{firstNativeRun:'42388898271',recipeSha256:CALENDAR_DIAGNOSTIC_RECIPE_SHA256,scope:'Two original missing Firefox calendar callbacks; no original Linux-cause assignment'},
   diagnosticSource:{targetCallSha256:api.sha(call),decoderSha256:d.mode==='waning'?api.sha(moonDecoder):null,prerequisiteCallSha256:api.sha(prerequisiteCall),additionalReadRecipeSha256:CALENDAR_DIAGNOSTIC_RECIPE_SHA256},diagnosticLimitations:recipe.limitations});
  p.script=`const controlStarted=performance.now(),entryLoadUntil=loadUntil;const prerequisiteResult=await ${prerequisiteCall};
const prerequisite={accepted:!!prerequisiteResult.w,expectedSourceSha,originalAttempt:attempts[0],originalResult:{error:prerequisiteResult.error??null,reason:prerequisiteResult.reason??null,hasWindow:!!prerequisiteResult.w}};
if(!prerequisiteResult.w){finalize();return {prerequisite,targetAttempted:false,targetName:${JSON.stringify(d.caseName)},observerCalls:0,helperRestored:loadUntil===entryLoadUntil,boundaryReads:[],originalAttempts:attempts,smoke:__smoke,controlElapsedMs:performance.now()-controlStarted};}
if(expectedSourceSha!==${JSON.stringify(api.sha(index))})throw Error('Original prerequisite admitted an unexpected source');
${recipe.prefix}
try{${d.mode==='waning'?moonDecoder:''}\n${call}}finally{${recipe.restore}}
finalize();return {...${recipe.resultExpression},prerequisite,targetAttempted:true,targetName:${JSON.stringify(d.caseName)},controlElapsedMs:performance.now()-controlStarted};`;
 }
 // OPTIONAL native replay of byte-current pure recorder subproof. Not default.
 for(const raw of ['valid','malformed','absent'])for(const outcome of ['success','failure','exception','timeout']){
  const p=plan('recorder-'+raw+'-'+outcome,'optional-recorder',{kind:'recorder',storage:raw,outcome});
  const callback={success:'ok=>ok("native recorder control",true)',failure:'ok=>ok("native recorder control",false)',exception:'()=>{throw Error("controlled callback exception");}',timeout:'ok=>{window.lateOk=ok;return new Promise(()=>{});}'}[outcome];
  const late=outcome==='timeout'?`const before=pass;await required("cloud identity is stable (no reseed per read)",ok=>{lateOk("late result cannot count for newer callback",true);ok("current callback",true);});lateOk("late after missing",true);finalize();late={before,after:pass,smoke:JSON.parse(JSON.stringify(__smoke))};`:'';
  p.script=`const controlStarted=performance.now();await required("weather gate availability",${callback});finalize();const first=JSON.parse(JSON.stringify(__smoke)),firstLog=out.textContent,elapsedMs=performance.now()-controlStarted;let late=null;${late}return {first,firstLog,late,controlElapsedMs:elapsedMs,log:out.innerText};`;
 }
 // OPTIONAL stronger original config/persistence outcome replay; published recipe.
 for(const raw of ['valid','malformed','absent'])for(const outcome of ['success','failure','exception','timeout']){
  const p=plan('config-storage-'+raw+'-'+outcome,'optional-config-storage',{kind:'config-storage',storage:raw,outcome,history:HISTORY.supplement});let setup='';
  if(outcome!=='success'){
   const after=outcome==='timeout'?'return new Promise(()=>{});':'return result;';
   const check='if(label==="clearLocal removes the private saved config"){'+(outcome==='failure'?'cond=false;':outcome==='exception'?'throw Error("controlled post-persistence exception");':'')+'}';
   setup='const originalRequired=required;required=(name,fn)=>originalRequired(name,async ok=>{if(name!=="config private persistence")return fn(ok);const result=await fn((label,cond,detail)=>{'+check+'return ok(label,cond,detail);});'+after+'});';
  }
  p.script=`const controlStarted=performance.now();${STORES}${setup}${config}finalize();return {smoke:__smoke,stores:privateStores.map(s=>({initial:s.initial,final:s.snapshot(),events:s.events})),controlElapsedMs:performance.now()-controlStarted,log:out.innerText};`;
 }
 const contract=require(path.join(api.ROOT,'tests/native-script-contract.js'));
 for(const p of plans){
  new Function('return (async()=>{'+p.script+'});');
  const product=p.overrides['index.html']||Buffer.from(index),scripts=contract.parseScripts(product.toString());
  p.expectedIndexSha256=api.sha(product);p.expectedWrapperSha256=api.sha(p.overrides['tests/widget-fixture.html']||Buffer.from(wrapper));
  try{const a=contract.admitScripts(product.toString(),scripts,scripts.map(s=>api.sha(s.body)),p.expectedIndexSha256);p.offlineAdmission={profile:a.profile,kind:a.provenance.kind,nativeSha256:api.sha(a.native.body),prerequisites:a.prerequisites};}
  catch(e){p.offlineAdmission={error:String(e.message)};}
  if(p.kind==='motion'&&p.mode.startsWith('ignore-')&&p.offlineAdmission.profile!=='split-moon')throw Error('Semantic mutant would not reach current admitted native body: '+p.id);
  if(p.kind==='transport'&&p.mode.startsWith('source-')&&!p.offlineAdmission.error)throw Error('Source mutant unexpectedly admitted offline: '+p.id);
 }
 return {plans,declared,heldSha256:api.sha(held),history:HISTORY,sourceSpans:{media:api.sha(media),motion:api.sha(motion),config:api.sha(config),newMoonCall:api.sha(newMoonCall),waningCall:api.sha(waningCall),moonDecoder:api.sha(moonDecoder),prerequisiteCall:api.sha(prerequisiteCall)},groups:['current','public','calendar-diagnostics','waning-diagnostic','optional-recorder','optional-config-storage']};
}

function sameValue(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function sourceError(mode){return 'SETUP_INCOMPLETE: '+(mode==='source-anchor'?'Unreviewed widget script anchors':'First-paint source identity mismatch');}
function assertionRows(log){
 if(typeof log!=='string')return null;
 const rows={pass:[],fail:[],skip:[]};
 for(const line of log.split(/\r?\n/)){let m;if((m=/^✓ PASS  (.*)$/.exec(line)))rows.pass.push(m[1]);else if((m=/^✗ FAIL  (.*)$/.exec(line)))rows.fail.push(m[1]);else if((m=/^• MISSING  (.*)$/.exec(line)))rows.skip.push(m[1]);}
 return rows;
}
function failureMatches(actual,expected){
 if(typeof expected==='string')return actual===expected;
 const prefix=expected.label+' — ',detail=typeof actual==='string'&&actual.startsWith(prefix)?actual.slice(prefix.length):'';
 return detail.trim()!==''&&/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i.test(detail)&&Number.isFinite(Number(detail));
}
function expectedNarrow(p,declared,phase='final'){
 const entries=declared.map(([name,expected])=>({name,expected,assertions:0,state:'pending',reason:null}));
 const put=(name,state,assertions,reason=null)=>{const x=entries.find(c=>c.name===name);if(!x)throw Error('Undeclared narrow case: '+name);Object.assign(x,{state,assertions,reason});};
 const spec={pass:0,fail:0,skip:0,failures:[],skips:[],entries,attempts:[]};
 const want=HASH+'&tz=Asia/Riyadh&qa=1',ready=hash=>({hash,result:'ready',reason:null});
 if(p.kind==='motion'){
  spec.attempts=[ready(want),ready(want),ready(HASH+'&motion=full&tz=Asia/Riyadh&qa=1')];
  if(p.mode==='native-reduce'){spec.pass=5;put(MOTION_NAMES[0],'executed',3);put(MOTION_NAMES[1],'executed',2);}
  else if(p.mode==='ignore-reduction'||p.mode==='ignore-full-override'){
   spec.pass=4;spec.fail=1;put(MOTION_NAMES[0],p.mode==='ignore-reduction'?'failed':'executed',3);put(MOTION_NAMES[1],p.mode==='ignore-full-override'?'failed':'executed',2);
   spec.failures=[{label:p.mode==='ignore-reduction'?'reduce=true freezes sunpulse to 1':'motion=full wins over reduce=true'}];
  }else if(p.mode==='assertion-throw'){
   spec.fail=2;for(const name of MOTION_NAMES){put(name,'failed',0,'controlled assertion-throw');spec.failures.push(name+' — callback error: controlled assertion-throw');}
  }else if(p.mode==='timeout-exception'||p.mode==='actual-callback-timeout'){
   const actual=p.mode==='actual-callback-timeout';spec.pass=actual?5:0;spec.skip=2;
   for(const [i,name]of MOTION_NAMES.entries()){const reason=actual?name+' deadline exceeded':'controlled timeout-exception';put(name,'missing',actual?[3,2][i]:0,reason);spec.skips.push(name+' — '+reason);}
  }else throw Error('Unknown motion accounting mode: '+p.mode);
 }else if(p.kind==='transport'){
  const source=p.mode.startsWith('source-'),reason=source?sourceError(p.mode):'required scene readiness deadline exceeded',name='weather gate availability';
  spec.fail=source?1:0;spec.skip=1;put(name,'missing',0,reason);spec.skips=[name+' — '+reason];if(source)spec.failures=[name+' — fixture bootstrap: '+reason];
  spec.attempts=[{hash:want,result:source?'bootstrap-error':'timeout',reason}];
 }else if(p.kind==='tomorrow')spec.attempts=[ready(want)];
 else if(p.kind==='recorder'){
  const name='weather gate availability';
  if(p.outcome==='success'){spec.pass=1;put(name,'executed',1);}
  else if(p.outcome==='failure'){spec.fail=1;put(name,'failed',1);spec.failures=['native recorder control'];}
  else if(p.outcome==='exception'){spec.fail=1;put(name,'failed',0,'controlled callback exception');spec.failures=[name+' — callback error: controlled callback exception'];}
  else if(p.outcome==='timeout'){spec.skip=1;put(name,'missing',0,name+' deadline exceeded');spec.skips=[name+' — '+name+' deadline exceeded'];if(phase==='final'){spec.pass=1;put('cloud identity is stable (no reseed per read)','executed',1);}}
  else throw Error('Unknown recorder outcome');
 }else if(p.kind==='config-storage'){
  put('config parsing + precedence','executed',14);put('config denied storage','executed',4);const name='config private persistence';
  if(p.outcome==='success'){spec.pass=26;put(name,'executed',8);}
  else if(p.outcome==='failure'){spec.pass=25;spec.fail=1;put(name,'failed',8);spec.failures=['clearLocal removes the private saved config'];}
  else if(p.outcome==='exception'){spec.pass=25;spec.fail=1;put(name,'failed',7,'controlled post-persistence exception');spec.failures=[name+' — callback error: controlled post-persistence exception'];}
  else if(p.outcome==='timeout'){spec.pass=26;spec.skip=1;put(name,'missing',8,name+' deadline exceeded');spec.skips=[name+' — '+name+' deadline exceeded'];}
  else throw Error('Unknown config-storage outcome');
 }else throw Error('Unknown narrow accounting kind: '+p.kind);
 spec.status=spec.fail?'FAIL':'INCOMPLETE';spec.executed=entries.filter(c=>c.state==='executed'||c.state==='failed').length;spec.failed=entries.filter(c=>c.state==='failed').length;
 spec.missing=entries.filter(c=>c.state==='pending'||c.state==='missing').map(c=>c.name);return spec;
}
function attemptPopulation(p,smoke,expected){
 const list=smoke?.fixture?.attempts,run=smoke?.fixture?.run;
 const checks={fixtureMode:smoke?.fixture?.mode==='healthy',runIdentity:typeof run==='string'&&run.length>0,attemptCount:Array.isArray(list)&&list.length===expected.length,attemptOrderAndIdentity:true,attemptDocumentsDistinct:true};
 if(!checks.attemptCount){checks.attemptOrderAndIdentity=false;checks.attemptDocumentsDistinct=false;return checks;}
 const docs=[];
 for(let i=0;i<expected.length;i++){
  const a=list[i],e=expected[i],f=a?.fixture,n=i+1,isReady=e.result==='ready';
  const own=!!a&&a.attempt===n&&a.hash===e.hash&&a.mode==='healthy'&&a.result===e.result&&a.reason===e.reason&&!!f&&f.run===run&&f.attempt===n&&f.hash===e.hash&&f.mode==='healthy'&&/^[a-f0-9-]{36}$/.test(f.documentId||'')&&f.sourceSha256===p.expectedIndexSha256&&Array.isArray(f.consoleErrors)&&f.consoleErrors.length===0;
  const admission=isReady?(a.documentId===f?.documentId&&a.sourceSha256===p.expectedIndexSha256&&bodyReady(f)&&/^[a-f0-9]{64}$/.test(f.bridgeSha256||'')):(a.documentId===undefined&&a.sourceSha256===undefined);
  if(!own||!admission)checks.attemptOrderAndIdentity=false;
  if(f)docs.push(f.documentId);
 }
 checks.attemptDocumentsDistinct=docs.length===expected.length&&new Set(docs).size===docs.length;return checks;
}
function exactNarrowAccounting(p,smoke,declared,log,phase='final'){
 const e=expectedNarrow(p,declared,phase),r=smoke?.required,lines=assertionRows(log);
 const checks={originalDeclaration:Array.isArray(r?.cases)&&r.total===30&&declared.length===30&&declared.reduce((n,x)=>n+x[1],0)===141&&sameValue(r.cases.map(x=>[x.name,x.expected]),declared),
  exactCaseStates:Array.isArray(r?.cases)&&r.cases.length===e.entries.length&&r.cases.every((x,i)=>x.name===e.entries[i].name&&x.expected===e.entries[i].expected&&x.state===e.entries[i].state&&x.assertions===e.entries[i].assertions&&x.reason===e.entries[i].reason),
  exactCounters:!!smoke&&smoke.pass===e.pass&&smoke.fail===e.fail&&smoke.skip===e.skip&&smoke.status===e.status&&r?.executed===e.executed&&r.failed===e.failed,
  exactMissingList:sameValue(r?.missing,e.missing),
  logCounts:!!lines&&lines.pass.length===e.pass&&lines.fail.length===e.fail&&lines.skip.length===e.skip,
  onlyIntendedFailureLines:!!lines&&lines.fail.length===e.failures.length&&lines.fail.every((x,i)=>failureMatches(x,e.failures[i])),
  exactMissingLines:!!lines&&sameValue(lines.skip,e.skips),...attemptPopulation(p,smoke,e.attempts)};
 return {passed:allTrue(checks),checks,expected:{pass:e.pass,fail:e.fail,skip:e.skip,status:e.status,executed:e.executed,failed:e.failed,missing:e.missing,cases:e.entries,attempts:e.attempts,failures:e.failures,skips:e.skips},observedFailureLines:lines?.fail??null};
}
function pulseConsumer(x){
 if(!x||typeof x.pulseRaw!=='string'||x.pulseRaw.trim()===''||!Number.isFinite(x.pulse)||x.pulse<=0||Number(x.pulseRaw)!==x.pulse||x.pulse<PULSE_RANGE.minimum||x.pulse>PULSE_RANGE.maximum)return false;
 // qaState.sim projects partsInTz().dateStr (DD-MM-YYYY), including this pinned noon.
 if(x.qa?.sim!=='07-09-2026 12:30'||!Number.isFinite(x.qa.sunEl)||x.qa.sunEl<40)return false;
 const expected=['.suncorner .corona','.suncorner .rays'];
 return Array.isArray(x.transforms)&&x.transforms.length===2&&x.transforms.every((t,i)=>t.selector===expected[i]&&t.count===1&&typeof t.raw==='string'&&t.raw.trim()!==''&&t.raw!=='none'&&t.error===null&&t.matrix?.is2D===true&&['m11','m12','m21','m22'].every(k=>typeof t.matrix[k]==='number'&&Number.isFinite(t.matrix[k]))&&Math.abs(t.matrix.m11-x.pulse)<=0.000001&&Math.abs(t.matrix.m22-x.pulse)<=0.000001&&Math.abs(t.matrix.m12)<=0.000001&&Math.abs(t.matrix.m21)<=0.000001);
}
function exactOwner(x,expectedSource){const f=x?.fixture,o=x?.owner;return bodyReady(f)&&f.sourceSha256===expectedSource&&/^[a-f0-9]{64}$/.test(f.bridgeSha256||'')&&!!o&&o.run===f.run&&o.attempt===f.attempt&&o.documentId===f.documentId&&o.hash===f.hash&&o.sourceSha256===f.sourceSha256&&x.hash===f.hash;}
function oracle(p,v,row,declared){
 const c=row.checks;const data=v?.data||{};
 row.accounting=exactNarrowAccounting(p,row.smoke,declared,row.snapshot?.assertionLog);c.exactNarrowOutcome=row.accounting.passed;
 c.probeCompleted=v.done===true&&!v.error;
 if(p.kind==='motion'){
  const s=data.smoke,selected=s?.required?.cases?.filter(x=>MOTION_NAMES.includes(x.name))||[],first=selected[0],second=selected[1],obs=data.observations||[];
  c.actualBeforeReady=bodyReady(data.before?.fixture)&&data.before?.qa?.cache?.prayerLoaded===true;c.actualAfterReady=bodyReady(data.after?.fixture);
  c.actualConsumerPresent=pulseConsumer(data.before)&&pulseConsumer(data.after)&&obs.every(o=>pulseConsumer(o.surface));
  c.actualOwnerLinked=exactOwner(data.before,p.expectedIndexSha256)&&exactOwner(data.after,p.expectedIndexSha256)&&data.before?.fixture?.documentId===row.smoke?.fixture?.attempts?.[0]?.fixture?.documentId&&data.after?.fixture?.documentId===row.smoke?.fixture?.attempts?.[2]?.fixture?.documentId;
  c.bothOriginalCallbacksObserved=obs.length===2&&obs.every((x,i)=>x.name===MOTION_NAMES[i]&&x.documentId===row.smoke?.fixture?.attempts?.[i+1]?.fixture?.documentId&&exactOwner(x.surface,p.expectedIndexSha256));
  c.eachExactNativeFunctionRestored=obs.length===2&&obs.every(x=>x.exact===true&&x.nativeReduced===true)&&data.after?.originalMatchMediaRestored===true;
  if(p.mode==='native-reduce'){c.originalAssertions=first?.state==='executed'&&first.assertions===3&&second?.state==='executed'&&second.assertions===2;c.nativeReducedPulse=data.before?.pulse===1;c.fullOverridePulse=data.after?.pulse!==1&&data.after?.motionFull===true;}
  else if(p.mode.startsWith('ignore-')){const target=p.mode==='ignore-reduction'?first:second,label=p.mode==='ignore-reduction'?'reduce=true freezes sunpulse to 1':'motion=full wins over reduce=true';c.mutantReachedItsCompleteAssertionSet=target?.state==='failed'&&target.assertions===target.expected;c.exactIntendedFailLine=(data.log||'').split('\n').some(x=>x.includes('FAIL')&&x.includes(label));const opposite=p.mode==='ignore-reduction'?second:first;c.independentOtherMotionCase=opposite?.state==='executed'&&opposite.assertions===opposite.expected;c.currentHelperAdmittedMutant=data.before?.fixture?.scriptProfile==='split-moon'&&data.before?.fixture?.sourceSha256===p.expectedIndexSha256;}
  else if(p.mode==='actual-callback-timeout'){c.originalFourSecondTimeouts=first?.state==='missing'&&second?.state==='missing'&&first.assertions===3&&second.assertions===2&&data.controlElapsedMs>=8000;c.exactTimeoutReasons=first?.reason==='explicit reduced + full motion deadline exceeded'&&second?.reason==='motion=full overrides reduction deadline exceeded';}
  else{const state=p.mode==='assertion-throw'?'failed':'missing';c.exactExceptionalOutcome=selected.length===2&&selected.every(x=>x.state===state&&x.reason==='controlled '+p.mode);}
 }else if(p.kind==='transport'){
  const f=data.fixture,q=data.qa,today=f?.ledger?.filter(x=>x.url.includes('/v1/timings/07-09-2026?'))||[];
  c.actualFixtureSnapshotOwned=!!f&&f.run===row.smoke?.fixture?.run&&f.attempt===1&&f.documentId===row.smoke?.fixture?.attempts?.[0]?.fixture?.documentId&&f.sourceSha256===p.expectedIndexSha256;
  c.notAdmitted=data.admitted===false;const target=row.smoke?.required?.cases?.find(x=>x.name==='weather gate availability');c.realSceneRecordedMissing=target?.state==='missing'&&target.assertions===0;
  if(p.mode.startsWith('source-')){const error='SETUP_INCOMPLETE: '+(p.mode==='source-anchor'?'Unreviewed widget script anchors':'First-paint source identity mismatch');c.exactCurrentHelperFailure=f?.state==='error'&&f.error===error&&data.error===error;c.beforePrivateHooks=f?.storageIsolated===false&&f.clockFixed===false&&f.fetchIntercepted===false;c.noConsumerRequests=f?.ledger?.length===0;c.sourceFailureIsFail=row.smoke?.status==='FAIL';}
  else{c.actualReadyFixture=bodyReady(f);c.originalEightSecondTimeout=data.error===null&&data.reason==='required scene readiness deadline exceeded'&&data.controlElapsedMs>=8000;c.bodyFailureIsIncomplete=row.smoke?.status==='INCOMPLETE';
   if(p.mode==='bypass-json'){c.realPrayerRenderedWithoutJson=q?.cache?.prayerLoaded===true&&!!q?.render?.currentKey&&!!q?.render?.nextKey;c.noJsonCalls=today.length>0&&f.ledger.every(x=>x.jsonReads===0);}
   else{c.nativeTodayJsonReached=today.length>0&&today.every(x=>x.attempt===1&&x.jsonReads===1&&x.result==='json-consumed'&&x.cache==='no-store');c.prayerNotAdopted=q?.cache?.prayerLoaded===false;}
  }
 }else if(p.kind==='tomorrow'){
  const x=data.consumer,f=x?.fixture,q=x?.qa,rows=f?.ledger?.filter(r=>r.url.includes('/v1/timings/08-09-2026')&&r.jsonReads>0)||[];
  c.actualConsumerOwner=exactOwner(x,p.expectedIndexSha256)&&f?.documentId===row.smoke?.fixture?.attempts?.[0]?.fixture?.documentId;
  c.actualCurrentDayConsumer=bodyReady(f)&&q?.cache?.prayerLoaded===true&&q.cache.prayerDate==='07-09-2026'&&q.render.currentKey==='Dhuhr'&&q.render.nextKey==='Asr'&&q.render.leftMin===180&&x?.model?.nextTime==='15:30';
  c.expectedTomorrowJsonInvocationsReached=rows.length>=(p.mode==='matching-tomorrow'?1:3)&&rows.every(r=>r.result==='json-consumed'&&r.attempt===1);c.actualTomorrowAtSample=q?.cache?.tomorrowLoaded===(p.mode==='matching-tomorrow');row.tomorrowObservationScope=p.mode==='matching-tomorrow'?'Actual matching tomorrow cache adoption observed':'No tomorrow cache adoption at the sample after three json() invocations; terminal settlement of the third response is not asserted';c.originalEightSecondSceneBound=data.controlElapsedMs<8000;c.actualCountdown=x?.dom?.countdown==='3h 0m left until Asr';c.actualCard=x?.rect?.width===325&&x.rect.height===530;
 }else if(p.kind==='recorder'){
  row.firstAccounting=exactNarrowAccounting(p,data.first,declared,data.firstLog,'first');c.exactInitialRecorderOutcome=row.firstAccounting.passed;const entry=data.first?.required?.cases?.find(x=>x.name==='weather gate availability');c.recordedOutcome=entry?.state===({success:'executed',failure:'failed',exception:'failed',timeout:'missing'})[p.outcome];
  c.suppressedCasesRemainMissing=data.first?.status!=='PASS'&&data.first?.required?.missing?.includes('motion=full overrides reduction');
  if(p.outcome==='timeout'){const late=data.late;c.originalFourSecondBound=data.controlElapsedMs>=4000;c.lateCannotCompleteMissingOrNewer=late?.after===late?.before+1&&late?.smoke?.required?.cases?.find(x=>x.name==='weather gate availability')?.state==='missing';}
 }else if(p.kind==='config-storage'){
  const a=data.smoke?.required?.cases||[],expected={success:'executed',failure:'failed',exception:'failed',timeout:'missing'}[p.outcome],stores=data.stores||[];
  c.originalConfigCallbacks=a[0]?.state==='executed'&&a[0].assertions===14&&a[2]?.state==='executed'&&a[2].assertions===4;c.intendedPersistenceOutcome=a[1]?.state===expected&&a[1].assertions===(p.outcome==='exception'?7:8);
  c.privateOperationsDistinguished=stores.length===1&&JSON.stringify(stores[0].final)===JSON.stringify({'salah_widget:config:v1':null,'__sw_probe__':null,'private-unrelated':'private retained bytes Ω'})&&stores[0].events.some(e=>e[0]==='set'&&e[1]==='salah_widget:config:v1');if(p.outcome==='timeout')c.originalFourSecondBound=data.controlElapsedMs>=4000;
 }
}

function diagnosticOracle(p,v,row,declared){
 const d=v?.data||{},s=row.smoke,r=s?.required,lines=assertionRows(row.snapshot?.assertionLog),list=s?.fixture?.attempts||[],target=r?.cases?.find(x=>x.name===p.caseName),c=row.checks;
 const attempted=d.targetAttempted===true,prerequisite=list[0],last=list.at(-1),want=p.hash+'&tz=Asia/Riyadh&qa=1';
 const genealogy=p.history?.diagnosticOf?{diagnosticOf:clone(p.history.diagnosticOf),recipeOriginFirstNativeRun:'42388898271'}:{firstNativeRun:p.history?.firstNativeRun??'42388898271'};
 row.diagnosticTargetState=attempted?(target?.state||'unknown'):'not_executed';
 row.diagnosticProductOutcome={wholeInstrument:s?.status??null,targetState:row.diagnosticTargetState,qualification:'PARTIAL',reason:target?.reason??d.prerequisite?.originalResult?.reason??null,
  scope:'One original target callback after one original admission prerequisite; all other required callbacks stay pending. No full healthy claim; no cause assigned to the older Linux result.'};
 c.probeCompleted=v?.done===true&&!v.error;c.exactHelperRestored=d.helperRestored===true;c.declaredTarget=d.targetName===p.caseName;
 c.prerequisiteRecorded=!!d.prerequisite&&!!prerequisite&&d.prerequisite.originalAttempt?.attempt===1&&d.prerequisite.originalAttempt?.fixture?.documentId===prerequisite.fixture?.documentId&&d.prerequisite.originalResult?.hasWindow===d.prerequisite.accepted;
 const expectedEntries=declared.map(([name,expected])=>({name,expected,assertions:0,state:'pending',reason:null}));
 let pass=0,fail=0,skip=0,executed=0,failed=0,permitted=true,expectedFailures=[],expectedSkips=[];
 if(!attempted){permitted=d.prerequisite?.accepted===false&&list.length===1&&prerequisite?.result!=='ready'&&d.observerCalls===0&&Array.isArray(d.boundaryReads)&&d.boundaryReads.length===0;}
 else{
  c.actualPrerequisiteAdmission=d.prerequisite?.accepted===true&&d.prerequisite.expectedSourceSha===p.expectedIndexSha256;
  const expected=expectedEntries.find(x=>x.name===p.caseName);
  if(!target||!expected)permitted=false;
  else{
   Object.assign(expected,{state:target.state,assertions:target.assertions,reason:target.reason});
   if(target.state==='executed'){pass=expected.expected;executed=1;permitted=target.assertions===expected.expected&&target.reason===null&&last?.result==='ready';}
   else if(target.state==='missing'){
    skip=1;permitted=target.assertions===0;
    const readiness=last?.result==='timeout'&&target.reason==='required scene readiness deadline exceeded'&&last.reason===target.reason;
    const bootstrap=last?.result==='bootstrap-error'&&typeof target.reason==='string'&&target.reason===last.reason&&target.reason===last.fixture?.error;
    const decode=p.mode==='waning'&&last?.result==='ready'&&target.reason==='PBR moon image decode deadline exceeded';
    permitted=permitted&&(readiness||bootstrap||decode);if(bootstrap){fail=1;expectedFailures=[p.caseName+' — fixture bootstrap: '+target.reason];}expectedSkips=[p.caseName+' — '+target.reason];
   }else if(target.state==='failed'){
    executed=1;failed=1;
    if(target.reason!==null){
     const allowed=['Calendar fixture lost its exact current composed stage within the original window'];if(p.mode==='waning')allowed.push('Missing PBR moon image','PBR moon image decode failed');
     permitted=target.assertions===0&&allowed.includes(target.reason)&&last?.result==='ready';fail=1;expectedFailures=[p.caseName+' — callback error: '+target.reason];
    }else{
     const allowed=p.mode==='newmoon'?[{label:'moonlightOpacity is 0'},'calendarMoonVisible (slot not empty)',{label:'calendar disc group opaque at deep night',prefix:'--moongrp='}]:[{label:'waning lit side is LEFT',oneOf:['RIGHT']}];
     expectedFailures=lines?.fail||[];fail=expectedFailures.length;pass=expected.expected-fail;
     const allowedLine=x=>allowed.some(a=>typeof a==='string'?x===a:a.oneOf?a.oneOf.some(value=>x===a.label+' — '+value):a.prefix?x.startsWith(a.label+' — '+a.prefix)&&Number.isFinite(Number(x.slice((a.label+' — '+a.prefix).length))):failureMatches(x,a));
     permitted=target.assertions===expected.expected&&last?.result==='ready'&&fail>0&&fail<=expected.expected&&new Set(expectedFailures).size===fail&&expectedFailures.every(allowedLine);
    }
   }else permitted=false;
  }
 }
 const missing=expectedEntries.filter(x=>x.state==='pending'||x.state==='missing').map(x=>x.name),status=fail?'FAIL':'INCOMPLETE';
 const accounting={permitted,exactCases:Array.isArray(r?.cases)&&r.cases.length===30&&r.cases.every((x,i)=>x.name===expectedEntries[i].name&&x.expected===expectedEntries[i].expected&&x.state===expectedEntries[i].state&&x.assertions===expectedEntries[i].assertions&&x.reason===expectedEntries[i].reason),
  exactCounters:s?.pass===pass&&s?.fail===fail&&s?.skip===skip&&s?.status===status&&r?.executed===executed&&r.failed===failed,exactMissing:sameValue(r?.missing,missing),
  exactLogs:!!lines&&lines.pass.length===pass&&sameValue(lines.fail,expectedFailures)&&sameValue(lines.skip,expectedSkips)};
 const expectedAttempts=attempted?[{hash:HASH+'&tz=Asia/Riyadh&qa=1',result:'ready',reason:null},{hash:want,result:last?.result,reason:last?.reason}]:[{hash:HASH+'&tz=Asia/Riyadh&qa=1',result:prerequisite?.result,reason:prerequisite?.reason}];
 Object.assign(accounting,attemptPopulation(p,s,expectedAttempts));row.accounting={passed:allTrue(accounting),checks:accounting,expected:{pass,fail,skip,status,executed,failed,missing,cases:expectedEntries,attempts:expectedAttempts}};c.exactDiagnosticAccounting=row.accounting.passed;
 if(attempted){
  const trace=last?.calendarView,reads=d.boundaryReads;
  c.oneUntouchedTarget=d.observerCalls===1&&list.length===2&&Array.isArray(d.originalAttempts)&&d.originalAttempts.length===2&&last.hash===want;
  c.originalCalendarTraceRetained=trace?.schema==='r0017-calendar-stage/v1'&&trace.attempt===2&&trace.hash===want&&trace.budgetMs===8000&&trace.styleRestored===true;
  c.failureOnlyBoundaryRead=Array.isArray(reads)&&(last.result==='ready'?reads.length===0:reads.length===1&&reads[0].phase==='after-original-loadUntil-resolved-before-scene-continuation'&&reads[0].observedCall===1&&reads[0].input?.hash===p.hash&&reads[0].input.boundMs===8000&&reads[0].expectedHash===want&&reads[0].sourceSha256===p.expectedIndexSha256&&reads[0].ownerAccepted===true&&reads[0].ownerStillExact===true&&reads[0].documentId===last.fixture.documentId&&reads[0].originalAttemptResult===last.result&&reads[0].originalResult?.reason===last.reason&&!reads[0].captureError);
  row.calendarDiagnostic={originalCalendarView:trace??null,additionalBoundaryReads:reads??null,source:p.diagnosticSource,limitations:p.diagnosticLimitations,...genealogy};
 }else row.calendarDiagnostic={target:'NOT_EXECUTED',reason:'The genuine original source-admission prerequisite failed; no target navigation or retry was performed',prerequisite:d.prerequisite??null,...genealogy};
}

async function variantServer(api){
 const root=fs.realpathSync(api.ROOT);let active=null;const digestCache=new Map();
 const server=http.createServer((req,res)=>{
  let rel,file,bytes,variant=active;try{
   if(!['GET','HEAD'].includes(req.method))throw Error('Only static GET/HEAD');const u=new URL(req.url,'http://127.0.0.1');rel=decodeURIComponent(u.pathname).replace(/^\/+/, '')||'index.html';
   file=fs.realpathSync(path.join(root,rel));if(!file.toLowerCase().startsWith((root+path.sep).toLowerCase())||!fs.statSync(file).isFile())throw Error('Outside static payload');
   bytes=variant?.overrides[rel]||null;
  }catch(e){res.writeHead(404);res.end('Not found');api.record(path.join(api.OUT,'static-server.jsonl'),{utc:new Date().toISOString(),variant:variant?.id??null,url:req.url,status:404,reason:String(e)});return;}
  const size=bytes?bytes.length:fs.statSync(file).size;
  let digest=bytes?api.sha(bytes):digestCache.get(rel);if(!digest){digest=api.sha(fs.readFileSync(file));digestCache.set(rel,digest);}
  res.writeHead(200,{'Content-Type':api.mime[path.extname(file)]||'application/octet-stream','Content-Length':size,'Cache-Control':'no-cache'});
  api.record(path.join(api.OUT,'static-server.jsonl'),{utc:new Date().toISOString(),variant:variant?.id??null,url:req.url,path:rel,status:200,bytes:size,sha256:digest,override:!!bytes});
  if(req.method==='HEAD')res.end();else if(bytes)res.end(bytes);else{const stream=fs.createReadStream(file);stream.on('error',e=>res.destroy(e));res.on('close',()=>stream.destroy());stream.pipe(res);}
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
 return {origin:'http://127.0.0.1:'+server.address().port+'/',set(p){active=p;},close:()=>new Promise(resolve=>{server.closeAllConnections();server.close(resolve);})};
}
function observedWithin(value,observedAt,deadline){return value===true&&Number.isFinite(observedAt)&&Number.isFinite(deadline)&&observedAt<deadline;}
async function sampleBeforeDeadline(session,script,deadline,label,trace=()=>{}){
 const began=performance.now(),value=await session.eval(script),ended=performance.now();
 const timing={label,beganMonotonicMs:began,observedMonotonicMs:ended,deadlineMonotonicMs:deadline,elapsedMs:ended-began,admitted:ended<deadline};trace(timing);
 if(!observedWithin(true,ended,deadline)){const e=Error('Collector '+label+' returned after its declared observation deadline');e.code='R0017_OBSERVATION_LATE';e.timing=timing;throw e;}
 return value;
}
async function waitFor(session,script,deadline,predicate,trace){
 let last=null;while(performance.now()<deadline){last=await sampleBeforeDeadline(session,script,deadline,'readiness',trace);if(predicate(last))return {matched:true,value:last};const remaining=deadline-performance.now();if(remaining>0)await delay(Math.min(150,remaining));}
 return {matched:false,value:last};
}
function timingTrace(api,row,dir){return value=>{api.record(path.join(dir,'observation-timings.jsonl'),value);row.lastObservationTiming=value;};}
function observationError(message){const e=Error(message);e.code='R0017_OBSERVATION_INVALID';return e;}
const HELPER_INITIALIZATION=`return {ready:window.__r0017HelpersReady===true,types:{required:typeof required,loadUntil:typeof loadUntil,scene:typeof scene,calendarScene:typeof calendarScene,finalize:typeof finalize},
 declared:typeof CASES==='undefined'?null:CASES,cases:typeof cases==='undefined'?null:cases,attempts:typeof attempts==='undefined'?null:attempts,
 counters:{pass:typeof pass==='undefined'?null:pass,fail:typeof fail==='undefined'?null:fail,skip:typeof skip==='undefined'?null:skip},smoke:window.__smoke??null,url:location.href};`;
function initializedPageHelpers(v,declared){return v?.ready===true&&Object.values(v.types||{}).length===5&&Object.values(v.types).every(t=>t==='function')&&sameValue(v.declared,declared)&&Array.isArray(v.cases)&&v.cases.length===30&&v.cases.every((c,i)=>c.name===declared[i][0]&&c.expected===declared[i][1]&&c.assertions===0&&c.state==='pending'&&c.reason===null)&&Array.isArray(v.attempts)&&v.attempts.length===0&&v.counters?.pass===0&&v.counters.fail===0&&v.counters.skip===0&&v.smoke===null;}
function nativePreload(api,seed,origin){const original=api.preload(seed,origin,false);return `()=>{if(location.origin!==${JSON.stringify(new URL(origin).origin)})return;window.__r0017OriginalMatchMedia=window.matchMedia;(${original})();}`;}
function exactDenominator(smoke,declared){return !!smoke&&smoke.required?.total===30&&JSON.stringify(smoke.required.cases.map(x=>[x.name,x.expected]))===JSON.stringify(declared);}

function requireObservationReserve(api){if(api.remainingBudgetMs()<150000){const e=Error('Insufficient phase-2 operation budget for unchanged observation and final capture');e.code='R0017_BUDGET_EXHAUSTED';throw e;}}
function classifyError(api,row,e){
 row.setupFailure=row.stage==='setup';row.status=e.code==='R0017_BUDGET_EXHAUSTED'?'COLLECTOR_BUDGET_EXHAUSTED':row.setupFailure?'CAPABILITY_OR_SETUP_ERROR':'COLLECTOR_OR_ATTEMPT_ERROR';row.error=String(e.stack||e);if(e.timing)row.failedObservationTiming=e.timing;
 if(e.code==='R0017_BUDGET_EXHAUSTED')api.result.stopLaunches={kind:'orchestration-budget',case:row.name,receipt:row.name+'/result.json',reason:row.error};
 else{api.result.engineSetupBlocks[row.engine]={kind:row.setupFailure?'engine-setup':'engine-observation',case:row.name,receipt:row.name+'/result.json',reason:row.error};if(!row.installed)api.result.inventory[row.engine]={status:'UNAVAILABLE',error:row.error,receipt:row.name+'/result.json'};}
}
function snapshotScript(api,row){
 if(row.kind!=='calendar-diagnostic')return api.SNAPSHOT;
 let script=api.SNAPSHOT;
 for(const [anchor,replacement]of [
  ["qa:typeof w.qaState==='function'?copy(w.qaState()):null","qa:null,qaReadOmitted:'Use untouched original calendarView; no additional child QA/runtime getter'"],
  ["qa:typeof window.qaState==='function'?safe(()=>copy(window.qaState())):null","qa:null"],
  ["model:typeof window.model==='function'?safe(()=>copy(window.model())):null","model:null"]
 ])script=once(script,anchor,replacement,'calendar diagnostic snapshot observation boundary');
 return script;
}
async function finishOwnedCase(api,row,session,dir,started,withControl){
 row.primaryOutcome={status:row.status,error:row.error??null,stage:row.stage};
 if(session){
  try{row.finalSnapshot=await session.eval(snapshotScript(api,row),true);row.smoke=row.finalSnapshot.smoke;api.write(path.join(dir,'smoke.json'),row.smoke);}catch(e){row.finalCaptureError=String(e);api.write(path.join(dir,'smoke.json'),row.smoke??null);classifyError(api,row,observationError('Final snapshot unavailable: '+String(e)));}
  if(withControl)try{row.finalControl=await session.eval('return window.__r0017Control??null;',true);}catch(e){row.finalControlCaptureError=String(e);classifyError(api,row,observationError('Final control snapshot unavailable: '+String(e)));}
  if(!row.screenshots.some(x=>x.sha256))row.screenshots.push(await api.screenshot(session,path.join(dir,'error.png')));
  try{const cleanup=await session.close();if(!row.cleanup&&cleanup)row.cleanup=cleanup;}catch(e){row.cleanup={verifiedExited:false,scopeKnown:false,ok:false,status:'CLEANUP_THREW',error:String(e.stack||e)};}
 }else{
  api.write(path.join(dir,'smoke.json'),null);
  // startSession records cleanup itself if it acquired a process before throwing.
  if(!row.cleanup&&!row.driverPid){row.cleanup={verifiedExited:null,processExitRequired:false,scopeKnown:true,ok:true,status:'NO_PROCESS_STARTED'};if(row.profileRoot){try{fs.rmSync(row.profileRoot,{recursive:true,force:true});row.cleanup.profileCleanup={status:'REMOVED',absent:!fs.existsSync(row.profileRoot)};row.cleanup.ok=row.cleanup.profileCleanup.absent;}catch(e){row.cleanup.ok=false;row.cleanup.error=String(e);}}}
 }
 const c=row.cleanup;
 const noProcessWitness=!session&&!row.driverPid&&!row.browserPid&&c?.verifiedExited===null&&(c.processExitRequired===false||c.noProcessStarted===true)&&c.scopeKnown===true&&c.ok===true&&
  (!c.ownedProcesses||c.ownedProcesses.length===0)&&(!c.remaining||c.remaining.length===0)&&(!c.unresolvedObserved||c.unresolvedObserved.length===0)&&
  (!c.queries||c.queries.every(q=>Array.isArray(q.observed)&&q.observed.length===0))&&(!(row.profileRoot||c.profileRoot)||c.profileCleanup?.absent===true);
 const exitEstablished=session?c?.verifiedExited===true:(noProcessWitness||c?.verifiedExited===true);
 if(noProcessWitness)row.cleanupEvidenceKind='NO_PROCESS_ACQUIRED_NO_EXIT_PROOF';

 if(row.cleanup?.ok!==true||!exitEstablished||row.cleanup.scopeKnown!==true){api.result.stopLaunches={kind:'cleanup-unverified',case:row.name,receipt:row.name+'/result.json',reason:'No further native launch after uncertain owned process/profile cleanup'};row.status='CLEANUP_FAILED';}
 else row.checks.ownedCleanupSafetyEstablished=true;
 // Finalize against the last owned callback, not the earlier common-check cut.
 if(session?.bidi)session.bidi.boundary('case-final-cut');
 if(row.bidiTrace){
  row.checks.networkInterceptionsClean=Array.isArray(row.network?.interceptErrors)&&row.network.interceptErrors.length===0;
  row.checks.noUnexpectedNetwork=Array.isArray(row.network?.blockedURLs)&&row.network.blockedURLs.every(u=>/^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(u)||u==='https://theislampill.github.io/favicon.ico');
  row.checks.protocolFinalizationComplete=row.protocolFinalization?.ok===true;
  row.checks.bidiTraceIntact=Array.isArray(row.bidiTrace.writeErrors)&&row.bidiTrace.writeErrors.length===0;
  if(!row.checks.protocolFinalizationComplete&&row.status!=='CLEANUP_FAILED')row.status='PROTOCOL_FINALIZATION_FAILED';
  if(!row.checks.bidiTraceIntact&&row.status!=='CLEANUP_FAILED')row.status='COLLECTOR_TRACE_ERROR';
  if(!Object.values(row.checks).every(x=>x===true)){
   if(row.status==='CONTROL_ORACLES_PASSED_NOT_CLOSURE')row.status='CONTROL_ORACLE_FAILURE';
   else if(row.status==='PUBLIC_HEALTHY_PASSED_NOT_CLOSURE')row.status='PUBLIC_HEALTHY_FAILURE';
   else if(row.status.startsWith('DIAGNOSTIC_CAPTURED_'))row.status='DIAGNOSTIC_CAPTURE_OR_ACCOUNTING_FAILURE';
  }
 }
 row.finishedUtc=new Date().toISOString();row.elapsedMs=Date.now()-started;
 // Keep late callbacks on their mutable owner; result and summary use one cut.
 const frozen=JSON.parse(JSON.stringify(row));const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};freeze(frozen);
 const index=api.result.cases.indexOf(row);if(index<0)throw Error('Final case is not registered');api.result.cases[index]=frozen;
 api.write(path.join(dir,'result.json'),frozen);api.write(path.join(api.OUT,'summary.json'),api.result);
}
function plannedRows(groups){
 const perEngine=[];
 if(groups.includes('current')){
  for(const mode of ['native-reduce','ignore-reduction','ignore-full-override','assertion-throw','timeout-exception','actual-callback-timeout'])perEngine.push({id:'motion-'+mode,kind:'motion',mode,group:'current',storage:'valid',preference:'reduce'});
  for(const mode of ['body-pending','malformed-json','wrong-response-day','missing-timings','bypass-json','source-anchor','source-digest'])perEngine.push({id:'transport-'+mode,kind:'transport',mode,group:'current',storage:'valid',preference:'reduce'});
  for(const mode of ['matching-tomorrow','duplicate-current-day-tomorrow'])perEngine.push({id:mode,kind:'tomorrow',mode,group:'current',storage:'valid',preference:'reduce'});
 }
 for(const [group,kind] of [['optional-recorder','recorder'],['optional-config-storage','config-storage']])if(groups.includes(group))for(const storage of ['valid','malformed','absent'])for(const outcome of ['success','failure','exception','timeout'])perEngine.push({id:kind+'-'+storage+'-'+outcome,kind,group,outcome,storage,preference:'reduce'});
 const rows=[];
 for(const d of CALENDAR_DIAGNOSTICS)if(groups.includes(d.group))for(const engine of d.engines)rows.push({...d,engine,name:engine+'-'+d.id,kind:'calendar-diagnostic',storage:'valid',preference:'no-preference',schema:'r0017-native-controls/v3'});
 rows.push(...['chromium','firefox'].flatMap(engine=>perEngine.map(p=>({...p,engine,name:engine+'-'+p.id,schema:'r0017-native-controls/v3'}))));
 if(groups.includes('public'))for(const engine of ['chromium','firefox'])for(const preference of ['no-preference','reduce'])rows.push({name:engine+'-public-healthy-'+preference,engine,preference,mode:'healthy',storage:'absent',group:'public',schema:'r0017-public-native-proof/v3'});
 return Object.freeze(rows.map(p=>Object.freeze(p)));
}
function selectPopulation(groups,cases){
 const available=plannedRows(groups);
 if(cases===undefined)return {planned:available,requestedCaseNames:null,notSelected:[]};
 if(typeof cases!=='string')throw Error('Explicit --cases must be a comma-separated list of exact case names');
 const requested=cases.split(',');
 if(requested.some(n=>!n||n!==n.trim())||new Set(requested).size!==requested.length||requested.some(n=>!available.some(p=>p.name===n)))throw Error('Explicit --cases must name unique cases within the selected groups, with no empty or unknown entries');
 // Preserve canonical execution order. Omitted cases are explicitly unselected,
 // never fabricated NOT_ATTEMPTED results or implicit qualification credit.
 const selected=new Set(requested);
 return {planned:Object.freeze(available.filter(p=>selected.has(p.name))),requestedCaseNames:requested,notSelected:available.filter(p=>!selected.has(p.name)).map(p=>p.name)};
}
async function collectProbe(api,srv,p,engine,declared){
 const name=engine+'-'+p.id,planned={name,engine,id:p.id,group:p.group,kind:p.kind,storage:p.storage,preference:p.preference,schema:'r0017-native-controls/v3'};
 const block=api.launchBlock(planned);if(block){api.notAttempted(planned,block.reason,block);return false;}
 const dir=path.join(api.OUT,name);if(fs.existsSync(dir))throw Error('Case output already exists: '+name);fs.mkdirSync(dir);
 const row={schema:'r0017-native-controls/v3',qualification:'PARTIAL',name,kind:p.kind,group:p.group,mode:p.mode??null,engine,history:p.history,startedUtc:new Date().toISOString(),status:'STARTED',payloadCommit:api.EXPECTED,expectedIndexSha256:p.expectedIndexSha256,expectedWrapperSha256:p.expectedWrapperSha256,mutations:p.mutations,checks:{},screenshots:[]};
 api.result.cases.push(row);api.write(path.join(dir,'result.json'),row);api.write(path.join(api.OUT,'summary.json'),api.result);srv.set(p);
 let session;const seed=api.seeds(p.storage),started=Date.now();row.stage='setup';row.executionStarted=false;
 try{
  session=await api.startSession(engine,p.preference,p.viewport,p.dpr,row,dir,srv.origin);
  if(typeof session.navigate!=='function'||typeof session.eval!=='function')throw observationError('Corrected page-realm/navigation interface is missing');
  const preload=nativePreload(api,seed,srv.origin);fs.writeFileSync(path.join(dir,'preload.js'),preload+'\n');row.preloadSha256=api.sha(preload);await session.bidi.call('script.addPreloadScript',{functionDeclaration:preload});
  row.url=new URL('tests/smoke.html?fixture=healthy',srv.origin).href;requireObservationReserve(api);row.stage='navigation';row.executionStarted=true;
  const navigationStarted=performance.now(),deadline=navigationStarted+120000,trace=timingTrace(api,row,dir);
  row.navigation=await session.navigate(row.url);row.stage='instrument-initialization';
  const initialization=await waitFor(session,HELPER_INITIALIZATION,navigationStarted+8000,v=>v?.ready===true,trace);row.heldInitialization=initialization;
  if(!initialization.matched||!initializedPageHelpers(initialization.value,declared))throw observationError('Held page lexical helpers/declaration/initial counters were not established in the actual page realm within 8000 ms');
  row.checks.actualPageHelpersAdmitted=true;row.stage='observation';const captureScript=snapshotScript(api,row);row.snapshotScriptSha256=api.sha(captureScript);row.snapshotPolicy=p.kind==='calendar-diagnostic'?'No extra child/top QA or model evaluation; original calendarView remains the runtime evidence':'Inherited actual snapshot';
  const setView=p.kind==='calendar-diagnostic'?'':"fr.setAttribute('style','position:fixed;left:20px;top:60px;width:325px;height:530px;border:0');";
  const script=`window.__r0017Control={schema:'r0017-controlled-native/v3',id:${JSON.stringify(p.id)},done:false,data:null,error:null,errorKind:null};${setView}
(async()=>{try{return await (async()=>{${p.script}\n})();}finally{finalize();}})().then(data=>{window.__r0017Control.data=data;window.__r0017Control.done=true;},error=>{window.__r0017Control.error=String(error&&error.stack||error);window.__r0017Control.errorKind=error&&error.code||null;window.__r0017Control.done=true;});return true;`;
  fs.writeFileSync(path.join(dir,'control.js'),script+'\n');row.controlSha256=api.sha(script);
  if(await sampleBeforeDeadline(session,script,deadline,'control-launch',trace)!==true)throw observationError('Actual page did not acknowledge its finite control');
  let last='',terminal=null;const captured=new Set();
  while(performance.now()<deadline){
   const value=await sampleBeforeDeadline(session,`return {done:window.__r0017Control?.done===true,state:(()=>{${api.PROGRESS}})(),control:window.__r0017Control?.done?window.__r0017Control:null,snapshot:window.__r0017Control?.done?(()=>{${captureScript}})():null};`,deadline,'control-progress',trace);
   if(!value||typeof value.done!=='boolean'||!value.state)throw observationError('Invalid actual page control/progress observation');
   const encoded=JSON.stringify(value.state);if(encoded!==last){api.record(path.join(dir,'progress.jsonl'),{elapsedMs:Date.now()-started,done:value.done,...value.state});last=encoded;}
   if(value.done){terminal=value;break;}
   const f=value.state.child;
   if(p.kind==='calendar-diagnostic'&&f?.visible&&f.width===325&&f.height===530&&f.photoBytes>50&&!captured.has(f.attempt)){
    captured.add(f.attempt);const shot=await api.screenshot(session,path.join(dir,'stage-'+f.attempt+'.png'));row.screenshots.push({...shot,evidence:f});if(shot.error)throw observationError('Diagnostic stage screenshot unavailable: '+shot.error);
   }
   const remaining=deadline-performance.now();if(remaining>0)await delay(Math.min(150,remaining));
  }
  if(!terminal)throw observationError('Finite control was not observed terminal within the unchanged 120000 ms outer collector bound');
  row.terminalObservationWithin120000ms=true;row.control=terminal.control;row.snapshot=terminal.snapshot;row.smoke=row.snapshot?.smoke;api.write(path.join(dir,'smoke.json'),row.smoke??null);
  if(!row.snapshot||!row.control)throw observationError('Terminal observation lacks actual control or snapshot');
  if(row.control.error&&row.control.errorKind!=='R0017_NATIVE_PRECONDITION')throw observationError('Generated control observation failed: '+row.control.error);
  if(row.control.data?.observations?.some(o=>o.captureError))throw observationError('Motion finally observation failed: '+row.control.data.observations.filter(o=>o.captureError).map(o=>o.captureError).join('\n'));
  api.checkCommon(row,row.snapshot,p.viewport,p.dpr,seed);row.checks.originalDenominator=exactDenominator(row.smoke,declared);row.checks.terminalWithinDeclaredBound=row.terminalObservationWithin120000ms===true;
  if(p.kind==='calendar-diagnostic')diagnosticOracle(p,row.control,row,declared);else oracle(p,row.control,row,declared);
  row.screenshots.push(await api.screenshot(session,path.join(dir,'viewport.png')));if(row.snapshot.children?.visible)row.screenshots.push(await api.screenshot(session,path.join(dir,'fixture.png'),'#w'));
  if(row.screenshots.some(x=>x.error))throw observationError('A declared screenshot observation failed: '+row.screenshots.filter(x=>x.error).map(x=>x.error).join('\n'));
  row.checks.recordedScreenshot=row.screenshots.some(x=>x.sha256);
  if(p.kind==='calendar-diagnostic')row.status=allTrue(row.checks)?'DIAGNOSTIC_CAPTURED_'+row.diagnosticTargetState.toUpperCase():'DIAGNOSTIC_CAPTURE_OR_ACCOUNTING_FAILURE';
  else row.status=allTrue(row.checks)?'CONTROL_ORACLES_PASSED_NOT_CLOSURE':'CONTROL_ORACLE_FAILURE';
 }catch(e){classifyError(api,row,e);}
 finally{await finishOwnedCase(api,row,session,dir,started,true);}
 return row.status==='CONTROL_ORACLES_PASSED_NOT_CLOSURE'||row.status==='DIAGNOSTIC_CAPTURED_EXECUTED';
}

async function publicNativeNoPreferenceBaseline(api,session,row,dir,viewport,dpr,seed){
 const run=api.runId+'-'+row.engine+'-public-native-no-preference',hash=HASH+'&tz=Asia/Riyadh&qa=1';
 const url=new URL('tests/widget-fixture.html?mode=healthy&run='+encodeURIComponent(run)+'&attempt=1#'+hash,api.PUBLIC).href;
 const baseline=row.nativeNoPreferenceBaseline={schema:'r0017-public-native-motion-baseline/v1',engine:row.engine,processId:row.browserPid,capabilities:row.capabilities,preference:row.preference,
  scope:'Actual public direct wrapper before the separate full smoke; no matchMedia override or product mutation',url,expectedRun:run,expectedAttempt:1,expectedHash:hash,expectedSourceSha256:api.source.files['index.html'].sha256,
  sourceProvenance:'Actual wrapper-computed index hash + separate pinned public response readback',pulseEnvelope:PULSE_RANGE,checks:{}};
 const began=performance.now(),deadline=began+8000,trace=timingTrace(api,row,dir);baseline.navigation=await session.navigate(url);baseline.navigationElapsedMs=performance.now()-began;if(performance.now()>=deadline)throw observationError('Public native baseline navigation exceeded its 8000 ms observation bound before readiness sampling');
 const code=`const f=window.__widgetFixture,q=typeof window.qaState==='function'?window.qaState():null,o=window.__smokeWeather?.identity?.();
 const ready=!!f&&f.state==='ready'&&f.error===null&&f.storageIsolated===true&&f.clockFixed===true&&f.fetchIntercepted===true&&q?.cache?.prayerLoaded===true&&!!q?.render?.currentKey&&!!q?.render?.nextKey&&!!o;
 return {ready,data:ready?(${READ})(window):null,snapshot:ready?(()=>{${api.SNAPSHOT}})():null};`;
 const observed=await waitFor(session,code,deadline,v=>v?.ready===true,trace);baseline.observedWithin8000ms=observed.matched;baseline.data=observed.value?.data??null;baseline.snapshot=observed.value?.snapshot??null;
 const x=baseline.data,c=baseline.checks;
 c.actualWithinOriginalBound=observed.matched;c.currentNativeOwner=exactOwner(x,baseline.expectedSourceSha256)&&x.fixture.run===run&&x.fixture.attempt===1&&x.fixture.mode==='healthy'&&x.hash===hash&&x.url===url&&x.fixture.scriptProfile==='split-moon';
 c.nativeFunctionUntouched=x?.originalMatchMediaRestored===true;c.nativeNoPreference=x?.nativeReduced===false;c.noFullOverride=x?.motionFull===false&&!new URLSearchParams(hash).has('motion');
 c.actualNoonConsumer=pulseConsumer(x)&&x.pulse!==1&&x.qa.cache.prayerDate==='07-09-2026'&&x.qa.render.currentKey==='Dhuhr'&&x.qa.render.nextKey==='Asr'&&x.qa.render.leftMin===180&&x.model.nextTime==='15:30';
 if(baseline.snapshot){const b={...row,checks:{}};api.checkCommon(b,baseline.snapshot,viewport,dpr,seed);baseline.commonChecks=b.checks;c.nativePlatformAndStorage=allTrue(b.checks);}
 else c.nativePlatformAndStorage=false;
 baseline.observedMonotonicMs=row.lastObservationTiming?.observedMonotonicMs??null;baseline.assessedMonotonicMs=performance.now();baseline.status=allTrue(c)?'NATIVE_NO_PREFERENCE_CONSUMER_OBSERVED':'NATIVE_NO_PREFERENCE_BASELINE_FAILURE';
 api.write(path.join(dir,'native-no-preference-baseline.json'),baseline);
 row.screenshots.push({...await api.screenshot(session,path.join(dir,'native-no-preference-baseline.png')),stage:'native-no-preference-baseline'});
 if(row.screenshots.at(-1).error)throw observationError('Public native baseline screenshot unavailable: '+row.screenshots.at(-1).error);
 return allTrue(c);
}
async function collectPublic(api,engine,preference,declared){
 const name=engine+'-public-healthy-'+preference,planned={name,engine,group:'public',mode:'healthy',preference,storage:'absent',schema:'r0017-public-native-proof/v3'};
 const block=api.launchBlock(planned);if(block){api.notAttempted(planned,block.reason,block);return false;}
 const dir=path.join(api.OUT,name);if(fs.existsSync(dir))throw Error('Public output already exists: '+name);fs.mkdirSync(dir);
 const row={schema:'r0017-public-native-proof/v3',qualification:'PARTIAL',name,engine,preferenceRequested:preference,startedUtc:new Date().toISOString(),status:'STARTED',payloadCommit:api.EXPECTED,
 scope:'Actual public responses; no fulfillment or public seed writes; unchanged 30/141 smoke. No-preference rows add one declared direct-wrapper native baseline before this smoke.',
 plannedTopLevelDocuments:preference==='no-preference'?2:1,checks:{},screenshots:[]};
 api.result.cases.push(row);api.write(path.join(dir,'result.json'),row);api.write(path.join(api.OUT,'summary.json'),api.result);
 const viewport={width:1100,height:900},dpr=1,seed=Object.fromEntries(Object.keys(api.seeds('absent')).map(k=>[k,null]));let session;const started=Date.now();row.stage='setup';row.executionStarted=false;
 try{
  session=await api.startSession(engine,preference,viewport,dpr,row,dir,api.PUBLIC);
  if(typeof session.navigate!=='function'||typeof session.eval!=='function')throw observationError('Corrected page-realm/navigation interface is missing');
  const preload=nativePreload(api,seed,api.PUBLIC);fs.writeFileSync(path.join(dir,'preload.js'),preload+'\n');row.preloadSha256=api.sha(preload);await session.bidi.call('script.addPreloadScript',{functionDeclaration:preload});
  requireObservationReserve(api);row.executionStarted=true;
  if(preference==='no-preference'){row.stage='native-no-preference-baseline';row.checks.actualNativeNoPreferenceConsumer=await publicNativeNoPreferenceBaseline(api,session,row,dir,viewport,dpr,seed);}
  row.url=new URL('tests/smoke.html?fixture=healthy',api.PUBLIC).href;requireObservationReserve(api);row.stage='navigation';
  const navigationStarted=performance.now(),deadline=navigationStarted+120000,trace=timingTrace(api,row,dir);row.navigation=await session.navigate(row.url);row.stage='observation';
  const captured=new Set();let terminal=null,last='';
  while(performance.now()<deadline){
   const value=await sampleBeforeDeadline(session,`return {progress:(()=>{${api.PROGRESS}})(),snapshot:window.__smoke?(()=>{${api.SNAPSHOT}})():null};`,deadline,'public-progress',trace),progress=value?.progress;
   if(!progress||typeof progress.done!=='boolean')throw observationError('Invalid public page progress observation');
   const encoded=JSON.stringify(progress);if(encoded!==last){api.record(path.join(dir,'progress.jsonl'),{elapsedMs:Date.now()-started,...progress});last=encoded;}
   if(progress.done){if(!value.snapshot)throw observationError('Public terminal sample lacks its same-evaluation snapshot');terminal=value;break;}
   const f=progress.child;if(f?.visible&&f.width===325&&f.height===530&&f.photoBytes>50&&!captured.has(f.attempt)){
    captured.add(f.attempt);const shot=await api.screenshot(session,path.join(dir,'stage-'+String(f.attempt).padStart(2,'0')+'.png'));row.screenshots.push({...shot,evidence:f,elapsedMs:Date.now()-started});if(shot.error)throw observationError('Public stage screenshot unavailable: '+shot.error);
   }
   const remaining=deadline-performance.now();if(remaining>0)await delay(Math.min(150,remaining));
  }
  if(!terminal)throw observationError('Public smoke was not observed terminal within 120000 ms measured from navigation start');
  row.snapshot=terminal.snapshot;row.smoke=row.snapshot.smoke;api.write(path.join(dir,'smoke.json'),row.smoke);const s=row.smoke,r=s?.required,attempts=s?.fixture?.attempts;
  api.checkCommon(row,row.snapshot,viewport,dpr,seed);row.checks.terminalWithin120000ms=true;row.checks.originalDenominator=exactDenominator(s,declared);
  row.checks.fullOriginalHealthy=s?.status==='PASS'&&r?.total===30&&r.executed===30&&r.failed===0&&Array.isArray(r.missing)&&r.missing.length===0&&s.pass===141&&s.fail===0&&s.skip===0&&r.cases.every(x=>x.state==='executed'&&x.assertions===x.expected&&x.reason===null);
  const lines=assertionRows(row.snapshot.assertionLog);row.checks.exactHealthyLog=!!lines&&lines.pass.length===141&&lines.fail.length===0&&lines.skip.length===0;
  row.checks.freshOwnedActualSources=Array.isArray(attempts)&&attempts.length>0&&new Set(attempts.map(a=>a.fixture?.documentId)).size===attempts.length&&attempts.every((a,i)=>a.attempt===i+1&&a.mode==='healthy'&&a.result==='ready'&&a.reason===null&&a.fixture?.run===s.fixture.run&&a.fixture.attempt===a.attempt&&a.fixture.hash===a.hash&&a.fixture.mode==='healthy'&&a.documentId===a.fixture.documentId&&a.sourceSha256===api.source.files['index.html'].sha256&&/^[a-f0-9-]{36}$/.test(a.fixture.documentId||'')&&a.fixture.sourceSha256===api.source.files['index.html'].sha256&&bodyReady(a.fixture));
  row.checks.childPreference=row.snapshot.children?.preference===(preference==='reduce');row.screenshots.push(await api.screenshot(session,path.join(dir,'viewport.png')));
  if(row.screenshots.some(x=>x.error))throw observationError('A declared public screenshot failed');row.checks.recordedScreenshot=row.screenshots.some(x=>x.sha256);
  row.status=allTrue(row.checks)?'PUBLIC_HEALTHY_PASSED_NOT_CLOSURE':'PUBLIC_HEALTHY_FAILURE';
 }catch(e){classifyError(api,row,e);}
 finally{await finishOwnedCase(api,row,session,dir,started,false);}
 return row.status==='PUBLIC_HEALTHY_PASSED_NOT_CLOSURE';
}

async function observedPublicReadback(api){
 const paths=new Set(),unmapped=[];
 for(const row of api.result.cases.filter(x=>x.schema==='r0017-public-native-proof/v3')){
  const file=path.join(api.OUT,row.name,'network.jsonl');if(!fs.existsSync(file))continue;
  for(const line of fs.readFileSync(file,'utf8').split('\n').filter(Boolean)){const event=JSON.parse(line),raw=event.request?.url;if(typeof raw!=='string'||!raw.startsWith(api.PUBLIC))continue;const u=new URL(raw),prefix=new URL(api.PUBLIC).pathname;let relative=decodeURIComponent(u.pathname.slice(prefix.length))||'index.html';if(relative.endsWith('/'))relative+='index.html';if(api.source.files[relative])paths.add(relative);else unmapped.push({case:row.name,url:raw,status:event.response?.status??null});}
 }
 const plannedPaths=[...paths].sort(),rows=[];
 for(const file of plannedPaths){
  const url=new URL(file,api.PUBLIC).href,fetchStartedUtc=new Date().toISOString(),expected={commit:api.EXPECTED,path:file,sha256:api.source.files[file].sha256};
  try{const r=await fetch(url,{redirect:'error',signal:AbortSignal.timeout(api.operationTimeout(20000))}),b=Buffer.from(await r.arrayBuffer());rows.push({file,url,fetchStartedUtc,fetchFinishedUtc:new Date().toISOString(),status:r.status,bytes:b.length,sha256:api.sha(b),expected,matches:r.ok&&api.sha(b)===expected.sha256});}
  catch(e){rows.push({file,url,fetchStartedUtc,fetchFinishedUtc:new Date().toISOString(),expected,matches:false,error:String(e)});if(e.code==='R0017_BUDGET_EXHAUSTED'){api.result.stopLaunches={kind:'orchestration-budget',reason:String(e),receipt:'public-observed-dependencies.json'};break;}}
  api.write(path.join(api.OUT,'public-observed-dependencies.json'),{scope:'Readback of same-origin paths actually requested by these public contexts; not every delivered route',plannedPaths,unmapped,rows});
 }
 const unreadPaths=plannedPaths.filter(file=>!rows.some(r=>r.file===file)),receipt={scope:'Observed consumer dependencies only; broader final delivery map remains a review gate',plannedPaths,unreadPaths,unmapped,rows,passed:rows.length>0&&unreadPaths.length===0&&unmapped.length===0&&rows.every(r=>r.matches)};
 api.write(path.join(api.OUT,'public-observed-dependencies.json'),receipt);return receipt;
}
async function run(api,options={}){
 const groups=(options.groups||'current,public,calendar-diagnostics').split(',').filter(Boolean),allowed=['current','public','calendar-diagnostics','waning-diagnostic','optional-recorder','optional-config-storage'];
 if(!groups.length||new Set(groups).size!==groups.length||groups.some(x=>!allowed.includes(x)))throw Error('Use a unique explicit selection from '+allowed.join(','));
 const population=selectPopulation(groups,options.cases),planned=population.planned,publicRows=planned.filter(p=>p.group==='public');
 const baselineDocuments=publicRows.filter(p=>p.preference==='no-preference').length,calendarDocuments=planned.filter(p=>p.kind==='calendar-diagnostic').length;
 api.result.schema='r0017-windows-phase2/v2';api.result.qualification='PARTIAL';api.result.status='STARTED';api.result.scope='Explicit finite second-phase population; only plannedCases are commissioned in this execution. Narrow controls, public consumers and original calendar diagnostics retain their own evidence limits; no unselected-case credit';api.result.groups=groups;api.result.selection={requestedCaseNames:population.requestedCaseNames,notSelected:population.notSelected};api.result.history=HISTORY;api.result.plannedCases=planned;api.result.plannedCount=planned.length;
 api.result.documentPlan={nativeSessions:planned.length,topLevelNavigations:planned.length+baselineDocuments,additionalPublicBaselineDocuments:baselineDocuments,calendarPrerequisiteDocuments:calendarDocuments,calendarTargetDocuments:calendarDocuments,ordering:'Selected calendar diagnostics by declared engine first, then selected current/optional groups by engine, then selected public contexts; no retries',scope:'Counts describe only selected planned stages, not actual execution; public full-smoke fixture attempts are recorded from the original instrument'};
 api.result.pending=['Retain first native run 42388898271 and corrected base run 42390915224 as separate actual outcomes; no assumed PASS','Assess the two original Firefox calendar diagnostics without assigning a cause to the older Linux result','Independent admission of historical pure subproof transfer from exact raw receipts and dependency lineage','Reconcile all first-phase outcomes and every retained failure; no rerun-until-green credit','Complete final served-source/documentation/currentness map and independent pixel/contract review','Original eight exceptions/four TODOs and all limitations individually retained','Root-owned evidence publication and conditional closure; this collector has no such authority'];
 api.write(path.join(api.OUT,'summary.json'),api.result);let server;let ok=true;
 try{
  for(const name of ['remainingBudgetMs','operationTimeout','launchBlock','notAttempted'])if(typeof api[name]!=='function')throw Error('Revised owned-cleanup/budget interface missing: '+name);
  if(process.platform!=='win32'||typeof WebSocket!=='function')throw Error('Native Windows with built-in WebSocket is required');api.identify();
  const catalog=prepare(api),selected=catalog.plans.map(p=>({...p,engines:p.engines.filter(engine=>planned.some(row=>row.name===engine+'-'+p.id))})).filter(p=>p.engines.length);
  if(planned.filter(p=>p.group!=='public').length!==selected.reduce((n,p)=>n+p.engines.length,0))throw Error('Immutable phase-2 plan cardinality mismatch');
  api.result.plan=selected.map(p=>({id:p.id,kind:p.kind,group:p.group,engines:p.engines,history:p.history,mode:p.mode??null,diagnosticSource:p.diagnosticSource??null,diagnosticLimitations:p.diagnosticLimitations??null,storage:p.storage,preference:p.preference,viewport:p.viewport,dpr:p.dpr,expectedIndexSha256:p.expectedIndexSha256,expectedWrapperSha256:p.expectedWrapperSha256,scriptSha256:api.sha(p.script),mutations:p.mutations,offlineAdmission:p.offlineAdmission}));
  api.write(path.join(api.OUT,'phase2-plan.json'),{history:HISTORY,heldSmokeSha256:catalog.heldSha256,sourceSpans:catalog.sourceSpans,groups,selection:api.result.selection,plans:api.result.plan,publicContexts:publicRows});
  for(const p of selected){const folder=path.join(api.OUT,'variants',p.id);fs.mkdirSync(folder,{recursive:true});for(const [rel,bytes]of Object.entries(p.overrides)){const file=path.join(folder,rel);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,bytes);}}
  if(selected.length){server=await variantServer(api);
   // Capture selected original calendar diagnostics with each plan's declared engine; no retries.
   for(const p of selected.filter(p=>p.kind==='calendar-diagnostic'))for(const engine of p.engines)if(!await collectProbe(api,server,p,engine,catalog.declared))ok=false;
   for(const engine of ['chromium','firefox'])for(const p of selected.filter(p=>p.kind!=='calendar-diagnostic'&&p.engines.includes(engine)))if(!await collectProbe(api,server,p,engine,catalog.declared))ok=false;
  }
  if(publicRows.length){
   let publicBound=!api.result.stopLaunches;
   if(publicBound)try{api.result.publicReadback=await api.publicReadback();}catch(e){publicBound=false;ok=false;api.result.publicReadbackError=String(e.stack||e);if(e.code==='R0017_BUDGET_EXHAUSTED')api.result.stopLaunches={kind:'orchestration-budget',reason:String(e),receipt:'summary.json#publicReadbackError'};}
   if(publicBound){for(const p of publicRows)if(!await collectPublic(api,p.engine,p.preference,catalog.declared))ok=false;
    if(!api.result.stopLaunches){api.result.publicObservedReadback=await observedPublicReadback(api);if(!api.result.publicObservedReadback.passed)ok=false;}else{ok=false;api.result.publicObservedReadback={status:'NOT_ATTEMPTED',reference:api.result.stopLaunches};}
   }else{ok=false;api.result.publicContextsNotRun={reason:api.result.stopLaunches?.reason||'Public source identity not established',reference:api.result.stopLaunches||api.result.publicReadbackError,planned:planned.filter(p=>p.group==='public').map(p=>p.name)};for(const p of planned.filter(p=>p.group==='public'))api.notAttempted(p,api.result.publicContextsNotRun.reason,api.result.publicContextsNotRun.reference);}
  }
  api.result.status=api.result.stopLaunches?.kind==='cleanup-unverified'?'PHASE2_CLEANUP_FAILED':ok?'PHASE2_ORACLES_PASSED_NOT_CLOSURE':'PHASE2_HAS_FAILURES';process.exitCode=ok?0:1;
 }catch(e){api.result.status='PHASE2_CAPABILITY_OR_SETUP_FAILED';api.result.error=String(e.stack||e);api.result.stopLaunches=api.result.stopLaunches||{kind:'phase-setup',reason:api.result.error,receipt:'summary.json#error'};process.exitCode=1;}
 finally{
  if(server)await server.close();
  for(const p of planned)if(!api.result.cases.some(r=>r.name===p.name))api.notAttempted(p,api.result.stopLaunches?.reason||'Phase ended before this planned row',api.result.stopLaunches||'summary.json');
  api.result.attemptedCount=api.result.cases.filter(r=>r.status!=='NOT_ATTEMPTED').length;api.result.notAttemptedCount=api.result.cases.filter(r=>r.status==='NOT_ATTEMPTED').length;
  api.result.finishedUtc=new Date().toISOString();api.write(path.join(api.OUT,'summary.json'),api.result);
 }
 return api.result;
}
module.exports={prepare,run,HISTORY,plannedRows,review:{expectedNarrow,exactNarrowAccounting,attemptPopulation,oracle,diagnosticOracle,pulseConsumer,observedWithin,sampleBeforeDeadline,initializedPageHelpers,snapshotScript,finishOwnedCase,classifyError,publicNativeNoPreferenceBaseline,calendarDiagnosticRecipe,PULSE_RANGE}};
