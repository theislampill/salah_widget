#!/usr/bin/env python3
"""Scratch R0016 macOS PTY drain discriminator; never execute an installer.

Derive the child, sentinel, environment and sandbox from pinned harness bytes.
Only the parent gains a read before the original blocking wait. Diagnostic
markers and failure cleanup are separately removable in an AST identity proof.
--inspect-only creates source/policy evidence without launching any subject.
The archived original is bound by digest, never rerun by this program.
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


SOURCE_PATH = "tests/install-preview.py"
SOURCE_SHA256 = "5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760"
ORIGINAL_SHA256 = "8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904"
SUBJECT_SECONDS = 30
CLEANUP_SECONDS = 6
ARCHIVED_RED = {
    "artifact": "r0016-13868376534.zip",
    "sha256": "128e0cdcc9c465f2dc0b5dac3505339e2127c4911898578442db345c1b7f5b68",
    "commit": "65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5",
    "tree": "988d6191b24c6f64b6c71014a0077be1e48c4327",
    "resultSha256": "86506deb4592a138382f74c584aefa9f517d89dd43933d82bf9f6e5fd0598c9d",
    "sameProfilePhasesSha256": "9450c7ddff205e13e4aad0b0a5d3c22844afe96f87cca2650e6a51fa629da52b",
    "hostControlPhasesSha256": "48c4bca3c97d4b09c2a14a2b6d67f9b919372dbe6725211a2565cb55921a53c5",
    "scope": "Original acquisition-incomplete PTY diagnostic; no product rows; not replayed",
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def binding(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw)}


def fresh_directory(path):
    path.mkdir(mode=0o700)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise RuntimeError("Fresh owned directory verification failed")
    return path.resolve(strict=True)


def one(values, label):
    if len(values) != 1:
        raise ValueError("Expected one " + label)
    return values[0]


def assigned(function, name):
    return one([n for n in ast.walk(function) if isinstance(n, ast.Assign)
                and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == name], name)


def call_name(node):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return node.func.value.id + "." + node.func.attr
    return ""


def extract(raw):
    if sha256(raw) != SOURCE_SHA256:
        raise ValueError("Pinned harness digest mismatch; no subject authorized")
    source = raw.decode("utf-8")
    tree = ast.parse(source)
    functions = {name: one([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name], name)
                 for name in ("bootstrap", "fixture", "darwin_profile", "sandbox_run")}
    original = ast.literal_eval(assigned(functions["bootstrap"], "terminal_probe").value)
    if not isinstance(original, str) or sha256(original.encode()) != ORIGINAL_SHA256:
        raise ValueError("Pinned original terminal snippet mismatch")
    sandbox = functions["sandbox_run"]
    defaults = dict(zip([a.arg for a in sandbox.args.args][-len(sandbox.args.defaults):], sandbox.args.defaults))
    if ast.literal_eval(defaults["timeout"]) != SUBJECT_SECONDS:
        raise ValueError("Original subject ceiling changed")
    environment = assigned(functions["fixture"], "env").value
    if not isinstance(environment, ast.Dict):
        raise ValueError("Fixture environment shape changed")
    denials = ast.literal_eval(one([n for n in tree.body if isinstance(n, ast.Assign)
                                   and any(isinstance(t, ast.Name) and t.id == "DENIALS" for t in n.targets)], "DENIALS").value)
    sentinel_call = one([n for n in ast.walk(ast.parse(original)) if call_name(n) == "os.write"], "terminal write")
    sentinel = ast.literal_eval(sentinel_call.args[1])
    if not isinstance(sentinel, bytes) or not sentinel:
        raise ValueError("Original sentinel is not nonempty bytes")
    return functions, environment, denials, original, sentinel


SUBJECT_HELPERS = r'''
import select as _dp_select, signal as _dp_signal, time as _dp_time
_dp_parent = os.getpid()
_dp_phase_fd = int(os.environ['R0016_DRAIN_PHASE_FD'])
_dp_data_fd = int(os.environ['R0016_DRAIN_DATA_FD'])
_dp_nonce = os.environ['R0016_NONCE']
_dp_deadline = int(os.environ['R0016_DRAIN_DEADLINE_NS']) / 1_000_000_000
_dp_expected = bytes.fromhex(os.environ['R0016_DRAIN_SENTINEL_HEX'])
_dp_reaped = False
_dp_status = None
_dp_master_closed = False

def _dp_emit(phase, **fields):
    value = dict(phase=phase, pid=os.getpid(), ppid=os.getppid(), uid=os.getuid(),
                 pgid=os.getpgrp(), monotonicNs=_dp_time.monotonic_ns(), nonce=_dp_nonce)
    value.update(fields)
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')
    if os.write(_dp_phase_fd, raw) != len(raw):
        raise RuntimeError('short phase write')

def _dp_abort(signum, frame):
    raise TimeoutError('controller requested subject termination at the original deadline')

def _dp_prepare_parent():
    _dp_signal.signal(_dp_signal.SIGTERM, _dp_abort)
    _dp_emit('parent.cleanup-handler.ready')

def _dp_drain(master):
    _dp_emit('drain.before')
    os.set_blocking(master, False)
    received = bytearray()
    maximum = len(_dp_expected) + _dp_expected.count(b'\n')
    while True:
        remaining = _dp_deadline - _dp_time.monotonic()
        if remaining <= 0:
            raise TimeoutError('original subject ceiling reached before the sentinel')
        if not _dp_select.select([master], [], [], remaining)[0]:
            raise TimeoutError('original subject ceiling reached while waiting for PTY data')
        try:
            chunk = os.read(master, 4096)
        except BlockingIOError:
            continue
        except OSError as error:
            _dp_emit('drain.read.error', errno=error.errno)
            raise
        if not chunk:
            _dp_emit('drain.eof', retainedBytes=len(received))
            raise RuntimeError('PTY EOF before complete sentinel')
        if os.write(_dp_data_fd, chunk) != len(chunk):
            raise RuntimeError('short PTY capture write')
        received.extend(chunk)
        _dp_emit('drain.read.after', readBytes=len(chunk), retainedBytes=len(received))
        if bytes(received).replace(b'\r\n', b'\n') == _dp_expected:
            _dp_emit('drain.sentinel', retainedBytes=len(received))
            return
        if len(received) >= maximum:
            raise RuntimeError('PTY bytes differ from the original sentinel')

def _dp_mark_reaped(done, status):
    global _dp_reaped, _dp_status
    if done != pid:
        raise RuntimeError('waitpid returned a different child')
    _dp_reaped, _dp_status = True, status

def _dp_mark_closed():
    global _dp_master_closed
    _dp_master_closed = True

def _dp_cleanup():
    global _dp_reaped, _dp_status, _dp_master_closed
    if os.getpid() != _dp_parent:
        return
    _dp_signal.signal(_dp_signal.SIGTERM, _dp_signal.SIG_IGN)
    child = globals().get('pid')
    master = globals().get('fd')
    deadline = min(_dp_time.monotonic() + 6, _dp_deadline + 6)
    signals = []
    if isinstance(master, int) and master >= 0 and not _dp_master_closed:
        os.close(master)
        _dp_master_closed = True
        _dp_emit('cleanup.master.closed')
    if isinstance(child, int) and child > 0 and not _dp_reaped:
        # waitpid certifies our unreaped direct child. With no SIGCHLD handler,
        # its PID cannot be recycled between this check and our one kill.
        done, status = os.waitpid(child, os.WNOHANG)
        if done:
            _dp_reaped, _dp_status = True, status
        else:
            try:
                os.kill(child, _dp_signal.SIGKILL)
                signals.append('SIGKILL')
            except ProcessLookupError:
                pass
            while _dp_time.monotonic() < deadline:
                done, status = os.waitpid(child, os.WNOHANG)
                if done:
                    _dp_reaped, _dp_status = True, status
                    break
                _dp_time.sleep(min(0.01, max(0, deadline - _dp_time.monotonic())))
    _dp_emit('cleanup.final', childPid=child, reaped=_dp_reaped, status=_dp_status,
             masterClosed=_dp_master_closed, signals=signals,
             noForkReturned=child is None)
'''


def statement(source):
    return one(ast.parse(source).body, "diagnostic statement")


def instrument(original):
    """AST proof: deleting only diagnostic calls restores the exact original."""
    tree = ast.parse(original)
    counts = {}

    class Add(ast.NodeTransformer):
        def visit_Assign(self, node):
            name = call_name(node.value)
            markers = {"pty.fork": ("fork", "childPid=pid, masterFd=fd"),
                       "os.open": ("tty.open", "terminalFd=terminal"),
                       "os.waitpid": ("waitpid", "waitedPid=done, status=status")}
            if name not in markers:
                return node
            counts[name] = counts.get(name, 0) + 1
            phase, fields = markers[name]
            before = []
            after = []
            if name == "os.waitpid":
                before = [statement("_dp_prepare_parent()"), statement("_dp_drain(fd)")]
                after = [statement("_dp_mark_reaped(done, status)")]
            return before + [statement("_dp_emit(%r)" % (phase + ".before")), node,
                             statement("_dp_emit(%r, %s)" % (phase + ".after", fields))] + after

        def visit_Expr(self, node):
            name = call_name(node.value)
            if name == "os.close":
                argument = one(node.value.args, "close argument")
                if not isinstance(argument, ast.Name) or argument.id not in ("terminal", "fd"):
                    raise ValueError("Original close target changed")
                name += "." + argument.id
            names = {"os.write": "tty.write", "os.close.terminal": "tty.close",
                     "os.close.fd": "master.close", "print": "result.print"}
            if name in names:
                counts[name] = counts.get(name, 0) + 1
                phase = names[name]
                suffix = [statement("_dp_mark_closed()")] if name == "os.close.fd" else []
                return [statement("_dp_emit(%r)" % (phase + ".before")), node,
                        statement("_dp_emit(%r)" % (phase + ".after"))] + suffix
            if name == "os._exit":
                counts[name] = counts.get(name, 0) + 1
                code = ast.literal_eval(one(node.value.args, "child exit status"))
                return [statement("_dp_emit('child.exit.before', exitCode=%r)" % code), node]
            return node

    amended = Add().visit(copy.deepcopy(tree))
    expected = {"pty.fork": 1, "os.open": 1, "os.waitpid": 1, "os.write": 1,
                "os.close.terminal": 1, "os.close.fd": 1, "print": 1, "os._exit": 2}
    if counts != expected:
        raise ValueError("Original operation inventory changed")
    removable = {"_dp_emit", "_dp_prepare_parent", "_dp_drain", "_dp_mark_reaped", "_dp_mark_closed"}

    class Remove(ast.NodeTransformer):
        def visit_Expr(self, node):
            return None if call_name(node.value) in removable else node

    restored = Remove().visit(copy.deepcopy(amended))
    if ast.dump(restored, include_attributes=False) != ast.dump(tree, include_attributes=False):
        raise ValueError("Removing diagnostics/drain did not restore original operations")
    original_import = amended.body.pop(0)
    wrapper = ast.Try(body=[statement("_dp_emit('subject.start')")] + amended.body +
                      [statement("_dp_emit('subject.complete')")],
                      handlers=[ast.ExceptHandler(type=ast.Name(id="BaseException", ctx=ast.Load()),
                                name="_dp_error", body=[statement("_dp_emit('subject.exception', errorType=type(_dp_error).__name__, message=str(_dp_error)[:300])"), ast.Raise()])],
                      orelse=[], finalbody=[statement("_dp_cleanup()")])
    result = ast.Module(body=[original_import] + ast.parse(SUBJECT_HELPERS).body + [wrapper], type_ignores=[])
    ast.fix_missing_locations(result)
    rendered = ast.unparse(result) + "\n"
    compile(rendered, "terminal-probe.drain.py", "exec")
    return rendered, {"originalOperations": counts, "removingDiagnosticsAndDrainRestoresOriginalAst": True,
                      "soleNormalPathOperationChange": "parent reads and retains original sentinel before original blocking waitpid"}


def read_phases(path, nonce):
    rows = []
    errors = []
    for index, line in enumerate(path.read_bytes().splitlines(), 1):
        try:
            row = json.loads(line)
            if row.get("nonce") != nonce or not isinstance(row.get("phase"), str) or type(row.get("pid")) is not int:
                raise ValueError("wrong phase identity or shape")
            rows.append(row)
        except Exception as error:
            errors.append({"line": index, "error": str(error)})
    return rows, errors


def lifecycle(rows, launch_pid):
    parents = [r for r in rows if r["pid"] == launch_pid]
    forks = [r for r in parents if r["phase"] == "fork.after" and type(r.get("childPid")) is int and r["childPid"] > 0]
    child = forks[0]["childPid"] if len(forks) == 1 else None
    finals = [r for r in parents if r["phase"] == "cleanup.final"]
    final = finals[-1] if len(finals) == 1 else {}
    reaped = child is not None and final.get("childPid") == child and final.get("reaped") is True
    return {"childPid": child, "reaped": reaped, "status": final.get("status"),
            "masterClosed": final.get("masterClosed") is True,
            "complete": reaped and final.get("masterClosed") is True,
            "cleanupSignals": final.get("signals")}


def assess(record, rows, stdout, stderr, master, sentinel):
    """Strict independent oracle: a sentinel or intended exit alone cannot pass."""
    reasons = []
    life = lifecycle(rows, record.get("launchPid"))
    if record.get("executionOutcome") != "TERMINAL_EXIT" or record.get("returncode") != 0:
        reasons.append("subject did not terminate successfully within original ceiling")
    if record.get("capturesStable") is not True or record.get("phaseErrors"):
        reasons.append("capture termination or phase integrity unproven")
    if not life["complete"] or life["status"] != 0 or life["cleanupSignals"] != []:
        reasons.append("original child did not exit 0 and reap without failure cleanup")
    if master.replace(b"\r\n", b"\n") != sentinel:
        reasons.append("raw PTY capture does not equal original sentinel after newline normalization")
    try:
        value = json.loads(stdout)
        if (not isinstance(value, dict) or set(value) != {"controllingTerminalAllowed", "childExit"}
                or value["controllingTerminalAllowed"] is not True or type(value["childExit"]) is not int or value["childExit"] != 0):
            raise ValueError("wrong terminal result")
    except (ValueError, UnicodeError, TypeError):
        reasons.append("complete original terminal JSON missing or invalid")
    if stderr:
        reasons.append("subject stderr is nonempty")
    parents = [r for r in rows if r["pid"] == record.get("launchPid")]
    names = [r["phase"] for r in parents]
    required = ["drain.before", "drain.sentinel", "waitpid.before", "waitpid.after",
                "master.close.after", "result.print.after", "subject.complete", "cleanup.final"]
    if any(names.count(name) != 1 for name in required) or [n for n in names if n in required] != required:
        reasons.append("parent drain/reap/completion ordering is not established")
    waits = [r for r in parents if r["phase"] == "waitpid.after"]
    if len(waits) != 1 or waits[0].get("waitedPid") != life["childPid"] or waits[0].get("status") != 0:
        reasons.append("actual successful waitpid receipt missing")
    completions = [r for r in parents if r["phase"] == "subject.complete"]
    if (len(completions) != 1 or type(completions[0].get("monotonicNs")) is not int
            or type(record.get("deadlineMonotonicNs")) is not int
            or completions[0]["monotonicNs"] > record["deadlineMonotonicNs"]):
        reasons.append("subject completion before the original deadline is unproven")
    child_rows = [r for r in rows if r["pid"] == life["childPid"] and r.get("ppid") == record.get("launchPid")]
    child_names = [r["phase"] for r in child_rows]
    child_required = ["tty.open.after", "tty.write.after", "tty.close.after", "child.exit.before"]
    if [n for n in child_names if n in child_required] != child_required:
        reasons.append("original child operation evidence incomplete")
    return {"drainCorrectionObserved": not reasons, "reasons": reasons, "lifecycle": life,
            "productRowsExecuted": 0}


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


def run_case(case, env, command, sentinel, cwd):
    paths = {name: case / name for name in ("stdout.raw", "stderr.raw", "phases.raw.jsonl", "pty-master.raw")}
    record = {"case": case.name, "command": command, "subjectSeconds": SUBJECT_SECONDS,
              "cleanupSeconds": CLEANUP_SECONDS, "productRowsExecuted": 0,
              "executionOutcome": "NOT_LAUNCHED", "returncode": None, "capturesStable": False}
    process = None
    with paths["stdout.raw"].open("xb", buffering=0) as stdout, paths["stderr.raw"].open("xb", buffering=0) as stderr:
        phase_fd = os.open(paths["phases.raw.jsonl"], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        data_fd = os.open(paths["pty-master.raw"], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        started = time.monotonic()
        deadline = started + SUBJECT_SECONDS
        environment = dict(env, R0016_DRAIN_PHASE_FD=str(phase_fd), R0016_DRAIN_DATA_FD=str(data_fd),
                           R0016_DRAIN_DEADLINE_NS=str(int(deadline * 1_000_000_000)), R0016_DRAIN_SENTINEL_HEX=sentinel.hex())
        record.update(environment=environment, startedMonotonicNs=int(started * 1_000_000_000),
                      deadlineMonotonicNs=int(deadline * 1_000_000_000),
                      cwd=str(cwd), startNewSession=True, stdin="DEVNULL")
        write_json(case / "launch.json", record)
        try:
            process = subprocess.Popen(command, env=environment, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True,
                                       pass_fds=(phase_fd, data_fd))
            record["launchPid"] = process.pid
            write_json(case / "launch.json", record)
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
                record["executionOutcome"] = "TERMINAL_EXIT"
            except subprocess.TimeoutExpired:
                record["executionOutcome"] = "TIMEOUT"
                record["subjectElapsedSeconds"] = time.monotonic() - started
                write_json(case / "execution.json", record)
                cleanup_deadline = deadline + CLEANUP_SECONDS
                # Cooperative handler closes the owned master and reaps its
                # direct child. Reserve half the existing six-second allowance
                # for identity-verified fallback if that handler cannot return.
                live_phases, _ = read_phases(paths["phases.raw.jsonl"], env["R0016_NONCE"])
                ready = any(r["pid"] == process.pid and r["phase"] == "parent.cleanup-handler.ready" for r in live_phases)
                if not ready:
                    record["fallbackCleanup"] = force_cleanup(process, case, environment, cleanup_deadline)
                else:
                    process.send_signal(signal.SIGTERM)
                    record["cleanupRequest"] = "SIGTERM to our unreaped direct subject with recorded cleanup handler"
                    try:
                        process.wait(timeout=max(0, min(CLEANUP_SECONDS / 2, cleanup_deadline - time.monotonic())))
                    except subprocess.TimeoutExpired:
                        record["fallbackCleanup"] = force_cleanup(process, case, environment, cleanup_deadline)
            record["returncode"] = process.poll()
        except BaseException as error:
            record["error"] = {"type": type(error).__name__, "message": str(error)}
            if process is not None and process.poll() is None:
                record["fallbackCleanup"] = force_cleanup(process, case, environment,
                                                          min(time.monotonic() + CLEANUP_SECONDS, deadline + CLEANUP_SECONDS))
                record["returncode"] = process.poll()
        finally:
            os.close(phase_fd)
            os.close(data_fd)
    record.setdefault("subjectElapsedSeconds", time.monotonic() - started)
    rows, errors = read_phases(paths["phases.raw.jsonl"], env["R0016_NONCE"])
    record["phases"], record["phaseErrors"] = rows, errors
    life = lifecycle(rows, record.get("launchPid"))
    record["capturesStable"] = record["returncode"] is not None and (life["complete"] or record.get("fallbackCleanup", {}).get("complete") is True)
    record["acquisitionComplete"] = record["capturesStable"] and not errors
    record["captures"] = {name: binding(path) for name, path in paths.items()}
    record["oracle"] = assess(record, rows, paths["stdout.raw"].read_bytes(), paths["stderr.raw"].read_bytes(),
                              paths["pty-master.raw"].read_bytes(), sentinel)
    record["classification"] = ("DIAGNOSTIC_DRAIN_CORRECTION_OBSERVED" if record["oracle"]["drainCorrectionObserved"]
                                else "DIAGNOSTIC_FAILURE_OBSERVED" if record["acquisitionComplete"] else "DIAGNOSTIC_ACQUISITION_INCOMPLETE")
    write_json(case / "result.json", record)
    return record


def metadata(command, output, label, env):
    stdout_path, stderr_path = output / (label + ".stdout.raw"), output / (label + ".stderr.raw")
    with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
        run = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=5, check=False)
    value = {"command": command, "returncode": run.returncode, "stdout": binding(stdout_path), "stderr": binding(stderr_path)}
    write_json(output / (label + ".json"), value)
    if run.returncode:
        raise RuntimeError("Metadata acquisition failed: " + label)
    return stdout_path.read_text(), value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin" and not args.inspect_only:
        print(json.dumps({"classification": "DIAGNOSTIC_UNSUPPORTED_HOST", "nativeSubjectsExecuted": False, "productRowsExecuted": 0}))
        return 2
    repo = args.repo.resolve(strict=True)
    output = fresh_directory(args.output.absolute())
    result = {"schema": "r0016-pty-drain-diagnostic.v1", "classification": "DIAGNOSTIC_ACQUISITION_INCOMPLETE",
              "scope": "Two original-child PTY drain observations; no installer or product qualification",
              "nativeSubjectsExecuted": False, "productRowsExecuted": 0, "inspectOnly": args.inspect_only,
              "archivedRed": dict(ARCHIVED_RED, replayed=False, artifactReadByThisRun=False),
              "probe": binding(Path(__file__).resolve()), "host": {"system": platform.system(), "kernel": platform.release(),
              "architecture": platform.machine(), "macOSVersion": platform.mac_ver()[0]},
              "python": {"executable": sys.executable, "version": sys.version, "binary": binding(Path(sys.executable).resolve())},
              "cases": []}
    write_json(output / "result.json", result)
    try:
        raw = (repo / SOURCE_PATH).read_bytes()
        functions, env_ast, denials, original, sentinel = extract(raw)
        amended, proof = instrument(original)
        frozen = fresh_directory(output / "frozen")
        for name, data in (("tests__install-preview.py", raw), ("terminal-probe.original.py", original.encode()),
                           ("terminal-probe.drain.py", amended.encode()),
                           ("darwin_profile.extracted.py", (ast.get_source_segment(raw.decode(), functions["darwin_profile"]) + "\n").encode())):
            (frozen / name).write_bytes(data)
        result["frozenManifest"] = {p.name: binding(p) for p in sorted(frozen.iterdir())}
        result["sourceTransformation"] = proof
        control = fresh_directory(output / "metadata")
        home, temp = fresh_directory(control / "home"), fresh_directory(control / "tmp")
        metadata_env = {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8" if platform.system() == "Darwin" else "C.UTF-8",
                        "HOME": str(home), "TMPDIR": str(temp), "GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        git = shutil.which("git")
        if not git:
            raise RuntimeError("Read-only Git identity command unavailable")
        identities, result["gitAcquisition"] = metadata([git, "-C", str(repo), "rev-parse", "HEAD", "HEAD^{tree}"], control, "git-identity", metadata_env)
        parts = identities.splitlines()
        if len(parts) != 2 or any(len(p) != 40 or any(c not in "0123456789abcdef" for c in p) for p in parts):
            raise ValueError("Malformed repository identity")
        result["commit"], result["tree"] = parts
        if not args.inspect_only:
            sandbox = Path("/usr/bin/sandbox-exec")
            if not sandbox.is_file() or not os.access(sandbox, os.X_OK):
                raise RuntimeError("Native sandbox-exec required; no uncontained replacement")
            result["sandbox"] = binding(sandbox)
            bash_version, bash_record = metadata(["/bin/bash", "--version"], control, "bash-version", metadata_env)
            result["bash"] = {"binary": binding(Path("/bin/bash")), "versionAcquisition": bash_record}
            if "version 3.2." not in bash_version.splitlines()[0]:
                raise RuntimeError("Actual Apple /bin/bash 3.2 required")
        plans = []
        for label in ("same-profile", "host-control"):
            case = fresh_directory(output / label)
            subject = fresh_directory(case / "subject")
            home, temp = fresh_directory(subject / "home"), fresh_directory(subject / "tmp")
            terminal = fresh_directory(case / "terminal-probe")
            (case / "bootstrap.sh").write_text(denials, encoding="ascii")
            namespace = {"ROOT": case}
            module = ast.Module(body=[copy.deepcopy(functions["darwin_profile"])], type_ignores=[])
            exec(compile(ast.fix_missing_locations(module), "pinned-darwin-profile", "exec"), namespace)
            profile = namespace["darwin_profile"](terminal)
            env = eval(compile(ast.Expression(copy.deepcopy(env_ast)), "pinned-fixture-environment", "eval"),
                       {"HOST": "Darwin", "ARGS": SimpleNamespace(bash="/bin/bash"), "root": case,
                        "home": home, "temp": temp, "route": "github", "secrets": secrets})
            command = [sys.executable, "-c", amended]
            if label == "same-profile":
                command = ["/usr/bin/sandbox-exec", "-f", str(profile)] + command
            plan = {"case": label, "profileApplied": label == "same-profile", "profile": binding(profile),
                    "environment": env, "command": command, "subjectSeconds": SUBJECT_SECONDS,
                    "sentinelBase64": base64.b64encode(sentinel).decode(), "productRowsExecuted": 0}
            write_json(case / "plan.json", plan)
            plans.append((case, env, command))
        if args.inspect_only:
            result["classification"] = "DIAGNOSTIC_INSPECTION_ONLY"
        else:
            for case, env, command in plans:
                if result["nativeSubjectsExecuted"] is not True:
                    result["nativeSubjectsExecuted"] = None
                observed = run_case(case, env, command, sentinel, repo)
                result["cases"].append(observed)
                result["nativeSubjectsExecuted"] = any(row.get("launchPid") for row in result["cases"])
                write_json(output / "result.json", result)
                if not observed["capturesStable"]:
                    result["remainingCaseSuppressed"] = "Prior owned-process cleanup is incomplete"
                    break
            result["classification"] = ("DIAGNOSTIC_DRAIN_CORRECTION_OBSERVED" if len(result["cases"]) == 2
                and all(c["oracle"]["drainCorrectionObserved"] for c in result["cases"])
                else "DIAGNOSTIC_FAILURE_OBSERVED" if len(result["cases"]) == 2 and all(c["acquisitionComplete"] for c in result["cases"])
                else "DIAGNOSTIC_ACQUISITION_INCOMPLETE")
        result["inferenceLimit"] = "A drain/reap success supports this harness correction; it does not identify a kernel syscall, qualify installer rows, or authorize release."
    except BaseException as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    write_json(output / "result.json", result)
    print(json.dumps({"classification": result["classification"], "result": str(output / "result.json"),
                      "nativeSubjectsExecuted": result["nativeSubjectsExecuted"], "productRowsExecuted": 0}))
    return 0 if result["classification"] in ("DIAGNOSTIC_INSPECTION_ONLY", "DIAGNOSTIC_DRAIN_CORRECTION_OBSERVED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
