'use strict';
// R0036 V1 browser verification under enforced network isolation (issue 103, owner decision 2026-11-16).
// An equivalent runner of tests/v1_browser.py on the repository's existing Node Playwright: Python Playwright is not
// installed and is not downloaded. tests/v1_browser.py stays in place unchanged; every assertion it makes is executed
// here one-for-one under the id of its source line (A<line>), with the same expected values; the mapping is in
// docs/state-contracts/R0036.md §12. Differences, all stated: (1) fonts come from a deterministic offline fixture
// (tools/qa/v1_browser_helpers.py font) instead of a Python urlopen to Google Fonts; (2) each assertion is recorded
// and the run continues (the original stops at the first failure), so every row gets PASS / FAIL / NOT RUN;
// (3) the browser is Playwright's bundled Chromium unless --chromium names another executable.
// ISOLATION. Node side: tools/qa/v1_net_guard.cjs is installed before anything else (non-loopback connect/DNS/
// http(s)/fetch/WebSocket refused and logged; proxy variables removed). Python side: the helpers install
// tools/qa/v1_net_guard.py first. Browser side: Chromium starts with a REFUSING loopback proxy (every non-loopback
// connection, including a redirect the route never sees and an IP literal, is refused there before any outbound
// connection and logged) and a host-resolver rule that resolves nothing but 127.0.0.1; every context gets the catch-all route `**/*` and a catch-all WebSocket route BEFORE
// any page exists, neither is ever removed; only the loopback fixture origin and same-origin blob:/data: continue;
// providers are fulfilled from the original fixtures, anything else is aborted; every request is logged; the run
// fails (exit 3) on any request allowed off loopback, any request or WebSocket that bypassed the routes, or any
// Node/Python-side refusal outside the self-test.
// Usage: node tools/qa/r0036_v1_browser.cjs --out <dir> [--mode verify|selftest] [--config original|root-current]
//        [--layout original|full] [--blocks scenes,geo,storage,replacement] [--playwright <pkg>] [--chromium <exe>] [--root <tree>]
const guard=require('./v1_net_guard.cjs');guard.install();                   // before any other module can connect
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http'),https=require('node:https'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),REPO=path.resolve(a.root||path.join(__dirname,'..','..')),out=path.resolve(a.out),mode=a.mode||'verify';
// --config original (default): the historical configuration of tests/v1_browser.py, unchanged.
// --config root-current (owner decision "R0036 current-widget verification", 2026-11-16): ROOT sessions only get the
// three setup corrections the current widget needs (prayer fixture with date.gregorian.date, an advancing mocked clock
// during the root's waits, real-sky/ and moon/ served); V1 sessions keep the original setup exactly. Assertions whose
// premise is root == V1 are recorded FORMALLY INAPPLICABLE with their observation and an independent R-check.
const config=a.config||'original',ROOT_CURRENT=config==='root-current',layout=ROOT_CURRENT?'full':(a.layout||'original');
const BLOCKS=new Set((a.blocks||'scenes,geo,storage,replacement').split(','));
const ROOT_MUTANT=a['root-mutant']||null;   // test-only mutation of the STAGED root copy (tools/qa/r0036_v1_root_mutants.cjs)
const HELPERS=path.join(__dirname,'v1_browser_helpers.py');
fs.mkdirSync(out,{recursive:true});
// ---- verbatim constants of tests/v1_browser.py (L25-L29) ----
const FONT_CSS="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap";
const SETTINGS={"v":1,"lat":24.47,"lon":39.61,"tz":"Asia/Riyadh","label":"Madinah","method":"4","school":"0","time":"24","datefmt":"YYYY-MM-DD","units":"c","lp":0,"seed":1,"source":"manual","savedAt":1791345600000};
const ROOT_KEY="salah_widget:config:v1";
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
// ---- offline font fixture (replaces fonts() L36-L50, the only Python-side network touch) ----
const FONT_URL='https://fonts.gstatic.com/s/r0036fixture/v1/fixture.ttf';
const FIXTURE_CSS=[['Fraunces','400 700'],['Inter','400'],['Inter','500'],['Inter','600']].map(([f,w])=>
  `@font-face{font-family:'${f}';font-style:normal;font-weight:${w};font-display:swap;src:url(${FONT_URL}) format('truetype');}`).join('\n')+'\n';
function py(args){const r=spawnSync('python',['-I',HELPERS,...args],{encoding:'utf8',env:{...process.env}});
  if(r.status!==0)throw new Error('python helper failed: '+args[0]+' '+r.stderr);const o=JSON.parse(r.stdout.trim().split('\n').pop());
  if(args[0]!=='selftest'&&Array.isArray(o.refused))PY_REFUSED.push(...o.refused);return o;}
const PY_REFUSED=[];                                                       // Python-side refusals outside the self-test fail the run
// ---- verbatim provider fixture of tests/v1_browser.py fixture() L53-L68 ----
// root-current only: the current widget admits a prayer record only when it names the requested day
// (src/native/index.html L1263 `data.date.gregorian.date!==day` -> refused; L2568 the same identity on use). The added
// field is the DD-MM-YYYY segment of the requested URL; every other value is the original fixture's.
function fixtureFor(url,night,rootCurrent){const body=fixture(url,night);
  if(rootCurrent&&new URL(url).hostname==='api.aladhan.com')body.data.date.gregorian.date=new URL(url).pathname.replace(/\/+$/,'').split('/').pop();
  return body;}
