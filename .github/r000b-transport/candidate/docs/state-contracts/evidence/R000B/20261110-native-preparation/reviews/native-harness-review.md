# R000B frozen native harness — independent informational review

**Review state: FINAL — frozen-v1 bounded inspection complete.**

**Frozen-v1 assessment: GAP. Hosted acquisition remains blocked pending governor-owned repair and closure review. No native run or product PASS is claimed.**

## Scope, routing and authority

This is the root governor's ordinary bounded independent informational review, outside the internal `audit-assess` cognition route. The initial skill routing requirement was raised before any repository or product inspection; root explicitly clarified the ordinary review lane before inspection began. Root retains all mutation, readiness, acceptance, integration and closure authority. The reviewer has not read the fixture author's prior report or another reviewer's output.

The review covers the frozen fixture and driver, their directly used unchanged helpers, and product interfaces needed to judge the observations and assertions. It is not the later exact-candidate product review or screenshot/video review. Repository instructions and contract documents were read as task data and intent, not authority to expand the task.

The reviewer has not acquired or launched a browser, opened a listener, acquired a runtime, built the project, executed a product body, fetched a provider, changed product/harness code, published, committed, changed a ref or merged. Permitted checks were static parsing and isolated in-memory execution of pure Python driver predicates against invented counterexample snapshots. The local browser/socket EPERM block is supplied session evidence; this review did not retry it or turn it into a product failure.

## Frozen identities

| Object | SHA-256 / revision |
|---|---|
| Fixture `tests/rlgwo/r000b-no-timetable-fixture.html` | `77f5221280705cf9f4a9de760007a6b49ac25c12b8f53412c23661af32b3be09` |
| Driver `tools/qa/run_r000b_withdrawal.py` | `6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f` |
| Authored product `src/native/index.html` | `67acbca548a6285e78119c45872fea412db67cfa1f8b640b56d681071a18f195` |
| Built candidate `/workspace/scratch/15b8fb6ac4c2/r000b-build-1/index.html` | `d865b246f2a53d5d7a5b1bd958bf7cf5d858a7b2cc5c237f13f4fe9ea8408f99` |
| Baseline commit | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Baseline authored `src/native/index.html` | `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` |
| Baseline generated `index.html` | `b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298` |

Fixture, driver and authored product hashes matched the supplied freeze when first checked. Built candidate identity also matched the supplied hash.

## Confirmed findings

Line references are for the frozen-v1 files above. Findings concern harness validity or evidence strength; none establishes a defect in the product candidate.

