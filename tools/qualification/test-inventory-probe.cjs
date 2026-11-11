'use strict';
// Actual probe orchestration with an owned-process double and deterministic
// clock. These are collector controls, never Windows/native qualification.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const {EventEmitter}=require('node:events');
const probe=process.argv[2]||path.join(__dirname,'r0017-inventory-probe.cjs');
const base=process.argv[3]||path.join(__dirname,'r0017-windows-proof.cjs');
const source=fs.readFileSync(probe,'utf8'),baseBytes=fs.readFileSync(base),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(kind){
 let now=0,sequence=0,settled=false;const timers=new Map(),files=new Map(),calls=[];
 const child=new EventEmitter();child.pid=202;child.stdout=new EventEmitter();child.stderr=new EventEmitter();
 child.stdout.destroy=()=>calls.push('stdout.destroy');child.stderr.destroy=()=>calls.push('stderr.destroy');child.unref=()=>calls.push('unref');
 child.kill=signal=>{calls.push({signal,at:now});return true;};
 const fakeFs={existsSync:()=>false,readdirSync:()=>[],mkdirSync:()=>{},
  readFileSync:p=>p===base?baseBytes:p===probe?Buffer.from(source):Buffer.from('owned-executable-double'),
  writeFileSync:(p,b)=>files.set(p,Buffer.isBuffer(b)?b.toString():String(b)),copyFileSync:(a,b)=>files.set(b,source)};
 const fakeProcess={pid:101,arch:'x64',platform:'win32',version:'test-only-node',env:{SystemRoot:'C:\\Windows',ProgramFiles:'C:\\Program Files'},exitCode:undefined,
  argv:['node',probe,'--base-file',base,'--base-sha',sha(baseBytes),'--engine','winps','--out','/controlled-output']};
 const context={Buffer,console,process:fakeProcess,__filename:probe,performance:{now:()=>now},
  setTimeout:(fn,ms)=>{const id=++sequence;timers.set(id,{fn,at:now+ms});return id;},clearTimeout:id=>timers.delete(id),
  require:id=>id==='node:fs'?fakeFs:id==='node:child_process'?{spawn:(...args)=>{calls.push({spawn:args[0],at:now});return child;}}:require(id)};
 const completion=vm.runInNewContext(source,context,{filename:probe});
 Promise.resolve(completion).then(()=>{settled=true;});
 const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 const advance=async target=>{while(true){const due=[...timers].filter(([,t])=>t.at<=target).sort((a,b)=>a[1].at-b[1].at)[0];if(!due)break;now=due[1].at;timers.delete(due[0]);due[1].fn();await flush();}now=target;await flush();};
 const receipt=()=>JSON.parse([...files].find(([p])=>p.endsWith('/inventory-probe.json'))[1]);
 if(kind==='early-capture'){
  await advance(100);child.stdout.emit('data',Buffer.alloc(262145,120));await flush();
  assert.equal(calls.filter(x=>x.signal).length,1,'only original owned handle is stopped');
  await advance(5099);assert.equal(settled,false,'do not invent early terminal evidence');
  await advance(5100);
  assert.equal(settled,true,'early capture failure must finalize by original stop time +5000ms');
  const r=receipt();assert.equal(r.containment.ok,false);assert.equal(r.status,'CAPABILITY_NOT_ESTABLISHED');assert.equal(fakeProcess.exitCode,1);
  assert.equal(r.stop.reason,'CAPTURE_BOUND_EXCEEDED');assert.equal(r.errors.filter(x=>x.stage==='cleanup').length,1);
 }else if(kind==='query-deadline'){
  await advance(5000);assert.equal(calls.filter(x=>x.signal).length,1);
  await advance(5001);child.emit('exit',null,'SIGTERM');child.emit('close',null,'SIGTERM');await flush();
  const r=receipt();assert.equal(settled,true);assert.equal(r.completedWithin5000ms,false);assert.equal(r.containment.ok,true);assert.equal(r.status,'CAPABILITY_NOT_ESTABLISHED');
  assert.equal(r.stop.reason,'QUERY_DEADLINE_5000MS');assert.equal(fakeProcess.exitCode,0,'contained negative collection is explicit, never capability PASS');
 }else{
  await advance(100);child.stdout.emit('data',Buffer.from(JSON.stringify([{ProcessId:101,ParentProcessId:1,Name:'node.exe',CreationDate:'2026-11-08T00:00:00Z'},{ProcessId:202,ParentProcessId:101,Name:'powershell.exe',CreationDate:'2026-11-08T00:00:01Z'}])));
  await advance(200);child.emit('exit',0,null);child.emit('close',0,null);await flush();
  const r=receipt();assert.equal(settled,true);assert.equal(r.completedWithin5000ms,true);assert.equal(r.containment.ok,true);assert.equal(r.status,'CAPABILITY_OBSERVED_WITHIN_ORIGINAL_BOUND');assert.equal(calls.filter(x=>x.signal).length,0);
 }
 return {name:kind,status:'PASS'};
}
(async()=>{const results=[];for(const name of ['early-capture','query-deadline','timely-identity']){try{results.push(await run(name));}catch(e){results.push({name,status:'FAIL',error:String(e.stack||e)});}}console.log(JSON.stringify({schema:'r0017-inventory-orchestration-controls/v1',probeSha256:sha(source),baseSha256:sha(baseBytes),nativeExecutions:0,results},null,2));if(results.some(r=>r.status==='FAIL'))process.exitCode=1;})();
