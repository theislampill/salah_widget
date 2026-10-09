'use strict';
// Bounded equivalence/admission controls only; no timers, benchmark, browser or builder.
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const own=__dirname, run=path.resolve(own,'../../..');
const before=path.join(run,'candidates/pr43-r1r2-03'), after=path.join(run,'candidates/pr43-r1r2-04');
const worker=path.join(run,'workers/install/pr43-decode-cost');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const source=name=>fs.readFileSync(name,'utf8');
const binding=name=>({path:name,sha256:sha(fs.readFileSync(name)),bytes:fs.statSync(name).size});
const suite=require(path.join(worker,'controls.cjs'));
// Bind retained controls to the actual frozen candidates, not copied proposal paths.
suite.locations.production=path.join(before,'moon/src/moon-initial-compact.mjs');
suite.locations.candidate=path.join(after,'moon/src/moon-initial-compact.mjs');
suite.locations.digest=path.join(after,'moon/src/asset-digest.mjs');
assert.equal(source(suite.locations.digest),source(path.join(worker,'inputs/asset-digest.mjs')));
assert.equal(source(path.join(before,'moon/src/asset-digest.mjs')),source(suite.locations.digest));

function bootstrap(root){
 const html=source(path.join(root,'index.html'));
 const matches=[...html.matchAll(/<script id="moon-initial-code">([\s\S]*?)<\/script>/g)];
 assert.equal(matches.length,1,'Exactly one generated head Moon script');
 const code=matches[0][1], transport=/const text=atob\(("[A-Za-z0-9+/=]+")\),packed=new Uint8Array\(text.length\)/.exec(code);
 assert(transport,'Actual generated base64 transport');
 const payload=Buffer.from(JSON.parse(transport[1]),'base64');
 const decodeStart=code.indexOf('decodeCompactReceivers(packed,')+'decodeCompactReceivers(packed,'.length;
 const decodeEnd=code.indexOf(');window.SalahMoonInitial=createInitialMoon(bytes,',decodeStart);
 assert(decodeStart>='decodeCompactReceivers(packed,'.length&&decodeEnd>decodeStart);
 const initialStart=decodeEnd+');window.SalahMoonInitial=createInitialMoon(bytes,'.length;
 const initialEnd=code.indexOf(');}catch(error)',initialStart);assert(initialEnd>initialStart);
 const encoding=JSON.parse(code.slice(decodeStart,decodeEnd)), pin=JSON.parse(code.slice(initialStart,initialEnd));
 const fileEncoding=JSON.parse(source(path.join(root,'moon/initial-compact-manifest.json')));
 assert.deepEqual(encoding,fileEncoding,'Generated boot encoding binds its physical file manifest');
 assert.equal(sha(payload),suite.pins.payload);assert.deepEqual(payload,suite.payload);
 const names=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-initial-compact.mjs'];
 const api=Function(names.map(name=>source(path.join(root,'moon/src',name))).join('\n')+'\nreturn {assetDigest,decodeCompactReceivers,createInitialMoon};')();
 const decoded=api.decodeCompactReceivers(new Uint8Array(payload),encoding);
 assert.equal(decoded.length,3965156);assert.equal(sha(decoded),suite.pins.decoded);
 const initial=api.createInitialMoon(decoded,pin);
 assert.equal(initial.identity.sha256,suite.pins.decoded);
 assert.equal(initial.identity.parent.initialReceiverSha256,encoding.parentReceiverSha256);
 assert.equal(initial.identity.parent.initialManifestSha256,sha(fs.readFileSync(path.join(root,'moon/initial-manifest.json'))));
 return {payload,decoded,encoding,pin,initialIdentity:initial.identity,head:{sha256:sha(Buffer.from(code)),bytes:Buffer.byteLength(code)},
   bindings:names.map(name=>binding(path.join(root,'moon/src',name)))};
}
const a=bootstrap(before), b=bootstrap(after);
assert.deepEqual(a.payload,b.payload);assert.deepEqual(a.decoded,b.decoded);assert.deepEqual(a.encoding,b.encoding);assert.deepEqual(a.pin,b.pin);assert.deepEqual(a.initialIdentity,b.initialIdentity);
const comparison=suite.runControls();
assert.equal(comparison.negativeCount,32);assert.equal(comparison.decoded.sha256,suite.pins.decoded);

// Additional small-header boundaries preserve existing DataView error behavior.
const apiBefore=suite.load('production'),apiAfter=suite.load('candidate');
const headerErrors=[];
for(const size of [0,1,3,5,9]){
 const payload=Uint8Array.from(suite.payload.subarray(0,size));const encoding=structuredClone(suite.encoding);
 encoding.bytes=payload.length;encoding.sha256=sha(payload);
 const outcome=api=>{try{api.decodeCompactReceivers(payload,encoding);return {accepted:true};}catch(error){return {accepted:false,name:error.name,message:error.message};}};
 const first=outcome(apiBefore),second=outcome(apiAfter);assert.equal(first.accepted,false);assert.deepEqual(second,first);
 headerErrors.push({bytes:size,before:first,after:second});
}

const digestCalls={before:0,after:0};
function counted(root,key){
 const original=Function(source(path.join(root,'moon/src/asset-digest.mjs'))+'\nreturn assetDigest;')();
 const decode=Function('assetDigest',source(path.join(root,'moon/src/moon-initial-compact.mjs'))+'\nreturn decodeCompactReceivers;')(bytes=>{digestCalls[key]++;return original(bytes);});
 const value=decode(new Uint8Array(a.payload),a.encoding);assert.equal(sha(value),suite.pins.decoded);
}
counted(before,'before');counted(after,'after');assert.deepEqual(digestCalls,{before:2,after:2});

const report={schema:'pr43-decoder-independent-byte-error-controls/v1',scope:'Actual candidate03/candidate04 source and generated head bootstrap; no render, build, terrain, timing or browser claims',
 node:{executable:process.execPath,version:process.version,v8:process.versions.v8,execArgv:process.execArgv},
 controlsSource:binding(path.join(worker,'controls.cjs')), candidateBindings:{before:a.bindings,after:b.bindings},
 generatedHead:{before:a.head,after:b.head},encoded:{bytes:a.payload.length,sha256:sha(a.payload),byteIdentical:true},
 decoded:{bytes:a.decoded.length,sha256:sha(a.decoded),byteIdentical:true,coverageHeaderAndMaskIdentical:Buffer.from(a.decoded.subarray(0,36456)).equals(Buffer.from(b.decoded.subarray(0,36456)))},
 encodingEqual:true,decodedPinEqual:true,initialConsumerIdentityEqual:true,initialConsumerIdentity:a.initialIdentity,
 unchangedDigestCalls:digestCalls,retainedControlResult:comparison,extraShortHeaderErrors:headerErrors,
 negativeControls:32+headerErrors.length,allTestedErrorsExact:true,
 limits:['Concrete legal binary/JSON boundary controls, not arbitrary malicious JavaScript getters/prototype proof','Existing quantization approximations persist; byte equivalence does not improve precision','No startup, UI, native browser, resource or S1 qualification']};
fs.writeFileSync(path.join(own,'BYTE_ERROR_CONTROLS.json'),JSON.stringify(report,null,2)+'\n');
process.stdout.write(JSON.stringify({encoded:report.encoded,decoded:report.decoded,negativeControls:report.negativeControls,digestCalls,consumerIdentityEqual:true,noTimingCollected:true})+'\n');
