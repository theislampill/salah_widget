"use strict";
// R000F mutation controls. Each in-memory mutant of the GENERATED builder script (nothing written to disk) runs
// the same real-handler scenario as its healthy run and must fail an actual assertion; setup/TypeErrors are not
// detection. Every mutation site must occur exactly once.
const {test}=require("node:test");
const assert=require("node:assert/strict");
const {S,loader}=require("./builder-preview-publication-fixture.cjs");
const {readSource}=require("./r000f-fixture.cjs");
const script=readSource("builder.html").match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const EQ="  if(issued && issued.identity===identity) return; // equivalent output: no navigation, no revision\n";
const RECORD="  $(\"pv\").src=src;\n  issued={identity,src,allow,hash:h,rev}; rev++;\n";
const cases=[
  ["m1 navigate on every event",EQ,"","inputChangePair"],
  ["m2 revision bumped on equivalent output","if(issued && issued.identity===identity) return;","if(issued && issued.identity===identity){ rev++; return; }","inputChangePair"],
  ["m3 identity compared on raw form values","identity=previewIdentity(allow,h);",
    'identity=previewIdentity(allow,JSON.stringify([$("lat").value,$("lon").value,$("label").value,$("method").value,$("dfcode").value]));',"equivalentSpellings"],
  ["m4 invalid draft replaces the preview","  if(bad.length) return;                          // D1","  if(false) return;                          // D1","invalidDraft"],
  ["m5 Copy allowed while invalid",'$("copy").onclick=()=>{ if(refuseInvalid("copied")) return; ','$("copy").onclick=()=>{ ',"invalidDraft"],
  ["m6 provenance-only change navigates",'function previewIdentity(allow,h){ return allow+" "+base+"#"+h; }',
    'function previewIdentity(allow,h){ return allow+" "+base+"#"+h+" "+(builderLocation?builderLocation.source:"manual"); }',"provenance"],
  ["m7 Refresh issues the current (invalid) draft","if(issued) issuePreview(issued.identity,issued.allow,issued.hash); else update();",
    'issuePreview(previewIdentity(embedMode==="local"?"geolocation":"",hash()),embedMode==="local"?"geolocation":"",hash());',"refresh"],
  ["m8 Refresh suppressed by the dedupe","if(issued) issuePreview(issued.identity,issued.allow,issued.hash); else update();","update();","refresh"],
  ["m9a issued record written before the iframe is navigated",RECORD,"  issued={identity,src,allow,hash:h,rev}; rev++;\n  $(\"pv\").src=src;\n","assignmentFailure"],
  ["m9b issued record never updated",RECORD,"  $(\"pv\").src=src;\n  rev++;\n","inputChangePair"],
  ["m10 local-mode label edit navigates",'function previewIdentity(allow,h){ return allow+" "+base+"#"+h; }',
    'function previewIdentity(allow,h){ return allow+" "+base+"#"+h+" "+$("label").value; }',"localMode"],
  ["m11 export refreshed only after a completed navigation","  $(\"code\").value=snippet();                      // export always reflects the current valid draft\n",
    "  issuePreview=(f=>(...a)=>{ f(...a); $(\"code\").value=snippet(); })(issuePreview);\n","assignmentFailure"],
  ["m12 radio Enter/Space double-handled in keydown","  if(!direction) return;",
    '  if(!direction){ if(e.key==="Enter"||e.key===" ") setMode(e.target.id==="mode-local"?"local":"portable"); return; }',"radioKeys"],
  ["m13 Refresh uses the current allow instead of issued.allow","issuePreview(issued.identity,issued.allow,issued.hash)",
    'issuePreview(issued.identity,embedMode==="local"?"geolocation":"",issued.hash)',"localPortableRefresh"],
  ["m14 Refresh uses the current output instead of issued.hash","issuePreview(issued.identity,issued.allow,issued.hash)",
    "issuePreview(issued.identity,issued.allow,hash())","localPortableRefresh"],
  ["m15 invalid note ignores the retained issue's mode",'issued&&issued.allow==="geolocation"?INVALID_NOTE_LOCAL:INVALID_NOTE',"INVALID_NOTE","localPortableRefresh"],
  ["m16 refusal keeps the earlier copy's timer and sequence","clearTimeout(state.timer); state.seq++; $(buttonId)","$(buttonId)","refusalTimer"],
  ["m17 refusal does not invalidate an in-flight copy","state.seq++; $(buttonId)","$(buttonId)","refusalInFlight"],
  ["m18 refusal leaves the abandoned button disabled","$(buttonId).disabled=false;","","refusalInFlight"],
  ["m19 refusal leaves the manual-recovery box visible",'  $((buttonId==="copy"?"embed":"install")+"-recovery-wrap").hidden=true;\n',"","refusalRecovery"],
  ["m20 refusal text never cleared once valid",'  if(!bad.length) [["copied",""]','  if(false) [["copied",""]',"refusalCleared"],
  ["m21 identity omits the permission policy",'function previewIdentity(allow,h){ return allow+" "+base+"#"+h; }',
    'function previewIdentity(allow,h){ return base+"#"+h; }',"issuedIdentity"],
  ["m22 browser position bypasses the shared admission","const a=window.SalahConfig?SalahConfig.admitCoordinates(pos&&pos.coords&&pos.coords.latitude,pos&&pos.coords&&pos.coords.longitude):{ok:false};",
    "const a={ok:true,lat:+pos.coords.latitude,lon:+pos.coords.longitude};","admissionSeam"],
  ["m23 admitted search result never issues",'  if(methodAuto) $("method").value=(c.cc==="us"||c.cc==="ca"||c.cc==="mx")?"2":"4";\n  update();\n',
    '  if(methodAuto) $("method").value=(c.cc==="us"||c.cc==="ca"||c.cc==="mx")?"2":"4";\n',"admissionSeam"],
  ["m24 zero coordinate treated as missing",'return ["lat","lon"].filter(id=>c[id]==null);','return ["lat","lon"].filter(id=>!c[id]);',"zeroCoordinates"],
];
for(const [name,from,to,key]of cases)test("R000F publication mutation: "+name+" -> "+key,async()=>{
  assert.equal(script.split(from).length,2,"one declared mutation location");
  await S[key](loader());
  await assert.rejects(()=>S[key](loader(source=>source.replace(from,to))),
    error=>error instanceof assert.AssertionError,"only an actual assertion failure detects the mutant");
});
