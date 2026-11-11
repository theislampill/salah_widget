# R000B run 42963236609 - independent pixel review (evidence review, not acceptance)
Model: Sonnet 5.5 (claude-sonnet-5-5). Scratch: `<scratch>` (art/, fr/ frames, work/ contact sheets and work/masks.txt).

**How I looked.** I viewed every card, native-cloud, preview-foreground and consumed-solar-mask PNG for all 5 cells, but through stage-by-kind contact sheets at 1x (about 20 to 40 images per cell), not as separate Read calls. Refined-foreground and viewport PNGs were not opened individually. I measured alpha on every mask. The sheets for the hidden cell's expired-repeat, fresh-weather-without-prayers, recovery-capture-001, recovered-30s and recovered stages (ch2.png) were generated but not opened. I judged the hidden recovery from video frames instead. I did not read the acceptance rows or the driver beyond the row text in the prompt.

**Scene.** It is night. There is no sun and no sun-optics, so the sun is NOT_OBSERVABLE. Stars are present in every stage. The moon is a thin crescent at top right with a faint ashen dark side that is opaque; zoomed at 4x, no star shows through the disc in the candidate expired, repeat, resumed or fresh stages.

**Mask facts.**
- The native-cloud PNG is 144x232 RGBA. Healthy and recovered stages have about 9.0k non-zero pixels (27%), bbox x 0-143, y 0-86, drawn as a cloud deck. Whether the deck sits at or above the dashed horizon line was not checked.
- Preview-foreground and refined-foreground are fully opaque (alpha 255 everywhere) in every stage, so alpha says nothing about them. I judged them visually.
- The consumed-solar-mask PNG is a white field with the cloud silhouette. It is present only for healthy, last-eligible, recovery and hidden-before-expiry stages; later stages have only a .txt.

**Baseline (24 PNGs, 520-frame video of 20.8 s).**
- Healthy has a dense cloud deck, rain streaks, a rain-cloud icon with "24°" and the Isha arc.
- Last-eligible, expired-901s and expired-repeat still have the deck (mask 9.2k to 9.5k px, 28%). Rain and header icon are gone, the header shows "—", and the rows read "Prayer times unavailable". The deck is dimmer after expiry but still clearly drawn.
- Video: the deck persists from about 10.6 s to the end (about 20 s). There is one transient frame at 10.5 s with a flat blue backdrop, no clouds and a black moon disc.
- The baseline defect is visibly demonstrated.

**Candidate default (39 PNGs, 4138 frames, 165 s).**
- Healthy and last-eligible masks show the deck (9.0k and 9.2k px). Expired-901s, expired-repeat and fresh-weather-without-prayers masks have 0 px.
- Video: the deck, rain and header icon vanish together in one frame at 10.24 s. No stale-cloud or blue frame was seen across 9.9 to 10.9 s. The clean state shows stars and the crescent moon. The deck reappears at 130.12 s and fades in over about 0.3 s, with rain and the Fajr 05:00 card.
- Healthy motion: cloud-band mean absolute difference was 2.0 over 2 to 4 s and 1.3 over a single second, so the clouds visibly drift and morph. The deck is gone from about 10 to 130 s, with a 0.00 to 0.1 frame difference while static.

**Candidate full (39 PNGs, 4114 frames, 164.6 s).**
- It is the same as default. Deck gone at 10.24 s, back at 130.36 s. Healthy motion is 1.94 over 2 to 4 s, 1.36 over one second.
- The expired-repeat card has a grainy dense star field that the default card lacks (mean pixel difference 1.8). That is star rendering, not weather.

**Candidate reduced (39 PNGs, 4125 frames, 165 s).**
- Healthy and recovered native-cloud masks are identical (9044 px, 27%), so the deck is static. Deck gone at 10.44 s, back at 130.16 s.
- Frame difference over 140 to 141 s is 0.00, so the sky is frozen; it is 0.77 over 10 s, from small star or rain-tick changes.
- Rain is drawn as a flat row of evenly spaced vertical ticks near the deck base. This appears in healthy-before-midnight as well as after recovery, so it is this mode's static rain depiction, not a recovery artefact.

**Candidate controlled-hidden (47 PNGs, 4202 frames, 168 s).**
- hidden-before-expiry shows the full deck and rain.
- hidden-after-901s card shows a flat blue backdrop with no sky layers or stars, header "—", and stale Isha arc and prayer rows (05:00 to 19:30). Its native-cloud mask is empty (0 px). Its preview-foreground PNG still shows the cloud deck (the sheet row for that stage), so the foreground buffer is stale while hidden.
- resume-opportunity-001 has an empty cloud mask and a clean foreground. The resumed-expired card is fully withdrawn: "Prayer times unavailable", crescent moon, stars, no clouds or rain.
- Video: the first visible frame after resume (12.8 s) is already withdrawn, with no stale cloud or rain frame. The deck returns at 132.4 s. Healthy motion is similar to default.

