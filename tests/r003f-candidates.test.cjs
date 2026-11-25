'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {variants,variantSource,renderVariant,unpack,hash}=require('../tools/qa/r003f_variants.cjs');
const {cells,fragment}=require('../tools/qa/r003f_grid.cjs');
const {terrain,terminator,occultation,deltaE,compareTransitions,buckleRate,lab}=require('../tools/qa/r003f_diagnostics.cjs');
const {buildMasks,measure}=require('../tools/qa/r003f_p1.cjs');
const root=path.resolve(__dirname,'..'),read=file=>fs.readFileSync(path.join(root,file));
test('eight distinct served variants preserve the pristine B0 and the worker source identity guard',()=>{
  const html=read('index.html').toString(),src=read('moon/src/moon-calendar.mjs').toString().trimEnd();
  const outputs=variants.map(n=>renderVariant(html,src,n));
  assert.equal(outputs[0].html,html);assert.equal(new Set(outputs.map(b=>b.identity.worker.sha256)).size,8);
  const baseWorker=unpack(html).worker;assert.equal(baseWorker,read('moon/moon-worker.js').toString());
  for(const [i,{html:h,identity}] of outputs.entries()){
    const changed=variantSource(src,variants[i]);
    assert.equal(unpack(h).worker,baseWorker.replace(src,()=>changed));
    assert.equal(hash(h),identity.indexSha256);
  }
  const broken=outputs[1].html.replace(outputs[1].identity.worker.sha256,'0'.repeat(64));
  assert.throws(()=>unpack(broken),/pin drift/);
  assert.throws(()=>renderVariant(html.replace(src,''),src,'B4'),/anchor/);
  assert.throws(()=>variantSource(src+'\n'+src,'B4'),/anchor/);
});
test('both-sense, two-DPR grids cover exact weather, phase, horizon, motion and outlier controls',()=>{
  const expected=[.01,.04,.08,.15,.314,.5,.75,.85,.99];
  let total=0;
  for(const engine of ['chromium','firefox','webkit'])for(const dpr of [1,2]){
    const rows=cells(engine,dpr);total+=rows.length;assert.equal(new Set(rows.map(c=>c.id)).size,rows.length);
    for(const waxing of [true,false])assert.deepEqual(rows.filter(c=>c.group==='phase'&&c.waxing===waxing).map(c=>c.fraction),expected);
    const owner=rows.find(c=>c.group==='owner');assert.doesNotMatch(fragment(owner),/simMoon/);
    assert.doesNotMatch(fragment(owner,true),/simMoonAlt/);
    assert.equal(rows.filter(c=>c.group==='strap'&&c.repeats===10).length,12);
    assert.equal(rows.filter(c=>c.group==='buckle'&&c.repeats===20).length,16);
    assert.equal(rows.filter(c=>c.group==='horizon').length,dpr===1?85:0);
    assert.equal(rows.filter(c=>c.group==='motion').length,dpr===1&&engine!=='webkit'?4:0);
  }
  assert.equal(total,761);
  const listings=JSON.parse(require('node:child_process').execFileSync(process.execPath,['tools/qa/r003f_matrix.cjs','--list'],{cwd:root,encoding:'utf8'}));
  assert.equal(listings.length,187,'complete manifest through a pipe');
});
function frames(){
  const d={cx:150.5,cy:120.5,r:45},n=325*530;
  const mk=(field)=>{const b=Buffer.alloc(n*4);for(let i=0;i<n;i++){
    const x=i%325-150,y=Math.floor(i/325)-120,v=field(x,y);
    b.set([v,v,v,255],4*i);
  }return b;};
  const ramp=x=>Math.min(1,Math.max(0,(x+2)/4));
  const shape=(x,y,shift=0)=>Math.hypot(x,y)<45?Math.round(24+(100+Math.round(y/4))*ramp(x-shift)):24;
  const offset=mk(()=>24),reference=mk(shape),allowed=new Uint8Array(n).fill(1);
  const masks=buildMasks({dpr:1,fraction:.5,disc:d,offsetDisc:d,newMoon:offset,reference,headerRects:[],topIsSkyOrMoon:allowed});
  return {mk,shape,reference,masks};
}
test('P1 controls distinguish geometry, terrain flattening, real opacity sampling, and tone',()=>{
  const {mk,shape,reference,masks}=frames(),flat=mk((x,y)=>Math.max(shape(x,y),120));
  assert.ok(terrain(masks,flat).litCV<.9*terrain(masks,reference).litCV);
  const same=terminator(masks,reference,reference,true),shift=terminator(masks,mk((x,y)=>shape(x,y,3)),reference,true);
  assert.equal(same.mean,0);assert.ok(same.matched>50);assert.ok(shift.mean>.5);
  const hidden=mk((x,y)=>x===-10&&y===0?255:24);
  assert.deepEqual(occultation(masks,reference,hidden).starCoincidences,[]);
  const leak=mk((x,y)=>x===-10&&y===0?Math.round(24*.9+255*.1):shape(x,y));
  assert.equal(occultation(masks,leak,hidden).starCoincidences.length,1);
  assert.equal(deltaE(masks,reference,reference).max,0);
  assert.ok(Math.abs(lab(Buffer.from([255,255,255,255]),0)[0]-100)<.001);
  const red=lab(Buffer.from([255,0,0,255]),0);
  for(const [k,v] of [53.24,80.09,67.20].entries())assert.ok(Math.abs(red[k]-v)<.02);
  assert.ok(Math.abs(measure({...masks,lit:masks.sky.map(p=>p.i)},reference).deltaLitSkyL)<1e-9);
});
test('DB3 and buckle statistics retain missing minutes and degenerate controls',()=>{
  const baseline=[0,1,2,3,4].map((v,i)=>({minute:800+i,litL:10+v*2}));
  assert.equal(compareTransitions(baseline,baseline).db3,true);
  const step=baseline.map((x,i)=>({...x,litL:i<2?10:18}));assert.equal(compareTransitions(step,baseline).db3,false);
  assert.equal(compareTransitions(baseline.filter((_,i)=>i!==2),baseline).status,'INCOMPLETE');
  assert.equal(buckleRate(0,0,20).p,null);assert.equal(buckleRate(2,3,19).p,null);
  assert.ok(buckleRate(0,15,20).p<.001);assert.ok(buckleRate(4,5,20).p>.05);
});
for(const adverse of [false,true])test('R003F isolated matrix entry '+(adverse?'halts on physical light':'retains both tiers and signed outside-pixel hits'),t=>{
  const dir=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'r003f-matrix-test-')),out=path.join(dir,'cell');
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const stub=require.resolve('./r003f-matrix-fixture.cjs'),id=cells('chromium',1).find(c=>c.group==='phase'&&c.fraction===.5&&c.waxing).id;
  const run=require('node:child_process').spawnSync(process.execPath,['tools/qa/r003f_matrix.cjs','--root',root,'--out',out,'--id',id,'--variant','B1c','--playwright',stub,'--pngjs',stub],{
    cwd:root,encoding:'utf8',timeout:30000,env:{...process.env,R003F_FAKE:adverse?'leak':''}});
  assert.equal(run.status,adverse?4:0,run.stdout+run.stderr);
  const r=JSON.parse(fs.readFileSync(path.join(out,'summary.json')));
  assert.equal(r.network.allowedOffLoopback,0);
  assert.ok(r.network.abortedHosts.includes('foreign.test'));assert.equal(r.status,adverse?'ANDON':'DIAGNOSTIC');
  if(!adverse){
    assert.deepEqual(r.metrics.map(m=>m.tier),['initial','refined']);
    for(const m of r.metrics)assert.ok(m.cloudMatch&&m.metrics.deltaLitSkyL>0&&m.metrics.deltaPhysicalCandidateL>0);
    const lines=fs.readFileSync(path.join(out,'outside.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    assert.equal(lines.length,2);for(const l of lines){assert.equal(l.x,1);assert.deepEqual(l.delta,[1,1,1,0]);assert.ok(l.stack.length);}
  }
});

