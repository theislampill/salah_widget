"use strict";
const assert=require("node:assert/strict");
const {fixture}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
function make() {
  const mutate=source=>{
    if(mutant==="arrows") {
      const start=source.indexOf('modeGroup.addEventListener("keydown"'),end=source.indexOf("\n});",start)+4;
      if(start<0||end<4)throw new Error("arrow mutant source boundary missing"); return source.slice(0,start)+source.slice(end);
    }
    return mutant==="tabindex"?source.replace("button.tabIndex=selected?0:-1;",""):source;
  };
  return fixture("builder",{ref,mutate:mutant?mutate:undefined});
}
function selected(f,mode) {
  for(const value of ["portable","local"]) {
    const button=f.elements.get("mode-"+value), want=value===mode;
    assert.equal(button.getAttribute("aria-checked"),String(want)); assert.equal(button.classList.contains("active"),want);
    assert.equal(button.tabIndex,want?0:-1);
  }
  assert.equal(f.run("embedMode"),mode);
  assert.equal(new URLSearchParams(f.hash()).get("local"),mode==="local"?"1":null);
  assert.equal(f.elements.get("pv").allow,mode==="local"?"geolocation":"");
  assert.match(f.elements.get("code").value,/width:325px;height:530px/);
}
const revision=f=>+new URL(f.elements.get("pv").src).searchParams.get("r");
const cases=[],test=(name,body)=>cases.push({name,body});
test("positive: existing click selects local output and geolocation delegation",()=>{
  const f=make(); f.click("mode-local"); assert.equal(f.run("embedMode"),"local"); assert.equal(new URLSearchParams(f.hash()).get("local"),"1");
  assert.match(f.elements.get("code").value,/allow="geolocation"/); assert.match(f.elements.get("code").value,/width:325px;height:530px/);
});
test("initial group has one selected and tabbable radio",()=>{const f=make(); selected(f,"portable");});
test("Right arrow moves focus, selected state and output once",()=>{
  const f=make(),before=revision(f); f.elements.get("mode-portable").focus(); const {event}=f.key("mode-portable","ArrowRight");
  assert.equal(event.defaultPrevented,true); assert.equal(f.document.activeElement.id,"mode-local"); selected(f,"local"); assert.equal(revision(f),before+1);
});
test("all arrows wrap within the group",()=>{
  const f=make(); for(const [id,key,mode]of [["mode-portable","ArrowLeft","local"],["mode-local","ArrowRight","portable"],["mode-portable","ArrowDown","local"],["mode-local","ArrowUp","portable"]]){
    const {event}=f.key(id,key); assert.equal(event.defaultPrevented,true); selected(f,mode); assert.equal(f.document.activeElement.id,"mode-"+mode);
  }
});
test("Tab, Enter and Space remain native without duplicate application",()=>{
  const f=make(); for(const key of ["Tab","Enter"," "]) { const before=revision(f); const {event}=f.key("mode-local",key); assert.equal(event.defaultPrevented,false); assert.equal(revision(f),before); }
  // VM does not emulate native default activation. One actual click checks the
  // application's activation owner; parent must separately press native keys.
  const before=revision(f); f.click("mode-local"); assert.equal(revision(f),before+1); selected(f,"local");
});
test("click and programmatic mode changes synchronize a single tab stop",()=>{
  const f=make(); f.click("mode-local"); selected(f,"local"); f.run('setMode("portable")'); selected(f,"portable"); f.run('setMode("local")'); selected(f,"local");
});
test("disabled controls are excluded; one and no enabled item are safe",()=>{
  const f=make(); f.elements.get("mode-portable").disabled=true; f.run('setMode("portable")'); selected(f,"local");
  f.key("mode-local","ArrowRight"); assert.equal(f.document.activeElement?.id,"mode-local"); selected(f,"local");
  f.elements.get("mode-local").disabled=true; f.run('setMode("local")');
  for(const id of ["mode-portable","mode-local"]){ assert.equal(f.elements.get(id).tabIndex,-1); assert.equal(f.elements.get(id).getAttribute("aria-checked"),"false"); }
  assert.equal(f.key("mode-local","ArrowRight").event.defaultPrevented,false);
});
test("arrow handling ignores another target inside the group",()=>{
  const f=make(),before=revision(f); f.group.dispatch("keydown",{key:"ArrowRight",target:f.elements.get("label")}); assert.equal(revision(f),before);
});
async function main(){let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}
  console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;}
main();
