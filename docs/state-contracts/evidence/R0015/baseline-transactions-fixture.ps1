param(
    [Parameter(Mandatory=$true)][string]$SourceFile,
    [Parameter(Mandatory=$true)][string]$PresetFile,
    [string]$FixtureParent = [IO.Path]::GetTempPath()
)

# R0015 focused transaction controls. Import actual production functions, not main.
# Only transport, clipboard, browser launch, prompts and host rendering are spies.
# Linux PowerShell is supplemental; it does not qualify Windows ACL/NTFS behavior.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$script:results = @()
$script:caseEvents = @()
$script:caseNotes = [ordered]@{}
$script:hostMessages = @()
$script:downloadPlan = @()
$script:downloadIndex = 0
$script:releaseFixture = $null
$script:expectedPreset = $null
$script:fixtureRoot = $null
$script:caseRoot = $null
$script:sourceText = [IO.File]::ReadAllText($SourceFile, [Text.Encoding]::UTF8)
$script:canonicalPresetText = [IO.File]::ReadAllText($PresetFile, [Text.Encoding]::UTF8)
$script:utf8 = New-Object Text.UTF8Encoding $false
$script:oldTemp = $env:TEMP
$script:oldUserProfile = $env:USERPROFILE

function Assert-Case($Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Get-BytesHash([byte[]]$Bytes) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}

function Read-TestJson([string]$Text) {
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        return ConvertFrom-Json -InputObject $Text -DateKind String
    }
    return ConvertFrom-Json -InputObject $Text
}

function Assert-FixturePath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = $script:fixtureRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    Assert-Case ($full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) ('Fixture boundary violation: ' + $full)
}

function Get-FixtureSnapshot {
    $rows = @()
    foreach ($item in @(Get-ChildItem -LiteralPath $script:caseRoot -Force -Recurse | Sort-Object FullName)) {
        $relative = $item.FullName.Substring($script:caseRoot.Length)
        if ($item.PSIsContainer) { $rows += ('D:' + $relative) }
        else { $rows += ('F:' + $relative + ':' + (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash) }
    }
    return $rows -join "`n"
}

function New-TestZip($Entries) {
    $stream = New-Object IO.MemoryStream
    $zip = New-Object IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create, $true)
    try {
        foreach ($entry in $Entries) {
            $member = $zip.CreateEntry([string]$entry.name)
            if ($entry.PSObject.Properties['attributes']) { $member.ExternalAttributes = [int]$entry.attributes }
            $writer = $member.Open()
            try {
                $bytes = $script:utf8.GetBytes([string]$entry.text)
                $writer.Write($bytes, 0, $bytes.Length)
            } finally { $writer.Dispose() }
        }
    } finally { $zip.Dispose() }
    try { return ,$stream.ToArray() } finally { $stream.Dispose() }
}

function New-TestAsset([int]$Id, [byte[]]$Bytes, [string]$Suffix='a') {
    return [pscustomobject]@{
        id=$Id; name='tabliss-chromium.zip'; size=$Bytes.Length;
        browser_download_url=('https://fixture.invalid/assets/' + $Suffix + '/tabliss-chromium.zip');
        digest=('sha256:' + (Get-BytesHash $Bytes)); content_type='application/zip'
    }
}

function Set-DownloadPlan($Rows) {
    $script:downloadPlan = @($Rows)
    $script:downloadIndex = 0
}

function New-DownloadStep([byte[]]$Bytes, [string]$Failure='') {
    return [pscustomobject]@{bytes=$Bytes; failure=$Failure}
}

