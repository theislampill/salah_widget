'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {createHash} = require('node:crypto');

const sourcePath = process.env.SALAH_CLOCK_SOURCE || path.join(__dirname, '..', 'index.html');
const source = fs.readFileSync(sourcePath, 'utf8');
const configPath = process.env.SALAH_CLOCK_CONFIG || path.join(__dirname, '..', 'config.js');
const configSource = fs.readFileSync(configPath, 'utf8');
const sha256 = text => createHash('sha256').update(text).digest('hex');
function slice(start, end, text = source) {
  const a = text.indexOf(start), b = text.indexOf(end, a);
  assert(a >= 0 && b > a, `Actual source markers unavailable: ${start} / ${end}`);
  return text.slice(a, b);
}
const temporal = slice('const _RAFNOW =', '// ---- prayer-times data:');
const helpers = slice('const $    =', '// ---- SINGLE TEMPORAL SOURCE OF TRUTH');
const modelSource = slice('// build everything render() needs', '// draw the solar-prayer arc');
const renderSource = slice('let _lastBolt=-1', 'function updateSimClock');
const lifecycle = slice('async function loadPrayerData()', '// ——————————————————————— in-widget settings');
const prayerSource = slice('// ---- prayer-times data:', '// ---- weather (Open-Meteo:');
const configBindings = slice('function bindConfig(c)', 'if(window.SalahConfig)');
const persistenceSource = source.includes('function _publishPersistence(')
  ? slice('let _persistOutcome=null', '// A dialog session') : '';
// Accepted SKY gates run unchanged. Catalog/canvas producers remain outside these CLOCK source tests.
const skySources = source.includes('function beginSkyScene()') ? {
  astronomy: slice('const _RAD=', '// ---- moon phase'),
  stars: slice('let _starCat=null', 'function buildStars()'),
  moonSurface: slice('let _mAlb=null', '(function loadMoonMaps()'),
  moonGeometry: slice('let moonSky=', '// Raw backing-canvas'),
  cloudMotion: slice('let _cloudFieldSeed=0', '// puff template'),
  scene: slice('function skySceneIdentity()', '// build the animated weather overlay once')
} : null;

function realm({query = '', zone = 'UTC', wall = Date.parse('2026-09-07T12:00:00Z'), mono = 0,
  intl = Intl, block = temporal, globals = {}} = {}) {
  const clock = {wall, mono, reads: 0};
  class ClockDate extends Date {
    constructor(...args) { super(...(args.length ? args : [clock.wall])); }
    static now() { clock.reads++; return clock.wall; }
  }
  const q = new URLSearchParams(query);
  const context = vm.createContext({Date: ClockDate, Intl: intl, URLSearchParams, q,
    SIM: {time: q.get('simTime')}, tz: zone, performance: {now: () => clock.mono},
    pad: n => String(n).padStart(2, '0'), ...globals});
  const run = text => vm.runInContext(text, context, {timeout: 5000});
  run(block);
  return {context, clock, run};
}

function countedIntl(offset = 0) {
  const counts = {constructs: 0, projections: 0, invalid: 0};
  const intl = Object.create(Intl);
  intl.DateTimeFormat = function (...args) {
    counts.constructs++;
    const actual = new Intl.DateTimeFormat(...args);
    return {format: date => actual.format(date), resolvedOptions: () => actual.resolvedOptions(), formatToParts(date) {
      counts.projections++;
      if(!Number.isFinite(date.getTime())) counts.invalid++;
      return actual.formatToParts(new Date(date.getTime() + offset));
    }};
  };
  return {intl, counts};
}

function prayerRecord(date, zone = 'America/New_York', clocks = {}) {
  const [year, month, day] = date.split('-').map(Number);
  return {timings: {Fajr: '05:00', Sunrise: '06:00', Dhuhr: '12:00', Asr: '15:30',
    Maghrib: '18:00', Sunset: '18:00', Isha: '19:30', ...clocks},
    meta: {timezone: zone}, date: {gregorian: {year: String(year), day: String(day).padStart(2, '0'),
      month: {number: month, en: 'Fixture month'}, date: `${String(day).padStart(2, '0')}-${String(month).padStart(2, '0')}-${year}`},
      hijri: {year: '1448', day: '01', month: {number: 3, en: 'Fixture Hijri'}}}};
}

