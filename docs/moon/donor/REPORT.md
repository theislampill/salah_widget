# MB1 final browser Moon integration delivery

## Result

This delivery completes the narrow source patch, safe installer, available final-entry/failure/currentness testing and reproducible packaging for the browser terrain Moon. It builds on the already implemented WebAssembly renderer and CP9 candidate; no new lunar artistic tuning, repository restart or GitHub write was performed.

**Pin:** `1977217cc2ac26fcc436b991aff498d306a0cd26` in `theislampill/salah_widget`, PR39.
**Exact original served runtime:** `9f7146f0735bb5d999bada4680ca15393cf3b9457c66ff6ce32855c54134bb7a` (54 files).

The working directory did not survive intact. Source was recovered losslessly from the complete local offline/worker bundles and supplied CP9 archive, then the exact published 54-file served-runtime hash and relevant Git blob identities were reproduced. This is not a claim to have cloned every PR39 file/history or recovered all its newer test sources. The data and C/WASM physical solver are preserved, not recreated from screenshots or file fragments fetched over GitHub.

## Safe application

`MOON_AUTHORED.patch` is the four-owner text diff. `payload/` contains 26 source/data files: full postimages for those four existing owners and new Moon files. `INSTALL.json` binds 96 predecessor paths (served runtime, native inputs, builder and its vendor dependencies), donor content and 125 generated/runtime postimages.

`--check` is read-only. `--apply` requires the pinned HEAD, a separate unprotected branch, clean tracked/index state, valid preimages and no addition collisions. It builds twice in a disposable copy before writes, requires exact postimages and no unrelated modifications, rechecks receiver drift and uses atomic file replacement with rollback. No checkout/reset, commit, branch creation, fetch, network, compiler or package installation is performed. Concurrent editors are not formally locked out by a filesystem proof; detected late drift is refused, and any concurrent rollback conflict retains the journal/backups for manual adjudication.

All 20 installer tests pass. They include wrong HEAD, protected branch, tracked/staged dirtiness, new-path collisions, tamper, symlink/path/case aliases, failed or nondeterministic builds, unexpected build writes, late receiver edits, rollback, idempotency and preserving unrelated untracked files. The real-content fixture applies the actual 96 production preimages and exact generated results; only its disposable fixture Git commit identity differs from the historical pin. The package's production contract keeps the true pin. Review patch application was independently checked using `git apply --check` and actual text application.

## Final-entry defects corrected

1. Inert embedded asset nodes were removed after initial boot, making same-document retry impossible. They now remain as the document's source payload. No duplicate hidden asset cache is introduced.
2. Malformed numerical surfaces could advance publication state before adoption failed. Surface validation/adoption now precedes acceptance; errors withdraw to native fallback without an uncaught page error.
3. A crashed worker's failed cancel send could prevent cleanup. Withdrawal now survives that send failure.
4. A fully embedded opaque document does not need a relative resource base. Its data path no longer unnecessarily constructs one.
5. Result dimensions and extent must match the requested scene exactly before publication.

These changes are confined to host/protocol handling. The original numerical kernel and source/material/profile parameters are unchanged. Failed reproductions are retained. Two initial test-instrument mistakes (a misnamed surface helper and a synthetic messageerror dispatch that did not invoke the handler in this host) are labelled by their failed logs, not represented as physics defects. Final browser failure testing appends a fault-only message listener to the original worker source and causes an actual worker exception; numerical function bodies remain unchanged.

## Executed checks

- Moon component suite: **33 passed**, including real terrain/material decode and a small actual WASM render, cancellation, shape/identity gates, grey/model boundaries, geometric precision, opacity and cloud-once controls.
- Deterministic builder tests: **2 passed**.
- Installer safety tests: **20 passed**.
- Native unit suite from the retained native baseline: **410 passed, 4 existing TODO**.
- The 97 original archive integration assertions, run in their original path layout against this candidate: **95 passed, 2 retained failures**. The two compare the old PBR bytes and a settings-to-boot source slice now containing the appended Moon host. A separate region-level comparison proves unchanged prayer/clock, weather, clouds and actual settings business logic. No assertion was relaxed. Initial incorrect repository-layout test invocation (22 module-load failures) is also retained and superseded by the correct layout run; it was not a runtime failure.

Six successful final browser runs cover the self-contained entry, normal multi-file fetches, local-script asset transport, missing/truncated/corrupt input rejection, real worker exception/fallback/retry, profile invalidation, successive phase replacement and disposal. Small fault runs deliberately use a 40×40 physical-reference scene; they are not large-render fidelity claims.

The default canonical self-contained case uses the real **540×540** terrain workload at **DPR 3**, not the small test scene. It reached its first fully refined result in **166.78 seconds** including controlled document transport/startup. The four loaded date-dialog interactions completed, with maximum heartbeat gap **38.40 ms** and maximum automation round trip **156.69 ms**. These are one scoped run, not all-platform or CP9's whole stress campaign. Final refinement is expensive; a labelled early terrain preview and the original native fallback preserve usability meanwhile.

The default run and all final quick runs have zero unexpected page errors. Their per-entry hashes match the sealed product. Screenshots use controlled date/prayer/weather and fallback fonts; no QA timetable/date or font binary is inserted in the product. Moon pixels are computed, not pasted photographs.

## Native navigation boundary

Real HTTP and file navigation in this container both return `ERR_BLOCKED_BY_ADMINISTRATOR`. A sandbox-enabled Chromium launch is also unavailable in this container. The executed runs explicitly use controlled document/resource transport and the container-compatible process-sandbox setting, without disabling browser web security or circumventing administrator navigation policy. These results do **not** certify Windows file navigation, a particular production CSP, Firefox/WebKit, live providers, BFCache or arbitrary devices. The supplied runner has an explicit `navigation` mode for the existing Codex environment; it never silently turns a failed navigation into fixture PASS.

The single-file **contents and embedded loading/retry path are executed**, but ordinary file-URL navigation remains an environment-limited receiving check. This distinction is essential, not an additional missing rendering component.

## Frozen physical / product limits

The C/WASM solver, V5 scalar profile, finite Sun/Earth, original metric data and canonical/default policy are preserved. The source's NASA colour is appearance-adjusted, Earth is a grey approximation and high-phase photometry is not independently calibrated. Automatic exact observer ephemerides, finer terrain, universal spatial/temporal/photometric convergence, independent review and existing CP9 release gates remain distinct. This delivery does not repeat or reassign the original 18-scene V5 numerical comparison as newly executed dense validation. Its source-bound earlier results remain predecessor evidence; current small numerical and actual-entry checks are fresh.

No GitHub write or change to PR38/PR39/main occurred. The receiving branch should be a dependent Moon branch from the pinned CP9 source. No old research archive needs to be re-read or copied into production. See `CODEX_START_HERE.md` for bounded apply/test/review instructions.
