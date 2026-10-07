import {createRegisteredStarlightSampler,renderRegisteredStarlight} from '../src/registered-starlight.mjs';
import {finite,observationFrame,observeStar} from '../src/astronomy.mjs';
import {projectAllSky,projectPerspective} from '../src/projection.mjs';
import {diffuseRayToMap} from '../src/diffuse-map.mjs';
const RS_el=id=>document.getElementById(id);
const RS_locations={Florida:[28.54,-81.38],Madinah:[24.47,39.61],Reykjavik:[64.15,-21.94],Sydney:[-33.87,151.21]};
let RS_assets,RS_samplers,RS_current=null;
function RS_fail(error){const canvas=RS_el('sky');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);RS_current=null;RS_el('status').textContent='Diagnostic unavailable — '+error.message;RS_el('status').style.color='#efac97';RS_el('readback').textContent='The last sky has been cleared. No invented or stale fallback is shown.';window.__starlightDiag={ready:false,error:error.message,productionAdmissible:false};}
function RS_numeric(id){const text=RS_el(id).value.trim();if(!text)throw new Error(id+' is required');return finite(Number(text),id);}
function RS_signature(bytes){let hash=2166136261;for(const b of bytes)hash=Math.imul(hash^b,16777619);return (hash>>>0).toString(16).padStart(8,'0');}
function RS_render(){
 try{
  if(!RS_samplers)throw new Error('Local assets not ready');
  const observer={utcMs:Date.parse(RS_el('utc').value+'Z'),latDeg:RS_numeric('lat'),lonDeg:RS_numeric('lon'),pressureHpa:0};
  const type=RS_el('view').value,view=type==='allsky'?{type,width:420,height:420,padding:6,eastLeft:true}:{type,width:325,height:530,azDeg:RS_numeric('az'),altDeg:RS_numeric('alt'),fovYDeg:RS_numeric('fov'),rollDeg:RS_numeric('roll')};
  const tier=RS_el('tier').value,sampler=RS_samplers[tier],dpr=RS_numeric('dpr'),gain=finite(RS_numeric('gain'),'display gain',.001,3),samplesPerAxis=RS_numeric('samples');
  const start=performance.now(),raster=renderRegisteredStarlight(sampler,observer,view,{dpr,samplesPerAxis,allowEstimates:RS_el('estimates').checked}),elapsed=performance.now()-start;
  const canvas=RS_el('sky');canvas.width=raster.width;canvas.height=raster.height;canvas.style.width=view.width+'px';canvas.style.height=view.height+'px';
  const bytes=new Uint8ClampedArray(raster.width*raster.height*4);
  for(let i=0;i<raster.radiance.length;i++){
   const x=i%raster.width,y=Math.floor(i/raster.width),p=i*4;
   if(raster.missing[i]){const hatch=((x+y)%12)<6;bytes[p]=hatch?155:65;bytes[p+1]=hatch?85:40;bytes[p+2]=hatch?50:30;}
   else {const t=1-Math.exp(-gain*raster.radiance[i]/sampler.zeroPointWm2nm),v=Math.round(255*(t<=.0031308?12.92*t:1.055*t**(1/2.4)-.055));bytes[p]=bytes[p+1]=bytes[p+2]=v;}
   if(RS_el('showmask').checked&&raster.skyFraction[i]>0&&!raster.missing[i]){const f=.6*raster.estimatedFraction[i];bytes[p]=Math.round(bytes[p]*(1-f)+235*f);bytes[p+1]=Math.round(bytes[p+1]*(1-f)+140*f);bytes[p+2]=Math.round(bytes[p+2]*(1-f)+50*f);}
   bytes[p+3]=255;
  }
  const ctx=canvas.getContext('2d');ctx.putImageData(new ImageData(bytes,raster.width,raster.height),0,0);
  const frame=observationFrame(observer);let markers=0;
  if(RS_el('markers').checked){ctx.save();ctx.scale(raster.width/view.width,raster.height/view.height);ctx.strokeStyle='#7dd3fc';ctx.lineWidth=.8;
   for(const star of RS_assets.catalogue.stars){if(star.vmag>4||!star.emission.enabled)continue;const h=observeStar(star,frame);if(h.altDeg<0)continue;const p=type==='allsky'?projectAllSky(h,view):projectPerspective(h,view);if(!p||!p.visible)continue;ctx.beginPath();ctx.arc(p.x,p.y,star.vmag<1?2.8:1.6,0,2*Math.PI);ctx.stroke();markers++;}
   ctx.restore();
  }
  const center=diffuseRayToMap(view.width/2,view.height/2,view,frame);
  RS_current={observer,view,frame,sampler,raster};
  const signature=RS_signature(ctx.getImageData(0,0,raster.width,raster.height).data);
  window.__starlightDiag={ready:true,stage:'7.3',stageStatus:'ORIGINAL_GATES_COMPLETED',dataAdmitted:true,sourceGate:'PASS',physicalComposition:false,observer,view,tier,dpr,samplesPerAxis,sourceId:sampler.id,sourceSha256:sampler.sourceSha256,integratedWm2nm:sampler.integratedWm2nm,skyPixels:raster.skyPixels,missingPixels:raster.missingPixels,annotationCount:markers,center:{raDeg:center.raDeg,decDeg:center.decDeg},pixelSignature:signature,rasterMs:elapsed,estimatedSkyAreaFraction:RS_assets.report.estimatedAreaFraction,estimatesAllowed:RS_el('estimates').checked};
  RS_el('status').style.color='#7dd3c5';RS_el('status').textContent='Authenticated starlight · registered V component · diagnostic exposure';
  RS_el('readback').textContent=`Accepted UTC: ${new Date(observer.utcMs).toISOString()}
Observer: ${observer.latDeg.toFixed(2)}°, ${observer.lonDeg.toFixed(2)}°
Source: Gaia DR3 + Hipparcos, original BVRI retained
Excluded CP6 emitters: ${RS_assets.report.emittedSources.toLocaleString('en-GB')}
Integrated V: ${sampler.integratedWm2nm.toExponential(8)} W m⁻² nm⁻¹
Native estimated area: ${(100*RS_assets.report.estimatedAreaFraction).toFixed(2)}%
HEALPix nside ${tier}; raster ${raster.width} × ${raster.height}; DPR ${dpr}
Centre ICRS ≈ J2000: RA ${center.raDeg?.toFixed(5)??'below horizon'}°, Dec ${center.decDeg?.toFixed(5)??'—'}°
Annotations: ${markers}; unavailable pixels: ${raster.missingPixels}
Display gain is an inspection setting, not sky photometry.
Atmospheric composition: separate Checkpoint 7.4.`;

 }catch(error){RS_fail(error);}
}
async function RS_boot(){
 if(window.__registeredAssets)RS_assets=window.__registeredAssets;
 else{
  const fetchJSON=async path=>{const r=await fetch(path);if(!r.ok)throw new Error('Local asset unavailable: '+path);return r.json();};
  const [catalogue,report,...maps]=await Promise.all([fetchJSON('../data/bright-stars.json'),fetchJSON('../checkpoints/cp7_completion/asset-build.json'),...['128','64','32'].map(s=>fetchJSON('../data/registered-starlight/V-nside'+s+'.json'))]);
  RS_assets={catalogue,report,maps:Object.fromEntries(['128','64','32'].map((s,i)=>[s,maps[i]]))};
 }
 RS_samplers=Object.fromEntries(Object.entries(RS_assets.maps).map(([k,v])=>[k,createRegisteredStarlightSampler(v,{catalogueSha256:RS_assets.report.catalogueSha256})]));
 RS_el('location').addEventListener('change',()=>{const [lat,lon]=RS_locations[RS_el('location').value];RS_el('lat').value=lat;RS_el('lon').value=lon;RS_render();});
 for(const id of ['lat','lon','utc','view','az','alt','fov','roll','tier','dpr','samples','gain','markers','estimates','showmask'])RS_el(id).addEventListener('change',RS_render);
 for(const [id,step] of [['forward',21600000],['back',-21600000]])RS_el(id).addEventListener('click',()=>{try{const ms=finite(Date.parse(RS_el('utc').value+'Z'),'UTC instant');RS_el('utc').value=new Date(ms+step).toISOString().slice(0,19);RS_render();}catch(error){RS_fail(error);}});
 RS_el('render').addEventListener('click',RS_render);
 RS_el('sky').addEventListener('pointermove',event=>{if(!RS_current)return;const box=RS_el('sky').getBoundingClientRect(),x=(event.clientX-box.left)*RS_current.view.width/box.width,y=(event.clientY-box.top)*RS_current.view.height/box.height;const q=diffuseRayToMap(x,y,RS_current.view,RS_current.frame);
  if(!q.aboveHorizon){RS_el('hover').textContent='Outside the selected sky / below horizon';return;}
  const s=RS_current.sampler.sample(q.raDeg,q.decDeg);RS_el('hover').textContent=`ICRS RA ${q.raDeg.toFixed(4)}°, Dec ${q.decDeg.toFixed(4)}°\n${s.defined?s.value.toExponential(5)+' W m⁻² sr⁻¹ nm⁻¹':'Unavailable source support'} · ${(100*s.estimatedFraction).toFixed(1)}% estimated support`;
 });
 window.__renderRegisteredStarlight=RS_render;RS_render();
}
RS_boot().catch(RS_fail);
