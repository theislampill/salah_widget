'use strict';
// Synthetic clocks and scenes execute the actual original and transformed code.
// No browser, native measurement, physical-device or human evidence is claimed.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const {spawnSync}=require('node:child_process'),{pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'../../..'),helper=path.join(__dirname,'r0035_costs.mjs');
const names=['spectralFlux','psfRaster','calendarTransfer','nominalCompose','envelopeBounds',
  'lowerBoundCompose','upperBoundCompose','variableSelection','patchWeights','inputGathers',
  'centerWithdrawal','withdrawalCompose','centerRanking'];
async function collector(){
  assert.ok(fs.existsSync(helper),'separate aggregate collector has not been implemented');
  let now=100;
  const context=vm.createContext({performance:{now:()=>now}});
  const mod=new vm.SourceTextModule(fs.readFileSync(helper,'utf8'),{context});
  await mod.link(()=>{throw Error('collector must have no external dependency');});await mod.evaluate();
  return {api:mod.namespace,set:n=>{now=n;},advance:n=>{now+=n;}};
}
const plain=x=>JSON.parse(JSON.stringify(x));
test('cost collector retains fixed aggregate bounds and same-worker durations without per-source histories',async()=>{
  const {api,set,advance}=await collector(),cost=api.createCosts(7);
  assert.deepEqual(Object.keys(cost.buckets),names);
  for(let i=0;i<200;i++){api.costStart(cost,'spectralFlux');advance(2);api.countCost(cost,'transportSamples',95);api.costEnd(cost,'spectralFlux');}
  api.finishCosts(cost,'COMPLETE');
  assert.equal(cost.clockDomain,'worker-performance-now-ms');assert.equal(cost.epoch,7);
  assert.equal(cost.status,'COMPLETE');assert.equal(cost.active,null);
  assert.deepEqual(plain(cost.buckets.spectralFlux),{calls:200,completed:200,failed:0,ms:400});
  assert.equal(cost.counts.transportSamples,19000);
  assert.equal(Object.keys(cost.buckets).length,13);assert.ok(JSON.stringify(cost).length<4000);
  assert.equal('events' in cost,false);assert.equal('stars' in cost,false);
  const frozen=JSON.stringify(cost);set(900);api.countCost(cost,'transportSamples');
  assert.equal(cost.counts.transportSamples,19000);assert.equal(cost.faults.lifecycle,true);
  assert.notEqual(JSON.stringify(cost),frozen);
});
test('failed costs retain completed and interrupted work separately without inventing later buckets',async()=>{
  const {api,advance}=await collector(),cost=api.createCosts(8);
  api.costStart(cost,'spectralFlux');advance(3);api.costEnd(cost,'spectralFlux');
  api.costStart(cost,'psfRaster');advance(4);api.finishCosts(cost,'FAILED');
  assert.deepEqual(plain(cost.buckets.spectralFlux),{calls:1,completed:1,failed:0,ms:3});
  assert.deepEqual(plain(cost.buckets.psfRaster),{calls:1,completed:0,failed:1,ms:4});
  assert.equal(cost.buckets.calendarTransfer.calls,0);assert.equal(cost.status,'FAILED');
  assert.equal(cost.active,null);assert.ok(Object.values(cost.faults).every(v=>v===false));
});
test('bad clocks, overlapping marks, unknown buckets and unsafe counts remain inadmissible diagnostics',async()=>{
  for(const fault of ['clock','overlap','name','count']){
    const {api,set}=await collector(),cost=api.createCosts(9);
    api.costStart(cost,'spectralFlux');
    if(fault==='clock')set(99);
    if(fault==='overlap')api.costStart(cost,'psfRaster');
    if(fault==='name')api.countCost(cost,'inventedCounter',1);
    if(fault==='count')api.countCost(cost,'transportSamples',Infinity);
    api.costEnd(cost,'spectralFlux');api.finishCosts(cost,'COMPLETE');
    assert.equal(cost.faults[fault],true,fault);
    assert.equal('inventedCounter' in cost.counts,false);
  }
});

