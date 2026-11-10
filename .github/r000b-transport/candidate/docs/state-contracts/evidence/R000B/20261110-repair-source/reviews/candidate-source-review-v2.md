# R000B F01 repaired-source review

Report state: FINAL

**Bounded verdict: PASS for the F01 source/code remedy at `136f21b1697a5e1e9d9f453464c8250fb9f3e540`. No additional confirmed defect was found in this repair scope. Actual native qualification, generated-fixture o18 disposition, whole-candidate acceptance and formal occurrence closure remain separate GAPs for this reviewer.**

The independently rerun original scenario now retains eligible consumed A through capture-before-render, then takes the ordinary single 0.08 easing step when full render consumes B. The render-before-capture control reaches the same coverage. The repair does not let fresh B renew A's source or receipt age, bypass genuine model availability, revive a cold/withdrawn publication, or publish a superseded A callback.

This is an informational independent review for the root IMPLEMENTAUDIT governor. It recommends acceptance of the **bounded F01 source repair evidence**; it does not close o15, approve a public candidate, transfer old native approval, authorize integration, or waive the preceding R0017 corrective → R0007 acceptance requirement. The original FINAL BLOCKED [candidate-source-review.md](sandbox:/workspace/scratch/15b8fb6ac4c2/reviews/candidate-source-review.md) is preserved byte-for-byte at SHA-256 `c3c9181012079d9c70ac324679ccc0a6dbad2592a2a4390182570eb8b6fb2798`.

## Frozen scope and identity

| Identity | Exact value |
|---|---|
| Engineering baseline | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Baseline tree | `6b94a3933f9d1381b1c2ceaab287c93afb215ecb` |
| Repair parent / original F01 target | `9dabdcf338a7307c0256dcdccac48326b357f0d5` |
| Parent tree | `916d5d6ad09ae269095187a82b18c64b5684a79a` |
| Reviewed repair commit | `136f21b1697a5e1e9d9f453464c8250fb9f3e540` |
| Reviewed repair tree | `917ed30e193cb8c4caed36fece0a98a1a75c0326` |
| Repository | `/workspace/scratch/15b8fb6ac4c2/r000b-work` |
| Node runtime used | `v24.22.1` |

The committed parent-to-repair range contains exactly eight paths. Product inspection used exact `git show`/`git diff` commit inputs. Before executing source probes, I compared the working bytes of these eight paths and 143 fixture/integration/dependency paths with the reviewed commit. All 151 matched. I rechecked all 151 after the runs; all remained unchanged. The complete inventory is [preflight.json](sandbox:/workspace/scratch/15b8fb6ac4c2/evidence/candidate-source-review-v2/preflight.json). Hashing a dependency is an input-binding check, not a claim that every dependency received new semantic review.

| Committed path | SHA-256 |
|---|---|
| `src/native/index.html` | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |
| `index.html` | `604eddd742ea2818520d51d9b16da102e9375e6a88f6b1a2cce4ec8dbf7dbb92` |
| `offline.html` | `03b4ca62b94173a70c9d60c7db51a1b309f8eff4e5ae6d410e67d96ea2d0d29f` |
| `moon/BUILD.json` | `921a9097191c986951f625ec9ace73a785a786f87658319eb927c112fabb4d6e` |
| `docs/state-contracts/R000B.md` | `d22e5122d32fb8eb7d64447f17e026b21e9efc24a41a9a6cfe00bb7f597e7704` |
| `tests/weather-no-timetable-handoff.test.cjs` | `8f19ddb8e299f28ff1b76568fc67b68cf8bc58e431e04315e3a72c4319acc941` |
| `tests/real-sky/native-weather-withdrawal.test.mjs` | `446e36449e5fd1f2dabcace5093cba9c1b8dc6048a80ab6e6dbfc8ed835f90dc` |
| `tests/weather-withdrawal-mutations.test.cjs` | `b64a232d1f7c2944463ef497b2c4df440026ef213256ca2e752201f5d7e4e9b5` |

The reviewer binding is to this commit and these bytes, even if root subsequently commits disjoint fixture/docs/harness work. A later envelope needs root's explicit equality check for this write-frozen set plus qualification of its additional changes.

## Correctness / Bugs

### F01 disposition: repaired in the reviewed source scope

