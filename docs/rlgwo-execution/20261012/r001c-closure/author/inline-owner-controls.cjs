'use strict';
// Execute only the proposed inline-owner admission statements, never a force or native case.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const own=__dirname,proposal=path.join(own,'source-proposal-r2'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const fixture=fs.readFileSync(path.join(proposal,'proposed/tests/rlgwo-docs-contract.cjs'),'utf8');
const source=fs.readFileSync('C:/Users/theis/.codex/worktrees/r001c-docs-delivery/salah_widget/index.html','utf8');
const binding=JSON.parse(fs.readFileSync(path.join(proposal,'SOURCE_EQUIVALENCE.json'),'utf8')).forceFixture.currentInlineOwner;
assert.equal(sha(source),binding.wholeGeneratedSha256);
const marker='      // The delivered inline atmosphere owns this clamp.';
assert.equal(fixture.split(marker).length,2);
const a=fixture.indexOf(marker),b=fixture.indexOf('\n    }\n    const forced =',a);
assert(b>a);
const guard=fixture.slice(a,b);
const regionA=fixture.indexOf('function region(source, start, end) {'),regionB=fixture.indexOf('\nfunction context(',regionA);
assert(regionA>=0&&regionB>regionA);
const actualRegion=fixture.slice(regionA,regionB);
function admission(input,code=guard){
  const qLine=input.match(/^const q\s*=.*;$/m)?.[0];
  assert(qLine,'actual production parser declaration required');
  return vm.runInNewContext(`${actualRegion}\nlet clampLine='',eligibility='';\n${code}\n({clampLine,eligibility})`,{source:input,qLine,assert,digest:sha},{timeout:1000});
}
const controls=[];
function check(name,fn){fn();controls.push({name,status:'PASS'});}
function refused(name,input,expected,code=guard){check(name,()=>assert.throws(()=>admission(input,code),expected));}
check('connected valid delivered input selects exact widget dependency',()=>{
  const got=admission(source);assert.equal(got.clampLine,binding.widgetClamp);assert.equal(sha(got.eligibility),binding.permissionSha256);
});
check('old first-global-clamp RED; actual new admission GREEN',()=>{
  const old=source.match(/^const clamp\s*=.*$/m)[0];assert.notEqual(sha(old),binding.widgetClampSha256);
  const now=admission(source);assert.equal(sha(now.clampLine),binding.widgetClampSha256);
});
refused('duplicate widget script refused before digest association',source+'<script>const q = new URLSearchParams(location.hash.slice(1));\nfunction atmosphere(M){}</script>',/unique inline widget script owner/);
const scripts=[...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
const owner=scripts.filter(x=>x[2].includes('const q = new URLSearchParams(location.hash.slice(1));')&&x[2].includes('function atmosphere(M){'));
assert.equal(owner.length,1);
const role=source.slice(0,owner[0].index)+owner[0][0].replace('<script>','<script type="module">')+source.slice(owner[0].index+owner[0][0].length);
refused('changed actual script role refused',role,/inline widget script role/);
refused('wrong complete generated identity refused',source+'\n',/delivered inline generated entry/);
refused('changed source-body pin refused',source,/delivered inline widget script/,guard.replace(binding.scriptBodySha256,'0'.repeat(64)));
refused('changed clamp pin refused',source,/inline widget clamp changed/,guard.replace(binding.widgetClampSha256,'0'.repeat(64)));
refused('changed eligibility pin refused',source,/inline lunar eligibility changed/,guard.replace(binding.permissionSha256,'0'.repeat(64)));
const report={schema:'r001c-inline-owner-admission-controls/1',status:'PASS',producerFixtureSha256:sha(fixture),actualGuardSha256:sha(guard),actualRegionHelperSha256:sha(actualRegion),generatedSha256:sha(source),controls,originalForceCasesExecuted:0,originalNativeCasesExecuted:0,browser:0,server:0,build:0,sharedWrites:0};
fs.writeFileSync(path.join(own,'INLINE_OWNER_CONTROLS.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,controls:controls.length,originalOrNativeReplays:0}));
