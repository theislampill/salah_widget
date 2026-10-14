# RLGWO remaining-work specification — R000B — revision 1
Priority: P1 | Residual class: evidence, docs, qualification

<!-- COORDINATOR-READINESS:rev1 -->

## Coordinator reconciliation — ready specification, open execution gates

**READY_WITH_EXPLICIT_EXECUTION_GATES.** Author C; independent cold reader D; primary coordinator reconciled this exact revision. [Cold-read report](../reviews/D-C.json), [readiness and source hashes](../SPECIFICATION_READINESS.json), [consolidated execution graph](../CLOSURE_DAG.md). This qualifies the work order as executable. It does not claim that its future tests, platform proofs, repairs, merges or closure have happened. The AWAITING_COLD_REVIEW / READY_PENDING_REVIEW labels retained in the author text below record its pre-review drafting stage; this paragraph supersedes those labels only for specification cold-read readiness. Actual input, owner-decision, implementation, platform, qualification, delivery and closure gates remain binding. The issue remains open.

The consolidated graph separates exact candidate review, required effect authority, actual delivery and final closure. For documentation-only work, accurate DOC/DOCS output can receive its own review and authorized delivery before unrelated native proof completes. Where the authored stage combined both, DELIVERY-CONFIRM preserves all original output interfaces and proof requirements; CLOSE still consumes every mandatory row and delivered document. This refines ordering only, waiving no acceptance obligation. One actual approval/delivery receipt may satisfy several nodes for the same exact head/base/effects; duplicate approvals or merges are not required. Runtime delivery still requires its full affected qualification and separate exact-head release authority.

### Retained author specification

<!-- RLGWO-SPEC:18ff14860ff41c084b1db5f396bb62aa9c22b1be:R000B:rev1:2026-10-08 -->

**Status: AWAITING_COLD_REVIEW.** Residual work is documentation plus unverified hostile temporal metadata, independent mutants and night-transition preservation evidence. No current public precipitation defect has been established by these gaps. A finite raw radar-seconds value can overflow when converted to milliseconds; the existing consumer rejects nonfinite authority. B04 also binds admission: converted frame/index epochs must be finite before their relevant Image/install use. A01 must determine whether a narrow admission repair is needed; no runtime rewrite is presumed. This is an executable specification, not implementation, native qualification, delivery or closure authorization. All new commands/cases below are proposed and unexecuted in this planning stage. The original body and accepted audit remain unchanged.

## A — Identity, authority and observable objective

