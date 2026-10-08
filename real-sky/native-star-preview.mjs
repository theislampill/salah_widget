import {DiffuseAssetStore,parseDiffuseManifest} from './core/src/diffuse-assets.mjs';
import {validateCatalogue} from './core/src/catalogue.mjs';
import {DIFFUSE_MANIFEST_SHA256} from './core/src/diffuse-manifest-pin.mjs';
import {projectCatalogue,discOccults} from './core/src/scene.mjs';
import {projectPerspective} from './core/src/projection.mjs';
import {erf} from './core/src/renderer.mjs';
import {psfComponents} from './core/src/optics.mjs';
import {spectralStarFlux} from './core/src/spectral.mjs';
import {normaliseAtmosphere,directTransmission} from './core/src/atmosphere.mjs';
import {nativeInverseCode} from './native-composition.mjs';
import {nativeEncodingThresholds} from './native-encoding.mjs';

let previewEdges=null;
const preparedFields=new WeakMap();
function previewCode(value,exposure){
 if(!previewEdges)previewEdges=nativeEncodingThresholds();
 const y=exposure*Math.max(0,value);let low=0,high=256;
 while(high-low>1){const middle=(low+high)>>>1;if(y<previewEdges[middle])high=middle;else low=middle;}
 return low;
}

/** Exact separable evaluation of the reference preview PSF. The reference
 * renderer repeats each horizontal erf at every row and updates two zero
 * channels for each spectral component. Cache those horizontal integrals and
 * write only its nonzero channel; preserve support, arithmetic and summation
 * order. No source/halo cutoff, resolution, spectrum or quality change. */
export function renderPreviewStars(sources,fluxAt,visible){
 const width=325,height=530,linear=new Float64Array(width*height*3);
 const parts=[610,550,460].map(wavelengthNm=>psfComponents({preset:'reference',wavelengthNm,coreSigmaCss:.55,scatterSigmaCss:2.2,scatterFraction:.035}));
 let drawn=0;
 for(const s of sources){
  if(s.emission?.enabled===false||s.altDeg<0||s.visible===false||!visible(s))continue;
  const rgb=fluxAt(s).rgb;
  if(!Array.isArray(rgb)||!rgb.every(v=>Number.isFinite(v)&&v>=0)||!Number.isFinite(s.x)||!Number.isFinite(s.y))throw new RangeError('Invalid preview stellar source');
  if(rgb.every(v=>v===0))continue;
  for(let channel=0;channel<3;channel++)for(const part of parts[channel]){
   if(part.weight<=0)continue;
   const energy=rgb[channel]*part.weight,sigma=part.sigmaCss,support=Math.ceil(6*sigma)+1,inv=1/(sigma*Math.SQRT2);
   const xs=Math.max(0,Math.floor(s.x)-support),xe=Math.min(width-1,Math.floor(s.x)+support),ys=Math.max(0,Math.floor(s.y)-support),ye=Math.min(height-1,Math.floor(s.y)+support);
   const horizontal=[];
   for(let x=xs;x<=xe;x++)horizontal.push(.5*(erf((x+1-s.x)*inv)-erf((x-s.x)*inv)));
   for(let y=ys;y<=ye;y++){
    const wy=.5*(erf((y+1-s.y)*inv)-erf((y-s.y)*inv));
    for(let x=xs;x<=xe;x++)linear[3*(y*width+x)+channel]+=energy*Math.max(0,horizontal[x-xs]*wy);
   }
  }
  drawn++;
 }
 return {linear,width,height,drawn};
}

/** Bounded bright-catalogue preview while the registered diffuse worker is
 * pending/unavailable. Uses the pinned catalogue and unchanged astrometry,
 * spectral extinction and pixel-integrated reference PSF. It is not the full
 * catalogue/diffuse quality tier. No prayer/solar-altitude visibility switch.
 */
