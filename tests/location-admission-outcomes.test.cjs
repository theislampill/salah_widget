'use strict';
// R0026 / issue #68 source controls (ES26-01..17). Scenarios live in location-admission-fixture.cjs (shared with
// location-admission-mutations.test.cjs). Controlled provider replies and geolocation only; no network, no real
// position. ES26-18 and the native half of ES26-12 are qualified separately (tools/qa/run_r0026_native.py).
const { test } = require('node:test');
const fmt = v => Object.is(v, -0) ? '-0' : typeof v === 'number' && !Number.isFinite(v) ? String(v) : JSON.stringify(v);
const L = require('./location-admission-fixture.cjs'), S = L.base;

for (const [lat, lon] of [['999', '999'], ['24.47', '999'], ['-90.5', '10'], ['Infinity', '10'], [Infinity, 10], [['1'], '10'], ['12abc', '10'],
  ['', '10'], ['   ', '10'], [null, '10'], [true, '10'], ['0x10', '10'], ['1e2', '10'], ['24.47 junk', '10'], [{}, '10'], [NaN, '10']])
  test(`ES26-01/05 coarse GeoJS ${fmt(lat)}/${fmt(lon)} is rejected before normalization and the one fallback runs`, () => L.coarseRejectsPrimary(S, lat, lon));
for (const [lat, lon, expected] of [['24.47', '39.61', [24.47, 39.61]], [' 24.47 ', '+39.61', [24.47, 39.61]], ['-33.5', '151.25', [-33.5, 151.25]],
  ['0', '30', [0, 30]], ['30', '0', [30, 0]], ['0', '0', [0, 0]], ['-0', '-0', [-0, -0]], [-0, 0, [-0, 0]], ['90', '180', [90, 180]],
  ['-90', '-180', [-90, -180]], [45.5, -73.25, [45.5, -73.25]], ['.5', '-.5', [0.5, -0.5]]])
  test(`ES26-04/05 coarse GeoJS ${fmt(lat)}/${fmt(lon)} is admitted unchanged`, () => L.coarseAdmits(S, lat, lon, expected));
for (const [loc, expected] of [['51.5,-0.12', [51.5, -0.12]], ['0,-0', [0, -0]], ['999,999', null], ['51.5', null], ['51.5,-0.12,7', null], ['51.5junk,-0.12', null], ['', null]])
  test(`ES26-04/05 coarse ipinfo loc ${JSON.stringify(loc)}`, () => L.coarseIpinfo(S, loc, expected));
test('ES26-02 both coarse providers invalid: explicit failure, bounded attempts, no coordinates', () => L.coarseBothInvalid(S));
for (const [accuracy, expected] of [['5', 5], [5000, 5000], [0, 0], ['abc', null], [NaN, null], [-5, null], ['', null], [null, null], [undefined, null], ['Infinity', null], [true, null]])
  test(`ES26-14/A11 coarse accuracy ${fmt(accuracy)} → ${expected}`, () => L.coarseAccuracy(S, accuracy, expected));
test('A4 coarse attempts are additive, bounded and contain no provider body', () => L.coarseAttemptsBounded(S));

test('ES26-06 Nominatim HTTP 503 with a healthy-looking body is unavailable, not a match', () => L.nominatim503(S));
test('ES26-08 Nominatim 429/network/malformed/non-array/null/timeout are unavailable with their category', () => L.nominatimFailures(S));
test('ES26-07 Nominatim valid empty array is a distinguishable no-match', () => L.nominatimNoMatch(S));
test('ES26-03/05 Nominatim out-of-range, nonfinite, prefix, hex, exponent and non-numeric coordinates are never candidates', () => L.nominatimInvalid(S));
test('ES26-04 forward zero, signed-zero, boundary, trimmed and JSON-number coordinates admitted exactly', () => L.forwardBoundaries(S));
test('A1 Zippopotam 404 is a valid no-match; 500/502/503/400/403/429/network/malformed are failures', () => L.zippopotam(S));
test('A4/A9 partial means provider coverage: rejected items inside a completed provider stay complete, no partial note', () => L.partialIsPerProvider(S));
test('A2 decimal point forms: ".5" admitted, "5." rejected', () => L.decimalPointForms(S));
test('A9 builder tip title carries the full message for no-match, unavailable, partial, invalid position; cleared with the tip', () => L.builderTipTitle(S));
test('ES26-03/05 Zippopotam null/empty/missing latitude is rejected, never coerced to 0', () => L.zippopotamMissingLatitude(S));
test('ES26-09 one provider matches and the other fails: matches with partial coverage and usable candidates', () => L.partialMatches(S));
test('ES26-08 both providers fail: unavailable', () => L.bothFail(S));
test('ES26-10 one no-match plus one failure is not a comprehensive no-match', () => L.emptyPlusFailure(S));
test('A10 dedup keeps order, proximity policy and the surviving provenance; nonfinite never kept', () => L.dedupe(S));
test('ES26-11 short input is not-requested with zero requests', () => L.notRequested(S));
test('ES26-12 abort-ignorant body settles once at the existing deadline; late body/rejection changes nothing', () => L.lateBody(S));
test('ES26-15/A3 legacy geocodeSearch remains an array projection for every outcome', () => L.legacyProjection(S));

test('A5 SalahConfig.geolocate admits browser coordinates before publication; accuracy unknown stays null', () => L.geolocateAdmission(S));
test('A5 builder one-shot geolocation applies the canonical admission before publishing', () => L.builderGeolocation(S));
test('A5 settings precise location rejects invalid browser coordinates', () => L.settingsGeolocation(S));
test('ES26-01/02 builder coarse detection: invalid GeoJS uses the fallback; both invalid fail visibly', () => L.builderCoarse(S));

for (const kind of ['builder', 'settings']) {
  test(`ES26-07/08/16 ${kind}: valid no-match keeps the not-found message`, () => L.uiNoMatch(S, kind));
  test(`ES26-08/16 ${kind}: unavailable search is distinct from not-found and publishes nothing`, () => L.uiUnavailable(S, kind));
  test(`ES26-09/A9 ${kind}: partial coverage keeps usable candidates with a concise note`, () => L.uiPartial(S, kind));
  for (const late of ['success', 'error'])
    test(`ES26-13/A6 ${kind}: stale lookup ${late} cannot update the current form and reports superseded`, () => L.staleLookup(S, kind, late));
}
test('ES26-15/A8 manual, hash and saved normalization still clamp (distinct from external admission)', () => L.manualClampPreserved(S));
test('ES26-14 admitted browser fix keeps its acquisition time and accuracy through save/load', () => L.fixAgeSurvivesSave(S));
