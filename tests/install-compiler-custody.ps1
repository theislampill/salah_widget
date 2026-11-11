param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$FixtureParent=[IO.Path]::GetTempPath(),
    [string]$InternalCase,
    [string]$InternalRoot,
    [string]$CaseResult,
    [int]$ChildTimeoutSeconds=90
)
# Actual Windows-only compiler custody controls. No POSIX native adapter.
$ErrorActionPreference='Stop'
$Utf8=[Text.UTF8Encoding]::new($false)
function Hash([string]$Path){$h=[Security.Cryptography.SHA256]::Create();try{return [BitConverter]::ToString($h.ComputeHash([IO.File]::ReadAllBytes($Path))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function Assert-Control([bool]$Condition,[string]$Message){if(-not $Condition){throw $Message}}
function Set-OwnedDirectory([string]$Path,[Security.AccessControl.FileSystemRights]$Extra=0){
    Assert-Control ($Path.StartsWith($script:allowedRoot,[StringComparison]::OrdinalIgnoreCase)) 'Fixture ACL target escaped its fresh root'
    $acl=[Security.AccessControl.DirectorySecurity]::new();$acl.SetOwner($script:subjectSid);$acl.SetAccessRuleProtection($true,$false)
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($script:subjectSid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
    if([int]$Extra){$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-1-0'),$Extra,[Security.AccessControl.AccessControlType]::Allow))}
    Set-Acl -LiteralPath $Path -AclObject $acl
}
function Context-Observation($Context){
    if(-not $Context){return $null}
    [pscustomobject]@{id=$Context.Id;status=$Context.Status;path=$Context.Path;identity=$Context.Identity;sid=$Context.Sid;created=$Context.Created;cleanupError=$Context.CleanupError;rootLeaseClosed=if($Context.RootLease){$Context.RootLease.Handle.IsClosed}else{$null};parentLeaseCount=@($Context.Leases).Count;parentLeasesClosed=@($Context.Leases|ForEach-Object{$_.Handle.IsClosed})}
}

if($InternalCase){
    $script:allowedRoot=[IO.Path]::GetFullPath($InternalRoot).TrimEnd('\')+'\'
    $script:subjectSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $root=Join-Path $InternalRoot $InternalCase
    [void][IO.Directory]::CreateDirectory($root);Set-OwnedDirectory $root
    $temporary=Join-Path $root 'temp';$profile=Join-Path $root 'profile'
    foreach($path in @($temporary,$profile)){[void][IO.Directory]::CreateDirectory($path);Set-OwnedDirectory $path}
    $env:TEMP=$temporary;$env:TMP=$temporary;$env:USERPROFILE=$profile
    $script:DryRun=$false;$script:StagingAttempt=$null;$script:CompilerScratch=$null;$script:compilerCalls=@();$script:messages=@()
    $t=$null;$e=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$t,[ref]$e)
    Assert-Control (@($e).Count -eq 0) 'Source does not parse'
    foreach($definition in $ast.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){. ([scriptblock]::Create($definition.Extent.Text))}
    function Write-Host {param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline);$script:messages += [string]$Object}
    function Invoke-WebRequest {throw 'Unexpected network request'}
    function Invoke-RestMethod {throw 'Unexpected metadata request'}
    function Read-Host {throw 'Unexpected prompt'}
    function Add-Type {
        param([string]$TypeDefinition,[string[]]$AssemblyName,[object]$CompilerParameters)
        if($AssemblyName){Microsoft.PowerShell.Utility\Add-Type -AssemblyName $AssemblyName;return}
        $context=$script:CompilerScratch
        Assert-Control ($null -ne $context -and $context.Created -and $context.Identity -and $context.RootLease.Facts.Private -and -not $context.RootLease.Handle.IsClosed) 'Compiler reached before owned root identity/private lease'
        Assert-Control (@($context.Leases|Where-Object{$_.Handle.IsClosed}).Count -eq 0) 'Ancestor leases closed before compiler call'
        Assert-Control ($env:TEMP -ceq $context.Path -and $env:TMP -ceq $context.Path -and [IO.Path]::GetTempPath().TrimEnd('\') -ceq $context.Path.TrimEnd('\')) 'Compiler temporary paths are not the owned root'
        if($PSVersionTable.PSVersion.Major -eq 5){Assert-Control ($CompilerParameters.TempFiles.TempDir -ceq $context.Path -and $CompilerParameters.TempFiles.KeepFiles) 'PS5 compiler collection does not retain owned temporary files'}
        $script:compilerCalls += [pscustomobject]@{path=$context.Path;identity=$context.Identity;owner=$context.RootLease.Facts.Owner;private=$context.RootLease.Facts.Private;nativeTemp=[IO.Path]::GetTempPath();temp=$env:TEMP;tmp=$env:TMP;parentLeases=@($context.Leases).Count;keepFiles=if($CompilerParameters){$CompilerParameters.TempFiles.KeepFiles}else{$null}}
        if($InternalCase -eq 'compile-failure'){$TypeDefinition += "`n deliberately invalid compiler input !"}
        if($CompilerParameters){Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -CompilerParameters $CompilerParameters -ErrorAction Stop}
        else{Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -ErrorAction Stop}
    }
    $before=@([IO.Directory]::EnumerateFileSystemEntries($temporary));$observation=[ordered]@{};$pass=$false;$reason=$null;$expectedFailure=$null
    try{
        Assert-Control (-not ('SalahInstaller.StageNative' -as [type]) -and -not ('SalahInstaller.CompilerNative' -as [type])) 'Child native types were not cold'
        switch($InternalCase){
            'foreign-parent' {
                Set-OwnedDirectory $temporary ([Security.AccessControl.FileSystemRights]'CreateFiles,CreateDirectories')
                try{Initialize-StagingNative}catch{$expectedFailure=$_.Exception.Message}
                Assert-Control ($expectedFailure -like '*Compiler parent is not owned*') ('Compiler parent was accepted or refused at an unrelated boundary: '+$expectedFailure)
                Assert-Control ($script:compilerCalls.Count -eq 0 -and -not ('SalahInstaller.StageNative' -as [type]) -and -not $script:CompilerScratch.Created) 'Unsafe terminal parent reached compiler output'
                Assert-Control (@([IO.Directory]::EnumerateFileSystemEntries($temporary)).Count -eq 0) 'Unsafe terminal parent gained output'
            }
            'foreign-ancestor' {
                Set-OwnedDirectory $root ([Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles)
                try{Initialize-StagingNative}catch{$expectedFailure=$_.Exception.Message}
                Assert-Control ($expectedFailure -like '*Compiler ancestor permits foreign replacement*') ('Unsafe ancestor refused at unrelated boundary: '+$expectedFailure)
                Assert-Control ($script:compilerCalls.Count -eq 0 -and -not $script:CompilerScratch.Created -and @([IO.Directory]::EnumerateFileSystemEntries($temporary)).Count -eq 0) 'Unsafe ancestor reached compiler output'
            }
            'exclusive-collision' {
                $script:actualOpen=${function:Open-CompilerDirectoryLease};$script:collision=$null
                function Open-CompilerDirectoryLease([string]$Path,[string]$Sid,[string]$TrustedInstallerSid){
                    $lease=& $script:actualOpen $Path $Sid $TrustedInstallerSid
                    if($Path -ceq $temporary -and -not $script:collision){
                        $script:collision=Join-Path $temporary ('SalahWidgetCompiler-'+$script:CompilerScratch.Id)
                        [void][IO.Directory]::CreateDirectory($script:collision);Set-OwnedDirectory $script:collision
                        [IO.File]::WriteAllText((Join-Path $script:collision 'sentinel'),'preexisting fixture bytes')
                    }
                    return $lease
                }
                try{Initialize-StagingNative}catch{$expectedFailure=$_.Exception.Message}
                Assert-Control ($expectedFailure -like '*Create exclusive private compiler directory*' -and -not $script:CompilerScratch.Created -and $script:compilerCalls.Count -eq 0) 'Existing compiler directory was adopted'
                Assert-Control ([IO.File]::ReadAllText((Join-Path $script:collision 'sentinel')) -ceq 'preexisting fixture bytes') 'Collision sentinel changed'
                $observation.collision=$script:collision
            }
            'compile-failure' {
                try{Initialize-StagingNative}catch{$expectedFailure=$_.Exception.Message}
                Assert-Control ($expectedFailure -and $script:compilerCalls.Count -eq 1 -and -not ('SalahInstaller.StageNative' -as [type])) 'Actual compiler failure was not reached'
                Assert-Control ($script:CompilerScratch.Status -ceq 'retained-compilation-failed' -and [IO.Directory]::Exists($script:CompilerScratch.Path)) 'Compiler failure did not retain owned output'
                $lease=Open-CompilerDirectoryLease $script:CompilerScratch.Path $script:subjectSid.Value ''
                try{Assert-Control ($lease.Facts.Private -and $lease.Facts.Identity -ceq $script:CompilerScratch.Identity) 'Retained compiler root lost private identity'}finally{$lease.Handle.Dispose()}
                $observation.retainedFiles=@(Get-ChildItem -LiteralPath $script:CompilerScratch.Path -Recurse -Force|ForEach-Object{[pscustomobject]@{path=$_.FullName;attributes=[string]$_.Attributes;sha256=if(-not $_.PSIsContainer){Hash $_.FullName}else{$null}}})
            }
            'cleanup-identity-failure' {
                $script:actualClear=${function:Clear-StagingCompilerContext}
                function Clear-StagingCompilerContext($Context,[bool]$Compiled){$Context.Identity='deliberately mismatched proof'; & $script:actualClear $Context $Compiled}
                Initialize-StagingNative
                Assert-Control ($script:CompilerScratch.Status -ceq 'retained-cleanup-failed' -and [IO.Directory]::Exists($script:CompilerScratch.Path)) 'Unproved cleanup removed compiler directory'
                Assert-Control ($script:CompilerScratch.CleanupError -like '*identity or private access changed*') 'Cleanup failed at unrelated boundary'
            }
            'live-lease' {
                $context=New-StagingCompilerContext;$renamed=$context.Path+'-renamed';$nativeError=$null
                try{[IO.Directory]::Move($context.Path,$renamed)}catch{$nativeError=$_.Exception.InnerException.HResult -band 0xffff}
                Assert-Control ($nativeError -eq 32) 'Compiler root lease did not deny live rename with sharing violation'
                $context.RootLease.Handle.Dispose();[IO.Directory]::Move($context.Path,$renamed);[IO.Directory]::Move($renamed,$context.Path)
                $context.RootLease=Open-CompilerDirectoryLease $context.Path $context.Sid ''
                Assert-Control ($context.RootLease.Facts.Identity -ceq $context.Identity -and $context.RootLease.Facts.Private) 'After-release rename changed compiler identity/access'
                Clear-StagingCompilerContext $context $false
                Assert-Control ($context.Status -ceq 'retained-compilation-failed') 'Uncompiled native context was deleted'
                $observation.heldRenameError=$nativeError;$observation.afterReleaseRename=$true
            }
            'healthy' {
                Initialize-Staging
                Assert-Control ($script:compilerCalls.Count -eq 1 -and $script:CompilerScratch.Status -ceq 'closed' -and -not [IO.Directory]::Exists($script:CompilerScratch.Path)) 'Healthy private compiler scratch did not clean up'
                $path=New-OwnedStagingFile $script:StagingAttempt.Scratch.Path 'healthy-consumer.txt'
                [IO.File]::WriteAllText($path,'actual native staging consumer')
                $proof=Get-StagedFileDigest $path
                Assert-Control ($proof.Hash -ceq (Hash $path)) 'Native normal staging consumer failed'
                $observation.stagingScratch=$script:StagingAttempt.Scratch.Path;$observation.retained=$script:StagingAttempt.Retained.Path
                Clear-OwnedScratch
                Assert-Control (-not [IO.Directory]::Exists($observation.stagingScratch) -and [IO.Directory]::Exists($observation.retained)) 'Ordinary staging cleanup/retained lifetime changed'
            }
            default{throw 'Unknown controlled child case'}
        }
        Assert-Control ($env:TEMP -ceq $temporary -and $env:TMP -ceq $temporary) 'Actual initializer did not restore both temporary variables'
        $pass=$true
    }catch{$reason=$_.Exception.Message}
    $result=[pscustomobject]@{case=$InternalCase;pass=$pass;pass_=$pass;status=if($pass){'PASS'}else{'FAIL'};error=$reason;expectedFailure=$expectedFailure;sourceSha256=(Hash $SourceFile);host=$PSVersionTable.PSVersion.ToString();nativeWindows=$true;fixture=$root;compiler=(Context-Observation $script:CompilerScratch);compilerCalls=$script:compilerCalls;observation=$observation;messages=$script:messages;restoredTemp=$env:TEMP;restoredTmp=$env:TMP}
    [IO.File]::WriteAllText($CaseResult,($result|ConvertTo-Json -Depth 12),$Utf8)
    if(-not $pass){exit 1};exit 0
}

$sourceHash=Hash $SourceFile;$testHash=Hash $PSCommandPath
if([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT){
    [pscustomobject]@{schema='r0015-compiler-custody.native.v1';pass=$false;pass_=$false;sourceSha256=$sourceHash;testSha256=$testHash;nativeWindows=$false;results=@([pscustomobject]@{case='actual native Windows compiler custody';pass=$false;status='BLOCKED_NATIVE_HOST';error='No native Windows host; no modeled ACL or compiler substitute credited.'})}|ConvertTo-Json -Depth 5
    exit 2
}
$root=Join-Path ([IO.Path]::GetFullPath($FixtureParent)) ('r0015-compiler-custody-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
$script:allowedRoot=$root;$script:subjectSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
Set-OwnedDirectory $root
$frozen=Join-Path $root 'source.ps1';[IO.File]::WriteAllBytes($frozen,[IO.File]::ReadAllBytes($SourceFile))
$hostPath=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
function Invoke-ControlChild([string]$Name,[string]$InputSource,[string]$Label){
    $control=Join-Path $root $Label;[void][IO.Directory]::CreateDirectory($control);Set-OwnedDirectory $control
    $resultPath=Join-Path $control 'result.json'
    $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$hostPath
    $info.Arguments='-NoProfile -File "'+$PSCommandPath+'" -SourceFile "'+$InputSource+'" -InternalCase '+$Name+' -InternalRoot "'+$control+'" -CaseResult "'+$resultPath+'"'
    $info.UseShellExecute=$false;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true;$info.WorkingDirectory=$control
    $info.EnvironmentVariables['PSModuleAnalysisCachePath']=Join-Path $control 'module-cache';$info.EnvironmentVariables['DOTNET_CLI_HOME']=$control
    $child=[Diagnostics.Process]::new();$child.StartInfo=$info;[void]$child.Start();$child.StandardInput.Close()
    $stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync()
    $timedOut=-not $child.WaitForExit($ChildTimeoutSeconds*1000)
    if($timedOut){try{$child.Kill()}catch{};[void]$child.WaitForExit(5000)}
    $drainedOut=$stdout.Wait(2000);$drainedError=$stderr.Wait(2000)
    [IO.File]::WriteAllText((Join-Path $control 'stdout.txt'),$(if($drainedOut){$stdout.Result}else{''}),$Utf8)
    [IO.File]::WriteAllText((Join-Path $control 'stderr.txt'),$(if($drainedError){$stderr.Result}else{''}),$Utf8)
    if($timedOut -or -not $drainedOut -or -not $drainedError -or -not [IO.File]::Exists($resultPath)){return [pscustomobject]@{case=$Label;pass=$false;status='BOOTSTRAP_BLOCKED';timedOut=$timedOut;stdoutDrained=$drainedOut;stderrDrained=$drainedError;fixture=$control}}
    $observed=[IO.File]::ReadAllText($resultPath)|ConvertFrom-Json
    Assert-Control ($observed.sourceSha256 -ceq (Hash $InputSource)) 'Child receipt source binding differs'
    [pscustomobject]@{case=$Label;pass=($observed.pass -and $child.ExitCode -eq 0);status=if($observed.pass -and $child.ExitCode -eq 0){'PASS'}else{'FAIL'};exit=$child.ExitCode;observation=$observed;fixture=$control}
}
$results=[Collections.Generic.List[object]]::new()
foreach($name in @('foreign-parent','foreign-ancestor','exclusive-collision','compile-failure','cleanup-identity-failure','live-lease','healthy')){$results.Add((Invoke-ControlChild $name $frozen ('base-'+$name)))}
$mutant=Join-Path $root 'mutant-terminal-parent.ps1';$text=[IO.File]::ReadAllText($frozen)
$anchor="if (-not `$last.TrustedParent) { throw 'Compiler parent is not owned by this user with trusted write access.' }"
Assert-Control ([regex]::Matches($text,[regex]::Escape($anchor)).Count -eq 1) 'Terminal-parent mutation anchor drift'
[IO.File]::WriteAllText($mutant,$text.Replace($anchor,'# Controlled mutant: compiler terminal-parent admission omitted.'),$Utf8)
$t=$null;$e=$null;[void][Management.Automation.Language.Parser]::ParseFile($mutant,[ref]$t,[ref]$e)
Assert-Control (@($e).Count -eq 0) 'Mutant source does not parse'
$negative=Invoke-ControlChild 'foreign-parent' $mutant 'mutant-terminal-parent'
$positive=Invoke-ControlChild 'healthy' $mutant 'mutant-healthy'
$baseline=@($results|Where-Object{$_.case -eq 'base-foreign-parent'})[0]
$killed=$baseline.pass -and $negative.status -eq 'FAIL' -and $negative.observation.error -like 'Compiler parent was accepted*' -and @($negative.observation.compilerCalls).Count -eq 1 -and $positive.pass
$results.Add([pscustomobject]@{case='terminal-parent admission mutant with useful healthy caller';pass=$killed;status=if($killed){'PASS'}elseif($negative.status -eq 'BOOTSTRAP_BLOCKED' -or $positive.status -eq 'BOOTSTRAP_BLOCKED'){'BOOTSTRAP_BLOCKED'}else{'FAIL'};mutantSha256=(Hash $mutant);adverse=$negative;healthy=$positive})
$stable=(Hash $SourceFile) -ceq $sourceHash -and (Hash $PSCommandPath) -ceq $testHash
$report=[pscustomobject]@{schema='r0015-compiler-custody.native.v1';pass=($stable -and @($results|Where-Object{-not $_.pass}).Count -eq 0);pass_=($stable -and @($results|Where-Object{-not $_.pass}).Count -eq 0);nativeWindows=$true;host=$PSVersionTable.PSVersion.ToString();sourceSha256=$sourceHash;testSha256=$testHash;inputsStable=$stable;fixture=$root;results=$results.ToArray();scope='Actual cold Windows5.1/7 functions, native ACL/identity/lease and compiler effects; local disposable roots only. Observer of whole TEMP output remains a separate receipt.'}
$json=$report|ConvertTo-Json -Depth 16;[IO.File]::WriteAllText((Join-Path $root 'results.json'),$json,$Utf8);[Console]::WriteLine($json)
if(-not $report.pass){exit 1}
