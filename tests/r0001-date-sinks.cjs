'use strict';
// Runs the complete checked-out runtime and real config module, then its actual render().
// Recording DOM checks raw sink markup; the companion browser fixture checks nodes/events.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { ROOT, CLOCK, CANARY, HASH, prayer, mutate, sha } = require('./r0001-browser-fixture.cjs');
const html = fs.readFileSync(process.argv[2] || path.join(ROOT,'index.html'),'utf8');
const config = fs.readFileSync(path.join(ROOT,'config.js'),'utf8');
function run({source=html, format='YYYY-MM-DD', saved=false, month=false, preview=false, time='12:30', stale=false, missing=false}={}) {
  const nodes = new Map();
  const node = selector => {
    if (!nodes.has(selector)) nodes.set(selector,{innerHTML:'',textContent:'',style:{setProperty(){}},dataset:{}});
    return nodes.get(selector);
  };
  const store = new Map();
  if(saved) store.set('salah_widget:config:v1',JSON.stringify({v:1,lat:24.47,lon:39.61,tz:'Asia/Riyadh',label:'Madinah',method:'4',school:'0',time:'24',datefmt:format,units:'f',lp:0,source:'manual',savedAt:Date.parse(CLOCK)}));
  class FixedDate extends Date { constructor(...args) { super(...(args.length ? args : [Date.parse(CLOCK)])); } static now(){return Date.parse(CLOCK);} }
  const context = vm.createContext({Date:FixedDate,Intl,URLSearchParams,URL,console,performance:{now:()=>0},
    location:{hash:(saved?'#local=1&tz=Asia%2FRiyadh&simTime='+time:HASH.replace('simTime=12:30','simTime='+time)+'&datefmt='+encodeURIComponent(format))},
    localStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)},
    document:{querySelector:node,getElementById:id=>node('#'+id)},Image:class {},
    setTimeout(){throw new Error('Unexpected timer in admitted-state source control');},clearTimeout(){},
    fetch(){throw new Error('Unexpected network in admitted-state source control');}});
  context.window=context;
  vm.runInContext(config,context,{filename:'config.js'});
  const scripts=Array.from(source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g),m=>m[1]).filter(s=>s.trim());
  assert.equal(scripts.length,1,'Expected the real inline runtime');
  assert.equal(scripts[0].split('\nboot();').length,2,'Expected the real boot caller to suspend only async boot');
  vm.runInContext(scripts[0].replace('\nboot();','\n// admitted-state fixture suspends only boot'),context,{filename:'index.html:inline'});
  const today=prayer('07',month), tomorrow=prayer('08',month);
  if(preview) tomorrow.date.hijri.day=CANARY;
  if(missing){delete today.date;delete tomorrow.date;}
  vm.runInContext(`
    // Art/layout are unrelated to the three recording DOM sinks. Keep model/formatter/render real.
    syncWeather=()=>{}; renderMoon=()=>{}; projectStars=()=>{};
    drawArc=()=>''; fitCn=()=>{}; applyTheme=()=>{};
    today=${JSON.stringify(today)}; tomorrow=${JSON.stringify(tomorrow)};
    _prayerStale=${stale};
    render();
  `,context,{filename:'test-only-admitted-state'});
  assert.equal((node('.times').innerHTML.match(/class="p /g)||[]).length,6,'The actual timetable rendered');
  assert.equal(node('.cn').textContent,time==='19:00'?'Maghrib':'Dhuhr','Actual model() selected the expected current prayer');
  assert.ok(node('.nt').textContent,'A non-empty next-prayer time rendered');
  return {ce:node('#ce').innerHTML,ah:node('#ah').innerHTML,times:node('.times').innerHTML,
    configSource:vm.runInContext('CONFIG.source',context),fmt:value=>vm.runInContext(`fmtDate(${JSON.stringify(value)})`,context)};
}
function safe(output,field) {
  assert.doesNotMatch(output[field],/<(?:svg|img|script)(?:\s|>)/i,`${field} must not receive a raw injected node`);
  assert.match(output[field],/&lt;svg onload=&quot;window\.__sw_sec_probe=1&quot;&gt;&lt;\/svg&gt;/,`${field} retains the hostile text exactly once encoded`);
}
const results=[];
function test(name,body) {try{body();results.push({name,status:'PASS'});}catch(error){results.push({name,status:'FAIL',error:error.message});}}
test('ordinary actual renderer positive',()=>{const o=run();assert.equal(o.ce,'2026-09-07<span class="er">CE</span>');assert.match(o.ah,/^<span class="er">ه<\/span>1448-03-25 <span class="mph pre">\| .+ 26<\/span>$/);});
test('hash format reaches both sinks inert',()=>{const o=run({format:CANARY});safe(o,'ce');safe(o,'ah');assert.equal(o.configSource,'hash');});
test('saved format reaches both sinks inert',()=>{const o=run({format:CANARY,saved:true});safe(o,'ce');safe(o,'ah');assert.equal(o.configSource,'localStorage');});
test('provider months reach both sinks inert',()=>{const o=run({format:'DD MMMM YYYY',month:true});safe(o,'ce');safe(o,'ah');});
test('admitted preview day reaches its own sink inert',()=>{const o=run({preview:true});assert.match(o.ah,/class="mph pre"/);safe(o,'ah');});
test('after Maghrib selects tomorrow AH without preview',()=>{const o=run({format:'DD MMMM YYYY',month:true,time:'19:00'});safe(o,'ce');safe(o,'ah');assert.match(o.ah,/>ه<\/span>26 /);assert.doesNotMatch(o.ah,/mph pre/);});
test('ordinary held-out tokens stay plain text',()=>{const o=run({format:'YYYY YY MMMM MMM MM M DD D'});assert.equal(o.fmt({year:'1448',month:{number:2,en:'Safar'},day:'19'}),'1448 48 Safar Saf 02 2 19 19');assert.equal(o.fmt(null),'');});
test('Arabic quotes ampersand angle literals encode exactly once',()=>{const o=run({format:'التاريخ "\' & < > YYYY'});assert.equal(o.ce,'التاريخ &quot;&#39; &amp; &lt; &gt; 2026<span class="er">CE</span>');assert.doesNotMatch(o.ce,/&amp;(?:lt|gt|amp|quot);/);});
test('stale markup remains trusted alongside inert text',()=>{const o=run({format:CANARY,stale:true});safe(o,'ah');assert.match(o.ah,/class="staletag"/);assert.match(o.ah,/>stale<\/span>/);});
test('missing dates preserve existing unavailable output',()=>{const o=run({missing:true});assert.equal(o.ce,'');assert.equal(o.ah,'');});
for(const field of (process.argv.includes('--baseline') ? [] : ['ce','ah','preview'])) test(`${field}-only encoding mutant is detected`,()=>{
  const source=mutate(html,field);
  const o=run({source,format:field==='preview'?'YYYY-MM-DD':CANARY,preview:field==='preview'});
  assert.throws(()=>safe(o,field==='ce'?'ce':'ah'),assert.AssertionError,'Corresponding through-sink guard must reject its own mutant');
  assert.match(o[field==='ce'?'ce':'ah'],/<svg onload=/,'Mutant reached a non-empty actual sink');
  if(field==='ce') safe(o,'ah');
  if(field==='ah') safe(o,'ce');
});
console.log(JSON.stringify({sourceSha256:sha(html),configSha256:sha(config),fixtureClock:CLOCK,environment:'Node VM + recording DOM; actual config/model/render; art callbacks suspended; browser not implied',results},null,2));
process.exitCode=results.some(r=>r.status==='FAIL')?1:0;
