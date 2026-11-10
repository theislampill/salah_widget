# R000B committed candidate source review

Report state: FINAL

## Bounded verdict

**BLOCKED for source-only acceptance of this exact candidate:** F01 is a
confirmed P2 healthy-refresh ordering regression. The root accepted this as an
open regression occurrence (`o15`); no repair was performed by this reviewer.
No further confirmed product defect was found in the reviewed committed delta.

**PASS for the specifically checked identity/preservation properties:** exact
head/tree, declared build-input and generated-output hashes, deterministic
owner-to-generated textual parity, protected-path equality, and retained-log
identity checks described below.

**GAP, separately owned:** new native pixels, motion and joined final acceptance
remain unqualified here. Neither retained Node passes nor historical native
acceptance waives those gates. This is an informational reviewer assessment,
not an IMPLEMENTAUDIT readiness, merge, delivery or closure decision.

## Scope and identity

This is an independent, bounded source/code review of committed range
`eebba178172f96b3ffe5ab3845bc0fffd57c6e1b..9dabdcf338a7307c0256dcdccac48326b357f0d5`.
Expected and observed head: `9dabdcf338a7307c0256dcdccac48326b357f0d5`.
Expected and observed tree: `916d5d6ad09ae269095187a82b18c64b5684a79a`.
Baseline tree: `6b94a3933f9d1381b1c2ceaab287c93afb215ecb`.
The committed delta contains 25 changed paths. Untracked native harness/workflow
work is outside this review. No native/browser, build, listener, remote, or
provider action was performed. Root separately authorized the single bounded
pure Node product-fixture probe recorded in F01 and reproduced in Appendix A;
the remaining verification was read-only source, hash and retained-log analysis.
No merge, integration, readiness, native-pixel or final acceptance authority is
claimed. Preceding R0017 corrective → R0007 acceptance remains an owner/root
integration dependency.

## Correctness / Bugs

### F01 — P2: a healthy refresh can clear and snap an established deck before the next complete render

- Category: Correctness / Bugs; Tests / Validation.
- Owner/source: `src/native/index.html`, `cloudAuthorityMatches()` (2560–2564),
  `reconcileCloudPublication()` (2600–2604), `withdrawCloudState()` (2588–2598),
  and `applyCloudState()` (3080–3098); actual capture caller
  `real-sky/native-composition.mjs`, `NativeForegroundCapture.capture()`.
- Evidence: Root-authorized, bounded Node probe on committed head `9dabdcf3…`
  used the unchanged committed `tests/weather-no-timetable-fixture.cjs`, real
  admission, real accepted next-day prayer bundle/model, and real
  `NativeForegroundCapture.capture(183)`. Only the declared VM time/transport,
  canvas and alpha-sentinel boundaries were supplied. No product or harness
  file was edited; no browser, network, build or listener was used.
- At wall time `1788901251000` (2026-09-08 21:00:51 UTC), the timetable was
  available throughout both orderings. The published record A remained eligible:
  source age `891000` ms, receipt age `61000` ms, target generation `0`,
  latitude `24.47`, longitude `39.61`, live lane. Its source-valid time was
  `1788900360000`, retrieval `1788901190000`, code `95`, total cloud `95`,
  and layer coverages `[0.92, 0.90, 0.60]`.
- A real `fetchWeather()` replacement installed record B with the same target,
  code and total cloud, source-valid time `1788901200000`, retrieval
  `1788901251000`, and layer targets `[0.80, 0.75, 0.50]`. B was also eligible;
  `_renderDirty` was set, but the full native render had not run yet.
- **Capture-before-render:** exact-record mismatch caused capture reconciliation
  to publish `withdrawn-unavailable`, reason `complete atmosphere unavailable`,
  despite `model() !== null`. Readiness became false; coverage, targets and
  retained raster became zero; captured sentinel alpha was `0`. The subsequent
  ordinary `render()`/painter snapped coverage to `[0.80, 0.75, 0.50]`.
- **Render-before-capture control:** the same records and time preserved
  readiness and eased coverage to `[0.9104, 0.888, 0.592]`, the existing 0.08
  healthy-refresh rule. Capture retained nonzero sentinel alpha (`192`).
  Population `11.432099999998172` and phases `[0,0,0]` were unchanged in both
  cases. This proves a coverage/readiness discontinuity, not reseeding.
