# r131 — twilight lunar presence discriminator

**No missing lunar publication or new mask defect was demonstrated.** The inspected ordinary and restored whole-card pixels do not show a clearly distinct Moon. The actual exported lunar canvas nevertheless contains an opaque circular region nearly matching the foreground atmosphere. Both findings are retained.

The exact returned scene has Sun altitude −4.513500510866053°, Moon altitude −23.58169626406961°, `presentationUp=0`, lunar group opacity 0.301008 and a visible 109×109 detail canvas. Of its pixels, 8350 have alpha 255 and 3531 alpha zero; none have partial alpha. A nearest-sample comparison against the atmosphere differs by at most two RGB codes. That buffer comparison is not exact displayed subtraction: raster sampling differs and the native scene continues at 1×.

The diagnostic admits only current final refinement before exporting actual buffers and capturing full, detail-hidden, detail-and-SVG-hidden and restored controls. The latter controls leave the stellar mask and already-composed sky intact; they do not represent total calendar removal. [Full control](chromium-twilight/cold-diagnostic-full-control.png), [restored original](chromium-twilight/cold-restored-full.png), [exact exported Moon](chromium-twilight/offline-buffer-readback/moon.png), [returned data](chromium-twilight/results.json).

Issue #33 expressly permits natural twilight blending while stellar occlusion remains independent. The meaningful calendar-presence requirement at night does not establish a new minimum-contrast rule for this bright-twilight, below-horizon scene. No H1/V5, opacity, geometry, science or styling change is justified by this result. This is not a qualification of the full twilight transition, stellar leakage, all night appearances or uninterrupted pixels.

[Independent review](../reviews/twilight-r131-result-review-r1.json) and [publication inventory](../PUBLICATION-r130-r132.json) preserve the original indistinct endpoint, control meanings, source joins, all source frames and acquisition gaps. Runtime/inputs remained unchanged, no page exceptions occurred, and owned resources were released.
