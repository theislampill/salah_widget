'use strict';
// Disposable native observations only. No product owner, timer, visibility
// property or currentness predicate is replaced. Output is owner-private.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const http = require('node:http');

const BASE_INDEX = '88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1';
const COMBINED_INDEX = '55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2';
const INVENTORIES = Object.freeze({
  [BASE_INDEX]:'cbce31ba3a018b99e4259c192902442db421b2d8b8b65e48e143acf19bcaf4f2',
  [COMBINED_INDEX]:'69f819a9cce8b4fb82fc8977d64c71bdf0f071eec40972d0cf99df830250c481'
});
const KEYS = Object.freeze(['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha']);
const TIMES = Object.freeze(['05:00','06:00','12:00','15:30','18:00','19:30']);
const TARGETS = Object.freeze(['.cn','.nt','.left','.until-prayer','#ce','#ah','.bar>i','.arc','.times',
  '#dateGregorian','#dateHijri','#ceDateButton','#ahDateButton']);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function need(condition, message) { if (!condition) throw Error(message); }
function exactKeys(values, label) {
  need(Array.isArray(values) && values.length === 6 && new Set(values).size === 6 &&
    KEYS.every(k => values.includes(k)), 'incomplete '+label+': six distinct prayer keys required');
}
function prayerDifferences(s, expected) {
  need(s && expected, 'missing prayer sample');
  for (const target of TARGETS) need(s.targetCounts?.[target] === 1, 'incomplete target '+target);
  for (const field of ['current','nextPrayer','nextTime','countdown','gregorian','hijri']) {
    need(typeof s[field] === 'string' && s[field].trim(), 'blank prayer field '+field);
  }
  exactKeys(s.rows?.map(r=>r.key),'row'); exactKeys(s.markers?.map(m=>m.key),'marker');
  need(s.markers.filter(m=>m.next).length === 1 && (!KEYS.includes(s.nextPrayer) || s.markers.some(m=>m.next && m.key===s.nextPrayer)),
    'marker next does not match the observed next-prayer name');
  for (const m of s.markers) need([m.cx,m.cy,m.r].every(Number.isFinite) && m.r > 0 &&
    m.ring === (m.key === 'Sunrise'), 'incomplete marker geometry or sunrise ring');
  need(typeof s.arc === 'string' && s.arc.trim(), 'blank arc publication');
  need(s.currentRing?.count === 2 && [s.currentRing.cx,s.currentRing.cy].every(Number.isFinite),
    'incomplete current-position arc');
  need(s.progress && /^\d+(?:\.\d+)?%$/.test(s.progress.width) &&
    parseFloat(s.progress.width) <= 100 && s.progress.visibility === 'visible', 'incomplete progress publication');
  need(s.calendar && typeof s.calendar.gregorian === 'string' && typeof s.calendar.hijri === 'string' &&
    typeof s.calendar.gregorianAria === 'string' && typeof s.calendar.hijriAria === 'string', 'incomplete calendar disclosure');
  const differences = [];
  for (const field of ['current','nextPrayer','nextTime','countdown','gregorian','hijri','previewDay']) {
    if (s[field] !== expected[field]) differences.push(field);
  }
  if (s.calendar.gregorian !== expected.gregorian || s.calendar.hijri !== expected.hijri ||
      s.calendar.gregorianAria !== 'Show complete Gregorian date: '+expected.gregorian ||
      !s.calendar.hijriAria.startsWith('Show complete Hijri date: '+expected.hijri+'.')) differences.push('calendarDisclosure');
  if (s.progress.width !== expected.progressWidth) differences.push('progressWidth');
  if (s.rows.some((row,i)=>row.key !== KEYS[i] || row.label !== KEYS[i] || row.time !== TIMES[i] ||
      [...row.roles].sort().join(' ') !== expected.roles[i].split(' ').filter(Boolean).sort().join(' '))) differences.push('rows');
  if (s.markers.find(m=>m.next)?.key !== expected.nextPrayer) differences.push('nextMarker');
  if (!Number.isFinite(expected.ringX) || Math.abs(s.currentRing.cx-expected.ringX) > .02) differences.push('currentArc');
  return differences;
}
function qualifyPrayerPair(baseline, candidate, scenario) {
  try {
    for (const row of [baseline,candidate]) {
      need(row?.scenario === scenario.name && row.route === 'native-intersection-observer' &&
        row.sampleBoundary === 'mutation-observer-after-paused-removal', 'wrong restoration route or sample boundary');
      need(row.restoreCount === 1 && row.hidden?.paused === true && row.hidden.documentHidden === false &&
        row.hidden.intersects === false, 'restore/hide sequence incomplete');
      need(row.clock?.dateOnly === true && row.clock.performanceAdvanced === true &&
        row.clock.timerRan === true && row.clock.rafRan === true, 'real clock callbacks not established');
      const entries = row.intersections || [];
      const hidden = entries.findIndex(e=>e.isIntersecting === false);
      need(hidden >= 0 && entries.slice(hidden+1).some(e=>e.isIntersecting === true), 'native intersection sequence missing');
      need(Array.isArray(row.unexpectedRequests) && row.unexpectedRequests.length === 0, 'unexpected external request');
      need(row.before?.epoch === scenario.beforeUtc && row.afterTask?.epoch === scenario.afterUtc,
        'wrong fixed UTC at observation');
      need(row.afterTask.paused === false && row.afterTask.documentHidden === false && row.afterTask.bounds?.intersects,
        'return sample is not a visible card');
      need(prayerDifferences(row.before,scenario.before).length === 0, 'incorrect pre-hide prayer setup');
      need(prayerDifferences(row.afterRaf,scenario.after).length === 0, 'next probe rAF callback did not recover');
    }
    const baselineDifferences = prayerDifferences(baseline.afterTask,scenario.after);
    const candidateDifferences = prayerDifferences(candidate.afterTask,scenario.after);
    if (!baselineDifferences.length) return {status:'INCONCLUSIVE',reason:'baseline is already current at this boundary',
      baselineDifferences,candidateDifferences};
    if (candidateDifferences.length) return {status:'FAIL',baselineDifferences,candidateDifferences};
    return {status:'PASS',baselineDifferences,candidateDifferences,
      scope:'DOM at the restoring task boundary; no presented-frame or elapsed-cost claim'};
  } catch (error) { return {status:'INCOMPLETE',reason:error.message}; }
}
function selectedLayers(s) {
  need(s?.selector && s.ready === true && s.refined === false && s.frameCurrent === true &&
    s.framePresent === true && s.researchGeneration === s.selector, 'selected receipt does not identify current preview');
  const visible = (s.layers || []).filter(layer=>layer.visible);
  const sky = visible.filter(layer=>layer.className === 'r002f-sky-'+s.selector);
  const moon = visible.filter(layer=>layer.className === 'r002f-moon-'+s.selector);
  need(visible.length === 2 && sky.length === 1 && moon.length === 1, 'wrong native CSS-selected layers');
  for (const layer of [...sky,...moon]) need(layer.width > 0 && layer.height > 0 && layer.nonzeroAlpha > 0 &&
    /^[a-f0-9]{64}$/.test(layer.pixelsSha256), 'empty or incomplete selected canvas');
  need(s.mask && s.mask !== 'none' && s.moon?.current && s.moon.accepted, 'selected mask or lunar authority absent');
  return {sky:sky[0].pixelsSha256,moon:moon[0].pixelsSha256};
}
function qualifyPreview(row) {
  let before;
  try {
    need(row?.realMoonRuntime && row.realPreviewRuntime && row.refinedStartupBlocked &&
      Array.isArray(row.unexpectedRequests) && !row.unexpectedRequests.length, 'native owner or fixture admission incomplete');
    need(row.clock?.dateOnly && row.clock.performanceAdvanced && row.clock.timerRan && row.clock.rafRan,
      'real preview clock callbacks not established');
    need(row.fault?.hits === 1 && row.fault.message === 'r002f injected upload failure', 'staged upload fault was not exercised exactly once');
    need(Number.isInteger(row.fault.evaluation) && row.fault.evaluation === row.faultSnapshotEvaluation &&
      Number.isInteger(row.revokeEvaluation) && row.revokeEvaluation === row.revokeSnapshotEvaluation,
      'fault/revocation and selected layers were read in different evaluations');
    need(row.revocation?.kind==='actual-clock-discontinuity-invalidation' && row.revocation.deltaMs===2000 &&
      Number.isFinite(row.beforeRevoke?.epoch) && row.afterRevoke?.epoch-row.beforeRevoke.epoch===2000,
      'actual clock-discontinuity revocation was not established');
    before=selectedLayers(row.before);
  } catch (error) { return {status:'INCOMPLETE',reason:error.message}; }
  try {
    const after = selectedLayers(row.afterFault);
    need(before.sky === after.sky && before.moon === after.moon && row.before.selector === row.afterFault.selector &&
      row.before.mask === row.afterFault.mask && row.before.utcMs === row.afterFault.utcMs, 'failed upload mixed or replaced retained layers');
  } catch (error) { return {status:'FAIL',reason:error.message}; }
  try {
    selectedLayers(row.recovered);
    selectedLayers(row.beforeRevoke);
    need(row.recovered.selector !== row.before.selector && row.recovered.draws > row.before.draws &&
      row.recovered.utcMs === row.before.utcMs, 'healthy successor did not establish a new generation at the same fixed UTC');
  } catch (error) { return {status:'INCOMPLETE',reason:error.message}; }
  try {
    const revoked = row.afterRevoke;
    need(!revoked?.selector && revoked?.ready === false && revoked.refined === false && revoked.framePresent === false &&
      revoked.frameCurrent === false && revoked.researchGeneration == null && revoked.moon?.current === false &&
      revoked.moon.accepted === false && !(revoked.layers || []).some(layer=>layer.visible), 'lunar authority revocation left selected content');
  } catch (error) { return {status:'FAIL',reason:error.message}; }
  return {status:'PASS',scope:'native CSS selection and same-evaluation canvas state under deliberate faults; no compositor guarantee'};
}
function validateIsolation(receipt, host) {
  need(receipt?.protocol === 'salah-hosted-native-isolation/1' && receipt.passed === true &&
    Number.isInteger(host.uid) && host.uid > 0 && receipt.uid === host.uid &&
    typeof host.netns === 'string' && receipt.netns === host.netns &&
    typeof receipt.outerNetns === 'string' && receipt.outerNetns !== host.netns &&
    receipt.browserControl?.passed === true, 'native isolation receipt does not match the current nonroot network namespace');
  return true;
}
function installFixedDate(initialUtc) {
  const RealDate = globalThis.Date;
  let utc = initialUtc;
  function FixedDate(...args) {
    if (new.target) return Reflect.construct(RealDate,args.length ? args : [utc],new.target);
    return new RealDate(utc).toString();
  }
  FixedDate.prototype = RealDate.prototype;
  Object.setPrototypeOf(FixedDate,RealDate);
  FixedDate.now = () => utc;
  globalThis.Date = FixedDate;
  globalThis.__r002fClock = Object.freeze({set(value){if (!Number.isFinite(value)) throw Error('invalid fixed UTC');utc=value;},get:()=>utc});
}

