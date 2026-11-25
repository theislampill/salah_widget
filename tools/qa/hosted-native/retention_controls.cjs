'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawnSync} = require('node:child_process');
const entry = path.join(__dirname, 'retain_r0040.cjs');

test('retention wrapper is available before exercising evidence contracts', () => {
  assert.ok(fs.existsSync(entry), 'missing R0040 evidence-retention wrapper');
});

if (fs.existsSync(entry)) {
  const {RainRetention, verifyInputs, verifyIsolation} = require(entry);
  const oracle = require('../r0040/native-option-oracle.cjs');
  const good = {width:325,height:530,current:1.25,sunElevation:40,lit:'on',visible:30,
    animation:'fall',slant:142,computedAxis:-45,duration:'.8s',inlineDuration:'.8s',playState:'running'};
  function setup(t) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'rain-retention-'));
    t.after(() => fs.rmSync(root, {recursive:true,force:true}));
    const retain = new RainRetention(path.join(root, 'evidence'));
    t.after(() => retain.journal.close());
    return {root,retain,events:() => fs.readFileSync(path.join(root,'evidence','events.jsonl'),'utf8')
      .trim().split('\n').map(JSON.parse)};
  }
  function context() {
    const calls = [];
    const page = {on(){}, async evaluate(){return good;}, async screenshot(options){
      calls.push('screenshot'); const data = Buffer.from('controlled-png-bytes');
      if(options.path) fs.writeFileSync(options.path,data); return data;
    }};
    const ctx = {async route(pattern,handler){calls.push('route');this.handler=handler;},
      async newPage(){calls.push('newPage');return page;},async addInitScript(){},
      async close(){calls.push('close');}};
    return {ctx,page,calls};
  }
  async function open(retain, raw) {
    const cell = retain.beginCell('http://127.0.0.1:8765', {utcMs:123,wx:{code:63}});
    const wrapped = retain.wrapContext(raw.ctx, cell);
    await wrapped.route('**/*', r => r.abort());
    cell.page = await wrapped.newPage();
    cell.sceneLog = {continuedExternal:[],errors:[]};
    return {cell,wrapped};
  }
  test('completed cell and actual oracle failure remain durable without final report', async t => {
    const {root,retain,events} = setup(t), original = retain.wrapOracle(oracle);
    const first = await open(retain,context());
    original.check('day-rain',good,1.25);
    await first.cell.page.screenshot({path:path.join(root,'first.png')});
    const assertions = retain.wrapAssert(assert);
    assertions.equal(0,0); assertions.deepEqual([],[]);
    await first.wrapped.close();
    const second = await open(retain,context());
    let caught;
    try {original.check('day-drizzle',{...good,computedAxis:0},1.25);} catch(error){caught=error;}
    assert.ok(caught instanceof assert.AssertionError);
    await second.wrapped.close();
    assert.equal(events().filter(x=>x.event==='cell-body-completed').length,1);
    assert.ok(events().some(x=>x.event==='oracle-threw'&&x.error.message===caught.message));
    assert.ok(events().some(x=>x.event==='screenshot-received'&&x.kind==='failure-diagnostic'));
    assert.equal(fs.existsSync(path.join(root,'native-options.json')),false);
  });
  test('route installation precedes page creation and uninstalled contexts refuse creation', async t => {
    const {retain,events} = setup(t), raw = context();
    const cell=retain.beginCell('http://127.0.0.1:8765',{}), wrapped=retain.wrapContext(raw.ctx,cell);
    await assert.rejects(wrapped.newPage(), /route.*before.*page/i);
    assert.deepEqual(raw.calls,[]);
    await wrapped.route('**/*',r=>r.abort()); await wrapped.newPage();
    assert.deepEqual(raw.calls,['route','newPage']);
    assert.ok(events().findIndex(x=>x.event==='route-installed')<events().findIndex(x=>x.event==='page-created'));
  });
  test('request ledger records actual abort and vetoes attempted external continuation', async t => {
    const {retain,events}=setup(t),raw=context();
    const cell=retain.beginCell('http://127.0.0.1:8765',{}),ctx=retain.wrapContext(raw.ctx,cell);
    await ctx.route('**/*',r=>r.continue());
    let continued=0,aborted=0;
    const request={url:()=> 'https://unknown.invalid/payload',method:()=> 'GET',resourceType:()=> 'script'};
    await assert.rejects(raw.ctx.handler({request:()=>request,continue:async()=>{continued++;},abort:async()=>{aborted++;}}),/external continuation/);
    assert.equal(continued,0); assert.equal(aborted,1);
    assert.ok(events().some(x=>x.event==='request-action'&&x.action==='continue'&&x.refused));
    assert.ok(events().some(x=>x.event==='request-action-completed'&&x.action==='abort'));
  });
  test('diagnostic screenshot error retains the original oracle exception',async t=>{
    const {retain,events}=setup(t),raw=context();raw.page.screenshot=async()=>{throw Error('capture unavailable');};
    const {wrapped}=await open(retain,raw);let caught;
    try{retain.wrapOracle(oracle).check('day-rain',{...good,width:0},1.25);}catch(error){caught=error;}
    await wrapped.close();
    assert.ok(caught instanceof assert.AssertionError);
    assert.ok(events().some(x=>x.event==='diagnostic-failed'&&x.error.message==='capture unavailable'));
    assert.ok(events().some(x=>x.event==='oracle-threw'&&x.error.message===caught.message));
  });
  test('source drift and absent namespace receipt refuse before driver loading',t=>{
    const {root}=setup(t),driver=path.join(root,'native-options.cjs');fs.writeFileSync(driver,'changed');
    assert.throws(()=>verifyInputs(driver,root),/digest/);
    assert.throws(()=>verifyIsolation(undefined),/receipt/);
  });
  function originalDriverChild() {
    const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
    const [entry,driver,root,historical,veto,finalization]=process.argv.slice(1);
    const {RainRetention,executeOriginal}=require(entry);
    const candidate=path.join(root,'candidate'),out=path.join(root,'original');
    fs.mkdirSync(path.join(candidate,'tests'),{recursive:true});
    fs.copyFileSync(path.resolve(path.dirname(driver),'../../../tests/r0002-ordinary.json'),path.join(candidate,'tests/r0002-ordinary.json'));
    let number=0,active;
    const ids=['day-rain','day-drizzle','day-thunder','night','twilight','reduced-none','reduced-still','motion-full','dry'];
    const browser={async newContext(){
      const index=++number;
      const page={on(){},clock:{async install(){},async resume(){}},
        async goto(url){for(const item of [url,'https://unknown.invalid/payload'])
          await context.handler({request:()=>({url:()=>item,method:()=> 'GET',resourceType:()=> 'script'}),
            async continue(){},async abort(){},async fulfill(){}});},
        async waitForFunction(){},async waitForTimeout(){},
        async evaluate(expression){
          if(typeof expression==='string')return {prayer:true,rsStatus:'ready',rsRenders:1};
          if(expression.toString().includes('Date.now'))return Date.UTC(2026,8,11,12);
          if(finalization){const id=ids[index-1];return {
            width:325,height:530,current:active.wx.precip,sunElevation:id==='night'?-20:id==='twilight'?-5:40,
            moonlight:0,lit:id==='night'?'off':'on',visible:['night','reduced-none','dry'].includes(id)?0:30,
            animation:'fall',slant:142,computedAxis:-45,duration:'.8s',inlineDuration:'.8s',
            playState:id==='reduced-still'?'paused':'running'};}
          return {width:325,height:530,current:index===1?1.25:.3,sunElevation:40,moonlight:0,lit:'on',visible:30,
            animation:'fall',slant:142,computedAxis:index===1?-45:0,duration:'.8s',inlineDuration:'.8s',playState:'running'};
        },async screenshot(options){const data=Buffer.from('controlled-png-bytes');if(options.path)fs.writeFileSync(options.path,data);return data;}};
      const context={async route(pattern,handler){this.handler=handler;},async newPage(){return page;},
        async addInitScript(){},async close(){}};return context;
    },async close(){}};
    const fakeHelper={SITES:{madinah:{}},sceneTimes:()=>({'solar-noon':123,'night-early':123,'blue-hour':123}),
      async serve(){return {srv:{close(){}},base:'http://127.0.0.1:8765'};},async waitReady(){return {state:{ready:true}};},
      async openScene(wrapper,base,ordinary,options){active=options;const ctx=await wrapper.newContext({serviceWorkers:'block'});
        await ctx.route('**/*',r=>r.request().url().startsWith(base)||veto?r.continue():r.abort());
        const page=await ctx.newPage();await page.goto(base+'/index.html');
        return {ctx,page,log:{continuedExternal:[],errors:[]},url:'/index.html'};}};
    const load=Module.createRequire(driver),history=historical||path.join(root,'history'),helper=path.resolve(history,'tools/qa/precip_eval_lib.cjs');
    if(historical)require(entry).verifyInputs(driver,history);
    const retain=new RainRetention(path.join(root,'evidence'));
    if(finalization==='fsync-failure'){
      const realRecord=retain.journal.record.bind(retain.journal),realFsync=fs.fsyncSync;
      retain.journal.record=(event,value)=>{
        if(event==='driver-process-ended')fs.fsyncSync=()=>{throw Error('injected final fsync failure');};
        try{return realRecord(event,value);}finally{fs.fsyncSync=realFsync;}
      };
    }
    if(finalization==='close-failure'){
      const realClose=retain.journal.close.bind(retain.journal);
      retain.journal.close=()=>{realClose();throw Error('injected final close failure');};
    }
    executeOriginal(driver,['offline-playwright-control',history,candidate,out,'chromium'],
      retain,request=>{
        if(request==='offline-playwright-control')return {chromium:{async launch(){return browser;}}};
        if(request===helper&&!historical)return fakeHelper;
        return load(request);
      });
  }
  test('unchanged original driver aborts on second oracle and retains first completed cell',t=>{
    const root=fs.mkdtempSync(path.join(os.tmpdir(),'rain-driver-retention-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
    const driver=path.resolve(__dirname,'../r0040/native-options.cjs');
    const result=spawnSync(process.execPath,['-e',`(${originalDriverChild.toString()})()`,entry,driver,root,
      process.env.R0040_HISTORICAL_CONTROL||''],{encoding:'utf8'});
    assert.equal(result.status,1,result.stderr);
    assert.equal(fs.existsSync(path.join(root,'original/native-options.json')),false);
    assert.equal(fs.existsSync(path.join(root,'original/day-rain.png')),true);
    const events=fs.readFileSync(path.join(root,'evidence/events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    assert.equal(events.filter(x=>x.event==='cell-body-completed').length,1);
    assert.equal(events.find(x=>x.event==='oracle-threw').error.name,'AssertionError');
    assert.equal(events.filter(x=>x.event==='oracle-called')[1].id,'day-drizzle');
    assert.ok(events.some(x=>x.event==='request-action-completed'&&x.action==='abort'&&x.url==='https://unknown.invalid/payload'));
    assert.ok(events.some(x=>x.event==='screenshot-received'&&x.kind==='failure-diagnostic'));
    assert.equal(events.at(-1).exitCode,1);
  });
  test('original driver failure after an external continuation veto exits with the boundary stop code',t=>{
    const root=fs.mkdtempSync(path.join(os.tmpdir(),'rain-veto-retention-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
    const driver=path.resolve(__dirname,'../r0040/native-options.cjs');
    const result=spawnSync(process.execPath,['-e',`(${originalDriverChild.toString()})()`,entry,driver,root,'','veto'],{encoding:'utf8'});
    assert.equal(result.status,86,result.stderr);
    const events=fs.readFileSync(path.join(root,'evidence/events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    assert.ok(events.some(x=>x.event==='external-continuation-vetoed'));
    assert.equal(events.some(x=>x.event==='request-action-completed'&&x.action==='continue'&&x.url.startsWith('https://unknown')),false);
    assert.equal(events.at(-1).continuationVetoed,true);
  });
  test('CLI refuses missing boundary receipt before loading driver or browser',t=>{
    const {root}=setup(t),env={...process.env};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
    const result=spawnSync(process.execPath,[entry,'--driver','unopened-driver','--evidence',path.join(root,'cli-evidence'),
      '--','unopened-browser','unopened-history','unopened-root',path.join(root,'cli-output'),'chromium'],{encoding:'utf8',env});
    assert.equal(result.status,1);assert.match(result.stderr,/admitted isolation receipt required/);
    assert.equal(fs.existsSync(path.join(root,'cli-evidence')),false);
  });
  test('final journal fsync failure makes the original nine-cell run nonzero without changing its report',t=>{
    const reports=[];
    for(const mode of ['complete','fsync-failure']){
      const root=fs.mkdtempSync(path.join(os.tmpdir(),'rain-final-fsync-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
      const driver=path.resolve(__dirname,'../r0040/native-options.cjs');
      const result=spawnSync(process.execPath,['-e',`(${originalDriverChild.toString()})()`,entry,driver,root,'','',mode],{encoding:'utf8'});
      assert.equal(result.status,mode==='complete'?0:1,result.stderr);
      reports.push(fs.readFileSync(path.join(root,'original/native-options.json')));
      assert.equal(JSON.parse(reports.at(-1)).cells.length,9);
      const events=fs.readFileSync(path.join(root,'evidence/events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
      assert.equal(events.filter(x=>x.event==='cell-body-completed').length,9);
      if(mode==='fsync-failure'){
        const correction=events.find(x=>x.event==='retention-finalization-failed');
        assert.equal(correction.exitCode,1);assert.match(correction.error.message,/injected final fsync failure/);
      }
    }
    assert.deepEqual(reports[0],reports[1]);
  });
  test('retention finalization failures cannot replace the continuation-veto exit code',t=>{
    for(const mode of ['fsync-failure','close-failure']){
      const root=fs.mkdtempSync(path.join(os.tmpdir(),'rain-final-veto-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
      const driver=path.resolve(__dirname,'../r0040/native-options.cjs');
      const result=spawnSync(process.execPath,['-e',`(${originalDriverChild.toString()})()`,entry,driver,root,'','veto',mode],{encoding:'utf8'});
      assert.equal(result.status,86,result.stderr);
      assert.equal(fs.existsSync(path.join(root,'original/native-options.json')),false);
      const events=fs.readFileSync(path.join(root,'evidence/events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
      assert.ok(events.some(x=>x.event==='external-continuation-vetoed'));
    }
  });
  test('retention close failure after original completion is nonzero',t=>{
    const root=fs.mkdtempSync(path.join(os.tmpdir(),'rain-final-close-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
    const driver=path.resolve(__dirname,'../r0040/native-options.cjs');
    const result=spawnSync(process.execPath,['-e',`(${originalDriverChild.toString()})()`,entry,driver,root,'','','close-failure'],{encoding:'utf8'});
    assert.equal(result.status,1);assert.match(result.stderr,/injected final close failure/);
    assert.equal(JSON.parse(fs.readFileSync(path.join(root,'original/native-options.json'))).cells.length,9);
  });
}
