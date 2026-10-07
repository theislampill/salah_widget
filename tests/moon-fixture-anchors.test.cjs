'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const { nativeInlineRuntime, MOON_FILE_BOOTSTRAP } = require('./native-inline-runtime.cjs');
const runtime = 'function boot(){}\nboot();', script = value => `<script>${value}</script>`;
test('native fixture admits the exact Moon transport initializer', () => {
  assert.equal(nativeInlineRuntime(script(runtime) + script(MOON_FILE_BOOTSTRAP)), runtime);
  assert.equal(nativeInlineRuntime(script(runtime)), runtime);
});
test('native fixture refuses an unknown inline script or altered Moon initializer', () => {
  for (const value of ['window.unreviewed=true;', MOON_FILE_BOOTSTRAP + 'window.unreviewed=true;'])
    assert.throws(() => nativeInlineRuntime(script(runtime) + script(value)), /exactly one native/);
});
test('native fixture refuses duplicate Moon initializers and duplicate boot owners', () => {
  assert.throws(() => nativeInlineRuntime(script(runtime) + script(MOON_FILE_BOOTSTRAP).repeat(2)), /Duplicate Moon/);
  assert.throws(() => nativeInlineRuntime(script(runtime).repeat(2)), /exactly one native/);
});
