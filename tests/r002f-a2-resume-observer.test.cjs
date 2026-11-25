'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const {SCENARIOS, comparePrayer, runMatrix, synchronousRenderControl} = require('../tools/qa/r002f_a2_resume.cjs');
const repo = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(repo, 'index.html'), 'utf8');
const expected = SCENARIOS[0].expected;
const first = {repeats:1, scenarios:[SCENARIOS[0]]};

function replaceOnce(entry, from, to) {
  assert.equal(entry.split(from).length, 2, 'test control requires a unique anchor: ' + from);
  return entry.replace(from, () => to);
}

// Replay selected pre-hide DOM values after the whole restoring listener has
// returned, even on a candidate that already performs its own synchronous refresh.
function replayHiddenFields(entry, selectors) {
  const registration = 'document.addEventListener("visibilitychange",setVis);';
  return replaceOnce(entry, registration, `
    const targets = ${JSON.stringify(selectors)}.map(s => document.querySelector(s));
    let saved;
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") saved = targets.map(node => node.innerHTML);
      setVis();
      if (document.visibilityState === "visible") targets.forEach((node, i) => { node.innerHTML = saved[i]; });
    });`);
}

test('R2FA2-O1: every prayer field contributes to the freshness verdict', () => {
  assert.deepEqual(comparePrayer(expected, expected), []);
  for (const field of Object.keys(expected)) {
    assert.deepEqual(comparePrayer({...expected, [field]:'stale'}, expected), [field]);
  }
});

test('R2FA2-O2: absent, empty and whitespace-only data cannot count as current', () => {
  assert.throws(() => comparePrayer(null, expected), /incomplete/i);
  for (const field of Object.keys(expected)) {
    for (const value of [undefined, '', '   ']) {
      const bad = {...expected, [field]:value};
      assert.throws(() => comparePrayer(bad, expected), /incomplete/i);
      assert.throws(() => comparePrayer(expected, bad), /incomplete/i);
    }
  }
});

test('R2FA2-O3: the positive control requires a unique resume owner', () => {
  assert.throws(() => synchronousRenderControl(''), /one resume/i);
  assert.throws(() => synchronousRenderControl(source + source), /one resume/i);
  assert.notEqual(synchronousRenderControl(source), source);
});

test('R2FA2-O4: every candidate callback restores the five fixture outputs in a source-state observation', async () => {
  const report = await runMatrix({source, repeats:1});
  assert.equal(report.scope, 'source-state VM; no browser or paint timing');
  assert.equal(report.rows.length, 6);
  for (const row of report.rows) {
    assert.deepEqual(row.afterFirstCallback.differences, [], row.scenario);
    assert.deepEqual([row.framesBeforeHide, row.framesWhileHidden, row.framesQueuedOnReturn,
      row.callbacksExecuted, row.framesAfterCallback], [1, 0, 1, 1, 1]);
    assert.equal(row.afterTask.painted, false);
    assert.equal(row.afterFirstCallback.painted, false);
  }
});

test('R2FA2-O5: the synchronous control meets all fixture outputs, including unavailable and fault rows', async () => {
  const {rows} = await runMatrix({source:synchronousRenderControl(source), repeats:1});
  for (const row of rows) {
    assert.deepEqual(row.afterTask.differences, [], row.scenario);
    assert.deepEqual(row.afterFirstCallback.differences, [], row.scenario);
    assert.equal(row.moonFaults, Number(row.scenario === 'moon-fault'));
    assert.equal(row.moonSeen.length, 1);
  }
  assert.ok(rows.every(r => Number.isInteger(r.themeCallsInReturnTask) && r.themeCallsInReturnTask >= 0));
});

test('R2FA2-O6: replaying all pre-hide fields after a working refresh is detected in every scenario', async () => {
  const faulty = replayHiddenFields(synchronousRenderControl(source), ['.cn', '.nt', '.left', '#ce', '#ah']);
  const {rows} = await runMatrix({source:faulty, repeats:1});
  for (const row of rows) {
    assert.deepEqual(row.afterTask.state, row.before);
    assert.ok(row.afterTask.differences.length, row.scenario);
  }
});

test('R2FA2-O7: a current prayer name cannot mask replayed countdown and calendar fields', async () => {
  const faulty = replayHiddenFields(synchronousRenderControl(source), ['.nt', '.left', '#ce', '#ah']);
  const {rows} = await runMatrix({source:faulty, repeats:1});
  for (const row of rows) assert.equal(row.afterTask.state.current, row.expected.current);
  assert.ok(rows.find(r => r.scenario === 'fajr').afterTask.differences.includes('countdown'));
  assert.ok(rows.find(r => r.scenario === 'maghrib').afterTask.differences.includes('hijri'));
  assert.ok(rows.find(r => r.scenario === 'midnight').afterTask.differences.includes('gregorian'));
});