function fixture(url,night){
  const u=new URL(url),host=u.hostname;
  if(host==='api.aladhan.com'){const day=parseInt(u.pathname.replace(/\/+$/,'').split('/').pop().split('-')[0],10);
    return {"code":200,"data":{"timings":{"Fajr":"05:00","Sunrise":"06:15","Dhuhr":"12:15","Asr":"15:40","Maghrib":"18:15","Sunset":"18:15","Isha":"19:45"},"meta":{"timezone":"Asia/Riyadh"},"date":{"gregorian":{"day":String(day),"month":{"number":10,"en":"October"},"year":"2026"},"hijri":{"day":String(day+17),"month":{"number":4,"en":"Rabi al-Thani"},"year":"1448"}}}};}
  if(host==='api.open-meteo.com')return {"elevation":620,"current":{"weather_code":2,"temperature_2m":28,"apparent_temperature":28,"relative_humidity_2m":45,"dew_point_2m":14,"wind_speed_10m":2,"wind_direction_10m":45,"wind_gusts_10m":3,"cloud_cover":30,"cloud_cover_low":5,"cloud_cover_mid":20,"cloud_cover_high":15,"precipitation":0,"rain":0,"showers":0,"snowfall":0,"visibility":30000,"is_day":night?0:1}};
  if(host==='api.rainviewer.com')return {"host":"https://tilecache.rainviewer.com","radar":{"past":[]}};
  if(host==='get.geojs.io')return {"latitude":"24.47","longitude":"39.61","city":"Madinah","country":"Saudi Arabia","country_code":"SA","timezone":"Asia/Riyadh"};
  if(host==='ipinfo.io')return {"loc":"24.47,39.61","city":"Madinah","country":"SA","timezone":"Asia/Riyadh"};
  if(host==='nominatim.openstreetmap.org')return [{"lat":"24.47","lon":"39.61","class":"place","address":{"city":"Madinah","country":"Saudi Arabia","country_code":"sa"}}];
  throw new Error('Unplanned external request: '+url);
}
// ---- isolation ledger ----
const LEDGER={seen:0,continued:0,allowedOffLoopback:[],fulfilledFixture:0,fulfilledFont:0,aborted:[],unplanned:[],bypassed:[],websockets:[],wsBypassed:[]};
const LOOP=new Set(['127.0.0.1','localhost','[::1]','::1']);
const hostOf=u=>{try{return new URL(u).hostname;}catch{return null;}};
// Refusing loopback proxy: every browser connection that is not to loopback (a redirect the route never saw, an IP
// literal, anything else) goes to this proxy, which refuses it BEFORE any outbound connection and logs it. Chromium
// bypasses the proxy only for loopback (its implicit rule). The resolver rule stays as a second layer.
const PROXY_REFUSED=[];let PROXY_PORT=0;
const proxy=http.createServer((req,res)=>{PROXY_REFUSED.push({kind:'http',target:req.url,at:Date.now()});res.writeHead(403);res.end('R0036 isolation');});
proxy.on('connect',(req,sock)=>{PROXY_REFUSED.push({kind:'connect',target:req.url,at:Date.now()});sock.end('HTTP/1.1 403 Forbidden\r\n\r\n');});
proxy.on('upgrade',(req,sock)=>{PROXY_REFUSED.push({kind:'upgrade',target:req.url,at:Date.now()});sock.destroy();});
const launchArgs=()=>['--proxy-server=http://127.0.0.1:'+PROXY_PORT,'--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1','--disable-background-networking','--disable-component-update','--disable-domain-reliability','--no-pings'];
const PROXY_ON=()=>launchArgs().some(x=>x.startsWith('--proxy-server=http://127.0.0.1:'));
async function isolatedContext(browser,origin,options,{night=false,font=null,rootCurrent=false}={}){
  const context=await browser.newContext(options);const routed=new WeakSet(),wsRouted=new Set();
  await context.route('**/*',route=>{const req=route.request(),url=req.url();routed.add(req);LEDGER.seen++;
    if(url.startsWith(origin+'/')||url.startsWith('blob:'+origin+'/')){LEDGER.continued++;if(!LOOP.has(hostOf(url))&&!url.startsWith('blob:'))LEDGER.allowedOffLoopback.push(url);return route.continue();}
    if(url===FONT_CSS){LEDGER.fulfilledFont++;return route.fulfill({body:FIXTURE_CSS,contentType:'text/css',headers:{'Access-Control-Allow-Origin':'*'}});}
    if(url===FONT_URL&&font){LEDGER.fulfilledFont++;return route.fulfill({body:font,contentType:'font/ttf',headers:{'Access-Control-Allow-Origin':'*'}});}
    let body;try{body=fixtureFor(url,night,rootCurrent);}catch(e){LEDGER.unplanned.push(url);LEDGER.aborted.push(url);return route.abort('blockedbyclient');}
    LEDGER.fulfilledFixture++;return route.fulfill({json:body,headers:{'Access-Control-Allow-Origin':'*'}});});
  await context.routeWebSocket(/.*/,ws=>{const url=ws.url();wsRouted.add(url);LEDGER.websockets.push(url);
    if(LOOP.has(hostOf(url)))return ws.connectToServer();ws.close({code:1008,reason:'R0036 isolation'});});
  context.on('request',req=>{const url=req.url();if(url.startsWith('data:'))return;setTimeout(()=>{if(!routed.has(req))LEDGER.bypassed.push(url);},0);});
  context.on('page',page=>page.on('websocket',ws=>{const url=ws.url();setTimeout(()=>{if(!wsRouted.has(url))LEDGER.wsBypassed.push(url);},0);}));
  return context;
}
// ---- one-for-one assertions ----
const ROWS=[];
function check(id,cond,detail){ROWS.push({id,result:cond?'PASS':'FAIL',detail:cond?undefined:detail});return !!cond;}
function notRun(id,why){ROWS.push({id,result:'NOT RUN',detail:why});}
const tryRun=async(id,fn)=>{try{return await fn();}catch(e){ROWS.push({id,result:'FAIL',detail:String(e.message||e).slice(0,400)});return null;}};
async function setupBrowser(browser,font,origin,{night=false,dpr=1,seed=true,denied=false,version='v1'}={}){       // setup_browser L76-L105
  const rootCurrent=ROOT_CURRENT&&version==='root';
  const context=await isolatedContext(browser,origin,{viewport:{width:390,height:600},deviceScaleFactor:dpr,timezoneId:'Asia/Riyadh',locale:'en-US',
    reducedMotion:'reduce',colorScheme:'light',geolocation:{latitude:21.4225,longitude:39.8262,accuracy:10}},{night,font,rootCurrent});
  if(!denied)await context.grantPermissions(['geolocation'],{origin});
  if(seed)await context.addInitScript("if(location.protocol === 'http:' && !localStorage.getItem("+JSON.stringify(ROOT_KEY)+")) localStorage.setItem("+JSON.stringify(ROOT_KEY)+","+JSON.stringify(JSON.stringify(SETTINGS))+");");
  const requests=[],errors=[],failed=[];
  context.on('request',r=>requests.push(r.url()));
  context.on('page',page=>page.on('pageerror',e=>errors.push(String(e))));
  context.on('requestfailed',r=>failed.push({url:r.url(),failure:r.failure()}));
  context.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});
  const page=await context.newPage();
  if(denied){const s=await context.newCDPSession(page);await s.send('Browser.setPermission',{permission:{name:'geolocation'},setting:'denied',origin});}
  const instant=new Date(Date.UTC(2026,9,7,night?20:9,30));
  await page.clock.install({time:instant});await page.clock.pauseAt(instant);
  return {context,page,requests,errors,failed,rootCurrent};
}
// The original waits with the page clock PAUSED (L103-L104). The current root boots through animation frames and
// timers, which a paused mocked clock never delivers, so in root-current a ROOT wait advances the mocked clock in
// 100 ms steps (clock.runFor) between polls, up to the same 30 s wall-clock budget. Only waiting changes: the
// installed instant, the assertions and their expected values are unchanged; at most the elapsed wait (seconds)
// is added to the mocked time before A114-A116, which read rows/date labels that do not depend on seconds.
async function waitFor(s,frame,expr,timeout=30000){
  if(!s.rootCurrent)return frame.waitForFunction(expr,null,{polling:100,timeout}).then(()=>true);
  const t0=Date.now();s.advancedMs=s.advancedMs||0;
  while(Date.now()-t0<timeout){if(await frame.evaluate(expr).catch(()=>false))return true;await s.page.clock.runFor(100);s.advancedMs+=100;}
  throw new Error('waitFor: Timeout '+timeout+'ms exceeded (clock advanced '+s.advancedMs+' ms)');
}
async function loaded(page,url,tag,diag){                                                                                  // loaded L108-L117
  await page.goto(url,{waitUntil:'load'});const frame=page.frames()[1];
  const ok=await waitFor(diag,frame,"typeof qaState === 'function' && qaState().cache.prayerLoaded && qaState().cache.tomorrowLoaded").then(()=>true,async e=>{
    // Diagnostic only (the wait itself is the assertion): what the page reported when the wait expired.
    const seen=await frame.evaluate("typeof qaState==='function'?(()=>{const q=qaState();return {cache:q.cache,configMode:q.config&&q.config.configMode,autoDetectStatus:q.config&&q.config.autoDetectStatus,source:q.config&&q.config.configSource};})():'qaState unavailable'").catch(x=>'evaluate failed: '+x.message);
    check(tag+':A111',false,{wait:'timed out: '+String(e.message).slice(0,120),seen,diag:diag&&{errors:diag.errors.slice(0,5),failed:diag.failed.slice(0,8)}});return false;});
  if(!ok){for(const id of ['A114','A115','A116'])notRun(tag+':'+id,'A111 wait failed');return null;}
  check(tag+':A111',true);
  await frame.evaluate('document.fonts.ready');await page.clock.runFor(3500);
  const rows=await frame.locator('.times .p b').allTextContents();
  check(tag+':A114',JSON.stringify(rows)===JSON.stringify(["Fajr","Sunrise","Dhuhr","Asr","Maghrib","Isha"]),rows);
  const ce=await frame.locator('#ce').innerText();check(tag+':A115',ce.includes('2026-10-07'),ce);
  const ah=await frame.locator('#ah').innerText();check(tag+':A116',ah.includes('1448'),ah);
  return frame;
}
async function snapshot(page,frame,name){                                                                             // snapshot L120-L126
  const file=path.join(out,name+'.png');await page.locator('iframe').screenshot({path:file,animations:'disabled'});
  return {screenshot:name+'.png',sha256:sha(fs.readFileSync(file)),qa:await frame.evaluate('qaState()'),
    geometry:await frame.evaluate("(() => {const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}}; return {innerWidth,innerHeight,dpr:devicePixelRatio,card:box('.c'),footer:box('.d'),header:box('.h'),scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight};})()"),   // the original passes this function source; Node evaluates a string as an expression, so it is invoked
   
    rows:await frame.locator('.times').innerText(),countdown:await frame.locator('.left').innerText(),
    // R191 inputs only (no original assertion reads them):
    visible:await frame.evaluate("(()=>{const c=document.querySelector('.c');if(!c)return false;const cs=getComputedStyle(c);return cs.visibility==='visible'&&cs.display!=='none'&&+cs.opacity>0;})()"),
    footerText:await frame.evaluate("document.querySelector('#ce')?.innerText??null"),
    // R191 rendered-visibility inputs: box, computed-style chain and hit test for the card and its three regions.
    rendered:await frame.evaluate("(()=>{const out={};for(const [k,s] of [['card','.c'],['header','.h'],['rows','.times'],['footer','#ce']]){const e=document.querySelector(s);if(!e){out[k]=null;continue;}const r=e.getBoundingClientRect();let shown=true;for(let n=e;n&&n.nodeType===1;n=n.parentElement){const cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility==='hidden'||cs.visibility==='collapse'||+cs.opacity===0)shown=false;}const hit=r.width>0&&r.height>0?document.elementFromPoint(r.x+r.width/2,r.y+r.height/2):null;out[k]={x:r.x,y:r.y,width:r.width,height:r.height,shown,hit:!!hit&&(hit===e||e.contains(hit)||hit.contains(e))};}return out;})()"),
    fonts:await frame.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>({family:f.family,weight:f.weight,status:f.status}))")};
}
const compare=(x,y)=>py(['compare',out,x,y]);                                                                       // compare L129-L135 (verbatim, Pillow)
// Test-only mutations of the staged ROOT copy, to prove each R-check fails when its property breaks.
const ROOT_MUTANTS={
  'hide-card':["</head>","<style>.c{visibility:hidden!important}</style></head>"],
  'no-precise-adoption':['_byId("set-lat").value=(+r.lat).toFixed(5); _byId("set-lon").value=(+r.lon).toFixed(5);',''],
  // Independent review (2026-11-16): a fully black card, a hidden footer date, swapped fix coordinates.
  'black-card':["</head>","<style>.c{filter:brightness(0)!important}</style></head>"],
  'no-footer-date':["</head>","<style>#ce{display:none!important}</style></head>"],
  'swap-lat-lon':['_byId("set-lat").value=(+r.lat).toFixed(5); _byId("set-lon").value=(+r.lon).toFixed(5);','_byId("set-lat").value=(+r.lon).toFixed(5); _byId("set-lon").value=(+r.lat).toFixed(5);'],
};
function stage(layoutKind){
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'salah-v1-browser-')),site=path.join(tmp,'salah_widget');fs.mkdirSync(site);
  for(const n of ['index.html','config.js'])fs.copyFileSync(path.join(REPO,n),path.join(site,n));
  if(ROOT_MUTANT){const [from,to]=ROOT_MUTANTS[ROOT_MUTANT],p=path.join(site,'index.html'),t=fs.readFileSync(p,'utf8');
    if(t.split(from).length!==2)throw new Error('root mutant anchor missing: '+ROOT_MUTANT);fs.writeFileSync(p,t.replace(from,()=>to));}
  fs.cpSync(path.join(REPO,'v1'),path.join(site,'v1'),{recursive:true});
  if(layoutKind==='full')for(const d of ['real-sky','moon'])fs.cpSync(path.join(REPO,d),path.join(site,d),{recursive:true});   // ADJUNCT only
  for(const [name,src] of [['root','/salah_widget/#local=1'],['v1','/salah_widget/v1/#local=1']]){
    const html='<!doctype html><html><head><meta charset="utf-8"><title>Preservation comparison</title></head><body>\n<iframe\n  title="Prayer Times"\n  referrerpolicy="no-referrer"\n  allow="geolocation"\n  src="'+src+'"\n  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"\n  scrolling="no">\n</iframe>\n</body></html>\n';
    fs.writeFileSync(path.join(tmp,name+'.html'),html);fs.writeFileSync(path.join(out,name+'-iframe.html'),html);}
  return {tmp,site};
}
function serve(dir,extra=()=>false){const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.gz':'application/gzip'};
  return http.createServer((req,res)=>{if(extra(req,res))return;let p=path.normalize(path.join(dir,decodeURIComponent(new URL(req.url,'http://x').pathname)));
    if(p.endsWith(path.sep))p=path.join(p,'index.html');
    if(!p.startsWith(dir)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
    res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res);});}
