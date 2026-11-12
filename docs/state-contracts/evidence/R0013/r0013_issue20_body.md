# R0014: Repair PowerShell minimum-host parsing and release-asset selection

Live read: https://github.com/theislampill/salah_widget/issues/20
State: closed; updated 2026-10-12T14:27:17Z

<!-- salah-widget-audit-20260907:SW-020 -->
# R0014: Repair PowerShell minimum-host parsing and release-asset selection

**Repository-local identity:** `R0014` in `theislampill/salah_widget`; existing tracker [#20](https://github.com/theislampill/salah_widget/issues/20). The SW identifier is historical draft provenance.


Campaign draft alias: SW-020. Product defect; proposed priority P1. The exact downloaded file must parse on declared Windows PowerShell 5.1, and valid release assets must reach the manual-install path. VAL-005 establishes a file-decoding failure before execution; VAL-004 independently establishes a selector failure after parsing. Repair both. A newer host or successful store fallback can hide one failure without fixing it.

## Baseline and evidence custody

Historical source: main `fd2972ba64225fe9d6848e92497e6d0ed20ea624`, candidate `9d9c43649748555afbe09e3ca49bc47db2d7e7bb`. Both produced the same selector exception. Before future edits, bind the authorized checkout and preserve unrelated work:

```text
git --no-optional-locks rev-parse --show-toplevel
git --no-optional-locks remote get-url origin
git --no-optional-locks status --short --branch
git --no-optional-locks rev-parse HEAD
git --no-optional-locks diff fd2972ba64225fe9d6848e92497e6d0ed20ea624 HEAD -- install.ps1 README.md builder.html
```

Require the intended `theislampill/salah_widget` target and inspect any changed encoding, selector, callers and advertised host. Stop on incompatible drift; do not assume the old defect survives at a future HEAD. The candidate is not approved for wholesale adoption.

Owners are [install.ps1 exact file/minimum-host declaration](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.ps1#L1-L26), [Select-TablissNgAsset](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.ps1#L314-L339), [download/manual/fallback consumers](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.ps1#L341-L503), [the non-ASCII display string](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.ps1#L527-L535), [README Windows route](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/README.md#L41-L68) and [builder Windows command](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/builder.html#L344-L357). [Candidate installer](https://github.com/theislampill/salah_widget/blob/9d9c43649748555afbe09e3ca49bc47db2d7e7bb/install.ps1) is comparison evidence.

## What actually failed, and competing interpretations

The 7 September controlled native-host probe recorded Windows PowerShell `5.1.26100.9168` and PowerShell `7.6.5`. On 5.1, `Parser.ParseFile` over the BOM-less UTF-8 file returned four errors, at source lines 535, 535, 583 and 527: unexpected `{`, missing `)`, missing string terminator, missing `}`. Its initial bytes were `35,32,83`, not a UTF-8 BOM. Explicit UTF-8 `ReadAllText` followed by `ParseInput` returned zero errors; PS7 `ParseFile` also returned zero. This differential ties the failure to exact file decoding. It does not establish that README’s `irm | iex` response-string route fails identically, and it does not make a PS7-only parse an acceptable 5.1 gate.

The independently extracted selector was given `tabliss-chromium.zip` and `tabliss-firefox-signed.xpi` as in-memory release assets. On both hosts and both source trees it threw `Cannot convert 'System.Object[]' to the type 'System.String' required by parameter 'Property'. Specified method is not supported.` The comma after each `Where-Object` pipeline inside `@(...)` changes argument binding; this is not a missing upstream release or failed download. `Install-TablissNG` catches the exception and offers a store, so observing a store prompt would not prove valid GitHub selection.

No whole wizard, download, store opening, browser profile mutation or extension installation was executed by this evidence. Four independent combinations of tree/family share the same implementation and are not four independent defect mechanisms.

## Public RED recipe: exact bytes plus bounded selector

Save this as `red-powershell.ps1` outside the source checkout. Execute it with both actual hosts, supplying an absolute source file path:

```powershell
powershell.exe -NoProfile -File .\red-powershell.ps1 -SourceFile C:\fixture\install.ps1
pwsh.exe -NoProfile -File .\red-powershell.ps1 -SourceFile C:\fixture\install.ps1
```

The fixture does not execute installer top level or call a remote API. Its text is ASCII-safe so the fixture itself does not reproduce the decoding mistake accidentally.

```powershell
param([Parameter(Mandatory=$true)][string]$SourceFile)
$ErrorActionPreference = 'Stop'
$tokens=$null; $fileErrors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile(
  $SourceFile,[ref]$tokens,[ref]$fileErrors)
$text=[IO.File]::ReadAllText($SourceFile,[Text.Encoding]::UTF8)
$tokens=$null; $textErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseInput(
  $text,[ref]$tokens,[ref]$textErrors)
if (@($textErrors).Count) { throw 'Unexpected source syntax drift' }
$defs=@($ast.FindAll({param($n)
  $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
  $n.Name -eq 'Select-TablissNgAsset'
},$true))
if ($defs.Count -ne 1) { throw 'Selector identity mismatch' }
. ([scriptblock]::Create($defs[0].Extent.Text))
function Get-LatestRelease {
  [pscustomobject]@{tag_name='fixture'; assets=@(
    [pscustomobject]@{name='tabliss-chromium.zip'; browser_download_url='https://example.invalid/chromium'}
    [pscustomobject]@{name='tabliss-firefox-signed.xpi'; browser_download_url='https://example.invalid/firefox'}
  )}
}
$rows=foreach($family in 'chromium','firefox') {
  try {
    $chosen=@(Select-TablissNgAsset $family)
    [pscustomobject]@{family=$family; result='selected'; count=$chosen.Count; names=@($chosen.name)}
  } catch {
    [pscustomobject]@{family=$family; result='threw'; error=$_.Exception.Message}
  }
}
[pscustomobject]@{
  host=$PSVersionTable.PSVersion.ToString()
  fileErrors=@($fileErrors).Count
  fileErrorLines=@($fileErrors | ForEach-Object {$_.Extent.StartLineNumber})
  explicitUtf8Errors=@($textErrors).Count
  cases=@($rows)
} | ConvertTo-Json -Depth 6
```

At the pinned RED baseline: 5.1 fileErrors=4, explicitUtf8Errors=0; PS7 both=0; both families throw the Property-binding error on both hosts. Extracting from explicit UTF-8 text is intentional isolation of the second defect, not a replacement for the exact-file parser gate. Run final GREEN against the repaired file and, when distribution is claimed, against bytes freshly read from the authorized raw-script endpoint. Never resave that downloaded copy through a text editor before hashing and parsing it.

## Staged implementation design

**1. Repair byte interpretation without raising the floor.** Keep `#requires -Version 5.1`. Prefer making the installer source ASCII-safe: replace the decorative em dash in the quoted status line with ` - `, inspect remaining non-ASCII bytes, and normalize only display/comment text needed for this policy. Preserve variable-expanded Unicode browser/profile paths and preset/config strings; source encoding policy does not mean transliterating user data. A byte scan of the final distributed script must find no byte above 127 if this option is selected. A UTF-8 BOM is a viable competing policy, but it relies on every distribution/rewrite step retaining that marker; choose it only with a byte-preservation gate. Raising the minimum to PS7 transfers avoidable installation work to users and evades the admitted 5.1 contract.

Intermediate acceptance: final file parses on both native hosts before any whole-entry fixture is credited. Keep the pre-repair bytes as the RED discriminator. `ParseInput` remains an explanation control, never the sole acceptance gate.

**2. Repair ordering at the existing selector.** Remove pipeline-separating commas and emit each candidate pipeline as a separate statement inside `@(...)`, or concatenate separately parenthesized arrays. Prefer the former: each complete pipeline contributes zero or more objects in stable order without additional state. Keep `Select-Object -First 1` and exactly one returned object after flattening; diagnostics go through `Write-Host`/warning channels, not the success pipeline. Preserve existing source order within each preference tier.

The retained tier contract is precise:

| Family | Tier precedence | Exclusions |
|---|---|---|
| Chromium | ZIP name matching `chrom(e|ium)`, then a `tabliss*.zip` fallback | Names containing firefox, safari or source |
| Firefox | XPI with signed/firefox in name, then other XPI, then firefox ZIP fallback | Names containing unsigned or source |

These are filename filters. They neither verify a signature nor prove the fallback Firefox ZIP is installable through “Install Add-on From File”. The earlier phrase “signed Firefox requirements” must not become a new cryptographic claim. Retain rejection of explicitly unsigned/source builds and the current preference semantics in this repair. If the owner wants to prohibit generic XPI or ZIP fallback, that needs a separately stated compatibility/security decision; do not silently change those tiers while fixing syntax.

**3. Qualify the consumer without letting catch hide failure.** Invoke `Install-TablissNG` in an effect-stubbed fixture after parsing succeeds. With the valid release fixture, assert `Download-Asset` receives exactly the selected object; Chromium reaches `Expand-ChromiumAsset` with the returned path and Firefox reaches its existing manual path. Replace `Open-TargetUrl`, `Copy-Text`, `Read-Host`, downloads and extraction with in-memory spies. Record which branch ran. Valid assets must never hit the “Falling back” path. Empty/no-match releases may reach fallback, with an honest unavailable diagnostic. Unsupported family remains an error. A network/auth failure remains a network/auth failure, not “installed”.

**4. Update distribution-facing claims as a unit.** Keep the README’s response-string route and the script’s review/download/`-File` route accurate, including the exact supported host and manual action boundary. Change builder Windows command only if its actual invocation changes; do not churn the encoded hash grammar or preset content. IMPLEMENTAUDIT R001D applies to exact distributed bytes and usage prose, not merely a local syntax result. IMPLEMENTAUDIT R001E applies to the native parser fixture and actual selector caller, preventing unused test helpers from standing in for entry qualification.

## Deterministic GREEN and mutation controls

| Fixture | Required result |
|---|---|
| Exact final file on PS5.1 and PS7 | Zero ParseFile errors; explicit UTF-8 control also zero; record host version, file SHA256 and encoding policy. |
| Valid Chromium ZIP + signed Firefox XPI | One object per family with the exact appropriate name and URL; no fallback. |
| Put `tabliss.zip` before `tabliss-chromium.zip` in source array | Chromium-specific tier still wins despite array order. Reverse within one tier to verify stable source order. |
| `source.zip`, `tabliss-firefox-unsigned.xpi`, `safari.zip`, competing family | These never displace a valid same-family asset. Only unsuitable assets produces the existing no-safe-asset error. |
| Empty assets; unsupported `safari`; metadata exception | Defined rejection; stubbed manual store fallback only where the actual caller owns it. No download/open occurs accidentally. |
| Generic XPI / Firefox ZIP only | Explicitly characterize retained fallback selection; do not label signature authenticity or browser installability PASS. |
| Paths/config containing spaces and Unicode | Caller receives unchanged strings, despite ASCII-safe script source. |
| Reinsert comma; restore original BOM-less non-ASCII bytes | Selector and native file gate respectively fail. Neither PS7 parsing nor catch/store success can mask those mutants. |

Whole-file `-File` entry proof needs a disposable, fully effect-stubbed/native environment. Its setup must intercept `New-Item`, profile discovery, web requests, clipboard, process launch, extraction and deletion before top-level execution; do not launch the current installer against the owner’s profiles merely to show that parsing works. Host unavailability is an open native qualification gap, not a skipped PASS.

## Siblings, rollback and DONE

No hard whole-issue predecessor is introduced. [R0016](https://github.com/theislampill/salah_widget/issues/22) already consumes this work’s qualification contract for Windows no-effect preview. Agree the source owner for final `install.ps1` integration: its effect guards must not reintroduce a non-ASCII parsing problem or alter selector output, and this issue must not absorb its dry-run work. [R0013](https://github.com/theislampill/salah_widget/issues/19) owns Bash. Shared README/test insertions use the designated integrator. No new edge or broad platform campaign is needed.

Preserve manual extension installation, explicit dashboard-replacement warning, builder config carry-through, the preset’s 325×530 iframe and permission scope. Roll back the bounded encoding/selector patch and matching tests if a supported artifact path regresses, but remove any unsupported host claim at the same time. Keep actual downloaded/manual assets; no cleanup or profile rollback belongs to this authoring issue. Stop on incompatible drift, absent minimum-host qualification, broken selector controls or unresolved Firefox policy changes.

DONE requires final-tree RED→GREEN/control evidence on both claimed hosts, exact-byte identity, consumer branch proof, and an evidence comment before manual closure. Where publication/distribution is claimed, additionally bind the authorized raw-script readback to those bytes; a local fix does not prove public replacement. Use non-closing `Implements #20` PR wording. A work-order publication, parser success, selected asset, downloaded file and installed extension remain distinct outcomes.

Methodology references (separate repository, not Salah work owners): [R001D in IMPLEMENTAUDIT](https://github.com/theislampill/IMPLEMENTAUDIT.md/issues/155), [R001E in IMPLEMENTAUDIT](https://github.com/theislampill/IMPLEMENTAUDIT.md/issues/157).

Identity provenance: first repository-local allocation batch; existing GitHub object order was used to assign distinct monotonic hex-4 IDs. Closed/held IDs are not reused. Issue number is not implementation priority.


