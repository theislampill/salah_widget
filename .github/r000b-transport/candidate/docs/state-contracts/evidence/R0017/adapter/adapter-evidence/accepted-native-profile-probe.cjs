"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),crypto=require("node:crypto"),assert=require("node:assert/strict"),{execFileSync}=require("node:child_process");
const root=path.resolve(process.argv[2]),ref="18ff14860ff41c084b1db5f396bb62aa9c22b1be:index.html";
const bytes=execFileSync("git",["show",ref],{cwd:root,maxBuffer:4*1024*1024});
const sourceSha256=crypto.createHash("sha256").update(bytes).digest("hex");
assert.equal(sourceSha256,"ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee");
const source=bytes.toString("utf8"),{nativeInlineRuntime}=require(path.join(root,"tests/native-inline-runtime.cjs"));
try{
 const runtime=nativeInlineRuntime(source),owners=[...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(s=>!s[1].trim()&&s[2].includes("async function boot(){"));
 assert.equal(owners.length,1);assert.equal(runtime,owners[0][2]);new vm.Script(runtime);
 console.log(JSON.stringify({ref,sourceSha256,status:"ADMITTED_AND_COMPILED",productExecution:false,runtimeSha256:crypto.createHash("sha256").update(runtime).digest("hex")}));
}catch(error){console.log(JSON.stringify({ref,sourceSha256,status:error.code??"FAIL",error:error.message,productExecution:false}));process.exitCode=1;}
