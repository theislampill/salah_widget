#!/usr/bin/env node
'use strict';
// One native, driver-only fault control. No browser or product assertion credit.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),Module=require('node:module');
const basePath=path.join(__dirname,'r0017-windows-proof.cjs');
const base=fs.readFileSync(basePath,'utf8');
const expectedBase='dfbd7c58c63afb716499694e1f6da239c16fb64ace070663e893e7fafbe7e517';
const actualBase=crypto.createHash('sha256').update(base).digest('hex');
if(actualBase!==expectedBase)throw Error('Cleanup probe base differs from its independently reviewed binding');
const entry='main().catch(e=>{';
if(base.split(entry).length!==2)throw Error('Cleanup probe requires one exact base entry point');
const binding={baseSha256:actualBase,probeSha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),probeFile:__filename};
async function nativePreSessionProbe(){
 const row={name:'controlled-initial-inventory-failure',status:'STARTED',executionStarted:false,qualification:'PARTIAL',checks:{},primaryOutcome:null};
 result.schema='r0017-native-driver-cleanup-probe/v1';
 result.scope='One controlled initial inventory exception through actual startSession and cleanup on Windows; zero browser/application execution';
 result.pending=['All R0017 browser and product acceptance remains outside this driver-only control'];
 result.probeBinding=PROBE_BINDING;result.plannedCases=[{name:row.name,kind:'driver-only-fault-control'}];result.plannedCount=1;result.cases=[row];
 let injected=0,caught=null,unexpectedSession=null;
 const nativeProcessTree=processTree;
 try{
  identify();
  if(process.platform!=='win32')throw Error('Native Windows required for the retained-handle guarantee');
  const dir=path.join(OUT,row.name);fs.mkdirSync(dir,{recursive:true});
  fs.copyFileSync(PROBE_BINDING.probeFile,path.join(OUT,'probe-loader.cjs'));
  // Restore the real OS query before throwing. startSession's real catch/finally
  // must then clean the acquired driver using actual Windows queries and exit.
  processTree=(...args)=>{
   processTree=nativeProcessTree;injected++;
   const e=Error('Controlled initial process inventory failure before session creation');
   e.code='R0017_CONTROLLED_INITIAL_INVENTORY_FAILURE';throw e;
  };
  try{unexpectedSession=await startSession('chromium','no-preference',{width:1100,height:900},1,row,dir,'http://127.0.0.1/');}
  catch(e){caught=e;row.primaryOutcome={status:'CAPABILITY_OR_SETUP_ERROR',code:e.code??null,error:String(e.stack||e),stage:'setup'};}
  finally{processTree=nativeProcessTree;if(unexpectedSession)await unexpectedSession.close();}
  row.checks.exactControlledSetupFailure=injected===1&&caught?.code==='R0017_CONTROLLED_INITIAL_INVENTORY_FAILURE';
  row.checks.noBrowserSession=unexpectedSession===null&&row.capabilities===undefined&&row.browserPid==null&&row.executionStarted===false;
  row.checks.realDriverAcquired=Number.isInteger(row.driverPid)&&row.driverPid>0&&!!row.installed?.driverSha256;
  const c=row.cleanup;
  row.checks.realDriverObservedBeforeTermination=c?.queries?.find(q=>q.stage==='before-delete')?.observed?.some(p=>p.ProcessId===row.driverPid)===true;
  row.checks.originalHandleExitObserved=c?.directDriverTermination?.killRequested===true&&c.directDriverTermination.killReturned===true&&c.directDriverTermination.exitObserved===true&&c.directDriverTermination.exitWithinBound===true;
  row.checks.noUnknownPidTermination=c?.kills?.length===0&&c?.ownedProcesses?.length===0;
  row.checks.actualProcessAndProfileCleanup=c?.verifiedExited===true&&c.scopeKnown===true&&c.ok===true&&c.remaining?.length===0&&c.unresolvedObserved?.length===0&&c.profileCleanup?.absent===true;
  row.status=Object.values(row.checks).every(v=>v===true)?'DRIVER_FAULT_CONTROL_PASSED':'DRIVER_FAULT_CONTROL_FAILED';
  result.status=row.status;process.exitCode=row.status==='DRIVER_FAULT_CONTROL_PASSED'?0:1;
 }catch(e){row.status='DRIVER_FAULT_CONTROL_ERROR';row.error=String(e.stack||e);result.status=row.status;process.exitCode=1;}
 finally{
  processTree=nativeProcessTree;row.injectedFailureCount=injected;row.finishedUtc=new Date().toISOString();
  result.finishedUtc=row.finishedUtc;result.recordedCount=1;result.executedCount=0;result.nativeDriverAcquired=Number.isInteger(row.driverPid);
  write(path.join(OUT,'summary.json'),result);
 }
}
const suffix='\nconst PROBE_BINDING='+JSON.stringify(binding)+';\n('+nativePreSessionProbe.toString()+')().catch(e=>{result.status="UNHANDLED_DRIVER_PROBE_ERROR";result.error=String(e.stack||e);write(path.join(OUT,"summary.json"),result);process.exitCode=1;});\n';
const compiled=base.slice(0,base.indexOf(entry))+suffix;
const child=new Module(basePath,module);child.filename=basePath;child.paths=Module._nodeModulePaths(path.dirname(basePath));child._compile(compiled,basePath);
