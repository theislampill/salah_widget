'use strict';
// Offline source controls. All injected DOM, geometry, clocks and pixels below
// are synthetic. None is native layout, timing or product acceptance evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const M=require('./r003f_matrix_materialize.cjs');
const source=path.resolve(__dirname,'../../..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function temporary(t){const d=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-matrix-source-'));t.after(()=>fs.rmSync(d,{recursive:true,force:true}));return d;}
function prepared(t){const dir=temporary(t),out=path.join(dir,'derived'),receipt=M.materialize({source,out});return {dir,out,receipt,digest:sha(fs.readFileSync(path.join(out,'materialization.json')))};}
test('new matrix receipt binds fourteen published inputs and sixteen complete output bodies',t=>{
  const p=prepared(t);assert.equal(p.receipt.protocol,'R003F/corrected-matrix-harness/1');assert.equal(p.receipt.status,'PREPARED');
  assert.equal(p.receipt.sourceFiles.length,14);assert.equal(p.receipt.outputFiles.length,16);assert.equal(p.receipt.nativeExecution,'NOT_RUN');
  for(const f of p.receipt.outputFiles){const b=fs.readFileSync(path.join(p.out,f.path));assert.equal(sha(b),f.sha256);assert.equal(b.length,f.bytes);}
  assert.equal(fs.existsSync(path.join(p.out,'index.html')),false);assert.equal(JSON.stringify(p.receipt).includes(p.dir),false);
});
test('independent materializations are byte-identical and every JavaScript output compiles',t=>{
  const p=prepared(t),out=path.join(p.dir,'other');assert.deepEqual(M.materialize({source,out}),p.receipt);
  const scripts=p.receipt.outputFiles.filter(x=>/\.(?:cjs|mjs)$/.test(x.path));assert.equal(scripts.length,13);
  for(const s of scripts){const r=spawnSync(process.execPath,['--check',path.join(p.out,s.path)],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);}
});
const S=require('./r003f_matrix_support.cjs'),U=require('./r003f_ui.cjs');
const {createRequire}=require('node:module'),{EventEmitter}=require('node:events');
const {cells,fragment}=require('../r003f_grid.cjs'),{variants}=require('../r003f_variants.cjs');
const PNG=require(process.env.PNGJS_PATH||'pngjs').PNG;
const plain=x=>JSON.parse(JSON.stringify(x));
function copyInputs(target){for(const f of Object.keys(M.INPUTS)){const p=path.join(target,f);fs.mkdirSync(path.dirname(p),{recursive:true});fs.copyFileSync(path.join(source,f),p);}}
function syntheticUi(bad=false){
  const style={display:'block',visibility:'visible',contentVisibility:'visible',opacity:'1',position:'relative',fontSize:'12px',color:'rgb(240, 240, 240)'};
  const node=(x,y,w,h,text='',display='block')=>({text,rect:{left:x,top:y,right:x+w,bottom:y+h,width:w,height:h},style:{...style,display},ancestors:[style]});
  const o={coordinateSpace:'card-border-box-css-px',cardCount:1,card:node(0,0,325,530),header:[node(16,16,293,25,'','grid')],
    location:[node(20,19,90,18,'Synthetic location')],buckle:[node(150,16,25,25)],weather:[node(210,19,80,18,'21 C')],
    times:[node(16,300,293,192,'','grid')],footer:[node(16,500,293,17,'','flex')],gregorian:[node(26,500,125,17,'Synthetic date')],hijri:[node(190,500,109,17,'Synthetic date')],
    refinedCanvas:[{style:{position:'absolute'}}],previewCanvas:[{style:{position:'absolute'}}]};
  o.rows=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'].map((key,i)=>({...node(16,300+32*i,293,27,'','flex'),key,
    labels:[node(25,305+32*i,65,17,key)],times:[node(250,305+32*i,45,17,'5:15 AM')]}));
  if(bad)o.rows[0].times[0].text='';return U.admitNativeUi(o);
}
const goodUi=syntheticUi();assert.equal(goodUi.status,'PASS');
function syntheticState(cell,{offset=false,reference=false,tier='refined',hidden=false,minute=Date.parse(cell.epoch)/60000,altitude=cell.alt,ui=goodUi}={}){
  const d=new Date(minute*60000),wall=new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(d).split(':').map(Number);
  const phase=offset?.01:cell.fraction,up=Math.min(1,Math.max(0,(altitude+2)/6)),eligible=altitude>-2&&phase>.02;
  const light={eligible,...Object.fromEntries(['eligibility','illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'].map(k=>[k,0]))};
  const identity={epochMinute:minute,minute:wall[0]*60+wall[1],context:'28.54|-81.38|America/New_York'};
  const geometry={altitudeDeg:altitude,fresh:true,produced:identity,expected:identity,phaseFraction:phase,light};
  return {nativeUi:ui,card:[325,530],disc:{cx:150.5,cy:120.5,r:45},geometry,now:cell.epoch,motionReduced:cell.motion==='reduce',ready:true,composed:true,
    quality:tier==='initial'?'initial-v5':'empirical-adaptive',source:tier==='initial'?'initial-v5':'refined-terrain',profile:reference?'unboosted-v5-01':'calendar-neutral-v5-01',
    acceptedFraction:phase,nativeFraction:phase,waxing:cell.waxing,nativeWaxing:cell.waxing,up,moonAltitude:altitude,moonlightOpacity:0,light,beam:'0',
    calendarVisible:true,groupOpacity:1,featureOpacity:1,weatherCode:0,weatherFixtureReads:1,prayerLoaded:true,consumed:{status:'completed',fresh:true,observation:geometry},
    wx:{currentWeatherSource:(cell.group==='motion'?'forecast':'current')+' (Open-Meteo model estimate)'},presentable:true,visibility:hidden?['hidden','hidden']:['visible','visible'],
    detail:{visible:true},sunEl:-27,utcMs:minute*60000,weatherFields:{code:0,rh:55,vis:24000,cloud:0},displayMode:'physical'};
}
function pixels({offset=false,reference=false,hidden=false}={}){
  const data=Buffer.alloc(325*530*4,255);for(let i=0;i<325*530;i++){
    const x=i%325-150,y=Math.floor(i/325)-120,ramp=Math.min(1,Math.max(0,(x+2)/4));
    const code=offset||hidden||Math.hypot(x,y)>=45?24:Math.round(24+(reference?110:75)*ramp);
    for(let k=0;k<3;k++)data[4*i+k]=code;
  }return PNG.sync.write({width:325,height:530,data});
}
function actualFunctions(p,{mutate,afterError=false,writeError=false,styleError=false}={}){
  const output=path.join(p.dir,'capture');fs.mkdirSync(output);const report={captures:{},streams:[],retentionFaults:[]},lifecycle=S.createLifecycle(report);
  const cell=cells('chromium',1).find(c=>c.group==='phase'&&c.fraction===.5&&c.waxing),state=syntheticState(cell);
  if(mutate)mutate(state);let count=0;const raw=pixels(),calls=[];
  const page={close:async()=>{},waitForFunction:async()=>{},waitForTimeout:async()=>{},
    locator:()=>({screenshot:async()=>{calls.push('screenshot');return raw;}}),
    addStyleTag:async()=>({evaluate:async()=>{if(styleError)throw Error('controlled style cleanup failure');}}),
    evaluate:async fn=>{
      if(fn.name==='facts'){calls.push('facts');if(++count===2&&afterError)throw Error('controlled missing after-state');return plain(state);}
      const s=fn.toString();if(s.includes('detailAvailable'))return true;
      if(s.includes('cloudcanvas'))return {rgba:[24,24,24,0],covered:0};
      if(s.includes('Object.fromEntries'))return Object.fromEntries(['.moccluder','.moon-detail-canvas','.buckle','.e','.wt','.h'].map(k=>[k,k==='.moccluder'?{x:105.5,y:75.5,w:90,h:90,filter:'none'}:{x:140,y:15,w:25,h:25,filter:'none'}]));
      throw Error('unexpected controlled evaluate');
    }};
  const helper=require(path.join(p.out,'tools/qa/r003f_capture.cjs')),text=fs.readFileSync(path.join(p.out,'tools/qa/r003f_matrix.cjs'),'utf8');
  const extracts=[['async function shot(','\nasync function diff('],['async function hiddenFrame(','\nasync function optionalRefinement('],['async function ineligible(','\nasync function repetitions(']].map(([a,b])=>text.slice(text.indexOf(a),text.indexOf(b,text.indexOf(a)))).join('\n');
  const deps={support:S,report,lifecycle,cell,dpr:1,PNG,fs,path,assert,hash:sha,facts:helper.facts,checkPair:helper.checkPair,
    waitTier:async()=>{},write:(name,b)=>{if(writeError)throw Error('controlled disk retention failure');fs.writeFileSync(path.join(output,name),b);},documents:new WeakMap([[page,{id:1}]]),
    names:['B0'],open:async()=>page,inhibitedLightVerdict:require('../r003f_p1.cjs').inhibitedLightVerdict,
    fail:message=>{throw Object.assign(Error(message),{andon:true});}};
  const functions=Function('deps','const {'+Object.keys(deps).join(',')+'}=deps;\n'+extracts+'\nreturn {shot,hiddenFrame,ineligible};')(deps);
  return {...functions,page,state,report,lifecycle,output,raw,calls,cell};
}
function generatedDouble(p,{badUi=false,leak=false,afterError=false,cleanupError=false,disconnect=false}={}){
  const fixture=fs.readFileSync(path.join(source,'tests/r003f-matrix-fixture.cjs'),'utf8');
  const runtime=process.env.R003F_CONTROL_RUNTIME||source;
  const baseline=path.join(runtime,'index.html');assert.ok(fs.existsSync(baseline),'set R003F_CONTROL_RUNTIME to an independently prepared original baseline runtime');
  assert.equal(sha(fs.readFileSync(baseline)),require(path.join(source,'docs/state-contracts/evidence/R003F/publication-paths.json')).indexSha256,'actual pinned control runtime required');
  let body=fixture.replace("require('./r0033-fake-playwright.cjs')",'require('+JSON.stringify(path.join(source,'tests/r0033-fake-playwright.cjs'))+')')
    .replace("require('../tools/qa/r003f_variants.cjs')",'require('+JSON.stringify(path.join(source,'tools/qa/r003f_variants.cjs'))+')')
    .replace("require('node:path').resolve(__dirname,'..')",JSON.stringify(runtime));
  body=body.replace('          return state;','          state.nativeUi='+JSON.stringify(syntheticUi(badUi))+';\n          if('+JSON.stringify(afterError)+'&&++p.__factReads===2)throw Error("controlled missing after-state");\n          return state;');
  body=body.replace("const ctx=await newContext(options),newPage=ctx.newPage;","const ctx=await newContext(options),newPage=ctx.newPage;const closeContext=ctx.close;ctx.close=async()=>{if("+JSON.stringify(cleanupError)+")throw Error('controlled context cleanup');return closeContext();};");
  body=body.replace('let fraction=.5,','p.__factReads=0;let fraction=.5,');
  if(disconnect){
    body=body.replace('const b=await fake.chromium.launch(options),newContext=b.newContext;',"const b=await fake.chromium.launch(options),newContext=b.newContext;b.on=(event,fn)=>{if(event==='disconnected')b.__disconnect=fn;};const oldClose=b.close;b.close=async()=>{b.__disconnect?.();return oldClose();};");
    body=body.replace("if(fn.name==='facts'){","if(fn.name==='facts'){if(profile==='unboosted-v5-01')b.__disconnect?.();");
  }
  const driver=path.join(p.dir,'synthetic-playwright.cjs');fs.writeFileSync(driver,body);
  return {driver,runtime,env:{...process.env,NODE_PATH:path.dirname(require.resolve('pngjs/package.json'))+'/..',R003F_ENCODE_PNG:'1',R003F_FAKE:leak?'leak':''}};
}
function runEntry(t,options={}){
  const p=prepared(t),d=generatedDouble(p,options),out=path.join(p.dir,'entry');
  const id=cells('chromium',1).find(c=>c.group==='phase'&&c.fraction===.5&&c.waxing).id;
  const argv=[path.join(p.out,'tools/qa/r003f_matrix.cjs'),'--root',d.runtime,'--out',out,'--id',id,'--playwright',d.driver,'--pngjs',d.driver,'--materialization-sha256',p.digest];
  if(options.variant)argv.push('--variant',options.variant);
  const run=spawnSync(process.execPath,argv,{cwd:source,env:d.env,encoding:'utf8',timeout:45000,maxBuffer:1e6});
  const file=path.join(out,'summary.json');assert.ok(fs.existsSync(file),run.stdout+run.stderr);
  return {...p,out,file,report:JSON.parse(fs.readFileSync(file)),run};
}
test('each original input is pinned and drift refuses output creation',t=>{
  const dir=temporary(t),input=path.join(dir,'source');copyInputs(input);
  for(const relative of Object.keys(M.INPUTS)){
    const f=path.join(input,relative),bytes=fs.readFileSync(f);fs.appendFileSync(f,'\ncontrolled drift');
    assert.throws(()=>M.materialize({source:input,out:path.join(dir,'out')}),/source digest mismatch/);assert.equal(fs.existsSync(path.join(dir,'out')),false);fs.writeFileSync(f,bytes);
  }
});
test('input symlinks and reused or aliased output are refused without rewriting prior files',t=>{
  const dir=temporary(t),input=path.join(dir,'source');copyInputs(input);const relative=Object.keys(M.INPUTS)[0],f=path.join(input,relative),bytes=fs.readFileSync(f),real=path.join(dir,'real');
  fs.writeFileSync(real,bytes);fs.unlinkSync(f);fs.symlinkSync(real,f);assert.throws(()=>M.materialize({source:input,out:path.join(dir,'out')}),/symlink/);
  const p=prepared(t),before=fs.readFileSync(path.join(p.out,'materialization.json'));assert.throws(()=>M.materialize({source,out:p.out}),/already exists/);assert.deepEqual(fs.readFileSync(path.join(p.out,'materialization.json')),before);
  assert.throws(()=>M.materialize({source,out:path.join(source,'derived')}),/outside source/);
});
test('external digest and every member of the derived closure are independently checked',t=>{
  const p=prepared(t);assert.equal(S.admitClosure(p.out,p.digest).outputFiles.length,16);assert.throws(()=>S.admitClosure(p.out),/independent/);assert.throws(()=>S.admitClosure(p.out,'0'.repeat(64)),/digest/);
  for(const row of p.receipt.outputFiles){const f=path.join(p.out,row.path),bytes=fs.readFileSync(f);fs.appendFileSync(f,'\n');assert.throws(()=>S.admitClosure(p.out,p.digest),/digest/);fs.writeFileSync(f,bytes);}
  fs.writeFileSync(path.join(p.out,'unlisted.txt'),'extra');assert.throws(()=>S.admitClosure(p.out,p.digest),/exact materialized closure/);fs.unlinkSync(path.join(p.out,'unlisted.txt'));
  const f=path.join(p.out,p.receipt.outputFiles[0].path),bytes=fs.readFileSync(f),real=path.join(p.dir,'saved');fs.writeFileSync(real,bytes);fs.unlinkSync(f);fs.symlinkSync(real,f);assert.throws(()=>S.admitClosure(p.out,p.digest),/symlink/);
});
test('all six catalogue listings and the complete ordered eight variants are unchanged',t=>{
  const p=prepared(t);let count=0;
  for(const engine of ['chromium','firefox','webkit'])for(const dpr of [1,2]){
    const r=spawnSync(process.execPath,[path.join(p.out,'tools/qa/r003f_matrix.cjs'),'--list','--engine',engine,'--dpr',String(dpr)],{encoding:'utf8',maxBuffer:2e6});assert.equal(r.status,0,r.stderr);
    const got=JSON.parse(r.stdout);assert.deepEqual(got,cells(engine,dpr));count+=got.length;
  }
  assert.equal(count,761);assert.deepEqual(require(path.join(p.out,'tools/qa/r003f_variants.cjs')).variants,['B0','B0-T','B1c','B1c-T','B4','B4-T','B6','B6-T']);
});
test('corrected actual loopback server preserves stylesheet bytes and supplies CSS MIME',async t=>{
  const p=prepared(t),http=require('node:http'),server=require(path.join(p.out,'tools/qa/r003f_capture.cjs')).makeServer(p.out);
  await new Promise(r=>server.listen(0,'127.0.0.1',r));try{
    const result=await new Promise((resolve,reject)=>http.get({host:'127.0.0.1',port:server.address().port,path:'/real-sky/native-sky.css'},r=>{const chunks=[];r.on('data',b=>chunks.push(b));r.on('end',()=>resolve({mime:r.headers['content-type'],bytes:Buffer.concat(chunks)}));}).on('error',reject));
    assert.equal(result.mime,'text/css');assert.equal(sha(result.bytes),M.INPUTS['real-sky/native-sky.css']);
  }finally{await new Promise(r=>server.close(r));}
});
test('original physics, clock registration, transform rules and full-population intake are retained',t=>{
  const p=prepared(t),read=(base,f)=>fs.readFileSync(path.join(base,'tools/qa/'+f+'.cjs'),'utf8');
  for(const f of ['r003f_p1','r003f_grid','r003f_variants','r003f_diagnostics','r0033_isolation','v1_net_guard'])assert.equal(read(source,f),read(p.out,f));
  const a=read(source,'r003f_capture'),b=read(p.out,'r003f_capture');assert.equal(a.slice(a.indexOf('function checkState(')),b.slice(b.indexOf('function checkState(')));
  const c=read(source,'r003f_motion'),d=read(p.out,'r003f_motion');assert.equal(c.slice(c.indexOf('function startMotionClock('),c.indexOf('async function run(')),d.slice(d.indexOf('function startMotionClock('),d.indexOf('async function run(')));
  const e=read(source,'r003f_receipt'),f=read(p.out,'r003f_receipt');assert.equal(e.slice(e.indexOf('  if(fixtureOnly)'),e.indexOf('module.exports')),f.slice(f.indexOf('  if(fixtureOnly)'),f.indexOf('module.exports')));
  assert.ok(read(p.out,'r003f_matrix').includes("{timeout:150000,polling:200}"));assert.ok(d.includes('lead=30,minutes=50'));
});
test('actual transformed still capture retains raw pixels and both observations before acceptance',async t=>{
  const p=prepared(t),f=actualFunctions(p);await f.shot(f.page,'test','refined');assert.deepEqual(f.calls,['facts','screenshot','facts']);
  const r=f.report.captures.test;assert.equal(r.retention.status,'RETAINED');assert.deepEqual(fs.readFileSync(path.join(f.output,'test.png')),f.raw);assert.equal(S.uiVerdict(f.report).status,'PASS');
});
test('actual after-state failure retains raw capture and truthfully leaves after null',async t=>{
  const p=prepared(t),f=actualFunctions(p,{afterError:true});await assert.rejects(()=>f.shot(f.page,'test','refined'),/controlled missing after-state/);
  assert.equal(f.report.captures.test.after,null);assert.match(f.report.captures.test.afterError.message,/missing after-state/);assert.equal(fs.existsSync(path.join(f.output,'test.png')),true);
  const q=prepared(t),g=actualFunctions(q,{afterError:true,mutate:s=>{s.profile='controlled-wrong-profile';}});
  await assert.rejects(()=>g.shot(g.page,'both','refined'),/controlled-wrong-profile/);
  assert.match(g.report.captures.both.rejection.message,/controlled-wrong-profile/);assert.match(g.report.captures.both.afterError.message,/missing after-state/);
});
test('original physical Andon dominates invalid UI, missing after-state and retention failure',async t=>{
  for(const writeError of [false,true]){
    const p=prepared(t),f=actualFunctions(p,{afterError:true,writeError,mutate:s=>{s.light.beam=.01;s.nativeUi=syntheticUi(true);}});
    await assert.rejects(()=>f.shot(f.page,'test','refined'),e=>e.andon===true&&/physical light/.test(e.message));
    assert.equal(f.report.captures.test.after,null);assert.equal(f.report.captures.test.retention.status,writeError?'RETENTION_FAILED':'RETAINED');
    assert.equal(f.report.rejected.reason,'physical light while inhibited');
  }
});
test('ineligible pre-capture failure retains explicitly supplemental pixels without replacing the original gate',async t=>{
  const p=prepared(t),f=actualFunctions(p,{mutate:s=>{s.geometry.altitudeDeg=20;s.light.beam=.01;}});f.cell.mode='unavailable';f.state.ready=false;f.state.displayMode='surface-unavailable';
  await assert.rejects(()=>f.ineligible(),e=>e.andon===true);assert.equal(Object.keys(f.report.captures).length,0);
  const r=f.report.supplementalCaptures['supplemental-B0'];assert.equal(r.captureKind,'supplementary-after-original-failure');assert.match(r.originalError.message,/inhibited/);assert.equal(r.retention.status,'RETAINED');
});
test('hidden raw capture survives after-state and style cleanup faults without masking original failure',async t=>{
  const p=prepared(t),f=actualFunctions(p,{afterError:true,styleError:true,mutate:s=>{s.visibility=['hidden','hidden'];}});
  await assert.rejects(()=>f.hiddenFrame(f.page,{state:f.state},'refined'),/missing after-state/);
  assert.equal(f.report.captures['hidden-refined'].after,null);assert.equal(fs.existsSync(path.join(f.output,'hidden-refined.png')),true);assert.equal(f.report.lifecycle.faults[0].kind,'hidden-style-cleanup');
});
test('complete injected eight-variant entry replays all original evidence and stays non-native',t=>{
  const p=runEntry(t);assert.equal(p.run.status,0,p.run.stderr);assert.equal(p.report.status,'DIAGNOSTIC');assert.deepEqual(p.report.names,variants);
  const R=require(path.join(p.out,'..','derived/tools/qa/r003f_receipt.cjs'));
  R.replayFixture(p.file,PNG,p.digest);assert.equal(p.report.evidenceClass,'injected-diagnostic');assert.throws(()=>R.validate(p.file,PNG,p.digest));
  assert.throws(()=>R.replayFixture(p.file,PNG),/independent/);assert.throws(()=>R.replayFixture(p.file,PNG,'0'.repeat(64)),/digest/);
  for(const change of [r=>r.names=['B0'],r=>r.builds.pop(),r=>r.metrics.pop(),r=>r.captures['B1c-initial'].after=null,
    r=>r.harness.outputFiles.pop(),r=>{r.harnessUi.status='PASS';r.captures['B1c-initial'].state.nativeUi.observed.rows[0].times[0].text='';},
    r=>r.lifecycle.faults.push({kind:'late-fault'}),r=>r.lifecycle.pages.splice(1),r=>r.retentionFaults.push({path:'unretained'}),
    r=>r.captures['B1c-initial'].retention.status='RETENTION_FAILED',r=>r.captures['B1c-initial'].retention.bytes++]){
    const r=plain(p.report);change(r);fs.writeFileSync(p.file,JSON.stringify(r));assert.throws(()=>R.replayFixture(p.file,PNG,p.digest));
  }
  fs.writeFileSync(p.file,JSON.stringify(p.report));fs.writeFileSync(path.join(p.out,'unlisted.png'),'extra');assert.throws(()=>R.replayFixture(p.file,PNG,p.digest),/unlisted/);
});
test('selected B0 entry remains diagnostic and cannot satisfy unchanged full-cell intake',t=>{
  const p=runEntry(t,{variant:'B0'});assert.equal(p.run.status,0,p.run.stderr);assert.equal(p.report.status,'DIAGNOSTIC');assert.deepEqual(p.report.names,['B0']);
  assert.equal(Object.keys(p.report.captures).length,11);const R=require(path.join(p.out,'..','derived/tools/qa/r003f_receipt.cjs'));
  assert.throws(()=>R.replayFixture(p.file,PNG,p.digest));assert.throws(()=>R.validate(p.file,PNG,p.digest));
});
test('UI veto is deferred until original group completion and cannot hide later Andon',t=>{
  const ui=runEntry(t,{badUi:true});assert.equal(ui.run.status,2,ui.run.stderr);assert.equal(ui.report.status,'INCOMPLETE');assert.equal(ui.report.harnessUi.status,'INCOMPLETE');assert.equal(ui.report.metrics.length,16);
  const physical=runEntry(t,{badUi:true,leak:true});assert.equal(physical.run.status,4,physical.run.stderr);assert.equal(physical.report.status,'ANDON');assert.ok(physical.report.captures['B1c-initial']);assert.equal(physical.report.harnessUi.status,'INCOMPLETE');
});
test('actual entry preserves missing after-state, late disconnect and terminal cleanup failure as incomplete',t=>{
  const missing=runEntry(t,{afterError:true});assert.equal(missing.run.status,2,missing.run.stderr);assert.equal(missing.report.captures['offset-initial'].after,null);assert.equal(missing.report.status,'INCOMPLETE');
  const cleanup=runEntry(t,{cleanupError:true,variant:'B0'});assert.equal(cleanup.run.status,2,cleanup.run.stderr);assert.equal(cleanup.report.status,'INCOMPLETE');assert.ok(cleanup.report.lifecycle.faults.some(x=>x.kind==='cleanup'));
  const disconnected=runEntry(t,{disconnect:true,variant:'B0'});assert.equal(disconnected.run.status,2,disconnected.run.stderr);assert.equal(disconnected.report.status,'INCOMPLETE');assert.ok(disconnected.report.lifecycle.faults.some(x=>x.kind==='unexpected-browser-disconnect'));
});
test('page crash, unexpected closure and browser disconnect are observed while expected cleanup is quiet',async()=>{
  const report={evidenceClass:'native'},life=S.createLifecycle(report),browser=new EventEmitter();life.watchSession({browser});
  const p=new EventEmitter();p.close=async()=>p.emit('close');life.watchPage(p);p.emit('crash');p.emit('close');browser.emit('disconnected');
  assert.deepEqual(report.lifecycle.faults.map(f=>f.kind),['page-crash','unexpected-page-close','unexpected-browser-disconnect']);
  const clean={evidenceClass:'native'},l=S.createLifecycle(clean),b=new EventEmitter(),q=new EventEmitter();q.close=async()=>q.emit('close');l.watchSession({browser:b});l.watchPage(q);await q.close();
  await l.cleanup('session',async()=>b.emit('disconnected'));assert.deepEqual(clean.lifecycle.faults,[]);
});
test('final isolation overrides original Andon and cleanup faults and all cleanups are attempted',async t=>{
  for(const isolated of [true,false]){
    const dir=temporary(t),report={status:'ANDON',reason:'original physical Andon',captures:{},retentionFaults:[]},life=S.createLifecycle(report),calls=[];
    const session={close:async()=>{calls.push('session');},verdict:()=>({ok:!isolated}),ledger:{requests:[]}};
    const code=await S.finishMatrix({report,context:{context:{close:async()=>{calls.push('context');throw Error('cleanup failed');}}},session,
      server:{close:cb=>{calls.push('server');cb();}},out:dir,write:(n,b)=>fs.writeFileSync(path.join(dir,n),b),lifecycle:life});
    assert.deepEqual(calls,['context','session','server']);assert.equal(code,isolated?3:4);assert.equal(report.status,isolated?'ISOLATION FAIL':'ANDON');assert.equal(report.reason,'original physical Andon');
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'summary.json'))).status,report.status);
  }
});
async function motionRun(t,{fault=null}={}){
  const p=prepared(t),out=path.join(p.dir,'motion');fs.mkdirSync(out);fs.writeFileSync(path.join(out,'outside.jsonl'),'');
  const cell=cells('chromium',1).find(c=>c.group==='motion'),pins=require(path.join(source,'docs/state-contracts/evidence/R003F/publication-paths.json'));
  const report={protocol:S.REPORT_PROTOCOL,harness:S.admitClosure(p.out,p.digest),evidenceClass:'injected-diagnostic',driver:null,decoder:null,version:'synthetic-1.0',
    archiveIndexSha256:pins.indexSha256,cell,engine:'chromium',dpr:1,names:variants,builds:pins.builds,captures:{},pairs:[],metrics:[],retentionFaults:[]};
  const life=S.createLifecycle(report),documents=new WeakMap(),clock={value:1000},writes=[],requests=[],browser=new EventEmitter();life.watchSession({browser});
  const pngs={offset:pixels({offset:true}),reference:pixels({reference:true}),candidate:pixels()},module={exports:{}},motionFile=path.join(p.out,'tools/qa/r003f_motion.cjs');
  const localRequire=createRequire(motionFile),fileSystem={...fs,writeFileSync:(file,bytes,...args)=>{
    writes.push({file,time:clock.value});clock.value+=25;
    if(fault==='write'&&file.endsWith('000.png'))throw Error('controlled motion write failure');return fs.writeFileSync(file,bytes,...args);
  }};
  const req=name=>name==='node:perf_hooks'?{performance:{now:()=>clock.value}}:name==='node:fs'?fileSystem:localRequire(name);
  Function('require','module','exports',fs.readFileSync(motionFile,'utf8'))(req,module,module.exports);
  let serial=0;
  const facts=function facts(){};
  async function open(name,offset){
    const page=new EventEmitter();let anchor,started,mode,reference=false,reads=0;
    page.close=async()=>page.emit('close');page.waitForFunction=async()=>{if(fault==='setup')throw Error('controlled motion setup failure');};
    page.waitForTimeout=async ms=>{clock.value+=ms;};
    page.evaluate=async(fn,arg)=>{
      if(fn.name==='startMotionClock'){anchor=arg.epoch;started=clock.value;mode=arg.mode;return 0;}
      if(fn.name!=='facts'){if(fn.toString().includes("setProfile('reference')"))reference=true;return;}
      const elapsed=clock.value-started,bin=Math.floor(elapsed/1000),i=bin-30,minute=(anchor/60000)+bin,altitude=-3+i*.2;
      const state=syntheticState(cell,{offset,reference,minute,altitude});
      state.utcMs=minute*60000+(mode==='continuous'?100:0);
      const transform='synthetic-registered-transform';
      state.motionClock={anchorUtcMs:anchor,sampledRealMs:elapsed,rendered:transform,
        last:{mode,utcMs:state.utcMs,elapsedRealMs:bin*1000+(mode==='continuous'?100:0),altitude,up:state.up,transform},expected:{altitude,up:state.up,transform}};
      if(fault==='andon'){state.light.beam=.01;state.nativeUi=syntheticUi(true);}
      if(fault==='after'&&++reads===2)throw Error('controlled motion missing after-state');return state;
    };
    page.locator=()=>({screenshot:async()=>{clock.value+=2;return pngs[offset?'offset':reference?'reference':'candidate'];}});
    const url='http://127.0.0.1:12345/index.html?variant='+name+fragment(cell,offset);
    documents.set(page,{id:++serial,name,offset:!!offset,url,responseSha256:pins.builds.find(b=>b.variant===name).indexSha256});
    for(const row of [{action:'continue',host:'127.0.0.1',url:'http://127.0.0.1:12345/index.html',type:'document'},
      {action:'fulfill',host:'api.aladhan.com',url:'https://api.aladhan.com/v1/timings/03-11-2026',type:'fetch'}])requests.push({n:requests.length,...row});
    life.watchPage(page);return page;
  }
  let error;try{await module.exports.run({open,cell,names:variants,out,report,PNG,waitTier:async()=>{},facts,dpr:1,documents});report.status='DIAGNOSTIC';}
  catch(e){error=e;report.status=e.andon?'ANDON':'INCOMPLETE';report.reason=e.message;}
  const session={browser,close:async()=>browser.emit('disconnected'),ledger:{requests},verdict:()=>({ok:true,escapes:[],seen:requests.length,continued:serial,fulfilled:serial,aborted:0,allowedOffLoopback:0,refusedAtProxy:0,refusedByNodeGuard:0})};
  const exitCode=await S.finishMatrix({report,context:{context:{close:async()=>{}}},session,server:{close:cb=>cb()},out,
    write:(n,b)=>fs.writeFileSync(path.join(out,n),b),lifecycle:life});
  return {...p,capture:out,file:path.join(out,'summary.json'),report,error,exitCode,writes};
}
test('motion raw frame survives original physical Andon and writes follow original ended timestamp',async t=>{
  const p=await motionRun(t,{fault:'andon'});assert.equal(p.error.andon,true);assert.equal(p.exitCode,4);assert.equal(p.report.status,'ANDON');
  assert.equal(p.report.streams.length,1);const s=p.report.streams[0],f=s.frames[0];assert.equal(s.status,'INCOMPLETE');assert.equal(s.frames.length,1);assert.equal(f.retention.status,'RETAINED');
  assert.equal(fs.existsSync(path.join(p.capture,f.file)),true);assert.equal(f.started,450);assert.equal(f.ended,452);assert.equal(s.clip,null);assert.equal(p.report.harnessUi.status,'INCOMPLETE');
});
test('motion after-state transport failure retains exactly the acquired frame with null after',async t=>{
  const p=await motionRun(t,{fault:'after'}),s=p.report.streams[0];assert.match(p.error.message,/missing after-state/);assert.equal(p.exitCode,2);assert.equal(s.frames.length,1);
  assert.equal(s.frames[0].after,null);assert.match(s.frames[0].afterError.message,/missing after-state/);assert.equal(s.frames[0].retention.status,'RETAINED');assert.equal(s.clip,null);
});
test('motion retention failure records the attempted bytes and cannot report a completed stream',async t=>{
  const p=await motionRun(t,{fault:'write'}),s=p.report.streams[0];assert.equal(p.exitCode,2);assert.equal(s.frames.length,1);assert.equal(s.frames[0].retention.status,'RETENTION_FAILED');
  assert.equal(fs.existsSync(path.join(p.capture,s.frames[0].file)),false);assert.equal(p.report.retentionFaults.length,1);assert.equal(s.status,'INCOMPLETE');
});
test('motion setup failure keeps an empty attempted stream without invented frames or clips',async t=>{
  const p=await motionRun(t,{fault:'setup'});assert.equal(p.exitCode,2);assert.equal(p.report.streams.length,1);const s=p.report.streams[0];assert.deepEqual(s.frames,[]);
  assert.equal(s.clip,null);assert.equal(s.status,'INCOMPLETE');assert.match(s.error.message,/setup failure/);assert.deepEqual(p.report.clockStarts,{});
});
test('full eighteen-by-fifty synthetic motion passes actual local FFV1 encode probe decode and original replay',async t=>{
  for(const exe of ['ffmpeg','ffprobe']){const r=spawnSync(exe,['-version'],{encoding:'utf8'});assert.equal(r.status,0,'real local '+exe+' required; no download or native fallback');}
  const p=await motionRun(t);assert.equal(p.error,undefined,p.error?.stack);assert.equal(p.exitCode,0);assert.equal(p.report.status,'DIAGNOSTIC');assert.equal(p.report.streams.length,18);
  assert.equal(p.report.streams.reduce((n,s)=>n+s.frames.length,0),900);assert.equal(p.writes.length,900);assert.equal(p.report.harnessUi.checkedFrames,900);
  for(const stream of p.report.streams){assert.equal(stream.status,'CAPTURED');assert.equal(stream.frames.length,50);assert.equal(stream.cadence.oneCapturePerSecond,true);
    for(const [i,f] of stream.frames.entries()){assert.equal(f.started,1000*i+450);assert.equal(f.ended,1000*i+452);assert.equal(f.retention.status,'RETAINED');}}
  const R=require(path.join(p.out,'tools/qa/r003f_receipt.cjs'));R.replayFixture(p.file,PNG,p.digest);assert.throws(()=>R.validate(p.file,PNG,p.digest));
  const original=fs.readFileSync(p.file);const bad=plain(p.report);bad.streams.pop();fs.writeFileSync(p.file,JSON.stringify(bad));assert.throws(()=>R.replayFixture(p.file,PNG,p.digest));fs.writeFileSync(p.file,original);
  const first=p.report.streams[0].frames[0].file,bytes=fs.readFileSync(path.join(p.capture,first));fs.appendFileSync(path.join(p.capture,first),'changed');assert.throws(()=>R.replayFixture(p.file,PNG,p.digest),/unbound|digest/);fs.writeFileSync(path.join(p.capture,first),bytes);
  const clip=path.join(p.capture,p.report.streams[0].clip),saved=fs.readFileSync(clip);fs.writeFileSync(clip,Buffer.from('not an encoded clip'));
  const tampered=plain(p.report);tampered.artifacts[p.report.streams[0].clip]={sha256:sha(fs.readFileSync(clip)),bytes:fs.statSync(clip).size};fs.writeFileSync(p.file,JSON.stringify(tampered));assert.throws(()=>R.replayFixture(p.file,PNG,p.digest),/invalid motion clip/);
  fs.writeFileSync(clip,saved);fs.writeFileSync(p.file,original);
});
test('failed terminal retention cannot turn a completed acquisition into success or mask Andon',async t=>{
  for(const original of ['DIAGNOSTIC','ANDON']){
    const out=temporary(t),report={status:original,reason:'original',captures:{},retentionFaults:[]},lifecycle=S.createLifecycle(report);
    const result=await S.finishMatrix({report,lifecycle,out,context:{context:{close:async()=>{}}},session:{close:async()=>{},verdict:()=>({ok:true}),ledger:{requests:[]}},server:{close:cb=>cb()},
      write:()=>{throw Error('controlled final retention failure');}});
    assert.equal(result,original==='ANDON'?4:2);assert.equal(report.status,original==='ANDON'?'ANDON':'INCOMPLETE');assert.ok(report.lifecycle.faults.some(f=>f.kind==='summary-retention'));
  }
});
test('failed materialization retains exact partial output and refuses to repair or reuse it',t=>{
  const dir=temporary(t),out=path.join(dir,'partial'),write=fs.writeFileSync;let n=0;
  fs.writeFileSync=function(file,...args){if(String(file).startsWith(out+path.sep)&&++n===3)throw Error('controlled preparation write failure');return write.call(fs,file,...args);};
  try{assert.throws(()=>M.materialize({source,out}),/preparation write failure/);}finally{fs.writeFileSync=write;}
  assert.equal(S.filesUnder(out).length,2);assert.equal(fs.existsSync(path.join(out,'materialization.json')),false);const saved=S.filesUnder(out).map(f=>[f,sha(fs.readFileSync(path.join(out,f)))]);
  assert.throws(()=>M.materialize({source,out}),/already exists/);assert.deepEqual(S.filesUnder(out).map(f=>[f,sha(fs.readFileSync(path.join(out,f)))]),saved);
});
