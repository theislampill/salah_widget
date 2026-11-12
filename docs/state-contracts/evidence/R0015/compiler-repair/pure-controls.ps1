param([Parameter(Mandatory=$true)][string]$SourceFile,[Parameter(Mandatory=$true)][string]$BaselineFile)
$ErrorActionPreference='Stop'
$Utf8=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$Utf8
$tokens=$null; $parseErrors=$null
$tree=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$parseErrors)
$oldTokens=$null; $oldErrors=$null
$oldTree=[Management.Automation.Language.Parser]::ParseFile($BaselineFile,[ref]$oldTokens,[ref]$oldErrors)
if ($parseErrors.Count -or $oldErrors.Count) { throw 'Source parse failed.' }
function Get-ActualFunction($Tree,[string]$Name) {
    $found=@($Tree.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $Name},$true))
    if ($found.Count -ne 1) { throw ('Function not unique: '+$Name) }
    return $found[0]
}
function Get-ActualCondition($Function,[string]$Message) {
    $found=@($Function.Body.FindAll({param($node) $node -is [Management.Automation.Language.IfStatementAst] -and $node.Extent.Text.Contains($Message)},$true) | Where-Object {$_.Clauses.Count -eq 1 -and $_.Clauses[0].Item2.Extent.Text -match '^\{\s*throw '})
    if ($found.Count -ne 1) { throw ('Condition not unique: '+$Message) }
    return $found[0].Clauses[0].Item1.Extent.Text
}
$results=[Collections.Generic.List[object]]::new()
function Record([string]$Name,[bool]$Pass,$Observation) { $results.Add([pscustomobject]@{case=$Name;pass=$Pass;observation=$Observation}) }

# Only declare these actual function definitions. No installer initialization,
# native API, compiler, child process, or production cleanup is executed here.
foreach ($name in @('Read-CompilerPathFacts','Open-CompilerOutputLease','Invoke-StagingCompiler')) {
    . ([scriptblock]::Create((Get-ActualFunction $tree $name).Extent.Text))
}
$script:DryRun=$true
$script:CompilerScratch=[pscustomobject]@{Status='unchanged';InvocationStarted=$false}
$before=$script:CompilerScratch | ConvertTo-Json -Compress
foreach ($name in @('Read-CompilerPathFacts','Open-CompilerOutputLease','Invoke-StagingCompiler')) {
    $refused=$false; $reason=$null
    try { & $name | Out-Null } catch { $reason=$_.Exception.Message; $refused=$reason.StartsWith('Offline preview does not ',[StringComparison]::Ordinal) }
    Record ($name+' guards before native/effect access') ($refused -and ($script:CompilerScratch | ConvertTo-Json -Compress) -ceq $before) @{reason=$reason}
}

$cleanup=Get-ActualCondition (Get-ActualFunction $tree 'Clear-StagingCompilerContext') 'Compiler output custody could not be proved.'
$oldCleanup=Get-ActualCondition (Get-ActualFunction $oldTree 'Clear-StagingCompilerContext') 'Compiler output custody could not be proved.'
$openOutput=Get-ActualCondition (Get-ActualFunction $tree 'Open-CompilerOutputLease') 'Compiler output custody could not be proved.'
$Context=[pscustomobject]@{Sid='S-1-5-21-1-2-3-1000';DefaultOwnerSid='S-1-5-32-544'}
$cases=@(
    @('subject-owned regular output',$Context.Sid,$true,$false,1,$false),
    @('captured Administrators owner regular output',$Context.DefaultOwnerSid,$true,$false,1,$false),
    @('foreign owner is refused','S-1-5-21-1-2-3-2000',$true,$false,1,$true),
    @('foreign writable default-owner file is refused',$Context.DefaultOwnerSid,$false,$false,1,$true),
    @('foreign writable subject file is refused',$Context.Sid,$false,$false,1,$true),
    @('hardlinked output is refused',$Context.DefaultOwnerSid,$true,$false,2,$true),
    @('captured owner directory may be cleaned',$Context.DefaultOwnerSid,$true,$true,1,$false)
)
foreach ($case in $cases) {
    $facts=[pscustomobject]@{Owner=$case[1];WriteRestricted=$case[2];TrustedParent=($case[1] -ceq $Context.Sid -and $case[2]);Directory=$case[3];Links=$case[4]}
    $observed=& ([scriptblock]::Create($cleanup)); $oldObserved=& ([scriptblock]::Create($oldCleanup))
    $fileRefused=& ([scriptblock]::Create($openOutput))
    Record ('actual cleanup predicate: '+$case[0]) ($observed -eq $case[5]) @{refused=$observed;baselineRefused=$oldObserved;nativeExecuted=$false}
    Record ('actual file-admission predicate: '+$case[0]) ($fileRefused -eq ($case[5] -or $case[3])) @{refused=$fileRefused;nativeExecuted=$false}
}

# Evaluate the actual full-write condition, without constructing a Windows ACL
# or replacing it with a policy implementation. Inputs are plain scalar values.
$readFunction=Get-ActualFunction $tree 'Read-CompilerPathFacts'
$writeIf=@($readFunction.Body.FindAll({param($node) $node -is [Management.Automation.Language.IfStatementAst] -and $node.Extent.Text.Contains('0x500d0156')},$true))
if ($writeIf.Count -ne 1) { throw 'Actual full-write condition not unique.' }
$writeCondition=$writeIf[0].Clauses[0].Item1.Extent.Text
$Sid=$Context.Sid; $allowed=$true; $inheritOnly=$false; $principal='S-1-5-21-1-2-3-2000'
foreach ($mask in @(2,4,0x100,0x10000,0x40000,0x80000)) {
    $refused=& ([scriptblock]::Create($writeCondition))
    Record ('actual full write mask rejects foreign bit '+$mask) ($refused -eq $true) @{mask=$mask;refused=$refused}
}
$mask=1; $refused=& ([scriptblock]::Create($writeCondition))
Record 'actual full write mask permits harmless foreign read' ($refused -eq $false) @{mask=$mask;refused=$refused}
$mask=0x1f01ff; $principal=$Sid; $refused=& ([scriptblock]::Create($writeCondition))
Record 'actual full write mask preserves subject full access' ($refused -eq $false) @{mask=$mask;refused=$refused}

$defaultOwner=Get-ActualCondition (Get-ActualFunction $tree 'New-StagingCompilerContext') 'Unsupported compiler default owner.'
foreach ($defaultOwnerSid in @($Sid,'S-1-5-32-544','S-1-5-21-1-2-3-2000')) {
    $refused=& ([scriptblock]::Create($defaultOwner))
    Record ('actual default-owner admission '+$defaultOwnerSid) ($refused -eq ($defaultOwnerSid -cnotin @($Sid,'S-1-5-32-544'))) @{refused=$refused}
}
$report=[ordered]@{
    schema='r0015-compiler-repair.pure-controls.v1'
    sourceSha256=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
    baselineSha256=(Get-FileHash -LiteralPath $BaselineFile -Algorithm SHA256).Hash.ToLowerInvariant()
    testSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    host=$PSVersionTable.PSVersion.ToString();nativeWindows=$false;installerExecuted=$false;nativeApisExecuted=$false;compilerExecuted=$false
    productQualification=$false;nativeQualification=$false
    scope='Source AST parse, three actual early DryRun guards, and actual scalar predicate expressions only. No main entry, native handles, ACL creation, compilation, or assembly loading.'
    pass=(@($results | Where-Object {-not $_.pass}).Count -eq 0);results=@($results.ToArray())
}
$report | ConvertTo-Json -Depth 10
if (-not $report.pass) { exit 1 }
