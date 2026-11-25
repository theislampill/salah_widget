'use strict';

// R003F F-GAIN. Each proposal is evaluated on the same admitted V5 fields.
// These are surface gains. They are not P1 measurements of the composited card.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');

const moon = path.resolve(__dirname, '../../moon');
const fractions = [0.01, 0.04, 0.08, 0.15, 0.314, 0.5, 0.75, 0.85, 0.99];
const caps = {B1c: 0.6, B4: 0.5, B6: 0.6};
const Y = [0.2126, 0.7152, 0.0722];
const units = ['asset-digest.mjs', 'surface_v5.mjs', 'moon-detail.mjs', 'moon-calendar.mjs',
  'moon-engine.mjs', 'moon-quality.mjs', 'moon-precision.mjs'];
const read = file => fs.readFileSync(path.join(moon, file));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

function gainProperties(base, gain, cap) {
  assert.ok(Number.isFinite(gain) && gain >= base && gain <= 1, 'gain below B0 or outside [0,1]');
  assert.ok(gain === base || gain <= cap, 'raised gain exceeds cap');
}

// Compare +/-T at the receiver level. Integer codes here are straight sRGB
// before resampling or composition. They cannot predict a card screenshot.
function toneDifference(refined, coverage, gain) {
  const tint = [0.94, 1.0, 1.10];
  const tintY = tint.reduce((sum, channel, k) => sum + channel * Y[k], 0);
  let changed = 0, maxYError = 0;
  const code = value => {
    const v = Math.min(1, Math.max(0, value));
    return Math.round(255 * (v <= 0.0031308 ? 12.92*v : 1.055*v**(1/2.4)-0.055));
  };
  for (let i = 0; i < coverage.length; i++) {
    const a = coverage[i];
    if (!a) continue;
    const j = 3*i;
    const yl = gain * (Y[0]*refined[j] + Y[1]*refined[j+1] + Y[2]*refined[j+2]);
    let tintedY = 0, differs = false;
    for (let k = 0; k < 3; k++) {
      const q = refined[j+k]*gain;
      const tinted = Math.fround(Math.max(0, 0.4*q + 0.6*yl*tint[k]/tintY));
      tintedY += Y[k]*tinted;
      if (code(Math.fround(q)/a) !== code(tinted/a)) differs = true;
    }
    if (differs) changed++;
    maxYError = Math.max(maxYError, Math.abs(tintedY-yl));
  }
  assert.ok(maxYError < 1e-7, 'tone cue changed receiver luminance');
  return {changedReceivers8bit:changed, maxLinearYError:maxYError};
}

function kernelMaterial(engine, size) {
  const count = size * size;
  const receivers = new Float64Array(engine.e.memory.buffer, engine.e.get_pixels(), count * 24);
  const material = new Float32Array(3 * count);
  for (let i = 0; i < count; i++) {
    for (let k = 0; k < 3; k++) material[3*i+k] = receivers[24*i+6+k];
  }
  return material;
}

function measure(api, material, result, waxing) {
  const {surfaceSize: size, surfaceCoverage: coverage, surfaceLinear: refined} = result;
  const count = coverage.length;
  assert.equal(material.length, refined.length);
  const luma = new Float64Array(count);
  let total = 0, ceiling = 0, moment = 0;
  for (let i = 0; i < count; i++) {
    for (let k = 0; k < 3; k++) {
      const j = 3 * i + k;
      ceiling += Y[k] * 0.020 * material[j] * coverage[i];
      total += Y[k] * refined[j];
      luma[i] += Y[k] * refined[j];
    }
    moment += luma[i] * (2 * (i % size + 0.5) / size - 1);
  }
  assert.ok(total > 0 && ceiling > 0);
  const g0 = Math.min(1, ceiling / total);
  const sorted = luma.slice().sort();
  const rank = 0.995 * (count - 1), lo = Math.floor(rank), hi = Math.ceil(rank);
  const p995 = sorted[lo] + (rank - lo) * (sorted[hi] - sorted[lo]);
  let litCount = 0, litSum = 0;
  for (let i = 0; i < count; i++) {
    if (coverage[i] > 0.5 && luma[i] >= 0.25 * p995) {
      litCount++;
      litSum += luma[i] / coverage[i];
    }
  }
  const litMean = litCount ? litSum / litCount : null;
  const gains = {
    B0: g0,
    B1c: Math.max(g0, Math.min(caps.B1c, 2 * g0)),
    B4: litCount ? Math.max(g0, Math.min(caps.B4, 0.055 / litMean)) : g0,
    B6: Math.max(g0, Math.min(caps.B6, Math.max(1.5 * g0, 0.19)))
  };
  const base = api.calendarProxy(material, coverage, refined);
  const baseBytes = Buffer.from(base.buffer, base.byteOffset, base.byteLength);
  if (result.calendarLinear) assert.ok(baseBytes.equals(Buffer.from(result.calendarLinear.buffer)),
    'reconstructed gain differs from the published initial token');
  const tokens = {}, tone = {};
  for (const [name, gain] of Object.entries(gains)) {
    gainProperties(g0, gain, caps[name] ?? 1);
    const candidate = Buffer.from(refined.map(v => gain * v).buffer);
    if (name === 'B0' || g0 >= caps[name] || gain === g0) {
      assert.ok(candidate.equals(baseBytes), name + ' differs from the shipped B0 at unchanged gain');
    }
    tokens[name] = hash(candidate);
    tone[name] = toneDifference(refined, coverage, gain);
  }
  if (result.scene.fraction === 0.99) {
    for (const name of Object.keys(caps)) assert.ok(gains[name] > g0,
      name + ' incorrectly retained the baseline at full phase');
  }
  const centroidX = moment / total;
  if (result.scene.fraction === 0.08) {
    const matchingSense = sense => (sense ? centroidX : -centroidX) > 0;
    assert.equal(gains.B4, g0, 'thin B4 control must reproduce B0');
    assert.ok(matchingSense(waxing), 'thin illuminated limb on the wrong side');
    assert.ok(!matchingSense(!waxing), 'swapped sense escaped detection');
    const b2 = Math.min(1, 0.057 / 0.020 * ceiling / total);
    assert.equal(b2, 1, 'seeded B2 thin control must reach physical gain');
    assert.throws(() => gainProperties(g0, b2, caps.B1c), /exceeds cap/);
    assert.throws(() => gainProperties(g0, 2 * g0, caps.B1c), /exceeds cap/);
  }
  assert.throws(() => gainProperties(g0, g0 / 2, caps.B6), /below B0/);
  return {size, fraction: result.scene.fraction, waxing, sourceSamples: result.diagnostics.sourceSamples ?? result.diagnostics.quality?.solarSamples,
    quality: result.diagnostics.quality?.status ?? "fixed-64",
    physicalSurfaceIdentity: result.physicalIdentity, centroidX, p995, litCount, litMean, gains, tokenSha256: tokens, tone};
}

