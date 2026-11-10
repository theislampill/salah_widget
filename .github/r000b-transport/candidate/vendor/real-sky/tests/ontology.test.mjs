import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
let mod={};try{mod=await import('../src/constellations.mjs')}catch{}
const read=n=>JSON.parse(fs.readFileSync(new URL('../data/'+n,import.meta.url)));
test('constellation membership handles poles, RA wrap, deterministic boundaries',()=>{
 assert.equal(typeof mod.constellationB1875,'function');const d=read('constellations.json');
 assert.equal(mod.constellationB1875(0,90,d),'UMi');assert.equal(mod.constellationB1875(359,90,d),'UMi');assert.equal(mod.constellationB1875(0,-90,d),'Oct');
 for(const ra of [0,24*15,-360,720])assert.equal(mod.constellationB1875(ra,0,d),'Psc');
 assert.throws(()=>mod.constellationB1875(NaN,0,d));assert.throws(()=>mod.constellationB1875(0,91,d));
});
test('reference-frame-aware catalogue membership finds real bright sources',()=>{
 assert.equal(typeof mod.constellationJ2000,'function');const c=read('catalogue-v6_5.json'),d=read('constellations.json');
 for(const [hip,name] of [[11767,'UMi'],[32349,'CMa'],[24436,'Ori'],[80763,'Sco'],[30438,'Car']]){
  const s=c.stars.find(s=>s.hip===hip);assert.equal(mod.constellationJ2000(s.raDeg,s.decDeg,d),name);
 }
});
test('88 regions cover full sphere and every source-pattern endpoint resolves',()=>{
 assert.equal(fs.existsSync(new URL('../data/constellations.json',import.meta.url)),true);const d=read('constellations.json'),a=read('annotations.json'),c=read('catalogue-v6_5.json');
 assert.equal(d.regions.length,88);assert.equal(new Set(d.regions.map(r=>r.abbr)).size,88);assert.ok(Math.abs(d.regions.reduce((s,r)=>s+r.areaSteradians,0)-4*Math.PI)<1e-9);
 assert.equal(d.boundaryFrame,'B1875-mean-equatorial');assert.ok(d.edges.length>500);for(const e of d.edges)assert.notEqual(e.regions[0],e.regions[1]);
 assert.equal(a.patterns.filter(p=>p.kind==='constellation-pattern').length,88);const hips=new Set(c.stars.map(s=>s.hip));
 for(const p of a.patterns)for(const path of p.paths)for(const hip of path)assert.ok(hips.has(hip),`${p.id}: ${hip}`);
 assert.ok(a.patterns.find(p=>p.id==='SummerTriangle'));assert.ok(a.patterns.find(p=>p.id==='BigDipper'));assert.equal(a.enabledByDefault,false);
});
test('all record memberships are geometric; historical invalid tokens are retained separately',()=>{
 assert.equal(fs.existsSync(new URL('../data/constellations.json',import.meta.url)),true);const c=read('catalogue-v6_5.json'),d=read('constellations.json');
 const names=new Set(d.regions.map(r=>r.abbr));for(const s of c.stars)assert.ok(names.has(s.constellationMembership?.abbr));
 assert.equal(c.stars.find(s=>s.hygId===119628).sourceValues.con,'Eco');assert.notEqual(c.stars.find(s=>s.hygId===119628).constellationMembership.abbr,'Eco');
});
test('system records and components cannot both contribute duplicated flux',()=>{
 assert.equal(fs.existsSync(new URL('../data/star-systems.json',import.meta.url)),true);const c=read('bright-stars.json'),g=read('star-systems.json');const by=new Map(c.stars.map(s=>[s.id,s]));
 assert.equal(by.get('hyg:24549').emission.enabled,true);assert.equal(by.get('hyg:118360').emission.enabled,false);
 assert.equal(by.get('hyg:36744').emission.enabled,true);assert.equal(by.get('hyg:118485').emission.enabled,false);
 for(const group of g.groups){assert.ok(group.evidence);assert.ok(group.memberIds.length>1);for(const id of group.emitterIds)assert.ok(group.memberIds.includes(id));
  assert.equal(group.emitterIds.length,group.memberIds.filter(id=>by.get(id).emission.enabled).length);
 }
 assert.equal(by.get('hyg:71453').emission.enabled,true);assert.equal(by.get('hyg:71456').emission.enabled,true);
});
test('names are aliases returning all records rather than masquerading as identities',()=>{
 assert.equal(typeof mod.lookupAlias,'function');const a=read('star-aliases.json');const p=mod.lookupAlias('  p Eridani  ',a);
 assert.ok(p.length>=2);assert.notEqual(p[0],p[1]);assert.deepEqual(mod.lookupAlias('not-a-star',a),[]);
});
test('small-circle boundaries are sampled in their defining frame',()=>{
 assert.equal(typeof mod.boundarySamples,'function');const d=read('constellations.json');const edge=d.edges.find(e=>e.a[1]===e.b[1]&&e.a[0]!==e.b[0]);
 const a=mod.boundarySamples(edge,1);assert.ok(a.length>=2);assert.ok(a.every(v=>v.every(Number.isFinite)));assert.ok(a.every(v=>Math.abs(Math.hypot(...v)-1)<1e-12));
});
test('suppressed inventory record cannot leak into renderer',async()=>{
 const {renderStars}=await import('../src/renderer.mjs');const s={hip:1,vmag:1,bv:0,altDeg:60,visible:true,x:8,y:8,emission:{enabled:false}};
 const r=renderStars([s],{width:16,height:16});assert.equal(r.drawn,0);assert.equal(r.linear.reduce((a,b)=>a+b,0),0);
});
