'use strict';
// R003A same-tree pixel control (issue 124, R3A-07). Global Playwright; forced zone America/New_York; Playwright clock
// installed at a fixed instant; reduced motion with frozen simTime scenes; prayer fulfilled from tests/r0002-ordinary.json
// (re-dated), weather answered in-page from a fixture, every other non-loopback request aborted. No provider is contacted.
// One tree is served; only /index.html is swapped between the runs, because the generated index is the only served
// byte that differs between the compared commits (GENERATED.json and moon/BUILD.json are build metadata, never loaded).
// Runs per engine: A = --index-a, B = --index-b, A2 = --index-a again (the run-to-run noise floor). Each scene's card
// screenshot is diffed pixel by pixel in the same engine: A vs A2 (noise) and A vs B (change).
// Usage: node tools/qa/r003a_pixel_control.cjs --root <tree> --index-a <main index.html> --index-b <branch index.html>
//        --out <fresh dir> --engine chromium|firefox|webkit [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium';
fs.mkdirSync(out,{recursive:true});
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='America/New_York';
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
   return json({timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,
    current:{time:iso(m),interval:900,weather_code:W.code,temperature_2m:70,apparent_temperature:70,relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:W.cloud,precipitation:0,is_day:W.isDay,visibility:24000}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;}
const STATE=`(()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c');return {composed:!!c?.classList.contains('real-sky-composed'),status:s?.status??null,
 pending:!!c?.classList.contains('sky-pending'),optics:Object.fromEntries(['--ray','--anticrep','--sunhalo','--sundogs','--sunpillar','--sunray'].map(k=>[k,c?.style.getPropertyValue(k)??null]))};})()`;
const BASE='#lat=28.5383&lon=-81.3792&label=Central%20FL&method=2&tz=America%2FNew_York&seed=1';
const SCENES=[['clear-noon','&simTime=12:30&simWx=0',true],['sunrise','&simTime=06:58&simWx=0',true],['sunset','&simTime=17:25&simWx=0',true],
 ['broken','&simTime=12:30&simWx=2&simCloud=50',true],['overcast','&simTime=12:30&simWx=3&simCloud=100',true],
 ['night-moon','&simTime=19:30&simWx=0&simMoon=0.5&simWax=1&simMoonAlt=30&simMoonH=30',true],
 ['no-timetable-day','&simTime=12:30&simWx=2&simCloud=50',false]];
async function shoot(browser,base,[name,suffix,prayer]){
 const ctx=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'America/New_York',locale:'en-US',reducedMotion:'reduce'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m&&prayer)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(shim({code:0,cloud:0,isDay:1}));
 const page=await ctx.newPage();await page.clock.install({time:Date.parse('2026-11-13T17:00:00Z')});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(base+'/index.html'+BASE+suffix);
 let s=null;const t0=Date.now();while(Date.now()-t0<30000){s=await page.evaluate(STATE);if(s.composed&&s.status==='ready')break;await page.waitForTimeout(250);}
 await page.waitForTimeout(2500);s=await page.evaluate(STATE);const png=await page.screenshot();await ctx.close();
 return {png,state:s,errors,aborted:[...new Set(aborted)]};}
async function diff(browser,x,y){const ctx=await browser.newContext();const page=await ctx.newPage();
 const r=await page.evaluate(async([p,q])=>{const load=async s=>{const i=new Image();i.src='data:image/png;base64,'+s;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;const g=c.getContext('2d');g.drawImage(i,0,0);return g.getImageData(0,0,i.width,i.height);};
  const A=await load(p),B=await load(q);if(A.width!==B.width||A.height!==B.height)return {sizeMismatch:true};let n=0,max=0;
  for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {pixels:A.width*A.height,differing:n,maxChannelDelta:max};},[x.toString('base64'),y.toString('base64')]);
 await ctx.close();return r;}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const runs={A:path.resolve(a['index-a']),B:path.resolve(a['index-b']),A2:path.resolve(a['index-a'])};
 const browser=await PW[engine].launch({headless:true});const results=[];
 try{
  for(const scene of SCENES){const shot={};
   for(const [run,file] of Object.entries(runs)){indexFile=file;shot[run]=await shoot(browser,base,scene);fs.writeFileSync(path.join(out,`${engine}-${scene[0]}-${run}.png`),shot[run].png);}
   const row={scene:scene[0],engine,indexA:sha(fs.readFileSync(runs.A)),indexB:sha(fs.readFileSync(runs.B)),
    sha:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,sha(o.png)])),noiseAvsA2:await diff(browser,shot.A.png,shot.A2.png),changeAvsB:await diff(browser,shot.A.png,shot.B.png),
    composed:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.state.composed])),optics:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.state.optics])),
    errors:Object.fromEntries(Object.entries(shot).map(([k,o])=>[k,o.errors])),aborted:[...new Set(Object.values(shot).flatMap(o=>o.aborted))]};
   results.push(row);console.log(JSON.stringify(row));}
  fs.writeFileSync(path.join(out,`pixel-control-${engine}.json`),JSON.stringify({engine,version:browser.version(),results},null,1));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
