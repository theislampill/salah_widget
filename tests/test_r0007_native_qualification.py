"""Pure qualification controls: temporary evidence, no native browser or server.

These fixtures are deliberately synthetic. Passing this suite proves collector
and observer decisions, never application behavior, native pixels or cleanup of
an actual browser. The real side-effect boundaries are mocked; evidence parsing,
driver action sequencing and emitted receipts remain the production code.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NATIVE = load_module("r0007_native_test_subject", "tools/qualification/r0007_native.py")
BROWSER = load_module("r0007_browser_test_subject", "tools/cp9/r0007_browser.py")


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r0007-qualification-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "consumer"
        self.case_dir = self.output / "healthy"
        self.case_dir.mkdir(parents=True)
        self.executable = self.root / "synthetic-browser.exe"
        self.executable.write_bytes(b"TEST FIXTURE, NOT A BROWSER")
        self.case = {"caseId": "healthy", "entry": "index.html", "expectedFailure": False,
                     "orderedActions": [{"type": "capture", "name": "first-current", "firstRender": True,
                                         "firstPredicate": "s.stage==='render-completed'", "selector": ".c"}]}
        self.producer = {"terminalState": "exited", "exitCode": 0,
                         "command": ["python", "r0007_browser.py", "--engine", "chromium"]}
        self.files = {"index.html": checksum(b"source"), NATIVE.FIXTURE: checksum(b"fixture")}
        self.row = {"stage": "render-completed", "renderOrdinal": 1, "render": {"acceptedUtcMs": 1}}
        self.trace = {"caseId": "healthy", "status": "PASS_ASSERTIONS_PENDING_PIXEL_REVIEW", "variant": None,
                      "snapshots": [self.row], "checkpointSnapshots": [{**self.row, "checkpoint": "first-current"}],
                      "pageErrors": [], "unexpected": [], "captureMismatches": [], "expectedOracleFailure": False}
        self.summary = {"status": "PARTIAL_NATIVE_REVIEW_REQUIRED", "receipts": [
            {"caseId": "healthy", "status": self.trace["status"], "trace": str(self.case_dir / "trace.json")}],
            "preservation": "NOT_QUALIFIED_BY_DRIVER"}
        self.identity = {"family": "chromium", "engineRequested": "chromium", "version": "TEST.1",
                         "os": platform.system(), "machine": platform.machine(), "headless": False,
                         "executable": str(self.executable.resolve()), "executableSha256": checksum(self.executable.read_bytes()),
                         "executableSelection": "runtime-selected", "chromiumSandboxRequested": True}
        self.presentation = {"beforeOrdinal": 1, "afterOrdinal": 1, "receiptOrdinal": 1,
                             "capture": "native-full-viewport", "firstRenderRequested": True,
                             "selectionKind": "first-matching-render", "firstPredicate": "s.stage==='render-completed'",
                             "requestedSelector": ".c", "requestedBounds": {"x": 0, "y": 0, "width": 325, "height": 530},
                             "viewport": {"width": 370, "height": 570}}
        self.flush()
        write_json(self.case_dir / "document-hashes.json", {"source": self.files["index.html"],
                   "fixture": self.files[NATIVE.FIXTURE], "observed": checksum(b"observed document")})
        write_json(self.case_dir / "first-current-presentation.json", self.presentation)
        (self.case_dir / "first-current.png").write_bytes(b"SYNTHETIC PNG FIXTURE")
        (self.case_dir / "video").mkdir()
        (self.case_dir / "video" / "native.webm").write_bytes(b"SYNTHETIC VIDEO FIXTURE")

    def flush(self):
        write_json(self.case_dir / "trace.json", self.trace)
        write_json(self.output / "summary.json", self.summary)
        write_json(self.case_dir / "browser-identity.json", self.identity)

    def adjudicate(self, controls=None):
        try:
            return NATIVE.adjudicate(self.case, self.output, self.producer, self.files, controls or {})
        except Exception as error:
            self.fail("malformed evidence must be rejected, not escape adjudication: " + repr(error))

    def association(self, result):
        records = result.get("presentationAssociations", [])
        self.assertEqual(len(records), 1, "each declared capture needs its own evidence disposition")
        self.assertEqual(records[0]["capture"], self.case["orderedActions"][0]["name"])
        return records[0]

    def test_q01_valid_terminal_source_assertions_do_not_accept_pixels(self):
        result = self.adjudicate()
        self.assertTrue(result["accepted"])
        self.assertTrue(result["cleanupEstablished"])
        self.assertEqual(result["pixelAcceptance"], "PARTIAL_INDEPENDENT_PIXELS_REQUIRED")

    def test_q02_missing_final_summary_cannot_be_accepted(self):
        (self.output / "summary.json").unlink()
        result = self.adjudicate()
        self.assertFalse(result["accepted"])
        self.assertFalse(result["cleanupEstablished"])

    def test_q03_final_summary_must_match_the_single_terminal_trace(self):
        original = copy.deepcopy(self.summary)
        variants = [[], [dict(original["receipts"][0], caseId="another")], original["receipts"] * 2,
                    [dict(original["receipts"][0], status="FAIL")]]
        for receipts in variants:
            with self.subTest(receipts=receipts):
                write_json(self.output / "summary.json", dict(original, receipts=receipts))
                result = self.adjudicate()
                self.assertFalse(result["accepted"], "terminal receipt mismatch must gate source credit")
                self.assertFalse(result["cleanupEstablished"])

    def test_q03_malformed_summary_or_trace_fails_closed(self):
        for path in [self.output / "summary.json", self.case_dir / "trace.json"]:
            for malformed in ["{", "[]", "null"]:
                with self.subTest(path=path.name, malformed=malformed):
                    self.flush()
                    path.write_text(malformed)
                    self.assertFalse(self.adjudicate()["accepted"])

    def test_q04_sole_final_result_with_unverified_cleanup_fails_aggregate(self):
        source = self.root / "empty-source"
        source.mkdir()
        recipe = {"schema": "remaining-prayer-cases/v1", "issue": 7, "cases": [self.case]}
        write_json(source / NATIVE.DEFAULT_RECIPE, recipe)
        candidate = {"commit": "fixture-commit", "tree": "fixture-tree"}
        packet = dict(recipe, sourceCommit=candidate["commit"], sourceFiles={})
        bad_result = {"caseId": "healthy", "accepted": True, "cleanupEstablished": False,
                      "status": "SOURCE_ASSERTIONS_MET_PIXELS_PENDING"}
        with patch.object(NATIVE, "clean_identity", return_value=candidate), \
             patch.object(NATIVE, "bind_packet", return_value=packet), \
             patch.object(NATIVE, "run_producer", return_value=self.producer), \
             patch.object(NATIVE, "adjudicate", return_value=bad_result), \
             patch.object(NATIVE.subprocess, "check_output", return_value="test-node"), \
             patch.object(NATIVE.importlib.metadata, "version", return_value="test-playwright"), \
             patch.dict(os.environ, {"SALAH_BROWSER_EXECUTABLE": ""}), contextlib.redirect_stdout(io.StringIO()):
            exit_code = NATIVE.main(["--source-root", str(source), "--evidence-root", str(self.root / "runs"), "--engine", "chromium"])
        summary_path = next((self.root / "runs").glob("*/summary.json"))
        result = json.loads(summary_path.read_text())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["selectedSourceAssertionsMet"])

    def make_mutant(self):
        self.case.update(expectedFailure=True, variant="wall-countdown", healthyControlCaseIds=["healthy-control"],
                         expectedFailureContains="render/leftMin: expected 150, observed 210")
        self.producer["exitCode"] = 1
        self.trace.update(status="FAIL", variant="wall-countdown", expectedOracleFailure=True,
                          failure="AssertionError('render/leftMin: expected 150, observed 210')")
        self.summary["receipts"][0]["status"] = "FAIL"
        self.flush()

    def test_q05_intended_mutant_requires_healthy_controls_and_terminal_summary(self):
        self.make_mutant()
        self.assertTrue(self.adjudicate({"healthy-control": True})["accepted"])
        self.assertFalse(self.adjudicate({"healthy-control": False})["accepted"])
        self.summary["receipts"] = []
        self.flush()
        self.assertFalse(self.adjudicate({"healthy-control": True})["accepted"])

    def test_q05_unrelated_mutant_exit_never_discriminates(self):
        self.make_mutant()
        for failure in ["TimeoutError('timeout')", "AssertionError('unrelated assertion')", None]:
            with self.subTest(failure=failure):
                self.trace["failure"] = failure
                self.flush()
                self.assertFalse(self.adjudicate({"healthy-control": True})["accepted"])

    def test_q06_no_browser_empty_mismatches_do_not_record_presentation(self):
        self.producer["exitCode"] = 1
        self.trace = {"caseId": "healthy", "status": "FAIL", "actions": [], "snapshots": [],
                      "captureMismatches": [], "failure": "TargetClosedError('BrowserType.launch')"}
        self.summary["receipts"][0]["status"] = "FAIL"
        self.flush()
        (self.case_dir / "browser-identity.json").unlink()
        result = self.adjudicate()
        self.assertFalse(result["accepted"])
        self.assertFalse(result["nativeSetupEstablished"])
        self.assertEqual(result.get("firstPresentationAssociation"), "UNVERIFIED_NO_NATIVE_SETUP")
        self.assertEqual(self.association(result)["status"], "UNVERIFIED_NO_NATIVE_SETUP")

    def test_q07_missing_capture_is_unverified_even_with_empty_mismatches(self):
        (self.case_dir / "first-current.png").unlink()
        result = self.adjudicate()
        self.assertEqual(self.association(result)["status"], "UNVERIFIED_NO_CAPTURE_ARTIFACT")

    def test_q07_latest_recovery_capture_is_only_eventual_state(self):
        self.case["orderedActions"][0].update(name="after-next-settlement", firstRender=False)
        self.case["orderedActions"][0].pop("firstPredicate")
        self.presentation.update(firstRenderRequested=False, selectionKind="latest-render", firstPredicate=None)
        self.trace["checkpointSnapshots"][0]["checkpoint"] = "after-next-settlement"
        self.flush()
        write_json(self.case_dir / "after-next-settlement-presentation.json", self.presentation)
        (self.case_dir / "after-next-settlement.png").write_bytes(b"SYNTHETIC EVENTUAL CAPTURE")
        result = self.adjudicate()
        self.assertEqual(self.association(result)["status"], "EVENTUAL_STATE_ONLY")
        self.assertEqual(result.get("firstFrameAcceptance"), "UNVERIFIED_PENDING_INDEPENDENT_REVIEW")

    def test_q09_matching_first_receipt_still_requires_independent_pixels(self):
        result = self.adjudicate()
        self.assertEqual(self.association(result)["status"], "RECORDED_PENDING_INDEPENDENT_REVIEW")
        self.assertEqual(result.get("firstFrameAcceptance"), "UNVERIFIED_PENDING_INDEPENDENT_REVIEW")

    def test_q09_mismatch_remains_unverified_despite_source_success(self):
        self.presentation["afterOrdinal"] = 2
        write_json(self.case_dir / "first-current-presentation.json", self.presentation)
        self.trace["captureMismatches"] = [{"capture": "first-current", "beforeOrdinal": 1, "afterOrdinal": 2, "receiptOrdinal": 1}]
        self.trace["status"] = "PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED"
        self.summary["receipts"][0]["status"] = self.trace["status"]
        self.flush()
        result = self.adjudicate()
        self.assertTrue(result["accepted"], "source assertions and presentation association are separate")
        self.assertEqual(self.association(result)["status"], "UNVERIFIED_ORDINAL_MISMATCH")

    def test_q09_capture_receipt_must_bind_its_actual_named_checkpoint(self):
        self.presentation.update(beforeOrdinal=7, afterOrdinal=7, receiptOrdinal=7)
        write_json(self.case_dir / "first-current-presentation.json", self.presentation)
        result = self.adjudicate()
        self.assertFalse(result["accepted"], "an absent ordinal cannot establish the declared capture")
        self.assertEqual(self.association(result)["status"], "UNVERIFIED_MALFORMED_CAPTURE_EVIDENCE")

    def test_q11_identity_requires_real_requested_engine_and_executable_binding(self):
        original = copy.deepcopy(self.identity)
        invalid = [{}, dict(original, family="firefox"), dict(original, engineRequested="firefox"),
                   dict(original, executable="explicit system chromium if available; otherwise Playwright managed engine"),
                   dict(original, executableSha256="0" * 64), dict(original, version=""),
                   dict(original, os="invented-platform"), dict(original, chromiumSandboxRequested=False)]
        for identity in invalid:
            with self.subTest(identity=identity):
                write_json(self.case_dir / "browser-identity.json", identity)
                self.assertFalse(self.adjudicate()["accepted"])

    def test_q11_malformed_identity_fails_closed(self):
        for malformed in ["{", "null", "[]"]:
            with self.subTest(malformed=malformed):
                (self.case_dir / "browser-identity.json").write_text(malformed)
                self.assertFalse(self.adjudicate()["accepted"])

    def test_q12_setup_failure_skips_same_engine_but_cleanup_failure_stops_all(self):
        for cleanup in [True, False]:
            with self.subTest(cleanup=cleanup), tempfile.TemporaryDirectory() as directory:
                task = Path(directory)
                source = task / "source"
                source.mkdir()
                cases = [{"caseId": name, "entry": "index.html"} for name in ["first", "second"]]
                recipe = {"schema": "remaining-prayer-cases/v1", "issue": 7, "cases": cases}
                write_json(source / NATIVE.DEFAULT_RECIPE, recipe)
                candidate = {"commit": "fixture-commit", "tree": "fixture-tree"}
                packet = dict(recipe, sourceCommit=candidate["commit"], sourceFiles={})
                attempted = []
                def producer(command, *args):
                    engine = command[command.index("--engine") + 1]
                    case_id = command[command.index("--case-id") + 1]
                    attempted.append((engine, case_id))
                    return {"command": command, "terminalState": "exited", "exitCode": 1 if engine == "chromium" else 0}
                def adjudicate(case, output, produced, *args, **kwargs):
                    failed = produced["exitCode"] == 1
                    return {"caseId": case["caseId"], "accepted": not failed,
                            "nativeSetupEstablished": not failed, "engineSetupFailed": failed,
                            "cleanupEstablished": cleanup if failed else True,
                            "status": "OBSERVATION_NOT_ACCEPTED" if failed else "SOURCE_ASSERTIONS_MET_PIXELS_PENDING"}
                with patch.object(NATIVE, "clean_identity", return_value=candidate), \
                     patch.object(NATIVE, "bind_packet", return_value=packet), \
                     patch.object(NATIVE, "run_producer", side_effect=producer), \
                     patch.object(NATIVE, "adjudicate", side_effect=adjudicate), \
                     patch.object(NATIVE.subprocess, "check_output", return_value="test-node"), \
                     patch.object(NATIVE.importlib.metadata, "version", return_value="test-playwright"), \
                     patch.dict(os.environ, {"SALAH_BROWSER_EXECUTABLE": ""}), contextlib.redirect_stdout(io.StringIO()):
                    code = NATIVE.main(["--source-root", str(source), "--evidence-root", str(task / "runs")])
                result = json.loads(next((task / "runs").glob("*/summary.json")).read_text())
                expected = [("chromium", "first"), ("firefox", "first"), ("firefox", "second")] if cleanup else [("chromium", "first")]
                self.assertEqual(attempted, expected)
                self.assertEqual(code, 1)
                self.assertFalse(result["selectedSourceAssertionsMet"])
                self.assertEqual(len(result["unattempted"]), 1 if cleanup else 3)


class CommittedBindingTests(unittest.TestCase):
    """Real disposable Git objects; no application/native execution or remote."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r0007-binding-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.recipe = self.root / NATIVE.DEFAULT_RECIPE
        self.case = {"caseId": "bound-control"}
        for relative in ["src/native/index.html", "index.html", "offline.html", "config.js",
                         NATIVE.DRIVER, NATIVE.FIXTURE, NATIVE.RUNTIME, NATIVE.FONT_OBSERVER, "tools/qualification/r0007_native.py"]:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC COMMITTED SOURCE: " + relative)
        write_json(self.recipe, {"schema": "remaining-prayer-cases/v1", "issue": 7, "cases": [self.case]})
        (self.root / ".gitignore").write_text("__pycache__/\n")
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=R0007 synthetic fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "synthetic immutable binding fixture")
        self.identity = NATIVE.clean_identity(self.root)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True)

    def test_q13_tracked_recipe_and_sources_bind_their_actual_commit(self):
        packet = NATIVE.bind_packet(self.root, self.recipe, self.identity, [self.case])
        self.assertEqual(packet["sourceCommit"], self.identity["commit"])
        self.assertEqual(packet["acquisitionBinding"]["recipeSha256"], checksum(self.recipe.read_bytes()))

    def test_q14_ignored_recipe_cannot_claim_committed_provenance_from_clean_status(self):
        ignored = self.root / "__pycache__/uncommitted-recipe.json"
        write_json(ignored, json.loads(self.recipe.read_text()))
        self.assertEqual(NATIVE.clean_identity(self.root), self.identity)
        with self.assertRaisesRegex(ValueError, "not a committed"):
            NATIVE.bind_packet(self.root, ignored, self.identity, [self.case])

    def test_q15_assume_unchanged_cannot_hide_changed_recipe_or_bound_source_bytes(self):
        for relative in [NATIVE.DEFAULT_RECIPE, NATIVE.DRIVER]:
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                self.git("update-index", "--assume-unchanged", relative)
                path.write_bytes(original + b"\n")
                self.assertEqual(NATIVE.clean_identity(self.root), self.identity)
                with self.assertRaisesRegex(ValueError, "committed bytes"):
                    NATIVE.bind_packet(self.root, self.recipe, self.identity, [self.case])
                path.write_bytes(original)
                self.git("update-index", "--no-assume-unchanged", relative)

    def test_q16_ignored_extra_source_cannot_gain_committed_provenance(self):
        ignored = self.root / "__pycache__/extra.txt"
        ignored.parent.mkdir()
        ignored.write_text("uncommitted extra evidence")
        recipe = json.loads(self.recipe.read_text())
        recipe["sourceFiles"] = {"__pycache__/extra.txt": checksum(ignored.read_bytes())}
        write_json(self.recipe, recipe)
        self.git("add", NATIVE.DEFAULT_RECIPE)
        self.git("-c", "user.name=R0007 synthetic fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "declare an ignored source to challenge binding")
        identity = NATIVE.clean_identity(self.root)
        with self.assertRaisesRegex(ValueError, "not a committed"):
            NATIVE.bind_packet(self.root, self.recipe, identity, [self.case])


class FakeFrame:
    """Browser boundary only; the actual driver still selects/records/actions."""
    def __init__(self, first_ordinal):
        self.ordinal = first_ordinal
        self.snapshots = [{"stage": "render-completed", "renderOrdinal": 1, "currentDay": "fixture",
                           "render": {"unavailable": True}, "dom": {}}]

    def evaluate(self, expression, argument=None):
        if expression == "window.__prayerFixture.ordinal":
            return self.ordinal
        if "window.__prayerFixture[type](id,n)" in expression:
            self.ordinal += 1
            self.snapshots.append(dict(self.snapshots[0], renderOrdinal=self.ordinal))
            return None
        if "snapshots.find(" in expression:
            return copy.deepcopy(self.snapshots[0])
        if ".snapshots.filter(" in expression or "readSnapshot()" in expression:
            return copy.deepcopy(self.snapshots[-1])
        if "const f=window.__prayerFixture" in expression:
            return {"startedPerformance": 0, "events": [], "snapshots": copy.deepcopy(self.snapshots),
                    "requests": [], "storageLog": [], "timerLog": [], "activeTimers": [], "storage": [],
                    "pending": [], "unexpected": [], "assetEvents": [], "resourceTiming": [],
                    "fonts": {"status": "loaded", "faces": []}}
        raise AssertionError("unexpected browser-boundary expression: " + expression)

    def locator(self, selector):
        return types.SimpleNamespace(bounding_box=lambda: {"x": 0, "y": 0, "width": 325, "height": 530})


class DriverTests(unittest.TestCase):
    def run_driver(self, parent, first_name="unavailable", first_ordinal=2, engine="chromium", selection="managed", launch_failure=False):
        source, output = parent / "source", parent / "consumer"
        fixture = source / "tests/rlgwo/prayer-browser-fixture.cjs"
        fixture.parent.mkdir(parents=True)
        fixture.write_text("test-only fixture placeholder")
        (source / "index.html").write_text("<html></html>")
        executable = parent / "test-browser.exe"
        executable.write_bytes(b"SYNTHETIC EXECUTABLE, NEVER RUN")
        options = {"headless": True}
        if engine == "chromium":
            options.update(chromium_sandbox=True, args=["--disable-dev-shm-usage"])
        if selection != "managed":
            options["executable_path"] = str(executable)
        runtime_path = source / "tools/cp9/browser_runtime.py"
        runtime_path.parent.mkdir(parents=True)
        (runtime_path.parent / "r0007_font_observer.js").write_text("SYNTHETIC OBSERVER INPUT")
        runtime_path.write_text("import platform\n"
            + "def browser_options(): return " + repr((engine, options)) + "\n"
            + "def browser_identity(browser): return " + repr({"family": engine, "version": "TEST.1",
                "os": platform.system(), "machine": platform.machine(),
                "executable": "explicit system chromium if available; otherwise Playwright managed engine",
                "chromiumSandboxRequested": options.get("chromium_sandbox")}) + "\n")
        case = {"caseId": "fixture", "entry": "index.html", "hash": "#fixture", "clockPolicy": {"mode": "fixed"},
                "cacheSeeds": [], "responseRules": [], "orderedActions": [
                    {"type": "capture", "name": first_name, "firstRender": True, "firstPredicate": "s.stage==='render-completed'"},
                    {"type": "release", "id": "tomorrow"},
                    {"type": "capture", "name": "after-next-settlement", "firstRender": False}],
                "expected": [{"stage": "after-next-settlement", "equals": {"currentDay": "fixture"}}]}
        packet = {"schema": "remaining-prayer-cases/v1", "issue": 7, "sourceCommit": "fixture-commit",
                  "sourceFiles": {"index.html": checksum((source / "index.html").read_bytes()),
                                  NATIVE.FONT_OBSERVER: checksum((source / NATIVE.FONT_OBSERVER).read_bytes())}, "cases": [case]}
        cases, lease = parent / "cases.json", parent / "lease.json"
        write_json(cases, packet)
        write_json(lease, {"resource": "heavy-browser", "status": "GRANTED", "owner": "prayer", "sourceCommit": "fixture-commit"})
        frame = FakeFrame(first_ordinal)
        initialization_order = []
        page = types.SimpleNamespace(main_frame=frame, viewport_size={"width": 370, "height": 570},
                                     on=lambda *args: None, goto=lambda *args, **kwargs: initialization_order.append("navigation"),
                                     screenshot=lambda path: Path(path).write_bytes(b"SYNTHETIC SCREENSHOT"))
        launch_options = {}

        def new_context(**kwargs):
            video = Path(kwargs["record_video_dir"]) / "native.webm"
            def close():
                video.parent.mkdir(parents=True, exist_ok=True)
                video.write_bytes(b"SYNTHETIC VIDEO")
            return types.SimpleNamespace(new_page=lambda: page, close=close,
                                         add_init_script=lambda script: initialization_order.append("observer-installed:" + script))

        browser = types.SimpleNamespace(version="TEST.1", new_context=new_context, close=lambda: None)
        def launch(**kwargs):
            launch_options.update(kwargs)
            if launch_failure:
                raise RuntimeError("synthetic browser launch failure")
            return browser
        browser_type = types.SimpleNamespace(name=engine, executable_path=str(executable), launch=launch)
        playwright = types.SimpleNamespace(**{engine: browser_type}, stop=lambda: None)
        api = types.ModuleType("playwright.sync_api")
        api.sync_playwright = lambda: types.SimpleNamespace(start=lambda: playwright)
        server = types.SimpleNamespace(server_port=12345, serve_forever=lambda: None, shutdown=lambda: None, server_close=lambda: None)
        thread = types.SimpleNamespace(start=lambda: None, join=lambda **kwargs: None)
        environment = {"SALAH_BROWSER_EXECUTABLE": str(executable) if selection == "explicit" else ""}
        with patch.object(BROWSER, "__file__", str(source / "tools/cp9/r0007_browser.py")), \
             patch.object(BROWSER.subprocess, "check_output", return_value=b"<html>instrumented fixture</html>"), \
             patch.object(BROWSER.http.server, "ThreadingHTTPServer", return_value=server), \
             patch.object(BROWSER.threading, "Thread", return_value=thread), \
             patch.dict(sys.modules, {"playwright.sync_api": api}), patch.dict(os.environ, environment), \
             contextlib.redirect_stdout(io.StringIO()):
            exit_code = BROWSER.main(["--issue", "7", "--engine", engine, "--source-root", str(source),
                                     "--cases", str(cases), "--output", str(output), "--capacity-lease", str(lease)])
        launch_options["testInitializationOrder"] = initialization_order
        return exit_code, output / "fixture", executable, launch_options

    def test_q17_font_observer_is_installed_before_actual_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            code, _, _, launch_options = self.run_driver(Path(directory), first_ordinal=1)
            self.assertEqual(code, 0)
            self.assertEqual(launch_options["testInitializationOrder"], ["observer-installed:SYNTHETIC OBSERVER INPUT", "navigation"])

    def test_q08_first_capture_mismatch_retains_evidence_and_continues_for_any_name(self):
        for name in ["unavailable", "first-current"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                code, case_dir, _, _ = self.run_driver(Path(directory), first_name=name)
                trace = json.loads((case_dir / "trace.json").read_text())
                self.assertEqual(code, 0, "ordinal mismatch must not abort later actual acquisition")
                self.assertEqual(trace["status"], "PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED")
                self.assertEqual(trace["captureMismatches"][0]["capture"], name)
                self.assertIn("release", [a["type"] for a in trace["actions"]])
                self.assertTrue((case_dir / "after-next-settlement-presentation.json").is_file())

    def test_q10_actual_selected_executable_and_hash_bind_the_launch_without_sandbox_change(self):
        for engine, selection in [("chromium", "explicit"), ("chromium", "system"),
                                  ("chromium", "managed"), ("firefox", "managed")]:
            with self.subTest(engine=engine, selection=selection), tempfile.TemporaryDirectory() as directory:
                code, case_dir, executable, launch_options = self.run_driver(Path(directory), first_ordinal=1, engine=engine, selection=selection)
                self.assertEqual(code, 0)
                identity = json.loads((case_dir / "browser-identity.json").read_text())
                self.assertEqual(identity.get("executable"), str(executable.resolve()))
                self.assertEqual(identity.get("executableSha256"), checksum(executable.read_bytes()))
                self.assertEqual(identity.get("engineRequested"), engine)
                self.assertEqual(launch_options.get("executable_path"), str(executable.resolve()))
                if engine == "chromium":
                    self.assertIs(launch_options.get("chromium_sandbox"), True)
                    self.assertNotIn("--no-sandbox", launch_options.get("args", []))

    def test_q12_launch_failure_is_classified_without_product_failure_credit(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory)
            code, case_dir, _, _ = self.run_driver(task, launch_failure=True)
            self.assertEqual(code, 1)
            trace = json.loads((case_dir / "trace.json").read_text())
            self.assertEqual(trace.get("failureStage"), "browser-launch")
            packet = json.loads((task / "cases.json").read_text())
            files = dict(packet["sourceFiles"], **{NATIVE.FIXTURE: checksum((task / "source" / NATIVE.FIXTURE).read_bytes())})
            result = NATIVE.adjudicate(packet["cases"][0], case_dir.parent,
                {"terminalState": "exited", "exitCode": 1, "command": ["python", "driver", "--engine", "chromium"]}, files, {})
            self.assertFalse(result["accepted"])
            self.assertTrue(result["cleanupEstablished"])
            self.assertTrue(result.get("engineSetupFailed"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
