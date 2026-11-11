'use strict';
// Pure source-branch controls; these do not launch a browser or contact a host.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = __dirname;
const bundlePath = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages/playwright/driver/package/lib/coreBundle.js';
const sourcePath = path.join(root, 'original-candidate/src/native/index.html');
const bundle = fs.readFileSync(bundlePath, 'utf8');
const source = fs.readFileSync(sourcePath, 'utf8');
const digest = text => crypto.createHash('sha256').update(text).digest('hex');
const anchor = 'if (redirectedFrom || !this._userRequestInterceptionEnabled && this._protocolRequestInterceptionEnabled)';
const at = bundle.indexOf(anchor);
assert(at >= 0 && at === bundle.lastIndexOf(anchor), 'Unique Chromium redirect branch');
const start = bundle.lastIndexOf('let route2 = null;', at);
const end = bundle.indexOf('const isNavigationRequest', at);
const branch = bundle.slice(start, end);
const branchFile = path.join(root, 'sdk-chromium-redirect-branch.js');
fs.writeFileSync(branchFile, branch);
const sdkRun = redirectedFrom => {
  const messages = [];
  let routes = 0;
  const context = {
    redirectedFrom,
    requestPausedEvent: {requestId: 'pure-control-id', request: {headers: {}, url: 'https://unapproved.example/test'}},
    requestPausedSessionInfo: {session: {_sendMayFail: (command, params) => messages.push({command, params})}},
    RouteImpl: class {constructor() { routes++; }},
  };
  const fn = vm.runInNewContext('(function(){' + branch + ';return route2;})', context);
  const result = fn.call({_userRequestInterceptionEnabled: true, _protocolRequestInterceptionEnabled: true});
  return {messages, userRouteCreated: result !== null, routes};
};
const initial = sdkRun(null);
const redirected = sdkRun({_originalRequestRoute: {_alreadyContinuedParams: {}}});
assert.equal(initial.userRouteCreated, true);
assert.deepEqual(initial.messages, []);
assert.equal(redirected.userRouteCreated, false);
assert.equal(redirected.messages.length, 1);
assert.equal(redirected.messages[0].command, 'Fetch.continueRequest');

const font = source.match(/function cnFontChanged\(\)\{[^\n]+\}/g);
const loop = source.match(/if\(sec!==_lastSec \|\| _renderDirty\)\{[^\n]+\}/g);
assert.equal(font.length, 1);
assert.equal(loop.length, 1);
const fontContext = {
  _cnFit: 'cached', _renderDirty: false, sec: 1, _lastSec: 1,
  ADVANCING: false, n: {}, painted: 0,
};
fontContext.render = () => { fontContext.painted++; };
vm.createContext(fontContext);
vm.runInContext(font[0], fontContext);
vm.runInContext(loop[0], fontContext);
const withoutWake = fontContext.painted;
vm.runInContext('cnFontChanged();' + loop[0], fontContext);
const withFontCompletion = fontContext.painted;
assert.equal(withoutWake, 0);
assert.equal(withFontCompletion, 1);

const report = {
  scope: 'Pure execution of extracted source branches only. No native frame, model outcome, HTTP request, browser launch, or real provider contact.',
  playwrightVersion: '1.62.0',
  sdk: {path: bundlePath, sha256: digest(bundle), branchSha256: digest(branch)},
  chromiumRedirect: {initial, redirected},
  candidateSource: {path: sourcePath, sha256: digest(source)},
  fontWakeup: {fontSource: font[0], loopSource: loop[0], frozenWithoutDirtyPaints: withoutWake, frozenAfterFontCompletionPaints: withFontCompletion},
};
fs.writeFileSync(path.join(root, 'source-mechanism-results.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
