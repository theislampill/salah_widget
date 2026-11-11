#!/usr/bin/env python3
"""Native normal/NoOpen survival for retained R0016 preview mutants.

This driver validates custody and invokes the maintained entry harness unchanged.
It contains no installer implementation and never executes a native host on Linux.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys
import tempfile
import time


RECIPES = {
    "eager-staging": ("eager", "<entry>", "wrapper", "IO.Directory::CreateDirectory"),
    "cleanup-in-preview": ("cleanup", "Clear-OwnedScratch", "helper", "::Dispose owner=Clear-OwnedScratch"),
    "cached-path-return": ("cached-path", "Download-Asset", "helper", "usable success-stream value"),
    "copy-success-when-suppressed": ("copy-success", "Copy-Text", "helper", "exactly Boolean false"),
    "copy-null-array-truthiness": ("copy-array", "Copy-Text", "helper", "exactly Boolean false"),
    "clipboard-attempt-during-preview": ("copy-effect", "Copy-Text", "helper", "command Set-Clipboard"),
    "native-api-load-before-guard": ("native-load", "Initialize-StagingNative", "helper", "command Add-Type"),
    "swallowed-direct-transport": ("transport", "<entry>", "wrapper", "::Connect owner="),
}
SCENARIOS = ["positive", "no-open"]
JSON_LIMIT = 64 * 1024 * 1024


class Blocked(Exception):
    def __init__(self, classification, message):
        super().__init__(message)
        self.classification = classification


def require(condition, message, classification="PROVENANCE_BLOCKED"):
    if not condition:
        raise Blocked(classification, message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_fact(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file(), "Expected a regular supplied evidence file: " + str(path))
    data = path.read_bytes()
    return {"path": str(path), "sha256": sha(data), "bytes": len(data)}


def load_json(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and path.stat().st_size <= JSON_LIMIT, "JSON evidence missing or exceeds bounded input size")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def within(path, root):
    return path == root or path.is_relative_to(root)


def owned_file(value, root):
    path = Path(value).resolve(strict=True)
    require(within(path, root) and path.is_file(), "Retained evidence file escaped its recorded fixture: " + str(path))
    return path


def mutation_candidates(base, name):
    """Reconstruct only the declared fixture deltas, not any installer behavior."""
    kind, function, _, _ = RECIPES[name]
    if function == "<entry>":
        points = list(re.finditer(r"(?m)^\$ErrorActionPreference\b", base))
        require(len(points) == 1, "Actual entry mutation anchor changed: " + name)
        offset = points[0].start()
        prefix = (
            "if ($DryRun) { [void][IO.Directory]::CreateDirectory((Join-Path $env:TEMP 'r0016-eager-staging')) }"
            if kind == "eager" else
            "if ($DryRun) { $r0016Transport=New-Object Net.Sockets.TcpClient; try { $r0016Transport.Connect('127.0.0.1',9) } catch { } }"
        )
        return [base[:offset] + prefix + newline + base[offset:] for newline in ("\n", "\r\n")]
    expression = (
        r"(?m)^function " + re.escape(function)
        + r"(?:\([^\r\n]*\))?[ \t]*\{[ \t]*\r?\n[ \t]*"
        + r"(if[ \t]*\(\$DryRun\)[ \t]*\{[^\r\n]*\})"
    )
    points = list(re.finditer(expression, base))
    require(len(points) == 1, "Actual first helper guard anchor changed: " + function)
    point = points[0]
    guard = point.group(1)
    if kind == "cleanup":
        replacements = [""]
    elif kind == "cached-path":
        replacements = ["if ($DryRun) { return $CachedPath }"]
    elif kind in ("copy-success", "copy-array"):
        require(guard.count("return $false") == 1, "Actual copy guard changed")
        replacement = "return $true" if kind == "copy-success" else "return @($null,$false)"
        replacements = [guard.replace("return $false", replacement)]
    elif kind == "native-load":
        replacements = ["if ($DryRun) { Add-Type -AssemblyName System.IO.Compression }" + newline + guard for newline in ("\n", "\r\n")]
    elif kind == "copy-effect":
        replacements = ["if ($DryRun) { Set-Clipboard -Value $Text }" + newline + guard for newline in ("\n", "\r\n")]
    else:
        raise Blocked("PROVENANCE_BLOCKED", "Unrecognized retained mutation recipe")
    return [base[:point.start(1)] + replacement + base[point.end(1):] for replacement in replacements]


def verify_case_files(row, core_root, expected_hash, expected_mode):
    fixture = Path(row["fixture"]).resolve(strict=True)
    require(within(fixture, core_root) and fixture.is_dir(), "Prior case fixture is outside its core fixture")
    spec_path = owned_file(fixture / "host-control" / "case.json", fixture)
    spec = load_json(spec_path)
    require(spec.get("mode") == expected_mode and spec.get("sourceSha256") == expected_hash, "Prior case source/scope binding differs")
    ready_path = owned_file(spec["readiness"], fixture)
    nonce = spec.get("nonce")
    require(isinstance(nonce, str) and len(nonce) >= 16 and ready_path.read_text(encoding="utf-8-sig") == nonce, "Prior pre-source readiness is missing or mismatched")
    process = row.get("process", {})
    require(process.get("timedOut") is False and process.get("preparation") == "COMPLETED", "Prior preview was a preparation failure")
    require(process.get("stdoutDrainCompleted", True) is True and process.get("stderrDrainCompleted", True) is True, "Prior output drain was incomplete")
    baseline = row.get("baseline", {})
    require(baseline.get("exit") == 0 and baseline.get("timedOut") is False and baseline.get("preparation") == "COMPLETED", "Prior host baseline did not complete normally")
    require(baseline.get("stdoutDrainCompleted", True) is True and baseline.get("stderrDrainCompleted", True) is True, "Prior baseline output drain was incomplete")
    require(process.get("subjectUnchanged") is True, "Prior preview changed its subject")
    events_path = owned_file(spec["events"], fixture)
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    require(events == row.get("attempts", []), "Prior attempt list differs from its retained raw event file")
    observation = row.get("observation")
    proof_paths = [spec_path, ready_path, events_path]
    if observation is not None:
        require(process.get("exit") == 0, "Completed prior preview child exited abnormally")
        result_path = owned_file(spec["result"], fixture)
        require(load_json(result_path) == observation, "Prior child observation differs from its retained raw result")
        require(observation.get("guardEstablished") is True and not observation.get("preparationError"), "Prior source guard was not established")
        proof_paths.append(result_path)
    return {"spec": spec, "events": events, "files": [file_fact(path) for path in proof_paths]}


def inspect_entry_interface(path):
    text = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    options = set()
    deadline = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            options.update(arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str))
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ENTRY_TIMEOUT_SECONDS" for target in node.targets):
            if isinstance(node.value, ast.Constant):
                deadline = node.value.value
    require({"--host", "--scenario", "--preset"}.issubset(options), "Maintained entry harness lacks the supplied native selection interface", "INTERFACE_BLOCKED")
    require(isinstance(deadline, (int, float)) and deadline >= 60, "Maintained native entry budget is below the acquired 60-second ceiling", "INTERFACE_BLOCKED")
    return {"flags": sorted(options), "entryTimeoutSeconds": deadline, "logicReimplemented": False}


def preflight(args):
    input_path = args.input.resolve(strict=True)
    incoming = load_json(input_path)
    if isinstance(incoming, list):
        core_path = (args.core_receipt or input_path.parent / "results.json").resolve(strict=True)
        core = load_json(core_path)
        variants = incoming
        require(variants == core.get("mutants"), "Manifest differs from the associated core receipt")
    else:
        require(isinstance(incoming, dict), "Input must be a core receipt or retained mutant manifest")
        core_path, core = input_path, incoming
        variants = core.get("mutants")
    require(core.get("schema") == "r0016-preview-powershell-core.v1", "Unrecognized core receipt schema")
    require(core.get("sourceUnchanged") is True and core.get("testUnchanged") is True and core.get("fixtureLibraryUnchanged") is True, "Producer source/test/library custody was not stable")
    require(file_fact(args.preview_harness)["sha256"] == core.get("testSha256"), "Supplied preview fixture differs from the producer test hash")
    base_fact = file_fact(args.source)
    require(base_fact["sha256"] == core.get("sourceSha256"), "Supplied base source differs from the preview receipt")
    base = Path(base_fact["path"]).read_bytes().decode("ascii")
    core_root = Path(core["fixture"]).resolve(strict=True)
    frozen_source = owned_file(core["frozenSource"], core_root)
    require(file_fact(frozen_source)["sha256"] == base_fact["sha256"], "Frozen preview base bytes differ")
    require(isinstance(variants, list) and len(variants) == len(RECIPES), "The complete current retained mutation inventory is required")
    names = [variant.get("name") for variant in variants]
    require(len(set(names)) == len(names) and set(names) == set(RECIPES), "Retained mutation inventory differs")
    rows = core.get("results")
    require(isinstance(rows, list), "Core result rows are missing")
    for kind in ("outside-subject-method-write", "direct-loopback-transport"):
        for denied in (False, True):
            matches = [row for row in rows if row.get("case") == f"control-{kind}-{denied}"]
            require(len(matches) == 1, "Independent producer control is missing")
            control = matches[0]
            require(control.get("pass") is True and control.get("readiness") is True and control.get("denied") is denied and control.get("effectExecuted") is (not denied), "Independent producer control failed")
            control_process = control.get("process", {})
            require(control_process.get("timedOut") is False and control_process.get("preparation") == "COMPLETED", "Independent producer control did not complete")
            require(control_process.get("stdoutDrainCompleted", True) is True and control_process.get("stderrDrainCompleted", True) is True, "Independent producer control output drain was incomplete")
            if not denied:
                require(control_process.get("exit") == 0, "Allowed producer control exited abnormally")
    accepted = []
    producer_executables = set()
    for variant in variants:
        name = variant["name"]
        kind, function, mode, discriminator = RECIPES[name]
        require(variant.get("kind") == kind and variant.get("function") == function and variant.get("baseSourceSha256") == base_fact["sha256"], "Retained mutation metadata differs: " + name)
        source = owned_file(variant["source"], core_root)
        fact = file_fact(source)
        require(fact["sha256"] == variant.get("sha256"), "Retained mutation bytes changed: " + name)
        text = source.read_bytes().decode("ascii")
        require(text in mutation_candidates(base, name), "Retained source is not the intended bounded mutation: " + name)
        matches = [row for row in rows if row.get("case") == "mutant-discriminator-" + name]
        require(len(matches) == 1, "Prior preview discriminator is missing or ambiguous: " + name)
        prior = matches[0]
        require(prior.get("variant") == variant and prior.get("pass") is True and prior.get("classification") == "PASS", "Prior discriminator did not pass: " + name)
        healthy, mutant = prior.get("healthy", {}), prior.get("mutant", {})
        require(healthy.get("pass") is True and healthy.get("classification") == "PASS" and healthy.get("sourceSha256") == base_fact["sha256"], "Matched healthy preview failed: " + name)
        require(mutant.get("pass") is False and mutant.get("classification") == "PRODUCT_ASSERTION_FAILED" and mutant.get("sourceSha256") == fact["sha256"], "Mutation was not rejected by a real source assertion: " + name)
        require(discriminator in str(mutant.get("error", "")), "Wrong prior assertion discriminator: " + name)
        healthy_proof = verify_case_files(healthy, core_root, base_fact["sha256"], mode)
        mutant_proof = verify_case_files(mutant, core_root, fact["sha256"], mode)
        require(healthy.get("process", {}).get("exit") == 0 and healthy.get("observation") is not None,
                "Matched healthy preview did not complete with a normal child result: " + name)
        require(Path(mutant_proof["spec"]["source"]).resolve(strict=True) == source, "Prior caller used different mutant source")
        require(not healthy_proof["events"], "Healthy matched preview reached an effect")
        if kind in ("eager", "cleanup", "native-load", "transport", "copy-effect"):
            require(any(event.get("kind") == "source-call" and discriminator in event.get("detail", "") for event in mutant_proof["events"]), "Required raw source-call discriminator is absent: " + name)
        else:
            require(not mutant_proof["events"] and mutant.get("observation") is not None, "Return-value mutation lacks a completed child observation")
            value = mutant["observation"]
            if kind == "cached-path":
                require(value.get("returnCount", 0) > 0 and any(isinstance(item, str) and item for item in value.get("returned", [])), "No usable cached path was observed")
            elif kind == "copy-success":
                require(value.get("returned") == [True], "Copy-success mutation did not produce true")
            else:
                require(value.get("returned") == [False] and value.get("nullReturnCount", 0) > 0, "Null-plus-false copy discriminator is absent")
        for row in (healthy, mutant):
            require(isinstance(row.get("commandHost"), str) and row["commandHost"], "Producer executable is missing")
            producer_executables.add(row["commandHost"])
        accepted.append({"name": name, "source": str(source), "sha256": fact["sha256"], "kind": kind, "priorAssertion": mutant["error"], "priorEvidence": healthy_proof["files"] + mutant_proof["files"]})
    require(len(producer_executables) == 1, "Producer preview mixed native executables")
    host_version = core.get("host", "")
    host_matches = (args.host == "ps51" and host_version.startswith("5.1.")) or (args.host == "ps7" and host_version == "7.6.6")
    plan = {
        "input": file_fact(input_path), "coreReceipt": file_fact(core_path), "coreRoot": str(core_root),
        "coreAggregatePass": core.get("pass"), "source": base_fact, "preset": file_fact(args.preset),
        "previewHarness": file_fact(args.preview_harness), "producerLibrarySha256": core.get("fixtureLibrarySha256"),
        "entryHarness": file_fact(args.entry_harness), "entryInterface": inspect_entry_interface(args.entry_harness),
        "producerHost": host_version, "producerNativeWindows": core.get("nativeWindows") is True,
        "producerExecutable": next(iter(producer_executables)), "requestedHostMatchesProducer": host_matches,
        "variants": accepted,
    }
    custody = [plan[key] for key in ("input", "coreReceipt", "source", "preset", "previewHarness", "entryHarness")]
    custody.append(file_fact(frozen_source))
    for variant in accepted:
        custody.append(file_fact(variant["source"]))
        custody.extend(variant["priorEvidence"])
    plan["custodyFiles"] = list({fact["path"]: fact for fact in custody}.values())
    return plan


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def verify_custody(facts):
    for fact in facts:
        current = file_fact(fact["path"])
        require(current == fact, "Custody file changed during companion execution: " + fact["path"])


def bound_copy(fact, destination):
    data = Path(fact["path"]).read_bytes()
    require(sha(data) == fact["sha256"] and len(data) == fact["bytes"], "Evidence changed before retained copy: " + fact["path"])
    Path(destination).write_bytes(data)


def allocate_root(parent):
    """Use the parent's default native ACL; never introduce tempfile's 0700 ACE."""
    parent = Path(parent).resolve(strict=True)
    while True:
        root = parent / ("p-" + secrets.token_hex(8))
        try:
            root.mkdir(mode=0o777)
            return root.resolve(strict=True)
        except FileExistsError:
            continue


def native_host_identity(plan, root):
    require(os.name == "nt" and platform.system() == "Windows", "Native Windows is required; no host process was started", "NATIVE_HOST_REQUIRED")
    require(plan["producerNativeWindows"] and plan["requestedHostMatchesProducer"], "Prior preview is not from the requested native Windows version", "NATIVE_HOST_REQUIRED")
    executable = Path(plan["producerExecutable"]).resolve(strict=True)
    host_root = root / "host-version"
    host_root.mkdir()
    env = dict(os.environ)
    replacements = {"HOME", "USERPROFILE", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA", "PSMODULEANALYSISCACHEPATH"}
    for key in list(env):
        if key.upper() in replacements:
            del env[key]
    for key, part in [("HOME", "user-profile"), ("USERPROFILE", "user-profile"), ("TEMP", "temp"), ("TMP", "temp"), ("LOCALAPPDATA", "local"), ("APPDATA", "roam")]:
        path = host_root / part
        path.mkdir(exist_ok=True)
        env[key] = str(path)
    env["PSModuleAnalysisCachePath"] = str(host_root / "analysis-cache")
    env["POWERSHELL_TELEMETRY_OPTOUT"] = "1"
    command = [str(executable), "-NoProfile", "-NonInteractive", "-Command", "[Console]::Write($PSVersionTable.PSVersion.ToString())"]
    try:
        result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        (host_root / "stdout.txt").write_bytes(error.stdout or b"")
        (host_root / "stderr.txt").write_bytes(error.stderr or b"")
        raise Blocked("BOOTSTRAP_BLOCKED", "Native version acquisition timed out") from error
    (host_root / "stdout.txt").write_bytes(result.stdout)
    (host_root / "stderr.txt").write_bytes(result.stderr)
    version = result.stdout.decode("utf-8-sig", errors="replace").strip()
    require(result.returncode == 0 and version == plan["producerHost"], "Current native executable differs from the preview producer", "NATIVE_HOST_REQUIRED")
    return {"executable": file_fact(executable), "version": version, "command": command, "installerExecuted": False}


def run_entry(args, plan, root, label, source, expected_hash, native_identity, carrier_index=0):
    require(os.name == "nt" and platform.system() == "Windows", "Native Windows is required before entry execution", "NATIVE_HOST_REQUIRED")
    require(file_fact(source)["sha256"] == expected_hash, "Source changed immediately before native execution")
    require(file_fact(args.entry_harness)["sha256"] == plan["entryHarness"]["sha256"], "Entry harness changed before execution")
    carrier_root = root / "c" / str(carrier_index)
    carrier_root.mkdir(parents=True)
    child_temp = carrier_root / "t"
    child_temp.mkdir()
    env = dict(os.environ)
    replaced = {"TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PSMODULEANALYSISCACHEPATH"}
    for key in list(env):
        if key.upper() in replaced:
            del env[key]
    for key in ("TEMP", "TMP", "TMPDIR"):
        env[key] = str(child_temp)
    for key, part in (("HOME", "host-profile"), ("USERPROFILE", "host-profile"), ("LOCALAPPDATA", "host-local"), ("APPDATA", "host-roam")):
        path = carrier_root / part
        path.mkdir(exist_ok=True)
        env[key] = str(path)
    env["PSModuleAnalysisCachePath"] = str(carrier_root / "host-analysis-cache")
    env["POWERSHELL_TELEMETRY_OPTOUT"] = "1"
    if args.host == "ps7":
        env["INSTALL_TEST_PS7"] = native_identity["executable"]["path"]
    command = [sys.executable, str(args.entry_harness.resolve()), str(Path(source).resolve()), "--host", args.host,
               "--scenario", "positive", "--scenario", "no-open", "--preset", str(args.preset.resolve())]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    clock = time.monotonic()
    code, terminal_error = None, None
    out_path, err_path = carrier_root / "stdout.json", carrier_root / "stderr.txt"
    observed = {"command": command, "startedUtc": started, "timeoutSeconds": args.entry_budget,
                "stdout": str(out_path), "stderr": str(err_path), "ownedCarrierRoot": str(carrier_root),
                "caseLabel": label, "carrierIndex": carrier_index,
                "ownedTempParent": str(child_temp), "outputCapture": "owned regular files; no companion output pipes"}
    write_json(carrier_root / "launch.json", observed)
    try:
        with out_path.open("wb") as out_stream, err_path.open("wb") as err_stream:
            child = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=out_stream, stderr=err_stream)
            observed["carrierPid"] = child.pid
            try:
                code = child.wait(timeout=args.entry_budget)
            except subprocess.TimeoutExpired as error:
                terminal_error = str(error)
                observed["timedOut"] = True
                # This targets only the still-running carrier spawned immediately above.
                # A failure is retained as acquisition failure, never product evidence.
                taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
                try:
                    stopped = subprocess.run([str(taskkill), "/PID", str(child.pid), "/T", "/F"],
                                             stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
                    observed["ownedTreeTermination"] = {"command": stopped.args, "exit": stopped.returncode,
                                                        "stdout": stopped.stdout.decode("utf-8", errors="replace"),
                                                        "stderr": stopped.stderr.decode("utf-8", errors="replace")}
                except (OSError, subprocess.TimeoutExpired) as stop_error:
                    observed["ownedTreeTermination"] = {"error": str(stop_error), "verified": False}
                if child.poll() is None:
                    child.kill()
                try:
                    code = child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    observed["carrierTerminationUnverified"] = True
    except OSError as error:
        terminal_error = str(error)
    observed.update(exit=code, elapsedSeconds=time.monotonic() - clock)
    write_json(carrier_root / "terminal.json", observed)
    raw_out = out_path.read_bytes() if out_path.is_file() else b""
    classification, failure, receipt, fixture = "PASS", None, None, None
    try:
        require(terminal_error is None, "Native entry carrier did not complete: " + str(terminal_error), "BOOTSTRAP_BLOCKED")
        receipt = json.loads(raw_out.decode("utf-8-sig"))
        require(receipt.get("source") == expected_hash and receipt.get("preset") == plan["preset"]["sha256"], "Native receipt source/preset binding differs")
        fixture = Path(receipt["fixture"]).resolve(strict=True)
        require(fixture.is_dir() and within(fixture, child_temp), "Native fixture escaped its owned disposable parent")
        require(receipt.get("selectedHosts") == [args.host] and receipt.get("selectedScenarios") == SCENARIOS, "Native harness ran a different host/scenario selection")
        rows = receipt.get("results", [])
        if any(row.get("classification") == "BOOTSTRAP_BLOCKED" for row in rows):
            raise Blocked("BOOTSTRAP_BLOCKED", "Native entry preparation failed")
        if any(row.get("classification") == "ENTRY_TIMEOUT" for row in rows):
            raise Blocked("ENTRY_TIMEOUT", "Native entry exceeded its deadline after readiness")
        require(len(rows) == 2 and {row.get("case") for row in rows} == set(SCENARIOS), "Native carrier did not complete both required scenarios", "BOOTSTRAP_BLOCKED")
        for row in rows:
            observation = row.get("observation", {})
            require(row.get("host") == args.host, "Native row host differs")
            require(observation.get("interceptionLoaded") is True, "Native final readiness is missing", "BOOTSTRAP_BLOCKED")
            actual_command = observation.get("command", [])
            lower = [str(value).lower() for value in actual_command]
            require("-file" in lower, "Native entry is not an actual -File invocation")
            index = lower.index("-file")
            require(index + 1 < len(actual_command) and Path(actual_command[index + 1]).resolve() == Path(source).resolve(), "Native -File target differs from the retained source")
            require(not any(value.startswith("-dryrun") for value in lower), "Normal companion invoked preview")
            require(("-noopen" in lower) == (row["case"] == "no-open"), "NoOpen selection differs")
            require(Path(actual_command[0]).resolve() == Path(native_identity["executable"]["path"]).resolve(), "Native invocation used a different executable")
            require(row.get("pass_") is True and observation.get("entryExit") == 0, "Actual normal assertion failed: " + str(row.get("error", row["case"])), "NORMAL_ASSERTION_FAILED")
        require(code == 0, "Native carrier returned failure despite passing rows", "NORMAL_ASSERTION_FAILED")
    except Blocked as error:
        classification, failure = error.classification, str(error)
    except (OSError, ValueError, KeyError, TypeError) as error:
        classification, failure = "BOOTSTRAP_BLOCKED", "Native receipt could not be validated: " + str(error)
    try:
        stable = file_fact(source)["sha256"] == expected_hash and file_fact(args.entry_harness)["sha256"] == plan["entryHarness"]["sha256"]
        require(stable, "Source or maintained harness changed during native execution")
    except (Blocked, OSError) as error:
        stable = False
        classification, failure = "PROVENANCE_BLOCKED", str(error)
    return {"case": label, "pass_": classification == "PASS", "classification": classification, "error": failure,
            "scope": "actual complete-file native normal and NoOpen through the maintained entry harness",
            "source": str(source), "sourceSha256": expected_hash, "sourceAndHarnessUnchanged": stable,
            "observation": observed, "nativeReceipt": receipt, "fixture": str(fixture) if fixture else None,
            "retainedCarrierRoot": str(carrier_root)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Actual core results JSON or its mutants.json")
    parser.add_argument("--core-receipt", type=Path, help="Associated core JSON when the input is a manifest")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--preview-harness", required=True, type=Path)
    parser.add_argument("--entry-harness", required=True, type=Path)
    parser.add_argument("--preset", required=True, type=Path)
    parser.add_argument("--host", required=True, choices=("ps51", "ps7"))
    parser.add_argument("--output-root", type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument("--entry-budget", type=int, default=300, help="Per two-scenario carrier, including native ACL setup")
    parser.add_argument("--variant", action="append", choices=tuple(RECIPES))
    parser.add_argument("--validate-only", action="store_true", help="Validate custody only; never launch PowerShell or the native entry harness")
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)
    # Windows Python 3.12.4+ treats 0700 specially, including mkdtemp's implicit
    # 0700 allocation. Default-mode exclusive mkdir avoids introducing that
    # fixture-only OWNER RIGHTS ancestor. The maintained carrier reads every
    # ancestor ACL and the actual installer still decides whether it is trusted.
    root = allocate_root(args.output_root)
    test_fact = file_fact(Path(__file__))
    report = {"schema": "r0016-native-positive-companion.v1", "fixture": str(root), "auxiliaryFixtures": [],
              "pass_": False, "nativeExecution": False, "mode": "validate-only" if args.validate_only else "native",
              "host": args.host, "test": test_fact, "results": [], "status": "PREPARING"}
    report["fixtureAllocation"] = {"method": "exclusive random Path.mkdir(mode=0o777)",
                                   "nativeAclPremise": "default inherited ACL; actual carrier records ancestor ACLs",
                                   "ancestorAclMutationByCompanion": False, "nativeTrustEstablishedLocally": False}
    status, plan = 2, None
    try:
        require(270 <= args.entry_budget <= 900, "Carrier budget must be 270 through 900 seconds", "INTERFACE_BLOCKED")
        plan = preflight(args)
        report["preflight"] = plan
        selected = args.variant or list(RECIPES)
        require(len(set(selected)) == len(selected), "Selected mutation list contains duplicates")
        report["selectedVariants"] = selected
        report["coverage"] = {"requiredVariants": list(RECIPES), "completeDenominatorSelected": set(selected) == set(RECIPES),
                              "nativeCasesPlanned": 2 * (1 + len(selected)), "harnessInvocationsPlanned": 1 + len(selected)}
        report["recommendedCollectorMinimumSeconds"] = 60 + (1 + len(selected)) * (args.entry_budget + 15) + 60
        inputs = root / "inputs"
        inputs.mkdir()
        for key, name in (("coreReceipt", "core-receipt.json"), ("input", "supplied-input.json"),
                          ("source", "base-install.ps1"), ("preset", "canonical-preset.json")):
            bound_copy(plan[key], inputs / name)
        for variant in plan["variants"]:
            bound_copy(file_fact(variant["source"]), inputs / (variant["name"] + ".ps1"))
        evidence = inputs / "prior-evidence"
        evidence.mkdir()
        report["retainedCustodyFiles"] = []
        for index, fact in enumerate(plan["custodyFiles"]):
            destination = evidence / (str(index).zfill(3) + ".bin")
            bound_copy(fact, destination)
            report["retainedCustodyFiles"].append(dict(fact, retainedCopy=str(destination)))
        if args.validate_only:
            report["status"] = "STRUCTURAL_VALIDATION_ONLY"
            report["validated"] = True
            status = 0
        else:
            require(within(root, Path(tempfile.gettempdir()).resolve()), "Native companion root must be under the collector's disposable temporary parent")
            identity = native_host_identity(plan, root)
            report["nativeHost"] = identity
            report["nativeExecution"] = True
            baseline = run_entry(args, plan, root, "base-normal-and-no-open", args.source, plan["source"]["sha256"], identity)
            report["results"].append(baseline)
            write_json(root / "partial-results.json", report)
            if not baseline["pass_"]:
                report["status"] = "BASELINE_NORMAL_FAILED"
                status = 2 if baseline["classification"] in ("BOOTSTRAP_BLOCKED", "PROVENANCE_BLOCKED") else 1
            else:
                by_name = {variant["name"]: variant for variant in plan["variants"]}
                for carrier_index, name in enumerate(selected, start=1):
                    variant = by_name[name]
                    row = run_entry(args, plan, root, name, Path(variant["source"]), variant["sha256"], identity, carrier_index)
                    row["priorPreviewAssertion"] = variant["priorAssertion"]
                    row["normalSurvival"] = "PASS" if row["pass_"] else "NOT_ESTABLISHED"
                    report["results"].append(row)
                    write_json(root / "partial-results.json", report)
                    if row["classification"] in ("BOOTSTRAP_BLOCKED", "PROVENANCE_BLOCKED"):
                        break
                completed = len(report["results"]) == len(selected) + 1
                report["pass_"] = completed and all(row["pass_"] for row in report["results"])
                report["status"] = "PASS" if report["pass_"] else "NATIVE_NORMAL_INCOMPLETE_OR_FAILED"
                status = 0 if report["pass_"] else 2 if any(row["classification"] in ("BOOTSTRAP_BLOCKED", "PROVENANCE_BLOCKED") for row in report["results"]) else 1
            require(1 + len(report["auxiliaryFixtures"]) <= 16, "Native receipt exceeds collector root limit")
    except (Blocked, OSError, ValueError, KeyError, TypeError) as error:
        report["status"] = getattr(error, "classification", "PROVENANCE_BLOCKED")
        report["error"] = str(error)
        report["pass_"] = False
        status = 2
    try:
        verify_custody((plan["custodyFiles"] if plan else []) + [test_fact])
        report["custodyUnchanged"] = plan is not None
    except (Blocked, OSError) as error:
        report["custodyUnchanged"] = False
        report["statusBeforeCustodyFailure"] = report["status"]
        report["status"], report["error"], report["pass_"], status = "PROVENANCE_BLOCKED", str(error), False, 2
        report["validated"] = False
    report["allRequiredNativeSurvivalEstablished"] = report["pass_"] and set(report.get("selectedVariants", [])) == set(RECIPES)
    report["scopeLimits"] = [
        "The maintained entry harness owns actual normal behavior assertions; this driver does not replace them.",
        "A prior preview rejection plus syntax alone does not establish normal survival.",
        "Preparation failure, missing readiness, timeout and normal assertion failure retain different classifications.",
        "Native normal execution is blocked outside Windows and for a different preview producer host/version.",
        "Structural validation never claims native execution or normal survival.",
        "All carrier temp/profile paths and raw output remain nested in the primary fixture, including acquisition failures.",
        "The companion adds no operating-system effect sandbox; the maintained native fixture owns effect interception.",
        "No installer, maintained test, branch or remote is modified by this driver.",
    ]
    write_json(root / "results.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
