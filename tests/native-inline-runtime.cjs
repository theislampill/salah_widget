'use strict';
const assert = require('node:assert/strict');
const MOON_FILE_BOOTSTRAP = 'if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;';

// The Moon donor adds exactly this file-transport initializer. Keep rejecting
// unknown/duplicate inline scripts while extracting the unchanged native owner.
function nativeInlineRuntime(source) {
  const scripts = Array.from(source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g), m => m[1]).filter(s => s.trim());
  const loaders = scripts.filter(s => s.trim() === MOON_FILE_BOOTSTRAP);
  assert.ok(loaders.length <= 1, 'Duplicate Moon file initializer');
  const native = scripts.filter(s => s.trim() !== MOON_FILE_BOOTSTRAP);
  assert.equal(native.length, 1, 'Expected exactly one native inline runtime');
  assert.equal(native[0].split('\nboot();').length, 2, 'Expected the real boot caller');
  return native[0];
}
module.exports = { nativeInlineRuntime, MOON_FILE_BOOTSTRAP };
