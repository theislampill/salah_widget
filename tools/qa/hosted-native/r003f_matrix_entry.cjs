'use strict';
// Process custody only. Original derived driver bytes/argv execute in a child.
// No frame listener, screenshot copy or per-frame host write is added.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {spawn,spawnSync}=require('node:child_process'),{parseArgs}=require('node:util');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function durable(file,value){const fd=fs.openSync(file,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(value,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
function terminalCode(p,error){if([86,3,4].includes(p.returncode))return p.returncode;return p.timedOut||p.returncode==null||error?2:p.returncode;}
function isolation(file){
 try{
  assert.ok(file,'current isolation receipt required');const bytes=fs.readFileSync(file),r=JSON.parse(bytes);
  assert.equal(r.protocol,'salah-hosted-native-isolation/1');assert.equal(r.passed,true);assert.equal(r.browserControl?.passed,true);
  assert.ok(process.getuid()>0);assert.equal(r.uid,process.getuid());assert.equal(r.netns,fs.readlinkSync('/proc/self/ns/net'));
  assert.ok(r.outerNetns&&r.netns!==r.outerNetns);
  return {path:path.resolve(file),sha256:sha(bytes)};
 }catch(e){e.exitCode=86;throw e;}
}
function pins(expected){
 const file=path.join(__dirname,'r003f-matrix-central-pins.json'),bytes=fs.readFileSync(file);assert.equal(sha(bytes),expected,'central source manifest differs');
 const p=JSON.parse(bytes);assert.equal(p.protocol,'R003F/matrix-central-source/1');
 for(const [name,hash] of Object.entries(p.files)){const f=path.join(__dirname,name);assert.ok(!fs.lstatSync(f).isSymbolicLink());assert.equal(sha(fs.readFileSync(f)),hash,'central source differs: '+name);}
 return {path:file,sha256:expected};
}
function childProcess(argv,cwd,env,seconds,streams){
 return new Promise((resolve,reject)=>{
  let fds=[],child,timer,timedOut=false;
  try{
   fds=streams?[fs.openSync(streams.stdout,'wx',0o600),fs.openSync(streams.stderr,'wx',0o600)]:[];
   child=spawn(argv[0],argv.slice(1),{cwd,env,detached:true,stdio:streams?['ignore',...fds]:'inherit'});
   timer=setTimeout(()=>{timedOut=true;try{process.kill(-child.pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')reject(e);}},seconds*1000);
   child.once('error',reject);child.once('close',(returncode,signal)=>{clearTimeout(timer);resolve({returncode,signal,timedOut});});
  }catch(e){reject(e);}finally{for(const fd of fds)fs.closeSync(fd);}
 });
}
function originalArguments(a,options,admission){
 const values=parseArgs({args:a,options:Object.fromEntries(['root','out','engine','dpr','id','variant','playwright','pngjs','materialization-sha256'].map(k=>[k,{type:'string'}])),strict:true}).values;
 const expected={root:admission.runtime,out:values.out,engine:options.engine,dpr:options.dpr,id:options.id,
   playwright:path.join(process.env.NODE_PATH,'playwright'),pngjs:path.join(process.env.NODE_PATH,'pngjs'),'materialization-sha256':admission.harness.materializationSha256};
 if(options.variant!=='all')expected.variant=options.variant;
 assert.deepEqual({...values},expected,'original argv or selected cell differs');
 assert.deepEqual(a,Object.entries(expected).flatMap(([key,value])=>['--'+key,value]),'original argv order, multiplicity or population differs');
 assert.ok(path.isAbsolute(values.out)&&path.isAbsolute(values.playwright)&&path.isAbsolute(values.pngjs));
 const selector=JSON.parse(fs.readFileSync(path.join(__dirname,'r003f-matrix-catalogue.json')));
 const pop=selector.populations.find(p=>p.engine===options.engine&&p.dpr===Number(options.dpr));
 assert.equal(pop?.cells.filter(c=>c.id===options.id).length,1);assert.ok(options.variant==='all'||selector.variants.includes(options.variant));
 return values;
}
async function run(argv=process.argv.slice(2)){
 const split=argv.indexOf('--');assert.ok(split>=0,'original driver arguments required');
 const o=parseArgs({args:argv.slice(0,split),options:Object.fromEntries(['entry','pins-sha256','evidence','engine','dpr','id','variant','native-seconds'].map(k=>[k,{type:'string'}])),strict:true}).values;
 const original=argv.slice(split+1);assert.ok(o.evidence&&path.isAbsolute(o.evidence));fs.mkdirSync(o.evidence,{mode:0o700});
 const r={protocol:'R003F/matrix-driver/1',instrumentation:'Host preflight and terminal process custody; no per-frame writes or pixel copies.',
  originalDriverUnchanged:true,originalArgv:[process.execPath,...original],process:{returncode:null,timedOut:false},retentionError:null};
 let error=null;
 try{
  r.isolation=isolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);r.central=pins(o['pins-sha256']);
  const entry=JSON.parse(fs.readFileSync(o.entry)),python=entry.argv[0];
  const command=[python,path.join(__dirname,'r003f_matrix_campaign.py'),'admit','--entry',o.entry,'--pins-sha256',o['pins-sha256'],'--native','--engine',o.engine,'--dpr',o.dpr,'--id',o.id,'--variant',o.variant];
  const check=spawnSync(command[0],command.slice(1),{cwd:__dirname,encoding:'utf8',timeout:90000,maxBuffer:4*1024*1024});
  r.sourceCheck={argv:command,cwd:__dirname,returncode:check.status,timedOut:check.error?.code==='ETIMEDOUT',signal:check.signal,error:check.error?.message||null};
  durable(path.join(o.evidence,'source-check.json'),r.sourceCheck);
  for(const [name,bytes] of [['source.stdout',check.stdout||''],['source.stderr',check.stderr||'']]){const fd=fs.openSync(path.join(o.evidence,name),'wx',0o600);try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
  assert.equal(check.status,0,'current source/preparation admission failed');assert.ok(!check.error);
  r.admission=JSON.parse(check.stdout);assert.equal(r.admission.status,'PASS');
  assert.equal(original[0],path.join(r.admission.root,'tools/qa/r003f_matrix.cjs'));assert.equal(r.admission.node,process.execPath);
  r.selection={id:o.id,variant:o.variant,engine:o.engine,dpr:Number(o.dpr)};
  originalArguments(original.slice(1),o,r.admission);
  const seconds=Number(o['native-seconds']);assert.equal(seconds,r.admission.matrix.budget.nativeSeconds,'native ceiling differs from original selected population');
  r.nativeSeconds=seconds;r.cwd=r.admission.research;
  durable(path.join(o.evidence,'started.json'),r);
  r.process=await childProcess(r.originalArgv,r.cwd,{...process.env},seconds);
 }catch(e){error=e;r.error={name:e.name,message:e.message,stack:e.stack};if(e.exitCode)r.process.returncode=e.exitCode;}
 r.exitCode=terminalCode(r.process,error);
 try{durable(path.join(o.evidence,'driver.json'),r);}catch(e){r.retentionError=e.message;error=error||e;process.stderr.write('matrix terminal retention failed: '+e.message+'\n');}
 return terminalCode(r.process,error);
}
module.exports={durable,terminalCode,isolation,pins,childProcess,originalArguments,run};
if(require.main===module)run().then(code=>{process.exitCode=code;},e=>{process.stderr.write(e.stack+'\n');process.exitCode=e.exitCode||2;});
