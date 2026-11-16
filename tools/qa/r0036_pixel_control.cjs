'use strict';
// R0036 (issue 103) same-tree pixel control and observer-effect differential (ES36-04, browser part). Global Playwright.
// NETWORK ISOLATION (binding): every browser context is created by isolatedContext(), which installs the catch-all
// route `**/*` BEFORE any page exists and never removes or narrows it (no unroute/unrouteAll anywhere). A request is
// allowed through only when it is the loopback fixture server's own origin or a same-origin blob:; prayer requests are
// FULFILLED from tests/r0002-ordinary.json (re-dated) and every other request is ABORTED. Weather is answered in-page
// by an init-script fetch shim (no request is issued). Every request seen by the context is logged; the run FAILS
// (exit 3) if any non-loopback request was allowed through or any request bypassed the route.
// Runs per engine and scene: A = --index-a, B = --index-b, A2 = --index-a again (noise floor), Bp = --index-b with
// qaState() polled on every animation frame (observer-effect differential). Pass: diff(A2,B) <= diff(A,A2) and
// diff(B,Bp) <= diff(A,A2), per scene, same engine.
// Usage: node tools/qa/r0036_pixel_control.cjs --root <tree> --index-a <main index> --index-b <branch index> --out <dir>
//        --engine chromium|firefox|webkit [--playwright <pkg path>] [--scenes a,b]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium';
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
const LEDGER={seen:0,allowed:0,fulfilled:0,aborted:0,escapes:[],bypass:[],abortedHosts:{}};
const LOOPBACK=new Set(['127.0.0.1','localhost','[::1]']);
async function isolatedContext(browser,base,options){
 const ctx=await browser.newContext(options);const routed=new Set();
 await ctx.route('**/*',route=>{const req=route.request(),u=req.url();routed.add(req);LEDGER.seen++;
  let host=null;try{host=new URL(u).hostname;}catch{}
  if(u.startsWith(base+'/')||(u.startsWith('blob:'+base+'/'))){LEDGER.allowed++;if(!LOOPBACK.has(host)&&!u.startsWith('blob:'))LEDGER.escapes.push(u);return route.continue();}
  const m=/^https:\/\/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m){LEDGER.fulfilled++;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});}
  LEDGER.aborted++;LEDGER.abortedHosts[host]=(LEDGER.abortedHosts[host]||0)+1;return route.abort();});
 // Every request the context issues must have passed the route (data: URLs are not network requests).
 ctx.on('request',req=>{const u=req.url();if(u.startsWith('data:'))return;setTimeout(()=>{if(!routed.has(req))LEDGER.bypass.push(u);},0);});
 return ctx;}
function shim(){return `(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000;
   return json({timezone:'${TZ}',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,
    current:{time:iso(m),interval:900,weather_code:0,temperature_2m:70,apparent_temperature:70,relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:0,precipitation:0,is_day:1,visibility:24000}});}
  return nf(input,init);};})();`;}
// Observer: a diagnostic read on every animation frame, from the first frame on.
const POLL=`(()=>{let n=0;const tick=()=>{try{if(typeof window.qaState==='function'){window.qaState();n++;}}catch(e){}window.__r36polls=n;requestAnimationFrame(tick);};requestAnimationFrame(tick);})();`;
const STATE=`(()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c');return {composed:!!c?.classList.contains('real-sky-composed'),status:s?.status??null,polls:window.__r36polls??0};})()`;
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&seed=1';
const LOWSUN='&simTime=16:50&simWx=2&simCloud=50&simHumid=80';
const SCENES=[['clear-noon','&simTime=12:30&simWx=0',true],['sunrise','&simTime=05:50&simWx=0',true],['sunset','&simTime=18:55&simWx=0',true],
 ['broken-low-sun-rays',LOWSUN,true],['overcast','&simTime=12:30&simWx=3&simCloud=100',true],['rain','&simTime=12:30&simWx=63&simPrecip=2',true],
 ['thunder-dusk','&simTime=18:40&simWx=95&simPrecip=5',true],['crescent-night','&simTime=19:30&simWx=0&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42',true],
 ['gibbous-night-cloud','&simTime=23:00&simWx=2&simCloud=30&simMoon=0.92&simWax=1&simMoonAlt=35&simMoonH=10',true],['near-fajr','&simTime=04:40&simWx=0',true]];
