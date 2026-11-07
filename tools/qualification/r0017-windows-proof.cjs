#!/usr/bin/env node
'use strict';
/* One-off R0017 native Windows evidence collector. Only Node built-ins.
 * Talks W3C WebDriver + BiDi to image-installed ChromeDriver/GeckoDriver.
 * Does not replace __smoke, qaState, assertions, application code or deadlines.
 * A successful process exit means FIRST-PHASE checks passed, never R0017 closure.
 */
const fs=require('node:fs'), path=require('node:path'), os=require('node:os');
const http=require('node:http'), net=require('node:net'), crypto=require('node:crypto');
const {spawn,execFileSync}=require('node:child_process');
const {setTimeout:delay}=require('node:timers/promises');
const PIN='eebba178172f96b3ffe5ab3845bc0fffd57c6e1b';
const PUBLIC='https://theislampill.github.io/salah_widget/';
const args={}; for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i].startsWith('--')||!process.argv[i+1])throw Error('Use --root PATH --out PATH');args[process.argv[i].slice(2)]=process.argv[i+1];}
const ROOT=path.resolve(args.root||'candidate'),OUT=path.resolve(args.out||'artifacts');
const EXPECTED=args['payload-sha']||PIN;
if(EXPECTED!==PIN)throw Error('This reviewed first-phase proposal is bound to '+PIN);
const runId='R0017-'+(process.env.GITHUB_RUN_ID||'manual')+'-'+crypto.randomUUID();
const budgetStart=performance.now(),budgetWallStart=Date.now(),configuredDeadline=Date.parse(process.env.R0017_OPERATION_DEADLINE_UTC||'');
const operationWindowMs=process.env.R0017_OPERATION_DEADLINE_UTC?(Number.isFinite(configuredDeadline)?Math.max(0,Math.min(960000,configuredDeadline-budgetWallStart)):0):960000;
const remainingBudgetMs=()=>operationWindowMs-(performance.now()-budgetStart);
function operationTimeout(max){const left=Math.floor(remainingBudgetMs());if(left<=0){const e=Error('Collector operation budget exhausted; application deadlines remain unchanged');e.code='R0017_BUDGET_EXHAUSTED';throw e;}return Math.min(max,left);}
const FIRST_PHASE_PLAN=Object.freeze(['chromium','firefox'].flatMap(engine=>[['healthy','no-preference','valid'],['healthy','reduce','malformed'],['reject','no-preference','absent'],['hang','reduce','malformed'],['bootstrap-error','no-preference','valid']].map(([mode,preference,storage])=>({engine,mode,preference,storage,ordinary:false}))).concat(['chromium','firefox'].map(engine=>({engine,mode:'healthy',preference:'no-preference',storage:'absent',ordinary:true}))).map(p=>Object.freeze({...p,name:[p.engine,p.ordinary?'public-ordinary':p.mode,p.preference,p.storage].join('-')})));
if(fs.existsSync(OUT)&&fs.readdirSync(OUT).length)throw Error('Refusing nonempty output directory; choose a fresh path to preserve all previous attempts');
fs.mkdirSync(OUT,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function write(file,obj){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(obj,null,2)+'\n');}
function record(file,obj){fs.appendFileSync(file,JSON.stringify(obj)+'\n');}
function git(...a){return execFileSync('git',a,{cwd:ROOT,encoding:'utf8',windowsHide:true}).trim();}
function fail(message){throw Error(message);}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
const safeEnv=Object.fromEntries(['ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_REF','GITHUB_REPOSITORY'].map(k=>[k,process.env[k]??null]));
const result={schema:'r0017-windows-first-phase/v1',qualification:'PARTIAL',status:'STARTED',runId,
 startedUtc:new Date().toISOString(),host:{platform:process.platform,release:os.release(),version:os.version(),arch:os.arch(),cpus:os.cpus().length,node:process.version,runner:safeEnv},
 scope:'First native Windows affected matrix; real engines, emulated motion, controlled providers, private storage. No production appearance, full-sky or normal-live M0 credit.',
 pending:['A03 current native null-frame/missing-config/source-anchor/duplicate-date/stale-owner semantic controls',
 'A04 current native ignore-reduction/ignore-full semantic mutants and forced throw/timeout exact restoration',
 'Storage valid/malformed/absent full outcome cross-product and restored/spied throw/timeout controls',
 'Delivered public smoke matrix and complete served dependency identity reconciliation',
 'Independent cold review, source-currentness admission, old eight exceptions and four TODO disposition, publication and conditional closure'],cases:[]};
result.plannedCases=FIRST_PHASE_PLAN;result.plannedCount=FIRST_PHASE_PLAN.length;result.inventory={};result.engineSetupBlocks={};
result.budget={configuredDeadlineUtc:process.env.R0017_OPERATION_DEADLINE_UTC||null,operationWindowMs,minimumRemainingBeforeLaunchMs:180000,clock:'monotonic elapsed after one workflow UTC admission',purpose:'Predeclared orchestration limit, with workflow cleanup/upload reserve; no inner deadline change'};
write(path.join(OUT,'summary.json'),result);fs.copyFileSync(__filename,path.join(OUT,'collector.cjs'));
function seeds(kind){return {'salah_widget:config:v1':({valid:'{"v":1,"lat":12,"lon":34,"label":"fixture-user-setting","method":"4","savedAt":42}',malformed:'  { not-json: "preserve\\u0000 literal"\n',absent:null})[kind],
 '__sw_probe__':'R0017 untouched probe Ω\nraw','unrelated-origin-key':'retained exactly ☃\n{"spaces":  2}'};}
