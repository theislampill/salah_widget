'use strict';
// R0033 remaining-row native recipes (issue 100): the ONE way those recipes start a browser.
// Rule implemented (execution brief, "Network isolation in every native harness"):
//   - Node side: tools/qa/v1_net_guard.cjs is installed before anything else (non-loopback connect/DNS/http(s)/
//     fetch/WebSocket refused and logged; proxy variables removed).
//   - Browser side: every engine is launched behind a REFUSING loopback proxy (anything that is not loopback and
//     somehow passed the route is refused there, before any outbound connection, and logged); Chromium also gets a
//     resolver rule that resolves nothing but 127.0.0.1 and has background networking switched off.
//   - Every context gets the catch-all route `**/*` and a catch-all WebSocket route BEFORE any page exists. Neither
//     is ever removed or narrowed: neither this module nor a recipe that uses it calls unroute/unrouteAll (checked
//     statically by tests/r0033-isolation.test.cjs). The route exists before the context can produce a page.
//   - classify() is the whole policy: only the loopback fixture origin, data:/blob:/about: and (file-entry cells
//     only) file: URLs inside the served tree continue; a provider URL is fulfilled from a caller-supplied fixture;
//     everything else is aborted. Every request is logged with its disposition.
//   - verdict() fails on ANY escape: a non-loopback request that was continued, a request that finished without
//     passing the route, a response whose server address is not loopback, a proxy hit, or a Node-side refusal.
// classify() and verdict() are pure and are unit-tested without a browser (tests/r0033-isolation.test.cjs).
const path=require('node:path'),http=require('node:http'),{fileURLToPath}=require('node:url');
const guard=require('./v1_net_guard.cjs');
const isLoopbackHost=h=>h!=null&&h!==''&&guard.isLoopback(String(h));   // 127/8, ::1, localhost (the R0036 guard's rule)

// policy = {origin, fileRoot?, fixture?(URL)->body|null}. Returns {action:'continue'|'fulfill'|'abort', why, host, body?}.
function classify(raw,policy){
  let u;try{u=new URL(raw);}catch{return {action:'abort',why:'unparseable',host:null};}
  const scheme=u.protocol,host=u.hostname;
  if(scheme==='data:'||scheme==='blob:'||scheme==='about:')return {action:'continue',why:'local-scheme',host:null};
  if(scheme==='file:'){
    if(!policy.fileRoot||host!=='')return {action:'abort',why:host!==''?'file-remote-host':'file-not-admitted',host:host||null};
    let p;try{p=path.resolve(fileURLToPath(u));}catch{return {action:'abort',why:'file-unparseable',host:null};}
    const root=path.resolve(policy.fileRoot),inside=p===root||p.startsWith(root+path.sep);
    return inside?{action:'continue',why:'file-entry',host:null}:{action:'abort',why:'file-outside-root',host:null};
  }
  if(scheme==='http:'||scheme==='https:'){
    if(policy.origin&&u.origin===policy.origin&&isLoopbackHost(host))return {action:'continue',why:'fixture-origin',host};
    const body=policy.fixture?policy.fixture(u):null;
    if(body!=null)return {action:'fulfill',why:'provider-fixture',host,body};
    return {action:'abort',why:isLoopbackHost(host)?'loopback-not-fixture-origin':'non-loopback',host};
  }
  return {action:'abort',why:'scheme',host:host||null};
}
function newLedger(){return {requests:[],continued:0,fulfilled:0,aborted:0,offLoopbackContinued:[],bypassed:[],offLoopbackResponses:[],websockets:[],proxyRefused:[]};}
// Pure: the ledger (plus Node-side refusals) decides. ok is false on any escape.
function verdict(ledger,nodeRefused=[]){
  const escapes=[...ledger.offLoopbackContinued.map(x=>({...x,kind:'continued-off-loopback'})),...ledger.bypassed.map(x=>({...x,kind:'bypassed-route'})),
    ...ledger.offLoopbackResponses.map(x=>({...x,kind:'response-off-loopback'})),...ledger.proxyRefused.map(x=>({...x,kind:'reached-proxy'})),
    ...nodeRefused.map(x=>({...x,kind:'node-refused',refusal:x.kind}))];
  return {ok:escapes.length===0,escapes,seen:ledger.requests.length,continued:ledger.continued,fulfilled:ledger.fulfilled,aborted:ledger.aborted,
    abortedHosts:[...new Set(ledger.requests.filter(r=>r.action==='abort'&&r.host).map(r=>r.host))],websockets:ledger.websockets.length};
}
const strip=raw=>{try{const u=new URL(raw);return u.protocol==='data:'?'data:':u.protocol==='blob:'?'blob:':u.protocol+'//'+u.host+u.pathname;}catch{return String(raw).slice(0,80);}};

