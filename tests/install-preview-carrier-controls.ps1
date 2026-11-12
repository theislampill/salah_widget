#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][ValidateSet('ps51','ps7')][string]$ExpectedHost,
    [string]$OutputRoot=$(if($env:RUNNER_TEMP){$env:RUNNER_TEMP}else{[IO.Path]::GetTempPath()}),
    [string]$PreviewHarness=(Join-Path $PSScriptRoot 'install-preview.ps1'),
    [string]$FixtureLibrary=(Join-Path $PSScriptRoot 'install-preview-acquire-timed.ps1'),
    [string]$WindowLibrary=(Join-Path $PSScriptRoot 'install-preview-window.ps1')
)
# NEW reconstruction from recovered, digest-bound fixture bytes. Native execution
# is an explicitly dispatched acquisition step. This adapter evaluates only the
# exact maintained source-free control span and owned synthetic nested files.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$Utf8=New-Object Text.UTF8Encoding $false
$NativeWindows=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$HostExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$NativeModules=Join-Path $PSHOME 'Modules'
$hostVersion=$PSVersionTable.PSVersion.ToString()
$FixtureRoot=$null;$problem=$null;$inputs=@();$Results=@();$extraction=$null
$startedUtc=[DateTime]::UtcNow.ToString('o')
function Get-CarrierFact([string]$Path){
    $full=[IO.Path]::GetFullPath($Path);$bytes=[IO.File]::ReadAllBytes($full)
    $hasher=[Security.Cryptography.SHA256]::Create()
    try{$digest=([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
    [pscustomobject]@{path=$full;sha256=$digest;bytes=$bytes.Length}
}
function Read-CarrierAst([string]$Path){
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors)
    if(@($errors).Count){throw ('Source-free input parse failure: '+[IO.Path]::GetFileName($Path))}
    return $ast
}
function Get-UniqueCarrierSpan([string]$Text,[string]$Start,[string]$End){
    $first=$Text.IndexOf($Start,[StringComparison]::Ordinal)
    $last=$Text.IndexOf($End,[StringComparison]::Ordinal)
    if($first -lt 0 -or $last -le $first -or $Text.IndexOf($Start,$first+1,[StringComparison]::Ordinal) -ge 0 -or $Text.IndexOf($End,$last+1,[StringComparison]::Ordinal) -ge 0){throw 'Source-free extraction delimiters are not unique'}
    return $Text.Substring($first,$last-$first)
}
try{
    if(-not $NativeWindows -or -not [IO.Path]::IsPathRooted($HostExecutable)){throw 'Native Windows with an absolute host executable is required'}
    if(($ExpectedHost -eq 'ps51' -and ($hostVersion -notlike '5.1.*' -or $PSVersionTable.PSEdition -ne 'Desktop')) -or
       ($ExpectedHost -eq 'ps7' -and ($hostVersion -cne '7.6.6' -or $PSVersionTable.PSEdition -ne 'Core'))){throw 'Native host version or edition differs from ExpectedHost'}
    if($env:SALAH_TEST_CHILD_TIMEOUT_SECONDS -and $env:SALAH_TEST_CHILD_TIMEOUT_SECONDS -cne '60'){throw 'Source-free carrier requires the unchanged 60-second child budget'}
    $env:SALAH_TEST_CHILD_TIMEOUT_SECONDS='60'
    $FixtureRoot=[IO.Path]::GetFullPath((Join-Path $OutputRoot ('r0016-source-free-carrier-'+[guid]::NewGuid().ToString('N'))))
    [void][IO.Directory]::CreateDirectory($FixtureRoot)
    $inputRoot=Join-Path $FixtureRoot 'inputs';[void][IO.Directory]::CreateDirectory($inputRoot)
    $declared=@(
        @($PreviewHarness,'install-preview.ps1','e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916'),
        @($FixtureLibrary,'install-preview-acquire-timed.ps1','b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1'),
        @($WindowLibrary,'install-preview-window.ps1','05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83'),
        @($PSCommandPath,'install-preview-carrier-controls.ps1',$null)
    )
    foreach($entry in $declared){
        $original=Get-CarrierFact $entry[0]
        if($entry[2] -and $original.sha256 -cne $entry[2]){throw ('Supplied input digest differs: '+$entry[1])}
        $retained=Join-Path $inputRoot $entry[1]
        [IO.File]::WriteAllBytes($retained,[IO.File]::ReadAllBytes($original.path))
        $copy=Get-CarrierFact $retained
        if($copy.sha256 -cne $original.sha256 -or $copy.bytes -ne $original.bytes){throw 'Input copy custody differs'}
        $inputs+=@([pscustomobject]@{name=$entry[1];original=$original;retained=$copy})
    }
    $FixtureLibrary=Join-Path $inputRoot 'install-preview-acquire-timed.ps1'
    $PreviewHarness=Join-Path $inputRoot 'install-preview.ps1'
    $FrozenWindowLibrary=Join-Path $inputRoot 'install-preview-window.ps1'
    $libraryAst=Read-CarrierAst $FixtureLibrary
    $coreAst=Read-CarrierAst $PreviewHarness
    $windowAst=Read-CarrierAst $FrozenWindowLibrary
    $allowedFixtureFunctions=@('Write-FixtureText','Hash-File','Snapshot-Subject','New-ChildContext','Invoke-AcquisitionChild')
    foreach($name in $allowedFixtureFunctions){
        $definitions=@($libraryAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -ceq $name})
        if($definitions.Count -ne 1){throw ('Fixture function is missing or ambiguous: '+$name)}
        . ([scriptblock]::Create($definitions[0].Extent.Text))
    }
    $allowedWindowFunctions=@('Get-PreviewFileFact','Write-PreviewJson','Snapshot-Subject','Save-PreviewInventory','Wait-PreviewInvocationGate','Invoke-PreviewWindowChild')
    if(@($windowAst.EndBlock.Statements).Count -ne $allowedWindowFunctions.Count){throw 'Window library contains unexpected top-level statements'}
    foreach($name in $allowedWindowFunctions){
        $definitions=@($windowAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -ceq $name})
        if($definitions.Count -ne 1){throw ('Window function is missing or ambiguous: '+$name)}
        . ([scriptblock]::Create($definitions[0].Extent.Text))
    }
    $caseDefinitions=@($coreAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -ceq 'New-PreviewCase'})
    if($caseDefinitions.Count -ne 1){throw 'Maintained synthetic case constructor is missing or ambiguous'}
    . ([scriptblock]::Create($caseDefinitions[0].Extent.Text))
    $driverNodes=@($coreAst.FindAll({param($node) $node -is [Management.Automation.Language.StringConstantExpressionAst] -and $node.StringConstantType -eq 'SingleQuotedHereString'},$true))
    if($driverNodes.Count -ne 1){throw 'Maintained embedded driver is not uniquely delimited'}
    $Driver=Join-Path $FixtureRoot 'actual-embedded-driver.ps1'
    Write-FixtureText $Driver $driverNodes[0].Value
    $null=Read-CarrierAst $Driver
    $BaselineInvocation=Join-Path $FixtureRoot 'source-free-nested-invocation.ps1'
    Write-FixtureText $BaselineInvocation 'param([object]$Value) $null = $Value'
    $SourceFunctions=Join-Path $FixtureRoot 'source-free-functions.ps1'
    Write-FixtureText $SourceFunctions 'function R0016SourceFreeNoop { }'
    $EffectHelpers=@('R0016SourceFreeNoop')
    $FrozenSource=Join-Path $FixtureRoot 'source-free-placeholder.ps1'
    Write-FixtureText $FrozenSource 'param([switch]$DryRun) $null = $DryRun'
    $SourceHash=Hash-File $FrozenSource
    $coreText=[IO.File]::ReadAllText($PreviewHarness)
    $controlSpan=Get-UniqueCarrierSpan $coreText '$Results=New-Object ''System.Collections.Generic.List[object]''' 'if($guardProven -and $Suite -in @(''Helpers'',''All'')){'
    if($controlSpan -match '\$SourceFile\b|Run-PreviewCase|New-PreviewSourceVariant'){throw 'Source-free span includes product entry logic'}
    $spanPath=Join-Path $FixtureRoot 'source-free-control-span.ps1'
    Write-FixtureText $spanPath $controlSpan
    $null=Read-CarrierAst $spanPath
    $extraction=[pscustomobject]@{
        fixtureFunctions=$allowedFixtureFunctions;windowFunctions=$allowedWindowFunctions;coreFunctions=@('New-PreviewCase')
        embeddedDriver=(Get-CarrierFact $Driver);controlSpan=(Get-CarrierFact $spanPath)
        sourceFreePlaceholder=(Get-CarrierFact $FrozenSource);sourceFreeFunctions=(Get-CarrierFact $SourceFunctions)
        baselineInvocation=(Get-CarrierFact $BaselineInvocation)
    }
    # Execute this exact source-free span, never the core's top-level acquisition
    # or any Helpers/Wrapper/Mutants/All product dispatch.
    . ([scriptblock]::Create($controlSpan))
    $expectedCases=@('control-outside-subject-method-write-False','control-outside-subject-method-write-True','control-direct-loopback-transport-False','control-direct-loopback-transport-True','carrier-control-fallthrough','carrier-control-exit-zero','carrier-control-exit-nonzero','carrier-control-throw','carrier-control-finally-exit','carrier-control-parameter-failure')
    if($Results.Count -ne 10 -or @($Results|Where-Object{$_.case -notin $expectedCases}).Count){throw 'Source-free result inventory is incomplete or ambiguous'}
    foreach($expected in $expectedCases){if(@($Results|Where-Object{$_.case -ceq $expected}).Count -ne 1){throw 'Source-free case is missing or duplicated'}}
    foreach($row in $Results){
        $label=if($row.case -like 'carrier-control-*'){'carrier-control'}else{'guard-control'}
        $launchPath=Join-Path $row.process.fixture ($label+'.launch.json')
        $launch=[IO.File]::ReadAllText($launchPath)|ConvertFrom-Json
        if($launch.host -cne $HostExecutable -or $launch.processId -ne $row.process.processId -or $launch.nativeFile -cne $Driver -or $launch.budgetSeconds -ne 60){throw 'Source-free launch host, process, driver or budget differs'}
        if($row.process.stdoutDrainCompleted -ne $true -or $row.process.stderrDrainCompleted -ne $true -or $row.process.killGraceExpired -ne $false){throw 'Source-free child output or terminal acquisition is incomplete'}
        $elapsed=if($label -eq 'carrier-control'){$row.process.terminalObservedElapsedMs}else{$row.process.processExitObservedElapsedMs}
        if($null -eq $elapsed -or $elapsed -lt 0 -or $elapsed -ge 60000){throw 'Source-free terminal was first observed at/after its deadline'}
        $row|Add-Member -NotePropertyName commandHost -NotePropertyValue $HostExecutable
        $row|Add-Member -NotePropertyName rawLaunch -NotePropertyValue (Get-CarrierFact $launchPath)
    }
    foreach($input in $inputs){
        $current=Get-CarrierFact $input.original.path;$retained=Get-CarrierFact $input.retained.path
        if($current.sha256 -cne $input.original.sha256 -or $current.bytes -ne $input.original.bytes -or $retained.sha256 -cne $input.retained.sha256 -or $retained.bytes -ne $input.retained.bytes){throw 'Source-free input custody changed during execution'}
    }
}catch{$problem=$_.Exception.Message}
$rows=@($Results|ForEach-Object{$_})
$passed=$null -eq $problem -and $rows.Count -eq 10 -and @($rows|Where-Object{-not $_.pass}).Count -eq 0
$report=[pscustomobject][ordered]@{
    schema='r0016-source-free-native-carrier.v1';pass=$passed;classification=if($passed){'PASS'}else{'BOOTSTRAP_BLOCKED'};error=$problem
    provenance='NEW reconstructed adapter; exact recovered maintained fixture inputs';installerExecuted=$false
    expectedHost=$ExpectedHost;host=$hostVersion;nativeWindows=$NativeWindows;commandHost=$HostExecutable;fixture=$FixtureRoot
    startedUtc=$startedUtc;completedUtc=[DateTime]::UtcNow.ToString('o');inputs=$inputs;extraction=$extraction
    childBudgetSeconds=60;phaseAckBudgetSeconds=20;killGraceSeconds=5;pipeDrainSecondsEach=2
    casesExpected=10;casesObserved=$rows.Count;results=$rows;independentHardContainment='NOT_ACQUIRED'
    scopeLimits=@(
        'Owned synthetic method-write, loopback and nested-file controls only; no installer source is read or evaluated.',
        'Full prelaunch/postexit subject snapshots are retained separately from the six held invocation windows. No path, timestamp or startup-profile filename is excluded.',
        'Method/cmdlet denial is a fixture control, not an operating-system sandbox. External workflow containment and pre-start runtime settings require their own evidence.',
        'Native carrier acceptance does not qualify installer helpers, wrapper product cases, direct -File behavior, normal/NoOpen variants or whole-contract obligations.',
        'Recovered historical Linux or Windows observations are not execution evidence for these NEW adapter bytes.'
    )
}
$reportFact=$null
if($FixtureRoot){
    $reportPath=Join-Path $FixtureRoot 'carrier-report.json'
    [IO.File]::WriteAllText($reportPath,($report|ConvertTo-Json -Depth 20),$Utf8)
    $reportFact=Get-CarrierFact $reportPath
}
$result=[pscustomobject][ordered]@{
    schema='r0016-source-free-native-carrier-result.v1';pass=$passed;classification=$report.classification;error=$problem
    installerExecuted=$false;expectedHost=$ExpectedHost;host=$hostVersion;nativeWindows=$NativeWindows;commandHost=$HostExecutable
    casesExpected=10;casesObserved=$rows.Count;report=$reportFact;inputs=$inputs
}
$json=$result|ConvertTo-Json -Depth 8
if($FixtureRoot){[IO.File]::WriteAllText((Join-Path $FixtureRoot 'carrier-result.json'),$json,$Utf8)}
[Console]::WriteLine($json)
if(-not $passed){exit 2}
exit 0
