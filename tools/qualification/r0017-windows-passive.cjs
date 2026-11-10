#!/usr/bin/env node
'use strict';
// R0017-C14: explicit passive-only caller, separate from the enforced phase-2
// entry and historical verdicts. Root must admit these exact bytes before use.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const passive=require('./r0017-passive-network.cjs');
const accounting=require('./r0017-request-accounting.cjs');
const BOUND_BASE_SHA='da890861d874a8fe5b05351071bca9bb290a061dbe51f59bb8cfa78ff19a2279';
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function assertDiagnostics(options){
 passive.assertSelection(options);
 if(options['request-accounting']!==undefined&&(options['request-accounting']!=='observed-records'||options['security-provenance']!=='csp'||options['image-assignment-provenance']!==undefined))throw Error('Observed-record accounting requires explicit observed-records mode, csp provenance and no image assignment instrumentation');
 if(options['image-assignment-provenance']!==undefined&&(options['image-assignment-provenance']!=='src'||options['security-provenance']!=='csp'))throw Error('Image assignment provenance requires explicit src mode and csp security correlation');
}
// Serialized into the existing original preload only under the explicit C17
// diagnostic flag. This observes attempted setter calls, never load outcomes.
function imageAssignmentProbe(){
 'use strict';
 const marker='R0017_IMAGE_ASSIGNMENT ',purpose='DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT';
 let debug,stringify,epochNow,performanceNow,realmNonce=null,sequence=0,recordingFailures=0;
 const emit=(event,extra={})=>{
  const next=++sequence;
  try{debug(marker+stringify({schema:'r0017-image-assignment/v1',purpose,event,realmNonce,sequence:next,recordingFailuresBefore:recordingFailures,realEpochMs:epochNow(),realPerformanceMs:performanceNow(),...extra}));}
  catch{recordingFailures++;}
 };
 const errorText=e=>{try{return String(e?.stack||e);}catch{return 'Diagnostic error text unavailable';}};
 try{
  debug=console.debug.bind(console);stringify=JSON.stringify.bind(JSON);
  epochNow=Date.now.bind(Date);performanceNow=performance.now.bind(performance);
  realmNonce=crypto.randomUUID();
  const prototype=HTMLImageElement.prototype,getDescriptor=Object.getOwnPropertyDescriptor,define=Object.defineProperty,apply=Reflect.apply,ErrorConstructor=Error;
  const original=getDescriptor(prototype,'src');
  if(!original||typeof original.set!=='function'||original.configurable!==true)throw Error('Image src native descriptor unavailable or not configurable');
  const nativeSetter=original.set,ids=new WeakMap();let nextImageId=0;
  function r0017ImageSrc(value){
   try{
    let imageId=null;
    if(this!==null&&(typeof this==='object'||typeof this==='function')){
     if(!ids.has(this))ids.set(this,++nextImageId);imageId=ids.get(this);
    }
    const fixture={};let fixtureReadError=null,fixtureAvailable=false;
    try{const source=window.__widgetFixture;if(source&&typeof source==='object'){fixtureAvailable=true;for(const key of ['run','attempt','documentId','sourceSha256','hash','mode']){const v=source[key];if(v===null||['string','number','boolean'].includes(typeof v))fixture[key]=v;}}}
    catch(e){fixtureReadError=errorText(e);}
    const row={phase:'BEFORE_NATIVE_SETTER',imageId,url:location.href,isTop:window===window.top,documentReadyState:document.readyState,fixture,fixtureAvailable,fixtureReadError,
     valueType:typeof value,stringCoverage:typeof value==='string'?'FULL_INPUT_STRING':'NON_STRING_NOT_COERCED',stack:new ErrorConstructor('Image src setter invocation').stack,
     descriptorMatches:getDescriptor(prototype,'src')?.set===r0017ImageSrc};
    if(typeof value==='string'){row.assignedString=value;row.stringCodeUnits=value.length;}
    emit('setter-invocation-attempt',row);
   }catch(e){recordingFailures++;emit('assignment-recording-failed',{error:errorText(e)});}
   // Deliberately outside the diagnostic catch: exactly one native invocation,
   // with the original receiver/value, preserves native conversion and throws.
   return apply(nativeSetter,this,[value]);
  }
  define(prototype,'src',{...original,set:r0017ImageSrc});
  const installed=getDescriptor(prototype,'src');
  if(installed.set!==r0017ImageSrc||installed.get!==original.get||installed.enumerable!==original.enumerable||installed.configurable!==original.configurable)throw Error('Image src installation readback mismatch');
  emit('installed',{url:location.href,isTop:window===window.top,descriptor:{getterPreserved:true,enumerable:installed.enumerable,configurable:installed.configurable},coverage:'src setter only; no lifecycle listeners or subsequent descriptor census'});
 }catch(e){emit('installation-failed',{error:errorText(e)});}
}
function imageAssignmentPreload(original,origin){
 if(typeof original!=='string')throw Error('Original storage preload source missing');
 return '()=>{const originalResult=('+original+')();if(location.origin==='+JSON.stringify(new URL(origin).origin)+'){('+imageAssignmentProbe.toString()+')();}return originalResult;}';
}
function parse(tokens){
 const allowed=new Set(['network-observation','groups','cases','base-file','base-sha','root','out','payload-sha','security-provenance','image-assignment-provenance','request-accounting']),args={};
 if(tokens.length%2)throw Error('Arguments must be explicit --name VALUE pairs');
 for(let i=0;i<tokens.length;i+=2){const key=tokens[i].startsWith('--')?tokens[i].slice(2):null;if(!allowed.has(key)||Object.hasOwn(args,key)||!tokens[i+1]||tokens[i+1].startsWith('--'))throw Error('Unknown, duplicate or missing passive argument: '+tokens[i]);args[key]=tokens[i+1];}
 assertDiagnostics(args);
 if(!args['base-file']||!/^[a-f0-9]{64}$/.test(args['base-sha']||'')||!args.root||!args.out)throw Error('Explicit --base-file, --base-sha, --root and --out are required');
 return args;
}
function configure(api,options){
 assertDiagnostics(options);
 if(api.networkObservation!==undefined||typeof api.startSession!=='function')throw Error('Passive caller requires one unconfigured native session interface');
 const imageRequested=options['image-assignment-provenance']==='src',originalPreload=api.preload;
 if(imageRequested&&typeof originalPreload!=='function')throw Error('Image assignment diagnostic requires the original preload interface');
 if(imageRequested)api.preload=function(...args){
  if(args.length!==3||args[2]!==false)throw Error('Image assignment diagnostic requires the unchanged public storage preload signature');
  return imageAssignmentPreload(Reflect.apply(originalPreload,this,args),args[1]);
 };
 const observedRecords=options['request-accounting']==='observed-records';
 const start=api.startSession;api.networkObservation=observedRecords?accounting.METHOD:passive.METHOD;
 api.startSession=(...args)=>{
  if(args.length!==7)throw Error('Passive session caller signature changed');
  if(observedRecords){
   if(Object.hasOwn(args[4],'requestAccountingRequest'))throw Error('Request accounting already owned');
   const source=accounting.admitSource(api.ROOT,api.source),served=accounting.admitPublicReadback(source,api.result.publicReadback);
   Object.assign(args[4],{requestAccountingRequest:Object.freeze({schema:'r0017-accounting-request/v1',method:accounting.METHOD}),requestAccountingSource:source,requestAccountingPublicSource:served});
  }
  if(options['security-provenance']==='csp'){
   if(Object.hasOwn(args[4],'securityProvenanceRequest'))throw Error('Security provenance request already owned');
   Object.defineProperty(args[4],'securityProvenanceRequest',{enumerable:true,value:Object.freeze({schema:'r0017-security-provenance-request/v1',mode:'csp'})});
  }
  if(imageRequested){
   if(Object.hasOwn(args[4],'imageAssignmentProvenance'))throw Error('Image assignment provenance already owned');
   Object.defineProperty(args[4],'imageAssignmentProvenance',{enumerable:true,value:Object.freeze({schema:'r0017-image-assignment-request/v1',mode:'src',purpose:'DIAGNOSTIC_ONLY_NO_ACCEPTANCE_CREDIT',probeSourceSha256:hash(imageAssignmentProbe.toString()),transport:'EXISTING_BIDI_LOG_ENTRY_ADDED',marker:'R0017_IMAGE_ASSIGNMENT ',coverage:'Attempted src setter assignments; imageId is not publisher identity; no CSS/parser/srcset/SVG/setAttribute coverage',limitations:'Stack, full-string serialization and console add work before native setter. Missing/replaced/lost markers or absent later descriptor census are coverage gaps, never evidence of no assignment. Native load/microtask outcomes are not observed.'})});
  }
  return start(...args,'passive');
 };
 return api;
}
async function main(){
 const args=parse(process.argv.slice(2)),baseFile=path.resolve(args['base-file']);
 if(args['base-sha']!==BOUND_BASE_SHA)throw Error('C14 entry is bound to a different base; independent review is required before rebinding');
 if(baseFile!==path.join(__dirname,'r0017-windows-proof.cjs'))throw Error('C14 base and its observation dependency must come from this source directory');
 const raw=fs.readFileSync(baseFile);if(hash(raw)!==BOUND_BASE_SHA)throw Error('C14 base collector hash mismatch');
 const text=raw.toString('utf8'),marker='async function main(){';
 if(text.split(marker).length!==2||!text.startsWith('#!/usr/bin/env node\n'))throw Error('C14 exact base extraction anchor changed');
 const prefix=text.slice('#!/usr/bin/env node\n'.length,text.indexOf(marker));
 const exportInterface=`\nmodule.exports={ROOT,OUT,EXPECTED,PUBLIC,runId,result,sha,write,record,seeds,mime,identify,locate,startSession,preload,SNAPSHOT,PROGRESS,checkCommon,screenshot,publicReadback,remainingBudgetMs,operationTimeout,launchBlock,notAttempted,get source(){return source;},get declared(){return declared;}};\n`;
 const loaded={exports:{}};new Function('require','module','exports','__filename','__dirname',prefix+exportInterface)(require,loaded,loaded.exports,baseFile,path.dirname(baseFile));
 const api=configure(loaded.exports,args),files=['r0017-windows-passive.cjs','r0017-passive-network.cjs','r0017-request-accounting.cjs','r0017-phase2-controls.cjs','r0017-windows-proof.cjs'];
 api.result.loader={schema:'r0017-passive-loader/v2',method:api.networkObservation,baseSha256:BOUND_BASE_SHA,compiledPrefixSha256:hash(prefix),exportInterfaceSha256:hash(exportInterface),baseReuse:'Exact base function source; first-phase main withheld; default enforced path unchanged',sourceFiles:files.map(file=>({file,sha256:hash(fs.readFileSync(path.join(__dirname,file)))}))};
 for(const file of files)fs.copyFileSync(path.join(__dirname,file),path.join(api.OUT,file));fs.writeFileSync(path.join(api.OUT,'base-export-interface.js'),exportInterface);
 try{return await require('./r0017-phase2-controls.cjs').run(api,{groups:args.groups,cases:args.cases});}
 catch(e){api.result.qualification='PARTIAL';api.result.status='PASSIVE_UNHANDLED_COLLECTOR_FAILURE';api.result.error=String(e.stack||e);api.result.finishedUtc=new Date().toISOString();api.write(path.join(api.OUT,'summary.json'),api.result);process.exitCode=1;}
}
module.exports={parse,configure,main,BOUND_BASE_SHA,imageAssignmentProbe};
if(require.main===module)main().catch(e=>{console.error(String(e.stack||e));process.exitCode=1;});
