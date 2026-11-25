'use strict';

// Read publication sinks after the existing contained fixture renders the authored runtime.
// All provider calls end in weather-renewal-fixture's in-memory transport.
const assert = require('node:assert/strict');
const {fixture} = require('./weather-no-timetable-fixture.cjs');
const {provider} = require('./weather-renewal-fixture.cjs');

async function sample({amount, code = 63, windFrom = 270, speed = 8, gust = 8, hash = '', source}) {
  const fetch = provider({code, mutate(_host, body) {
    Object.assign(body.current, {precipitation: amount, rain: amount, showers: 0,
      wind_gusts_10m: gust, wind_speed_10m: speed, wind_direction_10m: windFrom});
    body.hourly.precipitation.fill(amount);
    return body;
  }});
  const host = await fixture({source, hash, fetch});
  const value = host.run(`(() => {
    const decision = weatherDecision(), card = document.querySelector('.c'), icon = document.querySelector('#wi');
    return {
      source: decision.record?.src,
      code: decision.record?.code,
      quantity: decision.model.quantity?.value ?? null,
      rate: decision.model.quantity?.averageRateMmH ?? null,
      amountState: decision.model.state,
      category: card.dataset.fx,
      particles: card.dataset.precip,
      opacity: card.style.getPropertyValue('--rain-op'),
      slant: card.style.getPropertyValue('--rain-slant'),
      icon: icon.textContent,
      currentText: document.querySelector('#weather-information').textContent.split('. Nearby:')[0],
      title: icon.title,
      ariaLabel: icon.getAttribute('aria-label'),
      reason: decision.modelDowngrade,
      observed: decision.observedPresent
    };
  })()`);
  assert.ok(['current', 'forecast', 'sim'].includes(value.source), 'fixture must admit a record');
  assert.ok(/^\d+\.\d+$/.test(value.opacity) && /^-?\d+px$/.test(value.slant), 'missing CSS publication');
  return JSON.parse(JSON.stringify(value));
}

const clamp = value => Math.max(0, Math.min(1, value));
function expectedOpacity(amount, interval) {
  const rate = amount * 3600 / interval;
  return clamp(0.42 + 0.6 * clamp((rate / 4 - 0.1) / 6)).toFixed(3);
}

async function measure(source) {
  const rate = [], wind = [], amounts = [];
  for (const interval of [900, 3600]) {
    for (const amount of [0.3, 1.25, 3, ...(interval === 3600 ? [5] : [])]) {
      const value = await sample({amount, hash: interval === 3600 ? '&timeScale=2' : '', source});
      assert.equal(value.source, interval === 900 ? 'current' : 'forecast');
      assert.equal(value.quantity, amount);
      assert.equal(value.particles, 'on', 'a withdrawn scene cannot test intensity');
      rate.push({interval, amount, expectedRate: amount * 3600 / interval, headerRate: value.rate,
        opacity: value.opacity, expected: expectedOpacity(amount, interval)});
    }
  }

  // Cardinal screen directions from the right axis of a north-clockwise camera.
  // Rows are wind FROM north, east, south, west. Positive CSS displacement is right.
  for (const [azimuth, expected] of [[180, [0, 1, 0, -1]], [90, [1, 0, -1, 0]]]) {
    for (const [i, windFrom] of [0, 90, 180, 270].entries()) {
      const value = await sample({amount: 1.25, windFrom, hash: '&skyAz=' + azimuth, source});
      assert.equal(value.particles, 'on');
      wind.push({azimuth, windFrom, speed: 8, slantPx: parseInt(value.slant, 10), expectedSign: expected[i]});
    }
    const calm = await sample({amount: 1.25, speed: 0, hash: '&skyAz=' + azimuth, source});
    wind.push({azimuth, windFrom: 270, speed: 0, slantPx: parseInt(calm.slant, 10), expectedSign: 0});
  }

  for (const code of [63, 3]) {
    for (const amount of code === 63 ? [1.25, 0, null] : [null]) {
      for (const lane of ['live', 'sim']) {
        const suffix = amount === null ? 'unavailable' : String(amount);
        const hash = lane === 'sim' ? '&simWx=' + code + '&simCloud=95&simPrecip=' + suffix : '';
        const value = await sample({amount, code, hash, source});
        assert.equal(value.source, lane === 'sim' ? 'sim' : 'current');
        amounts.push({lane, inputCode: code, inputAmount: amount,
          simPrecipToken: lane === 'sim' ? suffix : null, ...value});
      }
    }
  }
  const omitted = await sample({amount: null, hash: '&simWx=63&simCloud=95', source});
  return {rate, wind, amounts, simOmitted: {quantity: omitted.quantity, particles: omitted.particles}};
}

