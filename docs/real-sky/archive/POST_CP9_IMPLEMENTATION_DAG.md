# Post-CP9 implementation DAG

Checkpoint 9 is the final checkpoint. This graph is implementation work after the delivered CP9 candidate, not Checkpoint 9.5 or 10. The authoritative tree is `widget/`, identified by `CP9_RUNTIME_IDENTITY.json`; use the complete package, not the donor or the patch alone.

## Frontier and dependency order

```text
CP9-N001 — loaded presentation/interaction cost ─┐
                                               ├─> CP9-N003 — actual-platform final acceptance
CP9-N002 — accelerated-time sky availability ────┘
```

N001 and N002 are independently ready because they address different event-loop/solver bottlenecks. They share a host/message boundary: coordinate interface changes rather than making conflicting overlays. N003 runner preparation may begin early, but its final acceptance is invalidated by any later N001/N002 runtime change. All three nodes are mandatory for the expanded acceptance matrix; none is presently closed.

## Evidence and execution rules

Read `POST_CP9_FINDINGS.json` and `POST_CP9_ACCEPTANCE_MATRIX.json` together. Each item below is backed by actual CP9 code/measurements. The graphs contain no work for already-fixed elevation, worker-loss, mask or metadata findings. Existing scientific approximations remain explicit boundaries rather than fabricated tickets. First reproduce the packaged baseline; preserve failures and judge every gate independently of a command merely completing.

The full local qualifier returns **0** only when all mandatory gates pass, **2** when executable checks pass but mandatory qualification is incomplete, and **1** on an execution/invariant failure. Currently the platform gate is deliberately unqualified: N003 must add the actual collector/evidence, not change a label.

## CP9-N001 — Main-thread native presentation, shared display encoding, canvas readback and native dialog/layout scheduling—not celestial source brightness or the worker-loss policy.

**Priority:** mandatory. **State:** OPEN. **Finding:** CP9-F101. **Dependencies:** none.

### Exact problem
The five-trial loaded CPU×4 responsiveness target remains unmet after the verified mask hoist and exact-input presentation cache. Candidate full-motion maxima are 621.8, 458.1, 316.5, 325.3 and 339.2 ms; reduced-motion maxima include 459.0 ms. The untouched native control also exceeds 250 ms. Final-source V8 samples identify repeated shared display encoding and native foreground/readback, not the now-hoisted Moon mask, as substantial remaining integration cost. This is a measured stress deficiency, not a universal device-speed claim.

### Supporting CP9 evidence
- `evidence/cp9/performance-final/results.json` (`/cases`): Five sequential trials per condition; inspect candidate cases separately from the native baseline. This pre-seal run precedes only the diagnostic-metadata refresh fix; final archive qualification reruns the exact final runtime.
- `evidence/cp9/profile-final/results.json` (`/cases/1/profile`): Exact final runtime sampled under CPU×4; CP9 top-self linearToSrgb 1437.258 ms, encodeFrame 1307.661 ms, nativeForeground 727.751 ms and getImageData 601.960 ms across a 12224.768 ms sample interval. Inclusive times overlap; (program) is not assigned to an invented JS owner.
- `evidence/cp9/mask-benchmark-final/results.json`: Mask hoist already closed: exact samples and roughly 9× median improvement. Do not redo or claim this as new work.
- `evidence/cp9/presentation-final/results.json`: Identical-input skip and changes to PBR pixels, cloud pixels, cutout geometry, physical frame and metadata are all discriminating controls.

### Affected owners
`widget/real-sky/native-host.mjs`, `widget/real-sky/native-composition.mjs`, `widget/real-sky/native-engine.mjs`, `widget/real-sky/core/src/renderer.mjs`, `widget/index.html`, `tools/build_native.py`, `tools/cp9_profile.py`, `tools/cp9_performance.py`, `tools/cp9_presentation_check.py`

