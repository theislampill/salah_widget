#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot = $(if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }),
    [ValidateRange(30,180)][int]$ChildTimeoutSeconds = 60,
    [ValidateSet('Minimal','Exports')][string]$VariantSet = 'Minimal'
)
# R0013 run4 cold/warm timing derivative; never executes the installer.
# Parent probe SHA256 ae274fa5edbd0e9fe950af8ede7503befec1eeea36d9ba5d54c912de00ec307e remains unchanged.
# Derived from install-preview-acquire.ps1 SHA256 ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68.
# Reuses owned child contexts, case-insensitive environment replacement and retained timeout evidence.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
$Utf8 = New-Object Text.UTF8Encoding $false
$NativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$FixtureRoot = Join-Path $OutputRoot ('r0013-native-bootstrap-timing-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($FixtureRoot)
$FixtureRoot = [IO.Path]::GetFullPath($FixtureRoot)
$HostExecutable = [Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$NativeModules = Join-Path $PSHOME 'Modules'
$Results = New-Object 'System.Collections.Generic.List[object]'

function Write-FixtureText([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, $Utf8)
}
function Hash-File([string]$Path) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash([IO.File]::ReadAllBytes($Path)))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}
function Snapshot-Subject([string]$Path) {
    $rows = @([IO.Directory]::EnumerateFileSystemEntries($Path, '*', [IO.SearchOption]::AllDirectories) |
        Sort-Object | ForEach-Object {
            $attributes = [IO.File]::GetAttributes($_)
            [pscustomobject][ordered]@{
                path = $_.Substring($Path.Length)
                attributes = [string]$attributes
                hash = if (($attributes -band [IO.FileAttributes]::Directory) -eq 0) { Hash-File $_ } else { $null }
            }
        })
    return ,$rows
}
function New-ChildContext([string]$Name) {
    $caseRoot = Join-Path $FixtureRoot $Name
    $subject = Join-Path $caseRoot 'subject'
    $hostControl = Join-Path $caseRoot 'host-control'
    foreach ($path in @($caseRoot, $subject, $hostControl)) { [void][IO.Directory]::CreateDirectory($path) }
    $values = [ordered]@{
        USERPROFILE = (Join-Path $subject 'user-profile')
        HOME = (Join-Path $subject 'user-profile')
        TEMP = (Join-Path $subject 'temp')
        TMP = (Join-Path $subject 'temp')
        LOCALAPPDATA = (Join-Path $subject 'user-profile\AppData\Local')
        APPDATA = (Join-Path $subject 'user-profile\AppData\Roaming')
        ProgramFiles = (Join-Path $subject 'program-files')
        'ProgramFiles(x86)' = (Join-Path $subject 'program-files-x86')
        PSModulePath = $NativeModules
        PSModuleAnalysisCachePath = (Join-Path $hostControl 'module-analysis-cache')
        POWERSHELL_TELEMETRY_OPTOUT = '1'
        DOTNET_EnableDiagnostics = '0'
        DOTNET_CLI_TELEMETRY_OPTOUT = '1'
        DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
        DOTNET_CLI_HOME = $hostControl
        R0013_ACQUIRE_READY = (Join-Path $hostControl 'ready.txt')
        R0013_ACQUIRE_NONCE = [guid]::NewGuid().ToString('N')
        R0013_EARLY_WRITE = (Join-Path $subject 'user-profile\early-write.txt')
        R0013_BP_TARGET = (Join-Path $subject 'user-profile\breakpoint-target.txt')
        R0013_BP_EVENTS = (Join-Path $hostControl 'breakpoint-events.txt')
        R0013_BP_RESULT = (Join-Path $hostControl 'breakpoint-result.json')
        R0013_PHASES = (Join-Path $hostControl 'autoload-phases.txt')
        R0013_NATIVE_UTILITY = (Join-Path $NativeModules 'Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1')
    }
    $values.R0013_FIXTURE_PF = $values.ProgramFiles
    $values.R0013_FIXTURE_PF86 = $values['ProgramFiles(x86)']
    foreach ($key in @('USERPROFILE','TEMP','LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)')) {
        [void][IO.Directory]::CreateDirectory($values[$key])
    }
    [pscustomobject]@{ root=$caseRoot; subject=$subject; hostControl=$hostControl; values=$values }
}
function Invoke-AcquisitionChild($Context, [string]$File, [string]$Label) {
    $before = Snapshot-Subject $Context.subject
    Write-FixtureText (Join-Path $Context.root ($Label + '.before.json')) (ConvertTo-Json -InputObject $before -Depth 5)
    $cacheBeforeExists=[IO.File]::Exists($Context.values.PSModuleAnalysisCachePath)
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $HostExecutable
    $info.Arguments = '-NoProfile -File "' + $File.Replace('"','\"') + '"'
    $info.WorkingDirectory = $Context.root
    $info.UseShellExecute = $false
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    # Remove case variants before replacing Windows' case-insensitive keys.
    foreach ($key in @($info.EnvironmentVariables.Keys)) {
        if (@($Context.values.Keys) -contains [string]$key) { $info.EnvironmentVariables.Remove([string]$key) }
    }
    foreach ($key in $Context.values.Keys) { $info.EnvironmentVariables[[string]$key] = [string]$Context.values[$key] }
    $child = New-Object Diagnostics.Process
    $child.StartInfo = $info
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $startedUtc=[DateTime]::UtcNow.ToString('o')
    [void]$child.Start()
    $createdUtc=[DateTime]::UtcNow.ToString('o')
    $createdElapsedMs=$clock.Elapsed.TotalMilliseconds
    $launch=[pscustomobject]@{startedUtc=$startedUtc;createdUtc=$createdUtc;processId=$child.Id;host=$HostExecutable;nativeFile=$File;arguments=$info.Arguments;budgetSeconds=$ChildTimeoutSeconds;nonce=$Context.values.R0013_ACQUIRE_NONCE;installerExecuted=$false}
    Write-FixtureText (Join-Path $Context.root ($Label+'.launch.json')) ($launch|ConvertTo-Json -Depth 5)
    $child.StandardInput.Close()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()
    $timedOut=$false;$readinessElapsedMs=$null;$killGraceExpired=$false;$killError=$null
    while($true){
        if($null -eq $readinessElapsedMs -and [IO.File]::Exists($Context.values.R0013_ACQUIRE_READY)){
            try{if([IO.File]::ReadAllText($Context.values.R0013_ACQUIRE_READY) -ceq $Context.values.R0013_ACQUIRE_NONCE){$readinessElapsedMs=$clock.Elapsed.TotalMilliseconds}}catch{}
        }
        if($child.HasExited){break}
        if($clock.Elapsed.TotalSeconds -ge $ChildTimeoutSeconds){
            $timedOut=$true
            try{$child.Kill()}catch{$killError=$_.Exception.Message}
            $killGraceExpired=-not $child.WaitForExit(5000)
            break
        }
        $null=$child.WaitForExit(100)
    }
    $exitObservedUtc=[DateTime]::UtcNow.ToString('o');$exitObservedElapsedMs=$clock.Elapsed.TotalMilliseconds
    $stdoutDrained=$stdoutTask.Wait(2000);$stderrDrained=$stderrTask.Wait(2000)
    $stdout=if($stdoutDrained){$stdoutTask.GetAwaiter().GetResult()}else{''}
    $stderr=if($stderrDrained){$stderrTask.GetAwaiter().GetResult()}else{''}
    $after = Snapshot-Subject $Context.subject
    Write-FixtureText (Join-Path $Context.root ($Label + '.stdout.txt')) $stdout
    Write-FixtureText (Join-Path $Context.root ($Label + '.stderr.txt')) $stderr

    Write-FixtureText (Join-Path $Context.root ($Label + '.after.json')) (ConvertTo-Json -InputObject $after -Depth 5)
    $ready = [IO.File]::Exists($Context.values.R0013_ACQUIRE_READY) -and
        [IO.File]::ReadAllText($Context.values.R0013_ACQUIRE_READY) -ceq $Context.values.R0013_ACQUIRE_NONCE
    [pscustomobject]@{
        exit=if($child.HasExited){$child.ExitCode}else{$null}; processId=$child.Id; fixture=$Context.root; nativeFile=$File
        startedUtc=$startedUtc;createdUtc=$createdUtc;processExitObservedUtc=$exitObservedUtc
        processCreationElapsedMs=$createdElapsedMs;processExitObservedElapsedMs=$exitObservedElapsedMs
        readinessObservedElapsedMs=if($null -ne $readinessElapsedMs){$readinessElapsedMs}elseif($ready){$exitObservedElapsedMs}else{$null}
        readinessFileUtc=if($ready){[IO.File]::GetLastWriteTimeUtc($Context.values.R0013_ACQUIRE_READY).ToString('o')}else{$null}
        budgetSeconds=$ChildTimeoutSeconds;killGraceSeconds=5;pipeDrainSecondsEach=2
        killGraceExpired=$killGraceExpired;killError=$killError;stdoutDrainCompleted=$stdoutDrained;stderrDrainCompleted=$stderrDrained
        moduleCacheBeforeExists=$cacheBeforeExists;moduleCacheAfterExists=[IO.File]::Exists($Context.values.PSModuleAnalysisCachePath)
        moduleCacheAfterUtc=if([IO.File]::Exists($Context.values.PSModuleAnalysisCachePath)){[IO.File]::GetLastWriteTimeUtc($Context.values.PSModuleAnalysisCachePath).ToString('o')}else{$null}
        timedOut=$timedOut
        preparation=if($timedOut){'BOOTSTRAP_BLOCKED_TIMEOUT'}elseif($killGraceExpired -or -not $stdoutDrained -or -not $stderrDrained){'BOOTSTRAP_BLOCKED_DRAIN'}else{'COMPLETED'}
        readiness=$ready
        subjectUnchanged=((ConvertTo-Json -InputObject $before -Depth 5 -Compress) -ceq (ConvertTo-Json -InputObject $after -Depth 5 -Compress))
        before=$before; after=$after; stdout=$stdout; stderr=$stderr
    }
}


