# R0039 (issue 106) discriminator B2: PowerShell non-interactive acknowledgement.
# Runs the EXACT install.ps1 entry in normal mode (not preview) inside a disposable fixture, in the style of
# tests/install-entry.ps1: fixture TEMP/TMP/LOCALAPPDATA/APPDATA/ProgramFiles, one eligible Chrome and one
# eligible Firefox fixture profile, and argument spies for every external boundary (Invoke-RestMethod,
# Invoke-WebRequest, Set-Clipboard, Start-Process). Read-Host is NOT replaced: the point is the host's
# real prompt behaviour. The caller chooses how the host is started (-NonInteractive, redirected input).
# Inputs (environment): R0039_B2_SOURCE (install.ps1), R0039_B2_FIXTURE (new empty directory).
$ErrorActionPreference = 'Stop'
$source = $env:R0039_B2_SOURCE; $fixture = [IO.Path]::GetFullPath($env:R0039_B2_FIXTURE)
if (@([IO.Directory]::EnumerateFileSystemEntries($fixture)).Count) { throw 'Fixture must be empty' }
foreach ($part in 'temp','local','roam','pf','pf86') { [void][IO.Directory]::CreateDirectory((Join-Path $fixture $part)) }
$env:TEMP = Join-Path $fixture 'temp'; $env:TMP = $env:TEMP
$env:LOCALAPPDATA = Join-Path $fixture 'local'; $env:APPDATA = Join-Path $fixture 'roam'
$env:ProgramFiles = Join-Path $fixture 'pf'; ${env:ProgramFiles(x86)} = Join-Path $fixture 'pf86'
$env:SALAH_INSTALL_SOURCE = 'github'; $env:SALAH_WIDGET_HASH = 'lat=24.47&lon=39.61&method=4'
[void][IO.Directory]::CreateDirectory((Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Default'))
$firefox = Join-Path $env:APPDATA 'Mozilla\Firefox\Profiles\fixture profile'
[void][IO.Directory]::CreateDirectory($firefox)
[IO.File]::WriteAllText((Join-Path $firefox 'extensions.json'), '{"addons":[]}')
function Snapshot { @([IO.Directory]::EnumerateFileSystemEntries($fixture, '*', [IO.SearchOption]::AllDirectories) | Sort-Object | ForEach-Object { $_.Substring($fixture.Length) }) }
$before = Snapshot
$global:R0039Events = @()
function Invoke-RestMethod { param($Uri, $Headers) $global:R0039Events += ('metadata:' + $Uri); throw 'Denied fixture network' }
function Invoke-WebRequest { param($Uri, $OutFile, [switch]$UseBasicParsing) $global:R0039Events += ('download:' + $Uri); throw 'Denied fixture network' }
function Set-Clipboard { param($Value) $global:R0039Events += ('clipboard:' + $Value) }
function Start-Process { param($FilePath, $ArgumentList) $global:R0039Events += ('open:' + $FilePath + ' ' + $ArgumentList) }
$arguments = @{ PresetUrl = 'https://example.invalid/preset'; InstallSource = 'github'; WidgetHash = $env:SALAH_WIDGET_HASH }
$global:LASTEXITCODE = 0; $entryError = $null; $entryExit = $null
$transcript = @()
try { $transcript = @(& $source @arguments *>&1 | ForEach-Object { [string]$_ }); $entryExit = $LASTEXITCODE }
catch { $entryExit = 'terminating-error'; $entryError = $_.Exception.GetType().FullName + ': ' + $_.Exception.Message }
$after = Snapshot
[pscustomobject]@{
    host = $PSVersionTable.PSVersion.ToString(); edition = $PSVersionTable.PSEdition
    sourceSha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    entryExit = $entryExit; entryError = $entryError; events = $global:R0039Events
    createdEntries = @($after | Where-Object { $before -notcontains $_ })
    removedEntries = @($before | Where-Object { $after -notcontains $_ })
    lastOutput = @($transcript | Select-Object -Last 12)
} | ConvertTo-Json -Depth 5