### Authorised implementation scope
- Start from the final profile and its source hash, not a fresh general investigation. At native-host compose/accept, remove repeated encode work and readbacks only when the full physical-frame, support, mask, PBR and cloud identity is unchanged; the existing guard already proves that contract.
- Move or cooperatively schedule pure encode/composition work off the prayer event loop through a new authored native module/worker message if necessary. Carry the same job epoch, source IDs and native presentation identity through every asynchronous result; recheck these before publication. Preserve exact Float64/encoded comparisons and diagnostic refresh on cache hits.
- If native dialog/layout work still independently breaches the same budget, make a bounded generated-index change in the native owner through tools/build_native.py; add targeted native assertions and identify the exact protected change. Do not attribute unknown browser/program samples to a convenient function.
- Use the retained renderer as immutable numerical oracle. A new faster implementation belongs in widget/real-sky/ and its deterministic builder, not in an overwritten core copy. Record added buffer lifetime and release on invalidation/disposal.

### Invariants
- Accepted native simNow(), observer, configuration generation and elevation custody remain the only astronomical input authority; independent invalidation epoch, A→B→A, hidden, seek, retry and disposal fences survive.
- No visible or newly published frame may differ from accepted native UTC by more than 30,000 ms. Invalid, hidden, superseded or failed input never leaves old light or stale diagnostics visible.
- Prayer admission, six prayer rows, countdown, day rollover, Maghrib calendar selection, settings and weather eligibility remain independent of optional astronomy.
- Preserve the actual native PBR backing canvas, phase, Earthshine and enlarged calendar mask; physical lunar sky illumination/occultation remain separate.
- Retain the one declared cloud/light/exposure equation, strict/missing/estimated source masks, admitted catalogue and no synthetic stellar fallback.
- All 162 native baseline and 950 scientific-reference files remain untouched; generated widget/core files are not a new canonical source. Any new optimised runtime must be authored as a separately tested adapter and included deterministically by tools/build_native.py.

### Prohibited shortcuts
- Do not fix responsiveness by restoring a synchronous physical solver, reducing display/physics resolution or catalogue/map tier silently, concealing exceptions, dropping native clouds/PBR, changing opacity/exposure or fabricating stars.
- Do not edit test limits, remove negative controls, redefine an excluded frame as visible, change fixture clocks or weaken the 30-second currentness bound to obtain PASS.
- Do not edit baseline/ or real-sky-reference/ in place, directory-overlay the donor, patch generated native-sky.js/offline.html directly, or perform GitHub writes.
- Do not replace max-delay criteria with median/FPS, discard the slowest trial or overlap the benchmark with other campaigns. Do not claim all baseline cost is caused by CP9.

### Implementation objective
Preserve the accepted native image and metadata while every candidate loaded trial at CPU 1 and CPU 4, full and reduced motion, stays within 250 ms for both maximum heartbeat gap and scheduled dialog lag. Correct only the measured presentation/interaction bottlenecks.

### Discriminating tests and measurements
- Run tools/cp9_performance.py --trials 5 with no concurrent browser/solver job; check every candidate trial, not the aggregate MEASURED status. Baseline is a separately reported control.
- Run the actual-widget presentation cache controls, material preservation, moved-Moon full-frame equation and motion checks. Add a regression test for each changed cache/worker/chunk boundary and an obsolete completion while a native foreground change is pending.
- Run memory restart/dispose, all lifecycle/asset mutations, the 97 baseline integration cases plus new cases, 849 applicable native regressions, and the retained scientific suites. Capture a new profile to verify work moved/vanished rather than changed appearance.

### Exact acceptance and closure
- All 20 candidate trials (five each at CPU1/CPU4 × full/reduced motion) have maxGapMs <= 250 and maxScheduledDialogLagMs <= 250, six prayer rows, working dialog actions, no page errors, and an actual current physical sky in supported normal playback.
- The 8,044 opaque native lunar samples and full-frame moved-Moon composition remain exact; dirty-input metadata, cloud/PBR changes and moving foreground controls pass.
- No lifecycle/source-admission/native-regression failure or memory-resource leak is introduced. Results bind to the exact rebuilt widget tree, with raw trials and negative controls retained.
- A reviewer checks the source delta and new oracle/negative controls; rerunning only the old CP8 receipt does not close this node.

### Reproduction commands
```text
python tools/cp9_profile.py --output ../post-cp9-profile
python tools/cp9_performance.py --trials 5 --output ../post-cp9-performance
python tools/cp9_presentation_check.py --output ../post-cp9-presentation
python tools/native_material_check.py --output ../post-cp9-material
python tools/native_composition_check.py --output ../post-cp9-composition
python tools/native_motion_check.py --output ../post-cp9-motion
python tools/cp9_memory_check.py --output ../post-cp9-memory
```

