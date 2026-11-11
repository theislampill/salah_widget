# R0013 native run 4: first-command timing and test-only correction

## Finding

The complete installer entry receipt has **24 passing cases**: 12 on Windows
PowerShell 5.1.20348.5773 and 12 on PowerShell 7.6.6, including normal and NoOpen
controls. Both deliberate invalid-option cases exit before readiness; the other
22 cases have the required readiness nonce. The aggregate collector says FAIL
because the separate PowerShell 5.1 no-installer diagnostic timed out. These are
different evidence scopes.

All four PowerShell 5.1 diagnostic variants stop after `script-enter` and
`join-path-begin`, including `native-only`. The delay therefore is not specific
to the private Utility wrapper's export configuration. The underlying Windows
cause remains unresolved. No installer timeout, staging algorithm, compiler
initialization or product assertion was changed by this worker.

The source measured in run 4 is R0013 commit
`f2161ed6a1fe2e0647ee541487ab1ac792d4d3df`, installer SHA-256
`56d91d484643b82a72e5714c678d2fe8640eb2b66e1d5350dd59889924d62471`.
These receipts are not rebound to a later R0015 source.

## Evidence and timing limits

[archive-timing.json](archive-timing.json) binds the original ZIP, its embedded
tar, the extracted tar, collector JSON, entry JSON and diagnostic JSON. It also
retains exact archive member names, hashes, fractional PAX mtimes, phase content
and all 24 per-case intervals. The ZIP's embedded tar is byte-identical to
`Windows.tar.gz`, SHA-256
`0dd1e25539080f226f5567526250a9afb897b4c8eda3b380eed6f3428d8f4a2b`.

| Host / case group | Before-snapshot to readiness | Readiness to after-snapshot |
| --- | --- | --- |
| PS5.1, 11 cases reaching readiness | 19.615–22.770 seconds; median 19.687 | 0.078–0.564 seconds |
| PS7.6.6, 11 cases reaching readiness | 0.470–0.563 seconds; median 0.484 | 0.094–0.531 seconds |

For PS5.1 GitHub preview, the archived before snapshot is
`07:49:17.437272 UTC`, readiness is `07:49:40.207728 UTC`, and the after snapshot
is `07:49:40.411057 UTC`. For its normal positive case the corresponding times
are `07:52:20.384683`, `07:52:40.072133`, and `07:52:40.635844 UTC`.

These are filesystem timestamp envelopes. The after snapshot was produced after
process completion and output handling; its mtime is not an exact process-exit
timestamp. The old diagnostic writes its `before.json` after waiting for its
child, so that file's mtime must not be used as a launch time. Old phase files
contain names without individual timestamps; their mtime describes the last
append only.

The four PS5.1 diagnostic module-analysis-cache files were written
13.108–13.193 seconds after their last recorded phase, before the 15-second
kill. This shows preparation activity during the wait. It does not establish
that cache work caused the delay, that the foreground command was making
progress, or a particular Windows mechanism.

The full native entry collector command ran from `07:49:17.327891` to
`07:53:09.880837 UTC`: **232.552946 seconds**. Its 240-second outer limit left
only **7.447054 seconds**, or 3.10% of that limit. Its successful first PS5.1
case also consumed approximately 23 seconds of the former 25-second case
window. The shorter 15-second diagnostic could not observe the later return
seen in the complete-entry run.

## Frozen no-installer correction

`../r0013-native-bootstrap-timing.ps1` is a new derivative of the unchanged
`ae274fa5...` probe. Its SHA-256 is
`a553c9790f04c34ddbe672b469e157ddf6c5d4903484b1f3b17eb82bd2f86510`.

```powershell
HOST -NoProfile -File .\r0013-native-bootstrap-timing.ps1 `
  -SourceFile .\install.ps1 -OutputRoot $env:RUNNER_TEMP `
  -ChildTimeoutSeconds 60 -VariantSet Minimal
```

Replace HOST with the actual selected executable. Minimal performs four
launches: native-only cold/warm and private-wildcard cold/warm. A cold child has
a new owned USERPROFILE and module cache. Its warm partner is a new process
reusing exactly those paths. Reuse after an incomplete cold child is explicitly
labeled; it does not become evidence of a completed warm baseline.

