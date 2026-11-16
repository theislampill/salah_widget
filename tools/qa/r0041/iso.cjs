'use strict';
// Copied unchanged in its isolation layers from docs/audit/startup-advisory-20261115/harness/iso.cjs at 2e9a6159 (via the
// Moon-reuse study, docs/audit/moon-refinement-reuse-20261116/harness/iso.cjs at e3248c92)
// (startup advisory, 2026-11-15). Only change: an optional deviceScaleFactor launch option (default 1).
// It is the ONE isolation helper every browser launch in the Moon-reuse feasibility audit goes through.
//
// Layers (all always on unless stated):
//  L1  Loopback origin servers (127.0.0.1 and localhost, one port each) serving the repository tree with
//      GitHub-Pages-like headers: Cache-Control max-age=600, weak ETag + Last-Modified derived from a "deploy"
//      instant, gzip Content-Encoding for every type except .gz/.png/.jpg/.woff2, 304 on matching validators.
//      redeploy() changes the validators without changing a byte. dateSkewMs back-dates the Date header so a
//      response is stored already aged (RFC 9111 4.2.3 apparent_age) - used to model "after max-age expiry".
//  L2  An isolation proxy on loopback. The browser is launched with it as its ONLY proxy and with loopback
//      bypass removed, so every request (page, worker, preconnect, prefetch, WebSocket CONNECT) reaches it.
//      Loopback targets are answered by L1 in-process; every other host is refused (403 / CONNECT refused) and
//      logged as blocked. Nothing is ever forwarded off the machine (there is no forwarding code at all).
//  L3  Chromium only: --host-resolver-rules maps every hostname except 127.0.0.1/localhost to NOTFOUND.
//  L4  mode 'route': a context-level route '**/*' (plus routeWebSocket) installed before any navigation:
//      loopback/data/blob continue, provider hosts fulfilled from synthetic fixtures, everything else aborted.
//      mode 'cache': L4 is NOT installed, because a Playwright route disables the HTTP cache (demonstrated by
//      selftest.cjs, "route-cache probe"); provider hosts are then answered by the in-page fetch shim (L5) and
//      L2/L3 remain the catch-all.
//  L5  In-page fetch shim (init script) answering prayer/weather/radar/geocoding from synthetic fixtures before
//      any network use, in both modes.
// Every request seen at any layer is logged {layer, host, type, outcome}. finish() FAILS (throws) if any
// request to a non-loopback host was allowed through at any layer.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),net=require('node:net'),zlib=require('node:zlib'),crypto=require('node:crypto');
// Global Playwright: set PLAYWRIGHT_PKG to its package directory (e.g. "$(npm root -g)/playwright") or NODE_PATH.
function loadPlaywright(){
  for(const c of [process.env.PLAYWRIGHT_PKG,'playwright'].filter(Boolean)){try{return require(c);}catch{}}
  throw new Error('playwright not found; set PLAYWRIGHT_PKG');
}
const LOOP=new Set(['127.0.0.1','localhost','[::1]','::1']);
const isLoopHost=h=>LOOP.has(String(h).toLowerCase());
const TYPES={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.mjs':'application/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm',
  '.gz':'application/gzip','.bin':'application/octet-stream','.txt':'text/plain; charset=utf-8','.ttf':'font/ttf','.woff2':'font/woff2'};
const NO_GZIP=new Set(['.gz','.png','.jpg','.jpeg','.woff2']);

// ---------------- fixtures (synthetic, deterministic) ----------------
const PRAYER_HOSTS=['api.aladhan.com'],WX_HOSTS=['api.open-meteo.com'],RADAR_HOSTS=['api.rainviewer.com','tilecache.rainviewer.com'],
  GEO_HOSTS=['nominatim.openstreetmap.org','ipinfo.io','get.geojs.io','api.zippopotam.us'],FONT_HOSTS=['fonts.googleapis.com','fonts.gstatic.com'];
