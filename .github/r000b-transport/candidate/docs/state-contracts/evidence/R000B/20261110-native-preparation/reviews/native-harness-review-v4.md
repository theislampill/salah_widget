# R000B HR1/HR2 independent closure review

**FINAL PASS — bounded instrument repair review only.** HR1 and HR2 are verified repaired in the exact freeze below. Root retains readiness, acquisition, acceptance and formal finding/issue closure authority. The original v3 FINAL GAP remains immutable; this result does not rewrite its evidence or qualify native/product output.

## Frozen identities

Paths are relative to `/workspace/scratch/15b8fb6ac4c2/r000b-work`.

| Input | SHA256 |
|---|---|
| `tools/qa/run_r000b_withdrawal.py` | `1eeb84e2800231ef74349af2152be5b85df807232403199afa3566e804edfb2c` |
| `tests/weather-no-timetable-native-oracles.test.py` | `25ee18492a84ca4646d7695b26d81799afe56ba059ddfed3901707f3351af3d4` |
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` |
| `src/native/index.html` | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |

Live bytes matched before testing and at final attestation. The fixture and product source remain unchanged. Root-supplied HEAD/tree are context; this reviewer performed no ref/index operation.

## Finding dispositions

The complete original finding rows remain in `reviews/native-harness-review-v3.md`, SHA256 `000756008c67be0595ec914a7ded40a1934d7f08b2e3a6a1e1964d64ffa53dce`.

| Finding field | HR1 — target representations | HR2 — deadline clock domains |
|---|---|---|
| Status / category | Verified repaired; instrument API correctness. | Verified repaired; instrument timing correctness. |
| Evidence | Driver `_healthy_refresh_target_projection` at 497, endpoint at 526 and full sample at 618 match source `captureWeatherTarget`, `admitWeatherRecord` and `publishCloudAuthority`. | Driver clock binding at 504, request matcher at 549 and acquisition origin at 1113 match source `_RAFNOW`/`beginAttempt` and unchanged fixture origins. |
| Impact | Genuine ten-field targets now qualify against three-field receipts. | Genuine consumed responses now qualify using their native deadline. |
| Fix / implementation route | Project finite generation/latitude/longitude; separately retain full raw/snapshot provenance equality and runtime/request generation checks. | Carry observed performance/epoch origins; derive the entire integer receipt interval; require body completion and interval upper edge strictly before deadline. |
| Acceptance criteria | Actual schemas pass; identity and provenance disagreement reject. Met. | Nonzero origins pass; absent/inconsistent origins, wrong-domain deadlines and late/ambiguous evidence reject. Met. |
| Verification | Independent C1: old record/full predicates reject; repaired predicates accept. Drift negatives reject. | C2/C4/C5: old matcher rejects valid native timing; repaired matcher accepts. Wrong-domain and boundary negatives reject. |
| Risk / remaining risk | Real native observations remain unperformed; interface changes require rebinding. | A legitimate receipt in the last millisecond can be conservatively refused; no native timing claim. |

For **both rows**: repair class is **instrument/acceptance defect**; owner/source is the driver and focused tests, with product interfaces unchanged; effort was a bounded two-file correction; confidence is **HIGH**. Route is **dispatch-review** to root. Neither finding is rejected or deferred. Rollback/plan closure preserves the original v3 freeze and counterexamples; root decides formal closure and any later acquisition. No product rollback is implied.

## Independent verification

Evidence resides in `/workspace/scratch/15b8fb6ac4c2/evidence/native-harness-review-v4/`. The command was `python -B` on `closure-controls.py` there. It compiled Python without importing/executing driver main, ran only `HealthyRefreshTests` and `HealthyRefreshInterfaceTests`, and loaded actual archived/current pure predicates through AST.

**27 focused tests passed; 16 independent probe records matched their declared results.** Raw output is `focused-tests.log`; discriminators are in `independent-controls.json`. No exception or `TypeError` received failure credit: archived predicates were called with their original signatures.

The independent controls extracted target keys, receipt projection, the 10000 ms request budget and fixture epoch from actual source text; no JavaScript/product function was executed. They use nonzero fractional origins and a request deadline beginning 0.375 ms before interception. With origin 3701.3125, JSON completion is 183706.4375 and receipt interval `[183711.3125,183712.3125)` precedes deadline 193700.9375. Old matching returns None; repaired matching and full evidence pass. Reduced/full companions also pass. An epoch-shaped deadline accepted by old v3 is rejected by the repair.

Safe complete intervals pass. Fractional deadline straddles, exact upper-edge contact, and body completion at/after deadline reject. The `1e-7` ms allowances concern origin equality and budget plausibility; neither extends the strict body/receipt deadline comparisons.

## Propagation, preservation and read confirmation

Complete actual driver/test diffs were read. The progress expression reads existing `started`/`startUtc`; both pair-selection paths and final evidence receive that same observed origin. Acquisition and final fixture checks reject origin changes. These are passive reads and host-side checks, without new producers.

AST and source comparisons confirm all **23 prior pure functions**, all **four HN1–HN4 classes**, and the original **30-second watch** unchanged. Fixture cap 240000 ms and acquisition deadline 235000 ms remain intact. `preservation-and-propagation.json` records the actual call sites; prior campaigns were not rerun.

Read scope comprised current/archived driver and tests, relevant unchanged fixture clock/ledger/motion/target fields, and source target/admission/deadline/publication interfaces. The author report was read only after FINAL, as supporting evidence. `final-attestation.json` records exact read extents and final hashes; `artifact-manifest.json` binds this report and evidence. Original v3 report and archives remain unchanged.

Only this report and its designated evidence directory were written. No repository mutation, browser/listener, build, provider request, product producer execution, install, ref/index/remote operation or secret reproduction occurred. M2 manifest routing, source-stage binding, hosted acquisition, continuous video, pixel judgment, product qualification and acceptance remain separate root-owned gates.
