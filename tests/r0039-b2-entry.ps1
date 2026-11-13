# R0039 (issue 106) discriminator B2: PowerShell non-interactive / ended-input acknowledgement.
# Runs the EXACT install.ps1 entry in normal mode (not preview) inside a disposable fixture, in the style of
# tests/install-entry.ps1. Everything the installer may write is redirected into the fixture: TEMP/TMP,
# USERPROFILE (retained bundle parent), LOCALAPPDATA, APPDATA, ProgramFiles. One eligible Chrome fixture
# profile. Argument spies replace every external boundary: Invoke-RestMethod returns a FIXTURE release
# (never real metadata), Invoke-WebRequest copies a fixture ZIP or the repository preset into the
# installer's own candidate path (never a real download), Set-Clipboard and Start-Process only record.
# Read-Host is NOT replaced: the point is the host's real prompt behaviour. The caller chooses how the
# host is started (-NonInteractive, or redirected input that ends). Nothing is installed; no browser runs.
# Inputs (environment): R0039_B2_SOURCE (install.ps1), R0039_B2_PRESET (repository preset JSON),
# R0039_B2_FIXTURE (new empty directory). Output: one JSON object on stdout.
$ErrorActionPreference = 'Stop'
$source = $env:R0039_B2_SOURCE; $presetSource = $env:R0039_B2_PRESET
$fixture = [IO.Path]::GetFullPath($env:R0039_B2_FIXTURE)
if (@([IO.Directory]::EnumerateFileSystemEntries($fixture)).Count) { throw 'Fixture must be empty' }
foreach ($part in 'temp','home','local','roam','pf','pf86','payload') { [void][IO.Directory]::CreateDirectory((Join-Path $fixture $part)) }
$env:TEMP = Join-Path $fixture 'temp'; $env:TMP = $env:TEMP; $env:USERPROFILE = Join-Path $fixture 'home'
$env:LOCALAPPDATA = Join-Path $fixture 'local'; $env:APPDATA = Join-Path $fixture 'roam'
$env:ProgramFiles = Join-Path $fixture 'pf'; ${env:ProgramFiles(x86)} = Join-Path $fixture 'pf86'
$env:SALAH_INSTALL_SOURCE = 'github'; $env:SALAH_WIDGET_HASH = 'lat=24.47&lon=39.61&method=4'
[void][IO.Directory]::CreateDirectory((Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Default'))
[IO.File]::WriteAllText((Join-Path $fixture 'payload\manifest.json'), '{"manifest_version":3,"name":"Fixture","version":"1.0"}')
Add-Type -AssemblyName System.IO.Compression.FileSystem
$global:R0039Zip = Join-Path $fixture 'fixture-asset.zip'
[IO.Compression.ZipFile]::CreateFromDirectory((Join-Path $fixture 'payload'), $global:R0039Zip)
$global:R0039Preset = $presetSource
$global:R0039Fixture = $fixture
function global:R0039-InFixture([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($global:R0039Fixture + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw ('Effect escaped fixture: ' + $full) }
}
function Snapshot { @([IO.Directory]::EnumerateFileSystemEntries($fixture, '*', [IO.SearchOption]::AllDirectories) | Sort-Object | ForEach-Object { $_.Substring($fixture.Length) }) }
$before = Snapshot
$global:R0039Events = New-Object System.Collections.Generic.List[string]
function Invoke-RestMethod { param($Uri, $Headers)
    $global:R0039Events.Add('metadata:' + $Uri)
    [pscustomobject]@{ id = 1; tag_name = 'v-fixture'; assets = @(
        [pscustomobject]@{ id = 11; name = 'tabliss-chromium.zip'; browser_download_url = 'https://example.invalid/tabliss-chromium.zip' }) }
}
function Invoke-WebRequest { param($Uri, $OutFile, [switch]$UseBasicParsing)
    $global:R0039Events.Add('download:' + $Uri); R0039-InFixture $OutFile
    if ($Uri -eq 'https://example.invalid/preset') { [IO.File]::Copy($global:R0039Preset, $OutFile, $true) }
    elseif ($Uri -eq 'https://example.invalid/tabliss-chromium.zip') { [IO.File]::Copy($global:R0039Zip, $OutFile, $true) }
    else { throw 'Unexpected fixture URL' }
}
function Set-Clipboard { param($Value) $global:R0039Events.Add('clipboard') }
function Start-Process { param($FilePath, $ArgumentList) $global:R0039Events.Add('open:' + $FilePath + ' ' + $ArgumentList) }
$arguments = @{ PresetUrl = 'https://example.invalid/preset'; InstallSource = 'github'; WidgetHash = $env:SALAH_WIDGET_HASH }
$global:LASTEXITCODE = 0; $entryError = $null; $entryExit = $null
$global:R0039Transcript = New-Object System.Collections.Generic.List[string]
try { & $source @arguments *>&1 | ForEach-Object { $global:R0039Transcript.Add([string]$_) }; $entryExit = $LASTEXITCODE }
catch { $entryExit = 'terminating-error'; $entryError = $_.Exception.GetType().FullName + ': ' + $_.Exception.Message }
$after = Snapshot
$created = @($after | Where-Object { $before -notcontains $_ })
$events = @($global:R0039Events)
$handoff = [array]::IndexOf($events, @($events | Where-Object { $_ -eq 'clipboard' })[0])
$storeOpens = @($events | Where-Object { $_ -like 'open:*chromewebstore.google.com*' })
[pscustomobject]@{
    host = $PSVersionTable.PSVersion.ToString(); edition = $PSVersionTable.PSEdition
    sourceSha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    entryExit = $entryExit; entryError = $entryError; events = $events
    handoffReached = ($handoff -ge 0)
    storeOpenedAfterHandoff = [bool](@($events | Select-Object -Skip ([Math]::Max($handoff, 0)) | Where-Object { $_ -like 'open:*chromewebstore.google.com*' }).Count -and $handoff -ge 0)
    storeOpenCount = $storeOpens.Count
    fallbackWarning = [bool]@($global:R0039Transcript | Where-Object { $_ -like '*Falling back to official store page*' }).Count
    retainedBundleUnderFixtureHome = [bool]@($created | Where-Object { $_ -like '\home\*' }).Count
    createdEntryCount = $created.Count
    removedEntries = @($before | Where-Object { $after -notcontains $_ })
    lastOutput = @($global:R0039Transcript | Select-Object -Last 15)
} | ConvertTo-Json -Depth 5