The previous predicate treated any selected record replacement as revocation, including a healthy full-model refresh. An independent capture could therefore clear A before ordinary full render consumed B. Clearing `_cloudReady` turned the next expected easing update into a first-deck snap. The original report demonstrated this with genuine weather and prayer ingress, a separately eligible A, and capture-before-render versus render-before-capture controls.

The repair changes only the per-record selector and the private publication permit/association in [src/native/index.html](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/src/native/index.html). The substantive checks are:

| Owner / location at reviewed commit | Independent assessment |
|---|---|
| `selectedWeather`, line 1301 | The optional record parameter defaults to the existing global record. The live path still delegates to unchanged `weatherEligibility(record, now)`; the preview path retains its existing target rule. A can now be evaluated without swapping the global selected weather or copying B's metadata. |
| `cloudAuthorityMatches`, line 2561 | A different-record handoff requires an already eligible publication, an available candidate, matching lane/target generation/scene/mode, separately selectable A and B, and the actual `model()` result. This is a bounded exception to exact-record equality, not a blanket bypass. |
| A's own lease | The handoff invokes `selectedWeather(now, p.record)` independently of the selected B decision. A's expiry is therefore detected even while B/C's decision remains cached. The existing inclusive 0–900000 ms source and receipt limits and zero future allowance are not rewritten. |
| Genuine model availability | `model()` is the actual prayer-model function, checking admitted day, timezone, generation, finite time and timings. Its body is unchanged and does not invoke render, weather acquisition, painter or an astronomy producer. The handoff does not manufacture prayer data or treat selected weather as evidence of a timetable. |
| Consumed direct evidence | In the different-record branch, any direct evidence used by A must remain the identical evidence object in the candidate decision and must independently pass `weatherFixtureEligibility` at current time. Candidate renewal cannot substitute a new lease for A. Recordless evidence is not granted a new different-record handoff. |
| Scene/mode publication binding | The private association records `skySceneIdentity()` and the current SIM/ADVANCING/clock-preview mode tuple. Both are checked by the permit and by receipt reuse. Scene resets still withdraw through `beginSkyScene`; same-coordinate new generations cannot reuse the previous generation. |
| `reconcileCloudPublication`, line 2609 | Reconciliation returns the original A receipt when the permit holds. It does not publish B, invoke a producer, or perform another easing step. If it fails, the existing joined state/raster/effect withdrawal remains in force. |
| `cloudPublicationCurrent`, line 2616 | The final read still first requires exact identity with the currently active receipt. A callback cannot become valid merely because its old weather remains eligible after B has published. The same permit is shared with reconciliation. |
| `applyCloudState`, line 3089 | Unchanged from the parent. Only ordinary complete render consumes B, with the previous snap/ease rules. Motion advancement, coverage gain, population, phases, life/wander, wind integration, weather cache/admission and existing loops are unchanged by the repair. |

The old exact-record warm no-timetable policy remains. A no-model replacement, cold consumer, or already withdrawn consumer cannot gain a deck from capture alone. In the bounded tests, a later genuine complete render can restore a deck through its existing owner. Genuine SIM and forecast object turnover keeps its separate preview contract, with no fabricated live source/receipt/interval fields.

The integration files are byte-identical to the parent. I reread the relevant capture, pending-decode, post-detail, same-byte reuse and failure-retention guards. They still call the shared authority predicate and preserve the separate astronomical job/scene fences. The change therefore benefits the existing capture and final-publication consumers without adding another producer loop or altering Moon composition code.

### Original F01 ordering reproduced independently

I reconstructed Appendix A from my original FINAL report, checked that the entire scenario body was unchanged, and rebound only the expected native-source digest plus its assertion label. The other five declared inputs still require their original 9dab committed bytes. The independently reconstructed script was also byte-identical to the supplied author rerun script. My run produced new raw output, not a copied author result.

The clock at replacement/capture was `1788901251000` (2026-09-08 21:00:51 UTC; next local day in Asia/Riyadh). Both records had target generation 0, latitude 24.47, longitude 39.61, weather code 95 and total cloud 95. A's current-valid time was `1788900360000`, its original retrieval time `1788901190000`, and its layers `[0.92,0.90,0.60]`. Thus A's source age was 891000 ms and its receipt age 61000 ms. Actual contained `fetchWeather()` admitted a distinct B with current-valid time `1788901200000`, retrieval time `1788901251000`, and layers `[0.80,0.75,0.50]`.

