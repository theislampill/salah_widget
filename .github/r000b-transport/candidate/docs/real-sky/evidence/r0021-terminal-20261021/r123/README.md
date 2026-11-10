# Chromium actual-event costs: incomplete with concerning increases

The one admitted event group returned six ordinary night/twilight/day A/B cases. A is the preserved comparison runtime `f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`; B is runtime `3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821`. Scene, provider fixture, DPR, cache method and power controls were pinned. No case was repeated.

The [independent offline analysis r2](../reviews/events-r123-offline-analysis-r2.json) uses the existing v5 native marker decoder, inclusive descendants and original allowance `max(0.25 ms, 10% of the corresponding baseline statistic)`. It conservatively excludes marked snapshot envelopes and their synchronous getter-triggered adoption. Pooled full-side empirical overhead maxima are A 0.205 ms / B 0.146 ms. The preliminary r1 used per-case maxima and remains retained as superseded analysis, not a separate experiment or independent corroboration.

The [sealed result review](../reviews/events-r123-result-review-r1.json) joins 209,323 calls and excludes 938 observer-envelope calls. Recorders closed without reported data loss or callback exceptions. Those acquisition facts do not resolve the event-matching limits below.

| Actual owner / scene | Baseline → candidate observation | Limitation |
|---|---|---|
| First-paint preparation, night | 53.350 →143.161 ms | One call per side; candidate adds synchronous initial Moon composition. |
| First-paint preparation, twilight | 125.708 →242.272 ms | One call per side; changed work, no repeated distribution. |
| First-paint preparation, day | 183.765 →233.216 ms | One call per side; startup increase retained. |
| Twilight startup `sky.accept` | median138.622 →156.918 ms; p95 200.223 →176.447 ms | Six versus three natural calls, no immutable per-job scene/phase match; favourable p95 does not erase concerning median. |
| Day startup `sky.accept` | median155.594 →162.190 ms; p95 222.567 →231.310 ms | Six versus four calls; favourable arithmetic bounds do not establish a matched-event PASS. |

**Qualification remains INCOMPLETE.** Raw arithmetic PASS/FAIL labels inside the analysis are not acceptance verdicts. Sparse counts, unequal observation windows, same-side variability and incomplete asynchronous transaction joins remain. New mask callbacks have no directly matching baseline function: missing samples are not zero. The nominal unchanged-weather control was a read-only snapshot of admitted weather, not a second provider/admission event. The clock-minute control is not coordinate-target, DPR or refreshed-weather coverage.

Deep-night H1 worker routing does not establish twilight/day equivalence: those paths still execute atmospheric/display work on the UI thread. Worker-reported row/step elapsed times are not CPU measurements. These startup/event/worker obligations are outside TA5. Archived `moon.poll` retains only its narrow source-dependent qualification; warmed Chromium `main.paint`/`main.render` and Firefox submillisecond proof keep their specifically approved exceptions.

All raw calls/profiles, including the failed resource observer, are retained in per-slot `raw-events.zip` archives with original and public hashes in the [manifest](../PUBLICATION-r123-r126.json). No adverse interval was removed from the public archive. The [analysis script](../terminal-inputs/independent-review/analyse_events_r123_review_r2.py) and v5 helpers support offline reproduction after documented path rebinding; no new browser run is required. The first resource observer's separate acquisition defect and sole repeat are accounted for in [r124](../r124/README.md).
