#!/usr/bin/env python3
"""Acquire two bounded PTY-only observations; never execute an installer.

Normal execution is macOS-only. --inspect-only freezes/validates the exact
source-derived program and policies without launching either PTY subject.
"""
import argparse
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import time
from types import SimpleNamespace


BASELINE_COMMIT = "3d091c3515c6258e4983ea71d2426be399881936"
BASELINE_TREE = "2e57dcac25c52f3fd968006bfd3ddacb5d7073bb"
REVIEW_SHA256 = "c6b2089569ce01f987560b8decaeb7f97d2f453aff0e441fb11b522d0f158c63"
INPUT_SHA256 = {
    "tests/install-preview.py": "5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760",
    "install.sh": "9e0facbed4053dddbf676c58e4a07515371cdd7f35ad4d85164486d2c71fdb9c",
    "install.ps1": "b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e",
}
SUBJECT_SECONDS = 30
CLEANUP_SECONDS = 6
PHASE_FD_NAME = "R0016_POSIX_PHASE_FD"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def binding(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256(data)}


def owned_directory(path):
    path.mkdir(mode=0o700)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise RuntimeError("Fresh directory ownership/mode verification failed: " + str(path))
    return path


def one(items, label):
    if len(items) != 1:
        raise RuntimeError("Expected exactly one source AST node for " + label)
    return items[0]


def assignment(function, name):
    return one([node for node in ast.walk(function)
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name], name)


def extract(source):
    tree = ast.parse(source)
    functions = {name: one([node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name], name)
                 for name in ("darwin_profile", "fixture", "sandbox_run", "bootstrap")}
    terminal = assignment(functions["bootstrap"], "terminal_probe")
    literal = ast.literal_eval(terminal.value)
    if not isinstance(literal, str):
        raise RuntimeError("Actual terminal_probe is not a string literal")
    environment = assignment(functions["fixture"], "env").value
    if not isinstance(environment, ast.Dict):
        raise RuntimeError("Actual fixture environment is not a dictionary expression")
    denials = ast.literal_eval(one([node for node in tree.body if isinstance(node, ast.Assign)
                                  and any(isinstance(target, ast.Name) and target.id == "DENIALS" for target in node.targets)], "DENIALS").value)
    sandbox = functions["sandbox_run"]
    defaults = dict(zip([arg.arg for arg in sandbox.args.args][-len(sandbox.args.defaults):], sandbox.args.defaults))
    if ast.literal_eval(defaults["timeout"]) != SUBJECT_SECONDS:
        raise RuntimeError("Original subject ceiling changed")
    return functions, environment, denials, literal


PHASE_PREFIX = '''import time as _r0016_time
_r0016_phase_fd = int(os.environ["R0016_POSIX_PHASE_FD"])
_r0016_nonce = os.environ["R0016_NONCE"]
def _r0016_phase(name, **fields):
    row = {"phase": name, "nonce": _r0016_nonce, "pid": os.getpid(),
           "ppid": os.getppid(), "pgid": os.getpgrp(), "sid": os.getsid(0),
           "uid": os.getuid(), "monotonicNs": _r0016_time.monotonic_ns()}
    row.update(fields)
    raw = (json.dumps(row, separators=(",", ":"), sort_keys=True) + "\\n").encode("ascii")
    try:
        if os.write(_r0016_phase_fd, raw) != len(raw):
            raise OSError("short phase-channel write")
    except BaseException as error:
        os.write(2, ("DIAGNOSTIC_PHASE_WRITE_FAILED: " + repr(error)[:400] + "\\n").encode("utf-8"))
        os._exit(125)
'''


def phase(expression):
    return ast.parse("_r0016_phase(" + expression + ")").body[0]


def call_name(node):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return node.func.value.id + "." + node.func.attr
    return None


