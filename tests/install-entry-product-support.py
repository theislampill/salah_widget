"""NEW product-only source-input association and held acquisition adaptation.

Pinned common/diagnostic files remain unchanged. No installer runs on import.
This module does not confer source-free or product native qualification.
"""
import hashlib
import importlib.util
import copy
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
CORE_PATH=HERE/'install-entry-composition-support.py'
DIAGNOSTIC_PATH=HERE/'install-entry-driver-diagnostic.py'
# Product candidate pin is independent of the immutable source-free instrument.
PREVIEW_SOURCE_SHA='07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a'
CORE_SHA='4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821'
DIAGNOSTIC_SHA='08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5'


def load_exact(name,path,expected):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise AssertionError('Product support dependency bytes differ: '+path.name)
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


core=load_exact('r0016_product_common',CORE_PATH,CORE_SHA)
diagnostic=load_exact('r0016_product_diagnostic',DIAGNOSTIC_PATH,DIAGNOSTIC_SHA)
# These exact reusable functions/constants retain their original implementation.
for name in ('TIMEOUT','ACK_TIMEOUT','SCENARIOS','FAILURE_SCENARIOS','ROW_FIELDS','ROLE_PATHS','CLONE_FIELDS',
    'require','sha','fact','save','complete_json','owned_environment','direct_parameters','exact_exit',
    'validate_rows','map_inputs','verify_input_mapping','inventory','double_inventory','extract_instrument',
    'mapped_environment','finish_owned_acquisition','require_positive_confinement'):
    globals()[name]=getattr(core,name)


def read_query_contract(proof, root, prepared_rows, scenario):
    """Exact fixed-fixture read controls, not a claim about source call counts."""
    prepared=validate_rows(prepared_rows);subject=root/'subject'
    queries=proof.get('queries')
    require(type(queries) is list,'Missing actual read-query control list')
    cursor=0;read_paths=set();enumerations=[]
    def relative(path):return path.relative_to(subject).as_posix()
    def take(expected):
        nonlocal cursor
        require(cursor<len(queries) and queries[cursor]==expected,
            'Missing/reordered/different actual read control: '+expected['id'])
        cursor+=1
    def test(identifier,path):
        key=('subject',relative(path));read_paths.add(key)
        present=key in prepared and prepared[key]['kind']!='absent'
        take(dict(id=identifier,operation='Test-Path',path=str(path),success=True,exists=present,error=None))
        return present
    configurations=(
        ('chrome','local','Google/Chrome/User Data','Google/Chrome/Application/chrome.exe',('pf','pf86','local')),
        ('edge','local','Microsoft/Edge/User Data','Microsoft/Edge/Application/msedge.exe',('pf86','pf','local')),
        ('brave','local','BraveSoftware/Brave-Browser/User Data','BraveSoftware/Brave-Browser/Application/brave.exe',('pf','pf86','local')),
        ('chromium','local','Chromium/User Data','Chromium/Application/chrome.exe',('pf','pf86','local')),
        ('firefox','roam','Mozilla/Firefox/Profiles','Mozilla Firefox/firefox.exe',('pf','pf86','local')),
        ('librewolf','roam','LibreWolf/Profiles','LibreWolf/librewolf.exe',('pf','pf86','local')))
    for browser,location,data_relative,executable,order in configurations:
        for index,base in enumerate(order):
            if test(browser+'/exe/'+str(index),subject/base/executable):break
        data=subject/location/data_relative
        if not test(browser+'/user-data',data):continue
        data_key=relative(data)
        profiles=[row for row in prepared_rows if row['role']=='subject' and row['kind']=='directory'
            and Path(row['path']).parent.as_posix()==data_key and row['path']!=data_key]
        require(len(profiles)==1,'The exact declared fixture requires one profile in each present browser family')
        entries=[]
        for row in profiles:
            read_paths.add(('subject',row['path']))
            entries.append(dict(name=Path(row['path']).name,path=str(subject/row['path']),
                kind='directory',attributes=row['attributes']))
        take(dict(id=browser+'/profiles',operation='enumerate-directories',path=str(data),entries=entries,
            success=True,errors=[],sourceErrorAction='SilentlyContinue'))
        enumerations.append(data_key)
        for index,row in enumerate(profiles):
            profile=subject/row['path'];prefix=browser+'/profile/'+str(index)
            if browser in ('chrome','edge','brave','chromium'):
                require(profile.name=='Default','Unexpected prepared Chromium fixture profile')
                identifiers=('mkaphhbkcccpgkfaifhhdfckagnkcmhm','dlaogejjiafeobgofajdlkkhjlignalk',
                    'lklaendlmlfkaabeleddanafeinnenih','hipekcciheckooncpjeljhnekcoolahp') if browser=='edge' else (
                    'dlaogejjiafeobgofajdlkkhjlignalk','hipekcciheckooncpjeljhnekcoolahp')
                for identifier in identifiers:test(prefix+'/extension/'+identifier,profile/'Extensions'/identifier)
                require(not test(prefix+'/preferences',profile/'Preferences'),
                    'Unexpected Preferences file in the exact declared fixture')
            else:
                metadata=profile/'extensions.json'
                if not test(prefix+'/extensions-json',metadata):continue
                original=prepared['subject',relative(metadata)]
                raw=b'{"addons":[]}\n'
                require(original['kind']=='file' and original['bytes']==len(raw) and original['sha256']==sha(raw),
                    'Prepared Firefox metadata differs from the exact fixture')
                expected=dict(id=prefix+'/extensions-read',operation='metadata-read',path=str(metadata),mode='strict-utf8',
                    success=True,bytes=dict(path=str(metadata),bytes=len(raw),sha256=sha(raw)),
                    text=dict(type='System.String',utf8Bytes=len(raw),sha256=sha(raw)),error=None,
                    nativeJsonParseSucceeded=True,nativeJsonParseError=None)
                if scenario=='unreadable':
                    require(cursor<len(queries),'Missing actual share-refusal read control')
                    failure=queries[cursor].get('error')
                    require(type(failure) is dict and set(failure)=={'exceptionType','nativeCode','errorId','category','message'}
                        and failure['exceptionType']=='System.IO.IOException' and type(failure['nativeCode']) is int
                        and failure['nativeCode']==32 and all(type(failure[key]) is str and failure[key]
                            for key in ('errorId','category','message')),'Unattributable native metadata sharing refusal')
                    expected.update(success=False,bytes=None,text=None,error=failure,nativeJsonParseSucceeded=False)
                take(expected)
    require(cursor==len(queries),'Extra or replayed actual read control')
    return dict(paths=[list(key) for key in sorted(read_paths)],enumerations=enumerations,queries=len(queries))


