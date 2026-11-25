'use strict';
// Exercise the emitted test-build operators in both publication paths. No DOM,
// atmosphere or human appearance measurement is inferred from these receipts.
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {variants,renderVariant,unpack,hash}=require('./r003f_variants.cjs');
const root=path.resolve(__dirname,'../..'), read=name=>fs.readFileSync(path.join(root,name));
const src=name=>read('moon/src/'+name+'.mjs').toString();
const bytes=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength);
const fractions=[.01,.04,.08,.15,.314,.5,.75,.85,.99], Y=[.2126,.7152,.0722];
// The production detail join is exercised on real V5 receiver values against
// controlled foreground gas, distant light and cloud fields. The raw fields
// deliberately carry no claim about the atmosphere of the Orlando screenshot.
function probeJoin(api, cloudChannel, v) {
  const gas=[.002,.003,.004],stars=[.12,.24,.36],black=[0,0,0],clear=[0,0,0,0],exposure=12;
  let samples=0, opaque=0, empty=0, partial=0, maxDistantLeak=0, maxConvexError=0, maxCloudDifference=0;
  const physical=api.prefixSurface({size:v.surfaceSize,linear:v.surfaceLinear,coverage:v.surfaceCoverage});
  const token=api.prefixSurface({size:v.surfaceSize,linear:v.calendarLinear,coverage:v.surfaceCoverage});
  // 43x43 fixed boxes deliberately straddle the projected limb.
  for(let y=0;y<43;y++)for(let x=0;x<43;x++){
    const step=v.surfaceSize/43,box=[x*step,y*step,(x+1)*step,(y+1)*step];
    const p=api.boxSurface(physical,...box),c=api.boxSurface(token,...box),a=p[3];
    assert.equal(a,c[3]);samples++;
    if(a>=1-1e-10)opaque++;else if(a<=1e-10)empty++;else partial++;
    const join=(surface,direct)=>api.joinLunarPixel({gas,direct,premult:surface,coverage:a,opacity:.78,cloud:clear,exposure});
    const calendar=join(c,stars),upper=join(p,stars),withoutStars=join(c,black);
    for(let k=0;k<3;k++){
      maxDistantLeak=Math.max(maxDistantLeak,Math.abs(calendar[k]-withoutStars[k]-stars[k]*(1-a)));
      maxCloudDifference=Math.max(maxCloudDifference,Math.abs(cloudChannel(calendar[k],84,1,exposure)-cloudChannel(upper[k],84,1,exposure)));
    }
    for(const up of [.00833333333333334,1/12,1/6,.25,1/3,.5,2/3,5/6]){
      const blended=c.slice(0,3).map((value,k)=>up*p[k]+(1-up)*value),mid=join(blended,stars);
      for(let k=0;k<3;k++)maxConvexError=Math.max(maxConvexError,
        Math.min(upper[k],calendar[k])-mid[k],mid[k]-Math.max(upper[k],calendar[k]));
    }
  }
  assert.ok(opaque&&partial&&empty);
  assert.ok(maxDistantLeak<1e-12&&maxCloudDifference<1e-12&&maxConvexError<1e-12);
  return {samples,opaque,partial,empty,maxDistantLeak,maxCloudDifference,maxConvexError};
}
async function main(){
  const {values}=require('node:util').parseArgs({options:{out:{type:'string'}}});
  const index=read('index.html').toString(), original=src('moon-calendar').trimEnd();
  const shared=['asset-digest','surface_v5','moon-detail','moon-engine','moon-quality','moon-initial-compact'].map(src).join('\n');
  const api=Function(shared+'\nreturn {MoonEngine,canonicalScene,decodeCompactReceivers,boxSurface,prefixSurface,joinLunarPixel};')();
  const manifest=JSON.parse(read('moon/asset-manifest.json')), compact=JSON.parse(read('moon/initial-compact-manifest.json'));
  // Match the actual packed string, decode manifest and decoded identity installed by build_moon.
  const install=/const text=atob\("([A-Za-z0-9+/=]+)"\).*?const bytes=decodeCompactReceivers\(packed,(\{.*?\})\);window.SalahMoonInitial=createInitialMoon\(bytes,(\{.*?\})\);/.exec(index);
  assert.ok(install,'served startup receipt');
  assert.deepEqual(JSON.parse(install[2]),compact);
  const decodedPin=JSON.parse(install[3]), packed=Buffer.from(install[1],'base64');
  assert.equal(hash(packed),compact.sha256); assert.equal(decodedPin.sha256,compact.decodedSha256);
  const decoded=api.decodeCompactReceivers(new Uint8Array(packed),compact);
  const {nativeCloudChannel}=await import('../../real-sky/native-cloud-transfer.mjs');
  const engine=await api.MoonEngine.create({manifest,wasm:read('moon/moon_kernel.wasm'),
    dem:read('moon/'+manifest.assets.dem.path),colour:read('moon/'+manifest.assets.colour.path)});
  const builds=variants.map(name=>{
    const {html,identity}=renderVariant(index,original,name), {worker}=unpack(html);
    const extract=s=>s.slice(s.indexOf('function calendarProxy('),s.indexOf('function blendCalendarBytes('));
    const hostOp=extract(html), workerOp=extract(worker);
    assert.equal(hostOp,workerOp,'both installed operators');
    const workerPublisher=Function(shared+'\n'+worker.slice(worker.indexOf('function calendarProxy('),worker.indexOf('// moon-engine.mjs'))+
      '\nreturn {calendarProxy,nativeCalendarResult,blendCalendarBytes};')();
    const startup=Function(shared+'\n'+hostOp+'\n'+src('moon-initial')+'\nreturn createInitialMoon;')()(decoded,decodedPin);
    return {name,identity,startup,workerPublisher};
  });
  const records=['compact-initial-gains','surface-gains'].map(file=>JSON.parse(read('docs/state-contracts/evidence/R003F/'+file+'.json')).rows);
  const rows=[];
  for(const tier of ['compact-initial','fixed-kernel'])for(const fraction of fractions)for(const waxing of [false,true]){
    const initial=tier==='compact-initial', size=initial?540:160;
    const scene=api.canonicalScene({fraction,waxing,size,diameter:103.68,outSize:108});
    const oracle=records[initial?0:1].find(r=>r.size===size&&r.fraction===fraction&&r.waxing===waxing);
    assert.ok(oracle);
    const kernel=initial?null:await engine.render(scene,{radial:4,azimuth:16,qualityFields:true});
    const row={tier,size,fraction,waxing,variants:{}};
    let physical,coverage,lower;
    for(const {name,startup,workerPublisher} of builds){
      const v=initial?startup.render(scene):{...kernel,...workerPublisher.nativeCalendarResult(engine,kernel)};
      const physicalHash=hash(bytes(v.rgba)),coverageHash=hash(bytes(v.surfaceCoverage)),surfaceHash=hash(bytes(v.surfaceLinear));
      const identity=[physicalHash,coverageHash,surfaceHash];
      if(!physical){physical=identity;coverage=v.surfaceCoverage;lower=v.calendarRgba;row.physical={backing:physicalHash,coverage:coverageHash,surface:surfaceHash};}
      assert.deepEqual(identity,physical,'physical backing/surface/coverage changed');
      assert.equal(v.rgba.length,v.calendarRgba.length);
      let alphaChanges=0, zeroAlphaRgbChanges=0, codeChanges=0;
      for(let i=0;i<v.rgba.length;i+=4){
        const changed=[0,1,2].some(k=>v.calendarRgba[i+k]!==lower[i+k]);
        codeChanges+=Number(changed);zeroAlphaRgbChanges+=Number(changed&&!v.rgba[i+3]);
        alphaChanges+=Number(v.rgba[i+3]!==v.calendarRgba[i+3]);
      }
      assert.equal(alphaChanges,0);
      const join=probeJoin(api,nativeCloudChannel,v);
      const token=hash(bytes(v.calendarLinear)),rule=name.split('-')[0],gain=oracle.gains[rule];
      if(!name.endsWith('-T'))assert.equal(token,oracle.tokenSha256[rule]);
      let maxYError=0,maxChannelError=0,opaque=0;
      const source=v.surfaceLinear, out=v.calendarLinear;
      for(let i=0;i<coverage.length;i++){
        let sum=0,actual=0;
        for(let k=0;k<3;k++){sum+=Y[k]*source[i*3+k]*gain;actual+=Y[k]*out[i*3+k];}
        maxYError=Math.max(maxYError,Math.abs(sum-actual));
        for(let k=0;k<3;k++){
          const expected=name.endsWith('-T')?.4*source[3*i+k]*gain+.6*sum*[.94,1,1.10][k]/(.94*Y[0]+Y[1]+1.10*Y[2]):source[3*i+k]*gain;
          maxChannelError=Math.max(maxChannelError,Math.abs(Math.fround(expected)-out[3*i+k]));
        }
        if(coverage[i]===1)opaque++;
        if(coverage[i]===0)assert.ok(out[3*i]===0 && out[3*i+1]===0 && out[3*i+2]===0);
      }
      assert.ok(maxChannelError<1e-7 && maxYError<1e-7);
      assert.deepEqual(workerPublisher.blendCalendarBytes(v.rgba,v.calendarRgba,1),v.rgba);
      assert.deepEqual(workerPublisher.blendCalendarBytes(v.rgba,v.calendarRgba,0),v.calendarRgba);
      row.variants[name]={token,backing:hash(bytes(v.calendarRgba)),maxYError,maxChannelError,opaque,
        alphaChanges,zeroAlphaRgbChanges,changedBackingPixels:codeChanges,join};
    }
    rows.push(row);
  }
  const report={protocol:'R003F/publication-paths/1',indexSha256:hash(index),packed:compact.sha256,
    decoded:decodedPin.sha256,parent:compact.parentReceiverSha256,builds:builds.map(b=>b.identity),rows};
  fs.writeFileSync(values.out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log('PASS '+rows.length+' surfaces x '+builds.length+' emitted test variants');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
