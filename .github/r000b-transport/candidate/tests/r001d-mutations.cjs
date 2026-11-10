// Mutate only an in-memory copy. Each probe still reaches the actual product consumer.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {load,makeElement,syntheticDisc,sha,root}=require('./r001d-harness.cjs');
const sourcePath=process.argv[2]||path.join(root,'index.html'),source=fs.readFileSync(sourcePath,'utf8');
function change(from,to){assert.equal(source.split(from).length,2,'mutation anchor must match once');return source.replace(from,to);}
function freshProbe(html){const h=load({source:html});h.run('render();_simBase+=60000;applyTheme(model());renderMoon();');assert.equal(h.select('.c').dataset.fx,'cloud');return h.run('qaState().moonTruth.moonSkyFresh')===false;}
function samplerProbe(html){const h=load({source:html,debugMoon:true}),cv=makeElement('canvas');cv.ctx.data=syntheticDisc().data;h.ctx.__sampleCanvas=cv;h.run('_moonCv=__sampleCanvas;renderMoon();');assert.ok(h.select('.dbgmoon').textContent.includes('MOON frac'));return /limb[^\n]*0\/255/.test(h.select('.dbgmoon').textContent);}
function boundsProbe(html){const h=load({source:html});h.ctx.__pixels=syntheticDisc().data;return h.run('sampleMoonPixel(__pixels,300,300,300,150).status')==='OOB';}
function zeroProbe(html,prop){const h=load({source:html});h.run('SIM.moon="0.01";render();');assert.equal(h.select('.c').dataset.fx,'cloud');return +(prop==='--mgo'?h.select('.mglow'):h.select('.c')).style.getPropertyValue(prop)===0;}
function appearanceProbe(html){const h=load({source:html,hash:'#lat=24.47&lon=39.61&tz=Asia%2FRiyadh&units=c&seed=1&simMoon=.5&simWax=1&simMoonAlt=20&simMoonH=42'});assert.equal(h.run('FOLLOW_WALL_CLOCK'),true);h.run('SIM.moon="1";render();');const before=h.run('JSON.stringify(_starEls.map(e=>e.style.opacity))'),positions=h.run('JSON.stringify(_starEls.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")]))');h.clock.wall+=60000;h.clock.now+=60000;h.run('SIM.moon="0.01";render();');assert.equal(h.run('JSON.stringify(_starEls.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")]))'),positions);return h.run('JSON.stringify(_starEls.map(e=>e.style.opacity))')!==before;}
const mutants=[
  ['restore not-false QA projection',change('moonSkyFresh:_lastMoonPaint?_lastMoonPaint.fresh:null','moonSkyFresh:(A.moonSkyFresh!==false)'),freshProbe],
  ['recompute freshness after consumption',change('moonSkyFresh:_lastMoonPaint?_lastMoonPaint.fresh:null','moonSkyFresh:(A.moonObservation?A.moonObservation.fresh:null)'),freshProbe],
  ['obsolete radius58',change('radius=_MR,cx=width/2','radius=58,cx=width/2'),samplerProbe],
  ['remove coordinate bounds',change('if(!Number.isInteger(x)||!Number.isInteger(y)||x<0||y<0||x>=width||y>=height)','if(false)'),boundsProbe],
  ['restore physical-zero local glow floor',change('const moonGlow=moonLightEligible?(0.03+0.24*mFrac*mFrac):0','const moonGlow=(0.03+0.24*mFrac*mFrac)'),html=>zeroProbe(html,'--mgo')],
  ['restore independent optics envelope',change('const moonLume=moonLightEligible?moonUp*darkness*clamp(0.25+0.75*mFrac):0','const moonLume=moonUp*darkness*clamp(0.25+0.75*mFrac)'),html=>zeroProbe(html,'--mhalo')],
  ['omit held-position appearance refresh',change('refreshStarAppearance(A);                                   // same consumed','/* refresh omitted */                                      // same consumed'),appearanceProbe],
];
let detected=0,failed=0;
for(const [name,mutant,probe] of mutants){
  try{assert.equal(probe(source),true,'healthy positive control failed');assert.equal(probe(mutant),false,'mutant escaped');detected++;console.log('DETECTED '+name+' mutant_sha256='+sha(Buffer.from(mutant)));}
  catch(e){failed++;console.log('FAIL '+name+' :: '+e.message);}
}
console.log(JSON.stringify({sourcePath,sourceSha256:sha(Buffer.from(source)),fixtureSha256:sha(fs.readFileSync(__filename)),detected,failed,limits:'source/VM mutations; no browser or shader beauty'}));
process.exitCode=failed?1:0;
