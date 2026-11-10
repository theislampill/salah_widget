# R0006 — bounded prayer recovery qualification

Implements [issue #6](https://github.com/theislampill/salah_widget/issues/6).
This packet qualifies the original remaining work against base
`c431733c57f76e2b441ee8f8cd85a1fa6675de55`, including merged PRs #56, #57 and #58.
Delivery, `CLOSE-R0006` and completed issue closure remain pending the owner's
reserved exact-head merge authorization. A Draft PR is not delivery.

The accepted prayer lifecycle is unchanged. All 135 runtime files match the
delivered R0004 tree; the nine original prayer-owner source spans and five
original regression files remain current. The affected source suite passes
72 tests, with no failures, skips or TODOs. The deadline, cold-branch and cooldown
mutation controls remain in that suite. Frozen V1 verification passes.

## What changed

- README clarifies the nominal 32.7-second all-timeout path and the absence of a
  hard real-time CPU guarantee. Existing cache, visibility, day/generation and
  weather documentation is preserved.
- Ten R0006 cases use the existing serial Playwright driver and unchanged
  read-only observation fixture. Native performance clocks, timers and animation
  frames remain active. Controlled ingress is the original September 7 UTC
  provider/cache fixture; no scheduler is invoked directly.
- Firefox promotion uses the separately bound `R0006-promotion-polling.json`
  variant with native 100 ms observation polling and the existing headed mode.
  Its provider, cache, clock and product semantics match the canonical case;
  its observation schedule and environment are explicitly different.
- The existing driver gains bounded complete trace transport for the 120x case,
  native interval polling for hidden observation waits, and an actual card
  offscreen stimulus. These are fixture repairs, not product changes.
- Original native traces, videos, frame receipts, source/currentness checks,
  contrary acquisitions and independent review are retained below.

## Evidence and original acceptance matrix

[cases.json](cases.json) identifies every acquisition and its disposition.
[manifest.json](manifest.json) binds the public files. Large JSON traces are
losslessly compressed with gzip or XZ; each case member records both compressed
and original hashes.
No render receipt is thinned. The accelerated export seals a complete snapshot
cut; video recorded after that cut is an export tail, not additional traced proof.

| Original condition | Evidence and scope |
| --- | --- |
| 6.01–6.12, 6.14 | [Currentness](qualification/currentness.json), [72-test TAP](qualification/source-tests.tap), [independent owner bindings](qualification/independent-review/bindings.json); accepted implementation retained. |
| A01 / 6.13 | [README review](qualification/docs-review.json); three attempts, full-body 10-second deadlines, 900/1800 ms backoffs, nominal 32.7 seconds plus scheduling, real operation-start cooldown, cache/tomorrow/visibility limits. Publication pending. |
| A02 / 6.15.a | `native/{chromium,firefox}/R0006-cold-body`: successful headers with three unsettled bodies, exhausted operation cleanup, healthy fourth current request after the 60-second fence, first recovered same-day card, and hostile late bodies unable to change accepted state. |
| A03 / 6.15.b | `R0006-hidden-resume`, `R0006-frozen-recovery`, `R0006-accelerated-recovery`, `R0006-generation-late-cleanup`: real elapsed eligibility, actual offscreen pause, one resumed recovery, and successor ownership. This is offscreen evidence, not a successful document-hidden claim. |
| A04 / 6.15.c | `R0006-third-success`, `R0006-cache-offline`, `R0006-cache-denied`, `R0006-tomorrow-promotion`: successful third attempt, usable selected cache, denied writes, matching tomorrow suppression past 65 seconds and legitimate next-day promotion/acquisition. |
| A05 / 6.15.d | Original first-card/frame review plus [exact preservation reuse](qualification/preservation-reuse.json): all six rows, header/footer, arc/next output, generated offline entry, actual iframe, normal 30-second motion, reduced/full preferences, opaque ashen Moon and frozen V1. |
| A06 / 6.16.a | [Independent qualification](qualification/independent-review/final-review.md) reconciles each original row, source and input identities, trace/ownership/clock observations, first native pixels and contrary evidence. A01–A06 are qualified before delivery; A07 remains reserved. |
| A07 / 6.16.b | **Pending reserved merge authorization**, followed by merged-tree/Pages delivery, public consumer and evidence readback, published/read-back `CLOSE-R0006`, completed closure and independent closed-state verification. |

The original immutable specification and audit are copied verbatim in `authority/`.
Their relative historical links belong to the original specification commit
`21e7a84365fae37a86cae5c7d5e41008c0adc53f`; the copies are provenance, not rewritten
specifications. Current issue body and audit-comment hashes are in currentness.

The [independent native pixel index](qualification/independent-review/native-pixel-index.json)
joins each exact first frame, predecessor, video hash and decoded RGB/PNG receipt.
See the [fixture/input bindings](qualification/fixture-review.json) for all twenty
selected engine/case acquisitions and the separate promotion variant.

## Measured native recovery

Times below are fixture `performance.now()` elapsed observations, distinct from
video presentation timestamps. Attempt counts do not count high-level operations.
Each cold case has **four current-day attempts in two current operations**, plus
one separate successful tomorrow-prefetch operation/attempt.

| Cold full-body case | Three-timeout path from operation start | 60-second fence | Fourth current request | First recovered render |
| --- | ---: | ---: | ---: | ---: |
| Chromium | 32715.7 ms | 60527.3 ms | 60541.0 ms | 60617.3 ms |
| Firefox | 32716 ms | 60376 ms | 60376 ms | 60419 ms |

The 15.7/16 ms excess is measured scheduling delay over the nominal 32700 ms,
not a CPU deadline guarantee. Per-attempt native timer and backoff delays,
operation IDs, cleanup receipts and negative checker controls are retained in
[Chromium trace review](qualification/trace-review-selected-chromium.json) and
[Firefox trace review](qualification/trace-review-selected-firefox.json).
Concurrent current/prefetch backoff timer candidates in the offline-cache case
are disclosed as ambiguous; timing proximity is not invented timer ownership.

The offscreen case moves the real card to y=1200 inside its disposable iframe.
The product's existing IntersectionObserver pauses it while the document remains
visible. It stays paused beyond 65 seconds, then restores its original geometry
and starts exactly one eligible current operation. Native 100 ms observation
polling does not call the product scheduler or change its clock.

## Pixel scope and contrary evidence

First current and promoted-date images are taken from the original native video
and reviewed with their predecessors. A later healthy card never replaces an
incomplete first current card. DOM ordinals remain preserved, but no unsupported
one-to-one association between a checkpoint still and an earlier render is made.

Firefox functional recordings contain intermittent whole-frame blanks/partial
captures. Selected first-current images and bounded loading/exhausted states are
qualified individually. These clips receive **no continuous-readability or
motion credit**. Early font-loading frames without labels, later blank frames,
the initial incomplete cold capture, incomplete cache/promotion first images,
headed observation failures and the parent-iframe display:none failure remain
retained and explicitly limited. No OS, renderer or capturer cause is inferred.

Normal motion/preference/Moon preservation uses only the exact previously
qualified original controls: full Chromium executable in its original mode and
Firefox headed controls, with identical runtime and regenerated observed input
bytes. All 91 retained files were independently rehashed. Fresh Chromium
functional cases use headless shell; the older full-Chromium motion result is
not relabelled as shell motion. See [environment receipts](qualification/acquisition-environments.json).

Two earlier accelerated exports failed: recursive protocol export did not
complete, and one giant JSON string exceeded Node's string limit. Both remain
unqualified. The accepted bounded export retains every original 120x render.
One action-schema validation rejection happened before browser launch and is
documented separately as a fixture preparation error.

## Reproduction

Use the existing pinned Playwright 1.60.0 environment and installed browser
binaries identified in the receipts, with disposable profiles. The acquisition
used an isolated cached package installation because the default Python lacked
Playwright; no product dependency or browser download was introduced.

```powershell
node --test --test-reporter=tap --test-concurrency=1 tests/r0006-recovery.test.cjs tests/r0003-ownership.test.cjs tests/r0005-day-return.test.cjs tests/r0005-adoption.test.cjs tests/r0004-boot-day.test.cjs
python tools/cp9/r0007_browser.py --issue 6 --engine chromium --source-root . --cases tests/rlgwo/R0006-cases.json --output <disposable-output> --validate-only
# Actual execution requires the existing driver's authorized capacity-lease input.
# Run one engine/case context at a time with --video-only; never use a personal profile.
python tools/cp9/r0006_verify.py --input docs/rlgwo-execution/20261014/R0006/native/chromium --output <trace-review-chromium.json>
python tools/cp9/r0006_verify.py --input docs/rlgwo-execution/20261014/R0006/native/firefox --output <trace-review-firefox.json>
python tools/verify_v1.py
```

Trace checks are separate from native pixel review. Neither command success,
nominal timing, DOM state nor a cloud hash grants visual or delivery acceptance.
