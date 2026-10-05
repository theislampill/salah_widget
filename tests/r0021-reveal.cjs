const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {load,root,sha}=require('./r001d-harness.cjs');const sourcePath=process.argv.slice(2).find(a=>!a.startsWith('--'))||path.join(root,'index.html'),source=fs.readFileSync(sourcePath,'utf8');let pass=0,fail=0,done=false;const cases=[];
const cp8SnapshotOnly=process.argv.includes("--cp8-snapshot-only"),cp8Exclusions={"ordinary held star positions remain stable across a healthy render": "removed synthetic-array producer; actual catalogue sink lifecycle tested separately", "first accepted target cannot retain the unresolved-coordinate projection": "removed synthetic-array producer; actual first accepted catalogue tested separately", "same-day explicit preview anchor correction reprojects accepted stars": "removed synthetic-array producer; actual catalogue seeks tested separately", "moon PBR shader and embedded payloads retain exact accepted bytes": "unsupplied historical commit 47c0fa0c6e32618f22b43b6a18717908b0de5f5e; supplied 2057503 PBR comparison runs in native-preservation tests"};
function test(name,fn){if(cp8SnapshotOnly&&cp8Exclusions[name]){console.log("SKIP_EXPLICIT",name,"—",cp8Exclusions[name]);return;}cases.push([name,fn]);}
process.on('beforeExit',()=>{if(!done){console.error('INCOMPLETE reveal suite terminal absent');process.exitCode=1;}});
function fixture(){return load({sourcePath});}
const positions=h=>h.run('JSON.stringify(_starEls.map(e=>[e.style.display,e.getAttribute("cx"),e.getAttribute("cy")]))');
test('ordinary held star positions remain stable across a healthy render',()=>{
  const h=load({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia%2FRiyadh&units=c&seed=1&simMoon=.5&simWax=1&simMoonAlt=20&simMoonH=42'});
  h.run('render();');const before=positions(h);h.clock.wall+=60000;h.clock.now+=60000;h.run('render();');assert.equal(positions(h),before);
});
test('first accepted target cannot retain the unresolved-coordinate projection',()=>{
  const h=fixture();h.run('lat=null;lon=null;buildStars();lat=24.47;lon=39.61;render();');const first=positions(h);h.run('projectStars(simDate())');assert.equal(first,positions(h));
});
test('same-day explicit preview anchor correction reprojects accepted stars',()=>{
  const h=fixture();h.run('render();_simBase+=3600000;render();');const first=positions(h);h.run('projectStars(simDate())');assert.equal(first,positions(h));
});
test('initial source hides only sky decorations and retains usable prayer/settings markup',()=>{
  assert.match(source,/<div class="c[^\"]*sky-pending/);assert.match(source,/\.c\.sky-pending[^{}]*\{[^}]*background:/);
  for(const layer of ['sky','atmo','wfx','climate'])assert.ok(new RegExp('\\.c\\.sky-pending \\.'+layer).test(source),layer);
  assert.ok(!/\.c\.sky-pending \.(?:panel|times|d|header)[^{}]*\{[^}]*visibility:hidden/.test(source));
  assert.match(source,/<div class="panel">/);assert.match(source,/settings/);
});
test('ordinary twilight requires occlusion outside the fading lunar group',()=>{
  const h=fixture();h.run('_simBase=Date.parse("2026-09-08T02:40:00Z");render();');
  const A=h.run('atmosphere(model())');assert.ok(A.moonGrp>0&&A.moonGrp<1,'actual ordinary twilight group fade');assert.ok(A.starOpacity>0,'actual stellar background visible');
  assert.match(source,/<g class="stellar-background" mask="url\(#stellar-cutout\)">\s*<g class="milkyway"><\/g>\s*<g class="stars"><\/g>\s*<g class="starglints"><\/g>\s*<\/g>/);
  assert.equal(h.select('.moon-mask-geometry').getAttribute('transform'),h.select('.moon').getAttribute('transform'));
  assert.equal(+h.select('.moon-mask-disc').getAttribute('r'),h.run('_MR*96/_MN'));
});
test('accepted sky/UI does not wait for unknown weather, pending fonts or map decode',async()=>{
  const h=fixture();h.ctx.document.fonts.ready=new Promise(()=>{});
  h.run('beginSkyScene();today=null;tomorrow=null;weather=null;weatherTrack=null');
  await h.complete(h.run('boot()'));if(h.rafs.length)h.rafs.shift()();
  assert.equal(h.run('_skyCommitted'),true);assert.equal(h.select('.c').classList.contains('sky-pending'),false);
  assert.equal(h.select('.c').classList.contains('sky-initializing'),false);assert.equal(h.run('selectedWeather()'),null);
  assert.ok(h.select('.cn').textContent);assert.equal(h.select('.c').classList.contains('moon-ready'),false);
  assert.equal(h.select('.moon-mask-disc').classList.contains('mask-on'),false);assert.equal(h.select('.mphoto').getAttribute('href'),null);
  for(const im of h.images)if(typeof im.onload==='function')im.onload();
  assert.ok(h.select('.mphoto').getAttribute('href'),'real source PBR producer');
  assert.equal(h.select('.c').classList.contains('moon-ready'),true);assert.equal(h.select('.moon-mask-disc').classList.contains('mask-on'),true);
});
test('missing accepted coordinates retain neutral sky and unavailable projection',()=>{
  const h=fixture();h.run('lat=null;lon=null;beginSkyScene();buildStars();render();');
  assert.equal(h.run('_skyCommitted'),false);assert.equal(h.select('.c').classList.contains('sky-pending'),true);
  assert.equal(h.run('_starProjectionKey'),null);assert.ok(h.run('_starEls.every(e=>e.style.display==="none")'));
});
test('stale consumed moon geometry cannot commit an initial scene',()=>{
  const h=fixture();h.run('beginSkyScene();renderMoon();_simBase+=60000;projectStars(simDate());applyTheme(model())');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),false);assert.equal(h.run('_skyCommitted'),false);assert.equal(h.select('.c').classList.contains('sky-pending'),true);
});
test('failed first paint keeps entry pending and a healthy actual retry reveals',()=>{
  const h=fixture(),style=h.select('.c').style,set=style.setProperty;
  style.setProperty=(key,value)=>{if(key==='--moonbeam')throw new Error('owned style boundary failure');set(key,value);};
  assert.throws(()=>h.run('render()'),/owned style boundary failure/);assert.equal(h.run('_skyCommitted'),false);assert.equal(h.select('.c').classList.contains('sky-pending'),true);
  style.setProperty=set;h.run('render()');assert.equal(h.run('_skyCommitted'),true);assert.equal(h.select('.c').classList.contains('sky-pending'),false);
});
for(const [name,frac,alt] of [['new',.01,20],['crescent',.08,20],['half',.5,20],['gibbous',.92,20],['full',1,20],['below',.5,-10]])
  test(name+' twilight uses a surface-bound mask independent of physical light',()=>{
    const h=fixture();h.run('_simBase=Date.parse("2026-09-08T02:40:00Z");SIM.moon="'+frac+'";SIM.moonAlt="'+alt+'";render();');
    for(const im of h.images)if(typeof im.onload==='function')im.onload();
    assert.equal(h.select('.moon-mask-disc').classList.contains('mask-on'),true);assert.ok(+h.select('.c').style.getPropertyValue('--moongrp')<1);
    if(frac===.01||alt<0)assert.equal(+h.select('.c').style.getPropertyValue('--moonbeam'),0);
    assert.equal(h.select('.moon-mask-geometry').getAttribute('transform'),h.select('.moon').getAttribute('transform'));
  });
test('daytime real surface has no mask target or calendar group presence',()=>{
  const h=fixture();h.run('_simBase=Date.parse("2026-09-08T09:30:00Z");render()');
  for(const im of h.images)if(typeof im.onload==='function')im.onload();
  assert.equal(+h.select('.c').style.getPropertyValue('--moongrp'),0);assert.equal(h.select('.moon-mask-disc').classList.contains('mask-on'),false);
  assert.equal(h.select('.c').classList.contains('sky-pending'),false);
});
test('mask follows the actual transform transition and existing withdrawal duration',()=>{
  assert.match(source,/\.moon\{[^}]*opacity 1\.2s,transform 1\.6s linear/);assert.match(source,/\.moon-mask-geometry\{transition:transform 1\.6s linear\}/);
  assert.match(source,/\.moon-mask-disc\{opacity:0;transition:opacity 0s linear 1\.2s\}/);assert.match(source,/\.moon-mask-disc\.mask-on\{opacity:1;transition-delay:0s\}/);
  assert.match(source,/\.c\.fast,\.c\.fast \*\{transition:none!important\}/);
});
test('moon PBR shader and embedded payloads retain exact accepted bytes',()=>{
  const {execFileSync}=require('node:child_process'),base=execFileSync('git',['show','47c0fa0c6e32618f22b43b6a18717908b0de5f5e:index.html'],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
  const shader=s=>s.slice(s.indexOf('function renderMoonPBR('),s.indexOf('function moonNow('));assert.equal(shader(source),shader(base));
  for(const name of ['MOON_ALBEDO','MOON_NORMAL'])assert.equal(source.split('\n').find(l=>l.startsWith('const '+name+'=')),base.split('\n').find(l=>l.startsWith('const '+name+'=')));
});
// The original six controls run on the accepted pre-repair source without relying
// on newly added helpers. Preserve meaningful REDs separately from expanded coverage.
const selected=process.argv.includes('--initial-controls')?[...cases.slice(0,5),cases.at(-1)]:cases;
(async()=>{for(const [name,fn] of selected){try{await fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message.split('\n')[0]);}}
  done=true;console.log(JSON.stringify({terminal:true,declared:selected.length,executed:pass+fail,missing:selected.length-pass-fail,sourcePath,sourceSha256:sha(Buffer.from(source)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'actual state/source/CSS geometry controls; first compositor frame and occlusion pixels unrun'}));process.exitCode=fail?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
