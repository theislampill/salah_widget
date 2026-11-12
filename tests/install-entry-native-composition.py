#!/usr/bin/env python3
"""NEW direct -File / held full-file composition proposal; no historical native credit.

The original direct coverage predicates remain visible. Preview composition and
normal positive confinement have distinct mandatory receivers. A new held carrier
needs independent source-free native qualification before product credit.
"""
import argparse, base64, collections, datetime, hashlib, json, math, os, pathlib, re, secrets, subprocess, sys, tempfile, time, zipfile
import xml.etree.ElementTree as ET
import importlib.util
sys.dont_write_bytecode=True
SUPPORT_PATH = pathlib.Path(__file__).with_name('install-entry-coverage-support.py')
support_spec = importlib.util.spec_from_file_location('r0016_entry_coverage_support', SUPPORT_PATH)
support = importlib.util.module_from_spec(support_spec)
support_spec.loader.exec_module(support)
COMPOSITION_PATH = pathlib.Path(__file__).with_name('install-entry-product-support.py')
composition_spec = importlib.util.spec_from_file_location('r0016_entry_composition_support', COMPOSITION_PATH)
composition = importlib.util.module_from_spec(composition_spec)
composition_spec.loader.exec_module(composition)
HELD_DRIVER = pathlib.Path(__file__).with_name('install-entry-held.ps1').resolve()
LOCKS = {}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=pathlib.Path, nargs='?', default=pathlib.Path(__file__).resolve().parents[1]/'install.ps1')
parser.add_argument('--host', action='append', choices=('ps51','ps7'), required=True)
parser.add_argument('--host-executable', type=pathlib.Path, required=True)
parser.add_argument('--output-root', type=pathlib.Path, required=True)
SCENARIOS = composition.SCENARIOS
parser.add_argument('--scenario', action='append', choices=SCENARIOS)
parser.add_argument('--preset', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1]/'presets/salah-widget.tablissng.json')
parser.add_argument('--preview-core', type=pathlib.Path, default=pathlib.Path(__file__).with_name('install-preview.ps1'))
parser.add_argument('--window-library', type=pathlib.Path, default=pathlib.Path(__file__).with_name('install-preview-window.ps1'))
args = parser.parse_args()
if len(args.host)!=1:parser.error('Exactly one explicit native host per invocation is required')
SOURCE = args.source.resolve()
PRESET = args.preset.resolve()
SOURCE_HASH_BEFORE = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
ENTRY_TIMEOUT_SECONDS = 60  # Native PS5.1 cold readiness alone measured 19.615-22.770s.
HOSTS = [(args.host[0],str(args.host_executable),str(args.host_executable.parent/'Modules'))]
ROOT = None
PATH_BUDGET = None
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
if($env:R0016_INPUT_PROBE) {
    . $env:R0016_INPUT_PROBE
    Invoke-R0016EntryInputProbe -SourcePath $env:R0016_ENTRY_SOURCE -SourceSha256 $env:R0016_ENTRY_SOURCE_SHA -ProbePath $env:R0016_INPUT_PROBE -ProofPath $env:R0016_MODULE_INPUT_PROOF -Phase $env:R0016_INPUT_PHASE -Nonce $env:INSTALL_READY_NONCE -ExpectedHost $env:R0016_EXPECTED_HOST
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

def digest(raw):return hashlib.sha256(raw).hexdigest()

def warm_control_body(mode):
    body="$ErrorActionPreference='Stop'\nWrite-Host 'R0016 independent host startup control'\n"
    if mode=='warm-json':
        body+=r'''
$command=Get-Command -Name ConvertFrom-Json -CommandType Cmdlet -ErrorAction Stop
if(@($command).Count -ne 1){throw 'Ambiguous native JSON command'}
$parsed=& $command -InputObject '{"r0016Probe":"source-free","value":16}'
if($parsed.r0016Probe -cne 'source-free' -or $parsed.value -ne 16){throw 'Native JSON warm-up failed'}
$assemblyPath=$command.ImplementingType.Assembly.Location
$assemblyBytes=[IO.File]::ReadAllBytes($assemblyPath)
$hasher=[Security.Cryptography.SHA256]::Create()
try{$assemblySha=([BitConverter]::ToString($hasher.ComputeHash($assemblyBytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
$context=[ordered]@{schema='r0016-source-free-json-context.v1';pid=$PID;nonce=$env:INSTALL_READY_NONCE;normal=$env:INSTALL_FIXTURE_NORMAL;command=$command.Name;commandType=[string]$command.CommandType;module=$command.ModuleName;nativeUtility=$env:INSTALL_NATIVE_UTILITY;analysisCachePath=$env:PSModuleAnalysisCachePath;parsedMarker=$parsed.r0016Probe;parsedValue=$parsed.value;assemblyPath=$assemblyPath;assemblyBytes=$assemblyBytes.Length;assemblySha256=$assemblySha;moduleSearchPath=$env:PSModulePath}
[Console]::WriteLine('R0016_WARM_JSON_CONTEXT '+($context|ConvertTo-Json -Depth 4 -Compress))
'''
    if mode in ('warm20','warm-json'):body+='[Threading.Thread]::Sleep(20000)\n'
    return body+'exit 0\n'

def receive_cache_bytes(raw,rows):
    require(type(rows) is list and all(type(row) is dict for row in rows),'Invalid cache inventory')
    matches=[row for row in rows if row.get('role')=='analysisCache']
    require(len(matches)==1 and matches[0].get('path')=='.','Missing or duplicate cache root')
    row=matches[0]
    if row.get('kind')=='absent':
        require(raw is None,'Absent cache has an invented byte capture')
    else:
        require(row.get('kind')=='file' and type(raw) is bytes and type(row.get('bytes')) is int
            and row['bytes']>=0 and len(raw)==row['bytes'] and digest(raw)==row.get('sha256'),
            'Cache capture differs from its full-input observation')
    return row

def parse_warm_context(raw):
    require(type(raw) is bytes,'Warm context is not original raw bytes')
    lines=[line[len('R0016_WARM_JSON_CONTEXT '):] for line in raw.decode('utf-8-sig').splitlines()
        if line.startswith('R0016_WARM_JSON_CONTEXT ')]
    require(len(lines)==1,'Missing or duplicate source-free JSON context')
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'Duplicate warm-context key')
            result[key]=value
        return result
    context=json.loads(lines[0],object_pairs_hook=unique)
    require(type(context) is dict,'Invalid source-free JSON context')
    return context

def receive_native_assembly(driver,context,journal_path):
    journal=dict(schema='r0016-warm-json-native-file-binding.v1',comparisons=[])
    child=dict(path=context.get('assemblyPath'),bytes=context.get('assemblyBytes'),
        sha256=context.get('assemblySha256'))
    driver.record_probe_file_binding(child,'warm-json/assembly',journal_path,journal)
    require(len(journal['comparisons'])==1,'Missing native JSON assembly binding')
    return journal['comparisons'][0]

