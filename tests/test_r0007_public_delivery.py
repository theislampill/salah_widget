#!/usr/bin/env python3
"""Pure authored regression controls; no browser/network/product qualification.

Set R0007_PROBE_UNDER_TEST to an archived probe for the preserved RED run.
All browser-shaped objects are explicit doubles; PNG/WebM fixtures are structural
test bytes and never receive native pixel or motion credit.
"""
from __future__ import annotations
import copy
import importlib.util
import inspect
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zlib

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parent
FONT_PATH = REPOSITORY / "tools/cp9/r0007_font_observer.js"
PROBE = Path(os.environ.get("R0007_PROBE_UNDER_TEST", REPOSITORY / "tools/qualification/r0007_public_consumer.py"))
spec = importlib.util.spec_from_file_location("delivery_instrument_under_test", PROBE)
subject = importlib.util.module_from_spec(spec); spec.loader.exec_module(subject)
CASES = json.loads((PROBE.parent / "r0007_public_cases.json").read_text())
TEMPLATE = json.loads(Path(os.environ.get("R0007_DELIVERY_TEMPLATE", REPOSITORY / "docs/state-contracts/evidence/R0007/delivery/request.template.json")).read_text())
FONT_SOURCE = FONT_PATH.read_bytes().decode("utf-8")
RUN = Path(tempfile.mkdtemp(prefix="r0007-public-pure-", dir=os.environ.get("R0007_TEST_OUTPUT_ROOT")))
BINARY = RUN / "not-a-browser"; BINARY.write_text("Synthetic file; never executed.\n")
KEYS = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]


def set_path(obj, key, value):
    parts = key.split("/")
    for part in parts[:-1]: obj = obj.setdefault(part, {})
    obj[parts[-1]] = copy.deepcopy(value)


def snapshot(expected, wrong_duration=False):
    obj = {"render": {"atMs": 123}, "dom": {}, "rows": [{"key": k} for k in KEYS], "fonts": {"status": "loaded", "settlement": {"settled": True}, "faces": []},
           "diagnosticSurface": {"before": {}, "after": {}}, "stage": "synthetic"}
    for key, value in expected["equals"].items(): set_path(obj, key, value)
    target, clock = obj["render"].get("nextKey"), obj["render"].get("nextTime")
    obj["render"].setdefault("progress", .5)
    if target:
        duration = "999h 59m" if wrong_duration else "1h 31m" if target == "Isha" else "6h 0m"
        obj["dom"][".left"] = {"text": duration + " left until " + target, "html": ""}
        obj["dom"][".times"] = {"text": " ".join(KEYS), "html": f'<div class="p on" data-prayer-key="{target}"><b>{target}</b><span class="tm">{clock}</span></div>'}
        obj["dom"][".arc"] = {"text": "", "html": f'<g class="dot next" data-prayer-key="{target}"></g>'}
    else:
        obj["dom"][".times"] = {"text": " ".join(KEYS), "html": '<div class="p"></div>'}
        obj["dom"][".arc"] = {"text": "", "html": '<g class="dot"></g>'}
    obj["dom"]["#ce"] = {"text": "7 September 2026", "html": ""}
    for item in obj["dom"].values(): item.setdefault("geometry", {"x": 0, "y": 0, "width": 325, "height": 530})
    return obj


def png_bytes():
    def chunk(kind, data): return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack(">IIBBBBB", 370, 570, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + b'\0' * (370 * 3)) * 570)) + chunk(b'IEND', b'')


class Response:
    status = 200
    headers = {}
    def __init__(self, url, content): self.url, self.content = url, content
    def body(self): return self.content


class Route:
    def __init__(self, owner, url): self.owner = owner; self.request = SimpleNamespace(url=url, method="GET", resource_type="fetch", failure=None)
    def fulfill(self, **kwargs):
        self.owner.events.append("fulfill-next" if "08-09" in self.request.url else "fulfill-current")
        if "08-09" in self.request.url: self.owner.released = True
    def abort(self, *args): self.owner.events.append("abort")
    def continue_(self): self.owner.events.append("unbounded-continue")


