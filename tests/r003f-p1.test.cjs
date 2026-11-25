'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {buildMasks, measure, lightness, calendarLightVerdict, compareCards, assertOwnerScene, assertOwnerMeasurement} = require('../tools/qa/r003f_p1.cjs');

function fixture(dpr=1) {
  const width = 325*dpr, count = width*530*dpr, disc = {cx:268.8,cy:55.8,r:49.6};
  const newMoon = new Uint8Array(4*count), reference = new Uint8Array(4*count), candidate = new Uint8Array(4*count);
  for (let i=0; i<count; i++) {
    const x = (i%width+0.5)/dpr, y = (Math.floor(i/width)+0.5)/dpr;
    const inside = Math.hypot(x-disc.cx,y-disc.cy)<disc.r, lit = inside && x>=disc.cx;
    for (const [image,code] of [[newMoon,10],[reference,lit?128:10],[candidate,lit?64:inside?10:32]]) {
      image.fill(code,4*i,4*i+3); image[4*i+3]=255;
    }
  }
  return {dpr,disc,offsetDisc:disc,fraction:0.5,newMoon,reference,candidate,
    headerRects:[[160,20,220,39]],topIsSkyOrMoon:new Uint8Array(count).fill(1)};
}
const decode = c => c/255<=0.04045 ? c/255/12.92 : ((c/255+0.055)/1.055)**2.4;
for (const dpr of [1,2]) {
  test('P1 fixed reference mask and corner annulus at DPR '+dpr, () => {
    const f = fixture(dpr), masks = buildMasks(f), m = measure(masks,f.candidate);
    assertOwnerMeasurement(m);
    assert.ok(m.litPixels>100 && m.darkPixels>100);
    assert.ok(m.sky.count>=600*dpr*dpr);
    assert.equal(m.sky.elementExclusion,true);
    assert.ok(Math.abs(m.deltaLitSkyL-(lightness(decode(64))-lightness(decode(32))))<1e-9);
    assert.ok(Math.abs(m.deltaPhysicalCandidateL-(lightness(decode(128))-lightness(decode(64))))<1e-9);
    // Deliberately place the lit mask on uniform sky. A mask that ignores the
    // supplied reference indices would keep measuring the bright half-disc.
    const skyIndices = masks.sky.map(p=>p.i);
    const displaced = measure({...masks,lit:skyIndices},f.candidate);
    assert.ok(Math.abs(displaced.deltaLitSkyL)<1e-9);
    assert.deepEqual(m.sky.octantRangeL.map(Math.round), [Math.round(lightness(decode(32))),Math.round(lightness(decode(32)))]);
    for (const {i} of masks.sky) {
      const x = (i%(325*dpr)+0.5)/dpr, y=(Math.floor(i/(325*dpr))+0.5)/dpr;
      assert.ok(x>=8 && y>=8 && x<317 && y<522);
      assert.ok(!(x>=158 && x<222 && y>=18 && y<41));
    }
  });
}
test('P1 extends the annulus before dropping hit-test exclusions, then reports short sky separately', () => {
  const f=fixture();
  for (let i=0; i<f.topIsSkyOrMoon.length; i++) {
    const radius=Math.hypot(i%325+0.5-f.disc.cx,Math.floor(i/325)+0.5-f.disc.cy)/f.disc.r;
    f.topIsSkyOrMoon[i]=Number(radius>1.3);
  }
  let m=measure(buildMasks(f),f.candidate);
  assert.ok(m.sky.outerRadius>1.3 && m.sky.elementExclusion);
  f.topIsSkyOrMoon.fill(0);
  m=measure(buildMasks(f),f.candidate);
  assert.ok(m.sky.outerRadius===1.6 && !m.sky.elementExclusion && m.sky.count>=600);
  f.headerRects=[[0,0,325,530]];
  m=measure(buildMasks(f),f.candidate);
  assert.equal(m.sky.count,0);
  assert.equal(m.deltaLitSkyL,null);
  assert.throws(()=>assertOwnerMeasurement(m),/inconclusive lit\/sky apertures/);
  assert.ok(m.deltaPhysicalCandidateL>0);
});
test('near-new reports only disc values; a missing physical lit signal stays unmeasured', () => {
  const f=fixture();
  const nearNew=measure(buildMasks({...f,fraction:0.01}),f.newMoon);
  assert.ok(nearNew.disc.count);
  assert.ok(!Object.hasOwn(nearNew,'deltaLitSkyL'));
  const flat=measure(buildMasks({...f,fraction:0.314,reference:f.newMoon}),f.candidate);
  assert.equal(flat.referenceP95,0);
  assert.ok(Number.isFinite(flat.deltaLitSkyL) && Number.isFinite(flat.deltaPhysicalCandidateL));
  assert.throws(()=>assertOwnerMeasurement(flat),/inconclusive physical reference/);
  assert.ok(flat.maskOverlapPixels>0 && flat.litPixels>0,'G.0 includes the threshold equality at exactly zero');
  const dim=new Uint8Array(f.newMoon);
  for(let i=0;i<dim.length;i+=4) dim.fill(0,i,i+3);
  // A uniform brighter reference has positive P95 but no distinct dark side.
  const bright=new Uint8Array(f.newMoon.length).fill(128);
  const uniform=measure(buildMasks({...f,fraction:0.314,reference:bright}),f.candidate);
  assert.ok(uniform.referenceP95>0 && uniform.darkPixels===0);
  assert.throws(()=>assertOwnerMeasurement(uniform),/inconclusive physical reference/);
  const noSignal=measure(buildMasks({...f,reference:dim}),f.candidate);
  assert.ok(noSignal.referenceP95<0);
  assert.equal(noSignal.litPixels,0);
  assert.throws(()=>assertOwnerMeasurement(noSignal),/inconclusive physical reference/);
  assert.equal(noSignal.deltaPhysicalCandidateL,null);
  assert.throws(()=>buildMasks({...f,topIsSkyOrMoon:new Uint8Array(5)}),/device pixel/);
  assert.throws(()=>buildMasks({...f,reference:f.reference.subarray(4)}),/whole card/);
});