function prayerFixture(day){const [d,m,y]=day.split('-').map(Number);
  return {code:200,status:'OK',data:{timings:{Fajr:'05:01',Sunrise:'06:18',Dhuhr:'11:54',Asr:'15:05',Maghrib:'17:30',Sunset:'17:30',Isha:'19:00',Imsak:'04:51',Midnight:'23:54'},
    meta:{timezone:'Asia/Riyadh',method:{id:4,name:'Umm Al-Qura',params:{Fajr:18.5,Isha:'90 min'}},latitude:24.47,longitude:39.61},
    date:{readable:`${d} Nov ${y}`,timestamp:String(Math.floor(Date.UTC(y,m-1,d)/1000)),gregorian:{date:day,format:'DD-MM-YYYY',day:String(d).padStart(2,'0'),weekday:{en:'Sunday'},month:{number:m,en:'November'},year:String(y)},
      hijri:{date:'24-05-1448',format:'DD-MM-YYYY',day:'24',weekday:{en:'Al Ahad'},month:{number:5,en:'Jumādá al-ūlá'},year:'1448'}}}};}
// In-page shim: same fixtures, answered inside the page before any network use (works in both modes).
function shimSource({wxCode=0,cloud=0}={}){return `(()=>{if(window.__ISO_SHIM__)return;window.__ISO_SHIM__=true;const nf=window.fetch.bind(window);
 const iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 const P=${prayerFixture.toString()};
 window.__isoShimLog=[];
 window.fetch=function(input,init){const u=String(input&&input.url||input);let h='';try{h=new URL(u,location.href).hostname;}catch{}
  if(h==='api.aladhan.com'){window.__isoShimLog.push({h,t:performance.now()});const m=/(\\d{2}-\\d{2}-\\d{4})/.exec(u);const now=new Date(Date.now()+3*3600000);
   const day=m?m[1]:String(now.getUTCDate()).padStart(2,'0')+'-'+String(now.getUTCMonth()+1).padStart(2,'0')+'-'+now.getUTCFullYear();return json(P(day));}
  if(h==='api.open-meteo.com'){window.__isoShimLog.push({h,t:performance.now()});const w=Date.now(),m=Math.floor(w/900000)*900000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},f);
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({latitude:24.47,longitude:39.61,timezone:'Asia/Riyadh',utc_offset_seconds:10800,elevation:600,current:{time:iso(m),interval:900,weather_code:${wxCode},temperature_2m:24,apparent_temperature:24,relative_humidity_2m:40,dew_point_2m:10,wind_speed_10m:3,wind_direction_10m:90,cloud_cover:${cloud},cloud_cover_low:${cloud},cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,visibility:24000,surface_pressure:950,is_day:1},
    hourly:{time:t,temperature_2m:arr(()=>24),weather_code:arr(()=>${wxCode}),precipitation:arr(()=>0),precipitation_probability:arr(()=>0),cloud_cover:arr(()=>${cloud}),cloud_cover_low:arr(()=>${cloud}),cloud_cover_mid:arr(()=>0),cloud_cover_high:arr(()=>0),relative_humidity_2m:arr(()=>40),dew_point_2m:arr(()=>10),wind_speed_10m:arr(()=>3),wind_direction_10m:arr(()=>90),visibility:arr(()=>24000),is_day:arr(()=>0)}});}
  if(${JSON.stringify(RADAR_HOSTS.concat(GEO_HOSTS))}.includes(h)){window.__isoShimLog.push({h,t:performance.now(),refused:true});return Promise.reject(new TypeError('isolation: provider refused in page'));}
  return nf(input,init);};})();`;}

