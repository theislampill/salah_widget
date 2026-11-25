'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {measure, assess, expectedOpacity} = require('./r0040-rain-controls.cjs');

test('R0040 permitted and withheld quantities reach distinct particle and opacity sinks', async () => {
  const cells = await measure();
  assert.equal(assess(cells).effect_authority, true);
  for (const lane of ['live', 'sim']) {
    for (const inputAmount of [0, null]) {
      const fabricated = structuredClone(cells);
      const row = fabricated.amounts.find(v => v.lane === lane && v.inputCode === 63 && v.inputAmount === inputAmount);
      Object.assign(row, {quantity: 2, amountState: 'wet', particles: 'on', opacity: '0.605'});
      assert.equal(assess(fabricated).effect_authority, false, 'fabricated wet amount in ' + lane);
    }
  }
  cells.amounts[0] = cells.amounts[1];
  assert.equal(assess(cells).effect_authority, false, 'a duplicate SIM cell cannot stand in for live');
});

test('R0040 reads each published accessible disclosure independently', async () => {
  const fs = require('node:fs');
  const {sourcePath} = require('./weather-no-timetable-fixture.cjs');
  const source = fs.readFileSync(sourcePath, 'utf8');
  const sink = 'wi.setAttribute("aria-label",value.label);';
  assert.equal(source.split(sink).length, 2, 'mutate only the actual header publisher');
  const mutated = source.replace(sink, 'wi.title="Weather unavailable";wi.setAttribute("aria-label",wi.title);');
  const cells = await measure(mutated);
  const wet = cells.amounts.find(v => v.inputCode === 63 && v.inputAmount > 0);
  assert.equal(wet.title, 'Weather unavailable');
  assert.equal(wet.ariaLabel, wet.title);
  assert.match(wet.currentText, /1.25 mm/);
  assert.equal(assess(cells).D11_wet_disclosure, false);
  assert.equal(assess(cells).effect_authority, true, 'publication-only mutation preserves effect permissions');
});

test('R0040 distinguishes both coherent zero policies and rejects contradictory wording', async () => {
  const cells = await measure();
  assert.equal(assess(cells).D11_wet_disclosure, true);
  const zeroRows = cells.amounts.filter(v => v.inputCode === 63 && v.inputAmount === 0);
  for (const category of ['rain', 'overcast']) {
    for (const row of zeroRows) {
      row.category = category;
      row.icon = cells.amounts.find(v => v.lane === row.lane && v.category === category && v.inputAmount !== 0).icon;
      const label = (row.lane === 'live' ? 'Current: Model estimate' : 'Current: SIM weather preview') +
        ' — ' + category + '; no measurable amount; not observed';
      row.title = row.ariaLabel = row.currentText = label;
    }
    assert.equal(assess(cells).D11_zero_lane_agreement, true, 'permitted zero disposition ' + category);
  }
  zeroRows[0].ariaLabel += '; 2 mm';
  assert.equal(assess(cells).D11_zero_lane_agreement, false, 'contradictory published amount in ARIA alone');
});

test('R0040 D3 preserves the live curve and compares equal rates across intervals', () => {
  for (const [quarterHour, hour, expected] of [[0.3, 1.2, '0.440'], [1.25, 5, '0.535'], [3, 12, '0.710']]) {
    assert.equal(expectedOpacity(quarterHour, 900), expected);
    assert.equal(expectedOpacity(hour, 3600), expected);
  }
  assert.equal(expectedOpacity(0.3, 3600), '0.420');
  assert.equal(expectedOpacity(40, 3600), '1.000');
});
