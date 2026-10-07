"use strict";
const assert=require("node:assert/strict"),{spawnSync}=require("node:child_process"),path=require("node:path");
for(const mutant of ["headers","abort-only"]){const r=spawnSync(process.execPath,[path.join(__dirname,"r001f-deadline.cjs"),"--mutant",mutant],{encoding:"utf8"});assert.equal(r.status,1);assert.ok(r.stderr.includes("FAIL body stall retains deadline and advances exactly once"),r.stderr);assert.ok(!r.stderr.includes("TypeError")&&!r.stderr.includes("boundary missing"),"bootstrap is not mutation evidence");console.log("PASS mutant caught:",mutant);}
