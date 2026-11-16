# Moon refinement reuse and scheduling: feasibility assessment (2026-11-16)

Research only, under the owner directive of 2026-11-16 (sections 3 and 5). Nothing here changes the product: no
cross-tab storage, no change to the refinement stopping rule, no change to R0033's accepted decisions, no product
path change. Probes run the generated product worker unchanged, or an in-memory copy with one documented string
patch. Source identity: `main` 47faae32b21e08adc8928f139f0c5387c7316e71 (`moon/BUILD.json`: worker
`e6d3f732…`, kernel `4fcf7888…`, asset manifest `3d4cb527…`). Evidence: `evidence/`. Probes: `harness/`.
Every browser launch went through the startup-advisory isolation helper (copied as `harness/iso.cjs`).
**Isolation: ⟨ISO⟩ requests in total, 0 allowed off loopback** (per-run proxy, route and browser logs; section 7).

Dispositions use the directive's three values: CONFIRMED, REFUTED, UNDETERMINED. Facts (F) are measured or read
from source at the commit above; hypotheses (H) are reasoned but not measured; unknowns (U) are open.

## Front section (for the owner)

### Answer in brief

The refined Moon is a pure function of a small, location-free scene, and it is reproducible bit-for-bit
⟨DET-SUMMARY⟩. But the advisory's premise that the scene "depends only on a phase bucket" is **refuted for the
normal live widget**: an advancing clock gives every refinement a *continuous* phase angle (the native phase plus a
leading-edge offset), so two tabs never request the same scene and no stored result could ever be hit. The phase
is quantised only when the clock is frozen. Memoisation is therefore possible only after one product change: snap
the advancing-clock scene to a fixed phase grid. That changes what the Moon worker computes, so it needs owner
authority even before any storage question arises.

Today each visible tab refines about ⟨RPD1⟩ times a day at DPR 1 and ⟨RPD2⟩ at DPR 2. In every engine,
**⟨DAYFRAC⟩ of that work is done while the Moon is day-suppressed**, and in some of it the Moon is also below the
horizon. Any time the
refinement takes longer than the remaining validity of the old result (Firefox at DPR 2 is close), the visible
Moon falls back to the preview tier. The work also hits a pathology that the advisory did not report. On about 25
occasions a year, near full and new Moon, the product's waxing flag disagrees with the direction in which the phase
angle is moving, for 1 to 261 minutes each time. The leading edge then points the wrong way, and ⟨STORM⟩.

### Strongest supported option (not recommended for adoption)