Every child phase is still a direct .NET append, so phase instrumentation does
not introduce an earlier cmdlet lookup. Records contain UTC, within-child
monotonic ticks and frequency, PID, nonce and phase. Parent launch, process
creation, first observed readiness, terminal observation and monotonic elapsed
times are retained. Before snapshots are now written before launch. Results
are written per child and incrementally, preserving useful evidence even if
the outer collector is interrupted.

The original successful-exit/readiness/completed-script assertions remain.
Phase identity and monotonic data are validated; module-phase interleaving is
recorded rather than invented as a new product requirement. Child deadlines
remain bounded, with a five-second kill grace and two seconds per output pipe
to drain. No installer is invoked.

## Versioned R0016 budget library

`../install-preview-acquire-timed.ps1` has SHA-256
`b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1`.
The original `ed07186c...` library is unchanged. The new library retains the
effect assertions and extends only child-launch timing, deadline/drain handling
and evidence fields. Its imported child launcher defaults to 60 seconds; an
explicit `SALAH_TEST_CHILD_TIMEOUT_SECONDS` value from 30 through 180 may select
another reported bound.

Use the frozen R0016 core with the new library explicitly:

```powershell
HOST -NoProfile -NonInteractive -File .\install-preview.ps1 `
  -SourceFile .\install.ps1 -OutputRoot $env:RUNNER_TEMP `
  -FixtureLibrary .\install-preview-acquire-timed.ps1 -Suite All
```

The R0016 core itself remains SHA-256
`e4b1ba795650bc9b737faaf79c535f7cbfb989160152ca65abd47ebc0bae9a3b`.
It records the actual imported library hash. This timing change does not
establish OS containment or native Windows qualification.

## Collector budget proposal

| Scheduled carrier | Proposed bound / decision |
| --- | --- |
| Minimal cold/warm diagnostic on one host | 60 seconds per child; collector 360 seconds. Explicit launch/kill/drain arithmetic is `4 × (60 + 9) + 30 = 306` seconds. |
| Standalone full no-installer acquisition library | Seven children plus native capability acquisition; collector 600 seconds is a bounded receiving envelope. |
| Future required 24-case full native installer carrier | 60 seconds per actual case and collector at least `24 × 60 + 120 = 1560` seconds. This covers the chosen case ceilings and collection allowance; it is not a request to rerun unchanged R0013 suites. |
| R0016 core `Helpers` | 62 child launches, including per-context no-installer baselines and four controls. Use native cold/warm measurements to schedule it. |
| R0016 core `Wrapper` or `Mutants` separately | 32 launches each. Each retained source/context still receives its required baseline. |
| R0016 core `All` | 118 launches. If each cold owned profile costs about 20 seconds and reuse is fast, expect roughly 20 minutes on PS5.1; if reuse is also slow, roughly 40 minutes. These are conditional scheduling estimates, not measured native core runtimes. |

Do not reuse the fixed 240-second collector budget for these different
denominators. For a strict ceiling that allows every core launch to reach its
selected deadline, the upper budget formula is `N × (child bound + 9) +
collection allowance`. Batching the existing named suites makes interruption
and artifact collection easier. The minimal native timing run should precede
the decision about an All run. Useful Apple publication/qualification does not
depend on that Windows scheduling experiment.

For subsequent actual `-File` receipts, the parent-owned harness should record
monotonic launch, first observed valid final nonce and terminal exit times,
alongside UTC and PID. Keep the installer as the actual native `-File` target,
keep readiness after all spies are exported, and retain the exact nonce check.
No-readiness timeout, timeout after readiness, and product assertion failure
must retain distinct classifications. Do not infer these timestamps
retroactively from the old mtime envelopes.

## Bounded local verification

Both new files parse cleanly on local Linux PowerShell 7.6.6. The minimal timing
probe completed all four cold/warm rows with matching identities and preserved
phase order. The imported library controls passed default-60-second and
explicit-30-second launches. An actual 30-second owned no-installer timeout
retained its pre-wait phase and drained output and was correctly classified as
`BOOTSTRAP_BLOCKED_TIMEOUT`.

Receipts are `parse-receipt.json`, `probe-local-mechanics.json`, and
`library-local-mechanics.json` in this directory. These verify fixture mechanics
only; no native Windows result is fabricated. All original failed 15-second
receipts and all earlier installer timeout receipts remain intact.
