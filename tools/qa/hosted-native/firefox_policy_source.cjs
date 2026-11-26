'use strict';
// Source/filesystem and receipt admission only. This module never imports a browser.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const POLICY='{"policies":{"DisableAppUpdate":true}}\n';
const LIMITS=Object.freeze({jsonBytes:8*1024*1024,faults:32,domRows:16,domCells:4,domText:1024,processes:128,packageFiles:4096,censusEntries:4096,readFailures:64});
const BUDGET=Object.freeze({protocol:'firefox-policy-budget/1',dwellMs:60000,childSeconds:270,preflightSeconds:30,killGraceSeconds:4,intakeSeconds:16,entrySeconds:330,
  phases:{sourceAndPolicy:30,launch:45,contextAndPage:20,navigation:20,initialReadback:10,dwell:60,finalReadback:10,cleanup:30,finalCurrentness:15}});
const FILES=Object.freeze(['tools/qa/hosted-native/firefox_policy_source.cjs','tools/qa/hosted-native/firefox_policy_probe.cjs',
  'tools/qa/hosted-native/firefox_policy_controls.cjs','tools/qa/hosted-native/FIREFOX_POLICY.md',
  'tools/qa/r0033_isolation.cjs','tools/qa/v1_net_guard.cjs','tools/qa/hosted-native/node/package.json','tools/qa/hosted-native/node/package-lock.json']);
