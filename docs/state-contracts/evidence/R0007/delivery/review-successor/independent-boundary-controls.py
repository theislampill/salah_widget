#!/usr/bin/env python3
"""Focused independent boundary challenges, using only review-owned pure fixtures."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SCOPE = ROOT / "scope"
spec = importlib.util.spec_from_file_location("successor_pure_fixtures", SCOPE / "test_delivery_instrument.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
subject = fixtures.subject
results = []

def result(name, evidence):
    results.append({"name": name, "status": "PASS", "evidence": evidence})

calls = []
with patch.object(fixtures.Context, "add_init_script", lambda self, text: calls.append(text)):
    trace, driver, output = fixtures.acquire("independent-one-init")
assert trace["status"] == "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING"
assert calls == [fixtures.FONT_SOURCE + "\n" + subject.INIT.replace("__EPOCH__", "1788822000000")]
assert driver.context_options["service_workers"] == "block"
result("single-init-exact-order-and-service-worker-boundary", {"initCalls": len(calls), "fontObserverFirst": True, "serviceWorkers": "block"})

case = next(c for c in fixtures.CASES["cases"] if c["caseId"] == "public-reordered24")
driver = fixtures.Driver(case)
request = copy.deepcopy(fixtures.TEMPLATE)
trace = subject.acquire_case(driver, "chromium", case, request, fixtures.RUN / "independent-wrong-local-font", False, fixtures.FONT_SOURCE + "\n// wrong bytes\n")
assert trace["status"] == "FAILED_OR_UNVERIFIED"
assert driver.events.count("launch") == 0
result("acquire-rejects-wrong-local-observer-before-launch", {"launches": 0, "failure": trace.get("failure")})

response = SimpleNamespace(status=200, dispose=Mock(side_effect=RuntimeError("controlled-dispose-failure")))
route = SimpleNamespace(fetch=Mock(return_value=response), fulfill=Mock(), abort=Mock())
row, trace = {}, {"blocked": []}
subject.original_response(route, row, trace)
assert trace["blocked"] == [row]
assert "controlled-dispose-failure" in row["responseDisposeFailure"]
result("response-disposal-failure-remains-nonpassing", {"blockedCount": len(trace["blocked"]), "failure": row["responseDisposeFailure"]})

response = SimpleNamespace(status=200, dispose=Mock())
route = SimpleNamespace(fetch=Mock(return_value=response), fulfill=Mock(side_effect=RuntimeError("controlled-fulfill-failure")), abort=Mock())
row, trace = {}, {"blocked": []}
subject.original_response(route, row, trace)
assert trace["blocked"] == [row]
route.abort.assert_called_once_with()
response.dispose.assert_called_once_with()
result("fulfillment-failure-aborts-and-disposes", {"blockedCount": len(trace["blocked"]), "policy": row["policy"]})

fixtures.GitIdentityControls.setUpClass()
objects = fixtures.GitIdentityControls
orphan_head = objects.git("commit-tree", objects.tree, input="pure orphan candidate with identical tree\n")
orphan_merge = objects.git("commit-tree", objects.tree, "-p", objects.base, "-p", orphan_head, input="pure ordered merge with unrelated candidate\n")
request = copy.deepcopy(objects.request)
request["ownerApproval"]["headSha"] = orphan_head
request["merge"]["mainSha"] = orphan_merge
try:
    subject.verify_git(request, objects.root, False)
except ValueError as error:
    assert "ancestor" in str(error)
    result("identical-tree-ordered-parents-do-not-bypass-base-ancestry", {"rejection": str(error)})
else:
    raise AssertionError("Unrelated approved head was accepted")

objects.git("fetch", ".", "feature")  # Review-owned local fixture, no external transport.
try:
    subject.verify_git(copy.deepcopy(objects.request), objects.root, True)
except ValueError as error:
    assert "freshly fetched main moved" in str(error)
    result("moved-fetch-head-is-rejected", {"rejection": str(error)})
else:
    raise AssertionError("Moved FETCH_HEAD was accepted")

wrong_font = ROOT / "wrong-observer-control.js"
wrong_font.write_text(fixtures.FONT_SOURCE + "\n// independent mismatch\n")
base_command = [sys.executable, str(SCOPE / "r0007_public_consumer.py"), "--request", str(SCOPE / "delivery-request.template.json"), "--cases", str(SCOPE / "r0007_public_cases.json")]
for name, arguments, expected in [
    ("template", ["--font-observer", str(SCOPE / "r0007_font_observer.js"), "--validate-only", "--template"], 0),
    ("unbound", ["--font-observer", str(SCOPE / "r0007_font_observer.js"), "--validate-only"], 1),
    ("observer-required", ["--validate-only", "--template"], 2),
    ("observer-hash-mismatch", ["--font-observer", str(wrong_font), "--validate-only", "--template"], 1),
]:
    command = base_command + arguments
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log = ROOT / ("independent-" + name + ".log")
    log.write_text(completed.stdout + "\n--- STDERR ---\n" + completed.stderr)
    assert completed.returncode == expected, (name, completed.returncode)
    result("cli-" + name, {"command": command, "exitCode": completed.returncode, "log": log.name, "logSha256": hashlib.sha256(log.read_bytes()).hexdigest()})

report = {"scope": "Pure review-owned fixtures only; no browser/HTTP/server/workflow/candidate effect. Local Git objects and local-file fetch are synthetic controls, never approval evidence.", "probeSha256": subject.sha((SCOPE / "r0007_public_consumer.py").read_bytes()), "fixtureArtifacts": str(fixtures.RUN), "results": results}
(ROOT / "independent-boundary-results.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": "PASS_PURE_BOUNDARY_CONTROLS", "count": len(results), "nativeExecutions": 0, "httpRequests": 0}))
