"""Exact R0007 input reanchor; no main, browser, server or producer call."""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT / "candidate"
PRIOR_OUT = OUT.parent / "qualification-review-2f2d64c"
PRIOR = "2f2d64c5ee27708937dfcaa1233272f0cfa54ddc"
HEAD = "226c5e8fb1badc7244ca3fa4e0ce8d5f726972e5"
TREE = "d42f5ba6290aee94c677202cc64fba3024f427d5"
BASE = "5e946fe18a31750cf528bd58210ce79182dcf1e1"
RECIPE = "tests/rlgwo/R0007-next-event-recipes.json"
RAW = "docs/state-contracts/evidence/R0007/qualification/coverage-2f2d64c/evidence/original-native-requirement-excerpt.json"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


packet = json.loads((ROOT / RECIPE).read_text())
previous = json.loads(git("show", PRIOR + ":" + RECIPE))
old = {c["caseId"]: c for c in previous["cases"]}
new = {c["caseId"]: c for c in packet["cases"]}
assert len(old) == 30 and len(new) == 31 and set(new) - set(old) == {"NE07-dst-recovery12"}
assert all(old[i] == new[i] for i in old)
assert set(packet) == set(previous)
assert all(packet[k] == previous[k] for k in packet if k not in {"cases", "execution"})

added = new["NE07-dst-recovery12"]
control = new["NE07-dst-recovery24"]
allowed = {"caseId", "hash", "expected", "reviewRequirements"}
assert {k for k in added if added[k] != control[k]} == allowed
assert added["hash"] == control["hash"].replace("time=24", "time=12")
assert "simTime=23%3A30" in added["hash"] and "timeScale" not in added["hash"]
assert added["clockPolicy"] == control["clockPolicy"]
assert added["orderedActions"] == control["orderedActions"]
assert added["responseRules"] == control["responseRules"]
expected = copy.deepcopy(control["expected"])
recovered = next(e for e in expected if e["stage"] == "after-next-settlement")
recovered["equals"]["dom/.nt/text"] = "5:00 AM"
recovered["equals"]["dom/.left/text"] = "4h 30m left until Fajr"
recovered["regex"]["dom/.times/html"] = recovered["regex"]["dom/.times/html"].replace("05:00", "5:00 AM")
assert expected == added["expected"]
assert added["reviewRequirements"][:-1] == control["reviewRequirements"]
assert "Original A05" in added["reviewRequirements"][-1]

delta_execution = {k for k in packet["execution"] if packet["execution"][k] != previous["execution"][k]}
assert delta_execution == {"defaultCaseIds", "healthyCaseIds"}
for key in delta_execution:
    values = packet["execution"][key]
    assert values.count(added["caseId"]) == 1
    assert [v for v in values if v != added["caseId"]] == previous["execution"][key]

raw_bytes = git("show", HEAD + ":" + RAW)
assert raw_bytes == (OUT / "original-native-requirement-excerpt.json").read_bytes()
raw = json.loads(raw_bytes)
a05 = next(e for e in raw["excerpts"] if "R0007-A05" in e)
for term in ["Run12/24h fresh realms", "2026-03-08T04:30Z", "5:00 AM", "270m", "4h 30m"]:
    assert term in a05, term
literal = recovered["equals"]
accepted = datetime.fromtimestamp(literal["render/acceptedUtcMs"] / 1000, timezone.utc)
endpoint = datetime.fromtimestamp(literal["render/nextEpoch"] / 1000, timezone.utc)
assert accepted.isoformat() == "2026-03-08T04:30:00+00:00"
assert endpoint.isoformat() == "2026-03-08T09:00:00+00:00"
assert (endpoint - accepted).total_seconds() / 60 == literal["render/leftMin"] == 270
assert accepted.astimezone(ZoneInfo("America/New_York")).isoformat() == "2026-03-07T23:30:00-05:00"
assert endpoint.astimezone(ZoneInfo("America/New_York")).isoformat() == "2026-03-08T05:00:00-04:00"

