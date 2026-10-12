#!/usr/bin/env python3
"""Direct native -File entry with private startup spies; no owner profile is used."""
import collections, hashlib, json, os, pathlib, subprocess, sys, tempfile, zipfile

SOURCE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1]/'install.ps1').resolve()
HOSTS = [('ps51', r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe', r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\Modules'),
         ('ps7', r'C:\Program Files\PowerShell\7\pwsh.exe', r'C:\Program Files\PowerShell\7\Modules')]
ROOT = pathlib.Path(tempfile.mkdtemp(prefix='salah native entry-'))
RESULTS = []
MODULE = r'''
Import-Module $env:INSTALL_NATIVE_UTILITY -Scope Local
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
# The native host can restore Windows ProgramFiles locations at startup.
# Set the discovery roots in this private child session before Get-Targets.
$env:ProgramFiles=$env:INSTALL_FIXTURE_PF
${env:ProgramFiles(x86)}=$env:INSTALL_FIXTURE_PF86
[IO.File]::WriteAllText($env:INSTALL_READY_FILE,'private startup spies loaded')
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
    if($Uri -eq 'https://example.invalid/preset'){[IO.File]::WriteAllText($OutFile,'{"input":"#local=1"}')}
    else{[IO.File]::Copy($env:INSTALL_ASSET_ZIP,$OutFile)}
}
function Expand-Archive { param($LiteralPath,$DestinationPath,[switch]$Force)
    In-Fixture $LiteralPath; In-Fixture $DestinationPath; Record 'extract' $LiteralPath
    Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $LiteralPath -DestinationPath $DestinationPath -Force:$Force
}
function Set-Clipboard { param($Value) Record 'clipboard' $Value }
function Start-Process { param($FilePath,$ArgumentList) Record 'open' ($FilePath+' '+$ArgumentList) }
function Read-Host { param($Prompt) Record 'prompt' $Prompt; if($Prompt -like 'Select target*'){return 'all'}; return '' }
Export-ModuleMember -Function Write-Host,New-Item,Remove-Item,Invoke-RestMethod,Invoke-WebRequest,Expand-Archive,Set-Clipboard,Start-Process,Read-Host -Cmdlet *
'''

def require(value, reason):
    if not value: raise AssertionError(reason)

def snapshot(root):
    return [(str(p.relative_to(root)), p.stat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else '') for p in sorted(root.rglob('*'))]

