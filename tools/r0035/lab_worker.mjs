// Disposable live-lab worker. No DOM, no astronomical clock, no provider calls.
import {prepareStars,preparePatch,glassMembership} from './stellar_replay.mjs';
import {prepareReplay,stellarOverlay} from './prepared_replay.mjs';
import {sha256Hex} from '../../real-sky/core/src/sha256.mjs';
import {spectralStarFlux} from '../../real-sky/core/src/spectral.mjs';
import {directTransmission,normaliseAtmosphere} from '../../real-sky/core/src/atmosphere.mjs';
import {projectPerspective} from '../../real-sky/core/src/projection.mjs';
import {projectCatalogue,discOccults} from '../../real-sky/core/src/scene.mjs';
import {displayVisibility} from '../../real-sky/core/src/visibility.mjs';
import {luminance} from '../../real-sky/core/src/photometry.mjs';
let current=null, generation=0, catalogue=null;
async function records(digest){
  if(!catalogue) catalogue=(async()=>{
    const response=await fetch(new URL('../../vendor/real-sky/data/bright-stars.json',import.meta.url));
    if(!response.ok) throw new Error('Catalogue unavailable');
    const bytes=new Uint8Array(await response.arrayBuffer());
    return {digest:sha256Hex(bytes),records:new Map(JSON.parse(new TextDecoder().decode(bytes)).stars.map(s=>[s.id,s]))};
  })();
  const data=await catalogue;if(data.digest!==digest)throw new Error('Accepted source identity mismatch');
  return data.records;
}
export function livePreviewStars(raster,sources){
  if(raster.starPreview.belowByteResolution) return [];
  const stars=[],moon=raster.physicalState.moon,radiusDeg=moon.angularRadiusDeg??.25;
  const atmosphere=normaliseAtmosphere(raster.atmosphere);
  for(const s of sources){
    if(s.altDeg<=0||s.emission?.enabled===false||!s.visible
       ||moon.altDeg+radiusDeg>=0&&discOccults(s,{...moon,radiusDeg}))continue;
    const flux=spectralStarFlux(s,s.altDeg,{}, {response:'CIE1931',
      transportAt:wavelength=>directTransmission(wavelength,s.altDeg,atmosphere,1)});
    const i=3*(Math.floor(s.y)*raster.width+Math.floor(s.x));
    if(displayVisibility(luminance(flux.rgb),luminance(raster.skyBackgroundLinear.subarray(i,i+3)),raster.effectiveExposure).detectable)
      stars.push(preparePatch({...s,detectable:true},flux,raster.width,raster.height));
  }
  return stars;
}
export async function prepareLiveFrame(msg) {
  const {raster,sources}=msg.frame;
  const preview=raster.starPreview,job=msg.job??msg.frame.job;
  const catalogue=await records(preview?.sha256??msg.frame.catalogue.sha256);
  const input=[...catalogue.values()].filter(s=>s.emission?.enabled!==false&&(!preview||s.vmag<=4.5));
  const expected=projectCatalogue({stars:input},job.observer,h=>projectPerspective(h,job.options.view)).filter(s=>s.visible);
  const byId=new Map(sources.map(s=>[s.id,s]));
  const fields=['hygId','hip','vmag','x','y','altDeg','azDeg'];
  if(sources.length!==expected.length||byId.size!==sources.length||expected.some(e=>fields.some(k=>e[k]!==byId.get(e.id)?.[k])))
    throw new Error('Projected catalogue membership or coordinates mismatch');
  if(!preview){
    const moon=raster.physicalState.moon,disc={...moon,radiusDeg:moon.angularRadiusDeg??.25};
    const visible=expected.filter(s=>moon.altDeg+disc.radiusDeg<0||!discOccults({...s,altDeg:s.geometricAltDeg??s.altDeg},disc));
    const diagnostics=raster.sourceDiagnostics,byId=new Map(diagnostics.map(d=>[d.id,d]));
    if(diagnostics.length!==visible.length||byId.size!==visible.length||visible.some(s=>byId.get(s.id)?.vmag!==s.vmag||byId.get(s.id)?.hip!==s.hip))
      throw new Error('Transport diagnostics membership mismatch');
  }
  const stars=preview?livePreviewStars(raster,expected):prepareStars({...msg.frame,sources:expected},catalogue);
  const prepared=prepareReplay(raster,stars,msg.config,msg.foreground);
  // The original owner published these exact bytes. Never substitute a
  // reconstruction with a different exposure, mask, foreground, or owner.
  if(msg.nominal.length!==prepared.nominal.length||prepared.nominal.some((value,i)=>value!==msg.nominal[i]))throw new Error('Nominal native bytes mismatch');
  const scoped=stars.filter(s=>msg.config.scope==='all'||s.vmag<=4.5);
  const center=(s)=>Math.floor(s.y)*raster.width+Math.floor(s.x);
  const under=scoped.filter(s=>glassMembership(s,msg.foreground.glass,0));
  const margin=scoped.filter(s=>!glassMembership(s,msg.foreground.glass,0)&&glassMembership(s,msg.foreground.glass,msg.config.margin));
  const mask=msg.foreground.signalMask??msg.foreground.mask;
  prepared.census={projected:sources.length,transportDiagnostics:raster.sourceDiagnostics?.length??null,
    detectable:stars.length,projectedIds:expected.map(s=>s.id),detectableIds:stars.map(s=>s.id),scopedIds:scoped.map(s=>s.id),omittedByMagnitude:stars.filter(s=>msg.config.scope!=='all'&&s.vmag>4.5).map(s=>s.id),
    centerUnderGlass:under.map(s=>s.id),addedMargin:margin.map(s=>s.id),glassFactor:msg.config.glassFactor,
    fullyCalendarMaskedCenters:scoped.filter(s=>mask?.[center(s)]===0).map(s=>s.id),
    fullyCloudMaskedCenters:scoped.filter(s=>msg.foreground.cloudRGBA?.[4*center(s)+3]===255).map(s=>s.id)};
  return prepared;
}
if(typeof self!=='undefined'&&typeof document==='undefined') self.onmessage=async event=>{
  const msg=event.data;
  try{
    if(msg.op==='prepare'){
      generation=msg.epoch;current=null;const candidate=await prepareLiveFrame(msg);
      if(generation!==msg.epoch)return;
      current=candidate;self.postMessage({op:'ready',epoch:generation,sources:candidate.sourceCount,contributingCenters:candidate.contributingCenters,variablePixels:candidate.indices.length,census:candidate.census});
    }else if(msg.op==='sample'&&msg.epoch===generation&&current){
      const result=current.present(msg.utcMs,msg.motion),rgba=stellarOverlay(current,result.rgba);
      // Include the encoded pixels at the fixed eligible positions of this
      // epoch. Only the UI owner knows which previous reply actually painted.
      const newPixels=new Uint32Array(rgba.buffer);
      const signal=Uint32Array.from(current.indices,p=>newPixels[p]);
      self.postMessage({op:'sample',epoch:generation,utcMs:msg.utcMs,sample:result.sample,rgba,signal},[rgba.buffer,signal.buffer]);

    }
  }catch(error){self.postMessage({op:'failed',epoch:msg.epoch,reason:String(error?.message??error)});}
};
