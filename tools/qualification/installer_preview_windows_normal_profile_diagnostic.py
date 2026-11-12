#!/usr/bin/env python3
"""Prospective six-entry profile diagnostic. Never grants qualification credit.

Inherited fixtures/comparators are pinned. Each mode runs genuine -File positive
and no-open entries inside the existing suspended/assigned Job carrier. Complete
default failures and every owned artifact remain present.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, math, os, re, secrets, shutil, stat, struct, sys, tarfile
from pathlib import Path
sys.dont_write_bytecode=True

INPUTS = {'install.ps1': (111249, '07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a'), 'presets/salah-widget.tablissng.json': (1341, '9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f'), 'tests/install-entry-native-composition.py': (56398, 'a453230b3527bdc5a81dcf7279d9af2aad14b32c07756a4700c97eab2ce24646'), 'tests/install-entry-product-support.py': (44780, '70a6ce6193206d757783a3fb4ba2bc32462677d1980818c75a1e60e6bbb56a99'), 'tests/install-entry-composition-support.py': (37442, '4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821'), 'tests/install-entry-coverage-support.py': (14701, '52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a'), 'tests/install-entry-held.ps1': (8262, '742b42edd3828ec98dc25f717fdbacbd3e68ed877139c90e358d43f7c5142ca2'), 'tests/install-entry-input-probe.ps1': (12493, 'f4c871734c72a71c04423a3fcfc1c4c9a2286da7683d09a1eb6ffeefb73c2bf0'), 'tests/install-entry-driver-diagnostic.py': (57115, '08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5'), 'tests/install-entry-diagnostic-shadow.psm1': (5710, '5bc1cb8b88c6c873a295f664304968d7a859c0f322223b8b6bb8b15798f67663'), 'tests/install-preview.ps1': (57909, 'e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916'), 'tests/install-preview-window.ps1': (13117, '05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83'), 'tools/qualification/installer_preview_host_probe.py': (16807, '6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'), 'tools/qualification/installer_preview_windows_full_entry.py': (45698, '652848809fc581452e4bf48e2895786cd3c780e60e0a2c3091e2969d7b856616')}
CASES=('positive','no-open')
PREFIX='r16d-'
MODE_SECONDS=480
OUTER_ROLE='tools/qualification/installer_preview_windows_full_entry.py'
HELPER_ROLE='tools/qualification/installer_preview_host_probe.py'
HARNESS_ROLE='tests/install-entry-native-composition.py'
PRODUCT_ROLE='tests/install-entry-product-support.py'
COMMON_ROLE='tests/install-entry-composition-support.py'

def require(value,reason):
    if not value:raise ValueError(reason)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def modes(host):
    if host=='ps7':return [('default',False,0),('no-gather',True,0)]
    if host=='ps51':return [('warm20',False,20)]
    raise ValueError('Unknown native diagnostic host')

def derive_harness(raw,mode):
    require((len(raw),digest(raw))==INPUTS[HARNESS_ROLE],'Inherited harness bytes differ')
    require(mode in ('default','no-gather','warm20'),'Unknown diagnostic mode')
    text=raw.decode('utf-8')
    def replace(old,new):
        nonlocal text
        require(text.count(old)==1,'Missing/ambiguous exact derivation anchor')
        text=text.replace(old,new,1)
    replace("    startup_env=dict(env, INSTALL_READY_FILE=",
        "    composition.double_inventory(root,support,startup/'full-before-launch.json',LOCKS)\n"
        "    startup_env=dict(env, INSTALL_READY_FILE=")
    replace("startup_env,startup,host_home,ENTRY_TIMEOUT_SECONDS)",
        "startup_env,startup,host_home,ENTRY_TIMEOUT_SECONDS,root)\n"
        "        composition.double_inventory(root,support,startup/'full-after-exit.json',LOCKS)")
    if mode=='warm20':
        replace("Write-Host 'R0016 independent host startup control'\\nexit 0\\n",
            "Write-Host 'R0016 independent host startup control'\\n[Threading.Thread]::Sleep(20000)\\nexit 0\\n")
    if mode=='no-gather':
        replace('    env = composition.owned_environment(os.environ)\n',
            "    env = composition.owned_environment(os.environ)\n    env['COMPlus_MultiCoreJitNoProfileGather']='1'\n")
    # A guard against accidentally replacing an assertion/receiver along with an anchor.
    before,after=ast.parse(raw),ast.parse(text)
    functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body
        if isinstance(n,ast.FunctionDef) and n.name!='_case_impl'}
    require(functions(before)==functions(after),'Derivation changed a receiver/comparator function')
    checks=lambda tree:[ast.dump(n,include_attributes=False) for n in ast.walk(tree)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require']
    require(checks(before)==checks(after),'Derivation changed an existing assertion')
    return text.encode('utf-8')

def delta(before,after):
    def keyed(rows):
        value={(r['role'],r['path']):r for r in rows}
        require(len(value)==len(rows),'Duplicate full-input row')
        return value
    a,b=keyed(before),keyed(after)
    return dict(added=[b[k] for k in sorted(b.keys()-a.keys())],
        removed=[a[k] for k in sorted(a.keys()-b.keys())],
        changed=[dict(key=list(k),fields={f:dict(before=a[k].get(f),after=b[k].get(f))
            for f in sorted(a[k].keys()|b[k].keys()) if a[k].get(f)!=b[k].get(f)})
            for k in sorted(a.keys()&b.keys()) if a[k]!=b[k]])

def load_pinned(path,expected,name):
    raw=Path(path).read_bytes();require((len(raw),digest(raw))==expected,'Pinned dependency differs: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module

def complete_inventory(outer,common,path,case):
    value=outer.read_json(path,case)
    require(value.get('schema')=='r0016-entry-full-input-inventory.v1' and value.get('root')==str(case)
        and value.get('complete') is True and type(value.get('rows')) is list
        and value.get('passes')==[value['rows'],value['rows']],'Incomplete full-input observation')
    common.validate_rows(value['rows']);return value

def original_status(rows,report_status,envelope_status,exit_code):
    require(all(type(r.get('pass_')) is bool for r in rows),'Untyped original result')
    status='PASS' if all(r['pass_'] for r in rows) else 'FAIL'
    require(report_status==envelope_status==status and type(exit_code) is int
        and exit_code==(0 if status=='PASS' else 1),'Original failure/terminal was relabeled')
    return status

def diagnostic_terminal(outer,receipt,command,capture):
    # The existing whole20 receiver requires exit0/PASS. This observational
    # receiver deliberately admits the actual harness exit1/FAIL without changing
    # that value or claiming that any original product assertion passed.
    require(receipt.get('command')==command and type(receipt.get('exit')) is int
        and receipt['exit'] in (0,1),'No complete diagnostic harness terminal')
    for field in ('exitObserved','jobAssignedBeforeResume','jobClosedKillOnClose'):
        require(receipt.get(field) is True,'Missing Job lifecycle fact: '+field)
    require(receipt.get('timedOut') is False and receipt.get('error','missing') is None
        and receipt.get('timeoutSeconds')==MODE_SECONDS,'Diagnostic process timeout/error')
    seconds=receipt.get('elapsedSeconds')
    require(type(seconds) in (int,float) and math.isfinite(seconds) and 0<=seconds<=MODE_SECONDS,
        'Invalid diagnostic elapsed time')
    require(all(type(receipt.get(k)) is int and receipt[k]>0 for k in ('processId','threadId')),
        'Missing actual process/thread identity')
    require(receipt.get('capture')=='direct files; no redirected pipe drain'
        and receipt.get('drain')=='not applicable','Incomplete diagnostic capture protocol')
    for key in ('createdSuspendedUtc','resumedUtc','exitObservedUtc','finishedUtc'):
        require(type(receipt.get(key)) is str and receipt[key],'Missing lifecycle timestamp')
    require(outer.read_json(capture/'observer.process.json',capture)==receipt,'Process receipt differs')
    launch=outer.read_json(capture/'observer.launch.json',capture)
    require(launch.get('command')==command and launch.get('processId')==receipt['processId']
        and launch.get('threadId')==receipt['threadId'] and launch.get('jobAssignedBeforeResume') is True
        and launch.get('jobClosedKillOnClose') is False and launch.get('exit') is None
        and launch.get('error','missing') is None and launch.get('timedOut') is False
        and launch.get('timeoutSeconds')==MODE_SECONDS
        and launch.get('createdSuspendedUtc')==receipt['createdSuspendedUtc'],'Invalid suspended Job launch')
    for stream in ('stdout','stderr'):
        outer.verify_fact(receipt[stream],capture/('observer.'+stream+'.raw'),capture)

def bind_nested_evidence(outer,receipt,case,capture,expected_nonce=None):
    """Bind already-acquired nested bytes and readiness to this owned receipt."""
    for stream in ('stdout','stderr'):
        outer.verify_fact(receipt.get(stream),capture/(stream+'.raw'),case)
    environment=receipt.get('environment');nonce=receipt.get('nonce');pid=receipt.get('pid')
    require(type(environment) is dict and type(nonce) is str and re.fullmatch(r'[0-9a-f]{32}',nonce)
        and type(pid) is int and pid>0,'Invalid nested readiness identity')
    require(environment.get('INSTALL_READY_NONCE')==nonce
        and (expected_nonce is None or expected_nonce==nonce),'Nested readiness nonce differs')
    token=str(pid)+'\t'+nonce
    require(receipt.get('ready') is True and receipt.get('readyToken')==token,'Nested PID/nonce token differs')
    ready=outer.checked_path(environment.get('INSTALL_READY_FILE'),case)
    ack=outer.checked_path(environment.get('INSTALL_PROFILE_ACK'),case)
    require(ready!=ack,'Nested ready/ACK paths are aliased')
    for fact_key,path in (('readyFact',ready),('ackFact',ack)):
        fact=outer.verify_fact(receipt.get(fact_key),path,case)
        raw=path.read_bytes()
        require(len(raw)==fact['bytes'] and digest(raw)==fact['sha256'],'Nested readiness bytes changed during readback')
        require(raw.decode('utf-8-sig')==token,'Nested ready/ACK bytes differ from PID/nonce')
    return nonce

def receive_mode(outer,common,process,command,capture,outputs,control,host,executable,mode,derived_fact):
    diagnostic_terminal(outer,process,command,capture)
    require((capture/'observer.stderr.raw').read_bytes()==b'','Diagnostic controller stderr is nonempty')
    envelope=outer.read_json(capture/'observer.stdout.raw',capture)
    require(envelope.get('schema')=='r0016-native-entry-composition-result.v1'
        and envelope.get('status') in ('PASS','FAIL') and envelope.get('expectedHost')==host
        and envelope.get('commandHost')==str(executable) and envelope.get('nativeWindows') is True,
        'Missing complete diagnostic envelope')
    report_fact=envelope.get('report');require(type(report_fact) is dict,'Missing original report fact')
    report_path=outer.checked_path(report_fact['path'],outputs)
    fixture=report_path.parent
    require(report_path.name=='entry-composition-report.json' and fixture.parent==outputs
        and re.fullmatch(r'e[0-9a-f]{16}',fixture.name) and list(outputs.iterdir())==[fixture]
        and envelope.get('fixture')==str(fixture),'Wrong original fixture/report association')
    outer.verify_fact(report_fact,report_path,outputs);report=outer.read_json(report_path,outputs)
    require(report.get('schema')=='r0016-native-entry-composition.v1' and report.get('nativeWindows') is True
        and report.get('expectedHost')==host and report.get('commandHost')==str(executable)
        and report.get('fixture')==str(fixture) and report.get('selectedHosts')==[host]
        and report.get('selectedScenarios')==list(CASES),'Wrong original report scope')
    require(report.get('sourceUnchanged') is True
        and report.get('sourceBefore')==report.get('source')==INPUTS['install.ps1'][1],
        'Candidate source changed or differs')
    expected=dict(testSha256=derived_fact['sha256'],supportSha256=INPUTS['tests/install-entry-coverage-support.py'][1],
        compositionSha256=INPUTS[PRODUCT_ROLE][1],compositionCoreSha256=INPUTS[COMMON_ROLE][1],
        diagnosticSha256=INPUTS['tests/install-entry-driver-diagnostic.py'][1],
        heldDriverSha256=INPUTS['tests/install-entry-held.ps1'][1],preset=INPUTS['presets/salah-widget.tablissng.json'][1])
    require(all(report.get(k)==v for k,v in expected.items()),'Original report instrument identity differs')
    rows=report.get('results')
    require(type(rows) is list and [r.get('case') for r in rows]==list(CASES),'Incomplete/duplicate diagnostic rows')
    row_status=original_status(rows,report.get('status'),envelope['status'],process['exit'])
    direct=outer.selected_pure_receiver(control/HARNESS_ROLE,'validate_direct_terminal',derived_fact['sha256'])
    collected=[];nonces=[]
    for row in rows:
        scenario=row['case'];case=fixture/('c10' if scenario=='positive' else 'c11')
        observation=row.get('observation');require(type(observation) is dict,'Missing direct observation')
        expected_command=outer.expected_entry_command(executable,control/'install.ps1',scenario)
        require(row.get('host')==host and observation.get('fixture')==str(case)
            and observation.get('command')==expected_command,'Wrong genuine -File source invocation')
        require(type(observation.get('entryExit')) is int and observation['entryExit']==0,'Product entry failed')
        nonce=observation.get('readinessNonce');require(type(nonce) is str and re.fullmatch(r'[0-9a-f]{32}',nonce),'Missing nonce')
        profile=outer.read_json(case/'entry-profile-window/profile-window.json',case)
        warmup=outer.read_json(case/'host-only-control/profile-window.json',case)
        require(observation.get('profileWindow')==profile and observation.get('hostOnlyBaseline')==warmup,
            'Original readiness receipt differs')
        direct(profile,expected_command,60)
        direct(warmup,[str(executable),'-NoProfile','-File',str(case/'host-only-control/host-only.ps1')],60)
        require(warmup['entryExit']==0 and profile['entryExit']==observation['entryExit']
            and warmup['ready'] is True and profile['ready'] is True,'Source-free/direct readiness or exit missing')
        launch=outer.read_json(case/'direct-launch-inputs.json',case)
        require(launch==observation.get('directLaunchInputs') and launch['command']==expected_command,
            'Actual direct launch differs')
        require(launch.get('environment')==profile.get('environment'),'Actual direct launch environment differs')
        nonces.append(bind_nested_evidence(outer,profile,case,case/'entry-profile-window',nonce))
        nonces.append(bind_nested_evidence(outer,warmup,case,case/'host-only-control'))
        for receipt in (warmup,profile):
            env=receipt['environment'];flag={k:v for k,v in env.items() if k.upper()=='COMPLUS_MULTICOREJITNOPROFILEGATHER'}
            require(flag==({'COMPlus_MultiCoreJitNoProfileGather':'1'} if mode=='no-gather' else {}),
                'Actual prelaunch gather variable differs')
        require(warmup['environment']['INSTALL_FIXTURE_NORMAL']=='0','Warmup could exercise normal effect spies')
        body=(case/'host-only-control/host-only.ps1').read_bytes()
        expected_body=b"$ErrorActionPreference='Stop'\nWrite-Host 'R0016 independent host startup control'\n"
        if mode=='warm20':expected_body+=b'[Threading.Thread]::Sleep(20000)\n'
        expected_body+=b'exit 0\n'
        require(body.replace(b'\r\n',b'\n')==expected_body,'Source-free control body differs')
        if mode=='warm20':require(warmup['elapsedSeconds']>=20,'Declared source-free hold did not elapse')
        effect=case/'host-only-control/effects';require(not effect.exists() or not effect.read_bytes(),'Source-free control reached effect spy')
        phases={name:complete_inventory(outer,common,case/path,case) for name,path in [
            ('warmBefore','host-only-control/full-before-launch.json'),('warmReady','host-only-control/full-at-ready.json'),
            ('warmAfter','host-only-control/full-after-exit.json'),('productBefore','direct-full-before-launch.json'),
            ('productReady','entry-profile-window/full-at-ready.json'),('productAfter','direct-full-after-exit.json')]}
        require(phases['warmReady']==warmup.get('fullReady'),'Warmup full-ready receipt differs')
        require(phases['productReady']==profile.get('fullReady'),'Product full-ready receipt differs')
        for field,key in [('fullInputsBefore','productBefore'),('fullInputsAtReady','productReady'),('fullInputsAfter','productAfter')]:
            require(phases[key]==observation.get(field),'Original product inventory differs')
        collected.append(dict(case=scenario,originalResult={k:v for k,v in row.items() if k!='observation'},
            productExit=profile['entryExit'],warmupSeconds=warmup['elapsedSeconds'],
            warmupBeforeReady=delta(phases['warmBefore']['rows'],phases['warmReady']['rows']),
            warmupReadyAfter=delta(phases['warmReady']['rows'],phases['warmAfter']['rows']),
            warmupAfterProductBefore=delta(phases['warmAfter']['rows'],phases['productBefore']['rows']),
            productBeforeReady=delta(phases['productBefore']['rows'],phases['productReady']['rows']),
            productReadyAfter=delta(phases['productReady']['rows'],phases['productAfter']['rows'])))
    require(len(set(nonces))==2*len(rows),'Replayed product or warmup nonce')
    return dict(mode=mode,originalReport=report_fact,originalStatus=row_status,rows=collected,
        classification='DIAGNOSTIC_ONLY',qualificationAccepted=False)

def archive_root(outer,parent,destination):
    roots=list(parent.glob(PREFIX+'*'));require(len(roots)==1,'Exactly one diagnostic root required')
    root=outer.checked_path(roots[0],parent,directory=True)
    require(re.fullmatch(PREFIX+r'[0-9a-f]{16}',root.name),'Wrong diagnostic root constructor')
    destination=Path(destination);require(destination.is_absolute() and destination.parent==parent
        and not destination.exists(),'Unowned/replayed archive destination')
    with tarfile.open(destination,'x:gz',dereference=False) as archive:
        pending=[root]
        while pending:
            path=pending.pop();info=path.lstat();name='installer-evidence'+('' if path==root else '/'+path.relative_to(root).as_posix())
            require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)
                or stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400,'Unsupported evidence type')
            if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                entry=tarfile.TarInfo(name);entry.type=tarfile.SYMTYPE;entry.linkname=os.readlink(path)
                entry.mode=stat.S_IMODE(info.st_mode);entry.mtime=int(info.st_mtime);archive.addfile(entry)
            else:
                archive.add(path,arcname=name,recursive=False)
                if stat.S_ISDIR(info.st_mode):pending.extend(sorted(path.iterdir(),reverse=True))
    return destination

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('ps51','ps766'));parser.add_argument('--powershell',type=Path)
    parser.add_argument('--output-parent',required=True,type=Path);parser.add_argument('--source-commit')
    parser.add_argument('--archive-only',action='store_true');parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if os.name!='nt' or struct.calcsize('P')!=8:parser.error('Native 64-bit Windows required; no child started')
    repo=Path(__file__).resolve().parents[2]
    outer=load_pinned(repo/OUTER_ROLE,INPUTS[OUTER_ROLE],'r16_diagnostic_outer')
    parent=outer.checked_path(args.output_parent,directory=True)
    require(parent.drive.lower()=='c:' and parent==Path(os.environ['USERPROFILE']).resolve(strict=True),'Actual C: profile parent required')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None and args.source_commit is None,'Wrong archive-only arguments')
        print(archive_root(outer,parent,args.archive));return 0
    require(args.host is not None and args.powershell is not None and args.archive is None
        and type(args.source_commit) is str and re.fullmatch(r'[0-9a-f]{40}',args.source_commit),'Exact host/source commit required')
    host='ps7' if args.host=='ps766' else 'ps51';executable=outer.checked_path(args.powershell)
    python=outer.checked_path(Path(sys.executable).resolve());host_fact=outer.file_fact(executable)
    if host=='ps7':require((host_fact['bytes'],host_fact['sha256'])==(301368,outer.PS7_EXE_SHA),'Pinned PS7 executable differs')
    else:require(executable==Path(os.environ['SYSTEMROOT'],'System32/WindowsPowerShell/v1.0/powershell.exe').resolve(strict=True),'Wrong system PS5.1 executable')
    require(not list(parent.glob(PREFIX+'*')),'Diagnostic root already exists; no replay')
    root=parent/(PREFIX+secrets.token_hex(8));require(len(str(root).encode('utf-16-le'))//2<=48,'Diagnostic root too long');root.mkdir()
    result=dict(schema='r0016-normal-profile-diagnostic.v1',status='INCOMPLETE',qualificationAccepted=False,
        sourceCommit=args.source_commit,expectedHost=host,fixture=str(root),modes=[],phases={},
        expectedNormalEntries=2*len(modes(host)),sourceAndInputsUnchanged=False,
        scope='Prospective diagnostic only. Every original result and full state difference remains. Job bounds lifetime, not filesystem/network access.')
    outer.save(root/'diagnostic-result.json',result);fixed=[];exit_status=2;custody_complete=False
    try:
        inherited=root/'inherited';inherited.mkdir();copied={}
        for role,pin in INPUTS.items():
            original=outer.file_fact(repo/role);require((original['bytes'],original['sha256'])==pin,'Inherited input differs: '+role)
            target=inherited/role;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/role,target)
            fact=outer.file_fact(target,root);require((fact['bytes'],fact['sha256'])==pin,'Inherited copy differs')
            copied[role]=fact;fixed.extend([original,fact])
        own=outer.file_fact(Path(__file__).resolve());retained=inherited/'diagnostic-runner.py';shutil.copyfile(own['path'],retained)
        fixed.extend([own,outer.file_fact(retained,root),host_fact,outer.file_fact(python)])
        native_dependencies=[]
        names=['Microsoft.PowerShell.ConsoleHost.dll','System.Management.Automation.dll','coreclr.dll','pwsh.runtimeconfig.json'] if host=='ps7' else ['powershell.exe.config']
        for name in names:
            fact=outer.file_fact(executable.parent/name);native_dependencies.append(fact);fixed.append(fact)
        custody_complete=True
        helper=load_pinned(inherited/HELPER_ROLE,INPUTS[HELPER_ROLE],'r16_diagnostic_job_helper')
        common=load_pinned(inherited/COMMON_ROLE,INPUTS[COMMON_ROLE],'r16_diagnostic_common')
        version=root/'version';version.mkdir();version_state=root/'v';version_env=outer.owned_environment(helper,version_state,executable)
        version_command=[str(executable),'-NoProfile','-NonInteractive','-Command',outer.VERSION_CODE]
        plan=dict(schema='r0016-normal-profile-diagnostic-plan.v1',sourceCommit=args.source_commit,
            host=host_fact,nativeDependencies=native_dependencies,python=outer.file_fact(python),
            inherited=copied,runner=own,modes=[],budget=dict(version=60,eachMode=MODE_SECONDS,
            modeCount=len(modes(host)),maximumNormalEntries=2*len(modes(host))),qualificationAccepted=False,
            version=dict(command=version_command,environment=version_env))
        outer.save(root/'diagnostic-plan.json',plan)
        process=outer.run_phase(helper,version_command,version_env,version_state,version,60)
        result['phases']['version']=process;outer.save(root/'diagnostic-result.json',result)
        outer.validate_terminal(process,version_command,version,60)
        require((version/'observer.stderr.raw').read_bytes()==b'','Version stderr nonempty')
        result['nativeHost']=outer.validate_version((version/'observer.stdout.raw').read_bytes(),host,executable)
        for index,(mode,no_gather,hold) in enumerate(modes(host)):
            mode_root=root/('m'+str(index));mode_root.mkdir();control=mode_root/'control';control.mkdir();launched={}
            for role,pin in INPUTS.items():
                target=control/role;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(inherited/role,target)
                if role==HARNESS_ROLE:target.write_bytes(derive_harness(target.read_bytes(),mode))
                fact=outer.file_fact(target,root);fixed.append(fact)
                if role in outer.INPUTS:launched[role]=fact
            capture=mode_root/'run';capture.mkdir();outputs=mode_root/'f';outputs.mkdir();state=mode_root/'s'
            env=outer.owned_environment(helper,state,executable)
            command=outer.build_command(launched,python,host,executable,outputs)
            for case in CASES:command+=['--scenario',case]
            mode_plan=dict(mode=mode,noGather=no_gather,sourceFreeHoldSeconds=hold,command=command,
                controllerEnvironment=env,childEnvironmentChange={'COMPlus_MultiCoreJitNoProfileGather':'1'} if no_gather else {},
                derivedHarness=launched[HARNESS_ROLE],inheritedHarness=copied[HARNESS_ROLE],launchedInputs=launched,
                timeoutSeconds=MODE_SECONDS)
            plan['modes'].append(mode_plan);outer.save(root/'diagnostic-plan.json',plan)
            for fact in fixed:outer.verify_fact(fact,Path(fact['path']))
            process=outer.run_phase(helper,command,env,state,capture,MODE_SECONDS)
            result['phases'][mode]=process;outer.save(root/'diagnostic-result.json',result)
            result['modes'].append(receive_mode(outer,common,process,command,capture,outputs,control,
                host,executable,mode,launched[HARNESS_ROLE]))
            outer.save(root/'diagnostic-result.json',result)
        result['status']='DIAGNOSTIC_ONLY';exit_status=0
    except Exception as error:result['error']=type(error).__name__+': '+str(error)
    finally:
        try:
            require(custody_complete,'No complete custody established')
            for fact in fixed:outer.verify_fact(fact,Path(fact['path']))
            result['sourceAndInputsUnchanged']=True
        except Exception as error:
            result.update(status='INPUT_CUSTODY_FAILED',custodyError=type(error).__name__+': '+str(error));exit_status=2
        outer.save(root/'diagnostic-result.json',result)
    print(json.dumps(dict(status=result['status'],fixture=str(root),result=outer.file_fact(root/'diagnostic-result.json'),qualificationAccepted=False)))
    return exit_status

if __name__=='__main__':raise SystemExit(main())
