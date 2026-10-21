/* Test observer/control only. Native Image.decode and original owner callbacks execute. */
(()=>{'use strict';
 const records=[],instances=[],installed=new WeakSet(),images=new WeakMap(),imageRecords=[],plans=new Map();
 const now=performance.now.bind(performance);let imageSerial=0,planSerial=0;
 const emit=(kind,data={})=>records.push({at:now(),kind,...data});
 const imageId=image=>{if(!image)return null;if(!images.has(image)){const id=++imageSerial;images.set(image,id);imageRecords.push({id,ref:new WeakRef(image),started:0,settled:0});}return images.get(image);};
 const imageRecord=image=>imageRecords.find(r=>r.id===imageId(image));
 const nativeDecode=HTMLImageElement.prototype.decode;
 HTMLImageElement.prototype.decode=function(){
  const r=imageRecord(this);r.started++;r.lastStartedAt=now();r.sourceBytes=this.src.length;
  const token=window.__r21.enter('image.decodeInitiation');let promise;
  try{promise=nativeDecode.call(this);}finally{window.__r21.leave(token);}
  emit('decode-start',{image:r.id,sourceBytes:r.sourceBytes});
  promise.then(()=>settled(r,'fulfilled'),error=>settled(r,'rejected',String(error.message??error)));
  return promise;
 };
 function settled(r,status,error=null){r.settled++;r.lastSettledAt=now();r.status=status;emit('decode-settled',{image:r.id,status,error});}
 function owner(instance){for(const name of ['preview','sky']){const o=window.__r21.readOwner(name);if(o?.solarPublication===instance)return {name,o};}return null;}
 function rootState(instance){
  const css=document.querySelector('.c')?.style.getPropertyValue('--native-sun-cloud-mask')??'';
  const roots=[];for(const key of ['pending','displayed','decoded']){const v=instance[key];if(v?.image)roots.push({root:key,image:imageId(v.image),decoded:key!=='pending',css:css===v.mask});}
  // A cancelled JS owner can still have its last committed mask displayed in CSS.
  for(const r of instances){const last=r.lastCss;if(r.instance.deref()===instance&&last&&last.mask===css)roots.push({root:'CSS',image:last.imageId,decoded:true,owner:r.id});}
  return {id:instances.find(r=>r.instance.deref()===instance)?.id,revision:instance.revision,disposed:instance.disposed,pending:instance.pending?1:0,retainedDecoded:[...new Set(roots.filter(r=>r.decoded).map(r=>r.image))].length,roots};
 }
 function snapshot(label){const value={label,at:now(),instances:instances.map(r=>{const s=r.instance.deref();return s?rootState(s):{id:r.id,collected:true};}),images:imageRecords.map(({ref,...r})=>({...r,weaklyReachable:!!ref.deref()})),counts:window.__r21.snapshot()};emit('snapshot',{label,instances:value.instances});return value;}
 function active(o){return o.name==='preview'?window.SalahSkyPreview?.state.status==='ready'&&!document.querySelector('.c').classList.contains('real-sky-composed'):window.SalahRealSky?.state.status==='ready'&&document.querySelector('.c').classList.contains('real-sky-composed');}
 function cancelOwner(o,dispose=false){
  if(o.name==='preview'){window.SalahSkyPreview.clear('TA3 controlled pending cancellation');if(dispose)window.SalahSkyPreview.dispose();}
  else {window.SalahRealSky.invalidate('TA3 controlled pending cancellation');if(dispose)window.SalahRealSky.dispose();}
 }
 function checked(p,stage){const s=rootState(p.instance);p.states.push({stage,...s});if(s.pending>1||s.retainedDecoded>2)throw Error('TA3 resource bound at '+stage);return s;}
 function register(instance){
  instances.push({id:instances.length+1,instance:new WeakRef(instance),lastCss:null});
  const proto=Object.getPrototypeOf(instance);if(installed.has(proto))return;installed.add(proto);
  const publish=proto.publish,finish=proto.finish;
  proto.publish=function(mask,commit,onError,context){
   const o=owner(this),p=o&&plans.get(o.name);let chosen=mask,stage=null;
   if(p&&!p.done&&p.instance===this&&!this.pending&&mask.startsWith('url(')){
    if(p.phase==='A'&&active(o)&&mask!==p.aMask)stage='A';
    else if(p.phase==='B'&&mask!==p.aMask)stage='B';
    else if(p.phase==='INVALID'){stage='INVALID';chosen='url("data:image/png;base64,AA==")';}
    else if(p.phase==='C'&&mask!==p.aMask&&mask!==p.bMask)stage='C';
    else if(p.phase==='DISPOSE'&&mask!==p.aMask)stage='DISPOSE';
   }
   const observedCommit=stage?function(...args){p.commitCalls.push({stage,at:now(),revision:this?.revision??null});return commit.apply(this,args);}:commit;
   const before=imageSerial,result=publish.call(this,chosen,observedCommit,onError,context);
   if(stage&&result){
    const image=this.pending?.image??this.displayed?.image,rev=this.revision;
    p.attempts.push({stage,image:imageId(image),revision:rev,positiveProductionPng:stage!=='INVALID',sourceBytes:chosen.length,at:now(),newNativeImage:imageSerial>before});
    if(stage==='A'){p.aMask=mask;p.phase='WAIT_A';}
    if(stage==='C'){p.cArgs=[mask,commit,onError,context];p.phase='WAIT_C';}
    if(stage==='INVALID'){p.invalidImage=imageId(image);p.invalidRevision=rev;p.phase='WAIT_INVALID';}
    if(stage==='B'||stage==='DISPOSE'){
     if(!this.pending)throw Error('Changed B must actually be pending');
     p.bMask=mask;p.staleImage=imageId(image);p.staleRevision=rev;p.phase=stage==='B'?'WAIT_STALE':'WAIT_DISPOSE';
     checked(p,'pending-'+stage);cancelOwner(o,stage==='DISPOSE');checked(p,'synchronous-cancel-'+stage);
    }
    checked(p,'published-'+stage);
   }
   return result;
  };
  proto.finish=function(candidate,revision,commit,onError,context){
   const o=owner(this),p=o&&plans.get(o.name),stale=this.disposed||revision!==this.revision;
   reaction(this,revision,'fulfilled');
   let result;try{result=finish.call(this,candidate,revision,commit,onError,context);}finally{reactionComplete(this,revision,'fulfilled');}
   if(this.displayed===candidate&&candidate.image){instances.find(r=>r.instance.deref()===this).lastCss={mask:candidate.mask,imageId:imageId(candidate.image)};}
   if(p&&!p.done&&!stale&&this.displayed===candidate){
    if(p.phase==='WAIT_A'){p.phase='B';p.commits.push({stage:'A',image:imageId(candidate.image),at:now()});checked(p,'A-commit');}
    else if(p.phase==='WAIT_C'){
     p.commits.push({stage:'C',image:imageId(candidate.image),at:now()});checked(p,'C-commit');
     const args=p.cArgs;p.cArgs=null;p.phase='CACHE';const count=imageRecords.reduce((n,r)=>n+r.started,0);const currentRevision=this.revision;
     const accepted=publish.apply(this,args);const after=imageRecords.reduce((n,r)=>n+r.started,0);
     p.cached={accepted,decodeStarts:after-count,displayedSame:this.displayed===candidate,revisionAdvanced:this.revision>currentRevision};checked(p,'C-cached-reuse');
     p.done=true;p.phase='DONE';p.aMask=null;p.bMask=null;
    }
   }
   return result;
  };
 }
 function visibleState(instance){const o=owner(instance)?.o;return {displayed:instance.displayed,decoded:instance.decoded,mask:document.querySelector('.c')?.style.getPropertyValue('--native-sun-cloud-mask'),paintedFrame:o?.paintedFrame,paintedJob:o?.paintedJob,previewFrame:o?.previewFrame,value:o?.value};}
 function reaction(instance,revision,kind){
  const o=owner(instance),p=o&&plans.get(o.name);emit('native-publication-reaction',{owner:o?.name,revision,currentRevision:instance.revision,disposed:instance.disposed,kind});
  if(!p||p.done)return;
  if(revision===p.staleRevision){
   p.staleBefore=visibleState(instance);p.stale={revision,currentRevision:instance.revision,kind,disposed:instance.disposed,at:now(),fenced:instance.disposed||revision!==instance.revision};
   if(p.phase==='WAIT_STALE')p.phase=p.index===0?'INVALID':'C';
   else if(p.phase==='WAIT_DISPOSE'){p.done=true;p.phase='DONE';p.aMask=null;p.bMask=null;}
  }else if(revision===p.invalidRevision&&p.phase==='WAIT_INVALID'){p.invalidReaction={kind,at:now()};p.phase='C';}
 }
 function reactionComplete(instance,revision,kind){
  const o=owner(instance),p=o&&plans.get(o.name);if(!p||revision!==p.staleRevision)return;
  const after=visibleState(instance);p.stale.actualReactionCompleted=true;p.stale.visibleAndOwnerUnchanged=Object.keys(after).every(k=>after[k]===p.staleBefore[k]);p.stale.commitCalls=p.commitCalls.filter(x=>x.stage==='B'||x.stage==='DISPOSE').length;p.staleBefore=null;
  emit('stale-reaction-complete',{owner:o.name,revision,kind,...p.stale});
 }
 async function run(name,index,disposal=false){
  const o=window.__r21.readOwner(name),instance=o?.solarPublication;if(!instance||instance.disposed)throw Error('Missing live publication owner '+name);
  const p={id:++planSerial,index,instance,phase:disposal?'DISPOSE':'A',aMask:instance.displayed?.mask??null,bMask:null,attempts:[],states:[],commits:[],commitCalls:[],done:false};plans.set(name,p);
  const begin=now();while(!p.done){
   for(const attempt of p.attempts){const r=imageRecords.find(r=>r.id===attempt.image);if(r&&r.started>r.settled&&now()-r.lastStartedAt>10000)throw Error('INCOMPLETE native decode settlement10s');}
   if(now()-begin>30000)throw Error('INCOMPLETE finite cycle30s');
   await new Promise(resolve=>setTimeout(resolve,20));
  }
  await new Promise(resolve=>setTimeout(resolve,0));checked(p,'complete');
  const result={...p,instance:undefined,aMask:undefined,bMask:undefined,cArgs:undefined,elapsedMs:now()-begin};plans.delete(name);
  if(!p.stale?.fenced||!p.stale.actualReactionCompleted||!p.stale.visibleAndOwnerUnchanged||p.stale.commitCalls!==0)throw Error('Stale reaction changed visible content/owner or called commit');
  if(!disposal&&index===0&&(!p.invalidImage||p.invalidReaction?.kind!=='rejected'||imageRecords.find(r=>r.id===p.invalidImage)?.status!=='rejected'))throw Error('Missing actual invalid PNG native rejection');
  if(!disposal&&(!p.cached?.accepted||p.cached.decodeStarts!==0||!p.cached.displayedSame))throw Error('Cached C was not reused');
  if(disposal&&(!instance.disposed||instance.pending||instance.displayed||instance.decoded||rootState(instance).retainedDecoded))throw Error('Disposal retained a publication or CSS root');
  for(const attempt of p.attempts){const r=imageRecords.find(r=>r.id===attempt.image);if(r&&r.started!==r.settled)throw Error('Unsettled native decode at completed cycle');}
  return result;
 }
 window.__r21Resources={register,reaction,reactionComplete,run,snapshot,export:()=>({records,images:imageRecords.map(({ref,...r})=>r),instances:instances.map(r=>{const s=r.instance.deref();return s?rootState(s):{id:r.id,collected:true};})})};
})();
