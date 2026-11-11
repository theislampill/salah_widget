#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot = $(if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() })
)
# R0013 preparation-only derivative; never executes the installer.
# Derived from install-preview-acquire.ps1 SHA256 ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68.
# Reuses owned child contexts, case-insensitive environment replacement and retained timeout evidence.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
$Utf8 = New-Object Text.UTF8Encoding $false
$NativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$FixtureRoot = Join-Path $OutputRoot ('r0013-native-bootstrap-' + [guid]::NewGuid().ToString('N'))
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
    [void]$child.Start()
    $child.StandardInput.Close()
    $stdoutTask = $child.StandardOutput.ReadToEndAsync()
    $stderrTask = $child.StandardError.ReadToEndAsync()
    $timedOut = -not $child.WaitForExit(15000)
    if ($timedOut) {
        $child.Kill()
        $child.WaitForExit()
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $after = Snapshot-Subject $Context.subject
    Write-FixtureText (Join-Path $Context.root ($Label + '.stdout.txt')) $stdout
    Write-FixtureText (Join-Path $Context.root ($Label + '.stderr.txt')) $stderr
    Write-FixtureText (Join-Path $Context.root ($Label + '.before.json')) (ConvertTo-Json -InputObject $before -Depth 5)
    Write-FixtureText (Join-Path $Context.root ($Label + '.after.json')) (ConvertTo-Json -InputObject $after -Depth 5)
    $ready = [IO.File]::Exists($Context.values.R0013_ACQUIRE_READY) -and
        [IO.File]::ReadAllText($Context.values.R0013_ACQUIRE_READY).Contains($Context.values.R0013_ACQUIRE_NONCE)
    [pscustomobject]@{
        exit=$child.ExitCode; processId=$child.Id; fixture=$Context.root; nativeFile=$File
        timedOut=$timedOut
        preparation=if($timedOut){'BOOTSTRAP_BLOCKED_TIMEOUT'}else{'COMPLETED'}
        readiness=$ready
        subjectUnchanged=((ConvertTo-Json -InputObject $before -Depth 5 -Compress) -ceq (ConvertTo-Json -InputObject $after -Depth 5 -Compress))
        before=$before; after=$after; stdout=$stdout; stderr=$stderr
    }
}


$SourceFile=[IO.Path]::GetFullPath($SourceFile)
$SourceHash=Hash-File $SourceFile
$probeFile=Join-Path $FixtureRoot 'phase-only-no-installer.ps1'
Write-FixtureText $probeFile @'
[IO.File]::AppendAllText($env:R0013_PHASES,'script-enter'+[Environment]::NewLine)
[IO.File]::AppendAllText($env:R0013_PHASES,'join-path-begin'+[Environment]::NewLine)
$path=Join-Path $env:TEMP 'no-created-directory'
[IO.File]::AppendAllText($env:R0013_PHASES,'join-path-returned'+[Environment]::NewLine)
[IO.File]::AppendAllText($env:R0013_PHASES,'write-host-begin'+[Environment]::NewLine)
Write-Host 'R0013 bootstrap probe; no installer invocation'
[IO.File]::AppendAllText($env:R0013_PHASES,'write-host-returned'+[Environment]::NewLine)
[IO.File]::WriteAllText($env:R0013_ACQUIRE_READY,$env:R0013_ACQUIRE_NONCE)
[IO.File]::AppendAllText($env:R0013_PHASES,'script-completed'+[Environment]::NewLine)
'@
$observations=@()
foreach($variant in @('native-only','private-wildcard-cmdlets','private-explicit-cmdlets','private-no-cmdlets')) {
    $context=New-ChildContext $variant
    if($variant -ne 'native-only') {
        $moduleRoot=Join-Path $context.root 'modules'
        $utilityRoot=Join-Path $moduleRoot 'Microsoft.PowerShell.Utility'
        [void][IO.Directory]::CreateDirectory($utilityRoot)
        $context.values.PSModulePath=$moduleRoot+[IO.Path]::PathSeparator+$NativeModules
        Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psm1') @'
[IO.File]::AppendAllText($env:R0013_PHASES,'utility-wrapper-entered'+[Environment]::NewLine)
Import-Module $env:R0013_NATIVE_UTILITY -Scope Local
[IO.File]::AppendAllText($env:R0013_PHASES,'native-utility-imported'+[Environment]::NewLine)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
[IO.File]::AppendAllText($env:R0013_PHASES,'encoding-constructor-returned'+[Environment]::NewLine)
function Write-Host { param($Object) [Console]::WriteLine([string]$Object) }
Export-ModuleMember -Function Write-Host -Cmdlet *
[IO.File]::AppendAllText($env:R0013_PHASES,'utility-exports-complete'+[Environment]::NewLine)
'@
        $exports=if($variant -eq 'private-wildcard-cmdlets'){"'*'"}elseif($variant -eq 'private-explicit-cmdlets'){"@('New-Object','ConvertTo-Json','ConvertFrom-Json')"}else{'@()'}
        $manifest="@{RootModule='Microsoft.PowerShell.Utility.psm1';ModuleVersion='99.0';GUID='71364fa3-4674-4018-8cd0-e606d351ce41';FunctionsToExport=@('Write-Host');CmdletsToExport="+$exports+";AliasesToExport=@()}"
        Write-FixtureText (Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psd1') $manifest
    }
    $run=Invoke-AcquisitionChild $context $probeFile 'native-file'
    $phases=if([IO.File]::Exists($context.values.R0013_PHASES)){@([IO.File]::ReadAllLines($context.values.R0013_PHASES))}else{@()}
    $observations += [pscustomobject]@{
        case=$variant
        pass=($run.exit -eq 0 -and -not $run.timedOut -and $run.readiness -and $phases -contains 'script-completed')
        scope='R0013 no-installer native -File bootstrap diagnosis only'
        phases=$phases
        observation=$run
        moduleManifest=if($variant -eq 'native-only'){$null}else{[IO.File]::ReadAllText((Join-Path $utilityRoot 'Microsoft.PowerShell.Utility.psd1'))}
    }
}
$report=[pscustomobject][ordered]@{
    schema='r0013-native-bootstrap-diagnostic.v1'
    derivedFrom='install-preview-acquire.ps1'
    derivedFromSha256='ed07186c3d3ba5c3ccaf641a26297c03efec7512ea3a414c858959f6a6690e68'
    derivation='Retained owned child launch/snapshot/timeout helpers; matched R0013 -NoProfile -File flags; replaced R0016 acquisition tests with no-installer Join-Path/Write-Host module-export differential.'
    host=$PSVersionTable.PSVersion.ToString()
    nativeWindows=$NativeWindows
    hostExecutable=$HostExecutable
    installerExecuted=$false
    installerQualified=$false
    source=$SourceFile
    sourceSha256=$SourceHash
    sourceUnchanged=((Hash-File $SourceFile) -ceq $SourceHash)
    testSha256=(Hash-File $PSCommandPath)
    fixture=$FixtureRoot
    results=$observations
    limitations=@('This cannot qualify installer behavior.','The private modules are diagnostic derivatives, not changes to shared tests.','Timeout and missing phases are preparation evidence.','No network calls, tracing, firewall/audit changes, or AppContainer setup are performed.')
}
$json=$report | ConvertTo-Json -Depth 12
Write-FixtureText (Join-Path $FixtureRoot 'diagnostic.json') $json
[Console]::WriteLine($json)
exit 0
