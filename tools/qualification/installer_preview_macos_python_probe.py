#!/usr/bin/env python3
"""Contained, source-free Apple Python/xcrun discriminator; zero product rows.

Only an AST-selected, digest-pinned bootstrap core is read from the existing
preview harness. No installer source is read, imported, extracted, or executed.
All diagnostic subjects use that unchanged sandbox, subject layout, readiness,
snapshots, network/write-denial controls, and native PTY control.
"""
import argparse
import ast
import gzip
import hashlib
import json
import os
import pathlib
import platform
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace

CORE_SHA256 = "02e7934793b6e371c63cc9af1cf377cc881801fa94463059c1bb7276e71e9e5f"
CORE_FUNCTIONS = {"digest", "require", "snapshot", "darwin_profile", "acquire_host",
                  "fixture", "sandbox_run", "transport_attempts", "evidence",
                  "no_effects", "darwin_denial_readback", "bootstrap"}
CORE_CONSTANTS = {"DENIALS", "READINESS_LINE"}
STREAM_CEILING = 16 * 1024 * 1024
PROGRAM = '''import json, os, sys
with open(sys.argv[1], encoding="utf-8-sig") as source:
    metadata = json.load(source)
print(json.dumps({"schema":"r0016-source-free-python.v1",
"pid":os.getpid(),"parentPid":os.getppid(),"executable":sys.executable,
"version":sys.version,"argv":sys.argv,"metadata":metadata,
"environment":{key:os.environ.get(key) for key in
("PATH","HOME","TMPDIR","PYTHONDONTWRITEBYTECODE","DEVELOPER_DIR")}},sort_keys=True))
'''
DRIVER = 'exec "$1" - "$2" < "$3"'
SUCCESS = "DIAGNOSTIC_SHIM_CACHE_ATTEMPT_DISCRIMINATED"
CASE_NAMES = ("baseline-shim-before", "baseline-direct", "baseline-shim-after",
              "developer-dir-shim", "developer-dir-direct")


def write_json(path, value):
    pathlib.Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def binding(path):
    path = pathlib.Path(path)
    physical = path.resolve(strict=True)
    info = physical.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Expected regular file: " + str(path))
    return {"path": str(path), "physicalPath": str(physical), "bytes": info.st_size,
            "sha256": hashlib.sha256(physical.read_bytes()).hexdigest(),
            "mode": stat.S_IMODE(info.st_mode)}


def fresh(path):
    path = pathlib.Path(path)
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path.resolve(strict=True)


def load_core(harness, expected_sha, output, observer):
    raw = harness.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("Whole preview harness digest differs from reviewed workflow pin")
    text = raw.decode("utf-8")
    selected = []
    found = set()
    for node in ast.parse(text, filename=str(harness)).body:
        name = node.name if isinstance(node, ast.FunctionDef) else None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in CORE_FUNCTIONS | CORE_CONSTANTS:
            if name in found:
                raise ValueError("Duplicated selected core definition: " + name)
            found.add(name)
            selected.append(node)
    if found != CORE_FUNCTIONS | CORE_CONSTANTS:
        raise ValueError("Selected core interface changed")
    core = "\n\n".join(ast.get_source_segment(text, node) for node in selected) + "\n"
    if hashlib.sha256(core.encode()).hexdigest() != CORE_SHA256:
        raise ValueError("Selected sandbox/readiness/snapshot/PTY core changed")
    frozen = fresh(output / "frozen")
    (frozen / "install-preview.exact.py").write_bytes(raw)
    (frozen / "bootstrap-core.extracted.py").write_text(core)
    (frozen / "python-subject.py").write_text(PROGRAM)
    namespace = dict(globals(), __name__="r0016_source_free_core", __file__=str(harness),
                     HOST="Darwin", ROOT=output, ARGS=SimpleNamespace(bash="/bin/bash"),
                     ACQUISITION={}, RESULTS=[], subprocess=observer)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(harness), "exec"), namespace)
    return namespace, frozen