$SourceFile=[IO.Path]::GetFullPath($SourceFile)
$SourceHash=Hash-File $SourceFile
$TestHash=Hash-File $PSCommandPath
$probeFile=Join-Path $FixtureRoot 'phase-only-no-installer.ps1'
Write-FixtureText $probeFile @'
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'script-enter'+[Environment]::NewLine))
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'join-path-begin'+[Environment]::NewLine))
$path=Join-Path $env:TEMP 'no-created-directory'
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'join-path-returned'+[Environment]::NewLine))
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'write-host-begin'+[Environment]::NewLine))
Write-Host 'R0013 bootstrap probe; no installer invocation'
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'write-host-returned'+[Environment]::NewLine))
[IO.File]::WriteAllText($env:R0013_ACQUIRE_READY,$env:R0013_ACQUIRE_NONCE)
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'script-completed'+[Environment]::NewLine))
'@
$observations=@()
$variants=if($VariantSet -eq 'Exports'){@('native-only','private-wildcard-cmdlets','private-explicit-cmdlets','private-no-cmdlets')}else{@('native-only','private-wildcard-cmdlets')}
foreach($variant in $variants) {
    $context=New-ChildContext $variant
    if($variant -ne 'native-only') {
        $moduleRoot=Join-Path $context.root 'modules'
        $utilityRoot=Join-Path $moduleRoot 'Microsoft.PowerShell.Utility'
        [void][IO.Directory]::CreateDirectory($utilityRoot)
        $context.values.PSModulePath=$moduleRoot+[IO.Path]::PathSeparator+$NativeModules
        Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psm1') @'
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'utility-wrapper-entered'+[Environment]::NewLine))
Import-Module $env:R0013_NATIVE_UTILITY -Scope Local
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'native-utility-imported'+[Environment]::NewLine))
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'encoding-constructor-returned'+[Environment]::NewLine))
function Write-Host { param($Object) [Console]::WriteLine([string]$Object) }
Export-ModuleMember -Function Write-Host -Cmdlet *
[IO.File]::AppendAllText($env:R0013_PHASES,([DateTime]::UtcNow.ToString('o')+"`t"+[Diagnostics.Stopwatch]::GetTimestamp().ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+[Diagnostics.Stopwatch]::Frequency.ToString([Globalization.CultureInfo]::InvariantCulture)+"`t"+$PID+"`t"+$env:R0013_ACQUIRE_NONCE+"`t"+'utility-exports-complete'+[Environment]::NewLine))
'@
        $exports=if($variant -eq 'private-wildcard-cmdlets'){"'*'"}elseif($variant -eq 'private-explicit-cmdlets'){"@('New-Object','ConvertTo-Json','ConvertFrom-Json')"}else{'@()'}
        $manifest="@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='71364fa3-4674-4018-8cd0-e606d351ce41';FunctionsToExport=@('Write-Host');CmdletsToExport="+$exports+";AliasesToExport=@()}"
        Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psd1') $manifest
    }
    $coldCompleted=$false
    foreach($iteration in @('cold','warm')){
        $context.values.R0013_PHASES=Join-Path $context.hostControl ($iteration+'-phases.tsv')
        $context.values.R0013_ACQUIRE_READY=Join-Path $context.hostControl ($iteration+'-ready.txt')
        $context.values.R0013_ACQUIRE_NONCE=[guid]::NewGuid().ToString('N')
        $run=Invoke-AcquisitionChild $context $probeFile $iteration
        $phaseRows=New-Object 'System.Collections.Generic.List[object]'
        $phaseError=$null;$phaseProtocol=$true;$previousTicks=$null;$firstTicks=$null
        try{
            foreach($line in @([IO.File]::ReadAllLines($context.values.R0013_PHASES))){
                if(-not $line){continue}
                $parts=$line -split "`t"
                if($parts.Count -ne 6){throw 'Malformed timestamped phase record'}
                $null=[DateTimeOffset]::Parse($parts[0],[Globalization.CultureInfo]::InvariantCulture)
                $ticks=[long]$parts[1];$frequency=[long]$parts[2];$recordPid=[int]$parts[3]
                if($frequency -le 0 -or $recordPid -ne $run.processId -or $parts[4] -cne $context.values.R0013_ACQUIRE_NONCE){throw 'Phase identity/clock mismatch'}
                if($null -ne $previousTicks -and $ticks -lt $previousTicks){throw 'Phase monotonic clock went backwards'}
                if($null -eq $firstTicks){$firstTicks=$ticks}
                $phaseRows.Add([pscustomobject]@{utc=$parts[0];counterTicks=$ticks;counterFrequency=$frequency;processId=$recordPid;nonce=$parts[4];phase=$parts[5];elapsedSinceScriptEnterMs=1000.0*($ticks-$firstTicks)/$frequency})
                $previousTicks=$ticks
            }
        }catch{$phaseError=$_.Exception.Message;$phaseProtocol=$false}
        $phases=@($phaseRows|ForEach-Object{$_.phase})
        $expected=@('script-enter','join-path-begin','join-path-returned','write-host-begin')
        if($variant -ne 'native-only'){$expected+=@('utility-wrapper-entered','native-utility-imported','encoding-constructor-returned','utility-exports-complete')}
        $expected+=@('write-host-returned','script-completed')
        # Preserve the original completion assertion. Autoload can interleave
        # module phases differently; record that ordering without inventing a
        # new acceptance requirement for the unresolved preparation mechanism.
        $sequenceMatchesExpected=(($phases -join '|') -ceq ($expected -join '|'))
        $phaseProtocol=$phaseProtocol -and ($phases -contains 'script-completed')
        $pass=$run.exit -eq 0 -and -not $run.timedOut -and $run.readiness -and $phaseProtocol -and $run.stdoutDrainCompleted -and $run.stderrDrainCompleted
        $observations += [pscustomobject]@{
            case=($variant+'-'+$iteration);variant=$variant;iteration=$iteration;pass=$pass
            scope='R0013 no-installer cold/warm native -File first-command timing only'
            classification=if($pass){'ACQUISITION_COMPLETED'}else{'BOOTSTRAP_BLOCKED'}
            profileAndModuleCacheReused=($iteration -eq 'warm')
            priorColdCompleted=if($iteration -eq 'warm'){$coldCompleted}else{$null}
            reuseInterpretation=if($iteration -eq 'cold'){'new owned profile/cache'}elseif($coldCompleted){'fresh process reusing completed cold profile/cache'}else{'reuse after incomplete cold; not a completed warm baseline'}
            phases=$phases;phaseRecords=$phaseRows.ToArray();phaseProtocolValid=$phaseProtocol;phaseError=$phaseError
            phaseSequenceMatchesExpected=$sequenceMatchesExpected;expectedPhaseSequence=$expected
            observation=$run
            moduleManifest=if($variant -eq 'native-only'){$null}else{[IO.File]::ReadAllText((Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psd1'))}
        }
        if($iteration -eq 'cold'){$coldCompleted=$pass}
        Write-FixtureText (Join-Path $context.root ($iteration+'.observation.json')) ($observations[-1]|ConvertTo-Json -Depth 12)
        Write-FixtureText (Join-Path $FixtureRoot 'partial-results.json') (ConvertTo-Json -InputObject $observations -Depth 12)
    }
}
$report=[pscustomobject][ordered]@{
    schema='r0013-native-bootstrap-timing.v2'
    parentProbeSha256='ae274fa5edbd0e9fe950af8ede7503befec1eeea36d9ba5d54c912de00ec307e'
    pass=(@($observations|Where-Object{-not $_.pass}).Count -eq 0 -and (Hash-File $SourceFile) -ceq $SourceHash -and (Hash-File $PSCommandPath) -ceq $TestHash)
    variantSet=$VariantSet
    budgets=[pscustomobject]@{childSeconds=$ChildTimeoutSeconds;scheduledChildren=2*$variants.Count;killGraceSeconds=5;pipeDrainSecondsEach=2;recommendedCollectorMinimumSeconds=2*$variants.Count*($ChildTimeoutSeconds+9)+30}
    derivedFrom='install-preview-acquire.ps1'
    derivedFromSha256='ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68'
    derivation='Versioned run4 correction: retain owned no-installer source/flags, use bounded60s child budget by default, timestamp each phase, compare fresh cold and same-profile/cache warm processes; preserve prior failed15s receipts.'
    host=$PSVersionTable.PSVersion.ToString()
    nativeWindows=$NativeWindows
    hostExecutable=$HostExecutable
    installerExecuted=$false
    installerQualified=$false
    source=$SourceFile
    sourceSha256=$SourceHash
    sourceUnchanged=((Hash-File $SourceFile) -ceq $SourceHash)
    testSha256=$TestHash
    testUnchanged=((Hash-File $PSCommandPath) -ceq $TestHash)
    fixture=$FixtureRoot
    results=$observations
    limitations=@('No installer or unchanged product suite is rerun.','Underlying Windows delay cause is unresolved.','Warm reuse after an incomplete cold child is labeled separately.','Parent elapsed Stopwatch and child within-process monotonic phase deltas are recorded separately from wall-clock timestamps.','This cannot qualify installer behavior.','The private modules are diagnostic derivatives, not changes to shared tests.','Timeout and missing phases are preparation evidence.','No network calls, tracing, firewall/audit changes, or AppContainer setup are performed.')
}
$json=$report | ConvertTo-Json -Depth 12
Write-FixtureText (Join-Path $FixtureRoot 'timing.json') $json
[Console]::WriteLine($json)
exit 0
