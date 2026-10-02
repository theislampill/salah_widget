'use strict';
// ROOT drives native review. Importing/preparing this fixture starts no browser or server.
// ROOT run: node tests/r0018-appearance-browser-fixture.cjs [new-evidence-directory] [candidate-workspace]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {execFileSync}=require('node:child_process');
const {ROOT,BASE:PREVIOUS,sha}=require('./r0018-appearance-fixture.cjs');
const {prayer}=require('./r0001-browser-fixture.cjs');
const {mutateTimetable}=require('./r0018-timetable-contrast.cjs');
const scenes={noon:{time:'12:30',wx:0,cloud:0},sunrise:{time:'05:50',wx:0,cloud:0},sunset:{time:'18:55',wx:0,cloud:0},night:{time:'23:30',wx:0,cloud:0},broken:{time:'12:30',wx:2,cloud:50},overcast:{time:'12:30',wx:3,cloud:100}};
function spec(name='noon',appearance='default'){
 if(!Object.hasOwn(scenes,name)||!['default','glass','contrast'].includes(appearance))throw Error('Unknown bounded appearance scene');
 const scene=scenes[name],parts=scene.time.split(':').map(Number),clock=new Date(Date.UTC(2026,8,7,parts[0]-3,parts[1])).toISOString();
 return {name,appearance,...scene,clock,zone:'Asia/Riyadh',today:prayer('07'),tomorrow:prayer('08')};
}
function routeHash(s){
 const q=new URLSearchParams({lat:'24.47',lon:'39.61',label:'Madinah',method:'4',tz:s.zone,simTime:s.time,simWx:String(s.wx),simCloud:String(s.cloud),simTemp:'72',simHumid:'45',simWind:'3',simWindDir:'225',simPrecip:'0',units:'f',motion:'full'});
 if(s.appearance!=='default')q.set('appearance',s.appearance);
 return '#'+q.toString();
}
function buildPage(source,s,options={}){
 if(options.mutant)source=mutateTimetable(source,options.mutant);
 if(source.split('<script src="config.js">').length!==2)throw Error('Expected one real config loader');
 const pre=`<script>(()=>{
 const spec=${JSON.stringify(s)},NativeDate=Date,wall=NativeDate.parse(spec.clock),data=new Map(),writes=[],requests=[],unexpectedFetch=[];
 window.Date=class extends NativeDate{constructor(...a){super(...(a.length?a:[wall]));}static now(){return wall;}};
 const fixture=window.__appearanceFixture={spec,storage:'private per-document Map; no owner storage',writes,requests,unexpectedFetch,failSave:${!!options.failSave},failReset:${!!options.failReset}};
 const storage={getItem:k=>data.get(String(k))??null,setItem:(k,v)=>{if(fixture.failSave&&k==='salah_widget:config:v1'){const e=Error('Controlled refusal');e.name='QuotaExceededError';throw e;}writes.push({operation:'set',key:String(k)});data.set(String(k),String(v));},removeItem:k=>{if(fixture.failReset&&k==='salah_widget:config:v1'){const e=Error('Controlled refusal');e.name='SecurityError';throw e;}writes.push({operation:'remove',key:String(k)});data.delete(String(k));}};
 Object.defineProperty(window,'localStorage',{value:storage});
 window.fetch=async input=>{const url=new URL(typeof input==='string'?input:input.url,location.href);requests.push(url.href);
  if(url.origin==='https://api.aladhan.com'&&/^\\/v1\\/timings\\/(07|08)-09-2026$/.test(url.pathname))return new Response(JSON.stringify({code:200,status:'OK',data:url.pathname.includes('/08-')?spec.tomorrow:spec.today}),{status:200,headers:{'Content-Type':'application/json'}});
  unexpectedFetch.push(url.href);throw Error('Fixture blocks unrelated provider '+url.href);
 };
 fixture.textHidden=false;fixture.setTextHidden=hidden=>{let style=document.getElementById('appearance-fixture-hidden-text');if(!style){style=document.createElement('style');style.id='appearance-fixture-hidden-text';document.head.appendChild(style);}style.textContent=hidden?'.p b,.p .tm{visibility:hidden!important}':'';fixture.textHidden=!!hidden;};
 })();</script>`;
 const inspect=`<script>window.__appearanceFixture.snapshot=()=>{
 const f=window.__appearanceFixture,rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
 const rows=Array.from(document.querySelectorAll('.p')).map(e=>{const cs=getComputedStyle(e);return {text:e.textContent,className:e.className,rect:rect(e),color:cs.color,opacity:cs.opacity,background:cs.background,filter:cs.filter,blend:cs.mixBlendMode,backdropFilter:cs.backdropFilter,texts:Array.from(e.querySelectorAll('b,.tm')).map(t=>({text:t.textContent,rect:rect(t),font:getComputedStyle(t).font,fontFamily:getComputedStyle(t).fontFamily}))};});
 const card=document.querySelector('.c'),fonts=Array.from(document.fonts,f=>({family:f.family,status:f.status,weight:f.weight,style:f.style}));
 return {spec:f.spec,ready:!!today&&!!tomorrow&&rows.length===6,configAppearance:CONFIG&&CONFIG.appearance,cardAppearance:card.dataset.appearance,card:rect(card),rows,ce:document.getElementById('ce').textContent,ah:document.getElementById('ah').textContent,units,weather:{wx:SIM.wx,cloud:SIM.cloud,precip:SIM.precip},viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},browser:navigator.userAgent,fontStatus:document.fonts.status,fonts,inter:document.fonts.check('600 12.5px Inter','Fajr 04:46'),fraunces:document.fonts.check('600 30px Fraunces','Dhuhr'),texture:{albedo:!!_mAlb,normal:!!_mNrm,pbrReady:_pbrReady},motion:{scale:TIMESCALE,reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,override:'full',claim:'Frozen stills; no live-motion evidence'},date:{current:today&&today.date.gregorian.date,next:tomorrow&&tomorrow.date.gregorian.date,zone:tz},textHidden:f.textHidden,requests:[...f.requests],unexpectedFetch:[...f.unexpectedFetch],writes:[...f.writes]};
};</script>`;
 const stress=options.stress?'<style>.times{background:#fff}</style>':'';
 // Keep every production script body and the real boot/rAF/admission/calendar callers intact.
 return source.replace('<script src="config.js">',pre+stress+'<script src="config.js">').replace('</body>',inspect+'</body>');
}
function routes(){
 const out=[];for(const scene of Object.keys(scenes))for(const surface of ['previous-dark','default-glass','high-contrast']){const s=spec(scene,surface==='high-contrast'?'contrast':'default');out.push({name:surface+'-'+scene,spec:s,route:'/'+(surface==='previous-dark'?'previous':'candidate')+'/index.html?scene='+scene+'&appearance='+s.appearance+'&fresh='+surface+'-'+scene+routeHash(s)});}
 for(const mutant of ['','past','on']){const s=spec('noon','contrast');out.push({name:'contrast-white-stress'+(mutant?'-'+mutant+'-mutant':''),spec:s,options:{stress:true,mutant},route:'/candidate/index.html?scene=noon&appearance=contrast&stress=1'+(mutant?'&mutant='+mutant:'')+'&fresh=stress-'+(mutant||'healthy')+routeHash(s)});}
 for(const refuse of ['','save','reset']){const s=spec('noon','glass');out.push({name:'native-settings'+(refuse?'-refused-'+refuse:''),spec:s,options:{failSave:refuse==='save',failReset:refuse==='reset'},route:'/candidate/index.html?scene=noon&appearance=glass'+(refuse?'&refuse='+refuse:'')+'&fresh=settings-'+(refuse||'healthy')+routeHash(s)+'&preferLocal=1'});}
 return out;
}
if(require.main===module){
 const evidence=process.argv[2]?path.resolve(process.argv[2]):null,candidateRoot=process.argv[3]?path.resolve(process.argv[3]):ROOT;
 if(evidence&&!fs.existsSync(evidence))throw Error('Create a new owned evidence directory before server start');
 const prior={index:execFileSync('git',['show',PREVIOUS+':index.html'],{cwd:ROOT}),config:execFileSync('git',['show',PREVIOUS+':config.js'],{cwd:ROOT})},candidate={index:fs.readFileSync(path.join(candidateRoot,'index.html')),config:fs.readFileSync(path.join(candidateRoot,'config.js'))};
 let origin='';const server=http.createServer((req,res)=>{try{const url=new URL(req.url,'http://127.0.0.1');
  if(url.pathname==='/cases.json'){res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(routes().map(c=>({...c,url:origin+c.route})),null,2));return;}
  if(/^\/(previous|candidate)\/config\.js$/.test(url.pathname)){const bytes=url.pathname.startsWith('/previous/')?prior.config:candidate.config;res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8','Cache-Control':'no-store'});res.end(bytes);return;}
  if(!/^\/(previous|candidate)\/index\.html$/.test(url.pathname)){res.writeHead(404);res.end('Owned appearance fixture routes only');return;}
  const s=spec(url.searchParams.get('scene')||'noon',url.searchParams.get('appearance')||'default'),options={stress:url.searchParams.has('stress'),mutant:url.searchParams.get('mutant')||'',failSave:url.searchParams.get('refuse')==='save',failReset:url.searchParams.get('refuse')==='reset'},bytes=url.pathname.startsWith('/previous/')?prior.index:candidate.index;
  const page=buildPage(bytes.toString('utf8'),s,options),receipt={at:new Date().toISOString(),route:url.pathname+url.search,sourceSha256:sha(bytes),fixtureSha256:sha(page),spec:s,...options};
  if(evidence)fs.appendFileSync(path.join(evidence,'r0018-appearance-requests.jsonl'),JSON.stringify(receipt)+'\n');
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(page);
 }catch(e){res.writeHead(500,{'Content-Type':'text/plain'});res.end(String(e));}});
 server.listen(0,'127.0.0.1',()=>{origin='http://127.0.0.1:'+server.address().port;const receipt={pid:process.pid,origin,previousCommit:PREVIOUS,previousIndexSha256:sha(prior.index),previousConfigSha256:sha(prior.config),candidateRoot,candidateIndexSha256:sha(candidate.index),candidateConfigSha256:sha(candidate.config),caseIndex:origin+'/cases.json',scope:'ROOT native driver; exact source bytes frozen at server start; no browser results yet'};if(evidence)fs.writeFileSync(path.join(evidence,'r0018-appearance-server.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(receipt));});
}
module.exports={PREVIOUS,scenes,spec,routeHash,buildPage,routes};