test('R2FA2-O8: all five authored owners must exist once, including class selectors', async () => {
  for (const attr of ['class="cn"', 'class="nt"', 'class="left"', 'id="ce"', 'id="ah"']) {
    // Only this markup occurrence is the published target. A comment is not an owner.
    const target = new RegExp('<(?:div|span)\\b[^>]*? ' + attr + '[^>]*>');
    const match = source.match(target);
    assert.ok(match, attr);
    const missing = replaceOnce(source, match[0], '<!--' + match[0] + '--><div>');
    const duplicate = replaceOnce(source, match[0], '<div ' + attr + '></div>' + match[0]);
    await assert.rejects(runMatrix({source:missing, ...first}), /authored observation target.*found 0/);
    await assert.rejects(runMatrix({source:duplicate, ...first}), /authored observation target.*found 2/);
  }
});

test('R2FA2-O9: a malformed or empty next-time publisher cannot validate itself', async () => {
  const publish = '$(".nt").textContent=time;';
  for (const wrong of ['99:77', '']) {
    // Corrupt only the return value, keeping the pre-hide fixture valid.
    const replacement = '$(".nt").textContent=time === "06:00" ? ' + JSON.stringify(wrong) + ' : time;';
    const faulty = replaceOnce(synchronousRenderControl(source), publish, replacement);
    if (!wrong) {
      await assert.rejects(runMatrix({source:faulty, ...first}), /incomplete prayer observation: next/);
    } else {
      const {rows:[row]} = await runMatrix({source:faulty, ...first});
      assert.deepEqual(row.afterTask.differences, ['next']);
      assert.deepEqual(row.afterFirstCallback.differences, ['next']);
    }
  }
});

test('R2FA2-O10: missing, duplicate or uncancelled callbacks invalidate an otherwise current sample', async () => {
  const current = synchronousRenderControl(source);
  const schedule = 'if(on) start(); else stop();';
  for (const [fault, error] of [
    ['if(on && !resumed) start(); else stop();', /one callback queued on return/],
    ['if(on) { start(); if(resumed) requestAnimationFrame(()=>{}); } else stop();', /one callback queued on return/],
    ['if(on) start();', /no pending callback while hidden/]
  ]) {
    await assert.rejects(runMatrix({source:replaceOnce(current, schedule, fault), ...first}), error);
  }
  const requeue = 'if(_wanted) _raf=requestAnimationFrame(loop);';
  await assert.rejects(runMatrix({source:replaceOnce(current, requeue, ''), ...first}), /one successor callback queued/);
});

test('R2FA2-O11: missing Moon dispatch or misclassified injected faults invalidate the row', async () => {
  const request = 'window.SalahMoonRuntime?.request(); updateSkySurface(); }catch(e){ recordRenderFault("moon-resume",e);';
  const drop = replaceOnce(source, request, request.replace('window.SalahMoonRuntime?.request(); ', ''));
  await assert.rejects(runMatrix({source:drop, ...first}), /one Moon request/);
  const fault = replaceOnce(source, 'recordRenderFault("moon-resume",e);', 'recordRenderFault("other",e);');
  await assert.rejects(runMatrix({source:fault, repeats:1, scenarios:[SCENARIOS.at(-1)]}), /Moon resume fault count/);
});

test('R2FA2-O12: the receipt hashes the executed config override and both recording harnesses', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'r002f-a2-config-'));
  t.after(() => fs.rmSync(dir, {recursive:true, force:true}));
  const file = path.join(dir, 'config.js');
  fs.writeFileSync(file, fs.readFileSync(path.join(repo, 'config.js'), 'utf8') + '\n// alternate test input\n');
  const script = `
    const {runMatrix, SCENARIOS} = require('./tools/qa/r002f_a2_resume.cjs');
    const source = require('node:fs').readFileSync('index.html', 'utf8');
    runMatrix({source, repeats:1, scenarios:[SCENARIOS[0]]}).then(r => {
      console.log(JSON.stringify([r.configSha256, r.fixtureSha256, r.recordingDocumentSha256]));
    });`;
  const printed = execFileSync(process.execPath, ['-e', script], {cwd:repo, encoding:'utf8',
    env:{...process.env, SALAH_REQUEST_CONFIG:file}});
  const digest = name => crypto.createHash('sha256').update(fs.readFileSync(name)).digest('hex');
  assert.notEqual(digest(file), digest(path.join(repo, 'config.js')));
  assert.deepEqual(JSON.parse(printed), [file, path.join(__dirname, 'r0003-harness.cjs'),
    path.join(__dirname, 'r0002-harness.cjs')].map(digest));
});
