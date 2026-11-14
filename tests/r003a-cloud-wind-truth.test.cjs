'use strict';
// R003A (issue 124) CI-06, owner gate G1 = retain: cloudState.wy (cos of the wind "from" direction, a horizontal
// north–south component, not vertical wind) is written by applyCloudState and read by nothing. R3A-02.1 census over
// tracked consumer-class files (retention form); inertness negative control; R3A-02.3 drift trajectories byte-identical
// to main 516d8cc8. Patterns are assembled at run time so this file never matches itself (it is also excluded).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),
 crypto=require('node:crypto'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),self=path.relative(root,__filename).split(path.sep).join('/');
const F='w'+'y',U='wind'+'UY';
const FIELD=new RegExp('\\.'+F+'\\b|\\b'+F+':|'+U,'g');
const COPY=new RegExp('\\{\\.\\.\\.cloud'+'State\\}|run\\(\'cloud'+'State\'\\)|copy\\(cloud'+'State\\)|stringify\\(cloud'+'State','g');
const CONSUMER=/^(src\/native\/[^/]+\.(html|js)|index\.html|offline\.html|real-sky\/[^/]+\.(mjs|js)|moon\/src\/.+|tools\/.+|tests\/.+)$/;
const EXCLUDED=p=>p===self||p.startsWith('v1/')||p.startsWith('vendor/')||p.startsWith('real-sky/core/src/');
// Expected consumer-class findings (retention): the authored producer and its two generated copies; the r0025 mutation
// anchor (assignment text); the pinned R000B fixture, which records the value but no oracle reads it; three
// value-agnostic whole-object copies.
const EXPECTED_FIELD=['index.html','offline.html','src/native/index.html','tests/r0025-mutations.cjs','tests/rlgwo/r000b-no-timetable-fixture.html'];
const PRODUCER_SNIPPETS=[F+':0.2',U+': Math.cos(','CS.'+F+'=A.'+U];
const EXPECTED_COPY=['tests/r0025-context.cjs','tests/real-sky/native-weather-withdrawal.test.mjs','tests/weather-native/native-controls.js'];
function census(files){
 const field=new Set(),copy=new Set();let sourceHits=null;
 for(const [p,text] of files){if(!CONSUMER.test(p)||EXCLUDED(p))continue;const n=(text.match(FIELD)||[]).length;
  if(p==='src/native/index.html')sourceHits=n;if(n)field.add(p);if((text.match(COPY)||[]).length)copy.add(p);}
 return {field:[...field].sort(),copy:[...copy].sort(),sourceHits};}
function tracked(){return execFileSync('git',['ls-files','-z','--','src/native','index.html','offline.html','real-sky','moon/src','tools','tests'],{cwd:root,encoding:'utf8',maxBuffer:1<<28}).split('\0').filter(Boolean)
 .filter(p=>CONSUMER.test(p)&&!EXCLUDED(p)&&fs.existsSync(path.join(root,p))).map(p=>[p,fs.readFileSync(path.join(root,p),'latin1')]);}

test('R3A-02.1 census: no consumer-class reader or producer of the removed field; copy sites enumerated',()=>{
 const files=tracked();assert(files.some(([p])=>p==='src/native/index.html'),'population includes the authored source');
 const found=census(files);assert.deepEqual(found.field,EXPECTED_FIELD);assert.deepEqual(found.copy,EXPECTED_COPY);
 assert.equal(found.sourceHits,4,'authored source: initialiser, producer, write and its descriptor read only');
});
test('R3A-02.1 negative controls: a planted reader and an unlisted copy site each fail the census',()=>{
 const files=tracked(),i=files.findIndex(([p])=>p==='src/native/index.html');
 const planted=files.map((f,j)=>j===i?[f[0],f[1].replace('function paintClouds(','const __r003a=cloud'+'State.'+F+';function paintClouds(')]:f);
 assert.notEqual(census(planted).sourceHits,4,'a planted reader in the authored source is detected');
 const copied=[...files,['tests/r003a-planted.cjs','const x={...cloud'+'State};']];
 assert.notDeepEqual(census(copied).copy,EXPECTED_COPY);
});
test('R3A-02.1 authored source: one initialiser, one producer, one write, no reader',()=>{
 const src=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
 const hits=[...src.matchAll(FIELD)].map(m=>src.slice(m.index-(m[0].startsWith('.')?2:0),m.index+m[0].length+(m[0]===U?10:4)));
 assert.equal(hits.length,4,'wy: initialiser, windUY producer, CS.wy write and its A.windUY source');
 for(const s of PRODUCER_SNIPPETS)assert.equal(src.split(s).length,2,'exactly one '+s);
});
test('R3A-02.1 negative control: changing the retained field moves no cloud; changing wx does',async()=>{
 const {fixture}=require('./weather-no-timetable-fixture.cjs');
 const advance=async(wx,v)=>{const h=await fixture();h.at(890500);h.run('advanceCloudMotion(simNow()/1000)');
  h.run('cloudState.wx='+wx+';cloudState.'+F+'='+v+';cloudState.wspd=0.3');h.at(891500);h.run('advanceCloudMotion(simNow()/1000)');
  return h.run('JSON.stringify(_cloudMotion.phase)');};
 const base=await advance(0.7,-1);assert.equal(await advance(0.7,1),base);assert.notEqual(await advance(-0.7,-1),base);
});
test('R3A-02.3 drift trajectories are byte-identical to main 516d8cc8 (100 cases x 60 steps)',()=>{
 const out=execFileSync(process.execPath,[path.join(root,'tools/qa/r003a_drift_matrix.cjs')],{cwd:root,encoding:'utf8',maxBuffer:1<<26});
 assert.equal(JSON.parse(out).cases,100);
 assert.equal(crypto.createHash('sha256').update(out).digest('hex'),'a6602501cca37a05ddef40a9b0477c9d307521bd0b62df7906dee044e2cf8e6d');
});
