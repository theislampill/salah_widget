param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [string]$OutputRoot=[IO.Path]::GetTempPath()
)
# Actual source policy; only volume responses are changed on native Windows.
# Linux adds explicit path/drive/identity adapters and earns no native claim.
$ErrorActionPreference='Stop'
$Utf8=[Text.UTF8Encoding]::new($false)
function Hash-Bytes([byte[]]$Bytes){$h=[Security.Cryptography.SHA256]::Create();try{return [BitConverter]::ToString($h.ComputeHash($Bytes)).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function Hash-Text([string]$Text){Hash-Bytes ([Text.Encoding]::UTF8.GetBytes($Text))}
function Assert-Probe([bool]$Condition,[string]$Message){if(-not $Condition){throw $Message}}
$sourceBytes=[IO.File]::ReadAllBytes($SourceFile);$sourceHash=Hash-Bytes $sourceBytes;$testHash=Hash-Bytes ([IO.File]::ReadAllBytes($PSCommandPath))
$raw=[Text.Encoding]::UTF8.GetString($sourceBytes)
$t=$null;$e=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($raw,[ref]$t,[ref]$e)
Assert-Probe (@($e).Count -eq 0) 'Actual source does not parse'
$definitions=@{}
foreach($definition in $ast.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){
    $definitions[$definition.Name]=$definition
    . ([scriptblock]::Create($definition.Extent.Text))
}
$literals=@($definitions['Initialize-StagingNative'].Body.FindAll({param($node) $node -is [Management.Automation.Language.StringConstantExpressionAst] -and $node.Value.Contains('namespace SalahInstaller') -and $node.Value.Contains('public static class StageNative')},$true))
Assert-Probe ($literals.Count -eq 1) 'Actual native source literal extraction is not unique'
$csharp=$literals[0].Value
$policyPattern='(?s)public static void RequireLocalAclVolume\(string path\).*?\n    }'
$policy=[regex]::Match($csharp,$policyPattern).Value
Assert-Probe ([bool]$policy) 'Actual C# volume policy was not found'
$nativeWindows=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$fixture=Join-Path ([IO.Path]::GetFullPath($OutputRoot)) ('r0015-volume-policy-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($fixture)
$control=Join-Path $fixture 'control';$temporary=Join-Path $fixture 'temp';$profile=Join-Path $fixture 'profile'
foreach($path in @($control,$temporary,$profile)){[void][IO.Directory]::CreateDirectory($path)}
$rows=[Collections.Generic.List[object]]::new();$adapters=[Collections.Generic.List[object]]::new();$healthyNative=$null
$oldTemp=[Environment]::GetEnvironmentVariable('TEMP','Process');$oldTmp=[Environment]::GetEnvironmentVariable('TMP','Process');$oldProfile=[Environment]::GetEnvironmentVariable('USERPROFILE','Process')
try{
    if($nativeWindows){
        $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
        foreach($path in @($fixture,$control,$temporary,$profile)){
            $acl=[Security.AccessControl.DirectorySecurity]::new();$acl.SetOwner($sid);$acl.SetAccessRuleProtection($true,$false)
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
            Set-Acl -LiteralPath $path -AclObject $acl
        }
        $env:TEMP=$temporary;$env:TMP=$temporary;$env:USERPROFILE=$profile
        $actualFormat=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($temporary)).DriveFormat
        Assert-Probe ($actualFormat -ceq 'NTFS') 'Native healthy control requires actual NTFS; no unsupported volume is created or credited'
        $script:DryRun=$false;$script:StagingAttempt=$null
        Initialize-Staging
        $scratch=[SalahInstaller.StageNative]::Inspect($script:StagingAttempt.Scratch.Path,$script:StagingAttempt.Sid)
        $retained=[SalahInstaller.StageNative]::Inspect($script:StagingAttempt.Retained.Path,$script:StagingAttempt.Sid)
        Assert-Probe ($scratch.Private -and $retained.Private) 'Actual unchanged NTFS staging positive failed'
        $healthyNative=[pscustomobject]@{pass=$true;filesystem=$actualFormat;scratchIdentity=$scratch.Identity;retainedIdentity=$retained.Identity;sourceSha256=$sourceHash}
        Clear-OwnedScratch
        $rows.Add([pscustomobject]@{case='actual NTFS Initialize-Staging positive';scope='actual native source, no volume adapter';pass=$true;observation=$healthyNative})
    }else{
        $rows.Add([pscustomobject]@{case='actual NTFS Initialize-Staging positive';scope='not executed on Windows';pass=$null;status='BLOCKED_NATIVE_HOST'})
    }
    $namespace='SalahVolumeProbe'+[guid]::NewGuid().ToString('N')
    $derived=$csharp.Replace('namespace SalahInstaller {','namespace '+$namespace+' {')
    $declaration='    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]'+"`n"+'    static extern bool GetVolumeInformationW(string root, StringBuilder name, uint nameSize, out uint serial, out uint maximumComponent, out uint flags, StringBuilder format, uint formatSize);'
    Assert-Probe ([regex]::Matches($derived,[regex]::Escape($declaration)).Count -eq 1) 'Native volume-response boundary signature drift'
    $boundary=@'
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true, EntryPoint="GetVolumeInformationW")]
    static extern bool ReadActualVolume(string root, StringBuilder name, uint nameSize, out uint serial, out uint maximumComponent, out uint flags, StringBuilder format, uint formatSize);
    public static bool FixtureNative, FixtureSuccess=true, FixturePreserveActual;
    public static string FixtureFilesystem="NTFS", FixtureActualFilesystem="";
    public static uint FixtureFlags=8;
    public static int FixtureCalls;
    public static bool FixtureNameRequested;
    public static bool GetVolumeInformationW(string root, StringBuilder name, uint nameSize, out uint serial, out uint maximumComponent, out uint flags, StringBuilder format, uint formatSize) {
      FixtureCalls++; FixtureNameRequested=format!=null && formatSize!=0;
      if (FixtureNative) {
        StringBuilder actual=new StringBuilder(64);
        bool ok=ReadActualVolume(root,name,nameSize,out serial,out maximumComponent,out flags,actual,64);
        FixtureActualFilesystem=actual.ToString();
        if (!ok) return false;
        if (FixturePreserveActual) { if (format!=null) format.Append(actual); return true; }
      } else { serial=1; maximumComponent=255; flags=8; FixtureActualFilesystem="NO_NATIVE_VOLUME"; }
      if (!FixtureSuccess) return false;
      flags=FixtureFlags;
      if (format!=null) { format.Length=0; format.Append(FixtureFilesystem); }
      return true;
    }
'@
    $derived=$derived.Replace($declaration,$boundary)
    $adapters.Add([pscustomobject]@{language='C#';kind='GetVolumeInformationW response boundary';nativeReadbackDelegated=$nativeWindows;policyBodyChanged=$false})
    if(-not $nativeWindows){
        foreach($replacement in @(
            @('System.IO.Path.GetPathRoot(path)','"C:\\"'),
            @('new DriveInfo(root).DriveType','DriveType.Fixed')
        )){
            Assert-Probe ([regex]::Matches($derived,[regex]::Escape($replacement[0])).Count -eq 1) 'Supplemental C# native path boundary drift'
            $derived=$derived.Replace($replacement[0],$replacement[1])
            $adapters.Add([pscustomobject]@{language='C#';kind='supplemental native path/drive read';from=$replacement[0];to=$replacement[1]})
        }
    }
    $normalizedPolicy=[regex]::Match($derived,$policyPattern).Value
    if(-not $nativeWindows){$normalizedPolicy=$normalizedPolicy.Replace('"C:\\"','System.IO.Path.GetPathRoot(path)').Replace('DriveType.Fixed','new DriveInfo(root).DriveType')}
    Assert-Probe ($normalizedPolicy -ceq $policy) 'Actual C# volume decision logic changed beyond declared read adapters'
    [IO.File]::WriteAllText((Join-Path $control 'actual-native-literal.cs'),$csharp,$Utf8)
    [IO.File]::WriteAllText((Join-Path $control 'volume-response-derived.cs'),$derived,$Utf8)
    Microsoft.PowerShell.Utility\Add-Type -TypeDefinition $derived -ErrorAction Stop
    $probeType=($namespace+'.StageNative') -as [type]
    Assert-Probe ($null -ne $probeType) 'Derived exact-source type did not load'
    $probeType::FixtureNative=$nativeWindows
    $cases=@(
        @('reported NTFS','NTFS',8,$true,$true),
        @('reported ReFS','ReFS',8,$true,$false),
        @('reported unknown filesystem','',8,$true,$false),
        @('reported unsupported filesystem','OtherFS',8,$true,$false),
        @('NTFS without persistent ACLs','NTFS',0,$true,$false),
        @('volume query failure','NTFS',8,$false,$false)
    )
    foreach($case in $cases){
        $probeType::FixtureFilesystem=$case[1];$probeType::FixtureFlags=[uint32]$case[2];$probeType::FixtureSuccess=$case[3];$probeType::FixtureCalls=0;$probeType::FixtureNameRequested=$false
        $accepted=$true;$reason=$null
        try{$probeType::RequireLocalAclVolume($(if($nativeWindows){$temporary}else{'C:\fixture'}))}catch{$accepted=$false;$reason=$_.Exception.Message}
        $rows.Add([pscustomobject]@{case=('C# '+$case[0]);scope='actual RequireLocalAclVolume with declared read boundary';expectedAccepted=$case[4];accepted=$accepted;pass=($accepted -eq $case[4] -and $probeType::FixtureCalls -eq 1);reason=$reason;volumeCalls=$probeType::FixtureCalls;filesystemBufferRequested=$probeType::FixtureNameRequested;reportedFilesystem=$case[1];actualNativeFilesystem=$probeType::FixtureActualFilesystem})
    }
    $originalCompiler=$definitions['New-StagingCompilerContext'].Extent.Text
    $compiler=$originalCompiler
    if(-not $nativeWindows){
        # The actual context reads User and token Owner, then disposes the
        # identity wrapper. Replace only that unsupported native read here.
        function New-FixtureIdentity {
            $value=[pscustomobject]@{User=[pscustomobject]@{Value='S-1-5-21-0'};Owner=[pscustomobject]@{Value='S-1-5-21-0'}}
            $value|Add-Member -MemberType ScriptMethod -Name Dispose -Value {}
            return $value
        }
        foreach($replacement in @(
            @('[Security.Principal.WindowsIdentity]::GetCurrent()','(New-FixtureIdentity)'),
            @('[IO.Path]::GetTempPath()','''C:\fixture'''),
            @('[IO.Path]::GetFullPath($path).TrimEnd([IO.Path]::DirectorySeparatorChar)','$path'),
            @('[IO.Path]::GetPathRoot($full)','''C:\'''),
            @('[IO.DriveInfo]::new($root).DriveType','[IO.DriveType]::Fixed')
        )){
            Assert-Probe ([regex]::Matches($compiler,[regex]::Escape($replacement[0])).Count -eq 1) 'Supplemental compiler native read boundary drift'
            $compiler=$compiler.Replace($replacement[0],$replacement[1])
            $adapters.Add([pscustomobject]@{language='PowerShell';kind='supplemental native identity/path/drive read';from=$replacement[0];to=$replacement[1]})
        }
        function Join-Path([string]$Path,[string]$ChildPath){return $Path.TrimEnd('\')+'\'+$ChildPath}
        $adapters.Add([pscustomobject]@{language='PowerShell';kind='supplemental Join-Path returns Windows path string; no filesystem call'})
    }
    . ([scriptblock]::Create($compiler))
    $script:volumeProbeType=$probeType
    function Initialize-CompilerNative {return $script:volumeProbeType}
    function Open-CompilerDirectoryLease {throw 'FIXTURE_STOP_AFTER_VOLUME_ADMISSION'}
    $adapters.Add([pscustomobject]@{language='PowerShell';kind='actual compiler initializer receives response-boundary type; first directory lease stops invocation before any allocation'})
    $script:DryRun=$false
    foreach($case in $cases){
        $probeType::FixtureFilesystem=$case[1];$probeType::FixtureFlags=[uint32]$case[2];$probeType::FixtureSuccess=$case[3];$probeType::FixtureCalls=0;$probeType::FixtureNameRequested=$false
        $reason=$null;try{$null=New-StagingCompilerContext}catch{$reason=$_.Exception.Message}
        $accepted=$reason -ceq 'FIXTURE_STOP_AFTER_VOLUME_ADMISSION'
        $rows.Add([pscustomobject]@{case=('PowerShell '+$case[0]);scope='actual compiler context stops at first lease after volume policy';expectedAccepted=$case[4];accepted=$accepted;pass=($accepted -eq $case[4] -and $probeType::FixtureCalls -eq 1);reason=$reason;volumeCalls=$probeType::FixtureCalls;filesystemBufferRequested=$probeType::FixtureNameRequested;reportedFilesystem=$case[1];actualNativeFilesystem=$probeType::FixtureActualFilesystem;contextCreated=$script:CompilerScratch.Created;contextPath=$script:CompilerScratch.Path})
    }
    [IO.File]::WriteAllText((Microsoft.PowerShell.Management\Join-Path $control 'actual-compiler-function.ps1'),$originalCompiler,$Utf8)
    [IO.File]::WriteAllText((Microsoft.PowerShell.Management\Join-Path $control 'compiler-read-derived.ps1'),$compiler,$Utf8)
}finally{
    foreach($saved in @(@('TEMP',$oldTemp),@('TMP',$oldTmp),@('USERPROFILE',$oldProfile))){$value=if($null -eq $saved[1]){[System.Management.Automation.Language.NullString]::Value}else{$saved[1]};[Environment]::SetEnvironmentVariable($saved[0],$value,'Process')}
}
$policyRows=@($rows|Where-Object{$null -ne $_.expectedAccepted})
$healthyRows=@($policyRows|Where-Object{$_.reportedFilesystem -ceq 'NTFS'})
$unsupported=@($policyRows|Where-Object{$_.reportedFilesystem -cne 'NTFS' -and $_.accepted})
$sourceStable=(Hash-Bytes ([IO.File]::ReadAllBytes($SourceFile))) -ceq $sourceHash
$testStable=(Hash-Bytes ([IO.File]::ReadAllBytes($PSCommandPath))) -ceq $testHash
$report=[pscustomobject]@{
    schema='r0015-volume-admission-policy.v1';pass=($sourceStable -and $testStable -and @($policyRows|Where-Object{-not $_.pass}).Count -eq 0);nativeWindows=$nativeWindows
    source=$SourceFile;sourceSha256=$sourceHash;sourceUnchanged=$sourceStable
    testSha256=$testHash;testUnchanged=$testStable;host=$PSVersionTable.PSVersion.ToString();fixture=$fixture
    actualCSharpLiteralSha256=(Hash-Text $csharp);actualCSharpVolumePolicySha256=(Hash-Text $policy);normalizedPolicyEqual=$true;actualCompilerFunctionSha256=(Hash-Text $originalCompiler)
    healthyControlsPass=(@($healthyRows|Where-Object{-not $_.pass}).Count -eq 0);unsupportedReportsAccepted=@($unsupported|ForEach-Object{$_.case})
    nativeNTFSHealthy=$healthyNative;adapters=$adapters.ToArray();results=$rows.ToArray()
    limits=@('Counterfactual reported-volume responses are not execution on ReFS or an unsupported filesystem.','Actual source decision logic is preserved; local path/identity adapters are declared separately.','No unsupported volume is created, mounted or modified. No real profile is used.','Supplemental Linux policy evidence cannot qualify Windows ACL, identity, private creation, leases or native NTFS.')
}
$json=$report|ConvertTo-Json -Depth 12
[IO.File]::WriteAllText((Microsoft.PowerShell.Management\Join-Path $fixture 'results.json'),$json,$Utf8)
[Console]::WriteLine($json)
if(-not $report.pass){exit 1}