class Page:
    def __init__(self, owner): self.owner, self.handlers = owner, {}; self.video = SimpleNamespace(path=self.video_path)
    def video_path(self): return str(self.owner.video_dir / "fixture.webm")
    def set_default_timeout(self, value): pass
    def on(self, key, fn): self.handlers[key] = fn
    def goto(self, url, **kwargs):
        query = "?latitude=40.71&longitude=-74.01&method=2&school=0"
        for day in ["07", "08"]: self.owner.router(Route(self.owner, f"https://api.aladhan.com/v1/timings/{day}-09-2026" + query))
        self.handlers["response"](Response(subject.SITE + "config.js", b"fixture-config"))
        return Response(url, b"fixture-navigation")
    def wait_for_function(self, expression, **kwargs):
        self.owner.events.append("wait:" + expression)
        if "fontState" in expression and (not self.owner.css_terminal or not self.owner.fonts_loaded):
            raise TimeoutError("synthetic authored CSS/font state is not settled")
        if "fontObserver" in expression and not self.owner.font_event_settled:
            raise TimeoutError("synthetic fonts.ready resolved but terminal event/deferred receipt remains pending")
    def wait_for_timeout(self, ms): self.owner.events.append("native-wait:" + str(ms))
    def evaluate(self, expression, arg=None):
        if "snapshots:p.snapshots" in expression:
            if self.owner.export_failure: raise RuntimeError("controlled-export-failure")
            return {"snapshots": self.owner.snapshots, "events": [], "started": 0, "fontSettlement": {"settled": self.owner.font_event_settled}, "fontState": {"cssReady": True, "fontStatus": "loaded", "fontObserver": {"settled": self.owner.font_event_settled}}}
        if "awaitTypography" in expression:
            self.owner.events.append("fonts-ready-promise")
            if not self.owner.css_terminal or not self.owner.fonts_loaded: raise TimeoutError("synthetic typography not settled")
            return {"readyPromiseFulfilled": True, "fontStatus": "loaded", "dirtyState": "not-exposed", "binding": "fixture-native-state"}
        if "observeStable" in expression:
            self.owner.events.append("native-stability-observation")
            return {"settled": True, "dirtyState": "not-exposed", "observations": [{"render": {"atMs": 123}, "geometry": {}, "fontState": {"fontObserver": {"settled": self.owner.font_event_settled}}}] * 3}
        if expression.startswith("JSON.stringify"): return json.dumps(self.owner.current["render"])
        if "receipt()" in expression:
            self.owner.receipt_reads += 1
            receipt = copy.deepcopy(self.owner.current["render"])
            if self.owner.receipt_mismatch and self.owner.receipt_reads % 2 == 0: receipt["atMs"] += 1
            return receipt
        if "geometry()" in expression:
            return {selector: self.owner.current["dom"].get(selector, {}).get("geometry") for selector in [".c", ".nt", ".left", ".times", ".arc"]}
        if "fontState()" in expression:
            return {"cssReady": True, "fontStatus": "loaded", "fontObserver": {"settled": self.owner.font_event_settled}}
        expected = self.owner.case["expectedUnavailable"] if arg and str(arg).startswith("unavailable") else self.owner.case["expectedFinal"]
        self.owner.current = snapshot(expected)
        self.owner.current["stage"] = arg or "synthetic"
        self.owner.snapshots.append(copy.deepcopy(self.owner.current))
        return copy.deepcopy(self.owner.current)
    def screenshot(self, path): Path(path).write_bytes(b"not-a-png" if self.owner.bad_png else png_bytes())


class Context:
    def __init__(self, owner): self.owner = owner
    def add_init_script(self, script): pass
    def route(self, pattern, fn): self.owner.router = fn
    def route_web_socket(self, pattern, fn): pass
    def new_page(self): return Page(self.owner)
    def close(self):
        self.owner.events.append("context.close")
        if self.owner.close_failure: raise RuntimeError("controlled-context-close-failure")
        if not self.owner.missing_video:
            self.owner.video_dir.mkdir(parents=True, exist_ok=True)
            # Structural EBML/WebM fixture, explicitly not native video evidence.
            (self.owner.video_dir / "fixture.webm").write_bytes(b'\x1aE\xdf\xa3\x87B\x82\x84webm\x18S\x80g\xff\x16T\xaek\x85\xae\x83\x83\x81\x01\x1fC\xb6u\x8a\xe7\x81\0\xa3\x85\x81\0\0\x80\0')


class Browser:
    version = "synthetic-browser-control"
    def __init__(self, owner): self.owner = owner
    def new_context(self, **kwargs): self.owner.context_options = kwargs; self.owner.video_dir = Path(kwargs["record_video_dir"]); return Context(self.owner)
    def close(self): self.owner.events.append("browser.close")


class Family:
    executable_path = str(BINARY)
    def __init__(self, owner): self.owner = owner
    def launch(self, **kwargs):
        self.owner.events.append("launch")
        if self.owner.launch_failure: raise RuntimeError("controlled-launch-failure-before-handle")
        return Browser(self.owner)


