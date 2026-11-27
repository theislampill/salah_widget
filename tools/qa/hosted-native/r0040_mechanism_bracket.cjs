'use strict';
// Explicit reversible diagnostic seams. Original samples and stop stay separate.
const {createHash}=require('node:crypto');
const S=require('./r0040_passive_sampler.cjs');
const sha=value=>createHash('sha256').update(value).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const DRIVER_SHA256='19a766ccacf0ac784f46961a5cd0079390f10a34d14825ef5ac7b28adbd33e26';
const MAIN_SHA256='ec300b48e036c198b5ad0a8b7c2eb3081453552e19420dac5c319a5ab4ab95ec';
const MAIN_SEAM="bus.addEventListener('r0040-read',()=>{bus.textContent=JSON.stringify(window.__r0040Sample());});";
const CALLBACK="()=>{bus.textContent=JSON.stringify(window.__r0040Sample());}";
const ISOLATED_SEAM="const read=ts=>{if(!active)return;const passiveEntry=passiveSampler.enter();";
const READ_JOIN='globalThis.__R0040_MECHANISM_JOIN__?.snapshot()??null';
const LIMIT=4096,STOP_BYTES=8*1024*1024;

function originalExpressions(source){
  need(Buffer.isBuffer(source)&&sha(source)===DRIVER_SHA256,'original capture source digest differs');
  const text=source.toString('utf8'),start='    await page.evaluate(({utc,rectRecipe})=>{',end='    },{utc:utcMs,rectRecipe:L.RECTS});';
  need(text.split(start).length===2&&text.split(end).length===2,'unique original main listener expression required');
  const a=text.indexOf(start),b=text.indexOf(end,a),main=text.slice(a+start.indexOf('({utc'),b+5);
  need(sha(main)===MAIN_SHA256,'original main expression digest differs');
  const matches=[...text.matchAll(/await isolated\(`([\s\S]*?)`\);/g)];
  need(matches.length===1,'one original isolated expression required');
  S.instrumentStart(matches[0][1]);
  return {main,isolated:matches[0][1]};
}

// This callable is serialized inside the original main-world installation.
// It wraps that exact listener body, not __r0040Sample or the direct geometry read.
function installMainBracket(original){
  if(Object.hasOwn(globalThis,'__R0040_MECHANISM_MAIN__')||typeof original!=='function')throw Error('fresh main bracket required');
  const nativePerformance=performance,nativeNow=performance.now,nativeDate=Date,nativeDateNow=Date.now;
  const witness=globalThis.__R0040_DATE_ONLY__;
  const state={protocol:'r0040-mechanism-main-bracket/1',clockDomain:'main-performance',timeOriginMs:performance.timeOrigin,
    anchor:{protocol:witness?.protocol,utcMs:witness?.utcMs,anchorPerformanceMs:witness?.anchorPerformanceMs,timeOriginMs:witness?.timeOriginMs},
    limit:4096,calls:0,rows:[],dropped:0,faults:0,clockPreserved:true,datePreserved:true};
  const identities=()=>{
    state.clockPreserved&&=performance===nativePerformance&&performance.now===nativeNow&&performance.timeOrigin===state.timeOriginMs;
    state.datePreserved&&=Date===nativeDate&&Date.now===nativeDateNow&&globalThis.__R0040_DATE_ONLY__===witness;
  };
  const clock=()=>{try{identities();const value=nativeNow.call(nativePerformance);
    if(!Number.isFinite(value)||value<0)throw Error('nonfinite main clock');return value;
  }catch(_){state.faults++;return null;}};
  const snapshot=()=>{try{identities();}catch(_){state.faults++;}
    return {...state,anchor:{...state.anchor},rows:state.rows.map(row=>[...row])};};
  Object.defineProperty(globalThis,'__R0040_MECHANISM_MAIN__',{value:Object.freeze({snapshot}),writable:false,configurable:false});
  return function(...args){
    const ordinal=state.calls++;let stamp=null,outcome='returned';
    try{stamp=args[0]?.timeStamp;if(typeof stamp!=='number'||!Number.isFinite(stamp)||stamp<0)throw Error('event stamp unavailable');}
    catch(_){stamp=null;state.faults++;}
    const before=clock();
    try{return Reflect.apply(original,this,args);}
    catch(error){outcome='threw';throw error;}
    finally{
      const after=clock();
      try{if(state.rows.length<state.limit)state.rows.push([ordinal,stamp,before,after,outcome]);else state.dropped++;}
      catch(_){state.faults++;}
    }
  };
}

function snapshotMain(){return globalThis.__R0040_MECHANISM_MAIN__?.snapshot()??null;}

