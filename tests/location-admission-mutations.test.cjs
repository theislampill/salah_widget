'use strict';
// R0026 mutation controls. Each disposable in-memory mutant of the generated config.js, builder.html or settings
// runtime reaches the same real scenario as its healthy run and must fail an actual assertion (setup errors and
// TypeErrors are not detection). No mutated source is written to disk.
const { test } = require('node:test'), assert = require('node:assert/strict');
const L = require('./location-admission-fixture.cjs'), { readSource } = require('./r000f-fixture.cjs');
const sources = { config: L.base.config, builder: readSource('builder.html'), index: readSource('index.html') };
function mutant(file, from, to) {
  assert.equal(sources[file].split(from).length, 2, 'one declared mutation location in ' + file);
  const S = { ...L.base };
  if (file === 'config') S.config = sources.config.replace(from, to);
  else S[file === 'builder' ? 'builderMutate' : 'indexMutate'] = script => { assert.equal(script.split(from).length, 2, 'location reaches the executed script'); return script.replace(from, to); };
  return S;
}
const GUARD_B = 'if(!ownsLookup(owner)) return "superseded";', GUARD_S = 'if(!_ownsSetLookup(owner)) return "superseded";';
const cases = [
  ['m1 restore parseFloat partial acceptance (coarse)', 'config', 'if (!DECIMAL.test(x)) return null; x = parseFloat(x);', 'x = parseFloat(x);', S => L.coarseRejectsPrimary(S, '12abc', '10')],
  ['m1 restore parseFloat partial acceptance (forward)', 'config', 'if (!DECIMAL.test(x)) return null; x = parseFloat(x);', 'x = parseFloat(x);', S => L.nominatimInvalid(S)],
  ['m2 admit via clamping: domain check after clamp', 'config', 'var d = p.parse(j), a = admitCoordinates(d.lat, d.lon);',
    'var d = p.parse(j), a = admitCoordinates(clampN(parseFloat(d.lat), -90, 90), clampN(parseFloat(d.lon), -180, 180));', S => L.coarseRejectsPrimary(S, '999', '999')],
  ['m3 omit Nominatim HTTP gate', 'config', '.then(null, transportFailure).then(httpStage).then(jsonStage).then(function (arr) {', '.then(null, transportFailure).then(jsonStage).then(function (arr) {', S => L.nominatim503(S)],
  ['m4a Zippopotam 404 treated as failure', 'config', 'return r.status === 404 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', 'return jsonStage(httpStage(r));', S => L.zippopotam(S)],
  ['m4b Zippopotam 5xx treated as no-match', 'config', 'return r.status === 404 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', 'return r.status === 404 || r.status >= 500 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', S => L.zippopotam(S)],
  ['m4c Zippopotam HTTP 500 treated as no-match', 'config', 'return r.status === 404 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', 'return r.status === 404 || r.status === 500 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', S => L.zippopotam(S)],
  ['m4d Zippopotam any 4xx treated as no-match', 'config', 'return r.status === 404 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', 'return r.status >= 400 && r.status < 500 ? ZIP_NOT_FOUND : jsonStage(httpStage(r));', S => L.zippopotam(S)],
  ['m5 null latitude coerced to 0', 'config', 'admitCoordinates(p.latitude, p.longitude)', 'admitCoordinates(+p.latitude, +p.longitude)', S => L.zippopotamMissingLatitude(S)],
  ['m6 lose partial-match evidence: partial reported as complete', 'config', 'coverage: !failed ? "complete"', 'coverage: !failed || cands.length ? "complete"', S => L.partialMatches(S)],
  ['m6 lose partial-match evidence in the builder UI', 'builder', 'partial=!!r&&r.coverage==="partial";', 'partial=false;', S => L.uiPartial(S, 'builder')],
  ['m7 failure plus no-match reported as comprehensive no-match', 'config', 'status: cands.length ? "matches" : failed ? "unavailable" : "no-match"', 'status: cands.length ? "matches" : failed === rs.length ? "unavailable" : "no-match"', S => L.emptyPlusFailure(S)],
  ['collapse error into empty', 'config', 'var a = attemptOf(provider, e); return providerResult(provider, a.state, a.reason, []);', 'return providerResult(provider, "no-match", null, []);', S => L.nominatimFailures(S)],
  ['m8 remove late-intent guard: stale error updates the builder form', 'builder', GUARD_B, '', S => L.staleLookup(S, 'builder', 'error')],
  ['m8 remove late-intent guard: stale error updates the settings form', 'index', GUARD_S, '', S => L.staleLookup(S, 'settings', 'error')],
  ['m9 invalid accuracy coerced to 0', 'config', 'return n !== null && n >= 0 ? n : null; }', 'return n !== null && n >= 0 ? n : 0; }', S => L.coarseAccuracy(S, 'abc', null)],
  ['m10 builder geolocation bypasses admission', 'builder', 'const a=window.SalahConfig?SalahConfig.admitCoordinates(pos&&pos.coords&&pos.coords.latitude,pos&&pos.coords&&pos.coords.longitude):{ok:false};',
    'const a={ok:true,lat:+pos.coords.latitude,lon:+pos.coords.longitude};', S => L.builderGeolocation(S)],
  ['m10 SalahConfig.geolocate bypasses admission', 'config', 'a = admitCoordinates(pos && pos.coords && pos.coords.latitude, pos && pos.coords && pos.coords.longitude);',
    'a = { ok: true, lat: pos.coords.latitude, lon: pos.coords.longitude };', S => L.geolocateAdmission(S)],
  ['m11 legacy projection returns a non-array', 'config', '.then(function (r) { return r.candidates; }, function () { return []; });', '.then(function (r) { return r; }, function () { return []; });', S => L.legacyProjection(S)],
  ['m11 legacy projection throws', 'config', '.then(function (r) { return r.candidates; }, function () { return []; });', '.then(function () { throw new Error("projection"); }, function () { return []; });', S => L.legacyProjection(S)],
  ['current UI keeps the old compatibility array (builder)', 'builder', 'r=await SalahConfig.geocodeSearchDetailed(q,{homeCC:bias});',
    'r=await SalahConfig.geocodeSearch(q,{homeCC:bias}).then(c=>({status:c.length?"matches":"no-match",coverage:"complete",candidates:c}));', S => L.uiUnavailable(S, 'builder')],
  ['current UI keeps the old compatibility array (settings)', 'index', 'r=await SalahConfig.geocodeSearchDetailed(q,{homeCC:bias});',
    'r=await SalahConfig.geocodeSearch(q,{homeCC:bias}).then(c=>({status:c.length?"matches":"no-match",coverage:"complete",candidates:c}));', S => L.uiUnavailable(S, 'settings')],
  ['forward deadline abort-only (no terminal outcome)', 'config', 'reject(attemptError("timeout", "deadline")); ac.abort(); }, opts.timeoutMs || 8000);', 'ac.abort(); }, opts.timeoutMs || 8000);', S => L.lateBody(S)],
  ['replace acquiredAt with savedAt', 'config', 'c.v = 1; c.savedAt = Date.now();', 'c.v = 1; c.savedAt = Date.now(); if (c.locationEvidence) c.locationEvidence.acquiredAt = c.savedAt;', S => L.fixAgeSurvivesSave(S)],
];
for (const [name, file, from, to, scenario] of cases) test('R0026 mutation discriminator: ' + name, async t => {
  const S = mutant(file, from, to);
  await scenario(L.base);
  let killedBy = null;
  await assert.rejects(() => scenario(S), error => { killedBy = String(error && error.message).split(/\r?\n/).filter(Boolean)[0].slice(0, 160);
    return error instanceof assert.AssertionError && !/one declared mutation location|location reaches/.test(error.message); }, 'only an actual assertion failure detects the mutant');
  t.diagnostic('killed by assertion: ' + killedBy);
});