class CaptureObserver:
    """Preserve raw child stdout/stderr without changing commands or environment.

    Files remain open until the direct child exits and its new process group is
    absent. A timeout, excessive output, cleanup, census gap, or residual group
    aborts the diagnostic. No subject is retried outside the sandbox.
    """
    def __init__(self, output):
        self.directory = fresh(output / "observer-runs")
        self.records = []
        self.blocked = False

    def __getattr__(self, key):
        return getattr(subprocess, key)

    def run(self, command, **kwargs):
        if self.blocked:
            raise RuntimeError("A prior capture/lifecycle failure suppresses all remaining subjects")
        if kwargs.pop("capture_output", False) is not True:
            raise ValueError("Unexpected capture interface in pinned core")
        if kwargs.pop("text", False) is not True:
            raise ValueError("Unexpected text interface in pinned core")
        budget = kwargs.pop("timeout", None)
        if type(budget) not in (int, float) or not 0 < budget <= 30:
            raise ValueError("Unexpected subprocess deadline in pinned core")
        kwargs["start_new_session"] = True
        kwargs.setdefault("stdin", subprocess.DEVNULL)
        case = fresh(self.directory / ("%03d" % (len(self.records) + 1)))
        record = {"command": command, "environment": kwargs.get("env"),
                  "budgetSeconds": budget, "returncode": None,
                  "acquisitionComplete": False, "cleanupRequired": False}
        self.records.append(record)
        write_json(case / "plan.json", record)
        started = time.monotonic()
        stdout_path, stderr_path = case / "stdout.raw", case / "stderr.raw"
        process = None
        try:
            with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, **kwargs)
                record["launchPid"] = process.pid
                while True:
                    terminal = process.poll()
                    observed_elapsed = time.monotonic() - started
                    if terminal is not None:
                        record["terminalObservedElapsedSeconds"] = observed_elapsed
                        record["terminalWithinBudget"] = 0 <= observed_elapsed < budget
                        if record["terminalWithinBudget"] is not True:
                            raise TimeoutError("First terminal observation was outside the subject deadline")
                        break
                    if not 0 <= observed_elapsed < budget:
                        raise TimeoutError("Subject exceeded the existing bounded deadline")
                    if stdout_path.stat().st_size + stderr_path.stat().st_size > STREAM_CEILING:
                        raise RuntimeError("Raw stream acquisition exceeded 16 MiB; retained without truncation")
                    time.sleep(0.02)
                record["returncode"] = process.returncode
                if stdout_path.stat().st_size + stderr_path.stat().st_size > STREAM_CEILING:
                    raise RuntimeError("Raw stream acquisition exceeded 16 MiB; retained without truncation")
                census_rows = census(case, "terminal-census", kwargs["env"], time.monotonic() + 2)
                residual = [row for row in census_rows.values() if row["pgid"] == process.pid]
                record["residualOwnedGroup"] = residual
                if residual:
                    raise RuntimeError("Terminal direct child left an owned process group; remaining cases suppressed")
                record["acquisitionComplete"] = True
        except BaseException as error:
            self.blocked = True
            record["error"] = {"type": type(error).__name__, "message": str(error)}
            if process is not None and process.poll() is None:
                record["cleanupRequired"] = True
                cleanup_deadline = time.monotonic() + 6
                record["cleanup"] = force_cleanup(process, case, kwargs["env"], cleanup_deadline - 1)
                record["cleanup"]["topologyCoverage"] = (
                    "Existing no-child or single-fork PTY cleanup only; unsupported xcrun/other topology remains incomplete.")
                try:
                    rows = census(case, "post-cleanup-census", kwargs["env"], cleanup_deadline)
                    known = {row["pid"]: row for row in record["cleanup"].get("known", [])}
                    record["postCleanupCensus"] = {
                        "status": "ACQUIRED",
                        "sameOwnedGroup": [row for row in rows.values() if row["pgid"] == process.pid],
                        "sameKnownIdentities": [row for pid, row in rows.items() if pid in known
                            and all(row[key] == known[pid][key] for key in ("started", "uid", "pgid"))],
                        "completeProcessTreeClaim": False}
                except BaseException as census_error:
                    record["postCleanupCensus"] = {"status": "ACQUISITION_GAP",
                        "error": {"type": type(census_error).__name__, "message": str(census_error)},
                        "completeProcessTreeClaim": False}
            raise
        finally:
            record["elapsedSeconds"] = time.monotonic() - started
            record["captureFinality"] = "OBSERVED_GROUP_ABSENT" if record["acquisitionComplete"] else "NOT_ESTABLISHED"
            record["captures"] = {name: binding(path) for name, path in
                                  (("stdout", stdout_path), ("stderr", stderr_path)) if path.is_file()}
            if process is not None:
                record["returncode"] = process.poll()
            write_json(case / "result.json", record)
        # Match the existing text=True newline semantics; raw files stay intact.
        stdout = stdout_path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        stderr = stderr_path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def row_for(core, observer, pair, subject, env, label, command):
    case = fresh(pair / label)
    before = core["snapshot"](subject)
    ready = pathlib.Path(env["R0016_READY"])
    ready_before = ready.read_bytes() if ready.exists() else b""
    run = core["sandbox_run"](command, case, env)
    observed = core["evidence"](case, subject, before, env, run)
    # The environment is intentionally byte-for-byte identical within each
    # pair, so readiness/events live at the common fixture path. Preserve and
    # validate this launch's suffix rather than accepting a prior valid nonce.
    ready_after = ready.read_bytes() if ready.exists() else b""
    suffix = ready_after[len(ready_before):] if ready_after.startswith(ready_before) else b""
    acquisition = observer.records[-1]
    expected_ready = (str(acquisition["launchPid"]) + "\t" + env["R0016_NONCE"] + "\n").encode()
    observed["launchReadinessExact"] = suffix == expected_ready
    (case / "readiness-window.raw").write_bytes(suffix)
    events_path = pathlib.Path(env["R0016_EVENTS"])
    events = events_path.read_text().splitlines() if events_path.exists() else []
    observed["events"] = events
    row = {"case": label, "command": command, "environment": env,
           "observation": observed, "acquisition": acquisition,
           "stdout": binding(case / "stdout.txt"), "stderr": binding(case / "stderr.txt"),
           "stderrText": run.stderr, "stdoutText": run.stdout}
    write_json(case / "result.json", row)
    core["no_effects"](observed)
    if not observed["launchReadinessExact"]:
        raise RuntimeError("This subject did not establish its own exact PID/nonce readiness")
    return row


