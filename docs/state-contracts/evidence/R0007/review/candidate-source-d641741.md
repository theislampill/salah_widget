Reviewer attestation:
- reviewer_identity: /root/r0007_candidate_review
- requested_model: gpt-6-astra
- actual_model: gpt-6-astra (self-report: GPT-6 Astra Pro; no separate backend telemetry available)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- base_sha: eebba178172f96b3ffe5ab3845bc0fffd57c6e1b
- head_sha: d641741df1397659da6ef817fa41aa975f7f3930

Report state: FINAL

# R0007 independent exact-candidate source and contract review

**Disposition: GAP-REVISE for this source/candidate review.** Two important, independently reproduced source regressions remain. No critical finding is raised. Native pixels, the mandatory platform decision, preceding accepted-main reconciliation, exact merge approval, delivery and whole-owner acceptance remain pending independently of these findings. This report grants no merge, release, lifecycle or closure authority.

Candidate tree: `ce00619ac4821469647cf3f5ff905e82936a7688`. The checkout was clean and HEAD/tree matched the requested identities before and after the read-only checks. Only this report was written. No source, index, branch, controller, GitHub, browser, native-process or hosted-resource mutation was performed. No subagent was used.

## Review boundary and contract denominator

Inputs were the owner commission `intake/prompts/02_R0007_EXECUTE.md`, the original issue and binding discussion bodies in `analysis-contract/live-r0007-intake.json`, the current `docs/state-contracts/R0007.md`, `docs/state-contracts/evidence/R0007/acceptance-ledger.md`, the complete changed executable/source surfaces and affected callers/tests. Existing source execution receipts were treated as claims to assess, not independent acceptance. Current or historical reports under `review/` and parent working notes were not consulted.

The review retains original rows 7.01–7.16, child duties A01–A09, ES07-01–15, preservation/generated boundaries and the separate terminal gates. The ES07 chronological-selection extension supersedes the old hardcoded-next-day-Fajr policy only; it does not remove original elapsed arithmetic, unavailable/recovery, actual-consumer or native obligations. The historical closure remains historical at its own bindings.

The owner's concurrent isolated engineering authorization is compatible with this review. Accepted integration remains ordered R0017 → R0007 → R000B. This candidate is not reviewed as reconciled with a future accepted R0017 corrective main; the actual incoming delta and affected evidence must be reconciled before final acceptance.

## Important findings

### SRC-01 — Discarding a known one-sided gap bound suppresses healthy endpoints at civil-day edges

**Owner:** R0007/N06 candidate ordering. **Location:** `src/native/index.html:2232–2241`, particularly the `before>=0 && after<1440` gate at 2238; the resulting uncertainty is consumed at 2263–2269. The same implementation is present in generated `index.html` and `offline.html`.

For a gap touching midnight, one neighboring supported minute lies outside the current day's profile. The code therefore retains neither bound and leaves both at infinity. Missing a lower neighbor does not erase the known upper bound, and missing an upper neighbor does not erase the known lower bound. The existing profile is sufficient to prove respectively that the gap has elapsed or that a healthy earlier target precedes it, without assigning any epoch to the nonexistent event.

Two real-Intl, real-admission/model/render reproductions demonstrate the failure:

| Admitted fixture and captured now | Supported profile fact | Required healthy result / literal independent oracle | Candidate result |
|---|---|---|---|
| `America/Santiago`, record `06-09-2026`; ordinary clocks except Fajr `00:30`; now `2026-09-06T05:00:00Z` (02:00 local) | The day's gap is minutes 0–59. First supported minute 01:00 is `2026-09-06T04:00:00Z`, already elapsed. | Sunrise `06:00`, `2026-09-06T09:00:00Z`, **240 minutes** | `endpoint-unresolved`, reason `Fajr:gap`, no target, `Countdown unavailable` |
| `America/Nuuk`, record `28-03-2026`; Fajr `22:30`, Isha `23:30`, other ordinary clocks; now `2026-03-29T00:00:00Z` (22:00 local) | The day's gap is minutes 1380–1439. Its known preceding supported minute lies after the healthy Fajr target. | Fajr `22:30`, `2026-03-29T00:30:00Z`, **30 minutes** | `endpoint-unresolved`, reason `Isha:gap`, no target, `Countdown unavailable` |

Both `admitPrayerRecord` and `adoptPrayerBundle` return true. Substituting only the baseline model slice in the same disposable VM selects the expected Sunrise240 and Fajr30 respectively, with exact equality to the literal UTC epochs above. This is a regression, not an invented timezone policy or a claim about provider incidence.

