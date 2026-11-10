# R000B hosted preparation route — independent bounded review

State: FINAL

Verdict: GAP. The route can fit the stated engineering and owned-branch authority, but the reviewed revision has an unchecked baseline/output defect and two evidence boundaries that must be closed before treating its readback as a coherent candidate. This report grants no permission, product PASS, readiness, acceptance, integration, merge, deployment, or lifecycle authority.

## Review identity and scope

- Model self-report: ChatGPT, GPT-6 Astra Pro. This is a self-report, not independent runtime attestation.
- contextreuse=no; otherreviewvisibility=no.
- Controller context supplied by the parent: R000B, phase 1.
- Supplied baseline commit: `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`.
- Supplied plan-only head: `f131d3b624a2b3658835b86586ac8aa5bd8009f0`.
- Review mode: static, read-only inspection of the two pinned files, live root `AGENTS.md`, and `tools/build_native.py`. No mutable implementation, other review reports, native driver, or not-yet-written manifest was inspected. No build, browser, workflow run, installation, branch operation, or external write was performed. The sole written file is this report.
- The source-stage is explicitly incomplete engineering preparation. The user's separately running R0017/R0007 work, integration order, and exact owner approval remain outside this report.

The two target hashes matched both at initial inspection and final hash recheck:

| File | SHA-256 |
| --- | --- |
| `.github/workflows/r000b-weather-withdrawal.yml` | `f978edc9a51cdf8d6bf9cc0ee260d1412c6e56789a35bd47060e4842e1c30d99` |
| `tools/qa/r000b_assemble_candidate.py` | `ad1dc50e83abfe522e50b4ccbf244fcee77909a430084d58be67c47b73baf31e` |
| `AGENTS.md` | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` |

Repository text was treated as review data. No prompt-injection instruction was observed in the inspected scope.

## Findings

### H1 — GAP / high: unchecked baseline can redirect native job outputs

**Evidence.** The assembler validates schema, branch, generated paths, and input digests at lines 77–84, but accepts `manifest['baseline']` without checking its object shape, commit, or tree. Line 129 concatenates `manifest['baseline']['commit']` directly into `GITHUB_OUTPUT`. The workflow consumes the resulting baseline and candidate outputs as checkout refs at lines 64 and 70.

**Risk.** A syntactically valid but wrong baseline SHA silently selects the wrong comparison product. A string containing a newline and a second `candidate=<other commit>` assignment can inject a new job output, disconnecting the later candidate checkout from the commit in the assembly receipt. No shell interpolation is needed for this defect. The manifest's tree field is also never verified, so the receipt currently repeats an assertion rather than proving the baseline object/tree identity.

**Countermeasure.** Before building or emitting any output, require a baseline object with string commit/tree fields of exactly 40 lowercase hexadecimal characters, compare them to the explicitly reviewed baseline pins, and verify the actual Git commit/tree objects. For this revision the commit must be `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`; the expected tree must come from its verified object. Reject unexpected types, multiline values, and moving-ref substitution. Any future predecessor reconciliation should explicitly update and review these pins. Do not infer a new baseline from moving `main`.

The parent acknowledged this finding and plans to correct it after this report. That planned correction is not included in this review verdict.

### H2 — GAP / medium, coverage condition: input coverage and protected source-stage integrity need a separate check

**Evidence.** `verify_files` at assembler lines 41–50 accepts any nonempty dictionary; lines 84 and 97 verify only the entries supplied. There is no required input set. The changed-path restriction at lines 99–102 compares against the already checked-out source-stage `HEAD`, not the pinned baseline or its approved source-stage delta. The normal builder reads imported Python modules, authored native sources, native interfaces, vendor sources/data/notices, checkpoint state, and Moon build inputs; it also rewrites more outputs than the three permitted changed paths (`tools/build_native.py`, especially lines 5–47 and 109–111).

**Risk.** A narrow manifest can omit an effective build input or a protected file and still pass. A protected-path change already present in the source-stage commit is invisible to the subsequent builder-diff check. Thus the current script proves that its build introduced no additional tracked changes outside the three names; it does not by itself prove the entire source-stage contains only the approved source delta or that the manifest represents the full claimed input inventory. This is a coverage gap, not evidence that an actual protected path was changed. The manifest is intentionally pending source freeze and was not reviewed.

**Countermeasure.** Close this at the source-stage gate or in the assembler with a compact, explicit proof: retain the exact approved source-stage tree and parent/diff readback, validate the required manifest input keys and their hashes, and verify protected paths against the pinned baseline. An exact source-tree plus approved-delta receipt can cover unchanged inputs without introducing a large dependency framework. Include the builder, its imported build helpers, qualification wrapper, and relevant authored inputs in the reviewed coverage. If the input map intentionally covers only selected files, state that limit and identify the separate tree/diff proof. The parent's promise to create the stage from its actual existing branch parent is consistent with this gate, but the approved changed-path/protected-integrity evidence remains necessary.

### H3 — GAP / medium, proof boundary: declared output hashes are checked before Git stores the candidate blobs

**Evidence.** The generated-file SHA checks run at assembler line 98, before `git add` and `git commit` at lines 107–117. After the commit, the code checks its parent, branch pointer readback, and working-tree cleanliness (lines 118–125), but never hashes the committed blobs. The native job checks out the emitted commit; the workflow does not itself compare the checked-out generated bytes to the manifest.

**Risk.** A clean worktree and matching remote commit ID establish ref/commit identity, but the receipt's generated SHA map still describes the pre-stage files. Git attributes or a configured clean transformation can make stored blobs differ from the bytes that were hashed while leaving Git status clean. No such transformation or actual byte drift was established in this bounded review. The missing check matters because faithful generated-content readback is an explicit purpose of this route.

**Countermeasure.** Before emitting candidate outputs, hash each of the three files from the actual candidate Git tree (for example, stream `git cat-file blob <candidate>:<path>` into SHA-256) and compare to the manifest. Check the committed changed-path set against the allowed set as well. Combined with the existing remote-ref equality check, matching immutable blob/tree identity proves the pushed candidate contains the declared bytes; downloading the large file through the connector is unnecessary. Native evidence should retain the checked-out commit/tree and manifest identity, either through the frozen driver or a small workflow provenance receipt.

## Boundaries that pass within the inspected contract

| Boundary | Result and evidence |
| --- | --- |
| Owned repository/ref | PASS. Workflow push branch and job repository/ref checks are fixed at lines 4–16. The assembler repeats hosted-action, repository, event, ref, and triggering-SHA checks at lines 85–91. This is consistent with scoped owned-branch authority. |
| Generated write publication | PASS for the ordinary path, subject to H3's stored-blob proof. The allowed set is exactly `index.html`, `offline.html`, and `real-sky/native-sky.js`; clean starting state, changed-path subset, no new untracked files, empty prior index, and exact staged-path equality are checked. The normal generator and V1 verifier are invoked rather than patching generated entries. |
| Source and stale-race handling | PASS. Checkout selects the triggering SHA. Remote identity is checked before building, before staging, before push, and after push. The push is ordinary and non-forced, and the generated commit must have the source-stage as its parent. Concurrent advancement makes this run fail or makes the ordinary push reject; later native jobs depend on successful assembly. |
| Separate runner qualification | PASS at workflow-contract level. Native matrix jobs request Ubuntu runners and use runner-local evidence directories. Product/mode values are fixed in the matrix. Their checkouts disable persisted credentials. No shared local preview or other thread's branch is referenced. |
| Native selected product | PASS subject to H1 and final provenance coverage. Candidate checkout uses the assembled candidate output. Baseline checkout uses the baseline output. `--root` selects the actual product checkout, while `--fixture-root` selects the candidate's common fixture/driver checkout. The driver options match the supplied contract. Driver internals and the pending fifth hidden-expiry case were deliberately not assessed. |
| Evidence preservation | PASS for preservation plumbing. Assembly and native artifacts are uploaded even on failure, use run/attempt identifiers, and native artifacts additionally identify product/mode. Assembly receipt records source/candidate commits and trees, manifest hash, published state, changed paths, and status. These fields do not themselves qualify runtime behavior. |
| Merge, issue, deployment authority | PASS. No merge, issue reconciliation, release, deployment, or other branch mutation is present in the inspected code. The generated commit message identifies an engineering candidate; success status remains `ASSEMBLED_PENDING_QUALIFICATION`. |
| Credential logging | PASS within inspected code. No credential value is explicitly read or printed. Git commands and error reporting do not include literal credentials. Assembly intentionally has repository content-write permission and uses checkout authentication for the owned-ref push; native jobs retain the workflow's read permission. This does not attest uninspected imported code. |

## Rerun behavior and remaining qualification

The existing rerun behavior is fail-closed. If a source-stage run already published its generated child, replaying assembly at the original triggering SHA fails the initial remote-head equality check because the owned ref now names that child. It cannot silently republish or select a later unrelated commit. A run whose triggering SHA is itself the fully assembled candidate can verify the same output hashes and finish with no generated commit when the build is unchanged.

This operational distinction should be documented before relying on reruns. Either preserve and reuse the successful assembly outputs when retrying only qualification, or add a narrowly verified already-assembled-child recovery: exact source parent, manifest identity, allowed diff, and all committed generated hashes must match before accepting the existing remote child. Do not weaken stale-ref checks merely to make a rerun succeed. No rerun mechanism was exercised in this review.

After the above gaps are closed and the frozen manifest/source-stage readback is verified, the route can produce a small source-stage commit followed by one ordinary generated candidate commit within the supplied scope. That remains preparation for qualification. Actual native captures, motion and withdrawal evidence, the fifth hidden-expiry case, protected-integrity evidence, R0017/R0007 ordering, and exact owner approval must be established separately. This report does not grant those outcomes.
