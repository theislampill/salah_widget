'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
function makeServer(root,indexFor){
  const types = {'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm'};
  return http.createServer((req,res)=>{
    try {
      const url = new URL(req.url,'http://127.0.0.1');
      const file = fs.realpathSync(path.join(root,decodeURIComponent(url.pathname)));
      if (!file.startsWith(root+path.sep) || !fs.statSync(file).isFile()) throw Error('not a file');
      if(url.pathname==='/index.html' && indexFor){
        const body=indexFor(url.searchParams.get('variant')||'B0');
        res.writeHead(200,{'content-type':'text/html','cache-control':'no-store'});res.end(body);return;
      }
      res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream','cache-control':'no-store'});
      fs.createReadStream(file).on('error',()=>res.destroy()).pipe(res);
    } catch {res.writeHead(404);res.end();}
  });
}
function prayerFixture(ordinary,zone){
  return function prayer(url) {
    if (url.hostname!=='api.aladhan.com') return null;
    const match=/^\/v1\/timings\/(\d\d)-(\d\d)-(\d{4})$/.exec(url.pathname);
    if (!match) return null;
    const [,day,month,year]=match, r=structuredClone(ordinary);
    r.date.gregorian={date:[day,month,year].join('-'),day,year,month:{number:+month,
      en:new Intl.DateTimeFormat('en',{month:'long',timeZone:'UTC'}).format(new Date(Date.UTC(+year,+month-1,+day)))}};
    r.meta.timezone=zone;
    return {code:200,status:'OK',data:r};
  }
}
function clearWeather(fixture={}) {
  const original=window.fetch.bind(window);
  window.__r003fWeatherReads=0;
  window.fetch=(input,options)=>{
    const url=new URL(input.url||input,location.href);
    if (url.hostname!=='api.open-meteo.com' || url.pathname!=='/v1/forecast') return original(input,options);
    window.__r003fWeatherReads++;
    const fahrenheit=url.searchParams.get('temperature_unit')==='fahrenheit';
    const body={timezone:'America/New_York',utc_offset_seconds:-18000,elevation:30,
      current:{time:fixture.time||'2026-11-15T04:30',interval:900,weather_code:0,cloud_cover:0,is_day:0,visibility:24000,
        temperature_2m:fahrenheit?70:21,apparent_temperature:fahrenheit?70:21,relative_humidity_2m:55,dew_point_2m:fahrenheit?53:12,
        wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,precipitation:0,...fixture}};
    // Accelerated preview reads the hourly track, including its preroll. Use
    // local wall-time strings from the same fixed Orlando scene as current.
    const stamp=Date.parse(body.current.time+'Z');
    body.hourly={time:[-2,-1,0,1,2].map(h=>new Date(stamp+3600000*h).toISOString().slice(0,16))};
    for(const key of Object.keys(body.current))if(!['time','interval'].includes(key))body.hourly[key]=body.hourly.time.map(()=>body.current[key]);
    return Promise.resolve(new Response(JSON.stringify(body),{headers:{'Content-Type':'application/json'}}));
  };
}
function facts() {
  const c=document.querySelector('.c'), b=c.getBoundingClientRect(), r=document.querySelector('.moccluder').getBoundingClientRect();
  const state=window.SalahMoonRuntime?.observe()?.state, q=window.qaState?.(), m=q?.moonTruth;
  return {motionClock:window.__r003fMotionObservation?.(),card:[b.width,b.height],disc:{cx:r.x-b.x+r.width/2,cy:r.y-b.y+r.height/2,r:r.width/2},
    now:new Date().toISOString(),motionReduced:matchMedia('(prefers-reduced-motion: reduce)').matches,ready:c.classList.contains('moon-ready'),composed:c.classList.contains('real-sky-composed'),
    utcMs:window.SalahMoonHost?.capture()?.utcMs,up:window.SalahMoonHost?.capture()?.up,
    sunEl:q?.sunEl, presentable:window.SalahMoonRuntime?.observe()?.wouldPresent,consumed:m?.lastConsumed,geometry:m?.currentGeometry,beam:getComputedStyle(c).getPropertyValue('--moonbeam').trim(),
    detail:window.SalahMoonDetail?.state, weatherFields:q?.wx,wx:q?.wxTruth, source:state?.visibleSource,quality:state?.quality,profile:state?.accepted?.scene?.profile?.profile_id,
    acceptedFraction:state?.accepted?.scene?.fraction,waxing:state?.accepted?.scene?.waxing,
    nativeFraction:window.SalahMoonHost?.capture()?.fraction,nativeWaxing:window.SalahMoonHost?.capture()?.waxing,
    moonAltitude:m?.moonAltitudeDeg,moonlightOpacity:m?.moonlightOpacity,
    light:m?.lunarLight,moonGroup:getComputedStyle(c).getPropertyValue('--moongrp').trim(),
    calendarVisible:m?.calendarMoonVisible,displayMode:m?.displayMode,
    visibility:['.moon','.moon-detail-canvas'].map(sel=>{const el=c.querySelector(sel);return el?getComputedStyle(el).visibility:null;}),
    groupOpacity:Number(getComputedStyle(c.querySelector('.moon')).opacity),
    featureOpacity:Number(getComputedStyle(c.querySelector('.mfeatures')).opacity),
    weatherCode:q?.wxTruth.rawCode,weatherFixtureReads:window.__r003fWeatherReads,prayerLoaded:q?.cache.prayerLoaded};
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
const assert=require('node:assert/strict');
const {weather}=require('./r003f_grid.cjs'),{inhibitedLightVerdict,assertOwnerScene}=require('./r003f_p1.cjs');
const finite=Number.isFinite;
function checkState(s,c,o){
  const minute=o.minute??Math.floor(Date.parse(c.epoch)/60000);
  const stamp=new Date(minute*60000),time=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(stamp).split(':').map(Number);
  const identity={epochMinute:minute,minute:time[0]*60+time[1],context:'28.54|-81.38|America/New_York'};
  const phase=o.offset?.01:c.fraction, unavailable=c.mode==='unavailable',day=c.mode==='daylight';
  assert.ok(s,'missing scene');
  const beam=typeof s.beam==='string'&&s.beam.trim()!==''?Number(s.beam):NaN;
  const altitude=c.group==='motion'?s.geometry?.altitudeDeg:c.alt;
  const inhibited=altitude<=-2||day||unavailable||phase<=.02;
  if(inhibited && (inhibitedLightVerdict(s)==='FAIL'||finite(beam)&&beam!==0)){
    const e=Error('physical light while inhibited');e.andon=true;throw e;
  }
  assert.ok([s.utcMs,s.up,s.sunEl,s.nativeFraction].every(finite),'missing scene numbers');
  assert.equal(Math.floor(s.utcMs/60000),minute,'native clock minute');assert.equal(s.now,c.epoch);
  assert.ok(finite(beam)&&beam>=0,'missing/invalid CSS beam');assert.ok(finite(altitude),'missing true altitude');
  assert.equal(s.consumed?.status,'completed');assert.equal(s.consumed.fresh,true);
  for(const g of [s.geometry,s.consumed.observation]){
    assert.equal(g?.fresh,true);assert.deepEqual(g.produced,identity);assert.deepEqual(g.expected,identity);
    assert.ok(finite(g.altitudeDeg)&&Math.abs(g.altitudeDeg-altitude)<(c.owner?.05:1e-6),'wrong painted altitude');
    assert.equal(g.phaseFraction,s.nativeFraction);
  }
  assert.deepEqual(s.consumed.observation.light,s.light);assert.deepEqual(s.geometry.light,s.light);
  assert.ok(Math.abs(s.up-Math.min(1,Math.max(0,(s.geometry.altitudeDeg+2)/6)))<1e-9,'wrong display ramp');
  assert.ok(Math.abs(s.nativeFraction-phase)<.0005);assert.equal(s.nativeWaxing,c.waxing);
  assert.ok(finite(s.light?.beam)&&Math.abs(s.light.beam-beam)<=.00051,'CSS/physical beam mismatch');
  if(inhibited)assert.equal(inhibitedLightVerdict(s),'PASS');else assert.equal(s.light?.eligible,true);
  assert.ok(day?s.sunEl>=-3:c.epoch.includes('T11:05')?s.sunEl>=-12&&s.sunEl<-6:s.sunEl<-12,'wrong solar regime');
  assert.deepEqual(s.card,[325,530]);assert.equal(s.prayerLoaded,true);assert.equal(s.composed,true);
  assert.equal(s.motionReduced,c.motion==='reduce');
  assert.ok(s.disc&&[s.disc.cx,s.disc.cy,s.disc.r].every(finite)&&s.disc.r>0&&
    s.disc.cx>=0&&s.disc.cx<=325&&s.disc.cy>=0&&s.disc.cy<=530,'off-screen disc');
  assert.ok(s.wx?.currentWeatherSource===(c.group==='motion'?'forecast':'current')+' (Open-Meteo model estimate)','wrong weather source');
  const w=weather[c.weather],v=s.weatherFields;
  assert.equal(s.weatherCode,w.weather_code);assert.equal(v?.code,w.weather_code);assert.equal(v?.cloud,w.cloud_cover);
  assert.equal(v?.vis,w.visibility);assert.equal(v?.rh,w.relative_humidity_2m);
  assert.ok(Number.isInteger(s.weatherFixtureReads)&&s.weatherFixtureReads>=0);
  if(unavailable){assert.equal(s.calendarVisible,false);assert.equal(s.ready,false);assert.equal(s.displayMode,'surface-unavailable');return;}
  if(day){assert.equal(s.displayMode,'day-suppressed');assert.equal(s.calendarVisible,false);return;}
  assert.equal(s.ready,true);assert.equal(s.presentable,true);assert.ok(s.groupOpacity>0&&s.featureOpacity>0&&s.disc?.r>0,'hidden Moon');
  if(o.hidden){assert.equal(s.detail?.visible,true);assert.deepEqual(s.visibility,['hidden','hidden']);}
  else assert.equal(s.visibility?.[s.detail?.visible?1:0],'visible','presented Moon visibility');
  assert.equal(s.source,o.tier==='initial'?'initial-v5':'refined-terrain');assert.equal(s.quality,o.tier==='initial'?'initial-v5':'empirical-adaptive');
  assert.equal(s.profile,o.reference?'unboosted-v5-01':'calendar-neutral-v5-01');
  assert.equal(s.waxing,c.waxing);assert.ok(finite(s.acceptedFraction)&&Math.abs(s.acceptedFraction-phase)<.002,'wrong accepted phase');
  if(altitude<=-2)assert.equal(s.calendarVisible,true);
  if(c.owner&&o.tier==='refined')assertOwnerScene(o.offset?'offset':o.reference?'reference':'b0',s);
  if(c.group==='owner-control'&&!o.offset){assert.equal(s.displayMode,'physical');assert.ok(s.moonlightOpacity>0);}
}
function checkPair(before,after,c,options){
  checkState(before,c,options);checkState(after,c,options);
  for(const k of ['source','quality','profile','acceptedFraction','waxing','up','disc','nativeFraction','geometry','light','weatherFields','beam'])
    assert.deepEqual(after[k],before[k],k+' changed during screenshot');
}
function aperture(m){
  const lit=Number.isFinite(m?.referenceP95)&&m.referenceP95>0&&m.litPixels>0&&m.maskOverlapPixels===0&&finite(m.litMeanY)&&finite(m.physicalLitMeanY);
  return {lit, dark:lit&&m.darkPixels>0&&finite(m.darkMeanY), sky:lit&&finite(m.deltaLitSkyL)};
}
function riseBracket(rows){
  if(!rows.every((r,i)=>finite(r.altitude)&&finite(r.up)&&r.up>=0&&r.up<=1&&Number.isInteger(r.minute)&&(!i||r.minute===rows[i-1].minute+1)))return null;
  const first=rows.findIndex(r=>r.altitude>-2)-1,last=rows.findIndex(r=>r.altitude>=4);
  return first>=0&&last>first&&rows.slice(first,last+1).every((r,i,a)=>!i||r.altitude>=a[i-1].altitude)?[first,last+1]:null;
}
module.exports={makeServer,prayerFixture,clearWeather,facts,readUiMask,checkPair,aperture,riseBracket};