// ---------------- L1 origin servers with Pages-like headers ----------------
class Origins{
  constructor({root,log,extra={}}){this.root=path.resolve(root);this.log=log;this.extra=extra;this.deployMs=Date.parse('2026-11-15T08:00:00Z');this.deploys=0;
    this.dateSkewMs=0;this.gz=new Map();this.servers=[];this.ports={};this.policy={};this.inflight=0;this.held=[];}
  redeploy(){this.deployMs+=60000;this.deploys++;}
  validators(size){const lm=new Date(Math.floor(this.deployMs/1000)*1000);return {etag:`W/"${Math.floor(this.deployMs/1000).toString(16)}-${size.toString(16)}"`,lastModified:lm.toUTCString(),lmMs:lm.getTime()};}
  body(file){const st=fs.statSync(file);const key=file+':'+st.mtimeMs;let e=this.gz.get(key);
    if(!e){const raw=fs.readFileSync(file);const ext=path.extname(file).toLowerCase();e={raw,gz:NO_GZIP.has(ext)?null:zlib.gzipSync(raw,{level:6})};this.gz.set(key,e);}return e;}
  handle(req,res,originLabel,via){
    const t0=Date.now();const u=new URL(req.url,'http://x');let pathname=decodeURIComponent(u.pathname);
    const rec={layer:via,origin:originLabel,host:req.headers.host,path:pathname,query:u.search,method:req.method,t0,
      inm:req.headers['if-none-match']||null,ims:req.headers['if-modified-since']||null,cacheControl:req.headers['cache-control']||null,pragma:req.headers.pragma||null};
    const finish=(status,bytes)=>{rec.status=status;rec.bytes=bytes;rec.ms=Date.now()-t0;this.log.push(rec);};
    if(this.extra[pathname]){const x=this.extra[pathname](u,req);res.writeHead(200,{'content-type':x.type||'text/html; charset=utf-8','cache-control':'no-store'});res.end(x.body);return finish(200,Buffer.byteLength(x.body));}
    const pol=this.policy[pathname];
    if(pol==='stall'){this.held.push(res);rec.held=true;return finish('held',0);}
    if(pol==='404'){res.writeHead(404,{'cache-control':'no-store'});res.end();return finish(404,0);}
    if(pathname.endsWith('/'))pathname+='index.html';
    const file=path.normalize(path.join(this.root,pathname));
    if(!file.startsWith(this.root)||!fs.existsSync(file)||fs.statSync(file).isDirectory()){res.writeHead(404,{'content-type':'text/plain'});res.end('not found');return finish(404,0);}
    const ext=path.extname(file).toLowerCase(),e=this.body(file),v=this.validators(e.raw.length);
    const date=new Date(Date.now()-this.dateSkewMs).toUTCString();
    const h={'content-type':TYPES[ext]||'application/octet-stream','cache-control':'max-age=600','etag':v.etag,'last-modified':v.lastModified,
      'date':date,'expires':new Date(Date.now()-this.dateSkewMs+600000).toUTCString(),'access-control-allow-origin':'*','vary':'Accept-Encoding','accept-ranges':'bytes'};
    const inmMatch=rec.inm&&rec.inm.split(',').map(s=>s.trim()).some(x=>x===v.etag||x==='*'||x.replace(/^W\//,'')===v.etag.replace(/^W\//,''));
    const imsOk=!rec.inm&&rec.ims&&Date.parse(rec.ims)>=v.lmMs;
    if(req.method==='GET'&&(inmMatch||imsOk)){res.writeHead(304,{etag:v.etag,'last-modified':v.lastModified,'cache-control':'max-age=600',date,expires:h.expires,vary:'Accept-Encoding'});res.end();return finish(304,0);}
    const useGz=e.gz&&/\bgzip\b/.test(req.headers['accept-encoding']||'');const buf=useGz?e.gz:e.raw;if(useGz)h['content-encoding']='gzip';h['content-length']=buf.length;
    res.writeHead(200,h);if(req.method==='HEAD'){res.end();return finish(200,0);}
    this.inflight++;res.on('close',()=>{this.inflight--;});
    res.end(buf,()=>finish(200,buf.length));rec.rawBytes=e.raw.length;rec.gzip=!!useGz;
  }
  async start(labels=['127.0.0.1','localhost']){
    for(const label of labels){const s=http.createServer((req,res)=>this.handle(req,res,label,'origin-direct'));
      await new Promise(r=>s.listen(0,'127.0.0.1',r));this.servers.push(s);this.ports[label]=s.address().port;}
    return this;}
  url(label,p){return `http://${label}:${this.ports[label]}${p}`;}
  close(){for(const r of this.held)try{r.destroy();}catch{}for(const s of this.servers)s.close();}
}

// ---------------- L2 isolation proxy ----------------
class IsoProxy{
  constructor({origins,log}){this.origins=origins;this.log=log;this.allowedExternal=0;}
  async start(){
    this.server=http.createServer((req,res)=>{let u;try{u=new URL(req.url);}catch{u=null;}
      const host=u?u.hostname:(req.headers.host||'').split(':')[0];const port=u?Number(u.port||80):0;
      if(u&&isLoopHost(host)){const label=Object.entries(this.origins.ports).find(([,p])=>p===port)?.[0];
        if(label){req.url=u.pathname+u.search;return this.origins.handle(req,res,label,'proxy-loopback');}
        this.log.push({layer:'proxy',host:host+':'+port,path:u.pathname,outcome:'blocked-unknown-loopback-port',t0:Date.now()});res.writeHead(502);return res.end();}
      this.log.push({layer:'proxy',host,path:u?u.pathname:req.url,method:req.method,outcome:'blocked',upgrade:req.headers.upgrade||null,t0:Date.now()});
      res.writeHead(403,{'content-type':'text/plain','cache-control':'no-store'});res.end('blocked by isolation proxy');});
    this.server.on('connect',(req,sock)=>{const [host]=String(req.url).split(':');
      this.log.push({layer:'proxy',host,path:'CONNECT '+req.url,method:'CONNECT',outcome:'blocked',t0:Date.now()});
      try{sock.end('HTTP/1.1 403 Forbidden\r\n\r\n');}catch{}});
    this.server.on('upgrade',(req,sock)=>{let host='';try{host=new URL(req.url).hostname;}catch{}
      this.log.push({layer:'proxy',host,path:req.url,method:'UPGRADE',outcome:'blocked',t0:Date.now()});try{sock.end('HTTP/1.1 403 Forbidden\r\n\r\n');}catch{}});
    this.server.on('clientError',(e,sock)=>{try{sock.destroy();}catch{}});
    await new Promise(r=>this.server.listen(0,'127.0.0.1',r));this.port=this.server.address().port;return this;}
  close(){this.server.close();}
}

// ---------------- launch ----------------
// opts: engine, mode ('route'|'cache'), profileDir (persistent; null = fresh non-persistent context),
//       viewport, reducedMotion ('reduce'|'no-preference'), fonts (route mode: fulfil font hosts with stand-in faces)
async function launch(env,opts){
  const PW=loadPlaywright();const {engine='chromium',mode='route',profileDir=null,reducedMotion='no-preference',viewport={width:325,height:530},
    timezoneId='Asia/Riyadh',fonts=null,headless=true,shim={},extraArgs=[],deviceScaleFactor=1}=opts;
  const log=env.log;const proxy={server:`http://127.0.0.1:${env.proxy.port}`,bypass:'<-loopback>'};
  const common={viewport,deviceScaleFactor,timezoneId,locale:'en-US',reducedMotion,serviceWorkers:'block',proxy};
  const launchOpts={headless};
  if(engine==='chromium')launchOpts.args=['--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1 , EXCLUDE localhost','--disable-background-networking',
    '--dns-prefetch-disable','--no-pings','--force-webrtc-ip-handling-policy=disable_non_proxied_udp','--webrtc-ip-handling-policy=disable_non_proxied_udp','--disable-component-update','--disable-domain-reliability','--disable-sync','--disable-features=NetworkPrediction,OptimizationHints,MediaRouter',...extraArgs];
  if(engine==='firefox')launchOpts.firefoxUserPrefs={'network.proxy.allow_hijacking_localhost':true,'network.proxy.no_proxies_on':'','network.dns.disablePrefetch':true,
    'network.predictor.enabled':false,'network.prefetch-next':false,'network.http.speculative-parallel-limit':0,'browser.safebrowsing.malware.enabled':false,
    'browser.safebrowsing.phishing.enabled':false,'app.update.enabled':false,'network.captive-portal-service.enabled':false,'network.connectivity-service.enabled':false,
    'dom.serviceWorkers.enabled':false,'media.peerconnection.enabled':false,'media.peerconnection.ice.proxy_only':true};
  let browser=null,context;
  if(profileDir){fs.mkdirSync(profileDir,{recursive:true});context=await PW[engine].launchPersistentContext(profileDir,{...launchOpts,...common});}
  else{browser=await PW[engine].launch({...launchOpts,proxy});context=await browser.newContext(common);}
  // A persistent context opens one about:blank page at launch; it has made no request. Record it, then route.
  const preexisting=context.pages().map(p=>p.url());
  const decisions=env.routeDecisions;
  if(mode==='route'){
    await context.route('**/*',async route=>{const r=route.request();const u=r.url();let host='';try{host=new URL(u).hostname;}catch{}
      const rec={layer:'route',host,type:r.resourceType(),url:u.slice(0,160),t0:Date.now()};
      if(u.startsWith('data:')||u.startsWith('blob:')){rec.outcome='continue-local';decisions.push(rec);return route.continue();}
      if(isLoopHost(host)){rec.outcome='continue-loopback';decisions.push(rec);return route.continue();}
      if(PRAYER_HOSTS.includes(host)){const m=/(\d{2}-\d{2}-\d{4})/.exec(u);rec.outcome='fulfilled-fixture';decisions.push(rec);
        return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(prayerFixture(m?m[1]:'15-11-2026'))});}
      if(fonts&&FONT_HOSTS.includes(host)){const f=fonts(u);if(f){rec.outcome='fulfilled-fixture';decisions.push(rec);return route.fulfill(f);}}
      rec.outcome='aborted';decisions.push(rec);return route.abort('blockedbyclient');});
    if(context.routeWebSocket)await context.routeWebSocket(/.*/,ws=>{let host='';try{host=new URL(ws.url()).hostname;}catch{}decisions.push({layer:'route-ws',host,url:ws.url(),outcome:'closed',t0:Date.now()});ws.close({code:1008,reason:'isolation'});});
  }
  await context.addInitScript(shimSource(shim));
  // Browser-level observation of every request (page and workers where the engine reports them).
  context.on('request',r=>{let host='';try{host=new URL(r.url()).hostname;}catch{}env.observed.push({layer:'browser',host,type:r.resourceType(),url:r.url().slice(0,200),t0:Date.now(),outcome:'issued'});});
  context.on('requestfinished',r=>{let host='';try{host=new URL(r.url()).hostname;}catch{}if(!isLoopHost(host)&&!/^(data|blob):/.test(r.url())){
      // a finished non-loopback request is only acceptable if a fixture fulfilled it (route layer); the shim never issues one
      const fulfilled=decisions.some(d=>d.url===r.url().slice(0,160)&&d.outcome==='fulfilled-fixture');env.observed.push({layer:'browser',host,url:r.url().slice(0,200),outcome:fulfilled?'finished-fixture':'finished-UNEXPECTED',t0:Date.now()});}});
  context.on('requestfailed',r=>{let host='';try{host=new URL(r.url()).hostname;}catch{}env.observed.push({layer:'browser',host,url:r.url().slice(0,200),outcome:'failed:'+(r.failure()?.errorText||''),t0:Date.now()});});
  return {browser,context,preexisting,close:async()=>{await context.close();if(browser)await browser.close();}};
}