test('every owner capture requires the public altitude, matching phase and visible refined presentation',()=>{
  for (const tag of ['offset','b0','b0-repeat','reference']) {
    const fraction=tag==='offset' ? 0.01 : 0.31385485;
    const scene={profile:tag==='reference' ? 'unboosted-v5-01' : 'calendar-neutral-v5-01',
      nativeFraction:fraction,acceptedFraction:fraction+0.0001,nativeWaxing:true,waxing:true,
      moonAltitude:-81.9,displayMode:'refined-calendar',calendarVisible:true,moonGroup:'1.000',groupOpacity:1,
      featureOpacity:1};
    assertOwnerScene(tag,scene);
    for (const [key,value] of Object.entries({moonAltitude:-20,profile:'swapped',nativeFraction:0.85,
      acceptedFraction:0.85,nativeWaxing:false,waxing:false,displayMode:'debug-hidden',calendarVisible:false,
      moonGroup:'0.000',groupOpacity:0,featureOpacity:0})) {
      assert.throws(()=>assertOwnerScene(tag,{...scene,[key]:value}),undefined,tag+' admitted wrong '+key);
    }
  }
});

test('calendar-only light observations preserve Andon priority over missing fields', () => {
  const light={eligible:false,eligibility:0,illumination:0,beam:0,cloudLight:0,localStarWash:0,localGlow:0,
    halo:0,corona:0,paraselenae:0};
  const scene={moonAltitude:-2,moonlightOpacity:0,light};
  assert.equal(calendarLightVerdict(scene),'PASS');
  for (const key of Object.keys(light)) {
    assert.equal(calendarLightVerdict({...scene,light:{...light,[key]:key==='eligible'?true:0.01}}),'FAIL');
    assert.equal(calendarLightVerdict({...scene,light:{...light,[key]:undefined}}),'INCOMPLETE');
  }
  assert.equal(calendarLightVerdict({...scene,light:null,moonlightOpacity:0.01}),'FAIL');
  assert.equal(calendarLightVerdict({...scene,moonAltitude:-1.99}),'OUTSIDE REGIME');
});

test('repeat census retains signed code deltas and device-pixel coordinates outside the limb',()=>{
  const f=fixture(2), repeat=f.candidate.slice(), width=650;
  const outer=4*(40*width+300), inner=4*(112*width+538);
  repeat[outer]++;repeat[outer+3]--;repeat[inner+1]+=6;
  const diff=compareCards(2,f.disc,f.candidate,repeat);
  assert.equal(diff.changedPixels,2);assert.equal(diff.maxChannelCode,6);
  assert.equal(diff.outside.length,1);
  assert.deepEqual(diff.outside[0].delta,[1,0,0,-1]);
  assert.equal(diff.outside[0].x,300); assert.equal(diff.outside[0].y,40);
  assert.equal(diff.outside[0].limbDistanceCss,Math.hypot(150.25-f.disc.cx,20.25-f.disc.cy)-f.disc.r);
  assert.equal(compareCards(2,f.disc,repeat,repeat).changedPixels,0);
});
