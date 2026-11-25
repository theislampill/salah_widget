'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),
  os=require('node:os'),zlib=require('node:zlib'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
test('R0040 gated authored variants agree across lanes and withdraw on the expiry frame',()=>{
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'r0040-options-'));
  try{
    const source=path.join(tmp,'src/native/index.html');
    fs.mkdirSync(path.dirname(source),{recursive:true});
    fs.copyFileSync(path.join(root,'src/native/index.html'),source);
    const patch=zlib.gunzipSync(fs.readFileSync(path.join(root,'docs/state-contracts/evidence/R0040/phase1-options.patch.gz')));
    execFileSync('git',['apply','--whitespace=error','-'],{cwd:tmp,input:patch});
    const text=execFileSync(process.execPath,[path.join(root,'tools/qa/r0040/evaluate-options.cjs'),source],{encoding:'utf8'});
    const result=JSON.parse(text);
    assert.equal(result.policies.length,4);
    assert.equal(result.physical.length,2);
    assert.equal(result.expiry.length,2);
    assert.equal(result.ordinalMutantRejected,true);
  }finally{fs.rmSync(tmp,{recursive:true,force:true});}
});
