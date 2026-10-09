# Remaining RLGWO priorities — revision 1

This ranks current residual obligations, not historical issue titles. Planning readiness does not mean implementation or closure is complete. Source target: `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; accepted audit evidence: `b879573c298f19189d1f2392108b8b9f3b2cda0b`. No existing priority labels were found at inventory capture, and this programme does not change unrelated labels.

## Rubric and ordering

- **P0:** demonstrated critical security/data-integrity/core-correctness failure or severe operational blockage requiring immediate action or containment.
- **P1:** substantial user-facing functionality, reliability or fidelity failure, or a significant release/closure-confidence gap that should be addressed next.
- **P2:** bounded lower-urgency quality, documentation, coverage or maintenance completion that can safely follow higher-impact work.

Current authored dispositions: P0 **0**, P1 **21**, P2 **5** across **26** specifications. Final publication additionally requires cold review and primary reconciliation. No P0 is invented to populate the rubric. Missing evidence is not proof of a current vulnerability.

Within P1, demonstrated ordinary visible failures receive attention before confidence-only gaps; broad core prayer/currentness exposure precedes less frequent edge cases. Platform acquisition starts early because its wait can dominate the schedule. Within P2, small, well-bounded document/coverage packages can finish early. The ordering below is a risk tie-breaker, not a false dependency or a promise to idle an available resource. The single heavy-browser queue, existing startup lease, native-host availability and independent review determine the actual ready waves.

Estimates below sum each issue’s declared active-work and exclusive-machine node ranges before cross-issue reuse. They are planning envelopes, not elapsed-time promises, and should not be summed across issues as independent campaigns. Confidence/basis and exclusions are in each work order. External platform/owner waits have no fabricated duration.

| Issue / ID | Residual class | Priority | Specification readiness | Execution owner | Hard prerequisites / gates | Active hours; exclusive minutes | Specification / published comment |
|---|---|---|---|---|---|---|---|
| #24 / R0018 | demonstrated-bug; evidence; docs | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | one UI/source integrator; shared docs/test integrator | Accepted interfaces already supplied; own proof/review; runtime-merge | 5.5–13h; 30–72min | [spec](REMAINING_RLGWOs/R0018.md) · publication pending |
| #33 / R0021 | demonstrated-bug; evidence; external-handoff; platform | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | primary coordinator consumes definite planning input and the same active thread successor; startup source-thread timing owner after definite intake; primary/owner actual extension new-tab surface acquisition owner | startup-source-thread/v1; r0022-l1-source/v1; r0021-cost-budget/v1; reported-parent-surface/v1; r0022-l1-full-composition/v1; runtime-merge | 4–14h; 33–125min | [spec](REMAINING_RLGWOs/R0021.md) · publication pending |
| #34 / R0022 | evidence; demonstrated-bug; design-decision | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | physical display integrator plus independent reviewer/owner; one physical display/source integrator | r0022-cost-budget/v1; r0021-startup-intake/v1; runtime-merge | 9.5–22h; 62–151min | [spec](REMAINING_RLGWOs/R0022.md) · publication pending |
| #36 / R0024 | implementation; evidence; docs; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | single native weather source integrator; shared documentation integrator; native weather state/accessibility reviewer; weather resource baseline acquirer and independent reviewer; independent weather resource reviewer | R0024-exact-head-authority/v1; R0024-required-delivery/v1; runtime-merge | 13.5–25h; 41–90min | [spec](REMAINING_RLGWOs/R0024.md) · publication pending |
| #2 / R0002 | docs; evidence; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | documentation integrator; prayer native-evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 4.5–9.25h; 25–67min | [spec](REMAINING_RLGWOs/R0002.md) · publication pending |
| #3 / R0003 | evidence; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | prayer native-evidence executor | Accepted interfaces already supplied; own proof/review; evidence-publication-and-existing-runtime-readback | 6.5–12h; 35–92min | [spec](REMAINING_RLGWOs/R0003.md) · publication pending |
| #4 / R0004 | docs; evidence; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | documentation integrator; prayer native-evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 4.25–8.5h; 20–57min | [spec](REMAINING_RLGWOs/R0004.md) · publication pending |
| #6 / R0006 | docs; evidence; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | documentation integrator; prayer native-evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 4.25–8.5h; 20–62min | [spec](REMAINING_RLGWOs/R0006.md) · publication pending |
| #7 / R0007 | evidence; docs; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | documentation integrator; prayer native-evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 4.5–9.25h; 30–77min | [spec](REMAINING_RLGWOs/R0007.md) · publication pending |
| #32 / R0020 | evidence; documentation; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | Future authorized R0020 executor; one integrator for shared writes; separate reviewer | Accepted interfaces already supplied; own proof/review; docs-merge | 9–16h; 14–45min | [spec](REMAINING_RLGWOs/R0020.md) · publication pending |
| #8 / R0008 | evidence; documentation; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | Future authorized R0008 executor; one integrator for shared writes; separate reviewer | Accepted interfaces already supplied; own proof/review; docs-merge | 9–16h; 16–45min | [spec](REMAINING_RLGWOs/R0008.md) · publication pending |
| #11 / R000B | evidence; docs; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | weather temporal fixture executor; shared documentation integrator; native weather consumer reviewer | R000B-exact-head-authority/v1; R000B-required-delivery/v1; docs-merge | 7–14h; 25–58min | [spec](REMAINING_RLGWOs/R000B.md) · publication pending |
| #12 / R000C | evidence; docs; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | weather admission mutation executor; shared documentation integrator; native acquisition/header reviewer | R000C-exact-head-authority/v1; R000C-required-delivery/v1; docs-merge | 7.5–14.5h; 18–43min | [spec](REMAINING_RLGWOs/R000C.md) · publication pending |
| #13 / R000D | evidence; docs; qualification | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | weather lifetime mutation executor; shared documentation integrator; native weather transport/recovery executor | R000D-exact-head-authority/v1; R000D-required-delivery/v1; docs-merge | 10.5–18h; 29–62min | [spec](REMAINING_RLGWOs/R000D.md) · publication pending |
| #17 / R0011 | docs; evidence | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | single documentation/source integrator; serial native evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 4.5–8.5h; 30–55min | [spec](REMAINING_RLGWOs/R0011.md) · publication pending |
| #35 / R0023 | docs; evidence | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | single documentation/source integrator; serial native evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 7–13h; 40–80min | [spec](REMAINING_RLGWOs/R0023.md) · publication pending |
| #19 / R0013 | platform-qualification; evidence; documentation | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | native macOS platform custodian; installer fixture executor; shared README integrator; independent issue evidence/prose reviewer | apple-native-host/v1; future-delivery-authority/v1; docs-merge | 7–16.75h; 45–125min | [spec](REMAINING_RLGWOs/R0013.md) · publication pending |
| #21 / R0015 | platform-qualification; evidence; documentation | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | Linux security fixture custodian; shared README integrator; independent issue evidence/prose reviewer | r0013-apple-platform/v1; r0013-native-fixture/v1; privileged-native-linux-fixture/v1; future-delivery-authority/v1; docs-merge | 6–13.5h; 37–100min | [spec](REMAINING_RLGWOs/R0015.md) · publication pending |
| #22 / R0016 | platform-qualification; documentation | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | shared README integrator; independent issue evidence/prose reviewer | r0013-apple-platform/v1; r0013-native-fixture/v1; r0015-apple-roots/v1; r0013-apple-launch/v1; future-delivery-authority/v1; docs-merge | 4–9h; 27–75min | [spec](REMAINING_RLGWOs/R0016.md) · publication pending |
| #23 / R0017 | evidence; docs | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | shared docs integrator; independent smoke reviewer and primary | Accepted interfaces already supplied; own proof/review; docs-merge | 5–11h; 25–57min | [spec](REMAINING_RLGWOs/R0017.md) · publication pending |
| #37 / R0025 | evidence | P1 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | independent cloud/time/visual reader and primary | r0025-cost-budget/v1; evidence-and-existing-runtime-readback | 4.5–10h; 23–53min | [spec](REMAINING_RLGWOs/R0025.md) · publication pending |
| #20 / R0014 | documentation | P2 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | shared README integrator; independent issue evidence/prose reviewer | future-delivery-authority/v1; docs-merge | 2–5h; 7–30min | [spec](REMAINING_RLGWOs/R0014.md) · publication pending |
| #16 / R0010 | docs; evidence | P2 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | single documentation/source integrator; serial native evidence executor | Accepted interfaces already supplied; own proof/review; docs-merge | 3–7h; 20–40min | [spec](REMAINING_RLGWOs/R0010.md) · publication pending |
| #25 / R0019 | evidence; documentation; conditional-platform-qualification | P2 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | Future authorized R0019 executor; one integrator for shared writes; separate reviewer | Accepted interfaces already supplied; own proof/review; docs-merge | 7–14h; 15–42min | [spec](REMAINING_RLGWOs/R0019.md) · publication pending |
| #27 / R001B | documentation; rendered-delivery-evidence | P2 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | shared README integrator; shared documentation fixture integrator; independent issue evidence/prose reviewer | future-delivery-authority/v1; docs-merge | 4.25–9.5h; 15–55min | [spec](REMAINING_RLGWOs/R001B.md) · publication pending |
| #28 / R001C | documentation; fixture-coverage; diagnostic-consumer-evidence; rendered-delivery-evidence | P2 | PENDING_COLD_OR_PRIMARY_RECONCILIATION | shared diagnostic docs integrator; shared documentation fixture integrator; independent issue evidence/prose reviewer | r001b-doc-scope/v1; future-delivery-authority/v1; docs-merge | 4.75–11.25h; 25–84min | [spec](REMAINING_RLGWOs/R001C.md) · publication pending |

## Individual rationales and material sub-obligations

The following preserves severity, confidence, exposure and execution cost as different dimensions. Sub-obligations retain their own priority even when the parent’s highest-risk residual sets its issue rank. The detailed acceptance rows and evidence remain in the linked specifications.

### #24 / R0018 — P1

Current default core timetable retains informational attenuation and low intended-color bright stress; the fix is small but affects the primary product information.

**Impact:** Elapsed names/times fade and ordinary glass intended colors can converge over bright sky; current approved NEXT plate does not solve other states. **Affected conditions:** Default .pastopacity.42 and bright local cell backdrop **Exposure/recurrence:** Core schedule in default appearance; optional contrast is user-selected

**Evidence confidence:** High for source/stress diagnosis; scene-specific noon numbers still need native proof **Containment:** Use stable local opacity/backing/foreground while preserving H6 subdued elapsed/readable future and existing NEXT/CURRENT hierarchy **Existing priority/label departure:** Original body called this P2. Owner current rubric assigns P1 to substantial access to core schedule text; docs compatibility remains P2. Scope/cost remain bounded; no P0 claim.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 18-02 | demonstrated-bug | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |
| 18-03 | demonstrated-bug | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |
| 18-04 | evidence | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |
| 18-05 | evidence | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |
| 18-06 | evidence | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |
| 18-07 | docs | P2 | Document the bounded local policy and unchanged interfaces after repair. |
| 18-08 | evidence | P1 | Core schedule text can be attenuated/wash out in default appearance; exact native/final proof is substantial closure confidence. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/24-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/followup-tests/receipt.json), [input 3](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/tests/r0018-timetable-contrast.cjs)

### #33 / R0021 — P1

Owner explicitly requires a first complete current celestial scene; delivered root currently reveals atmosphere then principal Moon/stars later. New complete-scene S10 links an existing ownerrejected settled displaygap.

**Impact:** Visible principal-content pop-in at normal startup and unaccepted whole-scene composition; original callback cost confidence remains missing. **Affected conditions:** Saved observer/current night cold/warm/newtab entry and actual owner reported parent **Exposure/recurrence:** Current ordinary root/native entry; V1 growthcaptures excluded

**Evidence confidence:** High on owner amendment and currentbaseline delay; source-thread final candidate/handoff not yet received **Containment:** External thread owns implementation; preserve accepted geometry/V5/catalogue/currentness/neutralUI and wait exact source intake; S10 remains visually OPEN **Existing priority/label departure:** Use current residual P1 fidelity/reliability; inherited callbackcost subtask P2. No criticalP0/no existingapprovedfinalclaim.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 21-08 | evidence | P2 | Original cost gate remains a bounded measurement gap despite accepted geometry/lifecycle; it is not replaced by new first-scene work. |
| 21-10 | demonstrated-bug | P1 | Ordinary first scene appearance misses principal celestial content for seconds; owner supplied explicit acceptance amendment and active independent repair lineage. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/33-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/release.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-browser-summary.json), [input 4](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/docs/real-sky/evidence/startup-cloud-20261007/final-v49/visual-review/chromium-moon-cold-motion.png), [input 5](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/R0022_L1_DISPLAY_INCREMENT.md), [input 6](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/INPUT_RECEIPT.json), [input 7](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/GLOW_PIXEL_ATTRIBUTION.json), [input 8](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/OWNER_AMENDMENTS.md), [input 9](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/OWNER_AMENDMENTS.md)

### #34 / R0022 — P1

New owner requestedL1 settled full-scene lunar-display defect is causally attributed on currentbaseline; original eligibility/balance/cost remainsdistinct.

**Impact:** Strong left white concentration andbroadgreywash reduceordinarynight fidelity; native eligible gain/costproof alsoincomplete. **Affected conditions:** BrightacceptedphysicalMoon atphysicalcamera-left, ordinaryOrlandoIsha scene **Exposure/recurrence:** Delivered current root and startup candidate; no startup amplification

**Evidence confidence:** High causal model/ablation and owner rejection; no calibration or accepted repair claimed **Containment:** Preserve physical astronomy/raw fields andopaqueV5calendar body; chooseonly bounded display correction underownercomplete-scenegate **Existing priority/label departure:** Original remaining balance proof/cost alone could follow as bounded coverage; newexplicitownerL1fidelity defect makesissueP1. Cost subtask P2; no P0or retroactive original-contractfailure.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 22-05 | evidence | P1 | Six originalcombined comparisons stop at removed arrays before meaningful protected gain assertions; acceptedmoderninterfaces do not waive completing this narrowlymapped proof. |
| 22-08 | evidence | P2 | One bounded warmed cost comparison follows retained native correctness; no substantial current operational failure demonstrated. |
| 22-L1 | demonstrated-bug | P1 | Ownerrejected ordinary full-night left white source andgreywash; matched field subtraction causally attributes currentphysicaldisplaycontribution, with completed boundedhandoff. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/34-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/followup-tests/replacement-receipt.json), [input 3](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/R0022_L1_DISPLAY_INCREMENT.md), [input 4](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/INPUT_RECEIPT.json), [input 5](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/inputs/startup/l1/GLOW_PIXEL_ATTRIBUTION.json), [input 6](https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/OWNER_AMENDMENTS.md)

### #36 / R0024 — P1

P1 because the missing information distinction is substantial user-visible fidelity: a supported-dry+nearby/approach decision cannot be communicated outside QA. Native A–G authority/pixel proof also remains materially incomplete. Resource/prose pieces are P2. There is no current critical security/integrity demonstration forP0.

**Impact:** Users cannot distinguish an admitted current state from nearby/approaching/numerical/unknown information; poor wording could upgrade a model to observation or forecast to present. **Affected conditions:** Current dry/wet/unknown with supplied synthetic spatial/horizon/forecast data, live adapters unavailable, local-mode settings buckle, optional probability/time/quantity fields. **Exposure/recurrence:** The weather chip is an ordinary public interface; live nearby/arrival source is absent, so missinginformation must state unavailable rather than invent useful arrival.

**Evidence confidence:** High on actual weatherHeader omission and accepted63-state/quality logic; medium on unexecuted full native/resource proof. **Containment:** Accepted finite/time/target/current/permission guards remain; bounded unavailable behavior, source-coupled rollback and isolated fixture/effect authority. **Existing priority/label departure:** No GitHub priority label present. Original body has no Pn label; owner local rubric assigns residualP1, with2421/2422 P2.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 2419 | implementation | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| 2420 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| 2421 | evidence | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| 2422 | docs | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| 2425 | qualification | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/36-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/36-publication.json)

### #2 / R0002 — P1

P1: significant closure-confidence gap at the core prayer ingress/recovery consumer; no current critical failure justifies P0. README child is P2 because it is bounded disclosure work.

**Impact:** Malformed schedules previously caused unusable prayer output or nontermination; current admission/finite defenses pass, but end-user rejection/recovery and optional date presentation have not been qualified. **Affected conditions:** Bad provider envelope/clock/date/zone, corrupt selected cache, missing/malformed optional AH, followed by healthy service. **Exposure/recurrence:** Network and selected legacy-cache consumers on ordinary root/offline loads; current runtime risk is unverified consumer behavior, not a newly reproduced bypass.

**Evidence confidence:** High for audited remaining row/scope identities; medium for future browser completion/cost because the native cases have not run. **Containment:** Current admission/ownership/day/deadline/converter fences are accepted; isolate all fixture input/storage/browser effects and withhold completed closure until missing proofs/docs/delivery pass. **Existing priority/label departure:** No live priority labels exist. Original body proposedP1; retained P1 for significant current native confidence gap, with explicitP2 docs children and no artificialP0.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 2.13 | docs | P2 | P2: narrow truthful documentation of already implemented behavior; no new runtime defect. |
| 2.13.a | docs | P2 | Bounded disclosure/maintenance |
| 2.14 | evidence | P1 | P1: significant closure-confidence gap at the core prayer ingress/recovery consumer; no current critical failure justifies P0. README child is P2 because it is bounded disclosure work. |
| 2.14.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.14.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.14.c | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.14.d | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.14.e | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.15 | qualification | P1 | P1: significant closure-confidence gap at the core prayer ingress/recovery consumer; no current critical failure justifies P0. README child is P2 because it is bounded disclosure work. |
| 2.15.a | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 2.15.b | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/A/02-assessment.json), [input 2](https://github.com/theislampill/salah_widget/issues/2#issuecomment-6073034448), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/primary-reconciliation.json)

### #3 / R0003 — P1

P1: the remaining native cross-configuration proof covers substantial user-visible correctness and persisted data. P0 is unsupported by current accepted source controls. No new mandatory README task is added.

**Impact:** Wrong-location/unit/timezone adoption would corrupt the selected timetable/weather and persisted reload state; current source fences pass but native settings/deferred consumers remain unverified. **Affected conditions:** Settings close applies A→B or A→B→A while fetch headers, body, manifest or native Image is pending; method/school/units-only changes and owned cleanup. **Exposure/recurrence:** Local/preferLocal actual settings consumers and all four acquisition slots. This is a significant confidence gap; no current reachable failure was demonstrated by the audit.

**Evidence confidence:** High for audited remaining row/scope identities; medium for future browser completion/cost because the native cases have not run. **Containment:** Current admission/ownership/day/deadline/converter fences are accepted; isolate all fixture input/storage/browser effects and withhold completed closure until missing proofs/docs/delivery pass. **Existing priority/label departure:** No live priority labels exist. Original body proposedP1; retained P1 for significant current native confidence gap, with explicitP2 docs children and no artificialP0.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 3.15 | evidence | P1 | P1: the remaining native cross-configuration proof covers substantial user-visible correctness and persisted data. P0 is unsupported by current accepted source controls. No new mandatory README task is added. |
| 3.15.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.c | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.d | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.e | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.f | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.15.g | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.16 | qualification | P1 | P1: the remaining native cross-configuration proof covers substantial user-visible correctness and persisted data. P0 is unsupported by current accepted source controls. No new mandatory README task is added. |
| 3.16.a | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 3.16.b | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/A/03-assessment.json), [input 2](https://github.com/theislampill/salah_widget/issues/3#issuecomment-6073055313), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/primary-reconciliation.json)

### #4 / R0004 — P1

P1: significant first-current-paint/upgrade-confidence gap on a core schedule consumer. README/ARCHITECTURE clauses are P2 bounded truthful documentation. No present critical failure warrants P0.

**Impact:** Painting a prior Gregorian day as current could misstate the selected schedule; filtering cache before resolved metadata would remove legitimate offline functionality. Current source controls pass; native first paint and required prose remain absent. **Affected conditions:** Tokyo coordinates without tz hint while the default NewYork hint has a different civil day, or selected old main-format cache resolves Tokyo; corrected responses across midnight/configuration changes. **Exposure/recurrence:** Existing embeds may omit tz; both live bootstrap and selected legacy cache are relevant. The missing browser discriminator concerns first accepted current frame, not eventual correction.

**Evidence confidence:** High for audited remaining row/scope identities; medium for future browser completion/cost because the native cases have not run. **Containment:** Current admission/ownership/day/deadline/converter fences are accepted; isolate all fixture input/storage/browser effects and withhold completed closure until missing proofs/docs/delivery pass. **Existing priority/label departure:** No live priority labels exist. Original body proposedP1; retained P1 for significant current native confidence gap, with explicitP2 docs children and no artificialP0.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 4.13 | docs | P2 | P2: narrow truthful documentation of already implemented behavior; no new runtime defect. |
| 4.13.a | docs | P2 | Bounded disclosure/maintenance |
| 4.14 | evidence | P1 | P1: significant first-current-paint/upgrade-confidence gap on a core schedule consumer. README/ARCHITECTURE clauses are P2 bounded truthful documentation. No present critical failure warrants P0. |
| 4.14.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.14.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.14.c | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.14.d | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.14.e | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.15 | qualification | P1 | P1: significant first-current-paint/upgrade-confidence gap on a core schedule consumer. README/ARCHITECTURE clauses are P2 bounded truthful documentation. No present critical failure warrants P0. |
| 4.15.a | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 4.15.b | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/A/04-assessment.json), [input 2](https://github.com/theislampill/salah_widget/issues/4#issuecomment-6073056799), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/primary-reconciliation.json)

### #6 / R0006 — P1

P1: significant native liveness confidence gap for unavailable→recovered functionality. README numeric/visibility disclosure is P2. No current critical dead end/storm has been reproduced, so P0 is unsupported.

**Impact:** Without real consumer proof an unavailable timetable may fail to recover or run request storms; current full-body deadlines, same-day scheduling and prefetch cooldown source controls pass. **Affected conditions:** No cache and stalled headers/body or repeated failures, network restored before elapsed60s; hidden/offscreen during cooldown; usable next-day records and new day/generation. **Exposure/recurrence:** Ordinary visible real-time boot/apply/current/prefetch paths on qualified performance.now hosts. Date.now-only fallback has a retained nonmonotonic limitation, not a new universal host obligation.

**Evidence confidence:** High for audited remaining row/scope identities; medium for future browser completion/cost because the native cases have not run. **Containment:** Current admission/ownership/day/deadline/converter fences are accepted; isolate all fixture input/storage/browser effects and withhold completed closure until missing proofs/docs/delivery pass. **Existing priority/label departure:** No live priority labels exist. Original body proposedP1; retained P1 for significant current native confidence gap, with explicitP2 docs children and no artificialP0.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 6.13 | docs | P2 | P2: narrow truthful documentation of already implemented behavior; no new runtime defect. |
| 6.13.a | docs | P2 | Bounded disclosure/maintenance |
| 6.15 | evidence | P1 | P1: significant native liveness confidence gap for unavailable→recovered functionality. README numeric/visibility disclosure is P2. No current critical dead end/storm has been reproduced, so P0 is unsupported. |
| 6.15.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 6.15.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 6.15.c | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 6.15.d | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 6.16 | qualification | P1 | P1: significant native liveness confidence gap for unavailable→recovered functionality. README numeric/visibility disclosure is P2. No current critical dead end/storm has been reproduced, so P0 is unsupported. |
| 6.16.a | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 6.16.b | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/A/06-assessment.json), [input 2](https://github.com/theislampill/salah_widget/issues/6#issuecomment-6073060055), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/primary-reconciliation.json)

### #7 / R0007 — P1

P1: substantial displayed precision/recovery confidence gap at the actual consumer. README child is P2 bounded clarification. Current source correctness is accepted and supplies no P0 counterexample.

**Impact:** DST wall-minute subtraction previously misstated elapsed time by an hour; current epoch consumer and unavailable behavior pass source controls. Actual DST pixels/arc and unsupported endpoint/recovery consumers are not yet qualified. **Affected conditions:** A timezone offset changes before the next selected prayer, or the intended future record/inverse is missing, wrong-day, gap/fold; frozen late-prefetch recovery. **Exposure/recurrence:** Location-clock next-prayer UI across DST/overnight boundaries; current significant confidence gap concerns actual .left/.nt output and physical arc preservation, not a new converter defect.

**Evidence confidence:** High for audited remaining row/scope identities; medium for future browser completion/cost because the native cases have not run. **Containment:** Current admission/ownership/day/deadline/converter fences are accepted; isolate all fixture input/storage/browser effects and withhold completed closure until missing proofs/docs/delivery pass. **Existing priority/label departure:** No live priority labels exist. Original body proposedP1; retained P1 for significant current native confidence gap, with explicitP2 docs children and no artificialP0.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 7.12 | evidence | P1 | P1: substantial displayed precision/recovery confidence gap at the actual consumer. README child is P2 bounded clarification. Current source correctness is accepted and supplies no P0 counterexample. |
| 7.12.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.12.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.14 | docs | P2 | P2: narrow truthful documentation of already implemented behavior; no new runtime defect. |
| 7.14.a | docs | P2 | Bounded disclosure/maintenance |
| 7.15 | evidence | P1 | P1: substantial displayed precision/recovery confidence gap at the actual consumer. README child is P2 bounded clarification. Current source correctness is accepted and supplies no P0 counterexample. |
| 7.15.a | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.15.b | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.15.c | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.15.d | evidence | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.16 | qualification | P1 | P1: substantial displayed precision/recovery confidence gap at the actual consumer. README child is P2 bounded clarification. Current source correctness is accepted and supplies no P0 counterexample. |
| 7.16.a | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |
| 7.16.b | qualification | P1 | Required actual consumer correctness/preservation/closure-confidence proof |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/A/07-assessment.json), [input 2](https://github.com/theislampill/salah_widget/issues/7#issuecomment-6073061264), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/primary-reconciliation.json)

### #32 / R0020 — P1

Significant scheduled native prayer/day/late-response/cache/real-elapsed ownership qualification gap after repaired wall authority.

**Impact:** Combined confidence that corrected current instant changes prayer/countdown/day/acquisition truthfully and preserves explicit preview/visibility. **Affected conditions:** Forward/reverse wall changes at prayer/day boundary, held response or retry, hidden/offscreen resume and explicit clock modes. **Exposure/recurrence:** Ordinary no-override mode consumers; existing repaired source and exact-root native direct-render correction provide substantial containment.

**Evidence confidence:** High for44 source controls and retained27-assertion native direct-wall/model-host-sky case; complete scheduled release matrix not yet established. **Containment:** Direct-wall default, anchored explicit preview, backward-aware loop, strict inverse, matched admitted day/current cache and elapsed prayer cooldown/owning slots. **Existing priority/label departure:** Original proposed P1 retained; docs subobligationP2; no P0 quota or current critical defect inferred.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0020-O06 | evidence | P1 | Core day/current/cache/late/slot combined native qualification gap. |
| R0020-O08 | evidence | P1 | Real-elapsed prayer budget and ownership are core acquisition confidence; weather finding explicitly outside scope. |
| R0020-O12 | evidence | P1 | Retained native Date/performance proof credited; missing scheduled loop/cache/day/slot consumer remainder must be joined. |
| R0020-O13 | evidence | P1 | Complete required native boundary/day/visibility/explicit matrix supplies substantial core-consumer closure confidence. |
| R0020-O14 | evidence | P1 | State-matched corrected day/prayer pixels missing despite retained broader native wall/full/reduced evidence. |
| R0020-O15 | documentation | P2 | Narrow universal-formula/explicit1x DESIGN inaccuracy can safely be corrected. |
| R0020-O16 | qualification | P1 | Final exact-source/caller/native/delivery review mandatory; adjacent weather is not added repair scope. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/32-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/r0020-clock.cjs.log), [input 3](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/docs/real-sky/evidence/startup-cloud-20261007/final-v49/runs/joined-v49-final-chromium-native-lifecycle/results.json#L14302-L15932)

### #8 / R0008 — P1

Significant combined native qualification gap on strict timezone inverse consumed by real hourly weather, invalid-scene recovery and provider-zone adoption; source arithmetic already repaired.

**Impact:** Unqualified combined correctness/availability on reached weather and explicit clock consumers; inaccurate documented resolver/clock contract. **Affected conditions:** DST gap/fold, deferred weather with changed global context/generation, invalid-to-valid scene, cold native Intl profile. **Exposure/recurrence:** Real hourly parser plus opt-in explicit simulation; ordinary source controls and fail-closed gates remain accepted.

**Evidence confidence:** High in repaired source/37-case oracle and existing guards; combined actual native paths remain unverified, not demonstrated current defects. **Containment:** Unique finite inverse or unavailable, generation/attempt guards, separate current/hourly admission; stop on observed failure/unresponsiveness. **Existing priority/label departure:** No live priority label is changed. Original body proposed P2; residual caller/native closure-confidence exposure is assessed P1. Documentation row remains P2; no P0 finding.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0008-O08 | evidence | P1 | Actual captured-zone hourly interface combines inverse and async ownership beyond accepted helper arithmetic. |
| R0008-O09 | evidence | P1 | Native current/hourly separation and valid source age are consequential real-weather consumer gaps. |
| R0008-O12 | evidence | P1 | Full native invalidation/recovery/provider-zone pathways materially exceed scalar source proof. |
| R0008-O13 | evidence | P1 | Actual native cold cost/reuse is a meaningful acceptance gap; no invented numeric deadline or routine owner approval. |
| R0008-O14 | evidence | P1 | Invalid/recovered native visual boundary and affected valid-scene regression must be qualified without weakening accepted renderer. |
| R0008-O15 | documentation | P2 | Narrow inaccurate/missing DESIGN facts can safely be corrected without a runtime redesign. |
| R0008-O16 | qualification | P1 | Mandatory final exact-source/caller/browser/delivery obligation remains a real closure node. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/08-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/r0008-timezone.cjs.log), [input 3](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1230-L1385)

### #11 / R000B — P1

P1 because source-time/receipt-time and per-use expiry guard a core weather-authority pathway, and their required regression controls remain missing. Missing public prose and overflow diagnostic coverage alone are P2. Accepted runtime fences contain the known historical defect; no demonstrated critical current failure supports P0.

**Impact:** Potential regression could keep expired weather visually current or label a fresh retrieval as fresh source information; the actual final source is fail-closed on known invalid ages. **Affected conditions:** Malformed source metadata, repeated old mosaic, provider outage, tab resume, client clock skew or request-zone supersession. **Exposure/recurrence:** All ordinary real-time weather users rely on current authority; hostile overflow is a rare input, not a recorded provider incident.

**Evidence confidence:** High on source/accepted boundary behavior and remaining documentation gap; medium on unexecuted hostile/mutant/native coverage. **Containment:** Accepted finite/time/target/current/permission guards remain; bounded unavailable behavior, source-coupled rollback and isolated fixture/effect authority. **Existing priority/label departure:** Original draft proposed P1; no GitHub priority label is present. Retain P1 for the current closure-confidence gap, distinguish lower-urgency P2 documentation/overflow subrows.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| B04 | evidence | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| B13 | evidence | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| B14 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| B16 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| B17 | docs | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| B18 | qualification | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/11-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/11-publication.json)

### #12 / R000C — P1

P1 for substantial confidence missing at the transport→admission→cache→visible header/effect boundary. The originalP2 draft described a product repair; current runtime repair is accepted, so the P1 recommendation refers to native/mutation confidence, not a newly claimed defect. Documentation is P2; no P0 evidence.

**Impact:** A future regression could manufacture0° from null or permit malformed measurements to drive effects; native exact input proof prevents a parser-only false closure. **Affected conditions:** Partial/malformed200, healthy-shaped500, legacy/cache records and true zero/negative measurements; forecast/current split. **Exposure/recurrence:** Weather header is visible to every ordinary weather user; poisoned values are adversarial controls rather than recorded provider incidents.

**Evidence confidence:** High on current source and accepted119/245-pass logic evidence; native malformed/zero cases and mutants remain unverified. **Containment:** Accepted finite/time/target/current/permission guards remain; bounded unavailable behavior, source-coupled rollback and isolated fixture/effect authority. **Existing priority/label departure:** No GitHub priority label present. Original draftP2 → residualP1 because missing native/mutation proof affects a material authority pathway; keep prose subrowP2.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| C14 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| C15 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| C16 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| C17 | docs | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| C18 | qualification | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/12-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/12-publication.json)

### #13 / R000D — P1

P1 because no native proof currently covers a material reliability path from a stalled acquisition through release and a real replacement consumer. Source/runtime repair is accepted; this is not evidence of a current eternal-busy bug. The documentation/preservation-only pieces are P2; originalP2 title does not set remaining confidence priority.

**Impact:** An unnoticed body/Image/finalizer regression could permanently block weather or let late old completion damage successor ownership; wrong recovery evidence would conceal it. **Affected conditions:** Headers never arrive, partial JSON never completes, Image remains undecoded, delayed timers, ignored abort or configuration supersession. **Exposure/recurrence:** Ordinary provider/network failures across allweather users; held-body/Image fixtures are deliberate adversarial cases, not current provider-health claims.

**Evidence confidence:** High on actual source and24 deterministic lifetime/ownership tests; medium on future native scheduling/transport observation. **Containment:** Accepted finite/time/target/current/permission guards remain; bounded unavailable behavior, source-coupled rollback and isolated fixture/effect authority. **Existing priority/label departure:** No GitHub label present. OriginalP2 → residualP1 for the unproven native reliability/recovery pathway; preserve P2 docs and geometry-only subrow.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| D11 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| D12 | evidence | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |
| D13 | evidence | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| D14 | docs | P2 | Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. |
| D15 | qualification | P1 | Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/13-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/13-publication.json)

### #17 / R0011 — P1

Actual denied-storage caller feedback, close/reopen usability and warning rendering remain materially unverified; the product repair itself is accepted.

**Impact:** A user may trust persistence/reset or miss a session-only warning; native confidence and usability need a discriminating bridge. **Affected conditions:** Storage read/write/removal denied, or iframe host storage restrictions. **Exposure/recurrence:** Settings in local/preferLocal mode; denial prevalence is unknown and not inferred from mocks.

**Evidence confidence:** High on documentation errors, medium on missing native behavior proof. **Containment:** Existing in-memory fallback accepted; issue stays open and fault tests use disposable storage only. **Existing priority/label departure:** No current priority label. Original proposed P2 applied to the historic caller defect; P1 here is justified by significant remaining native failure/feedback confidence, not a newly demonstrated critical failure.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0011-O15 | evidence | P1 | Actual native caller reliability under denied storage is a significant remaining closure-confidence gap despite accepted source repair. |
| R0011-O16 | evidence | P1 | Users must find and read failure state after closing a modal; warning geometry/focus needs real rendered/native evidence. |
| R0011-O17 | docs | P2 | Bounded misleading partition/reset wording; no demonstrated data purge or failure prevalence. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/17-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/README.md#L134-L139)

### #35 / R0023 — P1

Native metadata persistence/builder negative lifecycle and native iframe policy confidence remain materially incomplete, while the implementation and downstream meaning contract are accepted.

**Impact:** Saved device coordinates must not imply current presence/fresh precision; acquisition controls must fail honestly in embed policy contexts. **Affected conditions:** Stored browser position, unrelated later save, malformed metadata, cached fix, legacy record or denied iframe policy. **Exposure/recurrence:** Local/preferLocal Settings and builder one-shot location paths; actual host/sensor prevalence unmeasured.

**Evidence confidence:** High on explicit doc omissions and retained source/native positive; medium on remaining native matrix. **Containment:** Keep fixed sites usable; one-shot opt-in acquisition and isolated synthetic inputs, no continuous GPS or owner permission interaction. **Existing priority/label departure:** No current priority label. Current P1 reflects significant closure-confidence gaps, not a claim that the original metadata bug persists.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0023-O04 | docs | P2 | Timestamp behavior and boundary controls already pass; only actual zero-skew/clock documentation remains. |
| R0023-O18 | docs | P2 | Bounded metadata/recipient disclosure corrects unsupported precision and persistence/fix wording. |
| R0023-O21 | evidence | P1 | Actual delegated/denied permission paths are a significant remaining platform-policy confidence gap; injected success/error cannot prove browser enforcement. |
| R0023-O22 | evidence | P1 | Complete actual form/persistence/builder negative lifecycle bridge remains missing after 31 source positives and current native25m/T acquisition/reopen positive. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/35-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/config.js#L56-L85), [input 3](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L339-L341)

### #19 / R0013 — P1

The supported Apple Bash3.2 floor and complete detector matrix still lack native qualification. This is a significant supported-platform closure-confidence gap; accepted launch/path repairs are preserved.

**Impact:** A macOS user may encounter an undetected shell/native discovery incompatibility. No current native failure has been demonstrated; missing terminal/cache/path instructions can also mislead a manual installer user. **Affected conditions:** Normal advertised Bash launch on actual Apple macOS; zero/multiple/odd profile paths under nounset, or reading public install guidance. **Exposure/recurrence:** Claimed macOS installer users; documentation is public. Existing modern Linux and builder controls are accepted.

**Evidence confidence:** High that specified proof/docs are absent; unknown native product outcome until measured. **Containment:** Retain fail-closed terminal/staging guards and reviewed-file guidance. Acquire the native host and use disposable contained fixtures before stronger support/closure claims. **Existing priority/label departure:** No priority label is present in the captured issue. P1 remains the original body proposal, now justified by residual qualification rather than the already repaired historical defects.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 19-05 | platform-qualification | P1 | Missing native minimum-host proof is a significant support-confidence gap; complete modern matrix and line-delimited disclosure are lower-cost closure prerequisites, not evidence of a current product failure. |
| 19-09 | documentation | P2 | The launch/path implementations are accepted; omission of terminal/review/cache instructions is bounded user guidance work, with a public/manual-execution impact. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/19-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/native-rebind.json), [input 4](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/CUSTODY.json), [input 5](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-helper-archived-source.json), [input 6](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-entry-archived-source.json), [input 7](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-mutations-archived-source.json), [input 8](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/native-applicability-2fafcbf.json), [input 9](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/builder-config-rebind.json), [input 10](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/fresh-positive-receipts.json), [input 11](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/r0010-preferences.stdout.log), [input 12](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/r0012-clipboard.stdout.log)

### #21 / R0015 — P1

The unqualified native Apple filesystem branch and missing ownership-isolated admission negative are material confidence gaps in a security boundary. No current unintended write is demonstrated after accepted private-root repairs.

**Impact:** An undetected native filesystem/utility or HOME-admission failure could affect private staging or retention; incomplete lifetime guidance can cause users to remove an unpacked extension directory too early. **Affected conditions:** Actual macOS normal staging/extraction/cleanup, or a reachable HOME owned by a different UID but not group/world writable; public manual bundle use. **Exposure/recurrence:** Bash supported platform/security boundary; existing modern Linux guard/ZIP/lifetime/DAC controls are qualified.

**Evidence confidence:** High that these separate native/admission cells and public facts are missing; native/security failure outcome remains unknown until measured. **Containment:** Keep strict UID/mode/symlink/root-identity guards and isolated fixtures. Acquire Apple and privileged Linux fixture prerequisites; do not relax checks or use writable /tmp as the missing discriminator. **Existing priority/label departure:** No priority label captured. Original bodyP1 is retained for residual security/platform confidence; the historical overwrite witness is not represented as a current unpatched defect.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 21-03 | platform-qualification | P1 | Actual Apple/native-filesystem branch is part of the private staging security/lifetime interface; absent proof is substantial confidence uncertainty, not proof of an exploit. |
| 21-05 | evidence | P1 | The wrong-UID parent boundary must be independently distinguished from mode refusal because the admission rule protects retained output ownership. |
| 21-15 | documentation | P2 | Missing lifetime/cache instructions are bounded manual-use guidance; implementation and historical consumption already pass. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/21-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/native-rebind.json), [input 4](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/CUSTODY.json), [input 5](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-helper-archived-source.json), [input 6](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-mutations-archived-source.json), [input 7](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/crossuid-nonlogin/result.json), [input 8](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/crossuid-nonlogin/post-run-native-readback-qualified.json), [input 9](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/native-applicability-2fafcbf.json)

### #22 / R0016 — P1

The complete Apple whole-entry no-effect boundary has no native receipt. Supported-platform preview/normal separation is a significant closure-confidence gap; Linux/Windows and current guards remain accepted.

**Impact:** An unmeasured Apple preview effect path could undermine a claimed no-effect dry run; missing public preview/NoOpen guidance prevents informed use. No current Apple effect escape is demonstrated. **Affected conditions:** DRY_RUN=1 or normal/NO_OPEN under actual Apple3.2/macOS; public readers choosing -DryRun/-NoOpen. **Exposure/recurrence:** Bash macOS preview and all public installer instructions. Complete native Linux and exact Windows5.1/7 entry proofs are retained.

**Evidence confidence:** High that Apple/documentation cells remain missing; unknown Apple product outcome until native controlled execution. **Containment:** Keep current early-exit/effect guards, private fixtures and source snapshot/interception. No real network/files/profile/clipboard/browser operation is allowed in future qualification. **Existing priority/label departure:** No captured priority label. OriginalP1 remains justified by the residual minimum-platform whole-entry boundary; historical Linux/Windows effect defects are not represented as current failures.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 22-09 | platform-qualification | P1 | Missing actual Apple complete entry is significant confidence uncertainty in a claimed no-effect boundary. Existing native Linux/Windows proof is accepted and must not be replayed. |
| 22-12 | documentation | P2 | Script boundary is already accurate; missing public mode distinctions are bounded docs work and can draft before native access. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/22-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/native-rebind.json), [input 4](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/CUSTODY.json), [input 5](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-entry-archived-source.json), [input 6](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/bash-mutations-archived-source.json), [input 7](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/direct-native-final.json), [input 8](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/direct-native-mutants.json), [input 9](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/native-applicability-2fafcbf.json)

### #23 / R0017 — P1

Current required native execution and hostile-mode proof is missing despite implemented recorder/transport controls; this is a significant closure-confidence gap.

**Impact:** A healthy-looking instrument can be trusted beyond actual executed consumer coverage; README omission makes scope easy to misread. **Affected conditions:** Final current 30-case smoke wrapper and browser preference/mode envelope **Exposure/recurrence:** Maintainer verification; not evidence of production data loss

**Evidence confidence:** High on missing specific receipts and README facts; product mechanisms remain accepted **Containment:** Honest INCOMPLETE/FAIL and private storage already implemented; leave issue open until actual native proof **Existing priority/label departure:** Original priority does not decide residual scheduling; P1 for material native closure confidence, P2 docs subtask; no P0 evidence.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 17-03 | evidence | P1 | Significant final-consumer closure-confidence gap; source controls alone cannot prove all native callbacks. |
| 17-07 | evidence | P1 | Prayer readiness can be falsely green if response consumption/attempt identity is not exercised by a native consumer. |
| 17-08 | evidence | P1 | The positive ledger is not discriminating without actual hostile-mode bounded non-pass. |
| 17-09 | evidence | P1 | Native preference/override failure and restoration need the real consumer, not an assumed restored OS signal. |
| 17-10 | docs | P2 | Missing bounded safe-use/outcome docs can be repaired without product behavior changes. |
| 17-11 | evidence | P1 | Final current public consumer and independent denominator proof are mandatory closure gates. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/23-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/followup-tests/receipt.json)

### #37 / R0025 — P1

The original named native continuity raster discriminator remains absent despite accepted commands/motion; this is a significant residual closure-confidence gap.

**Impact:** Ordinary wind/civil updates could still violate a specifically required displayed-pixel invariant; no current failing image is asserted. **Affected conditions:** Equal-time wind and day/month/year operators on an established native cloud field **Exposure/recurrence:** Ordinary weather refresh and continuous sky use

**Evidence confidence:** High on missing raster/cost receipts; high accepted confidence in source mechanisms **Containment:** Evidence-only first; keep stable population, integrated old wind and real motion; no Plan07 or whole-sky refactor **Existing priority/label departure:** Residual native displayed-continuity confidence is P1 under owner rubric; bounded cost subtask P2. Original historical defect title alone is not evidence of a current bug.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 25-07 | evidence | P1 | Source/state equality and existing normal motion do not establish the issue explicitly named native raster operators; this is substantial continuity closure confidence. |
| 25-10 | evidence | P2 | One bounded cost/state receipt follows the accepted correctness/motion work; no current operational failure is demonstrated. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/37-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/F/followup-tests/replacement-receipt.json), [input 3](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/tests/r0025-context.cjs)

### #20 / R0014 — P2

Only the advertised host/reviewed-file instructions remain. The original native parse/selector/caller/entry failures have accepted exact-file proof on Windows5.1 and supported7.

**Impact:** Public readers may not know the supported WindowsPowerShell floor or safe review/download/quoted -File route, and may mistake staged manual artifacts for installation. **Affected conditions:** Reading/copying the Windows instructions in README; host execution policy and user choice still govern future local execution. **Exposure/recurrence:** Public installer guidance; unchanged encoded builder command and native script are qualified.

**Evidence confidence:** High: delivered README omission and exact native script/fixture identity are independently recorded. **Containment:** Add precise prose and a downloaded-file review route; preserve script bytes, selector tiers, manual boundary and native receipt binding. **Existing priority/label departure:** Captured issue has no priority label. Original body proposed P1 for two implementation failures; residual is re-triaged to P2 because those failures are repaired/qualified and only bounded documentation remains.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 20-08 | documentation | P2 | Host/reviewed-file/manual instructions are the sole residual; native defects are already qualified, so this safely follows implementation without a new platform or production change. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/20-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/native-rebind.json), [input 4](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/CUSTODY.json), [input 5](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/final-r0014-ps51.txt), [input 6](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/final-r0014-ps7.txt), [input 7](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/ps51-mutations-qualified.json), [input 8](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/ps7-mutations-final-source.json), [input 9](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/direct-native-final.json), [input 10](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/direct-native-mutants.json)

### #16 / R0010 — P2

The implementation is accepted; the residual is one truthful README paragraph and bounded native-origin coverage.

**Impact:** Users need to know whose fresh defaults and saved preferences win; closure confidence lacks the real display bridge. **Affected conditions:** Fresh local embed versus previously saved viewer; no demonstrated current failure. **Exposure/recurrence:** All builder local exports, with source-level 9/9 and both omission controls already accepted.

**Evidence confidence:** High on documentation omission, medium on unexecuted native bridge. **Containment:** Keep issue open; use disposable contexts and no production mutation. **Existing priority/label departure:** No current priority label. Historic proposed P1 described the original product defect; P2 assesses the now bounded residual.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0010-O09 | docs | P2 | Bounded local-mode explanation; source behavior already verified, no current harmful failure demonstrated. |
| R0010-O12 | evidence | P2 | Focused native display/persistence bridge missing after nine source positives and two omission mutants; a coverage gap, not a demonstrated reappearance of the historic product bug. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/D/16-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/README.md#L80-L119)

### #25 / R0019 — P2

Source access mechanism and short native interaction already work; remaining long-input/native coverage and docs are bounded lower-urgency closure work.

**Impact:** Complete-value access confidence for long/preset/fallback font/touch/continuous-open states, and missing user instructions. **Affected conditions:** Long format/provider month, blocked webfont, actual Tab/touch selection, open source/day transitions or supported-host modal incompatibility. **Exposure/recurrence:** Footer full-value readers, especially long-format/touch/keyboard users; compact date remains visible and access has accepted native smoke.

**Evidence confidence:** High in16 source cases/stable CSS/handlers and accepted native ordinary/missing smoke; long native matrix not established. **Containment:** Same selected projection, native modal, stable nodes, selectable wrapping CSS, no-effect read and inert text; conditional failure keeps host/issue open. **Existing priority/label departure:** Original body proposed P2 retained; no live label mutation. Re-triage only if actual supported-host access/dismissal failure is demonstrated.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| R0019-O11 | evidence | P2 | Actual Tab/tick focus qualification is bounded interface confidence work; short native controls already credited. |
| R0019-O12 | evidence | P2 | Long touch/scroll/selectability extends accepted ordinary touch without a demonstrated defect. |
| R0019-O13 | evidence | P2 | Preset/font overflow native coverage is bounded lower urgency while strict source/CSS controls work. |
| R0019-O14 | evidence | P2 | Continuous open/effect matrix remains bounded missing proof with accepted security/selector interfaces. |
| R0019-O15 | evidence | P2 | Matched card/builder geometry proof is bounded UI qualification; owner shell amendment remains accepted. |
| R0019-O16 | conditional-platform-qualification | P2 | No unsupported-host defect established; qualify actual supported engines and gate only a measured incompatible host. |
| R0019-O17 | documentation | P2 | Existing discoverability/access instructions absent; narrow doc improvement. |
| R0019-O18 | qualification | P2 | Final mandatory consumer security/selection/native/docs/delivery gate cannot disappear into a generic task. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/25-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/r0019-date-disclosure.cjs.log), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/B/native-followup-review.json)

### #27 / R001B — P2

Current request constructors/callers and Reset controls are qualified. Remaining work is precise public privacy disclosure and rendered/delivered agreement, without a network-policy or provider-retention change.

**Impact:** Readers may misunderstand which typed queries/coordinates/location-derived indices leave the browser or what Reset erases because the old public blanket statement and incomplete provider list remain. **Affected conditions:** Reading README privacy or following builder Request details; external requests depend on user actions/config/cache/provider readiness. **Exposure/recurrence:** Public human guidance for current implemented behavior; builder summary is already correct.

**Evidence confidence:** High: eight exact source/caller/Reset controls passed; independent prose inspection identifies missing table/reset facts. No external retention policy is inferred. **Containment:** Replace only inaccurate prose; retain user-triggered precise permission, coarse/manual fallback and existing behavior. Make each source-supported request disclosure explicit. **Existing priority/label departure:** No priority label is present. P2 matches original documentation proposal; no implementation/security escalation is invented.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 27-01 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-02 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-03 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-04 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-05 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-06 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-07 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-08 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-09 | documentation | P2 | Bounded disclosure gap for an accepted request/reset interface: public comprehension matters, but no current runtime/network-policy defect or retention fact is demonstrated. |
| 27-12 | rendered-delivery-evidence | P2 | Rendered complete disclosure and future changed public bytes are necessary completion proof. Current public availability/byte binding is already accepted, so no blanket runtime gate is created. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/27-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/docs-contract-primary.json)

### #28 / R001C — P2

Hash parser/motion flag construction, five existing append recipes and current public normal-runtime baseline pass. Remaining work is bounded inaccurate diagnostic recipes/enum, one incomplete force VM fixture and specific rendered/browser proof.

**Impact:** Reviewers using query-only examples fail to activate intended diagnostics or may assert unsupported forces; incomplete fixture evidence can be mistaken for a runtime defect or visible-pixel proof. **Affected conditions:** Copying AGENTS/DESIGN/OPTICS diagnostic recipes, interpreting force names, or using motion=full under reduced-motion for diagnostic qualification. **Exposure/recurrence:** Public documentation and future QA users; no demonstrated default-runtime failure or new physics/appearance claim.

**Evidence confidence:** High that positive query-only recipes/enum prose are incorrect; source/readback/source-control scope is exact. Specific browser motion-overlay/reduced cases and completed force fixture are unverified. **Containment:** Correct prose and fixture context without changing q, force branches, physical eligibility or runtime behavior. Keep screenshots/real-watch requirements for visual claims; inspect actual browser native preference before declaring override. **Existing priority/label departure:** No priority label present. P2 matches original diagnostic-docs proposal; the failed _pbrFailed fixture is not used to inflate product priority.

| Residual obligation | Class | Priority | Reason |
|---|---|---|---|
| 28-01 | documentation | P2 | Incorrect public positive examples are bounded guidance defects; actual parser is correct and must remain unchanged. |
| 28-02 | documentation | P2 | Incomplete force enum/blanket forceability can mislead QA; runtime branches/gates are already inspected and remain unchanged. |
| 28-03 | documentation | P2 | Missing complete copyable examples make correct & shorthand hard to use; bounded documentation completion. |
| 28-04 | documentation | P2 | Freeze and activation/pixel boundary protects QA accuracy; preserves existing visual/physics requirements without a new runtime claim. |
| 28-05 | fixture-coverage | P2 | Actual parser positive/negative already passes; corrected literals and completed force/corona execution need bounded evidence. Omitted VM binding is a fixture failure, not a production bug. |
| 28-06 | diagnostic-consumer-evidence | P2 | The mandatory specific browser diagnostic/override cell remains open;16 normal-runtime cases already qualified baseline and do not need replay. |
| 28-09 | rendered-delivery-evidence | P2 | Final correct prose/evidence/rendered-public agreement is necessary delivery proof; existing current raw availability is accepted and does not close changed text. |

Evidence: [input 1](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/28-assessment.json), [input 2](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-document-distribution.json), [input 3](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/docs-contract-primary.json)

## Startup and glow boundary

R0021/#33 owns first-scene initialization/availability and its original callback-cost residuals. The separately demonstrated settled lunar atmospheric/display hotspot and broad wash is the named R0022-L1 successor under #34, linked from S10. Its presence in both baseline and candidate does not make it an accepted appearance or a new startup-caused regression. Attribution is completed; the bounded display correction and full-scene acceptance remain explicitly gated. The definite [STARTUP_HANDOFF](STARTUP_HANDOFF.md) records an active uncommitted candidate, no PR at capture, two Chromium timing failures, final Firefox measurement pending, actual extension parent unavailable and original callback cost unverified. It is a completed planning handoff, not a final implementation acceptance. Do not wait for all issue closures to plan these nodes, and do not count a lunar RGB comparison as whole-scene acceptance.

No change to N001/N002 PARTIAL or N003 BLOCKED is implied. Native Apple requirements remain specific to their installer/filesystem/entry contracts, not a global barrier to unrelated Windows/browser/docs work. New merges/deployments require separate exact-head approval.
