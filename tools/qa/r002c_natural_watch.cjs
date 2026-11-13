'use strict';
// R002C R2C-15 natural-trigger watch: the candidate tree, NO injection, real time (no mocked clock), served on
// 127.0.0.1. The prayer provider is route-stubbed (tests/r0002-ordinary.json re-dated to each requested day,
// zone Asia/Riyadh); every other non-local request is aborted, so weather/radar/fonts/geocoding are unavailable
// (real providers are never contacted). One page per engine, all engines concurrently, for --minutes (default
// 30). Every 30 s: qaState().renderFaults, the render receipt, Moon runtime status. All pageerror events and
// console errors are recorded. A non-empty renderFaults is a naturally fired contained stage.
// Usage: node tools/qa/r002c_natural_watch.cjs --root <tree> --out <fresh dir> [--minutes 30]
//        [--engines chromium,firefox,webkit] [--hash <extra fragment>] [--playwright <package>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const argv=process.argv.slice(2),args={};
for(let i=0;i<argv.length;i++)if(argv[i].startsWith('--')){const k=argv[i].slice(2),v=[];while(argv[i+1]&&!argv[i+1].startsWith('--'))v.push(argv[++i]);args[k]=v.length>1?v:v[0];}
const PW=require(args.playwright||'playwright');
const root=path.resolve(args.root),out=path.resolve(args.out);fs.mkdirSync(out,{recursive:false});
const minutes=+(args.minutes||30),engines=(args.engines||'chromium,firefox,webkit').split(',');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='Asia/Riyadh';
  r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2','.jpg':'image/jpeg','.webp':'image/webp'};
const server=http.createServer((req,res)=>{const p=path.normalize(path.join(root,decodeURIComponent(new URL(req.url,'http://x').pathname)));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const HASH='#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh'+(args.hash||'');
async function watch(engine,base){
  const browser=await PW[engine].launch({headless:true}),context=await browser.newContext({viewport:{width:325,height:530},timezoneId:'Asia/Riyadh',locale:'en-US'});
  const requests={prayer:0,aborted:0};
  await context.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base))return route.continue();
    const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
    if(m){requests.prayer++;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});}
    requests.aborted++;return route.abort();});
  const page=await context.newPage(),pageErrors=[],consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push({at:Date.now(),message:String(e&&e.message||e).slice(0,300)}));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push({at:Date.now(),text:m.text().slice(0,300)});});
  const t0=Date.now();await page.goto(base+'/index.html'+HASH,{waitUntil:'domcontentloaded'});
  const samples=[];
  while(Date.now()-t0<minutes*60000){
    await page.waitForTimeout(30000);
    samples.push(await page.evaluate(()=>{let q=null;try{const s=window.qaState();q={faults:s.renderFaults,render:s.render?{atMs:s.render.atMs,leftMin:s.render.leftMin,currentKey:s.render.currentKey,nextKey:s.render.nextKey,fx:s.render.fx}:null};}catch(e){q={error:String(e.message)};}
      let moon=null;try{const s=window.SalahMoonRuntime?.state;moon=s?{status:s.status,visibleSource:s.visibleSource}:null;}catch(e){}
      return {t:Date.now(),left:document.querySelector('.left')?.textContent??null,...q,moon};}));
  }
  const shot=await page.locator('.c').screenshot();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,engine+'-final.png'),shot);
  const version=browser.version();await browser.close();
  const faultNames=[...new Set(samples.flatMap(s=>s.faults?Object.keys(s.faults):[]))];
  const atMs=samples.map(s=>s.render&&s.render.atMs);
  return {engine,version,minutes,samples:samples.length,requests,pageErrors,consoleErrors,naturalFaults:faultNames,finalFaults:samples.at(-1)?.faults??null,
    receiptAdvancedEverySample:atMs.every((v,i)=>i===0||(v!=null&&v>atMs[i-1])),finalScreenshotSha256:sha(shot),trace:samples};
}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const results=await Promise.all(engines.map(e=>watch(e,base)));
  const report={scope:'R002C R2C-15 natural watch: no injection; real time; prayer stubbed; all other non-local requests aborted',hash:HASH,
    inputs:Object.fromEntries(['index.html','config.js'].map(f=>[f,sha(fs.readFileSync(path.join(root,f)))])),results};
  fs.writeFileSync(path.join(out,'watch.json'),JSON.stringify(report,null,1)+'\n');
  console.log(JSON.stringify(results.map(r=>({engine:r.engine,version:r.version,samples:r.samples,pageErrors:r.pageErrors.length,consoleErrors:r.consoleErrors.length,naturalFaults:r.naturalFaults,receiptAdvancedEverySample:r.receiptAdvancedEverySample,requests:r.requests}))));
  server.close();})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
