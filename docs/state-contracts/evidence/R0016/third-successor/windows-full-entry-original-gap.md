# Retained Windows full-entry proposal — GAP / bounded correction required

Reviewed exact retained proposal **38860 bytes / SHA-256 f1a98a4e2f46b379d739cb25e6f16dc655c8c2eb4f7b3a26b49abf15542410d4** against the current six helper/held/probe/guard/window inputs. The proposal's duplicate in recovered T0006 is byte-identical. Current copied APIs also match independently received immutable published bytes at 0a7cd429. Full identities are in `input-hashes.json` and `provenance-and-paths.json`.

This is a new bounded review, not restoration of the missing original full-entry review. The supplied original review directory is absent. Historical held cleanup adverse `65952b699485bc91981a222b81a9b9a3b378226425638b806e9a34255c149fa6` is retained as history; the current held helper already contains its correction. No source-free qualification or product native credit follows from this report. No installer, PowerShell, native child, archived main or shared-source edit ran in this lane.

## Actionable findings

### FE1 — Actual source-entry input relation is not received

Current composition support `4600bac1…` prepares a complete six-role clone and requires `before.rows == heldPreparedRows` in `validate_held`. The direct/held native input probes are generated but never consumed by the product receiver: direct `control/module-inputs.json`, held module proof, and `held-before-inputs.json` do not participate in the full-entry relation. Probe source bytes are checked, which is a different fact from comparing the actual child observations.

A narrow original native witness grounds the boundary problem. From **failed source-free run43140174110 / PS7**, six exact original files were received from frozen repair packet `3276ed32…`; every hash matches its manifest. They show prepared==prelaunch; **six prepared-to-before changes** (profile root mtime, four new profile directories, subject/temp mtime); **before==after** across the held source invocation; then two additional after-to-postexit changes. This record lacks the separate original Utility ready/ACK and remains a diagnostic FAIL. It is evidence that startup and invocation windows differ, not a qualified driver or product result.

**Bounded correction:** keep complete prepared-clone custody and consume the existing actual native input proofs for the direct/held source-entry relation. Bind PID/nonce/phase, source, native host, environment, command/provider identities and source-bound read outcomes under the declared root mapping. Keep all lifecycle snapshots; do not equate unrelated startup changes with source effects, remove fields, or admit by simply dropping the current equality check. The raw witness and exact differences are in `native-relation-evidence/` and `native-source-entry-relation.json`.

### FE2 — Direct-helper cleanup can lose the final receipt and primary error

The current coverage helper `52a268b0…`, `invoke_with_profile_boundary`, still runs `process.kill()` directly in its exception handler and `process.wait(timeout=10)` in finally. A failure in either can skip the receipt-writing code after the capture context. The corrected held `finish_owned_acquisition` does not cover this direct path.

The exact selected direct function was exercised with inert process/clock/native-snapshot boundaries:

| Witness | Observed result |
|---|---|
| Healthy terminal | Exit0, ready true, receipt saved |
| Snapshot refusal + successful cleanup | Original OSError preserved, receipt saved |
| Same refusal + exit race at kill | ProcessLookupError replaces primary error; wait observes exit0; final profile-window receipt absent |
| Same refusal + denied kill + wait timeout | TimeoutExpired replaces primary error; fake terminal remains unknown; final receipt absent |

All raw fake stdout/stderr files remain; no real Popen occurred. **Bounded correction:** independently attempt owned termination, wait, captures, observation and receipt persistence, preserving the primary error and explicitly refusing unknown termination. Do not label this as an unfixed held-helper issue. Exact witness source/output: `inert_direct_witnesses.py`, `inert-direct-results.json`.

### FE3 — Late first terminal observation bypasses the declared direct deadline

The same direct helper tests the timeout only inside `while process.poll() is None`. When poll first returns a terminal code after the deadline, the loop exits before the time check. The outer full-entry proposal does not subsequently admit a bounded terminal-observation clock.

The exact-function inert witness returns **exit0, ready true, elapsedSeconds61.25, error null** for a 60-second deadline. Its healthy 1-second counterpart passes. This is a receiving/control-flow counterexample, not a claim that a native run actually timed out.

**Bounded correction:** record and validate the first observed terminal time against the existing deadline; preserve late-terminal failure and its raw captures/cleanup. This does not request a larger deadline or new host-wide telemetry. The same five-row witness file covers FE2 and FE3.

### FE4 — Normal confinement ignores an unexpected file in the retained subject facts

The proposal computes `snapshotUnchanged` and complete `fullInputsBefore/After`, but normal/NoOpen admission does not inspect them. It validates USERPROFILE's eight retained entries and checks absence of `SalahWidgetAttempt-*`; an unexpected differently named file under subject/temp is outside those predicates.

The exact pure `require_positive_confinement` plus exact `assert_profile_window` were exercised on explicitly inert data:

| Input | Admission |
|---|---|
| Healthy exact eight-entry profile bundle | Accepted |
| Extra file outside the profile bundle | Rejected |
| Same healthy profile, but subject/temp/unexpected.bin added and snapshotUnchanged=false | **Accepted** |

The full-entry normal branch has no additional subject-state comparison that closes this gap. **Bounded correction:** use the already-retained subject/private-temp facts to require the declared normal postcondition and reject unexpected remnants, while retaining any explicitly accounted temporary-parent metadata changes. Preserve the eight-entry profile inventory and all existing normal effects/output assertions. This requires no new global observation surface. Witnesses are `pure_receiver_witnesses.py` and `pure-receiver-results.json`.

## Preserved controls and non-findings

The original **20 scenario identities** remain exact: 18 paired preview cases plus positive and NoOpen. Pure exact-exit verification admitted all18 declared success/failure values and rejected five malformed/wrong typed cases (Boolean, float, string, held Boolean and contradictory explicit exit). Normal direct exit also requires integer zero. These checks are retained; they are not candidates for relaxation.

Current helper signatures and held/probe fields are compatible at the call boundary. The review does not assign API-drift failure or revive the corrected held cleanup finding. Source-free native qualification remains a prerequisite to product credit.

**MAX_PATH remains conditional, not a proved failure here.** The retained preset layout adds177 UTF-16 units to the temporary parent. Two explicit static examples total216 and231 units, so they do not establish a native path failure. Keep the actual carrier parent short and bound its complete constructed paths when composing it; no source path-policy change is justified by this review alone.

## Delivery boundary

Findings and witnesses were sent to windows_recovery for the root-authorized bounded correction. All original scenario/assertion coverage, typed exits, complete input facts and prior failures must remain. Any common-helper change has a new byte identity and must be reflected in source-free custody pins and qualification composition before native product credit. Root retains publication, native execution and final review authority.

No broad redesign, expanded hosted diagnostic campaign, or new whole-host requirement is proposed. The receipt and witness scripts ended terminal0; no active native process or shared mutation exists in this lane.