async function shoot(browser,base,[name,suffix,prayer],poll){
 const ctx=await isolatedContext(browser,base,{viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:TZ,locale:'en-US',reducedMotion:'reduce'});
 await ctx.addInitScript(shim());if(poll)await ctx.addInitScript(POLL);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(INSTANT)});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(base+'/index.html'+BASE+suffix);
 let s=null;const t0=Date.now();while(Date.now()-t0<30000){s=await page.evaluate(STATE);if(s.composed&&s.status==='ready')break;await page.waitForTimeout(250);}
 await page.waitForTimeout(2500);s=await page.evaluate(STATE);const png=await page.screenshot();await ctx.close();return {png,state:s,errors};}
async function diff(browser,base,x,y){const ctx=await isolatedContext(browser,base,{});const page=await ctx.newPage();
 const r=await page.evaluate(async([p,q])=>{const load=async s=>{const i=new Image();i.src='data:image/png;base64,'+s;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;const g=c.getContext('2d');g.drawImage(i,0,0);return g.getImageData(0,0,i.width,i.height);};
  const A=await load(p),B=await load(q);if(A.width!==B.width||A.height!==B.height)return {sizeMismatch:true};let n=0,max=0;
  for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {pixels:A.width*A.height,differing:n,maxChannelDelta:max};},[x.toString('base64'),y.toString('base64')]);
 await ctx.close();return r;}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const runs=[['A',path.resolve(a['index-a']),false],['B',path.resolve(a['index-b']),false],['A2',path.resolve(a['index-a']),false],['Bp',path.resolve(a['index-b']),true]];
 const browser=await PW[engine].launch({headless:true});const results=[];
 const meta={engine,version:browser.version(),indexA:sha(fs.readFileSync(runs[0][1])),indexB:sha(fs.readFileSync(runs[1][1]))};
 try{for(const scene of SCENES.filter(s=>!a.scenes||a.scenes.split(',').includes(s[0]))){const shot={};
   for(const [run,file,poll] of runs){indexFile=file;shot[run]=await shoot(browser,base,scene,poll);fs.writeFileSync(path.join(out,`${engine}-${scene[0]}-${run}.png`),shot[run].png);}
   const noise=await diff(browser,base,shot.A.png,shot.A2.png),change=await diff(browser,base,shot.A2.png,shot.B.png),observer=await diff(browser,base,shot.B.png,shot.Bp.png);
   const within=d=>d.differing<=noise.differing&&d.maxChannelDelta<=noise.maxChannelDelta;
   const row={scene:scene[0],sha:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,sha(o.png)])),noiseAvsA2:noise,changeA2vsB:change,observerBvsBp:observer,
    polls:shot.Bp.state.polls,composed:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.state.composed])),errors:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.errors])),
    pass:within(change)&&within(observer)&&shot.Bp.state.polls>0};
   results.push(row);console.log(JSON.stringify({scene:row.scene,noise:[noise.differing,noise.maxChannelDelta],change:[change.differing,change.maxChannelDelta],observer:[observer.differing,observer.maxChannelDelta],polls:row.polls,pass:row.pass}));}
 }finally{await browser.close();server.close();}
 await new Promise(r=>setTimeout(r,50));
 const isolation={...LEDGER,allowedNonLoopback:LEDGER.escapes.length,bypassed:LEDGER.bypass.length};
 fs.writeFileSync(path.join(out,`pixel-${engine}.json`),JSON.stringify({...meta,isolation,results},null,1));
 console.log(JSON.stringify({isolation:{seen:isolation.seen,allowed:isolation.allowed,fulfilled:isolation.fulfilled,aborted:isolation.aborted,abortedHosts:isolation.abortedHosts,allowedNonLoopback:isolation.allowedNonLoopback,bypassed:isolation.bypassed},allPass:results.every(r=>r.pass)}));
 if(isolation.allowedNonLoopback||isolation.bypassed){console.error('NETWORK ISOLATION FAILURE');process.exitCode=3;}
 else if(!results.every(r=>r.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
