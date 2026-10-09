'use strict';
// Offline association/re-evaluation only. Never changes or replays native results.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sourcePath=path.join(__dirname,'browser14-chromium-v2/results.json');
const original=fs.readFileSync(sourcePath),sourceSha=crypto.createHash('sha256').update(original).digest('hex');
const report=JSON.parse(original),dry=report.cases.find(c=>c.id==='14-dry'),wet=report.cases.find(c=>c.id==='14-wet');
if(!dry||!wet||report.runtime.treeSha256!=='f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'||!report.runtimeUnchanged)throw Error('Wrong or changed runtime');
const q=dry.state.qa.wxTruth,reason='thunder model code, interval precip 0.00mm below model threshold → overcast';
const checks={
 exactDryModelAndNoRadarMm:q.rawCode===95&&q.modelPrecipMm===0&&q.effectivePrecipMm===0&&q.radarPrecipMm===0&&!q.radarConfirming,
 quantitativeGateDecision:q.modelGateReason===reason&&q.visualPermissions.quantitativeSupport===reason,
 currentModelConditionRetainedUnderH5:q.modelCondition==='thunder'&&q.conditionState==='model-estimated-thunder'&&dry.state.fx==='thunder',
 actualNoWetEffects:!q.visualPermissions.rain&&!q.visualPermissions.snow&&!q.visualPermissions.lightning&&!q.activePrecip&&!q.activeThunder&&dry.state.precip==='off'&&dry.state.lightning==='off'&&dry.state.visibleParticles===0,
 accessibleQuantitativeWithdrawal:dry.state.headerLabel.includes('current model estimate')&&dry.state.headerLabel.includes('quantitative effect decision: '+reason),
 originalMeaningfulDryAssertions: Object.entries(dry.checks).every(([key,value])=>key==='gateDowngradeDespite0dBZ'||value===true),
 originalWetPositive:wet.status==='PASS'&&Object.values(wet.checks).every(v=>v===true)&&wet.state.visibleParticles>0&&wet.state.precip==='on'&&wet.state.lightning==='off',
 actualReadableTile:dry.state.radar.sample.returnCount===49&&dry.state.radar.sample.coverage===1&&Math.abs(dry.state.radar.sample.meanAlpha-73/255)<1e-12,
 exactSnapshotCustody:dry.fixture.sourceSha256==='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'&&wet.fixture.sourceSha256===dry.fixture.sourceSha256,
};
const result={schema:'rlgwo-radar-browser-semantic-oracle-reconciliation-v1',
 status:Object.values(checks).every(v=>v===true)?'MATCHES CORRECT QUANTITATIVE-EFFECT ORACLE':'DOES NOT MATCH',
 target:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',browserExecution:'PRIMARY executed V2; C independently read exact snapshots and inspected both card crops',
 original:{path:'workers/C/browser14-chromium-v2/results.json',sha256:sourceSha,status:report.status,dryStatus:dry.status,wetStatus:wet.status,
  failedAssertion:'gateDowngradeDespite0dBZ',expected:'qa.wxTruth.modelCondition == overcast',observed:q.modelCondition,retainedUnchanged:true},
 classification:'HARNESS SEMANTIC ORACLE ERROR; original FAIL preserved, no product counterexample established by this predicate',
 authorities:[{file:'WORKER_BRIEF.md',authority:'Explicit binding H5/H8 owner amendment: fresh eligible CURRENT model WMO condition retained separately from amount-gated precipitation effects and observed authority'},
  {file:'src/native/index.html',lines:[1625,1651],url:'https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1625-L1651',
   explanation:'1629 effectCode and modelDowngrade consume the lower gate;1630 raw live modelCode is deliberate;1638–1640 final quantities gate model rain/snow independently;1643 assigns raw modelCode diagnostic.'},
  {file:'src/native/index.html',lines:[2393,2413],url:'https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L2393-L2413',explanation:'Original lower gate 95/precip0/unsupported radar must still return3. Fresh source tests plus independent direct-gate mutant detect restoring numeric radar influence.'},
  {file:'DESIGN.md',lines:[244,267],url:'https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267'}],
 correctedExpected:'Effect decision is overcast with exact zero quantitative amount, no particle/strike permission or mm from radar, and accessible uncertainty; raw current WMO95/modelCondition may remain thunder under explicit owner amendment.',
 checks,observed:{dry:{modelGateReason:q.modelGateReason,modelCondition:q.modelCondition,quantity:q.model.quantity,visualPermissions:q.visualPermissions,particles:dry.state.visibleParticles,fx:dry.state.fx,precip:dry.state.precip,lightning:dry.state.lightning,tile:dry.state.radar.sample},
 wet:{particles:wet.state.visibleParticles,precip:wet.state.precip,lightning:wet.state.lightning,visualPermissions:wet.state.qa.wxTruth.visualPermissions}},
 independentLowerGateProof:'mutation-receipts.json: untouched GREEN5/5; alpha accessor mutant4/5 RED; direct numeric-radar mutant3/5 RED. Required pure-gate downgrade is not waived or weakened.',
 noRerun:'Read-only re-evaluation of fully recorded native effects and state; consumer unchanged, no repeat native operation, original FAIL/driver/fixture/crops remain.',
 limits:'No live precipitation/local observation/ETA/provider coverage claim. Pixel crops and fixed-clock transport wrapper do not newly certify all-phase optics or normal-live M0.'};
if(fs.readFileSync(sourcePath).compare(original)!==0)throw Error('Original failure was changed');
fs.writeFileSync(path.join(__dirname,'browser14-v2-semantic-reconciliation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,checks,originalStatus:report.status},null,2));
