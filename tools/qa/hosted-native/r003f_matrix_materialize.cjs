'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {parseArgs}=require('node:util');
const {readNativeUi,admitNativeUi}=require('./r003f_ui.cjs');
const PROTOCOL='R003F/corrected-matrix-harness/1';
const INPUTS=Object.freeze({
  'tools/qa/r003f_matrix.cjs':'abd1590e95fe4865373d1a5799252a54fa63b0a58b2f0460532f7bb7c0278c11',
  'tools/qa/r003f_motion.cjs':'1e9f0f4f05077d74e639417fd78b08b6b4434ed0c99d89c18a27b927b04ad99f',
  'tools/qa/r003f_receipt.cjs':'973d239ef191322e788880a963c180c5b85d45401eb13555c9b0513cc8765608',
  'tools/qa/r003f_capture.cjs':'af84f6c9de2534658ddc327618622a6b33803a141c026927a44890805317b982',
  'tools/qa/r003f_p1.cjs':'eaabdfa55a1043a701ef08643b7a304cce6bad217073f2d30f3c51ecc599d380',
  'tools/qa/r003f_grid.cjs':'532de10b100f3388b1fa677a4e61c1afdb221628c23c50b1229a2530ef1845a3',
  'tools/qa/r003f_variants.cjs':'9e517644780f9870d00c3513506f8e049219a122fcd18e1ba01a02be2f7fade1',
  'tools/qa/r003f_diagnostics.cjs':'3875326a6439ab9dc0cee009f364f69f878d1a0dcdbe6dba7ad40d1254923706',
  'tools/qa/r0033_isolation.cjs':'2aef5788ea21cf33a201348e2e4ab901c6d0a8d7c16251859411768cb4b8132a',
  'tools/qa/v1_net_guard.cjs':'2b00cb52a72384862156f7ba771bc5daedcb420780b05b84cf8366962b4affab',
  'moon/src/moon-calendar.mjs':'b508ea0a0bbc2a68039ba71bb4be75299cfa57bcb74992be1b1b0a0eddfad953',
  'tests/r0002-ordinary.json':'40c6412a36a4644ec9db9a5c92ae2e682aa22dfd6bac45be249886cfe7e76282',
  'real-sky/native-sky.css':'298a11d0d91a801de2e8f63b7e4997ff33d7a7423ebd0e4c8a0bbd5710f68f31',
  'docs/state-contracts/evidence/R003F/publication-paths.json':'9571d1b287f37599d6f7639c6d761440ad27f49778ec17d681048f1d11e42b0f'
});
const UI_SHA256='ccce93bcbe1bcd4834789e03ead8a2a104710e4955e05d57cc846ab4a341c82a';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function exactly(source,anchor,replacement,label){assert.ok(anchor&&source.split(anchor).length===2,'missing or repeated source anchor: '+label);return source.replace(anchor,()=>replacement);}
function nativeUiSource(){return 'function nativeUiReceipt(){\nconst readNativeUi='+readNativeUi.toString()+';\nconst admitNativeUi='+admitNativeUi.toString()+';\nreturn admitNativeUi(readNativeUi());\n}';}
// These functions are serialized into the disposable original entry. Their
// bindings are the original recipe's bindings plus the closed support helper.
async function matrixShot(p,tag,tier,options={}){
  const profile=options.reference?'unboosted-v5-01':'calendar-neutral-v5-01';
  await waitTier(p,tier,profile);await p.waitForTimeout(2500);
  const state=await p.evaluate(facts),image=await p.locator('.c').screenshot();
  const post=await support.readAfter(p,facts),after=post.value;
  const targetCell=options.cell||cell,admission={tier,offset:!!options.offset,reference:!!options.reference};
  const retained=support.retainCapture(report,tag,{state,after,afterError:post.error,admission,document:documents.get(p)},image,write);
  try{checkPair(state,after,targetCell,admission);}catch(e){
    retained.rejection=support.plainError(e);
    const original=e.andon||e.message!=='missing scene'?e:post.error||e;report.rejected={tag,state,after,reason:original.message};throw original;
  }
  support.requireRetained(retained);
  const decoded=PNG.sync.read(image);assert.equal(decoded.width,325*dpr);assert.equal(decoded.height,530*dpr);
  const cloud=await p.evaluate(()=>{
    const cv=document.querySelector('.cloudcanvas');
    if(!cv||cv.width<1||cv.height<1)return null;
    const g=cv.getContext('2d').getImageData(0,0,cv.width,cv.height),b=cv.getBoundingClientRect(),disc=document.querySelector('.moccluder').getBoundingClientRect();
    const data=[];let covered=0;
    for(let y=0;y<cv.height;y++)for(let x=0;x<cv.width;x++){
      const dx=b.left+(x+.5)*b.width/cv.width-disc.left-disc.width/2,dy=b.top+(y+.5)*b.height/cv.height-disc.top-disc.height/2;
      if(Math.hypot(dx,dy)>disc.width/2)continue;
      const i=(y*cv.width+x)*4;data.push(...g.data.subarray(i,i+4));if(g.data[i+3])covered++;
    }
    return {rgba:data,covered};
  });
  if(cloud)write(tag+'-cloud.rgba',Buffer.from(cloud.rgba));
  const cloudInfo=cloud&&{sha256:hash(Buffer.from(cloud.rgba)),pixels:cloud.rgba.length/4,nonzeroAlpha:cloud.covered};
  const boxes=await p.evaluate(()=>{const card=document.querySelector('.c').getBoundingClientRect();return Object.fromEntries(['.wt','.buckle','.e','.h','.moccluder','.moon-detail-canvas'].map(s=>{
    const e=document.querySelector(s),b=e.getBoundingClientRect();return [s,{x:b.x-card.x,y:b.y-card.y,w:b.width,h:b.height,filter:getComputedStyle(e).backdropFilter}];
  }));});
  if(cell.mode==='long-text')assert.ok(Math.abs(boxes['.wt'].w-128)<.5,'weather strap did not reach 128 px');
  if(cell.mode==='no-backdrop')assert.ok(['.wt','.e'].every(s=>['none',''].includes(boxes[s].filter)));
  Object.assign(retained,{boxes,cloud:cloudInfo});
  return {tag,state,pixels:decoded.data,cloud:cloudInfo,boxes};
}
async function matrixHiddenFrame(p,frame,tier){
  if(!await p.evaluate(()=>window.SalahMoonRuntime.observe().detailAvailable&&window.SalahMoonDetail?.state.visible))return null;
  const style=await p.addStyleTag({content:'.moon,.moon-detail-canvas{visibility:hidden!important}'});
  try{
    const before=await p.evaluate(facts),png=await p.locator('.c').screenshot(),post=await support.readAfter(p,facts),after=post.value;
    const admission={tier,offset:false,reference:false,hidden:true},tag='hidden-'+tier;
    const retained=support.retainCapture(report,tag,{state:before,after,afterError:post.error,admission,document:documents.get(p)},png,write);
    try{checkPair(before,after,cell,admission);}catch(e){retained.rejection=support.plainError(e);throw e.andon||e.message!=='missing scene'?e:post.error||e;}
    assert.deepEqual(before.disc,frame.state.disc);support.requireRetained(retained);
    return PNG.sync.read(png).data;
  }finally{try{await style.evaluate(e=>e.remove());}catch(e){lifecycle.fault('hidden-style-cleanup',e);}}
}
async function matrixIneligible(){
  for(const name of names){
    const p=await open(name,false,{hold:false});
    try{
      await p.waitForFunction(()=>window.qaState?.().cache.prayerLoaded && window.qaState?.().moonTruth?.lunarLight!=null,
        null,{timeout:150000});
      await p.waitForTimeout(2500);
      const f=await p.evaluate(facts);
      assert.ok(f.geometry.altitudeDeg>0 && f.motionReduced && f.prayerLoaded);
      if(cell.mode==='daylight')assert.ok(f.sunEl>=-3,'Sun did not reach the test regime');
      else assert.ok(!f.ready&&f.displayMode==='surface-unavailable'&&f.sunEl<-3,'missing-surface precondition');
      const v=inhibitedLightVerdict(f);
      if(v==='FAIL'||typeof f.beam==='string'&&f.beam.trim()&&Number.isFinite(Number(f.beam))&&Number(f.beam)!==0)fail('physical light with an inhibited source');
      assert.equal(v,'PASS');
      const png=await p.locator('.c').screenshot(),post=await support.readAfter(p,facts),after=post.value,admission={tier:'inhibited'};
      const retained=support.retainCapture(report,name,{state:f,after,afterError:post.error,admission,document:documents.get(p)},png,write);
      try{checkPair(f,after,cell,admission);}catch(e){retained.rejection=support.plainError(e);throw e.andon||e.message!=='missing scene'?e:post.error||e;}
      support.requireRetained(retained);
    }catch(e){
      if(!report.captures[name])await support.supplemental(p,{report,tag:'supplemental-'+name,facts,write,document:documents.get(p),originalError:e});
      throw e;
    }finally{await p.close();}
  }
}
function corrected(relative,bytes,patches){
  let source=bytes.toString('utf8');
  const patch=(name,anchor,replacement)=>{source=exactly(source,anchor,replacement,relative+' '+name);patches.push({path:relative,name,occurrences:1,preimageSha256:hash(anchor),postimageSha256:hash(replacement)});};
  const span=(name,start,end,replacement)=>{const at=source.indexOf(start),stop=source.indexOf(end,at+start.length);assert.ok(at>=0&&stop>at,'missing span '+name);patch(name,source.slice(at,stop),replacement);};
  if(relative==='tools/qa/r003f_capture.cjs'){
    patch('css-mime',"const types = {'.html':'text/html',","const types = {'.css':'text/css','.html':'text/html',");
    patch('ui-facts','function facts() {','function facts() {\n  const nativeUi=('+nativeUiSource()+')();');
    patch('ui-field','  return {motionClock:','  return {nativeUi,motionClock:');
  }
  if(relative==='tools/qa/r003f_matrix.cjs'){
    patch('support-import',"const iso=require('./r0033_isolation.cjs');","const iso=require('./r0033_isolation.cjs');\nconst support=require('./hosted-native/r003f_matrix_support.cjs');");
    patch('external-digest-option',"'pngjs','executable']","'pngjs','executable','materialization-sha256']");
    patch('external-closure',"const index=fs.readFileSync(path.join(root,'index.html'),'utf8')","const harness=support.admitClosure(path.resolve(__dirname,'../..'),a['materialization-sha256']);\nconst index=fs.readFileSync(path.join(root,'index.html'),'utf8')");
    patch('report-protocol',"const report={protocol:'R003F/P1/native-matrix/2',","const report={protocol:'R003F/P1/native-matrix-ui/1',harness,retentionFaults:[],");
    patch('lifecycle',"const write=(n,data)=>fs.writeFileSync(path.join(out,n),data);","const lifecycle=support.createLifecycle(report);\nconst write=(n,data)=>fs.writeFileSync(path.join(out,n),data);");
    span('raw-still-retention','async function shot(', '\nasync function diff(',matrixShot.toString().replace('matrixShot','shot'));
    span('raw-hidden-retention','async function hiddenFrame(', '\nasync function optionalRefinement(',matrixHiddenFrame.toString().replace('matrixHiddenFrame','hiddenFrame'));
    span('ineligible-retention','async function ineligible(', '\nasync function repetitions(',matrixIneligible.toString().replace('matrixIneligible','ineligible'));
    patch('browser-lifecycle',"session=await iso.launch(launcher,engine);report.version=session.browser.version();","session=await iso.launch(launcher,engine);lifecycle.watchSession(session);report.version=session.browser.version();");
    patch('page-lifecycle',"reducedMotion:cell.motion},{origin,fixture:prayer});","reducedMotion:cell.motion},{origin,fixture:prayer});\n    lifecycle.watchContext(context);");
    patch('deferred-ui',"    report.status=report.tierDisposition||report.motionDisposition?'PARTIAL'","    support.requireUi(report);\n    report.status=report.tierDisposition||report.motionDisposition?'PARTIAL'");
    span('terminal-priority','  finally{\n    try{if(context)await context.context.close();', '\n}\nmain().catch(',
      "  finally{\n    process.exitCode=await support.finishMatrix({report,context,session,server,out,write,lifecycle});\n    console.log(JSON.stringify({cell:cell.id,status:report.status,reason:report.reason}));\n    if(!session||report.lifecycle.faults.some(f=>f.kind==='cleanup'))process.exit(process.exitCode||2);\n  }");
  }
  if(relative==='tools/qa/r003f_motion.cjs'){
    patch('support-import',"const {checkPair,aperture,riseBracket}=require('./r003f_capture.cjs');","const {checkPair,aperture,riseBracket}=require('./r003f_capture.cjs');\nconst support=require('./hosted-native/r003f_matrix_support.cjs');");
    patch('retain-attempted-stream',"    const p=await open(name,offset,{hold:false});\n    const directory=path.join(out,label);fs.mkdirSync(directory,{mode:0o700});\n    const frames=[];\n    try{",
      "    const frames=[],result={label,mode,evidenceClass:motionEvidence[mode],status:'INCOMPLETE',frames,cadence:support.cadence(frames),clip:null,clipError:null};\n    report.streams.push(result);\n    const directory=path.join(out,label);let p;\n    try{\n      p=await open(name,offset,{hold:false});fs.mkdirSync(directory,{mode:0o700});");
    const begin="        const started=performance.now()-began,before=await p.evaluate(facts),bytes=await p.locator('.c').screenshot(),after=await p.evaluate(facts),ended=performance.now()-began;";
    const end="        frames.push({file:label+'/'+file,sha256:hash(bytes),minute,expected,started,ended,before,after,admission,registration,document:documents.get(p),altitude,disc:before.disc,up:before.up,beam:before.beam,why});";
    const at=source.indexOf(begin),last=source.indexOf(end,at);assert.ok(at>=0&&last>at);
    patch('retain-frame-after-original-timestamps',source.slice(at,last+end.length),[
      "        const started=performance.now()-began,before=await p.evaluate(facts),bytes=await p.locator('.c').screenshot();",
      "        const post=await support.readAfter(p,facts),after=post.value,ended=performance.now()-began;",
      "        const minute=before.consumed?.observation?.produced?.epochMinute,expected=startMinute+i,why=[];",
      "        const admission={minute:expected,tier:'refined',offset,reference},altitude=before.consumed?.observation?.altitudeDeg;",
      "        const file=String(i).padStart(3,'0')+'.png';",
      "        const frame={file:label+'/'+file,sha256:hash(bytes),minute,expected,started,ended,before,after,admission,registration:null,document:documents.get(p),altitude,disc:before.disc,up:before.up,beam:before.beam,why};",
      "        if(post.error)frame.afterError=support.plainError(post.error);frames.push(frame);",
      "        frame.retention=support.retainBytes(report,frame.file,bytes,(n,b)=>fs.writeFileSync(path.join(out,n),b));",
      "        try{checkPair(before,after,cell,admission);frame.registration=frameRegistration({before,after},expected,mode,epoch-lead*60000);}",
      "        catch(e){frame.rejection=support.plainError(e);if(e.andon)throw e;why.push((post.error||e).message);}",
      "        if(post.error)throw post.error;support.requireRetained(frame);",
      "        const decoded=PNG.sync.read(bytes);assert.equal(decoded.width,325*dpr);assert.equal(decoded.height,530*dpr);"
    ].join('\n'));
    patch('partial-stream-disposition',"    }finally{await p.close();}","    }catch(e){result.error=support.plainError(e);throw e;}\n    finally{if(p)await p.close();result.cadence=support.cadence(frames);}");
    const resultLine="    const result={label,mode,evidenceClass:motionEvidence[mode],frames,cadence:{startsMs:frames.map(f=>f.started),durationsMs:frames.map(f=>f.ended-f.started),oneCapturePerSecond:frames.every((f,i)=>f.started>=1000*i&&f.ended<1000*(i+1))},clip:clip.status===0?label+'/clip.mkv':null,clipError:clip.error?.message||clip.stderr||null};";
    patch('completed-stream-disposition',resultLine,"    Object.assign(result,{status:clip.status===0?'CAPTURED':'INCOMPLETE',clip:clip.status===0?label+'/clip.mkv':null,clipError:clip.error?.message||clip.stderr||null});");
    patch('stream-retained-once','    report.streams.push(result);summaries.set(label,result);return result;','    summaries.set(label,result);return result;');
  }
  if(relative==='tools/qa/r003f_receipt.cjs'){
    patch('support-import',"const {spawnSync}=require('node:child_process');","const {spawnSync}=require('node:child_process');\nconst support=require('./hosted-native/r003f_matrix_support.cjs');");
    patch('native-external-digest','function validate(file,PNG){return replay(file,PNG,false);}','function validate(file,PNG,expectedSha256){return replay(file,PNG,false,expectedSha256);}');
    patch('fixture-external-digest','function replayFixture(file,PNG){return replay(file,PNG,true);}','function replayFixture(file,PNG,expectedSha256){return replay(file,PNG,true,expectedSha256);}');
    patch('replay-external-digest','function replay(file,PNG,fixtureOnly){','function replay(file,PNG,fixtureOnly,expectedSha256){');
    patch('replay-closed-ui-admission',"  assert.equal(r.protocol,'R003F/P1/native-matrix/2');","  support.admitReceipt(r,{root:path.resolve(__dirname,'../..'),expectedSha256,file,fixtureOnly});");
    patch('cli-external-digest','try{validate(file,PNG);return null;}','try{validate(file,PNG,process.argv[3]);return null;}');
  }
  return Buffer.from(source);
}
function regularInput(root,relative){let current=root;for(const part of relative.split('/')){current=path.join(current,part);assert.equal(fs.lstatSync(current).isSymbolicLink(),false,'source symlink refused: '+relative);}assert.ok(fs.statSync(current).isFile());return fs.readFileSync(current);}
function materialize({source,out}){
  assert.ok(source&&out,'explicit source and out required');source=fs.realpathSync(source);out=path.resolve(out);
  assert.ok(out!==source&&!out.startsWith(source+path.sep),'output must be outside source');assert.equal(fs.existsSync(out),false,'output already exists');
  out=path.join(fs.realpathSync(path.dirname(out)),path.basename(out));assert.ok(out!==source&&!out.startsWith(source+path.sep),'output must be outside source');
  assert.equal(fs.existsSync(out),false,'output already exists');
  const inputs=new Map(),sourceFiles=[],outputFiles=[],patches=[],outputs=new Map();
  for(const [relative,expected] of Object.entries(INPUTS)){const bytes=regularInput(source,relative);assert.equal(hash(bytes),expected,'source digest mismatch: '+relative);inputs.set(relative,bytes);sourceFiles.push({path:relative,sha256:expected,bytes:bytes.length});}
  for(const [relative,bytes] of inputs){const next=corrected(relative,bytes,patches);outputs.set(relative,next);outputFiles.push({path:relative,originalSha256:INPUTS[relative],sha256:hash(next),bytes:next.length});}
  for(const name of ['r003f_ui.cjs','r003f_matrix_support.cjs']){const bytes=fs.readFileSync(path.join(__dirname,name));if(name==='r003f_ui.cjs')assert.equal(hash(bytes),UI_SHA256,'existing UI helper drift');const relative='tools/qa/hosted-native/'+name;outputs.set(relative,bytes);outputFiles.push({path:relative,originalSha256:null,sha256:hash(bytes),bytes:bytes.length});}
  const receipt={protocol:PROTOCOL,status:'PREPARED',sourceReference:'55d1b3edb66d2c35679707120b01ee1d3455e4a3',sourceAdmission:'exact per-file SHA-256; no claim that checkout HEAD was inspected',
    materializerSha256:hash(fs.readFileSync(__filename)),sourceFiles,outputFiles,patches,productFilesChanged:[],assetBytesChanged:false,nativeExecution:'NOT_RUN',
    scope:'original full matrix and motion research; selected variants remain diagnostic; no product or human acceptance'};
  fs.mkdirSync(out,{mode:0o700});
  // A failed write leaves its exact partial output for diagnosis. Existing
  // output is never reused or silently repaired, including failed preparation.
  for(const [relative,bytes] of outputs){const file=path.join(out,relative);fs.mkdirSync(path.dirname(file),{recursive:true,mode:0o700});fs.writeFileSync(file,bytes,{flag:'wx',mode:0o600});}
  fs.writeFileSync(path.join(out,'materialization.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});return receipt;
}
if(require.main===module){try{const {values}=parseArgs({options:{source:{type:'string'},out:{type:'string'}}});console.log(JSON.stringify(materialize(values),null,2));}
  catch(e){console.error(JSON.stringify({protocol:PROTOCOL,status:'INCOMPLETE',error:e.message}));process.exitCode=2;}}
module.exports={PROTOCOL,INPUTS,UI_SHA256,exactly,corrected,materialize};
