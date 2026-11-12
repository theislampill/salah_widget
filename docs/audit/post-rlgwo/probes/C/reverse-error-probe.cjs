"use strict";
// Effect-free: builder VM fixture. A reverse-geocode reply without continentCode (e.g. a provider error JSON)
// is adopted as "not North America" and rewrites the auto method.
const path=require("node:path");
const {fixture}=require(path.join(process.argv[2],"tests","r000f-fixture.cjs"));
(async()=>{
  const f=fixture("builder");
  await f.resolve("coarse",0,{ok:true,cfg:{lat:40.7,lon:-74,label:"New York",method:"2",source:"coarse-ip",tz:"America/New_York"}});
  const before={method:f.elements.get("method").value,hash:f.hash()};
  f.input("lat","40.8"); await f.advance(800);
  await f.resolve("reverse",0,{status:429,description:"rate limited"});
  console.log(JSON.stringify({before,after:{method:f.elements.get("method").value,hash:f.hash(),label:f.elements.get("label").value},reverseCalls:f.calls.reverse.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
