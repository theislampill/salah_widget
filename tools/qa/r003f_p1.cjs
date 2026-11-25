'use strict';
const assert = require('node:assert/strict');

// R003F G.0 offline measurement. Inputs are decoded, composited card screenshots
// (device pixels). Geometry and header boxes are card-relative CSS pixels.
const weights = [0.2126, 0.7152, 0.0722];
const linear = Float64Array.from({length:256}, (_, code) => {
  const c = code / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
});
function lightness(y) {
  return y > 216 / 24389 ? 116 * Math.cbrt(y) - 16 : (24389 / 27) * y;
}
function luminance(rgba, i) {
  return weights[0] * linear[rgba[4*i]] + weights[1] * linear[rgba[4*i+1]] + weights[2] * linear[rgba[4*i+2]];
}
function quantile(values, q) {
  if (!values.length) return null;
  const sorted = values.sort((a,b) => a-b);
  const rank = (sorted.length-1) * q, lo = Math.floor(rank);
  return sorted[lo] + (rank-lo) * (sorted[Math.ceil(rank)]-sorted[lo]);
}
function mean(values) {
  return values.length ? values.reduce((sum,y) => sum+y,0) / values.length : null;
}
function checkFrame(rgba, count) {
  if (!(rgba instanceof Uint8Array || rgba instanceof Uint8ClampedArray) || rgba.length !== count*4)
    throw new RangeError('expected decoded RGBA bytes for the whole card at the declared DPR');
}
function checkDisc(disc) {
  if (!disc || ![disc.cx,disc.cy,disc.r].every(Number.isFinite) || disc.r <= 0)
    throw new RangeError('invalid card-relative disc');
}
function buildMasks({dpr, fraction, disc, offsetDisc, newMoon, reference, headerRects, topIsSkyOrMoon}) {
  if (![1,2].includes(dpr) || !Number.isFinite(fraction) || fraction < 0 || fraction > 1)
    throw new RangeError('invalid G.0 DPR or phase');
  checkDisc(disc); checkDisc(offsetDisc);
  const width = 325*dpr, height = 530*dpr, count = width*height;
  checkFrame(newMoon,count); checkFrame(reference,count);
  if (!(topIsSkyOrMoon instanceof Uint8Array) || topIsSkyOrMoon.length !== count || topIsSkyOrMoon.some(x => x > 1))
    throw new RangeError('expected one binary elementsFromPoint sample per device pixel');
  if (!Array.isArray(headerRects) || headerRects.some(box => !Array.isArray(box) || box.length!==4 ||
      !box.every(Number.isFinite) || box[0]>box[2] || box[1]>box[3])) throw new RangeError('invalid header boxes');
  const offset = [], interior = [], discPixels = [], annulus = [];
  for (let i=0; i<count; i++) {
    const x = (i%width+0.5)/dpr, y = (Math.floor(i/width)+0.5)/dpr;
    if (Math.hypot(x-offsetDisc.cx,y-offsetDisc.cy) < 0.9*offsetDisc.r) offset.push(luminance(newMoon,i));
    const dx = x-disc.cx, dy = y-disc.cy, radius = Math.hypot(dx,dy)/disc.r;
    if (radius < 0.9) discPixels.push(i);
    if (radius < 0.95) interior.push({i,radius,yRef:luminance(reference,i)});
    if (radius < 1.08 || radius > 1.6 || x<8 || y<8 || x>=325-8 || y>=530-8) continue;
    if (headerRects.some(([x0,y0,x1,y1]) => x>=x0-2 && x<x1+2 && y>=y0-2 && y<y1+2)) continue;
    const octant = (Math.floor(Math.atan2(dy,dx)/(Math.PI/4))+8)%8;
    annulus.push({i,radius,left:dx<0,lower:dy>0,octant});
  }
  if (!offset.length || !interior.length || !discPixels.length) throw new RangeError('empty reference or offset aperture');
  const g0 = quantile(offset,0.5);
  const p95 = quantile(interior.map(p => p.yRef-g0),0.95);
  const lit = [], dark = [];
  let maskOverlapPixels = 0;
  if (fraction > 0.02) {
    for (const {i,radius,yRef} of interior) {
      const inLit = yRef-g0 >= 0.5*p95;
      const inDark = radius < 0.92 && yRef-g0 <= 0.05*p95;
      if (inLit) lit.push(i);
      if (inDark) dark.push(i);
      if (inLit && inDark) maskOverlapPixels++;
    }
  }
  const minimum = 600*dpr*dpr;
  let sky = [], outer, elementExclusion = true;
  for (outer of [1.3,1.4,1.5,1.6]) {
    sky = annulus.filter(p => p.radius <= outer && topIsSkyOrMoon[p.i]);
    if (sky.length >= minimum) break;
  }
  if (sky.length < minimum) {
    elementExclusion = false; sky = annulus;
  }
  const physicalLitMean = mean(lit.map(i => luminance(reference,i)));
  return {count, dpr, fraction, g0, p95, lit, dark, maskOverlapPixels, discPixels, sky, outer, elementExclusion, minimum, physicalLitMean};
}
function measure(masks, candidate) {
  const {count,dpr,fraction,g0,p95,lit,dark,maskOverlapPixels,discPixels,sky,outer,elementExclusion,minimum,physicalLitMean} = masks;
  checkFrame(candidate,count);
  const sample = i => luminance(candidate,i);
  const disc = discPixels.map(sample);
  const summary = {fraction,offsetG0:g0,disc:{count:disc.length,meanY:mean(disc),medianY:quantile(disc,0.5)}};
  if (fraction<=0.02) return summary;
  const litY = mean(lit.map(sample));
  const median = pixels => quantile(pixels.map(p => sample(p.i)),0.5);
  const octants = Array.from({length:8}, (_,octant) => {
    const pixels = sky.filter(p => p.octant===octant);
    return {count:pixels.length, medianY:pixels.length>=40*dpr*dpr ? median(pixels) : null};
  });
  const medians = octants.map(o=>o.medianY).filter(y=>y!==null);
  const skyY = sky.length>=minimum ? median(sky) : null;
  return {...summary,referenceP95:p95,litPixels:lit.length,darkPixels:dark.length,maskOverlapPixels,
    litMeanY:litY,physicalLitMeanY:physicalLitMean,darkMeanY:mean(dark.map(sample)),
    sky:{count:sky.length,minimum,outerRadius:outer,elementExclusion,medianY:skyY,
      leftMedianY:median(sky.filter(p=>p.left)),lowerMedianY:median(sky.filter(p=>p.lower)),octants,
      octantRangeL:medians.length ? [lightness(Math.min(...medians)),lightness(Math.max(...medians))] : null},
    deltaLitSkyL:litY!==null && skyY!==null ? lightness(litY)-lightness(skyY) : null,
    deltaPhysicalCandidateL:litY!==null ? lightness(physicalLitMean)-lightness(litY) : null};
}
// The owner phase is partial. Keep the G.0 threshold inclusions and their raw
// statistics even when the reference cannot identify separate lit/dark regions.
function assertOwnerMeasurement(m) {
  assert.ok(m.referenceP95>0 && m.litPixels>0 && m.darkPixels>0 && m.maskOverlapPixels===0,
    'inconclusive physical reference for the owner phase');
  assert.ok(Number.isFinite(m.deltaLitSkyL) && Number.isFinite(m.deltaPhysicalCandidateL),
    'inconclusive lit/sky apertures');
}

