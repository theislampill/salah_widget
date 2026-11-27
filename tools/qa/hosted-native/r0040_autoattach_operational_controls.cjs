'use strict';
// Full protected driver and original CRLF helper execute through the unchanged
// Date-only transform. Every browser/HTTP dependency is an explicit source-test
// fake. These runs cannot establish runtime noninterference or native coverage.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const sha=x=>createHash('sha256').update(x).digest('hex');
const driver=path.resolve(__dirname,'../r0040/capture.cjs');

function childSource(){
  const source=fs.readFileSync(path.join(__dirname,'r0040_passive_controls.cjs'),'utf8');
  const start=source.indexOf('function dateOnlyChildSource(){'),end=source.indexOf('\nfunction runPassive(',start);
  assert.ok(start>=0&&end>start,'protected existing source-test recipe required');
  let code=vm.runInNewContext('(()=>{'+source.slice(start,end)+';return passiveChildSource();})()',{fs,path,assert,vm,__dirname});
  function replace(before,after){assert.equal(code.split(before).length,2,'operational test seam '+before);code=code.replace(before,()=>after);}
  replace("const P=require(entry),D=require(path.join(path.dirname(entry),'r0040_dateonly.cjs')),{PassiveRetention:CaptureRetention,executeOriginal}=P,load=Module.createRequire(driver);",
    "const M=require(entry),P=require(path.join(path.dirname(entry),'r0040_passive.cjs')),D=require(path.join(path.dirname(entry),'r0040_dateonly.cjs')),{MechanismRetention:CaptureRetention}=M,executeOriginal=P.executeOriginal,load=Module.createRequire(driver);\n"+
    "    const networkFake=require(path.join(path.dirname(entry),'r0040_autoattach_fixture.cjs')).fakeBrowser();");
  replace("passive:P.passiveIdentity(driver),collectionTimeoutMs:100});",
    "passive:P.passiveIdentity(driver),mechanism:M.mechanismIdentity(driver),collectionTimeoutMs:100,networkTimeoutMs:100});");
  replace("const bus={textContent:'',dispatchEvent(){sampleClock+=2;this.textContent=JSON.stringify(sample);}};",
    "const joined=[];const bus={textContent:'',addEventListener(name,fn){if(name!=='r0040-read')throw Error('unexpected synthetic bus listener');joined.push(fn);},dispatchEvent(event){sampleClock+=2;this.textContent=JSON.stringify(sample);for(const fn of joined)fn(event);}};");
  replace("Event:class{constructor(type){this.type=type;}}",
    "Event:class{constructor(type){this.type=type;this.timeStamp=sampleClock;}}");
  replace("browser.newContext=async options=>{",
    "browser.newBrowserCDPSession=networkFake.browser.newBrowserCDPSession;\n    browser.newContext=async options=>{");
  replace("ctx.emit('close');page.emit('close');",
    "ctx.emit('close');page.emit('close');networkFake.close();");
  replace("process.env.R0040_DISPERSION='common';delete process.env.R0040_OPTIONS;",
    "trace.operational=[];trace.scope='SYNTHETIC_PUBLIC_API_FULL_ORIGINAL_DRIVER';\n"+
    "    const value=x=>{if(x===page)return {object:'page'};if(x===ctx)return {object:'context'};if(x===cdp)return {object:'capture-cdp'};if(x===browser)return {object:'browser'};\n"+
    "      if(typeof x==='function')return {callableSha256:hash(x.toString())};if(x===undefined)return {undefined:true};if(Array.isArray(x))return x.map(value);\n"+
    "      if(x&&typeof x==='object')return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,value(v)]));return x;};\n"+
    "    for(const [owner,object,names]of [['page',page,['on','goto','evaluate','waitForFunction','waitForTimeout','addScriptTag','addInitScript']],\n"+
    "      ['context',ctx,['on','route','newPage','newCDPSession','close']],['browser',browser,['on','newContext','close']],['capture-cdp',cdp,['on','send','detach']]])\n"+
    "      for(const name of names){const original=object[name];object[name]=function(...args){trace.operational.push({owner,method:name,args:value(args)});return Reflect.apply(original,this,args);};}\n"+
    "    trace.actualOriginalArgv=['bounded-playwright',history,main,out,'chromium','bday','moderate','M1'];\n"+
    "    trace.originalDriverSha256=hash(fs.readFileSync(driver));trace.originalHelperSha256=hash(fs.readFileSync(helper));\n"+
    "    trace.fixtureLimits='Main bracket snapshot and selected network ownership deliberately incomplete; no native or diagnostic qualification.';\n"+
    "    process.env.R0040_DISPERSION='common';delete process.env.R0040_OPTIONS;");
  replace("trace.reportAfterClose=fs.existsSync(report)?hash(fs.readFileSync(report)):null;",
    "trace.reportAfterClose=fs.existsSync(report)?hash(fs.readFileSync(report)):null;trace.observerCalls=networkFake.calls;");
  return code;
}

