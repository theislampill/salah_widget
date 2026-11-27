'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');
// The entry is never imported as a browser package. A bounded package-identity
// double lets these source controls run with the repository's PNG-only setup.
const intakeFile=path.join(__dirname,'r003f_matrix_intake.cjs'),realRequire=createRequire(intakeFile);
const syntheticEntry=__filename,syntheticVersion='0.0.0-synthetic';
const intakeRequire=name=>name==='playwright/package.json'?{version:syntheticVersion}:realRequire(name);
intakeRequire.resolve=name=>name==='playwright'?syntheticEntry:realRequire.resolve(name);
let I=null;if(fs.existsSync(intakeFile)){const module={exports:{}};Function('require','module','__dirname',fs.readFileSync(intakeFile,'utf8'))(intakeRequire,module,__dirname);I=module.exports;}
function fixture(t,options={variant:'B0'}){
 const file=path.join(__dirname,'r003f_matrix_controls.cjs'),req=createRequire(file);
 const local=n=>n==='node:test'?()=>{}:req(n);local.resolve=req.resolve;
 const F=Function('require','__dirname',fs.readFileSync(file,'utf8')+'\nreturn {runEntry};')(local,__dirname);
 const p=F.runEntry(t,options);assert.equal(p.run.status,0,p.run.stderr);
 // Synthetic admission objects exercise intake, not native provenance claims.
 p.report.evidenceClass='native';p.report.version='1.2.3';
 for(const [field,name] of [['driver','playwright'],['decoder','pngjs']])p.report[field]={name,version:(name==='playwright'?syntheticVersion:require(name+'/package.json').version),entrySha256:require('node:crypto').createHash('sha256').update(fs.readFileSync(name==='playwright'?syntheticEntry:require.resolve(name))).digest('hex')};
 p.report.lifecycle.browserEventsBound=true;for(const x of p.report.lifecycle.pages)x.eventsBound=true;
 fs.writeFileSync(p.file,JSON.stringify(p.report));return p;
}
test('actual selected original source result stays a diagnostic with checked source card UI and images',t=>{
 assert.ok(I,'diagnostic intake required');const p=fixture(t),result=I.diagnostic(p.file,p.out.replace(/entry$/,'derived'),p.digest,{engine:'chromium',dpr:1,id:p.report.cell.id,variant:'B0'});
 assert.equal(result.status,'ADMITTED_MATRIX_DIAGNOSTIC');assert.equal(result.nativeAcceptance,'NOT_EVALUATED');assert.ok(result.captures>=9);
});
test('missing selected capture and wrong variant population cannot admit',t=>{
 assert.ok(I);const p=fixture(t),root=path.join(p.dir,'derived'),s={engine:'chromium',dpr:1,id:p.report.cell.id,variant:'B0'};
 const original=JSON.parse(JSON.stringify(p.report));delete p.report.captures['B0-refined'];fs.writeFileSync(p.file,JSON.stringify(p.report));assert.throws(()=>I.diagnostic(p.file,root,p.digest,s));
 fs.writeFileSync(p.file,JSON.stringify(original));assert.throws(()=>I.diagnostic(p.file,root,p.digest,{...s,variant:'all'}));
});
test('altered actual PNG and late lifecycle error cannot admit a success label',t=>{
 assert.ok(I);const p=fixture(t),root=path.join(p.dir,'derived'),s={engine:'chromium',dpr:1,id:p.report.cell.id,variant:'B0'};
 const file=path.join(p.out,'B0-refined.png'),bytes=fs.readFileSync(file);fs.appendFileSync(file,'drift');assert.throws(()=>I.diagnostic(p.file,root,p.digest,s));fs.writeFileSync(file,bytes);
 p.report.lifecycle.faults.push({kind:'page-crash'});fs.writeFileSync(p.file,JSON.stringify(p.report));assert.throws(()=>I.diagnostic(p.file,root,p.digest,s));
});
test('unmodified full-eight replay rejects a selected diagnostic despite its status label',t=>{
 assert.ok(I);const p=fixture(t),r=I.fullReplay(p.file,path.join(p.dir,'derived'),p.digest,require.resolve('pngjs'),path.join(p.dir,'replay'),5);
 assert.equal(r.returncode,0);assert.equal(r.admitted,false);assert.ok(r.rejections[0]);assert.equal(JSON.parse(fs.readFileSync(p.file)).status,'DIAGNOSTIC');
});

test('complete eight synthetic records use the actual unmodified verifier process and cannot be a union',t=>{
 const p=fixture(t,{}),root=path.join(p.dir,'derived');p.report.status='ACQUIRED';
 const moduleRoot=path.join(p.dir,'node_modules'),pkg=path.join(moduleRoot,'playwright');fs.mkdirSync(pkg,{recursive:true});
 fs.copyFileSync(syntheticEntry,path.join(pkg,'index.js'));fs.writeFileSync(path.join(pkg,'package.json'),JSON.stringify({name:'playwright',version:syntheticVersion,main:'index.js'}));
 fs.writeFileSync(p.file,JSON.stringify(p.report));const before=process.env.NODE_PATH;process.env.NODE_PATH=moduleRoot+path.delimiter+(before||'');
 try{
  const r=I.fullReplay(p.file,root,p.digest,require.resolve('pngjs'),path.join(p.dir,'full-replay'),30);
  assert.equal(r.admitted,true,JSON.stringify(r));assert.deepEqual(r.rejections,[null]);assert.equal(r.expectedMaterializationSha256,p.digest);
  p.report.names.pop();fs.writeFileSync(p.file,JSON.stringify(p.report));
  const incomplete=I.fullReplay(p.file,root,p.digest,require.resolve('pngjs'),path.join(p.dir,'missing-variant'),30);assert.equal(incomplete.admitted,false);
 }finally{if(before===undefined)delete process.env.NODE_PATH;else process.env.NODE_PATH=before;}
});
