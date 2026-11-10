(() => {
 const NativeDate=Date, epoch=1788822000000;
 window.Date=class extends NativeDate {constructor(...args){super(...(args.length?args:[epoch]));}static now(){return epoch;}};
 const P=window.__r0007PublicDelivery={snapshots:[],events:[],started:performance.now()};
 const copy=x=>JSON.parse(JSON.stringify(x,(_,v)=>typeof v==='number'&&!Number.isFinite(v)?{finite:false,value:null}:v));
 const dom=selector=>{const e=document.querySelector(selector);if(!e)return {unavailable:true};const r=e.getBoundingClientRect();return {text:e.textContent,html:e.innerHTML,tagName:e.tagName.toLowerCase(),geometry:{x:r.x,y:r.y,width:r.width,height:r.height}};};
 P.sample=stage=>{
  if(typeof window.qaState!=='function')return null;
  const before={href:document.querySelector('.mphoto')?.getAttribute('href'),classes:document.querySelector('.c')?.className};
  try{
   const q=window.qaState(),s={stage,observedAt:performance.now(),wallUtcMs:Date.now(),render:copy(q.render),cache:copy(q.cache),currentDay:q.cache?.prayerDate,timezone:q.render?.zone,
    dom:Object.fromEntries(['.c','.nt','.left','.times','.arc','#ce','#ah','.buckle','.d'].map(x=>[x,dom(x)])),
    rows:[...document.querySelectorAll('.times .p')].map(e=>({key:e.dataset.prayerKey,on:e.classList.contains('on'),clock:e.querySelector('.tm')?.textContent,classes:e.className})),
    fonts:{status:document.fonts.status,faces:[...document.fonts].map(f=>({family:f.family,status:f.status}))},
    diagnosticSurface:{before,after:{href:document.querySelector('.mphoto')?.getAttribute('href'),classes:document.querySelector('.c')?.className}}};
   P.snapshots.push(s);return s;
  }catch(e){P.events.push({type:'observation-error',message:String(e),at:performance.now()});return null;}
 };
 const watch=()=>{P.sample('dom-ready');const observer=new MutationObserver(()=>P.sample('actual-prayer-dom-mutation'));for(const s of ['.nt','.left','.times']){const e=document.querySelector(s);if(e)observer.observe(e,{childList:true,subtree:true,characterData:true});}};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',watch,{once:true});else watch();
})();