def receive_warm_context(raw,receipt,assembly_binding):
    context=parse_warm_context(raw);env=receipt.get('environment',{})
    require(context.get('schema')=='r0016-source-free-json-context.v1'
        and type(context.get('pid')) is int and context['pid']==receipt.get('pid')
        and context.get('nonce')==receipt.get('nonce')
        and context.get('normal')==env.get('INSTALL_FIXTURE_NORMAL')=='0',
        'Source-free JSON context has the wrong process')
    require(context.get('command')=='ConvertFrom-Json' and context.get('commandType')=='Cmdlet'
        and context.get('module')=='Microsoft.PowerShell.Utility'
        and context.get('nativeUtility')==env.get('INSTALL_NATIVE_UTILITY')
        and context.get('analysisCachePath')==env.get('PSModuleAnalysisCachePath'),
        'Source-free JSON command/cache binding differs')
    require(context.get('parsedMarker')=='source-free' and type(context.get('parsedValue')) is int
        and context['parsedValue']==16 and type(context.get('moduleSearchPath')) is str
        and context['moduleSearchPath'],'Source-free native JSON result missing')
    child=dict(path=context.get('assemblyPath'),bytes=context.get('assemblyBytes'),
        sha256=context.get('assemblySha256'))
    require(type(child['path']) is str and type(child['bytes']) is int and child['bytes']>0
        and type(child['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}',child['sha256'])
        and assembly_binding.get('childFact')==child and assembly_binding.get('matches') is True
        and assembly_binding.get('error') is None,'Native JSON assembly binding missing or differs')
    identity=assembly_binding.get('nativeFileIdentity',{});parent=assembly_binding.get('parentFact',{})
    require(all(identity.get(field) is True for field in
        ('resolutionMatches','sameFile','stable','contentMatches'))
        and identity.get('rawPath')==child['path'] and type(parent.get('path')) is str
        and all(identity.get(field)==parent['path'] for field in
            ('canonicalPath','resolvedRawPath','resolvedCanonicalPath'))
        and identity.get('rawReadbackFact')==identity.get('canonicalReadbackFact')==parent
        and all(child[field]==parent.get(field) for field in ('bytes','sha256')),
        'Native JSON assembly lacks canonical identity/content proof')
    observations=identity.get('observations',{})
    require(set(observations)=={'rawBefore','canonicalBefore','rawAfter','canonicalAfter'},
        'Incomplete native JSON assembly observations')
    first=observations['rawBefore']
    require(type(first) is dict and type(first.get('device')) is int
        and type(first.get('inode')) is int and first['inode']>0
        and first.get('bytes')==child['bytes']
        and all(value==first for value in observations.values()),
        'Native JSON assembly identity or metadata changed')
    return context

def require_scoped_preparation_environment(host, scenario, environments):
    require(host in ('ps51','ps7') and scenario in SCENARIOS,'Unknown normal preparation host/case')
    require(type(environments) is list and len(environments)==3
        and all(type(env) is dict for env in environments),'Missing actual preparation environments')
    for env in environments:
        flags={key:value for key,value in env.items() if key.upper()=='COMPLUS_MULTICOREJITNOPROFILEGATHER'}
        require(len(flags)==(1 if host=='ps7' and scenario in ('positive','no-open') else 0)
            and all(value=='1' for value in flags.values()),'Wrong scoped prelaunch gather environment')


def capture_preparation_cache(path, inventory, destination):
    raw=path.read_bytes() if path.is_file() else None
    row=receive_cache_bytes(raw,inventory['rows'])
    capture=None
    if raw is not None:
        destination.write_bytes(raw);capture=composition.fact(destination)
    return dict(inventoryRow=row,capture=capture)


def require_normal_preparation(observation, host, scenario, script, phases, cache_raw, warm_raw, assembly_binding):
    require(scenario in ('positive','no-open') and host in ('ps51','ps7'),'Wrong normal preparation host/case')
    preparation=observation.get('normalPreparation')
    require(type(preparation) is dict and set(preparation)=={'schema','mode','holdSeconds','script',
        'phaseFacts','cacheCaptures','warmJsonContext'},'Missing complete normal preparation')
    mode='warm-json' if host=='ps51' else 'no-gather'
    require(preparation['schema']=='r0016-normal-preparation.v1' and preparation['mode']==mode
        and type(preparation['holdSeconds']) is int and preparation['holdSeconds']==(20 if host=='ps51' else 0),
        'Wrong host-specific normal preparation mode/hold')
    require(type(script) is bytes and script.replace(b'\r\n',b'\n')==warm_control_body(mode).encode('ascii'),
        'Source-free normal preparation body differs')
    warm=observation['hostOnlyBaseline'];product=observation['profileWindow'];launch=observation['directLaunchInputs']
    require(launch.get('environment')==product.get('environment'),'Actual normal product launch environment differs')
    require_scoped_preparation_environment(host,scenario,[launch.get('environment'),warm.get('environment'),product.get('environment')])
    require(warm['environment'].get('INSTALL_FIXTURE_NORMAL')=='0'
        and product['environment'].get('INSTALL_FIXTURE_NORMAL')=='1','Wrong source-free/product effect environment')
    shared=('PSModulePath','PSModuleAnalysisCachePath','INSTALL_NATIVE_UTILITY','USERPROFILE','HOME',
        'INSTALL_SUBJECT_ROOT','INSTALL_ASSET_ZIP','INSTALL_PRESET_FIXTURE','INSTALL_FIXTURE_PF','INSTALL_FIXTURE_PF86')
    require(all(type(warm['environment'].get(key)) is str and warm['environment'][key]==product['environment'].get(key)
        for key in shared),'Preparation used different fixture/native inputs')
    require(warm.get('nonce')==warm['environment'].get('INSTALL_READY_NONCE')
        and product.get('nonce')==product['environment'].get('INSTALL_READY_NONCE')==observation.get('readinessNonce')
        and warm['nonce']!=product['nonce'] and warm.get('pid')!=product.get('pid'),
        'Preparation PID/nonce is missing or replayed')
    require(warm.get('ready') is True and product.get('ready') is True
        and type(warm.get('entryExit')) is int and warm['entryExit']==0
        and type(warm.get('terminalObservedElapsedSeconds')) in (int,float)
        and warm['terminalObservedElapsedSeconds']>=preparation['holdSeconds']
        and not any(step.get('step')=='kill-owned-process' for step in warm.get('cleanup',{}).get('steps',[])),
        'Source-free preparation did not naturally complete its bounded hold')
    names={'warmBefore','warmReady','warmAfter','productBefore','productReady','productAfter'}
    require(type(phases) is dict and set(phases)==names
        and type(preparation['phaseFacts']) is dict and set(preparation['phaseFacts'])==names,
        'Missing normal preparation inventory phase')
    for inventory in phases.values():
        require(type(inventory) is dict and inventory.get('schema')=='r0016-entry-full-input-inventory.v1'
            and inventory.get('root')==observation['fixture'] and inventory.get('complete') is True
            and type(inventory.get('rows')) is list and inventory.get('passes')==[inventory['rows'],inventory['rows']],
            'Incomplete normal preparation double inventory')
        composition.validate_rows(inventory['rows'])
    require(phases['warmReady']==warm.get('fullReady') and phases['productReady']==product.get('fullReady')
        and phases['productBefore']==observation.get('fullInputsBefore')
        and phases['productReady']==observation.get('fullInputsAtReady')
        and phases['productAfter']==observation.get('fullInputsAfter'),
        'Normal preparation phase differs from actual receipt')
    require(phases['warmAfter']['rows']==phases['productBefore']['rows'],
        'Normal inputs changed between completed preparation and product baseline')
    cache_names={'warmBefore','warmAfter','productBefore','productAfter'}
    require(type(cache_raw) is dict and set(cache_raw)==cache_names
        and type(preparation['cacheCaptures']) is dict and set(preparation['cacheCaptures'])==cache_names,
        'Missing normal raw cache phase')
    for name in cache_names:
        row=receive_cache_bytes(cache_raw[name],phases[name]['rows'])
        entry=preparation['cacheCaptures'][name]
        require(type(entry) is dict and set(entry)=={'inventoryRow','capture'} and entry['inventoryRow']==row,
            'Normal raw cache inventory binding differs')
        capture=entry['capture'];raw=cache_raw[name]
        require((raw is None and capture is None) or (type(raw) is bytes and type(capture) is dict
            and capture.get('bytes')==len(raw) and capture.get('sha256')==digest(raw)),
            'Normal raw cache fact differs')
    if host=='ps51':
        context=receive_warm_context(warm_raw,warm,assembly_binding)
        expected=preparation['warmJsonContext']
        require(type(expected) is dict and set(expected)=={'context','assemblyBinding','bindingFact'}
            and expected['context']==context and expected['assemblyBinding']==assembly_binding,
            'Native JSON preparation proof differs')
    else:
        require(assembly_binding is None and preparation['warmJsonContext'] is None,
            'PS7 normal preparation contains an invented native JSON proof')
    return preparation


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

def validate_direct_terminal(receipt, command, timeout):
    """Admit only a complete direct-file capture and timely integer terminal."""
    require(receipt.get('schema')=='r0016-entry-direct-profile-observation.v1'
        and receipt.get('command')==command and receipt.get('timeoutSeconds')==timeout,
        'Wrong direct acquisition identity or deadline')
    require(type(receipt.get('pid')) is int and receipt['pid']>0
        and type(receipt.get('entryExit')) is int and receipt.get('exitObserved') is True
        and receipt.get('timedOut') is False and receipt.get('error') is None,
        'Missing direct terminal observation or failed acquisition')
    terminal,elapsed=receipt.get('terminalObservedElapsedSeconds'),receipt.get('elapsedSeconds')
    require(type(terminal) in (int,float) and math.isfinite(terminal) and 0<=terminal<timeout
        and type(elapsed) in (int,float) and math.isfinite(elapsed) and terminal<=elapsed,
        'Direct first terminal observation exceeded the deadline')
    cleanup=receipt.get('cleanup',{});steps=cleanup.get('steps',[])
    require(cleanup.get('processStarted') is True and cleanup.get('terminalObserved') is True
        and type(cleanup.get('terminalExit')) is int and cleanup['terminalExit']==receipt['entryExit']
        and cleanup.get('receiptWriteAttempted') is True and 'receiptWriteError' not in cleanup
        and steps and all(step.get('completed') is True and step.get('error') is None for step in steps),
        'Direct owned cleanup did not complete')
    names=[step.get('step') for step in steps]
    require(len(names)==len(set(names)) and {'poll-owned-process','wait-owned-process',
        'close-owned-stdout','close-owned-stderr','capture-owned-stdout','capture-owned-stderr',
        'observe-owned-profile'}<=set(names),'Missing or repeated direct cleanup step')
    require(receipt.get('capture')=='direct files; no redirected pipe drain'
        and receipt.get('captureCompletion')=='closed-after-observed-exit'
        and all(type(receipt.get(key)) is dict for key in ('stdout','stderr')),
        'Direct capture is incomplete')

def invoke_with_profile_boundary(command, env, control, home, timeout, full_root=None):
    """Direct product adapter; primary failures survive every cleanup attempt."""
    control=pathlib.Path(control)
    started=time.monotonic();process=None;primary=None;secondary=None
    handles={};captures={};at_ready=None
    cleanup=dict(processStarted=False,terminalObserved=False,terminalExit=None,cleanupSeconds=10,
        steps=[],receiptWriteAttempted=False)
    receipt=dict(schema='r0016-entry-direct-profile-observation.v1',command=command,
        environment=dict(env),pid=None,nonce=env['INSTALL_READY_NONCE'],entryExit=None,
        exitObserved=False,terminalObservedElapsedSeconds=None,timedOut=False,
        ready=False,before=None,atReady=None,after=None,timeoutSeconds=timeout,
        capture='direct files; no redirected pipe drain',captureCompletion='termination-unconfirmed',
        cleanup=cleanup,error=None)
    def attempt(name, operation):
        nonlocal secondary
        row=dict(step=name,completed=False,error=None);cleanup['steps'].append(row)
        try:
            value=operation();row['completed']=True
            return True,value
        except BaseException as error:
            row['error']=dict(type=type(error).__name__,message=str(error),
                errno=getattr(error,'errno',None),winerror=getattr(error,'winerror',None))
            if secondary is None:secondary=error
            return False,None
    def terminal(status, phase):
        require(type(status) is int,'Owned direct process did not return an integer terminal')
        if receipt['exitObserved']:
            require(receipt['entryExit']==status,'Direct terminal status changed during cleanup')
        else:
            receipt.update(entryExit=status,exitObserved=True,terminalObservedElapsedSeconds=time.monotonic()-started,
                terminalObservationPhase=phase)
            if receipt['terminalObservedElapsedSeconds']>=timeout:receipt['timedOut']=True
    try:
        require(type(timeout) is int and timeout>0,'Direct deadline must be a positive integer')
        control.mkdir(exist_ok=True)
        ready_path=pathlib.Path(env['INSTALL_READY_FILE']);ack_path=pathlib.Path(env['INSTALL_PROFILE_ACK'])
        require(not ready_path.exists() and not ack_path.exists(),'Direct ready/ACK paths are already occupied')
        receipt['before']=support.profile_snapshot(home)
        support.save(control/'profile-before-launch.json',receipt['before'])
        for stream in ('stdout','stderr'):
            path=control/(stream+'.raw')
            require(not path.exists(),'Direct capture path is already occupied')
            handles[stream]=path.open('wb')
        process=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,
            stdout=handles['stdout'],stderr=handles['stderr'])
        cleanup['processStarted']=True;receipt['pid']=process.pid
        env['INSTALL_EXPECTED_PID']=str(process.pid)
        expected=str(process.pid)+'\t'+env['INSTALL_READY_NONCE']
        while True:
            status=process.poll()
            elapsed=time.monotonic()-started
            if status is not None:terminal(status,'acquisition')
            if elapsed>=timeout:
                receipt['timedOut']=True
                raise subprocess.TimeoutExpired(command,timeout)
            if status is not None:break
            if at_ready is None and ready_path.is_file():
                require(ready_path.read_text(encoding='utf-8-sig')==expected,'Wrong direct ready PID/nonce')
                ready_started=time.monotonic()
                at_ready=support.profile_snapshot(home);receipt['atReady']=at_ready
                support.save(control/'profile-at-ready.json',at_ready)
                if full_root is not None:
                    receipt['fullReady']=composition.double_inventory(full_root,support,control/'full-at-ready.json',LOCKS)
                status=process.poll()
                if status is not None:terminal(status,'readiness')
                require(status is None and time.monotonic()-started<timeout
                    and time.monotonic()-ready_started<10,'Direct readiness observation exceeded its ACK deadline')
                temporary=ack_path.with_name(ack_path.name+'.partial')
                temporary.write_text(expected,encoding='utf-8');temporary.replace(ack_path)
                receipt.update(ready=True,readyToken=expected,
                    readyFact=composition.fact(ready_path),ackFact=composition.fact(ack_path))
            time.sleep(0.02)
    except BaseException as error:
        primary=error
        receipt['primaryFailure']=dict(type=type(error).__name__,message=str(error))
    finally:
        if process is not None:
            polled,status=attempt('poll-owned-process',process.poll)
            if polled and status is not None:
                attempt('observe-polled-terminal',lambda:terminal(status,'cleanup-poll'))
            if not polled or status is None:attempt('kill-owned-process',process.kill)
            waited,status=attempt('wait-owned-process',lambda:process.wait(timeout=10))
            if waited:
                confirmed,_=attempt('observe-waited-terminal',lambda:terminal(status,'cleanup-wait'))
                if confirmed:cleanup.update(terminalObserved=True,terminalExit=status)
        for stream,handle in handles.items():
            attempt('close-owned-'+stream,handle.close)
        def capture(stream):
            path=control/(stream+'.raw');raw=path.read_bytes();captures[stream]=raw
            receipt[stream+'Sha256']=support.digest(raw)
            value=composition.fact(path)
            require(value['bytes']==len(raw) and value['sha256']==receipt[stream+'Sha256'],
                'Direct capture changed during readback')
            receipt[stream]=value
        for stream in ('stdout','stderr'):
            attempt('capture-owned-'+stream,lambda stream=stream:capture(stream))
        def observe_profile():
            value=support.profile_snapshot(home)
            field='after' if cleanup['terminalObserved'] else 'cleanupProfile'
            receipt[field]=value
            filename='profile-after-exit.json' if cleanup['terminalObserved'] else 'profile-termination-unconfirmed.json'
            support.save(control/filename,value)
        attempt('observe-owned-profile',observe_profile)
        for name,left,right in (('startupDelta','before','atReady'),('entryDelta','atReady','after'),('fullDelta','before','after')):
            if receipt.get(left) is not None and receipt.get(right) is not None:
                def delta(name=name,left=left,right=right):
                    receipt[name]=support.profile_delta(receipt[left],receipt[right])
                attempt('derive-'+name,delta)
            else:receipt[name]=None
        receipt['elapsedSeconds']=time.monotonic()-started
        if cleanup['terminalObserved']:
            receipt['captureCompletion']='closed-after-observed-exit'
        cleanup['receiptWriteAttempted']=True
        failure=primary if primary is not None else secondary
        receipt['error']=str(failure) if failure is not None else None
        if failure is None:
            try:validate_direct_terminal(receipt,command,timeout)
            except BaseException as error:
                secondary=error;receipt['error']=str(error)
        try:support.save(control/'profile-window.json',receipt)
        except BaseException as error:
            cleanup['receiptWriteError']=dict(type=type(error).__name__,message=str(error))
            if secondary is None:secondary=error
            if primary is None:receipt['error']=str(secondary)
    failure=primary if primary is not None else secondary
    if failure is not None:
        try:
            failure.r0016_cleanup_receipt=receipt
            failure.stdout=captures.get('stdout',b'');failure.stderr=captures.get('stderr',b'')
        except BaseException:
            pass
        raise failure
    return subprocess.CompletedProcess(command,receipt['entryExit'],captures['stdout'],captures['stderr']),receipt