// FORMALLY INAPPLICABLE: the assertion's premise (root == V1) ended when the root was replaced by the current widget
// (pull request 39, merge 5f1f0003, 2026-10-07; docs/V1_PRESERVATION.md "Preserved pre-overhaul widget", the
// --check-root note). The observation is still recorded; nothing is tuned; an independent R-check tests the purpose.
function inapplicable(id,premise,observed,replacement){ROWS.push({id,result:'FORMALLY INAPPLICABLE',detail:{premise,ended:'pull request 39, merge 5f1f0003 (2026-10-07); docs/V1_PRESERVATION.md',historical:'original configuration record (docs/state-contracts/R0036.md section 12)',observed,replacement}});}
const pyStats=(file,box,dpr)=>py(['stats',out,file,String(Math.round(box.x*dpr)),String(Math.round(box.y*dpr)),String(Math.round(box.width*dpr)),String(Math.round(box.height*dpr))]);
// R191 content measure: the card INTERIOR (inset 30 CSS px, beyond the 28 px corner radius and clear of the drop
// shadow) and the header, prayer-row and footer regions, in device pixels.
// Thresholds = about one quarter of the healthy minimum measured on main 47faae32 over the three scenes (interior:
// 4778 distinct colours, luminance sd 38.1; header/rows/footer: sd 22.1, 142 distinct). A blank, black or flat card is
// 1 colour, sd 0.
const R191_T_INTERIOR_DISTINCT=()=>1000,R191_T_INTERIOR_STD=()=>10,R191_T_REGION_STD=()=>5,R191_T_REGION_DISTINCT=()=>32;
const R191_INSET=30,R191_MIN={interiorDistinct:R191_T_INTERIOR_DISTINCT(),interiorLumStd:R191_T_INTERIOR_STD(),regionLumStd:R191_T_REGION_STD(),regionDistinct:R191_T_REGION_DISTINCT()};
function r191Regions(file,rendered,dpr){const c=rendered.card,box=(r,i=0)=>r?[(r.x+i)*dpr,(r.y+i)*dpr,(r.width-2*i)*dpr,(r.height-2*i)*dpr]:[0,0,0,0];
  return py(['regions',out,file,JSON.stringify({interior:box(c,R191_INSET),header:box(rendered.header),rows:box(rendered.rows),footer:box(rendered.footer)})]);}
