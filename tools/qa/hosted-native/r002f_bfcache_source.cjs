'use strict';
// Additive custody/retention only. The original witness and classifiers are hash-pinned inputs.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm'),zlib=require('node:zlib');
const {createRequire}=require('node:module'),{isDeepStrictEqual}=require('node:util');
const HERE=__dirname,REPO=path.resolve(HERE,'../../..'),ORIGINAL=path.join(REPO,'tools/qa/r0041');
const PINS=Object.freeze({'real-witness.cjs':'dc692105f2c5bb583e4d14da6b9b748fecd4d699aedf7e2d5833d86f7e000d0c',
  'iso.cjs':'c39d5e764f2231de5b5784a44da0ab9036925383d34a9542a0a30d8727b01202','png.cjs':'101311def95442acb87c32a52762aee6ad0955cfa239007bd6ec0566df5baa7b'});
const LIMITS=Object.freeze({returns:512,pngBytes:2*1024**2,pngPopulationBytes:256*1024**2,videoBytes:64*1024**2,
  metadataBytes:8*1024**2,decodeFrames:20000,frameRgbBytes:326*530*3,dependencyFiles:512,dependencyBytes:1024**3});
const STATUS='OBSERVED_BFCACHE_DIAGNOSTIC',QUALIFICATION='R002F_BFCACHE_MOON_WITNESS_ONLY',CLOCK='2026-11-18T16:30:00Z';
const DISCLOSURE=Object.freeze({timingClass:'instrumented-existing-witness-retention',captureCallsAdded:0,timingComparableToOriginal:false,
  launchContract:'kernel-no-egress/context-experiment-proxy/same-browser-direct-boundaries',browserWideBackgroundProxyVisibilityPreserved:false});
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function need(ok,why){if(!ok)throw Error(why);}
function plain(x){return JSON.parse(JSON.stringify(x));}
function same(a,b){return isDeepStrictEqual(plain(a),plain(b));}
function noSymlinks(value){const literal=path.resolve(value);let current=path.parse(literal).root;
  for(const part of literal.slice(current.length).split(path.sep).filter(Boolean)){current=path.join(current,part);need(!fs.lstatSync(current).isSymbolicLink(),'symlink path refused');}return literal;}
function systemPath(value){const literal=path.resolve(value);let pending=literal.split('/').slice(1),current='/',symlinks=[];
  while(pending.length){const part=pending.shift();if(!part||part==='.')continue;if(part==='..'){current=path.dirname(current);continue;}
    const candidate=path.join(current,part),st=fs.lstatSync(candidate);if(st.isSymbolicLink()){
      const target=fs.readlinkSync(candidate);symlinks.push({path:candidate,target});need(symlinks.length<=40,'system symlink loop');
      if(path.isAbsolute(target))current='/';pending=target.split('/').filter(Boolean).concat(pending);
    }else current=candidate;}
  return {resolvedPath:current,symlinks};}
