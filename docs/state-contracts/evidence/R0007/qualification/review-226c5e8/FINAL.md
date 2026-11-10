# R0007 exact native-input reanchor — FINAL

**Disposition: PASS for this bounded input-qualification reanchor.** The added `NE07-dst-recovery12` supplies the original A05 12-hour frozen spring overnight recipe cell. Exact candidate `226c5e8fb1badc7244ca3fa4e0ce8d5f726972e5` binds and validates all 31 selected cases. No new concrete blocker is identified. This is not native, pixel, first-visible or whole-owner acceptance, and does not confer dispatch or integration authority.

## Exact identity and independence

- model_requested: inherited parent model; no override requested
- model_actual: GPT-6 Astra Pro (self-report from active developer identity; independent backend model identifier not exposed)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- candidate_commit: `226c5e8fb1badc7244ca3fa4e0ce8d5f726972e5`
- candidate_tree: `d42f5ba6290aee94c677202cc64fba3024f427d5`
- accepted_qualification_prior_commit: `2f2d64c5ee27708937dfcaa1233272f0cfa54ddc`
- accepted_qualification_prior_tree: `c8693811c4dfe73b2810e7bb5f6cb81f33019d1a`
- accepted_product_base_commit: `5e946fe18a31750cf528bd58210ce79182dcf1e1`
- accepted_product_base_tree: `6e9eced1194d2463f5090fcdb086e771e1100916`
- native_executed: no

The inputs came from an isolated clean detached local clone pinned to that commit. All 18 selected materialized inputs were compared with exact Git objects and reverified after the direct binding check. No later root working-tree or evidence-only commit is credited. The review reused only this reviewer's own preceding report and source bindings; the original A05 excerpt is preserved raw requirement data. No other review, coverage analysis, Andon report or author reasoning was opened, and no agent-list query was made.

All writes are confined to this review directory. The target repository, refs and index were not modified. No network, browser, server, main, producer, workflow or other native action was invoked. The local clone read existing Git objects only. Repository AGENTS and the audit playbook/Finding Row Contract from the preceding bounded review remain applicable; this is plain engineering review without formal audit-assess authority.

## Original requirement and added case

The preserved raw source is `docs/state-contracts/evidence/R0007/qualification/coverage-2f2d64c/evidence/original-native-requirement-excerpt.json`, SHA-256 `edf91261070a446f76659601c95290f8236851a7a6d9732467aedd8f7faae041`. It identifies a prior received contract readback from issue 7, comment 6074567851; this review made no current network retrieval. The raw excerpt explicitly requires A05 to run the frozen New York spring overnight recovery in fresh 12- and 24-hour realms, keeping the accepted `2026-03-08T04:30Z` epoch through admission of March 8 Fajr and expecting `05:00`/`5:00 AM`, 270 minutes and a 4h 30m countdown.

The new case is an exact clone of `NE07-dst-recovery24` except for these deliberate fields:

| Field | New case |
|---|---|
| Case identifier | `NE07-dst-recovery12` |
| Display-format hash parameter | `time=12`, retaining `simTime=23%3A30` and omitting `timeScale` |
| Recovered `.nt` literal | `5:00 AM` |
| Selected Fajr row literal | `5:00 AM` |
| Additional recovered `.left` equality | `4h 30m left until Fajr` |
| Review requirement | Adds an explicit original-A05 12-hour cell note |

Its clock policy, response rules, cache inputs, entry, ordered actions, captures, readiness predicate and deadlines are unchanged from the 24-hour source case. Existing unavailable-state assertions and the remaining recovered assertions are retained. The unchanged driver creates a fresh context for each case; this is a declared execution path, not an observed native run.

The new expectations retain accepted UTC `1772944200000`, next UTC `1772960400000` and `leftMin=270`. An independent Python UTC conversion verifies 04:30Z to 09:00Z, exactly 270 minutes. ZoneInfo maps those literals to March 7 23:30 EST and March 8 05:00 EDT in New York. This verifies internal consistency of the supplied literal endpoints, without deriving a replacement product oracle or claiming browser output.

**All 30 prior case objects are identical as parsed JSON.** The only changed top-level recipe section besides the case list is `execution`: the new ID is inserted once into both `defaultCaseIds` and `healthyCaseIds`; all prior entries keep their order. The mutation and conditional-preservation lists are unchanged. Machine-readable evidence is retained in `verification.json`, with the exact checks in `verify-reanchor.py`.

## Selection, binding and native-scope isolation

The native workflow's existing selection now yields **18 default + 4 conditional-preservation + 9 mutant cases = 31 unique cases per engine**. The actual launcher selection returns all 31, with **22 healthy cases before 9 mutants**. Existing mutant dependency declarations are unchanged because their full case objects are unchanged. The same serial two-engine plan therefore has 62 planned case observations, two more than before; workflow time limits and resource policy are unchanged. No runtime sufficiency or completed observation is inferred from that count.

