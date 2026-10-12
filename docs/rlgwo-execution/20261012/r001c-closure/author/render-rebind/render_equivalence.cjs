'use strict';
// Offline parsing only. Imports no browser, server, native harness or product builder.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const OWN=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const cfg=JSON.parse(fs.readFileSync(path.join(OWN,'RENDER_INPUTS.json'),'utf8'));
assert.deepEqual(process.argv.slice(2),['--offline-parse']);
assert.equal(path.resolve(process.execPath),path.resolve(cfg.node.path));
assert.equal(sha(fs.readFileSync(cfg.node.path)),cfg.node.sha256);
const css='body{font:16px/1.45 sans-serif;margin:30px;max-width:1220px;color:#111;background:white}table{border-collapse:collapse;table-layout:fixed;width:100%;font-size:14px}td,th{border:1px solid;padding:8px;vertical-align:top;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid;padding:12px}code{font-size:13px}';
function render(marked,source,doc,digest){
 const renderer=new marked.Renderer(),baseHeading=renderer.heading;
 renderer.heading=function(token){return baseHeading.call(this,token);};
 const engine=new marked.Marked({gfm:true,breaks:false,renderer});
 return'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'none\'; frame-src \'none\'; img-src \'none\'; font-src \'none\'; base-uri \'none\'"><title>LOCAL source preview '+doc+'</title><style>'+css+'</style></head><body><p id="preview-scope">LOCAL SOURCE PREVIEW. Not GitHub-public delivery or widget optical/motion qualification.</p><article id="document" data-doc="'+doc+'" data-source-sha256="'+digest+'">'+engine.parse(source)+'</article></body></html>';
}
async function main(){
 assert.equal(sha(fs.readFileSync(cfg.marked.path)),cfg.marked.sha256);
 const marked=await import(pathToFileURL(cfg.marked.path).href),rows=[];
 for(const doc of cfg.docs){
  const old=fs.readFileSync(doc.oldSource.path),final=fs.readFileSync(doc.finalSource.path),frozen=fs.readFileSync(doc.finalSnapshot.path),retained=fs.readFileSync(doc.retainedHTML.path);
  assert.equal(sha(old),doc.oldSource.sha256);assert.equal(sha(final),doc.finalSource.sha256);assert.equal(sha(frozen),doc.finalSource.sha256);assert.equal(sha(retained),doc.retainedHTML.sha256);
  const reproduced=Buffer.from(render(marked,old.toString('utf8'),doc.doc,doc.oldSource.sha256));
  assert(reproduced.equals(retained),'full retained original HTML reproduction failed:'+doc.doc);
  const result=Buffer.from(render(marked,frozen.toString('utf8'),doc.doc,doc.finalSource.sha256));
  const relative='rendered-input/'+doc.doc.replace('.md','.html'),dest=path.join(OWN,relative);
  assert(path.dirname(dest)===path.join(OWN,'rendered-input')&&!fs.existsSync(dest));
  fs.writeFileSync(dest,result,{flag:'wx'});
  rows.push({doc:doc.doc,retainedWholeHTMLReproducedExactly:true,oldSourceSha256:doc.oldSource.sha256,finalSourceSha256:doc.finalSource.sha256,retainedHTMLSha256:sha(retained),finalHTML:{path:dest,bytes:result.length,sha256:sha(result)}});
 }
 const report={schema:'r001c-a10-offline-final-html-input/1',status:'PASS_EXACT_RETAINED_GENERATOR_REPRODUCTION_FINAL_INPUT_PARSED',rows,css,cssSha256:sha(Buffer.from(css)),nativeExecuted:false,pixelsProduced:false,browserImports:0,serverImports:0,subjectVMReplays:0};
 fs.writeFileSync(path.join(OWN,'OFFLINE_RENDER_RESULT.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({status:report.status,docs:rows.length,browserServerNative:0}));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
