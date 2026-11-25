'use strict';
// R0041 (issue 143) row R41-CEN: census of the mismatch intervals by whole-minute replay of the product's own
// ephemeris (moonIllum, src/native/index.html, extracted read-only as moon/tests/r0041-direction.test.cjs does).
// A whole-minute step t is WRONG-WAY when the phase angle alpha = acos(2f - 1) moves against the sense the waxing flag
// implies: sign(alpha(t) - alpha(t - 1 min)) != (waxing(t) ? -1 : +1). Contiguous wrong-way steps form an interval.
// Year: 525,600 whole-minute steps from 2026-11-16T00:00Z (issue 143 C.1, method 2).
// Expected (issue 143 C.1): 25 intervals, 2,953 wrong-way steps, each 1-261 min, including 24 Nov 15:55-17:35 Z,
// 8 Dec 23:18-23:57 Z, 24 Dec 01:17-01:45 Z and 7 Jan 2027 19:04-20:29 Z (edges within 1 min).
// Discriminator: the seeded flag inversion (waxing negated) yields 525,600 - 2,953 wrong-way steps.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../../src/native/index.html'),'utf8');
const s0=html.indexOf('const _RAD=Math.PI/180'),s1=html.indexOf('// Galactic centre',s0);
const eph={Math,Date};vm.createContext(eph);vm.runInContext(html.slice(s0,s1)+';this.moonIllum=moonIllum;',eph);
const START=Date.parse('2026-11-16T00:00:00Z'),STEPS=525600;
function census(invert=false){
  const alpha=f=>Math.acos(Math.max(-1,Math.min(1,2*f-1)));
  let prev=alpha(eph.moonIllum(new Date(START-60000)).fraction),wrong=0;const intervals=[];let open=null;
  for(let k=0;k<STEPS;k++){const t=START+k*60000,il=eph.moonIllum(new Date(t)),a=alpha(il.fraction),waxing=invert?!il.waxing:il.waxing;
    const bad=Math.sign(a-prev)!==(waxing?-1:1);prev=a;
    if(bad){wrong++;if(!open)open={from:t,to:t,steps:0};open.to=t;open.steps++;}else if(open){intervals.push(open);open=null;}}
  if(open)intervals.push(open);
  return {wrong,intervals};
}
const iso=t=>new Date(t).toISOString().slice(0,16)+'Z';
test('R41-CEN: 25 intervals and 2,953 wrong-way whole-minute steps over the year from 2026-11-16',t=>{
  const c=census();
  assert.equal(c.intervals.length,25,'intervals: '+c.intervals.map(i=>iso(i.from)+'..'+iso(i.to)).join(', '));
  assert.equal(c.wrong,2953);
  for(const i of c.intervals){assert.ok(i.steps>=1&&i.steps<=261,`interval ${iso(i.from)} has ${i.steps} steps`);}
  // named intervals of issue 143 C.1 (first and last wrong-way minute, within 1 min)
  for(const [a,b] of [['2026-11-24T15:55Z','2026-11-24T17:35Z'],['2026-12-08T23:18Z','2026-12-08T23:57Z'],['2026-12-24T01:17Z','2026-12-24T01:45Z'],['2027-01-07T19:04Z','2027-01-07T20:29Z']]){
    const A=Date.parse(a),B=Date.parse(b),hit=c.intervals.find(i=>Math.abs(i.from-A)<=60000);
    assert.ok(hit,`no interval starting within 1 min of ${a}`);assert.ok(Math.abs(hit.to-B)<=60000,`interval from ${a} ends ${iso(hit.to)}, expected ${b} within 1 min`);}
  t.diagnostic(JSON.stringify(c.intervals.map(i=>[iso(i.from),iso(i.to),i.steps])));
});
test('R41-CEN discriminator: a seeded waxing-flag inversion yields 525,600 - 2,953 wrong-way steps',()=>{
  assert.equal(census(true).wrong,STEPS-2953);
});