class Driver:
    def __init__(self, case, **flags):
        self.case, self.events, self.snapshots = case, [], []
        defaults = dict(launch_failure=False, export_failure=False, close_failure=False, missing_video=False, bad_png=False,
                        receipt_mismatch=False, css_terminal=True, fonts_loaded=True, font_event_settled=True)
        defaults.update(flags); self.__dict__.update(defaults)
        self.released, self.receipt_reads = False, 0
        self.chromium = Family(self)


def acquire(name, case_id="public-reordered24", **flags):
    case = next(c for c in CASES["cases"] if c["caseId"] == case_id)
    driver = Driver(case, **flags)
    request = copy.deepcopy(TEMPLATE)
    request["fontObserverSha256"] = subject.sha(FONT_SOURCE.encode())
    for path, content in [("index.html", b"fixture-navigation"), ("config.js", b"fixture-config")]: request["expectedFiles"][path]["sha256"] = subject.sha(content)
    output = RUN / name
    kwargs = {"font_observer_source": FONT_SOURCE} if "font_observer_source" in inspect.signature(subject.acquire_case).parameters else {}
    result = subject.acquire_case(driver, "chromium", case, request, output, False, **kwargs)
    (output / "pure-double-events.json").write_text(json.dumps(driver.events, indent=2) + "\n")
    return result, driver, output


class InstrumentControls(unittest.TestCase):
    def test_literal_duration_healthy_and_wrong_visible_controls(self):
        for case in CASES["cases"]:
            if case["expectedFinal"]:
                with self.subTest(case=case["caseId"]):
                    subject.assert_expected(snapshot(case["expectedFinal"]), case["expectedFinal"])
                    with self.assertRaises(AssertionError): subject.assert_expected(snapshot(case["expectedFinal"], True), case["expectedFinal"])

    def test_healthy_structural_acquisition_stays_pixels_pending(self):
        trace, driver, _ = acquire("healthy")
        self.assertEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")
        self.assertEqual(driver.context_options["service_workers"], "block")
        self.assertTrue(trace["artifactInventory"]["video"]["recordedBlockCount"])

    def test_export_failure_cannot_keep_acquisition_credit(self):
        trace, _, _ = acquire("export-failure", export_failure=True)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_missing_video_cannot_keep_acquisition_credit(self):
        trace, _, _ = acquire("missing-video", missing_video=True)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_invalid_png_cannot_keep_acquisition_credit(self):
        trace, _, _ = acquire("invalid-png", bad_png=True)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_mismatched_capture_receipt_cannot_keep_acquisition_credit(self):
        trace, _, _ = acquire("receipt-mismatch", receipt_mismatch=True)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_launch_without_handle_is_unknown_custody(self):
        trace, driver, _ = acquire("launch-failure", launch_failure=True)
        self.assertFalse(trace["ownedCleanupReturned"])
        self.assertFalse(any(x.endswith(".close") for x in driver.events))

    def test_close_failure_stays_unverified(self):
        trace, driver, _ = acquire("close-failure", close_failure=True)
        self.assertFalse(trace["ownedCleanupReturned"])
        self.assertIn("browser.close", driver.events)

    def test_pending_authored_stylesheet_cannot_release_recovery(self):
        trace, driver, _ = acquire("stylesheet-pending", "public-recovery24", css_terminal=False, fonts_loaded=True)
        self.assertFalse(driver.released)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_loading_fonts_cannot_release_recovery(self):
        trace, driver, _ = acquire("fonts-loading", "public-recovery24", fonts_loaded=False)
        self.assertFalse(driver.released)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_ready_without_deferred_font_events_cannot_release_recovery(self):
        trace, driver, _ = acquire("font-event-pending", "public-recovery24", font_event_settled=False)
        self.assertFalse(driver.released)
        self.assertNotEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")

    def test_healthy_recovery_awaits_typography_and_native_stability(self):
        trace, driver, _ = acquire("recovery-healthy", "public-recovery24")
        self.assertEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")
        self.assertLess(driver.events.index("fonts-ready-promise"), driver.events.index("fulfill-next"))
        self.assertLess(driver.events.index("native-stability-observation"), driver.events.index("fulfill-next"))

    def test_retained_artifact_tampering_is_rejected(self):
        trace, _, out = acquire("artifact-tamper")
        case = next(c for c in CASES["cases"] if c["caseId"] == "public-reordered24")
        self.assertEqual(trace["status"], "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING")
        presentation = out / "actual-completed-consumer-presentation.json"
        saved = presentation.read_bytes(); data = json.loads(saved); data["beforeReceipt"]["atMs"] += 1; subject.dump(presentation, data)
        with self.assertRaises(ValueError): subject.verify_acquisition_artifacts(trace, case, out)
        presentation.write_bytes(saved)
        export = out / "observation-export.json"; saved_export = export.read_bytes(); export.write_text('{"snapshots":[]}')
        with self.assertRaises(ValueError): subject.verify_acquisition_artifacts(trace, case, out)
        export.write_bytes(saved_export)
        image = out / "actual-completed-consumer.png"; saved_image = image.read_bytes(); image.unlink()
        with self.assertRaises(ValueError): subject.verify_acquisition_artifacts(trace, case, out)
        image.write_bytes(saved_image)
        video = Path(trace["ownedVideoPath"]); video.write_bytes(video.read_bytes()[:-1])
        with self.assertRaises(ValueError): subject.verify_acquisition_artifacts(trace, case, out)

    def test_launch_unknown_stops_the_real_population_loop(self):
        case = next(c for c in CASES["cases"] if c["caseId"] == "public-reordered24")
        driver = Driver(case, launch_failure=True)
        class Manager:
            def __enter__(self): return driver
            def __exit__(self, *args): return False
        fake_api = SimpleNamespace(sync_playwright=lambda: Manager())
        req = copy.deepcopy(TEMPLATE); req["probeSha256"] = subject.sha(PROBE.read_bytes()); req["casesSha256"] = subject.sha((PROBE.parent / "r0007_public_cases.json").read_bytes())
        request_path = RUN / "frontier-request.json"; request_path.write_text(json.dumps(req))
        output = RUN / "frontier"
        # Only authority/network gates are explicit stubs. The production
        # population loop and failing acquire_case run unchanged, without a browser.
        with mock.patch.object(subject, "validate", return_value={}), mock.patch.object(subject, "verify_git", return_value={}), mock.patch.object(subject, "served_readback", return_value=[]), mock.patch.dict(sys.modules, {"playwright": SimpleNamespace(), "playwright.sync_api": fake_api}):
            arguments = ["--request", str(request_path), "--cases", str(PROBE.parent / "r0007_public_cases.json"), "--repository-root", str(RUN / "unopened-repo"), "--output", str(output)]
            if hasattr(subject, "FONT_OBSERVER_PATH"): arguments.extend(["--font-observer", str(FONT_PATH)])
            code = subject.main(arguments)
        self.assertEqual(code, 1)
        self.assertEqual(driver.events.count("launch"), 1)
        result = json.loads((output / "summary.json").read_text())
        self.assertEqual(len(result["results"]), 8)
        self.assertTrue(all(r["status"] == "UNATTEMPTED_OWNED_CLEANUP_UNVERIFIED" for r in result["results"][1:]))