[Issue #11](https://github.com/theislampill/salah_widget/issues/11) · [complete original audit packet](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/issues/11.json) · [current complete planning packet](../issues/11.json) · [accepted obligation assessment](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/11-assessment.json) · [published parent next-increment comment](https://github.com/theislampill/salah_widget/issues/11#issuecomment-6073038339).

Original issue body SHA-256 `f83c4f3516b63a068dc768b16d64e14cb970cf41ea074e240e73dcffda6d0bcc`. Current discussion contains one unchanged audit comment `6073038339`, SHA-256 `bef692a8ea29d0b590fd07725728876870b4056af556ef9f402accd259d73db3`, updated `2026-10-09T02:29:30Z`. Rename events are identity provenance, not amendments; #36 has no such event. Full body/discussion packet and accepted audit matrix are consumed. Parent comment is the unversioned next increment; this revision specifies its surviving obligations without silently changing their meaning.

Source/main `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; tree `35208181eea714c17f5e77b2644e76434345db60`; reviewed checkout HEAD `4bccdf43363926c3077f60de87e5617ccb9abcb9` has the same tree. Runtime SHA-256 `f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`; generated root index SHA-256 `ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee`. Audit evidence `b879573c298f19189d1f2392108b8b9f3b2cda0b` is immutable at `docs/rlgwo-audit/20261008`. New specification links use only the declared `SPEC_EVIDENCE_COMMIT` placeholder until this package is published. Local paths identify executable work, never sole public proof.

[Owner H5/H8 authority](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267): eligible Open-Meteo CURRENT MODEL ESTIMATE WMO/temp and quantitative rain/snow presentation are allowed without a direct observation adapter; current model condition and quantitative effect decisions remain separate. Raw WMO95 may remain a thunder icon with uncertainty while particles and lightning are off. Forecast-only/stale/wrong-target/malformed input cannot become live current; alpha remains unitless. For R0024 only2405 and the model-withholding part of2415 are superseded. State/source/quality/target/UI/resource obligations survive.

Accepted row IDs: `B01` (satisfied), `B02` (satisfied), `B03` (satisfied), `B05` (satisfied), `B06` (satisfied), `B07` (satisfied), `B08` (satisfied), `B09` (satisfied), `B10` (satisfied), `B11` (satisfied), `B12` (satisfied), `B15` (satisfied). Exact source assertions and original evidence are in the linked accepted matrix and machine metadata; they are not assigned new implementation work.

Residual mandatory row IDs: `B04` (unverified; evidence; P2), `B13` (unverified; evidence; P2), `B14` (unverified; evidence; P1), `B16` (unverified; evidence; P1), `B17` (unmet; docs; P2), `B18` (unverified; qualification; P1). Every one has a concrete F acceptance and G node, including final-proof rows. Closure means these residuals are proven at the exact delivered candidate while accepted rows remain valid, a different reviewer reconciles the joined consumer, evidence is published/read back, and primary authorizes manual closure. A versioned spec alone is never that result.

**Priority assessment.** P1 because source-time/receipt-time and per-use expiry guard a core weather-authority pathway, and their required regression controls remain missing. Missing public prose and overflow diagnostic coverage alone are P2. Accepted runtime fences contain the known historical defect; no demonstrated critical current failure supports P0.

Impact: Potential regression could keep expired weather visually current or label a fresh retrieval as fresh source information; the actual final source is fail-closed on known invalid ages. Conditions: Malformed source metadata, repeated old mosaic, provider outage, tab resume, client clock skew or request-zone supersession. Exposure: All ordinary real-time weather users rely on current authority; hostile overflow is a rare input, not a recorded provider incident. Confidence: High on source/accepted boundary behavior and remaining documentation gap; medium on unexecuted hostile/mutant/native coverage. Containment: accepted conservative source/quantity/owner fences and coupled rollback remain. Original draft proposed P1; no GitHub priority label is present. Retain P1 for the current closure-confidence gap, distinguish lower-urgency P2 documentation/overflow subrows.

## B — Retained witness and reproducible missing discriminator

Historical source installed four-hour-old current as thunder and repeatedly renewed a four-hour-old frame; future cache and five-hour cache plus24h outage also retained thunder. These are reporter-preserved VM RED at the original fd2972/candidate identities, not current browser failures. Current119-pass WEATHER fixture and exact V45 source-equivalent expiry503→native retry proof satisfy the mapped rows. Only explicitly absent acquired NaN/overflow/mutant/night-transition receipts remain.

Retained exact evidence: [serial source-executing test receipts](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/test-receipts.json), [V45 source-equivalence and limitations](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/historical-source-equivalence.json), [original TODO/failure/reuse accounting](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/11-assessment.json), [completed public delivery](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/release.json), [16 public browser receipts](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/public-browser-summary.json). Prior source fixes include the CP9 prerequisite integration before PR42; do not attribute all repairs to PR42. Authored weather source and generated root differ by the builder’s narrow [acceptedElevation handoff](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/tools/build_native.py#L64-L67).

The current default checkout `C:/workspace/ai/salah_widget` is historical fd2972 with unrelated scratch files; do not implement there. Re-anchor the reviewed source through `C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget`, then acquire an authorized isolated execution checkout. Planning inspection observed that reviewed checkout clean, with the HEAD/tree above. Re-acquire state before any future source/test/build mutation. Tools already used for the accepted audit: `C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe` and `C:/workspace/ai/cp9-integration-20261005/venv/Scripts/python.exe`; verify their actual capabilities in execution rather than install a new dependency.

Read-only re-anchor syntax inspected; no product tests were run in this planning stage:

```powershell
git --no-optional-locks rev-parse --show-toplevel
git --no-optional-locks rev-parse HEAD
git --no-optional-locks status --short
git --no-optional-locks rev-parse '18ff14860ff41c084b1db5f396bb62aa9c22b1be^{tree}'
git --no-optional-locks diff -- src/native/index.html tools/build_native.py real-sky/native-host-hooks.js README.md DESIGN.md HANDOFF.md
```

VM recipe: `NOW=Date.parse("2026-09-07T21:00:00Z")`, site24.47/39.61, Celsius, captured UTC, generation0, SIM.wx=null, ADVANCING=false; use existing source-executing r000c fixture and actual shared timezone/request-owner declarations. Healthy CURRENT fields: time21:00, interval900, WMO95, temp20, apparent19, humidity90, dew18, wind2m/s/direction180/gust4, cloud95, precipitation2mm, elevation100; aligned hourly21:00/22:00 with temp20/19/code95/3/precip2/0. A test may override only its declared discriminator. Treat legal JSON parser overflow, malformed JSON and VM-only NaN as three different input classes.

Native recipe: Windows x64; installed Chromium and Firefox via tools/cp9/browser_runtime.py; record actual executable/version. Fresh profile per case, private Map storage, 390×600 viewport, DPR 1, 325×530 card, Asia/Riyadh browser zone, fixed-site lat24.47/lon39.61, method4/school0/Celsius/seed1; source/runtime/fixture hashes bound. No local=1 unless config is seeded before parse. Fixed-clock acquisition cases use `2026-09-07T09:30:00Z` (Riyadh12:30) and no timeScale/simWx. Night temporal/motion cases explicitly use a real1x moving wall clock and the declared source quarter-hour; no frozen-clock motion inference. Every synthetic present fixture is scoped/owned and marked preview; it is not a provider response. Controlled prayer dates/Hijri are test values, not calendar research or public prayer proof.

Cheapest retained native preparation: [versioned C driver](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/run_weather_browser_v2.py) and [versioned wrapper/changes](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/browser-fixture-preparation-v2.json). Existing CLI accepts only12/14/30; #12 cases are prepared but unexecuted. #13/#36/newnight recipes require the named thin adaptation, not invented existing CLI support. Preserve the first #14 CSP/local-mode harness error and the second old quantitative-oracle FAIL; [offline H5/H8 effect reconciliation](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/browser14-v2-semantic-reconciliation.json) records why raw95condition is allowed while the actual zero-amount effect is off.

## C — Authored owners, generated consumers and exact interfaces

| Owner / file | Responsibility |
|---|---|
| `src/native/index.html:1005–1044,1230–1386,1387–1459,1654–1668,2953–2962,3068–3078,3131–3162` | request/attempt ownership, temporal admission, cache, per-use selection, acquisition, header, renderer and diagnostics |
| `real-sky/native-host-hooks.js:12–34` | native sky captures selected weather every use; do not substitute stale raw weather |
| `tools/build_native.py:64–67` | only builder rebuilds generated root and narrow acceptedElevation handoff |
| `tests/r000c-weather.test.cjs; tests/r000d-weather.test.cjs; tests/r0024-cloud-expiry.test.cjs; tests/hotfix-prayer-weather.test.cjs` | existing accepted controls remain literal; new remaining fixtures extend source execution |

The generated deployed consumer is root `index.html` with config/native host/Moon worker assets, not a separate corrected fixture implementation. `tools/build_native.py` owns generation. The native browser wrapper must load the unchanged product bodies and native HTTP assets, then add labelled dependency/observer hooks; record source/bridge/CSP hashes and exact hook modifications. Preserve first-paint/scene/currentness/worker identities. No arbitrary generic execution bridge or unsafe-eval is permitted.

| Required input interface | Status / precise contract | Evidence |
|---|---|---|
| `captured-weather-operation/v1` | SATISFIED: beginRequest/attemptEligible/finishRequest capture generation, target, requestzone, units/cachekey; obsolete A never commits or clears activeB | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1005-L1044) |
| `admitted-model-current-and-track/v1` | SATISFIED: finite known-field normalized current with captured units/zone/target and separate sourcevalid/interval/receipt; valid track independent; nulls preserved | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1213-L1386) |
| `weather-per-use-authority/v1` | SATISFIED: selectedWeather current source andreceipt eachinclusive0..900000ms; validpositiveinterval/targetgeneration; forecast not livecurrent | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1278-L1292) |
| `captured-calendar-zone-converter/v1` | SATISFIED: explicit request-zone/correct calendar/gap-fold rejection; NewYork03:30 on2026-03-08 means07:30Z despite globalRiyadh | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1230-L1242) |
| `bounded-weather-body-image-owner/v1` | SATISFIED: actualweather/manifestfetch+body each10s andImage10s; absolute monotonic guard/idempotentownedcleanup; retry60sweather/10mradar | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1323-L1459) |
| `radar-unitless-and-zero-axis/v1` | SATISFIED: actualImage samples unitless;radarPrecipNow0, noobservational orparticle grant; finitecoordinates including0axes dispatch correctly | [source/receipt](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/C/14-assessment.json) |
| `captured-location-evidence/v1` | SATISFIED: fixedsite distinctdevicefix/coarseIP; originalacquiredAt/accuracy/intent/targetgeneration preserved; noinventedradius orsave-renewal | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1293-L1312) |
| `weather-evidence-decision/v1` | SATISFIED: current/spatial/horizon/forecast independent; synthetic-present-v1 only in markedpreview; liveadapters closed; cacheduntil earliesteligibility boundary | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/src/native/index.html#L1523-L1651) |
| `owner-H5-H8-model-presentation/v1` | SATISFIED: eligibleCURRENT modelWMO/temp andquantity-supportedrain/snow mayrender asMODEL ESTIMATE; rawcondition distinctfromeffectgate; noobservedlightning/forecast-as-current/radaralpha authority | [source/receipt](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/DESIGN.md#L244-L267) |
| `delivered-baseline18ff/v1` | SATISFIED: actualmain SOURCE18ff14860ff41c084b1db5f396bb62aa9c22b1be/tree35208181eea714c17f5e77b2644e76434345db60/runtimef443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260;16publicChrome/Firefox root/V1 cold/warm direct/iframe readbacks; relevantweather counterexamples notcovered bygenericrollout | [source/receipt](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/release.json) |

An administratively open issue is not a dependency. Consume these verified interface artifacts; if their exact source/input contract drifts, gate only the affected node. New outputs below are reviewable node receipts with candidate/source/fixture/input/environment hashes, raw states and independent disposition; all are planned, not claimed to exist.

## D — Ordered bounded work and decision rules

1. Re-anchor the authorized isolated candidate and compare the exact weather/request/temporal/native-host interfaces with SOURCE. Obtain a per-interface source-equivalence record for accepted rows; use the published B15 V45 receipt and existing source comparison, not another37-issue audit.
2. Add `tests/r000b-remaining.test.cjs` using the existing r000c fixture extraction and controlled actual acquisition. Implement A01/A02 in fresh fixtures, including legal JSON1e309/MAX_VALUE and separately labelled VM-onlyNaN. The default B04 oracle is binding: validate raw numeric seconds, convert once and require finite valid frame/index epochs before relevant Image/admission/install use. Preserve existing authority rejection separately. If acquisition dispatches an Image or installs invalid converted metadata, record the exact diagnostic/admission RED; gate the affected node for only a finite-derived-frame/index epoch guard in authored fetchRadar, one hostile negative and fresh healthy control, and its source/build/delivery authorization. Do not require a runtime rewrite if the bound consumer already passes, and do not permit an authority-only interpretation without a separately explicit owner amendment. Do not relax future allowance or age limits.
3. Add `tools/qa/run_r000b_mutants.py`, which makes four exact one-anchor source variants in isolated evidence-owned copies, points SALAH_WEATHER_SOURCE at each, uses bounded test subprocesses, and retains A03 paired GREEN/RED/raw hashes. No mutation in W/main. A syntax/extraction/timeout-harness error is FAILED_HARNESS, never a detected semantic regression.
4. Add a thin `tools/qa/run_r000b_native.py` and versioned wrapper based on published C weather fixture. For A04 use actual1x advancing wall time rather than frozen Date or a manual weather-install helper. Native weather retry follows existing lastWxTry60s and render opportunity. Supply fresh controlled body on each eligible retry from the current fixture clock; retain original prayer fields and explicit fixture provenance. Capture the affected half-Moon/night transition and allowed-motion clip; reuse unchanged day B15 only for its recorded input/environment.
5. Through one docs integrator add the A05 temporal facts to README Features/weather and Auto-retry; amend existing DESIGN Weather truthfulness and URL/debug diagnostic description, and correct the running nowcast approximation in DESIGN/HANDOFF. Do not introduce a missing QA.md/DIAGNOSTICS.md or rewrite historical source descriptions.
6. If A01/A02 finds an actual violation, stop evidence-only classification, record red input/state and request only the concrete source/generator repair/delivery scope already required by the work order. Qualify changed interfaces before joining A06; otherwise runtime remains SOURCE and only docs/fixtures change.

Proposed executable entries (not yet created or executed; `<authorized-candidate>` and `<isolated-evidence/...>` must be bound by the future executor, then replace these metasyntactic values):

```text
node.exe --test --test-concurrency=1 tests/r000b-remaining.test.cjs
python.exe tools/qa/run_r000b_mutants.py --root <authorized-candidate> --out <isolated-evidence/R000B/mutants>
python.exe tools/qa/run_r000b_native.py --root <authorized-candidate> --out <isolated-evidence/R000B/native> --browser chromium --matrix night-expiry-recovery --clock real1x
```

Existing source tests may be run later only if source/interface changes or a listed residual needs the discriminator. Syntax/source inspection and prior exact receipts establish the existing test entry names, not new execution. In the isolated candidate bind `SALAH_WEATHER_SOURCE` to its generated index, `SALAH_CONFIG_SOURCE` to generated config and `SALAH_HOTFIX_SOURCE` to authored native source; do not accidentally execute the historical default checkout. Run serial `node.exe --test --test-concurrency=1 tests/r000c-weather.test.cjs`, `tests/r000d-weather.test.cjs`, `tests/r0024-weather.test.cjs`, `tests/r0024-response-zone.test.cjs`, `tests/r0024-cloud-expiry.test.cjs`, `tests/hotfix-prayer-weather.test.cjs` only as affected. Preserve4 inherited TODOs as TODO. Mutant copies carry actual extracted source, not duplicate corrected business logic.

## E — Scope, preservation and compensation

Preserve existing finite/WMO/unit/null/time/target/generation admission, current-hourly-SIM separation, per-use expiry, captured config/cache identity, quantitative model permissions and independent lightning. H5/H8 explicitly allows labelled CURRENT model rain/snow; unknown/invalid amount cannot authorize particles and neither model thunder nor RainViewer alpha grants strikes. No live source becomes qualified by formatter output or `trusted:true`.

Preserve CP9 scientific core and accepted V5 stellar/source registries, physical Sun/Moon radiance, calendar Moon opacity/material/Earthshine, cloud continuity and full-/reduced-motion policy, prayer clock/currentness/rows, settings persistence/keyboard focus, terrain/composition/entry contracts,325×530 card and owner-approved330×534 productioniframe. FrozenV1 remains unchanged. Prior N001/N002PARTIAL andN003BLOCKED and historical lunar assertion failures retain their exact status; close neither by implication. Reuse only the unaffected identified interface/input evidence, never a blanket all-art PASS.

Single source integrator owns any shared authored native weather/header/settings hunk, one documentation integrator owns README/DESIGN/HANDOFF, and one shared heavy native/terrain/performance queue runs at a time. Read-only source inspection and separate drafts can proceed in parallel. Authoritative owners are src/native/index.html/config/builder and real-sky/native-*; generated index/config/offline/bundles/CSS/data/worker are rebuilt only by authorized builders, never patched first. PR38, immutable vendor/scientific oracle, installer/presets/storage schema/location provider changes are outside this increment.

Use isolated checkout/evidence directories, disposable origin/profile and private fixture storage. Do not touch user browser profiles, live preferences/caches or clipboard; no remote telemetry. HTTP fixtures disclose synthetic dates/Hijri/provider inputs and never present them as live observations. Roll back an actual source repair and its generated outputs together if a healthy control regresses; keep failed receipts/cache bytes and conservative unavailability. A failed information formatter can return the prior approved condition/model description while leaving nearby/arrival unavailable; it may not invent observation or restore alpha-mm. Publication/spec authoring does not authorize commit/push/deploy/state change; future executor/merge/publication leases remain separate. Containment does not satisfy a still-unverified closure row.

## F — Complete residual acceptance matrix

| Mandatory residual | Current gap / priority | Concrete acceptance | Node / independent gate |
|---|---|---|---|
| `B04` — Radar frame seconds must be finite and valid before epoch multiplication; absent frame time cannot borrow index time. | unverified, P2; Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. | `R000B-A01` | `R000B-EVIDENCE`; each fixture has an independent gate below |
| `B13` — Four-hour old model/radar/repeated-frame, missing/NaN time, future+1ms/+24h cache, invalid interval and healthy wet restoration require final-tree discriminators. | unverified, P2; Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. | `R000B-A02` | `R000B-EVIDENCE`; each fixture has an independent gate below |
| `B14` — Independent source→receipt, consumer-expiry bypass and global-zone mutants must make corresponding witnesses fail. | unverified, P1; Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. | `R000B-A03` | `R000B-EVIDENCE`; each fixture has an independent gate below |
| `B16` — Preserve 325×530 card/header/footer, moon opacity and cloud continuity in the affected transitions. | unverified, P1; Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. | `R000B-A04` | `R000B-NATIVE`; each fixture has an independent gate below |
| `B17` — Update DESIGN, README and diagnostics to distinguish model-valid time, interval, retrieval, mosaic generation and unavailable; no ground-observation/universal-coverage/offline guarantee. | unmet, P2; Bounded documented/diagnostic or resource coverage gap; accepted authority logic contains immediate risk. | `R000B-A05` | `R000B-DOCS`; each fixture has an independent gate below |
| `B18` — Joined temporal/cache/consumer review and evidence comment precede manual closure; public repair requires matching served-source/consumer readback. | unverified, P1; Material current weather authority, native consumer or final closure-confidence gap; existing logic contains known historical defects but cannot replace required proof. | `R000B-A06` | `R000B-QUALIFY`, `CLOSE-R000B`; each fixture has an independent gate below |

All fixture rows are future required acceptance. Exact constants0.05mm precipitation and0.8mm thunder gate, source/receipt TTLs900000/1200000ms, nofuture,10s stage waits,250m/5m syntheticdevice policy and exclusive syntheticvalidUntil come from the existing accepted source/contracts. Do not import a raw-condition downgrade oracle from an amended old test. No new rainfall/calibrated-confidence/predictive threshold is invented. Native deadlines permit recorded scheduling lateness; VM controls prove exact9999/10000 boundaries. Art/motion require crops/clip and independent inspection, not only numbers.

### R000B-A01

**Fixture:** WALL=2026-09-07T21:00:00Z, UTC, generation0, SIM.wx=null/ADVANCING=false. HTTP200 manifest generated=WALL/1000, latest path=/v2/radar/test; independently set past[0].time absent, null, "1788814800", -1, 1e309 JSON token (JSON.parse produces Infinity), and Number.MAX_VALUE as legal JSON. Separately hold frame time healthy and apply the same malformed/overflow set to generated/index seconds; retain a fresh finite frame/index control. In a separately labelled VM json() double also pass NaN and Infinity (not JSON wire values).

**Actual consumer:** Actual fetchRadar → wxFetchJson → wxRadarSample → weatherRadar → radarEvidence/qaState; actual gateWeatherCode/atmosphere

**Assertion / threshold:** Binding B04 oracle: validate raw numeric frame and index seconds, convert each once, and require a finite valid derived epoch before Image dispatch or admission/install. Absent/null/string/negative/nonfinite raw frame time or finite-seconds multiplication overflow must dispatch no Image and install no invalid frame/index epoch; an invalid index epoch must not be installed or used as a frame-time substitute. For every rejection radarEvidence.available=false and radarPrecipNow()=0; pre-existing authority rejection alone cannot pass the admission row. Fresh finite frame/index control samples the actual fixture Image/canvas and preserves separate frame/index/receipt clocks. Check generated/index multiplication independently of a healthy frame; do not call Infinity a finite valid epoch.

**Environment:** Windows x64; Node v22.16.0; exact final generated index.html selected with SALAH_WEATHER_SOURCE; source-owning native file also selected in the hotfix suite. Contained fetch/Image/storage/DOM/wall and monotonic clocks; never native-browser or provider evidence.

**Expected:** Hostile derived epochs rejected before their relevant Image/admission/install use, finite fresh diagnostic control available, zero radar mm and no strikes. The current consumer already withholds authority for nonfinite derived epochs; preserve that accepted fact. If actual acquisition nevertheless dispatches or stores invalid derived metadata, retain the exact RED diagnostic/admission receipt and gate a narrow authored finite-derived-frame/index epoch repair plus healthy proof and future delivery authorization. This is not a demonstrated public precipitation effect defect. No authority-only closure interpretation is permitted without a separately explicit owner amendment.

**Planned evidence:** `evidence/R000B/R000B-A01/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Cold reviewer checks exact source extraction, pre/post mutation hashes, unchanged oracle, intended assertion failure and surviving healthy control; syntax/harness failure is not mutation detection.

### R000B-A02

**Fixture:** Same fixed UTC acquisition as A01; current.time="invalid", "NaN", absent, null and calendar-invalid string, interval=900, WMO95/temp20/precip2/cloud95; valid aligned hourly may be retained independently. Separately label VM json() current.time=NaN. Healthy control time="2026-09-07T21:00". Actual HTTP literal NaN is malformed JSON and exercises body rejection, not a valid NaN timestamp.

**Actual consumer:** fetchWeather → admitWeatherRecord/wxEpoch → selectedWeather → atmosphere/paintWeatherHeader/native-host-hooks

**Assertion / threshold:** Derived currentValidAt must remain unavailable/nonfinite and currentEligible=false on malformed time; lastWxAt not renewed, no live current chip/temp/particles; valid hourly cannot substitute for live current. Stored raw diagnostic record may survive with null epoch. Healthy control installs/cache temp20 and eligible quantity-supported model rain, direct observation false, strikes off.

**Environment:** Windows x64; Node v22.16.0; exact final generated index.html selected with SALAH_WEATHER_SOURCE; source-owning native file also selected in the hotfix suite. Contained fetch/Image/storage/DOM/wall and monotonic clocks; never native-browser or provider evidence.

**Expected:** Explicit acquired malformed/NaN-derived metadata discriminator with prior accepted old/future/boundary rows reused, not relabelled as new execution.

**Planned evidence:** `evidence/R000B/R000B-A02/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Cold reviewer checks exact source extraction, pre/post mutation hashes, unchanged oracle, intended assertion failure and surviving healthy control; syntax/harness failure is not mutation detection.

### R000B-A03

**Fixture:** Four isolated actual-source copies: (M1) substitute currentValidAt with retrievedAt in current eligibility; (M2) substitute radar frameGeneratedAt with retrievedAt in radar eligibility; (M3) bypass real-time per-use source expiry while retaining admission; (M4) change captured request-zone use to mutable global tz. Use existing four-hour current/repeated old-frame, acquired-fresh→900001ms→offline consumer and New York2026-03-08T03:30→07:30Z/globalRiyadh witnesses.

**Actual consumer:** Actual acquisition/cache/selection/atmosphere/header/native-host capture and explicit-zone converter; mutations made only in disposable source copies

**Assertion / threshold:** M1 old-current must wrongly become eligible and its no-current witness RED; M2 repeated old-frame must wrongly become diagnostic-available and its frame-age witness RED; M3 expired header/temp/cloud/effects withdrawal witness RED; M4 captured-zone witness RED. One anchor per mutation, one mutation per run; healthy fresh/timezone controls still pass. Full final-source GREEN paired with each expected assertion RED.

**Environment:** Windows x64; Node v22.16.0; exact final generated index.html selected with SALAH_WEATHER_SOURCE; source-owning native file also selected in the hotfix suite. Contained fetch/Image/storage/DOM/wall and monotonic clocks; never native-browser or provider evidence.

**Expected:** Four detected independent regressions, not four command errors; retain unmodified fixture TODOs and separately map replacement controls.

**Planned evidence:** `evidence/R000B/R000B-A03/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Cold reviewer checks exact source extraction, pre/post mutation hashes, unchanged oracle, intended assertion failure and surviving healthy control; syntax/harness failure is not mutation detection.

### R000B-A04

**Fixture:** Native night at wall2026-09-07T18:44:50Z (Asia/Riyadh21:44:50); controlled CURRENT source time21:30:00/interval900/WMO63/temp24/precip2/cloud70, receipt initially fresh. Wall advances at1x; source eligibility inclusive until18:45:00Z, unavailable after +1ms; controlled refresh503, then healthy next eligible native weather retry with current quarter-hour time. Keep no simWx/simTime/timeScale, force calendar phase only simMoon=.5/simMoonAlt=20/simMoonH=42 if needed and disclose it. Repeat no-preference, reduced-motion default and motion=full override; capture ≥15–60s allowed-motion clip.

**Actual consumer:** Actual browser HTTP acquisition → native render/header/precip/cloud painter/Moon overlay/native host; no installModel recovery helper

**Assertion / threshold:** 325×530 card and readable header/footer throughout; initial/recovered model particles from cloud systems; expired header em dash/temp blank/effects off, prayer rows independent. Opaque half-Moon/stars never visible through disc; cloud population retains identity and continuous drift/morph, no reseed/slideshow. Screenshot/clip reviewer decides; qaState.clouds.hash forbidden as motion evidence. OS reduced default reduces motion and motion=full restores it.

**Environment:** Windows x64; installed Chromium and Firefox via tools/cp9/browser_runtime.py; record actual executable/version. Fresh profile per case, private Map storage, 390×600 viewport, DPR 1, 325×530 card, Asia/Riyadh browser zone, fixed-site lat24.47/lon39.61, method4/school0/Celsius/seed1; source/runtime/fixture hashes bound. No local=1 unless config is seeded before parse.

**Expected:** B16 remaining night/opacity/continuity proof; reuse B15 V45 day expiry503→real retry evidence only for unchanged exact weather regions. This is controlled native1x elapsed proof, not live provider or all-phase lunar qualification.

**Planned evidence:** `evidence/R000B/R000B-A04/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Independent native reviewer reads network/owner/admitted/cache/DOM receipts and actually inspects card/header/footer/Moon/cloud crops or clip; numeric PASS cannot override pixels. Primary reconciles exact candidate.

### R000B-A05

**Fixture:** Review README Features/Auto-retry/Credits; DESIGN Weather truthfulness/API & data/URL-debug/Known approximations; HANDOFF running weather limitation. Compare to actual qaState.wxTruth cache/age/request diagnostics; no QA.md or DIAGNOSTICS.md exists, so use the existing DESIGN diagnostic section rather than inventing a second manual.

**Actual consumer:** Public prose and actual selectedWeather/radarEvidence/qaState diagnostic contract

**Assertion / threshold:** State separate model-valid/currentTime/currentZone/preceding interval/retrievedAt, radar frameGeneratedAt/indexGeneratedAt/retrievedAt; processing duration not epoch; 15m/20m inclusive both source+receipt, future allowance0, cache retention6h not authority; expired unavailable dash/blank/effects off, prayer cache distinct, clock-skew limitation, no local observation/coverage/offline guarantee. Correct contradictory current nowcast wording only where it presents current behavior; preserve historical commit provenance.

**Environment:** Static exact candidate prose plus retained source/consumer receipts; no browser required for documentation review

**Expected:** All required facts explicit in coherent public docs; missing diagnostic fields, if discovered, become a narrow source gap with a red fixture before edit.

**Planned evidence:** `evidence/R000B/R000B-A05/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Independent documentation reviewer compares every stated fact with pinned source and actual consumer receipts, then rejects observation/arrival/offline/cancellation overclaims.

### R000B-A06

**Fixture:** Join all18 original B rows, A01–A05 receipts, unchanged V45 source-equivalence and delivered baseline; candidate commit/tree/runtime/root-index/config/source/fixture hashes; current body/discussion marker check before future effects.

**Actual consumer:** Independent joined temporal/cache/consumer review → future merged/deployed served consumer → exact evidence comment → separately authorized manual closure

**Assertion / threshold:** Every residual row mapped, no metadata-only closure, no unexecuted mutant/pixel promotion. If runtime unchanged, prove exact served18ff hash still matches; if narrow guard changed, build authored owner, obtain merge/delivery authorization, verify new public bytes and relevant unavailable/fresh consumer, then publish proof/read it back. Existing audit comment already posted and issue remains open; new spec publication alone is not closure.

**Environment:** Immutable candidate/release/public-source readback and issue readback

**Expected:** CLOSE-R000B certificate only after actual required delivery and primary reconciliation.

**Planned evidence:** `evidence/R000B/R000B-A06/receipt.json`; alongside it retain exact input/source/runtime/bridge/browser identities, raw events/assertions and relevant card/header/footer/Moon/cloud crop or clip. Do not label planned paths as executed evidence.

**Independent gate:** Different reviewer checks complete accepted-plus-residual matrix, delivery identity and immutable evidence hashes; primary approves exact comment before any separately authorized publication/closure.

QUALIFY produces only `evidence/R000B/reviewed-candidate-certificate.json`: independently reconciled source/evidence/native/resource/docs candidate and preserved final-proof rows, with exact-head authority, required delivery and closure marked PENDING. It does not assert the final F receipt complete. The completed `evidence/R000B/closure-certificate.json` adds actual `exact-head-authority.json` and `required-delivery-receipt.json`, merged/public identity, approved evidence/issue readbacks and complete original dispositions. Unmatched/unknown completion stays unverified; local candidate review cannot be delivery or closure.

## G — Dependencies, outputs, execution order and cost

The machine graph is [metadata](../metadata/R000B.json). It consumes accepted interface identities, not issue states; per-issue IDs are local so primary can coalesce shared documentation/source queue work without inventing global blockers.

| Node | Rows / output | Hard predecessor | Active effort (hours) | Exclusive machine (minutes) | Resource / basis |
|---|---|---|---:|---:|---|
| `R000B-EVIDENCE` | R000B:B04, R000B:B13, R000B:B14; `R000B-evidence-output/v1` → `evidence/R000B/evidence/receipt.json` | verified input interfaces only | 2–4 | 5–15 | light-node-fixture; confidence medium |
| `R000B-DOCS` | R000B:B17; `R000B-docs-output/v1` → `evidence/R000B/docs/source-facts-and-diff.md` | verified input interfaces only | 1–2 | 0–0 | documentation-writer; confidence medium |
| `R000B-NATIVE` | R000B:B16; `R000B-native-output/v1` → `evidence/R000B/native/receipt.json` | verified input interfaces only | 2–4 | 15–30 | exclusive-heavy-browser; confidence medium-low |
| `R000B-QUALIFY` | R000B:B18; `R000B-qualify-output/v1` → `evidence/R000B/reviewed-candidate-certificate.json` | R000B-EVIDENCE, R000B-DOCS, R000B-NATIVE | 1.5–3 | 3–8 | independent-review; confidence medium |
| `CLOSE-R000B` | R000B:B18; `R000B-close-output/v1` → `evidence/R000B/public-delivery-and-issue-readback.json` | R000B-QUALIFY | 0.5–1 | 2–5 | serialized-external-writer; confidence medium |

Issue estimate: active effort 7.0–14 hours; summed exclusive machine 25–58 minutes. These are bounded planning estimates, not measurements or a promise of elapsed finish. Independent source/fixture/docs draft effort can overlap; heavy native/performance work and external writers serialize. Counts exclude owner-review/deploy queue waiting and any newly demonstrated production defect. If#13radar retries must be watched for real10minutes rather than disclosed wall-offset, add30–60 exclusive machine minutes for the selected engines/stages; do not silently spend it. Primary may coalesce shared warmup/docs/observer setup instead of charging it perissue twice.

Entry: future execution lease, cold review/primary reconciliation, exact admitted input interfaces and fresh clean isolated candidate. Evidence/docs/implementation outputs are candidate artifacts. QUALIFY ends with pre-delivery reviewed-candidate certificate and pending later authority/delivery/closure gates. Delivery mode is `docs-merge`: For #11/#12/#13 only a preserved actual consumer counterexample plus separately authorized bounded source/build fix changes docs-merge to runtime-merge; no source rewrite is presumed. Exact-head authority and delivery receipt paths are named in closure metadata; primary expands independent-review → exact-head authority → delivery → closure in the unified DAG. Required new documentation is always merged/read back; unchanged18ff product delivery may be reused by current hash only. Final manual closure requires actual authorized delivery and immutable evidence/issue readback.

Exact shared-file risk: src/native/index.html weather/header/diagnostic/settings regions collide with generation/temporal/location/lunar/startup writers; one authored source integrator. README.md/DESIGN.md/HANDOFF.md overlap weather docs for#11/#12/#13/#36 and other residual specs; shared docs integrator coalesces exact facts before edit. tools/build_native.py/generatedroot/fixture script anchors shared; only builder owner regenerates after approved authored change. All heavy native/browser/performance jobs serialize; read-only/draft lanes may parallelize.

## H — Cold-executor and independent reviewer checklist

- [ ] Original issue/body/comment hashes, H5/H8 scope, source/main/tree/runtime and prior accepted matrix are read from immutable linked packets; no transcript needed. Current external target/state/drift is reacquired before any future effect.
- [ ] Every residual mandatory row appears in F and metadata; final-proof row is a real qualification/closure dependency, not deleted as paperwork. Accepted/superseded rows remain explicitly preserved.
- [ ] New CLI/file interfaces are created and reviewed before running; no pretend existing tool, browser/native/JSON-wire/field observation or visual PASS. Controlled clocks/data/environment and exact dependency substitutions are disclosed.
- [ ] Positive, boundary, hostile, recovery and required isolated mutations reach actual source/consumer; original FAIL/TODO remains and only narrow owner-approved supersession affects the expected result. No generic asset/body/Image substitution.
- [ ] Shared source/docs writer and exclusive heavy queue ownership are assigned; native/public/generated/source states separated. Privacy/profile/storage/clipboard and fixedcard/V1/sky/star/Sun/Moon/cloud/prayer/settings/currentness boundaries preserved.
- [ ] Pixels, accessible description, actual particles/strikes, motion and resource claims are independently inspected in their stated scope; unsupported metrics and missing completion remain unknown.
- [ ] Exact candidate certificate and delivery/evidence/issue readbacks are accepted by primary before separately authorized publication or completed closure. All material counterexamples retain exact input/state/command/artifact and stop only affected outputs.
- [ ] Readiness remains AWAITING_COLD_REVIEW until a different reviewer and primary reconcile this revision. No missing platform/owner research task is manufactured; the new bounded weather information route is authorized planning scope, while actual source/build/merge/publication requires its future lease.

Public custody: [current complete discussion](../issues/11.json) · [full remaining specification](R000B.md) · [machine obligations/DAG](../metadata/R000B.json) · [author review](../workers/C/AUTHOR_REVIEW.md). This comment adds revision1; it does not overwrite the original contract, prior audit proof or recorded state.
