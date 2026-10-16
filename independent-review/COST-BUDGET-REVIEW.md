# R0021 callback budget review

**Adopt before measurement:** candidate steady callback median and p95 may exceed the matched baseline by at most `max(0.25 ms, 10% of that baseline statistic)`. This implements the canonical proposal at lines 200–202; it is not an inherited numerical requirement or a measured PASS. No browser or cost measurement was performed by this reviewer.

Use four serial `A(5s), B(5s), B(5s), A(5s)` rounds per engine, with five seconds of actual-function warmup after each variant reaches the same admitted, quiescent state. Do not start that warmup while one side is still computing terrain or displaying a different lunar quality tier. Preserve every raw duration, count, exception, per-block median/p95 and retained-state inventory. Measure actual native scheduler/render/theme/commit owners, preserving their behavior and separating nested self-time from inclusive time.

Startup stays separate. The original Chromium `1000/250/80/250 ms` and Firefox `1500/400/80/400 ms` presentation budgets remain binding. Cost instrumentation and application publication cannot replace ordinary first-presentation evidence. Historical five-of-six strict timing failures, source-frame gaps and the missing extension parent remain open.

One baseline distinction must be explicit before running: canonical A01 names `18ff1486` versus the final integrated candidate. A comparison against current production `f270792f` establishes the incremental current-production claim; it cannot silently replace the canonical historical comparison or attribute all intervening changes to R0021. Bind the chosen claim and exact sources in the execution receipt.

The inventory must account for rAF ownership, pending jobs/workers, provider activity, listeners/timers, canvas/texture allocations, per-frame allocation sites and retained arrays/results. A new permanent controller or unbounded retention fails the structural obligation. Bounded initial work must be classified explicitly. Failed, noisy, missing-owner or unequal-state blocks are retained and return **INCOMPLETE**; at most one explained controlled repeat is permitted, with no threshold tuning.

The machine-readable decision and exact intake hashes are in [cost-budget-review.json](cost-budget-review.json). Root still needs to freeze the combined startup/H1 candidate and approve its native instrumentation/state-matching recipe before leasing measurement. This report grants no source, resource, release or closure authority.
