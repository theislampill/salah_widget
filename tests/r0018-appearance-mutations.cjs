'use strict';
// Each isolated source mutant must fail the same actual consumer oracle that the healthy source passes.
const assert=require('node:assert/strict');
const {read,sha,widget,builder,configSession}=require('./r0018-appearance-fixture.cjs');
const {composition}=require('./r0018-timetable-contrast.cjs');
const source=read('index.html'),config=read('config.js'),builderSource=read('builder.html');
const valid={lat:24.47,lon:39.61,tz:'UTC',label:'Madinah',method:'4',school:'0',time:'24',units:'f',datefmt:'YYYY-MM-DD',source:'manual'};
const once=(text,before,after)=>{assert.equal(text.split(before).length,2,'Exact single mutation seam');return text.replace(before,after);};
const cases=[
 {name:'opaque backing reintroduced as default',mutant:{source:once(source,'background:linear-gradient(160deg,#ffffff26,#ffffff0d);border:','background:linear-gradient(160deg,#ffffff26,#ffffff0d),rgba(9,17,28,.90);border:')},
  oracle:({source})=>{const c=composition(source,'normal');assert.equal(c.opacity,1);assert.ok(c.ratio<4.5,'Owner-selected glass must remain distinct from opt-in contrast');}},
 {name:'card binding forces contrast when glass is selected',mutant:{source:once(source,'card.dataset.appearance=c.appearance==="contrast"?"contrast":"glass"','card.dataset.appearance="contrast"')},
  oracle:({source,configSource})=>{const w=widget({source,configSource});assert.equal(w.render().rows,6);assert.equal(w.document.querySelector('.c').dataset.appearance,'glass');}},
 {name:'explicit hash glass omitted from detected preference overlay',mutant:{configSource:once(config,'"datefmt", "appearance", "lp"','"datefmt", "lp"')},
  oracle:({configSource})=>{const {api}=configSession(configSource),base=api.normalize({...valid,appearance:'contrast'});const c=api.applyHashPrefs(base,api.parseHash('#local=1&appearance=glass').cfg);assert.equal(c.lat,24.47);assert.equal(c.method,'4');assert.equal(c.appearance,'glass');}},
 {name:'serializer omits explicitly selected glass default',mutant:{configSource:once(config,'c.appearance !== DEFAULTS.appearance || Array.isArray(opts.explicitPrefs) && opts.explicitPrefs.indexOf("appearance") >= 0','c.appearance !== DEFAULTS.appearance')},
  oracle:({configSource,builderSource})=>{const b=builder({source:builderSource,configSource});for(const mode of ['portable','local']){b.run('setMode('+JSON.stringify(mode)+')');b.input('appearance','glass');assert.equal(new URLSearchParams(b.hash()).get('appearance'),'glass');assert.match(b.nodes.get('code').value,/width:325px;height:530px/);}}},
 {name:'pending reset loses ownership of a newer appearance edit',mutant:{source:once(source,',appearance:"set-appearance"','')},
  oracle:async({source,configSource})=>{const w=widget({source,configSource});w.open();await w.reset();w.input('set-appearance','contrast');await w.settleReset({...valid,lat:41,lon:-74,source:'coarse-ip'});assert.equal(w.evaluate('CONFIG.lat'),41);assert.equal(w.evaluate('CONFIG.appearance'),'contrast');assert.equal(w.field('set-appearance').value,'contrast');}},
 {name:'builder appearance edits do not update the real preview/output',mutant:{builderSource:once(builderSource,'const fields=["label","lat","lon","method","school","time","units","appearance"];','const fields=["label","lat","lon","method","school","time","units"];')},
  oracle:({configSource,builderSource})=>{const b=builder({source:builderSource,configSource});b.input('appearance','contrast');assert.equal(new URLSearchParams(b.hash()).get('appearance'),'contrast');assert.equal(new URL(b.nodes.get('pv').src).hash.slice(1),b.hash());}}
];
async function main(){
 const results=[];
 for(const c of cases){const healthy={source,configSource:config,builderSource};try{
   await c.oracle(healthy);let error;
   try{await c.oracle({...healthy,...c.mutant});}catch(e){error=e;}
   assert.ok(error instanceof assert.AssertionError,'Mutant must fail a consumer assertion, not instrumentation');
   results.push({name:c.name,status:'PASS',healthyControl:'PASS',mutant:'DETECTED',failure:error.message,mutantSha256:Object.fromEntries(Object.entries(c.mutant).map(([k,v])=>[k,sha(v)]))});
  }catch(e){results.push({name:c.name,status:'FAIL',error:e.message});}}
 console.log(JSON.stringify({sourceSha256:sha(source),configSha256:sha(config),builderSha256:sha(builderSource),limit:'Actual source/config/settings/builder consumer controls with recording DOM; no native visual/focus claim',results},null,2));
 process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
