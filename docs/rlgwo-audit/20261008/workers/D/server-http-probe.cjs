"use strict";
// Read-only loopback/native Node transport probe. This does not launch a browser.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto"),{spawn}=require("node:child_process");
const child=spawn(process.execPath,[path.join(__dirname,"audit-server.cjs"),"0"],{stdio:["ignore","pipe","pipe"],windowsHide:true});
const errors=[];child.stderr.on("data",data=>errors.push(String(data)));
let buffer="";
const announcement=new Promise((resolve,reject)=>{child.stdout.on("data",data=>{buffer+=data;if(buffer.includes("\n"))resolve(JSON.parse(buffer.split("\n")[0]));});child.once("error",reject);child.once("exit",code=>{if(!buffer)reject(Error("server exited "+code));});});
const receipt={scope:"read-only loopback HTTP/Node transport; browser NOT_RUN",checks:[],errors};
async function test(name,body){await body();receipt.checks.push({name,passed:true});}
(async()=>{try{const server=await announcement,origin=server.origin;receipt.server=server;
 await test("source byte pins and exact audit fixture served",async()=>{for(const [file,expected] of [["index.html","ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee"],["builder.html","66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e"],["config.js","91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81"]]){const res=await fetch(origin+"/"+file);assert.equal(res.status,200);assert.equal(crypto.createHash("sha256").update(Buffer.from(await res.arrayBuffer())).digest("hex"),expected);}
 const res=await fetch(origin+"/audit/r0023-current-native.html");assert.equal(res.status,200);assert.equal(await res.text(),fs.readFileSync(path.join(__dirname,"r0023-current-native.html"),"utf8"));assert.match(res.headers.get("content-security-policy"),/worker-src 'self' blob:/);});
 await test("arbitrary paths denied and iframe redirect bounded",async()=>{assert.equal((await fetch(origin+"/tests/r0023-native.html")).status,404);const redirect=await fetch(origin+"/?r=123",{redirect:"manual",headers:{"Sec-Fetch-Dest":"iframe"}});assert.equal(redirect.status,302);assert.equal(redirect.headers.get("location"),"/audit/r0023-current-native.html?page=widget&seed=none&gps=unsupported&detect=success");});
 await test("finite native stream parses healthy bytes",async()=>{const res=await fetch(origin+"/geojs-finite"),value=await res.json();assert.equal(value.latitude,"24.47");assert.equal(value.longitude,"39.61");});
 await test("headers plus stalled native body responds to actual abort",async()=>{const controller=new AbortController(),res=await fetch(origin+"/geojs-stall",{signal:controller.signal});assert.equal(res.status,200);const body=res.json();setTimeout(()=>controller.abort(),50);await assert.rejects(body);assert.equal(controller.signal.aborted,true);await new Promise(resolve=>setTimeout(resolve,30));const ledger=await (await fetch(origin+"/ledger")).json();const row=ledger.find(x=>x.path==="/geojs-stall");assert.ok(row.closedAt);assert.equal(row.completed,false);receipt.streamRow=row;});
 assert.deepEqual(errors,[]);receipt.status="PASS_NODE_ONLY";
 }catch(error){receipt.status="FAIL";receipt.error=error.stack;process.exitCode=1;}finally{child.kill();fs.writeFileSync(path.join(__dirname,"server-http-probe.json"),JSON.stringify(receipt,null,2)+"\n");console.log(JSON.stringify(receipt));}})();
