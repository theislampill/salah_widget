'use strict';
// Independent output/interaction mutants; no product writes, browser calls or native claims.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const {ROOT,sha}=require('./r0009-calendar-harness.cjs');
function edit(source,from,to,count=1){
  assert.equal(source.split(from).length-1,count,'Exact mutation owner occurrence count');
  return source.split(from).join(to);
}
function mutateDate(source,name){
  switch(name){
    case 'after-only-title':return edit(source,'attr("ah","title",projection.explanation);','attr("ah","title",projection.beforeOrAfterMaghrib==="after"?"Hijri date already advanced at sunset":projection.explanation);');
    case 'backwards-hold':return edit(source,'function renderCalendarDates(projection){','let mutantHeldHijri="";\nfunction renderCalendarDates(projection){\n  if(projection.hijriText){ if(mutantHeldHijri>projection.hijriText)projection={...projection,hijriText:mutantHeldHijri};else mutantHeldHijri=projection.hijriText; }');
    case 'second-calendar-instant':return edit(source,'const n=M?partsInTz(M.nowEpoch):null,','const n=M?nowParts():null,');
    case 'title-only-triggers':{
      const hits=Array.from(source.matchAll(/<button type="button" class="date-trigger"[^>]*>[\s\S]*?<\/button>/g));
      assert.equal(hits.length,2,'Both actual footer trigger owners');
      for(const hit of hits)source=edit(source,hit[0],hit[0].replace(/^<button/,'<span').replace(/<\/button>$/,'</span>'));
      return source;
    }
    case 'today-on-click':return edit(source,'dialog.showModal();','$("#dateHijri").textContent=fmtDate(today.date.hijri,"hijri"); dialog.showModal();');
    case 'rebuild-focused-close':return edit(source,'function renderCalendarDates(projection){','function renderCalendarDates(projection){\n  const replacedClose=$("#dateClose");replacedClose.replaceWith(replacedClose.cloneNode(true));');
    case 'dialog-nowrap':return edit(source,'white-space:normal;overflow-wrap:anywhere;','white-space:nowrap;overflow-wrap:normal;',2);
    case 'dialog-unbounded':return edit(source,'width:calc(100vw - 28px);max-width:297px;max-height:calc(100vh - 28px);','width:325px;max-width:none;max-height:none;');
    default:throw Error('Unknown date mutation '+name);
  }
}
const mutationCases=[
  {name:'after-only-title',suite:'r0009-date-selection.cjs',detect:'missing tomorrow is visibly disclosed independently of prayer stale'},
  {name:'backwards-hold',suite:'r0009-date-selection.cjs',detect:'same-day backwards provider correction remains provider-derived positive'},
  {name:'second-calendar-instant',suite:'r0009-date-selection.cjs',detect:'model instant and calendar context remain one snapshot across midnight'},
  {name:'title-only-triggers',suite:'r0019-date-disclosure.cjs',detect:'either real footer value has native keyboard/touch trigger'},
  {name:'today-on-click',suite:'r0019-date-disclosure.cjs',detect:'post-Maghrib click uses the already selected tomorrow value'},
  {name:'rebuild-focused-close',suite:'r0019-date-disclosure.cjs',detect:'unchanged render retains focused control stable nodes and unchanged date text'},
  {name:'dialog-nowrap',suite:'r0019-date-disclosure.cjs',detect:'long full values remain complete while actual dialog CSS wraps and bounds them'},
  {name:'dialog-unbounded',suite:'r0019-date-disclosure.cjs',detect:'long full values remain complete while actual dialog CSS wraps and bounds them'}
];
if(require.main===module){
  const sourcePath=process.argv[2]||path.join(ROOT,'index.html'),source=fs.readFileSync(sourcePath,'utf8');
  const parent=process.argv[3]?path.resolve(process.argv[3]):os.tmpdir();
  const directory=fs.mkdtempSync(path.join(parent,'date-mutations-')),results=[],healthy=new Map();
  const run=(suite,file)=>{const r=spawnSync(process.execPath,[path.join(__dirname,suite),file],{cwd:ROOT,encoding:'utf8'});assert.equal(r.error,undefined,'Child guard executed');const result=JSON.parse(r.stdout);assert.ok(Array.isArray(result.results),'Actual guard result parsed');return {exitCode:r.status,result,stderr:r.stderr};};
  for(const suite of ['r0009-date-selection.cjs','r0019-date-disclosure.cjs']){
    try{const r=run(suite,sourcePath);assert.equal(r.exitCode,0,'Unmodified through-consumer suite passes');assert.ok(r.result.results.every(x=>x.status==='PASS'));healthy.set(suite,r);results.push({name:suite+' unmodified positive',status:'PASS',cases:r.result.results.length});}
    catch(error){results.push({name:suite+' unmodified positive',status:'FAIL',error:error.message});}
  }
  if(healthy.size===2)for(const entry of mutationCases){
    try{
      const changed=mutateDate(source,entry.name);for(const m of changed.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim())new vm.Script(m[1]);
      const file=path.join(directory,entry.name+'.html');fs.writeFileSync(file,changed,{flag:'wx'});const bytes=fs.readFileSync(file);
      const r=run(entry.suite,file),failure=r.result.results.find(x=>x.name===entry.detect);
      assert.equal(r.exitCode,1,'Corresponding source guard rejects the isolated mutant');assert.equal(failure?.status,'FAIL','Required reached consumer discriminates its mutant');
      const positive=entry.suite==='r0009-date-selection.cjs'?'before Maghrib real render positive':'long preset complete real footer text positive';
      assert.equal(r.result.results.find(x=>x.name===positive)?.status,'PASS','Independent real prayer/date rendering remains healthy');
      const receipt={name:entry.name,status:'PASS',sourceSha256:sha(bytes),file,guard:entry.suite,guardExitCode:r.exitCode,detectedBy:failure,healthyPositive:positive,allGuardFailures:r.result.results.filter(x=>x.status==='FAIL')};
      fs.writeFileSync(path.join(directory,entry.name+'.json'),JSON.stringify(r,null,2),{flag:'wx'});results.push(receipt);
    }catch(error){results.push({name:entry.name,status:'FAIL',error:error.message});}
  }
  console.log(JSON.stringify({sourceSha256:sha(source),directory,limit:'Actual source guard reachability/explicit recording focus/CSS contract controls; native interaction and pixel containment still require ROOT',results},null,2));
  process.exitCode=healthy.size!==2||results.some(x=>x.status==='FAIL')?1:0;
}
module.exports={edit,mutateDate,mutationCases};
