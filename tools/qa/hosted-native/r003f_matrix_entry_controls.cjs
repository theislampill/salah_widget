'use strict';
// Source-only controls. No browser or native namespace is created.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const file=path.join(__dirname,'r003f_matrix_entry.cjs');
let E=null;try{E=require(file);}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;}
function temp(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'matrix-central-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return p;}
test('terminal custody failure cannot overrule original isolation or Andon',()=>{
 assert.ok(E,'entry implementation required');
 for(const code of [0,2,3,4,86])assert.equal(E.terminalCode({returncode:code,timedOut:false},Error('disk')),code===0?2:code);
 assert.equal(E.terminalCode({returncode:0,timedOut:true},null),2);
});
test('actual original child exit and streams survive entry execution',async t=>{
 assert.ok(E);const d=temp(t),script=path.join(d,'child.cjs');fs.writeFileSync(script,"process.stdout.write('retained');process.stderr.write('error-stream');process.exit(4)");
 const r=await E.childProcess([process.execPath,script],d,{...process.env},2,{stdout:path.join(d,'out'),stderr:path.join(d,'err')});
 assert.equal(r.returncode,4);assert.equal(r.timedOut,false);assert.equal(fs.readFileSync(path.join(d,'out'),'utf8'),'retained');assert.equal(fs.readFileSync(path.join(d,'err'),'utf8'),'error-stream');
});
test('actual timeout terminates child process and retains its prefix',async t=>{
 assert.ok(E);const d=temp(t),script=path.join(d,'child.cjs');fs.writeFileSync(script,"process.stdout.write('prefix');setInterval(()=>{},1000)");
 const r=await E.childProcess([process.execPath,script],d,{...process.env},.1,{stdout:path.join(d,'out'),stderr:path.join(d,'err')});
 assert.equal(r.timedOut,true);assert.equal(r.signal,'SIGKILL');assert.equal(fs.readFileSync(path.join(d,'out'),'utf8'),'prefix');
});
test('absent namespace rejects before source imports or original execution',t=>{
 assert.ok(E);const {spawnSync}=require('node:child_process'),d=temp(t);
 const r=spawnSync(process.execPath,[file,'--entry','unread','--pins-sha256','unread','--evidence',path.join(d,'evidence'),'--engine','chromium','--dpr','1','--id','unread','--variant','B0','--native-seconds','1800','--','unread'],{env:{...process.env,SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT:''},encoding:'utf8'});
 assert.equal(r.status,86,r.stderr);assert.equal(fs.existsSync(path.join(d,'evidence/driver.json')),true);
});
test('final fsync failure propagates as terminal failure with original error precedence',t=>{
 assert.ok(E);const d=temp(t),sync=fs.fsyncSync;fs.fsyncSync=()=>{throw Error('controlled final fsync');};
 try{assert.throws(()=>E.durable(path.join(d,'receipt.json'),{status:0}),/final fsync/);}finally{fs.fsyncSync=sync;}
 assert.equal(E.terminalCode({returncode:0,timedOut:false},Error('controlled final fsync')),2);
 assert.equal(E.terminalCode({returncode:3,timedOut:false},Error('controlled final fsync')),3);
});
test('current source manifest rejects drift before loading the original driver',t=>{
 const d=temp(t),manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'r003f-matrix-central-pins.json')));
 for(const file of ['r003f-matrix-central-pins.json',...Object.keys(manifest.files)])fs.copyFileSync(path.join(__dirname,file),path.join(d,file));
 const cloned=require(path.join(d,'r003f_matrix_entry.cjs')),hash=require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(d,'r003f-matrix-central-pins.json'))).digest('hex');
 assert.equal(cloned.pins(hash).sha256,hash);fs.appendFileSync(path.join(d,'r003f_matrix_support.cjs'),'\n// controlled drift');assert.throws(()=>cloned.pins(hash),/source differs/);
});
test('duplicated or substituted original arguments are refused',()=>{
 const old=process.env.NODE_PATH;process.env.NODE_PATH='/synthetic/modules';
 try{
  const options={engine:'chromium',dpr:'1',id:'owner_11150942_owner_wax_-81.9_150_clear_shipped_reduce_default',variant:'B0'};
  const admission={runtime:'/synthetic/runtime',harness:{materializationSha256:'a'.repeat(64)}};
  const argv=['--root',admission.runtime,'--out','/synthetic/output','--engine','chromium','--dpr','1','--id',options.id,'--playwright','/synthetic/modules/playwright','--pngjs','/synthetic/modules/pngjs','--materialization-sha256','a'.repeat(64),'--variant','B0'];
  assert.equal(E.originalArguments(argv,options,admission).id,options.id);
  assert.throws(()=>E.originalArguments([...argv,'--variant','B0'],options,admission));
  const changed=[...argv];changed[1]='/substitute/runtime';assert.throws(()=>E.originalArguments(changed,options,admission));
 }finally{if(old===undefined)delete process.env.NODE_PATH;else process.env.NODE_PATH=old;}
});
test('actual launch error releases its timeout and terminates promptly',()=>{
 const {spawnSync}=require('node:child_process');
 const code="require(process.argv[1]).childProcess(['/does-not-exist-r003f-control'],'/',process.env,10).then(()=>{process.exitCode=1},()=>{process.exitCode=2})";
 const r=spawnSync(process.execPath,['-e',code,file],{encoding:'utf8',timeout:500});
 assert.equal(r.status,2,'failed launch must not wait for its native timeout: '+r.error);
});
