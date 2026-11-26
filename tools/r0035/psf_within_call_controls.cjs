'use strict';
// Source-only parity. No browser, native timing, capture or perceptual evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createHash}=require('node:crypto'),{pathToFileURL}=require('node:url');
const {spawnSync}=require('node:child_process'),os=require('node:os');
const root=path.resolve(__dirname,'../..'),helper=path.join(__dirname,'psf_within_call.mjs');
const rendererPath='real-sky/core/src/renderer.mjs',stellarPath='tools/r0035/stellar_replay.mjs';
const derivedPath='tools/r0035/psf_within_call_renderer.mjs';
const read=name=>fs.readFileSync(path.join(root,name));
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const asBytes=view=>Buffer.from(view.buffer,view.byteOffset,view.byteLength);
function exact(a,b,label){assert.equal(a.byteLength,b.byteLength,label+' length');assert.ok(asBytes(a).equals(asBytes(b)),label+' complete binary64/byte output');}
const plain=value=>JSON.parse(JSON.stringify(value));
let helperPromise;
async function experiment(){
  assert.ok(fs.existsSync(helper),'within-call PSF experiment has not been implemented');
  return helperPromise??=(import(pathToFileURL(helper).href));
}

async function graph(entry,replacements=new Map(),math=Math,globals={}){
  // TextEncoder's result and the VM's typed-array checks share one platform
  // constructor set, as they do within an actual realm. No SHA guard is changed.
  const context=vm.createContext({performance,TextDecoder,TextEncoder,URL,AbortController,
    ArrayBuffer,DataView,Uint8Array,Uint8ClampedArray,Uint32Array,Int32Array,Float64Array,Math:math,...globals});
  const modules=new Map(),inputs=new Map();
  function module(name){
    assert.ok(!name.startsWith('../')&&!path.isAbsolute(name),'local source closure');
    if(modules.has(name))return modules.get(name);
    const bytes=replacements.get(name)??read(name);inputs.set(name,{bytes:bytes.length,sha256:digest(bytes)});
    const mod=new vm.SourceTextModule(bytes.toString('utf8'),{context,identifier:name,
      initializeImportMeta:meta=>{meta.url=pathToFileURL(path.join(root,name)).href;}});
    modules.set(name,mod);return mod;
  }
  const main=module(entry);
  await main.link((specifier,importer)=>{
    assert.ok(specifier.startsWith('.'),'no foreign imports in mathematical source closure');
    return module(path.posix.normalize(path.posix.join(path.posix.dirname(importer.identifier),specifier)));
  });
  await main.evaluate();return {api:main.namespace,inputs};
}
async function rawPair(candidateTransform=code=>code,maths=[Math,Math]){
  const api=await experiment(),original=read(rendererPath),candidate=api.deriveRenderer(original);
  return {original:await graph(rendererPath,new Map(),maths[0]),
    candidate:await graph(derivedPath,new Map([[derivedPath,candidateTransform(candidate)]]),maths[1]),
    code:candidate,api};
}
function initial(width,height,mode=0){
  return Float64Array.from({length:width*height*3},(_,i)=>mode===0?0:mode===1?(i%7===0?-0:(i%19)*.003):[0,1e-290,1e-12,.137,1e20][i%5]);
}
function apply(api,input,buffer){return api.splatGaussian(buffer,input.width,input.height,input.x,input.y,input.rgb,input.sigma);}
function population(){
  const cases=[];
  for(const [width,height] of [[1,1],[2,7],[17,13],[31,23]])for(const sigma of [.05,.1,.55,2.2,8,48,100]){
    const support=Math.ceil(6*sigma)+1;
    for(const [x,y] of [[0,0],[.49999999999999994,.5],[width-.0000000000000036,height-1],[-.25,2.75],
      [width+.25,height-.5],[-support-2,0],[width+support+2,height+support+2]])
      cases.push({width,height,x,y,sigma,rgb:[.123456789,0,3.141592653589793]});
  }
  let seed=0x35c0ffee;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  for(let i=0;i<512;i++){
    const width=1+Math.floor(31*random()),height=1+Math.floor(23*random());
    const sigma=[.05,.55,2.2,100,.05+99.95*random()][i%5],margin=Math.ceil(6*sigma)+2;
    cases.push({width,height,x:-margin+(width+2*margin)*random(),y:-margin+(height+2*margin)*random(),sigma,
      rgb:[random()*10**(-12+24*random()),i%3?random():0,random()]});
  }
  return cases;
}
const rawInputs=population();
function rawParity(a,b,inputs=rawInputs){
  let values=0;
  for(let n=0;n<inputs.length;n++){
    const input=inputs[n],before=initial(input.width,input.height,n%3),after=before.slice();
    assert.equal(apply(a,input,before),undefined);assert.equal(apply(b,input,after),undefined);
    exact(after,before,'raw case '+n);values+=before.length;
  }
  return {cases:inputs.length,comparedFloat64Values:values};
}
test('guarded transforms reverse to exact source and admit only actual paired bytes',async()=>{
  const api=await experiment(),renderer=read(rendererPath),stellar=read(stellarPath);
  const candidate=api.deriveRenderer(renderer),redirected=api.deriveStellarReplay(stellar);
  assert.ok(api.restoreRenderer(candidate).equals(renderer));assert.ok(api.restoreStellarReplay(redirected).equals(stellar));
  const identity=api.experimentIdentity(renderer,candidate,stellar,redirected);
  assert.equal(identity.protocol,'r0035-within-call-psf/1');assert.equal(identity.nativeQualification,'NOT_RUN');
  assert.equal(identity.referenceRenderer.sha256,'173283b65c4b89cd1c85067131183ad2a306199850f41ae070ede463de5add6b');
  assert.equal(identity.candidateRenderer.sha256,digest(candidate));
  assert.equal(identity.originalStellarReplay.sha256,digest(stellar));
  assert.equal(identity.redirectedStellarReplay.sha256,digest(redirected));
});
test('reference drift, inverse mutations and copied identities cannot admit a derivative',async()=>{
  const api=await experiment(),renderer=read(rendererPath),stellar=read(stellarPath);
  const candidate=api.deriveRenderer(renderer),redirected=api.deriveStellarReplay(stellar);
  for(const original of [Buffer.concat([renderer,Buffer.from('\n')]),Buffer.from(renderer.toString().replace('6*sigma','5*sigma'))])
    assert.throws(()=>api.deriveRenderer(original),/reference|identity|digest/i);
  for(const source of [Buffer.from(stellar.toString().replace('x:star.x-x0','x:Math.floor(star.x)-x0')),Buffer.concat([stellar,Buffer.from('\n')])])
    assert.throws(()=>api.deriveStellarReplay(source),/reference|identity|digest/i);
  for(const bytes of [Buffer.concat([candidate,Buffer.from('\n')]),Buffer.from(candidate.toString().replace('wx*wy','wx+wy'))]){
    assert.throws(()=>api.restoreRenderer(bytes));assert.throws(()=>api.experimentIdentity(renderer,bytes,stellar,redirected));
  }
  assert.throws(()=>api.restoreStellarReplay(Buffer.concat([redirected,Buffer.from('\n')])));
  assert.throws(()=>api.experimentIdentity(renderer,candidate,stellar,stellar));
  assert.throws(()=>api.deriveRenderer(renderer.toString()),/bytes|Buffer/);
});
test('complete Float64 buffers agree for bounded clipping, subpixel, sigma and flux populations',async t=>{
  const pair=await rawPair();t.diagnostic(JSON.stringify(rawParity(pair.original.api,pair.candidate.api)));
  // The public reference does not validate dimensions independently. Preserve
  // its ordinary numeric no-op/fractional behavior rather than inventing a guard.
  for(const input of [{width:0,height:2,x:0,y:0},{width:-1,height:-1,x:0,y:0},{width:2.5,height:2,x:.4,y:.8}]){
    Object.assign(input,{sigma:.55,rgb:[1,2,3]});
    const a=new Float64Array(input.width*input.height*3),b=a.slice();
    apply(pair.original.api,input,a);apply(pair.candidate.api,input,b);exact(a,b,'unchanged dimension behavior');
  }
});
test('separate calls keep location, width, channel and component values independent on overlapping buffers',async()=>{
  const pair=await rawPair(),a=initial(31,23,1),b=a.slice();
  for(let n=0;n<96;n++){
    const input={width:31,height:23,x:2.1+(n%19)*.733,y:-.8+(n%17)*.83,
      sigma:[.05,.55,2.2,8,100][n%5],rgb:[0,0,0]};input.rgb[n%3]=(n+1)*.137;
    apply(pair.original.api,input,a);apply(pair.candidate.api,input,b);exact(a,b,'overlapping call '+n);
  }
});
test('original validation order, exception types/messages and untouched buffers remain equal',async()=>{
  const pair=await rawPair();
  const changes=[{x:NaN},{x:Infinity},{x:'1'},{y:NaN},{y:-Infinity},{sigma:0},{sigma:.049999999999999996},
    {sigma:100.00000000000001},{sigma:NaN},{rgb:[-1,0,0]},{rgb:[NaN,0,0]},
    {rgb:[Infinity,0,0]},{rgb:[0,0]},{rgb:new Float64Array([1,2,3])},{bufferLength:1},
    {x:NaN,y:NaN,sigma:NaN,rgb:null,bufferLength:0},{y:NaN,sigma:NaN,rgb:null},{sigma:NaN,rgb:null},{rgb:null}];
  for(const change of changes){
    const input={width:9,height:7,x:3.2,y:2.8,sigma:.55,rgb:[1,2,3],...change};
    const a=new Float64Array(change.bufferLength??189).fill(.125),b=a.slice();let first,second;
    try{apply(pair.original.api,input,a);}catch(e){first={name:e.name,message:e.message};}
    try{apply(pair.candidate.api,input,b);}catch(e){second={name:e.name,message:e.message};}
    assert.ok(first,'the reference must throw');assert.deepEqual(second,first);exact(b,a,'exception prefix');
    assert.ok(a.every(v=>v===.125));
  }
});
function accessRun(api,failAt){
  const backing=initial(7,5,1),events=[];let writes=0;
  const buffer=new Proxy({}, {get(_,key){events.push(['get',String(key)]);return key==='length'?backing.length:backing[key];},
    set(_,key,value){events.push(['set',String(key),value]);if(++writes===failAt)throw new TypeError('intentional buffer write fault');backing[key]=value;return true;}});
  const rgb=[1,2,3];for(let c=0;c<3;c++)Object.defineProperty(rgb,c,{get(){events.push(['rgb',c]);return c+.137;}});
  let error=null;try{api.splatGaussian(buffer,7,5,2.2,1.7,rgb,.55);}catch(e){error={name:e.name,message:e.message};}
  return {backing,events,error};
}
test('tested RGB reads and buffer access faults retain row/pixel/channel order and partial writes',async()=>{
  const pair=await rawPair();
  for(const failAt of [1,2,4,29,83,Infinity]){
    const a=accessRun(pair.original.api,failAt),b=accessRun(pair.candidate.api,failAt);
    assert.deepEqual(b.error,a.error);assert.deepEqual(b.events,a.events);exact(b.backing,a.backing,'access fault prefix');
  }
});
test('horizontal reuse reduces actual exp evaluations only within one invocation',async t=>{
  const counts=[0,0],maths=counts.map((_,i)=>{const math=Object.create(Math);math.exp=value=>{counts[i]++;return Math.exp(value);};return math;});
  const pair=await rawPair(code=>code,maths),input={width:17,height:13,x:8.25,y:6.75,sigma:2.2,rgb:[.137,0,.913]};
  const a=initial(17,13,1),b=a.slice();counts.fill(0);
  apply(pair.original.api,input,a);apply(pair.candidate.api,input,b);exact(b,a,'counted math');
  assert.deepEqual(counts,[468,60]);t.diagnostic(JSON.stringify({referenceExpCalls:counts[0],candidateExpCalls:counts[1],nativeSpeedup:'NOT_MEASURED'}));
  counts.fill(0);input.y=100;apply(pair.original.api,input,a);apply(pair.candidate.api,input,b);
  assert.deepEqual(counts,[0,0]);exact(b,a,'empty support');
});
test('lazy first-row reuse preserves tested first-row math exceptions and write prefixes',async()=>{
  for(const failAt of [1,2,3,6,12]){
    let armed=false;
    const counts=[0,0],maths=counts.map((_,i)=>{const math=Object.create(Math);math.exp=value=>{
      if(++counts[i]===failAt&&armed)throw new RangeError('intentional first-row math fault');return Math.exp(value);};return math;});
    const pair=await rawPair(code=>code,maths),a=initial(7,5,1),b=a.slice();counts.fill(0);armed=true;let first,second;
    const input={width:7,height:5,x:3.2,y:2.2,sigma:2.2,rgb:[1,2,3]};
    try{apply(pair.original.api,input,a);}catch(e){first={name:e.name,message:e.message};}
    try{apply(pair.candidate.api,input,b);}catch(e){second={name:e.name,message:e.message};}
    assert.ok(first);assert.deepEqual(second,first);assert.deepEqual(counts,[failAt,failAt]);exact(a,b,'first-row fault');
  }
});
test('full-output controls reject arithmetic, precision, clipping, subpixel and stale-cache mutants',async()=>{
  const pair=await rawPair();
  const transforms={
    subpixel:code=>code.replace('(i+1-x)*inv','(i+.5-x)*inv'),
    clipping:code=>code.replace('xs=Math.max(0,ix-support)','xs=Math.max(0,ix-support+1)'),
    order:code=>code.replace('buffer[k+c]+=rgb[c]*w','buffer[k+c]+=(rgb[c]*wx)*wy'),
    float32:code=>code.replace('horizontal[i-xs]=.5*','horizontal[i-xs]=Math.fround(.5*').replace('erf((i-x)*inv)))','erf((i-x)*inv))))'),
    stale:code=>code.replace('const horizontal=[];','const horizontal=globalThis.r35Weights??=([]);').replace('j===ys?','horizontal[i-xs]===undefined?')
  };
  for(const [name,transform] of Object.entries(transforms)){
    const original=pair.code.toString(),mutant=Buffer.from(transform(original));assert.notEqual(mutant.toString(),original,name+' mutation applied');
    const changed=await graph(derivedPath,new Map([[derivedPath,mutant]]));
    assert.throws(()=>rawParity(pair.original.api,changed.api),/complete binary64/,name+' must change full output');
    assert.throws(()=>pair.api.restoreRenderer(mutant),undefined,name+' cannot be admitted');
  }
});

