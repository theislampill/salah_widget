#!/usr/bin/env python3
"""Direct native -File entry with private startup spies; no owner profile is used."""
import argparse, base64, collections, datetime, hashlib, json, os, pathlib, secrets, subprocess, sys, tempfile, time, zipfile
import xml.etree.ElementTree as ET
import importlib.util
SUPPORT_PATH = pathlib.Path(__file__).with_name('install-entry-coverage-support.py')
support_spec = importlib.util.spec_from_file_location('r0016_entry_coverage_support', SUPPORT_PATH)
support = importlib.util.module_from_spec(support_spec)
support_spec.loader.exec_module(support)
LOCKS = {}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=pathlib.Path, nargs='?', default=pathlib.Path(__file__).resolve().parents[1]/'install.ps1')
parser.add_argument('--host', action='append', choices=('ps51','ps7'))
SCENARIOS = ('github','cached','store','ask','installed','mixed','legacy','none','missing-preset','bad-option','positive','no-open','readable','unreadable')
parser.add_argument('--scenario', action='append', choices=SCENARIOS)
parser.add_argument('--preset', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1]/'presets/salah-widget.tablissng.json')
args = parser.parse_args()
SOURCE = args.source.resolve()
PRESET = args.preset.resolve()
SOURCE_HASH_BEFORE = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
ENTRY_TIMEOUT_SECONDS = 60  # Native PS5.1 cold readiness alone measured 19.615-22.770s.
PS7 = os.environ.get('INSTALL_TEST_PS7', r'C:\Program Files\PowerShell\7\pwsh.exe')
HOSTS = [('ps51', r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe', r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\Modules'),
         ('ps7', PS7, str(pathlib.Path(PS7).parent/'Modules'))]
