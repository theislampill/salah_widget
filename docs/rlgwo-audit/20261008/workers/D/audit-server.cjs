"use strict";
// Read-only loopback server for the primary's serial browser lease. No browser launch.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const root="C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget",audit=__dirname;
const manifestPath="docs/real-sky/evidence/startup-cloud-20261007/final-v49/CANDIDATE_RUNTIME.json";
const manifest=JSON.parse(fs.readFileSync(path.join(root,manifestPath),"utf8"));
if(manifest.treeSha256!=="f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260")throw Error("wrong target inventory");
for(const file of ["index.html","builder.html","config.js"]){const actual=crypto.createHash("sha256").update(fs.readFileSync(path.join(root,file))).digest("hex");if(actual!==manifest.files[file].sha256)throw Error("target bytes changed: "+file);}
const allowed=new Set([...Object.keys(manifest.files),manifestPath]);
const {createFixtureServer}=require(path.join(root,"tests/r001f-stream-server.cjs")),fixture=createFixtureServer();
const streamHandler=fixture.server.listeners("request")[0];fixture.server.removeAllListeners("request");
const csp="default-src 'none'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:; worker-src 'self' blob:; frame-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; font-src 'none'; base-uri 'self'; form-action 'none'";
const types={".html":"text/html; charset=utf-8",".js":"application/javascript; charset=utf-8",".mjs":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8",".css":"text/css; charset=utf-8",".wasm":"application/wasm",".gz":"application/gzip"};
fixture.server.on("request",(req,res)=>{
 const u=new URL(req.url,"http://127.0.0.1");
 if(["/geojs-stall","/geojs-finite","/ipinfo","/failure","/ledger"].includes(u.pathname)){req.url=u.pathname;return streamHandler(req,res);}
 // Production builder computes root/?r=... preview URLs. Keep its src/fragment
 // untouched; HTTP redirect supplies the same production widget inside isolation.
 if((u.pathname==="/"||u.pathname==="/index.html")&&u.searchParams.has("r")&&req.headers["sec-fetch-dest"]==="iframe"){
   res.statusCode=302;res.setHeader("Location","/audit/r0023-current-native.html?page=widget&seed=none&gps=unsupported&detect=success");res.end();return;
 }
 let file;
 if(u.pathname==="/audit/r0023-current-native.html"){file=path.join(audit,"r0023-current-native.html");res.setHeader("Content-Security-Policy",csp);}
 else {let relative;try{relative=decodeURIComponent(u.pathname.slice(1))||"index.html";}catch{res.statusCode=400;res.end();return;}
   if(!allowed.has(relative)){res.statusCode=404;res.end("not admitted");return;}file=path.join(root,relative);
 }
 res.setHeader("Content-Type",types[path.extname(file)]||"application/octet-stream");res.setHeader("Cache-Control","no-store");
 const read=fs.createReadStream(file);read.on("error",()=>{if(!res.headersSent)res.statusCode=404;res.end();});read.pipe(res);
});
fixture.server.listen(Number(process.argv[2]||0),"127.0.0.1",()=>console.log(JSON.stringify({origin:`http://127.0.0.1:${fixture.server.address().port}`,fixture:"/audit/r0023-current-native.html",target:"18ff14860ff41c084b1db5f396bb62aa9c22b1be",nativeStreams:["/geojs-stall","/geojs-finite","/ipinfo","/failure","/ledger"],preview:"current exact production widget in isolated wrapper; modules retained",browser:"NOT_LAUNCHED"})));
process.on("SIGINT",fixture.close);process.on("SIGTERM",fixture.close);
