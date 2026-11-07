# R0017 governor guide: reviewed-candidate handoff

**Read-only support guide. No lifecycle command below was executed; no run-root or package file was changed.** Commands are for root to apply at the real transition after the candidate is ready. A local checkpoint, independent source review, branch/PR publication, merge, deployment, and issue closure remain distinct claims.

## 1. Current gaps to reconcile

The active ROADMAP names phases 1–3, but the inspected run root has no `phases/` directory. It does have `implementation-plan.md`, whose task checkboxes remain open. STATE is `IN_PHASE`; its ledger/Andon/residual tables are empty, occurrence resolution says `not-applicable`, and both standardization decisions are pending. These are current bookkeeping observations, not a claim that the actual source work is absent.

Before final audit, root must reconcile actual completed work and evidence into one phase spec per declared phase and the authoritative ledger. Preserve real failed attempts and the six independent draft findings. Do not invent past marker emissions or backdate evidence. An earlier structural validator PASS does not establish these terminal facts.

The installed internal-child resolver remains unavailable: it rejects the host's hashed governor directory identity. Do not claim `audit-assess`, `audit-andon`, or `audit-state` was loaded; do not repair/rename/symlink the installation to manufacture the route. Ordinary separately attributed independent review remains usable when it satisfies the actual independence/evidence contract.

## 2. Continuity receipt and ordinary progress updates — concrete limitation

**Run `--require-current-continuity` before a governed ledger mutation. That is a precondition, not a refresh.** The installed controller binds HEAD, Git tree, STATE hash, ROADMAP hash, invalidation, epoch, and Next action. Any STATE/ROADMAP edit makes the existing G0002 receipt stale; a commit changes its HEAD/tree binding too. Merely verifying the old receipt again cannot update it.

There is **no documented or implemented ordinary refresh/rebind operation in this installed package**:

- `claim-run.sh` lines 133–168 recompute those live bindings and require exact equality.
- `--resume-controller` creates `refs/implementaudit/continuity-receipts/<controller>/<epoch>` using `git update-ref` with an all-zero expected previous value (lines 143–145). It cannot replace changed G0002 bindings in the existing G0002 receipt.
- The supported CLI has current/invalidate/resume/verify/require, not refresh. A package-wide search found no ordinary refresh contract.
- `apply-observed-mutation.sh` checks currentness before effects (lines 674–702), but contains no post-mutation receipt refresh.
- `references/continuity.md` says an uninterrupted turn adds no boundary ceremony; new epochs belong to real compaction/session/handoff/manual-resume/context-gap boundaries.

Therefore **do not fabricate another compaction, label an uninterrupted bookkeeping edit as an invented context gap, delete/overwrite the receipt ref, or recycle G0002 through resume**. Checking before mutation does not make the next effect current afterward. This is an executing-controller bookkeeping limitation, not missing user authorization. Record the exact limited capability and keep dependent currentness claims/effects open if this gate cannot be truthfully satisfied. Independent inspection/evidence can still be preserved; a stale receipt is not a verified-current receipt.

A genuinely occurring manual/handoff resume can use the existing supported boundary protocol with its real provenance/event and next unused generation. That is recovery from an actual boundary, not an ordinary refresh workaround. Its order is: discover controller; separately invalidate the real boundary; read STATE and then ROADMAP in separate completed host actions; reconcile live state and write the truthful epoch/Next action; resume; verify returned receipt; require currentness. Do not batch those boundary reads or mint an epoch solely to make a stale hash pass.

The currentness check root may invoke before the next governed mutation is:

```bash
bash "$R0017_SKILL/scripts/claim-run.sh" --require-current-continuity r0017-explicit
```

If a real later manual resume exists, the supported calls are:

```bash
bash "$R0017_SKILL/scripts/claim-run.sh" --current-controller r0017-explicit
bash "$R0017_SKILL/scripts/claim-run.sh" --invalidate-continuity r0017-explicit --boundary manual-resume --event "$R0017_REAL_BOUNDARY_EVENT"
```

Read STATE and ROADMAP separately, reconcile/write the actual new epoch, then:

```bash
bash "$R0017_SKILL/scripts/claim-run.sh" --resume-controller r0017-explicit --boundary manual-resume --epoch "$R0017_NEXT_EPOCH"
bash "$R0017_SKILL/scripts/claim-run.sh" --verify-resume-receipt "$R0017_ACTUAL_RETURNED_RECEIPT"
bash "$R0017_SKILL/scripts/claim-run.sh" --require-current-continuity r0017-explicit
```

These calls are conditional documentation, not a recommendation to manufacture that boundary. Appending pending-terminal or final-marker data to a receipt-bound file has the same hash consequence.

## 3. Freeze the review subject and reconcile required records

