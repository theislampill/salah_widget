// Explicit file and retained-history adapter. Never imports a browser and never
// changes the original trial loop. Inspection happens after the original report.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const here=path.dirname(fileURLToPath(import.meta.url));
const helper=path.resolve(here,'../../r0035/publish_diagnostic.mjs');
const helperSha='d1dad63ccfd123ce8cb8fa4a86f58a73c17004b2a26cc15817f59714e783f45a';
const live='tools/r0035/live_lab.mjs',kind='derived-r0035-publish-decision/1';
const need=(condition,message)=>{if(!condition)throw new Error(message);};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const row=bytes=>({bytes:bytes.length,sha256:sha(bytes)});
function ancestry(file){
  for(let current=file;;current=path.dirname(current)){
    need(!fs.lstatSync(current).isSymbolicLink(),'regular publish source ancestry required');
    if(path.dirname(current)===current)break;
  }
}
function canonical(file){
  need(typeof file==='string'&&path.isAbsolute(file)&&path.normalize(file)===file,
    'literal absolute publish root without aliases required');
  ancestry(file);need(fs.realpathSync(file)===file,'nonaliased publish root required');return file;
}
function read(file){
  ancestry(file);const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{const stat=fs.fstatSync(fd,{bigint:true});need(stat.isFile(),'regular publish input required');
    return {bytes:fs.readFileSync(fd),stat};}finally{fs.closeSync(fd);}
}
const helperInput=read(helper);need(sha(helperInput.bytes)===helperSha,'reviewed publish helper source drift');
const pure=await import(pathToFileURL(helper).href);

export function transformFiles(mode,baseArg,outArg){
  need(mode==='derive'||mode==='check','exact publish transform mode required');
  const base=canonical(baseArg),out=canonical(outArg);
  need(fs.statSync(base).isDirectory()&&fs.statSync(out).isDirectory()
    &&base!==out&&!out.startsWith(base+path.sep)&&!base.startsWith(out+path.sep),
    'separate existing publish source/output roots required');
  const input=read(path.join(base,live)),target=path.join(out,live);ancestry(target);
  const fd=fs.openSync(target,(mode==='derive'?fs.constants.O_RDWR:fs.constants.O_RDONLY)|fs.constants.O_NOFOLLOW);
  try{
    const stat=fs.fstatSync(fd,{bigint:true});need(stat.isFile()&&stat.nlink===1n,'single-link regular publish output required');
    need(![input.stat,helperInput.stat].some(p=>p.dev===stat.dev&&p.ino===stat.ino),
      'publish output aliases protected input inode');
    const actual=fs.readFileSync(fd);
    if(mode==='derive'){
      need(actual.equals(input.bytes),'publish output must begin as exact original bytes');
      const derived=pure.derivePublishDiagnostic(input.bytes);pure.publishDiagnosticIdentity(input.bytes,derived);
      fs.ftruncateSync(fd,0);
      for(let at=0;at<derived.length;){
        const written=fs.writeSync(fd,derived,at,derived.length-at,at);
        need(written>0,'publish output write made no progress');at+=written;
      }
      fs.fsyncSync(fd);
    }
  }finally{fs.closeSync(fd);}
  const derived=read(target).bytes,identity=pure.publishDiagnosticIdentity(input.bytes,derived);
  need(read(path.join(base,live)).bytes.equals(input.bytes)&&read(helper).bytes.equals(helperInput.bytes),
    'protected original or helper changed during publish admission');
  return {protocol:'r0035-publish-file-transform/1',helperSha256:helperSha,identity,files:{[live]:row(derived)}};
}

function object(value){return value!==null&&typeof value==='object'&&!Array.isArray(value);}
function exact(value,keys,label){
  need(object(value)&&Object.keys(value).length===keys.length&&keys.every(k=>Object.hasOwn(value,k)),label);
}
function finite(value){return typeof value==='number'&&Number.isFinite(value)&&value>=0;}
function identity(value){return value===null||typeof value==='string'&&value.length>0;}

