'use strict';
// Source/HTTP/retention controls only. Response doubles are not native evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http');
const crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const S=require('./r003f_preconnect_input.cjs'),M=require('./r003f_preconnect_materialize.cjs');
const B=require('./r003f_materialize.cjs'),ROOT=path.resolve(__dirname,'../../..');
const raw=fs.readFileSync(path.join(ROOT,'index.html')),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const URL='http://127.0.0.1:12345/index.html';
function temporary(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-preconnect-source-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return p;}
function input(t,root=ROOT){const out=path.join(temporary(t),'evidence');fs.mkdirSync(out);return {out,input:S.createInput({root,out})};}
function response(body,changes={}){return {url:()=>URL,status:()=>200,headers:()=>({'content-type':'text/html'}),body:async()=>Buffer.from(body),...changes};}
async function complete(t){const p=input(t);for(let i=0;i<2;i++)await p.input.recordResponse(response(p.input.indexFor('B0')),URL);p.input.assertComplete();return p;}
function prepared(t){const dir=temporary(t),out=path.join(dir,'derived');return {dir,out,receipt:M.materialize({source:ROOT,runtime:ROOT,out})};}

test('exact two tag spans produce the independently fixed served-document digest',()=>{
  const d=S.deriveIndex(raw);assert.equal(sha(raw),'88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1');
  assert.equal(sha(d.body),'16a0f207412572751609316186d5b1f64ee9b31987b9ec6f47c293c9280754b7');
  assert.equal(raw.length,1692708);assert.equal(d.body.length,1692581);
  const spans=d.identity.removals;assert.deepEqual(spans.map(x=>[x.offset,x.bytes]),[[159,59],[219,68]]);
  assert.deepEqual(d.body,Buffer.concat([raw.subarray(0,159),raw.subarray(218,219),raw.subarray(287)]));
});
test('source drift, missing hints, duplicate hints and other element changes are rejected',()=>{
  for(const body of [Buffer.concat([raw,Buffer.from('\n')]),Buffer.from(raw.toString().replace('<link rel="preconnect"','<link rel="other"')),
    Buffer.concat([raw,Buffer.from('<link rel="preconnect" href="https://fonts.googleapis.com">')]),Buffer.from(raw.toString().replace('crossorigin>','crossorigin="anonymous">'))])assert.throws(()=>S.deriveIndex(body));
});
test('the original runtime remains unchanged while the callback produces only guarded B0 bytes',t=>{
  const p=input(t);assert.deepEqual(p.input.indexFor('B0'),S.deriveIndex(raw).body);assert.deepEqual(fs.readFileSync(path.join(ROOT,'index.html')),raw);
  assert.equal(p.input.evidence.producedBodies.length,1);assert.equal(p.input.evidence.responses.length,0);
});
test('unsupported variants and extra document requests cannot become a complete diagnostic',t=>{
  let p=input(t);assert.throws(()=>p.input.indexFor('B1c'));assert.throws(()=>p.input.assertComplete());
  p=input(t);p.input.indexFor('B0');p.input.indexFor('B0');assert.throws(()=>p.input.indexFor('B0'));assert.equal(p.input.evidence.producedBodies.length,2);
});
test('two complete observed response bodies are retained and independently read back',async t=>{
  const p=await complete(t);assert.equal(p.input.evidence.status,'COMPLETE');assert.equal(p.input.evidence.responses.length,2);
  for(const row of p.input.evidence.responses){assert.equal(row.body.sha256,S.DERIVED_SHA);assert.deepEqual(fs.readFileSync(path.join(p.out,row.body.path)),S.deriveIndex(raw).body);}
  assert.equal(S.admitEvidence(p.input.evidence,p.out).status,'COMPLETE');
});
test('a wrong document body is retained before the identity rejection',async t=>{
  const p=input(t);p.input.indexFor('B0');const bad=Buffer.from('<html>controlled mismatch</html>');
  await assert.rejects(p.input.recordResponse(response(bad),URL));const row=p.input.evidence.responses[0];
  assert.deepEqual(fs.readFileSync(path.join(p.out,row.body.path)),bad);assert.equal(row.body.sha256,sha(bad));assert.notEqual(row.status,'VERIFIED');assert.throws(()=>p.input.assertComplete());
});
test('HTTP status, MIME, query and path mismatches fail after retaining the actual body',async t=>{
  for(const changes of [{status:()=>404},{headers:()=>({'content-type':'application/octet-stream'})},{url:()=>URL+'?variant=B0'},{url:()=>URL.replace('/index.html','/%69ndex.html')}]){
    const p=input(t),body=p.input.indexFor('B0');await assert.rejects(p.input.recordResponse(response(body,changes),URL));
    assert.deepEqual(fs.readFileSync(path.join(p.out,p.input.evidence.responses[0].body.path)),body);
  }
});
test('navigation and body-read failures retain truthful missing-body evidence',async t=>{
  const a=input(t);a.input.recordNavigationFailure(Error('controlled navigation failure'),URL);assert.equal(a.input.evidence.responses[0].body,undefined);assert.throws(()=>a.input.assertComplete());
  const b=input(t);b.input.indexFor('B0');await assert.rejects(b.input.recordResponse(response(Buffer.alloc(0),{body:async()=>{throw Error('controlled body failure');}}),URL));
  assert.equal(b.input.evidence.responses[0].body,undefined);assert.equal(b.input.evidence.responses[0].bodyReadError,'controlled body failure');
});
test('missing response and document overflow cannot invent complete records',async t=>{
  const p=input(t);p.input.indexFor('B0');await assert.rejects(p.input.recordResponse(null,URL));assert.throws(()=>p.input.assertComplete());
  const q=await complete(t);await assert.rejects(q.input.recordResponse(response(S.deriveIndex(raw).body),URL));assert.equal(q.input.evidence.responses.length,2);assert.throws(()=>S.admitEvidence(q.input.evidence,q.out));
});
test('oversized actual bodies are rejected with explicit retention-limit evidence',async t=>{
  const p=input(t);p.input.indexFor('B0');await assert.rejects(p.input.recordResponse(response(Buffer.alloc(S.ORIGINAL_BYTES+1)),URL));
  const row=p.input.evidence.responses[0];assert.equal(row.observedBodyBytes,S.ORIGINAL_BYTES+1);assert.equal(row.body,undefined);assert.match(row.retentionError,/limit/);
});
test('retained document alteration, removal and symlink replacement are rejected',async t=>{
  for(const kind of ['alter','remove','symlink']){
    const p=await complete(t),f=path.join(p.out,p.input.evidence.responses[0].body.path);
    if(kind==='alter')fs.appendFileSync(f,'\n');else {fs.unlinkSync(f);if(kind==='symlink')fs.symlinkSync(path.join(ROOT,'index.html'),f);}
    assert.throws(()=>S.admitEvidence(p.input.evidence,p.out));
  }
});
test('document retention faults remain failures with observed hashes and no invented file',async t=>{
  const p=input(t);fs.writeFileSync(path.join(p.out,'document-input'),'controlled obstruction');const body=p.input.indexFor('B0');
  await assert.rejects(p.input.recordResponse(response(body),URL));const row=p.input.evidence.responses[0];
  assert.equal(row.observedBodySha256,S.DERIVED_SHA);assert.equal(row.body,undefined);assert.ok(row.retentionError);assert.throws(()=>p.input.assertComplete());
});
test('a changed runtime index at the completion boundary cannot be admitted',async t=>{
  const dir=temporary(t);fs.writeFileSync(path.join(dir,'index.html'),raw);const p=input(t,dir);
  for(let i=0;i<2;i++)await p.input.recordResponse(response(p.input.indexFor('B0')),URL);
  fs.appendFileSync(path.join(dir,'index.html'),'\n');assert.throws(()=>p.input.assertComplete());assert.notEqual(p.input.evidence.status,'COMPLETE');
});
test('a late extra callback invalidates an earlier complete document record',async t=>{
  const p=await complete(t);assert.throws(()=>p.input.indexFor('B0'));assert.notEqual(p.input.evidence.status,'COMPLETE');assert.throws(()=>S.admitEvidence(p.input.evidence,p.out));
});
test('source materialization has a new complete identity and changes no runtime assets',t=>{
  const p=prepared(t);assert.equal(p.receipt.protocol,S.SOURCE_PROTOCOL);assert.equal(p.receipt.status,'PREPARED');assert.equal(p.receipt.nativeExecution,'NOT_RUN');
  assert.equal(p.receipt.outputFiles.length,8);assert.deepEqual(p.receipt.productFilesCopied,[]);assert.equal(p.receipt.assetBytesChanged,false);
  assert.equal(p.receipt.baseMaterializationSha256,'fab2e2ad49a14eee2ba715fb75365fa4b0abfa48a1d8b60247343ad29b1021e5');assert.deepEqual(fs.readFileSync(path.join(ROOT,'index.html')),raw);
});
test('closure requires an external exact digest and the complete output population',t=>{
  const p=prepared(t),f=path.join(p.out,'materialization.json'),hash=sha(fs.readFileSync(f));
  assert.throws(()=>S.admitClosure(p.out));assert.throws(()=>S.admitClosure(p.out,'0'.repeat(64)));
  assert.equal(S.admitClosure(p.out,hash).status,'PREPARED');assert.notEqual(hash,p.receipt.baseMaterializationSha256);
  fs.writeFileSync(path.join(p.out,'undeclared.txt'),'drift');assert.throws(()=>S.admitClosure(p.out,hash));
});
test('copied driver/helper drift, missing members and symlinks fail closure',t=>{
  for(const kind of ['alter','remove','symlink']){
    const p=prepared(t),hash=sha(fs.readFileSync(path.join(p.out,'materialization.json'))),f=path.join(p.out,'tools/qa/r0033_isolation.cjs');
    if(kind==='alter')fs.appendFileSync(f,'\n');else {fs.unlinkSync(f);if(kind==='symlink')fs.symlinkSync(path.join(ROOT,'tools/qa/r0033_isolation.cjs'),f);}
    assert.throws(()=>S.admitClosure(p.out,hash));
  }
});
test('the corrected capture function, helpers and strict cleanup/isolation tail stay byte-identical',t=>{
  const p=prepared(t),base=path.join(p.dir,'base');B.materialize({source:ROOT,out:base});
  const a=fs.readFileSync(path.join(base,'tools/qa/r003f_owner_baseline.cjs'),'utf8'),b=fs.readFileSync(path.join(p.out,'tools/qa/r003f_owner_baseline.cjs'),'utf8');
  const block=s=>s.slice(s.indexOf('async function capture('),s.indexOf('async function main()'));
  assert.equal(block(a),block(b));assert.equal(a.slice(a.indexOf('  } catch(error) {')),b.slice(b.indexOf('  } catch(error) {')));
  for(const name of B.COPIED.filter(x=>!x.endsWith('r003f_owner_baseline.cjs')).concat('tools/qa/hosted-native/r003f_ui.cjs'))assert.deepEqual(fs.readFileSync(path.join(base,name)),fs.readFileSync(path.join(p.out,name)));
  assert.ok(b.includes(S.SUCCESS));assert.ok(b.includes("protocol:'R003F/P1/B0-preconnect-input/1'"));assert.ok(!b.includes("harness:{protocol:'R003F/corrected-harness/1'"));
});
test('a changed original recipe or wrong runtime input cannot leave a partial output',t=>{
  const dir=temporary(t),source=path.join(dir,'source');fs.mkdirSync(source);
  for(const rel of Object.keys(B.INPUTS)){const p=path.join(source,rel);fs.mkdirSync(path.dirname(p),{recursive:true});fs.copyFileSync(path.join(ROOT,rel),p);}
  fs.appendFileSync(path.join(source,'tools/qa/r0033_isolation.cjs'),'\n');const out=path.join(dir,'bad');assert.throws(()=>M.materialize({source,runtime:ROOT,out}));assert.equal(fs.existsSync(out),false);
  fs.writeFileSync(path.join(dir,'index.html'),'wrong');assert.throws(()=>M.materialize({source:ROOT,runtime:dir,out}));assert.equal(fs.existsSync(out),false);
});
test('existing outputs and source-contained destinations are rejected without mutation',t=>{
  const dir=temporary(t);assert.throws(()=>M.materialize({source:ROOT,runtime:ROOT,out:dir}));assert.throws(()=>M.materialize({source:ROOT,runtime:ROOT,out:path.join(ROOT,'controlled-forbidden-output')}));
  assert.deepEqual(fs.readdirSync(dir),[]);
});
test('unsupported engine or DPR is rejected before any browser package import',t=>{
  const p=prepared(t),driver=path.join(p.out,'tools/qa/r003f_owner_baseline.cjs');
  for(const [engine,dpr] of [['chromium','1'],['firefox','1'],['webkit','2']]){
    const r=spawnSync(process.execPath,[driver,'--root',ROOT,'--out',path.join(p.dir,'never-created'),'--engine',engine,'--dpr',dpr,'--playwright','/synthetic/never-imported','--pngjs','/synthetic/never-imported'],{encoding:'utf8',timeout:10000});
    assert.notEqual(r.status,0);assert.match(r.stderr,/WebKit DPR1/);assert.ok(!r.stderr.includes('Cannot find module'));assert.equal(fs.existsSync(path.join(p.dir,'never-created')),false);
  }
});
test('the existing HTTP callback serves exact derived HTML while CSS and disk bytes remain unchanged',async t=>{
  const p=prepared(t),e=input(t),capture=require(path.join(p.out,'tools/qa/r003f_capture.cjs')),server=e.input.guardServer(capture.makeServer(ROOT,e.input.indexFor));
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  try{
    const origin='http://127.0.0.1:'+server.address().port;
    const get=pathname=>new Promise((resolve,reject)=>http.get(origin+pathname,r=>{const chunks=[];r.on('data',x=>chunks.push(x));r.on('end',()=>resolve({status:r.statusCode,headers:r.headers,body:Buffer.concat(chunks)}));r.on('error',reject);}).on('error',reject));
    for(let i=0;i<2;i++){const r=await get('/index.html');assert.equal(r.headers['content-type'],'text/html');await e.input.recordResponse(response(r.body,{url:()=>origin+'/index.html',status:()=>r.status,headers:()=>r.headers}),origin+'/index.html');}
    const css=await get('/real-sky/native-sky.css');assert.equal(css.headers['content-type'],'text/css');assert.deepEqual(css.body,fs.readFileSync(path.join(ROOT,'real-sky/native-sky.css')));
    e.input.assertComplete();assert.deepEqual(fs.readFileSync(path.join(ROOT,'index.html')),raw);
  }finally{await new Promise(resolve=>server.close(resolve));}
});
test('encoded index aliases and every query form are refused before serving any document bytes',async t=>{
  for(const target of ['/%69ndex.html','/index.html?variant=B0','/index.html?variant=B1c','/index.html?unclassified=1','/%2Findex.html']){
    const p=prepared(t),e=input(t),capture=require(path.join(p.out,'tools/qa/r003f_capture.cjs')),server=e.input.guardServer(capture.makeServer(ROOT,e.input.indexFor));
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    try{
      const r=await new Promise((resolve,reject)=>http.get({hostname:'127.0.0.1',port:server.address().port,path:target},r=>{const parts=[];r.on('data',x=>parts.push(x));r.on('end',()=>resolve({status:r.statusCode,body:Buffer.concat(parts)}));r.on('error',reject);}).on('error',reject));
      assert.equal(r.status,404);assert.equal(r.body.length,0);assert.equal(e.input.evidence.producedBodies.length,0);
      assert.equal(e.input.evidence.status,'INCOMPLETE');assert.equal(e.input.evidence.rejectedDocumentRequests,1);assert.throws(()=>e.input.assertComplete());
    }finally{await new Promise(resolve=>server.close(resolve));}
  }
});
test('symlinked output parents cannot place retained evidence inside the runtime',t=>{
  const dir=temporary(t),runtime=path.join(dir,'runtime'),alias=path.join(dir,'alias');fs.mkdirSync(runtime);fs.writeFileSync(path.join(runtime,'index.html'),raw);fs.symlinkSync(runtime,alias,'dir');
  assert.throws(()=>S.createInput({root:runtime,out:path.join(alias,'evidence')}),/symlink|outside/);
  assert.equal(fs.existsSync(path.join(runtime,'evidence')),false);assert.deepEqual(fs.readFileSync(path.join(runtime,'index.html')),raw);
});
test('evidence path ancestors and direct evidence symlinks are refused even outside the runtime',t=>{
  const dir=temporary(t),target=path.join(dir,'target'),alias=path.join(dir,'alias');fs.mkdirSync(target);fs.symlinkSync(target,alias,'dir');
  assert.throws(()=>S.createInput({root:ROOT,out:path.join(alias,'evidence')}),/symlink/);
  assert.throws(()=>S.createInput({root:ROOT,out:alias}),/symlink/);assert.deepEqual(fs.readdirSync(target),[]);
});
test('parent substitution after input creation refuses a body write while preserving its observed hash',async t=>{
  const dir=temporary(t),runtime=path.join(dir,'runtime'),holder=path.join(dir,'holder'),saved=path.join(dir,'saved'),out=path.join(holder,'evidence');
  fs.mkdirSync(runtime);fs.writeFileSync(path.join(runtime,'index.html'),raw);fs.mkdirSync(holder);fs.mkdirSync(out);
  const input=S.createInput({root:runtime,out});fs.renameSync(holder,saved);fs.symlinkSync(runtime,holder,'dir');fs.mkdirSync(path.join(runtime,'evidence'));
  const body=input.indexFor('B0');await assert.rejects(input.recordResponse(response(body),URL),/symlink/);
  const row=input.evidence.responses[0];assert.equal(row.observedBodySha256,S.DERIVED_SHA);assert.equal(row.body,undefined);assert.match(row.retentionError,/symlink/);
  assert.equal(fs.existsSync(path.join(runtime,'evidence/document-input')),false);
});
test('late same-byte evidence-parent aliases cannot re-admit completed document evidence',async t=>{
  const dir=temporary(t),holder=path.join(dir,'holder'),saved=path.join(dir,'saved'),out=path.join(holder,'evidence');fs.mkdirSync(holder);fs.mkdirSync(out);
  const input=S.createInput({root:ROOT,out});for(let i=0;i<2;i++)await input.recordResponse(response(input.indexFor('B0')),URL);input.assertComplete();
  fs.renameSync(holder,saved);fs.symlinkSync(saved,holder,'dir');assert.throws(()=>S.admitEvidence(input.evidence,out),/symlink/);
});
test('fresh canonical evidence output is still admitted before original driver directory creation',async t=>{
  const out=path.join(temporary(t),'fresh-evidence'),input=S.createInput({root:ROOT,out});assert.equal(fs.existsSync(out),false);fs.mkdirSync(out);
  for(let i=0;i<2;i++)await input.recordResponse(response(input.indexFor('B0')),URL);
  assert.equal(input.assertComplete().status,'COMPLETE');assert.equal(S.admitEvidence(input.evidence,out).status,'COMPLETE');
});
