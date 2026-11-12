#!/usr/bin/env python3
"""NEW outer acquisition for the pinned C2 source-free entry-driver diagnostic.

Only the fixed diagnostic CLI runs. The published Job helper controls process
lifetime; it is not filesystem/network containment or installer qualification.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
import ntpath
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import struct
import sys
import tarfile
import threading
import time
from types import SimpleNamespace

sys.dont_write_bytecode=True
HELPER_SHA='6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
C2_MANIFEST_SHA='5cf40d9285deca5b8e2d2a82e07abc01078dd448e3bfe4f4a629f9355fc8138d'
ROOT_PREFIX='r16-entry-'
VERSION_SECONDS=60
CHILD_SECONDS=60
HELD_CASES=10
DIRECT_CASES=1
CLEANUP_SECONDS=5
LOOPBACK_JOIN_SECONDS=2
FINAL_CAPTURE_SECONDS=31
OUTER_SECONDS=(HELD_CASES+DIRECT_CASES)*(CHILD_SECONDS+CLEANUP_SECONDS)+2*LOOPBACK_JOIN_SECONDS+FINAL_CAPTURE_SECONDS
JSON_LIMIT=64*1024*1024
PS7_EXE_SHA='bfb46af89433268872ddb43d1ca7a3f433452ee91ed356a9786940f90118e285'
INPUTS={
    'install-entry-driver-diagnostic.py':(47331,'e192018d2379792cdd1fd73e566b0d50057600b1d25e70430458fee56bbe9d76'),
    'install-entry-composition-support.py':(37442,'4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821'),
    'install-entry-coverage-support.py':(14701,'52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a'),
    'install-entry-held.ps1':(7729,'a3ccac853a6108a2ed860a66f6e8bd6547efd3cc06c3626283959b3126997ae6'),
    'install-entry-input-probe.ps1':(12493,'f4c871734c72a71c04423a3fcfc1c4c9a2286da7683d09a1eb6ffeefb73c2bf0'),
    'install-entry-diagnostic-shadow.psm1':(5710,'5bc1cb8b88c6c873a295f664304968d7a859c0f322223b8b6bb8b15798f67663'),
    'install-preview.ps1':(57909,'e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916'),
    'install-preview-window.ps1':(13117,'05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83'),
}
CASES=('fallthrough','exit-zero','exit-seventeen','throw','finally-exit-seventeen','parameter-failure',
       'method-write-allow','method-write-deny','loopback-allow','loopback-deny')
VERSION_CODE="[Console]::Write(('{0}|{1}|{2}|{3}|{4}' -f $PSVersionTable.PSVersion,$PSVersionTable.PSEdition,[Environment]::OSVersion.Platform,[Environment]::Is64BitProcess,[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName))"


class Rejected(ValueError):pass


def require(value,reason):
    if not value:raise Rejected(reason)


def utc():return datetime.now(timezone.utc).isoformat()


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf-8')


def checked_path(value,owner=None,directory=False):
    require(type(value) is str or isinstance(value,Path),'Missing evidence path')
    path=Path(value)
    require(path.is_absolute(),'Evidence path is not absolute')
    resolved=path.resolve(strict=True)
    require(str(path)==str(resolved),'Evidence path is not exact/canonical')
    if owner is not None:
        root=Path(owner).resolve(strict=True)
        require(path==root or path.is_relative_to(root),'Evidence path escaped its owned root')
    for part in (path,*path.parents):
        info=part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'Evidence has a link/reparse ancestor')
    mode=path.lstat().st_mode
    require(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode),'Wrong evidence path type')
    return path


def file_fact(value,owner=None):
    path=checked_path(value,owner);before=path.stat()
    require(before.st_size<=JSON_LIMIT,'Evidence exceeds bounded read size')
    raw=path.read_bytes();after=path.stat()
    require((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'Evidence changed while read')
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def verify_fact(value,path,owner=None):
    require(type(value) is dict and set(value)=={'path','bytes','sha256'} and type(value['path']) is str
        and type(value['bytes']) is int and value['bytes']>=0 and type(value['sha256']) is str
        and re.fullmatch(r'[0-9a-f]{64}',value['sha256']),'Malformed exact file fact')
    require(value['path']==str(path) and value==file_fact(path,owner),'File path/size/SHA differs')
    return value


def parse_json(raw):
    require(type(raw) is bytes and len(raw)<=JSON_LIMIT,'JSON exceeds bounded byte input')
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'Duplicate JSON member');result[key]=value
        return result
    def constant(value):raise Rejected('Nonfinite JSON constant: '+value)
    try:value=json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=constant)
    except (UnicodeError,json.JSONDecodeError) as error:raise Rejected('Not one complete UTF-8 JSON document') from error
    require(type(value) is dict,'Expected a JSON object')
    return value


def read_json(path,owner=None):
    path=checked_path(path,owner)
    require(path.stat().st_size<=JSON_LIMIT,'JSON exceeds bounded file size')
    return parse_json(path.read_bytes())


def load_exact(path,digest,name):
    require(file_fact(path)['sha256']==digest,'Pinned Python dependency differs')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_command(launched,python,host,executable,outputs):
    require(set(launched)==set(INPUTS) and host in ('ps51','ps7'),'Wrong fixed diagnostic roles/host')
    return [str(python),'-B',launched['install-entry-driver-diagnostic.py']['path'],
            '--host',host,'--host-executable',str(executable),'--output-root',str(outputs)]


def validate_terminal(process,command,capture,budget):
    require(type(process) is dict and process.get('command')==command,'Outer command differs from exact launch')
    require(type(process.get('exit')) is int and process['exit']==0,'Outer terminal is not integer zero')
    for key in ('exitObserved','jobAssignedBeforeResume','jobClosedKillOnClose'):
        require(process.get(key) is True,'Missing outer lifecycle fact: '+key)
    require(process.get('timedOut') is False and 'error' in process and process['error'] is None,'Outer timeout/error')
    elapsed=process.get('elapsedSeconds')
    require(type(process.get('timeoutSeconds')) is int and process['timeoutSeconds']==budget
        and type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=budget,'Wrong finite outer deadline')
    require(type(process.get('processId')) is int and process['processId']>0
        and type(process.get('threadId')) is int and process['threadId']>0,'Missing actual outer process/thread')
    require(process.get('capture')=='direct files; no redirected pipe drain' and process.get('drain')=='not applicable','Wrong outer capture protocol')
    for key in ('createdSuspendedUtc','resumedUtc','exitObservedUtc','finishedUtc'):
        require(type(process.get(key)) is str and bool(process[key]),'Missing helper lifecycle timestamp')
    require(read_json(capture/'observer.process.json',capture)==process,'Actual helper process receipt differs')
    launch=read_json(capture/'observer.launch.json',capture)
    require(launch.get('command')==command and launch.get('processId')==process['processId']
        and type(launch.get('processId')) is int and launch.get('threadId')==process['threadId']
        and type(launch.get('threadId')) is int and launch.get('createdSuspendedUtc')==process['createdSuspendedUtc']
        and launch.get('jobAssignedBeforeResume') is True and launch.get('jobClosedKillOnClose') is False
        and launch.get('timedOut') is False and launch.get('exit') is None and launch.get('error','missing') is None
        and type(launch.get('timeoutSeconds')) is int and launch['timeoutSeconds']==budget,'Actual suspended/assigned launch receipt differs')
    return [verify_fact(process.get(kind),capture/('observer.'+kind+'.raw'),capture) for kind in ('stdout','stderr')]


def validate_version(raw,host,executable):
    require(type(raw) is bytes,'Version capture is not raw bytes')
    text=raw.decode('utf-8-sig');parts=text.split('|')
    require(len(parts)==5 and parts[2:4]==['Win32NT','True'] and parts[4]==str(executable),'Native platform/64-bit/path differs')
    require((host=='ps7' and parts[:2]==['7.6.6','Core']) or
        (host=='ps51' and re.fullmatch(r'5\.1\.\d+\.\d+',parts[0]) and parts[1]=='Desktop'),'Native version/edition differs')
    return dict(version=parts[0],edition=parts[1],platform=parts[2],is64BitProcess=True,commandHost=parts[4])


def validate_header(value,schema,host,executable):
    require(type(value) is dict and value.get('schema')==schema and value.get('status')=='PASS','Wrong diagnostic schema/status')
    require(value.get('nativeWindows') is True and value.get('expectedHost')==host
        and value.get('commandHost')==str(executable),'Wrong diagnostic native host')
    require(value.get('installerExecuted') is False and value.get('productQualification') is False,'Diagnostic scope changed')


def validate_input_roles(values,launched,fixture,owner):
    require(type(values) is list and len(values)==8 and set(launched)==set(INPUTS),'Exactly eight fixed input roles required')
    names=[row.get('name') if type(row) is dict else None for row in values]
    require(all(type(name) is str for name in names) and len(set(names))==8 and set(names)==set(INPUTS),'Duplicate/missing/unexpected input role')
    retained=checked_path(fixture/'inputs',fixture,directory=True)
    require({path.name for path in retained.iterdir()}==set(INPUTS),'Retained input directory differs')
    facts=[]
    for row in values:
        require(set(row)=={'name','original','retained'},'Wrong input role shape')
        name=row['name'];expected=launched[name];length,digest=INPUTS[name]
        require((expected['bytes'],expected['sha256'])==(length,digest),'Launched input differs from fixed C2 bytes')
        require(row['original']==expected,'Original input was not the actual launched copy')
        facts.append(verify_fact(row['original'],Path(expected['path']),owner))
        fact=verify_fact(row['retained'],retained/name,fixture)
        require((fact['bytes'],fact['sha256'])==(length,digest),'Retained input bytes differ');facts.append(fact)
    return facts


def reconstruct_pair(label,fixture,executable,host,diagnostic):
    case=checked_path(fixture/label,fixture,directory=True)
    direct=checked_path(case/'direct',case,directory=True);held=checked_path(case/'held',case,directory=True)
    control=checked_path(held/'control',held,directory=True);case_control=checked_path(case/'control',case,directory=True)
    association=read_json(case_control/'association.json',case);spec_path=control/'spec.json';spec=read_json(spec_path,case)
    require(association.get('schema')=='r0016-source-free-entry-association.v1' and association.get('directRoot')==str(direct)
        and association.get('heldRoot')==str(held) and association.get('cwd')==str(fixture),'Wrong known case/root/cwd association')
    require(spec.get('schema')=='r0016-entry-held-spec.v1' and spec.get('scope')=='source-free-diagnostic'
        and spec.get('scenario')==label and spec.get('expectedHost')==host and spec.get('host')==str(executable),'Wrong known held spec identity')
    source=case_control/'source-free-body.ps1'
    paths={'source':source,'inputProbe':control/'input-probe.ps1','beforeInputProof':control/'held-before-inputs.json',
        'guardSource':fixture/'control/original-guard-driver.ps1','windowSupport':fixture/'control/original-window-support.ps1',
        'events':control/'events.jsonl','result':control/'result.json',
        'beforeSignal':control/'before.signal','beforeAck':control/'before.ack','afterSignal':control/'after.signal','afterAck':control/'after.ack'}
    for key,path in paths.items():require(spec.get(key)==str(path),'Spec redirects a known case role: '+key)
    require(association.get('source')==spec.get('sourceFact'),'Association source differs from actual spec')
    command=[str(executable),'-NoProfile','-File',str(source),'-PresetUrl','https://example.invalid/preset',
        '-WidgetHash','lat=24.47&lon=39.61&method=4','-InstallSource','github','-DryRun']
    require(association.get('directCommand')==command and association.get('heldCommand')==
        [str(executable),'-NoProfile','-File',str(control/'held-driver.ps1')],'Actual known direct/held constructor arguments differ')
    direct_prepared=read_json(case_control/'direct-prepared.json',case)
    held_prepared=read_json(case_control/'held-prepared.json',case)
    diagnostic.validate_window(direct_prepared,direct,case_control/'direct-prepared.json')
    diagnostic.validate_window(held_prepared,held,case_control/'held-prepared.json')
    diagnostic.c.verify_input_mapping(association.get('entries'),direct_prepared['rows'],held_prepared['rows'])
    return dict(root=held,control=control,env=association.get('heldEnvironment'),spec=spec,specPath=spec_path,
        association=association,directPrepared=direct_prepared,heldPrepared=held_prepared,directRoot=direct,
        caseControl=case_control,inputs=fixture/'inputs')


def validate_report(process,command,capture,outputs,owner,python,executable,host,launched):
    """Read-only receipt association. Imports only exact pinned pure receivers."""
    owner=checked_path(owner,directory=True);capture=checked_path(capture,owner,directory=True)
    outputs=checked_path(outputs,owner,directory=True);python=checked_path(python);executable=checked_path(executable)
    require(set(launched)==set(INPUTS),'Missing fixed launch role')
    for name,value in launched.items():verify_fact(value,owner/'control/tests'/name,owner)
    require(host in ('ps51','ps7') and command==build_command(launched,python,host,executable,outputs),'Wrong exact fixed controller CLI')
    facts=validate_terminal(process,command,capture,OUTER_SECONDS)
    require((capture/'observer.stderr.raw').read_bytes()==b'','Controller stderr is nonempty')
    envelope=read_json(capture/'observer.stdout.raw',owner)
    validate_header(envelope,'r0016-entry-driver-diagnostic-result.v1',host,executable)
    report_fact=envelope.get('report')
    require(type(report_fact) is dict and type(report_fact.get('path')) is str,'Missing full report fact')
    report_path=checked_path(report_fact['path'],outputs);fixture=report_path.parent
    require(report_path.name=='driver-diagnostic.json' and fixture.parent==outputs
        and re.fullmatch(r'r0016-entry-driver-[0-9a-f]{32}',fixture.name),'Wrong owned report/fixture constructor')
    require(list(outputs.iterdir())==[fixture] and envelope.get('fixture')==str(fixture),'Duplicate/replayed output fixture')
    facts.append(verify_fact(report_fact,report_path,outputs));report=read_json(report_path,outputs)
    validate_header(report,'r0016-entry-driver-diagnostic.v1',host,executable)
    require(report.get('fixture')==str(fixture) and report.get('inputCustodyErrors')==[],'Wrong full report fixture/input custody')
    facts.extend(validate_input_roles(report.get('inputs'),launched,fixture,owner))
    verify_fact(report.get('hostExecutableFact'),executable)
    module=verify_fact(report.get('moduleFact'),fixture/'control/shadow-module.psm1',fixture)
    require((module['bytes'],module['sha256'])==INPUTS['install-entry-diagnostic-shadow.psm1'],'Shadow module differs')
    facts.append(module)
    diagnostic=load_exact(Path(launched['install-entry-driver-diagnostic.py']['path']),INPUTS['install-entry-driver-diagnostic.py'][1],'r16_entry_c2_receivers')
    require(tuple(diagnostic.CASES)==CASES and report.get('expectedCases')==list(CASES),'Changed expected case sequence')
    rows=report.get('results')
    require(type(rows) is list and len(rows)==10 and [row.get('case') if type(row) is dict else None for row in rows]==list(CASES),'Missing/duplicated/reordered diagnostic cases')
    core=(fixture/'inputs/install-preview.ps1').read_text(encoding='ascii')
    drivers=re.findall(r"(?m)^\$DriverText=@'\n(.*?)\n'@\s*$",core,re.S)
    helpers=re.findall(r"(?m)^\$EffectHelpers=@\(\n(.*?)\n\)\s*$",core,re.S)
    require(len(drivers)==len(helpers)==1,'Ambiguous recovered guard extraction')
    require((fixture/'control/original-guard-driver.ps1').read_bytes()==drivers[0].encode('ascii')
        and file_fact(fixture/'control/original-window-support.ps1',fixture)['sha256']==INPUTS['install-preview-window.ps1'][1],
        'Exact guard/window data extraction differs')
    pairs={};nonces=[];pids=[]
    for label,row in zip(CASES,rows):
        require(row.get('status')=='PASS' and row.get('installerExecuted') is False,'Control failed or invoked installer')
        pair=reconstruct_pair(label,fixture,executable,host,diagnostic);pairs[label]=pair
        require(pair['spec'].get('effectHelpers')==re.findall(r"'([^']+)'",helpers[0]),'Guard helper inventory differs')
        receipt_path=pair['control']/'held-observation.json';receipt=read_json(receipt_path,fixture)
        require(row.get('observation')==receipt,'Full report replays a different raw held receipt')
        nonces.extend((pair['spec'].get('nonce'),pair['association']['directEnvironment'].get('INSTALL_READY_NONCE')))
        pids.append(receipt.get('pid'))
        loop=None
        if label.startswith('loopback-'):
            value=row.get('loopback');require(type(value) is dict and value.get('address')=='127.0.0.1','Missing owned loopback observation')
            loop=SimpleNamespace(port=value.get('port'),closed=value.get('closed'),accepted=value.get('accepted'))
        regenerated=diagnostic.evaluate(label,pair,receipt,loop)
        require(row==regenerated,'Case report differs from the exact C2 receiver over retained raw files')
        facts.extend(file_fact(path,fixture) for path in (pair['specPath'],pair['caseControl']/'association.json',receipt_path))
    require(all(type(value) is str and re.fullmatch(r'[0-9a-f]{32}',value) for value in nonces)
        and len(set(nonces))==20,'Missing/replayed direct or held case nonce')
    first=pairs['fallthrough'];direct_path=first['directRoot']/'control/direct-neutral.json'
    direct=read_json(direct_path,fixture)
    require(report.get('directNeutral')==direct,'Full report replays another genuine direct receipt')
    diagnostic.validate_direct_neutral(direct,first);pids.insert(0,direct['pid'])
    comparison=diagnostic.neutral_comparison(first,direct,rows[0]['observation'])
    comparison=json.loads(json.dumps(comparison,allow_nan=False))
    comparison_path=first['caseControl']/'neutral-comparison.json'
    require(report.get('neutralComparison')==comparison==read_json(comparison_path,fixture)
        and comparison.get('actualChildReadContextEquivalent') is True and comparison.get('entireHeldBeforeEqualsAfter') is True,
        'Full neutral read/physical comparison differs or failed')
    facts.extend((file_fact(direct_path,fixture),file_fact(comparison_path,fixture)))
    return dict(report=report_fact,fixture=str(fixture),expectedHost=host,commandHost=str(executable),
        cases=list(CASES),explicitDiagnosticExecutions=11,observedPids=pids,custodyFiles=facts,
        installerExecuted=False,productQualification=False,
        scope='Exact C2 source-free diagnostic receipts only. No installer inputs or product acceptance.')


def owned_environment(helper,state,host):
    env=helper.environment_for(state,host,os.environ,False)
    env['POWERSHELL_UPDATECHECK']='Off'  # Same pre-start setting as the reviewed source-free routes.
    require(not any(key.upper()=='COMPLUS_MULTICOREJITNOPROFILEGATHER' for key in env),'Default gather behavior changed')
    helper.prepare_environment(env)
    return env


def run_phase(helper,command,env,state,capture,budget):
    helper.save_required_snapshot(state,capture/'state.before.json')
    finished=threading.Event();outcome={}
    def worker():
        try:outcome['process']=helper.run_observer(command,env,capture,budget)
        except BaseException as error:outcome['error']=error
        finally:finished.set()
    thread=threading.Thread(target=worker,daemon=True);started=time.monotonic();thread.start()
    while not finished.wait(30):
        print(json.dumps(dict(event='phase-running',elapsedSeconds=round(time.monotonic()-started,3),timeoutSeconds=budget)),flush=True)
    thread.join()
    helper.save_required_snapshot(state,capture/'state.after.json')
    if 'error' in outcome:raise outcome['error']
    return outcome['process']


def archive_owned_root(parent,destination):
    """Retain every owned member; links are metadata, never followed."""
    parent=checked_path(parent,directory=True);roots=list(parent.glob(ROOT_PREFIX+'*'))
    require(len(roots)==1 and re.fullmatch(ROOT_PREFIX+r'[0-9a-f]{16}',roots[0].name),'Exactly one fresh owned route root required')
    root=checked_path(roots[0],parent,directory=True);destination=Path(destination)
    require(destination.is_absolute() and destination.parent==parent and not destination.exists(),'Replayed or unowned archive destination')
    with tarfile.open(destination,'x:gz',dereference=False) as archive:
        pending=[root]
        while pending:
            path=pending.pop();info=path.lstat()
            name='installer-evidence'+('' if path==root else '/'+path.relative_to(root).as_posix())
            if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                entry=tarfile.TarInfo(name);entry.type=tarfile.SYMTYPE;entry.linkname=os.readlink(path)
                entry.mode=stat.S_IMODE(info.st_mode);entry.mtime=int(info.st_mtime);archive.addfile(entry)
            else:
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),'Unsupported special evidence member')
                archive.add(path,arcname=name,recursive=False)
                if stat.S_ISDIR(info.st_mode):pending.extend(sorted(path.iterdir(),reverse=True))
    return str(destination)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('ps51','ps766'))
    parser.add_argument('--powershell',type=Path)
    parser.add_argument('--output-parent',required=True,type=Path)
    parser.add_argument('--source-commit')
    parser.add_argument('--archive-only',action='store_true')
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if os.name!='nt' or struct.calcsize('P')!=8:
        parser.error('Native 64-bit Windows required; no selected PowerShell started')
    parent=checked_path(args.output_parent,directory=True)
    require(parent.drive.lower()=='c:' and parent==Path(os.environ['USERPROFILE']).resolve(strict=True),'Actual C: profile parent required')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None and args.source_commit is None,'Wrong archive-only arguments')
        print(archive_owned_root(parent,args.archive));return 0
    require(args.host is not None and args.powershell is not None and args.archive is None
        and type(args.source_commit) is str and re.fullmatch(r'[0-9a-f]{40}',args.source_commit),'Exact host and source commit required')
    host='ps7' if args.host=='ps766' else 'ps51'
    executable=checked_path(args.powershell);python=checked_path(Path(sys.executable).resolve())
    if host=='ps7':
        fact=file_fact(executable);require((fact['bytes'],fact['sha256'])==(301368,PS7_EXE_SHA),'Exact 7.6.6 x64 executable differs')
    else:
        require(executable==Path(os.environ['SYSTEMROOT'],'System32/WindowsPowerShell/v1.0/powershell.exe').resolve(strict=True),'Selected PS51 is not the actual system executable')
    require(not list(parent.glob(ROOT_PREFIX+'*')),'Owned route root already present; no replay or reuse')
    root=parent/(ROOT_PREFIX+secrets.token_hex(8))
    require(len(str(root).encode('utf-16-le'))//2<=64,'Owned route root is not short enough')
    root.mkdir()
    result=dict(schema='r0016-source-free-entry-driver-acquisition.v1',status='ACQUISITION_INCOMPLETE',fixture=str(root),
        sourceCommit=args.source_commit,expectedHost=host,diagnosticAccepted=False,installerExecuted=False,productQualification=False,
        explicitDiagnosticExecutionsMaximum=11,coldVersionExecutionsMaximum=1,selectedPowerShellExecutionsMaximum=12,
        phases={},sourceAndInputsUnchanged=False,independentHardContainment='NOT_ACQUIRED')
    save(root/'route-result.json',result)
    fixed=[];copied={};status=2
    try:
        source=Path(__file__).resolve();repo=source.parents[2];control=root/'control';control.mkdir()
        roles={'tests/'+name:digest for name,(_,digest) in INPUTS.items()}
        roles['tools/qualification/installer_preview_host_probe.py']=HELPER_SHA
        roles['tools/qualification/installer_preview_windows_entry_driver.py']=file_fact(source)['sha256']
        originals=[]
        for role,digest in roles.items():
            fact=file_fact(repo/role);require(fact['sha256']==digest,'Pinned launch role differs: '+role)
            target=control/role;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fact['path'],target)
            retained=file_fact(target,root);require((retained['bytes'],retained['sha256'])==(fact['bytes'],fact['sha256']),'Launch copy differs')
            copied[role]=retained;originals.append(fact)
        fixed=originals+list(copied.values())+[file_fact(executable),file_fact(python)]
        helper=load_exact(copied['tools/qualification/installer_preview_host_probe.py']['path'],HELPER_SHA,'r16_entry_published_host_helper')
        launched={name:copied['tests/'+name] for name in INPUTS}
        version=root/'version';version.mkdir();capture=root/'run';capture.mkdir();outputs=root/'f';outputs.mkdir()
        version_state=root/'v';state=root/'s'
        version_env=owned_environment(helper,version_state,executable);environment=owned_environment(helper,state,executable)
        version_command=[str(executable),'-NoProfile','-NonInteractive','-Command',VERSION_CODE]
        command=build_command(launched,python,host,executable,outputs)
        plan=dict(schema='r0016-source-free-entry-driver-plan.v1',sourceCommit=args.source_commit,preparedUtc=utc(),root=str(root),
            c2ManifestSha256=C2_MANIFEST_SHA,expectedHost=host,host=file_fact(executable),python=file_fact(python),originals=originals,
            copiedInputs=copied,launchedInputs=launched,noGatherOverride=False,
            version=dict(command=version_command,environment=version_env,timeoutSeconds=VERSION_SECONDS),
            diagnostic=dict(command=command,environment=environment,timeoutSeconds=OUTER_SECONDS,outputs=str(outputs)),
            budget=dict(held=10,direct=1,childSeconds=60,cleanupSecondsEach=5,loopbackJoins=2,loopbackJoinSeconds=2,finalCaptureSeconds=31,total=750),
            scope='Source-free only. Suspended creation/Job assignment/resume/kill-on-close bounds lifetime; no filesystem/network sandbox.')
        save(root/'plan.json',plan)
        process=run_phase(helper,version_command,version_env,version_state,version,VERSION_SECONDS)
        result['phases']['version']=process;save(root/'route-result.json',result)
        validate_terminal(process,version_command,version,VERSION_SECONDS)
        require((version/'observer.stderr.raw').read_bytes()==b'','Cold version stderr is nonempty')
        result['nativeHost']=validate_version((version/'observer.stdout.raw').read_bytes(),host,executable)
        for fact in fixed:verify_fact(fact,Path(fact['path']))
        process=run_phase(helper,command,environment,state,capture,OUTER_SECONDS)
        result['phases']['diagnostic']=process;save(root/'route-result.json',result)
        result['association']=validate_report(process,command,capture,outputs,root,python,executable,host,launched)
        result.update(status='ACQUIRED_SOURCE_FREE_ENTRY_DRIVER_ONLY',diagnosticAccepted=True);status=0
    except Exception as error:
        result.update(status='ACQUISITION_OR_DIAGNOSTIC_NOT_ADMITTED',error=type(error).__name__+': '+str(error))
    finally:
        try:
            require(bool(fixed),'Complete launch custody was not established')
            for fact in fixed:verify_fact(fact,Path(fact['path']))
            result['sourceAndInputsUnchanged']=True
        except Exception as error:
            result.update(status='INPUT_CUSTODY_FAILED',diagnosticAccepted=False,sourceAndInputsUnchanged=False,
                custodyError=type(error).__name__+': '+str(error));status=2
        save(root/'route-result.json',result)
    print(json.dumps(dict(status=result['status'],fixture=str(root),report=file_fact(root/'route-result.json',root),
        diagnosticAccepted=result['diagnosticAccepted'],installerExecuted=False,productQualification=False),indent=2))
    return status


if __name__=='__main__':raise SystemExit(main())
