'use strict';
// R0028 (ISM-BLD-005): structural check of docs/state-contracts/CLOSURE_INDEX.md. Offline and
// read-only; the comment bodies themselves are re-read by tools/qa/r0028_closure_readback.py.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const INDEX = 'docs/state-contracts/CLOSURE_INDEX.md';

function section(text, heading) {
  const start = text.indexOf('\n## ' + heading + '\n');
  assert.ok(start >= 0, 'index section ' + heading);
  const end = text.indexOf('\n## ', start + 1);
  return text.slice(start, end < 0 ? text.length : end);
}
function rows(text, heading) {
  const lines = section(text, heading).split('\n').filter(line => line.startsWith('| '));
  const header = lines[0].split('|').slice(1, -1).map(cell => cell.trim());
  return lines.slice(1).map(line => {
    // Cells may contain code spans with pipes only inside double-backtick quotes; split on " | ".
    const cells = line.slice(2, -2).split(' | ').map(cell => cell.trim());
    assert.equal(cells.length, header.length, 'row shape: ' + line);
    return Object.fromEntries(header.map((key, index) => [key, cells[index]]));
  });
}
const unquote = cell => cell.replace(/^``\s?/, '').replace(/\s?``$/, '');

function check(indexText, read = file => fs.readFileSync(path.join(root, file), 'utf8')) {
  const certificates = rows(indexText, 'Certificates');
  const superseded = rows(indexText, 'Superseded contract lines');
  rows(indexText, 'Withdrawals, corrections and reopenings');
  rows(indexText, 'Acceptance bases that are not fresh observations');
  const finals = new Map();
  for (const row of certificates) {
    assert.match(row.WO, /^R[0-9A-F]{4}$/);
    assert.match(row.Comment, /^\d{8,}$/);
    if (row['Bound commit'] !== '-') assert.match(row['Bound commit'], /^[0-9a-f]{40}$/);
    if (row.Kind === 'FINAL') {
      assert.notEqual(row['Bound commit'], '-', 'FINAL certificate must carry its bound commit: ' + row.WO);
      finals.set(row.Contract, row);
    }
  }
  const covered = new Set();
  for (const row of superseded) {
    const lines = read(row.Contract).split(/\r?\n/), number = Number(row.Line);
    assert.ok(Number.isInteger(number) && number >= 1, 'line number ' + row.Line);
    assert.equal(lines[number - 1], unquote(row['Quoted line']), row.Contract + ':' + number + ' quoted line must still match');
    assert.match(row['Superseded by'], /FINAL \d{8,}/);
    covered.add(row.Contract + ':' + number);
  }
  for (const contract of finals.keys()) {
    read(contract).split(/\r?\n/).forEach((line, index) => {
      if (/wholeContractComplete/.test(line) && /\bremains\s+false\b|:\s*false\b/.test(line))
        assert.ok(covered.has(contract + ':' + (index + 1)),
          contract + ':' + (index + 1) + ' says wholeContractComplete is false but its FINAL certificate ' +
          finals.get(contract).Comment + ' has no supersession row');
    });
  }
  return {finals: finals.size, superseded: superseded.length};
}

const indexText = fs.readFileSync(path.join(root, INDEX), 'utf8');

test('closure index: every FINAL-certified contract false-completion line is superseded by a quoted row', () => {
  const result = check(indexText);
  assert.ok(result.finals >= 1 && result.superseded >= 3);
});

test('closure index: deleting the R0015 supersession row is detected', () => {
  const row = indexText.split('\n').find(line => line.startsWith('| docs/state-contracts/R0015.md | 450 |'));
  assert.ok(row, 'R0015 line 450 supersession row present');
  assert.throws(() => check(indexText.replace(row + '\n', '')), /R0015\.md:450 says wholeContractComplete is false/);
});

test('closure index: a stale quotation of a contract line is detected', () => {
  const row = indexText.split('\n').find(line => line.startsWith('| docs/state-contracts/R0015.md | 221 |'));
  assert.throws(() => check(indexText.replace(row, row.replace('| 221 |', '| 222 |'))), /quoted line must still match/);
});

test('closure index: a new false-completion sentence in a FINAL-certified contract is detected', () => {
  const read = file => fs.readFileSync(path.join(root, file), 'utf8') +
    (file === 'docs/state-contracts/R0015.md' ? '\n`wholeContractComplete` remains false (appended control).\n' : '');
  assert.throws(() => check(indexText, read), /has no supersession row/);
});

test('closure index: the R0007 owner-approved reuse basis is indexed', () => {
  const reuse = rows(indexText, 'Acceptance bases that are not fresh observations');
  const row = reuse.find(entry => entry.WO === 'R0007');
  assert.ok(row && /reuse/.test(row.Basis) && /6787290418/.test(row.Locator) && /42953929662/.test(row.Rows));
});
