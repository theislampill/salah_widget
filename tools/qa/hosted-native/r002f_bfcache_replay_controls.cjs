'use strict';
// Synthetic retained-shape controls only. These values are never admitted as a native observation.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),test=require('node:test'),assert=require('node:assert/strict');
function feature(){const file=path.join(__dirname,'r002f_bfcache_replay.cjs');assert.ok(fs.existsSync(file),'original-body replay is not implemented');return require(file);}
function temporary(fn){const root=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-bfcache-replay-control-'));try{return fn(root);}finally{fs.rmSync(root,{recursive:true,force:true});}}
function retainedStderr(root){const S=require('./r002f_bfcache_source.cjs'),file=path.join(root,'stderr');fs.writeFileSync(file,'');
  return {stderr:S.record(file),stderrBytes:0,stderrAcknowledgedBytes:0,stderrRetainedBytes:0,stderrClosed:true,stderrRetentionError:null};}
function fixture(){
  const bright=Uint8Array.from([100,100]),dark=Uint8Array.from([0,0]);
  const ev=[],frames=[];for(let k=1;k<=3;k++){
    ev.push({n:'pagehide',phase:'first',step:true,c:2*k-1,trusted:true,persisted:true,t:k*100,cur:true,ready:true});
    ev.push({n:'pageshow',phase:'first',step:true,c:2*k,trusted:true,persisted:true,t:k*100+20,cur:true,ready:true});
    ev.push({n:'visibilitychange',phase:'first',step:false,c:2*k,trusted:true,hidden:false,t:k*100+21,cur:true,ready:true});
    ev.push({n:'visibilitychange',phase:'dispatch-end',c:2*k,trusted:true,hidden:false,t:k*100+22,cur:true,ready:true,src:'original-source-fixture'});
    ev.push({n:'pageshow',phase:'next-task',c:2*k,t:k*100+23,cur:true});
    ev.push({n:'pageshow',phase:'raf-begin',c:2*k,t:k*100+24,dt:4,cur:true});frames.push([k*100+24,2*k,1,1,1,1,1]);}
  const out={schema:'r0041-real-witness/1',label:'baseline',engine:'chromium',route:'bfcache',fault:false,startISO:'2026-11-18T16:30:00Z',headed:true,events:3,void:[],notes:[],
    before:{cur:true,ready:true},after:{cur:true,ready:true},rect:{x:20,y:20,w:40,h:40},hiddenChecks:['away','away','away'],
    log:{ev,frames,c:6},truth:{displayMode:'source-control'},isolation:{allowedExternal:0,externalAttempts:0,byLayerHostOutcome:{}}};
  const shots=[];for(let k=1;k<=3;k++)for(let n=0;n<5;n++)shots.push({k,tag:'restore-'+k,marker:2*k,disc:bright});
  const video=[{marker:0,disc:bright}];for(let k=1;k<=3;k++){video.push({marker:2*k-1,disc:bright});for(let n=0;n<15;n++)video.push({marker:2*k,disc:bright});}
  video.push({marker:7,disc:dark},{marker:7,disc:dark});
  return {scope:'SOURCE_CONTROL_ONLY',out,shots,refs:{present:{marker:0,disc:bright},absent:{marker:7,disc:dark}},video,videoBytes:123,videoSha256:'a'.repeat(64)};
}
test('exact original judgment accepts the fixed trusted three-event synthetic population',async()=>{
  const R=feature(),f=fixture(),got=await R.sourceControl(f);
  assert.equal(got.full.valid,true);assert.equal(got.full.judged.videoFrames,45);assert.equal(got.full.judged.shots,15);
  assert.equal(got.full.verdict,'NO FRAME WITHOUT THE MOON AFTER THE RESTORING EVENT; NO STALE HIDDEN-STATE FRAME');
  assert.equal(got.slim.log.animationFrameCount,3);assert.equal(got.full.log.frames.length,3);
});
test('untrusted nonpersisted reloaded and missing lifecycle data retain original VOID judgments',async()=>{
  const R=feature();for(const mode of ['untrusted','nonpersisted','reload','missing']){
    const f=fixture();if(mode==='untrusted')f.out.log.ev[1].trusted=false;
    if(mode==='nonpersisted')f.out.log.ev[1].persisted=false;if(mode==='reload')f.out.log.ev=[];
    if(mode==='missing')f.out.log.ev=f.out.log.ev.filter(x=>x.c!==6);
    const got=await R.sourceControl(f);assert.equal(got.full.valid,false,mode);assert.equal(got.full.verdict,'VOID');assert.ok(got.full.void.length>0);}
});
test('original five-shot fifteen-video-frame and reference-distance minima are unchanged',async()=>{
  const R=feature();for(const mode of ['shots','frames','references','marker']){
    const f=fixture();if(mode==='shots')f.shots.shift();if(mode==='frames')f.video.splice(f.video.findIndex(x=>x.marker===2),1);
    if(mode==='references')f.refs.present.disc=Uint8Array.from([7,7]);if(mode==='marker')f.refs.absent.marker=6;
    const got=await R.sourceControl(f);assert.equal(got.full.valid,false,mode);assert.equal(got.full.verdict,'VOID');}
});
test('valid adverse Moon pixels and cached hidden-state failures survive original replay',async()=>{
  const R=feature(),f=fixture();f.shots[0].disc=Uint8Array.from([0,0]);f.video[2].disc=Uint8Array.from([0,0]);f.video[1].disc=Uint8Array.from([0,0]);
  const got=await R.sourceControl(f);assert.equal(got.full.valid,true);
  assert.equal(got.full.judged.shotsWithoutMoon,1);assert.equal(got.full.judged.videoWithoutMoon,1);assert.equal(got.full.judged.staleHiddenStateFramesWithoutMoon,1);
  assert.equal(got.full.verdict,'FRAMES WITHOUT THE MOON AFTER THE RESTORING EVENT; 1 STALE HIDDEN-STATE FRAMES WITHOUT THE MOON BEFORE IT');
});
test('pre-hide cached frames remain a separate original count with unchanged forty-millisecond arithmetic',async()=>{
  const R=feature(),f=fixture();f.video.splice(1,0,{marker:0,disc:Uint8Array.from([100,100])});
  const got=await R.sourceControl(f);assert.equal(got.full.judged.stalePreHideFrames,32);
  assert.deepEqual(Array.from(got.full.video.perRestoration,r=>r.staleFrames.preHide),[2,15,15]);
  assert.equal(got.full.video.perRestoration[0].staleFrames.milliseconds,120);
});
test('altered auxiliary events and pixel reports cannot pass comparison as the original output',async()=>{
  const R=feature(),got=await R.sourceControl(fixture());assert.equal(R.compareReport(got.slim,got.slim),true);
  for(const field of ['judged','log','verdict','before']){const copy=structuredClone(got.slim);copy[field]={altered:true};assert.throws(()=>R.compareReport(copy,got.slim),/original|differs/);}
});
test('a partial original RGB frame is incomplete even though original decoder ignores its tail',()=>temporary(root=>{
  const R=feature(),stderr=retainedStderr(root);assert.equal(R.admitDecoded({...stderr,returncode:0,timedOut:false,bytes:518340*50,frames:50,rgbSha256:'a'.repeat(64),mappingsComplete:true}),true);
  for(const change of [{bytes:518340*50+1},{frames:20001,bytes:518340*20001},{returncode:7},{timedOut:true},{mappingsComplete:false}])
    assert.throws(()=>R.admitDecoded({...stderr,returncode:0,timedOut:false,bytes:518340*50,frames:50,rgbSha256:'a'.repeat(64),mappingsComplete:true,...change}));
}));
test('the complete streamed RGB population must have an actual hash as well as an integer frame count',()=>temporary(root=>{
  const R=feature(),base={...retainedStderr(root),returncode:0,timedOut:false,bytes:518340,frames:1,mappingsComplete:true};
  for(const value of [undefined,'','not-a-hash'])assert.throws(()=>R.admitDecoded({...base,rgbSha256:value}));
  assert.equal(R.admitDecoded({...base,rgbSha256:'b'.repeat(64)}),true);
}));
test('synthetic fixture route refuses a missing disclosure and does not create a native status',async()=>{
  const R=feature(),f=fixture();delete f.scope;await assert.rejects(R.sourceControl(f));
  const result=await R.sourceControl(fixture());assert.equal(result.scope,'SOURCE_CONTROL_ONLY');assert.equal(result.nativeObservation,false);
  assert.notEqual(result.status,'OBSERVED_BFCACHE_DIAGNOSTIC');
});
// Synthetic process/mapping events with actual output descriptors; no decoder or browser is acquired or executed.
test('decoder callbacks preserve partial zero invalid and throwing stderr prefixes and refuse complete admission',()=>temporary(root=>{
  const R=feature(),S=require('./r002f_bfcache_source.cjs'),{EventEmitter}=require('node:events');
  for(const mode of ['ordinary','partial','zero','invalid','throw','lie']){const folder=path.join(root,mode);fs.mkdirSync(folder);
    const toolFile=path.join(folder,'synthetic-decoder'),input=path.join(folder,'input.webm');fs.writeFileSync(toolFile,'source-only nonexecuted decoder');fs.writeFileSync(input,'source-only input');
    const identity=S.record(toolFile),tools={tools:{decoder:identity},closure:{files:{[identity.path]:{identity,aliases:[]}}}},child=new EventEmitter();let kills=0,closed=0,writes=0;
    Object.assign(child,{pid:99999999,stdout:new EventEmitter(),stderr:new EventEmitter(),kill:()=>{kills++;return true;}});
    const rawLink=fs.readlinkSync,rawRead=fs.readFileSync,rawWrite=fs.writeSync,target=path.join(folder,'decoder.stderr');
    fs.readlinkSync=(name,...args)=>name==='/proc/99999999/exe'?identity.path:rawLink(name,...args);
    fs.readFileSync=(name,...args)=>name==='/proc/99999999/maps'?Buffer.from('1-2 r-xp 00000000 00:01 1 '+identity.path+'\n'):rawRead(name,...args);
    fs.writeSync=function(fd,bytes,...args){if(rawLink('/proc/self/fd/'+fd)!==target||mode==='ordinary')return rawWrite(fd,bytes,...args);
      writes++;if(mode==='zero')return 0;const prefix=bytes.subarray(0,Math.floor(bytes.length/2));rawWrite(fd,prefix);
      if(mode==='throw')throw Error('injected EIO after actual prefix');return mode==='invalid'?bytes.length+1:mode==='lie'?bytes.length:prefix.length;};
    try{const guard=R.decoderGuard(tools,input,folder,'decoder',{execute:()=>child,onClose:()=>{closed++;}});
      guard.spawn('ffmpeg',['-v','error','-i',input,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],{stdio:['ignore','pipe','pipe']});
      child.stdout.emit('data',Buffer.alloc(S.LIMITS.frameRgbBytes));assert.doesNotThrow(()=>child.stderr.emit('data',Buffer.alloc(1000,113)));
      if(!['ordinary','lie'].includes(mode))assert.doesNotThrow(()=>child.stderr.emit('data',Buffer.alloc(1000,113)));
      assert.doesNotThrow(()=>child.emit('close',0,null));const got=guard.state;assert.equal(closed,1);assert.equal(got.stderrClosed,true);assert.equal(got.stderrRetainedBytes,fs.statSync(target).size);
      if(mode==='ordinary'){assert.equal(kills,0);assert.equal(guard.finish(),got);assert.equal(got.stderrBytes,1000);assert.equal(got.stderrAcknowledgedBytes,1000);}
      else{assert.equal(writes,1);assert.ok(got.stderrRetentionError);assert.equal(got.stderrAcknowledgedBytes,mode==='partial'?500:mode==='lie'?1000:0);
        assert.equal(got.stderrRetainedBytes,mode==='zero'?0:500);assert.throws(()=>guard.finish());assert.throws(()=>R.admitDecoded({...got,error:null,stderrRetentionError:null}));}
    }finally{fs.readlinkSync=rawLink;fs.readFileSync=rawRead;fs.writeSync=rawWrite;}}
}));
test('decoder intake rechecks stderr closure counts and actual identity even after an alleged successful replay',()=>temporary(root=>{
  const R=feature(),row={...retainedStderr(root),returncode:0,timedOut:false,bytes:518340,frames:1,mappingsComplete:true,rgbSha256:'a'.repeat(64)};
  assert.equal(R.admitDecoded(row),true);
  for(const mutation of [x=>delete x.stderr,x=>x.stderrClosed=false,x=>x.stderrBytes++,x=>x.stderrAcknowledgedBytes++,
    x=>x.stderrRetainedBytes++,x=>x.stderrRetentionError='previous fault',x=>x.stderr.bytes++]){const changed=structuredClone(row);mutation(changed);assert.throws(()=>R.admitDecoded(changed));}
  fs.appendFileSync(row.stderr.path,'changed');assert.throws(()=>R.admitDecoded(row));
}));