let modulesPromise;
async function modules(){
  if(modulesPromise)return modulesPromise;
  modulesPromise=(async()=>{
    const mat=path.join(__dirname,'r0035_cost_materialize.py');
    assert.ok(fs.existsSync(mat),'separate reversible cost materializer has not been implemented');
    const run=spawnSync(process.env.PYTHON||'python3',['-B','-c',
      "import json,pathlib,sys;sys.path.insert(0,'tools/qa/hosted-native');import r0035_cost_materialize as m;print(json.dumps({n:m.transform(n,pathlib.Path(n).read_bytes())[0].decode() for n in m.MODIFIED}))"],
      {cwd:root,encoding:'utf8',maxBuffer:1024*1024});
    assert.equal(run.status,0,run.stderr);const changed=JSON.parse(run.stdout);
    const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'r0035-cost-parity-'));
    process.on('exit',()=>fs.rmSync(tmp,{recursive:true,force:true}));
    for(const mode of ['original','costs']){
      const target=path.join(tmp,mode),queue=['tools/r0035/stellar_replay.mjs','tools/r0035/prepared_replay.mjs'],done=new Set();
      while(queue.length){
        const name=queue.pop();if(done.has(name))continue;done.add(name);
        const original=fs.readFileSync(path.join(root,name),'utf8');
        const code=mode==='costs'&&changed[name]?changed[name]:original;
        const dest=path.join(target,name);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,code);
        for(const match of original.matchAll(/(?:import|export)\s[^;]*?from\s*['"]([^'"]+)['"]/g)){
          if(match[1].startsWith('.'))queue.push(path.posix.normalize(path.posix.join(path.posix.dirname(name),match[1])));
        }
      }
      if(mode==='costs')fs.copyFileSync(helper,path.join(target,'tools/r0035/r0035_costs.mjs'));
    }
    // The original lab already patches native-host for publication hooks. Use
    // that exact pinned recipe in both test copies before importing its encoder.
    const host=spawnSync(process.env.PYTHON||'python3',['-B','-c',
      "import pathlib,sys,hashlib,importlib.util;sys.path.insert(0,'tools/qa/hosted-native');import r0035_cost_materialize as m;p=pathlib.Path('tools/r0035/materialize_lab.py');assert hashlib.sha256(p.read_bytes()).hexdigest()==m.pins()['files'][str(p)]['sha256'];s=importlib.util.spec_from_file_location('original_lab_fixture',p);r=importlib.util.module_from_spec(s);s.loader.exec_module(r);[r.patch_refined(pathlib.Path(target),'real-sky/native-host.mjs') for target in sys.argv[1:]]",
      path.join(tmp,'original'),path.join(tmp,'costs')],{cwd:root,encoding:'utf8'});
    assert.equal(host.status,0,host.stderr);
    const imported={};
    for(const mode of ['original','costs']){
      const base=path.join(tmp,mode),load=name=>import(pathToFileURL(path.join(base,name)).href);
      imported[mode]={...await load('tools/r0035/stellar_replay.mjs'),...await load('tools/r0035/prepared_replay.mjs'),
        ...await load('real-sky/core/src/spectral.mjs'),...await load('real-sky/core/src/atmosphere.mjs'),
        ...await load('real-sky/core/src/renderer.mjs')};
      if(mode==='costs')Object.assign(imported[mode],await load('tools/r0035/r0035_costs.mjs'));
    }
    return {changed,fixtureRoots:{original:path.join(tmp,'original'),costs:path.join(tmp,'costs')},...imported};
  })();return modulesPromise;
}
test('physical import closure includes the pinned original lab host hooks in both parity copies',async()=>{
  const data=await modules(),{createHash}=require('node:crypto');
  for(const base of Object.values(data.fixtureRoots)){
    const body=fs.readFileSync(path.join(base,'real-sky/native-host.mjs'));
    assert.equal(createHash('sha256').update(body).digest('hex'),'f8497768c0c08c90434aa921ea532718f1aa928b602a9bba85ffcd8417d6a824');
  }
});
function sourceInputs(api){
  const width=16,height=11;
  const sources=[{id:'synthetic:1',hip:17,vmag:1,bv:.2,x:.4,y:.8,altDeg:9,azDeg:10,visible:true},
    {id:'synthetic:2',hip:18,vmag:3,bv:.4,x:7.3,y:5.4,altDeg:31,azDeg:20,visible:true},
    {id:'synthetic:3',hip:19,vmag:5,bv:1.1,x:7.7,y:5.2,altDeg:43,azDeg:30,visible:true},
    {id:'synthetic:below',hip:20,vmag:1,bv:.2,x:1,y:1,altDeg:0,visible:true},
    {id:'synthetic:ineligible',hip:21,vmag:1,bv:.2,x:2,y:2,altDeg:8,visible:true}];
  const atmosphere=api.normaliseAtmosphere({}),catalogue=new Map(sources.map(s=>[s.id,s]));
  const sourceDiagnostics=sources.map((s,i)=>({id:s.id,detectable:i<3,backgroundComplete:true,cloudTransmission:.83,
    scintillationFactor:1,vFlux:api.spectralStarFlux(s,s.altDeg,{}, {response:'CIE1931',
      transportAt:w=>api.directTransmission(w,s.altDeg,atmosphere,.83)}).vFlux}));
  return {catalogue,frame:{status:'ready',diffuseAsset:{mode:'registered'},sources,
    raster:{width,height,atmosphere,sourceDiagnostics}}};
}
test('actual full-population spectral transport and clipped PSFs preserve exact flux and patch values',async()=>{
  const {original,costs}=await modules(),input=sourceInputs(original),trace=costs.createCosts(1);
  const before=original.prepareStars(input.frame,input.catalogue),after=costs.prepareStars(input.frame,input.catalogue,trace);
  costs.finishCosts(trace,'COMPLETE');assert.deepEqual(after,before);
  assert.equal(trace.counts.fullInputSources,5);assert.equal(trace.counts.spectralSources,3);
  assert.equal(trace.counts.transportSamples,285);assert.equal(trace.counts.patchCalls,3);
  assert.equal(trace.counts.referencePsfChannels,9);assert.equal(trace.counts.referenceGaussianCalls,18);
  assert.equal(trace.buckets.spectralFlux.completed,3);assert.equal(trace.buckets.psfRaster.completed,3);
  for(const sources of [[],input.frame.sources]){
    const frame={...input.frame,sources,raster:{...input.frame.raster,
      sourceDiagnostics:input.frame.raster.sourceDiagnostics.map(row=>({...row,detectable:false}))}};
    const empty=costs.createCosts(20);
    assert.deepEqual(costs.prepareStars(frame,input.catalogue,empty),original.prepareStars(frame,input.catalogue));
    costs.finishCosts(empty,'COMPLETE');assert.equal(empty.counts.fullInputSources,sources.length);
    assert.equal(empty.counts.spectralSources,0);assert.equal(empty.counts.transportSamples,0);assert.equal(empty.counts.patchCalls,0);
  }
  assert.equal(after[2].vmag,5,'stellar preparation remains before replay scope filtering');
});
test('original flux mismatch preserves the same error and retains only the spectral prefix',async()=>{
  const {original,costs}=await modules(),input=sourceInputs(original),trace=costs.createCosts(2);
  input.frame.raster.sourceDiagnostics[0].vFlux+=1;
  assert.throws(()=>original.prepareStars(input.frame,input.catalogue),/Reference flux disagrees with worker/);
  assert.throws(()=>costs.prepareStars(input.frame,input.catalogue,trace),/Reference flux disagrees with worker/);
  costs.finishCosts(trace,'FAILED');assert.equal(trace.counts.transportSamples,95);
  assert.equal(trace.buckets.spectralFlux.completed,1);assert.equal(trace.buckets.psfRaster.calls,0);
});
test('zero-flux patch keeps original zero bytes and records no derived drawn Gaussian calls',async()=>{
  const {original,costs}=await modules(),trace=costs.createCosts(3);
  const star={id:'synthetic:zero',x:.4,y:.8,altDeg:9,vmag:1,detectable:true};
  assert.deepEqual(costs.preparePatch(star,{rgb:[0,0,0]},16,11,trace),original.preparePatch(star,{rgb:[0,0,0]},16,11));
  costs.finishCosts(trace,'COMPLETE');assert.equal(trace.counts.patchCalls,1);
  assert.equal(trace.counts.drawnPatches,0);assert.equal(trace.counts.referenceGaussianCalls,0);
});
test('actual prepared replay preserves nominal, full-frame, sampled and masked bytes across existing configurations',async()=>{
  const {original,costs}=await modules(),input=sourceInputs(original),patches=original.prepareStars(input.frame,input.catalogue);
  const {width,height}=input.frame.raster,n=width*height;
  const gas=Float64Array.from({length:3*n},(_,i)=>.0005+.00001*(i%11)),diffuse=new Float64Array(3*n).fill(.0002);
  const stellar=new Float64Array(3*n);
  for(const star of patches)for(let y=0;y<star.h;y++)for(let x=0;x<star.w;x++)for(let k=0;k<3;k++)
    stellar[3*((star.y0+y)*width+star.x0+x)+k]+=star.linear[3*(y*star.w+x)+k];
  const raster={width,height,effectiveExposure:11,linear:gas.map((v,i)=>v+stellar[i]+diffuse[i]),
    stellarLinear:stellar,skyBackgroundLinear:gas,diffusePhysicalLinear:diffuse};
  const cloud=new Uint8ClampedArray(4*n),moon=cloud.slice(),mask=new Float64Array(n);
  for(let p=0;p<n;p++){mask[p]=p%width<6?0:p%width===6?.4:1;
    cloud.set([94,130,163,[0,127,255][Math.floor(p/width)%3]],4*p);moon.set([25,54,90,mask[p]===0?235:0],4*p);}
  const fg={mask,cloudRGBA:cloud,moonRGBA:moon,glass:[{x:4,y:2,width:4,height:4}]};
  let epoch=0;
  for(const preview of [false,true])for(const scope of ['all','preview-members'])for(const glassFactor of [0,.5,1]){
    const config={scope,multiplier:2,glassFactor,margin:0},r={...raster,starPreview:preview},trace=costs.createCosts(++epoch);
    const a=original.prepareReplay(r,patches,config,fg),b=costs.prepareReplay(r,patches,config,fg,trace);
    costs.finishCosts(trace,'COMPLETE');
    for(const key of ['nominal','indices','sourceCount','contributingCenters'])assert.deepEqual(b[key],a[key]);
    for(let i=0;i<12;i++){
      const utc=1794182400000+i*1000/60,expected=a.present(utc),actual=b.present(utc);
      assert.deepEqual(actual,expected);assert.deepEqual(actual.rgba,original.replayFrame(r,patches,utc,config,fg).rgba);
      assert.deepEqual(costs.stellarOverlay(b,actual.rgba),original.stellarOverlay(a,expected.rgba));
    }
    assert.deepEqual(b.present(1794182400000,{paused:true}),a.present(1794182400000,{paused:true}));
    assert.equal(trace.counts.replayInputSources,3);assert.equal(trace.counts.replaySelectedSources,b.sourceCount);
    assert.equal(trace.counts.variablePixels,b.indices.length);assert.equal(trace.counts.fullComposeCalls,3);
    assert.equal(trace.counts.centerComposeCalls,1);assert.equal(trace.counts.withdrawalCenters,b.sourceCount);
    assert.ok(names.slice(2).every(k=>trace.buckets[k].calls===1&&trace.buckets[k].completed===1));
  }
});

