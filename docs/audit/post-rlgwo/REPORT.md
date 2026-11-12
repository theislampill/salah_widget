# Post-RLGWO implicit state-machine audit: report

**Status.** Owner-commissioned, documentation-only, repository-wide audit. Nothing in the
application, installers, tests, tools, workflows, generated or vendored files was changed; no
GitHub issue or comment was written. Findings are documentary (see [FINDINGS.md](FINDINGS.md)).
An apparent improvement direction in [GDOPL_ASSESSMENT.md](GDOPL_ASSESSMENT.md) is an analytical
result, not permission to change the repository.

Deliverables: registry [IMPLICIT_STATES.md](../../../IMPLICIT_STATES.md) ·
[CROSSWALK.md](CROSSWALK.md) · [FINDINGS.md](FINDINGS.md) ·
[GDOPL_ASSESSMENT.md](GDOPL_ASSESSMENT.md) · lane working papers in [lanes/](lanes/) ·
probes in [probes/](probes/README.md).

## 1. Methodology

**Lanes.** Six read-only census lanes, each bound by one shared brief (hard boundaries: audit and
document only; read the repository only at the baseline worktree; effect-free probes; no network
to any provider; no GitHub writes), produced a machine census, a historical reconciliation,
documentary findings, GDOPL inputs and a coverage statement for one domain:

| Lane | Domain | Paper |
|---|---|---|
| A | prayer, time and calendar (application core) | [A-prayer-time.md](lanes/A-prayer-time.md) |
| B | weather, radar, location/geocoding and their request ownership | [B-weather-location.md](lanes/B-weather-location.md) |
| C | configuration, persistence, builder, settings UI, frozen `v1/` | [C-config-builder.md](lanes/C-config-builder.md) |
| D | sky, cloud, star and optical rendering; native sky workers | [D-sky-rendering.md](lanes/D-sky-rendering.md) |
| E | Moon pipeline | [E-moon.md](lanes/E-moon.md) |
| F | installers, build and generation, deployment and qualification workflows; baseline inventory | [F-installers-build-workflows.md](lanes/F-installers-build-workflows.md), [F-baseline-inventory.md](lanes/F-baseline-inventory.md) |
| G | independent second omission pass (after the six lanes) | [G-omission-pass.md](lanes/G-omission-pass.md) |

**Integration and verification.** The integrator (the only writer) treated every lane output as
model output. For each finding carried as *demonstrated* and each *resolved and independently
verified* disposition, the cited `file:line` was re-opened at the baseline and compared with the
claim; cited tests were checked to exist and to contain the asserted case. The integrator also
re-ran every committed probe (A, B, C, D with a sanitised path, E, G), the full Node suite, the
seven red instruments at ten commits, `tools/verify_v1.py`, the lane F tree classifier, the Pages
payload estimate and a `gh` spot-check of the work-order inventory. Duplicates across lanes were
merged into one registry entry and one finding; contradictions are resolved in §8.

**What "demonstrated" means here.** Traced end to end in source at the baseline *and* reproduced
by an effect-free probe, an existing test or a recorded native observation. It is never a claim
of observed production behaviour: no browser and no native host were run in this audit. Where
the dependency is demonstrated but the trigger is not (PRA-F-01), both are stated. Two sub-labels
mark demonstrations that are not product observations: *injected fault* (PRA-F-01: a failure was
forced) and *model-parameterised* (PRA-F-03 poll timing, PRA-F-10 worker durations: the probe uses
chosen parameters, not measurements).

**IMPLEMENTAUDIT discipline.** Facts, hypotheses and unknowns are kept in separate lists in every
registry entry; evidence comes before claims; an issue closure, a document assertion or a passing
test is not taken as proof of a transition; every counted status names its evidence; a
counterfactual is never reported as an observed result.

## 2. Audited identity

| Item | Value |
|---|---|
| Baseline | main `363c3e536c8004935ef80230e43f7712e339e3a5`, tree `647b7159a60ceb7dc650563890a5a5a63af14319` (worktree verified clean at that commit) |
| Historical reference | original audit at `f71fef6ccf7e4efcb57b5a26688d2360461a3253`; archived at [`docs/state-contracts/evidence/R0017/original/ORIGINAL_STATE_MACHINE_AUDIT.zip`](../../state-contracts/evidence/R0017/original/ORIGINAL_STATE_MACHINE_AUDIT.zip), SHA256 `b4efa82003474f8ff3ec052aba4c98a5e94f9d9db98c6c0a755dacbc35dbffb8` (verified) |
| Pages | legacy build from `main` `/`; latest build commit `363c3e53`, status `built` (integrator `gh api …/pages/builds/latest`) |
| Public readback | lane F: served `index.html`, `offline.html`, `install.sh`, `install.ps1` equal the baseline tree (not repeated by the integrator) |
| Authored/generated parity | lane A: 40 audited symbols identical between `src/native/index.html` and root `index.html` (re-run); lane C: root `config.js`/`builder.html` byte-identical to `src/native/*`; build-twice result in §12 |

Tree classification at the baseline (lane F rules, [probes/F/classify.py](probes/F/classify.py),
re-run by the integrator with identical output): 16,996 files, 2.211 GB.

