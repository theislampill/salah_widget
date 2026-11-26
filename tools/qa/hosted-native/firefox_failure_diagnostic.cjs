'use strict';
// Failure evidence only. No browser import, launch, navigation, wait-for-state,
// process signal, policy write, or acceptance predicate belongs in this module.
const fs = require('node:fs');

const LIMITS = Object.freeze({events:64,snapshots:3,faults:16,urlChars:2048,errorChars:1024,
  evaluationMs:1000,identities:128,inputIdentities:256,statBytes:4096,cmdlineBytes:4096,
  exeBytes:4096,namespaceBytes:256,domRows:16,domCells:4,domTextChars:1024});
const NS_PER_MS = 1000000n;
const defaultNow = () => process.hrtime.bigint();
const errorRecord = error => ({name:String(error?.name || 'Error').slice(0,80),
  code:String(error?.code || '').slice(0,80),message:String(error?.message ?? error).slice(0,LIMITS.errorChars)});
function frozen(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) frozen(child);
    Object.freeze(value);
  }
  return value;
}
function text(value, limit) {
  if (typeof value !== 'string') throw Error('diagnostic string is unavailable');
  return {value:value.slice(0,limit),truncated:value.length > limit};
}
function addCount(state, key) {
  if (state[key] < Number.MAX_SAFE_INTEGER) state[key]++;
  else state.overflow = true;
}

function navigation(page, browser, {now=defaultNow}={}) {
  const state = {protocol:'firefox-navigation-failure-diagnostic/1',
    scope:'public main-frame events after listener attachment; cached API state only',
    events:[],snapshots:[],faults:[],mainFrameEvents:0,subframeEvents:0,overflow:false};
  let accepting = true, mainFrame = null, result = null;
  const attached = [];
  const stamp = () => now().toString();
  const fault = (phase,error) => {
    if (state.faults.length >= LIMITS.faults) { state.overflow = true; return; }
    let hostNs = null;
    try { hostNs = stamp(); } catch {}
    state.faults.push({phase,hostNs,...errorRecord(error)});
  };
  try {
    mainFrame = page.mainFrame();
    if (!mainFrame) throw Error('cached main frame is unavailable');
  } catch (error) { fault('main-frame-binding',error); }
  const recordEvent = (event, frame) => {
    if (!accepting) return;
    try {
      if (!mainFrame || page.mainFrame() !== mainFrame) throw Error('cached main-frame ownership changed or is unavailable');
      if (event === 'framenavigated' && frame !== mainFrame) { addCount(state,'subframeEvents'); return; }
      addCount(state,'mainFrameEvents');
      if (state.events.length >= LIMITS.events) { state.overflow = true; return; }
      const url = text(event === 'framenavigated' ? frame.url() : page.url(),LIMITS.urlChars);
      if (url.truncated) state.overflow = true;
      state.events.push({ordinal:state.mainFrameEvents-1,event,mainFrame:true,hostNs:stamp(),
        url:url.value,urlTruncated:url.truncated});
    } catch (error) { fault(event,error); }
  };
  for (const event of ['framenavigated','domcontentloaded','load']) {
    const handler = frame => recordEvent(event,frame);
    try { page.on(event,handler); attached.push([event,handler]); }
    catch (error) { fault('attach-'+event,error); }
  }
  return {
    snapshot(phase) {
      if (!accepting) return;
      try {
        if (!['before-attempt','on-rejection','before-cleanup'].includes(phase) ||
            state.snapshots.some(row => row.phase === phase)) throw Error('unexpected or duplicate snapshot phase');
        if (state.snapshots.length >= LIMITS.snapshots) { state.overflow = true; return; }
        const row = {phase,hostNs:stamp()};
        for (const [name,read] of [['url',()=>page.url()],['pageClosed',()=>page.isClosed()],
          ['browserConnected',()=>browser.isConnected()]]) {
          try {
            const value = read();
            if (name === 'url') {
              const bounded = text(value,LIMITS.urlChars); row.url = bounded.value;
              row.urlTruncated = bounded.truncated; if (bounded.truncated) state.overflow = true;
            } else {
              if (typeof value !== 'boolean') throw Error('cached state is not Boolean');
              row[name] = value;
            }
          } catch (error) { row[name+'Error'] = errorRecord(error); fault('snapshot-'+name,error); }
        }
        state.snapshots.push(row);
      } catch (error) { fault('snapshot',error); }
    },
    finish() {
      if (result) return result;
      accepting = false;
      for (const [event,handler] of attached) {
        try { page.off(event,handler); } catch (error) { fault('detach-'+event,error); }
      }
      result = frozen({...state,collectionComplete:!!mainFrame && !state.overflow && state.faults.length === 0});
      return result;
    }
  };
}

