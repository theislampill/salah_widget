'use strict';
// Native-free adapter contracts. No Playwright or display is launched.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),zlib=require('node:zlib');
const test=require('node:test'),assert=require('node:assert/strict');
const source=path.join(__dirname,'r002f_bfcache_source.cjs');
function feature(){assert.ok(fs.existsSync(source),'bfcache source/return admission is not implemented');return require(source);}
function temporary(fn){const root=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-bfcache-control-'));
  return Promise.resolve().then(()=>fn(root)).finally(()=>fs.rmSync(root,{recursive:true,force:true}));}
function crc(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=c&1?(c>>>1)^0xedb88320:c>>>1;}return(c^0xffffffff)>>>0;}
function png(width=325,height=530){
  const chunk=(name,data)=>{const type=Buffer.from(name),out=Buffer.alloc(12+data.length);out.writeUInt32BE(data.length);
    type.copy(out,4);data.copy(out,8);out.writeUInt32BE(crc(Buffer.concat([type,data])),8+data.length);return out;};
  const header=Buffer.alloc(13);header.writeUInt32BE(width);header.writeUInt32BE(height,4);header[8]=8;header[9]=2;
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),
    chunk('IDAT',zlib.deflateSync(Buffer.alloc(height*(1+width*3)))),chunk('IEND',Buffer.alloc(0))]);
}

test('descriptor identities reject hardlink and symlink aliases and retain exact nanoseconds',()=>temporary(root=>{
  const S=feature(),file=path.join(root,'file');fs.writeFileSync(file,'original');
  const r=S.record(file);assert.equal(r.sha256,'0682c5f2076f099c34cfdd15a9e063849ed437a49677e6fcc5b4198c76575be5');
  assert.equal(r.mtimeNs,fs.statSync(file,{bigint:true}).mtimeNs.toString());
  fs.writeFileSync(file,'changed!');assert.throws(()=>S.requireRecord(r),/identity|changed/);
  fs.symlinkSync(file,path.join(root,'sym'));assert.throws(()=>S.record(path.join(root,'sym')),/symlink/);
  fs.linkSync(file,path.join(root,'hard'));assert.throws(()=>S.record(file),/alias|link/);
}));
test('Linux unsigned 64-bit inode identity agrees with Python even when Node exposes a signed bigint',()=>temporary(root=>{
  const S=feature(),file=path.join(root,'inode-control');fs.writeFileSync(file,'actual descriptor bytes');
  const fstat=fs.fstatSync,lstat=fs.lstatSync,negative=-9223372036854493470n;
  const signed=row=>new Proxy(row,{get(target,key){return key==='ino'?negative:Reflect.get(target,key);}});
  fs.fstatSync=(fd,options)=>{const row=fstat(fd,options);return options?.bigint?signed(row):row;};
  fs.lstatSync=(name,options)=>{const row=lstat(name,options);return name===file&&options?.bigint?signed(row):row;};
  try{assert.equal(S.record(file).inode,'9223372036855058146');}finally{fs.fstatSync=fstat;fs.lstatSync=lstat;}
}));
test('lossless PNG admission rejects changed dimensions CRC truncation and trailing bytes',()=>{
  const S=feature(),good=png();assert.equal(S.pngInfo(good).width,325);assert.equal(S.pngInfo(good).height,530);
  const bad=Buffer.from(good);bad[bad.length-1]^=1;
  for(const data of [png(326),bad,good.subarray(0,-1),Buffer.concat([good,Buffer.from('tail')])])assert.throws(()=>S.pngInfo(data));
});
test('each existing screenshot return is retained once and the identical Buffer returns to original caller',()=>temporary(async root=>{
  const S=feature(),sink=S.returnSink(path.join(root,'returns')),bytes=png();let calls=0,options;
  const result=await sink.capture(async got=>{calls++;options=got;return bytes;},{type:'png'},'ref-present');
  assert.equal(result,bytes);assert.equal(calls,1);assert.deepEqual(options,{type:'png'});
  assert.equal(sink.state.received,1);assert.equal(sink.state.captureCallsAdded,0);
  assert.deepEqual(fs.readFileSync(path.join(root,'returns',sink.state.frames[0].file)),bytes);
  assert.equal(sink.state.frames[0].tag,'ref-present');
  const value={ev:[{trusted:true,persisted:true,c:2}],frames:[[0,2,true,true]],c:2};
  assert.equal(sink.value('log',value),value);assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root,'returns','value-log.json'))),value);
  sink.finish();assert.equal(sink.state.stopped,true);
}));
test('a native screenshot rejection is preserved and never counted as a returned PNG',()=>temporary(async root=>{
  const S=feature(),sink=S.returnSink(path.join(root,'returns')),failure=Error('actual screenshot rejected');
  await assert.rejects(sink.capture(async()=>{throw failure;},{type:'png'},'restore-1'),e=>e===failure);
  assert.equal(sink.state.received,0);assert.equal(sink.state.attempted,1);assert.equal(sink.state.errors.length,1);
}));
test('a counted return beyond a retention cap is incomplete with its real prefix preserved',()=>temporary(async root=>{
  const S=feature(),sink=S.returnSink(path.join(root,'returns'),{...S.LIMITS,returns:1}),bytes=png();
  await sink.capture(async()=>bytes,{type:'png'},'ref-present');
  await assert.rejects(sink.capture(async()=>bytes,{type:'png'},'restore-1'),/bound|overflow/);
  assert.equal(sink.state.received,2);assert.equal(sink.state.frames.length,1);assert.equal(sink.state.overflow,true);
  assert.deepEqual(fs.readFileSync(path.join(root,'returns',sink.state.frames[0].file)),bytes);
}));
test('no screenshot executes after retention closes or while an existing call remains pending',()=>temporary(async root=>{
  const S=feature(),sink=S.returnSink(path.join(root,'returns'));let release,calls=0;
  const first=sink.capture(async()=>{calls++;return await new Promise(resolve=>{release=resolve;});},{type:'png'},'ref-present');
  await assert.rejects(sink.capture(async()=>{calls++;return png();},{type:'png'},'restore-1'));
  assert.equal(calls,1);release(png());await first;sink.finish();
  await assert.rejects(sink.capture(async()=>{calls++;return png();},{type:'png'},'ref-absent'));assert.equal(calls,1);
}));
test('cleanup scope refuses preexisting or foreign recording directories without deleting them',()=>temporary(root=>{
  const S=feature(),owned=path.join(root,'arm'),outside=path.join(root,'unrelated');fs.mkdirSync(owned);fs.mkdirSync(outside);
  fs.writeFileSync(path.join(outside,'keep'),'kept');
  assert.throws(()=>S.recorderScope(owned,'baseline',outside));assert.equal(fs.readFileSync(path.join(outside,'keep'),'utf8'),'kept');
  const target=path.join(owned,'.video-baseline');fs.mkdirSync(target);fs.writeFileSync(path.join(target,'keep'),'kept');
  assert.throws(()=>S.recorderScope(owned,'baseline',target));assert.ok(fs.existsSync(path.join(target,'keep')));
}));
test('original function extraction is pinned and retains adverse and exact threshold behavior',()=>{
  const S=feature(),original=S.originalFunctions(),zero=new Uint8Array([0,0]),bright=new Uint8Array([100,100]);
  assert.equal(original.classify(zero,bright,zero).verdict,'absent');
  assert.equal(original.classify(bright,bright,zero).verdict,'present');
  assert.equal(original.classify(new Uint8Array([121,121]),bright,zero).verdict,'far');
  assert.equal(original.classify(new Uint8Array([120,120]),bright,zero).verdict,'present');
  assert.equal(original.dist(new Uint8Array([8,8]),zero),8);
});

