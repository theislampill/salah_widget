# Effect-free probe: evaluates the exact PowerShell selection-parsing statements of install.ps1
# (the two lines that build $wanted and $selected) against fixture targets. No installer top level,
# no network, no file writes. Usage: pwsh -NoProfile -File ps-selection-tokens.ps1 -SourceFile <install.ps1>
param([Parameter(Mandatory=$true)][string]$SourceFile)
$ErrorActionPreference = 'Stop'
$lines = [IO.File]::ReadAllLines($SourceFile, [Text.Encoding]::UTF8)
$wantedLine = @($lines | Where-Object { $_ -match '^\s*\$wanted = \$selection -split ","' })
$selectedLine = @($lines | Where-Object { $_ -match '^\s*\$selected = @\(\$targets \| Where-Object \{ \$wanted -contains \$_\.Index \}\)' })
if ($wantedLine.Count -ne 1 -or $selectedLine.Count -ne 1) { throw 'Selection statements drifted' }
$code = $wantedLine[0].Trim() + "`n" + $selectedLine[0].Trim()
$targets = @(1..3 | ForEach-Object { [pscustomobject]@{ Index = $_ } })
foreach ($selection in @('1,2', '1,2O', '1,,2', ',1', '1,99', '99', 'x', '2,2')) {
    $wanted = $null; $selected = $null
    . ([scriptblock]::Create($code))
    [pscustomobject]@{ input = $selection; selectedIndexes = (@($selected | ForEach-Object Index) -join ','); selectedCount = @($selected).Count }
}
