"""Finite hosted selection controls; never launches a browser or a workflow."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("request_selector", ROOT / "tools/qualification/r0007_native_request.py")
SELECTOR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SELECTOR)
RECIPE = json.loads((ROOT / "tests/rlgwo/R0007-next-event-recipes.json").read_text())


def request(profile):
    return {"schema": "r0007-native-request/v1", "profile": profile, "requestId": "test", "reason": "bounded selection control"}


class SelectionTests(unittest.TestCase):
    def test_full_preserves_the_original_62_cell_population(self):
        plan = SELECTOR.plan_request(request("full"), RECIPE)
        self.assertEqual(plan["plannedCells"], 62)
        self.assertEqual(set(plan["selectedCaseIds"]), {c["caseId"] for c in RECIPE["cases"]})
        self.assertFalse(plan["videoOnly"])

    def test_diagnostic_is_one_engine_three_cases_with_actual_barrier(self):
        plan = SELECTOR.plan_request(request("firefox-video-diagnostic"), RECIPE)
        self.assertEqual(plan["engines"], ["firefox"])
        self.assertEqual(set(plan["selectedCaseIds"]), {"NE07-ordinary24", "NE07-spring24", "NE07-recovery24"})
        self.assertEqual(plan["plannedCells"], 3)
        self.assertTrue(plan["videoOnly"])

    def test_affected_selection_retains_mutant_healthy_companions_and_order(self):
        plan = SELECTOR.plan_request(request("firefox-affected"), RECIPE)
        self.assertEqual(plan["plannedCells"], 20)
        selected = plan["selectedCaseIds"]
        for case in RECIPE["cases"]:
            if case["caseId"] in selected and case.get("expectedFailure"):
                for control in case["healthyControlCaseIds"]:
                    self.assertLess(selected.index(control), selected.index(case["caseId"]))
        self.assertEqual(set(selected) - set(SELECTOR.FIREFOX_FAILED_HEALTHY + SELECTOR.MUTANTS),
                         {"NE07-reordered24", "NE07-recovery12", "NE07-fold", "NE07-dst-recovery24"})

    def test_chromium_recaptures_all_five_barriers(self):
        plan = SELECTOR.plan_request(request("chromium-recovery"), RECIPE)
        self.assertEqual(plan["engines"], ["chromium"])
        self.assertEqual(set(plan["selectedCaseIds"]), set(SELECTOR.BARRIERS))
        self.assertEqual(plan["plannedCells"], 5)
        self.assertFalse(plan["videoOnly"])

    def test_invalid_or_command_bearing_requests_fail_closed(self):
        examples = [None, [], {}, request("typo"), dict(request("full"), arguments=["--case-timeout-seconds", "99999"]),
                    dict(request("full"), profile=True), dict(request("full"), schema="other"),
                    dict(request("full"), reason=""), dict(request("full"), requestId="x" * 1001)]
        for value in examples:
            with self.subTest(value=value), self.assertRaises(ValueError):
                SELECTOR.plan_request(value, RECIPE)

    def test_metadata_cannot_become_command_arguments_and_inputs_are_unchanged(self):
        original = copy.deepcopy(RECIPE)
        value = request("firefox-video-diagnostic")
        value["reason"] = "--engine chromium; arbitrary command"
        plan = SELECTOR.plan_request(value, RECIPE)
        self.assertNotIn(value["reason"], plan["arguments"])
        self.assertEqual(RECIPE, original)


if __name__ == "__main__":
    unittest.main()