## CP9-N002 — Native astronomical job scheduling, cancellation, physical/registered-sky evaluation cadence and explicit availability diagnostics.

**Priority:** mandatory. **State:** OPEN. **Finding:** CP9-F102. **Dependencies:** none.

### Exact problem
Accelerated native time advances beyond a physical job’s 30-second accepted-UTC eligibility window before completion. The measured 60× and 600× runs accept zero new moving frames; 10× has gaps. Safety works: no obsolete sky is published, and frozen recovery succeeds. The unresolved issue is throughput/availability and misleadingly indefinite updating, not permission to relax the fence. The initial forced transition is included in the retained 10-second test; 1× is continuously visible after its first current frame.

### Supporting CP9 evidence
- `evidence/cp9/temporal-after-mask/results.json` (`/cases`): At 1/10/60/600×, new accepted frames = 3/2/0/0. Visibility = 65/16/0/0 samples out of 99/100/99/92 in this retained run; consult exact JSON. All frozen recoveries current and no stale publications. First-current and post-first-current metrics explicitly distinguish warm-up.
- `evidence/cp9/affected-cp8/native-lifecycle/results.json`: Ordinary clock changes, A→B→A, old completion and hidden/restore safety controls already exist. This finding is additional high-rate liveness, not a general assertion that CP8 explicit seeks were broken.

### Affected owners
`widget/real-sky/native-lifecycle.mjs`, `widget/real-sky/native-host.mjs`, `widget/real-sky/native-engine.mjs`, `widget/real-sky/native-contract.mjs`, `widget/real-sky/core/src/reference-worker-client.mjs`, `widget/real-sky/core/src/physical-sky-renderer.mjs`, `tools/build_native.py`, `tools/cp9_temporal_rates.py`, `tools/native_lifecycle_check.py`

### Authorised implementation scope
- Reproduce the already-defined same-widget rate transitions and inspect per-request epochs/submission/acceptance. Give obsolete work cooperative cancellation or worker replacement where justified, without starving the newest target.
- Separate reusable observer/camera/source/transport work from time-dependent celestial evaluation in an authored native adapter. Every reuse key must include the existing accepted observer/elevation/weather, source/mask, camera and configuration owners. Compare resulting linear fields and encoded output against the unchanged physical renderer before enabling reuse.
- The 30,000/rate millisecond wall-time eligibility envelope is approximately 3000 ms at 10×, 500 ms at 60× and 50 ms at 600×. Meet it with measured implementation work, not a future timestamp or relabelled old result. Any approximation must first receive an explicit error contract and discriminating oracle tests; no unspecified tolerance is authorised.
- Add finite, explicit capability/availability reporting when a requested rate cannot currently be served, preserving prayer use and recovery to 1×/frozen time. This is a safety/usability improvement only: it does not close the continuous-availability gate while the rate still lacks current frames.

### Invariants
- Accepted native simNow(), observer, configuration generation and elevation custody remain the only astronomical input authority; independent invalidation epoch, A→B→A, hidden, seek, retry and disposal fences survive.
- No visible or newly published frame may differ from accepted native UTC by more than 30,000 ms. Invalid, hidden, superseded or failed input never leaves old light or stale diagnostics visible.
- Prayer admission, six prayer rows, countdown, day rollover, Maghrib calendar selection, settings and weather eligibility remain independent of optional astronomy.
- Preserve the actual native PBR backing canvas, phase, Earthshine and enlarged calendar mask; physical lunar sky illumination/occultation remain separate.
- Retain the one declared cloud/light/exposure equation, strict/missing/estimated source masks, admitted catalogue and no synthetic stellar fallback.
- All 162 native baseline and 950 scientific-reference files remain untouched; generated widget/core files are not a new canonical source. Any new optimised runtime must be authored as a separately tested adapter and included deterministically by tools/build_native.py.

### Prohibited shortcuts
- Do not fix responsiveness by restoring a synchronous physical solver, reducing display/physics resolution or catalogue/map tier silently, concealing exceptions, dropping native clouds/PBR, changing opacity/exposure or fabricating stars.
- Do not edit test limits, remove negative controls, redefine an excluded frame as visible, change fixture clocks or weaken the 30-second currentness bound to obtain PASS.
- Do not edit baseline/ or real-sky-reference/ in place, directory-overlay the donor, patch generated native-sky.js/offline.html directly, or perform GitHub writes.
- Do not supply a private astronomical clock, render future times as already accepted, reuse an old observer at a new site, hide failed rates from the matrix, or call explicit refusal continuous availability. Ordinary clock tick coalescing must not become perpetual supersession.

