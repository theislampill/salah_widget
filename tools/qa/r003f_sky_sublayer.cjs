'use strict';
// Numerical sky + Moon sublayer. There is no CSS, UI glass, cloud painting,
// browser rasterization or P1 elementsFromPoint mask in this experiment.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {variants,variantSource,hash}=require('./r003f_variants.cjs');
const {buildMasks,measure,compareCards}=require('./r003f_p1.cjs'),{deltaE,terrain,terminator,occultation}=require('./r003f_diagnostics.cjs');
const {phases}=require('./r003f_grid.cjs');
const root=path.resolve(__dirname,'../..'),read=f=>fs.readFileSync(path.join(root,f));
const disc={cx:268.8,cy:55.8,r:49.6}; // §B.4 representative CSS geometry, never a DOM read.
const source=read('moon/src/moon-calendar.mjs').toString().trimEnd();
const op=Object.fromEntries(variants.map(n=>[n,Function(variantSource(source,n)+'\nreturn calendarProxy;')()]));
async function atmosphere(epoch,visibility,calendarOnly=true){
  const {NativeSkyEngine}=await import('../../real-sky/native-engine.mjs');
  const {nativeJob,nativeCalendarComposite}=await import('../../real-sky/native-contract.mjs');
  const {nativeAtmosphereFields,nativeSkyPresentation}=await import('../../real-sky/native-preview.mjs');
  const {encodeNativeDisplay}=await import('../../real-sky/native-host.mjs');
  const data=f=>read('vendor/real-sky/data/'+f).toString();
  const sky=new NativeSkyEngine({catalogueText:data('bright-stars.json'),manifestText:data('registered-starlight/runtime-manifest.json'),
    assetTexts:{128:data('registered-starlight/V-nside128.json')}});
  const snapshot={utcMs:Date.parse(epoch),lat:28.54,lon:-81.38,heightM:30,generation:0,sceneIdentity:'R003F',units:'c',
    weather:{src:'current',temp:21,vis:visibility,rh:visibility===5000?90:55,cloud:0},lp:0,reducedMotion:true,
    camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0}};
  const job=nativeJob(snapshot,true),result=await sky.render(job);assert.equal(result.status,'ready');
  assert.equal(result.raster.atmosphere.cloudTransmission,1);assert.ok(result.raster.diffusePhysicalLinear);
  let raster=result.raster;
  if(raster.physicalState.sun.altDeg>=-20){
    const step=job.options.backgroundStepCss;
    const fields=nativeAtmosphereFields(raster.physicalState,raster.atmosphere,job.options.view,job.options.diffuse.residualNight,Math.ceil(325/step),Math.ceil(530/step));
    raster=nativeSkyPresentation({...raster,solarAerosolLinear:fields.solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,
      lunarBackgroundLinear:fields.lunarBackgroundLinear,twilightDisplay:fields.twilightDisplay},job.options.view,null);
  }else assert.equal(raster.nativeLunarDisplayPrepared,true);
  assert.equal(raster.width,325);assert.equal(raster.height,530);
  const background=encodeNativeDisplay(nativeCalendarComposite(raster),raster.effectiveExposure);
  const info={snapshot,solarAlt:raster.physicalState.sun.altDeg,lunarAlt:raster.physicalState.moon.altDeg,
    skySha256:hash(background),catalogue:result.catalogue,exposure:raster.effectiveExposure};
  if(calendarOnly)assert.ok(info.lunarAlt<-2,'astronomical Moon must be below the calendar-only threshold');
  sky.dispose();return {raster,background,info,encode:encodeNativeDisplay};
}
function compose(api,env,r,linear,geometry=disc,up=0,upper=null){
  const table=linear.data?linear:api.prefixSurface({size:r.surfaceSize,linear,coverage:r.surfaceCoverage}),out=env.background.slice();
  const diameter=2*geometry.r*48/45,ss=r.surfaceSize/(.96*r.surfaceExtent),sx=ss/diameter;
  const ox=r.surfaceSize/2-geometry.cx*sx,oy=r.surfaceSize/2-geometry.cy*sx;
  const raster=env.raster,sky=raster.skyBackgroundLinear??raster.backgroundLinear;
  const x0=Math.max(0,Math.floor(geometry.cx-diameter/2)-1),x1=Math.min(325,Math.ceil(geometry.cx+diameter/2)+1);
  const y0=Math.max(0,Math.floor(geometry.cy-diameter/2)-1),y1=Math.min(530,Math.ceil(geometry.cy+diameter/2)+1);
  const joined=new Float64Array((x1-x0)*(y1-y0)*3),covered=new Uint8Array(joined.length/3);
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
    const i=y*325+x,j=(y-y0)*(x1-x0)+x-x0,sp=api.boxSurface(table,ox+x*sx,oy+y*sx,ox+(x+1)*sx,oy+(y+1)*sx),a=sp[3];
    if(a<=1e-10)continue;
    if(up && upper){
      const phys=api.boxSurface(upper,ox+x*sx,oy+y*sx,ox+(x+1)*sx,oy+(y+1)*sx);
      for(let k=0;k<3;k++)sp[k]=up*phys[k]+(1-up)*sp[k];
    }
    const gas=sky.subarray(3*i,3*i+3),direct=[0,1,2].map(k=>raster.stellarLinear[3*i+k]+raster.diffusePhysicalLinear[3*i+k]);
    covered[j]=1;joined.set(api.joinLunarPixel({gas,direct,premult:sp,coverage:a,opacity:1,cloud:[0,0,0,0],exposure:raster.effectiveExposure}),3*j);
  }
  const codes=env.encode(joined,raster.effectiveExposure);
  for(let j=0;j<covered.length;j++)if(covered[j]){
    const i=(y0+Math.floor(j/(x1-x0)))*325+x0+(j%(x1-x0));out.set(codes.subarray(4*j,4*j+4),4*i);
  }
  return out;
}
function verifyReferenceFrames(report,original){
  assert.deepEqual(report.sky,original.sky,'physical sky fields changed since the primary capture');
  assert.equal(report.rows.length,original.rows.length);
  for(const [i,r] of report.rows.entries()){
    const prior=original.rows[i];
    for(const key of ['environment','tier','fraction','waxing','referenceSha256','referenceP95','g0','litPixels','darkPixels'])
      assert.equal(r[key],prior[key],'reference or aperture changed: '+key);
    for(const name of variants){
      assert.equal(r.metrics[name].sha256,prior.metrics[name].sha256,'candidate pixels changed: '+name);
      assert.deepEqual(r.metrics[name].terrain,prior.metrics[name].terrain,'terrain statistics drifted: '+name);
    }
  }
}
async function main(){
  const {values}=require('node:util').parseArgs({options:{out:{type:'string'},owner:{type:'boolean'},invariants:{type:'boolean'}}});
  const src=f=>read('moon/src/'+f+'.mjs').toString();
  const shared=['asset-digest','surface_v5','moon-detail','moon-calendar','moon-engine','moon-quality','moon-precision','moon-initial-compact'].map(src).join('\n');
  const api=Function(shared+'\nreturn {MoonEngine,adaptiveRender,canonicalScene,MOON_PROFILE,decodeCompactReceivers,boxSurface,prefixSurface,joinLunarPixel};')();
  const manifest=JSON.parse(read('moon/asset-manifest.json')),compact=JSON.parse(read('moon/initial-compact-manifest.json')),pin=JSON.parse(read('moon/initial-manifest.json'));
  const engine=await api.MoonEngine.create({manifest,wasm:read('moon/moon_kernel.wasm'),dem:read('moon/'+manifest.assets.dem.path),colour:read('moon/'+manifest.assets.colour.path)});
  let material;
  const seed=Function(shared+'\nreturn function(calendarProxy){'+src('moon-initial')+'\nreturn createInitialMoon;}')()((m,c,v)=>{material=m;return op.B0(m,c,v);})(
    api.decodeCompactReceivers(new Uint8Array(read('moon/assets/initial-compact.bin')),compact),{...pin,sha256:compact.decodedSha256});
  const size=values.owner?540:160;
  const refProfile={...api.MOON_PROFILE,profile_id:'unboosted-v5-01',mode:'reference',lift:0};
  const envs=await Promise.all([atmosphere('2026-11-15T09:42Z',24000),atmosphere('2026-11-15T09:42Z',5000),
    atmosphere('2026-11-15T11:05Z',24000)]);
  const rows=[],offsets=new Map(),allowed=new Uint8Array(325*530).fill(1);
  const samples=values.owner?[.01,.31385485]:phases,senses=values.owner?[true]:[true,false];
  for(const fraction of samples)for(const waxing of senses){
    const scene=api.canonicalScene({fraction,waxing,size});
    const render=s=>values.owner?api.adaptiveRender(engine,s):engine.render(s,{radial:4,azimuth:16,qualityFields:true});
    const ref=await render(api.canonicalScene({fraction,waxing,size,profile:refProfile}));
    const work=await render(scene);
    const physicalMaterial=new Float32Array(work.surfaceSize**2*3);
    const raw=new Float64Array(engine.e.memory.buffer,engine.e.get_pixels(),24*work.surfaceSize**2);
    for(let i=0;i<work.surfaceSize**2;i++)for(let k=0;k<3;k++)physicalMaterial[3*i+k]=raw[24*i+6+k];
    const initial=seed.render(scene);
    for(const [e,env] of envs.entries()){
      const reference=compose(api,env,ref,ref.surfaceLinear);
      for(const [tier,r,m] of [['compact-initial',initial,material],['kernel',work,physicalMaterial]]){
        const key=[e,tier,waxing].join('/'),base=compose(api,env,r,op.B0(m,r.surfaceCoverage,r.surfaceLinear));
        if(fraction===.01)offsets.set(key,base);
        const masks=buildMasks({dpr:1,fraction,disc,offsetDisc:disc,newMoon:offsets.get(key),reference,headerRects:[],topIsSkyOrMoon:allowed});
        const row={environment:e,tier,receiverSize:r.surfaceSize,fraction,waxing,referenceSha256:hash(reference),
          g0:masks.g0,referenceP95:masks.p95,referenceQuality:ref.diagnostics.quality?.status??'fixed-64',
          calendarQuality:r.diagnostics.quality?.status??'fixed-64',litPixels:masks.lit.length,darkPixels:masks.dark.length,metrics:{}};
        const plain={};
        if(values.invariants){
          const summarizeOccultation=frame=>{
            const o=occultation(masks,frame,env.background);
            return {median:o.median,hiddenPeaks:o.hiddenPeaks,maxOverMedian:o.maxOverMedian,
              coincidentPeaks:o.starCoincidences?.length??null};
          };
          row.reference={terrain:terrain(masks,reference),occultation:summarizeOccultation(reference)};
          row.b0={terrain:terrain(masks,base),occultation:summarizeOccultation(base)};
          row.maskOverlapPixels=masks.maskOverlapPixels;
          for(const name of variants){
            const frame=name==='B0'?base:compose(api,env,r,op[name](m,r.surfaceCoverage,r.surfaceLinear));
            const diff=compareCards(1,disc,base,frame),cand=terrain(masks,frame),cv=row.reference.terrain.litCV;
            const sd=row.b0.terrain.darkSdL,identifiable=fraction>.02&&masks.p95>0&&masks.lit.length>0&&masks.maskOverlapPixels===0;
            const term=fraction>=.15&&fraction<=.85?terminator(masks,frame,reference,waxing):null;
            row.metrics[name]={sha256:hash(frame),changedPixels:diff.changedPixels,outside106R:diff.outside.length,
              maxOutsideCode:diff.outside.reduce((m,v)=>Math.max(m,...v.delta.map(Math.abs)),0),terrain:cand,
              relativeLitCV:identifiable&&Number.isFinite(cand.litCV)&&cv>0?cand.litCV/cv:null,
              darkSdMinusB0:identifiable&&Number.isFinite(cand.darkSdL)&&Number.isFinite(sd)?cand.darkSdL-sd:null,
              occultation:summarizeOccultation(frame),terminator:term};
          }
          rows.push(row);continue;
        }
        for(const name of variants){
          const frame=name==='B0'?base:compose(api,env,r,op[name](m,r.surfaceCoverage,r.surfaceLinear)),metric=measure(masks,frame);
          if(!name.endsWith('-T'))plain[name]=frame;
          row.metrics[name]={sha256:hash(frame),discY:metric.disc.meanY,litMinusSkyL:metric.deltaLitSkyL??null,
            physicalMinusLitL:metric.deltaPhysicalCandidateL??null,terrain:terrain(masks,frame),
            toneDeltaE76:deltaE(masks,frame,plain[name.split('-')[0]])};
        }
        rows.push(row);
      }
    }
    console.log('PASS sublayer '+fraction+' '+waxing);
  }
  const report={protocol:values.invariants?'R003F/sublayer-reference-checks/1':'R003F/headless-sky-sublayer/1',classification:'Numerical field projection; not a native card or P1 result',
    geometry:{disc,dpr:1,groupOpacity:1,photoToOccluderRadius:48/45},sky:envs.map(x=>x.info),
    sampleSet:values.owner?'owner phase at issue-reported precision, empirical adaptive worker and compact initial':'canonical phase grid, fixed 64-sample worker and compact initial',
    omissions:['browser and device compositor','native cloud canvas','header glass, strap, buckle, text and other card layers','native hit-tested annulus','per-document phase bucketing'],
    rows};
  if(values.invariants){
    const original=JSON.parse(read('docs/state-contracts/evidence/R003F/sky-sublayer-'+(values.owner?'owner':'grid')+'.json'));
    verifyReferenceFrames(report,original);
  }
  fs.writeFileSync(values.out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
}
module.exports={atmosphere,compose,disc,op,verifyReferenceFrames};
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1;});
