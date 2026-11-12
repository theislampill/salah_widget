param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [Parameter(Mandatory=$true)][string]$FixtureParent
)
# Staging-parent environment observation (Windows).
# Records host facts for the user profile, temporary and local-application-data
# directories, then calls the installer's own staging-parent admission
# functions, loaded unmodified from the installer source by AST extraction the
# way the repository's staging tests load them. No installer entry point runs,
# no network or clipboard access, no browser is opened. Control fixtures are
# created only under the supplied fixture parent. A real staging initialisation
# creates and removes only the installer's own private roots; the empty retained
# root it creates in the profile is removed afterwards and recorded.
# This is an observation, not a gate: it always exits 0.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$report = [ordered]@{
    schema = 'staging-parent-environment-observation.windows.v1'
    observedUtc = [DateTime]::UtcNow.ToString('o')
    host = [ordered]@{}
    source = [ordered]@{}
    facts = @()
    admission = @()
    fixtures = @()
    staging = $null
    errors = @()
}
function Save-Report { [IO.File]::WriteAllText($OutputFile, ($report | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false)) }

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$userSid = $identity.User.Value
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$trustedInstallerSid = ''
try { $trustedInstallerSid = ([Security.Principal.NTAccount]::new('NT SERVICE','TrustedInstaller').Translate([Security.Principal.SecurityIdentifier])).Value } catch {}
function Get-SidClass([string]$Sid) {
    if (-not $Sid) { return 'none' }
    if ($Sid -ceq $userSid) { return 'current-user' }
    switch ($Sid) {
        'S-1-5-18' { return 'SYSTEM' }
        'S-1-5-32-544' { return 'Administrators' }
        'S-1-5-32-545' { return 'Users' }
        'S-1-5-11' { return 'AuthenticatedUsers' }
        'S-1-1-0' { return 'Everyone' }
        'S-1-3-0' { return 'CreatorOwner' }
        'S-1-5-19' { return 'LocalService' }
        'S-1-5-20' { return 'NetworkService' }
        'S-1-15-2-1' { return 'AllApplicationPackages' }
    }
    if ($trustedInstallerSid -and $Sid -ceq $trustedInstallerSid) { return 'TrustedInstaller' }
    if ($Sid -like 'S-1-5-21-*') { return 'other-account' }
    if ($Sid -like 'S-1-15-*') { return 'other-capability' }
    return 'other-wellknown'
}

$report.host = [ordered]@{
    psVersion = $PSVersionTable.PSVersion.ToString()
    psEdition = [string]$PSVersionTable.PSEdition
    osVersion = [Environment]::OSVersion.VersionString
    productName = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -ErrorAction SilentlyContinue).ProductName
    installationType = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -ErrorAction SilentlyContinue).InstallationType
    imageVersion = $env:ImageVersion
    elevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    administratorsMember = @($identity.Groups | Where-Object { $_.Value -ceq 'S-1-5-32-544' }).Count -gt 0
    tokenOwnerClass = Get-SidClass $identity.Owner.Value
}
$report.source = [ordered]@{
    path = [IO.Path]::GetFileName($SourceFile)
    sha256 = (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
    gitBlob = $env:OBSERVED_INSTALL_PS1_BLOB
}

function Get-PathFacts([string]$Label, [string]$Path) {
    $row = [ordered]@{ label = $Label; exists = $false }
    try {
        $item = Get-Item -LiteralPath $Path -Force
        $acl = Get-Acl -LiteralPath $Path
        $row.exists = $true
        $row.ownerClass = Get-SidClass ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value)
        $row.reparsePoint = (([int]$item.Attributes) -band 0x400) -ne 0
        $row.linkType = [string]$item.LinkType
        $row.daclProtected = $acl.AreAccessRulesProtected
        $row.dacl = @($acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]) | ForEach-Object {
            [ordered]@{ principalClass = Get-SidClass $_.IdentityReference.Value; type = [string]$_.AccessControlType
                        rightsMask = ('0x{0:x8}' -f [int64]$_.FileSystemRights); inherited = $_.IsInherited
                        inheritance = [string]$_.InheritanceFlags; propagation = [string]$_.PropagationFlags }
        })
        $root = [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Path))
        $drive = [IO.DriveInfo]::new($root)
        $row.volume = [ordered]@{ format = $drive.DriveFormat; type = [string]$drive.DriveType }
        $row.sameAsSystemDrive = [string]::Equals($root, [IO.Path]::GetPathRoot($env:SystemRoot), [StringComparison]::OrdinalIgnoreCase)
    } catch { $row.error = $_.Exception.Message }
    return $row
}
$profileParent = Split-Path -Parent $env:USERPROFILE
foreach ($pair in @(@('USERPROFILE', $env:USERPROFILE), @('USERPROFILE-parent', $profileParent), @('TEMP', $env:TEMP), @('LOCALAPPDATA', $env:LOCALAPPDATA), @('RUNNER_TEMP-fixture-parent', $FixtureParent))) {
    $report.facts += Get-PathFacts $pair[0] $pair[1]
}
Save-Report

