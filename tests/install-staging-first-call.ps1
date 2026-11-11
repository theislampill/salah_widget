#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot,
    [string]$ChildContext
)
# Independent R0015 observation probe. No installer main, transport, browser,
# clipboard, real profile, machine policy, or persistent environment changes.
# Only newly allocated fixture directories receive ACL changes.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$ProbeUtf8 = New-Object Text.UTF8Encoding $false
$NativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT

function Write-ProbeText([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, $ProbeUtf8)
}
function Get-ProbeHash([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($Path)))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Write-ProbeJson([string]$Path, $Value) {
    Write-ProbeText $Path (ConvertTo-Json -InputObject $Value -Depth 18)
}
function Read-ProbeJson([string]$Path) {
    return ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8))
}
function Add-ProbePhase([string]$Name, [string]$Detail='') {
    $row=[ordered]@{phase=$Name;utc=[DateTime]::UtcNow.ToString('o');pid=$PID;detail=$Detail}
    [IO.File]::AppendAllText($script:ProbeContext.phases, ((ConvertTo-Json -InputObject $row -Compress)+[Environment]::NewLine), $ProbeUtf8)
}
function Get-ProbeSnapshot([string]$Root) {
    $rows=New-Object 'System.Collections.Generic.List[object]'
    $pending=New-Object 'System.Collections.Generic.Queue[string]'
    $pending.Enqueue($Root)
    while($pending.Count) {
        $parent=$pending.Dequeue()
        foreach($path in [IO.Directory]::EnumerateFileSystemEntries($parent)) {
            $attributes=[IO.File]::GetAttributes($path)
            $directory=($attributes -band [IO.FileAttributes]::Directory) -ne 0
            $reparse=($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
            $rows.Add([pscustomobject][ordered]@{path=$path.Substring($Root.Length);attributes=[string]$attributes;hash=$(if(-not $directory -and -not $reparse){Get-ProbeHash $path}else{$null})})
            if($directory -and -not $reparse){$pending.Enqueue($path)}
        }
    }
    return ,@($rows.ToArray() | Sort-Object path)
}

if(-not $NativeWindows) {
    [Console]::Out.WriteLine((ConvertTo-Json -Compress -InputObject ([ordered]@{status='BLOCKED_NATIVE_HOST';complete=$false;reason='This first-call observer requires an actual Windows host. No POSIX compiler or ACL result is substituted.'})))
    exit 2
}
if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -eq 'S-1-5-18') {
    [Console]::Out.WriteLine((ConvertTo-Json -Compress -InputObject ([ordered]@{status='BLOCKED_SYSTEM_IDENTITY';complete=$false;reason='SYSTEM GetTempPath2 may select a global SystemTemp path; this bounded probe refuses that identity.'})))
    exit 2
}
$SourceFile=[IO.Path]::GetFullPath($SourceFile)
$SourceHash=Get-ProbeHash $SourceFile

