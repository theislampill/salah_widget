#!/usr/bin/env python3
"""Pure instrument controls. No browser, network, workflow, or candidate write.

The browser-shaped doubles below deliberately test verifier control flow only.
They are not native/product qualification or evidence of real rendered pixels.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREP = HERE / "original-scope"
PROBE = PREP / "r0007_public_consumer.py"
spec = importlib.util.spec_from_file_location("reviewed_public_consumer", PROBE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
manifest = json.loads((PREP / "r0007_public_cases.json").read_text())
template = json.loads((PREP / "delivery-request.template.json").read_text())
RUNS = HERE / "pure-control-artifacts"
RUNS.mkdir(exist_ok=True)
RUN = Path(tempfile.mkdtemp(prefix="run-", dir=RUNS))
binary = RUN / "not-a-browser.txt"
binary.write_text("Control fixture only; never executed.\n")
KEYS = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
findings = []

def record(name, evidence, result="REPRODUCED"):
    findings.append({"name": name, "result": result, "evidence": evidence})

def set_path(obj, key, value):
    parts = key.split("/")
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = copy.deepcopy(value)

def snapshot(expected, *, duration=None, fonts="loaded"):
    s = {"render": {}, "dom": {}, "rows": [{"key": k} for k in KEYS],
         "diagnosticSurface": {"before": {}, "after": {}},
         "fonts": {"status": fonts, "faces": []}}
    for key, value in expected["equals"].items():
        set_path(s, key, value)
    target = s["render"].get("nextKey")
    tm = s["render"].get("nextTime")
    s["render"].setdefault("progress", 0.5)
    s["dom"].setdefault(".left", {})
    if target:
        correct = "1h 31m" if target == "Isha" else "6h 0m"
        s["dom"][".left"]["text"] = f"{duration or correct} left until {target}"
        s["dom"][".times"] = {"text": " ".join(KEYS), "html": f'<div class="p on" data-prayer-key="{target}"><b>{target}</b><span class="tm">{tm}</span></div>'}
        s["dom"][".arc"] = {"text": "", "html": f'<g class="dot next" data-prayer-key="{target}"></g>'}
    else:
        s["dom"][".times"] = {"text": " ".join(KEYS), "html": '<div class="p"></div>'}
        s["dom"][".arc"] = {"text": "", "html": '<g class="dot"></g>'}
    s["dom"]["#ce"] = {"text": "7 September 2026", "html": ""}
    return s

def request_for_doubles():
    req = copy.deepcopy(template)
    req["expectedFiles"]["index.html"]["sha256"] = subject.sha(b"synthetic-nav")
    req["expectedFiles"]["config.js"]["sha256"] = subject.sha(b"synthetic-config")
    return req

class Response:
    status = 200
    def __init__(self, url, body): self.url, self._body = url, body
    def body(self): return self._body

class Route:
    def __init__(self, owner, url, method="GET", resource_type="fetch"):
        self.owner = owner
        self.request = SimpleNamespace(url=url, method=method, resource_type=resource_type)
    def fulfill(self, **kwargs):
        self.owner.log.append({"action": "fulfill", "url": self.request.url, "fonts": "loading"})
        if "08-09-2026" in self.request.url: self.owner.released = True
    def abort(self, *args): self.owner.log.append({"action": "abort", "url": self.request.url})
    def continue_(self): self.owner.log.append({"action": "continue", "url": self.request.url})

class Page:
    def __init__(self, owner):
        self.owner, self.handlers = owner, {}
    def set_default_timeout(self, value): pass
    def on(self, event, callback): self.handlers[event] = callback
    def goto(self, url, **kwargs):
        q = "?latitude=40.71&longitude=-74.01&method=2&school=0"
        self.owner.router(Route(self.owner, "https://api.aladhan.com/v1/timings/07-09-2026" + q))
        self.owner.router(Route(self.owner, "https://api.aladhan.com/v1/timings/08-09-2026" + q))
        self.handlers["response"](Response(subject.SITE + "config.js", b"synthetic-config"))
        return Response(url, b"synthetic-nav")
    def wait_for_function(self, expression, **kwargs):
        self.owner.log.append({"action": "wait_for_function", "expression": expression})
    def wait_for_timeout(self, ms): self.owner.log.append({"action": "wait", "ms": ms})
    def evaluate(self, expression, arg=None):
        if "snapshots:p.snapshots" in expression:
            if self.owner.export_failure: raise RuntimeError("controlled-export-failure")
            return {"snapshots": self.owner.snapshots, "events": [], "started": 0}
        if expression.startswith("JSON.stringify"):
            return json.dumps(self.owner.current["render"])
        expected = self.owner.case["expectedUnavailable"] if arg == "unavailable" else self.owner.case["expectedFinal"]
        self.owner.current = snapshot(expected, fonts="loading")
        self.owner.snapshots.append(self.owner.current)
        return self.owner.current
    def screenshot(self, path):
        # Not a PNG; this is intentionally an artifact-integrity negative control.
        Path(path).write_text("Not pixel evidence; pure test double.\n")

class Context:
    def __init__(self, owner): self.owner = owner
    def add_init_script(self, script): self.owner.log.append({"action": "init-script"})
    def route(self, pattern, callback): self.owner.router = callback
    def route_web_socket(self, pattern, callback): pass
    def new_page(self): return Page(self.owner)
    def close(self):
        self.owner.log.append({"action": "context.close"})
        if self.owner.close_failure: raise RuntimeError("controlled-context-close-failure")

class Browser:
    version = "test-double-not-a-browser"
    def __init__(self, owner): self.owner = owner
    def new_context(self, **kwargs): return Context(self.owner)
    def close(self): self.owner.log.append({"action": "browser.close"})

class Family:
    executable_path = str(binary)
    def __init__(self, owner): self.owner = owner
    def launch(self, **kwargs):
        self.owner.log.append({"action": "launch-double"})
        if self.owner.launch_failure: raise RuntimeError("controlled-launch-failure-before-handle")
        return Browser(self.owner)

class Driver:
    def __init__(self, case, *, launch_failure=False, export_failure=False, close_failure=False):
        self.case = case
        self.launch_failure, self.export_failure, self.close_failure = launch_failure, export_failure, close_failure
        self.log, self.snapshots = [], []
        self.released = False
        self.chromium = Family(self)

def acquire(name, **kwargs):
    case_id = kwargs.pop("case", "public-reordered24")
    c = next(x for x in manifest["cases"] if x["caseId"] == case_id)
    d = Driver(c, **kwargs)
    out = RUN / name
    trace = subject.acquire_case(d, "chromium", c, request_for_doubles(), out, False)
    (out / "test-double-events.json").write_text(json.dumps(d.log, indent=2) + "\n")
    return trace, d, out

# Independent civil UTC arithmetic; no product inverse/model is used.
utc = lambda value: int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
literal = {"now": utc("2026-09-07T23:00:00Z"), "isha": utc("2026-09-08T00:31:00Z"), "fajr": utc("2026-09-08T05:00:00Z")}
assert literal == {"now": 1788822000000, "isha": 1788827460000, "fajr": 1788843600000}
assert (literal["isha"] - literal["now"]) / 60000 == 91
assert (literal["fajr"] - literal["now"]) / 60000 == 360
record("independent-literal-oracles", literal, "PASS")

assert subject.validate(template, manifest, template=True)["status"] == "PREPARED_TEMPLATE_NOT_EXECUTABLE"
try:
    subject.validate(template, manifest)
except ValueError as error:
    record("unbound-template-rejected", str(error), "PASS")
else:
    raise AssertionError("Unbound request incorrectly executable")

for c in manifest["cases"]:
    if c["expectedFinal"] is None: continue
    normal = snapshot(c["expectedFinal"])
    subject.assert_expected(normal, c["expectedFinal"])
    wrong = snapshot(c["expectedFinal"], duration="999h 59m")
    subject.assert_expected(wrong, c["expectedFinal"])
    record("wrong-visible-duration-accepted:" + c["caseId"], {"receiptMinutes": wrong["render"]["leftMin"], "visible": wrong["dom"][".left"]["text"]})
    negative = copy.deepcopy(normal)
    negative["render"]["nextEpoch"] += 60000
    try: subject.assert_expected(negative, c["expectedFinal"])
    except AssertionError: pass
    else: raise AssertionError("Wrong epoch positive/negative control failed")
record("expected-epoch-discriminator", "Each applicable expectedFinal rejects an endpoint changed by 60,000 ms.", "PASS")

trace, driver, out = acquire("export-failure", export_failure=True)
assert trace["status"] == "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING"
assert trace["exportFailure"] == "RuntimeError('controlled-export-failure')"
record("export-failure-keeps-assertion-success", {"status": trace["status"], "exportFailure": trace["exportFailure"], "observationsPresent": "observations" in trace})
assert not list(out.rglob("*.webm"))
record("missing-video-not-gated", {"status": trace["status"], "videoFiles": []})

trace, driver, out = acquire("launch-failure", launch_failure=True)
assert trace["ownedCleanupReturned"] is True
assert not any(x["action"].endswith(".close") for x in driver.log)
record("launch-without-handle-claims-cleanup", {"status": trace["status"], "ownedCleanupReturned": trace["ownedCleanupReturned"], "closeCalls": 0})

trace, driver, out = acquire("close-failure", close_failure=True)
assert trace["ownedCleanupReturned"] is False and trace["status"] == "FAILED_OR_UNVERIFIED"
record("returned-owner-close-failure-discriminator", {"status": trace["status"], "cleanupFailures": trace["cleanupFailures"]}, "PASS")

trace, driver, out = acquire("recovery-fonts-loading", case="public-recovery24")
assert trace["status"] == "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING"
assert all(c["snapshot"]["fonts"]["status"] == "loading" for c in trace["checkpoints"])
record("recovery-accepted-before-font-settlement", {"status": trace["status"], "checkpointFontStates": [c["snapshot"]["fonts"]["status"] for c in trace["checkpoints"]], "waitPredicates": [x["expression"] for x in driver.log if x["action"] == "wait_for_function"]})

# Pure subprocess seam: all data are in memory. This does not authenticate an
# actual approval; it tests which declared identities the verifier consults.
req = copy.deepcopy(template)
req["status"] = "READY_AFTER_APPROVAL_MERGE_AND_PAGES_READBACK"
req["ownerApproval"] = {"status": "APPROVED_EXACT_CANDIDATE", "headSha": "a"*40, "baseSha": "b"*40, "treeSha": "d"*40, "receipt": "synthetic-pure-test-receipt"}
req["merge"] = {"status": "MERGED_VERIFIED", "mainSha": "c"*40, "treeSha": "d"*40, "receipt": "synthetic-pure-test-receipt"}
req["pages"] = {"status": "SUCCESS_VERIFIED_EXTERNALLY", "sourceSha": "c"*40, "runId": 1, "receipt": "synthetic-pure-test-receipt"}
content = {p: b"test-object" for p in subject.REQUIRED_FILES}
content[subject.PROBE_PATH] = PROBE.read_bytes()
content[subject.CASES_PATH] = (PREP / "r0007_public_cases.json").read_bytes()
req["expectedFiles"] = {p: {"bytes": len(b), "sha256": subject.sha(b)} for p, b in content.items() if p in subject.REQUIRED_FILES}
calls = []
def git_check_output(argv, **kwargs):
    calls.append(argv)
    if argv[-1] in ("c"*40 + "^{tree}", "a"*40 + "^{tree}"):
        return ("d"*40 if argv[-1].startswith("c") else "e"*40) + "\n"
    if argv[-1] == "FETCH_HEAD": return "c"*40 + "\n"
    if argv[-2] == "blob": return content[argv[-1].split(":", 1)[1]]
    raise AssertionError("Unexpected subprocess request: " + repr(argv))
subject.validate(req, manifest)
with patch.object(subject.subprocess, "check_output", git_check_output):
    subject.verify_git(req, RUN, True)
assert not any(("a"*40) in arg or ("b"*40) in arg for cmd in calls for arg in cmd)
record("approval-head-base-not-consulted", {"approvalHeadActualTreeInDouble": "e"*40, "declaredApprovedAndMergedTree": "d"*40, "verification": "returned normally", "approvalIdentityCommands": []})

(HERE / "pure-review-results.json").write_text(json.dumps({"schema": "independent-review-pure-controls/v1", "scope": "Instrument control flow only; no browser, network, workflow, or product qualification.", "probeSha256": subject.sha(PROBE.read_bytes()), "artifactRoot": str(RUN), "results": findings}, indent=2) + "\n")
print(json.dumps({"controlResults": len(findings), "evidence": str(HERE / "pure-review-results.json"), "scope": "pure controls only"}))