function assertOwnerScene(tag,state) {
  const offset=tag==='offset', fraction=offset ? 0.01 : 0.314;
  assert.equal(state.profile,tag==='reference' ? 'unboosted-v5-01' : 'calendar-neutral-v5-01',tag+' profile');
  assert.equal(state.moonAltitude,-81.9,tag+' native altitude at 0.1 degree precision');
  assert.ok(Number.isFinite(state.nativeFraction) && +state.nativeFraction.toFixed(3)===fraction,tag+' native phase');
  // The accepted renderer fraction includes its bounded geometry approximation.
  assert.ok(Number.isFinite(state.acceptedFraction) && Math.abs(state.acceptedFraction-fraction)<(offset?0.001:0.002),
    tag+' accepted phase');
  assert.equal(state.nativeWaxing,true,tag+' native phase sense');
  assert.equal(state.waxing,true,tag+' accepted phase sense');
  assert.equal(state.displayMode,'refined-calendar',tag+' display mode');
  assert.equal(state.calendarVisible,true,tag+' calendar visibility');
  assert.equal(Number(state.moonGroup),1,tag+' calendar group setting');
  assert.equal(state.groupOpacity,1,tag+' rendered group opacity');
  assert.equal(state.featureOpacity,1,tag+' rendered feature opacity');
}

// Keep each outlier for F-OUT follow-up. Coordinates are device-pixel
// indices; limb distance is in CSS pixels so DPRs can be compared.
function compareCards(dpr,disc,first,second) {
  if (![1,2].includes(dpr)) throw new RangeError('invalid DPR');
  checkDisc(disc);
  const width=325*dpr,count=width*530*dpr,outside=[];
  checkFrame(first,count); checkFrame(second,count);
  let changedPixels=0,maxChannelCode=0;
  for(let i=0;i<count;i++) {
    const start=4*i;
    if(first[start]===second[start] && first[start+1]===second[start+1] &&
       first[start+2]===second[start+2] && first[start+3]===second[start+3]) continue;
    changedPixels++;
    const delta=Array.from({length:4},(_,k)=>second[start+k]-first[start+k]);
    maxChannelCode=Math.max(maxChannelCode,...delta.map(Math.abs));
    const x=i%width,y=Math.floor(i/width);
    const distance=Math.hypot((x+0.5)/dpr-disc.cx,(y+0.5)/dpr-disc.cy);
    if(distance>1.06*disc.r) outside.push({x,y,limbDistanceCss:distance-disc.r,delta});
  }
  return {changedPixels,maxChannelCode,outside};
}

// An observed forbidden light is an Andon even if another diagnostic is missing.
function calendarLightVerdict({moonAltitude, moonlightOpacity, light}) {
  if (!Number.isFinite(moonAltitude) || moonAltitude > -2) return 'OUTSIDE REGIME';
  const terms = [moonlightOpacity, ...['eligibility','illumination','beam','cloudLight','localStarWash',
    'localGlow','halo','corona','paraselenae'].map(key => light?.[key])];
  if (light?.eligible === true || terms.some(v => Number.isFinite(v) && v !== 0)) return 'FAIL';
  return light?.eligible === false && terms.every(v => v === 0) ? 'PASS' : 'INCOMPLETE';
}
module.exports = {buildMasks, measure, lightness, calendarLightVerdict, compareCards, assertOwnerScene, assertOwnerMeasurement};
