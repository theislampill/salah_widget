"use strict";
const assert=require("node:assert/strict");
const {fixture,deferred,drain}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
const cases=[], denied=()=>Promise.reject(new Error("controlled clipboard denial"));
function make(options={}) {
  const mutate=source=>mutant==="success"?source.replace("if(ok){", "if(true){")
    :mutant==="install-recovery"?source.replace('$(kind+"-recovery")','$(buttonId==="install"?"code":kind+"-recovery")')
    :mutant==="stale"?source.replace("if(attempt!==state.seq) return;",""):source;
  return fixture("builder",{ref,...options,mutate:mutant?mutate:undefined});
}
const test=(name,body)=>cases.push({name,body});
const execute=async(f,id)=>{ f.elements.get(id).focus(); await Promise.all(f.click(id).results); await drain(); };
function status(f,id) { return f.elements.get(id==="copy"?"copied":"installtip").textContent; }
function verifyRecovery(f,id,payload) {
  assert.ok(!/copied|✓/i.test(status(f,id)),"false success feedback");
  assert.match(status(f,id),/couldn.t copy/i);
  const recovery=f.document.activeElement;
  assert.ok(recovery,"recovery must be focused"); assert.equal(recovery.value,payload,"manual recovery must expose captured payload");
  assert.equal(recovery.selectionStart,0); assert.equal(recovery.selectionEnd,payload.length);
  if(id==="install")assert.equal(recovery.id,"install-recovery");
}
test("positive: both primary copies succeed without fallback and restore button",async()=>{
  for(const id of ["copy","install"]) {
    const f=make(); await execute(f,id); assert.match(status(f,id),/copied/i); assert.equal(f.calls.fallback.length,0);
    assert.equal(f.elements.get(id).disabled,false); assert.equal(f.document.activeElement.id,id);
  }
});
test("positive: both denied-primary true-fallback copies report success",async()=>{
  for(const id of ["copy","install"]) {
    const f=make({clipboard:denied,fallback:()=>true}); await execute(f,id);
    assert.match(status(f,id),/copied/i); assert.equal(f.calls.fallback.length,1); assert.equal(f.calls.fallback[0].text,f.calls.copy[0]);
  }
});
test("both false or thrown fallback failures expose the exact artifact",async()=>{
  for(const fallback of [()=>false,()=>{throw new Error("controlled execCommand failure");}])for(const id of ["copy","install"]) {
    const f=make({clipboard:denied,fallback}); const canonical=f.elements.get("code").value;
    await execute(f,id); verifyRecovery(f,id,f.calls.copy[0]); assert.equal(f.elements.get("code").value,canonical);
    assert.equal(f.document.body.children.length,0,"temporary copy textarea must be removed");
  }
});
test("absent clipboard API retains true and false fallback outcomes",async()=>{
  for(const ok of [true,false])for(const id of ["copy","install"]) {
    const f=make({fallback:()=>ok}); delete f.sandbox.navigator.clipboard; await execute(f,id);
    if(ok)assert.match(status(f,id),/copied/i); else verifyRecovery(f,id,f.calls.fallback[0].text);
  }
});
test("install recovery is platform-specific exact command data",async()=>{
  const hash="lat=24.4672&lon=39.6142&label=Madinah&method=4&school=0";
  for(const platform of ["Win32","MacIntel","Linux x86_64"]) {
    const f=make({platform,clipboard:denied}); await execute(f,"install");
    const want=platform==="Win32"?`$env:SALAH_WIDGET_HASH='${hash}'; irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex`
      :`curl -fsSL https://raw.githubusercontent.com/theislampill/salah_widget/main/install.sh | SALAH_WIDGET_HASH='${hash}' bash`;
    assert.equal(f.calls.copy[0],want); verifyRecovery(f,"install",want);
  }
});
test("intentional generic install recovery does not invent carried settings",async()=>{
  const f=make({clipboard:denied});
  // R0010 makes builder selections explicit. This control deliberately supplies
  // the unchanged generic serializer input to the actual install/copy consumer.
  f.run('hash=()=>SalahConfig.serialize({}, {mode:"local"})'); await execute(f,"install");
  const want="irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex";
  assert.equal(f.calls.copy[0],want); verifyRecovery(f,"install",want);
});
test("pending embed failure preserves captured iframe when form changes",async()=>{
  const pending=deferred(),f=make({clipboard:()=>pending.promise}); const captured=f.elements.get("code").value;
  const attempt=f.click("copy").results[0]; assert.equal(f.elements.get("copy").disabled,true);
  f.input("label","Cairo"); const current=f.elements.get("code").value; assert.notEqual(current,captured);
  pending.reject(new Error("controlled denial")); await attempt; verifyRecovery(f,"copy",captured);
  assert.equal(f.document.activeElement.id,"embed-recovery"); assert.equal(f.elements.get("code").value,current);
});
test("new same-button attempt owns pending result and status timers",async()=>{
  for(const id of ["copy","install"]) {
    const first=deferred(),second=deferred(); let n=0; const f=make({clipboard:()=>n++===0?first.promise:second.promise});
    const old=f.click(id).results[0]; const latest=f.click(id).results[0];
    second.reject(new Error("controlled denial")); await latest; verifyRecovery(f,id,f.calls.copy[1]); const before=status(f,id);
    first.resolve(); await old; assert.equal(status(f,id),before); assert.equal(f.elements.get(id).disabled,false);
    await f.advance(9000); assert.equal(status(f,id),before,"manual recovery must not expire");
  }
});
test("earlier success timer cannot clear newer manual recovery",async()=>{
  for(const id of ["copy","install"]) {
    let n=0; const f=make({clipboard:()=>n++===0?Promise.resolve():denied()}); await execute(f,id); await f.advance(100);
    await execute(f,id); const before=status(f,id); await f.advance(9000); assert.equal(status(f,id),before); verifyRecovery(f,id,f.calls.copy[1]);
  }
});
test("independent buttons retain their own feedback and manual payloads",async()=>{
  const f=make({clipboard:denied}); await execute(f,"copy"); const embedStatus=status(f,"copy");
  await execute(f,"install"); assert.equal(status(f,"copy"),embedStatus); verifyRecovery(f,"install",f.calls.copy[1]);
  assert.equal(f.elements.get("code").value,f.calls.copy[0]);
});
test("hostile-looking labels stay encoded literal clipboard data",async()=>{
  const text="O'Brien \"quoted\" & Madinah\nمدينة $(echo literal) `literal`";
  const f=make({clipboard:denied}); f.input("label",text); await execute(f,"install"); const payload=f.calls.copy[0]; verifyRecovery(f,"install",payload);
  const fragment=payload.match(/SALAH_WIDGET_HASH='([^']*)'/)[1]; assert.equal(new URLSearchParams(fragment).get("label"),text);
  assert.ok(fragment.includes("%27")); assert.ok(fragment.includes("%0A"));
});
async function main(){ let failed=0; for(const c of cases){try{await c.body(); console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}
  console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0; }
main();
