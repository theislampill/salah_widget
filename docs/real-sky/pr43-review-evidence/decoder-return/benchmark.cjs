'use strict';
// Bounded Node decode-only measurement. No browser or first-scene inference.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process'),assert=require('node:assert/strict'),{performance}=require('node:perf_hooks');
const fixture=require('./controls.cjs'),{base,sha,pins,locations,payload,encoding,load}=fixture;
function once(api){const input=new Uint8Array(payload),start=performance.now();const decoded=api.decodeCompactReceivers(input,encoding),ms=performance.now()-start;assert.equal(sha(decoded),pins.decoded);return {ms,decodedSha256:pins.decoded,decodedBytes:decoded.length};}
function distribution(values){const sorted=[...values].sort((a,b)=>a-b),rank=p=>sorted[Math.max(0,Math.ceil(sorted.length*p)-1)];return {n:values.length,minMs:sorted[0],p25Ms:rank(.25),medianMs:rank(.5),p75Ms:rank(.75),p95Ms:rank(.95),maxMs:sorted.at(-1),meanMs:values.reduce((a,b)=>a+b,0)/values.length,quantile:'nearest rank; p95 is max for n=9 cold samples'};}
function summary(rows){const a=rows.map(x=>x.production.ms),b=rows.map(x=>x.candidate.ms),production=distribution(a),candidate=distribution(b);return {production,candidate,medianSavedMs:production.medianMs-candidate.medianMs,medianRatio:candidate.medianMs/production.medianMs,medianReductionPercent:100*(1-candidate.medianMs/production.medianMs),pairedSavedMs:distribution(rows.map(x=>x.production.ms-x.candidate.ms))};}
if(process.argv[2]==='--cold-sample'){
 const kind=process.argv[3];assert.ok(['production','candidate'].includes(kind));const api=load(kind),sample=once(api);process.stdout.write(JSON.stringify({...sample,kind})+'\n');
}else{
 const atUtc=new Date().toISOString(),coldRows=[];
 // Nine fresh processes per kind. Input reads, API compilation and Node startup
 // are outside the timed interval; this is first decoder call, not app startup.
 for(let i=0;i<9;i++){
  const order=i%2?['candidate','production']:['production','candidate'],row={pair:i,order};
  for(const kind of order){const run=cp.spawnSync(process.execPath,[__filename,'--cold-sample',kind],{encoding:'utf8',timeout:10000});assert.equal(run.status,0,run.stderr);assert.equal(run.stderr,'');row[kind]=JSON.parse(run.stdout);}
  coldRows.push(row);
 }
 const apis={production:load('production'),candidate:load('candidate')};
 const warmup=[];for(let i=0;i<5;i++)for(const kind of ['production','candidate'])warmup.push({kind,...once(apis[kind])});
 const warmRows=[];
 // Twenty-one alternating serial pairs; natural GC is included if it occurs
 // within the decoder. No --expose-gc/GC forcing or cost subtraction is used.
 for(let i=0;i<21;i++){
  const order=i%2?['candidate','production']:['production','candidate'],row={pair:i,order};
  for(const kind of order)row[kind]=once(apis[kind]);warmRows.push(row);
 }
 const report={schema:'pr43-compact-decode-node-microbenchmark/1',atUtc,endedUtc:new Date().toISOString(),node:{executable:process.execPath,version:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,execArgv:process.execArgv},host:{cpuModel:os.cpus()[0]?.model,logicalCpus:os.cpus().length},pins,sourceHashes:{production:sha(fs.readFileSync(locations.production)),candidate:sha(fs.readFileSync(locations.candidate)),digest:sha(fs.readFileSync(locations.digest))},timedScope:'decodeCompactReceivers only, including both unchanged assetDigest calls, validation, allocation, Huffman/Paeth and scalar output; excludes input/API preparation, Node startup and independent hash verification',cold:{definition:'first decoder invocation in each fresh existing-Node process; nine alternating serial pairs',rows:coldRows,summary:summary(coldRows)},warm:{definition:'same-process loaded functions; five warmups each then twenty-one alternating serial pairs; no forced GC',warmup,rows:warmRows,summary:summary(warmRows)},browserExecutions:0,terrainExecutions:0,limitations:['Windows Node/V8 timings do not establish Chromium/Firefox startup or any first-scene bound','Machine is not an isolated benchmark host; alternating serial pairs reduce ordering bias but do not establish browser causality','First decoder call excludes source parsing/base64 transport/preparation and rendering; warm timings exclude first-call JIT effects','No startup acceptance threshold is introduced or relaxed']};
 fs.writeFileSync(path.join(base,'BENCHMARK.json'),JSON.stringify(report,null,2)+'\n');
 process.stdout.write(JSON.stringify({cold:report.cold.summary,warm:report.warm.summary,output:path.join(base,'BENCHMARK.json')})+'\n');
}
