'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const {createHash} = require('node:crypto');
const zlib = require('node:zlib');
const {execFileSync} = require('node:child_process');
const {auditNamed, auditSource} = require('../tools/qa/r0040/parameter-audit.cjs');
const evidence = path.join(__dirname, '../docs/state-contracts/evidence/R0040');
const unpack = file => zlib.gunzipSync(fs.readFileSync(path.join(evidence, file)));

function change(source, before, after) {
  assert.equal(source.split(before).length, 2, 'control requires one occurrence: ' + before);
  return source.replace(before, after);
}

test('R0040 parameter inventory binds executable caps, thresholds and both research source versions', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'r0040-parameters-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const qa = path.join(root, 'tools/qa');
  fs.mkdirSync(qa, {recursive: true});
  const fixture = JSON.parse(unpack('parameter-source-fixture.json.gz'));
  for (const name of ['precip_models.js', 'precip_declared_gain.json', 'precip_models_geom.js']) {
    fs.writeFileSync(path.join(qa, name), fixture[name]);
  }
  const geometry = fixture['precip_models_geom.js'];
  const receipt = JSON.parse(fs.readFileSync(path.join(evidence, 'parameter-inventory.json')));
  for (const [design, patch] of [['historical', 'declared-gain.patch.gz'], ['revised', 'layer-study.patch.gz']]) {
    execFileSync('git', ['apply', '--whitespace=nowarn', '--include=tools/qa/precip_models.js', '--include=tools/qa/precip_declared_gain.json', '-'], {cwd: root, input: unpack(patch)});
    const source = fs.readFileSync(path.join(qa, 'precip_models.js'), 'utf8');
    // Initialise the original IIFE through its normal injected-profile entry.
    // There is no animation callback or raster in this declaration-only probe.
    const profileBytes = fs.readFileSync(path.join(qa, 'precip_declared_gain.json'));
    assert.equal(createHash('sha256').update(profileBytes).digest('hex'), receipt.profileSha);
    const profile = JSON.parse(profileBytes);
    const window = {__PM_PARAMS: profile};
    const element = () => ({style: {}, querySelector: () => null, insertBefore() {}, getContext: () => ({})});
    const document = {head: {appendChild() {}}, querySelector: element, getElementById: element, createElement: element};
    vm.runInNewContext(source, {window, document, URLSearchParams, location: {hash: ''}, requestAnimationFrame() {}});
    const params = window.__PM.params;
    assert.deepEqual(auditNamed(params), receipt.named);
    assert.throws(() => auditNamed({...params, render: {...params.render, alphaCap: 0.9}}), /render differs/);
    assert.throws(() => auditNamed({...params, undocumentedLift: 2}), /unclassified undocumentedLift/);
    assert.deepEqual(auditSource(source, geometry, design), receipt.sources[design]);
    const controls = [
      ['Math.min(0.9,G*4', 'Math.min(0.89,G*4', /^texture-alpha:/],
      ['alpha<0.01||x<-60', 'alpha<0.02||x<-60', /^near-clip:/],
      ['/(2*36)', '/(2*16)', /^field-grid:/],
      ['opt.cap||600', 'opt.cap||599', /^near-budget:/],
      ["MODEL==='M3'){if(st){rec.veil=veilLayer(In,Rg,fld,1)", "MODEL==='M3'){if(st){rec.veil=veilLayer(In,Rg,fld,2)", /^veil:/],
      ["MODEL==='M4'){if(st){rec.veil=veilLayer(In,Rg,null,1)", "MODEL==='M4'){if(st){rec.veil=veilLayer(In,Rg,null,2)", /^veil:/],
      ['vy*(fr-0.5)*CY/1000', 'vy*(fr-0.25)*CY/1000', /^near-budget:/],
      ['zMean:(zA+zB)/2*0.8', 'zMean:(zA+zB)/2*0.9', /^texture-motion:/]
    ];
    if (design === 'revised') controls.push(
      ['peak>=2?col.map', 'peak>2?col.map', /^cloud-support:/],
      ['value\/peak>0.16', 'value\/peak>=0.16', /^cloud-support:/],
      ['D<1?0:D<2?1:2', 'D<1.1?0:D<2?1:2', /^texture-dispersion:/]
    );
    for (const [before, after, expected] of controls) {
      const mutant = change(source, before, after);
      assert.throws(() => auditSource(mutant, geometry, design),
        error => expected.test(error.message), 'requires value-specific diagnosis, before the digest check: ' + before);
    }
    assert.throws(() => auditSource(source, change(geometry, 'rt:[Math.cos(a),-Math.sin(a),0]',
      'rt:[Math.cos(a),-Math.sin(a),0.2]'), design), error => /^projection:/.test(error.message));
    assert.throws(() => auditSource(source + '\n// independent identity control', geometry, design), /renderer identity/);
  }
});
