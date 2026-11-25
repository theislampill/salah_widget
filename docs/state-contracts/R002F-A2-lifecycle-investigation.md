# R002F-A2: restoration investigation and executable architecture experiments

Status: **research implementation and controlled-source evidence; native qualification outstanding; no product change, merge, acceptance or registry promotion**.
Source baseline: `df644ef60156b67b5c487395176369bcec7a0d7b` (the delivered R0041 tree).
This branch was commissioned for independent advancement and later integration review. It does not amend the
owner's existing hide, weather-authority, scene-currentness or visual-acceptance contracts.

## 1. What is ready to use

`tools/qa/r002f_a2_resume.cjs` runs the actual native prayer-selection, publication and render-loop owners through
the repository's existing `tests/r0003-harness.cjs`. It gives the next implementer a bounded discriminator for the
stale prayer state routed from R0041, including the previously missing midnight and Maghrib **source-state** cases.
`tests/r002f-a2-resume-observer.test.cjs` independently checks the observation fields, the boundary outcomes and
injected stale values, missing callbacks and incomplete fault routes. Both instruments are registered.

The [schema 2 receipt](evidence/R002F-A2/20261125-observer-review/source-state.json) contains 30 baseline observations
and 30 positive-control observations: five fresh-fixture repetitions of six scenarios. All baseline observations
have at least one old field at the end of the restoring task. All five fields match their specified fixture values after the first executed callback.
The synchronous-render positive control has no old field at either sample. These are deterministic VM repetitions,
**not five independent browser trials, presented frames, or fulfillment of the owner's native reproduction row**.

| Scenario | Task-end differences on unchanged source, each of five repetitions | First native callback |
|---|---|---|
| Fajr crossed | current prayer, next time, countdown | matches fixed fixture values |
| Maghrib crossed | current prayer, next time, countdown, Hijri display | matches fixed fixture values |
| Civil midnight crossed, next day admitted | countdown, Gregorian display | matches fixed fixture values |
| Two minutes within one prayer | countdown | matches fixed fixture values |
| Civil midnight crossed, next day unavailable | prayer name, availability message, Gregorian and Hijri display | withdrawal matches fixed fixture values |
| Fajr crossed, optional Moon request throws on return | current prayer, next time, countdown | current; next frame remains scheduled |

The fixture uses synthetic UTC prayer times (Fajr 05:00, Maghrib 18:00) and deliberately distinct synthetic calendar
records. It is not a prayer-method, astronomical-calendar or provider validation. The untouched source and the
in-memory control are separately SHA-256 bound in the receipt. The physical renderer and layout are boundary doubles.

The [original schema 1 receipt](evidence/R002F-A2/20261124-pro-resume/source-state.json) is preserved at its
original path from commit `9e6f91d22306d36081fb50bfcd09edf264307c9f`. Its seven tests included a same-publisher
oracle and could classify an absent class-selected target or a missing callback as current. Its `writesInTask`
field counted calls to the theme double. Use schema 2 for candidate comparisons. Both receipts observed the same
30 baseline task-end differences and zero callback differences on the unchanged entry.

### Reproduce

From the repository root:

```sh
node --test tests/r002f-a2-resume-observer.test.cjs
node tools/qa/r002f_a2_resume.cjs index.html /tmp/new-resume-observation.json --require-current
```

On this baseline the second command writes the receipt and exits **1**. `--require-current` checks both
task-end and callback state. Without it, exit 0 means the observation completed. Missing targets or values,
an incorrect pre-hide setup, lifecycle inconsistencies, or other source/harness errors exit 2. Output files
must be new. The CLI accepts another generated entry, and the whole-render control requires its exact resume
anchor once. Any `SALAH_REQUEST_CONFIG` override runs in the fixture and its executed UTF-8 text is hashed.
Comparisons across entries should use the same config, data, observer and two harness digests. No request leaves the VM.

### Controls and what they establish

