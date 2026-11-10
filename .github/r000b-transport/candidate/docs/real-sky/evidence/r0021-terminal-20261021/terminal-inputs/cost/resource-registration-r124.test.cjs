'use strict';
// Offline observer-only regression. This mock is not native decode evidence.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
async function check(name,expectFailure){
 const file=path.join(__dirname,name),source=fs.readFileSync(file,'utf8');
 let nativeCalls=0;
 const originalPromise=Promise.resolve();
 class TestImage {constructor(){this.src='test-observer-only';}decode(){nativeCalls++;return originalPromise;}}
 const window={__r21:{enter:()=>1,leave:()=>{},readOwner:()=>null}};
 const context=vm.createContext({window,HTMLImageElement:TestImage,performance,WeakRef,WeakSet,WeakMap,Map,Set});
 vm.runInContext(source,context,{filename:name});
 const first=new TestImage(),second=new TestImage();
 let failure=null;try{assert.equal(first.decode(),originalPromise);}catch(e){failure=String(e);}
 if(expectFailure){assert.match(failure,/undefined.*started|started.*undefined/);assert.equal(nativeCalls,0);assert.equal(window.__r21Resources.export().images.length,0);}
 else{
  assert.equal(failure,null);assert.equal(first.decode(),originalPromise);assert.equal(second.decode(),originalPromise);
  await originalPromise;await Promise.resolve();
  const rows=window.__r21Resources.export().images;assert.equal(rows.length,2);assert.equal(rows[0].started,2);assert.equal(rows[0].settled,2);assert.equal(rows[1].started,1);assert.equal(rows[1].settled,1);assert.notEqual(rows[0].id,rows[1].id);assert.equal(nativeCalls,3);
 }
 return {file:name,sha256:crypto.createHash('sha256').update(source).digest('hex'),expectedFailure:expectFailure,failure,nativeCalls,images:window.__r21Resources.export().images};
}
(async()=>{const before=await check('resource-controls-r123.js',true),after=await check('resource-controls-r124.js',false);const out={schema:'r0021-observer-first-image-regression/v1',scope:'Offline observer registration and exact Promise forwarding only; no product/native-decode qualification',status:'PASS',before,after};fs.writeFileSync(path.join(__dirname,'r124-OBSERVER-CONTROL.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:out.status,beforeNativeCalls:before.nativeCalls,afterNativeCalls:after.nativeCalls}));})().catch(e=>{console.error(e);process.exitCode=1;});
