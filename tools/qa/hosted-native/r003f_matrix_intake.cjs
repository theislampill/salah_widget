'use strict';
// Supplemental selected-cell intake. Complete-eight acceptance alone uses the
// unchanged corrected original replay in a separately retained actual process.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process'),{parseArgs}=require('node:util');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function identity(r,root,expected,s){
 const S=require('./r003f_matrix_support.cjs');S.admitReceipt(r,{root,expectedSha256:expected,file:s.file,fixtureOnly:false});
 assert.equal(r.evidenceClass,'native');assert.equal(r.engine,s.engine);assert.equal(r.dpr,s.dpr);assert.equal(r.cell.id,s.id);
 const {cells}=require(path.join(root,'tools/qa/r003f_grid.cjs'));
 assert.deepEqual(r.cell,cells(s.engine,s.dpr).find(c=>c.id===s.id));
 const variants=require(path.join(root,'tools/qa/r003f_variants.cjs')).variants;
 assert.deepEqual(r.names,s.variant==='all'?variants:[s.variant]);
 const pins=require(path.join(root,'docs/state-contracts/evidence/R003F/publication-paths.json'));
 assert.equal(r.archiveIndexSha256,pins.indexSha256);
 const builds=[...new Set(['B0',...r.names,...r.names.map(n=>n.split('-')[0])])].map(n=>pins.builds.find(b=>b.variant===n));
 assert.deepEqual(r.builds,builds);
 for(const [field,name] of [['driver','playwright'],['decoder','pngjs']]){
  assert.deepEqual(r[field],{name,version:require(name+'/package.json').version,entrySha256:hash(fs.readFileSync(require.resolve(name)))});
 }
 assert.match(r.version,/^\d+(\.\d+)+/);return {S,pins};
}
function expectedCaptures(cell,names){
 const result=[];const add=(tag,name,admission,scenario=cell)=>result.push({tag,name,admission,scenario});
 if(cell.group==='ineligible'){for(const name of names)add(name,name,{tier:'inhibited'});}
 else if(['strap','buckle'].includes(cell.group)){
  for(const name of names)for(let i=0;i<cell.repeats;i++)for(const arm of ['repeat','candidate']){
   const label=name+'-'+i+'-'+arm;add(label+'-base','B0',{tier:'refined',offset:false,reference:false});
   add(label+'-target',arm==='repeat'?'B0':name,{tier:'refined',offset:false,reference:false});
  }
 }else{
  assert.notEqual(cell.group,'motion','motion intake is not enabled');
  for(const prefix of ['offset','b0','baseline-repeat'])for(const tier of ['initial','refined'])add(prefix+'-'+tier,'B0',{tier,offset:prefix==='offset',reference:false});
  add('reference','B0',{tier:'refined',offset:false,reference:true});
  for(const name of [...new Set([...names.map(n=>n.split('-')[0]),...names])])for(const tier of ['initial','refined'])add(name+'-'+tier,name,{tier,offset:false,reference:false});
  if(cell.group==='horizon'&&cell.alt>-2&&cell.alt<4)for(const name of names)add(name+'-minus2',name,{tier:'refined',offset:false,reference:false},{...cell,alt:-2});
 }
 return result;
}
function diagnostic(file,root,expected,selection){
 const r=JSON.parse(fs.readFileSync(file)),{S,pins}=identity(r,root,expected,{...selection,file});
 assert.notEqual(selection.variant,'all','selected diagnostic cannot satisfy complete-eight intake');assert.equal(r.status,'DIAGNOSTIC');
 assert.equal(r.tierDisposition,undefined);assert.equal(r.motionDisposition,undefined);
 const directory=fs.realpathSync(path.dirname(file)),artifacts=new Map();
 for(const [name,claim] of Object.entries(r.artifacts)){const bytes=S.regular(directory,name);assert.deepEqual(claim,{sha256:hash(bytes),bytes:bytes.length},'actual artifact differs: '+name);artifacts.set(name,bytes);}
 const {PNG}=require('pngjs'),{checkPair}=require(path.join(root,'tools/qa/r003f_capture.cjs'));
 const {fragment}=require(path.join(root,'tools/qa/r003f_grid.cjs'));
 const rows=expectedCaptures(r.cell,r.names),documents=new Map();let fixture=false;
 for(const tier of ['initial','refined'])if(r.captures['hidden-'+tier])rows.push({tag:'hidden-'+tier,name:'B0',admission:{tier,offset:false,reference:false,hidden:true},scenario:r.cell});
 assert.deepEqual(Object.keys(r.captures).sort(),rows.map(x=>x.tag).sort(),'selected capture population differs');
 for(const {tag,name,admission,scenario} of rows){
  const c=r.captures[tag];assert.deepEqual(c.admission,admission);checkPair(c.state,c.after,scenario,admission);
  const bytes=artifacts.get(tag+'.png');assert.ok(bytes);assert.equal(hash(bytes),c.sha256);
  const png=PNG.sync.read(bytes);assert.equal(png.width,325*r.dpr);assert.equal(png.height,530*r.dpr);
  const d=c.document;assert.ok(d&&Number.isSafeInteger(d.id)&&d.id>0);assert.equal(d.name,name);assert.equal(d.offset,!!admission.offset);
  assert.equal(d.responseSha256,pins.builds.find(b=>b.variant===name).indexSha256);
  const url=new URL(d.url);assert.equal(url.hostname,'127.0.0.1');assert.equal(url.pathname,'/index.html');assert.equal(url.searchParams.get('variant'),name);assert.equal(url.hash,fragment(scenario,!!admission.offset));
  if(documents.has(d.id))assert.deepEqual(documents.get(d.id),d);else documents.set(d.id,d);
  if(scenario.mode==='away')for(const [before,after] of [['before','after'],['detailBefore','detailAfter']])assert.ok(Math.abs(d.translation[after].y-d.translation[before].y-60)<1.1);
  if(c.state.weatherFixtureReads>0)fixture=true;
  if(c.boxes){
   for(const selector of ['.moccluder','.moon-detail-canvas','.buckle','.h','.e','.wt']){const b=c.boxes[selector];assert.ok(b&&[b.x,b.y,b.w,b.h].every(Number.isFinite)&&b.w>=0&&b.h>=0);}
   const b=c.boxes['.moccluder'],disc=c.state.disc;assert.ok(Math.abs(b.x+b.w/2-disc.cx)<.001&&Math.abs(b.y+b.h/2-disc.cy)<.001&&Math.abs(b.w/2-disc.r)<.001);
   if(c.state.detail?.visible)assert.ok(c.boxes['.moon-detail-canvas'].w>0&&c.boxes['.moon-detail-canvas'].h>0);
   if(scenario.mode==='long-text')assert.ok(Math.abs(c.boxes['.wt'].w-128)<.5);
   if(scenario.mode==='no-backdrop')assert.ok(['.wt','.e'].every(k=>['none',''].includes(c.boxes[k].filter)));
  }else assert.ok(tag.startsWith('hidden-')||r.cell.group==='ineligible');
  if(c.cloud){const raw=artifacts.get(tag+'-cloud.rgba');assert.ok(raw);assert.equal(hash(raw),c.cloud.sha256);assert.equal(raw.length,4*c.cloud.pixels);let n=0;for(let i=3;i<raw.length;i+=4)if(raw[i])n++;assert.equal(n,c.cloud.nonzeroAlpha);}
 }
 assert.ok(fixture,'original fixture consumption missing');
 const network=artifacts.get('network.jsonl').toString().split('\n').filter(Boolean).map(JSON.parse),net=r.network;
 assert.ok(network.length&&net.ok);assert.equal(net.seen,network.length);assert.deepEqual(net.escapes,[]);
 for(const k of ['allowedOffLoopback','refusedAtProxy','refusedByNodeGuard'])assert.equal(net[k],0);
 const origins=new Set([...documents.values()].map(d=>new URL(d.url).origin));assert.equal(origins.size,1);const [origin]=origins;
 for(const [i,n] of network.entries()){
  assert.equal(n.n,i);assert.ok(['continue','fulfill','abort'].includes(n.action));
  if(n.action==='fulfill')assert.equal(n.host,'api.aladhan.com');
  if(n.action==='continue')assert.ok(n.host==='127.0.0.1'&&new URL(n.url).origin===origin||/^(blob|data|about):/.test(n.url));
 }
 for(const [action,key] of [['continue','continued'],['fulfill','fulfilled'],['abort','aborted']])assert.equal(net[key],network.filter(n=>n.action===action).length);
 assert.ok(network.some(n=>n.action==='fulfill'&&n.host==='api.aladhan.com'));
 assert.ok(network.filter(n=>n.action==='continue'&&n.type==='document'&&n.url===origin+'/index.html').length>=documents.size);
 if(r.cell.gpu==='software'){
  if(r.engine==='chromium')assert.match(r.rasterization,/disabled|unavailable_software/);
  else if(r.engine==='firefox'){const b=artifacts.get('firefox-support.txt');assert.ok(b);assert.equal(hash(b),r.rasterization.sha256);assert.match(b.toString(),/WebRender \(Software\)/i);}
  else assert.fail('unsupported software trace');
 }
 return {status:'ADMITTED_MATRIX_DIAGNOSTIC',nativeAcceptance:'NOT_EVALUATED',originalStatus:r.status,
   captures:rows.length,documents:documents.size,artifacts:artifacts.size,
   scope:'Selected original capture/source/card/UI/image/network admission only. Numeric statistics are retained, not a complete-eight verifier result; human inspection remains outstanding.'};
}
function fullReplay(file,root,expected,pngjs,folder,seconds=600){
 fs.mkdirSync(folder,{mode:0o700});const argv=[process.execPath,path.join(root,'tools/qa/r003f_receipt.cjs'),pngjs,expected];
 const r=spawnSync(argv[0],argv.slice(1),{input:JSON.stringify([file]),encoding:'utf8',timeout:seconds*1000,maxBuffer:4*1024*1024});
 fs.writeFileSync(path.join(folder,'stdout'),r.stdout||'',{flag:'wx',mode:0o600});fs.writeFileSync(path.join(folder,'stderr'),r.stderr||'',{flag:'wx',mode:0o600});
 let rejections=null;try{rejections=JSON.parse(r.stdout);}catch(_){}
 const result={argv,cwd:process.cwd(),returncode:r.status,signal:r.signal,timedOut:r.error?.code==='ETIMEDOUT',error:r.error?.message||null,
   verifierSha256:hash(fs.readFileSync(argv[1])),expectedMaterializationSha256:expected,rejections,
   admitted:r.status===0&&!r.error&&Array.isArray(rejections)&&rejections.length===1&&rejections[0]===null};
 require('./r003f_matrix_entry.cjs').durable(path.join(folder,'process.json'),result);return result;
}
function run(request){
 const E=require('./r003f_matrix_entry.cjs');const iso=E.isolation(process.env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT);E.pins(request.pinsSha256);
 const sourceArgv=[request.python,path.join(__dirname,'r003f_matrix_campaign.py'),'admit','--entry',request.preparationEntry,'--pins-sha256',request.pinsSha256,'--native','--engine',request.selection.engine,'--dpr',String(request.selection.dpr),'--id',request.selection.id,'--variant',request.selection.variant];
 const check=spawnSync(sourceArgv[0],sourceArgv.slice(1),{cwd:__dirname,encoding:'utf8',timeout:90000,maxBuffer:4*1024*1024});
 E.durable(path.join(request.output,'source-process.json'),{argv:sourceArgv,returncode:check.status,timedOut:check.error?.code==='ETIMEDOUT',error:check.error?.message||null,stdout:check.stdout,stderr:check.stderr});
 assert.equal(check.status,0);assert.ok(!check.error);const current=JSON.parse(check.stdout);
 const d=JSON.parse(fs.readFileSync(request.driverReceipt));assert.equal(d.protocol,'R003F/matrix-driver/1');assert.equal(d.exitCode,0);assert.equal(d.process.returncode,0);assert.equal(d.process.timedOut,false);assert.equal(d.retentionError,null);assert.equal(d.error,undefined);
 assert.equal(d.sourceCheck.returncode,0);assert.equal(d.sourceCheck.timedOut,false);assert.equal(d.sourceCheck.error,null);assert.equal(d.originalDriverUnchanged,true);assert.equal(d.nativeSeconds,current.matrix.budget.nativeSeconds);assert.deepEqual(d.isolation,iso);assert.deepEqual(d.originalArgv,request.originalArgv);assert.deepEqual(d.selection,request.selection);assert.deepEqual(d.admission,current);
 const report=JSON.parse(fs.readFileSync(request.file));identity(report,request.root,request.materialization,{...request.selection,file:request.file});
 let result;
 if(request.selection.variant==='all'){
  const replay=fullReplay(request.file,request.root,request.materialization,request.pngjs,path.join(request.output,'original-replay'));
  assert.equal(replay.admitted,true,'original complete-eight replay failed');
  result={status:'VERIFIED_MATRIX_CAPTURE',nativeAcceptance:'ORIGINAL_COMPLETE_EIGHT_REPLAY_ONLY',originalStatus:report.status,replay};
 }else result=diagnostic(request.file,request.root,request.materialization,request.selection);
 return {...result,protocol:'R003F/matrix-intake/1',summary:{path:request.file,sha256:hash(fs.readFileSync(request.file))},
  driver:{path:request.driverReceipt,sha256:hash(fs.readFileSync(request.driverReceipt))},sourceAdmission:current,isolation:iso,humanAcceptance:'OUTSTANDING',noVariantUnion:true};
}
module.exports={identity,expectedCaptures,diagnostic,fullReplay,run};
if(require.main===module){
 const o=parseArgs({options:{request:{type:'string'}},strict:true}).values;
 try{const request=JSON.parse(fs.readFileSync(o.request)),result=run(request);process.stdout.write(JSON.stringify(result));}
 catch(e){process.stdout.write(JSON.stringify({protocol:'R003F/matrix-intake/1',status:'INCOMPLETE',error:{name:e.name,message:e.message,stack:e.stack}}));process.exitCode=e.exitCode||2;}
}
