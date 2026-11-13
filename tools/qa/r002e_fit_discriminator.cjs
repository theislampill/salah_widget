'use strict';
// R002E stage 1 (issue 95 §F.2): native discriminator for PRA-F-23, the countdown-name fit key.
// fitCn() reuses the previous .cn fit (font-size, top, margin-bottom) when currentKey | rounded sunrise |
// rounded sunset | font signature is unchanged, although the rail it fits against also depends on latitude,
// noon and declination. This recipe measures whether that reuse is VISIBLE in reachable transitions.
//
// For each pair it measures the .cn fit after (i) a warm transition into the target state (the cache from the
// source state may be reused) and (ii) a fresh load of the target state, plus a second fresh load (crop noise
// floor). Decision rule (issue): > 0.1 px font-size or > 0.5 px top / margin-bottom, or any pixel difference in
// the .cn crop beyond the fresh-vs-fresh noise -> defect established. A difference found ONLY on the unreachable
// reference pair is "mechanism, not user-visible".
//
// Pairs:
//   day      one site (Madinah), day D -> D+1 near the June solstice with equal rounded sunrise/sunset
//   sites    two real sites 1.2 deg apart on one meridian (Sendai -> Iwaki; Asia/Tokyo) on a date where both
//            rounded sunrise and sunset coincide (Madinah/Makkah never coincide in 2026-2030 with these fixtures)
//   sites-hl two real sites 19.7 deg apart on one meridian (Pisa, Europe/Rome -> Trondheim, Europe/Oslo; both
//            UTC+2 in September) on the date their rounded sunrise and sunset coincide
//   polar    Tromso midnight sun (degenerate provider times), day D -> D+1
//   fonts    fallback -> substitute web faces (local system fonts served under the Inter/Fraunces names)
//   ref      UNREACHABLE reference: the same record at latitude 24.47 -> 55 (a provider never returns it)
//
// Records are FIXTURES computed here from the NOAA general solar position equations (sunrise/noon/sunset; the
// other prayers are ordered placeholders). They are not provider output. Every request is route-stubbed: the
// prayer provider from these fixtures, the webfont stylesheet/faces only in the fonts pair (local files), and
// every other non-local request is aborted. Mocked clock; browser zone America/Los_Angeles; reduced motion.
//
// --inputs (fit-key completeness, R002E item 4): instead of the pairs, load one scene per engine and refit .cn in
// place (key cleared, fitCn(model())) while varying one UNKEYED input at a time — the .nt text ("—", 24 h, 12 h), the
// "now" knot of the rail (clock seeks inside one current period), the appearance (glass/contrast), the .left text and
// the header label — and report the largest deviation from the scene's own fit. Within the issue's bounds (0.1 px
// font-size, 0.5 px top/margin-bottom) the input cannot change the fitted geometry at the measured scenes.
// Usage: node tools/qa/r002e_fit_discriminator.cjs --root <generated tree> --out <fresh dir>
//          [--engines chromium,firefox,webkit] [--playwright <playwright package dir>] [--pairs day,sites,...]
//          [--fonts <regular.ttf>,<display.ttf>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const argv=process.argv.slice(2),args={};
for(let i=0;i<argv.length;i++)if(argv[i].startsWith('--')){const k=argv[i].slice(2),v=[];while(argv[i+1]&&!argv[i+1].startsWith('--'))v.push(argv[++i]);args[k]=v.length>1?v.join(','):v[0];}
if(!args.root||!args.out){console.error('usage: --root <tree> --out <fresh dir>');process.exit(2);}
const {chromium,firefox,webkit}=require(args.playwright||'playwright');
const ENG={chromium,firefox,webkit};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const root=path.resolve(args.root),out=path.resolve(args.out);fs.mkdirSync(out,{recursive:false});
const engines=(args.engines||'chromium,firefox,webkit').split(',');
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const tromso=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-tromso-summer.json'),'utf8')).data;
const [fontA,fontB]=(args.fonts||'C:/Windows/Fonts/segoeui.ttf,C:/Windows/Fonts/georgia.ttf').split(',');
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const pad=n=>String(n).padStart(2,'0');
const hhmm=m=>{m=Math.round(m);m=((m%1440)+1440)%1440;return pad(Math.floor(m/60))+':'+pad(m%60);};
// NOAA general solar position (fractional-year form); minutes after local midnight for a fixed UTC offset.
function solar(lat,lon,y,mo,d,offsetMin){
  const doy=Math.round((Date.UTC(y,mo-1,d)-Date.UTC(y,0,0))/864e5),g=2*Math.PI/365*(doy-1);
  const eq=229.18*(0.000075+0.001868*Math.cos(g)-0.032077*Math.sin(g)-0.014615*Math.cos(2*g)-0.040849*Math.sin(2*g));
  const dec=0.006918-0.399912*Math.cos(g)+0.070257*Math.sin(g)-0.006758*Math.cos(2*g)+0.000907*Math.sin(2*g)-0.002697*Math.cos(3*g)+0.00148*Math.sin(3*g);
  const R=Math.PI/180,phi=lat*R,c=Math.cos(90.833*R)/(Math.cos(phi)*Math.cos(dec))-Math.tan(phi)*Math.tan(dec);
  const ha=Math.acos(Math.max(-1,Math.min(1,c)))/R;
  return {sunrise:720-4*(lon+ha)-eq+offsetMin,noon:720-4*lon-eq+offsetMin,sunset:720-4*(lon-ha)-eq+offsetMin};
}
const day=(y,mo,d)=>`${pad(d)}-${pad(mo)}-${y}`;
function record(site,ds){
  const [d,mo,y]=ds.split('-').map(Number),r=JSON.parse(JSON.stringify(site.polar?tromso:ordinary));
  if(!site.polar){
    const s=solar(site.lat,site.lon,y,mo,d,site.offset);
    r.timings={Fajr:hhmm(s.sunrise-80),Sunrise:hhmm(s.sunrise),Dhuhr:hhmm(s.noon+2),Asr:hhmm(s.noon+200),Sunset:hhmm(s.sunset),Maghrib:hhmm(s.sunset),Isha:hhmm(s.sunset+90)};
  }
  r.meta={...(r.meta||{}),timezone:site.zone};
  r.date.gregorian={...r.date.gregorian,date:ds,day:pad(d),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};
  return r;
}
const SITES={
  madinah:{lat:24.47,lon:39.61,zone:'Asia/Riyadh',offset:180,label:'Madinah'},
  makkah:{lat:21.42,lon:39.83,zone:'Asia/Riyadh',offset:180,label:'Makkah'},
  sendai:{lat:38.27,lon:140.87,zone:'Asia/Tokyo',offset:540,label:'Sendai'},
  iwaki:{lat:37.05,lon:140.89,zone:'Asia/Tokyo',offset:540,label:'Iwaki'},
  trondheim:{lat:63.43,lon:10.4,zone:'Europe/Oslo',offset:120,label:'Trondheim'},
  pisa:{lat:43.72,lon:10.4,zone:'Europe/Rome',offset:120,label:'Pisa'},
  tromso:{lat:69.65,lon:18.96,zone:'Europe/Oslo',offset:120,label:'Tromso',polar:true},
  ref55:{lat:55,lon:39.61,zone:'Asia/Riyadh',offset:180,label:'Ref55',recordOf:'madinah'}
};
const times=(site,ds)=>{const t=record(site.recordOf?SITES[site.recordOf]:site,ds).timings;return t.Sunrise+'|'+t.Sunset;};
function scan(from,days,pred){const t=Date.UTC(...from);for(let i=0;i<days;i++){const x=new Date(t+i*864e5),ds=day(x.getUTCFullYear(),x.getUTCMonth()+1,x.getUTCDate());if(pred(ds,x))return ds;}return null;}
const next=ds=>{const [d,mo,y]=ds.split('-').map(Number),x=new Date(Date.UTC(y,mo-1,d+1));return day(x.getUTCFullYear(),x.getUTCMonth()+1,x.getUTCDate());};
// UTC instant of local 13:00 (after Dhuhr: currentKey "Dhuhr" at every site used) on ds.
const instant=(site,ds)=>{const [d,mo,y]=ds.split('-').map(Number);return Date.UTC(y,mo-1,d,13,0)-site.offset*6e4;};
function pairs(){
  const P={};
  const dD=scan([2026,5,15],14,ds=>times(SITES.madinah,ds)===times(SITES.madinah,next(ds)));
  if(dD)P.day={kind:'day',from:{site:'madinah',day:dD},to:{site:'madinah',day:next(dD)},reachable:true};
  const sD=scan([2026,2,1],60,ds=>times(SITES.sendai,ds)===times(SITES.iwaki,ds));
  if(sD)P.sites={kind:'site',from:{site:'sendai',day:sD},to:{site:'iwaki',day:sD},reachable:true};
  // UTC+2 for both zones is only valid in summer time: scan April-October.
  const hD=scan([2026,3,1],200,ds=>times(SITES.pisa,ds)===times(SITES.trondheim,ds));
  if(hD)P['sites-hl']={kind:'site',from:{site:'pisa',day:hD},to:{site:'trondheim',day:hD},reachable:true};
  P.polar={kind:'day',from:{site:'tromso',day:'21-06-2026'},to:{site:'tromso',day:'22-06-2026'},reachable:true};
  P.fonts={kind:'fonts',from:{site:'madinah',day:'07-09-2026'},to:{site:'madinah',day:'07-09-2026'},reachable:true};
  P.ref={kind:'site',from:{site:'madinah',day:'07-09-2026'},to:{site:'ref55',day:'07-09-2026'},reachable:false};
  return P;
}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2','.jpg':'image/jpeg','.webp':'image/webp'};
function serve(dir){return http.createServer((req,res)=>{
  const u=new URL(req.url,'http://x'),p=path.normalize(path.join(dir,decodeURIComponent(u.pathname)));
  if(!p.startsWith(dir)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);
});}
const hashOf=s=>`#lat=${s.lat}&lon=${s.lon}&label=${s.label}&method=4&seed=1&tz=${encodeURIComponent(s.zone)}`;
const FONT_CSS=`@font-face{font-family:"Inter";font-weight:400 600;src:url(https://fonts.gstatic.com/r002e/a.ttf) format("truetype")}
@font-face{font-family:"Fraunces";font-weight:400 700;src:url(https://fonts.gstatic.com/r002e/b.ttf) format("truetype")}`;
async function open(browser,base,{site,instantMs,fonts=null}){
  const context=await browser.newContext({viewport:{width:325,height:530},timezoneId:'America/Los_Angeles',locale:'en-US',reducedMotion:'reduce'});
  const days=[],held=[];
  await context.route('**/*',async route=>{const u=route.request().url();
    if(u.startsWith(base))return route.continue();
    const m=/api\.aladhan\.com\/v1\/timings\/([^?]*)\?(.*)$/.exec(u);
    if(m&&/^\d{2}-\d{2}-\d{4}$/.test(m[1])){
      const lat=+new URLSearchParams(m[2]).get('latitude'),s=Object.values(SITES).find(x=>x.lat===lat);days.push(m[1]+'@'+lat);
      if(s)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(s.recordOf?{...SITES[s.recordOf]}:s,m[1])})});
      return route.abort();
    }
    if(fonts&&/fonts\.googleapis\.com\/css2/.test(u))return route.fulfill({status:200,contentType:'text/css',body:FONT_CSS});
    if(fonts&&/fonts\.gstatic\.com\/r002e\/(a|b)\.ttf/.test(u)){
      const body=fs.readFileSync(/a\.ttf/.test(u)?fontA:fontB),go=()=>route.fulfill({status:200,contentType:'font/ttf',body,headers:{'access-control-allow-origin':'*'}});
      if(fonts==='held'){held.push(go);return;} return go();
    }
    return route.abort();});
  const page=await context.newPage();const pageErrors=[];page.on('pageerror',e=>pageErrors.push(String(e&&e.message||e).slice(0,200)));
  await page.clock.install({time:new Date(instantMs)});
  await page.goto(base+'/index.html'+hashOf(site),{waitUntil:'domcontentloaded'});
  return {context,page,days,held,pageErrors};
}
async function settle(page,site,ds){
  await page.waitForFunction(([lat,ds])=>{try{return window.eval('lat')===lat&&window.eval('today')?.date?.gregorian?.date===ds&&!!window.eval('model()')&&window.eval('_cnFit')!==''&&window.eval('_loopStarted');}catch(e){return false;}},[site.lat,ds],{timeout:20000});
  await page.waitForTimeout(500);
}
async function freeze(page,ms){await page.evaluate(ms=>window.SalahClock.set({utcMs:ms,rate:0}),ms);await page.waitForTimeout(500);}
const measure=async (page,crop=true)=>({...(await page.evaluate(()=>{const cn=document.querySelector('.cn'),cs=getComputedStyle(cn),rail=document.querySelector('.arc .rail');
  return {text:cn.textContent,fontSize:cn.style.fontSize,top:cn.style.top,marginBottom:cn.style.marginBottom,computed:{fontSize:cs.fontSize,top:cs.top,marginBottom:cs.marginBottom},
    fitKey:window.eval('_cnFit'),railD:rail?rail.getAttribute('d'):null,webfonts:document.documentElement.classList.contains('webfonts'),today:window.eval('today')?.date?.gregorian?.date,lat:window.eval('lat'),timings:window.eval('today')?.timings};})),
  crop:crop?await page.locator('.cn').screenshot():null});