function runFixture(t,mode,all=false){
  const dir=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'r003f-admission-test-')),out=path.join(dir,'cell');
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const stub=require.resolve('./r003f-matrix-fixture.cjs'),id=cells('chromium',1).find(c=>c.group==='phase'&&c.fraction===.5&&c.waxing).id;
  const args=['tools/qa/r003f_matrix.cjs','--root',root,'--out',out,'--id',id,'--playwright',stub,'--pngjs',stub];
  if(!all)args.push('--variant','B1c');
  const run=require('node:child_process').spawnSync(process.execPath,args,{cwd:root,encoding:'utf8',timeout:30000,
    env:{...process.env,R003F_FAKE:mode,R003F_ENCODE_PNG:all?'1':'0'}});
  const file=path.join(out,'summary.json');
  assert.ok(fs.existsSync(file),run.stdout+run.stderr);
  return {dir,out,file,r:JSON.parse(fs.readFileSync(file)),status:run.status};
}
test('screenshot admission rejects stale, hidden, wrong phase/scene, weather, ramp and tier on either side',t=>{
  const {checkPair}=require('../tools/qa/r003f_capture.cjs');
  const {r}=runFixture(t,'');const m=r.captures['B1c-initial'];
  for(const update of [
    s=>s.consumed.status='failed',s=>s.consumed.observation.produced.epochMinute=0,s=>s.up=.75,s=>s.beam='',
    s=>s.weatherFields.vis=5000,s=>s.weatherFields.rh=98,s=>s.wx.currentWeatherSource='none',
    s=>s.quality='pending',s=>s.profile='unboosted-v5-01',s=>s.nativeFraction=.1,
    s=>s.visibility=['hidden','hidden'],s=>s.disc.cx=500,s=>s.presentable=false,s=>s.sunEl=30
  ])for(const side of ['state','after']){
    const v=structuredClone(m);update(v[side]);assert.throws(()=>checkPair(v.state,v.after,r.cell,m.admission));
  }
  for(const mode of ['stale','wrongup','emptybeam','weather','wrongtier']){
    const bad=runFixture(t,mode);assert.equal(bad.status,2);assert.equal(bad.r.status,'INCOMPLETE');
    assert.equal(bad.r.rejected.tag,'B1c-initial');
  }
});
test('150 s refinement timeout retains subsequent variant, baseline and offset initial evidence',t=>{
  const {r,status}=runFixture(t,'late');
  assert.equal(status,2);assert.equal(r.status,'PARTIAL');
  for(const tag of ['B1c','offset','b0','baseline-repeat']){
    assert.ok(r.captures[tag+'-initial']);assert.match(r.tierDisposition[tag].reason,/150000/);assert.ok(!r.captures[tag+'-refined']);
  }
  assert.equal(r.metrics[0].status,'INCONCLUSIVE');assert.equal(r.metrics[0].cloudMatch,true);assert.ok(r.metrics[0].pair&&r.metrics[0].envelope);
  assert.equal(r.metrics[1].status,'INCOMPLETE');assert.ok(r.tierDisposition.reference);
});
test('flat or overlapping apertures withhold phase measurements and the DB3 window excludes preroll',t=>{
  const {aperture,riseBracket}=require('../tools/qa/r003f_capture.cjs'),{r}=runFixture(t,'flat');
  for(const v of r.metrics){
    assert.ok(v.metrics.maskOverlapPixels>0);assert.equal(v.metrics.referenceP95,0);
    assert.deepEqual(v.aperture,{lit:false,dark:false,sky:false});assert.ok(!v.db1);
    assert.equal(aperture({...v.metrics,referenceP95:1}).lit,false);
  }
  const rows=[-5,-4,-3,-2,-1,0,2,4,6].map((altitude,i)=>({minute:700+i,altitude,up:Math.min(1,Math.max(0,(altitude+2)/6)),litL:[0,10,10,10,12,14,16,18,20][i]}));
  const variant=rows.map((r,i)=>({...r,litL:[0,1,2,2,7,8,9,10,11][i]}));
  assert.equal(compareTransitions(variant,rows).db3,true);const bracket=riseBracket(rows);assert.deepEqual(bracket,[3,8]);
  assert.equal(compareTransitions(variant.slice(...bracket),rows.slice(...bracket)).db3,false);
  assert.equal(riseBracket(rows.slice(0,7)),null);assert.equal(riseBracket(rows.map((r,i)=>({...r,up:i===3?NaN:r.up}))),null);
  const program=`import sys,json
sys.path.insert(0,'tools/qa')
from r003f_sheets import adjudicate
r=json.load(open(sys.argv[1]))
key=('chromium',1,r['cell']['id'])
def row(): return adjudicate({key:(r,{})},(0,999,0))['cells'][0]
v=row()
assert all(v[k] is None for k in ('legibilityFloorMet','D2','F-INV-4-cv','F-INV-4-darkStd','F-INV-5-crossings','DB1'))
s=r['metrics'][0]
s.update(aperture={'lit':True,'dark':True,'sky':True},repeatStable={'lit':True,'dark':True,'sky':True},terminator={'matched':1,'max':2,'mean':.1,'missing':4,'ambiguous':1})
v=row()
assert v['F-INV-5-crossings'] is False and v['F-INV-5-observedMax']==2 and v['F-INV-5-allRowMean'] is None
s['repeatStable']['lit']=False
assert row()['F-INV-5-crossings'] is None
`;
  const tmp=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'r003f-flat-report-'));t.after(()=>fs.rmSync(tmp,{recursive:true,force:true}));
  const summary=path.join(tmp,'summary.json');fs.writeFileSync(summary,JSON.stringify(r));
  require('node:child_process').execFileSync('python',['-c',program,summary],{cwd:root});
});
test('eight-variant synthetic archive replays structurally and stays diagnostic at sheet intake',t=>{
  const {r,status,out,file,dir}=runFixture(t,'',true),{PNG}=require('pngjs');
  const {validate,replayFixture}=require('../tools/qa/r003f_receipt.cjs');
  assert.equal(status,0);assert.throws(()=>validate(file,PNG),/native/);replayFixture(file,PNG);
  const write=v=>fs.writeFileSync(file,JSON.stringify(v));
  for(const mutate of [
    x=>x.cell.group='ineligible',x=>x.names=['B0'],x=>x.builds.pop(),x=>x.metrics.pop(),x=>x.pairs.pop(),
    x=>x.metrics[0].metrics.litMeanY=42,x=>x.captures['B1c-initial'].after.consumed.status='failed',
    x=>x.captures['B0-initial'].document.responseSha256='0'.repeat(64)
  ]){const bad=structuredClone(r);mutate(bad);write(bad);assert.throws(()=>replayFixture(file,PNG));}
  for(const group of ['ineligible','motion','buckle','strap']){
    const bad=structuredClone(r);bad.cell=cells('chromium',1).find(c=>c.group===group);bad.names=['B0'];write(bad);
    assert.throws(()=>replayFixture(file,PNG));
  }
  write(r);
  for(const name of ['network.jsonl','outside.jsonl','hidden-initial.png','masks-initial.json']){
    const f=path.join(out,name);fs.renameSync(f,f+'.removed');assert.throws(()=>replayFixture(file,PNG));fs.renameSync(f+'.removed',f);
  }
  const motion=structuredClone(r);motion.cell=cells('chromium',1).find(c=>c.group==='motion');
  motion.streams=['offset','reference',...variants,...variants.map(n=>'observer-'+n)].map(label=>({label,frames:Array(50).fill({}),clip:label+'/clip.mkv'}));
  fs.mkdirSync(path.join(out,'offset'));write(motion);assert.throws(()=>replayFixture(file,PNG),/clip\.mkv/);write(r);
  const dest=path.join(dir,'sheets'),result=require('node:child_process').spawnSync('python',['tools/qa/r003f_sheets.py','--reports',out,'--out',dest],{cwd:root});
  assert.equal(result.status,2);const intake=JSON.parse(fs.readFileSync(path.join(dest,'sheets.json')));
  assert.equal(intake.measuredCellCount,0);assert.equal(intake.absentCells.length,761);assert.deepEqual(intake.sheets,[]);
});
test('current and accelerated weather fixtures cover the preroll and entire controlled clip',async()=>{
  const {clearWeather}=require('../tools/qa/r003f_capture.cjs');
  const vm=require('node:vm'),context={window:{fetch:()=>{throw Error('unexpected passthrough');}},URL,Response,location:{href:'http://127.0.0.1/'}};
  vm.runInNewContext('('+clearWeather.toString()+')({time:"2026-11-03T00:50",weather_code:0,visibility:5000,relative_humidity_2m:90})',context);
  const b=await (await context.window.fetch('https://api.open-meteo.com/v1/forecast')).json();
  assert.equal(context.window.__r003fWeatherReads,1);assert.equal(b.current.visibility,5000);
  assert.equal(b.hourly.time[0],'2026-11-02T22:50');assert.equal(b.hourly.time.at(-1),'2026-11-03T02:50');
  for(const w of ['visibility','relative_humidity_2m','weather_code','cloud_cover','temperature_2m'])assert.deepEqual(b.hourly[w],Array(5).fill(b.current[w]));
});

