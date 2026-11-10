# F01 healthy full-model handoff — bounded repair handoff

## Status and authority

**Implementation and focused source/native Node verification are complete in this lane. Product source, the three affected test files, and the narrow policy update are write-frozen at the hashes below. F01 closure, browser qualification, generated qualification, integration and delivery remain with the root controller and independent review.**

The starting committed candidate was `9dabdcf338a7307c0256dcdccac48326b357f0d5`, tree `916d5d6ad09ae269095187a82b18c64b5684a79a`. Root selected the consumed-A remedy after reading [healthy-handoff-diagnosis.md](sandbox:/workspace/scratch/15b8fb6ac4c2/reviews/healthy-handoff-diagnosis.md), SHA-256 `f205cf2f16d769106ef83d2dff2a57ae8b3868ba74ec00fac9a6bf64461d78a7`, and separately authorized this engineering repair. The independent F01 input is [candidate-source-review.md](sandbox:/workspace/scratch/15b8fb6ac4c2/reviews/candidate-source-review.md), SHA-256 `c3c9181012079d9c70ac324679ccc0a6dbad2592a2a4390182570eb8b6fb2798`.

No integration source owner, shared extractor, generated output, browser harness, native driver/oracle, branch/ref or remote was changed in this lane. No build, browser, listener, provider request or install was run. The Node transport and DOM boundaries are contained doubles. This report does not assume root's concurrent work has passed its separate gates.

## Repair and owner boundaries

The only product change is in [src/native/index.html](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/src/native/index.html).

| Owner | Repaired behavior |
|---|---|
| `selectedWeather`, line 1301 | Accepts an optional admitted record, defaulting to the existing global current record. The unchanged live eligibility and explicit-preview target rules can therefore evaluate consumed A using A's own metadata. No temporary global record replacement or duplicated TTL rule is used. |
| Private `_cloudPublication`, line 2557 | Keeps the existing record/decision/receipt association and adds private scene and mode bindings. Public serializable receipts retain their existing fields. |
| `cloudAuthorityMode` / `cloudAuthorityMatches`, lines 2560–2572 | The one pure permit predicate first requires the active eligible publication, matching lane/target/scene/mode and available candidate. The existing exact-record path remains. A different real B record may retain real A only while each passes the existing per-record selector, actual `model()` is non-null, and any consumed direct evidence remains the same independently eligible evidence. |
| `publishCloudAuthority`, lines 2574–2579 | Associates a publication with its current scene and mode. Idempotent receipt reuse also checks those bindings. |
| Existing reconciliation/final consumers, lines 2609 and 2616 | Both consume the same predicate. Reconciliation can return the unchanged A receipt. The final check still separately requires exact identity with the currently active receipt. No integration-owner changes were needed. |

The handoff retains the same A receipt, original source/retrieval timestamps, coverage, readiness, density, backing raster and effect provenance. Candidate B remains unconsumed until ordinary full render applies B once with the existing easing gain. No producer, new clock, deadline, renewal, history cache or loop is introduced. The painter, cloud motion, acquisition, prayer admission and celestial mathematics are untouched.

### Permit limits

| State at consumer opportunity | Result |
|---|---|
| Active A, same selected record and target, no timetable | Existing warm exact-record retention remains. |
| Active A, healthy different B, complete actual model, matching target/lane/scene/mode, A and B independently current | Retain A's exact existing publication until ordinary full render consumes B. |
| A source or receipt age 900,001 ms, or either age -1 ms, with fresh B | Reject A using A's own age; reconciliation clears the joined state and raster. |
| A source or receipt age 899,999 or 900,000 ms, with the other A age valid and B fresh | Retain A under the inclusive existing live rule. |
| Different B with no genuine model | Withhold; fresh B cannot retain or restore A. |
| Cold or previously withdrawn consumer, even if weather and model have become available | Capture alone remains clear; genuine full render is required to restore a deck. |
| Genuine SIM or forecast record-object turnover | Use the existing preview rule; do not invent live validity/receipt metadata. Missing-model replacement still withholds. |
| Consumed direct-evidence lease expired or replaced by a different candidate evidence object | Refuse the handoff. A candidate's newer evidence cannot replace A's consumed lease. |
| B has completed full publication, or the active publication was superseded/withdrawn | An A callback fails exact active-receipt identity even if A itself remains otherwise eligible. |

