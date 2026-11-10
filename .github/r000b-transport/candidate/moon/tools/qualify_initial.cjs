#!/usr/bin/env node
'use strict';
// Focused initial-to-approved-final comparison. References are retained full
// adaptive renders, not an initial tier relabelled as its own oracle.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),moon=path.join(root,'moon'),references=process.argv[2],out=process.argv[3];
if(!references||!out)throw Error('Usage: node moon/tools/qualify_initial.cjs REFERENCE_DIRECTORY OUTPUT_DIRECTORY');
fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-initial.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(moon,'src',n),'utf8')).join('\n')+'\nreturn {createInitialMoon,prefixSurface,boxSurface,encodeSrgb};')();
const bytes=fs.readFileSync(path.join(moon,'assets/initial-receivers.bin')),pin=JSON.parse(fs.readFileSync(path.join(moon,'initial-manifest.json'))),seed=api.createInitialMoon(new Uint8Array(bytes),pin);
function project(s,diameter,shift){
 const p=api.prefixSurface({size:s.size,linear:s.linear,coverage:s.coverage}),N=Math.ceil(diameter*1.1),scale=s.size/(diameter*s.extent),ox=s.size/2-N*scale/2-shift[0]*scale,oy=s.size/2-N*scale/2-shift[1]*scale,rgba=new Uint8ClampedArray(N*N*4);
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){
  const c=api.boxSurface(p,ox+x*scale,oy+y*scale,ox+(x+1)*scale,oy+(y+1)*scale),a=c[3],i=4*(y*N+x);
  for(let k=0;k<3;k++)rgba[i+k]=Math.floor(255*api.encodeSrgb(a?c[k]/a:0)+.5);rgba[i+3]=Math.floor(255*a+.5);
 }return {size:N,rgba};
}
const rows=[],identities={};
for(const sense of ['wax','wane'])for(const fraction of [.01,.08,.5,.92,1]){
 const name=`reference-${sense}-${fraction}`,metaBytes=fs.readFileSync(path.join(references,name+'.json')),meta=JSON.parse(metaBytes);
 if(meta.scene.fraction!==fraction||meta.scene.waxing!==(sense==='wax')||meta.scene.size!==540||meta.diagnostics.quality.status!=='empirical-adaptive')throw Error('Reference identity/quality');
 const read=field=>{const b=fs.readFileSync(path.join(references,name+'-'+field+'.bin'));identities[name+'-'+field]=sha(b);return new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));};
 identities[name]=sha(metaBytes);const reference={linear:read('surfaceLinear'),coverage:read('surfaceCoverage'),size:540,extent:1.08};
 const value=seed.render(meta.scene),initial={linear:value.surfaceLinear,coverage:value.surfaceCoverage,size:value.surfaceSize,extent:value.surfaceExtent};
 for(const dpr of [1,2])for(const shift of [[0,0],[.37,-.21]]){
  // Native maximum photo width=96*1.13 CSS px; physical diameter=.96*photo.
  const diameter=96*1.13*.96*dpr,a=project(initial,diameter,shift),b=project(reference,diameter,shift),delta=[];let coverageMismatch=0;
  for(let i=0;i<a.rgba.length;i+=4){if(a.rgba[i+3]!==b.rgba[i+3])coverageMismatch++;if(a.rgba[i+3]===255&&b.rgba[i+3]===255)for(let k=0;k<3;k++)delta.push(Math.abs(a.rgba[i+k]-b.rgba[i+k]));}
  delta.sort((a,b)=>a-b);const rms=Math.sqrt(delta.reduce((a,b)=>a+b*b,0)/delta.length),p95=delta[Math.floor(.95*delta.length)],key=`${sense}-${fraction}-dpr${dpr}-${shift[0]}`;
  fs.writeFileSync(path.join(out,key+'-initial.rgba'),a.rgba);fs.writeFileSync(path.join(out,key+'-final.rgba'),b.rgba);
  rows.push({key,fraction,sense,dpr,shift,diameter,size:a.size,rms,p95,max:delta.at(-1),coverageMismatch,seedMs:value.diagnostics.totalMs,pass:rms<=4&&p95<=12&&coverageMismatch===0});
 }
}
const report={schema:'moon-initial-comparison/1',initialSha256:sha(bytes),initialManifestSha256:sha(fs.readFileSync(path.join(moon,'initial-manifest.json'))),consumerSha256:sha(fs.readFileSync(path.join(moon,'src/moon-initial.mjs'))),referenceFiles:identities,budgets:{interiorRmsCode:4,p95Code:12,silhouetteDisplacementDevicePixels:.5},rows,status:rows.every(r=>r.pass)?'NUMERICAL_PASS_VISUAL_REVIEW_REQUIRED':'FAIL'};
fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,rows:rows.length,maxRms:Math.max(...rows.map(r=>r.rms)),maxP95:Math.max(...rows.map(r=>r.p95)),failures:rows.filter(r=>!r.pass)}));
if(report.status==='FAIL')process.exitCode=1;