def instrument(literal):
    """Insert markers into the actual AST and prove removal restores its AST."""
    original = ast.parse(literal)
    counts = {}

    class Insert(ast.NodeTransformer):
        def visit_Assign(self, node):
            label = call_name(node.value)
            specifications = {
                "pty.fork": ("fork", "childPid=pid, masterFd=fd"),
                "os.open": ("tty.open", "terminalFd=terminal"),
                "os.waitpid": ("waitpid", "waitedPid=done, status=status"),
            }
            if label not in specifications:
                return node
            name, fields = specifications[label]
            counts[label] = counts.get(label, 0) + 1
            return [phase(repr(name + ".before")), node, phase(repr(name + ".after") + ", " + fields)]

        def visit_Expr(self, node):
            label = call_name(node.value)
            if label == "os.close":
                argument = one(node.value.args, "os.close argument")
                if not isinstance(argument, ast.Name) or argument.id not in ("terminal", "fd"):
                    raise RuntimeError("Unexpected close in actual terminal probe")
                label += "." + argument.id
            names = {"os.write": "tty.write", "os.close.terminal": "tty.close", "os.close.fd": "master.close", "print": "result.print"}
            if label in names:
                counts[label] = counts.get(label, 0) + 1
                return [phase(repr(names[label] + ".before")), node, phase(repr(names[label] + ".after"))]
            if label == "os._exit":
                counts[label] = counts.get(label, 0) + 1
                return [phase("'child.exit.before', exitCode=" + ast.unparse(one(node.value.args, "os._exit argument"))), node]
            return node

        def visit_If(self, node):
            self.generic_visit(node)
            node.body.insert(0, phase("'child.branch'"))
            return node

        def visit_ExceptHandler(self, node):
            self.generic_visit(node)
            if node.name is not None or not isinstance(node.type, ast.Name) or node.type.id != "OSError":
                raise RuntimeError("Actual child exception handler changed")
            node.name = "_r0016_error"
            node.body.insert(0, phase("'child.oserror', errorType=type(_r0016_error).__name__, errno=_r0016_error.errno, message=str(_r0016_error)[:400]"))
            return node

    amended = Insert().visit(copy.deepcopy(original))
    expected = {"pty.fork": 1, "os.open": 1, "os.waitpid": 1, "os.write": 1,
                "os.close.terminal": 1, "os.close.fd": 1, "print": 1, "os._exit": 2}
    if counts != expected:
        raise RuntimeError("Actual PTY operation inventory changed: " + repr(counts))

    class Remove(ast.NodeTransformer):
        def visit_Expr(self, node):
            return None if call_name(node.value) == "_r0016_phase" else node

        def visit_ExceptHandler(self, node):
            self.generic_visit(node)
            node.name = None
            return node

    restored = Remove().visit(copy.deepcopy(amended))
    if ast.dump(restored, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise RuntimeError("Instrumentation did not preserve the original AST")
    # Keep the original import ahead of the diagnostic helper. The original
    # operations remain in order inside a reporting-only exception wrapper.
    initial_import = amended.body.pop(0)
    if not isinstance(initial_import, ast.Import):
        raise RuntimeError("Original terminal import changed")
    wrapped = ast.Try(body=[phase("'subject.start'")] + amended.body + [phase("'subject.complete'")],
                      handlers=[ast.ExceptHandler(type=ast.Name(id="BaseException", ctx=ast.Load()), name="_r0016_exception",
                      body=[phase("'subject.exception', errorType=type(_r0016_exception).__name__, errno=getattr(_r0016_exception, 'errno', None), message=str(_r0016_exception)[:400]"), ast.Raise()])],
                      orelse=[], finalbody=[])
    result = ast.Module(body=[initial_import] + ast.parse(PHASE_PREFIX).body + [wrapped], type_ignores=[])
    ast.fix_missing_locations(result)
    rendered = ast.unparse(result) + "\n"
    compile(rendered, "terminal-probe.instrumented.py", "exec")
    return rendered, {"originalOperations": counts, "markerRemovalRestoresOriginalAst": True}


def exception_record(error):
    value = {"type": type(error).__name__, "message": str(error), "repr": repr(error)}
    if isinstance(error, subprocess.TimeoutExpired):
        value.update({"timeout": error.timeout, "command": error.cmd})
        for name in ("output", "stderr"):
            raw = getattr(error, name, None)
            value[name + "Base64"] = base64.b64encode(raw).decode("ascii") if isinstance(raw, bytes) else None
            value[name + "Text"] = raw if isinstance(raw, str) else None
    if isinstance(error, OSError):
        value["errno"] = error.errno
    return value


def decode_retained(path):
    raw = path.read_bytes()
    result = {"path": str(path), "bytes": len(raw), "sha256": sha256(raw)}
    try:
        result["text"] = raw.decode("utf-8", errors="strict")
        result["decodeError"] = None
    except UnicodeDecodeError as error:
        result.update({"text": None, "decodeError": {"type": type(error).__name__, "start": error.start,
                                                     "end": error.end, "reason": error.reason}})
    return result


def metadata_command(command, directory, label, env, timeout=5):
    """Fixed read-only metadata commands, with raw files opened first."""
    stdout_path, stderr_path = directory / (label + ".stdout.raw"), directory / (label + ".stderr.raw")
    record = {"command": command, "timeoutSeconds": timeout}
    with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                    env=env, timeout=timeout, start_new_session=True, check=False)
            record["returncode"] = result.returncode
        except Exception as error:
            record["error"] = exception_record(error)
    record["stdout"] = decode_retained(stdout_path)
    record["stderr"] = decode_retained(stderr_path)
    write_json(directory / (label + ".json"), record)
    return record


