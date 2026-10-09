const assert=require('node:assert/strict');
const fs=require('node:fs');
const {load,makeElement,syntheticDisc,sha}=require("C:\\Users\\theis\\.codex\\worktrees\\hotfix-startup-clouds\\salah_widget\\tests\\r001d-harness.cjs");
const sourcePath=process.argv[2];
let pass=0,fail=0;
function test(name,fn){try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
function fixture(opts={}){return load({sourcePath,...opts});}

test('positive actual render reaches paint and strict fresh smoke',()=>{
  const h=fixture(); h.run('render()');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),true);
  assert.equal(h.select('.c').dataset.fx,'cloud');
  assert.ok(+h.select('.c').style.getPropertyValue('--moonbeam')>0);
});
test('consumer-before-update remains stale after later producer (strict smoke fails)',()=>{
  const h=fixture(); h.run('render(); _simBase+=60000; applyTheme(model()); renderMoon(); moonSky._min=Math.floor(model().nowMin);');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false,'later geometry erased consumed stale result');
});
test('actual render-order mutant reaches paint and cannot turn stale consumption fresh',()=>{
  const base=fixture(),source=fs.readFileSync(base.sourcePath,'utf8');
  const line=source.split('\n').find(s=>s.includes('const mm=Math.floor(M.nowMin);'));
  assert.ok(line,'actual minute update line required');
  const mutant=source.replace(line+'\n','').replace('  applyTheme(M);\n  // OBSERVABILITY','  applyTheme(M);\n'+line+'\n  // OBSERVABILITY');
  assert.notEqual(mutant,source);
  const h=load({source:mutant});h.run('render();_simBase+=60000;render();');
  assert.equal(h.select('.c').dataset.fx,'cloud');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false);
  assert.equal(h.run('qaState().moonTruth.lastConsumed.fresh'),false);
  assert.equal(h.run('qaState().moonTruth.currentGeometry.fresh'),true);
});
test('pre-first observation is unavailable',()=>{
  const h=fixture(); assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),null);
});
test('failed atmosphere cannot make freshness pass',()=>{
  const h=fixture(); h.run('render(); atmosphere=()=>{throw new Error("controlled atmosphere failure")}; try{applyTheme(model())}catch(e){}');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false);
});
test('failed paint cannot retain previous successful freshness',()=>{
  const h=fixture(); h.run('render(); paint=()=>{throw new Error("controlled paint failure")}; try{applyTheme(model())}catch(e){}');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false);
});
test('same minute of day on a different date is stale at actual consume',()=>{
  const h=fixture(); h.run('render(); _simBase+=86400000; maintainPrayerDay(); applyTheme(model());');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false);
});
test('same minute in another location is stale at actual consume',()=>{
  const h=fixture(); h.run('render(); lat=51.5; lon=-0.12; applyTheme(model());');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),false);
});
test('direct producer owns its stamp after replacing geometry',()=>{
  const h=fixture(); h.run('render(); renderMoon(); applyTheme(model());');
  assert.equal(h.run('qaState().moonTruth.moonSkyFresh===true'),true);
});
test('omitted update captures stale identities and a bounded consumption warning',()=>{
  const h=fixture(); h.run('render(); _simBase+=60000; applyTheme(model()); applyTheme(model());');
  const q=h.run('qaState().moonTruth');
  assert.equal(q.moonSkyFresh,false);
  assert.equal(q.lastConsumed.status,'completed');
  assert.equal(q.lastConsumed.observation.produced.epochMinute,29814900);
  assert.equal(q.lastConsumed.observation.expected.epochMinute,29814901);
  assert.equal(h.warnings.length,1);
});
test('empty atmosphere and failures name the actually reached stage',()=>{
  for(const [override,stage] of [['atmosphere=()=>({})','paint'],['atmosphere=()=>{throw new Error("atmosphere")}', 'atmosphere'],['paint=()=>{throw new Error("paint")}', 'paint']]){
    const h=fixture();h.run('render();'+override+';try{applyTheme(model())}catch(e){}');
    const q=h.run('qaState().moonTruth');
    assert.equal(q.moonSkyFresh,null);assert.equal(q.lastConsumed.status,'failed');assert.equal(q.lastConsumed.stage,stage);
  }
});
test('same-minute geometry reuse is fresh with unchanged producer identity',()=>{
  const h=fixture();h.run('render();const originalMoon=moonSky;render();');
  assert.equal(h.run('moonSky===originalMoon'),true);assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
  assert.equal(h.warnings.length,0);
});
test('failed geometry does not advance lastMoonMin',()=>{
  const h=fixture();h.run('render();_simBase+=60000;const mmBefore=lastMoonMin;moonAltAz=()=>{throw new Error("geometry")};SIM.moonAlt=null;try{render()}catch(e){}');
  assert.equal(h.run('lastMoonMin===mmBefore'),true);
});
test('consumed diagnostic and nested identities are immutable',()=>{
  const h=fixture();h.run('render()');
  assert.equal(h.run('Object.isFrozen(_lastMoonPaint)&&Object.isFrozen(_lastMoonPaint.observation)&&Object.isFrozen(_lastMoonPaint.observation.produced)&&Object.isFrozen(_lastMoonPaint.observation.expected)&&Object.isFrozen(_lastMoonPaint.observation.light)'),true);
});
test('actual debug readout distinguishes dark opaque limb and canvas exterior',()=>{
  const h=fixture({debugMoon:true}),disc=syntheticDisc(),cv=makeElement('canvas'); cv.ctx.data=disc.data;
  h.ctx.__sampleCanvas=cv; h.run('SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas; renderMoon();');
  const read=h.select('.dbgmoon').textContent;
  assert.match(read,/limb[^\n]*0\/255/);
  assert.match(read,/canvas exterior[^\n]*0\/0/);
});
test('bright-disc positive debug readout is not hardcoded dark',()=>{
  const h=fixture({debugMoon:true}),cv=makeElement('canvas'); cv.ctx.data=syntheticDisc(true).data;
  h.ctx.__sampleCanvas=cv; h.run('SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas; renderMoon();');
  assert.match(h.select('.dbgmoon').textContent,/limb[^\n]*255\/255/);
});
test('sampler coordinates and geometry use actual dimensions/shared radius',()=>{
  const h=fixture(),cv=makeElement('canvas');cv.ctx.data=syntheticDisc().data;h.ctx.__sampleCanvas=cv;h.run('SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas');
  const p=h.run('moonDebugSamples()');assert.equal(p.width,300);assert.equal(p.height,300);assert.equal(p.radius,144);
  assert.deepEqual(Array.from(p.samples,s=>[s.label,s.x,s.y,s.status,s.lum,s.alpha]),[
    ['inner',222,150,'ok',255,255],['limb',293,150,'ok',0,255],['edge',294,150,'ok',0,255],
    ['disc exterior',295,150,'ok',0,0],['canvas exterior',299,150,'ok',0,0]]);
});
test('coordinate bounds reject row wrapping, negative coordinates and y=height',()=>{
  const h=fixture();h.ctx.__pixels=syntheticDisc().data;
  for(const [x,y] of [[300,150],[-1,150],[150,-1],[150,300],[1.5,150]]){
    h.ctx.__x=x;h.ctx.__y=y;const p=h.run('sampleMoonPixel(__pixels,300,300,__x,__y)');assert.equal(p.status,'OOB');assert.equal(p.alpha,null);
  }
  assert.equal(h.run('sampleMoonPixel(null,300,300,222,150).status'),'unavailable');
});
test('absent/empty/throwing image read is explicitly unavailable',()=>{
  for(const kind of ['absent','context','empty','error']){
    const h=fixture(),cv=makeElement('canvas');
    if(kind==='context')cv.getContext=()=>null;
    if(kind==='empty')cv.ctx.data=new Uint8ClampedArray(0);
    if(kind==='error')cv.ctx.error=true;
    h.ctx.__sampleCanvas=kind==='absent'?null:cv;h.run('SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas');assert.equal(h.run('moonDebugSamples().status'),'unavailable');
  }
});
test('cropped backing canvas does not relabel an interior pixel as exterior',()=>{
  const h=fixture(),cv=makeElement('canvas');cv.width=200;cv.height=200;h.ctx.__sampleCanvas=cv;h.run('SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas');
  assert.equal(h.run('moonDebugSamples().samples.find(p=>p.label==="canvas exterior").status'),'unavailable');
});
test('PBR cache preserves reuse threshold and storage without texture changes',()=>{
  const h=fixture();h.run('_mAlb=new Uint8ClampedArray(_MTW*_MTH*4).fill(150);_mNrm=new Uint8ClampedArray(_MTW*_MTH*4).fill(128);_pbrReady=true;renderMoonPBR(.5,true);const pbrCv=_moonCv,pbrOut=_moonOut;const pbrPuts=_moonCtx.puts;renderMoonPBR(.501,true);');
  assert.equal(h.run('_moonCtx.puts===pbrPuts && _moonCv===pbrCv && _moonOut===pbrOut'),true);
  h.run('renderMoonPBR(.506,true)');assert.equal(h.run('_moonCtx.puts===pbrPuts+1 && _moonCv===pbrCv && _moonOut===pbrOut'),true);
});
const h=fixture();
console.log(JSON.stringify({sourcePath:h.sourcePath,sourceSha256:h.sourceHash,fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'VM boundaries; no native compositor/texture/motion/cost proof'}));
process.exitCode=fail?1:0;