// Minimal PNG decoder (8-bit RGB/RGBA, non-interlaced: what Playwright screenshots produce); no browser involved.
function decodePng(buf){
  const zlib=require('node:zlib');let p=8,w=0,h=0,ct=0,idat=[];
  while(p<buf.length){const len=buf.readUInt32BE(p),type=buf.toString('latin1',p+4,p+8),data=buf.subarray(p+8,p+8+len);
    if(type==='IHDR'){w=data.readUInt32BE(0);h=data.readUInt32BE(4);if(data[8]!==8||data[12]!==0)throw new Error('unsupported PNG');ct=data[9];}
    else if(type==='IDAT')idat.push(data);else if(type==='IEND')break;p+=12+len;}
  const bpp=ct===6?4:ct===2?3:0;if(!bpp)throw new Error('unsupported PNG colour type '+ct);
  const raw=zlib.inflateSync(Buffer.concat(idat)),stride=w*bpp,outb=Buffer.alloc(h*stride);
  for(let y=0;y<h;y++){const f=raw[y*(stride+1)],src=raw.subarray(y*(stride+1)+1,(y+1)*(stride+1)),row=outb.subarray(y*stride,(y+1)*stride),prev=y?outb.subarray((y-1)*stride,y*stride):null;
    for(let x=0;x<stride;x++){const a=x>=bpp?row[x-bpp]:0,b=prev?prev[x]:0,c=(prev&&x>=bpp)?prev[x-bpp]:0;let v=src[x];
      if(f===1)v+=a;else if(f===2)v+=b;else if(f===3)v+=(a+b)>>1;else if(f===4){const pp=a+b-c,pa=Math.abs(pp-a),pb=Math.abs(pp-b),pc=Math.abs(pp-c);v+=(pa<=pb&&pa<=pc)?a:(pb<=pc)?b:c;}
      row[x]=v&255;}}
  return {w,h,bpp,data:outb};
}
function pixelDiff(a,b){
  const A=decodePng(a),B=decodePng(b);if(A.w!==B.w||A.h!==B.h)return {sizeDiffers:true,a:[A.w,A.h],b:[B.w,B.h],bytesEqual:false};
  let n=0,max=0;for(let i=0;i<A.w*A.h;i++){let d=0;for(let k=0;k<Math.min(A.bpp,B.bpp);k++)d=Math.max(d,Math.abs(A.data[i*A.bpp+k]-B.data[i*B.bpp+k]));if(d){n++;max=Math.max(max,d);}}
  return {differingPixels:n,of:A.w*A.h,maxDelta:max,bytesEqual:sha(a)===sha(b)};
}
const px=v=>parseFloat(v)||0;
function verdict(w,f){
  const dFont=Math.abs(px(w.fontSize)-px(f.fontSize)),dTop=Math.abs(px(w.top)-px(f.top)),dMb=Math.abs(px(w.marginBottom)-px(f.marginBottom));
  return {dFont:+dFont.toFixed(3),dTop:+dTop.toFixed(3),dMarginBottom:+dMb.toFixed(3),geometryExceeds:dFont>0.1||dTop>0.5||dMb>0.5};
}
async function inputsMode(){
  const server=serve(root);await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const report={scope:'R002E fit-key completeness: unkeyed-input sensitivity of the in-place .cn fit',root:{'index.html':sha(fs.readFileSync(path.join(root,'index.html')))},engines:{},cells:[]};
  // Seeks stay inside the reference's current period (same currentKey), so only the rail's "now" knot moves.
  const scenes=[['madinah','07-09-2026',[12,30],[[13,30],[14,30],[15,0]]],['trondheim','25-09-2026',[13,30],[[14,0],[14,45],[15,30]]],['madinah','07-09-2026',[20,30],[[21,30],[23,0],[23,50]]]];
  for(const engine of engines){
    const browser=await ENG[engine].launch({headless:true});report.engines[engine]=browser.version();
    for(const [key,ds,[h,mi],seeks] of scenes){
      const site=SITES[key],[d,mo,y]=ds.split('-').map(Number),at=(hh,mm)=>Date.UTC(y,mo-1,d,hh,mm)-site.offset*6e4;
      const c=await open(browser,base,{site,instantMs:at(h,mi)});let row={engine,scene:key+' '+ds+' '+h+':'+mi};
      try{
        await settle(c.page,site,ds);await freeze(c.page,at(h,mi));
        const fit=()=>c.page.evaluate(()=>{_cnFit="";fitCn(model());const s=document.querySelector('.cn').style;return {key:model().currentKey,fontSize:s.fontSize,top:s.top,marginBottom:s.marginBottom};});
        const ref=await fit(),out={};
        const dev=(a)=>({font:Math.abs(px(a.fontSize)-px(ref.fontSize)),top:Math.abs(px(a.top)-px(ref.top)),mb:Math.abs(px(a.marginBottom)-px(ref.marginBottom)),key:a.key});
        const nt0=await c.page.evaluate(()=>document.querySelector('.nt').textContent);
        out.nt=[];for(const t of ['—','15:30','3:30 PM','12:00',nt0]){await c.page.evaluate(t=>{document.querySelector('.nt').textContent=t;},t);out.nt.push({t,...dev(await fit())});}
        const left0=await c.page.evaluate(()=>document.querySelector('.left').innerHTML);
        out.left=[];for(const t of ['Countdown unavailable','Prayer times unavailable']){await c.page.evaluate(t=>{document.querySelector('.left').textContent=t;},t);out.left.push({t,...dev(await fit())});}
        await c.page.evaluate(h=>{document.querySelector('.left').innerHTML=h;},left0);
        out.appearance=[];for(const a of ['contrast','glass']){await c.page.evaluate(a=>{document.querySelector('.c').dataset.appearance=a;},a);out.appearance.push({a,...dev(await fit())});}
        out.label=[];for(const l of ['','A much longer location label']){await c.page.evaluate(l=>{const e=document.querySelector('#loc');e.textContent=l;e.style.display=l?'':'none';},l);out.label.push({l,...dev(await fit())});}
        out.now=[];for(const [sh,sm] of seeks){await freeze(c.page,at(sh,sm));const f=await fit();out.now.push({at:sh+':'+sm,...dev(f)});}
        if(out.now.some(x=>x.key!==ref.key))throw new Error('a clock seek left the reference period');
        const all=[...out.nt,...out.left,...out.appearance,...out.label,...out.now];
        const max={font:Math.max(...all.map(x=>x.font)),top:Math.max(...all.map(x=>x.top)),mb:Math.max(...all.map(x=>x.mb))};
        row={...row,status:'MEASURED',ref,out,max:{font:+max.font.toFixed(3),top:+max.top.toFixed(3),mb:+max.mb.toFixed(3)},exceeds:max.font>0.1||max.top>0.5||max.mb>0.5,pageErrors:c.pageErrors};
      }catch(e){row={...row,status:'ERROR',error:String(e&&e.message||e).slice(0,300)};}
      await c.context.close().catch(()=>{});report.cells.push(row);console.log(JSON.stringify({engine:row.engine,scene:row.scene,status:row.status,max:row.max,exceeds:row.exceeds,error:row.error}));
    }
    await browser.close();
  }
  server.close();
  report.summary={cells:report.cells.length,errors:report.cells.filter(c=>c.status!=='MEASURED').length,exceeding:report.cells.filter(c=>c.exceeds).map(c=>c.engine+':'+c.scene)};
  fs.writeFileSync(path.join(out,'inputs-report.json'),JSON.stringify(report,null,1));console.log(JSON.stringify({summary:report.summary}));
  process.exit(report.summary.errors?3:0);
}
if('inputs' in args){inputsMode().catch(e=>{console.error(e);process.exit(1);});}
else (async()=>{
  const server=serve(root);await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const P=pairs(),want=args.pairs?String(args.pairs).split(','):Object.keys(P);
  const report={scope:'R002E stage 1 (PRA-F-23) native fit discriminator; fixture records (NOAA solar equations), every request route-stubbed, mocked clock',
    root:{'index.html':sha(fs.readFileSync(path.join(root,'index.html')))},engines:{},pairs:Object.fromEntries(want.map(k=>[k,P[k]||'NOT FOUND'])),cells:[]};
  for(const engine of engines){
    const browser=await ENG[engine].launch({headless:true});report.engines[engine]=browser.version();
    for(const name of want){
      const pr=P[name];if(!pr){const row={engine,pair:name,status:'NOT_FOUND'};report.cells.push(row);console.log(JSON.stringify(row));continue;}
      const A=SITES[pr.from.site],B=SITES[pr.to.site],T=instant(B,pr.to.day);let row={engine,pair:name,reachable:pr.reachable,from:pr.from,to:pr.to,
        keyTimes:{from:times(A,pr.from.day),to:times(B,pr.to.day)}};
      try{
        // (i) warm transition
        const w=await open(browser,base,{site:A,instantMs:instant(A,pr.from.day),fonts:pr.kind==='fonts'?'held':null});
        await settle(w.page,A,pr.from.day);const source=await measure(w.page,pr.kind!=='fonts');
        if(pr.kind==='day')await freeze(w.page,T);
        else if(pr.kind==='site'){await w.page.evaluate(([lat,lon,label,zone])=>applyConfig({...CONFIG,lat,lon,label,tz:zone},{save:false}),[B.lat,B.lon,B.label,B.zone]);}
        else if(pr.kind==='fonts'){for(const go of w.held.splice(0))await go();await w.page.waitForFunction(()=>document.documentElement.classList.contains('webfonts'),null,{timeout:10000});}
        await settle(w.page,B,pr.to.day);await freeze(w.page,T);
        if(pr.kind==='fonts')await w.page.waitForFunction(()=>document.documentElement.classList.contains('webfonts'),null,{timeout:10000});
        const warm=await measure(w.page);row.warmPageErrors=w.pageErrors;row.warmRequests=w.days;await w.context.close().catch(()=>{});
        // (ii) fresh load of the target state, twice (noise floor)
        const fresh=[];
        for(const k of [1,2]){const f=await open(browser,base,{site:B,instantMs:T,fonts:pr.kind==='fonts'?'immediate':null});await settle(f.page,B,pr.to.day);
          if(pr.kind==='fonts')await f.page.waitForFunction(()=>document.documentElement.classList.contains('webfonts'),null,{timeout:10000});
          await freeze(f.page,T);if(pr.kind==='fonts')await f.page.waitForTimeout(300);fresh.push(await measure(f.page));await f.context.close().catch(()=>{});}
        for(const [k,v] of Object.entries({source,warm,fresh1:fresh[0],fresh2:fresh[1]}))if(v.crop)fs.writeFileSync(path.join(out,`${engine}-${name}-${k}.png`),v.crop);
        const strip=m=>{const {crop,railD,...rest}=m;return {...rest,railDSha:railD?sha(railD).slice(0,16):null};};
        const cropWarm=pixelDiff(warm.crop,fresh[0].crop),cropNoise=pixelDiff(fresh[0].crop,fresh[1].crop);
        const g=verdict(warm,fresh[0]);
        const cropExceeds=!cropWarm.bytesEqual&&!(cropWarm.differingPixels<=((cropNoise.differingPixels)||0)&&cropNoise.differingPixels>0);
        row={...row,source:strip(source),warm:strip(warm),fresh:strip(fresh[0]),fresh2:strip(fresh[1]),railEqualWarmFresh:warm.railD===fresh[0].railD,
          railChangedSourceToTarget:source.railD!==fresh[0].railD,fitKeyEqualSourceTarget:source.fitKey===fresh[0].fitKey,
          geometry:g,cropWarmVsFresh:cropWarm,cropFreshVsFresh:cropNoise,
          defect:pr.reachable?(g.geometryExceeds||cropExceeds):false,mechanismOnly:!pr.reachable&&(g.geometryExceeds||cropExceeds),status:'MEASURED'};
      }catch(e){row={...row,status:'ERROR',error:String(e&&e.message||e).slice(0,300)};}
      report.cells.push(row);console.log(JSON.stringify(row));
    }
    await browser.close();
  }
  server.close();
  const measured=report.cells.filter(c=>c.status==='MEASURED');
  report.summary={cells:report.cells.length,measured:measured.length,errors:report.cells.filter(c=>c.status==='ERROR').length,
    reachableDefects:measured.filter(c=>c.defect).map(c=>c.engine+':'+c.pair),mechanismOnly:measured.filter(c=>c.mechanismOnly).map(c=>c.engine+':'+c.pair),
    decision:measured.some(c=>c.defect)?'DEFECT ESTABLISHED':measured.length===report.cells.length?'NO DEFECT ESTABLISHED':'INCOMPLETE'};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,1));
  console.log(JSON.stringify({summary:report.summary}));
  process.exit(report.summary.decision==='INCOMPLETE'?3:0);
})().catch(e=>{console.error(e);process.exit(1);});
