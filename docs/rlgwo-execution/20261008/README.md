# Salah remaining-work execution package

This package continues the completed 37-issue audit. It specifies the remaining **26** open work orders; it does not implement them or close them. Eleven justified closures remain preserved. The delivered runtime is `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; prior audit evidence is documents-only commit `b879573c298f19189d1f2392108b8b9f3b2cda0b`.

Start with [priorities](PRIORITIES.md), [execution graph and schedule](CLOSURE_DAG.md), [startup/glow handoff](STARTUP_HANDOFF.md), and the [third-thread launch prompt](THIRD_THREAD_EXECUTION_PROMPT.md). The graph plans original residual rows plus explicit owner amendments. Follow each linked [issue specification](REMAINING_RLGWOs/) and its actual original contract; a graph node is not permission to weaken one.

## Package navigation

| Artifact | Purpose |
|---|---|
| [INVENTORY.json](INVENTORY.json) | Complete live issue-only planning inventory and intervening-change check |
| [BASELINE_OBLIGATIONS.json](BASELINE_OBLIGATIONS.json) | 111 original residual parent rows and 280 accepted/superseded rows retained from the completed audit |
| [PRIORITIES.md](PRIORITIES.md) | Sorted priority table and issue/material-child reasoning, confidence and containment |
| [CLOSURE_DAG.json](CLOSURE_DAG.json), [Mermaid](CLOSURE_DAG.mmd) | Exact nodes/interfaces, typed dependencies and distinct resource constraints |
| [OBLIGATION_COVERAGE.csv](OBLIGATION_COVERAGE.csv) | Remaining parent obligation → execution nodes → evidence → closure gate |
| [SCHEDULE.json](SCHEDULE.json) | Structural paths, ready-after-intake candidates and resource demand; not an elapsed-time promise |
| [STARTUP_HANDOFF.json](STARTUP_HANDOFF.json) | Active startup source/PR/runtime, exact qualified and unresolved scope, acknowledged ownership |
| [OWNER_AMENDMENTS.md](OWNER_AMENDMENTS.md) | Current-model precipitation and named startup/L1 contract changes, without rewriting originals |
| [REVIEW_RECONCILIATION.md](REVIEW_RECONCILIATION.md) | Six author/cold-review assignments, material findings, corrections, primary reconciliation and package review |
| [SPECIFICATION_READINESS.json](SPECIFICATION_READINESS.json) | Per-issue independent cold-read and publication readiness; distinct from runtime completion |
| [NODE_LEDGER.json](NODE_LEDGER.json), [ISSUE_LEDGER.json](ISSUE_LEDGER.json) | Resumable planning/execution boundary and individually linked publication/disposition |
| [PUBLICATION_LEDGER.json](PUBLICATION_LEDGER.json) | Actual issue-comment revision, readback and final state; no issue state changed by planning |
| [MANIFEST.json](MANIFEST.json) | Exact package bytes; excludes itself and its detached digest to avoid self-reference |
| [DAG_VALIDATION.json](DAG_VALIDATION.json), [negative controls](DAG_NEGATIVE_CONTROLS.json) | Fresh planning-only structural/coverage validation and intentionally failing controls |

## Reuse and effects

The six Sol6.1/max reviewers are recorded in [REVIEWERS.json](REVIEWERS.json), with requested settings distinguished from client-confirmed configuration. An independent cold read qualifies a specification's executability; it does not execute its future native tests or approve a production release.

Source/evidence links to prior commits are immutable. New package-internal links are relative to the containing file, so they resolve within whichever immutable package commit was selected. Absolute source and actual published issue-comment links remain intact. `PUBLICATION_TRANSFORMS.json` records mechanical link binding and readiness stamping; it does not replace the reviewed source hashes. The third executor must record the immutable package commit as `SPEC_SHA`.

Future product execution requires the owner to launch/approve the supplied prompt. Each new merge/deployment requires a separate exact-head approval. Required actual delivery precedes completed issue closure. Evidence-only work may qualify an unchanged delivered consumer without a fictional runtime rewrite. Resources and existing ownership are in [RESOURCE_AND_AUTHORITY.md](RESOURCE_AND_AUTHORITY.md).

Use an isolated output directory when revalidating; never overwrite historic receipts:

```text
python tools/verify_manifest.py --root <package-root>
python tools/validate_execution_plan.py --root <package-root> --output <isolated-output>/DAG_VALIDATION.json
```

No production runtime, frozen V1, PR38, real browser profile, clipboard or machine clock is modified by this documentation programme. Partial scientific/platform qualifications remain mapped to their own obligations, not generalized into unrelated blockers or silently closed.