Use the existing root; do not initialize another controller:

```bash
R0017_ROOT=/workspace/scratch/7a8daf93afaa/r0017-explicit-work
R0017_SKILL=/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58
R0017_RUN="$R0017_ROOT/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr"
R0017_BASE=f71fef6ccf7e4efcb57b5a26688d2360461a3253
R0017_CLOSURE="$R0017_RUN/final-audit.md"
R0017_PACKET="$R0017_RUN/handoff-packet.md"
cd "$R0017_ROOT"
```

Required records:

- Actual branch, baseline/head/commit-tree identities, complete tracked/untracked/local-only diff disposition; immutable candidate and file/evidence hashes.
- ES17-01–14 matrix: source/input bindings, actual commands, expected/observed outcomes, mutants, setup/history/exclusion limitations, and exact review attribution. Preserve original red and failed attempts.
- Phases/ROADMAP/STATE agree. Each completed phase has actual `IMPLEMENTAUDIT_PHASE_DONE` evidence; an owner-deferred phase has its actual owner/policy disposition.
- Every finding/Andon has its real class, cause, countermeasure and rerun evidence, anchored with the full commit SHA. Every consequential residual has an authorized non-`unresolved` disposition, named owner/policy and evidence. Decision-time `deferrals.jsonl` is append-only; do not reconstruct a fictional history at closure. `pending`/`unresolved` blocks completion.
- `AGENTS_UPDATE_DECISION`: `updated`, `not warranted`, or `OWNER DECISION`, with reason/scope/evidence. `CONTINUITY_DECISION`: `none`, `updated`, `deferred`, or `OWNER DECISION`, with reason/destination/evidence boundary.
- Existing authorization grants remain active: scoped source/tests/docs, branch commit/push, evidence comment and non-closing PR. The guide adds no merge/main-push/deployment/tag/release/issue-closure permission.

Complete working-tree readback commands, not just a last-commit diff:

```bash
git rev-parse "$R0017_BASE" HEAD 'HEAD^{tree}'
git rev-parse --abbrev-ref HEAD
git status --short --untracked-files=all
git diff --stat "$R0017_BASE"
git diff --check "$R0017_BASE"
git diff "$R0017_BASE" --
git ls-files --others --exclude-standard
```

The original mandatory command set is not yet fully enumerable from phase specs because those files are missing. Author the actual deduplicated set from the commission, implementation plan and recorded affected checks. It includes the instrument controls and retained smoke contract/transport checks; it does not authorize an inherited full campaign merely to fill a table.

## 4. Independent exact-candidate review

Use a genuinely separate reviewer over the frozen candidate, full diff and acceptance/evidence packet. The draft GAP-REVISE report is not a final PASS. A prospective cold-review record requires this exact attestation shape in a run-relative report:

```text
Reviewer attestation:
- reviewer_identity: <actual host/task identity>
- requested_model: <actual request>
- actual_model: <actually run model>
- authoring_context_reuse: no
- other_reviewer_output_seen: yes|no
- base_sha: <full lowercase 40-hex>
- head_sha: <full lowercase 40-hex>
Report state: FINAL
```

The report ends with one exact disposition token: `PASS`, `GAP-REVISE`, `BLOCKED`, or `OWNER DECISION`. Base/head are distinct resolving commits with base ancestral to head. Model identity matches STATE; do not guess an unavailable identity. Record in STATE:

```text
cold-review: disposition: <token> | attestation: <run-relative-report.md> | base_sha: <base> | head_sha: <head>
```

Relevant changes after review require affected re-review. The installed successor/non-verdict branch needs an absent source-side checker if actual `successor-review:` or `REVIEWER_RUNTIME_NON_VERDICT` rows occur; preserve truthful records and report that limitation. An ordinary substantive GAP-REVISE/revision cycle is not itself a runtime non-verdict.

## 5. Final audit commands and fields

At the real final-audit start, re-read ROADMAP from disk. Record `Skill version`, round number, total criteria count, deduplicated mandatory command list and baseline ref. Resolve package version rather than guessing; the last observed installed result was `unknown`:

```bash
bash "$R0017_SKILL/scripts/detect-env.sh" --package-version "$R0017_SKILL"
```

For each actual phase spec and deliverable:

```bash
bash "$R0017_SKILL/scripts/validate-phase.sh" "$R0017_RUN/phases/phase-N.md"
bash "$R0017_SKILL/scripts/repo-state.sh" deliverable "$R0017_BASE" <actual-deliverable-path>
```

Capture every mandatory command in full, producer exit and current verification anchor; expose a short excerpt. Label each check `re-verified` or justified `trust-prior`. If its anchor moved, prior evidence is usable only after the complete diff is proved disjoint from its declared surfaces. Record failures/hangs/timeouts/substitutions as Andons before disposition. No optional broad reruns are required beyond a concrete gate/risk.

