param([string]$SourceFile = (Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'))
$ErrorActionPreference='Stop'
$script:results=@()
$script:diagnostics=@()
$script:SelectedCases=if($env:SALAH_DISCOVERY_CASES){@(ConvertFrom-Json -InputObject $env:SALAH_DISCOVERY_CASES)}else{$null}
$SourceFile=[IO.Path]::GetFullPath($SourceFile)
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$parseErrors)
if(@($parseErrors).Count){throw 'Exact-file parser failed before discovery fixture'}
foreach($def in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)){
    . ([scriptblock]::Create($def.Extent.Text))
}
function Write-Warn([string]$Text){$script:diagnostics+=,$Text}
function Assert($Condition,[string]$Message){if(-not $Condition){throw $Message}}
function Check([string]$Name,[scriptblock]$Body){
    if($null -ne $script:SelectedCases -and $Name -notin $script:SelectedCases){return}
    try{$observed=& $Body;$script:results+=,[pscustomobject]@{case=$Name;pass=$true;observation=$observed}}
    catch{$script:results+=,[pscustomobject]@{case=$Name;pass=$false;error=$_.Exception.Message}}
}
$FixtureRoot=Join-Path ([IO.Path]::GetTempPath()) ('salah-discovery-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $FixtureRoot
$utf8=New-Object Text.UTF8Encoding $false
function Profile([string]$Name,$Data){
    $path=Join-Path $FixtureRoot $Name;$null=New-Item -ItemType Directory -Path $path
    if($Data -eq 'directory'){$null=New-Item -ItemType Directory -Path (Join-Path $path 'extensions.json')}
    elseif($Data -is [byte[]]){[IO.File]::WriteAllBytes((Join-Path $path 'extensions.json'),$Data)}
    elseif($null -ne $Data){[IO.File]::WriteAllText((Join-Path $path 'extensions.json'),[string]$Data,$utf8)}
    return $path
}
function Parser-Case([string]$Name,$Data,[string]$Status,[string]$Reason,[bool]$New,[bool]$Old){
    $p=Profile ('parser-'+$Name) $Data
    $value=@(Get-FirefoxExtensionStatus $p)
    Assert ($value.Count -eq 1) 'Diagnostic or extra value contaminated discovery object stream'
    $r=$value[0]
    Assert ($r.Status -ceq $Status -and $r.Reason -ceq $Reason) ('False knowledge: '+($r|ConvertTo-Json -Compress -Depth 8))
    Assert ($r.HasNew -eq $New -and $r.HasOld -eq $Old) 'Retained positive flags differ'
    Assert ($r.MetadataSource -ceq (Join-Path $p 'extensions.json') -and $r.EvidenceClass -ceq 'firefox-extensions-json') 'Metadata identity or class lost'
    return [pscustomobject]@{status=$r.Status;reason=$r.Reason;source=$r.MetadataSource}
}
$empty='{"addons":[]}'
$old='{"addons":[{"name":"Tabliss"}]}'
$new='{"addons":[{"name":"TablissNG"}]}'
$both='{"addons":[{"name":"TablissNG"},{"name":"Tabliss"}]}'
Check 'retained actual parser positive control' {
    $p=Profile 'retained-positive' $both;$r=Get-FirefoxExtensionStatus $p
    Assert ($r.HasNew -and $r.HasOld -and $r.NewMatches.Count -eq 1 -and $r.OldMatches.Count -eq 1) 'Known positives broken'
}
Check 'literal bracketed Firefox profile name' {
    $p=Profile 'Profile [1]' $both
    Assert (-not [IO.Directory]::Exists((Join-Path $FixtureRoot 'Profile 1'))) 'Wildcard alias contaminated the literal-path control'
    $r=Get-FirefoxExtensionStatus $p
    Assert ($r.Status -ceq 'known-both' -and $r.Reason -ceq 'supported-metadata' -and $r.HasNew -and $r.HasOld) 'Bracketed literal profile was not read'
    Assert ($r.MetadataSource -ceq (Join-Path $p 'extensions.json')) 'Literal profile metadata identity changed'
}
foreach($row in @(
    @('empty',$empty,'known-neither','supported-metadata',$false,$false),
    @('object-leading-whitespace',("`r`n`t "+$empty),'known-neither','supported-metadata',$false,$false),
    @('malformed','{"addons":[','unknown','metadata-malformed',$false,$false),
    @('missing',$null,'unknown','metadata-absent',$false,$false),
    @('unreadable','directory','unknown','metadata-unreadable',$false,$false),
    @('invalid-encoding',[byte[]](255,123),'unknown','metadata-encoding',$false,$false),
    @('legacy',$old,'known-legacy','supported-metadata',$false,$true),
    @('new',$new,'known-new','supported-metadata',$true,$false),
    @('both',$both,'known-both','supported-metadata',$true,$true)
)){
    $r=$row
    Check ('actual parser '+$r[0]) {Parser-Case $r[0] $r[1] $r[2] $r[3] $r[4] $r[5]}
}
foreach($row in @(
    @('root-array','[]'),@('root-singleton-empty','[{"addons":[]}]'),@('root-singleton-new','[{"addons":[{"name":"TablissNG"}]}]'),
    @('root-null','null'),@('missing-addons','{}'),@('addons-object','{"addons":{}}'),
    @('addons-null','{"addons":null}'),@('addon-scalar','{"addons":[1]}'),@('locale-scalar','{"addons":[{"defaultLocale":2}]}'),
    @('name-object','{"addons":[{"name":{}}]}'),
    @('addons-key-case','{"ADDONS":[]}'),
    @('id-key-case','{"addons":[{"ID":"ordinary@example.invalid"}]}'),
    @('name-key-case','{"addons":[{"NAME":"TablissNG"}]}'),
    @('locale-key-case','{"addons":[{"defaultlocale":{"name":"TablissNG"}}]}'),
    @('locale-name-key-case','{"addons":[{"defaultLocale":{"NAME":"TablissNG"}}]}')
)){
    $r=$row
    Check ('unsupported shape '+$r[0]) {Parser-Case $r[0] $r[1] 'unknown' 'metadata-unsupported' $false $false}
}
Check 'metadata retains exact Unicode and delimiter match object' {
    $match='TablissNG|line'+[char]10+[char]0x0645
    $p=Profile 'unicode-match' (@{addons=@(@{name=$match})}|ConvertTo-Json -Compress)
    $r=Get-FirefoxExtensionStatus $p
    Assert ($r.Status -ceq 'known-new' -and $r.NewMatches.Count -eq 1 -and $r.NewMatches[0] -ceq $match) 'Object match/source corrupted'
}
foreach($row in @(
    @('empty-object','{"addons":[{}]}'),@('unrelated-keys','{"addons":[{"version":"1"}]}'),
    @('null-identities','{"addons":[{"id":null,"name":null,"defaultLocale":{"name":null}}]}'),
    @('empty-identities','{"addons":[{"id":"","name":"","defaultLocale":{"name":""}}]}'),
    @('whitespace-identities','{"addons":[{"id":"  ","name":"\t","defaultLocale":{"name":"\n"}}]}')
)){
    $r=$row
    Check ('insufficient identity '+$r[0]) {Parser-Case $r[0] $r[1] 'unknown' 'metadata-unsupported' $false $false}
}
foreach($row in @(
    @('id-only','{"addons":[{"id":"ordinary@example.invalid"}]}'),
    @('name-only','{"addons":[{"name":"Ordinary extension"}]}'),
    @('locale-name-only','{"addons":[{"defaultLocale":{"name":"Ordinary extension"}}]}')
)){
    $r=$row
    Check ('supported identity '+$r[0]) {Parser-Case $r[0] $r[1] 'known-neither' 'supported-metadata' $false $false}
}
Check 'partial metadata preserves conservative legacy hint' {Parser-Case 'partial-legacy' '{"addons":[{"name":"Tabliss"},{}]}' 'unknown' 'metadata-unsupported' $false $true}
foreach($row in @(
    @('trailing-comma','{"addons":[],}'),@('trailing-comment','{"addons":[]} /* comment */'),
    @('internal-comment','{/* comment */ "addons":[]}'),@('single-quotes',"{'addons':[]}"),@('bare-key','{addons:[]}'),
    @('duplicate-addons','{"addons":[{"name":"Tabliss"}],"addons":[]}'),
    @('duplicate-name','{"addons":[{"name":"Tabliss","name":"Ordinary extension"}]}'),
    @('escaped-duplicate-name','{"addons":[{"name":"Tabliss","na\u006de":"Ordinary extension"}]}'),
    @('duplicate-locale-name','{"addons":[{"defaultLocale":{"name":"Tabliss","name":"Ordinary extension"}}]}'),
    @('non-json-NaN','{"addons":[],"other":NaN}'),@('non-json-Infinity','{"addons":[],"other":Infinity}'),
    @('empty-document',''),@('array-trailing-comma','{"addons":[],"other":[1,]}'),
    @('leading-zero','{"addons":[],"n":01}'),@('leading-plus','{"addons":[],"n":+1}'),
    @('leading-dot','{"addons":[],"n":.1}'),@('trailing-dot','{"addons":[],"n":1.}'),@('missing-exponent','{"addons":[],"n":1e}'),
    @('missing-comma','{"addons":[],"other":{"a":1 "b":2}}'),@('multiple-roots','{"addons":[]}{}'),
    @('invalid-string-escape','{"addons":[],"s":"\x31"}'),@('short-unicode-escape','{"addons":[],"s":"\u12"}')
)){
    $r=$row
    Check ('strict JSON '+$r[0]) {Parser-Case $r[0] $r[1] 'unknown' 'metadata-malformed' $false $false}
}
Check 'strict JSON complex valid control' {Parser-Case 'complex-valid' '{"addons":[],"other":{"same":1,"array":[0,-1,1.5,1e+2,true,false,null,{},[]],"text":"quote\" slash\/ backslash\\ line\n unicode\u0645"},"another":{"same":2}}' 'known-neither' 'supported-metadata' $false $false}
Check 'actual strict validator valid paired control' {
    $values=@(Test-StrictJson '{"addons":[],"other":[{},[],true,false,null,1.25]}')
    Assert ($values.Count -eq 1 -and $values[0] -is [bool] -and $values[0]) 'Actual strict validator rejected valid paired input'
}
foreach($row in @(@('object-trailing-comma','{"addons":[],}'),@('array-trailing-comma','{"addons":[],"other":[1,]}'))){
    $r=$row
    Check ('actual strict validator '+$r[0]) {
        $values=@(Test-StrictJson $r[1])
        Assert ($values.Count -eq 1 -and $values[0] -is [bool] -and -not $values[0]) 'Actual strict validator admitted a trailing separator before downstream host conversion'
    }
}
Check 'actual target builder keeps states source and safe peers' {
    $script:Data=Join-Path $FixtureRoot 'builder';$null=New-Item -ItemType Directory -Path $script:Data
    $i=0
    foreach($body in @($empty,'{"addons":[',$old,$new,$both,'[]')){
        $p=Join-Path $script:Data ('profile-'+$i);$null=New-Item -ItemType Directory -Path $p
        [IO.File]::WriteAllText((Join-Path $p 'extensions.json'),$body,$utf8);$i++
    }
    function Get-BrowserConfigs { [pscustomobject]@{Key='firefox';Label='Firefox';Family='firefox';UserData=$script:Data;Exes=@();StoreUrl='fixture://store';ManagerUrl='about:addons';NewTabUrl='about:newtab'} }
    $targets=@(Get-Targets | Sort-Object ProfileName)
    Assert ($targets.Count -eq 6) 'Shape failure suppressed independent targets'
    Assert (($targets.DiscoveryStatus -join ',') -ceq 'known-neither,unknown,known-legacy,known-new,known-both,unknown') 'Builder dropped or fabricated status'
    foreach($t in $targets){Assert ($t.DiscoverySource -ceq (Join-Path $t.ProfilePath 'extensions.json') -and $t.DiscoveryEvidence -ceq 'firefox-extensions-json') 'Builder dropped source identity'}
}

# Child processes execute the actual main-body bytes with actual parser/builders.
# Staging/transport/clipboard/open boundaries are spies; profile reads are real.
$child=Join-Path $FixtureRoot 'main-consumer.ps1'
$childText=@'
param([string]$SourceFile,[string]$Fixture,[string]$Selection,[string]$Preview)
$ErrorActionPreference='Stop'
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Fixture source does not parse'}
foreach($def in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)){. ([scriptblock]::Create($def.Extent.Text))}
function Event([string]$Text){[IO.File]::AppendAllText((Join-Path $Fixture 'effects.txt'),$Text+[Environment]::NewLine)}
function Get-BrowserConfigs {[pscustomobject]@{Key='firefox';Label='Firefox';Family='firefox';UserData=(Join-Path $Fixture 'profiles');Exes=@();StoreUrl='fixture://store';ManagerUrl='about:addons';NewTabUrl='about:newtab'}}
function Initialize-Staging {Event 'stage'}
function Get-LatestRelease {[pscustomobject]@{tag_name='v-fixture';assets=@([pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/asset'})}}
function Download-Asset($Asset){Event 'asset';return (Join-Path $Fixture 'asset.xpi')}
function Download-Preset {Event 'preset';return (Join-Path $Fixture 'preset.json')}
function Copy-Text([string]$Text){Event 'clipboard';return $true}
function Open-TargetUrl($Target,[string]$Url){Event ('open:'+ $Url)}
function Read-Host([string]$Prompt){Event 'prompt';if($Prompt -like 'Select target*'){return $Selection};return ''}
$DryRun=$Preview -eq '1';$NoOpen=$false;$InstallSource='github';$PresetUrl='https://example.invalid/preset';$WidgetHash='';$WorkRoot=Join-Path $Fixture 'stage'
$marker=[regex]::Match($text,'(?m)^Write-Host ""\r?\nWrite-Host "Salah Widget Installer" -ForegroundColor Cyan')
if(-not $marker.Success){throw 'Fixture main boundary missing'}
& ([scriptblock]::Create($text.Substring($marker.Index)))
'@
[IO.File]::WriteAllText($child,$childText,[Text.Encoding]::ASCII)
$hostExe=Join-Path $PSHOME $(if($PSVersionTable.PSEdition -eq 'Desktop'){'powershell.exe'}elseif($env:OS -eq 'Windows_NT'){'pwsh.exe'}else{'pwsh'})
function Main-Case([string]$Name,[object[]]$Bodies,[string]$Selection,[bool]$Preview,[int]$Eligible,[int]$Held,[int]$Refused,[bool]$NoProfile=$false){
    $root=Join-Path $FixtureRoot ('entry-'+$Name);$null=New-Item -ItemType Directory -Path $root
    $profiles=Join-Path $root 'profiles';$null=New-Item -ItemType Directory -Path $profiles
    $i=0;foreach($body in $Bodies){
        $p=Join-Path $profiles ('profile-'+$i);$null=New-Item -ItemType Directory -Path $p
        if($null -ne $body){[IO.File]::WriteAllText((Join-Path $p 'extensions.json'),[string]$body,$utf8)};$i++
    }
    [IO.File]::WriteAllText((Join-Path $root 'asset.xpi'),'fixture bytes',$utf8)
    [IO.File]::WriteAllText((Join-Path $root 'preset.json'),'{}',$utf8)
    $before=@(Get-ChildItem -LiteralPath $profiles -File -Recurse | ForEach-Object {($_.FullName+':'+(Get-FileHash -LiteralPath $_.FullName).Hash)}) -join '|'
    $output=(& $hostExe -NoProfile -File $child -SourceFile $SourceFile -Fixture $root -Selection $Selection -Preview $(if($Preview){'1'}else{'0'}) 2>&1 | Out-String)
    $code=$LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $root 'output.txt'),$output,$utf8)
    $events=@();if(Test-Path -LiteralPath (Join-Path $root 'effects.txt')){$events=@(Get-Content -LiteralPath (Join-Path $root 'effects.txt'))}
    Assert (($code -eq 0) -eq ($Eligible -gt 0)) ('Wrong exit '+$code+': '+$output)
    $effectEvents=@($events|Where-Object {$_ -ne 'prompt'})
    if($Preview -or $Eligible -eq 0){Assert ($effectEvents.Count -eq 0) ('Held/preview target reached effects: '+($events -join ','))}
    else {Assert (@($events|Where-Object {$_ -ceq 'open:about:newtab'}).Count -eq $Eligible) 'Wrong target reached actual handoff';Assert ($events -contains 'stage') 'Known peer lost useful effects'}
    if($Preview){Assert ($events.Count -eq 0) 'Preview prompted'}
    $after=@(Get-ChildItem -LiteralPath $profiles -File -Recurse | ForEach-Object {($_.FullName+':'+(Get-FileHash -LiteralPath $_.FullName).Hash)}) -join '|'
    Assert ($before -ceq $after) 'Profile metadata changed'
    Assert ($output.Contains(([string]$Eligible+' eligible')) -and $output.Contains(([string]$Held+' held')) -and $output.Contains(([string]$Refused+' refused'))) ('Missing/false result counts: '+$output)
    Assert ($output -match '(?i)manual') 'Manual boundary lost'
    return [pscustomobject]@{exit=$code;effects=$effectEvents.Count;eligible=$Eligible;held=$Held;refused=$Refused;fixture=$root}
}
Check 'actual all mixed selection keeps known peer' {Main-Case 'mixed' @($empty,'{"addons":[',$old) 'all' $false 1 1 1}
Check 'actual explicit known target stays useful' {Main-Case 'explicit-known' @($empty,'{"addons":[',$old) '1' $false 1 0 0}
Check 'actual explicit unknown refuses before staging' {Main-Case 'explicit-unknown' @($empty,'{"addons":[',$old) '2' $false 0 1 0}
Check 'actual unknown only refuses before staging' {Main-Case 'unknown' @('{"addons":[') 'all' $false 0 1 0}
Check 'actual both refuses before staging' {Main-Case 'both' @($both) 'all' $false 0 0 1}
Check 'actual missing metadata held' {Main-Case 'missing' @($null) 'all' $false 0 1 0}
Check 'actual no-profile fallback held' {Main-Case 'no-profile' @() 'all' $false 0 1 0 $true}
Check 'actual wrong shape keeps known peer' {Main-Case 'shape-peer' @($empty,'[]') 'all' $false 1 1 0}
Check 'preview mixed has zero effects and truthful states' {Main-Case 'preview-mixed' @($empty,'{"addons":[',$old) 'all' $true 1 1 1}
Check 'preview unknown refuses without effects' {Main-Case 'preview-unknown' @('{"addons":[') 'all' $true 0 1 0}
Check 'actual existing new target stays useful with unknown peer' {Main-Case 'new-unknown-peer' @($new,'[]') 'all' $false 1 1 0}
Check 'actual insufficient identity held with known peer' {Main-Case 'insufficient-peer' @($empty,'{"addons":[{}]}') 'all' $false 1 1 0}
Check 'actual singleton root array held with known peer' {Main-Case 'singleton-root-peer' @($empty,'[{"addons":[]}]') 'all' $false 1 1 0}
Check 'actual duplicate keys cannot hide legacy from selection' {Main-Case 'duplicate-peer' @($empty,'{"addons":[{"name":"Tabliss"}],"addons":[]}') 'all' $false 1 1 0}
Check 'actual wrong-case addons cannot certify absence' {Main-Case 'addons-case' @('{"ADDONS":[]}') 'all' $false 0 1 0}
Check 'actual wrong-case identity held with known peer' {Main-Case 'identity-case-peer' @($empty,'{"addons":[{"NAME":"TablissNG"}]}') 'all' $false 1 1 0}
[pscustomobject]@{host=$PSVersionTable.PSVersion.ToString();platform=[Environment]::OSVersion.Platform.ToString();source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();fixture=$FixtureRoot;results=$script:results} | ConvertTo-Json -Depth 10
if(@($script:results|Where-Object {-not $_.pass}).Count){exit 1}
