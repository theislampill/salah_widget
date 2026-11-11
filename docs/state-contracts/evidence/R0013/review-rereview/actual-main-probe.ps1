param([string]$SourceFile,[string]$Fixture)
$ErrorActionPreference='Stop'
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Fixture source parse failed'}
foreach($def in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)){. ([scriptblock]::Create($def.Extent.Text))}
function Event([string]$Text){[IO.File]::AppendAllText((Join-Path $Fixture 'effects.txt'),$Text+[Environment]::NewLine)}
function Get-BrowserConfigs {[pscustomobject]@{Key='firefox';Label='Firefox';Family='firefox';UserData=(Join-Path $Fixture 'profiles');Exes=@();StoreUrl='fixture://store';ManagerUrl='about:addons';NewTabUrl='about:newtab'}}
function Initialize-Staging {Event 'stage'}
function Get-LatestRelease {[pscustomobject]@{tag_name='v-fixture';assets=@([pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/asset'})}}
function Download-Asset($Asset){Event 'asset';return (Join-Path $Fixture 'asset.xpi')}
function Download-Preset {Event 'preset';return (Join-Path $Fixture 'preset.json')}
function Copy-Text([string]$Text){Event 'clipboard';return $true}
function Open-TargetUrl($Target,[string]$Url){Event ('open:'+$Url)}
function Read-Host([string]$Prompt){Event 'prompt';if($Prompt -like 'Select target*'){return 'all'};return ''}
$DryRun=$false;$NoOpen=$false;$InstallSource='github';$PresetUrl='https://example.invalid/preset';$WidgetHash='';$WorkRoot=Join-Path $Fixture 'stage'
$marker=[regex]::Match($text,'(?m)^Write-Host ""\r?\nWrite-Host "Salah Widget Installer" -ForegroundColor Cyan')
if(-not $marker.Success){throw 'Fixture main boundary missing'}
& ([scriptblock]::Create($text.Substring($marker.Index)))
