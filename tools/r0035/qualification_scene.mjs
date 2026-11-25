import {NativeSkyEngine} from '../../real-sky/native-engine.mjs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {NativeStarPreview,joinNativeStarPreview} from '../../real-sky/native-star-preview.mjs';
import {nativeAtmosphereFields,nativeSkyPresentation,renderNativeBackgroundPreview} from '../../real-sky/native-preview.mjs';
import {encodeNativeDisplay} from '../../real-sky/native-host.mjs';
import {nativeInverseCode} from '../../real-sky/native-composition.mjs';
import {discOccults} from '../../real-sky/core/src/scene.mjs';
import {displayVisibility} from '../../real-sky/core/src/visibility.mjs';
import {luminance} from '../../real-sky/core/src/photometry.mjs';
import {directTransmission,normaliseAtmosphere} from '../../real-sky/core/src/atmosphere.mjs';
import {spectralStarFlux} from '../../real-sky/core/src/spectral.mjs';
import {prepareStars,preparePatch} from './stellar_replay.mjs';

export const replayObserver = {lat:24.47,lon:39.61,heightM:0,generation:1,sceneIdentity:'r0035-clear',
  camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{src:'synthetic-clear',vis:20000,temp:10},
  lp:0,reducedMotion:false,solarAnchor:null};

export async function prepareScene(pack,snapshot,tier) {
  if (tier === 'refined') {
    const engine = new NativeSkyEngine(pack);
    try {
      const job = nativeJob(snapshot,true), frame = await engine.render(job);
      if (frame.status !== 'ready') throw new Error(frame.error || 'No refined frame');
      if (frame.raster.physicalState.sun.altDeg >= -20) {
        const step = job.options.backgroundStepCss;
        const fields = nativeAtmosphereFields(frame.raster.physicalState,frame.raster.atmosphere,
          job.options.view,job.options.diffuse.residualNight,Math.ceil(325/step),Math.ceil(530/step));
        const {solarAerosolLinear,solarBackgroundLinear,lunarBackgroundLinear,twilightDisplay} = fields;
        frame.raster = nativeSkyPresentation({...frame.raster,solarAerosolLinear,solarBackgroundLinear,
          lunarBackgroundLinear,twilightDisplay},job.options.view,snapshot.solarAnchor);
      }
      const stars = prepareStars(frame,new Map(engine.store.catalogue.stars.map(s=>[s.id,s])));
      return {tier,raster:frame.raster,stars,projected:frame.sources.length,diagnostics:frame.raster.sourceDiagnostics.length,
        catalogueSha256:frame.catalogue.sha256,diffuseSha256:frame.diffuseAsset.assetSha256};
    } finally { engine.dispose(); }
  }
  if (tier !== 'preview') throw new RangeError('Unknown scene tier');
  const preview = renderNativeBackgroundPreview(snapshot), renderer = new NativeStarPreview(pack);
  const E = preview.raster.effectiveExposure, background = encodeNativeDisplay(preview.raster.linear,E);
  const layer = renderer.render(preview.job,preview.raster.physicalState,{background,exposure:E});
  const joined = joinNativeStarPreview(preview,background,layer);
  const moon = preview.raster.physicalState.moon, radiusDeg = moon.angularRadiusDeg??.25;
  const atmosphere = normaliseAtmosphere(preview.job.options.atmosphere), stars = [];
  for (const s of layer.sources) {
    if (s.altDeg<=0 || s.emission?.enabled===false || layer.diagnostics.belowByteResolution
        || (moon.altDeg+radiusDeg>=0 && discOccults(s,{...moon,radiusDeg}))) continue;
    const flux = spectralStarFlux(s,s.altDeg,{}, {response:'CIE1931',
      transportAt:wavelength=>directTransmission(wavelength,s.altDeg,atmosphere,1)});
    const i = 4*(Math.floor(s.y)*325+Math.floor(s.x));
    const bg = Array.from(background.slice(i,i+3),code=>nativeInverseCode(code,E));
    if (displayVisibility(luminance(flux.rgb),luminance(bg),E).detectable) {
      stars.push(preparePatch({...s,detectable:true},flux,325,530));
    }
  }
  return {tier,raster:joined.raster,stars,projected:layer.sources.length,diagnostics:null,
    catalogueSha256:renderer.identity.sha256,diffuseSha256:null};
}