const CAPS=Object.freeze(['CapInh','CapPrm','CapEff','CapBnd','CapAmb']);
const ROOT=path.resolve(__dirname,'../../..');
const need=(value,message)=>{if(!value)throw Error(message);};
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const equal=(left,right)=>{try{assert.deepEqual(left,right);return true;}catch{return false;}};
function safe(file,kind='file'){
  need(typeof file==='string'&&path.isAbsolute(file)&&path.normalize(file)===file,'absolute normalized path required');
  for(let current=file;;current=path.dirname(current)){
    need(!fs.lstatSync(current).isSymbolicLink(),'symlink in admitted path');if(path.dirname(current)===current)break;
  }
  need(kind==='file'?fs.statSync(file).isFile():fs.statSync(file).isDirectory(),'regular '+kind+' required');return file;
}
function record(file){
  safe(file);const fd=fs.openSync(file,'r'),hash=crypto.createHash('sha256'),buffer=Buffer.allocUnsafe(1024*1024);let bytes=0;
  try{for(;;){const count=fs.readSync(fd,buffer,0,buffer.length,null);if(!count)break;bytes+=count;hash.update(buffer.subarray(0,count));}}
  finally{fs.closeSync(fd);}return {path:file,bytes,sha256:hash.digest('hex')};
}
function read(file){safe(file);need(fs.statSync(file).size<=LIMITS.jsonBytes,'JSON retention/read bound exceeded');return JSON.parse(fs.readFileSync(file,'utf8'));}
function fileTree(folder){
  safe(folder,'directory');const files={};
  function visit(relative){for(const name of fs.readdirSync(path.join(folder,relative)).sort()){
    const item=path.join(relative,name),file=path.join(folder,item),s=fs.lstatSync(file);need(!s.isSymbolicLink(),'symlink in installed package');
    if(s.isDirectory())visit(item);else {need(Object.keys(files).length<LIMITS.packageFiles,'installed package file bound exceeded');const row=record(file);files[item]={bytes:row.bytes,sha256:row.sha256};}
  }}visit('');return files;
}
function write(file,value){
  safe(path.dirname(file),'directory');const bytes=Buffer.from(typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');
  need(bytes.length<=LIMITS.jsonBytes,'JSON retention/write bound exceeded');const fd=fs.openSync(file,'wx',0o600);
  try{let at=0;while(at<bytes.length)at+=fs.writeSync(fd,bytes,at,bytes.length-at);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}return record(file);
}
function packet(expected){
  need(typeof expected==='string'&&/^[0-9a-f]{64}$/.test(expected),'independently expected source manifest digest required');
  const file=path.join(__dirname,'firefox-policy-pins.json'),identity=record(file);need(identity.sha256===expected,'source manifest digest differs');
  const manifest=read(file);need(manifest.protocol==='firefox-policy-source/1'&&manifest.nativeExecution==='NOT_RUN'&&equal(Object.keys(manifest.files||{}).sort(),[...FILES].sort()),'source manifest population differs');
  for(const name of FILES){const actual=record(path.join(ROOT,name));need(equal(manifest.files[name],{bytes:actual.bytes,sha256:actual.sha256}),'source drift: '+name);}
  return {manifest:identity,files:manifest.files};
}
function admitAcquisition(task,actualNode){
  safe(task,'directory');need(task!==path.parse(task).root,'task cannot be filesystem root');
  const runtimePath=path.join(task,'runtime.json'),acquisitionPath=path.join(task,'capture/acquisition-identity.json');
  const runtime=read(runtimePath),a=read(acquisitionPath),modules=path.join(task,'node/node_modules');
  need(a.protocol==='salah-hosted-native-acquisition/1'&&equal(a.runtime,runtime),'acquisition runtime differs');
  need(runtime.node===actualNode&&path.isAbsolute(runtime.node),'invoking Node differs from acquired runtime');
  need(runtime.engine==='firefox'&&runtime.modules===modules&&runtime.playwright===path.join(modules,'playwright')&&runtime.pngjs===path.join(modules,'pngjs'),'acquired runtime dependency paths differ');
  const expected={'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'},packages={};
  need(equal(a.nodePackages,expected),'acquired package versions differ');
  for(const [name,version] of Object.entries(expected)){
    const file=path.join(modules,name,'package.json');need(read(file).version===version,'installed package differs: '+name);
    packages[name]={packageJson:record(file),currentFiles:fileTree(path.join(modules,name))};
  }
  for(const name of ['node/package.json','node/package-lock.json'])need(a.locks?.[name]===record(path.join(__dirname,name)).sha256&&
    a.locks[name]===record(path.join(task,name)).sha256,'acquisition or installed package lock differs');
  const descriptorFile=path.join(modules,'playwright-core/browsers.json'),descriptor=read(descriptorFile);
  need(record(descriptorFile).sha256===a.browserDescriptors?.node?.sha256&&equal(descriptor,a.browserDescriptors.node.body),'acquired browser descriptor differs');
  const entries=descriptor.browsers?.filter(row=>row.name==='firefox');need(entries?.length===1&&typeof entries[0].revision==='string'&&/^\d+$/.test(entries[0].revision),'one managed Firefox descriptor required');
  const relative='node-browsers/firefox-'+entries[0].revision+'/firefox/firefox',executable=path.join(task,relative),binary=record(executable);
  need(equal(a.browserExecutables?.[relative],{size:binary.bytes,sha256:binary.sha256}),'acquired Firefox executable differs');
  const installation=path.dirname(executable),executables={};
  for(const [name,wanted] of Object.entries(a.browserExecutables||{}))if(name.startsWith(path.relative(task,installation)+'/')){
    need(!path.isAbsolute(name)&&!name.split('/').some(p=>!p||p==='.'||p==='..'),'unsafe acquired executable path');
    const file=path.join(task,name),actual=record(file);need(equal(wanted,{size:actual.bytes,sha256:actual.sha256}),'acquired installation executable drift');executables[file]=actual;
  }
  need(Object.keys(executables).length>0&&Object.keys(executables).length<=LIMITS.packageFiles,'acquired executable population bound exceeded');
  return {task,runtime,runtimeRecord:record(runtimePath),acquisition:record(acquisitionPath),packages,descriptor:record(descriptorFile),
    executable,installation,binary,executables};
}
function preparePolicy(acquired,live){
  need(Array.isArray(live)&&live.length===0,'live process already uses the selected Firefox installation');
  need(equal(admitAcquisition(acquired.task,process.execPath),acquired),'acquisition changed before policy preparation');
  const installation=safe(acquired.installation,'directory'),directory=path.join(installation,'distribution'),file=path.join(directory,'policies.json');
  need(fs.statSync(installation).uid===process.getuid(),'Firefox installation is not task-user-owned');
  if(fs.existsSync(directory))safe(directory,'directory');else fs.mkdirSync(directory,{mode:0o700});
  need(!fs.existsSync(file),'per-installation policy already exists; replacement and adoption are refused');
  const policy=write(file,POLICY);
  return {protocol:'firefox-policy-preparation/1',acquisition:structuredClone(acquired.acquisition),runtime:structuredClone(acquired.runtimeRecord),
    executable:structuredClone(acquired.binary),installation,policy,policyValue:{policies:{DisableAppUpdate:true}},exclusiveCreate:true,
    priorPolicyAbsent:true,noLiveInstallationAtCheck:true,installedBefore:'this-diagnostic-launch',historicalFirstStartup:'NOT_ESTABLISHED'};
}
function admitPolicy(acquired,r){
  need(equal(admitAcquisition(acquired.task,process.execPath),acquired),'current policy acquisition differs');
  need(r?.protocol==='firefox-policy-preparation/1'&&equal(r.acquisition,acquired.acquisition)&&equal(r.runtime,acquired.runtimeRecord),'policy acquisition binding differs');
  const file=path.join(acquired.installation,'distribution/policies.json');
  need(equal(r.executable,acquired.binary)&&r.installation===acquired.installation&&equal(r.policy,record(file))&&fs.readFileSync(file,'utf8')===POLICY,'policy file or executable differs');
  need(equal(r.policyValue,{policies:{DisableAppUpdate:true}})&&r.exclusiveCreate===true&&r.priorPolicyAbsent===true&&r.noLiveInstallationAtCheck===true&&
    r.installedBefore==='this-diagnostic-launch'&&r.historicalFirstStartup==='NOT_ESTABLISHED','policy preparation protocol differs');return r;
}
function processInfo(pid){
  const base='/proc/'+pid,status=Object.fromEntries(fs.readFileSync(base+'/status','utf8').split('\n').filter(x=>x.includes(':')).map(x=>{const at=x.indexOf(':');return [x.slice(0,at),x.slice(at+1).trim()];}));
  const stat=fs.readFileSync(base+'/stat','utf8'),fields=stat.slice(stat.lastIndexOf(')')+2).trim().split(/\s+/);
  const ids=name=>(status[name]||'').split(/\s+/).filter(Boolean).map(Number);
  return {pid:Number(pid),ppid:Number(fields[1]),startTicks:fields[19],exe:fs.readlinkSync(base+'/exe'),
    argv:fs.readFileSync(base+'/cmdline','utf8').split('\0').filter(Boolean),uid:ids('Uid')[0],gid:ids('Gid')[0],uids:ids('Uid'),gids:ids('Gid'),groups:ids('Groups'),
    netns:fs.readlinkSync(base+'/ns/net'),pidns:fs.readlinkSync(base+'/ns/pid'),status:Object.fromEntries([...CAPS,'NoNewPrivs'].map(k=>[k,status[k]]))};
}
function noPrivilege(host){
  need(Number.isInteger(host.uid)&&host.uid>0&&Number.isInteger(host.gid)&&host.gid>0,'current nonroot UID/GID required');
  for(const [key,id] of [['uids',host.uid],['gids',host.gid]])need(Array.isArray(host[key])&&host[key].length===4&&host[key].every(x=>Number.isInteger(x)&&x===id),'current real/effective/saved/filesystem identity differs');
  need(Array.isArray(host.groups)&&host.groups.length===0,'supplementary groups retained');
  for(const name of CAPS)need(typeof host.status?.[name]==='string'&&/^0+$/.test(host.status[name]),'retained or malformed capability');
  need(host.status?.NoNewPrivs==='1','no-new-privileges missing');
  need(/^net:\[\d+\]$/.test(host.netns)&&/^pid:\[\d+\]$/.test(host.pidns),'current namespace identity missing');
}
function loopbackRoute(route){
  if(!route||route.dev!=='lo'||route.gateway||typeof route.dst!=='string')return false;
  if(['::1','::1/128','ff00::/8'].includes(route.dst))return true;
  const m=/^(\d+)\.(\d+)\.(\d+)\.(\d+)(?:\/(\d+))?$/.exec(route.dst);
  return !!m&&m.slice(1,5).every(x=>Number(x)<=255)&&Number(m[1])===127&&Number(m[5]??32)>=8&&Number(m[5]??32)<=32;
}
function validateIsolation(r,host){
  need(r?.protocol==='salah-hosted-native-isolation/1'&&r.passed===true&&!r.error,'isolation receipt is absent or unsuccessful');noPrivilege(host);
  need(r.uid===host.uid&&r.netns===host.netns&&/^net:\[\d+\]$/.test(r.outerNetns)&&r.outerNetns!==r.netns,'current isolation identity differs');
  const k=r.kernel;need(k&&k.netns===r.netns&&equal(k.uids,[host.uid,host.uid,host.uid])&&equal(k.gids,[host.gid,host.gid,host.gid])&&equal(k.groups,[]),'isolation kernel identities differ');
  need(Array.isArray(k.links)&&k.links.length===1&&k.links[0].ifname==='lo'&&Array.isArray(k.links[0].flags)&&['LOOPBACK','UP'].every(x=>k.links[0].flags.includes(x)),'isolation loopback interface missing');
  need(Array.isArray(k.routes4)&&Array.isArray(k.routes6)&&[...k.routes4,...k.routes6].every(loopbackRoute),'isolation route differs');
  for(const name of CAPS)need(typeof k.status?.[name]==='string'&&/^0+$/.test(k.status[name]),'isolation kernel capability differs');
  need(k.status?.NoNewPrivs==='1'&&[101,113].includes(k.externalSocketErrno),'isolation kernel refusal missing');
  const p=r.browserProcess,b=r.browserControl;
  need(p&&Number.isInteger(p.returncode)&&p.returncode===0&&p.timedOut===false&&!p.error,'isolation browser process did not complete');
  need(b?.protocol==='salah-hosted-browser-boundary/1'&&b.passed===true&&b.chromiumSandbox===true&&!b.error&&b.uid===r.uid&&b.netns===r.netns&&
    b.postNegativePage==='fresh-page-same-browser'&&Number.isInteger(b.loopbackRequests)&&b.loopbackRequests>=2&&typeof b.externalNavigationError==='string'&&
    /ERR_(NETWORK|ADDRESS)_UNREACHABLE|ERR_INTERNET_DISCONNECTED/.test(b.externalNavigationError)&&Array.isArray(b.processes)&&b.processes.length>0,'isolation browser boundary is incomplete');
  for(const row of b.processes)need(typeof row.exe==='string'&&path.isAbsolute(row.exe)&&/^[0-9a-f]{64}$/.test(row.sha256)&&Array.isArray(row.cmdline)&&row.cmdline.length>0&&
    row.cmdline.every(x=>typeof x==='string'&&!x.startsWith('--no-sandbox')),'isolation browser executable or sandbox receipt differs');return true;
}
function readIsolation(file,host=processInfo(process.pid)){
  try{const body=read(file);validateIsolation(body,host);const folder=path.dirname(file);
    need(equal(read(path.join(folder,'browser.json')),body.browserControl),'isolation browser body differs from retained sibling');
    const streams={};for(const name of ['browser.stdout','browser.stderr'])streams[name]=record(path.join(folder,name));
    return {receipt:record(file),browser:record(path.join(folder,'browser.json')),streams,body,host};
  }catch(error){error.isolation=true;throw error;}
}
function liveInstallation(acquired,io={}){
  const result={protocol:'firefox-process-census/1',hostNs:process.hrtime.bigint().toString(),scanned:0,totalEntries:null,candidates:[],readFailures:[],overflow:false};
  const failure=(pid,phase,error)=>{const row={pid,phase,code:String(error.code||''),message:String(error.message||error).slice(0,1024)};
    if(result.readFailures.length<LIMITS.readFailures)result.readFailures.push(row);else result.overflow=true;return row;};
  let entries;try{entries=(io.entries||(()=>fs.readdirSync('/proc')))().filter(x=>/^\d+$/.test(x)).sort((a,b)=>Number(a)-Number(b));}
  catch(error){result.rootError=failure(null,'directory',error);return result;}
  result.totalEntries=entries.length;if(entries.length>LIMITS.censusEntries)result.overflow=true;
  const identities=new Map();
  for(const item of entries.slice(0,LIMITS.censusEntries)){
    result.scanned++;let exe;
    try{exe=(io.readExe||((pid)=>fs.readlinkSync('/proc/'+pid+'/exe')))(Number(item));}
    catch(error){failure(Number(item),'executable-link',error);continue;}
    if(!exe.startsWith(acquired.installation+'/'))continue;
    if(result.candidates.length>=LIMITS.processes){result.overflow=true;continue;}
    const candidate={pid:Number(item),seenExecutable:exe,status:'INCOMPLETE',process:null};result.candidates.push(candidate);
    try{
      const row=(io.processInfo||processInfo)(Number(item));candidate.process=row;
      need(row.exe===exe&&acquired.executables[row.exe],'live browser binary is outside acquired executable population or changed during read');
      if(!identities.has(row.exe))identities.set(row.exe,record(row.exe));
      need(equal(identities.get(row.exe),acquired.executables[row.exe]),'live browser binary differs from acquisition');
      candidate.process={...row,binary:identities.get(row.exe)};candidate.status='IDENTIFIED';
    }catch(error){candidate.error=failure(Number(item),'process-identity',error);}
  }return result;
}
function censusRows(census){
  need(census?.protocol==='firefox-process-census/1'&&census.overflow===false&&!census.rootError&&Array.isArray(census.candidates)&&Array.isArray(census.readFailures),
    'process census is absent, overflowing or incomplete');
  need(census.readFailures.every(row=>['ENOENT','ESRCH'].includes(row.code)),'process census contains a retained nontransient read failure');
  need(census.candidates.every(row=>row.status==='IDENTIFIED'&&row.process&&row.pid===row.process.pid),'process census has an unidentified installation candidate');
  return census.candidates.map(row=>row.process);
}
function ownedProcesses(census,host,ownerPid){
  const rows=censusRows(census);
  need(rows.length>0,'no acquired Firefox process was observed');const roots=rows.filter(r=>r.ppid===ownerPid);need(roots.length===1,'one direct diagnostic Firefox process required');
  const ids=new Set([ownerPid]);let pending=[...rows];
  while(pending.length){const next=pending.filter(r=>ids.has(r.ppid));need(next.length>0,'unrelated process uses the diagnostic installation');for(const row of next){ids.add(row.pid);pending=pending.filter(x=>x.pid!==row.pid);}}
  noPrivilege(roots[0]);need(roots[0].uid===host.uid&&roots[0].gid===host.gid&&roots[0].netns===host.netns&&roots[0].pidns===host.pidns,'Firefox root process differs from current namespace');
  return {root:roots[0],observed:rows,scope:'observed installation processes and root identity; no exhaustive content-process sandbox claim'};
}
function sameLive(row){try{return processInfo(row.pid).startTicks===row.startTicks;}catch(error){if(['ENOENT','ESRCH'].includes(error.code))return false;throw error;}}
function admitPolicyDom(d){
  need(d?.protocol==='firefox-effective-policy-dom/1'&&d.url==='about:policies'&&d.readyState==='complete'&&d.activeTables===1&&d.errorTables===1&&
    d.overflow===false&&d.inactiveVisible===false&&d.noPoliciesVisible===false,'effective policy DOM contract is incomplete');
  need(d.errorCount===0&&equal(d.errorRows,[]),'effective policy contains error rows');
  need(d.activeCount===1&&equal(d.activeRows,[['DisableAppUpdate','true']]),'effective active policy differs');return true;
}
function readPoliciesDom(){
  // Executed in the actual about:policies document; no file-derived result.
  const active=document.querySelectorAll('#activeContent'),errors=document.querySelectorAll('#errorsContent');let overflow=false;
  const rows=nodes=>{const all=nodes.length===1?[...nodes[0].children].filter(x=>x.tagName==='TR'):[];if(all.length>16)overflow=true;
    return {count:all.length,values:all.slice(0,16).map(row=>{const cells=[...row.children];if(cells.length>4)overflow=true;return cells.slice(0,4).map(cell=>{
      const text=cell.textContent.trim();if(text.length>1024)overflow=true;return text.slice(0,1024);});})};};
  const a=rows(active),e=rows(errors),visible=selector=>[...document.querySelectorAll(selector)].some(element=>{const s=getComputedStyle(element);return !element.hidden&&element.getClientRects().length>0&&s.display!=='none'&&s.visibility!=='hidden';});
  return {protocol:'firefox-effective-policy-dom/1',url:location.href,readyState:document.readyState,activeTables:active.length,errorTables:errors.length,
    activeRows:a.values,errorRows:e.values,activeCount:a.count,errorCount:e.count,inactiveVisible:visible('.inactive-service-message'),
    noPoliciesVisible:visible('.no-specified-policies-message'),overflow};
}
function watch(target,kind,isOpen){
  const state={kind,cleanupRequested:false,closed:false,faults:[],overflow:false};
  const fault=(event,error='')=>{if(state.faults.length<LIMITS.faults)state.faults.push({event,message:String(error?.message??error).slice(0,4096),hostNs:process.hrtime.bigint().toString()});else state.overflow=true;};
  target.on(kind==='browser'?'disconnected':'close',()=>{state.closed=true;if(!state.cleanupRequested)fault('unexpected-'+(kind==='browser'?'disconnect':'close'));});
  if(kind==='page'){target.on('crash',()=>fault('page-crash'));target.on('pageerror',error=>fault('pageerror',error));}
  return {state,fault,requestCleanup(){if(state.closed||!isOpen())fault('closed-before-cleanup-request');state.cleanupRequested=true;}};
}
function resultCode(report){
  if(report.isolationError||report.network?.ok===false)return 86;
  try{
    need(report.protocol==='firefox-policy-observation/1'&&report.phase==='FINALIZED'&&!report.error&&equal(report.errors,[])&&equal(report.retentionErrors,[]),'unfinished observation');
    need(report.engine==='firefox'&&report.nativeProductAcceptance==='NOT_EVALUATED'&&report.originalFailedObservation==='UNCHANGED'&&
      report.refinedCapture==='NOT_OBSERVED'&&report.historicalFirstStartup==='NOT_ESTABLISHED'&&equal(report.budget,BUDGET),'diagnostic scope or budget changed');
    need(report.currentVerified===true&&report.policy&&report.acquired&&report.source&&report.isolation&&report.processes?.root&&report.launch,'missing actual custody');
    admitPolicyDom(report.initial?.dom);admitPolicyDom(report.final?.dom);
    need(report.initial.hostNs!==report.final.hostNs&&BigInt(report.final.hostNs)>BigInt(report.initial.hostNs),'readbacks are not ordered in the driver clock');
    need(report.dwell?.intendedMs===BUDGET.dwellMs&&BigInt(report.dwell.endedNs)-BigInt(report.dwell.startedNs)>=BigInt(BUDGET.dwellMs)*1000000n&&
      BigInt(report.initial.hostNs)<=BigInt(report.dwell.startedNs)&&BigInt(report.dwell.endedNs)<=BigInt(report.final.hostNs),'complete ordered ordinary-clock dwell missing');
    need(report.network?.ok===true&&report.cleanup?.complete===true&&report.cleanup.browserLaunchAttempted===true&&report.cleanup.trackedProcessesStopped===true,'network or cleanup incomplete');
    need(Array.isArray(report.lifecycle)&&equal(report.lifecycle.map(x=>x.kind),['browser','context','page'])&&report.lifecycle.every(x=>x.cleanupRequested===true&&x.closed===true&&x.overflow===false&&equal(x.faults,[])),'lifecycle failure');
    return 0;
  }catch{return 2;}
}
module.exports={POLICY,LIMITS,BUDGET,FILES,ROOT,need,sha,equal,safe,record,read,write,packet,admitAcquisition,preparePolicy,admitPolicy,
  processInfo,noPrivilege,validateIsolation,readIsolation,liveInstallation,censusRows,ownedProcesses,sameLive,admitPolicyDom,readPoliciesDom,watch,resultCode};
