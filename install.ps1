# Salah Widget Installer for Windows
# Safe wizard: detects browsers/profiles, refuses legacy Tabliss profiles, downloads TablissNG release assets,
# and stages the Salah Widget preset for manual import into TablissNG.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -PresetUrl "https://raw.githubusercontent.com/YOU/REPO/main/presets/salah-widget.tablissng.json"
#   powershell -File .\install.ps1 -DryRun  # offline local discovery; no writes, network, clipboard or browser opens
#
# Environment overrides:
#   SALAH_WIDGET_HASH        Optional URL-hash config (lat=..&lon=..&method=..) baked into the widget iframe
#   SALAH_WIDGET_PRESET_URL  Raw URL to your TablissNG preset JSON
#   SALAH_INSTALL_SOURCE     github | store | ask
#   TABLISSNG_REPO           owner/repo for upstream TablissNG, default BookCatKid/TablissNG

#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$PresetUrl = $(if ($env:SALAH_WIDGET_PRESET_URL) { $env:SALAH_WIDGET_PRESET_URL } else { "https://raw.githubusercontent.com/theislampill/salah_widget/main/presets/salah-widget.tablissng.json" }),
    [string]$WidgetHash = $(if ($env:SALAH_WIDGET_HASH) { $env:SALAH_WIDGET_HASH } else { "" }),
    [ValidateSet("ask", "github", "store")]
    [string]$InstallSource = $(if ($env:SALAH_INSTALL_SOURCE) { $env:SALAH_INSTALL_SOURCE } else { "github" }),
    [string]$TablissNgRepo = $(if ($env:TABLISSNG_REPO) { $env:TABLISSNG_REPO } else { "BookCatKid/TablissNG" }),
    [switch]$DryRun,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$ChromeTablissNgId = "dlaogejjiafeobgofajdlkkhjlignalk"
$EdgeTablissNgId   = "mkaphhbkcccpgkfaifhhdfckagnkcmhm"

$ChromeLegacyTablissId = "hipekcciheckooncpjeljhnekcoolahp"
$EdgeLegacyTablissId   = "lklaendlmlfkaabeleddanafeinnenih"

$ChromeStoreUrl  = "https://chromewebstore.google.com/detail/tablissng/$ChromeTablissNgId"
$FirefoxStoreUrl = "https://addons.mozilla.org/en-US/firefox/addon/tablissng/"
$EdgeStoreUrl    = "https://microsoftedge.microsoft.com/addons/detail/tablissng/$EdgeTablissNgId"

$WorkRoot = $null
$DownloadRoot = $null
$PresetRoot = $null
$script:StagingAttempt = $null

# These native boundaries are loaded only after the offline-preview guard. The
# protected descriptor is supplied at exclusive creation, never applied later
# to an adopted shared path. Readback uses native file identity, not a sidecar.
function Initialize-CompilerNative {
    if ($DryRun) { throw 'Offline preview does not load compiler custody support.' }
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw 'Native compiler custody requires Windows.' }
    $existing = 'SalahInstaller.CompilerNative' -as [type]
    if ($existing) { return $existing }
    # Emit only transient P/Invoke metadata. Bootstrap must not invoke a compiler.
    $name = [Reflection.AssemblyName]::new('SalahInstaller.CompilerBootstrap')
    $assembly = if ($PSVersionTable.PSVersion.Major -eq 5) {
        [AppDomain]::CurrentDomain.DefineDynamicAssembly($name, [Reflection.Emit.AssemblyBuilderAccess]::Run)
    } else { [Reflection.Emit.AssemblyBuilder]::DefineDynamicAssembly($name, [Reflection.Emit.AssemblyBuilderAccess]::Run) }
    $builder = $assembly.DefineDynamicModule($name.Name).DefineType('SalahInstaller.CompilerNative', [Reflection.TypeAttributes]'Public, Abstract, Sealed')
    $pointerRef = [IntPtr].MakeByRefType(); $uintRef = [uint32].MakeByRefType()
    $methods = @(
        @('CreateFileW','kernel32.dll',[Microsoft.Win32.SafeHandles.SafeFileHandle],@([string],[uint32],[uint32],[IntPtr],[uint32],[uint32],[IntPtr])),
        @('CreateDirectoryW','kernel32.dll',[bool],@([string],[IntPtr])),
        @('GetFileInformationByHandle','kernel32.dll',[bool],@([Microsoft.Win32.SafeHandles.SafeFileHandle],[IntPtr])),
        @('GetFinalPathNameByHandleW','kernel32.dll',[uint32],@([Microsoft.Win32.SafeHandles.SafeFileHandle],[Text.StringBuilder],[uint32],[uint32])),
        @('GetFileType','kernel32.dll',[uint32],@([Microsoft.Win32.SafeHandles.SafeFileHandle])),
        @('GetSecurityInfo','advapi32.dll',[uint32],@([Microsoft.Win32.SafeHandles.SafeFileHandle],[int],[uint32],$pointerRef,$pointerRef,$pointerRef,$pointerRef,$pointerRef)),
        @('GetSecurityDescriptorLength','advapi32.dll',[uint32],@([IntPtr])),
        @('LocalFree','kernel32.dll',[IntPtr],@([IntPtr])),
        @('GetVolumeInformationW','kernel32.dll',[bool],@([string],[Text.StringBuilder],[uint32],$uintRef,$uintRef,$uintRef,[Text.StringBuilder],[uint32]))
    )
    $constructor = [Runtime.InteropServices.DllImportAttribute].GetConstructor([type[]]@([string]))
    $fields = [Reflection.FieldInfo[]]@('EntryPoint','SetLastError','ExactSpelling','CharSet','CallingConvention' | ForEach-Object { [Runtime.InteropServices.DllImportAttribute].GetField($_) })
    foreach ($method in $methods) {
        $definition = $builder.DefineMethod($method[0],[Reflection.MethodAttributes]'Public, Static, PinvokeImpl',[Reflection.CallingConventions]::Standard,$method[2],[type[]]$method[3])
        $attribute = [Reflection.Emit.CustomAttributeBuilder]::new($constructor,[object[]]@($method[1]),$fields,[object[]]@($method[0],$true,$true,[Runtime.InteropServices.CharSet]::Unicode,[Runtime.InteropServices.CallingConvention]::Winapi))
        $definition.SetCustomAttribute($attribute)
        $definition.SetImplementationFlags($definition.GetMethodImplementationFlags() -bor [Reflection.MethodImplAttributes]::PreserveSig)
    }
    return $builder.CreateType()
}

