> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane C — configuration, persistence, builder, settings UI, frozen `v1/`

Baseline: main `363c3e53`. Historical reference: `f71fef6c`. This is a read-only audit. Line numbers point to the authored source at the baseline unless stated. Generated counterparts:

- root `config.js` and `builder.html` are byte-identical to `src/native/*`. Verified with `cmp`. sha256 `719efed9…` and `873e8ded…`.
- In root `index.html`, the settings and config code sits about 3,430 lines later than in the source: `classifyConfigChange` L4250, `applyConfig` L7162, `_commitSettings` L7530, `_resetLocal` L7555.
- `offline.html` carries the same code: `classifyConfigChange` L4734, `applyConfig` L7646, `_resetLocal` L8039.

Evidence vocabulary:
- **VM** means the repo's own source-bound VM fixture (`tests/r000f-fixture.cjs`). It is not native browser evidence.
- **Native** means a historical headless Chromium or Firefox report retained under `docs/state-contracts/evidence/`. I did not re-run it here.

## 1. Machine census

### N01 (configuration-propagation side) — accepted-config apply, effect classification and dispatch
- **Scope.** Decides what a proposed WidgetConfig invalidates: nothing, presentation only, or the location generation (prayer, weather, radar, sky).
- **Sources:**
  - `src/native/index.html` `bindConfig` L683-690
  - `CONFIG_EFFECTS` L697-708
  - `sameConfigEvidence` L710-720
  - `classifyConfigChange` L721-741
  - module resolve L742-761
  - `resetForNewLocation` L3717-3726
  - `applyConfig` L3729-3760
  - `boot` L3779-3815
- **Dimensions:**
  - accepted `CONFIG` (object or null)
  - live bindings `lat/lon/tz/_cacheTz/label/fmt24/datefmtStr/LPOLL/units/method/school`
  - classification path: `none` / `presentation` / `broad`
  - `_runtimeGeneration`
  - persistence result (see N22)
  - `_cfgMode`: hardcoded / local / preferLocal / bare
- **Transitions:**

| Event | Guard | Effect |
|---|---|---|
| `applyConfig(cfg,opts)` | always | `normalize` → classify against the live `CONFIG` **before** `saveLocal` rewrites `source/savedAt` (L3734) |
| opts.save | SalahConfig present | `saveLocal` → `_publishPersistence` before any await (L3735-3738) |
| path `none` | equal semantics | `CONFIG=cfg` only (L3740) |
| path `presentation` | only label/time/datefmt/appearance differ | rebinds `label/fmt24/datefmtStr`, card dataset, `setLocLabel`, `_renderDirty`. Never `bindConfig`, so the provider-adopted `tz` and `_cacheTz` survive (L3741-3748) |
| path `broad` | any broad field, an unknown key, an evidence/origin difference, or `opts.reset` | `beginRuntimeGeneration` → `bindConfig` → `resetForNewLocation` → `startWeather` → `await loadPrayerData` → generation recheck → `startRenderLoop` (L3750-3759) |
| superseded apply | `generation!==_runtimeGeneration` after await | returns without starting the loop (L3758) |

- **Invariants:**
  - The classifier is pure and fails closed: an unknown key or unknown evidence field goes broad (L713, L729).
  - Reset is broad even when values are equal (L722).
  - `applyConfig` is the sole dispatcher.
- **Failures:**
  - `_commitSettings` calls `applyConfig` fire-and-forget with no `catch` (L4103). See F-C07.
  - Legacy `config.js`-missing path: hand-built `CONFIG` without `locationEvidence/seed` (L746-760). In that mode settings are never enabled.
- **Enforcement:**
  - documentation: state contract `docs/state-contracts/R0003.md` plus comments L691-696
  - implementation: explicit and enforced (frozen table consumed once)
  - verification: unit + mutation tests (`tests/config-effects-state.test.cjs`, `-mutations.test.cjs`, run here: pass). Native was observed on an earlier tree; served `index.html` has since changed through R0021/R0027 merges, so it is history by byte identity.
