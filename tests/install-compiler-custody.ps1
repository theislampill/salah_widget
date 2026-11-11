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
function Hash-Text([string]$Text){$h=[Security.Cryptography.SHA256]::Create();try{return [BitConverter]::ToString($h.ComputeHash($Utf8.GetBytes($Text))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
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
    [pscustomobject]@{id=$Context.Id;status=$Context.Status;path=$Context.Path;identity=$Context.Identity;sid=$Context.Sid;defaultOwnerSid=$Context.DefaultOwnerSid;invocationStarted=$Context.InvocationStarted;compilerExitCode=$Context.CompilerExitCode;created=$Context.Created;cleanupError=$Context.CleanupError;rootLeaseClosed=if($Context.RootLease){$Context.RootLease.Handle.IsClosed}else{$null};parentLeaseCount=@($Context.Leases).Count;parentLeasesClosed=@($Context.Leases|ForEach-Object{$_.Handle.IsClosed})}
}

if($InternalCase){
    $script:allowedRoot=[IO.Path]::GetFullPath($InternalRoot).TrimEnd('\')+'\'
    $script:subjectSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $root=Join-Path $InternalRoot $InternalCase
    [void][IO.Directory]::CreateDirectory($root);Set-OwnedDirectory $root
    $temporary=Join-Path $root 'temp';$profile=Join-Path $root 'profile'
    foreach($path in @($temporary,$profile)){[void][IO.Directory]::CreateDirectory($path);Set-OwnedDirectory $path}
    $env:TEMP=$temporary;$env:TMP=$temporary;$env:USERPROFILE=$profile
    $script:DryRun=$false;$script:StagingAttempt=$null;$script:CompilerScratch=$null;$script:compilerCalls=@();$script:managedCompilerCalls=@();$script:messages=@()
    $t=$null;$e=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$t,[ref]$e)
    Assert-Control (@($e).Count -eq 0) 'Source does not parse'
    foreach($definition in $ast.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){. ([scriptblock]::Create($definition.Extent.Text))}
    function Write-Host {param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline);$script:messages += [string]$Object}
    function Invoke-WebRequest {throw 'Unexpected network request'}
    function Invoke-RestMethod {throw 'Unexpected metadata request'}
    function Read-Host {throw 'Unexpected prompt'}
    function Add-Type {
        [CmdletBinding()]
        param([string]$TypeDefinition,[string[]]$AssemblyName)
        if($AssemblyName){Microsoft.PowerShell.Utility\Add-Type -AssemblyName $AssemblyName;return}
        $call=[pscustomobject]@{sourceSha256=(Hash-Text $TypeDefinition);returned=$false;errorId=$null;errorMessage=$null}
        $script:managedCompilerCalls += $call
        try{Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -ErrorAction Stop;$call.returned=$true}
        catch{$call.errorId=$_.FullyQualifiedErrorId;$call.errorMessage=$_.Exception.Message;throw}
    }
    $script:actualCompiler=${function:Invoke-StagingCompiler}
    function Invoke-StagingCompiler([string]$NativeSource,$Context) {
        $context=$Context
        Assert-Control ([object]::ReferenceEquals($context,$script:CompilerScratch)) 'Compiler invocation received a different context object'
        Assert-Control ($null -ne $context -and $context.Created -and $context.Identity -and $context.RootLease.Facts.Private -and -not $context.RootLease.Handle.IsClosed) 'Compiler reached before owned root identity/private lease'
        Assert-Control (@($context.Leases|Where-Object{$_.Handle.IsClosed}).Count -eq 0) 'Ancestor leases closed before compiler call'
        Assert-Control ($env:TEMP -ceq $context.Path -and $env:TMP -ceq $context.Path -and [IO.Path]::GetTempPath().TrimEnd('\') -ceq $context.Path.TrimEnd('\')) 'Compiler temporary paths are not the owned root'
        Assert-Control ($context.DefaultOwnerSid -ceq [Security.Principal.WindowsIdentity]::GetCurrent().Owner.Value) 'Compiler context did not capture the actual token default owner'
        $script:compilerCalls += [pscustomobject]@{path=$context.Path;identity=$context.Identity;owner=$context.RootLease.Facts.Owner;defaultOwnerSid=$context.DefaultOwnerSid;private=$context.RootLease.Facts.Private;nativeTemp=[IO.Path]::GetTempPath();temp=$env:TEMP;tmp=$env:TMP;parentLeases=@($context.Leases).Count;sameContext=$true}
        if($InternalCase -eq 'compile-failure'){$NativeSource += "`n deliberately invalid compiler input !"}
        $script:compilerSuppliedSource=$NativeSource
        & $script:actualCompiler $NativeSource $Context
    }
    # Test-owned interventions run only after the actual compiler returned and
    # Initialize-StagingNative marked its context compiled. Cleanup is delegated.
    function Install-CleanupSecurityControl([string]$Mode) {
        $script:cleanupSecurityMode=$Mode
        $script:cleanupSecurity=$null
        $script:securityActualClear=${function:Clear-StagingCompilerContext}
        function script:Clear-StagingCompilerContext($Context,[bool]$Compiled) {
            if(-not $Compiled){& $script:securityActualClear $Context $Compiled;return}
            Assert-Control ($Context.Status -ceq 'compiled' -and $Context.InvocationStarted -and ('SalahInstaller.StageNative' -as [type])) 'Cleanup intervention did not follow actual successful compilation'
            Assert-Control ([object]::ReferenceEquals($Context,$script:CompilerScratch) -and -not $Context.RootLease.Handle.IsClosed) 'Cleanup intervention lost its actual live context'
            Assert-Control ($null -eq $script:cleanupSecurity) 'Cleanup intervention ran more than once'
            $script:cleanupSecurity=[ordered]@{mode=$script:cleanupSecurityMode;compiled=$Compiled;delegateCalls=0;delegateReturned=$false;defaultOwnerSid=$Context.DefaultOwnerSid;defaultOwnerDiffersFromUser=($Context.DefaultOwnerSid -cne $Context.Sid);generatedBeforeInjection=@();injected=$null;outside=$null;rootExistsAfter=$null;statusAfter=$null}
            $observation.cleanupSecurity=$script:cleanupSecurity
            foreach($entry in [IO.Directory]::EnumerateFiles($Context.Path)){
                $facts=[SalahInstaller.StageNative]::Inspect($entry,$Context.Sid)
                $script:cleanupSecurity.generatedBeforeInjection += [pscustomobject]@{path=$facts.Path;owner=$facts.Owner;writeRestricted=$facts.WriteRestricted;identity=$facts.Identity;links=$facts.Links;length=$facts.Length}
            }
            $child=Join-Path $Context.Path 'control.dat'
            if($script:cleanupSecurityMode -in @('foreign-write-data','healthy-default-owner')){
                $bytes=$Utf8.GetBytes('owned cleanup control '+[guid]::NewGuid().ToString('N'))
                $writer=[IO.FileStream]::new($child,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
                try{$writer.Write($bytes,0,$bytes.Length)}finally{$writer.Dispose()}
                if($script:cleanupSecurityMode -eq 'foreign-write-data'){
                    $acl=[Security.AccessControl.FileSecurity]::new();$acl.SetOwner($script:subjectSid);$acl.SetAccessRuleProtection($true,$false)
                    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($script:subjectSid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow))
                    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-1-0'),[Security.AccessControl.FileSystemRights]2,[Security.AccessControl.AccessControlType]::Allow))
                    Set-Acl -LiteralPath $child -AclObject $acl
                    $readAcl=Get-Acl -LiteralPath $child
                    $world=@($readAcl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier])|Where-Object{$_.IdentityReference.Value -ceq 'S-1-1-0' -and $_.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow})
                    Assert-Control ($world.Count -eq 1 -and [int]$world[0].FileSystemRights -in @(2,1048578)) 'WriteData-only fixture ACE was not installed (Synchronize is permitted)'
                }
                $facts=[SalahInstaller.StageNative]::Inspect($child,$Context.Sid)
                $script:cleanupSecurity.injected=[pscustomobject]@{path=$child;sha256=(Hash $child);identity=$facts.Identity;owner=$facts.Owner;links=$facts.Links;writeRestricted=$facts.WriteRestricted;worldAllowMask=if($script:cleanupSecurityMode -eq 'foreign-write-data'){[int]$world[0].FileSystemRights}else{$null}}
                Assert-Control (-not $facts.Directory -and $facts.Links -eq 1) 'Cleanup control is not a fresh ordinary single-link file'
                if($script:cleanupSecurityMode -eq 'healthy-default-owner'){
                    Assert-Control ($facts.Owner -ceq $Context.DefaultOwnerSid -and $facts.WriteRestricted) 'Generated default-owner control lacks actual safe native readback'
                    if($PSVersionTable.PSVersion.Major -eq 5){
                        $dll=@($script:cleanupSecurity.generatedBeforeInjection|Where-Object{[IO.Path]::GetFileName($_.path) -ceq 'native.dll'})
                        Assert-Control ($dll.Count -eq 1 -and $dll[0].owner -ceq $Context.DefaultOwnerSid -and $dll[0].writeRestricted -and $dll[0].links -eq 1 -and $dll[0].length -gt 0) 'Actual Framework compiler DLL lacks captured-default-owner evidence'
                    }
                }
            }elseif($script:cleanupSecurityMode -in @('hardlink','junction')){
                $outside=Join-Path $root 'outside-compiler';Assert-Control (-not [IO.Directory]::Exists($outside)) 'Outside sentinel root was not fresh'
                [void][IO.Directory]::CreateDirectory($outside);Set-OwnedDirectory $outside
                $sentinel=Join-Path $outside 'sentinel.bin';$bytes=$Utf8.GetBytes('outside-context sentinel '+[guid]::NewGuid().ToString('N'))
                $writer=[IO.FileStream]::new($sentinel,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
                try{$writer.Write($bytes,0,$bytes.Length)}finally{$writer.Dispose()}
                $outsideFacts=[SalahInstaller.StageNative]::Inspect($outside,$Context.Sid)
                $sentinelFacts=[SalahInstaller.StageNative]::Inspect($sentinel,$Context.Sid)
                Assert-Control ($outsideFacts.Private -and $sentinelFacts.Links -eq 1) 'Outside sentinel did not start as an owned private fixture'
                $script:cleanupSecurity.outside=[pscustomobject]@{path=$outside;identity=$outsideFacts.Identity;sentinel=$sentinel;sentinelIdentity=$sentinelFacts.Identity;sha256=(Hash $sentinel)}
                if($script:cleanupSecurityMode -eq 'hardlink'){
                    New-Item -ItemType HardLink -Path $child -Target $sentinel -ErrorAction Stop | Out-Null
                    $linked=[SalahInstaller.StageNative]::Inspect($sentinel,$Context.Sid)
                    Assert-Control ($linked.Identity -ceq $sentinelFacts.Identity -and $linked.Links -eq 2 -and (Hash $child) -ceq $script:cleanupSecurity.outside.sha256) 'Hardlink setup did not produce two names for the owned sentinel'
                    $script:cleanupSecurity.injected=[pscustomobject]@{path=$child;kind='hardlink';sentinelLinks=$linked.Links;sentinelIdentity=$linked.Identity}
                }else{
                    New-Item -ItemType Junction -Path $child -Target $outside -ErrorAction Stop | Out-Null
                    $attributes=[IO.File]::GetAttributes($child)
                    Assert-Control (($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -and (Hash (Join-Path $child 'sentinel.bin')) -ceq $script:cleanupSecurity.outside.sha256) 'Junction setup did not resolve to the owned outside sentinel'
                    $script:cleanupSecurity.injected=[pscustomobject]@{path=$child;kind='junction';attributes=[string]$attributes;target=@((Get-Item -LiteralPath $child -Force).Target)}
                }
            }else{throw 'Unknown cleanup security intervention'}
            # Do not assert the policy under test before this actual cleanup call.
            $script:cleanupSecurity.delegateCalls++
            & $script:securityActualClear $Context $Compiled
            $script:cleanupSecurity.delegateReturned=$true
            $script:cleanupSecurity.rootExistsAfter=[IO.Directory]::Exists($Context.Path)
            $script:cleanupSecurity.statusAfter=$Context.Status
        }
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
                if($PSVersionTable.PSVersion.Major -eq 5){
                    $sourcePath=Join-Path $script:CompilerScratch.Path 'native.cs'
                    $diagnostics=@('compiler.stdout.bin','compiler.stderr.bin'|ForEach-Object{Join-Path $script:CompilerScratch.Path $_})
                    $diagnosticRows=@($diagnostics|Where-Object{[IO.File]::Exists($_)}|ForEach-Object{[pscustomobject]@{path=$_;length=[IO.FileInfo]::new($_).Length;sha256=(Hash $_)}})
                    $sourceMatches=[IO.File]::Exists($sourcePath) -and [IO.File]::ReadAllText($sourcePath) -ceq $script:compilerSuppliedSource
                    $observation.compilerFailureEvidence=[pscustomobject]@{exit=$script:CompilerScratch.CompilerExitCode;sourceMatches=$sourceMatches;sourceSha256=if([IO.File]::Exists($sourcePath)){Hash $sourcePath}else{$null};diagnostics=$diagnosticRows}
                    Assert-Control ($null -ne $script:CompilerScratch.CompilerExitCode -and $script:CompilerScratch.CompilerExitCode -ne 0 -and $sourceMatches -and $diagnosticRows.Count -eq 2 -and ($diagnosticRows|Measure-Object -Property length -Sum).Sum -gt 0) 'Failure was not an actual nonzero Framework compiler result with retained input/diagnostics'
                }else{
                    $observation.compilerFailureEvidence=$script:managedCompilerCalls
                    Assert-Control ($script:managedCompilerCalls.Count -eq 1 -and -not $script:managedCompilerCalls[0].returned -and $script:managedCompilerCalls[0].errorId -ceq 'SOURCE_CODE_ERROR,Microsoft.PowerShell.Commands.AddTypeCommand' -and $script:managedCompilerCalls[0].sourceSha256 -ceq (Hash-Text $script:compilerSuppliedSource)) 'Failure was not the actual Add-Type compiler syntax diagnostic'
                }
                $lease=Open-CompilerDirectoryLease $script:CompilerScratch.Path $script:subjectSid.Value ''
                try{Assert-Control ($lease.Facts.Private -and $lease.Facts.Identity -ceq $script:CompilerScratch.Identity) 'Retained compiler root lost private identity'}finally{$lease.Handle.Dispose()}
                $observation.retainedFiles=@(Get-ChildItem -LiteralPath $script:CompilerScratch.Path -Recurse -Force|ForEach-Object{[pscustomobject]@{path=$_.FullName;attributes=[string]$_.Attributes;sha256=if(-not $_.PSIsContainer){Hash $_.FullName}else{$null}}})
            }
            'cleanup-write-data' {
                Install-CleanupSecurityControl 'foreign-write-data'
                Initialize-StagingNative
                $observation.cleanupSecurity=$script:cleanupSecurity
                Assert-Control ($script:cleanupSecurity.compiled -and $script:cleanupSecurity.delegateCalls -eq 1 -and $script:cleanupSecurity.delegateReturned -and $script:compilerCalls.Count -eq 1) 'WriteData control did not delegate actual post-compilation cleanup'
                Assert-Control ($script:CompilerScratch.Status -ceq 'retained-cleanup-failed' -and [IO.Directory]::Exists($script:CompilerScratch.Path)) 'Foreign WriteData cleanup was accepted or failed before the actual refusal'
                Assert-Control ($script:CompilerScratch.CleanupError -like '*Compiler output custody could not be proved*') 'Foreign WriteData cleanup failed at an unrelated boundary'
                Assert-Control ((Hash $script:cleanupSecurity.injected.path) -ceq $script:cleanupSecurity.injected.sha256) 'Refused cleanup changed its WriteData control bytes'
            }
            {$_ -in @('cleanup-hardlink','cleanup-junction')} {
                $mode=if($InternalCase -eq 'cleanup-hardlink'){'hardlink'}else{'junction'}
                Install-CleanupSecurityControl $mode
                Initialize-StagingNative
                $observation.cleanupSecurity=$script:cleanupSecurity
                Assert-Control ($script:cleanupSecurity.compiled -and $script:cleanupSecurity.delegateCalls -eq 1 -and $script:cleanupSecurity.delegateReturned -and $script:compilerCalls.Count -eq 1) 'Link control did not delegate actual post-compilation cleanup'
                Assert-Control ($script:CompilerScratch.Status -ceq 'retained-cleanup-failed' -and [IO.Directory]::Exists($script:CompilerScratch.Path)) 'Link cleanup did not retain the refused context'
                $failure=$script:CompilerScratch.CleanupError
                if($mode -eq 'hardlink'){Assert-Control ($failure -like '*Compiler output custody could not be proved*' -or $failure -like '*Aliased staging path refused*') 'Hardlink cleanup failed at an unrelated boundary'}
                else{Assert-Control ($failure -like '*Reparse or non-disk staging object refused*') 'Junction cleanup failed at an unrelated boundary'}
                $outside=$script:cleanupSecurity.outside
                Assert-Control ((Hash $outside.sentinel) -ceq $outside.sha256) 'Refused cleanup changed outside-context sentinel bytes'
                $after=[SalahInstaller.StageNative]::Inspect($outside.path,$script:CompilerScratch.Sid)
                $sentinel=[SalahInstaller.StageNative]::Inspect($outside.sentinel,$script:CompilerScratch.Sid)
                Assert-Control ($after.Identity -ceq $outside.identity -and $after.Private -and $sentinel.Identity -ceq $outside.sentinelIdentity) 'Refused cleanup changed outside-context sentinel identity/private parent'
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
                Install-CleanupSecurityControl 'healthy-default-owner'
                Initialize-Staging
                $observation.cleanupSecurity=$script:cleanupSecurity
                Assert-Control ($script:cleanupSecurity.compiled -and $script:cleanupSecurity.delegateCalls -eq 1 -and $script:cleanupSecurity.delegateReturned -and $script:cleanupSecurity.statusAfter -ceq 'closed' -and $script:cleanupSecurity.rootExistsAfter -eq $false) 'Healthy default-owner cleanup did not reach the actual successful cleanup'
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
foreach($name in @('foreign-parent','foreign-ancestor','exclusive-collision','compile-failure','cleanup-identity-failure','cleanup-write-data','cleanup-hardlink','cleanup-junction','live-lease','healthy')){$results.Add((Invoke-ControlChild $name $frozen ('base-'+$name)))}
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
# This single literal belongs to actual StageNative.Read, which actual cleanup
# calls. The separate PowerShell compiler-output reader remains unchanged.
$writeMutant=Join-Path $root 'mutant-cleanup-write-mask.ps1'
$writeAnchor='if (allowed && !inheritOnly && (mask & 0x500d0156u) != 0 && principal != sid && principal != "S-1-5-18" && principal != "S-1-5-32-544") { parentSafe = false; writeRestricted = false; }'
$writeReplacement=$writeAnchor.Replace('0x500d0156u','0x500d0150u')
Assert-Control ([regex]::Matches($text,[regex]::Escape($writeAnchor)).Count -eq 1) 'Cleanup full-write-predicate mutation anchor drift'
[IO.File]::WriteAllText($writeMutant,$text.Replace($writeAnchor,$writeReplacement),$Utf8)
$t=$null;$e=$null;[void][Management.Automation.Language.Parser]::ParseFile($writeMutant,[ref]$t,[ref]$e)
Assert-Control (@($e).Count -eq 0) 'Cleanup write-mask mutant source does not parse'
$writeNegative=Invoke-ControlChild 'cleanup-write-data' $writeMutant 'mutant-cleanup-write-mask'
$writePositive=Invoke-ControlChild 'healthy' $writeMutant 'mutant-write-mask-healthy'
$writeBaseline=@($results|Where-Object{$_.case -eq 'base-cleanup-write-data'})[0]
$writeKilled=$writeBaseline.pass -and $writeNegative.status -eq 'FAIL' -and $writeNegative.observation.error -like 'Foreign WriteData cleanup was accepted*' -and @($writeNegative.observation.compilerCalls).Count -eq 1 -and $writeNegative.observation.compiler.status -ceq 'closed' -and $writeNegative.observation.observation.cleanupSecurity.delegateCalls -eq 1 -and $writeNegative.observation.observation.cleanupSecurity.delegateReturned -eq $true -and $writeNegative.observation.observation.cleanupSecurity.rootExistsAfter -eq $false -and $writePositive.pass
$results.Add([pscustomobject]@{case='cleanup full-write predicate mutant with useful healthy caller';pass=$writeKilled;status=if($writeKilled){'PASS'}elseif($writeNegative.status -eq 'BOOTSTRAP_BLOCKED' -or $writePositive.status -eq 'BOOTSTRAP_BLOCKED'){'BOOTSTRAP_BLOCKED'}else{'FAIL'};mutantSha256=(Hash $writeMutant);adverse=$writeNegative;healthy=$writePositive})

$stable=(Hash $SourceFile) -ceq $sourceHash -and (Hash $PSCommandPath) -ceq $testHash
$report=[pscustomobject]@{schema='r0015-compiler-custody.native.v1';pass=($stable -and @($results|Where-Object{-not $_.pass}).Count -eq 0);pass_=($stable -and @($results|Where-Object{-not $_.pass}).Count -eq 0);nativeWindows=$true;host=$PSVersionTable.PSVersion.ToString();sourceSha256=$sourceHash;testSha256=$testHash;inputsStable=$stable;fixture=$root;results=$results.ToArray();scope='Actual cold Windows5.1/7 functions, native ACL/identity/lease and compiler effects; local disposable roots only. Observer of whole TEMP output remains a separate receipt.'}
$json=$report|ConvertTo-Json -Depth 16;[IO.File]::WriteAllText((Join-Path $root 'results.json'),$json,$Utf8);[Console]::WriteLine($json)
if(-not $report.pass){exit 1}