// This listener runs in the same synchronous dispatch before original samples.push.
// The native event stamp is a strict join value, never a replacement clock.
function installIsolatedJoin(bus){
  if(Object.hasOwn(globalThis,'__R0040_MECHANISM_JOIN__'))throw Error('fresh isolated event join required');
  const state={protocol:'r0040-mechanism-event-join/1',clockDomain:'isolated-event-stamp',timeOriginMs:performance.timeOrigin,
    limit:4096,calls:0,rows:[],dropped:0,faults:0};
  Object.defineProperty(globalThis,'__R0040_MECHANISM_JOIN__',{value:Object.freeze({snapshot(){return {...state,rows:state.rows.map(row=>[...row])};}}),
    writable:false,configurable:false});
  bus.addEventListener('r0040-read',event=>{
    state.calls++;
    try{const ordinal=globalThis.samples.length,stamp=event.timeStamp;
      if(!Number.isSafeInteger(ordinal)||ordinal<0||typeof stamp!=='number'||!Number.isFinite(stamp)||stamp<0)throw Error('event ordinal unavailable');
      if(state.rows.length<state.limit)state.rows.push([ordinal,stamp]);else state.dropped++;
    }catch(_){state.faults++;}
  });
}

const mainReplacement=()=>"bus.addEventListener('r0040-read',("+installMainBracket.toString()+')('+CALLBACK+'));';
function reverseMain(expression){
  const added=mainReplacement();need(typeof expression==='string'&&expression.split(added).length===2,'unique main bracket reversal required');
  const original=expression.replace(added,()=>MAIN_SEAM);need(sha(original)===MAIN_SHA256,'main bracket reversal digest differs');return original;
}
function instrumentMain(expression){
  need(typeof expression==='string'&&sha(expression)===MAIN_SHA256&&expression.split(MAIN_SEAM).length===2,'original main listener source differs');
  const transformed=expression.replace(MAIN_SEAM,mainReplacement);need(reverseMain(transformed)===expression,'original main source not recovered');
  return {expression:transformed,identity:{protocol:'r0040-mechanism-main-transform/1',originalExpressionSha256:MAIN_SHA256,
    transformedExpressionSha256:sha(transformed),installerSha256:sha(installMainBracket.toString()),changedSeams:1,originalRecoveredExactly:true,limit:LIMIT}};
}
const isolatedReplacement=()=>'('+installIsolatedJoin.toString()+')(bus);\n        '+ISOLATED_SEAM;
function reverseIsolated(expression){
  const added=isolatedReplacement();need(typeof expression==='string'&&expression.split(added).length===2,'unique isolated join reversal required');
  const passive=expression.replace(added,()=>ISOLATED_SEAM),original=S.reverseStart(passive);
  need(S.instrumentStart(original).expression===passive,'passive expression recovery differs');return passive;
}
function instrumentIsolated(expression){
  const original=S.reverseStart(expression);
  need(S.instrumentStart(original).expression===expression&&expression.split(ISOLATED_SEAM).length===2,'reviewed passive source required');
  const transformed=expression.replace(ISOLATED_SEAM,isolatedReplacement);
  need(reverseIsolated(transformed)===expression,'passive source not recovered exactly');
  return {expression:transformed,identity:{protocol:'r0040-mechanism-isolated-transform/1',passiveExpressionSha256:sha(expression),
    transformedExpressionSha256:sha(transformed),installerSha256:sha(installIsolatedJoin.toString()),changedSeams:1,
    passiveRecoveredExactly:true,originalRecoveredExactly:true,limit:LIMIT}};
}

function sameWorldArithmetic(rows,anchorPerformanceMs,utcMs=0){
  need(Array.isArray(rows)&&rows.length>=2&&Number.isFinite(anchorPerformanceMs)&&Number.isSafeInteger(utcMs),'same-world clock arithmetic inputs required');
  for(const row of rows)need(Array.isArray(row)&&row.length===3&&row.every(Number.isFinite)&&
    Math.floor(utcMs+row[1]-anchorPerformanceMs)-utcMs===row[2],'same-world Date formula differs');
  const a=rows[0],b=rows.at(-1),lag=row=>row[1]-row[0],round=row=>row[2]-(row[1]-anchorPerformanceMs);
  return {protocol:'r0040-same-world-delay-arithmetic/1',dateVersusRafResidualMs:(b[2]-a[2])-(b[0]-a[0]),
    callbackLagChangeMs:lag(b)-lag(a),roundingResidualChangeMs:round(b)-round(a),
    interpretation:'Same declared clock only; no cross-world calibration or original-verifier substitution.'};
}

