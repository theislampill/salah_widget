'use strict';
// Actual repository source and assets. The public API route is the control for the production compact factory.
// No builder execution, worker, browser, timing budget or numerical sweep.
// Regressions caught: duplicate digest, forged admission, dropped pin/domain checks and error reordering.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=process.env.SALAH_TEST_ROOT?path.resolve(process.env.SALAH_TEST_ROOT):path.resolve(__dirname,'../..');
const cp=require('node:child_process');
const python=process.env.SALAH_TEST_PYTHON||(process.platform==='win32'?'python':'python3');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=(r,n)=>fs.readFileSync(path.join(r,n),'utf8');
const bytes=new Uint8Array(fs.readFileSync(path.join(root,'moon/assets/initial-compact.bin')));
const encoding=JSON.parse(read(root,'moon/initial-compact-manifest.json'));
const authored=JSON.parse(cp.execFileSync(python,['-I','-S','-B',path.join(__dirname,'helpers/initial_bootstrap.py'),root],{maxBuffer:2*1024*1024}));
const {pin,profile}=authored;
const publicBoot='\nwindow.SalahMoonInitial=createInitialMoon(decodeCompactReceivers(Uint8Array.from(atob('+JSON.stringify(Buffer.from(bytes).toString('base64'))+'),c=>c.charCodeAt(0)),'+JSON.stringify(encoding)+'),'+JSON.stringify(pin)+');';
const units=['surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-initial-compact.mjs'];
const metrics={schema:'initial-admission-source-controls/1',sourceRoot:root,node:{executable:process.execPath,version:process.version,v8:process.versions.v8},bootstrapSha256:sha(Buffer.from(authored.bootstrap)),digests:[],inherited:[],rawRejections:[],pinRejections:[],forgedBypasses:[],precedence:[],limits:['Work-count and one canonical fixture equality only; no timing, S1, pixels or full numerical qualification','Binary/JSON protocol boundary, not an arbitrary hostile JavaScript getter/prototype proof']};
assert.equal(sha(bytes),'dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269');
assert.equal(sha(fs.readFileSync(path.join(root,'moon/src/asset-digest.mjs'))),'41a02370ec87de6e028d34b7ec2ecf947c8c37bee11d3047bc903b06f15c0620');

function load(r,{bootstrap=null,observe=false}={}){
 const original=Function(read(r,'moon/src/asset-digest.mjs')+'\nreturn assetDigest;')();
 const calls=[],allocations=[];
 const digest=value=>{const computed=original(value);if(observe)calls.push({bytes:value.length,sha256:computed});return computed;};
 const track=Native=>new Proxy(Native,{construct(Target,args){const value=Reflect.construct(Target,args);if(observe)allocations.push(value);return value;}});
 const window={};
 const api=Function('assetDigest','Float32Array','Float64Array','Uint32Array','window',units.map(n=>read(r,'moon/src/'+n)).join('\n')+(bootstrap||'')+'\nreturn {decodeCompactReceivers,createInitialMoon,createCompactInitialMoon:typeof createCompactInitialMoon===\'function\'?createCompactInitialMoon:null,privateConstructorHidden:typeof constructInitialMoon===\'undefined\'};')(digest,track(Float32Array),track(Float64Array),track(Uint32Array),window);
 return {api,window,calls,allocations};
}
const current=load(root).api,old={...current,createCompactInitialMoon:null};
const decoded=old.decodeCompactReceivers(bytes,encoding);
assert.equal(decoded.length,3965156);assert.equal(sha(decoded),'25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331');
function route(api,b,e,p,proof){return api.createCompactInitialMoon?api.createCompactInitialMoon(b,e,p,proof):api.createInitialMoon(api.decodeCompactReceivers(b,e),p);}
function outcome(fn){try{fn();return {accepted:true};}catch(error){return {accepted:false,name:error.name,message:error.message};}}
function rejected(fn,message){const value=outcome(fn);assert.equal(value.accepted,false);if(message)assert.equal(value.message,message);return value;}
function dataOwner(run){
 const count=540*540;
 const last=(kind,length)=>run.allocations.filter(value=>value instanceof kind&&value.length===length).at(-1);
 const result={material:last(Float32Array,count*3),coverage:last(Float32Array,count),records:last(Float64Array,pin.records*9),indices:last(Uint32Array,pin.records)};
 for(const [name,value] of Object.entries(result))assert(value,name+' allocation was reached');
 return result;
}
function byteHash(value){return sha(new Uint8Array(value.buffer,value.byteOffset,value.byteLength));}

