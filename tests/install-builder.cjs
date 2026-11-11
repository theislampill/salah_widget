/* Actual builder/serializer command preservation; no network or real installer. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const builder = fs.readFileSync(path.join(root, 'src/native/builder.html'), 'utf8');
const config = fs.readFileSync(path.join(root, 'src/native/config.js'), 'utf8');
function actual(name) {
  const start = builder.indexOf('function ' + name + '(');
  assert(start >= 0, 'Actual function absent: ' + name);
  const body = builder.slice(start);
  const end = body.indexOf('\n}');
  const first = body.indexOf('\n');
  return body.slice(0, body.slice(0, first).endsWith('}') ? first : end + 2);
}
const fields = {lat:'24.47',lon:'39.61',label:"O'Hare & $(printf INJECTION_CONTROL) <script>مدينة</script> \\ line",
  method:'4',school:'0',time:'24',units:'c',appearance:'glass',dfcode:'YYYY-MM-DD'};
const ctx = {URLSearchParams, navigator:{platform:'Linux'}, fields};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(config, ctx);
vm.runInContext('const $=id=>({value:fields[id]}); let builderLocation=null, embedMode="portable"; const base="https://theislampill.github.io/salah_widget/"; const INSTALL_REPO="theislampill/salah_widget";\n' +
  ['formConfig','hash','url','snippet','installCmd'].map(actual).join('\n'), ctx);
const results = [];
function check(name, fn) { try { fn(); results.push({case:name,pass:true}); } catch(e) { results.push({case:name,pass:false,error:e.message}); } }
check('portable hostile-looking Unicode label roundtrip', () => {
  const hash = vm.runInContext('hash()', ctx);
  assert.equal(new URLSearchParams(hash).get('label'), fields.label);
  assert(!hash.includes("'"), 'single quote escaped by actual serializer');
  const command = vm.runInContext('installCmd()', ctx);
  assert(command.carry);
  assert(command.cmd.includes("| SALAH_WIDGET_HASH='" + hash + "' bash"));
  const run = cp.spawnSync(process.env.SALAH_TEST_BASH || '/bin/bash', ['--noprofile','--norc','-c',
    String.raw`curl(){ printf '%s\n' 'printf "%s" "$SALAH_WIDGET_HASH"'; }; eval "$INSTALL_TEST_COMMAND"`],
    {env:{...process.env,INSTALL_TEST_COMMAND:command.cmd},encoding:'utf8'});
  assert.equal(run.status, 0, run.stderr);
  assert.equal(run.stdout, hash, 'actual pipeline delivers exact hash to Bash process');
});
check('local command omits coordinates and retains explicit preferences', () => {
  vm.runInContext('embedMode="local"', ctx);
  const hash = vm.runInContext('hash()', ctx), params = new URLSearchParams(hash);
  assert.equal(params.get('local'), '1');
  for (const name of ['lat','lon','label']) assert(!params.has(name), name + ' leaked into local command');
  assert.equal(params.get('method'), '4');
  assert.equal(params.get('units'), 'c');
  const snippet = vm.runInContext('snippet()', ctx);
  assert(snippet.includes('allow="geolocation"'));
  assert(snippet.includes('width:325px;height:530px'));
});
check('Windows command retains canonical serializer output', () => {
  ctx.navigator.platform = 'Win32';
  vm.runInContext('embedMode="portable"', ctx);
  const hash = vm.runInContext('hash()', ctx);
  const command = vm.runInContext('installCmd()', ctx).cmd;
  assert.equal(command, "$env:SALAH_WIDGET_HASH='" + hash + "'; irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex");
});
check('plain local default does not invent carried preferences', () => {
  vm.runInContext('hash=()=>"local=1"', ctx);
  const output = vm.runInContext('installCmd()', ctx);
  assert.equal(output.carry, false);
  assert(!output.cmd.includes('SALAH_WIDGET_HASH'));
});
console.log(JSON.stringify({source:{builder:crypto.createHash('sha256').update(builder).digest('hex'),config:crypto.createHash('sha256').update(config).digest('hex')},results},null,2));
process.exit(results.some(r=>!r.pass)?1:0);