ROOT = pathlib.Path(tempfile.mkdtemp(prefix='salah native entry-')).resolve()
RESULTS = []
MODULE = r'''
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'utility-wrapper-entered'+[Environment]::NewLine)
Import-Module $env:INSTALL_NATIVE_UTILITY -Scope Local
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'native-utility-imported'+[Environment]::NewLine)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'output-encoding-set'+[Environment]::NewLine)
# The native host can restore Windows ProgramFiles locations at startup.
# Set the discovery roots in this private child session before Get-Targets.
$env:ProgramFiles=$env:INSTALL_FIXTURE_PF
${env:ProgramFiles(x86)}=$env:INSTALL_FIXTURE_PF86
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'discovery-environment-set'+[Environment]::NewLine)
function Record([string]$Kind,[string]$Value) { [IO.File]::AppendAllText($env:INSTALL_EFFECT_LOG,$Kind+"`t"+$Value+[Environment]::NewLine) }
function In-Fixture([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if(-not $full.StartsWith(($env:INSTALL_SUBJECT_ROOT+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){ throw ('Effect escaped fixture: '+$full) }
}
function Write-Host { param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline,[object]$Separator=' ')
    $text=(@($Object) -join $Separator); if($NoNewline){[Console]::Write($text)}else{[Console]::WriteLine($text)}
}
function New-Item { param($ItemType,$Path,[switch]$Force)
    foreach($p in @($Path)){ In-Fixture $p; Record 'mkdir' $p }
    Microsoft.PowerShell.Management\New-Item -ItemType $ItemType -Path $Path -Force:$Force
}
function Remove-Item { param($LiteralPath,[switch]$Recurse,[switch]$Force)
    In-Fixture $LiteralPath; Record 'remove' $LiteralPath
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Recurse:$Recurse -Force:$Force
}
function Invoke-RestMethod { param($Uri,$Headers)
    Record 'metadata' $Uri
    if($env:INSTALL_FIXTURE_NORMAL -ne '1'){throw 'Denied fixture network'}
    [pscustomobject]@{tag_name='v-fixture';assets=@(
        [pscustomobject]@{name='tabliss-chromium.zip';browser_download_url='https://example.invalid/chromium'},
        [pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/firefox'})}
}
function Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing)
    Record 'download' $Uri; In-Fixture $OutFile
    if($env:INSTALL_FIXTURE_NORMAL -ne '1'){throw 'Denied fixture network'}
    if($Uri -eq 'https://example.invalid/preset'){[IO.File]::Copy($env:INSTALL_PRESET_FIXTURE,$OutFile,$true)}
    else{[IO.File]::Copy($env:INSTALL_ASSET_ZIP,$OutFile,$true)}
}
function Expand-Archive { param($LiteralPath,$DestinationPath,[switch]$Force)
    In-Fixture $LiteralPath; In-Fixture $DestinationPath; Record 'extract' $LiteralPath
    Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $LiteralPath -DestinationPath $DestinationPath -Force:$Force
}
function Set-Clipboard { param($Value) Record 'clipboard' $Value }
function Start-Process { param($FilePath,$ArgumentList) Record 'open' ($FilePath+' '+$ArgumentList) }
function Read-Host { param($Prompt) Record 'prompt' $Prompt; if($Prompt -like 'Select target*'){return 'all'}; return '' }
Export-ModuleMember -Function Write-Host,New-Item,Remove-Item,Invoke-RestMethod,Invoke-WebRequest,Expand-Archive,Set-Clipboard,Start-Process,Read-Host -Cmdlet *
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'all-spies-exported'+[Environment]::NewLine)
if($env:INSTALL_UNREADABLE_FILE) {
    $probe=[ordered]@{pid=$PID;nonce=$env:INSTALL_READY_NONCE;path=$env:INSTALL_UNREADABLE_FILE;exists=[IO.File]::Exists($env:INSTALL_UNREADABLE_FILE);readSucceeded=$false;nativeCode=$null;exceptionType=$null;targetSha256=$null;peerReadable=$false;peerSha256=$null}
    try {
        $null=[IO.File]::ReadAllText($env:INSTALL_UNREADABLE_FILE);$probe.readSucceeded=$true
        $targetBytes=[IO.File]::ReadAllBytes($env:INSTALL_UNREADABLE_FILE);$targetHasher=[Security.Cryptography.SHA256]::Create()
        try {$probe.targetSha256=([BitConverter]::ToString($targetHasher.ComputeHash($targetBytes))).Replace('-','').ToLowerInvariant()}finally{$targetHasher.Dispose()}
    }
    catch { $cause=$_.Exception.GetBaseException();$probe.nativeCode=($cause.HResult -band 65535);$probe.exceptionType=$cause.GetType().FullName }
    try {
        $peer=[IO.File]::ReadAllBytes($env:INSTALL_READABLE_PEER)
        $hasher=[Security.Cryptography.SHA256]::Create()
        try {$probe.peerSha256=([BitConverter]::ToString($hasher.ComputeHash($peer))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
        $probe.peerReadable=$probe.peerSha256 -ceq $env:INSTALL_METADATA_SHA
    } catch { $probe.peerError=$_.Exception.GetBaseException().Message }
    [IO.File]::WriteAllText($env:INSTALL_UNREADABLE_PROOF,($probe|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
}
$readyToken=[string]$PID+"`t"+$env:INSTALL_READY_NONCE
[IO.File]::WriteAllText($env:INSTALL_READY_FILE,$readyToken)
$wait=[Diagnostics.Stopwatch]::StartNew()
while(-not ([IO.File]::Exists($env:INSTALL_PROFILE_ACK) -and [IO.File]::ReadAllText($env:INSTALL_PROFILE_ACK) -ceq $readyToken)) {
    if($wait.Elapsed.TotalSeconds -gt 10){throw 'Parent profile-boundary acknowledgement missing'}
    Start-Sleep -Milliseconds 20
}
'''

def require(value, reason):
    if not value: raise AssertionError(reason)