async function workerRun(mode,nominalFault=false){
  const data=await modules(),api=data[mode],original=data.original,input=sourceInputs(original);
  const patches=original.prepareStars(input.frame,input.catalogue),{width,height}=input.frame.raster,n=width*height;
  const stellar=new Float64Array(3*n),gas=new Float64Array(3*n).fill(.0005);
  for(const star of patches)for(let y=0;y<star.h;y++)for(let x=0;x<star.w;x++)for(let k=0;k<3;k++)
    stellar[3*((star.y0+y)*width+star.x0+x)+k]+=star.linear[3*(y*star.w+x)+k];
  Object.assign(input.frame.raster,{effectiveExposure:11,stellarLinear:stellar,skyBackgroundLinear:gas,
    diffusePhysicalLinear:new Float64Array(3*n),linear:gas.map((v,i)=>v+stellar[i]),physicalState:{moon:{altDeg:-90}}});
  const config={scope:'all',multiplier:1,glassFactor:.5,margin:4},foreground={glass:[]};
  const nominal=original.prepareReplay(input.frame.raster,patches,config,foreground).nominal;
  if(nominalFault)nominal[0]^=1;
  for(const row of input.frame.raster.sourceDiagnostics){const s=input.catalogue.get(row.id);row.vmag=s.vmag;row.hip=s.hip;}
  const bytes=new TextEncoder().encode(JSON.stringify({stars:[...input.catalogue.values()]}));
  const digest=bytes=>require('node:crypto').createHash('sha256').update(bytes).digest('hex');
  input.frame.catalogue={sha256:digest(bytes)};
  const messages=[],context=vm.createContext({performance,URL,TextDecoder,Uint8Array,Uint32Array,Uint8ClampedArray,Float64Array,
    self:{postMessage:(message,transfers)=>messages.push({message:structuredClone(message),transfers:transfers?.length??0})},
    fetch:async()=>({ok:true,arrayBuffer:async()=>bytes.buffer})});
  const dependencies={
    'stellar_replay.mjs':{prepareStars:api.prepareStars,preparePatch:api.preparePatch,glassMembership:api.glassMembership},
    'prepared_replay.mjs':{prepareReplay:api.prepareReplay,stellarOverlay:api.stellarOverlay},
    'r0035_costs.mjs':Object.fromEntries(['createCosts','costStart','costEnd','countCost','finishCosts'].map(k=>[k,api[k]])),
    'sha256.mjs':{sha256Hex:digest},'spectral.mjs':{spectralStarFlux:api.spectralStarFlux},
    'atmosphere.mjs':{directTransmission:api.directTransmission,normaliseAtmosphere:api.normaliseAtmosphere},
    'projection.mjs':{projectPerspective:()=>{throw Error('bounded projection adapter must not be called');}},
    'scene.mjs':{projectCatalogue:catalogue=>catalogue.stars,discOccults:()=>false},
    'visibility.mjs':{displayVisibility:()=>({detectable:true})},'photometry.mjs':{luminance:rgb=>.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]}
  };
  const code=mode==='original'?fs.readFileSync(path.join(root,'tools/r0035/lab_worker.mjs'),'utf8'):data.changed['tools/r0035/lab_worker.mjs'];
  const mod=new vm.SourceTextModule(code,{context,initializeImportMeta:meta=>{meta.url='file:///synthetic/tools/r0035/lab_worker.mjs';}});
  await mod.link(specifier=>{const values=dependencies[path.basename(specifier)];assert.ok(values,specifier);
    return new vm.SyntheticModule(Object.keys(values),function(){for(const [key,value]of Object.entries(values))this.setExport(key,value);},{context});});
  await mod.evaluate();
  await context.self.onmessage({data:{op:'prepare',epoch:4,frame:input.frame,job:{observer:{},options:{view:{}}},config,foreground,nominal}});
  if(!nominalFault)await context.self.onmessage({data:{op:'sample',epoch:4,utcMs:1794182400000,motion:{}}});
  return messages;
}
test('actual worker passes the local collector through real stellar and replay functions without changing original ready/sample outputs',async()=>{
  const original=await workerRun('original'),costs=await workerRun('costs');
  assert.equal(costs[0].message.op,'ready');const trace=costs[0].message.r0035Stages;delete costs[0].message.r0035Stages;
  assert.deepEqual(costs,original);assert.equal(costs[1].transfers,2);
  assert.equal(trace.costs.status,'COMPLETE');assert.equal(trace.costs.epoch,4);
  assert.equal(trace.costs.counts.fullInputSources,5);assert.equal(trace.costs.counts.transportSamples,285);
  assert.equal(trace.costs.counts.replayInputSources,3);assert.equal(trace.costs.counts.fullComposeCalls,3);
  assert.equal(trace.costs.counts.centerComposeCalls,1);assert.equal(trace.costs.active,null);
  assert.equal(trace.marks.at(-1).kind,'ready-post');assert.ok(trace.costs.endedAt<=trace.marks.at(-1).at);
});
test('actual worker nominal mismatch retains completed cost totals with the unchanged failed reply',async()=>{
  const original=await workerRun('original',true),costs=await workerRun('costs',true);
  assert.equal(costs[0].message.op,'failed');const trace=costs[0].message.r0035Stages;delete costs[0].message.r0035Stages;
  assert.deepEqual(costs,original);assert.match(costs[0].message.reason,/Nominal native bytes mismatch/);
  assert.equal(trace.costs.status,'FAILED');assert.equal(trace.costs.buckets.centerRanking.completed,1);
  assert.equal(trace.marks.at(-1).kind,'failed');assert.equal(trace.marks.at(-2).kind,'replay-prepared');
});
