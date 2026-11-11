# R000B native observer interface repair

**Report state: FINAL — HR1/HR2 implementation and bounded verification complete; repaired repository bytes write-frozen for independent closure review. No native result or product acceptance is claimed.**

## Authority, preserved failure and scope

This lane initially inspected repository files read-only, as dispatched. Root subsequently released the two-file correction after reading the complete independent v3 FINAL GAP report, SHA-256 `000756008c67be0595ec914a7ded40a1934d7f08b2e3a6a1e1964d64ffa53dce`. The original v3 findings remain preserved against driver `9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e` and tests `36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209`. Root retains o21 and all qualification/acquisition/closure authority.

Only `tools/qa/run_r000b_withdrawal.py` and `tests/weather-no-timetable-native-oracles.test.py` were mutated, each through the installed mutation-window wrapper with a previously prepared script. The fixture and all product/source/generated files remain unchanged. No browser, listener, provider request, product producer, build, install, ref or remote effect occurred. All commands completed; this lane leaves no running process.

The source-interface evidence includes a contained Node evaluation of the exact **pure** `captureWeatherTarget` constructor and the receipt-projection/deadline expressions under declared inputs. It does not invoke `publishCloudAuthority`, `beginAttempt`, product bootstrap, an acquisition owner or any native producer. No full product runtime or browser body was executed.

## Final frozen identities

Paths are relative to `/workspace/scratch/15b8fb6ac4c2/r000b-work`.

| File | SHA-256 | Disposition |
|---|---|---|
| `tools/qa/run_r000b_withdrawal.py` | `1eeb84e2800231ef74349af2152be5b85df807232403199afa3566e804edfb2c` | HR1/HR2 repair; write-frozen |
| `tests/weather-no-timetable-native-oracles.test.py` | `25ee18492a84ca4646d7695b26d81799afe56ba059ddfed3901707f3351af3d4` | Realistic factory and 12 interface tests; write-frozen |
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` | Accepted fixture unchanged |
| `src/native/index.html` | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` | Product interface source unchanged |

`protected-inputs.json` binds the unchanged fixture, five authored product owners and four generated files. Both v2 and v3 archived fixture/driver/test sets were checked against their preserved manifests. No post-window repository edit was made.

## Decisive original failures, retained before mutation

`preserve_old_controls.py` first verified that both live repository files and their v3 archive still held the original hashes. It then loaded only the actual archived pure predicates and called their **original signatures**. No new context argument was passed to an old function, and no missing new helper or `TypeError` was accepted as a finding. The original invented v3 factory still returned true, establishing a live positive control.

| Control | Actual frozen-v3 behavior | Corrected counterpart |
|---|---|---|
| HR1: snapshot/raw target contains the actual ten fields; receipt contains only generation/lat/lon | `healthy_refresh_record()` returns `None`; actual full-sample predicate returns false | Record selection and full-sample check both return true |
| HR2, with compact targets solely to isolate the clock: origin 125.25 ms, JSON at 180130.25 native ms, receipt interval `[180135.25,180136.25)`, deadline 190125.25 native ms | Record selects, but original three-argument request matcher returns `None`; pair fails | Request matches in the native clock domain |
| Both actual interface shapes together | Full verdict false | Same retained case qualifies under the corrected actual predicates with its observed origin supplied |

The HR2 epoch receipt is `1788901370010`; comparing that value directly to `190125.25` was the defect. The retained source-interface output also establishes the actual weather attempt budget as 10,000 ms. The previous test factory's epoch-shaped 12,000 ms deadline was not a faithful product observation.

Primary preserved evidence:

- `old-v3-discriminators.json` — SHA-256 `aa56aeef2f27fa56aa36c8f8c35193cc8308eacb012624f1a4036a36a0a8af51`; actual old signatures completed without `TypeError`.
- `old-v3-realistic-case.json` — complete retained production-shaped synthetic counterpart used by the new predicates.
- `source-interface-shapes.json` — SHA-256 `723e13b3207ab946912385f3ae20f935080c0ae9e532352ed8843b9edf13d619`; exact source fragment hashes and contained outputs.
- `independent-v3-counterexamples-preserved.json` — copied original independent discriminators, unchanged.
- `repair-discriminators-repository.json` — final actual driver/test hashes and old-fail/new-pass comparison.

