Read-only review control for Root to retain as a source-bound test. It joins the actual native lifecycle, celestial publication and boot functions to the existing Moon host fixture. Art/provider callbacks remain doubles; no browser or pixel claim. The fixed absolute repo path may be replaced by the destination test's normal repository-root resolver.

The original attempt omitted the global SalahConfig alias in the unresolved-location fixture and ended with an openSettings ReferenceError. It is superseded by the complete control below, which checks that coarseDetect was actually called and execution is paused at its unresolved promise.

```javascript
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const repo=String.raw`<candidate>`;
const sourceFile=path.join(repo,'src/native/index.html');
const hostFile=path.join(repo,'moon/tests/host.test.cjs');
const html=fs.readFileSync(sourceFile,'utf8'),host=fs.readFileSync(hostFile,'utf8');
const fixtureEnd=host.indexOf("test('initial document");
assert.ok(fixtureEnd>0,'host fixture boundary');
const returnPrefix='return {w,workers,state,detail,nodes,events,jobs,flush,frame,request,response,head,doc,';
const fixture=host.slice(0,fixtureEnd);
assert.equal(fixture.split(returnPrefix).length,2,'one fixture return boundary');
const rig=Function('require','__dirname',
 fixture.replace(returnPrefix,'return {context:c,w,workers,state,detail,nodes,events,jobs,flush,frame,request,response,head,doc,')+'\nreturn rig;'
)(require,path.join(repo,'moon/tests'));
function section(start,end){
 const a=html.indexOf(start),b=html.indexOf(end,a+start.length);
 assert.ok(a>=0&&b>a,'actual source section '+start);return html.slice(a,b);
}
const lifecycle=section('let _skySceneKey=null','// A current V5 receiver presentation');
const celestial=section('function paintCelestialWithoutTimetable(){','function atmosphere(');
const boot=section('async function boot(){','// SINGLE rAF render clock');
function setup(){
 const r=rig({initial:true,deferWorker:true}),c=r.context;r.head();
 const card={classList:{add(){},remove(){}},style:{setProperty(){}}};
 Object.assign(c,{
  _runtimeGeneration:0,_cfgMode:'bare',QA:false,lat:28.5,lon:-81.4,_needsDetect:false,
  $:()=>card,cloudState:{},_colDens:null,_cloudCtx:null,_cloudCv:null,
  updateSkySurface(){},skySceneIdentity:()=>r.state.sceneIdentity,
  nowParts:()=>({h:2,mi:0,s:0}),moonGeometryObservation:()=>({fresh:true}),
  renderMoon(){},projectStars(){},simDate:()=>new Date(),
  lunarPresentation:()=>({moonShow:1,moonlight:1}),simulationReady:()=>true,
  buildSceneOnce(){},startWeather(){},enableSettingsAffordance(){},
  openSettings(){},startRenderLoop(){}
 });
 r.w.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:-20}})};
 r.w.SalahStartSkyPreview=()=>{};
 vm.runInContext(lifecycle+'\n'+celestial+'\n'+boot,c);
 c.render=()=>vm.runInContext('paintCelestialWithoutTimetable()',c);
 return r;
}
const cases=[];
{
 const r=setup();vm.runInContext('boot()',r.context);
 const value={renders:r.initialRenders,headHandoff:r.w.SalahMoonRuntime.state.firstInitial?.headHandoff,
  flag:vm.runInContext('_skyInitialDocument',r.context),retained:r.w.SalahFirstPaint.moon.result!==null,epoch:r.w.SalahMoonRuntime.state.epoch};
 cases.push({case:'actual known boot before first yield',value,passed:value.renders===1&&value.headHandoff===true&&!value.flag&&!value.retained&&value.epoch===2});
}
{
 const r=setup();let acquisitions=0;r.context.lat=null;r.context._needsDetect=true;
 const config={coarseDetect:()=>{acquisitions++;return new Promise(()=>{});}};
 r.w.SalahConfig=config;r.context.SalahConfig=config;
 vm.runInContext('boot()',r.context);
 const value={acquisitions,flag:vm.runInContext('_skyInitialDocument',r.context),retained:r.w.SalahFirstPaint.moon.result!==null,renders:r.initialRenders};
 cases.push({case:'actual unresolved boot at acquisition await',value,passed:value.acquisitions===1&&!value.flag&&!value.retained&&value.renders===1});
}
{
 const r=setup();r.context.simulationReady=()=>false;vm.runInContext('boot()',r.context);
 const value={flag:vm.runInContext('_skyInitialDocument',r.context),retained:r.w.SalahFirstPaint.moon.result!==null};
 cases.push({case:'actual invalid initial clock return',value,passed:!value.flag&&!value.retained});
}
{
 const r=setup();vm.runInContext('beginSkyScene();paintCelestialWithoutTimetable()',r.context);
 const value={renders:r.initialRenders,headHandoff:r.w.SalahMoonRuntime.state.firstInitial?.headHandoff,flag:vm.runInContext('_skyInitialDocument',r.context)};
 cases.push({case:'actual default scene invalidation',value,passed:value.renders===2&&value.headHandoff===false&&!value.flag});
}
for(const condition of ['paused','invalid']){
 const r=rig({initial:true,deferWorker:true});r.head();
 if(condition==='paused')r.state.paused=true;else r.state.utcMs=NaN;
 r.w.SalahMoonRuntime.request();
 if(condition==='paused')r.state.paused=false;else r.state.utcMs=1000;
 r.w.SalahMoonRuntime.request();
 const value={renders:r.initialRenders,headHandoff:r.w.SalahMoonRuntime.state.firstInitial?.headHandoff,retained:r.w.SalahFirstPaint.moon.result!==null};
 cases.push({case:condition+' return before first acceptance',value,passed:value.renders===2&&value.headHandoff===false&&!value.retained});
}
console.log(JSON.stringify({allPassed:cases.every(x=>x.passed),cases},null,2));
if(cases.some(x=>!x.passed))process.exitCode=1;

```

