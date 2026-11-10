'use strict';
// ROOT-owned driver fixture. Preparing/importing this file never starts a browser/server.
// ROOT run: node tests/r0009-browser-fixture.cjs [evidence-dir] [candidate-workspace-root]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {execFileSync}=require('node:child_process');
const {ROOT,record,sha,CANARY}=require('./r0009-calendar-harness.cjs');
const BASE='af553d1c9c9af402c29570abec2044e50420ca35';
function spec(name){
  const s={name,clock:'2026-09-07T17:59:59Z',zone:'UTC',today:record(),tomorrow:record('08','20'),format:'YYYY-MM-DD',holdTomorrow:false,saved:false,stale:false,injectedNext:null};
  if(['boundary','after','missing','late','different-method','unknown-method','wrong-day','wrong-zone'].includes(name))s.clock=name==='boundary'?'2026-09-07T18:00:00Z':'2026-09-07T18:01:00Z';
  if(['missing','late'].includes(name))s.holdTomorrow=true;
  if(name==='different-method')s.tomorrow.date.hijri.method='UAQ';
  if(name==='unknown-method')delete s.tomorrow.date.hijri.method;
  if(name==='wrong-day')s.injectedNext=record('09','21');
  if(name==='wrong-zone'){s.injectedNext=record('08','20');s.injectedNext.meta.timezone='Asia/Riyadh';}
  if(name==='invalid-next')s.injectedNext=record('08','31');
  if(name==='absent'){s.today.date.hijri=null;s.tomorrow.date.hijri=null;}
  if(['long','saved-long','preset-us','preset-eu','literal','month-literal','very-long','fallback-font','long-month','stale'].includes(name)){
    s.clock='2026-09-08T09:30:00Z';s.zone='Asia/Riyadh';s.today=record('08','26');s.tomorrow=record('09','27');s.format='DD MMMM YYYY';
    for(const data of [s.today,s.tomorrow]){data.meta.timezone=s.zone;data.date.hijri.month={number:3,en:'Rabīʿ al-awwal'};data.date.hijri.date=data.date.hijri.day+'-03-1448';}
  }
  if(name==='saved-long')s.saved=true;
  if(name==='preset-us')s.format='MM/DD/YYYY';
  if(name==='preset-eu')s.format='DD/MM/YYYY';
  if(name==='literal')s.format=CANARY+' التاريخ & "\' YYYY';
  if(name==='month-literal')for(const data of [s.today,s.tomorrow]){data.date.gregorian.month.en=CANARY;data.date.hijri.month.en=CANARY;}
  if(name==='long-month')for(const data of [s.today,s.tomorrow])data.date.hijri.month.en='Rabīʿ al-awwal '.repeat(70);
  if(name==='named-missing-name'){s.format='DD MMMM YYYY';delete s.today.date.hijri.month.en;}
  if(name==='very-long')s.format=('التاريخ full value < > & '.repeat(30))+'DD MMMM YYYY';
  if(name==='stale')s.stale=true;
  return s;
}
const cases=['before','boundary','after','missing','late','different-method','unknown-method','wrong-day','wrong-zone','invalid-next','absent','named-missing-name','long','saved-long','preset-us','preset-eu','literal','month-literal','very-long','long-month','fallback-font','stale'];
function routeHash(s){const fmt=s.saved?'&local=1':'&datefmt='+encodeURIComponent(s.format);return '#lat=24.47&lon=39.61&label=Madinah&method=4&tz='+encodeURIComponent(s.zone)+'&simWx=0&units=f&motion=full'+fmt;}
function buildPage(source,s){
  if(source.split('\nboot();').length!==2)throw Error('Actual boot caller drift');
  if(s.name==='fallback-font')source=source.replace(/<link\b[^>]*href=["']https:\/\/fonts\.googleapis\.com[^"']*["'][^>]*>/g,'');
  const pre=`<script>(()=>{
    const fixture=${JSON.stringify(s)},NativeDate=Date;let wall=NativeDate.parse(fixture.clock);
    window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[wall]));}static now(){return wall;}};
    const data=new Map(),writes=[],requests=[],pending=[];
    const storage={getItem:k=>data.get(String(k))??null,setItem:(k,v)=>{writes.push({operation:'set',key:String(k)});data.set(String(k),String(v));},removeItem:k=>{writes.push({operation:'remove',key:String(k)});data.delete(String(k));},clear:()=>{writes.push({operation:'clear'});data.clear();}};
    Object.defineProperty(window,'localStorage',{value:storage});
    if(fixture.saved)data.set('salah_widget:config:v1',JSON.stringify({v:1,lat:24.47,lon:39.61,tz:fixture.zone,label:'Madinah',method:'4',school:'0',time:'24',datefmt:fixture.format,units:'f',lp:0,source:'manual',savedAt:wall}));
    window.__sw_sec_probe=0;
    const response=value=>new Response(JSON.stringify({code:200,status:'OK',data:value}),{status:200,headers:{'Content-Type':'application/json'}});
    window.__calendarFixture={...fixture,storage:'per-document Map; no persistent owner storage',writes,requests,pending,ready:false,renders:0,instant:()=>wall,releaseTomorrow(value){fixture.holdTomorrow=false;fixture.tomorrow=value||fixture.tomorrow;pending.splice(0).forEach(resolve=>resolve(response(fixture.tomorrow)));},setInstant(value){wall=NativeDate.parse(value);},effects(){return {writes:writes.map(x=>({...x})),requests:[...requests]};}};
    window.fetch=input=>{const url=new URL(typeof input==='string'?input:input.url,location.href);requests.push(url.href);
      if(url.origin!=='https://api.aladhan.com')return Promise.reject(Error('Fixture blocks non-prayer fetch '+url.href));
      const requested=url.pathname.split('/').pop();
      if(requested===fixture.today.date.gregorian.date)return Promise.resolve(response(fixture.today));
      if(requested===fixture.tomorrow.date.gregorian.date){if(fixture.holdTomorrow)return new Promise(resolve=>pending.push(resolve));return Promise.resolve(response(fixture.tomorrow));}
      return Promise.reject(Error('Fixture request day not configured '+requested));
    };
  })();</script>`;
  const hooks=`
// TEST-ONLY admitted-state mismatches after real admission. The production clock/model stay intact.
const calendarFixtureRender=render;
render=function(){
  const fixture=window.__calendarFixture;
  if(fixture.injectedNext && tomorrow)tomorrow=structuredClone(fixture.injectedNext);
  if(fixture.stale)_prayerStale=true;
  const result=calendarFixtureRender();fixture.renders++;
  fixture.ready=!!today && document.querySelectorAll('.p').length===6;
  return result;
};
window.__calendarFixture.render=()=>render();
window.__calendarFixture.admittedState=(current,next)=>{today=current;tomorrow=next;fetchingTomorrow=true;render();};
`;
  return source.replace('<script src="config.js">',pre+'<script src="config.js">').replace('\nboot();',hooks+'\nboot().then(()=>setTimeout(render,0));');
}
if(require.main===module){
  const evidence=process.argv[2]?path.resolve(process.argv[2]):null,candidateRoot=process.argv[3]?path.resolve(process.argv[3]):ROOT;
  const baseline=execFileSync('git',['show',BASE+':index.html'],{cwd:ROOT}),baseConfig=execFileSync('git',['show',BASE+':config.js'],{cwd:ROOT});
  const candidate=fs.readFileSync(path.join(candidateRoot,'index.html')),config=fs.readFileSync(path.join(candidateRoot,'config.js')),receipts=[];
  let origin='';const server=http.createServer((req,res)=>{try{
    const url=new URL(req.url,'http://127.0.0.1');
    if(url.pathname==='/cases.json'){res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(cases.map(name=>({name,url:origin+'/candidate/index.html?case='+name+'&scene='+name+routeHash(spec(name))})),null,2));return;}
    if(/^\/(baseline|candidate)\/config\.js$/.test(url.pathname)){res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8','Cache-Control':'no-store'});res.end(url.pathname.startsWith('/baseline/')?baseConfig:config);return;}
    if(!/^\/(baseline|candidate)\/index\.html$/.test(url.pathname)){res.writeHead(404);res.end('Owned calendar fixture routes only');return;}
    const name=url.searchParams.get('case')||'before';if(!cases.includes(name))throw Error('Unknown controlled case');
    const bytes=url.pathname.startsWith('/baseline/')?baseline:candidate,page=buildPage(bytes.toString('utf8'),spec(name));
    receipts.push({at:new Date().toISOString(),route:url.pathname+url.search,sourceSha256:sha(bytes),fixtureSha256:sha(page),case:name});
    if(evidence)fs.writeFileSync(path.join(evidence,'r0009-server-receipts.json'),JSON.stringify(receipts,null,2));
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(page);
  }catch(error){res.writeHead(500,{'Content-Type':'text/plain'});res.end(String(error));}});
  server.listen(0,'127.0.0.1',()=>{origin='http://127.0.0.1:'+server.address().port;const receipt={pid:process.pid,origin,baselineCommit:BASE,baselineSha256:sha(baseline),candidateRoot,candidateSha256:sha(candidate),configSha256:sha(config),caseIndex:origin+'/cases.json',scope:'ROOT driver only; captured bytes frozen at server start; no clock/loader qualification'};if(evidence)fs.writeFileSync(path.join(evidence,'r0009-server.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));});
}
module.exports={BASE,cases,spec,routeHash,buildPage};
