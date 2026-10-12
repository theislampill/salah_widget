'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module');
const author=path.resolve(__dirname,'../../r0010_delivered_native_closure_r2');
const filename=path.join(author,'connected_controls.cjs'),genuineRequire=createRequire(filename);
const originalOutput=path.join(author,'CONNECTED_SOURCE_CONTROLS.json'),ownOutput=path.join(__dirname,'CONNECTED_REPLAY.json');
let writes=0;
const safeFS=Object.create(fs);
safeFS.writeFileSync=(target,...args)=>{
  if(path.resolve(target)!==originalOutput)throw Error('Unadmitted control write: '+target);
  writes++;return fs.writeFileSync(ownOutput,...args);
};
const safeRequire=name=>name==='node:fs'?safeFS:genuineRequire(name);
const source=fs.readFileSync(filename,'utf8');
const run=vm.runInThisContext('(function(require,__dirname,__filename,process,console,Buffer){\n'+source+'\n})',{filename});
run(safeRequire,author,filename,process,console,Buffer);
process.on('beforeExit',()=>{if(!process.exitCode&&writes!==1)throw Error('Expected exactly one redirected source-control output');});