The twelve registered tests cover the five fields in all six scenarios. Each scenario specifies the complete
pre-hide and return displays independently of the entry being measured. Blank fields invalidate a sample. The
unavailable scenario admits the specified em dashes for the prayer name and next time. The observer counts
authored body targets and checks that each recorded node has its target class or ID. A missing, commented-out
or duplicated owner fails the markup check. A plausible but wrong next time, such as `99:77`, differs at both
checkpoints when injected in the return publisher.

Each retained row has one callback pending before hide, zero while hidden, one queued on return, one actually
executed by the drainer and one successor pending. The return task makes exactly one request to the Moon double.
Only the fault scenario records the injected exception under `moon-resume` in that task. Removing, duplicating
or failing to cancel or reschedule the callback, skipping the Moon request, or misclassifying the exception
invalidates the observation. `themeCallsInReturnTask` counts calls to the harness's `applyTheme` double
during show. In the positive control's unavailable row four fields changed with zero theme calls.

Two test-only controls replay pre-hide DOM values after a working restoring listener has completed. Replaying
all five fields produces a task-end difference in every scenario. Preserving the refreshed name while replaying
the other four exposes countdown, Maghrib Hijri and midnight Gregorian differences. Both controls work on an
entry that already refreshes synchronously. The full synchronous-render control calls the complete render path
in the visibility task, can duplicate optional work and has no measured performance qualification.

## 2. Source diagnosis

The current `startRenderLoop()` owner in `src/native/index.html` has two distinct paths:

1. `setVis()` clears the card's paused class, schedules a frame, then synchronously requests/composes the Moon on
   an actual paused-to-visible transition. It does not call the prayer-day or prayer-publication owners.
2. `loop()` later calls `maintainPrayerDay()` and publishes `render()` when the accepted second changes or the
   render is dirty. Inside `render()`, prayer publication precedes optional weather and astronomy stages.

This ordering explains the VM result: the model can already select Fajr while `.cn` still says Isha in the Moon
request made by the restoring task. The next native callback replaces it. A current `model()` value alone is not
evidence that current prayer information has reached the DOM, and a current DOM value alone is not evidence of a
presented frame. The existing source comment saying prayer publication does not wait for this optional work is
too broad as a scheduling statement: the queued callback cannot execute while the event task is still running.
The existing R0041 record already discloses the measured real-tab cost; this branch does not remeasure it.

The finding is consistent with the existing [R0041 contract](R0041.md) §9.2 and §10.2, but is narrower than its
real-browser observation. It neither proves nor disproves which cached image a compositor reveals before the
restoring listener executes. That separate limitation belongs to the back-navigation restoration work.

## 3. Smallest next implementation to qualify

