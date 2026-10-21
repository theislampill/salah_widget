const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function actualMethods(dir){
 const s=fs.readFileSync(path.join(__dirname,dir,'lib/coreBundle.js'),'utf8');
 const start=s.indexOf('      writeFrame(frame, timestamp) {'),end=s.indexOf('      _writeFrame(frame, timestamp) {',start);
 const close=s.indexOf('      _closeSalahSource() {');
 const stop=s.indexOf('      async _stop() {',start),stopEnd=s.indexOf('\n    };',stop);
 assert(start>0&&end>start&&stop>end&&stopEnd>stop);
 return (close>=0?s.slice(close,start):'')+s.slice(start,end)+s.slice(stop,stopEnd);
}
function fixture(dir,{reopenFails=false,writeFails=false,launchError=null}={}){
 const log={opens:0,closes:0,records:[],images:[]},handles=new Set();
 const io={mkdirSync(){},openSync(p,mode){log.opens++;if(reopenFails&&log.opens>1)throw Error('UNKNOWN open');handles.add(7);return 7;},
  appendFileSync(target,line){if(typeof target==='string'){log.opens++;if(reopenFails&&log.opens>1)throw Error('UNKNOWN open');}else assert(handles.has(target));if(writeFails)throw Error('write fault');log.records.push(line);},
  writeFileSync(p,bytes){log.images.push({p,bytes:Buffer.from(bytes)});},closeSync(fd){assert(handles.delete(fd));log.closes++;}};
 const C=vm.runInNewContext('(class Recorder {'+actualMethods(dir)+'})',{process:{env:{SALAH_CAPTURE_NATIVE_FRAMES:'1'}},require:n=>n==='node:fs'?io:require(n),Date:{now:()=>42},Buffer,monotonicTime:()=>2000,debugLogger:{log(){}},createWhiteImage:()=>Buffer.from('white')});
 const o=new C();Object.assign(o,{_outputFile:'owned.webm',_launchPromise:Promise.resolve(launchError),_writeFrame(){},_lastFrame:{timestamp:1},_lastWriteNodeTime:1000,_lastWritePromise:Promise.resolve(),_gracefullyClose:async()=>{}});
 return {o,log,handles};
}
test('retained reopen failure is reproduced; one owned descriptor removes that operation',async()=>{
 const old=fixture('capture-driver',{reopenFails:true});old.o.writeFrame(Buffer.from('first'),1);assert.throws(()=>old.o.writeFrame(Buffer.from('next'),1.1),/UNKNOWN open/);
 const fixed=fixture('capture-driver-r130',{reopenFails:true});fixed.o.writeFrame(Buffer.from('first'),1);fixed.o.writeFrame(Buffer.from('next'),1.1);
 assert.equal(fixed.log.opens,1);assert.deepEqual(fixed.log.records.map(JSON.parse),[{seq:1,sourceTimeSeconds:1,receiptUtcMs:42,file:'000001.jpeg',bytes:5},{seq:2,sourceTimeSeconds:1.1,receiptUtcMs:42,file:'000002.jpeg',bytes:4}]);
 assert.deepEqual(fixed.log.images.map(x=>x.bytes.toString()),['first','next']);await fixed.o._stop();assert.equal(fixed.handles.size,0);assert.equal(fixed.log.closes,1);
 fixed.o.writeFrame(Buffer.from('after-stop'),2);assert.equal(fixed.log.records.length,2);await fixed.o._stop();assert.equal(fixed.log.closes,1);
});
test('write errors propagate and release the descriptor without a retry or invented record',()=>{
 const f=fixture('capture-driver-r130',{writeFails:true});assert.throws(()=>f.o.writeFrame(Buffer.from('x'),1),/write fault/);assert.equal(f.handles.size,0);assert.equal(f.log.closes,1);assert.equal(f.log.records.length,0);assert.equal(f.log.images.length,0);
});
test('launch failure still releases a previously opened sidecar',async()=>{
 const f=fixture('capture-driver-r130',{launchError:Error('launch fault')});f.o.writeFrame(Buffer.from('x'),1);await assert.rejects(f.o._stop(),/launch fault/);assert.equal(f.handles.size,0);assert.equal(f.log.closes,1);
});
