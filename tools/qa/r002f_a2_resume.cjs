'use strict';
// This VM observes task and callback state. It has no browser presentation boundary.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {harness, record, configSha256} = require('../../tests/r0003-harness.cjs');

const TARGETS = {current: '.cn', next: '.nt', countdown: '.left', gregorian: '#ce', hijri: '#ah'};
const FIELDS = Object.freeze(Object.keys(TARGETS));
const sep7 = '2026-09-07 CE', sep8 = '2026-09-08 CE';
const hijri25 = 'ه 1448-02-25 | moon 26', hijri26 = 'ه 1448-02-26';
function prayer(current, next, countdown, gregorian, hijri) {
  return Object.freeze({current, next, countdown, gregorian, hijri});
}

// Independent display expectations for the fixed UTC fixture. Countdown minutes
// truncate; the Hijri day advances at Maghrib. The unavailable row has two real dash values.
const beforeFajr = prayer('Isha', '05:00', '30s left until Fajr', sep7, hijri25);
const afterFajr = prayer('Fajr', '06:00', '58m left until Sunrise', sep7, hijri25);
const SCENARIOS = Object.freeze([
  {name:'fajr', before:'2026-09-07T04:59:30Z', initial:beforeFajr, expected:afterFajr},
  {name:'maghrib', before:'2026-09-07T17:59:30Z',
    initial:prayer('Asr', '18:00', '30s left until Maghrib', sep7, hijri25),
    expected:prayer('Maghrib', '19:30', '1h 28m left until Isha', sep7, hijri26)},
  {name:'midnight', before:'2026-09-07T23:59:30Z',
    initial:prayer('Isha', '05:00', '5h 0m left until Fajr', sep7, hijri26),
    expected:prayer('Isha', '05:00', '4h 58m left until Fajr', sep8, hijri26)},
  {name:'within-prayer', before:'2026-09-07T12:05:00Z',
    initial:prayer('Dhuhr', '15:30', '3h 25m left until Asr', sep7, hijri25),
    expected:prayer('Dhuhr', '15:30', '3h 23m left until Asr', sep7, hijri25)},
  {name:'missing-next-day', before:'2026-09-07T23:59:30Z', next:false,
    initial:prayer('Isha', '—', 'Countdown unavailable', sep7, 'Sunset date update unavailable ه 1448-02-25'),
    expected:prayer('—', '—', 'Prayer times unavailable', 'Gregorian date unavailable', 'stale Hijri date unavailable')},
  {name:'moon-fault', before:'2026-09-07T04:59:30Z', moonFault:true, initial:beforeFajr, expected:afterFajr}
].map(s => Object.freeze({...s, gapMs:120000})));

