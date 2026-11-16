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
// tools/qa/v1_net_guard.py first. Browser side: Chromium starts with --no-proxy-server and a host-resolver rule that
// resolves nothing but 127.0.0.1; every context gets the catch-all route `**/*` and a catch-all WebSocket route BEFORE
// any page exists, neither is ever removed; only the loopback fixture origin and same-origin blob:/data: continue;
// providers are fulfilled from the original fixtures, anything else is aborted; every request is logged; the run
// fails (exit 3) on any request allowed off loopback, any request or WebSocket that bypassed the routes, or any
// Node/Python-side refusal outside the self-test.
// Usage: node tools/qa/r0036_v1_browser.cjs --out <dir> [--mode verify|selftest] [--layout original|full]
//        [--playwright <pkg>] [--chromium <exe>] [--root <tree>]
const guard=require('./v1_net_guard.cjs');guard.install();                   // before any other module can connect
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http'),https=require('node:https'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),REPO=path.resolve(a.root||path.join(__dirname,'..','..')),out=path.resolve(a.out),mode=a.mode||'verify',layout=a.layout||'original';
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
  if(r.status!==0)throw new Error('python helper failed: '+args[0]+' '+r.stderr);return JSON.parse(r.stdout.trim().split('\n').pop());}
// ---- verbatim provider fixture of tests/v1_browser.py fixture() L53-L68 ----
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
const LAUNCH_ARGS=['--no-proxy-server','--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1','--disable-background-networking','--disable-component-update','--disable-domain-reliability','--no-pings'];
async function isolatedContext(browser,origin,options,{night=false,font=null}={}){
  const context=await browser.newContext(options);const routed=new WeakSet(),wsRouted=new Set();
  await context.route('**/*',route=>{const req=route.request(),url=req.url();routed.add(req);LEDGER.seen++;
    if(url.startsWith(origin+'/')||url.startsWith('blob:'+origin+'/')){LEDGER.continued++;if(!LOOP.has(hostOf(url))&&!url.startsWith('blob:'))LEDGER.allowedOffLoopback.push(url);return route.continue();}
    if(url===FONT_CSS){LEDGER.fulfilledFont++;return route.fulfill({body:FIXTURE_CSS,contentType:'text/css',headers:{'Access-Control-Allow-Origin':'*'}});}
    if(url===FONT_URL&&font){LEDGER.fulfilledFont++;return route.fulfill({body:font,contentType:'font/ttf',headers:{'Access-Control-Allow-Origin':'*'}});}
    let body;try{body=fixture(url,night);}catch(e){LEDGER.unplanned.push(url);LEDGER.aborted.push(url);return route.abort('blockedbyclient');}
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
async function setupBrowser(browser,font,origin,{night=false,dpr=1,seed=true,denied=false}={}){                   // setup_browser L76-L105
  const context=await isolatedContext(browser,origin,{viewport:{width:390,height:600},deviceScaleFactor:dpr,timezoneId:'Asia/Riyadh',locale:'en-US',
    reducedMotion:'reduce',colorScheme:'light',geolocation:{latitude:21.4225,longitude:39.8262,accuracy:10}},{night,font});
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
  return {context,page,requests,errors,failed};
}
async function loaded(page,url,tag){                                                                                  // loaded L108-L117
  await page.goto(url,{waitUntil:'load'});const frame=page.frames()[1];
  const ok=await frame.waitForFunction("typeof qaState === 'function' && qaState().cache.prayerLoaded && qaState().cache.tomorrowLoaded",null,{polling:100,timeout:30000}).then(()=>true,e=>{check(tag+':A111',false,'wait timed out: '+String(e.message).slice(0,200));return false;});
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
    geometry:await frame.evaluate("() => {const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}}; return {innerWidth,innerHeight,dpr:devicePixelRatio,card:box('.c'),footer:box('.d'),header:box('.h'),scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight};}"),
    rows:await frame.locator('.times').innerText(),countdown:await frame.locator('.left').innerText(),
    fonts:await frame.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>({family:f.family,weight:f.weight,status:f.status}))")};
}
const compare=(x,y)=>py(['compare',out,x,y]);                                                                       // compare L129-L135 (verbatim, Pillow)
function stage(layoutKind){
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'salah-v1-browser-')),site=path.join(tmp,'salah_widget');fs.mkdirSync(site);
  for(const n of ['index.html','config.js'])fs.copyFileSync(path.join(REPO,n),path.join(site,n));
  fs.cpSync(path.join(REPO,'v1'),path.join(site,'v1'),{recursive:true});
  if(layoutKind==='full')for(const d of ['real-sky','moon'])fs.cpSync(path.join(REPO,d),path.join(site,d),{recursive:true});   // ADJUNCT only
  for(const [name,src] of [['root','/salah_widget/#local=1'],['v1','/salah_widget/v1/#local=1']]){
    const html='<!doctype html><html><head><meta charset="utf-8"><title>Preservation comparison</title></head><body>\n<iframe\n  title="Prayer Times"\n  referrerpolicy="no-referrer"\n  allow="geolocation"\n  src="'+src+'"\n  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"\n  scrolling="no">\n</iframe>\n</body></html>\n';
    fs.writeFileSync(path.join(tmp,name+'.html'),html);fs.writeFileSync(path.join(out,name+'-iframe.html'),html);}
  return {tmp,site};
}
function serve(dir){const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.gz':'application/gzip'};
  return http.createServer((req,res)=>{let p=path.normalize(path.join(dir,decodeURIComponent(new URL(req.url,'http://x').pathname)));
    if(p.endsWith(path.sep))p=path.join(p,'index.html');
    if(!p.startsWith(dir)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
    res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res);});}