These are bounded source-interface/pure controls, not native observations or pixel proof.

## HR1 correction: compare the owned identity projection

`captureWeatherTarget` retains generation, latitude, longitude and seven provenance fields. The cloud publication intentionally projects its public target to generation/latitude/longitude. The adapter now expresses that projection explicitly through `_healthy_refresh_target_projection()`.

Endpoint selection requires the compact publication target to equal the projection of the full snapshot target. It separately requires **deep equality of the complete raw target and snapshot target**, including their provenance. Runtime/request generation checks remain. The full-sample path now applies these same checks instead of comparing the rich raw target directly to the compact receipt. Endpoint A/B target consistency, immutable receipt membership, lane checks and retained interval checks remain intact.

The corrected factory uses the ten-field target and three-field receipt actually returned by the inspected source expressions. Controls independently reject generation/latitude/longitude drift in snapshot, raw and receipt identities; runtime/request generation drift; and provenance disagreement between raw and snapshot targets. The repair does not discard target checks or collapse all target schemas into one invented dictionary.

## HR2 correction: observed origins and a bounded receipt interval

The unchanged fixture already exposes `started` in the native performance clock and `startUtc` in the epoch clock. The driver now carries those values as `clockOrigin` through its existing passive progress read, acquisition receipt, pair selection and final evidence. It verifies that the origin remains identical across progress reads and the final fixture record. No origin is added to or manufactured by the fixture.

For each endpoint used to bind a request, `_healthy_refresh_clock()` checks the observed origin against the already retained native motion observation:

```text
motion.lastRt - motion.elapsedRtMs = observed started
```

The equality permits `1e-7` ms for floating-point representation only. Missing/nonfinite origins, wrong performance origin, inconsistent native motion, an incorrect fixed-case epoch, or invalid observed capture time fail closed. The default missing context is refusal, never an assumed zero origin. Several distinct nonzero origins are exercised by the tests.

Let `S` be observed `started`, `U` observed `startUtc`, `J` the fixture's actual JSON elapsed time, `R` the admitted integer epoch receipt and `D` the native attempt deadline. The matcher uses:

```text
JSON native time = S + J
receipt native time lies in [S + (R - U), S + (R - U) + 1)
```

It subtracts the integer epoch values before adding the fractional native origin, avoiding needless loss of precision. JSON completion must be strictly before `D`, and the **entire receipt interval's upper edge must also be strictly before `D`**. Epoch comparisons remain separate: the actual request wall time, JSON-derived epoch lower bound, admitted receipt and observed capture wall time must be chronologically consistent.

The request's deadline must also be plausible in the native domain: it follows the observed request performance time and is no more than the source's 10,000 ms weather budget after it, with only `1e-7` ms representation allowance. `beginAttempt` precedes the fixture request, so the deadline can be closer. This rejects an epoch-shaped deadline rather than accepting an enormous unrelated value as a distant monotonic deadline. Neither numerical allowance extends the strict body/receipt deadline comparisons.

**Deliberate conservatism:** `R` identifies a one-millisecond interval, not an exact native receipt instant. An interval touching or straddling the deadline is refused, including exact upper-edge contact. A legitimate receipt in the final millisecond before the deadline can therefore be refused by this instrument. That is an explicit evidence limitation, not a product timeout claim. The matched-request evidence records the origin, JSON native time, receipt interval, deadline and remaining margin.

The existing source-body time parsing, interval 900, exactly one settled JSON read, distinct operation/attempt ownership, generation, ordinal, ordinary 60-second request spacing and consumed native/foreground record binding remain required. Ambiguous matching responses still fail.

## Verification and preservation

**Final canonical repository suite: 47/47, exit 0.** This comprises the original 20 HN1–HN4 tests, the 15 meaningful healthy-refresh tests with faithful target/clock data and necessary context adapters, and 12 new interface tests.

