'use strict';
// Actual HTTP, source transformation, browser-function, and capture-path controls.
// The DOM and PNG boundary doubles below are not native layout or pixel evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const http=require('node:http'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const M=require('./r003f_materialize.cjs'),U=require('./r003f_ui.cjs');
const source=path.resolve(__dirname,'../../..'),original=require('../r003f_capture.cjs');
const p1=require('../r003f_p1.cjs'),keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const plain=o=>JSON.parse(JSON.stringify(o));
function temporary(t){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-harness-control-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));return dir;}
function prepared(t){const dir=temporary(t),out=path.join(dir,'corrected');const receipt=M.materialize({source,out});return {dir,out,receipt,helper:require(path.join(out,'tools/qa/r003f_capture.cjs'))};}
function copyInputs(dir){for(const relative of Object.keys(M.INPUTS)){const file=path.join(dir,relative);fs.mkdirSync(path.dirname(file),{recursive:true});fs.copyFileSync(path.join(source,relative),file);}}
async function response(makeServer,root){
  const server=makeServer(root);
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  try{return await new Promise((resolve,reject)=>{
    http.get({hostname:'127.0.0.1',port:server.address().port,path:'/real-sky/native-sky.css'},r=>{
      const chunks=[];r.on('data',b=>chunks.push(b));r.on('end',()=>resolve({status:r.statusCode,type:r.headers['content-type'],bytes:Buffer.concat(chunks)}));r.on('error',reject);
    }).on('error',reject);
  });}finally{await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));}
}

