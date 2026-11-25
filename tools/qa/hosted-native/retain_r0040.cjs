'use strict';
// Host-side successor instrumentation. The original CommonJS bytes execute
// unchanged. This private journal never stands in for native-options.json.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const PIN_PATH = path.join(__dirname, 'retention-pins.json');
const pins = JSON.parse(fs.readFileSync(PIN_PATH));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const errorData = error => ({name:error?.name, message:String(error?.message ?? error), stack:error?.stack});
const need = (ok, message) => {if (!ok) throw Error(message);};

class Journal {
  constructor(directory) {
    this.directory = path.resolve(directory); this.sequence = 0;
    fs.mkdirSync(this.directory, {mode:0o700});
    this.fd = fs.openSync(path.join(this.directory, 'events.jsonl'), 'wx', 0o600);
    this.record('instrumentation', {protocol:'salah-native-evidence-retention/1',recipe:'R0040',
      interpretation:'Supplemental retention only; original result and failures remain authoritative.',
      overhead:'Host serialization, hashing, synchronous fsync and screenshot copies affect timing. Failure captures follow the fault; no presentation timestamps.'});
  }
  record(event, value = {}) {
    const row = {sequence:++this.sequence, atUtc:new Date().toISOString(), monotonicNs:process.hrtime.bigint().toString(),event,...value};
    fs.writeFileSync(this.fd, JSON.stringify(row)+'\n'); fs.fsyncSync(this.fd); return row;
  }
  preserve(event, value) {
    // A secondary retention failure must not replace an original exception.
    try {this.record(event,value);} catch(error) {this.retentionError = error;}
  }
  blob(name, bytes) {
    const target = path.join(this.directory,name), fd=fs.openSync(target,'wx',0o600);
    try {fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
    return {file:name,bytes:bytes.length,sha256:sha(bytes)};
  }
  close() {if(this.fd!==null){fs.closeSync(this.fd);this.fd=null;}}
}

function verifyInputs(driver, historical) {
  const rows = [
    ['tools/qa/r0040/native-options.cjs',path.resolve(driver)],
    ['tools/qa/r0040/native-option-oracle.cjs',path.join(path.dirname(path.resolve(driver)),'native-option-oracle.cjs')],
    ['tools/qa/precip_eval_lib.cjs',path.resolve(historical,'tools/qa/precip_eval_lib.cjs')]
  ];
  return rows.map(([name,file])=>{const digest=sha(fs.readFileSync(file));need(digest===pins.files[name],'source digest mismatch: '+name);
    return {name,file,sha256:digest};});
}
function verifyIsolation(file) {
  need(file, 'admitted isolation receipt required');
  const receipt=JSON.parse(fs.readFileSync(file));
  need(receipt.protocol==='salah-hosted-native-isolation/1'&&receipt.passed===true&&receipt.browserControl?.passed===true,
    'admitted isolation receipt required');
  need(typeof process.getuid==='function'&&process.getuid()>0&&receipt.uid===process.getuid(), 'nonroot receipt identity mismatch');
  need(receipt.netns===fs.readlinkSync('/proc/self/ns/net')&&receipt.outerNetns&&receipt.netns!==receipt.outerNetns,
    'isolation receipt namespace mismatch');
  return {file,sha256:sha(fs.readFileSync(file))};
}
function allowedContinuation(url,base) {
  const parsed=new URL(url);
  return ['data:','blob:'].includes(parsed.protocol)||
    (['http:','https:'].includes(parsed.protocol)&&parsed.origin===new URL(base).origin&&
      ['127.0.0.1','localhost','[::1]'].includes(parsed.hostname));
}

class RainRetention {
  constructor(directory) {this.journal=new Journal(directory);this.cells=[];this.current=null;this.requests=0;this.shots=0;}
  record(event,value={}) {return this.journal.record(event,{cell:this.current?.number,...value});}
  failure(event,error,cell=this.current,fields={}) {
    if(cell&&!cell.failure) cell.failure=error;
    this.journal.preserve(event,{cell:cell?.number,...fields,error:errorData(error)});
  }
  beginCell(base,options) {
    const cell={number:this.cells.length+1,base,options,postconditions:0};
    this.cells.push(cell);this.current=cell;this.record('cell-started',{base,options});return cell;
  }
  wrapRoute(raw,cell) {
    const request=raw.request(), url=request.url(), requestId=++this.requests;
    this.record('request',{cell:cell.number,requestId,url,method:request.method?.(),resourceType:request.resourceType?.()});
    return new Proxy(raw,{get:(target,key)=>{
      if(['continue','fulfill','abort'].includes(key)) return async(...args)=>{
        const refused=key==='continue'&&!allowedContinuation(args[0]?.url||url,cell.base);
        const fields={cell:cell.number,requestId,url,action:key,refused};
        this.record('request-action',fields);
        if(refused) {
          const error=Error('external continuation refused by retention guard');
          this.continuationVeto=error;
          this.failure('external-continuation-vetoed',error,cell,fields);
          try {await target.abort();this.record('request-action-completed',{...fields,action:'abort',guard:true});}
          catch(abortError){this.failure('request-action-failed',abortError,cell,fields);}
          throw error;
        }
        let result;
        try {result=await target[key](...args);}
        catch(error){this.failure('request-action-failed',error,cell,fields);throw error;}
        this.record('request-action-completed',fields);return result;
      };
      if(['fetch','fallback'].includes(key)) return ()=>{throw Error('unsupported route bypass in retention successor');};
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  async screenshot(raw,args,cell,kind) {
    const shotId=++this.shots, requestNs=process.hrtime.bigint().toString();
    this.record('screenshot-requested',{cell:cell.number,shotId,kind,requestNs});
    const rawCallNs=process.hrtime.bigint().toString();let data;
    try {data=await raw.screenshot(...args);}
    catch(error){this.failure(kind==='original'?'screenshot-threw':'diagnostic-failed',error,cell);throw error;}
    const receiptNs=process.hrtime.bigint().toString();
    try {
      const file=this.journal.blob(`cell-${String(cell.number).padStart(2,'0')}-shot-${shotId}.png`,data);
      this.record('screenshot-received',{cell:cell.number,shotId,kind,requestNs,rawCallNs,receiptNs,...file,originalPath:args[0]?.path??null});
      if(kind==='original')cell.screenshotReceived=true;
      return data;
    } catch(error) {this.failure('screenshot-retention-failed',error,cell);throw error;}
  }
  wrapPage(raw,cell) {
    cell.rawPage=raw;
    raw.on('pageerror',error=>this.journal.preserve('pageerror',{cell:cell.number,error:errorData(error)}));
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='screenshot')return (...args)=>this.screenshot(target,args,cell,'original');
      if(['goto','evaluate','waitForFunction','waitForTimeout'].includes(key))return async(...args)=>{
        try {return await target[key](...args);}catch(error){this.failure('page-operation-threw',error,cell);throw error;}
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  async retainFailure(cell) {
    if(!cell.failure||!cell.rawPage||cell.diagnosticAttempted)return;
    cell.diagnosticAttempted=true;
    try {await this.screenshot(cell.rawPage,[{timeout:10000}],cell,'failure-diagnostic');}catch(_){}
  }
  wrapContext(raw,cell) {
    const wrapped=new Proxy(raw,{get:(target,key)=>{
      if(key==='route')return async(pattern,handler,...rest)=>{
        need(pattern==='**/*','catch-all route required');
        await target.route(pattern,(route,...args)=>handler(this.wrapRoute(route,cell),...args),...rest);
        cell.routeInstalled=true;this.record('route-installed',{cell:cell.number,pattern});
      };
      if(['unroute','unrouteAll'].includes(key))return ()=>{throw Error('route removal forbidden during retention');};
      if(key==='addInitScript')return async(...args)=>{
        const result=await target.addInitScript(...args);cell.researchOptions=args[1];
        this.record('init-script-installed',{cell:cell.number,scriptSha256:sha(String(args[0])),argument:args[1]});return result;
      };
      if(key==='newPage')return async(...args)=>{
        need(cell.routeInstalled,'install catch-all route before creating a page');
        const page=this.wrapPage(await target.newPage(...args),cell);
        cell.page=page;this.record('page-created',{cell:cell.number});return page;
      };
      if(key==='close')return async(...args)=>{
        this.journal.preserve('scene-log',{cell:cell.number,log:cell.sceneLog??null});
        const completed=cell.oraclePassed&&cell.screenshotReceived&&cell.postconditions===2;
        if(!completed)await this.retainFailure(cell);
        let result;
        try {result=await target.close(...args);cell.closed=true;}
        catch(error){this.failure('context-close-threw',error,cell);throw error;}
        this.journal.preserve('context-closed',{cell:cell.number});
        if(completed)
          this.record('cell-body-completed',{cell:cell.number,id:cell.id,options:cell.options,researchOptions:cell.researchOptions});
        return result;
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
    cell.context=wrapped;return wrapped;
  }
  wrapBrowser(raw) {
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='newContext')return async(...args)=>{
        need(this.current,'context outside original cell');
        need(args[0]?.serviceWorkers==='block','original service-worker block required');
        return this.wrapContext(await target.newContext(...args),this.current);
      };
      if(key==='close')return async(...args)=>{
        for(const cell of this.cells)if(!cell.closed)await this.retainFailure(cell);
        return target.close(...args);
      };
      const value=target[key];return typeof value==='function'?value.bind(target):value;
    }});
  }
  wrapPlaywright(raw,engine) {
    return new Proxy(raw,{get:(target,key)=>key===engine?new Proxy(target[key],{get:(browserType,name)=>{
      if(name==='launch')return async(...args)=>this.wrapBrowser(await browserType.launch(...args));
      const value=browserType[name];return typeof value==='function'?value.bind(browserType):value;
    }}):target[key]});
  }
  wrapHelper(raw) {
    return new Proxy(raw,{get:(target,key)=>{
      if(key==='openScene')return async(browser,base,ordinary,options)=>{
        const cell=this.beginCell(base,options);
        try {const scene=await target.openScene(browser,base,ordinary,options);cell.sceneLog=scene.log;
          this.record('scene-opened',{url:scene.url,log:scene.log});return scene;
        }catch(error){this.failure('scene-open-threw',error,cell);throw error;}
      };
      if(key==='waitReady')return async(...args)=>{
        let value;
        try {value=await target.waitReady(...args);}
        catch(error){this.failure('readiness-threw',error);throw error;}
        this.record('readiness-returned',{value});return value;
      };
      return target[key];
    }});
  }
  wrapOracle(raw) {return {check:(id,state,amount)=>{
    const cell=this.current;cell.id=id;this.record('oracle-called',{id,state,amount});
    let result;
    try {result=raw.check(id,state,amount);}
    catch(error){this.failure('oracle-threw',error,cell);throw error;}
    cell.oraclePassed=true;this.record('oracle-returned',{id});return result;
  }};}
  wrapAssert(raw) {return new Proxy(raw,{get:(target,key)=>{
    if(['equal','deepEqual'].includes(key))return (...args)=>{
      let result;
      try {result=target[key](...args);}
      catch(error){this.failure('postcondition-threw',error);throw error;}
      this.current.postconditions++;this.record('postcondition-returned',{assertion:key});return result;
    };
    return target[key];
  }});}
}

function runDriver(driver,args,evidence) {
  need(args.length===5,'five unchanged original arguments required');
  const [pw,historical,root,out,engine]=args;
  const isolation=verifyIsolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT),sources=verifyInputs(driver,historical);
  need(!fs.existsSync(out),'original output must be fresh');
  need(path.resolve(evidence)!==path.resolve(out),'retention and original outputs must differ');
  const retain=new RainRetention(evidence);
  retain.record('sources',{sources,isolation,wrapperSha256:sha(fs.readFileSync(__filename)),pinsSha256:sha(fs.readFileSync(PIN_PATH)),
    researchCommit:pins.researchCommit,historicalCommit:pins.historicalCommit,originalArgv:args});
  executeOriginal(driver,args,retain);return retain;
}
// Separate callable for offline dependency doubles. The CLI always enters via
// runDriver's source and current namespace admission, never through this helper.
function executeOriginal(driver,args,retain,load=Module.createRequire(path.resolve(driver))) {
  const [pw,historical,root,out,engine]=args;
  const filename=path.resolve(driver), helper=path.resolve(historical,'tools/qa/precip_eval_lib.cjs');
  const source=fs.readFileSync(filename,'utf8');
  need(sha(Buffer.from(source))===pins.files['tools/qa/r0040/native-options.cjs'],'source digest mismatch: original driver');
  const mod=new Module(filename,module);mod.filename=filename;mod.paths=Module._nodeModulePaths(path.dirname(filename));
  mod.require=request=>{
    if(request===helper)return retain.wrapHelper(load(request));
    if(request===pw)return retain.wrapPlaywright(load(request),engine);
    if(request==='./native-option-oracle.cjs')return retain.wrapOracle(load(request));
    if(request==='node:assert/strict')return retain.wrapAssert(load(request));
    return load(request);
  };
  const originalError=console.error;
  console.error=(...values)=>{retain.journal.preserve('driver-error-output',{errors:values.map(errorData)});return originalError(...values);};
  process.argv=[process.argv[0],filename,...args];
  process.once('beforeExit',()=>{
    console.error=originalError;
    const terminalStatus=()=>{
      if(retain.continuationVeto)process.exitCode=86;
      if(retain.journal.retentionError&&!(process.exitCode>0))process.exitCode=1;
    };
    const finalizationFailure=error=>{
      retain.journal.retentionError ||= error;
      terminalStatus();
      try {originalError('R0040 retention finalization failed:',error);}catch(_){}
    };
    terminalStatus();
    try {
      retain.journal.record('driver-process-ended',{exitCode:process.exitCode||0,originalReportExists:fs.existsSync(path.join(out,'native-options.json')),continuationVetoed:Boolean(retain.continuationVeto),
        retentionError:retain.journal.retentionError?errorData(retain.journal.retentionError):null});
    } catch(error) {
      finalizationFailure(error);
      // Preserve the failed attempt; append a correction only if the sink can
      // still accept it. The actual child exit remains authoritative.
      retain.journal.preserve('retention-finalization-failed',{exitCode:process.exitCode,error:errorData(error)});
    }
    try {retain.journal.close();}catch(error){finalizationFailure(error);}
    terminalStatus();
  });
  try {mod._compile(source,filename);}
  catch(error){retain.failure('driver-load-threw',error);throw error;}
  return retain;
}
if(require.main===module) {
  const args=process.argv.slice(2),separator=args.indexOf('--');
  need(separator===4&&args[0]==='--driver'&&args[2]==='--evidence',
    'usage: retain_r0040.cjs --driver ORIGINAL --evidence NEW_PRIVATE_DIR -- PLAYWRIGHT HISTORICAL BUILT_TREE NEW_OUT ENGINE');
  runDriver(args[1],args.slice(separator+1),args[3]);
}
module.exports={RainRetention,Journal,verifyInputs,verifyIsolation,allowedContinuation,runDriver,executeOriginal};
