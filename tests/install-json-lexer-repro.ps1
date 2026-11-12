# Reproducer for the R0013 Test-StrictJson slowdown on PowerShell 7.
# Usage:  pwsh -NoProfile -File repro-lexer.ps1 -Installer <path to install.ps1> [-SizesKB "20,50,100"]
#         powershell.exe -NoProfile -ExecutionPolicy Bypass -File repro-lexer.ps1 -Installer <path> -SizesKB "20,50,100,500"
# It extracts ONLY the text of the Test-StrictJson function from the installer (no other installer code runs),
# builds synthetic extensions.json-like documents of the requested sizes and times the validation. For
# comparison it times one single-pass tokenisation of the same text with the same token grammar.
param([Parameter(Mandatory=$true)][string]$Installer,[string]$SizesKB="20,50,100")
$ErrorActionPreference='Stop'
$lines=[IO.File]::ReadAllLines($Installer)
$start=-1; for($i=0;$i -lt $lines.Length;$i++){ if($lines[$i] -match '^function Test-StrictJson\('){ $start=$i; break } }
if($start -lt 0){ throw 'Test-StrictJson not found' }
$end=-1; for($i=$start+1;$i -lt $lines.Length;$i++){ if($lines[$i] -eq '}'){ $end=$i; break } }
if($end -lt 0){ throw 'end of Test-StrictJson not found' }
Invoke-Expression (($lines[$start..$end]) -join "`n")
function New-Doc([int]$kb){
  $sb=New-Object System.Text.StringBuilder; [void]$sb.Append('{"schemaVersion":36,"addons":['); $n=0
  while($sb.Length -lt ($kb*1024)){
    if($n -gt 0){ [void]$sb.Append(',') }
    [void]$sb.Append('{"id":"addon'+$n+'@example.invalid","version":"1.2.'+$n+'","type":"extension","active":true,"userDisabled":false,"path":"extensions/addon'+$n+'.xpi","defaultLocale":{"name":"Example add-on '+$n+'","description":"synthetic entry"},"targetApplications":[{"id":"toolkit@example.invalid","minVersion":"1.0","maxVersion":"*"}]}')
    $n++
  }
  [void]$sb.Append(']}'); $sb.ToString()
}
$grammar='(?:[ \t\r\n]+|"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null|[{}\[\],:])'
$single=New-Object System.Text.RegularExpressions.Regex($grammar)
"PowerShell $($PSVersionTable.PSVersion)"
foreach($kb in ($SizesKB -split ',' | ForEach-Object { [int]$_ })){
  $doc=New-Doc $kb
  $sw=[Diagnostics.Stopwatch]::StartNew(); $ok=Test-StrictJson $doc; $sw.Stop()
  $sw2=[Diagnostics.Stopwatch]::StartNew(); $c=$single.Matches($doc).Count; $sw2.Stop()
  '{0,5} KB  chars={1,7}  Test-StrictJson={2,8:N2} s  valid={3}  single-pass={4,6:N3} s  tokens={5}' -f $kb,$doc.Length,$sw.Elapsed.TotalSeconds,$ok,$sw2.Elapsed.TotalSeconds,$c
}