function span(s,a,b){if(s.split(a).length!==2||s.split(b).length!==2)fail('Non-unique controlled ingress extraction anchor');const start=s.indexOf(a),end=s.indexOf(b,start);if(end<start)fail('Reversed extraction anchors');return s.slice(start,end);}
let source,declared,ingress;
function identify(){
 if(git('rev-parse','HEAD')!==EXPECTED)fail('Candidate HEAD differs from reviewed payload');
 if(git('status','--porcelain','--untracked-files=no'))fail('Candidate has tracked changes');
 const names=git('ls-files','--','index.html','offline.html','builder.html','config.js','README.md','docs/state-contracts/R0017.md','real-sky','vendor','src/native','moon','tests/smoke.html','tests/widget-fixture.html','tests/native-script-contract.js','tests/r0017-*').split('\n').filter(p=>/^(index\.html|offline\.html|builder\.html|config\.js|README\.md)$/.test(p)||p==='docs/state-contracts/R0017.md'||p.startsWith('real-sky/')||p.startsWith('vendor/')||p.startsWith('src/native/')||(p.startsWith('moon/')&&!/^moon\/(src|tests)\//.test(p))||/^tests\/(smoke\.html|widget-fixture\.html|native-script-contract\.js|r0017-[^/]+)$/.test(p)).sort();
 const files={};for(const name of names){const b=fs.readFileSync(path.join(ROOT,name));files[name]={bytes:b.length,sha256:sha(b)};}
 const canonical=Object.entries(files).map(([p,v])=>v.sha256+'  '+p+'\n').join('');
 source={commit:EXPECTED,tree:git('rev-parse','HEAD^{tree}'),algorithm:'SHA256 of sorted sha256 + two spaces + POSIX path + LF',treeSha256:sha(canonical),files};
 const smoke=fs.readFileSync(path.join(ROOT,'tests/smoke.html'),'utf8');
 const m=smoke.match(/const CASES=(\[[\s\S]*?\n\]);/);if(!m)fail('Missing exact CASES declaration');declared=JSON.parse(m[1]);
 if(declared.length!==30||declared.reduce((n,x)=>n+x[1],0)!==141)fail('Reviewed 30/141 denominator changed');
 for(const literal of ['),4000,name)','loadUntil(hash,8000,ready)', '),3000,"PBR moon image decode"'])if(!smoke.includes(literal))fail('Original bound anchor changed: '+literal);
 const wrapper=fs.readFileSync(path.join(ROOT,'tests/widget-fixture.html'),'utf8');
 const declarations=span(wrapper,'  const nativeFetch=window.fetch.bind(window),NativeDate=window.Date;','  // Serialized as a separate, labeled classic script');
 const hooks=span(wrapper,'    // These hooks must exist before DOM parsing','    const doc=new DOMParser()');
 ingress={declarations,hooks,provenance:{source:'tests/widget-fixture.html',sourceSha256:files['tests/widget-fixture.html'].sha256,declarationsSha256:sha(declarations),hooksSha256:sha(hooks)}};
 write(path.join(OUT,'source-identity.json'),source);write(path.join(OUT,'denominator.json'),declared);write(path.join(OUT,'controlled-ingress-provenance.json'),ingress.provenance);
 result.source={commit:source.commit,tree:source.tree,treeSha256:source.treeSha256};
}
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.cjs':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.wasm':'application/wasm','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.dat':'application/octet-stream','.bin':'application/octet-stream'};
async function server(){
 const rootReal=fs.realpathSync(ROOT);
 const s=http.createServer((req,res)=>{
  let u,rel,p;try{u=new URL(req.url,'http://127.0.0.1');rel=decodeURIComponent(u.pathname).replace(/^\/+/, '')||'index.html';p=fs.realpathSync(path.join(rootReal,rel));
   if(!p.toLowerCase().startsWith((rootReal+path.sep).toLowerCase()))throw Error('Outside payload');
   if(!fs.statSync(p).isFile()||!['GET','HEAD'].includes(req.method))throw Error('Not a file GET');
  }catch(e){res.writeHead(404);res.end('Not found');record(path.join(OUT,'static-server.jsonl'),{utc:new Date().toISOString(),url:req.url,status:404});return;}
  const stat=fs.statSync(p);res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream','Content-Length':stat.size,'Cache-Control':'no-cache'});
  record(path.join(OUT,'static-server.jsonl'),{utc:new Date().toISOString(),url:req.url,status:200,path:rel,bytes:stat.size});
  if(req.method==='HEAD')res.end();else{const f=fs.createReadStream(p);f.on('error',e=>res.destroy(e));res.on('close',()=>f.destroy());f.pipe(res);}
 });
 await new Promise((resolve,reject)=>{s.once('error',reject);s.listen(0,'127.0.0.1',resolve);});
 return {origin:'http://127.0.0.1:'+s.address().port+'/',close:()=>new Promise(resolve=>{s.closeAllConnections();s.close(resolve);})};
}
function locate(engine){
 const candidates=engine==='chromium'?[process.env.ProgramFiles&&path.join(process.env.ProgramFiles,'Google/Chrome/Application/chrome.exe'),process.env['ProgramFiles(x86)']&&path.join(process.env['ProgramFiles(x86)'],'Google/Chrome/Application/chrome.exe')]:[process.env.ProgramFiles&&path.join(process.env.ProgramFiles,'Mozilla Firefox/firefox.exe')];
 const binary=candidates.find(p=>p&&fs.existsSync(p));
 const driverDir=process.env[engine==='chromium'?'CHROMEWEBDRIVER':'GECKOWEBDRIVER'];
 const driver=driverDir&&path.join(driverDir,engine==='chromium'?'chromedriver.exe':'geckodriver.exe');
 if(!binary||!driver||!fs.existsSync(driver))fail('Image-installed executable unavailable for '+engine+'; no install fallback is permitted');
 return {binary,driver,browserSha256:sha(fs.readFileSync(binary)),driverSha256:sha(fs.readFileSync(driver)),driverVersion:execFileSync(driver,['--version'],{encoding:'utf8',windowsHide:true,timeout:10000}).trim()};
}
async function request(base,method,route,body,timeout=15000,cleanup=false){
 if(!cleanup)timeout=operationTimeout(timeout);
 const r=await fetch(base+route,{method,headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(timeout)});
 const text=await r.text();let j;try{j=JSON.parse(text);}catch{throw Error('Driver returned non-JSON HTTP '+r.status+': '+text.slice(0,300));}
 if(!r.ok||j.value?.error)throw Error('WebDriver '+route+': '+(j.value?.error||r.status)+' '+(j.value?.message||''));return j.value;
}
class BiDi{
 constructor(url,file,onEvent){this.seq=0;this.pending=new Map();this.file=file;this.onEvent=onEvent;
  const u=new URL(url);if(u.protocol!=='ws:'||!['127.0.0.1','localhost','[::1]'].includes(u.hostname))fail('Non-loopback BiDi endpoint');
  this.ws=new WebSocket(url);this.opened=new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('BiDi connection deadline')),15000);this.ws.addEventListener('open',()=>{clearTimeout(timer);resolve();},{once:true});this.ws.addEventListener('error',()=>{clearTimeout(timer);reject(Error('BiDi connection failed'));},{once:true});});
  this.ws.addEventListener('message',e=>{let v;try{v=JSON.parse(e.data);}catch{return;}
   if(v.id){const p=this.pending.get(v.id);if(!p)return;clearTimeout(p.timer);this.pending.delete(v.id);v.type==='error'?p.reject(Error('BiDi '+v.error+': '+v.message)):p.resolve(v.result);}
   else if(v.method){Promise.resolve(this.onEvent(v)).catch(err=>record(this.file,{collectorEventError:String(err),method:v.method}));}
  });
  this.ws.addEventListener('close',()=>{for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(Error('BiDi closed'));}this.pending.clear();});
 }
 async call(method,params={}){await this.opened;const id=++this.seq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('BiDi command deadline: '+method));},operationTimeout(15000));this.pending.set(id,{resolve,reject,timer});this.ws.send(JSON.stringify({id,method,params}));});}
 close(){this.ws.close();}
}
function preload(seed,origin,ordinary){
 return `()=>{if(location.origin!==${JSON.stringify(new URL(origin).origin)})return;
 const isTop=window===window.top, docKey=crypto.randomUUID(), real=window.localStorage;
 const seed=${JSON.stringify(seed)}, keys=Object.keys(seed), snapshot=()=>Object.fromEntries(keys.map(k=>[k,real.getItem(k)]));
 if(isTop){const fresh=snapshot();if(Object.values(fresh).some(v=>v!==null))throw Error('Disposable profile already has seeded keys');
   for(const [k,v] of Object.entries(seed))if(v!==null)real.setItem(k,v);
   window.__r0017Recorder={schema:'r0017-storage/v1',seed,fresh,before:snapshot(),snapshot,entries:[],preferenceAtPreload:matchMedia('(prefers-reduced-motion: reduce)').matches,
     receive(text){this.entries.push(JSON.parse(text));}};
 }
 const emit=(event,extra={})=>{const row={event,docKey,url:location.href,isTop,...extra};try{window.top.__r0017Recorder.receive(JSON.stringify(row));}catch{}};
 let accesses=0;emit('document-preload',{raw:snapshot(),preference:matchMedia('(prefers-reduced-motion: reduce)').matches,dpr:devicePixelRatio});
 Object.defineProperty(window,'localStorage',{configurable:true,enumerable:true,get(){accesses++;emit('real-origin-storage-get',{accesses});return real;}});
 ${ordinary?`if(isTop){${ingress.declarations}
 report.sourceSha256=${JSON.stringify(source.files['index.html'].sha256)};
 ${ingress.hooks}
 report.documentMode='actual-public-root-controlled-ingress';
 document.addEventListener('DOMContentLoaded',()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=='function')throw Error('Actual public widget did not initialize');if(!report.error)report.state='ready';}catch(e){failure(e);}},{once:true});
 }`:''}
 }`;
}
const SNAPSHOT=`return (()=>{const copy=x=>x==null?null:JSON.parse(JSON.stringify(x));const safe=f=>{try{return f();}catch(e){return {captureError:String(e)};}};const r=window.__r0017Recorder;
 const frame=document.querySelector('#w'),w=frame?.contentWindow;let child=null;try{if(w){const rect=frame.getBoundingClientRect(),card=w.document.querySelector('.c'),p=w.document.querySelector('.mphoto');child={url:w.location.href,fixture:copy(w.__widgetFixture),qa:typeof w.qaState==='function'?copy(w.qaState()):null,preference:w.matchMedia('(prefers-reduced-motion: reduce)').matches,dpr:w.devicePixelRatio,frameRect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},visible:rect.left>=0&&rect.top>=0&&rect.right<=innerWidth&&rect.bottom<=innerHeight,card:card?{width:card.getBoundingClientRect().width,height:card.getBoundingClientRect().height}:null,photoBytes:(p?.getAttribute('href')||'').length};}}catch(e){child={error:String(e)};}
 const box=e=>{if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x,y:b.y,left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height};};
 return {url:location.href,readyState:document.readyState,userAgent:navigator.userAgent,platform:navigator.platform,preference:matchMedia('(prefers-reduced-motion: reduce)').matches,dpr:devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},visibility:document.visibilityState,
 smoke:safe(()=>copy(window.__smoke)),summary:document.querySelector('#sum')?.textContent??null,assertionLog:document.querySelector('#out')?.textContent??null,
 progress:typeof cases!=='undefined'?copy(cases):null,attempts:typeof attempts!=='undefined'?copy(attempts):null,
 fixture:safe(()=>copy(window.__widgetFixture)),qa:typeof window.qaState==='function'?safe(()=>copy(window.qaState())):null,model:typeof window.model==='function'?safe(()=>copy(window.model())):null,
 storage:r?safe(()=>({seed:r.seed,fresh:r.fresh,before:r.before,after:r.snapshot(),entries:r.entries,preferenceAtPreload:r.preferenceAtPreload})):null,
 card:box(document.querySelector('.c')),footer:box(document.querySelector('.c > .d')),countdown:document.querySelector('.panel .left')?.textContent??null,
 selectorCounts:{card:document.querySelectorAll('.c').length,footer:document.querySelectorAll('.c > .d').length,countdown:document.querySelectorAll('.panel .left').length,gregorianButton:document.querySelectorAll('#ceDateButton').length,hijriButton:document.querySelectorAll('#ahDateButton').length},
 children:child,resourceTimings:performance.getEntriesByType('resource').map(x=>({name:x.name,initiatorType:x.initiatorType,duration:x.duration,transferSize:x.transferSize})),
 observerAbsent:!window.__SalahSkyObserver,clockNow:Date.now(),documentMode:window.__widgetFixture?.documentMode??null};})();`;