def bind_source_read_rows(contract, prepared_rows, observed_rows):
    """All fields of each consulted input stay exact within its physical leg."""
    prepared,observed=validate_rows(prepared_rows),validate_rows(observed_rows)
    for key in contract['paths']:
        key=tuple(key)
        require(prepared.get(key)==observed.get(key),'Source-read input changed across startup: '+repr(key))
    for parent in contract['enumerations']:
        def entries(rows):
            return {key:value for key,value in rows.items() if key[0]=='subject'
                and value['kind']=='directory' and Path(key[1]).parent.as_posix()==parent and key[1]!=parent}
        require(entries(prepared)==entries(observed),'Complete profile enumeration changed across startup: '+parent)


def normalized_read_context(proof, root, bindings):
    """Map only known owned paths; retain every original value separately."""
    prefix=str(root)+os.sep;marker='@owned-root@'+os.sep
    def normalize(value,key=None):
        if type(value) is list:return [normalize(item,key) for item in value]
        if type(value) is dict:return {name:normalize(item,name) for name,item in value.items()}
        if type(value) is str:
            if key=='message':return value.replace(prefix,marker)
            return ';'.join(marker+part[len(prefix):] if part.startswith(prefix) else part for part in value.split(';'))
        return value
    fields=('nativeWindows','expectedHost','commandHost','hostVersion','hostEdition','source','probe','subject',
        'identitySid','culture','uiCulture','defaultCodePage','environment','commands','provider','queries','complete','error')
    value={field:copy.deepcopy(proof[field]) for field in fields}
    canonical={row['label']:row['parentFact'] for row in bindings['comparisons']}
    for command in value['commands']:
        for field in ('module','assembly'):command[field]=canonical[command['name']+'/'+field]
    value['provider']['assembly']=canonical['FileSystem/provider-assembly']
    value['nativeFileIdentities']=[dict(label=row['label'],canonicalFact=row['parentFact'],
        identity=row['nativeFileIdentity']['observations']['canonicalAfter']) for row in bindings['comparisons']]
    return normalize(value)


