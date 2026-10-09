// Audit-only copies of delivered index; never changes the product or shared tests.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const root = 'C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget';
const out = __dirname;
const node = 'C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe';
const sourcePath = path.join(root, 'index.html');
const bytes = fs.readFileSync(sourcePath);
const digest = v => crypto.createHash('sha256').update(v).digest('hex');
const expectedSource = 'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee';
if (digest(bytes) !== expectedSource) throw Error('Source changed from audit target');
const source = bytes.toString('utf8');
const dir = path.join(out, 'mutants');
fs.mkdirSync(dir, {recursive:true});
const suite = path.join(root, 'tests/r000c-weather.test.cjs');
const definitions = [
  {id:'R000E-accessor-alpha', pattern:'R000E .* actual tile sampler never contributes quantitative authority', total:5, fail:4,
   from:'function radarPrecipNow(){ return 0; }',
   to:'function radarPrecipNow(){ const r=radarEvidence(); const s=weatherRadar&&weatherRadar.sample; return r.available&&s&&s.returnCount>=3?(0.3+4.0*s.coverage)*s.meanAlpha:0; }',
   expectation:'0/15/20/45 dBZ fail; transparent/no-data remains passing; actual fetchRadar+7x7 sample is used'},
  {id:'R000E-direct-numeric-radar', pattern:'R000E lower-level model control', total:5, fail:3,
   from:'const precip=w?wxNumber(w.precip,0):null, has=precip!=null&&precip>=_PRECIP_MIN;',
   to:'const modelPrecip=w?wxNumber(w.precip,0):null, precip=Math.max(modelPrecip||0,wxNumber(radarMm,0)||0), has=precip!=null&&precip>=_PRECIP_MIN;',
   expectation:'dry rain, dry thunder and model0.3 thunder fail; model2 and raw-clear controls remain passing'},
  {id:'R001E-weather-truthiness', pattern:'R001E both real acquisitions preserve coordinate', total:6, fail:4,
   from:'if(!usableWeatherCoordinates(lat,lon)||wxBusy) return;',
   to:'if(!lat||!lon||wxBusy) return;',
   expectation:'equator, meridian, both-zero and negative-zero independently fail; tiny nonzero and ordinary coordinates remain passing'},
  {id:'R001E-radar-truthiness', pattern:'R001E both real acquisitions preserve coordinate', total:6, fail:4,
   from:'if(SIM.wx!=null || !usableWeatherCoordinates(lat,lon) || radarBusy) return;',
   to:'if(SIM.wx!=null || !lat || !lon || radarBusy) return;',
   expectation:'equator, meridian, both-zero and negative-zero independently fail; tiny nonzero and ordinary coordinates remain passing'}
];
const receipts = [];
for (const def of definitions) {
  const count = source.split(def.from).length - 1;
  if (count !== 1) throw Error(def.id+': mutation anchor count '+count);
  const mutated = source.replace(def.from, def.to);
  const mutant = path.join(dir, def.id+'.html');
  fs.writeFileSync(mutant, mutated);
  for (const [kind, target, wantedFail] of [['green',sourcePath,0],['mutant',mutant,def.fail]]) {
    const args = ['--test','--test-concurrency=1','--test-name-pattern',def.pattern,suite];
    const env = {...process.env, SALAH_WEATHER_SOURCE:target, SALAH_CONFIG_SOURCE:path.join(root,'config.js')};
    const start = new Date().toISOString();
    const result = cp.spawnSync(node,args,{cwd:root,env,encoding:'utf8',timeout:30000});
    const tap = (result.stdout||'')+(result.stderr||'');
    const tapPath = path.join(out,def.id+'.'+kind+'.tap');
    fs.writeFileSync(tapPath,tap);
    const stat = key => Number(tap.match(new RegExp('^# '+key+' (\\d+)$','m'))?.[1]);
    const pass = stat('pass'), fail = stat('fail'), skip = stat('skipped'), todo = stat('todo');
    const expected = {fail:wantedFail,pass:def.total-wantedFail,exitCode:wantedFail?1:0};
    const observed = {fail,pass,skip,todo,exitCode:result.status,error:result.error?.message||null};
    const conforms = !result.error&&observed.fail===expected.fail&&observed.pass===expected.pass&&observed.exitCode===expected.exitCode;
    receipts.push({id:def.id,kind,startedAtUtc:start,endedAtUtc:new Date().toISOString(),
      command:{executable:node,args,workingDirectory:root,environment:{SALAH_WEATHER_SOURCE:target,SALAH_CONFIG_SOURCE:env.SALAH_CONFIG_SOURCE}},
      mutation:{from:def.from,to:def.to,isolatedCopy:mutant,sha256:digest(mutated),anchorCount:count},
      discriminator:def.expectation,sourceSha256:expectedSource,testFileSha256:digest(fs.readFileSync(suite)),
      tapPath,tapSha256:digest(tap),expected,observed,conforms});
    if (!conforms) {
      fs.writeFileSync(path.join(out,'mutation-receipts.json'),JSON.stringify({status:'UNEXPECTED',receipts},null,2)+'\n');
      throw Error(def.id+' '+kind+' unexpected '+JSON.stringify(observed));
    }
  }
}
if (digest(fs.readFileSync(sourcePath)) !== expectedSource) throw Error('Product source changed during mutation run');
const report = {schema:'rlgwo-isolated-mutation-receipt-v1',target:'18ff14860ff41c084b1db5f396bb62aa9c22b1be',
  status:'EXPECTED GREEN AND MUTANT RED',sourceSha256:expectedSource,node:process.version,serial:true,
  browserExecution:false,productMutation:false,
  skipped:{R000B:'Independent explicit DESIGN/README valid-time/receipt-time contract still unmet',
    R000C:'Independent explicit README unavailable-temperature contract still unmet',
    R000D:'Independent explicit README bounded-wait/backoff/suspension contract still unmet'},receipts};
fs.writeFileSync(path.join(out,'mutation-receipts.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,controls:definitions.length,greenTests:receipts.filter(r=>r.kind==='green').reduce((n,r)=>n+r.observed.pass,0),
  mutantFailures:receipts.filter(r=>r.kind==='mutant').reduce((n,r)=>n+r.observed.fail,0)},null,2));
