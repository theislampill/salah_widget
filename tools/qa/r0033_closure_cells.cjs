'use strict';
// R0033 closure audit (issue 100): native observations for three acceptance rows whose recorded evidence did not
// cover the issue's own accepting observation (rows R33-17, R33-11 and R33-15; contract section 15.5).
// Every browser starts through tools/qa/r0033_isolation.cjs (refusing proxy, catch-all route and WebSocket route
// before any page, every request logged, exit 3 on any escape). Synthetic fixture only: lat 24.47, lon 39.61,
// Madinah, zone Asia/Riyadh; prayer fulfilled from a fixture, weather answered in-page from a fixture, radar refused
// in-page; no provider is contacted. Faults are injected from the harness (init scripts and the loopback server),
// never by editing a product file.
//   --cell neutrality --before <tree> --after <tree> --scene dayclear|halfcloud [--repeats 2]
//        R33-17: the same frozen scene served from two trees, alternating before/after, each load in a fresh
//        context; card PNGs compared pixel by pixel (differing pixels, maximum channel delta). Repeats of the same
//        tree give the determinism control. Page facts are read from the DOM only (no runtime getter, so the older
//        tree's adopting getters are never called by the recipe).
//   --cell twotier --root <tree> --variant recover|terminal
//        R33-11: the initial tier's render throws (wrapped receiver, armed by an init script) while the Moon assets
//        answer 404 (no-store), so both tiers fail. recover: the initial throw is disarmed, the initial tier's own
//        re-attempt (after 60 s, mocked clock) must restore the disc while the worker is still failing, then the
//        assets return and the worker's automatic attempt reaches the terrain. terminal: both keep failing until
//        both budgets are spent (the DG-1 = B outcome: no disc, no moonlight).
//   --cell cloudlight --root <tree>
//        R33-15: a cloudy night (simWx=2, simCloud=50, half Moon). A: healthy, Moon at +20 deg (surface presented).
//        B, B2: construction failure (no runtime, no surface), Moon at +20 deg. C: construction failure, Moon at
//        -20 deg (no lunar light by physics either). B vs C equal means no lunar light reaches sky, clouds or stars
//        without a surface; A vs B is the positive control.
// Moon facts are read through SalahMoonRuntime.observe() and qaState() only (non-adopting since R0036) in
// twotier and cloudlight, which run on the current tree.
// Usage: node tools/qa/r0033_closure_cells.cjs --cell <c> (--root <tree> | --before <tree> --after <tree>
//        [--before-label <commit>] [--after-label <commit>]) --out <dir> --engine <chromium|firefox|webkit> [--scene s] [--variant v] [--repeats n] [--playwright <pkg>]
// Output: one JSON line on stdout (with the isolation verdict), <out>/result.json, PNGs and
// <out>/<cell>-<engine>-requests.json. Exit 0 complete, 1 error, 2 INCOMPLETE, 3 isolation escape (overrides every
// other code), 4 FAIL (complete, and the accepting observation does not hold).
require('./v1_net_guard.cjs').install();                                  // before any other module can connect
const iso=require('./r0033_isolation.cjs');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),zlib=require('node:zlib'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),out=path.resolve(a.out),engine=a.engine||'chromium',cell=a.cell;
fs.mkdirSync(out,{recursive:true});
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.gz':'application/octet-stream','.bin':'application/octet-stream','.woff2':'font/woff2'};
const MOON_ASSETS=['/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
// One loopback server per served tree. Moon asset policy: serve | stall (held open: the initial tier presents, the
// refinement never starts, as in the first slice's `scenes` cell) | 404 (no-store).
function serveTree(root){const st={root:path.resolve(root),assets:'serve',served:[],held:[]};
 st.server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(st.root,decodeURIComponent(u.pathname)));
  const asset=MOON_ASSETS.includes(u.pathname);if(asset)st.served.push({path:u.pathname,policy:st.assets,at:Date.now()});
  if(asset&&st.assets==='stall'){st.held.push(res);return;}
  if(asset&&st.assets==='404'){res.writeHead(404,{'cache-control':'no-store'});return res.end();}
  if(!p.startsWith(st.root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':asset?'max-age=3600':'no-store'});fs.createReadStream(p).pipe(res);});
 st.listen=()=>new Promise(r=>st.server.listen(0,'127.0.0.1',()=>{st.base='http://127.0.0.1:'+st.server.address().port;r(st);}));
 st.close=()=>{for(const r of st.held)try{r.destroy();}catch{}return new Promise(r=>st.server.close(()=>r()));};return st;}
const prayer=day=>{const [d,m,y]=day.split('-').map(Number);return {timings:{Fajr:'04:47',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Maghrib:'18:33',Sunset:'18:33',Isha:'20:03'},
 meta:{timezone:'Asia/Riyadh',method:{id:4,params:{Fajr:18.5,Isha:'90 min'}}},date:{gregorian:{date:day,day:String(d).padStart(2,'0'),month:{number:m,en:'September'},year:String(y)},hijri:{day:'26',month:{number:3,en:'Rabi'},year:'1448'}}};};
const fixture=u=>{const m=u.hostname==='api.aladhan.com'&&/\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u.pathname);return m?{code:200,status:'OK',data:prayer(m[1])}:null;};
// In-page weather fixture (clear, the sim* parameters set the scene) and radar refusal: neither request leaves the page.
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},f);
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({timezone:'Asia/Riyadh',utc_offset_seconds:10800,elevation:600,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:24,apparent_temperature:24,relative_humidity_2m:40,dew_point_2m:10,wind_speed_10m:3,wind_direction_10m:90,wind_gusts_10m:5,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,is_day:0,visibility:24000},
    hourly:{time:t,temperature_2m:arr(()=>24),weather_code:arr(()=>0),precipitation:arr(()=>0),cloud_cover:arr(()=>0),relative_humidity_2m:arr(()=>40),wind_speed_10m:arr(()=>3),visibility:arr(()=>24000),is_day:arr(()=>0)}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;
// Construction failure (the seam of tools/qa/r0033_native_cells.cjs): the Moon wrapper's own 250 ms poll interval
// throws once. Installed after the Playwright clock, whose init script replaces setInterval.
const CONSTRUCTION=`(()=>{const si=window.setInterval;let armed=true;window.setInterval=function(f,ms,...r){if(armed&&ms===250&&document.currentScript?.id==='moon-initial-code'){armed=false;throw new Error('r0033-injected Moon construction failure');}return si.call(this,f,ms,...r);};})();`;
// Initial-tier render failure: the generated wrapper assigns window.SalahMoonInitial once; the setter replaces the
// frozen receiver by an equally frozen one with the same identity whose render() throws while armed. The head and
// the runtime both call that render(). window.__r0033Initial = {armed, throws}.
const INITIAL_THROW=`(()=>{const R=window.__r0033Initial={armed:true,throws:0};let held;
 Object.defineProperty(window,'SalahMoonInitial',{configurable:true,enumerable:true,get(){return held;},set(v){
  if(v&&typeof v.render==='function'){const render=v.render;held=Object.freeze({identity:v.identity,render(...x){if(R.armed){R.throws++;throw new Error('r0033-injected initial render failure');}return render.apply(v,x);}});}else held=v;}});})();`;
const HASH='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1';
const SCENES={dayclear:{hash:HASH+'&simTime=12:30&simWx=0',night:false},
 halfcloud:{hash:HASH+'&simTime=22:00&simWx=2&simCloud=50&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42',night:true}};
const CLOCK='2026-09-08T19:00:00Z';
async function open(S,st,hash,{inits=[]}={}){
 const C=await S.context({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'Asia/Riyadh',locale:'en-US',reducedMotion:'reduce'},{origin:st.base,fixture});
 await C.context.addInitScript(SHIM);
 const page=await C.newPage();await page.clock.install({time:Date.parse(CLOCK)});await page.clock.resume();
 for(const s of inits)await page.addInitScript(s);
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(st.base+'/index.html'+hash);return {context:C.context,page,errors};}
// DOM-only facts (every tree): classes and the CSS custom properties of the card.
const DOM=`(()=>{const c=document.querySelector('.c'),cs=getComputedStyle(c),ph=document.querySelector('.mphoto')?.getBoundingClientRect();
 return {moonReady:c.classList.contains('moon-ready'),composed:c.classList.contains('real-sky-composed'),skyPending:c.classList.contains('sky-pending'),
  maskOn:!!document.querySelector('.moon-mask-disc')?.classList.contains('mask-on'),moonbeam:cs.getPropertyValue('--moonbeam').trim(),moongrp:cs.getPropertyValue('--moongrp').trim(),
  moonocc:cs.getPropertyValue('--moonocc').trim(),disc:ph?{x:ph.x,y:ph.y,w:ph.width,h:ph.height}:null,constructionError:window.SalahMoonConstructionError??null};})()`;
// Runtime facts (current tree only): observe() and qaState() are pure reads there (R0036).
const RT=`(()=>{const o=window.SalahMoonRuntime?.observe?.()??null,s=o?.state??null,t=window.qaState?.()?.moonTruth??null;
 return {registered:!!window.SalahMoonRuntime,current:o?.current??null,wouldPresent:o?.wouldPresent??null,status:s?.status??null,visibleSource:s?.visibleSource??null,workerAlive:s?.workerAlive??null,
  recovery:s?.recovery??null,initialRetry:s?.initialRetry??null,initialEligible:s?.initialEligible??null,initialError:s?.initialError??null,retryCount:s?.retryCount??null,errors:(s?.errors??[]).slice(-4),
  moonTruth:t?{displayMode:t.displayMode,reason:t.reason,moonlightOpacity:t.moonlightOpacity,calendarMoonVisible:t.calendarMoonVisible,lunarLight:t.lunarLight??null}:null,
  injected:window.__r0033Initial?{armed:window.__r0033Initial.armed,throws:window.__r0033Initial.throws}:null};})()`;
const dom=page=>page.evaluate(DOM),rt=page=>page.evaluate(RT);
const facts=async page=>({...await dom(page),...await rt(page)});
async function until(page,read,pred,ms,step=250){const t0=Date.now();let f=null;while(Date.now()-t0<ms){f=await read(page);if(pred(f))return {ok:true,f,ms:Date.now()-t0};await page.waitForTimeout(step);}return {ok:false,f,ms:Date.now()-t0};}
// Minimal PNG decoder (8-bit greyscale/RGB/RGBA, non-interlaced: what the engines' screenshots produce).
function decodePng(buf){let o=8,w=0,h=0,type=0,depth=0,inter=0;const idat=[];
 while(o<buf.length){const len=buf.readUInt32BE(o),t=buf.toString('latin1',o+4,o+8),d=buf.subarray(o+8,o+8+len);o+=12+len;
  if(t==='IHDR'){w=d.readUInt32BE(0);h=d.readUInt32BE(4);depth=d[8];type=d[9];inter=d[12];}else if(t==='IDAT')idat.push(d);else if(t==='IEND')break;}
 if(depth!==8||inter!==0||![0,2,4,6].includes(type))throw Error('unsupported PNG '+JSON.stringify({depth,type,inter}));
 const ch={0:1,2:3,4:2,6:4}[type],stride=w*ch,raw=zlib.inflateSync(Buffer.concat(idat)),px=Buffer.alloc(w*h*4);let prev=Buffer.alloc(stride);
 for(let y=0;y<h;y++){const f=raw[y*(stride+1)],line=Buffer.from(raw.subarray(y*(stride+1)+1,(y+1)*(stride+1)));
  for(let i=0;i<stride;i++){const L=i>=ch?line[i-ch]:0,U=prev[i],UL=i>=ch?prev[i-ch]:0;let p=0;
   if(f===1)p=L;else if(f===2)p=U;else if(f===3)p=(L+U)>>1;else if(f===4){const q=L+U-UL,pa=Math.abs(q-L),pb=Math.abs(q-U),pc=Math.abs(q-UL);p=pa<=pb&&pa<=pc?L:pb<=pc?U:UL;}
   line[i]=(line[i]+p)&255;}
  for(let x=0;x<w;x++){const s=x*ch,d=(y*w+x)*4;if(ch===1||ch===2){px[d]=px[d+1]=px[d+2]=line[s];px[d+3]=ch===2?line[s+1]:255;}else{px[d]=line[s];px[d+1]=line[s+1];px[d+2]=line[s+2];px[d+3]=ch===4?line[s+3]:255;}}
  prev=line;}
 return {w,h,px};}
// Pixel comparison over the whole image or a rectangle: differing pixels (any channel) and the maximum channel delta.
function diff(A,B,rect=null){const a=decodePng(A),b=decodePng(B);if(a.w!==b.w||a.h!==b.h)return {sizeMismatch:[a.w,a.h,b.w,b.h]};
 const r=rect?{x0:Math.max(0,Math.floor(rect.x)),y0:Math.max(0,Math.floor(rect.y)),x1:Math.min(a.w,Math.ceil(rect.x+rect.w)),y1:Math.min(a.h,Math.ceil(rect.y+rect.h))}:{x0:0,y0:0,x1:a.w,y1:a.h};
 let n=0,max=0,total=0;for(let y=r.y0;y<r.y1;y++)for(let x=r.x0;x<r.x1;x++){total++;const i=(y*a.w+x)*4;let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(a.px[i+k]-b.px[i+k]));if(d){n++;if(d>max)max=d;}}
 return {pixels:total,differingPixels:n,maxChannelDelta:max};}
