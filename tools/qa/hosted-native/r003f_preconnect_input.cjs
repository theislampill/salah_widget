'use strict';
// Altered served-input diagnostic. This module supplies no native qualification.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ORIGINAL_SHA='88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1';
const DERIVED_SHA='16a0f207412572751609316186d5b1f64ee9b31987b9ec6f47c293c9280754b7';
const ORIGINAL_BYTES=1692708,DERIVED_BYTES=1692581;
const PROTOCOL='R003F/preconnect-served-input/1',SOURCE_PROTOCOL='R003F/preconnect-input-source/1';
const SUCCESS='OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC';
const BASE_MATERIALIZATION='fab2e2ad49a14eee2ba715fb75365fa4b0abfa48a1d8b60247343ad29b1021e5';
const TAGS=Object.freeze([
  {text:'<link rel="preconnect" href="https://fonts.googleapis.com">',offset:159},
  {text:'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',offset:219}
]);
const OUTPUTS=Object.freeze(['tools/qa/r003f_owner_baseline.cjs','tools/qa/r003f_capture.cjs','tools/qa/r003f_p1.cjs',
  'tools/qa/r003f_grid.cjs','tools/qa/r0033_isolation.cjs','tools/qa/v1_net_guard.cjs',
  'tools/qa/hosted-native/r003f_ui.cjs','tools/qa/hosted-native/r003f_preconnect_input.cjs']);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function need(value,message){if(!value)throw Error('R003F preconnect input: '+message);}
function identity(){return {protocol:PROTOCOL,original:{sha256:ORIGINAL_SHA,bytes:ORIGINAL_BYTES},
  served:{sha256:DERIVED_SHA,bytes:DERIVED_BYTES},removals:TAGS.map(x=>({offset:x.offset,bytes:Buffer.byteLength(x.text),sha256:sha(x.text)})),
  change:'Only two exact preconnect tag byte spans removed before parsing; all other bytes retained.'};}