The setup explicitly admitted the synthetic next-day bundle through actual `adoptPrayerBundle(__fixtureNextPrayer, "09-09-2026", null, true, false)` before the refresh. `model()` and selected B were both true before capture. This matters: a pending next-day provider alone would not establish the healthy full-model premise.

| Event order | State entering the capture opportunity | Capture/reconcile result | After the ordinary full render and painter |
|---|---|---|---|
| Capture before render | A coverage/targets `[0.92,0.90,0.60]`, ready true, active A receipt revision 2, retained raster fills 182 | Same A receipt and state; captured sentinel alpha 192; B remains unconsumed | Coverage `[0.9104,0.888,0.592]`, B targets `[0.80,0.75,0.50]`, ready true, B receipt revision 3 |
| Render before capture | The control first performs ordinary render, producing eased coverage `[0.9104,0.888,0.592]` and B receipt revision 3 | Capture does not clear or take an extra easing step; sentinel alpha 192 | Same eased coverage and B receipt revision 3 |

Population stayed `11.432099999998172`; phase stayed `[0,0,0]` in both orderings. No withdrawn receipt was inserted during the healthy gap. The log's field named `preCapture` is collected before the optional control render; `afterCapture` shows the post-control state. The committed two-order test additionally collects its pre-capture state after the optional render and asserts that capture leaves it unchanged.

The canvas readback is an explicit retained-raster sentinel. It establishes that reconciliation did not empty the backing raster. It does not establish browser cloud shape, opacity, color, continuous native motion, or that a not-yet-repainted raster already reflects the new numerical easing state. Those remain native evidence questions.

## Finding Row Contract

| Field | F01 / root occurrence o15 |
|---|---|
| Finding title | Healthy selected-record replacement cleared consumed clouds before ordinary full render, breaking easing |
| Category / severity | Correctness / Bugs; original P2 regression; source repair independently verified at 136f21b |
| Path / function | `src/native/index.html`: `selectedWeather`, private `_cloudPublication`, `cloudAuthorityMatches`, `publishCloudAuthority`; existing reconciliation/final-publication consumers |
| Evidence | Original FINAL report and exact Appendix A; fresh independent rebound output; 30 new handoff controls plus unchanged no-model/authority/mutation controls and 17 native publication boundary controls; committed hashes in this report |
| Impact | Original interposed capture cleared coverage/readiness/raster and made the next render snap B. Reviewed repair preserves A only within its own active authority and restores the ordinary single easing step. Native visible behavior is not inferred from sentinel values. |
| Effort | Narrow implemented source change plus focused tests/docs; no additional repair requested by this review |
| Risk | Overbroad retention could lend B's freshness/model state to A or admit obsolete callbacks. Independent own-age, missing-model, cold/withdrawn, scene/mode/target and active-receipt controls address the reviewed source risk. |
| Confidence | High for the bounded source ordering and guarded handoff; no native pixel confidence is claimed |
| Fix sketch / implementation route | Root-selected consumed-A retention: reuse existing per-record eligibility, keep A's original receipt, require genuine model and unchanged consumed context, let ordinary complete render consume B |
| Repair class | product-or-skill defect |
| Owner/source | Native cloud publication owner; root/owner retain occurrence, integration and acceptance authority |
| Acceptance criteria | Both original orders preserve ordinary easing; A cannot borrow B's age/evidence; model loss and cold/withdrawn states refuse handoff; scene/mode/target changes revoke; a superseded A decode fails exact active receipt identity; no new producer/easing/reseed side effect |
| Verification | Independent original scenario exit 0; focused 78/78 pass with 0 skips/TODOs; changed code and test assertions read; source/generated delta parity and exact committed input hashes verified |
| Rollback / Plan Closure | No rollback performed or authorized. Original failure and failed attempts remain preserved. Root may reconcile the source occurrence using this evidence; whole-candidate closure still requires its separate gates. Reverting to the parent would restore the demonstrated original ordering regression. |
| Rejected/deferred rationale | The finding is not rejected. Its repaired-source disposition is separated from formal root closure and native qualification. |
| Remaining risk | Browser-visible continuity/withdrawal, actual host scheduling/raster composition, o18 fixture qualification, public envelope and whole-ledger acceptance are not established here. |
| Route | reconcile |

**Additional confirmed findings: none in the bounded repair scope.** This is not a census claim about the whole application.

