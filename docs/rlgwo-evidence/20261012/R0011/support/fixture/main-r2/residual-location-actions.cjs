'use strict';
// Root-owned serial browser execution only. Importing/listing/validating does not launch a browser.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),vm=require('node:vm'),crypto=require('node:crypto');
const HERE=__dirname,T=1790942400000,KEY='salah_widget:config:v1',BASE='#lat=24.47&lon=39.61&label=Madinah&method=4';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
class ConsumerAssertion extends Error{constructor(name,detail){super(name+': '+JSON.stringify(detail));this.code='CONSUMER_ASSERTION';this.assertion=name;this.detail=detail;}}
function demand(row,name,value,detail){row.checks.push({name,passed:!!value,detail});if(!value)throw new ConsumerAssertion(name,detail);}
function replaceOne(text,from,to){assert.equal(text.split(from).length-1,1,'mutation/source anchor not unique: '+from);return text.replace(from,to);}
const mutations={
 ignoreSave:{file:'index.html',from:'const r=SalahConfig.saveLocal(cfg);',to:'const attemptedPersistence=SalahConfig.saveLocal(cfg);const r={ok:true,savedAt:Date.now()};',oracle:'session-only warning'},
 ignoreReset:{file:'index.html',from:'const r=window.SalahConfig?SalahConfig.clearLocal():{ok:false,error:"unavailable"};',to:'const attemptedReset=window.SalahConfig?SalahConfig.clearLocal():{ok:false,error:"unavailable"};const r={ok:true};',oracle:'reset-failed warning'},
 hideWarning:{file:'index.html',from:'const failed=!!_persistOutcome && (_persistOutcome.status==="session-only"||_persistOutcome.status==="reset-failed");',to:'const failed=false;',oracle:'closed warning marker'}
};
const cases=[];
function add(group,name,type,data={}){cases.push({group,name,type,...data});}
for(const container of ['top','iframe']){
 for(const deny of ['save','quota'])add('r0011',`${container}-${deny}-denied`,'saveDenied',{container,deny,closeVia:deny==='quota'?'escape':'button',acceptance:'R0011-A01',also:['R0011-A05']});
 add('r0011',`${container}-reset-denied`,'resetDenied',{container,acceptance:'R0011-A02',also:['R0011-A05']});
 for(const fault of ['getter','read','malformed','v2'])add('r0011',`${container}-read-${fault}`,'readFault',{container,fault,acceptance:'R0011-A03'});
 add('r0011',`${container}-save-recovery`,'saveRecovery',{container,acceptance:'R0011-A04'});
 for(const detect of ['held','success','failure','superseded'])add('r0011',`${container}-reset-${detect}`,'resetSuccess',{container,detect,acceptance:'R0011-A04'});
 for(const deny of ['save','quota'])add('r0011',`${container}-${deny}-denied-narrow`,'saveDenied',{container,deny,narrow:true,closeVia:deny==='quota'?'escape':'button',acceptance:'R0011-A05',also:['R0011-A01']});
 add('r0011',`${container}-reset-denied-narrow`,'resetDenied',{container,narrow:true,lookup:'search',acceptance:'R0011-A05',also:['R0011-A02']});
}
for(const mutant of ['ignoreSave','hideWarning'])add('r0011',`mutant-${mutant}`,'saveDenied',{container:'top',deny:'save',mutant,acceptance:'R0011-A07'});
add('r0011','mutant-ignoreReset','resetDenied',{container:'top',mutant:'ignoreReset',acceptance:'R0011-A07'});
class SourceServer{
 constructor(options){this.options=options;this.ref=options.sourceRef;this.cache=new Map();this.variant=null;this.binding=JSON.parse(fs.readFileSync(path.join(HERE,'source-binding.json'),'utf8'));this.fixture=fs.readFileSync(path.join(HERE,'residual-location-native.html'),'utf8');}
 raw(file){
  const admitted=this.binding.runtimeEntries[file];assert(admitted,'unadmitted runtime file '+file);
  assert.equal(fs.realpathSync(this.options.sourceRoot),fs.realpathSync(this.binding.sourceRoot),'wrong generated consumer root');
  if(!this.cache.has(file)){const target=path.resolve(this.options.sourceRoot,file);assert(target.startsWith(path.resolve(this.options.sourceRoot)+path.sep),'unsafe runtime path');const data=fs.readFileSync(target);assert.equal(data.length,admitted.bytes,'runtime length drift '+file);assert.equal(hash(data),admitted.sha256,'runtime digest drift '+file);this.cache.set(file,data);}return this.cache.get(file);
 }
 data(file){const original=this.raw(file),m=this.variant&&mutations[this.variant];return m&&m.file===file?Buffer.from(replaceOne(original.toString(),m.from,m.to)):original;}
 manifest(){const b=JSON.parse(JSON.stringify(this.binding));for(const [name,file]of[['widget','index.html'],['builder','builder.html']]){const data=this.data(file),scripts=[...data.toString().matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];b.pages[name]={sha:hash(data),attrs:scripts.map(x=>x[1]),bodiesSha256:scripts.map(x=>hash(x[2]))};}b.configSha256=hash(this.data('config.js'));b.fixtureMutation=this.variant?{name:this.variant,file:mutations[this.variant].file,baseSha256:hash(this.raw(mutations[this.variant].file)),mutatedSha256:hash(this.data(mutations[this.variant].file))}:null;return b;}
 wrapper(){const b=this.manifest();return this.fixture.replace(/  const expectedPages=.*?;\n/,`  const expectedPages=${JSON.stringify(b.pages)},expectedConfig="${b.configSha256}";\n`);}
 async start(){assert.equal(this.ref,this.binding.sourceRef,'source binding requires explicit re-preparation on different target');assert.equal(hash(this.raw('index.html')),this.binding.pages.widget.sha,'pinned root digest drift');const handler=(request,response)=>{try{const u=new URL(request.url,'http://127.0.0.1');let content,mime='text/plain; charset=utf-8';if(u.pathname==='/__parent.html'){const child=u.searchParams.get('child'),policy=u.searchParams.get('policy');assert(child&&child.startsWith(this.B+'/tests/'));let allow='';if(policy==='delegated')response.setHeader('Permissions-Policy',`geolocation=(self "${this.B}")`);if(policy==='restrictive')response.setHeader('Permissions-Policy','geolocation=()');if(policy!=='noallow')allow=' allow="geolocation"';content=`<!doctype html><html><body><iframe id="subject" src="${child.replaceAll('&','&amp;')}"${allow} style="width:325px;height:530px;border:0"></iframe></body></html>`;mime='text/html; charset=utf-8';}else if(u.pathname==='/tests/residual-location-native.html'){content=this.wrapper();mime='text/html; charset=utf-8';}else if(u.pathname==='/tests/residual-location-source-binding.json'){content=JSON.stringify(this.manifest());mime='application/json';}else{const name=decodeURIComponent(u.pathname.slice(1));if(!this.binding.runtimeFiles.includes(name))throw Error('unadmitted asset');content=this.data(name);mime=name.endsWith('.html')?'text/html; charset=utf-8':name.endsWith('.js')||name.endsWith('.mjs')?'text/javascript':name.endsWith('.json')?'application/json':name.endsWith('.wasm')?'application/wasm':name.endsWith('.png')?'image/png':name.endsWith('.webp')?'image/webp':name.endsWith('.css')?'text/css':'application/octet-stream';}response.writeHead(200,{'Content-Type':mime,'Cache-Control':'no-store'});response.end(content);}catch(error){response.writeHead(404);response.end('Owned fixture: '+error.message);}};this.servers=[http.createServer(handler),http.createServer(handler)];for(const server of this.servers)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));[this.A,this.B]=this.servers.map(server=>`http://127.0.0.1:${server.address().port}`);}
 async close(){for(const server of this.servers||[])await new Promise(resolve=>server.close(resolve));}
}
async function wait(frame,predicate,arg,ms=10000){const end=Date.now()+ms;while(Date.now()<end){if(await frame.evaluate(predicate,arg))return;await new Promise(r=>setTimeout(r,70));}throw Error('fixture observation budget exceeded');}
async function view(frame){return frame.evaluate(()=>{const f=window.__locationFixture;return {config:typeof CONFIG==='object'?JSON.parse(JSON.stringify(CONFIG)):null,form:typeof formConfig==='function'?JSON.parse(JSON.stringify(formConfig())):null,app:f.application(),report:{state:f.state,error:f.error,seedApplied:f.seedApplied,seedBytes:f.seedBytes,storageMode:f.storageMode,productionScriptBodiesPreserved:f.productionScriptBodiesPreserved,scriptCount:f.scriptCount,gpsCalls:f.gpsCalls,requests:f.requests,providerJobs:f.providerJobs,storageFaults:f.storageFaults,uiEvents:f.uiEvents,errors:f.errors,storageEvents:f.storageEvents,storage:f.rawStorage(),nativeCallbacks:f.nativeCallbacks,positionStimulus:f.positionStimulus,fonts:f.fonts,clock:f.clock},secure:isSecureContext};});}
async function snapshot(e,row,name){const s=await view(e.frame);row.snapshots[name]=s;return s;}
function configBytes(s){return s.report.storage.find(([k])=>k===KEY)?.[1]??null;}
async function create(browser,server,c,options={}){const context=await browser.newContext({viewport:{width:(options.narrow||c.narrow)?390:1000,height:(options.narrow||c.narrow)?844:900},deviceScaleFactor:1,timezoneId:options.zone||'UTC',reducedMotion:options.reduce?'reduce':'no-preference',geolocation:{latitude:52.52,longitude:13.41,accuracy:25}});await context.route('**/*',route=>{const u=new URL(route.request().url());return [server.A,server.B].includes(u.origin)?route.continue():route.abort('blockedbyclient');});if(c.type==='policy'){await context.grantPermissions(['geolocation'],{origin:server.A});await context.grantPermissions(['geolocation'],{origin:server.B});}const page=await context.newPage();const query=new URLSearchParams({storage:'native',page:c.page||'widget',seed:options.seed||'none',clock:options.clock||'fixed',gps:options.gps||c.gps||'success',copy:'success',...options.query});const origin=c.container==='iframe'||c.policy&&c.policy!=='top-level'?server.B:server.A;const fragment=options.fragment||'#local=1';const url=origin+'/tests/residual-location-native.html?'+query+fragment;let frame=page;if(c.container==='iframe'||c.policy&&c.policy!=='top-level'){await page.goto(server.A+'/__parent.html?'+new URLSearchParams({child:url,policy:c.policy||'delegated'}));await wait(page,()=>!!document.querySelector('#subject'));frame=await page.locator('#subject').elementHandle().then(h=>h.contentFrame());}else await page.goto(url);await wait(frame,()=>window.__locationFixture&&['ready','error'].includes(window.__locationFixture.state));const initial=await view(frame);assert.equal(initial.report.error,null,'fixture source/hook applicability failed');assert(initial.report.productionScriptBodiesPreserved,'actual source bodies required');assert.equal(initial.report.storageMode,'native');if(c.group==='r0011'){
  if(c.type==='readFault')await wait(frame,()=>typeof _autoDetectStatus!=='undefined'&&_autoDetectStatus==='failed'&&document.querySelector('.c').classList.contains('settings-open'));
  else await wait(frame,()=>typeof today!=='undefined'&&!!today&&typeof _loopStarted!=='undefined'&&_loopStarted);
 }return{context,page,frame,url,origin,container:c.container||'top',closeVia:c.closeVia||'button'};}