test('unchanged renderStars preserves separate optical channels, components, DPR and output metadata',async t=>{
  const pair=await rawPair(),stars=[
    {id:'synthetic:a',x:.15,y:.8,altDeg:9,vmag:1,bv:.2,hip:17},
    {id:'synthetic:b',x:7.35,y:5.8,altDeg:43,vmag:3,bv:1.1,hip:18},
    {id:'synthetic:c',x:7.7,y:5.2,altDeg:21,vmag:4,bv:.4,hip:19},
    {id:'synthetic:outside',x:22.7,y:15.2,altDeg:12,vmag:4,bv:0},
    {id:'synthetic:disabled',x:3,y:4,altDeg:10,emission:{enabled:false}},
    {id:'synthetic:below',x:4,y:5,altDeg:-1}];
  let cases=0,values=0;
  for(const opticalPreset of ['reference','camera','eye'])for(const dpr of [.5,1,1.5,2,4]){
    const opts={width:17,height:11,dpr,opticalPreset,background:[.001,.002,.003],
      atmosphere:{cloudTransmission:.83},pixelTransmissionAt:(x,y)=>x<3?0:y<5?.4:1};
    const a=pair.original.api.renderStars(stars,opts),b=pair.candidate.api.renderStars(stars,opts);
    exact(a.linear,b.linear,'complete renderer '+opticalPreset+'/'+dpr);
    const metadata=value=>{const {linear,...rest}=value;return plain(rest);};assert.deepEqual(metadata(b),metadata(a));
    assert.equal(a.drawn,4);cases++;values+=a.linear.length;
  }
  t.diagnostic(JSON.stringify({rendererCases:cases,comparedFloat64Values:values}));
});