The audit verification record contains per-phase done/blocked/missing, deliverable exists/nonempty/changed-since-baseline and command outcomes. Print:

```text
re_verified / (re_verified + trust_prior) = <fraction>
```

If trust-prior exceeds 30%, record the prescribed warning. A blocking gap gets a bounded `audit-fix-<round>.md` or an honest qualifying handoff, not a weakened success criterion.

Use `templates/final-report.md` for the closure record. At minimum give a bounded verdict (`proven`, `proven with deferrals`, `blocked`, `unverified`), findings, changed files, Smoke A/B, Andon/Hansei, commands/exits, residuals and authorization/evidence boundaries. One source-surface claim suffices for source-only claims; publication needs its own surface evidence. Canonical machine rows use:

```text
claim: <id> | surface: source | status: verified|failed|unverified|not-applicable | evidence-surface: source
```

The human claim table additionally names target/version, structural/behavioral/provenance property, evidence IDs, residual disposition reference and explicit non-claims. Full/N-of-N claims require full capture, defined population, population size, examined count and an actual enumeration source.

Exact qualification fields (one each, column zero):

```text
AUDIT_START_ANCHOR: <full start commit>
AUDIT_VERIFY_ANCHOR: <full current HEAD>
REANCHOR_DISPOSITION: unchanged|per-finding
REANCHOR_EVIDENCE: none|structured-rows
equivalent_config_attempts: <total>/<passing>
stochasticity_budget: none|<predeclared positive integer>
terminal_qualification: QUALIFIED|PROVISIONAL
```

Equal anchors use `unchanged`/`none`. Moved anchors need one hash-bound reanchor/residual row per claim, exactly as the final-report template specifies. Count real equivalent-configuration attempts: do not reset retries to `1/1`. Numeric budgets also require `stochasticity_budget_anchor` and `stochasticity_budget_path`, with the exact budget line already present in that tracked file at the start anchor. Omit those two fields for `none`.

A qualifying lesson gets one `Lesson-lift:` record covering observed lesson, lift/no-lift reason, destination, required authority, encoding written, observed activation, applicable installed-copy status, targeted class and future-prevention evidence explicitly unavailable. An active deterministic-test destination names the target, `enforcement state: ACTIVE`, and an actual nonzero red exercise plus observed passing activation; do not claim future recurrence prevention. A non-qualifying one-off may use a reasoned `No-lift:` line.

Run the installed final checkers with all applicable inputs:

```bash
bash "$R0017_SKILL/scripts/check-lesson-lift.sh" "$R0017_CLOSURE" --repo-root "$R0017_ROOT"
bash "$R0017_SKILL/scripts/check-closure-surface.sh" "$R0017_CLOSURE" --steer-dir "$R0017_RUN"
bash "$R0017_SKILL/scripts/validate-run-root.sh" "$R0017_RUN"
```

Add `--superseded-plan <path>` once for every replaced plan and `--plan-cycle-record <path>` once for every cycle-accounted plan. STATE currently says none; keep that only if true. `--steer-dir` is mandatory for this run-backed audit. Run-root validation is immediately before any legitimate completion transition. The source-only `scripts/check-marker-order.sh` is not shipped here; check transcript order against the installed reference rather than claiming that source-repository validator ran.

## 6. Authorized publication and receiver packet

Before an authorized branch push, use the actual authorization/invocation records:

```bash
bash "$R0017_SKILL/scripts/check-authorization-binding.sh" --auth "$R0017_RUN/authorization-record.md" --invocation <actual-invocation-record> --state "$R0017_RUN/STATE.md"
bash "$R0017_SKILL/scripts/check-closure-surface.sh" --automatic-effects "$R0017_ROOT" push <exact-branch> <actual-mutation-plan>
```

The mutation plan needs one ordered row:

```text
automatic-effect-preflight: event: push | ref: <branch> | workflows: <sorted-paths|none> | effects: <sorted-direct-effects|none> | post-state-readback: <sorted-readbacks|trigger-read-only> | excluded-outcomes: <truthful-list|none>
```

Read back the pushed SHA, non-closing PR (`Implements #23`), and evidence comment independently. The mutator's response is not readback. Verified publication rows must follow `references/repo-state-comparison.md` external mutation/grant and digest-binding grammar: separate target-bound mutation/read-only commands and evidence IDs, observed zero exits, contained hash-bound JSON, top-level readback field, matching expected/observed/parsed scalar, and the actual source grant. Preserve uncertainty rather than retrying a possibly completed external effect blindly. Do not infer merge, deployment or issue closure from publication.