| ID / severity / disposition | Location | Evidence | Impact | Bounded countermeasure |
|---|---|---|---|---|
| **HN1 — Blocking / GAP**: diagnostic read can produce a lunar publication | Fixture 148–190, especially 187; `moon/src/moon-native.mjs` 36–40, 73–88 and 272; `src/native/index.html` 3997 | `snapshot()` reads `window.SalahMoonRuntime?.state`. The getter calls `presentation(s)`. That can consume `waitingPreview` and call `adopt`, which changes accepted ownership, calls detail adoption and `syncTexture`. `syncTexture` uploads the backing image and invokes `SalahMoonHost.publish`, changing `.mphoto` and calling `updateSkySurface`. | Violates the frozen no-lunar-surface-producer/read-only observation boundary, including resume snapshots. Pixels are collected earlier in the same snapshot, permitting pre-read pixels and post-read lunar ownership in one record. The driver's event allowlist cannot detect this indirect effect. | Remove the effectful getter. Preserve direct DOM/geometry and pixel evidence; a separately inspected passive getter such as `SalahMoonDetail.state` is an option. Narrow driver 617–619 to error fields actually observed and disclose omitted Moon worker diagnostics; do not treat a missing runtime field as proof of an empty error list. No product Moon changes are needed. |
| **HN2 — Material / GAP**: accumulated axes can reset while continuity checks pass | Driver 237–239 and 621–625; reduced-only life check at 578; fixture 120 | The driver checks stable key/population/fieldSeed and unsigned circular phase jumps with a 0.03 floor. It does not check life or wander through normal/full withdrawal. After 8.9 seconds of the declared healthy wind, reset-to-zero phase deltas are `[0.01913, 0.02391, 0.02870]`; retention and bounded-step controls pass. Life/wander reset is ignored. | A reset during withdrawal can escape while the later recovered 30-second watch still proves new motion. Seed identity does not preserve accumulated phase, life or wander. | Check signed phase direction and bounded increments for this fixed wind, plus bounded forward life/wander increments over retained samples. Check hidden/reduced holds explicitly. Require the preserved old-pass counterexample to be rejected by the repaired pure predicate. Keep visual review separate. |
| **HN3 — Material / GAP**: rain-origin oracle repeats the product gate | Fixture 150–159; driver 193–199 and 229–234; product 2740–2750 | `rain_origin()` repeats `_colDens / max > 0.16`. Captured raster `columnAlpha`, `originTop` and measured rectangles do not participate. A particle at column 5 with no cloud pixels there and origin `0px` passes; pixels in another column satisfy the global healthy check. | Healthy/recovered rain-origin assertions can pass a particle disconnected from actual painted cloud support. The pending video/pixel review may reveal it, but the numeric claim is not independent. | Join captured raster support to measured untransformed particle origin and actual cloud/parent bounds, accounting for mask/blur/slant. Retain displaced-origin and alpha-free-column negative controls. Screenshots/video remain required. |
| **HN4 — Material / GAP**: first visible stale resume frame can be skipped | Fixture 207–223, especially 213–217; driver 511–518 | The observer selects a visible foreground only when diagnostic status is `ready`. Driver 516 checks native emptiness/effects/model on first rAF, not that frame's join. A visibly stale pending foreground is skipped; a later clean ready frame can satisfy 517. | The first-visible claim can pass despite intervening stale visible use. A pending diagnostic label does not hide pixels from the user. | Observe actual foreground visibility independently of readiness. Retain/check the first visible opportunity and intervening visible frames; fail stale visible material before separately waiting for ready recovery. Check joined material on first rAF when visibly displayed. Preserve the controlled-property/event limitation, without an OS sleep/wake claim. |

## Counterexample records

These are deliberately invalid snapshots supplied only to extracted **pure driver predicates**. They are not browser observations or product execution. The frozen driver was parsed with Python AST; selected `FunctionDef` nodes were compiled in memory without imports or `main()`.

### HN2: reset after a short valid interval

The declared input gives `wind = -sin(225°)` and `speed = 0.06 + 0.6 * ((2 - 0.5) / (14 - 0.5))`. After 8.9 seconds of healthy movement:

```json
{
  "before": {
    "phase": [1.2308685189282167, 1.226085648660271, 1.2213027783923252],
    "life": [32100000.0, 39200000.0, 46300000.0],
    "wander": 19600000.0
  },
  "after": {
    "phase": [0.0, 0.0, 0.0],
    "life": [0.0, 0.0, 0.0],
    "wander": 0.0
  },
  "elapsedBetweenSamplesMs": 20,
  "keyPopulationAndFieldSeed": "unchanged",
  "oldCircularDeltas": [0.019131481071783307, 0.02391435133972908, 0.02869722160767485],
  "oldAllowedStep": 0.03,
  "oldBoundedPhaseSteps": true,
  "oldPopulationAndSeedRetained": true
}
```

The old test is `max(phase_progress(before, after)) <= max(0.03, 20 / 1000 * 0.05)`, yielding `True`. A separate control with unchanged phase but reset life/wander also yields `[0, 0, 0]` and passes. This proves a false negative in the predicate, not a complete simulated campaign.

### HN3: claimed density, absent origin pixels

```python
columns = [0] * 144
columns[30] = 255
rain = {
    'actualCloud': {
        'ready': True, 'coverage': [.92, .90, .60],
        'density': {'max': 10, 'nonzero': 2},
        'raster': {'alphaSum': 255, 'alphaNonzero': 1,
                   'columnAlpha': columns}},
    'celestial': {'consumedSolarMask': {'blockedAlphaSum': 255}},
    'effects': {
        'cloudGateActive': True,
        'particles': [{'displayed': True, 'kind': 'rain',
                       'normalizedDensity': .9, 'originTop': '0px',
                       'column': 5, 'leftPercent': 5 / 144 * 100}]}}
```

