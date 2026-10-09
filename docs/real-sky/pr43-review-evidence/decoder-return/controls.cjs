'use strict';
// Byte/error controls only. No Python builder, terrain, browser or render.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const base=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const pins={production:'65baddcf5ef56e724b13ab14b840534610f62eda72129ca32e29122f2a0f8cc7',digest:'41a02370ec87de6e028d34b7ec2ecf947c8c37bee11d3047bc903b06f15c0620',payload:'dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269',manifest:'7062ce6c44b6abad4e690dd5d0218ed1a789015a78f194269cdf4fa93092b256',decoded:'25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331'};
const locations={production:path.join(base,'inputs/production.mjs'),candidate:path.join(base,'proposed/moon/src/moon-initial-compact.mjs'),digest:path.join(base,'inputs/asset-digest.mjs'),payload:path.join(base,'inputs/compact-receivers.bin'),manifest:path.join(base,'inputs/compact-encoding.json')};
for(const key of ['production','digest','payload','manifest'])assert.equal(sha(fs.readFileSync(locations[key])),pins[key],key+' pin');
const digestSource=fs.readFileSync(locations.digest,'utf8'),payload=fs.readFileSync(locations.payload),encoding=JSON.parse(fs.readFileSync(locations.manifest));
function load(kind){return Function(digestSource+'\n'+fs.readFileSync(locations[kind],'utf8')+'\nreturn {decodeCompactReceivers,assetDigest};')();}
function repin(b,e){e.bytes=b.length;e.sha256=sha(b);return [new Uint8Array(b),e];}
function channels(b){let at=36460;const rows=[];for(let field=0;field<8;field++){const start=at,width=b[at++],length=b.readUInt32LE(at);at+=4;const codebook=at;at+=1<<width;const body=at;at+=length;rows.push({start,width,length,codebook,body,end:at});}assert.equal(at,b.length);return rows;}
const channel=channels(payload)[0];
function replaceFirstChannel(body,lengths){const header=Buffer.alloc(5);header[0]=channel.width;header.writeUInt32LE(body.length,1);return Buffer.concat([payload.subarray(0,channel.start),header,lengths,body,payload.subarray(channel.end)]);}
function failed(api,b,e){try{api.decodeCompactReceivers(b,e);return {accepted:true};}catch(error){return {accepted:false,name:error.name,message:error.message};}}
function runControls(){
 const production=load('production'),candidate=load('candidate');
 const before=production.decodeCompactReceivers(new Uint8Array(payload),encoding),after=candidate.decodeCompactReceivers(new Uint8Array(payload),encoding);
 assert.equal(before.length,3965156);assert.equal(sha(before),pins.decoded);assert.equal(sha(after),pins.decoded);assert.deepEqual(after,before);
 const cases=[];
 function mutate(name,change,message){cases.push({name,make(){let b=Buffer.from(payload),e=structuredClone(encoding);const result=change(b,e);return result||[new Uint8Array(b),e];},message});}
 mutate('wrong-input-type',(b,e)=>[Array.from(b),e],'Compact receiver identity');
 mutate('wrong-byte-count',(b,e)=>{e.bytes--;},'Compact receiver identity');
 mutate('size-limit',(b,e)=>{b=Buffer.alloc(600001);e.bytes=b.length;return [new Uint8Array(b),e];},'Compact receiver identity');
 mutate('tampered-payload',(b,e)=>{b[b.length-1]^=1;},'Compact receiver identity');
 mutate('wrong-parent',(b,e)=>{e.parentReceiverSha256='0'.repeat(64);},'Compact receiver ancestry');
 mutate('wrong-schema',(b,e)=>{e.schema='moon-initial-compact/unknown';},'Compact receiver ancestry');
 mutate('wrong-method',(b,e)=>{e.method='unknown';},'Compact receiver ancestry');
 mutate('identity-before-ancestry',(b,e)=>{b[0]^=1;e.schema='unknown';},'Compact receiver identity');
 mutate('wrong-shape',(b,e)=>{e.size=539;},'Compact receiver shape');
 mutate('wrong-records',(b,e)=>{e.records--;},'Compact receiver shape');
 mutate('wrong-magic',(b,e)=>{b[0]^=1;return repin(b,e);},'Compact receiver shape');
 mutate('coverage-too-small',(b,e)=>{for(let i=0;i<540*540;i++)if(b[10+(i>>3)]&(1<<(i&7))){b[10+(i>>3)]^=1<<(i&7);break;}return repin(b,e);},'Compact coverage count');
 mutate('coverage-too-large',(b,e)=>{for(let i=0;i<540*540;i++)if(!(b[10+(i>>3)]&(1<<(i&7)))){b[10+(i>>3)]^=1<<(i&7);break;}return repin(b,e);},'Compact coverage count');
 mutate('channel-header-truncated',(b,e)=>repin(b.subarray(0,36460),e),'Compact channel header');
 mutate('channel-width',(b,e)=>{b[36460]=7;return repin(b,e);},'Compact channel bounds');
 mutate('channel-zero-length',(b,e)=>{b.writeUInt32LE(0,36461);return repin(b,e);},'Compact channel bounds');
 mutate('channel-length-limit',(b,e)=>{b.writeUInt32LE(392871,36461);return repin(b,e);},'Compact channel bounds');
 mutate('channel-body-truncated',(b,e)=>repin(b.subarray(0,b.length-1),e),'Compact channel bounds');
 mutate('invalid-codebook-depth',(b,e)=>{b[36465]=21;return repin(b,e);},'Compact Huffman length');
 mutate('empty-codebook',(b,e)=>{b.fill(0,36465,36465+256);return repin(b,e);},'Compact empty codebook');
 mutate('oversubscribed-codebook',(b,e)=>{b.fill(1,36465,36465+256);return repin(b,e);},'Compact oversubscribed Huffman');
 mutate('huffman-truncated',(b,e)=>repin(replaceFirstChannel(Buffer.alloc(1),b.subarray(channel.codebook,channel.body)),e),'Compact truncated Huffman');
 const oneSymbol=Buffer.alloc(256);oneSymbol[0]=1;
 mutate('huffman-invalid-word',(b,e)=>{b.fill(0xff,channel.body,channel.body+3);b.set(oneSymbol,channel.codebook);return repin(b,e);},'Compact invalid Huffman word');
 mutate('huffman-extra-bytes',(b,e)=>repin(replaceFirstChannel(Buffer.alloc(Math.ceil(196435/8)+1),oneSymbol),e),'Compact extra Huffman bytes');
 mutate('huffman-nonzero-padding',(b,e)=>{const body=Buffer.alloc(Math.ceil(196435/8));body[body.length-1]=1;return repin(replaceFirstChannel(body,oneSymbol),e);},'Compact nonzero Huffman padding');
 mutate('trailing-data',(b,e)=>repin(Buffer.concat([b,Buffer.from([0])]),e),'Compact trailing data');
 mutate('scalar-schema-not-array',(b,e)=>{e.fields={};},'Compact scalar schema');
 mutate('scalar-schema-bits',(b,e)=>{e.fields[1].bits=6;},'Compact scalar schema');
 mutate('scalar-range-descending',(b,e)=>{e.fields[0].range.reverse();},'Compact scalar range');
 mutate('scalar-range-not-finite',(b,e)=>{e.fields[3].range[1]=Infinity;},'Compact scalar range');
 mutate('changed-scalar-range',(b,e)=>{e.fields[0].range[0]+=1;},'Compact decoded identity');
 mutate('wrong-decoded-identity',(b,e)=>{e.decodedSha256='0'.repeat(64);},'Compact decoded identity');
 const rows=cases.map(({name,make,message})=>{const [b,e]=make(),old=failed(production,b,e),proposed=failed(candidate,b,e);assert.equal(old.accepted,false,name+' original must reject');assert.equal(old.message,message,name+' expected original branch');assert.deepEqual(proposed,old,name+' exact error parity');return {name,production:old,candidate:proposed};});
 return {scope:'same pinned compact payload and exact production digest; byte/error controls only',decoded:{bytes:after.length,sha256:sha(after),byteIdentical:true},negativeCount:rows.length,negativeControls:rows,pins,sourceHashes:{production:sha(fs.readFileSync(locations.production)),candidate:sha(fs.readFileSync(locations.candidate)),digest:sha(fs.readFileSync(locations.digest))}};
}
module.exports={base,sha,pins,locations,payload,encoding,load,runControls};
if(require.main===module){const report=runControls();fs.writeFileSync(path.join(base,'CONTROLS.json'),JSON.stringify(report,null,2)+'\n');process.stdout.write(JSON.stringify({positiveByteIdentity:report.decoded,negativeControls:report.negativeCount,allErrorsExact:true})+'\n');}
