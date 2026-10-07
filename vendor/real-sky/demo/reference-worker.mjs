import {ReferenceSkyEngine,rasterTransferables} from '../src/reference-engine.mjs';
let workerEngine=null;
// An async event handler can reject without raising a synchronous Worker error.
// Explicitly forward the fatal rejection so the accepted job is not stranded.
self.addEventListener('unhandledrejection',event=>{
 event.preventDefault();
 self.postMessage({kind:'fatal',error:String(event.reason?.message??event.reason)});
 workerEngine?.dispose();workerEngine=null;self.close();
});
self.onmessage=async event=>{
 const {kind,id,pack,job}=event.data??{};
 if(kind==='crash-test')throw new Error('Deliberate CP7.5 worker failure drill');
 try{
  if(kind==='boot'){workerEngine?.dispose();workerEngine=new ReferenceSkyEngine(pack);self.postMessage({kind:'ready'});return;}
  if(kind==='render'){if(!workerEngine)throw new Error('Worker is not initialised');const result=await workerEngine.render(job);self.postMessage({kind:'result',id,result},rasterTransferables(result));return;}
  if(kind==='dispose'){workerEngine?.dispose();workerEngine=null;self.close();return;}
  throw new Error('Unknown reference worker message');
 }catch(e){self.postMessage({kind:'error',id,error:String(e?.message??e)});}
};
