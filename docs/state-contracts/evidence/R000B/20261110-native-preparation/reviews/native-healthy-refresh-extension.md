# R000B healthy full-model refresh acquisition extension

**Report state: FINAL — bounded driver/oracle extension and pure verification complete; final bytes write-frozen for independent delta review. No native run, pixel result or product qualification is claimed.**

## Scope and frozen identities

Root separately authorized this acquisition extension after accepting the HN1–HN4 preparation. The accepted v2 fixture, driver and oracle test were preserved in `/workspace/scratch/15b8fb6ac4c2/evidence/native-harness-v2/`; its manifest binds the prior independent review SHA `241d33b91c6db32c7991de184975e08731393127a9ebf1cb5018c688648529ab`. This lane verified all three archived hashes before using them as the comparison baseline.

Only the two authorized repository files were changed. Both mutations used prepared scripts and the installed mutation-window wrapper. The fixture, synthetic inputs, clocks, existing HN1–HN4 predicates, original 30-second recovered watch and 240-second fixture limit remain unchanged. No product, Moon, generated, shared-helper, build, install, browser, listener, worker, ref or remote effect occurred in this lane. No process remains running.

Paths below are relative to `/workspace/scratch/15b8fb6ac4c2/r000b-work`.

| File | Final SHA-256 | Disposition |
|---|---|---|
| `tools/qa/run_r000b_withdrawal.py` | `9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e` | Extended; write-frozen |
| `tests/weather-no-timetable-native-oracles.test.py` | `36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209` | 15 focused controls added; write-frozen |
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` | Accepted v2 bytes unchanged |

## Required acquisition and deliberate interval choice

The candidate withdrawal branch now requires a real weather-record replacement after the full `recovered` capture establishes an available prayer model. The existing uninterrupted 30-second watch runs first, unchanged. If `recovered` and `recovered-30s` already bracket the required consumed replacement and full foreground publication, those actual captures and request records are reused.

Otherwise the driver polls only the existing passive fixture report, using native `performance.now()` for remaining budget. When it observes a newer eligible candidate, it takes an ordinary existing `read()` snapshot and retains it through the unchanged `capture()` path. It can retain an A-owned handoff snapshot while B is still only a candidate; that snapshot cannot complete selection. It continues bounded one-second waits until a full B publication qualifies or the remaining budget is exhausted. It never calls a product producer, capture, reconciliation, currentness, acquisition or painter helper and never changes capture ordering.

The fixture cap stays 240,000 ms. New acquisition stops at 235,000 ms, leaving 5,000 ms of headroom for final artifact reads and completion. The actual cap is checked against the unchanged fixture declaration. Failure to observe a qualifying refresh is a failure; an empty or unavailable state cannot count. The baseline-defect branch retains its earlier exit path and does not run this extension.

**The pre-capture remains `recovered`, including when extra waiting is needed.** Root explicitly accepted this stricter choice after reviewing the actual branch. It covers the complete healthy watch plus any extra wait, rather than dropping the first 30 seconds when rebasing to `recovered-30s`. All retained interval samples must belong to the exact endpoint A/B record identities and immutable receipts. A third candidate or consumed record is rejected, not silently omitted. This can conservatively fail a campaign containing an additional record; it cannot pass by hiding that earlier interval. This is a bound on retained evidence, not a claim that an unobserved transition between sampling opportunities is impossible.

## What constitutes an actual replacement

`healthy_refresh_record()` identifies a full capture only when the actual raw record, candidate, native consumed publication and target agree, with an available model, a selected current record and the live model-estimated-rain lane. `healthy_refresh_pair()` then requires strictly newer source and retrieval times and a newer publication revision, with the same target and lane.

Both endpoint records must bind to exactly one actual synthetic response in the existing request ledger. The check parses the response's own civil source time using the declared UTC+03:00 offset; a candidate timestamp cannot substitute for that body value. It requires status 200, exactly one JSON read, a settled `json-consumed` result, real operation/attempt ownership in the current generation, and a retrieval time after JSON completion and before the owned attempt deadline. The new request must start after the recovered capture, have distinct operation/attempt identities, a later ordinal, and at least the ordinary 60-second request spacing from the request that supplied A.

The paired full captures require nonempty native raster and consumed mask, existing rain-origin evidence, independent celestial output, and matching native/visible-foreground authority. The final B record must actually be consumed by every displayed foreground layer. A fresh raw/candidate timestamp with an old native or foreground A receipt is not a successful final pair.

The receipt records both actual record identities and both consumed request summaries. New artifacts are `healthy-refresh-evidence.json` and `healthy-refresh-passive.json`, alongside the existing numbered full snapshots, PNGs, card/viewport captures and original continuous video. The original runtime/source/harness manifest and private-ingress gates remain in force.

## Whole retained interval checks and the A-to-B handoff

`healthy_refresh_evidence()` checks every retained passive sample and every retained full snapshot in the inclusive interval from `recovered` to the final selected capture. Full snapshots sharing an endpoint timestamp are still checked. It also uses the unchanged signed phase/life/wander/population oracle over the combined chronological samples; clean endpoints cannot erase an intervening reset.

The intermediate candidate may be B while the active native or foreground receipt is still A. The check deliberately does **not** require candidate/consumed timestamp equality at every sample. A must retain its exact original receipt, including source, retrieval, target and lane, and remain within its own inclusive 900,000 ms source and retrieval ages. The allowed immutable receipts are A and selected B. Renewal, withdrawal, changed target/lane, an expired A lease, a third record, or a consumed B-to-A rollback fails.

Every passive sample checks the actual null-model flag, active lease, cloud readiness, expected live coverage, displayed foreground/mask presence, and precipitation state. Every retained full snapshot additionally checks native raster alpha, density, targets, independently decoded mask alpha, displayed canvas material, captured foreground cloud alpha and the unchanged rain-origin predicate. Full intermediate diagnostic status may be pending while healthy A is still displayed; the paired endpoints must have completed ordinary independent celestial publication.

**Sampling and alpha limit:** the frozen passive fixture schema has no raster bytes at each timer tick. Actual raster/mask/foreground alpha is checked on every retained full snapshot, while passive observations check their own available readiness, coverage and mask-presence fields. The evidence records the largest passive observation gap. The original continuous clip remains required to review intervening appearance. This native acquisition will qualify an actually observed ordinary healthy refresh; it does not force or prove the exact F01 capture-before-render ordering. That exact ordering belongs to the separate deterministic source test. Neither source qualification nor a native outcome is claimed here.

## Verification and controls

**Final repository suite: 35/35, exit 0.** The 20 accepted HN1–HN4 tests are unchanged; 15 extension tests add positive and negative controls against the actual driver functions extracted by AST. No driver module import/main, product body, browser or listener is executed by those tests.

| Controls | Observed pure result |
|---|---|
| Actual refresh inside the original watch; later ordinary refresh; default/full/reduced modes | Accepted |
| B candidate while immutable eligible A remains active, including a pending diagnostic label | Accepted |
| No new record after recovery; request begun before recovery | Rejected |
| Source-preserving timestamp renewal; unread/unsettled response; missing/reused ownership; expired attempt | Rejected |
| Body source time substituted by candidate timestamp; native A or foreground A at final B endpoint | Rejected |
| Null model, withdrawn/not-ready/zero-coverage deck, missing displayed foreground or mask in an intermediate passive sample | Rejected |
| Empty native raster, mask, captured foreground alpha or failed rain-origin evidence in an intermediate full snapshot | Rejected |
| Intermediate phase, life, wander or population reset despite clean endpoints | Rejected using unchanged v2 motion oracle |
| A lease renewal/expiry, changed target/lane, B-to-A rollback, missing passive interval | Rejected |
| Contradictory retained full snapshot at an endpoint timestamp | Rejected |

Static verification compared all 23 existing v2 top-level functions other than `main`, including the accepted HN1–HN4 predicates, and all four existing test classes by AST: unchanged. The complete original recovered-watch block is byte-preserved, including its single `page.wait_for_timeout(30000)`. Existing read constants and fixed input constants are unchanged. The fixture SHA verifies unchanged synthetic inputs, clock and cap. Python AST/whitespace checks and the scoped `git diff --check` passed. The new passive progress expression was extracted without evaluation and passed Node syntax checking; no JavaScript body was executed.

One initial scratch verifier run exited 1 because it expected the deadline literal to occur once, although it occurs in both the receipt and progress message. Only that scratch verification assertion was corrected. Its failure log is retained. Prepared final verification and the canonical repository run then passed 35/35. No native/product failure is inferred from that scratch-check error.

## Actual commands, receipts and retained evidence

Evidence is under `/workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/`. `evidence-index.json` binds the final report, frozen identities, prepared script/fragments, syntax/preservation logs and test results. `final-freeze.json` records the final repository hashes and unchanged v2 baseline. The independent delta reviewer should use the frozen repository files, with the archived v2 files as the comparison base.

The two authorized existing-file mutations both returned exit 0 and `anchor=absent-to-present` at then-current head `9dabdcf338a7307c0256dcdccac48326b357f0d5`:

```bash
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tools/qa/run_r000b_withdrawal.py --expect 'anchor:R000B_F01_HEALTHY_REFRESH_EXTENSION_V1' -- python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/apply_extension.py driver > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/driver-mutation-window.log 2>&1
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tests/weather-no-timetable-native-oracles.test.py --expect 'anchor:R000B_F01_HEALTHY_REFRESH_ORACLE_CONTROLS_V1' -- python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/apply_extension.py tests > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/tests-mutation-window.log 2>&1
```

The driver moved from `73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc` to `9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e`; tests moved from `3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82` to `36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209`. No post-window repository edit was made.

Final verification invocations, all exit 0:

```bash
PYTHONDONTWRITEBYTECODE=1 python tests/weather-no-timetable-native-oracles.test.py -v > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/native-oracles-final.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/verify_extension.py --static-only > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/static-preservation-final.log 2>&1
git diff --check -- tools/qa/run_r000b_withdrawal.py tests/weather-no-timetable-native-oracles.test.py > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/diff-check-final.log 2>&1
node --check /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/healthy-refresh-progress.js > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-extension/progress-expression-syntax.log 2>&1
```

## Handoff

The two final repository files are write-frozen. Root owns the independent delta review, final product/build binding, new expected manifests and isolated hosted acquisition. Its separately reported F01 source/build checkpoint is not qualified by this harness work. The candidate successful status remains only `PASS_ASSERTIONS_PENDING_PIXEL_REVIEW`; the baseline status remains separate. No native outcome, acceptance, readiness, integration or issue closure is conferred by this report.