def require_normal_input_postcondition(observation):
    """One retained bundle plus the source-declared TEMP parent mtime change."""
    composition.require_positive_confinement(observation,support)
    require(SOURCE_HASH_BEFORE==composition.PREVIEW_SOURCE_SHA,
        'Normal input postcondition requires the reviewed complete source')
    result=dict(schema='r0016-normal-input-postcondition.v1',complete=False,
        sourceSha256=SOURCE_HASH_BEFORE,added=[],removed=[],changed=[],
        tempParentContract='Initialize-Staging and compiler custody create private children of owned TEMP; Clear-OwnedScratch/Clear-StagingCompilerContext remove them. Only that existing parent mtime may differ.')
    observation['normalInputPostcondition']=result
    inputs=[]
    for field in ('fullInputsBefore','fullInputsAfter'):
        value=observation.get(field)
        require(type(value) is dict and value.get('schema')=='r0016-entry-full-input-inventory.v1'
            and value.get('root')==observation['fixture'] and value.get('complete') is True
            and value.get('passes')==[value.get('rows'),value.get('rows')],
            'Incomplete or replayed normal input inventory')
        inputs.append(composition.validate_rows(value['rows']))
    before,after=inputs
    result['added']=[dict(role=key[0],path=key[1]) for key in sorted(after.keys()-before.keys())]
    result['removed']=[dict(role=key[0],path=key[1]) for key in sorted(before.keys()-after.keys())]
    for key in sorted(before.keys()&after.keys()):
        fields={field:dict(before=before[key][field],after=after[key][field])
            for field in sorted(composition.ROW_FIELDS) if before[key][field]!=after[key][field]}
        if fields:result['changed'].append(dict(role=key[0],path=key[1],fields=fields,
            declaredTempParentMtime=(key==('subject','temp') and set(fields)=={'mtimeNs'}
                and before[key]['kind']==after[key]['kind']=='directory')))
    require(observation.get('snapshotUnchanged') is True,'Normal subject names/modes/bytes changed')
    retained=observation['normalConfinement']
    support.assert_profile_window([row for row in observation['fullInputsBefore']['rows'] if row['role']=='profile'],
        [row for row in observation['fullInputsAfter']['rows'] if row['role']=='profile'],
        retained['retainedRelative'],retained['expectedRetainedPaths'])
    non_profile_before={key:row for key,row in before.items() if key[0]!='profile'}
    non_profile_after={key:row for key,row in after.items() if key[0]!='profile'}
    require(non_profile_before.keys()==non_profile_after.keys(),
        'Normal invocation added or removed an unexpected owned input')
    for key,original in non_profile_before.items():
        current=non_profile_after[key]
        fields={field for field in composition.ROW_FIELDS if original[field]!=current[field]}
        require(not fields or (key==('subject','temp') and fields=={'mtimeNs'}
            and original['kind']==current['kind']=='directory'),
            'Normal invocation changed undeclared owned input fields: '+repr(key)+' '+repr(sorted(fields)))
    result['complete']=True
    return result

