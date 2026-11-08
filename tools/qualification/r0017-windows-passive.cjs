#!/usr/bin/env node
'use strict';
// R0017-C14: explicit passive-only caller, separate from the enforced phase-2
// entry and historical verdicts. Root must admit these exact bytes before use.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const passive=require('./r0017-passive-network.cjs');
const BOUND_BASE_SHA='c095924a71b4358677ff0d2bdf8630b9fdb11cd5d14969ac789ae4f17ac9d755';
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
function parse(tokens){
 const allowed=new Set(['network-observation','groups','cases','base-file','base-sha','root','out','payload-sha']),args={};
 if(tokens.length%2)throw Error('Arguments must be explicit --name VALUE pairs');
 for(let i=0;i<tokens.length;i+=2){const key=tokens[i].startsWith('--')?tokens[i].slice(2):null;if(!allowed.has(key)||Object.hasOwn(args,key)||!tokens[i+1]||tokens[i+1].startsWith('--'))throw Error('Unknown, duplicate or missing passive argument: '+tokens[i]);args[key]=tokens[i+1];}
 passive.assertSelection(args);
 if(!args['base-file']||!/^[a-f0-9]{64}$/.test(args['base-sha']||'')||!args.root||!args.out)throw Error('Explicit --base-file, --base-sha, --root and --out are required');
 return args;
}
function configure(api,options){
 passive.assertSelection(options);
 if(api.networkObservation!==undefined||typeof api.startSession!=='function')throw Error('Passive caller requires one unconfigured native session interface');
 const start=api.startSession;api.networkObservation=passive.METHOD;
 api.startSession=(...args)=>{if(args.length!==7)throw Error('Passive session caller signature changed');return start(...args,'passive');};
 return api;
}
async function main(){
 const args=parse(process.argv.slice(2)),baseFile=path.resolve(args['base-file']);
 if(args['base-sha']!==BOUND_BASE_SHA)throw Error('C14 entry is bound to a different base; independent review is required before rebinding');
 if(baseFile!==path.join(__dirname,'r0017-windows-proof.cjs'))throw Error('C14 base and its observation dependency must come from this source directory');
 const raw=fs.readFileSync(baseFile);if(hash(raw)!==BOUND_BASE_SHA)throw Error('C14 base collector hash mismatch');
 const text=raw.toString('utf8'),marker='async function main(){';
 if(text.split(marker).length!==2||!text.startsWith('#!/usr/bin/env node\n'))throw Error('C14 exact base extraction anchor changed');
 const prefix=text.slice('#!/usr/bin/env node\n'.length,text.indexOf(marker));
 const exportInterface=`\nmodule.exports={ROOT,OUT,EXPECTED,PUBLIC,runId,result,sha,write,record,seeds,mime,identify,locate,startSession,preload,SNAPSHOT,PROGRESS,checkCommon,screenshot,publicReadback,remainingBudgetMs,operationTimeout,launchBlock,notAttempted,get source(){return source;},get declared(){return declared;}};\n`;
 const loaded={exports:{}};new Function('require','module','exports','__filename','__dirname',prefix+exportInterface)(require,loaded,loaded.exports,baseFile,path.dirname(baseFile));
 const api=configure(loaded.exports,args),files=['r0017-windows-passive.cjs','r0017-passive-network.cjs','r0017-phase2-controls.cjs','r0017-windows-proof.cjs'];
 api.result.loader={schema:'r0017-passive-loader/v1',method:passive.METHOD,baseSha256:BOUND_BASE_SHA,compiledPrefixSha256:hash(prefix),exportInterfaceSha256:hash(exportInterface),baseReuse:'Exact base function source; first-phase main withheld; default enforced path unchanged',sourceFiles:files.map(file=>({file,sha256:hash(fs.readFileSync(path.join(__dirname,file)))}))};
 for(const file of files)fs.copyFileSync(path.join(__dirname,file),path.join(api.OUT,file));fs.writeFileSync(path.join(api.OUT,'base-export-interface.js'),exportInterface);
 try{return await require('./r0017-phase2-controls.cjs').run(api,{groups:args.groups,cases:args.cases});}
 catch(e){api.result.qualification='PARTIAL';api.result.status='PASSIVE_UNHANDLED_COLLECTOR_FAILURE';api.result.error=String(e.stack||e);api.result.finishedUtc=new Date().toISOString();api.write(path.join(api.OUT,'summary.json'),api.result);process.exitCode=1;}
}
module.exports={parse,configure,main,BOUND_BASE_SHA};
if(require.main===module)main().catch(e=>{console.error(String(e.stack||e));process.exitCode=1;});
