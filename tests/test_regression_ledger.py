"""R0028 controls for the expected-failure ledger and registered population (G-05..G-10).

Child execution is a controlled double; no renderer, provider or real instrument runs.
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
spec = importlib.util.spec_from_file_location("native_regression_runner_ledger", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

TAP_PASS = """TAP version 13
ok 1 - glob case
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


def lines(*cases):
    """json-summary instrument output: PASS/FAIL lines plus the matching terminal."""
    body = "".join(("PASS " + name if message is None else "FAIL " + name + " :: " + message) + "\n"
                   for name, message in cases)
    passed = sum(message is None for _, message in cases)
    return body + json.dumps({"pass": passed, "fail": len(cases) - passed}) + "\n"


def entry(case="beta", message="Expected values", **overrides):
    value = {"id": "L-" + str(case), "status": "active", "kind": "case-fail", "command": "alpha", "case": case,
             "messagePrefix": message, "firstRed": "red at every tested commit (controlled)",
             "causeClass": "stale-pin", "evidence": "tests/test_regression_ledger.py", "owner": "R0028",
             "disposition": "controlled fixture", "trigger": "controlled fixture"}
    value.update(overrides)
    return value


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests").mkdir()
        (self.root / "tests/probe.test.cjs").write_text("// controlled child boundary\n")
        (self.root / "tests/alpha.cjs").write_text("// controlled child boundary\n")
        (self.root / "index.html").write_text("<!-- isolated fixture -->\n")
        (self.root / "config.js").write_text("// isolated fixture\n")
        self.counter = 0

    def write_ledger(self, *entries, schema=runner.LEDGER_SCHEMA):
        (self.root / runner.LEDGER_FILE).write_text(json.dumps({"schema": schema, "entries": list(entries)}))

    def run_fixture(self, output, code=1, capabilities=None):
        self.counter += 1
        out = self.root / ("run-" + str(self.counter))

        def child(command, **kwargs):
            kwargs["stdout"].write(TAP_PASS if "--test" in command else output)
            kwargs["stdout"].flush()
            return subprocess.CompletedProcess(command, 0 if "--test" in command else code)

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(runner, "NAMED", ["alpha.cjs"]))
            stack.enter_context(patch.object(runner, "INSTRUMENT", None))
            stack.enter_context(patch.object(runner, "HISTORICAL", {}))
            stack.enter_context(patch.object(runner, "HISTORY_INPUTS", {}))
            source = {"head": "a" * 40, "tree": "b" * 40, "workingChanges": []}
            stack.enter_context(patch.object(runner, "source_identity", return_value=source))
            stack.enter_context(patch.object(runner, "host_identity", return_value={"node": "controlled"}))
            stack.enter_context(patch.object(runner.subprocess, "run", side_effect=child))
            if capabilities is not None:
                stack.enter_context(patch.object(runner, "probe_capabilities", return_value=capabilities))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            result = runner.run(self.root, out)
        self.assertEqual(json.loads((out / "results.json").read_text()), result)
        return result, result["commands"][-1]

    def test_exact_declared_failure_is_never_plain_pass(self):
        self.write_ledger(entry())
        result, row = self.run_fixture(lines(("alpha case", None), ("beta", "Expected values to be equal")))
        self.assertEqual(row["status"], runner.DECLARED)
        self.assertEqual(row["ledger"]["expectedFail"], [{"case": "beta", "id": "L-beta"}])
        self.assertEqual(result["status"], runner.DECLARED)
        self.assertEqual(result["verdict"], "PASS_WITH_DECLARED_FAILURES (1)")
        with patch.object(runner, "run", return_value=result), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(["--output", str(self.root / "cli")]), 3)

    def test_g05_new_failure_inside_ledgered_instrument_fails_by_name(self):
        self.write_ledger(entry())
        result, row = self.run_fixture(lines(("beta", "Expected values"), ("gamma", "new regression")))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual([hit["case"] for hit in row["ledger"]["unexpectedFail"]], ["gamma"])

    def test_g06_repaired_case_with_active_entry_is_unexpected_pass(self):
        self.write_ledger(entry())
        result, row = self.run_fixture(lines(("beta", None)), code=0)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(row["ledger"]["unexpectedPass"], ["L-beta"])

    def test_g07_abort_before_terminal_is_never_expected_fail(self):
        self.write_ledger(entry())
        result, row = self.run_fixture("FAIL beta :: Expected values\nTypeError: boom\n")
        self.assertNotEqual(row["status"], runner.DECLARED)
        self.assertIn(result["status"], ("FAIL", "INCOMPLETE"))
        self.assertEqual(row["ledger"]["notAdjudicated"], ["L-beta"])
        self.assertEqual(row["ledger"]["expectedFail"], [])

    def test_g07_only_an_exact_whole_command_signature_covers_an_incomplete_command(self):
        signature = "SETUP_INCOMPLETE: controlled missing capability"
        self.write_ledger(entry(case=None, kind="command-incomplete", messagePrefix=signature, id="L-cmd"))
        _, row = self.run_fixture("PASS beta\n" + signature + "\n", code=0)
        self.assertEqual(row["status"], runner.DECLARED)
        self.write_ledger(entry(case=None, kind="command-incomplete", messagePrefix=signature + " (other)", id="L-cmd"))
        _, row = self.run_fixture("PASS beta\n" + signature + "\n", code=0)
        self.assertEqual(row["status"], "INCOMPLETE")

    def test_g08_malformed_wildcard_or_duplicate_entries_are_setup_errors(self):
        cases = {
            "missing field": [{key: value for key, value in entry().items() if key != "trigger"}],
            "wildcard": [entry(case="be*")],
            "duplicate id": [entry(), entry(case="gamma", id="L-beta")],
            "duplicate case": [entry(), entry(id="L-other")],
            "unknown cause": [entry(causeClass="flaky")],
            "bad owner": [entry(owner="somebody")],
            "undetermined without discriminator": [entry(causeClass="undetermined")],
            "outside population": [entry(command="not-a-command")],
            "empty prefix": [entry(messagePrefix="")],
        }
        for label, entries in cases.items():
            with self.subTest(label=label):
                self.write_ledger(*entries)
                result, _ = self.run_fixture(lines(("beta", "Expected values")))
                self.assertNotIn(result["status"], ("PASS", runner.DECLARED))
                self.assertTrue(result["setupErrors"], label)
        self.write_ledger(entry(), schema="other")
        result, _ = self.run_fixture(lines(("beta", "Expected values")))
        self.assertNotIn(result["status"], ("PASS", runner.DECLARED))
        # A valid entry would declare beta; one malformed sibling still makes the run INCOMPLETE.
        broken = {key: value for key, value in entry(case="gamma").items() if key != "evidence"}
        self.write_ledger(entry(), broken)
        result, row = self.run_fixture(lines(("beta", "Expected values")))
        self.assertEqual(row["status"], runner.DECLARED)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertTrue(any("missing field" in error for error in result["setupErrors"]))

    def test_g09_same_case_with_different_message_prefix_fails(self):
        self.write_ledger(entry(message="Expected values"))
        result, row = self.run_fixture(lines(("beta", "TypeError: different cause")))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(row["ledger"]["unexpectedFail"][0]["entryMismatch"], ["L-beta"])

    def test_absent_ledgered_case_is_not_executed_failure(self):
        self.write_ledger(entry(case="removed case"))
        result, row = self.run_fixture(lines(("beta", None)), code=0)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(row["ledger"]["notExecuted"], ["L-removed case"])

    def test_retired_entry_is_never_matched(self):
        self.write_ledger(entry(status="retired"))
        result, row = self.run_fixture(lines(("beta", "Expected values")))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["ledger"]["retired"], ["L-beta"])

    def test_conditional_entry_applies_only_when_the_probed_condition_holds(self):
        self.write_ledger(entry(condition="symlink-unavailable"))
        output = lines(("beta", "Expected values"))
        result, _ = self.run_fixture(output, capabilities={"symlink-unavailable": True})
        self.assertEqual(result["status"], runner.DECLARED)
        result, _ = self.run_fixture(output, capabilities={"symlink-unavailable": False})
        self.assertEqual(result["status"], "FAIL")

    def test_todo_exclusion_needs_an_exact_not_executed_entry(self):
        tap = TAP_PASS.replace("ok 1 - glob case", "ok 1 - retained join # TODO retained placeholder").replace(
            "# pass 1", "# pass 0").replace("# todo 0", "# todo 1")
        result, row = self.run_fixture(tap, code=0)
        self.assertEqual(row["status"], "INCOMPLETE")
        self.write_ledger(entry(case="retained join", kind="case-not-executed", messagePrefix="# TODO retained"))
        result, row = self.run_fixture(tap, code=0)
        self.assertEqual(row["status"], runner.DECLARED)
        self.assertEqual(row["ledger"]["declaredNotExecuted"], [{"case": "retained join", "id": "L-retained join"}])


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests").mkdir()
        (self.root / "tests/probe.test.cjs").write_text("//\n")
        (self.root / "tests/extra.cjs").write_text("//\n")

    def manifest(self, **extra):
        value = {"schema": runner.POPULATION_SCHEMA, "commands": [
            {"name": "extra", "argv": ["node", "tests/extra.cjs"], "protocol": "auto", "covers": ["tests/extra.cjs"],
             "inputs": ["tests/extra.cjs"]}], "modules": [], "exclusions": []}
        value.update(extra)
        (self.root / runner.POPULATION_FILE).write_text(json.dumps(value))

    def errors(self):
        with patch.object(runner, "NAMED", []), patch.object(runner, "INSTRUMENT", None):
            manifest, errors = runner.load_population(self.root)
            if manifest is None:
                return errors
            return errors + runner.census(self.root, runner.build_plan(self.root, None, None, manifest), manifest)

    def test_g10_registered_population_has_no_census_error(self):
        self.manifest()
        self.assertEqual(self.errors(), [])

    def test_g10_new_unregistered_instrument_is_a_setup_error(self):
        self.manifest()
        for path in ("tests/new-instrument.cjs", "tests/real-sky/new.test.mjs", "tests/real-sky/new_test.py"):
            with self.subTest(path=path):
                (self.root / path).parent.mkdir(exist_ok=True)
                (self.root / path).write_text("//\n")
                self.assertTrue(any(path in error for error in self.errors()))
                (self.root / path).unlink()

    def test_g10_unregistered_instrument_makes_the_whole_run_incomplete(self):
        self.manifest(commands=[])

        def child(command, **kwargs):
            kwargs["stdout"].write(TAP_PASS.replace("glob case", "probe"))
            return subprocess.CompletedProcess(command, 0)

        with patch.object(runner, "NAMED", []), patch.object(runner, "INSTRUMENT", None), \
                patch.object(runner, "source_identity", return_value={"head": None, "workingChanges": []}), \
                patch.object(runner, "host_identity", return_value={"node": "controlled"}), \
                patch.object(runner.subprocess, "run", side_effect=child), contextlib.redirect_stdout(io.StringIO()):
            result = runner.run(self.root, self.root / "receipt")
        self.assertEqual(result["commands"][0]["status"], "PASS")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertTrue(any("tests/extra.cjs" in error for error in result["setupErrors"]))

    def test_g10_module_or_exclusion_needs_reason_owner_and_an_existing_path(self):
        self.manifest(exclusions=[{"path": "tests/extra.cjs", "reason": "controlled"}])
        self.assertTrue(any("owner" in error for error in self.errors()))
        self.manifest(modules=[{"path": "tests/missing.cjs", "reason": "controlled"}])
        self.assertTrue(any("does not exist" in error for error in self.errors()))

    def test_repository_shaped_root_requires_the_manifest(self):
        (self.root / "tools/cp9").mkdir(parents=True)
        (self.root / "tools/cp9/run_native_regressions.py").write_text("#\n")
        self.assertTrue(any("population manifest missing" in error for error in self.errors()))

    def test_case_lines_require_the_declared_population(self):
        complete = runner.classify_extended("PASS a\nFAIL b :: msg\n", "case-lines", {"expectedCases": 2})
        self.assertEqual((complete["status"], complete["complete"]), ("FAIL", True))
        short = runner.classify_extended("PASS a\n", "case-lines", {"expectedCases": 2})
        self.assertEqual((short["status"], short["complete"]), ("INCOMPLETE", False))

    def test_unittest_cases_names_failures_errors_and_skips(self):
        log = "\n".join([
            "test_a (pkg.Case.test_a) ... ok", "test_b (pkg.Case.test_b) ... FAIL", "test_c (pkg.Case.test_c) ... ERROR",
            "test_d (pkg.Case.test_d) ... skipped 'no runtime'", "",
            "=" * 70, "FAIL: test_b (pkg.Case.test_b)", "-" * 70, "Traceback (most recent call last):",
            '  File "x.py", line 1, in test_b', "AssertionError: 1 != 2", "",
            "=" * 70, "ERROR: test_c (pkg.Case.test_c)", "-" * 70, "Traceback (most recent call last):",
            "OSError: [WinError 1314] privilege", "", "-" * 70, "Ran 4 tests in 0.010s", "", "FAILED (failures=1, errors=1, skipped=1)", ""])
        cases, complete = runner.unittest_cases(log)
        self.assertTrue(complete)
        self.assertEqual({case["name"]: (case["state"], case["message"]) for case in cases}, {
            "test_a (pkg.Case.test_a)": ("pass", ""), "test_b (pkg.Case.test_b)": ("fail", "AssertionError: 1 != 2"),
            "test_c (pkg.Case.test_c)": ("fail", "OSError: [WinError 1314] privilege"),
            "test_d (pkg.Case.test_d)": ("not-executed", "'no runtime'")})
        _, complete = runner.unittest_cases(log.replace("FAILED (failures=1, errors=1, skipped=1)", "FAILED (failures=2, errors=1, skipped=1)"))
        self.assertFalse(complete)


