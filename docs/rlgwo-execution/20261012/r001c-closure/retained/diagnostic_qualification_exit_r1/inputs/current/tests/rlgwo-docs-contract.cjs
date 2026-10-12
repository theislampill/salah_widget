#!/usr/bin/env node
'use strict';
// No network or browser: execute the checked-in module/builder and diagnostic source.
// These assertions qualify disclosure/recipe contracts, not rendered pixels or motion.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const sourceOnly = process.argv.includes('--source-only');
const ref = process.argv.find(arg => arg.startsWith('--ref='))?.slice(6);
const scope = process.argv.find(arg => arg.startsWith('--scope='))?.slice(8);
assert(!scope || ['R001B', 'R001C'].includes(scope), 'scope must be R001B or R001C');
assert(!(scope && sourceOnly), 'owner scope includes its mandatory docs; source-only cannot narrow it');
const docsRoot = process.argv.find(arg => arg.startsWith('--docs-root='))?.slice(12);
const reusePath = process.argv.find(arg => arg.startsWith('--reuse-manifest='))?.slice(17);
const reuse = reusePath ? JSON.parse(fs.readFileSync(path.resolve(reusePath), 'utf8')) : null;
const digest = text => crypto.createHash('sha256').update(text).digest('hex');
const reuseNames = new Set([
  'source: exact M5V2T6 search recipients', 'source: London has no Canadian request or digit bias',
  'source: trimmed short query sends nothing', 'source: digit bias and prefix are actual triggers',
  'source caller: builder debounce and Enter', 'source caller: builder reverse coordinates and disabled controls',
  'source: coarse URLs and fallback', 'source: Reset key scope preserves unrelated caches',
  'source: complete fragment motion recipe and query negative'
]);
function ownerOf(name) {
  if (reuseNames.has(name)) return name.includes('fragment motion') ? 'R001C' : 'R001B';
  if (/^source: six real force|^docs: (?:AGENTS|DESIGN|OPTICS)|^recipe: (?:AGENTS|DESIGN|OPTICS)|^docs: DESIGN enum|^docs: diagnostic/.test(name)) return 'R001C';
  if (/^docs: README privacy|^docs: builder privacy|^docs mutant: removing a disclosed provider/.test(name)) return 'R001B';
  return 'OTHER';
}
const selectedLedger = [];
const docNames = ['README.md', 'AGENTS.md', 'DESIGN.md', 'OPTICS.md', 'ARCHITECTURE.md', 'HANDOFF.md'];
const sources = Object.fromEntries(['config.js', 'builder.html', 'index.html', ...docNames]
  .map(name => [name, docsRoot && docNames.includes(name) ? fs.readFileSync(path.join(path.resolve(docsRoot), name), 'utf8') : ref ? execFileSync('git', ['show', `${ref}:${name}`], { cwd: root, encoding: 'utf8', maxBuffer:32*1024*1024 }) : fs.readFileSync(path.join(root, name), 'utf8')]));
