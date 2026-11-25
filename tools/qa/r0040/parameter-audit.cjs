'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const read = name => fs.readFileSync(path.join(__dirname, name), 'utf8');
const digest = text => crypto.createHash('sha256').update(text).digest('hex');
const named = JSON.parse(read('parameter-ledger.json'));
const table = read('inline-parameters.tsv');
const inline = table.trimEnd().split('\n').slice(1).map(line => {
  const columns = line.split('\t');
  assert.ok(columns.length === 7 && columns.every(Boolean), 'incomplete inline declaration: ' + columns[0]);
  const [id, effective, unit, classification, owner, basis, expressions] = columns;
  return {id, effective, unit, classification, owner, basis, expressions: expressions.split(' ~~ ')};
});
assert.equal(new Set(inline.map(row => row.id)).size, inline.length, 'duplicate inline declaration');

function auditNamed(params) {
  const actual = JSON.parse(JSON.stringify(params));
  const expected = Object.fromEntries(named.map(row => [row.name, row.value]));
  for (const name of new Set([...Object.keys(expected), ...Object.keys(actual)])) {
    assert.ok(Object.hasOwn(expected, name) && Object.hasOwn(actual, name), 'missing or unclassified ' + name);
    assert.deepEqual(actual[name], expected[name], name + ' differs from the declared study');
  }
  return {namedParameters: named.length, matched: Object.keys(actual).length};
}

// Both pinned programs use single-line // comments only. Exclude the P defaults
// from the expression search: live Object.assign results have their own audit.
function executable(text) {
  return text.replace(/\/\/[^\r\n]*/g, '').replace(/const P=Object\.assign\(\{[\s\S]*?\},window\.__PM_PARAMS\|\|\{\}\);/, '');
}

function auditSource(source, geometry, design) {
  assert.ok(['historical', 'revised'].includes(design), 'explicit source design required');
  const pins = JSON.parse(read('pins-' + design + '.json'));
  const modelCode = executable(source);
  const geomCode = executable(geometry);
  let declarations = 0, expressions = 0;
  for (const row of inline) {
    let applicable = false;
    for (const binding of row.expressions) {
      const tag = binding.match(/^([GRH])@/);
      if ((tag?.[1] === 'R' && design === 'historical') || (tag?.[1] === 'H' && design === 'revised')) continue;
      const code = tag?.[1] === 'G' ? geomCode : modelCode;
      const declaration = tag ? binding.slice(2) : binding;
      const countPrefix = declaration.match(/^(\d+)× /);
      const expectedCount = countPrefix ? Number(countPrefix[1]) : 1;
      const expression = declaration.slice(countPrefix?.[0].length ?? 0);
      const actualCount = code.split(expression).length - 1;
      assert.equal(actualCount, expectedCount, row.id + ': executable occurrence count for ' + expression);
      applicable = true;
      expressions++;
    }
    if (applicable) declarations++;
  }
  // Unlisted code edits and new branches require reinspection, even if they keep
  // all the checked expressions intact. Diagnose concrete value drift first.
  const rendererSha = digest(source), geometrySha = digest(geometry);
  assert.equal(rendererSha, pins.rendererSha, design + ' renderer identity');
  assert.equal(geometrySha, pins.geometrySha, 'research geometry identity');
  return {design, declarations, expressions, rendererSha, geometrySha,
    namedLedgerSha: digest(read('parameter-ledger.json')), inlineLedgerSha: digest(table)};
}
module.exports = {auditNamed, auditSource};
