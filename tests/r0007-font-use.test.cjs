'use strict';
// Construction controls only: no browser, provider, server or product mutation.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {instrument,preload,observerHook}=require('./rlgwo/prayer-browser-fixture.cjs');
const source=fs.readFileSync(path.join(__dirname,'../src/native/index.html'),'utf8');
const original=JSON.parse(fs.readFileSync(path.join(__dirname,'rlgwo/R0007-next-event-recipes.json'),'utf8'));
const baseline=original.cases.find(c=>c.caseId==='NE07-fall24');
const spec={...baseline,caseId:'NE07-font-fallback-fall24',variant:'font-fallback'};
const edits=[['--font-body:"Inter",','--font-body:'],['--font-display:"Fraunces",','--font-display:']];

test('font-use control changes only the optional families in the existing stacks',()=>{
 let expected=source.replace(/\r\n/g,'\n');
 for(const [from,to] of edits) expected=expected.replace(from,to);
 expected=expected.replace('<head>','<head><script>'+preload(spec)+'</script>')
   .replace('\nboot();',observerHook()+'\nboot();');
 const actual=instrument(source,spec);
 assert.equal(actual,expected);
 assert.ok(actual.includes('--font-body:system-ui,-apple-system,"Segoe UI",sans-serif;'));
 assert.ok(actual.includes('--font-display:Georgia,"Times New Roman",serif;'));
 assert.equal((actual.match(/https:\/\/fonts\.googleapis\.com\/css2[^\"]*/g)||[])[0],
   (source.match(/https:\/\/fonts\.googleapis\.com\/css2[^\"]*/g)||[])[0]);
 // The date dialog now follows the same gated custom properties as the card.
 assert.ok(actual.includes('font-family:var(--font-body);overflow-y:auto'));
 assert.ok(actual.includes('.date-dialog h2{margin:0;font-family:var(--font-display);'));
});

test('missing or duplicated font anchors refuse the disposable intervention',()=>{
 for(const [from] of edits){
  assert.throws(()=>instrument(source.replace(from,''),spec),/exact variant anchor drift: font-fallback/);
  assert.throws(()=>instrument(source+from,spec),/exact variant anchor drift: font-fallback/);
 }
});

test('ordinary case retains both optional font families and the unchanged input object',()=>{
 const before=JSON.stringify(baseline),document=instrument(source,baseline);
 for(const [from] of edits) assert.ok(document.includes(from));
 assert.equal(JSON.stringify(baseline),before);
 assert.equal(baseline.expectedFailure,false);
 assert.equal(baseline.orderedActions.some(a=>a.awaitResult),false);
});