This intentionally preserves conservative no-model replacement behavior. It does not make independent direct-observation claims, relabel model weather as observed, or broaden the existing preview contract.

## Evidence sequence and failure accounting

All evidence for this repair is under [healthy-handoff-repair](sandbox:/workspace/scratch/15b8fb6ac4c2/evidence/healthy-handoff-repair). Logs are retained without overwriting failed attempts.

| Evidence file | Actual result and interpretation |
|---|---|
| `f01-ordering-red.log` | Frozen 9dab source: two asserting ordering tests; capture-before-render fails the intended alpha assertion (0 versus 192), render-first passes. Actual prayer admission, actual fetch replacement and actual `NativeForegroundCapture` are prerequisites. No setup failures. |
| `native-original-premise-baseline.log` | Original native test file against frozen 9dab: 14/14 pass. This preserves the original oracle premises before their authorized adjustment. |
| `authoring-tool-syntax-refusal.txt` | A functions tool call containing an unescaped nested template literal was rejected by the JavaScript parser before any tool execution. No file write or test ran in that call. This is authoring failure evidence, not a product RED. |
| `handoff-expanded-frozen-red.log` | First expanded run: 12 pass, 15 fail. Three failures were missing `notify` on the fixture's optional renderer boundary during real clock control. Those three are setup failures and are not credited as product detections. |
| `handoff-corrected-frozen-red.log` | A local test-only optional notification sink corrected that boundary. Against the same frozen 9dab source: 14 pass, 13 intended healthy-retention assertions fail; no setup errors. Source remained unchanged at this point. |
| `handoff-first-repair-run.log` | First product repair: 27/27 focused controls pass. |
| `native-original-premise-after-repair.log` | Original native oracle file against repaired source: 11 pass, three old withdrawal expectations fail because they retained a complete model and eligible A. Root authorized making those negatives explicitly revoke the genuine model, while retaining final-fence, clear-successor and same-byte assertions. |
| `native-healthy-companions-frozen-red.log` | The three new healthy native companions against frozen 9dab all fail the intended retained-alpha assertion. They exercise refined, preview and same-byte reuse publication owners. |
| `affected-focused-run.log` | Repaired source and final affected Node tests: **147/147 pass**, no failures, cancellations or skips. |
| `f01-appendix-a-candidate.log` | Actual Appendix A scenario rerun with an explicit native-source digest rebind only; both event orders preserve normal final easing. The scenario body is unchanged. |

The only existing source-mutation discriminator adjustment is in [weather-withdrawal-mutations.test.cjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/weather-withdrawal-mutations.test.cjs): the old `weather` variable anchor and bypass became the corresponding `record` parameter anchor and bypass. The semantic fault remains expiry checked only at acquisition, and its existing actual-consumer assertion still detects it. The other six existing fault mutations and oracles are unchanged.

The authorized premise correction in [native-weather-withdrawal.test.mjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/real-sky/native-weather-withdrawal.test.mjs) is confined to `replaceDuringDetail` at line 45 and three added healthy companions at lines 96–108. The original two post-detail final-fence negatives and the same-byte reuse negative now explicitly set `today=null` after admitting B. Their final zero-alpha/clear-successor assertions are unchanged. The paired healthy cases keep the actual model, retain A's receipt and coverage, and the same-byte case publishes no extra draw.

## Focused coverage and commands

The new [weather-no-timetable-handoff.test.cjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/weather-no-timetable-handoff.test.cjs) contains 30 tests:

- The exact F01 capture-before-render ordering and render-first companion use genuine `adoptPrayerBundle`, real weather fetch admission and actual `NativeForegroundCapture`.
- Repeated captures and final-currentness reads are observed through wrappers forwarding to the real producers. Render, atmosphere, paint, cloud state application, painter, sync and acquisition call counts stay zero; coverage, raster, receipts, motion and effect provenance stay unchanged.
- Missing model, cold, already withdrawn, generation, coordinate, scene and native clock-mode controls preserve revocation and genuine full-render recovery.
- Each A source/receipt boundary is supplied as original record-admission metadata, independently of the other age. No retained A field is edited. B is separately admitted and fresh.
- Repeated B/C candidates leave A's receipt unchanged; A expiry is caught even while B/C's decision remains cached.
- Actual `startWeather(true)` SIM turnover and admitted hourly-track `syncWeather()` forecast turnover preserve preview semantics, with explicit assertions that no live timestamp/interval metadata has been fabricated. The optional background-renderer notification sink is contained locally in these tests.
- Consumed direct evidence has both unchanged-expired and replaced-with-newer-candidate negatives.
- Actual solar-mask decode callbacks may finish while A remains active, and fail after B publishes.
- Three targeted mutants remove the model guard, borrow B's eligibility for A, or drop exact active-receipt identity. Detection requires the named consumer assertion; setup assertions or runtime exceptions do not count.

