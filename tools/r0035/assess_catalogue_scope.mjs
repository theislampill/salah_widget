/** R0035 offline experiment. Run at the repository root with Node.
 * Same catalogue, registered diffuse renderer, PSF and encoder as the widget.
 * Physical detectability comes from the worker diagnostics. RGB probes encode
 * its returned raster before host atmospheric adaptation and foreground composition. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {NativeSkyEngine} from '../../real-sky/native-engine.mjs';
import {NativeStarPreview} from '../../real-sky/native-star-preview.mjs';
import {directTransmission} from '../../real-sky/core/src/atmosphere.mjs';
import {sourceCenterResponse} from './center_signal.mjs';
import {spectralStarFlux} from '../../real-sky/core/src/spectral.mjs';

const data = new URL('../../vendor/real-sky/data/', import.meta.url);
const read = name => readFileSync(new URL(name, data), 'utf8');
const pack = {
  catalogueText: read('bright-stars.json'),
  manifestText: read('registered-starlight/runtime-manifest.json'),
  assetTexts: {128: read('registered-starlight/V-nside128.json')}
};
const scenes = {
  darkNight: '2026-11-09T00:00:00Z',
  moonlitNight: '2026-11-24T00:00:00Z',
  nearFajr: '2026-11-09T02:15:00Z',
  morningTwilight: '2026-11-09T03:15:00Z',
  daylight: '2026-11-09T09:00:00Z'
};
const observer = {
  lat: 24.47, lon: 39.61, heightM: 0, generation: 1, sceneIdentity: 'r0035-clear',
  camera: {azDeg: 180, altDeg: 45, fovYDeg: 90, rollDeg: 0},
  weather: {src: 'synthetic-clear', vis: 20000, temp: 10}, lp: 0, reducedMotion: false
};
// This split describes the actual bootstrap preview. The refined catalogue
// has no corresponding magnitude cutoff. Do not infer a modulation gate.
const preview = new NativeStarPreview(pack);
const previewLimit = preview.identity.maximumMagnitude;
const previewIds = new Set(preview.catalogue.stars.map(star => star.id));
const groupFor = star => {
  assert.equal(previewIds.has(star.id), star.vmag <= previewLimit);
  return previewIds.has(star.id) ? 'previewMembers' : 'refinedOnly';
};
function emptyGroup() {
  return {projected: 0, evaluated: 0, incompleteBackground: 0, modelDetectable: 0,
    centerContributes: 0, detectableCenterContributes: 0, detectableCenterResponds1pct: 0,
    detectableCenterResponds5pct: 0};
}

function measureCenter(frame, star, record, diagnostic) {
  const {raster} = frame;
  const flux = spectralStarFlux(record, star.altDeg, {}, {
    response: 'CIE1931',
    transportAt: wavelength => directTransmission(wavelength, star.altDeg, raster.atmosphere, diagnostic.cloudTransmission)
  });
  assert.equal(flux.vFlux, diagnostic.vFlux);
  return sourceCenterResponse(raster, star, flux);
}

async function census(engine, catalogue, utc) {
  const job = nativeJob({...observer, utcMs: Date.parse(utc)}, true);
  assert.equal(job.options.scintillation.strength, 0);
  const frame = await engine.render(job);
  assert.equal(frame.status, 'ready', frame.error);
  assert.equal(frame.diffuseAsset.mode, 'registered');
  const {raster} = frame;
  const sourceMap = new Map(frame.sources.map(s => [s.id, s]));
  assert.equal(sourceMap.size, frame.sources.length);
  const groups = {previewMembers: emptyGroup(), refinedOnly: emptyGroup()};
  for (const s of frame.sources) groups[groupFor(s)].projected++;
  const seen = new Set();
  const examples = [];
  for (const diagnostic of raster.sourceDiagnostics) {
    assert.ok(!seen.has(diagnostic.id));
    seen.add(diagnostic.id);
    const star = sourceMap.get(diagnostic.id);
    assert.ok(star && star.vmag === diagnostic.vmag);
    const group = groups[groupFor(star)];
    group.evaluated++;
    const center = measureCenter(frame, star, catalogue.get(star.id), diagnostic);
    if (center.contributes) group.centerContributes++;
    if (diagnostic.backgroundComplete === false) { group.incompleteBackground++; continue; }
    if (!diagnostic.detectable || star.altDeg <= 0) continue;
    group.modelDetectable++;
    if (center.contributes) group.detectableCenterContributes++;
    if (center.responds1pct) group.detectableCenterResponds1pct++;
    if (center.responds5pct) group.detectableCenterResponds5pct++;
    if (!previewIds.has(star.id) && center.contributes) {
      examples.push({id: star.id, vmag: star.vmag, x: +star.x.toFixed(2), y: +star.y.toFixed(2),
        modelContrastCodes: +(255 * diagnostic.deltaSrgb).toFixed(3), responds5pct: center.responds5pct});
    }
  }
  assert.equal(groups.previewMembers.modelDetectable + groups.refinedOnly.modelDetectable, raster.detectableSources);
  examples.sort((a, b) => b.modelContrastCodes - a.modelContrastCodes);
  return {utc, sunAltDeg: +raster.physicalState.sun.altDeg.toFixed(3),
    moonAltDeg: +raster.physicalState.moon.altDeg.toFixed(3),
    catalogueSha256: frame.catalogue.sha256, diffuseSha256: frame.diffuseAsset.assetSha256, groups,
    brightestRefinedOnlyExamplesByModelContrast: examples.slice(0, 3)};
}

const engine = new NativeSkyEngine(pack);
try {
  const catalogue = new Map(engine.store.catalogue.stars.map(s => [s.id, s]));
  const result = {
    measurementStage: {
      modelDetectable: 'Physical worker sourceDiagnostics.detectable with complete background and positive altitude.',
      centerRgb: 'Native display encoding of the raster returned by NativeSkyEngine.render, before host acceptance.',
      night: 'Below -20 degrees solar altitude the worker includes the native lunar night presentation.',
      twilightAndDay: 'At and above -20 degrees the host subsequently runs nativeAtmosphereFields and nativeSkyPresentation, which can change center RGB responses.'
    },
    previewLimit, observer, scenes: {}
  };
  for (const [label, utc] of Object.entries(scenes)) {
    result.scenes[label] = await census(engine, catalogue, utc);
  }
  console.log(JSON.stringify(result, null, 2));
} finally {
  engine.dispose();
}
