#!/usr/bin/env python3
"""NEW source-free native diagnostic for the exact typed entry driver and probe.

No installer/source argument exists. Only fixed owned synthetic script bodies
are executed. This is separate from the product matrix and grants no product
acceptance. A reviewed Windows launcher must own process/fixture containment.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


HERE = Path(__file__).resolve().parent
c = load('entry_diagnostic_common', HERE / 'install-entry-composition-support.py')
s = load('entry_diagnostic_inventory', HERE / 'install-entry-coverage-support.py')
CASES = ('fallthrough', 'exit-zero', 'exit-seventeen', 'throw', 'finally-exit-seventeen',
         'parameter-failure', 'method-write-allow', 'method-write-deny', 'loopback-allow', 'loopback-deny')
EXPECTED = {'fallthrough': ('fallthrough', 0, None), 'exit-zero': ('exit-code-observed', 0, 0),
    'exit-seventeen': ('exit-code-observed', 17, 17), 'throw': ('terminating-exception', 1, None),
    'finally-exit-seventeen': ('exit-code-observed', 17, 17), 'parameter-failure': ('terminating-exception', 1, None)}


def source_body(label):
    allowed = "[ValidateSet('only-permitted-control-value')]" if label == 'parameter-failure' else "[ValidateSet('ask','github','store')]"
    prefix = ("param([string]$PresetUrl,[string]$WidgetHash," + allowed +
        "[string]$InstallSource='github',[switch]$DryRun,[switch]$NoOpen)\n" +
        "function Invoke-R0016DormantEffect { [IO.File]::WriteAllText($env:R0016_CONTROL_PROBE,'must never run') }\n" +
        "Write-Host 'R0016 source-free body entered'\n")
    suffix = {'fallthrough': "Write-Host 'R0016 neutral marker'\n",
              'exit-zero': 'exit 0\n', 'exit-seventeen': 'exit 17\n',
              'throw': "throw 'R0016 synthetic throw'\n",
              'finally-exit-seventeen': "try { Write-Host 'R0016 synthetic try' } finally { exit 17 }\n",
              'parameter-failure': "throw 'Parameter control unexpectedly entered the body'\n"}
    if label.startswith('method-write-'):
        body = "[IO.File]::WriteAllText($env:R0016_CONTROL_PROBE,'R0016 owned method control')\nWrite-Host 'R0016 effect returned'\nexit 0\n"
    elif label.startswith('loopback-'):
        body = "$client=New-Object Net.Sockets.TcpClient\ntry { $client.Connect('127.0.0.1',[int]$env:R0016_CONTROL_PORT) } finally { $client.Close() }\nWrite-Host 'R0016 effect returned'\nexit 0\n"
    else:
        body = suffix[label]
    return (prefix + body).encode('ascii')


def finish_prepared_clone(direct, held, control, frozen_direct):
    """Restore only planned held directory mtimes, before any child can start."""
    receipt_path = control / 'directory-preparation.json'
    receipt = dict(schema='r0016-entry-directory-preparation.v1', complete=False,
        scope='owned clone preparation only; no diagnostic child started',
        snapshots={'directBeforeClone': c.fact(control / 'direct-before-clone.json')},
        plan=[], operations=[], errors=[])
    left = right = None
    def failure(phase, error):
        receipt['errors'].append(dict(phase=phase, type=type(error).__name__, message=str(error)))
    def observed(path):
        item = path.lstat()
        for component in [path] + list(path.parents):
            info = component.lstat()
            c.require(stat.S_ISDIR(info.st_mode) and not component.is_symlink()
                and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'Directory preparation refuses links/reparse or non-directories')
            if component == held:
                break
        else:
            raise AssertionError('Directory preparation target escaped held root')
        return dict(mode=item.st_mode, device=item.st_dev, inode=item.st_ino,
            uid=item.st_uid, gid=item.st_gid, mtimeNs=item.st_mtime_ns,
            ctimeNs=item.st_ctime_ns, atimeNs=item.st_atime_ns,
            attributes=getattr(item, 'st_file_attributes', None))
    try:
        left = c.double_inventory(direct, s, control / 'direct-prepared.json')
        receipt['snapshots']['directPrepared'] = c.fact(control / 'direct-prepared.json')
        c.require(left['rows'] == frozen_direct['rows'], 'Direct inputs changed during clone construction')
        before = c.double_inventory(held, s, control / 'held-before-directory-restoration.json')
        receipt['snapshots']['heldBeforeRestoration'] = c.fact(control / 'held-before-directory-restoration.json')
        source, copied = c.validate_rows(left['rows']), c.validate_rows(before['rows'])
        c.require(source.keys() == copied.keys(), 'Prepared clone names differ before restoration')
        for key in sorted(source):
            original, clone = source[key], copied[key]
            for field in c.ROW_FIELDS - c.CLONE_FIELDS:
                if field == 'mtimeNs' and original['kind'] == clone['kind'] == 'directory':
                    continue  # This field is restored below, then compared without exception.
                c.require(original[field] == clone[field], 'Prepared clone differs beyond directory mtime: %s/%s:%s' % (*key, field))
            if original['kind'] == 'directory' and original['mtimeNs'] != clone['mtimeNs']:
                target = held / c.ROLE_PATHS[key[0]] / key[1]
                receipt['plan'].append(dict(role=key[0], path=key[1], target=str(target), direct=original, heldBefore=clone))
        receipt['plan'].sort(key=lambda row: (-len(Path(row['target']).parts), row['role'], row['path']))
        c.save(receipt_path, receipt)
        for planned in receipt['plan']:
            target = Path(planned['target']); prior = observed(target)
            c.require(all(value == planned['heldBefore'][field] for field, value in prior.items() if field != 'atimeNs'),
                'Held directory became stale before metadata restoration')
            operation = dict(role=planned['role'], path=planned['path'], target=str(target), before=prior,
                requestedMtimeNs=planned['direct']['mtimeNs'], preservedAtimeNs=prior['atimeNs'], status='ATTEMPTED')
            receipt['operations'].append(operation); c.save(receipt_path, receipt)
            # Python 3.12 Windows lacks utime(follow_symlinks=False). These are
            # freshly checked directories in the private, unlaunched held clone.
            os.utime(target, ns=(prior['atimeNs'], planned['direct']['mtimeNs']))
            operation.update(after=observed(target), status='RETURNED')
            c.save(receipt_path, receipt)
    except BaseException as error:
        failure('plan-or-restore', error)
    finally:
        for name, root, filename in [('directAfter', direct, 'direct-after-directory-restoration.json'),
                                      ('heldAfter', held, 'held-prepared.json')]:
            try:
                snapshot = c.double_inventory(root, s, control / filename)
                receipt['snapshots'][name] = c.fact(control / filename)
                if name == 'directAfter':
                    c.require(snapshot['rows'] == frozen_direct['rows'], 'Frozen direct inputs changed during preparation')
                    left = snapshot
                else:
                    right = snapshot
            except BaseException as error:
                failure(name, error)
        if not receipt['errors']:
            try:
                c.map_inputs(left['rows'], right['rows'])  # Original complete strict comparison.
            except BaseException as error:
                failure('complete-input-association', error)
        receipt['complete'] = not receipt['errors']
        c.save(receipt_path, receipt)
    c.require(receipt['complete'], 'Prepared directory restoration failed: ' + json.dumps(receipt['errors']))
    return left, right


def make_pair(root, label, host_name, host, inputs, module_bytes, guard, window, helpers):
    case = root / label
    case.mkdir()
    direct, held, control = case / 'direct', case / 'held', case / 'control'
    control.mkdir(); direct.mkdir()
    for relative in ('subject/temp', 'subject/local/Google/Chrome/User Data/Default',
        'subject/roam/Mozilla/Firefox/Profiles/fixture profile', 'subject/pf', 'subject/pf86',
        'host-home', 'modules/Microsoft.PowerShell.Utility', 'control'):
        (direct / relative).mkdir(parents=True, exist_ok=True)
    (direct / 'subject/roam/Mozilla/Firefox/Profiles/fixture profile/extensions.json').write_bytes(b'{"addons":[]}\n')
    (direct / 'host-home/existing-profile-sentinel.bin').write_bytes(b'owned source-free sentinel\n')
    (direct / 'fixture.zip').write_bytes(b'inert source-free archive input; never extracted\n')
    (direct / 'canonical-preset.json').write_bytes(b'{"sourceFreeDiagnostic":true}\n')
    module = direct / 'modules/Microsoft.PowerShell.Utility'
    (module / 'Microsoft.PowerShell.Utility.psm1').write_bytes(module_bytes)
    (module / 'Microsoft.PowerShell.Utility.psd1').write_text("@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='b02389c7-c88e-40c9-a1c1-5c8217d2d593';FunctionsToExport=@('Write-Host','New-Item','Remove-Item','Invoke-RestMethod','Invoke-WebRequest','Expand-Archive','Set-Clipboard','Start-Process','Read-Host');CmdletsToExport='*';AliasesToExport=@()}\n", encoding='ascii')
    shutil.copy2(inputs / 'install-entry-input-probe.ps1', direct / 'control/input-probe.ps1')
    frozen_direct = c.double_inventory(direct, s, control / 'direct-before-clone.json')
    shutil.copytree(direct, held, copy_function=shutil.copy2)
    source = control / 'source-free-body.ps1'
    source.write_bytes(source_body(label))
    native_modules = str(Path(host).parent / 'Modules')
    env = c.owned_environment(os.environ)
    for key, part in [('TEMP','temp'),('TMP','temp'),('LOCALAPPDATA','local'),('APPDATA','roam'),('ProgramFiles','pf'),('ProgramFiles(x86)','pf86')]:
        env[key] = str(direct / 'subject' / part)
    env.update(HOME=str(direct/'host-home'),USERPROFILE=str(direct/'host-home'),
        PSModulePath=str(direct/'modules')+';'+native_modules,PSModuleAnalysisCachePath=str(direct/'analysis-cache'),
        INSTALL_NATIVE_UTILITY=str(Path(native_modules)/'Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1'),
        INSTALL_READY_FILE=str(direct/'ready'),INSTALL_PROFILE_ACK=str(direct/'profile-ack'),
        INSTALL_EFFECT_LOG=str(direct/'effects'),INSTALL_SUBJECT_ROOT=str(direct/'subject'),
        INSTALL_BOOTSTRAP_LOG=str(direct/'bootstrap-phases.txt'),INSTALL_READY_NONCE=secrets.token_hex(16),
        INSTALL_FIXTURE_NORMAL='0',INSTALL_ASSET_ZIP=str(direct/'fixture.zip'),INSTALL_PRESET_FIXTURE=str(direct/'canonical-preset.json'),
        INSTALL_FIXTURE_PF=str(direct/'subject/pf'),INSTALL_FIXTURE_PF86=str(direct/'subject/pf86'),
        SALAH_INSTALL_SOURCE='github',SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4',
        R0016_INPUT_PROBE=str(direct/'control/input-probe.ps1'),R0016_MODULE_INPUT_PROOF=str(direct/'control/module-inputs.json'),
        R0016_INPUT_PHASE='direct-pre-discovery',R0016_ENTRY_SOURCE=str(source),R0016_ENTRY_SOURCE_SHA=c.fact(source)['sha256'],
        R0016_EXPECTED_HOST=host_name,R0016_CONTROL_PROBE=str(control/'owned-method-probe.bin'),R0016_CONTROL_PORT='0')
    command = [host,'-NoProfile','-File',str(source),'-PresetUrl','https://example.invalid/preset',
               '-WidgetHash',env['SALAH_WIDGET_HASH'],'-InstallSource','github','-DryRun']
    nonce = secrets.token_hex(16)
    held_env = c.mapped_environment(env, direct, held, nonce)
    held_control = held / 'control'
    driver = held_control / 'held-driver.ps1'
    shutil.copy2(inputs/'install-entry-held.ps1',driver)
    probe = held_control/'input-probe.ps1'
    spec = dict(schema='r0016-entry-held-spec.v1',scenario=label,scope='source-free-diagnostic',
        expectedHost=host_name,host=host,guardMode='allow' if label.endswith('-allow') else 'deny',
        nonce=nonce,source=str(source),sourceFact=c.fact(source),driverFact=c.fact(driver),
        guardSource=str(guard),guardFact=c.fact(guard),windowSupport=str(window),windowFact=c.fact(window),
        inputProbe=str(probe),probeFact=c.fact(probe),beforeInputProof=str(held_control/'held-before-inputs.json'),
        effectHelpers=helpers,parameters=c.direct_parameters(command,host,source),
        events=str(held_control/'events.jsonl'),result=str(held_control/'result.json'),
        beforeSignal=str(held_control/'before.signal'),beforeAck=str(held_control/'before.ack'),
        afterSignal=str(held_control/'after.signal'),afterAck=str(held_control/'after.ack'))
    spec_path = held_control/'spec.json';c.save(spec_path,spec)
    held_env['R0016_COMPOSITION_SPEC']=str(spec_path)
    left,right=finish_prepared_clone(direct,held,control,frozen_direct)
    association=dict(schema='r0016-source-free-entry-association.v1',directRoot=str(direct),heldRoot=str(held),
        source=c.fact(source),sourceInventory=s.profile_snapshot(source),directCommand=command,
        heldCommand=[host,'-NoProfile','-File',str(driver)],parameters=spec['parameters'],cwd=str(root),
        directEnvironment=env,heldEnvironment=held_env,entries=c.map_inputs(left['rows'],right['rows']))
    c.require(not Path(env['R0016_CONTROL_PROBE']).exists(),'Owned control probe is already occupied')
    association['directoryPreparation']=c.fact(control/'directory-preparation.json')
    association['ownedControlProbeBefore']=dict(path=env['R0016_CONTROL_PROBE'],exists=False)
    c.save(control/'association.json',association)
    return dict(root=held,control=held_control,env=held_env,spec=spec,specPath=spec_path,
        association=association,directPrepared=left,heldPrepared=right,directRoot=direct,caseControl=control,
        inputs=inputs)


def run_direct_neutral(pair):
    association=pair['association'];root=pair['directRoot'];control=root/'control';env=dict(association['directEnvironment'])
    receipt=dict(schema='r0016-source-free-direct-neutral.v1',command=association['directCommand'],cwd=association['cwd'],
        nonce=env['INSTALL_READY_NONCE'],environment=env,timeoutSeconds=60,timedOut=False,error=None,
        exit=None,exitObserved=False,capture='direct files; no redirected pipe drain',ready=None)
    process=None;failure=None;started=time.monotonic()
    try:
        receipt['prelaunch']=c.double_inventory(root,s,control/'full-before-launch.json')
        with (control/'stdout.raw').open('wb') as stdout,(control/'stderr.raw').open('wb') as stderr:
            process=subprocess.Popen(association['directCommand'],cwd=association['cwd'],env=env,
                stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
            receipt['pid']=process.pid
            while True:
                elapsed=time.monotonic()-started
                if elapsed>=60:receipt['timedOut']=True;raise TimeoutError('Direct neutral terminal observation exceeded 60 seconds')
                terminal=process.poll()
                if terminal is not None:receipt.update(exit=terminal,exitObserved=True,elapsedSeconds=elapsed);break
                ready=Path(env['INSTALL_READY_FILE']);ack=Path(env['INSTALL_PROFILE_ACK'])
                if receipt['ready'] is None and ready.exists():
                    token=str(process.pid)+'\t'+env['INSTALL_READY_NONCE']
                    c.require(ready.read_text(encoding='utf-8-sig')==token,'Direct neutral ready PID/nonce mismatch')
                    receipt['ready']=c.double_inventory(root,s,control/'full-at-ready.json')
                    c.require(process.poll() is None and time.monotonic()-started<60,'Direct child exited during ready observation')
                    ack.write_text(token,encoding='utf-8')
                    receipt.update(readyToken=token,readyFact=c.fact(ready),ackFact=c.fact(ack),readyAcknowledged=True)
                time.sleep(0.02)
        receipt['stdout'],receipt['stderr']=c.fact(control/'stdout.raw'),c.fact(control/'stderr.raw')
        receipt['postexit']=c.double_inventory(root,s,control/'full-after-exit.json')
        c.require(type(receipt['exit']) is int and receipt['exit']==0 and receipt['readyAcknowledged'] is True,'Direct neutral did not complete its genuine File entry')
        c.require(b'R0016 neutral marker' in (control/'stdout.raw').read_bytes(),'Direct neutral body did not run')
        proof_path=Path(env['R0016_MODULE_INPUT_PROOF'])
        receipt['inputProofFact']=c.fact(proof_path);receipt['inputProof']=c.complete_json(proof_path.read_bytes())
        validate_probe(receipt['inputProof'],pair,'direct-pre-discovery',process.pid,env['INSTALL_READY_NONCE'])
    except BaseException as error:
        failure=error;receipt['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        cleanup=c.finish_owned_acquisition(process,{},root,control,s,receipt,failure,
                                            receipt_path=control/'direct-neutral.json')
        if cleanup is not None and failure is None:raise cleanup
    validate_direct_neutral(receipt,pair)
    return receipt


def validate_direct_neutral(receipt,pair):
    association=pair['association'];root=pair['directRoot'];control=root/'control';env=association['directEnvironment']
    c.require(receipt.get('schema')=='r0016-source-free-direct-neutral.v1'
        and receipt.get('command')==association['directCommand'] and receipt.get('cwd')==association['cwd']
        and receipt.get('environment')==env and receipt.get('nonce')==env['INSTALL_READY_NONCE'],'Wrong genuine direct neutral entry')
    c.require(type(receipt.get('pid')) is int and receipt['pid']>0 and type(receipt.get('exit')) is int
        and receipt['exit']==0 and receipt.get('exitObserved') is True and receipt.get('timedOut') is False
        and receipt.get('error') is None and type(receipt.get('elapsedSeconds')) in (int,float)
        and 0<=receipt['elapsedSeconds']<60 and receipt.get('timeoutSeconds')==60,'Incomplete direct neutral terminal receipt')
    token=str(receipt['pid'])+'\t'+env['INSTALL_READY_NONCE']
    c.require(receipt.get('readyAcknowledged') is True and receipt.get('readyToken')==token,'Missing genuine direct readiness hold')
    for variable,field in (('INSTALL_READY_FILE','readyFact'),('INSTALL_PROFILE_ACK','ackFact')):
        path=Path(env[variable])
        c.require(path.read_bytes()==token.encode('utf-8') and receipt.get(field)==c.fact(path),'Unbound genuine direct gate')
    for phase,filename in (('prelaunch','full-before-launch.json'),('ready','full-at-ready.json'),('postexit','full-after-exit.json')):
        validate_window(receipt.get(phase),root,control/filename)
    c.require(receipt['prelaunch']['rows']==pair['directPrepared']['rows'],'Neutral direct inputs changed after preparation')
    cleanup=receipt.get('cleanup',{})
    c.require(cleanup.get('processStarted') is True and cleanup.get('terminalObserved') is True and type(cleanup.get('terminalExit')) is int
        and cleanup['terminalExit']==0 and cleanup.get('receiptWriteAttempted') is True
        and 'receiptWriteError' not in cleanup and cleanup.get('steps')
        and all(row.get('completed') is True and row.get('error') is None for row in cleanup['steps']),'Incomplete genuine direct cleanup')
    c.require({'poll-owned-process','wait-owned-process','capture-owned-stdout','capture-owned-stderr'}
        <=set(row.get('step') for row in cleanup['steps']),'Missing independent direct owned cleanup steps')
    c.require(receipt.get('capture')=='direct files; no redirected pipe drain'
        and receipt.get('captureCompletion')=='closed-after-observed-exit','Direct capture lacks its exact protocol or terminal confirmation')
    for field in ('stdout','stderr'):c.require(receipt.get(field)==c.fact(control/(field+'.raw')),'Unbound direct closed capture')
    c.require((control/'stdout.raw').read_bytes().splitlines()==[b'R0016 source-free body entered',b'R0016 neutral marker']
        and (control/'stderr.raw').read_bytes()==b'','Unexpected genuine direct neutral output')
    proof_path=Path(env['R0016_MODULE_INPUT_PROOF'])
    c.require(receipt.get('inputProofFact')==c.fact(proof_path)
        and receipt.get('inputProof')==c.complete_json(proof_path.read_bytes()),'Unbound genuine direct input proof')
    validate_probe(receipt['inputProof'],pair,'direct-pre-discovery',receipt['pid'],env['INSTALL_READY_NONCE'])


def validate_host(value,spec):
    c.require(value.get('nativeWindows') is True and value.get('commandHost')==spec['host']
        and value.get('expectedHost')==spec['expectedHost'],'Wrong actual native host')
    if spec['expectedHost']=='ps51':
        c.require(value.get('hostEdition')=='Desktop' and type(value.get('hostVersion')) is str
            and re.fullmatch(r'5\.1(?:\.\d+){0,2}',value['hostVersion']),'Wrong native Windows PowerShell version')
    else:
        c.require(spec['expectedHost']=='ps7' and value.get('hostEdition')=='Core'
            and value.get('hostVersion')=='7.6.6','Wrong native PowerShell version')


def diagnostic_queries(root):
    """Independent complete expected query sequence for this fixed fixture only."""
    subject=root/'subject';rows=[]
    def path_query(identifier,path,exists):
        rows.append(dict(id=identifier,operation='Test-Path',path=str(path),success=True,exists=exists,error=None))
    configs=(('chrome','local','Google/Chrome/User Data','Google/Chrome/Application/chrome.exe',('pf','pf86','local')),
        ('edge','local','Microsoft/Edge/User Data','Microsoft/Edge/Application/msedge.exe',('pf86','pf','local')),
        ('brave','local','BraveSoftware/Brave-Browser/User Data','BraveSoftware/Brave-Browser/Application/brave.exe',('pf','pf86','local')),
        ('chromium','local','Chromium/User Data','Chromium/Application/chrome.exe',('pf','pf86','local')),
        ('firefox','roam','Mozilla/Firefox/Profiles','Mozilla Firefox/firefox.exe',('pf','pf86','local')),
        ('librewolf','roam','LibreWolf/Profiles','LibreWolf/librewolf.exe',('pf','pf86','local')))
    for key,location,data_relative,executable,order in configs:
        for index,base in enumerate(order):path_query(key+'/exe/'+str(index),subject/base/executable,False)
        data=subject/location/data_relative;present=key in ('chrome','firefox')
        path_query(key+'/user-data',data,present)
        if not present:continue
        name='Default' if key=='chrome' else 'fixture profile';profile=data/name
        rows.append(dict(id=key+'/profiles',operation='enumerate-directories',path=str(data),
            entries=[dict(name=name,path=str(profile),kind='directory',attributes=getattr(profile.stat(),'st_file_attributes',16))],
            success=True,errors=[],sourceErrorAction='SilentlyContinue'))
        prefix=key+'/profile/0'
        if key=='chrome':
            for extension in ('dlaogejjiafeobgofajdlkkhjlignalk','hipekcciheckooncpjeljhnekcoolahp'):
                path_query(prefix+'/extension/'+extension,profile/'Extensions'/extension,False)
            path_query(prefix+'/preferences',profile/'Preferences',False)
        else:
            metadata=profile/'extensions.json';path_query(prefix+'/extensions-json',metadata,True)
            raw=b'{"addons":[]}\n'
            c.require(metadata.read_bytes()==raw,'Diagnostic metadata input changed')
            rows.append(dict(id=prefix+'/extensions-read',operation='metadata-read',path=str(metadata),mode='strict-utf8',
                success=True,bytes=c.fact(metadata),text=dict(type='System.String',utf8Bytes=len(raw),sha256=c.sha(raw)),
                error=None,nativeJsonParseSucceeded=True,nativeJsonParseError=None))
    return rows


def record_probe_file_binding(value,label,journal_path,journal,reason='Unbound actual read module/assembly file'):
    """Bind raw spelling to one stable, canonically resolved native file."""
    row=dict(label=label,childFact=value,parentFact=None,matches=False,
             differingFields=[],differences={},nativeFileIdentity=None,error=None)
    failure=None
    def observed(path):
        c.require(path.is_absolute(),'Native file identity requires an absolute path')
        for component in [path]+list(path.parents):
            info=component.lstat()
            c.require(not component.is_symlink() and not (getattr(info,'st_file_attributes',0)&0x400),
                'Native file identity refuses links/reparse ancestors')
        info=path.lstat()
        c.require(stat.S_ISREG(info.st_mode) and type(info.st_dev) is int
            and type(info.st_ino) is int and info.st_ino>0,'Native file identity requires an identifiable regular file')
        return dict(device=info.st_dev,inode=info.st_ino,mode=info.st_mode,bytes=info.st_size,
            mtimeNs=info.st_mtime_ns,ctimeNs=info.st_ctime_ns,
            attributes=getattr(info,'st_file_attributes',None),links=info.st_nlink)
    try:
        c.require(type(value) is dict and set(value)=={'path','bytes','sha256'}
            and type(value['path']) is str and type(value['bytes']) is int and value['bytes']>=0
            and type(value['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}',value['sha256']),reason)
        raw=Path(value['path'])
        identity=dict(rawPath=value['path'],canonicalPath=None,observations={},
            resolutionMatches=False,sameFile=False,stable=False,contentMatches=False)
        row['nativeFileIdentity']=identity
        identity['observations']['rawBefore']=observed(raw)
        parent=c.fact(raw)
        row['parentFact']=parent
        row['differingFields']=sorted(key for key in set(value)|set(parent)
                                    if key not in value or key not in parent or value[key]!=parent[key])
        row['differences']={key:dict(childPresent=key in value,parentPresent=key in parent,
                                   child=value.get(key),parent=parent.get(key)) for key in row['differingFields']}
        canonical=Path(parent['path'])
        identity['canonicalPath']=parent['path']
        identity['resolvedRawPath']=str(raw.resolve(strict=True))
        identity['resolvedCanonicalPath']=str(canonical.resolve(strict=True))
        identity['resolutionMatches']=identity['resolvedRawPath']==identity['resolvedCanonicalPath']==parent['path']
        identity['observations']['canonicalBefore']=observed(canonical)
        identity['rawReadbackFact']=c.fact(raw)
        identity['canonicalReadbackFact']=c.fact(canonical)
        identity['observations']['rawAfter']=observed(raw)
        identity['observations']['canonicalAfter']=observed(canonical)
        observations=list(identity['observations'].values())
        identity['sameFile']=all((item['device'],item['inode'])==
            (observations[0]['device'],observations[0]['inode']) for item in observations)
        identity['stable']=all(item==observations[0] for item in observations)
        identity['contentMatches']=identity['rawReadbackFact']==identity['canonicalReadbackFact']==parent \
            and all(value[key]==parent[key] for key in ('bytes','sha256'))
        row['matches']=all(identity[key] is True for key in ('resolutionMatches','sameFile','stable','contentMatches'))
        c.require(row['matches'],reason)
    except Exception as error:
        failure=error
        row['error']=dict(type=type(error).__name__,message=str(error))
    journal['comparisons'].append(row)
    try:c.save(journal_path,journal)
    except Exception as error:
        if failure is not None:
            raise RuntimeError(type(failure).__name__+': '+str(failure)+'; file-binding evidence save failed: '+type(error).__name__+': '+str(error)) from failure
        raise
    if failure is not None:raise failure


def validate_probe(proof,pair,phase,pid,nonce):
    spec=pair['spec']
    c.require(proof.get('schema')=='r0016-entry-child-input-proof.v1' and proof.get('complete') is True and proof.get('error') is None,'Incomplete actual-child read proof')
    c.require(type(proof.get('pid')) is int and proof['pid']==pid and proof.get('nonce')==nonce and proof.get('phase')==phase,'Wrong input proof process/phase')
    validate_host(proof,spec)
    c.require(proof.get('source')==spec['sourceFact'],'Wrong source-free body input')
    direct=phase=='direct-pre-discovery'
    root=pair['directRoot'] if direct else pair['root']
    environment=pair['association']['directEnvironment'] if direct else pair['env']
    c.require(proof.get('probe')==c.fact(root/'control/input-probe.ps1'),'Wrong input probe path/bytes')
    c.require(proof.get('subject')==str(root/'subject'),'Wrong observed subject root')
    names=('SALAH_WIDGET_PRESET_URL','SALAH_WIDGET_HASH','SALAH_INSTALL_SOURCE','TABLISSNG_REPO',
        'LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)','HOME','USERPROFILE','TEMP','TMP','PSModulePath','PSModuleAnalysisCachePath')
    actual=proof.get('environment')
    c.require(type(actual) is list and [row.get('name') for row in actual]==list(names),'Missing/duplicated/reordered actual environment proof')
    folded={key.upper():value for key,value in environment.items()}
    for row in actual:
        key=row['name'].upper();present=key in folded
        c.require(type(row.get('present')) is bool and row['present']==present,'Child environment presence mismatch')
        if key=='PSMODULEPATH':
            # Native startup can expand the module search string. Retain that
            # full string; the actual resolved command files are verified below.
            # Product association must separately compare both actual strings.
            c.require(type(row.get('value')) is str and str(root/'modules') in row['value'].split(';')
                and str(Path(spec['host']).parent/'Modules') in row['value'].split(';'),'Owned/native module search roots missing')
        else:c.require(row.get('value')==(folded.get(key) if present else None),'Wrong actual child environment value: '+row['name'])
    c.require([row['name'] for row in proof.get('commands',[])]==['Test-Path','Get-ChildItem','Get-Content','ConvertFrom-Json'],'Incomplete actual command bindings')
    file_bindings=dict(schema='r0016-entry-probe-file-bindings.v1',phase=phase,pid=pid,nonce=nonce,
                       sourceFact=spec['sourceFact'],probeFact=proof.get('probe'),comparisons=[])
    binding_path=root/'control'/('read-file-bindings-'+phase+'.json')
    for row,kind in zip(proof['commands'],('TestPathCommand','GetChildItemCommand','GetContentCommand','ConvertFromJsonCommand')):
        c.require(row.get('commandType')=='Cmdlet' and row.get('implementingType')=='Microsoft.PowerShell.Commands.'+kind,'Wrong actual read cmdlet type')
        c.require(row.get('source')==('Microsoft.PowerShell.Utility' if row['name']=='ConvertFrom-Json' else 'Microsoft.PowerShell.Management'),'Wrong read cmdlet module')
        c.require(all(type(row.get(key)) is str and row[key] for key in ('definition','moduleVersion')),'Missing actual read cmdlet definition/version')
        for field in ('module','assembly'):
            value=row.get(field)
            record_probe_file_binding(value,row['name']+'/'+field,binding_path,file_bindings)
    provider=proof.get('provider',{})
    c.require(provider.get('name')=='FileSystem' and provider.get('implementingType')=='Microsoft.PowerShell.Commands.FileSystemProvider'
        and type(provider.get('capabilities')) is str and provider['capabilities'],'Wrong actual FileSystem provider')
    record_probe_file_binding(provider['assembly'],'FileSystem/provider-assembly',binding_path,file_bindings,'Unbound native provider assembly')
    c.require(type(proof.get('identitySid')) is str and re.fullmatch(r'S-1-[0-9-]+',proof['identitySid'])
        and type(proof.get('defaultCodePage')) is int and proof['defaultCodePage']>0
        and all(type(proof.get(key)) is str for key in ('culture','uiCulture')),'Missing actual identity/decoding context')
    c.require(proof.get('queries')==diagnostic_queries(root),'Incomplete/reordered/different actual diagnostic reads')


def validate_window(value,root,path):
    c.require(type(value) is dict and value.get('schema')=='r0016-entry-full-input-inventory.v1'
        and value.get('root')==str(root) and value.get('complete') is True
        and value.get('passes')==[value.get('rows'),value.get('rows')],'Incomplete full raw inventory')
    c.validate_rows(value['rows'])
    c.require(c.complete_json(path.read_bytes())==value,'Replayed raw inventory payload')


def validate_gate(receipt,spec,phase):
    token=str(receipt['pid'])+'\t'+spec['nonce']+'\t'+phase+'-invocation'
    c.require(receipt.get(phase+'Acknowledged') is True and receipt.get(phase+'Token')==token,'Wrong held phase PID/nonce/ACK')
    for kind in ('Signal','Ack'):
        path=Path(spec[phase+kind])
        c.require(path.read_bytes()==token.encode('utf-8') and receipt.get(phase+kind+'Fact')==c.fact(path),'Unbound held signal/ACK bytes')


def validate_original_ready(receipt,pair):
    spec=pair['spec']
    c.require(receipt.get('originalReadyAcknowledged') is True and receipt.get('originalReadyToken')==str(receipt['pid'])+'\t'+spec['nonce'],'Original Utility ready/ACK was not independently completed')
    for variable,field in (('INSTALL_READY_FILE','originalReadyFact'),('INSTALL_PROFILE_ACK','originalAckFact')):
        path=Path(pair['env'][variable])
        c.require(path.read_bytes()==receipt['originalReadyToken'].encode('utf-8') and c.fact(path)==receipt.get(field),'Unbound original Utility ready/ACK bytes')


def validate_terminal(receipt,pair):
    spec=pair['spec']
    association=pair['association'];control=pair['control']
    c.require(receipt.get('schema')=='r0016-entry-held-observation.v1','Wrong held receipt schema')
    expected_command=[spec['host'],'-NoProfile','-File',str(control/'held-driver.ps1')]
    c.require(receipt.get('command')==association['heldCommand']==expected_command and receipt.get('nonce')==spec['nonce'],'Wrong exact held launch')
    c.require(receipt.get('cwd')==association['cwd'] and receipt.get('environment')==pair['env']==association['heldEnvironment'],'Wrong held working directory/environment')
    mapped=c.mapped_environment(association['directEnvironment'],pair['directRoot'],pair['root'],spec['nonce'])
    mapped['R0016_COMPOSITION_SPEC']=str(pair['specPath'])
    c.require(pair['env']==mapped,'Held launch no longer matches the complete constructor mapping')
    c.require(type(receipt.get('pid')) is int and receipt['pid']>0 and type(receipt.get('exit')) is int and receipt.get('exitObserved') is True and receipt.get('timedOut') is False,'Missing finite terminal observation')
    elapsed=receipt.get('elapsedSeconds')
    c.require(type(elapsed) in (int,float) and 0<=elapsed<60 and receipt.get('timeoutSeconds')==60,'Late or invalid terminal time')
    validate_original_ready(receipt,pair)
    cleanup=receipt.get('cleanup',{})
    steps=cleanup.get('steps',[])
    c.require(cleanup.get('processStarted') is True and cleanup.get('terminalObserved') is True
        and type(cleanup.get('terminalExit')) is int and cleanup['terminalExit']==receipt['exit']
        and cleanup.get('receiptWriteAttempted') is True and 'receiptWriteError' not in cleanup
        and steps and all(step.get('completed') is True and step.get('error') is None for step in steps),'Unconfirmed termination or failed owned cleanup')
    c.require({'poll-owned-process','wait-owned-process','capture-owned-stdout','capture-owned-stderr'}<=set(step.get('step') for step in steps),'Missing independent owned cleanup steps')
    c.require(receipt.get('capture')=='direct files; no redirected pipe drain'
        and receipt.get('captureCompletion')=='closed-after-observed-exit' and receipt.get('error') is None,'Incomplete acquisition or capture')
    for phase in ('prelaunch','originalReady','before','postexit'):
        filename={'prelaunch':'full-before-launch.json','originalReady':'full-at-original-ready.json',
                  'before':'before-invocation.json','postexit':'full-after-exit.json'}[phase]
        validate_window(receipt.get(phase),pair['root'],control/filename)
    c.require(receipt['prelaunch']['rows']==pair['heldPrepared']['rows'],'Held prepared clone changed before launch')
    validate_gate(receipt,spec,'before')
    for field in ('sourceFact','driverFact','guardFact','windowFact','probeFact'):
        c.require(c.fact(spec[field]['path'])==spec[field] and receipt.get(field)==spec[field],'Source/instrument custody changed: '+field)
    c.require(spec['driverFact']['path']==str(control/'held-driver.ps1')
        and spec['probeFact']['path']==str(control/'input-probe.ps1')
        and spec['sourceFact']['path']==str(pair['caseControl']/'source-free-body.ps1')
        and spec['guardFact']['path']==str(pair['inputs'].parent/'control/original-guard-driver.ps1')
        and spec['windowFact']['path']==str(pair['inputs'].parent/'control/original-window-support.ps1'),'Wrong instrument/source role paths')
    c.require(s.profile_snapshot(spec['source'])==association['sourceInventory'],'Source metadata changed after launch association')
    for field,name in (('driverFact','install-entry-held.ps1'),('probeFact','install-entry-input-probe.ps1')):
        actual=c.fact(pair['inputs']/name)
        c.require(all(actual[key]==spec[field][key] for key in ('bytes','sha256')),'Child file differs from retained instrument input')
    c.require(c.fact(pair['specPath'])==receipt.get('specFact'),'Held spec changed')
    for field in ('stdout','stderr'):
        c.require(c.fact(pair['control']/(field+'.raw'))==receipt.get(field),'Incomplete actual closed capture: '+field)
    proof_path=Path(spec['beforeInputProof']);proof=c.complete_json(proof_path.read_bytes())
    validate_probe(proof,pair,'held-before-source',receipt['pid'],spec['nonce'])
    module_proof_path=Path(pair['env']['R0016_MODULE_INPUT_PROOF'])
    module_proof=c.complete_json(module_proof_path.read_bytes())
    validate_probe(module_proof,pair,'held-module-startup',receipt['pid'],spec['nonce'])
    return proof


class Loopback:
    def __init__(self):
        self.server=socket.socket();self.server.bind(('127.0.0.1',0));self.server.listen(2);self.server.settimeout(0.1)
        self.port=self.server.getsockname()[1];self.stop=threading.Event();self.accepted=[];self.error=None;self.closed=False
        self.thread=threading.Thread(target=self.observe,daemon=True);self.thread.start()
    def observe(self):
        try:
            while not self.stop.is_set():
                try:connection,peer=self.server.accept()
                except socket.timeout:continue
                with connection:self.accepted.append({'peer':list(peer)})
        except OSError as error:
            if not self.stop.is_set():self.error=type(error).__name__+': '+str(error)
    def close(self):
        self.stop.set();self.thread.join(timeout=2);self.server.close()
        c.require(not self.thread.is_alive() and self.error is None,'Owned loopback observation did not close cleanly')
        self.closed=True


def expected_breakpoints(label):
    rows=[]
    for line,text in enumerate(source_body(label).decode('ascii').splitlines(),1):
        if '[IO.File]::WriteAllText' in text:
            owner='Invoke-R0016DormantEffect' if text.startswith('function ') else ''
            rows.append(dict(line=line,column=text.index('[IO.File]')+1,detail='method IO.File::WriteAllText owner='+owner))
        if '$client.Connect' in text:
            rows.append(dict(line=line,column=text.index('$client.Connect')+1,detail='method ::Connect owner='))
    return rows


def validate_semantics(label,result,receipt,pair,events):
    """Pure semantic receiver: integer source exit is distinct from wrapper exit."""
    spec=pair['spec']
    c.require(type(result) is dict and result.get('schema')=='r0016-entry-held-result.v1'
        and type(result.get('pid')) is int and result['pid']==receipt['pid'] and result.get('nonce')==spec['nonce'],'Missing or replayed semantic result')
    validate_host(result,spec)
    expected_mode='allow' if label.endswith('-allow') else 'deny'
    c.require(result.get('scope')=='source-free-diagnostic' and result.get('guardMode')==expected_mode
        and result.get('guardEstablished') is (expected_mode=='deny') and result.get('preparationError') is None,'Wrong guard establishment/scope or preparation failure')
    c.require(result.get('sourceFact')==spec['sourceFact'] and result.get('parameters')==spec['parameters'],'Unbound source-free semantic inputs')
    c.require(result.get('events')==events and result.get('methodInventory')==(expected_breakpoints(label) if expected_mode=='deny' else []),'Wrong complete source event/breakpoint inventory')
    completion,code,explicit=EXPECTED.get(label,('exit-code-observed',0,0))
    c.require(result.get('sourceCompletion')==completion and type(result.get('entryExit')) is int
        and result['entryExit']==code,'Wrong exact semantic source exit/completion')
    c.require('sourceExitCode' in result and result['sourceExitCode']==explicit
        and (explicit is None or type(result['sourceExitCode']) is int),'Missing/incorrect explicit source exit')
    if completion=='terminating-exception':
        message=result.get('sourceException')
        c.require(type(message) is str and bool(message),'Missing source exception')
        if label=='throw':c.require(message=='R0016 synthetic throw','Unattributable source-free throw')
        else:c.require(all(token in message for token in ('InstallSource','github','only-permitted-control-value')),'Unattributable parameter-binding refusal')
    else:c.require('sourceException' in result and result['sourceException'] is None,'Unexpected/missing exception state')
    expected_messages=[] if label=='parameter-failure' else ['R0016 source-free body entered']
    if label=='fallthrough':expected_messages.append('R0016 neutral marker')
    if label=='finally-exit-seventeen':expected_messages.append('R0016 synthetic try')
    if label.endswith('-allow'):expected_messages.append('R0016 effect returned')
    c.require(result.get('messages')==expected_messages,'Source body markers are missing or reordered')


def evaluate(label,pair,receipt,loopback=None):
    proof=validate_terminal(receipt,pair);spec=pair['spec'];control=pair['control']
    c.require(label in CASES and spec.get('scenario')==label and spec.get('scope')=='source-free-diagnostic','Unknown or replayed source-free case')
    c.require(Path(spec['source'])==pair['caseControl']/'source-free-body.ps1'
        and Path(spec['source']).read_bytes()==source_body(label),'Diagnostic body is not the exact fixed constructor output')
    expected_parameters=[dict(name='PresetUrl',type='string',value='https://example.invalid/preset'),
        dict(name='WidgetHash',type='string',value='lat=24.47&lon=39.61&method=4'),
        dict(name='InstallSource',type='string',value='github'),dict(name='DryRun',type='switch',value=True)]
    c.require(spec.get('parameters')==expected_parameters
        and c.direct_parameters(pair['association']['directCommand'],spec['host'],spec['source'])==expected_parameters,'Wrong known typed diagnostic invocation')
    c.require(spec.get('guardMode')==('allow' if label.endswith('-allow') else 'deny'),'Wrong source-free guard mode')
    probe_path=pair['caseControl']/'owned-method-probe.bin'
    c.require(pair['env']['R0016_CONTROL_PROBE']==str(probe_path)
        and pair['association'].get('ownedControlProbeBefore')==dict(path=str(probe_path),exists=False),'Wrong owned effect probe or missing initial absence')
    if label.startswith('loopback-'):
        c.require(loopback is not None and loopback.closed is True and type(loopback.port) is int
            and 1<=loopback.port<=65535 and pair['env']['R0016_CONTROL_PORT']==str(loopback.port),'Missing exact closed loopback control endpoint')
        c.require(all(type(row.get('peer')) is list and len(row['peer'])==2 and row['peer'][0]=='127.0.0.1'
            and type(row['peer'][1]) is int and 1<=row['peer'][1]<=65535 for row in loopback.accepted),'Wrong accepted loopback peer')
    events_path=Path(spec['events']);events=[c.complete_json(line) for line in events_path.read_bytes().splitlines() if line]
    c.require(c.fact(events_path)==receipt.get('eventsFact'),'Raw event bytes differ from actual acquisition')
    result_path=Path(spec['result']);result=c.complete_json(result_path.read_bytes()) if result_path.exists() else None
    c.require(receipt.get('resultFact')==(c.fact(result_path) if result is not None else None),'Raw semantic bytes differ from actual acquisition')
    denied=label.endswith('-deny')
    if denied:
        expected_event=dict(kind='source-call',file=spec['source'],**expected_breakpoints(label)[-1])
        c.require(events==[expected_event],'Guard stop lacks the exact attributable effect-site event')
        c.require(receipt['exit'] in (0,1),'Unexpected denied-control wrapper exit')
        c.require(b'R0016 effect returned' not in (control/'stdout.raw').read_bytes(),'Denied source-free effect returned')
        c.require(not Path(pair['env']['R0016_CONTROL_PROBE']).exists(),'Denied method wrote its owned target')
        if loopback is not None:c.require(not loopback.accepted,'Denied loopback connected')
        # A debugger Stop can prevent the after gate/result. This is a causal
        # guard control only; it is never a healthy complete-source PASS.
        if receipt.get('after') is not None:
            validate_gate(receipt,spec,'after')
            validate_window(receipt['after'],pair['root'],control/'after-invocation.json')
            c.require(receipt['before']['rows']==receipt['after']['rows'],'Denied control changed a completed held window')
        if result is not None:
            validate_host(result,spec)
            c.require(result.get('schema')=='r0016-entry-held-result.v1' and type(result.get('pid')) is int
                and result['pid']==receipt['pid'] and result.get('nonce')==spec['nonce']
                and result.get('sourceFact')==spec['sourceFact'] and result.get('parameters')==spec['parameters']
                and result.get('scope')=='source-free-diagnostic' and result.get('guardMode')=='deny'
                and result.get('guardEstablished') is True and result.get('events')==events
                and result.get('methodInventory')==expected_breakpoints(label),'Unbound denied-control result')
    else:
        c.require(receipt.get('error') is None and receipt['exit']==0 and not events,'Healthy source-free carrier did not finish cleanly')
        validate_gate(receipt,spec,'after')
        validate_window(receipt.get('after'),pair['root'],control/'after-invocation.json')
        c.require(receipt['before']['rows']==receipt['after']['rows'],'Full source-free held interval changed')
        validate_semantics(label,result,receipt,pair,events)
        c.require((control/'stdout.raw').read_bytes().splitlines()==[value.encode('utf-8') for value in result['messages']]
            and (control/'stderr.raw').read_bytes()==b'','Unexpected complete source-free semantic captures')
        if label=='method-write-allow':c.require(Path(pair['env']['R0016_CONTROL_PROBE']).read_bytes()==b'R0016 owned method control','Allowed owned write did not occur')
        if label=='loopback-allow':c.require(loopback is not None and len(loopback.accepted)==1,'Allowed owned loopback did not connect exactly once')
    return dict(case=label,status='PASS',scope='source-free diagnostic only',observation=receipt,
        inputProof=proof,inputProofFact=c.fact(spec['beforeInputProof']),semanticResult=result,
        moduleStartupInputProof=c.complete_json(Path(pair['env']['R0016_MODULE_INPUT_PROOF']).read_bytes()),
        moduleStartupInputProofFact=c.fact(pair['env']['R0016_MODULE_INPUT_PROOF']),
        resultFact=c.fact(result_path) if result_path.exists() else None,events=events,eventsFact=c.fact(events_path),
        ownedControlProbeBefore=pair['association']['ownedControlProbeBefore'],
        ownedControlProbeAfter=dict(path=str(probe_path),exists=probe_path.exists(),fact=c.fact(probe_path) if probe_path.exists() else None),
        loopback=dict(address='127.0.0.1',port=loopback.port,closed=loopback.closed,accepted=list(loopback.accepted)) if loopback else None,
        installerExecuted=False)


def neutral_comparison(pair,direct,held):
    """Retain every physical row and every changed field; no lifecycle subtraction."""
    phases={'directPrepared':pair['directPrepared'],'directPrelaunch':direct['prelaunch'],
        'directReady':direct['ready'],'directPostexit':direct['postexit'],
        'heldPrepared':pair['heldPrepared'],'heldPrelaunch':held['prelaunch'],
        'heldModuleReady':held['originalReady'],'heldBefore':held['before'],
        'heldAfter':held['after'],'heldPostexit':held['postexit']}
    keyed={phase:c.validate_rows(value['rows']) for phase,value in phases.items()}
    keys=sorted(set().union(*(set(value) for value in keyed.values())))
    physical=[]
    comparisons=(('directPrepared','heldPrepared'),('directPrepared','directReady'),('directReady','directPostexit'),
        ('heldPrepared','heldModuleReady'),('heldModuleReady','heldBefore'),
        ('directReady','heldBefore'),('heldBefore','heldAfter'),('heldAfter','heldPostexit'))
    for key in keys:
        values={phase:rows.get(key) for phase,rows in keyed.items()}
        changes=[]
        for before,after in comparisons:
            left,right=values[before],values[after]
            if left!=right:
                changes.append(dict(before=before,after=after,fields={field:dict(before=left.get(field) if left else None,
                    after=right.get(field) if right else None) for field in sorted(c.ROW_FIELDS)
                    if (left or {}).get(field)!=(right or {}).get(field)},membershipChanged=(left is None)!=(right is None)))
        physical.append(dict(role=key[0],path=key[1],phases=values,changes=changes))
    def normalized(value,root):
        if type(value) is list:return [normalized(item,root) for item in value]
        if type(value) is dict:return {key:normalized(item,root) for key,item in value.items()}
        if type(value) is str:
            prefix=str(root)+os.sep
            # Paths and module-search entries only; no time/content projection.
            return ';'.join('@owned-root@'+os.sep+part[len(prefix):] if part.startswith(prefix) else part for part in value.split(';'))
        return value
    direct_proof=direct['inputProof'];held_proof=c.complete_json(Path(pair['spec']['beforeInputProof']).read_bytes())
    fields=('expectedHost','commandHost','hostVersion','hostEdition','source','identitySid','culture','uiCulture',
            'defaultCodePage','environment','commands','provider','queries','complete','error')
    compared={field:dict(direct=normalized(direct_proof[field],pair['directRoot']),
        held=normalized(held_proof[field],pair['root'])) for field in fields}
    input_equal=all(value['direct']==value['held'] for value in compared.values())
    return dict(schema='r0016-source-free-neutral-discriminator.v1',physicalRows=physical,comparisons=list(comparisons),
        actualChildReadContext=compared,actualChildReadContextEquivalent=input_equal,
        preparedCloneEqualsHeldBefore=pair['heldPrepared']['rows']==held['before']['rows'],
        entireHeldBeforeEqualsAfter=held['before']['rows']==held['after']['rows'],
        productQualification=False,scope='Fixed neutral body only. Every lifecycle row and field retained; no product acceptance.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',required=True,choices=('ps51','ps7'))
    parser.add_argument('--host-executable',required=True,type=Path)
    parser.add_argument('--output-root',required=True,type=Path)
    args=parser.parse_args()
    if os.name!='nt':
        print(json.dumps(dict(schema='r0016-entry-driver-diagnostic-result.v1',status='BLOCKED_NATIVE_HOST',nativeWindows=False,installerExecuted=False)))
        return 2
    c.require(args.host_executable.is_absolute() and args.output_root.is_absolute(),'Explicit absolute host/owned output paths are required')
    host=str(args.host_executable.resolve(strict=True))
    parent=args.output_root.resolve(strict=True)
    root=parent/('r0016-entry-driver-'+secrets.token_hex(16));root.mkdir()
    inputs=root/'inputs';inputs.mkdir();control=root/'control';control.mkdir()
    names=('install-entry-driver-diagnostic.py','install-entry-diagnostic-shadow.psm1','install-entry-composition-support.py',
        'install-entry-coverage-support.py','install-entry-held.ps1','install-entry-input-probe.ps1','install-preview.ps1','install-preview-window.ps1')
    input_facts=[]
    for name in names:
        original=HERE/name;target=inputs/name;shutil.copy2(original,target)
        input_facts.append(dict(name=name,original=c.fact(original),retained=c.fact(target)))
    module_bytes=(inputs/'install-entry-diagnostic-shadow.psm1').read_bytes()
    (control/'shadow-module.psm1').write_bytes(module_bytes)
    guard,window,helpers=c.extract_instrument(inputs/'install-preview.ps1',inputs/'install-preview-window.ps1',control)
    rows=[];direct=None;comparison=None
    for label in CASES:
        pair=None;loopback=None
        try:
            pair=make_pair(root,label,args.host,host,inputs,module_bytes,guard,window,helpers)
            if label=='fallthrough':direct=run_direct_neutral(pair)
            if label.startswith('loopback-'):
                loopback=Loopback()
                pair['association']['directEnvironment']['R0016_CONTROL_PORT']=str(loopback.port)
                pair['association']['heldEnvironment']['R0016_CONTROL_PORT']=str(loopback.port)
                pair['env']['R0016_CONTROL_PORT']=str(loopback.port)
                c.save(pair['caseControl']/'association.json',pair['association'])
            try:c.invoke_pair(pair,s)
            except BaseException:
                # Expected guard Stops are interpreted only from complete raw
                # terminal/gate/effect evidence below. No exception implies PASS.
                pass
            if loopback is not None:loopback.close()
            receipt=c.complete_json((pair['control']/'held-observation.json').read_bytes())
            row=evaluate(label,pair,receipt,loopback)
            if label=='fallthrough':
                comparison=neutral_comparison(pair,direct,receipt)
                c.save(pair['caseControl']/'neutral-comparison.json',comparison)
                c.require(comparison['actualChildReadContextEquivalent'],'Neutral direct/held child read contexts differ; inspect complete retained values')
            rows.append(row)
        except BaseException as error:
            if loopback is not None:
                try:loopback.close()
                except BaseException as cleanup:cleanup_text=type(cleanup).__name__+': '+str(cleanup)
                else:cleanup_text=None
            else:cleanup_text=None
            rows.append(dict(case=label,status='FAIL',error=type(error).__name__+': '+str(error),cleanupError=cleanup_text,
                             fixture=str(pair['root']) if pair else None,installerExecuted=False))
            break  # No repeated acquisition after an unexplained bootstrap failure.
    custody_errors=[]
    for row in input_facts:
        try:
            c.require(c.fact(row['original']['path'])==row['original'] and c.fact(row['retained']['path'])==row['retained'],
                'Input bytes changed during diagnostic: '+row['name'])
        except BaseException as error:custody_errors.append(type(error).__name__+': '+str(error))
    passed=len(rows)==len(CASES) and all(row['status']=='PASS' for row in rows) and direct is not None and not custody_errors
    report=dict(schema='r0016-entry-driver-diagnostic.v1',status='PASS' if passed else 'FAIL',nativeWindows=True,
        expectedHost=args.host,commandHost=host,fixture=str(root),inputs=input_facts,
        moduleFact=c.fact(control/'shadow-module.psm1'),directNeutral=direct,neutralComparison=comparison,
        results=rows,expectedCases=list(CASES),inputCustodyErrors=custody_errors,hostExecutableFact=c.fact(host),
        installerExecuted=False,productQualification=False,scope='NEW driver/probe/module diagnostic; full raw lifecycle differences retained.')
    report_path=root/'driver-diagnostic.json';c.save(report_path,report)
    print(json.dumps(dict(schema='r0016-entry-driver-diagnostic-result.v1',status=report['status'],nativeWindows=True,
        expectedHost=args.host,commandHost=host,fixture=str(root),report=c.fact(report_path),installerExecuted=False,productQualification=False)))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
