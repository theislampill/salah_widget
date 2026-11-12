# Salah Widget Installer for Windows
# Safe wizard: detects browsers/profiles, refuses legacy Tabliss profiles, downloads TablissNG release assets,
# and stages the Salah Widget preset for manual import into TablissNG.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -PresetUrl "https://raw.githubusercontent.com/YOU/REPO/main/presets/salah-widget.tablissng.json"
#   powershell -File .\install.ps1 -DryRun  # offline local discovery; no writes, network, clipboard or browser opens
#
# Environment overrides:
#   SALAH_WIDGET_HASH        Optional URL-hash config (lat=..&lon=..&method=..) baked into the widget iframe
#   SALAH_WIDGET_PRESET_URL  Raw URL to your TablissNG preset JSON
#   SALAH_INSTALL_SOURCE     github | store | ask
#   TABLISSNG_REPO           owner/repo for upstream TablissNG, default BookCatKid/TablissNG

#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$PresetUrl = $(if ($env:SALAH_WIDGET_PRESET_URL) { $env:SALAH_WIDGET_PRESET_URL } else { "https://raw.githubusercontent.com/theislampill/salah_widget/main/presets/salah-widget.tablissng.json" }),
    [string]$WidgetHash = $(if ($env:SALAH_WIDGET_HASH) { $env:SALAH_WIDGET_HASH } else { "" }),
    [ValidateSet("ask", "github", "store")]
    [string]$InstallSource = $(if ($env:SALAH_INSTALL_SOURCE) { $env:SALAH_INSTALL_SOURCE } else { "github" }),
    [string]$TablissNgRepo = $(if ($env:TABLISSNG_REPO) { $env:TABLISSNG_REPO } else { "BookCatKid/TablissNG" }),
    [switch]$DryRun,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$ChromeTablissNgId = "dlaogejjiafeobgofajdlkkhjlignalk"
$EdgeTablissNgId   = "mkaphhbkcccpgkfaifhhdfckagnkcmhm"

$ChromeLegacyTablissId = "hipekcciheckooncpjeljhnekcoolahp"
$EdgeLegacyTablissId   = "lklaendlmlfkaabeleddanafeinnenih"

$ChromeStoreUrl  = "https://chromewebstore.google.com/detail/tablissng/$ChromeTablissNgId"
$FirefoxStoreUrl = "https://addons.mozilla.org/en-US/firefox/addon/tablissng/"
$EdgeStoreUrl    = "https://microsoftedge.microsoft.com/addons/detail/tablissng/$EdgeTablissNgId"