function dom(options={}){
  const nodes=[],style={display:'block',visibility:'visible',opacity:'1',position:'relative',zIndex:'1',fontSize:'12.5px',lineHeight:'16.7px',color:'rgba(255, 255, 255, 0.95)',overflow:'visible',transform:'none',contentVisibility:'visible',backdropFilter:'none'};
  function node(name,x,y,width,height,text='',display='block',parent=null){
    const n={name,textContent:text,parentElement:parent,tagName:'DIV',id:name,dataset:{},selectors:{},style:{...style,display},
      bounds:{x,y,left:x,top:y,width,height,right:x+width,bottom:y+height}};
    n.getBoundingClientRect=()=>({...n.bounds});n.getAttribute=k=>k==='data-prayer-key'?n.dataset.prayerKey??null:null;
    n.querySelectorAll=s=>n.selectors[s]??[];n.querySelector=s=>n.querySelectorAll(s)[0]??null;nodes.push(n);return n;
  }
  const card=node('card',0,0,325,530);card.style.overflow='hidden';card.classList={contains:()=>true};
  const shift=options.displaced?1200:0; // Arbitrary synthetic out-of-card displacement.
  const header=node('header',16,16+shift,293,25,'','grid',card);
  const location=node('location',20,19+shift,90,18,'Orlando','flex',header);
  const buckle=node('buckle',150,16+shift,25,25,'','grid',header);
  const weather=node('weather',210,19+shift,80,18,'21°C','flex',header);
  const times=node('times',16,300+shift,293,192,'','grid',card);
  const rows=keys.map((key,i)=>{
    const row=node('row-'+i,16,300+shift+32*i,293,27,'','flex',times);row.dataset.prayerKey=key;
    row.selectors.b=[node('label-'+i,25,305+shift+32*i,65,17,key,'block',row)];
    row.selectors['.tm']=[node('time-'+i,250,305+shift+32*i,45,17,['5:15 AM','6:40 AM','12:10 PM','3:20 PM','5:30 PM','6:50 PM'][i],'block',row)];
    return row;
  });
  const footer=node('footer',16,500+shift,293,17,'','flex',card);
  const gregorian=node('gregorian',26,500+shift,125,17,'Sunday, Nov 15','block',footer);
  const hijri=node('hijri',190,500+shift,109,17,'5 Jumada II 1448','block',footer);
  const canvas=node('refined-canvas',1,1,323,528,'','block',card);canvas.style.position=options.badCss?'static':'absolute';
  const preview=node('preview-canvas',1,1,323,528,'','none',card);preview.style.position=options.badCss?'static':'absolute';
  const moon=node('moon',100,100,90,90,'','block',card),features=node('features',100,100,90,90,'','block',moon);
  card.selectors={'.h':options.missingHeader?[]:[header],'.h .e':[location],'.h .buckle':[buckle],'.h .wt':[weather],
    '.times':[times],'.times .p':options.missingRow?rows.slice(0,-1):rows,'.d':[footer],'.d .ce':[gregorian],'.d .ah':options.missingFooter?[]:[hijri],
    '.real-sky-canvas':[canvas],'.real-sky-preview':[preview],'.moon':[moon],'.mfeatures':[features]};
  if(options.duplicateKey)rows[5].dataset.prayerKey='Fajr';
  if(options.emptyTime)rows[0].selectors['.tm'][0].textContent='—';
  if(options.hidden)times.style.opacity='0';
  if(options.readError)header.getBoundingClientRect=()=>{throw Error('controlled rectangle read failure');};
  const before=JSON.stringify(nodes.map(n=>({name:n.name,text:n.textContent,bounds:n.bounds,style:n.style,key:n.dataset.prayerKey})));
  for(const n of nodes){Object.freeze(n.bounds);Object.freeze(n.style);Object.freeze(n.dataset);Object.freeze(n.selectors);Object.freeze(n);}
  const context={document:Object.freeze({querySelectorAll:s=>s==='.c'?[card]:[],querySelector:s=>s==='.c'?card:s==='.moccluder'?moon:null}),
    getComputedStyle:n=>({...n.style,getPropertyValue:key=>key==='--moonbeam'?'0':key==='--moongrp'?'1':''}),
    window:{qaState:()=>({cache:{prayerLoaded:true},wxTruth:{rawCode:0}})},matchMedia:()=>({matches:true})};
  return {context,unchanged:()=>assert.equal(JSON.stringify(nodes.map(n=>({name:n.name,text:n.textContent,bounds:n.bounds,style:n.style,key:n.dataset.prayerKey}))),before)};
}
function observed(options={}){const fixture=dom(options);const value=plain(vm.runInNewContext('('+U.readNativeUi.toString()+')()',fixture.context));fixture.unchanged();return value;}
function receipt(options={}){return U.admitNativeUi(observed(options));}
function state(ui=receipt()){
  const light={eligible:false,...Object.fromEntries(['eligibility','illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'].map(k=>[k,0]))};
  return {nativeUi:ui,card:[325,530],now:'2026-11-15T09:42:00.000Z',motionReduced:true,ready:true,composed:true,
    quality:'empirical-adaptive',source:'refined-terrain',weatherCode:0,prayerLoaded:true,profile:'calendar-neutral-v5-01',
    moonAltitude:-81.9,nativeFraction:.314,acceptedFraction:.3141,nativeWaxing:true,waxing:true,displayMode:'refined-calendar',
    calendarVisible:true,moonGroup:'1',groupOpacity:1,featureOpacity:1,moonlightOpacity:0,light};
}
async function capturePath(t,corrected,{before=receipt(),after=receipt(),mutate,afterError=false}={}){
  const setup=prepared(t),filename=path.join(corrected?setup.out:source,'tools/qa/r003f_owner_baseline.cjs');
  const body=fs.readFileSync(filename,'utf8');
  const start=body.indexOf('async function capture(page,tag,report) {'),end=body.indexOf('\nasync function main()',start);
  assert.ok(start>=0&&end>start);
  const out=path.join(setup.dir,'capture');fs.mkdirSync(out,{mode:0o700});
  const raw=state(before);if(mutate)mutate(raw);
  const scope={assert,fs,path,Buffer,out,dpr:1,epoch:raw.now,digest:hash,calendarLightVerdict:p1.calendarLightVerdict,assertOwnerScene:p1.assertOwnerScene,
    facts:setup.helper.facts,nativeUiReceipt:setup.helper.nativeUiReceipt,assertNativeUi:U.assertNativeUi,
    PNG:{sync:{read:()=>({width:325,height:530,data:Buffer.alloc(4)})}}};
  const ctx=vm.createContext(scope);
  vm.runInContext(body.slice(start,end)+'\nglobalThis.captureUnderTest=capture;',ctx);
  const inRealm=value=>vm.runInContext('JSON.parse('+JSON.stringify(JSON.stringify(value))+')',ctx);
  const report={captures:{}},calls=[];
  const page={waitForFunction:async()=>{},waitForTimeout:async()=>{},locator:()=>({screenshot:async()=>{calls.push('screenshot');return Buffer.from('CONTROL-NOT-A-PNG');}}),
    evaluate:async fn=>{calls.push(fn.name);if(fn.name==='facts')return inRealm(raw);if(fn.name==='nativeUiReceipt'){if(afterError)throw Error('controlled post-capture transport failure');return inRealm(after);}throw Error('unexpected evaluate '+fn.name);}};
  let error;try{await scope.captureUnderTest(page,'b0',report);}catch(e){error=e;}
  return {error,report:plain(report),calls,pngRetained:fs.existsSync(path.join(out,'b0.png'))};
}