test('authored production bootstrap uses two genuine digest calls',()=>{
 const prior=load(root,{bootstrap:publicBoot,observe:true});
 const actual=load(root,{bootstrap:authored.bootstrap,observe:true});
 assert.equal(prior.window.SalahMoonInitialError,undefined);assert.equal(actual.window.SalahMoonInitialError,undefined);
 assert(prior.window.SalahMoonInitial&&actual.window.SalahMoonInitial);
 assert.equal(prior.calls.length,3,'Public API control must genuinely hash encoded, decoded, decoded');
 assert.deepEqual(prior.calls.map(x=>x.bytes),[549170,3965156,3965156]);
 metrics.digests={before:prior.calls,current:actual.calls};
 assert.equal(actual.calls.length,2,'Corrected compact route must hash encoded and decoded only');
 assert.deepEqual(actual.calls,prior.calls.slice(0,2));
});

test('private compact factory exists without a public bypass parameter',()=>{
 assert.equal(typeof current.createCompactInitialMoon,'function');
 assert.equal(current.createCompactInitialMoon.length,3);assert.equal(current.createInitialMoon.length,2);assert.equal(current.decodeCompactReceivers.length,2);
 assert.equal(current.privateConstructorHidden,true);
 for(const fn of [current.createInitialMoon,current.decodeCompactReceivers,current.createCompactInitialMoon])assert.equal(Object.keys(fn).length,0);
});

test('actual constructed owner and derived receiver data remain identical',()=>{
 const prior=load(root,{bootstrap:publicBoot,observe:true});
 const actual=load(root,{bootstrap:authored.bootstrap,observe:true});
 assert.equal(actual.window.SalahMoonInitialError,undefined);
 const a=prior.window.SalahMoonInitial,b=actual.window.SalahMoonInitial;
 assert.deepEqual(b.identity,a.identity);assert(Object.isFrozen(a)&&Object.isFrozen(b));assert(Object.isFrozen(b.identity));
 assert.equal(b.render.toString(),a.render.toString(),'The actual render function body must remain exact');
 const x=dataOwner(prior),y=dataOwner(actual),bindings={};
 for(const key of Object.keys(x)){assert.deepEqual(y[key],x[key]);bindings[key]={type:x[key].constructor.name,length:x[key].length,sha256:byteHash(x[key])};}
 metrics.construction={identity:b.identity,ownerFrozen:true,renderFunctionSha256:sha(Buffer.from(b.render.toString())),derived:bindings};
});

test('one retained canonical fixture has identical render and calendar data',()=>{
 const a=route(old,bytes,encoding,pin),b=route(current,bytes,encoding,pin),alpha=Math.acos(2*.08-1);
 const scene={size:540,outSize:108,diameter:103.68,basis:[0,1,0,0,0,1,1,0,0],sun:[Math.cos(alpha),Math.sin(alpha),0],earth:[384400,0,0],distance:384400,extent:1.08,profile:structuredClone(profile),mode:'calendar-canonical',fraction:.08,waxing:true,tilt:0};
 const first=a.render(scene),second=b.render(scene);
 const withoutTimer=value=>{const diagnostics={...value.diagnostics};delete diagnostics.totalMs;return {...value,diagnostics};};
 assert.deepEqual(withoutTimer(second),withoutTimer(first));
 metrics.render={scene,arrays:Object.fromEntries(['rgba','surfaceLinear','surfaceCoverage','calendarLinear','calendarRgba'].map(key=>[key,{type:first[key].constructor.name,length:first[key].length,sha256:byteHash(first[key])}])),allNonTimingFieldsExact:true,qualification:'One unchanged-data control, not a phase/footprint sweep or visual acceptance'};
});

