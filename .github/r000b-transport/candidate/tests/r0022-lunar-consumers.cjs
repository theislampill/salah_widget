const assert=require('node:assert/strict');
const fs=require('node:fs');
const {load,sha}=require('./r001d-harness.cjs');
const sourcePath=process.argv[2]?.startsWith("--")?undefined:process.argv[2];
let pass=0,fail=0;
const cp8SnapshotOnly=process.argv.includes("--cp8-snapshot-only"),cp8Synthetic=new Set(["glints release wash with held star projection", "ordinary render refreshes star appearance while held projection stays fixed"]);
function test(name,fn){if(cp8SnapshotOnly&&cp8Synthetic.has(name)){console.log("SKIP_SUPERSEDED",name,"— real catalogue/physical compositor replaces synthetic arrays; see CP8 tests");return;}try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
function fixture(){return load({sourcePath});}
// Ordinary elapsed time holds geometry; editing _simBase deliberately seeks the
// explicit preview and now correctly invalidates its accepted projection.
function ordinaryFixture(){return load({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia%2FRiyadh&units=c&seed=1&simMoon=.5&simWax=1&simMoonAlt=20&simMoonH=42'});}
function zeroConsumers(h,reason){
  const light=h.run('qaState().moonTruth.lunarLight');assert.equal(light.eligible,false);assert.equal(light.eligibility,0);assert.equal(light.reason,reason);
  for(const key of ['illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'])assert.equal(light[key],0,key);
}

for(const [name,patch] of [['near-new','SIM.moon="0.01"'],['below-horizon','SIM.moon="1";SIM.moonAlt="-10"'],['daylight','SIM.moon="1";_simBase=Date.parse("2026-09-08T09:30:00Z")']]){
  test(name+' has zero atmospheric lunar consumers after actual paint',()=>{
    const h=fixture();h.run(patch+';render();');
    assert.equal(+h.select('.c').style.getPropertyValue('--moonbeam'),0,'physical beam');
    assert.equal(+h.select('.c').style.getPropertyValue('--mhalo'),0,'halo leak');
    assert.equal(+h.select('.c').style.getPropertyValue('--mcorona'),0,'corona leak');
    assert.equal(+h.select('.c').style.getPropertyValue('--mparhelia'),0,'paraselenae leak');
    assert.equal(+h.select('.mglow').style.getPropertyValue('--mgo'),0,'local atmospheric glow leak');
    assert.equal(h.run('cloudState.moonLit'),0,'cloud light');
    zeroConsumers(h,name);
    if(name!=='daylight'){
      assert.equal(+h.select('.c').style.getPropertyValue('--moongrp'),1,'calendar presence');
      assert.equal(+h.select('.c').style.getPropertyValue('--moonocc'),1,'calendar occlusion');
      assert.equal(+h.select('.c').style.getPropertyValue('--moonfeat'),1,'PBR surface');
    }
  });
}
for(const fraction of ['0.08','0.5','0.92','1'])test('eligible '+fraction+' preserves differentiated thin-high-cloud light',()=>{
  const h=fixture(); h.run('SIM.moon="'+fraction+'";render();');
  assert.equal(h.run('weatherEligibility(weather).eligible'),true,'accepted model input');
  assert.ok(h.run('selectedWeather()')!=null);
  assert.ok(+h.select('.c').style.getPropertyValue('--moonbeam')>0);
  assert.ok(+h.select('.c').style.getPropertyValue('--mhalo')>0);
  assert.equal(+h.select('.c').style.getPropertyValue('--mcorona'),0);
  assert.equal(+h.select('.c').style.getPropertyValue('--moongrp'),1);
});
for(const [name,patch] of [['missing source','weather.currentValidAt=null'],['expired source','weather.currentValidAt-=900001'],
  ['expired receipt','weather.retrievedAt-=900001'],['missing interval','weather.currentIntervalSec=null']])
  test(name+' cannot supply weather-dependent lunar optics',()=>{
    const h=fixture();h.run('SIM.moon="1";'+patch+';render();');
    assert.equal(h.run('weatherEligibility(weather).eligible'),false);assert.equal(h.run('selectedWeather()'),null);
    for(const p of ['--mhalo','--mcorona','--mparhelia'])assert.equal(+h.select('.c').style.getPropertyValue(p),0,p);
    assert.ok(+h.select('.c').style.getPropertyValue('--moonbeam')>0,'accepted geometry still supplies physical lunar beam');
    assert.equal(+h.select('.c').style.getPropertyValue('--moongrp'),1,'opaque calendar presence survives unavailable weather');
  });
test('fresh model input recovers lunar optical conditions after source expiry',()=>{
  const h=fixture();h.run('SIM.moon="1";render();globalThis.__healthyWx={...weather};');
  assert.ok(+h.select('.c').style.getPropertyValue('--mhalo')>0);
  h.run('weather.currentValidAt-=900001;render();');assert.equal(+h.select('.c').style.getPropertyValue('--mhalo'),0);
  h.run('weather=__healthyWx;render();');assert.equal(h.run('weatherEligibility(weather).eligible'),true);
  assert.ok(+h.select('.c').style.getPropertyValue('--mhalo')>0);
});
test('glints release wash with held star projection',()=>{
  const h=ordinaryFixture();assert.equal(h.run('FOLLOW_WALL_CLOCK'),true);h.run('SIM.moon="1";render();');
  const positions=h.run('JSON.stringify(_glintEls.map(e=>e.getAttribute("transform")))');
  const washed=h.run('JSON.stringify(_glintEls.map(e=>e.style.opacity))');
  h.clock.wall+=60000;h.clock.now+=60000;h.run('SIM.moon="0.01";render();');
  assert.equal(h.run('JSON.stringify(_glintEls.map(e=>e.getAttribute("transform")))'),positions);
  assert.notEqual(h.run('JSON.stringify(_glintEls.map(e=>e.style.opacity))'),washed);
});
test('physical zero does not alter the opaque PBR calendar raster',()=>{
  const h=fixture();h.run('_mAlb=new Uint8ClampedArray(_MTW*_MTH*4).fill(150);_mNrm=new Uint8ClampedArray(_MTW*_MTH*4).fill(128);_pbrReady=true;SIM.moon="0.01";render();');
  assert.equal(h.run('_moonOut.data[(150*300+150)*4+3]'),255);
  assert.ok(h.run('_moonOut.data[(150*300+150)*4]')>0,'ashen surface remains, not black');
  assert.equal(+h.select('.c').style.getPropertyValue('--moonfeat'),1);
});
for(const optic of ['lunarhalo','paraselene'])test('forced '+optic+' cannot bypass physical-zero permission',()=>{
  const h=load({sourcePath,extraHash:'&debugOptic='+optic});h.run('SIM.moon="0.01";render();');zeroConsumers(h,'near-new');
});
for(const [name,low,mid,high,humidity,wantHalo,wantCorona] of [
  ['clear',0,0,0,55,false,false],['thin ice',0,8,28,55,true,false],['droplet',0,30,0,80,false,true],['overcast',100,100,100,55,false,false]]){
  for(const waxing of ['1','0'])test(name+' retains distinct optics and opaque phase, wax='+waxing,()=>{
    const h=fixture();h.run('SIM.moon="0.92";SIM.wax="'+waxing+'";weather.cloudLow='+low+';weather.cloudMid='+mid+';weather.cloudHigh='+high+';weather.rh='+humidity+';render();');
    assert.equal(+h.select('.c').style.getPropertyValue('--mhalo')>0,wantHalo);
    assert.equal(+h.select('.c').style.getPropertyValue('--mcorona')>0,wantCorona);
    assert.equal(+h.select('.c').style.getPropertyValue('--moongrp'),1);
    assert.equal(h.select('.mfeatures').getAttribute('transform'),null);
  });
}
test('low eligible moon retains rare lateral paraselenae distinct from droplet corona',()=>{
  const h=fixture();h.run('SIM.moon="1";SIM.moonAlt="5";render();');
  assert.ok(+h.select('.c').style.getPropertyValue('--mparhelia')>0);assert.equal(+h.select('.c').style.getPropertyValue('--mcorona'),0);
});
test('ordinary render refreshes star appearance while held projection stays fixed',()=>{
  const h=ordinaryFixture();assert.equal(h.run('FOLLOW_WALL_CLOCK'),true);h.run('SIM.moon="1";render();');
  const before=h.run('JSON.stringify(_starEls.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")]))');
  const bright=h.run('JSON.stringify(_starEls.map(e=>e.style.opacity))');
  h.clock.wall+=60000;h.clock.now+=60000;h.run('SIM.moon="0.01";render();');
  assert.equal(h.run('JSON.stringify(_starEls.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")]))'),before);
  assert.notEqual(h.run('JSON.stringify(_starEls.map(e=>e.style.opacity))'),bright,'held projector retained previous moon wash');
});
const h=fixture(); console.log(JSON.stringify({sourcePath:h.sourcePath,sourceSha256:h.sourceHash,fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'VM consumption controls; no pixel/texture/motion/cost proof'}));
process.exitCode=fail?1:0;
