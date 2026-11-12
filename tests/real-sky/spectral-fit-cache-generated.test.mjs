// R0027 generated-deliverable contract. Reads the committed generated bundles (never edits
// them): the bound is present in every bundle copy of the spectral module, the real worker
// bundle is bounded when executed, and old (vendor-spectral) vs new generated worker bundles
// produce byte-identical first-paint preview and refined worker outputs for real scenes,
// cold, hit and after eviction/recompute. Also executes the Python generator contract so
// the integration qualification route (`tools/cp9/qualify_candidate.py --groups integration`)
// runs it.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {CAPACITY,ROOT,read,sha256,concatStrip,vendorBundle,bundleRealm,vendorSpectral,SPECTRAL_REL,sameOutput,orlando,SCENES,bvAt} from './spectral-fit-cache-fixture.mjs';

const text=rel=>read(rel).toString('utf8');
const segment=()=>concatStrip(text(SPECTRAL_REL));
const count=(hay,needle)=>hay.split(needle).length-1;
function previewScript(html){const m=html.match(/<script id="native-first-paint-code" data-sha256="([0-9a-f]{64})">([\s\S]*?)<\/script>/);assert.ok(m,'first-paint script');return {pin:m[1],code:m[2]};}
function embeddedWorker(sky){const at=sky.indexOf('startNativeSky(pack,"');assert.ok(at>0);const s=sky.slice(at+'startNativeSky(pack,'.length);let i=1;for(;i<s.length;i++){if(s[i]==='\\'){i++;continue;}if(s[i]==='"')break;}return JSON.parse(s.slice(0,i+1));}

test('ES27-11 every generated bundle carries exactly the generated spectral module text and compiles',()=>{
 const seg=segment(),worker=text('real-sky/native-worker.js'),sky=text('real-sky/native-sky.js'),{pin,code}=previewScript(text('index.html'));
 assert.ok(seg!==concatStrip(vendorSpectral.toString('utf8')),'generated core differs from vendor (transform applied)');
 assert.equal(count(worker,seg),1,'worker');
 assert.equal(count(sky,seg),1,'native-sky.js UI realm');
 assert.equal(embeddedWorker(sky),worker,'native-sky.js embeds the exact worker bundle');
 assert.equal(count(code,seg),1,'index.html first-paint realm');
 assert.equal(sha256(Buffer.from(code)),pin,'first-paint data-sha256 matches its text');
 for(const [name,src] of [['worker',worker],['native-sky',sky],['first-paint',code]])assert.doesNotThrow(()=>new vm.Script(src,{filename:name}),name+' compiles (no identifier collision)');
 const offline=text('offline.html');
 assert.equal(count(offline,seg),2,'offline.html inlines the UI and first-paint realms');
 assert.ok(offline.includes(sky.split('</'+'script').join('<'+String.fromCharCode(92)+'/script')),'offline.html inlines the exact native-sky.js (with its embedded worker)');
});

test('ES27-01/06 the real generated worker bundle is bounded when executed',async t=>{
 const realm=bundleRealm(text('real-sky/native-worker.js'));
 try{
  const a=bvAt(0,0),d=bvAt(0,1)-bvAt(0,0);
  await realm.eval(`for(let i=0;i<${CAPACITY+2};i++)selectSpectrum({bv:${a}+i*${d}});`);
  const r=await realm.eval(`({n:__r0027.inner.length,size:__r0027.inner[0].size,same:__r0027.inner[0]===sfFitCache,outer:__r0027.outer[0].size,first:__r0027.inner[0].keys().next().value})`);
  t.diagnostic(JSON.stringify(r));
  assert.equal(r.n,1);assert.ok(r.same);
  assert.equal(r.size,CAPACITY,'worker realm retains at most 12,000 fits');
  assert.equal(r.outer,CAPACITY,'worker outer bound unchanged');
  assert.ok(Object.is(r.first,a+2*d),'the two oldest keys were evicted (FIFO)');
 }finally{await realm.close();}
});

