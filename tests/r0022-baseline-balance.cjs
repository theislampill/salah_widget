// Matched source-consumer controls. Equality here does not certify composited pixels.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const {load,sha,root}=require('./r001d-harness.cjs');
const path=require('node:path');
const baseCommit='fd2972ba64225fe9d6848e92497e6d0ed20ea624';
const baseline=execFileSync('git',['show',baseCommit+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
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
for(const [name,start,end] of [['PBR','function renderMoonPBR(','function moonNow('],['cloud raster','function paintClouds(','// ---- ATMOSPHERE STATE'],['solar arc','function drawArc(','// ---- continuous time-of-day sky']])test(name+' source remains byte-identical',()=>{
  const part=s=>s.slice(s.indexOf(start),s.indexOf(end,s.indexOf(start)));assert.ok(part(baseline).length>100);assert.equal(part(candidate),part(baseline));
});
for(const key of ['MOON_ALBEDO','MOON_NORMAL'])test(key+' payload/provenance line remains byte-identical',()=>{
  const line=s=>s.split('\n').find(l=>l.startsWith('const '+key+'='));assert.ok(line(baseline));assert.equal(line(candidate),line(baseline));
});
console.log(JSON.stringify({baseCommit,baselineSha256:sha(Buffer.from(baseline)),sourcePath,sourceSha256:sha(Buffer.from(candidate)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'matched VM/source controls, not native no-op/crops/performance'}));
process.exitCode=fail?1:0;
