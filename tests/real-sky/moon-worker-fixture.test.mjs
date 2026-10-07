import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync(new URL('../../tools/cp9/native_lifecycle_check.py',import.meta.url),'utf8');
const instrument=source.match(/INSTRUMENT=r'''([\s\S]*?)'''/)[1];
function rig(){
 class ActualWorker{constructor(){this.sent=[];}postMessage(m){this.sent.push(m);}terminate(){}}
 class CanvasRenderingContext2D{putImageData(){}}
 const c=vm.createContext({Worker:ActualWorker,CanvasRenderingContext2D,Blob,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},document:{}});
 c.window=c;vm.runInContext(instrument,c);return c;
}
test('CP9 lifecycle fixture passes Moon protocol through without treating it as a sky job',()=>{
 const c=rig(),w=new c.Worker('blob:moon');w.postMessage({kind:'boot',offline:false});
 assert.doesNotThrow(()=>w.postMessage({kind:'render',scene:{fraction:.5}}));
 assert.equal(c.__workerControl.submissions.length,0);assert.equal(c.__workerControl.instances.length,0);
 c.__workerControl.mode='startup-hang';let delivered=false;w.onmessage=()=>{delivered=true;};w.actual.onmessage({data:{kind:'ready'}});assert.equal(delivered,true);
});
test('CP9 worker hold and failure controls remain active on their own worker',()=>{
 const c=rig(),w=new c.Worker('blob:sky');w.postMessage({kind:'boot',pack:{}});
 const job={observer:{utcMs:1,latDeg:2},native:{generation:3,lifecycleEpoch:4}};
 w.postMessage({kind:'render',job});assert.equal(c.__workerControl.submissions.length,1);assert.equal(c.__workerControl.instances.length,1);
 c.__workerControl.hold=true;w.actual.onmessage({data:{kind:'result'}});assert.equal(c.__workerControl.held.length,1);
 c.__workerControl.mode='post-failure';assert.throws(()=>w.postMessage({kind:'render',job}),/Controlled worker postMessage failure/);
});