| Class | Files | Bytes | Share | At `f71fef6c` |
|---|---|---|---|---|
| Retained historical evidence (`docs/rlgwo-execution`, `docs/state-contracts/evidence`, `docs/real-sky/evidence`, `docs/moon/evidence`, archives, `plans/`) | 16,119 | 1,878.8 MB | 85.0 % | 13,454 / 1,745.3 MB |
| Generated output | 117 | 165.4 MB | 7.5 % | 117 / 165.3 MB |
| Vendored or data | 195 | 157.0 MB | 7.1 % | 195 / 157.0 MB |
| Tests | 280 | 4.06 MB | 0.18 % | 189 / 2.04 MB |
| Tooling (`tools/**`, `.github/**`) | 185 | 2.65 MB | 0.12 % | 91 / 0.79 MB |
| Authored source and docs | 95 | 2.44 MB | 0.11 % | 71 / 1.43 MB |
| Frozen v1 | 5 | 0.29 MB | 0.01 % | 5 / 0.29 MB |

Workflows: 1 file at `f71fef6c`, 32 at the baseline (lane F: 36 registered in Actions, three no
longer in the tree). **Pages payload is an estimate**, not a measurement: the sum of git blob
sizes minus the single `_config.yml` exclusion and dot/underscore paths gives 0.898 GB at
`06772824` (PR 62), 1.771 GB at `f71fef6c`, 1.910 GB at the baseline (re-derived by the
integrator with [pages_payload_estimate.sh](probes/integrator/pages_payload_estimate.sh); no
`_site` was built).

## 3. Work-order inventory

The work orders are R0001…R0027 in hexadecimal numbering — **39 work orders** (GitHub issues
1–37, 68 and 69), not 27. All 39 are closed as completed. Twelve carry a
`<!-- Rxxxx-FINAL-CERTIFICATE:<sha>:<date> -->` comment and exactly these twelve have a
`docs/state-contracts/` contract; the other 27 carry an older-style closure comment.

Spot-check by the integrator (read-only `gh api` and `git log --first-parent`): fourteen rows
(issues 2, 3, 7, 11, 13, 15, 19, 21, 22, 23, 32, 33, 68, 69) — state, closure date and, for the
twelve certified ones, the certificate comment id and bound SHA all match; the merge commits
`daaada05`, `80e70386`, `18ff1486`, `c431733c`, `f270792f`, `f71fef6c` and the fifteen
first-parent merges `eebba178`…`363c3e53` were confirmed on main's first-parent history (39
first-parent merges in total).

Lane F inventory (PR numbers written without `#`):

Certificate column: **FINAL** means a comment carrying a `<!-- Rxxxx-FINAL-CERTIFICATE:<sha>:<date> -->` marker (comment id shown, with the bound sha). **Closure** means an earlier-style closure comment (id shown) and no FINAL marker. The `gh ... select(test("CERTIFICATE|certificate"))` query also matches the 2026-10-09 "remaining-work specification" comments, so the matches were classified by marker.