def snapshot(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        held=LOCKS.get(os.path.normcase(str(p.absolute())))
        if held is not None:
            rows.append(held.snapshot_row(p.relative_to(root)))
        else:
            rows.append((str(p.relative_to(root)),p.stat().st_mode,hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ''))
    return rows

def ready(root, env):
    path=root/'ready'
    value=path.read_text(encoding='utf-8-sig').split('\t') if path.is_file() else []
    return len(value)==2 and value[0]==env.get('INSTALL_EXPECTED_PID') and value[1]==env['INSTALL_READY_NONCE']

def protect_parents(root, host, native_modules, paths):
    """Create the self-owned Windows premise only on newly owned fixture parents."""
    for path in paths:
        require(path.is_dir() and (path == ROOT or path.is_relative_to(ROOT)), 'ACL setup escaped the owned fixture')
        require(not (path.lstat().st_file_attributes & 0x400), 'ACL setup refused a reparse point')
    code = r'''
$ErrorActionPreference='Stop'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
$owned=@($env:INSTALL_OWNED_PARENTS.Split('|'))
$observed=@()
foreach($parent in $owned) {
    $cursor=[IO.DirectoryInfo]::new($parent)
    while($cursor) {
        if($observed -notcontains $cursor.FullName){$observed += $cursor.FullName}
        $cursor=$cursor.Parent
    }
}
function Read-ParentFacts([string[]]$Paths) {
    foreach($path in $Paths) {
        $item=Get-Item -LiteralPath $path -Force
        $acl=Get-Acl -LiteralPath $path
        [pscustomobject]@{
            path=$item.FullName; attributes=[int]$item.Attributes;
            owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;
            group=$acl.GetGroup([Security.Principal.SecurityIdentifier]).Value;
            sddl=$acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]'Access,Owner,Group');
            protected=$acl.AreAccessRulesProtected;
            rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])|ForEach-Object{
                [pscustomobject]@{sid=$_.IdentityReference.Value; rights=[int64]$_.FileSystemRights; type=[string]$_.AccessControlType; inherited=$_.IsInherited; inheritance=[string]$_.InheritanceFlags; propagation=[string]$_.PropagationFlags}
            })
        }
    }
}
$before=@(Read-ParentFacts $observed)
[IO.File]::WriteAllText($env:INSTALL_ACL_BEFORE,($before|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
foreach($parent in $owned) {
    $full=[IO.Path]::GetFullPath($parent)
    if($full -cne $env:INSTALL_FIXTURE_ROOT -and -not $full.StartsWith($env:INSTALL_FIXTURE_ROOT+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'ACL setup escaped owned root'}
    if(([IO.File]::GetAttributes($full) -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'ACL setup refused reparse point'}
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($sid); $acl.SetAccessRuleProtection($true,$false)
    $rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
    $acl.AddAccessRule($rule)
    Set-Acl -LiteralPath $parent -AclObject $acl
}
$after=@(Read-ParentFacts $observed)
[IO.File]::WriteAllText($env:INSTALL_ACL_AFTER,($after|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
foreach($row in $after) {
    if($owned -contains $row.path) {
        if($row.owner -cne $sid.Value -or -not $row.protected -or $row.rules.Count -ne 1 -or $row.rules[0].sid -cne $sid.Value -or $row.rules[0].type -cne 'Allow' -or $row.rules[0].rights -ne [int64][Security.AccessControl.FileSystemRights]::FullControl){throw 'Owned parent ACL readback failed'}
    } else {
        $prior=@($before|Where-Object{$_.path -ceq $row.path})
        if($prior.Count -ne 1 -or $prior[0].sddl -cne $row.sddl){throw 'An external ancestor ACL changed'}
    }
}
'''
    env=dict(os.environ, POWERSHELL_TELEMETRY_OPTOUT='1', DOTNET_CLI_TELEMETRY_OPTOUT='1', POWERSHELL_UPDATECHECK='Off', INSTALL_OWNED_PARENTS='|'.join(map(str,paths)),
             INSTALL_FIXTURE_ROOT=str(ROOT), INSTALL_ACL_BEFORE=str(root/'parent-acl-before.json'),
             INSTALL_ACL_AFTER=str(root/'parent-acl-after.json'))
    for key in list(env):
        if key.upper() == 'PSMODULEPATH': del env[key]
    env['PSModulePath']=native_modules
    try:
        result=subprocess.run([host,'-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode('ascii')],env=env,capture_output=True,timeout=60)
    except subprocess.TimeoutExpired as error:
        (root/'parent-acl-setup.stdout.txt').write_bytes(error.stdout or b'')
        (root/'parent-acl-setup.stderr.txt').write_bytes(error.stderr or b'')
        raise
    (root/'parent-acl-setup.stdout.txt').write_bytes(result.stdout)
    (root/'parent-acl-setup.stderr.txt').write_bytes(result.stderr)
    require(result.returncode==0, 'Owned parent ACL setup failed before installer execution')

def _case_impl(host_name, host, native_modules, scenario):
    root = ROOT/(host_name+'-'+scenario); root.mkdir()
    subject = root/'subject'; subject.mkdir()
    env = dict(os.environ, POWERSHELL_TELEMETRY_OPTOUT='1', DOTNET_CLI_TELEMETRY_OPTOUT='1', POWERSHELL_UPDATECHECK='Off')
    replacements = {'TEMP','TMP','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','HOME','USERPROFILE','PSMODULEPATH','PSMODULEANALYSISCACHEPATH'}
    for key in list(env):
        if key.upper() in replacements: del env[key]
    for key, part in [('TEMP','temp'),('TMP','temp'),('LOCALAPPDATA','local'),('APPDATA','roam'),('PROGRAMFILES','pf'),('PROGRAMFILES(X86)','pf86')]:
        path = subject/part; path.mkdir(exist_ok=True); env[key] = str(path)
    # Native CLR/PowerShell startup writes its own home caches. Keep those in
    # a separate owned host boundary, distinct from installer effect targets.
    host_home = root/'host-home'; host_home.mkdir()
    (host_home/'existing-profile-sentinel.bin').write_bytes(b'preserve owned USERPROFILE bytes\n')
    env['HOME'] = env['USERPROFILE'] = str(host_home)
    if os.name == 'nt':
        try:
            protect_parents(root,host,native_modules,[ROOT,root,subject,subject/'temp',host_home])
        except (AssertionError,OSError,subprocess.TimeoutExpired) as error:
            RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='BOOTSTRAP_BLOCKED',error=str(error),observation=dict(fixture=str(root),stage='owned-parent-acl-setup',installerExecuted=False)))
            return False
    if scenario in ('readable','unreadable'):
        firefox = subject/'roam/Mozilla/Firefox/Profiles/fixture profile'; firefox.mkdir(parents=True)
        (firefox/'extensions.json').write_text('{"addons":[]}\n',encoding='utf-8')
        (firefox/'readable-peer.json').write_bytes((firefox/'extensions.json').read_bytes())
    elif scenario != 'none':
        chrome = subject/'local/Google/Chrome/User Data/Default'; chrome.mkdir(parents=True)
        if scenario == 'legacy': (chrome/'Extensions/hipekcciheckooncpjeljhnekcoolahp').mkdir(parents=True)
        elif scenario == 'installed': (chrome/'Extensions/dlaogejjiafeobgofajdlkkhjlignalk').mkdir(parents=True)
        else:
            firefox = subject/'roam/Mozilla/Firefox/Profiles/fixture profile'; firefox.mkdir(parents=True)
            (firefox/'extensions.json').write_text('{"addons":[]}\n',encoding='utf-8')
        if scenario == 'mixed': (subject/'local/Microsoft/Edge/User Data/Default/Extensions/lklaendlmlfkaabeleddanafeinnenih').mkdir(parents=True)
    asset = root/'fixture.zip'
    with zipfile.ZipFile(asset,'w') as archive: archive.writestr('manifest.json','{"manifest_version":3,"name":"Fixture","version":"1.0"}')
    preset_fixture=root/'canonical-preset.json'
    preset_fixture.write_bytes(PRESET.read_bytes())
    if scenario == 'cached':
        cache = subject/'temp/SalahWidgetInstaller/downloads/v-fixture'; cache.mkdir(parents=True)
        for name in ('tabliss-chromium.zip','tabliss-firefox-signed.xpi'): (cache/name).write_bytes(asset.read_bytes())
        (cache/'tabliss-chromium-unpacked').mkdir(); (cache/'tabliss-chromium-unpacked/marker').write_text('keep unpacked')
        preset = subject/'temp/SalahWidgetInstaller/presets'; preset.mkdir()
        (preset/'salah-widget.tablissng.json').write_text('{"input":"#local=1","sentinel":"keep"}')
    module = root/'modules/Microsoft.PowerShell.Utility'; module.mkdir(parents=True)
    (module/'Microsoft.PowerShell.Utility.psm1').write_text(MODULE,encoding='ascii')
    (module/'Microsoft.PowerShell.Utility.psd1').write_text("@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='b02389c7-c88e-40c9-a1c1-5c8217d2d593';FunctionsToExport=@('Write-Host','New-Item','Remove-Item','Invoke-RestMethod','Invoke-WebRequest','Expand-Archive','Set-Clipboard','Start-Process','Read-Host');CmdletsToExport='*';AliasesToExport=@()}\n",encoding='ascii')
    normal = scenario in ('positive','no-open')
    env.update(PSModulePath=str(root/'modules')+';'+native_modules, PSModuleAnalysisCachePath=str(root/'analysis-cache'),
               INSTALL_NATIVE_UTILITY=str(pathlib.Path(native_modules)/'Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1'),
               INSTALL_READY_FILE=str(root/'ready'), INSTALL_PROFILE_ACK=str(root/'profile-ack'), INSTALL_EFFECT_LOG=str(root/'effects'), INSTALL_SUBJECT_ROOT=str(subject),
               INSTALL_BOOTSTRAP_LOG=str(root/'bootstrap-phases.txt'),
               INSTALL_READY_NONCE=secrets.token_hex(16),
               INSTALL_FIXTURE_NORMAL='1' if normal else '0', INSTALL_ASSET_ZIP=str(asset),
               INSTALL_PRESET_FIXTURE=str(preset_fixture),
               INSTALL_FIXTURE_PF=str(subject/'pf'), INSTALL_FIXTURE_PF86=str(subject/'pf86'),
               SALAH_INSTALL_SOURCE='github', SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4')
    command = [host,'-NoProfile','-File',str(SOURCE),'-PresetUrl','' if scenario == 'missing-preset' else 'https://example.invalid/preset',
               '-InstallSource',scenario if scenario in ('ask','store') else 'invalid' if scenario == 'bad-option' else 'github',
               '-WidgetHash',env['SALAH_WIDGET_HASH']]
    if not normal: command += ['-DryRun']
    if scenario == 'no-open': command += ['-NoOpen']
    # Independently observe host-only startup in this same owned profile. No
    # observed path becomes an exclusion: actual entry comparisons remain exact.
    startup = root/'host-only-control'; startup.mkdir()
    host_control = startup/'host-only.ps1'
    host_control.write_text("$ErrorActionPreference='Stop'\nWrite-Host 'R0016 independent host startup control'\nexit 0\n",encoding='ascii')
    startup_env=dict(env, INSTALL_READY_FILE=str(startup/'ready'), INSTALL_PROFILE_ACK=str(startup/'ack'),
                     INSTALL_EFFECT_LOG=str(startup/'effects'), INSTALL_BOOTSTRAP_LOG=str(startup/'phases'),
                     INSTALL_READY_NONCE=secrets.token_hex(16), INSTALL_FIXTURE_NORMAL='0')
    startup_env.pop('INSTALL_UNREADABLE_FILE',None)
    try:
        startup_run,startup_window=support.invoke_with_profile_boundary([host,'-NoProfile','-File',str(host_control)],startup_env,startup,host_home,ENTRY_TIMEOUT_SECONDS)
        require(startup_run.returncode==0 and startup_window['ready'],'Independent host-only baseline failed')
        require(not (startup/'effects').exists() or not (startup/'effects').read_bytes(),'Host-only control reached an installer effect spy')
    except (AssertionError,OSError,subprocess.TimeoutExpired) as error:
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='PROFILE_BASELINE_BLOCKED',error=str(error),observation=dict(fixture=str(root),installerExecuted=False,baseline=str(startup/'profile-window.json'))))
        return False
    if scenario in ('readable','unreadable'):
        metadata=firefox/'extensions.json'
        metadata_sha=hashlib.sha256(metadata.read_bytes()).hexdigest()
        env.update(INSTALL_UNREADABLE_FILE=str(metadata),INSTALL_READABLE_PEER=str(firefox/'readable-peer.json'),
                   INSTALL_METADATA_SHA=metadata_sha,INSTALL_UNREADABLE_PROOF=str(root/'unreadable-child-proof.json'))
        if scenario == 'unreadable':
            held=support.NativeReadLock(metadata,ROOT)
            LOCKS[os.path.normcase(str(metadata.absolute()))]=held
            support.save(root/'unreadable-held-before.json',held.initial)
            require(held.initial['sha256']==metadata_sha,'Metadata bytes changed before exclusive fixture acquisition')
    before = snapshot(subject)
    (root/'subject-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    command_started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    command_clock = time.monotonic()
    try:
        run,profile_window = support.invoke_with_profile_boundary(command,env,root/'entry-profile-window',host_home,ENTRY_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError) as error:
        partial_out=getattr(error,'stdout',None) or b''
        partial_err=getattr(error,'stderr',None) or b''
        (root/'stdout.txt').write_bytes(partial_out)
        (root/'stderr.txt').write_bytes(partial_err)
        after=snapshot(subject)
        (root/'subject-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        effects=(root/'effects').read_text(encoding='utf-8-sig').splitlines() if (root/'effects').exists() else []
        phases=(root/'bootstrap-phases.txt').read_text(encoding='utf-8-sig').splitlines() if (root/'bootstrap-phases.txt').exists() else []
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,error=str(error),
                            classification='ENTRY_TIMEOUT' if ready(root,env) else 'BOOTSTRAP_BLOCKED',
                            observation=dict(command=command,fixture=str(root),interceptionLoaded=ready(root,env),
                            commandStartedUtc=command_started,elapsedSeconds=time.monotonic()-command_clock,timeoutSeconds=ENTRY_TIMEOUT_SECONDS,
                            bootstrapPhases=phases,snapshotUnchanged=before==after,effects=effects,profileWindow=str(root/'entry-profile-window/profile-window.json'),hostBaseline=str(startup/'profile-window.json'),
                            stdout=str(root/'stdout.txt'),stderr=str(root/'stderr.txt'))))
        return False
    stdout = run.stdout.decode('utf-8',errors='replace'); stderr = run.stderr.decode('utf-8',errors='replace')
    (root/'stdout.txt').write_bytes(run.stdout); (root/'stderr.txt').write_bytes(run.stderr)
    effect_path = root/'effects'
    effects = [tuple(row.split('\t',1)) for row in effect_path.read_text(encoding='utf-8-sig').splitlines()] if effect_path.exists() else []
    after=snapshot(subject)
    (root/'subject-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
    unchanged = before == after
    observation = dict(command=command,fixture=str(root),entryExit=run.returncode,interceptionLoaded=ready(root,env),readinessNonce=env['INSTALL_READY_NONCE'],snapshotUnchanged=unchanged,effects=effects,hostStartupState=snapshot(host_home),stdout=str(root/'stdout.txt'),stderr=str(root/'stderr.txt'),commandStartedUtc=command_started,elapsedSeconds=time.monotonic()-command_clock,timeoutSeconds=ENTRY_TIMEOUT_SECONDS)
    observation.update(profileWindow=profile_window,hostOnlyBaseline=startup_window,
                       profileScope='Complete owned USERPROFILE before launch, at actual PID/nonce readiness, and after exit; no path-name exclusions.')
    try:
        if scenario != 'bad-option':
            require(ready(root,env),'BOOTSTRAP_BLOCKED: final startup interception nonce missing or wrong')
            require(profile_window['before']==profile_window['atReady'],'PROFILE_STARTUP_NOT_QUIESCENT: actual host changed USERPROFILE before the installer boundary; no exclusion is credited')
        if scenario in ('readable','unreadable'):
            proof=json.loads((root/'unreadable-child-proof.json').read_text(encoding='utf-8-sig'))
            observation['unreadability']=proof
            require(proof['pid']==profile_window['pid'] and proof['nonce']==env['INSTALL_READY_NONCE'],'Unreadability proof is not from the actual entry child')
            require(proof['exists'] and proof['peerReadable'],'Actual child failed the native file-existence/readable-peer controls')
            if scenario == 'unreadable':
                require(not proof['readSucceeded'] and proof['nativeCode']==32 and proof['exceptionType']=='System.IO.IOException','Actual child did not prove native metadata read refusal')
                require('discovery unknown: HELD (metadata-unreadable)' in stdout and 'Preview targets: 0 eligible, 1 held, 0 refused.' in stdout and 'No eligible target; preview made no changes.' in stdout,'Unreadable metadata did not reach actual held/no-eligible main behavior')
            else:
                require(proof['readSucceeded'] and proof['nativeCode'] is None and proof['targetSha256']==env['INSTALL_METADATA_SHA'],'Unlocked actual-child metadata control failed')
                require('Preview targets: 1 eligible, 0 held, 0 refused.' in stdout and 'release/version/path unresolved' in stdout,'Readable healthy counterpart did not reach useful actual main behavior')
        if normal:
            require(run.returncode == 0,'Normal direct entry failed: '+stdout+stderr)
            by_kind = collections.defaultdict(list)
            for kind,value in effects: by_kind[kind].append(value)
            require(by_kind['metadata'] == ['https://api.github.com/repos/BookCatKid/TablissNG/releases/latest'],'Wrong release lookup/count')
            require(collections.Counter(by_kind['download']) == collections.Counter(['https://example.invalid/chromium','https://example.invalid/firefox','https://example.invalid/preset']),'Wrong download URLs/counts')
            bundles=list(host_home.glob('SalahWidgetBundle-*'))
            require(len(bundles)==1 and bundles[0].is_dir(),'Exactly one retained manual bundle required')
            stage=bundles[0]
            unpacked_rows=list(stage.glob('unpacked-*'))
            xpi_rows=list((stage/'downloads').glob('*-tabliss-firefox-signed.xpi'))
            preset_rows=list((stage/'presets').glob('*-salah-widget.tablissng.json'))
            require(len(unpacked_rows)==len(xpi_rows)==len(preset_rows)==1,'Actual admitted outputs missing or ambiguous')
            unpacked,xpi,preset=unpacked_rows[0],xpi_rows[0],preset_rows[0]
            require(not by_kind['extract'],'Native bounded extractor unexpectedly called Expand-Archive')
            require(collections.Counter(by_kind['clipboard']) == collections.Counter([str(unpacked),str(xpi),str(preset),str(preset)]),'Wrong copied paths/counts')
            require((unpacked/'manifest.json').is_file() and xpi.is_file(),'Actual staged local assets missing')
            configured=json.loads(preset.read_text(encoding='utf-8-sig'))
            frame=ET.fromstring(configured['data/orpul7IDXSSP']['input'])
            require(frame.tag=='iframe' and frame.attrib.get('src')=='https://theislampill.github.io/salah_widget/#'+env['SALAH_WIDGET_HASH'],'Canonical configured preset not consumed')
            require(not list((subject/'temp').glob('SalahWidgetAttempt-*')),'Owned scratch remains after successful normal cleanup')
            require(len(by_kind['prompt']) == 3,'Normal selection/manual confirmations not reached')
            expected_opens = ['chrome://extensions/ ','chrome://newtab/ ','about:addons ','about:newtab ']
            require(collections.Counter(by_kind['open']) == collections.Counter([] if scenario == 'no-open' else expected_opens),'Wrong manager/newtab opens or store fallback')
            require('Manual browser installation/import remain pending' in stdout,'False install completion wording')
            chromium_rows=list((stage/'downloads').glob('*-tabliss-chromium.zip'))
            require(len(chromium_rows)==1,'Actual retained Chromium archive missing or ambiguous')
            expected=[stage,stage/'downloads',stage/'presets',unpacked,unpacked/'manifest.json',xpi,preset,chromium_rows[0]]
            support.assert_profile_window(profile_window['before'],profile_window['after'],stage.name,[p.relative_to(host_home).as_posix() for p in expected])
        else:
            require(unchanged and not effects,'Dry-run changed owned state or reached effects')
            require(not list(host_home.glob('SalahWidgetBundle-*')),'Dry-run created a retained bundle outside the temp subject')
            support.assert_profile_window(profile_window['before'],profile_window['after'])
            failure = scenario in ('legacy','none','bad-option','unreadable')
            require((run.returncode != 0) == failure,'Wrong direct process exit')
            if not failure:
                require('Preview only; no changes made' in stdout,'Preview completion missing')
                require('Importing the preset replaces your current TablissNG dashboard' in stdout,'Replacement warning missing')
                if scenario == 'ask': require('Install source unresolved' in stdout,'Choice fabricated')
                if scenario in ('github','cached','mixed'): require('release/version/path unresolved' in stdout,'Remote facts fabricated')
                if scenario == 'missing-preset': require('No preset URL configured' in stdout,'Empty preset URL not honored')
        RESULTS.append(dict(host=host_name,case=scenario,pass_=True,observation=observation))
    except Exception as error:
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,error=str(error),observation=observation))
    return scenario=='bad-option' or ready(root,env)

