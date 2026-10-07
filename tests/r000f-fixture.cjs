"use strict";
// Source-bound VM fixture. DOM, timer, permission and provider doubles contain no
// network/clipboard sink. This is schedule evidence, not native browser evidence.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const {execFileSync} = require("node:child_process");
const root = path.resolve(__dirname, "..");
function readSource(file, ref) {
  return ref ? execFileSync("git", ["show", `${ref}:${file}`], {cwd:root, encoding:"utf8"})
    : fs.readFileSync(path.join(root, file), "utf8");
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes,no)=>{ resolve=yes; reject=no; });
  return {promise,resolve,reject};
}
async function drain() { for(let i=0;i<10;i++) await Promise.resolve(); }
function environment() {
  const elements = new Map(), timers = new Map(), storage = new Map();
  let time=0, timerId=0;
  const document = {activeElement:null};
  class Element {
    get value() { return this._value; }
    set value(value) { this._value=String(value); }
    constructor(id="") {
      this.id=id; this.value=""; this.textContent=""; this.innerHTML="";
      this.tagName="DIV"; this.style={}; this.attributes={}; this.listeners={}; this.children=[];
      this.dataset=new Proxy(Object.create(null),{set:(data,key,value)=>{
        data[key]=String(value);this.attributes["data-"+String(key).replace(/[A-Z]/g,c=>"-"+c.toLowerCase())]=String(value);return true;
      }});
      this.disabled=false; this.hidden=false; this.tabIndex=0; this.offsetParent={};
      const classes=new Set();
      const syncClass=()=>{this.attributes.class=[...classes].join(" ");};
      Object.defineProperty(this,"className",{get:()=>[...classes].join(" "),set:value=>{classes.clear();String(value).split(/\s+/).filter(Boolean).forEach(x=>classes.add(x));syncClass();}});
      this.classList={add:(...xs)=>{xs.forEach(x=>classes.add(x));syncClass();},
        remove:(...xs)=>{xs.forEach(x=>classes.delete(x));syncClass();}, contains:x=>classes.has(x),
        toggle:(x,on)=>{ on=on===undefined?!classes.has(x):on; on?classes.add(x):classes.delete(x);syncClass();return on; },
        toString:()=>[...classes].sort().join(" ")};
    }
    addEventListener(type,handler) { (this.listeners[type] ||= []).push(handler); }
    setAttribute(key,value) {
      this.attributes[key]=String(value);if(key==="tabindex")this.tabIndex=+value;if(key==="class")this.className=value;
      if(key.startsWith("data-"))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=value;
    }
    getAttribute(key) { return this.attributes[key] ?? null; }
    appendChild(child) { child.parent=this; this.children.push(child); return child; }
    remove() { if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this); }
    focus() { document.activeElement=this; }
    select() { this.selectionStart=0; this.selectionEnd=this.value.length; document.lastSelected=this; }
    querySelector(selector) { return this.children.find(x=>selector.startsWith(".")?x.classList.contains(selector.slice(1)):selector.startsWith("#")?x.id===selector.slice(1):false) || null; }
    querySelectorAll() { return this.children; }
    dispatch(type,options={}) {
      const event={type,target:this,key:"",shiftKey:false,defaultPrevented:false,
        preventDefault(){this.defaultPrevented=true;},...options};
      const results=[];
      for(let el=this;el;el=el.eventParent) {
        for(const listener of el.listeners[type] || []) results.push(listener(event));
        if(type==="click" && el===this && el.onclick)results.push(el.onclick(event));
      }
      return {event,results};
    }
  }
  function el(id,value="") { const element=new Element(id); element.value=value; elements.set(id,element); return element; }
  const body=new Element("body"), card=el("card"), buckle=el("buckle"), group=el("mode-group");
  card.classList.add("c");buckle.classList.add("buckle");group.classList.add("modebtns");
  document.body=body;
  document.getElementById=id=>elements.get(id) || null;
  document.createElement=tag=>{const element=new Element();element.tagName=String(tag).toUpperCase();return element;};
  document.querySelector=selector=>selector.startsWith("#")?elements.get(selector.slice(1))||null:selector.startsWith(".")?[...elements.values()].find(x=>x.classList.contains(selector.slice(1)))||null:null;
  function initializeTag(element,tag){for(const [,name,value]of tag.matchAll(/([\w:-]+)="([^"]*)"/g))element.setAttribute(name,value);}
  const localStorage={getItem:key=>storage.get(key)??null,
    setItem:(key,value)=>storage.set(key,String(value)),removeItem:key=>storage.delete(key)};
  const sandbox={console, URL, URLSearchParams, Intl, Date, document, localStorage,
    location:{href:"https://example.test/widget/builder.html"},
    navigator:{language:"en-US",platform:"Win32",userAgent:"controlled"},
    setTimeout:(callback,ms=0)=>{const id=++timerId; timers.set(id,{callback,at:time+ms}); return id;},
    clearTimeout:id=>timers.delete(id)};
  sandbox.window=sandbox;
  const context=vm.createContext(sandbox);
  async function advance(ms) {
    const until=time+ms;
    for(;;) {
      const next=[...timers].filter(([,t])=>t.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];
      if(!next)break;
      time=next[1].at; timers.delete(next[0]); next[1].callback(); await drain();
    }
    time=until; await drain();
  }
  function input(id,value,type="input") { const field=elements.get(id); field.value=String(value); field.dispatch(type); }
  return {el,elements,context,document,sandbox,card,buckle,group,storage,timers,advance,input,initializeTag,
    run:source=>vm.runInContext(source,context), key:(id,key,shiftKey=false)=>elements.get(id).dispatch("keydown",{key,shiftKey}),
    click:id=>elements.get(id).dispatch("click")};
}
function fixture(kind,options={}) {
  const env=environment(), {el,run,sandbox}=env;
  const sources={config:readSource("config.js",options.ref), page:readSource(kind==="builder"?"builder.html":"index.html",options.ref)};
  run(sources.config);
  const queues={search:[],coarse:[],gps:[],reverse:[],permission:[]};
  const calls={search:[],reverse:[],copy:[],fallback:[],applied:[]};
  function queue(name,args) { const d=deferred(); queues[name].push(d); if(calls[name])calls[name].push(args); return d.promise; }
  sandbox.SalahConfig.geocodeSearch=(q,opts)=>queue("search",{q,homeCC:opts.homeCC});
  sandbox.SalahConfig.coarseDetect=()=>queue("coarse",{});
  sandbox.SalahConfig.geolocate=()=>queue("gps",{});
  sandbox.SalahConfig.permissionState=()=> options.deferPermission ? queue("permission",{}) : Promise.resolve("granted");
  sandbox.navigator.geolocation={getCurrentPosition:(ok,bad,opts)=>{ queue("gps",{opts}).then(ok,bad); }};
  sandbox.fetch=url=>{ const d=deferred(); queues.reverse.push(d); calls.reverse.push(url); return Promise.resolve({json:()=>d.promise}); };
  sandbox.navigator.clipboard={writeText:text=>{calls.copy.push(text); return options.clipboard?options.clipboard(text):Promise.resolve();}};
  env.document.execCommand=command=>{ calls.fallback.push({command,text:env.document.lastSelected?.value}); return options.fallback?options.fallback(command):false; };
  if(options.platform)sandbox.navigator.platform=options.platform;
  if(kind==="builder") {
    const defaults={label:"Madinah",lat:"24.4672",lon:"39.6142",method:"4",school:"0",time:"24",units:"f",appearance:"glass",dfcode:"YYYY-MM-DD",datefmt:"YYYY-MM-DD"};
    for(const [id,value]of Object.entries(defaults))el(id,value);
    for(const id of ["loclabel","geotip","geo","dfCustomOpt","pv","code","copied","copy","open","reload","install","installtip","modenote","embed-recovery","embed-recovery-wrap","install-recovery","install-recovery-wrap"] )el(id);
    for(const id of ["embed-recovery-wrap","install-recovery-wrap"])env.elements.get(id).hidden=true;
    for(const id of ["mode-portable","mode-local"]) {
      const button=el(id), tag=sources.page.match(new RegExp('<button[^>]*id="'+id+'"[^>]*>'))[0];
      env.initializeTag(button,tag);
      button.classList.add("modebtn"); button.eventParent=env.group; env.group.children.push(button);
    }
    let script=sources.page.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
    if(options.mutate)script=options.mutate(script);
    run(script);
  } else {
    const cardTag=sources.page.match(/<div class="c(?:\s[^"]*)?"[^>]*>/);if(!cardTag)throw Error("card source tag missing");env.initializeTag(env.card,cardTag[0]);
    const panel=el("settings");
    for(const id of ["set-lat","set-lon","set-label","set-method","set-school","set-time","set-units","set-appearance","set-datefmt","set-datefmt-preset","setClose","set-pin","set-reset","set-status"]) {
      const field=el(id); field.eventParent=panel; panel.children.push(field);
    }
    run('let lat=24.4672,lon=39.6142,label="Madinah",method="4",school="0",fmt24=true,units="f",datefmtStr="YYYY-MM-DD",tz="Asia/Riyadh",LPOLL=0; let CONFIG={lat,lon,label,method,school,time:"24",units,datefmt:datefmtStr,tz,source:"manual"}; let _hashCfg={},_storageErr=null,_geoPermission="unknown",_geoLastError=null;');
    sandbox.applyConfig=async(cfg,opts)=>{
      calls.applied.push({cfg:JSON.parse(JSON.stringify(cfg)),opts});
      sandbox.fixtureCfg=cfg;
      run('CONFIG=fixtureCfg; lat=CONFIG.lat; lon=CONFIG.lon; label=CONFIG.label; method=CONFIG.method; school=CONFIG.school; fmt24=CONFIG.time!=="12"; units=CONFIG.units; datefmtStr=CONFIG.datefmt;');
      if(opts.save)sandbox.SalahConfig.saveLocal(cfg);
    };
    const start=sources.page.indexOf("let _setWired="), end=sources.page.lastIndexOf("\nboot();");
    if(start<0||end<start)throw new Error("settings source boundaries changed");
    let script=sources.page.slice(start,end);
    if(options.mutate)script=options.mutate(script);
    run(script);
    run("_enableSettingsAffordance()"); env.buckle.dispatch("click");
  }
  function tuple() {
    const ids=kind==="builder"?["label","lat","lon","method"]:["set-label","set-lat","set-lon","set-method"];
    return ids.map(id=>env.elements.get(id).value);
  }
  function snapshot() {
    return JSON.stringify({tuple:tuple(),status:env.elements.get(kind==="builder"?"geotip":"set-status").textContent,
      pin:env.elements.get(kind==="builder"?"geo":"set-pin").classList.toString(),
      candidates:run(kind==="builder"?"multiCands":"_setCands"),
      country:run(kind==="builder"?"homeCC":"_setHomeCC"),
      dirty:kind==="settings"?run("_setDirty"):null,
      code:kind==="builder"?env.elements.get("code").value:null,storage:[...env.storage],applied:calls.applied});
  }
  return {...env,kind,sources,queues,calls,tuple,snapshot,
    hash:()=>new URL(env.elements.get("code").value.match(/src="([^"]+)"/)[1]).hash.slice(1),
    resolve:async(name,index,value)=>{ queues[name][index].resolve(value); await drain(); },
    reject:async(name,index)=>{ queues[name][index].reject(new Error("controlled provider failure")); await drain(); }};
}
module.exports={fixture,environment,deferred,drain,readSource};
