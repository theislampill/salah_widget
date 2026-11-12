param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$FixtureParent=[IO.Path]::GetTempPath(),
    [string]$CaseList,
    [string]$ReportPath,
    [switch]$NoMutations
)

# Asset and archive refusal controls on native Windows (R0015 section B items
# 1, 2 and a CRC representative of item 3). Production functions are loaded
# unmodified from -SourceFile and run against disposable user-owned fixture
# TEMP/USERPROFILE parents. Only metadata/download transport is replaced (it
# returns fixture bytes); clipboard, browser and prompt functions refuse.
# Each mutant removes exactly one guard and runs in a fresh child host; it is
# KILLED when its target control fails while the healthy control still passes.
$Case=if($CaseList){$CaseList.Split('|')}else{@()}
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$script:results=New-Object 'System.Collections.Generic.List[object]'
$script:mutations=@()
$script:fixtureRoot=$null
$script:StagingAttempt=$null
$script:oldTemp=$env:TEMP; $script:oldTmp=$env:TMP; $script:oldProfile=$env:USERPROFILE
$script:utf8=New-Object Text.UTF8Encoding $false
$script:sourceHash=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
$script:testHash=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
$script:nativeHost=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$script:hostExe=(Get-Process -Id $PID).Path
$Healthy='healthy archive downloads and unpacks'
$Backslash='backslash member is refused before any write outside the private roots'
$Digest='declared digest mismatch publishes nothing'
$Size='declared size mismatch publishes nothing'
$Crc='member CRC mismatch is refused before any member is written'