def case_directory(scenario):
    require(scenario in SCENARIOS,'Unknown exact full-entry scenario')
    return ROOT/('c'+format(SCENARIOS.index(scenario),'02d'))

def prepare_output_root(parent, host):
    parent=pathlib.Path(parent);host=pathlib.Path(host)
    require(parent.is_absolute() and host.is_absolute(),'Explicit absolute output root and host are required')
    require(str(parent.resolve(strict=True))==str(parent) and parent.is_dir(),
        'Output parent is not an existing canonical directory')
    for component in [parent]+list(parent.parents):
        info=component.lstat()
        require(component.is_dir() and not component.is_symlink()
            and not (getattr(info,'st_file_attributes',0)&0x400),'Output parent has a link/reparse or non-directory ancestor')
    require(composition.fact(host)['path']==str(host),'Host executable is not exact/canonical')
    child=parent/('e'+secrets.token_hex(8));child.mkdir()
    return child

def normal_path_budget(root):
    """Bound the fixed fixture's concrete source-owned names before any child."""
    require(SOURCE_HASH_BEFORE==composition.PREVIEW_SOURCE_SHA,'Path templates require the exact reviewed installer')
    guid='0'*32;rows=[]
    for scenario in ('positive','no-open'):
        case=root/('c'+format(SCENARIOS.index(scenario),'02d'))
        temp=case/'subject/temp'
        compiler=temp/('SalahWidgetCompiler-'+guid)
        scratch=temp/('SalahWidgetAttempt-'+guid)
        bundle=case/'host-home'/('SalahWidgetBundle-'+guid)
        candidates=[('compiler-'+name,compiler/name) for name in ('native.cs','native.dll','compiler.stdout.bin','compiler.stderr.bin')]
        candidates += [('scratch-download',scratch/('download-'+guid+'.partial')),
            ('scratch-preset',scratch/('preset-'+guid+'.partial')),
            ('published-chromium',bundle/'downloads'/(guid+'-tabliss-chromium.zip')),
            ('published-firefox',bundle/'downloads'/(guid+'-tabliss-firefox-signed.xpi')),
            ('published-preset',bundle/'presets'/(guid+'-salah-widget.tablissng.json')),
            ('download-publication-partial',bundle/'downloads'/(guid+'.partial')),
            ('preset-publication-partial',bundle/'presets'/(guid+'.partial')),
            ('extracted-fixture-manifest',bundle/('unpacked-'+guid)/'manifest.json')]
        for role,path in candidates:
            rows.append(dict(scenario=scenario,role=role,pathTemplate=str(path),
                utf16Units=len(str(path).encode('utf-16-le'))//2))
    result=dict(schema='r0016-full-entry-path-budget.v1',sourceSha256=SOURCE_HASH_BEFORE,
        fixture=str(root),guidTemplate='Each 32-hex source GUID is represented by 32 zeros; no such template path is created.',
        conservativeHarnessLimitUtf16Units=240,rows=rows,maxUtf16Units=max(row['utf16Units'] for row in rows))
    result['complete']=result['maxUtf16Units']<=result['conservativeHarnessLimitUtf16Units']
    composition.save(root/'normal-path-budget.json',result)
    require(result['complete'],'Fixed normal fixture paths exceed the declared harness path budget')
    return result

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
    env=dict(composition.owned_environment(os.environ), INSTALL_OWNED_PARENTS='|'.join(map(str,paths)),
             INSTALL_FIXTURE_ROOT=str(ROOT), INSTALL_ACL_BEFORE=str(root/'parent-acl-before.json'),
             INSTALL_ACL_AFTER=str(root/'parent-acl-after.json'))
    for key in list(env):
        if key.upper() == 'PSMODULEPATH': del env[key]
    env['PSModulePath']=native_modules
    # ACL setup itself must start with a separate owned profile and temp state.
    acl_state=root/'acl-host-state'
    for key, part in [('HOME','home'),('USERPROFILE','home'),('TEMP','temp'),('TMP','temp'),('LOCALAPPDATA','local'),('APPDATA','roam')]:
        path=acl_state/part; path.mkdir(parents=True,exist_ok=True); env[key]=str(path)
    env['PSModuleAnalysisCachePath']=str(acl_state/'analysis-cache')
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
    root = case_directory(scenario); root.mkdir()
    subject = root/'subject'; subject.mkdir()
    env = composition.owned_environment(os.environ)
    replacements = {'TEMP','TMP','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','HOME','USERPROFILE','PSMODULEPATH','PSMODULEANALYSISCACHEPATH'}
    for key in list(env):
        if key.upper() in replacements: del env[key]
    (subject/'temp').mkdir()
    # Native CLR/PowerShell startup writes its own home caches. Keep those in
    # a separate owned host boundary, distinct from installer effect targets.
    host_home = root/'host-home'; host_home.mkdir()
    env['HOME'] = env['USERPROFILE'] = str(host_home)
    if os.name == 'nt':
        try:
            protect_parents(root,host,native_modules,[ROOT,root,subject,subject/'temp',host_home])
        except (AssertionError,OSError,subprocess.TimeoutExpired) as error:
            RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='BOOTSTRAP_BLOCKED',error=str(error),observation=dict(fixture=str(root),stage='owned-parent-acl-setup',installerExecuted=False)))
            return False
    # Establish private ancestry before creating any copied input children.
    for key, part in [('TEMP','temp'),('TMP','temp'),('LOCALAPPDATA','local'),('APPDATA','roam'),('PROGRAMFILES','pf'),('PROGRAMFILES(X86)','pf86')]:
        path = subject/part; path.mkdir(exist_ok=True); env[key] = str(path)
    (host_home/'existing-profile-sentinel.bin').write_bytes(b'preserve owned USERPROFILE bytes\n')
    if scenario in ('readable','unreadable'):
        firefox = subject/'roam/Mozilla/Firefox/Profiles/fixture profile'; firefox.mkdir(parents=True)
        (firefox/'extensions.json').write_bytes(b'{"addons":[]}\n')
        (firefox/'readable-peer.json').write_bytes((firefox/'extensions.json').read_bytes())
    elif scenario != 'none':
        chrome = subject/'local/Google/Chrome/User Data/Default'; chrome.mkdir(parents=True)
        if scenario == 'legacy': (chrome/'Extensions/hipekcciheckooncpjeljhnekcoolahp').mkdir(parents=True)
        elif scenario == 'installed': (chrome/'Extensions/dlaogejjiafeobgofajdlkkhjlignalk').mkdir(parents=True)
        else:
            firefox = subject/'roam/Mozilla/Firefox/Profiles/fixture profile'; firefox.mkdir(parents=True)
            (firefox/'extensions.json').write_bytes(b'{"addons":[]}\n')
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
    if normal and host_name=='ps7':
        env['COMPlus_MultiCoreJitNoProfileGather']='1'
    route = 'store' if scenario in ('store','valid-env-store','preview-noopen-store','explicit-source-override') else 'ask' if scenario == 'ask' else 'invalid' if scenario == 'bad-option' else 'github'
    env['SALAH_INSTALL_SOURCE'] = 'invalid' if scenario in ('invalid-env-source','explicit-source-override') else route
    if scenario == 'env-source-default': del env['SALAH_INSTALL_SOURCE']
    command = [host,'-NoProfile','-File',str(SOURCE),'-PresetUrl','' if scenario == 'missing-preset' else 'https://example.invalid/preset',
               '-WidgetHash',env['SALAH_WIDGET_HASH']]
    if scenario not in ('invalid-env-source','valid-env-store','env-source-default'): command += ['-InstallSource',route]
    if not normal: command += ['-DryRun']
    if scenario in ('no-open','preview-noopen-github','preview-noopen-store'): command += ['-NoOpen']
    # Independently observe host-only startup in this same owned profile. No
    # observed path becomes an exclusion: actual entry comparisons remain exact.
    startup = root/'host-only-control'; startup.mkdir()
    host_control = startup/'host-only.ps1'
    # This is a measured source-free calibration workload, not a unique causal repair.
    # Historical warm20 variation remains unresolved; product cache changes still fail.
    preparation_mode='warm-json' if normal and host_name=='ps51' else 'no-gather' if normal else 'default'
    host_control.write_text(warm_control_body(preparation_mode),encoding='ascii')
    preparation_phases={};preparation_cache={}
    if normal:
        preparation_phases['warmBefore']=composition.double_inventory(root,support,startup/'full-before-launch.json',LOCKS)
        preparation_cache['warmBefore']=capture_preparation_cache(root/'analysis-cache',preparation_phases['warmBefore'],startup/'cache-before.raw')
    startup_env=dict(env, INSTALL_READY_FILE=str(startup/'ready'), INSTALL_PROFILE_ACK=str(startup/'ack'),
                     INSTALL_EFFECT_LOG=str(startup/'effects'), INSTALL_BOOTSTRAP_LOG=str(startup/'phases'),
                     INSTALL_READY_NONCE=secrets.token_hex(16), INSTALL_FIXTURE_NORMAL='0')
    startup_env.pop('INSTALL_UNREADABLE_FILE',None)
    try:
        startup_run,startup_window=invoke_with_profile_boundary([host,'-NoProfile','-File',str(host_control)],startup_env,startup,host_home,ENTRY_TIMEOUT_SECONDS,root if normal else None)
        if normal:
            preparation_phases['warmReady']=startup_window.get('fullReady')
            preparation_phases['warmAfter']=composition.double_inventory(root,support,startup/'full-after-exit.json',LOCKS)
            preparation_cache['warmAfter']=capture_preparation_cache(root/'analysis-cache',preparation_phases['warmAfter'],startup/'cache-after.raw')
        require(startup_run.returncode==0 and startup_window['ready'],'Independent host-only baseline failed')
        require(not (startup/'effects').exists() or not (startup/'effects').read_bytes(),'Host-only control reached an installer effect spy')
        warm_json=None
        if normal and host_name=='ps51':
            warm_raw=(startup/'stdout.raw').read_bytes()
            binding_path=root/'warm-json-assembly-binding.json'
            assembly_binding=receive_native_assembly(composition.diagnostic,parse_warm_context(warm_raw),binding_path)
            warm_json=dict(context=receive_warm_context(warm_raw,startup_window,assembly_binding),
                assemblyBinding=assembly_binding,bindingFact=composition.fact(binding_path))
    except (AssertionError,OSError,subprocess.TimeoutExpired) as error:
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='PROFILE_BASELINE_BLOCKED',error=str(error),observation=dict(fixture=str(root),installerExecuted=False,baseline=str(startup/'profile-window.json'))))
        return False
    if scenario in ('readable','unreadable'):
        metadata=firefox/'extensions.json'
        metadata_sha=hashlib.sha256(metadata.read_bytes()).hexdigest()
        env.update(INSTALL_UNREADABLE_FILE=str(metadata),INSTALL_READABLE_PEER=str(firefox/'readable-peer.json'),
                   INSTALL_METADATA_SHA=metadata_sha,INSTALL_UNREADABLE_PROOF=str(root/'unreadable-child-proof.json'))
    paired = None
    if not normal:
        control=root/'control';control.mkdir()
        input_probe=control/'input-probe.ps1'
        input_probe.write_bytes(pathlib.Path(__file__).with_name('install-entry-input-probe.ps1').read_bytes())
        env.update(R0016_INPUT_PROBE=str(input_probe),R0016_MODULE_INPUT_PROOF=str(control/'module-inputs.json'),
                   R0016_INPUT_PHASE='direct-pre-discovery',R0016_ENTRY_SOURCE=str(SOURCE),R0016_ENTRY_SOURCE_SHA=SOURCE_HASH_BEFORE,
                   R0016_EXPECTED_HOST=host_name)
        paired = composition.prepare_pair(root,env,command,host_name,host,native_modules,SOURCE,
            args.preview_core.resolve(),args.window_library.resolve(),HELD_DRIVER,support,protect_parents,scenario)
    if scenario == 'unreadable':
        held=support.NativeReadLock(metadata,ROOT)
        LOCKS[os.path.normcase(str(metadata.absolute()))]=held
        support.save(root/'unreadable-held-before.json',held.initial)
        require(held.initial['sha256']==metadata_sha,'Metadata bytes changed before exclusive fixture acquisition')
    direct_inputs_before=composition.double_inventory(root,support,root/'direct-full-before-launch.json',LOCKS)
    if normal:
        preparation_phases['productBefore']=direct_inputs_before
        preparation_cache['productBefore']=capture_preparation_cache(root/'analysis-cache',direct_inputs_before,root/'cache-product-before.raw')
    source_inventory_before=support.profile_snapshot(SOURCE)
    direct_launch=dict(command=command,environment=dict(env),cwd=str(pathlib.Path.cwd().resolve()),sourceInventory=source_inventory_before)
    support.save(root/'direct-launch-inputs.json',direct_launch)
    if paired:
        require(direct_inputs_before['rows']==paired['directPrepared']['rows'],'Direct inputs changed after pair association')
        require(direct_launch['environment']==paired['association']['directEnvironment'] and source_inventory_before==paired['association']['sourceInventory'],'Direct environment/source inputs changed after association')
    before = snapshot(subject)
    (root/'subject-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    command_started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    command_clock = time.monotonic()
    try:
        run,profile_window = invoke_with_profile_boundary(command,env,root/'entry-profile-window',host_home,ENTRY_TIMEOUT_SECONDS,root)
    except Exception as error:
        partial_out=getattr(error,'stdout',None) or b''
        partial_err=getattr(error,'stderr',None) or b''
        (root/'stdout.txt').write_bytes(partial_out)
        (root/'stderr.txt').write_bytes(partial_err)
        after=snapshot(subject)
        (root/'subject-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
        effects=(root/'effects').read_text(encoding='utf-8-sig').splitlines() if (root/'effects').exists() else []
        phases=(root/'bootstrap-phases.txt').read_text(encoding='utf-8-sig').splitlines() if (root/'bootstrap-phases.txt').exists() else []
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,error=str(error),
                            classification='ENTRY_TIMEOUT' if isinstance(error,subprocess.TimeoutExpired) else 'BOOTSTRAP_BLOCKED' if not ready(root,env) else 'ENTRY_ACQUISITION_FAILED',
                            observation=dict(command=command,fixture=str(root),interceptionLoaded=ready(root,env),
                            commandStartedUtc=command_started,elapsedSeconds=time.monotonic()-command_clock,timeoutSeconds=ENTRY_TIMEOUT_SECONDS,
                            bootstrapPhases=phases,snapshotUnchanged=before==after,effects=effects,profileWindow=str(root/'entry-profile-window/profile-window.json'),hostBaseline=str(startup/'profile-window.json'),
                            stdout=str(root/'stdout.txt'),stderr=str(root/'stderr.txt'),
                            directCleanupReceipt=getattr(error,'r0016_cleanup_receipt',None))))
        return False
    stdout = run.stdout.decode('utf-8',errors='replace'); stderr = run.stderr.decode('utf-8',errors='replace')
    (root/'stdout.txt').write_bytes(run.stdout); (root/'stderr.txt').write_bytes(run.stderr)
    effect_path = root/'effects'
    effects = [tuple(row.split('\t',1)) for row in effect_path.read_text(encoding='utf-8-sig').splitlines()] if effect_path.exists() else []
    after=snapshot(subject)
    (root/'subject-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
    direct_inputs_after=composition.double_inventory(root,support,root/'direct-full-after-exit.json',LOCKS)
    if normal:
        preparation_phases['productAfter']=direct_inputs_after
        preparation_cache['productAfter']=capture_preparation_cache(root/'analysis-cache',direct_inputs_after,root/'cache-product-after.raw')
    require(support.profile_snapshot(SOURCE)==source_inventory_before,'Source bytes or metadata changed during direct entry')
    unchanged = before == after
    observation = dict(command=command,fixture=str(root),entryExit=run.returncode,interceptionLoaded=ready(root,env),readinessNonce=env['INSTALL_READY_NONCE'],snapshotUnchanged=unchanged,effects=effects,hostStartupState=snapshot(host_home),stdout=str(root/'stdout.txt'),stderr=str(root/'stderr.txt'),commandStartedUtc=command_started,elapsedSeconds=time.monotonic()-command_clock,timeoutSeconds=ENTRY_TIMEOUT_SECONDS)
    observation.update(profileWindow=profile_window,hostOnlyBaseline=startup_window,
                       profileScope='Complete owned USERPROFILE before launch, at actual PID/nonce readiness, and after exit; no path-name exclusions.',
                       fullInputsBefore=direct_inputs_before,fullInputsAtReady=profile_window.get('fullReady'),fullInputsAfter=direct_inputs_after,
                       directLaunchInputs=direct_launch,
                       legacyLifecycleChecks=dict(startupQuiescent=profile_window['before']==profile_window['atReady'],fullProfileUnchanged=profile_window['before']==profile_window['after']),
                       compositionScope='Direct -File semantics and paired held complete-file effects are separate observations; lifecycle deltas are retained, never subtracted.')
    if normal:
        preparation_phases['productReady']=profile_window.get('fullReady')
        phase_paths=dict(warmBefore=startup/'full-before-launch.json',warmReady=startup/'full-at-ready.json',
            warmAfter=startup/'full-after-exit.json',productBefore=root/'direct-full-before-launch.json',
            productReady=root/'entry-profile-window/full-at-ready.json',productAfter=root/'direct-full-after-exit.json')
        observation['normalPreparation']=dict(schema='r0016-normal-preparation.v1',mode=preparation_mode,
            holdSeconds=20 if host_name=='ps51' else 0,script=composition.fact(host_control),
            phaseFacts={name:composition.fact(path) for name,path in phase_paths.items()},
            cacheCaptures=preparation_cache,warmJsonContext=warm_json)
    try:
        if normal:
            raw_cache={name:pathlib.Path(value['capture']['path']).read_bytes() if value['capture'] else None
                for name,value in preparation_cache.items()}
            require_normal_preparation(observation,host_name,scenario,host_control.read_bytes(),preparation_phases,
                raw_cache,(startup/'stdout.raw').read_bytes(),warm_json['assemblyBinding'] if warm_json else None)
        if scenario not in ('bad-option','invalid-env-source'):
            require(ready(root,env),'BOOTSTRAP_BLOCKED: final startup interception nonce missing or wrong')
            if normal:
                require(profile_window['before']==profile_window['atReady'],'PROFILE_STARTUP_NOT_QUIESCENT: normal control changed USERPROFILE before the late interception boundary')
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
            require(type(run.returncode) is int and run.returncode == 0,'Normal direct entry failed: '+stdout+stderr)
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
            observation['normalConfinement']=dict(retainedRelative=stage.name,expectedRetainedPaths=[p.relative_to(host_home).as_posix() for p in expected])
            observation['normalConfinementValidated']=True
            composition.require_positive_confinement(observation,support)
            require_normal_input_postcondition(observation)
        else:
            require(unchanged and not effects,'Dry-run changed owned state or reached effects')
            require(not list(host_home.glob('SalahWidgetBundle-*')),'Dry-run created a retained bundle outside the temp subject')
            require(paired is not None,'Preview row has no same-input held pair')
            held_result=composition.invoke_pair(paired,support,observation)
            observation['heldComposition']=held_result
            observation['sourceInputRelation']=held_result['observation']['sourceInputRelation']
            composition.verify_input_mapping(paired['association']['entries'],direct_inputs_before['rows'],paired['heldPrepared']['rows'])
            composition.exact_exit(run.returncode,held_result['result'],scenario)
            failure = scenario in composition.FAILURE_SCENARIOS
            if scenario == 'invalid-env-source':
                require(('InstallSource' in stdout+stderr or 'SALAH_INSTALL_SOURCE' in stdout+stderr) and 'Preview only; no changes made' not in stdout,
                        'Invalid environment source did not produce a specific unsuccessful option refusal')
            if not failure:
                require('Preview only; no changes made' in stdout,'Preview completion missing')
                require('Importing the preset replaces your current TablissNG dashboard' in stdout,'Replacement warning missing')
                if scenario == 'ask': require('Install source unresolved' in stdout,'Choice fabricated')
                if scenario in ('github','cached','mixed','env-source-default'): require('release/version/path unresolved' in stdout,'Remote facts fabricated or environment-unset GitHub default changed')
                if scenario == 'missing-preset': require('No preset URL configured' in stdout,'Empty preset URL not honored')
                if scenario in ('valid-env-store','explicit-source-override'):
                    for url in ('https://chromewebstore.google.com/detail/tablissng/dlaogejjiafeobgofajdlkkhjlignalk','https://addons.mozilla.org/en-US/firefox/addon/tablissng/'):
                        require(re.search(r'^Would open official store: '+re.escape(url)+r'\r?$',stdout,re.M),'Valid environment source did not select the resolved fixture store plan')
                    require('Install source unresolved' not in stdout,'Valid environment store source remained unresolved')
                if scenario in ('preview-noopen-github','preview-noopen-store'):
                    automatic=[clause for clause in re.split(r'[;\r\n]+',stdout) if re.search(r'\bwould\b.*\b(open|launch)\b',clause,re.I)]
                    require(not automatic,'NoOpen preview promises automatic browser opens: '+repr(automatic))
                    require(re.search(r'NoOpen|NO_OPEN|open(?:ed)? manually|pages? yourself',stdout,re.I),'NoOpen preview lacks manual-opening guidance')
        RESULTS.append(dict(host=host_name,case=scenario,pass_=True,observation=observation))
    except Exception as error:
        if getattr(error, 'r0016_cleanup_receipt', None) is not None:
            observation['heldCleanupReceipt'] = error.r0016_cleanup_receipt
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,error=str(error),observation=observation))
    return scenario in ('bad-option','invalid-env-source') or ready(root,env)

