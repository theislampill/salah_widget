# Independent native-log diagnostic prereview

One unchanged 20-second headed reduced diagnostic with subprocess-local `MOZ_LOG=timestamp,PresShell:5,nsRefreshDriver:5` and `MOZ_LOG_FILE` beneath a new private acquisition directory is justified. This adds observation of a specific source-supported mechanism. It changes no preference, product, browser binary, foreground state, recorder, readiness predicate, input or qualification interval, and receives no qualification credit.

## Source association checked

I independently read the source packet and verified every acquired file against `../firefox-source-inspection/sources.json`. I opened the installed Firefox `omni.ja` directly as a read-only ZIP and compared `chrome/juggler/content/TargetRegistry.js`: its 46,743 bytes equal both the retained installed extraction and the official-source packet's `matched-TargetRegistry.js`, SHA256 `b430c0f6a9f946eb2082c85948f19d19bbe9233124055562f3e79c45fb66a98e`. The supplied Playwright revision is `c8604ecd97ffcc50b6c269df544b7cc36f258d3b`; its `matched-UPSTREAM_CONFIG.sh` selects Firefox base `c7fa3c91990bac266ee99a9e31863c202469f369`.

The installed `playwright.cfg` differs from the matched packet only by an added blank line and `pref("dom.permissions.testing.enabled", true);`. This is an exact installed JavaScript/config comparison and an upstream-base source association. It is not a reproducible C++ binary proof, nor does it prove that the native timer branch executed in an earlier acquisition.

The relevant matched source files are:

- `matched-PresShell.cpp`, SHA256 `b58f38fde6470a8319b9ffbcbabbf4ce4cabc46a5778d443d24213ca0e0497e9`: log module `PresShell` at line 581; `ComputeActiveness` at 11603; `SetIsActive` at 11682 propagates activity to the refresh driver.
- `matched-nsRefreshDriver.cpp`, SHA256 `e75074fc4009ae4d8c0e321b9af8d0f4e9c5a9b011af349a6d366aada55c9588`: log module `nsRefreshDriver` at 111; inactive timer rate doubling and log at 1115/1125; throttled timer selection at 1383; `PaintIfNeeded` returns false while throttled at 2598; `SetActivity` changes `mThrottled` at 2901.
- `matched-StaticPrefList.yaml`, SHA256 `ffc5a1f8a18955bbbc6fe14be8e11c6c6354df693e3563bd44ab8f7323bd82ee`: the top-level-always-active preference is documented for testing at 11003–11010. Its existence is not authority to change it in this diagnostic.
- `matched-firefox.patch`, SHA256 `a70698f090b88175bbff99b45e9a6eaedffc43fb8164336e056dc63095a50984`: the Playwright-specific activity branch must be considered, not only the unpatched upstream file.

## Interpretation and acquisition boundaries

Two distinctions are essential. First, `ComputeActiveness(url, %d)` logs the existing `mIsActive` before computing a new result; the integer is not a direct result receipt. Second, the matched patch at line 1605 changes the invisible BrowserChild branch from unconditional false to `GetForceActiveState()`. Therefore an exact fixture-URL log followed by "BrowserChild ... is not visible" alone does not prove the resulting native activity is false.

The planned native logs can provide the missing corroboration: associate the exact new fixture URL and process identity with the relevant PresShell/refresh-driver events and inactive-timer sequence, then compare them with native content visibility and observed render timestamps. Do not infer a document-to-driver association from a shared pointer shape or nearby timestamp alone if the log lacks the required join. Other startup/chrome/about:blank documents can have inactive timers too. Any incomplete association stays explicitly incomplete.

Run only the already reviewed `visibility_probe.py` SHA256 `9d4b7cc44a888aed71224f7566763aeee36e0edccf48cefb09e5005716679e90`, driver `76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce`, packet `268d820ff632135eb86ed92f3650b619cac71440eef2e282605d00dcd4749f67`, and same single reduced headed invocation. Add the two logging variables only to that spawned process environment. Retain the exact invocation/environment binding, every emitted parent/child log file, full native video, passive samples and explicit diagnostic termination; keep the previous diagnostic untouched.

Logging itself can affect timing. A complete native association would support a bounded causal hypothesis for this headed diagnostic, not retroactively explain all prior headless blanks or qualify the reduced watch. Missing logs, absent associations or altered behavior under logging earn no success credit and do not justify automatic replay. Any later activity preference or acquisition repair requires a separate evidence-led review of the concrete delta and then its own complete original interval proof.