export function inspectPublication(publication){
  exact(publication,['start','end','initial','overflow','events'],'exact original publication history required');
  need(finite(publication.start)&&finite(publication.end)&&publication.end>=publication.start,
    'bounded original publication interval required');
  need(publication.overflow===false&&Array.isArray(publication.events)&&publication.events.length<=16384,
    'complete nonoverflow original publication population required');
  exact(publication.initial,['status','tier','identity'],'original initial publication state required');
  need(typeof publication.initial.status==='string'&&identity(publication.initial.identity)
    &&[null,'preview','refined'].includes(publication.initial.tier),'original initial owner fields required');
  let at=publication.start,epoch=0,lastOwner=-1;const owners=[];
  const detail={status:['reason'],withdraw:['reason'],owner:['r0035Publish'],
    publication:['utcMs','ageMs','changed','nonempty','writes','id']};
  for(let index=0;index<publication.events.length;index++){
    const event=publication.events[index];need(object(event)&&Object.hasOwn(detail,event.kind),'known original event kind required');
    exact(event,['at','kind','epoch','tier','identity',...detail[event.kind]],'exact original event/supplement schema required');
    need(finite(event.at)&&event.at>=at&&event.at<=publication.end,'original event chronology differs');at=event.at;
    need(Number.isSafeInteger(event.epoch)&&event.epoch>=epoch,'original event epoch chronology differs');epoch=event.epoch;
    need([null,'preview','refined'].includes(event.tier)&&identity(event.identity),'original event owner identity required');
    if(event.kind==='owner'){
      need(event.epoch>lastOwner&&event.tier!==null&&event.identity!==null,'distinct original owner population required');
      const decision=pure.decodePublishDecision(event.r0035Publish,event.epoch);lastOwner=event.epoch;
      owners.push({eventIndex:index,at:event.at,epoch:event.epoch,tier:event.tier,identity:event.identity,decision});
    }
  }
  return {status:'COMPLETE',eventCount:publication.events.length,ownerCount:owners.length,owners,
    questionStatus:owners.length?'OWNER_DECISIONS_RETAINED':'NO_OWNER_EVENT_OBSERVED',
    interval:{start:publication.start,end:publication.end},clockDomain:'page-performance-now-ms',
    cpuTiming:'NOT_MEASURED',speed:'NOT_ESTABLISHED'};
}

export function inspectReports(reports){
  const labels=['main','unmodified','mitigated'];
  need(Array.isArray(reports)&&reports.length===labels.length,'complete original three-arm reports required');
  const arms=reports.map((body,index)=>{
    need(object(body)&&body.arm===labels[index]&&typeof body.commit==='string'&&body.commit
      &&typeof body.root==='string'&&path.isAbsolute(body.root)&&body.scope===kind&&object(body.trace),
      'ordered original trial source and scope required');
    const binding={arm:body.arm,commit:body.commit,root:body.root,scope:body.scope};
    if(body.arm==='main'){
      need(body.trace.publication===null,'original baseline must have no lab history');
      return {...binding,status:'BASELINE_NO_LAB',ownerCount:0};
    }
    return {...binding,...inspectPublication(body.trace.publication)};
  });
  return {protocol:'r0035-publish-history-intake/1',status:'COMPLETE',arms,
    totalOwners:arms.reduce((n,arm)=>n+arm.ownerCount,0),nativeQualification:'UNCHANGED_ORIGINAL_REPORT_ONLY',
    cpuTiming:'NOT_MEASURED',speed:'NOT_ESTABLISHED',humanAcceptance:'OUTSTANDING'};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const [mode,base,out,...extra]=process.argv.slice(2);let result;
  if(mode==='inspect'){
    need(base===undefined&&out===undefined&&!extra.length,'exact history intake arguments required');
    const raw=fs.readFileSync(0);need(raw.length<=64*1024*1024,'bounded retained history input required');
    result=inspectReports(JSON.parse(raw.toString('utf8')));
  }else{
    need(!extra.length,'exact transform arguments required');result=transformFiles(mode,base,out);
  }
  process.stdout.write(JSON.stringify(result)+'\n');
}