// Mean RGB of a rectangle, excluding an optional rectangle (the disc box).
function meanRgb(png,rect,exclude=null){const a=decodePng(png),s=[0,0,0];let n=0;
 for(let y=Math.max(0,rect.y);y<Math.min(a.h,rect.y+rect.h);y++)for(let x=Math.max(0,rect.x);x<Math.min(a.w,rect.x+rect.w);x++){
  if(exclude&&x>=exclude.x&&x<exclude.x+exclude.w&&y>=exclude.y&&y<exclude.y+exclude.h)continue;const i=(y*a.w+x)*4;for(let k=0;k<3;k++)s[k]+=a.px[i+k];n++;}
 return {pixels:n,mean:s.map(x=>+(x/n).toFixed(3))};}
async function shot(page,name,rect=null){const png=await page.screenshot();fs.writeFileSync(path.join(out,name+'.png'),png);
 let crop=null;if(rect){const pad=14,clip={x:Math.max(0,rect.x-pad),y:Math.max(0,rect.y-pad),width:Math.min(325,rect.w+2*pad),height:Math.min(200,rect.h+2*pad)};crop=await page.screenshot({clip});fs.writeFileSync(path.join(out,name+'-moon.png'),crop);}
 return {png,file:name+'.png',sha256:sha(png),cropFile:crop?name+'-moon.png':null,cropSha256:crop?sha(crop):null};}
