'use strict';
// Complete owned-source consumers, isolated storage/providers, recording DOM. No native/layout claim.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {ROOT,sha,session}=require('./r0009-calendar-harness.cjs');
const {deferred,drain}=require('./r000f-fixture.cjs');
const BASE='46cdfce00e7898e2e48776c3918b115badac5fca';
const read=file=>fs.readFileSync(path.join(ROOT,file),'utf8');
function configSession(source=read('config.js')){
  const data=new Map(),window={localStorage:{getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,String(v)),removeItem:k=>data.delete(k)}};
  const context=vm.createContext({window,URLSearchParams,Date,Intl,console});vm.runInContext(source,context);
  return {api:window.SalahConfig,data,context,sourceSha256:sha(source)};
}
function widget({source=read('index.html'),configSource,hash='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=UTC',failSave=false,failReset=false}={}){
  const s=session({source}),timers=new Map();let timerId=0;
  s.context.setTimeout=(fn,ms)=>{const id=++timerId;timers.set(id,{fn,ms});return id;};s.context.clearTimeout=id=>timers.delete(id);
  function enhance(n){
    if(!n||n.appearanceFixtureReady)return n;n.appearanceFixtureReady=true;
    let value=n.attributes.value||'',classes=new Set((n.attributes.class||'').split(/\s+/).filter(Boolean));
    Object.defineProperty(n,'value',{get:()=>value,set:v=>{value=String(v);}});
    n.classList={add:(...xs)=>xs.forEach(x=>classes.add(x)),remove:(...xs)=>xs.forEach(x=>classes.delete(x)),contains:x=>classes.has(x),toggle:(x,on)=>{on=on===undefined?!classes.has(x):on;on?classes.add(x):classes.delete(x);return on;}};
    n.querySelector=()=>null;n.querySelectorAll=()=>[];
    const dispatch=n.dispatchEvent;n.dispatchEvent=event=>{dispatch(event);if(n.eventParent)n.eventParent.dispatchEvent(event);return true;};
    return n;
  }
  s.nodes.forEach(enhance);const query=s.document.querySelector;s.document.querySelector=selector=>enhance(query(selector));
  const byId=s.document.getElementById;s.document.getElementById=id=>enhance(byId(id));
  for(const [selector,n]of s.nodes)if(selector.startsWith('#set-')||selector==='#setClose')n.eventParent=s.nodes.get('#settings');
  const originalSet=s.context.localStorage.setItem,originalRemove=s.context.localStorage.removeItem;
  s.context.localStorage.setItem=(k,v)=>{if(failSave&&k===s.context.SalahConfig.KEY){const e=Error('Controlled refused save');e.name='QuotaExceededError';throw e;}originalSet(k,v);};
  s.context.localStorage.removeItem=k=>{if(failReset&&k===s.context.SalahConfig.KEY){const e=Error('Controlled refused reset');e.name='SecurityError';throw e;}originalRemove(k);};
  if(configSource)s.evaluate(configSource);
  const coarse=[];s.context.SalahConfig.coarseDetect=()=>{const d=deferred();coarse.push(d);return d.promise;};
  // Keep real normalize/save/persistence publication/bindConfig/settings/render. Suspend unrelated acquisition/art.
  s.evaluate('beginRuntimeGeneration=()=>{};resetForNewLocation=()=>{};startWeather=()=>{};loadPrayerData=async()=>{};startRenderLoop=()=>render();');
  const resolve=nextHash=>{s.context.location.hash=nextHash;return s.evaluate('var appearanceResolution=SalahConfig.resolve(location.hash);_hashCfg=appearanceResolution.hashCfg;_cfgFlags=appearanceResolution.flags;_cfgMode=appearanceResolution.mode;if(appearanceResolution.cfg)bindConfig(appearanceResolution.cfg);appearanceResolution;');};
  resolve(hash);
  const field=id=>s.nodes.get('#'+id);
  return {...s,coarse,timers,resolve,field,open:()=>s.evaluate('_openSettings()'),close:async()=>{field('setClose').click();await drain();},
    input:(id,value)=>{const n=field(id);if(!n)throw Error('Actual appearance field absent: '+id);n.value=value;n.dispatchEvent({type:'change',target:n,preventDefault(){}});},
    reset:async()=>{field('set-reset').click();await drain();},settleReset:async(cfg)=>{coarse.at(-1).resolve({ok:true,cfg});await drain();}};
}
function builder({source=read('builder.html'),configSource=read('config.js')}={}){
  const nodes=new Map(),document={activeElement:null},coarse=[];
  const attrs=text=>Object.fromEntries(Array.from(text.matchAll(/([\w-]+)="([^"]*)"/g),m=>[m[1],m[2]]));
  function node(id,attributes={}){const events=new Map(),classes=new Set((attributes.class||'').split(/\s+/));const n={id,value:attributes.value||'',attributes:{...attributes},style:{},disabled:false,children:[],textContent:'',
    classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x),toggle:(x,on)=>on?classes.add(x):classes.delete(x)},
    addEventListener:(type,fn)=>{if(!events.has(type))events.set(type,[]);events.get(type).push(fn);},setAttribute:(k,v)=>{n.attributes[k]=String(v);if(k==='tabindex')n.tabIndex=+v;},getAttribute:k=>n.attributes[k]??null,
    querySelectorAll:()=>n.children,focus:()=>{document.activeElement=n;},dispatch:type=>{const e={type,target:n,preventDefault(){}};for(const fn of events.get(type)||[])fn(e);if(type==='click'&&n.onclick)n.onclick(e);}};nodes.set(id,n);return n;}
  for(const m of source.slice(0,source.indexOf('<script src="config.js">')).matchAll(/<([a-z][\w-]*)\b([^>]*\bid="[^"]+"[^>]*)>/gi)){const a=attrs(m[2]);node(a.id,a);}
  for(const m of source.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/g)){const id=attrs(m[1]).id,options=Array.from(m[2].matchAll(/<option\b([^>]*)>/g));const option=options.find(x=>/\bselected\b/.test(x[1]))||options[0];if(nodes.has(id)&&option)nodes.get(id).value=attrs(option[1]).value;}
  const group=node('mode-group');group.children=['mode-portable','mode-local'].map(id=>nodes.get(id));
  Object.assign(document,{getElementById:id=>nodes.get(id)||null,querySelector:selector=>selector==='.modebtns'?group:null});
  const context=vm.createContext({window:null,document,URLSearchParams,URL,Intl,Date,console,location:{href:'https://example.test/widget/builder.html'},navigator:{language:'en-US',platform:'Win32',userAgent:'controlled'},setTimeout:()=>1,clearTimeout(){}});context.window=context;
  vm.runInContext(configSource,context);context.SalahConfig.coarseDetect=()=>{const d=deferred();coarse.push(d);return d.promise;};
  const script=source.match(/<script>\s*([\s\S]*?)<\/script>/)[1];vm.runInContext(script,context);
  return {nodes,context,coarse,sourceSha256:sha(source),configSha256:sha(configSource),run:js=>vm.runInContext(js,context),
    input:(id,value)=>{const n=nodes.get(id);if(!n)throw Error('Actual builder field absent: '+id);n.value=value;n.dispatch('change');},
    hash:()=>new URL(nodes.get('code').value.match(/src="([^"]+)"/)[1]).hash.slice(1)};
}
module.exports={ROOT,BASE,read,sha,widget,builder,configSession,drain};
