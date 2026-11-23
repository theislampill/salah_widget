# R0033 R33-09 QA helper: an OS-level CPU limit for browser processes this QA run launched (Windows only).
# A Windows Job Object with CPU rate control (hard cap). Processes are assigned by PID; a process cannot leave a job,
# so "uncap" clears the rate control instead. The job has no kill-on-close flag: when the helper exits the limits
# stay with the (QA-owned) processes until they exit. Nothing system-wide is changed.
# Protocol: one command per stdin line, one JSON line per command on stdout.
#   assign <pid>      add a process to the job
#   cap <cpuRate>     hard cap, in 1/100 % of the WHOLE machine (all logical processors); 10000 = the whole machine
#   affinity <mask>   restrict the job's processes to the processors in <mask> (decimal); 0 clears it
#   uncap             clear the rate control (and keep any affinity)
#   account           total user+kernel CPU of the job's processes so far (100 ns units) and the active process count
#   quit
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class R0033Job {
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern IntPtr CreateJobObjectW(IntPtr a, string name);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr proc);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool SetInformationJobObject(IntPtr job, int cls, IntPtr info, uint len);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool QueryInformationJobObject(IntPtr job, int cls, IntPtr info, uint len, IntPtr ret);
  public static IntPtr Job = IntPtr.Zero;
  public static int Create(){ Job = CreateJobObjectW(IntPtr.Zero, null); return Job==IntPtr.Zero ? Marshal.GetLastWin32Error() : 0; }
  public static int Assign(uint pid){
    // PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION
    IntPtr p = OpenProcess(0x0100 | 0x0001 | 0x1000, false, pid); if(p==IntPtr.Zero) return Marshal.GetLastWin32Error();
    bool ok = AssignProcessToJobObject(Job, p); int e = ok ? 0 : Marshal.GetLastWin32Error(); CloseHandle(p); return e;
  }
  // JobObjectCpuRateControlInformation = 15: { DWORD ControlFlags; DWORD CpuRate } (union, CpuRate variant)
  public static int Rate(uint flags, uint rate){
    IntPtr b = Marshal.AllocHGlobal(8); Marshal.WriteInt32(b, 0, (int)flags); Marshal.WriteInt32(b, 4, (int)rate);
    bool ok = SetInformationJobObject(Job, 15, b, 8); int e = ok ? 0 : Marshal.GetLastWin32Error(); Marshal.FreeHGlobal(b); return e;
  }
  // JobObjectBasicLimitInformation = 2 (64-bit layout, 64 bytes): LimitFlags at 16, Affinity (ULONG_PTR) at 48.
  public static int Affinity(ulong mask){
    IntPtr b = Marshal.AllocHGlobal(64); for(int i=0;i<64;i++) Marshal.WriteByte(b, i, 0);
    if(mask != 0){ Marshal.WriteInt32(b, 16, 0x00000010); Marshal.WriteInt64(b, 48, (long)mask); }
    bool ok = SetInformationJobObject(Job, 2, b, 64); int e = ok ? 0 : Marshal.GetLastWin32Error(); Marshal.FreeHGlobal(b); return e;
  }
  // JobObjectBasicAccountingInformation = 1: TotalUserTime@0, TotalKernelTime@8, ..., ActiveProcesses@40 (48 bytes).
  public static long[] Account(){
    IntPtr b = Marshal.AllocHGlobal(48); bool ok = QueryInformationJobObject(Job, 1, b, 48, IntPtr.Zero);
    long[] r = ok ? new long[]{ Marshal.ReadInt64(b,0), Marshal.ReadInt64(b,8), Marshal.ReadInt32(b,40), 0 } : new long[]{0,0,0,Marshal.GetLastWin32Error()};
    Marshal.FreeHGlobal(b); return r;
  }
}
'@
function Out-Line($o) { [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress)); [Console]::Out.Flush() }
$e = [R0033Job]::Create()
Out-Line @{ op = 'create'; error = $e; logicalProcessors = [Environment]::ProcessorCount }
while ($null -ne ($line = [Console]::In.ReadLine())) {
  $p = $line.Trim() -split '\s+'
  switch ($p[0]) {
    'assign'   { Out-Line @{ op = 'assign'; pid = [uint32]$p[1]; error = [R0033Job]::Assign([uint32]$p[1]) } }
    # JOB_OBJECT_CPU_RATE_CONTROL_ENABLE (1) | JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP (4)
    'cap'      { Out-Line @{ op = 'cap'; cpuRate = [uint32]$p[1]; error = [R0033Job]::Rate(5, [uint32]$p[1]) } }
    'uncap'    { Out-Line @{ op = 'uncap'; error = [R0033Job]::Rate(0, 0) } }
    'affinity' { Out-Line @{ op = 'affinity'; mask = [uint64]$p[1]; error = [R0033Job]::Affinity([uint64]$p[1]) } }
    'account'  { $a = [R0033Job]::Account(); Out-Line @{ op = 'account'; user100ns = $a[0]; kernel100ns = $a[1]; activeProcesses = $a[2]; error = $a[3] } }
    'quit'     { Out-Line @{ op = 'quit' }; exit 0 }
    default    { Out-Line @{ op = $p[0]; error = 'unknown command' } }
  }
}