async function verify(browser,origin,font,site){
  const receipt={captures:{},checks:{}};
  if(BLOCKS.has('scenes'))for(const [night,dpr] of [[false,1],[true,1],[false,2]]){const scene=(night?'night':'day')+'-dpr'+dpr;let shots=0;
    for(const version of ['root','v1']){const tag=version+'-'+scene;
      await tryRun(tag+':setup',async()=>{const s=await setupBrowser(browser,font,origin,{night,dpr,version});
        try{const f=await loaded(s.page,origin+'/'+version+'.html',tag,s);
          if(!f){for(const id of ['A172','A173','A174','A175','A177','A179','A183','A185'])notRun(tag+':'+id,'page not loaded');return;}
          const r=await snapshot(s.page,f,tag);shots++;r.localRequests=s.requests.filter(u=>u.startsWith(origin)).map(u=>u.replace(origin,''));
          check(tag+':A172',r.geometry.card.width===325,r.geometry.card);check(tag+':A173',r.geometry.card.height===530,r.geometry.card);
          check(tag+':A174',r.geometry.footer.bottom<=534,r.geometry.footer);check(tag+':A175',r.fonts.length>0,'Font fixture did not load');
          const cfg='/salah_widget/'+(version==='v1'?'v1/':'')+'config.js';check(tag+':A177',r.localRequests.includes(cfg),r.localRequests);
          if(version==='v1')check(tag+':A179',!r.localRequests.includes('/salah_widget/config.js'),r.localRequests);
          const before=await f.locator('.left').innerText();await s.page.clock.fastForward(61000);
          const after=await f.locator('.left').innerText();check(tag+':A183',before!==after,'Countdown is frozen: '+before);
          r.countdownAfter61Seconds=after;check(tag+':A185',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
          r.errors=s.errors;r.failedRequests=s.failed;r.clockAdvancedDuringWaitsMs=s.advancedMs||0;receipt.captures[tag]=r;}finally{await s.context.close();}});}
    const root=receipt.captures['root-'+scene],v1=receipt.captures['v1-'+scene];
    if(ROOT_CURRENT){
      // R191: what the root-vs-V1 comparison was FOR, tested on the current widget alone: the embedded card is complete
      // (prayer rows, dated footer), rendered (not blank: >= 64 distinct colours inside the card box), visible, and has
      // the same embedding footprint as V1 (identical iframe screenshot dimensions).
      if(root&&v1){const c=compare('root-'+scene+'.png','v1-'+scene+'.png'),st=pyStats('root-'+scene+'.png',root.geometry.card,dpr),sv=pyStats('v1-'+scene+'.png',v1.geometry.card,dpr);
        receipt.checks['comparison-'+scene]=c;
        inapplicable('comparison-'+scene+':A191','root screenshot pixel-identical to V1',c,'R191-'+scene);
        const rg=r191Regions('root-'+scene+'.png',root.rendered,dpr),b=rg.boxes,R=root.rendered;
        const shown=['card','header','rows','footer'].every(k=>R[k]&&R[k].width>0&&R[k].height>0&&R[k].shown&&R[k].hit);
        const content=b.interior.distinct>=R191_MIN.interiorDistinct&&b.interior.lumStd>=R191_MIN.interiorLumStd&&
          ['header','rows','footer'].every(k=>b[k].lumStd>=R191_MIN.regionLumStd&&b[k].distinct>=R191_MIN.regionDistinct);
        const ok=st.width===sv.width&&st.height===sv.height&&shown&&content&&/Fajr/.test(root.rows)&&/2026-10-07/.test(root.footerText||'');
        check('comparison-'+scene+':R191',ok,{size:{root:[st.width,st.height],v1:[sv.width,sv.height]},rendered:R,regions:b,thresholds:R191_MIN});}
      else{inapplicable('comparison-'+scene+':A191','root screenshot pixel-identical to V1','a capture is missing','R191-'+scene);notRun('comparison-'+scene+':R191','a capture is missing');}}
    else if(shots===2){const c=compare('root-'+scene+'.png','v1-'+scene+'.png');receipt.checks['comparison-'+scene]=c;check('comparison-'+scene+':A191',c.pixelExact,c);}
    else notRun('comparison-'+scene+':A191','a capture is missing');}
  if(BLOCKS.has('geo'))for(const version of ['root','v1'])for(const denied of [false,true]){const tag=version+(denied?'-geo-denied':'-geo-granted');
    await tryRun(tag+':setup',async()=>{const s=await setupBrowser(browser,font,origin,{seed:false,denied,version});
      try{let f=await loaded(s.page,origin+'/'+version+'.html',tag,s);
        if(!f){for(const id of ['A199','A203','A205','A213','A215','A218','A220','A221'])notRun(tag+':'+id,'page not loaded');return;}
        const st=await f.evaluate('qaState().config.autoDetectStatus');check(tag+':A199',st==='ok',st);
        await f.locator('.buckle').click({force:true});await s.page.clock.runFor(100);await f.locator('#set-pin').click({force:true});
        await waitFor(s,f,"!document.querySelector('#set-status').textContent.includes('Requesting')",30000).then(()=>check(tag+':A203',true),e=>check(tag+':A203',false,String(e.message).slice(0,200)));
        const status=await f.locator('#set-status').innerText();
        if(s.rootCurrent&&!denied){
          // The granted text "Using your precise location" is V1's wording; the root's changed in 3cf6ce2f (reached main in
          // pull request 39). R205: the root ADOPTS the fix — its status names the browser position and the form holds the
          // emulated fix coordinates (21.4225, 39.8262).
          inapplicable(tag+':A205','root GPS status text equals V1 ("Using your precise location")',status,'R205-'+tag);
          const lat=await f.locator('#set-lat').inputValue(),lon=await f.locator('#set-lon').inputValue();
          check(tag+':R205',/^Browser position/.test(status)&&lat==='21.42250'&&lon==='39.82620',{status,lat,lon});}
        else check(tag+':A205',denied?status.includes('unavailable'):status.includes('Using your precise location'),status);
        if(denied){await f.locator('#set-label').fill('Manual after denial');await f.locator('#set-lat').fill('24.47');await f.locator('#set-lon').fill('39.61');}
        await f.locator('#setClose').click({force:true});await s.page.clock.runFor(1500);
        const saved=await f.evaluate('SalahConfig.loadLocal()');check(tag+':A213',!!saved&&(denied?saved.label==='Manual after denial':saved.lat===21.4225),saved);
        if(version==='v1')check(tag+':A215',await f.evaluate("localStorage.getItem('salah_widget:config:v1')")===null,'root key written by V1');
        await s.page.reload({waitUntil:'load'});f=s.page.frames()[1];
        const ok=await waitFor(s,f,"typeof qaState==='function' && qaState().cache.prayerLoaded").then(()=>true,()=>false);check(tag+':A218',ok,'reload wait timed out');
        await s.page.clock.runFor(1500);
        if(ok&&saved)check(tag+':A220',await f.evaluate('SalahConfig.loadLocal().label')===saved.label,saved.label);else notRun(tag+':A220','reload or save failed');
        check(tag+':A221',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
        receipt.checks[tag]={status,saved,reload:ok,errors:s.errors};}finally{await s.context.close();}});}
  if(BLOCKS.has('storage'))await tryRun('storage-isolation:setup',async()=>{const tag='storage-isolation';const s=await setupBrowser(browser,font,origin);
    try{let f=await loaded(s.page,origin+'/v1.html',tag,s);if(!f){for(const id of ['A236','A237','A242','A244','A245','A246','A247'])notRun(tag+':'+id,'page not loaded');return;}
      const original=await f.evaluate("localStorage.getItem('salah_widget:config:v1')");
      await f.locator('.buckle').click({force:true});await s.page.clock.runFor(100);await f.locator('#set-label').fill('V1 saved independently');await f.locator('#set-time').selectOption('12');
      receipt.captures['v1-settings']=await snapshot(s.page,f,'v1-settings');
      await f.locator('#setClose').click({force:true});await s.page.clock.runFor(1500);
      check(tag+':A236',await f.evaluate("localStorage.getItem('salah_widget:config:v1')")===original,'root key changed by V1 save');
      check(tag+':A237',await f.evaluate('SalahConfig.loadLocal().time')==='12','time not saved');
      await f.evaluate("localStorage.setItem('salah_widget:config:v1',JSON.stringify({v:99,label:'Future root schema'}))");
      await s.page.reload({waitUntil:'load'});f=s.page.frames()[1];
      // L241: the original reload wait, now its own row; a timeout leaves A242-A247 NOT RUN instead of aborting silently.
      const reloaded=await waitFor(s,f,"typeof qaState==='function' && qaState().cache.prayerLoaded").then(()=>true,()=>false);check(tag+':A241',reloaded,'reload wait timed out');
      if(!reloaded){for(const id of ['A242','A244','A245','A246','A247'])notRun(tag+':'+id,'A241 reload wait failed');return;}
      check(tag+':A242',await f.evaluate('SalahConfig.loadLocal().label')==='V1 saved independently','label');
      const keys=await f.evaluate('Object.keys(localStorage)');
      check(tag+':A244',keys.some(k=>k.startsWith('salah_widget:v1:prayer:')),keys);check(tag+':A245',keys.some(k=>k.startsWith('salah_widget:v1:weather:')),keys);
      check(tag+':A246',!keys.some(k=>k.startsWith('salah:')||k.startsWith('salahwx:')),keys);check(tag+':A247',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
      receipt.checks[tag]={keys};}finally{await s.context.close();}});
  if(BLOCKS.has('replacement'))await tryRun('root-replacement:setup',async()=>{const tag='root-replacement';
    fs.writeFileSync(path.join(site,'config.js'),"throw new Error('ROOT CONFIG REPLACED CONTROL');");fs.writeFileSync(path.join(site,'index.html'),'<!doctype html>ROOT REPLACED CONTROL');
    const s=await setupBrowser(browser,font,origin);
    try{const f=await loaded(s.page,origin+'/v1.html',tag,s);if(!f){notRun(tag+':A258','page not loaded');notRun(tag+':A259','page not loaded');return;}
      receipt.captures['v1-root-replaced']=await snapshot(s.page,f,'v1-root-replaced');
      const iso=fs.existsSync(path.join(out,'v1-day-dpr1.png'))?compare('v1-day-dpr1.png','v1-root-replaced.png'):null;
      if(iso)check(tag+':A258',iso.pixelExact&&!s.errors.length&&!s.failed.length,{iso,errors:s.errors,failed:s.failed});else notRun(tag+':A258','v1-day-dpr1 capture missing');
      check(tag+':A259',!s.requests.includes(origin+'/salah_widget/config.js'),'root config requested');receipt.checks[tag]=iso;}finally{await s.context.close();}});
  return receipt;
}
async function selftest(browser,origin){
  const s=await isolatedContext(browser,origin,{});const page=await s.newPage();const pageLog=[];
  await page.goto(origin+'/selftest.html');
  const r=await page.evaluate(async()=>{const out={};
    try{await fetch('https://fonts.googleapis.com/css2?family=Inter');out.fetch='connected';}catch(e){out.fetch='refused: '+e.message;}
    out.image=await new Promise(res=>{const i=new Image();i.onload=()=>res('loaded');i.onerror=()=>res('refused');i.src='https://tilecache.rainviewer.com/v2/radar/r0036/256/6/39/27/2/1_1.png';});
    out.websocket=await new Promise(res=>{let w;try{w=new WebSocket('wss://ws.r0036-provider.example/stream');}catch(e){return res('refused: '+e.message);}
      w.onopen=()=>res('connected');w.onerror=()=>res('refused');w.onclose=ev=>res('refused (close '+ev.code+')');setTimeout(()=>res('timeout'),5000);});
    // A loopback response that redirects off loopback: the redirected request skips the route, so it must be refused at
    // the loopback proxy before any outbound connection.
    try{await fetch('/r0036-redirect-name');out.redirectName='connected';}catch(e){out.redirectName='refused: '+e.message;}
    return out;});
  // IP-literal probes run only while the refusing proxy is configured (they would otherwise be routed by the OS).
  if(PROXY_ON())r.ip=await page.evaluate(async()=>{const o={};
    try{await fetch('http://10.255.255.1/r0036-direct');o.direct='connected';}catch(e){o.direct='refused: '+e.message;}
    try{await fetch('/r0036-redirect-ip');o.redirect='connected';}catch(e){o.redirect='refused: '+e.message;}
    return o;});
  await page.waitForTimeout(300);await s.close();
  const node={};
  node.httpGet=await new Promise(res=>{try{const q=http.get('http://0.0.0.0:9/r0036-selftest',()=>res('connected'));q.on('error',e=>res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message));}catch(e){res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);}});
  node.fetch=await fetch('http://0.0.0.0:9/r0036-selftest').then(()=>'connected',e=>(e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);
  if(guard.state.installed)node.ipLiteral=await new Promise(res=>{try{http.get('http://10.255.255.1/r0036-selftest',()=>res('connected')).on('error',e=>res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message));}catch(e){res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);}});
  if(guard.state.installed)node.httpsName=await new Promise(res=>{try{https.get('https://fonts.googleapis.com/css2?family=Inter',()=>res('connected')).on('error',e=>res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message));}catch(e){res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);}});
  const python=py(['selftest']);
  // Offline font fixture determinism (needs fontTools, so it lives in this native recipe, not the hermetic unit test).
  const FONT_PIN='3bdfe0e90e0bbe36439c6e05b567d5356288285dcf1287058f123c2302a5aadc';
  const fonts=[1,2].map(n=>py(['font',path.join(out,'font-check-'+n+'.ttf')]));
  const refusedInRoute=u=>LEDGER.aborted.includes(u),atProxy=t=>PROXY_REFUSED.some(x=>x.target.includes(t));
  const checks={
    pageFetchRefusedByRoute:r.fetch.startsWith('refused')&&refusedInRoute('https://fonts.googleapis.com/css2?family=Inter'),
    pageImageRefusedByRoute:r.image==='refused'&&refusedInRoute('https://tilecache.rainviewer.com/v2/radar/r0036/256/6/39/27/2/1_1.png'),
    pageWebSocketRefusedByRoute:r.websocket.startsWith('refused')&&LEDGER.websockets.includes('wss://ws.r0036-provider.example/stream'),
    nodeGuardInstalled:guard.state.installed===true,
    nodeRefusedByGuard:node.httpGet.startsWith('refused-by-guard')&&node.fetch.startsWith('refused-by-guard')&&(!('httpsName' in node)||node.httpsName.startsWith('refused-by-guard'))&&(!('ipLiteral' in node)||node.ipLiteral.startsWith('refused-by-guard')),
    redirectRefusedAtProxy:r.redirectName.startsWith('refused')&&atProxy('fonts.googleapis.com'),
    ipLiteralRefused:!!r.ip&&r.ip.direct.startsWith('refused')&&refusedInRoute('http://10.255.255.1/r0036-direct')&&r.ip.redirect.startsWith('refused')&&atProxy('10.255.255.1'),
    fontFixtureDeterministic:fonts.every(f=>f.sha256===FONT_PIN&&f.refused.length===0),
    pythonGuardInstalled:python.installed===true,
    pythonUrlopenRefusedByGuard:python.probes.length>0&&python.probes.every(p=>p.refusedByGuard===true),
    // The only route bypasses allowed are the two probe redirects, and only because the proxy refused them.
    noRequestOffLoopback:LEDGER.allowedOffLoopback.length===0&&LEDGER.wsBypassed.length===0&&LEDGER.bypassed.every(u=>(/^https:\/\/fonts\.googleapis\.com\/r0036-redirect/.test(u)&&atProxy('fonts.googleapis.com'))||(/^http:\/\/10\.255\.255\.1\/r0036-redirect/.test(u)&&atProxy('10.255.255.1')))};
  return {page:r,node,python,checks,pass:Object.values(checks).every(Boolean)};
}
(async()=>{
  const {tmp,site}=stage(layout);
  fs.writeFileSync(path.join(tmp,'selftest.html'),'<!doctype html><meta charset="utf-8"><title>R0036 isolation self-test</title><p>self-test</p>');
  const font=fs.readFileSync((()=>{const f=path.join(out,'fixture-font.ttf');const r=py(['font',f]);fs.writeFileSync(path.join(out,'fixture-font.json'),JSON.stringify(r));return f;})());
  const server=serve(tmp,(req,res)=>{const p=new URL(req.url,'http://x').pathname;
    if(mode==='selftest'&&p==='/r0036-redirect-name'){res.writeHead(302,{location:'https://fonts.googleapis.com/r0036-redirect'});res.end();return true;}
    if(mode==='selftest'&&p==='/r0036-redirect-ip'){res.writeHead(302,{location:'http://10.255.255.1/r0036-redirect'});res.end();return true;}
    return false;});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  await new Promise(r=>proxy.listen(0,'127.0.0.1',r));PROXY_PORT=proxy.address().port;
  const exe=a.chromium?{executablePath:a.chromium}:{};
  const browser=await PW.chromium.launch({headless:true,args:launchArgs(),...exe});
  const receipt={schema:'r0036-v1-browser/2',mode,config,blocks:[...BLOCKS],rootMutant:ROOT_MUTANT,layout,layoutNote:layout==='full'?'ADJUNCT: root runtime directories real-sky/ and moon/ also served; not the original layout':'original layout of tests/v1_browser.py (index.html, config.js, v1/)',
    browser:browser.version(),node:process.version,testSha256:sha(fs.readFileSync(path.join(REPO,'tests','v1_browser.py'))),runnerSha256:sha(fs.readFileSync(__filename)),
    payloadHashes:Object.fromEntries(['index.html','config.js','v1/index.html','v1/config.js'].map(n=>[n,sha(fs.readFileSync(path.join(REPO,n)))])),
    fontFixture:{css:FIXTURE_CSS,cssSha256:sha(FIXTURE_CSS),font:JSON.parse(fs.readFileSync(path.join(out,'fixture-font.json'),'utf8'))},
    fixtureNotice:'Controlled provider fixtures, emulated browser clock/location/permissions, OFFLINE font fixture (not the provider fonts); not live provider or real GPS evidence'};
  let failedIsolation=false;
  try{
    if(mode==='selftest'){receipt.selftest=await selftest(browser,origin);}
    else{const r=await verify(browser,origin,font,site);receipt.captures=r.captures;receipt.checks=r.checks;receipt.rows=ROWS;
      receipt.summary=ROWS.reduce((m,x)=>(m[x.result]=(m[x.result]||0)+1,m),{});}
  }finally{await browser.close();server.close();proxy.close();fs.rmSync(tmp,{recursive:true,force:true});
    const outsideSelftest=mode==='selftest'?[]:[...guard.state.refused,...PY_REFUSED,...PROXY_REFUSED];
    receipt.isolation={requestsSeen:LEDGER.seen,continuedLoopback:LEDGER.continued,allowedOffLoopback:LEDGER.allowedOffLoopback.length,fulfilledFixture:LEDGER.fulfilledFixture,
      fulfilledFont:LEDGER.fulfilledFont,aborted:LEDGER.aborted.length,abortedHosts:LEDGER.aborted.reduce((m,u)=>(m[hostOf(u)]=(m[hostOf(u)]||0)+1,m),{}),
      unplanned:LEDGER.unplanned,bypassed:LEDGER.bypassed,websockets:LEDGER.websockets,wsBypassed:LEDGER.wsBypassed,
      nodeGuard:{installed:guard.state.installed,refused:guard.state.refused,proxyVarsRemoved:guard.state.proxyVarsRemoved},pythonRefusedOutsideSelftest:PY_REFUSED,proxyRefused:PROXY_REFUSED,launchArgs:launchArgs()};
    failedIsolation=LEDGER.allowedOffLoopback.length>0||LEDGER.wsBypassed.length>0||outsideSelftest.length>0||(mode==='selftest'?!receipt.selftest?.checks?.noRequestOffLoopback:LEDGER.bypassed.length>0);
    fs.writeFileSync(path.join(out,mode==='selftest'?'selftest.json':'v1-browser-results.json'),JSON.stringify(receipt,null,1)+'\n');}
  const i=receipt.isolation;
  console.log(JSON.stringify({mode,config,layout,isolation:{seen:i.requestsSeen,continuedLoopback:i.continuedLoopback,allowedOffLoopback:i.allowedOffLoopback,fulfilledFixture:i.fulfilledFixture,fulfilledFont:i.fulfilledFont,aborted:i.aborted,abortedHosts:i.abortedHosts,bypassed:i.bypassed.length,wsBypassed:i.wsBypassed.length,proxyRefused:i.proxyRefused.length},
    ...(mode==='selftest'?{selftest:receipt.selftest.checks,pass:receipt.selftest.pass}:{summary:receipt.summary})}));
  if(failedIsolation){console.error('NETWORK ISOLATION FAILURE');process.exitCode=3;}
  else if(mode==='selftest'&&!receipt.selftest.pass)process.exitCode=1;
  else if(mode!=='selftest'&&ROWS.some(r=>r.result!=='PASS'&&r.result!=='FORMALLY INAPPLICABLE'))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=2;});