def validate_child_read_context(proof, pair, phase, pid, nonce, prepared, observed):
    spec=pair['spec'];direct=phase=='direct-pre-discovery'
    root=Path(pair['association']['directRoot']) if direct else pair['root']
    environment=pair['association']['directEnvironment'] if direct else pair['env']
    require(type(proof) is dict and proof.get('schema')=='r0016-entry-child-input-proof.v1'
        and proof.get('complete') is True and proof.get('error') is None,'Incomplete actual-child input proof')
    require(type(proof.get('pid')) is int and proof['pid']==pid and proof.get('nonce')==nonce
        and proof.get('phase')==phase,'Replayed input proof PID/nonce/phase')
    diagnostic.validate_host(proof,spec)
    require(proof.get('source')==spec['sourceFact'] and proof.get('probe')==fact(root/'control/input-probe.ps1')
        and proof.get('subject')==str(root/'subject'),'Wrong source/probe/subject input association')
    names=('SALAH_WIDGET_PRESET_URL','SALAH_WIDGET_HASH','SALAH_INSTALL_SOURCE','TABLISSNG_REPO',
        'LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)','HOME','USERPROFILE','TEMP','TMP','PSModulePath','PSModuleAnalysisCachePath')
    actual=proof.get('environment');folded={key.upper():value for key,value in environment.items()}
    require(len(folded)==len(environment) and type(actual) is list and [row.get('name') for row in actual]==list(names),
        'Missing/reordered/ambiguous actual environment proof')
    for row in actual:
        key=row['name'].upper();present=key in folded
        require(set(row)=={'name','present','value'} and type(row.get('present')) is bool and row['present']==present,
            'Wrong actual environment presence/schema')
        if key=='PSMODULEPATH':
            require(type(row['value']) is str and str(root/'modules') in row['value'].split(';')
                and str(Path(spec['host']).parent/'Modules') in row['value'].split(';'),
                'Owned/native module roots absent from actual search path')
        else:require(row['value']==(folded[key] if present else None),'Wrong actual child environment value: '+row['name'])
    commands=proof.get('commands')
    require(type(commands) is list and [row.get('name') for row in commands]==
        ['Test-Path','Get-ChildItem','Get-Content','ConvertFrom-Json'],'Incomplete actual native read bindings')
    bindings=dict(schema='r0016-entry-probe-file-bindings.v1',phase=phase,pid=pid,nonce=nonce,
        sourceFact=spec['sourceFact'],probeFact=proof['probe'],comparisons=[])
    journal=root/'control'/('product-read-file-bindings-'+phase+'.json')
    for row,kind in zip(commands,('TestPathCommand','GetChildItemCommand','GetContentCommand','ConvertFromJsonCommand')):
        require(set(row)=={'name','commandType','source','definition','implementingType','moduleVersion','module','assembly'}
            and row['commandType']=='Cmdlet' and row['implementingType']=='Microsoft.PowerShell.Commands.'+kind,
            'Wrong actual read command/schema')
        require(row['source']==('Microsoft.PowerShell.Utility' if row['name']=='ConvertFrom-Json' else 'Microsoft.PowerShell.Management')
            and all(type(row[key]) is str and row[key] for key in ('definition','moduleVersion')),
            'Wrong actual native read module/definition')
        for field in ('module','assembly'):
            diagnostic.record_probe_file_binding(row[field],row['name']+'/'+field,journal,bindings)
    provider=proof.get('provider')
    require(type(provider) is dict and set(provider)=={'name','implementingType','capabilities','assembly'}
        and provider['name']=='FileSystem' and provider['implementingType']=='Microsoft.PowerShell.Commands.FileSystemProvider'
        and type(provider['capabilities']) is str and provider['capabilities'],'Wrong native filesystem provider')
    diagnostic.record_probe_file_binding(provider['assembly'],'FileSystem/provider-assembly',journal,bindings)
    require(type(proof.get('identitySid')) is str and re.fullmatch(r'S-1-[0-9-]+',proof['identitySid'])
        and type(proof.get('defaultCodePage')) is int and proof['defaultCodePage']>0
        and all(type(proof.get(key)) is str for key in ('culture','uiCulture')),'Missing actual native identity/decoding context')
    contract=read_query_contract(proof,root,prepared['rows'],spec['scenario'])
    bind_source_read_rows(contract,prepared['rows'],observed['rows'])
    return dict(proof=proof,proofFileBindings=fact(journal),readContract=contract,
        normalized=normalized_read_context(proof,root,bindings))


def early_option_refusal(pair, direct, result):
    """The pinned parameter/early-throw prefix performs no discovery reads."""
    scenario=pair['spec']['scenario'];parameters=pair['spec']['parameters']
    environment=pair['association']['directEnvironment']
    require(scenario in ('bad-option','invalid-env-source'),'Unknown early refusal case')
    exact_exit(direct['entryExit'],result,scenario)
    require(result.get('sourceCompletion')=='terminating-exception'
        and type(result.get('sourceException')) is str and result.get('messages')==[],
        'Early refusal was not an attributable source/binding exception')
    output=(Path(direct['stdout']).read_bytes()+Path(direct['stderr']).read_bytes()).decode('utf-8',errors='strict')
    body_markers=('Salah Widget Installer','This wizard can:','Detecting browsers','Would prepare ',
        'Preview targets:','Preview only; no changes made','No eligible target; preview made no changes.',
        'Manual browser installation/import remain pending')
    require(not any(marker in output for marker in body_markers) and not re.search(r'(?m)^\[\d+\] ',output),
        'Early option refusal contains contradictory source body/discovery/action output')
    values=[row['value'] for row in parameters if row['name']=='InstallSource']
    if scenario=='bad-option':
        require(values==['invalid'],'Bad-option control no longer supplies the invalid typed argument')
        for text in (output,result['sourceException']):
            require(all(token in text for token in ('InstallSource','invalid','ask','github','store'))
                and ('Cannot validate argument' in text or 'ValidateSet' in text),
                'Bad-option exit lacks the exact parameter validation attribution')
        contract='Pinned ValidateSet on explicit InstallSource rejects invalid before script entry.'
    else:
        require(values==[] and environment.get('SALAH_INSTALL_SOURCE')=='invalid',
            'Invalid environment control no longer exercises the default parameter')
        message='InstallSource (SALAH_INSTALL_SOURCE) must be ask, github, or store.'
        require(message in output and result['sourceException']==message,
            'Invalid environment exit lacks the exact source throw attribution')
        contract='Pinned explicit InstallSource validation throws before constants, function definitions or the first Write-Host.'
    require('Preview only; no changes made' not in output,'Early option refusal reported preview completion')
    return dict(verified=True,sourceSha256=PREVIEW_SOURCE_SHA,contract=contract,
        directExit=direct['entryExit'],heldExit=result['entryExit'],heldException=result['sourceException'],
        stdout=fact(direct['stdout']),stderr=fact(direct['stderr']))


