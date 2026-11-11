#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$Plan)
# New source-free acquisition. No product source, installer helper, or profile is
# evaluated. Python prepares observer AND child TEMP/profile/cache before launch.
# FileSystemWatcher supplies path events, not writer PID or exhaustive syscalls.
$ErrorActionPreference='Stop'
$Utf8=[Text.UTF8Encoding]::new($false)
$Spec=[IO.File]::ReadAllText($Plan)|ConvertFrom-Json
$Root=[IO.Path]::GetFullPath($Spec.root)
$ObserverExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$ObserverVersion=$PSVersionTable.PSVersion.ToString()
$BoundKeys=@('USERPROFILE','HOME','TEMP','TMP','LOCALAPPDATA','APPDATA','PSModuleAnalysisCachePath','DOTNET_CLI_HOME','COMPlus_MultiCoreJitNoProfileGather')

function Need([bool]$Condition,[string]$Message){if(-not $Condition){throw $Message}}
function Hash-File([string]$Path){
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($Path)))).Replace('-','').ToLowerInvariant()}
    finally{$sha.Dispose()}
}
function Owned([string]$Path){
    $full=[IO.Path]::GetFullPath($Path)
    Need ($full -ceq $Root -or $full.StartsWith($Root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) ('Path outside allocated fixture: '+$full)
    $cursor=$full
    while($cursor -and $cursor.Length -ge $Root.Length){
        if([IO.File]::Exists($cursor) -or [IO.Directory]::Exists($cursor)){
            Need (([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Reparse entry refused: '+$cursor)
        }
        if($cursor -ceq $Root){break};$cursor=[IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}
function Save([string]$Path,$Value){
    $null=Owned $Path
    [IO.File]::WriteAllText($Path,(ConvertTo-Json -InputObject $Value -Depth 18),$Utf8)
}
function Fact([string]$Path){return [ordered]@{path=$Path;sha256=(Hash-File $Path);bytes=([IO.FileInfo]::new($Path)).Length}}
function Read-InventoryPass([string]$Watched){
    $rows=[Collections.Generic.List[object]]::new();$pending=[Collections.Generic.Stack[string]]::new()
    $record=[ordered]@{schema='r0016-inventory-pass.v1';root=$Watched;startedUtc=[DateTime]::UtcNow.ToString('o');completedUtc=$null;complete=$false;error=$null;rows=@()}
    try{
        $pending.Push((Owned $Watched))
        while($pending.Count){
            $path=$pending.Pop();$null=Owned $path
            $item=Get-Item -LiteralPath $path -Force -ErrorAction Stop;$item.Refresh()
            Need (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Snapshot refuses reparse entry: '+$path)
            $directory=$item.PSIsContainer;$stamp=$item.LastWriteTimeUtc.Ticks;$attributes=[int]$item.Attributes
            $sections=[Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group -bor [Security.AccessControl.AccessControlSections]::Access
            $security=(Get-Acl -LiteralPath $path -ErrorAction Stop).GetSecurityDescriptorSddlForm($sections)
            $relative=if($path -ceq $Watched){'.'}else{$path.Substring($Watched.Length+1).Replace('\','/')}
            $row=[ordered]@{path=$relative;kind=if($directory){'directory'}else{'file'};attributes=$attributes;mtimeUtcTicks=[string]$stamp;sddl=$security;bytes=$null;sha256=$null}
            if($directory){
                foreach($entry in @(Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop)){$pending.Push($entry.FullName)}
            }else{
                $length=$item.Length;Need ($length -le 67108864) ('Snapshot byte bound exceeded: '+$path)
                $row.bytes=$length;$row.sha256=Hash-File $path;$item.Refresh()
                Need ($item.Length -eq $length -and $item.LastWriteTimeUtc.Ticks -eq $stamp -and [int]$item.Attributes -eq $attributes) ('File changed during snapshot: '+$path)
            }
            $rows.Add([pscustomobject]$row);Need ($rows.Count -le 8192) 'Snapshot entry bound exceeded'
        }
        $record.complete=$true
    }catch{$record.error=$_.Exception.Message}
    $record.rows=@($rows.ToArray()|Sort-Object path -CaseSensitive)
    $record.completedUtc=[DateTime]::UtcNow.ToString('o')
    return [pscustomobject]$record
}
function Take-Snapshot([string]$Watched,[string]$Output){
    # Two fixed full passes, not a retry loop or an atomic snapshot claim.
    $first=Read-InventoryPass $Watched;$second=Read-InventoryPass $Watched
    $agree=$first.complete -and $second.complete -and ((ConvertTo-Json -InputObject $first.rows -Depth 8 -Compress) -ceq (ConvertTo-Json -InputObject $second.rows -Depth 8 -Compress))
    $problem=if(-not $first.complete -or -not $second.complete){'One or both inventory passes are incomplete'}elseif(-not $agree){'Consecutive complete inventories differ'}else{$null}
    $record=[ordered]@{schema='r0016-double-inventory.v2';root=$Watched;startedUtc=$first.startedUtc;completedUtc=$second.completedUtc;complete=$agree;passesAgree=$agree;passes=@($first,$second);rows=$second.rows;error=$problem;scope='Two consecutive full inventories compared exactly; a bounded stability check, not an atomic filesystem snapshot. Both passes are retained; no exclusions or retries.'}
    Save $Output $record
    return [pscustomobject]$record
}
function Delta($Before,$After){
    if(-not $Before.complete -or -not $After.complete){return [ordered]@{observed=$false;unchanged=$null;reason='Incomplete snapshot'}}
    $left=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    $right=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach($row in $Before.rows){$left.Add($row.path,$row)};foreach($row in $After.rows){$right.Add($row.path,$row)}
    $added=@($right.Keys|Where-Object{-not $left.ContainsKey($_)}|Sort-Object)
    $removed=@($left.Keys|Where-Object{-not $right.ContainsKey($_)}|Sort-Object)
    $changed=@(foreach($key in $left.Keys){
        if($right.ContainsKey($key)){
            $fields=@($left[$key].PSObject.Properties.Name|Where-Object{(ConvertTo-Json -InputObject $left[$key].$_ -Compress) -cne (ConvertTo-Json -InputObject $right[$key].$_ -Compress)})
            if($fields.Count){[ordered]@{path=$key;fields=$fields}}
        }
    })
    return [ordered]@{observed=$true;unchanged=($added.Count+$removed.Count+$changed.Count -eq 0);added=$added;removed=$removed;changed=$changed}
}

function Start-Recorder([string]$Watched,[string]$Control){
    $watcher=[IO.FileSystemWatcher]::new((Owned $Watched))
    $watcher.IncludeSubdirectories=$true;$watcher.InternalBufferSize=65536
    $watcher.NotifyFilter=[IO.NotifyFilters]::FileName -bor [IO.NotifyFilters]::DirectoryName -bor [IO.NotifyFilters]::LastWrite -bor [IO.NotifyFilters]::Attributes -bor [IO.NotifyFilters]::Size -bor [IO.NotifyFilters]::Security
    $prefix='R0016-'+$PID+'-'+[guid]::NewGuid().ToString('N')+'-'
    $rec=[pscustomobject]@{watcher=$watcher;prefix=$prefix;watched=$Watched;control=$Control;phase='setup';events=[Collections.Generic.List[object]]::new();errors=[Collections.Generic.List[object]]::new();dropped=0;maximumPending=0;ids=@()}
    try{
        foreach($kind in @('Created','Changed','Renamed','Deleted','Error')){
            $id=$prefix+$kind;$null=Register-ObjectEvent -InputObject $watcher -EventName $kind -SourceIdentifier $id
            $rec.ids+=@($id)
        }
        [IO.File]::WriteAllText((Join-Path $Control 'events.jsonl'),'',$Utf8)
        $watcher.EnableRaisingEvents=$true
    }catch{
        foreach($id in $rec.ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}
        $watcher.Dispose();throw
    }
    return $rec
}
function Pump-Events($Rec){
    $queued=@(Get-Event -ErrorAction SilentlyContinue|Where-Object{$_.SourceIdentifier.StartsWith($Rec.prefix,[StringComparison]::Ordinal)})
    $Rec.maximumPending=[Math]::Max($Rec.maximumPending,$queued.Count)
    if($queued.Count -gt $Spec.recorderEventLimit){
        $Rec.errors.Add([ordered]@{kind='observer-queue-limit';count=$queued.Count;utc=[DateTime]::UtcNow.ToString('o')})
        $Rec.watcher.EnableRaisingEvents=$false
    }
    foreach($event in $queued){
        try{
            $kind=$event.SourceIdentifier.Substring($Rec.prefix.Length)
            if($kind -eq 'Error'){
                $problem=$event.SourceEventArgs.GetException()
                $row=[ordered]@{kind='Error';exceptionType=$problem.GetType().FullName;message=$problem.Message;phaseAtDrain=$Rec.phase;observedUtc=[DateTime]::UtcNow.ToString('o')}
                $Rec.errors.Add($row);$Rec.watcher.EnableRaisingEvents=$false
            }else{
                $path=$event.SourceEventArgs.FullPath
                Need ($path.StartsWith($Rec.watched+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) 'Watcher returned path outside its subject'
                $row=[ordered]@{kind=$kind;path=$path.Substring($Rec.watched.Length+1).Replace('\','/');oldPath=$null;phaseAtDrain=$Rec.phase;eventQueuedUtc=$event.TimeGenerated.ToUniversalTime().ToString('o');observedUtc=[DateTime]::UtcNow.ToString('o')}
                if($kind -eq 'Renamed'){$row.oldPath=$event.SourceEventArgs.OldFullPath.Substring($Rec.watched.Length+1).Replace('\','/')}
            }
            if($Rec.events.Count -ge $Spec.recorderEventLimit){
                $Rec.dropped++;$Rec.watcher.EnableRaisingEvents=$false
                if($Rec.dropped -eq 1){$Rec.errors.Add([ordered]@{kind='retained-event-limit';limit=$Spec.recorderEventLimit})}
            }else{
                $Rec.events.Add([pscustomobject]$row)
                [IO.File]::AppendAllText((Join-Path $Rec.control 'events.jsonl'),(ConvertTo-Json -InputObject $row -Compress)+[Environment]::NewLine,$Utf8)
            }
        }finally{Remove-Event -EventIdentifier $event.EventIdentifier -ErrorAction SilentlyContinue}
    }
}
function Drain-For($Rec,[int]$Milliseconds){
    $clock=[Diagnostics.Stopwatch]::StartNew()
    while($clock.ElapsedMilliseconds -lt $Milliseconds){Pump-Events $Rec;[Threading.Thread]::Sleep(20)}
    Pump-Events $Rec
}
function Stop-Recorder($Rec){
    $Rec.watcher.EnableRaisingEvents=$false
    try{Pump-Events $Rec}finally{
        foreach($id in $Rec.ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}
        $Rec.watcher.Dispose()
        Save (Join-Path $Rec.control 'recorder-result.json') ([ordered]@{eventFile=(Fact (Join-Path $Rec.control 'events.jsonl'));retained=$Rec.events.Count;dropped=$Rec.dropped;maximumPending=$Rec.maximumPending;errors=$Rec.errors.ToArray();intact=($Rec.errors.Count -eq 0);scope='FileSystemWatcher path/queued-time evidence; no writer PID, exhaustive syscall coverage, or proof from absent events.'})
    }
    Need ($Rec.errors.Count -eq 0) 'Recorder reported an error during final drain'
}

$ChildText=@'
# Fixed source-free child: owned control records and wait loops only.
$ErrorActionPreference='Stop'
$encoder=[Text.UTF8Encoding]::new($false)
$token=[string]$PID+"`t"+$env:R0016_PROBE_NONCE
$lines=[Collections.Generic.List[string]]::new()
foreach($key in @('USERPROFILE','HOME','TEMP','TMP','LOCALAPPDATA','APPDATA','PSModulePath','PSModuleAnalysisCachePath','DOTNET_CLI_HOME','COMPlus_MultiCoreJitNoProfileGather')){
    $value=[Environment]::GetEnvironmentVariable($key)
    $lines.Add($key+"`t"+[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([string]$value)))
}
$lines.Add('__executable'+"`t"+[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)))
$lines.Add('__clr'+"`t"+[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([Environment]::Version.ToString())))
[IO.File]::WriteAllLines($env:R0016_PROBE_ENV,$lines.ToArray(),$encoder)
[IO.File]::WriteAllText($env:R0016_PROBE_READY+'.partial',$token+"`t"+$PSVersionTable.PSVersion.ToString(),$encoder)
[IO.File]::Move($env:R0016_PROBE_READY+'.partial',$env:R0016_PROBE_READY)
$clock=[Diagnostics.Stopwatch]::StartNew()
foreach($path in @($env:R0016_PROBE_ACK,$env:R0016_PROBE_RELEASE)){
    while(-not ([IO.File]::Exists($path) -and [IO.File]::ReadAllText($path) -ceq $token)){
        if($clock.Elapsed.TotalSeconds -ge 60){[Console]::Error.WriteLine('Owned source-free handshake expired');exit 3}
        [Threading.Thread]::Sleep(20)
    }
}
[IO.File]::WriteAllText($env:R0016_PROBE_TERMINAL,$token,$encoder)
[Console]::WriteLine('SOURCE_FREE_CHILD_COMPLETED')
exit 0
'@

function Run-Child($Mode,[string]$Label,[string]$ChildFile,$Rec){
    $control=Join-Path $Mode.control $Label;$null=Owned $control;[void][IO.Directory]::CreateDirectory($control)
    $nonce=[guid]::NewGuid().ToString('N');$childEnv=@{}
    foreach($property in $Mode.environment.PSObject.Properties){$childEnv[$property.Name]=[string]$property.Value}
    foreach($pair in @(@('READY','ready'),@('ACK','ack'),@('RELEASE','release'),@('TERMINAL','terminal'),@('ENV','effective-env.tsv'))){$childEnv['R0016_PROBE_'+$pair[0]]=Join-Path $control $pair[1]}
    $childEnv.R0016_PROBE_NONCE=$nonce
    $arguments='-NoProfile -File "'+$ChildFile+'"'
    $launchSpec=[ordered]@{label=$Label;mode=$Mode.name;host=(Fact $Spec.host.path);source=(Fact $ChildFile);arguments=$arguments;environment=$childEnv;nonce=$nonce;childTimeoutSeconds=$Spec.childTimeoutSeconds;prelaunchTempRebinding=$true;installerExecuted=$false}
    Save (Join-Path $control 'launch-spec.json') $launchSpec
    $record=[ordered]@{label=$Label;mode=$Mode.name;acquired=$false;installerExecuted=$false;processId=$null;exit=$null;timedOut=$false;ready=$false;error=$null;stdoutDrainCompleted=$false;stderrDrainCompleted=$false;killGraceExpired=$false;stdoutDrainError=$null;stderrDrainError=$null;launchSpec=(Fact (Join-Path $control 'launch-spec.json'));snapshots=[ordered]@{};deltas=[ordered]@{}}
    $child=$null;$outStream=$null;$errStream=$null;$outCopy=$null;$errCopy=$null;$before=$null;$atReady=$null;$held=$null;$started=$false
    try{
        $Rec.phase=$Label+'-before-launch';Pump-Events $Rec;Need ($Rec.errors.Count -eq 0) 'Recorder unavailable before child'
        $before=Take-Snapshot $Mode.watched (Join-Path $control 'before.json');Need $before.complete 'Incomplete pre-launch snapshot'
        Need ((Hash-File $Spec.host.path) -ceq $Spec.host.sha256) 'Selected native host changed'
        $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$Spec.host.path;$info.Arguments=$arguments;$info.WorkingDirectory=$control
        $info.UseShellExecute=$false;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
        $info.EnvironmentVariables.Clear();foreach($key in $childEnv.Keys){$info.EnvironmentVariables[$key]=[string]$childEnv[$key]}
        $outStream=[IO.File]::Open((Join-Path $control 'stdout.raw'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        $errStream=[IO.File]::Open((Join-Path $control 'stderr.raw'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        $child=[Diagnostics.Process]::new();$child.StartInfo=$info;$clock=[Diagnostics.Stopwatch]::StartNew()
        $record.startedUtc=[DateTime]::UtcNow.ToString('o');$Rec.phase=$Label+'-launch-to-ready'
        [void]$child.Start();$started=$true;$record.processId=$child.Id;$record.createdUtc=[DateTime]::UtcNow.ToString('o')
        Save (Join-Path $control 'launch.json') ([ordered]@{processId=$child.Id;host=$Spec.host.path;source=$ChildFile;sourceSha256=$launchSpec.source.sha256;arguments=$arguments;nonce=$nonce;startedUtc=$record.startedUtc;createdUtc=$record.createdUtc;timeoutSeconds=$Spec.childTimeoutSeconds;environmentSha256=(Hash-File (Join-Path $control 'launch-spec.json'))})
        $child.StandardInput.Close();$outCopy=$child.StandardOutput.BaseStream.CopyToAsync($outStream);$errCopy=$child.StandardError.BaseStream.CopyToAsync($errStream)
        $holdClock=$null
        while(-not $child.HasExited){
            Pump-Events $Rec;Need ($Rec.errors.Count -eq 0) 'Recorder error or overflow during child'
            if(-not $record.ready -and [IO.File]::Exists($childEnv.R0016_PROBE_READY)){
                $token=[string]$child.Id+"`t"+$nonce
                $expected=$token+"`t"+$ObserverVersion
                Need ([IO.File]::ReadAllText($childEnv.R0016_PROBE_READY) -ceq $expected) 'Actual child PID/nonce/version readiness mismatch'
                $effective=@{}
                foreach($line in [IO.File]::ReadAllLines($childEnv.R0016_PROBE_ENV)){
                    $parts=$line.Split("`t");Need ($parts.Count -eq 2 -and -not $effective.ContainsKey($parts[0])) 'Malformed effective environment'
                    $effective[$parts[0]]=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($parts[1]))
                }
                foreach($key in $BoundKeys){Need ([string]$effective[$key] -ceq [string]$childEnv[$key]) ('Runtime changed owned environment binding: '+$key)}
                Need ([string]::Equals($effective.__executable,$Spec.host.path,[StringComparison]::OrdinalIgnoreCase)) 'Child used a different executable'
                Save (Join-Path $control 'ready-identity.json') ([ordered]@{processId=$child.Id;nonce=$nonce;version=$ObserverVersion;effectiveEnvironment=$effective;observedUtc=[DateTime]::UtcNow.ToString('o')})
                $record.ready=$true;$record.readyObservedUtc=[DateTime]::UtcNow.ToString('o');$record.readyElapsedMilliseconds=$clock.Elapsed.TotalMilliseconds
                $Rec.phase=$Label+'-ready-snapshot';$atReady=Take-Snapshot $Mode.watched (Join-Path $control 'at-ready.json');Need $atReady.complete 'Incomplete ready snapshot'
                [IO.File]::WriteAllText($childEnv.R0016_PROBE_ACK,$token,$Utf8);$holdClock=[Diagnostics.Stopwatch]::StartNew();$Rec.phase=$Label+'-source-free-held'
            }
            if($record.ready -and $null -eq $held -and $holdClock.ElapsedMilliseconds -ge $Spec.holdMilliseconds){
                $held=Take-Snapshot $Mode.watched (Join-Path $control 'held-before-release.json');Need $held.complete 'Incomplete held snapshot'
                [IO.File]::WriteAllText($childEnv.R0016_PROBE_RELEASE,([string]$child.Id+"`t"+$nonce),$Utf8);$Rec.phase=$Label+'-release-to-exit'
            }
            if($clock.Elapsed.TotalSeconds -ge $Spec.childTimeoutSeconds){$record.timedOut=$true;throw 'Child deadline expired'}
            [Threading.Thread]::Sleep(20)
        }
        $record.exit=$child.ExitCode;$record.exitObservedUtc=[DateTime]::UtcNow.ToString('o');$record.elapsedSeconds=$clock.Elapsed.TotalSeconds
    }catch{$record.error=$_.Exception.Message}
    finally{
        if($started -and -not $child.HasExited){
            try{$child.Kill();$record.killGraceExpired=-not $child.WaitForExit(5000)}catch{$record.killError=$_.Exception.Message;$record.killGraceExpired=$true}
        }
        if($started -and $child.HasExited){$record.exit=$child.ExitCode;$record.exitObservedUtc=[DateTime]::UtcNow.ToString('o')}
        foreach($capture in @(@('stdout',$outCopy),@('stderr',$errCopy))){
            if($null -ne $capture[1]){
                try{$record[$capture[0]+'DrainCompleted']=$capture[1].Wait(2000)}catch{$record[$capture[0]+'DrainError']=$_.Exception.Message}
            }
        }
        if($outStream){$outStream.Dispose()};if($errStream){$errStream.Dispose()};if($child){$child.Dispose()}
        $Rec.phase=$Label+'-post-exit-drain'
        try{Drain-For $Rec $Spec.recorderDrainMilliseconds}catch{if(-not $record.error){$record.error=$_.Exception.Message}}
        $after=Take-Snapshot $Mode.watched (Join-Path $control 'after-exit.json')
        foreach($pair in @(@('before','before.json'),@('atReady','at-ready.json'),@('held','held-before-release.json'),@('after','after-exit.json'))){
            $path=Join-Path $control $pair[1];if([IO.File]::Exists($path)){$record.snapshots[$pair[0]]=Fact $path}
        }
        if($before){$record.deltas.full=Delta $before $after};if($atReady){$record.deltas.startup=Delta $before $atReady};if($held){$record.deltas.held=Delta $atReady $held;$record.deltas.exit=Delta $held $after}
        foreach($kind in @('stdout','stderr')){$path=Join-Path $control ($kind+'.raw');if([IO.File]::Exists($path)){$record[$kind]=Fact $path}}
        $terminalOK=[IO.File]::Exists($childEnv.R0016_PROBE_TERMINAL) -and [IO.File]::ReadAllText($childEnv.R0016_PROBE_TERMINAL) -ceq ([string]$record.processId+"`t"+$nonce)
        $record.terminalMarkerValid=$terminalOK
        $record.acquired=($record.ready -and $record.exit -eq 0 -and -not $record.error -and -not $record.timedOut -and -not $record.killGraceExpired -and $record.stdoutDrainCompleted -and $record.stderrDrainCompleted -and $after.complete -and $terminalOK -and $Rec.errors.Count -eq 0)
        Save (Join-Path $control 'result.json') $record
    }
    return [pscustomobject]$record
}

$Results=[Collections.Generic.List[object]]::new()
$Report=[ordered]@{schema='r0016-source-free-host-acquisition.v1';acquired=$false;installerExecuted=$false;productQualificationRows=0;hostVersion=$ObserverVersion;observerProcessId=$PID;plannedCases=@('default/cold','default/warm','no-gather/cold','no-gather/warm');notRun=@();results=@();error=$null;prelaunchTempRebinding=$true;scope='Observer and children have owned TEMP/profile/cache before runtime launch. Every watched path is retained. Handshake writes are outside the watched subject. Ready/held windows are source-free script activity after runtime startup, not pre-installer interception. FileSystemWatcher has no writer PID and absence of an event proves nothing.'}
try{
    Need ($Spec.schema -ceq $Report.schema) 'Unsupported acquisition schema'
    Need ([IO.Path]::GetFullPath($Plan) -ceq (Join-Path $Root 'control\plan.json')) 'Plan is not the allocated launcher plan'
    Need ((Hash-File $PSCommandPath) -ceq $Spec.observer.sha256) 'Observer source changed'
    Need ([string]::Equals($ObserverExecutable,$Spec.host.path,[StringComparison]::OrdinalIgnoreCase) -and (Hash-File $ObserverExecutable) -ceq $Spec.host.sha256) 'Observer executable differs from selected host'
    Need (($Spec.hostKind -eq 'ps51' -and $PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -eq 1) -or ($Spec.hostKind -eq 'ps766' -and $ObserverVersion -ceq '7.6.6')) 'Unsupported selected native runtime version'
    $observerEffective=@{};foreach($property in $Spec.observerEnvironment.PSObject.Properties){$observerEffective[$property.Name]=[Environment]::GetEnvironmentVariable($property.Name)}
    foreach($key in $BoundKeys){Need ([string]$observerEffective[$key] -ceq [string]$Spec.observerEnvironment.$key) ('Observer owned binding changed: '+$key)}
    Save (Join-Path $Root 'observer-identity.json') ([ordered]@{pid=$PID;version=$ObserverVersion;clr=[Environment]::Version.ToString();executable=(Fact $ObserverExecutable);source=(Fact $PSCommandPath);plan=(Fact $Plan);effectiveEnvironment=$observerEffective;knownFolderUserProfile=[Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile);knownFolderLocalAppData=[Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)})
    $ChildFile=Join-Path $Root 'control\source-free-child.ps1';$null=Owned $ChildFile;[IO.File]::WriteAllText($ChildFile,$ChildText,$Utf8)
    Need ($Spec.modes.Count -eq 2 -and $Spec.modes[0].name -ceq 'default' -and $Spec.modes[1].name -ceq 'no-gather') 'Fixed experimental mode set differs'
    foreach($mode in $Spec.modes){
        $null=Owned $mode.watched;$null=Owned $mode.control
        $expectedFlag=if($mode.name -ceq 'no-gather'){'1'}else{''}
        Need ([string]$mode.environment.COMPlus_MultiCoreJitNoProfileGather -ceq $expectedFlag) 'Experimental prelaunch flag differs'
        foreach($key in $BoundKeys|Where-Object{$_ -ne 'COMPlus_MultiCoreJitNoProfileGather'}){$null=Owned $mode.environment.$key}
        $rec=$null
        try{
            $rec=Start-Recorder $mode.watched $mode.control;$rec.phase='positive-event-control'
            $preControl=Take-Snapshot $mode.watched (Join-Path $mode.control 'before-event-control.json');Need $preControl.complete 'Positive-control starting snapshot incomplete'
            $first=Join-Path $mode.watched 'event-control\transient-created.txt';$second=Join-Path $mode.watched 'event-control\transient-renamed.txt'
            [IO.File]::WriteAllText($first,'declared observer event control',$Utf8);[IO.File]::AppendAllText($first,' appended',$Utf8);[IO.File]::Move($first,$second);[IO.File]::Delete($second)
            Drain-For $rec $Spec.recorderDrainMilliseconds
            $postControl=Take-Snapshot $mode.watched (Join-Path $mode.control 'after-event-control.json')
            $eventKinds=@($rec.events.ToArray()|Where-Object{$_.path -like 'event-control/*'}|ForEach-Object{$_.kind})
            $controlPassed=($postControl.complete -and $eventKinds -contains 'Created' -and $eventKinds -contains 'Renamed' -and $eventKinds -contains 'Deleted' -and $rec.errors.Count -eq 0)
            Save (Join-Path $mode.control 'event-control.json') ([ordered]@{pass=$controlPassed;producer='observer';operations=@('create','append','rename','delete');observedKinds=$eventKinds;paths=@($first,$second);delta=(Delta $preControl $postControl);scope='Same watcher and watched tree; declared preparation effects precede child before-snapshots. No exclusions.'})
            Need $controlPassed 'Watcher positive event control failed'
            $rec.phase='observer-only';$observerBefore=Take-Snapshot $mode.watched (Join-Path $mode.control 'observer-only-before.json')
            Drain-For $rec $Spec.holdMilliseconds
            $observerAfter=Take-Snapshot $mode.watched (Join-Path $mode.control 'observer-only-after.json')
            Save (Join-Path $mode.control 'observer-only.json') ([ordered]@{installerExecuted=$false;childExecuted=$false;delta=(Delta $observerBefore $observerAfter);before=(Fact (Join-Path $mode.control 'observer-only-before.json'));after=(Fact (Join-Path $mode.control 'observer-only-after.json'))})
            Need ($observerBefore.complete -and $observerAfter.complete -and $rec.errors.Count -eq 0) 'Observer-only acquisition incomplete'
            foreach($label in @('cold','warm')){
                $row=Run-Child $mode $label $ChildFile $rec;$Results.Add($row)
                Need $row.acquired ('Source-free child acquisition incomplete: '+$mode.name+'/'+$label)
            }
        }finally{if($rec){Stop-Recorder $rec}}
    }
    Need ($Results.Count -eq 4) 'Incomplete fixed cold/warm experiment'
    Need ((Hash-File $PSCommandPath) -ceq $Spec.observer.sha256 -and (Hash-File $ObserverExecutable) -ceq $Spec.host.sha256) 'Source or native executable changed during acquisition'
    $Report.acquired=$true
}catch{$Report.error=$_.Exception.Message}
finally{
    $Report.results=$Results.ToArray();$observed=@($Report.results|ForEach-Object{$_.mode+'/'+$_.label})
    $Report.notRun=@($Report.plannedCases|Where-Object{$_ -cnotin $observed})
    Save (Join-Path $Root 'observer-result.json') $Report
}
if($Report.acquired){exit 0}else{exit 2}
