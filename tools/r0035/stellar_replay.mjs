// Reference candidate for the R0035 qualification workbench. Reconstruct each
// detected star's complete linear PSF and vary its flux BEFORE the native join.
import {renderStars} from '../../real-sky/core/src/renderer.mjs';
import {psfComponents} from '../../real-sky/core/src/optics.mjs';
import {spectralStarFlux} from '../../real-sky/core/src/spectral.mjs';
import {directTransmission} from '../../real-sky/core/src/atmosphere.mjs';
import {nativeCalendarRegion, nativeForeground} from '../../real-sky/native-composition.mjs';
import {nativeCloudDisplayFrame} from '../../real-sky/native-cloud-transfer.mjs';
import {encodeNativeDisplay} from '../../real-sky/native-host.mjs';

const support = Math.max(...[610,550,460].flatMap(wavelengthNm => psfComponents({
  preset: 'reference', wavelengthNm, coreSigmaCss: .55, scatterSigmaCss: 2.2, scatterFraction: .035
}).map(part => Math.ceil(6*part.sigmaCss)+1)));

// Two-second, independently seeded wave packets crossfade with complementary
// raised-cosine weights. A fixed bank of perpetual tones gives large repeat
// correlations even when each source uses different frequencies. Integrate
// the signal AND the fade over a 100 ms exposure using the product-to-sum rule.
const packetStep = 2, fadeRad = Math.PI/packetStep;
export function starModes(id) {
  let seed = 2166136261;
  for (const c of id) seed = Math.imul(seed ^ c.charCodeAt(0), 16777619);
  // Aligning fades to UTC seconds synchronizes the population's noise
  // variance even when individual star phases are unrelated. Stagger the
  // packet lattice using a separately mixed, stable source-id offset.
  let mixed=Math.imul(seed^(seed>>>16),0x85ebca6b);
  mixed=Math.imul(mixed^(mixed>>>13),0xc2b2ae35);
  const offsetMs=((mixed^(mixed>>>16))>>>0)/4294967296*2000;
  return {seed,offsetMs,packets:new Map()};
}
function packet(bank,index) {
  if (bank.packets.has(index)) return bank.packets.get(index);
  let seed = bank.seed ^ Math.imul(index,0x85ebca6b);
  const random = () => {
    seed = (seed + 0x6d2b79f5) >>> 0;
    let n = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    n ^= n + Math.imul(n ^ (n >>> 7), 61 | n);
    return ((n ^ (n >>> 14)) >>> 0) / 4294967296;
  };
  const modes = Array.from({length:6}, (_,i)=>({
    rad:2*Math.PI*(.6+(i+random())*(4-.6)/6),phase:2*Math.PI*random()
  }));
  if(bank.packets.size>=4) bank.packets.delete(bank.packets.keys().next().value);
  bank.packets.set(index,modes); return modes;
}
const sinc=x=>Math.abs(x)<1e-12?1:Math.sin(x)/x;
function packetMean(bank,index,mid,half) {
  let sum=0;
  for(const {rad,phase} of packet(bank,index)){
    const average = w=>Math.sin(w*mid+phase)*sinc(w*half);
    sum += .5*average(rad)-.25*(average(rad+fadeRad)+average(rad-fadeRad));
  }
  return sum/6;
}
export function starOffset(star,utcMs,multiplier,motion) {
  if (motion.paused || motion.hidden || (motion.reduced && !motion.full)
      || !star.detectable || star.altDeg <= 0) return 0;
  if (![1,2,3,4].includes(multiplier) || !Number.isFinite(utcMs)) throw new RangeError('Star replay parameters');
  // Compute in milliseconds before converting to local packet time: adjacent
  // accepted timestamps retain sub-millisecond precision at modern UTC dates.
  const local=utcMs-star.modes.offsetMs;
  const first=Math.floor((local-50)/2000), last=Math.floor((local+50)/2000);
  let signal=0;
  for(let i=first;i<=last;i++){
    const lo=Math.max(0,(local-50-i*2000)/1000), hi=Math.min(2,(local+50-i*2000)/1000);
    if(hi<=lo) continue;
    const mid=(lo+hi)/2,half=(hi-lo)/2;
    signal += (hi-lo)*10*(packetMean(star.modes,i,mid,half)
      +packetMean(star.modes,i-1,mid+packetStep,half));
  }
  const gain=motion.gain??1;
  if(!Number.isFinite(gain)||gain<0||gain>1)throw new RangeError('Invalid experimental fade gain');
  return gain*multiplier*.04*(1-.75*Math.sin(star.altDeg*Math.PI/180))*signal;
}