export class NativeStarPreview {
 static async create(pack){
  // The same pinned byte/hash/schema admission, with the large catalogue hash
  // off the UI thread. The reference store's synchronous JS SHA-256 blocked
  // Firefox's startup controls before any Moon surface was published.
  if(!globalThis.crypto?.subtle)return new NativeStarPreview(pack);
  const manifest=parseDiffuseManifest(pack.manifestText,DIFFUSE_MANIFEST_SHA256);
  if(typeof pack.catalogueText!=='string')throw new TypeError('catalogue must be exact UTF-8 text');
  const bytes=new TextEncoder().encode(pack.catalogueText);
  if(bytes.byteLength!==manifest.catalogue.bytes)throw new RangeError('catalogue byte size mismatch');
  const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
  if(Array.from(digest,x=>x.toString(16).padStart(2,'0')).join('')!==manifest.catalogue.sha256)throw new TypeError('catalogue content hash mismatch');
  const catalogue=validateCatalogue(JSON.parse(pack.catalogueText)),renderer=Object.create(NativeStarPreview.prototype);
  const freeze=x=>{if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))freeze(v);Object.freeze(x);}return x;};
  renderer.catalogue=freeze({...catalogue,stars:catalogue.stars.filter(s=>s.emission?.enabled!==false&&s.vmag<=4.5)});
  renderer.identity={sha256:manifest.catalogue.sha256,totalRecords:catalogue.stars.length,previewRecords:renderer.catalogue.stars.length,maximumMagnitude:4.5};
  return renderer;
 }
 constructor(pack){
  const store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);
  this.catalogue={...store.catalogue,stars:store.catalogue.stars.filter(s=>s.emission?.enabled!==false&&s.vmag<=4.5)};
  this.identity={sha256:store.manifest.catalogue.sha256,totalRecords:store.catalogue.stars.length,previewRecords:this.catalogue.stars.length,maximumMagnitude:4.5};store.dispose();
 }
 render(job,state,display=null){
  const started=performance.now(),a=normaliseAtmosphere(job.options.atmosphere),sources=projectCatalogue(this.catalogue,job.observer,h=>projectPerspective(h,job.options.view));
  const moon={...state.moon,radiusDeg:state.moon.angularRadiusDeg??.25};
  const visible=s=>s.visible&&s.altDeg>=0&&(moon.altDeg+moon.radiusDeg<0||!discOccults(s,moon)),flux=new Map(),sum=[0,0,0];
  for(const s of sources)if(visible(s)){
   const f=spectralStarFlux(s,s.altDeg,{}, {response:'CIE1931',transportAt:lambda=>directTransmission(lambda,s.altDeg,a,1)});flux.set(s,f);
   for(let k=0;k<3;k++)sum[k]+=f.rgb[k];
  }
  let belowByteResolution=false;
  if(display){
   const {background,exposure:E}=display;if(background.length!==325*530*4)throw new RangeError('Catalogue contrast dimensions');
   const seen=new Uint8Array(256*3),decode=Float64Array.from({length:256},(_,i)=>nativeInverseCode(i,E));belowByteResolution=true;
   // Each nonnegative reference PSF integrates to <=1. Concentrating ALL
   // visible flux in one pixel is therefore a conservative upper bound.
   // Test every background code actually present against the exact encoder.
   // 1e-10 is conservative binary64 accumulation slack, not a light gain.
   for(let i=0;i<background.length&&belowByteResolution;i+=4)for(let k=0;k<3;k++){
    const code=background[i+k],at=3*code+k;if(seen[at])continue;seen[at]=1;
    if(previewCode(decode[code]+sum[k]*(1+1e-10),E)!==code){belowByteResolution=false;break;}
   }
  }
  const stars=belowByteResolution?{linear:new Float64Array(325*530*3),width:325,height:530,drawn:0}:renderPreviewStars(sources,s=>flux.get(s),visible);
  return {...stars,sources:sources.filter(s=>s.visible),diagnostics:{...this.identity,drawn:stars.drawn,belowByteResolution,summedFluxBound:sum,renderMs:performance.now()-started,utcMs:job.observer.utcMs,quality:'bright-catalogue-preview; registered diffuse and fainter catalogue pending',visibility:'shared apparent background/exposure; no solar threshold; native clouds/calendar once'}};
 }
}

