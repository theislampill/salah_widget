param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$FixtureParent=[IO.Path]::GetTempPath(),
    [string[]]$Case,
    [string]$CaseList,
    [string]$ReportPath,
    [switch]$RealCompile,
    [switch]$NoMutations
)

# Final staging-parent ownership controls (both predicates) on native Windows.
# Production functions are loaded unmodified from -SourceFile. Fixture owners
# are set by icacls in a separate process, so this process never enables a
# backup/restore privilege that could bypass the DACLs under test. Network,
# clipboard, browser and prompt functions are replaced by refusing stubs.
# The real USERPROFILE/TEMP probes only open read leases; -RealCompile also
# lets the compiler context create and remove one empty private directory in
# the real TEMP. Mutation controls run each mutant in a fresh child host.
if($CaseList){ $Case=$CaseList.Split('|') }
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$script:results=New-Object 'System.Collections.Generic.List[object]'
$script:fixtureRoot=$null
$script:StagingAttempt=$null
$script:realTemp=$env:TEMP
$script:realTmp=$env:TMP
$script:realProfile=$env:USERPROFILE
$script:sourceHash=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
$script:testHash=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
$script:nativeHost=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$script:hostExe=(Get-Process -Id $PID).Path
$script:mutations=@()

$TrustedInstallerSid='S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
$StageFinal='Staging parent is not owned by this user with trusted write access.'
$StageAncestor='Staging ancestor permits foreign replacement or has an untrusted owner.'
$CompileFinal='Compiler parent is not owned by this user with trusted write access.'
$CompileAncestor='Compiler ancestor permits foreign replacement or has an untrusted owner.'

function Assert-Control($Condition,[string]$Message) { if(-not $Condition){throw $Message} }
function Get-SidClass([string]$Sid) {
    if(-not $Sid){return 'none'}
    if($Sid -ceq $script:userSid){return 'current-user'}
    switch($Sid){
        'S-1-5-18'{return 'SYSTEM'} 'S-1-5-32-544'{return 'Administrators'} 'S-1-5-32-545'{return 'Users'}
        'S-1-5-11'{return 'AuthenticatedUsers'} 'S-1-1-0'{return 'Everyone'} 'S-1-5-19'{return 'LocalService'}
    }
    if($Sid -ceq $TrustedInstallerSid){return 'TrustedInstaller'}
    return 'other'
}
function Add-Row([string]$Name,[string]$Status,$Detail) {
    $script:results.Add([pscustomobject]@{case=$Name;pass=($Status -eq 'PASS');pass_=($Status -eq 'PASS');status=$Status;detail=$Detail})
}
function Want([string]$Name) { return (-not $Case) -or ($Name -in $Case) }

function Set-FixtureSddl([string]$Path,[string]$Sddl) {
    # Owner (self) and DACL only; never the SACL.
    [R15OwnerFixture.Acl]::Set($Path,$Sddl.Replace('{U}',$script:userSid),5)
}
function Set-FixtureOwner([string]$Path,[string]$Sid) {
    if($Sid -ceq $script:userSid){return $true}
    $previous=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $null=& icacls.exe $Path /setowner ('*'+$Sid) /Q 2>&1; $code=$LASTEXITCODE } finally { $ErrorActionPreference=$previous }
    return ($code -eq 0 -and [R15OwnerFixture.Acl]::Owner($Path) -ceq $Sid)
}
$CleanSddl='O:{U}D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;{U})'
function New-OwnerFixture([string]$Name,[string]$OwnerSid,[string]$Sddl=$CleanSddl,[string]$Parent=$script:fixtureRoot) {
    $path=Join-Path $Parent $Name
    [void][IO.Directory]::CreateDirectory($path)
    # Owner first (while the user still holds full control), then the requested DACL only.
    Set-FixtureSddl $path 'O:{U}D:P(A;OICI;FA;;;{U})'
    $owned=Set-FixtureOwner $path $OwnerSid
    [R15OwnerFixture.Acl]::Set($path,$Sddl.Replace('{U}',$script:userSid),4)
    $facts=[R15OwnerFixture.Acl]::Describe($path)
    return [pscustomobject]@{Path=$path;OwnerSet=$owned;RequestedOwner=(Get-SidClass $OwnerSid);ActualOwner=(Get-SidClass $facts.Owner);DaclNull=$facts.DaclNull;Sddl=$facts.Sddl.Replace($script:userSid,'{U}')}
}
function Get-EntryCount([string]$Path) { if($Path.StartsWith('\\')){ return -2 }; try { return @([IO.Directory]::GetFileSystemEntries($Path)).Count } catch { return -1 } }