| RLGWO | Issue | Closed (UTC) | Certificate / closure comment | Main merge(s) that carried it (first-parent) | State contract |
|---|---|---|---|---|---|
| R0001 | 1 | 2026-10-09 | Closure 6073040128 ("RLGWO closure proof") | PR 42 `18ff1486` (evidence commit `9cd9dfa3` is on side branch `codex/rlgwo-closure-audit-20261008`, not on main) | none |
| R0002 | 2 | 2026-10-14 | Closure 6163956116 (`CLOSE-R0002:daaada05`) | PR 57 `daaada05` | none |
| R0003 | 3 | 2026-11-11 | FINAL 6805636415 (`a4766a1b`); earlier CLOSE 6182373378 | PR 79 `a4766a1b` | R0003.md |
| R0004 | 4 | 2026-10-14 | Closure 6165919700 | PR 58 `c431733c` | none |
| R0005 | 5 | 2026-10-09 | Closure 6073058182 | PR 42 `18ff1486` | none |
| R0006 | 6 | 2026-10-14 | Closure 6168140633 | PR 59 `7827099d` (docs PR 51 `ec6e6282`, a direct first-parent commit) | none |
| R0007 | 7 | 2026-11-11 | FINAL 6787290418 (`dbf3370f`); earlier CLOSE 6162239043 | PR 56 `9d1bffe0`, PR 73 `dbf3370f` | R0007.md |
| R0008 | 8 | 2026-10-12 | Closure 6125639418 (`qualified-delivery:419301cb`, side branch) | Cites PR 46 `80e70386` and PR 48 `ec76c7e3`. Exact code carrier not determined | none |
| R0009 | 9 | 2026-10-09 | Closure 6073043445 | PR 42 `18ff1486` | none |
| R000A | 10 | 2026-10-09 | Closure 6073045468 | PR 42 `18ff1486` | none |
| R000B | 11 | 2026-11-11 | FINAL 6788969371 (`da126880`); CLOSE 6178041776 / 6178186713 / 6178296345 | PR 61 `763a460e`, PR 72 `da126880` (docs PR 53 `4e786ff5`) | R000B.md (+ ACCEPTANCE / CONTINUE / IMPLEMENTATION_PLAN / INTEGRATION) |
| R000C | 12 | 2026-10-14 | Closure 6172238574 | PR 60 `16658749` | none |
| R000D | 13 | 2026-11-11 | FINAL 6791942315 (`645b53cc`) + post-closure correction 6792330574; earlier CLOSE 6183596140 | PR 63 `ed5e7afb`, PR 74 `645b53cc` | R000D.md |
| R000E | 14 | 2026-10-09 | Closure 6073043480 | PR 42 `18ff1486` | none |
| R000F | 15 | 2026-11-11 | FINAL 6806041365 (`32f97b06`) | PR 80 `32f97b06` | R000F.md |
| R0010 | 16 | 2026-10-12 | Closure 6121872901 | PR 44 `88926dd1` | none |
| R0011 | 17 | 2026-10-12 | Closure 6132405695 (cites side commits `ac902173`, `b24ffa72`) | PR 50 `15367794`, PR 52 `83f3a86f` | none |
| R0012 | 18 | 2026-10-09 | Closure 6073058047 | PR 42 `18ff1486` | none |
| R0013 | 19 | 2026-11-12 | FINAL 6814244464 (`a1072ae1`) | PR 84 `a1072ae1` (PR 75 `ca2099ef` merged into a work-order branch; reached main through PR 84) | R0013.md |
| R0014 | 20 | 2026-10-12 | Closure 6126260975 (PR48 delivery; cites side commits `3bed0f01`, `de508730`) | PR 48 `ec76c7e3` (docs) | none |
| R0015 | 21 | 2026-11-12 | FINAL 6828391831 (`363c3e53`); post-merge evidence 6816287579; reopened after an unintended auto-closure (6816192574) | PR 85 `3b0e6141` (+ docs PR 87 `363c3e53`) | R0015.md + `docs/r0015-artifact-transactions.md` |
| R0016 | 22 | 2026-11-12 | FINAL 6828374683 (`e4dbf91b`) | PR 86 `e4dbf91b` | R0016.md |
| R0017 | 23 | 2026-11-11 | FINAL 6785616297 (`539c1366`); earlier CLOSE 6181111816 / 6181220586; WITHDRAWN 6703510170 | PR 54 `00d8d446` (direct), PR 62 `06772824`, PR 70 `eebba178`, PR 71 `539c1366` | R0017.md |
| R0018 | 24 | 2026-10-15 | Closure 6191194425 | PR 64 `ae24fec4` | none |
| R0019 | 25 | 2026-10-13 | Closure 6143489619 | PR 55 `3c4221c5` | none |
| R001A | 26 | 2026-10-09 | Closure 6073051392 | PR 42 `18ff1486` | none |
| R001B | 27 | 2026-10-12 | Closure 6127444270 | PR 49 `b690bc35` | none |
| R001C | 28 | 2026-10-12 | Closure 6124639912 | PR 45 `0e3a3ad6` | none |
| R001D | 29 | 2026-10-09 | Closure 6073052323 | PR 42 `18ff1486` | none |
| R001E | 30 | 2026-10-09 | Closure 6073045350 | PR 42 `18ff1486` | none |
| R001F | 31 | 2026-10-09 | Closure 6073059811 | PR 42 `18ff1486` | none |
| R0020 | 32 | 2026-10-12 | Closure 6124693557 (`RLGWO-CLOSE:R0020`) | PR 46 `80e70386` | none |
| R0021 | 33 | 2026-11-11 | FINAL 6809435795 (`5279958a`); CLOSE-R0021 6326407465 (`f71fef6c`) | PR 67 `f71fef6c`, PR 81 `294d2d37`, PR 83 `5279958a` | R0021.md |
| R0022 | 34 | 2026-10-16 | Closure 6220885146 | PR 66 `f270792f` | none |
| R0023 | 35 | 2026-10-12 | Closure 6125047409 | PR 47 `ba6d15d6` | none |
| R0024 | 36 | 2026-10-15 | Closure 6201665819 | PR 65 `fc8d1333` | none |
| R0025 | 37 | 2026-10-14 | Closure 6157899631 (cites side commit `9a6124df`) | PR 42 `18ff1486` cited. Exact carrier not determined | none |
| R0026 | 68 | 2026-11-11 | FINAL 6804824819 (`7f2e8d16`) | PR 78 `7f2e8d16` (PR 76 was closed unmerged) | R0026.md |
| R0027 | 69 | 2026-11-12 | FINAL 6810490146 (`546d8828`) | PR 82 `546d8828` | R0027.md |

Summary:
- 39 of 39 issues are closed (completed). 12 carry a FINAL-CERTIFICATE marker: R0003, R0007, R000B, R000D, R000F, R0013, R0015, R0016, R0017, R0021, R0026 and R0027. Exactly these 12 have a `docs/state-contracts/` contract.
- The other 27 carry a closure comment of an older style. Ten of them closed on 2026-10-09 against PR PR 42 with evidence on side branches.
- Main has 39 first-parent merges plus direct commits PR 51–PR 54.
- PRs 38 (37-work-order integration), 43 and 77 remain open.
- The FINAL markers on R0015 and R0016 carry the date "2026-11-13". The comments were created 2026-11-12T15:48Z.

## 4. Architecture overview by domain

