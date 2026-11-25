'use strict';
// R003F F-LEG-3, B0 only. The caller supplies a git archive of the runtime.
// Store full cards locally for the owner. The summary contains hashes and numbers.
require('./v1_net_guard.cjs').install();
const iso = require('./r0033_isolation.cjs');
const {buildMasks,measure,calendarLightVerdict,compareCards,assertOwnerScene,assertOwnerMeasurement} = require('./r003f_p1.cjs');
const {parseArgs} = require('node:util'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const {values:a} = parseArgs({options:Object.fromEntries(['root','out','engine','dpr','playwright','pngjs','executable'].map(k=>[k,{type:'string'}]))});
const root = fs.realpathSync(a.root), out = path.resolve(a.out), engine = a.engine || 'chromium', dpr = Number(a.dpr||1);
assert.ok(['chromium','firefox','webkit'].includes(engine) && [1,2].includes(dpr));
const pw = require(a.playwright||'playwright'), {PNG} = require(a.pngjs||'pngjs');
const launcher = {[engine]:{launch:opts=>pw[engine].launch({...opts,
  ...(a.executable ? {executablePath:a.executable} : {}), ...(engine==='chromium' ? {chromiumSandbox:true} : {})})}};
const epoch = '2026-11-15T09:42:00.000Z', zone = 'America/New_York';
const hash = '#lat=28.54&lon=-81.38&label=Orlando&method=2&tz=America%2FNew_York&seed=1&qa=1';
const digest = b=>crypto.createHash('sha256').update(b).digest('hex');
const ordinary = JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json')));
const types = {'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm'};
const server = http.createServer((req,res)=>{
  try {
    const url = new URL(req.url,'http://127.0.0.1');
    const file = fs.realpathSync(path.join(root,decodeURIComponent(url.pathname)));
    if (!file.startsWith(root+path.sep) || !fs.statSync(file).isFile()) throw Error('not a file');
    res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream','cache-control':'no-store'});
    fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
  } catch {res.writeHead(404);res.end();}
});
function prayer(url) {
  if (url.hostname!=='api.aladhan.com') return null;
  const match=/^\/v1\/timings\/(\d\d)-(\d\d)-(\d{4})$/.exec(url.pathname);
  if (!match) return null;
  const [,day,month,year]=match, r=structuredClone(ordinary);
  r.date.gregorian={date:[day,month,year].join('-'),day,year,month:{number:+month,
    en:new Intl.DateTimeFormat('en',{month:'long',timeZone:'UTC'}).format(new Date(Date.UTC(+year,+month-1,+day)))}};
  r.meta.timezone=zone;
  return {code:200,status:'OK',data:r};
}
function clearWeather() {
  const original=window.fetch.bind(window);
  window.__r003fWeatherReads=0;
  window.fetch=(input,options)=>{
    const url=new URL(input.url||input,location.href);
    if (url.hostname!=='api.open-meteo.com' || url.pathname!=='/v1/forecast') return original(input,options);
    window.__r003fWeatherReads++;
    const fahrenheit=url.searchParams.get('temperature_unit')==='fahrenheit';
    const body={timezone:'America/New_York',utc_offset_seconds:-18000,elevation:30,
      current:{time:'2026-11-15T04:30',interval:900,weather_code:0,cloud_cover:0,is_day:0,visibility:24000,
        temperature_2m:fahrenheit?70:21,apparent_temperature:fahrenheit?70:21,relative_humidity_2m:55,dew_point_2m:fahrenheit?53:12,
        wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,precipitation:0}};
    return Promise.resolve(new Response(JSON.stringify(body),{headers:{'Content-Type':'application/json'}}));
  };
}
function facts() {
  const c=document.querySelector('.c'), b=c.getBoundingClientRect(), r=document.querySelector('.moccluder').getBoundingClientRect();
  const state=window.SalahMoonRuntime?.observe()?.state, q=window.qaState?.(), m=q?.moonTruth;
  return {card:[b.width,b.height],disc:{cx:r.x-b.x+r.width/2,cy:r.y-b.y+r.height/2,r:r.width/2},
    now:new Date().toISOString(),motionReduced:matchMedia('(prefers-reduced-motion: reduce)').matches,ready:c.classList.contains('moon-ready'),composed:c.classList.contains('real-sky-composed'),
    source:state?.visibleSource,quality:state?.quality,profile:state?.accepted?.scene?.profile?.profile_id,
    acceptedFraction:state?.accepted?.scene?.fraction,waxing:state?.accepted?.scene?.waxing,
    nativeFraction:state?.currentNativeFraction,nativeWaxing:window.SalahMoonHost?.capture()?.waxing,
    moonAltitude:m?.moonAltitudeDeg,moonlightOpacity:m?.moonlightOpacity,
    light:m?.lunarLight,moonGroup:getComputedStyle(c).getPropertyValue('--moongrp').trim(),
    calendarVisible:m?.calendarMoonVisible,displayMode:m?.displayMode,
    groupOpacity:Number(getComputedStyle(c.querySelector('.moon')).opacity),
    featureOpacity:Number(getComputedStyle(c.querySelector('.mfeatures')).opacity),
    weatherCode:q?.wxTruth.rawCode,weatherFixtureReads:window.__r003fWeatherReads,prayerLoaded:q?.cache.prayerLoaded};
}
async function capture(page,tag,report) {
  try {
    await page.waitForFunction(()=>{
      const c=document.querySelector('.c'), s=window.SalahMoonRuntime?.observe()?.state;
      return c?.classList.contains('moon-ready') && c.classList.contains('real-sky-composed') &&
        s?.visibleSource==='refined-terrain' && s.quality==='empirical-adaptive';
    },null,{timeout:150000,polling:500});
  } catch {
    const state=await page.evaluate(facts);
    throw Error(tag+' refined capture unavailable: '+JSON.stringify(state));
  }
  await page.waitForTimeout(2500);
  const state=await page.evaluate(facts);
  const png=await page.locator('.c').screenshot(), decoded=PNG.sync.read(png);
  const sha256=digest(png), lightVerdict=calendarLightVerdict(state);
  fs.writeFileSync(path.join(out,tag+'.png'),png);
  report.captures[tag]={state,sha256,lightVerdict};
  if(lightVerdict==='FAIL') {
    const error=new Error(tag+' calendar-only scene reports physical light');
    error.code='R003F_ANDON'; throw error;
  }
  assert.equal(lightVerdict,'PASS',tag+' incomplete or off-regime light observation');
  assertOwnerScene(tag,state);
  assert.deepEqual(state.card,[325,530]); assert.deepEqual([decoded.width,decoded.height],[325*dpr,530*dpr]);
  assert.equal(state.now,epoch); assert.equal(state.motionReduced,true); assert.equal(state.ready,true); assert.equal(state.composed,true);
  assert.equal(state.quality,'empirical-adaptive'); assert.equal(state.source,'refined-terrain');
  assert.equal(state.weatherCode,0); assert.equal(state.prayerLoaded,true);
  return {state,pixels:decoded.data};
}
function readUiMask({disc,dpr}) {
  const card=document.querySelector('.c').getBoundingClientRect();
  const headerRects=[...document.querySelectorAll('.h *')].map(el=>el.getBoundingClientRect()).filter(r=>r.width&&r.height)
    .map(r=>[r.left-card.left,r.top-card.top,r.right-card.left,r.bottom-card.top]);
  const width=325*dpr, allowed=[];
  for (let y=0; y<530*dpr; y++) for (let x=0; x<width; x++) {
    const cx=(x+0.5)/dpr,cy=(y+0.5)/dpr, radius=Math.hypot(cx-disc.cx,cy-disc.cy)/disc.r;
    if (radius<1.08 || radius>1.6) continue;
    const top=document.elementsFromPoint(card.x+cx,card.y+cy)[0];
    if (top?.closest('.sky,.moon,.atmo,.real-sky-canvas,.real-sky-preview,.moon-detail-canvas')) allowed.push(y*width+x);
  }
  return {allowed,headerRects};
}
async function main() {
  fs.mkdirSync(out,{mode:0o700}); // A fresh location prevents mixing cells from different runs.
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin='http://127.0.0.1:'+server.address().port;
  let S;
  const report={protocol:'R003F/P1/B0-owner/2',engine,dpr,epoch,zone,hash,
    indexSha256:digest(fs.readFileSync(path.join(root,'index.html'))), captures:{}};
  try {
    S=await iso.launch(launcher,engine); report.version=S.browser.version();
    const C=await S.context({viewport:{width:325,height:530},deviceScaleFactor:dpr,locale:'en-US',timezoneId:zone,reducedMotion:'reduce'},{origin,fixture:prayer});
    await C.context.addInitScript(clearWeather);
    const open=async suffix=>{
      const p=await C.newPage(); await p.clock.setFixedTime(new Date(epoch));
      await p.goto(origin+'/index.html'+hash+suffix); return p;
    };
    const offsetPage=await open('&simMoon=0.01&simWax=1');
    const offset=await capture(offsetPage,'offset',report); await offsetPage.close();
    const p=await open(''), base=await capture(p,'b0',report), repeat=await capture(p,'b0-repeat',report);
    const ui=await p.evaluate(readUiMask,{disc:base.state.disc,dpr});
    const diff=compareCards(dpr,base.state.disc,base.pixels,repeat.pixels);
    report.repeatEnvelope={changedPixels:diff.changedPixels,outside106R:diff.outside.length,maxChannelCode:diff.maxChannelCode};
    const census=path.join(out,'outside-repeat.jsonl');
    fs.writeFileSync(census,'');
    for(let i=0;i<diff.outside.length;i+=256) {
      const points=diff.outside.slice(i,i+256);
      const stacks=await p.evaluate(({points,dpr})=>{
        const card=document.querySelector('.c').getBoundingClientRect();
        return points.map(({x,y})=>document.elementsFromPoint(card.x+(x+0.5)/dpr,card.y+(y+0.5)/dpr)
          .map(el=>({tag:el.localName,id:el.id,classes:[...el.classList]})));
      },{points,dpr});
      fs.appendFileSync(census,points.map((point,j)=>JSON.stringify({...point,hitStack:stacks[j]})).join('\n')+'\n');
    }
    await p.evaluate(()=>window.SalahMoonRuntime.setProfile('reference'));
    const reference=await capture(p,'reference',report);
    assert.ok(offset.state.weatherFixtureReads+base.state.weatherFixtureReads>0,'weather fixture was never consumed');
    assert.ok(S.ledger.requests.some(r=>r.action==='fulfill'&&r.host==='api.aladhan.com'),'no re-dated prayer fixture was consumed');
    assert.deepEqual(offset.state.disc,base.state.disc);
    for (const b of [repeat,reference]) {
      assert.deepEqual(b.state.disc,base.state.disc);
      assert.equal(b.state.acceptedFraction,base.state.acceptedFraction);
    }
    const allowed=new Uint8Array(325*530*dpr*dpr);
    for (const i of ui.allowed) allowed[i]=1;
    const masks=buildMasks({dpr,fraction:base.state.acceptedFraction,disc:base.state.disc,offsetDisc:offset.state.disc,
      newMoon:offset.pixels,reference:reference.pixels,headerRects:ui.headerRects,topIsSkyOrMoon:allowed});
    report.metrics=measure(masks,base.pixels); report.repeatMetrics=measure(masks,repeat.pixels);
    report.ui={headerRects:ui.headerRects,admittedInRawAnnulus:ui.allowed.length};
    assertOwnerMeasurement(report.metrics);
    assertOwnerMeasurement(report.repeatMetrics);
    report.status='MEASURED'; await C.context.close();
  } catch(error) {
    const andon=error.code==='R003F_ANDON';
    report.status=andon?'FAIL (Andon)':'INCOMPLETE'; report.error=error.message; process.exitCode=andon?4:2;
  }
  finally {
    if(S){
      await S.close(); report.isolation=S.verdict();
      fs.writeFileSync(path.join(out,'network.jsonl'),S.ledger.requests.map(x=>JSON.stringify(x)).join('\n')+'\n');
      if(!report.isolation.ok){report.status='ISOLATION FAIL';process.exitCode=3;}
    }
    server.close();
    fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({status:report.status,error:report.error,isolation:report.isolation,metrics:report.metrics}));
    // A launch rejection predates the returned isolation-session handle, so the
    // shared utility's refusing proxy cannot be closed by the caller.
    if (!S) process.exit(process.exitCode || 2);
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
