import {finite,observationFrame,observeStar} from '../src/astronomy.mjs';
import {projectAllSky,projectPerspective} from '../src/projection.mjs';
import {createDiagnosticDiffuseSampler,renderDiagnosticDiffuse,diffuseRayToMap} from '../src/diffuse-map.mjs';
const DD_el=id=>document.getElementById(id);
const DD_locations={Florida:[28.54,-81.38],Madinah:[24.47,39.61],Reykjavik:[64.15,-21.94],Sydney:[-33.87,151.21]};
let DD_assets,DD_samplers,DD_current=null;
function DD_fail(error){const canvas=DD_el('sky');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);DD_current=null;DD_el('status').textContent='Diagnostic unavailable — '+error.message;DD_el('status').style.color='#efac97';DD_el('readback').textContent='The last sky has been cleared. No invented or stale fallback is shown.';window.__diffuseDiag={ready:false,error:error.message,productionAdmissible:false};}
function DD_numeric(id){const text=DD_el(id).value.trim();if(!text)throw new Error(id+' is required');return finite(Number(text),id);}
function DD_signature(bytes){let hash=2166136261;for(const b of bytes)hash=Math.imul(hash^b,16777619);return (hash>>>0).toString(16).padStart(8,'0');}
function DD_render(){
 try{
  if(!DD_samplers)throw new Error('Local assets not ready');
  const observer={utcMs:Date.parse(DD_el('utc').value+'Z'),latDeg:DD_numeric('lat'),lonDeg:DD_numeric('lon'),pressureHpa:0};
  const type=DD_el('view').value,view=type==='allsky'?{type,width:420,height:420,padding:6,eastLeft:true}:{type,width:325,height:530,azDeg:DD_numeric('az'),altDeg:DD_numeric('alt'),fovYDeg:DD_numeric('fov'),rollDeg:DD_numeric('roll')};
  const tier=DD_el('tier').value,sampler=DD_samplers[tier],dpr=DD_numeric('dpr'),gain=finite(DD_numeric('gain'),'display gain',.001,3),samplesPerAxis=DD_numeric('samples');
  const start=performance.now(),raster=renderDiagnosticDiffuse(sampler,observer,view,{dpr,samplesPerAxis}),elapsed=performance.now()-start;
  const canvas=DD_el('sky');canvas.width=raster.width;canvas.height=raster.height;canvas.style.width=view.width+'px';canvas.style.height=view.height+'px';
  const bytes=new Uint8ClampedArray(raster.width*raster.height*4);
  for(let i=0;i<raster.radiance.length;i++){
   const x=i%raster.width,y=Math.floor(i/raster.width),p=i*4;
   if(raster.missing[i]){const hatch=((x+y)%12)<6;bytes[p]=hatch?155:65;bytes[p+1]=hatch?85:40;bytes[p+2]=hatch?50:30;}
   else {const t=1-Math.exp(-gain*raster.radiance[i]),v=Math.round(255*(t<=.0031308?12.92*t:1.055*t**(1/2.4)-.055));bytes[p]=bytes[p+1]=bytes[p+2]=v;}
   bytes[p+3]=255;
  }
  const ctx=canvas.getContext('2d');ctx.putImageData(new ImageData(bytes,raster.width,raster.height),0,0);
  const frame=observationFrame(observer);let markers=0;
  if(DD_el('markers').checked){ctx.save();ctx.scale(raster.width/view.width,raster.height/view.height);ctx.strokeStyle='#7dd3fc';ctx.lineWidth=.8;
   for(const star of DD_assets.catalogue.stars){if(star.vmag>4||!star.emission.enabled)continue;const h=observeStar(star,frame);if(h.altDeg<0)continue;const p=type==='allsky'?projectAllSky(h,view):projectPerspective(h,view);if(!p||!p.visible)continue;ctx.beginPath();ctx.arc(p.x,p.y,star.vmag<1?2.8:1.6,0,2*Math.PI);ctx.stroke();markers++;}
   ctx.restore();
  }
  const center=diffuseRayToMap(view.width/2,view.height/2,view,frame);
  DD_current={observer,view,frame,sampler,raster};
  const signature=DD_signature(ctx.getImageData(0,0,raster.width,raster.height).data);
  window.__diffuseDiag={ready:true,stage:'7.3',stageStatus:'PARTIAL_DIAGNOSTIC_ONLY',productionAdmissible:false,sourceGate:'BLOCKED',observer,view,tier,dpr,samplesPerAxis,sourceId:sampler.id,sourceSha256:sampler.sourceSha256,sourceCount:DD_assets.report.residualSourceCount,finiteSourceFlux:sampler.totalRelativeV0Flux,skyPixels:raster.skyPixels,missingPixels:raster.missingPixels,annotationCount:markers,center:{raDeg:center.raDeg,decDeg:center.decDeg},pixelSignature:signature,rasterMs:elapsed,externalSourceClaim:false};
  DD_el('status').style.color='#7dd3c5';DD_el('status').textContent='Registered diagnostic ready · production survey NOT admitted';
  DD_el('readback').textContent=`Accepted UTC: ${new Date(observer.utcMs).toISOString()}\nObserver: ${observer.latDeg.toFixed(2)}°, ${observer.lonDeg.toFixed(2)}°\nSource: ${DD_assets.report.residualSourceCount.toLocaleString('en-GB')} retained catalogue records\nFinite sum: ${sampler.totalRelativeV0Flux.toFixed(8)} V0-relative source flux\nGrid: ${tier}; raster: ${raster.width} × ${raster.height}; DPR ${dpr}\nCentre J2000: RA ${center.raDeg?.toFixed(5)??'below horizon'}°, Dec ${center.decDeg?.toFixed(5)??'—'}°\nAnnotations: ${markers}; unavailable sky pixels: ${raster.missingPixels}\nPhysical atmosphere / full diffuse radiometry: NOT CONNECTED\nObservational completeness: NOT ESTABLISHED`;
 }catch(error){DD_fail(error);}
}
async function DD_boot(){
 if(window.__diffuseAssets)DD_assets=window.__diffuseAssets;
 else{
  const fetchJSON=async path=>{const r=await fetch(path);if(!r.ok)throw new Error('Local asset unavailable: '+path);return r.json();};
  const [catalogue,report,...maps]=await Promise.all([fetchJSON('../data/bright-stars.json'),fetchJSON('../checkpoints/cp7_2/build-report.json'),...['256x128','128x64','64x32'].map(s=>fetchJSON('../data/diffuse/hyg-residual-'+s+'.json'))]);
  DD_assets={catalogue,report,maps:Object.fromEntries(['256x128','128x64','64x32'].map((s,i)=>[s,maps[i]]))};
 }
 DD_samplers=Object.fromEntries(Object.entries(DD_assets.maps).map(([k,v])=>[k,createDiagnosticDiffuseSampler(v)]));
 DD_el('location').addEventListener('change',()=>{const [lat,lon]=DD_locations[DD_el('location').value];DD_el('lat').value=lat;DD_el('lon').value=lon;DD_render();});
 for(const id of ['lat','lon','utc','view','az','alt','fov','roll','tier','dpr','samples','gain','markers'])DD_el(id).addEventListener('change',DD_render);
 for(const [id,step] of [['forward',21600000],['back',-21600000]])DD_el(id).addEventListener('click',()=>{try{const ms=finite(Date.parse(DD_el('utc').value+'Z'),'UTC instant');DD_el('utc').value=new Date(ms+step).toISOString().slice(0,19);DD_render();}catch(error){DD_fail(error);}});
 DD_el('render').addEventListener('click',DD_render);
 DD_el('sky').addEventListener('pointermove',event=>{if(!DD_current)return;const box=DD_el('sky').getBoundingClientRect(),x=(event.clientX-box.left)*DD_current.view.width/box.width,y=(event.clientY-box.top)*DD_current.view.height/box.height;const q=diffuseRayToMap(x,y,DD_current.view,DD_current.frame);
  if(!q.aboveHorizon){DD_el('hover').textContent='Outside the selected sky / below horizon';return;}
  const s=DD_current.sampler.sample(q.raDeg,q.decDeg);DD_el('hover').textContent=`J2000 RA ${q.raDeg.toFixed(4)}°, Dec ${q.decDeg.toFixed(4)}°\n${s.defined?s.value.toFixed(6)+' V0-relative flux/sr':'Unavailable source support'} · not total sky radiance`;
 });
 window.__renderDiffuseDiagnostic=DD_render;DD_render();
}
DD_boot().catch(DD_fail);
