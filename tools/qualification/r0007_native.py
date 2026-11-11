#!/usr/bin/env python3
"""Bind and collect R0007 native evidence, serially, without changing its oracles.

Zero exit means the selected observations met their declared source assertions,
including exact intended mutant rejections. Native pixel/preservation acceptance
remains PARTIAL. Every invocation retains a fresh directory and producer exits.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


DRIVER = "tools/cp9/r0007_browser.py"
FIXTURE = "tests/rlgwo/prayer-browser-fixture.cjs"
RUNTIME = "tools/cp9/browser_runtime.py"
FONT_OBSERVER = "tools/cp9/r0007_font_observer.js"
FONT_INGRESS = "tools/cp9/r0007_font_ingress.py"
DEFAULT_RECIPE = "tests/rlgwo/R0007-next-event-recipes.json"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path, committed_blob=None):
    path = Path(path)
    digest = hashlib.sha256()
    blob = hashlib.sha1(("blob " + str(path.stat().st_size) + "\0").encode(), usedforsecurity=False) if committed_blob else None
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            if blob is not None:
                blob.update(chunk)
    if blob is not None and blob.hexdigest() != committed_blob:
        raise ValueError("bound source file differs from committed bytes: " + str(path))
    return digest.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def clean_identity(root):
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("source-root must be the actual Git worktree root")
    dirty = git(root, "status", "--porcelain", "--untracked-files=normal")
    if dirty:
        raise ValueError("candidate is not clean; commit the reviewed source/recipes before native acquisition")
    return {"commit": git(root, "rev-parse", "HEAD"), "tree": git(root, "rev-parse", "HEAD^{tree}")}


def select_cases(packet, requested):
    cases = packet.get("cases", [])
    ids = [case.get("caseId") for case in cases]
    if not ids or len(ids) != len(set(ids)) or any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids):
        raise ValueError("case ids must be nonempty, unique, safe directory names")
    by_id = dict(zip(ids, cases))
    selected = set(requested or ids)
    if selected - set(ids):
        raise ValueError("unknown case-id: " + ", ".join(sorted(selected - set(ids))))
    pending = list(selected)
    while pending:
        case = by_id[pending.pop()]
        if case.get("cacheSeedsFromCase"):
            raise ValueError("this serial independent-case launcher does not admit cross-case cache seeding")
        if case.get("expectedFailure"):
            if not isinstance(case.get("expectedFailureContains"), str) or not case["expectedFailureContains"]:
                raise ValueError("mutant needs a nonempty exact expectedFailureContains: " + case["caseId"])
            controls = case.get("healthyControlCaseIds")
            if not isinstance(controls, list) or not controls:
                raise ValueError("mutant needs declared healthy controls: " + case["caseId"])
            for control in controls:
                if control not in by_id or by_id[control].get("expectedFailure"):
                    raise ValueError("mutant healthy control is missing or is itself a mutant: " + str(control))
                if control not in selected:
                    selected.add(control)
                    pending.append(control)
    # Healthy controls precede mutants even if a recipe author lists them later.
    ordered = [c for c in cases if c["caseId"] in selected and not c.get("expectedFailure")]
    ordered += [c for c in cases if c["caseId"] in selected and c.get("expectedFailure")]
    return ordered


def bind_packet(root, recipe_path, identity, selected):
    original = json.loads(recipe_path.read_text(encoding="utf-8"))
    if original.get("schema") != "remaining-prayer-cases/v1" or original.get("issue") != 7:
        raise ValueError("recipe must be remaining-prayer-cases/v1 for issue7")
    packet = copy.deepcopy(original)
    required = {"src/native/index.html", "index.html", "offline.html", "config.js", DRIVER, FIXTURE, RUNTIME, FONT_OBSERVER,
                "tools/qualification/r0007_native.py", recipe_path.relative_to(root).as_posix()}
    if any("fontIngress" in case for case in selected):
        required.add(FONT_INGRESS)
    required.update(original.get("sourceFiles", {}))
    required.update(original.get("bindingInstructions", {}).get("sourcePaths", []))
    # Bind the tracked runtime once, without copying generated offline payloads.
    runtime_paths = git(root, "ls-files", "--", "real-sky", "moon").splitlines()
    required.update(p for p in runtime_paths if not p.startswith(("moon/src/", "moon/tests/", "moon/tools/")))
    # Git status deliberately omits ignored files and can hide assume-unchanged
    # paths. Bind every declared source/recipe to a real blob in the immutable
    # commit, then compare its actual bytes during the same SHA-256 read.
    committed = {}
    for row in git(root, "ls-tree", "-r", "-z", identity["commit"]).split("\0"):
        if row:
            header, relative = row.split("\t", 1)
            mode, kind, blob = header.split()
            committed[relative] = (mode, kind, blob)
    files = {}
    for relative in sorted(required):
        path = root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError("invalid bound source file: " + relative)
        entry = committed.get(relative)
        if entry is None or entry[0] not in {"100644", "100755"} or entry[1] != "blob":
            raise ValueError("bound source file is not a committed regular file: " + relative)
        files[relative] = sha(path, committed_blob=entry[2])
    packet["sourceCommit"] = identity["commit"]
    packet["sourceTree"] = identity["tree"]
    packet["sourceFiles"] = files
    packet["cases"] = selected
    packet["bindingStatus"] = "BOUND_CANDIDATE_NOT_EXECUTED"
    packet["nativeStatus"] = "BOUND_NOT_EXECUTED"
    # The only case-list change is the explicitly reported selection; its oracles
    # and inputs remain byte-for-byte equivalent as JSON values to the recipes.
    by_id = {c["caseId"]: c for c in original["cases"]}
    if any(c != by_id[c["caseId"]] for c in packet["cases"]):
        raise ValueError("case input/oracle changed during binding")
    packet["acquisitionBinding"] = {"recipe": recipe_path.relative_to(root).as_posix(), "recipeSha256": sha(recipe_path),
                                    "identity": identity, "oraclesChanged": False}
    return packet


def run_producer(command, cwd, env, directory, timeout):
    directory.mkdir(parents=True, exist_ok=False)
    record = {"command": command, "startedUtc": utc(), "timeoutSeconds": timeout, "launched": False}
    write(directory / "producer.json", record)
    with (directory / "producer.log").open("wb") as output:
        options = {"cwd": str(cwd), "env": env, "stdout": output, "stderr": subprocess.STDOUT}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            options["start_new_session"] = True
        try:
            process = subprocess.Popen(command, **options)
            record.update(launched=True, pid=process.pid)
            write(directory / "producer.json", record)
            try:
                record["exitCode"] = process.wait(timeout=timeout)
                record["terminalState"] = "exited"
            except subprocess.TimeoutExpired:
                record["terminalState"] = "timed-out-owned-containment"
                # Act only on our still-owned Popen child/process group. A timeout
                # never earns assertion credit or authorizes another browser.
                if os.name == "nt":
                    cleanup = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, text=True)
                    (directory / "containment.log").write_text(cleanup.stdout + cleanup.stderr, encoding="utf-8")
                    record["containmentExitCode"] = cleanup.returncode
                elif process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    record["exitCode"] = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name != "nt" and process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    try:
                        record["exitCode"] = process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        record["exitCode"] = None
                record["cleanupQualification"] = "UNVERIFIED_STOP_NEW_LAUNCHES"
        except Exception as error:
            record["failure"] = repr(error)
            record.setdefault("exitCode", None)
            record.setdefault("terminalState", "launch-or-supervision-error")
    record["finishedUtc"] = utc()
    record["logSha256"] = sha(directory / "producer.log")
    write(directory / "producer.json", record)
    return record


def read_object(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evidence must be a JSON object: " + path.name)
    return value


def identity_matches(identity, engine):
    executable = identity.get("executable")
    checksum = identity.get("executableSha256")
    if (engine not in {"chromium", "firefox"} or identity.get("engineRequested") != engine
            or identity.get("family") != engine or identity.get("os") != platform.system()
            or identity.get("machine") != platform.machine() or not isinstance(identity.get("version"), str)
            or not identity["version"].strip() or type(identity.get("headless")) is not bool
            or identity.get("executableSelection") not in {"explicit-override", "runtime-selected", "playwright-managed"}
            or not isinstance(executable, str) or not isinstance(checksum, str)
            or re.fullmatch(r"[0-9a-f]{64}", checksum) is None
            or engine == "chromium" and identity.get("chromiumSandboxRequested") is not True):
        return False
    path = Path(executable)
    return path.is_absolute() and path.is_file() and sha(path) == checksum


def presentation_associations(case, case_dir, trace, setup_ok):
    """Record capture associations; no automatic result accepts first visible pixels."""
    captures = [a for a in case.get("orderedActions", []) if a.get("type") == "capture"]
    videos = []
    if setup_ok:
        for path in sorted((case_dir / "video").glob("*.webm")):
            if path.is_file() and path.stat().st_size:
                videos.append({"path": str(path.relative_to(case_dir)), "sha256": sha(path)})
    results = []
    for action in captures:
        name = action.get("name")
        result = {"capture": name, "firstRenderRequested": bool(action.get("firstRender")),
                  "status": "UNVERIFIED_NO_NATIVE_SETUP"}
        results.append(result)
        if not setup_ok:
            continue
        result["status"] = "UNVERIFIED_NO_CAPTURE_ARTIFACT"
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9_-]+", name) is None:
            result.update(status="UNVERIFIED_MALFORMED_CAPTURE_EVIDENCE", reason="invalid capture name")
            continue
        path = case_dir / (name + "-presentation.json")
        if not path.is_file() or not videos:
            continue
        try:
            presentation = read_object(path)
            ordinals = [presentation.get(k) for k in ("beforeOrdinal", "afterOrdinal", "receiptOrdinal")]
            kind = "first-matching-render" if action.get("firstRender") else "read-only-checkpoint" if action.get("readOnly") else "latest-render"
            if (any(type(n) is not int or n < 0 for n in ordinals)
                    or presentation.get("firstRenderRequested") is not bool(action.get("firstRender"))
                    or presentation.get("selectionKind") != kind
                    or presentation.get("firstPredicate") != action.get("firstPredicate")
                    or presentation.get("capture") not in {"native-full-viewport", "native-video-only"}):
                raise ValueError("capture declaration/ordinal binding is malformed")
            checkpoints = trace.get("checkpointSnapshots", [])
            if any(not isinstance(row, dict) for row in checkpoints):
                raise ValueError("malformed capture checkpoints")
            matching = [row for row in checkpoints if row.get("checkpoint") == name]
            if (len(matching) != 1 or matching[0].get("renderOrdinal") != ordinals[2]
                    or action.get("firstRender") and matching[0].get("stage") != "render-completed"):
                raise ValueError("capture receipt does not bind its actual named checkpoint")
            result.update(beforeOrdinal=ordinals[0], afterOrdinal=ordinals[1], receiptOrdinal=ordinals[2],
                          selectionKind=kind, presentationSha256=sha(path), video=videos)
            if presentation["capture"] == "native-full-viewport":
                still = case_dir / (name + ".png")
                if not still.is_file() or not still.stat().st_size:
                    continue
                result["image"] = {"path": still.name, "sha256": sha(still)}
            mismatch = any(m.get("capture") == name for m in trace.get("captureMismatches", []))
            if mismatch or len(set(ordinals)) != 1:
                result["status"] = "UNVERIFIED_ORDINAL_MISMATCH"
            else:
                result["status"] = "RECORDED_PENDING_INDEPENDENT_REVIEW" if action.get("firstRender") else "EVENTUAL_STATE_ONLY"
        except (OSError, ValueError, TypeError) as error:
            result.update(status="UNVERIFIED_MALFORMED_CAPTURE_EVIDENCE", reason=str(error))
    return results


def adjudicate(case, output, producer, source_files, controls, expected_engine=None):
    case_dir = output / case["caseId"]
    trace_path = case_dir / "trace.json"
    result = {"caseId": case["caseId"], "accepted": False, "expectedFailure": bool(case.get("expectedFailure")),
              "producerExitCode": producer.get("exitCode"), "producerTerminalState": producer.get("terminalState"),
              "status": "UNVERIFIED", "pixelAcceptance": "PARTIAL_INDEPENDENT_PIXELS_REQUIRED",
              "cleanupEstablished": False, "nativeSetupEstablished": False, "engineSetupFailed": False,
              "firstFrameAcceptance": "UNVERIFIED_NO_NATIVE_SETUP", "firstPresentationAssociation": "UNVERIFIED_NO_NATIVE_SETUP",
              "presentationAssociations": presentation_associations(case, case_dir, {}, False)}
    summary_path = output / "summary.json"
    if producer.get("terminalState") != "exited" or not trace_path.is_file() or not summary_path.is_file():
        result["reason"] = "producer/trace/final-summary missing; setup or cleanup is not assertion evidence"
        return result
    try:
        summary = read_object(summary_path)
        trace = read_object(trace_path)
        result.update(actualStatus=trace.get("status"), failure=trace.get("failure"), traceSha256=sha(trace_path))
        receipts = summary.get("receipts")
        result["cleanupEstablished"] = (summary.get("status") == "PARTIAL_NATIVE_REVIEW_REQUIRED"
            and isinstance(receipts, list) and len(receipts) == 1 and isinstance(receipts[0], dict)
            and receipts[0].get("caseId") == case["caseId"] and trace.get("caseId") == case["caseId"]
            and receipts[0].get("status") == trace.get("status")
            and isinstance(receipts[0].get("trace"), str) and Path(receipts[0]["trace"]).resolve() == trace_path.resolve())
        if expected_engine is None:
            command = producer.get("command", [])
            if isinstance(command, list) and command.count("--engine") == 1:
                index = command.index("--engine") + 1
                expected_engine = command[index] if index < len(command) else None
        identity_path = case_dir / "browser-identity.json"
        identity = read_object(identity_path) if identity_path.is_file() else {}
        hashes_path = case_dir / "document-hashes.json"
        hashes = read_object(hashes_path) if hashes_path.is_file() else {}
        snapshots = trace.get("snapshots", [])
        mismatches = trace.get("captureMismatches", [])
        if (not isinstance(snapshots, list) or any(not isinstance(s, dict) for s in snapshots)
                or not isinstance(mismatches, list) or any(not isinstance(m, dict) for m in mismatches)):
            raise ValueError("malformed render/mismatch receipts")
        real_render = any(s.get("stage") == "render-completed" and isinstance(s.get("render"), dict) and s["render"] for s in snapshots)
        setup_ok = (identity_matches(identity, expected_engine) and hashes.get("source") == source_files[case["entry"]]
                    and hashes.get("fixture") == source_files[FIXTURE] and isinstance(hashes.get("observed"), str)
                    and re.fullmatch(r"[0-9a-f]{64}", hashes["observed"]) is not None
                    and real_render and isinstance(trace.get("checkpointSnapshots"), list)
                    and trace.get("pageErrors") == [] and trace.get("unexpected") == []
                    and trace.get("variant") == case.get("variant"))
        result["nativeSetupEstablished"] = bool(setup_ok)
        result["engineSetupFailed"] = (not setup_ok and trace.get("status") == "FAIL"
            and trace.get("failureStage") in {"browser-launch", "browser-context"}
            and trace.get("actions") == [] and not real_render)
        result["presentationAssociations"] = presentation_associations(case, case_dir, trace, setup_ok)
        if setup_ok:
            result["firstFrameAcceptance"] = result["firstPresentationAssociation"] = "UNVERIFIED_PENDING_INDEPENDENT_REVIEW"
        capture_evidence_ok = all(p["status"] in {"RECORDED_PENDING_INDEPENDENT_REVIEW", "EVENTUAL_STATE_ONLY", "UNVERIFIED_ORDINAL_MISMATCH"}
                                  for p in result["presentationAssociations"])
        result["captureEvidenceEstablished"] = bool(setup_ok and capture_evidence_ok)
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.update(status="MALFORMED_OR_UNREADABLE_NATIVE_EVIDENCE", reason=repr(error))
        return result
    terminal_ok = result["cleanupEstablished"] and type(producer.get("exitCode")) is int
    if not case.get("expectedFailure"):
        source_assertions_met = trace.get("status") in {"PASS_ASSERTIONS_PENDING_PIXEL_REVIEW", "PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED"}
        result["accepted"] = bool(setup_ok and terminal_ok and capture_evidence_ok and producer["exitCode"] == 0 and source_assertions_met)
        result["status"] = "SOURCE_ASSERTIONS_MET_PIXELS_PENDING" if result["accepted"] else "OBSERVATION_NOT_ACCEPTED"
    else:
        # A timeout, missing anchor, page error, driver exception or unrelated
        # failing assertion cannot be converted into a killed-mutant verdict.
        failure = trace.get("failure", "")
        controls_ok = bool(case.get("healthyControlCaseIds")) and all(controls.get(c) is True for c in case["healthyControlCaseIds"])
        result["healthyControlsAccepted"] = controls_ok
        result["expectedFailureContains"] = case["expectedFailureContains"]
        result["accepted"] = bool(setup_ok and terminal_ok and capture_evidence_ok and controls_ok and producer["exitCode"] == 1
                              and trace.get("status") == "FAIL" and trace.get("expectedOracleFailure") is True
                              and isinstance(failure, str) and failure.startswith("AssertionError(") and case["expectedFailureContains"] in failure)
        result["status"] = "INTENDED_MUTANT_ASSERTION_REJECTED_PIXELS_PENDING" if result["accepted"] else "MUTANT_NOT_QUALIFIED"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--recipe", type=Path, default=Path(DEFAULT_RECIPE))
    parser.add_argument("--engine", action="append", choices=["chromium", "firefox"])
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--include-mutants", action="store_true", help="Add declared mutationCaseIds to the recipe's default healthy selection")
    parser.add_argument("--case-timeout-seconds", type=int, default=240)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--video-only", action="store_true")
    args = parser.parse_args(argv)
    root, evidence = args.source_root.resolve(), args.evidence_root.resolve()
    if evidence.is_relative_to(root) or args.case_timeout_seconds <= 0:
        parser.error("evidence-root must be outside source-root; timeout must be positive")
    engines = args.engine or ["chromium", "firefox"]
    if len(engines) != len(set(engines)):
        parser.error("duplicate engines are not additional independent attempts")
    if len(engines) > 1 and os.environ.get("SALAH_BROWSER_EXECUTABLE"):
        parser.error("SALAH_BROWSER_EXECUTABLE is engine-specific; use one --engine or clear it")
    evidence.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="r0007-native-", dir=evidence))
    summary = {"schema": "r0007-native-acquisition/v1", "status": "PARTIAL", "startedUtc": utc(), "runRoot": str(run),
               "nativeAcceptance": "PARTIAL_INDEPENDENT_PIXELS_REQUIRED", "results": [], "planned": [], "unattempted": []}
    print("R0007 native evidence:", run, flush=True)
    try:
        identity = clean_identity(root)
        recipe = args.recipe if args.recipe.is_absolute() else root / args.recipe
        recipe = recipe.resolve()
        if not recipe.is_relative_to(root):
            raise ValueError("recipes must be committed within the candidate source root")
        original = json.loads(recipe.read_text(encoding="utf-8"))
        requested = list(args.case_id or original.get("execution", {}).get("defaultCaseIds", []))
        if args.include_mutants:
            requested += original.get("execution", {}).get("mutationCaseIds", [])
        selected = select_cases(original, requested)
        packet = bind_packet(root, recipe, identity, selected)
        bound = run / "bound-cases.json"
        write(bound, packet)
        lease = run / "capacity-lease.json"
        write(lease, {"resource": "heavy-browser", "status": "GRANTED", "owner": "prayer", "sourceCommit": identity["commit"],
                      "scope": "THIS_PRIVATE_JOB_SERIAL_INVOCATION_ONLY", "capacity": 1, "pid": os.getpid(), "issuedUtc": utc()})
        summary.update(identity=identity, requestedCaseIds=args.case_id, selectedCaseIds=[c["caseId"] for c in selected],
                       engines=engines, boundPacketSha256=sha(bound), recipeSha256=sha(recipe), sourceFiles=packet["sourceFiles"])
        summary["planned"] = [{"engine": e, "caseId": c["caseId"]} for e in engines for c in selected]
        write(run / "summary.json", summary)
        summary["host"] = {"os": platform.system(), "release": platform.release(), "python": sys.version,
                           "node": subprocess.check_output(["node", "--version"], text=True).strip(),
                           "playwright": importlib.metadata.version("playwright"), "runnerOS": os.environ.get("RUNNER_OS"),
                           "imageVersion": os.environ.get("ImageVersion"), "runId": os.environ.get("GITHUB_RUN_ID"),
                           "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "workflowSha": os.environ.get("GITHUB_SHA")}
        stopped = False
        for engine in engines:
            controls = {}
            engine_setup_failed = False
            for case in selected:
                if stopped:
                    summary["unattempted"].append({"engine": engine, "caseId": case["caseId"], "reason": "previous producer cleanup/currentness not established"})
                    continue
                if engine_setup_failed:
                    summary["unattempted"].append({"engine": engine, "caseId": case["caseId"], "reason": "previous browser setup failed on this engine; unchanged setup not retried"})
                    continue
                if clean_identity(root) != identity:
                    raise ValueError("candidate changed during native acquisition")
                attempt = run / engine / case["caseId"] / "attempt-0001"
                consumer = attempt / "consumer"
                command = [sys.executable, str(root / DRIVER), "--issue", "7", "--engine", engine, "--source-root", str(root),
                           "--cases", str(bound), "--output", str(consumer), "--capacity-lease", str(lease), "--case-id", case["caseId"]]
                if args.headed:
                    command.append("--headed")
                if args.video_only:
                    command.append("--video-only")
                producer = run_producer(command, root, os.environ.copy(), attempt, args.case_timeout_seconds)
                try:
                    result = adjudicate(case, consumer, producer, packet["sourceFiles"], controls, expected_engine=engine)
                except Exception as error:
                    result = {"caseId": case["caseId"], "accepted": False, "cleanupEstablished": False,
                              "status": "MALFORMED_OR_UNREADABLE_NATIVE_EVIDENCE", "failure": repr(error),
                              "producerExitCode": producer.get("exitCode"), "producerTerminalState": producer.get("terminalState"),
                              "pixelAcceptance": "UNVERIFIED"}
                result.update(engine=engine, attempt=str(attempt.relative_to(run)))
                write(attempt / "adjudication.json", result)
                summary["results"].append(result)
                controls[case["caseId"]] = result["accepted"]
                stopped = not result.get("cleanupEstablished")
                engine_setup_failed = bool(result.get("engineSetupFailed"))
                write(run / "summary.json", summary)
                print(engine, case["caseId"], result["status"], "producer exit", producer.get("exitCode"), flush=True)
        if clean_identity(root) != identity or any(sha(root / p) != h for p, h in packet["sourceFiles"].items()):
            raise ValueError("candidate bytes drifted; collected observations cannot qualify this source")
        accepted = (len(summary["results"]) == len(summary["planned"]) and not summary["unattempted"]
                    and all(r.get("accepted") is True and r.get("cleanupEstablished") is True for r in summary["results"]))
        summary["selectedSourceAssertionsMet"] = accepted
        summary["exitCode"] = 0 if accepted else 1
    except Exception as error:
        summary.update(failure=repr(error), selectedSourceAssertionsMet=False, exitCode=1)
    accounted = {(r["engine"], r["caseId"]) for r in summary["results"] + summary["unattempted"]}
    for cell in summary["planned"]:
        if (cell["engine"], cell["caseId"]) not in accounted:
            summary["unattempted"].append({**cell, "reason": summary.get("failure", "native frontier stopped before launch")})
    summary["finishedUtc"] = utc()
    write(run / "summary.json", summary)
    print("PARTIAL native acquisition; independent actual pixels and final platform acceptance remain required.", flush=True)
    return summary["exitCode"]


if __name__ == "__main__":
    raise SystemExit(main())
