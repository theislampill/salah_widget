'use strict';
const crypto = require('node:crypto');
const contract = require('./native-script-contract.js');
const { MOON_FILE_BOOTSTRAP, SetupError } = contract;

// The same pure source contract is used by the pre-parser browser wrapper.
// Prerequisite scripts are verified separately; only the native owner is returned.
function nativeInlineRuntime(source) {
  const scripts=contract.parseScripts(source);
  const digests=scripts.map(script=>crypto.createHash('sha256').update(script.body).digest('hex'));
  const sourceSha256=crypto.createHash('sha256').update(source).digest('hex');
  return contract.admitScripts(source,scripts,digests,sourceSha256).native.body;
}
module.exports = { nativeInlineRuntime, MOON_FILE_BOOTSTRAP, SetupError };