function expected(current,nextPrayer,nextTime,countdown,gregorian,hijri,previewDay,progressWidth,roles,ringX) {
  return {current,nextPrayer,nextTime,countdown,gregorian,hijri,previewDay,progressWidth,roles:roles.split('|'),ringX};
}
const SCENARIOS = Object.freeze([
  {name:'fajr',beforeUtc:Date.parse('2026-09-07T04:59:30Z'),afterUtc:Date.parse('2026-09-07T05:01:30Z'),
    before:expected('Isha','Fajr','05:00','30s left until Fajr','2026-09-07','1448-02-25','26','99.9%','on|||||now',62.11513889),
    after:expected('Fajr','Sunrise','06:00','58m left until Sunrise','2026-09-07','1448-02-25','26','2.5%','now|on||||',62.52125)},
  {name:'maghrib',beforeUtc:Date.parse('2026-09-07T17:59:30Z'),afterUtc:Date.parse('2026-09-07T18:01:30Z'),
    before:expected('Asr','Maghrib','18:00','30s left until Maghrib','2026-09-07','1448-02-25','26','99.7%','past|past|past|now|on|',220.49847222),
    after:expected('Maghrib','Isha','19:30','1h 28m left until Isha','2026-09-07','1448-02-26',null,'1.7%','past|past|past|past|now|on',220.90458333)},
  {name:'midnight',beforeUtc:Date.parse('2026-09-07T23:59:30Z'),afterUtc:Date.parse('2026-09-08T00:01:30Z'),
    before:expected('Isha','Fajr','05:00','5h 0m left until Fajr','2026-09-07','1448-02-26',null,'47.3%','on|past|past|past|past|now',293.59847222),
    after:expected('Isha','Fajr','05:00','4h 58m left until Fajr','2026-09-08','1448-02-26',null,'47.6%','on|||||now',1.60458333)}
]);

