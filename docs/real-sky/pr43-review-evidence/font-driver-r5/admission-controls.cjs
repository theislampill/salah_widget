'use strict';
const originalAssert=require('node:assert/strict');let assertions=0;const assert=new Proxy(originalAssert,{get:(t,k)=>typeof t[k]==='function'?(...args)=>{assertions++;return t[k](...args);}:t[k]});
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const adapter=require('./rlgwo-clock-date-fixture.cjs'),base=require('../font-driver-r4/rlgwo-clock-date-fixture.cjs');
const binding=JSON.parse(fs.readFileSync(path.join(__dirname,'SOURCE_BINDING.json'),'utf8')),b=binding.sources['04'];
const source=fs.readFileSync(path.join(b.root,'index.html'),'utf8'),inventory=JSON.parse(fs.readFileSync(path.join(__dirname,'runtime-identity.json'),'utf8'));
const admitted=adapter.strictNativeRuntime(source);assert.equal(admitted.layoutId,'combined_r1r2_04');assert.equal(admitted.scripts.length,6);assert.equal(admitted.sourceSha256,b.indexSha256);
assert.equal(sha(admitted.native),b.nativeCoreSha256);assert.equal(sha(admitted.native),'a36585ace0ba7b223cafae72de14277f9b8c8874df53147eb03c08352243c8f2');
for(const script of Array.from(source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)))new vm.Script(script[2]);
const text=fs.readFileSync(path.join(__dirname,'rlgwo-clock-date-fixture.cjs'),'utf8'),baseText=fs.readFileSync(path.join(__dirname,'../font-driver-r4/rlgwo-clock-date-fixture.cjs'),'utf8');
const observationBlock=x=>x.slice(x.indexOf('function record('),x.indexOf('function prepare('));
assert.equal(observationBlock(text),observationBlock(baseText));
for(const name of ['rlgwo_native_checks.py','rlgwo_date_disclosure_check.py','rlgwo_wall_clock_check.py','rlgwo_timezone_check.py'])assert.equal(sha(fs.readFileSync(path.join(__dirname,name))),sha(fs.readFileSync(path.join(__dirname,'../font-driver-r4',name))));
const variants=['missing','delayed-css-forenoon','delayed-bytes-forenoon','split-face-forenoon','loaded-forenoon','permanent-bytes-forenoon','warm-cache-forenoon','loaded-sunrise','loaded-maghrib'];
for(const variant of variants){
 const built=adapter.prepare({root:b.root,suite:'access',name:'font',variant,runtimeIdentity:inventory});
 new vm.Script(built.preScript);new vm.Script(built.nativeScript);
 assert.equal(built.identity.sourceSha256,b.indexSha256);assert.equal(built.identity.effectiveSourceSha256,b.indexSha256);assert.equal(built.identity.sourceMutation,null);
 assert.equal(built.identity.runtimeTreeSha256,b.runtimeTreeSha256);assert.equal(built.identity.scriptLayout.id,'combined_r1r2_04');
 assert.equal(built.hooks,base.prepare({root:binding.sources['02'].root,suite:'access',name:'font',variant,runtimeIdentity:JSON.parse(fs.readFileSync(path.join(__dirname,'../prepared/combined-02-font-r3/font-runtime-identity.json'),'utf8'))}).hooks);
}
assert.throws(()=>adapter.strictNativeRuntime(source+'<script>void 0</script>'),/exactly 6/);
assert.throws(()=>adapter.strictNativeRuntime(source.replace('src="real-sky/native-sky.js"','src="unknown.js"')),/role\/order/);
const all=Array.from(source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g));
assert.throws(()=>adapter.strictNativeRuntime(source.replace(all[2][2],all[2][2]+'\n// changed decoder\n')),/digest/);
assert.throws(()=>adapter.strictNativeRuntime(source.replace(admitted.native,admitted.native+'\n// changed native\n')),/digest/);
assert.throws(()=>adapter.strictNativeRuntime(source.replace('<body>','<body data-unknown="1">')),/Whole source/);
const altered=structuredClone(inventory);altered.files['config.js'].sha256='0'.repeat(64);
assert.throws(()=>adapter.prepare({root:b.root,suite:'access',name:'font',variant:'loaded-forenoon',runtimeIdentity:altered}),/exact runtime tree/);
const wrongTree=structuredClone(inventory);wrongTree.treeSha256='0'.repeat(64);
assert.throws(()=>adapter.prepare({root:b.root,suite:'access',name:'font',variant:'loaded-forenoon',runtimeIdentity:wrongTree}),/exact runtime tree/);
const wrongIndex=structuredClone(inventory);wrongIndex.files['index.html'].sha256='0'.repeat(64);
assert.throws(()=>adapter.prepare({root:b.root,suite:'access',name:'font',variant:'loaded-forenoon',runtimeIdentity:wrongIndex}),/exact full runtime/);
// Old approved sources retain their strict admission and original profiles.
for(const id of ['02','03'])assert.equal(adapter.strictNativeRuntime(fs.readFileSync(path.join(binding.sources[id].root,'index.html'),'utf8')).layoutId,'combined_r1r2_02');
console.log(JSON.stringify({status:'PASS',assertions,variants:variants.length,nativeExecution:false,naturalObservationsUnchanged:true,sourceSha256:b.indexSha256,runtimeTreeSha256:b.runtimeTreeSha256}));
