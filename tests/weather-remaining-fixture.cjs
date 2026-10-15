'use strict';
// Reuse the retained source-executing fixture without running or changing its original tests/TODOs.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const Module = require('node:module'), vm = require('node:vm');
const fixturePath = path.join(__dirname, 'r000c-weather.test.cjs');
const fixtureText = fs.readFileSync(fixturePath, 'utf8');
const end = fixtureText.indexOf("test('control: actual fresh acquisition");
assert(end > 0, 'retained WEATHER extraction anchor');
const fixtureModule = new Module(fixturePath, module);
fixtureModule.filename = fixturePath; fixtureModule.paths = Module._nodeModulePaths(__dirname);
fixtureModule._compile(fixtureText.slice(0, end) + '\nmodule.exports={fixture,healthy,NOW,source};', fixturePath);
const { fixture, healthy, NOW, source } = fixtureModule.exports;
const fixed = () => ({ lat:24.47,lon:39.61,source:'hash',locationEvidence:{intent:'fixed-site',source:'hash',accuracyM:null,acquiredAt:null} });
function remainingFixture(options = {}) {
  const f = fixture({config:fixed(),...options});
  // The old generic DOM double creates arbitrary selectors. The new sink exists only if
  // the product's authored markup actually declares it; this is contained DOM evidence.
  const query = f.context.document.querySelector.bind(f.context.document);
  const sink = /<(?:span|div)\b[^>]*\bid="weather-information"[^>]*>/.test(source);
  f.context.document.querySelector = selector => selector === '#weather-information' && !sink ? null : query(selector);
  vm.runInContext(`globalThis.remaining={
    target:currentWeatherTarget,decision:weatherDecision,header:weatherHeader,paintHeader:paintWeatherHeader,
    information:typeof weatherInformation==='function'?weatherInformation:null,
    admit:raw=>admitWeatherFixture(raw,currentWeatherTarget(),Date.now()),
    consume:raw=>{weatherSynthetic=admitWeatherFixture(raw,currentWeatherTarget(),Date.now());return weatherSynthetic;},
    setMode:mode=>{_cfgMode=mode;},
    readSynthetic:()=>weatherSynthetic,
    snapshot:()=>{const decision=weatherDecision();const header=weatherHeader(decision,true);paintWeatherHeader(header);return {decision,header};}
  };`, f.context);
  return Object.assign(f, f.context.remaining);
}
function present(f, changes = {}) {
  const now=f.clock.now, target=f.target();
  return {scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',
    target:{generation:target.generation,lat:target.lat,lon:target.lon},measurementAt:now,retrievedAt:now,
    validFrom:now,validUntil:now+60000,frameAt:now,issuedAt:now,units:'categorical',
    footprint:{kind:'point',coverage:'target',lat:target.lat,lon:target.lon},
    quality:{status:'qualified',sampling:'direct',operationalHealth:'operational',localObservationAt:now},
    present:{state:'wet',type:'rain',lightning:'unavailable',quantity:null},...changes};
}
module.exports={fixture,remainingFixture,healthy,NOW,present,source,vm};
