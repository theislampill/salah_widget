"use strict";
const assert=require("node:assert/strict"),{spawnSync}=require("node:child_process"),path=require("node:path");
for(const mutant of ["method","units"]){const r=spawnSync(process.execPath,[path.join(__dirname,"r0010-preferences.cjs"),"--mutant",mutant],{encoding:"utf8"});assert.equal(r.status,1);assert.ok(r.stderr.includes("FAIL fresh runtime follows selected 2/f through every export"),r.stderr);assert.ok(!r.stderr.includes("TypeError")&&!r.stderr.includes("boundary missing"),"bootstrap is not mutation evidence");console.log("PASS mutant caught:",mutant);}
