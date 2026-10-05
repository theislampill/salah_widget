/** RPC is sequential (the LatestRenderQueue owns replacement/coalescing).
 * Worker startup/crash/timeouts recover with an explicitly labelled main-thread
 * engine; scientific/render errors never silently choose a different sky.
 */
import {ReferenceSkyEngine} from './reference-engine.mjs';
export class ReferenceRenderClient{
 #pack;#worker=null;#fallback=null;#fallbackFactory;#ready;#readyResolve;#bootTimer;#timeout;#serial=0;#pending=new Map();#disposed=false;#mode='starting';#warnings=[];
 constructor(pack,{workerFactory=null,fallbackFactory=p=>new ReferenceSkyEngine(p),timeoutMs=120000}={}){
  if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>600000)throw new RangeError('Bounded worker timeout required');
  this.#pack=pack;this.#timeout=timeoutMs;this.#fallbackFactory=fallbackFactory;this.#ready=new Promise(resolve=>{this.#readyResolve=resolve;});
  try{
   if(typeof workerFactory!=='function')throw new Error('Web Worker unavailable or explicitly disabled');
   const w=workerFactory();this.#worker=w;
   w.onmessage=e=>this.#receive(e.data);w.onerror=e=>{e.preventDefault?.();this.#failWorker(e.message??'Worker error');};w.onmessageerror=()=>this.#failWorker('Worker message could not be decoded');
   this.#bootTimer=setTimeout(()=>this.#failWorker('Worker startup timeout'),timeoutMs);w.postMessage({kind:'boot',pack});
  }catch(e){this.#failWorker(e.message??String(e));}
 }
 get mode(){return this.#mode;}
 get warnings(){return [...this.#warnings];}
 #receive(m){
  if(this.#disposed)return;
  if(m?.kind==='fatal'){this.#failWorker(m.error??'Unhandled worker rejection');return;}
  if(m?.kind==='ready'&&this.#worker){clearTimeout(this.#bootTimer);this.#mode='worker';this.#readyResolve(true);return;}
  if(m?.kind==='error'&&m.id==null){this.#failWorker(m.error??'Worker startup failed');return;}
  const p=this.#pending.get(m?.id);if(!p)return;clearTimeout(p.timer);this.#pending.delete(m.id);
  if(m.kind==='result')p.resolve(m.result);else p.reject(new Error(m.error??'Invalid worker response'));
 }
 #failWorker(reason){
  if(this.#disposed)return;this.#warnings.push(String(reason));this.#mode='main-thread-fallback';clearTimeout(this.#bootTimer);
  this.#worker?.terminate();this.#worker=null;this.#readyResolve(false);
  for(const p of this.#pending.values()){clearTimeout(p.timer);const e=new Error(String(reason));e.code='WORKER_UNAVAILABLE';p.reject(e);}this.#pending.clear();
 }
 async run(job){
  if(this.#disposed)throw new Error('Render client disposed');await this.#ready;if(this.#disposed)throw new Error('Render client disposed');
  if(this.#worker){
   if(this.#pending.size)throw new Error('Worker client requires the latest-only sequential queue');
   try{
    const result=await new Promise((resolve,reject)=>{const id=++this.#serial,timer=setTimeout(()=>this.#failWorker('Worker render timeout'),this.#timeout);this.#pending.set(id,{resolve,reject,timer});try{this.#worker.postMessage({kind:'render',id,job});}catch(e){this.#failWorker(e.message??String(e));}});
    return {...result,execution:{mode:'worker',warnings:this.warnings}};
   }catch(e){if(e.code!=='WORKER_UNAVAILABLE')throw e;}
  }
  if(this.#disposed)throw new Error('Render client disposed');
  this.#fallback??=this.#fallbackFactory(this.#pack);await new Promise(resolve=>setTimeout(resolve,0));
  if(this.#disposed)throw new Error('Render client disposed');const result=await this.#fallback.render(job);
  return {...result,execution:{mode:'main-thread-fallback',warnings:this.warnings}};
 }
 /** Reference-viewer fault drill, never invoked by scientific calculation. */
 crashForTest(){this.#worker?.postMessage({kind:'crash-test'});}
 dispose(){
  if(this.#disposed)return;this.#disposed=true;this.#mode='disposed';clearTimeout(this.#bootTimer);this.#readyResolve(false);this.#worker?.terminate();this.#worker=null;
  for(const p of this.#pending.values()){clearTimeout(p.timer);p.reject(new Error('Render client disposed'));}this.#pending.clear();this.#fallback?.dispose();this.#fallback=null;this.#pack=null;
 }
}