class LedgerMutationTests(unittest.TestCase):
    def test_runner_ledger_mutants_fail_their_named_controls(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        tests = Path(__file__).read_text(encoding="utf-8")
        mutations = [
            ("message-prefix-ignored", "and case['message'].startswith(hits[0]['messagePrefix'])", "",
             ("LedgerTests.test_g09_same_case_with_different_message_prefix_fails",)),
            ("unexpected-pass-ignored", "            report['unexpectedPass'].append(entry['id'])\n", "            pass\n",
             ("LedgerTests.test_g06_repaired_case_with_active_entry_is_unexpected_pass",)),
            ("ledger-errors-ignored", "    setup_errors += ledger_errors\n", "",
             ("LedgerTests.test_g08_malformed_wildcard_or_duplicate_entries_are_setup_errors",)),
            ("incomplete-adjudicated", "    if not complete or row['setup']['status'] != 'READY':", "    if False:",
             ("LedgerTests.test_g07_abort_before_terminal_is_never_expected_fail",)),
            ("census-blind", "    errors = ['unregistered instrument", "    errors = [] and ['unregistered instrument",
             ("PopulationTests.test_g10_new_unregistered_instrument_is_a_setup_error",)),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools/cp9").mkdir(parents=True)
            (root / "tests").mkdir()
            runner_path = root / "tools/cp9/run_native_regressions.py"
            test_path = root / "tests/test_regression_ledger.py"
            test_path.write_text(tests, encoding="utf-8")
            runner_path.write_text(source, encoding="utf-8")

            def execute(names):
                return subprocess.run([sys.executable, str(test_path), "-v", *names], capture_output=True, text=True, timeout=60)

            names = [name for *_, group in mutations for name in group]
            healthy = execute(names)
            self.assertEqual(healthy.returncode, 0, healthy.stdout + healthy.stderr)
            for label, before, after, group in mutations:
                with self.subTest(mutant=label):
                    self.assertEqual(source.count(before), 1, label + " mutation anchor")
                    runner_path.write_text(source.replace(before, after), encoding="utf-8")
                    mutated = execute(group)
                    output = mutated.stdout + mutated.stderr
                    self.assertNotEqual(mutated.returncode, 0, label + " survived")
                    self.assertIn("Ran ", output)
                    self.assertNotIn("SyntaxError", output)


if __name__ == "__main__":
    unittest.main()