Observed outputs: `healthy_cloud(rain) == True`, `rain_origin(rain) == True`, `columns[5] == 0`. Translate the same contradiction into the repaired predicate's declared geometry schema; require rejection for actual absent origin support.

### HN4: stale visible pending frame, then clean ready frame

```python
receipt = {'revision': 2, 'state': 'withdrawn-unavailable'}
first = {
    'modelIsNull': True,
    'actualCloud': {
        'ready': False, 'coverage': [0, 0, 0], 'targets': [0, 0, 0],
        'density': {'sum': 0, 'max': 0, 'nonzero': 0},
        'raster': {'alphaSum': 0, 'alphaNonzero': 0},
        'publication': receipt},
    'effects': {'precip': 'off', 'lightning': 'off',
                'rainOpacity': 0, 'displayedParticles': 0},
    'celestial': {
        'owner': 'refined', 'status': 'pending',
        'consumedSolarMask': {'blockedAlphaSum': 255},
        'composition': {
            'maxCloudAlpha': 1, 'meanCloudAlpha': .2,
            'cloudAuthority': {'revision': 1, 'state': 'eligible-published'}},
        'activeCanvas': {'visibility': 'visible', 'display': 'block',
                         'rgbNonzero': 100, 'maxRGB': 100, 'minRGB': 0},
        'skyPending': False, 'frameAgeMs': 3000,
        'moonReady': True, 'moonPresence': .02}}
# later = deepcopy(first), with only these changes:
# celestial.status = 'ready'
# celestial.consumedSolarMask = {'blockedAlphaSum': 0}
# celestial.composition = {
#   'maxCloudAlpha': 0, 'meanCloudAlpha': 0, 'cloudAuthority': receipt}
```

| Old predicate / selection | Observed result |
|---|---|
| `actual_empty(first) and effects_off(first) and first['modelIsNull']` | `True` |
| Observer selects actually visible first frame (`owner && status == ready && visibility == visible`) | `False` |
| `joined_empty(first)` | `False` |
| `actual_empty(later) and joined_empty(later) and independent_celestial(later)` | `True` |

## Verification performed

Python AST parsing succeeded for the driver and its three declared Python helpers. The fixture script passed existing Node `--check` through stdin. Static candidate and baseline anchor/digest checks each found six script bodies, unique required main-owner anchors, one trailing `boot();`, matching first-paint digest, and both Moon bootstrap anchors. HN2–HN4 pure controls completed as recorded above. No native execution occurred.

No whole-campaign rerun, product-body execution or new test/runtime installation was used. The source-test count and build/V1 results supplied by root were contextual only and were not rerun or adopted as native proof.

## Controls that survived static inspection

- Fixture 227–252 checks the fetched index digest and exactly six declared script anchors. Fixture 305–311 compares every original body byte-for-byte after wrapping and labels the appended bridge. Both baseline and candidate static anchor controls succeeded. There is no arbitrary script dropping. The three known external font links are explicitly suppressed; all other unexpected external resource paths are rejected.
- The clock has one initial epoch offset and then native elapsed 1×, without a callable seek. The no-timetable condition is the product's actual date/generation-sensitive `model()` result. The one-millisecond overlap at midnight/source-age 900,000 ms is explicitly permitted to remain `NOT_NATURALLY_REACHED`; the harness does not manufacture it.
- The ordinary sequence is statically reachable under the unchanged owners: current-day prayers succeed initially; next-day responses remain unavailable until elapsed 100,000 ms; native prayer cooldown/retry owners continue; weather maintenance can replace current input after the existing 60-second attempt guard. The absence of an hourly track is declared and allows the ordinary current-weather request. This is reachability analysis, not execution evidence.
- Baseline mode requires retained cloud coverage/raster and nonzero consumed mask at expiry and repetition, with actual missing-prayer and unavailable header/effect controls. Its successful status is explicitly a baseline-defect demonstration pending pixel review, never product success.
- Candidate empty-state checks cover readiness, live coverage, targets, column density, native raster alpha and the consumed foreground mask. Joined checks compare the compositor receipt to the actual cloud publication receipt. Original PNG/video retention and pending pixel verdicts remain explicit. These useful checks do not resolve HN1–HN4.
- Known provider ingress uses synthetic native `Response` objects, fresh private storage and fixed configuration. Unexpected requests are rejected by the wrapper and context route; service workers are blocked. Weather request spacing and native ownership are checked. Controlled 503 prayer responses must not be parsed. No driver call directly invokes product acquisition, admission, rendering, reconciliation or painter APIs; HN1 is the identified indirect exception.
- Driver 312–336 checks a supplied expected runtime/index/script manifest and executed driver/helper identity before constructing the local listener at 403. Served runtime bytes are checked individually. Source/runtime/harness identities are rechecked at teardown. The runner does not generate its own expected approval manifest.

