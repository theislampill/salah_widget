# CP9 candidate qualification

**Overall: PARTIAL; Draft PR only.** This records implementation and observations,
not merge/release approval. The authoritative starting graph, findings and matrix
are retained unchanged in [`archive/`](archive/POST_CP9_IMPLEMENTATION_DAG.md).
The current ledger is [`DAG_LEDGER.json`](DAG_LEDGER.json). Source reconstruction
and Moon ownership are in [`INTEGRATION.md`](INTEGRATION.md).

Base: `fd2972ba64225fe9d6848e92497e6d0ed20ea624`, tree
`c5382ee6cb32e71992da963f56b00c2eaa091d1c`. Qualified runtime SHA-256:
`9f7146f0735bb5d999bada4680ca15393cf3b9457c66ff6ce32855c54134bb7a`.
This identity covers root entries and every `real-sky/` file, including authored
adapters and generated copies; it is intentionally different from CP9's archive
layout identity. Two deterministic builds matched. All retained scientific source
bytes and three native authored source files match their archive owners.

## Implementation and dependency dispositions

| Cell | Starting prerequisites | Implementation and fresh observation | Disposition |
|---|---|---|---|
| CP9-N001 / F101 | Independently ready; inherited mask hoist and presentation cache retained | Added exact native encoding using the unchanged numerical encoder as oracle. All 255 rounding boundaries, adjacent doubles, exposure rounding and 1.26 million random channel comparisons pass. Actual 8,047 fully opaque lunar pixels differ by zero codes; full 325×530 composition and moved-Moon controls are exact. All 20 loaded candidate trials pass the unchanged 250 ms limits. | Technical gate advanced; **PARTIAL pending independent source/evidence review**. |
| CP9-N002 / F102 | Independently ready; shares host boundary with N001 | Added rate-aware scheduling, identical-force coalescing, preserved newer in-flight work when an old displayed frame expires, and finite unavailable diagnostics. Fresh 1×/10× observations each have 83/100 visible samples and 3/6 new frames. 60×/600× each have 0/100 and zero new frames. All four retain stale safety and exact frozen recovery. | **PARTIAL**. High-rate throughput target remains unmet; no age limit or source fidelity was reduced. |
| CP9-N003 / F103 | Runner preparation allowed; final join requires N001 and N002 | Added strict runtime/evidence collector, rejection controls, actual HTTP and offline-file runner, CSP, real history traversal and separate live provider observations. Windows Chromium, Firefox and explicitly identified Playwright WebKit are exercised. | **BLOCKED on prerequisite closure**, with partial platform evidence. BFCache/entry limitations and review remain explicit in the collector. |

The 60× and 600× measured executions took about 940 and 994 ms against 500 and
50 ms eligibility envelopes. The renderer still evaluates the admitted full
physical field; no old frame is relabelled, no private/future clock is supplied,
and no unbounded approximation or tier reduction was introduced. Further exact
worker-side throughput work belongs to N002.

The eleven historically closed findings are retained and rechecked, not awarded
as new work: F01 elevation custody; F02 currentness; F03 no synchronous physical
fallback; F04 composition; F005 controlled page lifecycle; F006 single cloud
owner; F007 explicit scintillation-disable semantics; F008 diagnostic ownership;
F009 exact mask; F010 presentation identity/metadata; F011 explicit browser
selection. The ledger maps each to current tests. B001 scientific approximations
remain a boundary, not an invented implementation ticket.

## Validation receipts

Raw observations, commands, hashes, failures and selected pixels are in
[`evidence/`](evidence/README.md). Large JSON is losslessly gzip-compressed; it is
not replaced by a PASS summary. Counts are correlated checks, not independent
reviews or independent scientific confirmations.

| Observation | Result |
|---|---|
| Archive CRC, all payload hashes and recorded inventories | 2,230 manifest files, 162 native baseline files, 950 scientific files, 213 product files verified; repeated at delivery |
| Candidate integration | **109 PASS**: 97 retained plus 12 added numerical/rate/source-reload controls |
| Candidate Python harness controls | **16 PASS**: five retained launcher tests and eleven collector tests |
| Archive handoff/DAG/verdict controls | **22 PASS**, historical reconstruction scope only |
| Scientific JS, Node 22.16.0 | **305 PASS** |
| Scientific Python | 117 run: **116 PASS, one existing seal-fixture skip**; immutable source untouched |
| Expanded native regression commands | **881 PASS, eight historical comparison failures, four existing TODOs, five explicit synthetic-producer exclusions**; see explanation below |
| Browser smoke instrument | **141 assertions PASS**, all 30 required callbacks executed |
| Native scenes | **15 scenes / 88 assertions PASS in each of Chromium, Firefox and WebKit** |
| Extended seasonal/polar/horizon/source-support matrix | **43 scenes PASS**; every startup below the retained 15 s budget |
| Lifecycle and asset failures | **19 cases / 386 assertions PASS in each engine**; six isolated lifecycle/asset mutants all detected |
| CP9 page/elevation/resize controls | **87 assertions PASS in each engine** |
| Presentation cache | **13 assertions PASS**, including dirty PBR/cloud/mask/physical frame and unchanged-pixel metadata |
| Resource lifetime | Eight restarts retain one worker/URL/canvas; disposal leaves zero of each and six prayer rows. Main-heap growth 36,956 bytes, below the unchanged 8 MiB budget. Not total process/GPU memory proof. |
| Loaded performance | All 20 candidate trials PASS with Chromium sandbox explicitly enabled; worst heartbeat **148.6 ms**, worst scheduled dialog delay **106.8 ms**; CPU×4 is an explicit stress fixture, not a device claim |
| Motion | 20 s actual wall-clock watch: 30,139 changed cloud channels by default, zero under OS reduction, 28,566 with `motion=full`; screenshots and video retained. Eight-second retained composed-pixel motion control also passes. |