function record(value,{system=false,limit=1024**3}={}){
  const literal=path.resolve(value),resolved=system?systemPath(literal):{resolvedPath:noSymlinks(literal),symlinks:[]};
  const fd=fs.openSync(resolved.resolvedPath,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
  try{const before=fs.fstatSync(fd,{bigint:true});need(before.isFile()&&before.size>=0n&&before.size<=BigInt(limit),'bounded regular file required');
    need(system||before.nlink===1n,'hardlink alias refused');const h=crypto.createHash('sha256'),chunk=Buffer.alloc(1024**2);let count=0,n;
    while((n=fs.readSync(fd,chunk,0,chunk.length,null))>0){count+=n;need(count<=limit,'file grew beyond bound');h.update(chunk.subarray(0,n));}
    const after=fs.fstatSync(fd,{bigint:true}),now=fs.lstatSync(resolved.resolvedPath,{bigint:true});
    need(['dev','ino','mode','nlink','size','mtimeNs','ctimeNs'].every(k=>before[k]===after[k])&&BigInt(count)===before.size&&now.ino===before.ino&&now.dev===before.dev,'file changed during descriptor read');
    if(system)need(same(systemPath(literal),resolved),'system symlink chain changed');
    return {path:literal,resolvedPath:resolved.resolvedPath,bytes:count,sha256:h.digest('hex'),device:BigInt.asUintN(64,before.dev).toString(),inode:BigInt.asUintN(64,before.ino).toString(),links:Number(before.nlink),mode:Number(before.mode&0o7777n),uid:Number(before.uid),mtimeNs:before.mtimeNs.toString(),ctimeNs:before.ctimeNs.toString(),system,symlinks:resolved.symlinks};
  }finally{fs.closeSync(fd);}}
function requireRecord(row){need(row&&same(record(row.path,{system:row.system===true}),row),'current file identity changed');return row;}
function currentRecords(value){const seen=new Map();function visit(item){if(!item||typeof item!=='object')return;
  if(!Array.isArray(item)&&['path','resolvedPath','sha256','inode','mtimeNs','ctimeNs','system'].every(k=>Object.hasOwn(item,k))){
    if(seen.has(item.path))need(same(seen.get(item.path),item),'conflicting file identities');else{requireRecord(item);seen.set(item.path,item);}}
  else for(const child of Object.values(item))visit(child);}visit(value);return seen.size;}
function readJson(file,limit=LIMITS.metadataBytes){const identity=record(file,{limit}),value=JSON.parse(fs.readFileSync(identity.path));requireRecord(identity);return {identity,value};}
function writeBytes(file,bytes){need(Buffer.isBuffer(bytes),'buffer required');noSymlinks(path.dirname(file));
  const fd=fs.openSync(file,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
  try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}return record(file);}
function writeJson(file,value){return writeBytes(file,Buffer.from(JSON.stringify(value,null,2)+'\n'));}
// A single attempted write: a partial, zero, invalid or throwing result is terminal, never retried.
function writeOnce(fd,bytes){need(Buffer.isBuffer(bytes)&&bytes.length>0,'nonempty write buffer required');
  try{const count=fs.writeSync(fd,bytes);if(!Number.isSafeInteger(count)||count<0||count>bytes.length)
      return {acknowledgedBytes:0,error:'invalid fs.writeSync byte count'};
    return {acknowledgedBytes:count,error:count===bytes.length?null:'short fs.writeSync byte count: '+count+'/'+bytes.length};
  }catch(error){return {acknowledgedBytes:0,error:'fs.writeSync failed: '+String(error.stack||error)};}}
function finishFile(fd,file){const result={closed:false};
  try{fs.fsyncSync(fd);}catch(error){result.error='retained file fsync failed: '+String(error);}
  try{fs.closeSync(fd);result.closed=true;}catch(error){result.error=result.error||'retained file close failed: '+String(error);}
  try{result.identity=record(file);}catch(error){result.error=result.error||'retained file identity failed: '+String(error);}
  return result;}
function admitRetained(identity,observed,acknowledged,retained,limit){need([observed,acknowledged,retained,limit].every(Number.isSafeInteger)&&
    observed>=0&&observed===acknowledged&&acknowledged===retained&&retained<=limit&&identity?.bytes===retained,
    'observed, acknowledged and actual retained byte counts differ');requireRecord(identity);return true;}
function freshDirectory(file){noSymlinks(path.dirname(file));need(!fs.existsSync(file),'output already exists');fs.mkdirSync(file,{mode:0o700});noSymlinks(file);return path.resolve(file);}
function crc(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=c&1?(c>>>1)^0xedb88320:c>>>1;}return(c^0xffffffff)>>>0;}
function pngInfo(bytes){need(Buffer.isBuffer(bytes)&&bytes.length<=LIMITS.pngBytes&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])),'bounded PNG required');
  let offset=8,header=null,ended=false,idat=[],sawData=false,dataEnded=false;
  while(offset<bytes.length){need(offset+12<=bytes.length&&!ended,'truncated or trailing PNG');const n=bytes.readUInt32BE(offset),end=offset+12+n;need(end<=bytes.length,'truncated PNG chunk');
    const type=bytes.toString('ascii',offset+4,offset+8),data=bytes.subarray(offset+8,end-4);need(/^[A-Za-z]{4}$/.test(type)&&crc(bytes.subarray(offset+4,end-4))===bytes.readUInt32BE(end-4),'PNG CRC/type differs');
    if(!header){need(type==='IHDR'&&n===13,'first PNG chunk must be IHDR');header={width:data.readUInt32BE(),height:data.readUInt32BE(4),depth:data[8],colour:data[9]};
      need(header.width===325&&header.height===530&&header.depth===8&&[2,6].includes(header.colour)&&data[10]===0&&data[11]===0&&data[12]===0,'original screenshot dimensions/format differ');
    }else if(type==='IDAT'){need(!dataEnded,'noncontiguous PNG image data');idat.push(data);sawData=true;}
    else {if(sawData)dataEnded=true;need(type!=='IHDR','duplicate PNG header');if(type==='IEND'){need(n===0&&sawData,'PNG end before data');ended=true;}
      else need(type[0]===type[0].toLowerCase()||type==='PLTE','unknown critical PNG chunk');}
    offset=end;}
  need(ended&&offset===bytes.length,'missing PNG end');const channels=header.colour===6?4:3,expected=header.height*(1+header.width*channels),compressed=Buffer.concat(idat);
  const result=zlib.inflateSync(compressed,{maxOutputLength:expected,info:true});need(result.buffer.length===expected&&result.engine.bytesWritten===compressed.length,'PNG decoded/trailing bytes differ');
  for(let y=0;y<header.height;y++)need(result.buffer[y*(1+header.width*channels)]<=4,'invalid PNG filter');
  return {...header,channels,bytes:bytes.length,sha256:sha(bytes)};}