function boundedDom(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('DOM evaluator did not return an object');
  const expected = ['protocol','url','readyState','activeTables','errorTables','activeRows','errorRows',
    'activeCount','errorCount','inactiveVisible','noPoliciesVisible','overflow'];
  if (Object.keys(value).length !== expected.length || expected.some(key => !Object.hasOwn(value,key)))
    throw Error('DOM evaluator returned a foreign field population');
  const dom = {}; let truncated = false;
  for (const [name,limit] of [['protocol',64],['url',LIMITS.urlChars],['readyState',32]]) {
    const field = text(value[name],limit); dom[name] = field.value; truncated ||= field.truncated;
  }
  for (const name of ['activeTables','errorTables','activeCount','errorCount']) {
    if (!Number.isSafeInteger(value[name]) || value[name] < 0) throw Error('DOM evaluator returned a malformed count');
    dom[name] = value[name];
  }
  for (const name of ['inactiveVisible','noPoliciesVisible','overflow']) {
    if (typeof value[name] !== 'boolean') throw Error('DOM evaluator returned a malformed Boolean');
    dom[name] = value[name];
  }
  for (const name of ['activeRows','errorRows']) {
    const rows = value[name]; if (!Array.isArray(rows)) throw Error('DOM evaluator returned malformed rows');
    truncated ||= rows.length > LIMITS.domRows;
    dom[name] = rows.slice(0,LIMITS.domRows).map(row => {
      if (!Array.isArray(row)) throw Error('DOM evaluator returned malformed cells');
      truncated ||= row.length > LIMITS.domCells;
      return row.slice(0,LIMITS.domCells).map(cell => {
        const field = text(cell,LIMITS.domTextChars); truncated ||= field.truncated; return field.value;
      });
    });
  }
  return {dom,truncated};
}

async function failureDom(page, evaluator, {deadlineNs,now=defaultNow}={}) {
  const started = now();
  const row = {protocol:'firefox-failure-dom-read/1',attempted:false,startedNs:started.toString(),
    allocation:'unused original initial readback; original hard child deadline still applies',
    evaluationCancelled:false};
  let timer;
  try {
    if (typeof deadlineNs !== 'bigint') throw Error('absolute unused readback deadline is required');
    const remaining = deadlineNs-started;
    const capMs = Math.min(LIMITS.evaluationMs,Number(remaining / NS_PER_MS));
    row.capMs = Math.max(0,capMs);
    if (capMs <= 0) return frozen({...row,status:'NOT_ATTEMPTED',reason:'unused readback allocation exhausted'});
    if (!page || page.isClosed()) return frozen({...row,status:'UNAVAILABLE',reason:'policy page is absent or closed'});
    row.attempted = true;
    // Playwright evaluate has no per-call cancellation here. Neither branch of
    // the evaluation promise writes into row or into the original report.
    const evaluation = Promise.resolve().then(() => page.evaluate(evaluator)).then(
      value => ({kind:'value',value}),error => ({kind:'error',error:errorRecord(error)}));
    const outcome = await Promise.race([evaluation,new Promise(resolve => {
      timer = setTimeout(() => resolve({kind:'timeout'}),capMs);
    })]);
    const ended = now(); row.endedNs = ended.toString();
    if (ended < started) throw Error('diagnostic monotonic clock moved backwards');
    if (outcome.kind === 'timeout' || ended-started >= BigInt(capMs)*NS_PER_MS || ended >= deadlineNs)
      return frozen({...row,status:'TIMED_OUT',uncancelledEvaluation:true});
    if (outcome.kind === 'error') return frozen({...row,status:'ERROR',error:outcome.error});
    const payload = boundedDom(outcome.value);
    return frozen({...row,status:'CAPTURED',dom:payload.dom,retentionTruncated:payload.truncated,
      collectionOverflow:payload.truncated || payload.dom.overflow});
  } catch (error) { return frozen({...row,status:'ERROR',error:errorRecord(error)}); }
  finally { clearTimeout(timer); }
}