function disclosuresMatch(row, category) {
  const wantsRain = category === 'rain';
  const categoryWord = wantsRain ? /\brain\b/i : /\bovercast\b/i;
  const qualification = row.lane === 'live' ? /model estimate/i : /\bSIM\b/i;
  const amount = row.inputAmount === null ? /amount unavailable/i :
    row.inputAmount === 0 ? /(?:\b0(?:\.0+)?\s*mm\b|no measurable amount)/i : /\b1\.25\s*mm\b/i;
  return [row.title, row.ariaLabel, row.currentText].every(text => {
    if (typeof text !== 'string') return false;
    // Forecast text can contain other amounts. Check only the published current section.
    const header = text.split('. Nearby:')[0];
    const current = header.includes('Current:') ? header.slice(header.indexOf('Current:')) : header;
    const quantities = [...current.matchAll(/(\d+(?:\.\d+)?)\s*mm\b(?!\/h)/gi)];
    return quantities.every(match => Number(match[1]) === row.inputAmount) &&
      categoryWord.test(header.split(';')[0]) && categoryWord.test(current.split(';')[0]) &&
      qualification.test(current) && amount.test(current) &&
      /(?:direct local observation unavailable|not observed|unobserved)/i.test(current) &&
      !(wantsRain && /→\s*overcast/i.test(header)) &&
      !(row.inputAmount !== null && /amount unavailable/i.test(current));
  });
}

function assess({rate, wind, amounts}) {
  // Input metadata is independent of the admitted model and the resulting presentation.
  const pair = (code, amount) => {
    const rows = amounts.filter(v => v.inputCode === code && v.inputAmount === amount);
    return rows.length === 2 && ['live', 'sim'].every(lane => rows.some(v => v.lane === lane)) ? rows : [];
  };
  const missing = pair(63, null), wet = pair(63, 1.25), zero = pair(63, 0), dryMissing = pair(3, null);
  const complete = amounts.length === 8 && [missing, wet, zero, dryMissing].every(p => p.length === 2);
  const wetIcon = row => wet.find(p => p.lane === row.lane)?.icon;
  const dryIcon = row => dryMissing.find(p => p.lane === row.lane)?.icon;
  const zeroAgrees = zero.length === 2 && zero[0].category === zero[1].category && zero[0].icon === zero[1].icon;
  return {
    D3: rate.every(v => v.opacity === v.expected),
    D4: wind.every(v => Math.sign(v.slantPx) === v.expectedSign),
    D11_wet_disclosure: complete && wet.every(v => v.category === 'rain' && v.icon &&
      v.icon !== dryIcon(v) && disclosuresMatch(v, 'rain')),
    D11_missing_category: complete && missing.every(v => v.icon === wetIcon(v) && disclosuresMatch(v, 'rain')),
    D11_zero_lane_agreement: complete && zeroAgrees && zero.every(v => {
      // G-5b permits the cover-class disposition or the rain category with no measurable amount.
      const category = v.category;
      return (category === 'rain' && v.icon === wetIcon(v) || category === 'overcast' && v.icon === dryIcon(v)) &&
        disclosuresMatch(v, category);
    }),
    nonrain_missing_stays_unknown: complete && dryMissing.every(v => v.amountState === 'unknown' &&
      v.quantity === null && disclosuresMatch(v, 'overcast')),
    effect_authority: complete && amounts.every(v => {
      const state = v.inputAmount === null ? 'unknown' : v.inputAmount === 0 ? 'dry' : 'wet';
      const permitted = state === 'wet';
      return v.code === v.inputCode && v.quantity === v.inputAmount && v.amountState === state &&
        v.particles === (permitted ? 'on' : 'off') && (permitted ? Number(v.opacity) > 0 : Number(v.opacity) === 0) &&
        v.observed === false;
    })
  };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length > 1 || (args.length && args[0] !== '--check')) throw Error('usage: node tests/r0040-rain-controls.cjs [--check]');
  measure().then(cells => {
    const checks = assess(cells);
    console.log(JSON.stringify({evidence: 'authored runtime, simulated provider and DOM, no browser pixels', checks, cells}, null, 2));
    if (args.includes('--check') && Object.values(checks).includes(false)) process.exitCode = 1;
  }).catch(error => { console.error(error); process.exitCode = 2; });
}
module.exports = {sample, measure, assess, expectedOpacity};