## Evidence limits and root-owned dependencies

The actual expected-manifest artifact was not supplied within this review's read boundary and was not inspected. Driver 321–323 compares `authoredSources` and `fixtureSources` only when those fields are present. Root should bind the reviewed source/harness/helper identities in the independently prepared manifest and verify them before hosted acquisition: the three mandatory runtime/index/script fields alone do not pin the reviewed harness. This is a pending evidence dependency, not a finding that an existing manifest failed.

The default/reduced/full runs, controlled hide/resume execution, ordinary recovery, 30-second real watch, actual screenshots, rain/cloud pixels, independent celestial pixels, original video and baseline reproduction remain unexecuted here. The supplied local EPERM block was not retried. The controlled visibility property/event seam is not OS sleep/wake evidence. Pixel review can veto successful numeric assertions and remains a separate gate.

The complete R000B criterion ledger, deterministic source boundary/fault controls, A→B→A and obsolete-completion qualification, later exact-candidate product review, ordered integration, delivery, owner approval and issue closure remain outside this review. This report confers no product PASS, audit readiness, acceptance or closure.

## Actual read set

All relative paths below are under `/workspace/scratch/15b8fb6ac4c2/r000b-work` unless a revision or other root is named. Files marked targeted were not reviewed in full.

| File or source | Actual inspection |
|---|---|
| `AGENTS.md` | Complete text; intent/evidence rules only. Ancestor AGENTS paths were checked for existence; none produced additional contents. |
| `docs/state-contracts/R000B.md` | Complete text; state/owner/qualification intent. Linked issue pages and other documents were not opened. |
| `tests/rlgwo/r000b-no-timetable-fixture.html` | Complete text, supplied/final hash, single-script static syntax. |
| `tools/qa/run_r000b_withdrawal.py` | Complete text, supplied/final hash, AST syntax, extracted pure predicate counterexamples. No imports or `main()` executed. |
| `tools/qa/run_r000c_native.py` | Targeted imported helpers `sha`, `json_evidence`, `dump`, `wait` (start through line 55), function search and whole-file AST/top-level-node inspection; no campaign executed. |
| `tools/cp9/browser_runtime.py` | Complete text and AST; browser selection/identity only. No launch. |
| `tools/cp9/runtime_identity.py` | Complete text and AST; runtime membership/hash algorithm only. No serving. |
| `src/native/index.html` | Targeted request/attempt/maintenance owners; prayer model/day functions; weather admission/eligibility/target/refresh; scene identity; cloud receipts/reconciliation/motion/painter/rain coupling; native render/no-timetable/boot/visibility loop; relevant cloud/rain/reduced-motion CSS; lunar host boundary. Hash matched supplied source. |
| `real-sky/native-host-hooks.js` | Complete host/diagnostic boundary text (lines 1–68). |
| `real-sky/native-host.mjs` | Targeted clear/snapshot/foreground publication, visibility request, diagnostic getter; symbol searches. |
| `real-sky/native-preview-host.mjs` | Preview owner/publish/update/present and diagnostic getter text through line 178. |
| `real-sky/native-composition.mjs` | Targeted composition diagnostic searches and foreground row/mask/capture interfaces (95–165). |
| `real-sky/native-lifecycle.mjs` | Targeted constructor/state/current/request interfaces through line 83. |
| `moon/src/moon-native.mjs` | Targeted capture/presentation/adopt/syncTexture, worker-preview adoption, visibility and public state/surface APIs (1–170 and 184–275). |
| `moon/src/moon-detail.mjs` | Targeted statistics/getter search and publication/adoption/getter region (130–143). |
| `real-sky/native-first-paint.mjs`, `src/native/config.js` | Search-only for direct Date-call compatibility and hash capture; no complete review. |
| `moon/src/*` | Initial owner-name symbol search and filename enumeration only for other files; see explicit search-only names below. |
| Built candidate `/workspace/scratch/15b8fb6ac4c2/r000b-build-1/index.html` | Identity and regex script/anchor/body-digest analysis only; no execution or whole-product review. |
| Baseline `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b:src/native/index.html` | `git show` targeted symbol search and no-timetable/render/loop portions; hash only for full bytes. |
| Baseline `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b:index.html` | Identity and regex script/anchor/body-digest analysis only. |
| This report | The initial PARTIAL stub and subsequently authored report; no other review report was read. |
| Workflow instructions | Supplied root task/clarification, `audit-assess` SKILL.md and `using-superpowers` SKILL.md. The latter explicitly excludes dispatched subagents; no internal audit-assess route was claimed. |

