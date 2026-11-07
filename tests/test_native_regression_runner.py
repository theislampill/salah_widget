"""Actual evaluator controls; child execution and elapsed clocks are isolated doubles.

These tests never run the renderer, providers or the whole inherited population.
The CLI controls use temporary Node fixtures to verify the public exit contract.
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


RUNNER_PATH = Path(__file__).resolve().parents[1] / "tools/cp9/run_native_regressions.py"
spec = importlib.util.spec_from_file_location("native_regression_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

JSON_PASS = json.dumps({"results": [{"name": "actual case", "status": "PASS"}]})
TAP_PASS = """TAP version 13
ok 1 - actual case
1..1
# tests 1
# suites 0
# pass 1
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 1
"""


class RunnerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests").mkdir()
        (self.root / "tests/probe.test.cjs").write_text("// controlled child boundary\n")
        (self.root / "index.html").write_text("<!-- isolated fixture -->\n")
        (self.root / "config.js").write_text("// isolated fixture\n")
        self.counter = 0

    def run_fixture(self, output=JSON_PASS, code=0, *, named=(), fault=None,
                    historical=None, history_inputs=None, history_available=False,
                    classification_fault=False, source_changed=False):
        self.counter += 1
        out = self.root / ("run-" + str(self.counter))
        for name in named:
            (self.root / "tests" / name).write_text("// controlled child boundary\n")
        calls = []

        def child(command, **kwargs):
            calls.append(command)
            kwargs["stdout"].write(output)
            kwargs["stdout"].flush()
            if fault == "timeout":
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            if fault == "launch":
                raise FileNotFoundError("controlled missing node")
            if fault == "cancel":
                raise KeyboardInterrupt()
            return subprocess.CompletedProcess(command, code)

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(runner, "NAMED", list(named)))
            stack.enter_context(patch.object(runner, "INSTRUMENT", None, create=True))
            stack.enter_context(patch.object(runner, "HISTORICAL", historical or {}))
            stack.enter_context(patch.object(runner, "HISTORY_INPUTS", history_inputs or {}, create=True))
            stack.enter_context(patch.object(runner, "history_input", create=True,
                side_effect=lambda root, locator: {"locator": locator, "available": history_available,
                                                  "reason": None if history_available else "object unavailable"}))
            initial_source = {"head": "a" * 40, "tree": "b" * 40, "workingChanges": []}
            stack.enter_context(patch.object(runner, "source_identity", create=True,
                side_effect=[initial_source, dict(initial_source, workingChanges=[{"path": "changed"}])
                             if source_changed else initial_source]))
            stack.enter_context(patch.object(runner, "host_identity", create=True,
                return_value={"python": sys.version, "node": "controlled child"}))
            stack.enter_context(patch.object(runner.subprocess, "run", side_effect=child))
            stack.enter_context(patch.object(runner.time, "monotonic", side_effect=range(100, 200)))
            if classification_fault:
                stack.enter_context(patch.object(runner, "classify_output", side_effect=KeyboardInterrupt))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            result = runner.run(self.root, out)
        self.assertEqual(json.loads((out / "results.json").read_text()), result)
        return result, out, calls

    def test_leading_json_one_second(self):
        result, _, _ = self.run_fixture()
        self.assertEqual(result["commands"][0]["seconds"], 1)
        self.assertEqual(result["status"], "PASS")

    def test_prefixed_json_one_second(self):
        result, _, _ = self.run_fixture("before\n" + JSON_PASS)
        self.assertEqual(result["commands"][0]["seconds"], 1)
        self.assertEqual(result["commands"][0]["counts"]["passCases"], 1)

    def test_actual_diagnostic_json_lines_precede_the_complete_count_summary(self):
        diagnostics = [
            {"realElapsedMs": 41.3, "instrument": "Node event-loop/deferred-body; browser stream NOT_RUN"},
            {"consumer": "fd2972ba64225fe9d6848e92497e6d0ed20ea624", "storedSource": "manual",
             "storedOrigin": "browser-geolocation", "title": "Manual location", "bytesUnchanged": True, "native": "NOT_RUN"},
        ]
        for diagnostic in diagnostics:
            with self.subTest(diagnostic=diagnostic):
                result, _, _ = self.run_fixture("PASS actual case\n" + json.dumps(diagnostic) + "\n" + json.dumps({"cases": 1, "passed": 1, "failed": 0}))
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["commands"][0]["seconds"], 1)

    def test_earlier_failed_or_broken_envelope_is_not_diagnostic_prefix(self):
        for earlier in ('{"results":[{"name":"earlier","status":"FAIL"}]}', '{"broken":'):
            result, _, _ = self.run_fixture("before\n" + earlier + "\n" + JSON_PASS)
            self.assertNotEqual(result["status"], "PASS")

    def test_tap_positive_preserves_duration_and_counts(self):
        result, _, _ = self.run_fixture(TAP_PASS)
        row = result["commands"][0]
        self.assertEqual(row["seconds"], 1)
        self.assertEqual(row["counts"], {"tests": 1, "pass": 1, "fail": 0,
                                       "cancelled": 0, "skipped": 0, "todo": 0})
        self.assertEqual(result["status"], "PASS")

    def test_nonzero_exit_cannot_be_overridden_by_success_output(self):
        for output in (JSON_PASS, "PASS actual case\n" + json.dumps({"pass": 1, "fail": 0}), TAP_PASS):
            with self.subTest(output=output):
                result, _, _ = self.run_fixture(output, 7)
                self.assertNotEqual(result["status"], "PASS")
                self.assertEqual(result["commands"][0]["exitCode"], 7)

    def test_zero_exit_does_not_erase_observed_assertion_failure(self):
        result, _, _ = self.run_fixture(json.dumps({"results": [{"name": "case", "status": "FAIL"}]}))
        self.assertEqual(result["status"], "FAIL")

    def test_outer_incomplete_status_cannot_hide_observed_assertion_failure(self):
        result, _, _ = self.run_fixture(json.dumps({"status": "INCOMPLETE", "results": [{"name": "case", "status": "FAIL"}]}))
        self.assertEqual(result["status"], "FAIL")

    def test_truncated_outer_object_cannot_admit_nested_success_object(self):
        result, _, _ = self.run_fixture('{"truncated":\n  ' + JSON_PASS)
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_prefixed_indented_truncated_envelope_cannot_admit_nested_success(self):
        result, _, _ = self.run_fixture('before\n  {"truncated":\n' + JSON_PASS)
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_named_results_and_supplied_counts_must_agree(self):
        for summary in ({"passed": 0, "failed": 1}, {"pass": 0, "fail": 1}, {"cases": 2}, {"passed": True}):
            with self.subTest(summary=summary):
                output = json.dumps(dict(summary, results=[{"name": "actual case", "status": "PASS"}]))
                result, _, _ = self.run_fixture(output)
                self.assertEqual(result["status"], "INCOMPLETE")
        result, _, _ = self.run_fixture(json.dumps({"passed": 1, "failed": 0, "cases": 1, "results": [{"name": "actual case", "status": "PASS"}]}))
        self.assertEqual(result["status"], "PASS")

    def test_conflicting_case_states_are_not_success(self):
        result, _, _ = self.run_fixture(json.dumps({"results": [{"name": "case", "status": "PASS", "result": "FAIL"}]}))
        self.assertNotEqual(result["status"], "PASS")

    def test_tap_failure_cannot_be_erased_by_success_totals(self):
        result, _, _ = self.run_fixture(TAP_PASS.replace("ok 1 - actual case", "not ok 1 - actual case"))
        self.assertNotEqual(result["status"], "PASS")

    def test_duplicate_json_properties_do_not_hide_failed_population(self):
        result, _, _ = self.run_fixture('{"results":[{"name":"case","status":"FAIL"}],"results":[{"name":"case","status":"PASS"}]}')
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_conflicting_summary_aliases_cannot_pass(self):
        result, _, _ = self.run_fixture('PASS actual case\n{"pass":1,"passed":0,"fail":0,"failed":1}')
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_empty_tap_plan_cannot_claim_positive_totals(self):
        result, _, _ = self.run_fixture(TAP_PASS.replace("ok 1 - actual case\n", "").replace("1..1", "1..0"))
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_tap_directives_must_match_excluded_counts(self):
        for directive in ("SKIP", "TODO"):
            with self.subTest(directive=directive):
                result, _, _ = self.run_fixture(TAP_PASS.replace("ok 1 - actual case", "ok 1 - actual case # " + directive))
                self.assertEqual(result["status"], "INCOMPLETE")

    def test_nested_node_tap_keeps_leaf_and_suite_population_distinct(self):
        nested = TAP_PASS.replace("ok 1 - actual case\n", "    ok 1 - actual case\n      ---\n      type: 'test'\n      ...\n    1..1\nok 1 - suite\n  ---\n  type: 'suite'\n  ...\n").replace("# suites 0", "# suites 1")
        result, _, _ = self.run_fixture(nested)
        self.assertEqual(result["status"], "PASS")

    def test_classification_cancellation_terminalizes_observed_exit_and_remainder(self):
        try:
            result, out, calls = self.run_fixture(named=("later.cjs",), classification_fault=True)
        except KeyboardInterrupt:
            self.fail("classification interruption abandoned the selected population")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(len(result["commands"]), 2)
        row = result["commands"][0]
        self.assertEqual(row["execution"], {"state": "exited", "returnCode": 0})
        self.assertEqual(row["seconds"], 1)
        self.assertIn(JSON_PASS, (out / row["log"]).read_text())
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][1]["execution"]["state"], "not-started")
        self.assertEqual(len(calls), 1)

    def test_source_drift_invalidates_evidence_without_erasing_observed_failure(self):
        result, _, _ = self.run_fixture(code=7, source_changed=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["sourceUnchanged"])
        self.assertIn("identityError", result)

    def test_mixed_pass_and_todo_keeps_unexecuted_obligation_incomplete(self):
        output = TAP_PASS.replace("1..1", "ok 2 - uncovered observation # TODO\n1..2").replace("# tests 1", "# tests 2").replace("# todo 0", "# todo 1")
        result, _, _ = self.run_fixture(output)
        row = result["commands"][0]
        self.assertEqual(row["counts"]["pass"], 1)
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertEqual(row["caseExclusions"][0]["name"], "uncovered observation")
        self.assertTrue(row["caseExclusions"][0]["residual"])

    def test_setup_exception_stack_is_incomplete_at_actual_import_boundary(self):
        result, _, _ = self.run_fixture('source excerpt\nSetupError: SETUP_INCOMPLETE: native block absent\n    at extract (fixture.cjs:3:1)\n', code=1)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][0]["setup"]["status"], "INCOMPLETE")

    def test_setup_and_behavior_failure_keep_both_dispositions(self):
        output = json.dumps({"results": [{"name": "setup", "status": "FAIL", "error": "SETUP_INCOMPLETE: missing native owner"},
                                         {"name": "actual assertion", "status": "FAIL", "error": "guard missing"}]})
        result, _, _ = self.run_fixture(output, code=1)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["commands"][0]["setup"]["status"], "INCOMPLETE")

    def test_tap_setup_exception_is_distinct_from_product_assertion_failure(self):
        output = TAP_PASS.replace("ok 1 - actual case", "not ok 1 - actual case\n  ---\n  type: 'test'\n  error: 'SETUP_INCOMPLETE: Unreviewed widget script anchors'\n  code: 'SETUP_INCOMPLETE'\n  name: 'SetupError'\n  ...").replace("# pass 1", "# pass 0").replace("# fail 0", "# fail 1")
        result, _, _ = self.run_fixture(output, code=1)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][0]["setup"]["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][0]["counts"]["fail"], 1, "raw Node accounting retained")
        mixed = output.replace("1..1", "not ok 2 - actual product failure\n1..2").replace("# tests 1", "# tests 2").replace("# fail 1", "# fail 2")
        result, _, _ = self.run_fixture(mixed, code=1)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["commands"][0]["setup"]["status"], "INCOMPLETE")

    def test_empty_unknown_malformed_and_truncated_output_is_incomplete(self):
        for output in ("", "hello\n", "{", '{"results":[', "[]", "null", "{}",
                       '{"status":"PASS"}', '{"results":[]}', '{"results":[4]}',
                       '{"results":[{"name":"case","status":"unexpected"}]}',
                       "PASS actual case\n", "# tests 1\n# pass 1\n", TAP_PASS.replace("# todo 0\n", "")):
            with self.subTest(output=output):
                result, _, _ = self.run_fixture(output)
                row = result["commands"][0]
                self.assertEqual(result["status"], "INCOMPLETE")
                self.assertEqual(row["output"]["status"], "INCOMPLETE")
                self.assertFalse(row["output"]["executionProven"])

    def test_json_rejects_duplicate_cases_and_inconsistent_terminal_denominator(self):
        for report in ({"results": [{"name": "case", "status": "PASS"}] * 2},
                       {"terminal": False, "declared": 2, "executed": 1, "missing": 1, "pass": 1, "fail": 0},
                       {"terminal": True, "declared": 2, "executed": 1, "missing": 0, "pass": 1, "fail": 0}):
            with self.subTest(report=report):
                result, _, _ = self.run_fixture(json.dumps(report))
                self.assertEqual(result["status"], "INCOMPLETE")

    def test_complete_line_summary_is_admitted_but_mismatched_counts_are_not(self):
        result, _, _ = self.run_fixture('PASS actual case\n{"pass":1,"fail":0}')
        self.assertEqual(result["status"], "PASS")
        result, _, _ = self.run_fixture('PASS actual case\n{"pass":2,"fail":0}')
        self.assertEqual(result["status"], "INCOMPLETE")

    def test_timeout_retains_partial_log_elapsed_and_missing_completion(self):
        result, out, calls = self.run_fixture("PASS partial case\n", fault="timeout", named=("later.cjs",))
        row = result["commands"][0]
        self.assertEqual(row["seconds"], 1)
        self.assertEqual(row["exitCode"], 124)
        self.assertEqual(row["execution"]["state"], "timed-out")
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertIsNone(row["execution"]["returnCode"])
        self.assertIn("PASS partial case", (out / row["log"]).read_text())
        self.assertEqual(len(calls), 1, "no later launch after uncertain infrastructure completion")
        self.assertEqual(result["commands"][1]["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][1]["execution"]["state"], "not-started")

    def test_launch_failure_has_one_terminal_record_and_cause(self):
        result, out, calls = self.run_fixture("", fault="launch", named=("later.cjs",))
        row = result["commands"][0]
        self.assertEqual(row["execution"]["state"], "launch-failed")
        self.assertIn("controlled missing node", row["reason"])
        self.assertIn("controlled missing node", (out / row["log"]).read_text())
        self.assertEqual(row["seconds"], 1)
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(result["commands"]), 2)

    def test_cancellation_preserves_denominator(self):
        try:
            result, _, calls = self.run_fixture("", fault="cancel", named=("later.cjs",))
        except KeyboardInterrupt:
            self.fail("runner abandoned its selected population on cancellation")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(len(result["commands"]), 2)
        self.assertEqual(result["commands"][0]["execution"]["state"], "cancelled")
        self.assertEqual(len(calls), 1)

    def test_every_selected_command_has_exactly_one_terminal(self):
        result, _, calls = self.run_fixture(named=("alpha.cjs", "beta.cjs"))
        expected = ["native-test-glob", "alpha", "beta"]
        self.assertEqual([row["name"] for row in result["plannedCommands"]], expected)
        self.assertEqual([row["name"] for row in result["commands"]], expected)
        self.assertEqual(len(calls), len(expected))
        for row in result["commands"]:
            self.assertEqual(row["lifecycle"].count("terminal"), 1)
            self.assertEqual(row["lifecycle"][-1], "terminal")

    def test_missing_required_file_prevents_child_launch(self):
        (self.root / "config.js").unlink()
        result, _, calls = self.run_fixture(named=("alpha.cjs",))
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["commands"][1]["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][1]["execution"]["state"], "not-started")

    def test_empty_glob_never_becomes_implicit_node_discovery(self):
        (self.root / "tests/probe.test.cjs").unlink()
        result, _, calls = self.run_fixture()
        self.assertEqual(calls, [])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(len(result["commands"]), 1)

    def test_terminal_assertion_failure_allows_independent_later_command(self):
        result, _, calls = self.run_fixture(code=7, named=("alpha.cjs",))
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(all(row["execution"]["state"] == "exited" for row in result["commands"]))

    def test_missing_history_is_incomplete_without_current_substitution(self):
        locator = "d" * 40 + ":index.html"
        result, _, calls = self.run_fixture(named=("alpha.cjs",), history_inputs={"alpha": (locator,)})
        row = result["commands"][1]
        self.assertEqual(row["status"], "INCOMPLETE")
        self.assertEqual(row["execution"]["state"], "not-started")
        self.assertEqual(row["setup"]["history"][0]["locator"], locator)
        self.assertFalse(row["setup"]["history"][0]["available"])
        self.assertEqual(len(calls), 1)

    def test_available_exact_history_allows_actual_child(self):
        result, _, calls = self.run_fixture(named=("alpha.cjs",), history_inputs={"alpha": ("d" * 40 + ":index.html",)}, history_available=True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(calls), 2)

    def test_excluded_command_stays_in_disposition_denominator(self):
        result, _, calls = self.run_fixture(named=("alpha.cjs",), historical={"alpha.cjs": {
            "reason": "removed fixture producer", "replacement": "tests/replacement.test.cjs#current consumer"}})
        self.assertEqual(len(result["commands"]), 2)
        row = result["commands"][1]
        self.assertEqual(row["status"], "HISTORICAL_EXCLUDED")
        self.assertEqual(row["counts"], {})
        self.assertIn("removed fixture producer", row["reason"])
        self.assertEqual(len(calls), 1)

    def test_setup_marker_cannot_be_a_product_assertion_pass(self):
        result, _, _ = self.run_fixture('SETUP_INCOMPLETE: missing intended native owner\n', code=2)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["commands"][0]["setup"]["status"], "INCOMPLETE")

    def test_todo_is_visible_and_not_added_to_pass_count(self):
        output = TAP_PASS.replace("ok 1 - actual case", "ok 1 - actual case # TODO retained placeholder").replace("# pass 1", "# pass 0").replace("# todo 0", "# todo 1")
        result, _, _ = self.run_fixture(output)
        row = result["commands"][0]
        self.assertEqual(row["counts"]["todo"], 1)
        self.assertEqual(row["counts"]["pass"], 0)
        self.assertTrue(row["explicitExclusions"])
        self.assertNotEqual(row["status"], "PASS")


class RunnerCliTests(unittest.TestCase):
    def test_actual_qualification_caller_preserves_runner_exit_and_receipt(self):
        cp9 = RUNNER_PATH.parent
        sys.path.insert(0, str(cp9))
        self.addCleanup(sys.path.remove, str(cp9))
        caller_spec = importlib.util.spec_from_file_location("r0017_qualification_consumer", cp9 / "qualify_candidate.py")
        caller = importlib.util.module_from_spec(caller_spec)
        caller_spec.loader.exec_module(caller)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            (root / "tests").mkdir()
            (root / "index.html").write_text("isolated source")
            (root / "config.js").write_text("isolated config")
            child = root / "tests/r0001-date-sinks.cjs"
            command = [sys.executable, str(RUNNER_PATH), "--root", str(root), "--select", "r0001-date-sinks"]
            for label, output, expected in (("healthy", JSON_PASS, 0), ("unproved", "hello", 1)):
                child.write_text("console.log(" + json.dumps(output) + ");\n")
                with patch.object(caller, "COMMANDS", {"native": command}), patch.object(caller, "runtime_identity", return_value={"treeSha256": "controlled-runtime"}), contextlib.redirect_stdout(io.StringIO()):
                    rows = caller.run(root, Path(directory) / label, ["native"])
                self.assertEqual(rows[0]["exitCode"], expected)
                self.assertTrue(rows[0]["runtimeUnchanged"])
                receipt = json.loads((Path(directory) / label / "native/results.json").read_text())
                self.assertEqual(receipt["status"], "PASS" if expected == 0 else "INCOMPLETE")

    def test_public_cli_matches_semantic_result_and_preserves_old_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "index.html").write_text("isolated input")
            (root / "config.js").write_text("isolated input")
            child = root / "tests/r0001-date-sinks.cjs"
            for label, text, status, exit_code in (("healthy", JSON_PASS, "PASS", 0), ("unproved", "hello", "INCOMPLETE", 1)):
                child.write_text("console.log(" + json.dumps(text) + ");\n")
                output = root / label
                cmd = [sys.executable, str(RUNNER_PATH), "--root", str(root), "--output", str(output), "--select", "r0001-date-sinks"]
                run = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                self.assertEqual(run.returncode, exit_code, run.stdout + run.stderr)
                report = json.loads((output / "results.json").read_text())
                self.assertEqual(report["status"], status)
                self.assertEqual(len(report["plannedCommands"]), 1)
                before = (output / "results.json").read_bytes()
                again = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                self.assertNotEqual(again.returncode, 0)
                self.assertEqual((output / "results.json").read_bytes(), before)


class RunnerMutationTests(unittest.TestCase):
    def test_actual_runner_mutants_fail_their_named_discriminators(self):
        source = RUNNER_PATH.read_text()
        tests = Path(__file__).read_text()
        mutations = [
            ("timing-origin-reuse",
             "        row['seconds'] = time.monotonic() - started_elapsed",
             "        started_elapsed = log.read_text(encoding='utf-8').find('\\n{')\n        row['seconds'] = time.monotonic() - started_elapsed",
             ("test_leading_json_one_second", "test_prefixed_json_one_second")),
            ("success-overrides-nonzero",
             "                row['status'] = 'FAIL' if row['exitCode'] != 0 else output['status']",
             "                row['status'] = output['status']",
             ("test_nonzero_exit_cannot_be_overridden_by_success_output",)),
            ("selected-command-dropped", "    for spec in plan:\n", "    for spec in plan[:-1]:\n",
             ("test_every_selected_command_has_exactly_one_terminal",)),
            ("missing-history-passes",
             "    elif stop_reason or row['setup']['status'] != 'READY':\n        row['reason'] = stop_reason or row['setup']['reason']",
             "    elif stop_reason or row['setup']['status'] != 'READY':\n        row['reason'] = stop_reason or row['setup']['reason']\n        row['status'] = 'PASS'",
             ("test_missing_history_is_incomplete_without_current_substitution",)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools/cp9").mkdir(parents=True)
            (root / "tests").mkdir()
            runner_path = root / "tools/cp9/run_native_regressions.py"
            test_path = root / "tests/test_native_regression_runner.py"
            test_path.write_text(tests)
            runner_path.write_text(source)
            names = list(dict.fromkeys(name for _, _, _, names in mutations for name in names))

            def execute(names):
                return subprocess.run([sys.executable, str(test_path), "-v", *["RunnerLifecycleTests." + name for name in names]],
                                      capture_output=True, text=True, timeout=20)

            healthy = execute(names)
            self.assertEqual(healthy.returncode, 0, healthy.stdout + healthy.stderr)
            for label, before, after, names in mutations:
                with self.subTest(mutant=label):
                    self.assertEqual(source.count(before), 1, label + " mutation anchor")
                    runner_path.write_text(source.replace(before, after))
                    mutated = execute(names)
                    output = mutated.stdout + mutated.stderr
                    self.assertNotEqual(mutated.returncode, 0, label + " survived")
                    self.assertIn("Ran ", output, "mutant must reach the named tests")
                    self.assertNotIn("SyntaxError", output)
                    self.assertTrue("FAIL:" in output or "ERROR:" in output)


if __name__ == "__main__":
    unittest.main()