- Impact: the independent capture/composition path can turn a healthy same-target
  refresh into an empty publication and a first-deck snap. This contradicts the
  preserved healthy-refresh easing claim in `docs/state-contracts/R000B.md` and
  the healthy/continuity requirements ES0B-03 and ES0B-14. The fixture proves
  actual owner state and captured bytes at its declared sentinel boundary;
  native flicker frequency or appearance is not claimed.
- Confidence: HIGH for the source ordering and easing regression; native
  visibility remains unjudged.
- Effort: bounded owner/join repair plus focused ordering regression.
- Risk: a broad bypass would revive the stale/no-timetable bug or let B's
  timestamps authorize A's bytes. Preserve exact target/generation and source
  freshness while distinguishing a healthy full-atmosphere handoff from the
  intentionally withheld no-timetable replacement.
- Fix sketch / implementation route: reconcile the healthy complete-atmosphere
  publication before capture can revoke/reset its established deck, or retain
  only a separately validated consumed authority through an explicitly bounded
  same-target handoff. Do not invent a timetable, new loop, timestamp renewal or
  blanket record-identity bypass. Root/source owner selects the narrow repair.
- Repair class: product-or-skill defect.
- Acceptance criteria: both orderings above preserve the expected healthy
  easing/population; true expired, target-superseded, cold and missing-timetable
  replacement cases still clear before capture; obsolete decode cannot restore
  a previous receipt.
- Verification: add the actual admitted-refresh → capture → render ordering and
  render → capture control to the focused suite, then rerun affected source,
  generated and native continuity/withdrawal controls. No new test execution
  beyond the expressly authorized probe is performed in this review.
- Rollback / Plan Closure: repair source and canonical outputs coherently;
  retain conservative true-unavailable withdrawal. This row is OPEN and prevents
  a source-only PASS for the current candidate pending owner resolution.
- Rejected/deferred rationale: not applicable; confirmed current source defect.
- Remaining risk: real browser scheduling/visibility and resulting native
  appearance need the separately owned native qualification.
- Route: DMAIC.

## Tests / Validation

### Actual evidence checked

| Evidence | Observed result | Boundaries |
|---|---|---|
| `evidence/source/r000b-final-node.log` | 114 passing test lines; trailer 114 pass, 0 fail, 0 skipped, 0 TODO. Source SHA-256 `67acbca548a6285e78119c45872fea412db67cfa1f8b640b56d681071a18f195`. | Retained execution; actual source owners inside VM/canvas/clock/transport boundaries. No new execution of this suite in this review. |
| `evidence/generated-cohorts/root-source-after-rebind.log` | Same 114 passing test names and 114/0/0/0 trailer; source SHA matches. | Its own source banner selects `r000b-build-1/src/native/index.html`. It is an authored-source rerun in the build copy, not evidence that all 114 tests executed generated `index.html`. |
| `final-cohort-results.json` and all ten named raw logs | 312 passes, 0 failures, 4 preserved TODOs; every listed test-source and raw-log hash matched. | Mixed TAP and explicit case counters; not 312 independent experiments. The relevant WEATHER/continuity logs explicitly bind generated `index.html` SHA-256 `d865b246…`. |
| `shared-harness-results.json` and all seven raw logs | 102 passes, 0 failures, 0 TODOs; every listed source/log hash matched, and TAP totals agreed. | Retained affected fixture compatibility coverage. No claim about browser script startup from these VM results. |
| `rebound-adapter-admission.log`, `rebound-contract-controls.log`, and selected `tests/r0017-adapters.test.cjs` assertions | Split-Moon profile; `runtimeQualified:false`; six selected admission controls pass. | Unknown/missing/duplicated/moved/altered prerequisite scripts remain rejected. This is explicit source admission, not native execution. |
| Reviewer probe, Appendix A | Both orderings execute successfully and discriminate F01 exactly. | One authorized in-memory product-fixture probe, actual admission/model/capture owners, sentinel alpha, no pixels. |

The source log's SHA-256 is
`b5bb38c2e16ee7a83ebb1773d8925a1ba99eb329970f38963cc7dc617b3ceb16`;
the build-copy rerun log's SHA-256 is
`bb96a45c43d2c019e38fd50d3018bf19b57831a1973adb0cc349f3f6fbd96c04`.
These are file-identity checks, not signatures of independently witnessed
historical execution.

### Test strengths and uncovered ordering

The new source tests reach actual admission, the real missing-day `model()` and
`render()`, cloud mutation, painter, column density and retained-raster sentinel.
They cover inclusive source/receipt bounds, +1 ms future rejection, warm/cold
no-model policy, fresh replacement/recovery, same-coordinate new generation,
A→B→A obsolete settlement, hidden/reduced resume, and diagnostics that leave
publication state unchanged. The retained new host tests reach the real
capture, solar-publication, preview and refined commit functions. They explicitly
substitute the numerical sky and Moon-detail boundaries and therefore establish
ordering/ownership, not rendering quality.