- **Observed:**
  - label/time/datefmt/no-op now avoid the generation bump (XF01 core).
  - `units`, `lp`, `seed`, `method`, `school` stay broad by owner decision (R0003 D3/D4).
  - `CONFIG.seed` has no runtime consumer: cloud and star seeds read `q.get("seed")` from the document hash (L2190, L2759, L2772).
- **Hypotheses.** The settings form carries `tz:(CONFIG&&CONFIG.tz)||tz` (L4026). A settings location change can keep the previous region's tz hint. `bindConfig` then freezes `_cacheTz` to it for the new site until the provider adopts the new zone. Cross-lane (prayer N04).
- **Unknowns.** Whether a native visible flash remains on broad applies. I took no screenshot in this lane.

### C01 — configuration persistence and mode resolution
- **Sources.** `src/native/config.js`:
  - `parseHash` L118-137
  - `normalize` L140-160
  - `validate` L163-174
  - `serialize` L182-206
  - `storageAvailable/loadLocal/saveLocal/clearLocal` L211-249
  - `resolve` L333-353
  - `applyHashPrefs` L357-362
- **Dimensions:**
  - mode: local > preferLocal > hardcoded (hash lat+lon) > bare
  - stored record: absent / valid v1 / invalid / unreadable
  - `source` (storage marker `localStorage`) vs `origin` (acquisition)
  - `savedAt`
- **Transitions:**
  - `resolve` is synchronous at script evaluation.
  - In local mode the saved record wins, else detection runs.
  - preferLocal: saved, then hash coordinates, then detection.
  - Hash preferences overlay only detected bases (`applyHashPrefs`). A saved record wins over embed hash preferences (intentional).
  - `saveLocal` returns `{ok,savedAt}` / `{ok:false,error}` and rewrites a browser-geolocation `source` to `manual` while keeping `origin` (L239-241).
  - `clearLocal` returns a result (L246-249).
- **Invariants:**
  - No accessor throws to its caller.
  - Version gate `v===1`.
  - `validate` rejects records without coordinates.
- **Failure:**
  - parse/version/validation failure → `null` (treated as absent; no diagnostic).
  - No cross-tab `storage` listener and no `hashchange` listener in `src/native/index.html` or `builder.html` (grep: none). A configuration change in another tab or a hash-only src change applies only on reload.
- **Enforcement:**
  - documentation: comments plus R0026/R0003 contract rows
  - implementation: partly explicit
  - verification: unit tests `tests/r0010-preferences.cjs` (9/9), `tests/r0011-storage.cjs` (18/18), `tests/location-admission-*` (run, pass)
- **Observed:**
  - Coarse detection at boot is bound but **not persisted** (L3795-3800). Local mode re-runs IP detection on every load until a settings close-save.
  - Stored detection after Reset is also not saved (`save:false`, L4136).
- **Unknowns.** Native blocked/quota/partitioned-storage behaviour was not run here.

### C05 — builder mode, form, serialization and preview publication (R000F)
- **Sources.** `src/native/builder.html`:
  - `formConfig` L205-210
  - `hash` L212
  - `snippet` L215-218
  - `issued`/`previewIdentity` L223-226
  - `draftInvalid` L229-233
  - `showValidity` L239-244
  - `refuseInvalid` L245-253
  - `issuePreview` L257-262
  - `update` L263-270
  - `setMode` L271-285
  - radio keydown L289-297
  - bindings L298-299
  - Refresh/Open/Copy L425-427
  - Install L492-495
- **Dimensions:**
  - draft (fields + `embedMode` + `builderLocation`)
  - validity (portable lat/lon null → invalid)
  - export (`#code`)
  - issue receipt `issued{identity,src,allow,hash,rev}`
  - `rev`
- **Transitions:**

| Event | Effect |
|---|---|
| input/change with an equivalent output | export refreshed; no navigation (identity equal) |
| genuine change | exactly one `issuePreview`; `allow` set before `src`; record and `rev++` only after the setter returns |
| invalid draft | `aria-invalid` + note; export and preview retained; Copy/Open/Install refuse (handler check) |
| Refresh | re-issues the last valid `issued` with a new `?r=`; with no record yet, it calls `update()` |
| active radio click | identity unchanged → 0 navigations |

- **Invariants:**
  - one serializer (`SalahConfig.serialize`)
  - iframe 325×530 (L167)
  - `allow="geolocation"` only in local mode
  - `issued` never means "loaded"
