'use strict';
// R0033 isolation wiring (issue 100): a hermetic fake of the small Playwright surface that
// tools/qa/r0033_isolation.cjs and the smoke cell of tools/qa/r0033_remaining_cells.cjs use. No browser, no network.
// It records every call in order and, on goto(), replays a scripted set of synthetic requests: each request is
// offered to every installed context route (the disposition the handler chose is recorded), then 'requestfinished'
// (or 'requestfailed') is emitted for it; 'bypass' requests are emitted WITHOUT being offered to any route, as an
// engine that does not route them would. Used in-process through create() and, as `--playwright <this file>`, by a
// child recipe run, which reads its scenario from R33_FAKE (JSON) and writes its call log to R33_FAKE_LOG.
const fs=require('node:fs');
// scenario: {requests:[{url,type?,fail?}], bypass:[{url,type?,fail?}], responses:[{url,ip}], noRouteWebSocket?, smoke?}
function create(scenario={},onLog=null){
  const log=[],note=e=>{log.push(e);if(onLog)onLog(log);};
  const guardState=()=>{try{return require('../tools/qa/v1_net_guard.cjs').state.installed;}catch{return null;}};
  function engine(name){return {launch:async options=>{note({call:'launch',engine:name,guardInstalled:guardState(),proxy:options?.proxy??null,args:options?.args??[]});
    const contexts=[];
    const browser={version:()=>'fake-1.0',contexts,
      newContext:async options=>{const routes=[],listeners={},ctx={options,routes,listeners,pages:0};contexts.push(ctx);note({call:'newContext',serviceWorkers:options?.serviceWorkers??null});
        const emit=(evt,arg)=>{for(const f of listeners[evt]||[])f(arg);};
        const fire=async(spec,offer)=>{const req={url:()=>spec.url,resourceType:()=>spec.type||'other'};
          if(offer)for(const r of routes){let disposition=null;const route={request:()=>req,continue:async()=>{disposition='continue';},abort:async()=>{disposition='abort';},fulfill:async o=>{disposition='fulfill';route.body=o?.body;}};
            await r.handler(route);note({call:'disposition',url:spec.url,disposition,pattern:r.pattern});if(disposition)break;}
          emit(spec.fail?'requestfailed':'requestfinished',req);};
        const page={on:(evt,f)=>{note({call:'page.on',evt});},addInitScript:async()=>{note({call:'page.addInitScript'});},
          clock:{install:async()=>{note({call:'clock.install'});},resume:async()=>{note({call:'clock.resume'});},fastForward:async()=>{}},
          goto:async url=>{note({call:'goto',url,routesInstalled:routes.length});
            for(const spec of scenario.requests||[])await fire(spec,true);
            for(const spec of scenario.bypass||[])await fire(spec,false);
            for(const r of scenario.responses||[])emit('response',{url:()=>r.url,serverAddr:()=>new Promise(res=>setTimeout(()=>res({ipAddress:r.ip,port:443}),20))});},
          waitForFunction:async()=>true,waitForTimeout:async()=>{},
          evaluate:async()=>scenario.smoke??{status:'PASS',pass:1,fail:0,skip:0,required:{cases:Array.from({length:22},(_,i)=>({name:'case '+(i+1),expected:'pass',assertions:1,state:'PASS',reason:null})),failed:[],missing:[]}}};
        Object.assign(ctx,{
          route:async(pattern,handler)=>{note({call:'route',pattern:String(pattern),pagesBefore:ctx.pages});routes.push({pattern:String(pattern),handler});},
          unroute:async()=>{note({call:'unroute'});routes.length=0;},unrouteAll:async()=>{note({call:'unrouteAll'});routes.length=0;},
          on:(evt,f)=>{note({call:'context.on',evt});(listeners[evt]=listeners[evt]||[]).push(f);},
          addInitScript:async()=>{note({call:'context.addInitScript'});},
          newPage:async()=>{ctx.pages++;note({call:'newPage',routesInstalled:routes.map(r=>r.pattern)});return page;},
          close:async()=>{note({call:'context.close'});}});
        if(!scenario.noRouteWebSocket)ctx.routeWebSocket=async(pattern)=>{note({call:'routeWebSocket',pattern:String(pattern),pagesBefore:ctx.pages});};
        return ctx;},
      newBrowserCDPSession:async()=>{throw new Error('fake: no CDP');},
      close:async()=>{note({call:'browser.close'});}};
    return browser;}};}
  return {chromium:engine('chromium'),firefox:engine('firefox'),webkit:engine('webkit'),log};
}
let scenario={};try{if(process.env.R33_FAKE)scenario=JSON.parse(process.env.R33_FAKE);}catch{}
const file=process.env.R33_FAKE_LOG,fromEnv=create(scenario,file?l=>fs.writeFileSync(file,JSON.stringify(l)):null);
module.exports={create,chromium:fromEnv.chromium,firefox:fromEnv.firefox,webkit:fromEnv.webkit,log:fromEnv.log};
