'use strict';
// Install at moon/tests/compact-codec.test.cjs. No writes, terrain, browser or
// render loop. Python is already the deterministic Moon build dependency.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=process.env.SALAH_TEST_ROOT?path.resolve(process.env.SALAH_TEST_ROOT):path.resolve(__dirname,'../..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const PARENT='0c5e4be7808367211ab3a8fec8a8dcba76f6f9a69ebf5591dc76ed3e188b2444',PARENT_PIN='f1184150163bb992279fe7a4f031917cd71d8558b2951b1997bf8dd67a3705f5',PACKED='dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269',DECODED='25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331';
const original=fs.readFileSync(path.join(root,'moon/assets/initial-receivers.bin')),pinBytes=fs.readFileSync(path.join(root,'moon/initial-manifest.json')),parentPin=JSON.parse(pinBytes);
assert.equal(sha(original),PARENT);assert.equal(sha(pinBytes),PARENT_PIN);
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-initial-compact.mjs'];
const sources=units.map(n=>fs.readFileSync(path.join(root,'moon/src',n),'utf8'));
const api=Function(sources.join('\n')+'\nreturn {assetDigest,decodeCompactReceivers,createInitialMoon};')();
const python=process.env.SALAH_TEST_PYTHON||(process.platform==='win32'?'python':'python3');
const buildScript="import importlib.util,json,pathlib,struct,sys\nroot=pathlib.Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('tested_compact_receivers',root/'tools/compact_receivers.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\nencoded,pin=module.compact_receivers((root/'moon/assets/initial-receivers.bin').read_bytes());text=json.dumps(pin,separators=(',',':')).encode();sys.stdout.buffer.write(struct.pack('<I',len(text))+text+encoded)";
function build(){const b=cp.execFileSync(python,['-I','-S','-B','-c',buildScript,root],{maxBuffer:2*1024*1024});const n=b.readUInt32LE(0);assert.ok(n>0&&n<16000);return {manifest:JSON.parse(b.subarray(4,4+n)),payload:Buffer.from(b.subarray(4+n))};}
const first=build(),second=build(),encoding=first.manifest,payload=first.payload;
test('selected compact builder is deterministic and retains exact parent/new identities',()=>{
 assert.deepEqual(first,second);assert.equal(payload.length,549170);assert.equal(sha(payload),PACKED);assert.equal(api.assetDigest(new Uint8Array(payload)),PACKED);
 assert.equal(encoding.schema,'moon-initial-compact/1');assert.equal(encoding.method,'paeth-huffman');assert.equal(encoding.parentReceiverSha256,PARENT);assert.equal(encoding.sha256,PACKED);assert.equal(encoding.decodedSha256,DECODED);assert.equal(encoding.size,540);assert.equal(encoding.records,196435);
 assert.deepEqual(encoding.fields.map(x=>x.bits),[8,5,5,5,5,5,8,8]);assert.ok(encoding.fields.slice(6).every(x=>x.exact===false));
});
test('decoded compact candidate retains exact coverage and admits only its new initial identity',()=>{
 const decoded=api.decodeCompactReceivers(new Uint8Array(payload),encoding);assert.equal(decoded.length,3965156);assert.equal(sha(decoded),DECODED);assert.notEqual(sha(decoded),PARENT);
 assert.deepEqual(Buffer.from(decoded.subarray(0,6+36450)),original.subarray(0,6+36450));
 assert.throws(()=>api.createInitialMoon(decoded,parentPin),/identity/);
 const seed=api.createInitialMoon(decoded,{...parentPin,sha256:DECODED,parentReceiverSha256:PARENT});assert.equal(seed.identity.sha256,DECODED);assert.equal(seed.identity.parentReceiverSha256,PARENT);
 // Admission is not a render. The separate retained forty numerical cases
 // and continuous-phase visual/quantization limits remain their own evidence.
});
const negatives=[
 ['wrong-parent',(b,e)=>{e.parentReceiverSha256='0'.repeat(64);},/ancestry/],
 ['wrong-schema',(b,e)=>{e.schema='moon-initial-compact/unknown';},/ancestry/],
 ['wrong-shape',(b,e)=>{e.size=539;},/shape/],
 ['tampered-payload',(b,e)=>{b[b.length-1]^=1;},/identity/],
 ['invalid-codebook-depth',(b,e)=>{b[36465]=21;e.sha256=sha(b);},/Huffman length/],
 ['oversubscribed-codebook',(b,e)=>{b.fill(1,36465,36465+256);e.sha256=sha(b);},/oversubscribed Huffman/],
 ['trailing-data',(b,e)=>{e.bytes=b.length;e.sha256=sha(b);},/trailing data/],
 ['changed-scalar-range',(b,e)=>{e.fields[0].range[0]+=1;},/decoded identity/]
];
for(const [name,mutate,error] of negatives)test('compact decoder rejects '+name,()=>{
 const b=name==='trailing-data'?Buffer.concat([payload,Buffer.from([0])]):Buffer.from(payload),e=structuredClone(encoding);mutate(b,e);
 assert.throws(()=>api.decodeCompactReceivers(new Uint8Array(b),e),error);
});
test('selected compact builder refuses mutated parent rather than silently repinning',()=>{
 const script="import importlib.util,pathlib,sys\nroot=pathlib.Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('tested_compact_receivers',root/'tools/compact_receivers.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);data=bytearray((root/'moon/assets/initial-receivers.bin').read_bytes());data[0]^=1\ntry:module.compact_receivers(bytes(data))\nexcept ValueError:sys.exit(0)\nraise RuntimeError('mutated parent admitted')";
 cp.execFileSync(python,['-I','-S','-B','-c',script,root]);
});
