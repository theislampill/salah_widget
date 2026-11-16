// R0038 / ISM-SKY-021: bounded retention of the display-geometry memo
// (`displayGeometryCache` in real-sky/native-preview.mjs). The sibling lunar memo
// is covered by native-lunar-cache.test.mjs; this file covers the camera-ray memo,
// which previously had no test that referenced it. The owner is evaluated from its
// real source (imports rewritten to absolute URLs, an inspection export appended)
// so the assertions bind the shipped bytes, and a mutant that deletes the eviction
// statement from that same source must fail the same discriminator.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const owner=new URL('../../real-sky/native-preview.mjs',import.meta.url);
const source=fs.readFileSync(owner,'utf8');
const EVICTION='if(displayGeometryCache.size===4)displayGeometryCache.delete(displayGeometryCache.keys().next().value);';
const HIT='if(c.type===\'camera\'&&cached)return cached;';
let instances=0;
const ROLL='rollDeg:view.rollDeg??0}';
async function load({dropEviction=false,dropHit=false,dropRoll=false}={}){
 let s=source.replace(/from '(\.\/[^']+)'/g,(_,v)=>'from '+JSON.stringify(new URL(v,owner).href));
 for(const [flag,rule,to] of [[dropEviction,EVICTION,''],[dropHit,HIT,''],[dropRoll,ROLL,'rollDeg:0}']])if(flag){assert.equal(s.split(rule).length,2,'the mutated statement exists exactly once in the shipped source');s=s.replace(rule,to);}
 s+='\n// instance '+(++instances)+'\nexport const peekDisplayGeometry=()=>[...displayGeometryCache];';
 return import('data:text/javascript;base64,'+Buffer.from(s).toString('base64'));
}
const raster={width:325,height:530,physicalState:{sun:{altDeg:40,azDeg:150}},atmosphere:{aerosolG:.76}};
const view=i=>({type:'camera',width:325,height:530,azDeg:180+i,altDeg:45,fovYDeg:90,rollDeg:0});
// The Sun is "active" (the only path that reaches the memo) when it is above 10
// degrees with a finite azimuth and the anchor lies inside the raster.
const touch=(m,i)=>m.nativeSolarRegistration(raster,view(i),{x:60,y:120,presence:1});
function exercise(m){
 const trace=[];
 for(let i=0;i<6;i++){touch(m,i);trace.push(m.peekDisplayGeometry().map(([key])=>key));}
 const firstKey=JSON.stringify({type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0});
 const rows=m.peekDisplayGeometry();
 return{trace,firstKey,rows};
}
function bounded({trace,firstKey,rows}){
 assert.deepEqual(trace.map(t=>t.length),[1,2,3,4,4,4],'size grows to four and never beyond');
 assert.ok(trace[3].includes(firstKey),'the oldest view is retained while there is room');
 assert.ok(!rows.some(([k])=>k===firstKey),'the oldest view is the one evicted by the fifth');
 assert.equal(rows.length,4);
}
test('display-geometry memo is activated by the real Sun path (precondition)',async()=>{
 const m=await load(),r=touch(m,0);assert.equal(r.active,true);assert.equal(m.peekDisplayGeometry().length,1);
});
test('display-geometry memo evicts its oldest view and retains at most four',async()=>bounded(exercise(await load())));
test('a repeated view returns the memoised geometry object, not a rebuilt one',async()=>{
 const m=await load();for(let i=0;i<4;i++)touch(m,i);
 const before=m.peekDisplayGeometry();touch(m,3);touch(m,1);const after=m.peekDisplayGeometry();
 assert.equal(after.length,4);
 for(let i=0;i<4;i++){assert.equal(after[i][0],before[i][0]);assert.strictEqual(after[i][1],before[i][1],'entry '+i+' is the same object');}
});
test('removing the actual eviction fails the same resource-bound discriminator',async()=>{
 const mutant=await load({dropEviction:true});assert.throws(()=>bounded(exercise(mutant)),assert.AssertionError);
});
test('removing the cache hit fails the identity discriminator',async()=>{
 const m=await load({dropHit:true});for(let i=0;i<4;i++)touch(m,i);
 const before=m.peekDisplayGeometry();touch(m,3);const after=m.peekDisplayGeometry();
 assert.throws(()=>{for(let i=0;i<4;i++)assert.strictEqual(after[i][1],before[i][1]);},assert.AssertionError);
});
test('views that differ only in roll are distinct cache keys',async()=>{
 const m=await load(),roll=r=>m.nativeSolarRegistration(raster,{...view(0),rollDeg:r},{x:60,y:120,presence:1});
 roll(0);roll(10);assert.equal(m.peekDisplayGeometry().length,2);
});
test('dropping roll from the key fails the roll discriminator',async()=>{
 const m=await load({dropRoll:true}),roll=r=>m.nativeSolarRegistration(raster,{...view(0),rollDeg:r},{x:60,y:120,presence:1});
 roll(0);roll(10);assert.throws(()=>assert.equal(m.peekDisplayGeometry().length,2),assert.AssertionError);
});