function returnSink(folder,limits=LIMITS){freshDirectory(folder);const state={protocol:'r002f-bfcache-returns/1',...DISCLOSURE,attempted:0,received:0,pngBytes:0,metadataBytes:0,frames:[],values:{},errors:[],overflow:false,stopped:false};let pending=false;
  function fail(error){state.errors.push(String(error.stack||error).slice(0,1000));return error;}
  async function capture(original,options,tag){need(!state.stopped&&!pending,'retention closed or concurrent screenshot');need(/^ref-(present|absent)$|^restore-[123]$/.test(tag),'unknown original screenshot tag');
    pending=true;state.attempted++;const calledNs=process.hrtime.bigint().toString();let bytes;
    try{bytes=await original(options);state.received++;const returnedNs=process.hrtime.bigint().toString();
      if(state.received>limits.returns||!Buffer.isBuffer(bytes)||bytes.length>limits.pngBytes||state.pngBytes+bytes.length>limits.pngPopulationBytes){state.overflow=true;throw Error('screenshot retention bound overflow');}
      const info=pngInfo(bytes),file=String(state.received).padStart(4,'0')+'.png',identity=writeBytes(path.join(folder,file),bytes);state.pngBytes+=bytes.length;
      state.frames.push({index:state.received,tag,file,calledNs,returnedNs,info,identity});return bytes;
    }catch(error){throw fail(error);}finally{pending=false;}}
  function value(name,value){need(!state.stopped&&!pending&&!Object.hasOwn(state.values,name)&&/^[a-z]+$/.test(name),'raw value repeated or after close');
    const bytes=Buffer.from(JSON.stringify(value)+'\n');if(state.metadataBytes+bytes.length>limits.metadataBytes){state.overflow=true;throw fail(Error('raw value metadata bound overflow'));}
    const identity=writeBytes(path.join(folder,'value-'+name+'.json'),bytes);state.metadataBytes+=bytes.length;state.values[name]=identity;return value;}
  function finish(){need(!pending&&!state.stopped,'retention already closed or screenshot pending');state.stopped=true;return state;}
  return {state,capture,value,finish};}
function recorderScope(out,label,literal){need(['baseline','candidate'].includes(label),'original arm label required');noSymlinks(out);
  const expected=path.join(path.resolve(out),'.video-'+label);need(literal===expected,'foreign recorder cleanup scope');need(!fs.existsSync(expected),'preexisting recorder directory refused');return expected;}