Healthy controls also passed: ordinary Santiago Fajr05:00 at the same now selects Fajr180; the existing interior New York elapsed gap selects Sunrise150. The current tests cover interior gaps but miss both day-edge forms.

**Contract affected:** original ordinary-availability/consumer preservation in 7.05/7.08, ES07-08 and the state contract's explicit rule that an elapsed gap or a later uncertainty must not blanket-disable a supported target. The current implementation is conservative beyond the known ordering evidence and incorrectly withholds valid output.

**Required correction:** retain each justified bound independently, leaving only the unavailable side infinite. Keep the gap event itself unresolved. Add real-admission/model/render controls for start-of-day elapsed gaps, end-of-day later gaps and a genuinely blocking uncertainty; preserve the inverse owner unchanged. Regenerate both delivered entries and refresh affected source/native bindings.

### SRC-02 — A newly enforced unpadded date comparison withdraws valid admitted years below 1000

**Owner:** R0007/N06 eligibility. **Location:** `src/native/index.html:2252–2254`, using the unpadded `prayerDayFields().dateStr` constructed at 2217. Admission's canonical date is constructed with a year padded to at least four digits at 1000; current-day ownership uses the same padding at 1120.

`prayerDayFields` converts the year to a number, then constructs `07-09-99`. A correctly admitted year-99 record carries `07-09-0099`. The new equality guard rejects that valid record, even though its numeric day, zone, generation and all six clocks match the captured current context and the UTC inverse is supported. `model()` returns null, and `render()` withdraws the entire current timetable as `Prayer times unavailable`.

Read-only reproductions used ordinary UTC clocks, captured now `<year>-09-07T01:30:00Z`, and the canonical four-digit admitted Gregorian date. The existing test helper emits unpadded years, so the reproducer corrected the fixture's `date.gregorian.date` before invoking actual admission and adoption; no product validation was bypassed.

| Year | Admission / adoption | Candidate | Baseline model with the identical admitted record |
|---|---|---|---|
| `0001` | true / true | `current-record-unavailable`; null model; whole prayer withdrawal | Fajr05:00, 210 minutes |
| `0099` | true / true | same failure | Fajr05:00, 210 minutes |
| `0999` | true / true | same failure | Fajr05:00, 210 minutes |
| `1000` | true / true | same-day Fajr05:00, 210 minutes | same healthy result |
| `2026` | true / true | same-day Fajr05:00, 210 minutes | same healthy result |

The calendar/admission and inverse owners deliberately support positive Gregorian years including 1–99. This finding concerns supported UTC inputs; it does not claim arbitrary historical second-offset support. The failure is introduced by the new comparison, although the old helper's unpadded returned string predates the candidate.

**Contract affected:** 7.01/7.02/7.06/7.08 and ES07-11/12/15: admitted identity must be coherent, and a valid current timetable must not become unavailable because of inconsistent representations of the same civil date.

**Required correction:** normalize the model's day identity consistently with admission/ownership, preserving the actual admitted civil day. Add padded-year same-day and civil-successor consumer cases with years1/99/999 and the year1000 healthy boundary. Regenerate delivered entries. This does not authorize a general calendar or timezone rewrite.

## Compact executable reproduction

Run from the exact candidate worktree. This script reads the baseline model into memory and exercises disposable VM realms only. It writes no file and performs no browser or network action.

```js
const {modelRealm, loadRender, prayerRecord, slice} = require('./tests/r0008-clock-harness.cjs');
const {execFileSync} = require('node:child_process');
const base = execFileSync('git', [
  'show', 'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b:src/native/index.html'
], {encoding:'utf8'});
const oldModel = slice('// build everything render() needs', '// draw the solar-prayer arc', base);
const cases = [
  ['America/Santiago','2026-09-06','2026-09-06T05:00:00Z',{Fajr:'00:30'},'2026-09-06T09:00:00Z'],
  ['America/Nuuk','2026-03-28','2026-03-29T00:00:00Z',{Fajr:'22:30',Isha:'23:30'},'2026-03-29T00:30:00Z'],
  ...['0001','0099','0999','1000','2026'].map(y =>
    ['UTC',y+'-09-07',y+'-09-07T01:30:00Z',{},y+'-09-07T05:00:00Z'])
];
for (const [zone,date,now,clocks,target] of cases) {
  const c = loadRender(modelRealm({zone,wall:Date.parse(now),globals:{today:null,tomorrow:null}}));
  c.context.input = prayerRecord(date,zone,clocks);
  c.context.input.date.gregorian.date = date.split('-').reverse().join('-');
  const admitted = c.run('admitPrayerRecord(input,input.date.gregorian.date).ok');
  const adopted = c.run('adoptPrayerBundle(input,input.date.gregorian.date,null,true,false)');
  const state = c.run('selectPrayerEvent(today,tomorrow,simNow(),nowParts()).state');
  const current = c.run('model()'); c.run('render()');
  const text = c.dom.querySelector('.left').textContent;
  c.run(oldModel); const previous = c.run('model()');
  console.log({zone,date,admitted,adopted,state,text,
    candidate: current && [current.nextKey,current.leftMin],
    baseline: previous && [previous.nextKey,previous.leftMin],
    expectedEpoch:Date.parse(target),expectedMinutes:(Date.parse(target)-Date.parse(now))/60000});
}
```