def source_input_relation(pair, direct, held, result):
    """Join the actual source-read inputs and retain every full lifecycle row."""
    spec=pair['spec'];association=pair['association'];direct_root=Path(association['directRoot'])
    held_root=pair['root'];control=pair['control'];scenario=spec['scenario']
    require(spec['scope']=='product' and spec['guardMode']=='deny' and spec['sourceFact']['sha256']==PREVIEW_SOURCE_SHA
        and fact(spec['source'])==spec['sourceFact'],'Relation requires the exact unchanged reviewed complete source')
    require(direct.get('fixture')==str(direct_root) and direct.get('command')==association['directCommand']
        and direct_parameters(direct['command'],spec['host'],spec['source'])==spec['parameters'],
        'Direct command/fixture differs from the held typed association')
    launch=direct.get('directLaunchInputs',{})
    launch_path=direct_root/'direct-launch-inputs.json'
    require(complete_json(launch_path.read_bytes())==launch,'Direct original launch payload differs from its retained file')
    require(complete_json((control/'association.json').read_bytes())==association,
        'Prepared association differs from its complete retained payload')
    require(complete_json(pair['specPath'].read_bytes())==spec,'Held invocation spec differs from its retained payload')
    require(launch.get('command')==association['directCommand'] and launch.get('environment')==association['directEnvironment']
        and launch.get('cwd')==association['cwd'] and launch.get('sourceInventory')==association['sourceInventory'],
        'Direct original launch inputs differ from preparation')
    window=direct.get('profileWindow',{})
    require(complete_json((direct_root/'entry-profile-window/profile-window.json').read_bytes())==window,
        'Direct profile receipt is not its complete original payload')
    require(window.get('command')==association['directCommand'] and window.get('environment')==association['directEnvironment']
        and type(window.get('pid')) is int and window['pid']>0 and window.get('nonce')==association['directEnvironment']['INSTALL_READY_NONCE']
        and type(window.get('entryExit')) is int and window['entryExit']==direct['entryExit']
        and window.get('exitObserved') is True and window.get('timedOut') is False and window.get('error') is None,
        'Wrong or failed actual direct acquisition')
    for stream in ('stdout','stderr'):
        require(fact(direct_root/'entry-profile-window'/(stream+'.raw'))==window.get(stream)
            and Path(direct[stream]).read_bytes()==(direct_root/'entry-profile-window'/(stream+'.raw')).read_bytes(),
            'Direct raw capture differs from actual acquisition')
    early=scenario in ('bad-option','invalid-env-source')
    direct_ready=window.get('ready') is True
    require(direct_ready or early,'Discovery case has no actual direct readiness gate')
    phases={
        'directPrepared':(pair['directPrepared'],direct_root,control/'direct-after-directory-restoration.json'),
        'directPrelaunch':(direct['fullInputsBefore'],direct_root,direct_root/'direct-full-before-launch.json'),
        'directPostexit':(direct['fullInputsAfter'],direct_root,direct_root/'direct-full-after-exit.json'),
        'heldPrepared':(pair['heldPrepared'],held_root,control/'held-prepared.json'),
        'heldPrelaunch':(held['prelaunch'],held_root,control/'full-before-launch.json'),
        'heldModuleReady':(held['originalReady'],held_root,control/'full-at-original-ready.json'),
        'heldBefore':(held['before'],held_root,control/'before-invocation.json'),
        'heldAfter':(held['after'],held_root,control/'after-invocation.json'),
        'heldPostexit':(held['postexit'],held_root,control/'full-after-exit.json')}
    if direct_ready:
        require(direct.get('fullInputsAtReady')==window.get('fullReady'),'Direct ready inventories differ')
        phases['directReady']=(direct['fullInputsAtReady'],direct_root,direct_root/'entry-profile-window/full-at-ready.json')
        token=str(window['pid'])+'\t'+window['nonce']
        require(window.get('readyToken')==token,'Direct ready PID/nonce differs')
        for variable,field in (('INSTALL_READY_FILE','readyFact'),('INSTALL_PROFILE_ACK','ackFact')):
            path=Path(association['directEnvironment'][variable])
            require(path.read_bytes()==token.encode('utf-8') and fact(path)==window.get(field),'Unbound actual direct ready/ACK')
    else:
        require(window.get('ready') is False and window.get('atReady') is None and window.get('fullReady') is None
            and direct.get('fullInputsAtReady') is None,'Early refusal invents a direct discovery boundary')
        for variable in ('INSTALL_READY_FILE','INSTALL_PROFILE_ACK','R0016_MODULE_INPUT_PROOF'):
            require(not Path(association['directEnvironment'][variable]).exists(),'Unreceived direct early-refusal readiness/proof exists')
    phase_facts={};keyed={}
    for name,(value,root,path) in phases.items():
        diagnostic.validate_window(value,root,path)
        phase_facts[name]=fact(path);keyed[name]=validate_rows(value['rows'])
    require(phases['directPrelaunch'][0]['rows']==pair['directPrepared']['rows'],
        'Direct prepared inputs changed before actual launch')
    require(held['prelaunch']['rows']==pair['heldPrepared']['rows'],'Held prepared inputs changed before launch')
    verify_input_mapping(association['entries'],pair['directPrepared']['rows'],pair['heldPrepared']['rows'])
    require(held['before']['rows']==held['after']['rows'],'Entire unfiltered held invocation window changed')
    token=str(held['pid'])+'\t'+spec['nonce']
    require(held.get('originalReadyAcknowledged') is True and held.get('originalReadyToken')==token,
        'Distinct held original Utility readiness was not acknowledged')
    for variable,field in (('INSTALL_READY_FILE','originalReadyFact'),('INSTALL_PROFILE_ACK','originalAckFact')):
        path=Path(pair['env'][variable])
        require(path.read_bytes()==token.encode('utf-8') and fact(path)==held.get(field),'Unbound held original ready/ACK')
    for phase in ('before','after'):
        diagnostic.validate_gate(held,spec,phase)
    module_path=Path(pair['env']['R0016_MODULE_INPUT_PROOF']);before_path=Path(spec['beforeInputProof'])
    module=validate_child_read_context(complete_json(module_path.read_bytes()),pair,'held-module-startup',
        held['pid'],spec['nonce'],pair['heldPrepared'],held['originalReady'])
    before=validate_child_read_context(complete_json(before_path.read_bytes()),pair,'held-before-source',
        held['pid'],spec['nonce'],pair['heldPrepared'],held['before'])
    require(module['normalized']==before['normalized'],'Held module/before-source actual read context differs')
    direct_context=None;direct_path=None
    if direct_ready:
        direct_path=Path(association['directEnvironment']['R0016_MODULE_INPUT_PROOF'])
        direct_context=validate_child_read_context(complete_json(direct_path.read_bytes()),pair,'direct-pre-discovery',
            window['pid'],window['nonce'],pair['directPrepared'],direct['fullInputsAtReady'])
        require(direct_context['normalized']==before['normalized'],'Direct/held actual source-read context differs')
        bind_source_read_rows(direct_context['readContract'],pair['directPrepared']['rows'],direct['fullInputsAfter']['rows'])
    early_proof=early_option_refusal(pair,direct,result) if early else None
    # Every row and every physical field remains in the relation. Runtime-only
    # changes are visible here; they are not subtracted from the held window.
    names=('directPrepared','directPrelaunch','directReady','directPostexit','heldPrepared','heldPrelaunch',
        'heldModuleReady','heldBefore','heldAfter','heldPostexit')
    comparisons=(('directPrepared','directPrelaunch'),('directPrepared','heldPrepared'),
        ('directPrelaunch','directReady'),('directReady','directPostexit'),('directPrelaunch','directPostexit'),
        ('heldPrepared','heldPrelaunch'),('heldPrelaunch','heldModuleReady'),('heldModuleReady','heldBefore'),
        ('directReady','heldBefore'),('heldBefore','heldAfter'),('heldAfter','heldPostexit'))
    physical=[]
    for key in sorted(set().union(*(set(rows) for rows in keyed.values()))):
        values={name:keyed[name].get(key) if name in keyed else None for name in names}
        differences=[]
        for left,right in comparisons:
            if left not in keyed or right not in keyed:continue
            if values[left]!=values[right]:
                differences.append(dict(before=left,after=right,membershipChanged=(values[left] is None)!=(values[right] is None),
                    fields={field:dict(before=(values[left] or {}).get(field),after=(values[right] or {}).get(field))
                        for field in sorted(ROW_FIELDS) if (values[left] or {}).get(field)!=(values[right] or {}).get(field)}))
        physical.append(dict(role=key[0],path=key[1],phases=values,changes=differences))
    relation=dict(schema='r0016-entry-source-input-relation.v1',complete=True,
        mode='early-option-refusal' if early else 'discovery',sourceSha256=PREVIEW_SOURCE_SHA,
        directDiscoveryObserved=direct_ready,directProofFact=fact(direct_path) if direct_path is not None else None,
        heldModuleProofFact=fact(module_path),heldBeforeProofFact=fact(before_path),
        directLaunchFact=fact(launch_path),associationFact=fact(control/'association.json'),specFact=fact(pair['specPath']),
        directContext=direct_context,heldModuleContext=module,heldBeforeContext=before,
        actualReadContextEquivalent=True if direct_ready else None,heldReadContextEquivalent=True,
        earlyOptionRefusal=early_proof,entireHeldBeforeEqualsAfter=True,phaseFacts=phase_facts,
        absentPhases=[] if direct_ready else ['directReady'],physicalRows=physical,comparisons=[list(pair) for pair in comparisons],
        scope='Pinned-source input association; the ordered probe is a read-input control, not an installer call trace. All physical lifecycle fields remain retained.')
    save(control/'source-input-relation.json',relation)
    return relation