async function createEnv({root,extra}={}){
  const env={log:[],observed:[],routeDecisions:[]};
  env.origins=await new Origins({root,log:env.log,extra}).start();
  env.proxy=await new IsoProxy({origins:env.origins,log:env.log}).start();
  env.summary=()=>summarise(env);
  env.finish=()=>{const s=summarise(env);env.origins.close();env.proxy.close();if(s.allowedExternal!==0)throw new Error('ISOLATION FAILURE: '+s.allowedExternal+' non-loopback request(s) allowed through: '+JSON.stringify(s.allowedList).slice(0,800));return s;};
  return env;
}
function summarise(env){
  const all=[...env.log,...env.routeDecisions,...env.observed];
  const ext=x=>x.host&&!isLoopHost(x.host.split(':')[0])&&!/^(data|blob)/.test(x.url||'');
  // "allowed through" = any non-loopback request that was answered by something other than our fixture/refusal:
  const allowedList=[...env.log.filter(x=>ext(x)&&x.layer!=='proxy'),                                 // a server log row for a foreign host (impossible by construction)
    ...env.log.filter(x=>x.layer==='proxy'&&x.outcome!=='blocked'&&ext(x)),
    ...env.routeDecisions.filter(x=>ext(x)&&!['aborted','fulfilled-fixture','closed'].includes(x.outcome)),
    ...env.observed.filter(x=>ext(x)&&x.outcome==='finished-UNEXPECTED')];
  const byHost={};for(const x of all.filter(ext)){const k=x.layer+' '+x.host+' '+(x.outcome||'');byHost[k]=(byHost[k]||0)+1;}
  return {totalRequests:{originServed:env.log.filter(x=>x.layer!=='proxy').length,proxyBlocked:env.log.filter(x=>x.layer==='proxy').length,
      routeDecisions:env.routeDecisions.length,browserObserved:env.observed.filter(x=>x.outcome==='issued').length},
    externalAttempts:all.filter(ext).length,externalByLayerHostOutcome:byHost,allowedExternal:allowedList.length,allowedList};
}
module.exports={createEnv,launch,loadPlaywright,isLoopHost,prayerFixture,shimSource,PRAYER_HOSTS,FONT_HOSTS};