All seven required mutation mechanisms alter actual source and require an
`AssertionError` at the consumer discriminator. Setup or syntax failure is not
counted as a killed mutation. The healthy control runs before each mutation.
This is materially stronger than merely asserting the presence of guard text.

The missing discriminator is the ordering in F01. The healthy-refresh control
in `tests/r0024-cloud-expiry.test.cjs` calls `cloudView()`, which calls `f.view()`
and thus performs the complete atmosphere/paint before the painter. The
continuity tests similarly modify/admit weather and call `render()` before
painting. They do not interpose the independent foreground capture between
actual weather settlement and `_renderDirty` consumption. The new replacement
host tests deliberately use a missing-timetable setup, so their correct
withholding result does not establish healthy full-model continuity.

### Generated and protected identity

All 18 `inputs` entries and all four `generated` entries in
`evidence/build-1/build-receipt-complete.json` matched exact committed blobs.
The transfer receipt binds the complete build receipt by SHA-256
`645de37ae0912cf7213623fedc0caf4dd1f7ed50160386b8fa5253dc87168803`.
The retained receipt reports build, V1 and protected-diff exit codes of 0;
`v1.log` says `PASS: frozen V1 payload and anchored manifest`. I did not rerun
the builder or V1 executable.

| Committed generated path | Verified SHA-256 |
|---|---|
| `index.html` | `d865b246f2a53d5d7a5b1bd958bf7cf5d858a7b2cc5c237f13f4fe9ea8408f99` |
| `offline.html` | `c3ce5d1097a396c35aef0b09a5614bfe937bf8041571f186419a1b7ffc0d7980` |
| `real-sky/native-sky.js` | `426754834c6c116c4521ad5067bb1e37a9845830fc07ebbb62dd22fcdc757d66` |
| `moon/BUILD.json` | `c2cec8e2b0f57f7a86f59a8bba0c7f59e3cbb7ecdbd749d1d3dae3386a613bd6` |

Read-only, in-memory textual comparisons independently established:

- The authored native runtime plus the unchanged declared builder transforms
  (catalogue replacement, guarded elevation handoff, scene/notify hooks and
  committed host-hook insertion) is byte-identical to the root native runtime.
  That runtime body hashes to
  `a7f638759e3ebdb22285ec30aec25e4abc3caae6cfc07f367ab753f15da997b6`.
- The old generated first-paint body with only the builder-concatenated
  `native-composition.mjs` and `native-preview-host.mjs` replacements is exactly
  the new first-paint body. Its hash is
  `be62ab92d4eb436981a2a3f8ce48c4961249c2904f14d31435f75d8a2657a9c7`.
  This agrees with the explicit single first-paint pin change and the retained
  `first-paint-owner-rebind-proof.json`; both Moon prerequisite pins are unchanged.
- The old `native-sky.js` with only transformed composition/host owner replacements
  is exactly the new bundle. No scientific core delta is hidden in that bundle.
- Root and offline native runtime bodies are equal; the offline expanded sky
  body is exactly `native-sky.js`. Of 75 offline script blocks, only positions
  1, 3 and 6 changed (zero-based: first-paint, native runtime, sky bundle).
  All 68 embedded Moon-data blocks are unchanged.
- `moon/BUILD.json` differs only at `/source/src/native/index.html`, from
  `6054f1eb…` to the verified authored hash `67acbca5…`.
- A fresh read-only committed diff exited 0 with no bytes for `v1`,
  `vendor/real-sky`, `real-sky/core`, `moon/src`, `moon/assets`, the Moon kernel,
  native/Moon builders, the horizon transform, authored config/builder and
  generated config/builder. `git diff --check` passed for the reviewed range.

### Substantiated source strengths

- The small private publication associates a frozen serializable receipt with
  the actual consumed record. Generation and coordinates prevent same-site new
  generation and A→B→A reuse. Current source/receipt TTL constants and the
  zero-future policy are unchanged.
- Withdrawal joins targets, coverage, readiness, density and the actual native
  backing canvas, with explicit physical/optical effect withdrawal. Repeated
  identical withdrawn painter opportunities avoid repeating DOM sink writes.
  Raw provenance/cache ownership is not deleted or renewed.