def prepare_pair(root, env, command, host_name, host, native_modules, source, core, window, driver, support, protect, scenario):
    require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: fixture preparation requires native Windows')
    require(fact(source)['sha256'] == PREVIEW_SOURCE_SHA, 'Preview relation is pinned to the reviewed complete source')
    root = Path(root).resolve(strict=True)
    require(scenario in SCENARIOS and scenario not in ('positive','no-open'), 'Unknown preview product scenario')
    paired = root / 'h'
    paired.mkdir()
    for name in ('subject', 'subject/temp', 'host-home'):
        (paired / name).mkdir(parents=True, exist_ok=True)
    protect(paired, host, native_modules, [paired, paired / 'subject', paired / 'subject/temp', paired / 'host-home'])
    control = paired / 'control'
    control.mkdir()
    before = double_inventory(root, support, control / 'direct-before-clone.json')
    for relative in ROLE_PATHS.values():
        original, copied = root / relative, paired / relative
        if original.is_dir():
            shutil.copytree(original, copied, dirs_exist_ok=True, copy_function=shutil.copy2)
        elif original.is_file():
            shutil.copy2(original, copied)
    # Reuse the exact published preparation-only repair and its full journal.
    before, copied = diagnostic.finish_prepared_clone(root, paired, control, before)
    mapping = map_inputs(before['rows'], copied['rows'])
    nonce = secrets.token_hex(16)
    held_env = mapped_environment(env, root, paired, nonce)
    copied_driver = control / 'held-driver.ps1'
    shutil.copy2(driver, copied_driver)
    probe = control / 'input-probe.ps1'
    shutil.copy2(env['R0016_INPUT_PROBE'], probe)
    guard, window_copy, helpers = extract_instrument(core, window, control)
    parameters = direct_parameters(command, host, source)
    require(any(row == {'name': 'DryRun', 'type': 'switch', 'value': True} for row in parameters), 'Held product call requires actual preview argv')
    spec = {'schema': 'r0016-entry-held-spec.v1', 'scenario': scenario, 'expectedHost': host_name,
            'scope': 'product', 'guardMode': 'deny', 'inputProbe': str(probe), 'probeFact': fact(probe),
            'beforeInputProof': str(control / 'held-before-inputs.json'),
            'host': str(host), 'nonce': nonce, 'source': str(source), 'sourceFact': fact(source),
            'driverFact': fact(copied_driver), 'guardSource': str(guard), 'guardFact': fact(guard),
            'windowSupport': str(window_copy), 'windowFact': fact(window_copy), 'effectHelpers': helpers,
            'parameters': parameters, 'events': str(control / 'events.jsonl'), 'result': str(control / 'result.json'),
            'beforeSignal': str(control / 'before.signal'), 'beforeAck': str(control / 'before.ack'),
            'afterSignal': str(control / 'after.signal'), 'afterAck': str(control / 'after.ack')}
    spec_path = control / 'spec.json'
    save(spec_path, spec)
    held_env['R0016_COMPOSITION_SPEC'] = str(spec_path)
    association = {'schema': 'r0016-entry-input-association.v1', 'directRoot': str(root), 'heldRoot': str(paired),
        'source': fact(source), 'directCommand': command, 'heldCommand': [str(host), '-NoProfile', '-File', str(copied_driver)],
        'sourceInventory': support.profile_snapshot(source),
        'parameters': parameters, 'cwd': str(Path.cwd().resolve()),
        'directEnvironment': dict(env), 'heldEnvironment': held_env, 'entries': mapping,
        'scenario': scenario, 'directoryPreparation': fact(control / 'directory-preparation.json'),
        'scope': 'All six prepared input roles; clone identity/creation facts explicitly mapped, all other fields equal.'}
    save(control / 'association.json', association)
    return {'root': paired, 'control': control, 'env': held_env, 'spec': spec, 'specPath': spec_path,
            'association': association, 'directPrepared': before, 'heldPrepared': copied}


