"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const root=path.resolve(process.argv[2]),field=process.argv[3],indexPath=path.join(root,"index.html");
const {mutate}=require(path.join(root,"tests/r0001-browser-fixture.cjs"));
const {nativeInlineRuntime}=require(path.join(root,"tests/native-inline-runtime.cjs"));
const read=fs.readFileSync,original=read(indexPath,"utf8"),changed=mutate(original,field);
const runtime=nativeInlineRuntime(changed);
console.log("MUTANT_INPUT "+JSON.stringify({field,setupAdmitted:true,sourceSha256:crypto.createHash("sha256").update(changed).digest("hex"),runtimeSha256:crypto.createHash("sha256").update(runtime).digest("hex"),productFileWritten:false}));
fs.readFileSync=function(file,options){
  if(typeof file==="string"&&path.resolve(file)===indexPath)return options==="utf8"||options?.encoding==="utf8"?changed:Buffer.from(changed);
  return read.apply(this,arguments);
};
process.argv=[process.execPath,path.join(root,"tests/r0001-date-sinks.cjs"),indexPath,"--baseline"];
require(path.join(root,"tests/r0001-date-sinks.cjs"));
