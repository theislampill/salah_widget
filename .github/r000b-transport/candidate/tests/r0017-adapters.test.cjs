'use strict';
// Adapter controls use checked-out product bytes and contained VM boundaries.
// They establish source discovery/scheduling, never native pixels or providers.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {nativeInlineRuntime}=require('./native-inline-runtime.cjs');
const {widget,drain}=require('./r0011-fixture.cjs');
const {load}=require('./r001d-harness.cjs');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'index.html'),'utf8');
const scripts=[...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
const native=scripts.filter(s=>!s[1].trim()&&s[2].includes('async function boot(){'));
assert.equal(native.length,1,'control source has one native runtime');
function replaceOnce(text,before,after){
  assert.equal(text.split(before).length-1,1,'one exact mutation anchor');
  assert.notEqual(before,after,'mutation must change bytes');
  return text.replace(before,after);
}
function incomplete(body){
  assert.throws(body,error=>error.code==='SETUP_INCOMPLETE'&&error.message.startsWith('SETUP_INCOMPLETE: '));
}

test('current delivered script layout reaches actual config and model declarations',()=>{
  const runtime=nativeInlineRuntime(source);
  assert.equal(runtime,native[0][2],'the unlabelled product owner is retained byte for byte');
  const h=load({source});
  assert.equal(h.run('CONFIG.lat'),24.47);
  assert.equal(h.run('CONFIG.lon'),39.61);
  assert.equal(h.run('today.date.gregorian.date'),'08-09-2026');
});

test('the exact current authored source retains its separate input identity',()=>{
  const authored=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
  const owners=[...authored.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .filter(entry=>!entry[1].trim()&&entry[2].includes('async function boot(){'));
  assert.equal(owners.length,1);
  assert.equal(nativeInlineRuntime(authored),owners[0][2],'the actual authored native owner is retained byte for byte');
  incomplete(()=>nativeInlineRuntime(authored+'\n<!-- unreviewed authored input -->'));
});

test('stripping the delivered page to config and native cannot impersonate authored source',()=>{
  let changed=source;
  for(const entry of scripts)if(entry!==native[0]&&entry[1].trim()!=='src="config.js"')
    changed=replaceOnce(changed,entry[0],'');
  assert.deepEqual([...changed.matchAll(/<script\b([^>]*)>/gi)].map(entry=>entry[1].trim()),['src="config.js"','']);
  incomplete(()=>nativeInlineRuntime(changed));
});

test('missing, duplicate and wrong native owner are setup failures',()=>{
  incomplete(()=>nativeInlineRuntime(replaceOnce(source,native[0][0],'')));
  incomplete(()=>nativeInlineRuntime(replaceOnce(source,native[0][0],native[0][0]+native[0][0])));
  const wrong='<script>function boot(){}\nboot();</script>';
  incomplete(()=>nativeInlineRuntime(replaceOnce(source,native[0][0],wrong)));
});

test('current Moon prerequisites reject missing, duplicated, moved and altered source',()=>{
  const initial=scripts.find(s=>s[1].trim()==='id="moon-initial-code"');
  const refinement=scripts.find(s=>s[1].trim()==='id="moon-refinement-code"');
  assert.ok(initial&&refinement,'control source uses the split Moon delivery');
  for(const entry of [initial,refinement]){
    incomplete(()=>nativeInlineRuntime(replaceOnce(source,entry[0],'')));
    incomplete(()=>nativeInlineRuntime(replaceOnce(source,entry[0],entry[0]+entry[0])));
    incomplete(()=>nativeInlineRuntime(replaceOnce(source,entry[0],entry[0].replace(entry[2],entry[2]+'\n// changed prerequisite\n'))));
  }
  const moved=replaceOnce(replaceOnce(source,initial[0],''),refinement[0],refinement[0]+initial[0]);
  incomplete(()=>nativeInlineRuntime(moved));
});

test('an unknown script cannot hide behind valid named prerequisites',()=>{
  incomplete(()=>nativeInlineRuntime(replaceOnce(source,'</body>','<script>window.unreviewed=true;</script></body>')));
});

test('simultaneously missing current prerequisites cannot downgrade the document profile',()=>{
  for(const ids of [['moon-initial-code','moon-refinement-code'],['native-first-paint-code','moon-initial-code','moon-refinement-code']]){
    let changed=source;
    for(const id of ids){const entry=scripts.find(s=>s[1].includes('id="'+id+'"'));assert.ok(entry);changed=replaceOnce(changed,entry[0],'');}
    incomplete(()=>nativeInlineRuntime(changed));
  }
});

test('boot subset binds the first-document declaration and retirement from actual source',async()=>{
  const h=widget({hash:'#local=1',open:false});
  assert.equal(h.run('_skyInitialDocument'),true);
  const operation=h.boot();
  assert.equal(h.run('_skyInitialDocument'),false,'unknown location retires the warrant before acquisition');
  assert.equal(h.calls.coarse.length,1);
  await h.resolveCall('coarse',0,{ok:false});
  await operation;
  assert.equal(h.calls.loop,1);
  assert.equal(h.calls.prayer.length,0);
  const changed=replaceOnce(source,'let _skyInitialDocument=true;','let _skyInitialDocument=false;');
  assert.equal(widget({source:changed,open:false}).run('_skyInitialDocument'),false,'the adapter must not hardcode its own initializer');
});

test('missing or ambiguous first-document declaration is explicitly incomplete setup',()=>{
  incomplete(()=>widget({source:replaceOnce(source,'let _skyInitialDocument=true;',''),open:false}));
  incomplete(()=>widget({source:replaceOnce(source,'let _skyInitialDocument=true;','let _skyInitialDocument=true;\nlet _skyInitialDocument=true;'),open:false}));
});

test('whole-runtime boot settles after its owned frames and message task',async()=>{
  const h=load({source});h.run('today=null;tomorrow=null;');
  await h.complete(h.run('boot()'));
  assert.ok(h.requests.some(r=>r.dateStr==='08-09-2026'),'actual boot reaches the prayer owner');
  assert.equal(h.run('_loopStarted'),true);
  assert.equal(h.run('_skyInitialDocument'),false);
});

test('subset boot preserves the paint opportunity before actual prayer launch',async()=>{
  const h=widget({hash:'#lat=24.47&lon=39.61&tz=Asia/Riyadh',open:false});
  const operation=h.boot();
  operation.catch(()=>{}); // Preserve the original rejection for the awaited assertion below.
  assert.equal(h.calls.prayer.length,0,'the adapter must not invent a call before the actual await');
  await drain();
  assert.equal(h.calls.prayer.length,1);
  h.calls.prayer[0].resolve();await operation;
  assert.equal(h.calls.loop,1);
});
