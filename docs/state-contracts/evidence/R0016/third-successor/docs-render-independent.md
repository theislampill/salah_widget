# Docs-only native browser renderer — independent source review FINAL

## Bounded disposition: PASS

The frozen two-file proposal is suitably limited to rendering the reviewed README and the actual authored builder/config in a browser. Its input binding, offline route wiring, source stability checks, command readback, error handling, cleanup, finite workflow steps, and artifact retention support a bounded native acquisition. No blocking source defect was found in this scope. **No browser was launched by this review, and no screenshot, native rendering, public delivery, or widget acceptance is claimed.**

## Frozen proposal and actual inputs

| Item | SHA256 |
|---|---|
| Browser candidate manifest | `f4f631171eb0010e17421ff693b2dc623f320988ed9a2bd26ed44a083e3f3db9` |
| Producer, 6,787 bytes | `fe45d9d2276e1a5ffa73de3bd7fe6288eaa43bc47417575d5cabfb4b6bb37a2f` |
| Workflow, 2,655 bytes | `92b2b672dc30701bdfd90f073c45d65c96622311e23ad82b7bb158cf95508860` |
| Reviewed README C2, 44,640 bytes | `b59a5bb543993eb5b6dd82a5594ee14f944e2de163b52a69bcbf970b5c655f2b` |
| Actual authored builder, 30,333 bytes | `66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e` |
| Actual authored config, 23,025 bytes | `91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81` |

All manifested bytes were verified and retained in reviewer scratch. The producer's hard README check matches `root-doc-binding/candidate-2/proposed/README.md`. The builder and config copies match their published Git blobs at observed commit `eb3f870b27e897664dfa25c5ed5e8c94baeef28a`. The script reads those authored files directly, rather than rebuilding or replacing them. It records input byte lengths/hashes before observation and rechecks the original files afterward.

Pinned npm versions **Playwright 1.62.1** and **marked 17.0.5** independently match the installed local package metadata. The workflow acquires them in an owned private prefix with lifecycle scripts disabled, retains the generated package lock and setup logs, and uses the same private `PLAYWRIGHT_BROWSERS_PATH` during setup and render. This establishes source wiring and exact selected versions, not successful future dependency acquisition.

## Rendering and execution boundary

The exact published checkout uses read-only repository permission, the trigger commit SHA, no persisted Git credentials, and a sparse input set containing only README, authored builder/config, and this producer. The workflow has a distinct noncancelling concurrency group, a fifteen-minute job limit, a three-minute render-step limit, and an always-run artifact upload with missing artifacts treated as an error.

The browser context fulfills only three exact page URLs from the input buffers: rendered README HTML, builder HTML, and config JavaScript. All other routed page requests are recorded and aborted. The producer evaluates the actual builder's `installCmd()`, `snippet()`, and `hash()` and retains the DOM text and install label; it never executes the generated command or clicks the install/clipboard action. Neither installer source nor the widget runtime is in the sparse checkout. The producer has no child-process command execution path.

The actual builder computes its preview iframe URL from the synthetic document origin. That iframe request falls outside the three allowed routes and is deliberately unavailable. Its blank/failed frame cannot qualify widget rendering, geometry, or live public behavior. The native result should be described as authored builder interface context and command generation only.

The producer retains the generated README HTML, full DOM text, two named README screenshots, a builder install-context screenshot, actual command/snippet/hash, input hashes, browser version, page request list, page errors, process command, Node/platform facts, total monotonic elapsed time, and final status. Source changes or page errors fail acquisition.

## Verification performed

An independent `node --check` passes. The exact reviewed README was also parsed using the same installed marked version without launching a browser. Both requested H4 headings survive exactly, all three pinned commit occurrences are present, the old pin is absent, and every policy substring used by the browser gate appears in the correct prepared section. This checks the Markdown/selector inputs; it supplies no layout or screenshot credit.

The source/data verifier completed **23** bounded checks. It does not execute the candidate producer, any installer, or an unrelated widget campaign. The local Chromium ProcessSingleton/socket failure remains preserved separately at `root-doc-binding/render/failure.txt`, with no screenshot credit and no attempted host-policy change by this lane.

## Cleanup and receipt precision

Normal completion awaits context close and then browser close in the finalizer. Any caught rendering error clears `complete`, retains the error, and makes the process fail. A browser-close error also clears completeness and records its cause. The final receipt is written after cleanup handling. The workflow captures stdout/stderr and retains partial evidence even when a step fails.

One nonblocking metadata detail remains: the finalizer sets `browserClosed=true` even if an earlier failure occurs before any browser object exists. Such a path still has `complete=false`. Consequently, `browserClosed` alone is not evidence that a browser launched or was actively closed. Accept only a complete native receipt joined to its expected inputs, outputs, screenshots, and actual browser version. The workflow's outer timeout also means a hung process may leave only partial evidence, which remains a GAP rather than a completed result.

The page interceptor is not independent OS-level or global network telemetry. It establishes the reviewed page-resource policy for this source-bound observation. Do not promote its request list to proof of zero browser-background/network syscalls.

## Native receiving still required

Readability, screenshot framing, visibility of the complete required documentation context, and the actual builder install context need inspection of the original native PNGs. Scrolling a heading into view and saving a viewport does not by itself prove that every relevant paragraph fits. If a required statement is cropped or unreadable, retain that original capture and acquire a focused supplementary view. The current source review does not pre-admit the eventual pixels.

`verification.json`, `verify_source.py`, the exact candidate snapshot, actual input copies, and Markdown preparation output are retained here. This review does not grant this lane publication/dispatch authority or close R0016. Root retains source and publication custody.
