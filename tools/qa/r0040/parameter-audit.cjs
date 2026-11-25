'use strict';

const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const ledger=JSON.parse(fs.readFileSync(path.join(__dirname,'parameter-ledger.json')));
function audit(params){
  const actual=JSON.parse(JSON.stringify(params));
  const expected=Object.fromEntries(ledger.map(p=>[p.name,p.value]));
  for(const name of new Set([...Object.keys(expected),...Object.keys(actual)])){
    assert.ok(Object.hasOwn(expected,name)&&Object.hasOwn(actual,name),'missing or unclassified '+name);
    assert.deepEqual(actual[name],expected[name],name+' differs from the declared study');
  }
  return {namedParameters:ledger.length,matched:Object.keys(actual).length,
    inlineResiduals:['tile alpha clamps at 0.9, near alpha at 0.92','default camera/roll, field smoothing, threshold and depth approximations require separate qualification']};
}
module.exports={audit};
