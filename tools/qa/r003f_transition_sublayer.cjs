'use strict';
// Evaluate the same pre-UI numerical sublayer at real and prescribed
// altitudes. Deterministic ephemeris steps are not an elapsed-time recording.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {atmosphere,compose,disc,op}=require('./r003f_sky_sublayer.cjs'),{variants}=require('./r003f_variants.cjs');
const {buildMasks,lightness,luminance}=require('./r003f_p1.cjs'),{horizon,night}=require('./r003f_grid.cjs');
const {compareTransitions}=require('./r003f_diagnostics.cjs'),{load}=require('../../tests/r001d-harness.cjs');
const root=path.resolve(__dirname,'../..'),read=f=>fs.readFileSync(path.join(root,f));
async function main(){
  const {values}=require('node:util').parseArgs({options:{out:{type:'string'}}});
  const code=['asset-digest','surface_v5','moon-detail','moon-engine','moon-quality'].map(f=>read('moon/src/'+f+'.mjs').toString()).join('\n');
  const api=Function(code+'\nreturn {MoonEngine,canonicalScene,MOON_PROFILE,boxSurface,prefixSurface,joinLunarPixel};')();
  const manifest=JSON.parse(read('moon/asset-manifest.json')),engine=await api.MoonEngine.create({manifest,wasm:read('moon/moon_kernel.wasm'),
    dem:read('moon/'+manifest.assets.dem.path),colour:read('moon/'+manifest.assets.colour.path)});
  const h=load();
  function snapshot(time,fraction,waxing,altitude){
    return h.run('nativeLunarSnapshot(new Date('+time+'),28.54,-81.38,'+JSON.stringify({moon:fraction,wax:waxing?'1':'0',
      ...(altitude===null?{}:{moonAlt:altitude,moonH:150})})+')');
  }
  const atBase=snapshot(Date.parse(night),.314,true,-2);
  function geometry(m){
    return {cx:disc.cx+m.x-atBase.x,cy:disc.cy+m.y-atBase.y,r:disc.r*m.scale/atBase.scale};
  }
  const prefix=(r,v)=>api.prefixSurface({size:r.surfaceSize,linear:v,coverage:r.surfaceCoverage});
  async function create(fraction,waxing){
    const draw=profile=>engine.render(api.canonicalScene({fraction,waxing,size:160,profile}),{radial:4,azimuth:16,qualityFields:true});
    const reference=await draw({...api.MOON_PROFILE,profile_id:'unboosted-v5-01',mode:'reference',lift:0});
    const surface=await draw(api.MOON_PROFILE),m=new Float32Array(160*160*3);
    const raw=new Float64Array(engine.e.memory.buffer,engine.e.get_pixels(),24*160*160);
    for(let i=0;i<160*160;i++)for(let k=0;k<3;k++)m[3*i+k]=raw[24*i+6+k];
    return {fraction,waxing,surface,physical:prefix(surface,surface.surfaceLinear),ref:prefix(reference,reference.surfaceLinear),
      variants:Object.fromEntries(variants.map(n=>[n,prefix(surface,op[n](m,surface.surfaceCoverage,surface.surfaceLinear))]))};
  }
  const states=[];for(const f of [.08,.314,.5,.85,.99])states.push(await create(f,![.5,.85].includes(f)));
  const offset=await create(.01,true),allowed=new Uint8Array(325*530).fill(1);
  const L=(indices,rgba)=>indices.length?lightness(indices.reduce((s,i)=>s+luminance(rgba,i),0)/indices.length):null;
  function sample(env,s,m,lower,minute){
    const g=geometry(m), frame=(table,up=0)=>compose(api,env,s.surface,table,g,up,s.physical);
    const baseNew=compose(api,env,offset.surface,offset.variants.B0,g,m.up,offset.physical);
    const reference=frame(s.ref),masks=buildMasks({dpr:1,fraction:s.fraction,disc:g,offsetDisc:g,newMoon:baseNew,reference,headerRects:[],topIsSkyOrMoon:allowed});
    const refL=L(masks.lit,reference),row={minute,altitude:m.alt,up:m.up,geometry:g,referenceL:refL,maskCount:masks.lit.length,variants:{}};
    row.offsetG0=masks.g0;row.referenceP95=masks.p95;row.usable=Number.isFinite(refL)&&masks.p95>0&&masks.lit.length>0&&masks.maskOverlapPixels===0;
    for(const name of variants){
      const card=frame(s.variants[name],m.up),litL=row.usable?L(masks.lit,card):null;
      const low=lower?L(masks.lit,lower[name]):null;
      row.variants[name]={litL,minus2L:low,convex:litL===null||low===null||m.up===0||m.up===1?null:litL>=Math.min(low,refL)-.5&&litL<=Math.max(low,refL)+.5};
    }
    return row;
  }
  const fixed=await atmosphere(night,24000),sweeps=[];
  for(const s of states){
    const low=Object.fromEntries(variants.map(n=>[n,compose(api,fixed,s.surface,s.variants[n],geometry(atBase))]));
    const rows=horizon.map(a=>sample(fixed,s,snapshot(Date.parse(night),s.fraction,s.waxing,a),low,null));
    const checks=Object.fromEntries(variants.map(n=>{
      const curve=rows.map(r=>r.variants[n].litL);
      return [n,{nondecreasing:curve.every(Number.isFinite)?curve.every((l,i)=>!i||l>=curve[i-1]):null,minus2ToMinus1L:curve[horizon.indexOf(-1)]!==null&&curve[horizon.indexOf(-2)]!==null?curve[horizon.indexOf(-1)]-curve[horizon.indexOf(-2)]:null,
        convexAll:rows.filter(r=>r.up>0&&r.up<1).every(r=>r.variants[n].convex!==null)?rows.every(r=>r.variants[n].convex!==false):null}];
    }));
    sweeps.push({fraction:s.fraction,waxing:s.waxing,rows,checks});
  }
  const sequences=states.filter(s=>[.314,.99].includes(s.fraction)).map(s=>({s,rows:[]}));
  const sky=[],begin=Date.parse('2026-11-03T05:50:00Z');
  for(let i=0;i<50;i++){
    const time=begin+i*60000,env=await atmosphere(new Date(time).toISOString(),24000,false);
    sky.push({minute:time/60000,skySha256:env.info.skySha256,exposure:env.info.exposure,solarAlt:env.info.solarAlt,lunarAlt:env.info.lunarAlt});
    for(const {s,rows} of sequences)rows.push(sample(env,s,snapshot(time,s.fraction,s.waxing,null),null,time/60000));
    if(i%10===0)console.log('Sublayer geometry minute',i);
  }
  const motion=sequences.map(({s,rows})=>{
    const series=n=>rows.map(r=>({litL:r.variants[n].litL,minute:r.minute}));
    // DB3 concerns moonrise: bracket -2 .. +4 with the immediately adjacent
    // geometry minutes, and also preserve every pre-roll/post-roll reading.
    const first=rows.findIndex(r=>r.altitude>-2)-1,end=rows.findIndex(r=>r.altitude>=4)+1;
    assert.ok(first>=0 && end>first);
    const baseline=series('B0').slice(first,end);
    return {fraction:s.fraction,waxing:s.waxing,first,endExclusive:end,rows,
      comparisons:Object.fromEntries(variants.map(n=>[n,compareTransitions(series(n).slice(first,end),baseline)]))};
  });
  fs.writeFileSync(values.out,JSON.stringify({protocol:'R003F/transition-sublayer/1',classification:'actual native ephemeris and atmospheric fields, prescribed projection, fixed 64-sample V5; no browser, CSS, cloud or compositor cadence',
    fixed:fixed.info,sky,sweeps,motion},null,2)+'\n',{flag:'wx'});
  console.log('PASS 85 altitude cells and 100 minute/phase cells x eight variants');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