- **Failure.** A throwing `src` setter leaves no record, so the next attempt navigates.
- **Enforcement:**
  - documentation: state contract `R000F.md`
  - implementation: explicit and enforced
  - verification: unit + mutation tests (`tests/builder-preview-publication*.test.cjs`, run: pass) plus native headless Chromium 148 / Firefox 153 on served builder `873e8ded…`. That byte-equals the baseline builder, so the native evidence applies by identity.
- **Observed:**
  - If `SalahConfig` is absent, `draftInvalid` returns `[]` and `hash()` returns `""`. The builder then issues a bare `base?r=0#`.
  - The `auto` parameter of `locate` is never passed `true` (only call: L512). It is dead.
- **Unknowns.** Real (headed) device behaviour.

### C06 — builder edit ownership, candidate cycle and automatic fills
- **Sources.** `builder.html`:
  - `searchReset/captureLookup/ownsLookup` L330-332
  - `doSearch` L353-366
  - label input/Enter L367-382
  - `fillNameFromCoords` L383-398
  - lat/lon input L399
  - `locate` L496-511
  - `detectArea` L514-527
  - `labelAuto/methodAuto` L303-305
- **Dimensions:**
  - `locationEdit`, `srchSeq`
  - candidates `multiCands/multiIdx/multiOwner`
  - timers `srchDebounce` (1 s), `geoTimer` (700 ms), `tipRevert` (4 s)
  - flags `labelAuto/methodAuto`
  - provenance `builderLocation`
- **Transitions:**
  - Every completion (forward, reverse, GPS, coarse) checks `ownsLookup(owner)` after its await.
  - Coordinate edits null `builderLocation`. Label edits preserve it.
  - R0026 admits external coordinates (`admitCoordinates`, L503) before publishing.
- **Failures:**
  - Reverse lookup has no timeout, no abort and no HTTP gate (L390-391).
  - Any JSON body is adopted. A body without `continentCode` sets `method="4"` when `methodAuto` (L395). See F-C02.
  - Failures are swallowed silently (L397).
- **Enforcement:**
  - documentation: R000F/R0026 contracts and comments
  - implementation: partly explicit (ownership explicit; reverse transport implicit)
  - verification: unit + mutation tests (`r000f-intent` 21/21, `r000f-mutations`, `location-admission-*`). The reverse error path is untested.
- **Observed.** In local mode, dimmed lat/lon edits still schedule BigDataCloud reverse lookups (probe P3, VM). Local mode does not export the coordinates, yet the reverse result can still change the exported `method`.

### C07 — clipboard attempts, fallback and expiring feedback
- **Sources.** `builder.html`:
  - `copyText` L450-468
  - `copyActions`/`copyArtifact` L471-491
  - `refuseInvalid` L245-253, which abandons an earlier copy on the same button
- **Dimensions:** per-button `{seq,timer}`; button disabled; tip text; recovery box.
- **Invariants:**
  - An older attempt cannot touch a newer one.
  - The temporary textarea is removed in `finally`.
  - The recovery box keeps the captured payload.
- **Enforcement:**
  - documentation: comments plus R0012 certificate (pre-audit)
  - implementation: explicit
  - verification: unit + mutation tests (`r0012-clipboard` 11/11, `r0012-effects` 3/3, mutation suites pass)
- **Known residual (R000F F4).** A "copied ✓" tip can outlive a later invalid draft until its timer clears.
- **Unknowns.** Native clipboard permission.

### N20 — settings disclosure, focus, dirty form and close-save
- **Sources.** `src/native/index.html`:
  - `_enableSettingsAffordance` L4008-4018
  - `_wireSettings` L4044-4094
  - `_recordSetEdit` L3947-3951
  - `_commitSettings` L4097-4104
  - `_openSettings` L4145-4154
  - `_closeSettings` L4155-4164
- **Dimensions:**
  - `_setOpen`, `_setSession`
  - `_setDirty`
  - `_setFocusTimer` (30 ms, session-guarded)
  - `_setLastFocus`
  - buckle tabindex/interactive
