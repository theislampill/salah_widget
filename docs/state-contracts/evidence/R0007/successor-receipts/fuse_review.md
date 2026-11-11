# R0007 font-use diagnostic — independent exact review

Disposition: **PASS**, findings only, for the exact frozen six-file candidate identified below. **No new actionable findings.** The patch implements the revised bounded plan and retains the original acquisition, oracles and acceptance population. This is not a native readability, production-fix, publication, readiness, merge or closure verdict.

A PARTIAL report was created before inspection. All executed controls used disposable review copies; the repository, index, refs, controller and frozen candidate were not modified by this reviewer.

## Immutable review object

| Object | Verified identity |
|---|---|
| Approved revised plan | SHA-256 `e7e4fed6b66780220835d2e11571ce8d1a8bcde69ee7c3011425eb9b2dd123a0` |
| Candidate manifest | SHA-256 `4dfedf0ec6ff8e24f588d0846ea96e4edfa709548de1f3ff7cbb1c3aaf67ed78` |
| Complete candidate patch | SHA-256 `31984510642be6fe6d029533036cdd2e8a8b56883e2d9898b4279320f470c0b1` |
| Expected parent | `9ed55e91db6df02f2bd1dfde153949a5bfb15811` |
| Reconstructed baseline tree | `786bceafa75231953599cb88bb5dbc2ef74a9eb3` |
| Independently computed candidate tree | `4d209e02084c99002ddf0f7f7509d62f3c409b79` |

Frozen root: `/workspace/scratch/66b3aaff4329/recovery/font-use-publication/candidate-4d209e02084c99002ddf0f7f7509d62f3c409b79`.

Every file's size, SHA-256, Git blob identity and Git `100644` classification matched the manifest. The frozen files are regular, non-symlink files with read-only filesystem permissions `0444`; no executable bits are set. The candidate directory contained exactly these six files:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `tests/r0007-font-use.test.cjs` | 2377 | `de22a06d317fa9d344390deba9b1027c21e0e3916c36cbaca020d6ed6a41dc3b` |
| `tests/rlgwo/R0007-font-use-recipes.json` | 18155 | `c49212867eec372aed08a95373b17d14d97cca6a7cf67eb6e99e9865fdab22d1` |
| `tests/rlgwo/R0007-native-request.json` | 390 | `b61c32c89faab6f75a16a588d8f9aa95c5e1b82288a7840df4e5864416724dc1` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | 15339 | `50642398dbb3ebacb36912cb2977b69e1520d60aaaf5f2dc4d2de63db6c107d2` |
| `tests/test_r0007_native_request.py` | 10311 | `85dce1e1d772e3f64068cc92b906820bda3e262cbb4c2bd60f18591a7dc90ec4` |
| `tools/qualification/r0007_native_request.py` | 6679 | `c54d3b8719aa00f77260e6db2ceadfaa92ab5c05003ffd981c4a4e0ce7a45213` |

Applying the exact patch to a disposable copy of the parent files reproduced the frozen files byte for byte. Independently enumerating the full baseline Git tree, hashing its structure in memory, replacing only the six manifest entries and hashing again reproduced both supplied tree identities. Thus the proposed tree delta retains every other tree entry, including the original recipe, authored/generated product, browser driver, workflow, scientific assets and V1. This is a prospective tree identity check, not a claim that publication has occurred.

## Exact implementation assessment

**Fixture intervention is limited to the two planned optional-family removals.** `tests/rlgwo/prayer-browser-fixture.cjs:119–124` adds one `font-fallback` variant to the existing exact-anchor mechanism. The fallback stacks remain the authored stacks. The link/provider/onload, direct hidden dialog fonts, all product JavaScript, existing rendering/fitting/dirty logic, and the instrumentation are otherwise unchanged. Existing anchor refusal remains at the same construction boundary.

**Diagnostic inputs and oracles are exact.** Full JSON comparison verifies that the first diagnostic object equals the complete original `NE07-fall24`; the second equals that same object with only `caseId` and `variant` added/changed. Both retain `expectedFailure: false`. The fixed epoch, held current body, loading capture and 250 ms hold, release occurrence, first-current predicate, target/time/date/epoch/countdown expectations, card geometry, acceptance IDs and independent endpoint all remain unchanged. The original recipe still contains 32 cases, and the unchanged full plan still selects 64 cells.

**The top-level selector actually reaches the new recipe.** `tools/qualification/r0007_native_request.py:109–112` selects one of two authored constant paths. Its new `firefox-font-use` branch selects only the ordinary/fallback pair (`:53–55`) and adds only the fixed diagnostic `--recipe` argument (`:72–74`). `plan_request` retains its exact request-key/schema/type/size validation (`:25–33`). No request value becomes a path, timeout, browser preference, or arbitrary command. The resulting arguments are exactly:

```text
--engine firefox --headed --video-only
--recipe tests/rlgwo/R0007-font-use-recipes.json
--case-id NE07-fall24 --case-id NE07-font-fallback-fall24
```

**The effect-bearing request is included.** `tests/rlgwo/R0007-native-request.json` selects `firefox-font-use`, uses request ID `r0007-font-use-20261110-01`, and explicitly states diagnostic-only intent. The unchanged workflow watches that request path. This resolves plan finding FUP-01 in the reviewed patch; actual remote selection remains a subsequent readback requirement.

