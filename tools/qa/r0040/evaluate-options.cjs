'use strict';

// Run on the patched authored source in a disposable checkout, before the builder.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {measure, assess, sample} = require('../../../tests/r0040-rain-controls.cjs');
const {fixture} = require('../../../tests/weather-no-timetable-fixture.cjs');
const {scene, B} = require('../../../tests/weather-renewal-fixture.cjs');
if (process.argv.length !== 3) throw Error('usage: node evaluate-options.cjs PATCHED_AUTHORED_INDEX');
const template = fs.readFileSync(process.argv[2], 'utf8');
const bind = options => template.replace('const rainExperiment =', 'window.__R0040_OPTIONS__=' + JSON.stringify(options) + ';\nconst rainExperiment =');
const option = {missing:'category',zero:'category',eyeLevel:0.8,cap:null,gust:'unused',night:'none',reduced:'none'};
const expected = {0.8:[23,47,65,18,40,59,16,36,56],1:[28,53,69,23,46,64,20,42,61]};
async function magnitudes(source, k) {
  const rows = [];
  for (const rate of [1.2,5,12]) for (const speed of [2,5,10]) {
    const {slant} = await sample({amount:rate/4, windFrom:90, speed, source});
    const measured = Math.atan2(parseInt(slant),142)*180/Math.PI;
    const target = expected[k][rows.length];
    rows.push({rate,speed,measured,target,within3deg:Math.abs(measured-target)<=3});
  }
  return rows;
}
async function main() {
  const policies = [], physical = [];
  for (const missing of ['category','cover']) for (const zero of ['category','cover']) {
    const cells = await measure(bind({...option,missing,zero}));
    const checks = assess(cells);
    assert.deepEqual(Object.values(checks).filter(v=>!v),[]);
    const missingRows = cells.amounts.filter(r => r.inputCode === 63 && r.inputAmount === null);
    assert.ok(missingRows.every(r=>r.category === (missing==='cover'?'overcast':'rain')));
    const zeroRows = cells.amounts.filter(r => r.inputCode === 63 && r.inputAmount === 0);
    assert.ok(zeroRows.every(r=>r.category === (zero==='cover'?'overcast':'rain')));
    assert.equal(cells.simOmitted.quantity,2);
    policies.push({missing,zero,checks,missingScene:missingRows[0].category,zeroScene:zeroRows[0].category});
  }
  for (const eyeLevel of [0.8,1]) {
    const rows = await magnitudes(bind({...option,eyeLevel}),eyeLevel);
    assert.ok(rows.every(r=>r.within3deg)); physical.push({eyeLevel,rows});
  }
  const mutant = bind(option).replace('const angle=Math.atan2', 'const angle=0.5*Math.atan2');
  const ordinal = await magnitudes(mutant,0.8);
  assert.ok(ordinal[2].measured > ordinal[5].measured && ordinal[5].measured > ordinal[8].measured);
  assert.ok(ordinal.some(r=>!r.within3deg));
  const profiles=[];
  for (const gust of ['unused','model']) {
    const source=bind({...option,gust,cap:55});
    const h=await fixture({source,hash:'&simWx=63&simPrecip=5&simWind=20&simWindDir=90'});
    const inspect=gustValue=>JSON.parse(JSON.stringify(h.run(`Array.from({length:301},(_,i)=>rainGeometry({code:63,wind:5,windDir:90,gust:${gustValue}},5,"rain",i*100))`)));
    const spread=a=>Math.max(...a)-Math.min(...a);
    const nullTrace=inspect('null'), same=inspect(5), strong=inspect(20);
    assert.equal(spread(nullTrace),0); assert.deepEqual(same,nullTrace);
    if(gust==='model')assert.ok(spread(strong)>10);else assert.deepEqual(strong,same);
    assert.ok(Math.max(...strong)<=55);
    const [slant, axis] = h.run(`["--rain-slant","--rain-axis"].map(p=>parseFloat(document.querySelector('.c').style.getPropertyValue(p)))`);
    assert.ok(Math.abs(Math.atan2(slant,142)*180/Math.PI+axis)<0.3);
    assert.ok(Math.abs(axis)<=55);
    profiles.push({gust,cap:55,span30sDegrees:spread(strong),axis,slant});
  }
  const styles=[];
  for (const night of ['none','environment']) for(const reduced of ['none','still']){
    const h=await fixture({source:bind({...option,night,reduced}),reduced:true,hash:'&simWx=63&simMoon=0&simMoonAlt=-20'});
    for(const sun of [-20,-5,30]){
      h.run(`window.SalahNativeSkyHost.cloudLighting=()=>({sun:{altDeg:${sun},azDeg:90},utcMs:simNow(),sample:()=>null});render()`);
      const state=h.run(`(()=>{const c=document.querySelector('.c');return {lit:c.dataset.rainLit,reduced:c.dataset.rainReduced,color:c.style.getPropertyValue('--rain-color')};})()`);
      assert.equal(state.lit,sun>=0||night==='environment'&&sun>=-12?'on':'off');
      assert.equal(state.reduced,reduced);
      if(sun<0)assert.match(state.color,/^rgba\(/);
      styles.push({sun,night,...state});
    }
  }
  const expiry=[];
  for(const [code,precipitation] of [[63,1.25],[65,3]]){
    const h=await scene({source:bind(option),code,precipitation,frame:50,phaseMs:10000,
      fail:host=>host.clock.wall>=B});
    const frames=await h.run(B+500);
    const last=frames.filter(f=>f.t<=0&&f.sel).at(-1);
    const after=frames.filter(f=>f.t>0);
    const correct=rows=>rows.length>0&&rows.every(f=>!f.sel&&f.precip==="off"&&f.lightning==="off");
    assert.ok(last&&last.precip==="on"&&correct(after));
    assert.ok(!correct([{...after[0],precip:"on"},...after.slice(1)]));
    expiry.push({code,rate:precipitation*4,lastWetMs:last.t,firstWithheldMs:after[0].t,
      checkedThroughMs:after.at(-1).t,afterExpiryMutantRejected:true});
  }
  console.log(JSON.stringify({expiry,evidence:'Research variant running in synthetic DOM. No browser pixels.',policies,physical,ordinalMutantRejected:ordinal.some(r=>!r.within3deg),profiles,styles},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1});
