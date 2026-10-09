import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
const built=fs.readFileSync(new URL('../../index.html',import.meta.url),'utf8');

test('prayer-name fitting snapshots one unchanged arc transform per fit',()=>{
 const code=source.slice(source.indexOf('function fitCn('),source.indexOf('// PROCEDURAL BRANCHING LIGHTNING'));
 let matrixReads=0,pointReads=0;
 const styles={fontSize:'30px',top:'100px',marginBottom:'0px',fontFamily:'serif'},cn={style:{...styles},textContent:'Isha'},nt={};
 const matrix={a:1,b:0,c:0,d:1,e:8,f:8};
 const rail={getTotalLength:()=>200,getPointAtLength:length=>{pointReads++;return {x:20+length*1.4,y:200-100*Math.sin(length*Math.PI/200)};},getScreenCTM(){matrixReads++;return matrix;},ownerSVGElement:{createSVGPoint:()=>({matrixTransform(m){return {x:this.x*m.a+m.e,y:this.y*m.d+m.f};}})}};
 const elements={'.cn':cn,'.nt':nt,'.arc .rail':rail,'.arc .horizon':{getBoundingClientRect:()=>({top:200})},'.bar':{getBoundingClientRect:()=>({top:260})}};
 const run=code=>{
  cn.style={...styles};matrixReads=0;pointReads=0;
  const scope={_cnFit:'',cnFontSignature:()=>'',Math,isFinite,parseFloat,$:s=>elements[s],getComputedStyle:el=>el.style,
   document:{querySelector:s=>elements[s],fonts:{check:()=>true},createRange:()=>({selectNodeContents(el){this.el=el;},getBoundingClientRect(){return this.el===cn?{left:120,right:200,width:80,bottom:190}:{top:200,bottom:250};}}),createElement:()=>({getContext:()=>({measureText:()=>({actualBoundingBoxAscent:21,fontBoundingBoxDescent:7.2})})})}};
  vm.createContext(scope);vm.runInContext(code,scope);scope.fitCn({currentKey:'Isha',sunrise:400,sunset:1100});return {...cn.style};
 };
 const before=run(code.replace('s.matrixTransform(railMatrix)','s.matrixTransform(rail.getScreenCTM())'));
 const after=run(code);assert.deepEqual(after,before,'fitted geometry must remain identical');assert.equal(pointReads,201,'retain the complete accepted path sampling');
 assert.equal(matrixReads,1,'201 identical layout-transform queries must not occupy the first scene');
});

