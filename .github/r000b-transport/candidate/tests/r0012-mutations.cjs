"use strict";
const assert=require("node:assert/strict");
const {spawnSync}=require("node:child_process");
const path=require("node:path");
const cases={success:"both false or thrown fallback", "install-recovery":"install recovery is platform-specific",stale:"new same-button attempt owns"};
for(const [mutant,discriminator]of Object.entries(cases)) {
  const result=spawnSync(process.execPath,[path.join(__dirname,"r0012-clipboard.cjs"),"--mutant",mutant],{encoding:"utf8"});
  assert.equal(result.status,1,`${mutant} must fail behaviour`); assert.ok(result.stderr.includes(`FAIL ${discriminator}`),result.stderr);
  assert.ok(!result.stderr.includes("TypeError"),"bootstrap errors cannot qualify a mutant"); console.log("PASS mutant caught:",mutant,"by",discriminator);
}
