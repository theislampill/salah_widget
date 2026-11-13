# R0039 (issue 106) discriminator B1: is SalahInstaller.StageNative reused within one PowerShell
# session after the installer source changed? Disposable experiment, not a product change.
#
# Inputs come from environment variables so the same text runs under -File and under iex:
#   R0039_B1_SOURCE  absolute path of install.ps1 (read only; never executed as a whole)
#   R0039_B1_MODE    'file' (definitions dot-sourced) or 'iex' (definitions passed to Invoke-Expression)
# The caller sets TEMP/TMP to a disposable fixture directory. Only installer FUNCTION definitions are
# loaded (no installer top level: no discovery, prompt, network, clipboard or browser). Two copies of
# the source are made in memory: S1 and S2 differ only in one constant added to the StageNative C#
# class. The probe calls the real Initialize-StagingNative of S1, then of S2, in the same process,
# and reports which constant the loaded type exposes after each call.
#   R0039_B1_COMPILER 'real' (the installer's own compiler custody) or 'fixture' (see below)
#   R0039_B1_ORDER   'S1,S2' (default) or a single load such as 'S2' (positive control: the constant is observable)
# Compiler 'fixture': the R0015 compiler-custody boundary (New-StagingCompilerContext, Invoke-StagingCompiler,
# Clear-StagingCompilerContext) refuses a host whose TEMP ancestors grant foreign writers (as on the
# executing workstation). Those three functions are then replaced by a fixture that compiles the exact
# C# text handed to Invoke-StagingCompiler with Add-Type in a fresh directory under the caller's TEMP and
# counts the invocations. Initialize-StagingNative itself (the type check at L341 that decides reuse) is
# the real function. The custody boundary is not under test here; it is covered by the R0015 suites.
$ErrorActionPreference = 'Stop'
$source = $env:R0039_B1_SOURCE; $mode = $env:R0039_B1_MODE
$compilerMode = if ($env:R0039_B1_COMPILER) { $env:R0039_B1_COMPILER } else { 'real' }
$order = if ($env:R0039_B1_ORDER) { $env:R0039_B1_ORDER.Split(',') } else { @('S1','S2') }
if ($mode -cnotin @('file','iex')) { throw 'R0039_B1_MODE must be file or iex' }
if ($compilerMode -cnotin @('real','fixture')) { throw 'R0039_B1_COMPILER must be real or fixture' }
$fixtureCompiler = @'
function New-StagingCompilerContext {
    $p = Join-Path $env:R0039_B1_TEMP_ROOT ('ctx-' + [guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($p)
    $script:CompilerScratch = [pscustomobject]@{ Id = [guid]::NewGuid().ToString('N'); Status = 'owned'; Path = $p }
    return $script:CompilerScratch
}
function Invoke-StagingCompiler([string]$NativeSource, $Context) {
    $script:R0039CompilerInvocations++
    $script:R0039LastCompiledTag = ([regex]::Match($NativeSource, 'R0039Probe = "(S\d)"')).Groups[1].Value
    Add-Type -TypeDefinition $NativeSource -Language CSharp
}
function Clear-StagingCompilerContext($Context, [bool]$Compiled) { $Context.Status = if ($Compiled) { 'closed' } else { 'retained-compilation-failed' } }
'@
$script:R0039CompilerInvocations = 0; $script:R0039LastCompiledTag = $null
$env:R0039_B1_TEMP_ROOT = [IO.Path]::GetTempPath()
$text = [IO.File]::ReadAllText($source, [Text.Encoding]::UTF8)
$anchor = '  public static class StageNative {'
if (([regex]::Matches($text, [regex]::Escape($anchor))).Count -ne 1) { throw 'StageNative anchor drifted' }
function New-Variant([string]$Tag) { $text.Replace($anchor, $anchor + "`n    public const string R0039Probe = `"$Tag`";") }
function Get-Definitions([string]$Variant) {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($Variant, [ref]$tokens, [ref]$errors)
    if (@($errors).Count) { throw 'Variant does not parse' }
    @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false) | ForEach-Object { $_.Extent.Text })
}
$DryRun = $false
$rows = @()
foreach ($tag in $order) {
    $defs = @(Get-Definitions (New-Variant $tag))
    if ($compilerMode -eq 'fixture') { $defs += $fixtureCompiler }
    if ($mode -eq 'file') { foreach ($d in $defs) { . ([scriptblock]::Create($d)) } }
    else { Invoke-Expression ($defs -join "`n`n") }
    $before = 'SalahInstaller.StageNative' -as [type]
    $contextBefore = if ($script:CompilerScratch) { $script:CompilerScratch.Id } else { $null }
    $invocationsBefore = $script:R0039CompilerInvocations
    $err = $null
    try { Initialize-StagingNative } catch { $err = $_.Exception.Message }
    $type = 'SalahInstaller.StageNative' -as [type]
    $observed = if ($type) { $type.GetField('R0039Probe').GetValue($null) } else { $null }
    $rows += [pscustomobject]@{
        load = $tag; typeLoadedBefore = [bool]$before; error = $err; observedConstant = $observed
        assembly = if ($type) { $type.Assembly.FullName } else { $null }
        compilerContextAllocated = ($script:CompilerScratch -and $script:CompilerScratch.Id -ne $contextBefore)
        compilerContextStatus = if ($script:CompilerScratch) { $script:CompilerScratch.Status } else { $null }
        compilerInvoked = ($script:R0039CompilerInvocations -gt $invocationsBefore)
        lastCompiledTag = $script:R0039LastCompiledTag
    }
}
[pscustomobject]@{
    host = $PSVersionTable.PSVersion.ToString(); edition = $PSVersionTable.PSEdition; mode = $mode
    compiler = $compilerMode; order = ($order -join ',')
    sourceSha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    rows = $rows
    outcome = if ($rows.Count -eq 1) { 'single-load control: observed ' + $rows[0].observedConstant }
              elseif ($rows[0].observedConstant -eq 'S1' -and $rows[1].observedConstant -eq 'S1' -and -not $rows[1].error) { 'reuse-confirmed: second call observed S1' }
              elseif ($rows[1].observedConstant -eq 'S2') { 'no-reuse: second call observed S2' }
              else { 'inconclusive' }
} | ConvertTo-Json -Depth 5
