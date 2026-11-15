'use strict';
// Precipitation-presentation evaluation (research only, 2026-11-15). Adapted copy of the sky-survey stage-1 library
// (tools/qa/sky_survey_lib.cjs on the survey branch) with: per-fixture gust and showers fields, and a loopback guard
// (every non-loopback request is fulfilled from a stub or aborted; log.continuedExternal must stay empty).
// Original header: Sky-quality survey (stage 1, research-only) shared library: loopback static server, fully stubbed providers
// (Aladhan prayer record computed per site/date, Open-Meteo weather fixture, RainViewer empty manifest; every other
// non-loopback request is aborted), a deterministic solar/prayer calculator, scene opening under a MOCKED clock, and
// the in-page state/geometry probes. Imported by sky_survey_capture.cjs and sky_survey_seq.cjs. Never contacts a
// real provider. No product file is read other than the served generated tree and tests/r0002-ordinary.json.
const fs=require('fs'),path=require('path'),http=require('http');
const MIME={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm','.png':'image/png','.bin':'application/octet-stream','.gz':'application/gzip','.css':'text/css','.svg':'image/svg+xml','.webp':'image/webp','.jpg':'image/jpeg','.woff2':'font/woff2'};
const SITES={
  madinah:{key:'madinah',lat:24.47,lon:39.61,label:'Madinah',method:4,tz:'Asia/Riyadh',fajr:18.5,isha:null,ishaMin:90},
  orlando:{key:'orlando',lat:28.54,lon:-81.38,label:'Orlando',method:2,tz:'America/New_York',fajr:15,isha:15,ishaMin:null}};
const DATES={equinox:'2026-09-23',solstice:'2026-12-21'};
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const HMONTHS=['Muharram','Safar',"Rabi' al-awwal","Rabi' al-thani",'Jumada al-ula','Jumada al-akhirah','Rajab',"Sha'ban",'Ramadan','Shawwal',"Dhu al-Qi'dah",'Dhu al-Hijjah'];

// ---------- time zone helpers ----------
function tzParts(ms,tz){const p={};for(const x of new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(ms)))p[x.type]=+x.value;return p;}
function localToUtc(dateStr,hhmm,tz){ // 'YYYY-MM-DD','HH:MM[:SS]' in tz -> epoch ms (fixed-offset zones and DST-stable days)
  const [y,mo,d]=dateStr.split('-').map(Number),[h,mi,s]=hhmm.split(':').map(Number);const guess=Date.UTC(y,mo-1,d,h,mi||0,s||0);
  const p=tzParts(guess,tz);const off=Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second)-guess;return guess-off;}
function fmtLocal(ms,tz){const p=tzParts(ms,tz);const z=n=>String(n).padStart(2,'0');return `${p.year}-${z(p.month)}-${z(p.day)} ${z(p.hour)}:${z(p.minute)}:${z(p.second)}`;}
function hhmm(ms,tz){const p=tzParts(ms,tz);const z=n=>String(n).padStart(2,'0');return `${z(p.hour)}:${z(p.minute)}`;}

// ---------- low-precision solar position (NOAA/Meeus-style, accurate to ~0.01 deg: ample for scheduling scenes) ----------
function solarEl(ms,lat,lon){
  const d=ms/86400000+2440587.5-2451545.0,g=(357.529+0.98560028*d)*Math.PI/180,q=280.459+0.98564736*d;
  const L=(q+1.915*Math.sin(g)+0.020*Math.sin(2*g))*Math.PI/180,e=(23.439-0.00000036*d)*Math.PI/180;
  const ra=Math.atan2(Math.cos(e)*Math.sin(L),Math.cos(L)),dec=Math.asin(Math.sin(e)*Math.sin(L));
  const gmst=(18.697374558+24.06570982441908*d)%24,lst=((gmst*15+lon)%360)*Math.PI/180,H=lst-ra,phi=lat*Math.PI/180;
  return Math.asin(Math.sin(phi)*Math.sin(dec)+Math.cos(phi)*Math.cos(dec)*Math.cos(H))*180/Math.PI;}
