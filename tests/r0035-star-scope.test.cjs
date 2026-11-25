const test = require('node:test');
const assert = require('node:assert/strict');

test('R0035 one-star center estimate matches full rerenders with an overlapping star and a nonuniform sky', async () => {
  const {sourceCenterResponse} = await import('../tools/r0035/center_signal.mjs');
  const {renderStars, encodeFrame} = await import('../real-sky/core/src/renderer.mjs');
  const width = 9, height = 6, exposure = 3;
  const background = Float64Array.from({length: width * height * 3}, (_, i) => (1 + i % 17) / 1400);
  const observations = [];
  for (const [x, y] of [[0.01, 0.02], [3.51, 3.85], [8.99, 5.98]]) {
    for (const intensity of [0, 0.0003, 0.007, 0.091, 0.82]) {
      const target = {id: 'target', altDeg: 30, x, y, rgb: [intensity, intensity / 2, intensity / 4]};
      const neighbour = {id: 'neighbour', altDeg: 30, x: x + 0.17, y: y - 0.19, rgb: [0.4, 0.06, 0.15]};
      const scene = factor => {
        const {linear: stellarLinear} = renderStars([target, neighbour], {width, height,
          fluxAt: star => ({rgb: star.rgb.map(v => v * (star.id === 'target' ? factor : 1))})});
        return {width, height, effectiveExposure: exposure, stellarLinear,
          linear: stellarLinear.map((v, i) => v + background[i])};
      };
      const pixel = factor => {
        const bytes = encodeFrame(scene(factor).linear, exposure);
        const start = 4 * (Math.floor(y) * width + Math.floor(x));
        return [...bytes.subarray(start, start + 3)];
      };
      const original = pixel(1);
      const differs = factor => pixel(factor).some((v, i) => v !== original[i]);
      const expected = {contributes: differs(0), responds1pct: differs(1.01) || differs(0.99),
        responds5pct: differs(1.05) || differs(0.95)};
      assert.deepEqual(sourceCenterResponse(scene(1), target, {rgb: target.rgb}), expected);
      observations.push(expected);
    }
  }
  // Exercise both sides of each quantisation test, including positive removal
  // with brightening/dimming still below one RGB code.
  for (const key of ['contributes', 'responds1pct', 'responds5pct']) {
    assert.deepEqual(new Set(observations.map(row => row[key])), new Set([true, false]));
  }
  assert.ok(observations.some(row => row.contributes && !row.responds5pct));
});