# Load the installer's function definitions exactly as written (no edits).
$script:DryRun = $false
$script:StagingAttempt = $null
$script:messages = @()
try {
    $raw = [IO.File]::ReadAllText($SourceFile, [Text.Encoding]::UTF8)
    $tokens = $null; $parseErrors = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($raw, [ref]$tokens, [ref]$parseErrors)
    if (@($parseErrors).Count) { throw 'installer source does not parse' }
    foreach ($definition in $ast.EndBlock.Statements | Where-Object { $_ -is [Management.Automation.Language.FunctionDefinitionAst] }) {
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    function Write-Host { param([Parameter(Position=0,ValueFromRemainingArguments=$true)][object[]]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[string]$Separator=' ',[switch]$NoNewline)
        $script:messages += (($Object | ForEach-Object { [string]$_ }) -join $Separator) }
    function Invoke-WebRequest { throw 'network disabled in observation' }
    function Invoke-RestMethod { throw 'network disabled in observation' }
    function Copy-Text { throw 'clipboard disabled in observation' }
    function Open-TargetUrl { throw 'browser disabled in observation' }
    function Read-Host { throw 'prompt disabled in observation' }
} catch { $report.errors += ('load: ' + $_.Exception.Message); Save-Report; exit 0 }

$compile = [ordered]@{ step = 'Initialize-StagingNative (compiles helper under the real temporary directory)' }
try { Initialize-StagingNative; $compile.result = 'loaded' } catch { $compile.result = 'refused'; $compile.message = $_.Exception.Message }
$report.compile = $compile
Save-Report
if ($compile.result -ne 'loaded') {
    # Second route, recorded separately: compile with TEMP pointed at a new
    # current-user-owned protected directory under the fixture parent, so the
    # admission functions can still be observed against the real parents.
    $compileTemp = Join-Path $FixtureParent ('envobs-compile-' + [guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($compileTemp)
    $compileAcl = New-Object Security.AccessControl.DirectorySecurity
    $compileAcl.SetAccessRuleProtection($true, $false)
    $compileAcl.SetOwner((New-Object Security.Principal.SecurityIdentifier $userSid))
    $compileAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier $userSid), [Security.AccessControl.FileSystemRights]::FullControl, [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit', [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)))
    Set-Acl -LiteralPath $compileTemp -AclObject $compileAcl
    $savedTemp = $env:TEMP; $savedTmp = $env:TMP
    $second = [ordered]@{ step = 'Initialize-StagingNative with TEMP = new current-user-owned fixture directory (compile only)' }
    try { $env:TEMP = $compileTemp; $env:TMP = $compileTemp; Initialize-StagingNative; $second.result = 'loaded' }
    catch { $second.result = 'refused'; $second.message = $_.Exception.Message }
    finally { $env:TEMP = $savedTemp; $env:TMP = $savedTmp }
    try { [IO.Directory]::Delete($compileTemp, $true); $second.fixtureRemoved = $true } catch { $second.fixtureRemoved = $false; $second.fixtureRemoveError = $_.Exception.Message }
    $report.compileSecondRoute = $second
    Save-Report
    if ($second.result -eq 'loaded') { $compile.result = 'loaded-via-fixture-temp' }
}
if ($compile.result -notlike 'loaded*') { $report.errors += 'native helper unavailable; admission calls skipped'; Save-Report; exit 0 }

function New-ObservationAttempt { return [pscustomobject]@{ Id = [guid]::NewGuid().ToString('N'); Sid = (Get-StagingUserSid); Status = 'observation'; Scratch = $null; Retained = $null; Artifacts = (New-Object 'System.Collections.Generic.List[object]'); Leases = (New-Object 'System.Collections.Generic.List[object]') } }
function Invoke-Admission([string]$Label, [string]$Path, [string]$Expected) {
    $row = [ordered]@{ label = $Label; expected = $Expected }
    $script:StagingAttempt = New-ObservationAttempt
    try {
        $info = Get-StagingPathInfo $Path
        $row.inspect = [ordered]@{ ownerClass = Get-SidClass $info.Owner; trustedParent = $info.TrustedParent; trustedAncestor = $info.TrustedAncestor; writeRestricted = $info.WriteRestricted; private = $info.Private; directory = $info.Directory }
    } catch { $row.inspectError = $_.Exception.Message }
    try { $null = Get-TrustedStagingParent $Path; $row.result = 'accepted' }
    catch { $row.result = 'refused'; $row.message = $_.Exception.Message }
    finally { foreach ($lease in $script:StagingAttempt.Leases) { try { $lease.Dispose() } catch {} }; $script:StagingAttempt = $null }
    return $row
}

$report.admission += Invoke-Admission 'real USERPROFILE' $env:USERPROFILE 'observe'
$report.admission += Invoke-Admission 'real TEMP' $env:TEMP 'observe'
$report.admission += Invoke-Admission 'real LOCALAPPDATA' $env:LOCALAPPDATA 'observe'
Save-Report

# Control fixtures: protected DACL mirroring a stock profile root
# (SYSTEM, Administrators, current user: full control), owner varied.
function New-ControlFixture([string]$Parent, [string]$Name, [string]$OwnerSid, [bool]$ForeignWrite) {
    $path = Join-Path $Parent $Name
    [void][IO.Directory]::CreateDirectory($path)
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true, $false)
    $inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
    foreach ($sid in @('S-1-5-18', 'S-1-5-32-544', $userSid)) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier $sid), [Security.AccessControl.FileSystemRights]::FullControl, $inherit, [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)))
    }
    if ($ForeignWrite) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier 'S-1-1-0'), [Security.AccessControl.FileSystemRights]::Modify, $inherit, [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)))
    }
    $acl.SetOwner((New-Object Security.Principal.SecurityIdentifier $userSid))
    Set-Acl -LiteralPath $path -AclObject $acl
    $ownerResult = 'current-user'
    if ($OwnerSid -cne $userSid) {
        # Native stderr must not become a terminating error under Windows PowerShell 5.1.
        $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { $out = & icacls.exe $path /setowner ('*' + $OwnerSid) 2>&1; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $previous }
        $ownerResult = 'icacls exit ' + $code + ': ' + (($out | ForEach-Object { [string]$_ }) -join ' ').Replace($path, '<fixture>').Trim()
    }
    $actualOwner = Get-SidClass ((Get-Acl -LiteralPath $path).GetOwner([Security.Principal.SecurityIdentifier]).Value)
    return [ordered]@{ path = $path; requestedOwnerClass = Get-SidClass $OwnerSid; actualOwnerClass = $actualOwner; setOwner = $ownerResult; foreignWriteAce = $ForeignWrite }
}
$controlSets = @(
    @{ label = 'runner-temp'; parent = (Join-Path $FixtureParent ('envobs-' + [guid]::NewGuid().ToString('N'))) },
    @{ label = 'user-temp'; parent = (Join-Path $env:TEMP ('envobs-' + [guid]::NewGuid().ToString('N'))) }
)
foreach ($set in $controlSets) {
    try {
        [void][IO.Directory]::CreateDirectory($set.parent)
        $baseAcl = New-Object Security.AccessControl.DirectorySecurity
        $baseAcl.SetAccessRuleProtection($true, $false)
        $baseAcl.SetOwner((New-Object Security.Principal.SecurityIdentifier $userSid))
        $baseAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier $userSid), [Security.AccessControl.FileSystemRights]::FullControl, [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit', [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)))
        Set-Acl -LiteralPath $set.parent -AclObject $baseAcl
        $report.fixtures += [ordered]@{ set = $set.label; parentAdmission = (Invoke-Admission ($set.label + ': fixture parent') $set.parent 'observe') }
        foreach ($spec in @(
            @('user-owned-clean', $userSid, $false, 'accept'),
            @('system-owned-clean', 'S-1-5-18', $false, 'observe'),
            @('administrators-owned-clean', 'S-1-5-32-544', $false, 'observe'),
            @('user-owned-foreign-write', $userSid, $true, 'refuse'))) {
            $fixture = New-ControlFixture $set.parent $spec[0] $spec[1] $spec[2]
            $admission = Invoke-Admission ($set.label + ': ' + $spec[0]) $fixture.path $spec[3]
            $report.fixtures += [ordered]@{ set = $set.label; fixture = $spec[0]; setup = $fixture; admission = $admission }
            Save-Report
        }
    } catch { $report.errors += ($set.label + ' fixtures: ' + $_.Exception.Message) }
    finally {
        try {
            $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
            try { & takeown.exe /F $set.parent /R /D Y 2>&1 | Out-Null; & icacls.exe $set.parent /reset /T /C /Q 2>&1 | Out-Null } finally { $ErrorActionPreference = $previous }
            [IO.Directory]::Delete($set.parent, $true); $report.fixtures += [ordered]@{ set = $set.label; removed = $true } }
        catch { $report.fixtures += [ordered]@{ set = $set.label; removed = $false; message = $_.Exception.Message } }
    }
}
Save-Report