// solar events on a local civil day of a site: noon (max elevation), sunrise/sunset (-0.833), and any elevation crossing
function dayEvents(site,dateStr){
  const t0=localToUtc(dateStr,'00:00',site.tz),el=m=>solarEl(m,site.lat,site.lon);let noon=t0,best=-99;
  for(let m=t0;m<t0+86400000;m+=60000){const e=el(m);if(e>best){best=e;noon=m;}}
  const cross=(target,from,to)=>{for(let m=from;m<to;m+=60000)if((el(m)-target)*(el(m+60000)-target)<=0)return m;return null;};
  const rising=(target)=>cross(target,t0,noon),setting=(target)=>cross(target,noon,t0+86400000);
  return {noon,maxEl:best,t0,rise:(t)=>rising(t),set:(t)=>setting(t),el};}
function prayerTimings(site,dateStr){
  const ev=dayEvents(site,dateStr),sr=ev.rise(-0.833),ss=ev.set(-0.833),fa=ev.rise(-site.fajr);
  const isha=site.ishaMin!=null?ss+site.ishaMin*60000:ev.set(-site.isha);
  // Asr (shadow = 1 x object + noon shadow): elevation where tan(el)=1/(1+tan|lat-dec|) approximated with noon altitude
  const noonEl=ev.maxEl,tn=Math.tan((90-noonEl)*Math.PI/180),asrEl=Math.atan(1/(1+tn))*180/Math.PI,asr=ev.set(asrEl);
  const f=m=>hhmm(m,site.tz);
  return {Fajr:f(fa),Sunrise:f(sr),Dhuhr:f(ev.noon+60000*2),Asr:f(asr),Sunset:f(ss),Maghrib:f(ss),Isha:f(isha),_ms:{fajr:fa,sunrise:sr,noon:ev.noon,asr,sunset:ss,isha}};}
// named scene times by solar elevation (morning/evening branches) for a site/date -> epoch ms
function sceneTimes(site,dateStr){
  const ev=dayEvents(site,dateStr),R=t=>ev.rise(t),S=t=>ev.set(t),sr=R(-0.833),ss=S(-0.833),mid=(a,b)=>Math.round((a+b)/2/60000)*60000;
  return {
    'predawn-night':R(-22)??R(-19),'astro-twilight':R(-15),'nautical-twilight':R(-9),'civil-twilight':R(-3),'sunrise':sr,'golden-am':R(5),
    'mid-morning':mid(sr,ev.noon),'solar-noon':ev.noon,'afternoon':mid(ev.noon,ss),'golden-pm':S(5),'sunset':ss,'blue-hour':S(-5),
    'dusk':S(-12),'night-early':S(-19)??S(-15),'deep-night':localToUtc(dateStr,'02:00',site.tz)+86400000};}