This section is a concrete proposal for the owner's lifecycle scope, not an implementation authorization or an
adopted threshold. The existing [owner response](https://github.com/theislampill/salah_widget/issues/96#issuecomment-6915229680)
reserves the architectural remedies for further evaluation. The later
[routing note](https://github.com/theislampill/salah_widget/issues/96#issuecomment-7117227888) does not authorize them.

### 3.1 Prayer publication on return

The proposal below is now implemented as an opt-in, source-bound research transformation. Section 6 records its
results and exports the patch; the authored and generated shipped owners on this branch remain unchanged.

Evaluate a shared, bounded prayer-publication operation owned by the native entry:

- Derive the current accepted time and run the existing `maintainPrayerDay()` once on a genuine paused-to-visible
  transition. Preserve its generation, target, day-selection and request-ownership rules.
- Reuse the existing prayer stage and `writePrayerStatus`/calendar owners. Publish the full coherent group: current
  prayer, next event, countdown, row classes, progress, arc and civil/Hijri dates, or the existing truthful
  unavailable state. Do not patch only `.cn` or fabricate a next timetable.
- Keep optional weather/Moon/sky work outside that operation. Reuse it from the normal `render()` path so the
  two paths cannot drift, preserve fault containment, and retain a single pending frame.
- Keep render receipts honest. A prayer-only write must not be reported as a newly composed sky, and a failed
  stage must not leave an earlier successful receipt describing the new state.

Why this is preferable to the positive control: it addresses a known publication-order gap without running the
whole optional render twice. Why it is not yet a complete solution: earlier DOM publication does not shorten a
long restoring task or control a cached frame displayed before JavaScript runs. The native experiment must verify
the first frame composed after the task and report cached pre-event frames separately.

Concrete red/green qualification should include all six scenarios above, five real returns per tree for each
mandatory boundary, missing/late/failed next-day records, repeated visible events, offscreen-to-onscreen, frozen
preview, and an injected optional fault. Check one frame owner, no duplicate prayer requests and no new timer.
Measure dispatch cost and time to actual current prayer pixels; do not substitute a DOM timestamp.

### 3.2 Short-hide Moon record retention

The current Moon runtime still calls `clear('document hidden')`, drops its accepted record and increments its
epoch. Reusing a record across a hide therefore changes an accepted state transition, even if its pixels would be
close. A proposal must separate these dimensions:

| Dimension | Required treatment in an experimental design |
|---|---|
| Presented pixels | Continue the accepted hide withdrawal unless the owner expressly changes it |
| Retained data | Quarantined as a possible reuse input, never automatically accepted or visible |
| Re-admission | Fresh capture; same scope and identity; current geometry/phase error within the existing 0.0416 device-pixel budget; current eligibility |
| In-flight work | Old generation/epoch replies remain rejected; retaining data cannot revive an obsolete request |
| Failure/expiry | Discard the record and use the existing valid successor/fault path |
| Memory | One bounded retained record; dispose releases it |

The proposed 0.0416 check is an existing product bound, not a new grace period. A short duration alone is not an
admission rule. Same elapsed hide at a changed location, device ratio, scene or phase can be invalid. Performance
savings require measurement with real receiver and composition code; this branch makes no new saving claim.

### 3.3 Weather continuity and transactional publication

The original R002F renewal implementation is already delivered and is not restarted. Its source-age admission,
three-second renewal margin and bounded retry behavior remain unchanged. The owner's bounded atmospheric-hold
choice permits further evaluation, but the five-second value, duration/easing and precipitation disposition are
still unaccepted. In particular, current weather text and accessibility claims must withdraw immediately on expiry.

For the architectural evaluation, track accepted evidence, retained presentation, pending successor and published
composition separately. Construct a complete successor before publishing it. A preview owner may withdraw only
its own layer; R0041's bounded preview-clear fix is part of this baseline and should be preserved. A new design must
not make a held layer pass `nativeResultCurrent()` or a cloud-authority check by relaxing those fences. It needs an
explicitly marked held-presentation state with its own owner-approved limits, or a current replacement.

The old local A2 candidate `6438b044` is not available in the published main checkout. This branch has not recreated
it or claimed to repair its repeated clear-before-publish exposures. Fable should apply the observer/evidence to
that candidate only after reconciling it with this delivered baseline and the current ownership fixes.

## 4. Native qualification still owed

| Obligation | This branch's result | Still required |
|---|---|---|
| Prayer-state return across Fajr, midnight and Maghrib | Shared-publisher research patch, complete-group controls and source-state discriminator complete | Real native returns and pixel/frame timing, at least five per tree |
| Back-navigation cached frames | Existing routed finding analyzed, no new measurement | Actual back/forward restoration with `pageshow.persisted` recorded; distinguish reloads and cached pre-event frames |
| Moon data retention across short hides | Opt-in actual-runtime quarantine/re-admission experiment, invalidation/fault controls and bounded data accounting | Owner adoption, native byte/resource/timing and visual evidence |
| Firefox/WebKit sky-host observations | No claim | Valid native launches and required host routes in both engines |
| Weather held/transactional architecture | Real identity probes, failed uploads and [shared selection of current preview layers](R002F-A2-preview-transaction.md), including producer revocation and reentry controls | Reconciliation with the original candidate, owner-bound held-state semantics, other presenter handoffs, native transition clips and full qualification |

The executor had no usable Chromium, Firefox or WebKit binary. The system Chromium command points to a missing
executable. A normal Playwright Chromium installation was attempted; its official download returned HTTP 403.
No browser or provider was launched by this recipe. Consequently, there is no native screenshot/clip, no first-frame
guarantee and no human visual verdict in this branch. The deterministic VM rows cannot be relabeled as those rows.

## 5. Integration guidance

This is a main-based, independent branch. Its delta is the observers, registered tests, reproducible research
transformations and receipts, plus a registry pointer without verification-level changes. Production, generated assets, immutable
scientific source and frozen V1 are unchanged. The work can be folded into the lifecycle investigation while its
owner decisions remain open. Run the new observer against any proposed remedy, keep the native qualification
matrix, and retain the distinctions between task-end DOM, native callback and actual displayed frame.

All numerical observations above are controlled source reproductions. No atmospheric or interface appearance is
changed by this branch. Physical fidelity and experiential fidelity of a future remedy remain separate native
review obligations; neither is certified by a green observer test.


## 6. Executed architecture experiments (2026-11-25)

These are three separately selectable transformations of the actual authored owners. They are held under
`tools/qa/`, not installed into `src/native`, `real-sky` or `moon/src`. The main-based source remains byte-identical
to the delivered product. This is the bounded architectural evaluation permitted by the issue, not adoption of
R1/R4, a weather grace period, an altered first-frame guarantee, or a new interpretation of G7.

### 6.1 One prayer publisher, two callers

`prayerOnlyCandidate()` extracts the exact existing prayer stage, including its existing catch/withdrawal path,
into one helper. Normal `render()` calls that helper. On an actual paused-to-visible transition a second, small
entry runs `maintainPrayerDay()`, handles simulation unavailability, and calls the same helper **before** the
existing Moon request. It clears `_lastRender`: a prayer-only publication must not claim a newly composed sky.
It adds no scheduling primitive. It does not call the normal weather-sync, Moon-geometry, stars or theme stages.
The existing restoring-task Moon work and its duration remain; earlier prayer DOM does not make that task shorter.

The [architecture receipt](evidence/R002F-A2/20261125-architecture/source-experiments.json) runs the unchanged
source and candidate through the independently specified six scenarios, five times each. The unchanged source
has 30 task-end differences; the candidate has zero. Both have zero differences after their first executed callback.
The Moon request sees the current prayer on every candidate return, including the fault case. Each task-end group is checked against fixed fixture expectations for all six keys, labels, times and classes (including past rows), progress width/visibility, and the six arc marker identities and classes. A per-scenario digest checks the entire arc against the independently exercised original callback, which also passes the same oracle. The date and countdown checks remain in the accepted observer. At Fajr the fixture publishes
2.5% progress, Fajr current and Sunrise next. Missing next-day data withdraws the bar and arc and replaces all six
row times with dashes. A thrown prayer model withdraws the full group and both dates and leaves one callback scheduled. A return-only Maghrib mutant erases the rows and arc and changes progress to 99.9%; all four corresponding oracle comparisons reject it.

The timer/request statement is deliberately narrower than “no new timers during return.” At civil midnight,
running the existing day owner earlier can start its existing request deadline in this task. The candidate and
unchanged source after its next callback have identical request URLs, request counts and pending timer counts.
Counters wrapped around the actual restoring entry and shared publisher each advance once on return and zero times on the repeated visible event. Repeated events add zero requests or timers. An unconditional restoring-call mutant enters the publisher twice while leaving the repeated DOM group identical. The four measured ordinary optional stages
run zero times during the candidate's return task. The separate Moon request remains exactly once.
Removing only the restoring helper call leaves all six task-end discrepancies and preserves next-callback recovery.

### 6.2 Preview upload failure, not a complete transaction

The actual preview owner finishes its detail composition, then uploads a full background and a foreground region
in two `putImageData` calls. In the existing deterministic host fixture, an injected failure **before the second
write** leaves changed visible-buffer bytes while the status retains the old UTC and reports retention. This is a
source-level failure-mode discriminator, not a claim that a real browser naturally threw at this point.

`singleUploadCandidate()` copies the fully prepared foreground into a private copy of the new background and
prepares its final ImageData before the time/pause and cloud publication fences, then performs one upload. Charging only the extra ImageData construction 60 ms at 600× playback ages the original job by 36,600 accepted ms. The candidate drops that job, retries once and writes only the fresh job at age 600 ms. Moving preparation after the fence publishes once at age 36,600 ms with a recorded age of 600 ms. These are injected costs.

For foreground-only updates the candidate keeps the existing region upload. The injected pre-write failure retains both original bytes and UTC. Independent patterned backgrounds change between frames. Complete and 64-row foregrounds match expected bytes, including the first pixel below the region and the final pixel. A later regional upload preserves the full tail. Omitted foreground, fabricated opaque black, previous-frame tail and displaced foreground mutants each fail their respective byte checks. The
full-background copy is 325 × 530 × 4 = 689,000 bytes per new background in this owner; its native cost is unmeasured.

The separate `crossOwner` rows in that receipt connect the real `moon-detail.mjs` adoption, join, encoding and canvas writes to the real preview and solar-mask publishers. The DOM, canvas storage, layout, atmospheric fields, clock and image decode transport are fixture boundaries. Each raster write records both backing digests, detail visibility and owner, displayed mask, preview frame identity and publication receipt. Settled rows follow the synchronous return.

| Fixture transition | At the detail write | At task end |
|---|---|---|
| Healthy new background | Both original and candidate write the second atmospheric Moon detail while the original background is still current | Both reach the same new background and detail bytes. The original writes the background twice, the candidate once. |
| Background write throws before changing any bytes | The already-visible detail changes to the exact bytes of the successful second scene | Both retain the original sky bytes, mask and frame UTC 0 with `retained=true`, but the visible Moon-detail canvas contains the second scene's bytes. The mixed backing state persists after the task. |
| Cloud authority revoked immediately after the second detail write | The second detail is visible over the first sky. The final cloud fence rejects the superseded candidate before its background writes. | Both owners retry once using the third authority. Its detail, background and receipt settle together. The mixed state was recorded inside the task. |

A single background upload resolves the split between the background and its foreground region. The independently owned detail canvas can still publish early. Clearing details on error would withdraw the previous Moon too. Repainting a prior frame would require current material, cloud inputs and another successful write, and cannot undo an already-observed write. A bounded current-preview handover can instead stage the participant outputs privately and expose them at a shared presentation boundary. The tested one-upload patch does not implement that boundary. No task-level event here establishes a displayed browser frame, a GPU guarantee or atmospheric hold semantics.

The same receipt calls real `nativeJob()` and `nativeResultCurrent()` against separately specified inputs.
Unchanged accepted input and a renewal with identical consumed fields remain current inside the time bound;
cloud-cover-only changes remain current in the numerical sky identity. Lost weather authority, changed visibility,
changed temperature, generation change and age above 30 accepted seconds do not. This explains why simply
retaining a previous frame and calling it current cannot implement the proposed atmospheric hold. The hold needs
a distinct presentation status and an explicit authority/expiry design. The original unpublished A2 candidate
`6438b044` still cannot be reconciled from its abbreviated public record alone.

### 6.3 One quarantined refined record

`quarantineCandidate()` adds an experimental one-record data quarantine to the **actual Moon runtime**. It retains
five dedicated views from one validated refined result and its admission metadata by reference during hide. The original clear still revokes epoch,
pending work, presentation and detail. No Moon is presentable or visible through the detail double while hidden.
It introduces no hide duration or relaxed phase allowance.

On return it permits one new adoption only when the saved epoch has not been invalidated, the original clock
continues at the same rate, the new host capture is eligible, scope is unchanged, and the original geometry remains
within the existing 0.0416-device-pixel bound. The new record receives the current epoch and a new adoption token;
it retains the original geometry, physical identity, profile identity and validated buffers. It does not revive an
old worker request or accept an old epoch reply. When the production poll or request runs, it checks outstanding custody against the original clock, geometry and scope, including while paused. Stashing and the final admission check independently validate the current host state. A disqualifying lifecycle sample permanently drops custody. The diagnostic `observe()` and `presentable` reads retain the original empty-surface path and do not consume custody. A transient change that ends between lifecycle samples has no recorded invalidation. The Moon listener may see the still-paused card on return. The fixture executes the source-native `setVis` listener next; it clears the card pause and calls the real Moon request. No surface is published in the intervening paused state.

Re-admission prepares the material prefixes and blended texture on a detached detail owner and canvas. Immediately before publishing, it checks the same private record, original geometry/epoch, clock/rate, eligibility, current altitude blend and absence of a successor. Abandoned stages are disposed; if reentrant work installed a successor its canvas, detail identity and authority survive. Generation and phase changes during detail adoption produce only a current initial publication. Removing the final fence exposes a stale host callback even though a subsequent current initial record restores the final state. A nested successor that completes before the outer preparation throws also survives.

The [runtime receipt](evidence/R002F-A2/20261125-architecture/quarantine-experiment.json) executes the real runtime
through the existing Moon host fixture. In the positive short-hide case, main recomputes the initial tier once and
starts one refinement request. The research runtime re-adopts the still-current refined record, with zero initial
rerenders, zero new worker render requests and zero pending request timers. Both execute the original hide
fallback once, with no presentable surface or available detail during hide. The fixture retains 8,884,800 bytes
across five dedicated typed-array buffers. The pooled producer also returns solar, earth and coverage intermediates; at the fixture's physical grid those add 9,331,200 bytes. The candidate excludes the envelope and these intermediates. A mutant retaining the envelope exposes all three. Nonzero, distinguishable material, coverage, calendar and upper inputs keep their view identity and exact SHA-256 at re-adoption. Two host publications using the real blend function match the original upper and calendar byte digests at the respective altitude extremes. Empty physical or missing/blank profile identity and oversized backing storage cannot enter quarantine.

The 8,884,800-byte figure counts the referenced payload. The ordinary detail owner's `clear()` already retains its material and prefix tables. Incremental reachability depends on other references and GC, and private staging briefly creates another detail owner and texture. No incremental heap delta or native allocation peak was measured.

Eleven rejection cases cover generation, scene, pixel ratio, lit limb, phase, seek, clock rate, explicit invalidation,
reference profile, presentation readiness and initial eligibility. They perform no reuse and no extra publication
over their corresponding unchanged-source controls. The late-worker-reply control increments rejection while
hidden and cannot resurrect authority. Throwing the detail adoption is contained and does not produce a current
record. Nine observed hidden A–B–A changes cover scene, generation, ratio, limb, rate, seek, phase, readiness and eligibility; all discard on B, and returning to A cannot revive any of them. Disabling hidden capture validation permits the scene round trip and one reuse. With no production request at the intermediate scene, four otherwise identical reversals compare zero diagnostic reads with `observe()`, `presentable`, and repeated reads. Every arm has zero diagnostic layout reads, one reuse, one initial render, one worker render and identical restored texture bytes. Moving custody validation back into the diagnostic path spends a layout read, loses reuse and produces a different texture. The later-fence mutation and paired-listener controls are recorded alongside these results.

The positive source fixture avoids one initial computation and one refinement request. Re-admission still prepares new prefixes and a texture, and its duration on a native host is unmeasured. The fixture doubles
receivers, worker transport, canvas, detail and host composition. Native memory pressure, receiver/readback cost,
resource disposal, masked material identity and real restoration pixels still require measurement. Quarantining
data changes the accepted lifecycle resource behavior and needs owner adoption before product integration.

### 6.4 Reproduce or inspect the candidate patches

```sh
node --test --test-concurrency=1 tests/r002f-a2-resume-observer.test.cjs tests/r002f-a2-architecture.test.cjs tests/r002f-a2-quarantine.test.cjs
node tools/qa/r002f_a2_architecture.cjs /tmp/new-architecture.json
node tools/qa/r002f_a2_quarantine.cjs /tmp/new-quarantine.json
node tools/qa/r002f_a2_architecture.cjs --prepare /tmp/new-r002f-patches
```

The original quarantine patch below is retained to reproduce this historical study. Its second calendar-byte installation failed two standing Moon source assertions. The [successor quarantine-only and combined patches](R002F-A2-preview-transaction.md) route both ordinary and restored material through the same adopter. The two restored-tier assertions still require an owner decision.

The quarantine and build receipts incorporate the diagnostic-purity correction following review of `0384a207`. The prayer and preview mechanisms and their qualified source bytes are unchanged from that commit. The original and hardened observer-only receipts retain their original scope. Each output path must be new. The patch manifest binds the exact authored preimages and candidate SHA-256s.
`prayer.patch`, `preview.patch` and `quarantine.patch` are independent. Apply selected patches only in a disposable
checkout whose preimages match, then use `python tools/build_native.py`. The routine does not choose a treatment,
apply a patch to the current tree, rewrite a production pin or bypass any builder guard.

All three patches were applied together to an isolated checkout of `df644ef6`. The normal native builder completed;
a second run wrote zero files and reported all 117 generated entries unchanged. Frozen V1 and the reviewed Pages
inclusion preflight passed; no deploy was attempted. The generated candidate index SHA-256 was
`e306e3bc220c1b61ab3debb875c37e8feb63269da1879a5160dfe119dfcd100a`.
The corrected combined build passed all 58 Moon host cases and all three R0036 observation cases. The unchanged preview owner passed 27/27 at `0384a207`. With the original test adapter, that earlier combined arm passed 38 request/day cases and stopped at setup on all 52 whole-entry containment cases.

For the exact combined index above, the independent reviewer reconstructed the before/after source blocks using the admitted baseline, reviewed transformations and unchanged builder, and compared the reconstructed bytes to the combined entry. The disposable adapter then bound the first-paint and Moon-initial blocks to two fixed reviewed literals, preserving the refinement pin. The normal request/day/containment command subsequently **passed 90/90 cases**, including all 52 containment cases and their 17 behavioral mutants. This supersedes the earlier setup block for the reviewed combined arm. The research branch's test adapter and shipped pins remain unchanged. The [build record](evidence/R002F-A2/20261125-architecture/build-check.json), [reviewed literal patch](evidence/R002F-A2/20261125-architecture/candidate-prerequisites.patch) and [command log](evidence/R002F-A2/20261125-architecture/combined-admitted-containment.log) bind this result to the exact entry and adapter.
The independently built **prayer-only** arm retains the original prerequisite identities and passes all 90
request/day/containment cases, including the existing seventeen behavioral mutation controls; its generated
index SHA-256 is `cd48bc47190a2edc45f4619e7152dc2382d6ead9bd278e5d756544e0b41c54ad`.

### 6.5 Work remaining, and why it is not another source-state test

| Remaining obligation | Work available for the next executor | Precise missing evidence or authority |
|---|---|---|
| Correct first presented prayer frame | Shared publisher patch, independent full-field source oracle, unchanged scheduling and request controls | Actual rendered return sequences, at least five per tree across Fajr/Maghrib/midnight; cached pre-listener images must be distinguished from new frames |
| True back/forward cache restoration | Existing R0041 real-navigation record and the separate pre-event/callback distinction retained | A real browser with `pageshow.persisted === true`; a synthesized `PageTransitionEvent` is insufficient |
| Short-hide data reuse | Executable real-runtime prototype, eleven return invalidations, nine observed round trips, per-write checks, private-stage failure and material-custody controls | Owner adoption plus native byte/resource, timing and material/opacity evidence |
| Atmospheric hold / transactional handover | Current-to-current cross-owner staging, same-task revocation and [combined prayer/quarantine/transaction research build](R002F-A2-preview-transaction.md) | Unpublished A2 candidate, owner-bound hold semantics, first-paint/refined transitions and native compositor evidence |
| Firefox/WebKit sky host | Existing source/currentness consumers and R0041 capture tools retained | Executable engines and valid native restoration routes; no synthetic replacement |
| Final qualification and registry | Registered instruments, preimage-bound artifacts, source receipts and builder proof | Native results, independent review of the exact adopted product, owner acceptance, hosted gate/delivery if commissioned |

Local browser executables were absent; the ordinary official download failed. A separately available cloud browser
could not reach the local fixture, and its subsequent inspection was denied by browser policy. These are execution
blockers, not passing cells. No cached frame, paint time, CPU saving, human appearance preference, native memory
figure or original-candidate integration is inferred from the controlled-source results.