### Dismissed observation: three previous native negative expectations changed

The original 14-test native suite passed on 9dab, then three post-detail/same-byte withdrawal expectations failed against the repaired source while their actual model remained available. That is visible in the retained before/after logs. The corrected tests make the negative premise explicit by setting `today=null` after admitting B and asserting the actual model is absent. Their zero-alpha/clear-successor assertions remain. Three healthy companions keep the actual model, require retained A authority/coverage, and retain the same-byte no-extra-draw assertion. Those healthy companions fail against frozen 9dab and pass in my independent repaired-source run.

I therefore do not classify this as an oracle weakened to hide F01. The original failure remains reproducible, both permitted and forbidden cases are represented, and model availability is asserted rather than inferred. This judgment would be falsified by a purported no-model negative that still had an available actual model, by removal of the final-sink assertions, or by a healthy companion passing against the faulty parent at the intended consumer assertion.

## Tests / Validation

### Fresh independent execution

All execution was bounded Node with contained VM/time/transport/canvas boundaries. No browser, network/provider call, build, server/listener, install, ref or repository mutation was performed. The two source-override environment variables `SALAH_WITHDRAWAL_SOURCE` and `SALAH_WITHDRAWAL_NATIVE_ROOT` were unset. The source fixture was bound to committed authored source and the integration modules to the same checkpoint.

1. Reconstructed original Appendix A: exit 0, both orderings inspected as above.
2. Focused affected suites: **78 tests, 78 pass, 0 fail, 0 cancelled, 0 skipped, 0 TODO**. Counts: 30 handoff, 18 no-timetable, six authority, seven original fault mutants, 17 native weather/publication boundaries.
3. Static identity/parity checks: all eight hashes verified; all 151 frozen path/input hashes equal before/after; exact repair delta identical in authored, root and offline runtime text; only one Moon build metadata field changed; unchanged native-sky bundle; `git diff --check` exit 0.

The focused command, from the repository cwd, was:

```bash
node --test \
  tests/weather-no-timetable-handoff.test.cjs \
  tests/weather-no-timetable-withdrawal.test.cjs \
  tests/weather-withdrawal-authority.test.cjs \
  tests/weather-withdrawal-mutations.test.cjs \
  tests/real-sky/native-weather-withdrawal.test.mjs
```

The new tests actually assert A's independent source and receipt ages at 899999, 900000, 900001 and -1 ms with fresh B; successor B/C does not extend A even with cached candidate decisions; eight captures and final checks call no wrapped producer and do not change state/effect provenance; actual SIM and forecast record turnover; genuine model loss; cold and withdrawn refusal; generation/coordinates/scene/mode revocation; direct-evidence expiry/replacement; and actual delayed solar decode completion before versus after B publication. Three new in-memory mutants are detected at named consumer assertions: absent model guard, borrowed B age and missing active-receipt identity. The seven original faults remain independently exercised; only the selected-weather mutation anchor changed from the global variable to the new record parameter.

The retained original authority tests also exercise an actual A→B→A generation cycle with late settlement and actual units reconfiguration at unchanged coordinates. The source tests observe numerical coverage, target/readiness/density state, receipt identity, effects, raster commands/sentinels, producer calls and motion invariants. They do not simulate native pixel quality.

### Actual supplied evidence inspected

I read the author handoff as claims, then checked the relevant source, assertions, raw logs and hashes. The source conclusion rests on the independent reruns and code, not on the author's conclusion.

| Supplied evidence | Actual inspected result / use |
|---|---|
| `f01-ordering-red.log` | Frozen 9dab: capture-first fails alpha 0 versus 192; render-first passes; 1/2 pass. This matches the original F01. |
| `handoff-expanded-frozen-red.log` | 12/27 pass, 15 fail, including three `notify is not a function` setup errors. Those setup errors are not credited as fault detection. |
| `handoff-corrected-frozen-red.log` | 14/27 pass, 13 assertion failures against frozen 9dab after the local notification-boundary correction; no TypeError/ReferenceError/SyntaxError in the inspected log. |
| `native-original-premise-baseline.log` | 14/14 pass on original source and original premises. |
| `native-original-premise-after-repair.log` | 11/14 pass; three retained-alpha versus zero expectations fail under the still-healthy premise. Preserved and explained above. |
| `native-healthy-companions-frozen-red.log` | All three new healthy companions fail their intended retained-alpha assertions against frozen 9dab. |
| `affected-focused-run.log` | Author's affected source run: 147/147 pass. |
| `root-focused-after-build2.log` | Root's separate 147/147 pass, source/test hashes recorded; SHA-256 `4461e48cb77d42c6b296ebc3f37cceb4d313dfd42691d6af45cee8acd5c88433`. I did not label it as my execution. |
| `build-2/build-receipt.json`, actual build/V1/protected logs | Recorded build, V1 and protected-diff exits are 0; actual build/V1 log hashes match the receipt. Generated output hashes match committed 136f21b bytes. I did not run the builder. |