// ---------- Aladhan record ----------
const ordinaryPath=path.join(__dirname,'..','..','tests','r0002-ordinary.json');
function prayerRecord(site,dayDDMMYYYY,ordinary){
  const [d,mo,y]=dayDDMMYYYY.split('-').map(Number),dateStr=`${y}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  const r=JSON.parse(JSON.stringify(ordinary)),t=prayerTimings(site,dateStr);
  r.meta.timezone=site.tz;Object.assign(r.timings,{Fajr:t.Fajr,Sunrise:t.Sunrise,Dhuhr:t.Dhuhr,Asr:t.Asr,Sunset:t.Sunset,Maghrib:t.Maghrib,Isha:t.Isha});
  const noonUtc=Date.UTC(y,mo-1,d,12);const hp={};for(const x of new Intl.DateTimeFormat('en-u-ca-islamic-umalqura-nu-latn',{day:'numeric',month:'numeric',year:'numeric'}).formatToParts(new Date(noonUtc)))hp[x.type]=+x.value;
  r.date.gregorian={...r.date.gregorian,date:dayDDMMYYYY,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};
  r.date.hijri={...r.date.hijri,date:`${String(hp.day).padStart(2,'0')}-${String(hp.month).padStart(2,'0')}-${hp.year}`,day:String(hp.day).padStart(2,'0'),month:{number:hp.month,en:HMONTHS[hp.month-1]},year:String(hp.year)};
  return r;}

// ---------- Open-Meteo fixture ----------
// W: {code,temp(F),hum,wind(m/s? the widget requests mph/its own units; value passed through),wdir,cloud,low,mid,high,vis(m),precip(mm),rain,snow,dew}
const WX_BASE={code:0,temp:72,hum:35,dew:40,wind:3,wdir:225,gust:null,cloud:0,low:0,mid:0,high:0,vis:24000,precip:0,rain:0,showers:0,snow:0};
function offSec(ms,tz){const p=tzParts(ms,tz);return Math.round((Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second)-Math.floor(ms/1000)*1000)/1000);}
function openMeteoBody(site,W,nowMs,wxFn){
  const iso=ms=>{const p=tzParts(ms,site.tz),z=n=>String(n).padStart(2,'0');return `${p.year}-${z(p.month)}-${z(p.day)}T${z(p.hour)}:${z(p.minute)}`;};
  const q=Math.floor(nowMs/900000)*900000,h=Math.floor(nowMs/3600000)*3600000,cw=wxFn?wxFn(q):W,x=(w,k)=>w[k]??WX_BASE[k];
  const cur={time:iso(q),interval:900,weather_code:x(cw,'code'),temperature_2m:x(cw,'temp'),apparent_temperature:x(cw,'temp')-2,relative_humidity_2m:x(cw,'hum'),dew_point_2m:x(cw,'dew'),
    wind_speed_10m:x(cw,'wind'),wind_direction_10m:x(cw,'wdir'),wind_gusts_10m:cw.gust!=null?cw.gust:x(cw,'wind')*1.5,cloud_cover:x(cw,'cloud'),cloud_cover_low:x(cw,'low'),cloud_cover_mid:x(cw,'mid'),cloud_cover_high:x(cw,'high'),
    precipitation:x(cw,'precip'),rain:x(cw,'rain'),showers:x(cw,'showers'),snowfall:x(cw,'snow'),is_day:solarEl(q,site.lat,site.lon)>-0.8?1:0,visibility:x(cw,'vis')};
  const hrs=[-1,0,1,2,3,4].map(k=>h+k*3600000),col=k=>hrs.map(t=>x(wxFn?wxFn(t):W,k));
  return {latitude:site.lat,longitude:site.lon,timezone:site.tz,utc_offset_seconds:offSec(nowMs,site.tz),elevation:30,current:cur,
    hourly:{time:hrs.map(iso),temperature_2m:col('temp'),apparent_temperature:col('temp').map(v=>v-2),relative_humidity_2m:col('hum'),dew_point_2m:col('dew'),cloud_cover:col('cloud'),cloud_cover_low:col('low'),cloud_cover_mid:col('mid'),cloud_cover_high:col('high'),
      wind_speed_10m:col('wind'),wind_direction_10m:col('wdir'),wind_gusts_10m:hrs.map(t=>{const w=wxFn?wxFn(t):W;return w.gust!=null?w.gust:x(w,'wind')*1.5;}),precipitation:col('precip'),weather_code:col('code'),visibility:col('vis'),is_day:hrs.map(t=>solarEl(t,site.lat,site.lon)>-0.8?1:0)}};}

// ---------- server + browser ----------
function serve(rootArg){const root=path.resolve(rootArg);const srv=http.createServer((q,s)=>{const p=path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){s.writeHead(404);return s.end();}
  s.writeHead(200,{'content-type':MIME[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(s);});
  return new Promise(r=>srv.listen(0,'127.0.0.1',()=>r({srv,base:'http://127.0.0.1:'+srv.address().port})));}
const CORS={'access-control-allow-origin':'*'};

// Opens a fresh context+page with all providers stubbed. opts:{engine browser, site, date, localTime|utcMs, wx:{...}|null, wxFn, hash(extra fragment), clock:'running'|'paused', reduced:bool}
function siteFor(u,dflt){const m=/latitude=(-?[\d.]+)/.exec(u);if(!m)return dflt;for(const k in SITES)if(Math.abs(SITES[k].lat-parseFloat(m[1]))<0.01)return SITES[k];return dflt;}
async function openScene(browser,base,ordinary,o){
  const site=o.site,ctx=await browser.newContext({...(o.video?{recordVideo:{dir:o.video,size:{width:325,height:530}}}:{}),serviceWorkers:'block',viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:site.tz,locale:'en-US',reducedMotion:o.reduced?'reduce':'no-preference'});
  const log={aborted:[],requests:[],continuedExternal:[]};let page=null;
  await ctx.route('**/*',async r=>{const u=r.request().url();log.all=(log.all||0)+1;if(u.startsWith('data:')||u.startsWith('blob:'))return r.continue();
    if(u.startsWith(base)){const h=new URL(u).hostname;if(h!=='127.0.0.1'&&h!=='localhost'&&h!=='[::1]'){log.continuedExternal.push(u);return r.abort();}return r.continue();}   // loopback only
    const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u),ls=siteFor(u,site);
    if(m){log.requests.push('aladhan:'+ls.key);return r.fulfill({status:200,contentType:'application/json',headers:CORS,body:JSON.stringify({code:200,status:'OK',data:prayerRecord(ls,m[1],ordinary)})});}
    if(u.includes('api.open-meteo.com')){let now=o.utcMs;try{now=await page.evaluate(()=>Date.now());}catch(e){}log.requests.push('open-meteo:'+ls.key+'@'+now);
      if(!o.wx&&!o.wxFn)return r.abort();return r.fulfill({status:200,contentType:'application/json',headers:CORS,body:JSON.stringify(openMeteoBody(ls,{...WX_BASE,...(o.wx||{})},now,o.wxFn))});}
    if(u.includes('api.rainviewer.com')){log.requests.push('radar');return r.fulfill({status:200,contentType:'application/json',headers:CORS,body:'{"version":"2.0","generated":0,"host":"https://tilecache.rainviewer.com","radar":{"past":[],"nowcast":[]}}'});}
    log.aborted.push(new URL(u).host);return r.abort();});
  page=await ctx.newPage();page.on('pageerror',e=>(log.errors||(log.errors=[])).push(String(e.message).slice(0,200)));
  await page.clock.install({time:new Date(o.utcMs)});if(o.clock==='paused')await page.clock.pauseAt(new Date(o.utcMs+1000));else await page.clock.resume();
  const frag=`lat=${site.lat}&lon=${site.lon}&label=${encodeURIComponent(site.label)}&method=${site.method}&tz=${encodeURIComponent(site.tz)}&seed=1&qa=1${o.hash||''}`;
  const url=base+'/index.html#'+frag;await page.goto(url,{waitUntil:o.waitUntil||'load'});
  return {ctx,page,log,url:'/index.html#'+frag};}

// Readiness: refined sky published + clouds (when applicable) + prayer rows loaded. Polls real time (clock running) or steps the mocked clock (paused).
const READY=`(()=>{try{const q=window.qaState(),rs=q.realSky||{};return {prayer:!!q.cache.prayerLoaded,rsStatus:rs.status||null,rsRenders:rs.renders??null,cloudsReady:!!q.clouds.ready,pub:q.clouds.publication&&q.clouds.publication.state,wx:q.wx&&q.wx.code}}catch(e){return {err:String(e)}}})()`;
async function waitReady(page,o={}){const max=o.maxMs||15000,t0=Date.now();let s=null;
  while(Date.now()-t0<max){s=await page.evaluate(READY);if(s&&s.prayer&&s.rsStatus&&/ready|published|ok|refined|rendered/i.test(String(s.rsStatus))&&(s.rsRenders??1)>0)break;
    if(o.step)await page.clock.runFor(o.step);else await page.waitForTimeout(250);}
  return {state:s,waitedMs:Date.now()-t0};}

// ---------- in-page probes ----------
// qaState excerpt (JSON-safe) + optics variables + prayer text geometry
const OPTIC_VARS=['--ray','--anticrep','--sunray','--sunamt','--sunvx','--sunvy','--sunx2','--sunlift','--sunpulse','--sundisc','--sunhalo','--sundogs','--sunpillar','--rain-op','--grain','--mrad','--mhalo','--mparhelia','--mcorona','--mbeam','--moonglow'];
const STATE=`(()=>{const c=document.querySelector('.c'),cs=c?getComputedStyle(c):null,g=k=>cs?cs.getPropertyValue(k).trim():null;const vars={};for(const k of ${JSON.stringify(OPTIC_VARS)}){const v=g(k);if(v)vars[k]=v;}
 let q=null;try{q=window.qaState();}catch(e){}
 const cv=document.querySelector('.cloudcanvas');let cloud=null;try{const W=cv.width,H=cv.height,d=cv.getContext('2d').getImageData(0,0,W,H).data;let n=0,sa=0,sx=0,sy=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){const a=d[(y*W+x)*4+3];if(a>16)n++;sa+=a;sx+=x*a;sy+=y*a;}cloud={w:W,h:H,coverFrac:n/(W*H),meanAlpha:sa/(W*H*255),cx:sa?sx/sa/W:null,cy:sa?sy/sa/H:null};}catch(e){cloud={error:String(e)}}
 const ex=q?{sunEl:q.sunEl,wx:q.wx,wxTruth:q.wxTruth&&{currentWeatherSource:q.wxTruth.currentWeatherSource,forecastTrackSource:q.wxTruth.forecastTrackSource,radarSource:q.wxTruth.radarSource,radarPrecipMm:q.wxTruth.radarPrecipMm,radarConfirming:q.wxTruth.radarConfirming,current:q.wxTruth.current,conditionState:q.wxTruth.conditionState,observedPresent:q.wxTruth.observedPresent,permissions:q.wxTruth.permissions,visualPermissions:q.wxTruth.visualPermissions,modelDowngrade:q.weatherCandidate&&q.weatherCandidate.modelDowngrade,renderCode:q.weatherCandidate&&q.weatherCandidate.renderCode,retryRenewal:q.wxTruth.retry&&q.wxTruth.retry.renewal&&q.wxTruth.retry.renewal.stage},
  moonTruth:q.moonTruth&&{phaseFraction:q.moonTruth.phaseFraction,waxing:q.moonTruth.waxing,moonAltitudeDeg:q.moonTruth.moonAltitudeDeg,displayMode:q.moonTruth.displayMode,physicalMoonVisible:q.moonTruth.physicalMoonVisible,calendarMoonVisible:q.moonTruth.calendarMoonVisible,moonSkyOpacity:q.moonTruth.moonSkyOpacity,moonCalendarOpacity:q.moonTruth.moonCalendarOpacity,moonlightOpacity:q.moonTruth.moonlightOpacity,reason:q.moonTruth.reason},
  clouds:q.clouds&&{low:q.clouds.low,mid:q.clouds.mid,high:q.clouds.high,ready:q.clouds.ready,density:q.clouds.density,pubState:q.clouds.publication&&q.clouds.publication.state,pubReason:q.clouds.publication&&q.clouds.publication.reason,lighting:q.clouds.lighting,alpha:q.clouds.alpha},
  stars:q.stars,sky:q.sky,realSky:q.realSky&&{status:q.realSky.status,renders:q.realSky.renders,frameUtcMs:q.realSky.frameUtcMs,errors:q.realSky.errors,composition:q.realSky.composition},cache:q.cache&&{prayerLoaded:q.cache.prayerLoaded,weatherSource:q.cache.weatherSource,weatherStale:q.cache.weatherStale,currentEligible:q.cache.currentEligible},
  weatherHeader:q.weatherHeader&&{label:q.weatherHeader.label,code:q.weatherHeader.code,temperature:q.weatherHeader.temperature,conditionState:q.weatherHeader.conditionState},renderFaults:q.renderFaults}:null;
 const g2=s=>{const e=document.querySelector(s);return e?e.textContent.trim():null};
 return {now:Date.now(),cls:c?c.className:null,data:c?{precip:c.dataset.precip,lightning:c.dataset.lightning,fx:c.dataset.fx}:null,vars,qa:ex,cloud,header:{wt:g2('#wt'),wi:g2('#wi'),loc:g2('.loc')},cn:g2('.cn')};})()`;
// text rectangles whose contrast is measured (label, time, countdown, header temp, date footer)
const RECTS=`(()=>{const out=[];const add=(name,el)=>{if(!el)return;const r=document.createRange();r.selectNodeContents(el);const b=r.getBoundingClientRect();if(b.width>0&&b.height>0)out.push({name,text:el.textContent.trim().slice(0,40),x:b.x,y:b.y,w:b.width,h:b.height});};
 document.querySelectorAll('.p').forEach((p,i)=>{add('row'+i+'-label',p.querySelector('b'));add('row'+i+'-time',p.querySelector('.tm'));});
 add('title',document.querySelector('.cn'));add('bigclock',document.querySelector('.nt'));add('countdown',document.querySelector('.left'));add('header-loc',document.querySelector('.loc'));add('header-temp',document.querySelector('#wt'));
 document.querySelectorAll('.d span,.d div').forEach((e,i)=>{if(!e.children.length&&e.textContent.trim())add('date'+i,e);});return out;})()`;

async function freeze(page,ms=1500){for(let i=0;i<5;i++){try{await page.clock.pauseAt(await page.evaluate(()=>Date.now())+ms*(i+1));break;}catch(e){if(i===4)throw e;}}await page.waitForTimeout(150);}

module.exports={SITES,DATES,fs,path,serve,openScene,waitReady,STATE,RECTS,freeze,localToUtc,fmtLocal,hhmm,solarEl,dayEvents,prayerTimings,sceneTimes,prayerRecord,openMeteoBody,WX_BASE,ordinaryPath,tzParts};
