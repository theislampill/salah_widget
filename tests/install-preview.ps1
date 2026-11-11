#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [ValidateSet('Helpers','Wrapper','Mutants','All')][string]$Suite='All',
    [string]$OutputRoot=$(if($env:RUNNER_TEMP){$env:RUNNER_TEMP}else{[IO.Path]::GetTempPath()}),
    [string]$FixtureLibrary=(Join-Path $PSScriptRoot 'install-preview-acquire-timed.ps1')
)
# Actual helper/wrapper supplement. Fresh native installer -File and normal
# controls remain separate receipts from the maintained native entry harness.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$Utf8=New-Object Text.UTF8Encoding $false
$NativeWindows=[Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
$HostExecutable=[Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
$NativeModules=Join-Path $PSHOME 'Modules'
$FixtureRoot=Join-Path $OutputRoot ('r0016-preview-ps-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($FixtureRoot)
$FixtureRoot=[IO.Path]::GetFullPath($FixtureRoot)
$libraryTokens=$null;$libraryErrors=$null
$libraryAst=[Management.Automation.Language.Parser]::ParseFile($FixtureLibrary,[ref]$libraryTokens,[ref]$libraryErrors)
if(@($libraryErrors).Count){throw 'BOOTSTRAP_BLOCKED: fixture library does not parse'}
$allowedFixtureFunctions=@('Write-FixtureText','Hash-File','Snapshot-Subject','New-ChildContext','Invoke-AcquisitionChild')
foreach($definition in $libraryAst.EndBlock.Statements){
    if($definition -is [Management.Automation.Language.FunctionDefinitionAst] -and $definition.Name -in $allowedFixtureFunctions){
        . ([scriptblock]::Create($definition.Extent.Text))
    }
}
foreach($name in $allowedFixtureFunctions){if(-not (Get-Command $name -CommandType Function -ErrorAction SilentlyContinue)){throw ('BOOTSTRAP_BLOCKED: missing fixture function '+$name)}}
$TestHashAtStart=Hash-File $PSCommandPath
$LibraryHashAtStart=Hash-File $FixtureLibrary
# This supplement extends, but does not mutate, the frozen acquisition library.
# DACL/owner/group changes and last-write timestamps belong to filesystem state.
function Snapshot-Subject([string]$Path){
    $rows=New-Object 'System.Collections.Generic.List[object]'
    foreach($item in @(Get-Item -LiteralPath $Path -Force)+@(Get-ChildItem -LiteralPath $Path -Force -Recurse|Sort-Object FullName)){
        $link=($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        $sddl=$null
        if($NativeWindows){
            $security=Get-Acl -LiteralPath $item.FullName
            $sections=[Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group -bor [Security.AccessControl.AccessControlSections]::Access
            $sddl=$security.GetSecurityDescriptorSddlForm($sections)
        }
        $rows.Add([pscustomobject]@{
            path=$item.FullName.Substring($Path.Length).Replace('\','/');attributes=[string]$item.Attributes
            hash=if(-not $item.PSIsContainer -and -not $link){Hash-File $item.FullName}else{$null}
            lastWriteUtc=$item.LastWriteTimeUtc.Ticks;sddl=$sddl
            linkTarget=if($link){[string]$item.Target}else{$null}
        })
    }
    return $rows.ToArray()
}
$SourceFile=[IO.Path]::GetFullPath($SourceFile)
$SourceBytes=[IO.File]::ReadAllBytes($SourceFile)
$SourceHash=Hash-File $SourceFile
$FrozenSource=Join-Path $FixtureRoot 'actual-source.ps1'
[IO.File]::WriteAllBytes($FrozenSource,$SourceBytes)
$tokens=$null;$parseErrors=$null
$sourceAst=[Management.Automation.Language.Parser]::ParseFile($FrozenSource,[ref]$tokens,[ref]$parseErrors)
if(@($parseErrors).Count -or @($SourceBytes|Where-Object{$_ -gt 127}).Count){throw 'BOOTSTRAP_BLOCKED: source must parse and preserve the ASCII source contract'}
$SourceFunctions=Join-Path $FixtureRoot 'actual-functions.ps1'
$definitions=@($sourceAst.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]})
Write-FixtureText $SourceFunctions (($definitions|ForEach-Object{$_.Extent.Text}) -join ([Environment]::NewLine+[Environment]::NewLine))

$EffectHelpers=@(
    'Initialize-CompilerNative','Read-CompilerPathFacts','Open-CompilerDirectoryLease','Open-CompilerOutputLease',
    'New-StagingCompilerContext','Clear-StagingCompilerContext','Invoke-StagingCompiler',
    'Initialize-StagingNative','Get-StagingUserSid','Open-StagingDirectoryLease','Get-StagingPathInfo',
    'New-PrivateStagingDirectory','New-PrivateStagingFile','Get-TrustedStagingParent','Assert-OwnedStagingPath',
    'New-OwnedStagingFile','Get-StagedFileDigest','Get-OwnedStagingFiles','Get-AdmittedArtifact',
    'Initialize-Staging','Clear-OwnedScratch','New-ArtifactRecord','Publish-OwnedFile','Test-ExtensionArchive',
    'Get-LatestRelease','Select-TablissNgAsset','Download-Asset','Expand-ChromiumAsset','Download-Preset',
    'Copy-Text','Open-TargetUrl','Install-TablissNG','Show-ImportInstructions'
)
$actualNames=@($definitions|ForEach-Object{$_.Name})
$missing=@($EffectHelpers|Where-Object{$_ -notin $actualNames})
if($missing.Count){throw ('BOOTSTRAP_BLOCKED: actual helper inventory changed: '+($missing -join ', '))}
$Driver=Join-Path $FixtureRoot 'preview-child.ps1'
$DriverText=@'
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false
$spec=[IO.File]::ReadAllText($env:R0016_PREVIEW_SPEC)|ConvertFrom-Json
$global:R0016EventFile=$spec.events
$global:R0016Effects=New-Object 'System.Collections.Generic.List[object]'
$global:R0016Breakpoints=New-Object 'System.Collections.Generic.List[object]'
$global:R0016Messages=New-Object 'System.Collections.Generic.List[string]'
function Add-Effect([string]$Kind,[string]$Detail){
    $row=[pscustomobject]@{kind=$Kind;detail=$Detail;utc=[DateTime]::UtcNow.ToString('o')}
    [void]$global:R0016Effects.Add($row)
    [IO.File]::AppendAllText($global:R0016EventFile,($row|ConvertTo-Json -Compress)+[Environment]::NewLine)
}
function Deny-Effect([string]$Kind,[object[]]$Values){Add-Effect $Kind ($Values -join ' ');throw ('Fixture denied '+$Kind)}
function Write-Host {
    param([object]$Object,[object]$ForegroundColor,[object]$BackgroundColor,[switch]$NoNewline,[object]$Separator=' ')
    $text=@($Object) -join $Separator
    [void]$global:R0016Messages.Add($text)
    if($NoNewline){[Console]::Write($text)}else{[Console]::WriteLine($text)}
}
function New-Item {Deny-Effect 'filesystem-create' $args}
function Remove-Item {Deny-Effect 'filesystem-remove' $args}
function Copy-Item {Deny-Effect 'filesystem-copy' $args}
function Move-Item {Deny-Effect 'filesystem-move' $args}
function Set-Content {Deny-Effect 'filesystem-write' $args}
function Add-Content {Deny-Effect 'filesystem-write' $args}
function Out-File {Deny-Effect 'filesystem-write' $args}
function Set-Acl {Deny-Effect 'filesystem-acl' $args}
function Expand-Archive {Deny-Effect 'extract' $args}
function Invoke-RestMethod {Deny-Effect 'metadata' $args}
function Invoke-WebRequest {Deny-Effect 'download' $args}
function Set-Clipboard {Deny-Effect 'clipboard' $args}
function Start-Process {Deny-Effect 'open' $args}
function Read-Host {Deny-Effect 'prompt' $args}
function Add-Type {Deny-Effect 'native-load-or-compiler' $args}
$stopHandler=[System.EventHandler[Management.Automation.DebuggerStopEventArgs]]{
    param($sender,$eventArgs)
    $eventArgs.ResumeAction=[Management.Automation.DebuggerResumeAction]::Stop
}
[Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.add_DebuggerStop($stopHandler)
function Add-SourceBreakpoints([string]$File,[string[]]$GuardedHelpers){
    $t=$null;$e=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($File,[ref]$t,[ref]$e)
    if(@($e).Count){throw 'BOOTSTRAP: breakpoint subject does not parse'}
    $rows=New-Object 'System.Collections.Generic.List[object]'
    $effectCommands=@('New-Item','Remove-Item','Copy-Item','Move-Item','Set-Content','Add-Content','Out-File','Set-Acl','Expand-Archive','Invoke-RestMethod','Invoke-WebRequest','Set-Clipboard','Start-Process','Read-Host','Add-Type')
    foreach($node in $ast.FindAll({param($n) $n -is [Management.Automation.Language.InvokeMemberExpressionAst] -or $n -is [Management.Automation.Language.CommandAst]},$true)){
        $effect=$false;$detail=''
        if($node -is [Management.Automation.Language.CommandAst]){
            $name=$node.GetCommandName()
            if($name -and (($name -split '\\')[-1] -in $effectCommands)){$effect=$true;$detail='command '+$name}
        } else {
            $method=if($node.Member -is [Management.Automation.Language.StringConstantExpressionAst]){$node.Member.Value}else{'<dynamic>'}
            $type=if($node.Expression -is [Management.Automation.Language.TypeExpressionAst]){$node.Expression.TypeName.FullName}else{''}
            $parent=$node.Parent;$owner=''
            while($parent){if($parent -is [Management.Automation.Language.FunctionDefinitionAst]){$owner=$parent.Name;break};$parent=$parent.Parent}
            if($owner -in $GuardedHelpers -or $type -eq 'SalahInstaller.StageNative' -or
                ($type -match '^(System\.)?IO\.(File|Directory)$' -and $method -match '^(Write|Append|Delete|Move|Copy|Create|Open|Set)') -or
                $type -match '^(System\.)?Net\.' -or
                $method -match '^(Connect|ConnectAsync|Send|SendAsync|SendTo|SendToAsync|GetResponse|GetResponseAsync|GetRequestStream|DownloadString|DownloadFile|DownloadData|UploadString|UploadFile|UploadData)$' -or
                ($type -match '^(System\.)?Diagnostics\.Process$' -and $method -eq 'Start') -or
                ($type -match 'Clipboard$' -and $method -match '^Set')){
                $effect=$true;$detail='method '+$type+'::'+$method+' owner='+$owner
            }
        }
        if($effect){[void]$rows.Add([pscustomobject]@{line=$node.Extent.StartLineNumber;column=$node.Extent.StartColumnNumber;detail=$detail})}
    }
    foreach($row in $rows){
        $eventPath=$global:R0016EventFile
        $lineJson=([pscustomobject]@{kind='source-call';detail=$row.detail;file=$File;line=$row.line;column=$row.column}|ConvertTo-Json -Compress)
        $action={
            [IO.File]::AppendAllText($eventPath,$lineJson+[Environment]::NewLine)
            break
        }.GetNewClosure()
        $bp=Set-PSBreakpoint -Script $File -Line $row.line -Column $row.column -Action $action
        [void]$global:R0016Breakpoints.Add($bp)
    }
    return $rows.ToArray()
}
$guardEstablished=$false;$preparationError=$null;$returned=New-Object 'System.Collections.Generic.List[object]'
$reason=$null;$reasonStack=$null;$entryExit=0;$nullReturnCount=0;$beforeContext=$null;$afterContext=$null;$typeBefore=$false;$typeAfter=$false
$beforeCompilerContext=$null;$afterCompilerContext=$null;$compilerTypeBefore=$false;$compilerTypeAfter=$false;$compilerReferenceUnchanged=$false
try {
    # Denial is proved in a separate child before product cases. Debugger Stop
    # ends the whole pipeline; it cannot resume an inline preparation probe.
    $global:R0016EventFile=$spec.events
    [IO.File]::WriteAllText($spec.events,'')
    if($spec.mode -eq 'control'){
        if($spec.denyControl){$inventory=Add-SourceBreakpoints $spec.controlMethod @('Invoke-R0016DirectTransport')}
    } elseif($spec.mode -eq 'helper'){
        $inventory=Add-SourceBreakpoints $spec.functions $spec.effectHelpers
        . $spec.functions
    } else {
        $inventory=Add-SourceBreakpoints $spec.source $spec.effectHelpers
    }
    [IO.File]::WriteAllText($spec.readiness,$spec.nonce)
    $guardEstablished=$true
    if($spec.mode -eq 'baseline'){
        [IO.File]::WriteAllText($spec.result,'{"baseline":true,"installerExecuted":false}')
        exit 0
    }
    if($spec.mode -eq 'control'){
        & $spec.controlMethod
        [IO.File]::WriteAllText($spec.result,'{"controlReturned":true}')
        exit 0
    }
    $DryRun=$true;$NoOpen=$false;$InstallSource='ask'
    $TablissNgRepo='fixture/repo';$PresetUrl='https://fixture.invalid/preset'
    $WidgetHash='lat=24.47&lon=39.61&label=Fixture%20City&method=4'
    $WorkRoot=$spec.work;$DownloadRoot=$spec.download;$PresetRoot=$spec.presets
    $CachedPath=$spec.cached;$PresetPath=$spec.preset
    $Asset=[pscustomobject]@{id=101;name='tabliss-chromium.zip';browser_download_url='https://fixture.invalid/asset'}
    $script:LatestRelease=[pscustomobject]@{id=201;tag_name='v-fixture';assets=@($Asset)}
    $Target=[pscustomobject]@{Browser='Fixture';ProfileName='fixture';ProfilePath=$spec.profile;Family='chromium';ExePath=$null;Config=[pscustomobject]@{StoreUrl='https://fixture.invalid/store';ManagerUrl='fixture://extensions';NewTabUrl='fixture://newtab'}}
    $global:R0016LeaseDispose=0
    $lease=[pscustomobject]@{FixtureLease=$true}
    $lease|Add-Member -MemberType ScriptMethod -Name Dispose -Value {$global:R0016LeaseDispose++;Add-Effect 'lease-dispose' 'fixture lease'}
    $artifacts=New-Object 'System.Collections.Generic.List[object]'
    foreach($kind in @('asset','unpacked','preset')){
        [void]$artifacts.Add([pscustomobject]@{
            Attempt='r0016-current';Kind=$kind;Source='fixture';State='published';Candidate=$CachedPath;CandidateIdentity='fixture'
            PublicationCandidate=$null;Path=if($kind -eq 'preset'){$PresetPath}else{$CachedPath};Identity='fixture';Hash='fixture';Length=1
            ExpectedLength=1;ExpectedDigest=$null;Validation='fixture sentinel only';Failure=$null;ExtractionRoot=$spec.unpacked;Files=@()
        })
    }
    $script:StagingAttempt=[pscustomobject]@{
        Id='r0016-current';Sid='S-1-0-0';Status='active'
        Scratch=[pscustomobject]@{Path=$WorkRoot;Identity='fixture';Private=$true;Directory=$true}
        Retained=[pscustomobject]@{Path=$spec.retained;Identity='fixture';Private=$true;Directory=$true}
        Artifacts=$artifacts;Leases=@($lease)
    }
    # Owned-like compiler sentinels exercise both cleanup outcomes without
    # inventing native admission. Their directory and bytes are in the subject.
    $global:R0016CompilerLeaseDispose=0
    $compilerRootHandle=[pscustomobject]@{FixtureCompilerHandle='root';Disposed=$false}
    $compilerParentHandle=[pscustomobject]@{FixtureCompilerHandle='parent';Disposed=$false}
    foreach($handle in @($compilerRootHandle,$compilerParentHandle)){
        $handle|Add-Member -MemberType ScriptMethod -Name Dispose -Value {$this.Disposed=$true;$global:R0016CompilerLeaseDispose++;Add-Effect 'compiler-lease-dispose' $this.FixtureCompilerHandle}
    }
    $compilerLeases=New-Object 'System.Collections.Generic.List[object]'
    [void]$compilerLeases.Add([pscustomobject]@{Handle=$compilerParentHandle;Facts=[pscustomobject]@{Path=$spec.work;Identity='fixture-compiler-parent';Directory=$true;TrustedAncestor=$true}})
    $CompilerContext=[pscustomobject]@{
        Id='r0016-compiler';Status='owned';Path=$spec.compiler;Identity='fixture-compiler';Sid='S-1-0-0';DefaultOwnerSid='S-1-0-0';InvocationStarted=$false;CompilerExitCode=$null;Created=$true
        RootLease=[pscustomobject]@{Handle=$compilerRootHandle;Facts=[pscustomobject]@{Path=$spec.compiler;Identity='fixture-compiler';Private=$true;Directory=$true}}
        Leases=$compilerLeases;CleanupError=$null
    }
    $script:CompilerScratch=$CompilerContext
    $Record=$artifacts[0]
    $beforeContext=$script:StagingAttempt|ConvertTo-Json -Depth 9 -Compress
    $typeBefore=$null -ne ('SalahInstaller.StageNative' -as [type])
    $beforeCompilerContext=$script:CompilerScratch|ConvertTo-Json -Depth 9 -Compress
    $compilerTypeBefore=$null -ne ('SalahInstaller.CompilerNative' -as [type])
    if($spec.mode -eq 'helper'){
        try { & ([scriptblock]::Create($spec.call)) | ForEach-Object {if($null -ne $_){[void]$returned.Add($_)}else{$nullReturnCount++}} }
        catch { $reason=$_.Exception.Message;$reasonStack=$_.ScriptStackTrace }
    } else {
        $env:ProgramFiles=$env:R0016_FIXTURE_PF
        [Environment]::SetEnvironmentVariable('ProgramFiles(x86)',$env:R0016_FIXTURE_PF86,'Process')
        $parameters=@{DryRun=$true;PresetUrl=$spec.presetUrl;WidgetHash=$WidgetHash}
        if(-not $spec.omitInstallSource){$parameters.InstallSource=$spec.route}
        if($spec.noOpen){$parameters.NoOpen=$true}
        $global:LASTEXITCODE=0
        try{& $spec.source @parameters | ForEach-Object {if($null -ne $_){[void]$returned.Add($_)}else{$nullReturnCount++}};$entryExit=$LASTEXITCODE}
        catch{$entryExit=1;$reason=$_.Exception.Message;$reasonStack=$_.ScriptStackTrace}
    }
    $typeAfter=$null -ne ('SalahInstaller.StageNative' -as [type])
    $afterContext=$script:StagingAttempt|ConvertTo-Json -Depth 9 -Compress
    $compilerTypeAfter=$null -ne ('SalahInstaller.CompilerNative' -as [type])
    $afterCompilerContext=$script:CompilerScratch|ConvertTo-Json -Depth 9 -Compress
    $compilerReferenceUnchanged=[object]::ReferenceEquals($CompilerContext,$script:CompilerScratch)
} catch {
    if(-not $guardEstablished){$preparationError=$_.Exception.Message}else{$reason=$_.Exception.Message;$entryExit=1}
} finally {
    foreach($bp in $global:R0016Breakpoints){Remove-PSBreakpoint -Breakpoint $bp}
    [Management.Automation.Runspaces.Runspace]::DefaultRunspace.Debugger.remove_DebuggerStop($stopHandler)
}
$events=@(if([IO.File]::Exists($spec.events)){[IO.File]::ReadAllLines($spec.events)|Where-Object{$_}|ForEach-Object{$_|ConvertFrom-Json}})
$result=[pscustomobject]@{
    guardEstablished=$guardEstablished;preparationError=$preparationError
    sourceSha256=$spec.sourceSha256;source=$spec.source;scope=$spec.mode
    methodInventory=$inventory;events=$events;returned=$returned.ToArray();returnCount=$returned.Count
    reason=$reason;reasonStack=$reasonStack;entryExit=$entryExit;nullReturnCount=$nullReturnCount;messages=$global:R0016Messages.ToArray()
    stagingContextUnchanged=($beforeContext -ceq $afterContext);leaseDisposeCalls=$global:R0016LeaseDispose
    nativeTypeBefore=$typeBefore;nativeTypeAfter=$typeAfter
    compilerContextBefore=$beforeCompilerContext;compilerContextAfter=$afterCompilerContext
    compilerContextUnchanged=($beforeCompilerContext -ceq $afterCompilerContext);compilerContextReferenceUnchanged=$compilerReferenceUnchanged
    compilerLeaseDisposeCalls=$global:R0016CompilerLeaseDispose;compilerNativeTypeBefore=$compilerTypeBefore;compilerNativeTypeAfter=$compilerTypeAfter
}
[IO.File]::WriteAllText($spec.result,($result|ConvertTo-Json -Depth 12))
'@
Write-FixtureText $Driver $DriverText

function New-PreviewCase([string]$Name,[string]$Mode,[string]$Population='known'){
    # Keep fixture source ASCII while exercising actual non-ASCII native paths.
    $context=New-ChildContext ($Name+'-unicode-'+[char]0x0635)
    $fixtureProfile=$context.values.USERPROFILE
    $work=Join-Path $context.values.TEMP 'SalahWidgetAttempt-existing'
    $retained=Join-Path $fixtureProfile 'SalahWidgetBundle-existing'
    $download=Join-Path $retained 'downloads'
    $presets=Join-Path $retained 'presets'
    $unpacked=Join-Path $retained 'unpacked-existing'
    $compiler=Join-Path $context.values.TEMP 'SalahWidgetCompiler-existing'
    foreach($path in @($work,$retained,$download,$presets,$unpacked,$compiler)){[void][IO.Directory]::CreateDirectory($path)}
    $cached=Join-Path $download 'tabliss-chromium.zip'
    $preset=Join-Path $presets 'salah-widget.tablissng.json'
    Write-FixtureText $cached 'malformed cached archive must remain unchanged'
    Write-FixtureText (Join-Path $download 'tabliss-firefox-signed.xpi') 'malformed cached xpi must remain unchanged'
    Write-FixtureText $preset ('{"sentinel":"keep '+[char]0x0635+'","input":"malformed preset fixture"}')
    Write-FixtureText (Join-Path $unpacked 'marker') 'existing unpacked bytes'
    Write-FixtureText (Join-Path $compiler 'compiler-output.tmp') 'existing compiler bytes must remain unchanged'
    if($Population -notin @('none','unknown','malformed','absent','wrong-case')){
        $chrome=Join-Path $context.values.LOCALAPPDATA 'Google\Chrome\User Data\Default'
        [void][IO.Directory]::CreateDirectory($chrome)
        if($Population -in @('legacy','mixed-legacy')){[void][IO.Directory]::CreateDirectory((Join-Path $chrome 'Extensions\hipekcciheckooncpjeljhnekcoolahp'))}
        if($Population -eq 'installed'){[void][IO.Directory]::CreateDirectory((Join-Path $chrome 'Extensions\dlaogejjiafeobgofajdlkkhjlignalk'))}
    }
    if($Population -notin @('none','legacy','installed')){
        $unknown=$Population -in @('unknown','malformed','absent','wrong-case','mixed-unknown')
        $firefox=Join-Path $context.values.APPDATA ('Mozilla\Firefox\Profiles\'+$(if($unknown){'r0016-unknown'}else{'r0016-known'}))
        [void][IO.Directory]::CreateDirectory($firefox)
        if($Population -ne 'absent'){
            $metadata=if($Population -in @('unknown','mixed-unknown')){'{"addons":42}'}elseif($Population -eq 'malformed'){'{invalid'}elseif($Population -eq 'wrong-case'){'{"ADDONS":[]}'}else{'{"addons":[]}'}
            Write-FixtureText (Join-Path $firefox 'extensions.json') $metadata
        }
    }
    $spec=[ordered]@{
        caseName=$Name;mode=$Mode;source=$FrozenSource;sourceSha256=$SourceHash;functions=$SourceFunctions;effectHelpers=$EffectHelpers
        events=(Join-Path $context.hostControl 'source-events.jsonl')
        bootstrapEvents=(Join-Path $context.hostControl 'bootstrap-events.jsonl')
        controlMethod=(Join-Path $context.hostControl 'method-control.ps1')
        readiness=(Join-Path $context.hostControl 'preview-ready');nonce=[guid]::NewGuid().ToString('N')
        result=(Join-Path $context.hostControl 'child-result.json')
        work=$work;retained=$retained;download=$download;presets=$presets;unpacked=$unpacked;cached=$cached;preset=$preset;profile=$fixtureProfile;compiler=$compiler
        call='';route='github';presetUrl='https://fixture.invalid/preset';omitInstallSource=$false;noOpen=$false;expectedSource=''
    }
    $context.values.R0016_METHOD_TARGET=Join-Path $context.hostControl 'method-must-not-run'
    $context.values.R0016_PREVIEW_SPEC=Join-Path $context.hostControl 'case.json'
    [pscustomobject]@{context=$context;spec=$spec;population=$Population}
}
function Run-PreviewCase($Case,[string]$Contract,[bool]$ExpectedFailure=$false){
    # Same host/preparation against the same subject, without evaluating product
    # source, makes independent startup changes visible before the product run.
    $mode=$Case.spec.mode
    $Case.spec.mode='baseline'
    Write-FixtureText $Case.context.values.R0016_PREVIEW_SPEC ($Case.spec|ConvertTo-Json -Depth 10)
    $baseline=Invoke-AcquisitionChild $Case.context $Driver 'host-baseline'
    $Case.spec.mode=$mode
    $evidencePaths=[pscustomobject]@{readiness=$Case.spec.readiness;result=$Case.spec.result;events=$Case.spec.events}
    try {
        $baselineReady=[IO.File]::Exists($Case.spec.readiness) -and [IO.File]::ReadAllText($Case.spec.readiness) -ceq $Case.spec.nonce
        if($baseline.preparation -cne 'COMPLETED' -or $baseline.timedOut -or $baseline.killGraceExpired -or
           -not $baseline.stdoutDrainCompleted -or -not $baseline.stderrDrainCompleted -or
           $null -eq $baseline.exit -or $baseline.exit -ne 0 -or -not $baselineReady -or -not [IO.File]::Exists($Case.spec.result)){
            throw 'Independent host baseline did not complete'
        }
        $baselineResult=[IO.File]::ReadAllText($Case.spec.result)|ConvertFrom-Json
        if($baselineResult.baseline -isnot [bool] -or -not $baselineResult.baseline -or
           $baselineResult.installerExecuted -isnot [bool] -or $baselineResult.installerExecuted){throw 'Baseline evidence does not prove an unevaluated installer'}
    } catch {
        return [pscustomobject]@{case=$Case.spec.caseName;pass=$false;classification='BOOTSTRAP_BLOCKED';error=('Independent baseline evidence: '+$_.Exception.Message);scope=$mode;baseline=$baseline;evidencePaths=$evidencePaths}
    }
    foreach($controlPath in @($Case.spec.readiness,$Case.spec.result,$Case.spec.events)){if([IO.File]::Exists($controlPath)){[IO.File]::Delete($controlPath)}}
    Write-FixtureText $Case.context.values.R0016_PREVIEW_SPEC ($Case.spec|ConvertTo-Json -Depth 10)
    $run=Invoke-AcquisitionChild $Case.context $Driver 'preview'
    $classification='PASS';$caseError=$null;$value=$null;$attempts=@()
    try {
        # Raw sidecars remain retained by path even when capture is incomplete.
        # Check capture before decoding them: truncated evidence is not a
        # product assertion and cannot credit a mutation kill.
        if($run.preparation -cne 'COMPLETED' -or $run.timedOut -or $run.killGraceExpired -or
           -not $run.stdoutDrainCompleted -or -not $run.stderrDrainCompleted -or $null -eq $run.exit){
            throw 'BOOTSTRAP: child capture did not complete with a terminal process result'
        }
        try {
            if(-not [IO.File]::Exists($Case.spec.readiness) -or [IO.File]::ReadAllText($Case.spec.readiness) -cne $Case.spec.nonce){throw 'guard readiness missing or wrong'}
            $attempts=@(if([IO.File]::Exists($Case.spec.events)){[IO.File]::ReadAllLines($Case.spec.events)|Where-Object{$_}|ForEach-Object{$_|ConvertFrom-Json}})
            foreach($attempt in $attempts){if($attempt.kind -isnot [string] -or $attempt.detail -isnot [string]){throw 'malformed source-event shape'}}
        } catch {throw ('BOOTSTRAP: unreadable or malformed source evidence: '+$_.Exception.Message)}
        if(@($attempts).Count){throw ('Installer reached effect/attempt boundary: '+(($attempts|ForEach-Object{$_.kind+' '+$_.detail}) -join '; '))}
        if($run.exit -ne 0){throw 'BOOTSTRAP: preview driver exited abnormally without a recorded source effect'}
        if(-not [IO.File]::Exists($Case.spec.result)){throw 'BOOTSTRAP: child did not produce a terminal result'}
        try {
            $value=[IO.File]::ReadAllText($Case.spec.result)|ConvertFrom-Json
            $required=@('guardEstablished','preparationError','events','nativeTypeBefore','nativeTypeAfter','stagingContextUnchanged','leaseDisposeCalls','returnCount','nullReturnCount','returned','reason','entryExit')
            $required+=@('compilerContextBefore','compilerContextAfter','compilerContextUnchanged','compilerContextReferenceUnchanged','compilerLeaseDisposeCalls','compilerNativeTypeBefore','compilerNativeTypeAfter')
            if($value -isnot [pscustomobject] -or @($required|Where-Object{$_ -cnotin @($value.PSObject.Properties.Name)}).Count){throw 'terminal evidence has an unsupported or incomplete shape'}
            foreach($field in @('guardEstablished','nativeTypeBefore','nativeTypeAfter','stagingContextUnchanged')){
                if($value.$field -isnot [bool]){throw ('terminal Boolean field has an unsupported shape: '+$field)}
            }
            foreach($field in @('leaseDisposeCalls','returnCount','nullReturnCount')){
                if(-not ($value.$field -is [int] -or $value.$field -is [long]) -or $value.$field -lt 0){throw ('terminal count has an unsupported shape: '+$field)}
            }
            if(-not ($value.entryExit -is [int] -or $value.entryExit -is [long]) -or
               $value.returned -isnot [array] -or $value.events -isnot [array] -or
               $value.returnCount -ne $value.returned.Count){throw 'terminal result collection or exit has an unsupported shape'}
            foreach($field in @('preparationError','reason')){
                if($null -ne $value.$field -and $value.$field -isnot [string]){throw ('terminal diagnostic has an unsupported shape: '+$field)}
            }
            foreach($attempt in $value.events){
                if($attempt.kind -isnot [string] -or $attempt.detail -isnot [string]){throw 'terminal source-event shape is malformed'}
            }
            if($value.compilerContextBefore -isnot [string] -or $value.compilerContextAfter -isnot [string] -or
               $value.compilerContextUnchanged -isnot [bool] -or $value.compilerContextReferenceUnchanged -isnot [bool] -or
               $value.compilerNativeTypeBefore -isnot [bool] -or $value.compilerNativeTypeAfter -isnot [bool] -or
               -not ($value.compilerLeaseDisposeCalls -is [int] -or $value.compilerLeaseDisposeCalls -is [long]) -or
               $value.compilerLeaseDisposeCalls -lt 0){throw 'compiler terminal evidence has an unsupported shape'}
        } catch {throw ('BOOTSTRAP: unreadable or malformed terminal evidence: '+$_.Exception.Message)}
        if(-not $value.guardEstablished -or $value.preparationError){throw ('BOOTSTRAP: '+$value.preparationError)}
        if(-not $run.subjectUnchanged){throw 'Installer changed subject USERPROFILE/TEMP names, attributes or bytes'}
        if(@($value.events).Count){throw ('Installer reached effect/attempt boundary: '+(($value.events|ForEach-Object{$_.kind+' '+$_.detail}) -join '; '))}
        if($value.nativeTypeAfter -and -not $value.nativeTypeBefore){throw 'Preview loaded the native staging API type'}
        if($value.compilerNativeTypeAfter -and -not $value.compilerNativeTypeBefore){throw 'Preview loaded the native compiler custody API type'}
        if($Case.spec.mode -eq 'helper'){
            if(-not $value.stagingContextUnchanged -or $value.leaseDisposeCalls){throw 'Preview changed admission/cleanup context or disposed a lease'}
            if(-not $value.compilerContextUnchanged -or -not $value.compilerContextReferenceUnchanged -or
               $value.compilerContextBefore -cne $value.compilerContextAfter -or $value.compilerLeaseDisposeCalls){throw 'Preview changed compiler custody context or disposed a compiler lease'}
            if($Contract -eq 'false'){
                if($value.returnCount -ne 1 -or $value.nullReturnCount -ne 0 -or -not ($value.returned[0] -is [bool]) -or $value.returned[0]){throw 'Suppressed copy did not return exactly Boolean false'}
            } else {
                if($value.returnCount -ne 0){throw 'Suppressed helper returned a usable success-stream value'}
                if($Contract -eq 'throw' -and ($value.reason -notmatch '(?i)preview|dry.run')){throw ('Helper did not report preview suppression: '+$value.reason)}
                if($Contract -eq 'empty' -and $value.reason){throw ('Suppressed no-op failed unexpectedly: '+$value.reason)}
            }
        } else {
            $text=$run.stdout+$run.stderr
            if(($value.entryExit -ne 0) -ne $ExpectedFailure){throw ('Wrong preview/refusal exit: '+$value.entryExit+' '+$value.reason)}
            if($text -match 'Select target numbers|Press Enter after|Choose \[1/2\]'){throw 'Preview requested interactive input'}
            if($text -match '\[OK\].*Copied|Validated manual-install files retained|Staging directory:'){throw 'Preview claimed an actual staged/copied artifact'}
            if(-not $ExpectedFailure){
                if($text -notmatch 'Preview only; no changes made' -or $text -notmatch 'replaces your current TablissNG dashboard'){throw 'Missing honest preview completion or replacement warning'}
                if($Case.spec.route -eq 'ask' -and $text -notmatch '(?i)source unresolved'){throw 'Preview resolved an unanswered source choice'}
            }
            if($Case.population -in @('unknown','malformed','absent','wrong-case','mixed-unknown')){
                if($text -notmatch '(?i)held|unknown'){throw 'Unknown discovery lacks explicit held/unknown diagnosis'}
                if($text -match 'Would prepare[^\r\n]*r0016-unknown'){throw 'Unknown target became an eligible plan'}
            }
            if($Case.population -eq 'mixed-unknown' -and $text -notmatch 'Would prepare Google Chrome'){throw 'Held target suppressed an eligible peer'}
            if($Case.spec.presetUrl -eq '' -and $text -notmatch 'No preset URL configured'){throw 'Missing preset was not reported honestly'}
            if($Case.spec.noOpen -and -not $ExpectedFailure){
                $automaticLines=@($text -split '[;\r\n]+' | Where-Object {
                    $_ -match '(?i)\bwould\b.*\b(open|launch)\b'
                })
                if($automaticLines.Count){throw 'NoOpen preview still promises automatic browser opens'}
                if($text -notmatch '(?i)NoOpen|NO_OPEN|open(?:ed)? manually|pages? yourself'){throw 'NoOpen preview does not explain manual browser opening'}
            }
            if(-not $ExpectedFailure -and $Case.spec.expectedSource -eq 'store'){
                foreach($url in @('https://chromewebstore.google.com/detail/tablissng/dlaogejjiafeobgofajdlkkhjlignalk','https://addons.mozilla.org/en-US/firefox/addon/tablissng/')){
                    if($text -notmatch ('(?m)^Would open official store: '+[regex]::Escape($url)+'\r?$')){throw 'Effective source did not select the resolved fixture store plan'}
                }
                if($text -match 'Install source unresolved'){throw 'Effective store source remained unresolved'}
            }
            if(-not $ExpectedFailure -and $Case.spec.expectedSource -eq 'github' -and $text -notmatch 'release/version/path unresolved'){throw 'Effective source did not select the GitHub plan'}
            if($Case.spec.omitInstallSource -and $ExpectedFailure){
                if($value.reason -notmatch '(?i)InstallSource|SALAH_INSTALL_SOURCE' -or $text -match 'Preview only; no changes made'){throw 'Invalid environment source lacked a specific unsuccessful option refusal'}
            }
        }
    } catch {
        $caseError=$_.Exception.Message
        $classification=if($caseError.StartsWith('BOOTSTRAP:')){'BOOTSTRAP_BLOCKED'}else{'PRODUCT_ASSERTION_FAILED'}
    }
    [pscustomobject]@{
        case=$Case.spec.caseName;pass=($classification -eq 'PASS');classification=$classification;error=$caseError
        scope=$Case.spec.mode;population=$Case.population;fixture=$Case.context.root
        commandHost=$HostExecutable;sourceSha256=$Case.spec.sourceSha256;observation=$value;attempts=$attempts;process=$run;baseline=$baseline;evidencePaths=$evidencePaths
    }
}
function New-PreviewSourceVariant([string]$Name,[string]$FunctionName,[string]$Kind){
    $original=[IO.File]::ReadAllText($FrozenSource)
    if($FunctionName -eq '<entry>'){
        $start=$sourceAst.EndBlock.Statements[0].Extent.StartOffset
        $prefix=if($Kind -eq 'eager'){
            'if ($DryRun) { [void][IO.Directory]::CreateDirectory((Join-Path $env:TEMP ''r0016-eager-staging'')) }'
        }else{
            'if ($DryRun) { $r0016Transport=New-Object Net.Sockets.TcpClient; try { $r0016Transport.Connect(''127.0.0.1'',9) } catch { } }'
        }
        $changed=$original.Substring(0,$start)+$prefix+[Environment]::NewLine+$original.Substring($start)
    }else{
        $fn=@($definitions|Where-Object{$_.Name -ceq $FunctionName})
        if($fn.Count -ne 1){throw ('BOOTSTRAP: mutation helper anchor missing: '+$FunctionName)}
        $guard=$fn[0].Body.EndBlock.Statements[0]
        if($guard -isnot [Management.Automation.Language.IfStatementAst] -or $guard.Clauses[0].Item1.Extent.Text -cne '$DryRun'){
            throw ('BOOTSTRAP: actual first DryRun guard changed: '+$FunctionName)
        }
        $replacement=switch($Kind){
            'cleanup' { '' }
            'cached-path' { 'if ($DryRun) { return $CachedPath }' }
            'copy-success' {
                if($guard.Extent.Text -notmatch [regex]::Escape('return $false')){throw 'BOOTSTRAP: copy return anchor changed'}
                $guard.Extent.Text.Replace('return $false','return $true')
            }
            'copy-array' {
                if($guard.Extent.Text -notmatch [regex]::Escape('return $false')){throw 'BOOTSTRAP: copy return anchor changed'}
                $guard.Extent.Text.Replace('return $false','return @($null,$false)')
            }
            'copy-effect' { 'if ($DryRun) { Set-Clipboard -Value $Text }'+[Environment]::NewLine+$guard.Extent.Text }
            'native-load' { 'if ($DryRun) { Add-Type -AssemblyName System.IO.Compression }'+[Environment]::NewLine+$guard.Extent.Text }
            default {throw 'BOOTSTRAP: unknown fixture variant'}
        }
        $changed=$original.Substring(0,$guard.Extent.StartOffset)+$replacement+$original.Substring($guard.Extent.EndOffset)
    }
    $root=Join-Path (Join-Path $FixtureRoot 'mutants') $Name
    [void][IO.Directory]::CreateDirectory($root)
    $file=Join-Path $root 'install.ps1'
    Write-FixtureText $file $changed
    $t=$null;$e=$null;$ast=[Management.Automation.Language.Parser]::ParseFile($file,[ref]$t,[ref]$e)
    if(@($e).Count){throw ('BOOTSTRAP: source mutant does not parse: '+$Name)}
    $functions=Join-Path $root 'actual-functions.ps1'
    Write-FixtureText $functions ((@($ast.EndBlock.Statements|Where-Object{$_ -is [Management.Automation.Language.FunctionDefinitionAst]})|ForEach-Object{$_.Extent.Text}) -join ([Environment]::NewLine+[Environment]::NewLine))
    $canonical=Join-Path (Split-Path $SourceFile -Parent) 'presets/salah-widget.tablissng.json'
    if([IO.File]::Exists($canonical)){
        [void][IO.Directory]::CreateDirectory((Join-Path $root 'presets'))
        [IO.File]::WriteAllBytes((Join-Path $root 'presets/salah-widget.tablissng.json'),[IO.File]::ReadAllBytes($canonical))
    }
    [pscustomobject]@{name=$Name;source=$file;functions=$functions;sha256=(Hash-File $file);baseSourceSha256=$SourceHash;kind=$Kind;function=$FunctionName}
}

$Results=New-Object 'System.Collections.Generic.List[object]'
$Variants=New-Object 'System.Collections.Generic.List[object]'
$guardResults=New-Object 'System.Collections.Generic.List[object]'
foreach($kind in @('outside-subject-method-write','direct-loopback-transport')){
    $listener=$null
    try{
        if($kind -eq 'direct-loopback-transport'){
            $listener=New-Object Net.Sockets.TcpListener ([Net.IPAddress]::Loopback),0
            $listener.Start()
            $port=$listener.LocalEndpoint.Port
        }
        foreach($deny in @($false,$true)){
            $case=New-PreviewCase ('control-'+$kind+'-'+$deny) 'control' 'none'
            $case.spec.denyControl=$deny
            $effectText=if($kind -eq 'outside-subject-method-write'){
                '[IO.File]::WriteAllText($env:R0016_METHOD_TARGET,''owned control effect'')'
            }else{
                'function Invoke-R0016DirectTransport { $client=New-Object Net.Sockets.TcpClient; try { $client.Connect(''127.0.0.1'','+$port+') } finally { $client.Dispose() } }; Invoke-R0016DirectTransport'
            }
            Write-FixtureText $case.spec.controlMethod $effectText
            Write-FixtureText $case.context.values.R0016_PREVIEW_SPEC ($case.spec|ConvertTo-Json -Depth 10)
            $run=Invoke-AcquisitionChild $case.context $Driver 'guard-control'
            $ready=[IO.File]::Exists($case.spec.readiness) -and [IO.File]::ReadAllText($case.spec.readiness) -ceq $case.spec.nonce
            $attempts=@(if([IO.File]::Exists($case.spec.events)){[IO.File]::ReadAllLines($case.spec.events)|Where-Object{$_}|ForEach-Object{$_|ConvertFrom-Json}})
            $executed=if($listener){$listener.Pending()}else{[IO.File]::Exists($case.context.values.R0016_METHOD_TARGET)}
            if($listener -and $executed){$connection=$listener.AcceptTcpClient();$connection.Dispose()}
            $expectedAttempt=if($kind -eq 'direct-loopback-transport'){'::Connect'}else{'::WriteAllText'}
            $captureComplete=$run.preparation -ceq 'COMPLETED' -and -not $run.timedOut -and -not $run.killGraceExpired -and
                $run.stdoutDrainCompleted -and $run.stderrDrainCompleted -and $null -ne $run.exit
            $pass=$ready -and $captureComplete -and ($executed -eq (-not $deny)) -and $(if($deny){@($attempts|Where-Object{$_.detail -match [regex]::Escape($expectedAttempt)}).Count -gt 0}else{$run.exit -eq 0 -and [IO.File]::Exists($case.spec.result)})
            $guardResults.Add([pscustomobject]@{case=('control-'+$kind+'-'+$deny);pass=$pass;classification=if($pass){'PASS'}else{'BOOTSTRAP_BLOCKED'};scope='fixture guard control; no installer executed';readiness=$ready;denied=$deny;effectExecuted=$executed;attempts=$attempts;process=$run})
        }
    } catch {
        $guardResults.Add([pscustomobject]@{case=('control-'+$kind);pass=$false;classification='BOOTSTRAP_BLOCKED';error=$_.Exception.Message;scope='fixture guard control; no installer executed'})
    } finally {if($listener){$listener.Stop()}}
}
foreach($row in $guardResults){$Results.Add($row)}
$guardProven=@($guardResults|Where-Object{-not $_.pass}).Count -eq 0 -and $guardResults.Count -eq 4
if($guardProven -and $Suite -in @('Helpers','All')){
    $helperCases=@(
        @('compiler-native-api-load','Initialize-CompilerNative','throw'),
        @('compiler-path-facts','Read-CompilerPathFacts $null $spec.compiler ''S-1-0-0'' ''''','throw'),
        @('compiler-directory-lease','Open-CompilerDirectoryLease $spec.compiler ''S-1-0-0'' ''S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464''','throw'),
        @('compiler-output-lease','Open-CompilerOutputLease $spec.compiler $CompilerContext','throw'),
        @('compiler-context-allocation','New-StagingCompilerContext','throw'),
        @('compiler-cleanup-compiled','Clear-StagingCompilerContext $CompilerContext $true','empty'),
        @('compiler-cleanup-failed','Clear-StagingCompilerContext $CompilerContext $false','empty'),
        @('compiler-invocation','Invoke-StagingCompiler ''deliberately invalid preview input'' $CompilerContext','throw'),
        @('native-api-load','Initialize-StagingNative','throw'),
        @('user-sid','Get-StagingUserSid','throw'),
        @('directory-lease','Open-StagingDirectoryLease $WorkRoot','throw'),
        @('path-info','Get-StagingPathInfo $CachedPath','throw'),
        @('private-directory','New-PrivateStagingDirectory (Join-Path $WorkRoot ''new-directory'')','throw'),
        @('private-file','New-PrivateStagingFile (Join-Path $WorkRoot ''new-file'')','throw'),
        @('trusted-parent','Get-TrustedStagingParent $WorkRoot','throw'),
        @('owned-path','Assert-OwnedStagingPath $CachedPath','throw'),
        @('owned-file','New-OwnedStagingFile $WorkRoot ''candidate.partial''','throw'),
        @('digest','Get-StagedFileDigest $CachedPath','throw'),
        @('owned-enumeration','Get-OwnedStagingFiles $WorkRoot','throw'),
        @('admitted-asset','Get-AdmittedArtifact $CachedPath ''asset''','throw'),
        @('admitted-unpacked','Get-AdmittedArtifact $CachedPath ''unpacked''','throw'),
        @('admitted-preset','Get-AdmittedArtifact $PresetPath ''preset''','throw'),
        @('initialize','Initialize-Staging','throw'),
        @('cleanup','Clear-OwnedScratch','empty'),
        @('begin-artifact','New-ArtifactRecord ''asset'' ''fixture''','throw'),
        @('publication','Publish-OwnedFile $Record $DownloadRoot ''published.zip''','throw'),
        @('archive-validation','Test-ExtensionArchive $CachedPath','throw'),
        @('archive-extraction','Test-ExtensionArchive $CachedPath $spec.unpacked','throw'),
        @('metadata-cache','Get-LatestRelease','throw'),
        @('selector','Select-TablissNgAsset ''chromium''','throw'),
        @('download-cache','Download-Asset $Asset','throw'),
        @('unpacked-cache','Expand-ChromiumAsset $CachedPath','throw'),
        @('preset-cache','Download-Preset','empty'),
        @('copy-false','Copy-Text ''fixture''','false'),
        @('open','Open-TargetUrl $Target ''https://fixture.invalid/manual''','empty'),
        @('install-ask','Install-TablissNG $Target','empty'),
        @('import','Show-ImportInstructions $Target $PresetPath','empty')
    )
    foreach($row in $helperCases){
        $case=New-PreviewCase ('helper-'+$row[0]) 'helper'
        $case.spec.call=$row[1]
        $Results.Add((Run-PreviewCase $case $row[2]))
    }
}
if($guardProven -and $Suite -in @('Wrapper','All')){
    foreach($route in @('github','store','ask')){
        $case=New-PreviewCase ('wrapper-'+$route) 'wrapper'
        $case.spec.route=$route
        $Results.Add((Run-PreviewCase $case 'entry'))
    }
    foreach($population in @('installed','mixed-legacy','mixed-unknown','none','legacy','unknown','malformed','absent','wrong-case')){
        $case=New-PreviewCase ('wrapper-'+$population) 'wrapper' $population
        $Results.Add((Run-PreviewCase $case 'entry' ($population -in @('none','legacy','unknown','malformed','absent','wrong-case'))))
    }
    $case=New-PreviewCase 'wrapper-missing-preset' 'wrapper';$case.spec.presetUrl=''
    $Results.Add((Run-PreviewCase $case 'entry'))
    $case=New-PreviewCase 'wrapper-invalid-option' 'wrapper';$case.spec.route='invalid'
    $Results.Add((Run-PreviewCase $case 'entry' $true))
    foreach($sourceCase in @(
        @{name='invalid-environment-source';environment='invalid';route='github';omit=$true;failure=$true},
        @{name='empty-environment-default-source';environment='';route='github';omit=$true;failure=$false},
        @{name='valid-environment-store-source';environment='store';route='store';omit=$true;failure=$false},
        @{name='explicit-source-overrides-invalid-environment';environment='invalid';route='store';omit=$false;failure=$false}
    )){
        $case=New-PreviewCase ('wrapper-'+$sourceCase.name) 'wrapper'
        $case.context.values.SALAH_INSTALL_SOURCE=$sourceCase.environment
        $case.spec.route=$sourceCase.route;$case.spec.expectedSource=$sourceCase.route;$case.spec.omitInstallSource=$sourceCase.omit
        $Results.Add((Run-PreviewCase $case 'entry' $sourceCase.failure))
    }
    foreach($route in @('github','store')){
        $case=New-PreviewCase ('wrapper-noopen-'+$route) 'wrapper'
        $case.spec.route=$route;$case.spec.noOpen=$true
        $Results.Add((Run-PreviewCase $case 'entry'))
    }
}
if($guardProven -and $Suite -in @('Mutants','All')){
    $mutantRows=@(
        @('eager-staging','<entry>','eager','wrapper','','entry'),
        @('cleanup-in-preview','Clear-OwnedScratch','cleanup','helper','Clear-OwnedScratch','empty'),
        @('cached-path-return','Download-Asset','cached-path','helper','Download-Asset $Asset','throw'),
        @('copy-success-when-suppressed','Copy-Text','copy-success','helper','Copy-Text ''fixture''','false'),
        @('copy-null-array-truthiness','Copy-Text','copy-array','helper','Copy-Text ''fixture''','false'),
        @('clipboard-attempt-during-preview','Copy-Text','copy-effect','helper','Copy-Text ''fixture''','false'),
        @('native-api-load-before-guard','Initialize-StagingNative','native-load','helper','Initialize-StagingNative','throw'),
        @('swallowed-direct-transport','<entry>','transport','wrapper','','entry')
    )
    foreach($row in $mutantRows){
        try{
            $variant=New-PreviewSourceVariant $row[0] $row[1] $row[2]
            $Variants.Add($variant)
            $healthy=New-PreviewCase ('matched-'+$row[0]) $row[3]
            $healthy.spec.call=$row[4]
            $healthyRun=Run-PreviewCase $healthy $row[5]
            $changed=New-PreviewCase ('mutant-'+$row[0]) $row[3]
            $changed.spec.call=$row[4]
            $changed.spec.source=$variant.source;$changed.spec.functions=$variant.functions;$changed.spec.sourceSha256=$variant.sha256
            $changedRun=Run-PreviewCase $changed $row[5]
            $pass=$healthyRun.pass -and $changedRun.classification -eq 'PRODUCT_ASSERTION_FAILED'
            if($row[2] -eq 'copy-effect'){
                $pass=$pass -and $changedRun.error -like '*command Set-Clipboard*' -and
                    @($changedRun.attempts|Where-Object{$_.kind -eq 'source-call' -and $_.detail -like '*command Set-Clipboard*'}).Count -gt 0
            }
            $classification=if($healthyRun.classification -eq 'BOOTSTRAP_BLOCKED' -or $changedRun.classification -eq 'BOOTSTRAP_BLOCKED'){'BOOTSTRAP_BLOCKED'}elseif($pass){'PASS'}else{'PRODUCT_ASSERTION_FAILED'}
            $Results.Add([pscustomobject]@{
                case=('mutant-discriminator-'+$row[0]);pass=$pass;classification=$classification
                scope='matched actual-source preview discriminator; native normal survival is a separate gate'
                variant=$variant;healthy=$healthyRun;mutant=$changedRun;nativeNoOpenSurvival='NOT_RUN_BY_WRAPPER'
            })
        }catch{
            $Results.Add([pscustomobject]@{case=('mutant-discriminator-'+$row[0]);pass=$false;classification='BOOTSTRAP_BLOCKED';error=$_.Exception.Message})
        }
    }
}
$unchanged=(Hash-File $SourceFile) -ceq $SourceHash
if(-not $unchanged){$Results.Add([pscustomobject]@{case='input source remained stable';pass=$false;classification='BOOTSTRAP_BLOCKED';error='Input source changed during the run'})}
$testUnchanged=(Hash-File $PSCommandPath) -ceq $TestHashAtStart
$libraryUnchanged=(Hash-File $FixtureLibrary) -ceq $LibraryHashAtStart
if(-not $testUnchanged -or -not $libraryUnchanged){$Results.Add([pscustomobject]@{case='fixture code remained stable';pass=$false;classification='BOOTSTRAP_BLOCKED';error='Fixture source or imported library changed during the run'})}
$report=[pscustomobject][ordered]@{
    schema='r0016-preview-powershell-core.v1';pass=(@($Results|Where-Object{-not $_.pass}).Count -eq 0)
    source=$SourceFile;sourceSha256=$SourceHash;sourceUnchanged=$unchanged;frozenSource=$FrozenSource
    testSha256=$TestHashAtStart;testUnchanged=$testUnchanged;fixtureLibrarySha256=$LibraryHashAtStart;fixtureLibraryUnchanged=$libraryUnchanged
    host=$PSVersionTable.PSVersion.ToString();nativeWindows=$NativeWindows;fixture=$FixtureRoot
    helperInventory=$EffectHelpers;results=$Results.ToArray();mutants=$Variants.ToArray()
    independentHardContainment='NOT_ACQUIRED'
    scopeLimits=@(
        'Actual helpers and whole-source wrapper entry; not fresh installer -File.',
        'Method/cmdlet source-call denial is proved in separate positive/negative control children before product execution; it is not an OS sandbox.',
        'Debugger Stop terminates its child pipeline; a post-readiness recorded source attempt remains a product assertion failure even without a final child result.',
        'Source static method/cmdlet inventory is explicit; arbitrary hostile dynamic code is not claimed contained.',
        'Known calls, denying guards, source guards and snapshots are distinct scopes.',
        'Native normal/NoOpen and complete -File use the maintained native entry harness, not this wrapper.',
        'Mutant preview rejection is scoped evidence; native normal/NoOpen survival must be established separately for each retained variant.',
        'Source-triggered Add-Type/compiler writes belong to installer effects, not independent host startup.',
        'Linux PowerShell results cannot qualify Windows 5.1 or Windows 7.6.6.'
    )
}
$json=$report|ConvertTo-Json -Depth 16
Write-FixtureText (Join-Path $FixtureRoot 'results.json') $json
Write-FixtureText (Join-Path $FixtureRoot 'mutants.json') ($Variants.ToArray()|ConvertTo-Json -Depth 5)
[Console]::WriteLine($json)
if(@($Results|Where-Object{$_.classification -eq 'BOOTSTRAP_BLOCKED'}).Count){exit 2}
if(-not $report.pass){exit 1}
exit 0
