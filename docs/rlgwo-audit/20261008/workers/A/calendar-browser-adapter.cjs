'use strict';
// Bounded adaptation of the retained R0009 fixture, not a browser driver.
// --prepare validates anchors and writes prepared inputs only. --serve is for
// the primary's serial browser lane. Neither mode launches a browser.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const ROOT='C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const {buildPage,spec,routeHash}=require(path.join(ROOT,'tests/r0009-browser-fixture.cjs'));
const {record}=require(path.join(ROOT,'tests/r0009-calendar-harness.cjs'));
const {nativeInlineRuntime}=require(path.join(ROOT,'tests/native-inline-runtime.cjs'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const replaceOne=(source,before,after)=>{assert.equal(source.split(before).length,2,'Exact single anchor: '+before.slice(0,100));return source.replace(before,after);};
const cases=['completed-offline','late-duplicate','late-rescue-hidden','no-promotion-control','unconditional-next-control','no-dirty-control'];
function input(name){
 assert(cases.includes(name));const s=spec('before');s.name=name;s.clock='2026-09-07T23:59:59Z';
 for(const [data,tag] of [[s.today,'day7'],[s.tomorrow,'day8-old']]){data.tag=tag;Object.assign(data.timings,{Asr:'15:30',Isha:'19:30'});}
 s.following=record('09','21');s.following.tag='day9';Object.assign(s.following.timings,{Asr:'15:30',Isha:'19:30'});
 s.holdTomorrow=!['completed-offline','no-promotion-control'].includes(name);s.hidden=false;s.offline=false;return s;
}
const OBSERVER=String.raw`
// Read-only observation after the actual production render. No manual render
// or admitted-state injection is used by this R0005 adapter.
window.__calendarFixture.paints=[];
window.__calendarFixture.settlements=[];
window.__calendarFixture.snapshot=()=>({utcMs:simNow(),generation:_runtimeGeneration,lastDate,
 today:today?{date:today.date.gregorian.date,tag:today.tag}:null,
 tomorrow:tomorrow?{date:tomorrow.date.gregorian.date,tag:tomorrow.tag}:null,
 stale:_prayerStale,dirty:_renderDirty,loopStarted:_loopStarted,
 slots:Object.fromEntries(Object.entries(_requestSlots).map(([k,v])=>[k,v?{operationId:v.operationId,generation:v.generation,requestedDay:v.requestedDay}:null])),
 ce:document.querySelector('#ce')?.textContent,ah:document.querySelector('#ah')?.textContent,
 next:document.querySelector('.nt')?.textContent,countdown:document.querySelector('.left')?.textContent,
 status:document.querySelector('.status')?.textContent,rows:document.querySelectorAll('.p').length,
 dateTruth:window.qaState?.().dateTruth,effects:window.__calendarFixture.effects()});
const auditCalendarRender=render;
render=function(){const result=auditCalendarRender();window.__calendarFixture.paints.push(window.__calendarFixture.snapshot());return result;};
window.__calendarFixture.setVisibility=hidden=>{window.__calendarFixture.hidden=!!hidden;document.dispatchEvent(new Event('visibilitychange'));};
`;
function adaptedPage(source,name){
 const s=input(name);nativeInlineRuntime(source);let changed=source;
 if(name==='no-promotion-control')changed=replaceOne(changed,'if(prayerRecordReady(tomorrow,day)) adoptPrayerBundle(tomorrow,day);','if(false) adoptPrayerBundle(tomorrow,day);');
 if(name==='unconditional-next-control')changed=replaceOne(changed,'fetchTimings(day,op).then(data=>{ adoptPrayerBundle(data,day,op,false); })','fetchTimings(day,op).then(data=>{ tomorrow=data; _renderDirty=true; })');
 if(name==='no-dirty-control')changed=replaceOne(changed,'if(sec!==_lastSec || _renderDirty)','if(sec!==_lastSec)');
 const coreSource=changed;
 // Observe the actual prefetch callback's state before its existing finally
 // and before a later visible frame can clear a poisoned slot. This adds only
 // one observation microtask; it never paints or changes admission/slots.
 changed=replaceOne(changed,'.catch(()=>{}).finally(()=>{ finishPrayerRequest(op); });',
  '.then(()=>{ window.__calendarFixture.settlements.push(window.__calendarFixture.snapshot()); })\n    .catch(()=>{}).finally(()=>{ finishPrayerRequest(op); });');
 let html=buildPage(changed,s);
 // The old driver manually painted after boot. Preserve the real caller and
 // remove that workaround so fixed-second consumer invalidation can fail.
 html=replaceOne(html,'boot().then(()=>setTimeout(render,0));',OBSERVER+'\nboot();');
 // Deliberately retain the original fixture API; the following extensions
 // expose its existing private Map/pending queues and exact local assets.
 html=replaceOne(html,'window.fetch=input=>{','const originalAuditFetch=window.fetch; window.fetch=(input,options)=>{');
 html=replaceOne(html,'requests.push(url.href);','requests.push(url.href); if(url.origin===location.origin)return originalAuditFetch(input,options); if(fixture.offline)return Promise.reject(Error("Controlled prayer offline"));');
 html=replaceOne(html,'if(fixture.holdTomorrow)return new Promise(resolve=>pending.push(resolve));','if(fixture.holdTomorrow)return new Promise(resolve=>{resolve.auditRequest={id:requests.length-1,date:requested};pending.push(resolve);});');
 html=replaceOne(html,"return Promise.reject(Error('Fixture request day not configured '+requested));",'if(requested===fixture.following.date.gregorian.date)return Promise.resolve(response(fixture.following)); return Promise.reject(Error("Fixture request day not configured "+requested));');
 return {name,input:s,sourceSha256:sha(source),instrumentedNativeSourceSha256:sha(changed),mutantSourceSha256:coreSource===source?null:sha(coreSource),mutant:name.endsWith('-control'),html};
}
// Add fixture controls at a unique existing pre-script boundary. The private
// storage/response closure remains the retained fixture's own implementation.
function pageFor(source,name){
 let result=adaptedPage(source,name),html=result.html;
 html=replaceOne(html,'const originalAuditFetch=window.fetch;',String.raw`
    const owner=window.__calendarFixture;
    Object.defineProperty(document,'hidden',{configurable:true,get:()=>owner.hidden});
    Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>owner.hidden?'hidden':'visible'});
    owner.releasePending=(index,value)=>{const resolve=pending.splice(index,1)[0];if(!resolve)throw Error('No held prayer at index '+index);resolve(response(value||fixture.tomorrow));};
    owner.failPending=index=>{const resolve=pending.splice(index,1)[0];if(!resolve)throw Error('No held prayer at index '+index);resolve(new Response('Controlled failure',{status:503}));};
    owner.setOffline=value=>{fixture.offline=!!value;};
    owner.pendingRequests=()=>pending.map(resolve=>resolve.auditRequest);
    owner.cache=()=>Object.fromEntries(data);
    const originalAuditFetch=window.fetch;`);
 result.html=html;result.fixtureSha256=sha(html);return result;
}
function prepare(){
 const source=fs.readFileSync(path.join(ROOT,'index.html'),'utf8');assert.equal(sha(source),'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee');
 const pages=cases.map(n=>pageFor(source,n));
 for(const p of pages){const scripts=Array.from(p.html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g));for(const s of scripts.filter(s=>s[2].trim()))new (require('node:vm').Script)(s[2],{filename:p.name+':inline'});assert.equal(p.html.split('\nboot();').length,2);assert(!p.html.includes('boot().then(()=>setTimeout(render,0));'));}
 return {source,pages,receipt:{schema:'bounded-calendar-browser-preparation/1',status:'PREPARED ONLY; NO BROWSER EXECUTION',targetCommit:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',root:ROOT,sourceSha256:sha(source),adapterSha256:sha(fs.readFileSync(__filename)),originalFixtureSha256:sha(fs.readFileSync(path.join(ROOT,'tests/r0009-browser-fixture.cjs'))),originalExpectationsPreserved:true,cases:pages.map(({html,...p})=>p),scope:'Retained R0009 fixed-clock/provider/Map fixture adapted to actual generated root; original boot caller restored, observation/control APIs added. Actual production render/rAF/admission/day code retained. No browser, pixel, OS-hidden-state, provider, clock or deployment proof follows.'}};
}
if(require.main===module){
 const prepared=prepare();fs.writeFileSync(path.join(__dirname,'calendar-browser-preparation.json'),JSON.stringify(prepared.receipt,null,2)+'\n');
 if(process.argv.includes('--serve')){
  const pages=new Map(prepared.pages.map(p=>[p.name,p]));let origin='';
  const server=http.createServer((req,res)=>{try{
   const u=new URL(req.url,'http://127.0.0.1');if(u.pathname==='/cases.json'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(prepared.pages.map(p=>({name:p.name,url:origin+'/index.html?case='+p.name+routeHash(p.input)}))));return;}
   if(u.pathname==='/index.html'){const p=pages.get(u.searchParams.get('case'));assert(p,'Known case required');res.setHeader('Content-Type','text/html; charset=utf-8');res.end(p.html);return;}
   const file=path.resolve(ROOT,'.'+decodeURIComponent(u.pathname));assert(file.startsWith(path.resolve(ROOT)+path.sep),'Asset stays inside exact root');if(!fs.statSync(file).isFile())throw Error('Not a file');res.setHeader('Content-Type',/\.m?js$/.test(file)?'text/javascript':/\.css$/.test(file)?'text/css':/\.wasm$/.test(file)?'application/wasm':/\.json$/.test(file)?'application/json':'application/octet-stream');res.end(fs.readFileSync(file));
  }catch(e){res.statusCode=404;res.end(String(e));}});
  server.listen(0,'127.0.0.1',()=>{origin='http://127.0.0.1:'+server.address().port;const info={pid:process.pid,origin,caseIndex:origin+'/cases.json',sourceSha256:prepared.receipt.sourceSha256};fs.writeFileSync(path.join(__dirname,'calendar-browser-server.json'),JSON.stringify(info,null,2)+'\n');console.log(JSON.stringify(info));});
 }else console.log(JSON.stringify({status:prepared.receipt.status,cases:prepared.pages.length,allInlineScriptsParse:true,sourceSha256:prepared.receipt.sourceSha256}));
}
module.exports={ROOT,cases,input,pageFor,prepare};
