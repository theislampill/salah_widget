
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'utility-wrapper-entered'+[Environment]::NewLine)
Import-Module $env:INSTALL_NATIVE_UTILITY -Scope Local
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'native-utility-imported'+[Environment]::NewLine)
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'output-encoding-set'+[Environment]::NewLine)
# The native host can restore Windows ProgramFiles locations at startup.
# Set the discovery roots in this private child session before Get-Targets.
$env:ProgramFiles=$env:INSTALL_FIXTURE_PF
${env:ProgramFiles(x86)}=$env:INSTALL_FIXTURE_PF86
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'discovery-environment-set'+[Environment]::NewLine)
function Record([string]$Kind,[string]$Value) { [IO.File]::AppendAllText($env:INSTALL_EFFECT_LOG,$Kind+"`t"+$Value+[Environment]::NewLine) }
function In-Fixture([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if(-not $full.StartsWith(($env:INSTALL_SUBJECT_ROOT+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){ throw ('Effect escaped fixture: '+$full) }
}
function Write-Host { param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline,[object]$Separator=' ')
    $text=(@($Object) -join $Separator); if($NoNewline){[Console]::Write($text)}else{[Console]::WriteLine($text)}
}
function New-Item { param($ItemType,$Path,[switch]$Force)
    foreach($p in @($Path)){ In-Fixture $p; Record 'mkdir' $p }
    Microsoft.PowerShell.Management\New-Item -ItemType $ItemType -Path $Path -Force:$Force
}
function Remove-Item { param($LiteralPath,[switch]$Recurse,[switch]$Force)
    In-Fixture $LiteralPath; Record 'remove' $LiteralPath
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $LiteralPath -Recurse:$Recurse -Force:$Force
}
function Invoke-RestMethod { param($Uri,$Headers)
    Record 'metadata' $Uri
    if($env:INSTALL_FIXTURE_NORMAL -ne '1'){throw 'Denied fixture network'}
    [pscustomobject]@{tag_name='v-fixture';assets=@(
        [pscustomobject]@{name='tabliss-chromium.zip';browser_download_url='https://example.invalid/chromium'},
        [pscustomobject]@{name='tabliss-firefox-signed.xpi';browser_download_url='https://example.invalid/firefox'})}
}
function Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing)
    Record 'download' $Uri; In-Fixture $OutFile
    if($env:INSTALL_FIXTURE_NORMAL -ne '1'){throw 'Denied fixture network'}
    if($Uri -eq 'https://example.invalid/preset'){[IO.File]::Copy($env:INSTALL_PRESET_FIXTURE,$OutFile,$true)}
    else{[IO.File]::Copy($env:INSTALL_ASSET_ZIP,$OutFile,$true)}
}
function Expand-Archive { param($LiteralPath,$DestinationPath,[switch]$Force)
    In-Fixture $LiteralPath; In-Fixture $DestinationPath; Record 'extract' $LiteralPath
    Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $LiteralPath -DestinationPath $DestinationPath -Force:$Force
}
function Set-Clipboard { param($Value) Record 'clipboard' $Value }
function Start-Process { param($FilePath,$ArgumentList) Record 'open' ($FilePath+' '+$ArgumentList) }
function Read-Host { param($Prompt) Record 'prompt' $Prompt; if($Prompt -like 'Select target*'){return 'all'}; return '' }
Export-ModuleMember -Function Write-Host,New-Item,Remove-Item,Invoke-RestMethod,Invoke-WebRequest,Expand-Archive,Set-Clipboard,Start-Process,Read-Host -Cmdlet *
[IO.File]::AppendAllText($env:INSTALL_BOOTSTRAP_LOG,'all-spies-exported'+[Environment]::NewLine)
if($env:INSTALL_UNREADABLE_FILE) {
    $probe=[ordered]@{pid=$PID;nonce=$env:INSTALL_READY_NONCE;path=$env:INSTALL_UNREADABLE_FILE;exists=[IO.File]::Exists($env:INSTALL_UNREADABLE_FILE);readSucceeded=$false;nativeCode=$null;exceptionType=$null;targetSha256=$null;peerReadable=$false;peerSha256=$null}
    try {
        $null=[IO.File]::ReadAllText($env:INSTALL_UNREADABLE_FILE);$probe.readSucceeded=$true
        $targetBytes=[IO.File]::ReadAllBytes($env:INSTALL_UNREADABLE_FILE);$targetHasher=[Security.Cryptography.SHA256]::Create()
        try {$probe.targetSha256=([BitConverter]::ToString($targetHasher.ComputeHash($targetBytes))).Replace('-','').ToLowerInvariant()}finally{$targetHasher.Dispose()}
    }
    catch { $cause=$_.Exception.GetBaseException();$probe.nativeCode=($cause.HResult -band 65535);$probe.exceptionType=$cause.GetType().FullName }
    try {
        $peer=[IO.File]::ReadAllBytes($env:INSTALL_READABLE_PEER)
        $hasher=[Security.Cryptography.SHA256]::Create()
        try {$probe.peerSha256=([BitConverter]::ToString($hasher.ComputeHash($peer))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
        $probe.peerReadable=$probe.peerSha256 -ceq $env:INSTALL_METADATA_SHA
    } catch { $probe.peerError=$_.Exception.GetBaseException().Message }
    [IO.File]::WriteAllText($env:INSTALL_UNREADABLE_PROOF,($probe|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
}
if($env:R0016_INPUT_PROBE) {
    . $env:R0016_INPUT_PROBE
    Invoke-R0016EntryInputProbe -SourcePath $env:R0016_ENTRY_SOURCE -SourceSha256 $env:R0016_ENTRY_SOURCE_SHA -ProbePath $env:R0016_INPUT_PROBE -ProofPath $env:R0016_MODULE_INPUT_PROOF -Phase $env:R0016_INPUT_PHASE -Nonce $env:INSTALL_READY_NONCE -ExpectedHost $env:R0016_EXPECTED_HOST
}
$readyToken=[string]$PID+"`t"+$env:INSTALL_READY_NONCE
[IO.File]::WriteAllText($env:INSTALL_READY_FILE,$readyToken)
$wait=[Diagnostics.Stopwatch]::StartNew()
while(-not ([IO.File]::Exists($env:INSTALL_PROFILE_ACK) -and [IO.File]::ReadAllText($env:INSTALL_PROFILE_ACK) -ceq $readyToken)) {
    if($wait.Elapsed.TotalSeconds -gt 10){throw 'Parent profile-boundary acknowledgement missing'}
    Start-Sleep -Milliseconds 20
}