module.exports={temporary,png};

function adapter(){const file=path.join(__dirname,'r002f_bfcache_preload.cjs');assert.ok(fs.existsSync(file),'original-call preload is not implemented');return require(file);}
function browserDouble(order){const {EventEmitter}=require('node:events'),browser=new EventEmitter();let open=true;
  Object.assign(browser,{contexts:()=>[],isConnected:()=>open,newPage:async opts=>{order.push(['direct-page',opts]);return {};},
    newContext:async opts=>{order.push(['experiment-context',opts]);return {close:async()=>order.push(['context-close'])};},
    close:async()=>{order.push(['browser-close']);open=false;browser.emit('disconnected');}});return browser;}
test('unchanged original iso requests global and context proxy without a sandbox request',()=>temporary(async root=>{
  const {EventEmitter}=require('node:events'),fake=path.join(root,'playwright.cjs');fs.writeFileSync(fake,'module.exports={}');
  const context=new EventEmitter();Object.assign(context,{pages:()=>[],route:async()=>{},routeWebSocket:async()=>{},addInitScript:async()=>{},close:async()=>{}});
  let launch,options;const browser={newContext:async opts=>{options=opts;return context;},close:async()=>{}};
  require(fake);require.cache[fake].exports={chromium:{launch:async opts=>{launch=opts;return browser;}}};
  const prior=process.env.PLAYWRIGHT_PKG;process.env.PLAYWRIGHT_PKG=fake;
  try{await require('../r0041/iso.cjs').launch({proxy:{port:1234},log:[],routeDecisions:[],observed:[]},
    {engine:'chromium',mode:'route',headless:false,reducedMotion:'reduce',recordVideo:{dir:'/source-control/video',size:{width:326,height:530}},ignoreDefaultArgs:['--disable-back-forward-cache']});}
  finally{if(prior===undefined)delete process.env.PLAYWRIGHT_PKG;else process.env.PLAYWRIGHT_PKG=prior;delete require.cache[fake];}
  assert.deepEqual(launch.proxy,{server:'http://127.0.0.1:1234',bypass:'<-loopback>'});assert.equal(launch.chromiumSandbox,undefined);
  assert.deepEqual(options.proxy,launch.proxy);assert.equal(launch.timeout,undefined);
  const A=adapter(),changed=A.launchOptions(launch,{proxy:launch.proxy,executable:'/actual/chrome',display:':42',env:{PATH:'/usr/bin:/bin'}});
  assert.equal(changed.chromiumSandbox,true);assert.equal(changed.proxy,undefined);assert.equal(changed.timeout,undefined);
  for(const key of ['headless','args','ignoreDefaultArgs'])assert.deepEqual(changed[key],launch[key]);
}));
test('launch adapter refuses changed original arguments default timeout and browser proxy contract',()=>{
  const A=adapter(),proxy={server:'http://127.0.0.1:1234',bypass:'<-loopback>'},base=A.expectedLaunch(proxy);
  for(const delta of [{timeout:30000},{headless:true},{args:[]},{ignoreDefaultArgs:[]},{env:{PWDEBUG:'1'}},{proxy:{server:'http://other'}}])
    assert.throws(()=>A.launchOptions({...base,...delta},{proxy,executable:'/actual/chrome',display:':1',env:{}}));
  for(const env of [{PWDEBUG:'1'},{NODE_OPTIONS:'--require fake'},{HTTP_PROXY:'http://proxy'},{SELENIUM_REMOTE_URL:'http://remote'}])assert.throws(()=>A.cleanChildEnvironment(env));
});
test('same-browser adapter gates experiment creation and preserves context-before-after-boundary-before-close order',async()=>{
  const A=adapter(),order=[],browser=browserDouble(order),expected={proxy:{server:'http://127.0.0.1:1234'}};let closed=false;
  const guard=await A.guardBrowser(browser,expected,{before:async b=>{order.push(['before']);await b.newPage({serviceWorkers:'block'});},
    after:async b=>{order.push(['after']);await b.newPage({serviceWorkers:'block'});},context:async c=>{const raw=c.close;c.close=async()=>{await raw();closed=true;};},contextsClosed:()=>closed,fault:()=>{}});
  const c=await browser.newContext(expected);await c.close();await browser.close();assert.equal(guard.closed,true);
  assert.deepEqual(order.map(x=>x[0]),['before','direct-page','experiment-context','context-close','after','direct-page','browser-close']);
  await assert.rejects(browser.newContext(expected));await assert.rejects(browser.close());
});
test('original swallowed close error cannot produce a complete post-boundary or skip actual browser cleanup',async()=>{
  const A=adapter(),order=[],browser=browserDouble(order);let faults=[];
  const guard=await A.guardBrowser(browser,{proxy:{}},{before:async()=>{},after:async()=>{order.push(['after']);},context:async()=>{},contextsClosed:()=>false,fault:e=>faults.push(String(e))});
  // This exact original suppression is not changed by the adapter.
  await browser.close().catch(()=>{});
  assert.equal(guard.closed,true);assert.equal(guard.afterComplete,false);assert.ok(faults.length);
  assert.deepEqual(order.map(x=>x[0]),['browser-close']);
});
test('failed post-boundary preserves failure and still invokes the actual close exactly once',async()=>{
  const A=adapter(),order=[],browser=browserDouble(order),failure=Error('actual strict routing refusal failed');
  const guard=await A.guardBrowser(browser,{proxy:{}},{before:async()=>{},after:async()=>{throw failure;},context:async()=>{},contextsClosed:()=>true,fault:()=>{}});
  await assert.rejects(browser.close(),e=>e===failure);assert.equal(guard.closed,true);assert.equal(guard.afterComplete,false);
  assert.equal(order.filter(x=>x[0]==='browser-close').length,1);await assert.rejects(browser.close());
});
test('unchanged direct boundary rejects proxy DNS abort and timeout substitutes',async()=>{
  const original=require('./browser-control.cjs').refuseExternalThenReadLoopback;
  for(const error of ['net::ERR_PROXY_CONNECTION_FAILED','net::ERR_NAME_NOT_RESOLVED','net::ERR_ABORTED','Timeout 10000ms exceeded'])
    await assert.rejects(original({newPage:async()=>assert.fail('must stop before second marker')},{goto:async()=>{throw Error(error);}},'http://127.0.0.1','marker',{}));
});
test('unexpected experiment context or direct-page proxy/recorder options are refused before execution',async()=>{
  const A=adapter(),order=[],browser=browserDouble(order);
  await A.guardBrowser(browser,{proxy:{expected:true}},{before:async b=>{
    await assert.rejects(b.newPage({serviceWorkers:'block',proxy:{server:'bad'}}));await assert.rejects(b.newPage({serviceWorkers:'block',recordVideo:{dir:'bad'}}));
    await assert.rejects(b.newContext({proxy:{expected:true}}));},after:async()=>{},context:async()=>{},contextsClosed:()=>true,fault:()=>{}});
  await assert.rejects(browser.newContext({proxy:{changed:true}}));assert.equal(order.length,0);
});
function driver(){const file=path.join(__dirname,'r002f_bfcache.cjs');assert.ok(fs.existsSync(file),'bounded paired process driver is not implemented');return require(file);}
test('actual child overflow and timeout preserve bytes and process failures without a native success claim',()=>temporary(async root=>{
  const D=driver();
  const overflow=await D.runChild([process.execPath,'-e','process.stdout.write("x".repeat(10000))'],root,'overflow',3,{PATH:'/usr/bin:/bin'},{streamBytes:64});
  assert.equal(overflow.complete,false);assert.equal(overflow.overflow,true);assert.equal(fs.statSync(path.join(root,'overflow.stdout')).size,64);
  const timeout=await D.runChild([process.execPath,'-e','setTimeout(()=>{},10000)'],root,'timeout',0.05,{PATH:'/usr/bin:/bin'});
  assert.equal(timeout.complete,false);assert.equal(timeout.timedOut,true);assert.ok(timeout.signals.length>0);
}));
test('unknown or repeated actual phase messages cannot extend the child budget',()=>temporary(async root=>{
  const D=driver();for(const [name,code] of [['unknown','process.send({protocol:"r002f-bfcache-phase/1",phase:"invented",seconds:99999})'],
    ['repeated','process.send({protocol:"r002f-bfcache-phase/1",phase:"admission",seconds:30});process.send({protocol:"r002f-bfcache-phase/1",phase:"admission",seconds:30})']]){
    const got=await D.runChild([process.execPath,'-e',code+';setTimeout(()=>{},10000)'],root,name,3,{PATH:'/usr/bin:/bin'},{phases:true});
    assert.equal(got.complete,false);assert.match(got.error,/phase/);}
}));
test('paired original invocation has an explicit preload and preserves every scientific argument',()=>{
  const D=driver();assert.deepEqual(D.childArgv('/actual/node','/actual/arm','/private/output','baseline'),[
    '/actual/node','--require',path.join(__dirname,'r002f_bfcache_preload.cjs'),path.resolve(__dirname,'../r0041/real-witness.cjs'),
    '/actual/arm','/private/output','chromium','bfcache','2026-11-18T16:30:00Z','3','--label=baseline']);
});
test('pinned Playwright newPage to newContext chain remains direct without admitting an extra experiment context',async()=>{
  const A=adapter(),order=[],browser=browserDouble(order),expected={proxy:{server:'http://127.0.0.1:1234'}};
  const rawContext=browser.newContext;
  browser.newContext=async options=>{const context=await rawContext(options);context.newPage=async()=>({context:()=>context});return context;};
  // The reviewed 1.62.1 Browser.newPage body calls this.newContext(options), then context.newPage().
  browser.newPage=async function(options){const context=await this.newContext(options);return await context.newPage();};
  const guard=await A.guardBrowser(browser,expected,{before:async b=>{
    await b.newPage({serviceWorkers:'block'});await assert.rejects(b.newContext({serviceWorkers:'block'}));
  },after:async b=>{await b.newPage({serviceWorkers:'block'});},context:async()=>{},contextsClosed:()=>true,fault:()=>{}});
  await browser.newContext(expected);await assert.rejects(browser.newContext(expected));await browser.close();
  assert.equal(guard.closed,true);assert.deepEqual(order.filter(x=>x[0]==='experiment-context').map(x=>x[1]),[
    {serviceWorkers:'block'},expected,{serviceWorkers:'block'}]);
});
test('owned failed recorder retains only a bounded actual prefix and refuses aliases or path guesses',()=>temporary(root=>{
  const S=feature(),dir=path.join(root,'.video-baseline');fs.mkdirSync(dir);const video=path.join(dir,'actual.webm');fs.writeFileSync(video,Buffer.from('0123456789'));
  assert.equal(typeof S.recorderPrefix,'function','bounded actual recorder failure preservation is missing');
  const got=S.recorderPrefix(dir,video,path.join(root,'kept-prefix.webm'),{limit:4});
  assert.equal(got.complete,false);assert.equal(got.originalBytes,10);assert.equal(got.retained.bytes,4);
  assert.equal(fs.readFileSync(got.retained.path,'utf8'),'0123');assert.equal(fs.readFileSync(video,'utf8'),'0123456789');
  assert.throws(()=>S.recorderPrefix(dir,path.join(dir,'guessed.webm'),path.join(root,'guess.webm'),{limit:4}));
  fs.linkSync(video,path.join(root,'alias'));assert.throws(()=>S.recorderPrefix(dir,video,path.join(root,'aliased.webm'),{limit:4}));
}));
test('child currentness rejects a generated population or actual Git tree rebound before any browser call',()=>{
  const A=adapter();assert.equal(typeof A.admitChildSources,'function','child generated/current Git admission is missing');
  const config={label:'baseline',root:'/source-control/root',sources:{root:feature().REPO,commit:'a'.repeat(40),tree:'b'.repeat(40),clean:true,files:{}},generated:{root:'/source-control/root',files:['original']}};
  const base={currentRecords:()=>0,generated:()=>config.generated,git:args=>args[0]==='status'?'':args.at(-1)==='HEAD'?'a'.repeat(40):'b'.repeat(40)};
  assert.doesNotThrow(()=>A.admitChildSources(config,base));
  assert.throws(()=>A.admitChildSources(config,{...base,generated:()=>({files:['changed']})}));
  assert.throws(()=>A.admitChildSources(config,{...base,git:args=>args[0]==='status'?'': 'c'.repeat(40)}));
});
test('an actual missing executable preserves its spawn error without inventing a stopped process group',()=>temporary(async root=>{
  const got=await driver().runChild([path.join(root,'does-not-exist')],root,'spawn-failure',1,{PATH:'/usr/bin:/bin'});
  assert.equal(got.complete,false);assert.match(got.error,/ENOENT/);assert.notEqual(got.groupStopped,true);
}));
test('source-only owner controls reject partial censuses ambiguous PIDs missing start identity and browser-wide proxy',()=>{
  const A=adapter(),binary={resolvedPath:'/source-control/chrome',sha256:'a'.repeat(64)},host={uid:1000,netns:'net:[fixture]',pidns:'pid:[fixture]'};
  const row={...host,pid:123,startTicks:'456',exe:binary.resolvedPath,sha256:binary.sha256,
    argv:[binary.resolvedPath,...A.ARGS,'--remote-debugging-pipe','--user-data-dir=/source-control/profile']};
  const census=rows=>({protocol:'r002f-bfcache-owner-census/1',executable:binary.resolvedPath,complete:true,entries:4,failures:[],rows});
  assert.deepEqual(A.owner(census([]),census([row]),host,binary),row);
  for(const changed of [{...row,pid:undefined},{...row,startTicks:''},{...row,argv:[...row.argv,'--proxy-server=http://proxy']},
    {...row,argv:[...row.argv,'--no-sandbox']},{...row,netns:'net:[other]'}])assert.throws(()=>A.owner(census([]),census([changed]),host,binary));
  for(const changed of [{...census([row]),failures:[{pid:9,code:'EACCES'}]},census([row,row]),{...census([row]),complete:false}])
    assert.throws(()=>A.owner(census([]),changed,host,binary));
  assert.throws(()=>A.owner(census([row]),census([row]),host,binary));
});
test('source-only adapter receipt cannot erase a boundary close recorder display or lifecycle failure with original exit zero',()=>temporary(root=>{
  const S=feature(),A=adapter(),D=driver(),write=(name,value)=>S.writeBytes(path.join(root,name),Buffer.from(typeof value==='string'?value:JSON.stringify(value)));
  const binary=write('chromium','synthetic nonexecuted Chromium identity'),xvfb=write('xvfb','synthetic nonexecuted display identity'),rec=write('recorder','synthetic nonexecuted recorder identity');
  const tools={acquired:{managed:{chromium:binary,recorder:rec}},tools:{xvfb}},host={pid:101,uid:1000,netns:'net:[fixture]',pidns:'pid:[fixture]'};
  const owner={...host,pid:102,startTicks:'123',exe:binary.path,sha256:binary.sha256,argv:[binary.path,...A.ARGS,'--remote-debugging-pipe','--user-data-dir=/fixture']};
  const census=rows=>({protocol:'r002f-bfcache-owner-census/1',executable:binary.path,complete:true,entries:4,failures:[],rows});
  const life=kind=>({protocol:'r002f-process-lifecycle/1',kind,closed:true,cleanupRequested:true,faults:[],overflow:false});
  const boundary=()=>({protocol:'salah-hosted-browser-boundary/1',passed:true,headless:false,chromiumSandbox:true,
    uid:host.uid,netns:host.netns,browserPid:owner.pid,executableSha256:binary.sha256,loopbackRequests:2,
    externalNavigationError:'net::ERR_NETWORK_UNREACHABLE',postNegativePage:'fresh-page-same-browser',contextsClosed:true});
  const originalPath=path.join(root,'.video-baseline','actual.webm');fs.mkdirSync(path.dirname(originalPath));fs.writeFileSync(originalPath,'synthetic recorder bytes');
  const original=S.record(originalPath),retained=write('baseline.webm','synthetic recorder bytes'),config=write('child-config.json',{label:'baseline',out:root,scope:'SOURCE_CONTROL_ONLY'});
  const isolation=write('isolation.json',{protocol:'salah-hosted-native-isolation/1',passed:true,uid:1000,netns:host.netns,outerNetns:'net:[outer-fixture]',browserControl:{passed:true}});
  const displayArgv=[xvfb.path,'-displayfd','3','-screen','0','1024x768x24','-nolisten','tcp','-noreset','-ac'];
  const recorderArgv=[rec.path,...A.recorderArguments(originalPath)],proxy={server:'http://127.0.0.1:1234',bypass:'<-loopback>'};
  const journal=A.eventJournal(path.join(root,'adapter-events.jsonl'));
  const phases=D.NORMAL_PHASES.map(phase=>journal.event('phase',{phase,seconds:A.PHASES[phase]}));
  const value={protocol:'r002f-bfcache-adapter/1',status:'COMPLETE',label:'baseline',...S.DISCLOSURE,errors:[],originalExitRequested:0,host,
    cleanup:{context:true,browser:true,browserPidsGone:true,recorder:true,display:true,servers:true},
    beforeCensus:census([]),afterLaunchCensus:census([owner]),finalCensus:census([]),owner,
    browserLifecycle:life('browser'),contextLifecycle:life('context'),pageLifecycle:life('page'),
    display:{stopped:true,lifecycle:life('display'),cleanup:{stopped:true},display:':1',argv:displayArgv,
      process:{...host,pid:103,startTicks:'124',exe:xvfb.resolvedPath,sha256:xvfb.sha256,argv:displayArgv}},
    recorders:[{closed:true,returncode:0,pid:104,lifecycle:life('recorder'),output:originalPath,argv:recorderArgv,
      process:{...host,pid:104,startTicks:'125',exe:rec.resolvedPath,sha256:rec.sha256,argv:recorderArgv}}],
    originalLaunch:A.expectedLaunch(proxy),adaptedLaunch:A.launchOptions(A.expectedLaunch(proxy),{proxy,executable:binary.path,display:':1',env:{PATH:'/usr/bin:/bin'}}),
    directContexts:{before:2,after:2},loopbackPorts:{proxy:1234},boundaries:{before:boundary(),after:boundary()},
    recorderCopy:{original,retained},config,isolation,tools:write('tools.json',{scope:'SOURCE_CONTROL_ONLY'}),actualVideoPath:originalPath,phases,journal:journal.finish()};
  assert.equal(D.admitAdapter(value,tools,{pid:host.pid,phases}),true);
  const mutations=[x=>x.boundaries.after.passed=false,x=>x.boundaries.before.externalNavigationError='net::ERR_PROXY_CONNECTION_FAILED',
    x=>x.cleanup.recorder=false,x=>x.recorders[0].returncode=7,x=>x.recorders[0].lifecycle.faults.push({event:'unexpected-close'}),
    x=>x.display.lifecycle.cleanupRequested=false,x=>x.display.process.argv.push('--other'),x=>x.directContexts.after=1,
    x=>x.browserLifecycle.faults.push({event:'unexpected-disconnected'}),x=>x.phases.pop(),x=>x.recorders[0].output='/foreign/recording.webm',
    x=>x.isolationFailure=true,x=>x.adaptedLaunch.proxy=proxy,x=>x.recorderCopy.retained={...retained,sha256:'0'.repeat(64)},
    x=>x.finalCensus.failures.push({pid:9,code:'EACCES'}),x=>x.finalCensus.protocol='foreign',
    x=>x.finalCensus.executable='/foreign/browser',x=>x.recorders[0].process.startTicks='',
    x=>x.display.process.exe='/foreign/display',x=>x.display.process.pid=-1,
    x=>delete x.journal,x=>x.journal.complete=false,x=>x.journal.closed=false,x=>x.journal.observedBytes++,
    x=>x.journal.acknowledgedBytes++,x=>x.journal.retainedBytes++,x=>x.journal.events++,x=>x.journal.error='previous write failure'];
  for(const mutate of mutations){const changed=structuredClone(value);mutate(changed);assert.throws(()=>D.admitAdapter(changed,tools,{pid:host.pid,phases}));}
}));

