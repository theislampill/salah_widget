'use strict';
// Exercises the driver's actual JavaScript boundary with native Promises.
// No browser, font service, product rendering or native acceptance is implied.
const test=require('node:test'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process'),path=require('node:path'),vm=require('node:vm');
const driver=path.join(__dirname,'../tools/cp9/r0007_browser.py');
const exported=JSON.parse(execFileSync('python3',['-c',
  'import importlib.util,json,sys;s=importlib.util.spec_from_file_location("d",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps({"poll":getattr(m,"ASYNC_WAIT_POLL",None),"state":getattr(m,"ASYNC_WAIT_STATE",None)}))',driver],{encoding:'utf8'}));
// The absence fallback is the original direct predicate call: its Promise
// return is exactly the immediate-truthiness defect retained in the RED probe.
const original='({source}) => (0,eval)("("+source+")")()';
function scene(){
  const context=vm.createContext({performance:{now:()=>0}});
  const poll=vm.runInContext(exported.poll||original,context);
  const state=vm.runInContext(exported.state||'({pending:false,accepted:false,cancelled:false,error:null,attempts:0,falseResults:0})',context);
  return {context,poll,state};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function invoke(s,source){
  const result=s.poll({state:s.state,source});
  // Preserve the legacy Promise value for assertions, but consume a rejection
  // so the RED test reports the boundary failure instead of an unrelated leak.
  if(result&&typeof result.then==='function')result.catch(()=>{});
  return result;
}
test('synchronous true is a live positive control',async()=>{
  const s=scene();let result=false;
  for(let i=0;i<3&&!result;i++){result=invoke(s,'() => true');await tick();}
  assert.equal(result,true);
});
test('an async false result cannot satisfy the wait; later true is polled',async()=>{
  const s=scene();s.context.calls=0;
  const source='async () => ++calls >= 3';
  let result;
  for(let i=0;i<8;i++){
    result=invoke(s,source);
    assert.equal(typeof result,'boolean','poll must return a boolean, never a Promise');
    if(result)break;
    await tick();
  }
  assert.equal(result,true);assert.equal(s.context.calls,3);assert.equal(s.state.falseResults,2);
});
test('an always-false async predicate remains unavailable',async()=>{
  const s=scene();
  for(let i=0;i<3;i++){
    assert.equal(invoke(s,'async () => false'),false);
    await tick();
  }
  assert.equal(s.state.accepted,false);assert.equal(s.state.falseResults,3);
});
test('a pending predicate is not overlapped and a late result cannot credit cancellation',async()=>{
  const s=scene();s.context.calls=0;
  const source='() => { calls++; return new Promise(resolve=>{globalThis.release=resolve;}); }';
  assert.equal(invoke(s,source),false);await tick();
  for(let i=0;i<4;i++)assert.equal(invoke(s,source),false);
  assert.equal(s.context.calls,1);
  s.state.cancelled=true;s.context.release(true);await tick();
  assert.equal(s.state.accepted,false);assert.equal(invoke(s,source),false);
});
test('an async rejection fails diagnostically instead of becoming truthy or unhandled',async()=>{
  const s=scene(),source='async () => {throw new Error("observer-boundary-failure");}';
  assert.equal(invoke(s,source),false);await tick();
  assert.throws(()=>invoke(s,source),/observer-boundary-failure/);
  assert.equal(s.state.accepted,false);
});
