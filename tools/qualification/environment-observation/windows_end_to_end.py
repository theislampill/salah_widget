#!/usr/bin/env python3
"""Staging-parent environment observation: Windows normal-mode entry.

Runs the installer source unmodified in normal (non-preview) mode with the
host account's real TEMP and USERPROFILE, so staging admission sees the real
parents. Browser discovery points at a fixture profile tree. Every network,
clipboard, browser-open and prompt cmdlet is replaced by a private module
loaded ahead of the native one, using the same startup-interception approach
as the repository's native entry test: no network, no store pages, no
clipboard. The run's own retained root is removed afterwards and recorded.
This is an observation, not a gate: it always exits 0.
"""
import argparse, hashlib, json, os, pathlib, secrets, subprocess, sys, tempfile, time, zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, type=pathlib.Path)
parser.add_argument('--preset', required=True, type=pathlib.Path)
parser.add_argument('--host-name', required=True, choices=('ps51', 'ps7'))
parser.add_argument('--host-exe', required=True)
parser.add_argument('--fixture-parent', required=True, type=pathlib.Path)
parser.add_argument('--output', required=True, type=pathlib.Path)
args = parser.parse_args()

MODULE = r'''
Import-Module $env:OBS_NATIVE_UTILITY -Scope Local
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$env:ProgramFiles=$env:OBS_FIXTURE_PF
${env:ProgramFiles(x86)}=$env:OBS_FIXTURE_PF86
function Record([string]$Kind,[string]$Value) { [IO.File]::AppendAllText($env:OBS_EFFECT_LOG,$Kind+"`t"+$Value+[Environment]::NewLine) }
function Assert-Allowed([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    foreach($prefix in $env:OBS_ALLOWED_PREFIXES.Split('|')) { if($prefix -and $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){ return } }
    throw ('Effect outside observed staging and fixture roots: '+$full)
}
function Write-Host { param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline,[object]$Separator=' ')
    $text=(@($Object) -join $Separator); if($NoNewline){[Console]::Write($text)}else{[Console]::WriteLine($text)} }
function New-Item { param($ItemType,$Path,[switch]$Force)
    foreach($p in @($Path)){ Assert-Allowed $p; Record 'mkdir' $p }
    Microsoft.PowerShell.Management\New-Item -ItemType $ItemType -Path $Path -Force:$Force }
function Remove-Item { param($LiteralPath,[switch]$Recurse,[switch]$Force)
    Assert-Allowed $LiteralPath; Record 'remove' $LiteralPath
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Recurse:$Recurse -Force:$Force }
function Invoke-RestMethod { param($Uri,$Headers)
    Record 'metadata' $Uri
    [pscustomobject]@{tag_name='v-fixture';assets=@(
        [pscustomobject]@{name='tabliss-chromium.zip';browser_download_url='https://example.invalid/chromium'},
        [pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/firefox'})} }
function Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing)
    Record 'download' $Uri; Assert-Allowed $OutFile
    if($Uri -eq 'https://example.invalid/preset'){[IO.File]::Copy($env:OBS_PRESET_FIXTURE,$OutFile,$true)}
    else{[IO.File]::Copy($env:OBS_ASSET_ZIP,$OutFile,$true)} }
function Expand-Archive { param($LiteralPath,$DestinationPath,[switch]$Force) Record 'expand-archive' $LiteralPath; throw 'Expand-Archive is not expected' }
function Set-Clipboard { param($Value) Record 'clipboard' $Value }
function Start-Process { param($FilePath,$ArgumentList) Record 'open' ($FilePath+' '+$ArgumentList) }
function Read-Host { param($Prompt) Record 'prompt' $Prompt; if($Prompt -like 'Select target*'){return 'all'}; return '' }
Export-ModuleMember -Function Write-Host,New-Item,Remove-Item,Invoke-RestMethod,Invoke-WebRequest,Expand-Archive,Set-Clipboard,Start-Process,Read-Host -Cmdlet *
[IO.File]::WriteAllText($env:OBS_READY_FILE,([string]$PID+"`t"+$env:OBS_READY_NONCE))
'''


def listing(parent):
    try:
        return sorted(p.name for p in pathlib.Path(parent).iterdir() if p.name.startswith('SalahWidget'))
    except OSError as error:
        return ['<unreadable: %s>' % error]


report = {'schema': 'staging-parent-environment-observation.windows-entry.v1', 'host': args.host_name,
          'sourceSha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
          'sourceGitBlob': os.environ.get('OBSERVED_INSTALL_PS1_BLOB')}
real_temp = os.environ['TEMP']
real_profile = os.environ['USERPROFILE']
root = pathlib.Path(tempfile.mkdtemp(prefix='envobs-entry-', dir=str(args.fixture_parent))).resolve()
subject = root / 'subject'
for part in ('local', 'roam', 'pf', 'pf86'):
    (subject / part).mkdir(parents=True)
(subject / 'local/Google/Chrome/User Data/Default').mkdir(parents=True)
firefox = subject / 'roam/Mozilla/Firefox/Profiles/fixture profile'
firefox.mkdir(parents=True)
(firefox / 'extensions.json').write_text('{"addons":[]}\n', encoding='utf-8')
asset = root / 'fixture.zip'
with zipfile.ZipFile(asset, 'w') as archive:
    archive.writestr('manifest.json', '{"manifest_version":3,"name":"Fixture","version":"1.0"}')