function nodes() {
  const store = new Map();
  const listeners = new Map();
  const createElement = () => {
      let html = '', text = '';
      const classes=new Set(), attributes=new Map(), events=new Map(), children=[];
      const element = {style: {setProperty(name,value){this[name]=String(value);},removeProperty(name){delete this[name];}}, dataset: {}, children, events,
        classList: {add(...names) {names.forEach(name=>classes.add(name));}, remove(...names) {names.forEach(name=>classes.delete(name));},
          toggle(name,on) {if(on===undefined)on=!classes.has(name);if(on)classes.add(name);else classes.delete(name);return !!on;}, contains(name) {return classes.has(name);}},
        set className(value) {classes.clear();String(value).split(/\s+/).filter(Boolean).forEach(name=>classes.add(name));},
        get className() {return [...classes].join(' ');},
        setAttribute(name,value) {attributes.set(name,String(value));if(name==='class')this.className=value;
          if(name.startsWith('data-'))this.dataset[name.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(value);},
        getAttribute(name) {return name==='class'?this.className:(attributes.get(name)??null);},
        appendChild(child) {children.push(child);}, querySelector(selector) {return children.find(child=>(child.className||'').split(' ').includes(selector.slice(1)))||null;},
        addEventListener(name,callback) {events.set(name,callback);},
        set textContent(value) {text = String(value); html = text;}, get textContent() {return text;},
        set innerHTML(value) {html = String(value); text = html.replace(/<[^>]*>/g, '');}, get innerHTML() {return html;}};
      return element;
  };
  // Read actual opening-tag attributes once; ID/class aliases share one node. This does not model layout,
  // parsed generated SVG, CSS or canvas, and cannot manufacture a successful celestial production.
  for(const match of slice('<body>', '<script src="config.js"></script>').matchAll(/<[a-z][\w:-]*\b([^>]*)>/gi)){
    const element=createElement();
    for(const attribute of match[1].matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/g)) element.setAttribute(attribute[1],attribute[3]);
    const id=element.getAttribute('id'); if(id&&!store.has('#'+id))store.set('#'+id,element);
    for(const name of element.className.split(/\s+/).filter(Boolean))if(!store.has('.'+name))store.set('.'+name,element);
  }
  const querySelector = selector => {
    if (!store.has(selector)) store.set(selector,createElement());
    return store.get(selector);
  };
  return {querySelector, getElementById:id=>querySelector('#'+id), createElement, store, visibilityState:'visible',
    addEventListener(name, callback) {listeners.set(name, callback);}, listeners};
}

function loadSkyBindings(r) {
  if(!skySources || r.skyBindingsLoaded) return r;
  for(const block of Object.values(skySources))r.run(block);
  return {...r,skyBindingsLoaded:true};
}

function modelRealm(options = {}) {
  const dom = nodes();
  const globals = {document: dom, fmt24: true, datefmtStr: 'YYYY-MM-DD',
    prayers: ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'],
    today: prayerRecord('2026-09-07', options.zone), tomorrow: null,
    ...options.globals};
  const r = realm({...options, globals});
  r.run(helpers);
  r.run(modelSource);
  r.run(slice('function showError(msg)', 'function isDayNow'));
  return {...r, dom};
}

