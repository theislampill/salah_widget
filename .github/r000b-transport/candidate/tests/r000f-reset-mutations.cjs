"use strict";
const assert=require("node:assert/strict"),{spawnSync}=require("node:child_process"),path=require("node:path");
const cases={preapply:"reset preserves newer method in applied",restore:"reset retains preference edits made during",dirty:"reset preserves newer method in applied"};
for(const [mutant,discriminator]of Object.entries(cases)) {
  const result=spawnSync(process.execPath,[path.join(__dirname,"r000f-reset.cjs"),"--mutant",mutant],{encoding:"utf8"});
  assert.equal(result.status,1,`${mutant} must fail behaviour`); assert.ok(result.stderr.includes(`FAIL ${discriminator}`),result.stderr);
  assert.ok(!result.stderr.includes("TypeError"),"bootstrap failure cannot qualify a mutant"); console.log("PASS mutant caught:",mutant,"by",discriminator);
}
