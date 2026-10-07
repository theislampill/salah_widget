"use strict";
const assert=require("node:assert/strict");
const {spawnSync}=require("node:child_process");
const path=require("node:path");
const cases={coarse:"coarse-after-London",reverse:"builder reverse body",gps:"builder GPS after manual",forward:"builder search after manual",
  "settings-gps":"settings GPS after manual",candidate:"settings changed query requests Cairo",close:"settings close alone"};
for(const [mutant,discriminator]of Object.entries(cases)) {
  const result=spawnSync(process.execPath,[path.join(__dirname,"r000f-intent.cjs"),"--mutant",mutant],{encoding:"utf8"});
  assert.equal(result.status,1,`${mutant} must fail its behaviour assertion`);
  assert.ok(result.stderr.includes(`FAIL ${discriminator}`),`${mutant} did not reach its discriminator: ${result.stderr}`);
  assert.ok(!result.stderr.includes("TypeError")&&!result.stderr.includes("gate missing"),"mutant must fail behaviour, not bootstrap");
  console.log("PASS mutant caught:",mutant,"by",discriminator);
}
