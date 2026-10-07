// No packages: node tests/v1_storage.cjs. Separate VM and storage for each case.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const code = fs.readFileSync(path.join(__dirname, '../v1/config.js'), 'utf8');
const ROOT = 'salah_widget:config:v1';
const V1 = 'salah_widget:v1:config:v1';
const MARK = 'salah_widget:v1:imported-root-config:v1';
const legacy = JSON.stringify({v:1,lat:24.47,lon:39.61,label:'Saved city',method:'4',school:'0',time:'24',units:'c',source:'manual'});
let passed = 0;
function boot(initial = {}, blocked = false) {
  const data = new Map(Object.entries(initial)), writes = [];
  const storage = {
    getItem(k) { if (blocked) throw new Error('SecurityError'); return data.has(k) ? data.get(k) : null; },
    setItem(k,v) { if (blocked) throw new Error('SecurityError'); writes.push(k); data.set(k,String(v)); },
    removeItem(k) { if (blocked) throw new Error('SecurityError'); writes.push(k); data.delete(k); }
  };
  const window = {localStorage:storage};
  vm.runInNewContext(code, {window, URLSearchParams});
  return {c:window.SalahConfig, data, writes};
}
function test(name, fn) { fn(); passed++; console.log('PASS: ' + name); }
test('valid legacy settings copied once; root remains byte-identical', () => {
  const {c,data,writes} = boot({[ROOT]:legacy, 'salah:old':'prayer', 'salahwx:old':'weather'});
  assert.equal(c.resolve('#local=1').cfg.label, 'Saved city');
  assert.equal(data.get(ROOT), legacy);
  data.set(ROOT, legacy.replace('Saved city','Future root'));
  assert.equal(c.loadLocal().label, 'Saved city');
  assert.ok(writes.every(k => k === V1 || k === MARK));
  assert.equal(data.get('salah:old'), 'prayer');
  assert.equal(data.get('salahwx:old'), 'weather');
});
test('V1 save and clear never modify root or resurrect it', () => {
  const {c,data} = boot({[ROOT]:legacy});
  c.loadLocal(); c.saveLocal({...JSON.parse(legacy),label:'V1 choice'});
  assert.equal(c.loadLocal().label, 'V1 choice');
  c.clearLocal(); assert.equal(c.loadLocal(), null);
  assert.equal(data.get(ROOT), legacy); assert.equal(data.get(MARK), '1');
});
test('reset before initial import also prevents resurrection', () => {
  const {c,data} = boot({[ROOT]:legacy});
  c.clearLocal(); assert.equal(c.loadLocal(), null); assert.equal(data.get(ROOT), legacy);
});
test('existing V1 settings take precedence', () => {
  const {c} = boot({[ROOT]:legacy,[V1]:legacy.replace('Saved city','V1')});
  assert.equal(c.loadLocal().label, 'V1');
});
for (const [name,value] of [['missing',undefined],['malformed','{'],['future schema',legacy.replace('"v":1','"v":2')],['invalid coordinates',legacy.replace('24.47','124.47')]]) {
  test(name + ' root data falls back without repeated imports', () => {
    const {c,data} = boot(value === undefined ? {} : {[ROOT]:value});
    assert.equal(c.loadLocal(), null); data.set(ROOT,legacy);
    assert.equal(c.loadLocal(), null); assert.equal(data.get(MARK), '1');
  });
}
test('blocked storage keeps session fallback usable', () => {
  const {c} = boot({},true);
  assert.equal(c.storageAvailable().ok,false); assert.equal(c.loadLocal(),null);
  assert.equal(c.saveLocal(JSON.parse(legacy)).ok,false);
  assert.equal(c.resolve('#local=1').needsDetect,true);
  assert.equal(c.resolve('#lat=24.47&lon=39.61').cfg.lat,24.47);
});
test('storage probe is V1-only', () => {
  const {c,writes} = boot(); assert.equal(c.storageAvailable().ok,true);
  assert.deepEqual(writes,['__sw_v1_probe__','__sw_v1_probe__']);
});
console.log(`${passed} passed; 0 failed`);