test('public decoder retains both actual identity checks and fresh raw bytes',()=>{
 const observed=load(root,{observe:true}),first=observed.api.decodeCompactReceivers(bytes,encoding),second=observed.api.decodeCompactReceivers(bytes,encoding);
 assert.deepEqual(first,decoded);assert.deepEqual(second,decoded);assert.notEqual(first.buffer,second.buffer);
 assert.equal(observed.calls.length,4);assert.deepEqual(observed.calls.slice(0,2).map(x=>x.bytes),[549170,3965156]);
 metrics.publicDecoder={digestsPerCall:2,decodedBytes:first.length,sha256:sha(first),freshBuffer:true};
});

test('public raw constructor retains its own genuine digest',()=>{
 const observed=load(root,{observe:true}),initial=observed.api.createInitialMoon(decoded,pin);
 assert.equal(initial.identity.sha256,pin.sha256);assert.deepEqual(observed.calls,[{bytes:decoded.length,sha256:pin.sha256}]);
 metrics.rawConstructor={digestsPerValidCall:1};
});

test('all 37 inherited compact rejection cases preserve exact errors',()=>{
 const cases=require('./helpers/initial_rejections.cjs').makeCases(Buffer.from(bytes),encoding);
 assert.equal(cases.length,37);
 for(const {name,make,message} of cases){
  const [b,e]=make(),prior=rejected(()=>old.decodeCompactReceivers(b,e),message);
  const raw=rejected(()=>current.decodeCompactReceivers(b,e),message),factory=rejected(()=>route(current,b,e,pin),message);
  assert.deepEqual(raw,prior,name+' public error parity');assert.deepEqual(factory,prior,name+' factory decoder-first error parity');
  metrics.inherited.push({name,before:prior,public:raw,compactRoute:factory});
 }
});

test('constructor pin is independent of the compact manifest assertion',()=>{
 for(const [name,change,message] of [
  ['wrong-sha',p=>{p.sha256='0'.repeat(64);},'Initial Moon identity'],
  ['wrong-bytes',p=>{p.bytes--;},'Initial Moon identity'],
  ['wrong-schema',p=>{p.schema='unknown';},'Initial Moon schema'],
  ['wrong-size',p=>{p.size=539;},'Initial Moon schema'],
  ['zero-records',p=>{p.records=0;},'Initial Moon record count'],
  ['fractional-records',p=>{p.records=.5;},'Initial Moon record count'],
  ['too-many-records',p=>{p.records=540*540+1;},'Initial Moon record count'],
  ['too-few-records',p=>{p.records--;},'Initial Moon record count']
 ]){
  const p=structuredClone(pin);change(p);const prior=rejected(()=>route(old,bytes,encoding,p),message),actual=rejected(()=>route(current,bytes,encoding,p),message);
  assert.deepEqual(actual,prior,name);metrics.pinRejections.push({name,before:prior,current:actual});
 }
 const e=structuredClone(encoding),p=structuredClone(pin);e.decodedSha256=p.sha256='0'.repeat(64);
 const actual=rejected(()=>route(current,bytes,e,p),'Compact decoded identity');metrics.pinRejections.push({name:'mutually-forged-expected-digests',current:actual});
});