# Real staging initialisation with the runner's own TEMP and USERPROFILE.
$staging = [ordered]@{ step = 'Initialize-Staging with real TEMP and USERPROFILE, then Clear-OwnedScratch' }
$beforeTemp = @(Get-ChildItem -LiteralPath $env:TEMP -Force -Filter 'SalahWidget*' -ErrorAction SilentlyContinue | ForEach-Object Name)
$beforeProfile = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Force -Filter 'SalahWidget*' -ErrorAction SilentlyContinue | ForEach-Object Name)
$script:StagingAttempt = $null
try {
    Initialize-Staging
    $staging.result = 'initialized'
    $staging.scratchCreated = [bool]$script:StagingAttempt.Scratch
    $staging.retainedCreated = [bool]$script:StagingAttempt.Retained
} catch { $staging.result = 'refused'; $staging.message = $_.Exception.Message }
$retainedPath = if ($script:StagingAttempt -and $script:StagingAttempt.Retained) { $script:StagingAttempt.Retained.Path } else { $null }
try { Clear-OwnedScratch; $staging.cleanup = 'Clear-OwnedScratch returned' } catch { $staging.cleanup = 'Clear-OwnedScratch threw: ' + $_.Exception.Message }
$afterTemp = @(Get-ChildItem -LiteralPath $env:TEMP -Force -Filter 'SalahWidget*' -ErrorAction SilentlyContinue | ForEach-Object Name)
$afterProfile = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Force -Filter 'SalahWidget*' -ErrorAction SilentlyContinue | ForEach-Object Name)
$staging.tempNewAfterCleanup = @($afterTemp | Where-Object { $beforeTemp -notcontains $_ })
$staging.profileNewAfterCleanup = @($afterProfile | Where-Object { $beforeProfile -notcontains $_ })
if ($retainedPath -and (Test-Path -LiteralPath $retainedPath)) {
    try { [IO.Directory]::Delete($retainedPath, $true); $staging.retainedRemovedByObserver = $true } catch { $staging.retainedRemovedByObserver = $false; $staging.retainedRemoveError = $_.Exception.Message }
}
$staging.messages = @($script:messages)
$report.staging = $staging
Save-Report
[Console]::WriteLine(('host {0}: compile={1}; USERPROFILE={2}; TEMP={3}; staging={4}' -f $report.host.psVersion, $compile.result, $report.admission[0].result, $report.admission[1].result, $staging.result))
exit 0