function recorderPrefix(folder,file,target,{limit=LIMITS.videoBytes}={}){
  noSymlinks(folder);need(path.dirname(file)===folder&&path.dirname(target)===path.dirname(folder)&&Number.isInteger(limit)&&limit>0&&limit<=LIMITS.videoBytes,
    'bounded owned recorder prefix scope required');noSymlinks(file);need(fs.lstatSync(folder).uid===process.getuid(),'recorder directory owner differs');
  const input=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);let output;
  const fields=st=>({device:BigInt.asUintN(64,st.dev).toString(),inode:BigInt.asUintN(64,st.ino).toString(),bytes:st.size.toString(),links:Number(st.nlink),
    uid:Number(st.uid),mtimeNs:st.mtimeNs.toString(),ctimeNs:st.ctimeNs.toString()});
  try{const before=fs.fstatSync(input,{bigint:true});need(before.isFile()&&before.nlink===1n&&before.uid===BigInt(process.getuid())&&before.size<=BigInt(Number.MAX_SAFE_INTEGER),
      'actual unaliased owned recorder file required');
    output=fs.openSync(target,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);
    const chunk=Buffer.alloc(Math.min(limit,1024**2));let observedBytes=0,acknowledgedBytes=0,count,error;
    while(observedBytes<limit&&(count=fs.readSync(input,chunk,0,Math.min(chunk.length,limit-observedBytes),null))>0){observedBytes+=count;
      const written=writeOnce(output,chunk.subarray(0,count));acknowledgedBytes+=written.acknowledgedBytes;if(written.error){error=written.error;break;}}
    const final=finishFile(output,target);output=undefined;error=error||final.error;
    const retainedBytes=final.identity?.bytes??null;if(observedBytes!==acknowledgedBytes||acknowledgedBytes!==retainedBytes)error=error||'recorder prefix byte counts differ';
    const after=fs.fstatSync(input,{bigint:true}),now=fs.lstatSync(file,{bigint:true});
    return {protocol:'r002f-bfcache-recorder-prefix/1',complete:false,scope:'ACTUAL_FAILED_RECORDER_PREFIX_NOT_COMPLETE_NATIVE_POPULATION',
      source:file,originalBytes:Number(before.size),before:fields(before),after:fields(after),
      sourceStable:same(fields(before),fields(after))&&now.dev===before.dev&&now.ino===before.ino,
      observedBytes,acknowledgedBytes,retainedBytes,retentionComplete:!error&&final.closed,error:error||null,
      truncated:retainedBytes===null?null:BigInt(retainedBytes)<before.size,retained:final.identity||null};
  }finally{fs.closeSync(input);if(output!==undefined)fs.closeSync(output);}}
function originalSources(root=ORIGINAL){const rows={};for(const [name,hash] of Object.entries(PINS)){const r=record(path.join(root,name));need(r.sha256===hash,'original source pin differs: '+name);rows[name]=r;}return rows;}
function originalText(root=ORIGINAL){const rows=originalSources(root),text=fs.readFileSync(rows['real-witness.cjs'].path,'utf8');requireRecord(rows['real-witness.cjs']);return {text,rows};}
function unique(text,anchor){need(text.indexOf(anchor)>=0&&text.indexOf(anchor)===text.lastIndexOf(anchor),'original extraction anchor differs');return text.indexOf(anchor);}
function originalFunctions({root=ORIGINAL,spawn,fs:filesystem}={}){const {text,rows}=originalText(root),end=unique(text,'(async()=>{'),localRequire=createRequire(rows['real-witness.cjs'].path);
  const controlledRequire=name=>name==='node:child_process'&&spawn?{spawn}:name==='node:fs'&&filesystem?filesystem:localRequire(name);
  const context={require:controlledRequire,process:{argv:['node',rows['real-witness.cjs'].path,'/source-control-root','/source-control-output','chromium','bfcache',CLOCK,'3','--label=baseline']},Buffer,Uint8Array,console};
  const code=text.slice(0,end)+'\n;({sample,classify,dist,mean,decodeVideo,decodePng,PAL,W,H,VW,VH,TH_FAR,EVENTS});';
  const functions=vm.runInNewContext(code,context,{filename:rows['real-witness.cjs'].path,timeout:1000});return {...functions,source:rows};}
module.exports={HERE,REPO,ORIGINAL,PINS,LIMITS,STATUS,QUALIFICATION,CLOCK,DISCLOSURE,sha,need,plain,same,noSymlinks,systemPath,record,requireRecord,currentRecords,readJson,writeBytes,writeJson,writeOnce,finishFile,admitRetained,freshDirectory,pngInfo,returnSink,recorderScope,recorderPrefix,originalSources,originalText,unique,originalFunctions};