- Capture checks current weather before reading cloud bytes; final-publication
  checks are pure. Pending decode context is cleared on completion, error and
  cancellation, and does not become part of the retained decoded-resource cache.
  Revision fencing protects a recursively published successor from its old
  callback. Failed detail preparation can retain only a still-current cloud
  receipt, not merely an independently current astronomical job.
- The full/no-model native paths share the narrow cloud boundary. No new
  request, timer or producer loop is introduced. The painter's population,
  phase, lifecycle and wander mathematics are unchanged, as are the independent
  Moon/scientific source owners. F01 is a failure of coverage handoff, despite
  those otherwise preserved identities.

## Docs / Handoff

The committed plan, state contract, README, DESIGN and HANDOFF consistently keep
qualification in progress and separate engineering, native output, exact review,
ordered integration, owner merge approval, delivery and deliberate closure.
They declare the warm/cold/replacement no-timetable policy and identify the
actual state owners. The healthy-easing statement in the state contract is
currently contradicted by F01; repair the behavior and its discriminator rather
than silently removing a preserved acceptance obligation.

The original issue, full ES0B amendment, B01–B18 matrix, corrected certificate
and historical independent acceptance were read for obligation and scope
custody. Original source-age/cache/radar qualifications are not reclassified
because this review began. Equally, changed painter/capture/host interfaces
prevent importing old B15/B16 pixels as acceptance of these changed bytes.
Original cold-Moon, Firefox video/PNG-route and scientific/startup/performance
limits retain their historical dispositions; this review does not reopen or
waive them. The complete current ledger and public/native candidate join remain
root-owned work outside this bounded source report.

No new credential, interpreter-input or external-effect concern was identified
in the changed runtime hunks. This is not a repository-wide security audit.
Repository, test and external contract content was treated as evidence; no
publication, provider, user profile, or other-owner effect was performed.

## Finding Row Contract

F01 above supplies the required title, category, evidence, impact, effort, risk,
confidence, owner/source, repair class, route, fix sketch, acceptance criteria,
verification, rollback/closure and remaining risk fields. No additional
LOW-confidence lead is being promoted into a defect or new independent gate.

Dismissed observations: equal-byte presentation reuse intentionally excludes the
receipt from the pixel comparator, then refreshes the consumed presentation
record only after a new capture/currentness check; the clear-mask synchronous
fast path still goes through the same commit fence. The source and focused
reentrant/late-decode controls support those designs. A contrary native result
would reopen the affected finding, but none is asserted here.

## Declined-to-judge behavior

- Native expired/no-prayer → withdrawn → replacement/recovery pixels: no browser
  acquisition or screenshot/clip inspection was delegated. Alpha sentinels and
  zeroed numerical fields do not establish visible removal.
- Real elapsed default/reduced/full cloud motion, rain origin, absence of
  slideshow/flicker, header/footer readability and 325×530 geometry in affected
  scenes: retained source controls and unchanged CSS are insufficient for the
  required new native judgment; F01 adds a concrete continuity regression to fix.
- New Moon opacity, refined terrain, Sun/catalogue quality and no-blank handoff
  under actual detail/decode failure: actual protected source is unchanged, but
  changed join owners need their affected native evidence. Moon-detail test
  doubles are explicitly not terrain or compositing proof.
- Browser decode scheduling, CSS fades, real document visibility/BFCache or OS
  sleep/wake: the Node fixture supplies contained boundaries, not those platforms.
- Live provider correctness, geolocation, deployment/public served bytes, full
  Windows/two-engine behavior and final exact-candidate public acceptance: none
  was accessed or executed, and historical scopes are not transferred.
- The untracked native harness/workflow, complete live acceptance ledger,
  R0017/R0007 integration, merge approval and issue lifecycle: outside this
  committed source review and retained with root/owner authority.

## Actual read set

All repository reads below refer to the exact committed head unless explicitly
described as the bounded probe's prechecked working-copy fixture input. No prior
candidate-review report was consulted. Historical acceptance comments were
consulted only because the task named them as authoritative carried-scope data.

**Instructions/specification and historical scope:**

- `AGENTS.md` (whole); `docs/real-sky/INTEGRATION.md` (whole);
  `docs/moon/QUALIFICATION.md` (whole).
- `docs/state-contracts/R000B_IMPLEMENTATION_PLAN.md` and `R000B.md` (whole).
- `/workspace/scratch/15b8fb6ac4c2/execution_packet/contracts/COMMON_EXECUTION_CONTRACT.md`
  (whole). The initial shorthand `/execution_packet/...` lookup was absent;
  root supplied the corrected absolute path before the contract assessment.
