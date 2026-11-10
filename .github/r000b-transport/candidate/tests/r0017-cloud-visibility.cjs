/* R0017: execute the actual cloud/orientation smoke cells against controlled DOM/readout
 * boundaries. No product observer, flags, renderer, browser or motion proof. */
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const root=path.resolve(process.argv.slice(2).find(a=>!a.startsWith("--"))||path.join(__dirname,".."));
const source=fs.readFileSync(path.join(root,"tests/smoke.html"),"utf8");
const driver='(async()=>{try{await run();}catch(e){line("fail","harness error: "+e.message);}finally{finalize();}})();';
function once(text,from,to){assert.equal(text.split(from).length,2,"source anchor must be unique");return text.replace(from,to);}
function helperMutation(text,name,from,to){
  const start=text.indexOf("async function "+name+"("),end=text.indexOf("\n}\n",start)+3;
  assert.ok(start>=0&&end>start,"owned helper boundary must exist");
  return text.slice(0,start)+once(text.slice(start,end),from,to)+text.slice(end);
}
function bothPresentationHelpers(text,from,to){
  return ["cloudScene","withCloudFrameInView"].reduce((body,name)=>helperMutation(body,name,from,to),text);
}
function fixture(text=source,options={}){
  let tick=0,next=0,scheduled=false,paused=true,rawStyle=options.absentStyle?null:"position:absolute;left:-9999px;top:0;width:325px;height:530px;border:0;outline: 1px solid red";
  const originalStyle=rawStyle,timers=new Map(),paints=[],checks=[],styles=[],navigations=[],decodes=[];
  let navigatedAt=0,stateReads=0,sceneReads=0;
  const surfaceSource=options.surfaceSource||"refined-terrain",publishedURI="data:image/png;base64,"+"A".repeat(64);
  function drain(){if(scheduled)return;scheduled=true;setImmediate(()=>{scheduled=false;
    const pending=[...timers].sort((a,b)=>a[1].due-b[1].due||a[0]-b[0])[0];
    if(pending){timers.delete(pending[0]);tick=pending[1].due;pending[1].fn();}if(timers.size)drain();});}
  function later(fn,ms){const id=++next;timers.set(id,{due:tick+ms,fn:()=>{if(ms===350&&options.afterElapsed)options.afterElapsed(state);fn();}});drain();return id;}
  const card={getBoundingClientRect:()=>({left:0,top:0,right:325,bottom:530,width:325,height:530}),classList:{contains(name){if(name==="paused")return paused;if(options.orientation&&["real-sky-composed","moon-ready"].includes(name))return true;throw Error("Unexpected card class "+name);}}};
  const photo={getAttribute(name){assert.equal(name,"href");return options.shortHref?"short":options.wrongPublication?publishedURI+"stale":publishedURI;}};
  const foreground={isConnected:true,width:2,height:2,getBoundingClientRect:()=>({left:20,top:20,right:22,bottom:22,width:2,height:2}),
    getContext:()=>({getImageData:()=>({data:Uint8ClampedArray.from([30,30,30,options.opaqueAlpha??255,30,30,30,options.opaqueAlpha??255,30,30,30,options.opaqueAlpha??255,30,30,30,options.opaqueAlpha??255])})})};
  const backing={width:300,height:300,toDataURL:()=>publishedURI};
  const doc={visibilityState:"visible",querySelector(selector){if(selector===".c")return card;if(selector===".cloudcanvas")return canvas;
    if(options.orientation&&selector===".mphoto")return photo;if(options.orientation&&selector===".mfeatures")return {getAttribute:()=>null};
    if(options.orientation&&selector===".moon-detail-canvas")return foreground;
    throw Error("Unexpected child selector "+selector);}};
  const ww={document:doc,location:{hash:"#owned-cloud-scene"},performance:{now:()=>tick},
    __widgetFixture:{run:null,attempt:1,documentId:"00000000-0000-4000-8000-000000000001",hash:"owned-cloud-scene",sourceSha256:"a".repeat(64),state:"ready"},
    qaState(){return {wxTruth:{cloudFieldSeed:123},cache:{prayerLoaded:true},render:{currentKey:"Dhuhr",nextKey:"Asr"},
      moonTruth:{surface:{identity:options.wrongIdentity?"stale-surface":"controlled-surface-"+ww.__widgetFixture.attempt,visibleSource:surfaceSource,legacyVisible:false}}};},simNow(){return 42;},
    paintClouds(t){const r=fr.getBoundingClientRect();assert.ok(r.right>0&&r.left<1280&&r.bottom>0&&r.top<900,"sampling requires an in-view iframe");
      assert.equal(paused,false,"sampling requires native paused readout to clear");assert.equal(ww.document.visibilityState,"visible");assert.equal(t,42/1000);paints.push(tick);if(options.paintThrows)throw Error("controlled paint failure");}};
  ww.__smokeWeather={identity:()=>ww.__widgetFixture,read(){}};
  ww.getComputedStyle=()=>({visibility:options.hiddenForeground?"hidden":"visible",display:"block",opacity:"1"});ww.innerWidth=325;ww.innerHeight=530;
  ww.SalahMoonHost={capture(){sceneReads++;return {generation:1,sceneIdentity:options.staleScene?"scene-"+sceneReads:"controlled-scene",paused,
    utcMs:1800000000000,fraction:.3,waxing:true,dpr:1};}};
  ww.SalahMoonDetail={available:!options.unreadySurface,get state(){return {visible:!options.hiddenForeground,renders:1};}};
  ww.SalahMoonRuntime={surface:()=>options.unreadySurface?null:backing,get state(){stateReads++;return {current:!options.unreadySurface&&tick-navigatedAt>=(options.currentAfter||0),
    epoch:options.staleEpoch?stateReads:1,generation:options.staleGeneration?2:1,
    accepted:{identity:"controlled-surface-"+ww.__widgetFixture.attempt,scene:{outSize:300}},visibleSource:surfaceSource,
    phasePrecision:{targetPositionErrorBound:options.badGeometry?.05:0,maximumPositionErrorDevicePixels:.0416}};}};
  // Literal alpha samples exercise the existing checksum/assertion consumer only.
  const canvas={width:2,height:1,getContext(kind){assert.equal(kind,"2d");return {getImageData(){return {data:Uint8ClampedArray.from([0,0,0,200,0,0,0,paints.length===1?100:120])};}};}};
  const fr={contentWindow:ww,isConnected:true,
    getAttribute(name){assert.equal(name,"style");return rawStyle;},
    setAttribute(name,value){assert.equal(name,"style");styles.push(value);rawStyle=value;},
    removeAttribute(name){assert.equal(name,"style");styles.push(null);rawStyle=null;},
    getBoundingClientRect(){const property=(name,fallback)=>{const m=(rawStyle||"").match(new RegExp("(?:^|;)\\s*"+name+":\\s*(-?[0-9]+)px"));return m?+m[1]:fallback;};
      const left=property("left",-9999),top=property("top",0);return {left,top,right:left+325,bottom:top+530,width:325,height:530};}};
  const elements={w:fr,out:{appendChild(){}},sum:{}};
  const document={visibilityState:"visible",getElementById(name){return elements[name];},createElement(name){
    if(options.orientation&&name==="canvas")return {getContext(){return {drawImage(){},getImageData(){
      // Four literal pixels exercise the unchanged actual moonLitSide consumer.
      const wax=new URLSearchParams(ww.location.hash.slice(1)).get("simWax")==="1",right=options.wrongSide?!wax:wax;
      const left=right?30:220,r=right?220:30;
      return {data:Uint8ClampedArray.from([left,left,left,255,r,r,r,255,left,left,left,255,r,r,r,255])};
    }};}};
    return {};}};fr.ownerDocument=document;
  class Clock extends Date{static now(){return 1800000000000+tick;}}
  class ControlledImage{constructor(){this.width=2;}set src(value){decodes.push({tick,value});later(()=>this.onload(),0);}}
  const ctx=vm.createContext({URLSearchParams,URL,Date:options.orientation?Clock:Date,Image:ControlledImage,Math,console,document,location:{search:""},innerWidth:1280,innerHeight:900,
    performance:{now:()=>tick},setTimeout:later,clearTimeout:id=>timers.delete(id)});ctx.window=ctx;
  const inline=[...text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].find(m=>! /\bsrc\s*=/.test(m[1]))[2];
  vm.runInContext(once(inline,driver,""),ctx,{filename:"actual smoke helpers; main driver held"});
  ww.__widgetFixture.run=vm.runInContext('smokeRun',ctx);vm.runInContext('_r=1;expectedSourceSha="a".repeat(64)',ctx);
  const state={ww,fr,ctx,doc,document,checks,paints,styles,navigations,decodes,originalStyle,get style(){return rawStyle;},get tick(){return tick;},set paused(value){paused=value;}};
  if(!options.neverResume)later(()=>{paused=false;},75);
  if(options.orientation){
    // Source controls only: controlled navigation feeds the real loadUntil,
    // scene, calendarScene, moonLitSide and named recorder. No widget executes.
    Object.defineProperty(fr,"src",{set(value){const url=new URL(value,"http://127.0.0.1/tests/smoke.html"),f=ww.__widgetFixture;
      navigatedAt=tick;navigations.push({tick,rect:fr.getBoundingClientRect(),style:rawStyle});
      f.run=url.searchParams.get("run");f.attempt=+url.searchParams.get("attempt");f.hash=url.hash.slice(1);ww.location.hash=url.hash;
      f.documentId="00000000-0000-4000-8000-"+String(f.attempt).padStart(12,"0");
      Object.assign(f,{bridgeSha256:"c".repeat(64),storageIsolated:true,clockFixed:true,fetchIntercepted:true,
        ledger:[{attempt:f.attempt,url:"https://api.aladhan.com/v1/timings/07-09-2026",jsonReads:1,result:"json-consumed"}]});
    }});
    const start=text.indexOf('  head("moon orientation ('),end=text.indexOf('  head("explicit motion preferences',start);assert.ok(start>=0&&end>start);
    state.run=async()=>{await vm.runInContext('(async()=>{'+text.slice(start,end)+'})()',ctx,{filename:"actual orientation cells; controlled readouts"});vm.runInContext('finalize()',ctx);};
    return state;
  }
  ctx.scene=async(hash,name,fn)=>{assert.equal(name,"cloud continuity");
    // Controlled navigation supplies the exact newly staged attempt/bridge.
    // The actual cloudScene, helper, recorder and assertion cell still execute.
    const attempt=vm.runInContext("++_r",ctx),want=hash+"&tz=Asia/Riyadh&qa=1";
    ww.__widgetFixture.attempt=attempt;ww.__widgetFixture.hash=want;ww.location.hash="#"+want;
    if(options.recorded)return ctx.required(name,ok=>fn(ww,ww.qaState(),(label,condition,detail)=>{checks.push({label,condition});ok(label,condition,detail);}));
    await fn(ww,ww.qaState(),(label,condition)=>checks.push({label,condition}));};
  const start=text.indexOf('  head("cloud continuity ('),end=text.indexOf('\n}\nfunction finalize',start);assert.ok(start>=0&&end>start);
  state.run=()=>vm.runInContext('(async()=>{'+text.slice(start,end)+'})()',ctx,{filename:"actual cloud continuity cell"});
  return state;
}
async function positive(text=source){const f=fixture(text);await f.run();assert.equal(f.checks.length,3);assert.ok(f.checks.every(c=>c.condition));
  assert.equal(f.paints.length,2);assert.ok(f.paints[0]>=75&&f.paints[1]-f.paints[0]>=300);assert.equal(f.style,f.originalStyle);}