function run(t,label,mode){
  const base=process.env.R0040_AUTOATTACH_TRACE_ROOT||os.tmpdir();fs.mkdirSync(base,{recursive:true});
  const root=fs.mkdtempSync(path.join(base,'autoattach-operational-'+label+'-'+mode+'-'));
  if(!process.env.R0040_AUTOATTACH_TRACE_ROOT)t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const entry=path.join(__dirname,label==='original'?'r0040_mechanism.cjs':'r0040_autoattach.cjs'),source=childSource();
  fs.writeFileSync(path.join(root,'control-child.cjs'),source);
  const argv=[process.execPath,'-e',source,entry,driver,root,mode,'',''],started=Date.now();
  const result=spawnSync(argv[0],argv.slice(1),{encoding:'utf8',timeout:10000,env:{...process.env,NODE_OPTIONS:''}});
  fs.writeFileSync(path.join(root,'child.stdout'),result.stdout||'');fs.writeFileSync(path.join(root,'child.stderr'),result.stderr||'');
  fs.writeFileSync(path.join(root,'child-process.json'),JSON.stringify({argv,cwd:process.cwd(),status:result.status,signal:result.signal,
    error:result.error?String(result.error):null,elapsedMs:Date.now()-started,timeoutMs:10000,scope:'SYNTHETIC_PUBLIC_API_SOURCE_ONLY'},null,2)+'\n');
  const read=name=>{const file=path.join(root,name);return fs.existsSync(file)?fs.readFileSync(file):null;};
  const json=name=>{const bytes=read(name);return bytes?JSON.parse(bytes):null;};
  return {root,result,trace:json('control-trace.json'),base:json('evidence/final-admission.json'),passive:json('evidence/passive-observation.json'),
    receipt:json('evidence/'+(label==='original'?'mechanism-observation.json':'autoattach-observation.json')),
    report:read('original/capture.json'),stop:read('evidence/passive-original-stop-1.json'),pngs:[0,1].map(i=>read('original/f'+String(i).padStart(5,'0')+'.png'))};
}

for(const mode of ['complete','oracle-failure'])test('full original operation trace and bytes retain '+mode+' behavior under separate collector',t=>{
  const old=run(t,'original',mode),fresh=run(t,'automatic',mode);
  for(const r of [old,fresh]){
    assert.equal(r.result.error,undefined,r.result.stderr);assert.equal(r.result.status,1,r.result.stderr);assert.ok(r.trace,r.result.stderr);
    assert.equal(r.trace.originalDriverSha256,require('./r0040_mechanism_bracket.cjs').DRIVER_SHA256);
    assert.equal(r.trace.originalHelperSha256,require('./r0040_dateonly.cjs').ORIGINAL_SHA256);
    assert.equal(r.trace.actualOriginalArgv.length,8);assert.deepEqual(r.trace.actualOriginalArgv.slice(4),['chromium','bday','moderate','M1']);
    assert.equal(r.trace.contextCloseCalls,1);assert.equal(r.trace.reportBeforeClose,r.trace.reportAfterClose);
    assert.equal(r.receipt.status,mode==='complete'?'INCOMPLETE':'FAILED');assert.equal(r.receipt.originalExitCode,mode==='complete'?0:1);
  }
  assert.deepEqual(fresh.trace.operational,old.trace.operational,'all underlying original public operations, argument values, callable bytes and order');
  assert.deepEqual(fresh.report,old.report);assert.deepEqual(fresh.pngs,old.pngs);assert.deepEqual(fresh.stop,old.stop);
  assert.deepEqual(fresh.trace.continued,old.trace.continued);assert.deepEqual(fresh.trace.aborted,old.trace.aborted);
  if(mode==='complete'){
    assert.ok(fresh.report&&fresh.stop&&fresh.pngs.every(Buffer.isBuffer));
    assert.equal(fresh.base.status,require('./r0040_dateonly.cjs').ADMITTED);assert.equal(fresh.passive.status,require('./r0040_passive.cjs').ADMITTED);
    assert.equal(fresh.trace.frameListenerCount,1);assert.equal(fresh.trace.streamFsyncs,0);assert.equal(fresh.trace.streamPngWrites,2);
  }else assert.equal(fresh.report,null);
  assert.equal(old.trace.observerCalls.some(row=>row.method==='Target.setAutoAttach'),false);
  assert.equal(fresh.trace.observerCalls.some(row=>row.method==='Target.setAutoAttach'),true);
  assert.ok(fresh.trace.observerCalls.every(row=>!/(?:Runtime\.|Page\.|detach|resume|pause|Fetch\.|setCache|getResponseBody)/.test(row.method)));
});

test('new operational entry has exact full inverse and protected method bodies with only declared journal labels',()=>{
  const old=require('./r0040_mechanism.cjs'),fresh=require('./r0040_autoattach.cjs');
  assert.equal(fresh.reverseMechanism(fresh.deriveMechanism(fs.readFileSync(path.join(__dirname,'r0040_mechanism.cjs'),'utf8')).source),
    fs.readFileSync(path.join(__dirname,'r0040_mechanism.cjs'),'utf8'));
  for(const name of ['wrapPage','wrapCDP','wrapContext'])
    assert.equal(fresh.MechanismRetention.prototype[name].toString(),old.MechanismRetention.prototype[name].toString());
  for(const [name,label,count]of [['collectBrackets','bracket-prefix',1],['wrapBrowser','network-prefix',2]]){
    const actual=fresh.MechanismRetention.prototype[name].toString(),token="'autoattach-"+label+"'";
    assert.equal(actual.split(token).length-1,count,'exact declared journal label count');
    assert.equal(actual.split(token).join("'mechanism-"+label+"'"),old.MechanismRetention.prototype[name].toString());
  }
  assert.equal(fresh.runDriver.toString(),old.runDriver.toString());
});