export function prepareStars(frame, catalogue) {
  if (frame.status !== 'ready' || frame.diffuseAsset.mode !== 'registered') throw new Error('Registered frame required');
  const {raster} = frame, diagnostics = new Map(raster.sourceDiagnostics.map(d => [d.id,d]));
  const stars = [];
  for (const source of frame.sources) {
    const d = diagnostics.get(source.id);
    if (!d?.detectable || d.backgroundComplete === false || source.altDeg <= 0) continue;
    const record = catalogue.get(source.id);
    const flux = spectralStarFlux(record, source.altDeg, {}, {response:'CIE1931',
      transportAt: wavelength => directTransmission(wavelength,source.altDeg,raster.atmosphere,d.cloudTransmission)});
    if (flux.vFlux !== d.vFlux || d.scintillationFactor !== 1) throw new Error('Reference flux disagrees with worker');
    stars.push(preparePatch({...source, detectable:true},flux,raster.width,raster.height));
  }
  return stars;
}
export function preparePatch(star, flux, width, height) {
  const cx = Math.floor(star.x), cy = Math.floor(star.y);
  const x0 = Math.max(0,cx-support), y0 = Math.max(0,cy-support);
  const w = Math.min(width,cx+support+1)-x0, h = Math.min(height,cy+support+1)-y0;
  const patch = renderStars([{...star,x:star.x-x0,y:star.y-y0}], {width:w,height:h,fluxAt:()=>flux});
  return {...star,x0,y0,w,h,linear:patch.linear,modes:starModes(star.id)};
}

export function glassMembership(star, boxes, margin) {
  return boxes.some(b => star.x >= b.x-margin && star.x < b.x+b.width+margin
    && star.y >= b.y-margin && star.y < b.y+b.height+margin);
}

// Synthetic/replayed owner inputs. The physical Moon was already applied in
// the frame's source diagnostics. Calendar, lunar material and painted clouds
// are separate foreground inputs, applied by the unchanged native operators.
export function replayFrame(raster, stars, utcMs, config, foreground, motion = {}) {
  if (!['preview-members','all'].includes(config.scope)
      || ![1,2,3,4].includes(config.multiplier) || !Number.isFinite(config.glassFactor)
      || config.glassFactor<0 || config.glassFactor>1 || !Number.isFinite(config.margin) || config.margin<0)
    throw new RangeError('Explicit scope, multiplier and glass treatment required');
  const delta = new Float64Array(raster.linear.length), selected = [], glass = [], margins = [];
  let brightest = null;
  for (const star of stars) {
    if (config.scope === 'preview-members' && star.vmag > 4.5) continue;
    const under = glassMembership(star,foreground.glass,0), near = glassMembership(star,foreground.glass,config.margin);
    if (under) glass.push(star.id);
    if (near && !under) margins.push(star.id);
    const glassScale = near ? config.glassFactor : 1;
    if (glassScale === 0) continue;
    selected.push(star.id);
    const shift = starOffset(star,utcMs,config.multiplier,motion)*glassScale;
    if (!brightest || star.vmag < brightest.vmag) brightest = {id:star.id,vmag:star.vmag,factor:1+shift};
    if (shift === 0) continue;
    for (let y = 0; y < star.h; y++) {
      let dst = 3*((y+star.y0)*raster.width+star.x0), src = 3*y*star.w;
      for (let k = 0; k < 3*star.w; k++) delta[dst++] += shift*star.linear[src++];
    }
  }
  const base = nativeCalendarRegion(raster,foreground.mask);
  const direct = foreground.signalMask??foreground.mask;
  for (let i = 0; i < base.length; i++) base[i] = Math.max(0,base[i]+delta[i]*(direct?.[Math.floor(i/3)]??1));
  if (raster.starPreview) {
    const encoded = encodeNativeDisplay(base,raster.effectiveExposure);
    const rgba = nativeCloudDisplayFrame(encoded,foreground.cloudRGBA??new Uint8ClampedArray(encoded.length),foreground.moonRGBA);
    return {rgba,selected,glass,margins,brightest};
  }
  const joined = nativeForeground(base,{cloudRGBA:foreground.cloudRGBA,moonRGBA:foreground.moonRGBA,
    atmosphereLinear:raster.skyBackgroundLinear??raster.backgroundLinear,exposure:raster.effectiveExposure});
  return {rgba:encodeNativeDisplay(joined.linear,raster.effectiveExposure), selected,glass,margins,brightest};
}
