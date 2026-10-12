"""Mechanical receiving update only: accepted prose on the recorded PR46 base."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
RUN = Path(r"C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009")
R1 = RUN / "workers/r0023_whole_closure_r1"
R2 = R1 / "addendum-r2"
OUT = R1 / "receiving-update-r3"
RECEIVER = Path(r"C:\Users\theis\.codex\worktrees\r0020-clock-docs-delivery\salah_widget")
W = Path(r"C:\Users\theis\.codex\worktrees\552b\salah_widget")
PR45 = RUN / "integration/r001c-whole-delivery-review-20261012-r1"
PR46 = RUN / "integration/r0020-whole-delivery-review-20261012-r1"
R1B = RUN / "workers/r001b_release_exit_r1"
BASE = "80e703864a74e3f67bc3d9b399fc1bbe64ea93b4"
PR45_BASE = "0e3a3ad6dc4f8e09ec8e246d12c70b8a996907df"
PREVIOUS = "88926dd12d22a6a8c1cd369d4823750778fccb48"
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def exact(record):
    actual = pin(record["path"])
    assert actual["bytes"] == record["bytes"] and actual["sha256"] == record["sha256"], record
    return Path(record["path"]).read_bytes()

def write(name, data):
    target = OUT / name
    assert target.resolve().is_relative_to(OUT.resolve())
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = data.encode("utf-8") if isinstance(data, str) else data
    if target.exists():
        assert target.is_file() and target.read_bytes() == raw, "Existing partial private output drifted; no overwrite."
        return pin(target)
    with target.open("xb") as stream:
        stream.write(raw)
    return pin(target)

def jout(name, value):
    return write(name, json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def privacy(text):
    assert text.count("### Auto-detect, precise location & privacy") == 1
    start = text.index("### Auto-detect, precise location & privacy")
    return text[start:text.index("\n---", start)]

# Only top-level sealed ancestry is checked. No 343-member recopy or re-review.
ancestry = {}
for label, folder, expected in [
    ("r1", R1, "4f4ce57e6cb4ddad4e150ecb471fd5dc43ce11e8d03c680fab5d05a61bec99c5"),
    ("r2", R2, "4529577fb15334fc9ef19c0aff697dccf0b5c5fa7b4429a379eb4722d998aca7"),
]:
    seal = pin(folder / "SEAL.json")
    assert seal["sha256"] == expected
    declared = read(folder / "SEAL.json")
    exact(declared["report"])
    exact(declared["manifest"])
    ancestry[label] = {"seal": seal, "report": declared["report"], "manifest": declared["manifest"]}

merge = read(PR45 / "MERGE_COMMIT_READBACK.json")
main = read(PR45 / "MAIN_AFTER_PR45.json")
assert merge["sha"] == main["object"]["sha"] == PR45_BASE
assert merge["parents"][0]["sha"] == PREVIOUS
assert {f["filename"] for f in merge["files"]} == {"AGENTS.md", "DESIGN.md", "OPTICS.md", "tests/rlgwo-docs-contract.cjs"}
proposal_path = RUN / "workers/r001c_whole_delivery_r1/source-proposal-r2/PROPOSED_SOURCE.json"
proposal = read(proposal_path)
assert proposal["baseCommit"] == PREVIOUS
main_files = []
for f in merge["files"]:
    original = next(p for p in proposal["files"] if p["file"] == f["filename"])
    raw = exact(original["proposed"])
    assert blob(raw) == f["sha"], f["filename"]
    if f["filename"] != "DESIGN.md":
        assert (RECEIVER / f["filename"]).read_bytes() == raw
    main_files.append({"file": f["filename"], "gitBlobSha1": f["sha"], "receiver": pin(RECEIVER / f["filename"]),
                       "acceptedPR45Postimage": original["proposed"], "exactHistoricPR45Blob": True,
                       "receiverContinuesViaOnlyPR46ClockHunks": f["filename"] == "DESIGN.md"})

merge46 = read(PR46 / "MERGE_COMMIT_READBACK.json")
main46 = read(PR46 / "MAIN_AFTER_PR46.json")
clock_review = read(PR46 / "REVIEW.json")
assert merge46["sha"] == main46["object"]["sha"] == BASE
assert merge46["tree"]["sha"] == "92ffde3dc7fa11ee9a6591b2a6def440f138aed1"
assert merge46["parents"][0]["sha"] == clock_review["receivingBase"] == PR45_BASE
assert clock_review["decision"] == "PASS_EXACT_RETAINED_CONSUMER_TRANSFER_AND_JOINED_DOCS_FOR_OWNER_RELEASE_REVIEW"
clock_guard_path = RUN / "workers/r0020_whole_closure_r1/PATCH_GUARD.json"
clock_guard = read(clock_guard_path)
assert clock_guard["onlyPatchPath"] == "DESIGN.md" and len(clock_guard["hunks"]) == 4

old_ops = read(R1 / "PATCH_MANIFEST.json")
base_readme = (R1 / "preimages/README.md").read_bytes()
assert (RECEIVER / "README.md").read_bytes() == base_readme
pr45_design_record = next(f["proposed"] for f in proposal["files"] if f["file"] == "DESIGN.md")
joined_clock_design = exact(pr45_design_record).decode("utf-8")
for hunk in clock_guard["hunks"]:
    before, after = exact(hunk["before"]).decode("utf-8"), exact(hunk["after"]).decode("utf-8")
    assert joined_clock_design.count(before) == 1 and joined_clock_design.count(after) == 0
    joined_clock_design = joined_clock_design.replace(before, after, 1)
base_design = joined_clock_design.encode("utf-8")
assert sha(base_design) == "8ea79974c6eb2d6df877d204135bff33b3466f78c3f78e2ce676cf9c0d4f9f05" and len(base_design) == 38354
assert exact(clock_review["actualJoinedDesign"]) == base_design == (RECEIVER / "DESIGN.md").read_bytes()
design_base_record = write("inputs/current-main-DESIGN.md", base_design)
bases = {"README.md": base_readme, "DESIGN.md": base_design}
base_records = {"README.md": pin(R1 / "preimages/README.md"), "DESIGN.md": design_base_record}

# PR45/PR46 changed no runtime: six accepted R0023 producer/consumer files remain exact.
source_binding = read(R1 / "SOURCE_BINDING.json")
runtime = []
for f in source_binding["files"]:
    observed = pin(RECEIVER / f["file"])
    assert observed["bytes"] == f["bytes"] and observed["sha256"] == f["sha256"]
    runtime.append({"file": f["file"], "receiver": observed, "r1AcceptedReadback": f["privateReadback"],
                    "exactUnchanged": True, "originalAcceptedSource": f["originalAcceptedSource"]})

# Consume the independently accepted sibling input, not a newly authored disclosure.
review_record = pin(R1B / "execution/R001B/release-review.json")
assert review_record["sha256"] == "00bc05cec952df7366280da6f31b1dc2125c4dcb24470264bd44ca735536659a"
review = read(review_record["path"])
assert review["decision"] == "PASS_EXACT_PRIVACY_DOCUMENTATION_ONLY_OWN_EXIT" and review["nodeExitSatisfied"]
assert review["reviewer"] == "/root/diagnostic_release_exit" and not review["wholeREADMEPASS"]
prose_record = review["evidenceBindings"]["ownedProseAndDiff"]
prose = json.loads(exact(prose_record).decode("utf-8-sig"))
accepted_readme_record = prose["acceptedRegionalEquality"][0]["accepted"]
accepted_text = exact(accepted_readme_record).decode("utf-8")
privacy_row = next(x for x in prose["regions"] if x["id"] == "R1B-PRIVACY")
credits_row = next(x for x in prose["regions"] if x["id"] == "R1B-CREDITS-STORAGE")
for row in [privacy_row, credits_row]:
    assert sha(row["text"].encode()) == row["utf8Sha256"]
accepted_privacy = privacy(accepted_text)
assert accepted_privacy == privacy_row["text"] + "\n"
r2_readme_record = pin(R2 / "postimages/README.md")
assert r2_readme_record["sha256"] == "ab6a41d5c0c0bcc8f5ea48507f546babcc2deaeb176fd4bbf0fbca0b566ab6a3"
r2_text = exact(r2_readme_record).decode("utf-8")
final_readme = r2_text.replace(privacy(r2_text), accepted_privacy, 1)
assert sha(final_readme.encode()) == "02d137c45bfdebd505cb39a775a94445e9bfc2be6312d46d6629e5776731ed13"
assert final_readme.count(credits_row["text"]) == 1
uncertainty = "Provider retention or handling is not established by this widget-source description."
assert final_readme.count(uncertainty) == 2  # Accepted privacy plus preserved r2 Credits.
design_op = next(x for x in old_ops["semanticOperations"] if x["file"] == "DESIGN.md")
design_text = base_design.decode("utf-8")
assert design_text.count(design_op["before"]) == 1
final_design = design_text.replace(design_op["before"], design_op["after"], 1)
assert final_design.replace(design_op["after"], design_op["before"], 1) == design_text
finals = {"README.md": final_readme, "DESIGN.md": final_design}

docs_record = pin(R1 / "accepted/evidence/R0023/documentation.json")
docs = read(docs_record["path"])
preserved = []
for row in docs["ownedRegions"]:
    text = finals[row["file"]]
    assert sha(row["text"].encode()) == row["sha256"] and text.count(row["text"]) == 1
    first = text[:text.index(row["text"])].count("\n") + 1
    preserved.append({"id": row["id"], "file": row["file"], "sha256": row["sha256"], "startLine": first,
                      "endLine": first + len(row["text"].splitlines()) - 1, "exact": True})
assert len(preserved) == 8
preferences = old_ops["preservedDeliveredR0010Preferences"]
assert final_readme.count(preferences["text"]) == 1 and sha(preferences["text"].encode()) == preferences["sha256"]
pr45_hunks = []
for hunk in proposal["hunks"]:
    if hunk["file"] != "DESIGN.md":
        continue
    value = exact(hunk["new"]).decode("utf-8")
    assert design_text.count(value) == final_design.count(value) == 1
    pr45_hunks.append({"id": hunk["id"], "acceptedHunk": hunk["new"], "exactFinalOccurrence": 1})
assert len(pr45_hunks) == 6
pr46_hunks = []
for hunk in clock_guard["hunks"]:
    value = exact(hunk["after"]).decode("utf-8")
    assert design_text.count(value) == final_design.count(value) == 1
    pr46_hunks.append({"id": hunk["id"], "acceptedHunk": hunk["after"], "exactFinalOccurrence": 1})
assert len(pr46_hunks) == 4

# Source identity continuation for the already accepted R001B request facts.
# Later runtime additions in two whole contexts do not alter the documented URLs/fields.
facts_record = review["evidenceBindings"]["sourceFacts"]
facts = json.loads(exact(facts_record).decode("utf-8-sig"))
r1b_facts = []
for row in facts["regions"]:
    relative = row["file"]["path"].split("salah_widget\\", 1)[1]
    raw = (RECEIVER / relative).read_bytes()
    accepted_raw = row["text"].encode()
    assert sha(accepted_raw) == row["regionSha256"]
    count = raw.count(accepted_raw)
    value = {"id": row["id"], "relativeFile": relative, "acceptedRegionSha256": row["regionSha256"],
             "exactWholeRegion": count == 1, "wholeFileEqual": sha(raw) == row["file"]["sha256"]}
    if count != 1:
        assert row["id"] in ["FONTS", "RADAR-URL"], row["id"]
        claim_lines = (
            ['<link rel="preconnect" href="https://fonts.googleapis.com">',
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
             'href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap"']
            if row["id"] == "FONTS" else
            ['  if(SIM.wx!=null || !usableWeatherCoordinates(lat,lon) || radarBusy) return;       // real mode only\n',
             '    const result=await wxFetchJson(op,a,"https://api.rainviewer.com/public/weather-maps.json");\n',
             '    const j=result.data, host=j&&j.host, past=j&&j.radar&&j.radar.past;\n',
             '      const fr=past[past.length-1];                           // mosaic generation time, not each contributing radar observation\n',
             '      const z=_RADAR_Z, n=Math.pow(2,z), latRad=captured.lat*Math.PI/180;\n',
             '      const fx=(captured.lon+180)/360*n, fy=(1-Math.log(Math.tan(latRad)+1/Math.cos(latRad))/Math.PI)/2*n;\n',
             '      const xt=Math.floor(fx), yt=Math.floor(fy);\n',
             '      const url=host+fr.path+"/256/"+z+"/"+xt+"/"+yt+"/2/1_1.png";\n',
             'sample:image.sample,source:"RainViewer mosaic",quantitativeAuthority:"unavailable (uncalibrated palette/alpha)"};']
        )
        for line in claim_lines:
            assert accepted_raw.count(line.encode()) == raw.count(line.encode()) == 1, (row["id"], line)
        value["exactDocumentedRequestConstruction"] = [{"text": line, "sha256": sha(line.encode()), "occurrences": 1} for line in claim_lines]
        value["differenceLimit"] = (
            "Accepted newer context has optional-font-loading comments/attributes; recipient and request URL are unchanged."
            if row["id"] == "FONTS" else
            "Accepted newer context additionally validates derived radar epochs; manifest, latest-past frame, coordinate tile construction and unavailable observation authority are unchanged."
        )
    r1b_facts.append(value)
assert len(r1b_facts) == 18 and sum(x["exactWholeRegion"] for x in r1b_facts) == 16

postimages = {name: write("postimages/" + name, text) for name, text in finals.items()}
patch = ""
patch_geometry = []
for name, text in finals.items():
    before = bases[name].decode("utf-8")
    old_lines, new_lines = before.splitlines(True), text.splitlines(True)
    opcodes = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes()
    rebuilt = "".join("".join(old_lines[i:j] if tag == "equal" else new_lines[k:l])
                      for tag, i, j, k, l in opcodes)
    assert rebuilt == text
    patch_geometry.append({"file": name, "preimage": base_records[name], "postimage": postimages[name],
                           "replaceOpcodes": sum(tag != "equal" for tag, *_ in opcodes), "deterministicReconstructionExact": True})
    patch += "".join(difflib.unified_diff(old_lines, new_lines, fromfile="a/" + name, tofile="b/" + name, n=3))
patch_record = write("R0023-current-main.patch", patch)

# Reuse the unchanged r2 VM adapter and exact accepted guard, with actual r3 input.
# The retained strengthened guard is in W, not PR45's delivered fixture.
guard_record = pin(RUN / "workers/settings_docs/pro-privacy-doc-correction-r1/guard-block.txt")
assert guard_record["sha256"] == "5c5102e92dfa2b519b411ec9a9d9b456d4600b899a1e2d2a51bc490d68e8d5db"
fixture_record = pin(W / "tests/rlgwo-docs-contract.cjs")
guard_bytes = exact(guard_record)
assert Path(fixture_record["path"]).read_bytes().count(guard_bytes) == 1
delivered_fixture = next(f for f in main_files if f["file"] == "tests/rlgwo-docs-contract.cjs")
assert Path(delivered_fixture["receiver"]["path"]).read_bytes().count(guard_bytes) == 0
adapter_record = pin(R2 / "credits-guard.cjs")
adapter_text = exact(adapter_record).decode("utf-8")
assert adapter_text.count("\n(async () => {\n") == 1
prefix = adapter_text.split("\n(async () => {\n", 1)[0]
adapter = prefix + """
(async () => {
  const r2 = exact(input.r2Readme);
  await probe('actual-r1-Credits-RED-retained', r1, creditsCheck, 'FAIL', 'sealed r1 actual Credits');
  await probe('actual-r2-whole-README-RED-retained', r2, wholeCheck, 'FAIL', 'sealed r2 actual postimage; old coarse paragraph');
  await probe('actual-r3-Credits-GREEN', successor, creditsCheck, 'PASS', 'actual r3 proposed README Credits');
  await probe('actual-r3-whole-README-guard-GREEN', successor, wholeCheck, 'PASS', 'actual r3 proposed README; bounded existing contradiction guard');
  await probe('actual-r3-blanket-claim-outside-privacy-RED', successor + '\\nControl: stores nothing about you.\\n', wholeCheck, 'FAIL', 'negative control appended outside privacy section');
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
"""
adapter_output = write("actual-postimage-guard.cjs", adapter)
control_input = jout("CONTROL_INPUT.json", {
    "schema": "r0023-actual-receiving-readme-guard-input/1", "r1Readme": pin(R1 / "postimages/README.md"),
    "r2Readme": r2_readme_record, "successorReadme": postimages["README.md"],
    "acceptedDisclosureReadme": accepted_readme_record, "acceptedCreditsClause": credits_row["text"],
    "providerUncertainty": uncertainty, "guard": guard_record, "currentFixture": fixture_record,
    "actualSuccessorNotProofOnly": True, "delivered": False, "wholeREADMEPASS": False,
})
node = shutil.which("node")
assert node
args = [node, adapter_output["path"], control_input["path"]]
result = subprocess.run(args, cwd=OUT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
stdout = write("checks/actual-postimage-guard.stdout.jsonl", result.stdout)
stderr = write("checks/actual-postimage-guard.stderr.log", result.stderr)
assert result.returncode == 0 and result.stderr == b"", (result.returncode, result.stdout, result.stderr)
controls = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
assert len(controls) == 5 and [row["status"] for row in controls] == ["FAIL", "FAIL", "PASS", "PASS", "FAIL"]
assert controls[3]["inputSha256"] == postimages["README.md"]["sha256"]
version = subprocess.run([node, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
assert version.returncode == 0 and version.stderr == b""

main_binding = jout("MAIN_BINDING.json", {
    "schema": "r0023-receiving-main-identity-continuation/1", "atUtc": NOW, "baseCommit": BASE,
    "baseTree": merge46["tree"]["sha"], "previousBase": PR45_BASE, "priorR1R2Base": PREVIOUS,
    "authority": "Owner-directed receiving update; root retains independent review/JOIN/Git/public/exact-head approval/closure.",
    "mainReadback": pin(PR46 / "MAIN_AFTER_PR46.json"), "mergeReadback": pin(PR46 / "MERGE_COMMIT_READBACK.json"),
    "ownerAuthorization": pin(PR46 / "OWNER_AUTHORIZATION.json"), "rootPR46Review": pin(PR46 / "REVIEW.json"),
    "PR46MergedReadback": pin(PR46 / "PR46_MERGED_READBACK.json"), "PR46ClockHunkInput": pin(clock_guard_path),
    "PR46ExactClockPostimage": design_base_record,
    "PR45MainReadback": pin(PR45 / "MAIN_AFTER_PR45.json"), "PR45MergeReadback": pin(PR45 / "MERGE_COMMIT_READBACK.json"),
    "PR45OwnerAuthorization": pin(PR45 / "OWNER_AUTHORIZATION.json"), "PR45ExactHeadDecision": pin(PR45 / "EXACT_HEAD_DECISION.json"),
    "rootSourceJoin": pin(PR45 / "SOURCE_JOIN.json"), "PR45SourceProposal": pin(proposal_path), "PR45Files": main_files,
    "READMEUnchangedFromPreviousMain": {"receiver": pin(RECEIVER / "README.md"), "immutablePreimage": base_records["README.md"], "exact": True},
    "acceptedR0023SourceBinding": pin(R1 / "SOURCE_BINDING.json"), "runtimeContinuation": runtime,
    "fullRuntimeIdenticalToAcceptedNewerE718Namespace": False, "qualificationTransferScope": "Only original bound location contract; original clocks/fixtures/native receipts and failures retained.",
    "liveRemoteCurrentnessRecheckedByWorker": False, "GitOperations": 0, "rootMustRecheckReceivingHeadBeforeEffects": True,
})
accepted_join = jout("ACCEPTED_INPUT_JOIN.json", {
    "schema": "r0023-mechanical-accepted-documentation-input-join/1", "atUtc": NOW,
    "acceptedR001BReview": review_record, "acceptedR001BSeal": pin(R1B / "SEAL.json"), "acceptedR001BProse": prose_record,
    "acceptedReadmeContext": accepted_readme_record, "privacyRegion": privacy_row, "creditsRegion": credits_row,
    "actualFinalPrivacyExact": True, "unchangedAcceptedR2Credits": True, "R001BIntroNotJoined": True,
    "sourceFactInput": facts_record, "currentMainSourceBindings": r1b_facts,
    "sourceBindingLimit": "16 accepted complete regions are exact; the two explicit later-context differences retain exact documented request construction. No source requalification or new transmission trace.",
    "priorCoalescedProof": pin(R2 / "CHECKS.json"), "actualFinalReadmeEqualsPriorProofSha256": postimages["README.md"]["sha256"],
    "independentReviewOfThisJoin": "PENDING_ROOT", "R001BWorkReopened": False, "R001BIssue27Complete": False,
    "wholeREADMEPASS": False, "newNativeCampaign": False,
})
checks = jout("CHECKS.json", {
    "schema": "r0023-receiving-update-checks/1", "atUtc": NOW,
    "command": {"args": args, "cwd": str(OUT), "exitCode": result.returncode, "stdout": stdout, "stderr": stderr,
                "input": control_input, "node": pin(node), "nodeVersion": version.stdout.decode().strip()},
    "existingGuardExecutedUnchanged": guard_record, "existingWorkingFixture": fixture_record,
    "PR45DeliveredFixture": delivered_fixture, "guardDeliveredByPR45": False, "fixtureModified": False,
    "reusedBoundedVMAdapter": adapter_record, "guardSourceAndAdapterPrefixUnchanged": True,
    "controls": controls, "all8R0023Regions": preserved, "deliveredR0010Preferences": preferences,
    "all6PR45DESIGNHunksPreserved": pr45_hunks, "all4PR46ClockHunksPreserved": pr46_hunks,
    "inverseR0023DESIGNEditRestoresExactPR46": True,
    "patchGeometry": patch_geometry, "gitApplyCheckedByWorker": False, "rootGitApplyCheckPending": True,
    "scope": "Bounded existing whole-document contradiction guard on actual proposed source, not whole-README factual approval.",
    "wholeREADMEPASS": False, "issue35Complete": False, "issue27Complete": False,
    "nativeExecutions": 0, "newSourceFixtureCampaigns": 0,
    "retainedPrivateAssemblyFailedAttempt": pin(OUT / "attempts/FIRST_EXECUTION.json"),
})
addendum = jout("DELIVERY_ADDENDUM.json", {
    "schema": "r0023-whole-return-receiving-update/1", "atUtc": NOW, "baseCommit": BASE, "ancestry": ancestry,
    "mainBinding": main_binding, "acceptedInputJoin": accepted_join, "checks": checks, "patch": patch_record,
    "preimages": base_records, "postimages": postimages, "all8R0023Regions": preserved,
    "supersedesPrivateDeliveryBindingsOnly": {"r1PatchManifest": pin(R1 / "PATCH_MANIFEST.json"), "r2PostimageAddendum": pin(R2 / "POSTIMAGE_ADDENDUM.json")},
    "unchanged343MembersRecopiedOrReaudited": False, "historicalFailedControlsAndNativeScopesRetained": True,
    "rootRequiredUpdates": ["Independently accept changed source/prose join and base continuation.",
                            "Check/apply only this README+DESIGN patch in the receiving checkout at exact current base.",
                            "Bind new doc postimages/lines/main identity in descendant documentation/final certificate/publication pins; retain original qualified evidence.",
                            "Create exact PR; obtain owner exact-head production merge/deploy approval; verify delivered/public state.",
                            "Reconcile/publish independent final certificate and manually close issue35 under original matrix."],
    "issue27CompletionCredit": False, "wholeREADMEPASS": False, "workerIndependentReviewCredit": False,
    "nativeGitPublicSharedCanonicalEffects": False,
})
write("PR_TITLE.txt", "Document reported location accuracy and saved target semantics\n")
write("PR_BODY.md", f"""README describes browser acquisition as precise GPS and treats partitioned storage as unwritable; DESIGN omits the implemented location-evidence schema. This delivers the eight independently accepted R0023 documentation regions, including reported accuracy, original fix age, saved targets, portable URL privacy, conservative legacy handling and conditional iframe permissions/storage. The delivered #16 preference paragraph, all PR45 hunks and all PR46 clock hunks are preserved.

The README also consumes the exact independently accepted R001B privacy/retention/Reset disclosure and browser settings/cache Credits clause to remove contradictory publication prose. Provider-policy uncertainty is retained. This is a mechanical accepted-input join; it does not claim whole-README factual approval or issue27 completion.

Validation at base `{BASE}`: all six connected R0023 source/consumer files remain byte-identical to the prior accepted delivered input; all eight prose regions remain exact. The unchanged existing whole-README contradiction guard is RED on the actual prior r2 postimage, GREEN on the actual final README, and RED when a blanket storage claim is appended outside the privacy section. The retained strengthened guard is a working-fixture check, not a claim that PR45 delivered it. The original 31 source cases/five named controls and 57 metadata/16 policy cases retain their prior receipts and evidence scope; no native replay occurred.

Refs #35. Exact-head owner approval, merge/public readback, independent final certificate/evidence publication and manual issue closure remain separately gated. Renderer/startup, third-party host, mobile and Apple evidence remains in its original scope.
""")
write("HANDOFF.md", f"""Use R0023-current-main.patch against exact base {BASE}. README postimage now actually contains the accepted privacy/retention/Reset hunk and the r2 Credits correction; its SHA equals the previously declared coalesced proof, but it is now a real proposed file. DESIGN is the exact PR46 delivered postimage plus only the original accepted R0023 schema/lifecycle replacement. All six PR45 DESIGN hunk contexts and four PR46 clock hunks remain exact; the inverse R0023 edit restores PR46 bytes. AGENTS/OPTICS/fixture/runtime are unchanged.

MAIN_BINDING.json binds existing owner/merge/source receipts and actual receiving bytes without Git/public reads or mutations. ACCEPTED_INPUT_JOIN.json binds exact independent R001B approval/prose and the source identity continuation, including two honest later-context differences that leave documented request construction intact. This does not re-open R001B, qualify its issue, or grant whole-README approval. Root must independently accept the changed JOIN/bindings; no competing #27 executor was created.

CHECKS.json executes the exact existing contradiction callback from the retained W fixture against the actual postimage. RED r1 Credits and RED actual r2 whole README are retained; actual r3 Credits/whole guard are GREEN; the appended whole-document contradiction control is RED. PR45's delivered fixture does not contain this later callback and is preserved unchanged. No full fixture or native campaign was run.

R1/r2 seals and all prior controls/receipt scopes remain immutable. No343-member recopy/re-review. This addendum replaces only private receiving patch/postimage/base bindings; root must update descendant documentation/final certificate/publication pins while retaining accepted evidence, run its own exact-base Git apply check, create the PR, secure owner's exact-head production merge/deploy approval, verify public delivery, publish the independently reconciled final certificate and manually close issue35. No worker whole-README, issue27, independent-review, delivered or issue-closure claim is made.
""")
report = jout("REPORT.json", {
    "schema": "rlgwo-whole-return-receiving-update-report/1", "worker": "/root/r0023_whole_closure", "atUtc": NOW,
    "issue": 35, "baseCommit": BASE, "status": "MECHANICAL_RECEIVING_UPDATE_READY_FOR_ROOT_INDEPENDENT_ACCEPTANCE",
    "patch": patch_record, "postimages": postimages, "mainBinding": main_binding, "acceptedInputJoin": accepted_join,
    "checks": checks, "deliveryAddendum": addendum, "preservedR0023Regions": 8, "preservedPR45DESIGNHunks": 6,
    "preservedPR46ClockHunks": 4,
    "preservedDeliveredR0010Paragraph": True, "actualFinalREADMEExistingGuard": "GREEN_WITH_RETAINED_RED_CONTROLS",
    "R1R2SealsImmutable": True, "unchanged343MembersRecopiedOrReaudited": False, "R001BCampaignAdded": False,
    "retainedPrivateAssemblyFailedAttempt": pin(OUT / "attempts/FIRST_EXECUTION.json"),
    "issue35Complete": False, "issue27Complete": False, "wholeREADMEPASS": False,
    "nativeGitPublicSharedCanonicalEffects": False, "rootIndependentAcceptance": "PENDING",
})

# Close only this additive private package; preserve both predecessors.
for value in ancestry.values():
    exact(value["seal"])
    exact(value["report"])
    exact(value["manifest"])
for name, record in postimages.items():
    exact(record)
members = [{"relativePath": p.relative_to(OUT).as_posix(), **pin(p)} for p in sorted(OUT.rglob("*")) if p.is_file()]
manifest = jout("MANIFEST.json", {"schema": "rlgwo-private-receiving-update-manifest/1", "atUtc": NOW,
                                  "files": members, "sealedAncestry": ancestry, "noUnchangedAncestryRecopy": True})
seal = jout("SEAL.json", {"schema": "rlgwo-private-receiving-update-seal/1", "atUtc": NOW,
                          "manifest": manifest, "report": report, "deliveryAddendum": addendum,
                          "sealedAncestry": ancestry, "rootIndependentAcceptance": "PENDING"})
print(json.dumps({"status": "RECEIVING_UPDATE_SEALED", "base": BASE, "patch": patch_record,
                  "postimages": postimages, "report": report, "seal": seal, "members": len(members),
                  "actualGuard": "RED r2 / GREEN actual r3 / RED appended blanket claim"}))