if($ChildContext) {
    $script:ProbeContext=Read-ProbeJson ([IO.Path]::GetFullPath($ChildContext))
    Add-ProbePhase 'child-script-enter'
    try {
        if($SourceHash -cne $script:ProbeContext.sourceSha256){throw 'BOOTSTRAP: source hash differs from the parent observation context.'}
        $raw=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
        $tokens=$null; $parseErrors=$null
        $ast=[Management.Automation.Language.Parser]::ParseInput($raw,[ref]$tokens,[ref]$parseErrors)
        if(@($parseErrors).Count){throw 'BOOTSTRAP: production source did not parse.'}
        foreach($definition in $ast.EndBlock.Statements) {
            if($definition -is [Management.Automation.Language.FunctionDefinitionAst]) {
                . ([scriptblock]::Create($definition.Extent.Text))
            }
        }
        $script:DryRun=$false
        $script:StagingAttempt=$null
        $script:WorkRoot=$null
        $script:DownloadRoot=$null
        $script:PresetRoot=$null
        $typeAbsent=-not ('SalahInstaller.StageNative' -as [type])
        $nativeTemp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
        if(-not $typeAbsent){throw 'BOOTSTRAP: production native type was already loaded.'}
        if(-not $nativeTemp.Equals(([IO.Path]::GetFullPath($script:ProbeContext.temp)).TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)){throw ('BOOTSTRAP: native temp resolution escaped the observed directory: '+$nativeTemp)}
        $script:OriginalProbeTrustedParent=(Get-Command Get-TrustedStagingParent -CommandType Function).ScriptBlock
        $script:ProbeParentCalls=0
        function Get-TrustedStagingParent([string]$Path) {
            $script:ProbeParentCalls++
            Add-ProbePhase 'native-parent-check-enter' $Path
            if($script:ProbeParentCalls -eq 1) {
                Write-ProbeJson $script:ProbeContext.boundary ([ordered]@{pid=$PID;nonce=$script:ProbeContext.nonce;path=$Path;utc=[DateTime]::UtcNow.ToString('o')})
                $wait=[Diagnostics.Stopwatch]::StartNew()
                while(-not [IO.File]::Exists($script:ProbeContext.boundaryAck)) {
                    if($wait.Elapsed.TotalSeconds -gt 10){throw 'OBSERVER: first native parent check was not released.'}
                    [Threading.Thread]::Sleep(25)
                }
                if([IO.File]::ReadAllText($script:ProbeContext.boundaryAck) -cne $script:ProbeContext.nonce){throw 'OBSERVER: first parent check acknowledgement nonce differs.'}
                Add-ProbePhase 'native-parent-check-released' $Path
            }
            try {
                $value=& $script:OriginalProbeTrustedParent $Path
                Add-ProbePhase 'native-parent-check-returned' $Path
                return $value
            } catch {Add-ProbePhase 'native-parent-check-threw' $_.Exception.Message;throw}
        }
        # These are the exact two Add-Type parameter sets used by this source.
        # The production compiler/type text and native cmdlet are unchanged.
        function Add-Type {
            [CmdletBinding(DefaultParameterSetName='Type')]
            param(
                [Parameter(Mandatory=$true,ParameterSetName='Type')][string]$TypeDefinition,
                [Parameter(Mandatory=$true,ParameterSetName='Assembly')][string[]]$AssemblyName
            )
            Add-ProbePhase 'native-add-type-enter' $PSCmdlet.ParameterSetName
            try {
                Microsoft.PowerShell.Utility\Add-Type @PSBoundParameters
                Add-ProbePhase 'native-add-type-returned' $PSCmdlet.ParameterSetName
            } catch {Add-ProbePhase 'native-add-type-threw' $_.Exception.Message;throw}
        }
        $ready=[ordered]@{pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;typeAbsent=$typeAbsent;nativeTemp=$nativeTemp;temp=$env:TEMP;tmp=$env:TMP;hostVersion=$PSVersionTable.PSVersion.ToString();hostExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName}
        Write-ProbeJson $script:ProbeContext.ready $ready
        Add-ProbePhase 'observer-ready'
        $wait=[Diagnostics.Stopwatch]::StartNew()
        while(-not [IO.File]::Exists($script:ProbeContext.go)) {
            if($wait.Elapsed.TotalSeconds -gt 15){throw 'OBSERVER: call was not released.'}
            [Threading.Thread]::Sleep(25)
        }
        if([IO.File]::ReadAllText($script:ProbeContext.go) -cne $script:ProbeContext.nonce){throw 'OBSERVER: call release nonce differs.'}
        $initialized=$false; $initializationError=$null; $cleanupError=$null
        Add-ProbePhase 'actual-initialize-staging-enter'
        try {Initialize-Staging;$initialized=$true;Add-ProbePhase 'actual-initialize-staging-returned'}
        catch {$initializationError=$_.Exception.Message;Add-ProbePhase 'actual-initialize-staging-threw' $initializationError}
        $beforeCleanup=if($script:StagingAttempt){[ordered]@{id=$script:StagingAttempt.Id;status=$script:StagingAttempt.Status;scratchPath=$(if($script:StagingAttempt.Scratch){$script:StagingAttempt.Scratch.Path}else{$null});retainedPath=$(if($script:StagingAttempt.Retained){$script:StagingAttempt.Retained.Path}else{$null})}}else{$null}
        if($initialized) {
            try {Clear-OwnedScratch;Add-ProbePhase 'actual-clear-owned-scratch-returned'}
            catch {$cleanupError=$_.Exception.Message;Add-ProbePhase 'actual-clear-owned-scratch-threw' $cleanupError}
        }
        $receipt=[ordered]@{status='OBSERVATION_COMPLETED';pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;nativeTemp=$nativeTemp;typeAbsentBefore=$typeAbsent;typePresentAfter=[bool]('SalahInstaller.StageNative' -as [type]);initialized=$initialized;initializationError=$initializationError;parentCheckCalls=$script:ProbeParentCalls;beforeCleanup=$beforeCleanup;afterCleanupStatus=$(if($script:StagingAttempt){$script:StagingAttempt.Status}else{$null});cleanupError=$cleanupError}
        Write-ProbeJson $script:ProbeContext.receipt $receipt
        Add-ProbePhase 'child-completed'
        exit 0
    } catch {
        Add-ProbePhase 'child-failed' $_.Exception.Message
        Write-ProbeJson $script:ProbeContext.receipt ([ordered]@{status='BOOTSTRAP_OR_OBSERVER_BLOCKED';pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;error=$_.Exception.Message})
        exit 2
    }
}

