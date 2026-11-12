#!/usr/bin/env python3
"""Bounded native diagnosis of measured R0015 compiler/path failures.

This records experiments, not qualification. The unchanged installer is loaded
only by the companion probe into separately owned disposable case roots.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Windows":
        parser.error("This diagnostic requires an actual Windows host")
    if args.archive:
        out = args.output.resolve()
        if not out.is_dir():
            parser.error("No diagnostic evidence directory exists")
        acquisition_error = None
        try:
            report = json.loads((out / "result.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            report = {"commands": []}
            acquisition_error = repr(error)
        # Preserve raw output even if the runner never wrote a final receipt.
        with tarfile.open(out.with_suffix(".tar.gz"), "w:gz", dereference=False) as archive:
            archive.add(out, arcname="installer-diagnostic")
            for row in report.get("commands", []):
                case = Path(row["fixture"])
                if case.parent.resolve() != Path(tempfile.gettempdir()).resolve() or not case.name.startswith("r15d-"):
                    raise RuntimeError("Fixture inventory escaped the diagnostic parent")
                if case.is_dir() and not case.is_symlink():
                    archive.add(case, arcname="fixtures/" + row["host"] + "-" + row["mode"])
        print(json.dumps({"archive": str(out.with_suffix(".tar.gz")), "receiptError": acquisition_error,
                          "qualification": False}))
        return 0 if acquisition_error is None else 1
    repo = Path(__file__).resolve().parents[2]
    source = repo / "install.ps1"
    probe = Path(__file__).with_name("windows_installer_probe.ps1")
    frozen = {str(p.relative_to(repo)): sha(p) for p in (source, probe, Path(__file__))}
    out = args.output.resolve()
    out.mkdir(parents=False, exist_ok=False)
    env = os.environ.copy()
    env.update(POWERSHELL_TELEMETRY_OPTOUT="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
               POWERSHELL_UPDATECHECK="Off")
    hosts = {"ps51": Path(env["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe",
             "ps7": Path(env["INSTALL_TEST_PS7"])}
    # A separate subject root is created by each child; the runner never changes
    # permissions of any preexisting parent or browser profile.
    rows = []
    result = {"schema": "r0015-windows-diagnosis.v1", "qualification": False,
              "host": platform.platform(), "inputs": frozen, "inputsStable": None,
              "complete": False, "commands": rows,
              "scope": "Native diagnostic observations only; no RLGWO acceptance."}
    def checkpoint() -> None:
        temporary = out / "result.pending.json"
        temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        temporary.replace(out / "result.json")
    checkpoint()
    for host, executable in hosts.items():
        for index, mode in enumerate(("compiler-ascii", "compiler-unicode", "path-length")):
            case = Path(tempfile.gettempdir()).resolve() / ("r15d-" + host + "-" + str(index) + "-" + os.urandom(8).hex())
            receipt = case / "result.json"
            command = [str(executable), "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(probe),
                       "-SourceFile", str(source), "-OutputRoot", str(case), "-Mode", mode,
                       "-ResultFile", str(receipt)]
            start = time.monotonic()
            row = {"host": host, "mode": mode, "command": command, "fixture": str(case),
                   "receipt": str(receipt), "status": "running",
                   "startedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            rows.append(row)
            checkpoint()
            acquisition_error = None
            try:
                child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       env=env, timeout=240, check=False)
                stdout, stderr, exit_code, timed_out = child.stdout, child.stderr, child.returncode, False
            except subprocess.TimeoutExpired as error:
                stdout, stderr, exit_code, timed_out = error.stdout or b"", error.stderr or b"", None, True
            except OSError as error:
                stdout, stderr, exit_code, timed_out = b"", b"", None, False
                acquisition_error = repr(error)
            (out / (host + "-" + mode + ".stdout.bin")).write_bytes(stdout)
            (out / (host + "-" + mode + ".stderr.bin")).write_bytes(stderr)
            receipt_hash = None
            if receipt.is_file() and not receipt.is_symlink():
                receipt_bytes = receipt.read_bytes()
                (out / (host + "-" + mode + ".json")).write_bytes(receipt_bytes)
                receipt_hash = hashlib.sha256(receipt_bytes).hexdigest()
            row.update(exit=exit_code, timeout=timed_out, seconds=round(time.monotonic() - start, 3),
                       receiptExists=receipt.is_file(), receiptSha256=receipt_hash, acquisitionError=acquisition_error,
                       status="captured", parentProcessTerminal=exit_code is not None,
                       descendantsIndependentlyMonitored=False,
                       finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            checkpoint()
            # Original retained subject trees are archived as opaque tar members
            # by the job packager; they are never recursively cleaned up here.
    stable = all(sha(repo / name) == value for name, value in frozen.items())
    result.update(inputsStable=stable, complete=True)
    checkpoint()
    print(json.dumps(result, indent=2))
    return 0 if stable and all(r["exit"] == 0 and r["receiptExists"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