def process_snapshot(directory, label, env, seconds):
    record = metadata_command(["/bin/ps", "-A", "-o", "pid=,ppid=,pgid=,uid=,stat=,lstart="],
                              directory, label, dict(env, LC_ALL="C"), timeout=max(0.01, min(1, seconds)))
    if record.get("returncode") != 0 or record["stdout"]["text"] is None:
        raise RuntimeError("Owned-process census unavailable; no unverified signal is allowed")
    rows = {}
    for line in record["stdout"]["text"].splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6:
            raise RuntimeError("Malformed process-census row")
        pid, ppid, pgid, uid = map(int, fields[:4])
        rows[pid] = {"pid": pid, "ppid": ppid, "pgid": pgid, "uid": uid, "state": fields[4], "started": fields[5]}
    return rows


def owned_processes(rows, launch_pid, controller_pid, uid):
    """Require a current direct-child anchor, then current same-UID ancestry."""
    root = rows.get(launch_pid)
    if root is None or root["ppid"] != controller_pid or root["pgid"] != launch_pid or root["uid"] != uid:
        return {}
    result = {launch_pid: root}
    for _ in range(32):
        additions = {pid: row for pid, row in rows.items() if pid not in result and row["ppid"] in result and row["uid"] == uid}
        if not additions:
            return result
        result.update(additions)
        if len(result) > 32:
            raise RuntimeError("Unexpectedly large diagnostic descendant tree")
    raise RuntimeError("Unexpectedly deep diagnostic descendant tree")


def identity(row):
    return tuple(row[key] for key in ("pid", "ppid", "pgid", "uid", "started"))


