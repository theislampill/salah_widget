param([string]$SourceFile=(Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'))
$ErrorActionPreference='Stop'
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Fixture source syntax drift'}
foreach($def in $ast.FindAll({param($n)$n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true)){ . ([scriptblock]::Create($def.Extent.Text)) }
$DryRun=$true; $NoOpen=$false; $InstallSource='ask'; $TablissNgRepo='fixture/repo'; $PresetUrl='https://example.invalid/preset'; $WidgetHash='lat=24.47&lon=39.61&method=4'
$root=Join-Path ([IO.Path]::GetTempPath()) ('salah-helper-guards-'+[guid]::NewGuid().ToString('N'))
$WorkRoot=$root; $DownloadRoot=Join-Path $root 'downloads'; $PresetRoot=Join-Path $root 'presets'
$cache=Join-Path $DownloadRoot 'v-fixture'; [void][IO.Directory]::CreateDirectory($cache); [void][IO.Directory]::CreateDirectory($PresetRoot)
$cachedPath=Join-Path $cache 'asset.zip'; [IO.File]::WriteAllText($cachedPath,'keep cached asset')
$presetPath=Join-Path $PresetRoot 'salah-widget.tablissng.json'; [IO.File]::WriteAllText($presetPath,'keep cached preset')
$script:LatestRelease=[pscustomobject]@{tag_name='v-fixture';assets=@([pscustomobject]@{name='asset.zip';browser_download_url='https://example.invalid/asset'})}
$target=[pscustomobject]@{Browser='Fixture';Family='chromium';Config=[pscustomobject]@{StoreUrl='https://store.invalid';ManagerUrl='fixture://manager';NewTabUrl='fixture://newtab'}}
$script:effects=@()
function New-Item {param($ItemType,$Path,[switch]$Force) $script:effects+='mkdir'}
function Remove-Item {param($LiteralPath,[switch]$Recurse,[switch]$Force) $script:effects+='remove'}
function Expand-Archive {param($LiteralPath,$DestinationPath,[switch]$Force) $script:effects+='extract'}
function Invoke-RestMethod {param($Uri,$Headers) $script:effects+='metadata';throw 'Denied fixture network'}
function Invoke-WebRequest {param($Uri,$OutFile,[switch]$UseBasicParsing) $script:effects+='download';throw 'Denied fixture network'}
function Set-Clipboard {param($Value) $script:effects+='clipboard'}
function Start-Process {param($FilePath,$ArgumentList) $script:effects+='open'}
function Read-Host {param($Prompt) $script:effects+='prompt';return ''}
$cases=@(
    @('initialize',{Initialize-Staging}),
    @('metadata cached',{Get-LatestRelease}),
    @('selector',{Select-TablissNgAsset 'chromium'}),
    @('download cached',{Download-Asset $script:LatestRelease.assets[0]}),
    @('extract cached',{Expand-ChromiumAsset $cachedPath}),
    @('preset cached',{Download-Preset}),
    @('clipboard',{Copy-Text 'fixture'}),
    @('open',{Open-TargetUrl $target 'https://example.invalid'}),
    @('install ask/store fallback',{Install-TablissNG $target}),
    @('import cached',{Show-ImportInstructions $target $presetPath})
)
$results=@()
foreach($row in $cases){
    $script:effects=@(); $value=$null; $reason=$null
    try { $value=& $row[1] } catch { $reason=$_.Exception.Message }
    $pass=$script:effects.Count -eq 0 -and ($null -eq $value -or $value -ceq $false)
    $results+=[pscustomobject]@{case=$row[0];pass=$pass;value=$value;reason=$reason;effects=$script:effects}
}
$sentinelUnchanged=[IO.File]::ReadAllText($cachedPath) -ceq 'keep cached asset' -and [IO.File]::ReadAllText($presetPath) -ceq 'keep cached preset'
[pscustomobject]@{host=$PSVersionTable.PSVersion.ToString();source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();fixture=$root;sentinelUnchanged=$sentinelUnchanged;results=$results} | ConvertTo-Json -Depth 8
if(-not $sentinelUnchanged -or @($results | Where-Object {-not $_.pass}).Count){exit 1}
