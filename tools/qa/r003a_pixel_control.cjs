'use strict';
// R003A same-tree pixel control (issue 124, R3A-07). Global Playwright; forced zone America/New_York; Playwright clock
// installed at a fixed instant; reduced motion with frozen simTime scenes; prayer fulfilled from tests/r0002-ordinary.json
// (re-dated), weather answered in-page from a fixture, every other non-loopback request aborted. No provider is contacted.
// One tree is served; only /index.html is swapped between the runs, because the generated index is the only served
// byte that differs between the compared commits (GENERATED.json and moon/BUILD.json are build metadata, never loaded).
// Runs per engine: A = --index-a, B = --index-b, A2 = --index-a again (the run-to-run noise floor). Each scene's card
// screenshot is diffed pixel by pixel in the same engine: A vs A2 (noise) and A vs B (change).
// Modes: --mode pixel (default; --dpr 1|2): healthy-scene A/B/A2 stills, pass rule diff(A2,B) <= diff(A,A2) and equal optics.
//        --mode fault  (R3A-01.8): broken low-Sun scene with visible .godray, then in page today=tomorrow=null and render(), with a .c setProperty
//                      wrapper throwing for --rain-op, _renderDirty=true; .godray opacity and crops at 0/2.5/5 s; no-fault control.
//        --mode motion (R3A-02.5): real-time page (no simTime) with &simWx=2&simCloud=50, 60 s; alpha-weighted centroid of the cloud painter
//                      canvas at 0/10/60 s (never the qaState hash); runs A, B, A2 default and B under OS reduced motion with and
//                      without &motion=full.
//        --mode moonprobe: --scene <name> --plan MB,BM,MM,... [--tag x]; per capture full PNG, Moon-box crop sha, Moon runtime
//                      state, .c class timeline and every load-time write of the five optics and Moon custom properties (JSONL).
// Usage: node tools/qa/r003a_pixel_control.cjs --root <tree> --index-a <main index.html> --index-b <branch index.html>
//        --out <fresh dir> --engine chromium|firefox|webkit [--mode pixel|fault|motion] [--dpr 1|2] [--scenes a,b] [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium',mode=a.mode||'pixel',dpr=+(a.dpr||1);
const TZ='Asia/Riyadh',INSTANT='2026-11-13T09:00:00Z';
fs.mkdirSync(out,{recursive:true});
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone=TZ;
 r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.gz':'application/octet-stream','.woff2':'font/woff2'};
