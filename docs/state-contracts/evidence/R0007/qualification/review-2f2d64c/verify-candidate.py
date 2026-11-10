"""Read-only exact-candidate binding and protected-source verification.

No producer/main/browser/server/remote invocation. The only writes are review
artifacts next to this file; the checked-out candidate remains clean.
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT / "candidate"
BASE = "5e946fe18a31750cf528bd58210ce79182dcf1e1"
PRIOR = "b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b"
HEAD = "2f2d64c5ee27708937dfcaa1233272f0cfa54ddc"
TREE = "c8693811c4dfe73b2810e7bb5f6cb81f33019d1a"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


native = load("exact_candidate_native", "tools/qualification/r0007_native.py")
driver = load("exact_candidate_driver", "tools/cp9/r0007_browser.py")
identity = native.clean_identity(ROOT)
assert identity == {"commit": HEAD, "tree": TREE}, identity
recipe = ROOT / native.DEFAULT_RECIPE
original = json.loads(recipe.read_text())
selected = native.select_cases(original, [])
bound = native.bind_packet(ROOT, recipe, identity, selected)
validated = driver.validate_cases(bound, ROOT)
assert validated["status"] == "PREPARED_NOT_EXECUTED"
assert len(selected) == 30
assert bound["bindingStatus"] == "BOUND_CANDIDATE_NOT_EXECUTED"
assert bound["nativeStatus"] == "BOUND_NOT_EXECUTED"
assert bound["sourceFiles"][native.FONT_OBSERVER] == "ca8fcb547fca54e5edd8ba40c896497c6cda75b38acc7a6e4df276a2eeb21d1b"
save("actual-bound-packet.json", bound)
healthy = [c["caseId"] for c in selected if not c.get("expectedFailure")]
mutants = [c["caseId"] for c in selected if c.get("expectedFailure")]
assert len(healthy) == 21 and len(mutants) == 9
first_mutant = min(i for i, c in enumerate(selected) if c.get("expectedFailure"))
assert all(not c.get("expectedFailure") for c in selected[:first_mutant])
assert all(c.get("expectedFailure") for c in selected[first_mutant:])
save("binding-validation.json", {
    "identity": identity,
    "status": validated["status"],
    "sourceFiles": len(bound["sourceFiles"]),
    "caseCount": len(selected),
    "healthyControls": healthy,
    "mutants": mutants,
    "healthyBeforeMutants": True,
    "actualCommittedRecipeSha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
    "observerSha256": bound["sourceFiles"][native.FONT_OBSERVER],
    "nativeInvoked": False,
})

protected = ["src", "index.html", "offline.html", "config.js", "builder.html", "tools/build_native.py",
             "real-sky", "moon", "vendor", "v1", "tests/rlgwo/prayer-browser-fixture.cjs",
             "tools/cp9/browser_runtime.py", "tools/cp9/runtime_identity.py"]
protected_rows = []
for relative in protected:
    base_object = git("rev-parse", BASE + ":" + relative).decode().strip()
    head_object = git("rev-parse", HEAD + ":" + relative).decode().strip()
    assert base_object == head_object, relative
    protected_rows.append({"path": relative, "baseObject": base_object,
                           "candidateObject": head_object, "identical": True})
assert not git("diff", "--name-only", BASE, HEAD, "--", *protected).strip()
save("protected-identities.json", protected_rows)

prior = json.loads(git("show", PRIOR + ":" + native.DEFAULT_RECIPE))
base = json.loads(git("show", BASE + ":" + native.DEFAULT_RECIPE))
base_by_id = {c["caseId"]: c for c in base["cases"]}
old_by_id = {c["caseId"]: c for c in prior["cases"]}
new_by_id = {c["caseId"]: c for c in original["cases"]}
assert old_by_id.keys() == new_by_id.keys()
changed = []
for case_id, new in new_by_id.items():
    old = old_by_id[case_id]
    assert base_by_id[case_id]["expected"] == new["expected"], case_id
    assert old["expected"] == new["expected"], case_id
    assert old["clockPolicy"] == new["clockPolicy"], case_id
    assert old["responseRules"] == new["responseRules"], case_id
    if old == new:
        continue
    differing = [k for k in old.keys() | new.keys() if old.get(k) != new.get(k)]
    assert differing == ["orderedActions"], (case_id, differing)
    assert len(old["orderedActions"]) == len(new["orderedActions"])
    actions = []
    for i, (oa, na) in enumerate(zip(old["orderedActions"], new["orderedActions"])):
        if oa != na:
            fields = sorted(k for k in oa.keys() | na.keys() if oa.get(k) != na.get(k))
            assert fields == ["predicate"], (case_id, i, fields)
            assert oa["type"] == na["type"] == "wait"
            assert "__r0007FontSettlement.settled()" in na["predicate"]
            actions.append({"index": i, "changedFields": fields})
    assert len(actions) == 1
    changed.append({"caseId": case_id, "actions": actions})
assert len(changed) == 4
assert not git("diff", "--name-only", PRIOR, HEAD, "--", ".github/workflows/r0007-native.yml").strip()
assert native.clean_identity(ROOT) == identity
save("recipe-delta.json", {"cases": len(new_by_id), "expectedOraclesUnchanged": True,
      "expectedOraclesUnchangedFromAcceptedBase": True,
      "clockPoliciesUnchanged": True, "ingressRulesUnchanged": True,
      "onlyChangedCaseFields": changed, "workflowUnchangedFromPrior": True})
manifest = json.loads((OUT / "input-manifest.json").read_text())
reverified = []
for item in manifest["files"]:
    data = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    assert data == git("show", HEAD + ":" + item["path"]), item["path"]
    reverified.append(item["path"])
save("verification.json", {"identity": identity, "cleanAfterTests": native.clean_identity(ROOT) == identity,
      "allManifestInputsMatchExactCommit": True, "reverifiedInputCount": len(reverified),
      "protectedObjectsMatchAcceptedBase": len(protected_rows), "nativeInvoked": False})
print(json.dumps({"identity": identity, "boundFiles": len(bound["sourceFiles"]),
                  "validatedCases": len(selected), "healthy": len(healthy), "mutants": len(mutants),
                  "protectedPathsIdentical": len(protected_rows), "changedBarriers": len(changed),
                  "status": validated["status"], "nativeInvoked": False}, indent=2))