async function timeout(text=source){const f=fixture(text,{neverResume:true});await assert.rejects(f.run(),{name:"RequiredTimeout"});
  assert.equal(f.paints.length,0);assert.equal(f.style,f.originalStyle);assert.ok(f.tick<=3000);}
async function paintFailure(text=source,absentStyle=false){const f=fixture(text,{paintThrows:true,absentStyle});await assert.rejects(f.run(),/controlled paint failure/);assert.equal(f.style,f.originalStyle);}
async function stale(text=source,field="document"){const f=fixture(text,{afterElapsed(s){if(field==="document")s.ww.document={...s.doc};
  else if(field==="hash")s.ww.location.hash="#another-scene";else if(field==="attempt")vm.runInContext('_r++',s.ctx);else s.ww.__widgetFixture[field]="stale";}});
  await assert.rejects(f.run(),/Cloud continuity.*owner/);assert.equal(f.paints.length,1);assert.equal(f.checks.length,0);assert.equal(f.style,f.originalStyle);}
async function orientation(text=source,options={}){
  const f=fixture(text,{...options,orientation:true});await f.run();const ledger=f.ctx.__smoke.required;
  assert.equal(ledger.total,30);assert.equal(ledger.cases.reduce((n,c)=>n+c.expected,0),141);
  assert.equal(f.style,f.originalStyle);assert.notEqual(f.ctx.__smoke.status,"PASS","other required cases remain unexecuted");
  const cells=ledger.cases.filter(c=>/^(waxing|waning) moon orientation$/.test(c.name));assert.equal(cells.length,2);
  return {f,cells,attempts:f.ctx.__smoke.fixture.attempts};
}
async function orientationPositive(text=source,options={}){
  const {f,cells,attempts}=await orientation(text,options);assert.deepEqual(Array.from(cells,c=>c.state),["executed","executed"]);
  assert.deepEqual(Array.from(cells,c=>c.assertions),[2,1]);assert.equal(f.decodes.length,2);
  for(const row of attempts){assert.equal(row.result,"ready");assert.ok(row.calendarView,"orientation must use the existing current-stage consumer");const v=row.calendarView,s=v.readyObservation;
    assert.equal(v.styleRestored,true);assert.equal(s.frameInView,true);assert.equal(s.paused,false);assert.equal(s.current,true);
    assert.equal(s.sameOwner,true);assert.equal(s.surfaceIdentity,s.acceptedIdentity);assert.ok(s.elapsedMs<8000);}
  assert.equal(attempts.length,2);assert.ok(f.navigations.every(n=>n.rect.left===20&&n.rect.top===60));
}
async function orientationMissing(text=source,options={}){
  const {f,cells,attempts}=await orientation(text,options);assert.deepEqual(Array.from(cells,c=>c.state),["missing","missing"]);
  assert.deepEqual(Array.from(cells,c=>c.assertions),[0,0]);assert.equal(f.decodes.length,0);
  assert.ok(attempts.every(r=>r.result==="timeout"&&r.calendarView&&r.calendarView.readyObservation===null));
  assert.deepEqual(f.navigations.map(n=>n.tick),[0,8100]);assert.equal(f.tick,16200,"no second readiness window or timer reset");
}
const results=[],stageComparatorControls=[];
async function check(name,fn){try{await fn();results.push({name,result:"PASS"});}catch(e){results.push({name,result:"FAIL",error:e.message});}}
async function main(){
  await check("cloud sampling reaches in-view iframe after native resume and restores exact style",()=>positive());
  await check("orientation uses original loadUntil and in-view same-owner current surface",()=>orientationPositive());
  await check("semantic stage admits published opaque current preview, independent of refinement label",async()=>{
    const {f,cells,attempts}=await orientation(source,{surfaceSource:"terrain-preview"});assert.deepEqual(Array.from(cells,c=>c.state),["executed","executed"]);
    assert.equal(f.decodes.length,2);for(const a of attempts){const s=a.calendarView.readyObservation;assert.ok(s);assert.equal(s.contentPublished,true);
      assert.equal(s.visibleOwner,true);assert.ok(s.opaqueVisiblePixels>0);assert.equal(s.nonopaqueVisiblePixels,0);assert.equal(s.runtimeEpoch,s.runtimeEpochAfter);}
  });
  for(const [name,options] of [
    ["unready preview",{surfaceSource:"terrain-preview",unreadySurface:true}],
    ["unpublished surface URI",{wrongPublication:true}], ["wrong surface identity",{wrongIdentity:true}],
    ["stale epoch",{staleEpoch:true}], ["stale generation",{staleGeneration:true}], ["stale native scene",{staleScene:true}],
    ["geometry outside original bound",{badGeometry:true}], ["hidden composed owner",{hiddenForeground:true}],
    ["empty visible backing",{opaqueAlpha:0}], ["nonopaque visible backing",{opaqueAlpha:128}]
  ])await check("semantic stage rejects "+name,()=>orientationMissing(source,options));
  await check("semantic comparator preserves7999/8000/8001 boundary and every current-content edge",async()=>{
    const {f,attempts}=await orientation(source,{surfaceSource:"terrain-preview"});
    const valid=JSON.parse(JSON.stringify(attempts[0].calendarView.readyObservation));assert.ok(valid);
    for(const [name,changes,expected] of [
      ["current preview7999",{elapsedMs:7999},true],["deadline8000",{elapsedMs:8000},false],["late8001",{elapsedMs:8001},false],
      ["wrong owner",{sameOwner:false},false],["wrong identity",{surfaceIdentity:"stale"},false],["wrong source",{surfaceSource:"stale"},false],
      ["stale epoch",{runtimeEpochAfter:2},false],["stale generation",{nativeGenerationAfter:2},false],["stale scene",{nativeSceneIdentityAfter:"stale"},false],
      ["unready preview",{current:false},false],["paused preview",{nativePaused:true},false],["offscreen preview",{frameInView:false},false],
      ["missing publication",{contentPublished:false},false],["hidden owner",{visibleOwner:false},false],["empty opaque backing",{opaqueVisiblePixels:0},false],
      ["nonopaque backing",{nonopaqueVisiblePixels:1},false],["geometry above unchanged bound",{phaseErrorBound:.0416000001},false],
      ["phase budget drift",{phaseMaxError:.05},false],["geometry shape mismatch",{expectedSurfaceSize:301},false],
      ["current refined content",{runtimeSource:"refined-terrain",surfaceSource:"refined-terrain",runtimeSourceAfter:"refined-terrain"},true]
    ]){const input={...valid,...changes};f.ctx.__stageControl=input;const actual=vm.runInContext('calendarStageReady(__stageControl)',f.ctx);
      stageComparatorControls.push({name,input,expected,actual});assert.equal(actual,expected,name);}
  });
  await check("orientation retains image href readiness in the original8s window",()=>orientationMissing(source,{shortHref:true}));
  await check("orientation paused source readout rejects both callbacks",()=>orientationMissing(source,{neverResume:true}));
  await check("orientation readiness cannot accept current surface arriving after original8s",()=>orientationMissing(source,{currentAfter:8000}));
  await check("orientation assertion remains false after successful readiness",async()=>{
    const {f,cells,attempts}=await orientation(source,{wrongSide:true});assert.deepEqual(Array.from(cells,c=>c.state),["failed","failed"]);
    assert.deepEqual(Array.from(cells,c=>c.assertions),[2,1]);assert.equal(f.decodes.length,2);
    assert.ok(attempts.every(r=>r.result==="ready"&&r.calendarView&&r.calendarView.readyObservation.current));
  });
  if(!process.argv.includes("--red")){
    await check("orientation missing style attribute is restored exactly",()=>orientationPositive(source,{absentStyle:true}));
    await check("orientation offscreen source readout rejects both callbacks",()=>orientationMissing(helperMutation(source,"calendarScene",'fr.setAttribute("style","position:fixed;left:20px;top:60px;width:325px;height:530px;border:0");','/* controlled omission: keep offscreen */')));
  }
  if(!process.argv.includes("--baseline")){
    await check("native pause held: finite non-pass before any paint; exact style restored",()=>timeout());
    for(const absent of [false,true])await check("paint exception restores "+(absent?"absent":"raw")+" style",()=>paintFailure(source,absent));
    for(const field of ["document","hash","attempt","run","documentId","sourceSha256"])await check("new "+field+" cannot supply second cloud sample",()=>stale(source,field));
    for(const hidden of ["parent","child","paused"])await check(hidden+" withdrawal prevents second sample",async()=>{
      const f=fixture(source,{afterElapsed(s){if(hidden==="paused")s.paused=true;else (hidden==="parent"?s.document:s.doc).visibilityState="hidden";}});
      await assert.rejects(f.run(),/Cloud continuity.*visible/);assert.equal(f.paints.length,1);assert.equal(f.style,f.originalStyle);
    });
    for(const held of [false,true])await check("actual named recorder reports cloud "+(held?"missing":"executed")+" without changing denominator",async()=>{
      const f=fixture(source,{recorded:true,neverResume:held});await f.run();vm.runInContext('finalize()',f.ctx);
      const ledger=f.ctx.__smoke.required,cloud=ledger.cases.find(c=>c.name==="cloud continuity");
      assert.equal(ledger.total,30);assert.equal(ledger.cases.reduce((n,c)=>n+c.expected,0),141);
      assert.equal(cloud.state,held?"missing":"executed");assert.equal(cloud.assertions,held?0:3);
      assert.notEqual(f.ctx.__smoke.status,"PASS","other unexecuted cases cannot become green");assert.equal(f.style,f.originalStyle);
    });
    for(const [name,mutate,oracle] of [
      ["omit iframe visibility effect",s=>bothPresentationHelpers(s,'fr.setAttribute("style","position:fixed;left:20px;top:60px;width:325px;height:530px;border:0");','/* visibility effect omitted */'),positive],
      ["ignore native paused readout",s=>helperMutation(s,"withCloudFrameInView",'cardPresent && !cardPaused','cardPresent && true'),positive],
      ["omit style restoration",s=>bothPresentationHelpers(s,'else fr.setAttribute("style",style);','else void style;'),paintFailure],
      ["admit replaced document",s=>helperMutation(s,"withCloudFrameInView",'ww.document!==doc','false'),stale],
      ["omit second-sample ownership/visibility check",s=>once(s,'sampleReady("post-350ms-before-second-paint");ww.paintClouds(ww.simNow()/1000);','ww.paintClouds(ww.simNow()/1000);'),stale]
    ])await check("mutant killed: "+name,async()=>{const mutant=mutate(source);await assert.rejects(oracle(mutant));});
  }
  console.log(JSON.stringify({kind:"actual smoke-cell DOM/readout controls; no native/widget/M0 qualification",root,results,stageComparatorControls},null,2));
  if(results.some(r=>r.result==="FAIL"))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