The new controls cover rich/compact target compatibility; coordinate and generation drift; full raw/snapshot provenance equality; absent/wrong clock origins; nonzero performance origins; binding to native motion; epoch-shaped deadlines; JSON completion at/after deadline; safe and boundary/straddling receipt intervals; ambiguous responses; fractional epoch receipts; and source/receipt substitution. Existing unconsumed-response, timestamp-renewal, clearing, model-null, lease, rollback and motion-reset controls remain exercised. The independent v3 third-record discriminator is preserved separately. Boundary matcher probes keep raw/candidate/publication receipt fields consistent with the tested receipt interval.

Static/source checks confirmed:

- All 23 prior v2 top-level functions outside `main`, including HN1–HN4 predicates, are unchanged in both AST and source text.
- All four accepted HN1–HN4 test classes are unchanged in AST and source text.
- The prior 15 healthy-refresh test assertions are preserved after accounting only for the explicit clock-context arguments and correction of the expired-attempt control into the native domain.
- The original uninterrupted 30-second recovered-watch block is byte-preserved. The fixture cap remains 240,000 ms and additional-acquisition cutoff remains 235,000 ms.
- The fixture, authored product and generated protected hashes did not change.
- Python parsing/whitespace checks, scoped `git diff --check`, and the updated passive progress expression's Node syntax check passed.

The final actual predicates also accepted the preserved realistic old-failure counterpart; this comparison was rerun against the repository bytes after the mutation windows. No setup error was counted as a discriminator. Prepared and final checks completed without a failed verification invocation in this repair lane.

## Commands and retained receipts

All repair evidence is under `/workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/`. `evidence-index.json` binds the report, final freeze, protected inputs, old/new controls, preparation scripts, exact delta artifacts and logs.

Before mutation, both commands returned exit 0:

```bash
node /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/derive-interfaces.js > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/source-interface-shapes.json
PYTHONDONTWRITEBYTECODE=1 python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/preserve_old_controls.py > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/old-v3-discriminators.log 2>&1
```

Both authorized mutations returned exit 0 with `anchor=absent-to-present` and exact before/after hashes at head `136f21b1697a5e1e9d9f453464c8250fb9f3e540`:

```bash
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tools/qa/run_r000b_withdrawal.py --expect 'anchor:R000B_HR1_HR2_INTERFACE_REPAIR_V1' -- python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/apply_interface_repair.py driver > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/driver-mutation-window.log 2>&1
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tests/weather-no-timetable-native-oracles.test.py --expect 'anchor:R000B_HR1_HR2_INTERFACE_CONTROLS_V1' -- python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/apply_interface_repair.py tests > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/tests-mutation-window.log 2>&1
```

Final verification commands, all exit 0:

```bash
PYTHONDONTWRITEBYTECODE=1 python tests/weather-no-timetable-native-oracles.test.py -v > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/native-oracles-final.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/verify_interface_repair.py --static-only > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/static-preservation-final.log 2>&1
git diff --check -- tools/qa/run_r000b_withdrawal.py tests/weather-no-timetable-native-oracles.test.py > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/diff-check-final.log 2>&1
node --check /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/progress-expression-repository.js > /workspace/scratch/15b8fb6ac4c2/evidence/native-healthy-refresh-interface-repair/progress-syntax-final.log 2>&1
```

## Remaining boundaries and handoff

The stricter recovered-through-watch-and-wait interval is unchanged: every retained healthy interval sample is checked, and a third record is conservatively rejected. Passive samples still lack per-tick raster bytes; all retained full snapshots check actual alpha, while the original continuous clip remains required for intervening appearance. An ordinary acquired refresh will not prove forced F01 capture-before-render ordering. Handled Moon worker diagnostics remain uninspected under HN1's accepted boundary. No pixel or native result has been acquired.

The repaired driver and tests are write-frozen. Root owns rebinding the expected manifests, independent HR1/HR2 closure review and any later isolated hosted acquisition. Successful candidate assertion status remains `PASS_ASSERTIONS_PENDING_PIXEL_REVIEW`; the separate baseline-defect status is unchanged. This report does not confer native acceptance, product readiness, integration, issue closure or authority to close o21.