test('native civil projection reuses only the formatter, never UTC or time-zone results',()=>{
 const body=source.slice(source.indexOf('function partsInTz('),source.indexOf('// Strict Gregorian coordinate'));
 let constructions=0;
 const scope={tz:'America/New_York',Date,pad:n=>String(n).padStart(2,'0'),_partsFormatter:null,_partsFormatterZone:null,
  Intl:{DateTimeFormat:function(...args){constructions++;return new Intl.DateTimeFormat(...args);}}};
 vm.createContext(scope);vm.runInContext(body,scope);
 for(const zone of ['America/New_York','Asia/Kathmandu','America/New_York']){
  scope.tz=zone;
  for(const stamp of ['2026-11-01T05:59:00Z','2026-11-01T06:01:00Z','2026-03-08T06:59:00Z','2026-03-08T07:01:00Z']){
   const ms=Date.parse(stamp),p={};for(const x of new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).formatToParts(new Date(ms)))p[x.type]=x.value;
   const actual=scope.partsInTz(ms);assert.deepEqual(JSON.parse(JSON.stringify(actual)),{y:+p.year,mo:+p.month,d:+p.day,h:+p.hour%24,mi:+p.minute,s:+p.second,dateStr:`${p.day}-${p.month}-${p.year}`});
  }
 }
 assert.equal(constructions,3,'formatter construction must not repeat for every startup capture/paint query');
});
test('optional remote font CSS cannot block the native bootstrap',()=>{
 const tag=source.match(/<link[^>]*href="https:\/\/fonts.googleapis.com\/css2[^>]*>/)[0];
 assert.match(tag,/media="print"/,'unavailable remote typography must not stall accepted celestial inputs');
 const handler=tag.match(/onload="([^"]+)"/)?.[1];assert.ok(handler);
 const link={media:'print'};vm.runInNewContext('(function(){'+handler+'}).call(link)',{link});assert.equal(link.media,'all','ordinary styles still apply once available');
});
test('cached fallback fitting responds once to relevant native font completion',()=>{
 const code=source.slice(source.indexOf('let _cnFit="";'),source.indexOf('// PROCEDURAL BRANCHING LIGHTNING'));
 let measurements=0;const listeners=new Map(),cn={style:{top:'100px',marginBottom:'0px',fontFamily:'Fraunces'},textContent:'Forenoon'},nt={};
 const rail={getTotalLength:()=>200,getPointAtLength:l=>({x:20+l*1.4,y:200-100*Math.sin(l*Math.PI/200)}),getScreenCTM:()=>({}),ownerSVGElement:{createSVGPoint:()=>({matrixTransform(){return {x:this.x,y:this.y};}})}};
 const elements={'.cn':cn,'.nt':nt,'.arc .rail':rail,'.arc .horizon':{getBoundingClientRect:()=>({top:200})},'.bar':{getBoundingClientRect:()=>({top:260})}};
 // Native check() may report true before an absent family is registered. The
 // browser regression covers the real CSS/font transport; this checks caching.
 const scope={_renderDirty:false,Math,isFinite,parseFloat,$:s=>elements[s],getComputedStyle:e=>e.style,
  document:{fonts:{check:()=>true,addEventListener:(name,fn)=>listeners.set(name,fn)},querySelector:s=>elements[s],
   createRange:()=>({selectNodeContents(e){this.e=e;},getBoundingClientRect(){return this.e===cn?{left:110,right:210,width:100,bottom:190}:{top:200,bottom:250};}}),
   createElement:()=>({getContext:()=>({measureText(){measurements++;return {actualBoundingBoxAscent:21,fontBoundingBoxDescent:7.2};}})})}};
 vm.createContext(scope);vm.runInContext(code,scope);
 const fit=()=>scope.fitCn({currentKey:'Forenoon',sunrise:400,sunset:1100});
 fit();fit();assert.equal(measurements,1,'fallback remains usable and cached while CSS is absent');
 const finish=(type,family)=>listeners.get(type)?.({fontfaces:[{family,status:type==='loadingdone'?'loaded':'error'}]});
 finish('loadingdone','"Fraunces"');fit();assert.equal(measurements,2,'real face arrival invalidates stale fallback metrics');
 assert.equal(scope._renderDirty,true,'arrival schedules a native render even at frozen preview time');
 fit();fit();assert.equal(measurements,2,'settled typography does not refit continuously');
 finish('loadingdone','Unrelated');fit();assert.equal(measurements,2,'unrelated font does not invalidate this geometry');
 finish('loadingerror','Inter');fit();fit();assert.equal(measurements,3,'terminal failure has one stable fallback fit');
});
test('individual font arrival refits before the other family settles',async()=>{
 const code=source.slice(source.indexOf('let _cnFit="";'),source.indexOf('// PROCEDURAL BRANCHING LIGHTNING'));
 let measurements=0,releaseFraunces,rejectInter;const listeners=new Map();
 const faces=[{family:'Fraunces',status:'loading',loaded:new Promise(r=>releaseFraunces=r)},
  {family:'Inter',status:'loading',loaded:new Promise((_,r)=>rejectInter=r)}];
 const cn={style:{top:'100px',marginBottom:'0px',fontFamily:'Fraunces'},textContent:'Forenoon'},nt={};
 const rail={getTotalLength:()=>200,getPointAtLength:l=>({x:20+l*1.4,y:200-100*Math.sin(l*Math.PI/200)}),getScreenCTM:()=>({}),ownerSVGElement:{createSVGPoint:()=>({matrixTransform(){return {x:this.x,y:this.y};}})}};
 const elements={'.cn':cn,'.nt':nt,'.arc .rail':rail,'.arc .horizon':{getBoundingClientRect:()=>({top:200})},'.bar':{getBoundingClientRect:()=>({top:260})}};
 const fonts={status:'loading',check:()=>true,[Symbol.iterator]:()=>faces[Symbol.iterator](),addEventListener:(name,fn)=>listeners.set(name,fn)};
 const scope={_renderDirty:false,Math,isFinite,parseFloat,$:s=>elements[s],getComputedStyle:e=>e.style,
  document:{fonts,querySelector:s=>elements[s],createRange:()=>({selectNodeContents(e){this.e=e;},getBoundingClientRect(){return this.e===cn?{left:110,right:210,width:100,bottom:190}:{top:200,bottom:250};}}),
   createElement:()=>({getContext:()=>({measureText(){measurements++;return {actualBoundingBoxAscent:21,fontBoundingBoxDescent:7.2};}})})}};
 vm.createContext(scope);vm.runInContext(code,scope);const fit=()=>scope.fitCn({currentKey:'Forenoon',sunrise:400,sunset:1100});
 fit();fit();assert.equal(measurements,1);
 faces[0].status='loaded';releaseFraunces(faces[0]);await Promise.resolve();await Promise.resolve();
 assert.equal(scope._renderDirty,true,'individual Fraunces completion must wake a frozen native preview while Inter stays pending');
 fit();fit();assert.equal(measurements,2,'no set-wide event or forced cache clear is needed');
 scope._renderDirty=false;faces[1].status='error';rejectInter(Error('font permanently unavailable'));await Promise.resolve();await Promise.resolve();
 assert.equal(scope._renderDirty,true);fit();fit();assert.equal(measurements,3,'terminal fallback stabilizes after its own invalidation');
});

