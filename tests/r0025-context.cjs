// Real whole runtime; gradient/arc/noise observations are boundary commands,
// never native pixels, cloud hashes or elapsed browser-motion qualification.
const {load}=require('./r001d-harness.cjs');
function cloudFixture(options={}){
  const h=load(options),trace=[],noise=[],cv=h.select('.cloudcanvas');cv.width=144;cv.height=232;
  Object.assign(cv.ctx,{clearRect(){trace.length=0;noise.length=0;},beginPath(){},arc(){},fill(){},
    createRadialGradient(...geometry){const entry={geometry,stops:[]};trace.push(entry);return {addColorStop(...stop){entry.stops.push(stop);}};}});
  h.ctx.__noiseTrace=noise;
  h.run('globalThis.__realCloudNoise=_vn3;_vn3=function(x,y,z){__noiseTrace.push([x,y,z]);return __realCloudNoise(x,y,z);};');
  h.run('__fixtureWeatherCurrent.cloud_cover=50;__fixtureWeatherCurrent.cloud_cover_low=25;__fixtureWeatherCurrent.cloud_cover_mid=50;__fixtureWeatherCurrent.cloud_cover_high=22;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});render();');
  const snapshot=()=>({trace:JSON.parse(JSON.stringify(trace)),noise:JSON.parse(JSON.stringify(noise)),columns:h.run('Array.from(_colDens||[])'),state:h.run('({...cloudState})')});
  function paint(){h.run('paintClouds(simNow()/1000)');return snapshot();}
  function step(ms){h.clock.now+=ms;h.clock.wall+=ms;return paint();}
  return Object.assign(h,{trace,noise,snapshot,paint,step});
}
module.exports={cloudFixture};