test('real ephemeris at independent rAF arrivals is paired only after sampling a common astronomical instant',()=>{
  const {load}=require('./r001d-harness.cjs'),{startMotionClock,frameRegistration,matchedRegistration}=require('../tools/qa/r003f_motion.cjs');
  const cell=cells('chromium',1).find(c=>c.group==='motion'),at=Date.parse('2026-11-03T06:15:00Z'),anchor=at-60000;
  function record(mode,elapsed,epoch=anchor){
    const h=load({hash:fragment(cell)});
    h.run('('+startMotionClock.toString()+')('+JSON.stringify({mode,epoch,fraction:.314,waxing:true})+')');
    h.clock.now=elapsed;h.run('renderMoon()');
    const before=JSON.parse(JSON.stringify(h.run('({motionClock:__r003fMotionObservation(),utcMs:simNow(),up:moonSky.up,consumed:{observation:{altitudeDeg:moonSky.alt}},disc:{cx:266.8,cy:56.4,r:45}})')));
    return {before,after:structuredClone(before)};
  }
  const naturalA=record('continuous',1000),naturalB=record('continuous',1016.666667);
  const targetA=record('minute-target',1000),targetB=record('minute-target',1016.666667);
  const register=(f,mode)=>frameRegistration(f,at/60000,mode,anchor);
  const [a,b]=[naturalA,naturalB].map(f=>register(f,'continuous'));
  assert.deepEqual([a.utcMs,b.utcMs],[at,at+1000]);assert.equal(a.transform,b.transform);
  assert.equal(a.altitude,.7832316599843617);assert.equal(b.altitude,.7866341532696296);
  assert.equal(a.up,.46387194333072695);assert.equal(b.up,.46443902554493827);
  assert.throws(()=>matchedRegistration(a,b));
  const [first,late]=[targetA,targetB].map(f=>register(f,'minute-target'));
  assert.deepEqual(matchedRegistration(first,late),first);assert.equal(late.altitude,a.altitude);
  assert.notEqual(targetA.before.motionClock.last.elapsedRealMs,targetB.before.motionClock.last.elapsedRealMs);
  for(const mutate of [
    s=>s.consumed.observation.altitudeDeg=b.altitude,s=>s.up=b.up,s=>s.motionClock.last.utcMs+=1000,
    s=>s.motionClock.last.altitude=b.altitude,s=>s.motionClock.expected.altitude=b.altitude,
    s=>s.motionClock.sampledRealMs+=1000,s=>s.motionClock.rendered='translate(0 0)'
  ]){
    const bad=structuredClone(targetB);mutate(bad.after);assert.throws(()=>register(bad,'minute-target'));
  }
  assert.throws(()=>frameRegistration(targetA,at/60000+1,'minute-target',anchor));
  // Find the actual within-minute +4 degree crossing in the generated ephemeris.
  const h=load({hash:fragment(cell)}),ephem=t=>h.run('nativeLunarSnapshot(new Date('+t+'),28.54,-81.38,{moon:.314,wax:"1"}).alt');
  let lo=at,hi=at+25*60000;
  while(hi-lo>1){const mid=Math.floor((lo+hi)/2);if(ephem(mid)>=4)hi=mid;else lo=mid;}
  assert.ok(ephem(lo)<4&&ephem(hi)>=4);
  const base=Math.floor(lo/60000)*60000;assert.equal(base,Math.floor(hi/60000)*60000);
  const justBefore=record('continuous',(lo-base+.25)/60,base),justAfter=record('continuous',(hi-base+.25)/60,base);
  const side=[justBefore,justAfter].map(f=>frameRegistration(f,base/60000,'continuous',base));
  assert.ok(side[0].up<1&&side[1].up===1);assert.throws(()=>matchedRegistration(...side));
});
test('sheet records unmodified-clock and controlled-time outcomes separately across OS settings',()=>{
  const cp=require('node:child_process');
  const program=`import sys
sys.path.insert(0,'tools/qa')
from r003f_sheets import adjudicate
def report(mode,actual):
    disc={"cx":267,"cy":56.4,"r":45}
    reg={"mode":"minute-target","utcMs":120000,"altitude":.783,"up":.46,"transform":"same transform","disc":disc}
    observer={**reg,"mode":"continuous","utcMs":actual,"altitude":.786 if actual>120000 else .783}
    sample={"name":"B0","sequence":[{"registration":reg}],"observerGeometry":[observer],"nativeDB3":{"status":"INCONCLUSIVE"},"controlledDB3":{"status":"MEASURED","db3":False}}
    return ({"cell":{"motion":mode,"group":"motion","fraction":.314},"pairs":[],"metrics":[sample]}, {})
r=adjudicate({("chromium",1,"a"):report("reduce",120000),("chromium",1,"b"):report("no-preference",121000)},(None,None,None))
assert all(x['DB3']['status']=='INCONCLUSIVE' and x['controlledTimeDB3']['db3'] is False for x in r['cells'])
m=r['motionModes'][0]
assert m['controlledReducedMotionSameGeometry'] and m['observerRequestedMinutesMatch'] and m['observerSameRenderedFootprints'] and m['observerCommonInstantCount']==0
`;
  cp.execFileSync('python',['-c',program],{cwd:root});
});