### Implementation objective
Deliver current registered catalogue/physical-sky frames through the tested native 1×/10×/60×/600× transitions while maintaining the existing stale-safety contract, and terminate unsupported-rate pending states explicitly until the performance target is actually met.

### Discriminating tests and measurements
- Use the retained cp9_temporal_rates.py 10-second transition matrix without removing warm-up observations: at least two new accepted frames and >=80% visible samples at every rate; retain firstCurrentSeconds and visibleFractionAfterFirstCurrent separately.
- Add burst coalescing, repeated force requests, worker cancellation, A→B→A plus rate change, backward seek without generation change and source-reload completion during acceleration. At every publication assert identity/epoch and absolute accepted-UTC difference <=30000.
- Compare any reused/accelerated calculation with the unchanged linear/encoded physical renderer on seasonal, polar, horizon, cloud, Moon, source-mask and camera cases; repeat normal 1× motion and prayer/countdown/calendar tests.

### Exact acceptance and closure
- All four rate cases meet newAcceptedFrames >= 2 and visibleSamples/sampleCount >= 0.8 in the exact retained 10-second transition test, with no stale publications or page errors and exact current frozen recovery.
- Ordinary native time, hidden/visible and target/source invalidation do not starve; a failed/unsupported request reports a finite explicit unavailable state without disabling prayer or preventing recovery. This status change alone is not availability PASS.
- Any accelerated/reused result meets the preserved composition/astrometric/source-support contract on the same native scenes; no unapproved light, coordinate, exposure, resolution or age-budget change is used as compensation.
- Close this node on its currentness/availability tests without claiming CP9-N001 is closed. Re-run and retain the responsiveness measurements after any shared host/message change; the downstream CP9-N003 join, not an implicit prerequisite on this independently ready node, requires both mandatory gates to pass on the combined tree.

### Reproduction commands
```text
python tools/cp9_temporal_rates.py --output ../post-cp9-rates
python tools/native_lifecycle_check.py --group all --output ../post-cp9-lifecycle
python tools/native_lifecycle_mutations.py --output ../post-cp9-mutations
python tools/cp9_seasonal_check.py --output ../post-cp9-seasonal
```

## CP9-N003 — Native entry/deployment boundary, real browser page lifecycle, external prayer/weather admission and hash-bound multi-platform acceptance collector.

**Priority:** mandatory. **State:** OPEN. **Finding:** CP9-F103. **Dependencies:** CP9-N001, CP9-N002.

### Exact problem
The delivery has actual-widget Linux Chromium embedded/subresource evidence, but no native Windows/Firefox/WebKit/live-provider/deployment qualification. Direct top-level HTTP and file navigation are administrator-blocked here; Firefox/WebKit executables are absent and the installation attempt has no successful receipt. Engine launch, synthetic persisted pageshow and CSS DPR emulation are not the missing end-to-end tests.

### Supporting CP9 evidence
- `evidence/cp9/navigation/results.json`: Both direct local HTTP and file entry attempts report ERR_BLOCKED_BY_ADMINISTRATOR. This is environmental, not evidence of a product navigation defect.
- `evidence/cp9/platform/results.json`: Actual OS/engine launch identities and absent Firefox/WebKit executables; no silently substituted engine.
- `evidence/cp9/platform/install-attempt.json`: Attempted managed browser install lacks success receipt; no platform PASS.
- `evidence/cp9/controls-final/results.json`: Controlled pagehide/persisted-pageshow ordering passes; explicitly not an actual browser BFCache traversal.
- `evidence/cp9/environment.json`: Exact development/qualification tool environment.

### Affected owners
`tools/browser_runtime.py`, `tools/cp9_platform_probe.py`, `tools/native_navigation_probe.py`, `tools/native_browser_check.py`, `tools/native_lifecycle_check.py`, `tools/qualify_cp9.py`, `widget/index.html`, `widget/offline.html`, `widget/real-sky/native-assets.mjs`, `widget/real-sky/native-host-hooks.js`

