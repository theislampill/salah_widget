#!/usr/bin/env python3
"""Focused original Windows positive/NoOpen path discriminator; two cases only.

The unchanged native entry harness owns its original assertions. The reviewed
Job helper bounds process lifetime; it is not a filesystem/network sandbox.
No All75, mutation campaign or direct-preview composition is executed here.
"""
from __future__ import annotations
import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import ntpath
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import tarfile
import threading
import time
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode=True
SUPPORT_SHA='9becda7102411dbef9a29efe5e5be95b9e02711563f3b845d496597011ff871b'
HELPER_SHA='6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
ROOT_PREFIX='r16-normal-'
OUTER_SECONDS=600
VERSION_SECONDS=60
ENTRY_SECONDS=60
INPUTS={
    'install.ps1':'7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4',
    'presets/salah-widget.tablissng.json':'9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f',
    'tests/install-entry-native.py':'223b8ed54b342c23e7d0380bc669072a5fd87f2e42eeadb276b024aa8aa29819',
    'tools/qualification/installer_preview_host_probe.py':HELPER_SHA,
    'tools/qualification/installer_preview_windows_carrier.py':SUPPORT_SHA,
}
WIDGET_HASH='lat=24.47&lon=39.61&method=4'
RELEASE_URL='https://api.github.com/repos/BookCatKid/TablissNG/releases/latest'
DOWNLOAD_URLS=['https://example.invalid/chromium','https://example.invalid/firefox','https://example.invalid/preset']
OPEN_URLS=['chrome://extensions/ ','chrome://newtab/ ','about:addons ','about:newtab ']
PS51_LITERAL=r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe'
PS7_SHA='bfb46af89433268872ddb43d1ca7a3f433452ee91ed356a9786940f90118e285'
VERSION_CODE="[Console]::Write(('{0}|{1}|{2}' -f $PSVersionTable.PSVersion,$PSVersionTable.PSEdition,[Environment]::OSVersion.Platform))"

def load_exact(path,digest,name):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Pinned Python input differs')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

# Only pure custody/JSON helpers are used; this module's native main is never run.
R=load_exact(Path(__file__).with_name('installer_preview_windows_carrier.py'),SUPPORT_SHA,'r16_normal_support')
Rejected=R.Rejected
require,save,file_fact,verify_fact=R.require,R.save,R.file_fact,R.verify_fact
checked_path,strict_json,utc=R.checked_path,R.strict_json,R.utc

