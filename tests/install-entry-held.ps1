# NEW composition carrier. Caller owns Windows execution containment.
# No installer/source fragment is evaluated before the explicit before gate.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$spec=[IO.File]::ReadAllText($env:R0016_COMPOSITION_SPEC)|ConvertFrom-Json
if($spec.schema -cne 'r0016-entry-held-spec.v1'){throw 'Wrong held spec schema'}
if([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT){throw 'Native Windows required'}
$hostPath=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
if($hostPath -cne $spec.host){throw 'Actual command host differs from frozen launch'}
if(($spec.expectedHost -ceq 'ps51' -and ($PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1)) -or
   ($spec.expectedHost -ceq 'ps7' -and ($PSVersionTable.PSEdition -cne 'Core' -or $PSVersionTable.PSVersion.ToString() -cne '7.6.6')) -or
   $spec.expectedHost -cnotin @('ps51','ps7')){throw 'Wrong native host version'}
function Assert-ExactInput($Fact){
    if(-not [IO.Path]::IsPathRooted([string]$Fact.path)){throw 'Input path is not absolute'}
    $raw=[IO.File]::ReadAllBytes($Fact.path);$hash=[Security.Cryptography.SHA256]::Create()
    try{$digest=([BitConverter]::ToString($hash.ComputeHash($raw))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
    if($raw.Length -ne $Fact.bytes -or $digest -cne $Fact.sha256){throw 'Exact input bytes changed'}
}
foreach($inputFact in @($spec.sourceFact,$spec.driverFact,$spec.guardFact,$spec.windowFact,$spec.probeFact)){Assert-ExactInput $inputFact}
if($spec.source -cne $spec.sourceFact.path -or $spec.driverFact.path -cne $PSCommandPath -or
   $spec.guardSource -cne $spec.guardFact.path -or $spec.windowSupport -cne $spec.windowFact.path -or $spec.inputProbe -cne $spec.probeFact.path){throw 'Input role/path mismatch'}
if($spec.scope -cnotin @('product','source-free-diagnostic') -or $spec.guardMode -cnotin @('deny','allow')){throw 'Unknown invocation scope/guard mode'}
if($spec.guardMode -ceq 'allow' -and $spec.scope -cne 'source-free-diagnostic'){throw 'Product invocation cannot disable source guards'}
. $spec.inputProbe

# Parse the exact recovered driver and import only its named guard definitions.
# Its top-level suite and hard-coded invocation parameters never execute here.
$guardNames=@('Add-Effect','Deny-Effect','Write-Host','New-Item','Remove-Item','Copy-Item','Move-Item',
    'Set-Content','Add-Content','Out-File','Set-Acl','Expand-Archive','Invoke-RestMethod','Invoke-WebRequest',
    'Set-Clipboard','Start-Process','Read-Host','Add-Type','Add-SourceBreakpoints')
$tokens=$null;$errors=$null
$guardAst=[Management.Automation.Language.Parser]::ParseFile($spec.guardSource,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Exact guard driver failed native parsing'}
foreach($name in $guardNames){
    $definitions=@($guardAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -ceq $name})
    if($definitions.Count -ne 1){throw ('Guard definition absent or duplicated: '+$name)}
    . ([scriptblock]::Create($definitions[0].Extent.Text))
}
$tokens=$null;$errors=$null
$windowAst=[Management.Automation.Language.Parser]::ParseFile($spec.windowSupport,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Exact window library failed native parsing'}
$gate=@($windowAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -ceq 'Wait-PreviewInvocationGate'})
if($gate.Count -ne 1){throw 'Gate definition absent or duplicated'}
. ([scriptblock]::Create($gate[0].Extent.Text))

$global:R0016EventFile=$spec.events
$global:R0016Effects=New-Object 'System.Collections.Generic.List[object]'
$global:R0016Breakpoints=New-Object 'System.Collections.Generic.List[object]'
$global:R0016Messages=New-Object 'System.Collections.Generic.List[string]'
[IO.File]::WriteAllText($spec.events,'')
$stopHandler=[System.EventHandler[Management.Automation.DebuggerStopEventArgs]]{
    param($sender,$eventArgs)
    $eventArgs.ResumeAction=[Management.Automation.DebuggerResumeAction]::Stop
}
[Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.add_DebuggerStop($stopHandler)
$guardEstablished=$false;$preparationError=$null;$entryExit=$null
$sourceCompletion='not-invoked';$sourceExitCode=$null;$sourceException=$null;$inventory=@()
try {
    $parameters=@{}
    foreach($parameter in @($spec.parameters)){
        if($parameters.ContainsKey([string]$parameter.name)){throw 'Duplicate typed parameter'}
        if($parameter.type -ceq 'string' -and $parameter.name -cin @('PresetUrl','WidgetHash','InstallSource') -and $parameter.value -is [string]){
            $parameters[$parameter.name]=[string]$parameter.value
        } elseif($parameter.type -ceq 'switch' -and $parameter.name -cin @('DryRun','NoOpen') -and $parameter.value -is [bool] -and $parameter.value){
            $parameters[$parameter.name]=[bool]$parameter.value
        } else {throw 'Unknown parameter name/type/value'}
    }
    if(-not $parameters.ContainsKey('PresetUrl') -or -not $parameters.ContainsKey('WidgetHash') -or $parameters.DryRun -ne $true){throw 'Missing required exact preview parameters'}
    if($spec.guardMode -ceq 'deny'){
        $inventory=Add-SourceBreakpoints $spec.source @($spec.effectHelpers)
        $guardEstablished=$true
    }
    $env:ProgramFiles=$env:INSTALL_FIXTURE_PF
    [Environment]::SetEnvironmentVariable('ProgramFiles(x86)',$env:INSTALL_FIXTURE_PF86,'Process')
    $global:LASTEXITCODE=$null
    Invoke-R0016EntryInputProbe -SourcePath $spec.source -SourceSha256 $spec.sourceFact.sha256 -ProbePath $spec.inputProbe -ProofPath $spec.beforeInputProof -Phase 'held-before-source' -Nonce $spec.nonce -ExpectedHost $spec.expectedHost
    Wait-PreviewInvocationGate $spec 'before'
    try {
        try {
            # Complete original file: parameter binding/defaults and source
            # finally/cleanup all occur inside this held interval.
            & $spec.source @parameters
            if($null -eq $LASTEXITCODE){$entryExit=0;$sourceCompletion='fallthrough'}
            else{$entryExit=[int]$LASTEXITCODE;$sourceExitCode=$entryExit;$sourceCompletion='exit-code-observed'}
        } catch {
            $entryExit=1;$sourceCompletion='terminating-exception';$sourceException=$_.Exception.Message
        }
    } finally {
        Wait-PreviewInvocationGate $spec 'after'
    }
} catch {
    $preparationError=$_.Exception.Message
} finally {
    foreach($breakpoint in $global:R0016Breakpoints){Remove-PSBreakpoint -Breakpoint $breakpoint}
    [Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.remove_DebuggerStop($stopHandler)
}
$events=@(if([IO.File]::Exists($spec.events)){[IO.File]::ReadAllLines($spec.events)|Where-Object{$_}|ForEach-Object{$_|ConvertFrom-Json}})
$result=[ordered]@{
    schema='r0016-entry-held-result.v1';pid=$PID;nonce=$spec.nonce;nativeWindows=$true
    expectedHost=$spec.expectedHost;commandHost=$hostPath;hostVersion=$PSVersionTable.PSVersion.ToString();hostEdition=$PSVersionTable.PSEdition
    sourceFact=$spec.sourceFact;parameters=@($spec.parameters);scope=$spec.scope;guardMode=$spec.guardMode;guardEstablished=$guardEstablished
    preparationError=$preparationError;entryExit=$entryExit;sourceCompletion=$sourceCompletion
    sourceExitCode=$sourceExitCode;sourceException=$sourceException;methodInventory=@($inventory)
    events=$events;messages=$global:R0016Messages.ToArray()
}
[IO.File]::WriteAllText($spec.result,($result|ConvertTo-Json -Depth 20),(New-Object Text.UTF8Encoding $false))
if($preparationError){exit 1}
exit 0