The repair adds/deletes the same 31 diff lines in `src/native/index.html`, `index.html` and `offline.html`. `real-sky/native-sky.js` remains SHA-256 `426754834c6c116c4521ad5067bb1e37a9845830fc07ebbb62dd22fcdc757d66`. The sole changed JSON value in `moon/BUILD.json` is `/source/src/native/index.html`; Moon source/assets and its execution behavior were not modified by this repair. These are source/output identity checks, not replacement for generated cohorts or native review.

### Reviewer artifacts and hashes

All reviewer evidence is under [candidate-source-review-v2](sandbox:/workspace/scratch/15b8fb6ac4c2/evidence/candidate-source-review-v2).

| Artifact | SHA-256 |
|---|---|
| `preflight.json` | `41551d722192cee8ff990e3d41eb0127cf08a9efcb0ad1ee8ece28289f229f16` |
| `appendix-a-rebound.cjs` | `06eaf47bf364b0f576ffdca6750e5fe7b5bbf25060b9a7ff851dc4d1b02c7607` |
| `appendix-a-rebound.log` | `ab5b738306bd5bca1d1ef6394d9a416c4d1be90184d9a4e9b60069c2206b11a6` |
| `appendix-a-run.json` | `13cb292befd16e12148971d36a012980537c5d99a2f40f13789ccb58ff06cccf` |
| `focused-78.log` | `f2c674e5a96a4c4cb2c962ba0e2f08c9df2b601c40024ab0d74cf6ef6e822e3d` |
| `focused-78-run.json` | `f7dd096a8bed909976668ac508334c31392943e589f032ad93f4c720ab54ef6d` |
| `static-parity.json` | `1bc22c66b5dde046a2588cd322a5e81afdfadf88768e1f6243876b4485dbcd94` |

[verification-receipt.json](sandbox:/workspace/scratch/15b8fb6ac4c2/evidence/candidate-source-review-v2/verification-receipt.json) records the post-run input check, unchanged original report, unchanged authoritative repo documents/integration sources and hashes of every supplied evidence file used. It also records the exact author report hash `0e983d9e8c9fa86a93f9819b06f092bfd2a23577b9b82c957facbe98f7151d34` and checkpoint manifest hash `746b3e0c87241fd404698b0c8e58ef479da7c3131ece2348449ed9438391fb1b`.

## Docs / Handoff

The revised [R000B contract](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/docs/state-contracts/R000B.md) explicitly distinguishes healthy full-model handoff from exact-record warm retention without a timetable, states own-record source/receipt custody, preview semantics and active-receipt final fencing, and names the focused tests. Its source-evidence versus browser-evidence boundary is appropriate. The root canonical build happened after the author report's source freeze; the actual build receipt and committed hashes supply that later output binding.

### Declined-to-judge behavior and reason

| Behavior / gate | Status for this review and reason |
|---|---|
| Native visible cloud continuity, shape, occlusion, pixels and healthy acquisition/capture scheduling | GAP. No native browser was acquired or executed here. The alpha sentinel and retained fill count cannot establish those properties. |
| Full ES0B native expiry/no-model matrix, real hidden/sleep resume, real transport and compositor timing | GAP. Only contained source boundary execution was authorized in this lane. Existing required native proof is not waived. |
| Generated R0025 continuity/lifecycle and native-head o18 fixture repair | Outside this frozen source closure. Root reported a separate authorized fixture lane; I neither ran nor accepted its later changes/results. Root must bind its own report and qualification. |
| Broad new scientific/Moon correctness or arbitrary direct-evidence redesign | Outside the narrow repair. Existing integration/science guards were checked for preservation; unrelated science or new recordless handoff was not requalified. |
| Public candidate identity, remote readback, whole-ledger reconciliation, acceptance and integration | GAP / root-owned. This is a local exact-commit source review. No remote operation or acceptance action occurred. |
| Prior native approval of changed host/painter joins | Not transferable. This source repair report supplies no native acceptance and carries no earlier pixel approval forward. |
| Preceding R0017 corrective → R0007 acceptance | Still required before R000B integration; this reviewer has no authority to waive it. |