function New-Case([string]$Name, [byte[]]$Bytes) {
    $script:caseEvents = @()
    $script:hostMessages = @()
    $script:caseNotes = [ordered]@{}
    $script:caseRoot = Join-Path $script:fixtureRoot $Name
    [void][IO.Directory]::CreateDirectory($script:caseRoot)
    $tempParent = Join-Path $script:caseRoot 'temp'
    $profileParent = Join-Path $script:caseRoot 'profile'
    [void][IO.Directory]::CreateDirectory($tempParent)
    [void][IO.Directory]::CreateDirectory($profileParent)
    $env:TEMP = $tempParent
    $env:USERPROFILE = $profileParent
    $script:DryRun = $false
    $script:NoOpen = $false
    $script:InstallSource = 'github'
    $script:TablissNgRepo = 'fixture/upstream'
    $script:PresetUrl = 'https://fixture.invalid/preset.json'
    $script:WidgetHash = ''
    $script:LatestRelease = $null
    # Baseline has these globals. Later Initialize-Staging owns fresh attempt state.
    $script:WorkRoot = Join-Path $tempParent 'SalahWidgetInstaller'
    $script:DownloadRoot = Join-Path $script:WorkRoot 'downloads'
    $script:PresetRoot = Join-Path $script:WorkRoot 'presets'
    $asset = New-TestAsset 101 $Bytes
    $script:releaseFixture = [pscustomobject]@{id=201; tag_name='v-fixture'; assets=@($asset)}
    Set-DownloadPlan @((New-DownloadStep $Bytes))
    $null = Initialize-Staging
    Assert-FixturePath $script:WorkRoot
    $script:caseNotes.root = $script:caseRoot
    return $asset
}

function Invoke-Case([string]$Name, [scriptblock]$Body) {
    $script:caseEvents = @()
    $script:hostMessages = @()
    $script:caseNotes = [ordered]@{}
    $passed = $false
    $failure = $null
    try { & $Body; $passed = $true }
    catch { $failure = $_.Exception.Message }
    $script:results += [pscustomobject]@{
        case=$Name; pass_=$passed; pass=$passed; status=$(if ($passed) {'PASS'} else {'FAIL'});
        error=$failure; observations=$script:caseNotes; events=@($script:caseEvents); messages=@($script:hostMessages)
    }
}

function Invoke-Captured([scriptblock]$Body) {
    $items = @()
    $failure = $null
    try { $items = @(& $Body) } catch { $failure = $_.Exception.Message }
    return [pscustomobject]@{items=$items; error=$failure}
}

function Assert-OnePath($Items, [string]$Description) {
    Assert-Case (@($Items).Count -eq 1 -and $Items[0] -is [string] -and -not [string]::IsNullOrWhiteSpace($Items[0])) ($Description + ' did not return one clean string path')
    Assert-FixturePath $Items[0]
    Assert-Case ([IO.File]::Exists($Items[0]) -or [IO.Directory]::Exists($Items[0])) ($Description + ' returned a missing path')
    return [string]$Items[0]
}