- **Prayer, time and calendar** (`ISM-PRAY`, 11 entries). One authored file,
  `src/native/index.html`, owns the clock, timezone authority, request leases, prayer
  acquisition/rollover, next-event selection (explicit since R0007) and calendar. The live `tz`
  has four writers and many readers, including the sky and Moon identities (ISM-PRAY-009).
  A singleton `requestAnimationFrame` loop drives prayer, weather polls, clouds and the sky
  preview on one synchronous path (ISM-PRAY-010).
- **Weather and location** (`ISM-WX`, 12). Explicit request/attempt fences (pre-campaign),
  an elapsed retry record (R000D), a cloud publication receipt (R000B), and admission of external
  coordinates before normalisation (R0026). Radar is diagnostic only.
- **Configuration and builder** (`ISM-CFG`, 11). A frozen effect classifier decides none /
  presentation / broad (R0003); the builder records an issued-preview identity (R000F). Settings
  Reset, dirty state and persistence outcome remain partly implicit. Diagnostic fragment overrides
  (`sim*`, `debugOptic`, `qa`) are read from any URL (ISM-CFG-011, added after the review).
- **Sky** (`ISM-SKY`, 31). The native scene identity and commit, the refined worker sky
  (lifecycle, queue, assets, host, preview) and copied `real-sky/core` caches. R0021 made
  construction custody and retirement explicit; R0027 bounded one spectral cache by a
  digest-guarded build transform.
- **Moon** (`ISM-MOON`, 20). Authored `moon/src/*` runs in a worker with four WASM shards;
  R0021 added replay refusal and construction unwind. Retry has no product owner.
- **Build, deployment, qualification** (`ISM-BLD`, 10). `tools/build_native.py` generates root
  entries and bundles in place; a merge to `main` deploys through the GitHub Pages service with
  no repository-owned gate; qualification lives on work-order branches, in issue certificates and
  in hash-pinned receipts.
- **Frozen v1** (`ISM-V1`, 9) is byte-unchanged and still served.
- **Installers** (`ISM-INST`, 8). The seven existing entries still describe the baseline
  installer bytes; one partial entry was added.

## 5. Current counts and changes of counting method

The registry holds **112 entries** (85 mapping the 83 original machines — C08…C12 map onto seven
installer entries — and 27 new, two of them added after the independent review). Counts by
status value and dimension:

| Status value | Code | Documentation | Implementation | Verification |
|---|---|---|---|---|
| implicit and materially significant | IMS | 47 | 38 | 4 |
| partially explicit | PEX | 42 | 44 | 55 |
| explicitly documented but weakly enforced | DWE | 6 | 0 | 0 |
| explicitly enforced but insufficiently verified | EEV | 0 | 18 | 13 |
| explicit, enforced and independently verified | EIV | 17 | 0 | 12 |
| historically problematic but demonstrably resolved | HRS | 0 | 11 | 10 |
| unknown or insufficient evidence | UNK | 0 | 1 | 18 |
| **Total** | | 112 | 112 | 112 |

| Domain | Entries | of which new |
|---|---|---|
| Prayer, time and calendar (`ISM-PRAY`) | 11 | 3 |
| Weather, radar and location acquisition (`ISM-WX`) | 12 | 6 |
| Configuration, settings and builder (`ISM-CFG`) | 11 | 3 |
| Sky, cloud, star and optical rendering (`ISM-SKY`) | 31 | 2 |
| Moon pipeline (`ISM-MOON`) | 20 | 5 |
| Build, deployment and qualification (`ISM-BLD`) | 10 | 7 |
| Frozen v1 compatibility snapshot (`ISM-V1`) | 9 | 0 |
| Installer workflows (`ISM-INST`) | 8 | 1 |
| **Total** | 112 | 27 |

For the 85 entries that map original machines, the implementation dimension reads IMS 25, PEX 37,
EEV 15, HRS 8 (installer entries included). The original audit reported 46 implicit / 31
partly explicit / 6 explicit on a single axis. These numbers are **not comparable one to one**:

- the original used one implementation class per machine; this audit uses three dimensions and a
  seven-value vocabulary that separates documentation from enforcement and from verification;
- C08…C12 (five machines) are represented by seven installer entries whose hardening statuses
  were mapped to the vocabulary, not re-derived;
- 27 machines were added (new mechanisms introduced by the campaign, such as the cloud receipt
  and the retry record, plus build/qualification and installer-delivery machines the original
  scoped out), and several lane entries were merged (NEW-A-02 + NEW-B-01; NEW-B-02 + NEW-D-02;
  NEW-B-06 + NEW-D-01; NEW-D-04 + NEW-E-05; N19 from lanes A, D and E; N21 from lanes B and C);
- "HRS" (historically problematic but demonstrably resolved) did not exist in the original
  vocabulary; 11 entries carry it on implementation and 10 on verification;
- after the review, verification statuses that had been asserted without a named test were
  lowered to "unknown or insufficient evidence" (18 entries now carry UNK on verification).

Crosswalk dispositions for the 83 original machines: resolved and independently verified 7,
implemented but not fully verified 38, partly resolved 11, still implicit or vulnerable 25,
superseded 1, no longer applicable 1. Original findings: 13 resolved and independently verified,
2 partly resolved, 3 still implicit (frozen v1). Original hypotheses: 3 still implicit
([CROSSWALK.md](CROSSWALK.md)).

