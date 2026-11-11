#!/usr/bin/env python3
"""Bounded actual PowerShell transaction/failure/mutation controls.

The driver freezes its supplied source and fixture bytes before execution.
It does not edit installers, repositories, branches, profiles, or accounts.
The optional POSIX adapter is explicitly supplemental; native-only mutation
controls remain BLOCKED_NATIVE_HOST on POSIX rather than receiving kill credit.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


PARSER = "exact-file parser and ASCII source"
HEALTHY = "healthy actual download and manual Chromium caller"
CONFIGURED = "targeted configured preset preserves unrelated strings and Unicode"
INTEGER = "large unrelated integer is preserved exactly or refused truthfully"
PUBLICATION = "publication collision preserves predecessor and complete partial"
MID_EXTRACT = "mid-extraction failure preserves predecessor and blocks actual handoff"
PREFLIGHT = "complete archive preflight precedes every delegated member writer"

EXTRA_CASES = r'''
    # Additional R0015 failure controls. These intercept only the declared
    # creation boundaries and always delegate to the exact imported function.
    $script:failureOwnedCreator=(Get-Command New-OwnedStagingFile).ScriptBlock
    $script:failureDirectoryCreator=(Get-Command New-PrivateStagingDirectory).ScriptBlock
    $script:failureMode=''
    $script:failureMemberCount=0
    $script:failureCollision=$null
    $script:failureWatchRoot=$null
    $script:failureMemberWrites=@()
    function New-OwnedStagingFile([string]$Parent,[string]$Name) {
        $proposed=Join-Path $Parent $Name
        if ($script:failureWatchRoot -and $proposed.StartsWith($script:failureWatchRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
            $script:failureMemberWrites += [pscustomobject]@{kind='file';path=$proposed}
        }
        if ($script:failureMode -eq 'mid-extraction' -and $Parent.StartsWith((Join-Path $script:StagingAttempt.Retained.Path 'unpacked-'),[StringComparison]::OrdinalIgnoreCase)) {
            $script:failureMemberCount++
            if ($script:failureMemberCount -eq 2) { throw [IO.IOException]::new('fixture second-member creation failure') }
        }
        $path=& $script:failureOwnedCreator $Parent $Name
        if ($script:failureMode -eq 'publication' -and $Parent -ceq $script:DownloadRoot -and $Name.EndsWith('.partial')) {
            $token=[IO.Path]::GetFileNameWithoutExtension($Name)
            $collision=& $script:failureOwnedCreator $Parent ($token+'-tabliss-chromium.zip')
            [IO.File]::WriteAllText($collision,'publication collision sentinel',$script:utf8)
            $script:failureCollision=$collision
        }
        return $path
    }
    function New-PrivateStagingDirectory([string]$Path) {
        if ($script:failureWatchRoot -and $Path.StartsWith($script:failureWatchRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
            $script:failureMemberWrites += [pscustomobject]@{kind='directory';path=$Path}
        }
        return & $script:failureDirectoryCreator $Path
    }

    Invoke-Case 'publication collision preserves predecessor and complete partial' {
        $asset=New-Case 'publication-collision' $goodBytes
        $oldArchive=Assert-OnePath @(Download-Asset $asset) 'Predecessor archive'
        $oldBundle=Assert-OnePath @(Expand-ChromiumAsset $oldArchive) 'Predecessor bundle'
        $sentinel=Join-Path $oldBundle 'previous-browser-consumer.txt'
        [IO.File]::WriteAllText($sentinel,'previous consumer stays usable',$script:utf8)
        $oldFiles=@()
        foreach($file in @(Get-ChildItem -LiteralPath $oldBundle -Recurse -File)) {
            $oldFiles += [pscustomobject]@{path=$file.FullName;hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
        }
        $oldArchiveHash=(Get-FileHash -LiteralPath $oldArchive -Algorithm SHA256).Hash
        $other=New-TestAsset 102 $secondBytes 'b'
        $script:releaseFixture=[pscustomobject]@{id=201;tag_name='v-fixture';assets=@($other)}
        $script:LatestRelease=$script:releaseFixture
        Set-DownloadPlan @((New-DownloadStep $secondBytes))
        $script:caseEvents=@()
        $script:failureCollision=$null
        $script:failureMode='publication'
        try {$null=Install-TablissNG $script:targetFixture} finally {$script:failureMode=''}
        $failed=@($script:StagingAttempt.Artifacts|Where-Object{$_.Kind -eq 'asset'}|Select-Object -Last 1)[0]
        $script:caseNotes.failed=[pscustomobject]@{state=$failed.State;path=$failed.Path;partial=$failed.PublicationCandidate;reason=$failed.Failure}
        $script:caseNotes.collision=$script:failureCollision
        Assert-Case ($failed.State -ceq 'publication-failed' -and -not $failed.Path) 'Publication failure produced a ready record or wrong state.'
        Assert-Case ($failed.PublicationCandidate -and [IO.File]::Exists($failed.PublicationCandidate)) 'Publication copy was not reached before the controlled collision.'
        Assert-Case ((Get-FileHash -LiteralPath $failed.PublicationCandidate -Algorithm SHA256).Hash.ToLowerInvariant() -ceq (Get-BytesHash $secondBytes)) 'Failure was earlier than the complete retained copy.'
        Assert-Case ([IO.File]::ReadAllText($script:failureCollision,[Text.Encoding]::UTF8) -ceq 'publication collision sentinel') 'Publication overwrote its preexisting collision sentinel.'
        Assert-Case ((Get-FileHash -LiteralPath $oldArchive -Algorithm SHA256).Hash -ceq $oldArchiveHash) 'Publication failure changed predecessor archive bytes.'
        foreach($file in $oldFiles) {Assert-Case ([IO.File]::Exists($file.path) -and (Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash -ceq $file.hash) 'Publication failure changed predecessor manifest, payload or sentinel.'}
        Assert-Case (-not @($script:caseEvents|Where-Object{$_.effect -eq 'copy'}).Count) 'Publication failure reached the actual clipboard handoff.'
        Assert-Case (@($script:caseEvents|Where-Object{$_.effect -eq 'open' -and $_.value -eq 'https://fixture.invalid/store'}).Count -eq 1) 'Publication failure did not reach actual truthful fallback.'
    }

    Invoke-Case 'mid-extraction failure preserves predecessor and blocks actual handoff' {
        $asset=New-Case 'mid-extraction' $goodBytes
        $archive=Assert-OnePath @(Download-Asset $asset) 'Predecessor archive'
        $oldBundle=Assert-OnePath @(Expand-ChromiumAsset $archive) 'Predecessor bundle'
        $sentinel=Join-Path $oldBundle 'previous-browser-consumer.txt'
        [IO.File]::WriteAllText($sentinel,'previous consumer stays usable',$script:utf8)
        $oldFiles=@()
        foreach($file in @(Get-ChildItem -LiteralPath $oldBundle -Recurse -File)) {
            $oldFiles += [pscustomobject]@{path=$file.FullName;hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
        }
        $archiveHash=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
        $script:caseEvents=@()
        $script:failureMemberCount=0
        $script:failureMode='mid-extraction'
        try {$null=Install-TablissNG $script:targetFixture} finally {$script:failureMode=''}
        $failed=@($script:StagingAttempt.Artifacts|Where-Object{$_.Kind -eq 'unpacked'}|Select-Object -Last 1)[0]
        $partialManifest=Join-Path $failed.ExtractionRoot 'extension/manifest.json'
        $script:caseNotes.failed=[pscustomobject]@{state=$failed.State;path=$failed.Path;root=$failed.ExtractionRoot;reason=$failed.Failure;memberCalls=$script:failureMemberCount}
        Assert-Case ($script:failureMemberCount -eq 2 -and [IO.File]::Exists($partialManifest)) 'The controlled failure did not occur after the first actual output member.'
        Assert-Case ($failed.State -ceq 'extraction-failed' -and -not $failed.Path) 'Mid-output failure produced a ready record or wrong state.'
        Assert-Case ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ceq $archiveHash) 'Extraction failure changed the predecessor archive.'
        foreach($file in $oldFiles) {Assert-Case ([IO.File]::Exists($file.path) -and (Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash -ceq $file.hash) 'Extraction failure changed predecessor manifest, payload or sentinel.'}
        Assert-Case (-not @($script:caseEvents|Where-Object{$_.effect -eq 'copy'}).Count) 'Mid-output failure reached actual clipboard handoff.'
        Assert-Case (@($script:caseEvents|Where-Object{$_.effect -eq 'open' -and $_.value -eq 'https://fixture.invalid/store'}).Count -eq 1) 'Mid-output failure did not reach actual truthful fallback.'
    }

    Invoke-Case 'complete archive preflight precedes every delegated member writer' {
        $null=New-Case 'preflight-writer-spy' $goodBytes
        $unsafe=New-TestZip @(
            [pscustomobject]@{name='extension/manifest.json';text=$manifest},
            [pscustomobject]@{name='extension/early-marker.txt';text='must not create a member before complete preflight'},
            [pscustomobject]@{name='../late-escape.txt';text='invalid final member'}
        )
        $candidate=New-OwnedStagingFile $WorkRoot 'unsafe-preflight.zip'
        [IO.File]::WriteAllBytes($candidate,$unsafe)
        $root=Join-Path $script:StagingAttempt.Retained.Path 'preflight-probe'
        $null=New-PrivateStagingDirectory $root
        # Root allocation is setup, not member extraction. Watch only after the
        # fresh empty root exists. All member writers in the exact function call
        # these delegated creation boundaries; no extraction implementation is mocked.
        $script:failureWatchRoot=$root
        $script:failureMemberWrites=@()
        try {$observed=Invoke-Captured {Test-ExtensionArchive $candidate $root}} finally {$script:failureWatchRoot=$null}
        $script:caseNotes.preflight=$observed
        $script:caseNotes.memberWriters=@($script:failureMemberWrites)
        Assert-Case (-not [string]::IsNullOrWhiteSpace($observed.error)) 'Actual archive validator accepted the unsafe late member.'
        Assert-Case ($script:failureMemberWrites.Count -eq 0) 'A production member writer was reached before complete archive preflight.'
        Assert-Case ([IO.Directory]::GetFileSystemEntries($root).Length -eq 0) 'Unsafe archive left member output.'
        Assert-Case (-not [IO.File]::Exists((Join-Path $script:StagingAttempt.Retained.Path 'late-escape.txt'))) 'Unsafe archive escaped its extraction root.'
    }
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def psq(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def json_output(stdout: str) -> dict:
    stripped = stdout.lstrip("\ufeff").strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        index = stripped.rfind("\n{")
        if index < 0:
            raise
        return json.loads(stripped[index + 1 :])


def section_replace(source: str, function: str, old: str, new: str) -> str:
    start_match = re.search(rf"(?m)^function {re.escape(function)}(?:\(|\s*\{{)", source)
    if not start_match:
        raise ValueError(f"Missing production function: {function}")
    end_match = re.search(r"(?m)^function ", source[start_match.end() :])
    end = start_match.end() + end_match.start() if end_match else len(source)
    body = source[start_match.start() : end]
    count = body.count(old)
    if count != 1:
        raise ValueError(f"{function} expected one mutation anchor, found {count}")
    return source[: start_match.start()] + body.replace(old, new, 1) + source[end:]


def make_mutant(source: str, mechanism: str) -> str:
    if mechanism == "existence-only-cache":
        anchor = "    foreach ($previous in @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'asset' -and $_.Source -ceq $source -and $_.State -in @('published','handed-off')})) {"
        injection = r"""    foreach ($candidateHit in @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'asset' -and $_.Source -ceq $source})) {
        if ($candidateHit.Path -and (Test-Path -LiteralPath $candidateHit.Path)) { return $candidateHit.Path }
        if ($candidateHit.Candidate -and (Test-Path -LiteralPath $candidateHit.Candidate)) { return $candidateHit.Candidate }
    }
