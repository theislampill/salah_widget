"use strict";
// Programmatic same-button reentry is deliberate: disabled buttons prevent a
// second ordinary user click while pending. No native clipboard is connected.
const assert=require("node:assert/strict"),{fixture,deferred}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
function make(options={}){return fixture("builder",{ref,...options,mutate:mutant==="fallback-owner"?source=>source.replace("copyText(payload,()=>attempt===state.seq)","copyText(payload)"):undefined});}
const cases=[],test=(name,body)=>cases.push({name,body});
test("obsolete rejection cannot fallback over the newest copied payload",async()=>{
  for(const id of ["copy","install"]) {
    const first=deferred(),second=deferred();let n=0,sink=null,f;
    f=make({clipboard:text=>(n++===0?first:second).promise.then(()=>{sink=text;}),fallback:()=>{sink=f.document.lastSelected.value;return true;}});
    const old=f.elements.get(id).onclick(); f.input("label","Cairo"); const latest=f.elements.get(id).onclick(),payload=f.calls.copy[1];
    assert.notEqual(f.calls.copy[0],payload); second.resolve(); await latest; assert.equal(sink,payload);
    first.reject(new Error("obsolete primary rejection")); await old;
    assert.equal(f.calls.fallback.length,0,"obsolete attempt must not initiate fallback"); assert.equal(sink,payload); assert.equal(f.document.activeElement.id,id);
  }
});
test("obsolete rejection cannot steal current recovery focus or selection",async()=>{
  for(const id of ["copy","install"]) {
    const first=deferred(),second=deferred();let n=0; const f=make({clipboard:()=>n++===0?first.promise:second.promise});
    const old=f.elements.get(id).onclick(); f.input("label","Cairo"); const latest=f.elements.get(id).onclick();
    second.reject(new Error("current primary rejection")); await latest;
    const recovery=f.document.activeElement,selection=f.document.lastSelected,previous=f.calls.fallback.length;
    assert.equal(recovery.id,id==="copy"?"embed-recovery":"install-recovery");
    first.reject(new Error("obsolete primary rejection")); await old;
    assert.equal(f.document.activeElement,recovery); assert.equal(f.document.lastSelected,selection); assert.equal(f.calls.fallback.length,previous);
  }
});
test("positive: current rejected primary still copies exact fallback payload",async()=>{
  for(const id of ["copy","install"]) {
    let sink=null,f; f=make({clipboard:()=>Promise.reject(new Error("current denial")),fallback:()=>{sink=f.document.lastSelected.value;return true;}});
    await f.elements.get(id).onclick(); assert.equal(f.calls.fallback.length,1); assert.equal(sink,f.calls.copy[0]);
    assert.equal(f.document.activeElement.id,id); assert.match(f.elements.get(id==="copy"?"copied":"installtip").textContent,/copied/i);
  }
});
async function main(){let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}
  console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN",reentry:"PROGRAMMATIC_DISABLED_BUTTON_BYPASS"}));process.exitCode=failed?1:0;}
main();