<a id="registered-instruments-and-their-history"></a>
## 6. Registered instruments and their history

The integrator ran each red instrument read-only at the baseline and at nine historical
first-parent commits, each in a scratch extraction with `GIT_DIR` pointing at the repository
([date_instruments.sh](probes/integrator/date_instruments.sh),
[results](probes/integrator/instrument_results.txt)). None writes into the tree (`git status`
clean afterwards).

| Instrument | Baseline | At `f71fef6c` | Cause and date |
|---|---|---|---|
| `tests/r0001-date-sinks.cjs` | 12 pass / 1 fail | all 13 fail ("Expected exactly one native inline runtime") | green at `eebba178` (R0017 extraction rebound) through `dbf3370f`; **red again from the R000B merge `da126880`**: the no-model branch calls `withdrawWeatherEffects` → `paintLunarOptic` → `el.style.getPropertyValue`, which the harness DOM stub lacks |
| `tests/r0009-date-selection.cjs` | 21 / 1 | aborts (same assertion) | same as r0001 |
| `tests/r0019-date-disclosure.cjs` | 15 / 1 | aborts (same assertion) | same as r0001 |
| `tests/r0021-reveal.cjs` | 17 / 1 ("moon PBR shader and embedded payloads retain exact accepted bytes") | 16 / 2 (same case plus a 64-turn settle failure fixed by R0017) | the byte-pin failure predates `f71fef6c` and is identical at every commit tested; origin before the original audit not isolated |
| `tests/r0022-baseline-balance.cjs` | 30 / 7 | 31 / 6 | six failures predate `f71fef6c`; **"London shallow night actual solar path/horizon/marker geometry matches baseline" became red at the R0007 merge `dbf3370f`** (cause inside that merge not isolated). Lanes D and E reported "9/10"; corrected |
| `tests/r0022-lunar-consumers.cjs` | 24 / 2 (star-wash cases against the generated stub) | 24 / 2 | identical; predates. Lane D reported "9/10"; corrected (lane E's 24/2 is right) |
| `tests/rlgwo-docs-contract.cjs` | 64 cases / 50 pass / 14 fail | 50 / 14, identical failing set | identical failing set at every commit tested; the instrument arrived via `3cf6ce2f` (2026-10-05, an ancestor of `f71fef6c`); ten "docs composed" cases expect text from docs commits `bdc806f0`/`89b29c47`, which are not on main |

Full suite: `node --test tests/*.test.cjs tests/*.test.mjs` = 959 tests / 955 pass / 0 fail /
4 todo at the baseline (integrator run), matching lane F and the R0013 certificate.

<a id="second-omission-pass"></a>
## 7. Second omission pass

An independent second pass ([G-omission-pass.md](lanes/G-omission-pass.md)) read only the lanes'
machine lists and registry headings, ran nine search strategies on the source, and only then
compared against the lane findings. It reported seven omissions and two first-pass entry gaps,
none an entirely new machine. Each claim was verified by the integrator against the source; both
G probes were re-run ([probes/G/](probes/README.md)).

| ID | Type | Name | Materiality | Evidence class after verification | Incorporated in |
|---|---|---|---|---|---|
| OM-01 | (c) coupling | Provider timezone adoption re-keys the sky/Moon scene | medium | demonstrated (source: identity L2219, paint L3246, `finishInitialSkyDocument` L3827 before `loadPrayerData` L3846; probe `tz-identity-probe`); visual effect unobserved | ISM-PRAY-009, ISM-SKY-001, ISM-MOON-002, ISM-MOON-005; PRA-F-08; GDOPL I-3 |
| OM-02 | (c) coupling | `tz` is parse-only: the builder never emits it | low-medium | demonstrated (`config.js` L182–206 contain no `tz`; probe: hash `lat=24.47&lon=39.61&label=Madinah&method=4&school=0`, hint `America/New_York`) | ISM-CFG-002, ISM-CFG-007, ISM-PRAY-009; PRA-F-08 |
| OM-03 | (b) of C01/N04/N08/N22 | Per-location cache namespaces never evicted; survive Reset | low-medium | demonstrated for lifecycle (only `removeItem` calls are `config.js` L215 and L247); speculative for quota coupling | ISM-CFG-002, ISM-WX-001; PRA-F-17 |
| OM-04 | (b) of N22/N20 | `source:"localStorage"` survives a successful `clearLocal` | low | demonstrated (source trace S:4038, S:3966) | ISM-CFG-003, ISM-CFG-004, ISM-WX-007; PRA-F-04 |
| OM-05 | (b) of C02/NEW-D-05 | Diagnostic acquisition flags boot-only and sticky | low | demonstrated (S:3794–3796, S:3586) | ISM-SKY-031, ISM-CFG-004, ISM-WX-010; PRA-F-15 |
| OM-06 | (c) extends NEW-C-02 | 325×530 geometry duplicated as literals across renderer modules | low | demonstrated as observation (source) | ISM-CFG-010; PRA-F-37 |
| OM-07 | (c) R14 ↔ R01/R15 | First paint re-parses the fragment with diverging semantics | low | demonstrated for the blank camera parameter (`native-first-paint.mjs` ~L15 `Number(…)` vs `native-host-hooks.js` L24 blank → `NaN`); impact speculative | ISM-SKY-019; PRA-F-37 |

First-pass entry gaps, both confirmed and fixed in the registry: NEW-A-03's reader list omitted
`skySceneIdentity`, `moonGeometryObservation`, `weatherInformation` and the native/Moon captures
(now in ISM-PRAY-009); N13 did not record timezone adoption as a scene-reset trigger (now a
transition row in ISM-SKY-001).

Search strategies that found nothing new (as the pass reported): (2) listener/timer/rAF/fetch
pairing; (4) caches and memos beyond OM-03; (5) time-dependent decisions; (6) worker
init/teardown and error-as-success; (8) installation/publication. Strategies not completed: (7)
installer version/digest constants (repository URLs only compared); (8) Pages state against the
live site (no network); (4) `vendor/real-sky` and `real-sky/core/src/**` internals beyond grep.

<a id="integrator-verification-corrections-and-downgrades"></a>
## 8. Integrator verification, corrections and downgrades

Confirmed at `file:line` (and re-run where a probe exists): A-F01/P1, A-F02/P2, A-F03 (with
commit dating), A-F04/P5, P3, P4, parity; BF01, BF02, BF03, BF04 consumers; F-C01, F-C02, F-C03,
F-C04, F-C05; D-F01 (probe), D-F02, D-F03, D-F04, D-F05, D-F06; EF-E01 (probe), EF-E02, EF-E03
trace, EF-E06; FND-F-01 estimate, FND-F-02 census, FND-F-03 lines, FND-F-04 write order,
FND-F-08, FND-F-09; OM-01…OM-07. Every *resolved and independently verified* row in the crosswalk
names a test that exists and contains the cited case (`hardcoded-fajr` mutant, construction
ownership, retry-clock RED counts in `R000D.md` L127–128, `config-effects` RED count in
`R0003.md` L194, installer cases by name).

Corrections and downgrades:

- **ISM-PRAY-005 (N06)** lane A "resolved and independently verified" → *implemented but not
  fully verified* at machine level: the final hosted Firefox run concluded FAILURE/PARTIAL and
  native acceptance rests on cross-run reuse. NF01 itself stays resolved and independently
  verified.
- **ISM-MOON-012 (R28)** lane E "resolved and independently verified" → *implemented but not
  fully verified*: unchanged since `f71fef6c`, unit evidence only, no independent review cited.
- **ISM-SKY-008 (R03)** lane D "resolved and independently verified" → *implemented but not
  fully verified*: the loader lines are unchanged; R0021's verification addressed the adjoining
  reset (R04) and construction custody (R10).
- **N19** lanes A ("partly resolved") and D ("still implicit") → *still implicit or vulnerable*:
  the cadence fix lives in the retry record (ISM-WX-003), not the loop.
- **N21** lanes B ("implemented but not fully verified") and C ("partly resolved") → *partly
  resolved* (PRA-F-04 is demonstrated).
- **EF-E01 / D-F03 / A-F06 / NH02** (demonstrated / plausible / speculative in three lanes) →
  one finding, PRA-F-01: dependency demonstrated (probe re-run), trigger speculative.
- **Instrument counts**: `r0022-lunar-consumers` is 24/2 and `r0022-baseline-balance` 30/7 at
  the baseline (lane D reported "9/10" for both); one baseline-balance failure dates from the
  R0007 merge, the others predate the original audit.
- **A-F03 framing**: R0017's ES17-07 claim of healthy date-harness passes was true when made;
  R000B later regressed them (`da126880`).
- **Line references**: `tools/native_star_bootstrap.py` asserts are at L14, L18, L26 (lane F:
  L16/L21/L28); `R0015.md` "wholeContractComplete remains false" is at L221, L335 and L450 (lane F:
  L449).
- **FND-F-01** reported strictly as an estimate with its method; GitHub's size-limit enforcement
  not verified.
- **FND-F-04/FND-F-03 probes** (build failure injection, `-O`) were lane F runs in a disposable
  copy and were not repeated; only the code structure was re-confirmed.
- **Probe D** embedded an absolute local path; the committed copy takes the repository root as
  an argument and was re-run with identical results.
- **Review corrections (second commit):** ISM-MOON-013 / R29 lowered from *resolved and
  independently verified* to *implemented but not fully verified* (no independent review covers
  the projection-cache protocol; the reason text contradicted the label); PRA-F-10 scoped to
  `ADVANCING`/`_clockPreview` modes; line references corrected (README L570; S:3880; S:2727;
  `wxAt` S:1556, `syncWeather` S:1573); PRA-F-03 linked to the R000B certificate that already
  recorded the quarter-hour gap; carried-forward entries marked and their verification status
  tied to named test files or lowered to UNK (ISM-SKY-007, 012, 013, 014, 025, 026, 027, 029 and
  ISM-V1-002…009 now UNK); registry enriched from the lane papers; ISM-CFG-011, ISM-PRAY-011 and
  PRA-F-38 added; GDOPL O-4 split so that only the committed-bytes growth is "demonstrated".
- **Lane F FND-F-11** omissions: release metadata/asset selection added as partial entry
  ISM-INST-008; installer-bytes delivery folded into ISM-BLD-006; Bash XPI reuse stays inside
  ISM-INST-006; qualification workflows are ISM-BLD-008.

## 9. Architectural and efficiency observations (source-evidenced only)

No performance was measured; nothing below is a performance claim.

- One synchronous loop and one `render()` carry prayer publication and optional Moon/sky work;
  the refined host contains its own exceptions, the native loop does not (PRA-F-01).
- The live timezone is a multi-writer global whose writes re-key formatter caches, explicit
  clocks and the sky/Moon scene identities (PRA-F-02, PRA-F-08, PRA-F-14).
- The campaign added several currency representations for weather — the decision cache, the
  cloud publication receipt, the effects receipt, the retry record and the refined-sky identity —
  without a single map of which receipt governs which consumer; the refined identity includes
  weather fields its job never reads, and in `timeScale`/clock-preview modes it churns every
  simulated second (PRA-F-10).
- Diagnostics are not pure reads in three places (PRA-F-15).
- Generation is in-place and unstaged; parity relies on executor discipline and there is no gate
  on main (PRA-F-09, PRA-F-19).
- Retained evidence is 85 % of the tree and dominates the deployed payload estimate (PRA-F-07);
  stale hash pins become permanent known failures (PRA-F-06).
- The installer PowerShell script grew from 614 to 1,741 lines and the workflows from 1 to 32
  while removing CF01–CF03 (demonstrated improvement; verification burden noted).

## 10. Remaining risks

Ordering rule: a finding with a demonstrated natural trigger and a hard-constraint consequence
ranks above a conditional structural violation whose trigger has not been found; within each
group, severity decides.

Demonstrated with a natural or ordinary trigger: PRA-F-02 (an invalid hint zone makes prayer
permanently unavailable), PRA-F-03 (quarter-hour cloud withdrawal; previously recorded by the
R000B certificate), PRA-F-04 (Reset lost on a dirty close), PRA-F-05 (method flip from a
reverse-geocode error body), PRA-F-08 (redundant scene teardown on non-default-zone boots),
PRA-F-06 (evidence masking by red instruments), PRA-F-07 (committed payload growth; built size
unmeasured), PRA-F-09 (no gate on main).

Conditional structural violation of a hard constraint: PRA-F-01 — prayer publication depends on
the optional Moon runtime not throwing; the propagation is demonstrated with an injected fault and
no natural trigger was found. It is listed first in FINDINGS.md for its severity if triggered, not
because it has been observed.

See [FINDINGS.md](FINDINGS.md) for all 38.

## 11. Coverage limits and unknowns

- **No browser, no native host, no CI run** in this audit; all runtime statements come from
  source, repository VM harnesses or retained native records produced by others. Visual effects
  (cloud snap, scene re-pending, star motion, Moon tint) were not observed.
- **No provider contacted** (prayer, weather, radar, geocoding, location); provider cadences and
  error-body shapes are unknown.
- **Sampled, not read fully** (per lane coverage statements): `atmosphere()` beyond lunar lines;
  `native-star-preview.mjs`, `native-cloud-transfer.mjs`, `native-encoding.mjs`, most of
  `real-sky/core/src/*` and all of `vendor/real-sky`; `surface_v5.mjs`, kernel numerics;
  `tools/qa/**`, most of `tools/qualification/**`; `R0016.md` detail, `R0017.md`, `R000B`
  annexes, `R0026.md` beyond the cited ranges; `offline.html` beyond symbol locations; the
  evidence trees under `docs/`.
- **Not re-run by the integrator**: Python native qualification tests (`tests/test_r0007_*.py`),
  `tests/r0025-mutations.cjs` (writes files), PowerShell and Bash installer suites, lane F's build
  failure-injection probes and public byte readback.
- **Probes model cadence**: worker durations (probe D) and poll timing (probe B) are parameters,
  not measurements.
- **Independent review** in the repository's certificates usually means a separate model
  context; it was cited, not re-performed.
- **Work-order inventory**: 14 of 39 rows spot-checked; R0008 and R0025 code carriers were not
  determined by lane F.
- **Field coverage.** In the registry a missing field means *not assessed*, never *none*. After the
  review corrections, over the 104 non-installer entries:

| Field | Before review corrections | After (assessed in this audit) | Carried forward from the original catalogue where the field is otherwise missing |
|---|---|---|---|
| Transitions | 38 / 102 | 65 / 104 | 34 |
| Guards | 55 / 102 | 58 / 104 | — |
| Failure and recovery | 41 / 102 | 46 / 104 | 43 |
| Invariants | 59 / 102 | 61 / 104 | 32 |
| Observed facts | 35 / 102 | 51 / 104 | — |
| Hypotheses | 15 / 102 | 39 / 104 | — |
| Unknowns | 76 / 102 | 79 / 104 | — |

  Guards remain the least covered field; the original catalogue has no guard field to carry forward.
- **Acknowledged omissions.** `offline.html`'s own asset-loading path (inline bundles, relative
  `file-data/` chunks, the `native-data.js` loader) was audited only as a generator output, not as a
  runtime machine. The user-visible status text owner was added as ISM-PRAY-011 after the review.