let indexFile=null;
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');let p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(u.pathname==='/index.html')p=indexFile;
 else if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function shim(wx){return `(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16),W=${JSON.stringify(wx)};
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000;
   return json({timezone:TZ,utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,
    current:{time:iso(m),interval:900,weather_code:W.code,temperature_2m:70,apparent_temperature:70,relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:W.cloud,precipitation:0,is_day:W.isDay,visibility:24000}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;}
const STATE=`(()=>{const g=document.querySelector('.wfx .godray');const s=window.SalahRealSky?.state,c=document.querySelector('.c');return {composed:!!c?.classList.contains('real-sky-composed'),status:s?.status??null,
 pending:!!c?.classList.contains('sky-pending'),godrayOpacity:g?getComputedStyle(g).opacity:null,optics:Object.fromEntries(['--ray','--anticrep','--sunhalo','--sundogs','--sunpillar','--sunray'].map(k=>[k,c?.style.getPropertyValue(k)??null]))};})()`;
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&seed=1';
const LOWSUN='&simTime=16:50&simWx=2&simCloud=50&simHumid=80';
const SCENES=[['clear-noon','&simTime=12:30&simWx=0',true],['sunrise','&simTime=05:50&simWx=0',true],['sunset','&simTime=18:55&simWx=0',true],
 ['broken-low-sun-rays',LOWSUN,true],['anticrep-forced',LOWSUN+'&debugOptic=anticrep',true],['overcast','&simTime=12:30&simWx=3&simCloud=100',true],
 ['crescent-night','&simTime=19:30&simWx=0&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42',true],
 ['no-timetable-day','&simTime=12:30&simWx=2&simCloud=50',false],['no-timetable-night','&simTime=22:00&simWx=0',false],['rain','&simTime=12:30&simWx=63&simPrecip=2',true]];
async function open(browser,base,suffix,prayer,{reduced=true,wx={code:0,cloud:0,isDay:1}}={}){
 const ctx=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:dpr,timezoneId:TZ,locale:'en-US',reducedMotion:reduced?'reduce':'no-preference'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m&&prayer)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(shim(wx));
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(INSTANT)});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(base+'/index.html'+BASE+suffix);return {ctx,page,errors,aborted};}
async function settle(page){let s=null;const t0=Date.now();while(Date.now()-t0<30000){s=await page.evaluate(STATE);if(s.composed&&s.status==='ready')break;await page.waitForTimeout(250);}await page.waitForTimeout(2500);return page.evaluate(STATE);}
async function shoot(browser,base,[name,suffix,prayer]){
 const o=await open(browser,base,suffix,prayer);const s=await settle(o.page);const png=await o.page.screenshot();await o.ctx.close();
 return {png,state:s,errors:o.errors,aborted:[...new Set(o.aborted)]};}
const CENTROID=`(()=>{const k=document.querySelector('.cloudcanvas');if(!k)return null;const g=k.getContext('2d'),d=g.getImageData(0,0,k.width,k.height).data;let s=0,x=0;
 for(let i=3;i<d.length;i+=4){const a=d[i];if(a){s+=a;x+=a*(((i-3)/4)%k.width);}}return s?{x:x/s,mass:s,width:k.width}:{x:null,mass:0,width:k.width};})()`;
async function faultRun(browser,base,inject){const o=await open(browser,base,LOWSUN,true);const before=await settle(o.page);
 await o.page.evaluate(inject=>{if(inject){const st=document.querySelector('.c').style,orig=st.setProperty.bind(st);st.setProperty=(k,v)=>{if(k==='--rain-op')throw Error('R003A injected');return orig(k,v);};}
  today=null;tomorrow=null;_renderDirty=true;render();},inject);
 const frames=[];for(const ms of [0,2500,5000]){if(ms)await o.page.waitForTimeout(2500);frames.push({ms,state:await o.page.evaluate(STATE),png:await o.page.screenshot({clip:{x:0,y:0,width:200,height:200}})});}
 await o.ctx.close();return {before,frames,errors:o.errors};}
async function motionRun(browser,base,suffix,reduced){const o=await open(browser,base,'&debugMotion=1&simWx=2&simCloud=50'+suffix,true,{reduced});
 await o.page.waitForTimeout(3000);const pts=[];const t0=Date.now();for(const at of [0,10000,60000]){while(Date.now()-t0<at)await o.page.waitForTimeout(250);pts.push({ms:Date.now()-t0,c:await o.page.evaluate(CENTROID)});}
 await o.ctx.close();
 const dx=i=>pts[i].c&&pts[0].c&&pts[i].c.x!=null&&pts[0].c.x!=null?+(pts[i].c.x-pts[0].c.x).toFixed(3):null;
 return {points:pts,delta10:dx(1),delta60:dx(2),errors:o.errors};}
const PROBE=`(()=>{const W=['--ray','--anticrep','--sunhalo','--sundogs','--sunpillar','--moongrp','--moonbeam','--moonfeat','--moonocc'];
 const L=window.__r3aLog=[];const sp=CSSStyleDeclaration.prototype.setProperty;
 CSSStyleDeclaration.prototype.setProperty=function(k,v,...r){try{const c=document.querySelector('.c');if(c&&this===c.style&&W.includes(k))L.push([+performance.now().toFixed(1),k,String(v)]);}catch{}return sp.call(this,k,v,...r);};
 document.addEventListener('DOMContentLoaded',()=>{const c=document.querySelector('.c');if(!c)return;L.push([+performance.now().toFixed(1),'class',c.className]);
  new MutationObserver(()=>L.push([+performance.now().toFixed(1),'class',c.className])).observe(c,{attributes:true,attributeFilter:['class']});});})();`;
async function probeShot(browser,base,suffix,prayer,file){indexFile=file;
 const ctx=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:dpr,timezoneId:TZ,locale:'en-US',reducedMotion:'reduce'});
 await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m&&prayer)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});return route.abort();});
 await ctx.addInitScript(shim({code:0,cloud:0,isDay:1}));await ctx.addInitScript(PROBE);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(INSTANT)});await page.clock.resume();
 const t0=Date.now();await page.goto(base+'/index.html'+BASE+suffix);const s=await settle(page);const readyMs=Date.now()-t0;
 const png=await page.screenshot();const moon=await page.screenshot({clip:{x:200,y:0,width:125,height:120}});
 const info=await page.evaluate(()=>{const c=document.querySelector('.c'),rt=window.SalahMoonRuntime;let st=null;try{st=JSON.parse(JSON.stringify(rt?.state??null));}catch{st='unserialisable';}
  return {classes:c?.className,moonState:st,surface:!!rt?.surface?.(),log:window.__r3aLog};});
 await ctx.close();return {png,moon,state:s,readyMs,...info};}
async function diff(browser,x,y){const ctx=await browser.newContext();const page=await ctx.newPage();
 const r=await page.evaluate(async([p,q])=>{const load=async s=>{const i=new Image();i.src='data:image/png;base64,'+s;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;const g=c.getContext('2d');g.drawImage(i,0,0);return g.getImageData(0,0,i.width,i.height);};
  const A=await load(p),B=await load(q);if(A.width!==B.width||A.height!==B.height)return {sizeMismatch:true};let n=0,max=0;
  for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {pixels:A.width*A.height,differing:n,maxChannelDelta:max};},[x.toString('base64'),y.toString('base64')]);
 await ctx.close();return r;}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const runs={A:path.resolve(a['index-a']),B:path.resolve(a['index-b']),A2:path.resolve(a['index-a'])};
 const browser=await PW[engine].launch({headless:true});const results=[];const meta={engine,mode,dpr,version:browser.version(),indexA:sha(fs.readFileSync(runs.A)),indexB:sha(fs.readFileSync(runs.B))};
 try{
  if(mode==='pixel'){for(const scene of SCENES.filter(s=>!a.scenes||a.scenes.split(',').includes(s[0]))){const shot={};
   for(const [run,file] of Object.entries(runs)){indexFile=file;shot[run]=await shoot(browser,base,scene);fs.writeFileSync(path.join(out,`${engine}-dpr${dpr}-${scene[0]}-${run}.png`),shot[run].png);}
   const noise=await diff(browser,shot.A.png,shot.A2.png),change=await diff(browser,shot.A2.png,shot.B.png),optics=Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.state.optics]));
   const row={scene:scene[0],engine,dpr,sha:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,sha(o.png)])),noiseAvsA2:noise,changeA2vsB:change,changeAvsB:await diff(browser,shot.A.png,shot.B.png),
    pass:change.differing<=noise.differing&&change.maxChannelDelta<=noise.maxChannelDelta&&JSON.stringify(optics.A2)===JSON.stringify(optics.B),
    composed:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.state.composed])),optics,errors:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.errors])),aborted:[...new Set(Object.values(shot).flatMap(o=>o.aborted))]};
   results.push(row);console.log(JSON.stringify({scene:row.scene,dpr,noise:[noise.differing,noise.maxChannelDelta],change:[change.differing,change.maxChannelDelta],pass:row.pass,ray:optics.B['--ray'],anticrep:optics.B['--anticrep'],errors:row.errors.B.length}));}}
  else if(mode==='moonprobe'){const scene=SCENES.find(s=>s[0]===a.scene),plan=a.plan.split(','),jl=path.join(out,`moonprobe-${engine}-${a.scene}.jsonl`);
   for(let i=0;i<plan.length;i++){const trial=plan[i];for(let j=0;j<trial.length;j++){const tree=trial[j],r=await probeShot(browser,base,scene[1],scene[2],tree==='M'?runs.A:runs.B);
    const name=`${engine}-${a.scene}-${a.tag||'t'}${i}-${j}${tree}`;fs.writeFileSync(path.join(out,name+'.png'),r.png);
    const row={name,trial,pos:j,tree,sha:sha(r.png),moonSha:sha(r.moon),readyMs:r.readyMs,composed:r.state.composed,classes:r.classes,surface:r.surface,moonState:r.moonState,log:r.log};
    fs.appendFileSync(jl,JSON.stringify(row)+String.fromCharCode(10));console.log(JSON.stringify({name,moonSha:row.moonSha.slice(0,10),readyMs:r.readyMs,surface:r.surface}));}}}
  else if(mode==='fault'){for(const [run,file] of [['A',runs.A],['B',runs.B]])for(const inject of [true,false]){indexFile=file;const r=await faultRun(browser,base,inject);
   r.frames.forEach(f=>fs.writeFileSync(path.join(out,`${engine}-fault-${run}-${inject?'injected':'control'}-${f.ms}ms.png`),f.png));
   const row={run,inject,before:{ray:r.before.optics['--ray'],godray:r.before.godrayOpacity},frames:r.frames.map(f=>({ms:f.ms,ray:f.state.optics['--ray'],godray:f.state.godrayOpacity,cropSha256:sha(f.png)})),errors:r.errors};
   results.push(row);console.log(JSON.stringify(row));}}
  else if(mode==='motion'){for(const [run,file,suffix,reduced] of [['A',runs.A,'',false],['B',runs.B,'',false],['A2',runs.A,'',false],['B-reduced',runs.B,'',true],['B-reduced-full',runs.B,'&motion=full',true]]){
   indexFile=file;const r=await motionRun(browser,base,suffix,reduced);const row={run,...r};results.push(row);console.log(JSON.stringify({run,delta10:r.delta10,delta60:r.delta60,mass:r.points[0].c?.mass??null,errors:r.errors.length}));}}
  if(mode!=='moonprobe')fs.writeFileSync(path.join(out,`${mode}-${engine}${mode==='pixel'?'-dpr'+dpr+(a.scenes?'-'+a.scenes.split(',')[0]:''):''}.json`),JSON.stringify({...meta,scenes:a.scenes||'all',results},null,1));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