## Independent checks and positive assessment

Environment: Node `v24.22.1`, Linux x64, ICU `78.3`, timezone data `2026e`. These are source/VM observations, not Windows or native-browser qualification.

| Check actually executed | Result |
|---|---|
| `node --test tests/prayer-next-event-state.test.cjs tests/r0007-countdown.cjs tests/r0008-timezone.cjs tests/r0018-prayer-row-status.test.cjs` | Exit0; 121 pass, zero fail/skip/TODO |
| `node --test tests/r0002-admission.test.cjs tests/r0005-adoption.test.cjs tests/r0005-day-return.test.cjs tests/r0020-clock.cjs tests/r000a-markers.test.cjs` | Exit0; 153 pass, zero fail/skip/TODO |
| `node --test tests/real-sky/native-prayer-arc-samples.test.cjs` | Exit0; 4 pass, zero fail/skip/TODO |
| `python tools/verify_v1.py` | Exit0; frozen V1 payload and anchored manifest pass |
| Independent baseline/candidate region and whole-file comparison | Authored/root/offline model and render slices agree exactly; all other bytes in each of the three HTML files are unchanged from base |
| Moon manifest comparison | Only `/source/src/native/index.html` changed |
| Additional adversarial real-admission probes | Reproduced SRC-01 and SRC-02 despite all278 existing tests passing |

The claimed 278 passing affected controls are independently reproduced. Their truth is compatible with the two missing edge cases; the total is not a complete contract proof.

Positive source assessment:

- Candidate/result arrays and scalar event fields are frozen and ephemeral. The target retains actual source-record identity, zone, date, key, source clock and generation. No persisted event history or second scheduler was introduced.
- For supported unique inverses, epoch ordering and declared rank enforce strict future selection, including exact ties and reordered next-day Isha. The ordinary Fajr360 control remains healthy. Fold candidates keep all alternatives; the tested fold with elapsed wall clock but a future alternative blocks false precision. Unavailable inverse results are never converted into an endpoint.
- `model` captures now once. All next key/time/date/zone/epoch aliases and elapsed subtraction come from the single selected target. The selected row and arc marker consume that key, and next-day marker/time substitution uses the selected record clock.
- Current labels, Forenoon, elapsed rows and wall progress remain explicit compatibility behavior. Before-first progress exposes no fabricated previous date/epoch. A nonunique previous endpoint is decorative; invalid spans have a finite fallback. The findings do not justify turning all progress into UTC fractions.
- Missing/wrong/rejected next data retains valid current timetable/calendar output and removes unsupported next highlighting. Real held-prefetch adoption and the existing dirty loop restore frozen12/24h output in source tests. A→B→A and late reply controls preserve generation/day ownership. No acquisition or render-loop owner was edited.
- Mutation anchors are unique and attached to the actual changed owner. HardcodedFajr, name-order, lost-date, ambiguous inverse, independent label, wall subtraction, +24h and complete missing-next-wakeup controls reach their intended consumer assertions. The single adoption-hook removal is correctly reported as a surviving redundancy control because request finalization also wakes the frame; it is not misreported as a killed mutant.
- Six candidates per consulted day and at most the existing matching successor bound the work. Existing day-profile caching is reused; the warm same-day test confirms one wall projection plus six bounded endpoint round trips without rebuilding the profile. No extra day horizon, timezone package or local prayer calculation appears.
- README/DESIGN explain chronological selection, stable ties, unavailable highlights and decorative progress while retaining the existing formatter precision and next-visible-frame recovery description. The source-linked contract and ledger retain native/platform/integration gates rather than declaring whole-owner completion.

### Exact source/generated bindings independently checked

