# Normal-clock lunar refinement availability

This follow-up addresses the Firefox preview starvation found while qualifying
the rim correction. It changes native geometry-cache precision and closes a
publication-time seek gap. It does not change the WASM kernel, terrain, material,
Earthlight, angular refinement rules, native UTC, or CP9 sky-age limit.

## Failure and discriminating controls

The actual Pages-shaped 330×534 iframe ran at normal 1× from a controlled
2026-10-07T20:30Z anchor, with Madinah settings and provider/font fixtures.
The unmodified phase policy used .0004-radian Sun-angle buckets at every DPR.
The native phase was updated at approximately 60-second intervals; the Moon
host polled every 250ms. In the Firefox trace, bucket 6406 became 6407 at
120.009s, then 6408 at 240.016s. Generation 0 and the native scene identity
`24.47|39.61|Asia/Riyadh|wall` remained unchanged. Each crossing withdrew the
preview, incremented the Moon epoch, and cancelled the pending full refinement.
The first cancellation occurred 118.964s into the worker, at lighting row
508/540 in its 1024-source pass. These were phase-key cancellations, not seeks,
worker failures, hidden state, or a failure of the sky-age fence.

Chromium completed the first identical waning target in 37.956s, before the
same 120-second crossing. Firefox's repeated preview publications were therefore
not evidence of final availability. Timer observation was additive: the worker
used its original scheduling; waits accounted for about 7 seconds of the first
119-second Firefox attempt. No timer-clamp workaround is claimed as the fix.

`moon_clock_trace.py` records render/cancel messages, native UTC and scene,
accepted sky UTC, raw phase, canonical bucket and quantum, epoch, preview/final
admission, worker progress and elapsed/yield time. A held-phase diagnostic must
also specify waxing/waning: the first held control used the wrong default
orientation and is excluded from same-target timing claims. Its receipt is
retained rather than silently relabelled.

The corrected matching waning control used the exact original physical target
and original runtime inventory. It completed in Firefox in 136.371 seconds of
worker time (137.504 seconds from entry). The target was viable; supersession
at 118.964 seconds prevented its publication in the unheld sequence.

With the corrected policy, the five-minute Firefox trace publishes a final
`empirical-adaptive` result at 139.454 seconds, with no phase cancellation during
the trace. The only cancellation is native scene initialization before any job.
The independent actual-iframe scenario passes at 139.453 seconds in Firefox and
39.797 seconds in Chromium. Both pass prayer readiness, real 1× countdown/sky UTC
advancement, date/settings interaction during refinement, retry and V1 isolation.

The new component regression replays the observed phase sequence with a slow
worker. It fails against the original host at 120s and passes after correction.
A second negative control demonstrated that an identical-geometry stale result
could publish immediately after a seek but before the next poll. Result
admission and surface reads now check clock continuity too.

## Fixed precision budget, measured footprint

The existing policy allowed at most **0.0416 device pixel** of spherical
terminator displacement at diameter 416. That budget is retained, not enlarged.
For angular error `da`, rotating a point on a sphere of displayed radius `D/2`
moves it at most `D*sin(abs(da)/2) <= D*abs(da)/2`. Nearest angular quantization
has `abs(da) <= q/2`, so choosing `q = 4*0.0416/D` preserves the same budget.
The independent test evaluates the rotation/chord bound and `D*abs(df)` across
20,001 phases at seven diameters, including endpoint clamping.

The host measures the enclosing `.mphoto` rectangle, multiplies by native DPR,
and rounds its maximum dimension upward. The image encloses the disc, making
the bound conservative. The quantum is capped at .0016 radians for footprints
smaller than 104 device pixels. Missing geometry uses the old 416-pixel policy.
The actual normal iframe measures 107 device pixels at DPR 1, giving
q=0.0015551401869158877. The same policy runs in every browser.

This is a geometric/display-position bound, **not** a proof bounding every
terrain shadow or photometric sample. Full terrain, cast-shadow and adaptive
quality evaluation still run at the chosen canonical geometry. No future UTC
is rendered or labelled current: canonical geometry is explicitly identified,
and native UTC continues to advance independently. Diagnostics disclose raw
fraction, quantum, bucket, measured diameter and current target error bound.

## Currentness and scope

Scene equality still includes generation, native scene identity, waxing/waning,
DPR, profile, explicit reference scene and now the measured diameter. Phase
crossings outside the display budget still cancel. Explicit forward/backward
seeks, A→B→A generations, native invalidation, hidden/paused/disposed state,
profile/reference changes and worker failures retain immediate withdrawal.
The 240-second refinement deadline and CP9's 30-second sky-age limit are unchanged.
Normal phase progression cannot permanently freeze the target.

Rollback before publication is the bounded follow-up diff on PR #40. After
publication, an owner-directed revert would preserve the frozen V1 escape hatch;
this work never rewrites V1. Qualification results and the final runtime identity
are recorded with the rim report. Historical N001/N002 PARTIAL and N003 BLOCKED
states remain unchanged.
