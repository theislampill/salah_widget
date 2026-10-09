# Remaining RLGWO specifications — bounded authoring contract

Primary programme: complete26 residual specifications, priority reasoning, startup handoff reconciliation, validated execution DAG, and publish all26 versioned issue comments. Documentation/planning only in this thread. No production changes, tests, builds, browser launches, issue state changes, labels, commits or GitHub writes by workers until an exact publication lease. Reuse source/audit work; do not repeat the37-issue audit. No recursive agents.

Paths:
- P = `C:/Users/theis/Documents/Codex/rlgwo-execution-plan-20261008`
- A = `C:/Users/theis/Documents/Codex/pr42-rlgwo-closure-20261008`
- W = `C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget`
- Source/main target `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; W is reviewed4bccdf with identical tree35208181.
- Published audit evidence `b879573c298f19189d1f2392108b8b9f3b2cda0b` under `docs/rlgwo-audit/20261008`.
- New specification prefix `docs/rlgwo-execution/20261008`; placeholder `SPEC_EVIDENCE_COMMIT` only for links to this not-yet-published package. Source/evidence links must use actual immutable commits above. No private paths as sole evidence.

Reanchor complete: live26open exactly match prior audit, no changed bodies/new discussion/reopened closed issues/new issues. Only PR38 is open and remains excluded. Read current complete packets P/issues/NN.json and your accepted audit assessments, then relevant source/tests to fill actual missing decisions. Do not infer a defect from a missing native receipt. Preserve satisfied/superseded rows and attribute earlier implementation honestly.

User wants full issue-specific A–H execution specifications, not a generic gap list. For EACH assigned issue write:
1. P/REMAINING_RLGWOs/Rxxxx.md, complete self-contained work order.
2. P/comments/NN.md, substantive GitHub comment (may be same full text if within65536characters), exact heading `RLGWO remaining-work specification — Rxxxx — revision 1`; second line `Priority: Pn | Residual class: ...`. Stable marker `<!-- RLGWO-SPEC:18ff14860ff41c084b1db5f396bb62aa9c22b1be:Rxxxx:rev1:2026-10-08 -->`. Existing unversioned audit next-increment is parent; original body/proof is not overwritten. #33 startup successor revision1 remains the named sub-contract, not renamed.
3. P/metadata/Rxxxx.json, machine-readable inputs for DAG/coverage. Follow schema below.
4. P/workers/X/AUTHOR_REVIEW.md summarizing decisions, uncertainties and handoff for cold reviewer. Do not call READY yet; a different reviewer will cold-read. Mark `AWAITING_COLD_REVIEW` or `BLOCKED_EXTERNAL_HANDOFF` (#33).

## Required execution content

A Identity/objective: exact issue/body hash/amendments/source/evidence identities, observable closure result, accepted rows and residual row IDs. Demonstrated bug versus unverified evidence versus missing docs/platform/policy is explicit.
B Witness/recipe: exact retained witness or missing discriminator; input/time/zone/generation/cache/provider/timeout/browser/viewport/DPR/entry where relevant; concrete proposed steps and expected/observed; executed versus inspected versus proposed commands. Do not invent results or payloads as historical fact.
C Owners/interfaces: authored files/functions, actual generated/deployed consumers, precise consumed/produced state/interface, shared-file collision list, existing/repaired/new tests and builder ownership.
D Ordered bounded work: reviewable steps/output; binding signatures/state domains/algorithms. Unknowns get bounded competing hypotheses + measurements + decision rule. Documentation tasks enumerate exact sections/facts/limitations. Avoid speculative refactors.
E Scope/preservation: all existing accepted sky/star/V5/Sun/Moon/cloud/weather/prayer/settings/currentness/V1 boundaries; isolated data/profiles/clipboard; rollback/containment. No generated-first edits or PR38.
F Complete acceptance matrix: EVERY residual mandatory row -> explicit fixture -> actual consumer -> assertion/threshold -> environment -> expected -> evidence artifact -> independent gate. Include required positive/boundary/hostile/recovery/mutants; existing contract thresholds only, proposed new thresholds must be labelled/design-justified. Late still is not first-scene proof; VM is not native; generic asset recovery is not weather body/Image recovery. State precise closure certificate and necessary merge/public delivery gate. Reuse only unchanged interfaces/source/inputs; list affected regression set.
G Dependencies/cost: exact input interface/artifact and status/evidence; ranges of active person/agent effort and exclusive machine wall-time separately, confidence/basis. No all-issue dependency when verified interface suffices. Parallel read-only/docs drafts versus one shared source integrator and single heavy browser/terrain/performance queue. Apple native platform needs acquisition gate; no Linux substitution.
H Cold-read checklist: executor needs no prior transcript. Explicit missing owner/platform decision as gated task; no pretend readiness.

## Priority

No established P0/P1/P2 rubric found in current retained guidance; apply owner's local rubric: P0 demonstrated critical security/data-integrity/core-correctness failure or severe operational blockage; P1 substantial functionality/reliability/fidelity issue or significant closure-confidence gap; P2 bounded lower urgency docs/coverage/maintenance safely following. Current residual matters, not historic title. Provide per issue AND material sub-obligation priority, rationale/impact/conditions/exposure/confidence/containment/evidence; no artificial P0 quota. Execution order remains distinct.

## Machine schema (all fields required unless optional)

```
{
 "issue":2,"canonicalId":"R0002","revision":1,"author":"A",
 "sourceTarget":"18ff...","auditEvidenceCommit":"b879...",
 "bodySha256":"...","specPath":"REMAINING_RLGWOs/R0002.md","commentPath":"comments/02.md",
 "priority":"P1","residualClasses":["evidence","docs"],
 "priorityAssessment":{"rationale":"...","impact":"...","conditions":"...","exposure":"...","confidence":"...","containment":"...","evidence":["immutable URLs"],"existingLabelDeparture":"none or explained"},
 "readiness":"AWAITING_COLD_REVIEW",
 "acceptedObligations":[{"id":"exact audited row ID","status":"satisfied/superseded","evidence":["..."]}],
 "remainingObligations":[{"id":"exact audited row ID","parentText":"...","class":"evidence","priority":"P1","priorityRationale":"...","witness":"...","acceptance":[{"id":"R0002-A01","fixture":"concrete values","consumer":"actual function/browser","assertion":"...","environment":"...","expected":"...","artifact":"planned relative path","reviewGate":"independent reviewer ..."}],"nodeIds":["R0002-EVIDENCE"],"closureGate":"CLOSE-R0002"}],
 "nodes":[{"id":"R0002-EVIDENCE","issueObligations":["R0002:exact-row-ID"],"priority":"P1","kind":"evidence","owner":"prayer-evidence executor","scope":"...","sourceRevision":"...","inputs":[{"id":"accepted-prayer-record/v1","contract":"...","status":"SATISFIED","evidence":["..."]}],"outputs":[{"id":"r0002-native-proof/v1","contract":"...","artifact":"..."}],"entryCriteria":["..."],"exitCriteria":["..."],"tests":["verified/proposed commands"],"resources":["heavy-browser"],"sharedFiles":["..."],"dependsOn":[{"node":"...","type":"hard-interface/qualification","reason":"..."}],"estimate":{"activeHours":[1,3],"exclusiveMachineMinutes":[5,15],"confidence":"medium","basis":"..."},"status":"READY_PENDING_REVIEW"}],
 "closure":{"id":"CLOSE-R0002","requiresDelivery":true,"requiredOutputs":["..."],"conditions":["..."],"authority":"closure only after future executor authorization and actual required delivery"},
 "documentationFacts":[...],"affectedRegressionSet":[...],"reuseRules":[...],
 "sharedFileRisks":[...],"decisions":[...],"nonGoals":[...]
}
```

Use actual full SHAs (ellipsis above schema only). Preserve original residual row IDs; if a single audited row mixes sub-obligations, child IDs append `.a/.b` and retain parent linkage. Do NOT erase unverified final-proof rows just because they are gates: map them to qualification/closure nodes. Shared cross-issue DOC nodes can be proposed with exact content; primary will coalesce/reconcile before finalgraph. Do not independently allocate common global IDs except CLOSE-Rxxxx perissue.

Do not create production code or run costly proof. This is executable specification preparation, with commands marked verified syntax/source or proposed-not-executed. Independent cold-read and primary reconciliation precede publication.

## #33 external handoff boundary

Startup source thread01a11e50-a65e-7e30-a8e6-202f4490f31f owns `codex/celestial-startup-repair`, currently active/uncommitted. Document `docs/real-sky/CELESTIAL_STARTUP_RLGWO.md` revision1, S10 left hotspot/grey wash active. Primary coordinates messages and final intake. Do not implement, send uncoordinated requests or replace its spec. Preserve original callback-cost rows. F may draft structure/original residuals and exact handoff gates now; final#33spec waits for definite completed investigation/writeup and S10 disposition, not necessarily merge. No numerical lunar-only comparison can close whole-scene first appearance.
