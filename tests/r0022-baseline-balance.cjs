// Matched source-consumer controls. Equality here does not certify composited pixels.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const {load,sha,root}=require('./r001d-harness.cjs');
const path=require('node:path');
const baseCommit='fd2972ba64225fe9d6848e92497e6d0ed20ea624';
const baseline=execFileSync('git',['show',baseCommit+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
// R000A intentionally changes accepted marker classifications and descriptions.
// Keep its exact accepted source identity and separately compare ALL arc geometry.
const acceptedPrayerCommit='8b83df029966c203a503ab217d121c48b8ee6e8a';
const acceptedPrayer=execFileSync('git',['show',acceptedPrayerCommit+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
const sourcePath=process.argv[2]||path.join(root,'index.html'),candidate=fs.readFileSync(sourcePath,'utf8');
let pass=0,fail=0;
function test(name,fn){try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
function scene(source,fraction,altitude=20,time='22:00'){
  const h=load({source});h.run('SIM.moon="'+fraction+'";SIM.moonAlt="'+altitude+'";'+(time==='12:30'?'_simBase=Date.parse("2026-09-08T09:30:00Z");':'')+'renderMoon();projectStars(simDate());applyTheme(model());');
  const A=h.run('atmosphere(model())'),css={};
  for(const p of ['--sunamt','--suncore','--sunmid','--sunhalo','--sundogs','--sunpillar','--anticrep','--moonbeam','--mhalo','--mcorona','--mparhelia','--moongrp','--moonocc','--moonfeat','--g1','--g2','--g3','--stars','--mw'])css[p]=h.select('.c').style.getPropertyValue(p);
  return {h,A,css,glow:h.select('.mglow').style.getPropertyValue('--mgo'),stars:h.run('JSON.stringify(_starEls.map(e=>[e.getAttribute("cx"),e.getAttribute("cy"),e.style.opacity]))'),glints:h.run('JSON.stringify(_glintEls.map(e=>[e.getAttribute("transform"),e.style.opacity]))')};
}
for(const frac of ['.08','.5','.92','1'])test('eligible '+frac+' matches baseline light gains and projected appearance',()=>{
  const before=scene(baseline,frac),after=scene(candidate,frac);
  assert.deepEqual(after.css,before.css);assert.equal(after.glow,before.glow);assert.equal(after.stars,before.stars);assert.equal(after.glints,before.glints);
  for(const field of ['moonlightIntensity','lunarHalo','lunarCorona','moonParhelia','cloudMoonLit'])assert.equal(after.A[field],before.A[field],field);
});
for(const [name,altitude,time] of [['daylight',20,'12:30'],['below horizon',-10,'22:00']])test(name+' keeps solar/sky/calendar outputs unchanged',()=>{
  const before=scene(baseline,'1',altitude,time),after=scene(candidate,'1',altitude,time);assert.deepEqual(after.css,before.css);
});
// R0025 intentionally changes travel/population/time and periodic copy orchestration.
// Protect the unchanged art, with an explicit mutation control, instead of requiring
// the entire old painter (and its epoch jump) to remain byte-identical.
const protectedCloudParts=[['puff template','const _PUFF=[','function _drawPuff('],['puff shader','function _drawPuff(','// CLOUD ENGINE — clouds are']];
for(const [name,start,end] of [['PBR','function renderMoonPBR(','function moonNow('],...protectedCloudParts])test(name+' source remains byte-identical',()=>{
  const part=s=>s.slice(s.indexOf(start),s.indexOf(end,s.indexOf(start)));assert.ok(part(baseline).length>100);assert.equal(part(candidate),part(baseline));
});
const decks=s=>{const start=s.indexOf('const decks=[',s.indexOf('function paintClouds('));assert.ok(start>0);return s.slice(start,s.indexOf('];',start)+2);};
test('cloud deck sizes/bands/opacity/slots remain identical',()=>assert.equal(decks(candidate),decks(baseline)));
const lighting=s=>{const start=s.indexOf('const sux=S.sunX*W-cx',s.indexOf('function paintClouds(')),end=s.indexOf('_drawPuff(ctx,px,py,pr,col,aBase);',start);assert.ok(start>0&&end>start);return s.slice(start,end).split('\n').map(l=>l.trim()).join('\n');};
test('cloud colour/volume/sun/moon lighting equations remain identical',()=>assert.equal(lighting(candidate),lighting(baseline)));
test('cloud growth/radius/coverage gate equations remain identical',()=>{
  for(const prefix of ['const base=[tint','const gate=clamp((cov','const aMul=life*gate','const R=R0*']){
    const line=s=>s.split('\n').map(l=>l.trim()).find(l=>l.startsWith(prefix));assert.ok(line(baseline));assert.equal(line(candidate),line(baseline));
  }
});
test('protected cloud shader guard catches a flattened core gradient',()=>{
  const start='function _drawPuff(',end='// CLOUD ENGINE — clouds are',part=s=>s.slice(s.indexOf(start),s.indexOf(end,s.indexOf(start)));
  const shader=part(candidate),anchor='g.addColorStop(0.5';assert.ok(shader.includes(anchor));
  assert.notEqual(part(candidate.replace(anchor,'g.addColorStop(0.4')),part(baseline));
});
const arcPart=s=>{const start=s.indexOf('function drawArc('),end=s.indexOf('// ---- continuous time-of-day sky',start);assert.ok(start>=0&&end>start);return s.slice(start,end);};
test('solar arc source matches exact accepted R000A reference',()=>assert.equal(arcPart(candidate),arcPart(acceptedPrayer)));
function arcGeometry(source,{lat,lon,epoch,record}){
  const h=load({source});if(record)h.ctx.__geometryPrayer=record;
  h.run('lat='+lat+';lon='+lon+';_simBase=Date.parse('+JSON.stringify(epoch)+');_simTz=tz;'+(record?'today=__geometryPrayer;tomorrow=__geometryPrayer;':''));
  const output=h.run('drawArc(model())');
  const geometry=[...output.matchAll(/<(line|path|circle)\b([^>]*?)\/?>/g)].map(([,tag,text])=>{
    const attrs=Object.fromEntries([...text.matchAll(/([\w-]+)="([^"]*)"/g)].map(([,k,v])=>[k,v]));
    if(tag==='circle'&&attrs.class?.split(/\s+/).includes('dot')){
      attrs.class=attrs.class.split(/\s+/).filter(v=>v!=='adj').join(' ');
      for(const k of ['data-adjustment','data-angle','data-solar-min','data-solar-max'])delete attrs[k];
    }
    return {tag,attrs};
  });
  assert.equal(geometry.filter(g=>g.tag==='circle').length,h.run('model().dots.length'));
  assert.ok(geometry.some(g=>g.tag==='path'&&g.attrs.class==='rail'));
  assert.ok(geometry.some(g=>g.tag==='line'&&g.attrs.class==='horizon'));
  return {geometry,output};
}
const summer=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-tromso-summer.json'),'utf8')).data;
const winter=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-tromso-winter.json'),'utf8')).data;
const arcCases=[
  ['Madinah noon',{lat:24.47,lon:39.61,epoch:'2026-09-08T09:30:00Z'}],
  ['London shallow night',{lat:51.5,lon:-.12,epoch:'2026-06-21T21:00:00Z'}],
  ['Tromso summer',{lat:69.6492,lon:18.9553,epoch:'2026-06-21T09:30:00Z',record:summer}],
  ['Tromso winter',{lat:69.6492,lon:18.9553,epoch:'2026-12-21T09:30:00Z',record:winter}],
];
for(const [name,inputs] of arcCases)test(name+' actual solar path/horizon/marker geometry matches baseline',()=>{
  const before=arcGeometry(baseline,inputs),after=arcGeometry(candidate,inputs);
  assert.deepEqual(after.geometry,before.geometry);assert.ok(after.output.includes('data-adjustment='));
});
test('solar geometry guard detects displaced horizon despite accepted metadata',()=>{
  const inputs=arcCases[0][1],anchor='H=180,hY=104,Ad=104';assert.ok(candidate.includes(anchor));
  const mutant=candidate.replace(anchor,'H=180,hY=103,Ad=104');
  assert.notDeepEqual(arcGeometry(mutant,inputs).geometry,arcGeometry(baseline,inputs).geometry);
});
for(const key of ['MOON_ALBEDO','MOON_NORMAL'])test(key+' payload/provenance line remains byte-identical',()=>{
  const line=s=>s.split('\n').find(l=>l.startsWith('const '+key+'='));assert.ok(line(baseline));assert.equal(line(candidate),line(baseline));
});
console.log(JSON.stringify({baseCommit,baselineSha256:sha(Buffer.from(baseline)),acceptedPrayerCommit,acceptedPrayerSha256:sha(Buffer.from(acceptedPrayer)),sourcePath,sourceSha256:sha(Buffer.from(candidate)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'matched VM/source controls, not native no-op/crops/performance'}));
process.exitCode=fail?1:0;