const results = [];
function requiredReuseBindings(name) {
  if (name === 'source: complete fragment motion recipe and query negative') {
    return { sources: [], helpers: ['parsed'], parser: true };
  }
  const builderCase = ['source caller: builder debounce and Enter',
    'source caller: builder reverse coordinates and disabled controls'].includes(name);
  return { sources: builderCase ? ['config.js', 'builder.html'] : ['config.js'],
    helpers: builderCase ? ['context', 'builder'] : ['context'], parser: false };
}
function requiredDigest(value, label) {
  assert(typeof value === 'string' && /^[a-f0-9]{64}$/.test(value), `${label}: required SHA-256 binding`);
}
function requiredDigestMap(map, keys, label) {
  assert(map && typeof map === 'object' && !Array.isArray(map), `${label}: required binding map`);
  assert.deepEqual(Object.keys(map).sort(), [...keys].sort(), `${label}: exact mandatory binding keys`);
  for (const key of keys) requiredDigest(map[key], `${label}/${key}`);
}
async function check(name, run) {
  const owner = ownerOf(name);
  if (scope && owner !== scope) { selectedLedger.push({name, owner, status:'NOT_SELECTED'}); return; }
  selectedLedger.push({name, owner, status:'SELECTED'});
  if (scope && reuseNames.has(name)) {
    try {
      assert(reuse?.schema === 'settings-docs-reuse/v1' && Array.isArray(reuse.cases), 'valid accepted reuse manifest required');
      assert(reuse.cases.every(row => row && typeof row === 'object' && !Array.isArray(row) && typeof row.name === 'string'), 'invalid reuse record');
      const matches = reuse.cases.filter(row => row.name === name);
      assert.equal(matches.length, 1, `${name}: one exact accepted reuse receipt required`);
      const row = matches[0], bindings = requiredReuseBindings(name);
      assert(row.status === 'PASS', `${name}: accepted PASS receipt required`);
      assert.equal(row.sourceRef, '18ff14860ff41c084b1db5f396bb62aa9c22b1be', 'accepted donor source identity required');
      assert.equal(row.receipt, 'https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/docs-contract-primary.json', 'accepted immutable receipt identity required');
      requiredDigest(row.callbackSha256, `${name}/callback`);
      assert.equal(digest(run.toString().replace(/\s+/g, ' ').trim()), row.callbackSha256, 'reused callback changed');
      if (bindings.sources.length || row.sourceSha256 !== undefined) requiredDigestMap(row.sourceSha256, bindings.sources, `${name}/source`);
      requiredDigestMap(row.helperSha256, bindings.helpers, `${name}/helper`);
      for (const file of bindings.sources) assert.equal(digest(sources[file]), row.sourceSha256[file], `reused ${file} changed`);
      for (const helper of bindings.helpers) assert.equal(digest(({context,builder,parsed})[helper].toString().replace(/\s+/g, ' ').trim()), row.helperSha256[helper], `reused ${helper} fixture inputs changed`);
      if (bindings.parser || row.parserSha256 !== undefined) {
        requiredDigest(row.parserSha256, `${name}/parser`);
        assert.equal(digest(qLine + '\n' + flags), row.parserSha256, 'reused parser declarations changed');
      }
      results.push({name,owner,status:'REUSED',receipt:row.receipt,sourceRef:row.sourceRef,bindingKeys:bindings});
    } catch(error) { results.push({name,owner,status:'FAIL',error:error.message}); }
    return;
  }
  try { await run(); results.push({ name, owner, status: 'PASS' }); }
  catch (error) { results.push({ name, owner, status: 'FAIL', error: error.message }); }
}
function region(source, start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, `source region missing: ${start}`);
  assert.equal(source.indexOf(start, a + start.length), -1, `ambiguous source region: ${start}`);
  return source.slice(a, b);
}
function context(extra = {}) {
  const timers = new Map(); let nextTimer = 0;
  const storage = new Map(); const requests = [];
  const ctx = vm.createContext({ URL, URLSearchParams, AbortController, console, Intl,
    setTimeout(fn, ms) { const id = ++nextTimer; timers.set(id, { fn, ms }); return id; },
    clearTimeout(id) { timers.delete(id); },
    localStorage: { getItem: k => storage.get(k) || null, setItem: (k, v) => storage.set(k, v), removeItem: k => storage.delete(k) },
    fetch: async url => {
      requests.push(String(url));
      const u = new URL(url); let body = {};
      if (u.hostname === 'get.geojs.io') body = { latitude: '51.5', longitude: '-0.12', city: 'London', country_code: 'GB' };
      if (u.hostname === 'nominatim.openstreetmap.org') body = [{ class: 'place', lat: '51.5', lon: '-0.12', address: { city: 'London', country_code: 'gb' } }];
      if (u.hostname === 'api.zippopotam.us') body = { places: [] };
      if (u.hostname === 'api.bigdatacloud.net') body = { city: 'London', countryCode: 'GB', continentCode: 'EU' };
      return { ok: true, json: async () => body };
    }, ...extra });
  ctx.window = ctx;
  vm.runInContext(sources['config.js'], ctx, { filename: 'config.js' });
  return { ctx, storage, requests, timers };
}
function builder() {
  const values = { label: 'Madinah', lat: '24.4672', lon: '39.6142', method: '4', school: '0', time: '24', units: 'f', dfcode: 'YYYY-MM-DD', datefmt: 'YYYY-MM-DD' };
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, { id, value: values[id] || '', style: {}, listeners: {}, attributes: {}, disabled: false, tabIndex: 0,
        classList: {
          add(...names) { names.forEach(name => classes.add(name)); },
          remove(...names) { names.forEach(name => classes.delete(name)); },
          contains(name) { return classes.has(name); },
          toggle(name, force = !classes.has(name)) { if (force) classes.add(name); else classes.delete(name); return force; }
        },
        setAttribute(name, value) { this.attributes[name] = String(value); if (name === 'tabindex') this.tabIndex = +value; },
        getAttribute(name) { return name === 'tabindex' ? String(this.tabIndex) : this.attributes[name] ?? null; },
        focus() { document.activeElement = this; }, select() {},
        addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); } });
    }
    return elements.get(id);
  }
  // Derive the radio members from the actual group markup; run its production listener.
  const scripts = [...sources['builder.html'].matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)].filter(m => !/\bsrc\s*=/.test(m[1]));
  assert.equal(scripts.length, 1, 'one production builder inline script');
  const modeIds = [...new Set([...scripts[0][2].matchAll(/\$\("(mode-[^"]+)"\)/g)].map(m => m[1]))];
  const groupMarkup = sources['builder.html'].match(/<div class="modebtns"[^>]*>([\s\S]*?)<\/div>/);
  const modeGroup = groupMarkup ? element('mode-group') : null, modeButtons = [];
  for (const match of groupMarkup?.[1].matchAll(/<button\b([^>]*)>/g) || []) {
    const attrs = Object.fromEntries([...match[1].matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
    if (!(attrs.class || '').split(/\s+/).includes('modebtn')) continue;
    const button = element(attrs.id);
    for (const [name, value] of Object.entries(attrs)) button.setAttribute(name, value);
    button.classList.add(...attrs.class.split(/\s+/)); button.disabled = /(?:^|\s)disabled(?:\s|$|=)/.test(match[1]);
    modeButtons.push(button);
  }
  // Missing required radios make this fixture inapplicable; ID lookup must not invent them.
  assert(modeGroup, 'fixture applicability: missing .modebtns markup');
  assert(modeIds.length, 'fixture applicability: production radio ID lookups unavailable');
  for (const id of modeIds) assert(modeButtons.some(button => button.id === id), `fixture applicability: missing required radio ${id}`);
  if (modeGroup) modeGroup.querySelectorAll = selector => selector === '.modebtn' ? modeButtons : [];
  const document = { activeElement: null,
    getElementById: id => modeIds.includes(id) ? modeButtons.find(button => button.id === id) || null : element(id),
    querySelector: selector => selector === '.modebtns' ? modeGroup : null };
  const env = context({ document, navigator: { language: 'en-CA', platform: 'Win32' },
    location: { href: 'https://example.invalid/builder.html' } });
  vm.runInContext(scripts[0][2], env.ctx, { filename: 'builder.html:inline' });
  return { ...env, elements, element,
    dispatch(id, type, event = {}) { for (const fn of element(id).listeners[type] || []) fn({ key: '', preventDefault() {}, ...event }); } };
}
const settled = () => new Promise(resolve => setImmediate(resolve));
const qLine = sources['index.html'].match(/^const q\s*=.*;$/m)?.[0];
assert(qLine, 'production q declaration present');
const flags = ['DEBUGMOTION', 'MOTIONFULL', 'DEBUGOPTIC', 'DEBUGLAYERS', 'DEBUGMOON'].map(name => {
  const line = sources['index.html'].match(new RegExp(`^const ${name}\\s*=.*$`, 'm'))?.[0];
  assert(line, `production ${name} declaration present`); return line;
}).join('\n');
function parsed(recipe) {
  const u = new URL(recipe, 'https://example.invalid/');
  return vm.runInNewContext(`${qLine}\n${flags}\n({q, DEBUGMOTION, MOTIONFULL, DEBUGOPTIC, DEBUGLAYERS, DEBUGMOON})`, { location: u, URLSearchParams });
}
const forceBlock = region(sources['index.html'], '  if(DEBUGOPTIC===', '\n  const pillarCol');
const forceNames = [...forceBlock.matchAll(/DEBUGOPTIC\s*===\s*"([a-z]+)"/g)].map(m => m[1]);
const claimedNames = ['halo', 'sundogs', 'pillar', 'anticrep', 'paraselene', 'lunarhalo'];
const base = 'index.html#lat=24.47&lon=39.61&label=Madinah&method=4';
// Preserve the original published-baseline replay; new composed contracts require their actual source.
const historicalBaseline = ref === 'fd2972ba64225fe9d6848e92497e6d0ed20ea624';
const prose = name => sources[name].replace(/\s+/g, ' ');
function mentions(name, tokens) {
  for (const token of tokens) assert(prose(name).includes(token), `${name}: missing contract ${token}`);
}

(async () => {
  await check('source: exact M5V2T6 search recipients', async () => {
    const e = context(); await e.ctx.SalahConfig.geocodeSearch('M5V2T6', {});
    assert.deepEqual(e.requests, ['https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=5&q=M5V2T6', 'https://api.zippopotam.us/ca/M5V']);
  });
  await check('source: London has no Canadian request or digit bias', async () => {
    const e = context(); await e.ctx.SalahConfig.geocodeSearch('London', { homeCC: 'ca' });
    assert.equal(e.requests.length, 1); assert.equal(new URL(e.requests[0]).searchParams.get('q'), 'London');
    assert.equal(new URL(e.requests[0]).searchParams.get('countrycodes'), null);
  });
  await check('source: trimmed short query sends nothing', async () => {
    const e = context(); await e.ctx.SalahConfig.geocodeSearch(' X ', {}); await e.ctx.SalahConfig.geocodeSearch(' ', {});
    assert.deepEqual(e.requests, []);
  });
  await check('source: digit bias and prefix are actual triggers', async () => {
    const e = context(); await e.ctx.SalahConfig.geocodeSearch('10 Downing', { homeCC: 'gb' });
    assert.equal(new URL(e.requests[0]).searchParams.get('countrycodes'), 'gb');
    e.requests.length = 0; await e.ctx.SalahConfig.geocodeSearch('m 5 v-not-a-valid-postcode', {});
    assert.equal(e.requests[1], 'https://api.zippopotam.us/ca/M5V');
  });
  await check('source caller: builder debounce and Enter', async () => {
    const e = builder(); await settled(); e.requests.length = 0;
    e.element('label').value = 'M5V2T6'; e.dispatch('label', 'input');
    assert.equal(e.requests.length, 0);
    const timer = [...e.timers.values()].find(t => t.ms === 1000); assert(timer, 'production debounce scheduled');
    await timer.fn(); assert.equal(e.requests.length, 2);
    e.requests.length = 0; e.element('label').value = 'London'; e.dispatch('label', 'keydown', { key: 'Enter' }); await settled();
    assert.equal(e.requests.length, 1); assert.equal(new URL(e.requests[0]).searchParams.get('q'), 'London');
  });
  await check('source caller: builder reverse coordinates and disabled controls', async () => {
    const e = builder(); await settled(); e.requests.length = 0;
    e.element('lat').value = '51.5'; e.element('lon').value = '-0.12';
    vm.runInContext('labelAuto = true; methodAuto = true;', e.ctx);
    await vm.runInContext('fillNameFromCoords()', e.ctx);
    assert.deepEqual(e.requests, ['https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=51.5&longitude=-0.12&localityLanguage=en']);
    e.requests.length = 0; vm.runInContext('labelAuto = false; methodAuto = false;', e.ctx);
    await vm.runInContext('fillNameFromCoords()', e.ctx); assert.deepEqual(e.requests, []);
    vm.runInContext('labelAuto = true;', e.ctx); e.element('lat').value = '';
    await vm.runInContext('fillNameFromCoords()', e.ctx); assert.deepEqual(e.requests, []);
  });
  await check('source: coarse URLs and fallback', async () => {
    const e = context(); await e.ctx.SalahConfig.coarseDetect();
    assert.deepEqual(e.requests, ['https://get.geojs.io/v1/ip/geo.json']);
    e.requests.length = 0; e.ctx.fetch = async url => {
      e.requests.push(url); if (url.includes('geojs')) throw Error('controlled primary failure');
      return { ok: true, json: async () => ({ loc: '51.5,-0.12', city: 'London', country: 'GB' }) };
    };
    const result = await e.ctx.SalahConfig.coarseDetect(); assert(result.ok);
    assert.deepEqual(e.requests, ['https://get.geojs.io/v1/ip/geo.json', 'https://ipinfo.io/json']);
  });
  await check('source: Reset key scope preserves unrelated caches', () => {
    const e = context(); for (const k of ['salah_widget:config:v1', 'salah:fixture', 'salahwx:fixture']) e.storage.set(k, '{}');
    assert(e.ctx.SalahConfig.clearLocal().ok); assert(!e.storage.has('salah_widget:config:v1'));
    assert(e.storage.has('salah:fixture') && e.storage.has('salahwx:fixture'));
  });
  await check('source: complete fragment motion recipe and query negative', () => {
    assert.equal(parsed(`${base}&debugMotion=1`).DEBUGMOTION, true);
    assert.equal(parsed(`${base}&debugMotion=1&motion=full`).MOTIONFULL, true);
    const negative = parsed('index.html?debugMotion=1&motion=full#lat=24.47&lon=39.61');
    assert.equal(negative.DEBUGMOTION, false); assert.equal(negative.MOTIONFULL, false);
    assert.throws(() => assert.equal(negative.DEBUGMOTION, true), 'moved flag mutant must fail');
  });
  await check('source: six real force branches and unsupported-string mutant', () => {
    assert.deepEqual(forceNames, claimedNames);
    const source = sources['index.html'];
    let clampLine = source.match(/^const clamp\s*=.*$/m)?.[0]; assert(clampLine, 'production clamp present');
    let eligibility = '';
    if (source.includes('function nativeLunarPresentation(')) {
      // Bind the exact current delegated owner; embedded first-paint helpers
      // are separate lexical owners. Script ordinal alone grants no authority.
      const wrapper = "function lunarPresentation(solarElevation){ return nativeLunarPresentation(moonSky,solarElevation,_pbrFailed); }";
      const scripts = [...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
      const owners = scripts.filter(match => match[2].includes(wrapper));
      assert.equal(owners.length,1,'unique delegated lunar script owner required');
      const [_,attrs,body] = owners[0];
      assert.equal(attrs,"",'delegated owner script role changed');
      const signature = "function nativeLunarPresentation(moon,solarElevation,surfaceFailed){";
      assert.equal([...body.matchAll(/^function nativeLunarPresentation\(/gm)].length,1,'unique delegated lunar helper required');
      assert.equal([...body.matchAll(/^function lunarPresentation\(/gm)].length,1,'unique delegated lunar wrapper required');
      const helper = region(body,signature,'\n}') + '\n}';
      assert.equal(digest(helper),"9b7d34b9b20517da2027f424db17f223d8f08e719518221a23439109d11b5f5e",'delegated lunar helper changed');
      const clamps = [...body.matchAll(/^const clamp\s*=.*$/gm)].map(match => match[0]);
      assert.equal(clamps.length,1,'unique delegated widget clamp required');
      assert.equal(digest(clamps[0]),"3996c2802e4d300d16f9cbffc98d15f9b14467f8d2068ae9d24ae8179e34fb8c",'delegated widget clamp changed');
      const calls = [...body.matchAll(/^  const \{mFrac,.*\}=lunarPresentation\(sm.altDeg\);$/gm)].map(match => match[0]);
      assert.equal(calls.length,1,'unique delegated atmosphere lunar call required');
      assert.equal(digest(calls[0]),"9fc8a550af80cf2ff526fcf69d40c4d9863135f551c97386e6ff65bce799d46f",'delegated atmosphere lunar call changed');
      assert.equal(digest(body),"5855c29ae0496734b791ded1e1f62939d8605d253ab836cea66a5bf122770ab7",'delegated native script changed');
      assert.equal(digest(source),"c773af444ed1071f9ba6b62b8e635c8d38b1b7f73de995c781ed23c0d307499a",'delegated current generated entry changed');
      clampLine = clamps[0];
      eligibility = helper + '\n' + wrapper + '\n' + calls[0];
    } else if (source.includes('function lunarPresentation(')) {
      // PR43 moved the semantic owner into this unique production function.
      const functionStart=source.match(/^function lunarPresentation\([^)]*\)\{$/m)?.[0];
      assert(functionStart, 'unique production lunarPresentation signature required');
      eligibility = region(source, functionStart, '\n}') + '\n}';
      const call = source.match(/^  const \{mFrac,.*\}=lunarPresentation\(sm.altDeg\);$/m)?.[0];
      assert(call, 'actual atmosphere lunarPresentation call required');
      eligibility += '\n' + call;
    } else if (/^\s*const moonLightEligible\s*=/m.test(source)) {
      const start = source.match(/^  const mFrac=clamp\(moonSky.frac\)[,;]/m)?.[0];
      assert(start, 'production inline lunar eligibility start required');
      eligibility = region(source, start, '\n  const moonLightReason');
    }
    const forced = (name, moonSky={frac:0.98,alt:20}, sm={altDeg:-18}, pbrFailed=false) => vm.runInNewContext(
      `${clampLine}\n${eligibility}\nlet sunHalo=0,sunDogs=0,sunPillar=0,antiCrep=0,moonParhelia=0,lunarHalo=0;\n${forceBlock}\n[sunHalo,sunDogs,sunPillar,antiCrep,moonParhelia,lunarHalo]`,
      {DEBUGOPTIC:name, moonSky, sm, _pbrFailed:pbrFailed});
    for (const [index,name] of forceNames.entries()) {
      const flags = parsed(`${base}&simTime=12:30&debugOptic=${name}`); assert.equal(flags.DEBUGOPTIC,name);
      const expected = [0,0,0,0,0,0]; expected[index]=[0.95,0.95,0.9,0.8,0.9,0.95][index];
      const state = Array.from(forced(name)); assert.deepEqual(state,expected, `${name} exact actual force output`);
      selectedLedger.push({owner:'R001C',kind:'force',name,state,context:{moonSky:{frac:0.98,alt:20},sm:{altDeg:-18},_pbrFailed:false}});
    }
    if (eligibility) for (const name of ['paraselene','lunarhalo']) {
      for (const [reason,moonSky,sm,pbrFailed] of [
        ['near-new',{frac:0.01,alt:20},{altDeg:-18},false],
        ['phase cutoff',{frac:0.02,alt:20},{altDeg:-18},false],
        ['below-horizon',{frac:0.98,alt:-10},{altDeg:-18},false],
        ['daylight',{frac:0.98,alt:20},{altDeg:20},false],
        ['surface-unavailable',{frac:0.98,alt:20},{altDeg:-18},true]
      ]) {
        const state=Array.from(forced(name,moonSky,sm,pbrFailed));
        assert(state.every(x=>x===0),`${name} must preserve ${reason} ineligibility`);
        selectedLedger.push({owner:'R001C',kind:'force-boundary',name,reason,state,context:{moonSky,sm,_pbrFailed:pbrFailed}});
      }
    }
    assert.equal(parsed(`${base}&debugOptic=corona`).DEBUGOPTIC,'corona');
    assert(!forceNames.includes('corona'));
    const corona=Array.from(forced('corona')); assert(corona.every(x=>x===0),'unsupported corona has no forced output');
    selectedLedger.push({owner:'R001C',kind:'force-negative',name:'corona',state:corona});
    assert.throws(()=>assert.deepEqual([...claimedNames,'corona'],forceNames),'unsupported enum mutant must fail');
  });
  if (!historicalBaseline) {
    await check('source: actual appearance exports, saved precedence and private fix age', async () => {
      let stamp = 1788880200000;
      class FixtureDate extends Date { static now() { return stamp; } }
      const e = context({ Date: FixtureDate }), api = e.ctx.SalahConfig;
      assert.equal(api.normalize({}).appearance, 'glass');
      assert.equal(api.normalize({ appearance: 'legacy' }).appearance, 'glass');
      const evidence = api.browserLocationEvidence({ coords: { accuracy: 25 }, timestamp: stamp - 300000 });
      const cfg = api.normalize({ lat: 24.47, lon: 39.61, source: 'browser-geolocation', locationEvidence: evidence, appearance: 'contrast' });
      assert(api.saveLocal(cfg).ok); stamp += 86400000;
      const saved = api.loadLocal(); assert.equal(saved.locationEvidence.accuracyM, 25);
      assert.equal(saved.locationEvidence.acquiredAt, 1788879900000);
      assert(api.saveLocal({ ...saved, units: 'c' }).ok);
      assert.equal(api.loadLocal().locationEvidence.acquiredAt, 1788879900000);
      assert.equal(api.resolve('#local=1&appearance=glass').cfg.appearance, 'contrast');
      const portable = api.serialize(cfg, { explicitPrefs: ['appearance'] });
      assert.equal(api.normalize({ ...api.parseHash(portable).cfg, source: 'hash' }).locationEvidence.intent, 'fixed-site');
      for (const key of ['locationEvidence', 'accuracyM', 'acquiredAt', 'savedAt']) assert(!new URLSearchParams(portable).has(key));
      const appearanceMarkup = sources['builder.html'].match(/<select\b[^>]*\bid="appearance"[^>]*>([\s\S]*?)<\/select>/)?.[1];
      assert(appearanceMarkup, 'fixture applicability: actual appearance select required');
      assert.deepEqual([...appearanceMarkup.matchAll(/<option\b[^>]*\bvalue="([^"]+)"/g)].map(m => m[1]), ['glass', 'contrast']);
      const b = builder(); await settled(); b.element('appearance').value = 'glass';
      for (const mode of ['portable', 'local']) {
        vm.runInContext(`setMode('${mode}')`, b.ctx);
        const params = new URLSearchParams(vm.runInContext('hash()', b.ctx));
        assert.equal(params.get('appearance'), 'glass', `actual ${mode} builder explicitly carries default glass`);
        if (mode === 'local') { assert(!params.has('lat')); assert(params.has('method') && params.has('units')); }
      }
    });
    await check('source: default wall correction versus explicit anchored one-times preview', () => {
      const temporal = region(sources['index.html'], 'const _RAFNOW', '\nfunction simDate');
      for (const scale of [null, '1']) {
        let wall = 1788880200000, elapsed = 0;
        class FixtureDate extends Date { static now() { return wall; } }
        const q = new URLSearchParams(scale === null ? '' : 'timeScale=1');
        const read = vm.runInNewContext(`${temporal}\n({now:simNow,wall:FOLLOW_WALL_CLOCK,advancing:ADVANCING})`,
          { Date: FixtureDate, performance: { now: () => elapsed }, q, SIM: { time: null }, tz: 'UTC', Intl });
        assert.equal(read.now(), wall); assert.equal(read.wall, scale === null); assert.equal(read.advancing, scale !== null);
        wall += 3600000; elapsed += 1000;
        assert.equal(read.now(), scale === null ? wall : 1788880201000);
        wall -= 7200000; elapsed += 1000;
        assert.equal(read.now(), scale === null ? wall : 1788880202000);
      }
    });
    await check('source: actual model-live negative and admitted synthetic wet, expiry and outage', () => {
      const source = sources['index.html'];
      const number = source.match(/^function wxNumber.*$/m)?.[0];
      const same = source.match(/^function weatherTargetSame.*$/m)?.[0];
      assert(number && same, 'fixture applicability: actual weather primitives required');
      const functions = region(source, 'const _WX_PRESENT_TTL', '\nfunction weatherDecision');
      const api = vm.runInNewContext(`${region(source, 'function usableWeatherCoordinates', '\nfunction wxNumber')}\n${number}\n${same}\n${functions}\n({admit:admitWeatherFixture,reconcile:reconcileWeatherEvidence})`);
      const now = 1788880200000, target = { generation: 3, lat: 24.47, lon: 39.61, intent: 'fixed-site', source: 'hash' };
      const raw = { scope: 'simulation-fixture', provider: 'Synthetic QA', product: 'present/nearby contract', policy: 'synthetic-present-v1', target,
        measurementAt: now - 60000, retrievedAt: now, validFrom: now - 60000, validUntil: now + 60000, units: 'categorical',
        quality: { status: 'qualified', sampling: 'direct', operationalHealth: 'operational', localObservationAt: now - 60000 },
        footprint: { kind: 'point', coverage: 'target', lat: target.lat, lon: target.lon }, present: { state: 'wet', type: 'rain', lightning: 'not-observed' } };
      const admitted = api.admit(raw, target, now); assert(admitted.ok, admitted.reason);
      const model = { src: 'current', code: 0, precip: 0, currentIntervalSec: 900, currentValidAt: now, retrievedAt: now, trusted: true };
      const inputs = { target, model, modelCategory: 'clear', present: admitted.evidence };
      const live = api.reconcile({ ...inputs, lane: 'live' }, now);
      assert.equal(live.present.available, false); assert.equal(live.spatial.state, 'unavailable');
      assert.equal(live.horizon.arrival, null); assert(!live.permissions.rain && !live.permissions.snow && !live.permissions.lightning);
      const wet = api.reconcile({ ...inputs, lane: 'simulation-fixture' }, now);
      assert.equal(wet.current, 'supported-wet'); assert.equal(wet.disagreement, true); assert.equal(wet.permissions.rain, true);
      assert.equal(api.reconcile({ ...inputs, lane: 'simulation-fixture' }, raw.validUntil).permissions.rain, false);
      const outage = api.admit(null, target, now); assert.equal(outage.ok, false);
      assert.equal(api.reconcile({ ...inputs, present: null, presentRejection: outage.reason, lane: 'simulation-fixture' }, now).permissions.rain, false);
      // A current/forecast preview does not become an explicitly synthetic strike scene.
      for (const src of ['current', 'forecast']) {
        const preview = api.reconcile({ ...inputs, model: { ...model, src, precip: 5 }, modelCategory: 'thunder', lane: 'preview' }, now);
        assert.equal(preview.permissions.rain, true); assert.equal(preview.permissions.lightning, false);
      }
      const syntheticPreview = api.reconcile({ ...inputs, model: { ...model, src: 'sim', precip: 5 }, modelCategory: 'thunder', lane: 'preview' }, now);
      assert.equal(syntheticPreview.permissions.rain, true); assert.equal(syntheticPreview.permissions.lightning, true);
      const unknownModel = api.reconcile({ ...inputs, model: null, lane: 'simulation-fixture' }, now);
      assert.equal(unknownModel.current, 'supported-wet'); assert.equal(unknownModel.model.state, 'unknown');
      // No supported model comparison: false is not an agreement or observation claim.
      assert.equal(unknownModel.disagreement, false);
    });
  }
  if (!sourceOnly) {
    await check('docs: README privacy names actual recipients and trigger fields', () => {
      const privacy = region(sources['README.md'], '### Auto-detect, precise location & privacy', '\n---');
      for (const token of ['GeoJS', 'ipinfo.io', 'Nominatim', 'Zippopotam', 'BigDataCloud', 'Aladhan', 'Open-Meteo', 'RainViewer', 'Google Fonts', 'countrycodes', 'localityLanguage', 'Reset', 'retention']) assert(privacy.includes(token), `privacy missing ${token}`);
      assert(!sources['README.md'].includes('no tracking'), 'remove unsupported blanket claim');
      assert(!privacy.includes('stores nothing about you on any server'));
    });
    await check('docs: README privacy complete eight-group field contract', () => {
      const privacy = region(sources['README.md'], '### Auto-detect, precise location & privacy', '\n---');
      const rows = privacy.split('\n').filter(line=>/^\| (?:Approximate area detection|Place\/postcode search|Canadian-style prefix assist|Builder coordinate reverse lookup|Prayer requests|Weather requests|Radar evidence requests|Font loading) \|/.test(line));
      assert.equal(rows.length,8,'exact eight request groups');
      const expected=[['get.geojs.io/v1/ip/geo.json','ipinfo.io/json','Intl'],['Nominatim','format=jsonv2','addressdetails=1','limit=5','countrycodes'],['Zippopotam','M5V2T6','/ca/M5V','prefix'],['BigDataCloud','700 ms','latitude','longitude','localityLanguage=en'],['Aladhan','timings/<date>','latitude','longitude','method','school'],['Open-Meteo','temperature_unit','wind_speed_unit=ms','forecast_days=3'],['RainViewer','/256/<z>/<x>/<y>/2/1_1.png','coordinates'],['Google Fonts','fonts.googleapis.com','fonts.gstatic.com']];
      for(const [index,tokens] of expected.entries())for(const token of tokens)assert(rows[index].includes(token),`request group ${index+1}: missing ${token}`);
      for(const fields of [
        'current=temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,is_day,weather_code,precipitation,rain,showers,snowfall',
        'hourly=temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,weather_code,visibility,is_day'
      ])assert(privacy.includes(fields),'complete exact selected weather fields');
      for(const token of ['retention','salah_widget:config:v1','prayer/weather caches','provider','700 ms','one-second','shorter than 2'])assert(privacy.includes(token),`privacy missing ${token}`);
    });
    await check('docs: README privacy whole-document storage consistency', () => {
      const readme = sources['README.md'];
      assert(!/stores nothing about you|does no tracking|no tracking/i.test(readme), 'whole README retains an unsupported blanket privacy claim');
      assert(readme.includes("Saved configuration uses this browser's storage."), 'keep local-storage disclosure');
      assert(readme.includes('Provider retention or handling is not established by this widget-source description.'), 'keep provider-policy uncertainty');
      assert(readme.includes('salah_widget:config:v1') && readme.includes('does not erase prayer/weather caches or data held by external providers'), 'keep exact Reset scope');
    });
    if (!sourceOnly) for (const name of ['AGENTS.md','DESIGN.md','OPTICS.md']) await check(`docs: diagnostic complete recipes and caveats: ${name}`, () => {
      const doc=sources[name];
      for(const recipe of [base+'&debugMotion=1',base+'&debugMotion=1&motion=full',base+'&simTime=12:30&debugOptic=halo'])assert(doc.split('\n').includes(recipe),`${name}: missing complete ${recipe}`);
      assert(doc.includes('simTime without timeScale freezes the clock-driven scene.'));
      assert(doc.includes('Flag activation alone does not prove visible motion or correct optical pixels.'));
      for(const token of ['halo, sundogs, pillar, anticrep, paraselene and lunarhalo','Corona, earthshine, refraction and the crepuscular ray','query-only ?debugMotion=1 is not read'])assert(doc.includes(token),`${name}: missing ${token}`);
    });
    await check('docs: builder privacy recipients, details link and host guidance', () => {
      const note = sources['builder.html'].match(/<p class="note"><strong>Self-configuring embeds &amp; privacy:<\/strong>[\s\S]*?<\/p>/)?.[0];
      assert(note, 'existing privacy paragraph');
      for (const token of ['GeoJS', 'ipinfo.io', 'Nominatim', 'Zippopotam', 'BigDataCloud', 'coordinates', 'allow="geolocation"', 'coarse', 'manual', 'Request details', '#auto-detect-precise-location--privacy']) assert(note.includes(token), `builder privacy missing ${token}`);
      assert(!note.includes('does no tracking'));
    });
    for (const name of docNames.filter(n => n !== 'README.md')) {
      const doc = sources[name];
      await check(`docs: ${name} no positive query-only diagnostic recipe`, () => {
        // Only this exact committed history paragraph is exempt, at its own offsets.
        const historyStart = name === 'HANDOFF.md' ? doc.indexOf('What changed in the (committed `91d0fc1`) live-motion pass') : -1;
        const historyEnd = historyStart < 0 ? -1 : doc.indexOf('\n- **Sun:**', historyStart);
        if (name === 'HANDOFF.md') {
          assert(historyStart >= 0 && historyEnd > historyStart, 'pinned HANDOFF history context required');
          assert.equal(doc.indexOf('What changed in the (committed `91d0fc1`) live-motion pass', historyStart + 1), -1, 'unique historical context required');
          assert.equal(digest(doc.slice(historyStart, historyEnd)), '7578c304b266ee6bb7b9cd49f46e6736edd69da97315a65b60a746156aa33694', 'historical context changed');
        }
        let offset = 0;
        for (const [index, line] of doc.split('\n').entries()) {
          const pinnedHistory = historyStart >= 0 && offset >= historyStart && offset < historyEnd;
          if (/\?(?:debugMotion|debugOptic|debugLayers|debugMoon|motion)=/.test(line)) assert(pinnedHistory || ((name !== 'ARCHITECTURE.md' && name !== 'HANDOFF.md') && (/query-only.*not read/.test(line) || /Query-only negative control:.*not read/.test(doc.split('\n').slice(Math.max(0,index-4),index).join(' ')))), `${name}:${index + 1}: ${line.trim()}`);
          offset += line.length + 1;
        }
      });
      for (const [index, line] of doc.split('\n').entries()) {
        const recipes = [...line.matchAll(/`([^`]*(?:&debugMotion=1|&motion=full|&debugOptic=[a-z]+|&debugLayers=1|&debugMoon=1)[^`]*)`/g)].map(m => m[1]);
        if (/^index\.html[?#]/.test(line) && !/Query-only negative control:.*not read/.test(doc.split('\n').slice(Math.max(0,index-4),index).join(' '))) recipes.push(line.trim());
        for (const recipe of recipes) await check(`recipe: ${name}:${index + 1}: ${recipe}`, () => {
          const actual = parsed(recipe.startsWith('&') ? base + recipe : recipe);
          selectedLedger.push({owner:ownerOf(`recipe: ${name}`),kind:'literal',file:name,line:index+1,recipe,hash:actual.q.toString(),flags:{DEBUGMOTION:actual.DEBUGMOTION,MOTIONFULL:actual.MOTIONFULL,DEBUGOPTIC:actual.DEBUGOPTIC,DEBUGLAYERS:actual.DEBUGLAYERS,DEBUGMOON:actual.DEBUGMOON}});
          if (recipe.includes('debugMotion=1')) assert.equal(actual.DEBUGMOTION, true);
          if (recipe.includes('motion=full')) assert.equal(actual.MOTIONFULL, true);
          if (recipe.includes('debugLayers=1')) assert.equal(actual.DEBUGLAYERS, true);
          if (recipe.includes('debugMoon=1')) assert.equal(actual.DEBUGMOON, true);
          const optic = recipe.match(/debugOptic=([a-z]+)/)?.[1];
          if (optic) { assert.equal(actual.DEBUGOPTIC, optic); assert(forceNames.includes(optic), `unsupported force ${optic}`); }
        });
      }
    }
    await check('docs: DESIGN enum matches executed force branches', () => {
      const enumText = sources['DESIGN.md'].match(/`debugOptic=([a-z|]+)`/)?.[1]; assert(enumText, 'documented enum');
      assert.deepEqual(enumText.split('|'), forceNames);
      assert(!/Each can be forced|force each via/.test(sources['DESIGN.md']), 'no blanket force claim');
      for (const name of ['Corona', 'earthshine', 'refraction', 'crepuscular ray']) assert(sources['DESIGN.md'].includes(name), `physical-only explanation missing ${name}`);
      assert(sources['DESIGN.md'].includes('Flag activation alone does not prove visible motion or correct optical pixels.'));
      assert(sources['DESIGN.md'].includes('simTime without timeScale freezes the clock-driven scene.'));
    });
    await check('docs mutant: removing a disclosed provider is detected', () => {
      const privacy = region(sources['README.md'], '### Auto-detect, precise location & privacy', '\n---');
      assert(privacy.includes('Nominatim'), 'positive disclosure control must exist before mutation');
      assert.throws(() => assert(privacy.replaceAll('Nominatim', 'withheld').includes('Nominatim')));
    });
    if (!historicalBaseline) {
      await check('docs composed: useful model estimate without local observation or arrival', () => {
        mentions('README.md', ['Open-Meteo CURRENT MODEL ESTIMATE', 'local precipitation', 'nearby', 'arrival']);
        const weather = region(sources['DESIGN.md'], '### Weather truthfulness (critical)', '\n## Star').replace(/\s+/g, ' ');
        // Exclude exactly the retained sentence that explicitly supersedes the old policy.
        // Positive or duplicate observation claims elsewhere still fail this oracle.
        const superseded = "The owner's PR42 policy supersedes both the old observed/nowcast wording and the later policy that suppressed all model precipitation when no observation adapter was connected.";
        const active = weather.replace(superseded, '');
        assert(!/observed\/nowcast|max\(Open-Meteo nowcast|INDEPENDENT observed-precip sensor/.test(active), 'model/radar must not acquire observed authority');
        mentions('DESIGN.md', ['current MODEL ESTIMATE, not a direct local observation', 'Supported current-model quantities', 'visualPermissions', 'distinct from observed-present', 'Thunder codes do not authorize observed strikes', 'Hourly forecasts remain forecast/preview data', 'RainViewer palette alpha is unitless']);
      });
      await check('docs composed: current and forecast quantity windows retain unavailable metadata', () => {
        mentions('DESIGN.md', ['preceding-interval-amount', 'preceding-hour-amount', 'instantaneous', 'probability', 'unavailable', 'issuedAt', 'probabilityEvent']);
        const source = sources['index.html'];
        const number = source.match(/^function wxNumber.*$/m)?.[0], same = source.match(/^function weatherTargetSame.*$/m)?.[0];
        assert(number && same, 'fixture applicability: actual weather primitives required');
        const api = vm.runInNewContext(`${region(source, 'function usableWeatherCoordinates', '\nfunction wxNumber')}\n${number}\n${same}\n${region(source, 'const _WX_PRESENT_TTL', '\nfunction weatherDecision')}\n({reconcile:reconcileWeatherEvidence,forecast:weatherForecast})`);
        const now = 1788880200000, target = { generation:3,lat:24.47,lon:39.61,intent:'fixed-site',source:'hash' };
        const model = {src:'current',code:63,precip:2,currentIntervalSec:900,currentValidAt:now,retrievedAt:now};
        const quantity = api.reconcile({target,model,modelCategory:'rain',lane:'live'},now).model.quantity;
        const documentedWindows = [...prose('DESIGN.md').matchAll(/The current `preceding-interval-amount` covers `currentValidAt` minus `currentIntervalSec \* ([0-9]+)` through `currentValidAt` \(epoch milliseconds\)/g)];
        assert.equal(documentedWindows.length,1,'one documented current quantity window in epoch milliseconds required');
        assert.equal(quantity.from,model.currentValidAt-model.currentIntervalSec*Number(documentedWindows[0][1]),'documented current interval conversion must match actual source window');
        assert.equal(quantity.kind,'preceding-interval-amount'); assert.equal(quantity.value,2); assert.equal(quantity.units,'mm');
        assert.equal(quantity.from,now-900000); assert.equal(quantity.to,now); assert.equal(quantity.averageRateMmH,8); assert.equal(quantity.instantaneous,false);
        const track = {target,retrievedAt:now,provider:'Open-Meteo',product:'hourly forecast',ep:[now,now+3600000],precipitation:[0,1],weather_code:[0,63]};
        const forecast = api.forecast(track,target,now);
        assert.equal(forecast.validFrom,now); assert.equal(forecast.validUntil,now+3600000); assert.equal(forecast.amount.kind,'preceding-hour-amount');
        assert.equal(forecast.amount.value,1); assert.equal(forecast.amount.units,'mm');
        assert.equal(forecast.issuedAt,null); assert.equal(forecast.probability,null); assert.equal(forecast.probabilityEvent,null);
        assert.equal(forecast.resolution,'native/interpolated provenance unavailable');
        assert.equal(api.forecast({...track,precipitation:[0,null]},target,now).amount.value,null);
        assert.equal(api.forecast({...track,precipitation:[0,0]},target,now).amount.value,0);
        assert.equal(api.forecast({...track,target:{...target,generation:4}},target,now),null);
      });
      await check('docs composed: admitted synthetic lane and immediate withdrawal stay separate', () => {
        mentions('DESIGN.md', ['synthetic-present-v1', 'exclusive to the explicit simulation-fixture lane', 'underlying', 'outage', 'generation', 'trusted:true', 'current-model visualPermissions']);
        const source = sources['index.html'];
        const number = source.match(/^function wxNumber.*$/m)?.[0], same = source.match(/^function weatherTargetSame.*$/m)?.[0];
        assert(number && same, 'fixture applicability: actual weather primitives required');
        const api = vm.runInNewContext(`${region(source, 'function usableWeatherCoordinates', '\nfunction wxNumber')}\n${number}\n${same}\n${region(source, 'const _WX_PRESENT_TTL', '\nfunction weatherDecision')}\n({admit:admitWeatherFixture,reconcile:reconcileWeatherEvidence})`);
        const now=1788880200000,target={generation:3,lat:24.47,lon:39.61,intent:'fixed-site',source:'hash'};
        const raw={scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',target,
          measurementAt:now-60000,retrievedAt:now,validFrom:now-60000,validUntil:now+60000,units:'categorical',
          quality:{status:'qualified',sampling:'direct',operationalHealth:'operational',localObservationAt:now-60000},
          footprint:{kind:'point',coverage:'target',lat:target.lat,lon:target.lon},present:{state:'wet',type:'rain',lightning:'not-observed'}};
        const accepted=api.admit(raw,target,now); assert.equal(accepted.ok,true);
        for(const altered of [{...raw,scope:'live',trusted:true},{...raw,provider:'RainViewer',trusted:true},{...raw,policy:'synthetic-present-v2'},
          {...raw,target:{...target,generation:4}},{...raw,validUntil:now},{...raw,quality:{...raw.quality,operationalHealth:'outage'}}])
          assert.equal(api.admit(altered,target,now).ok,false);
        const model={src:'current',code:0,precip:0,currentIntervalSec:900,currentValidAt:now,retrievedAt:now};
        const input={target,model,modelCategory:'clear',present:accepted.evidence};
        assert.equal(api.reconcile({...input,lane:'simulation-fixture'},now).permissions.rain,true);
        const live=api.reconcile({...input,lane:'live'},now); assert.equal(live.present.available,false); assert.equal(live.permissions.rain,false);
        assert.equal(api.reconcile({...input,lane:'simulation-fixture'},raw.validUntil).permissions.rain,false);
        const outage=api.admit(null,target,now); assert.equal(outage.ok,false);
        assert.equal(api.reconcile({...input,present:null,presentRejection:outage.reason,lane:'simulation-fixture'},now).permissions.rain,false);
      });
      await check('docs composed: fix acquisition age and portable privacy survive saving', () => {
        mentions('README.md', ['acquisition', 'Saving settings does not renew', 'Portable', 'partition']);
        mentions('DESIGN.md', ['locationEvidence', 'accuracyM', 'acquiredAt', 'savedAt', 'fixed-site']);
        assert(!/precise GPS|stores nothing about you/.test(sources['README.md']), 'unsupported precision/privacy claim');
      });
      await check('docs composed: ordinary wall and explicit anchored one-times authorities', () => {
        assert.equal(digest(region(sources["DESIGN.md"], "**Clock correction direction:**", '\n\n').replace(/\s+/g,' ').trim()), '5654dd69b5a8069125fbac2b011c92730c54abdddd0c2a1e22b962ba5757b35d', 'clock: exact current owned clause required');
        const simNowCopies=[];let simNowAt=sources['index.html'].indexOf("function simNow(){");
        while(simNowAt>=0){const end=sources['index.html'].indexOf('\n}',simNowAt);assert(end>simNowAt,'simNow: complete function required');simNowCopies.push(sources['index.html'].slice(simNowAt,end+2));simNowAt=sources['index.html'].indexOf("function simNow(){",simNowAt+1);}
        assert.equal(simNowCopies.length,1,'simNow: declared owner copies required');for(const body of simNowCopies)assert.equal(digest(body),'4734bd59393a7da39e8b8a91c071c1b38e2ca6a2c4e8986b0ad93df1a24716e9','simNow: actual source owner changed');const simNowCode=simNowCopies[0];
        let wall=1000,elapsed=0;
        const ctx=vm.createContext({Date:{now:()=>wall},FOLLOW_WALL_CLOCK:true,_simValid:true,_simInvalidTz:null,tz:'UTC',_simBase:500,_simTz:'UTC',_rafT0:0,TIMESCALE:1,_RAFNOW:()=>elapsed,initSim(){throw Error('unexpected reanchor');}});
        vm.runInContext(simNowCode,ctx);
        assert.equal(vm.runInContext('simNow()',ctx),1000);wall=300;assert.equal(vm.runInContext('simNow()',ctx),300);wall=2000;assert.equal(vm.runInContext('simNow()',ctx),2000);
        ctx.FOLLOW_WALL_CLOCK=false;elapsed=30;assert.equal(vm.runInContext('simNow()',ctx),530);wall=-10000;assert.equal(vm.runInContext('simNow()',ctx),530);
      });
      await check('docs composed: opaque calendar Earthshine versus atmospheric lunar eligibility', () => {
        assert.equal(digest(region(sources["DESIGN.md"], "**Current lunar body and light:**", '\n\n').replace(/\s+/g,' ').trim()), 'adc96b86e1f7affdf082440534894fd5b54b2c040996090d6852b9036f2abec5', 'lunar-design: exact current owned clause required');
        assert.equal(digest(region(sources["OPTICS.md"], "**Current lunar light permission:**", '\n\n').replace(/\s+/g,' ').trim()), '993f9ead1bc03e0bfc7b138dbb86e75ae16b7069bf89e4538601e0f1b67fb301', 'lunar-optics: exact current owned clause required');
        const nativeLunarPresentationCopies=[];let nativeLunarPresentationAt=sources['index.html'].indexOf("function nativeLunarPresentation(");
        while(nativeLunarPresentationAt>=0){const end=sources['index.html'].indexOf('\n}',nativeLunarPresentationAt);assert(end>nativeLunarPresentationAt,'nativeLunarPresentation: complete function required');nativeLunarPresentationCopies.push(sources['index.html'].slice(nativeLunarPresentationAt,end+2));nativeLunarPresentationAt=sources['index.html'].indexOf("function nativeLunarPresentation(",nativeLunarPresentationAt+1);}
        assert.equal(nativeLunarPresentationCopies.length,2,'nativeLunarPresentation: declared owner copies required');for(const body of nativeLunarPresentationCopies)assert.equal(digest(body),'9b7d34b9b20517da2027f424db17f223d8f08e719518221a23439109d11b5f5e','nativeLunarPresentation: actual source owner changed');const nativeLunarPresentationCode=nativeLunarPresentationCopies[0];
        const clampCode=sources['index.html'].match(/^const clamp= .*$/m)?.[0];assert(clampCode,'actual native clamp owner');
        const api=vm.runInNewContext(clampCode+'\n'+nativeLunarPresentationCode+'\nnativeLunarPresentation');
        const eligible=api({frac:.8,alt:30},-20,false);assert.equal(eligible.moonLightEligible,true);assert(eligible.moonlight>0);
        for(const [moon,sun,failed,reason] of [[{frac:.01,alt:30},-20,false,'near-new'],[{frac:.8,alt:-10},-20,false,'below-horizon'],[{frac:.8,alt:30},10,false,'daylight'],[{frac:.8,alt:30},-20,true,'surface-unavailable']]){
          const actual=api(moon,sun,failed);assert.equal(actual.moonLightEligible,false);assert.equal(actual.moonlight,0);assert.equal(actual.moonLightReason,reason);
        }
        const near=api({frac:.01,alt:30},-20,false);assert.equal(near.moonShow,eligible.moonShow,'calendar presence is separate from phase light permission');
        const buffered=api({frac:.8,alt:-1},-20,false);assert.equal(buffered.moonLightReason,'eligible');assert(buffered.moonlight>0,'renderer altitude fade is not a strict zero-altitude cutoff');
      });
      await check('docs composed: cloud monotonic intervals, old wind, identity and suspension', () => {
        mentions('DESIGN.md', ['signed', 'monotonic', 'old wind', 'two seconds', 'Empty decks', 'explicit seek']);
        assert(!/stable identity[^\n]*location \+ day|direct `paintClouds\(t1\)`/.test(sources['DESIGN.md'] + sources['HANDOFF.md']));
      });
      await check('docs composed: neutral initial reveal and separate texture failure', () => {
        assert.equal(digest(region(sources["DESIGN.md"], "**Current initial reveal:**", '\n\n').replace(/\s+/g,' ').trim()), 'f6a566503e3cec1ae4bbdd8fb7a0890fb57ed9e7cf649f70629c0ffd12dbdfb4', 'head: exact current owned clause required');
        const updateSkySurfaceCopies=[];let updateSkySurfaceAt=sources['index.html'].indexOf("function updateSkySurface(){");
        while(updateSkySurfaceAt>=0){const end=sources['index.html'].indexOf('\n}',updateSkySurfaceAt);assert(end>updateSkySurfaceAt,'updateSkySurface: complete function required');updateSkySurfaceCopies.push(sources['index.html'].slice(updateSkySurfaceAt,end+2));updateSkySurfaceAt=sources['index.html'].indexOf("function updateSkySurface(){",updateSkySurfaceAt+1);}
        assert.equal(updateSkySurfaceCopies.length,1,'updateSkySurface: declared owner copies required');for(const body of updateSkySurfaceCopies)assert.equal(digest(body),'02064b82512345de9e4b4770d8d42cc1c9de810210d764bdefa72d8f21105e0f','updateSkySurface: actual source owner changed');const updateSkySurfaceCode=updateSkySurfaceCopies[0];
        const commitSkySceneCopies=[];let commitSkySceneAt=sources['index.html'].indexOf("function commitSkyScene(");
        while(commitSkySceneAt>=0){const end=sources['index.html'].indexOf('\n}',commitSkySceneAt);assert(end>commitSkySceneAt,'commitSkyScene: complete function required');commitSkySceneCopies.push(sources['index.html'].slice(commitSkySceneAt,end+2));commitSkySceneAt=sources['index.html'].indexOf("function commitSkyScene(",commitSkySceneAt+1);}
        assert.equal(commitSkySceneCopies.length,1,'commitSkyScene: declared owner copies required');for(const body of commitSkySceneCopies)assert.equal(digest(body),'54e6ebdacabb1234bb3402a8b134717c8c0ef12e778e4e674af130f0196b6747','commitSkyScene: actual source owner changed');const commitSkySceneCode=commitSkySceneCopies[0];
        const toggles=new Map(),removed=[];
        const card={classList:{toggle:(n,v)=>toggles.set(n,v),remove:n=>removed.push(n)},getBoundingClientRect:()=>({})};
        let surface=null,href='';const photo={getAttribute:()=>href},mask={classList:{toggle:(n,v)=>toggles.set(n,v)}};
        const ctx=vm.createContext({window:{SalahMoonRuntime:{surface:()=>surface}},_skySceneKey:'a',_skyMoonPresence:1,_skyCommitted:false,_starProjectionKey:'a',_pbrReady:true,
          $:s=>s==='.c'?card:s==='.mphoto'?photo:s==='.moon-mask-disc'?mask:null,paintClouds(){},simNow:()=>0,tieRainToClouds(){},getComputedStyle:()=>({getPropertyValue:()=>''})});
        vm.runInContext(updateSkySurfaceCode+'\n'+commitSkySceneCode,ctx);
        vm.runInContext('updateSkySurface()',ctx);assert.equal(toggles.get('moon-ready'),false,'decoded legacy flag grants no surface');
        surface={};href='current';vm.runInContext('updateSkySurface()',ctx);assert.equal(toggles.get('moon-ready'),true);
        href='';vm.runInContext('updateSkySurface()',ctx);assert.equal(toggles.get('moon-ready'),false);href='current';ctx._skySceneKey=null;vm.runInContext('updateSkySurface()',ctx);assert.equal(toggles.get('moon-ready'),false);
        for(const [key,stars,fresh,want] of [['a','a',true,true],['a','a',false,false],['a','stale',true,false],[null,'a',true,false]]){
          ctx._skySceneKey=key;ctx._starProjectionKey=stars;ctx._skyCommitted=false;removed.length=0;ctx.observation={moonObservation:{fresh}};
          vm.runInContext('commitSkyScene(observation)',ctx);assert.equal(ctx._skyCommitted,want);assert.equal(removed.includes('sky-pending'),want);
        }
        const prayerUnavailableCopies=[];let prayerUnavailableAt=sources['index.html'].indexOf('function paintCelestialWithoutTimetable(){');
        while(prayerUnavailableAt>=0){const end=sources['index.html'].indexOf('\n}',prayerUnavailableAt);assert(end>prayerUnavailableAt,'prayer-unavailable reveal: complete owner required');prayerUnavailableCopies.push(sources['index.html'].slice(prayerUnavailableAt,end+2));prayerUnavailableAt=sources['index.html'].indexOf('function paintCelestialWithoutTimetable(){',prayerUnavailableAt+1);}
        assert.equal(prayerUnavailableCopies.length,1,'prayer-unavailable reveal: declared owner required');assert.equal(digest(prayerUnavailableCopies[0]),'fa5f0e305b182d2cf562e297eb599a5bf96bfbca752f9acd16dc470464d961fe','prayer-unavailable reveal: actual source owner changed');
        const fallbackRemoved=[],fallbackCalls=[],styleValues=new Map();let identity='active',solar=-20;
        const fallbackCard={style:{setProperty:(k,v)=>styleValues.set(k,v)},classList:{remove:n=>fallbackRemoved.push(n)}};
        const fallbackCtx=vm.createContext({window:{SalahNativeSkyHost:{cloudLighting:()=>({sun:{altDeg:solar}})},SalahMoonRuntime:{request:()=>fallbackCalls.push('surface-request')}},
          skySceneIdentity:()=>identity,_skySceneKey:null,beginSkyScene:()=>fallbackCalls.push('begin'),nowParts:()=>({h:12,mi:0,s:0}),moonGeometryObservation:()=>({fresh:false}),
          renderMoon:()=>fallbackCalls.push('moon'),projectStars:()=>fallbackCalls.push('stars'),simDate:()=>new Date(0),lunarPresentation:()=>({moonShow:.8,moonlight:.5}),
          $:()=>fallbackCard,updateSkySurface:()=>fallbackCalls.push('surface')});
        vm.runInContext(prayerUnavailableCopies[0],fallbackCtx);
        vm.runInContext('paintCelestialWithoutTimetable()',fallbackCtx);assert(fallbackCalls.indexOf('moon')<fallbackCalls.indexOf('stars'));assert(fallbackCalls.includes('surface'));
        assert.deepEqual(fallbackRemoved,['sky-pending']);assert.equal(fallbackCtx._skySceneKey,'active');
        for(const [key,altitude] of [[null,-20],['active',NaN]]){identity=key;solar=altitude;fallbackCalls.length=0;fallbackRemoved.length=0;vm.runInContext('paintCelestialWithoutTimetable()',fallbackCtx);assert.equal(fallbackCalls.length,0);assert.equal(fallbackRemoved.length,0);}
      });
      await check('docs composed: one selected provider calendar decision and complete-value access', () => {
        assert.equal(digest(region(sources["DESIGN.md"], "**Calendar source disclosure:**", '\n\n').replace(/\s+/g,' ').trim()), '2e7101fb46b5e82fa3d17c229cbad3819d688b486f900c27bc63251facce4408', 'calendar-design: exact current owned clause required');
        assert.equal(digest(region(sources["README.md"], "**Calendar selection:**", '\n\n').replace(/\s+/g,' ').trim()), 'fb5a3c94c1432a99eff03e868733fd3aaddd3b6050f9f12d649259501b397bcb', 'calendar-readme: exact current owned clause required');
        const selectCalendarDisplayCopies=[];let selectCalendarDisplayAt=sources['index.html'].indexOf("function selectCalendarDisplay(");
        while(selectCalendarDisplayAt>=0){const end=sources['index.html'].indexOf('\n}',selectCalendarDisplayAt);assert(end>selectCalendarDisplayAt,'selectCalendarDisplay: complete function required');selectCalendarDisplayCopies.push(sources['index.html'].slice(selectCalendarDisplayAt,end+2));selectCalendarDisplayAt=sources['index.html'].indexOf("function selectCalendarDisplay(",selectCalendarDisplayAt+1);}
        assert.equal(selectCalendarDisplayCopies.length,1,'selectCalendarDisplay: declared owner copies required');for(const body of selectCalendarDisplayCopies)assert.equal(digest(body),'b34a72e014b3527f97cc868e3fd8bc6df9103577bd8f77106eaf6e555ce5847b','selectCalendarDisplay: actual source owner changed');const selectCalendarDisplayCode=selectCalendarDisplayCopies[0];
        const data=(day,ah,method='method')=>({meta:{timezone:'UTC'},date:{gregorian:{date:day},hijri:ah==null?null:{day:ah,method}}});
        const today=data('03-10-2026',1,'current-method'),tomorrow=data('04-10-2026',2,'next-method');
        const ctx=vm.createContext({Date,tz:'UTC',today,tomorrow,_prayerStale:false,partsInTz:()=>({y:2026,mo:10,d:3,dateStr:'03-10-2026'}),pad:n=>String(n).padStart(2,'0'),
          calendarRecordDay:d=>d?.date?.gregorian?.date??null,calendarFields:o=>o?.day?{}:null,mins:s=>Number(s.split(':')[0])*60+Number(s.split(':')[1]),fmtDate:(o,c)=>o?(c==='hijri'?String(o.day):o.date):'',phaseEmoji:()=>'',moonNow:()=>({phase:0})});
        vm.runInContext(selectCalendarDisplayCode,ctx);ctx.M={nowEpoch:0,nowMin:600,t:{Maghrib:'18:00'}};
        let result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert.equal(result.selectedSource,'today');assert.equal(result.hijriText,'1');assert.equal(result.hijriMethod,'current-method');
        ctx.M.nowMin=1200;result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert.equal(result.selectedSource,'tomorrow');assert.equal(result.hijriText,'2');assert.equal(result.gregorianText,'03-10-2026');assert.equal(result.hijriAnomaly,null);
        ctx.tomorrow=null;result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert.equal(result.hijriText,'1');assert.equal(result.unavailableReason,'Sunset date update unavailable');
        ctx.today=data('03-10-2026',1,' ');result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert(result.explanation.includes('calendar convention unavailable'));assert.equal(result.hijriAnomaly,null);
        ctx.today=data('03-10-2026',null);result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert.equal(result.unavailableReason,'Hijri date unavailable');
        ctx.today=today;ctx.tomorrow={...tomorrow,meta:{timezone:'wrong'}};result=vm.runInContext('selectCalendarDisplay(M)',ctx);assert.equal(result.selectedSource,'today');assert.equal(result.maghribRollApplied,false);
      });
      await check('docs composed: default glass and opt-in contrast keep distinct gates', () => {
        assert.equal(digest(region(sources["README.md"], "**Timetable appearance:**", '\n\n').replace(/\s+/g,' ').trim()), '9ee45ebb3113306c65b53c32c95a4796b2a1bb1b8c5b7495cd3cec925afdca95', 'appearance: exact current owned clause required');
        assert.equal(digest(region(sources['DESIGN.md'], '- **Timetable readability:**', '\n- The arc').replace(/\s+/g,' ').trim()), 'e5ff4309f19b06f6c6d4682cbd2705b0f1a6dca8c1cfa7143a1b7c4340ce2413', 'adopted default readability obligation must remain exact');
        assert(sources['index.html'].includes('<option value="glass">Liquid glass (default)</option><option value="contrast">High contrast</option>'),'actual settings profiles required');
        const defaultPrayerRules=sources['index.html'].match(/^\.p\{[^\n]*\}$/gm)||[];
        assert.equal(defaultPrayerRules.length,1,'default names/times must not be faded: one actual default .p rule required');
        const defaultPrayerStyle=Object.fromEntries(defaultPrayerRules[0].slice(3,-1).split(';').filter(Boolean).map(declaration=>{
          const colon=declaration.indexOf(':');assert(colon>0,'complete actual default .p declaration required');return [declaration.slice(0,colon).trim(),declaration.slice(colon+1).trim()];
        }));
        assert.equal(defaultPrayerStyle.color,'#f0edf8','default names/times must not be faded: actual default .p color required');
        assert.equal(defaultPrayerStyle.opacity,'1','default names/times must not be faded: actual default .p opacity required');
        assert.equal(defaultPrayerStyle.background,'linear-gradient(160deg,#ffffff26,#ffffff0d),rgba(9,17,28,.82)','default names/times must not be faded: actual default .p backing required');
        const ctx=vm.createContext({URLSearchParams,Intl,Date});vm.runInContext(sources['config.js'],ctx);const config=ctx.SalahConfig;
        assert.equal(config.DEFAULTS.appearance,'glass');assert.equal(config.parseHash('#appearance=contrast').cfg.appearance,'contrast');assert.equal(config.parseHash('#appearance=unsupported').cfg.appearance,'glass');
        const store=new Map(),storage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
        const value={lat:24.47,lon:39.61,tz:'UTC',appearance:'contrast'};assert.equal(config.saveLocal(value,storage).ok,true);assert.equal(config.loadLocal(storage).appearance,'contrast');
        const denied={setItem(){const e=Error('private denied');e.name='SecurityError';throw e;}};assert.equal(config.saveLocal(value,denied).ok,false);
      });
      await check('docs composed: actual smoke terminal contract and held qualification', () => {
        const contract = region(sources['README.md'], '### Deterministic smoke test', '\n---');
        assert.equal(digest(contract), '54e8bc9884531c6b2e42586fadd6880dac24544f2b62b0aa7d1d237a15fac0f5', 'exact current README R0017 terminal contract required');
        for (const name of ['ARCHITECTURE.md', 'HANDOFF.md']) {
          const current = region(sources[name], '## Current R0017 smoke contract', '\n## ').replace(/\s+/g, ' ');
          for (const token of ['README.md#deterministic-smoke-test', '30 named required callbacks', '141 expected assertions',
            '**PASS** requires all declared callbacks to finish with their declared assertion counts and no recorded error.',
            'A recorded assertion, callback, harness or bootstrap error makes **FAIL**, even when callbacks are missing.',
            'With no recorded error, a missing callback makes **INCOMPLETE**.',
            'window.__smoke.required.total', 'window.__smoke.required.executed', 'window.__smoke.required.missing',
            'inline Moon startup/refinement layout', 'moon-initial-code', 'moon-refinement-code', 'Unreviewed widget script anchors',
            'separately reviewed wrapper adaptation before current-candidate qualification', 'No current native smoke PASS is claimed here.'])
            assert(current.includes(token), `${name}: missing current R0017 contract ${token}`);
          assert(!/Apple Bash 3\.2|round-4/.test(current), 'installer/platform gates stay in their own contracts');
          assert(!/\?run=1|manual Run button/.test(current), 'unimplemented smoke opt-in');
          assert.equal(digest(current), 'e7d61e06a3a80beb7ef4de880b3e0062d9ffde46b144f1a7f5e593e3c5f173fa', 'current R0017 prose differs from exact source-bound contract');
        }
      });
      await check('docs composed: two legacy SIM comments describe synthetic preview amount', () => {
        const parameter = sources['index.html'].match(/^\s*precip:\s*q\.get\("simPrecip"\).*$/m)?.[0];
        const defaultComment = sources['index.html'].match(/^\s*\/\/ default a code-appropriate.*$/m)?.[0];
        assert(parameter && defaultComment, 'fixture applicability: exact existing SIM comments required');
        assert(!/observed precip/.test(parameter + defaultComment));
        assert(/synthetic preview/.test(parameter) && /synthetic preview/.test(defaultComment));
      });
    }
  }
  for (const result of results) console.log(JSON.stringify(result));
  const failed = results.filter(r => r.status === 'FAIL').length;
  console.log(JSON.stringify({ summary: { cases: results.length, passed: results.filter(r=>r.status==='PASS').length, reused:results.filter(r=>r.status==='REUSED').length, failed, scope: scope || (sourceOnly ? 'source-only' : 'source-and-docs'), sourceRef: ref || 'working tree', docsSource:docsRoot || (ref || root), selectedLedger, browser: 'NOT_RUN', network: 'intercepted, no transmission' }, fixtureSha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'), sha256: Object.fromEntries(Object.entries(sources).map(([name, text]) => [name, crypto.createHash('sha256').update(text).digest('hex')])) }));
  process.exitCode = failed ? 1 : 0;
})().catch(error => { console.error(error.stack); process.exitCode = 2; });
