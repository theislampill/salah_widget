"use strict";
// R000F preview-publication scenarios over the actual GENERATED builder.html + config.js, run through the
// r000f-fixture.cjs VM doubles (no network, no clipboard sink). A src-assignment ledger is injected after the
// script's "use strict" directive; it counts iframe src ASSIGNMENTS (issued navigations) only. It is schedule
// evidence, not native frame navigation and never widget load/readiness evidence.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {fixture,deferred,drain}=require("./r000f-fixture.cjs");
const root=path.resolve(__dirname,"..");
const STRICT='"use strict";';
const LEDGER='(function(){var pv=document.getElementById("pv"),cur="";window.__pvLedger=[];window.__pvThrow=0;'+
  'Object.defineProperty(pv,"src",{configurable:true,get:function(){return cur;},set:function(v){'+
  'if(window.__pvThrow>0){window.__pvThrow--;throw new Error("controlled src assignment failure");}'+
  'cur=String(v);window.__pvLedger.push({src:cur,allow:pv.allow});}});})();';
// `mutate` is an in-memory source replacement (mutation controls); nothing is written to disk.
function loader(mutate) {
  return (options={})=>{
    const f=fixture("builder",{...options,mutate:source=>{
      const s=mutate?mutate(source):source;
      if(!s.startsWith(STRICT))throw new Error("setup: builder script no longer starts with the strict directive");
      return STRICT+LEDGER+s.slice(STRICT.length);
    }});
    f.opens=[]; f.sandbox.open=(...args)=>{ f.opens.push(args); return null; };
    return f;
  };
}
const ledger=f=>[...f.sandbox.__pvLedger];             // copied into this realm (deepEqual-safe)
const navs=f=>ledger(f).length;
const last=f=>ledger(f)[ledger(f).length-1];
const srcHash=src=>new URL(src).hash.slice(1);
const srcRev=src=>+new URL(src).searchParams.get("r");
const param=(h,key)=>new URLSearchParams(h).get(key);
// One committed edit: the browser fires input (per keystroke) and change (on commit) with the same value.
function pair(f,id,value){ f.input(id,value,"input"); f.elements.get(id).dispatch("change"); }
function installHash(f){ const m=f.run("installCmd().cmd").match(/SALAH_WIDGET_HASH='([^']*)'/); return m?m[1]:null; }
function issued(f){ return f.run("typeof issued==='undefined'?null:issued"); }
// Snippet, install command, iframe and the issued record all describe the same canonical output.
function coherent(f){
  const h=f.hash(), local=param(h,"local")==="1", rec=last(f);
  assert.equal(f.elements.get("pv").src,rec.src,"iframe src is the last assignment");
  assert.equal(srcHash(rec.src),h,"iframe fragment equals the embed snippet output");
  assert.equal(installHash(f),h==="local=1"?null:h,"install command carries the same output");
  assert.equal(rec.allow,local?"geolocation":"","permission policy assigned with the navigation");
  assert.equal(/allow="geolocation"/.test(f.elements.get("code").value),local,"snippet permission matches mode");
}
const S={};
// ES0F-01: exactly one initial navigation; an initial coarse result with equal coordinates adds none.
S.initial=async mk=>{
  const f=mk(); assert.equal(navs(f),1,"one initial navigation"); assert.equal(srcRev(last(f).src),0); coherent(f);
  await f.resolve("coarse",0,{ok:true,cfg:{lat:24.4672,lon:39.6142,label:"Madinah",method:"4",source:"coarse"}});
  assert.match(f.elements.get("geotip").textContent,/^Detected:/,"draft feedback updated");
  assert.equal(f.elements.get("lat").value,"24.46720");
  assert.equal(navs(f),1,"equal-coordinate coarse result issues no navigation");
};
// ES0F-01/02/04: input+change pairs with unchanged values issue nothing and consume no revision.
S.inputChangePair=async mk=>{
  const f=mk();
  for(const id of ["label","lat","lon","method","school","time","units","appearance"])pair(f,id,f.elements.get(id).value);
  assert.equal(navs(f),1,"equivalent input/change pairs issue no navigation");
  pair(f,"method","2");
  assert.equal(navs(f),2,"a real change issues exactly one navigation");
  assert.equal(srcRev(last(f).src),1,"equivalent events did not consume a revision");
  assert.equal(param(srcHash(last(f).src),"method"),"2"); coherent(f);
};
// ES0F-02: each actual change → exactly one navigation with the correct output.
S.changedOnce=async mk=>{
  const f=mk();
  for(const [id,value,key,want]of [["method","2","method","2"],["units","c","units","c"],["lat","21.5","lat","21.5"],["label","Makkah","label","Makkah"]]) {
    const before=navs(f); pair(f,id,value);
    assert.equal(navs(f),before+1,id+" change issues exactly one navigation");
    assert.equal(param(srcHash(last(f).src),key),want); coherent(f);
  }
};
// ES0F-05: canonically equivalent spellings never restart; a target change does.
S.equivalentSpellings=async mk=>{
  const f=mk();
  pair(f,"lat","24.46720"); pair(f,"lat"," 24.4672 "); pair(f,"lon","39.61420");
  f.input("dfcode","YYYY-MM-DD ","input"); pair(f,"datefmt","YYYY-MM-DD"); pair(f,"method","4");
  assert.equal(navs(f),1,"equivalent raw values issue no navigation");
  pair(f,"lat","24.5"); assert.equal(navs(f),2,"coordinate change issues one navigation"); coherent(f);
};
// ES0F-03 / D2: local mode omits location fields, so their edits are not output changes; switches publish once.
S.localMode=async mk=>{
  const f=mk();
  f.click("mode-local"); assert.equal(navs(f),2,"switch to local issues one navigation");
  assert.equal(param(srcHash(last(f).src),"local"),"1"); coherent(f);
  pair(f,"label","Cairo"); pair(f,"lat","30.04"); pair(f,"lon","31.24");
  assert.equal(navs(f),2,"local-mode location edits issue no navigation"); coherent(f);
  f.click("mode-local"); assert.equal(navs(f),2,"re-selecting the active mode issues no navigation");
  f.click("mode-portable"); assert.equal(navs(f),3,"switch to portable issues one navigation");
  assert.equal(param(srcHash(last(f).src),"lat"),"30.04"); coherent(f);
  f.elements.get("mode-portable").focus(); f.key("mode-portable","ArrowRight");
  assert.equal(navs(f),4,"arrow switch issues one navigation"); coherent(f);
};
// ES0F-10 (VM part): radio Enter/Space keydowns are left to native activation (the click); one click = one
// publication. Native Enter/Space default activation itself is only observable in a browser (native driver).
S.radioKeys=async mk=>{
  const f=mk();
  for(const id of ["mode-local","mode-portable"])for(const key of ["Enter"," "]) {
    const {event}=f.key(id,key); assert.equal(event.defaultPrevented,false,"native activation not prevented");
    assert.equal(navs(f),1,"keydown alone issues no publication ("+id+" "+JSON.stringify(key)+")");
  }
  f.click("mode-local"); assert.equal(navs(f),2,"one activation, one publication"); coherent(f);
};
// Rapid typing: navigations only for distinct outputs, in order; the final preview equals the final draft.
S.rapid=async mk=>{
  const f=mk();
  for(const v of ["2","21","21.","21.5"])f.input("lat",v,"input");
  f.elements.get("lat").dispatch("change");
  assert.deepEqual(ledger(f).slice(1).map(x=>param(srcHash(x.src),"lat")),["2","21","21.5"],"one navigation per distinct output");
  assert.deepEqual(ledger(f).map(x=>srcRev(x.src)),[0,1,2,3],"revisions are consecutive");
  assert.equal(srcHash(last(f).src),f.hash(),"final preview equals final draft"); coherent(f);
};
// ES0F-04/11/14: the issued record is exactly what the iframe received; no cachebuster or readiness in it.
S.issuedIdentity=async mk=>{
  const f=mk(); pair(f,"method","2"); f.click("mode-local");
  const rec=issued(f);
  assert.ok(rec&&typeof rec==="object","an issued-preview record exists");
  assert.equal(rec.src,f.elements.get("pv").src,"record src equals the iframe src");
  assert.equal(rec.allow,f.elements.get("pv").allow,"record permission equals the iframe permission");
  assert.equal(rec.hash,f.hash(),"record output equals the snippet output");
  assert.ok(!/[?&]r=/.test(String(rec.identity)),"identity excludes the cachebuster");
  assert.ok(String(rec.identity).includes(f.hash())&&String(rec.identity).includes("geolocation"),"identity includes output and permission");
  assert.ok(!Object.keys(rec).some(k=>/load|ready|render/i.test(k)),"no loaded/rendered state is invented");
  coherent(f);
};
// ES0F-06 / D1: invalid portable draft keeps the preview and export; outputs refuse with readable feedback.
S.invalidDraft=async mk=>{
  const f=mk(), code0=f.elements.get("code").value, src0=f.elements.get("pv").src;
  for(const bad of [""," ","abc"]) {
    pair(f,"lat",bad);
    assert.equal(navs(f),1,"invalid draft issues no navigation ("+JSON.stringify(bad)+")");
    assert.equal(f.elements.get("pv").src,src0,"last valid preview retained");
    assert.equal(f.elements.get("code").value,code0,"invalid export not presented");
    assert.equal(f.elements.get("lat").getAttribute("aria-invalid"),"true","invalid field marked");
    assert.notEqual(f.elements.get("lon").getAttribute("aria-invalid"),"true","valid field not marked");
    const note=f.elements.get("draftnote");
    assert.ok(note&&!note.hidden&&/latitude/i.test(note.textContent),"one short note names the problem");
  }
  await Promise.all(f.click("copy").results); await drain();
  assert.equal(f.calls.copy.length,0,"Copy refuses while invalid"); assert.match(f.elements.get("copied").textContent,/valid/i);
  await Promise.all(f.click("install").results); await drain();
  assert.equal(f.calls.copy.length,0,"Install refuses while invalid"); assert.match(f.elements.get("installtip").textContent,/valid/i);
  f.click("open"); assert.equal(f.opens.length,0,"Open refuses while invalid");
  pair(f,"lat","24.4672");
  assert.equal(navs(f),1,"returning to the last issued output issues no navigation");
  assert.notEqual(f.elements.get("lat").getAttribute("aria-invalid"),"true"); assert.equal(f.elements.get("draftnote").hidden,true);
  assert.equal(f.elements.get("code").value,code0);
  await Promise.all(f.click("copy").results); await drain();
  assert.deepEqual(f.calls.copy,[code0],"Copy works again with the current output");
  f.click("open"); assert.equal(f.opens.length,1); assert.equal(f.opens[0][0],f.run("url()"));
  pair(f,"lon",""); pair(f,"lat","25");
  assert.equal(navs(f),1,"still invalid (longitude) after a latitude change");
  pair(f,"lon","39.6142"); assert.equal(navs(f),2,"a different valid output issues one navigation"); coherent(f);
  pair(f,"lat",""); f.click("mode-local");
  assert.equal(navs(f),3,"local mode is never invalid for coordinates"); coherent(f);
  assert.equal(f.elements.get("draftnote").hidden,true);
  f.click("mode-portable");
  assert.equal(navs(f),3,"switch back to an invalid portable draft keeps the local preview");
  assert.equal(f.elements.get("pv").allow,"geolocation","retained preview keeps its own permission");
};
// D2: provenance-only change (same coordinates) updates draft state and issues no navigation.
S.provenance=async mk=>{
  const f=mk();
  f.click("geo"); await f.resolve("gps",0,{coords:{latitude:24.4672,longitude:39.6142,accuracy:12},timestamp:0});
  assert.equal(f.run("builderLocation&&builderLocation.source"),"browser-geolocation","provenance retained in draft");
  assert.match(f.elements.get("geotip").textContent,/^Using browser position/);
  assert.equal(navs(f),1,"provenance-only change issues no navigation");
  f.click("geo"); await f.resolve("gps",1,{coords:{latitude:21.42251,longitude:39.82616,accuracy:12},timestamp:0});
  assert.equal(navs(f),2,"a target change issues one navigation"); coherent(f);
};
// ES0F-13 / D3: Refresh re-issues the last issued identity exactly once, never an invalid draft.
S.refresh=async mk=>{
  const f=mk(); pair(f,"method","2");
  const before=last(f);
  f.click("reload"); assert.equal(navs(f),3,"Refresh issues exactly one navigation");
  assert.equal(srcHash(last(f).src),srcHash(before.src)); assert.equal(srcRev(last(f).src),srcRev(before.src)+1);
  assert.equal(last(f).allow,before.allow); coherent(f);
  pair(f,"lat",""); assert.equal(navs(f),3);
  f.click("reload"); assert.equal(navs(f),4,"Refresh with an invalid draft still issues once");
  assert.equal(param(srcHash(last(f).src),"lat"),"24.4672","Refresh re-issues the last valid output, not the invalid draft");
  assert.equal(f.elements.get("pv").src,last(f).src);
};
// ES0F-14 + ES0F-11: a throwing assignment records nothing; the export is still current; the retry navigates.
S.assignmentFailure=async mk=>{
  const f=mk(), rec0=issued(f);
  f.sandbox.__pvThrow=1;
  assert.throws(()=>f.input("method","2","input"),/controlled src assignment failure/);
  assert.equal(navs(f),1);
  assert.equal(param(f.hash(),"method"),"2");
  assert.equal(param(new URL(f.elements.get("code").value.match(/src="([^"]+)"/)[1]).hash.slice(1),"method"),"2","export refreshed though navigation failed");
  assert.ok(rec0,"an issued-preview record exists");
  assert.equal(issued(f).src,rec0.src,"failed assignment is not recorded as issued");
  f.elements.get("method").dispatch("change");
  assert.equal(navs(f),2,"the next legitimate attempt navigates"); coherent(f);
};
// ES0F-07/08: obsolete lookups (even equal-valued) mutate nothing; dedupe never decides intent.
S.staleLookup=async mk=>{
  const f=mk();
  pair(f,"lat","25"); assert.equal(navs(f),2);
  await f.resolve("coarse",0,{ok:true,cfg:{lat:24.4672,lon:39.6142,label:"Madinah",method:"4",source:"coarse"}});
  assert.equal(f.elements.get("lat").value,"25","stale coarse result cannot publish"); assert.equal(navs(f),2);
  f.click("geo"); pair(f,"lat","26"); pair(f,"lat","25"); assert.equal(navs(f),4);
  const snap=f.snapshot(), pin=f.elements.get("geo").classList.toString();
  await f.resolve("gps",0,{coords:{latitude:25,longitude:39.6142,accuracy:5},timestamp:0});
  assert.equal(f.snapshot(),snap,"obsolete equal-valued GPS result is a complete no-op");
  assert.equal(f.elements.get("geo").classList.toString(),pin); assert.equal(f.run("builderLocation"),null); assert.equal(navs(f),4);
};
// ES0F-09: candidate cycling keeps its behaviour; an identical-identity candidate adds no navigation.
S.cycling=async mk=>{
  const f=mk(); f.input("label","Inverness","input"); const base=navs(f);
  f.key("label","Enter");
  await f.resolve("search",0,[{lat:57.47778,lon:-4.22472,cc:"gb",norm:"Inverness, Scotland"},
    {lat:28.836,lon:-82.33,cc:"us",norm:"Inverness, Florida"},{lat:28.836,lon:-82.33,cc:"us",norm:"Inverness, FL"}]);
  assert.equal(navs(f),base+1); assert.match(f.elements.get("geotip").textContent,/^Match 1\/3/);
  f.key("label","Enter"); assert.equal(navs(f),base+2); assert.equal(param(srcHash(last(f).src),"method"),"2");
  f.key("label","Enter"); assert.match(f.elements.get("geotip").textContent,/^Match 3\/3/);
  assert.equal(navs(f),base+2,"identical-identity candidate issues no navigation");
  f.key("label","Enter"); assert.match(f.elements.get("geotip").textContent,/^Match 1\/3/);
  assert.equal(navs(f),base+3); coherent(f);
};
// ES0F-12: a pending copy keeps its captured bytes across equivalent and changed edits.
S.pendingCopy=async mk=>{
  let next=null;
  const f=mk({clipboard:()=>next.promise,fallback:()=>false}), captured=f.elements.get("code").value;
  next=deferred(); const pending=Promise.all(f.click("copy").results);
  pair(f,"method","4"); pair(f,"method","2"); assert.equal(navs(f),2);
  next.reject(new Error("controlled clipboard denial")); await pending; await drain();
  assert.equal(f.calls.copy[0],captured);
  assert.equal(f.elements.get("embed-recovery").value,captured,"recovery shows the captured payload");
  assert.notEqual(f.elements.get("code").value,captured,"current export moved on");
  // A later successful copy (existing success path) carries the CURRENT output, not the recovery bytes.
  next=deferred(); next.resolve(); await Promise.all(f.click("copy").results); await drain();
  assert.equal(f.calls.copy[1],f.elements.get("code").value); assert.match(f.elements.get("copied").textContent,/copied/i);
  assert.equal(navs(f),2,"copying issues no navigation");
};
// ES0F-15: 325×530 wrapper everywhere, local-only geolocation, focus untouched by publication.
S.invariants=async mk=>{
  const f=mk(), size=/width:325px;height:530px/;
  assert.match(f.elements.get("code").value,size);
  assert.match(f.sources.page.match(/<iframe id="pv"[^>]*>/)[0],size);
  const readme=fs.readFileSync(path.join(root,"README.md"),"utf8");
  // Current-version snippets only; the frozen V1 compatibility snippet (src .../v1/) keeps its own historical size.
  const current=(readme.match(/<iframe[\s\S]*?<\/iframe>/g)||[]).filter(x=>!/\/v1\//.test(x));
  assert.ok(current.length>=2,"README current snippets present");
  for(const snippet of current)assert.match(snippet,size,"README current wrapper is 325×530");
  assert.match(fs.readFileSync(path.join(root,"presets","salah-widget.tablissng.json"),"utf8"),size);
  assert.equal(f.elements.get("pv").allow,""); assert.ok(!/allow=/.test(f.elements.get("code").value));
  f.elements.get("lat").focus(); pair(f,"lat","24.4672"); pair(f,"lat","25"); f.click("reload");
  assert.equal(f.document.activeElement.id,"lat","publication does not move focus");
};
module.exports={S,loader,pair,navs,ledger};
