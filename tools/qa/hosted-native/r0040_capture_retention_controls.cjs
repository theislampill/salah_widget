'use strict';
// Offline controls execute the pinned capture driver, with bounded dependencies.
// No control starts a browser or treats the synthetic PNGs as native evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {spawnSync}=require('node:child_process');
const entry=path.join(__dirname,'retain_r0040_capture.cjs');
const driver=path.resolve(__dirname,'../r0040/capture.cjs');
test('capture retention entry exists before its source contracts run',()=>assert.ok(fs.existsSync(entry)));

if(fs.existsSync(entry)) {
  const {CaptureRetention,verifyDriver,verifySourceRows,verifyOutputs,verifyIsolation}=require(entry);
  function temporary(t) {const root=fs.mkdtempSync(path.join(os.tmpdir(),'capture-retention-'));
    t.after(()=>fs.rmSync(root,{recursive:true,force:true}));return root;}
  function child() {
    const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),{EventEmitter}=require('node:events');
    const [entry,driver,root,mode,actualHistory,actualMain]=process.argv.slice(1);
    const {CaptureRetention,executeOriginal}=require(entry),load=Module.createRequire(driver);
    const history=actualHistory||path.join(root,'history'),main=actualMain||path.join(root,'main'),out=path.join(root,'original');
    const helper=path.resolve(history,'tools/qa/precip_eval_lib.cjs');
    if(!actualHistory){fs.mkdirSync(path.join(history,'tools/qa'),{recursive:true});
      fs.writeFileSync(path.join(history,'tools/qa/precip_declared_gain.json'),JSON.stringify({enforceDeclaredGain:true,G:100,T:1/60}));
      fs.writeFileSync(path.join(history,'tools/qa/precip_models_geom.js'),'/* bounded geometry double */');
      fs.writeFileSync(path.join(history,'tools/qa/precip_models.js'),'window.__R0040_STUDY;');}
    if(!actualMain){fs.mkdirSync(path.join(main,'tests'),{recursive:true});fs.writeFileSync(path.join(main,'index.html'),'bounded product double');
      fs.copyFileSync(path.resolve(path.dirname(driver),'../../../tests/r0002-ordinary.json'),path.join(main,'tests/r0002-ordinary.json'));}
    const trace={continued:[],aborted:[],routes:[],streamFsyncs:0,streamPngWrites:0,rawCdp:true};let inStream=false,reportBeforeClose=null;
    const hash=b=>require('node:crypto').createHash('sha256').update(b).digest('hex');
    const profile=JSON.parse(fs.readFileSync(path.join(history,'tools/qa/precip_declared_gain.json')));
    const source={code:63,amount:1.25,interval:900,source:'current',permission:'on'};
    const geometry={card:[0,0,325,530],header:[5,5,300,20],footer:[5,500,300,20],rows:[],glass:'blur(2px)'};
    const sample={at:1000,geometry,tuple:[63,1.25,900,'on','M1','flat',100,1/60,5],phaseMs:1,poseMs:1,treatment:'common',rects:[]};
    const page=new EventEmitter();page.clock={async install(){},async resume(){}};
    const ctx=new EventEmitter(),browser=new EventEmitter();
    async function routed(url,actionFailure=false){
      const req={url:()=>url,method:()=> 'GET',resourceType:()=> 'script',failure:()=>({errorText:'controlled network failure'})};
      ctx.emit('request',req);
      const raw={request:()=>req,async continue(){trace.continued.push(url);},async abort(){trace.aborted.push(url);if(mode==='veto-disconnect')browser.emit('disconnected');},
        async fulfill(){if(actionFailure)throw Error('late fulfill failure');}};
      try{await ctx.handler(raw);ctx.emit('requestfinished',req);}catch(e){ctx.emit('requestfailed',req);throw e;}
    }
    page.goto=async url=>{await routed(url);await routed('https://unknown.invalid/blocked');};
    page.waitForFunction=async()=>{};page.addScriptTag=async()=>{};
    page.evaluate=async expression=>{
      const text=String(expression);
      if(typeof expression==='string')return {prayer:true,rsStatus:'ready',rsRenders:1};
      if(text.includes('code:w?.code'))return mode==='oracle-failure'?{...source,interval:1}:source;
      if(text.includes('window.__PM.params'))return profile;
      if(text.includes('moonFresh:'))return {sun:40,moon:0,moonAltitude:-20,moonFresh:true};
      if(text.includes('window.__r0040Sample()'))return sample;
      if(text.includes('samples.sort'))return {n:120,mean:0,p95:0,resolutionLimited:true};
      if(text.includes('Date.now'))return 1790154360000;
    };
    page.waitForTimeout=async()=>{if(mode==='timeout')await new Promise(()=>setInterval(()=>{},1000));};
    ctx.route=async(pattern,handler)=>{trace.routes.push(pattern);ctx.handler=handler;};
    ctx.newPage=async()=>{assertRoute();ctx.emit('page',page);return page;};
    function assertRoute(){if(trace.routes[0]!=='**/*')throw Error('page created before route');}
    const cdp=new EventEmitter();cdp.send=async(name,args)=>{
      if(name==='Page.getFrameTree')return {frameTree:{frame:{id:'bounded-frame'}}};
      if(name==='Page.createIsolatedWorld')return {executionContextId:1};
      if(name==='Runtime.evaluate')return {result:{value:args.expression.includes('globalThis.active=false')?[sample,{...sample,at:1017}]:true}};
      if(name==='Page.startScreencast'){inStream=true;
        for(let i=0;i<2;i++)cdp.emit('Page.screencastFrame',{sessionId:i,data:Buffer.from('bounded PNG '+i).toString('base64'),metadata:{timestamp:1+i*.017}});}
      if(name==='Page.stopScreencast')inStream=false;
      return {};
    };cdp.detach=async()=>{};
    ctx.newCDPSession=async rawPage=>{if(rawPage!==page)trace.rawCdp=false;return cdp;};
    ctx.close=async()=>{
      const report=path.join(out,'capture.json');if(fs.existsSync(report))reportBeforeClose=hash(fs.readFileSync(report));
      if(mode==='late-pageerror')page.emit('pageerror',Error('late page fault'));
      if(mode==='late-page-crash')page.emit('crash');
      if(mode==='unexpected-disconnect')browser.emit('disconnected');
      if(mode==='late-request')try{await routed('https://api.rainviewer.com/late',true);}catch(_){}
      if(mode==='late-network'){const req={url:()=> 'http://127.0.0.1:8765/late',method:()=> 'GET',resourceType:()=> 'image',failure:()=>({errorText:'late network failure'})};
        ctx.emit('request',req);await ctx.handler({request:()=>req,async continue(){},async abort(){},async fulfill(){}});ctx.emit('requestfailed',req);}
      if(mode==='close-failure')throw Error('original context close fault');
      ctx.emit('close');page.emit('close');
    };
    browser.newContext=async options=>{if(options.serviceWorkers!=='block')throw Error('service workers admitted');return ctx;};
    browser.close=async()=>{if(mode==='veto-crash')page.emit('crash');browser.emit('disconnected');if(mode==='veto-close')throw Error('secondary browser close fault');};
    const fakeHelper={SITES:{madinah:{}},sceneTimes:()=>({'solar-noon':1790154000000}),RECTS:'bounded rectangles',
      async serve(){const srv=new EventEmitter();srv.close=()=>{setImmediate(()=>{srv.emit('close');if(mode==='late-server-error')srv.emit('error',Error('late server fault'));});return srv;};return {srv,base:'http://127.0.0.1:8765'};},
      async waitReady(){return {state:{prayer:true,rsStatus:'ready'}};},
      async openScene(browser,base,ordinary,options){const ctx=await browser.newContext({serviceWorkers:'block'});
        const log={continuedExternal:[],errors:[],aborted:[]};
        await ctx.route('**/*',r=>{
          const url=r.request().url();
          if(url.startsWith(base)||mode.startsWith('veto'))return r.continue();
          if(url.includes('api.rainviewer.com'))return r.fulfill({body:'{}'});
          log.aborted.push(url);return r.abort();});
        const page=await ctx.newPage();page.on('pageerror',e=>log.errors.push(e.message));await page.goto(base+'/index.html');
        return {ctx,page,log,url:'/index.html'};}};
    // An explicit actual-helper run exercises its original routes/clock/cleanup.
    // The native CLI always uses manifest-bound source checks, unlike this double.
    const expected={schema:3,evidenceClass:'native-controlled-capture',engine:'chromium',block:'bday',condition:'moderate',model:'M1',
      design:'revised',treatment:'common',dispersion:'common',options:null,method:'compositor-png',clock:'browser-native-epoch-ms',utcMs:1790154360000,source};
    const pins={productSha:hash(fs.readFileSync(path.join(main,'index.html'))),geometrySha:hash(fs.readFileSync(path.join(history,'tools/qa/precip_models_geom.js'))),
      rendererSha:hash(fs.readFileSync(path.join(history,'tools/qa/precip_models.js'))),options:null,evidenceClass:'native-controlled-capture'};
    const retain=new CaptureRetention(path.join(root,'evidence'),{out,expected,pins});
    const originalFsync=fs.fsyncSync,originalWrite=fs.writeFileSync;
    fs.fsyncSync=(...args)=>{if(inStream)trace.streamFsyncs++;return originalFsync(...args);};
    fs.writeFileSync=(file,...args)=>{if(inStream&&typeof file==='string'&&file.endsWith('.png'))trace.streamPngWrites++;return originalWrite(file,...args);};
    if(mode==='final-fsync'||mode==='veto-fsync'){
      const record=retain.journal.record.bind(retain.journal);
      retain.journal.record=(event,value)=>{if(event!=='driver-process-ended')return record(event,value);
        const saved=fs.fsyncSync;fs.fsyncSync=()=>{throw Error('final journal fsync fault');};
        try{return record(event,value);}finally{fs.fsyncSync=saved;}};
    }
    if(mode==='receipt-fsync'){
      const publish=retain.journal.publish.bind(retain.journal);
      retain.journal.publish=(...args)=>{const saved=fs.fsyncSync;fs.fsyncSync=()=>{throw Error('final receipt fsync fault');};
        try{return publish(...args);}finally{fs.fsyncSync=saved;}};
    }
    process.env.R0040_DISPERSION='common';delete process.env.R0040_OPTIONS;
    executeOriginal(driver,['bounded-playwright',history,main,out,'chromium','bday','moderate','M1'],retain,request=>{
      if(request==='bounded-playwright')return {chromium:{async launch(){return browser;}}};
      if(request===helper&&!actualHistory)return fakeHelper;return load(request);
    });
    process.on('exit',()=>{trace.reportBeforeClose=reportBeforeClose;const report=path.join(out,'capture.json');
      trace.reportAfterClose=fs.existsSync(report)?hash(fs.readFileSync(report)):null;
      originalWrite(path.join(root,'control-trace.json'),JSON.stringify(trace));});
  }
  function run(t,mode,actual=false){const root=temporary(t);const result=spawnSync(process.execPath,['-e',`(${child.toString()})()`,entry,driver,root,mode,
    actual?process.env.R0040_CAPTURE_HISTORY_CONTROL||'':'',actual?process.env.R0040_CAPTURE_MAIN_CONTROL||'':''],
    {encoding:'utf8',timeout:mode==='timeout'?1800:10000,env:{...process.env,NODE_OPTIONS:''}});
    const evidence=path.join(root,'evidence'),events=fs.readFileSync(path.join(evidence,'events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    const receipt=fs.existsSync(path.join(evidence,'final-admission.json'))?JSON.parse(fs.readFileSync(path.join(evidence,'final-admission.json'))):null;
    const trace=fs.existsSync(path.join(root,'control-trace.json'))?JSON.parse(fs.readFileSync(path.join(root,'control-trace.json'))):null;
    return {root,result,events,receipt,trace};}
  test('unchanged capture report survives complete cleanup and raw CDP has no added per-frame fsync or copy',t=>{
    const r=run(t,'complete',true);assert.equal(r.result.status,0,r.result.stderr);
    assert.equal(r.receipt.status,'ADMITTED_FOR_OFFLINE_VERIFICATION');assert.equal(r.receipt.nativeQualification,'NOT_VERIFIED');
    assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.equal(r.trace.rawCdp,true);
    assert.equal(r.trace.streamFsyncs,0);assert.equal(r.trace.streamPngWrites,2);
    assert.equal(r.events.some(x=>x.event==='cell-body-completed'),false);
    assert.deepEqual(r.receipt.originalPngs.map(x=>x.file),['f00000.png','f00001.png']);
  });
  for(const [mode,message] of [['close-failure','original context close fault'],['late-pageerror','late page fault'],['late-page-crash','page crashed'],
    ['unexpected-disconnect','browser disconnected before original close'],['late-request','late fulfill failure'],['late-network','late network failure']]){
    test('final capture receipt preserves '+mode+' after the original report',t=>{
      const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.receipt.status,'FAILED');
      assert.ok(JSON.stringify(r.receipt).includes(message));assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
      assert.ok(r.trace.reportAfterClose);assert.equal(r.receipt.originalExitCode,mode==='close-failure'?1:0);
    });
  }
  test('the original source assertion remains a failure and no success report is synthesized',t=>{
    const r=run(t,'oracle-failure');assert.equal(r.result.status,1);assert.match(r.result.stderr,/unexpected admitted source/);
    assert.equal(r.receipt.originalReport,null);assert.equal(r.receipt.status,'FAILED');
    assert.ok(r.events.some(x=>x.event==='driver-error-output'));
  });
  test('a late uncaught server fault retains its diagnostic without suppressing original fatal behavior',t=>{
    const r=run(t,'late-server-error');assert.equal(r.result.status,1);assert.equal(r.receipt.originalExitCode,1);
    assert.match(r.result.stderr,/late server fault/);assert.ok(r.events.some(x=>x.event==='uncaught-exception'&&x.error.message==='late server fault'));
    assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.equal(r.receipt.status,'FAILED');
  });
  test('guard veto prevents actual external continuation and retains exit86 over cleanup and retention faults',t=>{
    for(const mode of ['veto','veto-close','veto-fsync','veto-crash','veto-disconnect']){const r=run(t,mode);assert.equal(r.result.status,86,r.result.stderr);
      assert.ok(r.events.some(x=>x.event==='external-continuation-vetoed'));
      assert.equal(r.trace.continued.some(x=>x.startsWith('https://unknown')),false);assert.ok(r.trace.aborted.includes('https://unknown.invalid/blocked'));
      if(r.receipt){assert.equal(r.receipt.exitCode,86);assert.equal(r.receipt.continuationVetoed,true);}}
  });
  test('the complete original report cannot hide final journal or final receipt fsync failure',t=>{
    for(const mode of ['final-fsync','receipt-fsync']){const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);
      assert.ok(r.trace.reportAfterClose);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
      assert.equal(r.receipt,null);assert.match(r.result.stderr,/final.*fsync fault/);}
  });
  test('outer timeout retains original partial PNGs and journal prefix without an admission receipt',t=>{
    const r=run(t,'timeout');assert.equal(r.result.signal,'SIGTERM');assert.equal(r.receipt,null);
    assert.deepEqual(fs.readdirSync(path.join(r.root,'original')).sort(),['f00000.png','f00001.png']);
    assert.ok(r.events.some(x=>x.event==='scene-opened'));assert.equal(r.events.some(x=>x.event==='driver-process-ended'),false);
  });
  test('source digest checks reject driver and bound source drift before their code executes',t=>{
    verifyDriver(driver);const root=temporary(t),copy=path.join(root,'capture.cjs');fs.copyFileSync(driver,copy);fs.appendFileSync(copy,'\n// drift\n');
    assert.throws(()=>verifyDriver(copy),/digest/);
    const expected={file:{bytes:fs.statSync(driver).size,sha256:require('node:crypto').createHash('sha256').update(fs.readFileSync(driver)).digest('hex')}};
    fs.copyFileSync(driver,path.join(root,'file'));verifySourceRows(root,expected);fs.appendFileSync(path.join(root,'file'),' ');
    assert.throws(()=>verifySourceRows(root,expected),/source.*file/);
    const input=path.join(root,'input'),alias=path.join(root,'alias');fs.mkdirSync(input);fs.symlinkSync(input,alias);
    verifyOutputs(path.join(root,'out'),path.join(root,'evidence'),[input]);
    assert.throws(()=>verifyOutputs(path.join(alias,'out'),path.join(root,'evidence'),[input]),/outside source/);
    fs.symlinkSync(path.join(root,'absent'),path.join(root,'broken'));
    assert.throws(()=>verifyOutputs(path.join(root,'broken'),path.join(root,'evidence'),[input]),/fresh/);
    assert.throws(()=>verifyIsolation(undefined),/receipt/);
  });
  test('route installation is required before page creation and raw CDP receives the original page',async t=>{
    const root=temporary(t),r=new CaptureRetention(path.join(root,'evidence'),{out:path.join(root,'out'),expected:{},pins:{}});
    t.after(()=>r.journal.close());r.scene={base:'http://127.0.0.1:8765'};
    let created=0;const page={on(){}},cdp={},raw={on(){},async route(){},async newPage(){created++;return page;},async newCDPSession(p){assert.equal(p,page);return cdp;}};
    const ctx=r.wrapContext(raw);await assert.rejects(ctx.newPage(),/route.*before.*page/);assert.equal(created,0);
    await ctx.route('**/*',()=>{});const wrapped=await ctx.newPage();assert.equal(await ctx.newCDPSession(wrapped),cdp);
  });
  test('CLI isolation refusal precedes source, helper and browser imports or evidence creation',t=>{
    const root=temporary(t),env={...process.env,NODE_OPTIONS:''};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
    const r=spawnSync(process.execPath,[entry,'--driver','unopened-driver','--manifest','unopened-manifest','--prepared','unopened-prepared',
      '--preparation-process','unopened-process','--evidence',path.join(root,'evidence'),'--','unopened-browser','unopened-history','unopened-main',path.join(root,'out'),
      'chromium','bday','moderate','M1'],{encoding:'utf8',env});
    assert.equal(r.status,1);assert.match(r.stderr,/admitted isolation receipt required/);assert.equal(fs.existsSync(path.join(root,'evidence')),false);
  });
}
