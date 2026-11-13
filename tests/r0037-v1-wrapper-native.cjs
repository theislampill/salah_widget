"use strict";
// R0037 row R37-13: the frozen V1 card renders fully in the canonical 325×530 wrapper, and its card region is
// pixel-identical to the historical 330×534 wrapper (only the removed 5×4 px margin differs).
//
// Usage: node tests/r0037-v1-wrapper-native.cjs <fresh-output-dir> <directory containing the playwright package>
// Effect boundary: serves a disposable copy of v1/ from 127.0.0.1; the browser clock, timezone, locale, viewport
// and reduced motion are fixed; prayer/weather/radar responses are fixtures (the same as tests/v1_browser.py);
// font requests are aborted (both captures use the same fallback fonts); every other non-local request is
// aborted and fails the run. No provider, geolocation or real network is contacted. Nothing in the repository is
// written.
const fs=require("node:fs"),path=require("node:path"),http=require("node:http"),os=require("node:os"),crypto=require("node:crypto");
if(process.argv.length!==4)throw Error("Expected <fresh-output-dir> <playwright package parent directory>");
const out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:false});
const {chromium}=require(path.join(path.resolve(process.argv[3]),"playwright"));
const REPO=path.resolve(__dirname,"..");
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const SETTINGS={v:1,lat:24.47,lon:39.61,tz:"Asia/Riyadh",label:"Madinah",method:"4",school:"0",time:"24",datefmt:"YYYY-MM-DD",units:"c",lp:0,seed:1,source:"manual",savedAt:1791345600000};
const V1_KEY="salah_widget:v1:config:v1";
const WRAPPERS={historical:[330,534],canonical:[325,530]};
function fixture(u){
  const url=new URL(u),host=url.hostname;
  if(host==="api.aladhan.com"){
    const day=+url.pathname.replace(/\/$/,"").split("/").pop().split("-")[0];
    return {code:200,data:{timings:{Fajr:"05:00",Sunrise:"06:15",Dhuhr:"12:15",Asr:"15:40",Maghrib:"18:15",Sunset:"18:15",Isha:"19:45"},meta:{timezone:"Asia/Riyadh"},
      date:{gregorian:{day:String(day),month:{number:10,en:"October"},year:"2026"},hijri:{day:String(day+17),month:{number:4,en:"Rabi al-Thani"},year:"1448"}}}};
  }
  if(host==="api.open-meteo.com")return {elevation:620,current:{weather_code:2,temperature_2m:28,apparent_temperature:28,relative_humidity_2m:45,dew_point_2m:14,wind_speed_10m:2,wind_direction_10m:45,wind_gusts_10m:3,cloud_cover:30,cloud_cover_low:5,cloud_cover_mid:20,cloud_cover_high:15,precipitation:0,rain:0,showers:0,snowfall:0,visibility:30000,is_day:1}};
  if(host==="api.rainviewer.com")return {host:"https://tilecache.rainviewer.com",radar:{past:[]}};
  return null;
}
(async()=>{
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),"salah-r0037-native-"));
  const result={row:"R37-13",complete:false,clock:"2026-10-07T09:30:00Z",timezone:"Asia/Riyadh",viewport:[390,600],reducedMotion:"reduce",
    fonts:"aborted for both captures (fallback fonts); not a font-fidelity check",fixtures:"controlled provider fixtures; not live evidence",
    v1Sha256:Object.fromEntries(["index.html","config.js"].map(n=>[n,sha(fs.readFileSync(path.join(REPO,"v1",n)))])),captures:{}};
  let browser=null,server=null;
  try{
    fs.mkdirSync(path.join(tmp,"salah_widget"));fs.cpSync(path.join(REPO,"v1"),path.join(tmp,"salah_widget","v1"),{recursive:true});
    for(const [name,[w,h]] of Object.entries(WRAPPERS))
      fs.writeFileSync(path.join(tmp,name+".html"),'<!doctype html><html><head><meta charset="utf-8"><title>R37-13</title></head><body style="margin:0;background:#fff">\n<iframe\n  title="Prayer Times"\n  referrerpolicy="no-referrer"\n  allow="geolocation"\n  src="/salah_widget/v1/#local=1"\n  style="width:'+w+'px;height:'+h+'px;border:0;border-radius:28px;overflow:hidden"\n  scrolling="no">\n</iframe>\n</body></html>\n');
    const types={".html":"text/html",".js":"application/javascript",".json":"application/json"};
    server=http.createServer((req,res)=>{const p=path.join(tmp,decodeURIComponent(new URL(req.url,"http://x").pathname));
      if(!p.startsWith(tmp)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){const idx=path.join(p,"index.html");if(fs.existsSync(idx)){res.writeHead(200,{"content-type":"text/html"});return res.end(fs.readFileSync(idx));}res.writeHead(404);return res.end();}
      res.writeHead(200,{"content-type":types[path.extname(p)]||"application/octet-stream"});res.end(fs.readFileSync(p));});
    await new Promise(r=>server.listen(0,"127.0.0.1",r));
    const origin="http://127.0.0.1:"+server.address().port;
    browser=await chromium.launch({headless:true});result.browser="chromium "+browser.version();result.node=process.version;
    for(const name of Object.keys(WRAPPERS)){
      const context=await browser.newContext({viewport:{width:390,height:600},deviceScaleFactor:1,timezoneId:"Asia/Riyadh",locale:"en-US",reducedMotion:"reduce",colorScheme:"light"});
      await context.addInitScript(`if(location.protocol==="http:"&&!localStorage.getItem(${JSON.stringify(V1_KEY)}))localStorage.setItem(${JSON.stringify(V1_KEY)},${JSON.stringify(JSON.stringify(SETTINGS))});`);
      const requests=[],unplanned=[],errors=[],aborted=[];
      await context.route("**/*",route=>{const u=route.request().url();requests.push(u);
        if(u.startsWith(origin+"/"))return route.continue();
        const host=new URL(u).hostname;
        if(host==="fonts.googleapis.com"||host==="fonts.gstatic.com"){aborted.push(u);return route.abort();}
        const body=fixture(u);if(body)return route.fulfill({json:body,headers:{"Access-Control-Allow-Origin":"*"}});
        unplanned.push(u);return route.abort();});
      const page=await context.newPage();page.on("pageerror",e=>errors.push(String(e)));
      const instant=new Date("2026-10-07T09:30:00Z");await page.clock.install({time:instant});await page.clock.pauseAt(instant);
      await page.goto(origin+"/"+name+".html",{waitUntil:"load"});
      const frame=page.frames()[1];
      await frame.waitForFunction("typeof qaState==='function'&&qaState().cache.prayerLoaded&&qaState().cache.tomorrowLoaded",null,{polling:100,timeout:20000});
      await page.clock.runFor(3500);
      const rows=await frame.locator(".times .p b").allTextContents();
      const geometry=await frame.evaluate(()=>{const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right}};
        return {innerWidth,innerHeight,card:box(".c"),footer:box(".d"),scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight};});
      const png=await page.locator("iframe").screenshot({animations:"disabled"});
      fs.writeFileSync(path.join(out,name+".png"),png);
      result.captures[name]={wrapper:WRAPPERS[name],png:name+".png",sha256:sha(png),rows,geometry,pageErrors:errors,unplannedRequests:unplanned,abortedFontRequests:aborted.length,
        localRequests:requests.filter(u=>u.startsWith(origin)).map(u=>u.slice(origin.length))};
      await context.close();
    }
    // Compare the 325×530 card region of both captures, pixel by pixel, in a blank page (no network).
    const cmp=await browser.newContext();const p=await cmp.newPage();
    await cmp.route("**/*",r=>r.abort());
    result.comparison=await p.evaluate(async([a,b])=>{
      const load=src=>new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=src;});
      const [ia,ib]=await Promise.all([load(a),load(b)]);
      const data=im=>{const c=document.createElement("canvas");c.width=im.width;c.height=im.height;const x=c.getContext("2d");x.drawImage(im,0,0);return {w:im.width,h:im.height,d:x.getImageData(0,0,325,530).data};};
      const A=data(ia),B=data(ib);let changed=0,max=0,x0=1e9,y0=1e9,x1=-1,y1=-1;
      for(let i=0;i<A.d.length;i+=4){let m=0;for(let k=0;k<4;k++)m=Math.max(m,Math.abs(A.d[i+k]-B.d[i+k]));if(m){changed++;max=Math.max(max,m);const px=(i/4)%325,py=Math.floor(i/4/325);x0=Math.min(x0,px);y0=Math.min(y0,py);x1=Math.max(x1,px);y1=Math.max(y1,py);}}
      return {region:"x 0-324, y 0-529 of each iframe capture",historicalSize:[A.w,A.h],canonicalSize:[B.w,B.h],changedPixels:changed,totalPixels:325*530,maxChannelDelta:max,diffBox:changed?[x0,y0,x1,y1]:null,pixelExact:changed===0};
    },["data:image/png;base64,"+fs.readFileSync(path.join(out,"historical.png")).toString("base64"),"data:image/png;base64,"+fs.readFileSync(path.join(out,"canonical.png")).toString("base64")]);
    await cmp.close();
    const c=result.captures.canonical,g=c.geometry;
    result.checks={
      canonicalCard325x530:g.card.width===325&&g.card.height===530&&g.card.x===0&&g.card.y===0,
      canonicalFooterInside:g.footer.bottom<=530,
      canonicalNoScroll:g.scrollWidth<=g.innerWidth&&g.scrollHeight<=g.innerHeight,
      canonicalViewport325x530:g.innerWidth===325&&g.innerHeight===530,
      prayerRows:JSON.stringify(c.rows)===JSON.stringify(["Fajr","Sunrise","Dhuhr","Asr","Maghrib","Isha"]),
      noPageErrors:Object.values(result.captures).every(x=>x.pageErrors.length===0),
      noUnplannedRequests:Object.values(result.captures).every(x=>x.unplannedRequests.length===0),
      cardRegionPixelExact:result.comparison.pixelExact};
    result.complete=Object.values(result.checks).every(Boolean);
    if(!result.complete)process.exitCode=1;
  }catch(e){result.error=String(e&&e.stack||e);process.exitCode=1;}
  finally{
    if(browser)await browser.close();if(server)server.close();fs.rmSync(tmp,{recursive:true,force:true});
    fs.writeFileSync(path.join(out,"result.json"),JSON.stringify(result,null,2)+"\n");
    console.log(JSON.stringify({complete:result.complete,checks:result.checks,comparison:result.comparison,browser:result.browser,error:result.error}));
  }
})();
