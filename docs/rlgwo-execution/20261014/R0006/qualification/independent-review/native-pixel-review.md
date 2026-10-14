# Independent original native pixel review — acquisition review, not final qualification

These findings concern the original WebM pixels, decoded losslessly with FFmpeg. Contact sheets nominate frame ordinals; the verdicts below come from the original full-frame PNGs, including predecessors. `samples.json` beside each pair binds video SHA256, ordinal, PTS, PNG SHA256 and decoded whole-frame RGB SHA256. No browser, screenshot substitution, product diagnostic or generated visual is used by this reviewer. PTS is the native video timeline, not the fixture's performance clock. No unique DOM-render ordinal to native-frame association is claimed.

## Chromium

| Acquisition / case | First visible current native frame | Full-frame finding | Independent evidence directory |
|---|---|---|---|
| original browser / cold-body | 1506 / 60.24s | Complete six clocks, arc, next/countdown, header/buckle and CE/AH footer; 1505 is unavailable | `original-cold/chromium` |
| original browser / frozen-recovery | 1495 / 59.80s | Complete; 1494 remains unavailable | `first-native/chromium/R0006-frozen-recovery` |
| original browser / hidden-resume | 1633 / 65.32s | Complete in actual iframe; previous frame unavailable. This older parent-display stimulus is distinct from the later offscreen control | `first-native/chromium/R0006-hidden-resume` |
| batch3 / cache-denied | 4 / 0.16s | Complete cached Fajr04:47; first refreshed Fajr05:03 frame35 / 1.40s complete; previous startup frame blank | `batch3-first/R0006-cache-denied` |
| batch3 / cache-offline | 4 / 0.16s | Complete cached current card; previous startup frame blank | `batch3-first/R0006-cache-offline` |
| batch3 / generation-late-cleanup | 47 / 1.88s | Complete New York B current card; predecessor truthful unavailable | `batch3-first/R0006-generation-late-cleanup` |
| batch3 / offline-entry | 74 / 2.96s | Complete generated offline current card; predecessor unavailable | `batch3-first/R0006-offline-entry` |
| batch3 / third-success | 74 / 2.96s | Complete third-attempt current card; predecessor unavailable | `batch3-first/R0006-third-success` |
| batch3 / tomorrow-promotion | 5 / 0.20s | Complete initial current card. First Sep8 promotion frame1624 / 64.96s complete, Fajr05:00 next/countdown; predecessor1623 remains Sep7 | `batch3-first/R0006-tomorrow-promotion`, `additional-first/promotion` |
| batch4 / accelerated-recovery | 1505 / 60.20s | Complete first recovered card, native SIM ×120 overlay at14:00:45; predecessor1504 unavailable at14:00:10 | `additional-first/accelerated` |
| batch8 / actual widget offscreen | 1636 / 65.44s | Complete first current card;1635 unavailable. Native intersection pause and original geometry restored inside actual iframe | `chromium-offscreen8-first` |

The bright daytime scene has faint row text, but the inspected complete first images remain decipherable, with no missing card region or clipped footer. This is prayer-card evidence, not a new atmospheric-rendering or headless-shell motion certificate.

## Firefox