- **Transitions:**
  - Open: session++, invalidate location, populate, focus timer.
  - Close/Escape: session++, invalidate, commit if dirty and valid, restore focus.
  - Any `input`/`change` marks the form dirty. Reverted edits still close-save, as the `none` path with a persistence outcome.
- **Invariant.** Close is auto-save (Escape included). This is intentional.
- **Gap.** `_resetLocal` never resets `_setDirty` before its awaits. See F-C01.
- **Enforcement:**
  - documentation: comments plus R000F/R0011 certificates
  - implementation: partly explicit
  - verification: unit tests (`r000f-intent`, `r000f-reset` 9/9, `r0011-storage`)
- **Unknowns.** Native tab order and screen reader.

### N21 — settings place search, GPS, candidate cycling and reset intent
- **Sources:**
  - `_invalidateSetLocation/_captureSetLookup/_ownsSetLookup` L3944-3946
  - `_runSetSearch` L3976-3989
  - `_showSetCand` L3990-4003
  - label keydown L4079-4093
  - `_usePrecise` L4105-4121
  - `_resetLocal` L4122-4144
  - `_newerSetPrefs` L3952-3956
- **Dimensions:**
  - owner `{session,edit,seq}`
  - candidates
  - `_setLocationEvidence/_setLocationOrigin/_setLocationSaved`
  - preference versions `_setPrefVersions`
- **Transitions:**

| Event | Effect |
|---|---|
| Reset | `clearLocal` (sync) → publish outcome; failure stops. Success → coarse detect → owner check → merge newer prefs → `applyConfig(c,{save:false,reset:true})` → owner check → repopulate + restore newer prefs + `_setDirty=prefs>0` |
| label/lat/lon input during Reset | invalidates the reset continuation |
| close during Reset | invalidates the continuation; the commit runs if `_setDirty` |

- **Invariant claimed.** The last explicit location intent wins. A display-name edit preserves location (comment L4063).
- **Violated path (VM-demonstrated, F-C01).** A display-name edit, or a pre-reset dirty edit, during the Reset window abandons the continuation. Close then commits the **pre-reset** coordinates, reverting the reset-applied location and re-persisting it.
- **Enforcement:**
  - documentation: R000F/R0026 contracts
  - implementation: partly explicit
  - verification: unit + mutation tests. The reset-then-close-with-dirty-form path is not tested.

### N22 — persistence outcome and persistent warning
- **Sources:**
  - `_persistenceMessage` L3915-3921
  - `_renderSettingsStatus` L3922-3925
  - `_renderPersistenceAffordance` L3926-3933
  - `_publishPersistence` L3934-3940
  - callers `applyConfig` L3737 and `_resetLocal` L4125
- **Dimensions:**
  - `_persistOutcome{operation,status:saved|cleared|session-only|reset-failed,error}`
  - `_storageErr`
  - hint `_setHint`
  - buckle `persist-warning` with gear `!`
- **Invariant.** A save failure never claims persistence. A reset failure never claims cleared. The hint composes with the outcome, not over it.
- **Enforcement:**
  - documentation: R0011 certificate
  - implementation: explicit
  - verification: unit + mutation tests (`r0011-storage` 18/18, `r0011-mutations`)
- **Observed:**
  - After a successful Reset and a close during detection, status keeps "Saved settings cleared. / Detecting your area…" while runtime keeps the old configuration (probe P2). See F-C04.
  - `qaState()` calls `storageAvailable()`, which performs a storage `setItem/removeItem` (L3587; config.js L211-218). This is a write on a diagnostic read (F-C08).

### NEW-C-01 — document-hash direct reads parallel to the resolved CONFIG
- **Scope.** Some consumers read `q = URLSearchParams(location.hash)` (L677) directly and not `CONFIG`:
  - `seed` at L2190, L2759, L2772
  - every SIM/debug flag (L770ff)
- **Effect.** Two authorities exist for `seed`:
  - In local mode a saved record's `seed` and `CONFIG.seed` are carried through settings and storage (L4026) but never read by the renderer.
  - A `seed` difference is classified broad (L707) without an in-place consumer. R0003's table admits this.
- **Enforcement:**
  - documentation: R0003 table row
  - implementation: implicit
  - verification: none beyond the table test
