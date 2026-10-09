"""Isolated adaptation only; production sources are read and hash-bound, never edited."""
import hashlib,json,re
from pathlib import Path

HERE=Path(__file__).parent
ROOT=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
source=ROOT/'tests/r0023-native.html'
text=source.read_text(encoding='utf-8')
changes=[]
def replace(old,new,label):
 global text
 assert text.count(old)==1,(label,text.count(old))
 text=text.replace(old,new)
 changes.append(label)

expected={}
for kind,name in [('widget','index.html'),('builder','builder.html')]:
 data=(ROOT/name).read_bytes();body=data.decode('utf-8')
 expected[kind]={'sha':hashlib.sha256(data).hexdigest(),'attrs':[m[0] for m in re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',body,re.I)]}
assert len(expected['widget']['attrs'])==6
assert len(expected['builder']['attrs'])==2

replace("script-src 'self' 'unsafe-inline'; style-src", "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' blob:; worker-src 'self' blob:; frame-src 'self'; style-src", 'Fixture-only CSP admits current local workers/wasm and isolated same-origin preview; no production CSP edit')
replace('  let now=NativeDate.parse("2026-10-02T12:00:00Z");',r'''  const stream=query.get("stream")||"none",copy=query.get("copy")||"deny",fallback=query.get("fallback")||"false",platform=query.get("platform")||"";
  const holds=new Set((query.get("hold")||"").split(",").filter(Boolean));
  const expectedPages=EXPECTED_PAGES,expectedConfig="91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81";
  let runtimeFiles=new Set(),now=NativeDate.parse("2026-10-02T12:00:00Z");'''.replace('EXPECTED_PAGES',json.dumps(expected,separators=(',',':'))), 'Pin exact widget/builder hashes and six/two script attributes; add explicit bounded query controls')
replace('  report.denySave=false;report.denyRemove=false;',r'''  report.denySave=false;report.denyRemove=false;
  report.target="18ff14860ff41c084b1db5f396bb62aa9c22b1be";report.nativeRuntimeScripts="preserved exact six; no module suppression";
  report.providerJobs=[];report.copyJobs=[];report.fallbackCalls=[];report.copyMode=copy;report.fallbackMode=fallback;report.streamMode=stream;
  const providerJobs=new Map(),copyJobs=[];
  function respond(kind,u,payload,status=200,init){
    const id=report.providerJobs.length,row={id,kind,url:u.href,at:now,state:holds.has(kind)?"held":"returned",status};report.providerJobs.push(row);
    if(init&&init.signal){row.signalAborted=init.signal.aborted;init.signal.addEventListener("abort",()=>{row.signalAborted=true;},{once:true});}
    if(!holds.has(kind))return json(payload,status);
    return new Promise((resolve,reject)=>providerJobs.set(id,{row,payload,status,resolve,reject}));
  }
  report.releaseProvider=(id,payload,status)=>{const job=providerJobs.get(Number(id));if(!job||job.row.state!=="held")throw Error("No held provider "+id);
    job.row.state="returned";job.resolve(new Response(JSON.stringify(payload===undefined?job.payload:payload),{status:status===undefined?job.status:status,headers:{"Content-Type":"application/json"}}));};
  report.rejectProvider=id=>{const job=providerJobs.get(Number(id));if(!job||job.row.state!=="held")throw Error("No held provider "+id);job.row.state="rejected";job.reject(Error("controlled provider failure"));};
  report.pendingProviders=kind=>report.providerJobs.filter(j=>j.state==="held"&&(!kind||j.kind===kind));
  function searchPayload(u){const q=(u.searchParams.get("q")||"").toLowerCase();
    if(q==="london")return [{class:"place",lat:"51.5",lon:"-0.12",address:{city:"London",country:"United Kingdom",country_code:"gb"}},
      {class:"place",lat:"42.98",lon:"-81.25",address:{city:"London",state:"Ontario",country:"Canada",country_code:"ca"}}];
    if(q==="cairo")return [{class:"place",lat:"30.0444",lon:"31.2357",address:{city:"Cairo",country:"Egypt",country_code:"eg"}}];
    return [{class:"place",lat:"52.52",lon:"13.41",address:{city:"Berlin",country:"Germany",country_code:"de"},boundingbox:["52","53","13","14"]}];
  }
  function copyWrite(payload){const row={index:report.copyJobs.length,payload:String(payload),state:report.copyMode==="hold"?"held":report.copyMode};report.copyJobs.push(row);
    if(report.copyMode==="success")return Promise.resolve();if(report.copyMode!=="hold")return Promise.reject(Error("controlled clipboard denial"));
    return new Promise((resolve,reject)=>copyJobs[row.index]={row,resolve,reject});}
  report.releaseCopy=(index,ok)=>{const job=copyJobs[index];if(!job||job.row.state!=="held")throw Error("No held copy "+index);job.row.state=ok?"success":"denied";ok?job.resolve():job.reject(Error("controlled clipboard denial"));};
  report.application=()=>{const ids=page==="builder"?["label","lat","lon","method","school","time","units","appearance","dfcode"]:["set-label","set-lat","set-lon","set-method","set-school","set-time","set-units","set-appearance","set-datefmt"];
    const pin=document.getElementById(page==="builder"?"geo":"set-pin"),qa=typeof window.qaState==="function"?window.qaState():null;
    return {inputs:Object.fromEntries(ids.map(id=>[id,document.getElementById(id)?.value])),config:qa?.config||null,
      status:document.getElementById("set-status")?.textContent||document.getElementById("geotip")?.textContent,
      pin:pin?{classes:pin.className,title:pin.title,name:pin.getAttribute("aria-label")}:null,
      code:document.getElementById("code")?.value,previewSrc:document.getElementById("pv")?.getAttribute("src"),
      savedBytes:bytes.get(key)??null};};''', 'Provider/copy controls capture actual action payloads with no owner network/clipboard sink; inspect whole application state')
replace('    if(u.href==="https://get.geojs.io/v1/ip/geo.json"||u.href==="https://ipinfo.io/json"){\n      if(detect==="fail")return json({error:"synthetic detection failure"},503);\n      return u.hostname==="get.geojs.io"?json({latitude:"24.47",longitude:"39.61",city:"Madinah",country:"Saudi Arabia",country_code:"SA",accuracy:"5"}):json({loc:"51.5,-0.12",city:"London",country:"GB"});\n    }',r'''    if(u.origin===rootURL.origin){const relative=decodeURIComponent(u.pathname.slice(rootURL.pathname.length));
      if(!runtimeFiles.has(relative))return Promise.reject(Error("Unadmitted local asset "+relative));return nativeFetch(input,init);}
    if(u.href==="https://get.geojs.io/v1/ip/geo.json"||u.href==="https://ipinfo.io/json"){
      if(stream!=="none"){
        const route=stream==="fail"?"/failure":u.hostname==="get.geojs.io"?(stream==="finite"?"/geojs-finite":"/geojs-stall"):"/ipinfo";
        const row={id:report.providerJobs.length,kind:"coarse-stream",url:u.href,route,state:"native-fetch",signalAborted:!!init?.signal?.aborted};report.providerJobs.push(row);
        init?.signal?.addEventListener("abort",()=>{row.signalAborted=true;},{once:true});
        return nativeFetch(new URL(route,rootURL),init).then(r=>{row.headersReturned=true;row.http=r.status;return r;},e=>{row.error=String(e);throw e;});
      }
      if(detect==="fail")return respond("coarse",u,{error:"synthetic detection failure"},503,init);
      return respond("coarse",u,u.hostname==="get.geojs.io"?{latitude:"24.47",longitude:"39.61",city:"Madinah",country:"Saudi Arabia",country_code:"SA",accuracy:"5"}:{loc:"51.5,-0.12",city:"London",country:"GB"},200,init);
    }''', 'Forward only admitted current runtime assets; native streamed routes retain real fetch/Response/AbortController signal')
replace('    if(u.origin==="https://nominatim.openstreetmap.org")return json([{class:"place",lat:"52.52",lon:"13.41",address:{city:"Berlin",country:"Germany",country_code:"de"},boundingbox:["52","53","13","14"]}]);', '    if(u.origin==="https://nominatim.openstreetmap.org")return respond("search",u,searchPayload(u),200,init);', 'Deferred production geocoder requests use canonical London/Cairo positive fixtures')
replace('    if(u.origin==="https://api.bigdatacloud.net")return json({city:"Berlin",countryCode:"DE",continentCode:"EU"});', '    if(u.origin==="https://api.bigdatacloud.net")return respond("reverse",u,{city:"Berlin",countryCode:"DE",continentCode:"EU"},200,init);', 'Deferred reverse body/request completion for cross-type controls')
replace('    const scripts=[...pageSource.text.matchAll(/<script\\b([^>]*)>([\\s\\S]*?)<\\/script>/gi)];if(scripts.length!==2||!/src="config\\.js"/.test(scripts[0][1])||scripts[1][1].trim())throw Error("Page script anchors changed");',r'''    if(pageSource.sha!==expectedPages[page].sha||configSource.sha!==expectedConfig)throw Error("Exact target source hash changed");
    const manifestSource=await source("docs/real-sky/evidence/startup-cloud-20261007/final-v49/CANDIDATE_RUNTIME.json"),manifest=JSON.parse(manifestSource.text);
    if(manifest.treeSha256!=="f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260")throw Error("Target runtime inventory changed");
    runtimeFiles=new Set(Object.keys(manifest.files));report.runtimeInventorySha256=manifest.treeSha256;
    const scripts=[...pageSource.text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)],expectedAttrs=expectedPages[page].attrs;
    if(scripts.length!==expectedAttrs.length||scripts.some((s,i)=>s[1]!==expectedAttrs[i]))throw Error("Page script anchors changed");
    report.scriptCount=scripts.length;report.scriptBodies=scripts.map(s=>s[2].length);
    if(!["none","stall","finite","fail"].includes(stream)||!["deny","hold","success","absent"].includes(copy)||!["true","false","throw"].includes(fallback)||[...holds].some(k=>!["coarse","search","reverse"].includes(k)))throw Error("Unknown current fixture control");
    Object.defineProperty(navigator,"clipboard",{configurable:true,value:copy==="absent"?undefined:{writeText:copyWrite}});
    document.execCommand=command=>{if(command!=="copy")throw Error("Unexpected execCommand "+command);const active=document.activeElement;
      report.fallbackCalls.push({command,payload:active?.value,selectionStart:active?.selectionStart,selectionEnd:active?.selectionEnd});
      if(report.fallbackMode==="throw")throw Error("controlled copy fallback failure");return report.fallbackMode==="true";};
    if(platform){Object.defineProperty(navigator,"platform",{configurable:true,value:platform});Object.defineProperty(navigator,"userAgentData",{configurable:true,value:{platform}});report.platformFixture=platform;}''', 'Replace obsolete two-script guard with stronger exact target hash+six/two attributes; no old checks are deleted without equivalent stronger checks')
replace('    const doc=new DOMParser().parseFromString(pageSource.text,"text/html"),originalScripts=doc.querySelectorAll("script"),module=originalScripts[0],runtime=originalScripts[1];', '    const doc=new DOMParser().parseFromString(pageSource.text,"text/html"),originalScripts=[...doc.querySelectorAll("script")],module=originalScripts[0],runtime=originalScripts[1];', 'Retain all original DOM script nodes and place seed before first production consumer/first paint')
replace('    if(after.length!==3||after[0][2]!==configSource.text||after[2][2]!==scripts[1][2])throw Error("Production script body changed during wrapping");',r'''    if(after.length!==scripts.length+1||after[0][2]!==configSource.text||after[1][2]!==seedScript.textContent||
      scripts.slice(1).some((s,i)=>after[i+2][2]!==s[2]||after[i+2][1].trim()!==s[1].trim()))throw Error("Production script body changed during wrapping");
    report.productionScriptBodiesPreserved=true;report.wrappedScriptCount=after.length;''', 'Preserve original body-equality guard across every production script, including all external anchors')

destination=HERE/'r0023-current-native.html'
destination.write_text(text,encoding='utf-8')
report={'status':'PREPARED_NOT_BROWSER_EXECUTED','sourceFixture':str(source),'sourceFixtureSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'adaptedFixture':str(destination),'adaptedFixtureSha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'target':'18ff14860ff41c084b1db5f396bb62aa9c22b1be',
 'expectedPages':expected,'changes':changes,'preserved':['Production script bodies/attributes/order (all six widget scripts, both builder scripts)','Storage isolation and fixed synthetic clock checks','Unknown query/resource rejection','Actual qaState/formConfig initialization check','No real location/clipboard/provider sink; only admitted local assets and loopback streams'],
 'limitations':['No browser executed by D','Provider/copy doubles prove native DOM/event behavior, not real provider availability/clipboard permission policy','Fonts suppressed as original fixture; no production-font appearance claim','Current modules/workers are retained, so primary must keep one case/preview context at a time','No #35 iframe policy certification added; explicit docs gaps remain open']}
(HERE/'native-fixture-adaptation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
