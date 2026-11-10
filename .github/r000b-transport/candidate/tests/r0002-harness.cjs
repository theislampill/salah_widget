"use strict";
// Source-bound, no-build VM fixture. Network, storage, DOM and clock are contained;
// loader/cache/formatter/model/arc/solar functions are read from index.html, never copied.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const sourcePath = path.resolve(__dirname, "../index.html");
const source = () => fs.readFileSync(sourcePath, "utf8");
const sha256 = value => crypto.createHash("sha256").update(value).digest("hex");
const clone = value => JSON.parse(JSON.stringify(value));
const ordinaryRaw=fs.readFileSync(path.join(__dirname,"r0002-ordinary.json"),"utf8");
assert.equal(sha256(ordinaryRaw),"40c6412a36a4644ec9db9a5c92ae2e682aa22dfd6bac45be249886cfe7e76282");
const ordinary = JSON.parse(ordinaryRaw);
const captured = {
  summer: { file:"r0002-tromso-summer.json", sha256:"1a0ef89fa1a68cb0ccdd29f3ceb1a8bafed32dc45c5a2bb8430feaad7d6fe1c4", epoch:"2026-06-21T10:00:00.000Z" },
  winter: { file:"r0002-tromso-winter.json", sha256:"b7a56f538c5b306b4c7ba8e8e447870e607311c58815365563c5cc14198b2a5c", epoch:"2026-12-21T11:00:00.000Z" }
};
function polar(season) {
  const fixture = captured[season], raw = fs.readFileSync(path.join(__dirname, fixture.file), "utf8");
  assert.equal(sha256(raw), fixture.sha256, "complete captured response bytes changed");
  return { envelope:JSON.parse(raw), epoch:fixture.epoch, sha256:fixture.sha256 };
}
function sliceBetween(raw, begin, end) {
  const a = raw.indexOf(begin), b = raw.indexOf(end, a + begin.length);
  assert.ok(a >= 0 && b > a, `source owners not found: ${begin} / ${end}`);
  return raw.slice(a,b);
}
// Record the actual markup's ID owners and native-handler effects. This does not
// emulate layout, keyboard activation or modal focus containment. Unknown IDs
// remain absent, so missing calendar markup cannot silently become a fixture node.
function recordingDocument(raw, {nodes=new Map(),onHtml=()=>{},onText=()=>{}}={}) {
  const document={activeElement:null,visibilityState:"visible"}, events=new Map();
  const encode=v=>String(v).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
  const plain=v=>String(v).replace(/<[^>]*>/g,"").replace(/&(amp|lt|gt|quot|#39);/g,(_,v)=>({amp:"&",lt:"<",gt:">",quot:'"',"#39":"'"}[v]));
  function make(selector,tag="div",attrs={}) {
    let html="",text=""; const listeners=new Map(), attributes=Object.assign(Object.create(null),attrs);
    const n={tagName:tag.toUpperCase(),id:attrs.id||"",attributes,dataset:{},style:{setProperty(){}},isConnected:true,calls:[],
      classList:{add(){},toggle(){},remove(){},contains(){return false;}},
      setAttribute:(key,value)=>{attributes[key]=String(value);},getAttribute:key=>attributes[key]??null,removeAttribute:key=>{delete attributes[key];},
      addEventListener:(type,fn)=>{if(!listeners.has(type))listeners.set(type,new Set());listeners.get(type).add(fn);},
      removeEventListener:(type,fn)=>listeners.get(type)?.delete(fn),
      dispatchEvent:event=>{event.target=event.target||n;event.currentTarget=n;for(const fn of [...listeners.get(event.type)||[]])fn.call(n,event);return !event.defaultPrevented;},
      click:()=>n.dispatchEvent({type:"click",preventDefault(){this.defaultPrevented=true;}}),
      focus:options=>{if(n.isConnected){document.activeElement=n;n.calls.push({type:"focus",options});}},
      showModal:()=>{n.open=true;n.calls.push({type:"showModal"});},
      close:()=>{n.calls.push({type:"close"});if(n.open){n.open=false;n.dispatchEvent({type:"close"});}}
    };
    for(const prop of ["open","hidden"])Object.defineProperty(n,prop,{get:()=>Object.hasOwn(attributes,prop),set:value=>{if(value)attributes[prop]="";else delete attributes[prop];}});
    Object.defineProperty(n,"innerHTML",{get:()=>html,set:value=>{html=String(value);text=plain(html);onHtml(selector,html);}});
    Object.defineProperty(n,"textContent",{get:()=>text,set:value=>{text=String(value);html=encode(text);onText(selector,text);}});
    nodes.set(selector,n);return n;
  }
  const start=raw.indexOf("<body"),end=raw.indexOf('<script',start);
  assert.ok(start>=0&&end>start,"actual widget body owners missing");
  for(const match of raw.slice(start,end).matchAll(/<([a-z][\w-]*)\b([^>]*\bid="[^"]+"[^>]*)>/gi)) {
    const attrs=Object.fromEntries(Array.from(match[2].matchAll(/([\w-]+)\s*=\s*"([^"]*)"/g),m=>[m[1],m[2]]));
    for(const prop of ["open","hidden"])if(new RegExp("(?:^|\\s)"+prop+"(?:\\s|$)").test(match[2]))attrs[prop]="";
    make("#"+attrs.id,match[1],attrs);
  }
  const node=selector=>nodes.get(selector)||(selector.startsWith("#")?null:make(selector));
  Object.assign(document,{querySelector:node,getElementById:id=>node("#"+id),querySelectorAll:()=>[],addEventListener:(type,fn)=>events.set(type,fn)});
  return {document,nodes,events};
}
function harness(options = {}) {
  const raw = options.source || source();
  const date = options.date || ordinary.date.gregorian.date;
  const zone = options.zone || "UTC";
  const data = clone(options.data || ordinary);
  const body = options.body === undefined ? {code:200,status:"OK",data} : clone(options.body);
  const epoch = Date.parse(options.epoch || "2026-09-07T12:00:00.000Z");
  const suffix = options.hash || "";
  const location = {hash:`#lat=${options.lat ?? 24.47}&lon=${options.lon ?? 39.61}&tz=${encodeURIComponent(zone)}&method=${options.method || 3}${suffix}`};
  const storage = new Map(), writes = [], requests = [], rendered = [], nodes = new Map();
  let elapsed=0, loads=0;
  const key = `salah:${options.lat ?? 24.47}|${options.lon ?? 39.61}|${zone}|${options.method || 3}|0`;
  if (options.cache !== undefined) storage.set(key, typeof options.cache === "string" ? options.cache : JSON.stringify(options.cache));
  class FixedDate extends Date {
    constructor(...args) { super(...(args.length ? args : [epoch])); }
    static now() { return epoch; }
  }
  let context;
  const {document}=recordingDocument(raw,{nodes});
  const sandbox = {
    location, URLSearchParams, Intl, Date:FixedDate, AbortController, performance:{now:()=>elapsed},
    console:{warn:()=>{},log:()=>{}}, setTimeout:(fn,ms)=>ms>=10000?setTimeout(fn,ms):queueMicrotask(fn), clearTimeout,
    document,
    localStorage:{
      getItem:k=>{ if(options.readDenied) throw new Error("storage denied"); return storage.get(k) ?? null; },
      setItem:(k,value)=>{ if(options.writeDenied) throw new Error("storage denied"); writes.push({key:k,value,zone:run("tz")}); storage.set(k,value); }
    },
    fetch:async (url,init)=>{
      requests.push({url,init,zone:run("tz"),today:run("today")});
      if(options.networkDenied) throw new Error("offline fixture");
      assert.ok(url.includes(`/timings/${date}?`), `wrong requested day: ${url}`);
      return {ok:options.httpOk === undefined ? true : options.httpOk, status:options.httpStatus || 200, json:async()=>clone(body)};
    },
    render:()=>{ rendered.push({today:run("today"),tomorrow:run("tomorrow"),zone:run("tz")}); }
  };
  sandbox.window=sandbox;
  context=vm.createContext(sandbox);
  function run(code) { return vm.runInContext(code,context,{timeout:300}); }
  if(options.config !== false) run(fs.readFileSync(path.resolve(__dirname,"../config.js"),"utf8"));
  const prefix='"use strict";\n'+sliceBetween(raw,'// ---- config:',"// ---- weather (Open-Meteo:");
  const state=sliceBetween(raw,"// ---- state ----","// ---- continuous time-of-day sky");
  const solar=sliceBetween(raw,"function solarElevationDeg(M,a){","function sunAltAt(M,a){");
  const loader=sliceBetween(raw,"async function loadPrayerData(){","// clear per-location state");
  // Unrelated renderer double: these fixtures consume actual model/arc separately, not star projection.
  run(prefix+"\nlet _loopStarted=false, _starsProjected=false;\n"+state+"\n"+solar+"\n"+loader);
  return {run,load:()=>{ if(loads++) elapsed+=60000; return run("loadPrayerData()"); },data,body,key,storage,writes,requests,rendered,nodes,
    state:()=>({today:run("today"),tomorrow:run("tomorrow"),zone:run("tz"),lastDate:run("lastDate"),error:nodes.get(".left")?.textContent||""})};
}
function finiteConsumers(h) {
  const m=h.run("model()"), svg=h.run("drawArc(model())");
  for(const k of ["noon","decl","doy","sunrise","sunset","nowMin","nowAbs","warmEnd","leftMin","progress"]) assert.ok(Number.isFinite(m[k]), `nonfinite model ${k}`);
  for(const dot of m.dots) assert.ok(Number.isFinite(dot.abs), `nonfinite ${dot.k} waypoint`);
  assert.doesNotMatch(svg,/NaN|Infinity|undefined/);
  assert.equal((svg.match(/<circle class="dot/g)||[]).length,6);
  return {model:m,svg};
}
module.exports={source,sourcePath,sha256,clone,ordinary,polar,recordingDocument,harness,finiteConsumers};
