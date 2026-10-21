# Missing visual observations: returned and stopped cases

All cases bind unchanged runtime `3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821` and the reviewed input packet. No profiler was used. Original source JPEGs, sidecars, videos, stills and execution receipts are published; gaps are not filled.

| Case | Actual result |
|---|---|
| Firefox exact retained lunar fixture | Acquisition failed while Node appended the source-frame log (`UNKNOWN`, errno -4094), before the late handoff. 36 original JPEGs/sidecar rows and the zero-byte video remain. No product-failure inference. |
| Firefox cloud / twilight | UNRUN after the shared Firefox recorder failure; no unchanged capture repeats. |
| Chromium cloud in actual parent | Widget absent from the fresh parent tab; stopped before affected controls. See [parent accounting](../r125/README.md). |
| Chromium twilight | Current admitted final refinement returned after ordinary 1x startup; source frames are retained for independent review. No blanket visual or S1 PASS. |

The Firefox append failure does not establish a Firefox-only defect: Chromium uses the same source-log writer. The successful Chromium twilight log does not explain the failed write. Its underlying OS cause remains unknown. See [independent acquisition stop review](../reviews/visual-r126-firefox-acquisition-stop-review-r1.json).

The Chromium twilight source contains 1,482 original JPEGs, from source+212.579 to +15,295.487 ms relative to the document origin. Two intervals are 116.301 and 183.243 ms; both remain **UNOBSERVED**. Moon refinement is current at projected change 0.2787628173828125 <=0.5 and zero unsettled receivers. State reports alone do not qualify the actual twilight lunar presentation. The [offline locators](offline-review/chromium-twilight-locators.json) identify sampled originals; their contact sheet is a derived locator, not continuous video playback or a new detector.

The prior accepted lunar, opacity, H1/V5, catalogue, dawn/rain, motion and glass evidence retains only its applicable source/fixture scope. No natural whole-day observation, physical-display continuity, or full-video watch is claimed here. The exact retained Firefox late transition, affected cloud/parent sequences and joint nonexcepted visual obligations remain incomplete.

The [independent result review](../reviews/visual-parent-r125-r126-result-review-r1.json) retains the twilight observation: no distinct calendar disc is apparent in the inspected original pixels, despite the visible/current detail-owner flags. Base-compositor `moonPixels=0` and `moonAlpha=0` are expected when the separate MoonDetail layer owns the footprint; they are not proof of a missing render. Actual astronomical solar altitude was -4.518 degrees, versus the UI fixture estimate -6.140. This is unqualified meaningful twilight/calendar presence, not an established unique product cause. The [unmodified detail crop](offline-review/chromium-twilight-final-detail-crop.png) is source rectangle x214,y1,width109,height109 from `cold-final.png`, with no contrast adjustment.
