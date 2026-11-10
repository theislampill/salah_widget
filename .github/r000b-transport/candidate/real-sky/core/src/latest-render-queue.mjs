/** One in-flight render + one latest replacement. No timer or observer-time cache.
 * The UI is invalidated immediately on submission, and only the latest ID publishes.
 * execute() may be a worker RPC or the explicitly labelled synchronous fallback.
 */
export class LatestRenderQueue{
 #execute;#hooks;#next=0;#busy=false;#pending=null;#disposed=false;
 constructor(execute,hooks={}){if(typeof execute!=='function')throw new TypeError('Render executor required');this.#execute=execute;this.#hooks=hooks;}
 submit(request){
  if(this.#disposed)return Promise.resolve({status:'disposed'});
  const id=++this.#next;
  if(this.#pending){this.#pending.resolve({status:'superseded',id:this.#pending.id});this.#pending=null;}
  let snapshot;
  try{snapshot=structuredClone(request);}catch(e){this.#hooks.onPending?.(id);this.#hooks.onError?.(e,id);return Promise.resolve({status:'error',id,error:String(e.message??e)});}
  this.#hooks.onPending?.(id);
  const promise=new Promise(resolve=>{this.#pending={id,request:snapshot,resolve};});this.#drain();return promise;
 }
 async #drain(){
  if(this.#busy||!this.#pending||this.#disposed)return;
  this.#busy=true;const job=this.#pending;this.#pending=null;
  try{const result=await this.#execute(job.request,job.id);
   if(this.#disposed)job.resolve({status:'disposed',id:job.id});
   else if(job.id!==this.#next)job.resolve({status:'superseded',id:job.id});
   else{this.#hooks.onResult?.(result,job.id,job.request);job.resolve({status:'ready',id:job.id,result});}
  }catch(e){
   if(this.#disposed)job.resolve({status:'disposed',id:job.id});
   else if(job.id!==this.#next)job.resolve({status:'superseded',id:job.id});
   else{this.#hooks.onError?.(e,job.id);job.resolve({status:'error',id:job.id,error:String(e?.message??e)});}
  }finally{this.#busy=false;this.#drain();}
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#next++;if(this.#pending){this.#pending.resolve({status:'disposed',id:this.#pending.id});this.#pending=null;}}
}
