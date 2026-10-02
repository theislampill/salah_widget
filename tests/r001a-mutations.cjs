"use strict";
const assert=require("node:assert/strict");
const {spawnSync}=require("node:child_process");
const path=require("node:path");
for(const [mutant,discriminator]of Object.entries({arrows:"Right arrow moves focus",tabindex:"Right arrow moves focus"})) {
  const result=spawnSync(process.execPath,[path.join(__dirname,"r001a-radio.cjs"),"--mutant",mutant],{encoding:"utf8"});
  assert.equal(result.status,1,`${mutant} must fail behaviour`); assert.ok(result.stderr.includes(`FAIL ${discriminator}`),result.stderr);
  assert.ok(!result.stderr.includes("TypeError")&&!result.stderr.includes("boundary missing"),"bootstrap failure cannot qualify a mutant");
  console.log("PASS mutant caught:",mutant,"by",discriminator);
}