function inspectBrackets(main,join,passive,originalStopBytes,proof){
  const finite=x=>typeof x==='number'&&Number.isFinite(x),count=x=>Number.isSafeInteger(x)&&x>=0;
  need(Buffer.isBuffer(originalStopBytes)&&originalStopBytes.length>0&&originalStopBytes.length<=STOP_BYTES,'actual bounded original stop Buffer bytes required');
  const response=JSON.parse(originalStopBytes),samples=response?.result?.value;
  need(response&&!response.exceptionDetails&&Array.isArray(samples)&&samples.length>0&&samples.length<=LIMIT,'bounded complete original stop population required');
  S.inspectSampler(passive);
  need(main?.protocol==='r0040-mechanism-main-bracket/1'&&main.clockDomain==='main-performance'&&
    join?.protocol==='r0040-mechanism-event-join/1'&&join.clockDomain==='isolated-event-stamp','bracket clock domains differ');
  for(const raw of [main,join])need(raw.limit===LIMIT&&count(raw.calls)&&count(raw.dropped)&&count(raw.faults)&&
    raw.dropped===0&&raw.faults===0&&Array.isArray(raw.rows)&&raw.rows.length===samples.length&&raw.calls===samples.length,
    'bracket/join overflow fault or incomplete population');
  need(main.clockPreserved===true&&main.datePreserved===true,'main clock or Date identity changed');
  need(proof&&finite(proof.utcMs)&&Number.isSafeInteger(proof.utcMs)&&finite(proof.anchorPerformanceMs)&&finite(proof.timeOriginMs)&&
    main.timeOriginMs===proof.timeOriginMs&&main.anchor?.protocol==='r0040-date-only-installed/1'&&
    main.anchor.utcMs===proof.utcMs&&main.anchor.anchorPerformanceMs===proof.anchorPerformanceMs&&main.anchor.timeOriginMs===proof.timeOriginMs&&
    join.timeOriginMs===passive.timeOriginMs,'main or isolated clock anchor differs');
  need(passive.rows.length===samples.length,'complete passive ordinal population required');
  const stamps=new Set(),offsetIntervals=[];let lower=-Infinity,upper=Infinity;
  for(let ordinal=0;ordinal<samples.length;ordinal++){
    const m=main.rows[ordinal],j=join.rows[ordinal],p=passive.rows[ordinal],sample=samples[ordinal];
    need(Array.isArray(m)&&m.length===5&&m[0]===ordinal&&Array.isArray(j)&&j.length===2&&j[0]===ordinal&&p[0]===ordinal,
      'main/isolated ordinal join differs');
    need(finite(m[1])&&m[1]>=0&&j[1]===m[1]&&!stamps.has(m[1]),'unique matching native event stamp required');stamps.add(m[1]);
    need(finite(m[2])&&finite(m[3])&&m[2]>=0&&m[3]>=m[2]&&m[4]==='returned','finite completed main callback bracket required');
    need(sample&&finite(sample.at)&&sample.at===passive.timeOriginMs+p[1]&&Number.isSafeInteger(sample.phaseMs),
      'actual original phase or timestamp population differs');
    const first=Math.floor(proof.utcMs+m[2]-proof.anchorPerformanceMs)-proof.utcMs;
    const last=Math.floor(proof.utcMs+m[3]-proof.anchorPerformanceMs)-proof.utcMs;
    need(sample.phaseMs>=first&&sample.phaseMs<=last,'original phase lies outside its main-world Date formula bracket');
    const interval={ordinal,lowerMs:p[2]-m[2],upperMs:p[3]-m[3]};offsetIntervals.push(interval);
    lower=Math.max(lower,interval.lowerMs);upper=Math.min(upper,interval.upperMs);
  }
  return {protocol:'r0040-mechanism-bracket-inspection/1',status:'OBSERVED',rows:samples.length,
    clockDomains:['main-performance','isolated-performance','isolated-event-stamp'],originalStopSha256:sha(originalStopBytes),
    mainDateFormulaWithinEveryBracket:true,
    clockBridge:{protocol:'r0040-conditional-clock-offset/1',status:lower<=upper?'BOUNDED_CONDITIONAL_OFFSET':'UNRESOLVED_CLOCK_BRIDGE',
      assumption:'A stable unit-rate offset mapping main performance to isolated performance; equality of time origins is not assumed.',
      lowerMs:lower,upperMs:upper,intervals:offsetIntervals},
    nativeQualification:'NOT_VERIFIED',cause:'NOT_ESTABLISHED',
    interpretation:'Complete ordered brackets only. Conditional clock relation is diagnostic; no timestamp repair, renderer/cadence/visual qualification or original failure override.'};
}

module.exports={DRIVER_SHA256,MAIN_SHA256,READ_JOIN,LIMIT,originalExpressions,installMainBracket,snapshotMain,installIsolatedJoin,
  instrumentMain,reverseMain,instrumentIsolated,reverseIsolated,sameWorldArithmetic,inspectBrackets};