- `/workspace/scratch/15b8fb6ac4c2/intake/issue11.md` and
  `comment-6700189703.md` (whole, including all ES0B rows);
  `comment-6073038339.md` (original matrix and surrounding scope);
  `comment-6178186713.md` (structured certificate disposition/temporal-policy,
  runtime, delivery/closure and limitation fields); `comment-6178296345.md`
  (historical independent acceptance and retained limitations).
- `/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/references/audit-playbook.md`
  (whole). The generic using-superpowers skill was read once and explicitly
  exempts dispatched subagents; no internal audit child skill was invoked.

**Committed implementation and distribution:**

- Entire committed source diff for `src/native/index.html`; surrounding actual
  admission/eligibility/selection/target/cache/fetch/forecast/decision owners,
  cloud receipt/withdrawal/painter/motion/rain, full/no-model atmosphere/render,
  diagnostics and existing-loop callers.
- Changed functions and surrounding flow in `real-sky/native-composition.mjs`,
  `native-host-hooks.js`, `native-host.mjs`, `native-preview-host.mjs`;
  unchanged `moon/src/moon-detail.mjs` compose/adopt/clear call context.
- `tools/build_native.py` (whole) and the relevant entry/concatenation/source
  association portions of `tools/build_moon.py`.
- All generated changed bodies in `index.html`, `offline.html`,
  `real-sky/native-sky.js` by exact blob/hash and textual owner-delta comparisons;
  `moon/BUILD.json` by complete structured comparison. Embedded unchanged
  payloads were compared by bytes, not manually interpreted as scientific data.
- Full changed hunks in `DESIGN.md`, `README.md`, `HANDOFF.md`.

**Tests and fixtures:**

- Whole new files: `tests/weather-no-timetable-fixture.cjs`,
  `weather-no-timetable-withdrawal.test.cjs`,
  `weather-withdrawal-authority.test.cjs`,
  `weather-withdrawal-mutations.test.cjs`, and
  `tests/real-sky/native-weather-withdrawal.test.mjs`.
- Whole `tests/r001d-harness.cjs`, `r0025-context.cjs`,
  `r0024-cloud-expiry.test.cjs`, `r0025-continuity.cjs`,
  `r0025-lifecycle.cjs`; selected admission/temporal/cache/expiry/radar/policy
  assertions and extraction setup in `r000c-weather.test.cjs` and
  `r0024-weather.test.cjs`; selected script-admission assertions in
  `r0017-adapters.test.cjs`.
- Changed hunks in `tests/native-script-contract.js`, `r0003-harness.cjs`,
  `r000b-sky-withdrawal.test.mjs`, `tests/real-sky/native-head-handoff.cjs`,
  `native-host-composition.test.mjs`, and `native-preview-host.test.mjs`.
- Hash-only binding of the other test source files listed in the two cohort
  JSON manifests; no broader assertion-inspection claim is made for those files.

**Retained evidence and fresh checks:**

- Complete source log and parsed complete build-copy rerun log named above;
  complete `final-cohort-results.json`, `shared-harness-results.json`, all ten
  final-cohort and seven shared-harness named logs (hash/trailer/failure scans),
  plus explicit whole reads of the continuity/lifecycle/head-handoff output.
- `rebound-adapter-admission.log`, `rebound-contract-controls.log`,
  `first-paint-owner-rebind-proof.json`, `build-receipt-complete.json`,
  `transfer-receipt.json`, and `v1.log`.
- Git base/head/tree identities, complete changed-path list/stat, committed
  protected-region comparison and `diff --check`; fresh SHA-256 comparisons
  of all 18 build-input and four output entries, and all cohort source/log pins.
- The exact authorized probe in Appendix A, with committed-byte preflight and
  observed results documented in F01. It wrote no file; this report is the only
  reviewer-authored artifact.

## Appendix A — Exact executable F01 probe

Executed as the following here-document in
`/workspace/scratch/15b8fb6ac4c2/r000b-work`, exit code 0. The assertions establish
owned setup and both eligible records; the printed outputs discriminate the
regression from the render-first control. `__fixtureNextPrayer` is the unchanged
`prayerForDate('09-09-2026')` payload from the committed `r001d-harness.cjs`;
the test adopts it through the real `adoptPrayerBundle()` owner. No fake model
function is substituted.

