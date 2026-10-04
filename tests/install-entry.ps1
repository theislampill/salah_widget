param(
    [string]$SourceFile = (Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'),
    [ValidateSet('github','store','ask','installed','legacy','mixed','none','cached','missing-preset','bad-option','no-open','positive')][string]$Scenario='github'
)
$ErrorActionPreference='Stop'
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('salah-install-entry-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($fixture)
foreach($part in 'temp','local','roam','pf','pf86') { [void][IO.Directory]::CreateDirectory((Join-Path $fixture $part)) }
$env:TEMP=Join-Path $fixture 'temp'; $env:TMP=$env:TEMP
$env:LOCALAPPDATA=Join-Path $fixture 'local'; $env:APPDATA=Join-Path $fixture 'roam'
$env:ProgramFiles=Join-Path $fixture 'pf'; ${env:ProgramFiles(x86)}=Join-Path $fixture 'pf86'
$env:SALAH_INSTALL_SOURCE='github'
$env:SALAH_WIDGET_HASH='lat=24.47&lon=39.61&method=4'
if($Scenario -ne 'none') {
    $chrome=Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Default'
    [void][IO.Directory]::CreateDirectory($chrome)
    if($Scenario -eq 'legacy') { [void][IO.Directory]::CreateDirectory((Join-Path $chrome 'Extensions\hipekcciheckooncpjeljhnekcoolahp')) }
    if($Scenario -eq 'installed') { [void][IO.Directory]::CreateDirectory((Join-Path $chrome 'Extensions\dlaogejjiafeobgofajdlkkhjlignalk')) }
    if($Scenario -ne 'legacy' -and $Scenario -ne 'installed') {
        [void][IO.Directory]::CreateDirectory((Join-Path $env:APPDATA 'Mozilla\Firefox\Profiles\fixture profile'))
    }
    if($Scenario -eq 'mixed') {
        [void][IO.Directory]::CreateDirectory((Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data\Default\Extensions\lklaendlmlfkaabeleddanafeinnenih'))
    }
}
$payload=Join-Path $fixture 'payload'; [void][IO.Directory]::CreateDirectory($payload)
[IO.File]::WriteAllText((Join-Path $payload 'manifest.json'),'{"manifest_version":3,"name":"Fixture","version":"1.0"}')
Add-Type -AssemblyName System.IO.Compression.FileSystem
$assetZip=Join-Path $fixture 'fixture.zip'
[IO.Compression.ZipFile]::CreateFromDirectory($payload,$assetZip)
if($Scenario -eq 'cached') {
    $cache=Join-Path $env:TEMP 'SalahWidgetInstaller\downloads\v-fixture'
    [void][IO.Directory]::CreateDirectory($cache)
    [IO.File]::Copy($assetZip,(Join-Path $cache 'tabliss-chromium.zip'))
    [IO.File]::Copy($assetZip,(Join-Path $cache 'tabliss-firefox-signed.xpi'))
    [void][IO.Directory]::CreateDirectory((Join-Path $cache 'tabliss-chromium-unpacked'))
    [IO.File]::WriteAllText((Join-Path $cache 'tabliss-chromium-unpacked\marker.txt'),'keep cached unpacked')
    $presetDir=Join-Path $env:TEMP 'SalahWidgetInstaller\presets'
    [void][IO.Directory]::CreateDirectory($presetDir)
    [IO.File]::WriteAllText((Join-Path $presetDir 'salah-widget.tablissng.json'),'{"input":"#local=1","sentinel":"keep"}')
}
function Snapshot {
    @([IO.Directory]::EnumerateFileSystemEntries($fixture,'*',[IO.SearchOption]::AllDirectories) | Sort-Object | ForEach-Object {
        $path=$_; $attr=[IO.File]::GetAttributes($path)
        $hash=if(($attr -band [IO.FileAttributes]::Directory) -eq 0){ (Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }else{''}
        ($path.Substring($fixture.Length)+'|'+$attr+'|'+$hash)
    }) -join "`n"
}
$before=Snapshot
$global:InstallFixtureEvents=@()
$normal=$Scenario -eq 'positive' -or $Scenario -eq 'no-open'
function In-Fixture([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if(-not $full.StartsWith(($fixture+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){ throw ('Effect escaped fixture: '+$full) }
}
function New-Item { param($ItemType,$Path,[switch]$Force)
    foreach($p in @($Path)){ In-Fixture $p; $global:InstallFixtureEvents+=('mkdir:'+$p) }
    Microsoft.PowerShell.Management\New-Item -ItemType $ItemType -Path $Path -Force:$Force
}
function Invoke-RestMethod { param($Uri,$Headers)
    $global:InstallFixtureEvents+=('metadata:'+$Uri)
    if(-not $normal){ throw 'Denied fixture network' }
    [pscustomobject]@{tag_name='v-fixture';assets=@(
        [pscustomobject]@{name='tabliss-chromium.zip';browser_download_url='https://example.invalid/chromium'},
        [pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/firefox'}
    )}
}
function Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing)
    $global:InstallFixtureEvents+=('download:'+$Uri); In-Fixture $OutFile
    if(-not $normal){ throw 'Denied fixture network' }
    if($Uri -like '*preset*'){ [IO.File]::WriteAllText($OutFile,'{"input":"#local=1"}') }
    else { [IO.File]::Copy($assetZip,$OutFile) }
}
function Set-Clipboard { param($Value) $global:InstallFixtureEvents+=('clipboard:'+$Value) }
function Start-Process { param($FilePath,$ArgumentList) $global:InstallFixtureEvents+=('open:'+$FilePath+' '+$ArgumentList) }
function Remove-Item { param($LiteralPath,[switch]$Recurse,[switch]$Force)
    In-Fixture $LiteralPath; $global:InstallFixtureEvents+=('remove:'+$LiteralPath)
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Recurse:$Recurse -Force:$Force
}
function Expand-Archive { param($LiteralPath,$DestinationPath,[switch]$Force)
    In-Fixture $LiteralPath; In-Fixture $DestinationPath; $global:InstallFixtureEvents+=('extract:'+$LiteralPath)
    Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $LiteralPath -DestinationPath $DestinationPath -Force:$Force
}
function Read-Host { param($Prompt) $global:InstallFixtureEvents+=('prompt:'+$Prompt); if($Prompt -like 'Select target*'){return 'all'}; return '' }
$arguments=@{PresetUrl='https://example.invalid/preset';InstallSource='github';WidgetHash=$env:SALAH_WIDGET_HASH}
if(-not $normal){$arguments.DryRun=$true}
if($Scenario -eq 'no-open'){$arguments.NoOpen=$true}
if($Scenario -in @('ask','store')){$arguments.InstallSource=$Scenario}
if($Scenario -eq 'missing-preset'){$arguments.PresetUrl=''}
if($Scenario -eq 'bad-option'){$arguments.InstallSource='invalid'}
$global:LASTEXITCODE=0; $entryError=$null
try { & $SourceFile @arguments; $entryExit=$LASTEXITCODE } catch { $entryExit=1; $entryError=$_.Exception.Message+" "+$_.ScriptStackTrace }
$after=Snapshot
$expectsFailure=$Scenario -in @('legacy','none','bad-option')
$pass=if($normal){
    $global:InstallFixtureEvents -match '^download:' -and $global:InstallFixtureEvents -match '^extract:' -and $global:InstallFixtureEvents -match '^clipboard:' -and $entryExit -eq 0 -and
        ($Scenario -eq 'no-open' -or ($global:InstallFixtureEvents -contains 'open:chrome://newtab/ ' -and $global:InstallFixtureEvents -contains 'open:about:newtab ')) -and
        ($Scenario -ne 'no-open' -or -not ($global:InstallFixtureEvents -match '^open:'))
}else{
    $before -ceq $after -and $global:InstallFixtureEvents.Count -eq 0 -and (($entryExit -eq 0) -ne $expectsFailure)
}
[pscustomobject]@{host=$PSVersionTable.PSVersion.ToString();scenario=$Scenario;fixture=$fixture;source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();entryExit=$entryExit;error=$entryError;snapshotUnchanged=($before -ceq $after);events=$global:InstallFixtureEvents;pass=[bool]$pass} | ConvertTo-Json -Depth 8
if(-not $pass){exit 1}