function writeFault(target,mode){const raw=fs.writeSync,state={calls:0};
  fs.writeSync=function(fd,bytes,...args){if(fs.readlinkSync('/proc/self/fd/'+fd)!==target)return raw(fd,bytes,...args);
    state.calls++;assert.equal(args.length,0);if(mode==='zero')return 0;
    const prefix=bytes.subarray(0,Math.floor(bytes.length/2));raw(fd,prefix);
    if(mode==='throw')throw Object.assign(Error('injected EIO after actual prefix'),{code:'EIO'});
    return mode==='invalid'?bytes.length+1:mode==='lie'?bytes.length:prefix.length;};
  return {state,restore(){fs.writeSync=raw;}};}
test('actual stdout and stderr write faults preserve the real prefix and await child closure without a COMPLETE claim',()=>temporary(async root=>{
  const D=driver();for(const stream of ['stdout','stderr'])for(const mode of ['partial','zero','invalid','throw','lie']){
    const label=stream+'-'+mode,target=path.join(root,label+'.'+stream),fault=writeFault(target,mode);let got;
    try{got=await D.runChild([process.execPath,'-e','process.'+stream+'.write("q".repeat(1000))'],root,label,3,{PATH:'/usr/bin:/bin'});}
    finally{fault.restore();}
    assert.equal(fault.state.calls,1,stream+'/'+mode);assert.equal(got.complete,false);assert.equal(got.observedBytes[stream],1000);
    assert.equal(got.acknowledgedBytes[stream],mode==='partial'?500:mode==='lie'?1000:0);
    assert.equal(got.retainedBytes[stream],mode==='zero'?0:500);assert.equal(got.streams[stream].bytes,fs.statSync(target).size);
    assert.equal(got.streamsClosed[stream],true);assert.equal(got.groupStopped,true);assert.ok(got.retentionErrors[stream]);
    assert.throws(()=>D.admitProcessRetention({...got,complete:true}));
    assert.throws(()=>process.kill(-got.pid,0),error=>error.code==='ESRCH');
  }
}));
test('currentness witness and replay process intake independently rechecks closed streams and all byte counts',()=>temporary(async root=>{
  const D=driver(),got=await D.runChild([process.execPath,'-e','process.stdout.write("actual bytes")'],root,'ordinary',3,{PATH:'/usr/bin:/bin'});
  assert.equal(got.complete,true);assert.equal(D.admitProcessRetention(got),true);
  for(const change of [x=>delete x.acknowledgedBytes,x=>x.acknowledgedBytes.stdout++,x=>x.retainedBytes.stdout++,x=>x.observedBytes.stdout++,
    x=>x.streamsClosed.stdout=false,x=>x.retentionErrors.stdout='prior write fault',x=>x.streamLimit++,x=>x.streams.stdout.bytes++]){
    const altered=structuredClone(got);change(altered);assert.throws(()=>D.admitProcessRetention(altered));}
  fs.appendFileSync(got.streams.stdout.path,'changed');assert.throws(()=>D.admitProcessRetention(got));
}));
test('recorder prefix short zero invalid and throwing writes stop once and report actual file truncation',()=>temporary(root=>{
  const S=feature(),dir=path.join(root,'.video-baseline');fs.mkdirSync(dir);const original=path.join(dir,'actual.webm');fs.writeFileSync(original,'q'.repeat(1000));
  for(const mode of ['partial','zero','invalid','throw','lie']){const target=path.join(root,mode+'.webm'),fault=writeFault(target,mode);let got;
    try{got=S.recorderPrefix(dir,original,target,{limit:1000});}finally{fault.restore();}
    assert.equal(fault.state.calls,1);assert.equal(got.complete,false);assert.equal(got.retentionComplete,false);assert.ok(got.error);
    assert.equal(got.observedBytes,1000);assert.equal(got.acknowledgedBytes,mode==='partial'?500:mode==='lie'?1000:0);
    assert.equal(got.retainedBytes,mode==='zero'?0:500);assert.equal(got.retained.bytes,fs.statSync(target).size);assert.equal(got.truncated,true);
    assert.equal(got.sourceStable,true);assert.equal(fs.readFileSync(original).length,1000);}
}));
test('event journal write failures remain sticky without recursive logging and finalize the real incomplete prefix',()=>temporary(root=>{
  const A=adapter();for(const mode of ['partial','zero','invalid','throw','lie']){const target=path.join(root,mode+'.jsonl');let failures=0;
    const journal=A.eventJournal(target,{onFailure:()=>{failures++;}}),fault=writeFault(target,mode);
    try{assert.doesNotThrow(()=>journal.event('source-control',{bytes:'q'.repeat(1000)}));
      // An acknowledged full count with missing physical bytes is discovered at finalization.
      if(mode!=='lie')assert.doesNotThrow(()=>journal.event('another-source-control',{bytes:'later event is not retried'}));
      const got=journal.finish();assert.equal(got.complete,false);assert.equal(got.closed,true);assert.ok(got.error);assert.equal(failures,1);
      assert.equal(fault.state.calls,1);assert.equal(got.retainedBytes,fs.statSync(target).size);assert.equal(got.identity.bytes,got.retainedBytes);
      assert.equal(got.acknowledgedBytes,mode==='partial'?got.retainedBytes:mode==='lie'?got.observedBytes:0);
      assert.equal(journal.finish(),got);assert.throws(()=>A.admitJournal({...got,complete:true,error:null}));
    }finally{fault.restore();}}
}));
test('journal completion follows fsync close and descriptor accounting and refuses a later append',()=>temporary(root=>{
  const A=adapter(),journal=A.eventJournal(path.join(root,'ordinary.jsonl'));const row=journal.event('phase',{phase:'admission',seconds:30});
  assert.equal(journal.state.complete,false);const got=journal.finish();assert.equal(A.admitJournal(got),true);
  assert.deepEqual(JSON.parse(fs.readFileSync(got.identity.path)),row);assert.equal(got.observedBytes,got.acknowledgedBytes);assert.equal(got.retainedBytes,got.identity.bytes);
  assert.doesNotThrow(()=>journal.event('after-close',{}));assert.equal(got.complete,false);assert.match(got.error,/finalization/);
  for(const mode of ['fsync','close']){const file=path.join(root,mode+'.jsonl'),bad=A.eventJournal(file),name=mode+'Sync',raw=fs[name];let injected=false;bad.event('source-control',{});
    fs[name]=function(fd){if(!injected&&fs.readlinkSync('/proc/self/fd/'+fd)===file){injected=true;if(mode==='close')raw(fd);throw Error('injected '+mode+' failure');}return raw(fd);};
    try{const result=bad.finish();assert.equal(result.complete,false);assert.ok(result.error);assert.equal(result.retainedBytes,fs.statSync(file).size);}
    finally{fs[name]=raw;}}
}));
test('one-write accounting refuses negative fractional nonfinite and over-request counts without inventing acknowledged bytes',()=>temporary(root=>{
  const S=feature(),file=path.join(root,'invalid-counts'),fd=fs.openSync(file,'wx',0o600),raw=fs.writeSync;
  try{for(const count of [-1,0.5,NaN,Infinity,5,'4',undefined]){let calls=0;fs.writeSync=()=>{calls++;return count;};const got=S.writeOnce(fd,Buffer.from('four'));
      assert.equal(calls,1);assert.equal(got.acknowledgedBytes,0);assert.match(got.error,/invalid/);}}
  finally{fs.writeSync=raw;fs.closeSync(fd);}
}));
test('the complete source-only return population retains more than the original five copies without adding calls',()=>temporary(async root=>{
  const S=feature(),R=require('./r002f_bfcache_replay.cjs'),sink=S.returnSink(path.join(root,'returns'));let calls=0;
  const bytes=png(),capture=async()=>{calls++;return bytes;},tags=['ref-present',...[1,2,3].flatMap(k=>Array(5).fill('restore-'+k)),'ref-absent'];
  for(const tag of tags)assert.equal(await sink.capture(capture,{type:'png'},tag),bytes);
  const values={rect:{x:20,y:20,w:40,h:40},before:{cur:false,ready:false},after:{cur:false,ready:false},truth:null,
    log:{ev:[],frames:[],c:0},hiddenone:'source-control',hiddentwo:'source-control',hiddenthree:'source-control',
    isolation:{allowedExternal:0,externalAttempts:0,externalByLayerHostOutcome:{}}};
  for(const [key,value] of Object.entries(values))assert.equal(sink.value(key,value),value);
  S.writeJson(path.join(root,'retention.json'),sink.finish());
  S.writeJson(path.join(root,'baseline.json'),{label:'baseline',engine:'chromium',route:'bfcache',startISO:S.CLOCK,events:3,fault:false,headed:true,
    scope:'SOURCE_CONTROL_ONLY',valid:false,void:['no native observation'],rect:values.rect,before:values.before,after:values.after,truth:values.truth,
    hiddenChecks:['source-control','source-control','source-control'],isolation:{allowedExternal:0,externalAttempts:0,byLayerHostOutcome:{}}});
  const population=R.population(root,'baseline');assert.equal(calls,17);assert.equal(population.retained.value.received,17);assert.equal(population.shots.length,15);
  assert.equal(population.body.valid,false);assert.equal(population.retained.value.captureCallsAdded,0);
  const altered=JSON.parse(fs.readFileSync(path.join(root,'retention.json')));altered.frames[2].calledNs='0';
  fs.writeFileSync(path.join(root,'retention.json'),JSON.stringify(altered));assert.throws(()=>R.population(root,'baseline'),/order/);
}));
