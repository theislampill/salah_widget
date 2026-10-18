'use strict';
// One owner-approved diagnostic reference. Product quality owner is unmodified.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib'),assert=require('node:assert/strict');
const [root,out,sceneFile,priorDir,build]=process.argv.slice(2);assert(root&&out&&sceneFile&&priorDir&&build);assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),read=n=>fs.readFileSync(path.join(root,'moon/src',n),'utf8');
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const originals=Object.fromEntries(units.map(n=>[n,read(n)]));
const priorBytes=fs.readFileSync(path.join(priorDir,'RESULT.json'));assert.equal(hash(priorBytes),'c72db7c1c7c46d915bacae42059b4323aef71e944e1963481ac5a08a534e0065');
const prior=JSON.parse(priorBytes),baseline=prior.runs[0],alternate=prior.runs[1];
for(const n of units)assert.equal(hash(originals[n]),prior.sources[n],n+' source drift');
const diagnosticEngine=fs.readFileSync(path.join(build,'moon-engine-reference.mjs'),'utf8');
assert.equal(diagnosticEngine,originals['moon-engine.mjs'].replace('radial*azimuth>8192','radial*azimuth>16384'));
const api=Function(units.map(n=>n==='moon-engine.mjs'?diagnosticEngine:originals[n]).join('\n')+'\nreturn {MoonEngine,MoonPool,adaptiveRender,nativeCalendarResult,qualityMask,projectedDifference};')();
const manifestBytes=fs.readFileSync(path.join(root,'moon/asset-manifest.json')),originalManifest=JSON.parse(manifestBytes),manifest=structuredClone(originalManifest);
const wasm=fs.readFileSync(path.join(build,'moon_kernel_reference.wasm'));manifest.wasm={...manifest.wasm,bytes:wasm.length,sha256:hash(wasm)};
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,'moon',n)));
const assets={wasm:new Uint8Array(wasm),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest};
assert.equal(hash(manifestBytes),prior.assets.manifestSha256);assert.equal(hash(assets.dem),prior.assets.dem);assert.equal(hash(assets.colour),prior.assets.colour);
const sceneBytes=fs.readFileSync(sceneFile),scene=JSON.parse(sceneBytes).observed.acceptedPreviewScene;assert.deepEqual(scene,prior.scene);
const record={schema:'r0021-single-reference/v1',status:'RUNNING',startedAt:new Date().toISOString(),harnessSha256:hash(fs.readFileSync(__filename)),sourceHead:'9df79b98d8dda7a0286b1b287dc03d1b4d760bdb',priorResultSha256:hash(priorBytes),sceneRecordSha256:hash(sceneBytes),scene,sources:Object.fromEntries(units.map(n=>[n,hash(originals[n])])),diagnosticEngineSha256:hash(diagnosticEngine),assets:{originalManifestSha256:hash(manifestBytes),diagnosticManifestSha256:hash(JSON.stringify(manifest)),wasmSha256:hash(wasm),demSha256:hash(assets.dem),colourSha256:hash(assets.colour)},stages:[],errors:[],scope:'One direct64x256 on the r112 final82receiver mask after identical4096 predecessor/cache. No browser, performance, absolute accuracy, product admission or sample-ceiling amendment.',stopRule:'Any prefix/mask/source mismatch stops before reference; one reference only;240s cooperative including initialization;600s outer process deadline.'};
fs.writeFileSync(path.join(out,'diagnostic-asset-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
function write(){fs.writeFileSync(path.join(out,'RESULT.json'),JSON.stringify(record,null,2)+'\n');}
const outer=setTimeout(()=>{record.status='INCOMPLETE';record.errors.push('Outer600000ms deadline');record.finishedAt=new Date().toISOString();write();process.exit(1);},600000);outer.unref();
const digest=a=>hash(Buffer.from(a.buffer,a.byteOffset,a.byteLength));
function save(name,a){const raw=Buffer.from(a.buffer,a.byteOffset,a.byteLength),packed=zlib.gzipSync(raw),file=name+'.bin.gz';fs.writeFileSync(path.join(out,file),packed);return {file,type:a.constructor.name,length:a.length,bytes:raw.length,sha256:hash(raw),gzipSha256:hash(packed)};}
function load(spec){const packed=fs.readFileSync(path.join(priorDir,spec.file));assert.equal(hash(packed),spec.gzipSha256);const b=zlib.gunzipSync(packed);assert.equal(hash(b),spec.sha256);assert.equal(b.length,spec.bytes);const a=new globalThis[spec.type](b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));assert.equal(a.length,spec.length);return a;}
function differences(a,b){assert.equal(a.length,b.length);const d=new Float64Array(a.length);let square=0,max=0,at=0;for(let i=0;i<a.length;i++){const v=Math.abs(a[i]-b[i]);assert(Number.isFinite(v));d[i]=v;square+=v*v;if(v>max){max=v;at=i;}}d.sort();return {count:a.length,rms:Math.sqrt(square/a.length),p95:d[Math.ceil(.95*d.length)-1],maximum:max,maximumIndex:at,storedAtMaximum:a[at],referenceAtMaximum:b[at]};}
function local(e){return {async render(s,options){const r=await e.render(s,{...options,qualityFields:true,diagnostic:'fields'}),N=s.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}
(async()=>{
 const begin=performance.now(),cancelled=()=>performance.now()-begin>240000,engines=[];
 for(let i=0;i<4;i++){assert(!cancelled(),'Initialization deadline');engines.push(local(await api.MoonEngine.create(assets)));}
 const pool=new api.MoonPool(engines),STOP=Symbol('before8192');let pending=null,previous=null;
 const intercept={render:async(s,options)=>{assert.deepEqual(s,scene);const samples=options.radial*options.azimuth;
  if(samples===8192){pending=options;throw STOP;}
  assert([64,256,1024,4096].includes(samples));const r=await pool.render(s,options),expected=baseline.stages[record.stages.length];
  const stage={radial:options.radial,azimuth:options.azimuth,samples,receiverCodesSha256:digest(r.receiverCodes),coverageSha256:digest(r.coverage),surfaceCoverageSha256:digest(r.surfaceCoverage),qualityImagesSha256:r.qualityImages.map(digest)};
  for(const key of ['radial','azimuth','samples','receiverCodesSha256','coverageSha256','surfaceCoverageSha256','qualityImagesSha256'])assert.deepEqual(stage[key],expected[key],'Prefix '+samples+' '+key);
  if(samples===4096){assert.equal(digest(options.lightingMask),expected.inputMask.sha256);stage.inputMask=save('prefix4096-mask',options.lightingMask);stage.receiverCodes=save('prefix4096-receiverCodes',r.receiverCodes);stage.qualityImages=r.qualityImages.map((a,i)=>save('prefix4096-projection'+i,a));}
  previous=r;record.stages.push(stage);write();console.log(JSON.stringify({stage:samples,prefixExact:true}));return r;}};
 try{await api.adaptiveRender(intercept,scene,{diagnostic:'fields',cancelled});throw new Error('Original adaptive loop did not request final8192');}catch(e){if(e!==STOP)throw e;}
 assert(pending&&previous&&record.stages.length===4);assert.equal(pending.radial,64);assert.equal(pending.azimuth,128);
 const mask=pending.lightingMask;assert.equal(digest(mask),baseline.stages[4].inputMask.sha256);assert.equal(digest(mask),alternate.stages[4].inputMask.sha256);assert.equal(mask.reduce((n,x)=>n+(x!==0),0),82);
 record.referenceMask=save('reference16384-mask',mask);record.prefixExact=true;write();
 const r=await pool.render(scene,{...pending,radial:64,azimuth:256,cancelled});assert.equal(r.diagnostics.sourceSamples,16384);
 record.reference={radial:64,azimuth:256,samples:16384,receiverCodes:save('reference16384-receiverCodes',r.receiverCodes),qualityImages:r.qualityImages.map((a,i)=>save('reference16384-projection'+i,a)),surface:save('reference16384-surface',r.surfaceLinear),coverage:save('reference16384-coverage',r.surfaceCoverage),rgba:save('reference16384-rgba',r.rgba),physicalIdentity:r.physicalIdentity,profileIdentity:r.profileIdentity};
 const expectedIdentity=hash(JSON.stringify([hash(JSON.stringify(manifest)),scene.basis,scene.sun,scene.earth,scene.distance,scene.size,scene.extent,64,256]));assert.equal(r.physicalIdentity,expectedIdentity);assert.equal(r.profileIdentity,baseline.profileIdentity);assert.equal(digest(r.surfaceCoverage),baseline.final.coverage.sha256);
 let changedUnselected=0;for(let i=0;i<mask.length;i++)if(!mask[i])for(let k=0;k<3;k++)if(r.receiverCodes[3*i+k]!==previous.receiverCodes[3*i+k])changedUnselected++;
 assert.equal(changedUnselected,0);record.changedUnselectedComponents=changedUnselected;
 const compared=api.qualityMask(previous,r);record.against4096={receivers:compared.count,maximumCode:compared.maxCode,projectedMaximumCode:api.projectedDifference(previous,r),scope:'Diagnostic difference, not a product quality/admission result'};
 record.fixedAxisComparisons=[baseline,alternate].map(old=>({storedRule:old.label,axis:old.label===baseline.label?'angular count128->256 at radial64':'radial count32->64 at angular256',receiverCodes:differences(load(old.stages[4].receiverCodes),r.receiverCodes),projections:old.stages[4].qualityImages.map((spec,i)=>differences(load(spec),r.qualityImages[i])),surface:differences(load(old.final.surface),r.surfaceLinear),rgba:differences(load(old.final.rgba),r.rgba)}));
 record.elapsedSeconds=(performance.now()-begin)/1000;record.status='COMPLETE_DIAGNOSTIC_ONLY';record.disposition='Independent result review required. No product correction, final refinement, S1, H1/V5 visual, callback-cost or merge credit.';
})().catch(e=>{record.status='INCOMPLETE';record.errors.push(String(e.stack||e));process.exitCode=1;}).finally(()=>{clearTimeout(outer);record.sourcesUnchanged=units.every(n=>hash(read(n))===record.sources[n]);if(!record.sourcesUnchanged){record.status='INCOMPLETE';record.errors.push('Source drift');process.exitCode=1;}record.finishedAt=new Date().toISOString();write();console.log(JSON.stringify({status:record.status,prefixExact:record.prefixExact,against4096:record.against4096,comparisons:record.fixedAxisComparisons,errors:record.errors}));});