def validate_held(receipt, result, expected, pair, direct_observation):
    require(receipt.get('schema') == 'r0016-entry-held-observation.v1', 'Wrong held observation schema')
    require(receipt.get('command') == expected['command'] and receipt.get('cwd') == expected['cwd'], 'Wrong held command or working directory')
    require(receipt.get('environment') == expected['heldEnvironment'], 'Wrong complete held launch environment')
    require(type(receipt.get('pid')) is int and receipt['pid'] > 0, 'Missing actual held PID')
    require(receipt.get('nonce') == expected['nonce'] and re.fullmatch(r'[0-9a-f]{32}', receipt['nonce']) is not None, 'Wrong held nonce')
    require(type(receipt.get('exit')) is int and receipt['exit'] == 0, 'Wrong wrapper process exit')
    require(receipt.get('exitObserved') is True and receipt.get('timedOut') is False and receipt.get('error') is None, 'Incomplete held process')
    elapsed = receipt.get('elapsedSeconds')
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < TIMEOUT and receipt.get('timeoutSeconds') == TIMEOUT, 'Unbounded or late held terminal receipt')
    require(receipt.get('capture') == 'direct files; no redirected pipe drain', 'Unproved capture completion')
    for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'specFact', 'stdout', 'stderr', 'resultFact', 'eventsFact'):
        require(receipt.get(field) == expected[field], 'Unbound held file fact: ' + field)
    for phase in ('prelaunch', 'before', 'after', 'postexit'):
        observed = receipt.get(phase)
        require(type(observed) is dict and observed.get('complete') is True and len(observed.get('passes', [])) == 2 and observed['passes'][0] == observed['passes'][1] == observed.get('rows'), 'Incomplete held ' + phase + ' inventory')
        require(observed.get('root') == expected['heldRoot'], 'Replayed or wrong full inventory root')
        validate_rows(observed['rows'])
    for phase in ('before', 'after'):
        require(receipt.get(phase + 'Token') == str(receipt['pid']) + '\t' + expected['nonce'] + '\t' + phase + '-invocation', 'Held phase token mismatch')
        require(receipt.get(phase + 'Acknowledged') is True, 'Held phase not acknowledged')
        for kind in ('SignalFact', 'AckFact'):
            require(receipt.get(phase + kind) == expected[phase + kind], 'Unbound phase signal/ack bytes')
    require(receipt['before']['rows'] == receipt['after']['rows'], 'Full held invocation changed owned inputs')
    require(receipt['prelaunch']['rows'] == expected['heldPreparedRows'], 'Prelaunch inputs differ from the prepared clone')
    # Product entry is joined through the complete source-bound actual read context.
    # No lifecycle row is removed and the entire held before/after equality above remains.
    receipt['sourceInputRelation'] = source_input_relation(pair, direct_observation, receipt, result)
    require(result.get('schema') == 'r0016-entry-held-result.v1' and type(result.get('pid')) is int and result['pid'] == receipt['pid'] and result.get('nonce') == expected['nonce'], 'Unbound held result')
    require(result.get('nativeWindows') is True and result.get('expectedHost') == expected['hostName'] and result.get('commandHost') == expected['host'], 'Wrong native host')
    if expected['hostName'] == 'ps51':
        require(result.get('hostEdition') == 'Desktop' and type(result.get('hostVersion')) is str and re.fullmatch(r'5\.1(?:\.\d+){0,2}', result['hostVersion']), 'Wrong Windows PowerShell version')
    else:
        require(expected['hostName'] == 'ps7' and result.get('hostEdition') == 'Core' and result.get('hostVersion') == '7.6.6', 'Wrong native PowerShell version')
    require(result.get('sourceFact') == expected['sourceFact'] and result.get('parameters') == expected['parameters'], 'Wrong source or typed invocation inputs')
    require(result.get('guardEstablished') is True and result.get('preparationError') is None and result.get('events') == [], 'Unproved denial or observed effects')
    require(type(result.get('methodInventory')) is list and bool(result['methodInventory']), 'Missing source breakpoint inventory')


