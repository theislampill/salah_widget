param([string]$OriginalFile,[string]$CorrectedFile)
$ErrorActionPreference='Stop'
function Inspect-ProbeVariables([string]$Path) {
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors)
    if($errors.Count){throw 'Probe parse failed'}
    $readonly=@(Get-Variable | Where-Object{($_.Options -band ([Management.Automation.ScopedItemOptions]::ReadOnly -bor [Management.Automation.ScopedItemOptions]::Constant)) -ne 0}|ForEach-Object{$_.Name})
    $assignments=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left -is [Management.Automation.Language.VariableExpressionAst]},$true))
    $collisions=@($assignments|Where-Object{$_.Left.VariablePath.UserPath -in $readonly}|ForEach-Object{[pscustomobject]@{variable=$_.Left.VariablePath.UserPath;line=$_.Extent.StartLineNumber;text=$_.Extent.Text}})
    [pscustomobject]@{ast=$ast;collisions=$collisions;assignments=$assignments;sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$original=Inspect-ProbeVariables $OriginalFile
$corrected=Inspect-ProbeVariables $CorrectedFile
$originalStatement=@($original.assignments|Where-Object{$_.Left.VariablePath.UserPath -ceq 'home'})
$correctedStatement=@($corrected.assignments|Where-Object{$_.Left.VariablePath.UserPath -ceq 'subjectHome'})
if($originalStatement.Count -ne 1 -or $correctedStatement.Count -ne 1){throw 'Actual assignment anchor drift'}
$case='/fixture/case'
$before=$HOME
$red=$null
try{. ([scriptblock]::Create($originalStatement[0].Extent.Text))}catch{$red=[pscustomobject]@{id=$_.FullyQualifiedErrorId;message=$_.Exception.Message}}
. ([scriptblock]::Create($correctedStatement[0].Extent.Text))
$pass=$original.collisions.Count -eq 1 -and $red.id -ceq 'VariableNotWritable' -and $subjectHome -ceq '/fixture/case/home' -and $HOME -ceq $before -and $corrected.collisions.Count -eq 0
$report=[pscustomobject]@{schema='r0015-probe-reserved-variable-control.v1';host=$PSVersionTable.PSVersion.ToString();nativeWindows=$false;fullProbeExecuted=$false;installerExecuted=$false;assignmentOnly=$true;originalSha256=$original.sha256;correctedSha256=$corrected.sha256;oldReservedAssignments=$original.collisions;newReservedAssignments=$corrected.collisions;red=$red;green=($subjectHome -ceq '/fixture/case/home');automaticHomeUnchanged=($HOME -ceq $before);pass=$pass}
[Console]::WriteLine(($report|ConvertTo-Json -Depth 6))
if(-not $pass){exit 1}
