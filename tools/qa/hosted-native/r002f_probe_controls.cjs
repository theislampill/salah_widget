'use strict';
// Controls exercise the probe's actual admission predicates. They do not emulate
// native layout, intersection delivery, the compositor, or product acceptance.
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawnSync} = require('node:child_process');
const crypto = require('node:crypto');
const P = require('./r002f_probe.cjs');

const keys = ['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
const times = ['05:00','06:00','12:00','15:30','18:00','19:30'];
const clone = value => structuredClone(value);
const expected = {
  current:'Fajr', nextPrayer:'Sunrise', nextTime:'06:00', countdown:'58m left until Sunrise',
  gregorian:'2026-09-07', hijri:'1448-02-25', previewDay:'26', progressWidth:'2.5%',
  roles:['now','on','','','',''],ringX:62.52125
};
const initial = {
  current:'Isha', nextPrayer:'Fajr', nextTime:'05:00', countdown:'30s left until Fajr',
  gregorian:'2026-09-07', hijri:'1448-02-25', previewDay:'26', progressWidth:'99.9%',
  roles:['on','','','','','now'],ringX:62.11514
};
const scenario = {name:'fajr', beforeUtc:Date.parse('2026-09-07T04:59:30Z'),
  afterUtc:Date.parse('2026-09-07T05:01:30Z'), before:initial, after:expected};
function sample(want=expected) {
  return {
    current:want.current,nextPrayer:want.nextPrayer,nextTime:want.nextTime,countdown:want.countdown,
    gregorian:want.gregorian,hijri:want.hijri,previewDay:want.previewDay,
    targetCounts:Object.fromEntries(['.cn','.nt','.left','.until-prayer','#ce','#ah','.bar>i','.arc','.times',
      '#dateGregorian','#dateHijri','#ceDateButton','#ahDateButton'].map(k=>[k,1])),
    calendar:{gregorian:want.gregorian,hijri:want.hijri,gregorianAria:'Show complete Gregorian date: '+want.gregorian,
      hijriAria:'Show complete Hijri date: '+want.hijri+'. Before Maghrib.'},
    progress:{width:want.progressWidth,visibility:'visible'},
    rows:keys.map((key,i)=>({key,label:key,time:times[i],roles:want.roles[i].split(' ').filter(Boolean)})),
    markers:keys.map((key,i)=>({key,next:key===want.nextPrayer,ring:key==='Sunrise',cx:i*30+5,cy:100,r:5})),
    arc:'<path d="M0 0"/>',currentRing:{count:2,cx:want.ringX,cy:80},epoch:scenario.afterUtc,paused:false,documentHidden:false,
    bounds:{x:0,y:0,width:325,height:530,intersects:true}
  };
}
function row(stale=false) {
  const before=sample(initial);before.epoch=scenario.beforeUtc;
  const task=stale?sample(initial):sample();task.epoch=scenario.afterUtc;
  return {scenario:'fajr',before,afterTask:task,afterRaf:sample(),restoreCount:1,
    route:'native-intersection-observer',sampleBoundary:'mutation-observer-after-paused-removal',
    hidden:{paused:true,documentHidden:false,intersects:false},
    clock:{dateOnly:true,performanceAdvanced:true,timerRan:true,rafRan:true},
    intersections:[{isIntersecting:false},{isIntersecting:true}],unexpectedRequests:[]};
}
function layer(id,kind,sha) {
  return {className:'r002f-'+kind+'-'+id,visible:true,width:kind==='sky'?325:100,
    height:kind==='sky'?530:100,nonzeroAlpha:100,pixelsSha256:sha.repeat(64)};
}
function selected(id='4') {
  return {selector:id,ready:true,refined:false,frameCurrent:true,framePresent:true,utcMs:10,draws:50,
    researchGeneration:id,mask:'url("mask-a")',moon:{current:true,accepted:true},
    layers:[layer(id,'sky','a'),layer(id,'moon','b'),
      {className:'real-sky-preview',visible:false},{className:'moon-detail-canvas',visible:false}]};
}
function previewRow() {
  const before=selected(),afterFault=selected(),recovered=selected('5');recovered.draws=51;
  const beforeRevoke=clone(recovered);beforeRevoke.epoch=10;
  const afterRevoke={selector:null,ready:false,refined:false,frameCurrent:false,framePresent:false,
    researchGeneration:null,utcMs:null,epoch:2010,mask:'none',moon:{current:false,accepted:false},
    layers:[{className:'real-sky-preview',visible:false},{className:'moon-detail-canvas',visible:false}]};
  return {before,afterFault,recovered,beforeRevoke,afterRevoke,fault:{hits:1,message:'r002f injected upload failure',
    evaluation:7},faultSnapshotEvaluation:7,revokeEvaluation:8,revokeSnapshotEvaluation:8,
    revocation:{kind:'actual-clock-discontinuity-invalidation',deltaMs:2000},
    clock:{dateOnly:true,performanceAdvanced:true,timerRan:true,rafRan:true},
    refinedStartupBlocked:true,realMoonRuntime:true,realPreviewRuntime:true,unexpectedRequests:[]};
}

async function previewPath(arm,{initialUnexpected=false,lateUnexpected=false,closeError=false}={}) {
  // Execute the actual observation/persistence functions. Browser acquisition,
  // page evaluations and their native pixels are explicit boundary doubles.
  // This checks orchestration admission, not browser or product rendering.
  const source=fs.readFileSync(path.join(__dirname,'r002f_probe.cjs'),'utf8');
  const start=source.indexOf('function persistPixels('),end=source.indexOf('async function main(',start);
  assert.ok(start>=0 && end>start);
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-preview-path-'));
  const fixture=previewRow(),state={closed:false,evaluations:0,qualifiedAfterClose:[]};
  const ledger={requests:[],unexpectedRequests:initialUnexpected?['https://unexpected.invalid/initial']:[],
    console:[],pageErrors:[],refinedStartupBlocked:true};
  const page={waitForFunction:async()=>{},screenshot:async()=>{},evaluate:async()=>{
    switch(++state.evaluations){
      case 1:return;
      case 2:return clone({before:fixture.before,afterFault:fixture.afterFault,fault:fixture.fault,
        faultSnapshotEvaluation:fixture.faultSnapshotEvaluation,realMoonRuntime:true,realPreviewRuntime:true});
      case 3:return clone(fixture.recovered);
      case 4:return clone({beforeRevoke:fixture.beforeRevoke,afterRevoke:fixture.afterRevoke,
        revokeEvaluation:fixture.revokeEvaluation,revokeSnapshotEvaluation:fixture.revokeSnapshotEvaluation,
        revocation:fixture.revocation,disposed:false});
      default:throw Error('unexpected page evaluation');
    }
  }};
  const scene={page,ledger,fragment:'controlled-boundary-fixture',servedIndexSha256:arm==='baseline'?P.BASE_INDEX:P.COMBINED_INDEX,
    context:{close:async()=>{
      await Promise.resolve();
      if(lateUnexpected){
        ledger.requests=lateUnexpected==='websocket'?[]:
          [{url:'https://unexpected.invalid/late',action:lateUnexpected==='aborted'?'unexpected-aborted':'route-error'}];
        ledger.unexpectedRequests=lateUnexpected==='route-error-only'?[]:['wss://unexpected.invalid/late'];
      }
      if(closeError)throw Error('controlled context cleanup failure');
      state.closed=true;
    }}};
  const sandbox={fs,path,Date,Buffer,BASE_INDEX:P.BASE_INDEX,COMBINED_INDEX:P.COMBINED_INDEX,
    need:(condition,message)=>assert.ok(condition,message),openScene:async()=>scene,
    readPreviewDom:()=>{},verifyLiveCallbacks:async()=>clone(fixture.clock),
    sha:bytes=>crypto.createHash('sha256').update(bytes).digest('hex'),
    qualifyPreview:row=>{state.qualifiedAfterClose.push(state.closed);return P.qualifyPreview(row);}};
  vm.createContext(sandbox);
  vm.runInContext(source.slice(start,end)+'\nglobalThis.runPreview=previewObservation;',sandbox);
  try {
    const row=await sandbox.runPreview({}, {origin:'http://127.0.0.1:1'},arm,{timeoutMs:5},dir);
    const saved=JSON.parse(fs.readFileSync(path.join(dir,arm+'-preview.json'),'utf8'));
    return {row,saved,state};
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
}

test('complete independent prayer fixture is admitted',()=>assert.deepEqual(P.prayerDifferences(sample(),expected),[]));
test('next prayer is its name, never the time in .nt',()=>{
  const s=sample();s.nextPrayer='06:00';assert.ok(P.prayerDifferences(s,expected).includes('nextPrayer'));
});
test('all six distinct arc keys and the expected next marker are required',()=>{
  for(const mutate of [s=>s.markers.pop(),s=>{s.markers[5].key='Fajr';},s=>{s.markers[1].next=false;s.markers[2].next=true;}]){
    const s=sample();mutate(s);assert.throws(()=>P.prayerDifferences(s,expected),/marker/);
  }
});
test('missing or duplicated authored targets invalidate the observation',()=>{
  for(const count of [0,2]){const s=sample();s.targetCounts['.until-prayer']=count;assert.throws(()=>P.prayerDifferences(s,expected),/target/);}
});
test('blank values are incomplete, while stale dates, rows and progress are differences',()=>{
  const blank=sample();blank.hijri='';assert.throws(()=>P.prayerDifferences(blank,expected),/blank/);
  const s=sample();s.gregorian='2026-09-06';s.progress.width='99.9%';s.rows[0].roles=['on'];
  const diff=P.prayerDifferences(s,expected);for(const field of ['gregorian','progressWidth','rows'])assert.ok(diff.includes(field));
});
test('current candidate requires a demonstrably stale paired baseline',()=>{
  assert.equal(P.qualifyPrayerPair(row(true),row(),scenario).status,'PASS');
  assert.equal(P.qualifyPrayerPair(row(),row(),scenario).status,'INCONCLUSIVE');
  assert.equal(P.qualifyPrayerPair(row(),row(true),scenario).status,'INCONCLUSIVE');
  assert.equal(P.qualifyPrayerPair(row(true),row(true),scenario).status,'FAIL');
});
test('a stale current-position arc cannot hide behind correct six marker labels',()=>{
  const s=sample();s.currentRing.cx=62.11514;assert.ok(P.prayerDifferences(s,expected).includes('currentArc'));
});
test('a stale baseline that never recovers cannot validate the discriminator',()=>{
  const base=row(true);base.afterRaf=sample(initial);assert.equal(P.qualifyPrayerPair(base,row(),scenario).status,'INCOMPLETE');
});
test('synthetic visibility, absent hide, duplicate restore and frozen timers cannot pass',()=>{
  for(const mutate of [r=>{r.route='synthetic-visibilitychange';},r=>{r.hidden.documentHidden=true;},
    r=>{r.hidden.paused=false;},r=>{r.restoreCount=2;},r=>{r.clock.performanceAdvanced=false;},
    r=>{r.intersections=[];},r=>{r.unexpectedRequests=['https://unexpected.invalid'];}]){
    const candidate=row();mutate(candidate);assert.equal(P.qualifyPrayerPair(row(true),candidate,scenario).status,'INCOMPLETE');
  }
});
test('complete retained native selection and same-evaluation revocation are admitted',()=>{
  assert.equal(P.qualifyPreview(previewRow()).status,'PASS');
});
test('unexercised or multiply exercised fault cannot count as retained',()=>{
  for(const hits of [0,2]){const r=previewRow();r.fault.hits=hits;assert.equal(P.qualifyPreview(r).status,'INCOMPLETE');}
});
test('intervening evaluation, absent native owners or unknown external request invalidates preview',()=>{
  for(const mutate of [r=>{r.faultSnapshotEvaluation=9;},r=>{r.revokeSnapshotEvaluation=9;},
    r=>{r.realMoonRuntime=false;},r=>{r.realPreviewRuntime=false;},r=>{r.refinedStartupBlocked=false;},
    r=>{r.unexpectedRequests=['unexpected'];}]){
    const r=previewRow();mutate(r);assert.equal(P.qualifyPreview(r).status,'INCOMPLETE');
  }
});
test('mixed pixels, wrong receipt, visible underlying layer and lost mask fail',()=>{
  for(const mutate of [r=>{r.afterFault.layers[1].pixelsSha256='c'.repeat(64);},
    r=>{r.afterFault.researchGeneration='9';},r=>{r.afterFault.layers[2].visible=true;},
    r=>{r.afterFault.mask='none';},r=>{r.afterFault.layers[1].nonzeroAlpha=0;},
    r=>{r.afterRevoke.layers[0].visible=true;},r=>{r.afterRevoke.framePresent=true;}]){
    const r=previewRow();mutate(r);assert.equal(P.qualifyPreview(r).status,'FAIL');
  }
});
test('failed healthy replacement remains incomplete rather than a fault-path pass',()=>{
  const r=previewRow();r.recovered=clone(r.before);assert.equal(P.qualifyPreview(r).status,'INCOMPLETE');
});
test('actual preview path admits clean baseline and candidate only after context cleanup',async()=>{
  for(const arm of ['baseline','candidate']){
    const {row,saved,state}=await previewPath(arm);
    assert.equal(row.verdict.status,arm==='baseline'?'OBSERVED':'PASS');
    assert.equal(saved.verdict.status,row.verdict.status);assert.equal(state.closed,true);
    if(arm==='candidate')assert.deepEqual(state.qualifiedAfterClose,[true]);
    assert.equal(state.evaluations,4);
  }
});
test('actual preview baseline path rejects an unexpected request and retains its captured row',async()=>{
  const {row,saved}=await previewPath('baseline',{initialUnexpected:true});
  assert.equal(row.verdict.status,'INCOMPLETE');assert.equal(saved.verdict.status,'INCOMPLETE');
  assert.deepEqual(saved.unexpectedRequests,['https://unexpected.invalid/initial']);
  assert.equal(saved.fault.hits,1);assert.equal(saved.afterFault.selector,'4');
});
test('actual preview paths admit the final ledger including events delivered during cleanup',async()=>{
  for(const arm of ['baseline','candidate'])for(const lateUnexpected of ['websocket','aborted','route-error-only']){
    const {row,saved}=await previewPath(arm,{lateUnexpected});
    assert.equal(row.verdict.status,'INCOMPLETE');assert.equal(saved.verdict.status,'INCOMPLETE');
    if(lateUnexpected==='route-error-only'){
      assert.deepEqual(saved.unexpectedRequests,[]);assert.equal(saved.requests[0].action,'route-error');
    }else assert.deepEqual(saved.unexpectedRequests,['wss://unexpected.invalid/late']);
    assert.equal(saved.fault.hits,1);
  }
});
test('actual preview paths preserve raw observations and context cleanup failure as incomplete',async()=>{
  for(const arm of ['baseline','candidate']){
    const {row,saved}=await previewPath(arm,{closeError:true});
    assert.equal(row.verdict.status,'INCOMPLETE');assert.equal(saved.verdict.status,'INCOMPLETE');
    assert.match(saved.cleanupError,/controlled context cleanup failure/);
    assert.equal(saved.before.selector,'4');assert.equal(saved.afterFault.selector,'4');
    assert.equal(saved.afterRevoke.selector,null);assert.equal(saved.fault.hits,1);
  }
});
test('revocation requires live callbacks, disclosed Date discontinuity and immediately prior authority',()=>{
  for(const mutate of [r=>{r.clock.rafRan=false;},r=>{r.revocation.kind='forced-DOM-clear';},
    r=>{r.afterRevoke.epoch=10;},r=>{r.beforeRevoke.selector=null;}]){
    const r=previewRow();mutate(r);assert.notEqual(P.qualifyPreview(r).status,'PASS');
  }
});
test('isolation requires actual nonroot identity and changed matching network namespace',()=>{
  const host={uid:1200,netns:'net:[22]'};
  const receipt={protocol:'salah-hosted-native-isolation/1',passed:true,uid:1200,netns:'net:[22]',outerNetns:'net:[11]',browserControl:{passed:true}};
  assert.equal(P.validateIsolation(receipt,host),true);
  for(const mutate of [r=>{r.uid=0;},r=>{r.uid=1201;},r=>{r.netns='net:[99]';},
    r=>{r.outerNetns=r.netns;},r=>{r.browserControl.passed=false;},r=>{r.passed=false;}]){
    const r=clone(receipt);mutate(r);assert.throws(()=>P.validateIsolation(r,host),/isolation/);
  }
});
test('CLI refuses absent isolation before loading Playwright or creating native output',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-isolation-control-'));
  try {
    const out=path.join(dir,'output'),env={...process.env};delete env.SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT;
    const result=spawnSync(process.execPath,[path.join(__dirname,'r002f_probe.cjs'),
      '--playwright',path.join(dir,'missing-playwright'),'--baseline',path.join(dir,'main'),
      '--candidate',path.join(dir,'candidate'),'--out',out],{encoding:'utf8',env});
    assert.equal(result.status,2);assert.match(result.stderr,/native isolation receipt required/);
    assert.equal(fs.existsSync(out),false);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
test('fixed Date preserves timer, performance and animation-frame identities',()=>{
  const sandbox={Date,performance:{now:()=>123},setTimeout:()=>1,clearTimeout:()=>{},
    setInterval:()=>2,clearInterval:()=>{},requestAnimationFrame:()=>3,cancelAnimationFrame:()=>{}};
  const original={...sandbox};vm.createContext(sandbox);
  vm.runInContext('('+P.installFixedDate.toString()+')(1000)',sandbox);
  assert.equal(vm.runInContext('Date.now()',sandbox),1000);
  assert.equal(vm.runInContext('new Date().getTime()',sandbox),1000);
  assert.equal(vm.runInContext('new Date(500).getTime()',sandbox),500);
  assert.equal(vm.runInContext('Date.parse("1970-01-01T00:00:02Z")',sandbox),2000);
  assert.equal(vm.runInContext('typeof Date()',sandbox),'string');
  vm.runInContext('__r002fClock.set(7000)',sandbox);assert.equal(vm.runInContext('Date.now()',sandbox),7000);
  for(const key of Object.keys(original).filter(k=>k!=='Date'))assert.equal(sandbox[key],original[key]);
});

test('generated source admission rejects an altered full inventory before browser use',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-identity-control-'));
  try {
    const root=path.resolve(__dirname,'../../..');
    fs.copyFileSync(path.join(root,'index.html'),path.join(dir,'index.html'));
    fs.writeFileSync(path.join(dir,'GENERATED.json'),JSON.stringify({schema:'salah-generated-inventory/1',fileCount:0,files:{}}));
    assert.throws(()=>P.builtIdentity(dir,P.BASE_INDEX),/inventory identity/);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
test('build wrapper refuses wrong inputs without creating a disposable candidate',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-build-control-'));
  try {
    const source=path.join(dir,'source'),out=path.join(dir,'output');fs.mkdirSync(source);
    fs.writeFileSync(path.join(source,'index.html'),'wrong generated entry');
    const result=spawnSync(process.env.PYTHON||'python',[path.join(__dirname,'r002f_prepare.py'),'--research',source,'--baseline',source,'--out',out],{encoding:'utf8'});
    assert.equal(result.status,2);assert.match(result.stderr,/unadmitted source identity/);assert.equal(fs.existsSync(out),false);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
test('actual timed-out build child retains both partial streams and successful JSON remains parseable',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-build-timeout-'));
  try {
    const code=`import json,os,sys,subprocess
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import r002f_prepare as owner
root=Path(sys.argv[2])
real_run=owner.subprocess.run
def short_run(*args,**kwargs):
    kwargs['timeout']=0.25
    return real_run(*args,**kwargs)
owner.subprocess.run=short_run
child="import os,sys,time; from pathlib import Path; Path('child.pid').write_text(str(os.getpid())); print('partial stdout',flush=True); print('partial stderr',file=sys.stderr,flush=True); time.sleep(10)"
timed_out=False
try:
    owner.command([sys.executable,'-c',child],root,root,'slow')
except subprocess.TimeoutExpired:
    timed_out=True
finally:
    owner.subprocess.run=real_run
alive=True
try: os.kill(int((root/'child.pid').read_text()),0)
except ProcessLookupError: alive=False
read=lambda name:(root/name).read_text() if (root/name).exists() else None
returned=owner.command([sys.executable,'-c','print(\\'{"phase":"published","written":0}\\')'],root,root,'success')
print(json.dumps({'timedOut':timed_out,'alive':alive,'stdout':read('slow.stdout'),'stderr':read('slow.stderr'),'success':json.loads(returned)}))
`;
    const result=spawnSync(process.env.PYTHON||'python',['-c',code,__dirname,dir],{encoding:'utf8',timeout:10000});
    assert.equal(result.status,0,result.stderr);const report=JSON.parse(result.stdout);
    assert.equal(report.timedOut,true);assert.equal(report.alive,false);
    assert.equal(report.stdout,'partial stdout\n');assert.equal(report.stderr,'partial stderr\n');
    assert.deepEqual(report.success,{phase:'published',written:0});
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
test('independent fixed expectations match the actual admitted prayer publisher in all six instants',()=>{
  const {harness}=require('../../../tests/r0003-harness.cjs');
  for(const cell of P.SCENARIOS)for(const phase of ['before','after']){
    const utc=cell[phase+'Utc'],want=cell[phase],h=harness({epoch:new Date(utc).toISOString()});
    const prayer=day=>P.fixturePrayer(new URL('https://api.aladhan.com/v1/timings/'+day+'-09-2026')).data;
    h.seed(prayer(utc>=Date.parse('2026-09-08T00:00:00Z')?'08':'07'),utc>=Date.parse('2026-09-08T00:00:00Z')?null:prayer('08'));
    h.run('render();');
    const plain=x=>String(x||'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
    assert.equal(plain(h.nodes.get('.cn').textContent),want.current);
    assert.equal(plain(h.nodes.get('.nt').textContent),want.nextTime);
    assert.equal(plain(h.nodes.get('.left').innerHTML),want.countdown);
    assert.equal(h.nodes.get('.bar>i').style.width,want.progressWidth);
    const dateText=plain(h.nodes.get('#ce').innerHTML);assert.ok(dateText.includes(want.gregorian));
    const hijri=plain(h.nodes.get('#ah').innerHTML);assert.ok(hijri.includes(want.hijri));
    const arc=h.nodes.get('.arc').innerHTML;
    assert.equal([...arc.matchAll(/data-prayer-key=/g)].length,6);
    const next=[...arc.matchAll(/class="dot next[^\"]*"[^>]*data-prayer-key="([^"]+)"/g)].map(m=>m[1]);
    assert.deepEqual(next,[want.nextPrayer]);
    const ring=/class="cur" d="M([\d.-]+) [\d.-]+ A8 8 0 0 0 ([\d.-]+)/.exec(arc);
    assert.ok(ring);assert.ok(Math.abs((Number(ring[1])+Number(ring[2]))/2-want.ringX)<.02);
  }
});
test('actual combined Moon owner reacquires on same-scope dispose but withdraws on clock discontinuity',()=>{
  const {combine}=require('../r002f-transaction/materialize.cjs');
  const {moonFixture}=require('../r002f_a2_quarantine.cjs');
  const source=combine().outputs[2];
  assert.equal(crypto.createHash('sha256').update(source).digest('hex'),'864e3e134d82e6e76ac842e63bdd4f979ea1275c95e253e74e1d85d319a772de');
  function ready(){
    // Existing source fixture controls host capture, transport, initial renderer,
    // layout, timers and detail projection. Only the real owner's callback is
    // exercised here; this is not native CSS or native canvas evidence.
    const r=moonFixture(source,{initial:true});r.state.timeScale=1;
    r.workers[0].emit({kind:'ready'});r.workers[0].emit(r.response());r.flush();
    let withdrew=0;r.w.SalahSkyPreview={researchMoonWithdraw(){withdrew++;}};
    return {r,rt:r.w.SalahMoonRuntime,withdrawals:()=>withdrew};
  }
  const same=ready();assert.equal(same.rt.observe().current,true);
  same.rt.dispose();assert.equal(same.rt.observe().accepted,true);assert.equal(same.withdrawals(),0);
  const seek=ready();assert.equal(seek.rt.observe().current,true);
  seek.r.state.utcMs+=2000;seek.rt.invalidate('probe actual clock discontinuity');
  assert.equal(seek.rt.observe().current,false);assert.equal(seek.rt.observe().accepted,false);
  assert.equal(seek.withdrawals(),1);assert.equal(seek.rt.disposed,false);
});
