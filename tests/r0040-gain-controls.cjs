'use strict';

// Run against the separate precipitation research checkout. The no-op drawing context
// exercises the real model's public set/frame and allocation paths, without taking pixels.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
if (process.argv.length !== 3) throw Error('usage: node tests/r0040-gain-controls.cjs RESEARCH_CHECKOUT');
const qa = path.join(process.argv[2], 'tools/qa');
const source = fs.readFileSync(path.join(qa, 'precip_models.js'), 'utf8');
const profile = JSON.parse(fs.readFileSync(path.join(qa, 'precip_declared_gain.json'), 'utf8'));

function renderer(rate, parameters, options, tileAlphas = []) {
  const noop = () => {};
  const presentedTiles = new Set();
  let frameTime = 0;
  function element() {
    const canvas = {style: {}}, context = Object.create(draw);
    let firstStroke = true;
    context.stroke = () => {
      if (firstStroke && canvas.width === 352 && canvas.height === 320) {
        firstStroke = false;
        tileAlphas.push(context.strokeStyle);
      }
    };
    canvas.getContext = () => context;
    return canvas;
  }
  const draw = {clearRect: noop, putImageData: noop, drawImage: source => {
    if (source.width === 352 && source.height === 320) presentedTiles.add(source);
  }, beginPath: noop,
    moveTo: noop, lineTo: noop, stroke: noop, save: noop, restore: noop,
    fillRect: noop, setTransform: noop, createLinearGradient: () => ({addColorStop: noop}),
    getImageData: (_x, _y, w, h) => ({data: new Uint8ClampedArray(w*h*4)})};
  const card = {dataset: {precip: 'on', fx: 'rain'}};
  const window = {__PM_PARAMS: parameters, qaState: () => ({})};
  const document = {querySelector: s => s === '.c' ? card : null, querySelectorAll: () => [],
    getElementById: () => ({querySelector: () => null, insertBefore: noop}),
    createElement: element, head: {appendChild: noop}};
  vm.runInNewContext(source, {window, document, location: {hash: ''}, URLSearchParams,
    selectedWeather: () => ({code: 63, precip: rate/4, wind: 0, cloud: 85}),
    getComputedStyle: () => ({getPropertyValue: () => '0'}), requestAnimationFrame: noop,
    performance: {now: () => 0}});
  window.__PM.set(options.shell ? 'M1' : 'M2', 'flat', options);
  return (nextRate = rate) => {
    rate = nextRate;
    frameTime += 1000; // refresh the prototype's 500 ms weather input cache
    presentedTiles.clear();
    const frame = window.__PM.frame(frameTime);
    return {R: frame.R, tiles: [...presentedTiles]};
  };
}

const tex = {layers: ['tex']};
const tileAlphas = [];
assert.equal(renderer(12, profile, tex, tileAlphas)().R, 12, 'largest stratiform condition of the historical pack');
// At G=100 the first seeded strokes are D=0.3/0.6 mm, depth 1.52902/3.04717 m,
// v=1.17/2.46393 m/s. Canvas receives alpha = G*4*f*(D/2000)^2/(z*v*T), rounded to 0.001.
assert.deepEqual(tileAlphas, ['rgba(255,255,255,0.080)', 'rgba(255,255,255,0.076)']);
const overflow = renderer(20, profile, tex);
assert.throws(overflow, /124160 strokes; cap 100000/, 'a stronger, forward-looking control binds the far slab cap');
assert.throws(overflow, /124160 strokes/, 'a failed tile build must never become a cache hit');
const recovery = renderer(12, profile, tex);
const before = recovery().tiles;
assert.equal(before.length, 2);
assert.throws(() => recovery(20), /124160 strokes/);
const after = recovery(12).tiles;
assert.equal(after.length, 2, 'both slabs are drawn after a rejected weather change');
before.forEach((canvas, i) => assert.equal(after[i], canvas, 'recovered image uses its original valid slab'));
const below = 14.72417113166102, above = 14.724191131661026;
assert.equal(below.toFixed(2), above.toFixed(2));
const crossing = renderer(below, profile, tex);
assert.equal(crossing().tiles.length, 2);
assert.throws(() => crossing(above), /100001 strokes; cap 100000/, 'the warm cache must honor the exact new rate');
assert.throws(renderer(above, profile, tex), /100001 strokes; cap 100000/, 'the cold decision must agree');
assert.throws(renderer(12, {...profile, render: {...profile.render, lineFloor: 0.6}}, tex), /additive line width/);
assert.throws(renderer(12, {...profile, sunKernel: {...profile.sunKernel, amp: 0.55}}, tex), /light kernels/);
assert.throws(renderer(12, {...profile, moonKernel: {...profile.moonKernel, amp: 0.35}}, tex), /light kernels/);
assert.throws(renderer(12, profile, {shell: [1, 3]}), /shell cap/);
console.log('PASS: nominal 12 mm/h stroke alphas, overflow, retry, 12→20→12 tile identity, same-rounded-rate cap crossing, width floor, Sun and Moon kernels, shell compensation');