The final affected command, run from `/workspace/scratch/15b8fb6ac4c2/r000b-work`, was:

```bash
node --test \
  tests/weather-no-timetable-handoff.test.cjs \
  tests/weather-no-timetable-withdrawal.test.cjs \
  tests/weather-withdrawal-authority.test.cjs \
  tests/weather-withdrawal-mutations.test.cjs \
  tests/real-sky/native-weather-withdrawal.test.mjs \
  tests/real-sky/native-host-composition.test.mjs \
  tests/real-sky/native-preview-host.test.mjs \
  tests/real-sky/native-solar-publication.test.mjs \
  tests/real-sky/native-composition.test.mjs
```

The 147 tests comprise 30 new F01 controls, 17 native weather-publication controls, 18 original no-timetable owner controls, six authority controls, seven original mutation controls and 69 native companions. This command does not use mutable shared generated output.

The preserved initial RED used:

```bash
SALAH_WITHDRAWAL_SOURCE=/workspace/scratch/15b8fb6ac4c2/evidence/healthy-handoff-repair/frozen-9dab-native.html \
  node --test tests/weather-no-timetable-handoff.test.cjs
```

The exact initial two-test bytes are preserved as `f01-ordering-red.test.cjs` (SHA-256 `e518bb2104e9016f6d814b72b4d82695c650806dd3ec958ea19bdc1371f3b8f7`), and the corrected 27-test RED version as `handoff-corrected-frozen-red.test.cjs` (SHA-256 `e124a9c9b56152bdd1f3366a7ea0dcbfb717144ea7c77630500036e0945df391`). Each was recovered by reversing only the later test additions and verified against the original logged byte hash before saving. Their relative fixture import retains the original repository test-file location contract. The current repository file contains later controls and mutation anchors. The frozen-source native healthy-companion check is reproducible with:

```bash
SALAH_WITHDRAWAL_SOURCE=/workspace/scratch/15b8fb6ac4c2/evidence/healthy-handoff-repair/frozen-9dab-native.html \
  node --test --test-name-pattern 'healthy post-detail replacement|healthy replacement without an extra draw' \
  tests/real-sky/native-weather-withdrawal.test.mjs
```

The Appendix A run used `node` with the recorded candidate script passed to stdin. Its reproducible shell form, from the repository cwd, is:

```bash
node < /workspace/scratch/15b8fb6ac4c2/evidence/healthy-handoff-repair/f01-appendix-a-candidate.cjs
```

The log's evidence-path annotation is shorthand for that stdin artifact. The original Appendix A script is retained alongside it. Only the expected digest for `src/native/index.html` was rebound to the repaired source; the other five declared inputs still require their 9dab committed bytes. The original script hash without terminal LF is `4b3b760329cd7bf58b7cb976e7c6c52f6f79e5a5bdd8665fd2f0b1e33e4d3b52`; the saved file with terminal LF is `9336ce5ba7c2aae15703c5f5cc6735f5e5c44b892919972f2866e8bcb1d1f9dc`. This newline distinction accounts for the different file hash and does not alter the scenario.

### Actual Appendix A outcome

| Order | Coverage at capture | Ready | Captured sentinel alpha | Coverage after ordinary render/painter |
|---|---|---|---:|---|
| Capture before render | `[0.92, 0.90, 0.60]` | true | 192 | `[0.9104, 0.888, 0.592]` |
| Render before capture | `[0.9104, 0.888, 0.592]` | true | 192 | `[0.9104, 0.888, 0.592]` |

A was independently eligible in the original F01 setup (source age 891,000 ms, receipt age 61,000 ms). The result is the original one-step 0.08 gain in both orders. The unchanged ADVANCING gain remains owned by `applyCloudState`. Population and phase invariants are asserted. Alpha here is a retained-raster sentinel in a source fixture; it is not browser pixel evidence.