const PROGRESS=`return (()=>{const fr=document.querySelector('#w'),w=fr?.contentWindow;let child=null;try{if(w){const r=fr.getBoundingClientRect();child={attempt:w.__widgetFixture?.attempt,documentId:w.__widgetFixture?.documentId,sourceSha256:w.__widgetFixture?.sourceSha256,hash:w.__widgetFixture?.hash,state:w.__widgetFixture?.state,error:w.__widgetFixture?.error,preference:w.matchMedia('(prefers-reduced-motion: reduce)').matches,dpr:w.devicePixelRatio,visible:r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,width:r.width,height:r.height,photoBytes:(w.document.querySelector('.mphoto')?.getAttribute('href')||'').length};}}catch(e){}return {done:!!window.__smoke,status:window.__smoke?.status??null,summary:document.querySelector('#sum')?.textContent??null,cases:typeof cases!=='undefined'?cases.map(x=>({name:x.name,state:x.state,assertions:x.assertions})):null,child};})();`;
const ORDINARY_READY=`return (()=>{const f=window.__widgetFixture,q=typeof qaState==='function'?qaState():null;return !!(f&&f.state==='ready'&&q?.cache?.prayerLoaded&&q.render.currentKey&&q.render.nextKey&&f.ledger.some(x=>x.url.includes('/v1/timings/08-09-2026')&&x.jsonReads>0));})();`;
function urlEvidence(value){if(typeof value==='string'&&value.startsWith('data:'))return {scheme:'data',metadata:value.slice(0,value.indexOf(',')<0?80:value.indexOf(',')),utf8Bytes:Buffer.byteLength(value),sha256:sha(value)};return value;}
function networkRecord(v){const p=v.params||{},q=p.request||{},r=p.response||{};return {utc:new Date().toISOString(),method:v.method,context:p.context??null,navigation:p.navigation??null,timestamp:p.timestamp??null,isBlocked:p.isBlocked??false,request:{id:q.request,url:urlEvidence(q.url),method:q.method,timings:q.timings},response:{url:urlEvidence(r.url),status:r.status,statusText:r.statusText,mimeType:r.mimeType,fromCache:r.fromCache,bytesReceived:r.bytesReceived},errorText:p.errorText??null};}
async function screenshot(session,file,element){try{
 let b;if(element){const e=await session.wd('POST','/element',{using:'css selector',value:element});const id=e['element-6066-11e4-a52e-4f735466cecf'];b=await session.wd('GET','/element/'+id+'/screenshot');}
 else b=await session.wd('GET','/screenshot');fs.writeFileSync(file,Buffer.from(b,'base64'));return {file:path.basename(file),sha256:sha(fs.readFileSync(file)),kind:element?'element':'viewport'};
 }catch(e){return {file:path.basename(file),error:String(e)};}}
