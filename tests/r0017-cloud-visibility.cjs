/* R0017: execute the actual cloud smoke cell against controlled DOM/readout
 * boundaries. No product observer, flags, renderer, browser or motion proof. */
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const root=path.resolve(process.argv.slice(2).find(a=>!a.startsWith("--"))||path.join(__dirname,".."));
const source=fs.readFileSync(path.join(root,"tests/smoke.html"),"utf8");
const driver='(async()=>{try{await run();}catch(e){line("fail","harness error: "+e.message);}finally{finalize();}})();';
function once(text,from,to){assert.equal(text.split(from).length,2,"source anchor must be unique");return text.replace(from,to);}
function fixture(text=source,options={}){
  let tick=0,next=0,scheduled=false,paused=true,rawStyle=options.absentStyle?null:"position:absolute;left:-9999px;top:0;width:325px;height:530px;border:0;outline: 1px solid red";
  const originalStyle=rawStyle,timers=new Map(),paints=[],checks=[],styles=[];
  function drain(){if(scheduled)return;scheduled=true;setImmediate(()=>{scheduled=false;
    const pending=[...timers].sort((a,b)=>a[1].due-b[1].due||a[0]-b[0])[0];
    if(pending){timers.delete(pending[0]);tick=pending[1].due;pending[1].fn();}if(timers.size)drain();});}
  function later(fn,ms){const id=++next;timers.set(id,{due:tick+ms,fn:()=>{if(ms===350&&options.afterElapsed)options.afterElapsed(state);fn();}});drain();return id;}
  const card={classList:{contains(name){assert.equal(name,"paused");return paused;}}};
  const doc={visibilityState:"visible",querySelector(selector){if(selector===".c")return card;if(selector===".cloudcanvas")return canvas;throw Error("Unexpected child selector "+selector);}};
  const ww={document:doc,location:{hash:"#owned-cloud-scene"},performance:{now:()=>tick},
    __widgetFixture:{run:null,attempt:1,documentId:"00000000-0000-4000-8000-000000000001",hash:"owned-cloud-scene",sourceSha256:"a".repeat(64),state:"ready"},
    qaState(){return {wxTruth:{cloudFieldSeed:123}};},simNow(){return 42;},
    paintClouds(t){const r=fr.getBoundingClientRect();assert.ok(r.right>0&&r.left<1280&&r.bottom>0&&r.top<900,"sampling requires an in-view iframe");
      assert.equal(paused,false,"sampling requires native paused readout to clear");assert.equal(ww.document.visibilityState,"visible");assert.equal(t,42/1000);paints.push(tick);if(options.paintThrows)throw Error("controlled paint failure");}};
  // Literal alpha samples exercise the existing checksum/assertion consumer only.
  const canvas={width:2,height:1,getContext(kind){assert.equal(kind,"2d");return {getImageData(){return {data:Uint8ClampedArray.from([0,0,0,200,0,0,0,paints.length===1?100:120])};}};}};
  const fr={contentWindow:ww,isConnected:true,
    getAttribute(name){assert.equal(name,"style");return rawStyle;},
    setAttribute(name,value){assert.equal(name,"style");styles.push(value);rawStyle=value;},
    removeAttribute(name){assert.equal(name,"style");styles.push(null);rawStyle=null;},
    getBoundingClientRect(){const property=(name,fallback)=>{const m=(rawStyle||"").match(new RegExp("(?:^|;)\\s*"+name+":\\s*(-?[0-9]+)px"));return m?+m[1]:fallback;};
      const left=property("left",-9999),top=property("top",0);return {left,top,right:left+325,bottom:top+530};}};
  const elements={w:fr,out:{appendChild(){}},sum:{}};
  const document={visibilityState:"visible",getElementById(name){return elements[name];},createElement(){return {};}};fr.ownerDocument=document;
  const ctx=vm.createContext({URLSearchParams,URL,Date,Math,console,document,location:{search:""},innerWidth:1280,innerHeight:900,
    performance:{now:()=>tick},setTimeout:later,clearTimeout:id=>timers.delete(id)});ctx.window=ctx;
  const inline=[...text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].find(m=>! /\bsrc\s*=/.test(m[1]))[2];
  vm.runInContext(once(inline,driver,""),ctx,{filename:"actual smoke helpers; main driver held"});
  ww.__widgetFixture.run=vm.runInContext('smokeRun',ctx);vm.runInContext('_r=1;expectedSourceSha="a".repeat(64)',ctx);
  const state={ww,fr,ctx,doc,document,checks,paints,styles,originalStyle,get style(){return rawStyle;},get tick(){return tick;},set paused(value){paused=value;}};
  if(!options.neverResume)later(()=>{paused=false;},75);
  ctx.scene=async(hash,name,fn)=>{assert.equal(name,"cloud continuity");
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
const results=[];
async function check(name,fn){try{await fn();results.push({name,result:"PASS"});}catch(e){results.push({name,result:"FAIL",error:e.message});}}
async function main(){
  await check("cloud sampling reaches in-view iframe after native resume and restores exact style",()=>positive());
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
    for(const [name,from,to,oracle] of [
      ["omit iframe visibility effect",'fr.setAttribute("style","position:fixed;left:20px;top:60px;width:325px;height:530px;border:0");','/* visibility effect omitted */',positive],
      ["ignore native paused readout",'!card.classList.contains("paused")','true',positive],
      ["omit style restoration",'else fr.setAttribute("style",style);','else void style;',paintFailure],
      ["admit replaced document",'ww.document!==doc','false',stale],
      ["omit second-sample ownership/visibility check",'sampleReady();ww.paintClouds(ww.simNow()/1000);','ww.paintClouds(ww.simNow()/1000);',stale]
    ])await check("mutant killed: "+name,async()=>{const mutant=once(source,from,to);await assert.rejects(oracle(mutant));});
  }
  console.log(JSON.stringify({kind:"actual smoke-cell DOM/readout controls; no native/widget/M0 qualification",root,results},null,2));
  if(results.some(r=>r.result==="FAIL"))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