function Probe-Staging([string]$Path) {
    $script:StagingAttempt=[pscustomobject]@{Id=[guid]::NewGuid().ToString('N');Sid=$script:userSid;Status='probe';Scratch=$null;Retained=$null;Artifacts=(New-Object 'System.Collections.Generic.List[object]');Leases=(New-Object 'System.Collections.Generic.List[object]')}
    $before=Get-EntryCount $Path
    try { $null=Get-TrustedStagingParent $Path; $r=[ordered]@{result='accepted';message=$null} }
    catch { $r=[ordered]@{result='refused';message=$_.Exception.Message} }
    finally { foreach($lease in $script:StagingAttempt.Leases){ try{$lease.Dispose()}catch{} }; $script:StagingAttempt=$null }
    $r.entriesBefore=$before; $r.entriesAfter=Get-EntryCount $Path
    return [pscustomobject]$r
}
function Probe-Compiler([string]$Path) {
    $savedTemp=$env:TEMP; $savedTmp=$env:TMP; $before=Get-EntryCount $Path
    $env:TEMP=$Path; $env:TMP=$Path
    $r=[ordered]@{}
    try {
        $context=New-StagingCompilerContext
        $r.result='accepted'; $r.message=$null; $r.contextStatus=$context.Status; $created=$context.Path
        $env:TEMP=$savedTemp; $env:TMP=$savedTmp
        Clear-StagingCompilerContext $context $true
        $r.cleanupStatus=$context.Status; $r.createdRemoved=-not [IO.Directory]::Exists($created)
    } catch {
        $r.result='refused'; $r.message=$_.Exception.Message
        $r.contextStatus=if($script:CompilerScratch){$script:CompilerScratch.Status}else{$null}
    } finally { $env:TEMP=$savedTemp; $env:TMP=$savedTmp }
    $r.entriesBefore=$before; $r.entriesAfter=Get-EntryCount $Path
    return [pscustomobject]$r
}
# accept: admitted (compiler: owned context created and removed again).
# refuse: refused with one of $Messages (or a -like pattern) and no new entry.
function Judge([string]$Name,$Fixture,$Probe,[string]$Expect,[string[]]$Messages) {
    $detail=[pscustomobject]@{expect=$Expect;fixture=$Fixture;probe=$Probe}
    if($Fixture -and $Fixture.PSObject.Properties['ExpectNullDacl'] -and -not $Fixture.DaclNull){ Add-Row $Name 'SETUP_ERROR' $detail; return }
    if($Fixture -and -not $Fixture.OwnerSet){ Add-Row $Name 'BLOCKED_PRIVILEGE' $detail; return }
    if($Expect -eq 'accept') {
        $ok=$Probe.result -eq 'accepted' -and $Probe.entriesAfter -eq $Probe.entriesBefore
        if($Probe.PSObject.Properties['cleanupStatus']){ $ok=$ok -and $Probe.contextStatus -eq 'owned' -and $Probe.cleanupStatus -eq 'closed' -and $Probe.createdRemoved }
    } else {
        $matched=$false; foreach($m in $Messages){ if($Probe.message -and ($Probe.message -ceq $m -or $Probe.message -like $m)){ $matched=$true } }
        $ok=$Probe.result -eq 'refused' -and $matched -and $Probe.entriesAfter -eq $Probe.entriesBefore
        if($Probe.PSObject.Properties['contextStatus'] -and $Probe.result -eq 'refused'){ $ok=$ok -and $Probe.contextStatus -eq 'refused-before-create' }
    }
    Add-Row $Name $(if($ok){'PASS'}else{'FAIL'}) $detail
}
function Judge-Both([string]$Label,$Fixture,[string]$Expect,[string[]]$StageMessages,[string[]]$CompileMessages) {
    $n=$Label+': staging predicate'; if(Want $n){ Judge $n $Fixture (Probe-Staging $Fixture.Path) $Expect $StageMessages }
    $n=$Label+': compiler predicate'; if(Want $n){ Judge $n $Fixture (Probe-Compiler $Fixture.Path) $Expect $CompileMessages }
}