const settle=(scene)=>f=>f.composed&&!f.skyPending&&(!scene.night||f.moonReady);
(async()=>{const trees=[];let S=null,incomplete=false,failed=false,result={};
 const emit=o=>{const line={cell,engine,version:S?.browser.version()??null,...o,isolation:S?S.verdict():null};fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(line,null,1));console.log(JSON.stringify(line));};
 try{
  S=await iso.launch(PW,engine);
  if(cell==='neutrality'){
   const scene=SCENES[a.scene];if(!scene)throw Error('--scene dayclear|halfcloud');const repeats=Number(a.repeats||2);
   const sides={before:await serveTree(a.before).listen(),after:await serveTree(a.after).listen()};trees.push(sides.before,sides.after);
   for(const st of Object.values(sides))st.assets='stall';
   const loads=[];
   // Repeat 0 is the first load of each tree in this browser (warm-up): recorded and compared, but the verdict uses
   // repeats 1..n only (a first load in a fresh browser was seen to differ from every later load of the same tree).
   for(let r=0;r<=repeats;r++)for(const side of ['before','after']){
    const o=await open(S,sides[side],scene.hash),w=await until(o.page,dom,settle(scene),90000);await o.page.waitForTimeout(3000);
    const f=await dom(o.page),s=await shot(o.page,`${a.scene}-${side}-${r}`,scene.night?f.disc:null);
    loads.push({side,repeat:r,settled:w.ok,settleMs:w.ms,facts:f,file:s.file,sha256:s.sha256,cropFile:s.cropFile,errors:o.errors,png:s.png,disc:f.disc});await o.context.close();}
   const pick=(side,r)=>loads.find(l=>l.side===side&&l.repeat===r);
   const cmp=(x,y)=>({a:x.file,b:y.file,card:diff(x.png,y.png),moon:x.disc?diff(x.png,y.png,{x:x.disc.x-14,y:x.disc.y-14,w:x.disc.w+28,h:x.disc.h+28}):null});
   const comparisons={beforeVsAfter:[],beforeRepeat:[],afterRepeat:[],warmup:[cmp(pick('before',0),pick('after',0)),cmp(pick('before',0),pick('before',1)),cmp(pick('after',0),pick('after',1))]};
   for(let r=1;r<=repeats;r++)comparisons.beforeVsAfter.push(cmp(pick('before',r),pick('after',r)));
   for(let r=2;r<=repeats;r++){comparisons.beforeRepeat.push(cmp(pick('before',1),pick('before',r)));comparisons.afterRepeat.push(cmp(pick('after',1),pick('after',r)));}
   incomplete=loads.some(l=>!l.settled);
   const noise=[...comparisons.beforeRepeat,...comparisons.afterRepeat].reduce((m,c)=>Math.max(m,c.card.differingPixels??Infinity),0);
   const ba=comparisons.beforeVsAfter.reduce((m,c)=>Math.max(m,c.card.differingPixels??Infinity),0);
   failed=!incomplete&&ba>noise;
   result={scene:a.scene,hash:scene.hash,clock:CLOCK,moonAssets:'stall (initial tier only, as the scenes cell)',trees:{before:a['before-label']??'before',after:a['after-label']??'after'},
    loads:loads.map(({png,...l})=>l),comparisons,repeatNoiseDifferingPixels:noise,beforeVsAfterDifferingPixels:ba,
    verdict:incomplete?'INCOMPLETE':failed?'DIFFERENT':ba===0?'IDENTICAL':'WITHIN-REPEAT-NOISE'};
  }else if(cell==='twotier'){
   const st=await serveTree(a.root).listen();trees.push(st);st.assets='404';const variant=a.variant||'recover',log=[];
   const o=await open(S,st,SCENES.halfcloud.hash.replace('&simWx=2&simCloud=50','&simWx=0'),{inits:[INITIAL_THROW]});
   const step=async(phase,ok,extra={})=>{const f=await facts(o.page);const s=await shot(o.page,`twotier-${variant}-${phase}`,f.disc);log.push({phase,ok,facts:f,shot:{file:s.file,sha256:s.sha256,cropFile:s.cropFile},...extra});return f;};
   const both=await until(o.page,facts,f=>f.recovery?.state==='scheduled'&&['waiting','exhausted'].includes(f.initialRetry?.state)&&f.composed,120000);
   await step('both-failed',both.ok);
   if(variant==='recover'){
    await o.page.evaluate(()=>{window.__r0033Initial.armed=false;});
    await o.page.clock.fastForward(61000);
    // Wait until the disc is back AND the worker's first automatic attempt (due at 30 s, assets still 404) has failed:
    // the slot is then filled by the initial tier alone while the refinement worker is down.
    const back=await until(o.page,facts,f=>f.moonReady&&f.current&&f.recovery?.attempts>=1&&f.status==='unavailable'&&!f.workerAlive,90000);
    const f1=await step('initial-tier-recovered-worker-failing',back.ok,{servedAssetRequests:st.served.length});
    st.assets='serve';await o.page.clock.fastForward(121000);
    const terr=await until(o.page,facts,f=>f.visibleSource==='refined-terrain'||f.visibleSource==='terrain-preview',300000,1000);
    const f2=await step('worker-recovered',terr.ok,{servedAssetRequests:st.served.length});
    incomplete=!(both.ok&&back.ok&&terr.ok);
    const accept={slotEmptyWhileBothFailed:!log[0].facts.moonReady,initialReattemptRestoredDisc:f1.moonReady&&f1.current&&f1.visibleSource==='initial-v5',workerFailedAgainMeanwhile:f1.recovery?.attempts>=1&&f1.status==='unavailable'&&!f1.workerAlive,
     lightWithDisc:Number(f1.moonbeam)>0,noLightWithoutDisc:Number(log[0].facts.moonbeam)===0&&log[0].facts.moonTruth?.lunarLight?.eligible===false,terrainReturned:terr.ok,noDriverRetry:f2.retryCount===0};
    failed=!incomplete&&!Object.values(accept).every(Boolean);result={variant,log,accept};
   }else{
    for(let i=0;i<3;i++){await o.page.clock.fastForward(61000);await o.page.waitForTimeout(1500);}
    await o.page.clock.fastForward(11*60000);await o.page.waitForTimeout(1500);await o.page.clock.fastForward(2*3600000);await o.page.waitForTimeout(3000);
    const end=await until(o.page,facts,f=>f.recovery?.state==='exhausted'&&f.initialRetry?.state==='exhausted',30000);
    const f=await step('both-exhausted',end.ok,{servedAssetRequests:st.served.length});incomplete=!end.ok;
    const accept={noDisc:!f.moonReady,noMoonbeam:Number(f.moonbeam)===0,lightIneligible:f.moonTruth?.lunarLight?.eligible===false,reason:f.moonTruth?.lunarLight?.reason??null,
     initialExhausted:f.initialRetry?.state==='exhausted',workerExhausted:f.recovery?.state==='exhausted',noWorker:!f.workerAlive};
    failed=!incomplete&&!(accept.noDisc&&accept.noMoonbeam&&accept.lightIneligible&&accept.initialExhausted&&accept.workerExhausted&&accept.noWorker);result={variant,log,accept};
   }
   result.errors=o.errors;await o.context.close();
  }else if(cell==='cloudlight'){
   const st=await serveTree(a.root).listen();trees.push(st);st.assets='stall';
   const base=SCENES.halfcloud.hash,below=base.replace('&simMoonAlt=20','&simMoonAlt=-20');
   const plan=[['A-surface-alt20',base,[]],['B-nosurface-alt20',base,[CONSTRUCTION]],['B2-nosurface-alt20',base,[CONSTRUCTION]],['C-nosurface-alt-20',below,[CONSTRUCTION]]];
   const loads={};
   for(const [name,hash,inits] of plan){const o=await open(S,st,hash,{inits});const healthy=!inits.length;
    const w=await until(o.page,facts,f=>f.composed&&!f.skyPending&&(!healthy||f.moonReady),90000);await o.page.waitForTimeout(3000);
    const f=await facts(o.page),s=await shot(o.page,'cloudlight-'+name,f.disc);loads[name]={settled:w.ok,facts:f,file:s.file,sha256:s.sha256,cropFile:s.cropFile,png:s.png,errors:o.errors};await o.context.close();}
   const L=loads,disc=L['A-surface-alt20'].facts.disc,sky={x:0,y:0,w:325,h:260},box=disc?{x:Math.floor(disc.x-14),y:Math.floor(disc.y-14),w:Math.ceil(disc.w+28),h:Math.ceil(disc.h+28)}:null;
   const comparisons={'B-vs-B2 (repeat)':diff(L['B-nosurface-alt20'].png,L['B2-nosurface-alt20'].png),'B-vs-C (no surface: Moon up vs Moon below)':diff(L['B-nosurface-alt20'].png,L['C-nosurface-alt-20'].png),
    'A-vs-B (positive control: surface vs none)':diff(L['A-surface-alt20'].png,L['B-nosurface-alt20'].png),'A-vs-B outside the disc box, upper sky':box?diff(L['A-surface-alt20'].png,L['B-nosurface-alt20'].png,{x:0,y:box.y+box.h,w:325,h:260-(box.y+box.h)}):null};
   const means=Object.fromEntries(Object.entries(L).map(([k,l])=>[k,meanRgb(l.png,sky,box)]));
   incomplete=Object.values(L).some(l=>!l.settled);
   const lightOf=k=>L[k].facts.moonTruth?.lunarLight,B=lightOf('B-nosurface-alt20'),A=lightOf('A-surface-alt20');
   const accept={noSurfaceNoLight:B?.eligible===false&&Number(L['B-nosurface-alt20'].facts.moonbeam)===0,noSurfaceReason:B?.reason??null,noDiscWithoutSurface:!L['B-nosurface-alt20'].facts.moonReady,
    pixelsNoSurfaceUpEqualBelow:comparisons['B-vs-C (no surface: Moon up vs Moon below)'].differingPixels<=comparisons['B-vs-B2 (repeat)'].differingPixels,
    positiveControlLit:A?.eligible===true&&Number(L['A-surface-alt20'].facts.moonbeam)>0,positiveControlDiffers:comparisons['A-vs-B (positive control: surface vs none)'].differingPixels>0};
   failed=!incomplete&&!(accept.noSurfaceNoLight&&accept.noDiscWithoutSurface&&accept.pixelsNoSurfaceUpEqualBelow&&accept.positiveControlLit&&accept.positiveControlDiffers);
   result={scene:base,clock:CLOCK,moonAssets:'stall',loads:Object.fromEntries(Object.entries(L).map(([k,{png,...l}])=>[k,l])),comparisons,skyBandMeanRgbExcludingDiscBox:{rect:sky,excluded:box,means},accept};
  }else throw Error('unknown cell '+cell);
  emit({result:incomplete?'INCOMPLETE':failed?'FAIL':'COMPLETE',...result});
 }catch(e){emit({error:String(e.stack||e).slice(0,800)});process.exitCode=1;}
 finally{if(S){await S.settle();fs.writeFileSync(path.join(out,`${cell}-${engine}-requests.json`),JSON.stringify({cell,engine,verdict:S.verdict(),served:trees.map(t=>({base:t.base,assets:t.served})),requests:S.ledger.requests},null,1));await S.close();}
  for(const t of trees)await t.close();}
 const verdict=S?S.verdict():{ok:true};if(!verdict.ok){console.error('ISOLATION ESCAPE '+JSON.stringify(verdict.escapes));process.exitCode=3;}else if(!process.exitCode&&failed)process.exitCode=4;else if(!process.exitCode&&incomplete)process.exitCode=2;
})();
