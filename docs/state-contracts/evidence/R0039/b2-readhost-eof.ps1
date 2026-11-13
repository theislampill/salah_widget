# R0039 (issue 106) discriminator B2 primitive: what Read-Host does on this host when input is
# non-interactive or redirected and then ends. Two consecutive prompts, as in the installer (target
# selection at install.ps1 L1670, then the hand-off acknowledgement at L1595). No installer code runs.
$ErrorActionPreference = 'Stop'
$rows = @()
foreach ($i in 1..3) {
    try { $v = Read-Host ("R0039 prompt " + $i); $rows += [pscustomobject]@{ prompt = $i; outcome = 'returned'; isNull = ($null -eq $v); value = $v } }
    catch { $rows += [pscustomobject]@{ prompt = $i; outcome = 'threw'; isNull = $null; value = ($_.Exception.GetType().FullName + ': ' + $_.Exception.Message) } }
}
[pscustomobject]@{ host = $PSVersionTable.PSVersion.ToString(); edition = $PSVersionTable.PSEdition; inputRedirected = [Console]::IsInputRedirected; rows = $rows } | ConvertTo-Json -Depth 4
