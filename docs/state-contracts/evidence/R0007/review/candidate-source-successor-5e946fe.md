Reviewer attestation:
- reviewer_identity: /root/r0007_candidate_review
- requested_model: gpt-6-astra
- actual_model: gpt-6-astra (self-report: GPT-6 Astra Pro; no separate backend telemetry available)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- base_sha: d641741df1397659da6ef817fa41aa975f7f3930
- head_sha: 5e946fe18a31750cf528bd58210ce79182dcf1e1

Report state: FINAL

# R0007 independent source successor review

**Disposition: PASS for the exact source successor and the resolution of SRC-01/SRC-02.** Both important findings from the prior independent source review are resolved at the source/model/render boundary. No new critical, important or minor source finding is raised in the reviewed delta. Native, final qualification helpers/workflow, platform, integration, delivery and whole-owner acceptance remain outside this disposition and pending.

Exact successor tree: `6e9eced1194d2463f5090fcdb086e771e1100916`. Original implementation base remains `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`; this report reviews the corrective delta from the prior reviewed candidate `d641741df1397659da6ef817fa41aa975f7f3930`.

## Scope and independence

I independently inspected the immutable commit delta for authored product source, both generated entries, the Moon build manifest, the ten new source controls, the updated state contract/acceptance ledger/continuation and the source execution records. I reused my own prior contract analysis and findings. I did not read the native-Andon report or another reviewer's report, and I did not implement either repair.

The current worktree contains separately owned qualification work; I do **not** assert that the whole checkout is clean. Before and after the source cohort, I compared the working product source, generated entries, config, relevant harnesses and all ten invoked test files with exact committed bytes at `5e946fe...`. They matched. Immutable `git show` supplied the baseline source and evidence review. Only this report was written by this reviewer. No browser, native process, remote service, branch, index, controller or source mutation occurred.

The final qualification Python/helper tests and own Windows workflow are receiving separate engineering/review and are explicitly excluded. The acceptance denominator remains original7.01–7.16, A01–A09 and ES07-01–15; this source disposition does not mark native-dependent or terminal rows complete. Accepted integration remains R0017 → R0007 → R000B, with latest accepted-main reconciliation and exact owner merge approval still required.

## Finding resolutions

### SRC-01 — RESOLVED: retain the available bound at a civil-day edge

The correction at `src/native/index.html:2232–2240` computes the preceding supported bound when available and the following supported bound when available. Only the absent side remains infinite. The range sanity check is retained. The candidate's `epoch` stays nonfinite and `unavailableReason` stays `gap`; a bound is used only to exclude an uncertainty from the strict-future ordering decision.

This preserves the existing unique inverse, full fold alternatives, unsupported-profile handling and current/successor horizon. It adds no interpolation, disambiguation, extra profile search or invented event. The generic selection predicate itself is unchanged.

The new real-admission/model/render controls reproduce both prior failures with literal expected epochs:

| Case | Successor observation |
|---|---|
| Santiago `06-09-2026`, now `2026-09-06T05:00:00Z`, Fajr00:30 in the midnight gap | Sunrise06:00, target `2026-09-06T09:00:00Z`, **240 minutes**; gap epoch remains NaN, lower bound −Infinity, upper bound `2026-09-06T04:00:00Z` |
| Nuuk `28-03-2026`, now `2026-03-29T00:00:00Z`, Fajr22:30 and Isha23:30 in the end-of-day gap | Fajr22:30, target `2026-03-29T00:30:00Z`, **30 minutes**; gap epoch remains NaN, lower bound `2026-03-29T00:59:00Z`, upper bound Infinity |
| Ordinary Santiago companion | Fajr05:00, **180 minutes** |
| Ordinary Nuuk companion | Fajr22:30, **30 minutes** |

I additionally ran independent consumer probes to ensure the repair does not merely skip day-edge gaps:

- With current Santiago record `05-09-2026` at `2026-09-06T03:00:00Z` and an admitted next day containing Fajr00:30, the still-future gap yields `endpoint-unresolved`. The renderer keeps six current rows, no next highlight, em dash and exactly `Countdown unavailable`.
- At the exact Santiago upper bound, `2026-09-06T04:00:00Z`, the gap is no longer a possible strictly future event. The renderer selects Sunrise06:00 at09:00Z, **300 minutes**. Progress remains `decorative-previous-unresolved`, and `previousEpoch` remains null; the known ordering bound does not fabricate a previous endpoint.
- In Nuuk at `2026-03-29T00:59:00Z`, after the last healthy Fajr22:30 has passed, the unbounded future side of the Isha gap still blocks a precise target even with a matching successor record. The unavailable central output and current rows remain correct.

These distinguish legitimate availability recovery from unsafe uncertainty suppression. The existing interior-gap, fold-first/fold-second and unsupported-inverse controls also pass in the full affected cohort.

### SRC-02 — RESOLVED: use admission's canonical Gregorian identity

`prayerDayFields` at `src/native/index.html:2217` now pads the positive year to at least four digits, consistently with admission and current/next-day ownership. Eligibility therefore compares equivalent canonical identities rather than rejecting years below1000.

The model's returned `nowWall` at2313 preserves the wall parts derived from its single captured instant and supplies the canonical current candidate date for the completed-render receipt. This does not resample now. Every valid model has the six current candidates: `current-record-unavailable` exits before this expression, so the first candidate is present. Eligibility already verifies the numeric civil day against the captured wall parts; the normalized receipt cannot introduce a different day.

The new tests admit real canonical records and verify the target epoch/date, `nowWall.dateStr`, rendered text and `_lastRender` date/sim fields for years0001,0099,0999,1000 and2026. Each selects Fajr05:00 with **210 minutes**. The small-year next-day Isha test verifies the actual successor `08-09-0001`, target `0001-09-08T00:31:00Z`, **91 minutes**, with current date `07-09-0001` retained.

My additional century-boundary probe admits `31-12-0099` and `01-01-0100` through the real owner at `0099-12-31T23:00:00Z`. It selects next-day Isha at `0100-01-01T00:31:00Z`, **91 minutes**, and the completed receipt carries `31-12-0099`/`01-01-0100` correctly.

The test helper correction is local to `admittedScene`: it supplies the canonical composite date before invoking actual adoption/admission. The shared clock harness remains unchanged, and no product validation is bypassed. This scope repairs the admitted-record eligibility/target/receipt regression; it does not make a new claim about arbitrary historical timezone offsets or another calendar owner's independent presentation policy.

## Independently executed evidence

Environment: Node `v24.22.1`, Linux x64, ICU `78.3`, timezone data `2026e` as in the prior source review. No native-browser or Windows evidence is inferred from these results.

| Execution | Independent result |
|---|---|
| Current ten committed controls against the complete old generated root from immutable `d641741...:index.html`, substituted only in memory at the harness read boundary | Exit1; **10 tests, 4 pass, 6 fail**, zero skip/TODO. Old source SHA256 `4f63d01b85c7979ba884a58ce6a3edc071047444efee0eb2a405fe58023a2256` |
| Focused ten new controls on exact successor bytes, using the command below | Exit0; **10 pass**, zero fail/skip/TODO |
| Full affected ten-suite cohort, below | Exit0; **288 pass**, zero fail/skip/TODO |
| Four additional independent real-admission/model/render boundary probes described above | All assertions pass |
| `python tools/verify_v1.py` | Exit0; frozen V1 payload and anchored manifest pass |
| Exact source/generated/manifest/receipt comparisons | All claimed identities and parity assertions checked match |

Focused and full affected commands:

