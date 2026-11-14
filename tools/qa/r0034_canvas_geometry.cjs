'use strict';
// R0034 sky-physics registry (ISM-SKY-037): measure sky canvas backing size versus displayed CSS rect.
// Global Playwright, DPR 1, one engine per run; the tree is served from loopback and every other request is
// aborted (no provider is contacted). Prints one JSON object on stdout.
// Usage: node tools/qa/r0034_canvas_geometry.cjs --root <tree> --engine chromium|firefox|webkit [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root||'.'),engine=a.engine||'chromium';
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream'};
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await PW[engine].launch();
 try{
  const context=await browser.newContext({viewport:{width:420,height:640},deviceScaleFactor:1,timezoneId:'Asia/Riyadh'});
  await context.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
  const page=await context.newPage();
  await page.goto(origin+'/index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30');
  await page.waitForFunction(()=>document.querySelector('.real-sky-preview')&&document.querySelector('.real-sky-canvas'),null,{timeout:30000}).catch(()=>{});
  const result=await page.evaluate(()=>{
   const card=document.querySelector('.c'),cr=card.getBoundingClientRect();
   const one=sel=>{const c=document.querySelector(sel);if(!c)return null;const r=c.getBoundingClientRect(),s=getComputedStyle(c);
    return {backing:[c.width,c.height],rect:[r.width,r.height],ratio:[c.width/r.width,c.height/r.height],imageRendering:s.imageRendering};};
   return {devicePixelRatio,card:{rect:[cr.width,cr.height],clientBox:[card.clientWidth,card.clientHeight],border:getComputedStyle(card).borderTopWidth},
    preview:one('.real-sky-preview'),refined:one('.real-sky-canvas')};
  });
  process.stdout.write(JSON.stringify({engine,version:browser.version(),...result})+'\n');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
