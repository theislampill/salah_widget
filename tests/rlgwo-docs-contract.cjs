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
const docNames = ['README.md', 'AGENTS.md', 'DESIGN.md', 'OPTICS.md', 'ARCHITECTURE.md', 'HANDOFF.md'];
const sources = Object.fromEntries(['config.js', 'builder.html', 'index.html', ...docNames]
  .map(name => [name, ref ? execFileSync('git', ['show', `${ref}:${name}`], { cwd: root, encoding: 'utf8' }) : fs.readFileSync(path.join(root, name), 'utf8')]));
const results = [];
async function check(name, run) {
  try { await run(); results.push({ name, status: 'PASS' }); }
  catch (error) { results.push({ name, status: 'FAIL', error: error.message }); }
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
    for (const name of forceNames) {
      const flags = parsed(`${base}&simTime=12:30&debugOptic=${name}`); assert.equal(flags.DEBUGOPTIC, name);
      const state = vm.runInNewContext(`let sunHalo=0,sunDogs=0,sunPillar=0,antiCrep=0,moonParhelia=0,lunarHalo=0;\n${forceBlock}\n[sunHalo,sunDogs,sunPillar,antiCrep,moonParhelia,lunarHalo]`, { DEBUGOPTIC: name });
      assert.equal(state.filter(x => x > 0).length, 1, `${name} has one actual force assignment`);
    }
    assert.equal(parsed(`${base}&debugOptic=corona`).DEBUGOPTIC, 'corona');
    assert(!forceNames.includes('corona'));
    assert.throws(() => assert.deepEqual([...claimedNames, 'corona'], forceNames), 'unsupported enum mutant must fail');
  });
  if (!sourceOnly) {
    await check('docs: README privacy names actual recipients and trigger fields', () => {
      const privacy = region(sources['README.md'], '### Auto-detect, precise location & privacy', '\n---');
      for (const token of ['GeoJS', 'ipinfo.io', 'Nominatim', 'Zippopotam', 'BigDataCloud', 'Aladhan', 'Open-Meteo', 'RainViewer', 'Google Fonts', 'countrycodes', 'localityLanguage', 'Reset', 'retention']) assert(privacy.includes(token), `privacy missing ${token}`);
      assert(!sources['README.md'].includes('no tracking'), 'remove unsupported blanket claim');
      assert(!privacy.includes('stores nothing about you on any server'));
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
        for (const [index, line] of doc.split('\n').entries()) {
          if (/\?(?:debugMotion|debugOptic|debugLayers|debugMoon|motion)=/.test(line)) assert(/query-only.*not read/.test(line), `${name}:${index + 1}: ${line.trim()}`);
        }
      });
      for (const [index, line] of doc.split('\n').entries()) {
        const recipes = [...line.matchAll(/`([^`]*(?:&debugMotion=1|&motion=full|&debugOptic=[a-z]+|&debugLayers=1|&debugMoon=1)[^`]*)`/g)].map(m => m[1]);
        if (/^index\.html#/.test(line)) recipes.push(line.trim());
        for (const recipe of recipes) await check(`recipe: ${name}:${index + 1}: ${recipe}`, () => {
          const actual = parsed(recipe.startsWith('&') ? base + recipe : recipe);
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
  }
  for (const result of results) console.log(JSON.stringify(result));
  const failed = results.filter(r => r.status === 'FAIL').length;
  console.log(JSON.stringify({ summary: { cases: results.length, passed: results.length - failed, failed, scope: sourceOnly ? 'source-only' : 'source-and-docs', sourceRef: ref || 'working tree', browser: 'NOT_RUN', network: 'intercepted, no transmission' }, fixtureSha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'), sha256: Object.fromEntries(Object.entries(sources).map(([name, text]) => [name, crypto.createHash('sha256').update(text).digest('hex')])) }));
  process.exitCode = failed ? 1 : 0;
})().catch(error => { console.error(error.stack); process.exitCode = 2; });