if(-not $OutputRoot){throw 'Supply an existing disposable OutputRoot on the native host.'}
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
if(-not [IO.Directory]::Exists($OutputRoot) -or (([IO.File]::GetAttributes($OutputRoot) -band [IO.FileAttributes]::ReparsePoint) -ne 0)){throw 'OutputRoot must be an existing real directory.'}
$script:ProbeFixtureRoot=Join-Path $OutputRoot ('r0015-first-call-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($script:ProbeFixtureRoot)
$script:ProbeSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
$HostExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$NativeModules=Join-Path $PSHOME 'Modules'
$ProbePath=[IO.Path]::GetFullPath($PSCommandPath)
$ProbeHash=Get-ProbeHash $ProbePath
function Set-ProbeAcl([string]$Path,[bool]$ForeignCreation=$false) {
    $full=[IO.Path]::GetFullPath($Path)
    if($full -cne $script:ProbeFixtureRoot -and -not $full.StartsWith($script:ProbeFixtureRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'ACL target escaped the new probe fixture.'}
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($script:ProbeSid);$acl.SetAccessRuleProtection($true,$false)
    $rule=New-Object Security.AccessControl.FileSystemAccessRule($script:ProbeSid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
    $acl.AddAccessRule($rule)
    if($ForeignCreation) {
        $everyone=New-Object Security.Principal.SecurityIdentifier 'S-1-1-0'
        $rights=[Security.AccessControl.FileSystemRights]::CreateFiles -bor [Security.AccessControl.FileSystemRights]::CreateDirectories
        $rule=New-Object Security.AccessControl.FileSystemAccessRule($everyone,$rights,[Security.AccessControl.InheritanceFlags]::None,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
Set-ProbeAcl $script:ProbeFixtureRoot
$results=New-Object 'System.Collections.Generic.List[object]'
$caseRoot=Join-Path $script:ProbeFixtureRoot 'matched-parent'
$temp=Join-Path $caseRoot 'temp'
$profile=Join-Path $caseRoot 'profile'
foreach($path in @($caseRoot,$temp,$profile)){[void][IO.Directory]::CreateDirectory($path);Set-ProbeAcl $path}
foreach($caseName in @('foreign-create-parent','owned-parent')) {
    $foreign=$caseName -ceq 'foreign-create-parent'
    Set-ProbeAcl $temp $foreign
    $control=Join-Path $script:ProbeFixtureRoot ($caseName+'-control')
    [void][IO.Directory]::CreateDirectory($control);Set-ProbeAcl $control
    $context=[ordered]@{sourceSha256=$SourceHash;nonce=[guid]::NewGuid().ToString('N');temp=$temp;profile=$profile;control=$control;ready=(Join-Path $control 'ready.json');go=(Join-Path $control 'go.txt');boundary=(Join-Path $control 'boundary.json');boundaryAck=(Join-Path $control 'boundary-ack.txt');receipt=(Join-Path $control 'child-receipt.json');phases=(Join-Path $control 'phases.jsonl')}
    $contextFile=Join-Path $control 'context.json';Write-ProbeJson $contextFile $context
    $acl=Get-Acl -LiteralPath $temp
    $aclFacts=[ordered]@{path=$temp;ownerSid=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;protected=$acl.AreAccessRulesProtected;sddl=$acl.Sddl;foreignCreateGrant=$foreign}
    $psi=New-Object Diagnostics.ProcessStartInfo
    $psi.FileName=$HostExecutable
    $psi.Arguments='-NoLogo -NoProfile -NonInteractive -File "'+$ProbePath+'" -SourceFile "'+$SourceFile+'" -ChildContext "'+$contextFile+'"'
    $psi.WorkingDirectory=$control;$psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    $environment=[ordered]@{TEMP=$temp;TMP=$temp;USERPROFILE=$profile;HOME=$profile;APPDATA=(Join-Path $profile 'AppData\Roaming');LOCALAPPDATA=(Join-Path $profile 'AppData\Local');PSModulePath=$NativeModules;PSModuleAnalysisCachePath=(Join-Path $control 'module-analysis-cache');POWERSHELL_TELEMETRY_OPTOUT='1';DOTNET_EnableDiagnostics='0';DOTNET_CLI_TELEMETRY_OPTOUT='1';DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1';DOTNET_CLI_HOME=$control}
    foreach($name in @('APPDATA','LOCALAPPDATA')){[void][IO.Directory]::CreateDirectory($environment[$name])}
    $before=Get-ProbeSnapshot $caseRoot
    foreach($key in @($psi.EnvironmentVariables.Keys)){if(@($environment.Keys) -contains [string]$key){$psi.EnvironmentVariables.Remove([string]$key)}}
    foreach($key in $environment.Keys){$psi.EnvironmentVariables[[string]$key]=[string]$environment[$key]}
    $child=New-Object Diagnostics.Process;$child.StartInfo=$psi
    $events=New-Object 'System.Collections.Generic.List[object]'
    $identifiers=@();$watcher=$null;$ready=$null;$receipt=$null;$timedOut=$false;$boundaryReleased=$false;$observerError=$null;$started=$false;$outTask=$null;$errTask=$null
    $marker=Join-Path $temp ('observer-control-'+$context.nonce+'.txt')
    function Receive-ProbeEvents([string]$Phase) {
        foreach($identifier in $identifiers) {
            foreach($event in @(Get-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue)) {
                $args=$event.SourceEventArgs
                $isError=$identifier.EndsWith('-Error')
                $events.Add([pscustomobject][ordered]@{observedPhase=$Phase;event=$identifier.Substring($identifier.LastIndexOf('-')+1);utc=$event.TimeGenerated.ToUniversalTime().ToString('o');path=$(if(-not $isError){$args.FullPath}else{$null});oldPath=$(if($identifier.EndsWith('-Renamed')){$args.OldFullPath}else{$null});error=$(if($isError){$args.GetException().ToString()}else{$null});observerControl=$(if(-not $isError){$args.FullPath -ceq $marker}else{$false})})
                Remove-Event -EventIdentifier $event.EventIdentifier
            }
        }
    }
    try {
        [void]$child.Start();$started=$true;$child.StandardInput.Close()
        $outTask=$child.StandardOutput.ReadToEndAsync();$errTask=$child.StandardError.ReadToEndAsync()
        $clock=[Diagnostics.Stopwatch]::StartNew()
        # Native PS5.1 owned-profile cold startup took 19.615-22.770 seconds
        # in the preserved R0013 run4. This budget covers observer acquisition;
        # the separate actual Initialize-Staging window below stays 25 seconds.
        while(-not [IO.File]::Exists($context.ready) -and -not $child.HasExited -and $clock.Elapsed.TotalSeconds -lt 60){[Threading.Thread]::Sleep(25)}
        if(-not [IO.File]::Exists($context.ready)){throw 'BOOTSTRAP: fresh child did not produce observer-ready within 60 seconds.'}
        $ready=Read-ProbeJson $context.ready
        if($ready.pid -ne $child.Id -or $ready.nonce -cne $context.nonce -or $ready.sourceSha256 -cne $SourceHash -or -not $ready.typeAbsent){throw 'BOOTSTRAP: PID/nonce/hash/cold-type readiness differs.'}
        $watcher=New-Object IO.FileSystemWatcher $temp
        $watcher.IncludeSubdirectories=$true;$watcher.InternalBufferSize=65536
        $watcher.NotifyFilter=[IO.NotifyFilters]'FileName,DirectoryName,LastWrite,Size,CreationTime'
        foreach($eventName in @('Created','Changed','Deleted','Renamed','Error')) {
            $identifier=$context.nonce+'-'+$eventName;$identifiers+=$identifier
            Register-ObjectEvent -InputObject $watcher -EventName $eventName -SourceIdentifier $identifier | Out-Null
        }
        $watcher.EnableRaisingEvents=$true
        Write-ProbeText $marker 'known observer creation and deletion'
        [IO.File]::Delete($marker)
        $clock.Restart()
        do {
            [Threading.Thread]::Sleep(25);Receive-ProbeEvents 'observer-control'
            $created=@($events.ToArray() | Where-Object {$_.observerControl -and $_.event -eq 'Created'}).Count
            $deleted=@($events.ToArray() | Where-Object {$_.observerControl -and $_.event -eq 'Deleted'}).Count
        } while((-not $created -or -not $deleted) -and $clock.Elapsed.TotalSeconds -lt 2)
        if(-not $created -or -not $deleted){throw 'OBSERVER: known create/delete control was not acquired.'}
        Write-ProbeText $context.go $context.nonce
        $clock.Restart()
        while(-not $child.HasExited -and $clock.Elapsed.TotalSeconds -lt 25) {
            if(-not $boundaryReleased -and [IO.File]::Exists($context.boundary)) {
                $boundary=Read-ProbeJson $context.boundary
                if($boundary.pid -ne $child.Id -or $boundary.nonce -cne $context.nonce -or $boundary.path -cne $temp){throw 'OBSERVER: first native parent-check boundary differs.'}
                [Threading.Thread]::Sleep(200)
                Receive-ProbeEvents 'before-first-native-parent-check'
                Write-ProbeText $context.boundaryAck $context.nonce
                $boundaryReleased=$true
            }
            Receive-ProbeEvents $(if($boundaryReleased){'after-first-parent-check-release'}else{'before-first-native-parent-check'})
            [Threading.Thread]::Sleep(25)
        }
        if(-not $child.HasExited){$timedOut=$true;throw 'OBSERVER: actual call did not terminate within 25 seconds.'}
    } catch {$observerError=$_.Exception.Message}
    finally {
        if($started -and -not $child.HasExited){$timedOut=$true;$child.Kill();$child.WaitForExit()}
        if($watcher){[Threading.Thread]::Sleep(200);Receive-ProbeEvents 'child-terminal';$watcher.EnableRaisingEvents=$false}
        foreach($identifier in $identifiers){Unregister-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue | Remove-Event -ErrorAction SilentlyContinue}
        if($watcher){$watcher.Dispose()}
    }
    $stdout=if($outTask){$outTask.GetAwaiter().GetResult()}else{''}
    $stderr=if($errTask){$errTask.GetAwaiter().GetResult()}else{''}
    Write-ProbeText (Join-Path $control 'stdout.txt') $stdout
    Write-ProbeText (Join-Path $control 'stderr.txt') $stderr
    if([IO.File]::Exists($context.receipt)){$receipt=Read-ProbeJson $context.receipt}
    $after=Get-ProbeSnapshot $caseRoot
    $allEvents=@($events.ToArray())
    $productEvents=@($allEvents | Where-Object {-not $_.observerControl})
    $preAdmissionEvents=@($productEvents | Where-Object {$_.observedPhase -ceq 'before-first-native-parent-check'})
    $watcherErrors=@($allEvents | Where-Object {$_.event -eq 'Error'})
    $acquired=$null -eq $observerError -and -not $timedOut -and $null -ne $ready -and $boundaryReleased -and $watcherErrors.Count -eq 0 -and $receipt -and $receipt.status -ceq 'OBSERVATION_COMPLETED' -and $receipt.pid -eq $child.Id -and $receipt.nonce -ceq $context.nonce
    $guardObserved=$acquired -and -not $receipt.initialized -and $receipt.initializationError -ceq 'Staging parent is not owned by this user with trusted write access.' -and $receipt.parentCheckCalls -eq 1
    $healthyObserved=$acquired -and $receipt.initialized -and $receipt.afterCleanupStatus -ceq 'closed' -and -not $receipt.cleanupError
    $status=if(-not $acquired){'BOOTSTRAP_OR_OBSERVER_BLOCKED'}elseif($foreign -and -not $guardObserved){'UNEXPECTED_PARENT_BEHAVIOR'}elseif(-not $foreign -and -not $healthyObserved){'HEALTHY_CONTROL_FAILED'}elseif($foreign -and $preAdmissionEvents.Count){'OBSERVED_PRE_ADMISSION_TEMP_EFFECTS'}elseif($foreign){'NO_OBSERVED_PRE_ADMISSION_TEMP_EFFECTS'}else{'HEALTHY_INITIALIZATION_OBSERVED'}
    $row=[pscustomobject][ordered]@{case=$caseName;status=$status;acquired=[bool]$acquired;guardObserved=[bool]$guardObserved;healthyObserved=[bool]$healthyObserved;fixture=$caseRoot;control=$control;pid=$(if($started){$child.Id}else{$null});exit=$(if($started){$child.ExitCode}else{$null});timedOut=$timedOut;observerError=$observerError;sourceSha256=$SourceHash;probeSha256=$ProbeHash;acl=$aclFacts;readiness=$ready;boundaryReleased=$boundaryReleased;childReceipt=$receipt;events=$allEvents;preAdmissionEvents=$preAdmissionEvents;before=$before;after=$after;stdout=$stdout;stderr=$stderr}
    Write-ProbeJson (Join-Path $control 'observation.json') $row
    $results.Add($row)
    $child.Dispose()
}
$summary=[ordered]@{schema='r0015-independent-native-first-call-observation-v1';sourceFile=$SourceFile;sourceSha256=$SourceHash;probeSha256=$ProbeHash;fixture=$script:ProbeFixtureRoot;hostExecutable=$HostExecutable;hostVersion=$PSVersionTable.PSVersion.ToString();subjectSid=$script:ProbeSid.Value;actualWindows=$true;complete=(@($results.ToArray() | Where-Object {-not $_.acquired}).Count -eq 0);scope='Actual Initialize-Staging with exact source functions; native Add-Type delegated unchanged; first parent check delayed for event drain. No installer main or transport. Watcher covers only verified TEMP/TMP, not every possible process file effect. A missing event is not global proof of no writes.';results=@($results.ToArray())}
Write-ProbeJson (Join-Path $script:ProbeFixtureRoot 'summary.json') $summary
[Console]::Out.WriteLine((ConvertTo-Json -InputObject $summary -Depth 18))
if(-not $summary.complete){exit 2}
exit 0
