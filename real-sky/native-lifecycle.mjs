import {nativeIdentity,nativeJob,nativeResultCurrent} from './native-contract.mjs';
import {LatestRenderQueue} from './core/src/latest-render-queue.mjs';

/** Native-only scheduling/fencing. Never supplies or advances astronomical time.
 * One active execution and one newest pending request belong to the retained queue.
 * Monotonic time detects wall-clock discontinuities; it is never a render UTC.
 */
export class NativeSkyLifecycle {
 constructor({capture,execute,onResult=()=>{},onInvalidate=()=>{},onError=()=>{},now=()=>performance.now(),physical=true,intervalMs=4000}) {
  this.capture=capture;this.now=now;this.physical=physical;this.intervalMs=intervalMs;
  this.hooks={onResult,onInvalidate,onError};this.epoch=0;this.identity=null;this.observed=null;
  this.displayed=null;this.latest=null;this.pending=null;this.lastSubmit=-Infinity;this.disposed=false;
  this.counts={requests:0,accepted:0,superseded:0,rejected:0,invalidations:0};
  this.queue=new LatestRenderQueue(execute,{
   onResult:(result,id,job)=>{
    if(!this.current(job)){this.counts.rejected++;return;}
    if(result.status!=='ready'||!result.raster)throw new Error(result.error??'Native real sky unavailable');
    this.displayed=job;this.hooks.onResult(result,id,job);this.counts.accepted++;
   },
   onError:(error,id)=>{if(this.current(this.latest))this.hooks.onError(error,id);else this.counts.rejected++;}
  });
 }
 get state(){return {...this.counts,epoch:this.epoch,disposed:this.disposed,pending:!!this.pending,paused:!!this.observed?.paused};}
 invalidate(reason='native invalidation') {
  if(this.disposed)return;
  this.epoch++;this.displayed=null;this.counts.invalidations++;this.hooks.onInvalidate(reason);
 }
 observe(state=this.capture()) {
  if(this.disposed)return null;
  let key;
  try{key=nativeIdentity(state);}catch(error){
   if(this.identity!==null||this.observed!==null)this.invalidate('invalid accepted native input');
   this.identity=null;this.observed=null;return null;
  }
  const now=this.now(),rate=Number.isFinite(state.timeScale)?state.timeScale:1,prior=this.observed;
  // Native explicit preview anchors are already part of sceneIdentity. This also
  // catches host wall-clock corrections without inventing a private wall clock.
  const jump=prior&&Math.abs((state.utcMs-prior.utcMs)-(now-prior.now)*prior.rate)>1000;
  let reason=null;
  if(key!==this.identity)reason='new accepted native scene';
  else if(prior&&!!state.paused!==prior.paused)reason=state.paused?'native hidden/paused':'native visible/resumed';
  else if(jump)reason='native clock discontinuity';
  else if(this.displayed&&!nativeResultCurrent(this.displayed,state))reason='native frame expired';
  this.identity=key;this.observed={now,utcMs:state.utcMs,rate,paused:!!state.paused};
  if(reason)this.invalidate(reason);
  return state;
 }
 current(job,state) {
  if(this.disposed||!job)return false;
  let current;
  try{current=this.observe(state??this.capture());}catch{return false;}
  return !!current&&!current.paused&&job.native.lifecycleEpoch===this.epoch&&nativeResultCurrent(job,current);
 }
 request(force=false) {
  if(this.disposed)return Promise.resolve({status:'disposed'});
  let state;
  try{state=this.observe();}catch(error){this.invalidate('host capture failed');this.hooks.onError(error);return Promise.resolve({status:'invalid'});}
  if(!state){this.hooks.onError(new Error('Invalid accepted native input'));return Promise.resolve({status:'invalid'});}
  if(state.paused)return Promise.resolve({status:'paused'});
  const changed=!this.latest||this.latest.native.lifecycleEpoch!==this.epoch;
  if(!force&&!changed&&this.pending)return Promise.resolve({status:'pending'});
  if(!force&&!changed&&this.displayed?.observer.utcMs===state.utcMs)return Promise.resolve({status:'unchanged'});
  if(!force&&!changed&&this.now()-this.lastSubmit<this.intervalMs)return Promise.resolve({status:'throttled'});
  const job=nativeJob(state,this.physical);job.native.lifecycleEpoch=this.epoch;
  this.latest=job;this.pending=job;this.lastSubmit=this.now();this.counts.requests++;
  return this.queue.submit(job).then(result=>{
   if(this.pending===job)this.pending=null;
   if(result.status==='superseded')this.counts.superseded++;
   return {status:result.status,id:result.id};
  });
 }
 dispose(){if(this.disposed)return;this.invalidate('disposed');this.disposed=true;this.queue.dispose();this.pending=null;this.latest=null;this.observed=null;}
}