def case(host_name,host,native_modules,scenario):
    start=len(RESULTS)
    keep_running=False
    try:
        keep_running=_case_impl(host_name,host,native_modules,scenario)
    except Exception as error:
        RESULTS.append(dict(host=host_name,case=scenario,pass_=False,classification='FIXTURE_ACQUISITION_FAILED',error=str(error),observation=dict(fixture=str(case_directory(scenario)))))
    finally:
        for key,held in list(LOCKS.items()):
            try:
                restored=held.restore()
                support.save(case_directory(scenario)/'unreadable-restoration.json',restored)
                for row in RESULTS[start:]: row.setdefault('observation',{})['unreadableRestoration']=restored
            except Exception as error:
                held.close_after_failure()
                for row in RESULTS[start:]: row.update(pass_=False,restorationError=str(error))
                keep_running=False
            finally:
                del LOCKS[key]
    return keep_running

if os.name != 'nt':
    print(json.dumps(dict(schema='r0016-native-entry-composition-result.v1',status='BLOCKED_NATIVE_HOST',
        expectedHost=args.host[0],commandHost=str(args.host_executable),nativeWindows=False,installerExecuted=False)))
    sys.exit(2)

ROOT=prepare_output_root(args.output_root,args.host_executable)
try:
    PATH_BUDGET=normal_path_budget(ROOT)