const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const fileSha = relative => sha(fs.readFileSync(path.resolve(__dirname, relative)));
const plain = s => String(s ?? '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

function requireAuthoredTargets(source) {
  // The shared recording DOM creates unknown class selectors on demand. Count
  // actual body owners first, excluding comments, raw text and template contents.
  const tags = /<!--[\s\S]*?-->|<(script|style|textarea|title|noscript)\b[^>]*>[\s\S]*?<\/\1\s*>|<(\/?)([\w:-]+)\b((?:"[^"]*"|'[^']*'|[^"'<>])*)>/gi;
  const attributes = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
  const counts = new Map(Object.values(TARGETS).map(selector => [selector, 0]));
  let inBody = false, templates = 0;
  for (const [, , closing, tagName, rawAttributes] of source.matchAll(tags)) {
    if (!tagName) continue;
    const tag = tagName.toLowerCase();
    if (tag === 'body') inBody = !closing;
    if (!inBody) continue;
    if (tag === 'template') templates += closing ? -1 : 1;
    if (closing || templates) continue;
    const attrs = new Map();
    for (const [, name, double, single, bare] of rawAttributes.matchAll(attributes)) {
      const key = name.toLowerCase();
      if (!attrs.has(key)) attrs.set(key, double ?? single ?? bare ?? '');
    }
    for (const selector of counts.keys()) {
      const match = selector[0] === '#' ? attrs.get('id') === selector.slice(1) :
        (attrs.get('class') || '').split(/\s+/).includes(selector.slice(1));
      if (match) counts.set(selector, counts.get(selector) + 1);
    }
  }
  for (const [selector, count] of counts) {
    assert.equal(count, 1, 'expected one authored observation target ' + selector + ', found ' + count);
  }
}

function snapshot(h) {
  const state = {};
  for (const [field, selector] of Object.entries(TARGETS)) {
    const node = h.nodes.get(selector);
    const ownsSelector = selector[0] === '#' ? node?.id === selector.slice(1) :
      node?.classList.contains(selector.slice(1));
    assert.ok(ownsSelector, 'incomplete DOM observation: ' + selector);
    state[field] = plain(node.innerHTML || node.textContent);
  }
  return state;
}

function comparePrayer(observed, expected) {
  for (const field of FIELDS) {
    for (const sample of [observed, expected]) {
      if (typeof sample?.[field] !== 'string' || !sample[field].trim()) {
        throw Error('incomplete prayer observation: ' + field);
      }
    }
  }
  return FIELDS.filter(field => observed[field] !== expected[field]);
}

function fixtureRecord(day) {
  const value = record(day, 'UTC', 'R002F-A2 synthetic calendar');
  const hd = day === '07-09-2026' ? '25' : '26';
  const hm = String(value.date.hijri.month.number).padStart(2, '0');
  value.date.hijri = {...value.date.hijri, day:hd, date:hd + '-' + hm + '-' + value.date.hijri.year};
  return value;
}

function fixture(source, scenario) {
  const h = harness({source, epoch:scenario.before});
  h.seed(fixtureRecord('07-09-2026'), scenario.next === false ? null : fixtureRecord('08-09-2026'));
  h.run('var _wxDecisionCache=null;window.__resumeMoon=[];window.__resumeThrow=false;'
    + 'window.SalahMoonRuntime={request(){__resumeMoon.push({prayer:document.querySelector(".cn").textContent});if(__resumeThrow)throw new Error("injected resume Moon failure");},surface(){return null},observe(){return {state:{}}}};');
  return h;
}

// A whole-render measurement control; it has no performance qualification.
function synchronousRenderControl(source) {
  const needle = 'if(resumed){ try{ window.SalahMoonRuntime?.request(); updateSkySurface(); }catch(e){ recordRenderFault("moon-resume",e); } } }';
  if (source.split(needle).length !== 2) throw Error('expected exactly one resume owner for the positive control');
  return source.replace(needle, 'if(resumed){ runRenderStage("resume-prayer-day-control",maintainPrayerDay); runRenderStage("resume-render-control",render); try{ window.SalahMoonRuntime?.request(); updateSkySurface(); }catch(e){ recordRenderFault("moon-resume",e); } } }');
}

async function observeReturn(source, s, repeat) {
  const h = fixture(source, s);
  h.run('render();startRenderLoop();');
  const before = snapshot(h);
  assert.deepEqual(comparePrayer(before, s.initial), [], s.name + ' pre-hide fixture differs');
  const framesBeforeHide = h.frames.size;
  assert.equal(framesBeforeHide, 1, 'one callback before hide');
  h.hide();
  const framesWhileHidden = h.frames.size;
  assert.equal(framesWhileHidden, 0, 'no pending callback while hidden');
  h.elapse(s.gapMs);
  h.run('window.__resumeThrow=' + !!s.moonFault + ';');
  const themeBeforeReturn = h.paints.length;
  const moonRequestsBeforeReturn = h.run('__resumeMoon.length');
  const faultCount = () => h.run('_renderFaults.get("moon-resume")?.count || 0');
  const faultsBeforeReturn = faultCount();
  h.show();
  const afterTask = snapshot(h);
  const themeCallsInReturnTask = h.paints.length - themeBeforeReturn;
  const framesQueuedOnReturn = h.frames.size;
  assert.equal(framesQueuedOnReturn, 1, 'one callback queued on return');
  const moonSeen = JSON.parse(h.run('JSON.stringify(__resumeMoon)')).slice(moonRequestsBeforeReturn);
  assert.equal(moonSeen.length, 1, 'one Moon request in the restoring task');
  const moonFaults = faultCount() - faultsBeforeReturn;
  assert.equal(moonFaults, Number(!!s.moonFault), 'Moon resume fault count in restoring task');
  if (s.moonFault) {
    assert.equal(h.run('_renderFaults.get("moon-resume").last.message'), 'injected resume Moon failure');
  }
  const callbacksExecuted = await h.frame();
  assert.equal(callbacksExecuted, 1, 'one return callback executed');
  const framesAfterCallback = h.frames.size;
  assert.equal(framesAfterCallback, 1, 'one successor callback queued');
  const afterFirstCallback = snapshot(h);
  return {
    scenario:s.name, repeat, beforeUtc:s.before, afterUtc:new Date(Date.parse(s.before) + s.gapMs).toISOString(),
    hiddenMs:s.gapMs, before, expected:s.expected, framesBeforeHide, framesWhileHidden, framesQueuedOnReturn,
    callbacksExecuted, framesAfterCallback, themeCallsInReturnTask, moonSeen, moonFaults,
    afterTask:{state:afterTask, differences:comparePrayer(afterTask, s.expected), painted:false},
    afterFirstCallback:{state:afterFirstCallback, differences:comparePrayer(afterFirstCallback, s.expected), painted:false}
  };
}

async function runMatrix({source, repeats=5, scenarios=SCENARIOS}={}) {
  if (typeof source !== 'string' || !source) throw Error('source required');
  if (!Number.isInteger(repeats) || repeats < 1 || repeats > 20) throw Error('repeats must be 1..20');
  requireAuthoredTargets(source);
  const rows = [];
  for (const s of scenarios) {
    for (let repeat = 1; repeat <= repeats; repeat++) rows.push(await observeReturn(source, s, repeat));
  }
  return {
    schema:'r002f-a2-resume-source/2', scope:'source-state VM; no browser or paint timing',
    sourceSha256:sha(source), fixtureSha256:fileSha('../../tests/r0003-harness.cjs'),
    recordingDocumentSha256:fileSha('../../tests/r0002-harness.cjs'), observerSha256:fileSha(__filename),
    configSha256, prayerFixtureSha256:fileSha('../../tests/r0002-ordinary.json'), repeats, rows,
    summary:{observations:rows.length, taskEndDifferent:rows.filter(r => r.afterTask.differences.length).length,
      firstCallbackDifferent:rows.filter(r => r.afterFirstCallback.differences.length).length},
    limitations:['Visibility and DOM are boundary doubles; the native loop and prayer-selection/publication functions are source-bound.',
      'All five pre-hide and return expectations are independently specified for each synthetic UTC scenario.',
      'Repeats are deterministic fixture repetitions, not independent hardware/browser trials.',
      'configSha256 binds the config text executed by the VM, including any SALAH_REQUEST_CONFIG override.',
      'A callback is not a presented frame; no screenshot, bfcache, real tab return, dispatch duration or human judgment is claimed.',
      'The whole-render positive control is test-only and is not an approved production correction.']
  };
}

async function main(args) {
  const sourcePath = path.resolve(args[0] || path.join(__dirname, '../../index.html'));
  const out = args[1];
  if (!out) throw Error('usage: node tools/qa/r002f_a2_resume.cjs <generated index.html> <new output.json> [--require-current]');
  const source = fs.readFileSync(sourcePath, 'utf8');
  const baseline = await runMatrix({source});
  const positiveControl = await runMatrix({source:synchronousRenderControl(source)});
  fs.writeFileSync(path.resolve(out), JSON.stringify({baseline, positiveControl}, null, 2) + '\n', {flag:'wx'});
  console.log(JSON.stringify({baseline:baseline.summary, positiveControl:positiveControl.summary, scope:baseline.scope}));
  if (args.includes('--require-current') && (baseline.summary.taskEndDifferent || baseline.summary.firstCallbackDifferent)) {
    process.exitCode = 1;
  }
}
module.exports = {FIELDS, SCENARIOS, comparePrayer, snapshot, synchronousRenderControl, runMatrix};
if (require.main === module) main(process.argv.slice(2)).catch(e => {console.error('INCOMPLETE: ' + e.stack);process.exitCode = 2;});
