'use strict';
// Consumes the real native observation through the unchanged demand implementation.
// No frame, browser, DOM, screenshot, network or storage operation is created.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const HERE=__dirname,read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const proposal=read(path.join(HERE,'PROJECTION_PROPOSAL.json'));
const raw=fs.readFileSync(proposal.actualObservation.path);assert.equal(sha(raw),proposal.actualObservation.sha256);
const actual=JSON.parse(raw),before=actual.snapshots['native boot fallback before explicit manual write'];
const old=fs.readFileSync(proposal.preimage.path,'utf8'),corrected=fs.readFileSync(proposal.proposed.path,'utf8');
assert.equal(sha(Buffer.from(old)),proposal.preimage.sha256);assert.equal(sha(Buffer.from(corrected)),proposal.proposed.sha256);
assert.equal(old.split(proposal.from).length,2);assert.equal(old.replace(proposal.from,proposal.to),corrected);
const load=(source)=>{const module={exports:{}},context={module,exports:module.exports,require,__dirname:path.dirname(proposal.preimage.path),Buffer,URL,URLSearchParams,process};vm.runInNewContext(source+'\nmodule.exports.__retainedDemand=demand;',context);return module.exports.__retainedDemand;};
const demand=load(corrected),name=proposal.assertionName,controls=[];
const predicate=clause=>new vm.Script(clause,{filename:'exact-readFault-demand-predicate'});
const oldPredicate=predicate(proposal.from),newPredicate=predicate(proposal.to);
function observe(label,state,expression,expected){const row={checks:[]};let error=null;try{demand(row,name,expression.runInNewContext({before:state}),state.config);}catch(e){error={name:e.name,code:e.code||null,assertion:e.assertion||null,message:e.message};}const disposition=error?'REJECTED':'ACCEPTED';assert.equal(disposition,expected,label);controls.push({label,disposition,checks:row.checks,error});return controls.at(-1);}
const red=observe('actual native null CONFIG reproduces original pre-demand TypeError',before,oldPredicate,'REJECTED');assert.equal(red.checks.length,0);assert.equal(red.error.name,'TypeError');
const green=observe('same immutable native observation satisfies explicit null active/diagnostic clause',before,newPredicate,'ACCEPTED');assert.equal(green.checks.length,1);assert.equal(green.checks[0].name,name);assert.equal(green.checks[0].passed,true);
for(const [label,change]of[
 ['adopted global target refuses despite old null diagnostics',s=>s.config={lat:51.5,lon:-.12}],
 ['non-null diagnostic latitude refuses',s=>s.app.config.lat=51.5],
 ['non-null diagnostic longitude refuses',s=>s.app.config.lon=-.12],
 ['missing active-config key refuses',s=>delete s.config],
 ['object with null coordinates refuses rather than replacing nullable contract',s=>s.config={lat:null,lon:null}],
 ['missing diagnostic object refuses',s=>s.app.config=null]
]){const state=JSON.parse(JSON.stringify(before));change(state);const out=observe(label,state,newPredicate,'REJECTED');if(out.error.code==='CONSUMER_ASSERTION')assert.equal(out.checks[0].passed,false);}
const result={schema:'r0011-real-retained-native-projection-adverse-controls/1',status:'PASS_SOURCE_CONSUMER_CONTROLS_ONLY',controls,controlCount:controls.length,actualNativeResult:proposal.actualObservation,oldRowStatus:actual.status,oldOriginalChecks:actual.checks.length,nativeObservationReplayedThroughPredicate:true,newNativeBrowserRuns:0,productOrOperativeDriverWrites:0,originalNativeAcceptanceConferred:false,cycleReset:false};
fs.writeFileSync(path.join(HERE,'PROJECTION_CONTROLS.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({status:result.status,controls:controls.length,native:'NOT_RUN'})+'\n');
