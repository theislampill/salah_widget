'use strict';
// R003A (issue 124) CI-06: the never-read north–south wind field was removed from cloudState, the atmosphere descriptor
// and applyCloudState. R3A-02.1 census over tracked consumer-class files; R3A-02.3 drift trajectories byte-identical
// to main 516d8cc8. Patterns are assembled at run time so this file never matches itself (it is also excluded).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),
 crypto=require('node:crypto'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),self=path.relative(root,__filename).split(path.sep).join('/');
const F='w'+'y',U='wind'+'UY';
const FIELD=new RegExp('\\.'+F+'\\b|\\b'+F+':|'+U,'g');
const COPY=new RegExp('\\{\\.\\.\\.cloud'+'State\\}|run\\(\'cloud'+'State\'\\)|copy\\(cloud'+'State\\)|stringify\\(cloud'+'State','g');
const CONSUMER=/^(src\/native\/[^/]+\.(html|js)|index\.html|offline\.html|real-sky\/[^/]+\.(mjs|js)|moon\/src\/.+|tools\/.+|tests\/.+)$/;
const EXCLUDED=p=>p===self||p.startsWith('v1/')||p.startsWith('vendor/')||p.startsWith('real-sky/core/src/');
// Expected consumer-class findings after removal: the pinned R000B fixture records a now-absent field (no oracle reads
// it; its bytes are unchanged), and three value-agnostic whole-object copies.
const EXPECTED_FIELD=['tests/rlgwo/r000b-no-timetable-fixture.html'];
const EXPECTED_COPY=['tests/r0025-context.cjs','tests/real-sky/native-weather-withdrawal.test.mjs','tests/weather-native/native-controls.js'];
function census(files){
 const field=new Set(),copy=new Set();
 for(const [p,text] of files){if(!CONSUMER.test(p)||EXCLUDED(p))continue;
  if((text.match(FIELD)||[]).length)field.add(p);if((text.match(COPY)||[]).length)copy.add(p);}
 return {field:[...field].sort(),copy:[...copy].sort()};}
function tracked(){return execFileSync('git',['ls-files','-z','--','src/native','index.html','offline.html','real-sky','moon/src','tools','tests'],{cwd:root,encoding:'utf8',maxBuffer:1<<28}).split('\0').filter(Boolean)
 .filter(p=>CONSUMER.test(p)&&!EXCLUDED(p)&&fs.existsSync(path.join(root,p))).map(p=>[p,fs.readFileSync(path.join(root,p),'latin1')]);}

test('R3A-02.1 census: no consumer-class reader or producer of the removed field; copy sites enumerated',()=>{
 const files=tracked();assert(files.some(([p])=>p==='src/native/index.html'),'population includes the authored source');
 const found=census(files);assert.deepEqual(found.field,EXPECTED_FIELD);assert.deepEqual(found.copy,EXPECTED_COPY);
});
test('R3A-02.1 negative controls: a planted reader and an unlisted copy site each fail the census',()=>{
 const files=tracked(),i=files.findIndex(([p])=>p==='src/native/index.html');
 const planted=files.map((f,j)=>j===i?[f[0],f[1].replace('function paintClouds(','const __r003a=cloud'+'State.'+F+';function paintClouds(')]:f);
 assert.notDeepEqual(census(planted).field,EXPECTED_FIELD);
 const copied=[...files,['tests/r003a-planted.cjs','const x={...cloud'+'State};']];
 assert.notDeepEqual(census(copied).copy,EXPECTED_COPY);
});
test('R3A-02.1 the authored runtime no longer carries the field in cloudState or the atmosphere descriptor',async()=>{
 const {fixture}=require('./weather-no-timetable-fixture.cjs');const h=await fixture();
 assert.equal(h.run('Object.prototype.hasOwnProperty.call(cloudState,"'+F+'")'),false);
 h.run('window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:20,azDeg:120},utcMs:simNow(),sample:()=>null})}');
 assert.equal(h.run('"'+U+'" in atmosphere(model())'),false);
 assert.equal(typeof h.run('cloudState.wx'),'number');assert.equal(typeof h.run('cloudState.wspd'),'number');
});
test('R3A-02.3 drift trajectories are byte-identical to main 516d8cc8 (100 cases x 60 steps)',()=>{
 const out=execFileSync(process.execPath,[path.join(root,'tools/qa/r003a_drift_matrix.cjs')],{cwd:root,encoding:'utf8',maxBuffer:1<<26});
 assert.equal(JSON.parse(out).cases,100);
 assert.equal(crypto.createHash('sha256').update(out).digest('hex'),'a6602501cca37a05ddef40a9b0477c9d307521bd0b62df7906dee044e2cf8e6d');
});
