'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {checkPair,aperture,riseBracket}=require('./r003f_capture.cjs');
const {spawnSync}=require('node:child_process'),{performance}=require('node:perf_hooks');
const {buildMasks,measure,lightness}=require('./r003f_p1.cjs');
const {hash}=require('./r003f_variants.cjs'),{compareTransitions}=require('./r003f_diagnostics.cjs');
// Executed in one page task. Real rAF and timers still run. The measurement
// page advances the same monotonic clock read by simNow and the Moon worker's
// discontinuity check. Continuous observer pages retain the native clock.
const motionEvidence={ 'minute-target':'controlled-time numerical sample', continuous:'unmodified-clock observer playback' };
const nativeDb3Disposition={status:'INCONCLUSIVE',reason:'continuous playback lacks same-instant pixel controls; synchronized-target DB3 is controlled-time only'};
function startMotionClock({mode,epoch,fraction,waxing}){
  const nativeNow=performance.now.bind(performance),origin=nativeNow(),tick=Math.floor(origin);
  const nativeSnapshot=window.nativeLunarSnapshot,nativeRender=window.renderMoon;
  if(typeof nativeSnapshot!=='function'||typeof nativeRender!=='function')throw Error('native geometry producer unavailable');
  if(mode==='minute-target')Object.defineProperty(performance,'now',{configurable:true,
    value:()=>tick+1000*Math.floor((nativeNow()-origin)/1000)});
  let producing=false,last=null;
  window.nativeLunarSnapshot=function(date,...args){
    const s=nativeSnapshot.call(this,date,...args);
    if(producing)last={mode,utcMs:date.getTime(),elapsedRealMs:nativeNow()-origin,
      altitude:s.alt,up:s.up,transform:s.transform};
    return s;
  };
  window.renderMoon=function(...args){producing=true;try{return nativeRender.apply(this,args);}finally{producing=false;}};
  window.__r003fMotionObservation=()=>{
    const at=last&&nativeSnapshot(new Date(last.utcMs),28.54,-81.38,{moon:fraction,wax:waxing?'1':'0'});
    return {last,expected:at&&{altitude:at.alt,up:at.up,transform:at.transform},
      rendered:document.querySelector('.moon')?.getAttribute('transform'),sampledRealMs:nativeNow()-origin,anchorUtcMs:epoch};
  };
  window.SalahClock.set({rate:60,utcMs:epoch});
  return nativeNow()-origin;
}
function motionRegistration(state,minute,mode,anchor){
  const obs=state.motionClock,p=obs?.last;
  assert.ok(p&&p.mode===mode&&Number.isFinite(p.elapsedRealMs)&&p.elapsedRealMs>=0&&
    Number.isFinite(obs.sampledRealMs)&&obs.sampledRealMs>=p.elapsedRealMs,'missing production observation');
  assert.equal(obs.anchorUtcMs,anchor);
  assert.equal(anchor+Math.floor(obs.sampledRealMs/1000)*60000,minute*60000,'wrong real capture interval');assert.equal(Math.floor(p.utcMs/60000),minute,'wrong produced minute');
  assert.equal(Math.floor(state.utcMs/60000),minute,'wrong sampled minute');
  assert.deepEqual(obs.expected,{altitude:p.altitude,up:p.up,transform:p.transform},'production differs from ephemeris at the recorded instant');
  assert.deepEqual([p.altitude,p.up,p.transform],[state.consumed.observation.altitudeDeg,state.up,obs.rendered]);
  assert.ok(Number.isFinite(p.altitude)&&Number.isFinite(p.up)&&p.up===Math.min(1,Math.max(0,(p.altitude+2)/6)),'wrong native altitude ramp');
  if(mode==='minute-target'){
    assert.equal(p.utcMs,minute*60000,'not common astronomical instant');assert.equal(state.utcMs,p.utcMs);
    assert.equal(anchor+Math.floor(p.elapsedRealMs/1000)*60000,p.utcMs,'wrong elapsed production interval');
  }else{
    assert.equal(mode,'continuous');assert.ok(state.utcMs>=p.utcMs);
  }
  return {mode,utcMs:p.utcMs,altitude:p.altitude,up:p.up,transform:p.transform,disc:state.disc};
}
function frameRegistration(frame,minute,mode,anchor){
  const start=motionRegistration(frame.before,minute,mode,anchor),end=motionRegistration(frame.after,minute,mode,anchor);
  assert.deepEqual(start,end,'geometry changed during capture');return start;
}
function matchedRegistration(...frames){
  const [first,...others]=frames;
  assert.ok(first?.mode==='minute-target'&&Number.isSafeInteger(first.utcMs)&&first.utcMs%60000===0,'missing registered minute');
  for(const frame of others)assert.deepEqual(frame,first,'unmatched produced target or rendered footprint');
  return first;
}
async function run({open,cell,names,out,report,PNG,waitTier,facts,dpr,documents}){
  // The ten measurement streams use common UTC targets. Continuous playback
  // has its own untouched clock and independent elapsed-time observations.
  const epoch=Date.parse(cell.epoch),lead=30,minutes=50,startMinute=Math.floor(epoch/60000);
  const summaries=new Map();
  async function stream(label,name,offset,reference,mode='minute-target'){
    const p=await open(name,offset,{hold:false});
    const directory=path.join(out,label);fs.mkdirSync(directory,{mode:0o700});
    const frames=[];
    try{
      await p.waitForFunction(()=>!!window.SalahClock&&!!window.SalahMoonRuntime);
      await p.evaluate(t=>window.SalahClock.set({rate:0,utcMs:t}),epoch-lead*60000);
      if(reference)await p.evaluate(()=>window.SalahMoonRuntime.setProfile('reference'));
      const profile=reference?'unboosted-v5-01':'calendar-neutral-v5-01';
      await waitTier(p,'refined',profile);await p.waitForTimeout(2500);
      const armedAt=performance.now();
      const pageSetupMs=await p.evaluate(startMotionClock,{mode,epoch:epoch-lead*60000,fraction:offset?.01:cell.fraction,waxing:cell.waxing});
      const returnedAt=performance.now();
      // Remove the synchronous native scene reset from the estimated host
      // origin. The page corroborates its true elapsed bin at every capture.
      report.clockStarts[label]={hostRoundTripMs:returnedAt-armedAt,pageSetupMs};
      const began=returnedAt-pageSetupMs+1000*lead;
      for(let i=0;i<minutes;i++){
        await p.waitForTimeout(Math.max(0,began+i*1000+450-performance.now()));
        const started=performance.now()-began,before=await p.evaluate(facts),bytes=await p.locator('.c').screenshot(),after=await p.evaluate(facts),ended=performance.now()-began;
        const minute=before.consumed?.observation?.produced?.epochMinute,expected=startMinute+i,why=[];
        const admission={minute:expected,tier:'refined',offset,reference};let registration=null;
        try{checkPair(before,after,cell,admission);registration=frameRegistration({before,after},expected,mode,epoch-lead*60000);}catch(e){if(e.andon)throw e;why.push(e.message);}
        const altitude=before.consumed?.observation?.altitudeDeg;
        const decoded=PNG.sync.read(bytes);assert.equal(decoded.width,325*dpr);assert.equal(decoded.height,530*dpr);
        const file=String(i).padStart(3,'0')+'.png';
        fs.writeFileSync(path.join(directory,file),bytes);
        frames.push({file:label+'/'+file,sha256:hash(bytes),minute,expected,started,ended,before,after,admission,registration,document:documents.get(p),altitude,disc:before.disc,up:before.up,beam:before.beam,why});
      }
    }finally{await p.close();}
    const clip=spawnSync('ffmpeg',['-nostdin','-v','error','-framerate','1','-i',path.join(directory,'%03d.png'),'-c:v','ffv1',path.join(directory,'clip.mkv')],{encoding:'utf8'});
    const result={label,mode,evidenceClass:motionEvidence[mode],frames,cadence:{startsMs:frames.map(f=>f.started),durationsMs:frames.map(f=>f.ended-f.started),oneCapturePerSecond:frames.every((f,i)=>f.started>=1000*i&&f.ended<1000*(i+1))},clip:clip.status===0?label+'/clip.mkv':null,clipError:clip.error?.message||clip.stderr||null};
    report.streams.push(result);summaries.set(label,result);return result;
  }
  report.streams=[];report.clockStarts={};
  await stream('offset','B0',true,false);await stream('reference','B0',false,true);
  for(const name of [...new Set(['B0',...names])]){
    await stream(name,name,false,false);await stream('observer-'+name,name,false,false,'continuous');
  }
  const read=f=>PNG.sync.read(fs.readFileSync(path.join(out,f.file))).data;
  const {frames:offs}=summaries.get('offset'),{frames:refs}=summaries.get('reference');
  const series=new Map();
  for(const name of [...new Set(['B0',...names])]){
    const sequence=summaries.get(name).frames.map((f,i)=>{
      const o=offs[i],r=refs[i],row={minute:f.minute,litL:null,beam:f.beam,up:f.up,altitude:f.altitude};
      if([o,r,f].some(v=>v.why.length))return row;
      try{row.registration=matchedRegistration(o.registration,r.registration,f.registration,summaries.get('B0').frames[i].registration);}
      catch{return row;}
      if(r.before.acceptedFraction!==f.before.acceptedFraction||r.before.nativeFraction!==f.before.nativeFraction)return row;
      // DB3 reads the lit mask only. No unavailable sky-visibility mask is credited.
      const masks=buildMasks({dpr,fraction:cell.fraction,disc:f.disc,offsetDisc:o.disc,newMoon:read(o),reference:read(r),headerRects:[],topIsSkyOrMoon:new Uint8Array(325*530*dpr*dpr)});
      const s=measure(masks,read(f));row.aperture=aperture(s);row.referenceP95=s.referenceP95;row.maskOverlapPixels=s.maskOverlapPixels;if(row.aperture.lit)row.litL=lightness(s.litMeanY);
      return row;
    });
    series.set(name,sequence);
    const bracket=riseBracket(sequence),base=series.get('B0'),same=bracket&&[refs,offs,base].every(rows=>JSON.stringify(riseBracket(rows))===JSON.stringify(bracket));
    const comparison=same?compareTransitions(sequence.slice(...bracket),base.slice(...bracket)):{status:'INCOMPLETE',reason:'unmatched physical horizon bracket'};
    comparison.bracket=bracket;
    if(!same||sequence.some(row=>!row.aperture))report.motionDisposition='unmatched native stream geometry or acquisition';

    report.metrics.push({name,sequence,controlledDB3:comparison,nativeDB3:nativeDb3Disposition,observerGeometry:summaries.get('observer-'+name).frames.map(f=>f.registration)});
  }
  assert.ok(report.streams.every(s=>s.clip&&s.cadence.oneCapturePerSecond&&s.frames.every(f=>!f.why.length)),'missing clip or unqualified geometry minute');

  assert.ok(refs[0].altitude<=-2&&refs.at(-1).altitude>=4,'sequence did not bracket both horizon endpoints');
}
module.exports={run,startMotionClock,frameRegistration,matchedRegistration,motionEvidence,nativeDb3Disposition};
