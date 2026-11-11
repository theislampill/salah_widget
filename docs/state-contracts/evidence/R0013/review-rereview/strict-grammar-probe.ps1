param([string]$SourceFile,[string]$Corpus)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($SourceFile,[ref]$tokens,[ref]$errors)
if(@($errors).Count){throw 'Source parser failure'}
$definitions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-StrictJson'},$true))
if($definitions.Count -ne 1){throw 'Strict validator definition not unique'}
. ([scriptblock]::Create($definitions[0].Extent.Text))
$cases=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($Corpus))
$rows=@(foreach($case in $cases){
 $actual=Test-StrictJson $case.text
 [pscustomobject]@{case=$case.name;expected=$case.expected;actual=$actual;pass=($actual -is [bool] -and $actual -eq $case.expected)}
})
[pscustomobject]@{reviewer='/root/r0013_review';host=$PSVersionTable.PSVersion.ToString();source=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();results=$rows}|ConvertTo-Json -Depth 5