const dataPins={
  'vendor/real-sky/data/bright-stars.json':'da5002f0eda9ad3e0f2cc7c95ab423043feea61e8522239d2930ca1945beef2e',
  'vendor/real-sky/data/registered-starlight/runtime-manifest.json':'630f169f30b617d947b5e3199eb854e8027a34540dde008da57b925577b777f6',
  'vendor/real-sky/data/registered-starlight/V-nside128.json':'4e8458bbb6d8b3baa432908fac405e6b3ba85e1acc1e026af165efbca87dcf91'
};
let sourcePairPromise;
async function sourcePair(){
  if(sourcePairPromise)return sourcePairPromise;
  sourcePairPromise=(async()=>{
    const api=await experiment(),renderer=api.deriveRenderer(read(rendererPath)),stellar=api.deriveStellarReplay(read(stellarPath));
    const data=Object.fromEntries(Object.entries(dataPins).map(([name,sha])=>{
      const bytes=read(name);assert.equal(digest(bytes),sha,name+' actual original input');return [name,bytes];}));
    const recipe='tools/r0035/materialize_lab.py';
    assert.equal(digest(read(recipe)),'2b35b1862502ac28a34f6c782b1174c228e819d7d42ef7d6596ea79b432b3096');
    const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'r0035-psf-original-hooks-'));
    let host;
    try{
      fs.mkdirSync(path.join(tmp,'real-sky'));fs.writeFileSync(path.join(tmp,'real-sky/native-host.mjs'),read('real-sky/native-host.mjs'));
      const patched=spawnSync(process.env.PYTHON||'python3',['-B','-c',
        "import pathlib,sys,importlib.util;p=pathlib.Path('tools/r0035/materialize_lab.py');s=importlib.util.spec_from_file_location('original_r0035_lab',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.patch_refined(pathlib.Path(sys.argv[1]),'real-sky/native-host.mjs')",tmp],
        {cwd:root,encoding:'utf8'});
      assert.equal(patched.status,0,patched.stderr);host=fs.readFileSync(path.join(tmp,'real-sky/native-host.mjs'));
      assert.equal(digest(host),'f8497768c0c08c90434aa921ea532718f1aa928b602a9bba85ffcd8417d6a824');
    }finally{fs.rmSync(tmp,{recursive:true,force:true});}
    const entry='tools/r0035/psf_test_entry.mjs',code=Buffer.from(
      "export {prepareScene,replayObserver} from './qualification_scene.mjs';\n"+
      "export {prepareStars,preparePatch,replayFrame} from './stellar_replay.mjs';\n"+
      "export {prepareReplay,stellarOverlay} from './prepared_replay.mjs';\n"+
      "export {prepareLiveFrame} from './lab_worker.mjs';\n"+
      "export {nativeJob} from '../../real-sky/native-contract.mjs';\n"+
      "export {NativeSkyEngine} from '../../real-sky/native-engine.mjs';\n");
    const catalogue=data['vendor/real-sky/data/bright-stars.json'];
    const localFetch=async url=>{
      assert.equal(url.href,pathToFileURL(path.join(root,'vendor/real-sky/data/bright-stars.json')).href,'local catalogue read only');
      return {ok:true,arrayBuffer:async()=>Uint8Array.from(catalogue).buffer};
    };
    const originalMap=new Map([[entry,code],['real-sky/native-host.mjs',host]]),candidateMap=new Map(originalMap);
    candidateMap.set(derivedPath,renderer);candidateMap.set(stellarPath,stellar);
    const original=await graph(entry,originalMap,Math,{fetch:localFetch}),candidate=await graph(entry,candidateMap,Math,{fetch:localFetch});
    const expectedChanges=new Set([derivedPath,stellarPath]);
    for(const [name,value] of candidate.inputs){
      if(!expectedChanges.has(name))assert.deepEqual(value,original.inputs.get(name),'unchanged shared source '+name);
    }
    assert.equal(candidate.inputs.size,original.inputs.size+1);
    const pack={catalogueText:catalogue.toString(),manifestText:data['vendor/real-sky/data/registered-starlight/runtime-manifest.json'].toString(),
      assetTexts:{128:data['vendor/real-sky/data/registered-starlight/V-nside128.json'].toString()}};
    return {original,candidate,pack,catalogue:new Map(JSON.parse(pack.catalogueText).stars.map(s=>[s.id,s])),
      identity:api.experimentIdentity(read(rendererPath),renderer,read(stellarPath),stellar)};
  })();return sourcePairPromise;
}
let scenesPromise;
async function originalScenes(){
  if(scenesPromise)return scenesPromise;
  scenesPromise=(async()=>{
    const pair=await sourcePair(),rows=[],dark={};let values=0,patches=0;
    // Literal populations from the unchanged original R0035 reconstruction.
    const times=[['dark','2026-11-09T00:00:00Z',[169,1404]],['moonlit','2026-11-24T00:00:00Z',[158,1355]],
      ['nearFajr','2026-11-09T02:15:00Z',[134,1406]],['twilight','2026-11-09T03:15:00Z',[0,0]],['day','2026-11-09T09:00:00Z',[0,0]]];
    for(const [scene,time,counts] of times)for(const [tierIndex,tier] of ['preview','refined'].entries()){
      const snapshot={...pair.original.api.replayObserver,utcMs:Date.parse(time)};
      const a=await pair.original.api.prepareScene(pair.pack,snapshot,tier),b=await pair.candidate.api.prepareScene(pair.pack,snapshot,tier);
      assert.equal(a.stars.length,counts[tierIndex],scene+'/'+tier+' original input population');assert.equal(b.stars.length,a.stars.length);
      for(const key of ['projected','diagnostics','catalogueSha256','diffuseSha256'])assert.equal(b[key],a[key]);
      const patchHash=createHash('sha256');let compared=0;
      for(let i=0;i<a.stars.length;i++){
        const first=a.stars[i],second=b.stars[i];
        const metadata=star=>{const {linear,modes,...rest}=star;return {star:plain(rest),seed:modes.seed,offsetMs:modes.offsetMs};};
        assert.deepEqual(metadata(second),metadata(first));exact(second.linear,first.linear,scene+'/'+tier+'/patch/'+i);
        patchHash.update(asBytes(first.linear));compared+=first.linear.length;
      }
      for(const [name,value] of Object.entries(a.raster))if(ArrayBuffer.isView(value))exact(b.raster[name],value,scene+'/'+tier+'/raster/'+name);
      rows.push({scene,tier,stars:a.stars.length,projected:a.projected,comparedPatchFloat64Values:compared,patchSha256:patchHash.digest('hex')});
      patches+=a.stars.length;values+=compared;if(scene==='dark')dark[tier]={original:a,candidate:b,snapshot};
    }
    return {pair,dark,rows,patches,values};
  })();return scenesPromise;
}
test('all original ten source scenes retain admitted inputs, complete patches and unchanged physical rasters',async t=>{
  const result=await originalScenes();assert.equal(result.patches,4626);
  t.diagnostic(JSON.stringify({scope:'original source recipe, not retained native splat inputs',patches:result.patches,
    comparedPatchFloat64Values:result.values,scenes:result.rows,identity:result.pair.identity,
    sourceInputs:Object.fromEntries(result.pair.original.inputs)}));
});
test('original-source patches preserve full replay, nominal, foreground, overlays and motion gating',async t=>{
  const {pair,dark}=await originalScenes();let configurations=0,samples=0;
  for(const tier of ['preview','refined']){
    const {original:a,candidate:b,snapshot}=dark[tier],n=a.raster.width*a.raster.height;
    const cloud=new Uint8ClampedArray(4*n),moon=cloud.slice(),mask=new Float64Array(n);
    for(let p=0;p<n;p++){
      const x=p%a.raster.width,y=Math.floor(p/a.raster.width),inside=x>110&&x<151&&y>130&&y<181;
      mask[p]=inside?0:x===110&&y>130&&y<181?.4:1;
      cloud.set([79+y%70,101+x%90,143,(x%3)*127],4*p);moon.set([37+x%19,48+y%23,61,inside?255:0],4*p);
    }
    const foreground={cloudRGBA:cloud,moonRGBA:moon,mask,glass:[{x:14,y:76,width:86,height:18},{x:18,y:276,width:289,height:24}]};
    for(const scope of ['all','preview-members'])for(const glassFactor of [0,.5,1]){
      const config={scope,glassFactor,margin:4,multiplier:2};
      const first=pair.original.api.prepareReplay(a.raster,a.stars,config,foreground),second=pair.candidate.api.prepareReplay(b.raster,b.stars,config,foreground);
      exact(second.nominal,first.nominal,'nominal');assert.deepEqual(plain(second.indices),plain(first.indices));
      for(const key of ['sourceCount','contributingCenters'])assert.equal(second[key],first[key]);
      for(const [offset,motion] of [[0,{}],[1000/60,{}],[137,{}],[1111,{}],[2033,{}],[0,{paused:true}],
        [0,{hidden:true}],[0,{reduced:true}],[1033,{reduced:true,full:true}],[0,{gain:0}],[513,{gain:.1}]]){
        const time=snapshot.utcMs+offset,one=first.present(time,motion),two=second.present(time,motion);
        exact(two.rgba,one.rgba,'complete presented frame');assert.deepEqual(plain(two.sample),plain(one.sample));
        exact(pair.candidate.api.stellarOverlay(second,two.rgba),pair.original.api.stellarOverlay(first,one.rgba),'complete overlay');
        if(offset===137||motion.paused)exact(one.rgba,pair.original.api.replayFrame(a.raster,a.stars,time,config,foreground,motion).rgba,'unchanged slow full-frame oracle');
        for(let p=0;p<n;p++)if(mask[p]===0)for(let c=0;c<3;c++)assert.equal(two.rgba[4*p+c],second.nominal[4*p+c],'opaque calendar interior');
        samples++;
      }
      configurations++;
    }
  }
  t.diagnostic(JSON.stringify({configurations,completePresentedFrames:samples,foreground:'synthetic nonuniform cloud/calendar/glass on original source scene',nativeQualification:'NOT_RUN'}));
});
test('actual original live-frame admission retains membership, flux and nominal refusals',async t=>{
  const {pair,dark}=await originalScenes(),snapshot=dark.refined.snapshot,job=pair.original.api.nativeJob(snapshot,true);
  const engine=new pair.original.api.NativeSkyEngine(pair.pack);let frame;
  try{frame=await engine.render(job);}finally{engine.dispose();}
  assert.equal(frame.status,'ready');const config={scope:'all',glassFactor:.5,margin:4,multiplier:1},foreground={glass:[]};
  const stars=pair.original.api.prepareStars(frame,pair.catalogue),nominal=pair.original.api.prepareReplay(frame.raster,stars,config,foreground).nominal;
  const msg={frame,job,config,foreground,nominal};
  const a=await pair.original.api.prepareLiveFrame(msg),b=await pair.candidate.api.prepareLiveFrame(msg);
  exact(b.nominal,a.nominal,'live admitted nominal');assert.deepEqual(plain(b.census),plain(a.census));
  assert.deepEqual(plain(b.indices),plain(a.indices));assert.equal(b.sourceCount,a.sourceCount);
  const changedSources=frame.sources.map((s,i)=>i? s:{...s,x:s.x+.25});
  const duplicate=[frame.sources[0],...frame.sources.slice(0,-1)];
  const fluxIndex=frame.raster.sourceDiagnostics.findIndex(d=>d.detectable&&d.backgroundComplete!==false);
  const changedFlux=frame.raster.sourceDiagnostics.map((d,i)=>i===fluxIndex?{...d,vFlux:d.vFlux+1}:d);
  const wrongNominal=nominal.slice();wrongNominal[0]^=1;
  const cases=[{...msg,frame:{...frame,sources:changedSources}},{...msg,frame:{...frame,sources:duplicate}},
    {...msg,frame:{...frame,raster:{...frame.raster,sourceDiagnostics:frame.raster.sourceDiagnostics.slice(1)}}},
    {...msg,frame:{...frame,raster:{...frame.raster,sourceDiagnostics:changedFlux}}},{...msg,nominal:wrongNominal}];
  const errors=[];
  for(const value of cases){
    let first,second;try{await pair.original.api.prepareLiveFrame(value);}catch(e){first={name:e.name,message:e.message};}
    try{await pair.candidate.api.prepareLiveFrame(value);}catch(e){second={name:e.name,message:e.message};}
    assert.ok(first,'unchanged original admission must refuse');assert.deepEqual(second,first);errors.push(first.message);
  }
  assert.deepEqual(errors,['Projected catalogue membership or coordinates mismatch','Projected catalogue membership or coordinates mismatch',
    'Transport diagnostics membership mismatch','Reference flux disagrees with worker','Nominal native bytes mismatch']);
  t.diagnostic(JSON.stringify({admittedSourceCount:a.sourceCount,originalRefusals:errors,scope:'local digest-verified source inputs; no native publication or cadence admission'}));
});
