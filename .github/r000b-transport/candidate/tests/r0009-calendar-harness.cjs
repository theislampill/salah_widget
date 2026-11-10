'use strict';
// Actual-source admitted-state controls; not a DOM, accessibility or wall-clock certification.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm'), assert=require('node:assert/strict');
const {nativeInlineRuntime}=require('./native-inline-runtime.cjs');
const {ROOT,sha,CANARY}=require('./r0001-browser-fixture.cjs');
const text=html=>String(html).replace(/<[^>]*>/g,'').replace(/&(amp|lt|gt|quot|#39);/g,(_,v)=>({amp:'&',lt:'<',gt:'>',quot:'"','#39':"'"}[v]));
const encodeText=value=>String(value).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function record(gDay='07',hDay='19',method='HJCoSA'){
  return {timings:{Fajr:'05:00',Sunrise:'06:00',Dhuhr:'12:00',Asr:'15:00',Sunset:'18:00',Maghrib:'18:00',Isha:'20:00'},
    date:{gregorian:{date:gDay+'-09-2026',day:gDay,month:{number:9,en:'September'},year:'2026'},hijri:{date:hDay+'-02-1448',day:hDay,month:{number:2,en:'Safar'},year:'1448',...(method==null?{}:{method})}},
    meta:{latitude:24.47,longitude:39.61,timezone:'UTC',method:{id:4},school:'STANDARD'}};
}
function session({sourcePath=path.join(ROOT,'index.html'),source,format='YYYY-MM-DD',at='2026-09-07T17:59:59Z',saved=false,zone='UTC'}={}){
  source=source||fs.readFileSync(sourcePath,'utf8');
  const config=fs.readFileSync(path.join(ROOT,'config.js'),'utf8'), nodes=new Map(), effects={storageWrites:0,fetches:0,timers:0};
  const start=source.indexOf('<body'),body=source.slice(start,source.indexOf('<script',start));
  const attributes=s=>Object.fromEntries(Array.from(s.matchAll(/([\w-]+)\s*=\s*"([^"]*)"/g),m=>[m[1],m[2]]));
  const document={activeElement:null};
  function make(selector,tag='div',attrs={},connected=true){
    let html='',plain=''; const events=new Map();
    const n={tagName:tag.toUpperCase(),id:attrs.id||'',attributes:{...attrs},dataset:{},style:{setProperty(){}},open:false,writes:0,attributeWrites:0,isConnected:connected,calls:[],
      get innerHTML(){return html;},set innerHTML(v){html=String(v);plain=text(html);n.writes++;},
      get textContent(){return plain;},set textContent(v){plain=String(v);html=encodeText(plain);n.writes++;},
      getAttribute:k=>n.attributes[k]??null,setAttribute:(k,v)=>{n.attributes[k]=String(v);n.attributeWrites++;},removeAttribute:k=>{delete n.attributes[k];n.attributeWrites++;},
      addEventListener:(k,f)=>{if(!events.has(k))events.set(k,[]);events.get(k).push(f);},
      dispatchEvent:event=>{event.target=event.target||n;for(const f of events.get(event.type)||[])f(event);if(typeof n['on'+event.type]==='function')n['on'+event.type](event);return true;},
      focus(){if(n.isConnected)document.activeElement=n;},click(){n.dispatchEvent({type:'click',preventDefault(){}});},
      // Modal focus containment is deliberately not emulated. Tests set recording focus explicitly.
      showModal(){n.calls.push('showModal');n.open=true;},close(){n.calls.push('close');if(n.open){n.open=false;n.dispatchEvent({type:'close'});}},
      cloneNode(){const copy=make(selector,tag,n.attributes,false);copy.textContent=n.textContent;return copy;},
      replaceWith(other){n.isConnected=false;other.isConnected=true;nodes.set(selector,other);if(document.activeElement===n)document.activeElement=null;},
      classList:{add(){},remove(){},toggle(){},contains(){return false;}},getContext(){throw Error('Recording DOM does not paint canvas');},getBoundingClientRect(){throw Error('Recording DOM does not measure layout');}};
    n.tabIndex=attrs.tabindex!=null?+attrs.tabindex:tag==='button'?0:-1;if(connected)nodes.set(selector,n);return n;
  }
  for(const m of body.matchAll(/<([a-z][\w-]*)\b([^>]*\bid="[^"]+"[^>]*)>/gi)){const attrs=attributes(m[2]);make('#'+attrs.id,m[1].toLowerCase(),attrs);}
  const triggers={};
  for(const m of body.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/gi)){const attrs=attributes(m[1]);for(const id of ['ce','ah'])if(new RegExp('id="'+id+'"').test(m[2]))triggers[id]=nodes.get('#'+attrs.id)||make('trigger:'+id,'button',attrs);}
  const node=selector=>{if(nodes.has(selector))return nodes.get(selector);if(selector.startsWith('#'))return null;return make(selector);};
  Object.assign(document,{querySelector:node,getElementById:id=>node('#'+id),querySelectorAll:selector=>selector==='.date-trigger'?Object.values(triggers):[],addEventListener(){}});
  const storage=new Map();
  if(saved)storage.set('salah_widget:config:v1',JSON.stringify({v:1,lat:24.47,lon:39.61,tz:zone,label:'Madinah',method:'4',school:'0',time:'24',datefmt:format,units:'f',lp:0,source:'manual',savedAt:Date.parse(at)}));
  let wall=Date.parse(at); class FixedDate extends Date{constructor(...args){super(...(args.length?args:[wall]));}static now(){return wall;}}
  const context=vm.createContext({Date:FixedDate,Intl,URLSearchParams,URL,console,performance:{now:()=>0},document,
    location:{hash:saved?'#local=1&tz='+encodeURIComponent(zone):'#lat=24.47&lon=39.61&label=Madinah&method=4&tz='+encodeURIComponent(zone)+'&simWx=0&datefmt='+encodeURIComponent(format)},
    localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>{effects.storageWrites++;storage.set(k,String(v));},removeItem:k=>{effects.storageWrites++;storage.delete(k);}},
    Image:class{},getComputedStyle:()=>({getPropertyValue:()=>'',opacity:'1',animationName:'none'}),
    setTimeout(){effects.timers++;throw Error('Unexpected async work in admitted-state fixture');},clearTimeout(){},
    fetch(){effects.fetches++;throw Error('Unexpected transport in admitted-state fixture');}});
  context.window=context;
  vm.runInContext(config,context,{filename:'config.js'});
  const nativeScript=nativeInlineRuntime(source);
  vm.runInContext(nativeScript.replace('\nboot();','\n// admitted-state fixture suspends async boot only'),context,{filename:'index.html:inline'});
  // Fixed Date is installed before initialization; real clock/model/partsInTz/render remain.
  // Async boot and unrelated art are suspended; this earns no clock/load/native qualification.
  vm.runInContext('syncWeather=()=>{};renderMoon=()=>{};projectStars=()=>{};drawArc=()=>"";fitCn=()=>{};applyTheme=()=>{};',context);
  const state=(t=record(),next=record('08','20'),stale=false)=>vm.runInContext('today='+JSON.stringify(t)+';tomorrow='+JSON.stringify(next)+';fetchingTomorrow=true;lastDate='+JSON.stringify(t?.date?.gregorian?.date||'')+';_prayerStale='+stale+';',context);
  state();
  function snapshot(){
    // qaState's config diagnostic probes storage availability with a set/remove pair.
    // Record actual consumer effects before that instrument; retain its cost separately.
    const consumerEffects={...effects};
    const qa=vm.runInContext('window.qaState()',context);
    return {ce:node('#ce').textContent,ah:node('#ah').textContent,ceHtml:node('#ce').innerHTML,ahHtml:node('#ah').innerHTML,
      title:node('#ah').getAttribute('title')||node('#ah').title||'',prayerStale:qa.cache.prayerStale,dateTruth:qa.dateTruth||null,
      ceButtonLabel:node('#ceDateButton')?.getAttribute('aria-label')||'',ahButtonLabel:node('#ahDateButton')?.getAttribute('aria-label')||'',
      dialog:{gregorian:node('#dateGregorian')?.textContent||'',hijri:node('#dateHijri')?.textContent||'',preview:node('#datePreview')?.textContent||'',reason:node('#dateReason')?.textContent||'',previewHidden:node('#datePreview')?.hidden},
      current:node('.cn').textContent,rows:(node('.times').innerHTML.match(/class="p(?:\s|")/g)||[]).length,effects:consumerEffects,qaProbeEffects:{before:consumerEffects,after:{...effects}},qa};
  }
  const render=()=>{vm.runInContext('render()',context);const s=snapshot();assert.equal(s.rows,6,'Actual six-row renderer positive');assert.ok(s.current,'Actual prayer model positive');return s;};
  return {source,sourceSha256:sha(source),configSha256:sha(config),context,nodes,triggers,document,effects,state,render,snapshot,storageState:()=>Array.from(storage.entries()),setClock:instant=>{wall=Date.parse(instant);},evaluate:js=>vm.runInContext(js,context)};
}
module.exports={ROOT,sha,CANARY,record,session};