try {
    if(-not $script:nativeHost){ throw 'BLOCKED_NATIVE_HOST: Windows ACL controls require a Windows host.' }
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
namespace R15OwnerFixture {
  public sealed class Facts { public string Owner; public bool DaclNull; public string Sddl; }
  public static class Acl {
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool SetFileSecurityW(string name, int info, byte[] descriptor);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool GetFileSecurityW(string name, int info, byte[] descriptor, int length, out int needed);
    public static void Set(string path, string sddl, int info) {
      RawSecurityDescriptor raw = new RawSecurityDescriptor(sddl);
      byte[] bytes = new byte[raw.BinaryLength]; raw.GetBinaryForm(bytes, 0);
      if (!SetFileSecurityW(path, info, bytes)) throw new Win32Exception(Marshal.GetLastWin32Error(), "Set fixture security");
    }
    static RawSecurityDescriptor Read(string path) {
      int needed; GetFileSecurityW(path, 5, null, 0, out needed);
      if (needed <= 0) throw new Win32Exception(Marshal.GetLastWin32Error(), "Size fixture security");
      byte[] bytes = new byte[needed];
      if (!GetFileSecurityW(path, 5, bytes, needed, out needed)) throw new Win32Exception(Marshal.GetLastWin32Error(), "Read fixture security");
      return new RawSecurityDescriptor(bytes, 0);
    }
    public static string Owner(string path) { RawSecurityDescriptor d = Read(path); return d.Owner == null ? "" : d.Owner.Value; }
    public static Facts Describe(string path) { RawSecurityDescriptor d = Read(path); return new Facts { Owner = d.Owner == null ? "" : d.Owner.Value, DaclNull = d.DiscretionaryAcl == null, Sddl = d.GetSddlForm(AccessControlSections.Owner | AccessControlSections.Access) }; }
  }
}
'@
    $raw=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
    $tokens=$null; $errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($raw,[ref]$tokens,[ref]$errors)
    if(@($errors).Count){throw 'SETUP: source does not parse.'}
    foreach($definition in $ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}) {
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    function Write-Host { param([Parameter(Position=0,ValueFromRemainingArguments=$true)][object[]]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[string]$Separator=' ',[switch]$NoNewline) }
    function Invoke-WebRequest {throw 'Unexpected network request in owner control.'}
    function Invoke-RestMethod {throw 'Unexpected metadata request in owner control.'}
    function Copy-Text {throw 'Unexpected clipboard effect in owner control.'}
    function Open-TargetUrl {throw 'Unexpected browser effect in owner control.'}
    function Read-Host {throw 'Unexpected prompt in owner control.'}
    $script:DryRun=$false

    $script:userSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $script:fixtureRoot=Join-Path ([IO.Path]::GetFullPath($FixtureParent)) ('r15o-'+[guid]::NewGuid().ToString('N').Substring(0,8))
    [void][IO.Directory]::CreateDirectory($script:fixtureRoot)
    Set-FixtureSddl $script:fixtureRoot 'O:{U}D:P(A;OICI;FA;;;{U})'

    # Bootstrap: compile the production native helper under a user-owned fixture TEMP.
    $boot=New-OwnerFixture 'bootstrap-temp' $script:userSid 'O:{U}D:P(A;OICI;FA;;;{U})'
    $env:TEMP=$boot.Path; $env:TMP=$boot.Path
    try { Initialize-StagingNative } finally { $env:TEMP=$script:realTemp; $env:TMP=$script:realTmp }
    Assert-Control ('SalahInstaller.StageNative' -as [type]) 'SETUP: production native helper did not load.'

    # Positives: the final parent may be owned by the user, SYSTEM or Administrators.
    Judge-Both 'user-owned clean' (New-OwnerFixture 'user-owned-clean' $script:userSid) 'accept' @() @()
    Judge-Both 'system-owned clean' (New-OwnerFixture 'system-owned-clean' 'S-1-5-18') 'accept' @() @()
    Judge-Both 'administrators-owned clean' (New-OwnerFixture 'administrators-owned-clean' 'S-1-5-32-544') 'accept' @() @()

    $n='system/administrators-owned parents: Initialize-Staging'
    if(Want $n) {
        $temp=New-OwnerFixture 'init-temp-administrators' 'S-1-5-32-544'
        $profile=New-OwnerFixture 'init-profile-system' 'S-1-5-18'
        $detail=[ordered]@{temp=$temp;profile=$profile}
        if(-not ($temp.OwnerSet -and $profile.OwnerSet)) { Add-Row $n 'BLOCKED_PRIVILEGE' ([pscustomobject]$detail) }
        else {
            $env:TEMP=$temp.Path; $env:TMP=$temp.Path; $env:USERPROFILE=$profile.Path
            try {
                Initialize-Staging
                $scratch=Get-StagingPathInfo $script:StagingAttempt.Scratch.Path; $retained=Get-StagingPathInfo $script:StagingAttempt.Retained.Path
                $detail.status=$script:StagingAttempt.Status
                $detail.scratch=[pscustomobject]@{owner=(Get-SidClass $scratch.Owner);private=$scratch.Private}
                $detail.retained=[pscustomobject]@{owner=(Get-SidClass $retained.Owner);private=$retained.Private}
                $scratchPath=$scratch.Path
                Clear-OwnedScratch
                $detail.scratchRemoved=-not [IO.Directory]::Exists($scratchPath)
                $ok=$detail.status -eq 'active' -and $scratch.Private -and $retained.Private -and $scratch.Owner -ceq $script:userSid -and $retained.Owner -ceq $script:userSid -and $detail.scratchRemoved
                Add-Row $n $(if($ok){'PASS'}else{'FAIL'}) ([pscustomobject]$detail)
            } catch { $detail.error=$_.Exception.Message; Add-Row $n 'FAIL' ([pscustomobject]$detail) }
            finally { $script:StagingAttempt=$null; $env:TEMP=$script:realTemp; $env:TMP=$script:realTmp; $env:USERPROFILE=$script:realProfile }
        }
    }

    # Real default environment: read-only leases (plus one created/removed empty
    # private compiler directory in the real TEMP with -RealCompile).
    $n='real USERPROFILE: staging predicate'
    if(Want $n){ $p=Probe-Staging $script:realProfile; $p | Add-Member ownerClass (Get-SidClass ([R15OwnerFixture.Acl]::Owner($script:realProfile))); Judge $n $null $p 'accept' @() }
    $n='real TEMP: staging predicate'
    if(Want $n){ $p=Probe-Staging $script:realTemp; $p | Add-Member ownerClass (Get-SidClass ([R15OwnerFixture.Acl]::Owner($script:realTemp))); Judge $n $null $p 'accept' @() }
    $n='real TEMP: compiler predicate'
    if($RealCompile -and (Want $n)){ $p=Probe-Compiler $script:realTemp; $p | Add-Member ownerClass (Get-SidClass ([R15OwnerFixture.Acl]::Owner($script:realTemp))); Judge $n $null $p 'accept' @() }

    # Negatives. TrustedInstaller is a trusted ANCESTOR owner but deliberately
    # not an admitted final-parent owner: only the final-parent term refuses it.
    Judge-Both 'trustedinstaller-owned clean' (New-OwnerFixture 'trustedinstaller-owned-clean' $TrustedInstallerSid) 'refuse' @($StageFinal) @($CompileFinal)
    $ownerAny=@($StageFinal,$StageAncestor); $compileAny=@($CompileFinal,$CompileAncestor)
    foreach($spec in @(@('localservice','S-1-5-19','LS'),@('users','S-1-5-32-545','BU'),@('everyone','S-1-1-0','WD'),@('authenticatedusers','S-1-5-11','AU'))) {
        Judge-Both ($spec[0]+'-owned clean') (New-OwnerFixture ($spec[0]+'-owned-clean') $spec[1]) 'refuse' $ownerAny $compileAny
        Judge-Both ($spec[0]+'-owned with own write ACE') (New-OwnerFixture ($spec[0]+'-owned-write') $spec[1] ($CleanSddl+'(A;OICI;0x1301bf;;;'+$spec[2]+')')) 'refuse' $ownerAny $compileAny
    }
    Judge-Both 'system-owned with Everyone Modify' (New-OwnerFixture 'system-owned-everyone-modify' 'S-1-5-18' ($CleanSddl+'(A;OICI;0x1301bf;;;WD)')) 'refuse' $ownerAny $compileAny
    Judge-Both 'user-owned with Everyone Modify' (New-OwnerFixture 'user-owned-everyone-modify' $script:userSid ($CleanSddl+'(A;OICI;0x1301bf;;;WD)')) 'refuse' $ownerAny $compileAny
    Judge-Both 'system-owned with CREATOR OWNER generic-all' (New-OwnerFixture 'system-owned-creator-owner' 'S-1-5-18' ($CleanSddl+'(A;;GA;;;CO)')) 'refuse' $ownerAny $compileAny
    Judge-Both 'system-owned null DACL' (New-OwnerFixture 'system-owned-null-dacl' 'S-1-5-18' 'O:{U}D:NO_ACCESS_CONTROL' | Add-Member ExpectNullDacl $true -PassThru) 'refuse' $ownerAny $compileAny
    Judge-Both 'user-owned null DACL' (New-OwnerFixture 'user-owned-null-dacl' $script:userSid 'O:{U}D:NO_ACCESS_CONTROL' | Add-Member ExpectNullDacl $true -PassThru) 'refuse' $ownerAny $compileAny

    $target=New-OwnerFixture 'junction-target-system' 'S-1-5-18'
    $junction=Join-Path $script:fixtureRoot 'junction-parent'
    New-Item -ItemType Junction -Path $junction -Target $target.Path | Out-Null
    Judge-Both 'junction to a system-owned clean parent' ([pscustomobject]@{Path=$junction;OwnerSet=$target.OwnerSet;target=$target}) 'refuse' @('*Reparse*') @('*Reparse*')
    Judge-Both 'network path' ([pscustomobject]@{Path='\\localhost\C$\r0015-owner-not-created';OwnerSet=$true}) 'refuse' @('Unsupported staging parent path.') @('Unsupported compiler parent path.')

    $ancestor=New-OwnerFixture 'foreign-write-ancestor' $script:userSid ('O:{U}D:P(A;OICI;FA;;;{U})(A;;0x40;;;WD)')
    Judge-Both 'system-owned parent under a foreign-write ancestor' (New-OwnerFixture 'system-owned-child' 'S-1-5-18' $CleanSddl $ancestor.Path) 'refuse' @($StageAncestor) @($CompileAncestor)

    # A user without write access to an admitted-owner parent: nothing is created.
    $n='system-owned parent without user write: Initialize-Staging'
    $noWrite=New-OwnerFixture 'system-owned-no-user-write' 'S-1-5-18' 'O:{U}D:P(A;OICI;FA;;;SY)(A;OICI;0x1200a9;;;{U})'
    if(Want $n) {
        $profile=New-OwnerFixture 'no-write-profile' $script:userSid 'O:{U}D:P(A;OICI;FA;;;{U})'
        $detail=[ordered]@{temp=$noWrite;profile=$profile}
        if(-not $noWrite.OwnerSet){ Add-Row $n 'BLOCKED_PRIVILEGE' ([pscustomobject]$detail) }
        else {
            $env:TEMP=$noWrite.Path; $env:TMP=$noWrite.Path; $env:USERPROFILE=$profile.Path
            try { Initialize-Staging; $detail.result='initialized' } catch { $detail.result='refused'; $detail.message=$_.Exception.Message }
            finally { if($script:StagingAttempt){ foreach($lease in $script:StagingAttempt.Leases){ try{$lease.Dispose()}catch{} } }; $script:StagingAttempt=$null; $env:TEMP=$script:realTemp; $env:TMP=$script:realTmp; $env:USERPROFILE=$script:realProfile }
            $detail.tempEntries=Get-EntryCount $noWrite.Path; $detail.profileEntries=Get-EntryCount $profile.Path
            $ok=$detail.result -eq 'refused' -and $detail.tempEntries -eq 0 -and $detail.profileEntries -eq 0
            Add-Row $n $(if($ok){'PASS'}else{'FAIL'}) ([pscustomobject]$detail)
        }
    }
    $n='system-owned parent without user write: compiler predicate'
    if(Want $n) {
        $p=Probe-Compiler $noWrite.Path
        $detail=[pscustomobject]@{fixture=$noWrite;probe=$p}
        if(-not $noWrite.OwnerSet){ Add-Row $n 'BLOCKED_PRIVILEGE' $detail }
        else { Add-Row $n $(if($p.result -eq 'refused' -and $p.contextStatus -eq 'refused-before-create' -and $p.entriesAfter -eq 0){'PASS'}else{'FAIL'}) $detail }
    }
} catch {
    $status=if($_.Exception.Message -like 'BLOCKED_NATIVE_HOST*'){'BLOCKED_NATIVE_HOST'}else{'SETUP_ERROR'}
    Add-Row 'owner fixture/bootstrap' $status ([pscustomobject]@{error=$_.Exception.Message})
} finally {
    $script:StagingAttempt=$null
    $env:TEMP=$script:realTemp; $env:TMP=$script:realTmp; $env:USERPROFILE=$script:realProfile
}