### Authorised implementation scope
- Prepare platform runners in parallel, but bind final acceptance to the single integrated runtime after CP9-N001 and CP9-N002. Use the existing explicit browser selector; add a result collector that requires actual OS/engine identity, runtime-tree SHA, entry URL scheme, source requests and per-check status, rather than promoting engine launch.
- Run real native Windows Chromium and Firefox with both the served widget/index.html tree and widget/offline.html local entry. Run WebKit on its documented supported host and report that OS explicitly, not as Windows WebKit. Preserve any blocked environment as NOT_TESTED.
- Repeat native scenes, failure/currentness controls, material/composition, prayer/settings, timezone/day/Maghrib and recovery in each engine. Replace CDP-only visibility/CPU mechanisms with honest engine-appropriate tests; keep the CPU×4 budget a Chromium-specific labelled control.
- Exercise actual navigation away/back with persisted BFCache status and worker cleanup/restart, plus a deployment-like CSP that permits only declared assets/worker requirements. Do not disable browser security globally to make the test pass.
- Use clearly separated live prayer/weather probes to test provider requests, accepted generation/elevation and normal unavailable states; record time/observer/admitted-source metadata without inventing a successful provider reply. Correct demonstrated compatibility defects only in the responsible authored adapter and regenerate.

### Invariants
- Accepted native simNow(), observer, configuration generation and elevation custody remain the only astronomical input authority; independent invalidation epoch, A→B→A, hidden, seek, retry and disposal fences survive.
- No visible or newly published frame may differ from accepted native UTC by more than 30,000 ms. Invalid, hidden, superseded or failed input never leaves old light or stale diagnostics visible.
- Prayer admission, six prayer rows, countdown, day rollover, Maghrib calendar selection, settings and weather eligibility remain independent of optional astronomy.
- Preserve the actual native PBR backing canvas, phase, Earthshine and enlarged calendar mask; physical lunar sky illumination/occultation remain separate.
- Retain the one declared cloud/light/exposure equation, strict/missing/estimated source masks, admitted catalogue and no synthetic stellar fallback.
- All 162 native baseline and 950 scientific-reference files remain untouched; generated widget/core files are not a new canonical source. Any new optimised runtime must be authored as a separately tested adapter and included deterministically by tools/build_native.py.

### Prohibited shortcuts
- Do not fix responsiveness by restoring a synchronous physical solver, reducing display/physics resolution or catalogue/map tier silently, concealing exceptions, dropping native clouds/PBR, changing opacity/exposure or fabricating stars.
- Do not edit test limits, remove negative controls, redefine an excluded frame as visible, change fixture clocks or weaken the 30-second currentness bound to obtain PASS.
- Do not edit baseline/ or real-sky-reference/ in place, directory-overlay the donor, patch generated native-sky.js/offline.html directly, or perform GitHub writes.
- Do not count engine launch, mocked providers, synthetic page events, Linux DPR emulation or an absent executable as native Windows/live/BFCache acceptance. Do not overwrite earlier failures, disable web security or remove a browser from the mandatory matrix without explicit owner approval.

### Implementation objective
Produce reproducible actual-entry, lifecycle, provider and render evidence for the declared target engines/platforms, fixing any demonstrated compatibility defects, and assemble one acceptance matrix bound to the final combined tree.

### Discriminating tests and measurements
- Implement a hash-bound platform collector and negative controls for wrong OS, wrong tree SHA, ENGINE_LAUNCH_ONLY, missing test sections, fixture-labelled results offered as live and duplicate results. Collector must refuse these as PASS.
- Use normal local HTTP and file entry, native browser navigation, actual calendars/settings, failure/retry and source-admission paths; capture screenshots plus numerical/identity assertions rather than screenshots alone.
- Repeat full final build/manifest/unit/native/scientific checks, affected CP8 browser assertions and CP9-N001/N002 evidence on the integrated tree, with an independent code/evidence review before merge or release.

