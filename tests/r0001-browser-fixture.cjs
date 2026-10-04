'use strict';
// Disposable local fixture: serve exact baseline/current source, inject only controlled inputs.
// Run: node tests/r0001-browser-fixture.cjs [evidence-directory]
// Each fresh scene must use a distinct query (e.g. ?case=ordinary&scene=noon), then HASH.
// A hash-only navigation does not rerun the widget's bootstrap or simulation parsing.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const ROOT = path.resolve(__dirname, '..');
const BASE = 'fd2972ba64225fe9d6848e92497e6d0ed20ea624';
const CLOCK = '2026-09-07T09:30:00.000Z';
const CANARY = '<svg onload="window.__sw_sec_probe=1"></svg>';
const HASH = '#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&simTime=12:30&simWx=0&simCloud=0&simTemp=72&simHumid=45&simWind=3&simWindDir=225&simPrecip=0&units=f&motion=full';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function prayer(day, hostileMonth = false) {
  const next = day === '08';
  return {
    timings: { Fajr:'04:46', Sunrise:'06:05', Dhuhr:'12:19', Asr:'15:48', Sunset:'18:33', Maghrib:'18:33', Isha:'20:03' },
    date: {
      gregorian: { date:`${day}-09-2026`, day, month:{number:9, en:hostileMonth ? CANARY : 'September'}, year:'2026' },
      hijri: { date:`${next ? '26' : '25'}-03-1448`, day:next ? '26' : '25', month:{number:3, en:hostileMonth ? CANARY : 'Rabi al-awwal'}, year:'1448', method:'HJCoSA' }
    },
    meta: { latitude:24.47, longitude:39.61, timezone:'Asia/Riyadh', method:{id:4}, school:'STANDARD' }
  };
}
function mutate(source, mutant) {
  const changes = {
    ce:[['${escHtml(projection.gregorianText)}','${projection.gregorianText}'],['${escHtml(fmtDate(g))}', '${fmtDate(g)}']],
    ah:[['${escHtml(projection.hijriText)}','${projection.hijriText}'],['${escHtml(fmtDate(ahH,"hijri"))}', '${fmtDate(ahH,"hijri")}']],
    preview:[['${escHtml(projection.previewDay)}','${projection.previewDay}'],['${escHtml(tomorrow.date.hijri.day)}', '${tomorrow.date.hijri.day}']],
    past:[['.p.past{', '.p.past{opacity:.42;']],
    on:[[',rgba(9,17,28,.90);border-color:', ';border-color:']]
  };
  if (!mutant) return source;
  const matches=(changes[mutant]||[]).filter(change=>source.includes(change[0]));
  if(matches.length!==1)throw new Error(`mutant ${mutant}: exact single version target missing`);
  const change=matches[0];
  if(source.split(change[0]).length!==2)throw new Error(`mutant ${mutant}: exact single target missing`);
  return source.replace(change[0], change[1]);
}
function preload(testCase) {
  const fixture = {clock:CLOCK, testCase, canary:CANARY, today:prayer('07', testCase === 'provider-month'), tomorrow:prayer('08', testCase === 'provider-month')};
  return `<script>"use strict";(() => {
    const fixture=${JSON.stringify(fixture)};
    const NativeDate=Date, fixedMs=NativeDate.parse(fixture.clock);
    window.Date=class extends NativeDate{constructor(...args){super(...(args.length?args:[fixedMs]));}static now(){return fixedMs;}};
    const storage=new Map();
    const memoryStorage={getItem:k=>storage.has(String(k))?storage.get(String(k)):null,setItem:(k,v)=>storage.set(String(k),String(v)),removeItem:k=>storage.delete(String(k)),clear:()=>storage.clear()};
    Object.defineProperty(window,'localStorage',{value:memoryStorage});
    if(fixture.testCase==='saved-format') memoryStorage.setItem('salah_widget:config:v1',JSON.stringify({v:1,lat:24.47,lon:39.61,tz:'Asia/Riyadh',label:'Madinah',method:'4',school:'0',time:'24',datefmt:fixture.canary,units:'f',lp:0,source:'manual',savedAt:fixedMs}));
    window.__sw_sec_probe=0;
    window.__uiFixture={...fixture,requests:[],renders:0,storage:'per-document in-memory Map (no persistent browser storage)',unexpectedFetch:[]};
    window.fetch=async input=>{
      const url=new URL(typeof input==='string'?input:input.url,location.href);
      window.__uiFixture.requests.push(url.href);
      if(url.origin==='https://api.aladhan.com' && /^\\/v1\\/timings\\/(07|08)-09-2026$/.test(url.pathname)){
        const value=url.pathname.includes('/08-')?fixture.tomorrow:fixture.today;
        return new Response(JSON.stringify({code:200,status:'OK',data:value}),{status:200,headers:{'Content-Type':'application/json'}});
      }
      window.__uiFixture.unexpectedFetch.push(url.href);
      throw new Error('Fixture blocks non-prayer fetch: '+url.href);
    };
  })();</script>`;
}
function hooks(testCase) {
  return `
// TEST-ONLY admitted-state control; source admission is never weakened.
// Selection now validates preview numbers; inject hostile text at the reached output boundary.
if(window.__uiFixture.testCase==='preview-day' && typeof renderCalendarDates==='function'){
  const uiFixtureDateSink=renderCalendarDates;
  renderCalendarDates=function(projection){
    if(projection.previewDay)projection={...projection,previewDay:window.__uiFixture.canary,previewText:phaseEmoji(moonNow().phase)+' '+window.__uiFixture.canary};
    return uiFixtureDateSink(projection);
  };
}
const uiFixtureRender=render;
render=function(){
  if(window.__uiFixture.testCase==='preview-day' && typeof renderCalendarDates!=='function' && tomorrow && tomorrow.date) tomorrow.date.hijri.day=window.__uiFixture.canary;
  if(window.__uiFixture.testCase==='stale') _prayerStale=true;
  const result=uiFixtureRender();
  window.__uiFixture.renders++;
  window.__uiFixture.ready=!!today && !!tomorrow && document.querySelectorAll('.p').length===6;
  window.__uiFixture.sourceConfig=CONFIG;
  return result;
};
`;
}
function documentFixture(source, options) {
  let html = mutate(source, options.mutant);
  if (html.split('\nboot();').length !== 2) throw new Error('Expected one real boot caller');
  // A frozen simTime does not schedule another render when tomorrow's async record arrives.
  // Render the already admitted records once after the real boot has completed.
  html = html.replace('\nboot();', hooks(options.testCase) + '\nboot().then(()=>setTimeout(render,0));');
  const styles = (options.hideText ? '.p b,.p .tm{visibility:hidden!important}' : '') + (options.stress ? '.times{background:#fff}' : '');
  return html.replace('<script src="config.js">', preload(options.testCase) + (styles ? `<style>${styles}</style>` : '') + '<script src="config.js">');
}
if (require.main === module) {
  const evidence = process.argv[2] ? path.resolve(process.argv[2]) : null;
  const baseline = execFileSync('git', ['show',`${BASE}:index.html`], {cwd:ROOT});
  const baseConfig = execFileSync('git', ['show',`${BASE}:config.js`], {cwd:ROOT});
  const receipts=[];
  const server=http.createServer((req,res)=>{
    try {
      const url=new URL(req.url,'http://127.0.0.1');
      if(url.pathname==='/favicon.ico'){res.writeHead(204);res.end();return;}
      if(/^\/(baseline|candidate)\/config\.js$/.test(url.pathname)){
        const bytes=url.pathname.startsWith('/baseline/')?baseConfig:fs.readFileSync(path.join(ROOT,'config.js'));
        res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8','Cache-Control':'no-store'});res.end(bytes);return;
      }
      if(!/^\/(baseline|candidate)\/index\.html$/.test(url.pathname)){res.writeHead(404);res.end('Fixture routes: /baseline/index.html and /candidate/index.html');return;}
      const bytes=url.pathname.startsWith('/baseline/')?baseline:fs.readFileSync(path.join(ROOT,'index.html'));
      const options={testCase:url.searchParams.get('case')||'ordinary',mutant:url.searchParams.get('mutant')||'',hideText:url.searchParams.has('hideText'),stress:url.searchParams.has('stress')};
      const html=documentFixture(bytes.toString('utf8'),options);
      receipts.push({at:new Date().toISOString(),route:url.pathname+url.search,sourceSha256:sha(bytes),servedFixtureSha256:sha(html),...options});
      if(evidence) fs.writeFileSync(path.join(evidence,'server-receipts.json'),JSON.stringify(receipts,null,2));
      res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(html);
    } catch(error){res.writeHead(500,{'Content-Type':'text/plain'});res.end(String(error));}
  });
  server.listen(0,'127.0.0.1',()=>{
    const receipt={pid:process.pid,port:server.address().port,host:'127.0.0.1',root:ROOT,base:BASE,baselineSha256:sha(baseline),baseConfigSha256:sha(baseConfig),clock:CLOCK,hash:HASH};
    if(evidence) fs.writeFileSync(path.join(evidence,'server.json'),JSON.stringify(receipt,null,2));
    console.log(JSON.stringify(receipt));
  });
}
module.exports={ROOT,BASE,CLOCK,CANARY,HASH,prayer,mutate,sha};
