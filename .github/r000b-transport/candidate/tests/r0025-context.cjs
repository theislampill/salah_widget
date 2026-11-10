// Real whole runtime; gradient/arc/noise observations are boundary commands,
// never native pixels, cloud hashes or elapsed browser-motion qualification.
const assert=require('node:assert/strict');
const {load,prayerForDate}=require('./r001d-harness.cjs');
function cloudFixture(options={}){
  const h=load(options),trace=[],noise=[],cv=h.select('.cloudcanvas');cv.width=144;cv.height=232;
  Object.assign(cv.ctx,{clearRect(){trace.length=0;noise.length=0;},beginPath(){},arc(){},fill(){},
    createRadialGradient(...geometry){const entry={geometry,stops:[]};trace.push(entry);return {addColorStop(...stop){entry.stops.push(stop);}};}});
  h.ctx.__noiseTrace=noise;
  h.run('globalThis.__realCloudNoise=_vn3;_vn3=function(x,y,z){__noiseTrace.push([x,y,z]);return __realCloudNoise(x,y,z);};');
  // Explicit setup publication after a test finalizes its intended clock. UTC
  // seeks may request corresponding synthetic prayer bundles through the real
  // admission owner; painting/stepping never repairs setup or rewrites a receipt.
  function publish({admitPrayerDay=false}={}){
    if(admitPrayerDay){
      for(const day of [h.run('prayerCivilDay()'),h.run('prayerNextDay(prayerCivilDay())')]){
        h.ctx.__fixtureCloudPrayer=prayerForDate(day);
        assert.equal(h.run('adoptPrayerBundle(__fixtureCloudPrayer,__fixtureCloudPrayer.date.gregorian.date,null,true,false)'),true,'actual prayer bundle admission for the selected fixture day');
      }
      delete h.ctx.__fixtureCloudPrayer;
    }
    assert.equal(h.run('model()!==null'),true,'motion setup requires the actual current prayer model');
    h.run('render()');
    assert.equal(h.run('cloudPublicationReceipt().state'),'eligible-published','motion setup requires a complete cloud publication');
    assert.equal(h.run('cloudPublicationCurrent(cloudPublicationReceipt())'),true,'motion setup must publish under its final clock and mode');
  }
  h.run('__fixtureWeatherCurrent.cloud_cover=50;__fixtureWeatherCurrent.cloud_cover_low=25;__fixtureWeatherCurrent.cloud_cover_mid=50;__fixtureWeatherCurrent.cloud_cover_high=22;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});');
  publish();
  const snapshot=()=>({trace:JSON.parse(JSON.stringify(trace)),noise:JSON.parse(JSON.stringify(noise)),columns:h.run('Array.from(_colDens||[])'),state:h.run('({...cloudState})')});
  function paint(){h.run('paintClouds(simNow()/1000)');return snapshot();}
  function step(ms){h.clock.now+=ms;h.clock.wall+=ms;return paint();}
  return Object.assign(h,{trace,noise,snapshot,paint,step,publish});
}
module.exports={cloudFixture};