**The recipe preserves conditional interpretation.** Its comparison rule includes all four ordinary/fallback visual outcomes. `diagnosticOnly: true` and the purpose text explicitly exclude production acceptance and preserve the original 32-case/full64 population. This resolves FUP-02 in the patch. Neither this metadata nor a successful source assertion makes the fallback arm a production qualification case.

## Independent executed verification

All evidence is retained under `/workspace/scratch/66b3aaff4329/recovery/font-use-exact-review-controls-gmyo3aem`. The JSON report lists exact evidence paths and hashes.

| Control | Result | Scope |
|---|---|---|
| Frozen Python selector suite | 12 passed | New finite recipe selection, exact case equality and original controls |
| Frozen Node fixture suite | 3 passed | Exact construction, missing/duplicate anchor refusal and ordinary preservation |
| Independently reconstructed baseline RED | Expected failures retained | New profile unknown, new recipe absent, new variant unknown; existing controls retain their expected success |
| Existing selector plans | 8 exactly equal | Full objects/arguments equal to independently loaded baseline selector and supplied baseline-plans receipt |
| Independent selector `main` controls | 18 passed | Fixed diagnostic routing, default-path preservation, metadata exclusion, nonzero propagation and refusal before native invocation |
| Original case document construction | 32 exactly equal | Old/new fixture output using verified generated root bytes for every original specification |
| Diagnostic generated document | Exact two-edit construction | Compared against baseline fixture's original preload/observer with precisely the two CSS removals |
| Generated-root anchor negatives | 4 refused | Missing/duplicate occurrence of each proposed font anchor |
| Manifest/patch/tree verification | Passed | Full six-file identities, exact patch reconstruction, full-tree identity derivation |

The 18 `main` controls include the positive diagnostic route, nonzero downstream return propagation, the original profile route with no diagnostic file, inert command-like metadata, additional recipe/argument fields, malformed schema/profile/text fields, non-object request, absent or malformed diagnostic JSON, missing/duplicate case IDs, changed committed request bytes, and a symlink request. Native execution was intercepted at `native.main`. Clean Git identity and committed request readback were also synthetic in these controls; the tests establish routing and refusal behavior, not a live Git or hosted-native acceptance result.

One reviewer-only mode probe initially expected writable filesystem permissions `0644` and failed on the deliberate read-only freeze (`0444`). That rejected probe is retained in `mode-controls-results.json`; the corrected regular-file/non-symlink/executable-bit classification confirms Git mode `100644` for all six files. It required no candidate change.

The supplied original RED/GREEN output hashes were independently verified. New baseline RED and candidate GREEN logs are separately retained; the original failures were not overwritten or converted into success.

### Generated-root identity and document results

The supplied immutable product was independently verified as 1,590,626 bytes, SHA-256 `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9`, Git blob `879bcc4c3d7866e02c7729f2252dce3553c6ae56`.

| Constructed diagnostic document | SHA-256 |
|---|---|
| Ordinary `NE07-fall24` | `882fddc98ac31c3b918de84ece81acbe09e6c51b73e24638164c84e3104c16d2` |
| Fallback `NE07-font-fallback-fall24` | `b8dc19a5779850deb5a692e8bb458eaaef0ea366096941dee996852a70e3a86e` |

All 32 old/new instrumented root-document hashes and both diagnostic hashes match the supplied preservation receipt. This covers string construction on the exact generated **root** entry using each case specification, including specifications naming offline. It does not inspect offline-entry bytes or requalify offline/native behavior.

## Findings reconciliation and dismissed observations

No new actionable findings were identified. The earlier findings FUP-01 and FUP-02 remain visible in `font_use_plan_review.md`; their plan-level remedies are present in this exact patch.

- **Recipe choice precedes full request validation.** Observed at selector lines 109–112. This is not an arbitrary-path boundary: the expression chooses only fixed authored paths and validates the request before calling native execution. Independent malformed-input controls refuse before that boundary. This assessment would be falsified by introducing request-derived path/argv text or invoking native execution before validation.
- **The diagnostic recipe retains inherited recovery and mutation guidance.** Those metadata fields do not select actions or cases. Exact two-case JSON equality, empty mutation/preservation lists and the fixed profile determine this acquisition. This is not a claim that recovery or mutation coverage was performed by the diagnostic. Counting those absent populations as qualified would exceed the evidence.
- **Font demand, fitting and timing may change.** These are admitted consequences of removing optional families from the two stacks. The intervention does not isolate all network, native-paint or recording variation, and the unchanged hidden dialog declarations remain. No font-free-document, universal cure, or exact browser timer claim follows.

## Reviewer provenance and authority ceiling

This reviewer did not author the plan or patch. The host reports a `fork_turns="none"` initial dispatch; the visible context contains the explicit task capsule, environment/skill instructions, supplied plan, this lane's prior findings-only plan review, and exact candidate/evidence. It does not contain the plan-authoring history. Supplied author test receipts were checked against independently executed controls rather than treated as sufficient by themselves.

Model self-report: **GPT-6 Astra Pro**, as provided by developer identity; no separate runtime model identifier was exposed. No nested reviewer was used. The audit playbook Finding Row Contract governs findings; this report claims no formal `audit-assess` lifecycle authority.

No browser, native acquisition, network request, workflow dispatch or publication occurred in this lane. No live pixels were adjudicated. Historical contrary native frames remain contrary evidence. Root owns remote currentness, prospective-effect verification, guarded publication, actual run/artifact readback and native frame review. Whole-contract qualification, accepted-main R0017 ordering, exact final review and owner merge approval remain required.

**Final disposition: PASS for this exact diagnostic patch, findings only.**
