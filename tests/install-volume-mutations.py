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


def terminal_receipt(text: str) -> dict:
    """Use the collector's framing: host messages may precede a terminal object."""
    decoder = json.JSONDecoder()
    for offset, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, end = decoder.raw_decode(text[offset:])
        except ValueError:
            continue
        if not text[offset + end:].strip() and isinstance(value, dict):
            return value
    raise ValueError("no terminal structured receipt")


def validate_receipt(value: dict, source_hash: str, test_hash: str) -> None:
    """Admit the fixture's existing typed evidence before evaluating mutants."""
    if value.get("schema") != "r0015-volume-admission-policy.v1":
        raise ValueError("unexpected volume receipt schema")
    for key in ("pass", "nativeWindows", "sourceUnchanged", "testUnchanged",
                "normalizedPolicyEqual", "healthyControlsPass"):
        if type(value.get(key)) is not bool:
            raise ValueError(f"receipt {key} is not Boolean")
    if (value.get("sourceSha256") != source_hash or value.get("testSha256") != test_hash
            or value["sourceUnchanged"] is not True or value["testUnchanged"] is not True
            or value["normalizedPolicyEqual"] is not True):
        raise ValueError("receipt source/test identity or stability differs")
    rows = value.get("results")
    if not isinstance(rows, list) or len(rows) != 13 or any(not isinstance(row, dict) for row in rows):
        raise ValueError("receipt does not contain the thirteen declared rows")
    cases = {
        "reported NTFS": ("NTFS", True), "reported ReFS": ("ReFS", False),
        "reported unknown filesystem": ("", False),
        "reported unsupported filesystem": ("OtherFS", False),
        "NTFS without persistent ACLs": ("NTFS", False), "volume query failure": ("NTFS", False),
    }
    expected = {f"{language} {case}": facts for language in ("C#", "PowerShell")
                for case, facts in cases.items()}
    policy = [row for row in rows if "expectedAccepted" in row]
    names = [row.get("case") for row in policy]
    if len(policy) != 12 or any(not isinstance(name, str) for name in names) or set(names) != set(expected):
        raise ValueError("policy rows are missing, duplicated or unexpected")
    for row in policy:
        if any(type(row.get(key)) is not bool for key in
               ("pass", "expectedAccepted", "accepted", "filesystemBufferRequested")):
            raise ValueError("policy row flags are not Boolean")
        if type(row.get("volumeCalls")) is not int or row["volumeCalls"] < 0:
            raise ValueError("policy volume call count is not a nonnegative integer")
        filesystem, accepted = expected[row["case"]]
        if row.get("reportedFilesystem") != filesystem or row["expectedAccepted"] is not accepted:
            raise ValueError("policy row expectations differ from the declared case")
        if row["pass"] is not (row["accepted"] == accepted and row["volumeCalls"] == 1):
            raise ValueError("policy verdict contradicts its observations")
    native_rows = [row for row in rows if "expectedAccepted" not in row]
    native = value.get("nativeNTFSHealthy")
    if len(native_rows) != 1 or native_rows[0].get("case") != "actual NTFS Initialize-Staging positive":
        raise ValueError("actual NTFS control row is missing")
    if value["nativeWindows"]:
        if (not isinstance(native, dict) or type(native.get("pass")) is not bool
                or native.get("sourceSha256") != source_hash or native.get("filesystem") != "NTFS"
                or native_rows[0].get("pass") is not native["pass"]
                or native_rows[0].get("observation") != native
                or any(not isinstance(native.get(key), str) or not native[key]
                       for key in ("scratchIdentity", "retainedIdentity"))
                or native["scratchIdentity"] == native["retainedIdentity"]):
            raise ValueError("actual NTFS control is not bound to this source and distinct roots")
    elif native is not None or native_rows[0].get("pass") is not None or native_rows[0].get("status") != "BLOCKED_NATIVE_HOST":
        raise ValueError("non-Windows receipt misstates its native control")


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
    driver_bytes = Path(__file__).read_bytes()
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
        started = time.monotonic()
        expected_failures = sorted(f"{language} {case}" for case in (
            "reported ReFS", "reported unknown filesystem", "reported unsupported filesystem"))
        stdout = args.output_root / f"{name}.stdout.bin"
        stderr = args.output_root / f"{name}.stderr.bin"
        stdout_bytes, stderr_bytes = b"", b""
        variant = None
        command, failed, healthy = [], [], []
        native, native_control, child_exit = None, None, None
        typed_path, typed_bytes, acquisition_error = None, None, None
        acquired, good, timed_out = False, False, False
        stage = "prepare-mutant"
        try:
            if source_text.count(removed_guard) != 1:
                raise ValueError(f"Unique actual {language} guard anchor was not found")
            variant = source_text.replace(removed_guard, "", 1).encode("utf-8")
            mutant = args.output_root / f"{name}.ps1"
            write_new(mutant, variant)
            command = [str(args.pwsh), "-NoLogo", "-NoProfile", "-NonInteractive",
                       "-File", str(args.fixture), "-SourceFile", str(mutant),
                       "-OutputRoot", str(args.output_root)]
            stage = "launch-or-wait"
            try:
                child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       timeout=args.timeout_seconds, check=False)
                stdout_bytes, stderr_bytes, child_exit = child.stdout, child.stderr, child.returncode
            except (OSError, subprocess.TimeoutExpired) as error:
                stdout_bytes = getattr(error, "stdout", None) or b""
                stderr_bytes = getattr(error, "stderr", None) or b""
                timed_out = isinstance(error, subprocess.TimeoutExpired)
                acquisition_error = {"stage": stage, "type": type(error).__name__, "message": str(error)}
            stage = "capture-original-streams"
            write_new(stdout, stdout_bytes)
            write_new(stderr, stderr_bytes)
            if acquisition_error is None:
                stage = "parse-terminal-receipt"
                receipt = terminal_receipt(stdout_bytes.decode("utf-8-sig", errors="strict"))
                stage = "validate-terminal-receipt"
                if type(child_exit) is not int:
                    raise ValueError("child exit code is not an integer")
                validate_receipt(receipt, digest(variant), digest(fixture_bytes))
                typed_bytes = (json.dumps(receipt, indent=2) + "\n").encode("utf-8")
                typed_path = args.output_root / f"{name}.receipt.json"
                write_new(typed_path, typed_bytes)
                acquired = True
                policy_rows = [row for row in receipt["results"] if "expectedAccepted" in row]
                failed = sorted(row["case"] for row in policy_rows if row["pass"] is False)
                healthy = [row for row in policy_rows if row["reportedFilesystem"] == "NTFS"]
                native = receipt["nativeWindows"]
                native_control = receipt["nativeNTFSHealthy"]
                good = (
                    child_exit == 1 and receipt["pass"] is False
                    and receipt["sourceSha256"] == digest(variant)
                    and receipt["testSha256"] == digest(fixture_bytes)
                    and receipt["sourceUnchanged"] is True and receipt["testUnchanged"] is True
                    and len(policy_rows) == 12 and failed == expected_failures
                    and all(row["volumeCalls"] == 1 for row in policy_rows)
                    and all(row["filesystemBufferRequested"] is True for row in policy_rows)
                    and len(healthy) == 6 and all(row["pass"] is True for row in healthy)
                    and (not native or native_control is not None and native_control["pass"] is True)
                )
        except Exception as error:
            acquisition_error = {"stage": stage, "type": type(error).__name__, "message": str(error)}
            acquired, good = False, False
        results.append({
            "case": name, "pass": good, "sourceSha256": digest(variant) if variant is not None else None,
            "removedGuard": removed_guard, "childExitCode": child_exit,
            "acquired": acquired, "acquisitionError": acquisition_error, "timedOut": timed_out,
            "status": "MUTANT_DETECTED" if good else "ASSERTION_FAILED" if acquired else "ACQUISITION_FAILED",
            "seconds": round(time.monotonic() - started, 3),
            "expectedFailures": expected_failures, "observedFailures": failed,
            "pairedHealthyControls": [{"case": row["case"], "pass": row["pass"]}
                                      for row in healthy],
            "nativeWindows": native, "nativeNTFSHealthy": native_control,
            "receipt": str(typed_path) if acquired else None,
            "receiptSha256": digest(typed_bytes) if acquired else None,
            "stdout": str(stdout), "stdoutSha256": digest(stdout_bytes),
            "stderr": str(stderr), "stderrSha256": digest(stderr_bytes),
            "command": command,
        })
    stability_errors = []
    def unchanged(path: Path, before: bytes) -> bool:
        try:
            return path.read_bytes() == before
        except OSError as error:
            stability_errors.append({"path": str(path), "type": type(error).__name__, "message": str(error)})
            return False
    source_stable = unchanged(args.source, source_bytes)
    fixture_stable = unchanged(args.fixture, fixture_bytes)
    driver_stable = unchanged(Path(__file__), driver_bytes)
    report = {
        "schema": "r0015-volume-admission-mutants.v1",
        "pass": source_stable and fixture_stable and driver_stable and len(results) == 2 and all(row["pass"] for row in results),
        "source": str(args.source), "sourceSha256": digest(source_bytes),
        "sourceUnchanged": source_stable, "fixture": str(args.output_root.resolve()),
        "fixtureSourceFile": str(args.fixture),
        "fixtureSha256": digest(fixture_bytes), "fixtureUnchanged": fixture_stable,
        "driverSha256": digest(driver_bytes), "driverUnchanged": driver_stable,
        "stabilityErrors": stability_errors, "results": results,
        "scope": "Actual policy decisions under declared volume-response adapters; no unsupported filesystem execution claim.",
        "nativeQualification": "Only actual nativeWindows receipts with successful actual NTFS positive may qualify the native boundary.",
    }
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    write_new(args.output_root / "results.json", encoded)
    print(encoded.decode("utf-8"), end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
