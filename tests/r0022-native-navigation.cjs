// Exercise actual open() and distinct whole product contexts. Controlled navigation,
// image decode and canvas commands do not certify native boot/texture/occlusion pixels.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),cp=require('node:child_process');
const {load,root,sha}=require('./r001d-harness.cjs');
const read=(file,revision)=>revision?cp.execFileSync('git',['show',revision+':'+file],{cwd:root,maxBuffer:4*1024*1024}):fs.readFileSync(path.join(root,file));
const option=name=>process.argv.find(a=>a.startsWith(name+'='))?.slice(name.length+1);
const product=read('index.html',option('--product-revision')).toString('utf8'),wrapper=read('tests/r0022-native.html',option('--wrapper-revision')).toString('utf8');
const script=/<script>([\s\S]*?)<\/script>/.exec(wrapper)[1],config=fs.readFileSync(path.join(root,'config.js'));
const hash='#'+new URLSearchParams({lat:'24.47',lon:'39.61',tz:'Asia/Riyadh',label:'Madinah',method:'4',units:'c',seed:'1',simTemp:'24',simHumid:'55',simWind:'3',simMoon:'0.5',simWax:'1',simMoonAlt:'20',simMoonH:'42',qa:'1',simTime:'22:00',motion:'full'}).toString();
const controls=[];
async function readyDocument(url,bootstrap){
  const h=load({source:product,hash});h.ctx.location.href=url;h.ctx.eval=code=>h.run(code);
  if(bootstrap)h.run(bootstrap);
  await h.complete(h.run('boot()'));
  if(h.rafs.length)h.rafs.shift()(); // consume the actual boot-owned first frame
  // The actual captured map callbacks own _pbrReady and call real renderMoonPBR.
  // Zeroed boundary decode bytes here are NOT a textured/native surface proof.
  for(const im of h.images)if(typeof im.onload==='function')im.onload();
  h.ctx.document.getAnimations=()=>[];h.ctx.document.fonts.status='loaded';h.ctx.document.fonts[Symbol.iterator]=function*(){};
  assert.equal(h.run('qaState().cache.prayerLoaded'),true);
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true,JSON.stringify(h.run('qaState().moonTruth')));
  assert.ok(h.select('.mphoto').getAttribute('href'));return h;
}
async function probe(mode){
  const old=await readyDocument('blob:old-document'+hash);old.ctx.__fixtureClock={kind:'prior document'};old.ctx.__fixturePrayerRequests=[{ownership:'prior'}];
  const before=old.run('JSON.stringify(weather)'),beforeWeather=old.run('weather'),oldToken=old.ctx.__fixtureDocumentToken;let now=0,assigned=null,committed=false,newDoc=null,navigating=null;
  const frame={contentWindow:old.ctx};Object.defineProperty(frame,'src',{set(value){assigned=value;},get(){return assigned;}});
  const commit=async()=>{
    const body=await (await fetch(assigned.split('#')[0])).text();const bootstrap=/<script>([\s\S]*?)<\/script>/.exec(body)[1];
    newDoc=await readyDocument(assigned,bootstrap);frame.contentWindow=newDoc.ctx;committed=true;
  };
  const sandbox={Date,Math,Intl,URL,URLSearchParams,Response,Blob,TextDecoder,Uint8Array,Promise,crypto:crypto.webcrypto,
    performance:{now:()=>now},location:{href:'https://fixture.invalid/tests/r0022-native.html',origin:'https://fixture.invalid'},
    document:{getElementById:id=>id==='widget'?frame:{textContent:''}},innerWidth:900,innerHeight:800,devicePixelRatio:1,
    fetch:async url=>new Response(String(url).endsWith('config.js')?config:Buffer.from(product),{status:200}),
    setTimeout:(fn,ms)=>{now+=ms;if(mode==='owned'&&!committed&&assigned){navigating=navigating||commit();navigating.then(()=>fn(),e=>{console.error('owned bootstrap limitation '+e.message);now=13000;fn();});}else queueMicrotask(fn);return 1;},clearTimeout(){}};
  sandbox.window=sandbox;vm.createContext(sandbox);vm.runInContext(script,sandbox);
  let completed=false,report,error;try{report=await sandbox.lunarFixture.open();completed=true;}catch(e){error=e.message;}
  const observation={mode,completed,committed,elapsedMs:now,oldWeatherMutated:old.run('weather')!==beforeWeather,
    documentIdentity:report?.documentIdentity||null,sourceSha256:sha(Buffer.from(product)),wrapperSha256:sha(Buffer.from(wrapper))};controls.push(observation);
  if(mode==='retained'){
    assert.equal(completed,false,'old ready document cannot complete a pending reload');assert.match(error,/readiness unavailable/);
    assert.equal(old.run('JSON.stringify(weather)'),before,'old weather unchanged');assert.equal(old.ctx.__fixtureCurrent,undefined,'old document never mutated');
    assert.equal(old.run('weather'),beforeWeather,'prior object identity unchanged');
    assert.equal(old.ctx.__fixtureDocumentToken,oldToken);assert.equal(committed,false);
  }else{
    assert.equal(completed,true,error);assert.equal(committed,true);assert.notEqual(newDoc.ctx,old.ctx);
    assert.equal(report.documentIdentity?.matched,true);assert.equal(report.documentIdentity?.url,assigned);
    assert.equal(newDoc.ctx.__fixtureDocumentToken,report.documentIdentity.token);assert.ok(newDoc.ctx.__fixturePrayerRequests.length>=2);
    assert.equal(report.sourceSha256,sha(Buffer.from(product)));assert.equal(report.weatherEligibility.eligible,true);
    assert.equal(old.run('JSON.stringify(weather)'),before,'prior context remains untouched');
    assert.equal(old.run('weather'),beforeWeather,'prior object identity unchanged');
  }
  return observation;
}
(async()=>{let pass=0,fail=0;for(const mode of ['retained','owned']){try{await probe(mode);pass++;console.log('PASS '+mode+' navigation ownership');}catch(e){fail++;console.log('FAIL '+mode+' navigation ownership :: '+e.message.split('\n')[0]);}}
  console.log(JSON.stringify({pass,fail,controls,fixtureSha256:sha(fs.readFileSync(__filename)),limits:'actual source open/boot/admission/map callbacks with navigation/decode boundaries; no native qualification'}));process.exitCode=fail?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
