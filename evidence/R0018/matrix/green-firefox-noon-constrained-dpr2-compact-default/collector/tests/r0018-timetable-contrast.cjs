'use strict';
// Source-bound composition guard. Native matched screenshots remain the visual authority.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {ROOT,sha} = require('./r0001-browser-fixture.cjs');
const BASE='ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d';
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
  // White-sky and white-accent stress control. Native pairs qualify actual state accents.
  const tintAlpha=Math.max(...hexStops,...accentStops);
  rawBackground=over([255,255,255],tintAlpha,rawBackground);
  const composedBackground=over(rawBackground,opacity,backdrop);
  const composedText=over(foreground,opacity,backdrop);
  return{state,appearance,opacity,foreground,backdrop,baseAlpha:rgba?Number(rgba[4]):0,tintAlpha,
    composedBackground,composedText,ratio:contrast(composedText,composedBackground)};
}
function mutateTimetable(html,kind){
  if(kind==='default-past'){
    const before='.p.past{';assert.equal(html.split(before).length,2);
    return html.replace(before,before+'opacity:.42;');
  }
  if(kind==='default-base'){
    for(const selector of ['.p','.p.past']){
      const before=rule(html,selector).background;
      assert.match(before,/,rgba\(9,17,28,\.[0-9]+\)$/);
      const declaration=selector+'{',start=html.indexOf(declaration),end=html.indexOf('}',start);
      assert.ok(start>=0&&end>start,'Unique actual cell rule');
      html=html.slice(0,start)+html.slice(start,end).replace(before,before.replace(/,rgba\(9,17,28,\.[0-9]+\)$/,''))+html.slice(end);
    }
    return html;
  }
  if(kind==='default-on'){
    const before=rule(html,'.p.on').color;assert.equal(before,'#211d15');
    const start=html.indexOf('.p.on{'),end=html.indexOf('}',start);
    return html.slice(0,start)+html.slice(start,end).replace('color:'+before+';','color:#f0edf8;')+html.slice(end);
  }
  if(kind==='past'){const before='.c[data-appearance="contrast"] .p{opacity:1;';assert.equal(html.split(before).length,2);return mutateTimetable(html,'default-past').replace(before,'.c[data-appearance="contrast"] .p{');}
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
const args=process.argv.slice(2),baselineIndex=args.indexOf('--baseline-file');
const sourcePath=args[0]&&!args[0].startsWith('--')?args[0]:path.join(ROOT,'index.html');
const source=fs.readFileSync(sourcePath,'utf8');
const baseline=baselineIndex>=0?fs.readFileSync(args[baselineIndex+1],'utf8'):execFileSync('git',['show',BASE+':index.html'],{cwd:ROOT}).toString('utf8');
assert.equal(sha(baseline),'d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f','Exact delivered baseline entry');
const results=[];
function test(name,body){try{const detail=body();results.push({name,status:'PASS',detail});}catch(error){results.push({name,status:'FAIL',error:error.message});}}
test('composition calculator positive and negative controls',()=>{assert.equal(contrast([0,0,0],[255,255,255]),21);assert.equal(contrast([255,255,255],[255,255,255]),1);});
test('approved next and current emphasis remains unchanged',()=>{
  for(const selector of ['.p.on','.p.on b','.p.on b,.p.on .tm','.p.now'])assert.deepEqual(rule(source,selector),rule(baseline,selector),selector);
  const r=rule(source,'.p.on');assert.match(r.background,/var\(--accent\) 88%/);assert.equal(r.color,'#211d15');assert.match(r['box-shadow'],/inset 3px 0/);assert.equal(rule(source,'.p.on b')['font-weight'],'700');
});
for(const appearance of ['glass','contrast'])for(const state of ['normal','past','on','now'])test(appearance+' '+state+' full information opacity and intended-color contrast on white stress',()=>{
  const c=composition(source,state,[255,255,255],appearance);assert.equal(c.opacity,1,'Information stays at full group opacity');assert.ok(c.ratio>=4.5,state+': '+c.ratio.toFixed(3)+' < 4.5');return c;
});
test('elapsed rows are subdued by decoration while text remains unchanged',()=>{
  const normal=composition(source,'normal'),past=composition(source,'past');
  assert.deepEqual(past.foreground,normal.foreground);assert.equal(past.opacity,1);assert.ok(past.tintAlpha<normal.tintAlpha);assert.equal(rule(source,'.p.past')['border-color'],'#ffffff20');
  return{normal,past};
});
test('geometry and typography declarations preserved',()=>{
  for(const selector of ['.times','.p','.p b','.tm']){
    const before=rule(baseline,selector),after=rule(source,selector);
    for(const key of ['display','justify-content','align-items','grid-template-columns','gap','padding','margin-top','border-radius','border','font-weight','font-size','line-height','letter-spacing']) assert.equal(after[key],before[key],selector+' '+key);
  }
});
if(!args.includes('--baseline')){
  for(const [kind,state] of [['default-past','past'],['default-base','normal'],['default-on','on']])test(kind+' independent loss control reaches contrast oracle',()=>{
    const c=composition(mutateTimetable(source,kind),state);
    assert.ok(c.ratio<4.5,'mutant unexpectedly '+c.ratio);if(kind==='default-past')assert.equal(c.opacity,.42);return c;
  });
}
return {sourceSha256:sha(source),baselineSha256:sha(baseline),baselineCommit:BASE,limit:'Authored intended-color composition with white sky/accent stress, no antialias/shadow/filter conformance claim. Native crops and text-free pixel pairs are required.',results};
}
if(require.main===module){const result=run();console.log(JSON.stringify(result,null,2));process.exitCode=result.results.some(r=>r.status==='FAIL')?1:0;}
module.exports={rule,composition,mutateTimetable};
