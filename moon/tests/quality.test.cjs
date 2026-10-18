'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const root=path.join(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,MoonPool,adaptiveRender};')();
const evidence=path.join(root,'..','docs/real-sky/evidence/r0021-terminal-20261018/r114');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),fixtureBytes=fs.readFileSync(path.join(evidence,'RESULT.json'));
assert.equal(sha(fixtureBytes),'77f2110c1d267ce35d94560f21b48cc20e1859a9c242b0c4a0ba3847140b23d9');
const fixture=JSON.parse(fixtureBytes);
function reference(spec){const packed=fs.readFileSync(path.join(evidence,spec.file));assert.equal(sha(packed),spec.gzipSha256);const b=zlib.gunzipSync(packed);assert.equal(sha(b),spec.sha256);return new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));}
function local(e){return {async render(scene,options){const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields'}),N=scene.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}

// The original64x128 rule rejects this actual retained scene at0.87832355.
// The separate fixed-axis reference checks the radial uncertainty that an
// azimuth-only final increment cannot establish by itself. It is empirical,
// sparse82-receiver evidence, not an absolute all-scene accuracy certificate.
test('retained DPR2 lunar scene reaches admitted refinement within its existing sample and projected-error budgets',{timeout:240000},async()=>{
 const started=performance.now(),manifest=JSON.parse(fs.readFileSync(path.join(root,'asset-manifest.json'))),bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,n)));
 const assets={wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest},engines=[];
 for(let i=0;i<4;i++)engines.push(local(await api.MoonEngine.create(assets)));
 const pool=new api.MoonPool(engines),result=await api.adaptiveRender(pool,fixture.scene,{diagnostic:'fields',cancelled:()=>performance.now()-started>180000});
 assert.equal(result.diagnostics.quality.status,'empirical-adaptive');
 assert.ok(result.diagnostics.quality.history.every(x=>x.samples<=8192),'product sample ceiling');
 assert.ok(result.diagnostics.quality.projectedMaximumCode<=.5,'unchanged projected gate');
 assert.equal(sha(Buffer.from(result.surfaceCoverage.buffer)),fixture.reference.coverage.sha256,'opaque geometry unchanged');
 for(let j=0;j<2;j++){
  const target=reference(fixture.reference.qualityImages[j]),actual=result.qualityImages[j];assert.equal(actual.length,target.length);
  let maximum=0;for(let i=0;i<actual.length;i++)maximum=Math.max(maximum,Math.abs(actual[i]-target[i]));
  assert.ok(maximum<=.5,`fixed-axis reference offset${j}: ${maximum}`);
 }
});

test('projected quality still admits the boundary and rejects a persistent excess at the sample ceiling',async()=>{
 for(const [increment,want] of [[.5,'empirical-adaptive'],[.5009765625,'limit-reached']]){
  let step=0;
  // Synthetic fields isolate the real quality decision from terrain cost.
  const engine={async render(scene,{radial,azimuth}){assert.ok(radial*azimuth<=8192);const value=step++;return {receiverCodes:new Float32Array([value,value,value]),ambiguous:new Uint8Array([3]),qualityImages:[new Float32Array([value*increment])],diagnostics:{totalMs:0}};}};
  const result=await api.adaptiveRender(engine,{},{});
  assert.equal(result.diagnostics.quality.status,want);
  assert.equal(result.diagnostics.quality.projectedGate,.5);
  assert.equal(result.diagnostics.quality.thresholdCode,.125);
  if(want==='limit-reached')assert.equal(result.diagnostics.quality.history.at(-1).samples,8192);
 }
});

test('diagnostic16384 sampling remains rejected by the production engine',async()=>{
 await assert.rejects(api.MoonEngine.prototype.render.call({active:false},fixture.scene,{radial:64,azimuth:256}),/Source quadrature/);
});
