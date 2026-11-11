#!/usr/bin/env python3
"""Bounded actual-source volume-policy mutants; never edits the supplied source."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--pwsh", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source_text = source_bytes.decode("utf-8")
    fixture_bytes = args.fixture.read_bytes()
    args.output_root.mkdir(parents=False, exist_ok=False)
    variants = [
        (
            "csharp-missing-ntfs-guard", "C#",
            '      if (!String.Equals(format.ToString(), "NTFS", StringComparison.OrdinalIgnoreCase)) throw new IOException("Staging requires the supported NTFS filesystem.");\n',
        ),
        (
            "powershell-missing-ntfs-guard", "PowerShell",
            "        if (-not [string]::Equals($format.ToString(),'NTFS',[StringComparison]::OrdinalIgnoreCase)) { throw 'Compiler scratch requires the supported NTFS filesystem.' }\n",
        ),
    ]
    results = []
    for name, language, removed_guard in variants:
        if source_text.count(removed_guard) != 1:
            raise RuntimeError(f"Unique actual {language} guard anchor was not found")
        variant = source_text.replace(removed_guard, "", 1).encode("utf-8")
        mutant = args.output_root / f"{name}.ps1"
        write_new(mutant, variant)
        command = [str(args.pwsh), "-NoLogo", "-NoProfile", "-NonInteractive",
                   "-File", str(args.fixture), "-SourceFile", str(mutant),
                   "-OutputRoot", str(args.output_root)]
        started = time.monotonic()
        child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=args.timeout_seconds, check=False)
        stdout = args.output_root / f"{name}.stdout.json"
        stderr = args.output_root / f"{name}.stderr.txt"
        write_new(stdout, child.stdout)
        write_new(stderr, child.stderr)
        receipt = json.loads(child.stdout.decode("utf-8-sig", errors="strict"))
        policy_rows = [row for row in receipt["results"] if "expectedAccepted" in row]
        expected_failures = sorted(f"{language} {case}" for case in (
            "reported ReFS", "reported unknown filesystem", "reported unsupported filesystem"))
        failed = sorted(row["case"] for row in policy_rows if row["pass"] is False)
        healthy = [row for row in policy_rows if row["reportedFilesystem"] == "NTFS"]
        native = receipt["nativeWindows"]
        native_control = receipt["nativeNTFSHealthy"]
        good = (
            child.returncode == 1 and receipt["pass"] is False
            and receipt["sourceSha256"] == digest(variant)
            and receipt["testSha256"] == digest(fixture_bytes)
            and receipt["sourceUnchanged"] is True and receipt["testUnchanged"] is True
            and len(policy_rows) == 12 and failed == expected_failures
            and all(row["volumeCalls"] == 1 for row in policy_rows)
            and all(row["filesystemBufferRequested"] is True for row in policy_rows)
            and len(healthy) == 6 and all(row["pass"] is True for row in healthy)
            and (not native or native_control is not None and native_control["pass"] is True)
        )
        results.append({
            "case": name, "pass": good, "sourceSha256": digest(variant),
            "removedGuard": removed_guard, "childExitCode": child.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "expectedFailures": expected_failures, "observedFailures": failed,
            "pairedHealthyControls": [{"case": row["case"], "pass": row["pass"]}
                                      for row in healthy],
            "nativeWindows": native, "nativeNTFSHealthy": native_control,
            "receipt": str(stdout), "receiptSha256": digest(child.stdout),
            "stderr": str(stderr), "stderrSha256": digest(child.stderr),
            "command": command,
        })
    source_stable = args.source.read_bytes() == source_bytes
    fixture_stable = args.fixture.read_bytes() == fixture_bytes
    report = {
        "schema": "r0015-volume-admission-mutants.v1",
        "pass": source_stable and fixture_stable and all(row["pass"] for row in results),
        "source": str(args.source), "sourceSha256": digest(source_bytes),
        "sourceUnchanged": source_stable, "fixture": str(args.output_root.resolve()),
        "fixtureSourceFile": str(args.fixture),
        "fixtureSha256": digest(fixture_bytes), "fixtureUnchanged": fixture_stable,
        "driverSha256": digest(Path(__file__).read_bytes()), "results": results,
        "scope": "Actual policy decisions under declared volume-response adapters; no unsupported filesystem execution claim.",
        "nativeQualification": "Only actual nativeWindows receipts with successful actual NTFS positive may qualify the native boundary.",
    }
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    write_new(args.output_root / "results.json", encoded)
    print(encoded.decode("utf-8"), end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