def case(host_name, host, native_modules, scenario):
    root = ROOT/(host_name+'-'+scenario); root.mkdir()
    subject = root/'subject'; subject.mkdir()
    env = dict(os.environ)
    replacements = {'TEMP','TMP','LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','HOME','USERPROFILE','PSMODULEPATH','PSMODULEANALYSISCACHEPATH'}
    for key in list(env):
        if key.upper() in replacements: del env[key]
    for key, part in [('TEMP','temp'),('TMP','temp'),('LOCALAPPDATA','local'),('APPDATA','roam'),('PROGRAMFILES','pf'),('PROGRAMFILES(X86)','pf86')]:
        path = subject/part; path.mkdir(exist_ok=True); env[key] = str(path)
    # Native CLR/PowerShell startup writes its own home caches. Keep those in
    # a separate owned host boundary, distinct from installer effect targets.
    host_home = root/'host-home'; host_home.mkdir()
    env['HOME'] = env['USERPROFILE'] = str(host_home)
    if scenario != 'none':
        chrome = subject/'local/Google/Chrome/User Data/Default'; chrome.mkdir(parents=True)
        if scenario == 'legacy': (chrome/'Extensions/hipekcciheckooncpjeljhnekcoolahp').mkdir(parents=True)
        elif scenario == 'installed': (chrome/'Extensions/dlaogejjiafeobgofajdlkkhjlignalk').mkdir(parents=True)
        else: (subject/'roam/Mozilla/Firefox/Profiles/fixture profile').mkdir(parents=True)
        if scenario == 'mixed': (subject/'local/Microsoft/Edge/User Data/Default/Extensions/lklaendlmlfkaabeleddanafeinnenih').mkdir(parents=True)
    asset = root/'fixture.zip'
    with zipfile.ZipFile(asset,'w') as archive: archive.writestr('manifest.json','{"manifest_version":3,"name":"Fixture","version":"1.0"}')
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
               INSTALL_READY_FILE=str(root/'ready'), INSTALL_EFFECT_LOG=str(root/'effects'), INSTALL_SUBJECT_ROOT=str(subject),
               INSTALL_FIXTURE_NORMAL='1' if normal else '0', INSTALL_ASSET_ZIP=str(asset),
               INSTALL_FIXTURE_PF=str(subject/'pf'), INSTALL_FIXTURE_PF86=str(subject/'pf86'),
               SALAH_INSTALL_SOURCE='github', SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4')
    command = [host,'-NoProfile','-File',str(SOURCE),'-PresetUrl','' if scenario == 'missing-preset' else 'https://example.invalid/preset',
               '-InstallSource',scenario if scenario in ('ask','store') else 'invalid' if scenario == 'bad-option' else 'github',
               '-WidgetHash',env['SALAH_WIDGET_HASH']]
    if not normal: command += ['-DryRun']
    if scenario == 'no-open': command += ['-NoOpen']
    before = snapshot(subject)
    run = subprocess.run(command,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=25)
    stdout = run.stdout.decode('utf-8',errors='replace'); stderr = run.stderr.decode('utf-8',errors='replace')
    (root/'stdout.txt').write_bytes(run.stdout); (root/'stderr.txt').write_bytes(run.stderr)
    effect_path = root/'effects'
    effects = [tuple(row.split('\t',1)) for row in effect_path.read_text(encoding='utf-8-sig').splitlines()] if effect_path.exists() else []
    unchanged = before == snapshot(subject)
    observation = dict(command=command,fixture=str(root),entryExit=run.returncode,interceptionLoaded=(root/'ready').exists(),snapshotUnchanged=unchanged,effects=effects,hostStartupState=snapshot(host_home),stdout=str(root/'stdout.txt'),stderr=str(root/'stderr.txt'))
    try:
        if scenario != 'bad-option': require((root/'ready').exists(),'Private startup interception did not load')
        if normal:
            require(run.returncode == 0,'Normal direct entry failed: '+stdout+stderr)
            by_kind = collections.defaultdict(list)
            for kind,value in effects: by_kind[kind].append(value)
            require(by_kind['metadata'] == ['https://api.github.com/repos/BookCatKid/TablissNG/releases/latest'],'Wrong release lookup/count')
            require(collections.Counter(by_kind['download']) == collections.Counter(['https://example.invalid/chromium','https://example.invalid/firefox','https://example.invalid/preset']),'Wrong download URLs/counts')
            stage = subject/'temp/SalahWidgetInstaller'
            unpacked = stage/'downloads/v-fixture/tabliss-chromium-unpacked'
            xpi = stage/'downloads/v-fixture/tabliss-firefox-signed.xpi'
            preset = stage/'presets/salah-widget.tablissng.json'
            require(by_kind['extract'] == [str(stage/'downloads/v-fixture/tabliss-chromium.zip')],'Wrong extraction path/count')
            require(collections.Counter(by_kind['clipboard']) == collections.Counter([str(unpacked),str(xpi),str(preset),str(preset)]),'Wrong copied paths/counts')
            require((unpacked/'manifest.json').is_file() and xpi.is_file(),'Actual staged local assets missing')
            require(json.loads(preset.read_text(encoding='utf-8-sig'))['input'] == '#'+env['SALAH_WIDGET_HASH'],'Configured preset not consumed')
            require(len(by_kind['prompt']) == 3,'Normal selection/manual confirmations not reached')
            expected_opens = ['chrome://extensions/ ','chrome://newtab/ ','about:addons ','about:newtab ']
            require(collections.Counter(by_kind['open']) == collections.Counter([] if scenario == 'no-open' else expected_opens),'Wrong manager/newtab opens or store fallback')
            require('Manual browser installation/import remain pending' in stdout,'False install completion wording')
        else:
            require(unchanged and not effects,'Dry-run changed owned state or reached effects')
            failure = scenario in ('legacy','none','bad-option')
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

for host_name, host, native_modules in HOSTS:
    for scenario in ('github','cached','store','ask','installed','mixed','legacy','none','missing-preset','bad-option','positive','no-open'):
        case(host_name,host,native_modules,scenario)
print(json.dumps(dict(source=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),fixture=str(ROOT),results=RESULTS),indent=2))
sys.exit(1 if any(not row['pass_'] for row in RESULTS) else 0)
