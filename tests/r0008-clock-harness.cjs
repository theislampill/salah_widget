'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {createHash} = require('node:crypto');

const sourcePath = process.env.SALAH_CLOCK_SOURCE || path.join(__dirname, '..', 'index.html');
const source = fs.readFileSync(sourcePath, 'utf8');
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
    return {formatToParts(date) {
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
      return {style: {}, dataset: {fx: 'clear'}, children, events,
        classList: {add(...names) {names.forEach(name=>classes.add(name));}, remove(...names) {names.forEach(name=>classes.delete(name));},
          toggle(name,on) {if(on===undefined)on=!classes.has(name);if(on)classes.add(name);else classes.delete(name);}, contains(name) {return classes.has(name);}},
        setAttribute(name,value) {attributes.set(name,String(value));}, getAttribute(name) {return attributes.get(name)??null;},
        appendChild(child) {children.push(child);}, querySelector(selector) {return children.find(child=>(child.className||'').split(' ').includes(selector.slice(1)))||null;},
        addEventListener(name,callback) {events.set(name,callback);},
        set textContent(value) {text = String(value); html = text;}, get textContent() {return text;},
        set innerHTML(value) {html = String(value); text = html.replace(/<[^>]*>/g, '');}, get innerHTML() {return html;}};
  };
  const querySelector = selector => {
    if (!store.has(selector)) store.set(selector,createElement());
    return store.get(selector);
  };
  return {querySelector, createElement, store, visibilityState:'visible',
    addEventListener(name, callback) {listeners.set(name, callback);}, listeners};
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

function loadRender(r, block = renderSource) {
  Object.assign(r.context, {lastMoonMin: -1, moonSky: {}, _starsProjected: true,
    fetchingTomorrow: true, _prayerStale: false, _moonStaleWarned: false,
    setLocLabel() {}, syncWeather() {}, renderMoon() {}, projectStars() {},
    fitCn() {}, drawArc: () => '<svg>fixture arc dependency</svg>', applyTheme() {},
    moonNow: () => ({phase: 0.5}), phaseEmoji: () => '◐', console});
  r.run(block);
  return r;
}

function loadLifecycle(r, block = lifecycle) {
  const calls={stars:0,weatherBuild:0,moon:0,weatherStart:0,cloud:0,requests:[],raf:0};
  const pending=new Map(); let rafId=0;
  Object.assign(r.context, {QA:false, MOTIONFULL:false, DEBUGMOTION:false,
    window:{}, lat:24, lon:39, label:'Fixture', _needsDetect:false, _cfgMode:'hardcoded',
    _loopStarted:false, lastDate:null, _prayerStale:false, _rolloverBusy:false,
    _rolloverNextTry:0, _ROLLOVER_RETRY_MS:60000, _cloudDirty:true,
    buildStars(){calls.stars++;}, buildWeather(){calls.weatherBuild++;},
    renderMoon(){calls.moon++;}, startWeather(){calls.weatherStart++;},
    loadCache:()=>null, saveCache(){}, fetchWeather(){}, fetchRadar(){},
    async fetchTimings(date) {calls.requests.push(date); return prayerRecord(date.split('-').reverse().join('-'),r.context.tz);},
    bindConfig(cfg){if(cfg.tz) r.context.tz=cfg.tz;}, isMotionReduced:()=>false,
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

module.exports = {sourcePath, source, sha256, slice, temporal, helpers, modelSource,
  renderSource, lifecycle, realm, countedIntl, prayerRecord, modelRealm, loadRender, loadLifecycle, loadSettingsAffordance};