"""
        return section_replace(source, "Download-Asset", anchor, injection + anchor)
    if mechanism == "direct-write-to-ready":
        anchor = "    $record.Candidate=New-OwnedStagingFile $WorkRoot ('download-'+[guid]::NewGuid().ToString('N')+'.partial')"
        injection = r"""    $readyOverwrite=@($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'asset' -and $_.Path -and $_.State -in @('published','handed-off')} | Select-Object -Last 1)
    if ($readyOverwrite.Count) { $record.Candidate=$readyOverwrite[0].Path }
    else { $record.Candidate=New-OwnedStagingFile $WorkRoot ('download-'+[guid]::NewGuid().ToString('N')+'.partial') }"""
        return section_replace(source, "Download-Asset", anchor, injection)
    if mechanism == "delete-predecessor-before-validation":
        anchor = "    $archiveRecord=Get-AdmittedArtifact $ZipPath 'asset'"
        injection = r"""    foreach ($oldBundle in @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'unpacked' -and $_.ExtractionRoot -and $_.Path})) {
        if (Test-Path -LiteralPath $oldBundle.ExtractionRoot) { Remove-Item -LiteralPath $oldBundle.ExtractionRoot -Recurse -Force }
    }
"""
        return section_replace(source, "Expand-ChromiumAsset", anchor, injection + anchor)
    if mechanism == "delete-predecessor-after-success":
        anchor = "        return $path"
        injection = r"""        foreach ($oldBundle in @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'unpacked' -and $_.ExtractionRoot -and $_.Path -and $_.Path -cne $path})) {
            if (Test-Path -LiteralPath $oldBundle.ExtractionRoot) { Remove-Item -LiteralPath $oldBundle.ExtractionRoot -Recurse -Force }
        }
