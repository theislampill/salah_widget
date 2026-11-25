'use strict';
// Entry-point control only: canned geometry, transport and pixel arrays.
const {create}=require('./r0033-fake-playwright.cjs');
const requests=[{url:'https://api.aladhan.com/v1/timings/15-11-2026'},{url:'https://foreign.test/refused'}];
const fake=create({requests});
const encoded=process.env.R003F_ENCODE_PNG==='1';
const real=require('pngjs').PNG;
exports.chromium={launch:async options=>{
  const b=await fake.chromium.launch(options),newContext=b.newContext;
  b.newContext=async options=>{
    const ctx=await newContext(options),newPage=ctx.newPage;
    ctx.newPage=async()=>{
      const q=await newPage(),p={...q};let fraction=.5,name='B0',profile,tier,hidden=false;
      p.clock={setFixedTime:async()=>{}};p.addInitScript=async()=>{};p.close=async()=>{};
      p.goto=async url=>{const u=new URL(url);requests[2]={url,type:'document'};await q.goto(url);fraction=Number(new URLSearchParams(u.hash.slice(1)).get('simMoon'));
        name=u.searchParams.get('variant');
        if(encoded){
          const {renderVariant}=require('../tools/qa/r003f_variants.cjs'),fs=require('node:fs'),root=require('node:path').resolve(__dirname,'..');
          return {body:async()=>Buffer.from(renderVariant(fs.readFileSync(root+'/index.html','utf8'),fs.readFileSync(root+'/moon/src/moon-calendar.mjs','utf8').trimEnd(),name).html)};
        }
      };
      p.waitForFunction=async(_fn,args,opts)=>{tier=args.tier;profile=args.profile;
        if(tier==='refined'&&process.env.R003F_FAKE==='late'){const error=Error('Timeout '+opts.timeout+'ms');error.name='TimeoutError';throw error;}};
      p.waitForTimeout=async()=>{};
      p.locator=()=>({screenshot:async()=>{const v={fraction,name,profile,hidden,tier};return encoded?real.sync.write(canned(v)):Buffer.from(JSON.stringify(v));}});
      p.addStyleTag=async()=>{hidden=true;return {evaluate:async()=>{hidden=false;}};};
      p.evaluate=async fn=>{
        if(fn.name==='facts'){
          const light=Object.fromEntries(['eligibility','illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'].map(k=>[k,0]));
          const state={card:[325,530],disc:{cx:150.5,cy:120.5,r:45},geometry:{altitudeDeg:-20},now:'2026-11-15T09:42:00.000Z',motionReduced:true,ready:true,composed:true,
            quality:tier==='initial'?'initial-v5':'empirical-adaptive',source:tier==='initial'?'initial-v5':'refined-terrain',profile,acceptedFraction:fraction,nativeFraction:fraction,
            waxing:true,nativeWaxing:true,up:0,moonAltitude:-20,moonlightOpacity:0,light:{...light,eligible:false},beam:'0',
            calendarVisible:true,groupOpacity:1,featureOpacity:1,weatherCode:0,weatherFixtureReads:1,prayerLoaded:true};
          const identity={epochMinute:Math.floor(Date.parse(state.now)/60000),minute:282,context:'28.54|-81.38|America/New_York'};
          state.geometry={altitudeDeg:-20,fresh:true,produced:identity,expected:identity,phaseFraction:fraction,light:state.light};
          state.consumed={status:'completed',fresh:true,observation:{...state.geometry}};
          state.wx={currentWeatherSource:'current (Open-Meteo model estimate)'};state.presentable=true;state.visibility=hidden?['hidden','hidden']:['visible','visible'];state.detail={visible:true};
          state.sunEl=-27;state.utcMs=Date.parse(state.now);state.weatherFields={code:0,rh:55,vis:24000,cloud:0};
          if(name==='B1c'&&process.env.R003F_FAKE==='stale')state.consumed.status='failed';
          if(name==='B1c'&&process.env.R003F_FAKE==='wrongup')state.up=.75;
          if(name==='B1c'&&process.env.R003F_FAKE==='emptybeam')state.beam='';
          if(name==='B1c'&&process.env.R003F_FAKE==='weather')state.weatherFields.vis=5000;
          if(name==='B1c'&&process.env.R003F_FAKE==='wrongtier')state.quality='pending';
          if(name==='B1c'&&process.env.R003F_FAKE==='leak')state.light.beam=.001;
          return state;
        }
        if(fn.name==='readUiMask')return {allowed:[],headerRects:[]};
        const body=fn.toString();
        if(body.includes('cloudcanvas'))return {rgba:[44,44,44,0],covered:0};
        if(body.includes('detailAvailable'))return true;
        if(body.includes('Object.fromEntries'))return Object.fromEntries(['.moccluder','.moon-detail-canvas','.buckle','.e','.wt','.h'].map(k=>[k,k==='.moccluder'?{x:105.5,y:75.5,w:90,h:90,filter:'none'}:{x:140,y:15,w:25,h:25,filter:'none'}]));
        if(body.includes('elementsFromPoint'))return [[['g','', 'sky']]];
      };return p;
    };return ctx;
  };return b;
}};
function canned(v){
  const data=Buffer.alloc(325*530*4,255);
  for(let i=0;i<325*530;i++){
    const x=i%325-150,y=Math.floor(i/325)-120;
    let code=25;
    if(Math.hypot(x,y)<45&&!v.hidden){
      code=v.fraction<.02||x<0?10:v.profile==='unboosted-v5-01'?144:v.name==='B0'?60:77;
    }
    if(v.name==='B1c'&&i===1)code++;
    if(process.env.R003F_FAKE==='flat'&&v.profile==='unboosted-v5-01')code=10;
    for(let k=0;k<3;k++)data[4*i+k]=code;
  }
  return {width:325,height:530,data};
}
exports.PNG={sync:{read:raw=>raw[0]===137?real.sync.read(raw):canned(JSON.parse(raw))}};
