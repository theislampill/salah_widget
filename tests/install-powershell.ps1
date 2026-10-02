param([string]$SourceFile = (Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'))
$ErrorActionPreference = 'Stop'
$script:results = @()
function Check([string]$Name, [scriptblock]$Body) {
    try { & $Body; $script:results += [pscustomobject]@{ case=$Name; pass=$true } }
    catch { $script:results += [pscustomobject]@{ case=$Name; pass=$false; error=$_.Exception.Message } }
}
function Assert($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
$tokens=$null; $fileErrors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$fileErrors)
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null; $textErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$textErrors)
if (@($textErrors).Count) { throw 'Fixture cannot identify functions: source syntax drift' }
foreach ($def in $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true)) {
    . ([scriptblock]::Create($def.Extent.Text))
}
Check 'explicit UTF8 parser control' { Assert (@($textErrors).Count -eq 0) 'ParseInput failed' }
Check 'exact-file native parser' { Assert (@($fileErrors).Count -eq 0) ('ParseFile errors: ' + (@($fileErrors | ForEach-Object {$_.Message}) -join '; ')) }
Check 'ASCII static source' { Assert (-not @([IO.File]::ReadAllBytes($SourceFile) | Where-Object {$_ -gt 127}).Count) 'Non-ASCII source byte' }
$DryRun=$false
$script:fixtureRelease=$null
function Get-LatestRelease { if ($script:fixtureRelease -is [Exception]) { throw $script:fixtureRelease }; return $script:fixtureRelease }
function Release([string[]]$Names) {
    [pscustomobject]@{tag_name='v-fixture'; assets=@($Names | ForEach-Object { [pscustomobject]@{ name=$_; browser_download_url=('https://example.invalid/' + $_) } })}
}
foreach ($row in @(
    @('chromium', @('tabliss.zip','tabliss-firefox.zip','source.zip','tabliss-chromium.zip'), 'tabliss-chromium.zip'),
    @('chromium', @('tabliss-chrome-b.zip','tabliss-chromium-a.zip'), 'tabliss-chrome-b.zip'),
    @('firefox', @('generic.xpi','tabliss-firefox-unsigned.xpi','tabliss-firefox-signed.xpi'), 'tabliss-firefox-signed.xpi'),
    @('firefox', @('generic.xpi'), 'generic.xpi'),
    @('firefox', @('tabliss-firefox.zip'), 'tabliss-firefox.zip')
)) {
    $family=$row[0]; $names=$row[1]; $expected=$row[2]
    Check ('selector '+$family+' '+$expected) {
        $script:fixtureRelease=Release $names
        $actual=@(Select-TablissNgAsset $family)
        Assert ($actual.Count -eq 1 -and $actual[0].name -ceq $expected -and $actual[0].browser_download_url -ceq ('https://example.invalid/'+$expected)) 'Wrong selected object or selector threw'
    }
}
foreach ($row in @(@('chromium',@()),@('firefox',@('source.xpi','tabliss-firefox-unsigned.xpi')), @('safari',@('tabliss-chromium.zip')))) {
    $family=$row[0]; $names=$row[1]
    Check ('selector rejects '+$family+' '+($names -join ',')) {
        $script:fixtureRelease=Release $names; $threw=$false
        try { $null=Select-TablissNgAsset $family } catch { $threw=$true }
        Assert $threw 'Unsuitable release was admitted'
    }
}

# Real Install-TablissNG consumer, external boundaries replaced with exact argument spies.
$script:events=@()
$InstallSource='github'; $NoOpen=$false
$fixturePath=Join-Path ([IO.Path]::GetTempPath()) ('fixture path '+[char]0x0645+' asset.zip')
function Download-Asset($Asset) { $script:events += ('download:'+$Asset.name); return $fixturePath }
function Expand-ChromiumAsset([string]$ZipPath) { Assert ($ZipPath -ceq $fixturePath) 'Path altered'; $script:events += 'extract'; return ($fixturePath+' unpacked') }
function Copy-Text([string]$Text) { $script:events += ('copy:'+$Text); return $true }
function Open-TargetUrl($Target,[string]$Url) { $script:events += ('open:'+$Url) }
function Read-Host([string]$Prompt) { $script:events += ('prompt:'+$Prompt); return '' }
foreach ($family in 'chromium','firefox') {
    Check ('actual install caller '+$family) {
        $script:events=@(); $script:fixtureRelease=Release @('tabliss-chromium.zip','tabliss-firefox-signed.xpi')
        $target=[pscustomobject]@{Browser='Fixture';Family=$family;Config=[pscustomobject]@{StoreUrl='https://store.invalid'; ManagerUrl='fixture://manager'}}
        $null=Install-TablissNG $target
        $expected=if($family -eq 'chromium'){'tabliss-chromium.zip'}else{'tabliss-firefox-signed.xpi'}
        Assert ($script:events -contains ('download:'+$expected)) 'Valid asset failed to reach download caller'
        Assert (-not ($script:events -contains 'open:https://store.invalid')) 'Selector failure hidden by store fallback'
        if($family -eq 'chromium'){ Assert ($script:events -contains 'extract') 'Actual extraction caller not reached' }
        Assert (@($script:events | Where-Object {$_ -like 'copy:*'}).Count -eq 1) 'Manual consumer not reached exactly once'
    }
}

[pscustomobject]@{host=$PSVersionTable.PSVersion.ToString(); source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant(); fileErrors=@($fileErrors).Count; results=$script:results} | ConvertTo-Json -Depth 8
if (@($script:results | Where-Object {-not $_.pass}).Count) { exit 1 }
