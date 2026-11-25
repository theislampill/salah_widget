/** R0035 analysis only. Isolate one source in an supplied linear sky raster. */
import assert from 'node:assert/strict';
import {renderStars} from '../../real-sky/core/src/renderer.mjs';
import {encodeNativeDisplay} from '../../real-sky/native-host.mjs';

export function sourceCenterResponse(raster, star, flux) {
  // A one-pixel crop of the original pixel-integrated PSF. All neighbouring
  // stars and the background of the supplied raster remain in the full frame.
  const x = Math.floor(star.x), y = Math.floor(star.y);
  assert.ok(x >= 0 && x < raster.width && y >= 0 && y < raster.height);
  const offset = 3 * (y * raster.width + x);
  const center = renderStars([{...star, x: star.x - x, y: star.y - y}], {
    width: 1, height: 1, fluxAt: () => flux
  }).linear;
  const combined = raster.linear.subarray(offset, offset + 3);
  for (let channel = 0; channel < 3; channel++) {
    const totalStar = raster.stellarLinear[offset + channel];
    assert.ok(center[channel] <= totalStar + 1e-12 * Math.max(1, totalStar), 'source PSF exceeds full stellar field');
  }
  const nominal = encodeNativeDisplay(combined, raster.effectiveExposure);
  // These are deterministic sensitivity probes, not the undisclosed candidate
  // amplitudes or an inference about temporal flicker.
  const changes = relative => {
    const shifted = combined.map((value, channel) => value + relative * center[channel]);
    const encoded = encodeNativeDisplay(shifted, raster.effectiveExposure);
    return nominal.some((byte, channel) => byte !== encoded[channel]);
  };
  return {
    contributes: changes(-1),
    responds1pct: changes(0.01) || changes(-0.01),
    responds5pct: changes(0.05) || changes(-0.05)
  };
}
