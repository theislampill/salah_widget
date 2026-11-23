# Annotation (2026-11-22): the warm-ashen control and the real Moon

This note annotates the accepted R0007 case `R0007-warm-ashen-below-horizon`. It adds to the R0007 record; it does
not replace, move or alter any of it. Every original file, every digest in [`manifest.json`](manifest.json), the
[independent review](qualification/independent-review.md), the [independent acceptance](qualification/independent-acceptance.json)
and R0002's reuse of the case (`../R0002/qualification/independent-checks.json`) are unchanged. No other R0007
acceptance is affected. The note sits at the top level of this directory because `manifest.json` inventories only
the evidence subdirectories (its 887 entries contain no top-level file), and no tool or test enumerates this
directory, so adding it changes no pinned inventory.

Authority: owner decision of 2026-11-22 on work order R0033 (issue 100): preserve the original record, annotate its
limitation, and re-capture the scene under controlled, astronomically consistent conditions.

## The limitation

The case's inputs (`preservation/*/R0007-warm-ashen-below-horizon/case-input.json`) simulate a new Moon below the
horizon (`simMoon=0.01&simWax=1&simMoonAlt=-20&simMoonH=42`) at the fixed clock 2026-03-08T06:30:00Z in New York
(`simTime=01:30`, EST). The `simMoon*` overrides drive the native disc, the native moonlight and the Moon worker
scene. They do not reach the refined physical sky, which computes its lunar scattering (KS1991) from the real
ephemeris for the scene's UTC and location (R0033 contract §14; DESIGN.md "URL parameters"). At that instant the
real Moon was 78.1% lit at +22.0° altitude. The effect-free computation
`node tools/qa/r0033_m6_lunar_divergence.mjs --instants 2026-03-08T06:30:00Z --lat 40.71 --lon -74.01` gives a
refined lunar frame mean of 0.00362 cd/m² (about 16 times the non-lunar sky), a presented-atmosphere mean
difference of 12.7 display codes (maximum 17) against the same job with the lunar term removed, and an exposure of
14.9 instead of 23.2. So the simulated Moon and the refined sky's real lunar contribution were inconsistent.

## What the original record established, and what it did not

Established (unaffected by the limitation, because each is a native consumer or a Moon crop):
- the calendar disc was present, current, mostly in frame and opaque, with no stars visible through it;
- every consumed native moonlight contribution (beam, cloud light, local wash, glow, halo, corona, paraselenae) was
  zero, so no light was fabricated for a below-horizon new Moon;
- the 325×530 card, its readability and the motion-preference scopes recorded with it.

Not established:
- that the sky around the disc was a moonless night sky. The presented atmosphere carried real lunar scattering
  from a bright gibbous Moon, which brightened it and roughly halved its exposure (and so lowered star contrast).
  The original stills show that grey, moonlit atmosphere;
- any whole-sky brightness, star-contrast or "no moonlight anywhere" reading for a new-Moon night.

The independent review's wording ("pixels and these receipts support a calendar disc without fabricated
moonlight") is a native-consumer claim and remains true. Read any whole-scene impression of those stills as a
real-Moon-lit atmosphere behind a simulated new-Moon disc.

## Controlled re-capture

Recipe `tools/qa/r0033_r0007_ashen.cjs` (R0033 branch), evidence in
`docs/state-contracts/evidence/R0033/r0007-ashen-recapture-20261122/`. The hash is the original byte for byte; only
the fixed epoch moves, to 2026-02-18T06:30:00Z: 01:30 EST, the same wall time and UTC offset, the day after the new
Moon of 2026-02-17. At that instant the real Moon is a waxing 0.68% crescent at −56.5° (Sun −56.0°): below the
horizon and near new, consistent with the simulated one. The computation above gives a refined lunar term of exactly
zero there (`instant-justification.json`, which also lists 02-17 and 02-19). Chromium 148.0.7778.96 and Firefox
150.0.2 (Playwright 1.60.0, headless, viewport 370×570, DPR 1, zone America/New_York, every browser started through
the R0033 network-isolation module, zero requests allowed off loopback) both observed in the page: the refined sky's
own instant 2026-02-18T06:30:00Z and its Moon at −56.51°, fraction 0.0068; `moonTruth.moonlightOpacity` 0 with
light reason `below-horizon`; `--moonbeam` 0, `--moongrp` and `--moonocc` 1; a current terrain disc; and no
star-like pixel inside the disc in either still (1 s and 15 s). The stills show a dark star field with the faint,
opaque ashen disc.

Differences from the original, stated so the two are not confused: stills instead of video; Firefox headless (the
original Firefox acceptance used a headed replacement because of headless video defects, which do not affect
screenshots); the footer date and the countdown text follow the new date (3h 30m to Fajr instead of the DST-night
2h 30m, which belonged to R0007's countdown cases, not to this control). The re-capture is to be verified
independently; until then it is a candidate record, not an acceptance.
