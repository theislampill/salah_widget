// Whole inline runtime in a VM. DOM/canvas/network/clock boundaries are doubles;
// source functions (including render, atmosphere, paint and PBR) remain real.
// This proves call/state behavior, not browser compositing or texture beauty.
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function makeElement(tag = 'div') {
  const props = new Map(), attrs = new Map(), classes = new Set();
  const el = {
    tagName: tag, dataset: {}, children: [], textContent: '', _html: '', width: 300, height: 300,
    style: {setProperty(k,v){props.set(k,String(v));}, getPropertyValue(k){return props.get(k)||'';}},
    classList: {add(...s){s.forEach(v=>classes.add(v));}, remove(...s){s.forEach(v=>classes.delete(v));},
      contains(s){return classes.has(s);}, toggle(s,on){if(on)classes.add(s);else classes.delete(s);}},
    setAttribute(k,v){attrs.set(k,String(v));}, getAttribute(k){return attrs.get(k)||null;},
    removeAttribute(k){attrs.delete(k);}, appendChild(c){this.children.push(c);return c;},
    addEventListener(){}, removeEventListener(){}, focus(){},
    getBoundingClientRect(){return {x:0,y:0,top:0,left:0,right:325,bottom:530,width:325,height:530};},
    getTotalLength(){return 295;}, getPointAtLength(x){return {x,y:104};}, getScreenCTM(){return {};},
    ownerSVGElement:{createSVGPoint(){return {x:0,y:0,matrixTransform(){return {x:this.x,y:this.y};}};}},
    querySelector(){return null;}, querySelectorAll(sel){return this.children.filter(c=>c.tagName===sel);},
    getContext(){return this.ctx;}, toDataURL(){this.exports=(this.exports||0)+1;return 'data:image/png;base64,VM_BOUNDARY';},
  };
  Object.defineProperty(el,'innerHTML',{get(){return this._html;},set(s){
    this._html=s; this.children=[];
    const childTag=s.includes('<circle')?'circle':s.includes('<g ')?'g':null;
    if(childTag) for(const m of s.matchAll(new RegExp('<'+childTag+'(?:\\s|>)','g'))) this.children.push(makeElement(childTag));
  }});
  el.ctx = {
    createImageData(w,h){return {data:new Uint8ClampedArray(w*h*4),width:w,height:h};},
    getImageData(x,y,w,h){if(this.error)throw new Error('image-read-failure');return {data:this.data||new Uint8ClampedArray(w*h*4)};},
    putImageData(d){this.data=d.data;this.puts=(this.puts||0)+1;}, drawImage(){},
    measureText(t){return {width:String(t).length*15};},
  };
  return el;
}

function load({sourcePath=path.join(root,'index.html'), source, debugMoon=false, extraHash=''}={}) {
  const html=source||fs.readFileSync(sourcePath,'utf8');
  const inline=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.includes('function renderMoon()'));
  if(!inline)throw new Error('actual inline runtime not found');
  // Hold only the final entrypoint so pre-first-render and ordered fixtures are possible.
  const runtime=inline.replace(/\nboot\(\);\s*$/, '\n');
  if(runtime===inline)throw new Error('boot interception did not match actual entrypoint');
  const elements=new Map(), storage=new Map(), warnings=[], rafs=[], clock={now:0};
  const select=s=>{if(!elements.has(s))elements.set(s,makeElement(s==='.cloudcanvas'?'canvas':'div'));return elements.get(s);};
  const prayer={timings:{Fajr:'04:46',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Maghrib:'18:33',Sunset:'18:33',Isha:'20:03'},
    meta:{timezone:'Asia/Riyadh'},date:{gregorian:{day:'8',month:{number:9,en:'September'},year:'2026'},hijri:{day:'26',month:{number:3,en:'Rabi'},year:'1448'}}};
  const sandbox={URLSearchParams,URL,Intl,Math,Uint8ClampedArray,Float32Array,Float64Array,Promise,
    console:{warn(s){warnings.push(s);},log(){}}, navigator:{language:'en-US'},
    location:{hash:'#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1&simTime=22:00&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42'+(debugMoon?'&debugMoon=1':'')+extraHash},
    performance:{now:()=>clock.now}, Image:class {set src(v){this._src=v;}},
    localStorage:{getItem(k){return storage.get(k)||null;},setItem(k,v){storage.set(k,String(v));},removeItem(k){storage.delete(k);}},
    document:{querySelector:select,getElementById:id=>select('#'+id),createElement:makeElement,
      querySelectorAll:s=>s==='.stars circle'?select('.stars').children:[],addEventListener(){},visibilityState:'visible',
      createRange(){let el;return {selectNodeContents(e){el=e;},getBoundingClientRect(){return el.getBoundingClientRect();}};},
      fonts:{ready:Promise.resolve(),addEventListener(){},check(){return true;} }},
    getComputedStyle(el){return {getPropertyValue:k=>el.style.getPropertyValue(k),opacity:el.style.opacity||'1',fontFamily:'sans-serif',animationName:'tw'};},
    requestAnimationFrame(fn){rafs.push(fn);return rafs.length;},cancelAnimationFrame(){},
    setTimeout(){return 1;},clearTimeout(){}, AbortController,
    fetch:async url=>{if(!String(url).includes('aladhan.com'))throw new Error('fixture denies network '+url);
      return {ok:true,json:async()=>({code:200,data:prayer})};},
  };
  sandbox.window=sandbox; sandbox.matchMedia=()=>({matches:false});
  const ctx=vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(root,'config.js'),'utf8'),ctx,{filename:'config.js'});
  vm.runInContext(runtime,ctx,{filename:'index.html:inline'});
  const run=code=>vm.runInContext(code,ctx);
  ctx.__fixturePrayer=prayer;
  run("today=__fixturePrayer; tomorrow=__fixturePrayer; lastDate='08-09-2026'; _simBase=Date.parse('2026-09-08T19:00:00Z'); _simTz=tz; _rafT0=0; TIMESCALE=0; weather={code:2,cloud:30,cloudLow:0,cloudMid:8,cloudHigh:28,precip:0,temp:24,rh:55,dew:15,vis:20000,wind:3,windDir:225,gust:5,src:'synthetic-test'}; buildStars();");
  warnings.length=0;
  return {run,ctx,elements,select,warnings,rafs,clock,storage,sourceHash:sha(Buffer.from(html)),runtimeHash:sha(Buffer.from(runtime)),sourcePath};
}

function syntheticDisc(bright=false) {
  const width=300,height=300,radius=144,data=new Uint8ClampedArray(width*height*4);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const r=Math.hypot(x-width/2,y-height/2),i=(y*width+x)*4;
    if(r<=radius){data[i]=data[i+1]=data[i+2]=(bright||r<100)?255:0;data[i+3]=255;}
  }
  return {width,height,radius,data};
}
module.exports={load,makeElement,syntheticDisc,sha,root};