Historical comparison failures are not hidden or changed to green. Six
`r0022-baseline-balance` cases reference the retired `_glintEls` consumer; two
`r0021`/`r0022` assertions demand pre-CP9 PBR source bytes. The supplied native
baseline already contains its opacity/Earthshine changes. The exact CP9 native
PBR/map/phase/Earthshine preservation tests and actual material equation pass.
Fourteen remaining cloud/arc/map checks in the old balance suite pass, as do the
13 timetable-contrast and restored metadata comparisons. The historical test
commits `8b83df0` and `47c0fa0` were locally available archive-pinned **test
controls**, not implementation donors or ancestors of current main. An early
native result's scope string incorrectly called them main ancestry; this
description and the corrected runner supersede that label, not its raw outcomes.

Node 24.14.0 fails one exact-bit CP6 compositor fixture even on the untouched
archive (304/305). The retained Node 22.16.0 runtime passes all 305 on both archive
and candidate. Do not loosen that fixture or claim Node 24 qualification. Python
3.11.9, Playwright 1.57.0, NumPy 2.3.5 and Pillow 12.2.0 are recorded in the
environment receipt; browser binaries are explicitly selected with no fallback.

## Platform and visual limits

The actual-entry records distinguish controlled fixture checks from unmodified
live Aladhan/Open-Meteo requests. Live prayer/model-weather admission and
target-bound elevation are observed; present-precipitation permission remains
unavailable when no qualified present adapter exists. Model weather is not
relabeled observed rain or lightning.

The engines are Chromium 148.0.7778.96, Firefox 150.0.2 and Playwright WebKit 26.0
on Windows build 26200. This is not Apple Safari/macOS/device qualification;
[Playwright documents that distinction](https://playwright.dev/python/docs/browsers#webkit).
The HTTP fixture has an explicit deployment-like CSP. Local offline files do not
receive HTTP headers and are not awarded that CSP result. No browser
web-security/CORS/file-access bypass is used. BFCache requires an observed persisted return, not a
synthetic event or ordinary reload. Chromium's default Playwright BFCache disable
flag is removed only for the actual-navigation probe; the preserved first attempt
exposed a test wait that wrongly required DOMContentLoaded on a cached return.

Chromium HTTP now records a persisted BFCache return, one fresh renderer and a
current sky (render counter 6 → 1). Offline-file and Firefox/WebKit traversals
recover but do not establish a persisted return. The collector leaves those
checks incomplete. WebKit's extended lifecycle harness initially aborted local
Blob-worker URLs through its foreign-host filter. The final four-line route
correction admits local Blob/data URLs; all original assertions and fault cases
then pass. Interrupted failures and matched worker controls are retained. No
product workaround, synthetic BFCache claim, font-wait bypass or broader HTTP
harness rewrite was retained.

The inherited Playwright default disabled Chromium's process sandbox even after
removing the explicit argument. Final launch options explicitly enable it; the
final performance/actual-entry/material/composition rerun records that setting.
Earlier observations retain their original scope and are not represented as
sandbox-enabled runs.

Screenshots were inspected for the native scenes and actual entries: the Moon
remains opaque and textured, header/footer remain in frame, and cloud composition
matches the retained equation. Bright scenes have modest text contrast and the
full Moon retains the supplied bright appearance. WebKit has visible native
text/arc rendering differences. These are not a completed visual panel, optical
calibration, high-DPR certification or blanket A–M gate PASS. No new lunar artwork
or speculative PBR change was added. Registered-star scintillation remains at the
explicit CP9 setting; a new twinkle feature was not invented to claim the old
native star gate.

The next admissible steps are independent review, exact N002 throughput work and
remaining N003 acceptance. A supplied Moon-PBR package can be reconciled on this
branch at the owners listed in INTEGRATION.md; it will invalidate affected lunar,
composition, performance and platform evidence and require fresh qualification.