// This function executes unchanged in the page. It reads actual DOM owners;
// qaState/model are deliberately not substitutes for prayer publication.
function readPrayerDom() {
  const selectors = ['.cn','.nt','.left','.until-prayer','#ce','#ah','.bar>i','.arc','.times',
    '#dateGregorian','#dateHijri','#ceDateButton','#ahDateButton'];
  const normalize = value => String(value ?? '').replace(/\s+/g,' ').trim();
  const one = selector => document.querySelector(selector);
  const text = selector => normalize(one(selector)?.textContent);
  const direct = selector => normalize(Array.from(one(selector)?.childNodes || []).filter(n=>n.nodeType===3).map(n=>n.nodeValue).join(''));
  const card = one('.c'), rect = card?.getBoundingClientRect();
  const intersects = !!rect && rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth;
  const progress = one('.bar>i');
  const ringPaths=Array.from(document.querySelectorAll('.arc path.cur'));
  const ringEnds=ringPaths[0]?[ringPaths[0].getPointAtLength(0),ringPaths[0].getPointAtLength(ringPaths[0].getTotalLength())]:null;
  return {
    epoch:Date.now(),at:performance.now(),paused:card?.classList.contains('paused'),documentHidden:document.hidden,
    targetCounts:Object.fromEntries(selectors.map(sel=>[sel,document.querySelectorAll(sel).length])),
    current:text('.cn'),nextPrayer:text('.until-prayer'),nextTime:text('.nt'),countdown:text('.left'),
    gregorian:direct('#ce'),hijri:direct('#ah'),previewDay:text('#ah .mph.pre').match(/(\d+)$/)?.[1] ?? null,
    calendar:{gregorian:text('#dateGregorian'),hijri:text('#dateHijri'),gregorianAria:one('#ceDateButton')?.getAttribute('aria-label'),
      hijriAria:one('#ahDateButton')?.getAttribute('aria-label'),reason:text('#dateReason'),visibleGregorian:text('#ce'),visibleHijri:text('#ah')},
    rows:Array.from(document.querySelectorAll('.times [data-prayer-key]')).map(el=>({key:el.dataset.prayerKey,label:normalize(el.querySelector('b')?.textContent),
      time:normalize(el.querySelector('.tm')?.textContent),roles:['now','on','past'].filter(role=>el.classList.contains(role))})),
    markers:Array.from(document.querySelectorAll('.arc circle[data-prayer-key]')).map(el=>({key:el.dataset.prayerKey,next:el.classList.contains('next'),
      ring:el.classList.contains('ring'),cx:Number(el.getAttribute('cx')),cy:Number(el.getAttribute('cy')),r:Number(el.getAttribute('r')),
      adjustment:el.getAttribute('data-adjustment')})),
    progress:{width:progress?.style.width,visibility:progress?getComputedStyle(progress).visibility:null},arc:one('.arc')?.innerHTML,
    currentRing:{count:ringPaths.length,cx:ringEnds?(ringEnds[0].x+ringEnds[1].x)/2:null,
      cy:ringEnds?(ringEnds[0].y+ringEnds[1].y)/2:null},
    raw:{current:one('.cn')?.outerHTML,nextTime:one('.nt')?.outerHTML,countdown:one('.left')?.outerHTML,
      times:one('.times')?.innerHTML,gregorian:one('#ce')?.outerHTML,hijri:one('#ah')?.outerHTML},
    bounds:rect?{x:rect.x,y:rect.y,width:rect.width,height:rect.height,intersects}:null
  };
}
function installRestoreObserver() {
  const card = document.querySelector('.c');
  if (!card || typeof IntersectionObserver !== 'function' || typeof MutationObserver !== 'function') throw Error('native observers unavailable');
  const state = window.__r002fRestore = {intersections:[],restoreCount:0,afterTask:null,afterRaf:null,
    hiddenSeen:false,wasPaused:card.classList.contains('paused'),armed:false};
  const intersection = new IntersectionObserver(entries=>{
    for (const entry of entries) state.intersections.push({isIntersecting:entry.isIntersecting,ratio:entry.intersectionRatio,
      at:entry.time,top:entry.boundingClientRect.top,bottom:entry.boundingClientRect.bottom});
  },{threshold:0});
  intersection.observe(card);
  const mutation = new MutationObserver(records=>{
    const paused = card.classList.contains('paused');
    if (paused) state.hiddenSeen = true;
    if (state.armed && state.hiddenSeen && state.wasPaused && !paused &&
        records.some(r=>r.target===card && r.type==='attributes' && r.attributeName==='class')) {
      state.restoreCount++;
      // A MutationObserver microtask follows the native restoring callback.
      // It precedes the next probe rAF; neither sample is a presented frame.
      if (!state.afterTask) {
        state.afterTask = window.__r002fReadPrayer();
        requestAnimationFrame(()=>{state.afterRaf=window.__r002fReadPrayer();});
      }
    }
    state.wasPaused = paused;
  });
  mutation.observe(card,{subtree:true,childList:true,characterData:true,attributes:true,attributeOldValue:true});
  window.__r002fRestoreDispose = () => {intersection.disconnect();mutation.disconnect();};
}