// Launch behind the refusing proxy. Returns {browser, ledger, context(options, policy), close()}.
async function launch(PW,engine,{headless=true}={}){
  guard.install();
  const ledger=newLedger();
  const proxy=http.createServer((req,res)=>{ledger.proxyRefused.push({target:strip(req.url),at:Date.now()});res.writeHead(403);res.end('r0033 isolation');});
  proxy.on('connect',(req,sock)=>{ledger.proxyRefused.push({target:String(req.url),at:Date.now()});sock.end('HTTP/1.1 403 Forbidden\r\n\r\n');});
  proxy.on('upgrade',(req,sock)=>{ledger.proxyRefused.push({target:String(req.url),at:Date.now()});sock.destroy();});
  await new Promise(r=>proxy.listen(0,'127.0.0.1',r));
  const args=engine==='chromium'?['--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1','--disable-background-networking','--disable-component-update','--disable-domain-reliability','--no-pings','--disable-sync']:[];
  const browser=await PW[engine].launch({headless,args,proxy:{server:'http://127.0.0.1:'+proxy.address().port,bypass:'127.0.0.1,localhost'}});
  async function context(options,policy){
    if(policy.origin&&!isLoopbackHost(new URL(policy.origin).hostname))throw new Error('r0033 isolation: fixture origin must be loopback');
    const ctx=await browser.newContext({...options,serviceWorkers:'block'}),routed=new WeakSet();
    await ctx.route('**/*',route=>{
      const request=route.request(),raw=request.url(),c=classify(raw,policy);routed.add(request);
      ledger.requests.push({n:ledger.requests.length,action:c.action,why:c.why,host:c.host,url:strip(raw),type:request.resourceType()});
      if(c.action==='continue'){ledger.continued++;if(c.host&&!isLoopbackHost(c.host))ledger.offLoopbackContinued.push({url:strip(raw)});return route.continue();}
      if(c.action==='fulfill'){ledger.fulfilled++;return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:typeof c.body==='string'?c.body:JSON.stringify(c.body)});}
      ledger.aborted++;return route.abort();
    });
    if(typeof ctx.routeWebSocket==='function')await ctx.routeWebSocket(/.*/,ws=>{ledger.websockets.push({url:strip(ws.url())});ws.close();});
    const settled=request=>{const raw=request.url();if(!routed.has(request)&&!/^(data|blob|about):/.test(raw))ledger.bypassed.push({url:strip(raw)});};
    ctx.on('requestfinished',settled);ctx.on('requestfailed',settled);
    ctx.on('response',response=>{response.serverAddr().then(a=>{if(a&&a.ipAddress&&!isLoopbackHost(a.ipAddress))ledger.offLoopbackResponses.push({url:strip(response.url()),ip:a.ipAddress});}).catch(()=>{});});
    return {context:ctx,newPage:()=>ctx.newPage()};   // the route above exists before any page can
  }
  return {browser,ledger,context,verdict:()=>verdict(ledger,guard.state.refused),close:async()=>{await browser.close();await new Promise(r=>proxy.close(r));}};
}
module.exports={classify,verdict,newLedger,isLoopbackHost,launch};
