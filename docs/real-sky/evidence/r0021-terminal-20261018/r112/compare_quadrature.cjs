'use strict';
// Owner-approved single numerical discriminator. No product source mutation,
// browser, performance claim, quality relaxation or automatic implementation.
// Reuse the real four-row MoonPool and existing test local-engine adapter.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const [root,out,sceneFile]=process.argv.slice(2);assert(root&&out&&sceneFile);assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),read=n=>fs.readFileSync(path.join(root,'moon/src',n),'utf8');
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const originals=Object.fromEntries(units.map(n=>[n,read(n)]));
const quality=originals['moon-quality.mjs'],old='8192:[64,128]',replacement='8192:[32,256]';
assert.equal(quality.split(old).length,2);const experimental=quality.replace(old,replacement);
const api=Function(units.map(n=>originals[n]).join('\n')+'\nreturn {MoonEngine,MoonPool,adaptiveRender,nativeCalendarResult,qualityMask,projectedDifference};')();
const alternate=Function(experimental+'\nreturn {adaptiveRender};')();
const manifestBytes=fs.readFileSync(path.join(root,'moon/asset-manifest.json')),manifest=JSON.parse(manifestBytes);
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,'moon',n)));
const assets={wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest};
const sceneBytes=fs.readFileSync(sceneFile),scene=JSON.parse(sceneBytes).observed.acceptedPreviewScene;
const record={schema:'r0021-bounded-quadrature-comparison/v1',scope:'Numerical experiment only; Node22 four local row owners, same global MoonPool join. No native presentation or browser performance claim.',startedAt:new Date().toISOString(),harnessSha256:hash(fs.readFileSync(__filename)),scene,sceneRecordSha256:hash(sceneBytes),sources:Object.fromEntries(units.map(n=>[n,hash(originals[n])])),experimentalQualitySha256:hash(experimental),substitution:{old,replacement,count:1},assets:{manifestSha256:hash(manifestBytes),wasm:hash(assets.wasm),dem:hash(assets.dem),colour:hash(assets.colour)},runs:[],errors:[],status:'RUNNING',stopRule:'One baseline and one alternative on the exact retained scene, 240000 ms each. Stop/reject if alternate fails unchanged empirical-adaptive gate. No other rule variants. Broader accuracy controls required only before considering a supported alternative for implementation.'};
fs.writeFileSync(path.join(out,'experimental-moon-quality.mjs'),experimental);
function write(){fs.writeFileSync(path.join(out,'RESULT.json'),JSON.stringify(record,null,2)+'\n');}
record.outerDeadlineMs=600000;
const outer=setTimeout(()=>{record.status='INCOMPLETE';record.errors.push('Outer600000ms process deadline including initialization/export');record.finishedAt=new Date().toISOString();write();process.exit(1);},record.outerDeadlineMs);outer.unref();
function save(name,array){const b=Buffer.from(array.buffer,array.byteOffset,array.byteLength),packed=zlib.gzipSync(b),file=name+'.bin.gz';fs.writeFileSync(path.join(out,file),packed);return {file,type:array.constructor.name,length:array.length,bytes:b.length,sha256:hash(b),gzipSha256:hash(packed)};}
// Exactly the adapter from moon/tests/pool.test.cjs: actual kernel per row,
// copied material, and actual global join/filter/quality code in MoonPool.
function local(e){return {async render(scene,options){const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields'}),N=scene.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}
const digest=a=>hash(Buffer.from(a.buffer,a.byteOffset,a.byteLength));
async function makePool(){const engines=[];for(let i=0;i<4;i++)engines.push(local(await api.MoonEngine.create(assets)));return new api.MoonPool(engines);}
function differences(a,b){
 const load=x=>{const raw=zlib.gunzipSync(fs.readFileSync(path.join(out,x.file)));assert.equal(hash(raw),x.sha256);return new globalThis[x.type](raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength));};
 const x=load(a),y=load(b);assert.equal(x.length,y.length);const delta=new Float64Array(x.length);let square=0,maximum=0,at=0;
 for(let i=0;i<x.length;i++){const d=Math.abs(x[i]-y[i]);delta[i]=d;square+=d*d;if(d>maximum){maximum=d;at=i;}}
 delta.sort();return {count:x.length,rms:Math.sqrt(square/x.length),p95:delta[Math.ceil(.95*delta.length)-1],maximum,maximumIndex:at,baselineAtMaximum:x[at],alternateAtMaximum:y[at]};
}
async function solve(label,adaptive){
 const begin=performance.now(),item={label,stages:[],preview:null};record.runs.push(item);write();let previous=null;
 const pool=await makePool(); // Initialization is inside this arm's elapsed bound.
 const engine={render:async(s,options)=>{assert.deepEqual(s,scene);const r=await pool.render(s,options),samples=options.radial*options.azimuth;
  const stage={radial:options.radial,azimuth:options.azimuth,samples,receiverCodesSha256:digest(r.receiverCodes),coverageSha256:digest(r.coverage),surfaceCoverageSha256:digest(r.surfaceCoverage),qualityImagesSha256:r.qualityImages.map(digest)};
  if(previous){const compared=api.qualityMask(previous,r,{first:samples===256});stage.comparison={receivers:compared.count,maximumCode:compared.maxCode,projectedMaximumCode:api.projectedDifference(previous,r)};}
  if(samples>=4096){stage.receiverCodes=save(label+'-'+samples+'-receiverCodes',r.receiverCodes);stage.qualityImages=r.qualityImages.map((a,i)=>save(label+'-'+samples+'-projection'+i,a));stage.inputMask=save(label+'-'+samples+'-mask',options.lightingMask);}
  previous=r;item.stages.push(stage);write();console.log(JSON.stringify({label,samples,comparison:stage.comparison}));return r;}};
 const result=await adaptive(engine,scene,{diagnostic:'fields',cancelled:()=>performance.now()-begin>240000,onPreview:r=>{item.preview={surface:digest(r.surfaceLinear),coverage:digest(r.surfaceCoverage),rgba:digest(r.rgba)};}});
 item.quality=result.diagnostics.quality;item.physicalIdentity=result.physicalIdentity;item.profileIdentity=result.profileIdentity;item.elapsedSeconds=(performance.now()-begin)/1000;
 item.final={surface:save(label+'-final-surface',result.surfaceLinear),coverage:save(label+'-final-coverage',result.surfaceCoverage),rgba:save(label+'-final-rgba',result.rgba)};
 const calendar=api.nativeCalendarResult(pool,result);item.calendar={linear:digest(calendar.calendarLinear),rgba:digest(calendar.calendarRgba)};write();return item;
}
(async()=>{
 assert.equal(hash(assets.wasm),manifest.wasm.sha256);
 const baseline=await solve('baseline64x128',api.adaptiveRender);
 assert.equal(baseline.quality.status,'limit-reached','Control must reproduce retained failure');assert.equal(baseline.quality.unsettled,17);assert.equal(baseline.quality.projectedMaximumCode,0.8783235549926758);assert.equal(baseline.quality.lastMaximumCode,1.4474468231201172);
 const candidate=await solve('alternate32x256',alternate.adaptiveRender);
 assert.deepEqual(candidate.preview,baseline.preview,'First64 preview unchanged');assert.deepEqual(candidate.stages.slice(0,3),baseline.stages.slice(0,3),'Pre4096 work unchanged');
 assert.equal(candidate.stages[3].receiverCodesSha256,baseline.stages[3].receiverCodesSha256,'4096 comparator unchanged');assert.deepEqual(candidate.stages[3].qualityImagesSha256,baseline.stages[3].qualityImagesSha256);
 assert.equal(candidate.stages[3].inputMask.sha256,baseline.stages[3].inputMask.sha256,'4096 selected receivers unchanged');
 assert.equal(candidate.stages[4].inputMask.sha256,baseline.stages[4].inputMask.sha256,'8192 input selection unchanged');
 const expectedIdentity=(radial,azimuth)=>hash(JSON.stringify([hash(JSON.stringify(manifest)),scene.basis,scene.sun,scene.earth,scene.distance,scene.size,scene.extent,radial,azimuth]));
 assert.equal(baseline.physicalIdentity,expectedIdentity(64,128));assert.equal(candidate.physicalIdentity,expectedIdentity(32,256));assert.notEqual(candidate.physicalIdentity,baseline.physicalIdentity,'Source quadrature belongs to physical identity');assert.equal(candidate.profileIdentity,baseline.profileIdentity);
 assert.equal(candidate.final.coverage.sha256,baseline.final.coverage.sha256,'Geometry/opaque coverage unchanged');
 record.crossRule={projections:baseline.stages[4].qualityImages.map((a,i)=>differences(a,candidate.stages[4].qualityImages[i])),surface:differences(baseline.final.surface,candidate.final.surface),rgba:differences(baseline.final.rgba,candidate.final.rgba),interpretation:'Cross-rule differences only, not an independent dense accuracy oracle. Proposed8192 retains32 radial nodes from4096; passing that comparison alone would not prove radial convergence.'};
 record.independentPoolHistories=true;
 record.controlReproduced=true;record.status=candidate.quality.status==='empirical-adaptive'?'SUPPORTED_FOR_ACCURACY_CONTROLS_ONLY':'REJECTED_ALTERNATIVE';
 record.disposition=record.status==='REJECTED_ALTERNATIVE'?'No implementation or further numerical variant. Existing product rule and failure retained.':'No implementation yet. Existing accuracy controls, independent review and named native regression remain required.';
})().catch(error=>{record.errors.push(String(error.stack||error));record.status='INCOMPLETE';process.exitCode=1;}).finally(()=>{
 clearTimeout(outer);record.sourcesUnchanged=units.every(n=>hash(read(n))===record.sources[n]);if(!record.sourcesUnchanged){record.status='INCOMPLETE';record.errors.push('Source drift');process.exitCode=1;}record.finishedAt=new Date().toISOString();write();console.log(JSON.stringify({status:record.status,sourcesUnchanged:record.sourcesUnchanged,quality:record.runs.map(r=>({label:r.label,quality:r.quality})),errors:record.errors}));
});
