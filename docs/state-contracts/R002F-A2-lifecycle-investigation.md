# R002F-A2: restoration investigation and bounded next implementation

Status: **partial research handoff; no product change, merge, acceptance or registry promotion**.
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
| Prayer-state return across Fajr, midnight and Maghrib | Source-state discriminator and currentness controls complete | Real native returns and pixel/frame timing, at least five per tree |
| Back-navigation cached frames | Existing routed finding analyzed, no new measurement | Actual back/forward restoration with `pageshow.persisted` recorded; distinguish reloads and cached pre-event frames |
| Moon data retention across short hides | Admission/invalidation proposal only | Owner scope, implementation, identity/fault controls, real timing and visual evidence |
| Firefox/WebKit sky-host observations | No claim | Valid native launches and required host routes in both engines |
| Weather held/transactional architecture | Ownership and gate boundaries recorded | Existing candidate reconciliation, architectural decision, failure/transition clips and full qualification |

The executor had no usable Chromium, Firefox or WebKit binary. The system Chromium command points to a missing
executable. A normal Playwright Chromium installation was attempted; its official download returned HTTP 403.
No browser or provider was launched by this recipe. Consequently, there is no native screenshot/clip, no first-frame
guarantee and no human visual verdict in this branch. The deterministic VM rows cannot be relabeled as those rows.

## 5. Integration guidance

This is a main-based, independent branch. Its delta is the observer, registered tests, receipt and this scoped
proposal, plus a registry pointer without verification-level changes. Production, generated assets, immutable
scientific source and frozen V1 are unchanged. The work can be folded into the lifecycle investigation while its
owner decisions remain open. Run the new observer against any proposed remedy, keep the native qualification
matrix, and retain the distinctions between task-end DOM, native callback and actual displayed frame.

All numerical observations above are controlled source reproductions. No atmospheric or interface appearance is
changed by this branch. Physical fidelity and experiential fidelity of a future remedy remain separate native
review obligations; neither is certified by a green observer test.