## Frozen identities

These five files are the complete engineering write set for this repair:

| File under `r000b-work` | SHA-256 |
|---|---|
| `src/native/index.html` | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |
| `tests/weather-no-timetable-handoff.test.cjs` | `8f19ddb8e299f28ff1b76568fc67b68cf8bc58e431e04315e3a72c4319acc941` |
| `tests/real-sky/native-weather-withdrawal.test.mjs` | `446e36449e5fd1f2dabcace5093cba9c1b8dc6048a80ab6e6dbfc8ed835f90dc` |
| `tests/weather-withdrawal-mutations.test.cjs` | `b64a232d1f7c2944463ef497b2c4df440026ef213256ca2e752201f5d7e4e9b5` |
| `docs/state-contracts/R000B.md` | `d22e5122d32fb8eb7d64447f17e026b21e9efc24a41a9a6cfe00bb7f597e7704` |

The source fixture remains `a26b75bd596fc1cd9aff55ef3ee7c44defd4d3b848905bf04eeb309df6d0477f`. Integration owners remain:

| File | Unchanged SHA-256 |
|---|---|
| `real-sky/native-host-hooks.js` | `a4e6ff4505ac2f8fe3115be0e46f635bd879ae70667d0d1d049908a3c8bcacf2` |
| `real-sky/native-composition.mjs` | `d3e5d216cad8942e923c9418ed18458f8d8a6e719238c7001288c730323e4fb5` |
| `real-sky/native-host.mjs` | `b197152f1bd2c5d365d73312ad1e2fb3c4cdc797a621b525e8b8a88679fe8777` |
| `real-sky/native-preview-host.mjs` | `2d77893c59b5fd25fcbe5a647133e6a9e7aacd986f143666975e811d3412b3e8` |

Key immutable evidence hashes:

| Evidence | SHA-256 |
|---|---|
| Initial asserting F01 RED | `d3ded5614970b293343510cf47b6c589bf89992aca6a6fdc4abc5700095ee18a` |
| Corrected expanded frozen RED | `55a56b31bb1b1bd0e6ac3a9ac369f9bb5fae2a9536d6777ab507bb2b6e1f3310` |
| Native original-premise baseline | `1b3138ab488c45dadf7948c8cd2d9afe508ce277e3d44b80fbaf554d84c1b28d` |
| Native original-premise post-repair failures | `c13aaab4cf55bf709e3f24f113f4941d56828da8ee5bfe333367f11101f6231b` |
| Native healthy companions frozen RED | `1cfce795352d4f62a835ab1fe3ba4e591da2553d95c93847e79439ede94441c5` |
| Final 147-test affected run | `2a867eedf3693ea9d99ede7e12ce8ead198244dc9739ea30c38e8fa59c767e6e` |
| Actual Appendix A candidate output | `cf78e4369c4e462acaa9c29ab0324210f9b76f65d093871bbf4cea4869d24ad9` |

Existing repository edits used the installed mutation-window helper with absent-to-present anchors. The new test was initially created with apply_patch; its later edits also used the helper. External evidence/report writes used the separately authorized scratch paths. Final `git diff --check` is clean. No commit was made by this lane.

## Remaining evidence obligations

Root may now rebuild from the frozen product source and requalify generated consumers against the explicit rebuilt identity. Any generated prerequisite rebind remains root-owned. The report does not carry forward pre-repair generated or browser results as qualification of the new product bytes.

Independent review must reassess the narrow permit and exact source/input binding, including own-record age, genuine model availability, preview object turnover, evidence expiry, scene/mode invalidation and active-receipt callback rejection. Native browser evidence must still establish visible continuity and withdrawal using the independently reviewed harness/driver, including the healthy capture/render order where applicable. Source sentinel and command-raster evidence cannot replace that pixel evidence.

The existing exact-record warm no-model rule remains the selected policy; the repair only supplies the bounded healthy complete-model replacement handoff. It does not claim broader direct-evidence recordless handoff, change preview validity rules, or settle unrelated Moon/prayer/science exceptions. Any contrary native evidence or independent source finding requires a newly authorized countermeasure and fresh source freeze. F01 and R000B acceptance/closure remain unclaimed.