- **Hypothesis.** Low materiality, because the settings form always proposes `CONFIG.seed` (no differing producer except Reset, which is broad anyway).

### NEW-C-02 — builder ↔ widget preview handoff and embed-size contract
- **Scope.** How a builder draft reaches a running widget, and the wrapper contract.
- **Sources:**
  - builder `base` L201, `issuePreview` L257-262, iframe L166-167, snippet L215-218
  - `presets/salah-widget.tablissng.json` L9
  - `README.md` L37, L224, L564-575
- **Observed facts:**
  - The preview is `base?r=N#hash` with a cache-busting query. The widget reads only the fragment, and there is no `hashchange` listener, so a reload is required.
  - The iframe has no `sandbox`, so the preview is same-origin with the builder.
  - In `#local=1`, the preview widget therefore uses the builder visitor's own saved root settings. Those win over the builder's explicit preferences, as disclosed in the mode note L281. The preview can also write that storage through its settings panel.
  - 325×530 holds in the builder iframe, snippet, README current snippets and TablissNG preset.
  - The README V1 snippet is 330×534 and says "For the current version, change only `src`" (L564-575). See F-C03.
- **Enforcement:**
  - documentation: AGENTS.md forbidden-regression row; R000F ES0F-15
  - implementation: static contract
  - verification: unit (R000F `invariants` scenario covers current snippets only) plus native layout cell

### C15–C23 — frozen `v1/` machines
`git diff f71fef6c 363c3e53 -- v1` is empty, so every v1 machine is byte-unchanged. `v1/` is **still reachable and served**:
- Pages builds the repository root through Jekyll. `_config.yml` excludes only one evidence directory.
- `tools/verify_r0017_pages_payload.py` L75 adds every tracked `v1/` file to the protected output set.
- `README.md` L556-575 advertises `/salah_widget/v1/#local=1`.

`v1/VERSION.json` `knownLimitations` still says "Public V1 deployment is pending…". I cannot determine whether that is stale without contacting Pages. Neither `docs/V1_PRESERVATION.md` nor `VERSION.json` records the CF07/CF08/CF09 limitations; the original audit proposed documenting them.

| id | name | sources (unchanged lines) | implementation | Notes |
|---|---|---|---|---|
| C15 | one-time root import latch | `v1/config.js` | partly explicit | `tests/v1_storage.cjs` 10/10 (run) |
| C16 | apply/boot without generation ownership | `v1/index.html` L2166ff | implicit | CF07 source |
| C17 | prayer cache/retry/rollover | `v1/index.html` L743ff | partly explicit | — |
| C18 | weather acquisition | L771ff | partly explicit | — |
| C19 | radar | L816ff | implicit | — |
| C20 | modal editing / lookup / GPS / Reset | L2302-2451 | implicit | CF07, CF08 (`_resetLocal` L2421-2428 ignores the `clearLocal` result and says "Local settings cleared.") |
| C21 | clock anchor | `v1/index.html` | partly explicit | — |
| C22 | Moon texture readiness | `v1/index.html` | implicit | — |
| C23 | synthetic stars | `v1/index.html` | implicit | — |

Enforcement for all of these:
- documentation: `docs/V1_PRESERVATION.md` (provenance only)
- verification: `tools/verify_v1.py` byte verification plus `tests/v1_storage.cjs`; no behavioural tests of CF07-09

## 2. Historical-to-current reconciliation

