// Installed only by the disposable native build. One latest accepted frame,
// one candidate worker, one in-flight sample, one extra sky canvas. The host
// keeps ownership of its original canvas, lifecycle, Moon, controls and UI.
import {nativeDiscMask,nativeResultCurrent} from '../../real-sky/native-contract.mjs';
import {SampleHistory} from './sample_history.mjs';
import {FrameGuard} from './frame_guard.mjs';
import {PresentationWriter} from './changed_rectangles.mjs';

export function installLab(config){
  if(!['full','changed'].includes(config.arm)||![8,16,32,64,128,530].includes(config.tile??16)||![1,2,3,4].includes(config.multiplier)
      ||!['all','preview-members'].includes(config.scope)||!Number.isFinite(config.margin)||config.margin<0
      ||!Number.isFinite(config.glassFactor)||config.glassFactor<0||config.glassFactor>1)throw new RangeError('Incomplete lab configuration');
  const guard=new FrameGuard(config.guard!==false);
  const worker=new Worker(new URL('./lab_worker.mjs',import.meta.url),{type:'module'});
  const overlay=document.createElement('canvas');overlay.width=325;overlay.height=530;overlay.setAttribute('aria-hidden','true');
  Object.assign(overlay.style,{position:'absolute',inset:'0',width:'100%',height:'100%',borderRadius:'inherit',pointerEvents:'none',zIndex:'0',visibility:'hidden'});
  const writer=new PresentationWriter(overlay.getContext('2d',{alpha:true}),config.arm,config.tile??16);
  let source=null,epoch=0,prepared=false,pending=false,terminal=false,preparing=null,latest=null;
  let state={status:'awaiting accepted sky',sourceCount:0,sample:null,frames:0,writes:0,pixels:0,late:0};
  const transitions=[],history=new SampleHistory();
  let trial=null,lastSignal=null,requestedUtc=null;
  function event(kind,details={}){
    if(!trial)return;
    if(trial.events.length>=16384){trial.overflow=true;return;}
    trial.events.push({at:performance.now(),kind,epoch,tier:source?.tier??null,identity:source?.job.native.identity??null,...details});
  }
  function status(reason){
    if(state.status!==reason){
      transitions.push({at:performance.now(),reason,frame:state.frames});
      if(transitions.length>128)transitions.shift();
      state.status=reason;event('status',{reason});
    }
  }
  const inactive=reason=>{overlay.style.visibility='hidden';lastSignal=null;status(reason);state.sample=null;state.utcMs=null;state.nonempty=null;if(reason!=='preparing accepted frame')history.reset();};
  function admissible(){
    if(!source||terminal)return false;
    const snap=window.SalahNativeSkyHost.capture(false);
    return !snap.paused && !snap.reducedMotion && snap.timeScale>0 && nativeResultCurrent(source.job,snap)
      && window.SalahNativeSkyHost.cloudsCurrent(source.authority)
      && source.canvas.parentElement?.classList.contains(source.tier==='refined'?'real-sky-composed':'real-sky-preview-ready')
      && (source.tier==='refined'||!source.canvas.parentElement.classList.contains('real-sky-composed'));
  }
  function revoke(reason){
    epoch++;source=null;latest=null;prepared=false;pending=false;guard.reset();writer.invalidate();
    Object.assign(state,{sourceCount:0,census:null,contributingCenters:0,variablePixels:0,sample:null,utcMs:null,guard:null});
    inactive(reason);event('withdraw',{reason});
  }
  function renew(canvas,job,frame,capture){
    if(source?.canvas!==canvas||source.job!==job||source.raster!==frame.raster)return;
    source.authority=capture.cloudAuthority;source.args[4]=capture;
  }
  const failed=reason=>{terminal=true;inactive(reason);worker.terminate();};
  function dispatchLatest(){
    if(terminal||preparing!==null||!latest)return;
    const make=latest;latest=null;preparing=epoch;
    try{worker.postMessage(make());}catch(e){failed(String(e));}
  }
  function glassBounds(canvas){
    const rect=canvas.getBoundingClientRect();
    return [...canvas.parentElement.querySelectorAll('.e,.wt,.buckle,.times .p,.settings,.simclock,.dbgmotion,.dbglayers,.dbgmoon')]
      .map(n=>n.getBoundingClientRect()).filter(b=>b.width&&b.height).map(b=>({x:(b.left-rect.left)*325/rect.width,
        y:(b.top-rect.top)*530/rect.height,width:b.width*325/rect.width,height:b.height*530/rect.height}));
  }
  function separateDisc(canvas,mask){
    if(mask)return null;
    const disc=canvas.parentElement.querySelector?.('.moon-mask-disc');
    if(!disc?.classList.contains('mask-on')||Number(getComputedStyle(disc).opacity)===0)return null;
    const m=disc.getScreenCTM();if(!m)return null;
    const r=canvas.getBoundingClientRect();
    return {rect:{left:r.left,top:r.top,width:r.width,height:r.height},matrix:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f},radius:Number(disc.getAttribute('r'))};
  }
  worker.onerror=event=>failed('worker: '+event.message);
  worker.onmessage=({data:m})=>{
    if(terminal)return;
    if((m.op==='ready'||m.op==='failed')&&preparing===m.epoch){preparing=null;dispatchLatest();}
    if(m.epoch!==epoch)return;
    try{
      if(m.op==='failed'){prepared=false;inactive(m.reason);return;}
      if(m.op==='ready'){prepared=true;state.sourceCount=m.sources;state.census=m.census;state.contributingCenters=m.contributingCenters;state.variablePixels=m.variablePixels;status(m.variablePixels?'prepared':'no display response');return;}
      if(m.op!=='sample'||!pending)return;pending=false;
      if(!admissible()){inactive('unavailable, paused or reduced');return;}
      if(!Number.isFinite(m.utcMs)||m.utcMs!==requestedUtc){inactive('sample timestamp mismatch');return;}
      const ageMs=Math.abs(window.SalahNativeSkyHost.capture(false).utcMs-m.utcMs);
      if(ageMs>100){state.late++;inactive('sample older than 100 accepted ms');return;}
      if(!(m.signal instanceof Uint32Array)||m.signal.length!==state.variablePixels)throw new Error('Incomplete encoded stellar signal');
      const nonempty=m.signal.some(pixel=>pixel!==0);
      const write=writer.publish(new ImageData(m.rgba,325,530));
      overlay.style.visibility='visible';
      status('active');
      if(m.sample)history.add(performance.now(),m.utcMs,m.sample,source.job.native.identity);
      else history.reset();
      const changed=!!lastSignal&&m.signal.some((p,i)=>p!==lastSignal[i]);lastSignal=m.signal;
      event('publication',{utcMs:m.utcMs,ageMs,changed,nonempty,writes:write.writes,id:m.sample?.id??null});
      state={...state,frames:state.frames+1,writes:state.writes+write.writes,pixels:state.pixels+write.pixels,nonempty,sample:m.sample,utcMs:m.utcMs};
    }catch(e){failed(String(e));}
  };
  function present(){
    if(terminal||!source)return;
    try{
      if(!admissible()){guard.reset();inactive('unavailable, paused or reduced');return;}
      if(source.boxes!==JSON.stringify(glassBounds(source.canvas))||source.discKey!==JSON.stringify(separateDisc(source.canvas,source.mask))){publish(...source.args);return;}
      const now=performance.now();guard.observe(now);
      if(pending||!prepared||!state.variablePixels)return;
      const s=window.SalahNativeSkyHost.capture(false);
      const gain=guard.nextGain(now);
      state.guard={enabled:guard.enabled,gain,retryAt:guard.retryAt};
      if(!gain){inactive('performance guard suspended');return;}
      requestedUtc=s.utcMs;pending=true;worker.postMessage({op:'sample',epoch,utcMs:requestedUtc,motion:{gain,paused:s.paused,reduced:s.reducedMotion}});
    }catch(e){failed(String(e));}
  }
  function publish(tier,canvas,job,frame,capture,mask){
    if(terminal)return;
    try{
      if(!frame.raster.starPreview && tier==='preview'){revoke('preview has no catalogue');return;}
      const r=frame.raster,glass=glassBounds(canvas),disc=separateDisc(canvas,mask),discKey=JSON.stringify(disc);
      const same=(a,b)=>a===b||!!a&&!!b&&a.length===b.length&&a.every((v,i)=>v===b[i]);
      if(source?.raster===r&&source.canvas===canvas&&source.discKey===discKey&&source.boxes===JSON.stringify(glass)
          &&same(source.cloud,capture.cloudRGBA)&&same(source.moon,capture.moonRGBA)&&same(source.mask,mask)){
        renew(canvas,job,frame,capture);return;
      }
      epoch++;pending=false;prepared=false;inactive('preparing accepted frame');writer.invalidate();
      Object.assign(state,{sourceCount:0,census:null,variablePixels:0,contributingCenters:0,guard:null});
      canvas.after(overlay);
      source={args:[tier,canvas,job,frame,capture,mask],job,tier,canvas,raster:r,mask,discKey,boxes:JSON.stringify(glass),cloud:capture.cloudRGBA,moon:capture.moonRGBA,authority:capture.cloudAuthority};
      event('owner');latest=()=>{
      const pad=(a,stride,defaultValue)=>{if(!a)return null;const out=new a.constructor(325*530*stride);if(defaultValue)out.fill(defaultValue);out.set(a);return out;};
      const raster={width:r.width,height:r.height,stellarLinear:r.stellarLinear,skyBackgroundLinear:r.skyBackgroundLinear??r.backgroundLinear,
        diffusePhysicalLinear:r.diffusePhysicalLinear,physicalState:r.physicalState,atmosphere:r.atmosphere,effectiveExposure:r.effectiveExposure,
        sourceDiagnostics:r.sourceDiagnostics,starPreview:r.starPreview};
      const nominal=canvas.getContext('2d').getImageData(0,0,325,530).data;
      return {op:'prepare',epoch,job,config,frame:{status:frame.status,sources:frame.sources??frame.replaySources,
        catalogue:frame.catalogue,diffuseAsset:frame.diffuseAsset,raster},nominal,
        foreground:{glass,cloudRGBA:pad(capture.cloudRGBA,4),moonRGBA:pad(capture.moonRGBA,4),mask:pad(mask,1,1),signalMask:disc?nativeDiscMask(325,530,disc.rect,disc.matrix,disc.radius):null}};};
      dispatchLatest();
    }catch(e){failed(String(e));}
  }
  function clear(canvas){
    if(source?.canvas!==canvas)return;
    revoke('owner withdrew');
  }
  function dispose(){terminal=true;worker.terminate();overlay.remove();source=null;inactive('disposed');}
  window.addEventListener('pagehide',event=>{if(!event.persisted)dispose();else inactive('page hidden');});
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',()=>{if(!admissible())inactive('motion preference changed');});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)inactive('document hidden');});
  return {publish,present,clear,dispose,renew,
    beginTrial(){trial={start:performance.now(),initial:{status:state.status,tier:source?.tier??null,identity:source?.job.native.identity??null},overflow:false,events:[]};},
    endTrial(){if(!trial)return null;const result={...trial,end:performance.now()};trial=null;return result;},
    debugLine:()=>history.line(performance.now()),observe:()=>structuredClone({...state,transitions})};
}