function Assert-NoReadyPath($Observation, [string]$Description) {
    Assert-Case (@($Observation.items | Where-Object { $_ -is [string] -and -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) ($Description + ' returned a usable-looking path')
}

try {
    $fileTokens=$null; $fileErrors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($SourceFile, [ref]$fileTokens, [ref]$fileErrors)
    $tokens=$null; $parseErrors=$null
    $sourceAst=[Management.Automation.Language.Parser]::ParseInput($script:sourceText, [ref]$tokens, [ref]$parseErrors)
    if (@($parseErrors).Count) { throw 'SETUP: exact source functions did not parse.' }
    # Do not execute discovery, profiles, terminal main or top-level native effects.
    foreach ($definition in @($sourceAst.EndBlock.Statements | Where-Object { $_ -is [Management.Automation.Language.FunctionDefinitionAst] })) {
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    # Host-output capture preserves real Write-Ok/Write-Warn wrappers and detects
    # an accidental success-stream diagnostic returned by a production helper.
    function Write-Host {
        param([Parameter(Position=0, ValueFromRemainingArguments=$true)][object[]]$Object,
              [object]$ForegroundColor, [object]$BackgroundColor, [string]$Separator=' ', [switch]$NoNewline)
        $script:hostMessages += (($Object | ForEach-Object {[string]$_}) -join $Separator)
    }
    function Invoke-RestMethod {
        param($Uri, $Headers)
        $script:caseEvents += [pscustomobject]@{effect='metadata'; uri=[string]$Uri}
        return $script:releaseFixture
    }
    function Invoke-WebRequest {
        param($Uri, [string]$OutFile, [switch]$UseBasicParsing, $Headers)
        Assert-FixturePath $OutFile
        $script:caseEvents += [pscustomobject]@{effect='download'; uri=[string]$Uri; path=$OutFile; ordinal=$script:downloadIndex}
        Assert-Case ($script:downloadIndex -lt $script:downloadPlan.Count) 'SETUP: unplanned acquisition reached the controlled transport.'
        $step = $script:downloadPlan[$script:downloadIndex]
        $script:downloadIndex++
        if ($null -ne $step.bytes) { [IO.File]::WriteAllBytes($OutFile, [byte[]]$step.bytes) }
        if ($step.failure) { throw [IO.IOException]::new([string]$step.failure) }
    }
    function Copy-Text([string]$Text) {
        $script:caseEvents += [pscustomobject]@{effect='copy'; value=$Text}
        return $true
    }
    function Open-TargetUrl($Target, [string]$Url) {
        $script:caseEvents += [pscustomobject]@{effect='open'; value=$Url}
    }
    function Read-Host([string]$Prompt) {
        $script:caseEvents += [pscustomobject]@{effect='prompt'; value=$Prompt}
        return ''
    }

    $fixtureName = 'r0015-ps-' + [guid]::NewGuid().ToString('N') + '-' + [char]0x0635
    $script:fixtureRoot = Join-Path ([IO.Path]::GetFullPath($FixtureParent)) $fixtureName
    [void][IO.Directory]::CreateDirectory($script:fixtureRoot)
    $manifest = '{"manifest_version":3,"name":"Fixture extension","version":"1.0","description":"R0015 disposable control"}'
    $unicodeMember = 'extension/assets/space ' + [char]0x0635 + '.txt'
    $goodBytes = New-TestZip @(
        [pscustomobject]@{name='extension/manifest.json'; text=$manifest},
        [pscustomobject]@{name=$unicodeMember; text=('payload ' + [char]0x0635)}
    )
    $secondBytes = New-TestZip @(
        [pscustomobject]@{name='extension/manifest.json'; text=$manifest.Replace('1.0', '2.0')},
        [pscustomobject]@{name=$unicodeMember; text='second payload'}
    )
    $script:targetFixture = [pscustomobject]@{
        Index=1; Browser='Disposable Chromium'; Family='chromium'; ProfileName='Fixture'; ProfilePath='fixture-only'; ExePath=$null;
        DiscoveryStatus='known-neither'; DiscoveryReason='Disposable complete negative observation';
        DiscoverySource='fixture-only'; DiscoveryEvidence='chromium-directory-and-preferences';
        HasLegacyTabliss=$false; HasTablissNG=$false; NewMatches=@(); OldMatches=@();
        Config=[pscustomobject]@{StoreUrl='https://fixture.invalid/store'; ManagerUrl='fixture://extensions'; NewTabUrl='fixture://newtab'}
    }

    Invoke-Case 'exact-file parser and ASCII source' {
        Assert-Case (@($fileErrors).Count -eq 0) ('Native ParseFile errors: ' + (@($fileErrors | ForEach-Object {$_.Message}) -join '; '))
        Assert-Case (-not @([IO.File]::ReadAllBytes($SourceFile) | Where-Object {$_ -gt 127}).Count) 'Non-ASCII production source byte.'
    }

    Invoke-Case 'healthy actual download and manual Chromium caller' {
        $asset = New-Case 'healthy-caller' $goodBytes
        $direct = @(Download-Asset $asset)
        $path = Assert-OnePath $direct 'Download-Asset'
        Assert-Case ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $goodBytes)) 'Downloaded bytes differ from the controlled valid archive.'
        $null = Install-TablissNG $script:targetFixture
        $copies = @($script:caseEvents | Where-Object {$_.effect -eq 'copy'})
        Assert-Case ($copies.Count -eq 1) 'Actual caller did not copy exactly one admitted unpacked path.'
        $bundle = $copies[0].value
        Assert-FixturePath $bundle
        Assert-Case ([IO.File]::Exists((Join-Path $bundle 'manifest.json'))) 'Actual caller handed off an unreadable manifest.'
        Assert-Case ([IO.File]::Exists((Join-Path $bundle ('assets/space ' + [char]0x0635 + '.txt')))) 'Healthy nested Unicode/spaced member was lost.'
        Assert-Case (@($script:caseEvents | Where-Object {$_.effect -eq 'download'}).Count -eq 1) 'Same-attempt actual caller refetched an unchanged validated asset.'
        Assert-Case (@($script:caseEvents | Where-Object {$_.effect -eq 'open' -and $_.value -eq 'fixture://extensions'}).Count -eq 1) 'Actual caller did not reach the manual extension manager.'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'open' -and $_.value -like '*store'}).Count) 'Healthy caller silently fell back to the store.'
        $script:caseNotes.archive=$path; $script:caseNotes.bundle=$bundle
    }

    Invoke-Case 'partial download is not a ready cache hit and healthy retry recovers' {
        $asset = New-Case 'partial-download' $goodBytes
        Set-DownloadPlan @(
            (New-DownloadStep $script:utf8.GetBytes('PK partial') 'fixture transport interrupted'),
            (New-DownloadStep $null 'fixture second transport refused'),
            (New-DownloadStep $goodBytes)
        )
        $first = Invoke-Captured { Download-Asset $asset }
        $second = Invoke-Captured { Download-Asset $asset }
        $script:caseNotes.first=$first; $script:caseNotes.second=$second
        Assert-NoReadyPath $first 'Interrupted acquisition'
        Assert-NoReadyPath $second 'Retry after interrupted acquisition'
        Assert-Case ($script:downloadIndex -eq 2) 'Retry bypassed acquisition using unvalidated partial bytes.'
        $recovered = Assert-OnePath @(Download-Asset $asset) 'Healthy retry'
        Assert-Case ((Get-FileHash -LiteralPath $recovered -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $goodBytes)) 'Healthy retry did not publish complete bytes.'
    }

    Invoke-Case 'same filename with changed source identity must reacquire' {
        $asset = New-Case 'source-identity' $goodBytes
        $first = Assert-OnePath @(Download-Asset $asset) 'Initial source'
        $otherAsset = New-TestAsset 102 $secondBytes 'b'
        Set-DownloadPlan @((New-DownloadStep $secondBytes))
        $other = Assert-OnePath @(Download-Asset $otherAsset) 'Changed source'
        $script:caseNotes.first=$first; $script:caseNotes.other=$other
        Assert-Case ($script:downloadIndex -eq 1) 'Changed asset id/URL reused an old filename hit.'
        Assert-Case ((Get-FileHash -LiteralPath $other -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $secondBytes)) 'Changed source was bound to predecessor bytes.'
        Assert-Case ((Get-FileHash -LiteralPath $first -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $goodBytes)) 'Changed source overwrote the predecessor archive.'
    }

    Invoke-Case 'altered admitted bytes cannot be reused by filename' {
        $asset = New-Case 'altered-bytes' $goodBytes
        $path = Assert-OnePath @(Download-Asset $asset) 'Initial source'
        [IO.File]::WriteAllText($path, 'fixture externally altered bytes', $script:utf8)
        Set-DownloadPlan @((New-DownloadStep $goodBytes))
        $result = Invoke-Captured { Download-Asset $asset }
        $script:caseNotes.reuse=$result
        if ($result.items.Count -gt 0) {
            $ready = Assert-OnePath $result.items 'Readback after alteration'
            Assert-Case ((Get-FileHash -LiteralPath $ready -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $goodBytes)) 'Altered bytes inherited readiness.'
            Assert-Case ($script:downloadIndex -eq 1) 'No actual reacquisition preceded restored readiness.'
        } else { Assert-Case (-not [string]::IsNullOrWhiteSpace($result.error)) 'Alteration had neither rejection nor valid reacquisition.' }
    }

    Invoke-Case 'failed replacement preserves already handed-off bundle' {
        $asset = New-Case 'failed-replacement' $goodBytes
        $path = Assert-OnePath @(Download-Asset $asset) 'Initial source'
        $old = Assert-OnePath @(Expand-ChromiumAsset $path) 'Initial extraction'
        $sentinel = Join-Path $old 'browser-still-using.txt'
        [IO.File]::WriteAllText($sentinel, 'old bundle remains needed', $script:utf8)
        $oldManifest = (Get-FileHash -LiteralPath (Join-Path $old 'manifest.json') -Algorithm SHA256).Hash
        [IO.File]::WriteAllText($path, 'bad candidate', $script:utf8)
        $replacement = Invoke-Captured { Expand-ChromiumAsset $path }
        $script:caseNotes.oldBundle=$old; $script:caseNotes.replacement=$replacement
        Assert-NoReadyPath $replacement 'Failed extraction'
        Assert-Case ([IO.File]::Exists($sentinel)) 'Failed replacement deleted the previously handed-off bundle.'
        Assert-Case ([IO.File]::ReadAllText($sentinel, [Text.Encoding]::UTF8) -ceq 'old bundle remains needed') 'Failed replacement changed the old sentinel.'
        Assert-Case ((Get-FileHash -LiteralPath (Join-Path $old 'manifest.json') -Algorithm SHA256).Hash -ceq $oldManifest) 'Failed replacement changed the old manifest.'
    }

    Invoke-Case 'successful restaging preserves already handed-off bundle' {
        $asset = New-Case 'successful-replacement' $goodBytes
        $path = Assert-OnePath @(Download-Asset $asset) 'Initial source'
        $old = Assert-OnePath @(Expand-ChromiumAsset $path) 'Initial extraction'
        $sentinel = Join-Path $old 'browser-still-using.txt'
        [IO.File]::WriteAllText($sentinel, 'do not infer release from Enter', $script:utf8)
        $next = Assert-OnePath @(Expand-ChromiumAsset $path) 'Successful restaging'
        $script:caseNotes.oldBundle=$old; $script:caseNotes.nextBundle=$next
        Assert-Case ([IO.File]::Exists($sentinel)) 'Successful restaging deleted the previously handed-off bundle.'
        Assert-Case ([IO.File]::ReadAllText($sentinel, [Text.Encoding]::UTF8) -ceq 'do not infer release from Enter') 'Successful restaging changed the predecessor sentinel.'
        Assert-Case ([IO.File]::Exists((Join-Path $next 'manifest.json'))) 'New handoff has no readable manifest.'
    }

    Invoke-Case 'unsafe late ZIP has no ready path or remaining member files' {
        $unsafeBytes = New-TestZip @(
            [pscustomobject]@{name='extension/manifest.json'; text=$manifest},
            [pscustomobject]@{name='extension/early-marker.txt'; text='must not extract before late path refusal'},
            [pscustomobject]@{name='../late-escape.txt'; text='must never escape'}
        )
        $asset = New-Case 'zip-preflight' $unsafeBytes
        $observation = Invoke-Captured {
            $candidate = Download-Asset $asset
            if ($candidate) { Expand-ChromiumAsset $candidate }
        }
        $script:caseNotes.result=$observation
        Assert-NoReadyPath $observation 'Unsafe late archive member'
        $markers = @(Get-ChildItem -LiteralPath $script:caseRoot -Recurse -File | Where-Object {$_.Name -in @('early-marker.txt','late-escape.txt')})
        Assert-Case ($markers.Count -eq 0) 'Unsafe archive left an earlier or escaping member in the fixture.'
        $script:caseNotes.limit='Final snapshot does not prove no transient writes or complete member preflight; native effect controls remain required.'
    }

    Invoke-Case 'actual install caller refuses a filename-only malformed manifest' {
        $badManifestBytes = New-TestZip @([pscustomobject]@{name='extension/manifest.json'; text='this is not JSON'})
        $null = New-Case 'manifest-shape' $badManifestBytes
        $null = Install-TablissNG $script:targetFixture
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Actual install caller copied a directory whose manifest is malformed.'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'open' -and $_.value -eq 'fixture://extensions'}).Count) 'Malformed manifest reached manual Load unpacked handoff.'
        Assert-Case (@($script:caseEvents | Where-Object {$_.effect -eq 'open' -and $_.value -eq 'https://fixture.invalid/store'}).Count -eq 1) 'Failed archive did not reach truthful store fallback.'
    }

    Invoke-Case 'malformed preset has no ready path or actual import handoff' {
        $null = New-Case 'preset-malformed' $goodBytes
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes('{broken fixture JSON')))
        $observed = Invoke-Captured { Download-Preset }
        $script:caseNotes.preset=$observed
        $candidate = if ($observed.items.Count) {[string]$observed.items[0]} else {$null}
        $null = Show-ImportInstructions $script:targetFixture $candidate
        Assert-NoReadyPath $observed 'Malformed preset'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Malformed preset reached real import-copy caller.'
        Assert-Case (-not @($script:hostMessages | Where-Object {$_ -match 'Select the preset JSON file above'}).Count) 'Unavailable preset is described as a selectable file above.'
    }

    Invoke-Case 'valid JSON with missing canonical widget is not import-ready' {
        $null = New-Case 'preset-missing-target' $goodBytes
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes('{"version":3,"note":"ordinary JSON is not an admitted widget preset"}')))
        $observed = Invoke-Captured { Download-Preset }
        $script:caseNotes.preset=$observed
        $candidate = if ($observed.items.Count) {[string]$observed.items[0]} else {$null}
        $null = Show-ImportInstructions $script:targetFixture $candidate
        Assert-NoReadyPath $observed 'Preset missing the intended iframe payload'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Wrong-shape JSON reached import-copy caller.'
    }

    Invoke-Case 'targeted configured preset preserves unrelated strings and Unicode' {
        $null = New-Case 'preset-target-and-encoding' $goodBytes
        $preset = Read-TestJson $script:canonicalPresetText
        $note = 'unrelated local=1 literal ' + [char]0x0635 + ' ' + [char]0x03A9
        $timestamp = '2026-10-08T02:03:04.125+03:00'
        $preset | Add-Member -NotePropertyName 'fixtureNote' -NotePropertyValue $note
        $preset | Add-Member -NotePropertyName 'fixtureTimestamp' -NotePropertyValue $timestamp
        $preset | Add-Member -NotePropertyName 'fixtureOptional' -NotePropertyValue ([pscustomobject]@{nullValue=$null; literal='local=1'; enabled=$false; count=7})
        $inputText = ConvertTo-Json -InputObject $preset -Depth 50
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes($inputText)))
        $script:WidgetHash = 'lat=24.7&lon=46.7&label=%24%28Get-Process%29%20%D8%B5%20%26%3Ctag%3E'
        $path = Assert-OnePath @(Download-Preset) 'Configured preset'
        $actual = Read-TestJson ([IO.File]::ReadAllText($path, [Text.Encoding]::UTF8))
        $payload = [string]$actual.'data/orpul7IDXSSP'.input
        $match = [regex]::Match($payload, '\bsrc\s*=\s*"([^"]*)"')
        Assert-Case $match.Success 'Configured intended iframe has no quoted src.'
        $src = [Net.WebUtility]::HtmlDecode($match.Groups[1].Value)
        Assert-Case ($src -ceq ('https://theislampill.github.io/salah_widget/#' + $script:WidgetHash)) 'The intended iframe fragment changed encoded literal meaning.'
        Assert-Case ($actual.fixtureNote -ceq $note) 'Configuration rewrite changed an unrelated local=1/Unicode string.'
        Assert-Case ($actual.fixtureTimestamp -is [string] -and $actual.fixtureTimestamp -ceq $timestamp) 'JSON rewrite changed an unrelated timestamp string.'
        Assert-Case ($actual.fixtureOptional.literal -ceq 'local=1' -and $actual.fixtureOptional.enabled -eq $false -and $actual.fixtureOptional.count -eq 7 -and $null -eq $actual.fixtureOptional.nullValue) 'JSON rewrite changed unrelated optional semantics.'
        Assert-Case ($payload -match 'width:325px;height:530px' -and $payload -match 'no-referrer' -and $payload -match 'geolocation' -and $payload -match 'Prayer Times') 'Configured iframe lost unrelated supported attributes.'
        $null = Show-ImportInstructions $script:targetFixture $path
        Assert-Case (@($script:caseEvents | Where-Object {$_.effect -eq 'copy' -and $_.value -ceq $path}).Count -eq 1) 'Valid configured preset did not reach the actual import caller once.'
        $script:caseNotes.readyPath=$path; $script:caseNotes.src=$src
    }

    Invoke-Case 'unadmitted existing preset path cannot enter import caller' {
        $null = New-Case 'preset-unadmitted' $goodBytes
        $foreign = Join-Path $script:caseRoot 'outside-admission.json'
        [IO.File]::WriteAllText($foreign, $script:canonicalPresetText, $script:utf8)
        $observation = Invoke-Captured { Show-ImportInstructions $script:targetFixture $foreign }
        $script:caseNotes.import=$observation
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'An unadmitted existing JSON path reached the import clipboard.'
    }

    Invoke-Case 'case-colliding JSON keys are explicitly unsupported and never import-ready' {
        $null = New-Case 'preset-case-collision' $goodBytes
        $inputText = $script:canonicalPresetText.Insert($script:canonicalPresetText.IndexOf('{') + 1, '"fixtureKeys":{"Keep":"first","keep":"second"},')
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes($inputText)))
        $script:WidgetHash = 'lat=24.7&lon=46.7'
        $observed = Invoke-Captured { Download-Preset }
        $script:caseNotes.preset=$observed
        $candidate = if ($observed.items.Count) {[string]$observed.items[0]} else {$null}
        $null = Show-ImportInstructions $script:targetFixture $candidate
        Assert-NoReadyPath $observed 'Unsupported case-colliding JSON object'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Unsupported JSON keys reached import-copy caller.'
    }

    Invoke-Case 'large unrelated integer is preserved exactly or refused truthfully' {
        $null = New-Case 'preset-large-integer' $goodBytes
        $inputText = $script:canonicalPresetText.Insert($script:canonicalPresetText.IndexOf('{') + 1, '"fixtureInteger":9007199254740993,')
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes($inputText)))
        $script:WidgetHash = 'lat=24.7&lon=46.7'
        $observed = Invoke-Captured { Download-Preset }
        $script:caseNotes.preset=$observed
        if ($observed.items.Count) {
            $path = Assert-OnePath $observed.items 'Integer-preserving configured preset'
            $raw = [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
            Assert-Case ([regex]::IsMatch($raw, '"fixtureInteger"\s*:\s*9007199254740993\s*[,}]')) 'The unrelated integer lost precision or changed numeric representation beyond this supported contract.'
            $null = Show-ImportInstructions $script:targetFixture $path
            Assert-Case (@($script:caseEvents | Where-Object {$_.effect -eq 'copy' -and $_.value -ceq $path}).Count -eq 1) 'Preserved valid integer preset did not reach actual import caller.'
        } else {
            Assert-Case ($observed.error -or @($script:hostMessages | Where-Object {$_ -match '\[WARN\]|\[ERROR\]'}).Count) 'Unsupported integer was silently discarded without a truthful rejection.'
            $null = Show-ImportInstructions $script:targetFixture $null
            Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Refused integer preset still reached clipboard.'
        }
    }

    Invoke-Case 'ambiguous canonical iframe payload has no ready import path' {
        $null = New-Case 'preset-ambiguous-iframe' $goodBytes
        $inputObject = Read-TestJson $script:canonicalPresetText
        $inputObject.'data/orpul7IDXSSP'.input = $inputObject.'data/orpul7IDXSSP'.input + $inputObject.'data/orpul7IDXSSP'.input
        $inputText = ConvertTo-Json -InputObject $inputObject -Depth 50
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes($inputText)))
        $script:WidgetHash = 'lat=24.7&lon=46.7'
        $observed = Invoke-Captured { Download-Preset }
        $script:caseNotes.preset=$observed
        $candidate = if ($observed.items.Count) {[string]$observed.items[0]} else {$null}
        $null = Show-ImportInstructions $script:targetFixture $candidate
        Assert-NoReadyPath $observed 'Ambiguous canonical iframe payload'
        Assert-Case (-not @($script:caseEvents | Where-Object {$_.effect -eq 'copy'}).Count) 'Ambiguous iframe preset reached import-copy caller.'
    }

    Invoke-Case 'dry helpers refuse warm cache and all artifact effects' {
        $asset = New-Case 'dry-helper-boundary' $goodBytes
        $path = Assert-OnePath @(Download-Asset $asset) 'Seeded archive'
        $null = Expand-ChromiumAsset $path
        Set-DownloadPlan @((New-DownloadStep $script:utf8.GetBytes($script:canonicalPresetText)))
        $presetPath = Assert-OnePath @(Download-Preset) 'Seeded preset'
        $before = Get-FixtureSnapshot
        $script:caseEvents = @()
        $script:DryRun = $true
        $init = Invoke-Captured { Initialize-Staging }
        $download = Invoke-Captured { Download-Asset $asset }
        $extract = Invoke-Captured { Expand-ChromiumAsset $path }
        $preset = Invoke-Captured { Download-Preset }
        $null = Show-ImportInstructions $script:targetFixture $presetPath
        $null = Install-TablissNG $script:targetFixture
        $script:caseNotes.guards=[pscustomobject]@{init=$init; download=$download; extract=$extract; preset=$preset}
        Assert-NoReadyPath $download 'Dry warm-cache download'
        Assert-NoReadyPath $extract 'Dry extraction'
        Assert-NoReadyPath $preset 'Dry preset'
        Assert-Case ($script:caseEvents.Count -eq 0) 'Dry helper reached a transport, clipboard, browser or prompt boundary.'
        Assert-Case ((Get-FixtureSnapshot) -ceq $before) 'Dry helper changed fixture files or directories.'
    }
} catch {
    $script:results += [pscustomobject]@{case='fixture/bootstrap'; pass_=$false; pass=$false; status='SETUP_ERROR'; error=$_.Exception.Message}
} finally {
    $env:TEMP = $script:oldTemp
    $env:USERPROFILE = $script:oldUserProfile
}

$receipt = [ordered]@{
    schema='r0015-powershell-transactions-v1'; source=[IO.Path]::GetFullPath($SourceFile);
    sourceSha256=(Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant();
    testSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();
    presetSha256=(Get-FileHash -LiteralPath $PresetFile -Algorithm SHA256).Hash.ToLowerInvariant();
    observedUtc=[DateTime]::UtcNow.ToString('o'); runtime=$PSVersionTable.PSVersion.ToString();
    edition=$PSVersionTable.PSEdition; platform=[Environment]::OSVersion.ToString();
    processArchitecture=$env:PROCESSOR_ARCHITECTURE;
    scope=$(if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) {'native Windows files; ACL-specific controls are separate'} else {'supplemental native POSIX files; no Windows ACL/NTFS qualification'});
    fixtureRoot=$script:fixtureRoot; retainedFixture=$true; results=@($script:results)
}
$receipt | ConvertTo-Json -Depth 50
if (-not $script:results.Count -or @($script:results | Where-Object {-not $_.pass_}).Count) { exit 1 }
exit 0