/** Keep stellar PSFs at native325x530 resolution even when the atmosphere is
 * spatially reduced. The already resampled atmospheric bytes are retained;
 * a lookup reverses their shared encoding, then stars join before encoding.
 */
export function joinNativeStarPreview(preview,background,stars){
 if(!(background instanceof Uint8ClampedArray)||background.length!==325*530*4||stars.linear.length!==325*530*3)throw new RangeError('Catalogue preview dimensions');
 const E=preview.raster.effectiveExposure,decode=Float64Array.from({length:256},(_,i)=>nativeInverseCode(i,E)),source=new Uint8ClampedArray(background),stellar=new Float64Array(stars.linear.length),rgba=new Uint8ClampedArray(source);
 for(let p=0;p<325*530;p++)for(let k=0;k<3;k++){
  const i=3*p+k,v=stars.linear[i];if(!Number.isFinite(v)||v<0)throw new RangeError('Catalogue preview channel');
  stellar[i]=v;
  // Unchanged atmospheric bytes already passed the SAME encoder. Re-encode
  // only actual PSF support, rather than all517k channels twice per preview.
  if(v>0)rgba[4*p+k]=previewCode(decode[source[4*p+k]]+v,E);
 }
 // Display preparation does not need two more full raw planes. Materialize
 // them only for a raw-field consumer (including device-resolution Moon gas).
 // Own the inputs first and validate EVERY stellar channel before returning;
 // this is scheduling/allocation only, never a star or atmosphere quality cut.
 let gas=null,linear=null;
 const atmosphere=()=>{
  if(!gas){gas=new Float64Array(stellar.length);for(let p=0;p<325*530;p++)for(let k=0;k<3;k++)gas[3*p+k]=decode[source[4*p+k]];}
  return gas;
 };
 const raster={...preview.raster,width:325,height:530,
  get linear(){if(!linear){const g=atmosphere();linear=new Float64Array(stellar.length);for(let i=0;i<linear.length;i++)linear[i]=g[i]+stellar[i];}return linear;},
  get backgroundLinear(){return atmosphere();},get skyBackgroundLinear(){return atmosphere();},stellarLinear:stellar,starPreview:stars.diagnostics};
 preparedFields.set(raster,{source,decode});
 return {...preview,rgba,atmosphereRGBA:source,quality:'physical-background-and-bright-catalogue-preview',raster,diagnostics:{...preview.diagnostics,stars:stars.diagnostics}};
}

/** Exact display-byte counterpart of nativeCalendarRegion. Only the moving
 * calendar footprint differs from the prepared stellar image. This is not a
 * lower quality tier or a relaxed age fence; byte equality is regression-tested.
 */
export function nativeStarPreviewRegion(preview,mask,rows){
 const r=preview.raster,n=325*rows;if(!Number.isInteger(rows)||rows<1||rows>530||mask&&mask.length!==n)throw new RangeError('Catalogue preview mask dimensions');
 const base=preview.rgba.subarray(0,n*4);if(!mask)return base;
 const out=new Uint8ClampedArray(base),prepared=preparedFields.get(r);
 for(let p=0;p<n;p++){
  const m=mask[p];if(!Number.isFinite(m)||m<0||m>1)throw new RangeError('Catalogue preview mask');if(m===1)continue;
  for(let k=0;k<3;k++)out[4*p+k]=m===0?preview.atmosphereRGBA[4*p+k]:previewCode((prepared?prepared.decode[prepared.source[4*p+k]]:r.skyBackgroundLinear[3*p+k])+r.stellarLinear[3*p+k]*m,r.effectiveExposure);
 }
 return out;
}