# Mutation controls: each widened/narrowed owner term must be detected.
$setupFailed=@($script:results | Where-Object {$_.status -in @('SETUP_ERROR','FAIL')}).Count -gt 0
if(-not $NoMutations -and $setupFailed) { Add-Row 'mutation controls' 'NOT_RUN_SETUP' ([pscustomobject]@{reason='baseline setup failed; mutants not evaluated'}) }
if(-not $NoMutations -and -not $setupFailed -and $script:nativeHost -and $script:fixtureRoot) {
    $text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
    $psAnchor="`$parentSafe = `$actualOwner -cin @(`$Sid,'S-1-5-18','S-1-5-32-544') -and `$writeRestricted"
    $csAnchor='bool parentSafe = (actualOwner == sid || actualOwner == "S-1-5-18" || actualOwner == "S-1-5-32-544") && writeRestricted;'
    $realProfileOwner=[R15OwnerFixture.Acl]::Owner($script:realProfile)
    $userOnlyStage=@('system-owned clean: staging predicate','administrators-owned clean: staging predicate')
    if($realProfileOwner -cne $script:userSid){ $userOnlyStage+='real USERPROFILE: staging predicate' }
    $specs=@(
        @{name='compiler-owner-user-only';anchor=$psAnchor;replacement="`$parentSafe = `$actualOwner -ceq `$Sid -and `$writeRestricted";targets=@('system-owned clean: compiler predicate','administrators-owned clean: compiler predicate')},
        @{name='compiler-owner-any';anchor=$psAnchor;replacement="`$parentSafe = `$writeRestricted";targets=@('trustedinstaller-owned clean: compiler predicate')},
        @{name='staging-owner-user-only';anchor=$csAnchor;replacement='bool parentSafe = actualOwner == sid && writeRestricted;';targets=$userOnlyStage},
        @{name='staging-owner-any';anchor=$csAnchor;replacement='bool parentSafe = writeRestricted;';targets=@('trustedinstaller-owned clean: staging predicate')}
    )
    foreach($spec in $specs) {
        $row=[ordered]@{mutant=$spec.name;targets=$spec.targets}
        try {
            Assert-Control ([regex]::Matches($text,[regex]::Escape($spec.anchor)).Count -eq 1) ('Mutation anchor drift: '+$spec.name)
            $mutant=Join-Path $script:fixtureRoot ('mutant-'+$spec.name+'.ps1')
            [IO.File]::WriteAllText($mutant,$text.Replace($spec.anchor,$spec.replacement),(New-Object Text.UTF8Encoding $false))
            $row.mutantSha256=(Get-FileHash -LiteralPath $mutant -Algorithm SHA256).Hash.ToLowerInvariant()
            $childReport=Join-Path $script:fixtureRoot ('mutant-'+$spec.name+'.json')
            $null=& $script:hostExe -NoLogo -NoProfile -NonInteractive -File $PSCommandPath -SourceFile $mutant -FixtureParent $script:fixtureRoot -NoMutations -ReportPath $childReport -CaseList ($spec.targets -join '|') 2>&1
            $child=[IO.File]::ReadAllText($childReport) | ConvertFrom-Json
            $baseline=@($script:results | Where-Object {$_.case -in $spec.targets})
            $mutantRows=@($child.results | Where-Object {$_.case -in $spec.targets})
            $row.baseline=@($baseline | ForEach-Object {[pscustomobject]@{case=$_.case;status=$_.status}})
            $row.mutantRows=@($mutantRows | ForEach-Object {[pscustomobject]@{case=$_.case;status=$_.status;result=$_.detail.probe.result;message=$_.detail.probe.message}})
            $baseOk=$baseline.Count -eq $spec.targets.Count -and -not @($baseline | Where-Object {$_.status -ne 'PASS'}).Count
            $killed=$mutantRows.Count -eq $spec.targets.Count -and -not @($mutantRows | Where-Object {$_.status -ne 'FAIL'}).Count
            $blocked=@($baseline + $mutantRows | Where-Object {$_.status -like 'BLOCKED*'}).Count -gt 0
            $row.status=if($baseOk -and $killed){'KILLED'}elseif($blocked){'BLOCKED_PRIVILEGE'}else{'SURVIVED'}
        } catch { $row.status='ERROR'; $row.error=$_.Exception.Message }
        $script:mutations+=[pscustomobject]$row
        Add-Row ('mutant '+$spec.name+' is detected') $(if($row.status -eq 'KILLED'){'PASS'}elseif($row.status -like 'BLOCKED*'){'BLOCKED_PRIVILEGE'}else{'FAIL'}) ([pscustomobject]$row)
    }
}

