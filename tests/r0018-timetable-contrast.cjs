'use strict';
// Source-bound composition guard. Native matched screenshots remain the visual authority.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {ROOT,BASE,sha} = require('./r0001-browser-fixture.cjs');
function rule(html,selector){
  const css=html.match(/<style>([\s\S]*?)<\/style>/)[1];
  const escaped=selector.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const matches=Array.from(css.matchAll(new RegExp('(?:^|\\n)'+escaped+'\\{([^}]+)\\}','g')));
  assert.equal(matches.length,1,`one actual ${selector} rule`);
  return Object.fromEntries(matches[0][1].split(';').filter(Boolean).map(d=>{const i=d.indexOf(':');return[d.slice(0,i).trim(),d.slice(i+1).trim()];}));
}
function hex(value){const m=/^#([0-9a-f]{6})$/i.exec(value);assert.ok(m,`supported local foreground ${value}`);return[0,2,4].map(i=>parseInt(m[1].slice(i,i+2),16));}
const over=(top,alpha,bottom)=>top.map((n,i)=>n*alpha+bottom[i]*(1-alpha));
function luminance(rgb){const linear=rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});return linear[0]*.2126+linear[1]*.7152+linear[2]*.0722;}
const contrast=(a,b)=>(Math.max(luminance(a),luminance(b))+.05)/(Math.min(luminance(a),luminance(b))+.05);
function composition(html,state,backdrop=[255,255,255],appearance='glass'){
  const cell=rule(html,'.p'),stateRule=state==='normal'?{}:rule(html,'.p.'+state);
  // Higher-specificity appearance rules override the normal state, then their own state rule.
  const contrastRule=appearance==='contrast'?rule(html,'.c[data-appearance="contrast"] .p'):{},contrastState=appearance==='contrast'&&state==='on'?rule(html,'.c[data-appearance="contrast"] .p.on'):{};
  const applied={...cell,...stateRule,...contrastRule,...contrastState},background=applied.background;
  const foreground=applied.color?hex(applied.color):[240,237,248]; // measured clear-noon inherited baseline text
  const opacity=Number(applied.opacity||1);
  const rgba=/,rgba\(\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\)$/.exec(background);
  let rawBackground=rgba?over(rgba.slice(1,4).map(Number),Number(rgba[4]),backdrop):backdrop;
  const gradient=background.split('),rgba(')[0];
  const hexStops=Array.from(gradient.matchAll(/#ffffff([\da-f]{2})/gi),m=>parseInt(m[1],16)/255);
  const accentStops=Array.from(gradient.matchAll(/var\(--accent\) ([\d.]+)%/g),m=>Number(m[1])/100);
  assert.ok(hexStops.length||accentStops.length,'Recognized actual decorative tint stops');
  // White is the component-wise upper bound for both sky and every possible accent.
  const tintAlpha=Math.max(...hexStops,...accentStops);
  rawBackground=over([255,255,255],tintAlpha,rawBackground);
  const composedBackground=over(rawBackground,opacity,backdrop);
  const composedText=over(foreground,opacity,backdrop);
  return{state,appearance,opacity,foreground,backdrop,baseAlpha:rgba?Number(rgba[4]):0,tintAlpha,
    composedBackground,composedText,ratio:contrast(composedText,composedBackground)};
}
function mutateTimetable(html,kind){
  if(kind==='past'){const before='.c[data-appearance="contrast"] .p{opacity:1;';assert.equal(html.split(before).length,2);return html.replace(before,'.c[data-appearance="contrast"] .p{');}
  assert.equal(kind,'on');const before=rule(html,'.c[data-appearance="contrast"] .p.on').background;
  if(rule(html,'.c[data-appearance="contrast"] .p.on').color==='#211d15'){
    // PR42 replaces translucent next-row glass with an opaque accent plate.
    // The corresponding fault is its old pale foreground, not removal of the
    // former dark backing. Keep the historical mutation for old-source controls.
    const selector='.c[data-appearance="contrast"] .p.on{color:#211d15;';
    assert.equal(html.split(selector).length,2);
    return html.replace(selector,'.c[data-appearance="contrast"] .p.on{color:#f0edf8;');
  }
  assert.equal(html.split(before).length,2,'One contrast-only next background');assert.match(before,/,rgba\(9,17,28,\.90\)$/);
  return html.replace(before,before.replace(/,rgba\(9,17,28,\.90\)$/,''));
}
function run(){
const sourcePath=process.argv.slice(2).find(arg=>!arg.startsWith('--'))||path.join(ROOT,'index.html');
const source=fs.readFileSync(sourcePath,'utf8');
const baseline=execFileSync('git',['show',`${BASE}:index.html`],{cwd:ROOT}).toString('utf8');
const results=[];
function test(name,body){try{const detail=body();results.push({name,status:'PASS',detail});}catch(error){results.push({name,status:'FAIL',error:error.message});}}
test('composition calculator positive and negative controls',()=>{assert.equal(contrast([0,0,0],[255,255,255]),21);assert.equal(contrast([255,255,255],[255,255,255]),1);});
test('glass retains original non-next state styling',()=>{for(const selector of ['.times','.p','.p.now','.p.past','.p b','.tm'])assert.deepEqual(rule(source,selector),rule(baseline,selector),selector);});
test('owner-authorized next emphasis is stronger without relabelling future rows',()=>{
  const check=html=>{const r=rule(html,'.p.on');assert.match(r.background,/var\(--accent\) 88%/);assert.equal(r.color,'#211d15');assert.match(r['box-shadow'],/inset 3px 0/);assert.equal(rule(html,'.p.on b')['font-weight'],'700');};
  check(source);assert.throws(()=>check(baseline),assert.AssertionError,'Old weak next styling is the negative control');
});
for(const state of ['normal','past','on','now'])test(`${state} retains its original glass state emphasis`,()=>{const c=composition(source,state);assert.equal(c.opacity,state==='past'?.42:1);return c;});
for(const state of ['normal','past','on']) test(`${state} opt-in contrast retains intended-color contrast on white stress backdrop`,()=>{const c=composition(source,state,[255,255,255],'contrast');assert.ok(c.ratio>=4.5,`${state}: ${c.ratio.toFixed(3)} < 4.5`);assert.equal(c.opacity,1,'Information stays at full group opacity');return c;});
test('glass default has no superseded white-stress 4.5 claim',()=>{const c=composition(source,'normal');assert.ok(c.ratio<4.5,'Control must distinguish glass from contrast');return {...c,claim:'Glass aesthetic selected by owner; prior white-stress gate applies only to contrast'};});
test('geometry and typography declarations preserved',()=>{
  for(const selector of ['.times','.p','.p b','.tm']){
    const before=rule(baseline,selector),after=rule(source,selector);
    for(const key of ['display','justify-content','align-items','grid-template-columns','gap','padding','margin-top','border-radius','border','font-weight','font-size','line-height','letter-spacing']) assert.equal(after[key],before[key],`${selector} ${key}`);
  }
});
if(!process.argv.includes('--baseline')){
  test('missing contrast opacity override exposes inactive-row attenuation',()=>{const c=composition(mutateTimetable(source,'past'),'past',[255,255,255],'contrast');assert.ok(c.ratio<4.5,`mutant unexpectedly ${c.ratio}`);assert.equal(c.opacity,.42);return c;});
  test('contrast next-only presentation mutant loses contrast independently',()=>{const c=composition(mutateTimetable(source,'on'),'on',[255,255,255],'contrast');assert.ok(c.ratio<4.5,`mutant unexpectedly ${c.ratio}`);return c;});
}
return {sourceSha256:sha(source),baselineSha256:sha(baseline),limit:'Authored intended-color composition with white sky/accent bounds, no antialias/shadow/filter conformance claim. Native crops and text-free pixel pairs are required.',results};
}
if(require.main===module){const result=run();console.log(JSON.stringify(result,null,2));process.exitCode=result.results.some(r=>r.status==='FAIL')?1:0;}
module.exports={rule,composition,mutateTimetable};
