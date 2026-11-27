'use strict';
// Explicit, source-pinned derived diagnostic entry. The protected original
// operational program is recovered exactly by the declared literal inverse.
// No global admission monkeypatch, different driver, or extra original wait.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const need=(ok,message)=>{if(!ok)throw Error(message);};
const ORIGINAL_SHA256='cc7a791fba7438a36743a424d6bd063289217b54bea05ec10be07206356abf93';
const SEAMS=[
  {
    "before": "const SOURCE_PINS={\n",
    "after": "const SOURCE_PINS={\n  'r0040_mechanism.cjs':'cc7a791fba7438a36743a424d6bd063289217b54bea05ec10be07206356abf93',\n  'r0040_autoattach_network.cjs':'6beea150ac4aadd4a7a741e62e1f9b9fd899d3a85cd20ac7d231185521649f66',\n",
    "count": 1
  },
  {
    "before": "N=require('./r0040_mechanism_network.cjs')",
    "after": "N=require('./r0040_autoattach_network.cjs')",
    "count": 1
  },
  {
    "before": "r0040-mechanism-",
    "after": "r0040-autoattach-",
    "count": 7
  },
  {
    "before": "ADMITTED_MECHANISM_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION",
    "after": "ADMITTED_AUTOATTACH_MECHANISM_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION",
    "count": 1
  },
  {
    "before": "instrumented-mechanism-passive-date-only",
    "after": "instrumented-autoattach-mechanism-passive-date-only",
    "count": 1
  },
  {
    "before": "const ARTIFACT='mechanism-observation.json'",
    "after": "const ARTIFACT='autoattach-observation.json'",
    "count": 1
  },
  {
    "before": "networkLimits:N.LIMITS,",
    "after": "networkLimits:N.LIMITS,autoAttach:N.identity(),",
    "count": 1
  },
  {
    "before": "mechanism-instrumentation",
    "after": "autoattach-instrumentation",
    "count": 1
  },
  {
    "before": "mechanism-bracket-prefix",
    "after": "autoattach-bracket-prefix",
    "count": 1
  },
  {
    "before": "mechanism-network-prefix",
    "after": "autoattach-network-prefix",
    "count": 3
  },
  {
    "before": "mechanism-observation-ended",
    "after": "autoattach-observation-ended",
    "count": 1
  },
  {
    "before": "usage: r0040_mechanism.cjs",
    "after": "usage: r0040_autoattach.cjs",
    "count": 1
  }
];

const originalFile=path.join(__dirname,'r0040_mechanism.cjs');
need(fs.lstatSync(originalFile).isFile()&&!fs.lstatSync(originalFile).isSymbolicLink(),'regular original mechanism source required');
const original=fs.readFileSync(originalFile,'utf8');
function replace(source,before,after,count){
  need(source.split(before).length-1===count,'derived mechanism seam population differs');
  return source.split(before).join(after);
}
function deriveMechanism(source){
  need(typeof source==='string'&&sha(source)===ORIGINAL_SHA256,'original mechanism source digest differs');
  let derived=source;for(const seam of SEAMS)derived=replace(derived,seam.before,seam.after,seam.count);
  let inverse=derived;for(const seam of [...SEAMS].reverse())inverse=replace(inverse,seam.after,seam.before,seam.count);
  need(inverse===source,'full mechanism source inverse differs');
  return {source:derived,identity:{protocol:'r0040-autoattach-entry-adapter/1',originalSha256:ORIGINAL_SHA256,derivedSha256:sha(derived),
    originalRecoveredExactly:true,seams:SEAMS.map(s=>({originalSha256:sha(s.before),derivedSha256:sha(s.after),occurrences:s.count}))}};
}
const derived=deriveMechanism(original);
function reverseMechanism(source){
  need(typeof source==='string'&&sha(source)===derived.identity.derivedSha256,'derived mechanism source digest differs');
  let inverse=source;for(const seam of [...SEAMS].reverse())inverse=replace(inverse,seam.after,seam.before,seam.count);
  need(sha(inverse)===ORIGINAL_SHA256,'mechanism source inverse identity differs');return inverse;
}
module._compile(derived.source,__filename);
Object.assign(module.exports,{ORIGINAL_SHA256,deriveMechanism,reverseMechanism,ENTRY_ADAPTER_IDENTITY:derived.identity});
