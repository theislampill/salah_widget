#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot,
    [string]$ChildContext
)
# Independent R0015 compiler-custody observer. Derived without replacing the
# native2 original probe SHA1cc468a93f9990015797b5d2ab60edf8e99e70fd56d169cc58f0bbddb1ba7073.
# The old artifact-parent check is a later boundary, not first compiler custody.
# No installer main, transport, browser,
# clipboard, real profile, machine policy, or persistent environment changes.
# Only newly allocated fixture directories receive ACL changes.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$ProbeUtf8 = New-Object Text.UTF8Encoding $false
[Console]::OutputEncoding = $ProbeUtf8
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
    Publish-ProbeText $Path (ConvertTo-Json -InputObject $Value -Depth 22)
}
function Publish-ProbeText([string]$Path, [string]$Text) {
    # Control publications are exclusive and atomic inside the fresh control
    # directory, outside the watched TEMP. A reader cannot see partial JSON.
    $partial=$Path+'.publishing-'+[guid]::NewGuid().ToString('N')
    Write-ProbeText $partial $Text
    [IO.File]::Move($partial,$Path)
}
function Read-ProbeJson([string]$Path) {
    return ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8))
}
function Add-ProbePhase([string]$Name, [string]$Detail='') {
    $row=[ordered]@{phase=$Name;utc=[DateTime]::UtcNow.ToString('o');pid=$PID;nonce=$script:ProbeContext.nonce;detail=$Detail}
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
            $rows.Add([pscustomobject][ordered]@{path=$path.Substring($Root.Length);attributes=[string]$attributes;hash=$(if(-not $directory -and -not $reparse){Get-ProbeHash $path}else{$null});length=$(if(-not $directory -and -not $reparse){[IO.FileInfo]::new($path).Length}else{$null})})
            if($directory -and -not $reparse){$pending.Enqueue($path)}
        }
    }
    return ,@($rows.ToArray() | Sort-Object path)
}
function Get-ProbeStringHash([string]$Text) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return [BitConverter]::ToString($sha.ComputeHash($ProbeUtf8.GetBytes($Text))).Replace('-','').ToLowerInvariant()}
    finally{$sha.Dispose()}
}
function Test-ProbeContainedPath([string]$Path,[string]$Root) {
    return [bool]($Path -and $Root -and ([string]::Equals($Path,$Root,[StringComparison]::OrdinalIgnoreCase) -or $Path.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)))
}
function Get-ProbeCompilerContext {
    $context=$script:CompilerScratch
    if(-not $context){return $null}
    $parents=@($context.Leases|ForEach-Object{[pscustomobject]@{path=$_.Facts.Path;identity=$_.Facts.Identity;owner=$_.Facts.Owner;trustedAncestor=$_.Facts.TrustedAncestor;trustedParent=$_.Facts.TrustedParent;closed=$_.Handle.IsClosed}})
    $root=if($context.RootLease){[ordered]@{path=$context.RootLease.Facts.Path;identity=$context.RootLease.Facts.Identity;owner=$context.RootLease.Facts.Owner;private=$context.RootLease.Facts.Private;closed=$context.RootLease.Handle.IsClosed}}else{$null}
    return [ordered]@{id=$context.Id;status=$context.Status;path=$context.Path;identity=$context.Identity;sid=$context.Sid;defaultOwnerSid=$context.DefaultOwnerSid;invocationStarted=$context.InvocationStarted;compilerExitCode=$context.CompilerExitCode;created=$context.Created;cleanupError=$context.CleanupError;rootLease=$root;parentLeases=$parents;exists=$(if($context.Path){[IO.Directory]::Exists($context.Path)}else{$false})}
}
function Get-ProbeCompilerReadback {
    $context=$script:CompilerScratch
    if(-not $context -or -not $context.Created -or -not $context.Path){return $null}
    $lease=$null;$facts=$null;$snapshot=$null;$aclRows=@();$readbackError=$null
    try {
        $lease=& $script:OriginalProbeCompilerOpen $context.Path $context.Sid ''
        $facts=$lease.Facts
        $snapshot=Get-ProbeSnapshot $context.Path
        $paths=@($context.Path)+@($snapshot|Where-Object{$_.attributes -notmatch 'ReparsePoint'}|ForEach-Object{$context.Path+$_.path})
        foreach($path in $paths){
            $acl=Get-Acl -LiteralPath $path
            $aclRows += [pscustomobject]@{path=$path;owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;protected=$acl.AreAccessRulesProtected;sddl=$acl.Sddl}
        }
    } catch {$readbackError=$_.Exception.Message}
    finally {if($lease){$lease.Handle.Dispose()}}
    return [ordered]@{facts=$facts;snapshot=$snapshot;acl=$aclRows;error=$readbackError}
}
function Wait-ProbeCompilerBoundary([string]$Stage,$Facts) {
    $path=if($Stage -ceq 'before'){$script:ProbeContext.compilerBefore}else{$script:ProbeContext.compilerAfter}
    $ack=if($Stage -ceq 'before'){$script:ProbeContext.compilerBeforeAck}else{$script:ProbeContext.compilerAfterAck}
    Write-ProbeJson $path ([ordered]@{pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;stage=$Stage;utc=[DateTime]::UtcNow.ToString('o');facts=$Facts})
    $clock=[Diagnostics.Stopwatch]::StartNew()
    while(-not [IO.File]::Exists($ack)) {
        if($clock.Elapsed.TotalSeconds -gt 10){throw ('OBSERVER: compiler '+$Stage+' boundary was not released.')}
        [Threading.Thread]::Sleep(25)
    }
    if([IO.File]::ReadAllText($ack) -cne $script:ProbeContext.nonce){throw ('OBSERVER: compiler '+$Stage+' boundary nonce differs.')}
    Add-ProbePhase ('compiler-'+$Stage+'-boundary-released')
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
        $script:CompilerScratch=$null
        $script:ProbeCompilerCalls=@()
        $script:ProbeManagedCompilerCalls=@()
        $script:ProbeObserverErrors=@()
        $script:WorkRoot=$null
        $script:DownloadRoot=$null
        $script:PresetRoot=$null
        $typeAbsent=-not ('SalahInstaller.StageNative' -as [type])
        $compilerTypeAbsent=-not ('SalahInstaller.CompilerNative' -as [type])
        $nativeTemp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
        if(-not $typeAbsent -or -not $compilerTypeAbsent){throw 'BOOTSTRAP: production native type was already loaded.'}
        if(-not $nativeTemp.Equals(([IO.Path]::GetFullPath($script:ProbeContext.temp)).TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)){throw ('BOOTSTRAP: native temp resolution escaped the observed directory: '+$nativeTemp)}
        $script:OriginalProbeTrustedParent=(Get-Command Get-TrustedStagingParent -CommandType Function).ScriptBlock
        $script:OriginalProbeCompilerOpen=(Get-Command Open-CompilerDirectoryLease -CommandType Function).ScriptBlock
        $script:OriginalProbeCompilerContext=(Get-Command New-StagingCompilerContext -CommandType Function).ScriptBlock
        function New-StagingCompilerContext {
            Add-ProbePhase 'compiler-context-enter'
            try {
                $value=& $script:OriginalProbeCompilerContext
                Add-ProbePhase 'compiler-context-owned' $value.Path
                return $value
            } catch {Add-ProbePhase 'compiler-context-threw' $_.Exception.Message;throw}
        }
        $script:ProbeParentCalls=0
        function Get-TrustedStagingParent([string]$Path) {
            $script:ProbeParentCalls++
            Add-ProbePhase 'later-artifact-parent-check-enter' $Path
            try {
                $value=& $script:OriginalProbeTrustedParent $Path
                Add-ProbePhase 'later-artifact-parent-check-returned' $Path
                return $value
            } catch {Add-ProbePhase 'later-artifact-parent-check-threw' $_.Exception.Message;throw}
        }
        # Delegate the actual compiler helper with the exact same context object.
        # Only the named compile-failure control appends invalid input; original
        # and supplied C# hashes are retained at the real invocation boundary.
        function Add-Type {
            [CmdletBinding()]
            param([string]$TypeDefinition,[string[]]$AssemblyName)
            if($AssemblyName){Microsoft.PowerShell.Utility\Add-Type -AssemblyName $AssemblyName;return}
            $call=[pscustomobject]@{sourceSha256=(Get-ProbeStringHash $TypeDefinition);returned=$false;errorId=$null;errorMessage=$null}
            $script:ProbeManagedCompilerCalls += $call
            try{Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -ErrorAction Stop;$call.returned=$true}
            catch{$call.errorId=$_.FullyQualifiedErrorId;$call.errorMessage=$_.Exception.Message;throw}
        }
        $script:OriginalProbeInvokeCompiler=(Get-Command Invoke-StagingCompiler -CommandType Function).ScriptBlock
        function Invoke-StagingCompiler([string]$NativeSource,$Context) {
            Add-ProbePhase 'native-compiler-enter' 'Invoke-StagingCompiler'
            $sameContext=[object]::ReferenceEquals($Context,$script:CompilerScratch)
            if(-not $sameContext){throw 'OBSERVER: actual compiler context object differs.'}
            $injected=$script:ProbeContext.case -ceq 'compile-failure'
            $suppliedSource=if($injected){$NativeSource+"`n deliberately invalid compiler input !"}else{$NativeSource}
            $call=[ordered]@{context=(Get-ProbeCompilerContext);temp=$env:TEMP;tmp=$env:TMP;nativeTemp=[IO.Path]::GetTempPath();originalTypeSha256=(Get-ProbeStringHash $NativeSource);suppliedTypeSha256=(Get-ProbeStringHash $suppliedSource);suppliedFileSha256=(Get-ProbeStringHash (([string][char]0xfeff)+$suppliedSource));failureInjected=$injected;sameContext=$sameContext;actualHelperSha256=(Get-ProbeStringHash $script:OriginalProbeInvokeCompiler.ToString());tokenDefaultOwner=[Security.Principal.WindowsIdentity]::GetCurrent().Owner.Value}
            $script:ProbeCompilerCalls += $call
            try {Wait-ProbeCompilerBoundary 'before' $call}
            catch {$script:ProbeObserverErrors += $_.Exception.Message;throw}
            $nativeError=$null
            try {
                & $script:OriginalProbeInvokeCompiler $suppliedSource $Context
                Add-ProbePhase 'native-compiler-returned' 'Invoke-StagingCompiler'
            } catch {$nativeError=$_;Add-ProbePhase 'native-compiler-threw' $_.Exception.Message}
            $after=[ordered]@{context=(Get-ProbeCompilerContext);readback=(Get-ProbeCompilerReadback);outcome=$(if($nativeError){'threw'}else{'returned'});nativeError=$(if($nativeError){$nativeError.Exception.Message}else{$null});managedCompilerCalls=@($script:ProbeManagedCompilerCalls);nativeTypePresent=[bool]('SalahInstaller.StageNative' -as [type]);temp=$env:TEMP;tmp=$env:TMP;nativeTemp=[IO.Path]::GetTempPath()}
            try {Wait-ProbeCompilerBoundary 'after' $after}
            catch {$script:ProbeObserverErrors += $_.Exception.Message;throw}
            if($nativeError){throw $nativeError}
        }
        $ready=[ordered]@{pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;typeAbsent=$typeAbsent;compilerTypeAbsent=$compilerTypeAbsent;nativeTemp=$nativeTemp;temp=$env:TEMP;tmp=$env:TMP;hostVersion=$PSVersionTable.PSVersion.ToString();hostExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName}
        Write-ProbeJson $script:ProbeContext.ready $ready
        Add-ProbePhase 'observer-ready'
        $wait=[Diagnostics.Stopwatch]::StartNew()
        while(-not [IO.File]::Exists($script:ProbeContext.go)) {
            if($wait.Elapsed.TotalSeconds -gt 60){throw 'OBSERVER: call was not released.'}
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
        $receipt=[ordered]@{status=$(if($script:ProbeObserverErrors.Count){'BOOTSTRAP_OR_OBSERVER_BLOCKED'}else{'OBSERVATION_COMPLETED'});pid=$PID;nonce=$script:ProbeContext.nonce;sourceSha256=$SourceHash;nativeTemp=$nativeTemp;typeAbsentBefore=$typeAbsent;compilerTypeAbsentBefore=$compilerTypeAbsent;typePresentAfter=[bool]('SalahInstaller.StageNative' -as [type]);compilerTypePresentAfter=[bool]('SalahInstaller.CompilerNative' -as [type]);initialized=$initialized;initializationError=$initializationError;parentCheckCalls=$script:ProbeParentCalls;compilerContext=(Get-ProbeCompilerContext);compilerCalls=$script:ProbeCompilerCalls;observerErrors=$script:ProbeObserverErrors;restoredTemp=$env:TEMP;restoredTmp=$env:TMP;beforeCleanup=$beforeCleanup;afterCleanupStatus=$(if($script:StagingAttempt){$script:StagingAttempt.Status}else{$null});cleanupError=$cleanupError}
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
foreach($caseName in @('foreign-create-parent','owned-parent','compile-failure')) {
    $foreign=$caseName -ceq 'foreign-create-parent'
    Set-ProbeAcl $temp $foreign
    $control=Join-Path $script:ProbeFixtureRoot ($caseName+'-control')
    [void][IO.Directory]::CreateDirectory($control);Set-ProbeAcl $control
    $context=[ordered]@{case=$caseName;sourceSha256=$SourceHash;nonce=[guid]::NewGuid().ToString('N');temp=$temp;profile=$profile;control=$control;ready=(Join-Path $control 'ready.json');go=(Join-Path $control 'go.txt');compilerBefore=(Join-Path $control 'compiler-before.json');compilerBeforeAck=(Join-Path $control 'compiler-before-ack.txt');compilerAfter=(Join-Path $control 'compiler-after.json');compilerAfterAck=(Join-Path $control 'compiler-after-ack.txt');receipt=(Join-Path $control 'child-receipt.json');phases=(Join-Path $control 'phases.jsonl')}
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
    $identifiers=@();$watcher=$null;$ready=$null;$receipt=$null;$timedOut=$false;$beforeReleased=$false;$afterReleased=$false;$compilerBefore=$null;$compilerAfter=$null;$observerError=$null;$started=$false;$outTask=$null;$errTask=$null;$stdoutDrained=$false;$stderrDrained=$false
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
        if($ready.pid -ne $child.Id -or $ready.nonce -cne $context.nonce -or $ready.sourceSha256 -cne $SourceHash -or -not $ready.typeAbsent -or -not $ready.compilerTypeAbsent){throw 'BOOTSTRAP: PID/nonce/hash/cold-type readiness differs.'}
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
        Publish-ProbeText $context.go $context.nonce
        $clock.Restart()
        while(-not $child.HasExited -and $clock.Elapsed.TotalSeconds -lt 25) {
            if(-not $beforeReleased -and [IO.File]::Exists($context.compilerBefore)) {
                $compilerBefore=Read-ProbeJson $context.compilerBefore
                if($compilerBefore.pid -ne $child.Id -or $compilerBefore.nonce -cne $context.nonce -or $compilerBefore.sourceSha256 -cne $SourceHash -or $compilerBefore.stage -cne 'before'){throw 'OBSERVER: native compiler before-boundary identity differs.'}
                [Threading.Thread]::Sleep(200)
                Receive-ProbeEvents 'before-native-type-call'
                Publish-ProbeText $context.compilerBeforeAck $context.nonce
                $beforeReleased=$true
            }
            if(-not $afterReleased -and [IO.File]::Exists($context.compilerAfter)) {
                $compilerAfter=Read-ProbeJson $context.compilerAfter
                if(-not $beforeReleased -or $compilerAfter.pid -ne $child.Id -or $compilerAfter.nonce -cne $context.nonce -or $compilerAfter.sourceSha256 -cne $SourceHash -or $compilerAfter.stage -cne 'after'){throw 'OBSERVER: native compiler after-boundary identity differs.'}
                [Threading.Thread]::Sleep(200)
                Receive-ProbeEvents 'during-native-type-call'
                Publish-ProbeText $context.compilerAfterAck $context.nonce
                $afterReleased=$true
            }
            Receive-ProbeEvents $(if($afterReleased){'after-native-type-call'}elseif($beforeReleased){'during-native-type-call'}else{'before-native-type-call'})
            [Threading.Thread]::Sleep(25)
        }
        if(-not $child.HasExited){$timedOut=$true;throw 'OBSERVER: actual call did not terminate within 25 seconds.'}
    } catch {$observerError=$_.Exception.Message}
    finally {
        if($started -and -not $child.HasExited){$timedOut=$true;try{$child.Kill()}catch{};[void]$child.WaitForExit(5000)}
        if($watcher){[Threading.Thread]::Sleep(200);Receive-ProbeEvents 'child-terminal';$watcher.EnableRaisingEvents=$false}
        foreach($identifier in $identifiers){Unregister-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue | Remove-Event -ErrorAction SilentlyContinue}
        if($watcher){$watcher.Dispose()}
    }
    if($outTask){$stdoutDrained=$outTask.Wait(5000)}
    if($errTask){$stderrDrained=$errTask.Wait(5000)}
    $stdout=if($stdoutDrained){$outTask.Result}else{''}
    $stderr=if($stderrDrained){$errTask.Result}else{''}
    if($started -and (-not $stdoutDrained -or -not $stderrDrained)){$observerError='OBSERVER: child stdout/stderr did not drain within the bounded read.'}
    Write-ProbeText (Join-Path $control 'stdout.txt') $stdout
    Write-ProbeText (Join-Path $control 'stderr.txt') $stderr
    if([IO.File]::Exists($context.receipt)){$receipt=Read-ProbeJson $context.receipt}
    $after=$null;$snapshotError=$null
    try{$after=Get-ProbeSnapshot $caseRoot}catch{$snapshotError=$_.Exception.Message}
    $allEvents=@($events.ToArray())
    $productEvents=@($allEvents | Where-Object {-not $_.observerControl -and $_.event -ne 'Error'})
    $compilerEvents=@($productEvents|Where-Object{$_.observedPhase -in @('before-native-type-call','during-native-type-call')})
    $ownedCompilerPath=if($compilerBefore){[string]$compilerBefore.facts.context.path}else{$null}
    $outsideCompilerRoot=@($compilerEvents|Where-Object{-not (Test-ProbeContainedPath $_.path $ownedCompilerPath) -or ($_.oldPath -and -not (Test-ProbeContainedPath $_.oldPath $ownedCompilerPath))})
    $watcherErrors=@($allEvents | Where-Object {$_.event -eq 'Error'})
    $hasCompilerCall=$receipt -and @($receipt.compilerCalls).Count -gt 0
    $boundariesAcquired=if($hasCompilerCall){$beforeReleased -and $afterReleased}else{-not $beforeReleased -and -not $afterReleased}
    $acquired=$null -eq $observerError -and $null -eq $snapshotError -and -not $timedOut -and $null -ne $ready -and $boundariesAcquired -and $watcherErrors.Count -eq 0 -and $receipt -and $receipt.status -ceq 'OBSERVATION_COMPLETED' -and $receipt.pid -eq $child.Id -and $receipt.nonce -ceq $context.nonce -and $receipt.sourceSha256 -ceq $SourceHash -and $stdoutDrained -and $stderrDrained
    $environmentRestored=$receipt -and $receipt.restoredTemp -ceq $temp -and $receipt.restoredTmp -ceq $temp
    $guardObserved=$acquired -and -not $receipt.initialized -and -not $hasCompilerCall -and -not $receipt.typePresentAfter -and $receipt.compilerContext.status -ceq 'refused-before-create' -and -not $receipt.compilerContext.created -and $receipt.initializationError -ceq 'Compiler parent is not owned by this user with trusted write access.' -and $receipt.parentCheckCalls -eq 0 -and $environmentRestored
    $custodyObserved=$false
    if($hasCompilerCall -and $compilerBefore){
        $facts=$compilerBefore.facts;$owned=$facts.context;$lease=$owned.rootLease
        $custodyObserved=$owned.created -and $owned.status -ceq 'compiling' -and $owned.identity -and $lease.identity -ceq $owned.identity -and $lease.owner -ceq $owned.sid -and $owned.sid -ceq $script:ProbeSid.Value -and $lease.private -and -not $lease.closed -and @($owned.parentLeases).Count -gt 0 -and @($owned.parentLeases|Where-Object{$_.closed -or -not $_.trustedAncestor -or -not $_.identity}).Count -eq 0 -and $owned.parentLeases[-1].trustedParent -and $owned.parentLeases[-1].path.TrimEnd('\') -ceq $temp.TrimEnd('\') -and $owned.path -ceq ($temp+'\SalahWidgetCompiler-'+$owned.id) -and $facts.temp -ceq $owned.path -and $facts.tmp -ceq $owned.path -and $facts.nativeTemp.TrimEnd('\') -ceq $owned.path.TrimEnd('\')
        $custodyObserved=$custodyObserved -and $facts.sameContext -and $facts.actualHelperSha256 -and $owned.defaultOwnerSid -ceq $facts.tokenDefaultOwner
    }
    $readbackObserved=$compilerAfter -and -not $compilerAfter.facts.readback.error -and $compilerAfter.facts.readback.facts.Private -and $compilerAfter.facts.readback.facts.Identity -ceq $receipt.compilerContext.identity -and $compilerAfter.facts.readback.facts.Owner -ceq $script:ProbeSid.Value
    $healthyObserved=$acquired -and $custodyObserved -and $readbackObserved -and $environmentRestored -and $receipt.initialized -and $receipt.parentCheckCalls -eq 2 -and $receipt.afterCleanupStatus -ceq 'closed' -and -not $receipt.cleanupError -and $receipt.compilerContext.status -ceq 'closed' -and -not $receipt.compilerContext.exists -and $compilerAfter.facts.outcome -ceq 'returned' -and $compilerAfter.facts.nativeTypePresent -and -not $compilerBefore.facts.failureInjected -and $compilerBefore.facts.originalTypeSha256 -ceq $compilerBefore.facts.suppliedTypeSha256
    if($PSVersionTable.PSVersion.Major -eq 5){$healthyObserved=$healthyObserved -and $compilerAfter.facts.context.invocationStarted -and $compilerAfter.facts.context.compilerExitCode -eq 0}
    $actualCompilerFailure=$false
    if($compilerAfter -and $compilerBefore){
        if($PSVersionTable.PSVersion.Major -eq 5){
            $sourceRows=@($compilerAfter.facts.readback.snapshot|Where-Object{$_.path -ceq '\native.cs'})
            $diagnosticRows=@($compilerAfter.facts.readback.snapshot|Where-Object{$_.path -cin @('\compiler.stdout.bin','\compiler.stderr.bin')})
            $actualCompilerFailure=$null -ne $compilerAfter.facts.context.compilerExitCode -and $compilerAfter.facts.context.compilerExitCode -ne 0 -and $sourceRows.Count -eq 1 -and $sourceRows[0].hash -ceq $compilerBefore.facts.suppliedFileSha256 -and $diagnosticRows.Count -eq 2 -and ($diagnosticRows|Measure-Object -Property length -Sum).Sum -gt 0
        }else{
            $managed=@($compilerAfter.facts.managedCompilerCalls)
            $actualCompilerFailure=$managed.Count -eq 1 -and -not $managed[0].returned -and $managed[0].errorId -ceq 'SOURCE_CODE_ERROR,Microsoft.PowerShell.Commands.AddTypeCommand' -and $managed[0].sourceSha256 -ceq $compilerBefore.facts.suppliedTypeSha256
        }
    }
    $failureObserved=$acquired -and $custodyObserved -and $readbackObserved -and $environmentRestored -and $actualCompilerFailure -and -not $receipt.initialized -and $receipt.parentCheckCalls -eq 0 -and -not $receipt.typePresentAfter -and $receipt.initializationError -and $receipt.compilerContext.status -ceq 'retained-compilation-failed' -and $receipt.compilerContext.exists -and $compilerAfter.facts.outcome -ceq 'threw' -and $compilerBefore.facts.failureInjected
    $status=if(-not $acquired){'BOOTSTRAP_OR_OBSERVER_BLOCKED'}elseif($foreign -and -not $guardObserved){'UNEXPECTED_PARENT_BEHAVIOR'}elseif($foreign -and $productEvents.Count){'OBSERVED_UNSAFE_PARENT_TEMP_EFFECTS'}elseif($foreign){'UNSAFE_PARENT_REFUSED_WITH_NO_OBSERVED_TEMP_EFFECTS'}elseif($outsideCompilerRoot.Count){'OBSERVED_COMPILER_EFFECTS_OUTSIDE_OWNED_ROOT'}elseif($caseName -ceq 'compile-failure' -and $failureObserved){'COMPILER_FAILURE_RETAINED_PRIVATE_OUTPUT'}elseif($caseName -ceq 'compile-failure'){'UNEXPECTED_COMPILER_FAILURE_BEHAVIOR'}elseif($healthyObserved){'HEALTHY_PRIVATE_COMPILER_AND_STAGING_OBSERVED'}else{'HEALTHY_CONTROL_FAILED'}
    $row=[pscustomobject][ordered]@{case=$caseName;status=$status;acquired=[bool]$acquired;installerQualified=$false;guardObserved=[bool]$guardObserved;compilerCustodyObserved=[bool]$custodyObserved;healthyObserved=[bool]$healthyObserved;compileFailureObserved=[bool]$failureObserved;environmentRestored=[bool]$environmentRestored;fixture=$caseRoot;control=$control;pid=$(if($started){$child.Id}else{$null});exit=$(if($started -and $child.HasExited){$child.ExitCode}else{$null});timedOut=$timedOut;observerError=$observerError;snapshotError=$snapshotError;stdoutDrained=$stdoutDrained;stderrDrained=$stderrDrained;sourceSha256=$SourceHash;probeSha256=$ProbeHash;acl=$aclFacts;readiness=$ready;compilerBeforeReleased=$beforeReleased;compilerAfterReleased=$afterReleased;compilerBefore=$compilerBefore;compilerAfter=$compilerAfter;childReceipt=$receipt;events=$allEvents;compilerPeriodEvents=$compilerEvents;compilerOutsideOwnedRootEvents=$outsideCompilerRoot;before=$before;after=$after;stdout=$stdout;stderr=$stderr}
    Write-ProbeJson (Join-Path $control 'observation.json') $row
    $results.Add($row)
    $child.Dispose()
}
$summary=[ordered]@{schema='r0015-independent-native-compiler-custody-observation-v3';sourceFile=$SourceFile;sourceSha256=$SourceHash;probeSha256=$ProbeHash;originalProbeSha256='1cc468a93f9990015797b5d2ab60edf8e99e70fd56d169cc58f0bbddb1ba7073';fixture=$script:ProbeFixtureRoot;hostExecutable=$HostExecutable;hostVersion=$PSVersionTable.PSVersion.ToString();subjectSid=$script:ProbeSid.Value;actualWindows=$true;installerQualified=$false;complete=(@($results.ToArray() | Where-Object {-not $_.acquired}).Count -eq 0);scope='Actual cold Initialize-Staging and compiler custody. The actual Invoke-StagingCompiler helper is delegated with the same context reference; source/helper hashes and token default owner are recorded. PS5.1 healthy admission also requires observed direct compiler invocation and exit0. Only the named compile-failure row appends declared invalid C# input; both hashes are recorded. Failure credit requires an actual nonzero Framework compiler result with retained input/diagnostics, or the actual delegated PS7 Add-Type syntax diagnostic. Compiler calls pause before and after for event drain while custody leases remain held. Later artifact-parent checks are separately observed. Whole verified TEMP/TMP is watched; this is not a global process trace. Acquired observations, including adverse findings, require independent adjudication and do not imply installer qualification.';results=@($results.ToArray())}
Write-ProbeJson (Join-Path $script:ProbeFixtureRoot 'summary.json') $summary
[Console]::Out.WriteLine((ConvertTo-Json -InputObject $summary -Depth 22))
if(-not $summary.complete){exit 2}
exit 0