| File / region | Candidate SHA256 |
|---|---|
| `src/native/index.html` | `dae7f12601732d7d8d6edab447f9182a7845ace4747048a57e8f5f95f65fe523` |
| `index.html` | `4f63d01b85c7979ba884a58ce6a3edc071047444efee0eb2a405fe58023a2256` |
| `offline.html` | `c56cf7e78cd2c924853982e3fc7f83ad08380de774fefd91c8fb327be7dd3c43` |
| Model slice: `// build everything render() needs` through immediately before `// draw the solar-prayer arc` | `2cbd552a7b7f24d0f448e570540925d5290ced86662ae8bb51e5c8bf0644c0fc` |
| Render slice: `function render(){` through immediately before `function updateSimClock` | `96042bc80d5518f671dd62139fcc8180f42576139dd8448c3ead75ba26d36419` |

The two region hashes use the delimiters stated here; the render slice is intentionally narrower than the harness slice beginning at `let _lastBolt=-1`. Outside those regions, byte equality proves the inverse/clock, admission/adoption/dirty loop, calendar, physical arc, Moon/motion and other authored HTML owners were not edited. Changed caller inputs still require their affected native preservation evidence.

## Native runner/oracle review and pending gates

I inspected `tools/qualification/r0007_native.py`, the changed native fixture variants, all recipe case identities/action/assertion structures, the existing `tools/cp9/r0007_browser.py` consumer/checker and `.github/workflows/r0007-native.yml`. Static review found no additional concrete critical/important source finding in that orchestration scope.

The launcher binds a clean candidate, preserves literal recipe oracles, orders declared healthy controls before mutants, retains fresh attempt directories and producer exits, and checks candidate identity before cases and source bytes at the end. The current driver writes its final summary after context/browser/Playwright/server cleanup; absence of that summary prevents continuation. Timeout containment is scoped to the owned process/group and stops further launches with cleanup unverified. A generic exit1, setup failure, unrelated assertion, page error or missing trace cannot satisfy the exact mutant failure substring gate. These are static findings, not executed cleanup/platform claims.

The healthy result remains `SOURCE_ASSERTIONS_MET_PIXELS_PENDING`; the launcher explicitly keeps native acceptance partial. Recovery captures after250ms test the actual latest completed output, while the recipe expressly leaves earliest eligible/presented-frame verification to all-render traces and video. That distinction must survive final reconciliation: neither a later correct still nor zero launcher exit alone satisfies 7.07/A05/ES07-06. First-current ordinal mismatch must remain partial until the retained original video and completed-render sequence justify the actual presentation claim.

| Contract family | Source-review conclusion / remaining gate |
|---|---|
| 7.01–7.05; ES07-01–04,07,09,11,13,15 | Main selection/arithmetic/tie/interval path is exercised; SRC-01 and SRC-02 require revision. Native target/arc consumer acceptance remains separate. |
| 7.06–7.08,7.11,7.13; ES07-05,06,08,10,12 | Missing-data, generation, real adoption and dirty-frame source controls pass within their inputs; both findings expose additional availability failures. Final first-visible/native recovery remains pending. |
| 7.09–7.10; A06 | Literal UTC/source-render and meaningful mechanism controls execute. They do not independently certify native DOM/raster or every originally required native mutation binding. |
| 7.12; A01–A02; ES07-13–14 | Protected byte boundaries and generated parity verified. Actual same-input native SVG/crop comparisons, readable325×530/header/footer and scoped preservation still need exact-candidate review. |
| 7.14; A03 | Current documentation matches the intended bounded behavior; it cannot cure the two concrete implementation discrepancies. |
| 7.15; A04–A07 | Actual Chromium/Firefox DST/format/recovery, native preservation and the mandatory Windows binding or entitled-owner platform amendment remain open. Historical qualified claims may be rebound only within proved relevant equivalence. |
| 7.16; A08–A09; integration/delivery/terminal ledger gates | This is one independent source report only. Resolve findings, review the successor, reconcile latest accepted main and all raw native/platform evidence, then obtain exact owner approval and verify actual delivery/certificate/closure. None is supplied here. |

Declined-to-judge behaviors are native pixels/readability, actual visible motion, Moon opacity, first presented frame/video ordinal association, Windows browser execution/cleanup, live-provider incidence, hosted check outcomes, latest accepted-main integration, public served bytes and formal audit lifecycle. The assigned read-only source review had no native or hosted execution authority/evidence for those claims. Their absence is an explicit pending gate, not evidence that the runtime is defective and not a reason to omit this completed source review.

## Required disposition

Return the candidate to the R0007 implementer for SRC-01 and SRC-02, preserving the valid inverse and ownership boundaries. Review the revised exact head/tree after focused real-admission/render regressions, generated refresh and affected qualification. **This exact candidate remains GAP-REVISE; final whole-R0007 acceptance remains pending.**