async function open(e){const wasOpen=await e.frame.locator('.c').evaluate(x=>x.classList.contains('settings-open'));if(!wasOpen)await e.frame.locator('.buckle').click();await wait(e.frame,()=>document.querySelector('.c').classList.contains('settings-open'));if(!wasOpen)await wait(e.frame,()=>document.activeElement===document.querySelector('#set-label'));}
async function close(e){if(e.closeVia==='escape')await e.frame.locator('#set-units').press('Escape');else await e.frame.locator('#setClose').click();await wait(e.frame,()=>!document.querySelector('.c').classList.contains('settings-open'));}
async function gps(e,c){if(c.page==='builder')await e.frame.locator('#geo').click();else{await open(e);await e.frame.locator('#set-pin').click();}if((c.gps||'success')!=='unsupported')await wait(e.frame,()=>window.__locationFixture.gpsCalls.length===1);await wait(e.frame,()=>!document.querySelector('#'+(typeof formConfig==='function'?'geo':'set-pin')).disabled);}
async function persist(e){await close(e);await wait(e.frame,()=>CONFIG&&CONFIG.lat!=null);}
async function reload(e,row,now=T){const u=new URL(e.url);u.searchParams.set('seed','none');u.searchParams.set('now',String(now));await e.page.goto(u.href);e.frame=e.page;await wait(e.frame,()=>window.__locationFixture&&['ready','error'].includes(window.__locationFixture.state));const s=await snapshot(e,row,'actual reload');demand(row,'native reload seed disabled',!s.report.seedApplied,s.report);demand(row,'native reload production initialized',!s.report.error,s.report);return s;}
async function capture(e,row,label){
 const file=path.join(row.out,label+'.png');await e.page.screenshot({path:file});
 const receipt={file,viewport:await e.page.viewportSize(),dpr:1,fontMode:'explicit system fallback',review:'PENDING'};
 if(await e.frame.locator('.c').count()){
  receipt.geometry=await e.frame.evaluate(()=>{
   const selectors=['.c','.h','.panel','.times','.d','.buckle','#settings','#set-status','.set-footer'];
   return Object.fromEntries(selectors.map(selector=>{const x=document.querySelector(selector);if(!x)return[selector,null];const r=x.getBoundingClientRect(),css=getComputedStyle(x);return[selector,{x:r.x,y:r.y,width:r.width,height:r.height,scrollHeight:x.scrollHeight,clientHeight:x.clientHeight,scrollWidth:x.scrollWidth,clientWidth:x.clientWidth,display:css.display,visibility:css.visibility,text:x.textContent}];}));
  });
  const card=receipt.geometry['.c'];demand(row,'native card dimensions retained',Math.abs(card.width-325)<.1&&Math.abs(card.height-530)<.1,card);
  receipt.cardFile=path.join(row.out,label+'-card.png');await e.frame.locator('.c').screenshot({path:receipt.cardFile});
 }
 for(const [selector,tag]of[['.buckle','buckle'],['#set-status','status']]){const bounds=await e.frame.locator(selector).boundingBox();if(bounds&&bounds.width>0&&bounds.height>0){const file=path.join(row.out,label+'-'+tag+'.png');await e.page.screenshot({path:file,clip:bounds});receipt[tag+'File']=file;}}
 receipt.pixelVerdict='PENDING_INDEPENDENT_REVIEW';receipt.spokenAnnouncement='NOT_OBSERVED';
 row.crops.push(receipt);
}
function sentinels(row,s){for(const key of ['salah:fixture','salahwx:fixture','unrelated:fixture'])demand(row,'unrelated key preserved: '+key,s.report.storage.find(([k])=>k===key)?.[1]==='untouched sentinel',s.report.storage);}
async function restoredOpener(e,row){
 const value=await e.frame.locator('.buckle').evaluate(b=>({name:b.getAttribute('aria-label'),title:b.title,gear:b.querySelector('.gear')?.textContent,warning:b.classList.contains('persist-warning')}));
 demand(row,'successful persistence restores normal opener',value.name==='Widget settings'&&value.title==='Widget settings'&&value.gear==='⚙'&&!value.warning,value);
}
async function keyboard(e,row){await open(e);const nodes=await e.frame.evaluateHandle(()=>[...document.querySelectorAll('#settings input,#settings select,#settings button,#settings textarea,#settings a[href]')].filter(x=>!x.disabled&&x.tabIndex>=0&&x.offsetParent!==null));const props=await nodes.getProperties();const handles=[...props.values()].map(h=>h.asElement()).filter(Boolean);assert(handles.length>1,'native focusable controls missing');await handles.at(-1).focus();await handles.at(-1).press('Tab');demand(row,'native Tab wraps first',await handles[0].evaluate(x=>document.activeElement===x));await handles[0].press('Shift+Tab');demand(row,'native Shift+Tab wraps last',await handles.at(-1).evaluate(x=>document.activeElement===x));await handles.at(-1).press('Escape');demand(row,'Escape returns exact opener',await e.frame.locator('.buckle').evaluate(x=>document.activeElement===x));row.accessibility=await e.frame.evaluate(()=>{const x=document.querySelector('#settings-persistence-status'),b=document.querySelector('.buckle');return{live:x?.getAttribute('aria-live'),role:x?.getAttribute('role'),text:x?.textContent,openerName:b?.getAttribute('aria-label'),openerTitle:b?.title,spokenAnnouncement:'NOT_OBSERVED',outsideDialog:!x?.closest('#settings'),footerLinks:[...document.querySelectorAll('#settings .set-footer a')].map(a=>({id:a.id||null,name:a.getAttribute('aria-label'),title:a.title}))};});
 demand(row,'native outside status attributes',row.accessibility.live==='polite'&&row.accessibility.role==='status'&&row.accessibility.outsideDialog,row.accessibility);
 demand(row,'native outside status contains retained outcome',/Could not save settings|Could not clear saved settings/.test(row.accessibility.text),row.accessibility.text);
 demand(row,'native opener exposes failure state',/Widget settings/.test(row.accessibility.openerName)&&/session only|could not be cleared/.test(row.accessibility.openerName)&&row.accessibility.openerName===row.accessibility.openerTitle,row.accessibility);
 demand(row,'native idless footer links remain focus controls',row.accessibility.footerLinks.length===3&&row.accessibility.footerLinks.every(a=>a.id===null&&a.name),row.accessibility.footerLinks);
 row.accessibility.nativeAriaSnapshot=await e.frame.locator('body').ariaSnapshot();
}
async function builderPayload(browser,server,c,row,platform){const e=await create(browser,server,{...c,page:'builder'},{zone:'Asia/Riyadh',query:{platform}});try{await e.frame.locator('#mode-local').click();await e.frame.locator('#method').selectOption(c.method);await e.frame.locator('#units').selectOption(c.units);await e.frame.locator('#copy').click();await e.frame.locator('#install').click();await e.frame.locator('#open').click();const value=await e.frame.evaluate(()=>({hash:hash(),cmd:installCmd(),code:document.querySelector('#code').value,preview:document.querySelector('#pv').getAttribute('src'),copies:window.__locationFixture.copyJobs,openURL:window.__locationFixture.openURLs.at(-1)}));const codeSrc=value.code.match(/\bsrc="([^"]+)"/)[1],payload=value.cmd.cmd.match(/SALAH_WIDGET_HASH='([^']*)'/)?.[1];for(const [name,v]of[['snippet',new URL(codeSrc).hash.slice(1)],['preview',new URL(value.preview,e.origin+'/builder.html').hash.slice(1)],['open',new URL(value.openURL).hash.slice(1)],['install',payload]])demand(row,'builder carried hash: '+name,v===value.hash,{v,hash:value.hash,platform});demand(row,'clipboard sink isolated',value.copies.length===2,value.copies);demand(row,'local coordinates omitted',!new URLSearchParams(value.hash).has('lat')&&!new URLSearchParams(value.hash).has('lon')&&!new URLSearchParams(value.hash).has('label'),value.hash);row.builderExports.push({platform,...value});return value.hash;}finally{await e.context.close();}}
const actions={
 async preference(browser,server,c,row){row.builderExports=[];const one=await builderPayload(browser,server,c,row,'Windows'),two=await builderPayload(browser,server,c,row,'Linux');demand(row,'Windows/Bash canonical equality',one===two,{one,two});const e=await create(browser,server,c,{zone:'Asia/Riyadh',fragment:'#'+one});try{await open(e);const s=await snapshot(e,row,'fresh widget consumer');demand(row,'selected preference',s.config.method===c.method&&s.config.units===c.units&&s.app.inputs['set-method']===c.method&&s.app.inputs['set-units']===c.units,s);await capture(e,row,'fresh-selected');}finally{await e.context.close();}},
 async generic(browser,server,c,row){const e=await create(browser,server,c,{zone:'Asia/Riyadh'});try{await open(e);const s=await snapshot(e,row,'generic local');demand(row,'generic detected 4/c',s.config.method==='4'&&s.config.units==='c',s.config);}finally{await e.context.close();}},
 async saved(browser,server,c,row){const e=await create(browser,server,c,{seed:'manual',fragment:'#local=1&method=2&units=f'});try{await open(e);const first=await snapshot(e,row,'first saved boot');demand(row,'saved London 3/c precedence',first.config.lat===51.5&&first.config.method==='3'&&first.config.units==='c',first);demand(row,'zero coarse requests',first.report.requests.filter(r=>/geojs|ipinfo/.test(r.url)).length===0,first.report.requests);const second=await reload(e,row);demand(row,'native saved bytes survive reload',configBytes(first)===configBytes(second),{before:configBytes(first),after:configBytes(second)});demand(row,'saved preference survives reload',second.config.method==='3'&&second.config.units==='c',second.config);}finally{await e.context.close();}},
 async prefer(browser,server,c,row){const e=await create(browser,server,c,{seed:c.saved?'manual':'none',fragment:BASE.replace('&label=Madinah&method=4','&method=2&units=f')+'&preferLocal=1'});try{await open(e);const s=await snapshot(e,row,'prefer-local');demand(row,'preferLocal saved/fixed rule',c.saved?s.config.lat===51.5&&s.config.method==='3'&&s.config.units==='c':s.config.lat===24.47&&s.config.method==='2'&&s.config.units==='f',s.config);demand(row,'preferLocal no coarse',!s.report.requests.some(r=>/geojs|ipinfo/.test(r.url)),s.report.requests);}finally{await e.context.close();}},
 async saveDenied(browser,server,c,row){
  const e=await create(browser,server,c,{seed:'manual',query:{deny:c.deny||'save'}});
  try{
   const before=await snapshot(e,row,'loaded saved London before denied save');
   demand(row,'literal saved London 3/f seed',before.config.lat===51.5&&before.config.lon===-.12&&before.config.method==='3'&&before.config.units==='f',before.config);
   await capture(e,row,'baseline-card');
   await e.frame.evaluate(()=>window.__locationFixture.holdProvider('prayer',true));
   await open(e);await e.frame.locator('#set-units').selectOption('c');await close(e);
   const after=await snapshot(e,row,'closed denied save before prayer settles');
   const failed=after.report.storageFaults.filter(f=>f.operation==='save'&&f.key===KEY);
   row.mutantReached=failed.length===1;
   demand(row,'denied config write reached actual close caller',failed.length===1&&failed[0].error===(c.deny==='quota'?'QuotaExceededError':'SecurityError'),failed);
   demand(row,'denied save in-memory usable',after.config.units==='c',after.config);
   demand(row,'old native bytes preserved',configBytes(after)===configBytes(before),{before:configBytes(before),after:configBytes(after)});
   const event=after.report.uiEvents.at(-1);
   demand(row,'end-of-event close applies and focuses synchronously',event?.closed&&event.exactOpenerFocused&&event.config.units==='c'&&event.savedBytes===configBytes(before),event);
   const held=after.report.providerJobs.filter(j=>j.kind==='prayer'&&j.state==='held');
   demand(row,'actual apply prayer transport remains unresolved',held.length>0&&held.every(j=>j.consumerAtDispatch.config.units==='c'),held);
   if(c.mutant)await capture(e,row,'mutant-through-close-state');
   demand(row,'session-only warning',/session only.*Could not save settings/i.test(after.app.status),after.app.status);
   demand(row,'failure is published at prayer dispatch',held.every(j=>j.consumerAtDispatch.persistence?.status==='session-only'&&/session only.*Could not save settings/i.test(j.consumerAtDispatch.status)),held);
   demand(row,'closed warning marker',await e.frame.locator('.buckle').evaluate(x=>x.classList.contains('persist-warning')&&x.querySelector('.gear')?.textContent==='!'));
   sentinels(row,after);await capture(e,row,'closed-warning');
   await open(e);demand(row,'reopened full warning',/session only.*Could not save settings/i.test((await view(e.frame)).app.status));
   await capture(e,row,'reopened-warning');await keyboard(e,row);
   demand(row,'Escape returns opener while prayer stays unresolved',(await view(e.frame)).report.providerJobs.some(j=>j.kind==='prayer'&&j.state==='held'));
   await e.frame.evaluate(()=>{
    const f=window.__locationFixture,live=f.pendingProviders('prayer');
    if(!(live.length>0&&live.every(j=>j.consumerAtDispatch?.config?.units==='c')))throw Error('Live held prayer collection missing or stale choice');
    if(!live.every(j=>j.consumerAtDispatch?.persistence?.status==='session-only'&&/session only.*Could not save settings/i.test(j.consumerAtDispatch?.status)))throw Error('Live held prayer collection lost save warning');
    const ids=live.map(j=>j.id);
    f.holdProvider('prayer',false);for(const id of ids)f.releaseProvider(id);
   });
   await wait(e.frame,()=>!!today&&window.__locationFixture.pendingProviders('prayer').length===0);
   const settled=await snapshot(e,row,'prayer settled without warning overwrite');
   demand(row,'prayer settlement retains complete warning',/session only.*Could not save settings/i.test(settled.app.status)&&configBytes(settled)===configBytes(before),settled);
   await capture(e,row,'settled-closed-warning');
  }finally{await e.context.close();}
 },
 async resetDenied(browser,server,c,row){
  const lookup=c.lookup||'gps';
  const e=await create(browser,server,c,{seed:'manual',query:{deny:'reset',gps:'held',hold:lookup==='search'?'search':''}});
  try{
   await capture(e,row,'baseline-card');await open(e);
   if(lookup==='search'){
    // Enter searches the populated London name without making a new dirty edit.
    await e.frame.locator('#set-label').press('Enter');
    await wait(e.frame,()=>window.__locationFixture.pendingProviders('search').length===1);
   }else{await e.frame.locator('#set-pin').click();await wait(e.frame,()=>window.__locationFixture.gpsCalls.length===1);}
   const before=await snapshot(e,row,'pending '+lookup+' before denied reset');
   await e.frame.locator('#set-reset').click();
   const immediate=await snapshot(e,row,'synchronous denied reset event');
   row.mutantReached=immediate.report.storageFaults.some(f=>f.operation==='reset'&&f.key===KEY);
   demand(row,'denied config removal reached actual reset caller',row.mutantReached,immediate.report.storageFaults);
   if(lookup==='search')await e.frame.evaluate(()=>{const f=window.__locationFixture;f.releaseProvider(f.pendingProviders('search')[0].id);});
   else await e.frame.evaluate(()=>window.__locationFixture.releaseGPS(0));
   // Observe after the callback and two browser turns; no product timing threshold.
   await e.frame.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   const after=await snapshot(e,row,'reset denied after obsolete '+lookup+' returns');
   if(c.mutant)await capture(e,row,'mutant-through-reset-state');
   demand(row,'reset-failed warning',/Could not clear saved settings/i.test(after.app.status),after.app.status);
   demand(row,'failed reset native bytes retained',configBytes(after)===configBytes(before));
   demand(row,'failed reset active target retained',JSON.stringify(after.config)===JSON.stringify(before.config),{before:before.config,after:after.config});
   demand(row,'failed reset no coarse',!after.report.requests.some(r=>/geojs|ipinfo/.test(r.url)),after.report.requests);
   demand(row,'one config removal',after.report.storageEvents.filter(([op,k])=>op==='remove'&&k===KEY).length===1,after.report.storageEvents);
   demand(row,'obsolete result cannot overwrite reset warning',after.app.status===immediate.app.status&&!/Saved settings cleared|Using estimated area|Searching|Requesting/.test(after.app.status),{immediate:immediate.app.status,after:after.app.status});
   sentinels(row,after);await capture(e,row,'reset-failed');await keyboard(e,row);
   await capture(e,row,'reset-closed-warning');await open(e);
   demand(row,'reset reopened retained warning',/Could not clear saved settings/.test((await view(e.frame)).app.status));
   await capture(e,row,'reset-reopened-warning');
  }finally{await e.context.close();}
 },
 async readFault(browser,server,c,row){
  const seed=['malformed','v2'].includes(c.fault)?c.fault:'manual',deny=['getter','read'].includes(c.fault)?c.fault:'none';
  const e=await create(browser,server,c,{seed,query:{deny,detect:'fail'}});
  try{
   const before=await snapshot(e,row,'native boot fallback before explicit manual write');
   demand(row,'load fallback has no adopted target',before.config===null&&before.app.config.lat===null&&before.app.config.lon===null,before.config);
   demand(row,'load record preserved before explicit save',configBytes(before)===before.report.seedBytes,{bytes:configBytes(before),seed:before.report.seedBytes});
   demand(row,'load is non-destructive',!before.report.storageEvents.some(([op,k])=>op==='remove'&&k===KEY),before.report.storageEvents);
   demand(row,'no uncaught storage failure',before.report.errors.length===0,before.report.errors);
   if(deny!=='none')demand(row,'selected denied load operation reached',before.report.storageFaults.some(f=>f.operation===deny&&f.key===KEY),before.report.storageFaults);
   sentinels(row,before);await capture(e,row,'boot-manual-fallback');await open(e);
   await e.frame.locator('#set-lat').fill('30');await e.frame.locator('#set-lon').fill('31');await close(e);
   const after=await snapshot(e,row,'through-close manual recovery');
   demand(row,'manual recovery useful',after.config.lat===30&&after.config.lon===31,after.config);
   if(c.fault==='getter'){
    demand(row,'getter denial session warning',/session only/i.test(after.app.status)&&configBytes(after)===configBytes(before),after);
   }else{
    demand(row,'read failure does not preclude later writable save',!!configBytes(after)&&JSON.parse(configBytes(after)).lat===30&&/Settings saved in this browser/.test(after.app.status),after);
   }
   sentinels(row,after);await capture(e,row,'manual-recovery');
  }finally{await e.context.close();}
 },
 async saveRecovery(browser,server,c,row){
  const e=await create(browser,server,c,{seed:'manual',query:{deny:'save'}});
  try{
   const before=await snapshot(e,row,'before failed save');await open(e);
   await e.frame.locator('#set-units').selectOption('c');await close(e);
   const denied=await snapshot(e,row,'denied save before recovery');
   demand(row,'initial save failed with old native bytes',/session only/i.test(denied.app.status)&&configBytes(denied)===configBytes(before),denied);
   await e.frame.evaluate(()=>window.__locationFixture.denySave=false);await open(e);
   await e.frame.locator('#set-time').selectOption('12');await close(e);
   const s=await snapshot(e,row,'successful later save through close'),saved=JSON.parse(configBytes(s));
   demand(row,'later save normalized bytes',saved.units==='c'&&saved.time==='12'&&configBytes(s)!==configBytes(before),saved);
   demand(row,'later save clears warning',/Settings saved in this browser/.test(s.app.status)&&!await e.frame.locator('.buckle').evaluate(x=>x.classList.contains('persist-warning')),s.app.status);
   demand(row,'successful save retains normalized source/origin/time',saved.v===1&&saved.savedAt===T&&s.config.source==='localStorage'&&s.config.origin==='manual',s.config);
   await restoredOpener(e,row);sentinels(row,s);await capture(e,row,'recovered-normal-opener');await open(e);
   demand(row,'reopened successful outcome replaces old failure',/Settings saved in this browser/.test((await view(e.frame)).app.status)&&!/session only/i.test((await view(e.frame)).app.status));
   await capture(e,row,'recovered-reopened');
  }finally{await e.context.close();}
 },
 async resetSuccess(browser,server,c,row){
  const e=await create(browser,server,c,{seed:'manual',query:{hold:'coarse',deny:'reset'}});
  try{
   await open(e);await e.frame.locator('#set-reset').click();
   const failed=await snapshot(e,row,'first removal denied before recovery');
   demand(row,'initial reset failed with saved bytes',/Could not clear saved settings/.test(failed.app.status)&&configBytes(failed)===failed.report.seedBytes,failed);
   await e.frame.evaluate(()=>window.__locationFixture.denyRemove=false);await e.frame.locator('#set-reset').click();
   await wait(e.frame,()=>window.__locationFixture.pendingProviders('coarse').length===1);await restoredOpener(e,row);
   const cleared=await snapshot(e,row,'cleared and detecting');
   demand(row,'reset removed only config',configBytes(cleared)===null,cleared.report.storage);
   demand(row,'one denied and one recovered removal attempt',cleared.report.storageEvents.filter(([op,k])=>op==='remove'&&k===KEY).length===2&&cleared.report.storageFaults.filter(f=>f.operation==='reset').length===1,cleared.report.storageEvents);
   demand(row,'cleared detecting stage',/Saved settings cleared.*Detecting your area/is.test(cleared.app.status),cleared.app.status);
   sentinels(row,cleared);await capture(e,row,'reset-cleared-detecting');
   if(c.detect==='held')return;
   if(c.detect==='superseded'){
    await e.frame.locator('#set-lat').fill('30');await e.frame.locator('#set-lon').fill('31');await close(e);
    row.currentEditStatus=(await view(e.frame)).app.status;
   }
   await e.frame.evaluate(fail=>{const f=window.__locationFixture,id=f.pendingProviders('coarse')[0].id;fail?f.rejectProvider(id):f.releaseProvider(id);},c.detect==='failure');
   if(c.detect==='failure'){
    await wait(e.frame,()=>window.__locationFixture.pendingProviders('coarse').length===1);
    await e.frame.evaluate(()=>{const f=window.__locationFixture;f.rejectProvider(f.pendingProviders('coarse')[0].id);});
   }
   await wait(e.frame,()=>!/Detecting your area/.test(document.querySelector('#set-status').textContent));
   await e.frame.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   const final=await snapshot(e,row,'reset final '+c.detect+' stage');
   if(c.detect==='superseded')demand(row,'current manual edit owns late reset',final.config.lat===30&&final.config.lon===31&&JSON.parse(configBytes(final)).lat===30&&final.app.status===row.currentEditStatus,final);
   else{
    demand(row,'successful reset does not recreate config',configBytes(final)===null,final.report.storage);
    demand(row,'reset truthful stage',c.detect==='failure'?/Enter your location/.test(final.app.status):/Using estimated area/.test(final.app.status),final.app.status);
    demand(row,'reset save:false does not write config',final.report.storageEvents.filter(([op,k])=>op==='set'&&k===KEY).length===cleared.report.storageEvents.filter(([op,k])=>op==='set'&&k===KEY).length,final.report.storageEvents);
   }
   sentinels(row,final);await capture(e,row,'reset-final-'+c.detect);
  }finally{await e.context.close();}
 },
 async metadata(browser,server,c,row){const e=await create(browser,server,c,{gps:c.kind==='cached'?'cached':'success',query:{...(c.accuracy!==undefined?{accuracy:c.accuracy}:{}),...(c.timestamp!==undefined?{timestamp:c.timestamp}:{})}});try{await gps(e,c);let s=await snapshot(e,row,'acquired through actual form');const evidence=c.page==='builder'?s.form.locationEvidence:await e.frame.evaluate(()=>_setLocationEvidence);const acc=c.expectedAccuracy===undefined?25:c.expectedAccuracy,stamp=c.expectedTimestamp===undefined?(c.kind==='cached'?T-300000:T):c.expectedTimestamp;demand(row,'original metadata',evidence.accuracyM===acc&&evidence.acquiredAt===stamp,{evidence,acc,stamp});demand(row,'one-shot options unchanged',s.report.gpsCalls.length===1&&s.report.gpsCalls[0].options.enableHighAccuracy===false&&s.report.gpsCalls[0].options.timeout===10000&&s.report.gpsCalls[0].options.maximumAge===600000,s.report.gpsCalls);if(c.page==='widget'){await persist(e);s=await reload(e,row);demand(row,'native load original metadata',s.config.locationEvidence.accuracyM===acc&&s.config.locationEvidence.acquiredAt===stamp,s.config.locationEvidence);}else{const portable=await e.frame.evaluate(()=>hash());const params=new URLSearchParams(portable);demand(row,'portable omits private history',['locationEvidence','accuracyM','acquiredAt','savedAt'].every(k=>!params.has(k)),portable);const recipient=await create(browser,server,{page:'widget'},{fragment:'#'+portable});try{const fixed=await view(recipient.frame);demand(row,'portable recipient is configured destination',fixed.config.locationEvidence.intent==='fixed-site'&&fixed.config.locationEvidence.source==='hash'&&fixed.config.locationEvidence.acquiredAt===null,fixed.config);}finally{await recipient.context.close();}}
 if(c.kind==='day-later'||c.kind==='label-only'){await e.frame.evaluate(()=>window.__locationFixture.advance(86400000));if(c.page==='widget'){await open(e);await e.frame.locator('#set-label').fill('Custom display name');await e.frame.locator('#set-units').selectOption('c');await close(e);const later=await snapshot(e,row,'day-later preference save');demand(row,'original acquisition time',later.config.locationEvidence.acquiredAt===T&&JSON.parse(configBytes(later)).locationEvidence.acquiredAt===T,later.config);demand(row,'savedAt independently advances',JSON.parse(configBytes(later)).savedAt===T+86400000,configBytes(later));const loaded=await reload(e,row,T+86400000);demand(row,'day-later native reload preserves original acquisition',loaded.config.locationEvidence.acquiredAt===T,loaded.config.locationEvidence);await open(e);const title=(await view(e.frame)).app.pin.title;demand(row,'saved browser pin shows original age',title.includes('Saved browser position')&&title.includes('1440 min old'),title);}else{await e.frame.locator('#label').fill('Custom display name');await e.frame.locator('#units').selectOption('c');const later=await snapshot(e,row,'builder later display name');demand(row,'original acquisition time',later.form.locationEvidence.acquiredAt===T,later.form.locationEvidence);}}await capture(e,row,'metadata');}finally{await e.context.close();}},
 async intent(browser,server,c,row){if(c.kind==='label-only')return actions.metadata(browser,server,{...c,kind:'day-later'},row);const e=await create(browser,server,c,{seed:c.kind==='manual'?'manual':'none',query:{...(c.kind.startsWith('place')?{bounds:c.kind.slice(6)}:{})}});try{const widget=c.page!=='builder';if(widget)await open(e);if(c.kind==='coordinate-after-gps')await gps(e,c);const prefix=widget?'set-':'';if(c.kind==='manual'||c.kind==='coordinate-after-gps'){await e.frame.locator('#'+prefix+'lat').fill('30.12345');await e.frame.locator('#'+prefix+'lon').fill('31.12345');}else if(c.kind.startsWith('place')){await e.frame.locator('#'+prefix+'label').fill('Berlin');await e.frame.locator('#'+prefix+'label').press('Enter');await wait(e.frame,p=>document.getElementById(p+'lat').value==='52.52000',prefix);}else if(c.kind==='coarse'){const s=await snapshot(e,row,'coarse target');const ev=widget?s.config.locationEvidence:s.form.locationEvidence;demand(row,'coarse scalar not metres',ev.source==='coarse-ip'&&ev.accuracyM===null,ev);return;}const s=await snapshot(e,row,'actual intent form');const ev=widget?await e.frame.evaluate(()=>_setLocationEvidence):s.form.locationEvidence;if(c.kind.startsWith('place')){demand(row,'place source/provider',ev.intent==='fixed-site'&&ev.source==='place'&&ev.provider==='Nominatim',ev);demand(row,'place bounds known or unknown',c.kind==='place-valid'?ev.bounds?.south===52&&ev.bounds?.north===53&&ev.bounds?.west===13&&ev.bounds?.east===14:ev.bounds===null,ev);}else demand(row,'manual fixed site clears incompatible metadata',ev.intent==='fixed-site'&&ev.source==='manual'&&ev.accuracyM===null&&ev.acquiredAt===null,ev);if(widget)await persist(e);}finally{await e.context.close();}},
 async legacy(browser,server,c,row){const e=await create(browser,server,c,{seed:'legacy'});try{const s=await snapshot(e,row,'legacy load');demand(row,'legacy usable without fabricated fix',s.config.lat===52.52&&s.config.lon===13.41&&s.config.locationEvidence.accuracyM===null&&s.config.locationEvidence.acquiredAt===null,s.config);demand(row,'legacy reading non-destructive',configBytes(s)===s.report.seedBytes,configBytes(s));}finally{await e.context.close();}},
 async metadataDenied(browser,server,c,row){const e=await create(browser,server,c,{seed:'manual',query:{deny:'save'}});try{const before=await view(e.frame);await gps(e,c);await close(e);const s=await snapshot(e,row,'denied metadata save');demand(row,'denied metadata accurate in memory',s.config.locationEvidence.accuracyM===25&&s.config.locationEvidence.acquiredAt===T,s.config);demand(row,'denied metadata old native bytes',configBytes(s)===configBytes(before));demand(row,'denied metadata session warning',/session only/i.test(s.app.status));}finally{await e.context.close();}},
 async policy(browser,server,c,row){const e=await create(browser,server,c,{seed:'manual',gps:'native',clock:'real'});try{if(c.page==='builder'){await e.frame.locator('#lat').fill('51.5');await e.frame.locator('#lon').fill('-0.12');}const before=await snapshot(e,row,'native policy before opt-in');demand(row,'native policy no boot GPS',before.report.gpsCalls.length===0);await gps(e,c);await wait(e.frame,()=>window.__locationFixture.nativeCallbacks.length===1);const after=await snapshot(e,row,'native callback consumer');const cb=after.report.nativeCallbacks[0],allowed=['top-level','delegated'].includes(c.policy);row.policy={origins:{A:server.A,B:server.B},parentPolicy:c.policy==='restrictive'?'geolocation=()':c.policy==='delegated'?`geolocation=(self "${server.B}")`:null,allow:c.policy==='noallow'?null:c.policy==='top-level'?null:'geolocation',grants:[server.A,server.B],secure:after.secure,introspection:await e.frame.evaluate(()=>({allows:document.permissionsPolicy?.allowsFeature('geolocation')??document.featurePolicy?.allowsFeature('geolocation')??null})),clock:'real Date',location:'browser context synthetic, not sensor'};demand(row,'native policy exactly one opt-in call',after.report.gpsCalls.length===1,after.report.gpsCalls);if(allowed){demand(row,'native policy success',cb.kind==='success'&&cb.accuracy===25,cb);const ev=c.page==='builder'?after.form.locationEvidence:await e.frame.evaluate(()=>_setLocationEvidence);demand(row,'native captured timestamp exact',ev.acquiredAt===cb.timestamp&&ev.accuracyM===25,ev);}else{demand(row,'native policy denial 1',cb.kind==='error'&&cb.code===1,cb);const current=c.page==='builder'?after.form:after.config;demand(row,'denied native target unchanged',current.lat===before[c.page==='builder'?'form':'config'].lat&&current.lon===before[c.page==='builder'?'form':'config'].lon,current);const prefix=c.page==='builder'?'':'set-';if(c.page!=='builder')await open(e);await e.frame.locator('#'+prefix+'lat').fill('30');await e.frame.locator('#'+prefix+'lon').fill('31');if(c.page!=='builder')await close(e);const recovery=await snapshot(e,row,'policy manual recovery');demand(row,'native policy manual recovery',Number(recovery[c.page==='builder'?'form':'config'].lat)===30,recovery);}await capture(e,row,'native-policy');}finally{await e.context.close();}},
 async errorConsumer(browser,server,c,row){const e=await create(browser,server,c,{seed:'manual',gps:c.gps});try{if(c.page==='builder'){await e.frame.locator('#lat').fill('51.5');await e.frame.locator('#lon').fill('-0.12');}const before=await snapshot(e,row,'before synthetic error');demand(row,'mock no automatic call',before.report.gpsCalls.length===0);await gps(e,c);const after=await snapshot(e,row,'mock error consumer');demand(row,'mock at most one opt-in/no retry',after.report.gpsCalls.length===(c.gps==='unsupported'?0:1),after.report.gpsCalls);const kind=c.page==='builder'?'form':'config';demand(row,'mock preserves target and metadata',after[kind].lat===before[kind].lat&&after[kind].lon===before[kind].lon,after[kind]);const prefix=c.page==='builder'?'':'set-';await e.frame.locator('#'+prefix+'lat').fill('30');await e.frame.locator('#'+prefix+'lon').fill('31');if(c.page!=='builder')await close(e);demand(row,'mock manual recovery',Number((await view(e.frame))[kind].lat)===30);row.mockScope='deterministic caller error; not native policy or sensor proof';}finally{await e.context.close();}},
 async diagnostics(browser,server,c,row){const reduced=['reduced','full'].includes(c.kind),fragment=c.kind==='query-negative'?'#lat=24.47&lon=39.61':BASE+'&debugMotion=1'+(c.kind==='full'?'&motion=full':'');const e=await create(browser,server,c,{clock:'real',reduce:reduced,fragment});try{if(c.kind==='query-negative'){const u=new URL(e.url);u.searchParams.set('debugMotion','1');u.searchParams.set('motion','full');await e.page.goto(u.href);await wait(e.frame,()=>window.__locationFixture?.state==='ready');}await e.frame.evaluate(()=>{window.__rlgwoOverlayUpdates=0;const dm=document.querySelector('.dbgmotion');if(dm)new MutationObserver(()=>window.__rlgwoOverlayUpdates++).observe(dm,{childList:true,characterData:true,subtree:true});});const read=()=>e.frame.evaluate(()=>({search:location.search,hash:location.hash,overlayUpdates:window.__rlgwoOverlayUpdates,q:Object.fromEntries(q.entries()),DEBUGMOTION,MOTIONFULL,reduced:isMotionReduced(),nativeReduced:matchMedia('(prefers-reduced-motion: reduce)').matches,TIMESCALE,overlay:document.querySelector('.dbgmotion')?.textContent,display:getComputedStyle(document.querySelector('.dbgmotion')).display,fullClass:document.querySelector('.c').classList.contains('motionfull'),visibility:document.visibilityState}));const first=await read();await new Promise(r=>setTimeout(r,1250));const second=await read();row.diagnostic={first,second,mediaEmulation:'BrowserContext reducedMotion, native matchMedia readback',visibleMotionClaim:false};if(c.kind==='query-negative')demand(row,'native query negative flags/overlay',!second.DEBUGMOTION&&!second.MOTIONFULL&&second.display==='none'&&new URLSearchParams(second.search).get('debugMotion')==='1'&&new URLSearchParams(second.search).get('motion')==='full',second);else{demand(row,'native diagnostic active real-time',second.DEBUGMOTION&&second.TIMESCALE===1&&second.display!=='none'&&second.visibility==='visible',second);demand(row,'native media state truthful',second.nativeReduced===reduced,second);demand(row,'native reduced/full semantics',second.reduced===(c.kind==='reduced')&&second.MOTIONFULL===(c.kind==='full')&&second.fullClass===(c.kind==='full'),second);demand(row,'rendered telemetry populated',typeof second.overlay==='string'&&second.overlay.length>20,second.overlay);demand(row,'actual loop updates rendered telemetry',second.overlayUpdates>first.overlayUpdates,{first:first.overlayUpdates,second:second.overlayUpdates});}await capture(e,row,'diagnostic');}finally{await e.context.close();}}
};
function preflight(options){
 assert.equal(options.group,'r0011','only R0011 assigned');
 const server=new SourceServer(options),binding=server.binding;assert.equal(options.sourceRef,binding.sourceRef);
 const fixture=fs.readFileSync(path.join(HERE,'residual-location-native.html'),'utf8');new vm.Script(fixture.match(/<script>([\s\S]*?)<\/script>/)[1]);
 assert(!fixture.includes("script-src 'self' 'unsafe-inline' 'unsafe-eval'"),'CSP eval was weakened');
 const canonical=Object.entries(binding.runtimeEntries).sort(([a],[b])=>a<b?-1:a>b?1:0).map(([name,e])=>e.sha256+'  '+name+'\n').join('');assert.equal(hash(canonical),binding.runtimeSha256,'runtime manifest canonical identity');
 for(const name of binding.runtimeFiles)server.raw(name);
 const authored=fs.readFileSync(path.join(options.sourceRoot,'src/native/index.html'));assert.equal(hash(authored),binding.authoredIndexSha256,'authored source drift');
 for(const [name,file]of[['widget','index.html'],['builder','builder.html']]){const source=server.raw(file),scripts=[...source.toString('utf8').matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];assert.equal(hash(source),binding.pages[name].sha);assert.deepEqual(scripts.map(s=>s[1]),binding.pages[name].attrs);assert.deepEqual(scripts.map(s=>hash(s[2])),binding.pages[name].bodiesSha256);}
 assert.equal(hash(server.raw('config.js')),binding.configSha256);assert.equal(binding.pages.widget.attrs.length,6);assert.equal(binding.pages.builder.attrs.length,2);
 for(const c of cases)assert.equal(typeof actions[c.type],'function','native action absent '+c.type);
 for(const [name,m]of Object.entries(mutations)){const mutated=replaceOne(server.raw(m.file).toString('utf8'),m.from,m.to);for(const s of mutated.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi))if(!/src=/.test(s[1]))new vm.Script(s[2]);}
 return{cases:cases.length,group:'r0011',runtimeSha256:binding.runtimeSha256,authoredIndexSha256:binding.authoredIndexSha256,mutants:Object.keys(mutations),native:'NOT_RUN',browser:'NOT_RUN'};
}
async function execute(options){assert(options.leaseAuthorized===true,'root serial browser lease is required');const out=path.resolve(options.out);assert(out.startsWith(path.resolve(HERE,'..')+path.sep),'output must remain in persistence_native worker');fs.mkdirSync(out,{recursive:true});const selected=cases.filter(c=>c.group===options.group&&(!options.only?.length||options.only.includes(c.name)));assert(selected.length,'selected native cases absent');for(const name of options.only||[])assert(selected.some(c=>c.name===name),'unknown case '+name);preflight(options);const lib=require(path.join(options.packageRoot,'playwright'));const server=new SourceServer(options);let browser;const rows=[];try{await server.start();browser=await lib.chromium.launch({headless:true,chromiumSandbox:true,...(options.executable?{executablePath:options.executable}:{})});for(const c of selected){server.variant=c.mutant||null;const directory=path.join(out,c.name);fs.mkdirSync(directory,{recursive:true});const row={...c,out:directory,status:'RUNNING',checks:[],snapshots:{},crops:[],sourceRef:options.sourceRef,sourceBinding:server.manifest(),sourceKind:c.mutant?'isolated counterfactual':'exact generated consumer with explicit fixture hooks',runtimeSha256:server.binding.runtimeSha256,native:{browser:'chromium',version:browser.version(),os:process.platform,node:process.version,playwright:require(path.join(options.packageRoot,'playwright/package.json')).version,viewport:{width:c.narrow?390:1000,height:c.narrow?844:900},dpr:1,timezone:c.type==='preference'?'Asia/Riyadh':'UTC'},independentReview:'PENDING'};try{await actions[c.type](browser,server,c,row);if(c.mutant)throw Error('Mutation unexpectedly passed its actual consumer oracle');row.status='PASS';}catch(error){row.error={message:error.message,code:error.code,assertion:error.assertion,stack:error.stack};if(c.mutant&&error.code==='CONSUMER_ASSERTION'&&error.assertion.includes(mutations[c.mutant].oracle)){row.status='CAUGHT';row.mutantConsumerFailurePreserved=true;}else row.status='FAIL';}fs.writeFileSync(path.join(directory,'result.json'),JSON.stringify(row,null,2)+'\n');rows.push(row);process.stdout.write(JSON.stringify({name:c.name,status:row.status,error:row.error?.message})+'\n');if(row.status==='FAIL'&&options.stopOnFailure!==false)break;}}finally{if(browser)await browser.close();await server.close();}const result={schema:'residual-native-results/v1',sourceRef:options.sourceRef,group:options.group,selected: selected.map(c=>c.name),executed:rows.map(r=>({name:r.name,status:r.status,result:path.join(r.out,'result.json')})),notRun:selected.filter(c=>!rows.some(r=>r.name===c.name)).map(c=>c.name),independentPixels:'PENDING',closure:'NOT_AUTHORIZED'};fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');return rows.some(r=>r.status==='FAIL')?1:0;}
module.exports={cases,actions,mutations,preflight,execute,ConsumerAssertion,replaceOne,SourceServer,KEY,T};
if(require.main===module){const options=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));if(options.list){process.stdout.write(JSON.stringify({cases:cases.filter(c=>!options.group||c.group===options.group),browser:'NOT_RUN'},null,2)+'\n');}else if(options.validateOnly){process.stdout.write(JSON.stringify(preflight(options))+'\n');}else execute(options).then(code=>process.exitCode=code).catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=2;});}