$WorkRoot = Join-Path $env:TEMP "SalahWidgetInstaller"
$DownloadRoot = Join-Path $WorkRoot "downloads"
$PresetRoot = Join-Path $WorkRoot "presets"
function Initialize-Staging {
    if ($DryRun) { throw "Offline preview does not create staging directories." }
    New-Item -ItemType Directory -Force -Path $DownloadRoot, $PresetRoot | Out-Null
}

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Write-Ok([string]$Text) { Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-Warn([string]$Text) { Write-Host "[WARN] $Text" -ForegroundColor Yellow }
function Write-Err([string]$Text) { Write-Host "[ERROR] $Text" -ForegroundColor Red }

function First-ExistingPath([string[]]$Paths) {
    foreach ($p in $Paths) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    return $null
}

function Open-TargetUrl($Target, [string]$Url) {
    if ($NoOpen) {
        Write-Host "Open manually: $Url"
        return
    }
    if ($DryRun) {
        Write-Host "[dry-run] Would open: $Url"
        return
    }
    try {
        if ($Target -and $Target.ExePath -and (Test-Path -LiteralPath $Target.ExePath)) {
            Start-Process -FilePath $Target.ExePath -ArgumentList $Url | Out-Null
        } else {
            Start-Process $Url | Out-Null
        }
    } catch {
        Write-Warn "Could not open automatically. Open manually: $Url"
    }
}

function Copy-Text([string]$Text) {
    if ($DryRun) { Write-Host "[dry-run] Clipboard copy suppressed."; return $false }
    try {
        Set-Clipboard -Value $Text
        return $true
    } catch {
        return $false
    }
}

function Sanitize-FilePart([string]$Name) {
    return ($Name -replace '[^\w.\-]+', '_')
}

function Get-BrowserConfigs {
    $local = $env:LOCALAPPDATA
    $roam = $env:APPDATA

    @(
        [pscustomobject]@{
            Key="chrome"; Label="Google Chrome"; Family="chromium";
            UserData=Join-Path $local "Google\Chrome\User Data";
            Exes=@(
                "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "$local\Google\Chrome\Application\chrome.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="chrome://extensions/"; NewTabUrl="chrome://newtab/"
        },
        [pscustomobject]@{
            Key="edge"; Label="Microsoft Edge"; Family="chromium";
            UserData=Join-Path $local "Microsoft\Edge\User Data";
            Exes=@(
                "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
                "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
                "$local\Microsoft\Edge\Application\msedge.exe"
            );
            NewIds=@($EdgeTablissNgId, $ChromeTablissNgId);
            OldIds=@($EdgeLegacyTablissId, $ChromeLegacyTablissId);
            StoreUrl=$EdgeStoreUrl; ManagerUrl="edge://extensions/"; NewTabUrl="edge://newtab/"
        },
        [pscustomobject]@{
            Key="brave"; Label="Brave"; Family="chromium";
            UserData=Join-Path $local "BraveSoftware\Brave-Browser\User Data";
            Exes=@(
                "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
                "${env:ProgramFiles(x86)}\BraveSoftware\Brave-Browser\Application\brave.exe",
                "$local\BraveSoftware\Brave-Browser\Application\brave.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="brave://extensions/"; NewTabUrl="brave://newtab/"
        },
        [pscustomobject]@{
            Key="chromium"; Label="Chromium"; Family="chromium";
            UserData=Join-Path $local "Chromium\User Data";
            Exes=@(
                "$env:ProgramFiles\Chromium\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Chromium\Application\chrome.exe",
                "$local\Chromium\Application\chrome.exe"
            );
            NewIds=@($ChromeTablissNgId);
            OldIds=@($ChromeLegacyTablissId);
            StoreUrl=$ChromeStoreUrl; ManagerUrl="chrome://extensions/"; NewTabUrl="chrome://newtab/"
        },
        [pscustomobject]@{
            Key="firefox"; Label="Firefox"; Family="firefox";
            UserData=Join-Path $roam "Mozilla\Firefox\Profiles";
            Exes=@(
                "$env:ProgramFiles\Mozilla Firefox\firefox.exe",
                "${env:ProgramFiles(x86)}\Mozilla Firefox\firefox.exe",
                "$local\Mozilla Firefox\firefox.exe"
            );
            NewIds=@(); OldIds=@();
            StoreUrl=$FirefoxStoreUrl; ManagerUrl="about:addons"; NewTabUrl="about:newtab"
        },
        [pscustomobject]@{
            Key="librewolf"; Label="LibreWolf"; Family="firefox";
            UserData=Join-Path $roam "LibreWolf\Profiles";
            Exes=@(
                "$env:ProgramFiles\LibreWolf\librewolf.exe",
                "${env:ProgramFiles(x86)}\LibreWolf\librewolf.exe",
                "$local\LibreWolf\librewolf.exe"
            );
            NewIds=@(); OldIds=@();
            StoreUrl=$FirefoxStoreUrl; ManagerUrl="about:addons"; NewTabUrl="about:newtab"
        }
    )
}

function Get-ChromiumProfiles($Config) {
    if (-not (Test-Path -LiteralPath $Config.UserData)) { return @() }
    $dirs = Get-ChildItem -LiteralPath $Config.UserData -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq "Default" -or
            $_.Name -match "^Profile \d+$" -or
            (Test-Path -LiteralPath (Join-Path $_.FullName "Preferences"))
        }
    return @($dirs)
}

function Get-FirefoxProfiles($Config) {
    if (-not (Test-Path -LiteralPath $Config.UserData)) { return @() }
    return @(Get-ChildItem -LiteralPath $Config.UserData -Directory -ErrorAction SilentlyContinue)
}

function Get-ChromiumExtensionStatus($ProfilePath, [string[]]$NewIds, [string[]]$OldIds) {
    $newFound = New-Object System.Collections.Generic.List[string]
    $oldFound = New-Object System.Collections.Generic.List[string]

    $extDir = Join-Path $ProfilePath "Extensions"
    foreach ($id in $NewIds) {
        if ($id -and (Test-Path -LiteralPath (Join-Path $extDir $id))) { [void]$newFound.Add($id) }
    }
    foreach ($id in $OldIds) {
        if ($id -and (Test-Path -LiteralPath (Join-Path $extDir $id))) { [void]$oldFound.Add($id) }
    }

    $prefsPath = Join-Path $ProfilePath "Preferences"
    if (Test-Path -LiteralPath $prefsPath) {
        try {
            $prefs = Get-Content -Raw -LiteralPath $prefsPath | ConvertFrom-Json
            if ($prefs.extensions -and $prefs.extensions.settings) {
                $settingIds = @($prefs.extensions.settings.PSObject.Properties.Name)
                foreach ($id in $NewIds) {
                    if ($settingIds -contains $id) { [void]$newFound.Add($id) }
                }
                foreach ($id in $OldIds) {
                    if ($settingIds -contains $id) { [void]$oldFound.Add($id) }
                }
            }
        } catch {
            # Preferences can be locked or malformed while a browser is running. Directory detection still works.
        }
    }

    $hasNewResult = (($newFound | Select-Object -Unique).Count -gt 0)
    $hasOldResult = (($oldFound | Select-Object -Unique).Count -gt 0)
    [pscustomobject]@{
        HasNew = $hasNewResult
        HasOld = $hasOldResult
        NewMatches = @($newFound | Select-Object -Unique)
        OldMatches = @($oldFound | Select-Object -Unique)
        Status = $(if ($hasNewResult -and $hasOldResult) { 'known-both' } elseif ($hasOldResult) { 'known-legacy' } elseif ($hasNewResult) { 'known-new' } else { 'known-neither' })
        Reason = 'existing-chromium-detector'
        EvidenceClass = 'chromium-directory-and-preferences'
        MetadataSource = $ProfilePath
    }
}

# Validate strict JSON grammar and unambiguous object keys before the host's
# permissive ConvertFrom-Json conversion. This helper has no external effects.
function Test-StrictJson([string]$Json) {
    $lexer = [regex]'\G(?:(?<space>[ \t\r\n]+)|(?<string>"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*")|(?<number>-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|(?<literal>true|false|null)|(?<mark>[{}\[\],:]))'
    $frames = New-Object 'System.Collections.Generic.List[object]'
    $position=0; $rootComplete=$false
    try {
        # Continue one match sequence instead of passing the whole document to
        # a fresh Match call for every token. Keep contiguous, complete coverage.
        for ($tokenMatch=$lexer.Match($Json); $tokenMatch.Success; $tokenMatch=$tokenMatch.NextMatch()) {
            if (-not $tokenMatch.Success -or $tokenMatch.Index -ne $position) { return $false }
            $position += $tokenMatch.Length
            if ($tokenMatch.Groups['space'].Success) { continue }
            $token=$tokenMatch.Value
            $frame=if ($frames.Count) { $frames[$frames.Count-1] } else { $null }

            if ($null -ne $frame -and $frame.Kind -eq 'object' -and ($frame.State -eq 'key-or-end' -or $frame.State -eq 'key')) {
                if ($token -eq '}' -and $frame.State -eq 'key-or-end') { $frames.RemoveAt($frames.Count-1); continue }
                if (-not $tokenMatch.Groups['string'].Success) { return $false }
                # Decode strict JSON string escapes so name and na\u006de are
                # the same property. Compare case-insensitively because the
                # downstream PowerShell object's property lookup does so too.
                $keyText=New-Object System.Text.StringBuilder
                for ($i=1; $i -lt $token.Length-1; $i++) {
                    if ($token[$i] -ne [char]92) { [void]$keyText.Append($token[$i]); continue }
                    $i++
                    switch ($token[$i]) {
                        '"' { [void]$keyText.Append([char]34) }
                        '\' { [void]$keyText.Append([char]92) }
                        '/' { [void]$keyText.Append([char]47) }
                        'b' { [void]$keyText.Append([char]8) }
                        'f' { [void]$keyText.Append([char]12) }
                        'n' { [void]$keyText.Append([char]10) }
                        'r' { [void]$keyText.Append([char]13) }
                        't' { [void]$keyText.Append([char]9) }
                        'u' { [void]$keyText.Append([char][Convert]::ToInt32($token.Substring($i+1,4),16)); $i+=4 }
                    }
                }
                if (-not $frame.Keys.Add($keyText.ToString())) { return $false }
                $frame.State='colon'; continue
            }
            if ($null -ne $frame -and $frame.State -eq 'colon') {
                if ($token -ne ':') { return $false }
                $frame.State='value'; continue
            }
            if ($null -ne $frame -and $frame.State -eq 'after-value') {
                $closing=if ($frame.Kind -eq 'object') { '}' } else { ']' }
                if ($token -eq $closing) { $frames.RemoveAt($frames.Count-1); continue }
                if ($token -ne ',') { return $false }
                $frame.State=if ($frame.Kind -eq 'object') { 'key' } else { 'value' }
                continue
            }
            if ($null -ne $frame -and $frame.Kind -eq 'array' -and $frame.State -eq 'value-or-end' -and $token -eq ']') {
                $frames.RemoveAt($frames.Count-1); continue
            }

            # A value consumes exactly one parent slot; nested containers must
            # close before that parent accepts its next separator or member.
            if ($null -ne $frame) { $frame.State='after-value' }
            elseif ($rootComplete) { return $false }
            else { $rootComplete=$true }
            if ($token -eq '{') {
                $keys=New-Object 'System.Collections.Generic.HashSet[string]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
                [void]$frames.Add([pscustomobject]@{Kind='object';State='key-or-end';Keys=$keys})
            } elseif ($token -eq '[') {
                [void]$frames.Add([pscustomobject]@{Kind='array';State='value-or-end'})
            } elseif (-not ($tokenMatch.Groups['string'].Success -or $tokenMatch.Groups['number'].Success -or $tokenMatch.Groups['literal'].Success)) {
                return $false
            }
        }
        return ($position -eq $Json.Length -and $rootComplete -and $frames.Count -eq 0)
    } catch { return $false }
}

function Get-FirefoxExtensionStatus($ProfilePath) {
    $extensionsJson = Join-Path $ProfilePath "extensions.json"
    $result = [pscustomobject]@{
        HasNew=$false; HasOld=$false; NewMatches=@(); OldMatches=@()
        Status='unknown'; Reason='metadata-absent'; EvidenceClass='firefox-extensions-json'; MetadataSource=$extensionsJson
    }
    $newMatches = New-Object System.Collections.Generic.List[string]
    $oldMatches = New-Object System.Collections.Generic.List[string]
    try {
        if (-not (Test-Path -LiteralPath $extensionsJson)) { return $result }
        $decoder = New-Object System.Text.UTF8Encoding -ArgumentList $false,$true
        $raw = [IO.File]::ReadAllText($extensionsJson, $decoder)
    } catch [System.Text.DecoderFallbackException] {
        $result.Reason='metadata-encoding'
        Write-Warn "Firefox discovery held: invalid metadata encoding."
        return $result
    } catch {
        $result.Reason='metadata-unreadable'
        Write-Warn "Firefox discovery held: metadata could not be read."
        return $result
    }
    try {
        if (-not (Test-StrictJson $raw)) { throw 'Invalid or ambiguous JSON metadata.' }
        $data = ConvertFrom-Json -InputObject $raw
    }
    catch {
        $result.Reason='metadata-malformed'
        Write-Warn "Firefox discovery held: malformed metadata."
        return $result
    }
    # ConvertFrom-Json can unwrap a singleton root array into one object.
    if ($raw -notmatch '^\s*\{' -or -not ($data -is [pscustomobject]) -or $null -eq $data.PSObject.Properties['addons'] -or $data.PSObject.Properties['addons'].Name -cne 'addons' -or -not ($data.addons -is [array])) {
        $result.Reason='metadata-unsupported'
        return $result
    }
    $supported=$true
    foreach ($addon in $data.addons) {
        if (-not ($addon -is [pscustomobject])) { $supported=$false; break }
        # PowerShell member lookup ignores case; Firefox JSON field names do not.
        foreach ($key in 'id','name','defaultLocale') {
            $property=$addon.PSObject.Properties[$key]
            if ($null -ne $property -and $property.Name -cne $key) { $supported=$false }
        }
        foreach ($key in 'id','name') {
            if ($null -ne $addon.$key -and -not ($addon.$key -is [string])) { $supported=$false }
        }
        $locale=$addon.defaultLocale
        if ($null -ne $locale -and (-not ($locale -is [pscustomobject]) -or ($null -ne $locale.name -and -not ($locale.name -is [string])))) { $supported=$false }
        if ($locale -is [pscustomobject]) {
            $localeName=$locale.PSObject.Properties['name']
            if ($null -ne $localeName -and $localeName.Name -cne 'name') { $supported=$false }
        }
        if (-not $supported) { break }
        $parts = @()
        if ($addon.id) { $parts += $addon.id }
        if ($addon.name) { $parts += $addon.name }
        if ($locale -and $locale.name) { $parts += $locale.name }
        $hay = ($parts -join " ")
        if ([string]::IsNullOrWhiteSpace($hay)) { $supported=$false; break }
        if ($hay -match "(?i)\bTablissNG\b|tablissng") {
            $result.HasNew=$true; [void]$newMatches.Add($hay)
        } elseif ($hay -match "(?i)\bTabliss\b" -and $hay -notmatch "(?i)NG|tablissng") {
            $result.HasOld=$true; [void]$oldMatches.Add($hay)
        }
    }
    $result.NewMatches=@($newMatches | Select-Object -Unique)
    $result.OldMatches=@($oldMatches | Select-Object -Unique)
    if ($supported) {
        $result.Status = if ($result.HasNew -and $result.HasOld) { 'known-both' } elseif ($result.HasOld) { 'known-legacy' } elseif ($result.HasNew) { 'known-new' } else { 'known-neither' }
        $result.Reason='supported-metadata'
    } else {
        $result.Reason='metadata-unsupported'
    }
    return $result
}

# One derived guard serves preview, pre-staging selection and actual dispatch.
function Get-DiscoveryEligibility($Target) {
    if ($Target.HasLegacyTabliss) { return 'legacy-refused' }
    switch ($Target.DiscoveryStatus) {
        'known-new' { return 'eligible-known' }
        'known-neither' { return 'eligible-known' }
        'known-legacy' { return 'legacy-refused' }
        'known-both' { return 'legacy-refused' }
        default { return 'unknown-held' }
    }
}

function Get-Targets {
    $targets = New-Object System.Collections.Generic.List[object]
    foreach ($cfg in Get-BrowserConfigs) {
        $exe = First-ExistingPath $cfg.Exes
        $profiles = if ($cfg.Family -eq "chromium") { Get-ChromiumProfiles $cfg } else { Get-FirefoxProfiles $cfg }
        $browserInstalled = [bool]($exe -or (Test-Path -LiteralPath $cfg.UserData))

        if ($profiles.Count -eq 0) {
            if ($browserInstalled) {
                [void]$targets.Add([pscustomobject]@{
                    Index=$targets.Count + 1; Config=$cfg; Browser=$cfg.Label; Family=$cfg.Family;
                    ProfileName="(no profile detected)"; ProfilePath=$null; ExePath=$exe;
                    HasTablissNG=$false; HasLegacyTabliss=$false; NewMatches=@(); OldMatches=@()
                    DiscoveryStatus='unknown'; DiscoveryReason='no-profile'; DiscoveryEvidence='browser-profile-discovery'; DiscoverySource=$cfg.UserData
                })
            }
            continue
        }

        foreach ($p in $profiles) {
            $status = if ($cfg.Family -eq "chromium") {
                Get-ChromiumExtensionStatus $p.FullName $cfg.NewIds $cfg.OldIds
            } else {
                Get-FirefoxExtensionStatus $p.FullName
            }
            [void]$targets.Add([pscustomobject]@{
                Index=$targets.Count + 1; Config=$cfg; Browser=$cfg.Label; Family=$cfg.Family;
                ProfileName=$p.Name; ProfilePath=$p.FullName; ExePath=$exe;
                HasTablissNG=$status.HasNew; HasLegacyTabliss=$status.HasOld;
                NewMatches=$status.NewMatches; OldMatches=$status.OldMatches
                DiscoveryStatus=$status.Status; DiscoveryReason=$status.Reason;
                DiscoveryEvidence=$status.EvidenceClass; DiscoverySource=$status.MetadataSource
            })
        }
    }
    return $targets.ToArray()
}

$script:LatestRelease = $null
function Get-LatestRelease {
    if ($DryRun) { throw "Offline preview cannot resolve remote GitHub releases or use cached metadata." }
    if ($script:LatestRelease) { return $script:LatestRelease }
    $uri = "https://api.github.com/repos/$TablissNgRepo/releases/latest"
    Write-Host "Resolving latest TablissNG release from $uri"
    $headers = @{
        "Accept" = "application/vnd.github+json"
        "User-Agent" = "salah-widget-installer"
    }
    $script:LatestRelease = Invoke-RestMethod -Uri $uri -Headers $headers
    return $script:LatestRelease
}

function Select-TablissNgAsset([string]$Family) {
    if ($DryRun) { throw "Offline preview leaves release assets unresolved." }
    $release = Get-LatestRelease
    $assets = @($release.assets)
    if ($assets.Count -eq 0) { throw "Latest release '$($release.tag_name)' has no assets." }

    if ($Family -eq "firefox") {
        $preferred = @(
            $assets | Where-Object { $_.name -match "(?i)\.xpi$" -and $_.name -match "(?i)signed|firefox" -and $_.name -notmatch "(?i)unsigned|source" }
            $assets | Where-Object { $_.name -match "(?i)\.xpi$" -and $_.name -notmatch "(?i)unsigned|source" }
            $assets | Where-Object { $_.name -match "(?i)firefox.*\.zip$" -and $_.name -notmatch "(?i)unsigned|source" }
        ) | ForEach-Object { $_ }
    } elseif ($Family -eq "chromium") {
        $preferred = @(
            $assets | Where-Object { $_.name -match "(?i)chrom(e|ium).*\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" }
            $assets | Where-Object { $_.name -match "(?i)tabliss.*\.zip$" -and $_.name -notmatch "(?i)firefox|safari|source" }
        ) | ForEach-Object { $_ }
    } else {
        throw "Unsupported browser family for GitHub release install: $Family"
    }

    $asset = @($preferred | Where-Object { $_ } | Select-Object -First 1)
    if (-not $asset) {
        throw "No safe $Family asset found in latest release '$($release.tag_name)'."
    }
    return $asset
}

function Download-Asset($Asset) {
    if ($DryRun) { throw "Offline preview does not download or return cached asset paths." }
    $release = Get-LatestRelease
    $tag = Sanitize-FilePart $release.tag_name
    $name = Sanitize-FilePart $Asset.name
    $destDir = Join-Path $DownloadRoot $tag
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    $dest = Join-Path $destDir $name
    if (Test-Path -LiteralPath $dest) {
        Write-Ok "Already downloaded $name"
        return $dest
    }
    Write-Host "Downloading $($Asset.name)"
    Write-Host "  $($Asset.browser_download_url)"
    Invoke-WebRequest -UseBasicParsing -Uri $Asset.browser_download_url -OutFile $dest
    return $dest
}

function Expand-ChromiumAsset([string]$ZipPath) {
    if ($DryRun) { throw "Offline preview does not extract assets." }
    $leaf = [IO.Path]::GetFileNameWithoutExtension($ZipPath)
    $extractRoot = Join-Path (Split-Path -Parent $ZipPath) "$leaf-unpacked"
    if (Test-Path -LiteralPath $extractRoot) {
        Remove-Item -LiteralPath $extractRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $extractRoot -Force

    $manifest = Get-ChildItem -LiteralPath $extractRoot -Recurse -Filter "manifest.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\__MACOSX\\" } |
        Sort-Object FullName |
        Select-Object -First 1
    if (-not $manifest) {
        throw "Downloaded Chromium asset did not contain manifest.json after extraction: $ZipPath"
    }
    return Split-Path -Parent $manifest.FullName
}

function Download-Preset {
    if ($DryRun) { Write-Host "[dry-run] Preset staging suppressed."; return $null }
    if (-not $PresetUrl) {
        Write-Warn "No preset URL configured. Set -PresetUrl or SALAH_WIDGET_PRESET_URL."
        return $null
    }

    $presetFile = Join-Path $PresetRoot "salah-widget.tablissng.json"
    Write-Host "Downloading Salah Widget preset:"
    Write-Host "  $PresetUrl"

    try {
        Invoke-WebRequest -UseBasicParsing -Uri $PresetUrl -OutFile $presetFile
        if ($WidgetHash) {
            # bake the builder's chosen configuration into the staged preset's iframe URL
            # (replaces the default #local=1 hash) so the user's settings carry through the install
            $raw = (Get-Content -Raw -LiteralPath $presetFile).Replace("local=1", $WidgetHash)
            [System.IO.File]::WriteAllText($presetFile, $raw, (New-Object System.Text.UTF8Encoding $false))
            Write-Ok "Applied your widget configuration to the preset (#$WidgetHash)."
        }
        try {
            Get-Content -Raw -LiteralPath $presetFile | ConvertFrom-Json | Out-Null
            Write-Ok "Preset JSON is parseable: $presetFile"
        } catch {
            Write-Warn "Downloaded preset is not parseable JSON. Check the preset file before publishing."
        }
        return $presetFile
    } catch {
        Write-Warn "Could not download preset from the configured URL."
        Write-Warn "Configure -PresetUrl after you publish the preset JSON in your repository."
        return $null
    }
}

function Show-ImportInstructions($Target, [string]$PresetFile) {
    if ($DryRun) { Write-Host "[dry-run] Would guide manual preset import; no artifact resolved."; return }
    Write-Section "Import Salah Widget preset for $($Target.Browser) / $($Target.ProfileName)"
    if ($PresetFile) {
        Write-Host "Preset file:"
        Write-Host "  $PresetFile"
        if (Copy-Text $PresetFile) {
            Write-Ok "Copied the preset file path to clipboard."
        }
    } else {
        Write-Warn "Preset file is not available yet."
    }

    Write-Host ""
    Write-Host "Manual import path:"
    Write-Host "  1. Open a new tab controlled by TablissNG."
    Write-Host "  2. Open TablissNG settings."
    Write-Host "  3. Use Import/Restore settings."
    Write-Host "  4. Select the preset JSON file above."
    Write-Host ""
    Write-Host "This wizard does not directly write into browser extension storage."
    Write-Host "That avoids corrupting profiles and avoids touching legacy Tabliss."
    Write-Warn "Importing the preset replaces your current TablissNG dashboard."

    Open-TargetUrl $Target $Target.Config.NewTabUrl
}

function Install-TablissNG($Target) {
    if ($DryRun) { Write-Host "[dry-run] Manual installation actions suppressed; release and paths unresolved."; return }
    $source = $InstallSource
    if ($source -eq "ask") {
        Write-Host ""
        Write-Host "Install source for $($Target.Browser):"
        Write-Host "  1) GitHub latest release/manual install"
        Write-Host "  2) Official browser store page"
        $choice = Read-Host "Choose [1/2] (default 1)"
        if ($choice -eq "2") { $source = "store" } else { $source = "github" }
    }

    if ($source -eq "store") {
        Write-Section "Open official store page for $($Target.Browser)"
        Write-Host $Target.Config.StoreUrl
        Open-TargetUrl $Target $Target.Config.StoreUrl
        Write-Host "Finish the browser's normal extension install, then return here."
        Read-Host "Press Enter after TablissNG is installed"
        return
    }

    Write-Section "Download TablissNG from GitHub latest release for $($Target.Browser)"
    try {
        $asset = Select-TablissNgAsset $Target.Family
        $path = Download-Asset $asset

        if ($Target.Family -eq "chromium") {
            $unpacked = Expand-ChromiumAsset $path
            Write-Host ""
            Write-Host "Chromium-family install steps:"
            Write-Host "  1. Open Extensions."
            Write-Host "  2. Enable Developer mode."
            Write-Host "  3. Click Load unpacked."
            Write-Host "  4. Select this folder:"
            Write-Host "     $unpacked"
            if (Copy-Text $unpacked) {
                Write-Ok "Copied unpacked extension folder path to clipboard."
            }
            Open-TargetUrl $Target $Target.Config.ManagerUrl
        } elseif ($Target.Family -eq "firefox") {
            Write-Host ""
            Write-Host "Firefox-family install steps:"
            Write-Host "  1. Open Add-ons Manager."
            Write-Host "  2. Click the gear icon."
            Write-Host "  3. Click Install Add-on From File."
            Write-Host "  4. Select this file:"
            Write-Host "     $path"
            if (Copy-Text $path) {
                Write-Ok "Copied XPI path to clipboard."
            }
            Open-TargetUrl $Target $Target.Config.ManagerUrl
        }

        Write-Host ""
        Write-Host "Finish the browser's install prompt, then return here."
        Read-Host "Press Enter after TablissNG is installed"
    } catch {
        Write-Warn $_.Exception.Message
        Write-Warn "Falling back to official store page."
        Open-TargetUrl $Target $Target.Config.StoreUrl
        Read-Host "Press Enter after TablissNG is installed"
    }
}

Write-Host ""
Write-Host "Salah Widget Installer" -ForegroundColor Cyan
Write-Host ""
Write-Host "This wizard can:"
Write-Host "- detect supported browsers/profiles"
Write-Host "- check for TablissNG"
Write-Host "- safely refuse to modify legacy Tabliss profiles"
Write-Host "- download the right TablissNG build from GitHub latest release when needed"
Write-Host "- guide the browser-required install step"
Write-Host "- stage the Salah Widget preset for import"
Write-Host ""
Write-Host "It will not silently force-install extensions or write directly into extension storage."

Write-Section "Detecting browsers"
$targets = @(Get-Targets)

if ($targets.Count -eq 0) {
    Write-Err "No supported browser profiles or installs were detected."
    exit 1
}

foreach ($t in $targets) {
    $eligibility=Get-DiscoveryEligibility $t
    $status = if ($eligibility -eq 'legacy-refused') {
        "legacy Tabliss evidence: REFUSED ($($t.DiscoveryStatus))"
    } elseif ($eligibility -eq 'unknown-held') {
        "discovery unknown: HELD ($($t.DiscoveryReason))"
    } elseif ($t.DiscoveryStatus -eq 'known-new') {
        "TablissNG detected"
    } else {
        "neither extension identified by $($t.DiscoveryEvidence)"
    }
    Write-Host ("[{0}] {1} / {2} - {3}" -f $t.Index, $t.Browser, $t.ProfileName, $status)
}

# Preview is a whole-entry boundary: no terminal prompts or artifact helpers run.
if ($DryRun) {
    Write-Section "Offline preview"
    $eligibleCount=0; $heldCount=0; $refusedCount=0
    foreach ($target in $targets) {
        $eligibility=Get-DiscoveryEligibility $target
        if ($eligibility -eq 'legacy-refused') { $refusedCount++; Write-Warn "Legacy Tabliss: refusing $($target.Browser) / $($target.ProfileName)."; continue }
        if ($eligibility -ne 'eligible-known') { $heldCount++; Write-Warn "Held $($target.Browser) / $($target.ProfileName): $($target.DiscoveryReason). Review metadata manually; no automatic actions."; continue }
        $eligibleCount++
        Write-Host "Would prepare $($target.Browser) / $($target.ProfileName)."
        if (-not $target.HasTablissNG) {
            if ($InstallSource -eq "ask") { Write-Host "Install source unresolved: GitHub manual route or official store page." }
            elseif ($InstallSource -eq "store") { Write-Host "Would open official store: $($target.Config.StoreUrl)" }
            else { Write-Host "Would resolve/download GitHub release; release/version/path unresolved until execution." }
        }
        if ($PresetUrl) { Write-Host "Would stage configured preset and guide manual import; path unresolved until execution." }
        else { Write-Warn "No preset URL configured; preset import cannot be prepared." }
        Write-Host "Would open the browser's manual installation/import pages and offer clipboard paths."
    }
    Write-Host "Preview targets: $eligibleCount eligible, $heldCount held, $refusedCount refused."
    Write-Warn "Importing the preset replaces your current TablissNG dashboard."
    if ($eligibleCount -eq 0) { Write-Err "No eligible target; preview made no changes."; exit 1 }
    Write-Host "Preview only; no changes made. No network requests were made."
    exit 0
}

Write-Host ""
$selection = Read-Host "Select target numbers separated by commas, or 'all' (default all)"
if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "all" }

$selected = @()
if ($selection.Trim().ToLowerInvariant() -eq "all") {
    $selected = $targets
} else {
    $wanted = $selection -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -match "^\d+$" } | ForEach-Object { [int]$_ }
    $selected = @($targets | Where-Object { $wanted -contains $_.Index })
}

