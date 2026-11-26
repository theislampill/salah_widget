'use strict';
// Disposable research-harness support. These checks add no product policy.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {assertNativeUi}=require('./r003f_ui.cjs');
const PROTOCOL='R003F/corrected-matrix-harness/1',REPORT_PROTOCOL='R003F/P1/native-matrix-ui/1';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const plainError=e=>({name:String(e?.name||'Error'),message:String(e?.message??e),...(e?.code?{code:String(e.code)}:{})});
function regular(root,relative){
  assert.ok(typeof relative==='string'&&relative&&!path.isAbsolute(relative)&&!relative.split(/[\\/]/).some(x=>!x||x==='.'||x==='..'),'relative regular-file path required');
  let current=root;
  for(const part of relative.split('/')){current=path.join(current,part);assert.equal(fs.lstatSync(current).isSymbolicLink(),false,'symlink refused: '+relative);}
  assert.ok(fs.statSync(current).isFile(),'not a regular file: '+relative);return fs.readFileSync(current);
}
function filesUnder(root){
  const result=[];
  function visit(relative){
    for(const name of fs.readdirSync(path.join(root,relative)).sort()){
      const rel=relative?relative+'/'+name:name,s=fs.lstatSync(path.join(root,rel));
      assert.equal(s.isSymbolicLink(),false,'symlink refused: '+rel);
      if(s.isDirectory())visit(rel);else{assert.ok(s.isFile(),'nonregular artifact: '+rel);result.push(rel);}
    }
  }
  visit('');return result.sort();
}
function admitClosure(root,expectedSha256){
  assert.match(expectedSha256??'',/^[0-9a-f]{64}$/,'independent expected materialization SHA-256 is required');
  root=fs.realpathSync(root);const bytes=regular(root,'materialization.json');
  assert.equal(hash(bytes),expectedSha256,'materialization differs from independent expected digest');
  const m=JSON.parse(bytes);assert.equal(m.protocol,PROTOCOL);assert.equal(m.status,'PREPARED');
  assert.equal(m.nativeExecution,'NOT_RUN');assert.equal(m.sourceFiles.length,14);assert.equal(m.outputFiles.length,16);
  assert.equal(new Set(m.sourceFiles.map(f=>f.path)).size,14);assert.equal(new Set(m.outputFiles.map(f=>f.path)).size,16);
  for(const f of m.outputFiles){const b=regular(root,f.path);assert.equal(hash(b),f.sha256,'derived helper digest: '+f.path);assert.equal(b.length,f.bytes);}
  assert.deepEqual(filesUnder(root),['materialization.json',...m.outputFiles.map(f=>f.path)].sort(),'derived directory is not the exact materialized closure');
  return {protocol:PROTOCOL,materializationSha256:expectedSha256,sourceProtocol:'R003F/P1/native-matrix/2',
    outputFiles:m.outputFiles.map(({path,sha256,bytes})=>({path,sha256,bytes}))};
}
function createLifecycle(report){
  const r=report.lifecycle={protocol:'R003F/matrix-lifecycle/1',phase:'RUNNING',browserEventsBound:false,pages:[],faults:[],cleanups:[]};
  const pages=new Map();let cleaning=false,closingBrowser=false;
  const fault=(kind,error,detail={})=>{const f={kind,...detail,error:plainError(error)};r.faults.push(f);return f;};
  function watchPage(p){
    if(pages.has(p))return p;
    const state={id:r.pages.length+1,eventsBound:typeof p.on==='function',closeRequested:false,closed:false};
    r.pages.push(state);pages.set(p,state);
    if(state.eventsBound){
      p.on('crash',()=>fault('page-crash',Error('page crashed'),{page:state.id}));
      p.on('close',()=>{state.closed=true;if(!state.closeRequested&&!cleaning)fault('unexpected-page-close',Error('page closed outside requested cleanup'),{page:state.id});});
    }else if(report.evidenceClass==='native')fault('missing-page-events',Error('native page event API is absent'),{page:state.id});
    const close=p.close.bind(p);
    p.close=async(...args)=>{state.closeRequested=true;try{const value=await close(...args);state.closed=true;return value;}
      catch(e){fault('page-cleanup',e,{page:state.id});}};
    return p;
  }
  function watchSession(session){
    r.browserEventsBound=typeof session.browser.on==='function';
    if(r.browserEventsBound)session.browser.on('disconnected',()=>{if(!closingBrowser)fault('unexpected-browser-disconnect',Error('browser disconnected before requested cleanup'));});
    else if(report.evidenceClass==='native')fault('missing-browser-events',Error('native browser event API is absent'));
  }
  function watchContext(context){const newPage=context.newPage.bind(context);context.newPage=async(...args)=>watchPage(await newPage(...args));}
  async function cleanup(label,work){
    if(label==='context'){cleaning=true;for(const state of pages.values())state.closeRequested=true;}
    if(label==='session')closingBrowser=true;
    try{await work();r.cleanups.push({label,status:'PASS'});if(label==='context')for(const state of pages.values())state.closed=true;}
    catch(e){r.cleanups.push({label,status:'FAIL',error:plainError(e)});fault('cleanup',e,{label});}
  }
  return {record:r,fault,watchPage,watchContext,watchSession,cleanup};
}
async function readAfter(page,facts){try{return {value:await page.evaluate(facts),error:null};}catch(error){return {value:null,error};}}
function retainBytes(report,name,bytes,write){
  try{write(name,bytes);return {status:'RETAINED',bytes:bytes.length};}
  catch(e){const error=plainError(e);(report.retentionFaults??=[]).push({path:name,error});return {status:'RETENTION_FAILED',bytes:bytes.length,error};}
}
function retainCapture(report,tag,{state,after,afterError,admission,document},bytes,write){
  const capture={state,after,admission,document,sha256:hash(bytes),retention:retainBytes(report,tag+'.png',bytes,write)};
  if(afterError)capture.afterError=plainError(afterError);report.captures[tag]=capture;return capture;
}
function requireRetained(record){if(record.retention?.status!=='RETAINED')throw Object.assign(Error('capture retention failed'),{code:'R003F_RETENTION_FAILED'});}
function uiVerdict(report){
  const failures=[];let checkedCaptures=0,checkedFrames=0;
  const check=(state,label)=>{try{assertNativeUi(state?.nativeUi);}catch(e){failures.push({label,error:plainError(e)});}};
  for(const [tag,c] of Object.entries(report.captures||{})){checkedCaptures++;check(c.state,tag+' before');check(c.after,tag+' after');}
  for(const s of report.streams||[])for(const [i,f] of s.frames.entries()){checkedFrames++;check(f.before,s.label+'/'+i+' before');check(f.after,s.label+'/'+i+' after');}
  return {protocol:'R003F/matrix-ui/1',status:failures.length?'INCOMPLETE':'PASS',checkedCaptures,checkedFrames,failures};
}
function requireUi(report){const result=report.harnessUi=uiVerdict(report);if(result.status!=='PASS')throw Object.assign(Error('matrix native UI admission incomplete'),{code:'R003F_UI_INCOMPLETE'});}
function cadence(frames){return {startsMs:frames.map(f=>f.started),durationsMs:frames.map(f=>f.ended-f.started),oneCapturePerSecond:frames.every((f,i)=>f.started>=1000*i&&f.ended>=f.started&&f.ended<1000*(i+1))};}
async function supplemental(page,{report,tag,facts,write,document,originalError}){
  // The original gate already failed. This observation can explain that failure
  // but cannot stand in for the original capture or create an admitted metric.
  const record={captureKind:'supplementary-after-original-failure',originalError:plainError(originalError),state:null,after:null};
  (report.supplementalCaptures??={})[tag]=record;
  try{
    try{record.state=await page.evaluate(facts);}catch(e){record.beforeError=plainError(e);}
    const bytes=await page.locator('.c').screenshot({timeout:10000});record.sha256=hash(bytes);
    const after=await readAfter(page,facts);record.after=after.value;if(after.error)record.afterError=plainError(after.error);
    record.document=document;record.retention=retainBytes(report,tag+'.png',bytes,write);
  }catch(e){record.observationError=plainError(e);}
}
function disposition(report){
  if(report.network?.ok===false){report.status='ISOLATION FAIL';return 3;}
  if(report.status==='ANDON')return 4;
  if(report.lifecycle?.faults.length||report.retentionFaults?.length||report.harnessUi?.status==='INCOMPLETE'){
    if(report.status!=='INCOMPLETE'&&report.status!=='PARTIAL')report.reason='matrix lifecycle, retention or UI admission incomplete';
    report.status='INCOMPLETE';return 2;
  }
  return ['ACQUIRED','DIAGNOSTIC'].includes(report.status)?0:2;
}
async function finishMatrix({report,context,session,server,out,write,lifecycle}){
  // Every cleanup is attempted even when a preceding one failed. None can
  // replace an already observed physical Andon or the final isolation verdict.
  if(context)await lifecycle.cleanup('context',()=>context.context.close());
  if(session)await lifecycle.cleanup('session',()=>session.close());
  if(session){
    try{report.network=session.verdict();}catch(e){lifecycle.fault('isolation-verdict-unavailable',e);}
    try{retainBytes(report,'network.jsonl',Buffer.from(session.ledger.requests.map(x=>JSON.stringify(x)).join('\n')+'\n'),write);}
    catch(e){lifecycle.fault('network-ledger-unavailable',e);}
  }
  await lifecycle.cleanup('server',()=>new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve())));
  report.harnessUi=uiVerdict(report);report.lifecycle.phase='FINALIZED';
  try{report.artifacts=Object.fromEntries(filesUnder(out).filter(f=>f!=='summary.json').map(f=>{const b=regular(out,f);return [f,{sha256:hash(b),bytes:b.length}];}));}
  catch(e){lifecycle.fault('artifact-inventory',e);report.artifacts=null;}
  let exitCode=disposition(report);
  try{write('summary.json',JSON.stringify(report,null,2)+'\n');}
  catch(e){lifecycle.fault('summary-retention',e);exitCode=disposition(report);}
  return exitCode;
}
function admitReceipt(report,{root,expectedSha256,file,fixtureOnly}){
  assert.equal(report.protocol,REPORT_PROTOCOL);assert.deepEqual(report.harness,admitClosure(root,expectedSha256),'report harness differs from independently pinned complete closure');
  const life=report.lifecycle;assert.equal(life?.protocol,'R003F/matrix-lifecycle/1');assert.equal(life.phase,'FINALIZED');assert.deepEqual(life.faults,[]);
  assert.deepEqual(life.cleanups,[{label:'context',status:'PASS'},{label:'session',status:'PASS'},{label:'server',status:'PASS'}]);
  assert.ok(Array.isArray(life.pages)&&life.pages.length>0);assert.ok(life.pages.every((p,i)=>p.id===i+1&&p.closeRequested===true&&p.closed===true));
  if(!fixtureOnly){assert.equal(life.browserEventsBound,true,'native browser lifecycle binding is absent');assert.ok(life.pages.every(p=>p.eventsBound===true),'native page lifecycle binding is absent');}
  assert.deepEqual(report.retentionFaults,[]);assert.equal(report.supplementalCaptures,undefined);
  const ui=uiVerdict(report);assert.equal(ui.status,'PASS','semantic native UI admission failed');assert.deepEqual(report.harnessUi,ui);
  const captures=[...Object.entries(report.captures||{}).map(([tag,c])=>[tag+'.png',c]),...(report.streams||[]).flatMap(s=>s.frames.map(f=>[f.file,f]))];
  assert.ok(life.pages.length>=new Set(captures.map(([,c])=>c.document?.id)).size,'untracked captured document');
  for(const [name,c] of captures){
    assert.ok(c.after&&c.afterError===undefined,'missing original after-state');requireRetained(c);assert.ok(Number.isSafeInteger(c.retention.bytes)&&c.retention.bytes>0);
    assert.deepEqual(c.retention,{status:'RETAINED',bytes:report.artifacts?.[name]?.bytes},'retention byte count differs from the exact artifact');
  }
  for(const s of report.streams||[]){assert.equal(s.status,'CAPTURED');assert.equal(s.error,undefined);assert.equal(s.frames.length,50);assert.deepEqual(s.cadence,cadence(s.frames));}
  const dir=fs.realpathSync(path.dirname(file)),summary=path.basename(file);
  assert.deepEqual(filesUnder(dir).filter(f=>f!==summary),Object.keys(report.artifacts).sort(),'unlisted or missing capture artifact');
}
module.exports={PROTOCOL,REPORT_PROTOCOL,hash,plainError,regular,filesUnder,admitClosure,createLifecycle,readAfter,retainBytes,retainCapture,
  requireRetained,uiVerdict,requireUi,cadence,supplemental,disposition,finishMatrix,admitReceipt};