function Assert-Control($Condition,[string]$Message) { if(-not $Condition){throw $Message} }
function Want([string]$Name) { return (-not $Case.Count) -or ($Name -in $Case) }
function Get-BytesHash([byte[]]$Bytes) { $h=[Security.Cryptography.SHA256]::Create(); try { return ([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() } finally { $h.Dispose() } }
function New-TestZip($Entries) {
    $stream=New-Object IO.MemoryStream
    $zip=New-Object IO.Compression.ZipArchive($stream,[IO.Compression.ZipArchiveMode]::Create,$true)
    try { foreach($entry in $Entries) { $member=$zip.CreateEntry([string]$entry.name); $writer=$member.Open(); try { $b=$script:utf8.GetBytes([string]$entry.text); $writer.Write($b,0,$b.Length) } finally { $writer.Dispose() } } }
    finally { $zip.Dispose() }
    try { return ,$stream.ToArray() } finally { $stream.Dispose() }
}
function Read-UInt16([byte[]]$B,[int]$O) { return [int]$B[$O] + 256*[int]$B[$O+1] }
function Get-ZipNames([byte[]]$Bytes) {
    $s=New-Object IO.MemoryStream(,$Bytes); $z=New-Object IO.Compression.ZipArchive($s,[IO.Compression.ZipArchiveMode]::Read)
    try { return @($z.Entries | ForEach-Object {[string]$_.FullName}) } finally { $z.Dispose(); $s.Dispose() }
}
# Flip one bit of the named member's CRC in both its local and central record.
function Set-ZipCrcMismatch([byte[]]$Bytes,[string]$Name) {
    $copy=[byte[]]$Bytes.Clone(); $local=0; $central=0
    for($i=0; $i -le $copy.Length-46; $i++) {
        if($copy[$i] -eq 0x50 -and $copy[$i+1] -eq 0x4b -and $copy[$i+2] -eq 3 -and $copy[$i+3] -eq 4) {
            $n=Read-UInt16 $copy ($i+26)
            if($script:utf8.GetString($copy,$i+30,$n) -ceq $Name) { Assert-Control (((Read-UInt16 $copy ($i+6)) -band 8) -eq 0) 'SETUP: fixture uses a data descriptor.'; $copy[$i+14]=$copy[$i+14] -bxor 1; $local++ }
        } elseif($copy[$i] -eq 0x50 -and $copy[$i+1] -eq 0x4b -and $copy[$i+2] -eq 1 -and $copy[$i+3] -eq 2) {
            $n=Read-UInt16 $copy ($i+28)
            if($script:utf8.GetString($copy,$i+46,$n) -ceq $Name) { $copy[$i+16]=$copy[$i+16] -bxor 1; $central++ }
        }
    }
    Assert-Control ($local -eq 1 -and $central -eq 1) 'SETUP: CRC fixture records not found exactly once.'
    return ,$copy
}
function New-TestAsset([byte[]]$Bytes,[string]$Digest,$Size) {
    return [pscustomobject]@{id=101;name='tabliss-chromium.zip';size=$Size;browser_download_url='https://fixture.invalid/assets/tabliss-chromium.zip';digest=('sha256:'+$Digest);content_type='application/zip'}
}
function Get-Tree([string]$Root) { return @(Get-ChildItem -LiteralPath $Root -Recurse -Force | ForEach-Object {$_.FullName}) }
function New-ArchiveCase([string]$Name,[byte[]]$Bytes) {
    if($script:StagingAttempt){ try{Clear-OwnedScratch}catch{}; $script:StagingAttempt=$null }
    $root=Join-Path $script:fixtureRoot $Name
    $temp=Join-Path $root 'temp'; $profile=Join-Path $root 'profile'
    foreach($p in @($root,$temp,$profile)) {
        [void][IO.Directory]::CreateDirectory($p)
        $acl=New-Object Security.AccessControl.DirectorySecurity
        $acl.SetOwner($script:subjectSid); $acl.SetAccessRuleProtection($true,$false)
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($script:subjectSid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)))
        Set-Acl -LiteralPath $p -AclObject $acl
    }
    $env:TEMP=$temp; $env:TMP=$temp; $env:USERPROFILE=$profile
    $script:DryRun=$false; $script:InstallSource='github'; $script:TablissNgRepo='fixture/upstream'; $script:LatestRelease=$null
    $script:downloadBytes=$Bytes; $script:downloads=0
    Initialize-Staging
    return [pscustomobject]@{Root=$root;Profile=$profile;Before=(Get-Tree $root)}
}
# Download and (if admitted) unpack; report refusal, ready paths and every new
# filesystem entry outside the attempt's two private roots.
function Invoke-Acquire($Fixture,$Asset) {
    $script:releaseFixture=[pscustomobject]@{id=201;tag_name='v-fixture';assets=@($Asset)}
    $r=[ordered]@{refused=$false;message=$null;archive=$null;bundle=$null}
    try { $r.archive=Download-Asset $Asset; $r.bundle=Expand-ChromiumAsset $r.archive } catch { $r.refused=$true; $r.message=$_.Exception.Message }
    $scratch=$script:StagingAttempt.Scratch.Path.TrimEnd('\')+'\'; $retained=$script:StagingAttempt.Retained.Path.TrimEnd('\')+'\'
    $new=@(Get-Tree $Fixture.Root | Where-Object {$_ -notin $Fixture.Before})
    $r.outside=@($new | Where-Object { -not ($_+'\').StartsWith($scratch,[StringComparison]::OrdinalIgnoreCase) -and -not ($_+'\').StartsWith($retained,[StringComparison]::OrdinalIgnoreCase) } | ForEach-Object {$_.Substring($Fixture.Root.Length)})
    $r.published=@(Get-ChildItem -LiteralPath $script:DownloadRoot -Force | ForEach-Object {$_.Name})
    $r.unpackedFiles=@(Get-ChildItem -LiteralPath $script:StagingAttempt.Retained.Path -Recurse -Force -File | Where-Object {$_.FullName -notlike ($script:DownloadRoot+'\*')} | ForEach-Object {$_.FullName.Substring($Fixture.Root.Length)})
    $r.downloads=$script:downloads
    $r.recordStates=@($script:StagingAttempt.Artifacts | ForEach-Object {$_.Kind+':'+$_.State})
    return [pscustomobject]$r
}
function Invoke-Control([string]$Name,[scriptblock]$Body) {
    if(-not (Want $Name)){return}
    $detail=$null; $status='FAIL'
    try { $detail=& $Body; if($detail.ok){$status='PASS'} } catch { $detail=[pscustomobject]@{error=$_.Exception.Message} }
    $script:results.Add([pscustomobject]@{case=$Name;pass=($status -eq 'PASS');pass_=($status -eq 'PASS');status=$status;detail=$detail})
}

try {
    if(-not $script:nativeHost){ throw 'BLOCKED_NATIVE_HOST: native staging requires Windows.' }
    $raw=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
    $tokens=$null; $errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($raw,[ref]$tokens,[ref]$errors)
    if(@($errors).Count){throw 'SETUP: source does not parse.'}
    foreach($definition in $ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}) { . ([scriptblock]::Create($definition.Extent.Text)) }
    Add-Type -AssemblyName System.IO.Compression
    function Write-Host { param([Parameter(Position=0,ValueFromRemainingArguments=$true)][object[]]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[string]$Separator=' ',[switch]$NoNewline) }
    function Invoke-RestMethod { param($Uri,$Headers) return $script:releaseFixture }
    function Invoke-WebRequest { param($Uri,[string]$OutFile,[switch]$UseBasicParsing,$Headers)
        Assert-Control ([IO.Path]::GetFullPath($OutFile).StartsWith($script:fixtureRoot+'\',[StringComparison]::OrdinalIgnoreCase)) 'Fixture download escaped its root.'
        $script:downloads++; [IO.File]::WriteAllBytes($OutFile,[byte[]]$script:downloadBytes) }
    function Copy-Text {throw 'Unexpected clipboard effect in archive control.'}
    function Open-TargetUrl {throw 'Unexpected browser effect in archive control.'}
    function Read-Host {throw 'Unexpected prompt in archive control.'}
    $script:subjectSid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $script:fixtureRoot=Join-Path ([IO.Path]::GetFullPath($FixtureParent)) ('r15a-'+[guid]::NewGuid().ToString('N').Substring(0,8))
    [void][IO.Directory]::CreateDirectory($script:fixtureRoot)

    $manifest='{"manifest_version":3,"name":"Fixture extension","version":"1.0"}'
    $good=New-TestZip @([pscustomobject]@{name='extension/manifest.json';text=$manifest},[pscustomobject]@{name='extension/data.txt';text='fixture payload bytes'})
    $goodHash=Get-BytesHash $good

    Invoke-Control $Healthy {
        $f=New-ArchiveCase 'healthy' $good
        $o=Invoke-Acquire $f (New-TestAsset $good $goodHash $good.Length)
        $ok=-not $o.refused -and $o.bundle -and [IO.File]::Exists((Join-Path $o.bundle 'manifest.json')) -and [IO.File]::Exists((Join-Path $o.bundle 'data.txt')) -and $o.outside.Count -eq 0 -and $o.published.Count -eq 1
        [pscustomobject]@{ok=$ok;observation=$o}
    }
    Invoke-Control $Backslash {
        # A directory member whose name uses backslash separators that would
        # climb from the extraction root to the profile parent.
        $marker='r15-archive-marker'
        $bytes=New-TestZip @([pscustomobject]@{name='extension/manifest.json';text=$manifest},[pscustomobject]@{name=('..\..\'+$marker+'/');text=''})
        Assert-Control (@(Get-ZipNames $bytes | Where-Object {$_.Contains('\')}).Count -eq 1) 'SETUP: fixture member lost its backslash.'
        $f=New-ArchiveCase 'backslash' $bytes
        $o=Invoke-Acquire $f (New-TestAsset $bytes (Get-BytesHash $bytes) $bytes.Length)
        $markerExists=[IO.Directory]::Exists((Join-Path $f.Profile $marker)) -or @(Get-ChildItem -LiteralPath $f.Root -Recurse -Force -Filter ($marker+'*')).Count -gt 0
        $ok=$o.refused -and $o.message -ceq 'Unsafe archive member path.' -and -not $o.archive -and -not $o.bundle -and $o.outside.Count -eq 0 -and -not $markerExists -and $o.published.Count -eq 0
        [pscustomobject]@{ok=$ok;markerExists=$markerExists;observation=$o}
    }
    Invoke-Control $Digest {
        $f=New-ArchiveCase 'digest' $good
        $o=Invoke-Acquire $f (New-TestAsset $good (Get-BytesHash ($script:utf8.GetBytes('other bytes'))) $good.Length)
        $ok=$o.refused -and $o.message -ceq 'Candidate identity, expected size or declared digest differs.' -and -not $o.archive -and $o.published.Count -eq 0 -and $o.unpackedFiles.Count -eq 0 -and $o.outside.Count -eq 0 -and ($o.recordStates -contains 'asset:validation-failed')
        [pscustomobject]@{ok=$ok;observation=$o}
    }
    Invoke-Control $Size {
        $f=New-ArchiveCase 'size' $good
        $o=Invoke-Acquire $f (New-TestAsset $good $goodHash ($good.Length+1))
        $ok=$o.refused -and $o.message -ceq 'Candidate identity, expected size or declared digest differs.' -and -not $o.archive -and $o.published.Count -eq 0 -and $o.unpackedFiles.Count -eq 0 -and $o.outside.Count -eq 0 -and ($o.recordStates -contains 'asset:validation-failed')
        [pscustomobject]@{ok=$ok;observation=$o}
    }
    Invoke-Control $Crc {
        $bytes=Set-ZipCrcMismatch $good 'extension/data.txt'
        $f=New-ArchiveCase 'crc' $bytes
        $o=Invoke-Acquire $f (New-TestAsset $bytes (Get-BytesHash $bytes) $bytes.Length)
        $dataFiles=@(Get-ChildItem -LiteralPath $f.Root -Recurse -Force -File -Filter 'data.txt')
        $ok=$o.refused -and -not $o.archive -and -not $o.bundle -and $o.published.Count -eq 0 -and $dataFiles.Count -eq 0 -and $o.outside.Count -eq 0
        [pscustomobject]@{ok=$ok;dataFiles=$dataFiles.Count;observation=$o}
    }
} catch {
    $status=if($_.Exception.Message -like 'BLOCKED_NATIVE_HOST*'){'BLOCKED_NATIVE_HOST'}else{'SETUP_ERROR'}
    $script:results.Add([pscustomobject]@{case='archive fixture/bootstrap';pass=$false;pass_=$false;status=$status;detail=[pscustomobject]@{error=$_.Exception.Message}})
} finally {
    if($script:StagingAttempt){ try{Clear-OwnedScratch}catch{} }; $script:StagingAttempt=$null
    $env:TEMP=$script:oldTemp; $env:TMP=$script:oldTmp; $env:USERPROFILE=$script:oldProfile
}

$setupFailed=@($script:results | Where-Object {$_.status -ne 'PASS'}).Count -gt 0
if(-not $NoMutations -and $setupFailed) { $script:results.Add([pscustomobject]@{case='mutation controls';pass=$false;pass_=$false;status='NOT_RUN_BASELINE';detail=[pscustomobject]@{reason='a baseline control did not pass; mutants not evaluated'}}) }
if(-not $NoMutations -and -not $setupFailed) {
    $text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
    $specs=@(
        @{name='archive-backslash-guard-removed';anchor=" -or `$relative.Contains('\')";target=$Backslash},
        @{name='asset-digest-check-removed';anchor=" -or (`$expectedDigest -and `$proof.Hash -cne `$expectedDigest)";target=$Digest},
        @{name='asset-size-check-removed';anchor="(`$null -ne `$expectedLength -and `$proof.Length -ne `$expectedLength) -or ";target=$Size},
        @{name='archive-crc-check-removed';anchor=" -or `$proof.Crc -ne `$member.Crc";target=$Crc}
    )
    foreach($spec in $specs) {
        $row=[ordered]@{mutant=$spec.name;target=$spec.target;positive=$Healthy}
        try {
            Assert-Control ([regex]::Matches($text,[regex]::Escape($spec.anchor)).Count -eq 1) ('Mutation anchor drift: '+$spec.name)
            $mutant=Join-Path $script:fixtureRoot ('mutant-'+$spec.name+'.ps1')
            [IO.File]::WriteAllText($mutant,$text.Replace($spec.anchor,''),$script:utf8)
            $row.mutantSha256=(Get-FileHash -LiteralPath $mutant -Algorithm SHA256).Hash.ToLowerInvariant()
            $childReport=Join-Path $script:fixtureRoot ('mutant-'+$spec.name+'.json')
            $null=& $script:hostExe -NoLogo -NoProfile -NonInteractive -File $PSCommandPath -SourceFile $mutant -FixtureParent $script:fixtureRoot -NoMutations -ReportPath $childReport -CaseList ($spec.target+'|'+$Healthy) 2>&1
            $child=[IO.File]::ReadAllText($childReport) | ConvertFrom-Json
            $base=@($script:results | Where-Object {$_.case -eq $spec.target})[0]
            $mt=@($child.results | Where-Object {$_.case -eq $spec.target})[0]
            $mp=@($child.results | Where-Object {$_.case -eq $Healthy})[0]
            $row.baseline=$base.status; $row.mutantTarget=$(if($mt){$mt.status}else{'MISSING'}); $row.mutantPositive=$(if($mp){$mp.status}else{'MISSING'})
            $row.mutantObservation=$(if($mt){$mt.detail}else{$null})
            $row.status=if($base.status -eq 'PASS' -and $mt -and $mt.status -eq 'FAIL' -and $mp -and $mp.status -eq 'PASS'){'KILLED'}else{'SURVIVED'}
        } catch { $row.status='ERROR'; $row.error=$_.Exception.Message }
        $script:mutations+=[pscustomobject]$row
        $script:results.Add([pscustomobject]@{case=('mutant '+$spec.name+' is detected');pass=($row.status -eq 'KILLED');pass_=($row.status -eq 'KILLED');status=$(if($row.status -eq 'KILLED'){'PASS'}else{'FAIL'});detail=[pscustomobject]$row})
    }
}
$removed=$null
if($script:fixtureRoot -and -not $NoMutations) { try { [IO.Directory]::Delete($script:fixtureRoot,$true); $removed=$true } catch { $removed=$false } }
$report=[pscustomobject]@{schema='r0015-archive-controls.v1';sourceSha256=$script:sourceHash;testSha256=$script:testHash;runtime=$PSVersionTable.PSVersion.ToString();edition=[string]$PSVersionTable.PSEdition;platform=[Environment]::OSVersion.VersionString;fixtureRemoved=$removed;results=$script:results.ToArray();mutations=$script:mutations}
$json=$report | ConvertTo-Json -Depth 12
if($ReportPath){ [IO.File]::WriteAllText($ReportPath,$json,$script:utf8) }
[Console]::WriteLine($json)
if(-not $script:nativeHost){exit 2}
if(@($script:results | Where-Object {$_.status -ne 'PASS'}).Count){exit 1}
exit 0
