#!/usr/bin/env node
'use strict';
/* Thin one-off loader. The root must supply the exact independently admitted
 * phase-1 collector SHA. Its hashbang and automatic main are withheld; native-driver,
 * storage, screenshot, source and protocol implementations are reused verbatim.
 * No source file is edited, and the phase-1 matrix is not re-executed here.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const REVIEWED_BASE_SHA='c095924a71b4358677ff0d2bdf8630b9fdb11cd5d14969ac789ae4f17ac9d755';
const argv={};for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i]?.startsWith('--')||!process.argv[i+1])throw Error('Arguments must be --name VALUE pairs');argv[process.argv[i].slice(2)]=process.argv[i+1];}
if(!argv['base-file']||!/^[a-f0-9]{64}$/.test(argv['base-sha']||''))throw Error('Explicit reviewed --base-file and --base-sha are required');
if(argv['base-sha']!==REVIEWED_BASE_SHA)throw Error('Phase-2 source is bound to a different reviewed base; re-review this loader before rebinding');
const baseFile=path.resolve(argv['base-file']),raw=fs.readFileSync(baseFile),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
if(hash(raw)!==argv['base-sha'])throw Error('Reviewed base collector hash mismatch');
const text=raw.toString('utf8'),marker='async function main(){';if(text.split(marker).length!==2)throw Error('Base main extraction anchor changed');
if(!text.startsWith('#!/usr/bin/env node\n'))throw Error('Base hashbang preamble changed');
const prefix=text.slice(0,text.indexOf(marker)).slice('#!/usr/bin/env node\n'.length);
const exportsSource=`\nmodule.exports={ROOT,OUT,EXPECTED,PUBLIC,runId,result,sha,write,record,seeds,mime,identify,locate,startSession,preload,SNAPSHOT,PROGRESS,checkCommon,screenshot,publicReadback,remainingBudgetMs,operationTimeout,launchBlock,notAttempted,
 get source(){return source;},get declared(){return declared;}};\n`;
const localModule={exports:{}};new Function('require','module','exports','__filename','__dirname',prefix+exportsSource)(require,localModule,localModule.exports,baseFile,path.dirname(baseFile));
const api=localModule.exports;
api.result.loader={sourceSha256:hash(fs.readFileSync(__filename)),baseFile:path.basename(baseFile),baseSha256:argv['base-sha'],baseReuse:'Exact function source before the sole async main declaration; leading hashbang omitted for Function syntax; no first-phase main or file mutation',compiledPrefixSha256:hash(prefix),moduleSha256:hash(fs.readFileSync(path.join(__dirname,'r0017-phase2-controls.cjs')))};
fs.copyFileSync(__filename,path.join(api.OUT,'phase2-loader.cjs'));
fs.copyFileSync(path.join(__dirname,'r0017-phase2-controls.cjs'),path.join(api.OUT,'phase2-controls.cjs'));
fs.writeFileSync(path.join(api.OUT,'base-export-interface.js'),exportsSource);
require('./r0017-phase2-controls.cjs').run(api,{groups:argv.groups||'current,public,calendar-diagnostics',cases:argv.cases}).catch(e=>{api.result.qualification='PARTIAL';api.result.status='PHASE2_UNHANDLED_COLLECTOR_FAILURE';api.result.error=String(e.stack||e);api.result.finishedUtc=new Date().toISOString();api.write(path.join(api.OUT,'summary.json'),api.result);process.exitCode=1;});
