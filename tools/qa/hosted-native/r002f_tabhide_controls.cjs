'use strict';
// Nonnative controls only. No Playwright import, display or browser launch.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),vm=require('node:vm');
const zlib=require('node:zlib'),{spawn,spawnSync}=require('node:child_process');
const {EventEmitter}=require('node:events');
const S=require('./r002f_tabhide_source.cjs');
const R=require('./r002f_tabhide_runtime.cjs');
const D=require('./r002f_tabhide.cjs');
const P=require('./r002f_probe.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));
function prayer(){
  const w=P.SCENARIOS[2].after,keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'],times=['05:00','06:00','12:00','15:30','18:00','19:30'];
  return {current:w.current,nextPrayer:w.nextPrayer,nextTime:w.nextTime,countdown:w.countdown,gregorian:w.gregorian,hijri:w.hijri,
    previewDay:w.previewDay,targetCounts:Object.fromEntries(['.cn','.nt','.left','.until-prayer','#ce','#ah','.bar>i','.arc','.times',
      '#dateGregorian','#dateHijri','#ceDateButton','#ahDateButton'].map(k=>[k,1])),
    calendar:{gregorian:w.gregorian,hijri:w.hijri,gregorianAria:'Show complete Gregorian date: '+w.gregorian,
      hijriAria:'Show complete Hijri date: '+w.hijri+'. Before Maghrib.'},progress:{width:w.progressWidth,visibility:'visible'},
    rows:keys.map((key,i)=>({key,label:key,time:times[i],roles:w.roles[i].split(' ').filter(Boolean)})),
    markers:keys.map((key,i)=>({key,next:key===w.nextPrayer,ring:key==='Sunrise',cx:i*30+5,cy:100,r:5})),
    arc:'<path d="M0 0"/>',currentRing:{count:2,cx:w.ringX,cy:80}};
}
function sample(at=0){return {hidden:false,paused:false,intersects:true,dpr:1,prayer:prayer(),
  clock:{protocol:'r002f-translated-date/1',rate:1,originUtc:S.CLOCK_UTC,originPerf:0,utc:S.CLOCK_UTC+at,perf:at,nativeCallbacks:true},
  sky:{status:'ready',physical:true,composed:true,displayed:true,displayedUtcMs:S.CLOCK_UTC,sunAltitude:-25},moon:{current:true,accepted:true,source:'refined-terrain',quality:'empirical-adaptive',identity:'controlled-model',phasePositionBudget:.0416}};}
const closedLifecycle=kind=>({protocol:'r002f-process-lifecycle/1',kind,cleanupRequested:true,closed:true,faults:[],overflow:false});
function row(mode='tabhide',arm='candidate'){
  const hidden=sample(100);hidden.hidden=true;hidden.paused=true;hidden.moon.current=false;hidden.moon.accepted=false;
  const png={width:400,height:650,encoding:'lossless-png',bytes:100,sha256:'a'.repeat(64)};
  return {protocol:'r002f-tabhide-row/1',arm,mode,contextClosed:true,cleanupError:null,error:null,completed:true,pageErrors:[],
    servedIndexSha256:arm==='baseline'?P.BASE_INDEX:P.COMBINED_INDEX,before:sample(1),settled:sample(1001),intendedHoldMs:250,
    lifecycleCustody:{page:closedLifecycle('page'),context:closedLifecycle('context')},
    clockCheck:{timerRan:true,rafRan:true,nativeCallbacks:true,performanceDeltaMs:50,dateDeltaMs:50},
    lifecycle:{protocol:'r002f-tabhide-lifecycle/1',clockDomain:'page-performance-now-ms',mode,limit:S.LIMITS.events,overflow:false,
      triggered:true,controlComplete:mode==='no-hide',
      events:mode==='tabhide'?[{type:'visibilitychange',trusted:true,at:100,sample:hidden},{type:'visibilitychange',trusted:true,at:400,sample:sample(400)}]:[],
      marks:['begin','trigger','callback-microtask','raf-1','raf-2','settled'].map((name,i)=>({name,at:[0,50,500,600,700,1000][i],sample:sample([0,50,500,600,700,1000][i])}))},
    route:'headed-chromium-bringToFront',frameBoundary:'first CDP PNG packet received after activation request began; not first displayed frame',
    capture:{protocol:'r002f-tabhide-frames/1',stopped:true,overflow:false,errors:[],limits:{frames:S.LIMITS.frames,bytes:S.LIMITS.bytes,frameBytes:S.LIMITS.frameBytes},
      received:2,bytes:200,frames:[{sequence:1,file:'frame-0001.png',phase:'before-action',hostNs:'1',metadata:{timestamp:1},acked:true,...png},
        {sequence:2,file:'frame-0002.png',phase:'activation-requested',hostNs:'2',metadata:{timestamp:2},acked:true,...png}]},firstCapturedFrame:'frame-0002.png',
    stills:{setup:{file:'setup.png',boundary:'mature setup before this schedule',...png},settled:{file:'settled.png',boundary:'later settled refined state; not first presented frame',...png}},
    ledger:{overflow:false,requests:[],unexpected:[],errors:[]}};
}
function crc(bytes){let c=0xffffffff;for(const byte of bytes){c^=byte;for(let k=0;k<8;k++)c=c&1?(c>>>1)^0xedb88320:c>>>1;}return (c^0xffffffff)>>>0;}
function png(){
  const chunk=(kind,data)=>{const k=Buffer.from(kind),n=Buffer.alloc(4),c=Buffer.alloc(4);n.writeUInt32BE(data.length);c.writeUInt32BE(crc(Buffer.concat([k,data])));return Buffer.concat([n,k,data,c]);};
  const header=Buffer.alloc(13);header.writeUInt32BE(400);header.writeUInt32BE(650,4);header[8]=8;header[9]=6;
  const scan=Buffer.alloc((400*4+1)*650);for(let y=0;y<650;y++)scan.fill(127,y*1601+1,(y+1)*1601);
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(scan)),chunk('IEND',Buffer.alloc(0))]);
}
const event=(data=png(),id=1)=>({data:data.toString('base64'),sessionId:id,metadata:{timestamp:id}});