async function verify(browser,origin,font,site){
  const receipt={captures:{},checks:{}};
  for(const [night,dpr] of [[false,1],[true,1],[false,2]]){const scene=(night?'night':'day')+'-dpr'+dpr;let shots=0;
    for(const version of ['root','v1']){const tag=version+'-'+scene;
      await tryRun(tag+':setup',async()=>{const s=await setupBrowser(browser,font,origin,{night,dpr});
        try{const f=await loaded(s.page,origin+'/'+version+'.html',tag);
          if(!f){for(const id of ['A172','A173','A174','A175','A177','A179','A183','A185'])notRun(tag+':'+id,'page not loaded');return;}
          const r=await snapshot(s.page,f,tag);shots++;r.localRequests=s.requests.filter(u=>u.startsWith(origin)).map(u=>u.replace(origin,''));
          check(tag+':A172',r.geometry.card.width===325,r.geometry.card);check(tag+':A173',r.geometry.card.height===530,r.geometry.card);
          check(tag+':A174',r.geometry.footer.bottom<=534,r.geometry.footer);check(tag+':A175',r.fonts.length>0,'Font fixture did not load');
          const cfg='/salah_widget/'+(version==='v1'?'v1/':'')+'config.js';check(tag+':A177',r.localRequests.includes(cfg),r.localRequests);
          if(version==='v1')check(tag+':A179',!r.localRequests.includes('/salah_widget/config.js'),r.localRequests);
          const before=await f.locator('.left').innerText();await s.page.clock.fastForward(61000);
          const after=await f.locator('.left').innerText();check(tag+':A183',before!==after,'Countdown is frozen: '+before);
          r.countdownAfter61Seconds=after;check(tag+':A185',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
          r.errors=s.errors;r.failedRequests=s.failed;receipt.captures[tag]=r;}finally{await s.context.close();}});}
    if(shots===2){const c=compare('root-'+scene+'.png','v1-'+scene+'.png');receipt.checks['comparison-'+scene]=c;check('comparison-'+scene+':A191',c.pixelExact,c);}
    else notRun('comparison-'+scene+':A191','a capture is missing');}
  for(const version of ['root','v1'])for(const denied of [false,true]){const tag=version+(denied?'-geo-denied':'-geo-granted');
    await tryRun(tag+':setup',async()=>{const s=await setupBrowser(browser,font,origin,{seed:false,denied});
      try{let f=await loaded(s.page,origin+'/'+version+'.html',tag);
        if(!f){for(const id of ['A199','A203','A205','A213','A215','A218','A220','A221'])notRun(tag+':'+id,'page not loaded');return;}
        const st=await f.evaluate('qaState().config.autoDetectStatus');check(tag+':A199',st==='ok',st);
        await f.locator('.buckle').click({force:true});await s.page.clock.runFor(100);await f.locator('#set-pin').click({force:true});
        await f.waitForFunction("!document.querySelector('#set-status').textContent.includes('Requesting')",null,{polling:100,timeout:15000}).then(()=>check(tag+':A203',true),e=>check(tag+':A203',false,String(e.message).slice(0,200)));
        const status=await f.locator('#set-status').innerText();check(tag+':A205',denied?status.includes('unavailable'):status.includes('Using your precise location'),status);
        if(denied){await f.locator('#set-label').fill('Manual after denial');await f.locator('#set-lat').fill('24.47');await f.locator('#set-lon').fill('39.61');}
        await f.locator('#setClose').click({force:true});await s.page.clock.runFor(1500);
        const saved=await f.evaluate('SalahConfig.loadLocal()');check(tag+':A213',!!saved&&(denied?saved.label==='Manual after denial':saved.lat===21.4225),saved);
        if(version==='v1')check(tag+':A215',await f.evaluate("localStorage.getItem('salah_widget:config:v1')")===null,'root key written by V1');
        await s.page.reload({waitUntil:'load'});f=s.page.frames()[1];
        const ok=await f.waitForFunction("typeof qaState==='function' && qaState().cache.prayerLoaded",null,{polling:100,timeout:30000}).then(()=>true,()=>false);check(tag+':A218',ok,'reload wait timed out');
        await s.page.clock.runFor(1500);
        if(ok&&saved)check(tag+':A220',await f.evaluate('SalahConfig.loadLocal().label')===saved.label,saved.label);else notRun(tag+':A220','reload or save failed');
        check(tag+':A221',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
        receipt.checks[tag]={status,saved,reload:ok,errors:s.errors};}finally{await s.context.close();}});}
  await tryRun('storage-isolation:setup',async()=>{const tag='storage-isolation';const s=await setupBrowser(browser,font,origin);
    try{let f=await loaded(s.page,origin+'/v1.html',tag);if(!f){for(const id of ['A236','A237','A242','A244','A245','A246','A247'])notRun(tag+':'+id,'page not loaded');return;}
      const original=await f.evaluate("localStorage.getItem('salah_widget:config:v1')");
      await f.locator('.buckle').click({force:true});await s.page.clock.runFor(100);await f.locator('#set-label').fill('V1 saved independently');await f.locator('#set-time').selectOption('12');
      receipt.captures['v1-settings']=await snapshot(s.page,f,'v1-settings');
      await f.locator('#setClose').click({force:true});await s.page.clock.runFor(1500);
      check(tag+':A236',await f.evaluate("localStorage.getItem('salah_widget:config:v1')")===original,'root key changed by V1 save');
      check(tag+':A237',await f.evaluate('SalahConfig.loadLocal().time')==='12','time not saved');
      await f.evaluate("localStorage.setItem('salah_widget:config:v1',JSON.stringify({v:99,label:'Future root schema'}))");
      await s.page.reload({waitUntil:'load'});f=s.page.frames()[1];
      await f.waitForFunction("typeof qaState==='function' && qaState().cache.prayerLoaded",null,{polling:100,timeout:30000});
      check(tag+':A242',await f.evaluate('SalahConfig.loadLocal().label')==='V1 saved independently','label');
      const keys=await f.evaluate('Object.keys(localStorage)');
      check(tag+':A244',keys.some(k=>k.startsWith('salah_widget:v1:prayer:')),keys);check(tag+':A245',keys.some(k=>k.startsWith('salah_widget:v1:weather:')),keys);
      check(tag+':A246',!keys.some(k=>k.startsWith('salah:')||k.startsWith('salahwx:')),keys);check(tag+':A247',!s.errors.length&&!s.failed.length,{errors:s.errors,failed:s.failed});
      receipt.checks[tag]={keys};}finally{await s.context.close();}});
  await tryRun('root-replacement:setup',async()=>{const tag='root-replacement';
    fs.writeFileSync(path.join(site,'config.js'),"throw new Error('ROOT CONFIG REPLACED CONTROL');");fs.writeFileSync(path.join(site,'index.html'),'<!doctype html>ROOT REPLACED CONTROL');
    const s=await setupBrowser(browser,font,origin);
    try{const f=await loaded(s.page,origin+'/v1.html',tag);if(!f){notRun(tag+':A258','page not loaded');notRun(tag+':A259','page not loaded');return;}
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
    return out;});
  await page.waitForTimeout(300);await s.close();
  const node={};
  node.httpGet=await new Promise(res=>{try{const q=http.get('http://0.0.0.0:9/r0036-selftest',()=>res('connected'));q.on('error',e=>res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message));}catch(e){res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);}});
  node.fetch=await fetch('http://0.0.0.0:9/r0036-selftest').then(()=>'connected',e=>(e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);
  if(guard.state.installed)node.httpsName=await new Promise(res=>{try{https.get('https://fonts.googleapis.com/css2?family=Inter',()=>res('connected')).on('error',e=>res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message));}catch(e){res((e.code==='ER0036_ISOLATED'?'refused-by-guard: ':'error: ')+e.message);}});
  const python=py(['selftest']);
  const refusedInRoute=u=>LEDGER.aborted.includes(u);
  const checks={
    pageFetchRefusedByRoute:r.fetch.startsWith('refused')&&refusedInRoute('https://fonts.googleapis.com/css2?family=Inter'),
    pageImageRefusedByRoute:r.image==='refused'&&refusedInRoute('https://tilecache.rainviewer.com/v2/radar/r0036/256/6/39/27/2/1_1.png'),
    pageWebSocketRefusedByRoute:r.websocket.startsWith('refused')&&LEDGER.websockets.includes('wss://ws.r0036-provider.example/stream'),
    nodeGuardInstalled:guard.state.installed===true,
    nodeRefusedByGuard:node.httpGet.startsWith('refused-by-guard')&&node.fetch.startsWith('refused-by-guard')&&(!('httpsName' in node)||node.httpsName.startsWith('refused-by-guard')),
    pythonGuardInstalled:python.installed===true,
    pythonUrlopenRefusedByGuard:python.probes.length>0&&python.probes.every(p=>p.refusedByGuard===true),
    noRequestOffLoopback:LEDGER.allowedOffLoopback.length===0&&LEDGER.bypassed.length===0&&LEDGER.wsBypassed.length===0};
  return {page:r,node,python,checks,pass:Object.values(checks).every(Boolean)};
}
(async()=>{
  const {tmp,site}=stage(layout);
  fs.writeFileSync(path.join(tmp,'selftest.html'),'<!doctype html><meta charset="utf-8"><title>R0036 isolation self-test</title><p>self-test</p>');
  const font=fs.readFileSync((()=>{const f=path.join(out,'fixture-font.ttf');const r=py(['font',f]);fs.writeFileSync(path.join(out,'fixture-font.json'),JSON.stringify(r));return f;})());
  const server=serve(tmp);await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  const exe=a.chromium?{executablePath:a.chromium}:{};
  const browser=await PW.chromium.launch({headless:true,args:LAUNCH_ARGS,...exe});
  const receipt={schema:'r0036-v1-browser/1',mode,layout,layoutNote:layout==='full'?'ADJUNCT: root runtime directories real-sky/ and moon/ also served; not the original layout':'original layout of tests/v1_browser.py (index.html, config.js, v1/)',
    browser:browser.version(),node:process.version,testSha256:sha(fs.readFileSync(path.join(REPO,'tests','v1_browser.py'))),runnerSha256:sha(fs.readFileSync(__filename)),
    payloadHashes:Object.fromEntries(['index.html','config.js','v1/index.html','v1/config.js'].map(n=>[n,sha(fs.readFileSync(path.join(REPO,n)))])),
    fontFixture:{css:FIXTURE_CSS,cssSha256:sha(FIXTURE_CSS),font:JSON.parse(fs.readFileSync(path.join(out,'fixture-font.json'),'utf8'))},
    fixtureNotice:'Controlled provider fixtures, emulated browser clock/location/permissions, OFFLINE font fixture (not the provider fonts); not live provider or real GPS evidence'};
  let failedIsolation=false;
  try{
    if(mode==='selftest'){receipt.selftest=await selftest(browser,origin);}
    else{const r=await verify(browser,origin,font,site);receipt.captures=r.captures;receipt.checks=r.checks;receipt.rows=ROWS;
      receipt.summary=ROWS.reduce((m,x)=>(m[x.result]=(m[x.result]||0)+1,m),{});}
  }finally{await browser.close();server.close();fs.rmSync(tmp,{recursive:true,force:true});
    const outsideSelftest=mode==='selftest'?[]:guard.state.refused;
    receipt.isolation={requestsSeen:LEDGER.seen,continuedLoopback:LEDGER.continued,allowedOffLoopback:LEDGER.allowedOffLoopback.length,fulfilledFixture:LEDGER.fulfilledFixture,
      fulfilledFont:LEDGER.fulfilledFont,aborted:LEDGER.aborted.length,abortedHosts:LEDGER.aborted.reduce((m,u)=>(m[hostOf(u)]=(m[hostOf(u)]||0)+1,m),{}),
      unplanned:LEDGER.unplanned,bypassed:LEDGER.bypassed,websockets:LEDGER.websockets,wsBypassed:LEDGER.wsBypassed,
      nodeGuard:{installed:guard.state.installed,refused:guard.state.refused,proxyVarsRemoved:guard.state.proxyVarsRemoved},launchArgs:LAUNCH_ARGS};
    failedIsolation=LEDGER.allowedOffLoopback.length>0||LEDGER.bypassed.length>0||LEDGER.wsBypassed.length>0||outsideSelftest.length>0;
    fs.writeFileSync(path.join(out,mode==='selftest'?'selftest.json':'v1-browser-results.json'),JSON.stringify(receipt,null,1)+'\n');}
  const i=receipt.isolation;
  console.log(JSON.stringify({mode,layout,isolation:{seen:i.requestsSeen,continuedLoopback:i.continuedLoopback,allowedOffLoopback:i.allowedOffLoopback,fulfilledFixture:i.fulfilledFixture,fulfilledFont:i.fulfilledFont,aborted:i.aborted,abortedHosts:i.abortedHosts,bypassed:i.bypassed.length,wsBypassed:i.wsBypassed.length},
    ...(mode==='selftest'?{selftest:receipt.selftest.checks,pass:receipt.selftest.pass}:{summary:receipt.summary})}));
  if(failedIsolation){console.error('NETWORK ISOLATION FAILURE');process.exitCode=3;}
  else if(mode==='selftest'&&!receipt.selftest.pass)process.exitCode=1;
  else if(mode!=='selftest'&&ROWS.some(r=>r.result!=='PASS'))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=2;});