"""
        return section_replace(source, "Expand-ChromiumAsset", anchor, injection + anchor)
    if mechanism == "parse-warning-with-ready-path":
        mutated = section_replace(
            source, "Download-Preset", "        $configured=Convert-ConfiguredPreset $raw",
            "        try { $configured=Convert-ConfiguredPreset $raw } catch { Write-Warn 'mutant: preset parse warning'; $configured=$raw }",
        )
        return section_replace(
            mutated, "Download-Preset", "        $null=Get-CanonicalPresetShape $readback",
            "        try { $null=Get-CanonicalPresetShape $readback } catch { Write-Warn 'mutant: preset revalidation warning' }",
        )
    if mechanism == "global-string-replacement":
        return section_replace(
            source, "Convert-ConfiguredPreset",
            "    $updated=$Raw.Substring(0,$shape.Token.Start)+$serialized+$Raw.Substring($shape.Token.Start+$shape.Token.Length)",
            "    $updated=$Raw.Replace('local=1',[Security.SecurityElement]::Escape($fragment))",
        )
    if mechanism == "foreign-root-cleanup":
        return section_replace(
            source, "Clear-OwnedScratch",
            "        $null = Assert-OwnedStagingPath $attempt.Scratch.Path\n        $null = @(Get-OwnedStagingFiles $attempt.Scratch.Path)",
            "        # mutant: delete the remembered pathname without current custody readback",
        )
    if mechanism == "dry-run-pretend-ready":
        return section_replace(
            source, "Download-Asset",
            '    if ($DryRun) { throw "Offline preview does not download or return cached asset paths." }',
            "    if ($DryRun) { return @($script:StagingAttempt.Artifacts | Where-Object {$_.Kind -eq 'asset' -and $_.Path} | Select-Object -First 1)[0].Path }",
        )
    if mechanism == "success-pipeline-diagnostic":
        return section_replace(
            source, "Download-Asset",
            "    try { return Publish-OwnedFile $record $DownloadRoot (Sanitize-FilePart $Asset.name) }",
            "    try { Write-Output 'mutant success-stream diagnostic'; return Publish-OwnedFile $record $DownloadRoot (Sanitize-FilePart $Asset.name) }",
        )
    raise ValueError(f"Unknown mechanism: {mechanism}")


SPECS = [
    {"name": "existence-only-cache", "target": "partial download is not a ready cache hit and healthy retry recovers", "positive": HEALTHY, "error": "Retry after interrupted acquisition returned a usable-looking path"},
    {"name": "direct-write-to-ready", "target": "same filename with changed source identity must reacquire", "positive": HEALTHY, "error": "Changed source overwrote the predecessor archive"},
    {"name": "delete-predecessor-before-validation", "target": "failed replacement preserves already handed-off bundle", "positive": HEALTHY, "error": "Failed replacement deleted the previously handed-off bundle"},
    {"name": "delete-predecessor-after-success", "target": "successful restaging preserves already handed-off bundle", "positive": HEALTHY, "error": "Successful restaging deleted the previously handed-off bundle"},
    {"name": "parse-warning-with-ready-path", "target": "malformed preset has no ready path or actual import handoff", "positive": CONFIGURED, "error": "Malformed preset returned a usable-looking path", "require_target_copy": True},
    {"name": "global-string-replacement", "target": CONFIGURED, "positive": INTEGER, "error": "Configuration rewrite changed an unrelated local=1/Unicode string", "require_positive_copy": True},
    {"name": "foreign-root-cleanup", "target": "native cleanup refuses a replaced root identity", "positive": "native cleanup holds ancestors and retains fresh-consumer output", "error": r"ReadAllText|Could not find|cannot find|Cleanup deleted", "native": True},
    {"name": "dry-run-pretend-ready", "target": "dry helpers refuse warm cache and all artifact effects", "positive": HEALTHY, "error": "Dry warm-cache download returned a usable-looking path"},
    {"name": "success-pipeline-diagnostic", "target": HEALTHY, "positive": CONFIGURED, "error": "Download-Asset did not return one clean string path"},
]


def invoke_pwsh(pwsh: Path, code: str, prefix: Path, timeout: int = 180) -> dict:
    # Bind both sides of the receipt transport. Windows' parent locale must not
    # reinterpret UTF-8 Unicode fixture paths as cp1252 text.
    code = "[Console]::OutputEncoding=New-Object Text.UTF8Encoding $false;\n" + code
    encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
    started = time.monotonic()
    command = [str(pwsh), "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        for stream, raw in (("stdout", error.stdout or b""), ("stderr", error.stderr or b"")):
            prefix.with_suffix("." + stream + ".bin").write_bytes(raw)
            prefix.with_suffix("." + stream + ".txt").write_text(raw.decode("utf-8", errors="replace"), encoding="utf-8")
        return {"exit": None, "status": "ACQUISITION_TIMEOUT", "seconds": time.monotonic() - started}
    prefix.with_suffix(".stdout.bin").write_bytes(result.stdout)
    prefix.with_suffix(".stderr.bin").write_bytes(result.stderr)
    try:
        stdout = result.stdout.decode("utf-8-sig")
        stderr = result.stderr.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return {"exit": result.returncode, "status": "INVALID_UTF8_RECEIPT", "error": str(error), "seconds": time.monotonic() - started}
    prefix.with_suffix(".stdout.txt").write_text(stdout, encoding="utf-8")
    prefix.with_suffix(".stderr.txt").write_text(stderr, encoding="utf-8")
    try:
        receipt = json_output(stdout)
        prefix.with_suffix(".json").write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except (ValueError, json.JSONDecodeError) as error:
        return {"exit": result.returncode, "status": "INVALID_RECEIPT", "error": str(error), "seconds": time.monotonic() - started}
    return {"exit": result.returncode, "status": "OBSERVED", "seconds": time.monotonic() - started, "receipt": receipt}


def fixture_code(test: Path, source: Path, preset: Path, cases: list[str], posix: bool, native: bool = False) -> str:
    code = "& " + psq(test) + " -SourceFile " + psq(source)
    # The child already creates its own full-UUID/Unicode fixture. Keep it next
    # to the driver root, avoiding an extra path component in native Win32 calls.
    # Each returned child root is explicitly retained through auxiliaryFixtures.
    code += " -FixtureParent " + psq(test.parent.parent)
    if not native:
        code += " -PresetFile " + psq(preset)
        if posix:
            code += " -UsePosixNativeAdapter"
    code += " -Case @(" + ",".join(psq(case) for case in cases) + ")"
    return code


def rows_by_case(run: dict) -> dict:
    return {row["case"]: row for row in run.get("receipt", {}).get("results", [])}


def passed(row: dict | None) -> bool:
    return bool(row and row.get("pass_", row.get("pass", False)))


def copy_count(row: dict | None) -> int:
    return sum(event.get("effect") == "copy" for event in (row or {}).get("events", []))


def retain_child_fixture(run: dict, roots: list[str], parent: Path) -> dict:
    """Admit only an actual, direct child of the declared disposable parent."""
    if run.get("status") != "OBSERVED":
        return run
    try:
        receipt = run.get("receipt")
        if not isinstance(receipt, dict):
            raise ValueError("Child fixture receipt is not an object")
        candidate = receipt.get("fixtureRoot")
        if not isinstance(candidate, str) or not candidate:
            raise ValueError("Missing actual child fixture root")
        path = Path(candidate)
        facts = path.lstat()
        if (not path.is_absolute() or path.is_symlink()
                or getattr(facts, "st_file_attributes", 0) & 0x400
                or not path.is_dir() or path.resolve().parent != parent.resolve()):
            raise ValueError("Child fixture is not a regular direct disposable child")
    except (OSError, ValueError) as error:
        run["status"] = "INVALID_FIXTURE_RECEIPT"
        run["fixtureError"] = str(error)
        # Raw bytes and the parsed JSON remain on disk. Exclude unadmitted
        # observations from baseline/mutation credit, retaining them separately.
        run["unqualifiedReceipt"] = run.pop("receipt", None)
        return run
    if candidate not in roots:
        roots.append(candidate)
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--preset", type=Path, required=True)
    parser.add_argument("--native-test", type=Path, required=True)
    parser.add_argument("--pwsh", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-source-sha")
    parser.add_argument("--posix-native-adapter", action="store_true")
    parser.add_argument("--mutant", action="append", choices=[spec["name"] for spec in SPECS])
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    if os.name == "nt" and args.posix_native_adapter:
        parser.error("The POSIX native-boundary adapter is forbidden on native Windows.")
    args.out.mkdir(parents=True, exist_ok=False)
    source_bytes = args.source.read_bytes()
    source_sha = sha(source_bytes)
    if args.expect_source_sha and source_sha != args.expect_source_sha:
        raise SystemExit("Exact source hash differs from the requested freeze.")
    source_text = source_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    baseline_source = args.out / "source.ps1"
    baseline_source.write_bytes(source_bytes)
    base_test_bytes = args.test.read_bytes()
    base_test = base_test_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    marker = "    Invoke-Case 'dry helpers refuse warm cache and all artifact effects' {"
    if base_test.count(marker) != 1:
        raise SystemExit("Failure-control harness insertion boundary is not unique.")
    derived_test = args.out / "failure-controls.ps1"
    derived_test.write_bytes(base_test.replace(marker, EXTRA_CASES + "\n" + marker, 1).encode("utf-8"))
    native_test = args.out / "native-controls.ps1"
    native_test.write_bytes(args.native_test.read_bytes())
    preset = args.out / "canonical-preset.json"
    preset.write_bytes(args.preset.read_bytes())
    selected = [spec for spec in SPECS if not args.mutant or spec["name"] in args.mutant]
    report = {
        "schema": "r0015-actual-powershell-mutations-v1",
        "fixture": str(args.out.resolve()),
        "auxiliaryFixtures": [],
        "childFixtureParent": str(args.out.parent.resolve()),
        "sourcePath": str(args.source.resolve()),
        "sourceSha256": source_sha,
        "driverSha256": sha(Path(__file__).read_bytes()),
        "baseTestSha256": sha(base_test_bytes),
        "derivedTestSha256": sha(derived_test.read_bytes()),
        "nativeTestSha256": sha(native_test.read_bytes()),
        "presetSha256": sha(preset.read_bytes()),
        "nativeBoundaryAdapter": args.posix_native_adapter,
        "scope": "native Windows" if os.name == "nt" else "supplemental POSIX boundary adapter; native Windows cleanup mutation remains unqualified",
        "failureControls": [],
        "mutations": [],
    }
    def finish_report():
        report["results"] = report["failureControls"] + report["mutations"]
        (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)
    core_cases = [PARSER, HEALTHY, CONFIGURED, PUBLICATION, MID_EXTRACT, PREFLIGHT]
    for spec in selected:
        if not spec.get("native"):
            core_cases += [spec["target"], spec["positive"]]
    core_cases = list(dict.fromkeys(core_cases))
    control_run = invoke_pwsh(args.pwsh, fixture_code(derived_test, baseline_source, preset, core_cases, args.posix_native_adapter), args.out / "baseline-controls")
    retain_child_fixture(control_run, report["auxiliaryFixtures"], args.out.parent)
    controls = rows_by_case(control_run)
    controls_good = control_run.get("status") == "OBSERVED" and control_run.get("exit") == 0 and set(core_cases).issubset(controls) and all(passed(controls[case]) for case in core_cases)
    report["failureControls"] = [{"case": case, "pass_": passed(controls.get(case)), "result": controls.get(case)} for case in core_cases]
    report["baselineStatus"] = "PASS" if controls_good else "FAIL_OR_ACQUISITION_GAP"
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"phase": "actual baseline and failure controls", "status": report["baselineStatus"], "cases": len(core_cases)}), flush=True)
    if not controls_good:
        report["complete"] = False
        finish_report()
        return 1
    if args.controls_only:
        report["complete"] = True
        finish_report()
        return 0
    native_baseline = None
    for index, spec in enumerate(selected, 1):
        row = {"mechanism": spec["name"], "targetCase": spec["target"], "positiveCase": spec["positive"], "pass_": False}
        if spec.get("native") and os.name != "nt":
            row.update(status="BLOCKED_NATIVE_HOST", reason="Foreign-root cleanup requires the actual native Windows identity/lease fixture. No POSIX kill is credited.")
            report["mutations"].append(row)
            print(json.dumps(row), flush=True)
            continue
        if spec.get("native") and native_baseline is None:
            native_baseline = invoke_pwsh(args.pwsh, fixture_code(native_test, baseline_source, preset, [spec["target"], spec["positive"]], False, True), args.out / "native-baseline")
            retain_child_fixture(native_baseline, report["auxiliaryFixtures"], args.out.parent)
        if spec.get("native"):
            native_rows = rows_by_case(native_baseline)
            if native_baseline.get("exit") != 0 or not passed(native_rows.get(spec["target"])) or not passed(native_rows.get(spec["positive"])):
                row.update(status="BLOCKED_NATIVE_BASELINE", reason="Native healthy/adverse controls did not first pass on the exact unmutated source.")
                report["mutations"].append(row)
                print(json.dumps(row), flush=True)
                continue
        try:
            mutant_text = make_mutant(source_text, spec["name"])
        except ValueError as error:
            row.update(status="MUTANT_BUILD_ERROR", error=str(error))
            report["mutations"].append(row)
            print(json.dumps(row), flush=True)
            continue
        mutant = args.out / f"mutant-{index:02}.ps1"
        mutant.write_bytes(mutant_text.encode("utf-8"))
        row["sourceSha256"] = sha(mutant.read_bytes())
        parse_code = "$t=$null;$e=$null;$null=[Management.Automation.Language.Parser]::ParseFile(" + psq(mutant) + ",[ref]$t,[ref]$e);[pscustomobject]@{errors=@($e|ForEach-Object{$_.Message});runtime=$PSVersionTable.PSVersion.ToString()}|ConvertTo-Json -Depth 5;if(@($e).Count){exit 1}"
        parsed = invoke_pwsh(args.pwsh, parse_code, args.out / f"parse-{index:02}")
        row["parsePass"] = parsed.get("exit") == 0 and parsed.get("status") == "OBSERVED" and not parsed.get("receipt", {}).get("errors")
        if not row["parsePass"]:
            row.update(status="INVALID_MUTANT_PARSE")
            report["mutations"].append(row)
            print(json.dumps(row), flush=True)
            continue
        native = bool(spec.get("native"))
        cases = [spec["target"], spec["positive"]] if native else [PARSER, spec["target"], spec["positive"]]
        observed = invoke_pwsh(args.pwsh, fixture_code(native_test if native else derived_test, mutant, preset, cases, args.posix_native_adapter and not native, native), args.out / f"run-{index:02}")
        retain_child_fixture(observed, report["auxiliaryFixtures"], args.out.parent)
        actual_rows = rows_by_case(observed)
        target = actual_rows.get(spec["target"])
        positive = actual_rows.get(spec["positive"])
        row["target"] = target
        row["positive"] = positive
        row["targetFailedForIntendedReason"] = bool(target and not passed(target) and re.search(spec["error"], str(target.get("error", "")), re.I))
        row["healthyPositivePassed"] = passed(positive)
        row["observedExit"] = observed.get("exit")
        row["actualTargetCopies"] = copy_count(target)
        row["actualPositiveCopies"] = copy_count(positive)
        qualified = row["targetFailedForIntendedReason"] and row["healthyPositivePassed"] and observed.get("exit") == 1
        if not native:
            qualified = qualified and passed(actual_rows.get(PARSER))
        if spec.get("require_target_copy"):
            qualified = qualified and row["actualTargetCopies"] >= 1
        if spec.get("require_positive_copy"):
            qualified = qualified and row["actualPositiveCopies"] >= 1
        row["pass_"] = bool(qualified)
        row["status"] = "KILLED_WITH_HEALTHY_CONTROL" if qualified else "NOT_QUALIFIED"
        report["mutations"].append(row)
        (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: value for key, value in row.items() if key not in {"target", "positive"}}), flush=True)
    report["complete"] = len(report["mutations"]) == len(selected) and all(row["pass_"] for row in report["mutations"])
    report["qualifiedKills"] = sum(row["pass_"] for row in report["mutations"])
    report["blocked"] = sum(row["status"].startswith("BLOCKED") for row in report["mutations"])
    finish_report()
    if report["complete"]:
        return 0
    return 2 if report["blocked"] and all(row["pass_"] or row["status"].startswith("BLOCKED") for row in report["mutations"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
