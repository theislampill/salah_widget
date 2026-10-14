# R000C — weather measurement qualification

Execution of [issue #12](https://github.com/theislampill/salah_widget/issues/12)
against delivered base `7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69`.
C01–C17 and the local pre-delivery portion of C18 are independently qualified
within the [final review's original scopes](independent-review/final-candidate-review.md).
Exact public PR-head review, owner merge authority, delivery and closure remain pending. Merge, Pages delivery, public consumer readback,
`CLOSE-R000C` publication and completed issue closure have not occurred.

No product repair was needed by the executed weather assertions. All 135 runtime
files remain identical to the base, with aggregate SHA256
`5003d304bd0dba119fbc74773cd8e9a97113948259203d8c5390c9062fcc7514`.
Root `index.html` is `7dd8067334c842025ea209d8cbdc20ce1ee31cd783a1f4da279072b1b310f0de`.
Authored native source is `b3094034d50bf0867a0f62c9f3e86a61f132c0126bed2a3fcdbd1bde38bc4dbd`.
Frozen V1 verification passes. No builder was run for this documentation/evidence change.

## Original obligations

[acceptance-matrix.json](acceptance-matrix.json) preserves all 18 original rows,
their source/evidence links, original limitations and separate current dispositions.
The immutable specification and original accepted assessment are copied byte for
byte in `authority/`; their historical relative links belong to specification
commit `21e7a84365fae37a86cae5c7d5e41008c0adc53f`.

| Rows | Evidence and scope |
| --- | --- |
| C01–C13 | [Currentness](currentness.json): exact accepted authored/generated spans and five original regression files. Original generated-weather suite: 119 pass, four inherited TODOs; authored hotfix: 21 pass; related controls: 97 pass. |
| C14 | [Four source mutations](mutants/receipt.json): null rounding, missing HTTP gate, raw-cache bypass and loose hourly shape each fail an unchanged original assertion. Five healthy controls survive each. Mutants are temporary variants, not candidate changes. |
| C15 | Six actual ingress cases in each engine: null, absent property, numerical zero temperature, invalid amount, zero amount and healthy wet. Native JSON consumption, admission, cache, visible header and effects are independently reconciled. Firefox bounded state crops qualify; its failed initial continuous watches do not. |
| C16 | New night malformed-to-healthy ordinary recovery with a native 1× clock; scoped original Chromium controls and Firefox default/full recovered watches. Affected reduced state/pixels and held behavior join exact unchanged policy preservation; no clean 30-second reduced watch is claimed. Exact prior SIM/preview, motion and opaque-ashen-Moon controls are separately bound in [preservation reuse](preservation-reuse.json). |
| C17 | README explains unavailable versus zero, valid negative C/F values, optional-condition survival, quantity-gated model effects and unchanged provider/configuration/cache/installer behavior. DESIGN adds the corresponding value paragraph. |
| C18 | Independent local qualification, exact published PR-head readback, owner authority, delivery and issue closure are separate states. This packet does not certify delivery or closure. |

The original RED belongs to reporter `fd2972ba64225fe9d6848e92497e6d0ed20ea624`
and candidate `9d9c43649748555afbe09e3ca49bc47db2d7e7bb`. It was not replayed or
attributed to the current runtime. The extra attempt to apply the generated-only
R000C extractor to authored HTML failed before consumer execution because its
generated star anchor is absent; [the harness limitation](authored-test-limitation.json)
is retained without product-defect or mutation-kill credit.

## Native evidence

The raw `native/` recordings and traces are retained byte-for-byte in the
[immutable Git evidence tree](https://github.com/theislampill/salah_widget/tree/2f9a5b82cd83e3ae7b994f110b58efc92bbb46a6/docs/rlgwo-execution/20261014/R000C/native)
and excluded only from the Pages payload. Resolve `native/...` paths in the case,
manifest and archive-map records beneath that tree; apply the existing `.json.xz`
mapping below. The [complete immutable packet](https://github.com/theislampill/salah_widget/tree/2f9a5b82cd83e3ae7b994f110b58efc92bbb46a6/docs/rlgwo-execution/20261014/R000C)
preserves the original relative paths, reviews, bytes and dispositions. This
publication-membership change does not alter any qualification or certificate.

[cases.json](cases.json) accounts for every selected, rejected and incomplete
acquisition. [fixture-review.json](fixture-review.json) binds canonical inputs,
all preserved driver/packet versions, original receipt/video hashes and browser
identities. [manifest.json](manifest.json) hashes the public files, including
nested manifests. Large JSON is losslessly XZ-compressed: a logical `file.json`
reference resolves to `file.json.xz` where present, and decompression restores
the original bytes. [archive-map.json](archive-map.json) resolves every copied
logical path to its stored file and retains both hashes, including non-case
reviews and authority records. Native videos and
decoded PNGs are unchanged; no frame is filtered from an original video.

The fixture uses controlled September 7, 2026 CURRENT records at site
24.47/39.61 (Madinah), with the Asia/Riyadh time zone, private Map storage, fresh
contexts, 390×600 viewport, DPR 1 and an actual 325×530 card.
Chromium is 148.0.7778.96; Firefox is 150.0.2; Playwright is 1.60.0 on Windows
AMD64. The browser binaries and tool versions are recorded. Day cases use a fixed
clock and receive no real-time-motion credit. Night uses its declared starting
epoch plus native elapsed time. The healthy response becomes available after
35 seconds and is consumed only through the ordinary retry around 90 seconds.
No fetch, admission, model installation or render API is invoked as a shortcut.

The actual consumer executes unchanged product script bodies and assets. Fetch
returns native `Response` objects with controlled bodies; this is synthetic
provider-input testing, not acquisition from a real weather provider. WMO95 can
retain a labelled current-model thunder condition while unsupported amounts
authorize neither particles nor lightning. Genuine 2 mm can authorize model rain
without direct-observation or strike authority.

The original wrapper and driver were reused with declared adaptations. Failed
headed and preparse pilots remain distinct from the selected original-wrapper
cases. The boundary observer retains the original readiness and full assertions
at both ends of each watch, removes full diagnostics inside it, and polls actual
admitted amount and particle DOM during recovery. Host-wait mode reuses the
previously successful headed/video-only preservation configuration with the
same monotonic deadlines. These fixture differences are not proven causes or
fixes for the missing recorded pixels.

The [final C16 scope audit](independent-review/c16-reduced-scope-audit.md) corrects
an earlier review inference: A03 specifies 30 seconds for no-preference motion,
plus reduced/full controls. Earlier reports that treated a separate clean
30-second reduced watch as mandatory are superseded only on that interpretation.
Their original pixel failures remain intact. The affected reduced behavior
evidence is separate from the retained Honolulu/SIM policy control.

## Contrary evidence and limits

All three original Firefox night recovered watches fail: missing footer at
111.04 s, whole-card blank at 99.40 s, and whole-card blank at 119.88 s. The boundary
default acquisition still loses its footer at 43.40, 57.68 and 83.28 s, outside its
separately predeclared recovered watch. The boundary full-override acquisition
has a whole-card blank at 62.56 s outside its recovered watch. The boundary
reduced acquisition fails its recovered watch at 107.40 s. No later healthy
frame repairs any of those failures; no new start was selected from the media.

An excluded initial Chromium label preflight overlaps the header. A later headed
reduced attempt aborted before its first watch because strict JSON serialization
rejected a native diagnostic NaN; its 1.56-second partial video and traceback
remain unqualified. The reporter now represents native non-finite numbers as
`{"$nativeNonFiniteNumber":"NaN"}` (or `Infinity`/`-Infinity`). Null, finite values
and the actual malformed input string `"Infinity"` remain distinct; assertions
still consume the original native values.

The encoded headed attempt passed initial state assertions but timed out waiting
for ordinary wet recovery; it never started a recovered watch. All 2,420 original
frames are blank. A separate twenty-second passive diagnostic found the native
document visible and the card unpaused, with increasingly stale render summaries.
Its 538 blank frames and all 21 samples remain diagnostic-only evidence. Neither
result establishes the cause of the separate headless missing-frame failures.
A logging-only diagnostic then bound the exact fixture to Firefox's inactive
refresh-driver branch. A separate documented automation activity override did
not restore capture: the override was logged, but the render summary stalled at
687 ms while native paint transactions waited, and all 541 frames remained blank.
Both are diagnostic-only; the activity override is absent from the qualification
driver and product. No desktop inspection or explicit foreground command was used.

Original complete frame indexes, one-second native-size samples and every
nominated missing-region frame support review. Measurements nominate candidates;
pixels decide. Neither image hashes nor DOM state prove motion. Host, fixture
and native video clocks have distinct origins; no unique render-to-frame join
is claimed. Full boundary diagnostics still call `qaState()`, read canvas pixels,
recompute atmospheric diagnostics and may adopt a pending lunar preview. Loaded
opaque Moon pixels are scoped evidence, not an unassisted first-Moon or startup
guarantee. The exact cause of Firefox missing pixels remains unknown.

The retained preservation controls keep their original Honolulu/SIM inputs,
browser/mode and acceptance scope. They do not become Riyadh current-ingress
proof. No new whole-scene scientific, provider-health, first-frame, deployment
or unrelated RLGWO qualification follows.

## Reproduction and delivery

Use the existing pinned environment and the source-bound case packet. The native
driver requires an output outside the checkout and verifies all source hashes.
Run one browser context at a time. Its `PASS_ASSERTIONS_PENDING_PIXEL_REVIEW`
status is deliberately separate from an independent visual finding.

```powershell
python tools/qa/run_r000c_mutants.py --help
python tools/qa/run_r000c_native.py --help
python tools/qa/verify_r000c_receipts.py <original-acquisition-directory>
python tools/qa/index_r000c_video.py <original-case-directory>
python tools/verify_v1.py
```

Archived independent scripts document their exact execution environment and may
contain original local paths. The parameterized tools above are the rerun entry
points. Do not replay accepted browser evidence solely for packaging or metadata.
After independently qualified exact-head owner approval, delivery still requires
merge and Pages/source verification, actual public consumer readback, publication
and independent readback of `CLOSE-R000C`, completed closure of #12 and independent
verification of its final GitHub state.