```bash
node <<'NODE'
'use strict';
const fs=require('node:fs'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.cwd(),head='9dabdcf338a7307c0256dcdccac48326b357f0d5';
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
for(const p of ['tests/weather-no-timetable-fixture.cjs','tests/r001d-harness.cjs','tests/native-script-contract.js','src/native/index.html','src/native/config.js','real-sky/native-composition.mjs'])assert.equal(sha(fs.readFileSync(p)),sha(cp.execFileSync('git',['show',head+':'+p])),'committed fixture/input '+p);
const {fixture}=require('./tests/weather-no-timetable-fixture.cjs');
(async()=>{
 const {NativeForegroundCapture}=await import('./real-sky/native-composition.mjs');
 async function scenario(order){
  const h=await fixture({fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?{ok:true,json:async()=>payload({time:'2026-09-08T23:46'})}:new Promise(()=>{})});
  const firstRecord=h.run('weather');h.ctx.__oldRecord=firstRecord;
  h.at(951000);assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render()');h.paint();
  assert(h.read().model);assert(h.run('weatherEligibility(__oldRecord).eligible'));
  const before=h.read();await h.refresh({time:'2026-09-09T00:00',cloud_cover_low:80,cloud_cover_mid:75,cloud_cover_high:50});
  assert.notEqual(h.run('weather'),firstRecord);assert(h.read().model);assert(h.read().selected);
  const state=()=>({model:!!h.run('model()'),oldEligible:h.run('weatherEligibility(__oldRecord)'),selected:h.read().selected,cov:h.read().cov,targets:h.read().targets,ready:h.read().ready,raster:h.read().raster.currentFills,receipt:h.read().publication,population:h.read().population,phase:h.read().phase});
  const preCapture=state();if(order==='render-before-capture')h.run('render()');
  const makeCanvas=()=>{let alpha=0;const c={width:325,height:530,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};const ctx={resetTransform(){},clearRect(){alpha=0;},createLinearGradient:()=>({addColorStop(){}}),fillRect(){},setTransform(){},drawImage(source){if(source===h.select('.cloudcanvas'))alpha=h.raster.currentFills?192:0;},getImageData(x,y,w,height){const data=new Uint8ClampedArray(w*height*4);data[3]=alpha;return {data};}};c.getContext=()=>ctx;return c;};
  const save={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle};
  globalThis.document={createElement:makeCanvas,querySelector:q=>q==='.c'?h.select(q):q==='.cloudcanvas'?h.select(q):null};
  globalThis.window={SalahNativeSkyHost:{reconcileClouds:()=>h.run('reconcileCloudPublication()'),lunarSurface:()=>null}};
  globalThis.getComputedStyle=()=>({filter:'none',visibility:'hidden',opacity:'1'});
  let captured;try{captured=new NativeForegroundCapture(makeCanvas()).capture(183);}finally{for(const [k,v]of Object.entries(save))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
  const afterCapture=state();if(order==='capture-before-render')h.run('render()');
  h.paint();const afterRenderPaint=state();
  const pick=w=>({code:w.code,cloud:w.cloud,cloudLow:w.cloudLow,cloudMid:w.cloudMid,cloudHigh:w.cloudHigh,currentValidAt:w.currentValidAt,retrievedAt:w.retrievedAt,target:w.target});
  console.log(JSON.stringify({order,clock:h.clock,recordA:pick(firstRecord),recordB:pick(h.run('weather')),beforeReplacement:{cov:before.cov,ready:before.ready,model:before.model},preCapture,afterCapture,capturedAlpha:captured.cloudRGBA[3],afterRenderPaint,expectedHealthyEase:before.cov.map((v,i)=>v+([.8,.75,.5][i]-v)*.08)},null,2));
 }
 await scenario('capture-before-render');await scenario('render-before-capture');
})().catch(e=>{console.error(e);process.exitCode=1;});
NODE
```

Observed result summary (complete relevant record/identity/timing values are in
F01 above):

| Order | Model available | A still eligible | Coverage at capture | Ready at capture | Captured sentinel alpha | Coverage after render/painter |
|---|---|---|---|---|---:|---|
| Capture → render | true | true | `[0, 0, 0]` | false | 0 | `[0.8, 0.75, 0.5]` |
| Render → capture | true | true | `[0.9104, 0.888, 0.592]` | true | 192 | `[0.9104, 0.888, 0.592]` |

The body A receipt was revision 2 in both controls. Capture-first published
revision 3 withdrawn, then revision 4 eligible; render-first published revision 3
eligible and capture retained it. This is the actual source consumer ordering
regression; the output makes no browser-pixel or observed-provider claim.