if ($selected.Count -eq 0) {
    Write-Err "No valid targets selected."
    exit 1
}

$eligibleCount=0; $heldCount=0; $refusedCount=0
foreach ($target in $selected) {
    switch (Get-DiscoveryEligibility $target) {
        'eligible-known' { $eligibleCount++ }
        'legacy-refused' { $refusedCount++ }
        default { $heldCount++ }
    }
}
Write-Host "Selected targets: $eligibleCount eligible, $heldCount held, $refusedCount refused."
if ($eligibleCount -eq 0) {
    Write-Err "No eligible target selected; unknown targets are held and legacy Tabliss profiles refused. Manual actions remain pending."
    exit 1
}
Initialize-Staging

$presetFile = $null

foreach ($target in $selected) {
    Write-Section "$($target.Browser) / $($target.ProfileName)"

    $eligibility=Get-DiscoveryEligibility $target
    if ($eligibility -eq 'legacy-refused') {
        Write-Warn "Legacy Tabliss detected in this profile. Refusing to touch this browser/profile."
        if ($target.OldMatches.Count -gt 0) {
            Write-Host "Matches:"
            foreach ($m in $target.OldMatches) { Write-Host "  $m" }
        }
        continue
    }
    if ($eligibility -ne 'eligible-known') {
        Write-Warn "Held $($target.Browser) / $($target.ProfileName): $($target.DiscoveryReason). Review metadata manually; no automatic actions."
        continue
    }

    if (-not $target.HasTablissNG) {
        Install-TablissNG $target
    } else {
        Write-Ok "TablissNG already appears to be installed."
    }

    if (-not $presetFile) { $presetFile = Download-Preset }
    Show-ImportInstructions $target $presetFile
}

Write-Section "Manual action pending"
Write-Host "Manual browser installation/import remain pending. Staging directory:"
Write-Host "  $WorkRoot"
Write-Host ""
Write-Host "Review this script before publishing it. The preset URL should point at your real raw JSON file."