# Retain nothing that needs privilege to remove: restore ownership, then delete.
$removed=$null
if($script:fixtureRoot -and -not $NoMutations) {
    $previous=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $null=& takeown.exe /F $script:fixtureRoot /R /D Y 2>&1; $null=& icacls.exe $script:fixtureRoot /reset /T /C /Q 2>&1 } finally { $ErrorActionPreference=$previous }
    try { foreach($j in @(Get-ChildItem -LiteralPath $script:fixtureRoot -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue)){ [IO.Directory]::Delete($j.FullName) }; [IO.Directory]::Delete($script:fixtureRoot,$true); $removed=$true } catch { $removed=$false }
}
$report=[pscustomobject]@{
    schema='r0015-staging-owner-controls.v1';sourceSha256=$script:sourceHash;testSha256=$script:testHash;
    runtime=$PSVersionTable.PSVersion.ToString();edition=[string]$PSVersionTable.PSEdition;platform=[Environment]::OSVersion.VersionString;
    elevated=$(if($script:nativeHost){([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)}else{$null});
    realCompile=[bool]$RealCompile;fixtureRemoved=$removed;
    decision='TrustedInstaller is not an admitted final-parent owner (not needed for observed defaults); it remains a trusted ancestor owner.';
    results=$script:results.ToArray();mutations=$script:mutations
}
$json=$report | ConvertTo-Json -Depth 12
if($ReportPath){ [IO.File]::WriteAllText($ReportPath,$json,(New-Object Text.UTF8Encoding $false)) }
[Console]::WriteLine($json)
if(-not $script:nativeHost){exit 2}
if(@($script:results | Where-Object {$_.status -in @('FAIL','SETUP_ERROR')}).Count){exit 1}
if(@($script:results | Where-Object {$_.status -ne 'PASS'}).Count){exit 2}
exit 0