native = load("exact_reanchor_native", "tools/qualification/r0007_native.py")
driver = load("exact_reanchor_driver", "tools/cp9/r0007_browser.py")
identity = native.clean_identity(ROOT)
assert identity == {"commit": HEAD, "tree": TREE}
execution = packet["execution"]
requested = execution["defaultCaseIds"] + execution["conditionalPreservationCaseIds"] + execution["mutationCaseIds"]
assert len(requested) == len(set(requested)) == 31
selected = native.select_cases(packet, requested)
assert {c["caseId"] for c in selected} == set(new)
healthy = [c for c in selected if not c.get("expectedFailure")]
mutants = [c for c in selected if c.get("expectedFailure")]
assert len(healthy) == 22 and len(mutants) == 9
assert selected == healthy + mutants
bound = native.bind_packet(ROOT, ROOT / RECIPE, identity, selected)
validated = driver.validate_cases(bound, ROOT)
assert validated["status"] == "PREPARED_NOT_EXECUTED" and validated["caseCount"] == 31
prior_bound = json.loads((PRIOR_OUT / "actual-bound-packet.json").read_text())
assert set(bound["sourceFiles"]) == set(prior_bound["sourceFiles"])
changed_bindings = [p for p, h in bound["sourceFiles"].items() if h != prior_bound["sourceFiles"][p]]
assert changed_bindings == [RECIPE]
assert len(bound["sourceFiles"]) == 147
save("actual-bound-packet.json", bound)

unchanged = ["src", "index.html", "offline.html", "config.js", "builder.html", "tools/build_native.py",
             "real-sky", "moon", "vendor", "v1", "tests/rlgwo/prayer-browser-fixture.cjs",
             "tools/cp9/browser_runtime.py", "tools/cp9/runtime_identity.py",
             "tools/cp9/r0007_browser.py", "tools/cp9/r0007_font_observer.js",
             "tools/qualification/r0007_native.py", ".github/workflows/r0007-native.yml",
             "tests/test_r0007_native_qualification.py", "tests/real-sky/cp9_browser_runtime_test.py"]
objects = []
for relative in unchanged:
    prior_object = git("rev-parse", PRIOR + ":" + relative).decode().strip()
    head_object = git("rev-parse", HEAD + ":" + relative).decode().strip()
    assert prior_object == head_object, relative
    item = {"path": relative, "priorObject": prior_object, "candidateObject": head_object, "identical": True}
    if relative in unchanged[:13]:
        base_object = git("rev-parse", BASE + ":" + relative).decode().strip()
        assert head_object == base_object
        item["acceptedBaseObject"] = base_object
    objects.append(item)
save("unchanged-identities.json", objects)

source_scope = ["tools", "tests", ".github", "src", "index.html", "offline.html", "config.js",
                "builder.html", "real-sky", "moon", "vendor", "v1"]
changed_paths = git("diff", "--name-only", PRIOR, HEAD, "--", *source_scope).decode().splitlines()
public_paths = {".github/workflows/r0007-public-delivery.yml", "tests/rlgwo/r0007-public-observer-control.cjs",
                "tests/test_r0007_public_delivery.py", "tools/qualification/r0007_public_cases.json",
                "tools/qualification/r0007_public_consumer.py"}
assert set(changed_paths) == public_paths | {RECIPE, "tests/r0007-recovery-precondition.test.cjs"}
assert not public_paths & set(bound["sourceFiles"])
old_font_test = git("show", PRIOR + ":tests/r0007-recovery-precondition.test.cjs").decode()
new_font_test = (ROOT / "tests/r0007-recovery-precondition.test.cjs").read_text()
assert old_font_test.replace("'NE07-dst-recovery24',", "'NE07-dst-recovery24','NE07-dst-recovery12',") == new_font_test

manifest = json.loads((OUT / "input-manifest.json").read_text())
for item in manifest["files"]:
    data = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
    assert data == git("show", HEAD + ":" + item["path"])
assert native.clean_identity(ROOT) == identity
result = {"identity": identity, "status": validated["status"], "oldCasesIdentical": 30,
          "addedCase": added["caseId"], "validatedCases": 31, "healthy": 22, "mutants": 9,
          "selectedDefault": len(execution["defaultCaseIds"]),
          "selectedPreservation": len(execution["conditionalPreservationCaseIds"]),
          "sourceFiles": len(bound["sourceFiles"]), "onlyChangedBinding": changed_bindings,
          "protectedIdentitiesUnchanged": len(objects), "acceptedBaseProtectedIdentitiesUnchanged": 13,
          "inputsReverified": len(manifest["files"]), "rawRequirementSha256": hashlib.sha256(raw_bytes).hexdigest(),
          "rawRequirementSource": RAW, "rawRequirementNetworkRetrieval": False,
          "newLiteralUtcEndpoints": [accepted.isoformat(), endpoint.isoformat()],
          "newLiteralLeftMin": 270, "publicFilesOutsideNativeBinding": sorted(public_paths),
          "nativeWorkflowUnchanged": True, "candidateClean": True,
          "mainInvoked": False, "nativeInvoked": False}
save("verification.json", result)
print(json.dumps(result, indent=2))