function cleanupPredicateMessage(report) {
  return !Array.isArray(report?.processes?.observed) || !Array.isArray(report?.finalProcesses?.observed)
    ? 'missing required success-path process census; tracked liveness is not established by this absence'
    : 'a tracked Firefox process remains live';
}

function parseStat(raw, pid) {
  const end = raw.lastIndexOf(')'),prefix = raw.slice(0,raw.indexOf('(')).trim();
  const fields = raw.slice(end+2).trim().split(/\s+/);
  if (end < 0 || prefix !== String(pid) || fields.length < 20 || !/^[A-Za-z]$/.test(fields[0]) ||
      !/^\d+$/.test(fields[1]) || !/^\d{1,32}$/.test(fields[19]) || !Number.isSafeInteger(Number(fields[1])))
    throw Error('bounded process stat identity is malformed');
  return {pid,state:fields[0],ppid:Number(fields[1]),startTicks:fields[19]};
}
function boundedReadFile(file, limit, check) {
  check(); const fd = fs.openSync(file,'r');
  const bytes = Buffer.alloc(limit+1); let count = 0;
  try {
    while (count < bytes.length) {
      check(); const got = fs.readSync(fd,bytes,count,bytes.length-count,null); count += got;
      check(); if (!got) break;
    }
  } finally { fs.closeSync(fd); }
  return {raw:bytes.subarray(0,Math.min(count,limit)).toString('utf8'),truncated:count > limit};
}
function cleanupProcesses(observed, {deadlineNs,now=defaultNow,io={}}={}) {
  const started = now(), result = {protocol:'firefox-cleanup-process-diagnostic/1',
    scope:'bounded stat-bracketed reads after original cleanup and predicates; no reaping or liveness qualification',
    startedNs:started.toString(),deadlineNs:typeof deadlineNs === 'bigint' ? deadlineNs.toString() : null,
    inputCount:Array.isArray(observed) ? observed.length : null,identities:[],inputErrors:[],overflow:false,
    budgetExpired:false,status:'PARTIAL'};
  const expired = () => now() >= deadlineNs;
  const check = () => {
    if (typeof deadlineNs !== 'bigint' || expired()) {
      const error = Error('absolute residual cleanup deadline exhausted'); error.code = 'DIAGNOSTIC_DEADLINE'; throw error;
    }
  };
  const inputError = message => {
    if (result.inputErrors.length < LIMITS.faults) result.inputErrors.push({message}); else result.overflow = true;
  };
  try {
    if (!Array.isArray(observed)) throw Error('observed PID/start-tick population is unavailable');
    const identities = new Map();
    if (observed.length > LIMITS.inputIdentities) result.overflow = true;
    for (const original of observed.slice(0,LIMITS.inputIdentities)) {
      if (!Number.isSafeInteger(original?.pid) || original.pid <= 0 ||
          typeof original.startTicks !== 'string' || !/^\d{1,32}$/.test(original.startTicks)) {
        inputError('malformed observed PID/start-tick identity'); continue;
      }
      const key = original.pid+':'+original.startTicks;
      if (!identities.has(key)) identities.set(key,{pid:original.pid,startTicks:original.startTicks});
    }
    result.uniqueIdentities = identities.size;
    if (!identities.size) {
      result.status = 'NO_OBSERVED_IDENTITIES'; result.endedNs = now().toString(); return frozen(result);
    }
    if (identities.size > LIMITS.identities) result.overflow = true;
    const read = (pid,name,limit,link=false) => {
      let before;
      try {
        check(); before = now();
        const value = link
          ? (io.readLink ? io.readLink(pid,name,limit) : fs.readlinkSync('/proc/'+pid+'/'+name))
          : (io.readText ? io.readText(pid,name,limit) : boundedReadFile('/proc/'+pid+'/'+name,limit,check));
        const rawValue = typeof value === 'string' ? {raw:value,truncated:false} : value;
        if (!rawValue || typeof rawValue.raw !== 'string' || typeof rawValue.truncated !== 'boolean') throw Error('malformed bounded proc read');
        const bytes = Buffer.from(rawValue.raw), after = now(), late = after >= deadlineNs;
        if (late) result.budgetExpired = true;
        return {status:'READ',beforeNs:before.toString(),afterNs:after.toString(),raw:bytes.subarray(0,limit).toString('utf8'),
          truncated:rawValue.truncated || bytes.length > limit,afterDeadline:late};
      } catch (error) {
        if (error.code === 'DIAGNOSTIC_DEADLINE') result.budgetExpired = true;
        return {status:error.code === 'DIAGNOSTIC_DEADLINE' ? 'BUDGET_EXHAUSTED' : 'ERROR',
          beforeNs:before?.toString() ?? null,error:errorRecord(error)};
      }
    };
    for (const expected of [...identities.values()].slice(0,LIMITS.identities)) {
      if (typeof deadlineNs !== 'bigint' || expired()) { result.budgetExpired = true; break; }
      const row = {expected,reads:{},identityStatus:'UNKNOWN',fieldStatus:'PARTIAL'};
      result.identities.push(row);
      row.reads.statBefore = read(expected.pid,'stat',LIMITS.statBytes);
      let before = null, after = null;
      if (row.reads.statBefore.status === 'READ' && !row.reads.statBefore.truncated) {
        try { before = parseStat(row.reads.statBefore.raw,expected.pid); row.statBefore = before; }
        catch (error) { row.statBeforeError = errorRecord(error); }
      }
      if (before && !result.budgetExpired) {
        for (const [name,limit,link] of [['cmdline',LIMITS.cmdlineBytes,false],['exe',LIMITS.exeBytes,true],
          ['ns/net',LIMITS.namespaceBytes,true],['ns/pid',LIMITS.namespaceBytes,true]]) {
          row.reads[name] = read(expected.pid,name,limit,link);
          if (result.budgetExpired) break;
        }
      }
      row.reads.statAfter = read(expected.pid,'stat',LIMITS.statBytes);
      if (row.reads.statAfter.status === 'READ' && !row.reads.statAfter.truncated) {
        try { after = parseStat(row.reads.statAfter.raw,expected.pid); row.statAfter = after; }
        catch (error) { row.statAfterError = errorRecord(error); }
      }
      const absent = reading => reading.status === 'ERROR' && ['ENOENT','ESRCH'].includes(reading.error.code);
      if (before && after && before.startTicks === after.startTicks) {
        row.identityStatus = after.startTicks === expected.startTicks ? 'SAME_INCARNATION' : 'DIFFERENT_INCARNATION';
        row.observedState = ['Z','X','x'].includes(after.state) ? (after.state === 'Z' ? 'ZOMBIE' : 'EXITED_STATE') : 'PRESENT';
        row.stateChanged = before.state !== after.state; row.parentChanged = before.ppid !== after.ppid;
      } else if ((before && after) || (before && absent(row.reads.statAfter)) || (after && absent(row.reads.statBefore))) {
        row.identityStatus = 'CHANGED_DURING_READ';
      } else if (absent(row.reads.statBefore) && absent(row.reads.statAfter)) {
        row.identityStatus = 'ABSENT_AT_BOTH_STAT_READS';
      }
      const readings = Object.values(row.reads);
      row.fieldStatus = readings.every(r => r.status === 'READ' && !r.truncated && !r.afterDeadline) ? 'COLLECTED' : 'PARTIAL';
      if (readings.some(r => r.truncated)) result.overflow = true;
      if (result.budgetExpired) break;
    }
    const complete = result.identities.length === identities.size && !result.overflow && !result.inputErrors.length &&
      result.identities.every(row => row.identityStatus === 'ABSENT_AT_BOTH_STAT_READS' ||
        (['SAME_INCARNATION','DIFFERENT_INCARNATION'].includes(row.identityStatus) && row.fieldStatus === 'COLLECTED'));
    result.status = result.budgetExpired ? 'BUDGET_EXHAUSTED' : complete ? 'COLLECTED' : 'PARTIAL';
  } catch (error) { result.error = errorRecord(error); }
  const ended = now(); result.endedNs = ended.toString();
  if (typeof deadlineNs === 'bigint' && ended >= deadlineNs) {
    result.budgetExpired = true; result.status = 'BUDGET_EXHAUSTED';
  }
  return frozen(result);
}

module.exports = {LIMITS,errorRecord,frozen,navigation,boundedDom,failureDom,cleanupPredicateMessage,parseStat,cleanupProcesses};