def path_budget(root,host):
    """All explicit constructors for the pinned one-manifest normal fixture."""
    require(host in ('ps51','ps7'),'Unknown host')
    token='0'*32;rows=[]
    for scenario in ('positive','no-open'):
        fixture=ntpath.join(str(root),'s','temp','salah native entry-'+'0'*8,host+'-'+scenario)
        temporary=ntpath.join(fixture,'subject','temp')
        compiler=ntpath.join(temporary,'SalahWidgetCompiler-'+token)
        scratch=ntpath.join(temporary,'SalahWidgetAttempt-'+token)
        retained=ntpath.join(fixture,'host-home','SalahWidgetBundle-'+token)
        downloads=ntpath.join(retained,'downloads');presets=ntpath.join(retained,'presets')
        unpacked=ntpath.join(retained,'unpacked-'+token)
        directories={'compiler-directory':compiler,'scratch-directory':scratch,'retained-directory':retained,
                     'downloads-directory':downloads,'presets-directory':presets,'unpacked-directory':unpacked}
        files={
            'compiler-source':ntpath.join(compiler,'native.cs'),'compiler-dll':ntpath.join(compiler,'native.dll'),
            'compiler-stdout':ntpath.join(compiler,'compiler.stdout.bin'),'compiler-stderr':ntpath.join(compiler,'compiler.stderr.bin'),
            'scratch-download':ntpath.join(scratch,'download-'+token+'.partial'),
            'scratch-preset':ntpath.join(scratch,'preset-'+token+'.partial'),
            'download-publication-partial':ntpath.join(downloads,token+'.partial'),
            'preset-publication-partial':ntpath.join(presets,token+'.partial'),
            'retained-chromium':ntpath.join(downloads,token+'-tabliss-chromium.zip'),
            'retained-firefox':ntpath.join(downloads,token+'-tabliss-firefox-signed.xpi'),
            'retained-preset':ntpath.join(presets,token+'-salah-widget.tablissng.json'),
            'unpacked-manifest':ntpath.join(unpacked,'manifest.json'),
        }
        for typ,values,ceiling in [('directory',directories,248),('file',files,260)]:
            for name,path in values.items():
                rows.append(dict(scenario=scenario,constructor=name,type=typ,modeledPath=path,
                                 utf16Units=len(path.encode('utf-16-le'))//2,limitExclusive=ceiling))
    return rows

def admit_path_budget(rows):
    require(len(rows)==36 and all(type(r['utf16Units']) is int and r['utf16Units']<r['limitExclusive'] for r in rows),
            'Explicit native path budget does not fit before runtime launch')

def build_command(inputs,python,host):
    return [str(python),'-B',inputs['tests/install-entry-native.py']['path'],inputs['install.ps1']['path'],
            '--host',host,'--scenario','positive','--scenario','no-open','--preset',inputs['presets/salah-widget.tablissng.json']['path']]

def child_command(executable,source,scenario):
    require(scenario in ('positive','no-open'),'Unexpected scenario')
    command=[str(executable),'-NoProfile','-File',str(source),'-PresetUrl',DOWNLOAD_URLS[2],
             '-InstallSource','github','-WidgetHash',WIDGET_HASH]
    return command+(['-NoOpen'] if scenario=='no-open' else [])

def validate_host_text(text,host):
    require(host in ('ps7','ps51'),'Unexpected native host selector')
    require(isinstance(text,str) and (text=='7.6.6|Core|Win32NT' if host=='ps7' else
            bool(re.fullmatch(r'5\.1\.\d+\.\d+\|Desktop\|Win32NT',text))), 'Native version/edition/platform differs')

def validate_terminal(process,command,capture,budget):
    require(isinstance(process,dict) and process.get('command')==command,'Actual outer command differs')
    require(type(process.get('exit')) is int and process['exit']==0,'Outer terminal is not integer zero')
    for key in ('exitObserved','jobAssignedBeforeResume','jobClosedKillOnClose'):
        require(process.get(key) is True,'Missing outer lifecycle observation: '+key)
    require(process.get('timedOut') is False and process.get('error','missing') is None,'Outer timeout or process error')
    require(type(process.get('timeoutSeconds')) is int and process['timeoutSeconds']==budget and
            R.finite_elapsed(process.get('elapsedSeconds'),budget),'Outer deadline differs')
    require(type(process.get('processId')) is int and process['processId']>0,'Missing outer PID')
    require(process.get('capture')=='direct files; no redirected pipe drain' and process.get('drain')=='not applicable','Outer capture protocol differs')
    return [verify_fact(process.get(k),capture/('observer.'+k+'.raw'),capture) for k in ('stdout','stderr')]

def run_phase(helper,command,environment,state,capture,budget):
    helper.save_required_snapshot(state,capture/'state.before.json')
    finished=threading.Event();outcome={}
    def worker():
        try:outcome['process']=helper.run_observer(command,environment,capture,budget)
        except BaseException as error:outcome['error']=error
        finally:finished.set()
    thread=threading.Thread(target=worker,daemon=True);start=time.monotonic();thread.start()
    while not finished.wait(30):
        print(json.dumps(dict(event='phase-running',elapsedSeconds=round(time.monotonic()-start,3),timeoutSeconds=budget)),flush=True)
    thread.join()
    # Every post-exit change remains visible, including startup and fixture data.
    helper.save_required_snapshot(state,capture/'state.after.json')
    if 'error' in outcome:raise outcome['error']
    return outcome['process']

def case_rows(rows):
    require(isinstance(rows,list) and len(rows)==2 and all(isinstance(r,dict) for r in rows),'Exactly two original cases required')
    names=[r.get('case') for r in rows]
    require(names==['positive','no-open'],'Case identity/order is missing, duplicated or unexpected')
    return {r['case']:r for r in rows}

def check_effects(effects,no_open,clipboard,opens):
    by_kind=collections.defaultdict(list)
    for row in effects:
        require(isinstance(row,list) and len(row)==2 and all(isinstance(v,str) for v in row),'Malformed raw effect row')
        require(row[0] in ('metadata','download','clipboard','open','prompt','mkdir','remove','extract'),'Unknown effect kind')
        by_kind[row[0]].append(row[1])
    require(by_kind['metadata']==[RELEASE_URL],'Wrong release lookup/count')
    require(collections.Counter(by_kind['download'])==collections.Counter(DOWNLOAD_URLS),'Wrong download URLs/counts')
    require(collections.Counter(by_kind['clipboard'])==collections.Counter(clipboard),'Wrong copied paths/counts')
    require(not by_kind['extract'],'Native extractor unexpectedly called Expand-Archive')
    require(len(by_kind['prompt'])==3,'Original selection/manual confirmations missing')
    require(collections.Counter(by_kind['open'])==collections.Counter(opens) and opens==([] if no_open else OPEN_URLS),
            'Wrong manager/newtab opens or store fallback')

def normal_outputs(case,owner):
    home=checked_path(case/'host-home',owner,directory=True)
    bundles=list(home.glob('SalahWidgetBundle-*'))
    require(len(bundles)==1 and re.fullmatch(r'SalahWidgetBundle-[0-9a-f]{32}',bundles[0].name),'Exactly one retained bundle required')
    bundle=checked_path(bundles[0],owner,directory=True)
    unpacked=list(bundle.glob('unpacked-*'))
    xpis=list((bundle/'downloads').glob('*-tabliss-firefox-signed.xpi'))
    presets=list((bundle/'presets').glob('*-salah-widget.tablissng.json'))
    require(len(unpacked)==len(xpis)==len(presets)==1,'Admitted outputs missing or ambiguous')
    unpacked=checked_path(unpacked[0],owner,directory=True);xpi=checked_path(xpis[0],owner);preset=checked_path(presets[0],owner)
    manifest=checked_path(unpacked/'manifest.json',owner)
    configured=strict_json(preset)
    frame=ET.fromstring(configured['data/orpul7IDXSSP']['input'])
    require(frame.tag=='iframe' and frame.attrib.get('src')=='https://theislampill.github.io/salah_widget/#'+WIDGET_HASH,
            'Canonical configured preset not consumed')
    require(not list((case/'subject/temp').glob('SalahWidgetAttempt-*')),'Owned scratch remains')
    return [str(unpacked),str(xpi),str(preset),str(preset)],[file_fact(p,owner) for p in (manifest,xpi,preset)]

def validate_acl_records(case,fixture):
    def pairs(items):
        value={}
        for key,item in items:
            require(key not in value,'Duplicate ACL record key');value[key]=item
        return value
    captures=[]
    for name in ('parent-acl-before.json','parent-acl-after.json'):
        rows=json.loads((case/name).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
        require(isinstance(rows,list) and rows and all(isinstance(r,dict) for r in rows),'Malformed ACL capture')
        require(all(isinstance(r.get('path'),str) and isinstance(r.get('sddl'),str) and r['sddl'] for r in rows),'Missing ACL path/SDDL')
        by_path={r['path']:r for r in rows};require(len(by_path)==len(rows),'Duplicate ACL path')
        captures.append(by_path)
    before,after=captures;require(set(before)==set(after),'ACL path set changed')
    owned={str(p) for p in (fixture,case,case/'subject',case/'subject/temp',case/'host-home')}
    require(owned<=set(after),'Owned ACL premise is incomplete')
    sid=after[str(fixture)].get('owner');require(isinstance(sid,str) and sid.startswith('S-1-'),'Owned ACL SID missing')
    for path,row in after.items():
        if path in owned:
            rules=row.get('rules')
            require(row.get('owner')==sid and row.get('protected') is True and isinstance(rules,list) and len(rules)==1 and
                    rules[0].get('sid')==sid and rules[0].get('type')=='Allow' and type(rules[0].get('rights')) is int and
                    rules[0]['rights']==0x1f01ff,'Owned parent ACL readback differs')
        else:require(before[path]['sddl']==row['sddl'],'Existing ancestor ACL changed')

def validate_original_pair(value,inputs,host,entry_executable,temp,owner):
    require(isinstance(value,dict) and value.get('source')==inputs['install.ps1']['sha256'] and
            value.get('preset')==inputs['presets/salah-widget.tablissng.json']['sha256'],'Original source/preset association differs')
    require(value.get('selectedHosts')==[host] and value.get('selectedScenarios')==['positive','no-open'],'Original selection differs')
    fixture=checked_path(value.get('fixture'),temp,directory=True)
    require(fixture.parent==temp and re.fullmatch(r'salah native entry-[a-z0-9_]{8}',fixture.name),'Original fixture is not the expected direct temp child')
    require([p for p in temp.iterdir() if re.fullmatch(r'salah native entry-[a-z0-9_]{8}',p.name)]==[fixture],'Duplicate original fixtures')
    tree=ast.parse(Path(inputs['tests/install-entry-native.py']['path']).read_bytes())
    modules=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and
             any(isinstance(t,ast.Name) and t.id=='MODULE' for t in n.targets)]
    manifests=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and
               n.value.startswith("@{RootModule='Microsoft.PowerShell.Utility.psm1';")]
    require(len(modules)==len(manifests)==1,'Pinned original module literals missing or duplicated')
    rows=case_rows(value.get('results'));facts=[];pids=[];nonces=[]
    for scenario,row in rows.items():
        require(row.get('host')==host and row.get('pass_') is True and 'error' not in row,'Original normal assertion did not pass')
        observed=row.get('observation');require(isinstance(observed,dict),'Missing original observation')
        case=checked_path(fixture/(host+'-'+scenario),owner,directory=True)
        require(observed.get('fixture')==str(case) and observed.get('command')==child_command(entry_executable,inputs['install.ps1']['path'],scenario),'Native case/argv differs')
        require(type(observed.get('entryExit')) is int and observed['entryExit']==0 and observed.get('interceptionLoaded') is True,'Native exit/readiness differs')
        require(type(observed.get('timeoutSeconds')) is int and observed['timeoutSeconds']==ENTRY_SECONDS and
                R.finite_elapsed(observed.get('elapsedSeconds'),OUTER_SECONDS),'Original entry budget/elapsed observation differs')
        # Original elapsed is sampled after capture/snapshot work, not at the
        # native terminal boundary. The outer Job supplies its bounded lifetime.
        nonce=observed.get('readinessNonce');require(isinstance(nonce,str) and re.fullmatch(r'[0-9a-f]{32}',nonce),'Bad readiness nonce')
        ready=(case/'ready').read_text(encoding='utf-8-sig').split('\t')
        require(len(ready)==2 and ready[0].isdigit() and int(ready[0])>0 and ready[1]==nonce,'Raw readiness PID/nonce differs')
        pids.append(int(ready[0]));nonces.append(nonce)
        raw={}
        for kind in ('stdout','stderr'):
            path=case/(kind+'.txt');require(observed.get(kind)==str(path),'Raw capture path differs')
            facts.append(file_fact(path,owner));raw[kind]=path.read_bytes()
        effects=[line.split('\t',1) for line in (case/'effects').read_text(encoding='utf-8-sig').splitlines()]
        require(effects==observed.get('effects'),'Reported effects differ from raw capture')
        module=case/'modules/Microsoft.PowerShell.Utility'
        require((module/'Microsoft.PowerShell.Utility.psm1').read_text(encoding='ascii')==modules[0] and
                (module/'Microsoft.PowerShell.Utility.psd1').read_text(encoding='ascii')==manifests[0],
                'Generated original spy module differs from pinned harness')
        require(file_fact(case/'canonical-preset.json',owner)['sha256']==inputs['presets/salah-widget.tablissng.json']['sha256'],
                'Original case preset fixture differs')
        validate_acl_records(case,fixture)
        with zipfile.ZipFile(case/'fixture.zip') as archive:
            require(archive.namelist()==['manifest.json'] and archive.testzip() is None and
                    archive.read('manifest.json')==b'{"manifest_version":3,"name":"Fixture","version":"1.0"}',
                    'Original asset fixture differs')
        clips,outputs=normal_outputs(case,owner);facts+=outputs
        check_effects(effects,scenario=='no-open',clips,[] if scenario=='no-open' else OPEN_URLS)
        require('Manual browser installation/import remain pending' in raw['stdout'].decode('utf-8',errors='replace'),'Manual-pending wording missing')
        for name in ('ready','effects','bootstrap-phases.txt','subject-before.json','subject-after.json','parent-acl-before.json','parent-acl-after.json',
                     'parent-acl-setup.stdout.txt','parent-acl-setup.stderr.txt','fixture.zip','canonical-preset.json',
                     'modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psm1','modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1'):
            facts.append(file_fact(case/name,owner))
    require(len(set(nonces))==2,'Replayed readiness nonce')
    # Sequential native processes can reuse a PID; freshness comes from the
    # independent nonce and actual original invocation/terminal association.
    return dict(fixture=str(fixture),cases=list(rows),nativeEntries=2,readinessPids=pids,custodyFiles=facts)

def environment(helper,state,executable,host):
    env=helper.environment_for(state,executable,os.environ,False)
    env['POWERSHELL_UPDATECHECK']='Off'
    if host=='ps7':env['INSTALL_TEST_PS7']=str(executable)
    require(not any(k.upper()=='COMPLUS_MULTICOREJITNOPROFILEGATHER' for k in env),'Default gather changed')
    helper.prepare_environment(env)
    return env

def archive_owned_root(parent,archive):
    parent=checked_path(parent,directory=True);roots=list(parent.glob(ROOT_PREFIX+'*'))
    require(len(roots)==1 and re.fullmatch(ROOT_PREFIX+r'[0-9a-f]{16}',roots[0].name),'Exactly one unambiguous owned normal root required')
    root=checked_path(roots[0],parent,directory=True);archive=Path(archive)
    require(archive.is_absolute() and archive.parent==parent and not archive.exists(),'Invalid or occupied archive destination')
    with tarfile.open(archive,'x:gz',dereference=False) as output:
        pending=[root]
        while pending:
            path=pending.pop();info=path.lstat();name='installer-evidence'+('' if path==root else '/'+path.relative_to(root).as_posix())
            if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                entry=tarfile.TarInfo(name);entry.type=tarfile.SYMTYPE;entry.linkname=os.readlink(path)
                entry.mode=stat.S_IMODE(info.st_mode);entry.mtime=int(info.st_mtime);output.addfile(entry)
            else:
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),'Unsupported special evidence member')
                output.add(path,arcname=name,recursive=False)
                if stat.S_ISDIR(info.st_mode):pending.extend(sorted(path.iterdir(),reverse=True))
    return str(archive)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('ps51','ps766'));parser.add_argument('--powershell',type=Path)
    parser.add_argument('--output-parent',type=Path,required=True);parser.add_argument('--source-commit')
    parser.add_argument('--archive-only',action='store_true');parser.add_argument('--archive',type=Path)
    args=parser.parse_args(argv)
    if os.name!='nt':parser.error('Native Windows required; no runtime was started')
    parent=checked_path(args.output_parent,directory=True)
    require(parent==checked_path(os.environ['USERPROFILE'],directory=True) and parent.drive.lower()=='c:',
            'Actual system-volume USERPROFILE parent required')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None and args.source_commit is None,'Invalid archive-only arguments')
        print(archive_owned_root(parent,args.archive));return 0
    require(args.host is not None and args.powershell is not None and args.archive is None and
            isinstance(args.source_commit,str) and re.fullmatch(r'[0-9a-f]{40}',args.source_commit),'Exact source and host are required')
    host='ps7' if args.host=='ps766' else 'ps51'
    executable=checked_path(args.powershell);python=checked_path(Path(sys.executable).resolve())
    if host=='ps7':
        fact=file_fact(executable)
        require(fact['bytes']==301368 and fact['sha256']==PS7_SHA,'Exact portable PowerShell 7.6.6 executable differs')
    entry_executable=str(executable) if host=='ps7' else PS51_LITERAL
    require(Path(entry_executable).resolve(strict=True)==executable,'Original entry host does not resolve to selected executable')
    root=parent/(ROOT_PREFIX+secrets.token_hex(8));root.mkdir()
    result=dict(schema='r0016-windows-normal-path.v1',status='ACQUISITION_INCOMPLETE',fixture=str(root),sourceCommit=args.source_commit,
                expectedHost=host,nativeNormalBaselineAccepted=False,coreRowsExecuted=0,mutantRowsExecuted=0,directPreviewRowsExecuted=0,
                nativeNormalCasesExpected=2,independentHardContainment='NOT_ACQUIRED',phases={},sourceAndInputsUnchanged=False)
    save(root/'route-result.json',result)
    originals=[];copied={};fixed=[];status=2
    try:
        source=Path(__file__).resolve();repo=source.parents[2];control=root/'control';control.mkdir()
        roles=dict(INPUTS);roles['tools/qualification/installer_preview_windows_normal_probe.py']=file_fact(source)['sha256']
        for role,digest in roles.items():
            fact=file_fact(repo/role);require(fact['sha256']==digest,'Input role hash differs: '+role)
            destination=control/role;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fact['path'],destination)
            copied[role]=file_fact(destination,root)
            require((copied[role]['bytes'],copied[role]['sha256'])==(fact['bytes'],fact['sha256']),'Copied input differs')
            originals.append(fact)
        fixed=originals+list(copied.values())+[file_fact(executable),file_fact(python)]
        helper=load_exact(copied['tools/qualification/installer_preview_host_probe.py']['path'],HELPER_SHA,'r16_normal_host_helper')
        budgets=path_budget(root,host);save(root/'path-budget.json',dict(host=host,rows=budgets));admit_path_budget(budgets)
        # Separate prepared state prevents the version query from warming the
        # actual pair's owned startup profile. Both precede selected PS startup.
        version=root/'version';version.mkdir();run=root/'run';run.mkdir()
        version_state=version/'state';state=root/'s'
        version_env=environment(helper,version_state,executable,host);pair_env=environment(helper,state,executable,host)
        version_command=[str(executable),'-NoProfile','-NonInteractive','-Command',VERSION_CODE]
        command=build_command(copied,python,host)
        plan=dict(schema='r0016-windows-normal-path-plan.v1',sourceCommit=args.source_commit,preparedUtc=utc(),root=str(root),
                  expectedHost=host,host=file_fact(executable),python=file_fact(python),entryExecutableLiteral=entry_executable,
                  originals=originals,copiedInputs=copied,version=dict(command=version_command,environment=version_env,timeoutSeconds=VERSION_SECONDS),
                  normal=dict(command=command,environment=pair_env,timeoutSeconds=OUTER_SECONDS,entryTimeoutSeconds=ENTRY_SECONDS),
                  pathBudget=file_fact(root/'path-budget.json',root),noGatherOverride=False,
                  scope='Only original positive and NoOpen; Job lifetime is not filesystem/network containment')
        save(root/'plan.json',plan)
        process=run_phase(helper,version_command,version_env,version_state,version,VERSION_SECONDS)
        result['phases']['version']=process;save(root/'route-result.json',result)
        validate_terminal(process,version_command,version,VERSION_SECONDS)
        require((version/'observer.stderr.raw').read_bytes()==b'','Host query stderr is nonempty')
        text=(version/'observer.stdout.raw').read_bytes().decode('utf-8-sig');validate_host_text(text,host)
        result['nativeHost']=dict(versionEditionPlatform=text,executable=file_fact(executable),command=version_command)
        for fact in fixed:verify_fact(fact,Path(fact['path']))
        process=run_phase(helper,command,pair_env,state,run,OUTER_SECONDS)
        result['phases']['normal']=process;save(root/'route-result.json',result)
        validate_terminal(process,command,run,OUTER_SECONDS)
        value=strict_json(run/'observer.stdout.raw')
        association=validate_original_pair(value,copied,host,entry_executable,Path(pair_env['TEMP']),root)
        result.update(status='ACQUIRED_ORIGINAL_NORMAL_PAIR',nativeNormalBaselineAccepted=True,normal=association)
        status=0
    except Exception as error:
        result.update(status='ACQUISITION_OR_ORIGINAL_NORMAL_NOT_ADMITTED',error=type(error).__name__+': '+str(error))
    finally:
        try:
            require(bool(fixed),'Complete launch custody was not established')
            for fact in fixed:verify_fact(fact,Path(fact['path']))
            result['sourceAndInputsUnchanged']=True
        except Exception as error:
            result.update(status='INPUT_CUSTODY_FAILED',nativeNormalBaselineAccepted=False,sourceAndInputsUnchanged=False,
                          custodyError=type(error).__name__+': '+str(error));status=2
        save(root/'route-result.json',result)
    print(json.dumps(result,indent=2));return status

if __name__=='__main__':raise SystemExit(main())
