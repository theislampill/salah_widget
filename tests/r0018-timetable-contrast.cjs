'use strict';
// Source-bound composition guard. Native matched screenshots remain the visual authority.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const {ROOT,BASE,sha,mutate} = require('./r0001-browser-fixture.cjs');
const source=fs.readFileSync(process.argv[2]||path.join(ROOT,'index.html'),'utf8');
const baseline=execFileSync('git',['show',`${BASE}:index.html`],{cwd:ROOT}).toString('utf8');
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
function composition(html,state,backdrop=[255,255,255]){
  const cell=rule(html,'.p'),stateRule=state==='normal'?{}:rule(html,'.p.'+state);
  const background=stateRule.background||cell.background;
  const foreground=cell.color?hex(cell.color):[240,237,248]; // measured clear-noon inherited baseline text
  const opacity=Number(stateRule.opacity||cell.opacity||1);
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
  return{state,opacity,foreground,backdrop,baseAlpha:rgba?Number(rgba[4]):0,tintAlpha,
    composedBackground,composedText,ratio:contrast(composedText,composedBackground)};
}
const results=[];
function test(name,body){try{const detail=body();results.push({name,status:'PASS',detail});}catch(error){results.push({name,status:'FAIL',error:error.message});}}
test('composition calculator positive and negative controls',()=>{assert.equal(contrast([0,0,0],[255,255,255]),21);assert.equal(contrast([255,255,255],[255,255,255]),1);});
for(const state of ['normal','past','on']) test(`${state} actual cell retains intended-color contrast on white stress backdrop`,()=>{const c=composition(source,state);assert.ok(c.ratio>=4.5,`${state}: ${c.ratio.toFixed(3)} < 4.5`);assert.equal(c.opacity,1,'Information stays at full group opacity');return c;});
test('geometry and typography declarations preserved',()=>{
  for(const selector of ['.times','.p','.p b','.tm']){
    const before=rule(baseline,selector),after=rule(source,selector);
    for(const key of ['display','justify-content','align-items','grid-template-columns','gap','padding','margin-top','border-radius','border','font-weight','font-size','line-height','letter-spacing']) assert.equal(after[key],before[key],`${selector} ${key}`);
  }
});
if(!process.argv.includes('--baseline')){
  test('past-only opacity mutant loses contrast independently',()=>{const c=composition(mutate(source,'past'),'past');assert.ok(c.ratio<4.5,`mutant unexpectedly ${c.ratio}`);return c;});
  test('next-only backing mutant loses contrast independently',()=>{const c=composition(mutate(source,'on'),'on');assert.ok(c.ratio<4.5,`mutant unexpectedly ${c.ratio}`);return c;});
}
console.log(JSON.stringify({sourceSha256:sha(source),baselineSha256:sha(baseline),limit:'Authored intended-color composition with white sky/accent bounds, no antialias/shadow/filter conformance claim. Native crops and text-free pixel pairs are required.',results},null,2));
process.exitCode=results.some(r=>r.status==='FAIL')?1:0;