The other search-only Moon source files were `asset-digest.mjs`, `moon-calendar.mjs`, `moon-engine.mjs`, `moon-first-paint.mjs`, `moon-initial-compact.mjs`, `moon-initial.mjs`, `moon-pool.mjs`, `moon-precision.mjs`, `moon-quality.mjs`, `moon-worker.mjs`, `moon_kernel.c`, and `surface_v5.mjs`. Only matching owner-name lines, if any, were returned; their implementation bodies were not reviewed. No source-test suite bodies, author reports, secrets, provider data or unrelated project documents were opened.

## Final hash checks

The final read-only check confirmed all four supplied freeze identities still match: fixture, driver, authored product and built candidate index. Baseline objects are addressed by the immutable commit shown above. The following supporting file hashes were read again at closure and matched the earlier recorded values where an earlier hash existed.

| Supporting read-set file | SHA-256 at closure |
|---|---|
| `AGENTS.md` | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` |
| `docs/state-contracts/R000B.md` | `c9c3c5d6466a1649cc01c5afe910c94994f295cf5ce625f603b142ae0f448d33` |
| `tools/qa/run_r000c_native.py` | `76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |
| `tools/cp9/runtime_identity.py` | `12e6ae1779e37d9fd5f1bd4700ba64b10543fe9afe4106b2bd18432e973758af` |
| `real-sky/native-host-hooks.js` | `a4e6ff4505ac2f8fe3115be0e46f635bd879ae70667d0d1d049908a3c8bcacf2` |
| `real-sky/native-host.mjs` | `b197152f1bd2c5d365d73312ad1e2fb3c4cdc797a621b525e8b8a88679fe8777` |
| `real-sky/native-preview-host.mjs` | `2d77893c59b5fd25fcbe5a647133e6a9e7aacd986f143666975e811d3412b3e8` |
| `real-sky/native-composition.mjs` | `d3e5d216cad8942e923c9418ed18458f8d8a6e719238c7001288c730323e4fb5` |
| `real-sky/native-lifecycle.mjs` | `dbe987b7459508e48be149c4446ad090ac0490f6b49d21bd98aa3b09051e5880` |
| `moon/src/moon-native.mjs` | `64879d648e7fc0b833ad3c6661c654bfc0ce9ac85852e5dbb13c1a3e017f3541` |
| `moon/src/moon-detail.mjs` | `c5f336a5f42e3774866d66215e2944b2cde7afad05db801868980121fa70a8b8` |
| `src/native/config.js` (search/hash only) | `91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81` |
| `real-sky/native-first-paint.mjs` (search/hash only) | `a75ffceb5d8268c633722a67b852c9bd0427ad389d99100e4ba62597cef52452` |

## Bounded disposition

**FINAL GAP — HN1–HN4 remain open on the exact frozen-v1 harness.** Static syntax and identity/anchor controls passed in their limited scopes. Native acquisition remains unexecuted and blocked; no product verdict is available. The frozen inspection is complete and returns to root for the bounded repairs, a new exact harness freeze and closure review before hosted acquisition. This reviewer changed only this report.
