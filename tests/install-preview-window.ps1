# Definition-only support for the versioned helper/wrapper invocation window.
# The caller owns containment. This protocol does not create an OS sandbox.
function Get-PreviewFileFact([string]$Path){
    $bytes=[IO.File]::ReadAllBytes($Path);$sha=[Security.Cryptography.SHA256]::Create()
    try{$digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    return [pscustomobject]@{path=$Path;sha256=$digest;bytes=$bytes.Length}
}
function Write-PreviewJson([string]$Path,$Value){
    [IO.File]::WriteAllText($Path,(ConvertTo-Json -InputObject $Value -Depth 12),(New-Object Text.UTF8Encoding $false))
}
function Snapshot-Subject([string]$Path){
    $rows=New-Object 'System.Collections.Generic.List[object]'
    foreach($item in @(Get-Item -LiteralPath $Path -Force -ErrorAction Stop)+@(Get-ChildItem -LiteralPath $Path -Force -Recurse -ErrorAction Stop|Sort-Object FullName)){
        $item.Refresh();$link=($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        $stamp=$item.LastWriteTimeUtc.Ticks;$attributes=[string]$item.Attributes;$sddl=$null
        if([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT){
            $security=Get-Acl -LiteralPath $item.FullName -ErrorAction Stop
            $sections=[Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group -bor [Security.AccessControl.AccessControlSections]::Access
            $sddl=$security.GetSecurityDescriptorSddlForm($sections)
        }
        $fact=if(-not $item.PSIsContainer -and -not $link){Get-PreviewFileFact $item.FullName}else{$null}
        $item.Refresh()
        if($item.LastWriteTimeUtc.Ticks -ne $stamp -or [string]$item.Attributes -cne $attributes -or ($fact -and $item.Length -ne $fact.bytes)){throw 'BOOTSTRAP: subject changed while being inventoried'}
        $rows.Add([pscustomobject]@{
            path=$item.FullName.Substring($Path.Length).Replace('\','/');attributes=$attributes
            hash=if($fact){$fact.sha256}else{$null};lastWriteUtc=$stamp;sddl=$sddl
            linkTarget=if($link){[string]$item.Target}else{$null};bytes=if($fact){$fact.bytes}else{$null}
        })
    }
    return $rows.ToArray()
}
function Save-PreviewInventory([string]$Subject,[string]$Path){
    $started=[DateTime]::UtcNow.ToString('o')
    $first=@(Snapshot-Subject $Subject);$second=@(Snapshot-Subject $Subject)
    $agree=(ConvertTo-Json -InputObject $first -Depth 8 -Compress) -ceq (ConvertTo-Json -InputObject $second -Depth 8 -Compress)
    $value=[pscustomobject]@{schema='r0016-preview-double-inventory.v1';root=$Subject;startedUtc=$started;completedUtc=[DateTime]::UtcNow.ToString('o');complete=$agree;passesAgree=$agree;passes=@($first,$second);rows=$second}
    Write-PreviewJson $Path $value
    if(-not $agree){throw 'BOOTSTRAP: consecutive full inventories disagree'}
    return $value
}
function Wait-PreviewInvocationGate($Spec,[ValidateSet('before','after')][string]$Phase){
    $signal=[string]$Spec.($Phase+'Signal');$ack=[string]$Spec.($Phase+'Ack')
    $token=[string]$PID+"`t"+$Spec.nonce+"`t"+$Phase+'-invocation'
    if([IO.File]::Exists($signal) -or [IO.File]::Exists($signal+'.partial') -or [IO.File]::Exists($ack)){throw 'BOOTSTRAP: phase control path already occupied'}
    [IO.File]::WriteAllText($signal+'.partial',$token,(New-Object Text.UTF8Encoding $false))
    [IO.File]::Move($signal+'.partial',$signal)
    $clock=[Diagnostics.Stopwatch]::StartNew()
    while(-not [IO.File]::Exists($ack)){
        if($clock.Elapsed.TotalSeconds -ge 20){throw 'BOOTSTRAP: phase acknowledgement deadline expired'}
        [Threading.Thread]::Sleep(20)
    }
    $observedAck=[IO.File]::ReadAllText($ack)
    if($clock.Elapsed.TotalSeconds -ge 20){throw 'BOOTSTRAP: phase acknowledgement first observed after deadline'}
    if($observedAck -cne $token){throw 'BOOTSTRAP: phase acknowledgement identity mismatch'}
}
function Invoke-PreviewWindowChild($Context,[string]$File,[string]$Label,$Spec){
    $budget=60
    if($env:SALAH_TEST_CHILD_TIMEOUT_SECONDS){
        $requested=0
        if(-not [int]::TryParse($env:SALAH_TEST_CHILD_TIMEOUT_SECONDS,[ref]$requested) -or $requested -lt 30 -or $requested -gt 180){throw 'BOOTSTRAP: invalid child timeout budget'}
        $budget=$requested
    }
    $window=[ordered]@{schema='r0016-held-invocation-window.v1';label=$Label;subject=$Context.subject;source=$Spec.source;sourceSha256=$Spec.sourceSha256;nonce=$Spec.nonce;processId=$null;started=$false;completed=$false;unchanged=$null;error=$null;spec=$null;launch=$null;hostBefore=$null;hostAfter=$null;before=$null;after=$null;beforeSignal=$null;beforeAck=$null;afterSignal=$null;afterAck=$null}
    $child=$null;$started=$false;$before=$null;$after=$null;$atBefore=$null;$atAfter=$null
    $stdoutTask=$null;$stderrTask=$null;$stdout='';$stderr='';$stdoutDrained=$false;$stderrDrained=$false
    $timedOut=$false;$killGraceExpired=$false;$killError=$null;$error=$null;$exitCode=$null;$terminalObservedElapsedMs=$null;$specPath=$null
    $clock=[Diagnostics.Stopwatch]::StartNew();$startedUtc=[DateTime]::UtcNow.ToString('o');$createdUtc=$null;$exitUtc=$null
    try{
        if($Label -notmatch '^[a-z][a-z0-9-]*$' -or [IO.Path]::GetFullPath([string]$Spec.subject) -cne [IO.Path]::GetFullPath($Context.subject)){throw 'BOOTSTRAP: invocation label or subject differs from context'}
        $specPath=[IO.Path]::GetFullPath([string]$Context.values.R0016_PREVIEW_SPEC)
        if(-not $specPath.StartsWith(([IO.Path]::GetFullPath($Context.hostControl)+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){throw 'BOOTSTRAP: invocation spec escaped host control'}
        $window.spec=Get-PreviewFileFact $specPath
        foreach($field in @('beforeSignal','beforeAck','afterSignal','afterAck')){
            $path=[IO.Path]::GetFullPath([string]$Spec.$field)
            if(-not $path.StartsWith(([IO.Path]::GetFullPath($Context.hostControl)+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase) -or [IO.File]::Exists($path) -or [IO.File]::Exists($path+'.partial')){throw 'BOOTSTRAP: phase control path is outside control or already occupied'}
        }
        if((Get-PreviewFileFact $Spec.source).sha256 -cne $Spec.sourceSha256){throw 'BOOTSTRAP: source changed before launch'}
        $before=Save-PreviewInventory $Context.subject (Join-Path $Context.root ($Label+'.before.json'))
        $window.hostBefore=Get-PreviewFileFact (Join-Path $Context.root ($Label+'.before.json'))
        $info=New-Object Diagnostics.ProcessStartInfo
        $info.FileName=$HostExecutable;$info.Arguments='-NoProfile -File "'+$File.Replace('"','\"')+'"';$info.WorkingDirectory=$Context.root
        $info.UseShellExecute=$false;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
        foreach($key in @($info.EnvironmentVariables.Keys)){if(@($Context.values.Keys) -contains [string]$key){$info.EnvironmentVariables.Remove([string]$key)}}
        foreach($key in $Context.values.Keys){$info.EnvironmentVariables[[string]$key]=[string]$Context.values[$key]}
        $child=New-Object Diagnostics.Process;$child.StartInfo=$info
        [void]$child.Start();$started=$true;$createdUtc=[DateTime]::UtcNow.ToString('o');$window.processId=$child.Id
        $launchPath=Join-Path $Context.root ($Label+'.launch.json')
        Write-PreviewJson $launchPath ([pscustomobject]@{startedUtc=$startedUtc;createdUtc=$createdUtc;processId=$child.Id;label=$Label;subject=$Context.subject;host=$HostExecutable;nativeFile=$File;arguments=$info.Arguments;budgetSeconds=$budget;nonce=$Spec.nonce;sourceSha256=$Spec.sourceSha256;spec=$window.spec})
        $window.launch=Get-PreviewFileFact $launchPath
        $child.StandardInput.Close();$stdoutTask=$child.StandardOutput.ReadToEndAsync();$stderrTask=$child.StandardError.ReadToEndAsync()
        while(-not $child.HasExited){
            $phase=if($window.started){'after'}else{'before'}
            $signal=[string]$Spec.($phase+'Signal');$ack=[string]$Spec.($phase+'Ack')
            if(-not $window.completed -and [IO.File]::Exists($signal)){
                $token=[string]$child.Id+"`t"+$Spec.nonce+"`t"+$phase+'-invocation'
                if([IO.File]::ReadAllText($signal) -cne $token){throw 'BOOTSTRAP: held phase PID/nonce mismatch'}
                if($child.HasExited){throw 'BOOTSTRAP: child exited before held observation'}
                $snapshotPath=Join-Path $Context.root ($Label+'.'+$phase+'-invocation.json')
                $snapshot=Save-PreviewInventory $Context.subject $snapshotPath
                if($child.HasExited){throw 'BOOTSTRAP: child exited during held observation'}
                if($clock.Elapsed.TotalSeconds -ge $budget){$timedOut=$true;throw 'BOOTSTRAP: held observation exceeded child deadline'}
                $window[$phase]=Get-PreviewFileFact $snapshotPath;$window[$phase+'Signal']=Get-PreviewFileFact $signal
                [IO.File]::WriteAllText($ack+'.partial',$token,(New-Object Text.UTF8Encoding $false));[IO.File]::Move($ack+'.partial',$ack)
                $window[$phase+'Ack']=Get-PreviewFileFact $ack
                if($phase -eq 'before'){$atBefore=$snapshot;$window.started=$true}else{$atAfter=$snapshot;$window.completed=$true}
            }
            if($clock.Elapsed.TotalSeconds -ge $budget){$timedOut=$true;throw 'BOOTSTRAP: child deadline expired'}
            $null=$child.WaitForExit(20)
        }
        $terminalObservedElapsedMs=$clock.Elapsed.TotalMilliseconds
        if($terminalObservedElapsedMs -ge ($budget*1000)){$timedOut=$true;throw 'BOOTSTRAP: terminal process first observed after deadline'}
        $exitCode=$child.ExitCode;$exitUtc=[DateTime]::UtcNow.ToString('o')
    }catch{$error=$_.Exception.Message;$window.error=$error}
    finally{
        if($started -and -not $child.HasExited){
            try{$child.Kill();$killGraceExpired=-not $child.WaitForExit(5000)}catch{$killError=$_.Exception.Message;$killGraceExpired=$true}
        }
        if($started -and $child.HasExited){$exitCode=$child.ExitCode;$exitUtc=[DateTime]::UtcNow.ToString('o');if($null -eq $terminalObservedElapsedMs){$terminalObservedElapsedMs=$clock.Elapsed.TotalMilliseconds}}
        try{if($stdoutTask){$stdoutDrained=$stdoutTask.Wait(2000);if($stdoutDrained){$stdout=$stdoutTask.GetAwaiter().GetResult()}}}catch{$error='BOOTSTRAP: stdout drain failed: '+$_.Exception.Message}
        try{if($stderrTask){$stderrDrained=$stderrTask.Wait(2000);if($stderrDrained){$stderr=$stderrTask.GetAwaiter().GetResult()}}}catch{$error='BOOTSTRAP: stderr drain failed: '+$_.Exception.Message}
        if($child){$child.Dispose()}
        try{$after=Save-PreviewInventory $Context.subject (Join-Path $Context.root ($Label+'.after.json'));$window.hostAfter=Get-PreviewFileFact (Join-Path $Context.root ($Label+'.after.json'))}catch{if(-not $error){$error=$_.Exception.Message}}
        try{if((Get-PreviewFileFact $Spec.source).sha256 -cne $Spec.sourceSha256){$error='BOOTSTRAP: source changed during invocation'}}catch{$error='BOOTSTRAP: source custody could not be read'}
        try{if($window.spec -and (Get-PreviewFileFact $specPath).sha256 -cne $window.spec.sha256){$error='BOOTSTRAP: invocation spec changed during child lifetime'}}catch{$error='BOOTSTRAP: invocation spec custody could not be read'}
    }
    if($atBefore -and $atAfter){$window.unchanged=(ConvertTo-Json -InputObject $atBefore.rows -Depth 8 -Compress) -ceq (ConvertTo-Json -InputObject $atAfter.rows -Depth 8 -Compress)}
    $window.error=$error
    $fullUnchanged=if($before -and $after){(ConvertTo-Json -InputObject $before.rows -Depth 8 -Compress) -ceq (ConvertTo-Json -InputObject $after.rows -Depth 8 -Compress)}else{$null}
    Write-PreviewJson (Join-Path $Context.root ($Label+'.window.json')) $window
    [IO.File]::WriteAllText((Join-Path $Context.root ($Label+'.stdout.txt')),$stdout,(New-Object Text.UTF8Encoding $false))
    [IO.File]::WriteAllText((Join-Path $Context.root ($Label+'.stderr.txt')),$stderr,(New-Object Text.UTF8Encoding $false))
    return [pscustomobject]@{
        exit=$exitCode;processId=$window.processId;label=$Label;subject=$Context.subject;fixture=$Context.root;nativeFile=$File;startedUtc=$startedUtc;createdUtc=$createdUtc;processExitObservedUtc=$exitUtc;terminalObservedElapsedMs=$terminalObservedElapsedMs
        budgetSeconds=$budget;killGraceSeconds=5;pipeDrainSecondsEach=2;timedOut=$timedOut;killGraceExpired=$killGraceExpired;killError=$killError
        stdoutDrainCompleted=$stdoutDrained;stderrDrainCompleted=$stderrDrained
        preparation=if($error -or $timedOut -or $killGraceExpired -or -not $stdoutDrained -or -not $stderrDrained){'BOOTSTRAP_BLOCKED'}else{'COMPLETED'};error=$error
        subjectUnchanged=$fullUnchanged;fullHostLifecycleUnchanged=$fullUnchanged;invocationUnchanged=$window.unchanged;invocationWindow=[pscustomobject]$window
        before=if($before){$before.rows}else{$null};after=if($after){$after.rows}else{$null};stdout=$stdout;stderr=$stderr
    }
}
