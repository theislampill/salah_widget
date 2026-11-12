param(
    [string]$SourceFile = (Join-Path (Split-Path $PSScriptRoot -Parent) 'install.ps1'),
    [string]$BaselineFile,
    [ValidateSet('All','Equivalence','Performance')][string]$Suite = 'All',
    [string]$ReportPath
)
$ErrorActionPreference='Stop'
$rows=New-Object 'System.Collections.Generic.List[object]'
$samples=New-Object 'System.Collections.Generic.List[object]'
$utf8=New-Object Text.UTF8Encoding $false
function Assert($Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
function Hash-Text([string]$Text) {
    $h=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
    finally { $h.Dispose() }
}
function Validator-Text([string]$Path) {
    $t=$null; $e=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile([IO.Path]::GetFullPath($Path),[ref]$t,[ref]$e)
    Assert (@($e).Count -eq 0) 'Installer source did not parse'
    $defs=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Test-StrictJson'},$true))
    Assert ($defs.Count -eq 1) 'Expected exactly one production strict validator'
    return $defs[0].Extent.Text
}
function Observe([string]$Name,[scriptblock]$Body) {
    try { $detail=& $Body; $rows.Add([pscustomobject]@{case=$Name;pass=$true;observation=$detail}) }
    catch { $rows.Add([pscustomobject]@{case=$Name;pass=$false;error=$_.Exception.Message}) }
}
function Result([string]$Function,[string]$Document) {
    $value=@(& $Function $Document)
    Assert ($value.Count -eq 1 -and $value[0] -is [bool]) 'Validator must return exactly one Boolean'
    return $value[0]
}
$source=Validator-Text $SourceFile
. ([scriptblock]::Create($source))
$baseline=$null
if ($BaselineFile) {
    $baseline=Validator-Text $BaselineFile
    Assert ((Hash-Text $baseline) -ceq '71a9501b677c226da98a06a9ba89e7c3a4c1f7f41f3a2e7fd066eedb0387c31c') 'R0013 original validator identity changed'
    . ([scriptblock]::Create($baseline.Replace('function Test-StrictJson(', 'function Test-R0013BaselineJson(')))
}

if ($Suite -ne 'Performance') {
    $cases=@(
        @('empty object','{}',$true), @('empty array','[]',$true),
        @('root string','"text"',$true), @('root number','-1.25e+2',$true),
        @('root true','true',$true), @('root false','false',$true), @('root null','null',$true),
        @('JSON whitespace',(" `t`r`n{}`n`t "),$true),
        @('nested containers','{"a":[{},[],{"b":[true,false,null]}],"c":{"a":0}}',$true),
        @('every string escape','["\"","\\","\/","\b","\f","\n","\r","\t","\u0041"]',$true),
        @('fractions and exponents','[0,-0,1,-2,1.25,1e2,1E+2,-1.5e-2]',$true),
        @('same key in separate objects','[{"a":1},{"a":2}]',$true),
        @('escaped surrogate spelling retained','["\ud800","\udc00","\ud83d\ude00"]',$true),
        @('empty document','',$false), @('whitespace only'," `r`n`t ",$false),
        @('gap before first token','@{}',$false), @('gap between tokens','{"a"@:1}',$false),
        @('gap between array values','[true,@false]',$false),
        @('trailing garbage after root','{}@',$false), @('trailing garbage after space','[] @',$false),
        @('second root','{}[]',$false), @('unterminated string','"text',$false),
        @('unterminated object','{"a":1',$false), @('unterminated array','[1',$false),
        @('mismatched close','[}',$false), @('object trailing comma','{"a":1,}',$false),
        @('array trailing comma','[1,]',$false), @('missing colon','{"a" 1}',$false),
        @('missing object comma','{"a":1 "b":2}',$false), @('missing array comma','[1 2]',$false),
        @('missing value','{"a":}',$false), @('bare key','{a:1}',$false),
        @('single quoted key',"{'a':1}",$false), @('internal comment','{/* comment */ "a":1}',$false),
        @('trailing comment','{} /* comment */',$false), @('leading zero','01',$false),
        @('leading plus','+1',$false), @('leading decimal point','.1',$false),
        @('trailing decimal point','1.',$false), @('missing exponent','1e+',$false),
        @('non JSON NaN','NaN',$false), @('non JSON Infinity','Infinity',$false),
        @('bad string escape','"\x41"',$false), @('short unicode escape','"\u12"',$false),
        @('literal control in string',('"a'+[char]10+'b"'),$false),
        @('non JSON whitespace',([string][char]0x00a0+'{}'),$false),
        @('duplicate key','{"name":1,"name":2}',$false),
        @('escaped duplicate key','{"name":1,"na\u006de":2}',$false),
        @('case insensitive duplicate key','{"Name":1,"name":2}',$false),
        @('escaped case insensitive duplicate key','{"Name":1,"\u006eame":2}',$false),
        @('escaped slash duplicate key','{"a/b":1,"a\/b":2}',$false)
    )
    foreach ($row in $cases) {
        $case=$row
        Observe ('strict lexer '+$case[0]) {
            $actual=Result 'Test-StrictJson' $case[1]
            Assert ($actual -eq $case[2]) ('Wrong strict result for '+$case[0])
            $old=$null
            if ($baseline) { $old=Result 'Test-R0013BaselineJson' $case[1]; Assert ($actual -eq $old) 'Original R0013 language changed' }
            [pscustomobject]@{expected=$case[2];actual=$actual;baseline=$old;inputSha256=(Hash-Text $case[1])}
        }
    }
}

# Match Fable's metadata-shaped reproducer: lots of short tokens and decoded
# object keys. A single long string would hide the per-token regression.
function New-Document([int]$Kilobytes) {
    $sb=New-Object System.Text.StringBuilder
    [void]$sb.Append('{"schemaVersion":36,"addons":['); $n=0
    while ($sb.Length -lt ($Kilobytes*1024)) {
        if ($n -gt 0) { [void]$sb.Append(',') }
        [void]$sb.Append('{"id":"addon'+$n+'@example.invalid","version":"1.2.'+$n+'","type":"extension","active":true,"userDisabled":false,"path":"extensions/addon'+$n+'.xpi","defaultLocale":{"name":"Example add-on '+$n+'","description":"synthetic entry"},"targetApplications":[{"id":"toolkit@example.invalid","minVersion":"1.0","maxVersion":"*"}]}')
        $n++
    }
    [void]$sb.Append(']}'); return $sb.ToString()
}
if ($Suite -ne 'Equivalence') {
    Observe 'linear metadata lexer budgets and scaling' {
        $warm=Result 'Test-StrictJson' (New-Document 20)
        Assert $warm 'Warm-up metadata rejected'
        $documents=@{}
        foreach ($kb in @(200,400,512,1024)) { $documents[$kb]=New-Document $kb }
        # Interleave sizes across three rounds. Retain every sample; do not
        # discard a slow run. Each must meet the 5-second hosted-runner budget.
        foreach ($round in @(1,2,3)) {
            foreach ($kb in @(200,400,512,1024)) {
                $doc=$documents[$kb]
                $watch=[Diagnostics.Stopwatch]::StartNew()
                $actual=Result 'Test-StrictJson' $doc
                $watch.Stop()
                $samples.Add([pscustomobject]@{round=$round;kilobytes=$kb;characters=$doc.Length;inputSha256=(Hash-Text $doc);seconds=$watch.Elapsed.TotalSeconds;valid=$actual})
                Assert $actual ('Valid '+$kb+'KB metadata rejected')
                Assert ($watch.Elapsed.TotalSeconds -le 5.0) ('Performance budget exceeded at '+$kb+'KB: '+$watch.Elapsed.TotalSeconds+' seconds (limit 5)')
            }
        }
        $median=@{}
        foreach ($kb in @(200,400,512,1024)) { $times=@($samples|Where-Object {$_.kilobytes -eq $kb}|ForEach-Object {$_.seconds}|Sort-Object); $median[$kb]=$times[1] }
        $smallRatio=$median[400]/$median[200]; $largeRatio=$median[1024]/$median[512]
        Assert ($smallRatio -le 3.0 -and $largeRatio -le 3.0) ('Nonlinear scaling: 400/200='+$smallRatio+'; 1024/512='+$largeRatio+' (limit 3)')
        [pscustomobject]@{budgetSeconds=5.0;maximumRatio=3.0;ratio400over200=$smallRatio;ratio1024over512=$largeRatio;median200=$median[200];median400=$median[400];median512=$median[512];median1024=$median[1024]}
    }
}
$report=[pscustomobject]@{
    schema='r0013-json-lexer-v1';host=$PSVersionTable.PSVersion.ToString();edition=$PSVersionTable.PSEdition
    platform=[Environment]::OSVersion.Platform.ToString();runtime=[Environment]::Version.ToString()
    source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
    functionSha256=(Hash-Text $source);baselineFunctionSha256=$(if($baseline){Hash-Text $baseline}else{$null})
    fixture=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    suite=$Suite;results=@($rows.ToArray());samples=@($samples.ToArray())
}
$json=$report|ConvertTo-Json -Depth 12
if ($ReportPath) { [IO.File]::WriteAllText([IO.Path]::GetFullPath($ReportPath),$json,$utf8) }
$json
if (@($rows|Where-Object {-not $_.pass}).Count) { exit 1 }
