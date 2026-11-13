# Post-RLGWO audit: corrective work-order portfolio

This index links the completed audit ([README](README.md), [FINDINGS](FINDINGS.md), [REPORT](REPORT.md),
[CROSSWALK](CROSSWALK.md), [GDOPL assessment](GDOPL_ASSESSMENT.md)) and the registry
([IMPLICIT_STATES.md](../../../IMPLICIT_STATES.md)) to the Research-Lab-Grade Work-Orders (RLGWOs) filed from it
under a separate owner commission. The audit documents are unchanged; where a work order corrects an audit
statement, the correction is in the work order and summarised in [section 6](#6-corrections-to-audit-statements-found-while-drafting).

**Status.** Filed on 2026-11-12 against main `5b84647686c28a3ce557fba2c2e6a801d0c0cb73`. All eighteen issues are
**open**. Filing authorises nothing further: implementation, merge to `main` (which deploys), delivery
verification and closure of each work order need a separate owner execution commission. Nothing here was
implemented, and no acceptance row in any issue has been executed unless the issue says it was run while drafting.

## 1. Filed work orders

| RLGWO | Issue | Title | Findings | Owner decision gates (defaults are in the issue) |
|---|---|---|---|---|
| R0028 | [89](https://github.com/theislampill/salah_widget/issues/89) | Regression-instrument truth: repair red instruments, declare expected failures, coherent closure record | F-06, F-27, F-35 | DG-1, DG-2; discriminator G-12 |
| R0029 | [90](https://github.com/theislampill/salah_widget/issues/90) | Generator output atomicity and fail-loud guards | F-19 | DG-1 |
| R002A | [91](https://github.com/theislampill/salah_widget/issues/91) | Qualification gate on main/PRs and post-merge delivery identity | F-09, F-28 | DG-1…DG-4 |
| R002B | [92](https://github.com/theislampill/salah_widget/issues/92) | Pages payload: measured deployed bytes and retained-evidence policy | F-07 | DG-1, DG-2 |
| R002C | [93](https://github.com/theislampill/salah_widget/issues/93) | Prayer publication independent of optional astronomy: render-loop liveness and exception containment | F-01 | G-C1 |
| R002D | [94](https://github.com/theislampill/salah_widget/issues/94) | Timezone authority: hint admission and recovery, zone adoption without scene rebuild, preview-clock anchor | F-02, F-08, F-14 | G-D1, G-D2 |
| R002E | [95](https://github.com/theislampill/salah_widget/issues/95) | Prayer presentation residual state: stale-marker reachability, rollover mirror flags, countdown fit key and status-text ownership | F-21, F-23 | G-E1…G-E3 |
| R002F | [96](https://github.com/theislampill/salah_widget/issues/96) | Weather authority renewal and cloud continuity across the freshness boundary | F-03, F-24, F-25, F-32 | D-2F-1…5, D-2F-6 (conditional), D-2F-7 |
| R0030 | [97](https://github.com/theislampill/salah_widget/issues/97) | Settings Reset authority, dirty-close commit and apply-failure handling | F-04, F-20, F-33 | G1, G1a, G1b, G2…G5 |
| R0031 | [98](https://github.com/theislampill/salah_widget/issues/98) | External location-response admission residuals: builder reverse geocode, permission-query bound, place-class field | F-05, F-29, F-30 | D-31-1…4 |
| R0032 | [99](https://github.com/theislampill/salah_widget/issues/99) | Location-derived data retention and third-party acquisition minimisation | F-16, F-17 | D-32-1…3 |
| R0033 | [100](https://github.com/theislampill/salah_widget/issues/100) | Moon failure recovery, fault-path presence and light eligibility | F-12, F-13, F-26, F-31 | DG-1…DG-5 |
| R0034 | [101](https://github.com/theislampill/salah_widget/issues/101) | Refined-sky identity, preview-mode status truth and preview-host lifecycle | F-10, F-22, F-34, F-36, F-37 | G1…G4 |
| R0035 | [102](https://github.com/theislampill/salah_widget/issues/102) | Star scintillation: reconcile the shipped renderer with gate I, DESIGN.md and motion telemetry | F-11 | D1, D1-b |
| R0036 | [103](https://github.com/theislampill/salah_widget/issues/103) | Diagnostic purity, truthful outcome records and visible provenance of diagnostic overrides | F-15, F-38 | G1, G2 |
| R0037 | [104](https://github.com/theislampill/salah_widget/issues/104) | Frozen V1: truthful limitation record, a meaningful `--check-pages`, and a 325×530 V1 embed snippet | F-18 | DG1…DG3 |
| R0038 | [105](https://github.com/theislampill/salah_widget/issues/105) | Verification census for implicit / unverified real-sky and Moon worker machines | — (registry gaps) | none |
| R0039 | [106](https://github.com/theislampill/salah_widget/issues/106) | Installer residuals: correct the registry's macOS record, bound the public preview claim to its evidence, complete release-asset selection, and decide the PowerShell/transport correction tranche | — (registry gaps) | DG-I1, DG-I2 |

Identifiers are repository-local hexadecimal RLGWO IDs continuing after R0027; they do not coincide with GitHub
issue numbers. No earlier work order (R0001–R0027, issues 1–37, 68, 69) was reopened, widened or revoked.

## 2. Finding dispositions (38 of 38)

Each finding has exactly one owning work order. Evidence classes are the audit's unless the disposition says the
work order states new evidence. "Discriminator-gated" means stage 1 is an experiment whose outcome decides whether
any remediation follows, with a defined "no defect established" exit.

| Finding | Audit evidence class | Work order | Disposition |
|---|---|---|---|
| [PRA-F-01](FINDINGS.md#pra-f-01) | demonstrated - injected fault (dependency); trigger speculative | [R002C](https://github.com/theislampill/salah_widget/issues/93) | corrective (hard-constraint enforcement) + decision gate G-C1; natural-trigger search kept as a claim-affecting row; class preserved |
| [PRA-F-02](FINDINGS.md#pra-f-02) | demonstrated | [R002D](https://github.com/theislampill/salah_widget/issues/94) | corrective |
| [PRA-F-03](FINDINGS.md#pra-f-03) | demonstrated - model-parameterised; deck snap plausible | [R002F](https://github.com/theislampill/salah_widget/issues/96) | discriminator-gated (stage-1 native measurement) + decision gate D-2F-1 (default B) + mandatory DESIGN correction |
| [PRA-F-04](FINDINGS.md#pra-f-04) | demonstrated (VM) | [R0030](https://github.com/theislampill/salah_widget/issues/97) | corrective + gates G1/G1a/G2; class strengthened to VM with real applyConfig/persistence (probe stated) |
| [PRA-F-05](FINDINGS.md#pra-f-05) | demonstrated (VM) | [R0031](https://github.com/theislampill/salah_widget/issues/98) | corrective + gates D-31-1/D-31-2 |
| [PRA-F-06](FINDINGS.md#pra-f-06) | demonstrated | [R0028](https://github.com/theislampill/salah_widget/issues/89) | corrective (repair regressed harnesses) + expected-failure ledger; origins refined with evidence; preview-lightning docs-contract case now dispositioned as a stale instrument expectation (src:"sim" policy at index.html L1708-1714), confirmed by G-12; product conflict, if any, routed to R002F D-2F-6 |
| [PRA-F-07](FINDINGS.md#pra-f-07) | demonstrated (estimate) | [R002B](https://github.com/theislampill/salah_widget/issues/92) | measurement-first + decision gates DG-1/DG-2; class strengthened to 'measured lower bound' from artifact metadata (inference stated) |
| [PRA-F-08](FINDINGS.md#pra-f-08) | demonstrated (source + probe); visual unobserved | [R002D](https://github.com/theislampill/salah_widget/issues/94) | corrective + gate G-D1 |
| [PRA-F-09](FINDINGS.md#pra-f-09) | demonstrated | [R002A](https://github.com/theislampill/salah_widget/issues/91) | corrective (new gate) + DG-1..DG-3 |
| [PRA-F-10](FINDINGS.md#pra-f-10) | demonstrated - model-parameterised | [R0034](https://github.com/theislampill/salah_widget/issues/101) | corrective + gate G1; scope refined (rate>0 incl. timeScale=1) |
| [PRA-F-11](FINDINGS.md#pra-f-11) | demonstrated | [R0035](https://github.com/theislampill/salah_widget/issues/102) | decision gate D1 between (i) feature and (ii) truth correction (default ii) + D1-b |
| [PRA-F-12](FINDINGS.md#pra-f-12) | demonstrated; EF-E10/E11 plausible | [R0033](https://github.com/theislampill/salah_widget/issues/100) | corrective + DG-2/DG-3; EF-E11 discriminator |
| [PRA-F-13](FINDINGS.md#pra-f-13) | demonstrated (injected, native); EF-E05 plausible | [R0033](https://github.com/theislampill/salah_widget/issues/100) | corrective + decision gate DG-1 (GDOPL I-14 incomparable; default B) |
| [PRA-F-14](FINDINGS.md#pra-f-14) | demonstrated | [R002D](https://github.com/theislampill/salah_widget/issues/94) | corrective |
| [PRA-F-15](FINDINGS.md#pra-f-15) | demonstrated (a-e) | [R0036](https://github.com/theislampill/salah_widget/issues/103) | corrective (a,b,d,e); (c) owned by R0036: retain production capture-time reconcile, document, pin with regression test (IR-2) |
| [PRA-F-16](FINDINGS.md#pra-f-16) | demonstrated (consumers) / plausible (host) | [R0032](https://github.com/theislampill/salah_widget/issues/99) | decision gate D-32-1 (default A off-by-default + opt-in + allowlist) |
| [PRA-F-17](FINDINGS.md#pra-f-17) | demonstrated; quota coupling speculative | [R0032](https://github.com/theislampill/salah_widget/issues/99) | corrective (siteElev) + decision gates D-32-2/D-32-3; quota a measurement item |
| [PRA-F-18](FINDINGS.md#pra-f-18) | demonstrated | [R0037](https://github.com/theislampill/salah_widget/issues/104) | corrective (docs + verifier) + DG1..DG3; no v1 byte change |
| [PRA-F-19](FINDINGS.md#pra-f-19) | demonstrated | [R0029](https://github.com/theislampill/salah_widget/issues/90) | corrective; unguarded-replace sub-claim upgraded plausible -> demonstrated (injected fault) with probe stated |
| [PRA-F-20](FINDINGS.md#pra-f-20) | demonstrated (efficiency); owner-deferred | [R0030](https://github.com/theislampill/salah_widget/issues/97) | retained by recorded owner decision (G4 retain) |
| [PRA-F-21](FINDINGS.md#pra-f-21) | demonstrated | [R002E](https://github.com/theislampill/salah_widget/issues/95) | decision gates G-E1/G-E2; 'unused model fields' part corrected with evidence (consumed by instruments) |
| [PRA-F-22](FINDINGS.md#pra-f-22) | demonstrated (source) | [R0034](https://github.com/theislampill/salah_widget/issues/101) | corrective (a,b); (c) lowered to no-defect-established with evidence (R0021 real bfcache restore) + G2 |
| [PRA-F-23](FINDINGS.md#pra-f-23) | plausible risk | [R002E](https://github.com/theislampill/salah_widget/issues/95) | discriminator-gated (stage 1); mechanism shown in VM, effect unmeasured |
| [PRA-F-24](FINDINGS.md#pra-f-24) | plausible risk | [R002F](https://github.com/theislampill/salah_widget/issues/96) | decision gate D-2F-3 (default A diagnostic only) |
| [PRA-F-25](FINDINGS.md#pra-f-25) | plausible risk | [R002F](https://github.com/theislampill/salah_widget/issues/96) | decision gate D-2F-4 (default A fail closed), backed by drafting probe |
| [PRA-F-26](FINDINGS.md#pra-f-26) | plausible risk | [R0033](https://github.com/theislampill/salah_widget/issues/100) | measurement-first (M5) + DG-4 (default no budget) |
| [PRA-F-27](FINDINGS.md#pra-f-27) | demonstrated | [R0028](https://github.com/theislampill/salah_widget/issues/89) | corrective (closure index, append-only) + DG-2 |
| [PRA-F-28](FINDINGS.md#pra-f-28) | demonstrated | [R002A](https://github.com/theislampill/salah_widget/issues/91) | detection (J5) + DG-4 retain; R0039 consumer |
| [PRA-F-29](FINDINGS.md#pra-f-29) | speculative | [R0031](https://github.com/theislampill/salah_widget/issues/98) | decision gate D-31-3 (default A publish-first as dependency hygiene); dependency demonstrated by injected fault, trigger kept speculative |
| [PRA-F-30](FINDINGS.md#pra-f-30) | speculative | [R0031](https://github.com/theislampill/salah_widget/issues/98) | research contract + D-31-4; proposes 'plausible (documentation-supported)' with cited Nominatim source |
| [PRA-F-31](FINDINGS.md#pra-f-31) | speculative | [R0033](https://github.com/theislampill/salah_widget/issues/100) | research contract (M6) + DG-5 (default a document) |
| [PRA-F-32](FINDINGS.md#pra-f-32) | plausible risk | [R002F](https://github.com/theislampill/salah_widget/issues/96) | decision gate D-2F-5 (default accept documented R000B policy) |
| [PRA-F-33](FINDINGS.md#pra-f-33) | plausible risk | [R0030](https://github.com/theislampill/salah_widget/issues/97) | discriminator-gated corrective (consequence by injected fault; trigger not found) |
| [PRA-F-34](FINDINGS.md#pra-f-34) | speculative (performance) | [R0034](https://github.com/theislampill/salah_widget/issues/101) | measurement gate G3; no optimisation without evidence |
| [PRA-F-35](FINDINGS.md#pra-f-35) | demonstrated (documentary) | [R0028](https://github.com/theislampill/salah_widget/issues/89) | closure-record disclosure; R0007 not reopened |
| [PRA-F-36](FINDINGS.md#pra-f-36) | plausible risk; retained UNVERIFIED by owner (R0021) | [R0034](https://github.com/theislampill/salah_widget/issues/101) | retained by recorded owner decision (G4 keep R0021) |
| [PRA-F-37](FINDINGS.md#pra-f-37) | demonstrated (source); impact speculative | [R0034](https://github.com/theislampill/salah_widget/issues/101) | corrective (first-paint parse parity) + census test; no shared-constant refactor |
| [PRA-F-38](FINDINGS.md#pra-f-38) | demonstrated (source trace) | [R0036](https://github.com/theislampill/salah_widget/issues/103) | decision gate G1 (recommended B, A applies until decided; WO stays open while pending); G1 is the single owner of visible provenance for every URL override (R0032 radar flag, R0033 DG-5(b) defer) |

No finding was dropped, declared disproved, or left without an owner. Findings that are not product defects
(PRA-F-20 owner-deferred efficiency, PRA-F-28 architecture, PRA-F-35 documentary, PRA-F-36 retained by a recorded
owner decision) are carried as decision gates or record corrections inside their owner, not as separate issues.

## 3. Machine dispositions (112 of 112)

D/I/V are the registry's Documentation / Implementation / Verification codes at the audit baseline
([status vocabulary](../../../IMPLICIT_STATES.md#status-vocabulary-for-repository-wide-entries)). A machine with
more than one work order is split by facet or row, as the disposition states; one invariant has one owner. A
machine with no work order is either already explicit and qualified (preserve), a frozen-v1 variant (document
only), or retained implicit with a reconsideration trigger recorded in the named work order.

| Machine | D/I/V | Work order(s) | Disposition |
|---|---|---|---|
| ISM-PRAY-001 | PEX/PEX/PEX | [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned: clock-anchor rows for PRA-F-14 (SalahClock preview survives zone adoption); target D/I explicit for the anchor rule |
| ISM-PRAY-002 | PEX/EEV/EEV | — | already explicit and qualified (R0003/R0006 slots) - preserve; no draft changes it |
| ISM-PRAY-003 | PEX/PEX/PEX | [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned: acquisition zone rows (zone rule extracted behaviour-identically) |
| ISM-PRAY-004 | IMS/IMS/PEX | [R002E](https://github.com/theislampill/salah_widget/issues/95), [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned, split by row: R002E contract for rollover/prefetch/stale + mirrors; R002D owns only the unresolved-day (!day) early return; both drafts agree |
| ISM-PRAY-005 | EIV/HRS/HRS | [R002C](https://github.com/theislampill/salah_widget/issues/93), [R002E](https://github.com/theislampill/salah_widget/issues/95), [R0028](https://github.com/theislampill/salah_widget/issues/89) | already explicit (R0007) - preserve; R002C adds ordering invariant P-1..P-3, R002E preserve, R0028 records R0007 cross-run reuse (PRA-F-35) |
| ISM-PRAY-006 | PEX/IMS/PEX | [R0028](https://github.com/theislampill/salah_widget/issues/89), [R002C](https://github.com/theislampill/salah_widget/issues/93) | R0028 repairs date harnesses; R002C lists it 'ordering only, preserve'; implementation retained |
| ISM-PRAY-007 | PEX/IMS/PEX | [R002E](https://github.com/theislampill/salah_widget/issues/95) | owned: fit-key completeness, discriminator-gated (PRA-F-23) |
| ISM-PRAY-008 | EIV/EEV/EIV | — | already explicit and qualified - preserve |
| ISM-PRAY-009 | IMS/IMS/PEX | [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned (primary): live zone authority, target explicit contract |
| ISM-PRAY-010 | IMS/IMS/PEX | [R002C](https://github.com/theislampill/salah_widget/issues/93) | owned (primary): render-loop liveness/containment |
| ISM-PRAY-011 | IMS/IMS/PEX | [R002E](https://github.com/theislampill/salah_widget/issues/95) | owned: status-text precedence (R002C adds no strings) |
| ISM-WX-001 | PEX/PEX/EIV | [R002F](https://github.com/theislampill/salah_widget/issues/96), [R0032](https://github.com/theislampill/salah_widget/issues/99), [R0036](https://github.com/theislampill/salah_widget/issues/103) | owned by facet: R002F acquisition/renewal, R0032 cache retention, R0036 attempt-outcome record; facets disjoint and agreed |
| ISM-WX-002 | PEX/PEX/EIV | [R002F](https://github.com/theislampill/salah_widget/issues/96) | owned: decision/header under renewal; receives R0028 G-12 product conflict only via D-2F-6 |
| ISM-WX-003 | EIV/HRS/HRS | [R002F](https://github.com/theislampill/salah_widget/issues/96) | already explicit (R000D) - preserve unless D-2F-2/3 amend |
| ISM-WX-004 | PEX/PEX/PEX | [R0032](https://github.com/theislampill/salah_widget/issues/99) | owned: radar acquisition (D-32-1) + host allowlist |
| ISM-WX-005 | EIV/HRS/HRS | [R002F](https://github.com/theislampill/salah_widget/issues/96) | already explicit (R000B) - preserve; renewal must not alter receipt semantics |
| ISM-WX-006 | PEX/PEX/EEV | — | implemented-but-not-fully-verified, closed owner R0023; no consequential gap identified by the audit - preserve (no owner needed) |
| ISM-WX-007 | IMS/PEX/PEX | [R0030](https://github.com/theislampill/salah_widget/issues/97) | owned only for the OM-04 marker row; evidence-normalisation rows retained at current status (R0030 says so explicitly) |
| ISM-WX-008 | IMS/IMS/IMS | [R0032](https://github.com/theislampill/salah_widget/issues/99) | owned: siteElev bound to location |
| ISM-WX-009 | IMS/IMS/PEX | [R002F](https://github.com/theislampill/salah_widget/issues/96), [R0034](https://github.com/theislampill/salah_widget/issues/101) | owned, split: R002F track range/age (PRA-F-25), R0034 identity-churn interface (PRA-F-10); agreed |
| ISM-WX-010 | EIV/HRS/HRS | — | already explicit and qualified (R001F) - preserve; R0037 cites as V1 CF09 analogue only |
| ISM-WX-011 | EIV/HRS/HRS | [R0031](https://github.com/theislampill/salah_widget/issues/98) | research contract on the jsonv2 field (PRA-F-30); otherwise preserve R0026 |
| ISM-WX-012 | PEX/PEX/EEV | [R0031](https://github.com/theislampill/salah_widget/issues/98), [R0036](https://github.com/theislampill/salah_widget/issues/103) | owned by facet; R0031 first, serialise on _usePrecise (both drafts agree) |
| ISM-CFG-001 | EIV/EEV/EIV | [R002C](https://github.com/theislampill/salah_widget/issues/93), [R0030](https://github.com/theislampill/salah_widget/issues/97) | already explicit - preserve; R002C adds boot/apply continuation property, R0030 adds commit-failure row |
| ISM-CFG-002 | PEX/PEX/PEX | [R0032](https://github.com/theislampill/salah_widget/issues/99) | owned: cache-namespace retention (D-32-2/3) |
| ISM-CFG-003 | PEX/PEX/PEX | [R0030](https://github.com/theislampill/salah_widget/issues/97) | owned: target EIV/EEV/EIV |
| ISM-CFG-004 | DWE/PEX/EEV | [R0030](https://github.com/theislampill/salah_widget/issues/97) | owned: target EIV/EEV/EIV |
| ISM-CFG-005 | PEX/EEV/EEV | [R0030](https://github.com/theislampill/salah_widget/issues/97), [R0036](https://github.com/theislampill/salah_widget/issues/103) | owned by row: R0030 Reset/close outcome rows, R0036 storage-probe row; agreed |
| ISM-CFG-006 | PEX/IMS/IMS | [R0030](https://github.com/theislampill/salah_widget/issues/97) | retained by recorded owner decision (G4 retain) with reconsideration trigger |
| ISM-CFG-007 | EIV/HRS/HRS | [R002D](https://github.com/theislampill/salah_widget/issues/94), [R0031](https://github.com/theislampill/salah_widget/issues/98) | already explicit - preserve; R002D tz-emission gate G-D1 only; R0031 export consumer only |
| ISM-CFG-008 | PEX/PEX/PEX | [R0031](https://github.com/theislampill/salah_widget/issues/98) | owned: reverse-geocode admission |
| ISM-CFG-009 | PEX/EEV/EEV | — | already explicit (R0012) - preserve; no finding |
| ISM-CFG-010 | DWE/PEX/PEX | [R0034](https://github.com/theislampill/salah_widget/issues/101), [R0037](https://github.com/theislampill/salah_widget/issues/104) | owned by facet: R0037 README V1 snippet (removes DWE); R0034 renderer-literal census; builder<->widget handoff retained under closed R000F (both drafts agree) |
| ISM-CFG-011 | PEX/PEX/PEX | [R0036](https://github.com/theislampill/salah_widget/issues/103) | owned: override surface + G1 visible provenance |
| ISM-SKY-001 | PEX/PEX/EIV | [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned: scene identity no longer rebuilt on zone adoption |
| ISM-SKY-002 | DWE/PEX/PEX | [R0035](https://github.com/theislampill/salah_widget/issues/102), [R0028](https://github.com/theislampill/salah_widget/issues/89) | owned: R0035 removes DWE (D1); R0028 harness evidence only |
| ISM-SKY-003 | PEX/PEX/PEX | [R002F](https://github.com/theislampill/salah_widget/issues/96) | owned: coverage establishment across the freshness boundary |
| ISM-SKY-004 | PEX/IMS/PEX | [R002F](https://github.com/theislampill/salah_widget/issues/96) | owned: explicit contract entry + verification (R2F-19), no behaviour change by default; conditional gate D-2F-6 only if R0028 G-12 shows a conflict |
| ISM-SKY-005 | PEX/PEX/PEX | [R002C](https://github.com/theislampill/salah_widget/issues/93) | owned: applyTheme failure receipt |
| ISM-SKY-006 | IMS/EEV/EEV | [R0034](https://github.com/theislampill/salah_widget/issues/101) | owned (primary): consumed-input identity + churn status |
| ISM-SKY-007 | IMS/EEV/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: already covered by vendor tests; registry correction UNK->PEX |
| ISM-SKY-008 | PEX/EEV/EIV | — | already explicit and qualified - preserve |
| ISM-SKY-009 | PEX/PEX/EEV | [R0034](https://github.com/theislampill/salah_widget/issues/101) | preserve; R0034 corrects the stale 'no persisted restore' registry text |
| ISM-SKY-010 | IMS/PEX/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: already covered; retain #warnings implicit with trigger |
| ISM-SKY-011 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | retained implicit with reason (bounded by client 15 s deadline) and trigger |
| ISM-SKY-012 | IMS/PEX/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: vendor-test coverage; registry correction |
| ISM-SKY-013 | IMS/EEV/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: vendor-test coverage; registry correction |
| ISM-SKY-014 | PEX/IMS/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: covered at bridge level; registry correction |
| ISM-SKY-015 | PEX/HRS/HRS | [R0034](https://github.com/theislampill/salah_widget/issues/101) | already resolved (R0021) - measurement only (PRA-F-34 G3) |
| ISM-SKY-016 | PEX/PEX/PEX | [R0034](https://github.com/theislampill/salah_widget/issues/101) | retained by recorded owner decision (RF04, R0021; G4 keep) + measurement |
| ISM-SKY-017 | PEX/PEX/PEX | [R0034](https://github.com/theislampill/salah_widget/issues/101) | owned: preview lifecycle (PRA-F-22a/b) |
| ISM-SKY-018 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: already covered (registry V PEX->EEV) |
| ISM-SKY-019 | IMS/IMS/PEX | [R0034](https://github.com/theislampill/salah_widget/issues/101) | owned: first-paint parse parity (OM-07) |
| ISM-SKY-020 | IMS/IMS/PEX | [R0036](https://github.com/theislampill/salah_widget/issues/103) | retained by recorded decision: production capture-time reconcile stays (R000B); R0036 documents and pins it; R0034 disclaims (residual wording R0036 L181, RR-B1) |
| ISM-SKY-021 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: partly covered (lunar memo only); one narrow eviction test for the display-geometry memo (ES38-04b); integrator correction to the reviewer map after the R0038 revision |
| ISM-SKY-022 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | retained implicit with trigger |
| ISM-SKY-023 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: already covered, bounded per-realm table (registry V PEX->EEV) |
| ISM-SKY-024 | EIV/HRS/HRS | — | already explicit and qualified (R0027) - preserve |
| ISM-SKY-025 | IMS/IMS/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | retained implicit: unreachable from shipped callers; trigger stated |
| ISM-SKY-026 | IMS/IMS/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: capability covered by vendor tests; weak memo retained |
| ISM-SKY-027 | IMS/IMS/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | retained implicit with trigger (model reuse across jobs) |
| ISM-SKY-028 | IMS/PEX/PEX | [R0032](https://github.com/theislampill/salah_widget/issues/99) | preserve (CP9 elevation lease is the correct fenced copy) |
| ISM-SKY-029 | IMS/PEX/UNK | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: already covered (registry V UNK->EEV) |
| ISM-SKY-030 | PEX/IMS/EEV | [R0034](https://github.com/theislampill/salah_widget/issues/101) | owned: fan-out table + registry bfcache correction; G2 preview pagehide default none |
| ISM-SKY-031 | DWE/IMS/PEX | [R0035](https://github.com/theislampill/salah_widget/issues/102), [R0036](https://github.com/theislampill/salah_widget/issues/103) | owned by row: R0035 star-telemetry rows, R0036 qaState purity; agreed (R0035 first) |
| ISM-MOON-001 | IMS/IMS/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | documentation of the dormant owner; implementation retained (DG-1 B keeps no-legacy-substitution) |
| ISM-MOON-002 | PEX/PEX/PEX | [R002C](https://github.com/theislampill/salah_widget/issues/93) | preserve (geometry receipt) - R002C must not change it |
| ISM-MOON-003 | IMS/PEX/PEX | [R0036](https://github.com/theislampill/salah_widget/issues/103), [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned by row: R0033 adds the pure non-adopting presence predicate (lands first); R0036 diagnostic getter purity reuses it, no second predicate |
| ISM-MOON-004 | PEX/PEX/EEV | [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned (primary): recovery owner |
| ISM-MOON-005 | IMS/PEX/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100), [R002D](https://github.com/theislampill/salah_widget/issues/94) | owned: R0033 initial-tier failure stickiness; R002D head revocation timing (preserve retirement); agreed |
| ISM-MOON-006 | IMS/PEX/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105), [R0033](https://github.com/theislampill/salah_widget/issues/100) | census by R0038 after R0033 (R0033 consumes replay); agreed |
| ISM-MOON-007 | IMS/IMS/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105), [R0033](https://github.com/theislampill/salah_widget/issues/100) | R0038 adds one narrow pump test; R0033 owns only failure-reporting edges; agreed ordering R0033->R0038 |
| ISM-MOON-008 | IMS/PEX/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | edge only (sticky failure reporting) |
| ISM-MOON-009 | IMS/PEX/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | census: covered |
| ISM-MOON-010 | IMS/PEX/PEX | [R0038](https://github.com/theislampill/salah_widget/issues/105) | one narrow test (engine exclusivity guard) |
| ISM-MOON-011 | IMS/IMS/IMS | [R0038](https://github.com/theislampill/salah_widget/issues/105) | retained implicit with reason (scheduling only) and trigger |
| ISM-MOON-012 | IMS/EEV/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | measured, not changed (M5) unless DG-4 |
| ISM-MOON-013 | PEX/HRS/EEV | — | already explicit (R0021/R0022) - preserve |
| ISM-MOON-014 | IMS/PEX/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned: failure behaviour only |
| ISM-MOON-015 | IMS/IMS/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100), [R0038](https://github.com/theislampill/salah_widget/issues/105) | R0033 measures memory (M5); R0038 retains implicit with trigger tied to R0033's measurement; agreed |
| ISM-MOON-016 | EIV/HRS/HRS | [R0033](https://github.com/theislampill/salah_widget/issues/100) | already explicit (R0021 replay refusal) - preserve |
| ISM-MOON-017 | PEX/EEV/EEV | [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned: reveal gate under DG-1 |
| ISM-MOON-018 | PEX/IMS/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned: asset cache admission (DG-3) |
| ISM-MOON-019 | IMS/PEX/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | measured, not changed (hide/show discard is truth-first by test) |
| ISM-MOON-020 | PEX/PEX/PEX | [R0033](https://github.com/theislampill/salah_widget/issues/100) | owned: light bound to presented surface (M4) + F-31 research (M6) |
| ISM-BLD-001 | PEX/PEX/PEX | [R0029](https://github.com/theislampill/salah_widget/issues/90) | owned: staged/atomic generation |
| ISM-BLD-002 | PEX/PEX/PEX | [R0029](https://github.com/theislampill/salah_widget/issues/90) | owned: Moon preflight/expansion inside the staged build |
| ISM-BLD-003 | PEX/EEV/IMS | [R002B](https://github.com/theislampill/salah_widget/issues/92) | owned: generalised payload verifier + bound |
| ISM-BLD-004 | PEX/IMS/PEX | [R002A](https://github.com/theislampill/salah_widget/issues/91), [R002B](https://github.com/theislampill/salah_widget/issues/92) | owned by facet: R002A gate/deploy model (DG-2), R002B payload measurement; agreed (serialise workflow) |
| ISM-BLD-005 | PEX/IMS/PEX | [R0028](https://github.com/theislampill/salah_widget/issues/89) | owned: closure index (PRA-F-27/35) |
| ISM-BLD-006 | PEX/IMS/PEX | [R002A](https://github.com/theislampill/salah_widget/issues/91), [R0039](https://github.com/theislampill/salah_widget/issues/106) | owned by R002A: single pinned-receipt rule (§4.3, J5(a)); cited by every README/builder/config editor (R002D, R002F, R0030, R0031, R0032, R0036, R0037, R0039); R0039 consumer |
| ISM-BLD-007 | DWE/IMS/PEX | [R0028](https://github.com/theislampill/salah_widget/issues/89) | owned (primary): expected-failure ledger |
| ISM-BLD-008 | IMS/IMS/UNK | [R002A](https://github.com/theislampill/salah_widget/issues/91) | retained by default DG-3 (retain + record lifecycle) |
| ISM-BLD-009 | PEX/PEX/PEX | [R0028](https://github.com/theislampill/salah_widget/issues/89) | owned: re-pin rule (only to accepted bytes) |
| ISM-BLD-010 | DWE/EEV/EEV | [R0037](https://github.com/theislampill/salah_widget/issues/104) | owned: meaningful --check-pages |
| ISM-V1-001 | IMS/PEX/PEX | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-002 | IMS/IMS/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-003 | IMS/PEX/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-004 | IMS/PEX/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-005 | IMS/IMS/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-006 | IMS/IMS/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-007 | IMS/PEX/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-008 | IMS/IMS/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-V1-009 | IMS/IMS/UNK | [R0037](https://github.com/theislampill/salah_widget/issues/104) | frozen v1 - document only (registry disposition; CF07-CF09 recorded; DG1 default A, no v1 byte change) |
| ISM-INST-001 | EIV/EEV/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-002 | EIV/EEV/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-003 | EIV/EEV/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-004 | EIV/EEV/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-005 | EIV/EEV/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-006 | EIV/HRS/HRS | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-007 | EIV/PEX/EIV | [R0039](https://github.com/theislampill/salah_widget/issues/106) | already explicit and qualified (R0013-R0016) - preserve; R0039 corrects registry text / Part A discriminators; Part C only under DG-I1 |
| ISM-INST-008 | PEX/UNK/UNK | [R0039](https://github.com/theislampill/salah_widget/issues/106) | owned: completion of release-asset selection record + Bash tier test (Part A) |

Work orders by machine (reverse view):

- [R0028](https://github.com/theislampill/salah_widget/issues/89): PRAY-005, PRAY-006, SKY-002, BLD-005, BLD-007, BLD-009
- [R0029](https://github.com/theislampill/salah_widget/issues/90): BLD-001, BLD-002
- [R002A](https://github.com/theislampill/salah_widget/issues/91): BLD-004, BLD-006, BLD-008
- [R002B](https://github.com/theislampill/salah_widget/issues/92): BLD-003, BLD-004
- [R002C](https://github.com/theislampill/salah_widget/issues/93): PRAY-005, PRAY-006, PRAY-010, CFG-001, SKY-005, MOON-002
- [R002D](https://github.com/theislampill/salah_widget/issues/94): PRAY-001, PRAY-003, PRAY-004, PRAY-009, CFG-007, SKY-001, MOON-005
- [R002E](https://github.com/theislampill/salah_widget/issues/95): PRAY-004, PRAY-005, PRAY-007, PRAY-011
- [R002F](https://github.com/theislampill/salah_widget/issues/96): WX-001, WX-002, WX-003, WX-005, WX-009, SKY-003, SKY-004
- [R0030](https://github.com/theislampill/salah_widget/issues/97): WX-007, CFG-001, CFG-003, CFG-004, CFG-005, CFG-006
- [R0031](https://github.com/theislampill/salah_widget/issues/98): WX-011, WX-012, CFG-007, CFG-008
- [R0032](https://github.com/theislampill/salah_widget/issues/99): WX-001, WX-004, WX-008, CFG-002, SKY-028
- [R0033](https://github.com/theislampill/salah_widget/issues/100): MOON-001, MOON-003, MOON-004, MOON-005, MOON-006, MOON-007, MOON-008, MOON-012, MOON-014, MOON-015, MOON-016, MOON-017, MOON-018, MOON-019, MOON-020
- [R0034](https://github.com/theislampill/salah_widget/issues/101): WX-009, CFG-010, SKY-006, SKY-009, SKY-015, SKY-016, SKY-017, SKY-019, SKY-030
- [R0035](https://github.com/theislampill/salah_widget/issues/102): SKY-002, SKY-031
- [R0036](https://github.com/theislampill/salah_widget/issues/103): WX-001, WX-012, CFG-005, CFG-011, SKY-020, SKY-031, MOON-003
- [R0037](https://github.com/theislampill/salah_widget/issues/104): CFG-010, BLD-010, V1-001, V1-002, V1-003, V1-004, V1-005, V1-006, V1-007, V1-008, V1-009
- [R0038](https://github.com/theislampill/salah_widget/issues/105): SKY-007, SKY-010, SKY-011, SKY-012, SKY-013, SKY-014, SKY-018, SKY-021, SKY-022, SKY-023, SKY-025, SKY-026, SKY-027, SKY-029, MOON-006, MOON-007, MOON-009, MOON-010, MOON-011, MOON-015
- [R0039](https://github.com/theislampill/salah_widget/issues/106): BLD-006, INST-001, INST-002, INST-003, INST-004, INST-005, INST-006, INST-007, INST-008

## 4. Dependency and integration plan

Filing order is ID order. The **integration (merge) order** below is a recommendation; every merge still needs
the owner's execution commission. Issue number is not priority.

1. **Foundation.** [R0028](https://github.com/theislampill/salah_widget/issues/89) (regression instruments and the expected-failure ledger) and [R0029](https://github.com/theislampill/salah_widget/issues/90) (generator atomicity), which are independent of each other, then [R002A](https://github.com/theislampill/salah_widget/issues/91)
   (gate on `main`/PRs; hard dependency on the R0028 ledger). [R002B](https://github.com/theislampill/salah_widget/issues/92) (Pages payload) is independent of the product
   chain and can start immediately.
2. **Serial chain for the shared authored owner `src/native/index.html`** (each change rebuilds every generated
   root file, so only one is open against `main` at a time):
   [R002D](https://github.com/theislampill/salah_widget/issues/94) → [R002C](https://github.com/theislampill/salah_widget/issues/93) → [R002E](https://github.com/theislampill/salah_widget/issues/95) → [R002F](https://github.com/theislampill/salah_widget/issues/96) → [R0030](https://github.com/theislampill/salah_widget/issues/97) → [R0031](https://github.com/theislampill/salah_widget/issues/98) → [R0032](https://github.com/theislampill/salah_widget/issues/99) → [R0033](https://github.com/theislampill/salah_widget/issues/100) → [R0034](https://github.com/theislampill/salah_widget/issues/101) → [R0035](https://github.com/theislampill/salah_widget/issues/102) → [R0036](https://github.com/theislampill/salah_widget/issues/103).
   - R0034 edits `real-sky/native-*.mjs` and follows R002D on `native-first-paint.mjs` / `native-contract.mjs`
     (R002D owns only the `tz` element of the identity).
   - R0033 lands before R0036 and adds its own non-adopting Moon surface-presence predicate; R0036 reuses it and
     owns diagnostic read-purity. R0033 owns Moon-side throw sites; R002C owns call-site containment and holds
     even if R0033 never lands.
   - R0030 lands before R0032; R0036 is last and nothing depends on it.
   - `tools/build_moon.py` edits by R0033 follow R0029.
3. **Independent lanes.** [R0037](https://github.com/theislampill/salah_widget/issues/104) and [R0039](https://github.com/theislampill/salah_widget/issues/106) (serialise only their `README.md` edits, and with any chain member editing
   README; R0037 and R002B share `_config.yml` — either may merge first, the second re-admits the digest).
   [R0038](https://github.com/theislampill/salah_widget/issues/105) runs last, after R0033.
4. **One rule for the pinned documentation receipt.** `tools/qualification/installer_preview_docs.cjs` pins the
   SHA-256 of `README.md`, `src/native/builder.html` and `src/native/config.js`. Any work order that changes one
   of them updates the pins and produces a successor documentation receipt in the same change. The rule is stated
   once in [R002A](https://github.com/theislampill/salah_widget/issues/91) and cited by the others.

Recommended execution tiers (the integrator's recommendation, not an owner decision):

- **Tier 1 — evidence foundation and hard-constraint or deployment-limit exposure:** [R0028](https://github.com/theislampill/salah_widget/issues/89), [R002B](https://github.com/theislampill/salah_widget/issues/92), [R002C](https://github.com/theislampill/salah_widget/issues/93), [R002D](https://github.com/theislampill/salah_widget/issues/94)
- **Tier 2 — demonstrated behavioural defects and the delivery gate:** [R0029](https://github.com/theislampill/salah_widget/issues/90), [R002A](https://github.com/theislampill/salah_widget/issues/91), [R002F](https://github.com/theislampill/salah_widget/issues/96), [R0030](https://github.com/theislampill/salah_widget/issues/97), [R0031](https://github.com/theislampill/salah_widget/issues/98), [R0033](https://github.com/theislampill/salah_widget/issues/100)
- **Tier 3 — residual state, documentation truth, privacy minimisation, recorded limitations:** [R002E](https://github.com/theislampill/salah_widget/issues/95), [R0032](https://github.com/theislampill/salah_widget/issues/99), [R0034](https://github.com/theislampill/salah_widget/issues/101), [R0035](https://github.com/theislampill/salah_widget/issues/102), [R0036](https://github.com/theislampill/salah_widget/issues/103), [R0037](https://github.com/theislampill/salah_widget/issues/104), [R0039](https://github.com/theislampill/salah_widget/issues/106)
- **Tier 4 — narrow verification census:** [R0038](https://github.com/theislampill/salah_widget/issues/105)

Release- and delivery-dependent acceptance: every product work order closes only after the merged tree's public
Pages bytes are read back against the merged tree; R002A specifies that readback as a repeatable check and R002B
measures the deployed artifact.

## 5. Review record

- **Authoring.** Seven research/authoring workers (one per domain), each re-opening the cited source at the
  baseline and re-running the audit's effect-free probes. No provider was contacted and no browser was launched.
- **Independent per-issue review.** Six reviewers in separate contexts, with no access to the authoring
  conversation, reviewed three drafts each against the owner's RLGWO methodology and IMPLEMENTAUDIT R001F: first
  round 2 PASS, 16 PASS WITH REQUIRED CORRECTIONS, 0 FAIL (28 blocking findings in total). After correction by
  the authors the same reviewers re-read every draft: 17 of 18 cleared for filing. The R0033 reviewer
  withheld clearance on one ground only — the draft exceeded a 60,000-character drafting cap by its count
  (GitHub's limit is 65,536); its substantive blocking finding was resolved. R0033 was filed on that basis and
  the complete published body was then reviewed by a further independent reviewer and accepted as published
  ([record](https://github.com/theislampill/salah_widget/issues/100#issuecomment-6840589815)). R0037 and R0039 were
  cleared only on a third pass, after the integrator aligned three table rows with the pinned-receipt rule.
- **Independent portfolio review.** A separate reviewer reconciled the set: 38/38 findings with exactly one owner;
  112/112 machines disposed; all 153 draft pairs disposed (individually where they share a source owner,
  invariant, test, document passage or decision gate); admission check against R0001–R0027; decision-gate
  census. First verdict "ready after required corrections" (5 blocking cross-draft items); final verdict ready
  to file once one remaining sentence in R0036 was aligned. That sentence was corrected by the integrator
  after the re-review and was not itself re-reviewed before filing; a bounded independent review afterwards
  found it correct and required a test amendment, recorded as binding on the issue
  ([amendment R0036-A1](https://github.com/theislampill/salah_widget/issues/103#issuecomment-6840589436)).
- **Publication readback.** Each issue was read back from the server after creation and again after the
  cross-link backfill; title, state (open) and complete body matched the reviewed text byte for byte (line
  endings normalised). The only differences between the reviewed drafts and the published bodies are the
  replacement of sibling placeholders by `Rxxxx (#issue)`, an opening identity line and a closing portfolio
  paragraph.

Limits. These are review results by separate model contexts, not human review. Reviewers spot-checked source
citations (their brief required at least twelve per draft) rather than every one. Acceptance rows are future recipes. Several work
orders rest on evidence classes short of a browser observation (VM fixtures, injected faults,
model-parameterised probes); each issue states its own.

## 6. Corrections to audit statements found while drafting

The audit documents are left as published. The work orders record these corrections with evidence:

- **Probe recipes.** The audit probes need an absolute repository path on Windows; the relative recipe in `probes/README.md` fails (R002C, R0031, R0036).
- **PRA-F-06.** The London `r0022-baseline-balance` case is a stale fixture against R0007's accepted next-day rule, not a product regression; the six `r0022` Moon pin failures begin at the R0021 merge; more red instruments exist than the seven the audit ran; `r0001` fails on its own test double as well as the shared harness (R0028).
- **PRA-F-07.** The audit's 1.91 GB figure was a git-blob estimate. The deployed `github-pages` artifact measures 1,624,134,849 bytes compressed — a measured lower bound above GitHub's documented 1 GB site limit (R002B).
- **PRA-F-14.** `SalahClock.set` has no `tz` parameter; the five CP9 tools that use it are not exposed because their fixtures make the hint equal the provider zone (R002D). A fifth `tz` writer exists (the legacy fallback when `config.js` is missing).
- **PRA-F-15.** Part (c), the capture-time cloud reconcile, is deliberate R000B production behaviour rather than a diagnostic side effect; part (d) is narrowed to a missing admission outcome (R0036).
- **PRA-F-18.** The frozen V1 card is 325×530, so the README V1 snippet's 330×534 is an invisible margin, reintroduced by `f1d056c9`; the documented verifier recipe also fails on `--check-root` (R0037).
- **PRA-F-19.** The unguarded-replacement no-op is demonstrated by an injected fault (R0029).
- **PRA-F-21.** `needTomorrow` and `warmEnd` are read by accepted tests, so they are not simply removable (R002E).
- **PRA-F-26.** The R0017 certificate already records an owner-accepted summed WASM allocation, and the restart-interval model gives shorter intervals than the audit's estimate (R0033).
- **PRA-F-30.** Nominatim's public documentation and source say `jsonv2` uses `category`; the work order proposes "plausible risk (documentation-supported)" and keeps a research/decision contract (R0031).
- **Registry.** ISM-SKY-009/030 predate R0021's recorded back/forward-cache restore (R0034); the installer open finding that the macOS native staging leg was never run on the merged bytes is contradicted by run 43173749688 (R0039); ISM-SKY-004 had no owner in the first allocation and is owned by R002F.
