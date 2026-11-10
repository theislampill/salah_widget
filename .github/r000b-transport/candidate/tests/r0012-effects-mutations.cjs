"use strict";
const assert=require("node:assert/strict"),{spawnSync}=require("node:child_process"),path=require("node:path");
const result=spawnSync(process.execPath,[path.join(__dirname,"r0012-effects.cjs"),"--mutant","fallback-owner"],{encoding:"utf8"});
assert.equal(result.status,1,"unbound fallback must fail behavioural effects assertions");
assert.ok(result.stderr.includes("FAIL obsolete rejection cannot fallback over"),result.stderr);
assert.ok(result.stderr.includes("FAIL obsolete rejection cannot steal current"),result.stderr);
assert.ok(!result.stderr.includes("TypeError"),"bootstrap errors cannot qualify a mutant");
console.log("PASS mutant caught: fallback owner omitted; newest clipboard payload and recovery focus assertions fail");
