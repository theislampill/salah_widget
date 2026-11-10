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
    def test_full_contains_the_original_population_and_two_sec_only_cells(self):
        plan = SELECTOR.plan_request(request("full"), RECIPE)
        self.assertEqual(plan["plannedCells"], 64)
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

    def test_timing_diagnostic_is_only_the_failed_healthy_cell(self):
        plan = SELECTOR.plan_request(request("firefox-reordered-timing"), RECIPE)
        self.assertEqual(plan["engines"], ["firefox"])
        self.assertEqual(plan["selectedCaseIds"], ["NE07-reordered24"])
        self.assertEqual(plan["plannedCells"], 1)
        self.assertTrue(plan["videoOnly"])

    def test_chromium_recaptures_all_five_barriers(self):
        plan = SELECTOR.plan_request(request("chromium-recovery"), RECIPE)
        self.assertEqual(plan["engines"], ["chromium"])
        self.assertEqual(set(plan["selectedCaseIds"]), set(SELECTOR.BARRIERS))
        self.assertEqual(plan["plannedCells"], 5)
        self.assertFalse(plan["videoOnly"])

    def test_sec_only_profiles_include_fresh_new_york_control_before_negative(self):
        for profile, engine, cells, video_only in [
                ("chromium-recovery-sec-only", "chromium", 6, False),
                ("firefox-dst-sec-only", "firefox", 2, True)]:
            with self.subTest(profile=profile):
                plan = SELECTOR.plan_request(request(profile), RECIPE)
                self.assertEqual(plan["engines"], [engine])
                self.assertEqual(plan["plannedCells"], cells)
                self.assertEqual(plan["videoOnly"], video_only)
                selected = plan["selectedCaseIds"]
                self.assertLess(selected.index("NE07-dst-recovery24"),
                                selected.index("NE07-mut-dst-sec-only"))
                expected = set(SELECTOR.BARRIERS) if engine == "chromium" else {"NE07-dst-recovery24"}
                self.assertEqual(set(selected), expected | {"NE07-mut-dst-sec-only"})

    def test_sec_only_uses_literal_frozen_ny_adoption_and_exact_stale_output(self):
        cases = {c["caseId"]: c for c in RECIPE["cases"]}
        case, healthy = cases["NE07-mut-dst-sec-only"], cases["NE07-dst-recovery24"]
        for field in ("entry", "hash", "clockPolicy", "cacheSeeds", "responseRules", "independentEndpoint"):
            self.assertEqual(case[field], healthy[field], field)
        self.assertNotIn("timeScale", case["hash"])
        self.assertIn("simTime=23%3A30", case["hash"])
        self.assertEqual(case["clockPolicy"], {"mode": "fixed", "epoch": "2026-03-08T04:30:00Z"})
        self.assertEqual(case["variant"], "sec-only")
        self.assertEqual(case["healthyControlCaseIds"], ["NE07-dst-recovery24"])
        self.assertEqual(case["expectedFailureContains"], "dom/.nt/text: expected '05:00', observed '—'")
        expected = {e["stage"]: e for e in case["expected"]}
        for field, value in {"wallUtcMs": 1772944200000, "clock/TIMESCALE": 0,
                             "clock/FOLLOW_WALL_CLOCK": False, "clock/ADVANCING": False}.items():
            self.assertEqual(expected["unavailable"]["equals"][field], value)
        self.assertEqual(expected["matching-tomorrow-settled"]["equals"], {
            "tomorrowDay": "08-03-2026", "wallUtcMs": 1772944200000,
            "clock/TIMESCALE": 0, "clock/FOLLOW_WALL_CLOCK": False, "clock/ADVANCING": False})
        self.assertLess([e["stage"] for e in case["expected"]].index("matching-tomorrow-settled"),
                        [e["stage"] for e in case["expected"]].index("after-next-settlement"))
        after = expected["after-next-settlement"]["equals"]
        self.assertEqual(next(iter(after)), "dom/.nt/text")
        self.assertEqual(after["render/nextEpoch"], 1772960400000)
        self.assertEqual(after["render/leftMin"], 270)
        self.assertEqual(after, next(e["equals"] for e in healthy["expected"] if e["stage"] == "after-next-settlement"))
        for actual, original in zip(case["orderedActions"], healthy["orderedActions"], strict=True):
            if original.get("awaitResult"):
                self.assertEqual(actual, {**original, "predicate": original["predicate"].replace("&&snapshot.dirty===false", "")})
            else:
                self.assertEqual(actual, original)

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
