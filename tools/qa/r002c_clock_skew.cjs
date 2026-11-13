// node clockskew.cjs <playwright> <tree> [scale]: per-frame entry offsets (ms, performance.now) of syncWeather/renderMoon/projectStars/applyTheme relative to model() under timeScale
const fs=require('fs'),path=require('path'),http=require('http');const {chromium}=require(process.argv[2]);const root=path.resolve(process.argv[3]);const scale=+(process.argv[4]||1800);
const T={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm','.png':'image/png','.bin':'application/octet-stream'};
const srv=http.createServer((q,s)=>{const p=path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname));if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){s.writeHead(404);return s.end();}s.writeHead(200,{'content-type':T[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(s);});
const rec=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
(async()=>{await new Promise(r=>srv.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+srv.address().port;
const b=await chromium.launch();const c=await b.newContext({viewport:{width:325,height:530},timezoneId:'America/Los_Angeles'});
await c.route('**/*',r=>{const u=r.request().url();if(u.startsWith(base))return r.continue();const m=/timings\/(\d\d-\d\d-\d{4})/.exec(u);if(m){const x=JSON.parse(JSON.stringify(rec));x.meta.timezone='Asia/Riyadh';x.date.gregorian.date=m[1];return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:x})});}return r.abort();});
const p=await c.newPage();await p.clock.install({time:new Date('2026-09-07T08:00:00Z')});await p.goto(base+'/index.html#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh&simTime=12:00&timeScale='+scale+'');
await p.waitForFunction(()=>{try{return !!window.eval('today')&&window.eval('_loopStarted')}catch(e){return false}},null,{timeout:20000});
const out=await p.evaluate(async()=>{const F=[];let cur=null;const wrap=n=>{const f=window[n];window[n]=function(...a){const t=performance.now();if(n==='model'){cur={model:t};F.push(cur);}else if(cur&&cur[n]==null)cur[n]=t;return f.apply(this,a);};};
 for(const n of ['model','syncWeather','renderMoon','projectStars','applyTheme'])wrap(n);
 await new Promise(r=>setTimeout(r,4000));return F.filter(f=>f.applyTheme!=null).map(f=>({sync:f.syncWeather-f.model,moon:f.renderMoon!=null?f.renderMoon-f.model:null,stars:f.projectStars!=null?f.projectStars-f.model:null,theme:f.applyTheme-f.model}));});
const st=k=>{const v=out.map(o=>o[k]).filter(x=>x!=null).sort((a,b)=>a-b);return v.length?{n:v.length,median:+v[v.length>>1].toFixed(2),p95:+v[Math.floor(v.length*0.95)].toFixed(2),max:+v[v.length-1].toFixed(2)}:null;};
console.log(JSON.stringify({tree:path.basename(root),timeScale:scale,frames:out.length,syncWeatherMinusModelMs:st('sync'),renderMoonMinusModelMs:st('moon'),projectStarsMinusModelMs:st('stars'),applyThemeMinusModelMs:st('theme')}));
await b.close();srv.close();})().catch(e=>{console.error(e);process.exit(1);});
