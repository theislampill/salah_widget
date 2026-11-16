'use strict';
// Moon-reuse feasibility audit: summarise determinism.json and quantify cross-engine byte differences from the
// exported (scratch, uncommitted) final surfaces. Usage: node analyse.cjs <repoRoot> <det.json> <bytesDir> <out.json>
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),zlib=require('node:zlib');
const [root,detFile,bytesDir,outFile]=process.argv.slice(2);
const det=JSON.parse(fs.readFileSync(detFile,'utf8'));
const ctx={Math,Float32Array,Float64Array,Uint8Array,Error,RangeError,Number,Array};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root,'moon/src/moon-detail.mjs'),'utf8')+';this.projectSurfaceCodes=projectSurfaceCodes;',ctx);
const load=(e,s,l,k,T)=>{const f=path.join(bytesDir,`${e}-${s}-${l}-${k}.b64`);if(!fs.existsSync(f))return null;const b=Buffer.from(fs.readFileSync(f,'utf8'),'base64');return new T(b.buffer,b.byteOffset,b.byteLength/T.BYTES_PER_ELEMENT);};
const out={summary:{},crossEngine:{},entrySize:{}};
for(const [engine,rec] of Object.entries(det)){
  const groups={};for(const r of rec.runs){const k=r.scene+'|'+(r.variant==='stepwise'?'product-equivalent(stepwise)':r.variant);(groups[k]??=[]).push({label:r.label,ms:Math.round(r.ms),hashes:r.hashes,physicalIdentity:r.physicalIdentity,samplesHistory:r.quality.history.map(h=>h.samples),status:r.quality.status,projectedMaximumCode:r.quality.projectedMaximumCode});}
  const byScene={};for(const r of rec.runs){(byScene[r.scene]??=[]).push(r);}
  const distinct={};for(const [s,rs] of Object.entries(byScene)){const set=new Set(rs.map(r=>JSON.stringify(r.hashes)));distinct[s]={runs:rs.length,distinctHashTuples:set.size,labels:rs.map(r=>r.label+':'+r.hashes.rgba.slice(0,10)+'/'+r.hashes.surfaceLinear.slice(0,10))};}
  out.summary[engine]={info:rec.info,infoDpr2:rec.infoDpr2,math:rec.math,distinctByScene:distinct,isolation:rec.isolation&&{totalRequests:rec.isolation.totalRequests,externalAttempts:rec.isolation.externalAttempts,externalByLayerHostOutcome:rec.isolation.externalByLayerHostOutcome,allowedExternal:rec.isolation.allowedExternal},error:rec.error||null,
    timings:rec.runs.map(r=>({label:r.label,variant:r.variant,scene:r.scene,ms:Math.round(r.ms),bootMs:Math.round(r.bootMs||0),previewAtMs:r.previews[0]&&Math.round(r.previews[0].at),history:r.quality.history})),
    steps:rec.runs.filter(r=>r.steps).map(r=>({scene:r.scene,steps:r.steps}))};
}
const engines=Object.keys(det);
for(const s of ['G','C']){const lab=s==='G'?'b1t1-first':'b1t1-C-after-G';
  const E={};for(const e of engines){E[e]={rgba:load(e,s,lab,'rgba',Uint8Array),cal:load(e,s,lab,'calendarRgba',Uint8Array),lin:load(e,s,lab,'surfaceLinear',Float32Array),cov:load(e,s,lab,'surfaceCoverage',Float32Array)};}
  for(let i=0;i<engines.length;i++)for(let j=i+1;j<engines.length;j++){const a=E[engines[i]],b=E[engines[j]];if(!a.rgba||!b.rgba)continue;
    const px=(x,y)=>{let p=0,p1=0,p3=0,m=0;for(let q=0;q<x.length;q+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(x[q+k]-y[q+k]));if(d){p++;if(d>1)p1++;if(d>3)p3++;m=Math.max(m,d);}}return {pixelsDiffering:p,over1:p1,over3:p3,maxDelta:m,pixels:x.length/4};};
    let linMax=0,linN=0;for(let q=0;q<a.lin.length;q++){const d=Math.abs(a.lin[q]-b.lin[q]);if(d){linN++;linMax=Math.max(linMax,d);}}
    const proj={};for(const D of [108,216]){const pa=ctx.projectSurfaceCodes({size:540,linear:a.lin,coverage:a.cov,extent:1.08},D),pb=ctx.projectSurfaceCodes({size:540,linear:b.lin,coverage:b.cov,extent:1.08},D);let m=0,r=0;for(let q=0;q<pa.length;q+=3){let rr=false;for(let k=0;k<3;k++){m=Math.max(m,Math.abs(pa[q+k]-pb[q+k]));if(Math.round(pa[q+k])!==Math.round(pb[q+k]))rr=true;}if(rr)r++;}proj[D]={maxCode:m,rounded8bitPixelsDiffering:r,pixels:pa.length/3};}
    out.crossEngine[s+' '+engines[i]+' vs '+engines[j]]={rgba300:px(a.rgba,b.rgba),calendarRgba300:px(a.cal,b.cal),surfaceLinearFloatsDiffering:linN,surfaceLinearMaxAbs:linMax,projected:proj};
  }
}
// Entry size: what a stored refined result must hold for adopt() (moon-native.mjs L108-116): rgba, calendarRgba,
// surfaceLinear, calendarLinear (= surfaceLinear*gain, moon-calendar.mjs L15-16), surfaceCoverage.
{const e=engines[0],g=k=>{const f=path.join(bytesDir,`${e}-G-b1t1-first-${k}.b64`);return fs.existsSync(f)?Buffer.from(fs.readFileSync(f,'utf8'),'base64'):null;};
 const parts={rgba:g('rgba'),calendarRgba:g('calendarRgba'),surfaceLinear:g('surfaceLinear'),surfaceCoverage:g('surfaceCoverage')};
 if(parts.rgba){const raw={},gz={};for(const [k,v] of Object.entries(parts)){raw[k]=v.length;gz[k]=zlib.gzipSync(v,{level:9}).length;}
  raw.calendarLinear=raw.surfaceLinear;gz.calendarLinear='derivable from surfaceLinear x one scalar gain (not measured separately)';
  out.entrySize={engine:e,scene:'G',rawBytes:raw,rawTotal:Object.values(raw).reduce((a,b)=>a+b,0),gzip9Bytes:gz,gzip9TotalWithoutCalendarLinear:Object.values(gz).filter(x=>typeof x==='number').reduce((a,b)=>a+b,0),note:'DPR-independent: the scene raster is fixed at size 540 / outSize 300 (moon-precision.mjs L67)'};}}
fs.writeFileSync(outFile,JSON.stringify(out,null,1));
console.log(JSON.stringify({summary:Object.fromEntries(Object.entries(out.summary).map(([k,v])=>[k,{distinct:v.distinctByScene,math:v.math,allowed:v.isolation&&v.isolation.allowedExternal,err:v.error}])),crossEngine:out.crossEngine,entrySize:out.entrySize},null,1));
