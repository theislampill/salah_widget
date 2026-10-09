param(
    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string]$LeaseId
)
# Root acquires and records the capacity-one lease before this serial candidate-only batch.
$clockDatePython = 'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe'
$clockDateNode = 'C:\Users\theis\AppData\Local\OpenAI\Codex\bin\node.exe'
$clockDateCandidate = 'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009\candidates\pr43-r1r2-04'
$clockDateDriver = Join-Path $PSScriptRoot 'rlgwo_date_disclosure_check.py'
$clockDateOutput = 'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009\evidence\PR43-review\R2-final-font-04'
$clockDateBrowsers = @{
    chromium = 'C:\Users\theis\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'
    firefox = 'C:\Users\theis\AppData\Local\ms-playwright\firefox-1522\firefox\firefox.exe'
}
foreach ($clockDateEngine in @('chromium','firefox')) {
    $clockDateEngineOutput = Join-Path $clockDateOutput ($clockDateEngine + '-green')
    if (Test-Path -LiteralPath $clockDateEngineOutput) { throw "Preserve existing receipts: $clockDateEngineOutput" }
    $env:SALAH_BROWSER = $clockDateEngine
    $env:SALAH_BROWSER_EXECUTABLE = $clockDateBrowsers[$clockDateEngine]
    & $clockDatePython -B -X utf8 $clockDateDriver `
        --root $clockDateCandidate --engine $clockDateEngine --node $clockDateNode `
        --cases font `
        --variants missing,delayed-css-forenoon,delayed-bytes-forenoon,split-face-forenoon,loaded-forenoon,permanent-bytes-forenoon,warm-cache-forenoon,loaded-sunrise,loaded-maghrib `
        --expected-source-sha256 67e2ff84eb1e7422bfc390f98b641c8e3f93f76a77400401681be10676eb8d3d `
        --output $clockDateEngineOutput --execute --lease-id $LeaseId
    if ($LASTEXITCODE -ne 0) { throw "Font native batch returned $LASTEXITCODE for $clockDateEngine. Preserve receipts and inspect before any retry." }
}
