// R002E E-05: run the unchanged tests/smoke.html instrument natively (Chromium, Firefox, WebKit) from a loopback
// server with every non-loopback request route-aborted and logged (the wrapper already synthesizes prayer responses).
// Usage: node tools/qa/r002e_smoke_stubbed.cjs <tree> <playwright package>  -> one JSON line per engine.
const fs=require('fs'),path=require('path'),http=require('http');
const [root,pw]=[path.resolve(process.argv[2]),process.argv[3]];const P=require(pw);
const T={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.wasm':'application/wasm','.bin':'application/octet-stream'};
const srv=http.createServer((q,s)=>{const p=path.normalize(path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname)));if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){s.writeHead(404);return s.end();}s.writeHead(200,{'content-type':T[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(s);});
(async()=>{await new Promise(r=>srv.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+srv.address().port;
for(const eng of ['chromium','firefox','webkit']){const b=await P[eng].launch({headless:true});const c=await b.newContext();const aborted=[];
 await c.route('**/*',r=>{const u=r.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return r.continue();aborted.push(new URL(u).host);return r.abort();});
 const pg=await c.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e.message).slice(0,150)));
 await pg.goto(base+'/tests/smoke.html',{waitUntil:'domcontentloaded'});
 let r=null;try{await pg.waitForFunction('!!window.__smoke',null,{timeout:240000});r=await pg.evaluate('window.__smoke');}catch(e){r={status:'TIMEOUT'};}
 const txt=await pg.locator('#out').innerText();const line=txt.split('\n').filter(l=>/rollover/.test(l));
 console.log(JSON.stringify({engine:eng,version:b.version(),status:r.status,pass:r.pass,fail:r.fail,skip:r.skip,missing:r.missing,pageErrors:errs,abortedHosts:[...new Set(aborted)],rolloverRow:line}));await b.close();}
srv.close();})().catch(e=>{console.error(e);process.exit(1);});