function loadPrayerPipeline(r) {
  if (r.prayerTransport) return r;
  const requests=[], timers=new Map(), storage=new Map(); let serial=0;
  const transport={requests,timers,storage,auto:false,onRequest:null};
  Object.assign(r.context, {lat:24,lon:39,label:'Fixture',method:'2',school:'0',units:'f',LPOLL:0,
    _cacheTz:r.context.tz,CONFIG:null,lastDate:null,_loopStarted:false,_storageErr:null,
    fetchingTomorrow:false,_prayerStale:false,_rolloverBusy:false,_rolloverNextTry:0,_ROLLOVER_RETRY_MS:60000,
    wxBusy:false,radarBusy:false,AbortController,
    setTimeout(callback,ms=0){const id=++serial;timers.set(id,{at:r.clock.mono+Number(ms),callback});return id;},
    clearTimeout(id){timers.delete(id);},
    localStorage:{getItem:key=>storage.get(key)??null,setItem:(key,value)=>storage.set(key,String(value)),removeItem:key=>storage.delete(key)},
    fetch(url,init){
      const day=new URL(url).pathname.split('/').pop(), zone=r.context.tz;
      let resolve,reject; const promise=new Promise((a,b)=>{resolve=a;reject=b;});
      const request={url,init,day,zone,resolve(data=prayerRecord(day.split('-').reverse().join('-'),zone)){
        resolve({ok:true,status:200,json:async()=>({code:200,status:'OK',data})});
      },reject};
      requests.push(request); if(transport.onRequest) transport.onRequest(request);
      if(transport.auto) request.resolve();
      return promise;
    }});
  r.context.window=r.context;
  r.run(configSource); r.run(configBindings);
  r.context._clockFixtureConfig={lat:24,lon:39,tz:r.context.tz,label:'Fixture',method:'2',school:'0',
    time:r.context.fmt24?'24':'12',units:'f',datefmt:r.context.datefmtStr,source:'manual'};
  r.run('bindConfig(SalahConfig.normalize(_clockFixtureConfig))');
  if(persistenceSource) r.run(persistenceSource); // Actual accepted settings/save disclosure, when present in this source.
  r.run(prayerSource); // Actual admission, ownership, deadlines, cache, prefetch, adoption and civil-day paths.
  transport.settle=async()=>{for(let i=0;i<16;i++) await Promise.resolve();};
  return {...r,prayerTransport:transport};
}

function loadRender(r, block = renderSource) {
  r=loadSkyBindings(loadPrayerPipeline(r));
  Object.assign(r.context, {lastMoonMin: -1,
    _prayerStale: false, _moonStaleWarned: false,
    setLocLabel() {}, syncWeather() {}, renderMoon() {},
    fitCn() {}, drawArc: () => '<svg>fixture arc dependency</svg>', applyTheme() {},
    moonNow: () => ({phase: 0.5}), phaseEmoji: () => '◐', console});
  if(!skySources)Object.assign(r.context,{moonSky:{},_starsProjected:true,projectStars(){}});
  r.run(block);
  return r;
}

function loadLifecycle(r, block = lifecycle, {autoTimings=true} = {}) {
  r=loadSkyBindings(loadPrayerPipeline(r)); r.prayerTransport.auto=autoTimings;
  const calls={stars:0,weatherBuild:0,moon:0,weatherStart:0,cloud:0,requests:[],raf:0};
  calls.requests.push(...r.prayerTransport.requests.map(request=>request.day));
  r.prayerTransport.onRequest=request=>calls.requests.push(request.day);
  const pending=new Map(); let rafId=0;
  Object.assign(r.context, {QA:false, MOTIONFULL:false, DEBUGMOTION:false,
    _needsDetect:false, _cfgMode:'hardcoded',
    _loopStarted:false, lastDate:null, _prayerStale:false, _rolloverBusy:false,
    _rolloverNextTry:0, _ROLLOVER_RETRY_MS:60000,
    buildStars(){calls.stars++;}, buildWeather(){calls.weatherBuild++;},
    renderMoon(){calls.moon++;}, startWeather(){calls.weatherStart++;},
    fetchWeather(){}, fetchRadar(){}, isMotionReduced:()=>false,
    paintClouds(){calls.cloud++;}, tieRainToClouds(){},
    requestAnimationFrame(callback){const id=++rafId; pending.set(id,callback); calls.raf++; return id;},
    cancelAnimationFrame(id){pending.delete(id);}, console});
  r.run(block);
  const frame=()=>{const [id,callback]=pending.entries().next().value || []; assert(callback,'An actual loop callback must be scheduled'); pending.delete(id); callback();};
  return {...r,calls,pending,frame};
}

function loadSettingsAffordance(r) {
  r.run(slice('function enableSettingsAffordance()', 'function openSettings()'));
  r.run(slice('function _enableSettingsAffordance()', 'function _settingsFormToConfig()'));
  r.context._toggleSettings=()=>{}; // Dialog contents remain the browser owner's qualification cell.
  return r;
}

module.exports = {sourcePath, source, configPath, configSource, sha256, slice, temporal, helpers, modelSource, prayerSource, persistenceSource,
  skySources, renderSource, lifecycle, realm, countedIntl, prayerRecord, modelRealm, loadPrayerPipeline, loadSkyBindings, loadRender, loadLifecycle, loadSettingsAffordance};