```sh
node --test --test-name-pattern='review SRC-01|review SRC-02' tests/prayer-next-event-state.test.cjs

node --test \
  tests/prayer-next-event-state.test.cjs \
  tests/r0007-countdown.cjs \
  tests/r0008-timezone.cjs \
  tests/r0005-adoption.test.cjs \
  tests/r0005-day-return.test.cjs \
  tests/r0002-admission.test.cjs \
  tests/r0020-clock.cjs \
  tests/r0018-prayer-row-status.test.cjs \
  tests/r000a-markers.test.cjs \
  tests/real-sky/native-prayer-arc-samples.test.cjs
```

The independent old-source run fails at the intended model/selection consumer assertions: three unusable current models for padded years, the small-year next-day render and the two edge-gap selections. The four ordinary/boundary positives survive. It does not rely on an admission setup failure as a product discriminator.

## Raw record and documentation accuracy

The committed `review-regressions-red.log` records the same six behavior failures/four passes independently reproduced here. `review-regressions-green.log` records ten passes, also freshly reproduced. The full TAP log has288 pass/zero fail and its SHA256 equals the producer receipt's `ce68ab3754bf7b9798ac5922d32f6e21988b5cc691fe275db6a53daaf7a3077c`.

The earlier failure attempts are retained honestly. In `review-initial-fixture-fail.log`, the four small-year cases fail inside `admittedScene` because adoption returns false for the helper's unpadded composite date; the two gap cases reach the behavioral failure. In `review-post-fix-fixture-fail.log`, the two gap controls pass while those four fixture-admission failures remain. The later corrected-fixture RED is the relevant six-failure behavioral record. The state contract and successor summary explicitly separate those earlier fixture failures from the credited behavior RED rather than turning a setup error into product evidence.

The successor summary's eight recorded source/test/manifest SHA256 values all match the exact commit. Its model/render parity values and the build log's generated root digest also match. The updated state contract accurately describes independent gap bounds, canonical dates, the initial278 controls, the corrected288 controls and independent successor/native gates still pending when authored. The acceptance ledger preserves its original denominator and does not promote source counts to native or whole-owner completion. Native acquisition/Andon and publication transport claims in the broader candidate are outside this source follow-up; I did not independently accept those claims.

## Source and generated preservation

| Binding | Verified successor SHA256 |
|---|---|
| `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` |
| `index.html` | `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9` |
| `offline.html` | `697ed290d2f71a777b9c1a44c3d7b12350cd51dfc66648e8c8907ff897e9be57` |
| `tests/prayer-next-event-state.test.cjs` | `3671ddda05287150269e58a1ebca5b94cfcbd908965e5db1425364c8c19ff696` |
| Model slice, `// build everything render() needs` to before `// draw the solar-prayer arc` | `ffc96c6bfff298983b6eded37eaeb48a89d17cd4a991079e2b19b1eb30cf9c52` |
| Render slice, `function render(){` to before `function updateSimClock` | `96042bc80d5518f671dd62139fcc8180f42576139dd8448c3ead75ba26d36419` |

The authored/root/offline model and render slices are byte-identical. The render slice itself is unchanged from the prior reviewed candidate. All other bytes in each HTML file match both `d641741...` and original base `eebba178...`. Thus this corrective delta does not edit the inverse/clock, admission/adoption/dirty loop, calendar, physical arc, Moon/motion or other protected authored HTML owners. The Moon manifest changes only `/source/src/native/index.html`. These checks verify the delivered source content and protection boundary; they are not a new build execution or native preservation verdict.

## Final bounded disposition

**SRC-01: resolved. SRC-02: resolved. Source successor: PASS at `5e946fe18a31750cf528bd58210ce79182dcf1e1`, tree `6e9eced1194d2463f5090fcdb086e771e1100916`.**

The source conditions underlying my prior GAP-REVISE are satisfied without weakening the inverse, admission or consumer oracles. The original whole-owner native/platform/review/integration/delivery/approval/certificate/closure gates remain pending. This report does not approve the concurrently changing qualification helpers or workflow, does not certify the final combined candidate, and grants no merge or formal lifecycle authority. Any later source/generated change requires affected review; final combined-tree currentness and the mandatory R0017→R0007→R000B integration order remain the root owner's responsibility.