The actual clean candidate's `clean_identity`, `select_cases`, `bind_packet` and `driver.validate_cases` all pass. The result binds **147 source files** to the exact commit/tree and returns **`PREPARED_NOT_EXECUTED`**. The source-path set is identical to the prior accepted binding; **only the recipe SHA-256 changes among those 147 bindings**. The full prepared packet is retained as `actual-bound-packet.json`, and the result log as `actual-reanchor-binding.log`.

Nineteen protected/helper/test tree or blob identities are identical to the accepted 2f candidate, including the native driver, collector, font observer, native workflow, qualification tests and selector tests. Thirteen product/generated/shared identities also directly match accepted 5e: `src`, generated entries, config, builder, build tool, `real-sky`, `moon`, `vendor`, `v1`, shared prayer fixture, browser runtime and runtime identity helper. Directory-tree equality covers all tracked descendants. See `unchanged-identities.json`.

The five public-delivery additions are separate paths: its workflow, observer control, tests, case packet and consumer. None belongs to the native binder's 147-file source set. Source-path delta inspection confirms that, apart from those additions, only the native recipe and its five-predicate control file changed. The native workflow and all its native code dependencies are unchanged. This establishes the requested file/binding isolation; the separate public delivery behavior and its review reports are outside this reanchor.

## Verification performed and reused

| Evidence | Result / treatment |
|---|---|
| Changed `tests/r0007-recovery-precondition.test.cjs` | 16/16 test groups pass, now exercising all five exact recovery predicates; exit 0 |
| Actual clean candidate binding and driver validation | 147 committed file bindings; 31 cases; `PREPARED_NOT_EXECUTED`; exit 0 |
| Prior 24 qualification controls | Reused; helper/driver/test identities unchanged; not rerun |
| Prior 5 browser-selector controls | Reused; runtime/selector test identities unchanged; not rerun |
| Prior observer adversarial controls and QR-B20-01/02 closures | Reused at their original instrumentation scope because driver/collector/observer bytes are unchanged |
| Case/source preservation | All 30 old cases identical; 19 protected/helper/test identities equal prior; 13 product/shared identities equal accepted base; all 18 selected input files reverified |

The changed test file differs from its predecessor only by adding `NE07-dst-recovery12` to its predicate-ID list. Its passing groups retain the delayed-stylesheet, layout, readiness, typed terminal-event, deferred-receipt, dirty-clear, lifecycle and fallback discrimination. The pure controls do not observe native font service or browser scheduling.

The reused own preceding report is SHA-256 `0206cc43ebc2092632b874ea2fe20bda90ada0f3e278f6a100bf6f0f34f8c9fe`. Its qualification-only PASS remains bounded as written; this reanchor does not retroactively turn those source controls into native evidence.

## Exact input hashes

| File | SHA-256 |
|---|---|
| `tests/rlgwo/R0007-next-event-recipes.json` | `63899d8bdb86ec9576edf66ce73777eef5c05e03ee58f691d0ed776cc985941e` |
| `tests/r0007-recovery-precondition.test.cjs` | `12c9a8edca89b05483be7eee226456464112d05ec8ebd814fa391bcb7ecca361` |
| `tools/cp9/r0007_browser.py` | `ac626e916160ef1359bdddf022483ac5d0602626e29439253fd4ddb253c2a48e` |
| `tools/qualification/r0007_native.py` | `d57416ad259713887ecfe913eed1ed509abbe589ccfe4bd5fae2a4a3722c156e` |
| `tools/cp9/r0007_font_observer.js` | `ca8fcb547fca54e5edd8ba40c896497c6cda75b38acc7a6e4df276a2eeb21d1b` |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` |
| `tests/test_r0007_native_qualification.py` | `358cae9819d8ed140327439df28080c1bbeddd406db207b5527697b318543899` |
| `tests/real-sky/cp9_browser_runtime_test.py` | `c13f998a3996844028b5fc1ba84712bde2a40dd4e7893cc9001f584c37fcbb89` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |

The complete selected input manifest is `input-manifest.json`; local checkout identity, direct verification, commands/results and artifact hashes are retained alongside this report.

## Findings and handoff boundary

**New findings: none.** No new Finding Row is opened. QR-B20-01 and QR-B20-02 remain closed at the exact instrumentation scope established by the preceding own review. The additional A05 cell passes input qualification and selection coverage; its actual native result remains pending.

Actual font/event behavior, all-render and video evidence, independent original pixels, earliest eligible/visible recovery and the required Windows two-engine gate remain open. The inherited 250 ms recovery observation is eventual-state acquisition; the font/request deadline limitation is unchanged. A passing input binder or synthetic barrier test supplies neither first-frame acceptance nor a reason to relax these requirements.

Required merge order remains **R0017 → R0007 → R000B**. Preceding accepted-main reconciliation, exact owner head/base/tree approval and terminal delivery/certification/issue-closure gates remain binding. This PASS applies only to the committed input candidate named above and does not authorize native finalization, publication or integration.
