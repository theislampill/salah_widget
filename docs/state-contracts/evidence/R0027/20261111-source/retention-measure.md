# R0027 retention measurement

Command: `node tools/qa/r0027_retention_measure.mjs` (spawns `node --expose-gc` per realm). Base = generated tree with the untouched vendor spectral.mjs (behaviour of main 645b53cc); candidate = generated bounded module.
Heap deltas: V8 heapUsed after forced GC, relative to realm start, for this synthetic workload only. Not a browser heap, latency, GPU or battery measurement.

Node v24.14.0, win32/x64. Workload: distinct exact B-V via selectSpectrum({bv}) then a revisit of the first 12,000 keys through distinct outer keys.

| distinct keys | base inner entries | base heap delta (MiB) | candidate inner entries | candidate heap delta (MiB) |
|---:|---:|---:|---:|---:|
| 1000 | 1000 | 2.7 | 1000 | 2.7 |
| 5000 | 5000 | 12.8 | 5000 | 12.8 |
| 10000 | 10000 | 25.4 | 10000 | 25.4 |
| 12000 | 12000 | 30.3 | 12000 | 30.3 |
| 15000 | 15000 | 37.2 | 12000 | 37.0 |
| 20000 | 20000 | 49.1 | 12000 | 48.5 |
| 30000 | 30000 | 72.0 | 12000 | 57.4 |
| 40000 | 40000 | 95.7 | 12000 | 57.4 |

| realm | fits computed (fill) | revisit refits | evictions | outer entries | mean self-time per fill call (ms) |
|---|---:|---:|---:|---:|---:|
| base (unbounded) | 40000 | 0 | 0 | 12000 | 0.195 |
| candidate (FIFO 12,000) | 40000 | 12000 | 40000 | 12000 | 0.192 |

Reading: candidate inner entries are flat at 12,000. The candidate heap keeps rising until about 24,000 distinct keys and is then flat: the outer selection cache (unchanged, first 12,000 keys) still references the sample arrays of fits the inner cache has evicted, so the per-instance union is up to 24,000 sample arrays (ES27-08). The base keeps growing linearly (about 2.4 KiB per distinct key here). Revisiting 12,000 evicted keys costs 12,000 refits on the candidate and none on the base; mean self-time per fill call was about 0.19 ms in both on this machine.