test('original actual HTTP server reproduces the CSS MIME defect without changing bytes',async()=>{
  const r=await response(original.makeServer,source);assert.equal(r.status,200);assert.equal(r.type,'application/octet-stream');
  assert.equal(r.bytes.length,1854);assert.equal(hash(r.bytes),M.INPUTS['real-sky/native-sky.css']);
});
test('corrected actual HTTP response is text/css with identical original bytes',async t=>{
  const p=prepared(t),r=await response(p.helper.makeServer,source);assert.equal(r.status,200);assert.equal(r.type,'text/css');
  assert.deepEqual(r.bytes,fs.readFileSync(path.join(source,'real-sky/native-sky.css')));
});
test('materialization is a closed six-helper copy with explicit original and corrected identities',t=>{
  const p=prepared(t);assert.equal(p.receipt.protocol,'R003F/corrected-harness/1');assert.equal(p.receipt.status,'PREPARED');
  assert.equal(p.receipt.sourceFiles.length,7);assert.equal(p.receipt.outputFiles.length,7);
  assert.equal(fs.existsSync(path.join(p.out,'index.html')),false);assert.equal(fs.existsSync(path.join(p.out,'real-sky')),false);
  for(const relative of M.COPIED){const row=p.receipt.outputFiles.find(r=>r.path===relative);assert.equal(row.sha256,hash(fs.readFileSync(path.join(p.out,relative))));
    assert.equal(row.originalSha256,M.INPUTS[relative]);if(!['tools/qa/r003f_capture.cjs','tools/qa/r003f_owner_baseline.cjs'].includes(relative))assert.equal(row.sha256,row.originalSha256);}
  assert.equal(p.receipt.nativeExecution,'NOT_RUN');assert.equal(p.receipt.matrixMotion,'NOT_INCLUDED');
  assert.ok(!JSON.stringify(p.receipt).includes(p.dir));assert.ok(!JSON.stringify(p.receipt).includes(source));
});
test('fresh repeated materializations have identical corrected bytes and receipts',t=>{
  const p=prepared(t),other=path.join(p.dir,'second'),second=M.materialize({source,out:other});assert.deepEqual(second,p.receipt);
});
test('wrong pinned input refuses preparation before creating output',t=>{
  const d=temporary(t),s=path.join(d,'source');copyInputs(s);fs.appendFileSync(path.join(s,M.COPIED[0]),'\n');
  assert.throws(()=>M.materialize({source:s,out:path.join(d,'out')}),/source digest mismatch/);assert.equal(fs.existsSync(path.join(d,'out')),false);
});
test('symlink input refuses preparation even when its bytes match',t=>{
  const d=temporary(t),s=path.join(d,'source');copyInputs(s);const file=path.join(s,M.COPIED[0]);fs.unlinkSync(file);fs.symlinkSync(path.join(source,M.COPIED[0]),file);
  assert.throws(()=>M.materialize({source:s,out:path.join(d,'out')}),/symlink/);
});
test('existing output and output inside source are refused without modifying either',t=>{
  const d=temporary(t),out=path.join(d,'existing');fs.mkdirSync(out);fs.writeFileSync(path.join(out,'sentinel'),'keep');
  assert.throws(()=>M.materialize({source,out}),/must not exist/);assert.equal(fs.readFileSync(path.join(out,'sentinel'),'utf8'),'keep');
  assert.throws(()=>M.materialize({source,out:path.join(source,'controlled-unwritten-output')}),/outside source/);
});
test('guarded source replacements reject absent and ambiguous anchors',()=>{
  assert.throws(()=>M.replaceExactly('abc','missing','replacement','control'),/exactly one/);
  assert.throws(()=>M.replaceExactly('anchor anchor','anchor','replacement','control'),/exactly one/);
});
test('actual serialized browser observation reads intact UI without mutations',()=>{
  const fixture=dom(),value=plain(vm.runInNewContext('('+M.browserReceiptSource()+')()',fixture.context));fixture.unchanged();
  assert.equal(value.status,'PASS');assert.deepEqual(value.observed.rows.map(r=>r.key),keys);assert.equal(value.observed.header[0].style.display,'grid');
});
test('actual copied facts function serializes with the UI reader and no host closure',t=>{
  const p=prepared(t),fixture=dom(),value=plain(vm.runInNewContext('('+p.helper.facts.toString()+')()',fixture.context));fixture.unchanged();
  assert.equal(value.nativeUi.status,'PASS');assert.equal(value.prayerLoaded,true);
});
for(const [name,options,reason] of [['complete-looking displaced UI',{displaced:true},/rectangle outside card/],['missing sixth prayer row',{missingRow:true},/expected six prayer rows/],['duplicate prayer identity',{duplicateKey:true},/six distinct prayer identities/],
  ['unpopulated prayer time',{emptyTime:true},/invalid displayed time/],['missing header',{missingHeader:true},/header: expected one/],['missing footer date',{missingFooter:true},/hijri: expected one/],
  ['hidden prayer ancestor',{hidden:true},/hidden or missing style/],['unpositioned CSS sky canvases',{badCss:true},/stylesheet positioning missing/]])test('UI admission rejects '+name,()=>{
  const r=receipt(options);assert.equal(r.status,'INCOMPLETE');assert.match(r.failures.join('; '),reason);assert.throws(()=>U.assertNativeUi(r),e=>e.code==='R003F_UI_INCOMPLETE');
});
test('observation read errors are retained as incomplete rather than hiding physics checks',()=>{
  const r=receipt({readError:true});assert.equal(r.status,'INCOMPLETE');assert.match(r.observed.observationError,/controlled rectangle read failure/);
});
test('forged PASS receipt does not admit displaced or missing observations',()=>{
  const r=receipt({displaced:true});r.status='PASS';r.failures=[];assert.throws(()=>U.assertNativeUi(r),e=>e.code==='R003F_UI_INCOMPLETE');
  assert.throws(()=>U.assertNativeUi({protocol:'R003F/native-ui/1',status:'PASS'}),e=>e.code==='R003F_UI_INCOMPLETE');
});
test('original actual B0 capture path admits the complete-looking displaced UI control',async t=>{
  const r=await capturePath(t,false,{before:receipt({displaced:true})});assert.equal(r.error?.message,undefined);assert.equal(r.pngRetained,true);
});
test('corrected actual B0 capture path admits clean before and after receipts',async t=>{
  const r=await capturePath(t,true);assert.equal(r.error?.message,undefined);assert.equal(r.report.captures.b0.nativeUiAfter.status,'PASS');
  assert.deepEqual(r.calls,['facts','screenshot','nativeUiReceipt']);
});
for(const arm of ['before','after'])test('corrected B0 retains '+arm+' displaced UI and PNG before rejecting',async t=>{
  const r=await capturePath(t,true,{[arm]:receipt({displaced:true})});assert.equal(r.error?.code,'R003F_UI_INCOMPLETE');assert.equal(r.pngRetained,true);
  assert.equal((arm==='before'?r.report.captures.b0.state.nativeUi:r.report.captures.b0.nativeUiAfter).status,'INCOMPLETE');
});
test('post-capture evaluation failure retains the PNG and incomplete receipt',async t=>{
  const r=await capturePath(t,true,{afterError:true});assert.equal(r.error?.code,'R003F_UI_INCOMPLETE');assert.equal(r.pngRetained,true);
  assert.match(r.report.captures.b0.nativeUiAfter.observed.observationError,/post-capture transport failure/);
});
test('original physical-light Andon takes precedence over an incomplete UI receipt',async t=>{
  const r=await capturePath(t,true,{before:receipt({missingRow:true}),afterError:true,mutate:s=>{s.light.beam=.001;}});
  assert.equal(r.error?.code,'R003F_ANDON');assert.equal(r.report.captures.b0.lightVerdict,'FAIL');assert.equal(r.pngRetained,true);
});
test('original scene assertion remains effective before UI admission',async t=>{
  const r=await capturePath(t,true,{before:receipt({missingRow:true}),mutate:s=>{s.profile='wrong-profile';}});
  assert.match(r.error?.message??'',/b0 profile/);assert.notEqual(r.error?.code,'R003F_UI_INCOMPLETE');
});
test('original shared physics checks and B0 assertion block remain byte-identical',t=>{
  const p=prepared(t),a=fs.readFileSync(path.join(source,'tools/qa/r003f_capture.cjs'),'utf8'),b=fs.readFileSync(path.join(p.out,'tools/qa/r003f_capture.cjs'),'utf8');
  assert.equal(a.slice(a.indexOf('function checkState('),a.indexOf('function aperture(')),b.slice(b.indexOf('function checkState('),b.indexOf('function aperture(')));
  const before=fs.readFileSync(path.join(source,'tools/qa/r003f_owner_baseline.cjs'),'utf8');
  const checks=before.slice(before.indexOf("  if(lightVerdict==='FAIL')"),before.indexOf('  return {state,pixels:decoded.data};'));
  assert.ok(fs.readFileSync(path.join(p.out,'tools/qa/r003f_owner_baseline.cjs'),'utf8').includes(checks));
});
test('both corrected helper files compile and the native report names the corrected harness',t=>{
  const p=prepared(t);
  for(const relative of ['tools/qa/r003f_capture.cjs','tools/qa/r003f_owner_baseline.cjs']){
    const run=spawnSync(process.execPath,['--check',path.join(p.out,relative)],{encoding:'utf8'});assert.equal(run.status,0,run.stderr);
  }
  const driver=fs.readFileSync(path.join(p.out,'tools/qa/r003f_owner_baseline.cjs'),'utf8');
  assert.ok(driver.includes("harness:{protocol:'R003F/corrected-harness/1'"));
  assert.ok(driver.includes('materializationSha256:'));assert.ok(driver.includes('driverSha256:'));
});
test('CLI requires explicit roots and returns a real private materialization receipt',t=>{
  const d=temporary(t),script=path.join(__dirname,'r003f_materialize.cjs');
  assert.equal(spawnSync(process.execPath,[script],{encoding:'utf8'}).status,2);
  const out=path.join(d,'cli'),run=spawnSync(process.execPath,[script,'--source',source,'--out',out],{encoding:'utf8'});
  assert.equal(run.status,0,run.stderr);const r=JSON.parse(run.stdout);assert.equal(r.status,'PREPARED');
  assert.deepEqual(r,JSON.parse(fs.readFileSync(path.join(out,'materialization.json'))));
  if(process.platform!=='win32'){assert.equal(fs.statSync(out).mode&0o077,0);assert.equal(fs.statSync(path.join(out,'materialization.json')).mode&0o077,0);}
});