def cleanup(process, directory, env):
    """Signal verified individual descendants before their direct parent."""
    deadline = time.monotonic() + CLEANUP_SECONDS
    record = {"budgetSeconds": CLEANUP_SECONDS, "signals": [], "observations": [], "complete": False,
              "scope": "Individual verified PIDs only; no killpg, name matching, or external process termination."}
    known = {}
    serial = 0

    def snapshot():
        nonlocal serial
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Diagnostic cleanup budget exhausted")
        serial += 1
        rows = process_snapshot(directory, "cleanup-census-%02d" % serial, env, remaining)
        owned = owned_processes(rows, process.pid, os.getpid(), os.getuid())
        for pid, row in owned.items():
            known.setdefault(pid, row)
        record["observations"].append({"monotonicNs": time.monotonic_ns(), "owned": list(owned.values())})
        return rows, owned

    def signal_verified(pid, requested):
        rows, owned = snapshot()
        row = owned.get(pid)
        if row is None or pid not in known or identity(row) != identity(known[pid]) or row["state"].startswith("Z"):
            record["signals"].append({"pid": pid, "signal": requested.name, "sent": False, "reason": "Current identity/ancestry not verified, or already zombie"})
            return
        if requested != signal.SIGSTOP and pid == process.pid and any(child != pid and not value["state"].startswith("Z") for child, value in owned.items()):
            record["signals"].append({"pid": pid, "signal": requested.name, "sent": False, "reason": "A current live descendant still needs its ancestry anchor"})
            return
        try:
            os.kill(pid, requested)
        except ProcessLookupError:
            record["signals"].append({"pid": pid, "signal": requested.name, "sent": False, "reason": "Process exited after the verified census"})
            return
        record["signals"].append({"pid": pid, "signal": requested.name, "sent": True, "verified": row})

    try:
        rows, owned = snapshot()
        if process.pid not in owned:
            raise RuntimeError("Direct-child identity is not currently verified; cleanup remains incomplete")
        # Freeze only this verified owned parent after its subject deadline (or
        # launch/wait failure). A confirmed stop closes the census-to-fork race
        # without changing anything during the observed 30-second interval.
        signal_verified(process.pid, signal.SIGSTOP)
        rows, owned = snapshot()
        if process.pid not in owned or identity(owned[process.pid]) != identity(known[process.pid]) or not owned[process.pid]["state"].startswith("T"):
            raise RuntimeError("Owned direct-child stop could not be confirmed; cleanup remains incomplete")
        record["anchorStoppedBeforeDescendantCleanup"] = True
        for requested in (signal.SIGTERM, signal.SIGKILL):
            # The extracted original has one fork. This additionally handles a
            # bounded deeper owned tree, always leaving its anchor alive first.
            children = [pid for pid in owned if pid != process.pid and not owned[pid]["state"].startswith("Z")]
            for pid in reversed(children):
                signal_verified(pid, requested)
            if children:
                time.sleep(min(0.15, max(0, deadline - time.monotonic())))
            rows, owned = snapshot()
        remaining_children = [pid for pid, row in owned.items() if pid != process.pid and not row["state"].startswith("Z")]
        if not remaining_children:
            if process.poll() is None:
                # Do not resume the frozen anchor and reopen the fork race.
                signal_verified(process.pid, signal.SIGKILL)
                try:
                    process.wait(timeout=min(0.25, max(0.01, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    pass
        rows, owned = snapshot()
        residual = [row for pid, row in rows.items() if pid in known
                    and row["started"] == known[pid]["started"] and row["uid"] == known[pid]["uid"]]
        record["remainingKnownProcesses"] = residual
        record["remainingKnownLive"] = [row for row in residual if not row["state"].startswith("Z")]
        record["directChildReturncode"] = process.poll()
        record["complete"] = record["directChildReturncode"] is not None and not residual
        if not known:
            record["complete"] = False
            record["reason"] = "No live direct-child ancestry was acquired; descendant cleanup is unproven"
    except Exception as error:
        record["error"] = exception_record(error)
        record["directChildReturncode"] = process.poll()
    record["elapsedSeconds"] = CLEANUP_SECONDS - max(0, deadline - time.monotonic())
    return record


def read_phases(capture, nonce):
    rows, errors = [], []
    if capture["text"] is None:
        return rows, ["Phase channel cannot be decoded as strict UTF-8"]
    for number, line in enumerate(capture["text"].splitlines(), 1):
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or row.get("nonce") != nonce or not isinstance(row.get("phase"), str):
                raise ValueError("Wrong phase shape or nonce")
            if any(type(row.get(key)) is not int for key in ("pid", "ppid", "pgid", "sid", "uid", "monotonicNs")):
                raise ValueError("Invalid process identity or timestamp")
            rows.append(row)
        except Exception as error:
            errors.append({"line": number, "error": exception_record(error)})
    return rows, errors


def run_case(case, env, command):
    stdout_path, stderr_path, phase_path = [case / name for name in ("stdout.raw", "stderr.raw", "phases.raw.jsonl")]
    record = {"classification": "DIAGNOSTIC_ACQUISITION_INCOMPLETE", "subjectSeconds": SUBJECT_SECONDS,
              "productRowsExecuted": 0, "command": command, "cwd": os.getcwd(), "startNewSession": True,
              "stdin": "DEVNULL", "environment": env, "rawCaptureMechanism": "Direct regular files; no pipe EOF/drain dependency"}
    process = None
    with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
        phase_fd = os.open(phase_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        try:
            launched_env = dict(env, **{PHASE_FD_NAME: str(phase_fd)})
            record["environment"] = launched_env
            record["phaseFd"] = phase_fd
            record["prelaunchCaptures"] = {"stdout": str(stdout_path), "stderr": str(stderr_path), "phase": str(phase_path)}
            write_json(case / "launch.json", record)
            started = time.monotonic()
            record["startedMonotonicNs"] = time.monotonic_ns()
            try:
                process = subprocess.Popen(command, env=launched_env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                           start_new_session=True, pass_fds=(phase_fd,))
                record["launchPid"] = process.pid
                record["controllerPid"] = os.getpid()
                write_json(case / "launch.json", record)
                # Count launch overhead inside the original 30-second ceiling.
                process.wait(timeout=max(0, SUBJECT_SECONDS - (time.monotonic() - started)))
                record["executionOutcome"] = "TERMINAL_EXIT"
            except subprocess.TimeoutExpired as error:
                record["executionOutcome"] = "TIMEOUT"
                record["exception"] = exception_record(error)
            except BaseException as error:
                record["executionOutcome"] = "LAUNCH_OR_WAIT_ERROR"
                record["exception"] = exception_record(error)
            record["subjectElapsedSeconds"] = time.monotonic() - started
            # Persist the terminal/timeout/error record before interpretation.
            try:
                write_json(case / "execution.json", record)
            except Exception as error:
                record["executionRecordError"] = exception_record(error)
            finally:
                if process is not None and process.poll() is None:
                    record["cleanup"] = cleanup(process, case, env)
                else:
                    record["cleanup"] = {"complete": None, "reason": "Direct child is terminal; original waitpid/child markers must prove child reaping"}
            record["returncode"] = process.returncode if process is not None else None
        finally:
            os.close(phase_fd)
    # Only now decode already-retained bytes. Incomplete cleanup keeps the
    # captures explicitly live/unproven instead of presenting a terminal hash.
    record["captures"] = {"stdout": decode_retained(stdout_path), "stderr": decode_retained(stderr_path), "phase": decode_retained(phase_path)}
    rows, errors = read_phases(record["captures"]["phase"], env["R0016_NONCE"])
    record["phases"], record["phaseErrors"] = rows, errors
    parents = [row for row in rows if row["pid"] == record.get("launchPid")]
    fork_returns = [row for row in parents if row["phase"] == "fork.after" and type(row.get("childPid")) is int and row["childPid"] > 0]
    child_pid = fork_returns[0]["childPid"] if len(fork_returns) == 1 else None
    reaped = any(row["phase"] == "waitpid.after" and row.get("waitedPid") == child_pid for row in parents) and child_pid is not None
    if record["cleanup"]["complete"] is None:
        # Pinned source contains exactly one fork and no other child creation.
        record["cleanup"]["complete"] = reaped
        record["cleanup"]["originalChildReaped"] = reaped
    record["capturesStable"] = record["cleanup"]["complete"] is True
    record["lastPhaseByPid"] = {str(row["pid"]): row for row in rows}
    record["terminalObservation"] = None
    if record["captures"]["stdout"]["text"] is not None:
        try:
            record["terminalObservation"] = json.loads(record["captures"]["stdout"]["text"])
        except Exception as error:
            record["stdoutParseError"] = exception_record(error)
    child_phases = {row["phase"] for row in rows if row["pid"] == child_pid and row["ppid"] == record.get("launchPid")}
    terminal = record["terminalObservation"]
    record["terminalIoObserved"] = bool(record["returncode"] == 0 and reaped and isinstance(terminal, dict)
                                         and terminal.get("controllingTerminalAllowed") is True and terminal.get("childExit") == 0
                                         and {"tty.open.after", "tty.write.after", "tty.close.after", "child.exit.before"}.issubset(child_phases))
    acquired = bool(record.get("launchPid") and parents and not errors and record["capturesStable"] and "executionRecordError" not in record
                    and all(value["decodeError"] is None for value in record["captures"].values()))
    record["classification"] = ("DIAGNOSTIC_TIMEOUT_OBSERVED" if record["executionOutcome"] == "TIMEOUT" else "DIAGNOSTIC_TERMINAL_OBSERVED") if acquired else "DIAGNOSTIC_ACQUISITION_INCOMPLETE"
    record["acquisitionComplete"] = acquired
    record["inferenceLimit"] = "A last before-marker locates an uncompleted interval; it does not identify the precise internal blocked syscall or establish a Python cause."
    write_json(case / "result.json", record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin" and not args.inspect_only:
        print(json.dumps({"classification": "DIAGNOSTIC_UNSUPPORTED_HOST", "nativeSubjectsExecuted": False,
                          "productRowsExecuted": 0, "reason": "Normal mode requires native macOS; use --inspect-only for source validation"}))
        return 2
    repo = args.repo.resolve(strict=True)
    output = owned_directory(args.output.absolute()).resolve(strict=True)
    result = {"schema": "r0016-posix-diagnostic.v1", "classification": "DIAGNOSTIC_ACQUISITION_INCOMPLETE",
              "scope": "Two instrumented owned PTY-only observations; no installer execution or product qualification",
              "productRowsExecuted": 0, "nativeSubjectsExecuted": False, "inspectOnly": args.inspect_only,
              "baselineCommit": BASELINE_COMMIT, "baselineTree": BASELINE_TREE, "native1ReviewSha256": REVIEW_SHA256,
              "repo": str(repo), "output": str(output), "cases": [], "inputs": {}, "subjectSeconds": SUBJECT_SECONDS,
              "probe": binding(Path(__file__).resolve()), "host": {"system": platform.system(), "kernel": platform.release(),
              "architecture": platform.machine(), "macOSVersion": platform.mac_ver()[0], "uid": os.getuid(), "gid": os.getgid()},
              "python": {"executable": sys.executable, "version": sys.version, "binary": binding(Path(sys.executable).resolve())},
              "bash": {"executable": "/bin/bash", "binary": binding(Path("/bin/bash").resolve())}}
    write_json(output / "result.json", result)
    try:
        frozen = owned_directory(output / "frozen")
        for relative, expected in INPUT_SHA256.items():
            path = repo / relative
            raw = path.read_bytes()
            destination = frozen / relative.replace("/", "__")
            destination.write_bytes(raw)
            result["inputs"][relative] = {"source": str(path), "frozen": binding(destination), "expectedSha256": expected}
            if sha256(raw) != expected:
                raise RuntimeError("Pinned input bytes changed: " + relative)
        source = (frozen / "tests__install-preview.py").read_text(encoding="utf-8")
        functions, env_ast, denials, literal = extract(source)
        instrumented, proof = instrument(literal)
        result["instrumentation"] = proof
        for name, node in functions.items():
            (frozen / (name + ".extracted.py")).write_text(ast.get_source_segment(source, node) + "\n", encoding="utf-8")
        (frozen / "fixture-env.extracted.txt").write_text(ast.get_source_segment(source, env_ast) + "\n", encoding="utf-8")
        (frozen / "terminal-probe.original.py").write_text(literal, encoding="utf-8")
        (frozen / "terminal-probe.instrumented.py").write_text(instrumented, encoding="utf-8")
        result["originalSnippet"] = binding(frozen / "terminal-probe.original.py")
        result["instrumentedSnippet"] = binding(frozen / "terminal-probe.instrumented.py")
        result["frozenManifest"] = {path.name: binding(path) for path in sorted(frozen.iterdir())}
        control = owned_directory(output / "metadata")
        owned_directory(control / "home")
        owned_directory(control / "tmp")
        meta_env = {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8" if platform.system() == "Darwin" else "C.UTF-8",
                    "HOME": str(control / "home"), "TMPDIR": str(control / "tmp"), "GIT_OPTIONAL_LOCKS": "0",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        git = shutil.which("git")
        if not git:
            raise RuntimeError("Read-only Git identity acquisition unavailable")
        git_record = metadata_command([git, "-C", str(repo), "rev-parse", "HEAD", "HEAD^{tree}"], control, "git-identity", meta_env)
        if git_record.get("returncode") != 0 or git_record["stdout"]["text"] is None:
            raise RuntimeError("Could not bind actual commit and tree")
        identities = git_record["stdout"]["text"].splitlines()
        if len(identities) != 2 or any(len(value) != 40 or any(character not in "0123456789abcdef" for character in value) for value in identities):
            raise RuntimeError("Malformed commit/tree acquisition")
        result["commit"], result["tree"] = identities
        result["gitAcquisition"] = git_record
        if not args.inspect_only:
            sandbox = Path("/usr/bin/sandbox-exec")
            if not sandbox.is_file() or not os.access(sandbox, os.X_OK):
                raise RuntimeError("Native sandbox-exec absent; no subject launched")
            result["sandboxExecutable"] = binding(sandbox)
            result["bash"]["versionAcquisition"] = metadata_command(["/bin/bash", "--version"], control, "bash-version", meta_env)
            if result["bash"]["versionAcquisition"].get("returncode") != 0:
                raise RuntimeError("Native Bash identity acquisition failed")
        prepared = []
        for label in ("same-profile", "host-control"):
            case = owned_directory(output / label)
            subject = owned_directory(case / "subject")
            home, temp = owned_directory(subject / "home"), owned_directory(subject / "tmp")
            terminal = owned_directory(case / "terminal-probe")
            (case / "bootstrap.sh").write_text(denials, encoding="ascii")
            namespace = {"ROOT": case}
            profile_module = ast.Module(body=[copy.deepcopy(functions["darwin_profile"])], type_ignores=[])
            exec(compile(ast.fix_missing_locations(profile_module), "actual-darwin-profile", "exec"), namespace)
            profile = namespace["darwin_profile"](terminal)
            env = eval(compile(ast.Expression(body=copy.deepcopy(env_ast)), "actual-fixture-environment", "eval"),
                       {"HOST": "Darwin", "ARGS": SimpleNamespace(bash="/bin/bash"), "root": case, "home": home,
                        "temp": temp, "route": "github", "secrets": secrets})
            command = [sys.executable, "-c", instrumented]
            if label == "same-profile":
                command = ["/usr/bin/sandbox-exec", "-f", str(profile)] + command
            plan = {"case": label, "profileApplied": label == "same-profile", "profile": binding(profile),
                    "environment": env, "command": command, "cwd": os.getcwd(), "subjectSeconds": SUBJECT_SECONDS,
                    "instrumentedSnippetSha256": sha256(instrumented.encode("utf-8"))}
            write_json(case / "plan.json", plan)
            prepared.append((case, env, command, plan))
        result["preparedCases"] = [value[3] for value in prepared]
        write_json(output / "result.json", result)
        if args.inspect_only:
            result["classification"] = "DIAGNOSTIC_INSPECTION_ONLY"
            result["nativeSubjectsExecuted"] = False
            result["acquisitionComplete"] = False
            result["remainingGate"] = "Exact native execution and independent receiving are still required"
        else:
            for case, env, command, plan in prepared:
                # Until a case returns its launch receipt, execution may be
                # unknown. An attempted launch is not an observed process.
                if result["nativeSubjectsExecuted"] is not True:
                    result["nativeSubjectsExecuted"] = None
                observed = run_case(case, env, command)
                observed.update({"case": plan["case"], "profileApplied": plan["profileApplied"], "profile": plan["profile"]})
                result["cases"].append(observed)
                result["nativeSubjectsExecuted"] = any(row.get("launchPid") for row in result["cases"])
                write_json(output / "result.json", result)
            result["acquisitionComplete"] = all(case["acquisitionComplete"] for case in result["cases"])
            result["classification"] = "DIAGNOSTIC_OBSERVATIONS_ACQUIRED" if result["acquisitionComplete"] else "DIAGNOSTIC_ACQUISITION_INCOMPLETE"
            result["comparison"] = {case["case"]: {"outcome": case["executionOutcome"], "terminalIoObserved": case["terminalIoObserved"],
                                                    "lastPhaseByPid": case["lastPhaseByPid"]} for case in result["cases"]}
            result["inferenceLimit"] = "These instrumented observations do not identify an internal blocked syscall, qualify any installer row, or authorize policy/timeout changes."
        write_json(output / "result.json", result)
    except BaseException as error:
        result["error"] = exception_record(error)
        write_json(output / "result.json", result)
    print(json.dumps({"classification": result["classification"], "result": str(output / "result.json"),
                      "productRowsExecuted": 0, "nativeSubjectsExecuted": result["nativeSubjectsExecuted"]}))
    return 0 if result["classification"] in ("DIAGNOSTIC_INSPECTION_ONLY", "DIAGNOSTIC_OBSERVATIONS_ACQUIRED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
