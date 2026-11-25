'use strict';
// R003F DB2 source-side check. The native producer supplies both numbers. This
// test makes no claim about the brightness of a blended or composited frame.
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const {load,root} = require('./r001d-harness.cjs');
const {nativeInlineRuntime} = require('./native-inline-runtime.cjs');

const alts = [-30,-6,-4,-3,-2.05,-2,-1.95,-1.5,-1,-0.5,0,1,2,3,4,6,10];
const fractions = [0.01,0.02,0.04,0.08,0.15,0.314,0.5,0.75,0.85,0.99];
const epoch = '2026-11-15T09:42:00Z';
function observations(sourcePath) {
  const h=load({sourcePath});
  return h.run(`(() => {
    const rows=[], date=new Date(${JSON.stringify(epoch)});
    for (const moon of ${JSON.stringify(fractions)}) for (const moonAlt of ${JSON.stringify(alts)}) {
      for (const wax of ['0','1']) {
        const m=nativeLunarSnapshot(date,28.54,-81.38,{moon,moonAlt,moonH:150,wax});
        const dark=nativeLunarPresentation(m,-27,false);
        rows.push({moon,moonAlt,wax,geometry:m.up,weight:dark.moonUp,light:dark.moonLightEligible,
          daylight:nativeLunarPresentation(m,-3,false).moonLightEligible,
          unavailable:nativeLunarPresentation(m,-27,true).moonLightEligible});
      }
    }
    return rows;
  })()`);
}
function check(row) {
  const label=JSON.stringify(row);
  assert.equal(row.geometry,row.weight,'geometry and light weight differ: '+label);
  assert.equal(row.geometry,Math.max(0,Math.min(1,(row.moonAlt+2)/6)),label);
  assert.equal(row.light,row.geometry>0&&row.moon>0.02,label);
  assert.equal(row.daylight,false,label);
  assert.equal(row.unavailable,false,label);
}
test('R003F native geometry and physical eligibility share onset at -2 degrees in both senses',()=>{
  const rows=observations(path.join(root,'index.html'));
  assert.equal(rows.length,fractions.length*alts.length*2);
  rows.forEach(check);
});
test('R003F detects a shifted display ramp with unchanged moonlight',t=>{
  const base=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const needle='const up=clamp((alt+2)/6),hd=';
  const runtime=nativeInlineRuntime(base);
  assert.equal(runtime.split(needle).length,2,'display geometry mutation must have exactly one anchor');
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-horizon-'));
  t.after(()=>fs.rmSync(temp,{recursive:true,force:true}));
  const mutant=path.join(temp,'index.html');
  fs.writeFileSync(mutant,base.replace(runtime,()=>runtime.replace(needle,'const up=clamp((alt+1)/6),hd=')));
  const row=observations(mutant).find(r=>r.moonAlt===-1.95&&r.moon===0.314&&r.wax==='1');
  assert.equal(row.light,true); assert.equal(row.geometry,0);
  assert.throws(()=>check(row),/geometry and light weight differ/);
});
