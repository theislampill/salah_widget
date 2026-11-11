"""Finite hosted selection controls; never launches a browser or a workflow."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("request_selector", ROOT / "tools/qualification/r0007_native_request.py")
SELECTOR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SELECTOR)
RECIPE = json.loads((ROOT / "tests/rlgwo/R0007-next-event-recipes.json").read_text())
FUSE_RECIPE = json.loads((ROOT / "tests/rlgwo/R0007-font-use-recipes.json").read_text())

# Independent, literal selections catch altered companion inclusion or ordering.
# Each prefix also fixes the producer boundary: engine, headed/video mode and
# the only non-default recipe path admitted by an existing profile.
PRIOR_PROFILES = [
    ("full", ["--engine", "chromium", "--engine", "firefox", "--headed"], [
        "NE07-reordered24", "NE07-ordinary24", "NE07-missing", "NE07-wrong-day",
        "NE07-recovery24", "NE07-recovery12", "NE07-equal-polar", "NE07-spring24",
        "NE07-spring12", "NE07-fall24", "NE07-dst-ordinary24", "NE07-gap", "NE07-fold",
        "NE07-dst-recovery24", "NE07-dst-recovery12", "NE07-reordered-offline",
        "NE07-reordered-iframe", "NE07-wall-ordinary-control", "NE07-preserve-no-preference",
        "NE07-preserve-reduce", "NE07-preserve-reduce-full", "NE07-preserve-warm-ashen-below-horizon",
        "NE07-mut-hardcoded-fajr", "NE07-mut-name-order", "NE07-mut-lost-date",
        "NE07-mut-independent-label", "NE07-mut-ambiguous-epoch", "NE07-mut-remove-next-dirty",
        "NE07-mut-epoch-plus24", "NE07-mut-wall-spring", "NE07-mut-wall-fall", "NE07-mut-dst-sec-only"]),
    ("firefox-video-diagnostic", ["--engine", "firefox", "--headed", "--video-only"], [
        "NE07-ordinary24", "NE07-recovery24", "NE07-spring24"]),
    ("firefox-affected", ["--engine", "firefox", "--headed", "--video-only"], [
        "NE07-reordered24", "NE07-ordinary24", "NE07-recovery24", "NE07-recovery12",
        "NE07-equal-polar", "NE07-spring24", "NE07-fall24", "NE07-fold",
        "NE07-dst-recovery24", "NE07-dst-recovery12", "NE07-wall-ordinary-control",
        "NE07-mut-hardcoded-fajr", "NE07-mut-name-order", "NE07-mut-lost-date",
        "NE07-mut-independent-label", "NE07-mut-ambiguous-epoch", "NE07-mut-remove-next-dirty",
        "NE07-mut-epoch-plus24", "NE07-mut-wall-spring", "NE07-mut-wall-fall"]),
    ("firefox-reordered-timing", ["--engine", "firefox", "--headed", "--video-only"], [
        "NE07-reordered24"]),
    ("firefox-reordered-companions", ["--engine", "firefox", "--headed", "--video-only"], [
        "NE07-reordered24", "NE07-ordinary24", "NE07-mut-hardcoded-fajr", "NE07-mut-name-order",
        "NE07-mut-lost-date", "NE07-mut-independent-label"]),
    ("firefox-font-use", ["--engine", "firefox", "--headed", "--video-only", "--recipe",
                          "tests/rlgwo/R0007-font-use-recipes.json"], [
        "NE07-fall24", "NE07-font-fallback-fall24"]),
    ("chromium-recovery", ["--engine", "chromium", "--headed"], [
        "NE07-recovery24", "NE07-recovery12", "NE07-dst-recovery24", "NE07-dst-recovery12",
        "NE07-mut-remove-next-dirty"]),
    ("chromium-recovery-sec-only", ["--engine", "chromium", "--headed"], [
        "NE07-recovery24", "NE07-recovery12", "NE07-dst-recovery24", "NE07-dst-recovery12",
        "NE07-mut-remove-next-dirty", "NE07-mut-dst-sec-only"]),
    ("firefox-dst-sec-only", ["--engine", "firefox", "--headed", "--video-only"], [
        "NE07-dst-recovery24", "NE07-mut-dst-sec-only"]),
]
INGRESS_PREFIX = ["--engine", "firefox", "--headed", "--video-only", "--recipe",
                  "tests/rlgwo/R0007-font-ingress-recipes.json"]
INGRESS_CASE_IDS = ["NE07-fall24", "NE07-font-fallback-fall24"]


def launch_arguments(prefix, case_ids):
    return prefix + [value for case_id in case_ids for value in ("--case-id", case_id)]


def ingress_template():
    diagnostic = copy.deepcopy(FUSE_RECIPE)
    for case in diagnostic["cases"]:
        case["fontIngress"] = "late-css-held-fonts-v1"
    return diagnostic


def load_ingress_recipe(test):
    try:
        return json.loads((ROOT / "tests/rlgwo/R0007-font-ingress-recipes.json").read_text())
    except FileNotFoundError:
        test.fail("the font-ingress profile has no committed-recipe template to select")


def request(profile):
    return {"schema": "r0007-native-request/v1", "profile": profile, "requestId": "test", "reason": "bounded selection control"}


class SelectionTests(unittest.TestCase):
    def test_font_ingress_is_a_constant_two_case_headed_video_selection(self):
        diagnostic = ingress_template()
        diagnostic["cases"].append(copy.deepcopy(next(
            c for c in RECIPE["cases"] if c["caseId"] == "NE07-ordinary24")))
        original = copy.deepcopy(diagnostic)
        value = request("firefox-font-ingress")
        original_request = copy.deepcopy(value)
        try:
            plan = SELECTOR.plan_request(value, diagnostic)
        except ValueError as error:
            self.fail("the fixed font-ingress profile must be selectable: " + str(error))
        self.assertEqual(plan, {
            "profile": "firefox-font-ingress", "engines": ["firefox"], "videoOnly": True,
            "requestedCaseIds": ["NE07-fall24", "NE07-font-fallback-fall24"],
            "selectedCaseIds": ["NE07-fall24", "NE07-font-fallback-fall24"],
            "plannedCells": 2, "arguments": launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS)})
        self.assertEqual(diagnostic, original)
        self.assertEqual(value, original_request)
        for field, override in [("recipe", "untrusted.json"), ("arguments", ["--case-id", "NE07-ordinary24"]),
                                ("fontIngress", "other-mode"), ("holdMs", 99999)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                SELECTOR.plan_request({**value, field: override}, diagnostic)

    def test_font_ingress_recipe_preserves_the_two_complete_fuse_case_objects(self):
        diagnostic = load_ingress_recipe(self)
        self.assertEqual(diagnostic["cases"], [
            {**case, "fontIngress": "late-css-held-fonts-v1"} for case in FUSE_RECIPE["cases"]])
        self.assertEqual(diagnostic["execution"], FUSE_RECIPE["execution"])
        plan = SELECTOR.plan_request(request("firefox-font-ingress"), diagnostic)
        self.assertEqual(plan["selectedCaseIds"], ["NE07-fall24", "NE07-font-fallback-fall24"])
        self.assertEqual(plan["arguments"], launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS))

    def test_effect_request_selects_the_fixed_font_ingress_pair(self):
        value = json.loads((ROOT / "tests/rlgwo/R0007-native-request.json").read_text())
        diagnostic = load_ingress_recipe(self)
        plan = SELECTOR.plan_request(value, diagnostic)
        self.assertEqual(plan["profile"], "firefox-font-ingress")
        self.assertEqual(plan["arguments"], launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS))
        self.assertEqual(plan["plannedCells"], 2)

    def test_all_nine_prior_profiles_keep_exact_selections_and_launch_arguments(self):
        for profile, prefix, case_ids in PRIOR_PROFILES:
            with self.subTest(profile=profile):
                recipe = FUSE_RECIPE if profile == "firefox-font-use" else RECIPE
                plan = SELECTOR.plan_request(request(profile), recipe)
                self.assertEqual(plan["selectedCaseIds"], case_ids)
                self.assertEqual(plan["arguments"], launch_arguments(prefix, case_ids))
                self.assertEqual(plan["engines"], ["chromium", "firefox"] if profile == "full" else [prefix[1]])
                self.assertEqual(plan["videoOnly"], "--video-only" in prefix)
                self.assertEqual(plan["plannedCells"], len(case_ids) * (2 if profile == "full" else 1))

    def test_font_use_diagnostic_is_a_constant_two_case_recipe(self):
        base = copy.deepcopy(next(c for c in RECIPE["cases"] if c["caseId"] == "NE07-fall24"))
        fallback = {**base, "caseId": "NE07-font-fallback-fall24", "variant": "font-fallback"}
        diagnostic = {**RECIPE, "cases": [base, fallback]}
        plan = SELECTOR.plan_request(request("firefox-font-use"), diagnostic)
        self.assertEqual(plan["engines"], ["firefox"])
        self.assertEqual(plan["selectedCaseIds"], ["NE07-fall24", "NE07-font-fallback-fall24"])
        self.assertEqual(plan["plannedCells"], 2)
        self.assertEqual(plan["arguments"], [
            "--engine", "firefox", "--headed", "--video-only",
            "--recipe", "tests/rlgwo/R0007-font-use-recipes.json",
            "--case-id", "NE07-fall24", "--case-id", "NE07-font-fallback-fall24"])
        self.assertNotIn("--case-timeout-seconds", plan["arguments"])
        with self.assertRaises(ValueError):
            SELECTOR.plan_request({**request("firefox-font-use"), "recipe": "untrusted.json"}, diagnostic)

    def test_font_use_recipe_preserves_every_original_case_input_and_oracle(self):
        diagnostic = json.loads((ROOT / "tests/rlgwo/R0007-font-use-recipes.json").read_text())
        base = next(c for c in RECIPE["cases"] if c["caseId"] == "NE07-fall24")
        self.assertEqual(diagnostic["cases"], [base, {
            **base, "caseId": "NE07-font-fallback-fall24", "variant": "font-fallback"}])
        self.assertEqual(diagnostic["execution"]["defaultCaseIds"],
                         ["NE07-fall24", "NE07-font-fallback-fall24"])
        self.assertEqual(diagnostic["execution"]["mutationCaseIds"], [])
        self.assertEqual(diagnostic["execution"]["conditionalPreservationCaseIds"], [])
        self.assertEqual(diagnostic["diagnosticOnly"], True)
        self.assertEqual(diagnostic["sourceCommit"], "UNBOUND")
        self.assertEqual(diagnostic["sourceFiles"]["index.html"], "UNBOUND")
        self.assertIn("tests/rlgwo/R0007-next-event-recipes.json",
                      diagnostic["bindingInstructions"]["sourcePaths"])

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

    def test_reordered_companions_keeps_both_fresh_controls_and_only_four_dependents(self):
        original = copy.deepcopy(RECIPE)
        plan = SELECTOR.plan_request(request("firefox-reordered-companions"), RECIPE)
        self.assertEqual(plan["engines"], ["firefox"])
        self.assertTrue(plan["videoOnly"])
        self.assertEqual(plan["plannedCells"], 6)
        self.assertEqual(plan["selectedCaseIds"], [
            "NE07-reordered24", "NE07-ordinary24", "NE07-mut-hardcoded-fajr",
            "NE07-mut-name-order", "NE07-mut-lost-date", "NE07-mut-independent-label"])
        cases = {case["caseId"]: case for case in RECIPE["cases"]}
        for case_id in plan["selectedCaseIds"][2:]:
            self.assertEqual(cases[case_id]["healthyControlCaseIds"],
                             ["NE07-reordered24", "NE07-ordinary24"])
        self.assertEqual(RECIPE, original)
        self.assertNotIn("--case-timeout-seconds", plan["arguments"])
        self.assertNotIn("--mutation-only", plan["arguments"])

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


class SelectorMainTests(unittest.TestCase):
    """Real selection and Git custody, with only the external producer replaced."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="r0007-selector-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def git(self, root, *arguments):
        return subprocess.check_output([
            "git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
            "-c", "user.name=R0007 selector test", "-c", "user.email=selector@example.invalid",
            "-C", str(root), *arguments], text=True, stderr=subprocess.PIPE).strip()

    def candidate(self, profile, recipe_path, recipe, request_mode="file"):
        root = self.directory / profile / "source"
        evidence = self.directory / profile / "evidence"
        root.mkdir(parents=True)
        destination = root / recipe_path
        destination.parent.mkdir(parents=True)
        destination.write_text(json.dumps(recipe) + "\n", encoding="utf-8")
        request_path = root / "tests/rlgwo/R0007-native-request.json"
        if request_mode != "missing":
            request_bytes = (json.dumps(request(profile), indent=2) + "\n").encode()
            if request_mode == "symlink":
                (root / "request.json").write_bytes(request_bytes)
                request_path.symlink_to("../../request.json")
            else:
                request_path.write_bytes(request_bytes)
        self.git(root, "-c", "init.templateDir=", "init", "--initial-branch=fixture")
        self.git(root, "add", "--all")
        self.git(root, "commit", "--quiet", "-m", "Synthetic selector request fixture")
        identity = {"commit": self.git(root, "rev-parse", "HEAD"),
                    "tree": self.git(root, "rev-parse", "HEAD^{tree}")}
        return root, evidence, identity

    def invoke(self, root, evidence, producer_exit=0):
        launches = []

        def external_producer(arguments):
            launches.append(list(arguments))
            return producer_exit

        with mock.patch.object(SELECTOR.native, "main", new=external_producer):
            result = SELECTOR.main(["--source-root", str(root), "--evidence-root", str(evidence)])
        receipt = json.loads((evidence / "request-selection.json").read_text())
        return result, receipt, launches

    def test_pair_css_receiving_contract(self):
        """Break: omitted/weakened external receiving obligations or loss during binding.

        These independent literals protect the reviewed declaration delivered to
        the receiver. They neither compare CSS nor adjudicate actual evidence.
        """
        diagnostic = load_ingress_recipe(self)
        requirements = diagnostic.get("comparisonRequirements")
        self.assertIsInstance(requirements, list, "the pair needs its external receiving contract")
        matches = [row for row in requirements if isinstance(row, dict)
                   and row.get("kind") == "font-ingress-diagnostic"]
        self.assertEqual(len(matches), 1, "exactly one contract must bind the diagnostic pair")
        contract = matches[0]
        self.assertEqual(contract.get("cases"), ["NE07-fall24", "NE07-font-fallback-fall24"])
        self.assertEqual(contract.get("receivingPrerequisite"),
            "Before any baseline-only, both-arm, fallback-only or neither-arm interpretation, receive the two actual "
            "fulfilled/delivered CSS SHA256 values with each complete arm binding below. Require hash equality or an "
            "explicit independently received semantic-equivalence disposition tied to both exact retained bodies, "
            "hashes and native receipts.")
        self.assertEqual(contract.get("cssPair"), {
            "deliveredHashField": "trace.fontIngress.css.deliveredCssSha256",
            "equalHashesDisposition": "Eligible for arm comparison only after both per-arm bindings and all other diagnostic prerequisites are received.",
            "differentHashesDisposition": "CONFOUNDED unless the independent equivalence review below establishes the relevant CSS equivalence.",
            "retainBothExactBodies": True,
            "armBinding": {
                "retainedFulfilledBody": "trace.fontIngress.css.apiBody: path, bytes and sha256 of the exact unmodified CSS supplied to fulfillment.",
                "originalLinkRequest": "trace.fontIngress.css.requestId: the actual original-link native Request identity.",
                "originalLinkResponse": "trace.fontIngress.css.responseId: the actual native Response associated with that Request.",
                "fulfillment": "trace.fontIngress.css.fulfillment must be fulfilled only after successful fulfill(response=api_response) without status, header or body overrides.",
                "nativeTerminal": "trace.fontIngress.css.nativeTerminal must be finished for that same original-link Request, with valid native status/MIME and no redirect or failure.",
                "trustedApplication": "Named observation receipts must bind the trusted original-link load to the exact connected authored link, its current media=all application and relevant registered faces. A capture receipt with mediaAtDispatch=print may be valid when the current link is all.",
                "hashBinding": "deliveredCssSha256 must equal apiBody.sha256 and may be accepted only after the actual native Request/Response/finished receipt, successful unmodified fulfillment and trusted load/current application are all bound.",
            },
            "nativeBody": {
                "field": "trace.fontIngress.css.nativeBody",
                "availabilityStates": ["captured", "unavailable"],
                "capturedRule": "Retain the separately captured native CSS hash and require it to equal deliveredCssSha256 and apiBody.sha256.",
                "unavailableRule": "Retain status=unavailable and the actual reason. Explicitly assess the fulfilled-byte/native-transaction binding with this limitation; do not claim independent native-body capture or treat an intended URL plus API body as sufficient.",
            },
            "independentEquivalence": {
                "requiredBindings": [
                    "both exact retained CSS bodies", "both deliveredCssSha256 values",
                    "both complete original-link native receipts",
                    "both native-body availability states and any captured hashes"],
                "requiredSemanticCoverage": [
                    "relevant @font-face descriptors", "family, style, weight and stretch coverage",
                    "font-display policy", "Unicode ranges", "declared resource identities"],
                "rule": "A separate explicit independent review must establish equivalence and retain its disposition against both bodies/hashes/native receipts. URL equality, user-agent equality, equal face counts or an assumed provider response cannot establish it.",
            },
            "allowResponseEditingNormalizationReplayOrReplacementForEquality": False,
            "requireEqualFontDemandOrBodyCounts": False,
            "fontDemandRule": "Arm-dependent font demand and body differences are intended evidence. Do not require the fallback arm to request or download unused optional faces.",
        })
        pair = contract["cssPair"]
        self.assertIs(pair["retainBothExactBodies"], True)
        self.assertIs(pair["allowResponseEditingNormalizationReplayOrReplacementForEquality"], False)
        self.assertIs(pair["requireEqualFontDemandOrBodyCounts"], False)
        self.assertIs(contract.get("automaticRerun"), False)
        self.assertEqual(contract.get("outcomes"), {
            "baselineOnlyLoss": "May implicate optional-family use in this controlled occurrence after all pair prerequisites; historical cause and ordinary-network timing equivalence remain unassigned.",
            "bothArmsOrFallbackOnlyLoss": "Family removal is insufficient; preserve the actual new witness and matched visibility/source state.",
            "neitherArmLoss": "INCONCLUSIVE; end this repeat line and retain the gap for an explicit bounded containment or truthful unresolved disposition.",
            "confoundedOrUnrealized": "Retain the exact missing or failed prerequisite and make no arm attribution.",
        })
        self.assertEqual(contract.get("scope"),
            "Receiving metadata only: no added prayer/font-readiness wait, case oracle, acceptance row, readability "
            "tolerance, browser preference, provider change, deadline change or native acceptance waiver.")

        # Exercise the real committed-source binder with the actual recipe data;
        # synthetic Git custody is confined to this test's temporary directory.
        original = copy.deepcopy(diagnostic)
        relative_recipe = "tests/rlgwo/R0007-font-ingress-recipes.json"
        root, _, _ = self.candidate("firefox-font-ingress", relative_recipe, diagnostic)
        sources = set(diagnostic["bindingInstructions"]["sourcePaths"]) | set(diagnostic["sourceFiles"])
        sources.update({"tools/cp9/r0007_font_observer.js", "tools/qualification/r0007_native.py"})
        for relative in sorted(sources):
            destination = root / relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                # The binder hashes these committed fixture blobs; no product
                # consumer is executed and scoped snapshots need not include it.
                destination.write_text("Synthetic contract-binding source: " + relative + "\n", encoding="utf-8")
        self.git(root, "add", "--all")
        self.git(root, "commit", "--quiet", "-m", "Synthetic pair-contract source binding")
        identity = SELECTOR.native.clean_identity(root)
        selected = SELECTOR.native.select_cases(diagnostic, ["NE07-fall24", "NE07-font-fallback-fall24"])
        bound = SELECTOR.native.bind_packet(root, root / relative_recipe, identity, selected)
        self.assertEqual(bound.get("comparisonRequirements"), requirements)
        self.assertEqual(bound["acquisitionBinding"]["recipeSha256"],
                         hashlib.sha256((root / relative_recipe).read_bytes()).hexdigest())
        self.assertEqual(diagnostic, original)

    def test_main_reads_only_the_fixed_ingress_recipe_and_binds_the_request(self):
        root, evidence, identity = self.candidate(
            "firefox-font-ingress", "tests/rlgwo/R0007-font-ingress-recipes.json", ingress_template())
        result, receipt, launches = self.invoke(root, evidence)
        self.assertEqual(result, 0, receipt.get("failure"))
        self.assertEqual(receipt["identity"], identity)
        self.assertEqual(receipt["requestSha256"], hashlib.sha256(
            (root / "tests/rlgwo/R0007-native-request.json").read_bytes()).hexdigest())
        self.assertEqual(receipt["selectorSha256"], hashlib.sha256(
            (ROOT / "tools/qualification/r0007_native_request.py").read_bytes()).hexdigest())
        self.assertEqual(receipt["request"], request("firefox-font-ingress"))
        self.assertEqual(receipt["selection"]["arguments"], launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS))
        self.assertEqual(launches, [["--source-root", str(root), "--evidence-root", str(evidence),
                                    *launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS)]])
        self.assertTrue(receipt["launched"])
        self.assertEqual(receipt["status"], "COLLECTED_SOURCE_SCOPES_ONLY")
        self.assertEqual(receipt["nativeAcceptance"], "NONE_SELECTION_ONLY")

    def test_main_preserves_the_actual_recipe_path_and_arguments_for_all_nine_profiles(self):
        for profile, prefix, case_ids in PRIOR_PROFILES:
            with self.subTest(profile=profile):
                recipe_path = ("tests/rlgwo/R0007-font-use-recipes.json" if profile == "firefox-font-use"
                               else "tests/rlgwo/R0007-next-event-recipes.json")
                recipe = FUSE_RECIPE if profile == "firefox-font-use" else RECIPE
                root, evidence, identity = self.candidate(profile, recipe_path, recipe)
                result, receipt, launches = self.invoke(root, evidence)
                self.assertEqual(result, 0, receipt.get("failure"))
                self.assertEqual(receipt["identity"], identity)
                self.assertEqual(receipt["selection"]["selectedCaseIds"], case_ids)
                self.assertEqual(receipt["selection"]["arguments"], launch_arguments(prefix, case_ids))
                self.assertEqual(launches, [["--source-root", str(root), "--evidence-root", str(evidence),
                                            *launch_arguments(prefix, case_ids)]])

    def test_main_rejects_request_byte_drift_even_when_git_status_hides_it(self):
        root, evidence, _ = self.candidate(
            "firefox-font-ingress", "tests/rlgwo/R0007-font-ingress-recipes.json", ingress_template())
        relative = "tests/rlgwo/R0007-native-request.json"
        self.git(root, "update-index", "--assume-unchanged", "--", relative)
        value = request("firefox-font-ingress")
        value["reason"] = "Uncommitted effect-bearing request bytes hidden from status"
        (root / relative).write_text(json.dumps(value) + "\n", encoding="utf-8")
        self.assertEqual(self.git(root, "status", "--porcelain", "--untracked-files=normal"), "")
        result, receipt, launches = self.invoke(root, evidence)
        self.assertEqual(result, 1)
        self.assertFalse(receipt["launched"])
        self.assertEqual(receipt["status"], "FAILED")
        self.assertIn("native request differs from its committed bytes", receipt["failure"])
        self.assertEqual(launches, [])

    def test_main_rejects_a_committed_request_symlink_before_launch(self):
        root, evidence, _ = self.candidate(
            "firefox-font-ingress", "tests/rlgwo/R0007-font-ingress-recipes.json",
            ingress_template(), request_mode="symlink")
        result, receipt, launches = self.invoke(root, evidence)
        self.assertEqual(result, 1)
        self.assertFalse(receipt["launched"])
        self.assertEqual(receipt["status"], "FAILED")
        self.assertIn("native request cannot be a symlink", receipt["failure"])
        self.assertEqual(launches, [])

    def test_main_rejects_dirty_source_before_launch(self):
        root, evidence, _ = self.candidate(
            "firefox-font-ingress", "tests/rlgwo/R0007-font-ingress-recipes.json", ingress_template())
        (root / "tests/rlgwo/R0007-native-request.json").write_text("{}\n", encoding="utf-8")
        result, receipt, launches = self.invoke(root, evidence)
        self.assertEqual(result, 1)
        self.assertFalse(receipt["launched"])
        self.assertEqual(receipt["status"], "FAILED")
        self.assertIn("candidate is not clean", receipt["failure"])
        self.assertEqual(launches, [])

    def test_main_without_a_committed_request_preserves_the_full_legacy_path(self):
        root, evidence, identity = self.candidate(
            "full", "tests/rlgwo/R0007-next-event-recipes.json", RECIPE, request_mode="missing")
        result, receipt, launches = self.invoke(root, evidence)
        self.assertEqual(result, 0, receipt.get("failure"))
        self.assertEqual(receipt["identity"], identity)
        self.assertIsNone(receipt["requestSha256"])
        self.assertEqual(receipt["request"]["requestId"], "legacy-no-request")
        self.assertEqual(receipt["selection"]["profile"], "full")
        _, prefix, case_ids = PRIOR_PROFILES[0]
        self.assertEqual(launches, [["--source-root", str(root), "--evidence-root", str(evidence),
                                    *launch_arguments(prefix, case_ids)]])

    def test_main_retains_a_failed_producer_exit_without_a_second_attempt(self):
        root, evidence, _ = self.candidate(
            "firefox-font-ingress", "tests/rlgwo/R0007-font-ingress-recipes.json", ingress_template())
        result, receipt, launches = self.invoke(root, evidence, producer_exit=23)
        self.assertEqual(result, 23, receipt.get("failure"))
        self.assertEqual(receipt["exitCode"], 23)
        self.assertTrue(receipt["launched"])
        self.assertEqual(receipt["status"], "ACQUISITION_NOT_ACCEPTED")
        self.assertEqual(receipt["nativeAcceptance"], "NONE_SELECTION_ONLY")
        self.assertEqual(launches, [["--source-root", str(root), "--evidence-root", str(evidence),
                                    *launch_arguments(INGRESS_PREFIX, INGRESS_CASE_IDS)]])


if __name__ == "__main__":
    unittest.main()
