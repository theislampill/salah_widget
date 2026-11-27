'use strict';
// Source/behavior controls only. Actual pinned driver/helper code executes with
// bounded page/HTTP/CDP doubles; no browser is imported or launched here.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const D=require('./r0040_dateonly.cjs');
const sha=b=>createHash('sha256').update(b).digest('hex');
const original=path.join(__dirname,'fixtures/r0040-precip-eval-original.txt');
const driver=path.resolve(__dirname,'../r0040/capture.cjs');
const entry=path.join(__dirname,'r0040_dateonly.cjs');
const plain=value=>JSON.parse(JSON.stringify(value));
function temporary(t){const root=fs.mkdtempSync(path.join(os.tmpdir(),'dateonly-control-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));return root;}
function clockContext(utcMs){
  const nativePerformance=require('node:perf_hooks').performance;
  const sandbox={performance:{now:()=>nativePerformance.now(),timeOrigin:nativePerformance.timeOrigin},
    setTimeout,clearTimeout,setInterval,clearInterval,queueMicrotask};
  sandbox.requestAnimationFrame=callback=>setTimeout(()=>callback(sandbox.performance.now()),2);
  sandbox.cancelAnimationFrame=clearTimeout;
  const context=vm.createContext(sandbox);vm.runInContext('globalThis.window=globalThis',context);
  vm.runInContext('('+D.installDateOnly.toString()+')('+JSON.stringify({utcMs})+')',context);
  return context;
}
async function proof(utcMs=1790154360000){return plain(await vm.runInContext('('+D.observeNativeClock.toString()+')()',clockContext(utcMs)));}

// Reuse the existing actual-driver boundary and change only its explicit test
// dependencies. The original capture file and recovered historical helper are
// never edited. Keep every derived test seam checked against its public source.
function childSource(){
  const source=fs.readFileSync(path.join(__dirname,'r0040_capture_retention_controls.cjs'),'utf8');
  const start=source.indexOf('  function child() {'),end=source.indexOf('\n  function run(',start);
  assert.ok(start>=0&&end>start);let code=source.slice(start,end);
  function replace(before,after){assert.equal(code.split(before).length,2,'control seam '+before);code=code.replace(before,()=>after);}
  replace("const {CaptureRetention,executeOriginal}=require(entry),load=Module.createRequire(driver);",
    "const D=require(entry),{DateOnlyRetention:CaptureRetention,executeOriginal}=D,load=Module.createRequire(driver);\n"+
    "    const vm=require('node:vm');let proofContext=null,blockedTimer=null;\n"+
    "    function clockContext(utcMs){const p=require('node:perf_hooks').performance;const x={performance:{now:()=>p.now(),timeOrigin:p.timeOrigin},setTimeout,clearTimeout,setInterval,clearInterval,queueMicrotask};x.requestAnimationFrame=f=>setTimeout(()=>f(x.performance.now()),2);x.cancelAnimationFrame=clearTimeout;const c=vm.createContext(x);vm.runInContext('globalThis.window=globalThis',c);vm.runInContext('('+D.installDateOnly.toString()+')('+JSON.stringify({utcMs})+')',c);return c;}");
  replace("fs.writeFileSync(path.join(history,'tools/qa/precip_models.js'),'window.__R0040_STUDY;');}",
    "fs.writeFileSync(path.join(history,'tools/qa/precip_models.js'),'window.__R0040_STUDY;');\n"+
    "      fs.copyFileSync(path.join(path.dirname(entry),'fixtures/r0040-precip-eval-original.txt'),helper);}");
  replace("const page=new EventEmitter();page.clock={async install(){},async resume(){}};",
    "const page=new EventEmitter();Object.defineProperty(page,'clock',{get(){throw Error('full mocked clock must never be used');}});\n"+
    "    page.addInitScript=async(fn,value)=>{if(mode==='install-failure')throw Error('controlled Date-only installation fault');if(fn.name!=='installDateOnly')throw Error('unexpected init script');proofContext=clockContext(value.utcMs);};");
  replace("const text=String(expression);",
    "const text=String(expression);\n"+
    "      if(expression?.name==='observeNativeClock'){\n"+
    "        if(mode==='proof-evaluate')throw Error('controlled clock evaluation fault');\n"+
    "        if(mode==='proof-timeout'){blockedTimer=setInterval(()=>{},1000);return new Promise(()=>{});}\n"+
    "        const raw=JSON.parse(JSON.stringify(await vm.runInContext('('+D.observeNativeClock.toString()+')()',proofContext)));\n"+
    "        if(mode.startsWith('proof-invalid'))raw.after.dateNowMs+=100;return raw;\n"+
    "      }");
  replace("ctx.close=async()=>{",
    "ctx.close=async()=>{\n"+
    "      trace.contextCloseCalls=(trace.contextCloseCalls||0)+1;if(blockedTimer)clearInterval(blockedTimer);\n"+
    "      if(mode==='proof-invalid-veto'){const req={url:()=> 'https://unknown.invalid/blocked'};const row=retain.requestRow(req,'route');try{await retain.wrapRoute({async continue(){trace.continued.push(req.url());},async abort(){trace.aborted.push(req.url());}},row).continue();}catch(error){}}\n"+
    "      if(mode==='proof-invalid-close')throw Error('secondary diagnostic context close fault');");
  replace("const retain=new CaptureRetention(path.join(root,'evidence'),{out,expected,pins});",
    "const retain=new CaptureRetention(path.join(root,'evidence'),{out,expected,pins,\n"+
    "      diagnostic:D.diagnosticIdentity(D.transformHelper(fs.readFileSync(helper)).identity),proofTimeoutMs:mode==='proof-timeout'?100:5000});");
  replace("if(request===helper&&!actualHistory)return fakeHelper;return load(request);",
    "if(request==='http')return {createServer(){const srv=new EventEmitter();srv.listen=(_port,_host,callback)=>{setImmediate(callback);return srv;};srv.address=()=>({port:8765});srv.close=()=>{setImmediate(()=>{srv.emit('close');if(mode==='late-server-error')srv.emit('error',Error('late server fault'));});return srv;};return srv;}};return load(request);");
  return '('+code.trim()+')()';
}
function run(t,mode){
  const root=temporary(t),result=spawnSync(process.execPath,['-e',childSource(),entry,driver,root,mode,'',''],
    {encoding:'utf8',timeout:mode==='timeout'?1800:10000,env:{...process.env,NODE_OPTIONS:''}});
  const evidence=path.join(root,'evidence'),file=path.join(evidence,'events.jsonl');
  const events=fs.existsSync(file)?fs.readFileSync(file,'utf8').trim().split('\n').map(JSON.parse):[];
  const read=name=>fs.existsSync(name)?JSON.parse(fs.readFileSync(name)):null;
  return {root,result,events,receipt:read(path.join(evidence,'final-admission.json')),trace:read(path.join(root,'control-trace.json'))};
}

test('exact CRLF historical bytes have one reversible clock seam and all original APIs',()=>{
  const bytes=fs.readFileSync(original);assert.equal(bytes.length,17990);assert.equal(sha(bytes),D.ORIGINAL_SHA256);
  assert.equal(bytes.toString().match(/\r\n/g).length,136);assert.equal(bytes.toString().match(/(?<!\r)\n/g),null);
  const transformed=D.transformHelper(bytes);assert.equal(transformed.identity.changedSeams,1);assert.equal(transformed.identity.originalRecoveredExactly,true);
  assert.deepEqual(D.reverseHelper(transformed.source),bytes);assert.ok(!transformed.source.includes(Buffer.from('await page.clock.install')));
  assert.equal(transformed.identity.installDateOnlySha256,sha(D.installDateOnly.toString()));
});
test('Date call construction static helpers and 1x progression preserve every timer and performance reference',async()=>{
  const c=clockContext(1790154360000),read=()=>plain(vm.runInContext('window.__R0040_DATE_ONLY__.sample()',c));
  const a=read();await new Promise(r=>setTimeout(r,45));const b=read();
  assert.ok(b.dateNowMs>a.dateNowMs);assert.ok(Object.values(a.preserved).every(x=>x===true));assert.ok(Object.values(b.preserved).every(x=>x===true));
  assert.equal(vm.runInContext('Date.UTC(2000,0,1)',c),946684800000);assert.equal(vm.runInContext('new Date(123).getTime()',c),123);
  assert.equal(vm.runInContext('new Date(2020,0,2) instanceof Date',c),true);
  assert.equal(vm.runInContext('typeof Date()',c),'string');assert.equal(vm.runInContext('Date.parse("2000-01-01T00:00:00Z")',c),946684800000);
});
test('actual startup observation completes a timer and two rAF callbacks in one clock domain and rejects corrupted raw proofs',async()=>{
  const raw=await proof(),admitted=D.admitClockProof(raw,raw.utcMs);assert.equal(admitted.status,'OBSERVED_NATIVE_TIMERS');
  const corrupt=[x=>x.frames.pop(),x=>x.frames.push(x.frames[0]),x=>x.timer=null,x=>x.after.dateNowMs+=100,
    x=>x.before.preserved.requestAnimationFrame=false,x=>x.after.timeOriginMs++,x=>x.utcMs++,x=>x.status='INCOMPLETE',
    x=>x.frames[1].timestampMs=x.frames[0].timestampMs,x=>x.after.performanceBeforeMs=NaN];
  for(const mutate of corrupt){const bad=plain(raw);mutate(bad);assert.throws(()=>D.admitClockProof(bad,raw.utcMs));}
});
test('native CLI refuses isolation before original helper browser source or output import',t=>{
  const root=temporary(t),env={...process.env,NODE_OPTIONS:''};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
  const r=spawnSync(process.execPath,[entry,'--driver','unopened','--manifest','unopened','--prepared','unopened','--preparation-process','unopened',
    '--preparation-entry','unopened','--evidence',path.join(root,'evidence'),'--','unopened','unopened','unopened',path.join(root,'out'),'chromium','bday','moderate','M1'],{encoding:'utf8',env});
  assert.equal(r.status,1);assert.match(r.stderr,/admitted isolation receipt required/);assert.equal(fs.existsSync(path.join(root,'evidence')),false);
});
test('actual outer preparation entry requires zero exit exact argv current source and no retention error',t=>{
  const root=temporary(t),processFile=path.join(root,'process.json'),entryFile=path.join(root,'entry.json'),main=path.join(root,'main'),work=path.join(root,'work');
  const options={manifest:path.resolve(__dirname,'../../../docs/state-contracts/evidence/R0040/native-capture-preflight.json'),
    driver,prepared:path.join(work,'receipts/prepared.json'),preparationProcess:processFile,evidence:path.join(root,'evidence')};
  const args=['/synthetic/playwright',path.join(work,'historical'),main,path.join(root,'out'),'chromium','bday','moderate','M1'];
  const inputs={manifest:options.manifest,research:path.resolve(__dirname,'../../..'),historical:path.join(root,'historical-inputs'),main,out:work};
  fs.writeFileSync(processFile,JSON.stringify({inputs}));
  const body={protocol:'r0040-capture-preparation-entry/1',returncode:0,timedOut:false,timeoutSeconds:240,cwd:__dirname,
    wrapperSha256:sha(fs.readFileSync(path.join(__dirname,'r0040_capture_prepare.py'))),
    argv:['/usr/bin/python3',path.join(__dirname,'r0040_capture_prepare.py'),'--manifest',inputs.manifest,'--research',inputs.research,
      '--historical',inputs.historical,'--main',inputs.main,'--out',inputs.out,'--receipts',root]};
  const write=value=>fs.writeFileSync(entryFile,JSON.stringify(value));write(body);
  assert.equal(D.admitPreparationEntry(entryFile,options,args).actualExitCode,0);
  for(const patch of [{returncode:false},{returncode:1},{timedOut:true},{retentionError:'lost stream'},{retentionError:''},{argv:[]},{cwd:'/other'},{wrapperSha256:'0'.repeat(64)}]){
    write({...body,...patch});assert.throws(()=>D.admitPreparationEntry(entryFile,options,args));}
});
test('actual pinned driver and transformed actual helper retain original report and raw CDP without per-frame host work',t=>{
  const r=run(t,'complete');assert.equal(r.result.status,0,r.result.stderr);assert.equal(r.receipt.status,D.ADMITTED);
  assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.equal(r.trace.rawCdp,true);assert.equal(r.trace.streamFsyncs,0);assert.equal(r.trace.streamPngWrites,2);
  assert.equal(r.receipt.clockProofs.length,1);assert.equal(r.receipt.clockProofs[0].status,'OBSERVED');assert.equal(r.trace.contextCloseCalls,1);
  assert.ok(r.trace.aborted.includes('https://unknown.invalid/blocked'));assert.ok(!r.trace.continued.includes('https://unknown.invalid/blocked'));
});
test('failed proof evaluation and timeout close acquired context before failed-open return and retain primary plus secondary errors',t=>{
  for(const mode of ['proof-invalid','proof-invalid-close','proof-evaluate','proof-timeout','install-failure']){
    const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.trace.contextCloseCalls,1);assert.equal(r.receipt.status,'FAILED');
    assert.equal(r.receipt.originalReport,null);assert.equal(r.receipt.clockProofs.length,1);
    if(mode.startsWith('proof-invalid')){assert.ok(r.receipt.clockProofs[0].raw);assert.match(r.result.stderr,/Date.*1x|Date.*anchor/);}
    else assert.equal(r.receipt.clockProofs[0].status,'UNAVAILABLE');
    if(mode==='proof-invalid-close')assert.ok(JSON.stringify(r.receipt).includes('secondary diagnostic context close fault'));
  }
});
test('original oracle exception and context cleanup exception remain failures without replacement reports',t=>{
  for(const mode of ['oracle-failure','close-failure']){
    const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.receipt.status,'FAILED');assert.equal(r.receipt.originalExitCode,1);
    if(mode==='oracle-failure'){assert.equal(r.receipt.originalReport,null);assert.match(r.result.stderr,/unexpected admitted source/);}
    else assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
  }
});
test('late page crash disconnection page error request error and fatal server error retain their failure after original report',t=>{
  for(const mode of ['late-pageerror','late-page-crash','unexpected-disconnect','late-request','late-network','late-server-error']){
    const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.receipt.status,'FAILED');
    assert.ok(r.trace.reportAfterClose);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
  }
});
test('diagnostic cleanup veto prevents external continuation and preserves actual exit86 over the proof error',t=>{
  const r=run(t,'proof-invalid-veto');assert.equal(r.result.status,86,r.result.stderr);assert.equal(r.receipt.status,'CONTINUATION_VETOED');
  assert.equal(r.receipt.originalExitCode,1);assert.equal(r.receipt.continuationVetoed,true);
  assert.equal(r.trace.continued.includes('https://unknown.invalid/blocked'),false);assert.ok(r.trace.aborted.includes('https://unknown.invalid/blocked'));
});
test('terminal journal and final receipt fsync faults cannot publish admitted evidence or hide actual failure',t=>{
  for(const mode of ['final-fsync','receipt-fsync']){const r=run(t,mode);assert.equal(r.result.status,1,r.result.stderr);assert.equal(r.receipt,null);
    assert.ok(r.trace.reportAfterClose);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);assert.match(r.result.stderr,/fsync fault/);}
});
test('outer acquisition timeout preserves original PNGs and proof prefix without invented terminal admission',t=>{
  const r=run(t,'timeout');assert.equal(r.result.signal,'SIGTERM',r.result.stderr);assert.equal(r.receipt,null);
  assert.deepEqual(fs.readdirSync(path.join(r.root,'original')).sort(),['f00000.png','f00001.png']);
  assert.ok(r.events.some(row=>row.event==='date-only-clock-proof'));assert.ok(!r.events.some(row=>row.event==='driver-process-ended'));
});
test('original helper driver and source seams reject byte drift before executing a substitute',t=>{
  const bytes=fs.readFileSync(original);assert.throws(()=>D.transformHelper(Buffer.concat([bytes,Buffer.from(' ')])),/digest/);
  const root=temporary(t),changed=path.join(root,'capture.cjs');fs.copyFileSync(driver,changed);fs.appendFileSync(changed,'\n// source drift');
  assert.throws(()=>require('./retain_r0040_capture.cjs').verifyDriver(changed),/digest/);
  assert.throws(()=>D.reverseHelper(Buffer.from('not the admitted transformed helper')),/seam|reversal|digest/);
});
