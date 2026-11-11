#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot = $(if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() })
)
# Capability acquisition only. This script never executes the installer.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
$Utf8 = New-Object Text.UTF8Encoding $false
$NativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$FixtureRoot = Join-Path $OutputRoot ('r0016-windows-acquire-' + [guid]::NewGuid().ToString('N'))
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
        R0016_ACQUIRE_READY = (Join-Path $hostControl 'ready.txt')
        R0016_ACQUIRE_NONCE = [guid]::NewGuid().ToString('N')
        R0016_EARLY_WRITE = (Join-Path $subject 'user-profile\early-write.txt')
        R0016_BP_TARGET = (Join-Path $subject 'user-profile\breakpoint-target.txt')
        R0016_BP_EVENTS = (Join-Path $hostControl 'breakpoint-events.txt')
        R0016_BP_RESULT = (Join-Path $hostControl 'breakpoint-result.json')
        R0016_PHASES = (Join-Path $hostControl 'autoload-phases.txt')
        R0016_NATIVE_UTILITY = (Join-Path $NativeModules 'Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1')
    }
    $values.R0016_FIXTURE_PF = $values.ProgramFiles
    $values.R0016_FIXTURE_PF86 = $values['ProgramFiles(x86)']
    foreach ($key in @('USERPROFILE','TEMP','LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)')) {
        [void][IO.Directory]::CreateDirectory($values[$key])
    }
    [pscustomobject]@{ root=$caseRoot; subject=$subject; hostControl=$hostControl; values=$values }
}
# Versioned timing derivative of frozen ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68.
# Effect assertions remain unchanged; launch/deadline/drain evidence is extended.
function Invoke-AcquisitionChild($Context, [string]$File, [string]$Label) {
    # Self-contained when imported by AST into the frozen R0016 core.
    $ChildTimeoutSeconds=60
    if($env:SALAH_TEST_CHILD_TIMEOUT_SECONDS){
        $explicitBudget=0
        if(-not [int]::TryParse($env:SALAH_TEST_CHILD_TIMEOUT_SECONDS,[ref]$explicitBudget) -or $explicitBudget -lt 30 -or $explicitBudget -gt 180){throw 'BOOTSTRAP_BLOCKED: SALAH_TEST_CHILD_TIMEOUT_SECONDS must be an integer from 30 through 180'}
        $ChildTimeoutSeconds=$explicitBudget
    }
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
    $launch=[pscustomobject]@{startedUtc=$startedUtc;createdUtc=$createdUtc;processId=$child.Id;host=$HostExecutable;nativeFile=$File;arguments=$info.Arguments;budgetSeconds=$ChildTimeoutSeconds;nonce=$Context.values.R0016_ACQUIRE_NONCE;scope='fixture child; installer evaluation is identified by its caller'}
    Write-FixtureText (Join-Path $Context.root ($Label+'.launch.json')) ($launch|ConvertTo-Json -Depth 5)
    $child.StandardInput.Close()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()
    $timedOut=$false;$readinessElapsedMs=$null;$killGraceExpired=$false;$killError=$null
    while($true){
        if($null -eq $readinessElapsedMs -and [IO.File]::Exists($Context.values.R0016_ACQUIRE_READY)){
            try{if([IO.File]::ReadAllText($Context.values.R0016_ACQUIRE_READY).Contains($Context.values.R0016_ACQUIRE_NONCE)){$readinessElapsedMs=$clock.Elapsed.TotalMilliseconds}}catch{}
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
    $ready = [IO.File]::Exists($Context.values.R0016_ACQUIRE_READY) -and
        [IO.File]::ReadAllText($Context.values.R0016_ACQUIRE_READY).Contains($Context.values.R0016_ACQUIRE_NONCE)
    [pscustomobject]@{
        exit=if($child.HasExited){$child.ExitCode}else{$null}; processId=$child.Id; fixture=$Context.root; nativeFile=$File
        startedUtc=$startedUtc;createdUtc=$createdUtc;processExitObservedUtc=$exitObservedUtc
        processCreationElapsedMs=$createdElapsedMs;processExitObservedElapsedMs=$exitObservedElapsedMs
        readinessObservedElapsedMs=if($null -ne $readinessElapsedMs){$readinessElapsedMs}elseif($ready){$exitObservedElapsedMs}else{$null}
        readinessFileUtc=if($ready){[IO.File]::GetLastWriteTimeUtc($Context.values.R0016_ACQUIRE_READY).ToString('o')}else{$null}
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

$SourceFile = [IO.Path]::GetFullPath($SourceFile)
$SourceHash = Hash-File $SourceFile
$tokens = $null; $parseErrors = $null
$sourceAst = [Management.Automation.Language.Parser]::ParseFile($SourceFile, [ref]$tokens, [ref]$parseErrors)
$sourceBytes = [IO.File]::ReadAllBytes($SourceFile)
$Results.Add([pscustomobject]@{
    case='exact supplied file parsing'; pass=(@($parseErrors).Count -eq 0 -and @($sourceBytes | Where-Object { $_ -gt 127 }).Count -eq 0)
    scope='parser only; installer not executed'; source=$SourceFile; sourceSha256=$SourceHash
    ascii=(@($sourceBytes | Where-Object { $_ -gt 127 }).Count -eq 0)
    errors=@($parseErrors | ForEach-Object { $_.Message })
    actualTopLevelFunctions=@($sourceAst.EndBlock.Statements | Where-Object { $_ -is [Management.Automation.Language.FunctionDefinitionAst] } | ForEach-Object { $_.Name })
})

$baselineFile = Join-Path $FixtureRoot 'baseline-no-effects.ps1'
Write-FixtureText $baselineFile @'
[IO.File]::WriteAllText($env:R0016_ACQUIRE_READY,$env:R0016_ACQUIRE_NONCE)
[Console]::WriteLine($PSVersionTable.PSVersion.ToString())
'@
$baseline = New-ChildContext 'host-startup-baseline'
$cold = Invoke-AcquisitionChild $baseline $baselineFile 'cold'
$warm = Invoke-AcquisitionChild $baseline $baselineFile 'warm'
$Results.Add([pscustomobject]@{
    case='exact-file host-startup baseline'; pass=($cold.exit -eq 0 -and $warm.exit -eq 0 -and $cold.readiness -and $warm.readiness)
    scope='owned USERPROFILE and TEMP remain fully monitored; observed startup changes are not installer effects'
    cold=$cold; warm=$warm
})

foreach ($startupVariant in @('minimal','original-prefix')) {
$late = New-ChildContext ('autoload-readiness-' + $startupVariant)
$moduleRoot = Join-Path $late.root 'modules'
$utilityRoot = Join-Path $moduleRoot 'Microsoft.PowerShell.Utility'
[void][IO.Directory]::CreateDirectory($utilityRoot)
$late.values.PSModulePath = $moduleRoot + [IO.Path]::PathSeparator + $NativeModules
$moduleText = @'
[IO.File]::AppendAllText($env:R0016_PHASES,'01 module-enter'+[Environment]::NewLine)
Import-Module $env:R0016_NATIVE_UTILITY -Scope Local
[IO.File]::AppendAllText($env:R0016_PHASES,'02 native-utility-imported'+[Environment]::NewLine)
[IO.File]::AppendAllText($env:R0016_PHASES,'03 constructor-begin'+[Environment]::NewLine)
__CONSTRUCTOR__
[IO.File]::AppendAllText($env:R0016_PHASES,'04 constructor-complete'+[Environment]::NewLine)
$env:ProgramFiles=$env:R0016_FIXTURE_PF
${env:ProgramFiles(x86)}=$env:R0016_FIXTURE_PF86
[IO.File]::AppendAllText($env:R0016_PHASES,'05 discovery-environment-reset'+[Environment]::NewLine)
function Write-Host { param($Object) [Console]::WriteLine([string]$Object) }
Export-ModuleMember -Function Write-Host -Cmdlet *
[IO.File]::AppendAllText($env:R0016_PHASES,'06 exports-complete'+[Environment]::NewLine)
[IO.File]::WriteAllText($env:R0016_ACQUIRE_READY,$env:R0016_ACQUIRE_NONCE)
'@
$constructor = if ($startupVariant -eq 'original-prefix') {
    '[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false'
} else { '[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)' }
Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psm1') $moduleText.Replace('__CONSTRUCTOR__',$constructor)
Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psd1') @'
@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='053c75b3-5af4-4900-97fd-2b431da6154a';FunctionsToExport=@('Write-Host');CmdletsToExport='*';AliasesToExport=@()}
'@
$lateFile = Join-Path $FixtureRoot 'early-dotnet-before-autoload.ps1'
Write-FixtureText $lateFile @'
[IO.File]::WriteAllText($env:R0016_EARLY_WRITE,'owned eager effect before first cmdlet')
Write-Host 'autoload occurs after the earlier method call'
'@
$lateRun = Invoke-AcquisitionChild $late $lateFile 'direct-file'
$earlyWrite = [IO.File]::Exists($late.values.R0016_EARLY_WRITE)
$Results.Add([pscustomobject]@{
    case=('Utility autoload pre-entry discriminator ' + $startupVariant); pass=($lateRun.exit -eq 0 -and $lateRun.readiness -and $earlyWrite -and -not $lateRun.timedOut)
    scope='controlled demonstration of late readiness; not a containment PASS'
    classification=if ($earlyWrite) { 'NOT_PRE_ENTRY' } else { 'ACQUISITION_GAP' }
    observation=$lateRun; earlierMethodExecuted=$earlyWrite
    phases=if([IO.File]::Exists($late.values.R0016_PHASES)){@([IO.File]::ReadAllLines($late.values.R0016_PHASES))}else{@()}
})
}

$methodFile = Join-Path $FixtureRoot 'owned-method-effect.ps1'
Write-FixtureText $methodFile '[IO.File]::WriteAllText($env:R0016_BP_TARGET,''owned effect must be suppressed by a claimed guard'')'
foreach ($mode in @('throw','break','stop-event')) {
    $context = New-ChildContext ('breakpoint-' + $mode)
    $context.values.R0016_BP_SOURCE = $methodFile
    $driver = Join-Path $FixtureRoot ('breakpoint-driver-' + $mode + '.ps1')
    $driverText = @'
$ErrorActionPreference='Stop'
__STOP_HANDLER__
$bp=Set-PSBreakpoint -Script $env:R0016_BP_SOURCE -Line 1 -Action {
    [IO.File]::AppendAllText($env:R0016_BP_EVENTS,'attempt'+[Environment]::NewLine)
    __ACTION__
}
$reason=$null
try { & $env:R0016_BP_SOURCE } catch { $reason=$_.Exception.Message }
finally {
    if($bp){Remove-PSBreakpoint -Breakpoint $bp}
    if($stopHandler){[Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.remove_DebuggerStop($stopHandler)}
}
$row=[pscustomobject]@{methodAttemptObserved=[IO.File]::Exists($env:R0016_BP_EVENTS);methodExecuted=[IO.File]::Exists($env:R0016_BP_TARGET);reason=$reason}
[IO.File]::WriteAllText($env:R0016_BP_RESULT,($row | ConvertTo-Json -Compress))
'@
    $action = if ($mode -eq 'throw') { "throw 'R0016 fixture denied method'" } else { 'break' }
    $stopHandler = if ($mode -eq 'stop-event') { @'
$stopHandler=[System.EventHandler[Management.Automation.DebuggerStopEventArgs]]{
    param($sender,$eventArgs)
    [IO.File]::AppendAllText($env:R0016_BP_EVENTS,'stop-event'+[Environment]::NewLine)
    $eventArgs.ResumeAction=[Management.Automation.DebuggerResumeAction]::Stop
}
[Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.add_DebuggerStop($stopHandler)
'@ } else { '$stopHandler=$null' }
    Write-FixtureText $driver $driverText.Replace('__ACTION__', $action).Replace('__STOP_HANDLER__', $stopHandler)
    $run = Invoke-AcquisitionChild $context $driver 'guard'
    $attempt = [IO.File]::Exists($context.values.R0016_BP_EVENTS)
    $executed = [IO.File]::Exists($context.values.R0016_BP_TARGET)
    $Results.Add([pscustomobject]@{
        case=('method breakpoint action ' + $mode); pass=($attempt -and -not $executed)
        scope='wrapper/runspace command-language guard only; not OS containment or fresh installer -File'
        classification=if ($attempt -and -not $executed) { 'GUARD_OBSERVED' } else { 'GUARD_UNPROVEN' }
        observation=$run; attempted=$attempt; executed=$executed
    })
}

$capabilities = [ordered]@{ nativeWindows=$NativeWindows; globalPolicyChanged=$false; containmentEstablished=$false; transportCallsAttempted=$false }
if ($NativeWindows) {
    $nativeControl = Join-Path $FixtureRoot 'host-capabilities'
    [void][IO.Directory]::CreateDirectory($nativeControl)
    $previousTemporary = [Environment]::GetEnvironmentVariable('TEMP','Process')
    $previousTmp = [Environment]::GetEnvironmentVariable('TMP','Process')
    $previousAnalysis = [Environment]::GetEnvironmentVariable('PSModuleAnalysisCachePath','Process')
    $env:TEMP = $nativeControl
    $env:TMP = $nativeControl
    $env:PSModuleAnalysisCachePath = Join-Path $nativeControl 'module-analysis-cache'
    $capabilities.hostControlRoot = $nativeControl
    try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal $identity
    $capabilities.elevatedAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $commands = @('Get-NetFirewallRule','New-NetFirewallRule','Remove-NetFirewallRule','Get-WinEvent','logman.exe','wpr.exe','pktmon.exe','auditpol.exe')
    $capabilities.commands = @($commands | ForEach-Object {
        $command = Get-Command $_ -ErrorAction SilentlyContinue
        [pscustomobject]@{ name=$_; available=($null -ne $command); kind=if($command){[string]$command.CommandType}else{$null} }
    })
    try {
        $security = Get-WinEvent -ListLog Security -ErrorAction Stop
        $capabilities.securityLog = [pscustomobject]@{ readable=$true; enabled=$security.IsEnabled; recordCount=$security.RecordCount }
    } catch { $capabilities.securityLog = [pscustomobject]@{ readable=$false; reason=$_.Exception.Message } }
    $auditpol = Join-Path $env:WINDIR 'System32\auditpol.exe'
    if ([IO.File]::Exists($auditpol)) {
        try {
            $audit = & $auditpol /get '/subcategory:Filtering Platform Connection' /r 2>&1 | Out-String
            $capabilities.filteringPlatformAudit = [pscustomobject]@{ exit=$LASTEXITCODE; text=$audit }
        } catch { $capabilities.filteringPlatformAudit = [pscustomobject]@{ reason=$_.Exception.Message } }
    }
    try {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class R0016CapabilityExports {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern IntPtr LoadLibraryW(string name);
    [DllImport("kernel32.dll", CharSet=CharSet.Ansi, SetLastError=true)]
    public static extern IntPtr GetProcAddress(IntPtr module, string name);
}
'@
        $exports = @()
        foreach ($row in @(
            @('userenv.dll','CreateAppContainerProfile'), @('userenv.dll','DeleteAppContainerProfile'),
            @('userenv.dll','DeriveAppContainerSidFromAppContainerName'),
            @('kernel32.dll','InitializeProcThreadAttributeList'), @('kernel32.dll','UpdateProcThreadAttribute'),
            @('kernel32.dll','CreateJobObjectW'), @('kernel32.dll','SetInformationJobObject'), @('kernel32.dll','AssignProcessToJobObject')
        )) {
            $moduleHandle = [R0016CapabilityExports]::LoadLibraryW($row[0])
            $exports += [pscustomobject]@{ library=$row[0]; api=$row[1]; present=($moduleHandle -ne [IntPtr]::Zero -and [R0016CapabilityExports]::GetProcAddress($moduleHandle,$row[1]) -ne [IntPtr]::Zero) }
        }
        $capabilities.nativeExports = $exports
    } catch { $capabilities.nativeExportAcquisitionError = $_.Exception.Message }
    } finally {
        [Environment]::SetEnvironmentVariable('TEMP',$previousTemporary,'Process')
        [Environment]::SetEnvironmentVariable('TMP',$previousTmp,'Process')
        [Environment]::SetEnvironmentVariable('PSModuleAnalysisCachePath',$previousAnalysis,'Process')
    }
} else {
    $capabilities.nativeStatus = 'NOT_RUN_ON_WINDOWS'
}

$report = [pscustomobject][ordered]@{
    schema='r0016-windows-acquisition.timing-v2'
    parentFixtureSha256='ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68'
    pass=(@($Results | Where-Object { -not $_.pass }).Count -eq 0)
    acquisitionCompleted=$true
    nativeWindows=$NativeWindows
    installerExecuted=$false
    installerQualified=$false
    host=$PSVersionTable.PSVersion.ToString()
    hostExecutable=$HostExecutable
    fixture=$FixtureRoot
    source=$SourceFile
    sourceSha256=$SourceHash
    sourceUnchanged=((Hash-File $SourceFile) -ceq $SourceHash)
    testSha256=(Hash-File $PSCommandPath)
    results=$Results.ToArray()
    capabilities=[pscustomobject]$capabilities
    gaps=@(
        'No OS containment has been established by API presence or command inventory.',
        'No network attempt was made; WFP/ETW availability is not attempted-call evidence.',
        'AppContainer suitability for representative R0015 private-DACL normal positives is unproved.',
        'Method breakpoints are a wrapper/runspace control and cannot establish fresh-host pre-entry -File instrumentation.',
        'Utility autoload follows early method expressions.',
        'No installer or real owner profile was exercised.'
    )
}
$json = $report | ConvertTo-Json -Depth 12
Write-FixtureText (Join-Path $FixtureRoot 'acquisition.json') $json
[Console]::WriteLine($json)
# Acquisition returns evidence even when a proposed guard is disproved.
exit 0
