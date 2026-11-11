param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$FixtureParent=[IO.Path]::GetTempPath(),
    [string[]]$Case
)

# Native Windows custody controls. No POSIX/ACL model adapter is permitted here.
# Every mutation is confined to a new disposable fixture; no real profile runs.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$script:results=@()
$script:notes=[ordered]@{}
$script:messages=@()
$script:creates=@()
$script:fixtureRoot=$null
$script:StagingAttempt=$null
$script:oldTemp=$env:TEMP
$script:oldProfile=$env:USERPROFILE
$script:utf8=New-Object Text.UTF8Encoding $false
$script:sourceHash=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
$script:nativeHost=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT

function Assert-Native($Condition,[string]$Message) { if(-not $Condition){throw $Message} }
function Assert-FixtureBoundary([string]$Path) {
    $prefix=$script:fixtureRoot.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
    Assert-Native ([IO.Path]::GetFullPath($Path).StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) 'Fixture write escaped its disposable root.'
}
function Invoke-NativeCase([string]$Name,[scriptblock]$Body) {
    if($Case -and $Name -notin $Case){return}
    $script:notes=[ordered]@{}; $script:messages=@(); $pass=$false; $errorText=$null
    try { & $Body; $pass=$true } catch {$errorText=$_.Exception.Message}
    $script:results += [pscustomobject]@{case=$Name;pass_=$pass;pass=$pass;status=$(if($pass){'PASS'}else{'FAIL'});error=$errorText;observations=$script:notes;messages=@($script:messages)}
}
function Set-FixtureDirectoryAcl([string]$Path,[Security.AccessControl.FileSystemRights]$ExtraRights=0) {
    Assert-FixtureBoundary $Path
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($script:subjectSid); $acl.SetAccessRuleProtection($true,$false)
    $rule=New-Object Security.AccessControl.FileSystemAccessRule($script:subjectSid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
    $acl.AddAccessRule($rule)
    if([int]$ExtraRights -ne 0) {
        $everyone=New-Object Security.Principal.SecurityIdentifier 'S-1-1-0'
        $extra=New-Object Security.AccessControl.FileSystemAccessRule($everyone,$ExtraRights,[Security.AccessControl.InheritanceFlags]::None,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($extra)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
function New-NativeFixture([string]$Name) {
    if($script:StagingAttempt) { $script:DryRun=$false; Clear-OwnedScratch; $script:StagingAttempt=$null }
    $root=Join-Path $script:fixtureRoot $Name
    [void][IO.Directory]::CreateDirectory($root)
    Set-FixtureDirectoryAcl $root
    $tempParent=Join-Path $root 'temp'
    $profileParent=Join-Path $root 'profile'
    foreach($parent in @($tempParent,$profileParent)) { [void][IO.Directory]::CreateDirectory($parent); Set-FixtureDirectoryAcl $parent }
    $env:TEMP=$tempParent; $env:USERPROFILE=$profileParent
    $script:DryRun=$false; $script:WorkRoot=$null; $script:DownloadRoot=$null; $script:PresetRoot=$null
    $script:creates=@()
    $script:notes.fixture=$root
    return [pscustomobject]@{Root=$root;Temp=$tempParent;Profile=$profileParent}
}
function Get-CustodyObservation([string]$Path) {
    $facts=Get-StagingPathInfo $Path
    $acl=Get-Acl -LiteralPath $Path
    return [pscustomobject]@{
        path=$Path;identity=$facts.Identity;owner=$facts.Owner;private=$facts.Private;trustedParent=$facts.TrustedParent;
        trustedAncestor=$facts.TrustedAncestor;protected=$acl.AreAccessRulesProtected;sddl=$acl.Sddl;
        filesystem=(New-Object IO.DriveInfo([IO.Path]::GetPathRoot($Path))).DriveFormat
    }
}

try {
    $raw=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
    $tokens=$null; $errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($raw,[ref]$tokens,[ref]$errors)
    if(@($errors).Count){throw 'SETUP: source does not parse.'}
    foreach($definition in $ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}) {
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    function Write-Host {
        param([Parameter(Position=0,ValueFromRemainingArguments=$true)][object[]]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[string]$Separator=' ',[switch]$NoNewline)
        $script:messages += (($Object|ForEach-Object{[string]$_}) -join $Separator)
    }
    function Invoke-WebRequest {throw 'Unexpected network request in native custody control.'}
    function Invoke-RestMethod {throw 'Unexpected metadata request in native custody control.'}
    function Copy-Text {throw 'Unexpected clipboard effect in native custody control.'}
    function Open-TargetUrl {throw 'Unexpected browser effect in native custody control.'}
    function Read-Host {throw 'Unexpected prompt in native custody control.'}

    if(-not $script:nativeHost) {
        $script:results += [pscustomobject]@{case='native Windows custody acquisition';pass_=$false;pass=$false;status='BLOCKED_NATIVE_HOST';error='Actual Windows ACL, SID, identity and lease controls require a Windows host; no simulation is substituted.'}
    } else {
        $script:subjectSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
        $fixtureName='r0015-native-'+[guid]::NewGuid().ToString('N')+'-'+[char]0x0635
        $script:fixtureRoot=Join-Path ([IO.Path]::GetFullPath($FixtureParent)) $fixtureName
        [void][IO.Directory]::CreateDirectory($script:fixtureRoot)
        $script:actualCreateDirectory=${function:New-PrivateStagingDirectory}
        $script:actualCreateFile=${function:New-PrivateStagingFile}
        function New-PrivateStagingDirectory([string]$Path) {
            if($DryRun){return (& $script:actualCreateDirectory $Path)}
            Assert-FixtureBoundary $Path
            $script:creates += [pscustomobject]@{kind='directory';path=$Path}
            return & $script:actualCreateDirectory $Path
        }
        function New-PrivateStagingFile([string]$Path) {
            if($DryRun){return (& $script:actualCreateFile $Path)}
            Assert-FixtureBoundary $Path
            $script:creates += [pscustomobject]@{kind='file';path=$Path}
            return & $script:actualCreateFile $Path
        }

        Invoke-NativeCase 'native private roots precede artifact writes' {
            $fixture=New-NativeFixture 'private-roots'
            Initialize-Staging
            $scratch=Get-CustodyObservation $script:StagingAttempt.Scratch.Path
            $retained=Get-CustodyObservation $script:StagingAttempt.Retained.Path
            $script:notes.scratch=$scratch; $script:notes.retained=$retained
            Assert-Native ($scratch.private -and $retained.private -and $scratch.protected -and $retained.protected) 'Initial roots do not have private protected ACLs.'
            Assert-Native ($scratch.owner -ceq $script:subjectSid.Value -and $retained.owner -ceq $script:subjectSid.Value) 'Initial owner is not the actual subject SID.'
            Assert-Native ($scratch.identity -cne $retained.identity) 'Scratch and retained roots share native identity.'
            Assert-Native (-not @($script:creates|Where-Object{$_.kind -eq 'file'}).Count) 'Artifact file was created before root ACL readback.'
            $path=New-OwnedStagingFile $scratch.path ('unicode-'+[char]0x0635+'.txt')
            [IO.File]::WriteAllText($path,'native positive bytes',$script:utf8)
            $proof=Get-StagedFileDigest $path
            Assert-Native ($proof.Hash -ceq (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()) 'Owned positive readback differs.'
            $refused=$false
            try {$null=Get-AdmittedArtifact $path 'asset'}catch{$refused=$true}
            Assert-Native $refused 'An owned file without semantic admission became a ready artifact.'
        }

        Invoke-NativeCase 'native exclusive creation never adopts existing objects' {
            $fixture=New-NativeFixture 'exclusive-collisions'
            Initialize-Staging
            $foreign=Join-Path $fixture.Root 'preexisting'
            [void][IO.Directory]::CreateDirectory($foreign)
            Set-FixtureDirectoryAcl $foreign ([Security.AccessControl.FileSystemRights]::ReadAndExecute)
            $sentinel=Join-Path $foreign 'sentinel.txt'
            [IO.File]::WriteAllText($sentinel,'foreign object must survive',$script:utf8)
            $beforeAcl=(Get-Acl -LiteralPath $foreign).Sddl
            $beforeFile=(Get-FileHash -LiteralPath $sentinel -Algorithm SHA256).Hash
            $directoryRefused=$false; $fileRefused=$false
            try {$null=New-PrivateStagingDirectory $foreign}catch{$directoryRefused=$true}
            try {$null=New-PrivateStagingFile $sentinel}catch{$fileRefused=$true}
            $script:notes.beforeAcl=$beforeAcl; $script:notes.afterAcl=(Get-Acl -LiteralPath $foreign).Sddl
            Assert-Native ($directoryRefused -and $fileRefused) 'Exclusive creation adopted a preexisting object.'
            Assert-Native ((Get-Acl -LiteralPath $foreign).Sddl -ceq $beforeAcl) 'Collision handling reset foreign directory ACLs.'
            Assert-Native ((Get-FileHash -LiteralPath $sentinel -Algorithm SHA256).Hash -ceq $beforeFile) 'Collision handling changed existing file bytes.'
        }

        Invoke-NativeCase 'native earlier ancestor replacement authority is refused with create-child positive' {
            $fixture=New-NativeFixture 'ancestor-authority'
            $ancestor=Join-Path $fixture.Root 'shared-ancestor'
            $profileParent=Join-Path $ancestor 'owned-profile'
            [void][IO.Directory]::CreateDirectory($ancestor); [void][IO.Directory]::CreateDirectory($profileParent)
            Set-FixtureDirectoryAcl $ancestor ([Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles)
            Set-FixtureDirectoryAcl $profileParent
            $env:USERPROFILE=$profileParent
            $rejected=$false; $reason=$null
            try {Initialize-Staging}catch{$rejected=$true;$reason=$_.Exception.Message}
            $negativeCreates=@($script:creates)
            $negative=Get-CustodyObservation $ancestor
            $script:notes.negative=[pscustomobject]@{rejected=$rejected;reason=$reason;ancestor=$negative;creates=$negativeCreates}
            if($script:StagingAttempt){Clear-OwnedScratch;$script:StagingAttempt=$null}
            # Same path/owner/native identity; change only the foreign ACL grant
            # from delete-child to harmless create-file/create-directory rights.
            Set-FixtureDirectoryAcl $ancestor ([Security.AccessControl.FileSystemRights]6)
            $script:creates=@()
            Initialize-Staging
            $positive=Get-CustodyObservation $ancestor
            $script:notes.positive=$positive
            Assert-Native ($negative.identity -ceq $positive.identity -and $negative.owner -ceq $positive.owner) 'Matched ancestry control changed object or owner.'
            Assert-Native ($rejected -and $negativeCreates.Count -eq 0) 'Foreign replacement authority on an earlier ancestor reached root creation.'
            Assert-Native (-not $negative.trustedAncestor -and $positive.trustedAncestor -and $script:StagingAttempt.Status -eq 'active') 'Ancestry policy did not distinguish replacement from create-child rights.'
        }

        Invoke-NativeCase 'native directory lease prevents live root replacement' {
            $fixture=New-NativeFixture 'live-lease'
            Initialize-Staging
            $scratch=$script:StagingAttempt.Scratch.Path
            $before=Get-CustodyObservation $scratch
            $proof=New-OwnedStagingFile $scratch 'lease-proof.txt'
            [IO.File]::WriteAllText($proof,'native lease positive bytes',$script:utf8)
            $script:notes.initialization=[pscustomobject]@{status=$script:StagingAttempt.Status;scratch=$before;proofHash=(Get-StagedFileDigest $proof).Hash}
            Assert-Native ($script:StagingAttempt.Status -eq 'active' -and $before.private) 'Healthy native initialization did not reach an owned artifact write.'
            $moved=Join-Path $fixture.Temp 'attempt-renamed'
            $refused=$false; $reason=$null; $nativeCode=$null
            try {[IO.Directory]::Move($scratch,$moved)}catch{
                $refused=$true; $cause=$_.Exception.GetBaseException(); $reason=$cause.Message
                $nativeCode=$cause.HResult -band 0xFFFF
            }
            $script:notes.rename=[pscustomobject]@{refused=$refused;reason=$reason;nativeCode=$nativeCode}
            Assert-Native $refused 'The held native root lease allowed replacement by rename.'
            Assert-Native ($nativeCode -eq 32) 'Live rename failed for a reason other than a native sharing violation.'
            Assert-Native ((Get-StagingPathInfo $scratch).Identity -ceq $before.identity) 'Live root identity changed.'
            Assert-Native (-not [IO.Directory]::Exists($moved)) 'The refused live rename created its destination.'

            # Change only the root lease lifetime. Parent leases and the same
            # root identity, ACL, proof bytes and rename destination remain.
            $rootLeases=@($script:StagingAttempt.Leases | Where-Object {$_.Facts.Path.Equals($scratch,[StringComparison]::OrdinalIgnoreCase)})
            Assert-Native ($rootLeases.Count -gt 0) 'The live root had no actual directory lease.'
            foreach($lease in $rootLeases){$lease.Dispose()}
            [IO.Directory]::Move($scratch,$moved)
            $after=Get-CustodyObservation $moved
            $movedProof=Join-Path $moved 'lease-proof.txt'
            $script:notes.afterDisposal=[pscustomobject]@{renamed=$true;rootLeaseCount=$rootLeases.Count;scratch=$after;proofHash=(Get-FileHash -LiteralPath $movedProof -Algorithm SHA256).Hash.ToLowerInvariant()}
            Assert-Native (-not [IO.Directory]::Exists($scratch) -and $after.identity -ceq $before.identity) 'Disposing the lease did not permit moving the same native root.'
            Assert-Native ($after.sddl -ceq $before.sddl -and $script:notes.afterDisposal.proofHash -ceq $script:notes.initialization.proofHash) 'Post-disposal rename changed ACLs or proof bytes.'
            [IO.Directory]::Move($moved,$scratch)
            [void]$script:StagingAttempt.Leases.Add((Open-StagingDirectoryLease $scratch))
            $script:notes.restored=[pscustomobject]@{path=$scratch;identity=(Get-StagingPathInfo $scratch).Identity}
        }

        Invoke-NativeCase 'native cleanup holds ancestors and retains fresh-consumer output' {
            $fixture=New-NativeFixture 'cleanup-and-consumer'
            Initialize-Staging
            $scratch=$script:StagingAttempt.Scratch.Path
            $retained=$script:StagingAttempt.Retained.Path
            $scratchFile=New-OwnedStagingFile $scratch 'scratch.txt'
            [IO.File]::WriteAllText($scratchFile,'owned scratch',$script:utf8)
            $retainedFile=New-OwnedStagingFile $retained ('retained-'+[char]0x0635+'.txt')
            [IO.File]::WriteAllText($retainedFile,'retained consumer bytes',$script:utf8)
            $disposals=New-Object 'System.Collections.Generic.List[object]'
            $leases=New-Object 'System.Collections.Generic.List[object]'
            foreach($native in $script:StagingAttempt.Leases) {
                $proxy=[pscustomobject]@{Native=$native;Facts=$native.Facts;Scratch=$scratch;Events=$disposals}
                $proxy|Add-Member -MemberType ScriptMethod -Name Dispose -Value {
                    [void]$this.Events.Add([pscustomobject]@{path=$this.Facts.Path;scratchExists=[IO.Directory]::Exists($this.Scratch)})
                    $this.Native.Dispose()
                }
                [void]$leases.Add($proxy)
            }
            $script:StagingAttempt.Leases=$leases
            Clear-OwnedScratch
            $script:notes.disposals=@($disposals.ToArray())
            Assert-Native (-not [IO.Directory]::Exists($scratch)) 'Owned native scratch survived successful cleanup.'
            Assert-Native (-not @($disposals|Where-Object{$_.path -cne $scratch -and $_.scratchExists}).Count) 'An ancestor/retained lease closed before scratch deletion.'
            $literal="'"+$retainedFile.Replace("'","''")+"'"
            $consumer='$p='+$literal+'; [pscustomobject]@{text=[IO.File]::ReadAllText($p,[Text.Encoding]::UTF8);sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()} | ConvertTo-Json -Compress'
            $encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($consumer))
            $hostExe=Join-Path $PSHOME $(if($PSVersionTable.PSEdition -eq 'Desktop'){'powershell.exe'}else{'pwsh.exe'})
            $readback=(& $hostExe -NoLogo -NoProfile -NonInteractive -EncodedCommand $encoded | Out-String)
            $consumerExit=$LASTEXITCODE
            $result=ConvertFrom-Json -InputObject $readback
            $script:notes.consumer=[pscustomobject]@{exit=$consumerExit;result=$result;retainedPath=$retainedFile}
            Assert-Native ($consumerExit -eq 0 -and $result.text -ceq 'retained consumer bytes') 'Fresh native consumer could not read retained output after cleanup.'
        }

        Invoke-NativeCase 'native cleanup refuses a replaced root identity' {
            $fixture=New-NativeFixture 'replaced-root'
            Initialize-Staging
            $scratch=$script:StagingAttempt.Scratch.Path
            $oldIdentity=$script:StagingAttempt.Scratch.Identity
            foreach($lease in $script:StagingAttempt.Leases){$lease.Dispose()}
            $displaced=Join-Path $fixture.Temp 'displaced-owned-attempt'
            [IO.Directory]::Move($scratch,$displaced)
            $replacement=New-PrivateStagingDirectory $scratch
            $sentinel=Join-Path $scratch 'replacement-sentinel.txt'
            [IO.File]::WriteAllText($sentinel,'replacement is not owned by the old attempt',$script:utf8)
            Assert-Native ($replacement.Identity -cne $oldIdentity) 'Native replacement did not change file identity.'
            Clear-OwnedScratch
            Assert-Native ([IO.File]::ReadAllText($sentinel,[Text.Encoding]::UTF8) -ceq 'replacement is not owned by the old attempt') 'Cleanup deleted or changed the replacement tree.'
            Assert-Native ([IO.Directory]::Exists($displaced)) 'Cleanup followed the displaced original root.'
            $script:notes.identities=[pscustomobject]@{original=$oldIdentity;replacement=$replacement.Identity;displaced=$displaced}
        }

        Invoke-NativeCase 'native junction child blocks writes and scratch cleanup' {
            $fixture=New-NativeFixture 'junction-child'
            Initialize-Staging
            $outside=Join-Path $fixture.Root 'outside'
            [void][IO.Directory]::CreateDirectory($outside)
            $sentinel=Join-Path $outside 'sentinel.txt'
            [IO.File]::WriteAllText($sentinel,'outside bytes unchanged',$script:utf8)
            $scratch=$script:StagingAttempt.Scratch.Path
            $junction=Join-Path $scratch 'junction'
            New-Item -ItemType Junction -Path $junction -Target $outside | Out-Null
            $refused=$false
            try {$null=New-OwnedStagingFile $junction 'must-not-write.txt'}catch{$refused=$true}
            Clear-OwnedScratch
            Assert-Native $refused 'Owned-path guard accepted a native junction parent.'
            Assert-Native (-not [IO.File]::Exists((Join-Path $outside 'must-not-write.txt'))) 'An artifact write followed the junction.'
            Assert-Native ([IO.File]::ReadAllText($sentinel,[Text.Encoding]::UTF8) -ceq 'outside bytes unchanged') 'Scratch cleanup followed a native junction.'
            Assert-Native ([IO.Directory]::Exists($scratch)) 'Cleanup did not retain the unproved tree.'
        }

        Invoke-NativeCase 'native next attempt preserves old retained bundle without admission' {
            $fixture=New-NativeFixture 'next-attempt'
            Initialize-Staging
            $firstId=$script:StagingAttempt.Id
            $oldRoot=$script:StagingAttempt.Retained.Path
            $oldFile=New-OwnedStagingFile $oldRoot 'old-manual-file.txt'
            [IO.File]::WriteAllText($oldFile,'older manual bundle',$script:utf8)
            Clear-OwnedScratch; $script:StagingAttempt=$null
            Initialize-Staging
            $secondId=$script:StagingAttempt.Id
            $refused=$false
            try {$null=Get-AdmittedArtifact $oldFile 'asset'}catch{$refused=$true}
            Assert-Native ($firstId -cne $secondId -and $oldRoot -cne $script:StagingAttempt.Retained.Path) 'A new attempt reused predecessor identity/path.'
            Assert-Native $refused 'Old retained file was adopted without current admission.'
            Assert-Native ([IO.File]::ReadAllText($oldFile,[Text.Encoding]::UTF8) -ceq 'older manual bundle') 'New initialization removed old manual output.'
            $script:notes.attempts=@($firstId,$secondId)
        }
    }
} catch {
    $script:results += [pscustomobject]@{case='native fixture/bootstrap';pass_=$false;pass=$false;status='SETUP_ERROR';error=$_.Exception.Message}
} finally {
    if($script:StagingAttempt) { $script:DryRun=$false; Clear-OwnedScratch }
    $env:TEMP=$script:oldTemp; $env:USERPROFILE=$script:oldProfile
}

[pscustomobject]@{
    schema='r0015-native-windows-custody-v1';source=$SourceFile;sourceSha256=$script:sourceHash;
    testSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();
    observedUtc=[DateTime]::UtcNow.ToString('o');runtime=$PSVersionTable.PSVersion.ToString();edition=$PSVersionTable.PSEdition;
    platform=[Environment]::OSVersion.ToString();subjectSid=$(if($script:nativeHost){$script:subjectSid.Value}else{$null});
    scope='actual Windows SID/ACL/native identity/directory leases in disposable fixtures; no real profile or browser installation';
    fixtureRoot=$script:fixtureRoot;retainedFixture=$true;results=@($script:results)
} | ConvertTo-Json -Depth 35
if(-not $script:nativeHost){exit 2}
if(-not $script:results.Count -or @($script:results|Where-Object{-not $_.pass_}).Count){exit 1}
exit 0