- The registry's absence of an entry is not a claim that no other implicit machine exists.

## 12. Checks at hand-back

Run by the integrator in the audit worktree after writing the deliverables, and re-run after the review corrections (results below are from the re-run):

| Check | Result |
|---|---|
| Changed paths versus `363c3e53` | only `IMPLICIT_STATES.md`, `AGENTS.md` (3 lines) and files under `docs/audit/post-rlgwo/` |
| `python tools/build_native.py`, run twice | rc 0 both times; no tracked or ignored file changed (generated outputs byte-identical) |
| `python tools/verify_v1.py` | `PASS: frozen V1 payload and anchored manifest` |
| `node --test tests/*.test.cjs tests/*.test.mjs` | 959 tests / 955 pass / 0 fail / 4 todo (same as baseline) |
| `node tests/rlgwo-docs-contract.cjs` | 64 cases / 50 pass / 14 fail; failing-case set identical to the baseline run |
| Relative-link check over all new or changed Markdown (files and anchors) | 771 links, 0 broken |
| Hygiene scan of every added line | no local absolute paths, e-mail addresses, credential patterns or closing keywords next to issue numbers |

<a id="independent-review"></a>
## 13. Independent review

**Reviewer.** A separate model instance with read-only access to the worktree, the scratch inputs
and GitHub; no authoring, committing or merging role. It reviewed commit `f9177173`. Its record
was relayed to the integrator by the coordinator; this section restates it without softening.

