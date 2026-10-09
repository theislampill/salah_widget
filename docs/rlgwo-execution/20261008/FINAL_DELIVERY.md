# Completed planning publication and execution handoff

All 26 remaining-work specifications are complete, independently cold-read, reconciled and published with full readback. The original 11 closures remain preserved; all 26 specified issues remain open. No issue state, production source, frozen V1 or PR38 was changed. No new issue appeared during the final full inventory readback.

The immutable specifications were first published at `845e4ab9f26efec6278682e72a64e656f807bb39` on `codex/rlgwo-closure-audit-20261008`. This follow-up package adds actual issue-comment receipts and final ledgers; it does not revise the binding specifications or graph. Delivered runtime/main remains `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; audit evidence remains `b879573c298f19189d1f2392108b8b9f3b2cda0b`. Select the immutable commit containing this final package as `SPEC_SHA`.

Start the third thread with [THIRD_THREAD_EXECUTION_PROMPT.md](THIRD_THREAD_EXECUTION_PROMPT.md). That file is the complete proposed owner launch authorization for bounded execution, proof and eligible closure. New production merges/deployments require separate exact-head approval. This planning publication itself does not launch product work.

## Published specifications, sorted by current residual priority

P0: 0; P1: 21; P2: 5. The full [priority table](PRIORITIES.md) contains per-issue and material-child rationale, severity, evidence confidence, exposure, containment, owner, exact prerequisites and resource/effort estimates. The order is a risk tie-breaker; resource availability and hard interfaces control actual execution.

| Issue / ID | Priority | Residual class | Planning readiness | Published comment |
|---|---|---|---|---|
| #24 / R0018 | P1 | demonstrated-bug, evidence, docs | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/24#issuecomment-6074560523) |
| #33 / R0021 | P1 | demonstrated-bug, evidence, external-handoff, platform | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/33#issuecomment-6074561470) |
| #34 / R0022 | P1 | evidence, demonstrated-bug, design-decision | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/34#issuecomment-6074562566) |
| #36 / R0024 | P1 | implementation, evidence, docs, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/36#issuecomment-6074563547) |
| #2 / R0002 | P1 | docs, evidence, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/2#issuecomment-6074564331) |
| #3 / R0003 | P1 | evidence, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/3#issuecomment-6074565259) |
| #4 / R0004 | P1 | docs, evidence, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/4#issuecomment-6074566216) |
| #6 / R0006 | P1 | docs, evidence, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/6#issuecomment-6074567030) |
| #7 / R0007 | P1 | evidence, docs, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/7#issuecomment-6074567851) |
| #32 / R0020 | P1 | evidence, documentation, qualification | READY with explicit execution gates | [revision 2](https://github.com/theislampill/salah_widget/issues/32#issuecomment-6074568802) |
| #8 / R0008 | P1 | evidence, documentation, qualification | READY with explicit execution gates | [revision 2](https://github.com/theislampill/salah_widget/issues/8#issuecomment-6074569920) |
| #11 / R000B | P1 | evidence, docs, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/11#issuecomment-6074570594) |
| #12 / R000C | P1 | evidence, docs, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/12#issuecomment-6074571322) |
| #13 / R000D | P1 | evidence, docs, qualification | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/13#issuecomment-6074572185) |
| #17 / R0011 | P1 | docs, evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/17#issuecomment-6074572966) |
| #35 / R0023 | P1 | docs, evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/35#issuecomment-6074573673) |
| #19 / R0013 | P1 | platform-qualification, evidence, documentation | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/19#issuecomment-6074574717) |
| #21 / R0015 | P1 | platform-qualification, evidence, documentation | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6074575663) |
| #22 / R0016 | P1 | platform-qualification, documentation | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/22#issuecomment-6074576487) |
| #23 / R0017 | P1 | evidence, docs | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6074577280) |
| #37 / R0025 | P1 | evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/37#issuecomment-6074578091) |
| #20 / R0014 | P2 | documentation | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/20#issuecomment-6074579192) |
| #16 / R0010 | P2 | docs, evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/16#issuecomment-6074580058) |
| #25 / R0019 | P2 | evidence, documentation, conditional-platform-qualification | READY with explicit execution gates | [revision 2](https://github.com/theislampill/salah_widget/issues/25#issuecomment-6074580883) |
| #27 / R001B | P2 | documentation, rendered-delivery-evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/27#issuecomment-6074582227) |
| #28 / R001C | P2 | documentation, fixture-coverage, diagnostic-consumer-evidence, rendered-delivery-evidence | READY with explicit execution gates | [revision 1](https://github.com/theislampill/salah_widget/issues/28#issuecomment-6074583092) |

## Planning proof and remaining execution gates

- The [JSON DAG](CLOSURE_DAG.json), [human schedule](CLOSURE_DAG.md) and [Mermaid graph](CLOSURE_DAG.mmd) agree: 213 nodes, 409 typed edges, no cycles or dangling dependencies. [Coverage](OBLIGATION_COVERAGE.csv) retains 111 original residual rows plus the named R0022-L1 amendment; [acceptance detail](ACCEPTANCE_COVERAGE.csv) has 189 rows. All 280 accepted/superseded parent rows remain preserved.
- [Structural validation](DAG_VALIDATION.json) passes. All 11 intentional graph defects are rejected by [negative controls](DAG_NEGATIVE_CONTROLS.json). The actual staged reference scan checks 1,379 immutable references to 139 distinct historical targets plus package-relative links; the final scan additionally checks published-input and delivery links. This proves reference availability and line ranges, not future runtime outcomes.
- Six actual `gpt-6.1-sol` / `max` reviewers authored disjoint sets, then different reviewers cold-read each set. [Client configuration receipts](REVIEWERS.json) distinguish requested and confirmed settings. [Review reconciliation](REVIEW_RECONCILIATION.md) includes findings and fixes; C independently reviewed the joined package and the focused reference-checker correction. No external human review or new product campaign is claimed.
- [The startup handoff](STARTUP_HANDOFF.md) is definite and acknowledged for planning, while implementation remains active in its original thread. Its measured Chromium first-scene budget failures, final Firefox/extension-parent/callback proof and final source publication are open. The left-side lunar atmospheric hotspot is attributed; R0022-L1/S10 full-scene correction/acceptance remains distinct from lunar RGB equivalence. The graph consumes this active thread's eventual exact result without duplicating it.
- Acquire native Apple Bash 3.2/macOS access early; preserve unavailable-host evidence gates. Reserve one heavy browser/terrain/performance queue, respecting the startup lease. The structural path envelope is 9.5–22.25 active hours, with 527–1,337 minutes of uncoalesced exclusive-machine demand; these are planning estimates, not elapsed-time promises, and exclude unbounded host/owner waits. Ready low-impact docs work can proceed in parallel.
- N001/N002 PARTIAL and N003 BLOCKED remain scoped to their actual obligations. Approved current-model precipitation remains explicitly distinct from observation. No extra upstream nowcast or V5 research programme is authorized.

## Actual publication and readback

[PUBLICATION_LEDGER.json](PUBLICATION_LEDGER.json) links all 26 exact comments; [FINAL_ISSUE_READBACK.json](FINAL_ISSUE_READBACK.json) records all 37 final issue states and discussion comparisons. [PUBLICATION_APPROVAL.json](PUBLICATION_APPROVAL.json) binds each approved comment body. The `publication-inputs/` bodies and `publication/` per-issue receipts retain the exact externally published effects. Retries look up stable issue/revision markers before posting.

The publisher performed a source/body/discussion/state precheck, individual comment POST, complete comment GET, and final main/issue/discussion readback for each issue. It has no close/reopen/label/PR mutation path. The documents commit used an isolated Git index, exact origin/parent/main guards, a normal append-only push and readback; the reviewed checkout stayed unchanged.

Executed environment: Windows PowerShell, installed Python 3.11 standard library and GitHub CLI. Python tooling ran with `PYTHONUTF8=1`; an initial local preparation attempt under cp1252 stopped on decoding before any issue effect, then resumed idempotently with UTF-8. No runtime, browser, scientific or native Apple qualification was rerun by this planning stage.

The commit that contains this file is the final specification package identity. Verify its [manifest](MANIFEST.json), then use the launch prompt and resumable [node](NODE_LEDGER.json) / [issue](ISSUE_LEDGER.json) ledgers. Implementation, qualification, review, delivery and closure remain separate completion events.
