// Matched source-consumer controls. Equality here does not certify composited pixels.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const {load,sha,root,prayerForDate}=require('./r001d-harness.cjs');
const path=require('node:path');
const option=name=>process.argv.find(s=>s.startsWith('--'+name+'='))?.slice(name.length+3);
const gitSource=(commit,file)=>execFileSync('git',['show',commit+':'+file],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
const baseCommit='fd2972ba64225fe9d6848e92497e6d0ed20ea624';
const baseline=option('baseline')?fs.readFileSync(option('baseline'),'utf8'):gitSource(baseCommit,'index.html');
assert.equal(sha(Buffer.from(baseline)),'446453b522f56f5f1bc0afd1a3abd09b73756754fa58a6b3b0ff09ce953a2eec','Pinned original baseline bytes');
// R000A intentionally changes accepted marker classifications and descriptions.
// Keep its exact accepted source identity and separately compare ALL arc geometry.
const acceptedPrayerCommit='8b83df029966c203a503ab217d121c48b8ee6e8a';
const acceptedPrayer=option('accepted-prayer')?fs.readFileSync(option('accepted-prayer'),'utf8'):gitSource(acceptedPrayerCommit,'index.html');
assert.equal(sha(Buffer.from(acceptedPrayer)),'63d2b3e46f71854cc383b5cd240d44f9dc3e006378ff4d3cd85bfb5861d3adf1','Pinned accepted prayer bytes');
const acceptedNativeCommit='18ff14860ff41c084b1db5f396bb62aa9c22b1be';
const acceptedNative=option('accepted-native')?fs.readFileSync(option('accepted-native'),'utf8'):gitSource(acceptedNativeCommit,'index.html');
assert.equal(sha(Buffer.from(acceptedNative)),'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee','Pinned accepted CP9/V5 native bytes');
const sourcePath=process.argv.slice(2).find(s=>!s.startsWith('--'))||path.join(root,'index.html'),candidate=fs.readFileSync(sourcePath,'utf8'),candidateRoot=path.dirname(path.resolve(sourcePath));
let pass=0,fail=0;
function test(name,fn){try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
const protectedGainFields=['moonlightIntensity','moonBeam','moonGlow','moonLocalWash','lunarHalo','lunarCorona','moonParhelia','cloudMoonLit','cloudMoonX','cloudMoonY','cloudMoonCol'];
const acceptedSolarCss=new Set(['--suncore','--sunmid']);
function plain(value){return JSON.parse(JSON.stringify(value));}
function scene(source,fraction,altitude=20,time='22:00',waxing='1'){
  const h=load({source});h.run('SIM.moon="'+fraction+'";SIM.moonAlt="'+altitude+'";SIM.wax="'+waxing+'";'+(time==='12:30'?'_simBase=Date.parse("2026-09-08T09:30:00Z");':'')+'renderMoon();render();');
  const A=h.run('atmosphere(model())'),css={};
  for(const p of ['--sunamt','--suncore','--sunmid','--sunhalo','--sundogs','--sunpillar','--anticrep','--moonbeam','--mhalo','--mcorona','--mparhelia','--moongrp','--moonocc','--moonfeat','--g1','--g2','--g3','--stars','--mw'])css[p]=h.select('.c').style.getPropertyValue(p);
  const gains=plain(Object.fromEntries(protectedGainFields.map(k=>[k,A[k]])));
  if(A.moonGlow===undefined||A.moonLocalWash===undefined){
    assert.equal(sha(Buffer.from(source)),sha(Buffer.from(baseline)),'Only pinned original baseline lacks the new raw gain fields');
    // The old inline owners consumed these expressions without exporting raw
    // fields. Execute their exact pinned expressions; do not restore arrays.
    const washLine=source.split('\n').find(l=>l.trim().startsWith('const mw=(moonSky&&moonSky.up!=null)?'));
    assert.ok(washLine&&washLine.trim().endsWith(';'),'original wash owner boundary');
    gains.moonLocalWash=h.run('(()=>{'+washLine+' return mw;})()');
    const oldGlow=source.match(/gl\.style\.setProperty\("--mgo",\(([^;]+)\)\.toFixed\(3\)\);/g);
    assert.equal(oldGlow?.length,1,'one original local glow owner');
    const expression=/gl\.style\.setProperty\("--mgo",\(([^;]+)\)\.toFixed\(3\)\);/.exec(oldGlow[0])[1];
    gains.moonGlow=h.run('((frac)=>('+expression+'))(moonSky.frac)');
  }
  return {h,A,css,glow:h.select('.mglow').style.getPropertyValue('--mgo'),gains,cloud:plain(h.run('({moonLit:cloudState.moonLit,moonX:cloudState.moonX,moonY:cloudState.moonY,moonCol:cloudState.moonCol})'))};
}
function compareCss(before,after,accepted){
  // CP9 accepted solar tone-map colours have their own exact oracle. Every
  // other original sky/calendar/light CSS value still compares to fd2972.
  for(const key of Object.keys(before.css))assert.equal(after.css[key],(acceptedSolarCss.has(key)?accepted:before).css[key],key);
}
function compareEligible(source,frac,waxing='1'){
  const before=scene(baseline,frac,20,'22:00',waxing),after=scene(source,frac,20,'22:00',waxing),accepted=scene(acceptedNative,frac,20,'22:00',waxing);
  compareCss(before,after,accepted);assert.equal(after.glow,before.glow,'actual .mglow consumer');
  assert.deepEqual(after.gains,before.gains,'all protected native lunar gains and source position');
  assert.deepEqual(after.cloud,before.cloud,'actual consumed cloud lunar state');
  assert.ok(after.gains.moonlightIntensity>0&&after.gains.moonBeam>0&&after.gains.moonGlow>0,'eligible positive controls');
  assert.equal(after.h.run('qaState().moonTruth.lunarLight.eligible'),true);
  return {fraction:frac,waxing,gains:after.gains,cloud:after.cloud,css:after.css,glow:after.glow};
}
const gainRows=[];
for(const frac of ['.08','.5','.92','1'])test('eligible '+frac+' matches protected baseline gains at actual native consumers',()=>{
  for(const waxing of ['1','0'])gainRows.push(compareEligible(candidate,frac,waxing));
});
for(const [name,altitude,time] of [['daylight',20,'12:30'],['below horizon',-10,'22:00']])test(name+' preserves protected solar/sky/calendar outputs with explicit accepted solar mapping',()=>{
  const before=scene(baseline,'1',altitude,time),after=scene(candidate,'1',altitude,time),accepted=scene(acceptedNative,'1',altitude,time);
  compareCss(before,after,accepted);
  for(const field of protectedGainFields)assert.deepEqual(after.gains[field],(['moonGlow','moonLocalWash'].includes(field)?accepted:before).gains[field],field+' native-zero amendment');
  assert.equal(after.glow,accepted.glow);assert.deepEqual(after.cloud,before.cloud);
});
test('protected phase-gain guard rejects a changed .08 crescent curve',()=>{
  const anchor='(0.35+0.65*mFrac)',hits=candidate.split(anchor).length-1;assert.equal(hits,1,'one actual native gain anchor');
  assert.throws(()=>compareEligible(candidate.replace(anchor,'(0.36+0.64*mFrac)'),'.08'),/protected|moon|--/);
});
// R0025 intentionally changes travel/population/time and periodic copy orchestration.
// Protect the unchanged art, with an explicit mutation control, instead of requiring
// the entire old painter (and its epoch jump) to remain byte-identical.
const protectedCloudParts=[['puff template','const _PUFF=[','function _drawPuff('],['puff shader','function _drawPuff(','// CLOUD ENGINE — clouds are']];
for(const [name,start,end] of protectedCloudParts)test(name+' source remains byte-identical',()=>{
  const part=s=>s.slice(s.indexOf(start),s.indexOf(end,s.indexOf(start)));assert.ok(part(baseline).length>100);assert.equal(part(candidate),part(baseline));
});
function materialPart(source){
  const start='function renderMoonCalendarFallback(',end='// REAL CATALOGUE:';
  assert.equal(source.split(start).length,2,'one current calendar/material owner');assert.equal(source.split(end).length,2,'one current catalogue boundary');
  return source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
}
test('current native phase/body/Earthshine/material equations match accepted CP9/V5 owner',()=>{
  assert.equal(sha(Buffer.from(materialPart(candidate))),'22e5b5c7abee4f3197a3a8ddfd2b5ebc879f2c9546e5d0cd298253bc98ab1392','accepted current material section');
  assert.equal(materialPart(candidate),materialPart(acceptedNative));
});
test('current material guard rejects altered Earthshine without relying on old PBR wrapper bytes',()=>{
  const part=materialPart(candidate),anchor='const esFloor=0.09';
  assert.equal(part.split(anchor).length,2,'one accepted native legacy material Earthshine floor');
  const mutated=part.replace(anchor,'const esFloor=0');assert.notEqual(sha(Buffer.from(mutated)),'22e5b5c7abee4f3197a3a8ddfd2b5ebc879f2c9546e5d0cd298253bc98ab1392','Earthshine counterfactual cannot earn material preservation');
});
// The owner-approved single-entry projection cache changes this compositor's
// source identity. Actual old/new material, atmosphere and cloud composition
// execute in moon-projection-cache.test.mjs and the bound native comparisons;
// this inventory and the generated-consumer checks are packaging guards only.
const protectedCurrentMaterial={"moon/src/surface_v5.mjs":"f0d0b4ab0b5478979371c8c9839d53dfb688596dd08773769d7d9c254c02b65f","moon/src/moon-calendar.mjs":"b508ea0a0bbc2a68039ba71bb4be75299cfa57bcb74992be1b1b0a0eddfad953","moon/src/moon-detail.mjs":"f2596f26f19f946873792a7e121ea472b361021c8cc2b1831faa6cd10fdef07c","moon/src/moon-precision.mjs":"e0ca3303f1cbdcb87a6d80b73fdbbe132d3c8e9e0becde25435724e8ac72dca1","moon/src/moon_kernel.c":"919bf0b0a17ceb1ce3d3d7e0b5d9958bba3835b96e8558d6b518e7db1137f57f","moon/moon_kernel.wasm":"4fcf7888b55486947189c4a701c75ab25465714036c42fc60980e98ac0bdcbb7","moon/asset-manifest.json":"3d4cb527489acda67082bbc97d984abbb28a11a40f0aec8b4030223fb15e9afa"};
test('frozen pre-cache compositor remains the exact adopted reference',()=>assert.equal(sha(fs.readFileSync(path.join(candidateRoot,'tests/fixtures/moon-detail-pre-cache.mjs'))),'3cfa1498918706adf21a5f8462f27f9919bed9402f179b03ae3e932500c5cba0'));
for(const [file,expected] of Object.entries(protectedCurrentMaterial))test(file+' matches adopted V5 material/profile/opaque source',()=>assert.equal(sha(fs.readFileSync(path.join(candidateRoot,file))),expected,file));
const moonHost=fs.readFileSync(path.join(candidateRoot,'moon/moon-host.js'),'utf8');
const moonWorker=fs.readFileSync(path.join(candidateRoot,'moon/moon-worker.js'),'utf8');
const moonBuild=JSON.parse(fs.readFileSync(path.join(candidateRoot,'moon/BUILD.json'),'utf8'));
function boundWorker(host){
  const declarations=[...host.matchAll(/^const MOON_WORKER_SOURCE=(.+);$/gm)];
  assert.equal(declarations.length,1,'one actual worker payload in loaded host');
  const worker=JSON.parse(declarations[0][1]);
  assert.equal(worker,moonWorker,'loaded host and standalone worker bytes');
  assert.equal(sha(Buffer.from(worker)),moonBuild.workerSha256,'canonical generated worker binding');
  return worker;
}
test('HTTP Moon consumer resolves the canonical host and its exact worker payload',()=>{
  assert.equal(candidate.split('<script src="moon/moon-host.js"></script>').length,2,'single HTTP host route');
  assert.equal(sha(Buffer.from(moonHost)),moonBuild.hostSha256,'canonical generated host binding');
  assert.equal(boundWorker(moonHost),moonWorker);
  assert.throws(()=>boundWorker(moonHost.replace(/^const MOON_WORKER_SOURCE=.+;$/m,'const MOON_WORKER_SOURCE="wrong worker";')),/worker/);
});
for(const file of ['moon/src/surface_v5.mjs','moon/src/moon-calendar.mjs','moon/src/moon-detail.mjs','moon/src/moon-precision.mjs'])test(file+' actual generated host/worker consumes the exact authored material once',()=>{
  const owner=fs.readFileSync(path.join(candidateRoot,file),'utf8');
  // build_moon.concat strips trailing whitespace and appends exactly one LF.
  const generated='// '+path.basename(file)+'\n'+owner.trimEnd()+'\n';
  // The current HTTP entry loads the host externally; surface_v5 belongs to
  // the worker embedded in that host, while the other three have host owners.
  // These packaging bindings supplement actual native material/opacity proof.
  const consumer=file.endsWith('surface_v5.mjs')?boundWorker(moonHost):moonHost;
  assert.equal(consumer.split(generated).length,2,'unique material source in actual generated consumer: '+file);
});
test('actual V5 material retains Earthshine and rejects a zero-Earth counterfactual',()=>{
  const source=fs.readFileSync(path.join(candidateRoot,'moon/src/surface_v5.mjs'),'utf8'),anchor='const c=Array.from(solar,(x,i)=>x+earth[i]);';
  assert.equal(source.split(anchor).length,2,'one actual current V5 solar/Earth material join');
  const mapping=s=>Function(s+'\nreturn mapSurfaceRgb;')(),healthy=mapping(source),wrong=mapping(source.replace(anchor,'const c=Array.from(solar,(x,i)=>x+0*earth[i]);'));
  const profile={schema:'lunar-presentation/5',profile_id:'calendar-neutral-v5-01',mode:'calendar',exposure:2.9195482731525044,lift:.003,knee:5.388411226362526e-6,colour_basis:'linear-sRGB',gamut:'luminance-preserving-neutral-axis'};
  const dark=[0,0,0],earth=[.001,.001,.001],ashen=healthy(dark,earth,profile);
  assert.ok(ashen.every(x=>x>0&&x<1),'positive ashen material source');assert.deepEqual(wrong(dark,earth,profile),dark,'counterfactual removes Earthshine');
  assert.notDeepEqual(wrong(dark,earth,profile),ashen,'material difference actually reaches the mapping');
  assert.deepEqual(healthy(dark,dark,profile),dark,'zero light control');assert.throws(()=>healthy(dark,[-.001,0,0],profile),/finite nonnegative/);
});
const decks=s=>{const start=s.indexOf('const decks=[',s.indexOf('function paintClouds('));assert.ok(start>0);return s.slice(start,s.indexOf('];',start)+2);};
test('cloud deck sizes/bands/opacity/slots remain identical',()=>assert.equal(decks(candidate),decks(baseline)));
// H7/H8 deliberately replaces the prayer-arc solar vector and whole-deck warm
// tint with physical camera-direction lighting. Keep the OLD equality guard
// for every other line (volume, opacity, lining gains and lunar illumination).
// Direction/continuity is independently tested in native-preview.test.mjs and
// actual camera-rotation/moving-weather captures, not claimed byte-identical.
const lighting=s=>{const start=s.indexOf('const mux=S.moonX*W-cx',s.indexOf('function paintClouds(')),end=s.indexOf('_drawPuff(ctx,px,py,pr,col,aBase);',start);assert.ok(start>0&&end>start);return s.slice(start,end).split('\n').map(l=>l.trim()).filter(l=>!l.startsWith('// Warm direct light')&&!l.startsWith('// physical camera direction')&&!l.startsWith('const warmth=(S.warmth??0)*facing;')).join('\n');};
test('cloud volume/opacity/lining/lunar equations remain identical outside authorised directional solar lighting',()=>assert.equal(lighting(candidate),lighting(baseline)));
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
test('solar arc math matches accepted R000A apart from the declared prayer-key diagnostic',()=>{
  const actual=arcPart(candidate),diagnostic=' data-prayer-key="${p.k}"';
  assert.equal(actual.split(diagnostic).length,2,'one explicit diagnostic owner');
  assert.equal(actual.replace(diagnostic,''),arcPart(acceptedPrayer));
});
function arcGeometry(source,{lat,lon,epoch,record,zone='Asia/Riyadh'}){
  const h=load({source});
  // A geometry comparison still needs an admitted date/zone. The old fixture
  // changed its clock to June/December while retaining a September prayer
  // bundle (and used Riyadh for the Oslo records). H6 correctly rejects that.
  zone=record?.meta.timezone||zone;
  const fields=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:zone,day:'2-digit',month:'2-digit',year:'numeric'}).formatToParts(new Date(epoch)).map(p=>[p.type,p.value]));
  const day=[fields.day,fields.month,fields.year].join('-');
  h.ctx.__geometryPrayer=record||prayerForDate(day);
  if(!record)h.ctx.__geometryPrayer.meta.timezone=zone;
  h.run('lat='+lat+';lon='+lon+';tz=__geometryPrayer.meta.timezone;_simBase=Date.parse('+JSON.stringify(epoch)+');_simTz=tz;today=__geometryPrayer;tomorrow=__geometryPrayer;');
  const output=h.run('drawArc(model())');
  const geometry=[...output.matchAll(/<(line|path|circle)\b([^>]*?)\/?>/g)].map(([,tag,text])=>{
    const attrs=Object.fromEntries([...text.matchAll(/([\w-]+)="([^"]*)"/g)].map(([,k,v])=>[k,v]));
    if(tag==='circle'&&attrs.class?.split(/\s+/).includes('dot')){
      attrs.class=attrs.class.split(/\s+/).filter(v=>v!=='adj').join(' ');
      for(const k of ['data-adjustment','data-angle','data-solar-min','data-solar-max','data-prayer-key'])delete attrs[k];
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
  ['London shallow night',{lat:51.5,lon:-.12,epoch:'2026-06-21T21:00:00Z',zone:'Europe/London'}],
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
console.log(JSON.stringify({acceptedNativeCommit,acceptedNativeSha256:sha(Buffer.from(acceptedNative)),gainRows,protectedCurrentMaterial,acceptedDeltas:{solarCss:[...acceptedSolarCss],corona:"current admitted mid-water cloud/fog, independently covered by lunar-consumers; no changed eligible thin-ice gain",catalogue:"real admitted catalogue/accepted astronomy replaces synthetic arrays; current interface controls required",material:"adopted V5/native body/Earthshine/opaque source; native image review still required",cloudSolar:"physical camera-direction lighting outside protected equations"},baseCommit,baselineSha256:sha(Buffer.from(baseline)),acceptedPrayerCommit,acceptedPrayerSha256:sha(Buffer.from(acceptedPrayer)),sourcePath,sourceSha256:sha(Buffer.from(candidate)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'matched VM/source controls, not native no-op/crops/performance'}));
process.exitCode=fail?1:0;
