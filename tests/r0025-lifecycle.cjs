// Whole-source visual state and painter-command controls. Only a native elapsed
// sequence can establish visible motion or quiescent performance.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {root,sha}=require('./r001d-harness.cjs'),{cloudFixture}=require('./r0025-context.cjs');
const sourcePath=process.argv[2]||path.join(root,'index.html');let pass=0,fail=0;
const fixture=extraHash=>cloudFixture({sourcePath,extraHash});
const axes=h=>JSON.parse(h.run('JSON.stringify({population:_cloudMotion.population,phase:_cloudMotion.phase,life:_cloudMotion.life,wander:_cloudMotion.wander})'));
function test(name,fn){try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message.split('\n')[0]);}}
function loop(h){
  const callbacks=new Map(),listeners=new Map();let id=0,reduced=false;
  h.ctx.requestAnimationFrame=fn=>{callbacks.set(++id,fn);return id;};h.ctx.cancelAnimationFrame=i=>callbacks.delete(i);
  h.ctx.document.addEventListener=(name,fn)=>listeners.set(name,fn);h.ctx.matchMedia=()=>({matches:reduced});h.run('startRenderLoop()');
  return {callbacks,listeners,reduce(value){reduced=value;},frame(ms=0){h.clock.now+=ms;h.clock.wall+=ms;const [id,fn]=callbacks.entries().next().value;callbacks.delete(id);fn();assert.equal(callbacks.size,1,'one owned next frame');},
    visibility(value){h.ctx.document.visibilityState=value;listeners.get('visibilitychange')();}};
}
test('live reduced/full toggles hold all axes and rebase without a substituted epoch',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();const l=loop(h);l.frame(100);const before=axes(h);
  l.reduce(true);l.frame(100);assert.deepEqual(axes(h),before);
  for(let i=0;i<30;i++)l.frame(1000);assert.deepEqual(axes(h),before);
  l.reduce(false);l.frame(100);assert.deepEqual(axes(h),before);l.frame(100);assert.notDeepEqual(axes(h),before);
});
test('motion=full respects the explicit override under a reduced OS signal',()=>{
  const h=fixture('&timeScale=1&motion=full');h.run('TIMESCALE=1');h.paint();const l=loop(h);l.reduce(true);const before=axes(h);l.frame(1000);
  assert.notDeepEqual(axes(h),before);assert.equal(h.select('.c').classList.contains('motionfull'),true);
});
test('hidden/resumed repeats freeze and rebase while retaining exactly one loop',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();const l=loop(h);l.frame(100);const before=axes(h);
  l.visibility('hidden');assert.equal(l.callbacks.size,0);h.clock.now+=60000;h.clock.wall+=60000;
  l.visibility('visible');l.visibility('visible');assert.equal(l.callbacks.size,1);l.frame();assert.deepEqual(axes(h),before);
  l.frame(100);assert.notDeepEqual(axes(h),before);l.visibility('hidden');l.visibility('visible');l.visibility('visible');assert.equal(l.callbacks.size,1);
});
test('a missing-frame gap over two seconds is bounded suspension, followed by resumed travel',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();const before=axes(h);h.step(5000);assert.deepEqual(axes(h),before);h.step(1000);assert.notDeepEqual(axes(h),before);
});
test('ordinary wall corrections preserve visual axes at the same monotonic instant',()=>{
  const h=cloudFixture({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia%2FRiyadh&units=c&seed=1&simMoon=.5&simMoonAlt=20&simMoonH=42'});h.paint();const before=axes(h);
  assert.equal(h.run('FOLLOW_WALL_CLOCK'),true);h.clock.wall+=3600000;h.run('render()');h.paint();assert.deepEqual(axes(h),before);
  h.clock.wall-=7200000;h.run('render()');h.paint();assert.deepEqual(axes(h),before);h.step(1000);assert.notDeepEqual(axes(h),before);
});
test('explicit forward/backward seeks reconstruct deterministic scene axes',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();h.step(1000);
  h.run('_simBase=Date.parse("2026-09-09T10:00:00Z");_rafT0=performance.now();render()');h.paint();const forward=axes(h);h.step(1000);
  h.run('_simBase=Date.parse("2026-09-07T10:00:00Z");_rafT0=performance.now();render()');h.paint();assert.notDeepEqual(axes(h),forward);
  h.run('_simBase=Date.parse("2026-09-09T10:00:00Z");_rafT0=performance.now();render()');h.paint();assert.deepEqual(axes(h),forward);
});
test('frozen explicit preview stays frozen when only monotonic time advances',()=>{
  const h=fixture();h.paint();const before=axes(h);h.step(1000);assert.deepEqual(axes(h),before);
});
for(const boundary of ['2026-09-09T00:00:00Z','2026-10-01T00:00:00Z','2027-01-01T00:00:00Z'])test(boundary+' retains lifecycle identity through ordinary preview travel',()=>{
  const h=fixture('&timeScale=1');h.run('_simBase=Date.parse('+JSON.stringify(boundary)+')-38;_rafT0=0;TIMESCALE=1');const a=h.paint(),b=h.step(76);
  const population=s=>s.noise.filter(n=>n[1]===7.3).map(n=>n.slice(0,2));assert.deepEqual(population(b),population(a));assert.equal(axes(h).population,h.run('_cloudMotion.population'));
});
test('all decks advance once with coverage-independent state and equal-time idempotence',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();const before=axes(h);h.step(1000);const after=axes(h);
  for(let di=0;di<3;di++)assert.ok(Math.abs((after.life[di]-before.life[di])-(.018+di*.004))<1e-7);
  h.paint();h.paint();assert.deepEqual(axes(h),after);
});
test('new speed/heading/gust affect subsequent travel without changing accumulated axes',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();h.step(1000);const before=axes(h);
  h.run('weather.wind=9;weather.windDir=45;weather.gust=18;render()');h.paint();assert.deepEqual(axes(h),before);
  const wind=h.run('cloudState.wx*cloudState.wspd');assert.ok(wind<0);h.step(1000);const after=axes(h);
  for(let di=0;di<3;di++){const expected=((before.phase[di]-wind*(.024+di*.006))%1.25+1.25)%1.25;assert.ok(Math.abs(after.phase[di]-expected)<1e-10);}
});
test('periodic edge copies keep actual painter commands continuous at phase wrap',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');const initial=h.paint(),lowSeed=h.run('19.1+_cloudMotion.population');
  // Cross the wrapped coordinate of a real visible low-deck cell, rather than
  // merely wrapping the accumulator while every cell remains away from an edge.
  const cell=initial.noise.find(n=>n[1]===2&&n[0]>=lowSeed&&n[0]<=lowSeed+6*1.37);assert.ok(cell,'visible low-deck cell');h.ctx.__edgeCellSeed=cell[0];
  h.run('globalThis.__edgeIndex=Math.round((__edgeCellSeed-(19.1+_cloudMotion.population))/1.37);_cloudMotion.phase[0]=_cloudWrap((cloudState.wx*cloudState.wspd>0?1e-8:_CLOUD_WRAP-1e-8)-(__edgeIndex*.618+_vn3(__edgeCellSeed,2,0)),_CLOUD_WRAP);');
  const a=h.paint(),b=h.step(1);
  const ordered=s=>s.trace.map(g=>g.geometry).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const aa=ordered(a),bb=ordered(b);assert.equal(aa.length,bb.length);assert.ok(aa.length>20);
  for(let i=0;i<aa.length;i++)for(let k=0;k<6;k++)assert.ok(Math.abs(aa[i][k]-bb[i][k])<.01,'wrapped actual gradient geometry');
  assert.equal(a.columns.length,144);assert.equal(b.columns.length,144);
});
test('accelerated motion remains finite and bounded with a fixed amount of retained state',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1e12');h.paint();h.step(1000);const a=axes(h);
  assert.equal(a.phase.length,3);assert.equal(a.life.length,3);for(const x of a.phase)assert.ok(Number.isFinite(x)&&x>=0&&x<1.25);
  for(const x of [...a.life,a.wander])assert.ok(Number.isFinite(x)&&x>=0&&x<4294967296);assert.equal(h.run('_colDens.length'),144);
});
test('clear scene paints no puffs or density while its hidden decks keep evolving',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');h.paint();const before=axes(h);h.run('cloudState.covLow=cloudState.covMid=cloudState.covHigh=0');const s=h.step(1000);
  assert.equal(s.trace.length,0);assert.ok(s.columns.every(v=>v===0));assert.notDeepEqual(axes(h),before);
});
test('rain columns follow actual visible copies without granting particle permission',()=>{
  const h=fixture();assert.equal(h.run('ADVANCING'),false);h.run('cloudState.covLow=cloudState.covMid=cloudState.covHigh=1');const s=h.paint(),max=Math.max(...s.columns);assert.ok(max>=2);
  const drops=Array.from({length:20},(_,i)=>({style:{left:(i*5+2)+'%',removeProperty(k){delete this[k];}}}));h.ctx.document.querySelectorAll=selector=>selector==='.wfx .drop'?drops:[];
  h.select('.c').dataset.fx='rain';h.run('tieRainToClouds()');for(const d of drops){const col=Math.min(143,Math.floor(parseFloat(d.style.left)/100*144));assert.equal(d.style.display,s.columns[col]/max>.16?'':'none');}
  h.select('.c').dataset.fx='clear';h.run('tieRainToClouds()');assert.ok(drops.every(d=>d.style.display===undefined));
  h.run('weather.currentValidAt-=900001;render()');assert.equal(h.run('selectedWeather()'),null);assert.ok(!['rain','thunder','snow','drizzle'].includes(h.select('.c').dataset.fx));
});
console.log(JSON.stringify({sourcePath,sourceSha256:sha(fs.readFileSync(sourcePath)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'source clocks/loop/axes/painter commands; no native pixels/elapsed-motion/cost'}));process.exitCode=fail?1:0;
