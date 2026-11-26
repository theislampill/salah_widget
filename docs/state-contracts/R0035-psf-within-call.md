# R0035: within-call Gaussian integral experiment

**Disposition: bounded source parity observed; independent exact-tree review
pending. Native comparison has not run. No configuration is selected for adoption.**

The 2026-11-26 continuation authorizes the narrow source experiment proposed by
the retained preparation-cost review: avoid recalculating a horizontal Gaussian
integral on every row of the same splat. This addition supplies an in-memory
derivative and reproducible controls. It does not change the shipped renderer,
the original lab, its source/foreground admission, or a hosted campaign.

[Issue 102](https://github.com/theislampill/salah_widget/issues/102) and
[the original reconstruction contract](R0035.md) retain their authority. The
original producer-predicate, initial-status and cadence failures remain. Native
timing, capture fidelity, the three-engine comparison, genuine human evaluation,
amplitude/glass/magnitude decisions and owner visual approval remain outstanding.

## Source boundary

`tools/r0035/psf_within_call.mjs` accepts actual Buffer bytes, verifies the exact
reference hashes, and derives two separately identified source strings:

1. A renderer intended only for the disposable name
   `tools/r0035/psf_within_call_renderer.mjs`. Its four relative imports point to
   the unchanged generated core. Every original function remains intact except
   for the local horizontal-weight reuse inside `splatGaussian`.
2. The original `stellar_replay.mjs` with its single `renderStars` import pointed
   at that separate module. No other stellar/replay expression changes.

Both transformations have guarded inverses. Missing/ambiguous seams, reference
drift, added bytes and altered derivative bytes fail admission. The identity
function binds these four actual byte populations, not caller-supplied hashes.
It identifies this source-only pair; it is not a full native preparation receipt
or a substitute for admitting all imports in a future integration.

| Population | Bytes | SHA-256 |
| --- | ---: | --- |
| Unchanged reference renderer | 5,021 | `173283b65c4b89cd1c85067131183ad2a306199850f41ae070ede463de5add6b` |
| Derived renderer | 5,264 | `26fe659062abd3363d229452a5abf1f2b0b289e7f0ba6c38790704ecff8f1b67` |
| Original stellar replay | 7,919 | `d58e92294f2f99b2d2405b153a228ec0a5484064f3efe09e0d26babb34acc4e7` |
| Redirected stellar replay | 7,913 | `d49a250db31d1d54d8e296336f84d296817f9f87ae2ea357bbffe13d858b6dde` |

The generator performs no filesystem, browser or network operation. The controls
load the derivative in separate Node VM module graphs. There is no operational
materializer, browser route, default flag, workflow selection or generated app
change. `vendor/real-sky`, `real-sky/core`, the original lab, source identities,
scientific parameters and all existing acceptance code remain unchanged.

## Arithmetic and state

The reference computes
`wx = .5 * (erf((i + 1 - x) * inv) - erf((i - x) * inv))`
again for every visited row. With ordinary scalar inputs and stable standard
intrinsics, its inputs are invariant during one call. The derivative evaluates
that exact expression lazily on the first visited row and retains its Number
value in a new local array. Later rows read that value at the same x position.
The array is unreachable after the invocation. There is no state shared between
stars, calls, channels, PSF components, source epochs or frames.

The original x/y/sigma validation and buffer/RGB checks execute first, in their
original order. The support and clipped bounds, fractional source position,
unchanged `erf`, per-row `wy`, `wx*wy`, `Math.max(0,...)`, `rgb[c]*w`, and
`buffer[k+c] += ...` retain their original expressions and order. Each row still
visits x from left to right and channels 0, 1, 2. The first row interleaves each
horizontal evaluation with its writes exactly as the reference does. The change
does not precompute every x weight before the original first write.

For the ordinary positive integer raster domain, sigma's existing upper bound
of 100 limits the horizontal population to 1,203 Number entries. The shipped
reference PSF parts used by the replay ordinarily require much smaller supports.
The new array allocation and reads have a cost; fewer transcendental evaluations
alone do not establish a useful elapsed-time or native frame-time improvement.

For a nonempty clipped support of `Nx` columns and `Ny` rows, the reference calls
`erf` twice per row and twice per pixel. The candidate calls it twice per row
and twice per column. In a source-only counted 17×13 case, actual `Math.exp`
calls inside the unchanged `erf` fall from **468 to 60**, with identical complete
output. Module-initialization calls are excluded by resetting the counters only
after both graphs load. An empty vertical support performs zero evaluations.
This is an operation count, not a CPU, allocation, scheduling or native speedup.

## Bounded parity coverage

The registered `r0035-within-call-psf-source-controls` command currently has 13
top-level controls. The source test gives a fresh pass/fail result, with exact
source/data hashes and population details in TAP diagnostics.

- **Raw buffers:** 708 explicit and fixed-seed numeric cases compare all 456,585
  Float64 values as bytes. Inputs include tiny/broad sigma, clipped and absent
  support, fractional coordinates, zero channels, nonzero initial buffers and
  differing numerical scales. Three additional dimension cases preserve the
  reference's ordinary zero/negative/fractional behavior without inventing a
  new dimension guard.
- **Call boundaries:** 96 successive, overlapping splats vary position, sigma,
  channel and component-like flux on the same nonzero buffer. Every intermediate
  complete buffer is compared.
- **Failures and ordering:** 19 malformed argument combinations compare error
  name/message and unchanged buffers. Six buffer-write fault/completion cases
  compare RGB reads, buffer reads/writes and complete partial buffers. Five
  deliberate first-row math faults compare the same exception and write prefix.
- **Mutations:** wrong subpixel integration, clipping, flux multiplication order,
  Float32 horizontal weights and stale cross-call horizontal values each fail
  full-output parity. They also fail inverse source admission. Reference and
  derivative byte mutations cannot acquire a valid source-pair identity.
- **Full renderer:** 15 reference/camera/eye × DPR 0.5/1/1.5/2/4 configurations
  compare all 39,807 returned Float64 values and metadata. They exercise distinct
  wavelength channels and Gaussian components, nonuniform pixel transmission,
  clipped sources and original ineligible-source handling.

These are bounded comparisons on the executing Node runtime. They do not
exhaust all binary64 inputs or JavaScript objects. Exception parity means the
tested class/message and output/access prefix, not identical stack traces or
equivalence under replaced intrinsics/prototypes, arbitrary side-effecting input
mutation, concurrent mutation, allocation exhaustion or engine termination.
In particular, a counter-based exception installed in a redundant later-row
math call is not expected to occur after that redundant call has been removed.
That does not weaken any original ordinary-input validation or native gate.

## Original source inputs and downstream checks

Both source graphs use the unchanged original `qualification_scene.mjs`, its
real catalogue and registered diffuse asset, and the original
`materialize_lab.py::patch_refined` host hooks. The hook recipe is pinned to
`2b35b1862502ac28a34f6c782b1174c228e819d7d42ef7d6596ea79b432b3096`, and both
resulting host modules match
`f8497768c0c08c90434aa921ea532718f1aa928b602a9bba85ffcd8417d6a824`.
The complete input inventory is emitted with each run.

The catalogue, runtime manifest and V-nside128 data are checked against their
fixed SHA-256 values before the original asset-admission functions run. The
original reference graph loads 41 real source modules plus one generated test
entry; the candidate adds one separate renderer and changes only the stellar
import. All other loaded module bytes match between the two graphs. The registry
binds 47 real input files, including the controls, generator, original hook
recipe and three data files.

| Original scene recipe | Preview patches | Refined patches |
| --- | ---: | ---: |
| Dark, 2026-11-09 00:00 UTC | 169 | 1,404 |
| Moonlit, 2026-11-24 00:00 UTC | 158 | 1,355 |
| Near Fajr, 2026-11-09 02:15 UTC | 134 | 1,406 |
| Twilight, 2026-11-09 03:15 UTC | 0 | 0 |
| Day, 2026-11-09 09:00 UTC | 0 | 0 |

All **4,626 complete patches**, comprising **13,052,868 Float64 values**, agree.
Every typed raster field also agrees. These inputs are genuine executions of
the admitted original source recipe; they are not claimed to be retained
per-splat arguments from the earlier native timing run.

Twelve preview/refined × scope × glass-factor configurations compare nominal
bytes, variable-pixel indices, source/center counts and **132 complete presented
frames** with their overlays and center samples. These use explicitly synthetic,
nonuniform cloud/calendar/glass foregrounds. Paused, hidden, reduced-motion,
full-motion override and zero/partial gain states are included. Opaque calendar
interiors remain at nominal values. Selected frames also match the unchanged
slow full-frame replay oracle.

The actual original `prepareLiveFrame` source admits the digest-verified dark
refined source scene at 1,404 sources in both graphs. Local catalogue reads are
supplied by a bounded test adapter returning the original bytes; no network or
browser runs. Changed coordinates, duplicate source membership, missing transport
diagnostics, mismatched flux and altered nominal bytes retain the five original
refusals. This supplies no publication-active, cadence or native-scene admission.

## Reproduction and remaining work

```sh
python tools/cp9/run_native_regressions.py --output /tmp/r0035-psf-source-results \
  --select native-runner-contract r0035-within-call-psf-source-controls
```

Use a new output directory. The source command has a 600-second bound because
it runs both complete original scene populations and downstream checks. This
new source-test bound changes no original native budget or acceptance threshold.
Keep the runner's exact verdict string; a test result is not product readiness.

Before any native comparison, root must obtain an independent exact-tree review,
design and review a separately identified source preparation/caller and actual
complete closure, bind the acquired runtime and namespace, retain the original
source/foreground/physics/currentness/cadence oracles, and run a matched comparison
with reviewable authenticated evidence. Keep originals and failed controls.
Neither spectral cache misses nor safe cross-frame keys follow from this result.