### Exact acceptance and closure
- Native Windows Chromium and Firefox and explicitly identified-host WebKit all have actual-widget evidence for both applicable entry forms, lifecycle/currentness/source failure, PBR/composition, prayer/calendar/settings and documented provider admission outcomes. Required cases are neither absent nor engine-launch-only.
- Actual BFCache/navigation and deployment/CSP behaviour are evidenced rather than inferred from synthetic events; externally unavailable providers are correctly labelled and cannot supply stale state. Live-admission successes and unavailable-path successes are distinguished.
- The acceptance collector detects wrong/stale/missing/fixture-mislabelled evidence and every accepted result binds the final CP9 runtime tree after CP9-N001/N002.
- All mandatory nodes are closed by their exact conditions with fresh extraction/rebuild/hash verification and independent review. A sealed archive or completed report alone is not release authority.

### Reproduction commands
```text
python tools/native_navigation_probe.py --output ../post-cp9-navigation
python tools/cp9_platform_probe.py --output ../post-cp9-platform-inventory
python tools/native_browser_check.py --scenes tests/native-scenes-82.json --output ../post-cp9-native-scenes
python tools/verify_native_scenes.py ../post-cp9-native-scenes/results.json --output ../post-cp9-native-scenes-acceptance.json
python tools/qualify_cp9.py --output ../post-cp9-integrated-verification
```

## Closed findings — excluded from the frontier

- **CP8-F01** — Target-bound accepted elevation: DEMONSTRATED_IMPROVEMENT_ADOPTED. Eight failing starting-candidate controls repaired; A→B→A, stale/absent/simulated weather and known zero covered; narrow post-native-admission hook.
- **CP8-F02** — Currentness and scheduler comparison: ALREADY_ADDRESSED_PLUS_BOUNDED_IMPROVEMENT. Retain CP8.3 epoch and native-clock mechanism; adopt 30-second ceiling; ordinary currentness safe. Accelerated availability separately OPEN CP9-F102.
- **CP8-F03** — Worker loss may block the prayer event loop: DEMONSTRATED_IMPROVEMENT_ADOPTED. Physical worker loss withdraws optional sky; failure path 2255.5→17.8 ms heartbeat in matched control; retries restore a worker. Broader CPU stress remains OPEN CP9-F101.
- **CP8-F04** — Composition, exposure, camera and lunar alternatives: COMPARED_COHERENT_MODEL_RETAINED. Matched no-colour uniform-transmission operator pixels coincide; native colour/meter policies differ. No measured calibration superiority established; no incompatible parameter transplant. PBR/material and exact operator invariants retained.
- **CP9-F005** — Page exit cleanup and persisted return: DONOR_SAFEGUARD_ADAPTED. Paired suspend/resume with generation fencing, only persisted pageshow resumes. Controlled ordering passes; real BFCache remains CP9-F103.
- **CP9-F006** — Second cloud owner admitted accidentally: DONOR_INVARIANT_ADOPTED. Native physical engine refuses second cloud attenuation/glow; own local-light policy unchanged.
- **CP9-F007** — Ignored scintillation disable parameter: REPRODUCED_AND_FIXED. Use actual strength:0 contract; no unintended sparsely sampled twinkle. Smooth optional scintillation is not invented as a mandatory residual.
- **CP9-F008** — Obsolete native synthetic diagnostic ownership: DONOR_DIAGNOSTIC_JOIN_ADAPTED. Additive compact realSky diagnostics preserve native fields; legacy counters labelled inactive and optional diagnostic exceptions isolated.
- **CP9-F009** — Per-pixel native transform reads: MEASURED_EXACT_OPTIMISATION. Six DOMMatrix coefficients/AA ramp hoisted once; 48 affine/radius/DPR controls exact; native browser median12.75→1.4ms.
- **CP9-F010** — Redundant unchanged native presentation: DONOR_FAST_PATH_ADAPTED_WITH_STRONGER_OWNERSHIP. Only exact physical-frame/support/geometry/cloud/PBR identity skips pixels; cached-pixel metadata refresh regression found and fixed. No cadence, alpha or source change.
- **CP9-F011** — Hard-coded browser launcher: PORTABLE_INVOCATION_IMPLEMENTED. Explicit engine/executable selection with no fallback; five tests. This closes invocation portability only, not target-platform acceptance.

## Completion

Completion requires every mandatory node’s exact closure conditions, a single combined deterministic tree and new current acceptance evidence. An archive hash establishes custody, not correctness; a prior receipt establishes only its own bytes. Independent review is still required before merge/release. No GitHub write is authorised by this package.