| Original | RLGWO / commit | Change | Disposition |
|---|---|---|---|
| N01 (config side) | R0003 #3: `e5a2ba25` RED, `a06957c6` fix, `411fef97` mutations, merge `64258c86` | `CONFIG_EFFECTS` + `classifyConfigChange` + three-path `applyConfig` (diff L48-77, L602); Reset gains `reset:true` | implemented but not fully verified. Source + mutation tests pass here; native evidence predates later `index.html` changes |
| XF01 | R0003 | label/time/datefmt/no-op/failed-save retry are now `presentation`/`none` with no generation bump; units/lp/seed/method/school still broad (D3/D4) | partly resolved. The projected direction was taken for display-only fields; the units/lp/seed narrowing was never done (deferred by owner) |
| C01 | R0026 #68 `fbd08aa1` (admission); R0010/R0011 pre-audit | `admitCoordinates`, `geocodeSearchDetailed`, bounded `attempts`; `normalize/serialize/resolve/loadLocal` byte-unchanged (A8) | partly resolved. External admission explicit; persistence/mode unchanged; no cross-tab/hashchange handling |
| C05 | R000F #15: `3fa22ff1` RED, `53d1dc32` fix, `12d60cca` mutations, `85546306` re-review, `08ce6573`/`47b39cbb` | issued-identity record, invalid-draft policy, forced Refresh | resolved and independently verified. Contract records an independent exact-tree review PASS_WITH_FINDINGS; native on identical bytes |
| CF05 | R000F | equivalent input/change pair → 0 navigations; changed → 1 | resolved and independently verified (same evidence; native main control FAIL 3 vs candidate PASS 0) |
| C06 | R0026 (search/GPS admission, detailed outcomes); R000F (`staleLookup` scenario) | consumer-side admission and outcome classes; reverse lookup untouched | partly resolved. Reverse lookup still has no timeout/HTTP gate (original C06 residual retained) plus new F-C02 |
| C07 | R000F `refuseInvalid` (abandons same-button copy) | refusal integrated with copy ownership | implemented but not fully verified (VM + mutations; no native clipboard) |
| N20 | R0003 (close-save classification) | close-save of reverted/cosmetic edits no longer broad | implemented but not fully verified. Dirty-state/Reset interplay still implicit (F-C01) |
| N21 | R0026 (`_runSetSearch` detailed outcomes); R0003 (`reset:true`) | three feedback classes; Reset explicit broad | partly resolved. The Reset continuation is still lost on dirty close (F-C01, new) |
| N22 | none after the audit (R0011 pre-audit) | unchanged except callers | still partly explicit, as before; no regression found |
| CF07 | none (v1 frozen) | none | still implicit or vulnerable (frozen; still served; limitation not documented) |
| CF08 | none | none | still implicit or vulnerable (same) |
| CF09 | none (root analogue already bounded; R001F) | none | still implicit or vulnerable in v1 (same) |
| C15–C23 | none | none | unchanged/frozen. Reachable at `/salah_widget/v1/` |
| R001A (radio) | pre-audit | unchanged; `r001a-radio` 8/8 | implemented but not fully verified (ES0F-10 PARTIAL in VM; native Enter/Space observed) |
| R001B (recipients doc) | pre-audit | README privacy table; builder note L193 still lists the recipients | not re-verified. The builder still sends coordinates to BigDataCloud in local mode (F-C05) |

## 3. Findings

**F-C01 — Reset's location authority is lost when the form is dirty at close (pre-reset edit or display-name edit during the Reset window)**
- Machines: N20, N21, N01, N22.
- Evidence class: **demonstrated (VM)**.
  - Probes `probes/C/reset-close-probe.cjs` P1 and `probes/C/reset-label-probe.cjs`.
  - Edit method → Reset (storage cleared, "Saved settings cleared.") → close before detection completes. Close-save re-persists the old site (lat 24.4672, method 3).
  - Typing a display name during Reset's apply await: runtime is at the detected 40.7, the form still shows 24.4672, and close applies plus saves 24.4672 with label "Home".
- Trace:
  - `_resetLocal` L4122-4144 never clears `_setDirty`, and only repopulates the form after both awaits.
  - The label input calls `_invalidateSetLocation` (L4064-4065) even though the comment at L4063 says name edits preserve acquisition.
  - `_closeSettings` → `_commitSettings` L4097-4104 commits stale form coordinates.
  - The lines are unchanged since `f71fef6c` except `reset:true`, so this predates the audit and was not in it. A fixture run at `f71fef6c` failed with `ENOBUFS` on `git show`, so it was not reproduced there.
- Severity: medium-low.
  - The user-intended Reset is silently undone, and the runtime flips back to a location the user tried to discard.
  - It needs a dirty form, Reset, and close or typing inside a window of up to about 6 s of detection plus prayer load.
- Open questions:
  - Should Reset clear pre-reset dirtiness (test L49-52 implies pre-reset edits are discarded)?
  - Should display-name edits invalidate the Reset continuation?