def physical_python(developer, shim):
    choices = []
    selected = None
    for relative in ("usr/bin/python3", "Library/Frameworks/Python3.framework/Versions/Current/bin/python3"):
        path = developer / relative
        row = {"path": str(path)}
        try:
            resolved = path.resolve(strict=True)
            row["binding"] = binding(path)
            with resolved.open("rb") as source:
                magic = source.read(4)
            mach = magic in (bytes.fromhex(x) for x in ("feedface", "cefaedfe", "feedfacf", "cffaedfe", "cafebabe", "bebafeca", "cafebabf", "bfbafeca"))
            inside = resolved == developer or developer in resolved.parents
            eligible = (inside and mach and os.access(resolved, os.X_OK)
                        and row["binding"]["sha256"] != shim["sha256"])
            row.update(machO=mach, insideSelectedDeveloper=inside, eligible=eligible)
            if eligible and selected is None:
                selected = resolved
        except (OSError, RuntimeError) as error:
            row["error"] = {"type": type(error).__name__, "message": str(error)}
        choices.append(row)
    if selected is None:
        raise RuntimeError("No physical non-shim Mach-O Python under the selected developer directory")
    return selected, choices


def assess(rows, expected_metadata, all_bindings_stable):
    reasons = []
    if [row.get("case") for row in rows] != list(CASE_NAMES):
        return {"discriminated": False, "reasons": ["The five bounded observations are incomplete"]}
    if all_bindings_stable is not True:
        reasons.append("A frozen observer or executable binding changed")
    for row in rows:
        observation, acquisition, payload = row.get("observation", {}), row.get("acquisition", {}), row.get("payload", {})
        if (type(observation.get("exit")) is not int or observation["exit"] != 0
                or observation.get("bootstrapReady") is not True
                or observation.get("launchReadinessExact") is not True
                or observation.get("snapshotUnchanged") is not True
                or observation.get("events") != []
                or observation.get("transportAttempts", "missing") is not None
                or acquisition.get("acquisitionComplete") is not True
                or acquisition.get("cleanupRequired") is not False
                or acquisition.get("residualOwnedGroup") != []
                or acquisition.get("captureFinality") != "OBSERVED_GROUP_ABSENT"
                or acquisition.get("terminalWithinBudget") is not True
                or type(acquisition.get("budgetSeconds")) not in (int, float)
                or not 0 < acquisition.get("budgetSeconds", 0) <= 30
                or type(acquisition.get("terminalObservedElapsedSeconds")) not in (int, float)
                or not 0 <= acquisition.get("terminalObservedElapsedSeconds", -1) < acquisition.get("budgetSeconds", 0)
                or type(acquisition.get("returncode")) is not int or acquisition.get("returncode") != 0):
            reasons.append(row["case"] + ": containment/readiness/capture premise failed")
        if (payload.get("schema") != "r0016-source-free-python.v1"
                or type(payload.get("pid")) is not int or payload.get("pid", 0) <= 0
                or payload.get("metadata") != {"addons": []}
                or payload.get("argv") != ["-", expected_metadata]
                or not isinstance(payload.get("version"), str) or not payload.get("version")
                or not row.get("runtimeBinding")
                or row.get("runtimeBinding", {}).get("sha256") != row.get("expectedRuntimeSha256")):
            reasons.append(row["case"] + ": Python execution/readable metadata not established")
        expected_env = {key: row["environment"].get(key) for key in
                        ("PATH", "HOME", "TMPDIR", "PYTHONDONTWRITEBYTECODE", "DEVELOPER_DIR")}
        if payload.get("environment") != expected_env or expected_env["PATH"] != "/usr/bin:/bin":
            reasons.append(row["case"] + ": reported environment differs")
    if not (rows[0]["environment"] == rows[1]["environment"] == rows[2]["environment"]):
        reasons.append("Baseline environment differed")
    if rows[3]["environment"] != rows[4]["environment"]:
        reasons.append("DEVELOPER_DIR pair environment differed")
    without_developer = {key: value for key, value in rows[3]["environment"].items() if key != "DEVELOPER_DIR"}
    if (without_developer != rows[0]["environment"]
            or "DEVELOPER_DIR" in rows[0]["environment"]
            or not isinstance(rows[3]["environment"].get("DEVELOPER_DIR"), str)
            or not rows[3]["environment"].get("DEVELOPER_DIR", "").startswith("/")):
        reasons.append("The override pair changed more than DEVELOPER_DIR")
    for row in (rows[0], rows[2]):
        if not re.search(r"couldn't create cache file .*xcrun_db-.*Operation not permitted", row.get("stderrText", "")):
            reasons.append(row["case"] + ": original shim cache diagnostic not reproduced")
    for row in (rows[1], rows[4]):
        if row.get("stderrText") != "":
            reasons.append(row["case"] + ": direct interpreter emitted stderr")
    identities = {(row.get("runtimeBinding", {}).get("sha256"), row.get("payload", {}).get("version")) for row in rows}
    if len(identities) != 1 or any(not value for pair in identities for value in pair):
        reasons.append("The actual Python executable/version was not identical across all cases")
    return {"discriminated": not reasons, "reasons": reasons,
            "developerDirShimCacheDiagnostics": len(re.findall("xcrun_db-", rows[3].get("stderrText", ""))),
            "inferenceLimit": "A reproduced stderr differential supports a launcher/cache hypothesis. Empty stderr and unchanged snapshots are not complete syscall-attempt tracing; zero installer rows execute."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--harness-sha256", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args(argv)
    output = fresh(args.output.absolute())
    result = {"schema": "r0016-macos-python-discriminator.v1",
              "classification": "DIAGNOSTIC_ACQUISITION_INCOMPLETE",
              "productRowsExecuted": 0, "installerSourceRead": False,
              "nativeSubjectsExecuted": False, "inspectOnly": args.inspect_only,
              "host": {"system": platform.system(), "kernel": platform.release(),
                       "architecture": platform.machine(), "macOSVersion": platform.mac_ver()[0]},
              "observer": {"script": binding(__file__), "python": binding(sys.executable), "version": sys.version},
              "cases": []}
    write_json(output / "result.json", result)
    contained = fresh(output / "fixture")
    observer = CaptureObserver(contained)
    try:
        repo = args.repo.resolve(strict=True)
        harness = repo / "tests/install-preview.py"
        core, frozen = load_core(harness, args.harness_sha256, contained, observer)
        result["harness"] = binding(harness)
        result["coreSha256"] = CORE_SHA256
        result["coreCaptureAdaptation"] = "Unchanged AST-selected functions; subprocess.run observer directs stdout/stderr to owned binary capture files, adds terminal process-group census and bounded cleanup. Commands, subject environments, profile policy and controls unchanged."
        pair, subject, env = core["fixture"]("python-pair", "known")
        metadata = subject / "home/Library/Application Support/Firefox/Profiles/r0016-known/extensions.json"
        program = frozen / "python-subject.py"
        result["metadata"] = binding(metadata)
        if args.inspect_only:
            profile = core["darwin_profile"](pair)
            result["inspectionPlan"] = {"profile": binding(profile), "environment": env,
                "subjectArgv": ["-", str(metadata)], "program": binding(program), "cases": list(CASE_NAMES),
                "discovery": ["/usr/bin/xcode-select", "--print-path"],
                "noNativeExecution": True}
            result["classification"] = "DIAGNOSTIC_INSPECTION_ONLY"
        else:
            if platform.system() != "Darwin":
                raise RuntimeError("Actual Darwin required; no replacement host execution")
            paths = {"bash": pathlib.Path("/bin/bash"), "sandbox": pathlib.Path("/usr/bin/sandbox-exec"),
                     "shim": pathlib.Path("/usr/bin/python3"), "xcodeSelect": pathlib.Path("/usr/bin/xcode-select"),
                     "xcrun": pathlib.Path("/usr/bin/xcrun"), "observer": pathlib.Path(sys.executable),
                     "probe": pathlib.Path(__file__), "harness": harness}
            before_bindings = {name: binding(path) for name, path in paths.items()}
            if before_bindings["observer"]["sha256"] == before_bindings["shim"]["sha256"]:
                raise RuntimeError("Observer must be an already selected physical interpreter, not the Apple shim")
            result["bindingsBefore"] = before_bindings
            result["nativeSubjectsExecuted"] = True
            result["bootstrap"] = core["bootstrap"]()
            if "version 3.2." not in core["ACQUISITION"].get("bashVersion", ""):
                raise RuntimeError("Actual Apple /bin/bash 3.2 required")
            selector_command = ["/bin/bash", "--noprofile", "--norc", "-c", 'exec "$@"',
                                "r0016-xcode-select-control", "/usr/bin/xcode-select", "--print-path"]
            selector = row_for(core, observer, pair, subject, env, "xcode-select-control", selector_command)
            result["developerDirectoryControl"] = selector
            if selector["observation"]["exit"] != 0 or selector["stderrText"] != "":
                raise RuntimeError("Contained xcode-select --print-path failed or emitted stderr")
            lines = selector["stdoutText"].splitlines()
            if len(lines) != 1 or not pathlib.Path(lines[0]).is_absolute():
                raise RuntimeError("Contained developer-directory output is not one absolute path")
            developer = pathlib.Path(lines[0]).resolve(strict=True)
            if not developer.is_dir():
                raise RuntimeError("Selected developer path is not a directory")
            physical, choices = physical_python(developer, before_bindings["shim"])
            result["physicalDiscovery"] = {"selectedDeveloper": str(developer), "candidates": choices,
                "physicalPython": binding(physical), "method": "Read-only fixed relative candidates; no xcrun lookup or Python-shim execution"}
            paths["physicalPython"] = physical
            before_bindings["physicalPython"] = binding(physical)
            for label in CASE_NAMES:
                case_env = dict(env, DEVELOPER_DIR=str(developer)) if label.startswith("developer-dir-") else dict(env)
                executable = physical if label.endswith("direct") else pathlib.Path("/usr/bin/python3")
                command = ["/bin/bash", "--noprofile", "--norc", "-c", DRIVER, "r0016-read-only-python",
                           str(executable), str(metadata), str(program)]
                row = row_for(core, observer, pair, subject, case_env, label, command)
                row["expectedRuntimeSha256"] = before_bindings["physicalPython"]["sha256"]
                try:
                    row["payload"] = json.loads(row["stdoutText"])
                    executable_reported = row["payload"].get("executable")
                    if not isinstance(executable_reported, str) or not pathlib.Path(executable_reported).is_absolute():
                        raise ValueError("Runtime did not report an absolute interpreter path")
                    row["runtimeBinding"] = binding(executable_reported)
                except (ValueError, OSError, TypeError, AttributeError) as error:
                    row["payloadError"] = {"type": type(error).__name__, "message": str(error)}
                result["cases"].append(row)
                write_json(pair / label / "result.json", row)
                write_json(output / "result.json", result)
            result["bindingsAfter"] = {name: binding(path) for name, path in paths.items()}
            stable = before_bindings == result["bindingsAfter"]
            result["assessment"] = assess(result["cases"], str(metadata), stable)
            result["classification"] = SUCCESS if result["assessment"]["discriminated"] else "DIAGNOSTIC_NO_DISCRIMINATION"
        result["frozenManifest"] = {path.name: binding(path) for path in sorted(frozen.iterdir())}
    except BaseException as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        (output / "exception.txt").write_text(traceback.format_exc())
    finally:
        result["observerRuns"] = observer.records
        result["productRowsExecuted"] = 0
        result["nativeQualification"] = "NOT_SUPPLIED"
        result["limits"] = ["No complete native process-tree syscall-attempt trace is acquired.",
            "The read-only diagnostic does not qualify any installer helper, entry, normal, or NoOpen row.",
            "Caches are never cleared, prewarmed, redirected, or named as exemptions; PATH remains /usr/bin:/bin.",
            "The DEVELOPER_DIR pair is separately labeled; the original baseline environment remains unchanged."]
        write_json(output / "result.json", result)
    print(json.dumps({"classification": result["classification"], "result": str(output / "result.json"),
                      "productRowsExecuted": 0, "nativeSubjectsExecuted": result["nativeSubjectsExecuted"]}))
    return 0 if result["classification"] in (SUCCESS, "DIAGNOSTIC_INSPECTION_ONLY") else 2


# Existing owned-PTY cleanup/census core is inserted below, without alteration.
def census(directory, label, env, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("owned cleanup ceiling reached")
    stdout_path, stderr_path = directory / (label + ".stdout.raw"), directory / (label + ".stderr.raw")
    with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
        run = subprocess.run(["/bin/ps", "-A", "-o", "pid=,ppid=,pgid=,uid=,stat=,lstart="],
                             env=dict(env, LC_ALL="C"), stdin=subprocess.DEVNULL, stdout=stdout,
                             stderr=stderr, timeout=min(1, remaining), check=False)
    if run.returncode:
        raise RuntimeError("owned-process census failed")
    rows = {}
    for line in stdout_path.read_text().splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6:
            raise ValueError("malformed owned-process census")
        pid, ppid, pgid, uid = map(int, fields[:4])
        rows[pid] = dict(pid=pid, ppid=ppid, pgid=pgid, uid=uid, state=fields[4], started=fields[5])
    return rows

def force_cleanup(process, case, env, deadline):
    """Fallback only: freeze direct parent; verify and kill leaves, then parent.

    Unlike the archived cleanup, a signalled exiting child does not prevent
    closing its master by terminating the verified stopped parent. No signals
    are sent after that ancestry anchor is gone. Any residual keeps FAIL closed.
    """
    record = {"complete": False, "signals": [], "scope": "current verified owned PIDs only"}
    known = {}
    serial = 0

    def snapshot():
        nonlocal serial
        serial += 1
        return census(case, "cleanup-census-%02d" % serial, env, deadline)

    try:
        rows = snapshot()
        parent = rows.get(process.pid)
        if (process.poll() is not None or parent is None or parent["ppid"] != os.getpid()
                or parent["pgid"] != process.pid or parent["uid"] != os.getuid()):
            raise RuntimeError("live direct parent identity unavailable; no fallback signals")
        known[parent["pid"]] = parent
        process.send_signal(signal.SIGSTOP)
        record["signals"].append({"pid": process.pid, "signal": "SIGSTOP", "identity": parent})
        rows = snapshot()
        stopped = rows.get(process.pid)
        if stopped is None or stopped["started"] != parent["started"] or not stopped["state"].startswith("T"):
            raise RuntimeError("owned parent stop unconfirmed")
        children = [r for r in rows.values() if r["ppid"] == process.pid]
        if len(children) > 1 or any(r["uid"] != os.getuid() or r["pgid"] != r["pid"] for r in children):
            raise RuntimeError("single-fork owned child topology changed")
        if any(r["ppid"] in {c["pid"] for c in children} for r in rows.values()):
            raise RuntimeError("unexpected deeper descendant; no unverified cleanup")
        for child in children:
            known[child["pid"]] = child
            if not child["state"].startswith("Z"):
                os.kill(child["pid"], signal.SIGKILL)
                record["signals"].append({"pid": child["pid"], "signal": "SIGKILL", "identity": child})
        # Parent is stopped, so it cannot reap/reuse the verified child PID or
        # fork another child. Its death closes the owned master and phase FDs.
        process.kill()
        record["signals"].append({"pid": process.pid, "signal": "SIGKILL", "identity": stopped})
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        while time.monotonic() < deadline:
            rows = snapshot()
            residual = [r for pid, r in rows.items() if pid in known and r["started"] == known[pid]["started"]
                        and r["uid"] == known[pid]["uid"] and r["pgid"] == known[pid]["pgid"]]
            record["remainingKnownProcesses"] = residual
            if not residual:
                record["complete"] = True
                break
            time.sleep(min(0.02, max(0, deadline - time.monotonic())))
    except Exception as error:
        record["error"] = {"type": type(error).__name__, "message": str(error)}
        # Census failure must not strand our direct child after SIGSTOP. Popen
        # still owns this unreaped process independently of descendant census.
        # Release its PTY master without guessing any descendant identity. The
        # acquisition remains incomplete: this rescue is not an ancestry proof.
        rescue = {"attempted": False, "terminal": False}
        record["directParentRescue"] = rescue
        if process.poll() is None:
            rescue["attempted"] = True
            try:
                process.kill()
                record["signals"].append({"pid": process.pid, "signal": "SIGKILL", "identity": "owned unreaped direct Popen child; no descendant signal"})
            except Exception as kill_error:
                rescue["killError"] = str(kill_error)
                try:
                    process.send_signal(signal.SIGCONT)
                    record["signals"].append({"pid": process.pid, "signal": "SIGCONT", "identity": "owned unreaped direct Popen child"})
                    process.terminate()
                    record["signals"].append({"pid": process.pid, "signal": "SIGTERM", "identity": "owned unreaped direct Popen child"})
                except Exception as signal_error:
                    rescue["signalError"] = str(signal_error)
            remaining = deadline - time.monotonic()
            if remaining > 0:
                try:
                    process.wait(timeout=remaining)
                except Exception as wait_error:
                    rescue["waitError"] = str(wait_error)
        rescue["terminal"] = process.poll() is not None
    record["known"] = list(known.values())
    record["directChildReturncode"] = process.poll()
    return record


if __name__ == "__main__":
    raise SystemExit(main())
