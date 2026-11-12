#!/usr/bin/env python3
"""NEW bounded native carrier for reviewed R0016 genuine full-entry qualification.

All input bytes and original case identities are fixed. Job lifetime control is
not a filesystem/network sandbox. The complete owned tree is always retained.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import ast, copy, hashlib, importlib.util, json, math, ntpath, os, re, secrets, shutil, stat, struct, sys, tarfile, threading, time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
HELPER_SHA='6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
ROOT_PREFIX='r16f-'
VERSION_SECONDS=60
CHILD_SECONDS=60
JSON_LIMIT=64*1024*1024
PS7_EXE_SHA='bfb46af89433268872ddb43d1ca7a3f433452ee91ed356a9786940f90118e285'
VERSION_CODE="[Console]::Write(('{0}|{1}|{2}|{3}|{4}' -f $PSVersionTable.PSVersion,$PSVersionTable.PSEdition,[Environment]::OSVersion.Platform,[Environment]::Is64BitProcess,[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName))"
INPUTS={'install.ps1': (110645, '7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4'), 'presets/salah-widget.tablissng.json': (1341, '9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f'), 'tests/install-entry-native-composition.py': (56323, 'b235e870a49c12238468e0dcb7e52135ec9db6cbe17cbd7a49f257b35ef86189'), 'tests/install-entry-product-support.py': (44517, '4cba85154dc359ea0389365f76660b2d095600cad7b05de7817de92debb7a987'), 'tests/install-entry-composition-support.py': (37442, '4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821'), 'tests/install-entry-coverage-support.py': (14701, '52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a'), 'tests/install-entry-held.ps1': (8262, '742b42edd3828ec98dc25f717fdbacbd3e68ed877139c90e358d43f7c5142ca2'), 'tests/install-entry-input-probe.ps1': (12493, 'f4c871734c72a71c04423a3fcfc1c4c9a2286da7683d09a1eb6ffeefb73c2bf0'), 'tests/install-entry-driver-diagnostic.py': (57115, '08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5'), 'tests/install-entry-diagnostic-shadow.psm1': (5710, '5bc1cb8b88c6c873a295f664304968d7a859c0f322223b8b6bb8b15798f67663'), 'tests/install-preview.ps1': (57909, 'e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916'), 'tests/install-preview-window.ps1': (13117, '05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83')}
CASES=('github', 'cached', 'store', 'ask', 'installed', 'mixed', 'legacy', 'none', 'missing-preset', 'bad-option', 'positive', 'no-open', 'readable', 'unreadable', 'invalid-env-source', 'valid-env-store', 'preview-noopen-github', 'preview-noopen-store', 'env-source-default', 'explicit-source-override')
FAILURE_CASES=('legacy', 'none', 'bad-option', 'unreadable', 'invalid-env-source')
BUDGET={'aclSetupMaximum': 38, 'aclSecondsEach': 60, 'directAndBaselineMaximum': 40, 'directSecondsEach': 60, 'directCleanupSecondsEach': 10, 'heldMaximum': 18, 'heldSecondsEach': 60, 'heldCleanupSecondsEach': 5, 'finalObservationSeconds': 300, 'total': 6550}
OUTER_SECONDS=BUDGET["total"]
SOURCE_FREE_PREREQUISITE={'runId':43152365236,'commit':'5b33e534b13062f7103852d560bf364435df91b6','scope':'Separate two-host source-free driver; no product case credit'}

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


def build_command(launched,python,host,executable,outputs):
    require(set(launched)==set(INPUTS) and host in ('ps51','ps7'),'Wrong fixed product roles/host')
    def path(name):return launched[name]['path']
    return [str(python),'-B',path('tests/install-entry-native-composition.py'),path('install.ps1'),
        '--preset',path('presets/salah-widget.tablissng.json'),'--host',host,
        '--host-executable',str(executable),'--output-root',str(outputs),
        '--preview-core',path('tests/install-preview.ps1'),'--window-library',path('tests/install-preview-window.ps1')]


def expected_entry_command(executable,source,scenario):
    require(scenario in CASES,'Unknown full-entry scenario')
    route='store' if scenario in ('store','valid-env-store','preview-noopen-store','explicit-source-override') else 'ask' if scenario=='ask' else 'invalid' if scenario=='bad-option' else 'github'
    command=[str(executable),'-NoProfile','-File',str(source),'-PresetUrl',
        '' if scenario=='missing-preset' else 'https://example.invalid/preset','-WidgetHash','lat=24.47&lon=39.61&method=4']
    if scenario not in ('invalid-env-source','valid-env-store','env-source-default'):command+=['-InstallSource',route]
    if scenario not in ('positive','no-open'):command+=['-DryRun']
    if scenario in ('no-open','preview-noopen-github','preview-noopen-store'):command+=['-NoOpen']
    return command


def selected_pure_receiver(path,name,digest,bindings=None):
    require(file_fact(path)['sha256']==digest,'Pure receiver source differs')
    tree=ast.parse(Path(path).read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    require(len(nodes)==1 and not nodes[0].decorator_list,'Missing or ambiguous pure receiving function')
    namespace=dict(require=require,math=math)
    if bindings is not None:namespace.update(bindings)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]


def validate_source_relation(observation,case,scenario,host,source,composition,product_receivers):
    relation=observation.get('sourceInputRelation');held=observation.get('heldComposition')
    require(type(relation) is dict and relation.get('schema')=='r0016-entry-source-input-relation.v1'
        and relation.get('complete') is True and relation.get('sourceSha256')==INPUTS['install.ps1'][1],
        'Missing exact-source input relation')
    require(type(held) is dict and set(held)=={'observation','result','association'}
        and type(held['observation']) is dict and held['observation'].get('sourceInputRelation')==relation,
        'Relation is not the actual held admission')
    control=case/'h/control';facts=[file_fact(control/'source-input-relation.json',case)]
    require(read_json(control/'source-input-relation.json',case)==relation,'Stored original relation differs')
    association=read_json(control/'association.json',case);facts.append(file_fact(control/'association.json',case))
    require(association==held['association'] and association.get('directRoot')==str(case)
        and association.get('heldRoot')==str(case/'h') and association.get('scenario')==scenario
        and association.get('directCommand')==observation['command']
        and association.get('source')==file_fact(source),'Replayed source-input association')
    receipt=held['observation'];result=held['result'];spec=read_json(control/'spec.json',case)
    facts.append(file_fact(control/'spec.json',case));facts.append(file_fact(control/'held-observation.json',case))
    require(receipt==read_json(control/'held-observation.json',case),'Held terminal receipt differs from its original file')
    require(receipt.get('schema')=='r0016-entry-held-observation.v1' and type(receipt.get('pid')) is int and receipt['pid']>0
        and type(receipt.get('nonce')) is str and re.fullmatch(r'[0-9a-f]{32}',receipt['nonce'])
        and receipt.get('command')==association.get('heldCommand') and receipt.get('cwd')==association.get('cwd')
        and receipt.get('environment')==association.get('heldEnvironment'),'Wrong held process association')
    require(type(receipt.get('exit')) is int and receipt['exit']==0 and receipt.get('exitObserved') is True
        and receipt.get('timedOut') is False and receipt.get('error') is None and receipt.get('terminationUnconfirmed') is not True
        and receipt.get('capture')=='direct files; no redirected pipe drain'
        and receipt.get('captureCompletion')=='closed-after-observed-exit','Incomplete held terminal/capture')
    elapsed=receipt.get('elapsedSeconds')
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<CHILD_SECONDS
        and type(receipt.get('timeoutSeconds')) in (int,float) and receipt['timeoutSeconds']==CHILD_SECONDS,'Late or invalid held terminal')
    cleanup=receipt.get('cleanup');require(type(cleanup) is dict and cleanup.get('processStarted') is True
        and cleanup.get('terminalObserved') is True and type(cleanup.get('terminalExit')) is int and cleanup['terminalExit']==0
        and cleanup.get('receiptWriteAttempted') is True and cleanup.get('receiptWriteError') is None,'Unconfirmed held cleanup')
    steps=cleanup.get('steps');require(type(steps) is list and steps
        and all(type(row) is dict and type(row.get('step')) is str and row.get('completed') is True and row.get('error') is None for row in steps)
        and len({row['step'] for row in steps})==len(steps)
        and {'poll-owned-process','wait-owned-process','capture-owned-stdout','capture-owned-stderr'}<={row['step'] for row in steps},
        'Missing or failed owned held cleanup step')
    require(spec.get('schema')=='r0016-entry-held-spec.v1' and spec.get('scope')=='product' and spec.get('guardMode')=='deny'
        and spec.get('scenario')==scenario and spec.get('expectedHost')==host and spec.get('nonce')==receipt['nonce']
        and spec.get('source')==str(source) and spec.get('sourceFact')==file_fact(source)
        and spec.get('host')==observation['command'][0],'Wrong actual held product spec')
    require(association.get('heldCommand')==[spec['host'],'-NoProfile','-File',str(control/'held-driver.ps1')]
        and spec.get('driverFact',{}).get('path')==str(control/'held-driver.ps1')
        and (spec['driverFact'].get('bytes'),spec['driverFact'].get('sha256'))==INPUTS['tests/install-entry-held.ps1'],
        'Actual held command is not the pinned copied driver')
    for path_key,fact_key in [('guardSource','guardFact'),('windowSupport','windowFact'),('inputProbe','probeFact')]:
        require(type(spec.get(fact_key)) is dict and spec.get(path_key)==spec[fact_key].get('path'),
            'Held instrument path/fact differs: '+path_key)
    require(spec.get('parameters')==composition.direct_parameters(observation['command'],spec['host'],str(source))
        and association.get('parameters')==spec['parameters'],'Held typed parameters differ from actual direct command')
    for key in ('sourceFact','driverFact','guardFact','windowFact','probeFact'):
        value=spec.get(key);require(type(value) is dict and receipt.get(key)==value,'Held launch fact differs: '+key)
        facts.append(verify_fact(value,Path(value['path']),source.parent if key=='sourceFact' else case))
    for key,path in [('specFact',control/'spec.json'),('stdout',control/'stdout.raw'),('stderr',control/'stderr.raw'),
        ('resultFact',control/'result.json'),('eventsFact',control/'events.jsonl')]:facts.append(verify_fact(receipt.get(key),path,case))
    require((control/'events.jsonl').read_bytes()==b'' and type(result) is dict and result==read_json(control/'result.json',case),
        'Held raw events/result differs')
    require(result.get('schema')=='r0016-entry-held-result.v1' and type(result.get('pid')) is int and result['pid']==receipt['pid']
        and result.get('nonce')==receipt['nonce'] and result.get('nativeWindows') is True and result.get('expectedHost')==host
        and result.get('commandHost')==spec['host'] and result.get('sourceFact')==spec['sourceFact']
        and result.get('parameters')==spec['parameters'],'Held source result is unbound')
    require(result.get('guardEstablished') is True and result.get('preparationError') is None and result.get('events')==[]
        and type(result.get('methodInventory')) is list and bool(result['methodInventory']),'Held source guard/result incomplete')
    require((host=='ps51' and result.get('hostEdition')=='Desktop' and type(result.get('hostVersion')) is str
        and re.fullmatch(r'5\.1(?:\.\d+){0,2}',result['hostVersion'])) or
        (host=='ps7' and result.get('hostEdition')=='Core' and result.get('hostVersion')=='7.6.6'),'Wrong held native host')
    composition.exact_exit(observation['entryExit'],result,scenario)
    early=scenario in ('bad-option','invalid-env-source');ready=relation.get('directDiscoveryObserved')
    require(type(ready) is bool and (ready or early),'Missing actual direct discovery observation')
    require(relation.get('mode')==('early-option-refusal' if early else 'discovery')
        and relation.get('actualReadContextEquivalent') is (True if ready else None)
        and relation.get('heldReadContextEquivalent') is True and relation.get('entireHeldBeforeEqualsAfter') is True,
        'Incomplete source-read context relation')
    locations={
        'directPrepared':(case,control/'direct-after-directory-restoration.json'),
        'directPrelaunch':(case,case/'direct-full-before-launch.json'),
        'directPostexit':(case,case/'direct-full-after-exit.json'),
        'heldPrepared':(case/'h',control/'held-prepared.json'),
        'heldPrelaunch':(case/'h',control/'full-before-launch.json'),
        'heldModuleReady':(case/'h',control/'full-at-original-ready.json'),
        'heldBefore':(case/'h',control/'before-invocation.json'),
        'heldAfter':(case/'h',control/'after-invocation.json'),
        'heldPostexit':(case/'h',control/'full-after-exit.json')}
    if ready:locations['directReady']=(case,case/'entry-profile-window/full-at-ready.json')
    require(relation.get('absentPhases')==([] if ready else ['directReady'])
        and type(relation.get('phaseFacts')) is dict and set(relation['phaseFacts'])==set(locations),
        'Omitted or invented physical input phase')
    inventories={};keyed={}
    for name,(root,path) in locations.items():
        facts.append(verify_fact(relation['phaseFacts'][name],path,case));value=read_json(path,case)
        require(value.get('schema')=='r0016-entry-full-input-inventory.v1' and value.get('root')==str(root)
            and value.get('complete') is True and value.get('passes')==[value.get('rows'),value.get('rows')],
            'Incomplete original relation inventory: '+name)
        inventories[name]=value;keyed[name]=composition.validate_rows(value['rows'])
    for field,name in [('fullInputsBefore','directPrelaunch'),('fullInputsAfter','directPostexit')]:
        require(observation.get(field)==inventories[name],'Direct report input differs from physical phase')
    for field,name in [('prelaunch','heldPrelaunch'),('originalReady','heldModuleReady'),('before','heldBefore'),('after','heldAfter'),('postexit','heldPostexit')]:
        require(held['observation'].get(field)==inventories[name],'Held report input differs from physical phase')
    require(keyed['directPrepared']==keyed['directPrelaunch'] and keyed['heldPrepared']==keyed['heldPrelaunch']
        and keyed['heldBefore']==keyed['heldAfter'],'Prepared or entire held invocation equality fails')
    composition.verify_input_mapping(association['entries'],inventories['directPrepared']['rows'],inventories['heldPrepared']['rows'])
    names=('directPrepared','directPrelaunch','directReady','directPostexit','heldPrepared','heldPrelaunch',
        'heldModuleReady','heldBefore','heldAfter','heldPostexit')
    comparisons=[['directPrepared','directPrelaunch'],['directPrepared','heldPrepared'],
        ['directPrelaunch','directReady'],['directReady','directPostexit'],['directPrelaunch','directPostexit'],
        ['heldPrepared','heldPrelaunch'],['heldPrelaunch','heldModuleReady'],['heldModuleReady','heldBefore'],
        ['directReady','heldBefore'],['heldBefore','heldAfter'],['heldAfter','heldPostexit']]
    require(relation.get('comparisons')==comparisons,'Missing original physical comparison')
    physical=[]
    for key in sorted(set().union(*(set(rows) for rows in keyed.values()))):
        values={name:keyed[name].get(key) if name in keyed else None for name in names};changes=[]
        for left,right in comparisons:
            if left not in keyed or right not in keyed or values[left]==values[right]:continue
            changes.append(dict(before=left,after=right,membershipChanged=(values[left] is None)!=(values[right] is None),
                fields={field:dict(before=(values[left] or {}).get(field),after=(values[right] or {}).get(field))
                    for field in sorted(composition.ROW_FIELDS) if (values[left] or {}).get(field)!=(values[right] or {}).get(field)}))
        physical.append(dict(role=key[0],path=key[1],phases=values,changes=changes))
    require(relation.get('physicalRows')==physical,'Physical relation omits or rewrites original values/deltas')
    contexts=[('heldModuleContext','heldModuleProofFact',case/'h','held-module-startup','heldPrepared','heldModuleReady'),
        ('heldBeforeContext','heldBeforeProofFact',case/'h','held-before-source','heldPrepared','heldBefore')]
    if ready:
        require(observation.get('fullInputsAtReady')==inventories['directReady'],'Direct ready report differs')
        contexts.append(('directContext','directProofFact',case,'direct-pre-discovery','directPrepared','directReady'))
    else:require(relation.get('directContext') is None and relation.get('directProofFact') is None,
        'Early refusal invents unobserved direct context')
    normalized=[]
    for context_key,fact_key,root,phase,prepared,observed in contexts:
        context=relation.get(context_key);value=relation.get(fact_key)
        require(type(context) is dict and type(value) is dict,'Missing actual source-read context/proof')
        path=checked_path(value.get('path'),root);facts.append(verify_fact(value,path,root));proof=read_json(path,root)
        require(context.get('proof')==proof and proof.get('schema')=='r0016-entry-child-input-proof.v1'
            and proof.get('complete') is True and proof.get('error') is None and proof.get('phase')==phase
            and proof.get('source')==file_fact(source) and proof.get('expectedHost')==host,
            'Actual source-read proof differs')
        native=observation['profileWindow'] if context_key=='directContext' else held['observation']
        require(type(proof.get('pid')) is int and proof['pid']==native['pid'] and proof.get('nonce')==native['nonce'],
            'Actual source-read proof PID/nonce is replayed')
        binding_path=root/'control'/('product-read-file-bindings-'+phase+'.json')
        facts.append(verify_fact(context.get('proofFileBindings'),binding_path,root));bindings=read_json(binding_path,root)
        contract=product_receivers['read_query_contract'](proof,root,inventories[prepared]['rows'],scenario)
        require(json.loads(json.dumps(contract))==context.get('readContract'),'Read contract differs from original proof')
        product_receivers['bind_source_read_rows'](contract,inventories[prepared]['rows'],inventories[observed]['rows'])
        if context_key=='directContext':product_receivers['bind_source_read_rows'](contract,inventories[prepared]['rows'],inventories['directPostexit']['rows'])
        value=product_receivers['normalized_read_context'](proof,root,bindings)
        require(context.get('normalized')==value,'Normalized context differs from actual proof and file bindings')
        normalized.append(value)
    require(all(value==normalized[0] for value in normalized),'Actual source-read contexts disagree')
    if early:
        refusal=relation.get('earlyOptionRefusal')
        require(type(refusal) is dict and refusal.get('verified') is True and refusal.get('sourceSha256')==INPUTS['install.ps1'][1]
            and type(refusal.get('directExit')) is int and refusal['directExit']==1
            and type(refusal.get('heldExit')) is int and refusal['heldExit']==1,'Early option refusal is not established')
        for stream in ('stdout','stderr'):facts.append(verify_fact(refusal.get(stream),case/(stream+'.txt'),case))
    else:require(relation.get('earlyOptionRefusal') is None,'Unexpected early refusal substituted for discovery')
    return facts


def validate_case_headers(rows,fixture,host,executable,source,direct_receiver,rows_receiver,normal_receiver,composition,product_receivers):
    require(callable(normal_receiver) and composition is not None and type(product_receivers) is dict
        and set(product_receivers)=={'read_query_contract','bind_source_read_rows','normalized_read_context'},
        'Full product receiving predicates are mandatory')
    require(type(rows) is list and len(rows)==len(CASES),'Incomplete full20 denominator')
    require([r.get('case') if type(r) is dict else None for r in rows]==list(CASES),'Missing, duplicate or reordered product case')
    facts=[];pids=[];nonces=[]
    for number,(scenario,row) in enumerate(zip(CASES,rows)):
        require(row.get('host')==host and row.get('pass_') is True and 'error' not in row and 'restorationError' not in row,'Failed or wrong-host product case')
        observation=row.get('observation');require(type(observation) is dict,'Missing actual entry observation')
        case=fixture/('c%02d'%number)
        require(observation.get('fixture')==str(case) and observation.get('command')==expected_entry_command(executable,source,scenario),'Wrong genuine full-entry command or case fixture')
        require(type(observation.get('entryExit')) is int and observation['entryExit']==(1 if scenario in FAILURE_CASES else 0),'Wrong typed actual entry exit')
        require(type(observation.get('readinessNonce')) is str and re.fullmatch(r'[0-9a-f]{32}',observation['readinessNonce']),'Missing direct case nonce')
        nonces.append(observation['readinessNonce'])
        direct=observation.get('directLaunchInputs');require(type(direct) is dict and direct.get('command')==observation['command'],'Actual direct launch differs')
        for name in ('fullInputsBefore','fullInputsAfter'):
            inventory=observation.get(name)
            require(type(inventory) is dict and inventory.get('schema')=='r0016-entry-full-input-inventory.v1' and inventory.get('root')==str(case) and inventory.get('complete') is True,'Missing complete '+name)
            require(type(inventory.get('rows')) is list and len(inventory.get('passes',[]))==2 and inventory['passes'][0]==inventory['passes'][1]==inventory['rows'],'Incomplete two-pass '+name)
            rows_receiver(inventory['rows'])
        for name in ('profileWindow','hostOnlyBaseline'):
            receipt=observation.get(name);require(type(receipt) is dict,'Missing native direct '+name)
            expected=observation['command'] if name=='profileWindow' else [str(executable),'-NoProfile','-File',str(case/'host-only-control/host-only.ps1')]
            direct_receiver(receipt,expected,CHILD_SECONDS)
            pids.append(receipt['pid'])
        require(observation['profileWindow']['entryExit']==observation['entryExit'],'Direct exit/receipt mismatch')
        require(type(observation['hostOnlyBaseline'].get('entryExit')) is int and observation['hostOnlyBaseline']['entryExit']==0,'Host-only baseline failed')
        for name in ('stdout','stderr'):
            require(observation.get(name)==str(case/(name+'.txt')),'Raw stream role redirected')
            facts.append(file_fact(case/(name+'.txt'),fixture))
        require(observation.get('snapshotUnchanged') is True,'Unexpected retained subject difference')
        if scenario in ('positive','no-open'):
            require(observation.get('normalConfinementValidated') is True,'Normal confinement not admitted')
            postcondition=normal_receiver(copy.deepcopy(observation))
            require(observation.get('normalInputPostcondition')==postcondition,'Normal postcondition differs from exact full input receiver')
        else:
            require(observation.get('effects')==[],'Dry-run reached an effect spy')
            require(type(observation.get('heldComposition')) is dict,'Dry-run lacks separate held full-file evidence')
            facts+=validate_source_relation(observation,case,scenario,host,source,composition,product_receivers)
    require(len(set(nonces))==len(CASES),'Replayed direct case nonce')
    return dict(cases=list(CASES),caseCount=len(CASES),observedDirectAndBaselinePids=pids,rawCaptureFacts=facts)


def validate_report(process,command,capture,outputs,owner,python,executable,host,launched):
    owner=checked_path(owner,directory=True);capture=checked_path(capture,owner,directory=True)
    outputs=checked_path(outputs,owner,directory=True);python=checked_path(python);executable=checked_path(executable)
    require(set(launched)==set(INPUTS),'Missing product launch role')
    for name,value in launched.items():verify_fact(value,owner/'control'/name,owner)
    require(command==build_command(launched,python,host,executable,outputs),'Wrong full product controller CLI')
    facts=validate_terminal(process,command,capture,OUTER_SECONDS)
    require((capture/'observer.stderr.raw').read_bytes()==b'','Full-entry controller stderr is nonempty')
    envelope=read_json(capture/'observer.stdout.raw',owner)
    require(envelope.get('schema')=='r0016-native-entry-composition-result.v1' and envelope.get('status')=='PASS','Incomplete product envelope')
    require(envelope.get('expectedHost')==host and envelope.get('commandHost')==str(executable),'Wrong actual product host')
    report_fact=envelope.get('report');require(type(report_fact) is dict and type(report_fact.get('path')) is str,'Missing exact product report')
    report_path=checked_path(report_fact['path'],outputs);fixture=report_path.parent
    require(report_path.name=='entry-composition-report.json' and fixture.parent==outputs and re.fullmatch(r'e[0-9a-f]{16}',fixture.name),'Wrong owned product fixture constructor')
    require(list(outputs.iterdir())==[fixture] and envelope.get('fixture')==str(fixture),'Duplicate/replayed product fixture')
    facts.append(verify_fact(report_fact,report_path,outputs));report=read_json(report_path,outputs)
    require(report.get('schema')=='r0016-native-entry-composition.v1' and report.get('nativeWindows') is True and report.get('status')=='PASS','Wrong native product report')
    require(report.get('sourceUnchanged') is True and report.get('sourceBefore')==report.get('source')==INPUTS['install.ps1'][1],'Product source changed or differs')
    for key,name in [('testSha256','tests/install-entry-native-composition.py'),('supportSha256','tests/install-entry-coverage-support.py'),('compositionSha256','tests/install-entry-product-support.py'),('compositionCoreSha256','tests/install-entry-composition-support.py'),('diagnosticSha256','tests/install-entry-driver-diagnostic.py'),('heldDriverSha256','tests/install-entry-held.ps1'),('preset','presets/salah-widget.tablissng.json')]:
        require(report.get(key)==INPUTS[name][1],'Wrong exact report input: '+key)
    require(report.get('selectedHosts')==[host] and report.get('selectedScenarios')==list(CASES) and report.get('fixture')==str(fixture),'Wrong selected host/scenario/fixture scope')
    direct_receiver=selected_pure_receiver(Path(launched['tests/install-entry-native-composition.py']['path']),'validate_direct_terminal',INPUTS['tests/install-entry-native-composition.py'][1])
    composition=load_exact(Path(launched['tests/install-entry-composition-support.py']['path']),INPUTS['tests/install-entry-composition-support.py'][1],'r16_full_entry_original_input_receivers')
    support=load_exact(Path(launched['tests/install-entry-coverage-support.py']['path']),INPUTS['tests/install-entry-coverage-support.py'][1],'r16_full_entry_original_coverage_receivers')
    normal_receiver=selected_pure_receiver(Path(launched['tests/install-entry-native-composition.py']['path']),'require_normal_input_postcondition',INPUTS['tests/install-entry-native-composition.py'][1],
        dict(composition=composition,support=support,SOURCE_HASH_BEFORE=INPUTS['install.ps1'][1]))
    product_receivers={name:selected_pure_receiver(Path(launched['tests/install-entry-product-support.py']['path']),name,INPUTS['tests/install-entry-product-support.py'][1],
        dict(Path=Path,os=os,copy=copy,validate_rows=composition.validate_rows,sha=lambda value:hashlib.sha256(value).hexdigest()))
        for name in ('read_query_contract','bind_source_read_rows','normalized_read_context')}
    path_budget=report.get('pathBudget');require(type(path_budget) is dict and path_budget==read_json(fixture/'normal-path-budget.json',fixture)
        and path_budget.get('schema')=='r0016-full-entry-path-budget.v1' and path_budget.get('complete') is True
        and path_budget.get('sourceSha256')==INPUTS['install.ps1'][1] and path_budget.get('fixture')==str(fixture)
        and type(path_budget.get('maxUtf16Units')) is int and path_budget['maxUtf16Units']<=240,'Missing bounded source-owned normal paths')
    facts.append(file_fact(fixture/'normal-path-budget.json',fixture))
    budget_rows=path_budget.get('rows');require(type(budget_rows) is list and len(budget_rows)==24,'Incomplete source-owned path budget')
    for row in budget_rows:
        require(type(row) is dict and row.get('scenario') in ('positive','no-open') and type(row.get('pathTemplate')) is str
            and type(row.get('utf16Units')) is int and row['utf16Units']==len(row['pathTemplate'].encode('utf-16-le'))//2
            and row['utf16Units']<=240 and Path(row['pathTemplate']).is_relative_to(fixture/('c%02d'%CASES.index(row['scenario']))),
            'Incorrect normal path length or case association')
    require(max(row['utf16Units'] for row in budget_rows)==path_budget['maxUtf16Units'],'Wrong maximum normal path length')
    cases=validate_case_headers(report.get('results'),fixture,host,executable,Path(launched['install.ps1']['path']),direct_receiver,composition.validate_rows,normal_receiver,composition,product_receivers)
    facts+=cases.pop('rawCaptureFacts')
    return dict(report=report_fact,fixture=str(fixture),expectedHost=host,commandHost=str(executable),**cases,
        custodyFiles=facts,sourceFreePrerequisite=SOURCE_FREE_PREREQUISITE,
        scope='Exact twenty genuine entry cases with separate held source invocation; normal/NoOpen keep their actual effects. No merge, release, closure, independent OS containment or global effect telemetry is implied.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('ps51','ps766'))
    parser.add_argument('--powershell',type=Path)
    parser.add_argument('--output-parent',required=True,type=Path)
    parser.add_argument('--source-commit')
    parser.add_argument('--archive-only',action='store_true')
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if os.name!='nt' or struct.calcsize('P')!=8:parser.error('Native 64-bit Windows required; no selected PowerShell started')
    parent=checked_path(args.output_parent,directory=True)
    require(parent.drive.lower()=='c:' and parent==Path(os.environ['USERPROFILE']).resolve(strict=True),'Actual C: profile parent required')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None and args.source_commit is None,'Wrong archive-only arguments')
        print(archive_owned_root(parent,args.archive));return 0
    require(args.host is not None and args.powershell is not None and args.archive is None and type(args.source_commit) is str and re.fullmatch(r'[0-9a-f]{40}',args.source_commit),'Exact host and source commit required')
    host='ps7' if args.host=='ps766' else 'ps51'
    executable=checked_path(args.powershell);python=checked_path(Path(sys.executable).resolve())
    if host=='ps7':
        fact=file_fact(executable);require((fact['bytes'],fact['sha256'])==(301368,PS7_EXE_SHA),'Exact7.6.6 x64 executable differs')
    else:require(executable==Path(os.environ['SYSTEMROOT'],'System32/WindowsPowerShell/v1.0/powershell.exe').resolve(strict=True),'Selected PS51 is not the actual system executable')
    require(not list(parent.glob(ROOT_PREFIX+'*')),'Owned full-entry route root already present; no replay')
    root=parent/(ROOT_PREFIX+secrets.token_hex(8));require(len(str(root).encode('utf-16-le'))//2<=48,'Owned full-entry route root is too long')
    root.mkdir()
    result=dict(schema='r0016-windows-full-entry-acquisition.v1',status='ACQUISITION_INCOMPLETE',fixture=str(root),sourceCommit=args.source_commit,
        expectedHost=host,fullEntryAccepted=False,expectedCases=list(CASES),phases={},sourceAndInputsUnchanged=False,
        independentHardContainment='NOT_ACQUIRED',independentGlobalTransportTelemetry=None,sourceFreePrerequisite=SOURCE_FREE_PREREQUISITE)
    save(root/'route-result.json',result);fixed=[];copied={};status=2
    try:
        source=Path(__file__).resolve();repo=source.parents[2];control=root/'control';control.mkdir()
        roles={name:digest for name,(_,digest) in INPUTS.items()}
        roles['tools/qualification/installer_preview_host_probe.py']=HELPER_SHA
        roles['tools/qualification/installer_preview_windows_full_entry.py']=file_fact(source)['sha256']
        originals=[]
        for role,digest in roles.items():
            fact=file_fact(repo/role);require(fact['sha256']==digest,'Pinned full-entry role differs: '+role)
            if role in INPUTS:require((fact['bytes'],fact['sha256'])==INPUTS[role],'Pinned full-entry size/hash differs: '+role)
            target=control/role;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fact['path'],target)
            retained=file_fact(target,root);require((retained['bytes'],retained['sha256'])==(fact['bytes'],fact['sha256']),'Full-entry launch copy differs')
            copied[role]=retained;originals.append(fact)
        fixed=originals+list(copied.values())+[file_fact(executable),file_fact(python)]
        helper=load_exact(copied['tools/qualification/installer_preview_host_probe.py']['path'],HELPER_SHA,'r16_full_entry_published_host_helper')
        launched={name:copied[name] for name in INPUTS}
        version=root/'version';version.mkdir();capture=root/'run';capture.mkdir();outputs=root/'f';outputs.mkdir()
        version_state=root/'v';state=root/'s'
        version_env=owned_environment(helper,version_state,executable);environment=owned_environment(helper,state,executable)
        version_command=[str(executable),'-NoProfile','-NonInteractive','-Command',VERSION_CODE]
        command=build_command(launched,python,host,executable,outputs)
        plan=dict(schema='r0016-windows-full-entry-plan.v1',sourceCommit=args.source_commit,preparedUtc=utc(),root=str(root),
            expectedHost=host,host=file_fact(executable),python=file_fact(python),originals=originals,copiedInputs=copied,launchedInputs=launched,noGatherOverride=False,
            version=dict(command=version_command,environment=version_env,timeoutSeconds=VERSION_SECONDS),
            fullEntry=dict(command=command,environment=environment,timeoutSeconds=OUTER_SECONDS,outputs=str(outputs)),budget=BUDGET,
            sourceFreePrerequisite=SOURCE_FREE_PREREQUISITE,scope='Actual full entry plus separate held invocation; Job Object bounds owned lifetime, not OS filesystem/network access.')
        save(root/'plan.json',plan)
        process=run_phase(helper,version_command,version_env,version_state,version,VERSION_SECONDS)
        result['phases']['version']=process;save(root/'route-result.json',result)
        validate_terminal(process,version_command,version,VERSION_SECONDS)
        require((version/'observer.stderr.raw').read_bytes()==b'','Cold version stderr is nonempty')
        result['nativeHost']=validate_version((version/'observer.stdout.raw').read_bytes(),host,executable)
        for fact in fixed:verify_fact(fact,Path(fact['path']))
        process=run_phase(helper,command,environment,state,capture,OUTER_SECONDS)
        result['phases']['fullEntry']=process;save(root/'route-result.json',result)
        result['association']=validate_report(process,command,capture,outputs,root,python,executable,host,launched)
        result.update(status='ACQUIRED_WINDOWS_FULL_ENTRY20',fullEntryAccepted=True);status=0
    except Exception as error:result.update(status='FULL_ENTRY_NOT_ADMITTED',error=type(error).__name__+': '+str(error))
    finally:
        try:
            require(bool(fixed),'Complete product launch custody was not established')
            for fact in fixed:verify_fact(fact,Path(fact['path']))
            result['sourceAndInputsUnchanged']=True
        except Exception as error:
            result.update(status='INPUT_CUSTODY_FAILED',fullEntryAccepted=False,finalError=type(error).__name__+': '+str(error));status=2
        save(root/'route-result.json',result)
    print(json.dumps(dict(status=result['status'],fixture=str(root),result=file_fact(root/'route-result.json'),fullEntryAccepted=result['fullEntryAccepted'])))
    return status


if __name__=='__main__':raise SystemExit(main())