except Exception as error:
    RESULTS.append(dict(host=args.host[0],case='fixture-path-preflight',pass_=False,
        classification='PREFLIGHT_FAILED',error=str(error),observation=dict(fixture=str(ROOT),installerExecuted=False)))
else:
    for host_name,host,native_modules in HOSTS:
        for scenario in args.scenario or SCENARIOS:
            if not case(host_name,host,native_modules,scenario):
                break  # Retain a terminal receipt; do not repeat a failed host bootstrap.
source_after=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if source_after!=SOURCE_HASH_BEFORE:
    RESULTS.append(dict(case='exact source custody',pass_=False,error='Source changed during fixture'))
status='FAIL' if any(not row['pass_'] for row in RESULTS) else 'PASS'
report=dict(schema='r0016-native-entry-composition.v1',status=status,instrumentStatus='NEW_PRODUCT_COMPOSITION',
    nativeCarrierQualificationRequired=True,expectedHost=args.host[0],commandHost=str(args.host_executable),
    source=source_after,sourceBefore=SOURCE_HASH_BEFORE,sourceUnchanged=source_after==SOURCE_HASH_BEFORE,
    sourceFact=composition.fact(SOURCE),presetFact=composition.fact(PRESET),
    testSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    supportSha256=hashlib.sha256(SUPPORT_PATH.read_bytes()).hexdigest(),
    compositionSha256=hashlib.sha256(COMPOSITION_PATH.read_bytes()).hexdigest(),
    compositionCoreSha256=hashlib.sha256(composition.CORE_PATH.read_bytes()).hexdigest(),
    diagnosticSha256=hashlib.sha256(composition.DIAGNOSTIC_PATH.read_bytes()).hexdigest(),
    heldDriverSha256=hashlib.sha256(HELD_DRIVER.read_bytes()).hexdigest(),
    preset=hashlib.sha256(PRESET.read_bytes()).hexdigest(),fixture=str(ROOT),pathBudget=PATH_BUDGET,
    selectedHosts=args.host,selectedScenarios=args.scenario or SCENARIOS,results=RESULTS,nativeWindows=True,
    scope='NEW exact -File product observations with separately qualified held driver, complete raw lifecycle inventories, source-bound input relation and mandatory normal confinement. No historical credit is implied.')
report_path=ROOT/'entry-composition-report.json'
composition.save(report_path,report)
print(json.dumps(dict(schema='r0016-native-entry-composition-result.v1',status=status,expectedHost=args.host[0],
    commandHost=str(args.host_executable),nativeWindows=True,fixture=str(ROOT),report=composition.fact(report_path)),indent=2))
sys.exit(0 if status=='PASS' else 1)