// Exact native pixel bytes are read synchronously with the selected CSS and
// receipt. Hashing/persistence happens later in Node, without rereading the page.
function readPreviewDom() {
  const card = document.querySelector('.c'), preview = window.SalahSkyPreview, state = preview?.state;
  const base64 = bytes => {
    let binary = '';
    for (let i=0;i<bytes.length;i+=32768) binary += String.fromCharCode(...bytes.subarray(i,i+32768));
    return btoa(binary);
  };
  const isVisible = node => {
    const rect=node.getBoundingClientRect(); if (!rect.width || !rect.height) return false;
    for (let n=node;n && n.nodeType===1;n=n.parentElement) {
      const style=getComputedStyle(n);
      if (style.display==='none' || style.visibility!=='visible' || Number(style.opacity)===0) return false;
    }
    return true;
  };
  const layers = Array.from(document.querySelectorAll('canvas.real-sky-preview,canvas.moon-detail-canvas,canvas[class^="r002f-sky-"],canvas[class^="r002f-moon-"]')).map(canvas=>{
    const style = getComputedStyle(canvas), visible=isVisible(canvas);
    const layer={className:canvas.className,visible,width:canvas.width,height:canvas.height,visibility:style.visibility,
      display:style.display,opacity:style.opacity,zIndex:style.zIndex};
    if (visible) {
      const rgba=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
      let nonzeroAlpha=0,nonzeroRgb=0;
      for (let i=0;i<rgba.length;i+=4) {if(rgba[i+3])nonzeroAlpha++;if(rgba[i]||rgba[i+1]||rgba[i+2])nonzeroRgb++;}
      Object.assign(layer,{nonzeroAlpha,nonzeroRgb,rgba:base64(rgba),png:canvas.toDataURL('image/png')});
    }
    return layer;
  });
  const maskNode=document.querySelector('.sun-cloud-mask');
  const observation = window.SalahMoonRuntime?.observe();
  return {at:performance.now(),epoch:Date.now(),selector:card?.getAttribute('data-r002f-preview'),
    ready:!!card?.classList.contains('real-sky-preview-ready'),refined:!!card?.classList.contains('real-sky-composed'),
    framePresent:!!preview?.frame,frameCurrent:!!preview?.frame?.current?.(),utcMs:state?.utcMs ?? null,
    researchGeneration:state?.researchGeneration ?? null,draws:state?.draws ?? null,status:state?.status,retained:state?.retained,reason:state?.reason,
    publication:state?.publication ?? null,mask:maskNode?getComputedStyle(maskNode).getPropertyValue('--native-sun-cloud-mask').trim():null,
    maskImage:maskNode?getComputedStyle(maskNode).maskImage:null,
    moon:{runtimePresent:!!window.SalahMoonRuntime,current:!!observation?.current,accepted:!!observation?.accepted,
      state:observation?.state ?? null},layers};
}

