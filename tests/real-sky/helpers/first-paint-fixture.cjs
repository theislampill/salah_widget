'use strict';
// Lifecycle source execution only. DOM/canvas, radiance, assets and scheduling
// are explicit doubles; shared native identity, lunar geometry and fences are real.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {nativeLunarOwner}=require('./native-lunar-test-source.cjs');
const source=(root,file)=>fs.readFileSync(path.join(root,file),'utf8').replace(/^import .*?;\s*$/gm,'').replace(/\bexport (?=(?:const|let|function|class|async function)\b)/g,'');
function fixture(root,{hidden=false,timing=true,observerSource=false,renderAdvance=0,moonError=false,initialProducer=null,hash='#lat=28.54&lon=-81.38&tz=America/New_York&simMoon=.92&simWax=0&simMoonAlt=40&simMoonH=0'}={}){
 let utc=Date.parse('2026-09-25T02:00:00Z'),mono=100,generation=0,rate=1,dpr=1,weather=null;
 const log=[],styles=new Map(),listeners=new Map(),windowListeners=new Map(),intervals=new Map();let serial=0;
 const add=(map,name,fn)=>{if(!map.has(name))map.set(name,new Set());map.get(name).add(fn);};
 class ClockDate extends Date{constructor(...a){super(...(a.length?a:[utc]));}static now(){return utc;}}
 const style=()=>({visibility:'hidden',setProperty(){},removeProperty(){}});
 const classes=new Set();const card={style:style(),classList:{add(...a){a.forEach(x=>classes.add(x));},remove(...a){a.forEach(x=>classes.delete(x));},contains:x=>classes.has(x)},prepend(){},getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
 const canvas=()=>({width:0,height:0,style:style(),setAttribute(){},remove(){},getContext:()=>({putImageData(){},drawImage(){},getImageData:()=>({data:new Uint8ClampedArray(325*530*4)})}),toDataURL:()=> 'data:image/png;base64,bGlmZWN5Y2xlLWZpeHR1cmU='});
 const document={hidden,readyState:'loading',baseURI:'https://fixture.invalid/index.html',currentScript:{src:'https://fixture.invalid/moon/moon-host.js'},head:{append(el){styles.set(el.id,el);log.push('css-published');}},createElement(tag){if(tag==='canvas')return canvas();return {id:'',textContent:'',remove(){styles.delete(this.id);log.push('css-removed');}};},querySelector(sel){if(sel==='#native-first-paint')return styles.get('native-first-paint')??null;if(sel==='.c')return card;if(sel==='.mphoto')return {getBoundingClientRect(){const g=context.SalahFirstPaint?.moon?.geometry;return {width:g?.w??108,height:g?.h??108};}};return null;},addEventListener:(n,f)=>add(listeners,n,f),removeEventListener:(n,f)=>listeners.get(n)?.delete(f)};
 const context={document,Date:ClockDate,performance:{now:()=>mono,timeOrigin:1000000},location:{hash,protocol:'https:'},navigator:{language:'en-US'},devicePixelRatio:dpr,matchMedia:()=>({matches:false}),URL,URLSearchParams,structuredClone,TextEncoder,TextDecoder,Uint8Array,Uint8ClampedArray,Float64Array,Float32Array,ImageData:class{constructor(data,width,height){Object.assign(this,{data,width,height});}},console,requestAnimationFrame:()=>++serial,cancelAnimationFrame(){},setInterval(fn){const id=++serial;intervals.set(id,fn);return id;},clearInterval:id=>intervals.delete(id),setTimeout:()=>++serial,clearTimeout(){},addEventListener:(n,f)=>add(windowListeners,n,f),getComputedStyle:()=>({opacity:'1'})};
 context.window=context;context.localStorage={getItem:()=>null,setItem(){},removeItem(){}};
 context.MOON_DEFAULT_PROFILE={schema:'lunar-presentation/5',profile_id:'calendar-neutral-v5-01',mode:'calendar',exposure:2.9195482731525044,lift:.003,knee:5.388411226362526e-6,colour_basis:'linear-sRGB',gamut:'luminance-preserving-neutral-axis'};
 context.MOON_WORKER_SOURCE=null;context.MOON_WORKER_PIN={bytes:1,sha256:'unused'};
 context.startMoonDetail=()=>({dispose(){},clear(){},adopt(){},compose(){},available:true});
 context.prefixSurface=x=>x;context.boxSurface=()=>[.2,.2,.2,1];context.sampleField=()=>[.001,.001,.001];context.joinLunarPixel=()=>[.2,.2,.2];
 context.encodeNativeFrame=linear=>new Uint8ClampedArray(linear.length/3*4);
 context.blendCalendarBytes=upper=>upper;
 context.SalahMoonInitial={render(scene){log.push('lunar-render');if(moonError)throw Error('fixture lunar render failure');return {kind:'initial',scene:{...scene,size:8},surfaceSize:8,surfaceExtent:1.08,surfaceLinear:new Float32Array(192),surfaceCoverage:new Float32Array(64).fill(1),calendarLinear:new Float32Array(192),rgba:new Uint8ClampedArray(256),calendarRgba:new Uint8ClampedArray(256),width:8,height:8,physicalIdentity:'lifecycle-fixture',profileIdentity:JSON.stringify(scene.profile),diagnostics:{quality:{status:'initial-v5'},totalMs:0}};}};
 if(initialProducer)context.SalahMoonInitial={...initialProducer,render(scene){log.push('lunar-render');return initialProducer.render(scene);}};
 context.SalahStarBootstrap={render:()=>({})};context.joinNativeStarPreview=p=>p;
 context.NativeForegroundCapture=class{bottom(){return 0;}capture(){return {cloudRGBA:new Float64Array(325*530*4),moonRGBA:new Float64Array(325*530*4),native:{}};}prepareSolarMask(){return 1;}};
 context.nativeForegroundRows=()=>530;context.nativeCloudDisplayFrame=bytes=>bytes;context.nativeStarPreviewRegion=()=>new Uint8ClampedArray(325*530*4);
 context.NativeStarPreview={create:async()=>context.SalahStarBootstrap};
 vm.createContext(context);
 const evaluate=s=>vm.runInContext(s,context,{timeout:5000});
 evaluate(source(root,'config.js'));
 evaluate(source(root,'real-sky/native-contract.mjs'));
 evaluate(nativeLunarOwner(root));
 evaluate(source(root,'moon/src/moon-precision.mjs'));
 context.renderNativeBackgroundPreview=snapshot=>{log.push('background-render');utc+=renderAdvance;mono+=renderAdvance;const job=context.nativeJob(snapshot,true);return {job,utcMs:snapshot.utcMs,quality:'lifecycle-fixture',raster:{width:325,height:530,linear:new Float64Array(325*530*3),skyBackgroundLinear:new Float64Array(325*530*3),stellarLinear:new Float64Array(325*530*3),diffusePhysicalLinear:new Float64Array(325*530*3),effectiveExposure:10.6,physicalState:{sun:{altDeg:-35}},starPreview:{fixture:true}},diagnostics:{}};};
 evaluate(source(root,'moon/src/moon-first-paint.mjs'));
 evaluate(source(root,'real-sky/native-preview-host.mjs'));
 evaluate(source(root,'real-sky/native-first-paint.mjs'));
 evaluate(source(root,'moon/src/moon-native.mjs'));
 context.SalahMoonHead={compose(preview,snapshot,sim,encode){return context.composeNativeHeadMoon(preview,snapshot,sim,{snapshot:context.nativeLunarSnapshot,presentation:context.nativeLunarPresentation,scene:context.nativeCalendarMoonScene},{initial:context.SalahMoonInitial,profile:context.MOON_DEFAULT_PROFILE,phaseQuantum:context.phaseQuantum,canonicalFraction:context.canonicalFraction,prefixSurface:context.prefixSurface,boxSurface:context.boxSurface,sampleField:context.sampleField,joinLunarPixel:context.joinLunarPixel,encode});},backgroundRule:context.nativeHeadMoonBackgroundRule};
 let admissionSerial=0,firstAdmission=null;const admitted=new Map(),events=[];
 if(observerSource){context.crypto=require('node:crypto').webcrypto;context.parent=context;evaluate(fs.readFileSync((fs.existsSync(path.join(root,'real-sky/native-startup-timing.js'))?path.join(root,'real-sky/native-startup-timing.js'):path.join(__dirname,'../fixtures/startup-timing-source.js')),'utf8'));}
 else if(timing)context.SalahStartupTiming={admit(snapshot,source,configIdentity){const key=JSON.stringify([snapshot.sceneIdentity,snapshot.generation,snapshot.dpr,configIdentity]);let id=admitted.get(key);if(!id){id='fixture-admission-'+(++admissionSerial);admitted.set(key,id);}const event={id,at:mono,source,configIdentity,snapshot:structuredClone(snapshot)};firstAdmission??=event;log.push('admit-'+source);return id;},stage(kind,details){events.push({kind,at:mono,...structuredClone(details)});log.push(kind);return 'fixture-event-'+events.length;}};
 const facadeBeforePrepare=context.SalahFirstPaintLifecycle;context.prepareNativeFirstPaint();const originalSnapshot=structuredClone(context.SalahFirstPaint?.snapshot);
 function nativeSnapshot(){const c=context.SalahConfig.resolve(context.location.hash).cfg;return {...structuredClone(originalSnapshot),utcMs:utc,lat:c.lat,lon:c.lon,tz:c.tz,units:c.units,lp:c.lp||0,generation,sceneIdentity:[c.lat,c.lon,c.tz||'America/New_York','wall'].join('|'),dpr,weather,timeScale:rate,paused:document.hidden};}
 function core(){context.SalahNativeSkyHost={capture:nativeSnapshot};context.SalahMoonHost={capture(){const s=nativeSnapshot(),q=new URLSearchParams(context.location.hash.slice(1)),moon=context.nativeLunarSnapshot(new ClockDate(s.utcMs),s.lat,s.lon,{moon:q.get('simMoon'),wax:q.get('simWax'),moonAlt:q.get('simMoonAlt'),moonH:q.get('simMoonH')});return {...s,fraction:moon.frac,waxing:moon.waxing,up:moon.up,presentationReady:true,initialWarranted:true,maximumPresentationRatio:1};},publish(){log.push('native-published');},fallback(){}};}
 return {context,log,styles,events,facadeBeforePrepare,hashListenerCount:()=>windowListeners.get('hashchange')?.size??0,firstAdmission:()=>firstAdmission,originalSnapshot,nativeSnapshot,core,advance(ms){utc+=ms;mono+=ms;},jump(ms){utc+=ms;},setDpr(v){dpr=v;context.devicePixelRatio=v;},setGeneration(v){generation=v;},setRate(v){rate=v;},setWeather(v){weather=v;},hash(v){context.location.hash=v;for(const fn of windowListeners.get('hashchange')||[])fn();},hidden(v){document.hidden=v;for(const fn of listeners.get('visibilitychange')||[])fn();},poll(){context.SalahMoonRuntime.request();},preview(){context.startNativeSkyPreview();return context.SalahSkyPreview;},intervalCount:()=>intervals.size};
}
module.exports={fixture};
