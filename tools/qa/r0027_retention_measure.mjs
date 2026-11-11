// R0027 retention measurement (Node only, no browser). Usage:
//   node --expose-gc tools/qa/r0027_retention_measure.mjs            (prints a Markdown table)
//   node --expose-gc tools/qa/r0027_retention_measure.mjs <cand|oracle>   (one realm, JSON)
// `oracle` = generated tree with the untouched vendor spectral.mjs (the base behaviour);
// `cand` = the generated (bounded) module. Each realm runs in its own process. Heap deltas
// are V8 heapUsed after a forced GC relative to the realm's start: approximate retained
// bytes of this workload, not a browser heap, latency or battery measurement.
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const mode=process.argv[2];
if(!mode){
 const self=fileURLToPath(import.meta.url),rows={};
 for(const m of ['oracle','cand']){const r=spawnSync(process.execPath,['--expose-gc',self,m],{encoding:'utf8'});if(r.status!==0)throw new Error(r.stderr);rows[m]=JSON.parse(r.stdout);}
 console.log(`Node ${process.version}, ${process.platform}/${process.arch}. Workload: distinct exact B-V via selectSpectrum({bv}) then a revisit of the first 12,000 keys through distinct outer keys.\n`);
 console.log('| distinct keys | base inner entries | base heap delta (MiB) | candidate inner entries | candidate heap delta (MiB) |');
 console.log('|---:|---:|---:|---:|---:|');
 rows.oracle.points.forEach((p,i)=>{const q=rows.cand.points[i];console.log(`| ${p.keys} | ${p.inner} | ${(p.heap/1048576).toFixed(1)} | ${q.inner} | ${(q.heap/1048576).toFixed(1)} |`);});
 console.log('\n| realm | fits computed (fill) | revisit refits | evictions | outer entries | mean self-time per fill call (ms) |');
 console.log('|---|---:|---:|---:|---:|---:|');
 for(const [m,label] of [['oracle','base (unbounded)'],['cand','candidate (FIFO 12,000)']]){const r=rows[m];console.log(`| ${label} | ${r.fits} | ${r.refits} | ${r.evictions} | ${r.outer} | ${r.msPerCall.toFixed(3)} |`);}
 process.exit(0);
}
const {spectralInstance,series,viaInner,probe,CAPACITY}=await import('../../tests/real-sky/spectral-fit-cache-fixture.mjs');
const heap=()=>{global.gc();global.gc();return process.memoryUsage().heapUsed;};
const c=await spectralInstance(mode==='oracle'?'oracle':'cand'),sel=c.spectral.selectSpectrum,base=heap(),points=[];
let keys=1,ms=0;const checkpoints=[1000,5000,10000,12000,15000,20000,30000,40000];
for(const target of checkpoints){const t0=performance.now();for(const bv of series(0,target-keys,keys-1))sel({bv});ms+=performance.now()-t0;keys=target;points.push({keys,inner:c.inner.size,outer:c.outer.size,heap:heap()-base});}
const fits=probe.stats(c.inner).sets,before=fits;
for(const bv of series(0,CAPACITY))sel(viaInner(bv));
const s=probe.stats(c.inner);
process.stdout.write(JSON.stringify({points,fits,refits:s.sets-before,evictions:s.deletes,outer:c.outer.size,msPerCall:ms/(keys-1)}));