For a machine-inspectable handoff packet, identity fields are mandatory: `packet_id`, `packet_version`, SHA-256 `packet_content_hash` over bytes excluding that hash line, and `sender_run_id`. Include actual branch/clean state, immutable commit and actual Git-tree identity, owner acceptance verbatim, current-state/provenance references and pending-effect disposition.

**Helper mismatch:** its field `claimed_tree` is compared to `git rev-parse HEAD` (commit), not `HEAD^{tree}`. Document that actual implemented meaning and preserve the true tree hash separately in the identity record. A PASS from this helper alone does not prove the Git-tree object or dirty overlay.

The receiver invokes:

```bash
bash "$R0017_SKILL/scripts/check-handoff-packet.sh" "$R0017_PACKET" --repo-root "$R0017_ROOT"
```

If the receiving continuation requires independent reproduction/re-adjudication, the **receiver** adds `--receiver-requires-reproduction`. Then `handoff_state: READY` requires these literal availability fields to be backed by actual supplied records:

```text
implementation_identity_present: yes
frozen_denominator_present: yes
acceptance_oracle_present: yes
reproduction_inputs_present: yes
evaluator_schema_semantics_present: yes
prior_evidence_present: yes|not-applicable
rejected_non_evidence_present: yes|not-applicable
authority_stop_boundaries_present: yes
exact_handoff_receipt_present: yes
```

Also require substantive values—not yes/no/unknown placeholders—for `current_state_ref`, `provenance_ref`, `pending_effects_disposition`, `authority_capability_ref`, `discrepancy_state`, and `receiver_live_verification`. A sender must not claim the receiver has already verified when it has not.

## 7. Choose the honest terminal path

- **Bounded candidate object actually complete:** only after all its required source/review/publication obligations and gates are satisfied, all consequential residuals properly disposed, coverage shown and currentness truthful, emit `AUDIT_COMPLETE` then `IMPLEMENTAUDIT_RUN_COMPLETE`. This closes the bounded audit object, not merge/deployment/issue closure.
- **Required gap remains, qualifying dependency/tool/authority blocker, no bounded countermeasure, or owner-requested early handoff:** emit `AUDIT_HANDOFF`; include exact blocker, retained candidate/evidence, pending effects and smallest next action. It must not coexist with `IMPLEMENTAUDIT_RUN_COMPLETE`.

Record the true STATE status and emitted terminal marker as its final nonblank line. A terminal action must have its actual `PENDING_TERMINAL` command/preconditions recorded and be cleared only after success. Do not replay an already-emitted completion marker in the later user summary. The mere use of the word “handoff” in prose does not decide the terminal marker; remaining in-scope obligations do.

## Sources and inspection boundary

Read the active PROTOCOL final-audit, authorization, lesson and handoff sections; active STATE/ROADMAP/implementation plan; installed SKILL runtime/trace rules, continuity and review contracts, final/child templates, handoff checker, and targeted final-checker/currentness implementations. No validator or lifecycle effect was executed. Package routing failure and version observations are from the earlier read-only readiness report. The claim that no ordinary refresh exists is based on the complete controller command switch and targeted package-wide search, not a live mutation experiment.

Inspected at 2026-11-07T03:57:57.981816+00:00. Key source hashes:

- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr/PROTOCOL.md` — SHA-256 `4fcbc5d99c0ce1f1d6a6a1544b9f937eaa97acbc5009cfad62ede4474b4925ce`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr/STATE.md` — SHA-256 `813917a313cbca6236477b829cefe2bc5671bc7b7bd85d629f0ea4a4c1851970`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr/ROADMAP.md` — SHA-256 `9056b9b4c5d817930f277e234f6f5432d0955985bcec35bc47d1a8ee92c644ed`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr/implementation-plan.md` — SHA-256 `c186ce97ffa3d2dbfc5f73671fca7c24bd580c99434c55497a50dbdb3034230c`
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/claim-run.sh` — SHA-256 `9c9945fdf650c72b8019f0dd908fff360162cc11ae7eb3197ccafe0f6ab3730f`
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-handoff-packet.sh` — SHA-256 `72a04a5311c988da1e745fdb368d95ac0125124919185bf0b87432c4c2b60ffc`
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-closure-surface.sh` — SHA-256 `ba994fed1fb6c5d4688627bd31a577e7ce6fec5f6214fa3cc1093c9b70337ed7`
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-lesson-lift.sh` — SHA-256 `d73a873b63fe4efc7a5dadcc7b45043b68242c0afedbae6b5eb6cdf6a2630e9a`
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/references/continuity.md` — SHA-256 `32813ccfdb15463d6f0230c147606bb48fedc1838f18d36171c523502f03070f`