module = root / 'modules/Microsoft.PowerShell.Utility'
module.mkdir(parents=True)
(module / 'Microsoft.PowerShell.Utility.psm1').write_text(MODULE, encoding='ascii')
(module / 'Microsoft.PowerShell.Utility.psd1').write_text("@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='5b0a43e8-63a5-4b8f-9b1e-7d5a1f0a9c11';FunctionsToExport=@('Write-Host','New-Item','Remove-Item','Invoke-RestMethod','Invoke-WebRequest','Expand-Archive','Set-Clipboard','Start-Process','Read-Host');CmdletsToExport='*';AliasesToExport=@()}\n", encoding='ascii')
native_modules = (r'C:\Windows\System32\WindowsPowerShell\v1.0\Modules' if args.host_name == 'ps51'
                  else str(pathlib.Path(args.host_exe).parent / 'Modules'))
env = dict(os.environ)
for key in list(env):
    if key.upper() in {'LOCALAPPDATA', 'APPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PSMODULEPATH', 'PSMODULEANALYSISCACHEPATH'}:
        del env[key]
nonce = secrets.token_hex(16)
env.update(LOCALAPPDATA=str(subject / 'local'), APPDATA=str(subject / 'roam'), PROGRAMFILES=str(subject / 'pf'),
           **{'PROGRAMFILES(X86)': str(subject / 'pf86')},
           PSModulePath=str(root / 'modules') + ';' + native_modules, PSModuleAnalysisCachePath=str(root / 'analysis-cache'),
           OBS_NATIVE_UTILITY=str(pathlib.Path(native_modules) / 'Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1'),
           OBS_FIXTURE_PF=str(subject / 'pf'), OBS_FIXTURE_PF86=str(subject / 'pf86'),
           OBS_EFFECT_LOG=str(root / 'effects.txt'), OBS_READY_FILE=str(root / 'ready.txt'), OBS_READY_NONCE=nonce,
           OBS_PRESET_FIXTURE=str(args.preset.resolve()), OBS_ASSET_ZIP=str(asset),
           OBS_ALLOWED_PREFIXES='|'.join([str(subject) + os.sep, os.path.join(real_temp, 'SalahWidget'), os.path.join(real_profile, 'SalahWidgetBundle-')]),
           SALAH_INSTALL_SOURCE='github', SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4')
command = [args.host_exe, '-NoProfile', '-File', str(args.source.resolve()), '-PresetUrl', 'https://example.invalid/preset',
           '-InstallSource', 'github', '-WidgetHash', env['SALAH_WIDGET_HASH'], '-NoOpen']
report['parents'] = {'tempNameClass': 'runner TEMP', 'profileNameClass': 'runner USERPROFILE'}
before = {'temp': listing(real_temp), 'profile': listing(real_profile)}
started = time.monotonic()
try:
    run = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
    report['exit'] = run.returncode
    report['stdout'] = run.stdout.decode('utf-8', errors='replace')
    report['stderr'] = run.stderr.decode('utf-8', errors='replace')
except subprocess.TimeoutExpired as error:
    report['exit'] = None
    report['timeout'] = True
    report['stdout'] = (error.stdout or b'').decode('utf-8', errors='replace')
    report['stderr'] = (error.stderr or b'').decode('utf-8', errors='replace')
report['elapsedSeconds'] = round(time.monotonic() - started, 1)
ready = root / 'ready.txt'
report['interceptionLoaded'] = ready.is_file() and ready.read_text(encoding='utf-8-sig').endswith(nonce)
report['effects'] = (root / 'effects.txt').read_text(encoding='utf-8-sig').splitlines() if (root / 'effects.txt').exists() else []
after = {'temp': listing(real_temp), 'profile': listing(real_profile)}
report['createdAfterRun'] = {k: [n for n in after[k] if n not in before[k]] for k in after}
out = report['stdout']
report['classification'] = ('staging-refused' if 'Staging parent is not owned' in out + report['stderr'] or 'Staging ancestor permits' in out + report['stderr']
                            else 'manual-action-pending' if 'Manual browser installation/import remain pending' in out
                            else 'other')
removed = []
for name in report['createdAfterRun']['profile']:
    if name.startswith('SalahWidgetBundle-'):
        path = pathlib.Path(real_profile) / name
        files = sorted(str(p.relative_to(path)) for p in path.rglob('*'))
        try:
            import shutil
            shutil.rmtree(path)
            removed.append({'name': name, 'contents': files, 'removed': True})
        except OSError as error:
            removed.append({'name': name, 'contents': files, 'removed': False, 'error': str(error)})
report['observerRemovedRetained'] = removed
report['remainingAfterObserverCleanup'] = {'temp': [n for n in listing(real_temp) if n not in before['temp']],
                                           'profile': [n for n in listing(real_profile) if n not in before['profile']]}
args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('%s: exit=%s classification=%s created=%s' % (args.host_name, report['exit'], report['classification'], report['createdAfterRun']))
sys.exit(0)