// Capture only descendants of the exact owned PIDs; creation times prevent killing reused PIDs.
function processTree(pids){
 const ids=[...new Set(pids.filter(n=>Number.isInteger(n)&&n>0))];if(!ids.length)return [];
 const script="$ErrorActionPreference='Stop'; $all=@(Get-CimInstance Win32_Process); $ids=[System.Collections.Generic.HashSet[uint32]]::new(); @("+ids.join(',')+") | ForEach-Object { [void]$ids.Add([uint32]$_) }; do { $changed=$false; foreach($p in $all){if($ids.Contains([uint32]$p.ParentProcessId) -and $ids.Add([uint32]$p.ProcessId)){$changed=$true}} } while($changed); $rows=@($all | Where-Object {$ids.Contains([uint32]$_.ProcessId)} | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;Name=$_.Name;ExecutablePath=$_.ExecutablePath;CreationDate=$_.CreationDate.ToUniversalTime().ToString('o')} }); ConvertTo-Json -InputObject $rows -Compress";
 const rows=JSON.parse(execFileSync('powershell.exe',['-NoLogo','-NoProfile','-NonInteractive','-Command',script],{encoding:'utf8',windowsHide:true,timeout:5000}));
 if(!Array.isArray(rows)||rows.some(p=>!Number.isInteger(p.ProcessId)||typeof p.CreationDate!=='string'))fail('Invalid owned-process query');return rows;
}
function sameProcess(a,b){return a.ProcessId===b.ProcessId&&a.CreationDate===b.CreationDate;}
function processBirth(value){const m=/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,7}))?(?:Z|\+00:00)$/.exec(value||'');return m?m[1]+'.'+(m[2]||'').padEnd(7,'0'):null;}
function extendOwned(known,observed){
 let added=true;while(added){added=false;for(const p of observed){if(known.some(k=>sameProcess(k,p)))continue;const parent=observed.find(q=>q.ProcessId===p.ParentProcessId);if(parent&&known.some(k=>sameProcess(k,parent))&&processBirth(p.CreationDate)!==null&&processBirth(parent.CreationDate)!==null&&processBirth(p.CreationDate)>=processBirth(parent.CreationDate)){known.push(p);added=true;}}}return known;
}
async function closeOwnedSession(session,row,base){
 if(row.cleanup)return row.cleanup;
 const c=row.cleanup={startedUtc:new Date().toISOString(),verifiedExited:false,ok:false,queries:[],kills:[],errors:[],profileRoot:session.profile};
 const known=[...(session.ownedProcesses||[])],observedIdentities=[],roots=[session.child?.pid,row.browserPid].filter(n=>Number.isInteger(n)&&n>0);
 c.noProcessStarted=roots.length===0&&!session.sessionCreateAttempted;
 const query=stage=>{try{const observed=processTree([...roots,...known.map(p=>p.ProcessId),...observedIdentities.map(p=>p.ProcessId)]);for(const p of observed)if(!observedIdentities.some(k=>sameProcess(k,p)))observedIdentities.push(p);c.queries.push({stage,observed});return observed;}catch(e){c.errors.push({stage,error:String(e)});return null;}};
 try{
  const before=query('before-delete');if(before)extendOwned(known,before);
  if(session.id){try{await request(base,'DELETE','/session/'+session.id,undefined,10000,true);c.deleteSession={status:'SUCCEEDED'};}catch(e){c.deleteSession={status:'FAILED',error:String(e)};}}
  else c.deleteSession={status:'NOT_AVAILABLE',reason:'No session id was returned'};
  if(session.bidi)try{session.bidi.close();}catch(e){c.errors.push({stage:'bidi-close',error:String(e)});}
  const afterDelete=query('after-delete');if(afterDelete)extendOwned(known,afterDelete);
  // Never terminate a PID merely because a former owned process once used it.
  const killable=afterDelete?afterDelete.filter(p=>known.some(k=>sameProcess(k,p))):[];
  if(killable.length){const args=killable.flatMap(p=>['/PID',String(p.ProcessId)]).concat(['/F']);try{const output=execFileSync('taskkill',args,{encoding:'utf8',windowsHide:true,timeout:10000});c.kills.push({args,status:'SUCCEEDED',output});}catch(e){c.kills.push({args,status:'FAILED',exitCode:e.status??null,error:String(e),stdout:String(e.stdout||''),stderr:String(e.stderr||'')});}}
  let afterKill=query('after-kill');const exitDeadline=performance.now()+5000;while(afterKill&&afterKill.some(p=>known.some(k=>sameProcess(k,p)))&&performance.now()<exitDeadline){await delay(100);afterKill=query('exit-verification');}c.ownedProcesses=known;c.remaining=afterKill?afterKill.filter(p=>known.some(k=>sameProcess(k,p))):null;
  const browserKnown=!session.sessionCreateAttempted||(Number.isInteger(row.browserPid)&&known.some(p=>p.ProcessId===row.browserPid));
  const driverKnown=!roots.length||known.some(p=>p.ProcessId===session.child?.pid)||(!session.sessionCreateAttempted&&before?.every(p=>p.ProcessId!==session.child?.pid));
  c.scopeKnown=browserKnown&&driverKnown;
  c.unresolvedObserved=afterKill?afterKill.filter(p=>!known.some(k=>sameProcess(k,p))&&!known.some(k=>k.ProcessId===p.ProcessId&&k.CreationDate!==p.CreationDate)):null;
  c.verifiedExited=c.noProcessStarted?null:!!before&&!!afterDelete&&!!afterKill&&c.scopeKnown&&c.remaining.length===0&&c.unresolvedObserved.length===0;
  if((c.noProcessStarted||c.verifiedExited)&&session.profile){try{fs.rmSync(session.profile,{recursive:true,force:true,maxRetries:2,retryDelay:100});c.profileCleanup={status:'REMOVED',path:session.profile,absent:!fs.existsSync(session.profile)};}catch(e){c.profileCleanup={status:'FAILED',path:session.profile,error:String(e)};}}
  else c.profileCleanup={status:'RETAINED',reason:'Owned process exit not established'};
  c.ok=(c.noProcessStarted||c.verifiedExited===true)&&(!session.profile||c.profileCleanup?.absent===true);
 }catch(e){c.errors.push({stage:'cleanup',error:String(e.stack||e)});c.ok=false;}
 c.finishedUtc=new Date().toISOString();if(!c.ok)result.stopLaunches={kind:'cleanup-unverified',case:row.name,receipt:row.name+'/result.json',reason:'No further browser launch after uncertain owned-process/profile cleanup'};
 return c;
}
function notAttempted(p,reason,reference){
 if(result.cases.some(r=>r.name===p.name))return;
 const dir=path.join(OUT,p.name),row={schema:'r0017-windows-case/v1',runId,...p,storageKind:p.ordinary?'fresh-absent-public-profile':p.storage,status:'NOT_ATTEMPTED',qualification:'PARTIAL',payloadCommit:EXPECTED,sourceTreeSha256:source?.treeSha256??null,startedUtc:null,finishedUtc:new Date().toISOString(),executionStarted:false,reason,reference,checks:{},screenshots:[],smoke:null};
 fs.mkdirSync(dir,{recursive:true});result.cases.push(row);write(path.join(dir,'result.json'),row);write(path.join(dir,'smoke.json'),null);write(path.join(OUT,'summary.json'),result);
}
function launchBlock(p){
 if(result.stopLaunches)return result.stopLaunches;
 if(result.engineSetupBlocks[p.engine])return result.engineSetupBlocks[p.engine];
 if(remainingBudgetMs()<180000){result.stopLaunches={kind:'orchestration-budget',reason:'Less than the predeclared 180-second launch reserve remains',receipt:'summary.json#budget'};return result.stopLaunches;}return null;
}
async function startSession(engine,preference,viewport,dpr,row,dir,origin){
 const installed=locate(engine);row.installed=installed;result.inventory[engine]={status:'AVAILABLE',...installed};const port=await freePort(),base='http://127.0.0.1:'+port;
 const profile=fs.mkdtempSync(path.join(process.env.RUNNER_TEMP||os.tmpdir(),'r0017-'+engine+'-'));row.profileRoot=profile;
 const driverArgs=engine==='chromium'?['--port='+port,'--allowed-ips=127.0.0.1']:['--host','127.0.0.1','--port',String(port),'--log','info','--profile-root',profile];
 const child=spawn(installed.driver,driverArgs,{windowsHide:true,stdio:['ignore',fs.openSync(path.join(dir,'driver.stdout.log'),'a'),fs.openSync(path.join(dir,'driver.stderr.log'),'a')]});
 row.driverPid=child.pid;row.driverArguments=driverArgs;let launchError=null;child.on('error',e=>{launchError=e;});
 const session={child,profile,bidi:null,id:null,sessionCreateAttempted:false,ownedProcesses:[],async close(){return closeOwnedSession(this,row,base);}};
 try{
 const initialTree=processTree([child.pid]);row.driverProcess=initialTree.find(p=>p.ProcessId===child.pid);if(!row.driverProcess)fail('Owned driver process identity unavailable');session.ownedProcesses=[row.driverProcess];extendOwned(session.ownedProcesses,initialTree);
 const until=Date.now()+20000;let ready=false;while(Date.now()<until){if(launchError)throw launchError;if(child.exitCode!==null)fail('Driver exited '+child.exitCode);try{const s=await request(base,'GET','/status',undefined,1000);if(s.ready){ready=true;break;}}catch{}await delay(100);}if(!ready)fail('Driver did not become ready');
 const options=engine==='chromium'?{'goog:chromeOptions':{binary:installed.binary,args:['--headless=new','--user-data-dir='+profile,'--no-first-run','--no-default-browser-check']}}:{'moz:firefoxOptions':{binary:installed.binary,args:['-headless'],prefs:{'ui.prefersReducedMotion':preference==='reduce'?1:0,'layout.css.devPixelsPerPx':String(dpr)}}};
 session.sessionCreateAttempted=true;
 const value=await request(base,'POST','/session',{capabilities:{alwaysMatch:{browserName:engine==='chromium'?'chrome':'firefox',platformName:'windows',webSocketUrl:true,acceptInsecureCerts:false,pageLoadStrategy:'none',...options}}},45000);
 session.id=value.sessionId;row.capabilities=value.capabilities;row.browserPid=value.capabilities['goog:processID']||value.capabilities['moz:processID']||null;
 const currentOwned=processTree([child.pid,row.browserPid]);
 if(!currentOwned.some(p=>sameProcess(p,row.driverProcess)))fail('Owned driver identity disappeared or changed during session creation');
 extendOwned(session.ownedProcesses,currentOwned);
 row.nativeProcess=currentOwned.find(p=>p.ProcessId===row.browserPid&&session.ownedProcesses.some(k=>sameProcess(k,p)))??null;
 row.actualProfile=engine==='firefox'?value.capabilities['moz:profile']??null:profile;
 if(engine==='firefox'&&(!row.actualProfile||!path.resolve(row.actualProfile).toLowerCase().startsWith((path.resolve(profile)+path.sep).toLowerCase())))fail('Firefox profile is not inside the session-owned profile root');
 if(!Number.isInteger(row.browserPid)||!row.nativeProcess)fail('Actual browser process identity unavailable');
 if(!session.id||!/windows/i.test(value.capabilities.platformName||''))fail('Missing actual Windows session capability');
 if(!value.capabilities.webSocketUrl)fail('Installed driver did not provide required BiDi endpoint');
 session.wd=(method,route,body)=>request(base,method,'/session/'+session.id+route,body);
 const np=path.join(dir,'network.jsonl'),cp=path.join(dir,'console.jsonl');row.network={allowed:0,allowedEmbedded:0,blocked:0,interceptErrors:[],blockedURLs:[]};
 session.bidi=new BiDi(value.capabilities.webSocketUrl,path.join(dir,'protocol-errors.jsonl'),async v=>{
  if(v.method==='log.entryAdded'){record(cp,{utc:new Date().toISOString(),...v.params});return;}
  if(v.method.startsWith('network.')){record(np,networkRecord(v));const p=v.params,q=p.request;
   if(v.method==='network.beforeRequestSent'&&p.isBlocked){let allowed=false;try{const u=new URL(q.url),o=new URL(origin);allowed=u.protocol==='blob:'?u.origin===o.origin:u.protocol==='data:'?/^data:image\/(?:png|jpe?g|gif|webp|svg\+xml)(?:[;,])/i.test(q.url):u.origin===o.origin&&u.pathname.startsWith(o.pathname);}catch{}
    try{if(allowed){row.network.allowed++;if(/^(blob|data):/.test(q.url))row.network.allowedEmbedded++;await session.bidi.call('network.continueRequest',{request:q.request});}else{row.network.blocked++;row.network.blockedURLs.push(urlEvidence(q.url));await session.bidi.call('network.failRequest',{request:q.request});}}
    catch(e){row.network.interceptErrors.push(String(e));}
   }
  }else record(path.join(dir,'lifecycle.jsonl'),v);
 });
 await session.bidi.opened;
 await session.bidi.call('session.subscribe',{events:['log.entryAdded','network.beforeRequestSent','network.responseCompleted','network.fetchError','browsingContext.contextCreated','browsingContext.contextDestroyed']});
 await session.bidi.call('network.addIntercept',{phases:['beforeRequestSent']});
 const tree=await session.bidi.call('browsingContext.getTree',{});session.context=tree.contexts[0]?.context;if(!session.context)fail('No top browsing context');
 await session.bidi.call('browsingContext.setViewport',{context:session.context,viewport,devicePixelRatio:dpr});
 row.preference={requested:preference,mechanism:engine==='chromium'?'ChromeDriver CDP Emulation.setEmulatedMedia':'Firefox ui.prefersReducedMotion profile preference',osAccessibilitySettingChanged:false};
 if(engine==='chromium')await session.wd('POST','/goog/cdp/execute',{cmd:'Emulation.setEmulatedMedia',params:{features:[{name:'prefers-reduced-motion',value:preference}]}});
 await session.wd('POST','/timeouts',{script:10000,pageLoad:30000,implicit:0});
 session.eval=(script,cleanup=false)=>request(base,'POST','/session/'+session.id+'/execute/sync',{script,args:[]},15000,cleanup);
 return session;
 }catch(e){await session.close();throw e;}
}
async function publicReadback(){const rows=[];for(const file of ['index.html','config.js','tests/smoke.html','tests/widget-fixture.html','tests/native-script-contract.js','real-sky/native-sky.css','real-sky/native-sky.js','real-sky/native-first-paint.mjs','README.md','docs/state-contracts/R0017.md']){
 const r=await fetch(new URL(file,PUBLIC),{redirect:'error',signal:AbortSignal.timeout(operationTimeout(20000))}),b=Buffer.from(await r.arrayBuffer());const row={file,retrievedUtc:new Date().toISOString(),url:r.url,status:r.status,bytes:b.length,sha256:sha(b),expectedSha256:source.files[file]?.sha256??null,etag:r.headers.get('etag'),lastModified:r.headers.get('last-modified')};row.matches=r.ok&&row.sha256===row.expectedSha256;rows.push(row);write(path.join(OUT,'public-source-readback.json'),rows);if(!row.matches)fail('Public source mismatch: '+file);}
 return rows;
}
// BEGIN negative accounting
function negativeAccounting(smoke,mode,declared){
 const r=smoke?.required,c=r?.cases,attempts=smoke?.fixture?.attempts;
 if(!['reject','hang','bootstrap-error'].includes(mode)||!Array.isArray(c)||c.length!==30||!Array.isArray(attempts)||attempts.length!==1)return false;
 const bootstrap=mode==='bootstrap-error',reason=bootstrap?'Controlled fixture bootstrap failure before widget parsing':'required scene readiness deadline exceeded';
 return r.total===30&&r.executed===3&&r.failed===0&&smoke.pass===26&&smoke.fail===(bootstrap?1:0)&&smoke.skip===1&&
   same(r.missing,declared.slice(3).map(x=>x[0]))&&c.every((x,i)=>x.name===declared[i][0]&&x.expected===declared[i][1]&&
     (i<3?x.state==='executed'&&x.assertions===x.expected&&x.reason===null:
      i===3?x.state==='missing'&&x.assertions===0&&x.reason===reason:
      x.state==='pending'&&x.assertions===0&&x.reason===null))&&attempts[0].reason===reason;
}
// END negative accounting
function checkCommon(row,s,viewport,dpr,seed){const c=row.checks;
 c.windowsProcess=process.platform==='win32'&&/windows/i.test(row.capabilities?.platformName||'')&&row.nativeProcess?.ProcessId===row.browserPid;
 c.viewportAndDpr=s.viewport?.width===viewport.width&&s.viewport?.height===viewport.height&&s.dpr===dpr;
 c.preference=s.preference===(row.preference.requested==='reduce');
 c.storageSeedInstalled=!!s.storage&&same(s.storage.before,seed);
 c.rawOriginBytesPreserved=!!s.storage&&same(s.storage.after,seed);
 c.noRealOriginGetterUse=!!s.storage&&Array.isArray(s.storage.entries)&&!s.storage.entries.some(x=>x.event==='real-origin-storage-get');
 c.networkInterceptionsClean=row.network?.interceptErrors.length===0;
 c.noUnexpectedNetwork=row.network?.blockedURLs.every(u=>/^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(u)||u==='https://theislampill.github.io/favicon.ico');
}
async function collect(engine,mode,preference,storage,ordinary,origin){
 const name=[engine,ordinary?'public-ordinary':mode,preference,storage].join('-'),dir=path.join(OUT,name);fs.mkdirSync(dir,{recursive:true});
 const row={schema:'r0017-windows-case/v1',runId,name,engine,mode,storageKind:ordinary?'fresh-absent-public-profile':storage,ordinary,startedUtc:new Date().toISOString(),status:'STARTED',qualification:'PARTIAL',payloadCommit:EXPECTED,sourceTreeSha256:source.treeSha256,checks:{},screenshots:[],smoke:null};result.cases.push(row);write(path.join(OUT,'summary.json'),result);write(path.join(dir,'result.json'),row);
 if(ordinary)row.sourceHashProvenance={kind:'expected pinned payload plus separate public response readback',assignedFixtureHashIsExpected:true,browserMainResponseHashMeasured:false,readbackFile:'public-source-readback.json'};
 const seed=ordinary?Object.fromEntries(Object.keys(seeds('absent')).map(k=>[k,null])):seeds(storage),viewport=ordinary?{width:375,height:800}:{width:1100,height:900},dpr=ordinary?2:1;
 let session;const started=Date.now();row.stage='setup';row.executionStarted=false;
 try{
 session=await startSession(engine,preference,viewport,dpr,row,dir,origin);
 const init=preload(seed,origin,ordinary);row.preloadSha256=sha(init);fs.writeFileSync(path.join(dir,'preload.js'),init+'\n');
 await session.bidi.call('script.addPreloadScript',{functionDeclaration:init});
 row.url=ordinary?new URL('?mode=healthy&run='+encodeURIComponent(runId)+'&attempt=1#lat=24.47&lon=39.61&label=Madinah&method=4&school=0&tz=Asia/Riyadh&qa=1',origin).href:new URL('tests/smoke.html?fixture='+encodeURIComponent(mode),origin).href;
 if(remainingBudgetMs()<150000){const e=Error('Insufficient collector budget for unchanged observation limit and final capture');e.code='R0017_BUDGET_EXHAUSTED';throw e;}
 row.stage='navigation';row.executionStarted=true;
 await session.wd('POST','/url',{url:row.url});row.stage='observation';
 if(ordinary){
  const until=Date.now()+8000;let ready=false;while(Date.now()<until){if(await session.eval(ORDINARY_READY)){ready=true;break;}await delay(150);}row.ordinaryReadyWithinOriginal8000ms=ready;
 }else{
  const until=Date.now()+120000,captured=new Set();let done=false,last='';
  while(Date.now()<until){const p=await session.eval(PROGRESS);const key=JSON.stringify(p);if(key!==last){record(path.join(dir,'progress.jsonl'),{elapsedMs:Date.now()-started,...p});last=key;}
   const f=p.child;if(f?.visible&&f.width===325&&f.height===530&&f.photoBytes>50&&!captured.has(f.attempt)){captured.add(f.attempt);row.screenshots.push({...await screenshot(session,path.join(dir,'stage-'+String(f.attempt).padStart(2,'0')+'.png')),evidence:f,elapsedMs:Date.now()-started});}
   if(p.done){done=true;break;}await delay(150);
  }row.terminalWithinCollector120000ms=done;
 }
 const s=await session.eval(SNAPSHOT);row.snapshot=s;row.smoke=s.smoke;write(path.join(dir,'smoke.json'),s.smoke);
 checkCommon(row,s,viewport,dpr,seed);
 if(!ordinary){const smoke=s.smoke,req=smoke?.required;
  row.checks.terminalInstrument=!!smoke&&row.terminalWithinCollector120000ms;
  row.checks.exactNamesAndMinima=!!req&&same(req.cases.map(x=>[x.name,x.expected]),declared);
  row.checks.everyAttemptIdentity=!!smoke&&smoke.fixture.attempts.length>0&&smoke.fixture.attempts.every(a=>a.fixture&&a.fixture.run===smoke.fixture.run&&a.fixture.attempt===a.attempt&&a.fixture.hash===a.hash&&a.fixture.mode===mode&&/^[a-f0-9-]{36}$/.test(a.fixture.documentId||'')&&(mode==='bootstrap-error'||a.fixture.sourceSha256===source.files['index.html'].sha256));
  row.checks.childPreference=!!s.children&&s.children.preference===(preference==='reduce');
  if(mode==='healthy')row.checks.fullHealthy=smoke?.status==='PASS'&&req.total===30&&req.executed===30&&req.failed===0&&req.missing.length===0&&smoke.pass===141&&smoke.fail===0&&smoke.skip===0&&req.cases.every(x=>x.state==='executed'&&x.assertions===x.expected);
  else{row.checks.expectedTerminalStatus=smoke?.status===(mode==='bootstrap-error'?'FAIL':'INCOMPLETE');
   row.checks.negativeAccounting=negativeAccounting(smoke,mode,declared);
   const a=smoke?.fixture?.attempts?.[0],f=a?.fixture;
   row.checks.negativeReachedOwnBoundary=mode==='bootstrap-error'?a?.result==='bootstrap-error'&&f?.error==='Controlled fixture bootstrap failure before widget parsing':a?.result==='timeout'&&f?.ledger.some(r=>r.url.startsWith('https://api.aladhan.com/v1/timings/')&&r.result===(mode==='reject'?'rejected':'pending')&&r.jsonReads===0);
  }
 }else{const f=s.fixture,q=s.qa,ledger=f?.ledger?.filter(r=>r.url.startsWith('https://api.aladhan.com/v1/timings/'))||[];
  row.checks.realOrdinaryEntry=s.url===row.url&&s.documentMode==='actual-public-root-controlled-ingress'&&row.ordinaryReadyWithinOriginal8000ms;
  row.checks.actualPrayerRender=q?.cache?.prayerLoaded===true&&q.render.currentKey==='Dhuhr'&&q.render.nextKey==='Asr'&&q.render.leftMin===180&&s.model?.nextTime==='15:30';
  row.checks.twoDistinctConsumedDates=['07-09-2026','08-09-2026'].every(day=>ledger.some(r=>new URL(r.url).pathname==='/v1/timings/'+day&&r.jsonReads===1&&r.result==='json-consumed'))&&ledger.length===2;
  row.checks.exactProviderQueries=ledger.every(r=>{const u=new URL(r.url);return u.searchParams.size===4&&u.searchParams.get('latitude')==='24.47'&&u.searchParams.get('longitude')==='39.61'&&u.searchParams.get('method')==='4'&&u.searchParams.get('school')==='0'&&r.attempt===1;});
  row.checks.privateClockAndStorage=!!f&&f.sourceSha256===source.files['index.html'].sha256&&f.storageIsolated&&f.clockFixed&&f.fetchIntercepted&&f.initialStorageEntries===0&&s.clockNow===Date.parse('2026-09-07T09:30:00.000Z');
  row.checks.cardDimensions=s.card?.width===325&&s.card?.height===530;
  row.checks.ordinarySelectorsUnique=Object.values(s.selectorCounts).every(n=>n===1);
  row.checks.footerInsideCard=!!s.footer&&!!s.card&&s.footer.left>=s.card.left&&s.footer.right<=s.card.right&&s.footer.bottom<=s.card.bottom&&s.footer.top>=s.card.top;
  row.screenshots.push(await screenshot(session,path.join(dir,'card.png'),'.c'));
 }
 row.screenshots.push(await screenshot(session,path.join(dir,'viewport.png')));
 row.checks.recordedScreenshot=row.screenshots.some(x=>x.sha256);
 row.status=Object.values(row.checks).every(x=>x===true)?'PHASE_CHECKS_PASSED':'PHASE_CHECKS_FAILED';
 }catch(e){row.setupFailure=row.stage==='setup';row.status=e.code==='R0017_BUDGET_EXHAUSTED'?'COLLECTOR_BUDGET_EXHAUSTED':row.setupFailure?'CAPABILITY_OR_SETUP_ERROR':'COLLECTOR_OR_ATTEMPT_ERROR';row.error=String(e.stack||e);
  if(e.code==='R0017_BUDGET_EXHAUSTED')result.stopLaunches={kind:'orchestration-budget',case:name,receipt:name+'/result.json',reason:row.error};
  else if(row.setupFailure){result.engineSetupBlocks[engine]={kind:'engine-setup',case:name,receipt:name+'/result.json',reason:row.error};if(!row.installed)result.inventory[engine]={status:'UNAVAILABLE',error:row.error,receipt:name+'/result.json'};}
 }finally{
  // Full __smoke is retained for every outcome. Null is explicit if finalization never happened.
  row.primaryOutcome={status:row.status,error:row.error??null,stage:row.stage};
  if(session){try{row.finalSnapshot=await session.eval(SNAPSHOT,true);row.smoke=row.finalSnapshot.smoke;write(path.join(dir,'smoke.json'),row.smoke);}catch(e){row.finalCaptureError=String(e);write(path.join(dir,'smoke.json'),row.smoke??null);}
   if(!row.screenshots.some(x=>x.sha256))row.screenshots.push(await screenshot(session,path.join(dir,'error.png')));
   await session.close();
  }else{write(path.join(dir,'smoke.json'),null);
   if(!row.cleanup&&!row.driverPid){row.cleanup={verifiedExited:null,processExitRequired:false,scopeKnown:true,ok:true,status:'NO_PROCESS_STARTED'};if(row.profileRoot){try{fs.rmSync(row.profileRoot,{recursive:true,force:true});row.cleanup.profileCleanup={status:'REMOVED',absent:!fs.existsSync(row.profileRoot)};row.cleanup.ok=row.cleanup.profileCleanup.absent;}catch(e){row.cleanup.ok=false;row.cleanup.error=String(e);}}}
  }
  if(!row.cleanup?.ok){result.stopLaunches={kind:'cleanup-unverified',case:name,receipt:name+'/result.json',reason:'Owned cleanup was not established'};row.status='CLEANUP_FAILED';}
  else row.checks.ownedCleanupSatisfied=true;
  row.finishedUtc=new Date().toISOString();row.elapsedMs=Date.now()-started;write(path.join(dir,'result.json'),row);write(path.join(OUT,'summary.json'),result);
 }
 console.log(name+': '+row.status);return row.status==='PHASE_CHECKS_PASSED';
}
async function main(){let srv;try{
 identify();if(process.platform!=='win32')fail('Native Windows is required; refusing to qualify on '+process.platform);
 if(typeof WebSocket!=='function'||typeof fetch!=='function')fail('Image Node lacks built-in WebSocket/fetch; no dependency install allowed');
 srv=await server();let ok=true;
 // One immutable twelve-row plan. No retries, no dropped rows, no overlap after uncertain cleanup.
 for(const p of FIRST_PHASE_PLAN.filter(p=>!p.ordinary)){
  const block=launchBlock(p);if(block){notAttempted(p,block.reason,block.receipt);ok=false;continue;}
  if(!await collect(p.engine,p.mode,p.preference,p.storage,false,srv.origin))ok=false;
 }
 const publicPlan=FIRST_PHASE_PLAN.filter(p=>p.ordinary);
 if(publicPlan.some(p=>!launchBlock(p))){
  try{result.publicReadback=await publicReadback();}
  catch(e){ok=false;result.publicReadbackError=String(e.stack||e);for(const p of publicPlan)notAttempted(p,'Required public source readback did not complete','public-source-readback.json / summary.json#publicReadbackError');}
 }
 for(const p of publicPlan){
  if(result.cases.some(r=>r.name===p.name))continue;
  const block=launchBlock(p);if(block){notAttempted(p,block.reason,block.receipt);ok=false;continue;}
  if(!await collect(p.engine,p.mode,p.preference,p.storage,true,PUBLIC))ok=false;
 }
 result.status=ok?'FIRST_PHASE_CHECKS_PASSED_NOT_CLOSURE':'FIRST_PHASE_HAS_FAILURES';process.exitCode=ok?0:1;
 }catch(e){result.status='CAPABILITY_OR_SETUP_FAILED';result.error=String(e.stack||e);process.exitCode=1;}
 finally{
  if(srv)await srv.close();
  for(const p of FIRST_PHASE_PLAN)notAttempted(p,'Run ended before this planned case could start','summary.json#error');
  result.finishedUtc=new Date().toISOString();result.recordedCount=result.cases.length;result.executedCount=result.cases.filter(r=>r.executionStarted).length;write(path.join(OUT,'summary.json'),result);
 }
}
main().catch(e=>{result.status='UNHANDLED_COLLECTOR_FAILURE';result.error=String(e.stack||e);for(const p of FIRST_PHASE_PLAN)notAttempted(p,'Unhandled collector failure prevented launch','summary.json#error');write(path.join(OUT,'summary.json'),result);process.exitCode=1;});
