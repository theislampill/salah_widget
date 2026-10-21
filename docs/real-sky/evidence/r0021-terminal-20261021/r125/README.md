# Actual extension parents: affected sequence remains incomplete

The single Chromium parent attempt imported the widget into the actual isolated Tabliss extension. The imported iframe was present, but the subsequent new tab displayed the default parent without the widget iframe. The acquisition then raised `StopIteration` before its required weather/mode controls. Original parent-import and fresh-tab PNGs, results and source frames are retained under [r126/chromium-cloud-parent](../r126/chromium-cloud-parent/). A parent storage-batching/import timing race is a source-supported hypothesis, not an established runtime cause.

The single Firefox attempt installed the pinned Tabliss NG 1.8.1 XPI through the established isolated Marionette route. Its initial `WebDriver:TakeScreenshot` returned `unsupported operation` from `Capture.sys.mjs` before the admitted-weather appearance sequence. The controller caught that error and exited zero: the wrapper's `RETURNED_FOR_REVIEW` is **not PASS**; the [actual result](firefox-parent/RESULT.json) is FAILED acquisition.

Both attempts cleaned up their owned processes and leases. Neither touched a personal browser. No repeat remained and none was launched. Historical actual-parent access and unchanged source/appearance evidence are retained, but do not supply the missing current sequence beginning with admitted weather, switching both modes and reloading. This row is **INCOMPLETE**, not an established widget regression or a claim that Firefox extension access is impossible.

The [independent result review](../reviews/visual-parent-r125-r126-result-review-r1.json) binds both underlying failure records and inspected Chromium originals.