**What it re-derived.**
- Probes A, B, C, D, E and G re-run; all reproduced the recorded outputs.
- 15 registry entries sampled at random (seed recorded by the reviewer; not supplied to the
  integrator) and checked against the source.
- Crosswalk identifiers checked against the original catalogue: 83 machines, 18 findings and 3
  hypotheses, each present exactly once.
- Registry, crosswalk and findings counts recounted.
- 14 work-order issues checked.
- Instruments re-run at the baseline: `r0001` 12/1, `r0009` 21/1, `r0019` 15/1, `r0021` 17/1,
  `r0022-baseline-balance` 30/7, `r0022-lunar-consumers` 24/2, `rlgwo-docs-contract` 50/14.

**Verdicts by area.** Scope and hygiene: hold. Counts: hold. Crosswalk totals: hold. Instruments:
hold. Work-order inventory: hold. GDOPL authorization boundary: holds. Overall: publishable after
the required corrections.

**Adverse findings (preserved as reported).**
1. Uneven depth: roughly a third to a half of the registry entries were skeletal. Of 102
   non-installer entries only 38 had transitions, 56 guards, 41 failure/recovery, 36 observed
   facts and 15 hypotheses.
2. Carried-forward statuses were asserted rather than re-derived, and some verification statuses
   named no specific test.