| Acquisition / case | Earliest native current frame | Full-frame finding | Independent evidence directory |
|---|---|---|---|
| original browser / cold-body | 1523 / 60.92s | **FAIL:** lower white region hides Asr/Maghrib/Isha and footer; predecessor1522 wholly blank | `original-cold/firefox` |
| batch5 headed / cold-body, hidden and interrupted frozen | No qualified acquisition | **FAIL/incomplete:** trace/observation timeouts or interrupted run. No native first-paint credit | Original batch5 files retained |
| batch6 / cold-body | 1519 / 60.76s | First recovered image complete. 1516 unavailable;1517–1518 blank. Loading body-pending frame50 / 2.00s and exhausted frame1000 / 40.00s complete, honest six em-dash rows and unavailable dates | `firefox-cold6-first`, `firefox-cold6-states` |
| batch6 / frozen-recovery | 1515 / 60.60s | Complete first recovered image; predecessor1514 blank | `batch6-first/R0006-frozen-recovery` |
| batch6 / accelerated-recovery | 1511 / 60.44s | Complete first recovered image, ×120 at14:00:16; predecessor1510 unavailable at14:00:15 | `batch6-first/R0006-accelerated-recovery` |
| batch6 / cache-offline | 17 / 0.68s | Complete first cached current card; predecessor16 blank | `batch6-first/R0006-cache-offline` |
| batch6 / cache-denied | 16 / 0.64s | **FAIL:** lower white region hides Maghrib/Isha/footer. Following17 loses labels while fonts load. Later complete refresh44 / 1.76s does not replace the first image | `batch6-first/R0006-cache-denied` |
| batch6 / generation-late-cleanup | 57 / 2.28s | Complete New York B current card; predecessor56 blank | `batch6-first/R0006-generation-late-cleanup` |
| batch6 / offline-entry | 80 / 3.20s | Complete first current card; predecessor79 unavailable | `batch6-first/R0006-offline-entry` |
| batch6 / third-success | 82 / 3.28s | Complete first current card;80 unavailable,81 blank | `batch6-first/R0006-third-success` |
| batch6 / tomorrow-promotion initial | 18 / 0.72s | **FAIL:** lower white region hides Maghrib/Isha/footer | `batch6-first/R0006-tomorrow-promotion` |
| batch6 / tomorrow-promotion new date | 1664 / 66.56s | **FAIL:** first Sep8 visible image has white upper region hiding header/arc/next/Fajr. Upper-region transition sheet confirms no earlier complete promoted image | `batch6-first/R0006-tomorrow-promotion`, `batch6-transitions/R0006-tomorrow-promotion/promotion-upper.png` |
| batch6 / parent-display hidden-resume | No qualified acquisition | **FAIL:** actual paused boundary not observed; no hidden success claimed | Original batch6 trace retained |
| batch8 / actual widget offscreen | 1641 / 65.64s | Complete first current card within iframe;1639 unavailable,1640 blank. Actual card translated offscreen, product paused across fence, then original geometry restored | `firefox-offscreen8-first` |
| batch9 / cache-denied | 18 / 0.72s | Complete first cached Fajr04:47 card; first refresh43 / 1.72s complete with05:03; predecessor17 blank | `firefox-denied9-first` |
| batch10 / tomorrow-promotion initial | 18 / 0.72s | Complete initial Sep7 current card; predecessor17 blank | `firefox-promotion10-first` |
| batch10 / tomorrow-promotion new date | 1632 / 65.28s | **FAIL:** upper white region hides header/most arc/Isha/next05:00; lower rows/date visible. First promoted portion, not a later gap | `firefox-promotion10-first` |
| batch11 headed / tomorrow-promotion | 25 / 1.00s initial;1627 / 65.08s promoted | Both first images complete. Initial predecessor24 blank; promotion predecessor1626 remains Sep7. Original upper/lower transition sheets show no earlier incomplete promoted image | `firefox-promotion11-first` |

**Strict limits retained:** the newly acquired headless Firefox videos contain intermittent blank or partial whole frames. The batch6 cold example includes blank recovered-state frame1522 / 60.88s, and loading frame16 / 0.64s has empty label/footer text while a font request is pending. Those original frames are preserved. None of the new functional videos is certified as continuously readable, or supplies the normal-motion gate. The bounded A02 state witnesses and exact first recovered frame are distinct from the continuous A05 normal30s control. No whole-scene startup PASS, font-readiness guarantee, or renderer/recorder causal diagnosis follows.

## Preserved continuous motion and Moon controls

Eight original, previously independently qualified controls are retained in their original full-Chromium and headed-Firefox environments. All91 named original files hash-match, and their observed HTML regenerates byte-identically from the current source and unchanged observer. The explicit full-Chromium receipt declares chrome.exe148.0.7778.96 / SHA256290fa7018fda22c52ada5eddb0113baf3ebc41fd0fde6085eddb19793606c635. The unchanged launcher passes that explicit executable through to launch; its default identity would contain the generic fallback description. Fresh functional Chromium uses a different headless-shell executable and receives no copied motion claim.

Independent original samples at5/15/30 seconds show supported normal cloud movement, reduced preference holding cloud positioning, and forced-full motion in both retained environments. Warm ashen/below-horizon samples show a faint mostly-in-frame opaque calendar disc with no visible star through it. Surface-currentness receipts and exact inputs accompany those originals. Continuous qualification is retained from the exact accepted original watch and its certificate; this reviewer does not claim to have freshly re-watched every frame or to have freshly executed those controls.

## Trace reconciliation and pending boundary

`accelerated-trace.json`, `batch3-traces.json`, `batch6-traces.json` and `replacement-traces.json` contain independently computed SHA256 and bounded-memory trace reconciliation. All original completed-render ordinals are present, including Chromium3021 and Firefox5057 accelerated renders, with the specified native clock flags, six rows, adopted date identity, finite clocks, operation/attempt identities, full10000ms owned deadline timers, settled body promises and real cooldown boundaries. Source originals retain exact retry ownership for the cache-current/prefetch case where the native observer cannot uniquely label concurrent backoff timers. Export-tail video after the sealed cut is not additional traced qualification.

All20 selected replacement/original acquisitions are now bound in `native-pixel-index.json`. `final-review.md` and `final-review.json` record every-row pre-delivery qualification. Exact committed-head/public artifact readback and reserved A07 delivery/closure remain separate. This acquisition report is not merge authorization or a continuous-readability claim for the fresh functional videos.