async function main() {
  const {parseArgs} = require('node:util');
  const {values} = parseArgs({options: {size: {type:'string'}, out: {type:'string'}, adaptive: {type:'boolean'}, initial: {type:'boolean'}}});
  const source = units.map(unit => read('src/' + unit).toString());
  const api = Function(source.join('\n') + '\nreturn {MoonEngine, adaptiveRender, canonicalScene, nativeCalendarMoonScene, calendarProxy};')();
  const shipped = api.nativeCalendarMoonScene({fraction: 0.5, physicalFraction: 0.5, waxing: true, timeScale: 0}, {}).size;
  assert.ok(!(values.initial && (values.adaptive || values.size)), '--initial uses the shipped receiver size');
  const sizes = values.initial ? [shipped] : values.size ? [Number(values.size)] : [160, shipped];
  for (const size of sizes) assert.ok([160, shipped].includes(size), 'expected 160 or the shipped receiver size');
  const manifest = JSON.parse(read('asset-manifest.json'));
  let engine, initial, material, initialPin, initialSource;
  if (values.initial) {
    initialPin = JSON.parse(read('initial-manifest.json'));
    initialSource = read('src/moon-initial.mjs').toString();
    // Observe the arguments to the real producer's canonical calendarProxy
    // call without changing its return value, as an in-process measuring probe.
    const withProxy = Function(source.join('\n') + '\nreturn function(calendarProxy){' + initialSource +
      '\nreturn createInitialMoon; }')();
    const create = withProxy((m, c, surface) => {
      material = m;
      return api.calendarProxy(m, c, surface);
    });
    initial = create(new Uint8Array(read('assets/initial-receivers.bin')), initialPin);
  } else {
    engine = await api.MoonEngine.create({manifest, wasm: new Uint8Array(read('moon_kernel.wasm')),
      dem: new Uint8Array(read(manifest.assets.dem.path)), colour: new Uint8Array(read(manifest.assets.colour.path))});
  }
  const rows = [];
  for (const size of sizes) {
    for (const fraction of fractions) {
      for (const waxing of [false, true]) {
        const scene = api.canonicalScene({size, fraction, waxing});
        let result;
        if (initial) {
          result = initial.render(scene);
        } else {
          result = values.adaptive ? await api.adaptiveRender(engine, scene)
            : await engine.render(scene, {radial: 4, azimuth: 16, qualityFields: true});
          material = kernelMaterial(engine, result.surfaceSize);
        }
        rows.push(measure(api, material, result, waxing));
        if (values.out) console.log('PASS F-GAIN', size, fraction, waxing ? 'waxing' : 'waning');
      }
    }
  }
  const report = {protocol:'R003F/F-GAIN/1', basis:initial ? 'shipped 540 initial V5 receiver' : values.adaptive ? 'canonical V5, production adaptiveRender' : 'canonical V5, fixed finite-source 4x16 quadrature',
    angularQualification:'headless surface gain; each row declares convergence or fixed sampling; no native P1 claim',
    node:process.version, sizes, ...(initial ? {initialReceiverSha256:initialPin.sha256, initialSourceSha256:hash(initialSource)} : {}),
    assets:{wasm:manifest.wasm.sha256, dem:manifest.assets.dem.sha256, colour:manifest.assets.colour.sha256},
    sourceSha256:Object.fromEntries(units.map((unit, i) => [unit, hash(source[i])])),
    percentile:'type 7 over the whole receiver raster, including zero coverage',
    controls:['unchanged-gain Float32 bytes versus shipped calendarProxy', 'thin B2 == 1 and cap mutant rejected',
      'floor below B0 rejected', 'thin illuminated-limb centroid rejects swapped sense'],
    rows};
  const json = JSON.stringify(report, null, 2) + '\n';
  if (values.out) fs.writeFileSync(values.out, json); else process.stdout.write(json);
}
main().catch(error => {console.error(error); process.exitCode = 1;});
