# R000C independent observer-only default pilot review

The separately predeclared recovered 30-second interval supports the scoped C16 default-motion/layout/Moon control. The whole recording does not pass continuous readability. Three inter-watch footer omissions remain failures, and the capture cause is unresolved.

## Exact acquisition

- Original path: `../native/firefox-boundary-pilot/R000C-night-default/`.
- Original video SHA256: `1407a58a964615743049dda205eba938819ef186682989511083029dc703e584`.
- Original receipt SHA256: `131428a28ac71a5f0c3c2281932c606bf21ccc2171f1d07cff4fe71a746d53ed`.
- Driver SHA256: `ed610a2ce09ebdfce661b563338d0cf31f89162676b9f03de40544f59e350737`; packet SHA256: `4bbe653b82edff0512a2dcd047aac069b6c96a535e5cb773224b973098acff77`.
- Unchanged wrapper SHA256: `917c651c95184eab56e72701a73a2338d3cf1e3131f38af40c4bcd77203de26f`.
- Same Firefox 150.0.2 binary, headless original wrapper, native recorder, current source, canonical night input and native 1× elapsed clock as the original night attempt. Only diagnostic sampling differs, as reviewed in `boundary-observer-check.json`.

`firefox-boundary-pilot-readback-check.json` records independent reconciliation. All 3,038 original RGB frame digests and PTS match the original index, ending at 121.48 seconds. The original four boundary snapshots pass the unchanged weather assertions. Actual native JSON was consumed once for each of two ordinary weather requests, with the second at fixture elapsed 89.813 seconds; recovery was not installed or invoked through a helper.

The driver records the initial watch at host monotonic 111096.546–111126.562, lasting 30.016 seconds. The separate recovered watch is 111186.125–111216.125, exactly 30.000 seconds, or navigation +90.469 to +120.469 seconds. Its boundary state snapshots are fixture elapsed 90.179 and 120.239 seconds. These are the original declared boundaries, not a cutoff chosen from the media. Host/fixture/video clocks remain distinct; no unique frame-to-render ordinal join is claimed.

## Pixel finding and limits

I inspected native original frame 250 / 10 seconds for the malformed state and frame 3000 / 120 seconds for recovery, plus native one-second temporal sequences across PTS 90–121 (`firefox-boundary-pilot/R000C-night-default/sequence-90-97.png` through `sequence-114-121.png`). The malformed state has `20°` with no particles; the recovered state has model-supported rain. Throughout the inspected recovered sequence the 325×530 card, header/buckle, six prayer rows and footer stay complete. Rain positions and cloud appearance change over the interval. The half-Moon remains in frame, textured and opaque, without visible stars through its disc. No cloud hash is used as motion proof.

The exhaustive original index has startup low-information frames through 0.44 seconds and three later candidates at 43.40, 57.68 and 83.28 seconds, with none near the recovered interval. I independently extracted and viewed all three later candidates. Each contains a white strip that removes the footer. They remain failures; the full original video and exact failed PNGs are retained. Their later healthy frames do not repair them. The original rejected night watches also remain rejected and are not rebound to this acquisition.

This is scoped acceptance of a separately declared complete recovered interval, supported by native pixels and raw boundaries. It is not whole-recording continuity, a startup-time result, a first-Moon presentation guarantee, manual viewing of every frame, or evidence that observer removal fixed the recording route. In fact, missing pixels persist while full diagnostic reads are absent, so those reads are not established as the cause. The existing boundary diagnostics can still adopt a pending lunar preview; that caveat remains.

Running the two other already required reduced/full night contexts once with these same pinned observer-only settings is now justified. Each requires its own raw ingress/recovery evidence and complete original predeclared interval review. They receive no automatic credit from this default case. C16 as a whole, final exact-head qualification and C18 remain pending those and the later delivery gates.
