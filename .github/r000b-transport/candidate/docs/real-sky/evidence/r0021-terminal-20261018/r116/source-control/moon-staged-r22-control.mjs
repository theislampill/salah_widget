// Read-only actual startMoonDetail control. Only DOM/canvas transport is simulated.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const R='${REPO_ROOT}';
const O='${WORK_ROOT}';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const {nativeCloudChannel,validateNativeRGBA}=await import(pathToFileURL(R+'/real-sky/native-cloud-transfer.mjs'));
const {encodeNativeDisplay}=await import(pathToFileURL(R+'/real-sky/native-host.mjs'));
const fixture=fs.readFileSync(R+'/tests/real-sky/moon-projection-cache.test.mjs','utf8');
const begin=fixture.indexOf('function surface('),end=fixture.indexOf("assert.equal(sha(original)");
assert(begin>=0&&end>begin);
const {surface,frame,instance}=new Function('vm','assert','sha','performance','Buffer','nativeCloudChannel','validateNativeRGBA','encodeNativeDisplay',fixture.slice(begin,end)+'\nreturn {surface,frame,instance};')(vm,assert,sha,performance,Buffer,nativeCloudChannel,validateNativeRGBA,encodeNativeDisplay);
const files={old:R+'/tests/fixtures/moon-detail-pre-cache.mjs',r11:O+'/builds/integrated-r11/moon/src/moon-detail.mjs',new:R+'/moon/src/moon-detail.mjs'};
const src=Object.fromEntries(Object.entries(files).map(([k,p])=>[k,fs.readFileSync(p,'utf8')]));
assert.equal(sha(src.old),'3cfa1498918706adf21a5f8462f27f9919bed9402f179b03ae3e932500c5cba0');
assert.equal(sha(src.r11),'f2596f26f19f946873792a7e121ea472b361021c8cc2b1831faa6cd10fdef07c');
assert.equal(sha(src.new),'c5f336a5f42e3774866d66215e2944b2cde7afad05db801868980121fa70a8b8');
const cases=[];
for(const [name,text] of Object.entries(src)){
 const h=instance(text);h.adopt(surface());h.classes.delete('real-sky-composed');h.classes.delete('real-sky-preview-ready');
 const f={...frame(),preview:true};const staged=h.compose(f);
 assert.equal(staged.publishes,name==='new'?1:0);
 cases.push({case:name+' current staged preview before ready class',...staged});
 if(name==='new'){
  const bytes=staged.hash;h.classes.add('real-sky-preview-ready');const settled=h.compose({...frame(),preview:true});assert.equal(settled.hash,bytes);assert.equal(settled.publishes,1);
  cases.push({case:'staged/settled exact output bytes',equal:true,sha256:bytes});
 }
}
for(const phase of ['entry','pre-upload']){
 const h=instance(src.new);h.adopt(surface());h.classes.delete('real-sky-composed');h.classes.delete('real-sky-preview-ready');
 let reads=0;const f={...frame(),preview:true,current:()=>{reads++;return phase==='pre-upload'&&reads===1;}};
 const result=h.compose(f);assert.equal(result.publishes,0);assert.equal(result.visible,false);
 assert.equal(reads,phase==='entry'?1:2);cases.push({case:'currentness rejected '+phase,reads,...result});
}
const prefix=t=>t.slice(0,t.indexOf('function startMoonDetail(){'));
const suffix=t=>t.slice(t.indexOf('function projectSurfaceCodes('));
for(const text of [src.r11,src.new]){assert.equal(prefix(text),prefix(src.old));assert.equal(suffix(text),suffix(src.old));}
const result={schema:'r0021-staged-moon-source-control/v1',scope:'Actual startMoonDetail and existing DOM/canvas fixture; no browser, terrain generation, rendered native pixel or timing claim.',allPassed:true,files:Object.fromEntries(Object.entries(files).map(([k,path])=>[k,{path,sha256:sha(fs.readFileSync(path))}])),fixture:{path:R+'/tests/real-sky/moon-projection-cache.test.mjs',sha256:sha(fixture)},unchangedPrefixSha256:sha(prefix(src.new)),unchangedSuffixSha256:sha(suffix(src.new)),cases};
const target=O+'/independent-review/worker-lunar-r20/MOON-STAGED-CONTROL.json';
fs.writeFileSync(target,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({allPassed:true,path:target,sha256:sha(fs.readFileSync(target)),prefix:result.unchangedPrefixSha256,suffix:result.unchangedSuffixSha256,cases:cases.length}));