function Open-CompilerDirectoryLease([string]$Path, [string]$Sid, [string]$TrustedInstallerSid) {
    if ($DryRun) { throw 'Offline preview does not inspect compiler custody paths.' }
    $native = Initialize-CompilerNative
    # Match StageNative.OpenDirectory: data access participates in delete sharing.
    $handle = $native::CreateFileW($Path,0x20081,3,[IntPtr]::Zero,3,0x02200000,[IntPtr]::Zero)
    if ($handle.IsInvalid) { $handle.Dispose(); throw [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error(),'Open compiler custody directory') }
    $information = [Runtime.InteropServices.Marshal]::AllocHGlobal(52)
    $descriptor = [IntPtr]::Zero
    try {
        if (-not $native::GetFileInformationByHandle($handle,$information)) { throw 'Cannot read compiler directory identity.' }
        $attributes = [Runtime.InteropServices.Marshal]::ReadInt32($information,0)
        if (($attributes -band 0x400) -ne 0 -or ($attributes -band 0x10) -eq 0 -or $native::GetFileType($handle) -ne 1) { throw 'Reparse or non-directory compiler path refused.' }
        $physical = [Text.StringBuilder]::new(32768)
        $count = $native::GetFinalPathNameByHandleW($handle,$physical,[uint32]$physical.Capacity,0)
        if ($count -eq 0 -or $count -ge $physical.Capacity) { throw 'Cannot read physical compiler path.' }
        $finalPath = $physical.ToString(); if ($finalPath.StartsWith('\\?\',[StringComparison]::Ordinal)) { $finalPath = $finalPath.Substring(4) }
        if (-not [string]::Equals($finalPath.TrimEnd('\'),[IO.Path]::GetFullPath($Path).TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Aliased compiler custody path refused.' }
        $owner=[IntPtr]::Zero; $group=[IntPtr]::Zero; $dacl=[IntPtr]::Zero; $sacl=[IntPtr]::Zero
        $code = $native::GetSecurityInfo($handle,1,5,[ref]$owner,[ref]$group,[ref]$dacl,[ref]$sacl,[ref]$descriptor)
        if ($code -ne 0) { throw [ComponentModel.Win32Exception]::new([int]$code,'Read compiler directory access control') }
        $bytes = New-Object byte[] ($native::GetSecurityDescriptorLength($descriptor))
        [Runtime.InteropServices.Marshal]::Copy($descriptor,$bytes,0,$bytes.Length)
        $security = [Security.AccessControl.RawSecurityDescriptor]::new($bytes,0)
        $actualOwner = if ($security.Owner) { $security.Owner.Value } else { '' }
        $trustedOwners = @($Sid,'S-1-5-18','S-1-5-32-544'); if ($TrustedInstallerSid) { $trustedOwners += $TrustedInstallerSid }
        $parentSafe = $actualOwner -ceq $Sid -and $null -ne $security.DiscretionaryAcl
        $ancestorSafe = $actualOwner -cin $trustedOwners -and $null -ne $security.DiscretionaryAcl
        $private = $parentSafe -and ($security.ControlFlags -band [Security.AccessControl.ControlFlags]::DiscretionaryAclProtected) -ne 0 -and $security.DiscretionaryAcl.Count -eq 1
        foreach ($ace in $security.DiscretionaryAcl) {
            if ($ace -isnot [Security.AccessControl.CommonAce] -or $ace.IsCallback) { $parentSafe=$false; $ancestorSafe=$false; $private=$false; continue }
            $allowed = $ace.AceQualifier -eq [Security.AccessControl.AceQualifier]::AccessAllowed
            $inheritOnly = ($ace.AceFlags -band [Security.AccessControl.AceFlags]::InheritOnly) -ne 0
            $principal = $ace.SecurityIdentifier.Value
            $mask = [uint64][BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$ace.AccessMask),0)
            # Keep these masks and trusted-owner rules identical to StageNative.Read.
            if ($allowed -and -not $inheritOnly -and ($mask -band 0x500d0156) -ne 0 -and $principal -cnotin @($Sid,'S-1-5-18','S-1-5-32-544')) { $parentSafe=$false }
            if ($allowed -and -not $inheritOnly -and ($mask -band 0x500d0150) -ne 0 -and $principal -cnotin $trustedOwners) { $ancestorSafe=$false }
            if (-not $allowed -or $inheritOnly -or $principal -cne $Sid -or ($mask -band 0x1f01ff) -ne 0x1f01ff) { $private=$false }
        }
        $identity = '{0:x8}:{1:x8}{2:x8}' -f [Runtime.InteropServices.Marshal]::ReadInt32($information,28),[Runtime.InteropServices.Marshal]::ReadInt32($information,44),[Runtime.InteropServices.Marshal]::ReadInt32($information,48)
        return [pscustomobject]@{Handle=$handle;Facts=[pscustomobject]@{Path=$finalPath;Identity=$identity;Owner=$actualOwner;Directory=$true;Private=$private;TrustedParent=$parentSafe;TrustedAncestor=$ancestorSafe}}
    } catch { $handle.Dispose(); throw }
    finally { if ($descriptor -ne [IntPtr]::Zero) { [void]$native::LocalFree($descriptor) }; [Runtime.InteropServices.Marshal]::FreeHGlobal($information) }
}

function New-StagingCompilerContext {
    if ($DryRun) { throw 'Offline preview does not allocate compiler scratch.' }
    $native = Initialize-CompilerNative
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $trustedInstaller = ''; try { $trustedInstaller = ([Security.Principal.NTAccount]::new('NT SERVICE','TrustedInstaller').Translate([Security.Principal.SecurityIdentifier])).Value } catch {}
    $context = [pscustomobject]@{Id=[guid]::NewGuid().ToString('N');Status='parent-admission';Path=$null;Identity=$null;Sid=$sid;Created=$false;RootLease=$null;Leases=[Collections.Generic.List[object]]::new();CleanupError=$null}
    $script:CompilerScratch = $context
    try {
        $path = [IO.Path]::GetTempPath()
        if (-not $path -or $path -notmatch '^[A-Za-z]:[\\/]' -or $path -match '[\x00-\x1f]' -or $path.Substring(2).Contains(':')) { throw 'Unsupported compiler parent path.' }
        $full = [IO.Path]::GetFullPath($path).TrimEnd([IO.Path]::DirectorySeparatorChar)
        $root = [IO.Path]::GetPathRoot($full)
        if ($root.Length -ne 3 -or [IO.DriveInfo]::new($root).DriveType -eq [IO.DriveType]::Network) { throw 'Compiler scratch requires a local drive.' }
        $serial=[uint32]0; $maximum=[uint32]0; $flags=[uint32]0
        $format=[Text.StringBuilder]::new(32)
        if (-not $native::GetVolumeInformationW($root,$null,0,[ref]$serial,[ref]$maximum,[ref]$flags,$format,[uint32]$format.Capacity) -or ($flags -band 8) -eq 0) { throw 'Compiler scratch requires persistent local access control.' }
        # The held-handle identity contract uses NTFS volume and 64-bit file IDs.
        if (-not [string]::Equals($format.ToString(),'NTFS',[StringComparison]::OrdinalIgnoreCase)) { throw 'Compiler scratch requires the supported NTFS filesystem.' }
        $paths=@($root); $current=$root
        foreach ($part in $full.Substring($root.Length).Split([IO.Path]::DirectorySeparatorChar)) {
            if (-not $part -or $part -in @('.','..') -or $part.Trim(' ') -cne $part -or $part.EndsWith('.')) { throw 'Ambiguous compiler parent component.' }
            $current=Join-Path $current $part; $paths += $current
        }
        $last=$null
        foreach ($component in $paths) {
            $lease=Open-CompilerDirectoryLease $component $sid $trustedInstaller; [void]$context.Leases.Add($lease)
            if (-not $lease.Facts.TrustedAncestor) { throw 'Compiler ancestor permits foreign replacement or has an untrusted owner.' }
            $last=$lease.Facts
        }
        if (-not $last.TrustedParent) { throw 'Compiler parent is not owned by this user with trusted write access.' }
        $context.Path=Join-Path $full ('SalahWidgetCompiler-'+$context.Id); $context.Status='candidate'
        $security=[Security.AccessControl.RawSecurityDescriptor]::new('O:'+ $sid +'D:P(A;OICI;FA;;;'+ $sid +')')
        $bytes=New-Object byte[] $security.BinaryLength; $security.GetBinaryForm($bytes,0)
        $descriptor=[Runtime.InteropServices.Marshal]::AllocHGlobal($bytes.Length)
        $size=if ([IntPtr]::Size -eq 8) {24} else {12}; $attributes=[Runtime.InteropServices.Marshal]::AllocHGlobal($size)
        try {
            [Runtime.InteropServices.Marshal]::Copy($bytes,0,$descriptor,$bytes.Length)
            [Runtime.InteropServices.Marshal]::WriteInt32($attributes,0,$size)
            [Runtime.InteropServices.Marshal]::WriteIntPtr($attributes,[IntPtr]::Size,$descriptor)
            [Runtime.InteropServices.Marshal]::WriteInt32($attributes,([IntPtr]::Size*2),0)
            if (-not $native::CreateDirectoryW($context.Path,$attributes)) { throw [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error(),'Create exclusive private compiler directory') }
            $context.Created=$true
        } finally { [Runtime.InteropServices.Marshal]::FreeHGlobal($attributes); [Runtime.InteropServices.Marshal]::FreeHGlobal($descriptor) }
        $context.RootLease=Open-CompilerDirectoryLease $context.Path $sid $trustedInstaller
        if (-not $context.RootLease.Facts.Private) { throw 'New compiler directory did not read back as private.' }
        $context.Identity=$context.RootLease.Facts.Identity; $context.Status='owned'
        return $context
    } catch {
        $context.Status=if ($context.Created) {'retained-unproved'} else {'refused-before-create'}
        if ($context.RootLease) { $context.RootLease.Handle.Dispose() }
        foreach ($lease in $context.Leases) { $lease.Handle.Dispose() }
        if ($context.Created) { Write-Warn ('Unproved compiler scratch retained at '+$context.Path) }
        throw
    }
}

function Clear-StagingCompilerContext($Context, [bool]$Compiled) {
    if ($DryRun) { return }
    if (-not $Context -or $Context.Status -in @('closed','retained-compilation-failed','retained-cleanup-failed','retained-unproved','refused-before-create')) { return }
    $descendantLeases=[Collections.Generic.List[object]]::new()
    try {
        if (-not $Compiled) { $Context.Status='retained-compilation-failed'; Write-Warn ('Compiler scratch retained after compilation failure at '+$Context.Path); return }
        $root=[SalahInstaller.StageNative]::Inspect($Context.Path,$Context.Sid)
        if (-not $root.Directory -or -not $root.Private -or $root.Identity -cne $Context.Identity) { throw 'Compiler scratch identity or private access changed.' }
        $pending=[Collections.Generic.Stack[string]]::new(); $pending.Push($Context.Path)
        $observed=[Collections.Generic.List[object]]::new()
        while ($pending.Count) {
            foreach ($path in [IO.Directory]::EnumerateFileSystemEntries($pending.Pop())) {
                $facts=[SalahInstaller.StageNative]::Inspect($path,$Context.Sid)
                if ($facts.Owner -cne $Context.Sid -or -not $facts.TrustedParent -or (-not $facts.Directory -and $facts.Links -ne 1)) { throw 'Compiler output custody could not be proved.' }
                [void]$observed.Add($facts)
                if ($facts.Directory) { $lease=[SalahInstaller.StageNative]::OpenDirectory($path,$Context.Sid); [void]$descendantLeases.Add($lease); $pending.Push($path) }
            }
        }
        foreach ($facts in $observed) { if ([SalahInstaller.StageNative]::Inspect($facts.Path,$Context.Sid).Identity -cne $facts.Identity) { throw 'Compiler output identity changed before cleanup.' } }
        foreach ($lease in $descendantLeases) { $lease.Dispose() }
        $Context.RootLease.Handle.Dispose()
        # The validated original ancestors remain leased through deletion.
        [IO.Directory]::Delete($Context.Path,$true)
        $Context.Status='closed'
    } catch { $Context.Status='retained-cleanup-failed'; $Context.CleanupError=$_.Exception.Message; Write-Warn ('Compiler scratch retained because cleanup custody failed at '+$Context.Path) }
    finally {
        foreach ($lease in $descendantLeases) { $lease.Dispose() }
        if ($Context.RootLease) { $Context.RootLease.Handle.Dispose() }
        foreach ($lease in $Context.Leases) { $lease.Handle.Dispose() }
    }
}

function Initialize-StagingNative {
    if ($DryRun) { throw "Offline preview does not load staging support." }
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw 'R0015 native staging requires Windows with persistent local ACLs.' }
    if (-not ('SalahInstaller.StageNative' -as [type])) {
        $compiler=New-StagingCompilerContext
        $previousTemp=[Environment]::GetEnvironmentVariable('TEMP','Process'); $previousTmp=[Environment]::GetEnvironmentVariable('TMP','Process')
        $compiled=$false
        try {
            [Environment]::SetEnvironmentVariable('TEMP',$compiler.Path,'Process'); [Environment]::SetEnvironmentVariable('TMP',$compiler.Path,'Process')
            if (-not [string]::Equals([IO.Path]::GetTempPath().TrimEnd('\'),$compiler.Path.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Native compiler temporary path did not use the owned directory.' }
            $compiler.Status='compiling'
            if (-not ('System.IO.Compression.ZipArchive' -as [type])) { Add-Type -AssemblyName System.IO.Compression }
            $nativeSource = @'
using System;
using System.IO;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using Microsoft.Win32.SafeHandles;
namespace SalahInstaller {
  public sealed class PathFacts {
    public string Path, Identity, Owner;
    public bool Directory, Private, TrustedParent, TrustedAncestor;
    public long Length;
    public uint Links;
  }
  public sealed class DirectoryLease : IDisposable {
    internal SafeFileHandle Handle;
    public PathFacts Facts;
    public void Dispose() { if (Handle != null) { Handle.Dispose(); Handle = null; } }
  }
  public sealed class ByteProof { public long Length; public uint Crc; public string Hash; }
  public static class StageNative {
    [StructLayout(LayoutKind.Sequential)] struct SecurityAttributes {
      public int Length; public IntPtr Descriptor; [MarshalAs(UnmanagedType.Bool)] public bool Inherit;
    }
    [StructLayout(LayoutKind.Sequential)] struct FileInformation {
      public uint Attributes; public System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write;
      public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool CreateDirectoryW(string path, ref SecurityAttributes security);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true, EntryPoint="CreateFileW")]
    static extern SafeFileHandle CreateSecuredFile(string path, uint access, uint share, ref SecurityAttributes security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle file, out FileInformation info);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetFinalPathNameByHandleW(SafeFileHandle file, StringBuilder path, uint length, uint flags);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint GetFileType(SafeFileHandle file);
    [DllImport("advapi32.dll", SetLastError=true)] static extern uint GetSecurityInfo(SafeFileHandle handle, int type, uint information, out IntPtr owner, out IntPtr group, out IntPtr dacl, out IntPtr sacl, out IntPtr descriptor);
    [DllImport("advapi32.dll")] static extern uint GetSecurityDescriptorLength(IntPtr descriptor);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr memory);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool GetVolumeInformationW(string root, StringBuilder name, uint nameSize, out uint serial, out uint maximumComponent, out uint flags, StringBuilder format, uint formatSize);
    static Exception Error(string operation) { return new Win32Exception(Marshal.GetLastWin32Error(), operation); }
    static string installerSid;
    static bool TrustedOwner(string owner, string user) {
      if (owner==user || owner=="S-1-5-18" || owner=="S-1-5-32-544") return true;
      // Resolve the local OS servicing principal only when needed. Do not
      // require self-ownership of the Windows volume/Users ancestors.
      if (installerSid==null) {
        try { installerSid=((SecurityIdentifier)new NTAccount("NT SERVICE", "TrustedInstaller").Translate(typeof(SecurityIdentifier))).Value; }
        catch { installerSid=""; }
      }
      return installerSid.Length!=0 && owner==installerSid;
    }
    static readonly uint[] CrcTable = MakeCrcTable();
    static uint[] MakeCrcTable() {
      uint[] table = new uint[256];
      for (uint i=0; i<256; i++) { uint value=i; for (int bit=0; bit<8; bit++) value=(value & 1) != 0 ? 0xedb88320u ^ (value >> 1) : value >> 1; table[i]=value; }
      return table;
    }
    public static ByteProof Fingerprint(Stream source, long maximum, Stream destination) {
      byte[] buffer = new byte[65536]; long length=0; uint crc=0xffffffffu;
      using (System.Security.Cryptography.SHA256 hash = System.Security.Cryptography.SHA256.Create()) {
        int count;
        while ((count=source.Read(buffer,0,buffer.Length)) != 0) {
          length += count; if (length > maximum) throw new IOException("Archive member exceeds its declared supported size.");
          for (int i=0; i<count; i++) crc=CrcTable[(crc ^ buffer[i]) & 255] ^ (crc >> 8);
          hash.TransformBlock(buffer,0,count,null,0); if (destination != null) destination.Write(buffer,0,count);
        }
        hash.TransformFinalBlock(new byte[0],0,0);
        return new ByteProof { Length=length, Crc=crc ^ 0xffffffffu, Hash=BitConverter.ToString(hash.Hash).Replace("-","").ToLowerInvariant() };
      }
    }
    static byte[] Exact(BinaryReader reader, int count) { byte[] bytes=reader.ReadBytes(count); if (bytes.Length != count) throw new IOException("Truncated ZIP structure."); return bytes; }
    static bool Same(byte[] first, byte[] second) { if (first.Length != second.Length) return false; for (int i=0; i<first.Length; i++) if (first[i] != second[i]) return false; return true; }
    // The supported archive contract is single-disk, non-ZIP64, stored/deflated
    // ZIP with checked central/local records, descriptors and member CRCs.
    public static uint[] ReadZipCrcs(Stream stream) {
      if (!stream.CanSeek || stream.Length < 22 || stream.Length > 134217728) throw new IOException("Unsupported ZIP size.");
      BinaryReader reader = new BinaryReader(stream, Encoding.UTF8, true);
      long tailStart=Math.Max(0,stream.Length-65557); stream.Position=tailStart; byte[] tail=Exact(reader,(int)(stream.Length-tailStart)); int end=-1;
      for (int i=tail.Length-22; i>=0; i--) if (BitConverter.ToUInt32(tail,i)==0x06054b50 && i+22+BitConverter.ToUInt16(tail,i+20)==tail.Length) { end=i; break; }
      if (end<0 || BitConverter.ToUInt16(tail,end+4)!=0 || BitConverter.ToUInt16(tail,end+6)!=0) throw new IOException("Unsupported or incomplete ZIP directory.");
      int count=BitConverter.ToUInt16(tail,end+10); uint centralSize=BitConverter.ToUInt32(tail,end+12), centralOffset=BitConverter.ToUInt32(tail,end+16);
      if (count==0 || count>10000 || count!=BitConverter.ToUInt16(tail,end+8) || (long)centralOffset+centralSize!=tailStart+end) throw new IOException("Inconsistent or unsupported ZIP directory.");
      uint[] crcs=new uint[count]; long[] starts=new long[count], ends=new long[count]; stream.Position=centralOffset;
      for (int i=0; i<count; i++) {
        byte[] central=Exact(reader,46); if (BitConverter.ToUInt32(central,0)!=0x02014b50) throw new IOException("Malformed ZIP central record.");
        ushort flags=BitConverter.ToUInt16(central,8), method=BitConverter.ToUInt16(central,10);
        uint compressed=BitConverter.ToUInt32(central,20), expanded=BitConverter.ToUInt32(central,24), local=BitConverter.ToUInt32(central,42);
        if ((flags & ~0x080e)!=0 || (method!=0 && method!=8) || compressed==uint.MaxValue || expanded==uint.MaxValue || local==uint.MaxValue || BitConverter.ToUInt16(central,34)!=0) throw new IOException("Unsupported encrypted, split or ZIP64 member.");
        crcs[i]=BitConverter.ToUInt32(central,16); byte[] name=Exact(reader,BitConverter.ToUInt16(central,28)); Exact(reader,BitConverter.ToUInt16(central,30)+BitConverter.ToUInt16(central,32));
        long nextCentral=stream.Position; stream.Position=local; byte[] header=Exact(reader,30);
        if (BitConverter.ToUInt32(header,0)!=0x04034b50 || BitConverter.ToUInt16(header,6)!=flags || BitConverter.ToUInt16(header,8)!=method) throw new IOException("ZIP local record disagrees with its directory.");
        byte[] localName=Exact(reader,BitConverter.ToUInt16(header,26)); if (!Same(name,localName)) throw new IOException("ZIP local member name differs.");
        Exact(reader,BitConverter.ToUInt16(header,28)); long dataEnd=stream.Position+compressed;
        if (local>=centralOffset || dataEnd>centralOffset) throw new IOException("ZIP member overlaps its directory.");
        if ((flags & 8)==0) {
          if (BitConverter.ToUInt32(header,14)!=crcs[i] || BitConverter.ToUInt32(header,18)!=compressed || BitConverter.ToUInt32(header,22)!=expanded) throw new IOException("ZIP local sizes or CRC differ.");
        } else {
          stream.Position=dataEnd; uint first=reader.ReadUInt32(); uint crc=first==0x08074b50 ? reader.ReadUInt32() : first;
          if (crc!=crcs[i] || reader.ReadUInt32()!=compressed || reader.ReadUInt32()!=expanded) throw new IOException("ZIP data descriptor differs."); dataEnd=stream.Position;
        }
        starts[i]=local; ends[i]=dataEnd; stream.Position=nextCentral;
      }
      if (stream.Position!=(long)centralOffset+centralSize) throw new IOException("Unexpected ZIP directory bytes.");
      Array.Sort(starts,ends); long previous=0;
      for (int i=0; i<count; i++) { if (starts[i]!=previous || ends[i]<=starts[i] || ends[i]>centralOffset) throw new IOException("Overlapping or unsupported ZIP member layout."); previous=ends[i]; }
      if (previous!=centralOffset) throw new IOException("Unaccounted ZIP payload bytes.");
      stream.Position=0; return crcs;
    }
    public static string CurrentSid() { using (WindowsIdentity identity = WindowsIdentity.GetCurrent()) { return identity.User.Value; } }
    public static void RequireLocalAclVolume(string path) {
      string root = System.IO.Path.GetPathRoot(path);
      if (root == null || root.Length != 3 || root[1] != ':' || new DriveInfo(root).DriveType == DriveType.Network)
        throw new IOException("Staging requires a supported local drive path.");
      uint serial, maximum, flags; StringBuilder format = new StringBuilder(32);
      if (!GetVolumeInformationW(root, null, 0, out serial, out maximum, out flags, format, (uint)format.Capacity)) throw Error("Read staging volume");
      if ((flags & 8) == 0) throw new IOException("Staging volume does not provide persistent access control.");
      if (!String.Equals(format.ToString(), "NTFS", StringComparison.OrdinalIgnoreCase)) throw new IOException("Staging requires the supported NTFS filesystem.");
    }
    static byte[] Descriptor(string sid, bool directory) {
      RawSecurityDescriptor descriptor = new RawSecurityDescriptor("O:" + sid + "D:P(A;" + (directory ? "OICI" : "") + ";FA;;;" + sid + ")");
      byte[] bytes = new byte[descriptor.BinaryLength]; descriptor.GetBinaryForm(bytes, 0); return bytes;
    }
    public static void CreatePrivateDirectory(string path, string sid) {
      byte[] bytes = Descriptor(sid, true); GCHandle pinned = GCHandle.Alloc(bytes, GCHandleType.Pinned);
      try {
        SecurityAttributes security = new SecurityAttributes(); security.Length = Marshal.SizeOf(typeof(SecurityAttributes)); security.Descriptor = pinned.AddrOfPinnedObject();
        if (!CreateDirectoryW(path, ref security)) throw Error("Create exclusive private staging directory");
      } finally { pinned.Free(); }
    }
    public static void CreatePrivateFile(string path, string sid) {
      byte[] bytes = Descriptor(sid, false); GCHandle pinned = GCHandle.Alloc(bytes, GCHandleType.Pinned);
      try {
        SecurityAttributes security = new SecurityAttributes(); security.Length = Marshal.SizeOf(typeof(SecurityAttributes)); security.Descriptor = pinned.AddrOfPinnedObject();
        using (SafeFileHandle file = CreateSecuredFile(path, 0xc0000000, 0, ref security, 1, 0x80, IntPtr.Zero)) {
          if (file.IsInvalid) throw Error("Create exclusive private staging file");
        }
      } finally { pinned.Free(); }
    }
    static PathFacts Read(SafeFileHandle handle, string path, string sid) {
      FileInformation info;
      if (!GetFileInformationByHandle(handle, out info)) throw Error("Read staging identity");
      if ((info.Attributes & 0x400) != 0 || GetFileType(handle) != 1) throw new IOException("Reparse or non-disk staging object refused.");
      StringBuilder physical = new StringBuilder(32768);
      uint count = GetFinalPathNameByHandleW(handle, physical, (uint)physical.Capacity, 0);
      if (count == 0 || count >= physical.Capacity) throw Error("Read physical staging path");
      string finalPath = physical.ToString(); if (finalPath.StartsWith("\\\\?\\", StringComparison.Ordinal)) finalPath = finalPath.Substring(4);
      if (!String.Equals(finalPath.TrimEnd('\\'), System.IO.Path.GetFullPath(path).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase)) throw new IOException("Aliased staging path refused.");
      IntPtr owner, group, dacl, sacl, descriptor;
      uint code = GetSecurityInfo(handle, 1, 5, out owner, out group, out dacl, out sacl, out descriptor);
      if (code != 0) throw new Win32Exception((int)code, "Read staging access control");
      try {
        byte[] bytes = new byte[GetSecurityDescriptorLength(descriptor)]; Marshal.Copy(descriptor, bytes, 0, bytes.Length);
        RawSecurityDescriptor security = new RawSecurityDescriptor(bytes, 0);
        string actualOwner = security.Owner == null ? "" : security.Owner.Value;
        bool parentSafe = actualOwner == sid && security.DiscretionaryAcl != null;
        bool ancestorSafe = TrustedOwner(actualOwner,sid) && security.DiscretionaryAcl != null;
        bool privateAcl = parentSafe && (security.ControlFlags & ControlFlags.DiscretionaryAclProtected) != 0 && security.DiscretionaryAcl.Count == 1;
        if (security.DiscretionaryAcl != null) foreach (GenericAce generic in security.DiscretionaryAcl) {
          CommonAce ace = generic as CommonAce;
          if (ace == null || ace.IsCallback) { parentSafe = false; ancestorSafe = false; privateAcl = false; continue; }
          bool allowed = ace.AceQualifier == AceQualifier.AccessAllowed;
          bool inheritOnly = (ace.AceFlags & AceFlags.InheritOnly) != 0;
          string principal = ace.SecurityIdentifier.Value;
          uint mask = unchecked((uint)ace.AccessMask);
          if (allowed && !inheritOnly && (mask & 0x500d0156u) != 0 && principal != sid && principal != "S-1-5-18" && principal != "S-1-5-32-544") parentSafe = false;
          // Earlier ancestors may grant create-file/create-directory (2/4)
          // without granting replacement, attribute or ACL/owner authority.
          if (allowed && !inheritOnly && (mask & 0x500d0150u) != 0 && principal != sid && principal != "S-1-5-18" && principal != "S-1-5-32-544" && !TrustedOwner(principal,sid)) ancestorSafe = false;
          if (!allowed || inheritOnly || principal != sid || (mask & 0x1f01ffu) != 0x1f01ffu) privateAcl = false;
        }
        return new PathFacts { Path=finalPath, Identity=info.Volume.ToString("x8") + ":" + info.IndexHigh.ToString("x8") + info.IndexLow.ToString("x8"), Owner=actualOwner,
          Directory=(info.Attributes & 0x10) != 0, Private=privateAcl, TrustedParent=parentSafe, TrustedAncestor=ancestorSafe, Length=((long)info.SizeHigh << 32) | info.SizeLow, Links=info.Links };
      } finally { if (descriptor != IntPtr.Zero) LocalFree(descriptor); }
    }
    public static PathFacts Inspect(string path, string sid) {
      using (SafeFileHandle file = CreateFileW(path, 0x20080, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero)) {
        if (file.IsInvalid) throw Error("Open staging object without following reparse points");
        return Read(file, path, sid);
      }
    }
    public static DirectoryLease OpenDirectory(string path, string sid) {
      // FILE_LIST_DIRECTORY participates in delete sharing; metadata-only access does not.
      SafeFileHandle file = CreateFileW(path, 0x20081, 3, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
      if (file.IsInvalid) { file.Dispose(); throw Error("Lock staging directory identity"); }
      try { PathFacts facts = Read(file, path, sid); if (!facts.Directory) throw new IOException("Expected staging directory."); return new DirectoryLease { Handle=file, Facts=facts }; }
      catch { file.Dispose(); throw; }
    }
  }
}
'@
            if ($PSVersionTable.PSVersion.Major -eq 5) {
                $parameters=[CodeDom.Compiler.CompilerParameters]::new()
                $parameters.GenerateInMemory=$true
                $parameters.TempFiles=[CodeDom.Compiler.TempFileCollection]::new($compiler.Path,$true)
                [void]$parameters.ReferencedAssemblies.Add('System.dll')
                Add-Type -TypeDefinition $nativeSource -CompilerParameters $parameters | Out-Null
            } else { Add-Type -TypeDefinition $nativeSource | Out-Null }
            $compiled=$null -ne ('SalahInstaller.StageNative' -as [type])
            if (-not $compiled) { throw 'Native staging compilation did not produce the required type.' }
            $compiler.Status='compiled'
        } finally {
            $restoreTemp=if ($null -eq $previousTemp) { [System.Management.Automation.Language.NullString]::Value } else { $previousTemp }
            $restoreTmp=if ($null -eq $previousTmp) { [System.Management.Automation.Language.NullString]::Value } else { $previousTmp }
            try { [Environment]::SetEnvironmentVariable('TEMP',$restoreTemp,'Process') }
            finally {
                try { [Environment]::SetEnvironmentVariable('TMP',$restoreTmp,'Process') }
                finally { Clear-StagingCompilerContext $compiler $compiled }
            }
        }
    }
}

function Get-StagingUserSid {
    if ($DryRun) { throw "Offline preview does not acquire staging identity." }
    return [SalahInstaller.StageNative]::CurrentSid()
}
function Open-StagingDirectoryLease([string]$Path) {
    if ($DryRun) { throw "Offline preview does not probe staging parents." }
    return [SalahInstaller.StageNative]::OpenDirectory($Path, $script:StagingAttempt.Sid)
}
function Get-StagingPathInfo([string]$Path) {
    if ($DryRun) { throw "Offline preview does not probe staging paths." }
    return [SalahInstaller.StageNative]::Inspect($Path, $script:StagingAttempt.Sid)
}
function New-PrivateStagingDirectory([string]$Path) {
    if ($DryRun) { throw "Offline preview does not create directories." }
    [SalahInstaller.StageNative]::CreatePrivateDirectory($Path, $script:StagingAttempt.Sid)
    return Get-StagingPathInfo $Path
}
function New-PrivateStagingFile([string]$Path) {
    if ($DryRun) { throw "Offline preview does not create files." }
    [SalahInstaller.StageNative]::CreatePrivateFile($Path, $script:StagingAttempt.Sid)
    return Get-StagingPathInfo $Path
}
function Get-TrustedStagingParent([string]$Path) {
    if ($DryRun) { throw "Offline preview does not inspect staging parents." }
    if (-not $Path -or $Path -notmatch '^[A-Za-z]:[\\/]' -or $Path -match '[\x00-\x1f]' -or $Path.Substring(2).Contains(':')) { throw 'Unsupported staging parent path.' }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar)
    [SalahInstaller.StageNative]::RequireLocalAclVolume($full)
    $root = [IO.Path]::GetPathRoot($full)
    $current = $root
    $paths = @($root)
    foreach ($part in $full.Substring($root.Length).Split([IO.Path]::DirectorySeparatorChar)) {
        if (-not $part -or $part -in @('.', '..') -or $part.Trim(' ') -cne $part -or $part.EndsWith('.')) { throw 'Ambiguous staging parent component.' }
        $current = Join-Path $current $part; $paths += $current
    }
    $last = $null
    foreach ($component in $paths) {
        $lease = Open-StagingDirectoryLease $component
        [void]$script:StagingAttempt.Leases.Add($lease)
        if (-not $lease.Facts.TrustedAncestor) { throw 'Staging ancestor permits foreign replacement or has an untrusted owner.' }
        $last = $lease.Facts
    }
    if (-not $last.TrustedParent) { throw 'Staging parent is not owned by this user with trusted write access.' }
    return $full
}

function Assert-OwnedStagingPath([string]$Path) {
    if ($DryRun) { throw "Offline preview has no owned artifact paths." }
    $attempt = $script:StagingAttempt
    if (-not $attempt -or $attempt.Status -ne 'active') { throw 'No active owned staging attempt.' }
    $full = [IO.Path]::GetFullPath($Path)
    $boundary = $null
    foreach ($root in @($attempt.Scratch, $attempt.Retained)) {
        if ($root -and ($full.Equals($root.Path, [StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($root.Path + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase))) { $boundary = $root; break }
    }
    if (-not $boundary) { throw 'Path is outside this staging attempt.' }
    $rootInfo = Get-StagingPathInfo $boundary.Path
    if (-not $rootInfo.Directory -or -not $rootInfo.Private -or $rootInfo.Identity -cne $boundary.Identity) { throw 'Staging root identity or access control changed.' }
    $current = $boundary.Path
    $info = $rootInfo
    $relative = $full.Substring($boundary.Path.Length).TrimStart([IO.Path]::DirectorySeparatorChar)
    if ($relative) {
        foreach ($component in $relative.Split([IO.Path]::DirectorySeparatorChar)) {
            if (-not $component -or $component -in @('.', '..') -or $component.Contains(':')) { throw 'Invalid owned path component.' }
            $current = Join-Path $current $component
            $info = Get-StagingPathInfo $current
            if (-not $info.Private -or (-not $info.Directory -and $info.Links -ne 1)) { throw 'Unowned, linked or non-private staging object refused.' }
        }
    }
    return $info
}

function New-OwnedStagingFile([string]$Parent, [string]$Name) {
    if ($DryRun) { throw "Offline preview does not reserve artifact candidates." }
    $parentInfo = Assert-OwnedStagingPath $Parent
    if (-not $parentInfo.Directory -or [IO.Path]::GetFileName($Name) -cne $Name -or $Name.Contains(':')) { throw 'Invalid artifact candidate destination.' }
    $path = Join-Path $Parent $Name
    $null = New-PrivateStagingFile $path
    $null = Assert-OwnedStagingPath $path
    return $path
}

function Get-StagedFileDigest([string]$Path) {
    if ($DryRun) { throw "Offline preview does not read admitted artifact bytes." }
    $before = Assert-OwnedStagingPath $Path
    if ($before.Directory) { throw 'Artifact is not a regular file.' }
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { $length=$stream.Length; $hash=([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose(); $stream.Dispose() }
    $after = Assert-OwnedStagingPath $Path
    if ($after.Identity -cne $before.Identity -or $after.Length -ne $length) { throw 'Artifact identity changed during readback.' }
    return [pscustomobject]@{Hash=$hash; Length=$length; Identity=$after.Identity}
}

function Get-OwnedStagingFiles([string]$Root) {
    if ($DryRun) { throw "Offline preview does not enumerate staging output." }
    $null = Assert-OwnedStagingPath $Root
    $pending = New-Object 'System.Collections.Generic.Queue[string]'
    $pending.Enqueue($Root)
    while ($pending.Count) {
        $directory = $pending.Dequeue()
        foreach ($path in [IO.Directory]::GetFileSystemEntries($directory)) {
            $info = Assert-OwnedStagingPath $path
            if ($info.Directory) { $pending.Enqueue($path) } else { Write-Output $path }
        }
    }
}

function Get-AdmittedArtifact([string]$Path, [string]$Kind) {
    if ($DryRun) { throw "Offline preview has no admitted artifacts." }
    if (-not $Path -or -not $script:StagingAttempt -or $script:StagingAttempt.Status -ne 'active') { throw 'No current admitted artifact.' }
    $matches = @($script:StagingAttempt.Artifacts | Where-Object { $_.Path -ceq $Path -and $_.Kind -ceq $Kind -and $_.Attempt -ceq $script:StagingAttempt.Id -and $_.State -in @('published','handed-off','retained') })
    if ($matches.Count -ne 1) { throw 'Artifact has no unique current admission record.' }
    $record = $matches[0]
    $info = Assert-OwnedStagingPath $Path
    if ($info.Identity -cne $record.Identity) { throw 'Admitted artifact identity changed.' }
    if ($Kind -eq 'unpacked') {
        $actualFiles = @(Get-OwnedStagingFiles $record.ExtractionRoot)
        if ($actualFiles.Count -ne $record.Files.Count) { throw 'Admitted unpacked output changed.' }
        foreach ($file in $record.Files) {
            $actual = Get-StagedFileDigest $file.Path
            if ($actual.Hash -cne $file.Hash -or $actual.Length -ne $file.Length -or $actual.Identity -cne $file.Identity) { throw 'Admitted unpacked bytes changed.' }
        }
    } else {
        $actual = Get-StagedFileDigest $Path
        if ($actual.Hash -cne $record.Hash -or $actual.Length -ne $record.Length) { throw 'Admitted artifact bytes changed.' }
    }
    return $record
}

function Initialize-Staging {
    if ($DryRun) { throw "Offline preview does not create staging directories." }
    if ($script:StagingAttempt) { throw 'A staging attempt already exists in this invocation.' }
    Initialize-StagingNative
    $script:StagingAttempt = [pscustomobject]@{
        Id=[guid]::NewGuid().ToString('N'); Sid=(Get-StagingUserSid); Status='initializing';
        Scratch=$null; Retained=$null; Artifacts=(New-Object 'System.Collections.Generic.List[object]');
        Leases=(New-Object 'System.Collections.Generic.List[object]')
    }
    try {
        $temporaryParent = Get-TrustedStagingParent $env:TEMP
        $retainedParent = Get-TrustedStagingParent $env:USERPROFILE
        $WorkRoot = Join-Path $temporaryParent ('SalahWidgetAttempt-' + $script:StagingAttempt.Id)
        $retainedPath = Join-Path $retainedParent ('SalahWidgetBundle-' + $script:StagingAttempt.Id)
        $scratch = New-PrivateStagingDirectory $WorkRoot
        $script:StagingAttempt.Scratch = $scratch
        $retained = New-PrivateStagingDirectory $retainedPath
        $script:StagingAttempt.Retained = $retained
        foreach ($root in @($scratch, $retained)) {
            if (-not $root.Directory -or -not $root.Private) { throw 'Exclusive root creation did not establish private custody.' }
            [void]$script:StagingAttempt.Leases.Add((Open-StagingDirectoryLease $root.Path))
        }
        $script:StagingAttempt.Status='active'
        $script:WorkRoot=$WorkRoot
        $script:DownloadRoot=Join-Path $retainedPath 'downloads'
        $script:PresetRoot=Join-Path $retainedPath 'presets'
        $null=New-PrivateStagingDirectory $script:DownloadRoot
        $null=New-PrivateStagingDirectory $script:PresetRoot
    } catch {
        if ($script:StagingAttempt) { $script:StagingAttempt.Status='initialization-failed'; foreach ($lease in $script:StagingAttempt.Leases) { $lease.Dispose() } }
        throw
    }
}

function Clear-OwnedScratch {
    if ($DryRun) { return }
    $attempt = $script:StagingAttempt
    if (-not $attempt -or $attempt.Status -eq 'closed') { return }
    try {
        if ($attempt.Status -ne 'active' -or -not $attempt.Scratch) { throw 'No complete scratch custody; partial paths retained.' }
        $null = Assert-OwnedStagingPath $attempt.Scratch.Path
        $null = @(Get-OwnedStagingFiles $attempt.Scratch.Path)
        # Release the scratch directory's own delete-denying handle only.
        # Keep every ancestor and retained-root lease until deletion completes.
        foreach ($lease in $attempt.Leases) {
            if ($lease.Facts.Path.Equals($attempt.Scratch.Path,[StringComparison]::OrdinalIgnoreCase)) { $lease.Dispose() }
        }
        [IO.Directory]::Delete($attempt.Scratch.Path, $true)
    } catch { Write-Warn ('Scratch cleanup skipped; partial material retained: ' + $_.Exception.Message) }
    finally {
        foreach ($lease in $attempt.Leases) { $lease.Dispose() }
        foreach ($record in $attempt.Artifacts) {
            if ($record.State -in @('published','handed-off')) { $record.State='retained' }
            elseif ($record.State -notmatch 'failed|retained') { $record.State='cancelled/partial-retained' }
        }
        $attempt.Status='closed'
    }
}

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Write-Ok([string]$Text) { Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-Warn([string]$Text) { Write-Host "[WARN] $Text" -ForegroundColor Yellow }
function Write-Err([string]$Text) { Write-Host "[ERROR] $Text" -ForegroundColor Red }

function First-ExistingPath([string[]]$Paths) {
    foreach ($p in $Paths) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    return $null
}

function Open-TargetUrl($Target, [string]$Url) {
    if ($NoOpen) {
        Write-Host "Open manually: $Url"
        return
    }
    if ($DryRun) {
        Write-Host "[dry-run] Would open: $Url"
        return
    }
    try {
        if ($Target -and $Target.ExePath -and (Test-Path -LiteralPath $Target.ExePath)) {
            Start-Process -FilePath $Target.ExePath -ArgumentList $Url | Out-Null
        } else {
            Start-Process $Url | Out-Null
        }
    } catch {
        Write-Warn "Could not open automatically. Open manually: $Url"
    }
}

function Copy-Text([string]$Text) {
    if ($DryRun) { Write-Host "[dry-run] Clipboard copy suppressed."; return $false }
    try {
        Set-Clipboard -Value $Text
        return $true
    } catch {
        return $false
    }
}

function Sanitize-FilePart([string]$Name) {
    return ($Name -replace '[^\w.\-]+', '_')
}

function Get-BrowserConfigs {
    $local = $env:LOCALAPPDATA
    $roam = $env:APPDATA

    @(
        [pscustomobject]@{
            Key="chrome"; Label="Google Chrome"; Family="chromium";
            UserData=Join-Path $local "Google\Chrome\User Data";
            Exes=@(
                "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "$local\Google\Chrome\Application\chrome.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="chrome://extensions/"; NewTabUrl="chrome://newtab/"
        },
        [pscustomobject]@{
            Key="edge"; Label="Microsoft Edge"; Family="chromium";
            UserData=Join-Path $local "Microsoft\Edge\User Data";
            Exes=@(
                "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
                "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
                "$local\Microsoft\Edge\Application\msedge.exe"
            );
            NewIds=@($EdgeTablissNgId, $ChromeTablissNgId);
            OldIds=@($EdgeLegacyTablissId, $ChromeLegacyTablissId);
            StoreUrl=$EdgeStoreUrl; ManagerUrl="edge://extensions/"; NewTabUrl="edge://newtab/"
        },
        [pscustomobject]@{
            Key="brave"; Label="Brave"; Family="chromium";
            UserData=Join-Path $local "BraveSoftware\Brave-Browser\User Data";
            Exes=@(
                "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
                "${env:ProgramFiles(x86)}\BraveSoftware\Brave-Browser\Application\brave.exe",
                "$local\BraveSoftware\Brave-Browser\Application\brave.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="brave://extensions/"; NewTabUrl="brave://newtab/"
        },
        [pscustomobject]@{
            Key="chromium"; Label="Chromium"; Family="chromium";
            UserData=Join-Path $local "Chromium\User Data";
            Exes=@(
                "$env:ProgramFiles\Chromium\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Chromium\Application\chrome.exe",
                "$local\Chromium\Application\chrome.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="chrome://extensions/"; NewTabUrl="chrome://newtab/"
        },
        [pscustomobject]@{
            Key="firefox"; Label="Firefox"; Family="firefox";
            UserData=Join-Path $roam "Mozilla\Firefox\Profiles";
            Exes=@(
                "$env:ProgramFiles\Mozilla Firefox\firefox.exe",
                "${env:ProgramFiles(x86)}\Mozilla Firefox\firefox.exe",
                "$local\Mozilla Firefox\firefox.exe"
            );
            NewIds=@(); OldIds=@();
            StoreUrl=$FirefoxStoreUrl; ManagerUrl="about:addons"; NewTabUrl="about:newtab"
        },
        [pscustomobject]@{
            Key="librewolf"; Label="LibreWolf"; Family="firefox";
            UserData=Join-Path $roam "LibreWolf\Profiles";
            Exes=@(
                "$env:ProgramFiles\LibreWolf\librewolf.exe",
                "${env:ProgramFiles(x86)}\LibreWolf\librewolf.exe",
                "$local\LibreWolf\librewolf.exe"
            );
            NewIds=@(); OldIds=@();
            StoreUrl=$FirefoxStoreUrl; ManagerUrl="about:addons"; NewTabUrl="about:newtab"
        }
    )
}

function Get-ChromiumProfiles($Config) {
    if (-not (Test-Path -LiteralPath $Config.UserData)) { return @() }
    $dirs = Get-ChildItem -LiteralPath $Config.UserData -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq "Default" -or
            $_.Name -match "^Profile \d+$" -or
            (Test-Path -LiteralPath (Join-Path $_.FullName "Preferences"))
        }
    return @($dirs)
}

function Get-FirefoxProfiles($Config) {
    if (-not (Test-Path -LiteralPath $Config.UserData)) { return @() }
    return @(Get-ChildItem -LiteralPath $Config.UserData -Directory -ErrorAction SilentlyContinue)
}

function Get-ChromiumExtensionStatus($ProfilePath, [string[]]$NewIds, [string[]]$OldIds) {
    $newFound = New-Object System.Collections.Generic.List[string]
    $oldFound = New-Object System.Collections.Generic.List[string]

    $extDir = Join-Path $ProfilePath "Extensions"
    foreach ($id in $NewIds) {
        if ($id -and (Test-Path -LiteralPath (Join-Path $extDir $id))) { [void]$newFound.Add($id) }
    }
    foreach ($id in $OldIds) {
        if ($id -and (Test-Path -LiteralPath (Join-Path $extDir $id))) { [void]$oldFound.Add($id) }
    }

    $prefsPath = Join-Path $ProfilePath "Preferences"
    if (Test-Path -LiteralPath $prefsPath) {
        try {
            $prefs = Get-Content -Raw -LiteralPath $prefsPath | ConvertFrom-Json
            if ($prefs.extensions -and $prefs.extensions.settings) {
                $settingIds = @($prefs.extensions.settings.PSObject.Properties.Name)
                foreach ($id in $NewIds) {
                    if ($settingIds -contains $id) { [void]$newFound.Add($id) }
                }
                foreach ($id in $OldIds) {
                    if ($settingIds -contains $id) { [void]$oldFound.Add($id) }
                }
            }
        } catch {
            # Preferences can be locked or malformed while a browser is running. Directory detection still works.
        }
    }

    $hasNewResult = (($newFound | Select-Object -Unique).Count -gt 0)
    $hasOldResult = (($oldFound | Select-Object -Unique).Count -gt 0)
    [pscustomobject]@{
        HasNew = $hasNewResult
        HasOld = $hasOldResult
        NewMatches = @($newFound | Select-Object -Unique)
        OldMatches = @($oldFound | Select-Object -Unique)
        Status = $(if ($hasNewResult -and $hasOldResult) { 'known-both' } elseif ($hasOldResult) { 'known-legacy' } elseif ($hasNewResult) { 'known-new' } else { 'known-neither' })
        Reason = 'existing-chromium-detector'
        EvidenceClass = 'chromium-directory-and-preferences'
        MetadataSource = $ProfilePath
    }
}

# Validate strict JSON grammar and unambiguous object keys before the host's
# permissive ConvertFrom-Json conversion. This helper has no external effects.
function Test-StrictJson([string]$Json) {
    $lexer = [regex]'\G(?:(?<space>[ \t\r\n]+)|(?<string>"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*")|(?<number>-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|(?<literal>true|false|null)|(?<mark>[{}\[\],:]))'
    $frames = New-Object 'System.Collections.Generic.List[object]'
    $position=0; $rootComplete=$false
    try {
        while ($position -lt $Json.Length) {
            $tokenMatch=$lexer.Match($Json,$position)
            if (-not $tokenMatch.Success -or $tokenMatch.Index -ne $position) { return $false }
            $position += $tokenMatch.Length
            if ($tokenMatch.Groups['space'].Success) { continue }
            $token=$tokenMatch.Value
            $frame=if ($frames.Count) { $frames[$frames.Count-1] } else { $null }

            if ($null -ne $frame -and $frame.Kind -eq 'object' -and ($frame.State -eq 'key-or-end' -or $frame.State -eq 'key')) {
                if ($token -eq '}' -and $frame.State -eq 'key-or-end') { $frames.RemoveAt($frames.Count-1); continue }
                if (-not $tokenMatch.Groups['string'].Success) { return $false }
                # Decode strict JSON string escapes so name and na\u006de are
                # the same property. Compare case-insensitively because the
                # downstream PowerShell object's property lookup does so too.
                $keyText=New-Object System.Text.StringBuilder
                for ($i=1; $i -lt $token.Length-1; $i++) {
                    if ($token[$i] -ne [char]92) { [void]$keyText.Append($token[$i]); continue }
                    $i++
                    switch ($token[$i]) {
                        '"' { [void]$keyText.Append([char]34) }
                        '\' { [void]$keyText.Append([char]92) }
                        '/' { [void]$keyText.Append([char]47) }
                        'b' { [void]$keyText.Append([char]8) }
                        'f' { [void]$keyText.Append([char]12) }
                        'n' { [void]$keyText.Append([char]10) }
                        'r' { [void]$keyText.Append([char]13) }
                        't' { [void]$keyText.Append([char]9) }
                        'u' { [void]$keyText.Append([char][Convert]::ToInt32($token.Substring($i+1,4),16)); $i+=4 }
                    }
                }
                if (-not $frame.Keys.Add($keyText.ToString())) { return $false }
                $frame.State='colon'; continue
            }
            if ($null -ne $frame -and $frame.State -eq 'colon') {
                if ($token -ne ':') { return $false }
                $frame.State='value'; continue
            }
            if ($null -ne $frame -and $frame.State -eq 'after-value') {
                $closing=if ($frame.Kind -eq 'object') { '}' } else { ']' }
                if ($token -eq $closing) { $frames.RemoveAt($frames.Count-1); continue }
                if ($token -ne ',') { return $false }
                $frame.State=if ($frame.Kind -eq 'object') { 'key' } else { 'value' }
                continue
            }
            if ($null -ne $frame -and $frame.Kind -eq 'array' -and $frame.State -eq 'value-or-end' -and $token -eq ']') {
                $frames.RemoveAt($frames.Count-1); continue
            }

            # A value consumes exactly one parent slot; nested containers must
            # close before that parent accepts its next separator or member.
            if ($null -ne $frame) { $frame.State='after-value' }
            elseif ($rootComplete) { return $false }
            else { $rootComplete=$true }
            if ($token -eq '{') {
                $keys=New-Object 'System.Collections.Generic.HashSet[string]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
                [void]$frames.Add([pscustomobject]@{Kind='object';State='key-or-end';Keys=$keys})
            } elseif ($token -eq '[') {
                [void]$frames.Add([pscustomobject]@{Kind='array';State='value-or-end'})
            } elseif (-not ($tokenMatch.Groups['string'].Success -or $tokenMatch.Groups['number'].Success -or $tokenMatch.Groups['literal'].Success)) {
                return $false
            }
        }
        return ($rootComplete -and $frames.Count -eq 0)
    } catch { return $false }
}

function Get-FirefoxExtensionStatus($ProfilePath) {
    $extensionsJson = Join-Path $ProfilePath "extensions.json"
    $result = [pscustomobject]@{
        HasNew=$false; HasOld=$false; NewMatches=@(); OldMatches=@()
        Status='unknown'; Reason='metadata-absent'; EvidenceClass='firefox-extensions-json'; MetadataSource=$extensionsJson
    }
    $newMatches = New-Object System.Collections.Generic.List[string]
    $oldMatches = New-Object System.Collections.Generic.List[string]
    try {
        if (-not (Test-Path -LiteralPath $extensionsJson)) { return $result }
        $decoder = New-Object System.Text.UTF8Encoding -ArgumentList $false,$true
        $raw = [IO.File]::ReadAllText($extensionsJson, $decoder)
    } catch [System.Text.DecoderFallbackException] {
        $result.Reason='metadata-encoding'
        Write-Warn "Firefox discovery held: invalid metadata encoding."
        return $result
    } catch {
        $result.Reason='metadata-unreadable'
        Write-Warn "Firefox discovery held: metadata could not be read."
        return $result
    }
    try {
        if (-not (Test-StrictJson $raw)) { throw 'Invalid or ambiguous JSON metadata.' }
        $data = ConvertFrom-Json -InputObject $raw
    }
    catch {
        $result.Reason='metadata-malformed'
        Write-Warn "Firefox discovery held: malformed metadata."
        return $result
    }
    # ConvertFrom-Json can unwrap a singleton root array into one object.
    if ($raw -notmatch '^\s*\{' -or -not ($data -is [pscustomobject]) -or $null -eq $data.PSObject.Properties['addons'] -or $data.PSObject.Properties['addons'].Name -cne 'addons' -or -not ($data.addons -is [array])) {
        $result.Reason='metadata-unsupported'
        return $result
    }
    $supported=$true
    foreach ($addon in $data.addons) {
        if (-not ($addon -is [pscustomobject])) { $supported=$false; break }
        # PowerShell member lookup ignores case; Firefox JSON field names do not.
        foreach ($key in 'id','name','defaultLocale') {
            $property=$addon.PSObject.Properties[$key]
            if ($null -ne $property -and $property.Name -cne $key) { $supported=$false }
        }
        foreach ($key in 'id','name') {
            if ($null -ne $addon.$key -and -not ($addon.$key -is [string])) { $supported=$false }
        }
        $locale=$addon.defaultLocale
        if ($null -ne $locale -and (-not ($locale -is [pscustomobject]) -or ($null -ne $locale.name -and -not ($locale.name -is [string])))) { $supported=$false }
        if ($locale -is [pscustomobject]) {
            $localeName=$locale.PSObject.Properties['name']
            if ($null -ne $localeName -and $localeName.Name -cne 'name') { $supported=$false }
        }
        if (-not $supported) { break }
        $parts = @()
        if ($addon.id) { $parts += $addon.id }
        if ($addon.name) { $parts += $addon.name }
        if ($locale -and $locale.name) { $parts += $locale.name }
        $hay = ($parts -join " ")
        if ([string]::IsNullOrWhiteSpace($hay)) { $supported=$false; break }
        if ($hay -match "(?i)\bTablissNG\b|tablissng") {
            $result.HasNew=$true; [void]$newMatches.Add($hay)
        } elseif ($hay -match "(?i)\bTabliss\b" -and $hay -notmatch "(?i)NG|tablissng") {
            $result.HasOld=$true; [void]$oldMatches.Add($hay)
        }
    }
    $result.NewMatches=@($newMatches | Select-Object -Unique)
    $result.OldMatches=@($oldMatches | Select-Object -Unique)
    if ($supported) {
        $result.Status = if ($result.HasNew -and $result.HasOld) { 'known-both' } elseif ($result.HasOld) { 'known-legacy' } elseif ($result.HasNew) { 'known-new' } else { 'known-neither' }
        $result.Reason='supported-metadata'
    } else {
        $result.Reason='metadata-unsupported'
    }
    return $result
}

# One derived guard serves preview, pre-staging selection and actual dispatch.
function Get-DiscoveryEligibility($Target) {
    if ($Target.HasLegacyTabliss) { return 'legacy-refused' }
    switch ($Target.DiscoveryStatus) {
        'known-new' { return 'eligible-known' }
        'known-neither' { return 'eligible-known' }
        'known-legacy' { return 'legacy-refused' }
        'known-both' { return 'legacy-refused' }
        default { return 'unknown-held' }
    }
}

function Get-Targets {
    $targets = New-Object System.Collections.Generic.List[object]
    foreach ($cfg in Get-BrowserConfigs) {
        $exe = First-ExistingPath $cfg.Exes
        $profiles = if ($cfg.Family -eq "chromium") { Get-ChromiumProfiles $cfg } else { Get-FirefoxProfiles $cfg }
        $browserInstalled = [bool]($exe -or (Test-Path -LiteralPath $cfg.UserData))

        if ($profiles.Count -eq 0) {
            if ($browserInstalled) {
                [void]$targets.Add([pscustomobject]@{
                    Index=$targets.Count + 1; Config=$cfg; Browser=$cfg.Label; Family=$cfg.Family;
                    ProfileName="(no profile detected)"; ProfilePath=$null; ExePath=$exe;
                    HasTablissNG=$false; HasLegacyTabliss=$false; NewMatches=@(); OldMatches=@()
                    DiscoveryStatus='unknown'; DiscoveryReason='no-profile'; DiscoveryEvidence='browser-profile-discovery'; DiscoverySource=$cfg.UserData
                })
            }
            continue
        }

        foreach ($p in $profiles) {
            $status = if ($cfg.Family -eq "chromium") {
                Get-ChromiumExtensionStatus $p.FullName $cfg.NewIds $cfg.OldIds
            } else {
                Get-FirefoxExtensionStatus $p.FullName
            }
            [void]$targets.Add([pscustomobject]@{
                Index=$targets.Count + 1; Config=$cfg; Browser=$cfg.Label; Family=$cfg.Family;
                ProfileName=$p.Name; ProfilePath=$p.FullName; ExePath=$exe;
                HasTablissNG=$status.HasNew; HasLegacyTabliss=$status.HasOld;
                NewMatches=$status.NewMatches; OldMatches=$status.OldMatches
                DiscoveryStatus=$status.Status; DiscoveryReason=$status.Reason;
                DiscoveryEvidence=$status.EvidenceClass; DiscoverySource=$status.MetadataSource
            })
        }
    }
    return $targets.ToArray()
}

$script:LatestRelease = $null
function Get-LatestRelease {
    if ($DryRun) { throw "Offline preview cannot resolve remote GitHub releases or use cached metadata." }
    if ($script:LatestRelease) { return $script:LatestRelease }
    $uri = "https://api.github.com/repos/$TablissNgRepo/releases/latest"
    Write-Host "Resolving latest TablissNG release from $uri"
    $headers = @{
        "Accept" = "application/vnd.github+json"
        "User-Agent" = "salah-widget-installer"
    }
    $script:LatestRelease = Invoke-RestMethod -Uri $uri -Headers $headers
    return $script:LatestRelease
}

function Select-TablissNgAsset([string]$Family) {
    if ($DryRun) { throw "Offline preview leaves release assets unresolved." }
    $release = Get-LatestRelease
    $assets = @($release.assets)
    if ($assets.Count -eq 0) { throw "Latest release '$($release.tag_name)' has no assets." }

    if ($Family -eq "firefox") {
        $preferred = @(
            $assets | Where-Object { $_.name -match "(?i)\.xpi$" -and $_.name -match "(?i)signed|firefox" -and $_.name -notmatch "(?i)unsigned|source" }
            $assets | Where-Object { $_.name -match "(?i)\.xpi$" -and $_.name -notmatch "(?i)unsigned|source" }
            $assets | Where-Object { $_.name -match "(?i)firefox.*\.zip$" -and $_.name -notmatch "(?i)unsigned|source" }
        ) | ForEach-Object { $_ }
    } elseif ($Family -eq "chromium") {
        $preferred = @(
            $assets | Where-Object { $_.name -match "(?i)chrom(e|ium).*\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" }
            $assets | Where-Object { $_.name -match "(?i)tabliss.*\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" }
        ) | ForEach-Object { $_ }
    } else {
        throw "Unsupported browser family for GitHub release install: $Family"
    }

    $asset = @($preferred | Where-Object { $_ } | Select-Object -First 1)
    if (-not $asset) {
        throw "No safe $Family asset found in latest release '$($release.tag_name)'."
    }
    return $asset
}

function New-ArtifactRecord([string]$Kind, [string]$Source) {
    if ($DryRun) { throw "Offline preview does not begin artifact transactions." }
    if (-not $script:StagingAttempt -or $script:StagingAttempt.Status -ne 'active') { throw 'No active staging attempt.' }
    $record=[pscustomobject]@{
        Attempt=$script:StagingAttempt.Id; Kind=$Kind; Source=$Source; State='unresolved';
        Candidate=$null; CandidateIdentity=$null; PublicationCandidate=$null; Path=$null;
        ExpectedLength=$null; ExpectedDigest=$null; Identity=$null; Hash=$null; Length=0;
        Validation=$null; Failure=$null; ExtractionRoot=$null; Files=@()
    }
    [void]$script:StagingAttempt.Artifacts.Add($record)
    return $record
}

function Publish-OwnedFile($Record, [string]$Parent, [string]$Name) {
    if ($DryRun) { throw "Offline preview does not publish artifact paths." }
    if ($Record.State -ne 'validated' -or $Record.Attempt -cne $script:StagingAttempt.Id) { throw 'Candidate is not validated in this attempt.' }
    $before=Get-StagedFileDigest $Record.Candidate
    if ($before.Identity -cne $Record.CandidateIdentity -or $before.Hash -cne $Record.Hash -or $before.Length -ne $Record.Length) { throw 'Validated candidate changed before publication.' }
    $token=[guid]::NewGuid().ToString('N')
    $partial=New-OwnedStagingFile $Parent ($token+'.partial')
    $Record.PublicationCandidate=$partial
    $source=$null; $destination=$null
    try {
        $source=[IO.File]::Open($Record.Candidate,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $destination=[IO.File]::Open($partial,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
        $source.CopyTo($destination)
    } finally { if ($destination) { $destination.Dispose() }; if ($source) { $source.Dispose() } }
    $copied=Get-StagedFileDigest $partial
    if ($copied.Hash -cne $Record.Hash -or $copied.Length -ne $Record.Length) { throw 'Publication copy differs from validated bytes.' }
    $ready=Join-Path $Parent ($token+'-'+$Name)
    [IO.File]::Move($partial,$ready)
    $published=Get-StagedFileDigest $ready
    if ($published.Identity -cne $copied.Identity -or $published.Hash -cne $Record.Hash -or $published.Length -ne $Record.Length) { throw 'Published artifact readback differs.' }
    $Record.Path=$ready; $Record.Identity=$published.Identity; $Record.State='published'
    $null=Get-AdmittedArtifact $ready $Record.Kind
    return $ready
}

function ConvertFrom-SupportedJson([string]$Raw) {
    if (-not (Test-StrictJson $Raw)) { throw 'JSON is malformed or contains ambiguous object keys.' }
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { return ConvertFrom-Json -InputObject $Raw -DateKind String }
    return ConvertFrom-Json -InputObject $Raw
}

function ConvertFrom-Utf8Bytes([byte[]]$Bytes) {
    $decoder=New-Object Text.UTF8Encoding -ArgumentList $false,$true
    $raw=$decoder.GetString($Bytes)
    if ($raw.Length -and $raw[0] -eq [char]0xfeff) { $raw=$raw.Substring(1) }
    return $raw
}

function Assert-ExtensionManifest([string]$Raw) {
    $data=ConvertFrom-SupportedJson $Raw
    if ($Raw -notmatch '^\s*\{' -or -not ($data -is [pscustomobject])) { throw 'Unsupported extension manifest shape.' }
    $required=@{}
    foreach ($name in @('manifest_version','name','version')) {
        $property=@($data.PSObject.Properties | Where-Object {$_.Name -ceq $name})
        if ($property.Count -ne 1) { throw 'Required extension manifest key is missing or has the wrong case.' }
        $required[$name]=$property[0].Value
    }
    if (-not ($required.manifest_version -is [int] -or $required.manifest_version -is [long]) -or $required.manifest_version -notin @(2,3) -or -not ($required.name -is [string]) -or [string]::IsNullOrWhiteSpace($required.name) -or -not ($required.version -is [string]) -or [string]::IsNullOrWhiteSpace($required.version)) { throw 'Unsupported extension manifest shape.' }
}

function Test-ExtensionArchive([string]$Path, [string]$ExtractRoot) {
    if ($DryRun) { throw "Offline preview does not inspect or extract archives." }
    $info=Assert-OwnedStagingPath $Path
    if ($info.Directory) { throw 'Archive candidate is not a regular file.' }
    $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $archive=$null
    try {
        $crcs=[SalahInstaller.StageNative]::ReadZipCrcs($stream)
        $archive=New-Object IO.Compression.ZipArchive($stream,[IO.Compression.ZipArchiveMode]::Read,$true)
        if ($archive.Entries.Count -ne $crcs.Length) { throw 'ZIP entry count differs from the validated directory.' }
        $members=New-Object 'System.Collections.Generic.List[object]'
        $seen=New-Object 'System.Collections.Generic.HashSet[string]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
        $nodes=New-Object 'System.Collections.Generic.Dictionary[string,object]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
        $expanded=0L; $manifest=$null
        for ($entryIndex=0; $entryIndex -lt $archive.Entries.Count; $entryIndex++) {
            $entry=$archive.Entries[$entryIndex]
            $name=[string]$entry.FullName
            $directory=$name.EndsWith('/')
            $relative=if ($directory) { $name.Substring(0,$name.Length-1) } else { $name }
            if (-not $relative -or $relative.StartsWith('/') -or $relative.Contains('\') -or $relative -match '[\x00-\x1f<>:"|?*]') { throw 'Unsafe archive member path.' }
            $parts=$relative.Split('/')
            $prefix=''
            for ($partIndex=0; $partIndex -lt $parts.Length; $partIndex++) {
                $part=$parts[$partIndex]
                if (-not $part -or $part -in @('.', '..') -or $part.Trim(' ') -cne $part -or $part.EndsWith('.') -or $part -match '^(?i:CON|PRN|AUX|NUL|COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3])(?:\..*)?$') { throw 'Unsupported Windows archive name or alias.' }
                $prefix=if ($prefix) { $prefix+'/'+$part } else { $part }
                $isDirectory=($partIndex -lt $parts.Length-1 -or $directory)
                if ($nodes.ContainsKey($prefix)) {
                    $node=$nodes[$prefix]
                    if ($node.Name -cne $prefix -or -not $node.Directory -or -not $isDirectory) { throw 'Archive member collision or file/directory alias.' }
                } else { $nodes.Add($prefix,[pscustomobject]@{Name=$prefix;Directory=$isDirectory}) }
            }
            if (-not $seen.Add($relative)) { throw 'Duplicate archive destination.' }
            $attributes=[BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$entry.ExternalAttributes),0)
            $unixType=($attributes -shr 16) -band 61440
            if (($attributes -band 1024) -ne 0 -or $unixType -notin @(0,16384,32768) -or ($unixType -eq 16384 -and -not $directory) -or ($unixType -eq 32768 -and $directory) -or (($attributes -band 16) -ne 0 -and -not $directory)) { throw 'Archive link, reparse or special-file attributes refused.' }
            if ($entry.Length -gt 134217728 -or ($directory -and $entry.Length -ne 0)) { throw 'Unsupported archive member size.' }
            $expanded += $entry.Length
            if ($expanded -gt 536870912) { throw 'Archive expanded size exceeds the supported limit.' }
            $member=[pscustomobject]@{Entry=$entry;Relative=$relative;Directory=$directory;Crc=$crcs[$entryIndex];Hash=$null;Length=$entry.Length}
            [void]$members.Add($member)
            if (-not $directory -and $parts[$parts.Length-1] -ceq 'manifest.json') {
                if ($manifest) { throw 'Archive contains ambiguous extension manifests.' }
                $manifest=$member
            }
        }
        if (-not $manifest -or $manifest.Length -gt 1048576) { throw 'Archive has no supported extension manifest.' }
        # Validate every member, including CRC/size, before the first extraction
        # file or directory is created. A late invalid entry cannot write early.
        foreach ($member in $members) {
            $input=$member.Entry.Open()
            try { $proof=[SalahInstaller.StageNative]::Fingerprint($input,$member.Length,$null) } finally { $input.Dispose() }
            if ($proof.Length -ne $member.Length -or $proof.Crc -ne $member.Crc) { throw 'Archive member CRC or declared length differs.' }
            $member.Hash=$proof.Hash
        }
        $manifestStream=$manifest.Entry.Open(); $manifestBytes=New-Object IO.MemoryStream
        try { $manifestStream.CopyTo($manifestBytes); $null=Assert-ExtensionManifest (ConvertFrom-Utf8Bytes $manifestBytes.ToArray()) }
        finally { $manifestStream.Dispose(); $manifestBytes.Dispose() }
        if ($ExtractRoot) {
            $rootInfo=Assert-OwnedStagingPath $ExtractRoot
            if (-not $rootInfo.Directory -or [IO.Directory]::GetFileSystemEntries($ExtractRoot).Length) { throw 'Extraction candidate is not a fresh empty owned directory.' }
            foreach ($member in $members) {
                $parts=$member.Relative.Split('/')
                $parent=$ExtractRoot
                $directoryCount=if ($member.Directory) { $parts.Length } else { $parts.Length-1 }
                for ($i=0; $i -lt $directoryCount; $i++) {
                    $next=Join-Path $parent $parts[$i]
                    if (-not [IO.Directory]::Exists($next)) { $null=Assert-OwnedStagingPath $parent; $null=New-PrivateStagingDirectory $next }
                    $nextInfo=Assert-OwnedStagingPath $next
                    if (-not $nextInfo.Directory) { throw 'Extraction directory changed type.' }
                    $parent=$next
                }
                if (-not $member.Directory) {
                    $output=New-OwnedStagingFile $parent $parts[$parts.Length-1]
                    $input=$member.Entry.Open(); $destination=$null
                    try {
                        $destination=[IO.File]::Open($output,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
                        $written=[SalahInstaller.StageNative]::Fingerprint($input,$member.Length,$destination)
                    } finally { if ($destination) {$destination.Dispose()}; $input.Dispose() }
                    if ($written.Hash -cne $member.Hash -or $written.Crc -ne $member.Crc -or $written.Length -ne $member.Length) { throw 'Extraction bytes differ from preflight.' }
                    $readback=Get-StagedFileDigest $output
                    if ($readback.Hash -cne $member.Hash) { throw 'Extracted output readback differs.' }
                }
            }
        }
        return [pscustomobject]@{Manifest=$manifest.Relative; Members=$members.Count; ExpandedBytes=$expanded; Checks='single-disk ZIP structure; Windows-safe names; regular members; CRC/length; strict manifest JSON'}
    } finally { if ($archive) { $archive.Dispose() }; $stream.Dispose() }
}

function Download-Asset($Asset) {
    if ($DryRun) { throw "Offline preview does not download or return cached asset paths." }
    $release=Get-LatestRelease
    if (-not ($Asset.name -is [string]) -or $Asset.name -notmatch '(?i)\.(zip|xpi)$' -or -not ($Asset.browser_download_url -is [string]) -or $Asset.browser_download_url -notmatch '^https://') { throw 'Unsupported asset source metadata.' }
    $expectedLength=$null
    if ($null -ne $Asset.size) {
        if ($Asset.size -is [bool] -or [string]$Asset.size -notmatch '^\d+$' -or [decimal]$Asset.size -le 0 -or [decimal]$Asset.size -gt 134217728) { throw 'Unsupported expected asset size.' }
        $expectedLength=[long]$Asset.size
    }
    $expectedDigest=$null
    if ($Asset.digest) {
        if ([string]$Asset.digest -notmatch '^sha256:[0-9a-fA-F]{64}$') { throw 'Unsupported asset digest metadata.' }
        $expectedDigest=([string]$Asset.digest).Substring(7).ToLowerInvariant()
    }
    $source=ConvertTo-Json -Compress -Depth 4 -InputObject @($release.id,$release.tag_name,$Asset.id,$Asset.name,$Asset.browser_download_url,$expectedLength,$expectedDigest)
    foreach ($previous in @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'asset' -and $_.Source -ceq $source -and $_.State -in @('published','handed-off')})) {
        try { $null=Get-AdmittedArtifact $previous.Path 'asset'; Write-Ok 'Reusing the same admitted asset bytes in this attempt.'; return $previous.Path }
        catch { $previous.State='validation-failed'; $previous.Failure='Admitted asset readback changed; reacquisition required.' }
    }
    $record=New-ArtifactRecord 'asset' $source
    $record.ExpectedLength=$expectedLength; $record.ExpectedDigest=$expectedDigest
    $record.Candidate=New-OwnedStagingFile $WorkRoot ('download-'+[guid]::NewGuid().ToString('N')+'.partial')
    $record.CandidateIdentity=(Assert-OwnedStagingPath $record.Candidate).Identity
    $record.State='downloading'
    try { Invoke-WebRequest -UseBasicParsing -Uri $Asset.browser_download_url -OutFile $record.Candidate | Out-Null }
    catch { $record.State='download-failed'; $record.Failure='Acquisition did not complete; candidate is not ready.'; throw $record.Failure }
    $record.State='downloaded-unvalidated'
    try {
        $proof=Get-StagedFileDigest $record.Candidate
        if ($proof.Identity -cne $record.CandidateIdentity -or ($null -ne $expectedLength -and $proof.Length -ne $expectedLength) -or ($expectedDigest -and $proof.Hash -cne $expectedDigest)) { throw 'Candidate identity, expected size or declared digest differs.' }
        $validation=Test-ExtensionArchive $record.Candidate
        $record.Hash=$proof.Hash; $record.Length=$proof.Length; $record.Validation=$validation.Checks; $record.State='validated'
    } catch { $record.State='validation-failed'; $record.Failure=$_.Exception.Message; throw }
    try { return Publish-OwnedFile $record $DownloadRoot (Sanitize-FilePart $Asset.name) }
    catch { $record.State='publication-failed'; $record.Failure=$_.Exception.Message; throw }
}

function Expand-ChromiumAsset([string]$ZipPath) {
    if ($DryRun) { throw "Offline preview does not extract assets." }
    $archiveRecord=Get-AdmittedArtifact $ZipPath 'asset'
    $record=New-ArtifactRecord 'unpacked' ($archiveRecord.Source+'|'+$archiveRecord.Hash)
    $record.State='downloaded-unvalidated'
    $root=Join-Path $script:StagingAttempt.Retained.Path ('unpacked-'+[guid]::NewGuid().ToString('N'))
    try {
        $null=Assert-OwnedStagingPath $script:StagingAttempt.Retained.Path
        $null=New-PrivateStagingDirectory $root
        $record.Candidate=$root; $record.ExtractionRoot=$root
        $validation=Test-ExtensionArchive $ZipPath $root
        $manifestPath=Join-Path $root ($validation.Manifest.Replace('/',[IO.Path]::DirectorySeparatorChar))
        $path=[IO.Path]::GetDirectoryName($manifestPath)
        $files=@()
        foreach ($file in @(Get-OwnedStagingFiles $root)) {
            $proof=Get-StagedFileDigest $file
            $files += [pscustomobject]@{Path=$file;Identity=$proof.Identity;Hash=$proof.Hash;Length=$proof.Length}
        }
        $record.Files=$files; $record.Validation=$validation.Checks; $record.State='validated'
        $record.Path=$path; $record.Identity=(Assert-OwnedStagingPath $path).Identity; $record.State='published'
        $null=Get-AdmittedArtifact $path 'unpacked'
        return $path
    } catch { $record.State='extraction-failed'; $record.Failure=$_.Exception.Message; throw }
}

# Locate only the canonical string token after strict grammar validation. The
# surrounding JSON is retained byte-for-byte; unrelated dates/numbers never
# pass through a whole-document serializer.
function Get-PresetInputToken([string]$Raw) {
    $tokens=[regex]::Matches($Raw,'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"|[{}\[\]]')
    $frames=New-Object 'System.Collections.Generic.List[object]'
    $found=@()
    foreach ($token in $tokens) {
        $value=$token.Value
        if ($value -eq '{' -or $value -eq '[') {
            $path=@()
            if ($frames.Count) { $parent=$frames[$frames.Count-1]; $path=@($parent.Path)+@($(if ($parent.Kind -eq '{') {$parent.Key} else {'[array]'})) }
            [void]$frames.Add([pscustomobject]@{Kind=$value;Path=$path;Key=$null}); continue
        }
        if ($value -eq '}' -or $value -eq ']') { $frames.RemoveAt($frames.Count-1); continue }
        if (-not $frames.Count) { continue }
        $frame=$frames[$frames.Count-1]
        $after=$token.Index+$token.Length
        while ($after -lt $Raw.Length -and [char]::IsWhiteSpace($Raw[$after])) { $after++ }
        if ($frame.Kind -eq '{' -and $after -lt $Raw.Length -and $Raw[$after] -eq ':') {
            $decoded=ConvertFrom-SupportedJson ('{"key":'+$value+'}')
            $frame.Key=[string]$decoded.key
        } elseif ($frame.Kind -eq '{' -and $frame.Path.Count -eq 1 -and $frame.Path[0] -ceq 'data/orpul7IDXSSP' -and $frame.Key -ceq 'input') {
            $found += [pscustomobject]@{Start=$token.Index;Length=$token.Length}
        }
    }
    if ($found.Count -ne 1) { throw 'Canonical preset input is missing or ambiguous.' }
    return $found[0]
}

function Get-CanonicalPresetShape([string]$Raw) {
    $data=ConvertFrom-SupportedJson $Raw
    if ($Raw -notmatch '^\s*\{' -or -not ($data -is [pscustomobject])) { throw 'Preset must be a supported JSON object.' }
    $widget=@($data.PSObject.Properties | Where-Object {$_.Name -ceq 'widget/orpul7IDXSSP'})
    $payload=@($data.PSObject.Properties | Where-Object {$_.Name -ceq 'data/orpul7IDXSSP'})
    if ($widget.Count -ne 1 -or $payload.Count -ne 1 -or -not ($widget[0].Value -is [pscustomobject]) -or -not ($payload[0].Value -is [pscustomobject])) { throw 'Preset lacks the canonical widget identity.' }
    $id=@($widget[0].Value.PSObject.Properties | Where-Object {$_.Name -ceq 'id'})
    $key=@($widget[0].Value.PSObject.Properties | Where-Object {$_.Name -ceq 'key'})
    if ($id.Count -ne 1 -or $key.Count -ne 1 -or -not ($id[0].Value -is [string]) -or -not ($key[0].Value -is [string]) -or $id[0].Value -cne 'orpul7IDXSSP' -or $key[0].Value -cne 'widget/html') { throw 'Preset lacks the exact canonical widget identity keys and values.' }
    $input=@($payload[0].Value.PSObject.Properties | Where-Object {$_.Name -ceq 'input'})
    if ($input.Count -ne 1 -or -not ($input[0].Value -is [string])) { throw 'Preset lacks the canonical iframe input.' }
    $settings=New-Object Xml.XmlReaderSettings
    $settings.DtdProcessing=[Xml.DtdProcessing]::Prohibit; $settings.XmlResolver=$null
    $reader=$null; $textReader=New-Object IO.StringReader ([string]$input[0].Value)
    $document=New-Object Xml.XmlDocument
    $document.PreserveWhitespace=$true; $document.XmlResolver=$null
    try { $reader=[Xml.XmlReader]::Create($textReader,$settings); $document.Load($reader) }
    finally { if ($reader) {$reader.Dispose()}; $textReader.Dispose() }
    $iframe=$document.DocumentElement
    if (-not $iframe -or $iframe.Name -cne 'iframe' -or $document.SelectNodes('//*').Count -ne 1 -or -not $iframe.HasAttribute('src')) { throw 'Preset iframe is missing, nested or ambiguous.' }
    $src=$iframe.GetAttribute('src')
    if (-not $src.StartsWith('https://theislampill.github.io/salah_widget/#',[StringComparison]::Ordinal)) { throw 'Preset iframe source is not the supported widget URL.' }
    $uri=$null
    if (-not [Uri]::TryCreate($src,[UriKind]::Absolute,[ref]$uri) -or $uri.Scheme -cne 'https' -or $uri.UserInfo -or $uri.Query) { throw 'Unsupported preset iframe URL.' }
    return [pscustomobject]@{Document=$document;Source=$src;Token=(Get-PresetInputToken $Raw)}
}

function Convert-ConfiguredPreset([string]$Raw) {
    $shape=Get-CanonicalPresetShape $Raw
    if (-not $WidgetHash) { return $Raw }
    if ($WidgetHash -match '[\x00-\x20\x7f]') { throw 'Widget configuration must be an encoded URL fragment.' }
    $fragment=if ($WidgetHash.StartsWith('#')) {$WidgetHash.Substring(1)} else {$WidgetHash}
    $expected='https://theislampill.github.io/salah_widget/#'+$fragment
    $shape.Document.DocumentElement.SetAttribute('src',$expected)
    $serialized=ConvertTo-Json -InputObject $shape.Document.OuterXml -Compress -Depth 4
    $updated=$Raw.Substring(0,$shape.Token.Start)+$serialized+$Raw.Substring($shape.Token.Start+$shape.Token.Length)
    $verified=Get-CanonicalPresetShape $updated
    if ($verified.Source -cne $expected) { throw 'Configured iframe fragment did not survive JSON/URL revalidation.' }
    return $updated
}

function Download-Preset {
    if ($DryRun) { Write-Host "[dry-run] Preset staging suppressed."; return $null }
    if (-not $PresetUrl) { Write-Warn 'No preset URL configured; no import artifact is available.'; return $null }
    $record=$null
    try {
        $record=New-ArtifactRecord 'preset' (ConvertTo-Json -Compress -InputObject @($PresetUrl,$WidgetHash))
        $record.Candidate=New-OwnedStagingFile $WorkRoot ('preset-'+[guid]::NewGuid().ToString('N')+'.partial')
        $record.CandidateIdentity=(Assert-OwnedStagingPath $record.Candidate).Identity
        $record.State='downloading'
        try { Invoke-WebRequest -UseBasicParsing -Uri $PresetUrl -OutFile $record.Candidate | Out-Null }
        catch { $record.State='download-failed'; throw 'Preset acquisition did not complete.' }
        $record.State='downloaded-unvalidated'
        $incoming=Get-StagedFileDigest $record.Candidate
        if ($incoming.Identity -cne $record.CandidateIdentity -or $incoming.Length -gt 16777216) { throw 'Preset candidate identity or supported size differs.' }
        $raw=ConvertFrom-Utf8Bytes ([IO.File]::ReadAllBytes($record.Candidate))
        $configured=Convert-ConfiguredPreset $raw
        [IO.File]::WriteAllText($record.Candidate,$configured,(New-Object Text.UTF8Encoding $false))
        $readback=ConvertFrom-Utf8Bytes ([IO.File]::ReadAllBytes($record.Candidate))
        $null=Get-CanonicalPresetShape $readback
        if ($readback -cne $configured) { throw 'Configured preset readback differs.' }
        $proof=Get-StagedFileDigest $record.Candidate
        if ($proof.Identity -cne $record.CandidateIdentity) { throw 'Configured preset identity changed.' }
        $record.Hash=$proof.Hash; $record.Length=$proof.Length; $record.Validation='strict UTF-8/JSON; canonical singular iframe; exact fragment revalidation'; $record.State='validated'
        try { $path=Publish-OwnedFile $record $PresetRoot 'salah-widget.tablissng.json' }
        catch { $record.State='publication-failed'; throw }
        Write-Ok 'Preset validated and staged for manual import.'
        return $path
    } catch {
        if ($record) { if ($record.State -notmatch 'failed') {$record.State='validation-failed'}; $record.Failure=$_.Exception.Message }
        Write-Warn ('Preset is unavailable; no import path was admitted. ' + $_.Exception.Message)
        return $null
    }
}

function Show-ImportInstructions($Target, [string]$PresetFile) {
    if ($DryRun) { Write-Host "[dry-run] Would guide manual preset import; no artifact resolved."; return }
    Write-Section "Import Salah Widget preset for $($Target.Browser) / $($Target.ProfileName)"
    if (-not $PresetFile) {
        Write-Warn 'No admitted preset is available. Resolve the download/validation error and run the wizard again before importing.'
        Write-Warn 'Importing a preset replaces your current TablissNG dashboard.'
        return
    }
    try { $admitted=Get-AdmittedArtifact $PresetFile 'preset' }
    catch {
        Write-Warn 'Preset path failed current admission readback; no import path will be copied or offered.'
        return
    }
    Write-Host "Preset file:"
    Write-Host "  $PresetFile"
    if (Copy-Text $PresetFile) {
        Write-Ok "Copied the preset file path to clipboard."
    }
    $admitted.State='handed-off'

    Write-Host ""
    Write-Host "Manual import path:"
    Write-Host "  1. Open a new tab controlled by TablissNG."
    Write-Host "  2. Open TablissNG settings."
    Write-Host "  3. Use Import/Restore settings."
    Write-Host "  4. Select the preset JSON file above."
    Write-Host ""
    Write-Host "This wizard does not directly write into browser extension storage."
    Write-Host "That avoids corrupting profiles and avoids touching legacy Tabliss."
    Write-Warn "Importing the preset replaces your current TablissNG dashboard."

    Open-TargetUrl $Target $Target.Config.NewTabUrl
}

function Install-TablissNG($Target) {
    if ($DryRun) { Write-Host "[dry-run] Manual installation actions suppressed; release and paths unresolved."; return }
    $source = $InstallSource
    if ($source -eq "ask") {
        Write-Host ""
        Write-Host "Install source for $($Target.Browser):"
        Write-Host "  1) GitHub latest release/manual install"
        Write-Host "  2) Official browser store page"
        $choice = Read-Host "Choose [1/2] (default 1)"
        if ($choice -eq "2") { $source = "store" } else { $source = "github" }
    }

    if ($source -eq "store") {
        Write-Section "Open official store page for $($Target.Browser)"
        Write-Host $Target.Config.StoreUrl
        Open-TargetUrl $Target $Target.Config.StoreUrl
        Write-Host "Finish the browser's normal extension install, then return here."
        Read-Host "Press Enter after TablissNG is installed"
        return
    }

    Write-Section "Download TablissNG from GitHub latest release for $($Target.Browser)"
    try {
        $asset = Select-TablissNgAsset $Target.Family
        $path = Download-Asset $asset
        $assetAdmission = Get-AdmittedArtifact $path 'asset'

        if ($Target.Family -eq "chromium") {
            $unpacked = Expand-ChromiumAsset $path
            $unpackedAdmission = Get-AdmittedArtifact $unpacked 'unpacked'
            Write-Host ""
            Write-Host "Chromium-family install steps:"
            Write-Host "  1. Open Extensions."
            Write-Host "  2. Enable Developer mode."
            Write-Host "  3. Click Load unpacked."
            Write-Host "  4. Select this folder:"
            Write-Host "     $unpacked"
            if (Copy-Text $unpacked) {
                Write-Ok "Copied unpacked extension folder path to clipboard."
            }
            $unpackedAdmission.State='handed-off'
            Write-Warn 'Keep this unpacked folder while the browser uses it. This wizard never deletes an earlier manual bundle.'
            Open-TargetUrl $Target $Target.Config.ManagerUrl
        } elseif ($Target.Family -eq "firefox") {
            Write-Host ""
            Write-Host "Firefox-family install steps:"
            Write-Host "  1. Open Add-ons Manager."
            Write-Host "  2. Click the gear icon."
            Write-Host "  3. Click Install Add-on From File."
            Write-Host "  4. Select this file:"
            Write-Host "     $path"
            if (Copy-Text $path) {
                Write-Ok "Copied XPI path to clipboard."
            }
            $assetAdmission.State='handed-off'
            Open-TargetUrl $Target $Target.Config.ManagerUrl
        }

        Write-Host ""
        Write-Host "Finish the browser's install prompt, then return here."
        Read-Host "Press Enter after TablissNG is installed"
    } catch {
        Write-Warn $_.Exception.Message
        Write-Warn "Falling back to official store page."
        Open-TargetUrl $Target $Target.Config.StoreUrl
        Read-Host "Press Enter after TablissNG is installed"
    }
}

Write-Host ""
Write-Host "Salah Widget Installer" -ForegroundColor Cyan
Write-Host ""
Write-Host "This wizard can:"
Write-Host "- detect supported browsers/profiles"
Write-Host "- check for TablissNG"
Write-Host "- safely refuse to modify legacy Tabliss profiles"
Write-Host "- download the right TablissNG build from GitHub latest release when needed"
Write-Host "- guide the browser-required install step"
Write-Host "- stage the Salah Widget preset for import"
Write-Host ""
Write-Host "It will not silently force-install extensions or write directly into extension storage."

Write-Section "Detecting browsers"
$targets = @(Get-Targets)

if ($targets.Count -eq 0) {
    Write-Err "No supported browser profiles or installs were detected."
    exit 1
}

foreach ($t in $targets) {
    $eligibility=Get-DiscoveryEligibility $t
    $status = if ($eligibility -eq 'legacy-refused') {
        "legacy Tabliss evidence: REFUSED ($($t.DiscoveryStatus))"
    } elseif ($eligibility -eq 'unknown-held') {
        "discovery unknown: HELD ($($t.DiscoveryReason))"
    } elseif ($t.DiscoveryStatus -eq 'known-new') {
        "TablissNG detected"
    } else {
        "neither extension identified by $($t.DiscoveryEvidence)"
    }
    Write-Host ("[{0}] {1} / {2} - {3}" -f $t.Index, $t.Browser, $t.ProfileName, $status)
}

# Preview is a whole-entry boundary: no terminal prompts or artifact helpers run.
if ($DryRun) {
    Write-Section "Offline preview"
    $eligibleCount=0; $heldCount=0; $refusedCount=0
    foreach ($target in $targets) {
        $eligibility=Get-DiscoveryEligibility $target
        if ($eligibility -eq 'legacy-refused') { $refusedCount++; Write-Warn "Legacy Tabliss: refusing $($target.Browser) / $($target.ProfileName)."; continue }
        if ($eligibility -ne 'eligible-known') { $heldCount++; Write-Warn "Held $($target.Browser) / $($target.ProfileName): $($target.DiscoveryReason). Review metadata manually; no automatic actions."; continue }
        $eligibleCount++
        Write-Host "Would prepare $($target.Browser) / $($target.ProfileName)."
        if (-not $target.HasTablissNG) {
            if ($InstallSource -eq "ask") { Write-Host "Install source unresolved: GitHub manual route or official store page." }
            elseif ($InstallSource -eq "store") { Write-Host "Would open official store: $($target.Config.StoreUrl)" }
            else { Write-Host "Would resolve/download GitHub release; release/version/path unresolved until execution." }
        }
        if ($PresetUrl) { Write-Host "Would stage configured preset and guide manual import; path unresolved until execution." }
        else { Write-Warn "No preset URL configured; preset import cannot be prepared." }
        Write-Host "Would open the browser's manual installation/import pages and offer clipboard paths."
    }
    Write-Host "Preview targets: $eligibleCount eligible, $heldCount held, $refusedCount refused."
    Write-Warn "Importing the preset replaces your current TablissNG dashboard."
    if ($eligibleCount -eq 0) { Write-Err "No eligible target; preview made no changes."; exit 1 }
    Write-Host "Preview only; no changes made. No network requests were made."
    exit 0
}

Write-Host ""
$selection = Read-Host "Select target numbers separated by commas, or 'all' (default all)"
if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "all" }

$selected = @()
if ($selection.Trim().ToLowerInvariant() -eq "all") {
    $selected = $targets
} else {
    $wanted = $selection -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -match "^\d+$" } | ForEach-Object { [int]$_ }
    $selected = @($targets | Where-Object { $wanted -contains $_.Index })
}

if ($selected.Count -eq 0) {
    Write-Err "No valid targets selected."
    exit 1
}

$eligibleCount=0; $heldCount=0; $refusedCount=0
foreach ($target in $selected) {
    switch (Get-DiscoveryEligibility $target) {
        'eligible-known' { $eligibleCount++ }
        'legacy-refused' { $refusedCount++ }
        default { $heldCount++ }
    }
}
Write-Host "Selected targets: $eligibleCount eligible, $heldCount held, $refusedCount refused."
if ($eligibleCount -eq 0) {
    Write-Err "No eligible target selected; unknown targets are held and legacy Tabliss profiles refused. Manual actions remain pending."
    exit 1
}
try {
Initialize-Staging

$presetFile = $null

foreach ($target in $selected) {
    Write-Section "$($target.Browser) / $($target.ProfileName)"

    $eligibility=Get-DiscoveryEligibility $target
    if ($eligibility -eq 'legacy-refused') {
        Write-Warn "Legacy Tabliss detected in this profile. Refusing to touch this browser/profile."
        if ($target.OldMatches.Count -gt 0) {
            Write-Host "Matches:"
            foreach ($m in $target.OldMatches) { Write-Host "  $m" }
        }
        continue
    }
    if ($eligibility -ne 'eligible-known') {
        Write-Warn "Held $($target.Browser) / $($target.ProfileName): $($target.DiscoveryReason). Review metadata manually; no automatic actions."
        continue
    }

    if (-not $target.HasTablissNG) {
        Install-TablissNG $target
    } else {
        Write-Ok "TablissNG already appears to be installed."
    }

    if (-not $presetFile) { $presetFile = Download-Preset }
    Show-ImportInstructions $target $presetFile
}

Write-Section "Manual action pending"
Write-Host "Manual browser installation/import remain pending. Retained bundle:"
Write-Host "  $($script:StagingAttempt.Retained.Path)"
Write-Host "Keep unpacked extension folders while the browser uses them. Enter does not prove installation or release an older folder."
Write-Host "After you verify successful import/install, you may manually delete unneeded preset/XPI files."
Write-Host "Failed candidates remain partial; existing bundles are never adopted as a new-run download cache."
Write-Host ""
Write-Host "Review this script before publishing it. The preset URL should point at your real raw JSON file."
} finally {
    Clear-OwnedScratch
}
