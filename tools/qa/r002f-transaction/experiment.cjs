'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {transform,combine,sha}=require('./materialize.cjs');
const root=path.resolve(__dirname,'../../..');
const get=f=>fs.readFileSync(path.join(root,f),'utf8');
function range(s,from,to){const begin=s.indexOf(from),end=s.indexOf(to,begin+1);assert(begin>=0&&end>begin);return s.slice(begin,end);}
function swap(s,from,to){assert.equal(s.split(from).length,2,from.slice(0,90));return s.replace(from,()=>to);}
async function run(){
 const {outputs,sources,stage}=transform();
 const {nativeCloudChannel,validateNativeRGBA,nativeCloudDisplayFrame}=await import(pathToFileURL(path.join(root,'real-sky/native-cloud-transfer.mjs')));
 const {encodeNativeFrame}=await import(pathToFileURL(path.join(root,'real-sky/native-encoding.mjs')));
 const {NativeForegroundCapture,NativeSolarMaskPublication}=await import(pathToFileURL(path.join(root,'real-sky/native-composition.mjs')));
 const hostSource=get('tests/real-sky/native-preview-host.test.mjs'),detailSource=get('tests/real-sky/moon-projection-cache.test.mjs');
 let projection=range(detailSource,'function surface(level=1','\nassert.equal(sha(original)');
 projection=swap(projection,"s.publishes.push({w:im.width,h:im.height,bytes:Buffer.from(im.data),style:cv.style});","cv.bytes=Buffer.from(im.data);s.publishes.push({w:im.width,h:im.height,bytes:cv.bytes,style:cv.style});if(cv!==s.canvases[0])control.hit('detail-upload');");
 projection=swap(projection,"surface:()=>s.adopted","surface:()=>{control.lunarReads++;return s.adopted;}");
 projection=swap(projection,"return {s,api,adopt,compose,classes};",`const material=surface();adopt(material);
 const ctx=vm.createContext(context);
 const leaseScript=leaseFunctions+'\\nwindow.SalahMoonRuntime.acquire=researchMoonLease;window.seed=m=>{accepted={token:++token};researchMaterial.set(accepted,m);};';
 Object.assign(ctx,{control,realDetail:api});
 vm.runInContext(leaseScript,ctx);ctx.window.seed(material);
 return {s,api,adopt,compose,classes,lease:()=>ctx.window.SalahMoonRuntime.acquire(),replace(){ctx.window.seed(material);},geo(){s.x+=1;},get geometry(){return s.x;}};`);
 const leaseSource=range(outputs[2],'function startResearchDetail',' function adopt(m,record){');
 // Physical and lunar projection code is the same source that the historical
 // fault probe exercises. The accepted record/epoch/clock below are controlled.
 const leaseFunctions=sources[3].replace(/^import .*;\r?\n/gm,'')+ '\nlet token=0,accepted=null,waitingPreview=null,disposed=false;function capture(){return {epoch:control.epoch};}function matches(record,s){return !!record&&s.epoch===1;}\n'+leaseSource;
 const detailFactory=new Function('vm','Buffer','assert','nativeCloudChannel','validateNativeRGBA','control','leaseFunctions',projection+';return source=>instance(source);');
 let harness=range(hostSource,'function host({','\nfunction initialHead(){');
 harness=swap(harness,'return deferMask?new Promise','return (deferMask||ctl.defer)?new Promise');
 harness=swap(harness,'const classes=new Set(),draws=[]','const classes=owner.classes,draws=[]');
 harness=swap(harness,'const c={style:{},setAttribute(){},getContext:()=>ctx,remove(){}};',`const c={style:{},setAttribute(){},getContext:()=>Object.assign({},ctx,{putImageData(image){if(ctl.failLegacy&&jobUtc===21000)throw Error('controlled legacy upload');c.bytes=Buffer.from(image.data);if(c.className?.startsWith('r002f-sky-'))ctl.hit('background-upload');else{if(ctl.failLegacy&&jobUtc===21000)throw Error('controlled legacy upload');ctx.putImageData(image);}}}),remove(){c.isConnected=false;}};`);
 harness=swap(harness,'const card={prepend(){},style:{setProperty(){},removeProperty(){}},',`const attrs=new Map();const card={prepend(node){node.isConnected=true;if(node.className?.startsWith('r002f-sky-'))ctl.hit('background-attach');},querySelector(q){return q==='.sky'?{after(node){node.isConnected=true;ctl.hit('detail-attach');}}:null;},
 getAttribute:k=>attrs.get(k)||null,removeAttribute:k=>attrs.delete(k),setAttribute(k,v){if(k!=='data-r002f-preview'){attrs.set(k,v);return;}ctl.hit('before-select');attrs.set(k,v);ctl.hit('after-select');},style:{setProperty(k,v){this[k]=v;},removeProperty(k){delete this[k];}},`);
 harness=swap(harness,'createElement:canvas},Uint8ClampedArray',`head:{append(node){node.isConnected=true;ctl.hit('style-attach');}},createElement(tag){return tag==='style'?ctl.style():canvas();}},Uint8ClampedArray`);
 harness=swap(harness,"native:{}};}prepareSolarMask","native:{cloudAuthority:ctl.cloud},cloudAuthority:ctl.cloud};}prepareSolarMask");
 harness=swap(harness,'vm.createContext(s);vm.runInContext(source',`s.window.SalahMoonDetail=owner.api;s.window.SalahMoonRuntime={researchMoonLease:owner.lease};
 s.window.SalahNativeSkyHost.cloudsCurrent=receipt=>receipt===ctl.cloud;
 s.window.SalahNativeSkyHost.capture=(presentation=true,moon=presentation)=>{if(presentation)ctl.anchors.push(moon);return {utcMs:now*timeScale,generation:ctl.weather,timeScale,sceneIdentity:'A',lat:1,lon:2};};
 s.encodeNativeFrame=encode;s.nativeCloudDisplayFrame=cloudFrame;
 s.renderNativeBackgroundPreview=c=>{jobUtc=c.utcMs;const width=325,height=530,base=jobUtc===0?.003:jobUtc<=20500?.012:jobUtc>42100?.043:.026,linear=Float64Array.from({length:width*height*3},(_,i)=>base*(1+((i%37)/40)));return {job:{utcMs:jobUtc,generation:c.generation},utcMs:jobUtc,quality:'fixture',raster:{width,height,effectiveExposure:12,linear,skyBackgroundLinear:linear,fixtureUtc:jobUtc,physicalState:{sun:{altDeg:30}}}};};
 ctl.attach({card,attrs,canvases,classes,visiblePixels,api:()=>s.window.SalahSkyPreview,advance:ms=>now+=ms,transfer(){classes.add('real-sky-composed');}});
 vm.createContext(s);vm.runInContext(source`);
 function arm(name,original=false,established=false){
  const events=[],styles=[];let env,owner,h,armed=false,acted=false;
  const ctl={cloud:1,weather:1,epoch:1,anchors:[],defer:false,lunarReads:0,failLegacy:original&&name!=='legacy-success',style(){const n={textContent:'',isConnected:false,remove(){this.isConnected=false;}};styles.push(n);return n;},attach:e=>env=e,hit(event){
    if(!armed)return;
    events.push({event,...observe()});
    if(event==='background-upload'&&acted&&name==='after-select-inner-fails')throw Error('nested staging upload failed');
    if(event==='after-select'&&!acted&&(name==='after-select-nested'||name==='after-select-inner-fails')){
     acted=true;h.changeMask();const later=established?62600:42500;h.present(later,later);return;
    }
    if(acted)return;
    if(event===name){acted=true;throw Error('injected '+name);}
    if(event!=='detail-attach')return;
    acted=true;
    switch(name){
      case 'cloud':ctl.cloud++;break;
      case 'weather':ctl.weather++;break;
      case 'epoch':ctl.epoch++;break;
      case 'adoption':owner.replace();break;
      case 'geometry':owner.geo();break;
      case 'expiry':env.advance(31006);break;
      case 'refined':env.transfer();break;
      case 'nested':h.present(established?42500:22000,established?42500:22000);break;
      default:acted=false;
    }
  }};
  owner=detailFactory(vm,Buffer,assert,nativeCloudChannel,validateNativeRGBA,ctl,leaseFunctions)(sources[3].replace(/^import .*;\r?\n/gm,''));
  owner.classes.delete('real-sky-composed');owner.classes.delete('real-sky-preview-ready');
  function observe(){
   const api=env.api(),id=env.card.getAttribute('data-r002f-preview'),ready=env.classes.has('real-sky-preview-ready'),refined=env.classes.has('real-sky-composed'),slot=ready&&!refined&&id;
   const visible=ready&&!refined;
   // Evaluate the emitted selector/declaration subset against each independently
   // retained node. Neither the observation nor the CSS parser uses slot records.
   function computed(className,property,fallback){
    let result=fallback;
    for(const sheet of styles.filter(n=>n.isConnected)){
     for(const [,selectors,body] of sheet.textContent.matchAll(/([^{}]+)\{([^{}]*)\}/g)){
      for(const sel of selectors.split(',')){
       const m=/^\.c\.real-sky-preview-ready:not\(\.real-sky-composed\)\[data-r002f-preview="(\d+)"\] \.([\w-]+)$/.exec(sel);
       if(!m){
        const hidden=/^\.c:not\(\.real-sky-preview-ready\):not\(\.real-sky-composed\)\[data-r002f-withdrawn="(\d+)"\] \.([\w-]+)$/.exec(sel);
        assert(hidden,'unsupported generated selector '+sel);
        if(!ready&&!refined&&hidden[1]===env.card.getAttribute('data-r002f-withdrawn')&&hidden[2]===className&&body.startsWith(property+':'))result=body.slice(property.length+1).replace(/!important$/,'');
        continue;
       }
       if(m[1]===id&&m[2]===className&&ready&&!refined&&body.startsWith(property+':'))result=body.slice(property.length+1).replace(/!important$/,'');
      }
     }
    }
    return result;
   }
   const visibleNodes=(all,ordinary,prefix)=>all.filter(n=>n.isConnected&&(n.className===ordinary||n.className?.startsWith(prefix))&&computed(n.className,'visibility',n.style.visibility)==='visible');
   const backgrounds=visible?visibleNodes(env.canvases,'real-sky-preview','r002f-sky-'):[], discs=visible?visibleNodes(owner.s.canvases,'moon-detail-canvas','r002f-moon-'):[];
   assert(backgrounds.length<=1&&discs.length<=1,'competing visible owners');
   const bg=backgrounds[0],d=discs[0];
   return {id,visible,refined,ordinaryBackground:computed('real-sky-preview','visibility',env.canvases[0]?.style.visibility),ordinaryDisc:computed('moon-detail-canvas','visibility',owner.s.canvases[0]?.style.visibility),connectedSheets:styles.filter(n=>n.isConnected).length,bg:bg?.bytes?sha(bg.bytes):null,disc:d?.bytes?sha(d.bytes):null,
    ready,svgRouteExposed:!ready&&!refined&&env.classes.has('moon-ready'),mask:visible?computed('sun-cloud-mask','--native-sun-cloud-mask',env.card.style['--native-sun-cloud-mask']):null,
    frame:api?.frame?.raster.fixtureUtc??null,receipt:api?.state.utcMs??null,retained:!!api?.state.retained};
  }
  const context={vm,Buffer,structuredClone,owner,ctl,jobUtc:null,encode:encodeNativeFrame,cloudFrame:nativeCloudDisplayFrame,NativeForegroundCapture,NativeSolarMaskPublication,
   source:(original?sources[0]:outputs[0]).replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview')};
  h=vm.runInNewContext(harness+'\nhost({foregroundMs:0,skyMs:0,timeScale:1});',context);
  if(established){h.changeMask();h.present(20500,20500);}
  if(name.startsWith('post-')){
   const [_,kind,source,successor]=name.split('-'),before=observe(),api=env.api();ctl.defer=successor==='pending';
   const notify=()=>api.researchRevokeIfStale();
   if(successor==='cleanupFault'){h.s.window.SalahNativeSkyHost.reconcileClouds=()=>{throw Error('reconcile fault');};owner.api.clearFor=()=>{throw Error('detail cleanup fault');};}
   if(successor==='cleanupSuccessor'){owner.api.clearFor=()=>{owner.api.clear();h.present(41600,41600);h.present(62700,62700);throw Error('obsolete cleanup after valid successor');};}
   if(kind==='adoption'){
    if(source==='owner'){
     // The controlled projector and runtime admission arms share the same
     // publication signal. Drive the callback from an actual presenter adoption.
     const {moonFixture}=require('../r002f_a2_quarantine.cjs'),r=moonFixture(outputs[2],{initial:true});
     r.state.timeScale=1;r.workers[0].emit({kind:'ready'});
     r.w.SalahSkyPreview={researchRevokeIfStale(){owner.replace();notify();}};
     r.workers[0].emit(r.response());r.flush();
    }else owner.replace();
   }else if(kind==='geometry'){
    if(source==='owner'){
     const fn=range(outputs[5],'function renderMoon(){','// PROJECTED STARFIELD:');
     vm.runInNewContext(fn+';renderMoon();',{window:{SalahSkyPreview:api},simDate:()=>new Date(0),lat:1,lon:2,SIM:{},nativeLunarSnapshot:()=>({frac:.3,waxing:true,alt:2,H:0,up:1,x:1,y:1,transform:'x'}),$:()=>null,moonGeometryIdentity:()=>({}),renderMoonPBR:()=>owner.geo(),_pbrFailed:false,DEBUGMOON:false});
    }else owner.geo();
   }else if(kind==='cloud'){
    if(source==='owner'){
     const fn=range(outputs[5],'function publishCloudAuthority(','function rememberWeatherEffects(');
     const context={window:{SalahSkyPreview:api},currentWeatherTarget:()=>({generation:1,lat:1,lon:2}),skySceneIdentity:()=>'A',cloudAuthorityMode:()=>1,weatherTargetSame:()=>true};
     let publication={receipt:{revision:0,state:'old'}};Object.defineProperty(context,'_cloudPublication',{get:()=>publication,set:v=>{publication=v;ctl.cloud=v.receipt;}});
     vm.runInNewContext(fn+';publishCloudAuthority("eligible-published",null,"research transfer");',context);
    }else ctl.cloud++;
   }else if(kind==='weather')ctl.weather++;
   const afterProducer=observe();
   if(successor==='fault'||successor==='cleanupFault'){h.s.renderNativeBackgroundPreview=()=>{throw Error('successor unavailable');};}
   h.changeMask();h.present(20501,20501);
   return {name,before,afterProducer,after:observe(),pending:h.pendingCount,reason:h.state.reason};
  }
  const before=observe(),oldLunarReads=ctl.lunarReads;ctl.anchors.length=0;h.changeMask();armed=true;const target=established?41500:21000;h.present(target,target);const after=observe();
  const beforeReads=ctl.lunarReads;for(let i=0;i<5;i++)observe();return {name,before,events,after,solarAnchorReadModes:ctl.anchors,legacyReadsInUpdate:beforeReads-oldLunarReads,diagnosticExtraReads:ctl.lunarReads-beforeReads,reason:h.state.reason};
 }
 function runtimeAdmission(){
  const {moonFixture}=require('../r002f_a2_quarantine.cjs');
  const runtime=outputs[2].replace(range(outputs[2],'function researchGeometryKey(){','// Included inside the disposable Moon presenter.'),'function researchGeometryKey(){return "controlled footprint";}\n');
  const fixture=moonFixture(runtime,{initial:true});fixture.state.timeScale=1;fixture.workers[0].emit({kind:'ready'});fixture.workers[0].emit(fixture.response());fixture.flush();
  const rt=fixture.w.SalahMoonRuntime,lease=rt.researchMoonLease();
  const snapshot=()=>({writes:fixture.published,fallbacks:fixture.fallbacks,initial:fixture.initialRenders,jobs:fixture.jobs.size,requests:fixture.workers[0].sent.length});
  const before=snapshot(),current=lease.current();for(let i=0;i<6;i++){rt.observe();rt.researchMoonLease();lease.current();}
  const after=snapshot();
  const card={style:{getPropertyValue:()=> '10'},classList:{contains:()=>false}},sun={getBoundingClientRect:()=>({left:20,top:30,width:10,height:12})},view={getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
  const hctx={window:fixture.w,document:fixture.doc,simulationReady:()=>true,skySceneIdentity:()=>'A',selectedWeather:()=>null,q:new URLSearchParams(),$:q=>({'.c':card,'.sunbody':sun,'.suncorner':{},'.real-sky-preview':view})[q],getComputedStyle:()=>({opacity:'.75'}),simNow:()=>100,lat:1,lon:2,_runtimeGeneration:1,tz:'UTC',TIMESCALE:1,units:'c',LPOLL:0,isMotionReduced:()=>false,today:{},_pbrFailed:false};
  vm.runInNewContext(outputs[4],hctx);const hook=hctx.window.SalahNativeSkyHost;
  fixture.state.up=0;const count=fixture.published;const stagedAnchor=hook.capture(true,false).solarAnchor,stagedWrites=fixture.published-count;
  const ordinaryAnchor=hook.capture().solarAnchor,ordinaryWrites=fixture.published-count-stagedWrites;
  const actualAnchor={stagedAnchor,ordinaryAnchor,stagedWrites,ordinaryWrites};
  fixture.state.generation++;const revoked=lease.current(),denied=rt.researchMoonLease()===null;
  rt.invalidate('research successor');rt.request();const reused=lease.current(),replacement=rt.researchMoonLease()?.token??null;
  fixture.doc.hidden=true;fixture.state.paused=true;fixture.events.get('visibilitychange')();
  return {current,before,after,actualAnchor,revoked,denied,reused,oldToken:lease.token,replacement,hiddenLease:rt.researchMoonLease()===null};
 }
 function combinedCustody(omitBinding){
  const {moonFixture}=require('../r002f_a2_quarantine.cjs');
  let source=combine().outputs[2];
  source=source.replace(range(source,'function researchGeometryKey(){','// Included inside the disposable Moon presenter.'),'function researchGeometryKey(){return "controlled footprint";}\n');
  source=swap(source,' const originalGeometry=researchGeometryKey();',' window.inspectMaterial?.(material);\n const originalGeometry=researchGeometryKey();');
  if(omitBinding)source=swap(source,'researchMaterial.set(accepted,researchAdoptedMaterial);','if(!preparedHandover)researchMaterial.set(accepted,researchAdoptedMaterial);');
  const r=moonFixture(source,{initial:true},{});
  r.state.timeScale=1;r.workers[0].emit({kind:'ready'});
  const m=r.response();m.surfaceLinear[0]=.125;m.calendarLinear[0]=.0625;m.surfaceCoverage[0]=.75;r.workers[0].emit(m);r.flush();
  const rt=r.w.SalahMoonRuntime,seen=[];r.w.inspectMaterial=v=>seen.push({identity:v.identity,same:v.linear===m.surfaceLinear&&v.calendarLinear===m.calendarLinear&&v.coverage===m.surfaceCoverage,values:[v.linear[0],v.calendarLinear[0],v.coverage[0]]});
  const old=rt.researchMoonLease(),initial=r.initialRenders;
  r.doc.hidden=true;r.state.paused=true;r.events.get('visibilitychange')();const hidden=rt.researchMoonLease();
  r.advance(100);r.state.utcMs+=100;r.doc.hidden=false;r.state.paused=false;r.events.get('visibilitychange')();
  const restored=rt.researchMoonLease();
  return {hidden:!!hidden,oldCurrent:old.current(),originalToken:old.token,restoredToken:restored?.token??null,restoredCurrent:restored?.current()??false,reuses:rt.quarantineResearch.reuses,extraInitial:r.initialRenders-initial,seen};
 }
 const revocations=['post-adoption-poll-pending','post-cloud-poll-pending','post-geometry-poll-pending','post-weather-poll-pending','post-adoption-owner-pending','post-geometry-owner-pending','post-cloud-owner-pending','post-adoption-poll-fault','post-adoption-poll-cleanupFault','post-adoption-poll-cleanupSuccessor'];
 const names=['success','background-upload','detail-upload','style-attach','background-attach','detail-attach','before-select','after-select','cloud','weather','epoch','adoption','geometry','expiry','refined','nested','after-select-nested','after-select-inner-fails'];
 return {revocations:revocations.map(name=>arm(name,false,true)),combinedCustody:combinedCustody(false),missingCombinedBinding:combinedCustody(true),runtimeAdmission:runtimeAdmission(),actualOwnerControl:arm('existing-two-owner-failure',true),actualOwnerSuccess:arm('legacy-success',true),arms:names.map(n=>arm(n)),established:names.map(n=>arm(n,false,true)),owners:Object.fromEntries(transform().paths.map((p,i)=>[p,{baseline:sha(sources[i]),candidate:sha(outputs[i])}])),fixturePins:{nativePreview:sha(hostSource),moonProjection:sha(detailSource)},scope:'Source-controlled canvas bytes, CSS selector rules, acquired lunar material and geometry. No browser compositor or weather-hold result.'};
}
if(require.main===module){run().then(r=>process.stdout.write(JSON.stringify(r,null,2)+'\n')).catch(e=>{console.error(e);process.exitCode=1;});}
module.exports={run};