test('all five exact source modules are checked before loading original owners',()=>{
  const record=S.admitSources();
  assert.equal(record.protocol,'r002f-tabhide-source/1');
  assert.deepEqual(Object.keys(record.modules).sort(),S.MODULES.slice().sort());
  assert.equal(Object.keys(record.modules).length,5);
});
test('source closure rejects an altered original helper without rebinding',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-source-'));
  try {
    for(const name of ['r002f-tabhide-pins.json',...S.MODULES])fs.copyFileSync(path.join(__dirname,name),path.join(dir,name));
    fs.appendFileSync(path.join(dir,'r002f_probe.cjs'),'\n// changed\n');
    assert.throws(()=>S.admitSources(dir),/source identity/);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('translated Date advances at one times native performance without replacing callbacks',()=>{
  let now=10;
  const sandbox={Date,performance:{now:()=>now},setTimeout:()=>1,clearTimeout:()=>{},
    setInterval:()=>2,clearInterval:()=>{},requestAnimationFrame:()=>3,cancelAnimationFrame:()=>{}};
  const original={...sandbox};vm.createContext(sandbox);
  vm.runInContext('('+R.installClock.toString()+')(10000)',sandbox);
  assert.equal(vm.runInContext('Date.now()',sandbox),10000);
  now=260;assert.equal(vm.runInContext('Date.now()',sandbox),10250);
  assert.equal(vm.runInContext('new Date().getTime()',sandbox),10250);
  assert.equal(vm.runInContext('new Date(17).getTime()',sandbox),17);
  for(const key of Object.keys(original).filter(k=>k!=='Date'))assert.equal(sandbox[key],original[key]);
  assert.equal(vm.runInContext('__r002fTabClock.read().nativeCallbacks',sandbox),true);
  assert.equal(vm.runInContext('typeof __r002fTabClock.set',sandbox),'undefined');
});

test('clock adapter detects replaced callbacks and preserves static Date operations',()=>{
  const box={Date,performance:{now:()=>30},setTimeout:()=>1,clearTimeout:()=>{},setInterval:()=>2,clearInterval:()=>{},requestAnimationFrame:()=>3,cancelAnimationFrame:()=>{}};
  vm.createContext(box);vm.runInContext('('+R.installClock.toString()+')(1000)',box);
  assert.equal(vm.runInContext('Date.parse("1970-01-01T00:00:02Z")',box),2000);
  assert.equal(vm.runInContext('typeof Date()',box),'string');
  box.requestAnimationFrame=()=>4;assert.equal(vm.runInContext('__r002fTabClock.read().nativeCallbacks',box),false);
});
test('source closure refuses omitted, duplicate-population and linked inputs',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-closure-'));
  try{
    for(const name of ['r002f-tabhide-pins.json',...S.MODULES])fs.copyFileSync(path.join(__dirname,name),path.join(dir,name));
    const file=path.join(dir,'r002f-tabhide-pins.json'),v=JSON.parse(fs.readFileSync(file));
    delete v.modules['browser-control.cjs'];fs.writeFileSync(file,JSON.stringify(v));assert.throws(()=>S.admitSources(dir),/population/);
    fs.copyFileSync(path.join(__dirname,'r002f-tabhide-pins.json'),file);
    fs.unlinkSync(path.join(dir,'browser-control.cjs'));fs.symlinkSync(path.join(__dirname,'browser-control.cjs'),path.join(dir,'browser-control.cjs'));
    assert.throws(()=>S.admitSources(dir),/symlink/);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('CLI fixes the selected engine, DPR, pair, section and maturity timeout',()=>{
  const base=['--playwright','/p','--baseline','/b','--candidate','/c','--out','/o'];assert.equal(D.parse(base).dpr,1);
  for(const [key,value] of [['engine','firefox'],['dpr','2'],['rounds','5'],['section','prayer'],['timeout-ms','60000']])
    assert.throws(()=>D.parse([...base,'--'+key,value]),/headed route/);
  assert.throws(()=>D.parse([...base,'--out','/z']),/repeated/);
});
test('entry refuses absent isolation before dependencies, display or private output creation',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-entry-'));
  try{
    const env={...process.env};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
    const result=spawnSync(process.execPath,[path.join(__dirname,'r002f_tabhide.cjs'),'--playwright',dir+'/missing',
      '--baseline',dir+'/main','--candidate',dir+'/candidate','--out',dir+'/output'],{encoding:'utf8',env,timeout:10000});
    assert.equal(result.status,86);assert.match(result.stderr,/R002F_TABHIDE ISOLATION_FAIL:.*native isolation receipt required/);assert.equal(fs.existsSync(dir+'/output'),false);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('malformed and mismatched isolation remain exit 86 before private output or dependencies',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-isolation-'));
  try{
    for(const [name,bytes] of [['malformed','{'],['mismatched',JSON.stringify({protocol:'salah-hosted-native-isolation/1',
      passed:true,uid:0,netns:'net:[incorrect]',outerNetns:'net:[other]',browserControl:{passed:true}})],['missing',null]]){
      const file=path.join(dir,name+'.json');if(bytes!==null)fs.writeFileSync(file,bytes);
      const result=spawnSync(process.execPath,[path.join(__dirname,'r002f_tabhide.cjs'),'--playwright',dir+'/missing-package',
        '--baseline',dir+'/main','--candidate',dir+'/candidate','--out',dir+'/output'],
        {encoding:'utf8',env:{...process.env,SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT:file},timeout:10000});
      assert.equal(result.status,86,name);assert.match(result.stderr,/R002F_TABHIDE ISOLATION_FAIL:/);
      assert.equal(fs.existsSync(dir+'/output'),false);
    }
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('argument and source failures retain exit 2 rather than being relabelled isolation',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-entry-source-'));
  try{
    const env={...process.env};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
    const argv=['--playwright',dir+'/missing','--baseline',dir+'/main','--candidate',dir+'/candidate','--out',dir+'/output'];
    const invalid=spawnSync(process.execPath,[path.join(__dirname,'r002f_tabhide.cjs'),...argv,'--engine','firefox'],{encoding:'utf8',env,timeout:10000});
    assert.equal(invalid.status,2);assert.match(invalid.stderr,/R002F_TABHIDE INCOMPLETE:/);
    for(const name of ['r002f-tabhide-pins.json',...S.MODULES])fs.copyFileSync(path.join(__dirname,name),path.join(dir,name));
    fs.appendFileSync(path.join(dir,'browser-control.cjs'),'\n// deliberately altered source\n');
    const changed=spawnSync(process.execPath,[path.join(dir,'r002f_tabhide.cjs'),...argv],{encoding:'utf8',env,timeout:10000});
    assert.equal(changed.status,2);assert.match(changed.stderr,/R002F_TABHIDE INCOMPLETE:.*source identity/);
    assert.equal(fs.existsSync(dir+'/output'),false);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('failed navigation or observer setup retains acquired evidence and both primary and cleanup errors',async()=>{
  for(const stage of ['navigation','observer'])for(const cleanupFails of [false,true]){
    const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-failed-scene-'));
    try{
      const context=new EventEmitter(),page=new EventEmitter();let closes=0,pageClosed=false;
      context.setDefaultTimeout=()=>{};context.addInitScript=async()=>{};
      context.route=async(_pattern,handler)=>{context.handler=handler;};context.routeWebSocket=async()=>{};
      context.newPage=async()=>page;page.isClosed=()=>pageClosed;
      page.goto=async()=>{
        await context.handler({request:()=>({url:()=> 'https://unexpected.invalid/setup'}),abort:async()=>{}});
        page.emit('pageerror',Error('retained setup page exception'));
        if(stage==='navigation')throw Error('original navigation setup failure');
        return {ok:()=>true,body:async()=>Buffer.from('controlled document')};
      };
      page.evaluate=async()=>{throw Error('original observer setup failure');};
      context.close=async()=>{closes++;pageClosed=true;page.emit('close');context.emit('close');if(cleanupFails)throw Error('separate cleanup failure');};
      const result=await D.arm({newContext:async()=>context},{origin:'http://127.0.0.1:1'},'baseline',dir,P);
      assert.equal(closes,1);assert.equal(result.entries.length,1);assert.equal(result.entries[0].verdict.status,'INCOMPLETE');
      const retained=JSON.parse(fs.readFileSync(path.join(dir,result.entries[0].file)));
      assert.match(retained.error,new RegExp('original '+stage+' setup failure'));
      assert.equal(retained.cleanupError===null,!cleanupFails);
      if(cleanupFails)assert.match(retained.cleanupError,/separate cleanup failure/);
      assert.deepEqual(retained.ledger.unexpected,['https://unexpected.invalid/setup']);
      assert.equal(retained.ledger.requests[0].action,'unexpected-aborted');
      assert.match(retained.pageErrors[0],/retained setup page exception/);
      assert.equal(retained.lifecycleCustody.page.faults[0].event,'pageerror');
      assert.equal(retained.lifecycleCustody.context.cleanupRequested,true);
      assert.equal(retained.contextClosed,true);assert.throws(()=>S.admitRow(retained),/completion/);
      assert.match(result.lifecycleCustody.setupError,new RegExp('original '+stage+' setup failure'));
      assert.equal(result.lifecycleCustody.cleanupError,retained.cleanupError);
    }finally{fs.rmSync(dir,{recursive:true,force:true});}
  }
});
test('maturity requires physical refined owners and preserves the original phase budget',()=>{
  S.mature(sample());
  for(const mutate of [s=>s.hidden=true,s=>s.paused=true,s=>s.intersects=false,s=>s.dpr=2,s=>s.sky.status='pending',s=>s.sky.composed=false,
    s=>s.sky.sunAltitude=2,s=>s.moon.source='initial-v5',s=>s.moon.quality='pending',s=>s.moon.phasePositionBudget=.05,s=>s.moon.identity='']){
    const s=sample();mutate(s);assert.throws(()=>S.mature(s));
  }
});
test('both arms and their no-hide controls admit only complete disclosed rows',()=>{
  for(const arm of ['baseline','candidate'])for(const mode of ['no-hide','tabhide'])assert.equal(S.admitRow(row(mode,arm)).status,'OBSERVED');
});
test('synthetic visibility events cannot stand in for native tab hiding',()=>{
  const r=row();r.lifecycle.events[0].trusted=false;assert.throws(()=>S.admitRow(r),/untrusted/);
});
test('missing, duplicated or reversed visibility records invalidate the route',()=>{
  for(const mutate of [r=>r.lifecycle.events.pop(),r=>r.lifecycle.events.push(clone(r.lifecycle.events[1])),r=>r.lifecycle.events.reverse()]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r));
  }
});
test('offscreen movement or a hidden property without actual pause does not qualify',()=>{
  for(const mutate of [r=>r.lifecycle.events[0].sample.hidden=false,r=>r.lifecycle.events[0].sample.paused=false,r=>r.lifecycle.events[0].sample.intersects=false]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r),/genuine tab/);
  }
});
test('the unchanged hidden-authority withdrawal remains a required observation',()=>{
  for(const key of ['accepted','current']){const r=row();r.lifecycle.events[0].sample.moon[key]=true;assert.throws(()=>S.admitRow(r),/withdraw/);}
});
test('no-hide control refuses actual visibility change or navigation',()=>{
  const r=row('no-hide');r.lifecycle.events=clone(row().lifecycle.events);assert.throws(()=>S.admitRow(r),/visibility/);
  const nav=row();nav.lifecycle.events.push({type:'pageshow',trusted:true,at:401,sample:sample(401),persisted:true});assert.throws(()=>S.admitRow(nav),/navigation/);
});
test('missing or duplicate next-frame samples cannot pass as callback completion',()=>{
  for(const mutate of [r=>r.lifecycle.marks.splice(3,1),r=>r.lifecycle.marks.push(clone(r.lifecycle.marks[4]))]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r),/callback sequence/);
  }
});
test('clock jumps, changed rate and a replaced callback are rejected without changing the 1000 ms owner fence',()=>{
  for(const mutate of [s=>s.utc+=1001,s=>s.rate=0,s=>s.nativeCallbacks=false]){
    const r=row();mutate(r.lifecycle.marks[2].sample.clock);assert.throws(()=>S.admitRow(r),/clock/);
  }
});
test('frozen timers and invented Date advancement cannot satisfy the live callback check',()=>{
  for(const mutate of [r=>r.clockCheck.timerRan=false,r=>r.clockCheck.rafRan=false,r=>r.clockCheck.performanceDeltaMs=0,r=>r.clockCheck.dateDeltaMs=0]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r),/callback check/);
  }
});
test('trace overflow, wrong clock domain and backwards callback time are inadmissible',()=>{
  for(const mutate of [r=>r.lifecycle.overflow=true,r=>r.lifecycle.clockDomain='host-wall-clock',r=>r.lifecycle.marks[3].at=-1]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r));
  }
});
test('original prayer structural checks reject missing, duplicated and blank actual targets',()=>{
  for(const mutate of [s=>delete s.targetCounts['.until-prayer'],s=>s.targetCounts['.nt']=2,s=>s.hijri='',s=>s.markers[5].key='Fajr']){
    const r=row();mutate(r.lifecycle.marks[2].sample.prayer);assert.throws(()=>S.admitRow(r));
  }
});
test('late context failures and page exceptions cannot retain an earlier success',()=>{
  for(const mutate of [r=>r.contextClosed=false,r=>r.cleanupError='close rejected',r=>r.pageErrors=['late runtime error']]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r),/completion/);
  }
});
test('late page crash and unexpected context close disqualify completed observations',()=>{
  for(const kind of ['page','context']){
    const target=new EventEmitter(),guard=D.watchLifecycle(target,kind,()=>true);
    if(kind==='page')target.emit('crash');else target.emit('close');
    guard.requestCleanup();target.emit('close');
    const r=row();r.lifecycleCustody[kind]=guard.state;
    assert.throws(()=>S.admitRow(r),/lifecycle custody/);
    assert.ok(guard.state.faults.length);
  }
});
test('late browser disconnect cannot be relabelled as requested cleanup',()=>{
  for(const delivered of [true,false]){
    const target=new EventEmitter();let connected=true;
    const guard=D.watchLifecycle(target,'browser',()=>connected);
    connected=false;if(delivered)target.emit('disconnected');
    guard.requestCleanup();target.emit('disconnected');
    assert.throws(()=>S.lifecycleCustody(guard.state,'browser'),/lifecycle custody/);
  }
});
test('requested cleanup is distinguished from faults and bounded late fault overflow',()=>{
  for(const kind of ['page','context','browser']){
    const target=new EventEmitter(),guard=D.watchLifecycle(target,kind,()=>true);
    guard.requestCleanup();target.emit(kind==='browser'?'disconnected':'close');S.lifecycleCustody(guard.state,kind);
    for(let i=0;i<40;i++)guard.fault('late-fault','controlled fault');
    assert.equal(guard.state.faults.length,32);assert.equal(guard.state.overflow,true);
    assert.throws(()=>S.lifecycleCustody(guard.state,kind),/lifecycle custody/);
  }
});
test('final intake rechecks live page guards after the earlier row was retained',()=>{
  const page=new EventEmitter(),guard=D.watchLifecycle(page,'page',()=>true);
  guard.requestCleanup();page.emit('close');
  const report={browserLifecycle:closedLifecycle('browser'),armLifecycles:['baseline','candidate'].map(arm=>({arm,
    setupError:null,cleanupError:null,page:closedLifecycle('page'),context:closedLifecycle('context'),pageErrors:[]}))};
  report.armLifecycles[1].page=guard.state;S.finalLifecycles(report);
  for(const key of ['setupError','cleanupError']){const failed=clone(report);failed.armLifecycles[0][key]='retained failure';assert.throws(()=>S.finalLifecycles(failed),/arm setup or cleanup failed/);}
  const earlier=clone(report);page.emit('crash');
  S.finalLifecycles(earlier);assert.throws(()=>S.finalLifecycles(report),/lifecycle custody/);
});
test('shared page clock orders the hide interval between trigger and restoration callbacks',()=>{
  for(const mutate of [r=>r.lifecycle.events[0].at=40,r=>r.lifecycle.events[1].at=501,
    r=>r.lifecycle.events[1].at=200,r=>r.intendedHoldMs=0,r=>r.lifecycle.triggered=false,
    r=>r.lifecycle.controlComplete=true]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r));
  }
  const control=row('no-hide');control.lifecycle.controlComplete=false;assert.throws(()=>S.admitRow(control));
  const short=row('no-hide');short.lifecycle.marks[2].at=100;assert.throws(()=>S.admitRow(short));
});
test('all samples share one immutable Date origin and native performance anchor',()=>{
  for(const get of [r=>r.before,r=>r.settled,r=>r.lifecycle.events[0].sample,r=>r.lifecycle.marks[3].sample]){
    const r=row(),clock=get(r).clock;clock.originPerf+=1;clock.utc-=1;
    assert.throws(()=>S.admitRow(r),/clock anchor/);
  }
  const r=row();r.lifecycle.marks[2].sample.clock=sample(499).clock;assert.throws(()=>S.admitRow(r),/sample precedes/);
});
test('final ledger includes late route errors, unknown traffic and explicit overflow',()=>{
  for(const mutate of [r=>r.ledger.requests.push({action:'route-error'}),r=>r.ledger.unexpected.push('https://unexpected.invalid'),r=>r.ledger.overflow=true]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r),/ledger/);
  }
});
test('a later or setup frame cannot replace the first captured activation packet',()=>{
  const r=row();r.firstCapturedFrame='frame-0001.png';assert.throws(()=>S.admitRow(r),/first captured/);
  r.firstCapturedFrame='frame-0002.png';r.frameBoundary='first displayed frame';assert.throws(()=>S.admitRow(r),/capture label/);
});
test('frame loss, missing acknowledgements and capture errors invalidate the complete claim',()=>{
  for(const mutate of [r=>r.capture.overflow=true,r=>r.capture.received++,r=>r.capture.frames[0].acked=false,r=>r.capture.errors=['write failed']]){
    const r=row();mutate(r);assert.throws(()=>S.admitRow(r));
  }
});
test('lossless PNG admission validates complete chunks, checksum, dimensions and decoded scanlines',()=>{
  const raw=png();assert.equal(S.pngInfo(raw).height,650);
  for(const bytes of [raw.subarray(0,raw.length-1),Buffer.concat([raw,Buffer.from([0])]),Buffer.from(raw)]){
    if(bytes.length===raw.length)bytes[60]^=1;assert.throws(()=>S.pngInfo(bytes));
  }
});
test('frame sink retains exact bytes before acknowledgement and finishes in receive order',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-frames-')),raw=png();let sink;const acks=[];
  try{
    sink=S.frameSink(dir,async id=>{assert.deepEqual(fs.readFileSync(path.join(dir,'frame-'+String(id).padStart(4,'0')+'.png')),raw);acks.push(id);});
    const a=sink.accept(event(raw,1),'before-action'),b=sink.accept(event(raw,2),'activation-requested');await Promise.all([a,b]);
    const final=await sink.finish();assert.deepEqual(acks,[1,2]);assert.equal(final.stopped,true);assert.equal(final.errors.length,0);
    assert.equal(final.frames[1].sha256,S.sha(raw));assert.equal(final.frames[1].acked,true);
    const journal=JSON.parse(fs.readFileSync(path.join(dir,'frame-0002.json')));
    assert.equal(journal.protocol,'r002f-tabhide-frame-journal/1');assert.equal(journal.recordState,'RETAINED_BEFORE_ACK');
    assert.equal(journal.acked,false);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('a later bound failure preserves the already queued lossless prefix',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-limit-'));const acks=[];
  try{
    const sink=S.frameSink(dir,async id=>acks.push(id),{...S.LIMITS,frames:1});
    await Promise.all([sink.accept(event(),'before-action'),sink.accept(event(png(),2),'activation-requested')]);const final=await sink.finish();
    assert.equal(final.overflow,true);assert.equal(final.frames.length,1);assert.equal(fs.existsSync(path.join(dir,'frame-0001.png')),true);
    assert.equal(fs.existsSync(path.join(dir,'frame-0002.png')),false);assert.deepEqual(acks,[1,2]);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('write failure and acknowledgement rejection retain completed frames and errors',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-partial-'));
  try{
    const sink=S.frameSink(dir,async id=>{if(id===1)throw Error('ack rejected');});
    await sink.accept(event(),'before-action');fs.writeFileSync(path.join(dir,'frame-0002.png'),'preexisting');
    await sink.accept(event(png(),2),'activation-requested');const final=await sink.finish();
    assert.equal(final.frames.length,1);assert.equal(final.frames[0].acked,false);assert.equal(final.errors.length,2);
    assert.deepEqual(fs.readFileSync(path.join(dir,'frame-0001.png')),png());assert.equal(fs.readFileSync(path.join(dir,'frame-0002.png'),'utf8'),'preexisting');
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('actual nonbrowser child cleanup kills and waits for its owned process',async()=>{
  const child=spawn(process.execPath,['-e','process.stdout.write("ready\\n");setInterval(()=>{},1000)'],{stdio:['ignore','pipe','pipe']});
  await new Promise((resolve,reject)=>{child.stdout.once('data',resolve);child.once('error',reject);});
  const info=D.processInfo(child.pid);assert.equal(D.sameLive(info),true);const closed=await D.closeProcess(child,info);
  assert.equal(closed.stopped,true);assert.equal(D.sameLive(info),false);assert.equal(closed.exit.signal,'SIGTERM');
});
test('external continuation is vetoed before invoking the real continue action',async()=>{
  let calls=0;const log=D.ledger(),route={request:()=>({url:()=> 'https://external.invalid/'}),continue:async()=>{calls++;}};
  await assert.rejects(D.continueLocal(route,'http://127.0.0.1:1',log),/vetoed/);assert.equal(calls,0);assert.equal(log.veto,true);
  route.request=()=>({url:()=> 'http://127.0.0.1:1/index.html'});await D.continueLocal(route,'http://127.0.0.1:1',log);assert.equal(calls,1);
});
test('headed boundary requires both native network outcomes and matching browser custody',()=>{
  const host={uid:1200,netns:'net:[22]',browserPid:42,executableSha256:'a'.repeat(64)},r={...host,
    protocol:'salah-hosted-browser-boundary/1',passed:true,headless:false,chromiumSandbox:true,loopbackRequests:2,
    externalNavigationError:'net::ERR_NETWORK_UNREACHABLE',postNegativePage:'fresh-page-same-browser',contextsClosed:true};S.boundary(r,host);
  for(const mutate of [x=>x.headless=true,x=>x.browserPid++,x=>x.contextsClosed=false,x=>x.externalNavigationError='ERR_TIMED_OUT',x=>x.loopbackRequests=1]){
    const x=clone(r);mutate(x);assert.throws(()=>S.boundary(x,host),/boundary/);
  }
});

test('actual page observer preserves trusted flags, read-only owners and two native callback boundaries',()=>{
  // Explicit DOM/event/clock boundary doubles exercise the observer body only.
  const listeners=new Map(),raf=[],micro=[];let at=0,hidden=false,paused=false,adoptions=0;
  const card={classList:{contains:key=>key==='paused'?paused:key==='real-sky-composed'},getBoundingClientRect:()=>({top:0,left:0,right:325,bottom:530})};
  const moon={observe:()=>({current:!hidden,accepted:!hidden,state:{visibleSource:'refined-terrain',quality:'empirical-adaptive',
    accepted:{identity:'controlled-model'},phasePrecision:{maximumPositionErrorDevicePixels:.0416}}})};
  for(const key of ['state','surface','detailEnabled'])Object.defineProperty(moon,key,{get(){adoptions++;throw Error('adopting access');}});
  const box={Date,performance:{now:()=>at++},innerHeight:650,innerWidth:400,devicePixelRatio:1,structuredClone,
    requestAnimationFrame:fn=>{raf.push(fn);return raf.length;},queueMicrotask:fn=>micro.push(fn),
    document:{get hidden(){return hidden;},get visibilityState(){return hidden?'hidden':'visible';},querySelector:()=>card,
      addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)},
    SalahMoonRuntime:moon,realSkyState:()=>({status:'ready',physical:true,displayed:{identity:'controlled',utcMs:S.CLOCK_UTC},last:{physicalState:{sun:{altDeg:-25}}}}),
    __r002fTabClock:{read:()=>sample(at).clock},addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
  box.window=box;vm.createContext(box);
  vm.runInContext('('+R.installObserver.toString()+')('+JSON.stringify('()=>('+JSON.stringify(prayer())+')')+')',box);
  box.__r002fTabObserver.begin('tabhide');box.__r002fTabObserver.trigger();
  hidden=true;paused=true;listeners.get('visibilitychange')({isTrusted:true,timeStamp:at});
  hidden=false;paused=false;listeners.get('visibilitychange')({isTrusted:true,timeStamp:at});
  assert.equal(raf.length,0);micro.shift()();assert.equal(raf.length,1);raf.shift()();assert.equal(raf.length,1);raf.shift()();
  box.__r002fTabObserver.settled();const trace=box.__r002fTabObserver.read();
  assert.deepEqual(Array.from(trace.marks,x=>x.name),['begin','trigger','callback-microtask','raf-1','raf-2','settled']);
  assert.deepEqual(Array.from(trace.events,x=>[x.trusted,x.sample.hidden]),[[true,true],[true,false]]);assert.equal(adoptions,0);
  box.__r002fTabObserver.dispose();assert.equal(listeners.size,0);
});
test('headed aggregate retains all four original maturity waits and discloses bounded overhead',()=>{
  assert.equal(S.BUDGET.evidenceWaitCeilingSeconds,4*(180+120));
  assert.equal(S.BUDGET.laneSeconds,S.BUDGET.evidenceWaitCeilingSeconds+S.BUDGET.remainingAggregateAllowanceSeconds);
  assert.equal(S.BUDGET.laneSeconds,1800);
});
test('private output refuses reused, source-contained or linked parent custody',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r2f-private-'));
  try{
    const protectedRoot=path.join(dir,'source');fs.mkdirSync(protectedRoot);
    fs.symlinkSync(protectedRoot,path.join(dir,'linked'));
    assert.throws(()=>S.privateRoot(path.join(dir,'linked','capture'),[]),/ancestor/);
    assert.throws(()=>S.privateRoot(path.join(protectedRoot,'capture'),[protectedRoot]),/outside/);
    const out=path.join(dir,'private','capture');assert.equal(S.privateRoot(out,[protectedRoot]),out);
    assert.equal(fs.statSync(out).mode&0o777,0o700);assert.throws(()=>S.privateRoot(out,[]),/fresh/);
    assert.equal(fs.existsSync(path.join(protectedRoot,'capture')),false);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});

// A declared read-only procfs double: these controls never launch a browser.
function procCensusIO(ids=['11','12']){
  const open=new Map(),closed=[];let next=1;
  const failures=new Map(),text=new Map(),links=new Map();
  links.set('/proc/self/ns/net','net:[controlled]');links.set('/proc/self/ns/pid','pid:[controlled]');
  for(const id of ids){
    links.set('/proc/'+id+'/exe','/controlled/chrome');
    links.set('/proc/'+id+'/ns/net','net:[controlled]');links.set('/proc/'+id+'/ns/pid','pid:[controlled]');
    text.set('/proc/'+id+'/cmdline',Buffer.from('/controlled/chrome\0--type=renderer\0'));
    text.set('/proc/'+id+'/status',Buffer.from('Name:\tcontrolled\nUid:\t1001\t1001\t1001\t1001\n'));
    text.set('/proc/'+id+'/stat',Buffer.from(id+' (controlled) S 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1234 0\n'));
  }
  function fail(name){if(failures.has(name))throw Object.assign(Error('controlled proc read'),{code:failures.get(name)});}
  return {failures,text,links,closed,open,
    readdirSync(name){fail(name);assert.equal(name,'/proc');return ['self','not-a-pid',...ids];},
    readlinkSync(name){fail(name);if(!links.has(name))throw Object.assign(Error('absent'),{code:'ENOENT'});return links.get(name);},
    openSync(name,flags){assert.equal(flags,'r');fail(name);if(!text.has(name))throw Object.assign(Error('absent'),{code:'ENOENT'});
      const fd=next++;open.set(fd,name);return fd;},
    readSync(fd,buffer,offset,length,position){const name=open.get(fd);fail('read:'+name);return text.get(name).copy(buffer,offset,position,position+length);},
    closeSync(fd){closed.push(fd);open.delete(fd);}
  };
}
test('failure-only proc census retains actual bounded fields without selecting an owner',()=>{
  const io=procCensusIO(),result=D.processCensus('/controlled/chrome',io);
  assert.equal(result.protocol,'r002f-headed-process-census/1');
  assert.equal(result.authority,'diagnostic-only; does not select or admit a browser owner');
  assert.equal(result.enumeration.truncated,false);assert.equal(result.rows.length,2);
  assert.equal(result.observer.netns.value,'net:[controlled]');
  assert.equal(result.rows[0].pid,11);assert.equal(result.rows[0].exe.value,'/controlled/chrome');
  assert.equal(result.rows[0].cmdline.value,'/controlled/chrome\0--type=renderer\0');
  assert.equal(result.rows[0].cmdline.truncated,false);assert.equal(io.open.size,0);assert.equal(io.closed.length,6);
  assert.equal('selectedPid' in result,false);
});
test('failure-only proc census retains EACCES and disappearing-process evidence',()=>{
  const io=procCensusIO();io.failures.set('/proc/11/exe','EACCES');io.failures.set('/proc/12/cmdline','ENOENT');
  const result=D.processCensus('/controlled/chrome',io);
  assert.equal(result.rows.length,2);assert.equal(result.rows[0].exe.errorCode,'EACCES');
  assert.equal(result.rows[0].cmdline.value,'/controlled/chrome\0--type=renderer\0');
  assert.equal(result.rows[1].cmdline.errorCode,'ENOENT');assert.equal(io.open.size,0);
});
test('failure-only proc census bounds process population and retained text prefixes',()=>{
  const io=procCensusIO(Array.from({length:258},(_,i)=>String(i+10)));
  io.text.set('/proc/10/cmdline',Buffer.alloc(20000,65));io.links.set('/proc/10/exe','x'.repeat(5000));
  const result=D.processCensus('/controlled/chrome',io);
  assert.deepEqual(result.limits,{processes:256,cmdlineBytes:16384,statusBytes:4096,statBytes:4096,linkCharacters:4096,readOperations:64});
  assert.equal(result.enumeration.numericEntries,258);assert.equal(result.enumeration.truncated,true);assert.equal(result.rows.length,256);
  assert.equal(result.rows[0].pid,10);assert.equal(result.rows[0].cmdline.value.length,16384);assert.equal(result.rows[0].cmdline.truncated,true);
  assert.equal(result.rows[0].exe.value.length,4096);assert.equal(result.rows[0].exe.truncated,true);assert.equal(io.open.size,0);
});
test('failure-only proc census closes descriptors even when a read fails',()=>{
  const io=procCensusIO(['11']);io.failures.set('read:/proc/11/status','EACCES');
  const result=D.processCensus('/controlled/chrome',io);
  assert.equal(result.rows[0].status.errorCode,'EACCES');assert.equal(io.open.size,0);assert.equal(io.closed.length,3);
});
test('failure-only proc census preserves enumeration failure as a diagnostic record',()=>{
  const io=procCensusIO();io.failures.set('/proc','EACCES');
  const result=D.processCensus('/controlled/chrome',io);
  assert.equal(result.enumeration.errorCode,'EACCES');assert.deepEqual(result.rows,[]);
  assert.equal(result.authority,'diagnostic-only; does not select or admit a browser owner');
});
test('short proc reads continue to EOF before claiming a complete field',()=>{
  const io=procCensusIO(['11']),read=io.readSync.bind(io);
  io.readSync=(fd,buffer,offset,length,position)=>read(fd,buffer,offset,Math.min(3,length),position);
  const result=D.processCensus('/controlled/chrome',io),row=result.rows[0].cmdline;
  assert.equal(row.value,io.text.get('/proc/11/cmdline').toString('utf8'));
  assert.equal(row.complete,true);assert.equal(row.eof,true);assert.equal(row.truncated,false);
  assert.ok(row.readCalls>1);assert.equal(io.open.size,0);
});
test('bounded repeated short reads retain an explicitly incomplete prefix',()=>{
  const io=procCensusIO(['11']),read=io.readSync.bind(io);
  io.text.set('/proc/11/cmdline',Buffer.alloc(20000,65));
  io.readSync=(fd,buffer,offset,length,position)=>read(fd,buffer,offset,Math.min(3,length),position);
  const result=D.processCensus('/controlled/chrome',io),row=result.rows[0].cmdline;
  assert.equal(row.value,'A'.repeat(192));assert.equal(row.complete,false);assert.equal(row.eof,false);
  assert.equal(row.truncated,null);assert.equal(row.readLimitReached,true);assert.equal(row.readCalls,64);
  assert.equal(io.open.size,0);
});
test('proc read errors retain previously read bytes and unknown completeness',()=>{
  const io=procCensusIO(['11']),read=io.readSync.bind(io);
  io.readSync=(fd,buffer,offset,length,position)=>{
    if(position>0)throw Object.assign(Error('controlled second read'),{code:'EACCES'});
    return read(fd,buffer,offset,3,position);
  };
  const result=D.processCensus('/controlled/chrome',io),row=result.rows[0].cmdline;
  assert.equal(row.value,'/co');assert.equal(row.bytesRead,3);assert.equal(row.errorCode,'EACCES');
  assert.equal(row.complete,false);assert.equal(row.truncated,null);assert.equal(io.open.size,0);
});
async function ownerSelectionControl(kind){
  // Exact main body; every browser/process operation below is an explicit double.
  let report,connected=true,enumerations=0;
  const options={out:'/controlled/output',playwright:'/controlled/playwright',baseline:'/controlled/baseline',candidate:'/controlled/candidate'};
  const host={uid:1001,netns:'net:[controlled]',pidns:'pid:[controlled]'};
  const browser={isConnected:()=>connected,close:async()=>{connected=false;},version:()=> 'controlled'};
  const scope={need:(value,message)=>{if(!value)throw Error(message);},path,Buffer,Set,console:{log(){}},__dirname,
    process:{env:{},exitCode:undefined},
    S:{admitSources:()=>({}),owners:()=>({}),privateRoot(){},identity:()=>({sha256:'controlled'}),generated:()=>({}),
      body:()=>JSON.stringify({version:'1.62.1'}),writeJson(p,value){report=clone(value);},BUDGET:{},STATUS:'OBSERVED_TABHIDE_DIAGNOSTIC'},
    parse:()=>options,nativeIsolation:()=>({isolationFile:'/controlled/isolation.json',host}),mainBrowserArgv:D.mainBrowserArgv,
    fs:{realpathSync:()=>'/controlled/chrome',readFileSync:p=>{
      if(kind==='second-read-fails'&&p==='/proc/12/cmdline')throw Object.assign(Error('controlled denied cmdline'),{code:'EACCES'});
      if((kind!=='second-read-fails'&&p==='/proc/12/cmdline'&&kind!=='two-main')||kind==='only-flattened')
        return '/controlled/chrome --type=zygote --user-data-dir=/controlled/profile\0';
      return '/controlled/chrome\0';}},
    require:()=>({chromium:{executablePath:()=>'/controlled/chrome',launch:async()=>{
      if(kind==='launch-fails')throw Error('controlled launch failure');return browser;}}}),
    startDisplay:async()=>({child:{},record:{display:':controlled',process:{}}}),
    browserPids:()=>++enumerations===1?[]:[11,12],watchLifecycle:()=>({state:{},requestCleanup(){}}),
    processInfo:pid=>({pid,...host,exe:kind==='identity-exe-changed'?'/other/chrome':'/controlled/chrome',
      sha256:kind==='identity-sha-changed'?'changed':'controlled',
      ...(kind==='identity-uid-changed'?{uid:1002}:{}),
      ...(kind==='identity-netns-changed'?{netns:'net:[other]'}:{}),
      ...(kind==='identity-pidns-changed'?{pidns:'pid:[other]'}:{}),
      argv:kind==='identity-becomes-flattened'?['/controlled/chrome --type=utility']:
        ['/controlled/chrome',...(kind==='identity-no-sandbox'?['--no-sandbox']:kind==='identity-headless'?['--headless=new']:[])]}),
    processCensus:()=>({evidenceClass:'synthetic-source-control'}),
    boundary:async()=>{throw Error('controlled stop before any native boundary');},
    bounded:async p=>await p,closeProcess:async()=>({stopped:true}),delay:async()=>{}};
  vm.createContext(scope);vm.runInContext('globalThis.mainUnderTest='+D.main.toString(),scope);
  await scope.mainUnderTest([]);return {report,exitCode:scope.process.exitCode};
}
test('owner selection retains completed candidate identities before a later read error',async()=>{
  const {report,exitCode}=await ownerSelectionControl('second-read-fails'),s=report.browserOwnerSelection;
  assert.deepEqual(s.mainPids,[11]);assert.deepEqual(s.observedPids,[11,12]);assert.equal(s.candidateScanComplete,false);
  assert.equal(s.phase,'candidate-cmdline');assert.equal(s.currentPid,12);assert.equal(s.candidateErrors[0].errorCode,'EACCES');
  assert.equal(s.admitted,false);assert.equal(report.status,'INCOMPLETE');assert.equal(exitCode,2);
});
test('failed browser launch leaves postlaunch observations absent',async()=>{
  const {report,exitCode}=await ownerSelectionControl('launch-fails'),s=report.browserOwnerSelection;
  assert.deepEqual(s.priorPids,[]);assert.equal('observedPids' in s,false);assert.equal('mainPids' in s,false);
  assert.equal(s.phase,'before-launch');assert.equal(s.admitted,false);assert.equal(report.status,'INCOMPLETE');assert.equal(exitCode,2);
});
test('main argv keeps exact executable and NUL argument boundaries without reparsing values',()=>{
  const executable='/controlled/browser path/chrome';
  for(const argv of [[executable], [executable,'--user-data-dir=/controlled/profile with spaces'],
    [executable,'--value=contains --type=renderer','--typeface=ordinary',' --type=literal-value']])
    assert.equal(D.mainBrowserArgv(argv,executable),true);
  for(const argv of [[], [''], [executable+' '], [' '+executable], ['/different/chrome'], [executable,null]])
    assert.equal(D.mainBrowserArgv(argv,executable),false);
  for(const value of ['--type','--type=','--type=renderer','--type= utility','--type=utility --other=value','--type=\nrenderer'])
    assert.equal(D.mainBrowserArgv([executable,value],executable),false);
});
test('flattened Chromium child titles are excluded for every whitespace and type value',()=>{
  const executable='/controlled/browser path/chrome';
  for(const separator of [' ','\t','\n','\r','\v','\f','\u00a0'])
    for(const value of ['zygote','utility','gpu-process','renderer','','unknown'])
      assert.equal(D.mainBrowserArgv([executable+separator+'--type='+value+' --user-data-dir=/controlled/profile'],executable),false);
  assert.equal(D.mainBrowserArgv([executable+' --no-startup-window'],executable),false);
});
test('exact main body excludes a flattened child and keeps the ordinary candidate',async()=>{
  const {report,exitCode}=await ownerSelectionControl('flattened-child');
  assert.deepEqual(report.browserOwnerSelection.mainPids,[11]);
  assert.equal(report.browserOwnerSelection.candidateScanComplete,true);
  assert.equal(report.browserOwnerSelection.admitted,true);
  assert.equal(report.browserProcess.pid,11);
  assert.match(report.errors[0],/controlled stop before any native boundary/);
  assert.equal(report.status,'INCOMPLETE');assert.equal(exitCode,2);
});
test('zero and multiple ordinary candidates retain exact-one failure and diagnostic-only census',async()=>{
  for(const [kind,pids] of [['only-flattened',[]],['two-main',[11,12]]]){
    const {report,exitCode}=await ownerSelectionControl(kind);
    assert.deepEqual(report.browserOwnerSelection.mainPids,pids);
    assert.equal(report.browserOwnerSelection.admitted,false);
    assert.equal(report.browserOwnerSelection.phase,'exact-one-owner');
    assert.equal(report.ownerFailureProcessCensus.evidenceClass,'synthetic-source-control');
    assert.match(report.errors[0],/one actual headed browser owner required/);
    assert.equal(report.status,'INCOMPLETE');assert.equal(exitCode,2);
  }
});
test('fresh owner identity rechecks argv and executable while preserving UID namespace and sandbox guards',async()=>{
  for(const kind of ['identity-becomes-flattened','identity-exe-changed','identity-sha-changed',
    'identity-uid-changed','identity-netns-changed','identity-pidns-changed','identity-no-sandbox','identity-headless']){
    const {report,exitCode}=await ownerSelectionControl(kind);
    assert.deepEqual(report.browserOwnerSelection.mainPids,[11]);
    assert.equal(report.browserOwnerSelection.phase,'owner-identity');
    assert.equal(report.browserOwnerSelection.admitted,false);
    assert.match(report.errors[0],/headed process identity differs/);
    assert.equal(report.status,'INCOMPLETE');assert.equal(exitCode,2);
  }
});