function deriveIndex(raw){
  need(Buffer.isBuffer(raw)&&raw.length===ORIGINAL_BYTES&&sha(raw)===ORIGINAL_SHA,'original index digest or size differs');
  for(const tag of TAGS){const b=Buffer.from(tag.text);need(raw.indexOf(b)===tag.offset&&raw.lastIndexOf(b)===tag.offset,'unique source tag differs');}
  let body=Buffer.from(raw);
  for(const tag of [...TAGS].reverse()){const n=Buffer.byteLength(tag.text);body=Buffer.concat([body.subarray(0,tag.offset),body.subarray(tag.offset+n)]);}
  need(body.length===DERIVED_BYTES&&sha(body)===DERIVED_SHA,'derived served index identity differs');
  return {body,identity:identity()};
}
function regular(root,relative){
  need(typeof relative==='string'&&relative&&!path.isAbsolute(relative)&&!relative.split('/').some(x=>!x||x==='.'||x==='..'),'relative file path required');
  let p=path.resolve(root);need(fs.lstatSync(p).isDirectory()&&!fs.lstatSync(p).isSymbolicLink(),'regular root directory required');
  for(const component of relative.split('/')){p=path.join(p,component);need(!fs.lstatSync(p).isSymbolicLink(),'symlink is not admitted');}
  need(fs.statSync(p).isFile(),'regular file required');return p;
}
function documentUrl(value){
  const u=new URL(value);u.hash='';
  need(u.protocol==='http:'&&u.hostname==='127.0.0.1'&&u.pathname==='/index.html'&&!u.search&&!u.username&&!u.password,'unexpected document URL');
  return u.href;
}
function evidenceDirectory(out,allowMissing=false){
  out=path.resolve(out);
  for(let current=out;;current=path.dirname(current)){
    let stat;
    try{stat=fs.lstatSync(current);}
    catch(error){if(!(allowMissing&&current===out&&error.code==='ENOENT'))throw error;}
    if(stat)need(stat.isDirectory()&&!stat.isSymbolicLink(),'symlink or non-directory evidence ancestor is not admitted');
    if(path.dirname(current)===current)break;
  }
  // The original driver creates only the final output directory. Its parent
  // must already exist, and its canonical location cannot be an input alias.
  return path.join(fs.realpathSync(path.dirname(out)),path.basename(out));
}
function createInput({root,out}){
  root=fs.realpathSync(root);out=evidenceDirectory(out,true);
  need(out!==root&&!out.startsWith(root+path.sep),'evidence must remain outside the runtime');
  const derived=deriveIndex(fs.readFileSync(regular(root,'index.html')));
  const evidence={protocol:PROTOCOL,status:'PENDING',identity:derived.identity,producedBodies:[],responses:[],rejectedDocumentRequests:0,
    bounds:{documents:2,maxRetainedBodyBytes:ORIGINAL_BYTES},diskInitialSha256:ORIGINAL_SHA};
  const fail=message=>{evidence.status='INCOMPLETE';if(!evidence.failure)evidence.failure=String(message);throw Error('R003F preconnect input: '+message);};
  let guarded=false;
  function guardServer(server){
    const handlers=server.listeners('request');
    need(!guarded&&handlers.length===1,'one original request handler required');guarded=true;
    const original=handlers[0];server.removeListener('request',original);
    server.on('request',(request,response)=>{
      let resolved;
      try{const u=new URL(request.url,'http://127.0.0.1');resolved=fs.realpathSync(path.join(root,decodeURIComponent(u.pathname)));}catch{}
      if(resolved===path.join(root,'index.html')&&request.url!=='/index.html'){
        evidence.rejectedDocumentRequests=Math.min(3,evidence.rejectedDocumentRequests+1);
        try{fail('noncanonical document request refused before serving');}catch{}
        response.writeHead(404);response.end();return;
      }
      original.call(server,request,response);
    });
    return server;
  }
  function indexFor(variant){
    if(variant!=='B0')return fail('unsupported document variant');
    if(evidence.producedBodies.length>=2)return fail('document request population exceeded');
    evidence.producedBodies.push({ordinal:evidence.producedBodies.length+1,sha256:DERIVED_SHA,bytes:DERIVED_BYTES});
    return Buffer.from(derived.body);
  }
  function begin(expected){
    if(evidence.responses.length>=2)return fail('response population exceeded');
    const row={ordinal:evidence.responses.length+1,status:'INCOMPLETE',expectedUrl:documentUrl(expected)};
    evidence.responses.push(row);return row;
  }
  function recordNavigationFailure(error,expected){
    try{const row=begin(expected);row.navigationError=String(error?.message??error);evidence.status='INCOMPLETE';if(!evidence.failure)evidence.failure=row.navigationError;}
    catch(failure){evidence.status='INCOMPLETE';if(!evidence.failure)evidence.failure=String(failure.message);}
  }
  async function recordResponse(response,expected){
    const row=begin(expected);
    try{
      need(response&&typeof response.body==='function','document response is missing');
      row.url=String(response.url());row.httpStatus=response.status();row.contentType=String(response.headers()['content-type']??'');
      let body;
      try{body=await response.body();need(Buffer.isBuffer(body),'response body is not bytes');}
      catch(error){row.bodyReadError=String(error.message);throw error;}
      row.observedBodySha256=sha(body);row.observedBodyBytes=body.length;
      if(body.length>ORIGINAL_BYTES){row.retentionError='body retention limit exceeded';throw Error(row.retentionError);}
      const relative='document-input/document-'+String(row.ordinal).padStart(2,'0')+'.html';
      try{
        evidenceDirectory(out);
        const folder=path.join(out,'document-input');
        if(row.ordinal===1)fs.mkdirSync(folder,{mode:0o700});
        need(fs.lstatSync(folder).isDirectory()&&!fs.lstatSync(folder).isSymbolicLink(),'regular document retention directory required');
        const fd=fs.openSync(path.join(out,relative),'wx',0o600);
        try{fs.writeFileSync(fd,body);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
        row.body={path:relative,sha256:sha(body),bytes:body.length};
      }catch(error){row.retentionError=String(error.message);throw error;}
      need(documentUrl(row.url)===row.expectedUrl,'actual document URL differs');
      need(Number.isInteger(row.httpStatus)&&row.httpStatus===200,'document HTTP status differs');
      need(row.contentType==='text/html','document MIME differs');
      need(row.body.sha256===DERIVED_SHA&&row.body.bytes===DERIVED_BYTES,'actual response body identity differs');
      row.status='VERIFIED';return row;
    }catch(error){row.error=String(error.message);return fail(row.error);}
  }
  function assertComplete(){
    try{
      need(!evidence.failure,'an earlier document failure is retained');
      evidence.diskFinalSha256=sha(fs.readFileSync(regular(root,'index.html')));
      need(evidence.diskFinalSha256===ORIGINAL_SHA,'runtime index changed at completion');
      evidence.status='COMPLETE';return admitEvidence(evidence,out);
    }catch(error){return fail(String(error.message));}
  }
  return {evidence,indexFor,guardServer,recordResponse,recordNavigationFailure,assertComplete};
}
function admitEvidence(evidence,out){
  out=evidenceDirectory(out);
  need(evidence&&evidence.protocol===PROTOCOL&&evidence.status==='COMPLETE'&&!evidence.failure,'document evidence is incomplete');
  need(evidence.rejectedDocumentRequests===0,'noncanonical document requests were observed');
  need(equal(evidence.identity,identity())&&equal(evidence.bounds,{documents:2,maxRetainedBodyBytes:ORIGINAL_BYTES}),'document source identity or limits differ');
  need(evidence.diskInitialSha256===ORIGINAL_SHA&&evidence.diskFinalSha256===ORIGINAL_SHA,'runtime disk identity is unconfirmed');
  need(Array.isArray(evidence.producedBodies)&&evidence.producedBodies.length===2&&Array.isArray(evidence.responses)&&evidence.responses.length===2,'complete document population required');
  let origin;
  for(let i=0;i<2;i++){
    need(equal(evidence.producedBodies[i],{ordinal:i+1,sha256:DERIVED_SHA,bytes:DERIVED_BYTES}),'produced document differs');
    const r=evidence.responses[i],relative='document-input/document-'+String(i+1).padStart(2,'0')+'.html';
    need(r&&r.ordinal===i+1&&r.status==='VERIFIED'&&!r.error&&!r.navigationError&&!r.bodyReadError&&!r.retentionError,'response record is incomplete');
    need(r.httpStatus===200&&Number.isInteger(r.httpStatus)&&r.contentType==='text/html'&&documentUrl(r.url)===documentUrl(r.expectedUrl),'response transport identity differs');
    const u=new URL(r.url).origin;if(origin)need(u===origin,'document origins differ');else origin=u;
    need(equal(r.body,{path:relative,sha256:DERIVED_SHA,bytes:DERIVED_BYTES})&&r.observedBodySha256===DERIVED_SHA&&r.observedBodyBytes===DERIVED_BYTES,'retained document identity differs');
    const bytes=fs.readFileSync(regular(out,relative));need(bytes.length===DERIVED_BYTES&&sha(bytes)===DERIVED_SHA,'retained document bytes differ');
  }
  return {protocol:PROTOCOL,status:'COMPLETE',qualification:'ALTERED_INPUT_DIAGNOSTIC_ONLY',nativeAcceptance:'NOT_EVALUATED',humanAcceptance:'OUTSTANDING'};
}
function admitClosure(root,expected){
  need(typeof expected==='string'&&/^[0-9a-f]{64}$/.test(expected),'external materialization digest required');
  root=path.resolve(root);const bytes=fs.readFileSync(regular(root,'materialization.json'));need(sha(bytes)===expected,'external materialization digest differs');
  const body=JSON.parse(bytes);
  need(body.protocol===SOURCE_PROTOCOL&&body.status==='PREPARED'&&body.nativeExecution==='NOT_RUN','source materialization class differs');
  need(body.baseMaterializationSha256===BASE_MATERIALIZATION&&sha(JSON.stringify(body.baseMaterialization,null,2)+'\n')===BASE_MATERIALIZATION,'original corrected source identity differs');
  need(equal(body.documentInput,identity())&&equal(body.productFilesCopied,[])&&body.assetBytesChanged===false,'source document or product boundary differs');
  need(Array.isArray(body.outputFiles)&&body.outputFiles.length===OUTPUTS.length&&equal(body.outputFiles.map(x=>x.path).sort(),[...OUTPUTS].sort()),'source output closure differs');
  for(const row of body.outputFiles){const data=fs.readFileSync(regular(root,row.path));need(data.length===row.bytes&&sha(data)===row.sha256,'source output bytes differ: '+row.path);}
  const files=[];
  function walk(folder,prefix=''){for(const name of fs.readdirSync(folder)){const relative=prefix+name,p=path.join(folder,name),s=fs.lstatSync(p);need(!s.isSymbolicLink(),'source symlink is not admitted');if(s.isDirectory())walk(p,relative+'/');else {need(s.isFile(),'nonregular source member');files.push(relative);}}}
  walk(root);need(equal(files.sort(),[...OUTPUTS,'materialization.json'].sort()),'undeclared source members');
  return {protocol:SOURCE_PROTOCOL,status:'PREPARED',root,materializationSha256:expected,outputFiles:body.outputFiles,
    documentInput:body.documentInput,nativeExecution:'NOT_RUN'};
}
module.exports={ORIGINAL_SHA,DERIVED_SHA,ORIGINAL_BYTES,DERIVED_BYTES,PROTOCOL,SOURCE_PROTOCOL,SUCCESS,BASE_MATERIALIZATION,OUTPUTS,
  deriveIndex,createInput,admitEvidence,admitClosure};
