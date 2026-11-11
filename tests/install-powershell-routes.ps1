param([string]$SourceFile = (Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'),[switch]$RoutesOnly)
$ErrorActionPreference = 'Stop'
$script:results = @()
$sourceBefore=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
function Check([string]$Name, [scriptblock]$Body) {
    if($RoutesOnly -and $Name -notlike 'route *'){return}
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
# Selector/caller fixture boundary only: these fake paths are deliberately not
# filesystem admission evidence. The R0015 transaction suite exercises the real
# guard, bytes and native custody. Preserve the actual caller's guard arguments.
function Get-AdmittedArtifact([string]$Path,[string]$Kind) {
    $expected=if($Kind -eq 'asset'){$fixturePath}elseif($Kind -eq 'unpacked'){$fixturePath+' unpacked'}else{throw 'Unexpected admission kind in selector fixture'}
    Assert ($Path -ceq $expected) 'Caller changed the selected artifact path before admission'
    $script:admissionCalls+=,[pscustomobject]@{path=$Path;kind=$Kind}
    return [pscustomobject]@{State='published'}
}
function Copy-Text([string]$Text) { $script:events += ('copy:'+$Text); return $true }
function Open-TargetUrl($Target,[string]$Url) { $script:events += ('open:'+$Url) }
function Read-Host([string]$Prompt) { $script:events += ('prompt:'+$Prompt); return '' }
function Write-Warn([string]$Text) { $script:events += ('warning:'+$Text) }
foreach ($family in 'chromium','firefox') {
    Check ('actual install caller '+$family) {
        $script:events=@(); $script:downloadedAssets=@(); $script:admissionCalls=@(); $script:fixtureRelease=Release @('tabliss-chromium.zip','tabliss-firefox-signed.xpi')
        $target=[pscustomobject]@{Browser='Fixture';Family=$family;Config=[pscustomobject]@{StoreUrl='https://store.invalid'; ManagerUrl='fixture://manager'}}
        $null=Install-TablissNG $target
        $expected=if($family -eq 'chromium'){'tabliss-chromium.zip'}else{'tabliss-firefox-signed.xpi'}
        $expectedObject=@($script:fixtureRelease.assets | Where-Object {$_.name -ceq $expected})[0]
        Assert ($script:downloadedAssets.Count -eq 1 -and [object]::ReferenceEquals($script:downloadedAssets[0],$expectedObject)) 'Wrong object or duplicate download'
        Assert ($script:downloadedAssets[0].browser_download_url -ceq ('https://example.invalid/'+$expected)) 'Download URL altered'
        Assert (-not ($script:events -contains 'open:https://store.invalid')) 'Selector failure hidden by store fallback'
        if($family -eq 'chromium'){ Assert ($script:events -contains 'extract') 'Actual extraction caller not reached' }
        Assert (@($script:admissionCalls|Where-Object {$_.kind -eq 'asset'}).Count -eq 1) 'Actual caller bypassed asset admission'
        Assert (@($script:admissionCalls|Where-Object {$_.kind -eq 'unpacked'}).Count -eq $(if($family -eq 'chromium'){1}else{0})) 'Actual caller changed unpacked admission boundary'
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
        $script:fixtureRelease=$releaseInput; $script:events=@(); $script:downloadedAssets=@(); $script:admissionCalls=@()
        $target=[pscustomobject]@{Browser='Fixture';Family='chromium';Config=[pscustomobject]@{StoreUrl='https://store.invalid';ManagerUrl='fixture://manager'}}
        $null=Install-TablissNG $target
        Assert ($script:downloadedAssets.Count -eq 0 -and -not ($script:events -contains 'extract') -and -not ($script:events -match '^copy:')) 'Fallback performed asset effects'
        Assert ($script:admissionCalls.Count -eq 0) 'Selector failure reached artifact admission'
        Assert (($script:events -join '|') -ceq ('warning:'+$expectedReason+'|warning:Falling back to official store page.|open:https://store.invalid|prompt:Press Enter after TablissNG is installed')) ('Wrong fallback events: '+($script:events -join '|'))
    }
}

# Additional actual-caller routes. Only network, prompt, browser, clipboard and
# artifact-boundary adapters are replaced; no installer implementation is copied.
# These rows do not claim native archive admission or whole-entry eligibility.
$script:routeObservations=@()
function Get-LatestRelease { $script:routeReleaseCalls++; return $script:fixtureRelease }
function Read-Host([string]$Prompt) {
    $script:events += ('prompt:'+$Prompt)
    Assert ($script:routeAnswers.Count -gt 0) ('Unexpected route prompt: '+$Prompt)
    $answer=$script:routeAnswers.Dequeue()
    return $answer
}
function Get-AdmittedArtifact([string]$Path,[string]$Kind) {
    $expected=if($Kind -eq 'asset'){$fixturePath}elseif($Kind -eq 'unpacked'){$fixturePath+' unpacked'}else{throw 'Unexpected route admission kind'}
    Assert ($Path -ceq $expected) 'Actual caller changed the selected artifact path before admission'
    $record=[pscustomobject]@{Path=$Path;Kind=$Kind;State='published'}
    $script:admissionCalls+=,$record
    return $record
}
foreach($family in 'chromium','firefox') {
    foreach($route in @(
        @('explicit-store','store',$null,'store'),
        @('ask-store','ask','2','store'),
        @('ask-github','ask','1','github'),
        @('ask-default-github','ask','','github')
    )) {
        $routeName=[string]$route[0];$requestedSource=[string]$route[1];$choice=$route[2];$resolved=[string]$route[3]
        $caseName='route '+$family+' '+$routeName
        Check $caseName {
            $script:InstallSource=$requestedSource
            $script:events=@();$script:downloadedAssets=@();$script:admissionCalls=@();$script:routeReleaseCalls=0
            $script:fixtureRelease=Release @('tabliss-chromium.zip','tabliss-firefox-signed.xpi')
            $script:routeAnswers=New-Object 'System.Collections.Generic.Queue[string]'
            if($requestedSource -eq 'ask'){$script:routeAnswers.Enqueue([string]$choice)}
            $script:routeAnswers.Enqueue('')
            $target=[pscustomobject]@{Browser='Fixture';Family=$family;DiscoveryStatus='known-neither';HasLegacyTabliss=$false;HasTablissNG=$false;Config=[pscustomobject]@{StoreUrl='https://store.invalid';ManagerUrl='fixture://manager'}}
            try {
                Assert ((Get-DiscoveryEligibility $target) -ceq 'eligible-known') 'Production eligibility no longer admits the positive route premise'
                $null=Install-TablissNG $target
                Assert ($script:InstallSource -ceq $requestedSource) 'Actual caller mutated the requested source variable'
                Assert ($script:routeAnswers.Count -eq 0) 'Actual route skipped a required confirmation'
                $prompts=@($script:events|Where-Object{$_ -like 'prompt:*'})
                $expectedPrompts=@()
                if($requestedSource -eq 'ask'){$expectedPrompts+='prompt:Choose [1/2] (default 1)'}
                $expectedPrompts+='prompt:Press Enter after TablissNG is installed'
                Assert (($prompts -join '|') -ceq ($expectedPrompts -join '|')) 'Wrong source-choice/manual-confirmation prompt sequence'
                $opens=@($script:events|Where-Object{$_ -like 'open:*'})
                if($resolved -eq 'store') {
                    Assert ($script:routeReleaseCalls -eq 0 -and $script:downloadedAssets.Count -eq 0 -and $script:admissionCalls.Count -eq 0) 'Store route reached GitHub or artifact admission'
                    Assert (-not @($script:events|Where-Object{$_ -like 'copy:*' -or $_ -eq 'extract' -or $_ -like 'warning:*'}).Count) 'Store route performed artifact/copy/fallback actions'
                    Assert ($opens.Count -eq 1 -and $opens[0] -ceq 'open:https://store.invalid') 'Store route opened the wrong target or wrong count'
                } else {
                    $assetName=if($family -eq 'chromium'){'tabliss-chromium.zip'}else{'tabliss-firefox-signed.xpi'}
                    $expectedAsset=@($script:fixtureRelease.assets|Where-Object{$_.name -ceq $assetName})[0]
                    Assert ($script:routeReleaseCalls -eq 1 -and $script:downloadedAssets.Count -eq 1) 'GitHub route performed the wrong release lookup/download count'
                    Assert ([object]::ReferenceEquals($script:downloadedAssets[0],$expectedAsset)) 'Actual R14 selector object identity changed'
                    Assert ($script:downloadedAssets[0].browser_download_url -ceq ('https://example.invalid/'+$assetName)) 'Selected URL changed at caller boundary'
                    $expectedKinds=if($family -eq 'chromium'){'asset|unpacked'}else{'asset'}
                    Assert (($script:admissionCalls.Kind -join '|') -ceq $expectedKinds) 'Actual caller skipped/reordered artifact admission'
                    $copyPath=if($family -eq 'chromium'){$fixturePath+' unpacked'}else{$fixturePath}
                    $copies=@($script:events|Where-Object{$_ -like 'copy:*'})
                    Assert ($copies.Count -eq 1 -and $copies[0] -ceq ('copy:'+$copyPath)) 'GitHub route did not hand off the exact selected path'
                    Assert ($script:admissionCalls[-1].State -ceq 'handed-off') 'Actual caller did not mark the returned handoff record'
                    Assert (@($script:events|Where-Object{$_ -eq 'extract'}).Count -eq $(if($family -eq 'chromium'){1}else{0})) 'Wrong family extraction route'
                    Assert ($opens.Count -eq 1 -and $opens[0] -ceq 'open:fixture://manager') 'GitHub route opened a store fallback or wrong manager'
                    Assert (-not @($script:events|Where-Object{$_ -like '*Falling back*'}).Count) 'Positive GitHub route hid a failure behind store fallback'
                }
            } finally {
                $script:routeObservations+=,[pscustomobject]@{case=$caseName;family=$family;requestedSource=$requestedSource;choice=$choice;expectedRoute=$resolved;events=$script:events;releaseCalls=$script:routeReleaseCalls;downloadedAssets=$script:downloadedAssets;admissionCalls=$script:admissionCalls;remainingAnswers=$script:routeAnswers.Count;eligibility=(Get-DiscoveryEligibility $target)}
            }
        }
    }
}

$sourceAfter=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
if($sourceAfter -cne $sourceBefore){$script:results+=,[pscustomobject]@{case='source custody';pass=$false;error='Source bytes changed'}}
if($script:results.Count -eq 0){$script:results+=,[pscustomobject]@{case='selected coverage';pass=$false;error='No test rows executed'}}
[pscustomobject]@{
    schema='r0016-install-route-caller.v1';host=$PSVersionTable.PSVersion.ToString()
    source=$sourceAfter;sourceBefore=$sourceBefore;sourceUnchanged=($sourceAfter -ceq $sourceBefore)
    testSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    nativeWindows=([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT)
    fileErrors=@($fileErrors).Count;routesOnly=[bool]$RoutesOnly;results=$script:results;routeObservations=$script:routeObservations
    adapters=@('controlled release object','download/expansion path spy','artifact admission record spy','prompt answer queue','browser/clipboard spies')
    scope='Actual Install-TablissNG, Select-TablissNgAsset and positive Get-DiscoveryEligibility functions from exact source. Route semantics only; native admission and whole-entry unknown refusal are separate.'
} | ConvertTo-Json -Depth 10
if (@($script:results | Where-Object {-not $_.pass}).Count) { exit 1 }