test('raw constructor retains schema size record and geometry boundaries',()=>{
 const maskBytes=Math.ceil(540*540/8),at=6+maskBytes;
 const cases=[
  ['wrong-type',()=>[Array.from(decoded),pin],'Initial Moon identity'],
  ['wrong-length',()=>[decoded.subarray(0,100),pin],'Initial Moon identity'],
  ['size-cap',()=>[new Uint8Array(4000001),{...pin,bytes:4000001}],'Initial Moon identity'],
  ['wrong-magic',b=>{b[0]^=1;},'Initial Moon schema'],
  ['below-min-size',b=>{new DataView(b.buffer).setUint16(4,127,true);},'Initial Moon schema'],
  ['above-max-size',b=>{new DataView(b.buffer).setUint16(4,541,true);},'Initial Moon schema'],
  ['truncated-record',()=>{const b=decoded.slice(0,-1);return [b,{...pin,bytes:b.length,sha256:sha(b)}];},'Initial Moon truncated record'],
  ['trailing-record-data',()=>{const b=new Uint8Array(decoded.length+1);b.set(decoded);return [b,{...pin,bytes:b.length,sha256:sha(b)}];},'Initial Moon record count'],
  ['nonfinite-position',b=>{new DataView(b.buffer).setFloat32(at,NaN,true);},'Initial Moon receiver geometry'],
  ['position-outside-radius',b=>{new DataView(b.buffer).setFloat32(at,1754,true);},'Initial Moon receiver geometry'],
  ['zero-normal',b=>{b.fill(0,at+4,at+10);},'Initial Moon receiver geometry']
 ];
 for(const [name,change,message] of cases){const b=decoded.slice(),result=change(b),[data,p]=result||[b,{...pin,sha256:sha(b)}];
  const prior=rejected(()=>old.createInitialMoon(data,p),message),actual=rejected(()=>current.createInitialMoon(data,p),message);assert.deepEqual(actual,prior,name);metrics.rawRejections.push({name,before:prior,current:actual});}
});

test('mutated raw buffers and caller-forged bypass arguments never admit',()=>{
 const b=decoded.slice();b[40]^=1;
 for(const proof of [true,pin.sha256,{verified:true,skipDigest:true,sha256:pin.sha256,bytes:decoded.length}]){
  const value=rejected(()=>current.createInitialMoon(b,pin,proof),'Initial Moon identity');metrics.forgedBypasses.push({boundary:'raw',proof,value});
 }
 const packed=bytes.slice();packed[packed.length-1]^=1;
 const proof={verified:true,skipDigest:true,sha256:encoding.sha256,decodedSha256:pin.sha256};
 metrics.forgedBypasses.push({boundary:'public-decoder',value:rejected(()=>current.decodeCompactReceivers(packed,encoding,proof),'Compact receiver identity')});
 metrics.forgedBypasses.push({boundary:'compact-factory',value:rejected(()=>route(current,packed,encoding,pin,proof),'Compact receiver identity')});
 if(current.createCompactInitialMoon){const wrong={...pin,sha256:'0'.repeat(64)};metrics.forgedBypasses.push({boundary:'factory-fourth-argument',value:rejected(()=>current.createCompactInitialMoon(bytes,encoding,wrong,proof),'Initial Moon identity')});}
 const observed=load(root,{observe:true}),raw=observed.api.decodeCompactReceivers(bytes,encoding);raw[40]^=1;
 rejected(()=>observed.api.createInitialMoon(raw,pin),'Initial Moon identity');assert.equal(observed.calls.length,3,'Prior decode cannot confer reusable raw-buffer admission');
 metrics.noReusableProof={decoderReturnedRawMutationRejected:true,genuineDigests:observed.calls};
});

test('dual-invalid compact input is rejected before constructor pin reads',()=>{
 for(const [name,change,message] of [
  ['encoded-and-pin',(b,e)=>{b[b.length-1]^=1;},'Compact receiver identity'],
  ['ancestry-and-pin',(b,e)=>{e.method='unknown';},'Compact receiver ancestry'],
  ['scalar-and-pin',(b,e)=>{e.fields[0].range.reverse();},'Compact scalar range'],
  ['decoded-and-pin',(b,e)=>{e.decodedSha256='0'.repeat(64);},'Compact decoded identity']
 ]){
  const b=bytes.slice(),e=structuredClone(encoding);change(b,e);
  const p={...pin,sha256:'0'.repeat(64),schema:'unknown',bytes:1};
  const prior=rejected(()=>route(old,b,e,p),message),actual=rejected(()=>route(current,b,e,p),message);assert.deepEqual(actual,prior,name);
  const inaccessible=new Proxy({}, {get(){throw new Error('Constructor pin was read before compact rejection');}});
  const unread=rejected(()=>route(current,b,e,inaccessible),message);assert.deepEqual(unread,prior,name+' strict read order');metrics.precedence.push({name,before:prior,current:actual,pinUnread:true});
 }
});
