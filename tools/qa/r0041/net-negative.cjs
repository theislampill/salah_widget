'use strict';
// R0041 (issue 143) row R41-NET negative control: a variant of the isolation that lets ONE host through must make the
// harness fail (iso.cjs finish() throws -> this recipe reports it). Native recipe; NOT part of the node glob.
// Nothing ever leaves the machine: the "let through" host (r0041-letthrough.test) is answered by a LOOPBACK listener
// started here; no forwarding to any other address exists.
// Cases per engine (one browser at a time, headless):
//   control         unmodified isolation; the page fetches the host -> refused; finish() must PASS with 0 allowed
//   route-let-through  a test route registered after iso's catch-all (so it takes precedence) continues the host
//                   instead of aborting it; the proxy then refuses it, and the browser observes a finished foreign
//                   request -> finish() must THROW
//   proxy-let-through  mode 'cache' (no route layer: the proxy and, in Chromium, the resolver rules are the only
//                   layers), and the proxy is patched to hand the host to the loopback listener -> finish() must THROW
//                   (for Firefox this is the case where the proxy alone must catch it)
// Also: no recipe under tools/qa/r0041 calls unroute (grep).
// Usage: node net-negative.cjs <repoRoot> <outJson> [engines=chromium,firefox,webkit]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,enginesArg]=process.argv.slice(2);const ENGINES=(enginesArg||'chromium,firefox,webkit').split(',');
const HOST='r0041-letthrough.test';
async function listener(){const hits=[];const s=http.createServer((q,r)=>{hits.push(q.url);r.writeHead(200,{'content-type':'text/plain','access-control-allow-origin':'*'});r.end('loopback stand-in');});await new Promise(r=>s.listen(0,'127.0.0.1',r));return {server:s,port:s.address().port,hits};}
async function runCase(engine,kase,lst){
  const env=await createEnv({root,extra:{'/net.html':()=>({body:'<!doctype html><meta charset="utf-8"><title>net</title><p>net'})}});
  if(kase==='proxy-let-through'){const orig=env.proxy.server.listeners('request')[0];env.proxy.server.removeAllListeners('request');
    env.proxy.server.on('request',(req,res)=>{let u=null;try{u=new URL(req.url);}catch{}
      if(u&&u.hostname===HOST){env.log.push({layer:'proxy',host:HOST,path:u.pathname,outcome:'LET-THROUGH (test variant, loopback stand-in)',t0:Date.now()});
        const f=http.request({host:'127.0.0.1',port:lst.port,path:u.pathname,method:req.method},r2=>{res.writeHead(r2.statusCode,r2.headers);r2.pipe(res);});f.on('error',()=>{res.writeHead(502);res.end();});req.pipe(f);return;}
      return orig(req,res);});}
  const L=await launch(env,{engine,mode:kase==='proxy-let-through'?'cache':'route',reducedMotion:'reduce'});
  const rec={engine,case:kase};
  try{
    if(kase==='route-let-through')await L.context.route(`http://${HOST}/**`,r=>r.continue());
    const page=await L.context.newPage();await page.goto(env.origins.url('127.0.0.1','/net.html'),{waitUntil:'load'});
    rec.fetch=await page.evaluate(async u=>{try{const r=await fetch(u,{cache:'no-store'});return {status:r.status,body:(await r.text()).slice(0,40)};}catch(e){return {error:String(e).slice(0,80)};}},`http://${HOST}/probe`);
    await page.waitForTimeout(500);
  }catch(e){rec.harnessError=String(e).slice(0,200);}
  await L.close().catch(()=>{});
  try{const s=env.finish();rec.finishThrew=false;rec.allowedExternal=s.allowedExternal;rec.externalAttempts=s.externalAttempts;rec.byLayer=s.externalByLayerHostOutcome;}
  catch(e){rec.finishThrew=true;rec.error=String(e.message).slice(0,300);const s=env.summary?.();if(s){rec.allowedExternal=s.allowedExternal;rec.byLayer=s.externalByLayerHostOutcome;}}
  rec.expected=kase==='control'?'finish passes, 0 allowed':'finish throws';rec.ok=kase==='control'?rec.finishThrew===false&&rec.allowedExternal===0:rec.finishThrew===true;
  return rec;
}
(async()=>{
  const lst=await listener();const out={schema:'r0041-net-negative/1',host:HOST,loopbackListenerOnly:true,cases:[]};
  for(const e of ENGINES)for(const k of ['control','route-let-through','proxy-let-through']){const r=await runCase(e,k,lst);out.cases.push(r);console.log(e,k,'finishThrew',r.finishThrew,'allowed',r.allowedExternal,'ok',r.ok,JSON.stringify(r.fetch||r.harnessError));}
  lst.server.close();out.loopbackListenerHits=lst.hits.length;
  const recipes=fs.readdirSync(__dirname).filter(f=>/\.(cjs|js|sh|py)$/.test(f)&&f!==path.basename(__filename));out.unrouteCalls=recipes.filter(f=>/\bunroute\s*\(/.test(fs.readFileSync(path.join(__dirname,f),'utf8')));
  out.pass=out.cases.every(c=>c.ok)&&out.unrouteCalls.length===0;
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));console.log('PASS',out.pass,'unroute',out.unrouteCalls);process.exit(out.pass?0:1);
})().catch(e=>{console.error(e);process.exit(1);});