def case(host_name,host,native_modules,scenario):
    start=len(RESULTS)
    keep_running=False
    try:
        keep_running=_case_impl(host_name,host,native_modules,scenario)
    except Exception as error:
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='FIXTURE_ACQUISITION_FAILED',error=str(error),observation=dict(fixture=str(ROOT/(host_name+'-'+scenario)))))
    finally:
        for key,held in list(LOCKS.items()):
            try:
                restored=held.restore()
                support.save(ROOT/(host_name+'-'+scenario)/'unreadable-restoration.json',restored)
                for row in RESULTS[start:]: row.setdefault('observation',{})['unreadableRestoration']=restored
            except Exception as error:
                held.close_after_failure()
                for row in RESULTS[start:]: row.update(pass_=False,restorationError=str(error))
                keep_running=False
            finally:
                del LOCKS[key]
    return keep_running

if os.name != 'nt':
    for host_name,_,_ in HOSTS:
        if not args.host or host_name in args.host:
            RESULTS.append(dict(host=host_name,case='native-entry-coverage',pass_=False,classification='BLOCKED_NATIVE_HOST',installerExecuted=False))
    print(json.dumps(dict(source=SOURCE_HASH_BEFORE,fixture=str(ROOT),results=RESULTS,nativeWindows=False),indent=2))
    sys.exit(2)

for host_name, host, native_modules in HOSTS:
    if args.host and host_name not in args.host: continue
    for scenario in args.scenario or SCENARIOS:
        if not case(host_name,host,native_modules,scenario):
            break  # Retain a terminal receipt; do not repeat a failed host bootstrap.
source_after=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if source_after!=SOURCE_HASH_BEFORE: RESULTS.append(dict(case='exact source custody',pass_=False,error='Source changed during fixture'))
print(json.dumps(dict(source=source_after,sourceBefore=SOURCE_HASH_BEFORE,sourceUnchanged=source_after==SOURCE_HASH_BEFORE,
                     testSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),supportSha256=hashlib.sha256(SUPPORT_PATH.read_bytes()).hexdigest(),
                     preset=hashlib.sha256(PRESET.read_bytes()).hexdigest(),fixture=str(ROOT),selectedHosts=args.host or ['ps51','ps7'],selectedScenarios=args.scenario or SCENARIOS,results=RESULTS,
                     nativeWindows=True,scope='Full exact -File entry; observed host-only baseline, complete USERPROFILE window, and actual Windows metadata share refusal; no host-path exclusions.'),indent=2))
sys.exit(1 if any(not row['pass_'] for row in RESULTS) else 0)