test('V5 ownership prevents discarded legacy-map GPU readback at startup',()=>{
 const start=source.indexOf('(function loadMoonMaps(){'),end=source.indexOf('})();',start)+5;
 let readbacks=0;
 const scope={window:{SalahMoonRuntime:{}},MOON_ALBEDO:'albedo',MOON_NORMAL:'normal',_MTW:160,_MTH:80,_pbrPending:null,
  Image:class{set src(v){this.onload();}},document:{createElement:()=>({getContext:()=>({drawImage(){},getImageData(){readbacks++;return {data:[]};}})})},
  updateSkySurface(){},renderMoonCalendarFallback(){},_mAlb:null,_mNrm:null,_pbrReady:false,_pbrFailed:false,_renderDirty:false};
 vm.runInNewContext(source.slice(start,end),scope);assert.equal(readbacks,0,'unconsumed legacy texture must not stall the V5 first scene');
});
test('initial foreground is composed after native geometry and only once before provider wait',async()=>{
 const boot=built.slice(built.indexOf('async function boot(){'),built.indexOf('// SINGLE rAF render clock'));
 let resolve;const provider=new Promise(r=>resolve=r),events=[],frames=[],tasks=[];
 const scope={window:{SalahStartSkyPreview(){events.push('preview');scope.window.SalahSkyPreview={update(){events.push('preview-update');}};},SalahNativeSkyHost:{}},_runtimeGeneration:0,_cfgMode:'local',QA:false,lat:1,lon:2,
  enableSettingsAffordance(){},beginSkyScene(){events.push('clear');},simulationReady:()=>true,buildSceneOnce(){events.push('geometry');},renderMoon(){events.push('moon');},
  startWeather(deferNetwork){if(!deferNetwork)events.push('weather-fetch');},fetchWeather(){events.push('weather-fetch');},fetchRadar(){},render(){events.push('native');},loadPrayerData(){events.push('prayer');return provider;},startRenderLoop(){events.push('loop');},requestAnimationFrame:cb=>frames.push(cb),MessageChannel:class{constructor(){this.port1={close(){}};this.port2={close(){},postMessage:()=>tasks.push(()=>this.port1.onmessage())};}}};
 vm.createContext(scope);vm.runInContext(boot,scope);const done=scope.boot();
 assert.ok(events.indexOf('preview')>events.indexOf('native'),'pre-geometry foreground is discarded by the first native scene');
 assert.equal(events.filter(x=>x==='preview'||x==='preview-update').length,1,'one foreground before first yield');
 assert.equal(events.includes('prayer'),false,'synchronous cached prayer fitting cannot occupy the first celestial paint opportunity');
 assert.equal(events.includes('weather-fetch'),false,'a fast observation response must not invalidate the first composed sky before it can paint; retained weather is already loaded');
 frames.shift()();assert.equal(events.includes('prayer'),false);frames.shift()();await Promise.resolve();
 assert.equal(events.includes('prayer'),false,'the promise continuation must not fit prayers inside the rendering callback');
 tasks.shift()();await Promise.resolve();
 assert.equal(events.includes('prayer'),true,'prayer acquisition proceeds after the first rendering opportunity, without a timer or ready gate');
 assert.equal(events.filter(x=>x==='weather-fetch').length,1);
 resolve();await done;assert.equal(events.at(-1),'loop');
});