- Limitation: the fixture stubs `applyConfig` (no real `_publishPersistence` on close).

**F-C02 — Builder reverse geocode adopts any JSON body; a body without `continentCode` silently switches the auto method to Umm al-Qura**
- Machines: C06, C05.
- Evidence class: **demonstrated (VM)**.
  - `probes/C/reverse-error-probe.cjs`: coarse US detection (method 2), lat edit, reverse reply `{status:429,…}`.
  - The export changes from `method=2` to `method=4`.
- Trace: `builder.html` L390-396. There is no `r.ok` check, no timeout or abort, and L395 is `(j.continentCode==="NA")?"2":"4"`. The code is unchanged from `f71fef6c` L339.
- Severity: medium-low. It changes the prayer calculation method baked into a portable embed. The real provider error body shape was not verified.
- This is an error represented as success.

**F-C03 — README V1 snippet sets 330×534 and tells current-version users to "change only src"**
- Machines: NEW-C-02.
- Evidence class: **demonstrated (source)**. `README.md` L564-575, against the AGENTS.md 325×530 forbidden regression.
- R000F recorded this as pre-existing (contract §Limits) and did not fix it. The R000F invariant test checks only current snippets.
- Severity: low (doc-induced embed drift).

**F-C04 — Successful Reset followed by close during detection leaves runtime ≠ storage for the session, with a stale "Detecting your area…" hint**
- Machines: N21, N22.
- Evidence class: **demonstrated (VM, P2)**. Applied count 0, storage empty, runtime lat 24.4672.
- The "cleared" claim is true for storage. The divergence and the hint are the issue.
- Severity: low.

**F-C05 — Local-mode builder still sends dimmed coordinates to BigDataCloud**
- Machines: C06.
- Evidence class: **demonstrated (VM, P3)** for the request.
- The resulting method change in the local export is **plausible**: it combines with F-C02 and `explicitPrefs:["method"]` (L212).
- Trace: L399 → L383-396.
- Severity: low (privacy/efficiency). The recipient is disclosed at L193.

**F-C06 — XF01 residual: units/lp/seed/method/school remain broad, and `seed` has dual authority (hash vs CONFIG)**
- Machines: N01, NEW-C-01.
- Evidence class: **plausible risk** (efficiency).
- Trace: L707, L2190, L2759, L2772, L4026.
- Owner-deferred (R0003 D3/D4). Not a defect claim.

**F-C07 — `_commitSettings` fires `applyConfig` without a rejection handler**
- Evidence class: **plausible risk**. L4103.
- An exception after `saveLocal` becomes an unhandled rejection. The persistence status is already published; prayer/weather may be left half-reset.

**F-C08 — Diagnostic `qaState()` performs a storage write probe**
- Evidence class: **speculative** impact. L3587 → config.js L211-218.

**F-C09 — Frozen v1 CF07/CF08/CF09 remain live on a served URL, and the limitation is not recorded**
- Evidence class: **demonstrated (source)**. v1 diff is empty; Pages inclusion per `verify_r0017_pages_payload.py` L75; `VERSION.json` `knownLimitations`.
- Severity: medium for privacy/control truth (CF08) on a compatibility surface.
- Repair needs owner authority. Respect the freeze.

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

Schematic only:
- `q` is the configuration-apply topology: classifier paths, Reset continuation, builder issue identity, and the reverse-lookup transport.
- The hard constraints `F_hard` in play:
  - prayer correctness, including calculation method
  - rejection of unauthorised late results
  - truthful location provenance
  - truthful persistence claims
  - accepted (runtime) ≠ displayed (form) separation
  - frozen v1 authority
  - 325×530 contract