function parseArgs(argv) {
  const out = {engine:'chromium',dpr:1,rounds:5,section:'all',timeoutMs:120000};
  const allowed = new Set(['playwright','baseline','candidate','out','engine','dpr','rounds','section','timeout-ms']);
  for (let i=0;i<argv.length;i+=2) {
    const key=argv[i]?.slice(2);need(argv[i]?.startsWith('--') && allowed.has(key) && argv[i+1] && !argv[i+1].startsWith('--'),'unknown or missing argument');
    const dest=key==='timeout-ms'?'timeoutMs':key;out[dest]=['dpr','rounds','timeout-ms'].includes(key)?Number(argv[i+1]):argv[i+1];
  }
  for (const key of ['playwright','baseline','candidate','out']) need(typeof out[key]==='string','required --'+key);
  need(['chromium','firefox','webkit'].includes(out.engine),'unsupported engine');
  need([1,2,3].includes(out.dpr),'DPR must be 1, 2 or 3');
  need(Number.isInteger(out.rounds) && out.rounds>=1 && out.rounds<=10,'rounds must be 1..10');
  need(['all','prayer','preview'].includes(out.section),'section must be all, prayer or preview');
  need(Number.isInteger(out.timeoutMs) && out.timeoutMs>=5000 && out.timeoutMs<=180000,'timeout must be 5000..180000 ms');
  for (const key of ['playwright','baseline','candidate','out']) out[key]=path.resolve(out[key]);
  return out;
}
function builtIdentity(root, expectedIndex) {
  const index=fs.readFileSync(path.join(root,'index.html'));
  need(sha(index)===expectedIndex,'unadmitted generated index');
  const raw=fs.readFileSync(path.join(root,'GENERATED.json')), inventory=JSON.parse(raw);
  need(INVENTORIES[expectedIndex] && sha(raw)===INVENTORIES[expectedIndex],'unadmitted generated inventory identity');
  need(inventory.schema==='salah-generated-inventory/1' && inventory.files && inventory.fileCount===Object.keys(inventory.files).length,'invalid generated inventory');
  const files=[];
  for (const [relative,entry] of Object.entries(inventory.files)) {
    const absolute=path.resolve(root,relative);
    need(absolute.startsWith(root+path.sep) && !fs.lstatSync(absolute).isSymbolicLink(),'unsafe generated path');
    const data=fs.readFileSync(absolute);
    need(data.length===entry.bytes && sha(data)===entry.sha256,'generated inventory drift: '+relative);
    files.push({path:relative,bytes:data.length,sha256:entry.sha256});
  }
  return {indexSha256:sha(index),generatedInventorySha256:sha(raw),files};
}
async function serve(root, ledger) {
  root=fs.realpathSync(root);
  const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json',
    '.css':'text/css','.wasm':'application/wasm','.bin':'application/octet-stream','.png':'image/png'};
  const server=http.createServer((request,response)=>{
    try {
      const url=new URL(request.url,'http://127.0.0.1');
      const absolute=fs.realpathSync(path.join(root,decodeURIComponent(url.pathname)));
      need(absolute.startsWith(root+path.sep) && fs.statSync(absolute).isFile(),'outside static root');
      ledger.push({path:url.pathname,status:200});
      response.writeHead(200,{'Content-Type':types[path.extname(absolute)]||'application/octet-stream','Cache-Control':'no-store'});
      fs.createReadStream(absolute).on('error',()=>response.destroy()).pipe(response);
    } catch {ledger.push({path:request.url,status:404});response.writeHead(404);response.end();}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  return {server,origin:'http://127.0.0.1:'+server.address().port};
}
function fixturePrayer(url) {
  const match=/^\/v1\/timings\/(07|08)-09-2026$/.exec(url.pathname);
  if (!match) return null;
  const day=match[1],hijri=day==='07'?'25':'26';
  return {code:200,status:'OK',data:{timings:{Fajr:'05:00',Sunrise:'06:00',Dhuhr:'12:00',Asr:'15:30',Sunset:'18:00',Maghrib:'18:00',Isha:'19:30'},
    date:{gregorian:{date:day+'-09-2026',day,month:{number:9,en:'September'},year:'2026'},
      hijri:{date:hijri+'-02-1448',day:hijri,month:{number:2,en:'Safar'},year:'1448'}},meta:{timezone:'UTC'}}};
}
function fixtureWeather(utc) {
  const time=new Date(Math.floor(utc/900000)*900000).toISOString().slice(0,16);
  const current={time,interval:900,temperature_2m:21,apparent_temperature:21,relative_humidity_2m:45,dew_point_2m:8,
    wind_speed_10m:2,wind_direction_10m:90,wind_gusts_10m:3,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,
    visibility:24000,is_day:0,weather_code:0,precipitation:0,rain:0,showers:0,snowfall:0};
  const hourly={time:Array.from({length:72},(_,i)=>new Date(Date.parse('2026-09-06T00:00:00Z')+i*3600000).toISOString().slice(0,16))};
  for (const [key,value] of Object.entries(current)) if (!['time','interval'].includes(key)) hourly[key]=hourly.time.map(()=>value);
  return {timezone:'UTC',utc_offset_seconds:0,elevation:30,current,hourly};
}
async function openScene(browser,origin,utc,options,previewOnly) {
  const ledger={requests:[],unexpectedRequests:[],console:[],pageErrors:[],refinedStartupBlocked:false};
  const clock={utc};
  const context=await browser.newContext({viewport:{width:400,height:650},deviceScaleFactor:options.dpr,timezoneId:'UTC',
    reducedMotion:'no-preference',serviceWorkers:'block'});
  try {
  await context.addInitScript(installFixedDate,utc);
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());let action;
    const json=value=>route.fulfill({status:200,headers:{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},body:JSON.stringify(value)});
    try {
      if (url.origin===origin) {
        if (previewOnly && url.pathname==='/real-sky/native-sky.js') {
          action='deliberate-refined-startup-failure';ledger.refinedStartupBlocked=true;
          await route.fulfill({status:503,contentType:'text/javascript',body:'/* R002F probe: only refined-sky startup unavailable. */'});
        } else {action='loopback';await route.continue();}
      } else if (url.hostname==='api.aladhan.com' && /^\/v1\/timings\//.test(url.pathname)) {
        const value=fixturePrayer(url);action=value?'prayer-fixture':'prayer-successor-deliberately-unavailable';
        if(value)await json(value);else await route.fulfill({status:503,body:'research fixture has no additional day'});
      } else if (url.hostname==='api.open-meteo.com' && url.pathname==='/v1/forecast') {action='weather-fixture';await json(fixtureWeather(clock.utc));}
      else if (url.hostname==='api.rainviewer.com' && url.pathname==='/public/weather-maps.json') {
        action='empty-radar-fixture';await json({version:'2.0',generated:Math.floor(clock.utc/1000),host:'https://tilecache.rainviewer.com',radar:{past:[],nowcast:[]}});
      } else if (['fonts.googleapis.com','fonts.gstatic.com'].includes(url.hostname)) {action='optional-font-unavailable';await route.fulfill({status:200,contentType:'text/css',body:''});}
      else {action='unexpected-aborted';ledger.unexpectedRequests.push(url.href);await route.abort('blockedbyclient');}
    } catch(error) {action='route-error';ledger.unexpectedRequests.push(url.href+' '+error.message);try{await route.abort();}catch{}}
    ledger.requests.push({url:url.href,action});
  });
  if (context.routeWebSocket) await context.routeWebSocket('**/*',socket=>{ledger.unexpectedRequests.push(socket.url());socket.close();});
  const page=await context.newPage();
  page.on('console',msg=>{if(ledger.console.length<100)ledger.console.push({type:msg.type(),text:msg.text()});});
  page.on('pageerror',error=>{if(ledger.pageErrors.length<100)ledger.pageErrors.push(error.stack||error.message);});
  let fragment='lat=24.47&lon=39.61&label=R002F%20research&method=4&school=0&tz=UTC&time=24&units=c&datefmt=YYYY-MM-DD';
  if (previewOnly) fragment+='&simMoon=0.55&simWax=1&simMoonAlt=20&simMoonH=42';
  const response=await page.goto(origin+'/index.html#'+fragment,{waitUntil:'domcontentloaded',timeout:options.timeoutMs});
  need(response?.ok(),'generated document did not load');
  const servedIndexSha256=sha(await response.body());
  return {context,page,ledger,clock,servedIndexSha256,fragment};
  } catch(error) {await context.close();throw error;}
}
async function verifyLiveCallbacks(page) {
  return page.evaluate(async()=>{
    const date=Date.now(),before=performance.now();let timerRan=false,rafRan=false;
    await new Promise(resolve=>setTimeout(()=>{timerRan=true;resolve();},40));
    await new Promise(resolve=>requestAnimationFrame(()=>{rafRan=true;resolve();}));
    return {dateOnly:Date.now()===date,performanceAdvanced:performance.now()>before+20,timerRan,rafRan};
  });
}
async function prayerObservation(browser,site,arm,scenario,round,options,folder) {
  let scene;const row={scenario:scenario.name,arm,round,route:'native-intersection-observer',
    sampleBoundary:'mutation-observer-after-paused-removal',status:'INCOMPLETE'};
  try {
    scene=await openScene(browser,site.origin,scenario.beforeUtc,options,false);
    const {page}=scene;need(scene.servedIndexSha256===(arm==='baseline'?BASE_INDEX:COMBINED_INDEX),'served entry drift');
    await page.waitForFunction(want=>document.querySelector('.cn')?.textContent===want.current &&
      document.querySelector('.until-prayer')?.textContent===want.nextPrayer &&
      document.querySelector('#dateHijri')?.textContent===want.hijri &&
      (want.previewDay===null || document.querySelector('#ah .mph.pre')?.textContent?.trim().endsWith(want.previewDay)),scenario.before,{timeout:options.timeoutMs});
    await page.evaluate(source=>{window.__r002fReadPrayer=(0,eval)('('+source+')');},readPrayerDom.toString());
    row.clock=await verifyLiveCallbacks(page);
    await page.evaluate(installRestoreObserver);
    row.before=await page.evaluate(()=>window.__r002fReadPrayer());
    need(!prayerDifferences(row.before,scenario.before).length,'initial DOM differs from fixed fixture');
    await page.screenshot({path:path.join(folder,arm+'-'+scenario.name+'-'+round+'-before.png')});
    await page.evaluate(()=>{
      const spacer=document.createElement('div');spacer.id='r002f-offscreen-spacer';spacer.style.height='2200px';
      spacer.setAttribute('aria-hidden','true');document.querySelector('.c').before(spacer);window.scrollTo(0,0);
    });
    await page.waitForFunction(()=>document.querySelector('.c')?.classList.contains('paused') &&
      window.__r002fRestore?.intersections.some(e=>e.isIntersecting===false),null,{timeout:options.timeoutMs});
    row.hidden=await page.evaluate(()=>{
      const sample=window.__r002fReadPrayer();return {paused:sample.paused,documentHidden:sample.documentHidden,intersects:sample.bounds.intersects,
        bounds:sample.bounds,epoch:sample.epoch};
    });
    scene.clock.utc=scenario.afterUtc;
    await page.evaluate(utc=>{window.__r002fRestore.armed=true;window.__r002fClock.set(utc);document.querySelector('#r002f-offscreen-spacer').remove();},scenario.afterUtc);
    await page.waitForFunction(()=>window.__r002fRestore?.afterRaf && window.__r002fRestore.intersections.at(-1)?.isIntersecting,
      null,{timeout:options.timeoutMs});
    const restoration=await page.evaluate(()=>({afterTask:window.__r002fRestore.afterTask,afterRaf:window.__r002fRestore.afterRaf,
      restoreCount:window.__r002fRestore.restoreCount,intersections:window.__r002fRestore.intersections}));
    Object.assign(row,restoration,{status:'OBSERVED'});
    await page.screenshot({path:path.join(folder,arm+'-'+scenario.name+'-'+round+'-settled.png')});
    row.screenshotBoundary='settled after the next probe rAF; never the first presented frame';
    row.servedIndexSha256=scene.servedIndexSha256;
  } catch(error) {row.error=error.stack||error.message;}
  finally {if(scene){Object.assign(row,scene.ledger);await scene.context.close();}else row.unexpectedRequests=['scene not established'];}
  fs.writeFileSync(path.join(folder,arm+'-'+scenario.name+'-'+round+'.json'),JSON.stringify(row,null,2)+'\n',{flag:'wx'});
  return row;
}
function persistPixels(value,folder,prefix) {
  let serial=0;
  function visit(node) {
    if (!node || typeof node!=='object') return;
    if (typeof node.rgba==='string') {
      const rgba=Buffer.from(node.rgba,'base64');need(rgba.length===node.width*node.height*4,'native canvas byte count');
      node.pixelsSha256=sha(rgba);node.pixelBytes=rgba.length;delete node.rgba;
      if (node.png?.startsWith('data:image/png;base64,')) {
        const name=prefix+'-'+String(++serial).padStart(3,'0')+'.png', bytes=Buffer.from(node.png.split(',')[1],'base64');
        fs.writeFileSync(path.join(folder,name),bytes,{flag:'wx'});node.pngFile=name;node.pngSha256=sha(bytes);delete node.png;
      }
    }
    for (const child of Object.values(node)) if (child && typeof child==='object') visit(child);
  }
  visit(value);return value;
}
async function previewObservation(browser,site,arm,options,folder) {
  const row={arm,status:'INCOMPLETE',contextClosed:false,
    scope:'current preview replacement at fixed UTC; synthetic lunar scene disclosed'};let scene;
  try {
    scene=await openScene(browser,site.origin,Date.parse('2026-09-07T00:10:05Z'),options,true);
    const {page}=scene;need(scene.servedIndexSha256===(arm==='baseline'?BASE_INDEX:COMBINED_INDEX),'served entry drift');
    await page.waitForFunction(candidate=>{
      const card=document.querySelector('.c'),moon=window.SalahMoonRuntime?.observe();
      return card?.classList.contains('real-sky-preview-ready') && !card.classList.contains('real-sky-composed') &&
        moon?.current && window.SalahMoonDetail?.state?.visible && window.SalahSkyPreview?.frame?.current?.() &&
        (!candidate || !!card.getAttribute('data-r002f-preview'));
    },arm==='candidate',{timeout:options.timeoutMs});
    await page.evaluate(source=>{window.__r002fReadPreview=(0,eval)('('+source+')');window.__r002fEvaluation=0;},readPreviewDom.toString());
    row.clock=await verifyLiveCallbacks(page);
    await page.screenshot({path:path.join(folder,arm+'-preview-established.png')});
    const fault=await page.evaluate(candidate=>{
      const evaluation=++window.__r002fEvaluation,before=window.__r002fReadPreview();
      const proto=CanvasRenderingContext2D.prototype,original=proto.putImageData;
      let hits=0,message=null,escaped=null;
      proto.putImageData=function(...args){
        const className=this.canvas.className;
        if (!hits && (candidate?className.startsWith('r002f-sky-'):className==='real-sky-preview')) {
          hits++;message='r002f injected upload failure';throw Error(message);
        }
        return Reflect.apply(original,this,args);
      };
      let afterFault;
      try {
        try {window.SalahSkyPreview.update();} catch(error) {escaped=String(error.message||error);}
        // No await or second evaluate may occur between the fault and this read.
        afterFault=window.__r002fReadPreview();
      } finally {proto.putImageData=original;}
      return {before,afterFault,fault:{hits,message,escaped,evaluation},faultSnapshotEvaluation:evaluation,
        realMoonRuntime:typeof window.SalahMoonRuntime?.observe==='function',realPreviewRuntime:typeof window.SalahSkyPreview?.update==='function'};
    },arm==='candidate');
    Object.assign(row,fault);
    row.recovered=await page.evaluate(()=>{window.SalahSkyPreview.update();return window.__r002fReadPreview();});
    const revocation=await page.evaluate(()=>{
      const evaluation=++window.__r002fEvaluation,beforeRevoke=window.__r002fReadPreview(),runtime=window.SalahMoonRuntime;
      window.__r002fClock.set(Date.now()+2000);
      runtime.invalidate('probe actual clock discontinuity');
      const afterRevoke=window.__r002fReadPreview();
      return {beforeRevoke,afterRevoke,revokeEvaluation:evaluation,revokeSnapshotEvaluation:evaluation,
        revocation:{kind:'actual-clock-discontinuity-invalidation',deltaMs:2000},disposed:runtime.disposed};
    });
    Object.assign(row,revocation,{status:'OBSERVED',servedIndexSha256:scene.servedIndexSha256,fragment:scene.fragment});
    persistPixels(row,folder,arm+'-preview-canvas');
  } catch(error) {row.error=error.stack||error.message;}
  finally {
    if(scene){
      try {await scene.context.close();row.contextClosed=true;}
      catch(error){row.cleanupError=error.stack||error.message;}
      // Closing the context can deliver final route/WebSocket errors. Collect
      // its final ledger only after cleanup settles, then admit either arm.
      Object.assign(row,scene.ledger);
    } else row.unexpectedRequests=['scene not established'];
  }
  try {persistPixels(row,folder,arm+'-preview-unfinished');}
  catch(error){row.persistenceError=error.stack||error.message;}
  try {
    need(row.contextClosed && !row.error && !row.cleanupError && !row.persistenceError,
      'preview observation or context cleanup did not complete');
    need(Array.isArray(row.unexpectedRequests) && !row.unexpectedRequests.length &&
      Array.isArray(row.requests) && !row.requests.some(request=>['route-error','unexpected-aborted'].includes(request.action)),
      'unexpected request, WebSocket or route error in final preview ledger');
    if(arm==='candidate')row.verdict=qualifyPreview(row);
    else{
      need(row.realMoonRuntime && row.realPreviewRuntime && row.refinedStartupBlocked &&
        row.clock?.dateOnly && row.clock.performanceAdvanced && row.clock.timerRan && row.clock.rafRan,
        'baseline preview owner or callback admission incomplete');
      const pixels=s=>s.layers.filter(l=>l.visible).map(l=>({className:l.className,pixelsSha256:l.pixelsSha256}));
      row.faultComparison={before:pixels(row.before),after:pixels(row.afterFault),
        scope:'unchanged UTC can yield identical replacement pixels; no mixed-pixel baseline claim without changed detail'};
      row.verdict={status:row.fault.hits===1 && row.fault.message==='r002f injected upload failure'?'OBSERVED':'INCOMPLETE',
        reason:'baseline native fault control is descriptive; only the candidate has a shared selector'};
    }
  } catch(error){row.verdict={status:'INCOMPLETE',reason:error.message};}
  fs.writeFileSync(path.join(folder,arm+'-preview.json'),JSON.stringify(row,null,2)+'\n',{flag:'wx'});
  return row;
}
function overallStatus(statuses) {
  if(statuses.includes('FAIL'))return 'FAIL';if(statuses.includes('INCOMPLETE'))return 'INCOMPLETE';
  if(statuses.includes('INCONCLUSIVE'))return 'INCONCLUSIVE';return statuses.length && statuses.every(s=>s==='PASS')?'PASS':'INCOMPLETE';
}
async function main(argv) {
  if(argv.length===1 && argv[0]==='--help') {
    console.log('node r002f_probe.cjs --playwright DIR --baseline BUILT_MAIN --candidate BUILT_COMBINED --out FRESH_PRIVATE --engine chromium|firefox|webkit --dpr 1|2|3 [--rounds 1..10] [--section all|prayer|preview] [--timeout-ms 120000]');return;
  }
  const options=parseArgs(argv);need(!fs.existsSync(options.out),'output must be fresh');
  for(const source of [options.baseline,options.candidate,options.playwright,path.resolve(__dirname,'../../..')]) {
    need(options.out!==source && !options.out.startsWith(source+path.sep),'output must be outside source and dependency trees');
  }
  const isolationPath=process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;need(isolationPath,'native isolation receipt required');
  const isolation=JSON.parse(fs.readFileSync(isolationPath,'utf8'));
  validateIsolation(isolation,{uid:process.getuid?.(),netns:fs.readlinkSync('/proc/self/ns/net')});
  fs.mkdirSync(options.out,{recursive:true,mode:0o700});
  const receipt={protocol:'r002f-hosted-native/1',status:'INCOMPLETE',engine:options.engine,dpr:options.dpr,rounds:options.rounds,section:options.section,
    observerSha256:sha(fs.readFileSync(__filename)),node:process.version,isolationSha256:sha(fs.readFileSync(isolationPath)),
    limitations:['Controlled Date, synthetic UTC prayer/weather fixtures and real browser observers; no provider contacted.',
      'Only IntersectionObserver offscreen restoration is exercised. No synthetic visibility event, actual tab-hide or bfcache claim.',
      'MutationObserver and probe rAF samples are DOM observations, never first-presented-frame or elapsed-cost measurements.',
      'Preview uses real Moon/preview owners, deliberately unavailable refined startup and disclosed lunar simulation.',
      'Fixed-UTC healthy preview replacement checks generation/draw identity; it does not establish changed-scene or held-atmosphere continuity.',
      'Preview revocation advances Date by 2000 ms then calls the real Moon invalidation owner; no native visibility or disposal claim.',
      'Product policy conflicts and the original 244/248 combined Moon result remain unchanged.'],prayerPairs:[],preview:[]};
  const servers=[];let browser;
  try {
    receipt.sources={baseline:builtIdentity(options.baseline,BASE_INDEX),candidate:builtIdentity(options.candidate,COMBINED_INDEX)};
    const playwright=require(options.playwright),packagePath=path.join(options.playwright,'package.json');
    receipt.playwright={version:fs.existsSync(packagePath)?JSON.parse(fs.readFileSync(packagePath)).version:null};
    const launcher=playwright[options.engine];need(launcher?.launch,'Playwright engine missing');
    const executable=launcher.executablePath();receipt.playwright.executableSha256=sha(fs.readFileSync(executable));
    receipt.playwright.executableBytes=fs.statSync(executable).size;
    const sites={};receipt.served={baseline:[],candidate:[]};
    for(const arm of ['baseline','candidate']) {sites[arm]=await serve(options[arm],receipt.served[arm]);servers.push(sites[arm].server);}
    receipt.playwright.launch={headless:true,timeout:30000,executable:'sha256:'+receipt.playwright.executableSha256,
      ...(options.engine==='chromium'?{chromiumSandbox:true}:{})};
    browser=await launcher.launch({headless:true,timeout:30000,executablePath:executable,
      ...(options.engine==='chromium'?{chromiumSandbox:true}:{})});
    receipt.browserVersion=browser.version();
    if(options.section!=='preview') for(let round=1;round<=options.rounds;round++) for(const scenario of SCENARIOS) {
      const rows={};
      for(const arm of round%2?['baseline','candidate']:['candidate','baseline']) rows[arm]=await prayerObservation(browser,sites[arm],arm,scenario,round,options,options.out);
      receipt.prayerPairs.push({scenario:scenario.name,round,verdict:qualifyPrayerPair(rows.baseline,rows.candidate,scenario),
        baseline:armFile('baseline',scenario.name,round),candidate:armFile('candidate',scenario.name,round)});
    }
    if(options.section!=='prayer') for(const arm of ['baseline','candidate']) {
      const row=await previewObservation(browser,sites[arm],arm,options,options.out);
      receipt.preview.push({arm,file:arm+'-preview.json',verdict:row.verdict||{status:'INCOMPLETE',reason:'preview observation did not finish'}});
    }
    const statuses=receipt.prayerPairs.map(p=>p.verdict.status);
    if(options.section!=='prayer') {
      statuses.push(receipt.preview.find(p=>p.arm==='candidate')?.verdict.status||'INCOMPLETE');
      if(receipt.preview.find(p=>p.arm==='baseline')?.verdict.status!=='OBSERVED')statuses.push('INCOMPLETE');
    }
    receipt.status=overallStatus(statuses);
  } catch(error) {receipt.error=error.stack||error.message;}
  finally {
    if(browser)try{await browser.close();}catch(error){receipt.cleanupError=String(error);receipt.status='INCOMPLETE';}
    await Promise.all(servers.map(server=>new Promise(resolve=>server.close(resolve))));
    fs.writeFileSync(path.join(options.out,'result.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  }
  console.log('R002F_NATIVE '+receipt.status);
  process.exitCode=receipt.status==='PASS'?0:receipt.status==='FAIL'?1:2;
}
function armFile(arm,scenario,round) {return arm+'-'+scenario+'-'+round+'.json';}
module.exports = {prayerDifferences, qualifyPrayerPair, qualifyPreview, validateIsolation, installFixedDate,
  readPrayerDom,installRestoreObserver,readPreviewDom,parseArgs,builtIdentity,fixturePrayer,fixtureWeather,SCENARIOS,BASE_INDEX,COMBINED_INDEX};
if(require.main===module)main(process.argv.slice(2)).catch(error=>{console.error('R002F_NATIVE INCOMPLETE: '+error.message);process.exitCode=2;});
