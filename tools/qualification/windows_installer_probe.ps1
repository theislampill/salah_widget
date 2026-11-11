#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [ValidateSet('All','compiler-ascii','compiler-unicode','path-length')][string]$Mode='All',
    [string]$ResultFile,
    [int]$ChildTimeoutSeconds=180,
    [switch]$InternalChild,
    [string]$CaseRoot,
    [string]$TempParent,
    [string]$Nonce,
    [string]$ExpectedSourceSha256='f801480d0f7ecbf7d5aec6a575036bc6fef7788dca68cde23ed4847ca9974140'
)
# Forensic acquisition only. No product PASS, installer main, downloads, browser,
# clipboard, unproved cleanup, source rewriting, or assembly adoption from csc.
$ErrorActionPreference='Stop'
$script:Utf8=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$script:Utf8
$script:Messages=[Collections.Generic.List[string]]::new()
$script:EvidenceNumber=0
function Probe-HashBytes([byte[]]$Bytes){$h=[Security.Cryptography.SHA256]::Create();try{[BitConverter]::ToString($h.ComputeHash($Bytes)).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function Probe-Hash([string]$Path){Probe-HashBytes ([IO.File]::ReadAllBytes($Path))}
function Probe-Require([bool]$Value,[string]$Message){if(-not $Value){throw $Message}}
function Probe-Exception($Record){
    $chain=@();$e=$Record.Exception;$n=0
    while($e -and $n -lt 24){$chain += [pscustomobject]@{type=$e.GetType().FullName;message=$e.Message;hresult=$e.HResult;win32=if($e -is [ComponentModel.Win32Exception]){$e.NativeErrorCode}else{$null};stack=$e.StackTrace};$e=$e.InnerException;$n++}
    [pscustomobject]@{text=[string]$Record;fullyQualifiedErrorId=$Record.FullyQualifiedErrorId;category=[string]$Record.CategoryInfo;position=if($Record.InvocationInfo){$Record.InvocationInfo.PositionMessage}else{$null};scriptStack=$Record.ScriptStackTrace;chain=$chain}
}
function Probe-Write([string]$Path,[byte[]]$Bytes){$f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$f.Write($Bytes,0,$Bytes.Length)}finally{$f.Dispose()}}
function Probe-Json([string]$Path,$Value){Probe-Write $Path ($script:Utf8.GetBytes(($Value|ConvertTo-Json -Depth 28)))}
function Probe-Identity {
    $id=[Security.Principal.WindowsIdentity]::GetCurrent()
    try{[pscustomobject]@{user=$id.User.Value;owner=if($id.Owner){$id.Owner.Value}else{$null};impersonation=[string]$id.ImpersonationLevel;encodingDefaultCodePage=[Text.Encoding]::Default.CodePage;processId=$PID}}finally{$id.Dispose()}
}
function Probe-Context($Context){
    if(-not $Context){return $null}
    [pscustomobject]@{id=$Context.Id;status=$Context.Status;path=$Context.Path;identity=$Context.Identity;sid=$Context.Sid;created=$Context.Created;cleanupError=$Context.CleanupError;rootLeaseClosed=if($Context.RootLease){$Context.RootLease.Handle.IsClosed}else{$null};parentLeases=@($Context.Leases|ForEach-Object{[pscustomobject]@{facts=$_.Facts;closed=$_.Handle.IsClosed}})}
}
function Probe-Extended([string]$Path){if($Path.StartsWith('\\?\',[StringComparison]::Ordinal)){$Path}else{'\\?\'+$Path}}
function Probe-U32([IntPtr]$Pointer,[int]$Offset){[BitConverter]::ToUInt32([BitConverter]::GetBytes([Runtime.InteropServices.Marshal]::ReadInt32($Pointer,$Offset)),0)}
function Probe-Native([string]$Path,[switch]$CaptureBytes){
    # Read-only native observation. It does not change or substitute product admission.
    $native=Initialize-CompilerNative;$h=$null;$info=[IntPtr]::Zero;$sd=[IntPtr]::Zero
    $o=[ordered]@{path=$Path;utf16Length=$Path.Length;native=$null;getAcl=$null;stageInspect=$null;bytes=$null;errors=@()}
    try{
        # Decimal avoids the signed high-bit hex conversion trap in PS5.1.
        $access=if($CaptureBytes){[uint32]2147614848}else{[uint32]0x20080}
        $h=$native::CreateFileW((Probe-Extended $Path),$access,7,[IntPtr]::Zero,3,0x02200000,[IntPtr]::Zero)
        if($h.IsInvalid){$code=[Runtime.InteropServices.Marshal]::GetLastWin32Error();throw [ComponentModel.Win32Exception]::new($code,'Probe native open')}
        $info=[Runtime.InteropServices.Marshal]::AllocHGlobal(52)
        if(-not $native::GetFileInformationByHandle($h,$info)){throw [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error(),'Probe native identity')}
        $attributes=Probe-U32 $info 0;$physical=[Text.StringBuilder]::new(32768)
        $count=$native::GetFinalPathNameByHandleW($h,$physical,[uint32]$physical.Capacity,0)
        Probe-Require ($count -gt 0 -and $count -lt $physical.Capacity) 'Probe cannot acquire physical path'
        $owner=[IntPtr]::Zero;$group=[IntPtr]::Zero;$dacl=[IntPtr]::Zero;$sacl=[IntPtr]::Zero
        $code=$native::GetSecurityInfo($h,1,5,[ref]$owner,[ref]$group,[ref]$dacl,[ref]$sacl,[ref]$sd)
        if($code -ne 0){throw [ComponentModel.Win32Exception]::new([int]$code,'Probe native security')}
        $raw=New-Object byte[] ($native::GetSecurityDescriptorLength($sd));[Runtime.InteropServices.Marshal]::Copy($sd,$raw,0,$raw.Length)
        $security=[Security.AccessControl.RawSecurityDescriptor]::new($raw,0)
        $length=([uint64](Probe-U32 $info 32)*4294967296)+[uint64](Probe-U32 $info 36)
        $o.native=[pscustomobject]@{physical=$physical.ToString();identity=('{0:x8}:{1:x8}{2:x8}' -f (Probe-U32 $info 28),(Probe-U32 $info 44),(Probe-U32 $info 48));attributes=$attributes;directory=(($attributes -band 16) -ne 0);reparse=(($attributes -band 1024) -ne 0);fileType=$native::GetFileType($h);length=$length;links=(Probe-U32 $info 40);creationLow=(Probe-U32 $info 4);creationHigh=(Probe-U32 $info 8);writeLow=(Probe-U32 $info 20);writeHigh=(Probe-U32 $info 24);owner=if($security.Owner){$security.Owner.Value}else{$null};group=if($security.Group){$security.Group.Value}else{$null};controlFlags=[string]$security.ControlFlags;sddl=$security.GetSddlForm([Security.AccessControl.AccessControlSections]::All);rawSecurityBase64=[Convert]::ToBase64String($raw);rawSecuritySha256=(Probe-HashBytes $raw)}
        if($CaptureBytes -and -not $o.native.directory){
            Probe-Require (-not $o.native.reparse -and $o.native.fileType -eq 1 -and $o.native.links -eq 1 -and $length -le 16777216) 'Probe file capture refused reparse/type/link/size boundary'
            $stream=[IO.FileStream]::new($h,[IO.FileAccess]::Read);$memory=[IO.MemoryStream]::new()
            try{$stream.CopyTo($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose();$stream.Dispose()}
            Probe-Require ($bytes.Length -eq $length) 'Probe file changed length during capture'
            $copy=Join-Path $script:EvidenceRoot ('raw-{0:d5}.bin' -f $script:EvidenceNumber);$script:EvidenceNumber++
            Probe-Write $copy $bytes
            $o.bytes=[pscustomobject]@{length=$bytes.Length;sha256=(Probe-HashBytes $bytes);rawCopy=$copy;copySha256=(Probe-Hash $copy);firstBytesBase64=[Convert]::ToBase64String($bytes,0,[Math]::Min(16,$bytes.Length))}
        }
    }catch{$o.errors += (Probe-Exception $_)}finally{if($sd -ne [IntPtr]::Zero){[void]$native::LocalFree($sd)};if($info -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::FreeHGlobal($info)};if($h){$h.Dispose()}}
    try{$acl=Microsoft.PowerShell.Security\Get-Acl -LiteralPath $Path -ErrorAction Stop;$o.getAcl=[pscustomobject]@{owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;sddl=$acl.Sddl;rawSecurityBase64=[Convert]::ToBase64String($acl.GetSecurityDescriptorBinaryForm())}}catch{$o.getAcl=[pscustomobject]@{error=(Probe-Exception $_)}}
    if('SalahInstaller.StageNative' -as [type]){try{$o.stageInspect=[SalahInstaller.StageNative]::Inspect($Path,$script:Sid)}catch{$o.stageInspect=[pscustomobject]@{error=(Probe-Exception $_)}}}
    $o.role=switch([IO.Path]::GetExtension($Path).ToLowerInvariant()){'.cmdline'{'compiler-command-line'}'.cs'{'compiler-source'}'.dll'{'compiler-output'}default{'other'}}
    [pscustomobject]$o
}
function Probe-Snapshot([string]$Root,[string]$Label,[switch]$CaptureBytes){
    $rows=[Collections.Generic.List[object]]::new();$errors=@();$pending=[Collections.Generic.Queue[object]]::new();$pending.Enqueue(@($Root,0))
    while($pending.Count){
        $item=$pending.Dequeue();$path=[string]$item[0];$depth=[int]$item[1]
        if($rows.Count -ge 128 -or $depth -gt 8){$errors += 'Snapshot bounded inventory exceeded';break}
        $row=Probe-Native $path -CaptureBytes:$CaptureBytes;$rows.Add($row)
        if($row.native -and $row.native.directory -and -not $row.native.reparse){try{foreach($child in [IO.Directory]::EnumerateFileSystemEntries($path)){$pending.Enqueue(@($child,($depth+1)))}}catch{$errors += (Probe-Exception $_)}}
    }
    $complete=$errors.Count -eq 0 -and @($rows|Where-Object{-not $_.native -or $_.errors.Count -ne 0 -or ($CaptureBytes -and -not $_.native.directory -and -not $_.bytes)}).Count -eq 0
    [pscustomobject]@{label=$Label;root=$Root;rows=$rows.ToArray();errors=$errors;complete=$complete}
}
function Probe-NewDirectory([string]$Path,[switch]$FixtureAmbientParent){
    $native=Initialize-CompilerNative;$parent=[IO.Path]::GetDirectoryName($Path);$proof=Open-CompilerDirectoryLease $parent $script:Sid ''
    $descriptor=[IntPtr]::Zero;$attributes=[IntPtr]::Zero
    try{
        if($FixtureAmbientParent){Probe-Require $proof.Facts.TrustedAncestor 'Fresh fixture parent is not replacement-safe'}
        else{Probe-Require $proof.Facts.Private 'Fixture creation requires its already private immediate parent'}
        $security=[Security.AccessControl.RawSecurityDescriptor]::new('O:'+$script:Sid+'D:P(A;OICI;FA;;;'+$script:Sid+')');$bytes=New-Object byte[] $security.BinaryLength;$security.GetBinaryForm($bytes,0)
        $descriptor=[Runtime.InteropServices.Marshal]::AllocHGlobal($bytes.Length);[Runtime.InteropServices.Marshal]::Copy($bytes,0,$descriptor,$bytes.Length)
        $size=if([IntPtr]::Size -eq 8){24}else{12};$attributes=[Runtime.InteropServices.Marshal]::AllocHGlobal($size)
        [Runtime.InteropServices.Marshal]::WriteInt32($attributes,0,$size);[Runtime.InteropServices.Marshal]::WriteIntPtr($attributes,[IntPtr]::Size,$descriptor);[Runtime.InteropServices.Marshal]::WriteInt32($attributes,2*[IntPtr]::Size,0)
        if(-not $native::CreateDirectoryW($Path,$attributes)){throw [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error(),'Probe exclusive protected directory')}
        [void]$script:CreatedFixturePaths.Add($Path)
        $readback=Open-CompilerDirectoryLease $Path $script:Sid '';Probe-Require $readback.Facts.Private 'Probe protected directory readback failed';[void]$script:FixtureLeases.Add($readback)
    }finally{$proof.Handle.Dispose();if($attributes -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::FreeHGlobal($attributes)};if($descriptor -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::FreeHGlobal($descriptor)}}
}
function Probe-PrepareOutputRoot([string]$Path){
    # Fixture-only acquisition: ambient parent may be administrator-owned.
    # Product New-StagingCompilerContext still checks its new self-owned parent.
    Probe-Require ($Path -match '^[A-Za-z]:[\\/]' -and $Path -notmatch '[\x00-\x1f]' -and -not $Path.Substring(2).Contains(':')) 'Unsupported fixture root path'
    $full=[IO.Path]::GetFullPath($Path).TrimEnd('\');$parent=[IO.Path]::GetDirectoryName($full);$volume=[IO.Path]::GetPathRoot($full)
    Probe-Require ($parent -and $volume.Length -eq 3 -and [IO.DriveInfo]::new($volume).DriveType -ne [IO.DriveType]::Network) 'Fixture requires a local drive and a parent'
    $native=Initialize-CompilerNative;$serial=[uint32]0;$maximum=[uint32]0;$flags=[uint32]0;$format=[Text.StringBuilder]::new(32)
    Probe-Require ($native::GetVolumeInformationW($volume,$null,0,[ref]$serial,[ref]$maximum,[ref]$flags,$format,[uint32]$format.Capacity) -and ($flags -band 8) -ne 0 -and [string]::Equals($format.ToString(),'NTFS',[StringComparison]::OrdinalIgnoreCase)) 'Fixture requires reported NTFS and persistent ACLs'
    $trustedInstaller='';try{$trustedInstaller=([Security.Principal.NTAccount]::new('NT SERVICE','TrustedInstaller').Translate([Security.Principal.SecurityIdentifier])).Value}catch{}
    $paths=@($volume);$current=$volume
    foreach($part in $parent.Substring($volume.Length).Split([IO.Path]::DirectorySeparatorChar)){
        if(-not $part){continue}
        Probe-Require ($part -notin @('.','..') -and $part.Trim(' ') -ceq $part -and -not $part.EndsWith('.')) 'Ambiguous fixture ancestor'
        $current=$current.TrimEnd('\')+'\'+$part;$paths += $current
    }
    $facts=@()
    foreach($component in $paths){$lease=Open-CompilerDirectoryLease $component $script:Sid $trustedInstaller;[void]$script:FixtureLeases.Add($lease);Probe-Require $lease.Facts.TrustedAncestor 'Fixture ancestor permits foreign replacement';$facts += $lease.Facts}
    $leaf=[IO.Path]::GetFileName($full);Probe-Require ($leaf -and $leaf -notin @('.','..') -and $leaf.Trim(' ') -ceq $leaf -and -not $leaf.EndsWith('.')) 'Ambiguous fixture leaf'
    Probe-NewDirectory $full -FixtureAmbientParent
    $script:OutputRootAdmission=[pscustomobject]@{boundary='Fixture-only held TrustedAncestor chain and exclusive private current-user child; product TrustedParent unchanged';requested=$Path;path=$full;volumeName=$format.ToString();volumeFlags=$flags;ancestors=$facts;created=(Probe-Native $full)}
    return $full
}
function Probe-Release($Context){if($Context){if($Context.RootLease){$Context.RootLease.Handle.Dispose()};foreach($lease in $Context.Leases){$lease.Handle.Dispose()}}}
function Probe-Checkpoint([string]$Phase){$script:Report.phase=$Phase;$script:Report.messages=$script:Messages.ToArray();Probe-Json (Join-Path $CaseRoot ('phase-{0:d3}.json' -f $script:PhaseNumber)) $script:Report;$script:PhaseNumber++}
function Probe-Direct([string]$Executable,[string]$Arguments,[string]$Working,[string]$Label,[int]$Seconds=75){
    $out=Join-Path $script:EvidenceRoot ($Label+'.stdout.bin');$err=Join-Path $script:EvidenceRoot ($Label+'.stderr.bin')
    $fo=[IO.File]::Open($out,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);$fe=[IO.File]::Open($err,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $p=[Diagnostics.Process]::new();$info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$Executable;$info.Arguments=$Arguments;$info.WorkingDirectory=$Working;$info.UseShellExecute=$false;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    $info.EnvironmentVariables['POWERSHELL_TELEMETRY_OPTOUT']='1';$info.EnvironmentVariables['DOTNET_CLI_TELEMETRY_OPTOUT']='1';$info.EnvironmentVariables['POWERSHELL_UPDATECHECK']='Off';$p.StartInfo=$info
    $o=[ordered]@{executable=$Executable;arguments=$Arguments;workingDirectory=$Working;started=$false;timedOut=$false;exitCode=$null;stdout=$out;stderr=$err;error=$null;stdoutDrained=$false;stderrDrained=$false;input=$null;output=$null}
    try{
        [void]$p.Start();$o.started=$true;$o.pid=$p.Id;$p.StandardInput.Close();$ot=$p.StandardOutput.BaseStream.CopyToAsync($fo);$et=$p.StandardError.BaseStream.CopyToAsync($fe)
        $o.timedOut=-not $p.WaitForExit($Seconds*1000)
        if($o.timedOut){try{$kill=Join-Path ([Environment]::GetFolderPath('System')) 'taskkill.exe';& $kill /PID $p.Id /T /F 2>&1|ForEach-Object{[void]$script:Messages.Add([string]$_)}}catch{};if(-not $p.HasExited){$p.Kill()};[void]$p.WaitForExit(5000)}
        $o.stdoutDrained=$ot.Wait(5000);$o.stderrDrained=$et.Wait(5000);if($p.HasExited){$o.exitCode=$p.ExitCode}
    }catch{$o.error=Probe-Exception $_}finally{$fo.Dispose();$fe.Dispose();$p.Dispose()}
    $o.stdoutSha256=Probe-Hash $out;$o.stderrSha256=Probe-Hash $err;[pscustomobject]$o
}

$sourceHash=Probe-Hash $SourceFile;$testHash=Probe-Hash $PSCommandPath
if([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT){[Console]::WriteLine(([pscustomobject]@{schema='r0015-native4-forensics.v1';status='BLOCKED_NATIVE_HOST';diagnosticOnly=$true;installerQualified=$false;sourceFile=$SourceFile;sourceSha256=$sourceHash;testSha256=$testHash;mode=$Mode}|ConvertTo-Json));exit 2}
try {
Probe-Require ($env:POWERSHELL_TELEMETRY_OPTOUT -ceq '1' -and $env:DOTNET_CLI_TELEMETRY_OPTOUT -ceq '1' -and $env:POWERSHELL_UPDATECHECK -ceq 'Off') 'Opt-outs must be set by the launcher before this process starts'
Probe-Require ($sourceHash -ceq $ExpectedSourceSha256) 'Frozen source hash differs'
Probe-Require ($ChildTimeoutSeconds -ge 30 -and $ChildTimeoutSeconds -le 240) 'Child timeout outside bounded range'
$tokens=$null;$parseErrors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$parseErrors)
Probe-Require (@($parseErrors).Count -eq 0) 'Frozen source does not parse'
foreach($definition in $ast.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){. ([scriptblock]::Create($definition.Extent.Text))}
$script:DryRun=$false;$script:NoOpen=$true;$script:StagingAttempt=$null;$script:CompilerScratch=$null;$script:FixtureLeases=[Collections.Generic.List[object]]::new();$script:CreatedFixturePaths=[Collections.Generic.List[string]]::new();$script:OutputRootAdmission=$null;$script:Sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
function Write-Host {param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline);[void]$script:Messages.Add([string]$Object)}
function Invoke-WebRequest {throw 'FORENSIC FORBIDS NETWORK'}
function Invoke-RestMethod {throw 'FORENSIC FORBIDS NETWORK'}
function Set-Clipboard {throw 'FORENSIC FORBIDS CLIPBOARD'}
function Copy-Text {throw 'FORENSIC FORBIDS CLIPBOARD'}
function Start-Process {throw 'FORENSIC FORBIDS EXTERNAL ACTION'}
function Open-Url {throw 'FORENSIC FORBIDS BROWSER'}
function Read-Host {throw 'FORENSIC FORBIDS PROMPTS'}

if($InternalChild){
    $script:EvidenceRoot=Join-Path $CaseRoot 'evidence';$script:PhaseNumber=0
    $script:Report=[ordered]@{schema='r0015-native4-forensics.child.v1';diagnosticOnly=$true;installerQualified=$false;status='ACQUIRING';mode=$Mode;nonce=$Nonce;pid=$PID;sourceFile=$SourceFile;sourceSha256=$sourceHash;testSha256=$testHash;host=$PSVersionTable.PSVersion.ToString();identity=(Probe-Identity);fixture=$CaseRoot;tempParent=$TempParent;tempParentUtf16Length=$TempParent.Length;coldStageNative=(-not ('SalahInstaller.StageNative' -as [type]));coldCompilerNative=(-not ('SalahInstaller.CompilerNative' -as [type]));phase='starting';error=$null;messages=@()}
    try{
        Probe-Require ($Nonce -match '^[a-f0-9]{32}$' -and $Mode -ne 'All') 'Bad child invocation'
        Probe-Require ($script:Report.coldStageNative -and $script:Report.coldCompilerNative) 'Diagnostic child did not begin with cold actual native types'
        Probe-Require ($env:TEMP -ceq $TempParent -and $env:TMP -ceq $TempParent) 'Child temporary variables do not match the protected fixture'
        $caseLease=Open-CompilerDirectoryLease $CaseRoot $script:Sid '';[void]$script:FixtureLeases.Add($caseLease);Probe-Require $caseLease.Facts.Private 'Child case root is not private'
        $tempLease=Open-CompilerDirectoryLease $TempParent $script:Sid '';[void]$script:FixtureLeases.Add($tempLease);Probe-Require $tempLease.Facts.Private 'Child compiler parent is not private'
        $evidenceLease=Open-CompilerDirectoryLease $script:EvidenceRoot $script:Sid '';[void]$script:FixtureLeases.Add($evidenceLease);Probe-Require $evidenceLease.Facts.Private 'Child evidence root is not private'
        $script:Report.parentBefore=Probe-Native $TempParent
        $script:ActualClear=${function:Clear-StagingCompilerContext};$script:CompilerCalls=@();$script:NativeText=$null
        function Add-Type {
            param([string]$TypeDefinition,[string[]]$AssemblyName,[object]$CompilerParameters)
            if($AssemblyName){Microsoft.PowerShell.Utility\Add-Type -AssemblyName $AssemblyName;return}
            $ctx=$script:CompilerScratch
            Probe-Require ($ctx -and $ctx.Created -and $ctx.Identity -and $ctx.RootLease.Facts.Private -and -not $ctx.RootLease.Handle.IsClosed -and @($ctx.Leases|Where-Object{$_.Handle.IsClosed}).Count -eq 0) 'Compiler boundary lacks owned held custody'
            Probe-Require ($env:TEMP -ceq $ctx.Path -and $env:TMP -ceq $ctx.Path) 'Compiler boundary escaped its scoped TEMP/TMP'
            $script:NativeText=$TypeDefinition
            $script:CompilerCalls += [pscustomobject]@{context=(Probe-Context $ctx);identity=(Probe-Identity);temp=$env:TEMP;tmp=$env:TMP;nativeTemp=[IO.Path]::GetTempPath();sourceUtf8Sha256=(Probe-HashBytes ($script:Utf8.GetBytes($TypeDefinition)));compilerParameters=if($CompilerParameters){[pscustomobject]@{tempDir=$CompilerParameters.TempFiles.TempDir;keepFiles=$CompilerParameters.TempFiles.KeepFiles;compilerOptions=$CompilerParameters.CompilerOptions;generateInMemory=$CompilerParameters.GenerateInMemory;referencedAssemblies=@($CompilerParameters.ReferencedAssemblies)}}else{$null}}
            $script:Report.beforeCompiler=Probe-Snapshot $ctx.Path 'before-actual-Add-Type' -CaptureBytes
            Probe-Checkpoint 'before-actual-Add-Type'
            try{if($CompilerParameters){Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -CompilerParameters $CompilerParameters -ErrorAction Stop}else{Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $TypeDefinition -ErrorAction Stop}}
            catch{$script:Report.addTypeException=Probe-Exception $_;throw}
            finally{$script:Report.afterCompiler=Probe-Snapshot $ctx.Path 'after-actual-Add-Type-before-cleanup' -CaptureBytes;Probe-Checkpoint 'after-actual-Add-Type'}
        }
        function Clear-StagingCompilerContext($Context,[bool]$Compiled){
            $script:Report.beforeCleanup=Probe-Snapshot $Context.Path 'before-actual-cleanup' -CaptureBytes
            $script:Report.cleanupInput=[pscustomobject]@{compiled=$Compiled;context=(Probe-Context $Context)}
            & $script:ActualClear $Context $Compiled
            $script:Report.cleanupOutput=Probe-Context $Context
            $script:Report.afterCleanup=Probe-Snapshot $Context.Path 'after-actual-cleanup' -CaptureBytes
        }
        Probe-Checkpoint 'ready';[Console]::WriteLine('NATIVE4_READY:'+$Nonce+':'+$PID)
        $initialized=$false;$initializationError=$null
        try{Initialize-StagingNative;$initialized=$true}catch{$initializationError=Probe-Exception $_}
        $baseline=$script:CompilerScratch
        $script:Report.initialization=[pscustomobject]@{returned=$initialized;exception=$initializationError;stageNativeLoaded=($null -ne ('SalahInstaller.StageNative' -as [type]));compilerContext=(Probe-Context $baseline);calls=$script:CompilerCalls;restoredTemp=$env:TEMP;restoredTmp=$env:TMP}
        $script:Report.parentAfter=Probe-Snapshot $TempParent 'baseline-parent-after' -CaptureBytes
        Probe-Checkpoint 'baseline-complete'
        if($Mode -eq 'path-length'){
            if(-not ('SalahInstaller.StageNative' -as [type])){$script:Report.pathLengths=[pscustomobject]@{status='BLOCKED_NO_NATIVE_TYPE';reason='Actual initialization did not make StageNative available'}}
            else{
                $parent=Join-Path $CaseRoot 'lengths';Probe-NewDirectory $parent
                $proof=[SalahInstaller.StageNative]::Inspect($parent,$script:Sid);Probe-Require $proof.Private 'Length fixture parent does not satisfy actual private readback'
                $rows=@()
                foreach($length in @(259,260,261,268)){
                    $suffix='-'+$length+'.bin';$padding=$length-$parent.Length-1-$suffix.Length
                    Probe-Require ($padding -ge 1 -and ($padding+$suffix.Length) -le 255) 'Output root cannot host bounded exact-length leaf'
                    $path=$parent+'\'+('x'*$padding)+$suffix;Probe-Require ($path.Length -eq $length) 'Requested exact path length drifted'
                    $row=[ordered]@{path=$path;utf16Length=$path.Length;parentBefore=(Probe-Native $parent);bareReturned=$false;bareError=$null;extendedAttempted=$false;extendedReturned=$false;extendedError=$null}
                    try{[SalahInstaller.StageNative]::CreatePrivateFile($path,$script:Sid);$row.bareReturned=$true}catch{$row.bareError=Probe-Exception $_}
                    $row.afterBare=Probe-Native $path -CaptureBytes
                    if(-not $row.bareReturned -and -not $row.afterBare.native){
                        $absentCodes=@($row.afterBare.errors|ForEach-Object{$_.chain}|Where-Object{$null -ne $_.win32}|ForEach-Object{$_.win32})
                        if(@($absentCodes|Where-Object{$_ -in @(2,3)}).Count){$row.extendedAttempted=$true;try{[SalahInstaller.StageNative]::CreatePrivateFile((Probe-Extended $path),$script:Sid);$row.extendedReturned=$true}catch{$row.extendedError=Probe-Exception $_}}
                        else{$row.extendedSkipped='Native absence was not proved; no second creation attempted'}
                    }else{$row.extendedSkipped='Bare call returned or an object already exists; no collision presented as a prefix experiment'}
                    $row.afterExtended=Probe-Native $path -CaptureBytes
                    if($row.extendedAttempted){try{$row.stageInspectExtended=[SalahInstaller.StageNative]::Inspect((Probe-Extended $path),$script:Sid)}catch{$row.stageInspectExtended=[pscustomobject]@{error=(Probe-Exception $_)}}}
                    $row.parentAfter=Probe-Native $parent;$rows += [pscustomobject]$row
                }
                $script:Report.pathLengths=[pscustomobject]@{status='OBSERVED';parent=$proof;results=$rows;productQualification=$false}
            }
        }elseif($PSVersionTable.PSVersion.Major -eq 5){
            # Separate from the baseline: these files cannot affect its cleanup.
            $diagnostic=$null;$priorTemp=$env:TEMP;$priorTmp=$env:TMP
            try{
                $diagnostic=New-StagingCompilerContext;$env:TEMP=$diagnostic.Path;$env:TMP=$diagnostic.Path
                $script:Report.environmentContextBefore=Probe-Context $diagnostic
                $childCode='$ErrorActionPreference="Stop";$id=[Security.Principal.WindowsIdentity]::GetCurrent();$u=[Text.UTF8Encoding]::new($false);$o=[ordered]@{tempUtf8Base64=[Convert]::ToBase64String($u.GetBytes([string]$env:TEMP));tmpUtf8Base64=[Convert]::ToBase64String($u.GetBytes([string]$env:TMP));encodingDefaultCodePage=[Text.Encoding]::Default.CodePage;user=$id.User.Value;owner=$id.Owner.Value;pid=$PID};$id.Dispose();[Console]::WriteLine("NATIVE4_ENV:"+($o|ConvertTo-Json -Compress))'
                $encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($childCode));$hostExe=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
                $childArguments='-NoLogo -NoProfile -NonInteractive -EncodedCommand '+$encoded
                $tempFiles=[CodeDom.Compiler.TempFileCollection]::new($diagnostic.Path,$true);$out=$null;$err=$null
                $executor=[ordered]@{status='STARTING';commandLine='"'+$hostExe+'" '+$childArguments;tempDir=$tempFiles.TempDir;keepFiles=$tempFiles.KeepFiles;exitCode=$null;exception=$null}
                try{$executor.exitCode=[CodeDom.Compiler.Executor]::ExecWaitWithCapture(('"'+$hostExe+'" '+$childArguments),$tempFiles,[ref]$out,[ref]$err);$executor.status='RETURNED'}catch{$executor.status='THREW';$executor.exception=Probe-Exception $_}
                $executor.stdout=$out;$executor.stderr=$err;$executor.tempFiles=@($tempFiles)
                $script:Report.executor=[pscustomobject]$executor
                $script:Report.executorFiles=Probe-Snapshot $diagnostic.Path 'after-CodeDOM-Executor' -CaptureBytes
                $script:Report.directEnvironment=Probe-Direct $hostExe $childArguments ([Environment]::CurrentDirectory) 'direct-env'
                $script:Report.expectedChildEnvironment=[pscustomobject]@{tempUtf8Base64=[Convert]::ToBase64String($script:Utf8.GetBytes($diagnostic.Path));tmpUtf8Base64=[Convert]::ToBase64String($script:Utf8.GetBytes($diagnostic.Path));parentIdentity=(Probe-Identity)}
                if($script:NativeText){
                    $csc=Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'csc.exe'
                    if([IO.File]::Exists($csc)){
                        $cs=Join-Path $diagnostic.Path 'direct-native.cs';$dll=Join-Path $diagnostic.Path 'direct-native.dll';$bom=[Text.UTF8Encoding]::new($true)
                        Probe-Write $cs ($bom.GetPreamble()+$bom.GetBytes($script:NativeText))
                        $cscArgs='/nologo /target:library /utf8output /reference:System.dll /out:"'+$dll+'" "'+$cs+'"'
                        $script:Report.directCompiler=Probe-Direct $csc $cscArgs $diagnostic.Path 'direct-csc'
                        $script:Report.directCompiler.input=Probe-Native $cs -CaptureBytes;$script:Report.directCompiler.output=Probe-Native $dll -CaptureBytes
                        $script:Report.directCompilerScope='Exact captured nativeSource text, explicit direct Framework csc command; output retained only, never loaded or admitted. Options are recorded, not assumed identical to CodeDOM.'
                    }else{$script:Report.directCompiler=[pscustomobject]@{status='UNAVAILABLE_COMPILER';path=$csc}}
                }
                $script:Report.environmentContextAfter=Probe-Context $diagnostic;$script:Report.environmentFiles=Probe-Snapshot $diagnostic.Path 'diagnostic-context-retained' -CaptureBytes
            }catch{$script:Report.environmentDiagnosticError=Probe-Exception $_}finally{$env:TEMP=$priorTemp;$env:TMP=$priorTmp;Probe-Release $diagnostic;$script:CompilerScratch=$baseline}
        }else{$script:Report.environmentDiagnostic=[pscustomobject]@{status='NOT_APPLICABLE_HOST';reason='Framework CodeDOM Executor comparison is PS5.1-only'}}
        $script:Report.inputsStable=((Probe-Hash $SourceFile) -ceq $sourceHash -and (Probe-Hash $PSCommandPath) -ceq $testHash)
        Probe-Require $script:Report.inputsStable 'Input bytes changed during acquisition'
        $script:Report.status='OBSERVATIONS_ACQUIRED'
    }catch{$script:Report.status='ACQUISITION_FAILED';$script:Report.error=Probe-Exception $_}
    finally{foreach($lease in $script:FixtureLeases){$lease.Handle.Dispose()};$script:Report.messages=$script:Messages.ToArray()}
    Probe-Checkpoint 'terminal';Probe-Json (Join-Path $CaseRoot 'result.json') $script:Report
    [Console]::WriteLine(($script:Report|ConvertTo-Json -Depth 28))
    if($script:Report.status -ne 'OBSERVATIONS_ACQUIRED'){exit 1};exit 0
}

$fixture=$null;$priorTemp=$env:TEMP;$priorTmp=$env:TMP;$hostExe=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
try{
    $OutputRoot=Probe-PrepareOutputRoot $OutputRoot
    $env:TEMP=$OutputRoot;$env:TMP=$env:TEMP
    $fixture=New-StagingCompilerContext
}finally{$env:TEMP=$priorTemp;$env:TMP=$priorTmp}
$root=$fixture.Path;$script:EvidenceRoot=$root
$sourceCopy=Join-Path $root 'source.ps1';Probe-Write $sourceCopy ([IO.File]::ReadAllBytes($SourceFile));Probe-Require ((Probe-Hash $sourceCopy) -ceq $sourceHash) 'Frozen source copy differs'
$cwd=Join-Path $root 'cwd';Probe-NewDirectory $cwd
$modes=if($Mode -eq 'All'){@('compiler-ascii','compiler-unicode','path-length')}else{@($Mode)}
$results=@();$counter=0
try{
    foreach($selected in $modes){
        $tag=switch($selected){'compiler-ascii'{'a'}'compiler-unicode'{'u'}'path-length'{'p'}}
        $case=Join-Path $root ('case-'+$tag);Probe-NewDirectory $case
        $temporary=Join-Path $root ('temp-'+$(if($selected -eq 'compiler-unicode'){[string][char]0x0635}elseif($selected -eq 'path-length'){'L'}else{'A'}));Probe-NewDirectory $temporary
        $evidence=Join-Path $case 'evidence';Probe-NewDirectory $evidence
        $subjectHome=Join-Path $case 'home';Probe-NewDirectory $subjectHome
        foreach($part in @('roaming','local','cache')){Probe-NewDirectory (Join-Path $subjectHome $part)}
        $nonceValue=[guid]::NewGuid().ToString('N')
        $arguments='-NoLogo -NoProfile -NonInteractive -File "'+$PSCommandPath+'" -SourceFile "'+$sourceCopy+'" -OutputRoot "'+$root+'" -Mode '+$selected+' -InternalChild -CaseRoot "'+$case+'" -TempParent "'+$temporary+'" -Nonce '+$nonceValue+' -ExpectedSourceSha256 '+$sourceHash
        $names=@('TEMP','TMP','HOME','USERPROFILE','APPDATA','LOCALAPPDATA','PSModuleAnalysisCachePath','DOTNET_CLI_HOME');$saved=@{}
        foreach($name in $names){$saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
        try{
            $env:TEMP=$temporary;$env:TMP=$temporary;$env:HOME=$subjectHome;$env:USERPROFILE=$subjectHome;$env:APPDATA=Join-Path $subjectHome 'roaming';$env:LOCALAPPDATA=Join-Path $subjectHome 'local';$env:PSModuleAnalysisCachePath=Join-Path $subjectHome 'cache\ModuleAnalysisCache';$env:DOTNET_CLI_HOME=$subjectHome
            $run=Probe-Direct $hostExe $arguments $cwd ('child-'+$tag) $ChildTimeoutSeconds
        }finally{foreach($name in $names){$restore=if($null -eq $saved[$name]){[Management.Automation.Language.NullString]::Value}else{$saved[$name]};[Environment]::SetEnvironmentVariable($name,$restore,'Process')}}
        $receipt=Join-Path $case 'result.json';$observed=$null;$receivingError=$null;$ready=$false
        try{
            $raw=[IO.File]::ReadAllBytes($run.stdout);$strict=[Text.UTF8Encoding]::new($false,$true);$text=$strict.GetString($raw)
            $ready=$text.Contains('NATIVE4_READY:'+$nonceValue+':')
            if([IO.File]::Exists($receipt)){$observed=[IO.File]::ReadAllText($receipt)|ConvertFrom-Json;Probe-Require ($observed.nonce -ceq $nonceValue -and $observed.sourceSha256 -ceq $sourceHash -and $observed.testSha256 -ceq $testHash -and $observed.pid -eq $run.pid) 'Child receipt nonce/PID/hash differs';$ready=$text.Contains('NATIVE4_READY:'+$nonceValue+':'+$observed.pid)}
        }catch{$receivingError=Probe-Exception $_}
        $results += [pscustomobject]@{mode=$selected;fixture=$case;tempParent=$temporary;tempParentUtf16Length=$temporary.Length;process=$run;ready=$ready;receipt=$receipt;receiptSha256=if([IO.File]::Exists($receipt)){Probe-Hash $receipt}else{$null};receivingError=$receivingError;observation=$observed;acquired=($ready -and $observed -and $observed.status -eq 'OBSERVATIONS_ACQUIRED' -and $run.exitCode -eq 0 -and -not $run.timedOut -and $run.stdoutDrained -and $run.stderrDrained -and -not $receivingError)}
        $counter++
    }
}finally{
    # Retain fixture and ancestor leases through the final receipt writes.
}
$stable=(Probe-Hash $SourceFile) -ceq $sourceHash -and (Probe-Hash $PSCommandPath) -ceq $testHash
$report=[pscustomobject]@{schema='r0015-native4-forensics.v1';diagnosticOnly=$true;installerQualified=$false;productPass=$false;status=if($stable -and @($results|Where-Object{-not $_.acquired}).Count -eq 0){'OBSERVATIONS_ACQUIRED'}else{'ACQUISITION_FAILED'};sourceFile=$SourceFile;sourceSha256=$sourceHash;testSha256=$testHash;inputsStable=$stable;mode=$Mode;host=$PSVersionTable.PSVersion.ToString();identity=(Probe-Identity);fixture=$root;fixtureContext=(Probe-Context $fixture);outputRootAdmission=$script:OutputRootAdmission;createdFixturePaths=$script:CreatedFixturePaths.ToArray();pairControl='ASCII temp-A versus temp-U+0635, private current-user descriptors and cold children. Compare actual recorded UTF-16 path lengths, ACLs, source hashes and CWD; All uses one shared fixture root, separately launched modes require equal-length OutputRoot names. Random private context IDs are equal-length.';results=$results;retention='No forensic fixture cleanup. Actual baseline source cleanup is delegated unchanged after raw capture. Extra Executor/direct-process/compiler artifacts use a separate owned context and are retained.';scope='Raw observations only. Native source failures, owner mismatches, prefix differences and acquisition labels are not product PASS.'}
Probe-Json (Join-Path $root 'results.json') $report
if($ResultFile){
    $resultParent=[IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ResultFile))
    Probe-Require ([string]::Equals($resultParent.TrimEnd('\'),[IO.Path]::GetFullPath($OutputRoot).TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)) 'ResultFile must be directly inside the admitted OutputRoot'
    $resultLease=Open-CompilerDirectoryLease $resultParent $script:Sid ''
    try{Probe-Require $resultLease.Facts.TrustedParent 'ResultFile parent custody changed';Probe-Json $ResultFile $report}finally{$resultLease.Handle.Dispose()}
}
[Console]::WriteLine(($report|ConvertTo-Json -Depth 28))
if($report.status -ne 'OBSERVATIONS_ACQUIRED'){exit 1}
} catch {
    $failure=[pscustomobject]@{schema='r0015-native4-forensics.v1';status='ACQUISITION_FAILED';diagnosticOnly=$true;installerQualified=$false;productPass=$false;mode=$Mode;sourceFile=$SourceFile;sourceSha256=$sourceHash;testSha256=$testHash;host=$PSVersionTable.PSVersion.ToString();fixture=if($fixture){$fixture.Path}else{$null};compilerContext=(Probe-Context $script:CompilerScratch);outputRootAdmission=$script:OutputRootAdmission;createdFixturePaths=@($script:CreatedFixturePaths);error=(Probe-Exception $_);messages=$script:Messages.ToArray()}
    [Console]::WriteLine(($failure|ConvertTo-Json -Depth 20));exit 1
} finally {
    foreach($lease in $script:FixtureLeases){$lease.Handle.Dispose()}
    Probe-Release $fixture
}