| Interaction | Current q | Neighbour q' = apply(q,η) | Benefit | Regression cost | Evidence | Class |
|---|---|---|---|---|---|---|
| Display-only config change vs prayer/weather/sky work (XF01) | 3-path classifier | — | — | — | before: `f71fef6c` broad chain (original probe); after: `config-effects-state` RED 16/34 → GREEN 34/34, mutations, native | **demonstrated improvement** |
| Units-only change | broad | η: weather-only path (no prayer/sky reset) | fewer requests | stale converted values, radar coupling | none | insufficient evidence (owner-deferred; retain) |
| Builder equivalent edits → preview navigations (CF05) | issued-identity gate | — | — | — | native main control 3 vs candidate 0; ledger 34 → 14 assignments | **demonstrated improvement** |
| Reset continuation vs dirty close-save (F-C01) | continuation dropped; stale form committed | η1: clear `_setDirty` and snapshot the form at Reset dispatch. η2: label input stops invalidating the Reset continuation. η3: close during Reset commits only newer prefs over the reset target | Reset intent kept; runtime/form agree | may drop genuine pre-reset edits users expect saved | VM probes only (counterfactual not executed) | plausible improvement requiring verification |
| Reverse geocode adoption (F-C02) | any JSON adopted, no deadline | η: HTTP gate + require `continentCode` before the method change + bounded deadline | no silent method flip | fewer auto-fills on flaky provider | VM probe | plausible improvement requiring verification |
| External coordinate admission (R0026) feeding builder/settings | admit before normalize | — | — | — | location-admission tests + seam scenario `admissionSeam` | demonstrated improvement (source/mutation; cross-lane owner C02-C04) |
| Hash vs CONFIG `seed` (NEW-C-01) | two representations | η: drop `seed` from the persisted/settings config, or have the renderer read CONFIG | less redundant state | changes stored record shape (C01 compat) | source only | incomparable / retain |
| Frozen v1 truthfulness (CF07-09) | frozen bytes, served | η: document the limitation in `V1_PRESERVATION.md` (no byte change) | truthful evidence claims | none to runtime | source | plausible improvement requiring verification (owner) |
| Embed size doc (F-C03) | README V1 at 330×534 | η: doc text only | contract coherence | none | source | plausible improvement requiring verification |

Comparison with the original `GDOPL_PROJECTION.md` §"configuration effect matrix":
- Taken: label, time/date and appearance rows.
- Taken conservatively: method/school, units and lp/seed rows stay broad, not narrowed.
- The "distinguish draft/serialized/committed preview" builder direction was taken (R000F).

## 5. Coverage

- **Read fully:**
  - `src/native/config.js`
  - `src/native/builder.html` L60-535 (L1-59 is CSS, sampled by grep)
  - `src/native/index.html` L670-761, L3705-3835, L3900-4189
  - `tests/r000f-reset.cjs`, `tests/r000f-fixture.cjs`
  - `docs/state-contracts/R000F.md`; R0003.md L1-200; R0026.md L1-120
  - the original catalogue entries for N01, N20-22, C01, C05-07, C15-23, CF05/07/08/09, XF01 and the GDOPL section
- **Sampled:**
  - v1 function locations
  - `docs/V1_PRESERVATION.md` L1-110
  - README L550-580
  - presets, `_config.yml`, `tools/verify_r0017_pages_payload.py` L60-95
  - the generated `index.html`/`offline.html` symbol locations
- **Not examined:**
  - C02-C04 internals beyond consumers (other lane)
  - installers/C08-C12
  - prayer/weather consumers of `tz`
  - the native evidence files themselves
  - R0026.md beyond L120
  - the original `config-invalidation.cjs` (not re-run)
- **Tests run** (`node` v24.14.0, read-only):
  - `node --test` on `config-effects-state`, `config-effects-mutations`, `builder-preview-publication`, `builder-preview-publication-mutations`, `location-admission-outcomes`, `location-admission-mutations`, `native-appearance-currentness` and `r0003-ownership`: 250/250 pass.
  - Run directly: `r000f-intent` 21/21, `r000f-reset` 9/9, `r0010-preferences` 9/9, `r0011-storage` 18/18, `r0012-clipboard` 11/11, `r0012-effects` 3/3, `r001a-radio` 8/8, `v1_storage` 10/10, plus their mutation suites (all mutants caught).
  - `git status --porcelain` stayed empty.
- **Probes** (`probes/C/`, VM fixture, no network or browser):
  - `reset-close-probe.cjs` (P1-P3) → `reset-close-probe.json`
  - `reset-label-probe.cjs` → `.json`
  - `reverse-error-probe.cjs` → `.json`
  - `reset-close-ref.cjs` against `f71fef6c` failed with `ENOBUFS` (no result)
- No browser was launched.