### Actual read set

**Fresh semantic/code inspection in this resumed lane:** exact repair commit/tree/parent and complete eight-path delta; authored native selector, eligibility, evidence reconciliation, decision cache, real `model()`, scene identity/reset, cloud publication/reconciliation/final guard and application/motion context; full new handoff test; full native weather boundary test; full original authority and mutation tests; unchanged authored fixture; revised R000B policy diff; build-native transformation boundary; relevant unchanged native host hooks, refined and preview publication/pending/failure/reuse guards; Moon build metadata delta and source/root/offline delta equality. The broader integration and source owners were also available from my original independent review, not supplied authoring context.

**Prior authoritative read set retained from the original review:** committed `AGENTS.md`, `docs/real-sky/INTEGRATION.md`, `docs/moon/QUALIFICATION.md`, `docs/state-contracts/R000B_IMPLEMENTATION_PLAN.md` and original `R000B.md`; the actual common execution contract at `/workspace/scratch/15b8fb6ac4c2/execution_packet/contracts/COMMON_EXECUTION_CONTRACT.md`; intake `issue11.md`, entire ES0B amendment `comment-6700189703.md`, original B matrix `comment-6073038339.md`, corrected historical certificate `comment-6178186713.md` and independent acceptance `comment-6178296345.md`. The unchanged repo documents were rechecked byte-for-byte against the repair parent. Historical acceptance defines carried scope, not current native approval.

**Evidence actually read or mechanically inspected now:** my original FINAL report and Appendix A; supplied `healthy-handoff-repair.md`; `committed-checkpoint.json`; original and rebound probe text comparison; the raw red/green evidence listed above; actual build-2 input/complete receipts and build/V1/protected logs; my new raw run logs and source/input/parity receipts. I read the installed audit playbook's `## Finding Row Contract` for report structure. Dependency inventories in the hash manifests are explicitly hash-only where not named in the semantic read set. I did not read a separate reviewer's new opinion or the separate o18 repair report.

### Explicit reviewer attestation

I wrote only this designated v2 report and files inside the designated reviewer evidence directory. I did not change repository/product/test/docs/index/HEAD/refs, run builds, use a browser/listener, acquire a real provider, contact a remote, or publish anything. No internal audit-child authority was assumed. The original FINAL report was not overwritten. The reviewed commit and all stated changed-file hashes were verified from committed objects; all 151 frozen path/input bindings were checked before and after bounded runs. Parent/root retains lifecycle and release decisions.

The source review is complete. The appropriate next join is root's source-occurrence reconciliation plus its separately qualified fixture/native/public-candidate evidence; this report alone supplies no whole-candidate acceptance.

## Appendix A — Exact original-scenario reproduction

The complete executable script, including synthetic admitted next-day prayer fixture use and contained weather transport setup, is preserved as [appendix-a-rebound.cjs](sandbox:/workspace/scratch/15b8fb6ac4c2/evidence/candidate-source-review-v2/appendix-a-rebound.cjs). The untouched original is in Appendix A of the original FINAL report. Only the expected digest for `src/native/index.html` and its preflight assertion label were changed; the remaining five frozen-input checks and entire scenario body are identical. The script hash is listed above.

Run from `/workspace/scratch/15b8fb6ac4c2/r000b-work` using stdin so the original relative imports retain their repository-cwd resolution:

```bash
node < /workspace/scratch/15b8fb6ac4c2/evidence/candidate-source-review-v2/appendix-a-rebound.cjs
```

The fixture's actual ingress and consumer sequence is: contained initial Open-Meteo current record A → advance controlled wall time → actual next-day `adoptPrayerBundle` → normal `render`/painter establishing the healthy premise → actual contained `fetchWeather` replacement B → optional control `render` → actual `NativeForegroundCapture.capture`, which calls native reconciliation → ordinary `render` if capture was first → painter. The report's raw log preserves A/B source and receipt times, target, actual model availability, pre-control snapshot, after-capture state and final coverage for both orders.
