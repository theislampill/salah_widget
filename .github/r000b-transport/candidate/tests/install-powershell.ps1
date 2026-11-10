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
    @('chromium', @('tabliss-chromium-a.zip','tabliss-chrome-b.zip'), 'tabliss-chromium-a.zip'),
    @('firefox', @('generic.xpi','tabliss-firefox-unsigned.xpi','tabliss-firefox-signed.xpi'), 'tabliss-firefox-signed.xpi'),
    @('firefox', @('generic.xpi'), 'generic.xpi'),
    @('firefox', @('tabliss-firefox.zip'), 'tabliss-firefox.zip')
)) {
    $family=$row[0]; $names=$row[1]; $expected=$row[2]
    Check ('selector '+$family+' '+$expected) {
        $script:fixtureRelease=Release $names
        $actual=@(Select-TablissNgAsset $family)
        Assert ($actual.Count -eq 1 -and $actual[0].name -ceq $expected -and $actual[0].browser_download_url -ceq ('https://example.invalid/'+$expected)) 'Wrong selected object or selector threw'
        $expectedObject=@($script:fixtureRelease.assets | Where-Object {$_.name -ceq $expected})[0]
        Assert ([object]::ReferenceEquals($actual[0],$expectedObject)) 'Selected object identity changed'
    }
}
foreach ($row in @(
    @('chromium',@(),"Latest release 'v-fixture' has no assets."),
    @('chromium',@('tabliss-chromium-source.zip','tabliss-safari.zip','tabliss-firefox.zip'),"No safe chromium asset found in latest release 'v-fixture'."),
    @('firefox',@('source.xpi','tabliss-firefox-unsigned.xpi'),"No safe firefox asset found in latest release 'v-fixture'."),
    @('safari',@('tabliss-chromium.zip'),'Unsupported browser family for GitHub release install: safari')
)) {
    $family=$row[0]; $names=$row[1]; $expectedReason=$row[2]
    Check ('selector rejects '+$family+' '+($names -join ',')) {
        $script:fixtureRelease=Release $names; $reason=$null
        try { $null=Select-TablissNgAsset $family } catch { $reason=$_.Exception.Message }
        Assert ($reason -ceq $expectedReason) ('Wrong rejection reason: '+$reason)
    }
}

# Real Install-TablissNG consumer, external boundaries replaced with exact argument spies.
$script:events=@()
$InstallSource='github'; $NoOpen=$false
$fixturePath=Join-Path ([IO.Path]::GetTempPath()) ('fixture path '+[char]0x0645+' asset.zip')
function Download-Asset($Asset) { $script:downloadedAssets += ,$Asset; $script:events += ('download:'+$Asset.name); return $fixturePath }
function Expand-ChromiumAsset([string]$ZipPath) { Assert ($ZipPath -ceq $fixturePath) 'Path altered'; $script:events += 'extract'; return ($fixturePath+' unpacked') }
function Copy-Text([string]$Text) { $script:events += ('copy:'+$Text); return $true }
function Open-TargetUrl($Target,[string]$Url) { $script:events += ('open:'+$Url) }
function Read-Host([string]$Prompt) { $script:events += ('prompt:'+$Prompt); return '' }
function Write-Warn([string]$Text) { $script:events += ('warning:'+$Text) }
foreach ($family in 'chromium','firefox') {
    Check ('actual install caller '+$family) {
        $script:events=@(); $script:downloadedAssets=@(); $script:fixtureRelease=Release @('tabliss-chromium.zip','tabliss-firefox-signed.xpi')
        $target=[pscustomobject]@{Browser='Fixture';Family=$family;Config=[pscustomobject]@{StoreUrl='https://store.invalid'; ManagerUrl='fixture://manager'}}
        $null=Install-TablissNG $target
        $expected=if($family -eq 'chromium'){'tabliss-chromium.zip'}else{'tabliss-firefox-signed.xpi'}
        $expectedObject=@($script:fixtureRelease.assets | Where-Object {$_.name -ceq $expected})[0]
        Assert ($script:downloadedAssets.Count -eq 1 -and [object]::ReferenceEquals($script:downloadedAssets[0],$expectedObject)) 'Wrong object or duplicate download'
        Assert ($script:downloadedAssets[0].browser_download_url -ceq ('https://example.invalid/'+$expected)) 'Download URL altered'
        Assert (-not ($script:events -contains 'open:https://store.invalid')) 'Selector failure hidden by store fallback'
        if($family -eq 'chromium'){ Assert ($script:events -contains 'extract') 'Actual extraction caller not reached' }
        $expectedCopy=if($family -eq 'chromium'){$fixturePath+' unpacked'}else{$fixturePath}
        Assert (@($script:events | Where-Object {$_ -like 'copy:*'}).Count -eq 1 -and $script:events -contains ('copy:'+$expectedCopy)) 'Copied path differs or count wrong'
        Assert (@($script:events | Where-Object {$_ -like 'open:*'}).Count -eq 1 -and $script:events -contains 'open:fixture://manager') 'Wrong manager URL or count'
        Assert (@($script:events | Where-Object {$_ -like 'prompt:*'}).Count -eq 1 -and $script:events -contains 'prompt:Press Enter after TablissNG is installed') 'Wrong prompt or count'
    }
}
foreach($row in @(
    @('empty', (Release @()), "Latest release 'v-fixture' has no assets."),
    @('unsuitable', (Release @('tabliss-chromium-source.zip','tabliss-safari.zip','tabliss-firefox.zip')), "No safe chromium asset found in latest release 'v-fixture'."),
    @('metadata', (New-Object Exception 'Fixture auth/rate-limit failure'), 'Fixture auth/rate-limit failure')
)) {
    $caseName=$row[0]; $releaseInput=$row[1]; $expectedReason=$row[2]
    Check ('actual caller fallback '+$caseName) {
        $script:fixtureRelease=$releaseInput; $script:events=@(); $script:downloadedAssets=@()
        $target=[pscustomobject]@{Browser='Fixture';Family='chromium';Config=[pscustomobject]@{StoreUrl='https://store.invalid';ManagerUrl='fixture://manager'}}
        $null=Install-TablissNG $target
        Assert ($script:downloadedAssets.Count -eq 0 -and -not ($script:events -contains 'extract') -and -not ($script:events -match '^copy:')) 'Fallback performed asset effects'
        Assert (($script:events -join '|') -ceq ('warning:'+$expectedReason+'|warning:Falling back to official store page.|open:https://store.invalid|prompt:Press Enter after TablissNG is installed')) ('Wrong fallback events: '+($script:events -join '|'))
    }
}

[pscustomobject]@{host=$PSVersionTable.PSVersion.ToString(); source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant(); fileErrors=@($fileErrors).Count; results=$script:results} | ConvertTo-Json -Depth 8
if (@($script:results | Where-Object {-not $_.pass}).Count) { exit 1 }
