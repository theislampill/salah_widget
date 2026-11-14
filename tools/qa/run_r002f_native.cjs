'use strict';
// R002F (issue 96) native boundary recipe: node tools/qa/run_r002f_native.cjs <playwright module dir> <tree> <out dir> [engines]
// Serves <tree> on loopback and drives its generated index.html across one Open-Meteo provider-step boundary with
// Playwright's clock (Date, timers, requestAnimationFrame and performance.now are all mocked) in Chromium, Firefox and
// WebKit. EVERY non-loopback request is route-stubbed: Aladhan from tests/r0002-ordinary.json, Open-Meteo by the
// upstream rule current.time = floor(server now, 15 min), interval 900, thunder with precipitation 2 mm and 95 %
// cloud, RainViewer an empty manifest; anything else is aborted. No provider is contacted. Two poll phases (the
// loop's ~30 s poll falls about 1 s and about 25 s after the boundary). Per 250 ms (4 fps) from B-5 s to B+60 s it
// records selection, deck readiness, cloud-canvas painted pixels, header text and particle/strike flags, plus
// whole-card PNG crops at B-1 s, B+0.5 s and the first sampled frame after re-establishment.
// Never uses qaState().clouds.hash. This is evidence under a stubbed provider, not a live-provider measurement.
const fs=require('fs'),path=require('path'),http=require('http');
const [pwDir,treeArg,outArg,engArg]=process.argv.slice(2);
if(!pwDir||!treeArg||!outArg) throw Error('usage: run_r002f_native.cjs <playwright> <tree> <out> [engines]');
const pw=require(pwDir), root=path.resolve(treeArg), out=path.resolve(outArg), engines=(engArg||'chromium,firefox,webkit').split(',');
fs.mkdirSync(out,{recursive:true});
const MIME={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm','.png':'image/png','.bin':'application/octet-stream','.css':'text/css','.svg':'image/svg+xml','.webp':'image/webp','.jpg':'image/jpeg'};
const srv=http.createServer((q,s)=>{const p=path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){s.writeHead(404);return s.end();}
  s.writeHead(200,{'content-type':MIME[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(s);});
const rec=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','tests','r0002-ordinary.json'),'utf8'));
const B=Date.parse('2026-09-07T09:00:00Z');                     // 12:00 Asia/Riyadh: the provider step 11:45 ends here
const iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
const LAG=+(process.env.R002F_NATIVE_LAG_MS||0);             // optional provider publication lag (early-renewal-miss cell)
const LOOK=`(()=>{const c=document.querySelector('.c'),cv=document.querySelector('.cloudcanvas');let painted=0;
  try{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;for(let i=3;i<d.length;i+=4)if(d[i])painted++;}catch(e){painted=-1;}
  const r=retryDiagnostics();return {now:Date.now(),sel:!!selectedWeather(),ready:_cloudReady,painted,wt:document.querySelector('#wt').textContent,
  wi:document.querySelector('#wi').textContent,precip:c.dataset.precip,lightning:c.dataset.lightning,step:weather&&weather.currentValidAt,
  seed:_cloudFieldSeed,population:_cloudMotion.population,renewal:r.renewal?r.renewal.stage:null};})()`;
async function run(engine,base,phaseS){
  const T0=B+phaseS*1000-150000;                                 // boot poll origin: polls at ~T0+30 s*k, one of them ~B+phase
  const b=await pw[engine].launch(); const c=await b.newContext({viewport:{width:325,height:530},timezoneId:'Asia/Riyadh',reducedMotion:'no-preference'});
  let pageNow=T0, page=null; const requests=[];
  // The provider stub reads the PAGE's mocked clock at request time (engines advance it slightly differently
  // from the runner's own step counter), so floor(server now, 15 min) is evaluated at the request's own instant.
  const pageClock=async()=>{ try{ return await page.evaluate(()=>Date.now()); }catch(e){ return pageNow; } };
  await c.route('**/*',async r=>{const u=r.request().url(); if(u.startsWith(base)) return r.continue();
    if(u.includes('api.aladhan.com')){const m=/timings\/(\d\d-\d\d-\d{4})/.exec(u);const x=JSON.parse(JSON.stringify(rec));x.meta.timezone='Asia/Riyadh';if(m)x.date.gregorian.date=m[1];
      return r.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify({code:200,status:'OK',data:x})});}
    if(u.includes('api.open-meteo.com')){const now=await pageClock();requests.push(now-B);const q=Math.floor((now-LAG)/900000)*900000,hr=q-q%3600000;
      const body={timezone:'Asia/Riyadh',elevation:600,current:{time:iso(q),interval:900,weather_code:95,temperature_2m:24,apparent_temperature:26,relative_humidity_2m:80,
        dew_point_2m:18,wind_speed_10m:6,wind_direction_10m:225,wind_gusts_10m:9,cloud_cover:95,cloud_cover_low:92,cloud_cover_mid:90,cloud_cover_high:60,precipitation:2,rain:2,showers:0,snowfall:0,is_day:1,visibility:10000},
        hourly:{time:[iso(hr),iso(hr+3600000),iso(hr+7200000)],temperature_2m:[24,24,24],weather_code:[95,95,95],cloud_cover:[95,95,95],precipitation:[2,2,2]}};
      return r.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(body)});}
    if(u.includes('api.rainviewer.com')) return r.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:'{"radar":{"past":[]}}'});
    return r.abort();});
  const p=await c.newPage(); page=p; const errors=[]; p.on('pageerror',e=>errors.push(String(e)));
  await p.clock.install({time:new Date(T0)}); await p.clock.pauseAt(new Date(T0+1000));   // paused: only runFor advances time (deterministic)
  await p.goto(base+'/index.html#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh');
  const step=async ms=>{await p.clock.runFor(ms);pageNow=await p.evaluate(()=>Date.now());};
  for(let i=0;i<40&&!(await p.evaluate(()=>{try{return window.eval('_loopStarted&&!!selectedWeather()')}catch(e){return false}}));i++) await step(250);
  const before=await p.evaluate(()=>window.eval('weather&&weather.currentValidAt'));
  pageNow=await p.evaluate(()=>Date.now()); await step(B-5000-pageNow);
  const samples=[],shots={};const tag=`${engine}-${path.basename(root)}-phase${phaseS}${LAG?"-lag"+LAG:""}`;
  while(pageNow<B+60000){ await step(250); const s=await p.evaluate(LOOK); s.t=s.now-B; samples.push(s);
    if(s.t>=-1000&&shots.before==null){shots.before=s.t;await p.screenshot({path:path.join(out,tag+'-before.png')});}
    if(s.t>=500&&shots.blink==null){shots.blink=s.t;await p.screenshot({path:path.join(out,tag+'-blink.png')});}
    if(s.t>0&&s.sel&&s.ready&&s.painted>0&&shots.after==null){shots.after=s.t;await p.screenshot({path:path.join(out,tag+'-after.png')});} }
  await b.close();
  const off=samples.find(s=>s.t>0&&!s.sel), on=off&&samples.find(s=>s.t>off.t&&s.sel&&s.ready&&s.painted>0);
  const header=off&&samples.find(s=>s.t>off.t&&s.wt!=='');
  const back=off&&samples.find(s=>s.t>off.t&&s.sel), gap=samples.filter(s=>off&&s.t>=off.t&&(!back||s.t<back.t));
  return {engine,tree:path.basename(root),phaseS,providerLagMs:LAG,recordStepBefore:before,requestsRelativeToB:requests.filter(t=>t>-200000),
    withdrawnAtMs:off?off.t:null,selectedAgainAtMs:back?back.t:null,deckBackAtMs:on?on.t:null,headerBackAtMs:header?header.t:null,
    withdrawnFramesShowNothing:gap.every(s=>s.painted===0&&!s.ready&&s.wt===''&&s.precip==='off'&&s.lightning==='off'),
    identityKept:!!(on&&samples[0].seed===on.seed&&samples[0].population===on.population),lightningEverOn:samples.some(s=>s.lightning==='on'),
    shots,pageErrors:errors,samples};
}
(async()=>{await new Promise(r=>srv.listen(0,'127.0.0.1',r)); const base='http://127.0.0.1:'+srv.address().port; const results=[];
  for(const engine of engines) for(const phaseS of [1,25]){ try{ const r=await run(engine,base,phaseS); results.push(r);
      fs.writeFileSync(path.join(out,`${engine}-${path.basename(root)}-phase${phaseS}${LAG?'-lag'+LAG:''}.json`),JSON.stringify(r,null,1));
      const {samples,...summary}=r; console.log(JSON.stringify(summary)); }
    catch(e){ console.log(JSON.stringify({engine,phaseS,error:String(e&&e.message||e)})); results.push({engine,phaseS,error:String(e)}); } }
  srv.close(); process.exit(results.some(r=>r.error)?2:0);
})().catch(e=>{console.error(e);process.exit(1);});