class TransportControls(unittest.TestCase):
    def test_original_response_uses_zero_redirect_fetch_and_same_response(self):
        for status in [200, 404, 302, 307]:
            with self.subTest(status=status):
                response = SimpleNamespace(status=status, dispose=mock.Mock())
                route = SimpleNamespace(fetch=mock.Mock(return_value=response), fulfill=mock.Mock(), abort=mock.Mock())
                row, trace = {"url": subject.SITE}, {"blocked": []}
                subject.original_response(route, row, trace)
                route.fetch.assert_called_once_with(max_redirects=0, timeout=45000)
                response.dispose.assert_called_once_with()
                if status in [302, 307]:
                    route.abort.assert_called_once_with(); route.fulfill.assert_not_called(); self.assertEqual(trace["blocked"], [row])
                else:
                    route.fulfill.assert_called_once_with(response=response); self.assertFalse(trace["blocked"])

    def test_transport_error_is_retained_and_aborted(self):
        route = SimpleNamespace(fetch=mock.Mock(side_effect=RuntimeError("synthetic-fetch-failure")), fulfill=mock.Mock(), abort=mock.Mock())
        row, trace = {}, {"blocked": []}; subject.original_response(route, row, trace)
        self.assertIn("synthetic-fetch-failure", row["failure"]); self.assertEqual(trace["blocked"], [row]); route.fulfill.assert_not_called()

    def test_routing_has_no_continue_escape(self):
        self.assertNotIn("route.continue_", PROBE.read_text())


class GitIdentityControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = RUN / "git-objects"; cls.root.mkdir()
        def git(*args, input=None): return subprocess.check_output(["git", "-C", str(cls.root), *args], input=input, text=True, stderr=subprocess.STDOUT).strip()
        cls.git = staticmethod(git)
        git("init", "-b", "main"); git("config", "user.name", "Pure fixture"); git("config", "user.email", "fixture@example.invalid")
        for p in subject.REQUIRED_FILES | {subject.PROBE_PATH, subject.CASES_PATH, getattr(subject, "FONT_OBSERVER_PATH", "tools/cp9/r0007_font_observer.js")}:
            file = cls.root / p; file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(PROBE.read_bytes() if p == subject.PROBE_PATH else (PROBE.parent / "r0007_public_cases.json").read_bytes() if p == subject.CASES_PATH else FONT_SOURCE.encode() if p.endswith("r0007_font_observer.js") else b"fixture-base")
        git("add", "."); git("commit", "-m", "base"); cls.base = git("rev-parse", "HEAD"); cls.base_tree = git("rev-parse", "HEAD^{tree}")
        git("checkout", "-b", "feature"); (cls.root / "index.html").write_bytes(b"fixture-candidate"); git("add", "."); git("commit", "-m", "candidate")
        cls.head = git("rev-parse", "HEAD"); cls.tree = git("rev-parse", "HEAD^{tree}")
        git("checkout", "main"); git("merge", "--no-ff", "feature", "-m", "approved merge"); cls.merged = git("rev-parse", "HEAD"); git("fetch", ".", "main")
        cls.request = copy.deepcopy(TEMPLATE)
        cls.request["ownerApproval"] = {"headSha": cls.head, "baseSha": cls.base, "treeSha": cls.tree, "baseTreeSha": cls.base_tree, "status": "APPROVED_EXACT_CANDIDATE", "receipt": "SYNTHETIC_PURE_CONTROL_NOT_AUTHORITY"}
        cls.request["merge"] = {"mainSha": cls.merged, "treeSha": cls.tree, "method": "merge", "status": "MERGED_VERIFIED", "receipt": "SYNTHETIC_PURE_CONTROL_NOT_AUTHORITY"}
        cls.request["expectedFiles"] = {p: {"sha256": subject.sha((cls.root / p).read_bytes()), "bytes": (cls.root / p).stat().st_size} for p in subject.REQUIRED_FILES}
        cls.request["probeSha256"] = subject.sha(PROBE.read_bytes()); cls.request["casesSha256"] = subject.sha((PROBE.parent / "r0007_public_cases.json").read_bytes())
        cls.request["fontObserverSha256"] = subject.sha(FONT_SOURCE.encode())

    def test_actual_approved_merge_control(self): subject.verify_git(copy.deepcopy(self.request), self.root, True)

    def test_mismatched_actual_approved_head_tree_rejected(self):
        bad_head = self.git("commit-tree", self.base_tree, "-p", self.base, input="wrong-actual-head-tree\n")
        req = copy.deepcopy(self.request); req["ownerApproval"]["headSha"] = bad_head
        with self.assertRaises((ValueError, subprocess.CalledProcessError)): subject.verify_git(req, self.root, True)

    def test_mismatched_actual_approved_base_tree_rejected(self):
        req = copy.deepcopy(self.request); req["ownerApproval"]["baseTreeSha"] = self.tree
        with self.assertRaises(ValueError): subject.verify_git(req, self.root, True)

    def test_wrong_merged_font_observer_identity_rejected(self):
        req = copy.deepcopy(self.request); req["fontObserverSha256"] = "0" * 64
        with self.assertRaises(ValueError): subject.verify_git(req, self.root, True)

    def test_wrong_merge_parent_topology_rejected(self):
        # Content tree is unchanged but parent order is deliberately wrong.
        bad = self.git("commit-tree", self.tree, "-p", self.head, "-p", self.base, input="wrong-parent-order\n")
        req = copy.deepcopy(self.request); req["merge"]["mainSha"] = bad
        with self.assertRaises((ValueError, subprocess.CalledProcessError)): subject.verify_git(req, self.root, False)

    def test_unagreed_merge_method_rejected(self):
        req = copy.deepcopy(self.request); req["merge"]["method"] = "rebase"
        with self.assertRaises(ValueError): subject.verify_git(req, self.root, True)


if __name__ == "__main__":
    print(json.dumps({"scope": "pure instrument/Git fixture controls; nativeExecutions0; no network", "subject": str(PROBE), "probeSha256": subject.sha(PROBE.read_bytes()), "artifacts": str(RUN)}), flush=True)
    unittest.main(verbosity=2)
