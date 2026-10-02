"use strict";
// Disposable loopback stream for the parent's exclusive native browser bridge.
// Inject only the two known coarse URLs to these routes before loading config.js.
const http=require("node:http");
function createFixtureServer(){
  const ledger=[],sockets=new Set();
  const server=http.createServer((req,res)=>{
    const row={path:req.url,headersAt:Date.now(),closedAt:null,completed:false};ledger.push(row);
    res.on("close",()=>row.closedAt=Date.now());
    res.setHeader("Access-Control-Allow-Origin","*");res.setHeader("Content-Type","application/json");
    if(req.url==="/ledger"){res.end(JSON.stringify(ledger));return;}
    if(req.url==="/ipinfo"){row.completed=true;res.end(JSON.stringify({loc:"51.5,-0.12",city:"London",country:"GB",timezone:"Europe/London"}));return;}
    if(req.url==="/geojs-finite"){res.write('{"latitude":"24.47",');setTimeout(()=>{if(!res.destroyed){row.completed=true;res.end('"longitude":"39.61","city":"Madinah","country_code":"SA"}');}},10);return;}
    if(req.url==="/geojs-stall"){res.write('{"latitude":"24.47",');return;}
    res.statusCode=503;row.completed=true;res.end('{"error":"fixture failure"}');
  });
  server.on("connection",socket=>{sockets.add(socket);socket.on("close",()=>sockets.delete(socket));});
  return {server,ledger,close:()=>{for(const socket of sockets)socket.destroy();server.close();}};
}
if(require.main===module){const fixture=createFixtureServer();fixture.server.listen(Number(process.argv[2]||0),"127.0.0.1",()=>console.log(JSON.stringify({origin:`http://127.0.0.1:${fixture.server.address().port}`,routes:["/geojs-stall","/geojs-finite","/ipinfo","/failure","/ledger"]})));process.on("SIGINT",fixture.close);}
module.exports={createFixtureServer};
