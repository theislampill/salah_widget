'use strict';
// One production-size adaptive pair. Numerical equivalence, not a timing race.
// Both paths use the current calendar presentation operator. This isolates row
// scheduling; it does not claim that the adapted calendar token equals c1 bytes.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=process.argv[2],out=process.argv[3];assert(root&&out);fs.mkdirSync(out,{recursive:true});
const read=n=>fs.readFileSync(path.join(root,'moon/src',n),'utf8'),hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const approved='c1a480c97e9af188cf57704502d818c0584cf265';
const old=cp.execFileSync('git',['show',approved+':moon/src/moon-engine.mjs'],{cwd:root,encoding:'utf8'});
const api=reference=>Function(units.map(n=>reference&&n==='moon-engine.mjs'?old:read(n)).join('\n')+'\nreturn {MoonEngine,MoonPool,adaptiveRender,canonicalScene,nativeCalendarResult};')();
const a=api(true),b=api(false),manifest=JSON.parse(fs.readFileSync(path.join(root,'moon/asset-manifest.json')));
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,'moon',n)));
const assets={wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest};
function local(e){return {async render(scene,options){const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields'}),N=scene.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}
function sha(array){return hash(Buffer.from(array.buffer,array.byteOffset,array.byteLength));}
function fieldDigest(r){const result={};for(const n of ['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','rgba'])result[n]={type:r[n].constructor.name,length:r[n].length,sha256:sha(r[n])};result.qualityImages=r.qualityImages.map(sha);return result;}
async function solve(label,api,engine,scene){let preview;const start=performance.now();const result=await api.adaptiveRender(engine,scene,{diagnostic:'fields',onPreview:r=>{preview={surface:sha(r.surfaceLinear),rgba:sha(r.rgba)};console.log(label,'preview',((performance.now()-start)/1000).toFixed(3));},onProgress:p=>{if(p.stage==='refinement')console.log(label,JSON.stringify(p));}});const calendar=api.nativeCalendarResult(engine,result);return {result,record:{elapsedSeconds:(performance.now()-start)/1000,preview,fields:fieldDigest(result),calendarLinear:sha(calendar.calendarLinear),calendarRgba:sha(calendar.calendarRgba),physicalIdentity:result.physicalIdentity,profileIdentity:result.profileIdentity,quality:result.diagnostics.quality,diagnostics:result.diagnostics}};}
(async()=>{
 const scene=a.canonicalScene({fraction:.4509,waxing:true,size:540,outSize:300,diameter:288});
 const reference=await solve('approved single worker',a,await a.MoonEngine.create(assets),scene);
 const pool=new b.MoonPool([local(await b.MoonEngine.create(assets)),local(await b.MoonEngine.create(assets))]);
 const joined=await solve('row assembly',b,pool,scene);
 const proof={schema:'moon-row-production-parity/1',status:'CHECKING',referenceCommit:approved,scope:'One identical N540 production geometry, unchanged V5 kernel/assets and quality rule; sequential approved single engine versus row scheduling. Wall times are not browser speed qualification.',scene,sources:Object.fromEntries(units.map(n=>[n,hash(read(n))])),approvedEngineSha256:hash(old),kernelSha256:sha(assets.wasm),manifest,reference:reference.record,joined:joined.record};
 const file=path.join(out,'results.json');fs.writeFileSync(file,JSON.stringify(proof,null,2));
 assert.deepEqual(joined.record.fields,reference.record.fields,'all raw fields/global filters/display codes must be bitwise identical');
 assert.deepEqual(joined.record.preview,reference.record.preview,'preview identical');
 assert.equal(joined.record.calendarLinear,reference.record.calendarLinear);assert.equal(joined.record.calendarRgba,reference.record.calendarRgba);
 assert.equal(joined.record.physicalIdentity,reference.record.physicalIdentity);assert.equal(joined.record.profileIdentity,reference.record.profileIdentity);
 const quality=q=>({...q,history:q.history.map(({milliseconds,...r})=>r),totalMs:null});
 assert.deepEqual(quality(joined.record.quality),quality(reference.record.quality),'same global adaptive decisions');
 proof.status='PASS_BITWISE';fs.writeFileSync(file,JSON.stringify(proof,null,2));console.log(proof.status,reference.record.elapsedSeconds,joined.record.elapsedSeconds);
})().catch(e=>{console.error(e);process.exitCode=1;});