3. PRA-F-10 was overstated: the identity churn occurs only when `syncWeather` substitutes forecast
   values (`timeScale` or clock-preview modes), not in default real-time.
4. PRA-F-01 was mis-ranked: listed as the top remaining risk without saying it is conditional on a
   throw that has no natural trigger.
5. PRA-F-03 was understated: the R000B certificate had already recorded the quarter-hour
   withdrawal on the delivered page as a delivered-behaviour finding for the owner.
6. R29 / ISM-MOON-013 carried "resolved and independently verified" while its own reason said the
   cache protocol was not fully verified.
7. The diagnostic-input override surface (`sim*`, `debugOptic`, `qa`) had no registry entry.
8. "Independent" reviews recorded in the repository were cited, not re-performed.
9. Line references were wrong in places (README L570, not L571; `reconcileCloudPublication()` at
   L3880, not L3881).

**Corrections made in response** (commit {{CORR_COMMIT}}):
- PRA-F-10 scoped to `ADVANCING`/`_clockPreview`; evidence class restated as "mechanism
  demonstrated; real worker durations unmeasured".
- R29 / ISM-MOON-013 lowered to *implemented but not fully verified*; crosswalk re-totalled (7 / 38 /
  11 / 25 / 1 / 1) and every dependent count updated.
- §10 reordered by an explicit rule; PRA-F-01 described as a conditional structural violation.
- Registry enriched from the lane papers (transitions 38 → 65 assessed, observed facts 35 → 51,
  hypotheses 15 → 39 of 104 non-installer entries); each original-mapped entry now carries the
  original catalogue's contract in a separate labelled block; carried-forward entries say so
  explicitly; verification statuses without a named test lowered to UNK; "missing field means not
  assessed" stated in the registry preamble and §11 with the coverage table.
- Line references corrected and the other cited lines of the top ten findings re-checked.
- ISM-CFG-011 (diagnostic overrides) and ISM-PRAY-011 (status-text owner) added; PRA-F-38 added;
  `offline.html` asset loading recorded as an acknowledged omission.
- PRA-F-03 linked to the R000B certificate; sub-labels *injected fault* and *model-parameterised*
  added; per-probe reproducibility notes added; GDOPL O-4 split so that only the committed-bytes
  growth is "demonstrated".
- Item 8 is unchanged in substance: independent reviews recorded in the repository remain cited,
  not re-performed, and are labelled as such (§11).

**What the reviewer could not verify.** The whole registry beyond its sample; runtime differences
between `index.html` and `offline.html`; lane F's build failure-injection probes; the Python and
installer suites; any browser, native or provider behaviour.