**Day deferral with an anticipatory dusk start, kept inside the current scene definition.** This is candidate (B)
with the startup advisory's day-deferral prototype as its base. No refinement runs while `_skyMoonPresence` is 0.
One refinement starts ahead of the dusk reveal, with a lead time between the measured duration and the validity
window (section 4B). It needs no storage, no new identity and no new presentation tier. It removes ⟨DAYFRAC⟩ of
steady-state refinement work. It adds one refinement per evening and leaves the night-time cadence, the
stopping rule and every accepted R0033 state unchanged. Its risks are a dusk race (a reveal that comes before the
result, which today's continuous work hides) and a moving reveal instant under weather changes. It is still a
scheduling change under R0033 DG-4 ("no new budget; keep accepted limits"), so the owner must decide it.

### Strongest competing alternative

**Exact memoisation on a canonical phase grid (candidate A), in memory first and across tabs second.** The
advisory's preferred design, corrected. The scene's phase angle is snapped to a grid that keeps the existing
0.0416 device-pixel bound. The key is (worker-source digest, engine Math fingerprint, profile, grid index, waxing),
which holds nothing derived from location. The value is the refined result (8.88 MB raw, about 2.3 MB gzip). Its
strength: a second tab, a hide/show cycle or a reload inside the same grid cell presents the refined Moon at once,
with zero worker time. Its costs: a product change to the scene definition; storage failure modes (opaque origins,
partitioned iframes, no OPFS in the WebKit build tested); an admission rule that has to be designed so that a cache
read is never mistaken for a worker result in R0033's recovery accounting; and, without (B), no reduction in
steady-state work for a single long-lived tab. Over a lunar month there are about ⟨ENTRIES⟩ grid cells per DPR
class, so a store can only ever hold the current and next cell, never a calendar of results.

### Verified from evidence in this audit

- Same engine: identical refined bytes across repeated renders in one worker, a new tab, a new browser process,
  2 instead of 4 shards, concurrent tabs and DPR 1 versus DPR 2 (`evidence/determinism.json`, `evidence/supplement.json`).
- Across engines: ⟨XENGINE⟩ (`evidence/determinism-analysis.json`).
- Display-referred stopping: the 1,024-sample step already sits within ⟨STOP1024⟩ of the final result at the real
  disc size (108 px at DPR 1, 216 px at DPR 2). The final 4,096-sample step, plus the 1,024 step that is mostly
  terminator work, take ⟨TAILFRAC⟩ of the refinement time (`evidence/determinism.json` `steps`; the stopping rule is
  not changed).
- Cadence and the wrong-way leading edge: `evidence/cadence-sim-30d.json` (a replay of the host's own decision rule
  over the product's own ephemeris), `evidence/waxing-mismatch-365d.json`, and live observation
  `evidence/live.json`.
- Storage: IndexedDB and the Cache API stored and read back a 8,884,800-byte entry intact in all three engines.
  OPFS worked in Chromium and Firefox but is absent from the WebKit build tested. All three refuse storage in an
  opaque-origin iframe (`evidence/storage-probe.json`).

### Unresolved

- Real Safari, real Chrome or Edge profiles, other machines and other CPUs (only Playwright builds on one 16-core
  Windows host were tested). The cross-machine claim in section 2(f) is an argument from the arithmetic, not a
  measurement.
- Worker CPU was not traced. The CPU figures here are wall time × 4 shards (an upper-bound estimate). The
  startup advisory's CDP traces (77–94 s in the first 30 s) remain the only measured CPU.
- Whether the wrong-way leading-edge interval is visible to a viewer (disc tier changes, main-thread initial
  re-renders), beyond the counts recorded in section 3.
- R0033 row R33-19 (the M5 30-minute duty-cycle record) is still not produced. This audit's cadence data informs
  it but does not discharge it.

### Owner decisions this would need

1. Whether the advancing-clock scene may be snapped to a canonical phase grid (precondition for any memoisation;
   changes what the worker computes; affects the R0033 DG-4 baseline and ISM-MOON-003).
2. Whether refinement may be deferred while the Moon is day-suppressed and started ahead of dusk (a scheduling
   change under DG-4).
3. Separately, and only after 1: whether the first cross-tab store may be introduced. That decision includes the
   storage technology, the size bound, the eviction rule, and whether a store hit is a new presentation source in
   the ISM-MOON-003 transaction.
4. Separately: whether a defect work order should own the wrong-way leading edge near full and new Moon (section
   3.3). It is a correctness and efficiency defect of the accepted V5 behaviour, independent of reuse.
5. Display-referred stopping (C) changes the accepted stopping rule and is not recommended by this evidence for a
   first step. The measured margin is reported for the owner only.

---

## 1. Q1 — Complete input identity of the refined Moon result

⟨Q1⟩

## 2. Q2 — Determinism

⟨Q2⟩

## 3. Q3 — Steady-state refinement frequency

⟨Q3⟩

## 4. Q4 — Candidates against the current V5 baseline

⟨Q4⟩

## 5. Q5 — What must not change without explicit owner authority, and what a work order would own

⟨Q5⟩

## 6. Facts, hypotheses, unknowns

⟨FHU⟩

## 7. Isolation and reproduction

⟨ISOREPRO⟩