const pack=(()=>{const box={window:{}};vm.runInNewContext(text('real-sky/native-data.js'),box);return JSON.parse(JSON.stringify(box.window.__SALAH_REAL_SKY_PACK__));})();
async function boot(source){
 const realm=bundleRealm(source);
 try{const ready=await realm.message({kind:'boot',pack});assert.equal(ready?.kind,'ready',JSON.stringify(ready));}catch(error){await realm.close();throw error;}
 const d=(bvAt(5,1)-bvAt(5,0))/16;
 return {realm,
  preview:snap=>realm.eval(`renderNativeBackgroundPreview(${JSON.stringify(snap)})`),
  async refined(snap,id){const m=await realm.job(`nativeJob(${JSON.stringify(snap)},true)`,id);assert.equal(m?.kind,'result',JSON.stringify(m?.error));return m.result;},
  flood:(offset,keyed)=>realm.eval(`for(let i=0;i<${CAPACITY};i++)selectSpectrum({bv:${bvAt(5,0)}+(i+${offset})*${d}${keyed?",spectralType:'r0027-flood'":''}});`)};
}

test('ES27-14 old vs new generated worker bundle: first-paint preview and refined worker outputs are byte-identical (cold / hit / recomputed)',async t=>{
 const newer=text('real-sky/native-worker.js'),older=vendorBundle(newer);
 assert.ok(older.includes(concatStrip(vendorSpectral.toString('utf8'))));
 // try/finally: a failing assertion must still close both worker realms, or node --test hangs on live threads.
 const oldB=await boot(older);let newB=null;
 try{
 newB=await boot(newer);
 await newB.flood(0,false);// saturate the new realm's outer cache so caller keys must use the inner cache
 let bytes=0,scenes=0;
 for(const [i,utc] of SCENES.entries()){
  const snap=orlando(utc),id=i+1;
  const expected={preview:await oldB.preview(snap),refined:await oldB.refined(snap,id)};
  const cold={preview:await newB.preview(snap),refined:await newB.refined(snap,id)};
  const hit={preview:await newB.preview(snap),refined:await newB.refined(snap,id)};
  const sceneKeys=await newB.realm.eval('[...__r0027.inner[0].keys()].slice(-8)');
  await newB.flood((i+1)*CAPACITY,true);
  assert.deepEqual(await newB.realm.eval(`${JSON.stringify(sceneKeys)}.filter(k=>__r0027.inner[0].has(k))`),[],utc+': the scene fits were evicted before the recomputed run');
  const again={preview:await newB.preview(snap),refined:await newB.refined(snap,id)};
  for(const [name,v] of [['cold',cold],['hit',hit],['recomputed',again]])bytes+=sameOutput(assert,v,expected,utc+' '+name).n;
  scenes++;
 }
 const retained=await newB.realm.eval('__r0027.inner[0].size'),oldRetained=await oldB.realm.eval('__r0027.inner[0].size');
 t.diagnostic(`scenes=${scenes} bytesCompared=${bytes} newInnerRetained=${retained} oldInnerRetained=${oldRetained} oldBundleSha256=${sha256(Buffer.from(older))} newBundleSha256=${sha256(Buffer.from(newer))}`);
 assert.ok(retained<=CAPACITY,'new realm bounded');
 }finally{await oldB.realm.close();if(newB)await newB.realm.close();}
});

test('ES27-09/10/11/12 Python generator contract and its mutation controls pass (executed from the integration route)',()=>{
 const py=process.env.PYTHON||'python',file=fileURLToPath(new URL('tests/real-sky/native_spectral_cache_build_test.py',ROOT));
 const r=spawnSync(py,[file,'-v'],{cwd:fileURLToPath(ROOT),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},timeout:600000});
 const out=(r.stdout||'')+(r.stderr||'');
 assert.equal(r.status,0,out.slice(-4000));
 assert.match(out,/Ran \d+ tests?/);assert.match(out,/\nOK\s*$/);
});
