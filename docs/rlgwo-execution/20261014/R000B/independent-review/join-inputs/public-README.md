# R000B — source-age weather and radar authority

Execution of [issue #11](https://github.com/theislampill/salah_widget/issues/11)
from delivered base `16658749209e0c567f49a3fc9dc855f665afa6e4`, which includes
R000C / #12. The immutable specification is commit
`21e7a84365fae37a86cae5c7d5e41008c0adc53f`; its original bytes and accepted
assessment are retained in `authority/`.

Qualification is in progress. B16 native/pixel review, B18 joined review,
publication readback, owner merge authority, delivery and closure are pending.
This packet does not certify delivery or issue closure.

## Product change and source controls

The actual radar acquisition accepted finite seconds whose millisecond conversion
overflowed or lay outside JavaScript's valid Date range. Four original assertions
failed because the acquisition dispatched Image requests before the invalid
epochs were rejected by downstream authority. Existing authority rejection is
preserved as a separate fact; it did not pass the admission requirement.

The authored `fetchRadar` now converts frame and index seconds once, validates
both derived Date epochs, and returns before Image dispatch or state installation
when either is invalid. The existing builder regenerates root `index.html` and
`offline.html`. There is no change to the accepted 15-minute weather or 20-minute
radar source/receipt limits, inclusive boundaries, no-future rule, captured-zone
ownership, model-estimate policy, cache retention or optional-quantity behavior.

The B16 recovery investigation also exposed a sky-publication omission: withdrawing
a refined frame could leave an expired preview marked ready, which continued to
hide the independently current SVG Moon. A bounded change in the authored
`real-sky/native-host.mjs` retires an invalid preview at that boundary and preserves
lunar detail owned by a still-current preview. An intermediate candidate exposed
the CSS background and raw lunar cutout between that withdrawal and the next
native paint. The final source correction completes the existing preview owner's
currentness-checked presentation in the same turn when needed. It neither keeps
an expired atmosphere nor relabels its time. The builder regenerates the sky bundle
and standalone consumer. Targeted source controls cover withdrawal, ownership,
same-turn re-publication, invalid input and preservation of an already-current
preview. Original failing versions and assertions are retained. These source
findings do not uniquely attribute any particular old video frame; final browser
preservation remains a separate gate.

The 57 remaining source controls pass. The genuine baseline has 53 passes and
four intended admission failures. Four isolated actual-source mutants each fail
their original semantic assertion while corresponding healthy controls pass.
Their exact changed spans, original/mutant hashes and raw TAP are retained;
mutant source files are excluded from the candidate. Affected inherited suites
have 245 passes, no failures and four unchanged TODO placeholders. Frozen V1
is separately verified. The independent source review records the source owner,
generated consumer, accepted-row currentness and original TODO mappings.

## Original obligations and evidence

[acceptance-matrix.json](acceptance-matrix.json) preserves every original B01–B18
row, original limitations and separate current dispositions. Accepted
B01–B03/B05–B12/B15 are carried forward only through inspected current interfaces
and narrowly scoped historical evidence. Original V45 day expiry/503/retry
receipts are not presented as newly executed night or all-phase Moon evidence.

| Rows | Evidence |
| --- | --- |
| B04 | `red-qualified.tap`, `red-qualified-observations.json`, `green.tap` and `green-observations.json`; independent source review. |
| B13 | Actual source acquisition and per-use controls in `green.tap`, including malformed JSON versus labelled VM-only non-finite inputs, four-hour source ages, repeated stale radar, source/receipt boundaries and healthy quantitative recovery. |
| B14 | `mutants/receipt.json` and each paired original, mutant and positive-control TAP. |
| B16 | Native weather/radar expiry, retry, pixels and motion: pending final joined disposition. |
| B17 | Existing README, DESIGN and HANDOFF weather/diagnostic sections; independent fact-to-source review. |
| B18 | Independent exact-candidate, public-head, delivery and completed-closure records are separate stages. |

## Native method

The delivered R000C Playwright wrapper, browser selection, native recording and
offline frame indexer are reused. The controlled fixed site is 24.47/39.61,
labelled Madinah, with Asia/Riyadh timezone, 390×600 viewport, DPR 1 and a
325×530 card. The native elapsed 1× wall begins at
`2026-09-07T18:44:50Z`. Initial CURRENT is 21:30 Riyadh, interval 900 seconds,
WMO63, temperature 24 °C, precipitation 2 mm and cloud cover 70%. Only calendar
Moon phase/altitude/height are forced (`.5`, `20`, `42`); no weather/time simulator
or acquisition/model-install shortcut is used.

Initial radar frame generation is 18:25 UTC and index generation is 18:44:30
UTC. Weather and radar source eligibility expire after the inclusive 18:45 UTC
boundary despite fresh receipts. The second ordinary weather acquisition returns
HTTP 503; the next eligible ordinary retry returns healthy current-quarter-hour
data. Original default cases also wait for the ordinary ten-minute radar refresh.
Request start, response consumption, source time, interval, receipt, frame time,
index time and per-use consumer states remain separately recorded.

Primary native videos begin with navigation and retain original startup and
transition pixels. Their declared recovered motion intervals use native video
without screenshot calls or repeated full diagnostics. Firefox recordings retain
blank or incomplete frames; their cause is not established. A separately labelled
five-state full-viewport PNG acquisition supplies only those states. A further
bounded alternative samples original full-viewport PNGs at a target100ms cadence
over30seconds, with per-call clocks, duration, gap and byte bindings, and a matched
full-motion control. Its independent qualification remains separate from every
original video's result. Full diagnostic reads can adopt waiting Moon terrain;
they are recorded at checkpoints and excluded from the sampled watch interval.
The affected final Firefox runs also record a six-second PNG span around ordinary
recovery, with the request, consumed response and first eligible consumer inside
the span and at least two seconds after that consumer. The exact final runtime
and the narrowly reused, unchanged ten-minute radar pathway are reconciled in
`post-handoff-currentness.json`; old whole-runtime visual acceptance is not reused.
Offline inventories and metrics select material for visual review; they cannot
establish motion or repair missing frames. Actual pixels, including contrary
frames, decide the scoped visual findings.

## Contrary evidence and limits

`baseline-red.tap` and `red.tap` retain fixture-development errors, not product
counterexamples. Only `red-qualified.tap` and its hash-bound baseline reproduce
the four genuine B04 admission failures. A direct authored-file invocation of
the generated-only inherited extractor is a retained harness limitation; the
appropriate authored hotfix suite passes separately.

The original Chromium native attempt completed its state sequence and radar
retry but failed receipt finalization because the first driver stopped
Playwright before closing the context and retrieving its video. Its original
checkpoints, exact driver/wrapper and complete recording remain retained. The
reconstructed failure receipt is labelled as such and earns no native acceptance.
The corrected driver keeps Playwright alive through cleanup and persists raw
checkpoint progress. Independent first-state review attributes the original Moon delay to unchanged,
documented terrain cold acquisition. Original sampled frames through 7 seconds
lack the Moon; the 8-second sample shows it. This is not an initial complete-Moon
PASS, and no later frame substitutes for an original first-state image. The
affected expiry/recovery preservation is reviewed separately.

The primary Firefox reduced and full recordings also contain a readable recovery
frame near150seconds with no Moon after earlier frames showed it. This later
withdrawal is a separate material B16 counterexample, not the cold-start exception
or a blank recording frame. A bounded native diagnostic observed stale preview
ownership after refined withdrawal but did not reproduce the old missing-Moon
pixels in its100ms PNG samples. The initially suspected clearing of a different
current owner was not observed in that run.
The diagnostic observes public MoonDetail.clear calls with exactly-once forwarding;
lexical clear calls are outside its scope. Observation errors fail qualification.
The source-level omission has paired failing and passing controls; final native
preservation remains pending. The healthy diagnostic samples never replace the
original failed frames or establish their exact causal attribution.

The intermediate Chromium reduced-motion candidate retained the Moon but exposed
a bright blue background and black lunar dark limb at150seconds. It failed the
preservation gate despite passing state assertions. The original149/150/151second
frames, candidate source, failing same-turn-publication controls and subsequent
source repair are retained in `recovery-handoff-source/flash-counterexample/` and
the intermediate native case. This finding required final affected browser
requalification; it was not converted into a Moon-presence-only PASS.

These are controlled source and real-browser consumer tests with synthetic
provider input, not live-provider, ground-observation, universal radar coverage,
all-phase lunar, operating-system or offline-app qualification. Clock-skew and
model-estimate limitations remain explicit in the product documentation.

## Custody

`cases.json` accounts for selected and failed acquisitions. `manifest.json`
binds every public file. Large JSON is compressed losslessly with XZ; logical
`.json` references resolve through `archive-map.json` to `.json.xz` when present.
Image sequences are stored without changing their bytes in deterministic
`original-images-*.tar.xz` chunks. The map binds every logical image path to its
archive member and original hash; the verifier checks every member and rejects
extra or missing files. Stored and decompressed hashes are both retained. Original
native videos and decoded pixels are unchanged, and no frame is removed from an
original video.
Execution paths in receipts are provenance only; private owner instructions are
excluded. The packet includes scripts for byte/membership and lossless-custody
verification.