**Per-obligation pixel findings.**
- **B08 (unavailable header, effects off):** SUPPORTED_BY_PIXELS for header "—" and no clouds or rain in candidate expired-901s, expired-repeat and resumed-expired cards. The header weather icon and temperature are absent after expiry. The fresh-weather-without-prayers stage is the exception discussed below. Baseline shows the same header "—" but keeps the deck.
- **B16 (labels, cloud withdrawal and recovery, stars and moon, motion):**
  - Withdrawal and recovery are SUPPORTED in all four candidate cells (video transitions above), with stars and moon present throughout.
  - Default and full motion is SUPPORTED. Reduced holds static, which is plausibly what the driver expects, though I did not read its assertion.
  - Truncated date footers are still visible.
- **ES0B-01:** SUPPORTED for the expiry withdrawal at about 10.2 s in the candidate, and the baseline retention is also visible.
- **ES0B-02 (native-cloud and foreground masks):** SUPPORTED for the native-cloud masks (empty after withdrawal, non-empty before and after recovery). Foreground PNGs are opaque, so they show nothing by alpha. They look clean after withdrawal in every cell except the hidden-after-901s foreground noted above.
- **ES0B-04 (stars and moon independent of weather):** SUPPORTED for stars and the opaque crescent after withdrawal. The sun is NOT_OBSERVABLE (night).
- **ES0B-14 (real cloud pixels and motion, rain origin):**
  - Real cloud pixels are SUPPORTED. Default and full drift visibly; reduced is static as expected.
  - Rain-origin check is partial. In default and full, the rain streaks in the card come from the deck region. The mask-based rain-origin predicate was not independently checked, and the reduced tick row is a flat band.
- **ES0B-08 (hidden resume):** SUPPORTED. The first visible resume frame is withdrawn, with no stale cloud or rain.

**Oddities.**
- **"last-eligible-before-midnight" PNGs.** In the candidate cells the card already shows the withdrawn state (no deck, "Prayer times unavailable") while the masks and foreground from the same stage still show the deck. The driver JSON for default says coverage [0.92, 0.9, 0.6] and source age 898.7 s, so the images were captured at different moments. This is a fixture or driver capture-order artefact. The baseline card at the same stage still has the deck. Not a product defect.
- **Thin vertical ticks in the reduced recovered card.** They are the reduced-motion static rain depiction, and they also appear in the reduced healthy card. I judge it intended or pre-existing reduced-motion behaviour, not a regression in this candidate. A flat row is arguably a poor rain depiction, which is a separate question.
- **Transient baseline frame (blue sky, black moon disc).** It is real, at 10.5 s in the baseline video: a flat blue backdrop and a black moon disc with the sky layers unpainted. A similar flat blue backdrop appears in the hidden cell while hidden. No such frame appeared in the visible candidate cells sampled. Judgment: pre-existing baseline behaviour on repaint. I did not review every candidate frame, so a one-frame flash cannot be ruled out.
- **"Rain 24°" header with no clouds.** Confirmed in the fresh-weather-without-prayers card in all candidate cells, and again in the video at 129.6 s before recovery. The rain icon and 24° show while the card shows "Prayer times unavailable" and no clouds or rain. Probably by design (fresh weather without a prayer model gives coverage 0), but it is visually inconsistent for a "weather withdrawn" claim. Unknown whether it is a product defect.
- **Truncated date footers.** "2026-09-…" in healthy and "Gregorian date unav…" in expired are clipped by ellipsis. Pre-existing or fixture. Not examined further.
- **Stale prayer rows and arc in hidden-after-901s.** Visible in the card and in the video 10.4 to 12.4 s while hidden, replaced at resume. The preview-foreground PNG at that stage also still holds the cloud deck. Likely a deferred-render artefact of the hidden state, unseen by a user, though it is weather-driven pixels in the foreground after withdrawal. Judgment: unknown, probably a capture of a paused hidden surface rather than a user-visible defect.
- **Video recorder artefacts.** Frames at 0 s are white. A few frames are larger than the card (for example the baseline at 18.0 s, the candidate at 10.6 s), which looks like a recorder scale glitch. The reduced cell shows "Loading…" at 0.8 s, so its first seconds are not comparable to the others.

**Could not inspect.** Viewport PNGs, refined-foreground PNGs and the hidden ch2 sheet individually. A per-frame check of all 4000+ frames per candidate video for one-frame flashes. The driver assertions and acceptance text were not read in depth. No numeric rain-origin check was run against the visible cloud columns. The Firefox and WebKit engines are not covered, as only Chromium cells ran.