def invoke_pair(pair, support, direct_observation):
    """Observe exact NEW driver with full snapshots. Native execution is caller-owned."""
    require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: held acquisition requires native Windows')
    root, control, env, spec = pair['root'], pair['control'], pair['env'], pair['spec']
    require(spec.get('scope') == 'product' and spec.get('guardMode') == 'deny', 'Product scope/guard mismatch')
    association = pair['association']
    expected_environment = mapped_environment(association['directEnvironment'], Path(association['directRoot']), root, spec['nonce'])
    expected_environment['R0016_COMPOSITION_SPEC'] = str(pair['specPath'])
    require(env == association['heldEnvironment'] == expected_environment, 'Launch environment differs from exhaustive mapping')
    require(direct_parameters(association['directCommand'], spec['host'], spec['source']) == spec['parameters'] == association['parameters'], 'Typed invocation differs from actual direct argv')
    require(support.profile_snapshot(spec['source']) == association['sourceInventory'], 'Source metadata changed before held launch')
    locks = {}
    receipt = {'schema': 'r0016-entry-held-observation.v1', 'command': association['heldCommand'],
        'cwd': association['cwd'], 'nonce': spec['nonce'], 'timeoutSeconds': TIMEOUT,
        'environment': dict(env),
        'capture': 'direct files; no redirected pipe drain', 'exitObserved': False,
        'timedOut': False, 'error': None, 'exit': None, 'before': None, 'after': None}
    started, process, failure = time.monotonic(), None, None
    try:
        if spec['scenario'] == 'unreadable':
            locked = support.NativeReadLock(env['INSTALL_UNREADABLE_FILE'], root)
            locks[os.path.normcase(str(locked.path))] = locked
            save(control / 'unreadable-held-before.json', locked.initial)
        receipt['prelaunch'] = double_inventory(root, support, control / 'full-before-launch.json', locks)
        require(receipt['prelaunch']['rows'] == pair['heldPrepared']['rows'], 'Prepared held inputs changed before launch')
        for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'probeFact'):
            require(fact(spec[field]['path']) == spec[field], 'Instrument/source changed before launch')
            receipt[field] = spec[field]
        receipt['specFact'] = fact(pair['specPath'])
        out, err = control / 'stdout.raw', control / 'stderr.raw'
        with out.open('wb') as stdout, err.open('wb') as stderr:
            process = subprocess.Popen(association['heldCommand'], cwd=association['cwd'], env=env,
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
            receipt['pid'] = process.pid
            while True:
                terminal = process.poll()
                elapsed = time.monotonic() - started
                if terminal is not None:
                    require(type(terminal) is int, 'Held process terminal is not an integer')
                    receipt.update(exit=terminal, exitObserved=True, elapsedSeconds=elapsed)
                if elapsed >= TIMEOUT:
                    receipt['timedOut'] = True
                    raise TimeoutError('Child or first terminal observation exceeded 60 seconds')
                if terminal is not None:
                    break
                # Original Utility module startup has a distinct late-ready gate;
                # accepting it never establishes the source invocation boundary.
                ready = Path(env['INSTALL_READY_FILE'])
                ack = Path(env['INSTALL_PROFILE_ACK'])
                token = str(process.pid) + '\t' + env['INSTALL_READY_NONCE']
                if ready.exists() and not ack.exists():
                    require(ready.read_text(encoding='utf-8-sig') == token, 'Original ready PID/nonce mismatch')
                    ready_clock = time.monotonic()
                    receipt['originalReady'] = double_inventory(root, support, control / 'full-at-original-ready.json', locks)
                    require(process.poll() is None and time.monotonic() - started < TIMEOUT
                            and time.monotonic() - ready_clock < 10, 'Original Utility ready observation exceeded its ACK deadline')
                    temporary = ack.with_name(ack.name + '.partial')
                    temporary.write_text(token, encoding='utf-8')
                    temporary.replace(ack)
                    receipt['originalReadyToken'] = token
                    receipt['originalReadyFact'], receipt['originalAckFact'] = fact(ready), fact(ack)
                    receipt['originalReadyAcknowledged'] = True
                phase = 'before' if receipt['before'] is None else 'after'
                signal = Path(spec[phase + 'Signal'])
                if receipt[phase] is None and signal.exists():
                    token = str(process.pid) + '\t' + spec['nonce'] + '\t' + phase + '-invocation'
                    require(signal.read_text(encoding='utf-8-sig') == token, 'Held phase PID/nonce mismatch')
                    gate_clock = time.monotonic()
                    receipt[phase] = double_inventory(root, support, control / (phase + '-invocation.json'), locks)
                    require(process.poll() is None and time.monotonic() - started < TIMEOUT and time.monotonic() - gate_clock < ACK_TIMEOUT, 'Child exited or held observation exceeded deadline')
                    ack_path = Path(spec[phase + 'Ack'])
                    temporary = ack_path.with_name(ack_path.name + '.partial')
                    temporary.write_text(token, encoding='utf-8')
                    temporary.replace(ack_path)
                    receipt[phase + 'Token'] = token
                    receipt[phase + 'Acknowledged'] = True
                    receipt[phase + 'SignalFact'] = fact(signal)
                    receipt[phase + 'AckFact'] = fact(ack_path)
                time.sleep(0.02)
        receipt['stdout'], receipt['stderr'] = fact(out), fact(err)
        receipt['postexit'] = double_inventory(root, support, control / 'full-after-exit.json', locks)
        receipt['eventsFact'] = fact(spec['events'])
        if spec['scope'] == 'source-free-diagnostic' and not Path(spec['result']).exists():
            # A causal debugger Stop may end a denied-effect child before the
            # semantic writer runs. Only the separate denied-control receiver
            # can interpret this absence; every healthy result requires it.
            receipt['resultFact'], receipt['resultMissing'] = None, True
            result = None
        else:
            receipt['resultFact'] = fact(spec['result'])
            result = complete_json(Path(spec['result']).read_bytes())
        if spec['scope'] != 'source-free-diagnostic':
            require(Path(spec['events']).read_bytes() == b'', 'Raw effects log is nonempty')
        if 'INSTALL_UNREADABLE_FILE' in env:
            proof_path = Path(env['INSTALL_UNREADABLE_PROOF'])
            proof = complete_json(proof_path.read_bytes())
            require(type(proof.get('pid')) is int and proof['pid'] == process.pid and proof.get('nonce') == spec['nonce'] and proof.get('path') == env['INSTALL_UNREADABLE_FILE'], 'Held metadata proof has wrong PID/nonce/path')
            require(proof.get('exists') is True and proof.get('peerReadable') is True and proof.get('peerSha256') == env['INSTALL_METADATA_SHA'], 'Held metadata existence/readable peer control failed')
            if locks:
                require(proof.get('readSucceeded') is False and proof.get('nativeCode') == 32 and proof.get('exceptionType') == 'System.IO.IOException', 'Held child did not prove native read refusal')
            else:
                require(proof.get('readSucceeded') is True and proof.get('nativeCode') is None and proof.get('targetSha256') == env['INSTALL_METADATA_SHA'], 'Held readable counterpart failed')
            receipt['metadataProof'], receipt['metadataProofFact'] = proof, fact(proof_path)
        expected = dict(receipt, command=association['heldCommand'], cwd=association['cwd'], nonce=spec['nonce'],
            hostName=spec['expectedHost'], host=spec['host'], parameters=spec['parameters'], heldEnvironment=expected_environment, heldRoot=str(root), heldPreparedRows=pair['heldPrepared']['rows'])
        # Expected facts above come from actual closed capture files and frozen
        # prelaunch inputs, not from self-declared report values.
        for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'probeFact'):
            require(fact(spec[field]['path']) == spec[field], 'Instrument/source changed while child ran')
        require(fact(pair['specPath']) == receipt['specFact'], 'Invocation spec changed while child ran')
        require(support.profile_snapshot(spec['source']) == association['sourceInventory'], 'Source metadata changed while child ran')
        if spec['scope'] != 'source-free-diagnostic':
            validate_held(receipt, result, expected, pair, direct_observation)
        return {'observation': receipt, 'result': result, 'association': association}
    except BaseException as error:
        failure = error
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        cleanup_error = finish_owned_acquisition(process, locks, root, control, support, receipt, failure)
        if cleanup_error is not None and failure is None:
            raise cleanup_error

