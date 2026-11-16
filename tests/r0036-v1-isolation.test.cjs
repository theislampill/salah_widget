'use strict';
// R0036 V1 browser verification (issue 103, owner decision 2026-11-16): unit tests of the process-side isolation
// layer, no browser. The guard is installed first in this test process, so every probe below is refused before a
// socket opens or a name resolves. Refusal probes target 0.0.0.0 (refused by the OS locally even without the guard)
// except the name probes, which run only after the guard is proven installed.
const assert=require('node:assert/strict'),{test}=require('node:test');
const path=require('node:path'),{spawnSync}=require('node:child_process');
const guard=require('../tools/qa/v1_net_guard.cjs');guard.install();
const http=require('node:http'),net=require('node:net'),dns=require('node:dns');
const HELPERS=path.join(__dirname,'..','tools','qa','v1_browser_helpers.py');

test('V1I-01 loopback classification: only 127/8, ::1 and localhost are loopback',()=>{
  for(const h of ['127.0.0.1','127.9.9.9','localhost','::1','[::1]','::ffff:127.0.0.1'])assert.equal(guard.isLoopback(h),true,h);
  for(const h of ['0.0.0.0','10.0.0.1','192.168.1.1','fonts.googleapis.com','api.aladhan.com','::','::ffff:8.8.8.8','128.0.0.1'])assert.equal(guard.isLoopback(h),false,h);
});

test('V1I-02 the Node guard refuses non-loopback http, fetch, raw socket and DNS before any connection, and logs each',async()=>{
  assert.equal(guard.state.installed,true);const before=guard.state.refused.length;
  await assert.rejects(new Promise((res,rej)=>{try{http.get('http://0.0.0.0:9/x',res).on('error',rej);}catch(e){rej(e);}}),e=>e.code==='ER0036_ISOLATED');
  await assert.rejects(fetch('http://0.0.0.0:9/x'),e=>e.code==='ER0036_ISOLATED');
  await assert.rejects(new Promise((res,rej)=>{const s=net.connect({host:'0.0.0.0',port:9});s.on('connect',res);s.on('error',rej);}),e=>e.code==='ER0036_ISOLATED');
  await assert.rejects(dns.promises.lookup('fonts.googleapis.com'),e=>e.code==='ER0036_ISOLATED');
  await assert.rejects(new Promise((res,rej)=>dns.lookup('api.aladhan.com',(e,a)=>e?rej(e):res(a))),e=>e.code==='ER0036_ISOLATED');
  assert.ok(guard.state.refused.length>=before+5,'every refusal is logged');
  for(const k of ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy'])assert.equal(k in process.env,false,k+' removed');
});

test('V1I-03 the Node guard allows loopback (the fixture server path)',async()=>{
  const server=http.createServer((q,r)=>r.end('ok'));await new Promise(r=>server.listen(0,'127.0.0.1',r));
  try{const body=await fetch('http://127.0.0.1:'+server.address().port+'/').then(r=>r.text());assert.equal(body,'ok');}
  finally{server.close();}
});

test('V1I-04 the Python guard refuses urlopen off loopback and logs it; helpers install it before anything else',()=>{
  const r=spawnSync('python',['-I',HELPERS,'selftest'],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  const o=JSON.parse(r.stdout.trim());assert.equal(o.installed,true);
  assert.ok(o.probes.length>=2&&o.probes.every(p=>p.refusedByGuard===true),JSON.stringify(o.probes));
  assert.equal(o.refused.length,o.probes.length);
});

test('V1I-05 the offline font fixture is deterministic and generated locally (no network)',()=>{
  const os=require('node:os'),fs=require('node:fs'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'r0036-font-'));
  try{const run=f=>JSON.parse(spawnSync('python',['-I',HELPERS,'font',path.join(dir,f)],{encoding:'utf8'}).stdout.trim());
    const a=run('a.ttf'),b=run('b.ttf');assert.equal(a.sha256,b.sha256);assert.ok(a.bytes>100);assert.deepEqual(a.refused,[]);}
  finally{fs.rmSync(dir,{recursive:true,force:true});}
});
