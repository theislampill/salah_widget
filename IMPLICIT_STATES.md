# Implicit state machines: repository-wide registry

## Purpose and scope

This registry records consequential state machines that the installers implement
implicitly, through variables, files, records, traps and control flow, rather than
through a declared model. It exists so that a change to staging, artifact admission,
cleanup, preview or manual hand-off starts from the states, guards and invariants that
the source already relies on.

Repository-wide scope. As of the post-RLGWO implicit state-machine audit, this registry
covers every materially relevant stateful mechanism that the audit's six census lanes and its
independent second omission pass identified in the repository at main
`363c3e536c8004935ef80230e43f7712e339e3a5` (tree `647b7159a60ceb7dc650563890a5a5a63af14319`):
prayer and time, weather and location, configuration and builder, sky rendering, the Moon
pipeline, build/deployment/qualification, the frozen `v1/` snapshot and the installers. The
method, evidence and limits are in the [audit report](docs/audit/post-rlgwo/REPORT.md); the
mapping from the original audit (commit `f71fef6c`) is in the
[crosswalk](docs/audit/post-rlgwo/CROSSWALK.md); documentary findings are in
[FINDINGS.md](docs/audit/post-rlgwo/FINDINGS.md). Absence of an entry is still not a claim that
no other implicit machine exists.

Installer scope (the original entries ISM-INST-001…007): these entries cover the installer workflows examined for R0015 (issue 21:
artifact transactions and staging trust) and R0016 (issue 22: dry-run as an offline,
effect-free preview), as of merged main `e4dbf91be91f7539b36297e030f86e2a0e99f54d`
(the PR 86 merge; its tree is identical to the candidate `dfff0f8f`). The installer
blobs are `install.sh` `e2e2640e` (SHA256 `27442c0e…`) and `install.ps1` `28cfdae7`
(SHA256 `07671cb9…`). Absence of
an entry is not a claim that no other implicit machine exists.

Authority rule. The state model describes allowed transitions. Execution records
establish what happened. Owner authorization determines what may be done. None of these
substitutes for the others. This document grants no execution authority and proves no
runtime behaviour.

Per-work-order contracts stay authoritative for their own obligations. This registry
links to them and does not restate them:
[R0013](docs/state-contracts/R0013.md),
[R0015](docs/state-contracts/R0015.md),
[R0015 Windows transactions](docs/r0015-artifact-transactions.md),
[R0016](docs/state-contracts/R0016.md),
[installer coordination](docs/state-contracts/installer-coordination/PLAN.md).

### Adding or changing an entry

- Give each machine a stable ID (`ISM-INST-NNN`). Never renumber or reuse an ID. Mark a
  retired entry as retired.
- Repository-wide IDs use a domain prefix: `ISM-PRAY-NNN`, `ISM-WX-NNN`, `ISM-CFG-NNN`,
  `ISM-SKY-NNN`, `ISM-MOON-NNN`, `ISM-BLD-NNN` (build, deployment, qualification),
  `ISM-V1-NNN` (frozen v1) and `ISM-INST-NNN`. The same never-renumber rule applies.
- Repository-wide entries record status on three separate dimensions with the vocabulary in
  [Status vocabulary](#status-vocabulary-for-repository-wide-entries). The installer entries keep
  their hardening-status vocabulary below; their index codes are a reading of it, not a
  replacement.
- Fill each field only as far as evidence supports. Omit a field rather than guess.
- Keep the three lists separate. **Observed facts** come from source reading or a cited
  record. **Hypotheses** are plausible but untraced or unexecuted. **Unknowns** are open
  questions.
- A hardening status is one of `documented`, `enforced in code`,
  `enforced and covered by tests`, `independently verified` or `unresolved`. Each status
  claim names its evidence (test file, mutant, run id or review).
- Hosted run ids are cited as their ledgers describe them. Where a run executed earlier
  installer bytes, the entry says so.
- Add a line to [Open findings](#open-findings) for anything material.

### Merged and dropped discovery targets (installer entries)

- Interruption and recovery is not a separate machine. It is a transition class of
  ISM-INST-004 (staging attempt) and ISM-INST-005 (compiler context).
- Transactional replacement is folded into ISM-INST-006. Every attempt publishes into a
  fresh root. No code path replaces an earlier bundle in place.
- Install-source selection is split. Option validation is in ISM-INST-001, and the
  per-target `ask` resolution is in ISM-INST-007.
- Retained-bundle lifetime is in ISM-INST-007. Root creation and identity are in
  ISM-INST-004.

## Status vocabulary for repository-wide entries

Each entry carries three status cells: **Documentation (D)**, **Implementation (I)** and
**Verification (V)**. A cell takes one value from the fixed vocabulary below, read for that
dimension. The cells are never collapsed into a PASS or FAIL.

| Code | Value | D: what is written | I: what the code enforces | V: what the evidence shows |
|---|---|---|---|---|
| IMS | implicit and materially significant | only inline comments, or nothing, for a consequential decision | state carried in variables and control flow; transitions not declared | no test exercises the consequential transitions |
| PEX | partially explicit | issue body, certificate, design document or a contract covering part of the machine | some states or guards are declared or centralised, others implicit | unit tests cover part of the transitions |
| DWE | explicitly documented but weakly enforced | a contract, AGENTS rule or design text exists, but the code or another document contradicts or only partly honours it | (not used) | (not used) |
| EEV | explicitly enforced but insufficiently verified | (not used) | explicit, centralised guards enforce the documented transitions | unit tests plus mutation/negative controls or native evidence, but not enough for the claim |
| EIV | explicit, enforced and independently verified | a state contract (or this registry) that matches the code | (installer entries only: see their hardening status) | mutation/negative controls plus native evidence or independent review, within the recorded scope |
| HRS | historically problematic but demonstrably resolved | (not used) | an original-audit defect on this machine is removed, shown by before/after source | before/after test or probe evidence shows the defect resolved |
| UNK | unknown or insufficient evidence | not examined | not examined | not examined or not re-run |

"Independent review" in this repository usually means a separate model context recorded in a
certificate or contract; it is cited as such and not upgraded to human review.

### Current counts

Entries by status value and dimension (all 110 entries, installer entries included):

| Status value | Code | Documentation | Implementation | Verification |
|---|---|---|---|---|
| implicit and materially significant | IMS | 46 | 37 | 12 |
| partially explicit | PEX | 41 | 43 | 61 |
| explicitly documented but weakly enforced | DWE | 6 | 0 | 0 |
| explicitly enforced but insufficiently verified | EEV | 0 | 18 | 12 |
| explicit, enforced and independently verified | EIV | 17 | 0 | 12 |
| historically problematic but demonstrably resolved | HRS | 0 | 11 | 11 |
| unknown or insufficient evidence | UNK | 0 | 1 | 2 |
| **Total** | | 110 | 110 | 110 |

| Domain | Entries | of which new |
|---|---|---|
| Prayer, time and calendar (`ISM-PRAY`) | 10 | 2 |
| Weather, radar and location acquisition (`ISM-WX`) | 12 | 6 |
| Configuration, settings and builder (`ISM-CFG`) | 10 | 2 |
| Sky, cloud, star and optical rendering (`ISM-SKY`) | 31 | 2 |
| Moon pipeline (`ISM-MOON`) | 20 | 5 |
| Build, deployment and qualification (`ISM-BLD`) | 10 | 7 |
| Frozen v1 compatibility snapshot (`ISM-V1`) | 9 | 0 |
| Installer workflows (`ISM-INST`) | 8 | 1 |
| **Total** | 110 | 25 |

## Index of machines

Status columns use the codes defined in [Status vocabulary](#status-vocabulary-for-repository-wide-entries). Historical disposition uses the crosswalk vocabulary of [CROSSWALK.md](docs/audit/post-rlgwo/CROSSWALK.md); `new` marks a machine absent from the original catalogue.

### Prayer, time and calendar (`ISM-PRAY`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-PRAY-001](#ism-pray-001) | Civil/simulation clock, timezone inverse, invalid-scene recovery, diagnostic clock control | N02 | PEX | PEX | PEX | still implicit or vulnerable |
| [ISM-PRAY-002](#ism-pray-002) | Request ownership and bounded attempt leases (prayer, weather, radar slots) | N03 | PEX | EEV | EEV | implemented but not fully verified |
| [ISM-PRAY-003](#ism-pray-003) | Current prayer acquisition, admission/cache and adopted-zone reconciliation | N04 | PEX | PEX | PEX | still implicit or vulnerable |
| [ISM-PRAY-004](#ism-pray-004) | Prayer day rollover, next-day prefetch, cooldown and stale state | N05 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-PRAY-005](#ism-pray-005) | Prayer model, explicit next-event selection, countdown and DOM publication | N06 | EIV | HRS | HRS | implemented but not fully verified |
| [ISM-PRAY-006](#ism-pray-006) | Calendar publication, Hijri provenance/rollover and date disclosure | N07 | PEX | IMS | PEX | implemented but not fully verified |
| [ISM-PRAY-007](#ism-pray-007) | Countdown font readiness, rail sampling and geometry-fit cache | N18 | PEX | IMS | PEX | partly resolved |
| [ISM-PRAY-008](#ism-pray-008) | Optional web-typography activation gate | new | EIV | EEV | EIV | new |
| [ISM-PRAY-009](#ism-pray-009) | Live timezone authority `tz` (multi-writer) and its consumer fan-out | new | IMS | IMS | PEX | new |
| [ISM-PRAY-010](#ism-pray-010) | Singleton render loop, visibility, provider cadence and motion lifecycle | N19 | IMS | IMS | PEX | still implicit or vulnerable |

### Weather, radar and location acquisition (`ISM-WX`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-WX-001](#ism-wx-001) | Weather acquisition, current/hourly records and persistent cache | N08 | PEX | PEX | EIV | partly resolved |
| [ISM-WX-002](#ism-wx-002) | Weather truth/decision, information text and header publication | N09 | PEX | PEX | EIV | implemented but not fully verified |
| [ISM-WX-003](#ism-wx-003) | Weather/radar elapsed retry eligibility | new | EIV | HRS | HRS | new |
| [ISM-WX-004](#ism-wx-004) | Radar diagnostic transport, image lease and expiry | N10 | PEX | PEX | PEX | partly resolved |
| [ISM-WX-005](#ism-wx-005) | Cloud publication authority receipt (weather → cloud consumers) | new | EIV | HRS | HRS | new |
| [ISM-WX-006](#ism-wx-006) | Weather target capture and location provenance | new | PEX | PEX | EEV | new |
| [ISM-WX-007](#ism-wx-007) | Location evidence normalisation and persistence provenance | new | IMS | PEX | PEX | new |
| [ISM-WX-008](#ism-wx-008) | Site elevation dual custody | new | IMS | IMS | IMS | new |
| [ISM-WX-009](#ism-wx-009) | Forecast-track preview substitution, live return and sky-identity churn | new | IMS | IMS | PEX | new |
| [ISM-WX-010](#ism-wx-010) | Coarse location provider cascade and whole-body deadline | C02 | EIV | HRS | HRS | resolved and independently verified |
| [ISM-WX-011](#ism-wx-011) | Forward geocoder aggregate completion | C03 | EIV | HRS | HRS | resolved and independently verified |
| [ISM-WX-012](#ism-wx-012) | Browser location and permission request completion | C04 | PEX | PEX | EEV | implemented but not fully verified |

### Configuration, settings and builder (`ISM-CFG`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-CFG-001](#ism-cfg-001) | Configuration resolution, effect classification, apply generation and boot sequence | N01 | EIV | EEV | EIV | implemented but not fully verified |
| [ISM-CFG-002](#ism-cfg-002) | Configuration persistence and mode resolution | C01 | PEX | PEX | PEX | partly resolved |
| [ISM-CFG-003](#ism-cfg-003) | Settings disclosure, focus, dirty form and close-save | N20 | PEX | PEX | PEX | implemented but not fully verified |
| [ISM-CFG-004](#ism-cfg-004) | Settings place search, GPS, candidate cycling and Reset intent | N21 | DWE | PEX | EEV | partly resolved |
| [ISM-CFG-005](#ism-cfg-005) | Persistence outcome and persistent warning publication | N22 | PEX | EEV | EEV | implemented but not fully verified |
| [ISM-CFG-006](#ism-cfg-006) | Document-hash direct reads parallel to the resolved CONFIG (seed, diagnostics) | new | PEX | IMS | IMS | new |
| [ISM-CFG-007](#ism-cfg-007) | Builder mode, form, serialisation and preview publication | C05 | EIV | HRS | HRS | resolved and independently verified |
| [ISM-CFG-008](#ism-cfg-008) | Builder edit ownership, candidate cycle and automatic fills (reverse geocode) | C06 | PEX | PEX | PEX | partly resolved |
| [ISM-CFG-009](#ism-cfg-009) | Clipboard attempts, fallback and expiring feedback | C07 | PEX | EEV | EEV | implemented but not fully verified |
| [ISM-CFG-010](#ism-cfg-010) | Builder ↔ widget preview handoff and the 325×530 geometry contract | new | DWE | PEX | PEX | new |

### Sky, cloud, star and optical rendering (`ISM-SKY`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-SKY-001](#ism-sky-001) | Sky scene identity, first-document warrant and renderer-surface commit | N13 | PEX | PEX | EIV | implemented but not fully verified |
| [ISM-SKY-002](#ism-sky-002) | Star projection / catalogue contract and held appearance | N14 | DWE | PEX | PEX | still implicit or vulnerable |
| [ISM-SKY-003](#ism-sky-003) | Cloud population, motion integration, coverage and paint cache | N15 | PEX | PEX | PEX | implemented but not fully verified |
| [ISM-SKY-004](#ism-sky-004) | Precipitation population, cloud-origin gating and lightning bucket | N16 | PEX | IMS | PEX | implemented but not fully verified |
| [ISM-SKY-005](#ism-sky-005) | Atmosphere publication, optical fade state and last-consumed diagnostics | N17 | PEX | PEX | PEX | partly resolved |
| [ISM-SKY-006](#ism-sky-006) | Native sky snapshot identity, epoch, freshness and throughput admission | R01 | IMS | EEV | EEV | implemented but not fully verified |
| [ISM-SKY-007](#ism-sky-007) | Latest-only serialised render queue | R02 | IMS | EEV | PEX | implemented but not fully verified |
| [ISM-SKY-008](#ism-sky-008) | Native asset loader generation, timeout, suspension and retry | R03 | PEX | EEV | EIV | implemented but not fully verified |
| [ISM-SKY-009](#ism-sky-009) | Native asset script, inline pack and page-lifecycle ownership | R04 | PEX | PEX | EEV | implemented but not fully verified |
| [ISM-SKY-010](#ism-sky-010) | Reference worker client boot, RPC deadlines and fallback mode | R05 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-SKY-011](#ism-sky-011) | Sky worker boot, engine ownership and transferable raster response | R06 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-012](#ism-sky-012) | Diffuse asset admission, cancellation and content cache | R07 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-SKY-013](#ism-sky-013) | Sky catalogue replacement generation and last-result authority | R08 | IMS | EEV | PEX | implemented but not fully verified |
| [ISM-SKY-014](#ism-sky-014) | Engine binding selection, load keys and declared physical fallback | R09 | PEX | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-015](#ism-sky-015) | Refined sky construction, accepted frame, displayed frame and DOM commit | R10 | PEX | HRS | HRS | resolved and independently verified |
| [ISM-SKY-016](#ism-sky-016) | Solar cloud-mask decode-before-publish transaction | R11 | PEX | PEX | PEX | partly resolved |
| [ISM-SKY-017](#ism-sky-017) | Preview base, pending paint, current display and shared DOM handoff | R12 | PEX | PEX | PEX | partly resolved |
| [ISM-SKY-018](#ism-sky-018) | Asynchronous preview catalogue admission revision | R13 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-019](#ism-sky-019) | Document head background and initial lunar CSS lease (first paint) | R14 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-020](#ism-sky-020) | Native snapshot adapter and single paint-hook installation | R15 | IMS | IMS | PEX | implemented but not fully verified |
| [ISM-SKY-021](#ism-sky-021) | Bounded camera/lunar sampling geometry memoisation | R16 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-022](#ism-sky-022) | Preview raster private-byte custody and lazy fields | R17 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-023](#ism-sky-023) | Exact immutable encoding-table initialisation | R18 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-024](#ism-sky-024) | Spectral selection and B–V fit retention | R31 | EIV | HRS | HRS | resolved and independently verified |
| [ISM-SKY-025](#ism-sky-025) | Bounded legacy photometry spectral memo | R32 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-026](#ism-sky-026) | Atmosphere validation capability and weak coefficient memo | R33 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-027](#ism-sky-027) | Per-physical-model solar sample grid lifetime | R34 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-SKY-028](#ism-sky-028) | Native target-elevation acceptance lease | R35 | IMS | PEX | PEX | still implicit or vulnerable |
| [ISM-SKY-029](#ism-sky-029) | Catalogue-bound diffuse resource capability | R36 | IMS | PEX | PEX | still implicit or vulnerable |
| [ISM-SKY-030](#ism-sky-030) | Page-lifecycle fan-out across sky owners | new | PEX | IMS | EEV | new |
| [ISM-SKY-031](#ism-sky-031) | Diagnostic telemetry state (debugMotion history, qaState) | new | DWE | IMS | PEX | new |

### Moon pipeline (`ISM-MOON`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-MOON-001](#ism-moon-001) | Legacy lunar texture/canvas fallback (dormant generated owner) | N11 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-MOON-002](#ism-moon-002) | Native lunar geometry production and consumption receipts | N12 | PEX | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-003](#ism-moon-003) | Lunar host accepted / pending / waiting-preview / presentation transaction | R19 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-004](#ism-moon-004) | Lunar runtime installation, worker source, bounded retry and deadlines | R20 | PEX | PEX | EEV | partly resolved |
| [ISM-MOON-005](#ism-moon-005) | One-shot initial-head eligibility and irreversible retirement | R21 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-006](#ism-moon-006) | Offline chunk DOM/script transport lease | R22 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-007](#ism-moon-007) | Lunar top worker boot, newest-job pump and cancellation | R23 | IMS | IMS | PEX | still implicit or vulnerable |
| [ISM-MOON-008](#ism-moon-008) | Lunar shard RPC bridge promises and sticky failure | R24 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-009](#ism-moon-009) | Lunar pool row ownership, sparse reuse and join barrier | R25 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-010](#ism-moon-010) | Lunar engine exclusive execution, asset admission and caches | R26 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-011](#ism-moon-011) | Lunar cooperative MessageChannel yield | R27 | IMS | IMS | IMS | still implicit or vulnerable |
| [ISM-MOON-012](#ism-moon-012) | Lunar adaptive refinement and final quality admission | R28 | IMS | EEV | PEX | implemented but not fully verified |
| [ISM-MOON-013](#ism-moon-013) | Lunar detail adoption, projection cache and DOM visibility owner | R29 | PEX | HRS | HRS | resolved and independently verified |
| [ISM-MOON-014](#ism-moon-014) | Admitted initial lunar receiver and canonical render closure | R30 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-MOON-015](#ism-moon-015) | Lunar C/WASM retained kernel state, frame arena and source witness | R37 | IMS | IMS | PEX | implemented but not fully verified |
| [ISM-MOON-016](#ism-moon-016) | Moon wrapper admission, construction unwind and replay refusal | new | EIV | HRS | HRS | new |
| [ISM-MOON-017](#ism-moon-017) | Native Moon reveal gate (`moon-ready` / `mask-on`) | new | PEX | EEV | EEV | new |
| [ISM-MOON-018](#ism-moon-018) | Moon worker asset HTTP acquisition and browser-cache admission | new | PEX | IMS | PEX | new |
| [ISM-MOON-019](#ism-moon-019) | Moon page-lifecycle withdrawal and worker lifetime | new | IMS | PEX | PEX | new |
| [ISM-MOON-020](#ism-moon-020) | Native physical lunar-light eligibility (sky, cloud, star consumers) | new | PEX | PEX | PEX | new |

### Build, deployment and qualification (`ISM-BLD`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-BLD-001](#ism-bld-001) | Native generation output publication sequence | C13 | PEX | PEX | PEX | implemented but not fully verified |
| [ISM-BLD-002](#ism-bld-002) | Moon generation preflight and expansion | C14 | PEX | PEX | PEX | implemented but not fully verified |
| [ISM-BLD-003](#ism-bld-003) | R0017 Pages payload qualification workflow and retained receipt | C24 | PEX | EEV | IMS | no longer applicable |
| [ISM-BLD-004](#ism-bld-004) | Pages deployment from main (a commit to main is a deploy) | new | PEX | IMS | PEX | new |
| [ISM-BLD-005](#ism-bld-005) | RLGWO delivery workflow (campaign governance) | new | PEX | IMS | PEX | new |
| [ISM-BLD-006](#ism-bld-006) | Installer-bytes delivery routes and README pin ↔ docs-receipt coupling | new | PEX | IMS | PEX | new |
| [ISM-BLD-007](#ism-bld-007) | Registered regression suites and the known-failure baseline | new | DWE | IMS | PEX | new |
| [ISM-BLD-008](#ism-bld-008) | Work-order-branch qualification workflows | new | IMS | IMS | UNK | new |
| [ISM-BLD-009](#ism-bld-009) | Evidence receipts bound to source hashes | new | PEX | PEX | PEX | new |
| [ISM-BLD-010](#ism-bld-010) | Frozen v1 verification | new | DWE | EEV | EEV | new |

### Frozen v1 compatibility snapshot (`ISM-V1`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-V1-001](#ism-v1-001) | Frozen v1 one-time root configuration import | C15 | IMS | PEX | PEX | implemented but not fully verified |
| [ISM-V1-002](#ism-v1-002) | Frozen v1 configuration apply and boot without generation ownership | C16 | IMS | IMS | IMS | still implicit or vulnerable |
| [ISM-V1-003](#ism-v1-003) | Frozen v1 prayer cache, retry, tomorrow and rollover | C17 | IMS | PEX | IMS | implemented but not fully verified |
| [ISM-V1-004](#ism-v1-004) | Frozen v1 weather current/forecast acquisition | C18 | IMS | PEX | IMS | implemented but not fully verified |
| [ISM-V1-005](#ism-v1-005) | Frozen v1 radar manifest, tile and freshness acquisition | C19 | IMS | IMS | IMS | still implicit or vulnerable |
| [ISM-V1-006](#ism-v1-006) | Frozen v1 modal editing, lookup, GPS and Reset | C20 | IMS | IMS | IMS | still implicit or vulnerable |
| [ISM-V1-007](#ism-v1-007) | Frozen v1 real/simulated clock anchor compatibility variant | C21 | IMS | PEX | IMS | implemented but not fully verified |
| [ISM-V1-008](#ism-v1-008) | Frozen v1 Moon texture readiness and pending render cache | C22 | IMS | IMS | IMS | still implicit or vulnerable |
| [ISM-V1-009](#ism-v1-009) | Frozen v1 synthetic star catalogue and projection cadence | C23 | IMS | IMS | IMS | still implicit or vulnerable |

### Installer workflows (`ISM-INST`)

| Registry ID | Name | Original ID | Doc | Impl | Verif | Historical disposition |
|---|---|---|---|---|---|---|
| [ISM-INST-001](#ism-inst-001-invocation-options-and-run-mode-preview-effect-boundary) | Invocation options and run mode (preview effect boundary) | C08 (part) | EIV | EEV | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-002](#ism-inst-002-discovery-knowledge-target-eligibility-and-selection) | Discovery knowledge, target eligibility and selection | C08 (part); CF10 | EIV | EEV | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-003](#ism-inst-003-staging-parent-trust-decision) | Staging-parent trust decision | C09 (part) | EIV | EEV | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-004](#ism-inst-004-private-staging-attempt-roots-identity-cleanup-interruption) | Private staging attempt (roots, identity, cleanup, interruption) | C09 (part); C11 (part) | EIV | EEV | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-005](#ism-inst-005-windows-native-helper-compile-and-load) | Windows native helper compile and load | C11 (part) | EIV | EEV | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-006](#ism-inst-006-artifact-admission-and-publication) | Artifact admission and publication | C10; C11 (part); C12 (part); CF01-CF03 | EIV | HRS | HRS | see CROSSWALK (C08–C12) |
| [ISM-INST-007](#ism-inst-007-manual-hand-off-and-retained-bundle) | Manual hand-off and retained bundle | C08 (part); C12 (part) | EIV | PEX | EIV | see CROSSWALK (C08–C12) |
| [ISM-INST-008](#ism-inst-008) | Release metadata and asset selection | new | PEX | UNK | UNK | new |

---

## Prayer, time and calendar (`ISM-PRAY`)

<a id="ism-pray-001"></a>
### ISM-PRAY-001 — Civil/simulation clock, timezone inverse, invalid-scene recovery, diagnostic clock control

Original audit: **N02** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** One epoch for prayer, calendar, sky and Moon; decides live vs frozen vs advancing vs runtime-preview time.
- **Sources.** `src/native/index.html` `partsInTz` ~L935, `zoneDay` ~L971-991, `epochForTzTime` ~L992, `initSim` ~L999, `simNow` ~L1011, `simulationReady` ~L1020-1035, `window.SalahClock.set` ~L3766-3777 (generated `index.html` ~L4540, ~L7199)
- **State dimensions.** clock mode {live-wall, frozen explicit (`TIMESCALE=0`), advancing explicit, runtime preview `_clockPreview`}; anchor `(_simBase,_rafT0,_simTz)`; validity `(_simValid,_simInvalidTz)`; formatter caches; `_zoneDays` (≤4)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | explicit mode, first call or `_simTz!==tz` | — | `initSim()` re-anchors to `simTime` in `tz`, or to `Date.now()` when no `simTime` |
  | gap/fold `simTime` | — | `_simValid=false`, sticky until `tz` changes; 8 layers hidden, "SIM unavailable" |
  | `SalahClock.set({rate,utcMs,live})` | validated | sets mode, anchors `_simTz=tz`, invalidates sky/preview, `maintainPrayerDay`, `render` |
  | `tz` written after a `SalahClock` preview | `_simTz!==tz` | preview `utcMs` replaced by wall now; `_clockPreview` stays true (PRA-F-14) |

- **Guards.** `Intl` formatter construction; gap/fold detection in `epochForTzTime`
- **Actors and ownership.** URL fragment (`simTime`, `timeScale`), `window.SalahClock` (diagnostics, `tools/cp9/*_check.py`), timezone writers (ISM-PRAY-009)
- **Effects.** every consumer's notion of now; deadline clocks use `_RAFNOW` (monotonic)
- **Invariants.** one epoch feeds prayer, calendar, sky and Moon; a gap/fold time is never shifted
- **Failure and recovery.** `partsInTz` silently falls back to the host zone when `Intl` throws (reachable with an invalid `tz`, PRA-F-02)
- **Invalid, duplicate, stale or concurrent risks.** stale preview anchor after zone adoption (PRA-F-14); silent host-zone fallback
- **Status evidence.** D: inline comments, issues 8 and 32 (no state contract) · I: mode flags explicit, re-anchor implicit · V: unit suites above; no negative control for preview survival
- **Work orders.** none after f71fef6c (R0008 issue 8, R0020 issue 32 closed before)
- **Accepted evidence.** r0020-clock 44/44, r0008-timezone 37/37 (lane A run)
- **Tests.** `tests/r0020-clock.cjs`, `tests/r0008-timezone.cjs`, `tests/r0007-countdown.cjs`
- **Observed facts.** Probe A P2 (re-run by the integrator): requested 2026-12-25T03:00Z, observed 2026-09-07T12:00Z after Tokyo adoption, `_clockPreview:true`
- **Hypotheses.** an advancing `timeScale` preview restarting from `simTime` on zone adoption is intended (comment ~L1010)
- **Unknowns.** cross-browser `Intl` historical offsets; cold `zoneDay` cost natively
- **Findings.** [PRA-F-02](docs/audit/post-rlgwo/FINDINGS.md#pra-f-02), [PRA-F-14](docs/audit/post-rlgwo/FINDINGS.md#pra-f-14)

<a id="ism-pray-002"></a>
### ISM-PRAY-002 — Request ownership and bounded attempt leases (prayer, weather, radar slots)

Original audit: **N03** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **PEX / EEV / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Which in-flight operation may mutate prayer, weather or radar state.
- **Sources.** `src/native/index.html` `cacheKey`, `_requestSlots`, `beginRequest` ~L1067-1112 (gen ~L4602), `fetchTimings` ~L1128-1164, `prayerResultEligible` ~L1194-1197
- **State dimensions.** slot per kind {current, prefetch, weather, radar} = null | op; op `{generation, operationId, captured target, attempt}`; attempt `{attemptId, controller, deadlineAt, timer, cancel, expired}`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `beginRequest(kind)` | slot empty | claims slot |
  | attempt completion | op current, attempt identity exact, not expired, `_RAFNOW()<deadline` | eligible to adopt |
  | `beginRuntimeGeneration` | — | slots cleared, attempts aborted |
  | old `finally` | — | cannot release a successor's slot |

- **Guards.** generation, operation id and attempt id equality; 10 s deadline; 3 attempts, 900·n ms backoff
- **Actors and ownership.** `applyConfig` (generation), loaders, loop poll
- **Effects.** adoption or silent rejection of provider results
- **Invariants.** a late result never mutates a successor generation
- **Failure and recovery.** backoff `sleep` is not cancellable but rechecks eligibility (~L1136)
- **Invalid, duplicate, stale or concurrent risks.** none demonstrated
- **Status evidence.** D: comments + R0003 contract table row · I: explicit fences · V: unit and control suites; independent review per R0003 certificate (classification scope)
- **Work orders.** R000D (issue 13, merge 645b53cc) for weather/radar spacing only
- **Accepted evidence.** r0003-ownership 24/24, r0005-adoption 16/16, r0006-recovery 18/18, r0004-currentness-controls 3/3
- **Tests.** `tests/r0003-ownership.test.cjs`, `tests/r0005-adoption.cjs`, `tests/r0006-recovery.cjs`, `tests/r0004-currentness-controls.cjs`
- **Observed facts.** no defect found by lane A
- **Unknowns.** native fetch abort and body-settlement timing

<a id="ism-pray-003"></a>
### ISM-PRAY-003 — Current prayer acquisition, admission/cache and adopted-zone reconciliation

Original audit: **N04** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Whether a prayer record becomes current for the requested civil day and zone.
- **Sources.** `src/native/index.html` `admitPrayerRecord` ~L1048-1066, `readPrayerCache`/`saveCache` ~L1114-1127, `prayerCivilDay` ~L1170-1176, `prayerRecordReady` ~L1184-1193, `adoptPrayerBundle` ~L1200-1223, `loadPrayerData` ~L3669-3708 (gen ~L7102)
- **State dimensions.** no current | cache candidate | cache current | network candidate | zone adopted / day re-derived | one corrected-day request | current admitted | unavailable | superseded
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | cache hit | `requestEligible` | `tz=cached.timezone` before the day filter (~L3676) |
  | network result | `prayerResultEligible` | `tz=data.meta.timezone` (~L3691, ~L3697) |
  | day differs after adoption | — | one corrected request within the same 3-attempt budget |
  | `prayerCivilDay()` returns null | invalid live `tz` | request `/timings/null`; every response rejected; never retried (PRA-F-02) |

- **Guards.** strict clocks, exact Gregorian date, valid IANA `meta.timezone`, malformed AH → `hijri:null`
- **Actors and ownership.** boot, `applyConfig`, `maintainPrayerDay`
- **Effects.** `today`, `tomorrow`, `tz`, cache envelope per `cacheKey`
- **Invariants.** no wrong-day, wrong-zone or old-generation record becomes current
- **Failure and recovery.** invalid hint zone: permanent "Prayer times unavailable" (truthful, but unrecoverable)
- **Invalid, duplicate, stale or concurrent risks.** `tz` written before the record is current (ISM-PRAY-009); one-day cache per key
- **Status evidence.** D: comments; issues 2, 4, 5 · I: admission explicit, zone adoption implicit · V: unit suites; no invalid-hint test
- **Work orders.** none after f71fef6c (R0002, R0004, R0005 before)
- **Accepted evidence.** r0002-admission 62/62, r0004-boot-day 8/8, r0005-day-return 6/6, hotfix-prayer-weather 21/21
- **Tests.** `tests/r0002-admission.cjs`, `tests/r0004-boot-day.cjs`, `tests/r0005-day-return.cjs`, `tests/hotfix-prayer-weather.test.cjs`
- **Observed facts.** Probe A P1 (re-run): 3 requests to `/v1/timings/null`; `today=null`, `tz="Bogus/Zone"` after 180 simulated seconds; probe G `tz-hint-probe` independently gives `prayerCivilDay=null` for `Asia/Riyad`
- **Unknowns.** provider response to `timings/null` (not contacted); whether builder/settings can emit an invalid zone (the builder never emits `tz`, ISM-CFG-007)
- **Findings.** [PRA-F-02](docs/audit/post-rlgwo/FINDINGS.md#pra-f-02)

<a id="ism-pray-004"></a>
### ISM-PRAY-004 — Prayer day rollover, next-day prefetch, cooldown and stale state

Original audit: **N05** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Promotion of tomorrow at civil midnight, recovery of a missing current day, next-day prefetch.
- **Sources.** `src/native/index.html` `_prayerCooldown` ~L1166, `prayerNextDay` ~L1177, `beginPrayerRequest`…`maintainPrayerDay` ~L1224-1260, state ~L2271-2274
- **State dimensions.** current region {ready, stale, absent} × recovery {idle, owned, cooldown(day,nextTry)}; prefetch region {idle, owned, cooldown, tomorrow-ready}; mirror flags `fetchingTomorrow`, `_rolloverBusy`, `_rolloverNextTry` (read only by `qaState`)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | visible frame / render | exact `tomorrow` | promote; else adopt exact cache |
  | not ready, slot free | 60 s cooldown per day elapsed | start `loadPrayerData` |
  | `render()` | — | `prefetchPrayerDay` |

- **Guards.** civil-day equality, slot ownership, 60 s cooldown
- **Actors and ownership.** loop (`maintainPrayerDay`), `render`
- **Effects.** `today`, `tomorrow`, `_prayerStale`
- **Invariants.** civil midnight is an ownership event; a next-day record cannot change the present zone
- **Failure and recovery.** cooldown retry each 60 s
- **Invalid, duplicate, stale or concurrent risks.** speculative endless 60 s retry if the provider zone of a prefetch differs from `tz`
- **Status evidence.** D: comments · I: parallel regions encoded by slots plus mirror flags · V: unit recovery cases
- **Work orders.** none after f71fef6c
- **Accepted evidence.** r0005-day-return, r0006-recovery, prayer-next-event-state recovery cases
- **Tests.** `tests/r0005-day-return.cjs`, `tests/r0006-recovery.cjs`, `tests/prayer-next-event-state.test.cjs`
- **Observed facts.** Probe A P5: stale record → `model()===null`, `.c[data-stale]` stays `""`; the only writer (~L3518) is on the model branch (PRA-F-21)
- **Hypotheses.** prefetch zone mismatch retried for the page lifetime
- **Unknowns.** native multi-day clock jumps
- **Findings.** [PRA-F-21](docs/audit/post-rlgwo/FINDINGS.md#pra-f-21)

<a id="ism-pray-005"></a>
### ISM-PRAY-005 — Prayer model, explicit next-event selection, countdown and DOM publication

Original audit: **N06** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** One target drives countdown, row highlight, arc marker and receipt.
- **Sources.** `src/native/index.html` `prayerDayFields` ~L2286, `prayerEventCandidates` ~L2294-2319, `selectPrayerEvent` ~L2320-2351 (gen ~L5752), `model` ~L2352-2394, `drawArc` ~L2397-2500, `render` ~L3482-3529; contract `docs/state-contracts/R0007.md`
- **State dimensions.** selection {current-record-unavailable, same-day-target, next-day-target, next-day-required, endpoint-unresolved}; progress kind {wall-interval, decorative-*}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | captured `nowEpoch`, eligible day | — | earliest strictly future unique epoch, then declared rank |
  | needs successor | matching civil successor only | `next-day-target` or `next-day-required` |
  | gap/fold/unsupported candidate that could precede | — | precision blocked (bounds only) |

- **Guards.** date, zone and generation of the current record
- **Actors and ownership.** `render`
- **Effects.** `.nt`, `.cn`, rows, arc, receipt
- **Invariants.** without a target, `.nt`="—" and "Countdown unavailable"; receipt copies the model instant
- **Failure and recovery.** no target → explicit unavailable output
- **Invalid, duplicate, stale or concurrent risks.** `drawArc` reads method parameters from global `today`, not the selected target (~L2476; speculative, minor); `warmEnd`/`needTomorrow` unused
- **Status evidence.** D: state contract R0007 + acceptance ledger · I: NF01 hard-coded Fajr removed · V: before/after (NF01 probe at f71fef6c vs P3) + mutants; hosted run 42953929662 FAILURE/PARTIAL
- **Work orders.** R0007 (issue 7, merge dbf3370f, PR 73)
- **Accepted evidence.** prayer-next-event-state 44/44 incl. ES07 `hardcoded-fajr`/`name-order` mutants (test L232); probe A P3; R0007 independent source review
- **Tests.** `tests/prayer-next-event-state.test.cjs`, `tests/r0018-prayer-row-status.cjs`, `tests/r000a-markers.cjs`
- **Observed facts.** P3 at 23:00 UTC: reordered Isha 00:31 → `next-day-target`, 91 min; control Fajr 360 min
- **Unknowns.** native pixel acceptance on Windows; real provider reordering incidence
- **Findings.** [PRA-F-21](docs/audit/post-rlgwo/FINDINGS.md#pra-f-21), [PRA-F-35](docs/audit/post-rlgwo/FINDINGS.md#pra-f-35)

<a id="ism-pray-006"></a>
### ISM-PRAY-006 — Calendar publication, Hijri provenance/rollover and date disclosure

Original audit: **N07** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Which Gregorian/Hijri dates the footer shows and when AH advances at Maghrib.
- **Sources.** `src/native/index.html` `calendarFields` ~L830-850, `selectCalendarDisplay` ~L854-917 (gen ~L4390), `renderCalendarDates`
- **State dimensions.** unavailable | before Maghrib | after Maghrib with next AH | after Maghrib, next unavailable | preview day; dialog {closed, open}; initiator focus
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | current context | loaded day = requested day and zone = `tz` | current AH |
  | after Maghrib | admitted matching `tomorrow` | next AH; never arithmetic roll-forward |

- **Guards.** current-context match
- **Actors and ownership.** `render`
- **Effects.** footer dates, disclosure dialog
- **Invariants.** old AH is never relabelled current
- **Failure and recovery.** "Sunset date update unavailable"
- **Invalid, duplicate, stale or concurrent risks.** no-model branch now also runs `withdrawWeatherEffects` → `paintLunarOptic` (~L3491 → ~L2728 → ~L3007), which the date harness stub cannot satisfy
- **Status evidence.** D: comments; issues 1, 9, 25 · I: derived projection plus one-value receipt · V: unit; 3 cases red at baseline (PRA-F-06)
- **Work orders.** R0007 (year padding, font variables)
- **Accepted evidence.** date harnesses r0001/r0009/r0019 each 1 case red since the R000B merge da126880
- **Tests.** `tests/r0001-date-sinks.cjs`, `tests/r0009-date-selection.cjs`, `tests/r0019-date-disclosure.cjs`
- **Observed facts.** integrator run: failing cases "missing dates expose explicit successor unavailable output", "wrong current context withholds the model…", "missing invalid and no-model values clear previously hidden full dates", all `el.style.getPropertyValue is not a function`
- **Unknowns.** native modal focus and footer pixels
- **Findings.** [PRA-F-06](docs/audit/post-rlgwo/FINDINGS.md#pra-f-06)

<a id="ism-pray-007"></a>
### ISM-PRAY-007 — Countdown font readiness, rail sampling and geometry-fit cache

Original audit: **N18** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** When the countdown text is re-measured and fitted to the arc rail.
- **Sources.** `src/native/index.html` `_cnFit`, `cnFontChanged`, `cnFontSignature` ~L3374-3402, `fitCn` ~L3403-3447 (gen ~L6836)
- **State dimensions.** fit key `currentKey|round(sunrise)|round(sunset)|faceStatusSignature`; `fitCn._arcSamples` keyed by rail `d`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | relevant face settles | — | `_cnFit=""`, dirty |
  | equal key | — | early return |
  | new key | — | measure and fit |

- **Guards.** key equality
- **Actors and ownership.** `render`, FontFaceSet listeners
- **Effects.** countdown font size/position
- **Invariants.** fit invalidated on web-font application
- **Invalid, duplicate, stale or concurrent risks.** key omits rail `d`, noon and declination; `resetForNewLocation` does not clear `_cnFit` (PRA-F-23)
- **Status evidence.** D: comments + R0007 font section · I: implicit cache · V: font-gate tests only; no fit-key test
- **Work orders.** R0007 font gate (58fc4afc, ec69edf8)
- **Accepted evidence.** r0007-font-gate 5/5, r0007-font-use 3/3, r0007-async-observation 5/5, r0007-recovery-precondition 21/21
- **Tests.** `tests/r0007-font-*.cjs`
- **Observed facts.** key at ~L3407
- **Hypotheses.** NH01 reuse of a prior fit after a broad location change
- **Unknowns.** visual magnitude
- **Findings.** [PRA-F-23](docs/audit/post-rlgwo/FINDINGS.md#pra-f-23)

<a id="ism-pray-008"></a>
### ISM-PRAY-008 — Optional web-typography activation gate

Original audit: **new (NEW-A-01)** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md) · Status D / I / V: **EIV / EEV / EIV** · Historical disposition: *new*

- **Scope and decision.** Whether web fonts are applied; never blocks prayer or sky.
- **Sources.** `src/native/index.html` `#webfont-css` ~L7-26, `WEBFONT_FACES`, `requestWebfonts` ~L3340-3368; `docs/state-contracts/R0007.md` ~L208-238
- **State dimensions.** not-requested → requested-pending → applied (`html.webfonts`) | failed-closed (no retry)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | stylesheet `media=="all"` | — | `fonts.load` for 3 faces |
  | all sets non-empty | — | class added + `cnFontChanged` |
  | rejected/empty | — | no effect, one-shot |

- **Guards.** one-shot flag
- **Actors and ownership.** link load hook
- **Effects.** typography
- **Invariants.** never blocks prayer or sky
- **Failure and recovery.** fail closed to fallback fonts
- **Invalid, duplicate, stale or concurrent risks.** on-demand non-Latin subsets can blank briefly (disclosed R0007 ~L238)
- **Status evidence.** D: R0007 contract · I: explicit one-shot · V: unit + one hosted cohort
- **Work orders.** R0007 (issue 7)
- **Accepted evidence.** r0007-font-gate 5/5, r0007-font-use 3/3; hosted Firefox cohort 0 text-loss frames in 20 cells (one run)
- **Tests.** `tests/r0007-font-gate.cjs`, `tests/r0007-font-use.cjs`
- **Unknowns.** stylesheet that never loads stays not-requested

<a id="ism-pray-009"></a>
### ISM-PRAY-009 — Live timezone authority `tz` (multi-writer) and its consumer fan-out

Original audit: **new (NEW-A-03; reader list extended by the second omission pass, OM-01)** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Which zone is current: config hint → provider-adopted → current-record zone.
- **Sources.** writers `src/native/index.html` `bindConfig` ~L686, `loadPrayerData` ~L3676/3691/3697, `adoptPrayerBundle` ~L1213; readers `partsInTz` ~L937, `prayerCivilDay` ~L1170, `simNow` ~L1014, `beginRequest` ~L1076, `selectPrayerEvent` ~L2324, `selectCalendarDisplay` ~L865, `prayerRecordReady` ~L1185, weather `requestZone`, and (added by OM-01) `skySceneIdentity` ~L2219, `moonGeometryObservation` ~L2031, `weatherInformation` ~L1749, `SalahMoonHost.capture` ~L4171, `real-sky/native-host-hooks.js` ~L42, `real-sky/native-first-paint.mjs` ~L18 (hint copy)
- **State dimensions.** hint (config, default `America/New_York` when absent) | provider-adopted | current-record zone; `_cacheTz` frozen separately
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | any write that changes `tz` | none on the hint | re-keys formatter caches; re-anchors explicit clocks (PRA-F-14); changes the requested civil day |
  | hint → adopted zone at boot | — | new `skySceneIdentity` → `beginSkyScene` on the next paint (ISM-SKY-001; PRA-F-08, OM-01) |
  | broad `applyConfig` | — | `bindConfig` resets `tz` to the hint carried by the form (~L4026), then adoption flips it again |

- **Guards.** network writes only after `prayerResultEligible`; cache writes after `requestEligible` + admission; no validity guard on the hint
- **Actors and ownership.** config, prayer loader
- **Effects.** every time and scene consumer
- **Failure and recovery.** invalid hint is fatal for prayer (PRA-F-02)
- **Invalid, duplicate, stale or concurrent risks.** multi-writer with side effects on clocks and scene identity
- **Status evidence.** D: comments (~L680, ~L3676, ~L3691) · I: implicit · V: adoption order only; no hint-validity, preview or scene-flip test (first-paint fixtures use the default zone, `tests/real-sky/native-first-paint.test.mjs` ~L20, ~L61)
- **Accepted evidence.** r0004-boot-day, r0005-* (adoption order only)
- **Tests.** `tests/r0004-boot-day.cjs`, `tests/r0005-*.cjs`
- **Observed facts.** probe G `tz-identity-probe` (re-run): builder hash has no `tz`; identity `24.47|39.61|America/New_York|wall` → `24.47|39.61|Asia/Riyadh|wall`
- **Hypotheses.** visible re-pending of celestial layers after the timetable arrives
- **Unknowns.** pixel visibility of the second scene
- **Findings.** [PRA-F-02](docs/audit/post-rlgwo/FINDINGS.md#pra-f-02), [PRA-F-08](docs/audit/post-rlgwo/FINDINGS.md#pra-f-08), [PRA-F-14](docs/audit/post-rlgwo/FINDINGS.md#pra-f-14)

<a id="ism-pray-010"></a>
### ISM-PRAY-010 — Singleton render loop, visibility, provider cadence and motion lifecycle

Original audit: **N19** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md), [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Drives prayer maintenance, render, weather/radar polls, cloud paint and preview presentation every visible frame.
- **Sources.** `src/native/index.html` `_loopStarted` ~L3648, `startRenderLoop` ~L3855-3898: `loop` L3869-3889, `_raf=requestAnimationFrame(loop)` L3888, `start` L3890, `stop`/`setVis` L3891-3892 (gen ~L7288)
- **State dimensions.** `_loopStarted`; `_raf` (null | id); `_onScreen`; `_lastSec`, `_lastWx`, `_lastCloud`; CSS `paused`/`fast`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | frame | simulation ready | `maintainPrayerDay` → poll (≥30 s, not ADVANCING) → `render` on new second/dirty → `reconcileCloudPublication` → cloud paint → telemetry → `SalahSkyPreview.present` → reschedule |
  | hidden/offscreen | — | `stop()` cancels and nulls `_raf` |
  | visible | `!_raf` | `start()` |
  | throw anywhere before L3888 | — | no next frame; `_raf` keeps the consumed id, so `start()` is a no-op until hide/show (PRA-F-01) |

- **Guards.** `!_raf` in `start`
- **Actors and ownership.** document visibility, IntersectionObserver
- **Effects.** all periodic UI
- **Invariants.** one loop and listener set per document; hidden time does not jump clouds; retry clocks independent of the simulation rate
- **Failure and recovery.** no try/finally; `applyTheme` rethrows (~L3336); contrast `real-sky/native-host.mjs` `animate` catches and reschedules (~L253)
- **Invalid, duplicate, stale or concurrent risks.** optional Moon/sky work on the same synchronous path as prayer publication (PRA-F-01)
- **Status evidence.** D: comments · I: implicit · V: lifecycle script tests; no exception-recovery test
- **Work orders.** R000B (per-frame cloud reconcile, ea9f8300); R000D (retry cadence, through ISM-WX-003)
- **Accepted evidence.** r001d-lifecycle 1/1, r0025-lifecycle 1/1, r0020-clock loop cases; probe E (re-run)
- **Tests.** `tests/r001d-lifecycle.cjs`, `tests/r0025-lifecycle.cjs`, `tests/r0020-clock.cjs`
- **Observed facts.** probe E (re-run): stub `SalahMoonRuntime.request()` throws → `render()` throws, `.cn` stays "SENTINEL", `.times` empty; control repopulates
- **Hypotheses.** no natural production throw identified
- **Unknowns.** real-browser rAF suspension and exception recovery
- **Findings.** [PRA-F-01](docs/audit/post-rlgwo/FINDINGS.md#pra-f-01)

## Weather, radar and location acquisition (`ISM-WX`)

<a id="ism-wx-001"></a>
### ISM-WX-001 — Weather acquisition, current/hourly records and persistent cache

Original audit: **N08** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **PEX / PEX / EIV** · Historical disposition: *partly resolved*

- **Scope and decision.** Whether a current-model record and hourly track exist for the current target, and whether a request is issued.
- **Sources.** `src/native/index.html` state ~L1263, admission ~L1300-1368, `weatherEligibility`/`selectedWeather` ~L1369-1383, `loadWx` ~L1405, `wxFetchJson` ~L1421-1445, `fetchWeather` ~L1446-1476, `startWeather` ~L3652, `resetForNewLocation` ~L3717-3726
- **State dimensions.** current {none, admitted-eligible, admitted-ineligible, sim, forecast-derived}; track {none, admitted}; slot; attempt stage {fetch, body, settled}; cache envelope (≤6 h); retry record (ISM-WX-003)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | poll ~30 s / boot / apply | `retryGate=="eligible"` | request + 10 s attempt |
  | body | `attemptEligible` after fetch and after `json()` | independent admission of current and track |
  | admitted current | eligible, or old record not eligible | replace `weather`, cache write |
  | timeout/abort/HTTP/parse | one-shot `finish` | attempt expired, slot released |
  | selected record ages past 900 s | — | withdrawn; replacement only at the next poll (PRA-F-03) |

- **Guards.** finite in-range coordinates; captured units/zone/target; response zone equal; strictly increasing hourly epochs; closed code set
- **Actors and ownership.** loop poll, boot, apply; `syncWeather` and SIM branch also write `weather`
- **Effects.** `weather`, `weatherTrack`, `siteElev`, `lastWxAt`, `salahwx:*` storage
- **Invariants.** receipt is not freshness (source and receipt ages both 0…900 000 ms); forecast never overwrites live current in real time
- **Failure and recovery.** existing record retained only while still eligible
- **Invalid, duplicate, stale or concurrent risks.** authority gap every quarter hour (PRA-F-03); `received` recorded for rejected bodies (PRA-F-15); no eviction of `salahwx:*` keys (OM-03, PRA-F-17)
- **Status evidence.** D: R000B, R000D contracts + comments · I: slots/attempts explicit, record lifecycle implicit · V: unit + mutation + native two engines (R000D)
- **Work orders.** R000D (issue 13, 645b53cc); R000B (issue 11, da126880)
- **Accepted evidence.** r000c/r000d-weather, r0024-*, weather-retry-clock-* (lane B: 618 tests, 614 pass, 4 todo); R000D native Chromium 148 / Firefox 153
- **Tests.** `tests/r000c-weather.test.cjs`, `tests/r000d-weather.test.cjs`, `tests/r0024-response-zone.test.cjs`, `tests/weather-retry-clock-*.test.cjs`
- **Observed facts.** retry shortcut ~L1276 returns `fresh-data-satisfied` while the record is selected; probe B quarter-gap (re-run): no fetch while selected, polls finding nothing eligible at 06:30:20 and 06:45:20
- **Hypotheses.** provider `current.time` advances in 15 min steps equal to the TTL
- **Unknowns.** provider response-size bound; storage partitioning
- **Findings.** [PRA-F-03](docs/audit/post-rlgwo/FINDINGS.md#pra-f-03), [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15), [PRA-F-17](docs/audit/post-rlgwo/FINDINGS.md#pra-f-17)

<a id="ism-wx-002"></a>
### ISM-WX-002 — Weather truth/decision, information text and header publication

Original audit: **N09** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **PEX / PEX / EIV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** What condition, permissions (rain/snow/lightning) and header text the widget claims.
- **Sources.** `src/native/index.html` `wxInfo` ~L1601, fixture lane ~L1619-1681, `weatherForecast` ~L1682, `reconcileWeatherEvidence` ~L1690, `weatherDecision` + `_wxDecisionCache` ~L1718-1745, `weatherInformation` ~L1747-1811, header ~L1818-1838, `gateWeatherCode` ~L2609-2637
- **State dimensions.** lane {live, preview, simulation-fixture}; condition {unavailable, model-estimated-*, preview-*, supported/conflicting/unknown}; decision cache [at, until)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | target/current/track/preview identity changes, or `now` leaves [at,until) | — | recompute decision |
  | header paint | — | from one decision in `render`, `paint` and on withdrawal |

- **Guards.** live present-evidence adapter closed in production; lightning only from a qualified fixture or explicit `simWx` thunder; model rain ≥0.05 mm, thunder ≥0.8 mm
- **Actors and ownership.** `render`, `paint`, withdrawal
- **Effects.** `#wi`, `#wt`, `#weather-information`, ARIA
- **Invariants.** a model estimate is always labelled; unavailable is not clear; radar grants nothing
- **Failure and recovery.** expiry evaluated on every decision
- **Invalid, duplicate, stale or concurrent risks.** header can show a model precipitation condition while clouds/particles are withheld without a timetable (PRA-F-32)
- **Status evidence.** D: R000B, R0024 contracts, AGENTS truth rules · I: pure decision + receipt · V: unit + mutation + native Chromium
- **Work orders.** R000B (issue 11); R0024 (issue 36, before f71fef6c)
- **Accepted evidence.** r0024-information, weather-withdrawal-authority/mutations, weather-no-timetable-*; native Chromium withdrawal cells (R000B certificate)
- **Tests.** `tests/r0024-information.test.cjs`, `tests/weather-withdrawal-*.test.cjs`, `tests/weather-no-timetable-*.test.cjs`
- **Observed facts.** `_wxDecisionCache` rejects `now<cache.at` (backward correction recomputes)
- **Unknowns.** native readability of the long accessible label
- **Findings.** [PRA-F-32](docs/audit/post-rlgwo/FINDINGS.md#pra-f-32)

<a id="ism-wx-003"></a>
### ISM-WX-003 — Weather/radar elapsed retry eligibility

Original audit: **new (NEW-A-02 + NEW-B-01; carries the XF02 resolution)** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md), [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *new*

- **Scope and decision.** When a replacement weather or radar request may start.
- **Sources.** `src/native/index.html` `_WX_RETRY`, `_wxRetry` L1269, `retryClockDomain`, `retryGate` L1272-1279, `retryDiagnostics` ~L1280-1286; stamps ~L1453, ~L1526; reset ~L3720
- **State dimensions.** `_wxRetry[kind]` = null | `{startedAt (elapsed), clock}`; gate {suppressed-by-mode, target-ineligible, active-owned-attempt, fresh-data-satisfied, cooldown, eligible}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | attempt start | — | stamp elapsed |
  | elapsed ≥ 60 s (weather) / 600 s (radar) | — | gate opens |
  | location/broad change | — | both cleared |

- **Guards.** order SIM → target → busy → shortcut → spacing → slot
- **Actors and ownership.** loop poll
- **Effects.** request issue
- **Invariants.** wall corrections do not move spacing when `performance.now` exists; UTC source/receipt ages unchanged
- **Failure and recovery.** without `performance.now`, degraded wall fallback disclosed in `qaState().wxTruth.retry`
- **Invalid, duplicate, stale or concurrent risks.** after a backward device-clock change, refetch every 60 s while each response's negative source age keeps it ineligible (PRA-F-24)
- **Status evidence.** D: `docs/state-contracts/R000D.md` · I: XF02 stranded-retry defect removed · V: RED→GREEN, mutants, native two engines, independent review
- **Work orders.** R000D (issue 13, merge 645b53cc, ba0851ae)
- **Accepted evidence.** weather-retry-clock-state 23/23 (RED 18 fail on prior main), mutations 12/12, native Chromium 148 / Firefox 153, independent delta review (R000D contract ~L154-205)
- **Tests.** `tests/weather-retry-clock-state.test.cjs`, `tests/weather-retry-clock-mutations.test.cjs`
- **Observed facts.** `lastWxTry`/`lastRadarAt` are write-only compatibility fields
- **Unknowns.** OS sleep / background resume (R000D limit)
- **Findings.** [PRA-F-24](docs/audit/post-rlgwo/FINDINGS.md#pra-f-24)

<a id="ism-wx-004"></a>
### ISM-WX-004 — Radar diagnostic transport, image lease and expiry

Original audit: **N10** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** Acquisition of a diagnostic-only RainViewer sample.
- **Sources.** `src/native/index.html` `weatherRadar` ~L1477-1481, `radarEvidence` ~L1482, `radarPrecipNow` (constant 0) ~L1489, `wxRadarSample` ~L1490-1519, `fetchRadar` ~L1520-1552; consumer `qaState().wxTruth` ~L3554
- **State dimensions.** manifest {fetching, body, settled}; image {loading, decoded, timeout/error/cancelled}; sample {none, available (≤20 min, same target), stale}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | manifest attempt (10 s) | — | image attempt (10 s) → 7×7 canvas sample → `weatherRadar` |
  | any failure | — | prior frame kept, expires by TTL |

- **Guards.** finite frame/index seconds; finite Web-Mercator tile; `attemptEligible` at load and after canvas
- **Actors and ownership.** loop poll (10 min)
- **Effects.** `weatherRadar` only (no header, ARIA, particle or permission consumer)
- **Invariants.** alpha is never precipitation evidence
- **Failure and recovery.** handlers detached on finish; physical download may continue
- **Invalid, duplicate, stale or concurrent risks.** tile location sent to a third party with no product benefit; manifest `host` concatenated unchecked (PRA-F-16)
- **Status evidence.** D: comments + R000D ES0D-14 · I: gate explicit, sample lifecycle implicit · V: unit; native admitted-state only
- **Work orders.** R000D (spacing); R000E (issue 14, before f71fef6c)
- **Accepted evidence.** r000d-weather, r000c-weather, r0017-transport
- **Tests.** `tests/r000d-weather.test.cjs`, `tests/r0017-transport.cjs`
- **Observed facts.** probe B outcome (re-run): manifest host `http://…` dispatched an image request
- **Hypotheses.** retained for a future qualified decoder
- **Unknowns.** browser reclamation of detached images
- **Findings.** [PRA-F-16](docs/audit/post-rlgwo/FINDINGS.md#pra-f-16)

<a id="ism-wx-005"></a>
### ISM-WX-005 — Cloud publication authority receipt (weather → cloud consumers)

Original audit: **new (NEW-B-02 + NEW-D-02; carries the NF02 resolution)** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md), [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *new*

- **Scope and decision.** Whether weather-derived cloud coverage, raster and effects may remain published.
- **Sources.** `src/native/index.html` `_cloudPublication` … `cloudPublicationCurrent` ~L2685-2752, `withdrawWeatherEffects` ~L2722-2729, `applyCloudState` ~L3222-3241, no-model branch L3491, per-frame reconcile L3881, `paintClouds` ~L2818, `beginSkyScene` ~L2230; consumers `real-sky/native-host.mjs`, `native-preview-host.mjs`, `native-composition.mjs` ~L132; hooks `real-sky/native-host-hooks.js` ~L12-13
- **State dimensions.** receipt `{revision, state: uninitialised|eligible-published|withdrawn-unavailable|superseded, reason, target, lane, sourceValidAt, retrievedAt, conditionState}`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | complete atmosphere, available decision | — | `eligible-published` |
  | decision unavailable / lane / target / scene / mode change / lease expiry | — | withdraw: zero coverage/density/canvas, effects off, header repainted |
  | identical republication | — | same receipt |
  | healthy A→B refresh | A still selected and `model()!==null` | A retained until full paint |

- **Guards.** decision availability, target and lane match
- **Actors and ownership.** painter, renderer owners (via `reconcileClouds`)
- **Effects.** cloud pixels, header, CSS effects
- **Invariants.** no cloud pixel published without a current receipt at final publication
- **Failure and recovery.** withdrawal immediate (truth over continuity)
- **Invalid, duplicate, stale or concurrent risks.** healthy-refresh retention depends on the prayer timetable (by R000B policy); renderer capture step has write effects (PRA-F-15); quarter-hour withdrawal/snap (PRA-F-03)
- **Status evidence.** D: `docs/state-contracts/R000B*.md` · I: NF02 bypass removed (no-model branch reconciles, L3491) · V: before/after + mutants + hosted Chromium; Firefox/WebKit withdrawal not observed
- **Work orders.** R000B (issue 11, PR 72, merge da126880)
- **Accepted evidence.** weather-no-timetable-*, r000b-remaining, r000b-sky-withdrawal, native-weather-withdrawal (pass); 7 mutation discriminators; hosted Chromium cells; independent review (certificate issue 11)
- **Tests.** `tests/weather-no-timetable-*.test.cjs`, `tests/r000b-*.test.*`, `tests/real-sky/native-weather-withdrawal.test.mjs`
- **Unknowns.** hidden-card retention of the old deck until resume (certificate issue 11 §5)
- **Findings.** [PRA-F-03](docs/audit/post-rlgwo/FINDINGS.md#pra-f-03), [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15), [PRA-F-32](docs/audit/post-rlgwo/FINDINGS.md#pra-f-32)

<a id="ism-wx-006"></a>
### ISM-WX-006 — Weather target capture and location provenance

Original audit: **new (NEW-B-03)** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **PEX / PEX / EEV** · Historical disposition: *new*

- **Scope and decision.** The immutable target a weather/radar record belongs to.
- **Sources.** `src/native/index.html` `captureWeatherTarget` ~L1384-1395, `weatherTargetSame` ~L1396, `currentWeatherTarget` ~L1397-1404
- **State dimensions.** cached target keyed by CONFIG identity, evidence identity, generation, lat, lon
- **Guards.** future `acquiredAt` → null
- **Actors and ownership.** weather/radar loaders
- **Effects.** record target
- **Invariants.** storage/save never renews a fix
- **Invalid, duplicate, stale or concurrent risks.** none found
- **Status evidence.** D: comments, issue 35 · I: partly explicit · V: unit + mutation
- **Work orders.** R0023 (issue 35, before f71fef6c)
- **Accepted evidence.** r0023-metadata 31/31, r0023-mutations (all caught)
- **Tests.** `tests/r0023-metadata.cjs`, `tests/r0023-mutations.cjs`
- **Observed facts.** live lane never uses device precision

<a id="ism-wx-007"></a>
### ISM-WX-007 — Location evidence normalisation and persistence provenance

Original audit: **new (NEW-B-04)** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *new*

- **Scope and decision.** How acquisition evidence survives normalise/save/load without being renewed or upgraded.
- **Sources.** `src/native/config.js` `normalizeLocationEvidence` ~L56-85, `loadLocal`/`saveLocal` ~L219-245, `applyHashPrefs` ~L357-362
- **State dimensions.** source {hash, manual, place, browser-geolocation, coarse-ip, legacy, unknown}; intent {fixed-site, device-position, coarse-area, unknown}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | browser claim without raw evidence | — | `legacy` |
  | future/non-positive fix time | — | null |
  | save | — | raw evidence and `origin` kept; browser source rewritten to `manual` |

- **Actors and ownership.** config module
- **Effects.** stored record
- **Invariants.** evidence never asserts "here now"
- **Failure and recovery.** backward wall correction demotes a saved fix to unknown time (fail-closed)
- **Invalid, duplicate, stale or concurrent risks.** in-memory `source:"localStorage"` survives a successful Reset (OM-04, PRA-F-04)
- **Status evidence.** D: comments · I: partly explicit · V: unit
- **Work orders.** R0023; R0026 (issue 68)
- **Accepted evidence.** r0023-*, location-admission-*
- **Tests.** `tests/r0023-*.cjs`, `tests/location-admission-*.test.cjs`
- **Findings.** [PRA-F-04](docs/audit/post-rlgwo/FINDINGS.md#pra-f-04)

<a id="ism-wx-008"></a>
### ISM-WX-008 — Site elevation dual custody

Original audit: **new (NEW-B-05)** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *new*

- **Scope and decision.** Surface elevation from the weather response, used by native atmosphere and the CP9 renderer.
- **Sources.** `src/native/index.html` `siteElev` L1291, writer L1467, readers ~L3083, ~L3192; CP9 `_cp9SiteElevation` `real-sky/native-host-hooks.js` ~L5-9, ~L23, injected by `tools/build_native.py` ~L69-71
- **State dimensions.** legacy scalar {0, last response elevation}; CP9 {null, frozen {heightM, generation, lat, lon}}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | accepted-attempt response with current or track | no eligibility or target binding | legacy updated |
  | eligible adoption | — | CP9 copy updated and bound |
  | `resetForNewLocation` | — | legacy NOT reset (L3717-3726) |

- **Guards.** CP9: generation + coordinates + selected current
- **Actors and ownership.** `fetchWeather`
- **Effects.** star haze/blur factors
- **Invariants.** CP9 consumption requires a match
- **Invalid, duplicate, stale or concurrent risks.** A's elevation persists for B when B's weather fails (PRA-F-17)
- **Status evidence.** D: comments · I: legacy implicit · V: legacy none
- **Accepted evidence.** CP9 copy: `tests/real-sky/cp9-elevation.test.mjs`; legacy none
- **Tests.** `tests/real-sky/cp9-elevation.test.mjs`
- **Observed facts.** integrator confirmed L1467 and the reset body
- **Hypotheses.** visual effect small
- **Unknowns.** visual magnitude
- **Findings.** [PRA-F-17](docs/audit/post-rlgwo/FINDINGS.md#pra-f-17)

<a id="ism-wx-009"></a>
### ISM-WX-009 — Forecast-track preview substitution, live return and sky-identity churn

Original audit: **new (NEW-B-06 + NEW-D-01)** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md), [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** In explicit preview (`ADVANCING`/`_clockPreview`) the current record is replaced each render by an interpolated forecast object that the sky snapshot also consumes.
- **Sources.** `src/native/index.html` `wxAt` ~L1553-1570, `syncWeather` ~L1571-1581 (called from `render` ~L3485), live return in `SalahClock.set` ~L3772; `real-sky/native-host-hooks.js` ~L42; `real-sky/native-contract.mjs` `nativeIdentity` ~L8
- **State dimensions.** `weather.src` {current, sim, forecast}; object identity changes every render while a track exists
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | render in preview | track target matches | `weather=wxAt(simNow())` (new object) |
  | new object | — | new native identity → lifecycle epoch++ → refined `clear` + preview re-render |
  | explicit live return | `src==="forecast"` | `weather=null; loadWx(); fetchWeather()` |

- **Guards.** track target; real time never substitutes
- **Actors and ownership.** `render`
- **Effects.** weather record, refined sky lifecycle
- **Invariants.** output labelled SIM/forecast preview
- **Invalid, duplicate, stale or concurrent risks.** refined frames never accepted once one worker render exceeds 1000/rate ms, and not reported as `rate-throughput` (PRA-F-10); no track age bound (PRA-F-25)
- **Status evidence.** D: comments · I: implicit · V: unit for substitution only
- **Accepted evidence.** r0024-weather, hotfix-prayer-weather (substitution); none for the sky interaction
- **Tests.** `tests/r0024-weather.test.cjs`, `tests/hotfix-prayer-weather.test.cjs`
- **Observed facts.** probe D (re-run, sanitised path): worker 300 ms → 0 accepted at rate 10; 800 ms → 0 at rate 2 and 10; 1200 ms → 0 at rates 1, 2, 10; constant weather accepted at every rate; `rate-throughput` never reported
- **Hypotheses.** mechanism behind the recorded "refined sky can stay pending at `timeScale` ≥ 2" observation
- **Unknowns.** native worker durations by device
- **Findings.** [PRA-F-10](docs/audit/post-rlgwo/FINDINGS.md#pra-f-10), [PRA-F-25](docs/audit/post-rlgwo/FINDINGS.md#pra-f-25)

<a id="ism-wx-010"></a>
### ISM-WX-010 — Coarse location provider cascade and whole-body deadline

Original audit: **C02** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** Permission-free area detection at boot (local/preferLocal without saved config) and on Reset.
- **Sources.** `src/native/config.js` `coarseDetect` ~L251-304, admission ~L87-115; callers `src/native/index.html` ~L3792-3809, ~L4130
- **State dimensions.** provider {GeoJS, ipinfo}; attempt {pending, ok, transport, http, parse, admission, timeout}; result {ok, failed}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | per provider | `Promise.race` with 6 s deadline | any stage failure advances |
  | exhaustion | — | `{ok:false,status:"failed"}` |

- **Guards.** `admitCoordinates` before `normalize`; no clamping
- **Actors and ownership.** boot, Reset
- **Effects.** detected config
- **Invariants.** exactly one adopted result per invocation; deadline owns headers+body+parse
- **Failure and recovery.** late work cannot trigger a second fallback
- **Invalid, duplicate, stale or concurrent risks.** a provider reporting `0,0` would be admitted (speculative); `_autoDetectStatus` boot-only (OM-05)
- **Status evidence.** D: `docs/state-contracts/R0026.md` · I: CF04 fixed · V: before/after tests + mutants + stubbed native + independent review
- **Work orders.** R0026 (issue 68, merge 7f2e8d16); R001F (issue 31, before)
- **Accepted evidence.** location-admission-outcomes/mutations, r001f-deadline 13/13; independent delivery review rejected 999/999, hex, exponent, Infinity (certificate issue 68 §2)
- **Tests.** `tests/location-admission-*.test.cjs`, `tests/r001f-deadline.cjs`, `tests/r001f-mutations.cjs`
- **Observed facts.** v1 copy (`v1/config.js`) frozen; CF09 remains there (ISM-V1)
- **Unknowns.** GeoJS `accuracy` unit
- **Findings.** [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

<a id="ism-wx-011"></a>
### ISM-WX-011 — Forward geocoder aggregate completion

Original audit: **C03** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** Distinguishes matches, no-match and unavailable for a place search.
- **Sources.** `src/native/config.js` ~L364-457 (`_nomCands`, `_zipCand`, `geocodeSearchDetailed`, lossy `geocodeSearch`)
- **State dimensions.** status {not-requested, matches, no-match, unavailable}; coverage {null, complete, partial, none}
- **Guards.** shared 8 s rejecting deadline; Zippopotam 404 = no-match
- **Actors and ownership.** settings, builder
- **Effects.** candidates
- **Invariants.** any failure prevents a no-match conclusion
- **Failure and recovery.** superseded lookups run to their deadline (bounded)
- **Invalid, duplicate, stale or concurrent risks.** Nominatim `class` vs `category` naming may make the preference inert (PRA-F-30)
- **Status evidence.** D: R0026 · I: CF06 fixed · V: tests + delivery review
- **Work orders.** R0026 (issue 68)
- **Accepted evidence.** location-admission-*, r000f-intent 21/21; delivery review: HTTP 503 → unavailable, `[]` → no-match
- **Tests.** `tests/location-admission-*.test.cjs`, `tests/r000f-intent.cjs`
- **Unknowns.** provider field naming
- **Findings.** [PRA-F-30](docs/audit/post-rlgwo/FINDINGS.md#pra-f-30)

<a id="ism-wx-012"></a>
### ISM-WX-012 — Browser location and permission request completion

Original audit: **C04** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **PEX / PEX / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Adopting a device position with its original age.
- **Sources.** `src/native/config.js` `geolocate`, `permissionState` ~L306-327; evidence ~L78-82
- **State dimensions.** unsupported | requesting | fix admitted | invalid coordinates | error(code); permission {granted, prompt, denied, unknown}
- **Guards.** `maximumAge` 10 min, timeout 10 s
- **Actors and ownership.** settings GPS, builder
- **Effects.** evidence with original timestamp/accuracy
- **Invariants.** a cached fix keeps its original age
- **Invalid, duplicate, stale or concurrent risks.** caller awaits an unbounded `permissions.query` before applying (PRA-F-29)
- **Status evidence.** D: R0026, comments · I: partly explicit · V: stubbed native
- **Work orders.** R0026 (issue 68)
- **Accepted evidence.** unit + native with stubbed geolocation
- **Tests.** `tests/location-admission-*.test.cjs`
- **Unknowns.** real permission prompt
- **Findings.** [PRA-F-29](docs/audit/post-rlgwo/FINDINGS.md#pra-f-29)

## Configuration, settings and builder (`ISM-CFG`)

<a id="ism-cfg-001"></a>
### ISM-CFG-001 — Configuration resolution, effect classification, apply generation and boot sequence

Original audit: **N01** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md), [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **EIV / EEV / EIV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** How much a proposed configuration invalidates (none / presentation / broad), and when the first scene and providers start.
- **Sources.** `src/native/index.html` `q`, `bindConfig` ~L677-690, `CONFIG_EFFECTS` ~L697-708, `classifyConfigChange` ~L721-741 (gen ~L4250), `buildSceneOnce`, `resetForNewLocation`, `applyConfig` ~L3711-3760 (gen ~L7162), `boot` ~L3779-3849; contract `docs/state-contracts/R0003.md`
- **State dimensions.** accepted `CONFIG` vs live scalars; `_cacheTz`; `_cfgMode` {bare, hardcoded, local, preferLocal}; `_autoDetectStatus`; `_runtimeGeneration`; change path {none, presentation, broad}; boot phase
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `applyConfig(cfg)` | classified before `saveLocal` rewrites source/savedAt | path selected |
  | none | all classified keys equal | `CONFIG=cfg` only |
  | presentation | only label/time/datefmt/appearance differ | rebinds 4 scalars, `_renderDirty`; no generation, `bindConfig`, reset or provider work |
  | broad | target/calc/tz/units/lp/seed/evidence/unknown key differs, Reset, or no config | generation++ → `bindConfig` → `resetForNewLocation` → `startWeather` → `await loadPrayerData` → recheck → loop |
  | boot/apply continuation after await | `generation!==_runtimeGeneration` | abandoned |

- **Guards.** pure frozen classifier; unknown key or evidence field fails closed to broad
- **Actors and ownership.** URL hash, settings close-save, Reset, coarse detect
- **Effects.** generation bump cancels all four request slots (ISM-PRAY-002)
- **Invariants.** a display-only edit preserves adopted `tz`, `_cacheTz`, request owners and sky; Reset is always broad
- **Failure and recovery.** `_commitSettings` calls `applyConfig` fire-and-forget without a rejection handler (PRA-F-33); bare mode never starts the loop
- **Invalid, duplicate, stale or concurrent risks.** broad `bindConfig` resets `tz` to the hint (ISM-PRAY-009); `units` restarts prayer and radar (PRA-F-20)
- **Status evidence.** D: R0003 contract · I: classifier explicit, boot phase implicit · V: unit + mutation + independent review; native on earlier bytes
- **Work orders.** R0003 (issue 3, PR 79, merge a4766a1b; fix a06957c6); R0026 (settings search only)
- **Accepted evidence.** config-effects-state 35/35, config-effects-mutations 21/21, r0003-ownership 24/24, native-appearance-currentness 15/15; native local headless observation + independent delivery review (certificate 6805636415) on earlier `index.html` bytes
- **Tests.** `tests/config-effects-*.test.cjs`, `tests/r0003-ownership.test.cjs`, `tests/native-appearance-currentness.test.cjs`
- **Observed facts.** probe A P4 (re-run): label+time change keeps requests 2 / generation 0; Reset → generation 1, +1 request
- **Hypotheses.** hidden first load defers the first prayer acquisition (double-rAF yield)
- **Unknowns.** native visible flash on broad applies
- **Findings.** [PRA-F-20](docs/audit/post-rlgwo/FINDINGS.md#pra-f-20), [PRA-F-33](docs/audit/post-rlgwo/FINDINGS.md#pra-f-33)

<a id="ism-cfg-002"></a>
### ISM-CFG-002 — Configuration persistence and mode resolution

Original audit: **C01** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** Which configuration the widget starts from and what is stored.
- **Sources.** `src/native/config.js` `parseHash` ~L118-137, `normalize` ~L140-160, `validate` ~L163, `serialize` ~L182-206, storage ~L211-249, `resolve` ~L333-353, `applyHashPrefs` ~L357
- **State dimensions.** mode local > preferLocal > hardcoded > bare; stored record {absent, valid v1, invalid, unreadable}; `source` vs `origin`; `savedAt`; cache namespaces `salah:*`, `salahwx:*` (OM-03)
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | script evaluation | — | `resolve` (synchronous) |
  | save | — | `{ok,savedAt}` / `{ok:false,error}` |
  | Reset | — | `clearLocal` removes only the config key; `salah:*`/`salahwx:*` keys remain (OM-03) |

- **Guards.** version gate `v===1`; `validate` requires coordinates; `tz` accepted by `parseHash` but never written by `serialize` (OM-02)
- **Actors and ownership.** config module, settings, builder
- **Effects.** `salah_widget:config:v1` and per-location caches
- **Invariants.** no accessor throws to its caller
- **Failure and recovery.** parse/version/validation failure → null (no diagnostic)
- **Invalid, duplicate, stale or concurrent risks.** coarse detection at boot is bound but not persisted (re-detects each load); cache keys grow without eviction and carry coordinates (PRA-F-17)
- **Status evidence.** D: comments + R0026/R0003 rows · I: partly explicit · V: unit
- **Work orders.** R0026 (admission); R0010, R0011 before
- **Accepted evidence.** r0010-preferences 9/9, r0011-storage 18/18, location-admission-*
- **Tests.** `tests/r0010-preferences.cjs`, `tests/r0011-storage.cjs`
- **Observed facts.** only `removeItem` calls: `clearLocal` (~L247) and the storage probe (~L215)
- **Unknowns.** native blocked/partitioned storage
- **Findings.** [PRA-F-17](docs/audit/post-rlgwo/FINDINGS.md#pra-f-17)

<a id="ism-cfg-003"></a>
### ISM-CFG-003 — Settings disclosure, focus, dirty form and close-save

Original audit: **N20** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Opening, editing and auto-saving the in-widget settings panel.
- **Sources.** `src/native/index.html` `_enableSettingsAffordance` ~L4008, `_wireSettings` ~L4044-4094, `_commitSettings` L4097-4104, `_openSettings`/`_closeSettings` ~L4145-4164
- **State dimensions.** `_setOpen`, `_setSession`, `_setDirty`, `_setFocusTimer`, `_setLastFocus`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | open | — | session++, populate, focus timer |
  | close/Escape | dirty and valid | commit (auto-save), restore focus |
  | any input | — | dirty |

- **Guards.** `validate`
- **Actors and ownership.** user
- **Effects.** `applyConfig(cfg,{save:true})`
- **Invariants.** close is auto-save (intentional)
- **Invalid, duplicate, stale or concurrent risks.** `_resetLocal` never clears `_setDirty`, so close can commit pre-Reset coordinates (PRA-F-04); `_setLocationSaved` derives from a stale `CONFIG.source` after Reset (OM-04)
- **Status evidence.** D: comments + R000F/R0011 certificates · I: partly explicit · V: unit
- **Work orders.** R0003 (close-save classification)
- **Accepted evidence.** r000f-intent, r000f-reset 9/9, r0011-storage
- **Tests.** `tests/r000f-*.cjs`, `tests/r0011-storage.cjs`
- **Unknowns.** native tab order and screen reader
- **Findings.** [PRA-F-04](docs/audit/post-rlgwo/FINDINGS.md#pra-f-04)

<a id="ism-cfg-004"></a>
### ISM-CFG-004 — Settings place search, GPS, candidate cycling and Reset intent

Original audit: **N21** · Lane papers: [B](docs/audit/post-rlgwo/lanes/B-weather-location.md), [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **DWE / PEX / EEV** · Historical disposition: *partly resolved*

- **Scope and decision.** Lookup ownership and the last-explicit-intent rule for location in the settings panel.
- **Sources.** `src/native/index.html` state ~L3907-3911, `_invalidateSetLocation`/`_captureSetLookup`/`_ownsSetLookup` ~L3942-3946, `_runSetSearch` ~L3976, `_showSetCand` ~L3990, label input L4063-4066, `_usePrecise` ~L4105-4121, `_resetLocal` L4122-4144
- **State dimensions.** owner `{session, edit, seq}`; candidates; `_setLocationEvidence/_Origin/_Saved`; `_setPrefVersions`; `_geoPermission`, `_geoLastError`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | Reset | `clearLocal` ok | publish "cleared" → coarse detect → owner check → merge newer prefs → `applyConfig(c,{save:false,reset:true})` → owner check → repopulate |
  | label/lat/lon input during Reset | — | continuation invalidated (label too, despite the comment at L4063) |
  | close during Reset | `_setDirty` | commits stale pre-Reset coordinates (PRA-F-04) |

- **Guards.** owner checks after each await
- **Actors and ownership.** user, coarse detect, GPS
- **Effects.** runtime config, storage
- **Invariants.** claimed: the last explicit location intent wins (violated, PRA-F-04)
- **Failure and recovery.** detect failure → "Enter your location."
- **Invalid, duplicate, stale or concurrent risks.** runtime ≠ storage after Reset + close (F-C04); stale "Saved browser position" label (OM-04); `_geoLastError` sticky (OM-05)
- **Status evidence.** D: R000F/R0026 contracts state the intent rule the code does not keep on this path · I: partly explicit · V: unit + mutation; reset-then-dirty-close untested
- **Work orders.** R0026 (issue 68); R0003 (`reset:true`); R000F
- **Accepted evidence.** r000f-intent 21/21, r000f-reset 9/9, config-effects-*, r0003-ownership; stubbed native (R0026 ES26-13)
- **Tests.** `tests/r000f-intent.cjs`, `tests/r000f-reset.cjs`
- **Observed facts.** probes C reset-close/reset-label (re-run): close re-persists lat 24.4672 method 3 after Reset; typing a name during Reset's apply await reverts the runtime from 40.7 to 24.4672
- **Unknowns.** native behaviour
- **Findings.** [PRA-F-04](docs/audit/post-rlgwo/FINDINGS.md#pra-f-04)

<a id="ism-cfg-005"></a>
### ISM-CFG-005 — Persistence outcome and persistent warning publication

Original audit: **N22** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / EEV / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Never claim persistence after a failed save, nor clearing after a failed reset.
- **Sources.** `src/native/index.html` `_persistenceMessage` ~L3915 … `_publishPersistence` ~L3934-3940
- **State dimensions.** `_persistOutcome{operation, status: saved|cleared|session-only|reset-failed, error}`; `_storageErr`; hint; buckle `persist-warning`
- **Actors and ownership.** `applyConfig`, `_resetLocal`
- **Effects.** status text, gear `!`
- **Invariants.** the hint composes with the outcome, not over it
- **Invalid, duplicate, stale or concurrent risks.** `qaState()` performs a storage write probe (PRA-F-15)
- **Status evidence.** D: R0011 certificate · I: explicit · V: unit + mutation
- **Work orders.** none after f71fef6c (R0011 before)
- **Accepted evidence.** r0011-storage 18/18, r0011-mutations
- **Tests.** `tests/r0011-storage.cjs`
- **Observed facts.** probe C P2: status "Saved settings cleared. / Detecting your area…" while runtime keeps the old site
- **Findings.** [PRA-F-04](docs/audit/post-rlgwo/FINDINGS.md#pra-f-04), [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

<a id="ism-cfg-006"></a>
### ISM-CFG-006 — Document-hash direct reads parallel to the resolved CONFIG (seed, diagnostics)

Original audit: **new (NEW-C-01)** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / IMS / IMS** · Historical disposition: *new*

- **Scope and decision.** Consumers that read `URLSearchParams(location.hash)` instead of `CONFIG`.
- **Sources.** `src/native/index.html` `q` ~L677; `seed` reads ~L2190, ~L2759, ~L2772; SIM/debug flags ~L770ff
- **State dimensions.** two authorities for `seed`: fragment vs `CONFIG.seed`
- **Actors and ownership.** renderer
- **Effects.** cloud/star seeds
- **Invalid, duplicate, stale or concurrent risks.** `CONFIG.seed` has no runtime consumer yet a `seed` difference is classified broad (PRA-F-20)
- **Status evidence.** D: R0003 table row · I: implicit · V: none
- **Work orders.** R0003 (table row admits it)
- **Accepted evidence.** table test only
- **Hypotheses.** low materiality: the form always proposes `CONFIG.seed`
- **Findings.** [PRA-F-20](docs/audit/post-rlgwo/FINDINGS.md#pra-f-20)

<a id="ism-cfg-007"></a>
### ISM-CFG-007 — Builder mode, form, serialisation and preview publication

Original audit: **C05** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** When the builder issues a new preview navigation and what the export contains.
- **Sources.** `src/native/builder.html` `formConfig` ~L205, `hash` ~L212, `snippet` ~L215, `issued`/`previewIdentity` ~L223, `draftInvalid` ~L229, `refuseInvalid` ~L245, `issuePreview` ~L257, `update` ~L263, `setMode` ~L271
- **State dimensions.** draft; validity; export `#code`; issue receipt `issued{identity,src,allow,hash,rev}`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | equivalent input/change | identity equal | export refreshed, no navigation |
  | genuine change | — | one `issuePreview` (`allow` before `src`) |
  | invalid draft | — | export and preview retained; Copy/Open/Install refuse |
  | Refresh | — | re-issue last valid with new `?r=` |

- **Guards.** one serializer (`SalahConfig.serialize`)
- **Actors and ownership.** user
- **Effects.** iframe navigation, snippet
- **Invariants.** iframe 325×530; `allow="geolocation"` only in local mode; `issued` never means loaded
- **Failure and recovery.** throwing `src` setter leaves no record
- **Invalid, duplicate, stale or concurrent risks.** the serializer never emits `tz`, so every portable embed boots on the default hint (OM-02, PRA-F-08)
- **Status evidence.** D: R000F · I: CF05 fixed · V: before/after native control + mutants + review
- **Work orders.** R000F (issue 15, PR 80, merge 32f97b06)
- **Accepted evidence.** builder-preview-publication(+mutations) pass; native Chromium 148 / Firefox 153 on byte-identical builder `873e8ded…`; independent exact-tree review PASS_WITH_FINDINGS
- **Tests.** `tests/builder-preview-publication*.test.cjs`
- **Observed facts.** `serialize` (`config.js` ~L182-206) contains no `tz` (integrator check)
- **Unknowns.** headed device behaviour
- **Findings.** [PRA-F-08](docs/audit/post-rlgwo/FINDINGS.md#pra-f-08)

<a id="ism-cfg-008"></a>
### ISM-CFG-008 — Builder edit ownership, candidate cycle and automatic fills (reverse geocode)

Original audit: **C06** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** Which asynchronous completion may write the builder form.
- **Sources.** `src/native/builder.html` `captureLookup/ownsLookup` ~L330, `doSearch` ~L353, `fillNameFromCoords` L383-398, lat/lon input L399, `locate` ~L496, `detectArea` ~L514
- **State dimensions.** `locationEdit`, `srchSeq`, candidates, timers (1 s, 700 ms, 4 s), `labelAuto`/`methodAuto`, `builderLocation`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | coordinate edit | — | `builderLocation=null`; reverse lookup after 700 ms |
  | reverse reply | `ownsLookup` | any JSON adopted; `methodAuto` → `continentCode==="NA"?"2":"4"` (L395) |

- **Guards.** owner check after each await
- **Actors and ownership.** user, BigDataCloud
- **Effects.** label, method, export
- **Failure and recovery.** failures swallowed (L397)
- **Invalid, duplicate, stale or concurrent risks.** error body flips the auto method (PRA-F-05); local-mode dimmed coordinates still sent to BigDataCloud
- **Status evidence.** D: R000F/R0026 · I: ownership explicit, reverse transport implicit · V: reverse error path untested
- **Work orders.** R0026; R000F
- **Accepted evidence.** r000f-intent, r000f-mutations, location-admission-*
- **Tests.** `tests/r000f-intent.cjs`
- **Observed facts.** probe C reverse-error (re-run): `{status:429}` body changes export `method=2` → `method=4`; reset-close P3: one reverse request from a dimmed local-mode edit
- **Unknowns.** real provider error body shape
- **Findings.** [PRA-F-05](docs/audit/post-rlgwo/FINDINGS.md#pra-f-05)

<a id="ism-cfg-009"></a>
### ISM-CFG-009 — Clipboard attempts, fallback and expiring feedback

Original audit: **C07** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **PEX / EEV / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Copy outcomes per button.
- **Sources.** `src/native/builder.html` `copyText` ~L450-468, `copyActions`/`copyArtifact` ~L471-491
- **State dimensions.** per-button `{seq,timer}`; disabled; tip; recovery box
- **Guards.** sequence
- **Actors and ownership.** user
- **Effects.** clipboard, tips
- **Invariants.** an older attempt cannot touch a newer one; textarea removed in `finally`
- **Failure and recovery.** recovery box keeps the payload
- **Invalid, duplicate, stale or concurrent risks.** a "copied ✓" tip can outlive a later invalid draft (R000F F4)
- **Status evidence.** D: comments + R0012 · I: explicit · V: unit + mutation
- **Work orders.** R000F (`refuseInvalid`)
- **Accepted evidence.** r0012-clipboard 11/11, r0012-effects 3/3, mutation suites
- **Tests.** `tests/r0012-*.cjs`
- **Unknowns.** native clipboard permission

<a id="ism-cfg-010"></a>
### ISM-CFG-010 — Builder ↔ widget preview handoff and the 325×530 geometry contract

Original audit: **new (NEW-C-02; extended by OM-06)** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **DWE / PEX / PEX** · Historical disposition: *new*

- **Scope and decision.** How a builder draft reaches a running widget and where the card geometry is fixed.
- **Sources.** `src/native/builder.html` `base` ~L201, iframe ~L166-167, snippet ~L215; `presets/salah-widget.tablissng.json` ~L9; `README.md` ~L564-575; geometry literals (OM-06) `src/native/index.html` ~L482, ~L520-554, ~L2072, ~L2088, ~L2986; `real-sky/native-contract.mjs` ~L20, `native-host.mjs`, `native-composition.mjs`, `native-first-paint.mjs`, `native-preview.mjs`, `native-host-hooks.js` ~L35
- **State dimensions.** preview `base?r=N#hash`; no `hashchange` listener (reload required); same-origin iframe (no sandbox)
- **Actors and ownership.** builder
- **Effects.** preview widget; in `#local=1` the preview uses and can write the visitor's own saved settings
- **Invariants.** 325×530 in builder iframe, snippet, README current snippets and preset (AGENTS forbidden regression)
- **Invalid, duplicate, stale or concurrent risks.** README V1 snippet is 330×534 and says "change only `src`" for the current version (PRA-F-18); the same literal is duplicated across renderer modules without a shared constant (OM-06)
- **Status evidence.** D: AGENTS rule contradicted by the README V1 snippet · I: static literals · V: current snippets only
- **Work orders.** R000F (ES0F-15)
- **Accepted evidence.** R000F invariants scenario (current snippets only); native layout cell
- **Tests.** R000F `invariants` scenario
- **Observed facts.** README L571 `width:330px;height:534px`, L575 "change only `src`" (integrator check); values agree across modules at baseline (OM-06)
- **Findings.** [PRA-F-18](docs/audit/post-rlgwo/FINDINGS.md#pra-f-18)

## Sky, cloud, star and optical rendering (`ISM-SKY`)

<a id="ism-sky-001"></a>
### ISM-SKY-001 — Sky scene identity, first-document warrant and renderer-surface commit

Original audit: **N13** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **PEX / PEX / EIV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** When an accepted celestial scene is the scene, when transitions are suppressed and when the Moon surface class may show.
- **Sources.** `src/native/index.html` `skySceneIdentity` L2217-2220, `beginSkyScene` L2225-2232, `updateSkySurface` L2236-2241, `commitSkyScene` ~L2242-2252, `paintCelestialWithoutTimetable` ~L3017-3040, `paint` adoption L3244-3246, `boot` ~L3779-3849; `tools/build_native.py` ~L72-73 injects `SalahSkyPreview.clear` + `SalahRealSky.invalidate` into `beginSkyScene`
- **State dimensions.** `_skySceneKey`; `_skyCommitted`; `_skyMoonPresence`; `_skyInitialDocument` (one-use); classes `sky-pending`, `sky-initializing`, `moon-ready`, `mask-on`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | boot / broad apply / `SalahClock.set` | — | `beginSkyScene`: pending classes, key null, uncommit, cloud receipt withdrawn |
  | paint sees identity ≠ key | identity ≠ null | `beginSkyScene(_skyInitialDocument)` then adopt key |
  | `tz` hint → provider zone (boot, after `finishInitialSkyDocument` L3827) | identity contains `tz` | second scene per boot; Moon invalidation non-initial (OM-01, PRA-F-08) |
  | `commitSkyScene` | not committed, key set, fresh Moon observation, star key = scene key | paint clouds, remove pending classes |

- **Guards.** identity equality
- **Actors and ownership.** boot, `applyConfig`, `paint`
- **Effects.** transition suppression, Moon reveal, cloud receipt
- **Invariants.** no stale target becomes current by association; initial warrant is one-use
- **Failure and recovery.** a never-met commit precondition leaves `sky-initializing` (does not hide content)
- **Invalid, duplicate, stale or concurrent risks.** identity carries `tz`, which an ordinary wall-clock sky does not need astronomically (OM-01)
- **Status evidence.** D: comments + R0021 contract · I: partly explicit · V: unit + R0021 native cells (default-zone fixtures only)
- **Work orders.** R000B (cloud receipt withdrawal, ea9f8300); R0003 (presentation path skips the scene reset)
- **Accepted evidence.** r0021-reveal 17/18 (the failing case is a stale byte pin); R0021 native first-boot/live-handoff cells
- **Tests.** `tests/r0021-reveal.cjs`, `tests/real-sky/native-first-paint.test.mjs`
- **Observed facts.** integrator: `skySceneIdentity` includes `tz` (L2219); `paint` begins a new scene on any identity change (L3246); `finishInitialSkyDocument()` at L3827 precedes `loadPrayerData` (L3846) which writes `tz` (L3676/L3691)
- **Hypotheses.** brief visible re-pending of celestial layers on non-default-zone boots
- **Unknowns.** pixel visibility; lifecycle coalescing
- **Findings.** [PRA-F-08](docs/audit/post-rlgwo/FINDINGS.md#pra-f-08)

<a id="ism-sky-002"></a>
### ISM-SKY-002 — Star projection / catalogue contract and held appearance

Original audit: **N14** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **DWE / PEX / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Which component owns star pixels and twinkle in the shipped app.
- **Sources.** source `src/native/index.html` ~L2102-2214; generated replacement `tools/build_native.py` L51-67; CSS hide L84; `real-sky/native-contract.mjs` L20 `scintillation:{strength:0}`; `real-sky/native-star-preview.mjs`
- **State dimensions.** generated: `_starProjectionKey`, `_starsProjected`; source-only: catalogue, `_starLightKey`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `projectStars(date)` | — | records key/validity; invalid → `SalahRealSky.invalidate` |
  | `refreshStarAppearance` | — | no-op in generated app |

- **Actors and ownership.** generator, refined/preview renderers
- **Effects.** star pixels
- **Invariants.** one star owner in the shipped app
- **Invalid, duplicate, stale or concurrent risks.** no scintillation producer in the shipped app (grep: none in preview modules; refined strength 0); AGENTS gate I and DESIGN.md L438-450 describe CSS twinkle (PRA-F-11)
- **Status evidence.** D: DESIGN.md stale; `docs/real-sky/QUALIFICATION.md` ~L130-132 discloses the CP9 setting · I: digest-free text substitution · V: unit
- **Work orders.** none
- **Accepted evidence.** `tests/real-sky/cp9-scintillation.test.mjs` (asserts disabled strength); `r0022-lunar-consumers` star cases fail against the generated entry (since before f71fef6c)
- **Tests.** `tests/real-sky/cp9-scintillation.test.mjs`, `tests/r0022-lunar-consumers.cjs`
- **Observed facts.** integrator confirmed strength 0, CSS `display:none!important`, and no `scintill`/`twinkl` token in `native-star-preview.mjs`/`native-preview*.mjs`/`native-host.mjs`
- **Unknowns.** native visual star motion beyond re-projection under `timeScale`
- **Findings.** [PRA-F-11](docs/audit/post-rlgwo/FINDINGS.md#pra-f-11)

<a id="ism-sky-003"></a>
### ISM-SKY-003 — Cloud population, motion integration, coverage and paint cache

Original audit: **N15** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Procedural cloud deck: population identity, wind integration, coverage easing/withdrawal, raster and density.
- **Sources.** `src/native/index.html` `_cloudMotion` ~L2756, `cloudSceneIdentity` ~L2757-2761, `advanceCloudMotion` ~L2768-2795, `paintClouds` ~L2817-2877, `applyCloudState` ~L3222-3241, loop ~L3881-3884
- **State dimensions.** population key `[lat,lon,seed,wall|anchor]`; `phase[3]`, `life[3]`, `lastRt`, `paused`, `reduced`; coverage `cov*`/`tgt*`; `_cloudReady`; `_cloudDirty`; `_colDens`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | identity change | — | reseed, reset phases |
  | visible healthy Δ ≤ 2 s | not reduced | integrate wind × Δ × rate |
  | first admitted deck | — | snap coverage |
  | later deck | — | ease 0.08 per paint |
  | decision unavailable | — | withdraw immediately |

- **Actors and ownership.** loop, `applyCloudState`
- **Effects.** cloud canvas, rain density
- **Invariants.** weather refresh changes coverage/light, never population; hidden time accumulates no travel
- **Invalid, duplicate, stale or concurrent risks.** easing time constant depends on paint cadence; quarter-hour withdrawal + snap (PRA-F-03)
- **Status evidence.** D: comments + R000B · I: partly explicit · V: unit
- **Work orders.** R000B (withdrawal through the receipt); R0025 (issue 37, before)
- **Accepted evidence.** r0025-context/-continuity/-lifecycle exit 0
- **Tests.** `tests/r0025-*.cjs`, `tests/r0024-cloud-expiry.test.cjs`
- **Unknowns.** continuity across bfcache restore
- **Findings.** [PRA-F-03](docs/audit/post-rlgwo/FINDINGS.md#pra-f-03)

<a id="ism-sky-004"></a>
### ISM-SKY-004 — Precipitation population, cloud-origin gating and lightning bucket

Original audit: **N16** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Which particles show and when lightning may flash.
- **Sources.** `src/native/index.html` `buildWeather` ~L2255-2268, `tieRainToClouds` ~L2882-2894, `genLightning` ~L3460-3475, `paint` ~L3302-3305, `withdrawWeatherEffects` L2722-2729
- **State dimensions.** particle pool; `_rainTiedFx`; per-particle `display`; `data-precip`, `data-lightning`; `_lastBolt`
- **Guards.** column density > 0.16 × max and max ≥ 2; lightning only with `visualPermissions.lightning`
- **Actors and ownership.** `paint`
- **Effects.** particles, flash
- **Invariants.** model thunder never authorises lightning
- **Invalid, duplicate, stale or concurrent risks.** per-particle `style.left` parse each paint (bounded, 72 nodes)
- **Status evidence.** D: comments + DESIGN.md · I: implicit · V: unit
- **Work orders.** R000B (effects withdrawn with the receipt)
- **Accepted evidence.** r0024-particle-origin, r000c-weather
- **Tests.** `tests/r0024-particle-origin.test.cjs`
- **Unknowns.** CSS animation completion not observed

<a id="ism-sky-005"></a>
### ISM-SKY-005 — Atmosphere publication, optical fade state and last-consumed diagnostics

Original audit: **N17** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** Published CSS variables and the diagnostics that report what was consumed.
- **Sources.** `src/native/index.html` `nativeSolarPresentation` ~L2909, `paintLunarOptic` L3004-3016, `atmosphere` ~L3041-3220, `paint` ~L3242-3325, `applyTheme` ~L3327-3338, `qaState` ~L3539-3624
- **State dimensions.** published CSS variables; per-optic `visibility:inherit`; `_lastMoonPaint`; `_lastWeatherEffects`; `_lastRender`
- **Actors and ownership.** `paint`
- **Effects.** CSS variables
- **Invariants.** physical eligibility separate from aesthetic opacity; diagnostics report last-consumed values
- **Failure and recovery.** `applyTheme` seals its receipt then rethrows (L3336); the native loop does not catch it
- **Invalid, duplicate, stale or concurrent risks.** diagnostic side effects (PRA-F-15)
- **Status evidence.** D: comments + issue contracts · I: partly explicit · V: unit
- **Work orders.** R000B; R001D (issue 29, before)
- **Accepted evidence.** r001d-lifecycle exit 0; r0022-lunar-consumers 24/26
- **Tests.** `tests/r001d-lifecycle.cjs`, `tests/r0022-lunar-consumers.cjs`
- **Findings.** [PRA-F-01](docs/audit/post-rlgwo/FINDINGS.md#pra-f-01), [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

<a id="ism-sky-006"></a>
### ISM-SKY-006 — Native sky snapshot identity, epoch, freshness and throughput admission

Original audit: **R01** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / EEV / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Which refined-sky worker result may be accepted and displayed.
- **Sources.** `real-sky/native-lifecycle.mjs` ~L8-93 (rate-throughput guard ~L24-26); `real-sky/native-contract.mjs` `nativeIdentity` ~L3-9, `nativeJob` ~L10-23; `real-sky/native-host-hooks.js` `capture` ~L20-49
- **State dimensions.** `epoch`; `identity`; `observed{now,utcMs,rate,paused}`; `latest`/`pending`/`displayed`; `availability`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | identity change / pause toggle / clock jump > 1 s | — | epoch++ → host `clear` |
  | displayed older than 30 s | — | `displayed=null` |
  | stale result | — | rejected; `rate-throughput` only if same epoch and identity, rate > 1, age > 30 s |

- **Guards.** epoch + identity
- **Actors and ownership.** refined host
- **Effects.** refined frame availability
- **Invariants.** no result for another epoch/identity is accepted
- **Invalid, duplicate, stale or concurrent risks.** identity includes `rh`, `cloud`, `code`, `wind`, which `nativeJob` never reads (it reads `vis`, `temp`, `src`); identity faster than one render never accepts and is not reported (PRA-F-10)
- **Status evidence.** D: comments · I: single fenced class · V: unit + one native throughput record
- **Work orders.** none (files unchanged)
- **Accepted evidence.** `tests/real-sky/native-lifecycle.test.mjs`, `native-contract.test.mjs`; R0027 native run1 recorded `rate-throughput` at 120×
- **Tests.** `tests/real-sky/native-lifecycle.test.mjs`
- **Observed facts.** integrator grep of `nativeJob`: only `w.vis`, `w.temp`, `w.src`
- **Findings.** [PRA-F-10](docs/audit/post-rlgwo/FINDINGS.md#pra-f-10)

<a id="ism-sky-007"></a>
### ISM-SKY-007 — Latest-only serialised render queue

Original audit: **R02** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / EEV / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Latest-only serialised render queue
- **Sources.** `real-sky/core/src/latest-render-queue.mjs` ~L1-31 (copied core)
- **State dimensions.** `#next`, `#busy`, `#pending` (≤1), `#disposed`
- **Invalid, duplicate, stale or concurrent risks.** a throwing `onResult` is routed to `onError` for the same id (consistent)
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-008"></a>
### ISM-SKY-008 — Native asset loader generation, timeout, suspension and retry

Original audit: **R03** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / EEV / EIV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Asset pack loading, suspension and retry for the refined sky.
- **Sources.** `real-sky/native-assets.mjs` ~L4-33
- **State dimensions.** `generation`, `controller`, `suspended`, `disposed`, `value.status` {idle, loading, ready, unavailable, suspended, disposed, superseded}
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | retry | — | abort prior, `onReset`, race load vs 15 s |
  | suspend | — | generation++, abort, reset |
  | resume | — | retry once |

- **Guards.** generation
- **Actors and ownership.** page lifecycle, construction
- **Effects.** asset readiness
- **Failure and recovery.** a throwing `start(pack)` publishes `unavailable` after `onReset`
- **Status evidence.** D: comments + R0021 · I: explicit · V: unit + R0021 native
- **Work orders.** R0021 (issue 33) touched the adjoining reset (ISM-SKY-009), not these lines
- **Accepted evidence.** `tests/real-sky/native-assets.test.mjs`, `native-construction-ownership.test.mjs`; R0021 native cells
- **Tests.** `tests/real-sky/native-assets.test.mjs`

<a id="ism-sky-009"></a>
### ISM-SKY-009 — Native asset script, inline pack and page-lifecycle ownership

Original audit: **R04** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / PEX / EEV** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Reset/suspend/resume of the refined sky across pagehide/pageshow.
- **Sources.** `real-sky/native-assets.mjs` ~L38-81 (`reset` ~L45, `pagehide`/`pageshow` ~L70-71)
- **State dimensions.** inline pack consumed once; per-generation script; `firstFrame` rAF id; listeners
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | pagehide | — | cancel first frame → suspend → refined `dispose({previewHandoff:false})` |
  | persisted pageshow | — | resume → retry |

- **Guards.** registry slot cleared only if it still holds the retired instance
- **Actors and ownership.** page lifecycle
- **Effects.** refined sky lifetime
- **Invalid, duplicate, stale or concurrent risks.** preview owner not suspended on pagehide (ISM-SKY-030)
- **Status evidence.** D: comments + R0021 · I: partly explicit · V: unit + partial native
- **Work orders.** R0021 (dcc8206b)
- **Accepted evidence.** unit + R0021 native (non-persisted navigation PASS; persisted restore only synthetic)
- **Tests.** `tests/real-sky/cp9-page-lifecycle.test.mjs`
- **Unknowns.** bfcache behaviour
- **Findings.** [PRA-F-22](docs/audit/post-rlgwo/FINDINGS.md#pra-f-22)

<a id="ism-sky-010"></a>
### ISM-SKY-010 — Reference worker client boot, RPC deadlines and fallback mode

Original audit: **R05** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Reference worker client boot, RPC deadlines and fallback mode
- **Sources.** `real-sky/core/src/reference-worker-client.mjs` ~L1-53; `real-sky/native-worker-policy.mjs` ~L1-7
- **State dimensions.** `#mode` {starting, worker, main-thread-fallback, disposed}, `#ready`, `#pending`, `#bootTimer`, `#warnings`
- **Invalid, duplicate, stale or concurrent risks.** 15 s boot and render timeouts; `requireNativeWorker` throws (no main-thread physics); `#warnings` uncapped but practically bounded
- **Status evidence.** D: comments only · I: as original catalogue · V: `tests/real-sky/cp9-worker-policy.test.mjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `tests/real-sky/cp9-worker-policy.test.mjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-011"></a>
### ISM-SKY-011 — Sky worker boot, engine ownership and transferable raster response

Original audit: **R06** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Sky worker boot, engine ownership and transferable raster response
- **Sources.** `tools/build_native.py` ~L31-34 (wrapper text), generated `real-sky/native-worker.js`; `real-sky/native-engine.mjs` ~L7-27
- **State dimensions.** boot → `ready`; render before boot → error; unhandled rejection → `fatal`
- **Invalid, duplicate, stale or concurrent risks.** `catalogue.emitters` re-filters the catalogue on every render (~L25)
- **Status evidence.** D: comments only · I: as original catalogue · V: `tests/real-sky/native-engine.test.mjs`
- **Work orders.** R0027 transform regenerated the worker bytes only
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `tests/real-sky/native-engine.test.mjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-012"></a>
### ISM-SKY-012 — Diffuse asset admission, cancellation and content cache

Original audit: **R07** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Diffuse asset admission, cancellation and content cache
- **Sources.** `real-sky/core/src/diffuse-assets.mjs` ~L14-69
- **State dimensions.** cache bounded to manifest entries (at most three)
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-013"></a>
### ISM-SKY-013 — Sky catalogue replacement generation and last-result authority

Original audit: **R08** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / EEV / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Sky catalogue replacement generation and last-result authority
- **Sources.** `real-sky/core/src/scene.mjs` ~L11-21
- **State dimensions.** generation; last result
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-014"></a>
### ISM-SKY-014 — Engine binding selection, load keys and declared physical fallback

Original audit: **R09** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Engine binding selection, load keys and declared physical fallback
- **Sources.** `real-sky/native-engine.mjs` ~L10-14; `real-sky/core/integration/resilient-sky-bridge.mjs` ~L7-18; `physical-sky-bridge.mjs` ~L5-18
- **State dimensions.** `loaded` set after the first `store.load` regardless of outcome
- **Invalid, duplicate, stale or concurrent risks.** a failed embedded tier stays on the declared CP6 fallback until a full asset retry
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-015"></a>
### ISM-SKY-015 — Refined sky construction, accepted frame, displayed frame and DOM commit

Original audit: **R10** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** Construction, acceptance, composition and DOM commit of the refined sky.
- **Sources.** `real-sky/native-host.mjs` `startNativeSky` ~L60-272 (custody ~L70-71, unwind ~L267-271, `animate` try/catch ~L253, dispose ~L263-264)
- **State dimensions.** `frame/job` (accepted); `paintedFrame/paintedJob` (displayed); `pendingJob`; `status.status` {loading, pending, ready, unavailable, retiring, disposed}; `status.retirement`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `accept(result)` | current, ready | store frame; `compose()` |
  | `compose` | not disposed, cloud receipt current before and after detail compose | encode, mask, publish |
  | `failure(e)` | — | retain displayed job only if current, else clear |
  | `dispose` | not disposed/retiring | record retirement, release all, rethrow first error |

- **Guards.** cloud receipt fences (ISM-WX-005)
- **Actors and ownership.** lifecycle, asset loader
- **Effects.** canvas pixels, classes
- **Invariants.** no orphan canvas/worker after failed construction
- **Failure and recovery.** `animate` always reschedules
- **Invalid, duplicate, stale or concurrent risks.** per-compose allocations and PNG mask encode up to 20 Hz (PRA-F-34)
- **Status evidence.** D: comments + R0021 lifetime map · I: RF02 fixed (canvas after context; unwind) · V: before/after tests + mutants + native + review
- **Work orders.** R0021 (issue 33; dcc8206b, 145b7ba9; merges 294d2d37, 5279958a); R000B (ea9f8300)
- **Accepted evidence.** `tests/real-sky/native-construction-ownership.test.mjs` (pass); 17/17 mutants killed per R0021; native construction/census/retirement cells Chromium + Firefox; independent review PASS_WITH_FINDINGS (R0021 §F)
- **Tests.** `tests/real-sky/native-construction-ownership.test.mjs`, `native-host-composition.test.mjs`
- **Findings.** [PRA-F-34](docs/audit/post-rlgwo/FINDINGS.md#pra-f-34)

<a id="ism-sky-016"></a>
### ISM-SKY-016 — Solar cloud-mask decode-before-publish transaction

Original audit: **R11** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** Whether a decoded mask may be displayed.
- **Sources.** `real-sky/native-composition.mjs` `NativeSolarMaskPublication` ~L36-68
- **State dimensions.** `revision`, `pending{mask,image}`, `pendingContext`, `decoded`, `displayed`, `disposed`
- **Guards.** revision
- **Actors and ownership.** refined/preview hosts
- **Effects.** mask
- **Invalid, duplicate, stale or concurrent risks.** no decode deadline (PRA-F-36)
- **Status evidence.** D: comments + R0021 TA3 · I: partly explicit · V: unit
- **Work orders.** R000B (`pendingContext`)
- **Accepted evidence.** `cp9-mask-performance.test.mjs`, `native-composition.test.mjs`
- **Tests.** see evidence
- **Unknowns.** browser decode settlement
- **Findings.** [PRA-F-36](docs/audit/post-rlgwo/FINDINGS.md#pra-f-36)

<a id="ism-sky-017"></a>
### ISM-SKY-017 — Preview base, pending paint, current display and shared DOM handoff

Original audit: **R12** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *partly resolved*

- **Scope and decision.** The synchronous numerical preview that bridges to the refined sky.
- **Sources.** `real-sky/native-preview-host.mjs` ~L10-194 (`update` ~L120-128, `present`/`tick` ~L166-167, `dispose` ~L186, registry release ~L187 only via the constructor catch ~L190)
- **State dimensions.** `value`, `pendingValue`, `previewFrame`, catalogue revisions, `nativeDriven`, `disposed`, `status.deadlineMisses` (≤8); classes `real-sky-preview-ready`, `real-sky-awaiting-input`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `present(now)` | not composed and (catalogue changed, |rate|>10, no value, not current, >100 ms) | `update()` |
  | `update` with no scene/target or paused | — | `clear()` + awaiting-input class |

- **Actors and ownership.** own `tick`, then the native loop
- **Effects.** preview canvas
- **Invalid, duplicate, stale or concurrent risks.** in bare mode `update→clear` (cloud reconcile, Moon detail clear) every frame (PRA-F-22); healthy `dispose` leaves `window.SalahSkyPreview` set (no shipped caller)
- **Status evidence.** D: comments + R0021 · I: partly explicit · V: unit
- **Work orders.** R0021 (10.3); R000B
- **Accepted evidence.** `tests/real-sky/native-preview-host.test.mjs` (construction cases pass)
- **Tests.** `tests/real-sky/native-preview-host.test.mjs`
- **Observed facts.** integrator read L120-128, L164-190
- **Findings.** [PRA-F-22](docs/audit/post-rlgwo/FINDINGS.md#pra-f-22)

<a id="ism-sky-018"></a>
### ISM-SKY-018 — Asynchronous preview catalogue admission revision

Original audit: **R13** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Asynchronous preview catalogue admission revision
- **Sources.** `real-sky/native-preview-host.mjs` `admitCatalogue` ~L173-185; `real-sky/native-star-preview.mjs`
- **State dimensions.** `catalogueRequest` generation; identical bootstrap does not bump revision
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-019"></a>
### ISM-SKY-019 — Document head background and initial lunar CSS lease (first paint)

Original audit: **R14** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Head-time background before the native scene exists.
- **Sources.** `real-sky/native-first-paint.mjs` ~L10-50 (identity `[lat,lon,c.tz||'America/New_York','wall']` ~L18; `Number(params.get(k))` ~L15); retirement `native-preview-host.mjs` ~L39-46
- **State dimensions.** `SalahFirstPaint` value / error; skipped for `simTime|simDate|timeScale`
- **Actors and ownership.** head script
- **Effects.** initial CSS pixels
- **Invariants.** retired on first successful preview publish or failed currentness
- **Failure and recovery.** Moon head failure records `SalahFirstPaint.error` (ISM-MOON-016)
- **Invalid, duplicate, stale or concurrent risks.** blank camera parameter becomes 0 here but `NaN`/throw natively; `simDate` (not a native parameter) suppresses first paint; reduced-motion and identity formats duplicated (OM-07, PRA-F-37)
- **Status evidence.** D: comments · I: implicit · V: unit, default zone only
- **Work orders.** none
- **Accepted evidence.** `tests/real-sky/native-first-paint.test.mjs` (default-zone fixtures only)
- **Tests.** `tests/real-sky/native-first-paint.test.mjs`
- **Findings.** [PRA-F-37](docs/audit/post-rlgwo/FINDINGS.md#pra-f-37)

<a id="ism-sky-020"></a>
### ISM-SKY-020 — Native snapshot adapter and single paint-hook installation

Original audit: **R15** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** How renderer owners read native state.
- **Sources.** `real-sky/native-host-hooks.js` ~L5-68
- **State dimensions.** `capture(false)` (no layout) vs `capture()`; `notify()` after each `commitSkyScene`
- **Actors and ownership.** refined/preview hosts
- **Invalid, duplicate, stale or concurrent risks.** `reconcileClouds()` can withdraw cloud state and repaint the header from inside renderer capture/compose (PRA-F-15)
- **Status evidence.** D: comments · I: implicit · V: unit
- **Work orders.** R000B (`reconcileClouds`, `cloudsCurrent`)
- **Accepted evidence.** `tests/r000b-sky-withdrawal.test.mjs` pass
- **Tests.** `tests/r000b-sky-withdrawal.test.mjs`
- **Findings.** [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

<a id="ism-sky-021"></a>
### ISM-SKY-021 — Bounded camera/lunar sampling geometry memoisation

Original audit: **R16** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Bounded camera/lunar sampling geometry memoisation
- **Sources.** `real-sky/native-preview.mjs` ~L17-31, ~L362-382
- **State dimensions.** FIFO 4 entries each
- **Invalid, duplicate, stale or concurrent risks.** bounded
- **Status evidence.** D: comments only · I: as original catalogue · V: `tests/real-sky/cp9-presentation-cache.test.mjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `tests/real-sky/cp9-presentation-cache.test.mjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-022"></a>
### ISM-SKY-022 — Preview raster private-byte custody and lazy fields

Original audit: **R17** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Preview raster private-byte custody and lazy fields
- **Sources.** `real-sky/native-star-preview.mjs` ~L20, ~L139-178
- **State dimensions.** `preparedFields` WeakMap
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-023"></a>
### ISM-SKY-023 — Exact immutable encoding-table initialisation

Original audit: **R18** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Exact immutable encoding-table initialisation
- **Sources.** `real-sky/native-host.mjs` ~L11-49; `real-sky/native-encoding.mjs`
- **State dimensions.** one table per realm
- **Status evidence.** D: comments only · I: as original catalogue · V: `native-encoding.test.mjs`, `native-host-encoding.test.mjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `native-encoding.test.mjs`, `native-host-encoding.test.mjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-024"></a>
### ISM-SKY-024 — Spectral selection and B–V fit retention

Original audit: **R31** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** Retention of fitted spectra for twilight B–V values.
- **Sources.** authored `tools/native_core_spectral_cache.py` ~L1-49 applied by `tools/build_native.py` ~L15; output `real-sky/core/src/spectral.mjs` ~L9-43
- **State dimensions.** inner `sfFitCache` 0..12,000 (FIFO); outer `sfCache` 0..12,000 (frozen when full)
- **Guards.** source/output digests pinned
- **Actors and ownership.** generator
- **Effects.** memory
- **Invariants.** spectral numbers bit-identical
- **Failure and recovery.** digest drift fails the build before that file is written
- **Invalid, duplicate, stale or concurrent risks.** continuous twilight B–V has ~0 hit rate (ES27-06), so each miss still runs a 48-step bisection
- **Status evidence.** D: R0027 + AGENTS · I: RF03 fixed · V: before/after + mutants + review
- **Work orders.** R0027 (issue 69, PR 82, merge 546d8828; 77014952)
- **Accepted evidence.** spectral-fit-cache-state/-mutations/-generated pass (lane D 183/183 incl. other files); ES27-08 `distinctSampleArrays=24000`; R0027 acceptance reconciliation
- **Tests.** `tests/real-sky/spectral-fit-cache-*.test.mjs`
- **Unknowns.** heap and latency (no measurement claimed)

<a id="ism-sky-025"></a>
### ISM-SKY-025 — Bounded legacy photometry spectral memo

Original audit: **R32** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Bounded legacy photometry spectral memo
- **Sources.** `real-sky/core/src/photometry.mjs` ~L27-35
- **State dimensions.** add below 2048
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-026"></a>
### ISM-SKY-026 — Atmosphere validation capability and weak coefficient memo

Original audit: **R33** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Atmosphere validation capability and weak coefficient memo
- **Sources.** `real-sky/core/src/atmosphere.mjs` ~L7; `sky-background.mjs` ~L14, ~L47
- **State dimensions.** WeakSet/WeakMap by object identity
- **Invalid, duplicate, stale or concurrent risks.** per-job recomputation expected (new object each job)
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-027"></a>
### ISM-SKY-027 — Per-physical-model solar sample grid lifetime

Original audit: **R34** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Per-physical-model solar sample grid lifetime
- **Sources.** `real-sky/core/src/sky-background.mjs` ~L72-96
- **State dimensions.** `grid` Map ≤ 19×36 per model
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-028"></a>
### ISM-SKY-028 — Native target-elevation acceptance lease

Original audit: **R35** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [B](docs/audit/post-rlgwo/lanes/B-weather-location.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Native target-elevation acceptance lease
- **Sources.** `real-sky/native-host-hooks.js` ~L4-9, ~L23; injection `tools/build_native.py` ~L69-71
- **State dimensions.** CP9 elevation bound to generation/coordinates
- **Invalid, duplicate, stale or concurrent risks.** the legacy native copy is unbound (ISM-WX-008)
- **Status evidence.** D: comments only · I: as original catalogue · V: `tests/real-sky/cp9-elevation.test.mjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `tests/real-sky/cp9-elevation.test.mjs`
- **Unknowns.** not re-proved in this audit
- **Findings.** [PRA-F-17](docs/audit/post-rlgwo/FINDINGS.md#pra-f-17)

<a id="ism-sky-029"></a>
### ISM-SKY-029 — Catalogue-bound diffuse resource capability

Original audit: **R36** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Catalogue-bound diffuse resource capability
- **Sources.** `real-sky/core/src/diffuse-binding.mjs` ~L4-18; `registered-starlight.mjs`
- **State dimensions.** capability per catalogue
- **Status evidence.** D: comments only · I: as original catalogue · V: unit tests
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** unit tests
- **Unknowns.** not re-proved in this audit

<a id="ism-sky-030"></a>
### ISM-SKY-030 — Page-lifecycle fan-out across sky owners

Original audit: **new (NEW-D-03)** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md) · Status D / I / V: **PEX / IMS / EEV** · Historical disposition: *new*

- **Scope and decision.** What each sky owner does on pagehide, hide/offscreen and persisted pageshow.
- **Sources.** `real-sky/native-assets.mjs` ~L70-72; `src/native/index.html` L3891-3895; `real-sky/native-host.mjs` ~L255; `real-sky/native-lifecycle.mjs` ~L55; `real-sky/native-preview-host.mjs` (no lifecycle listener)
- **State dimensions.** refined: suspend/resume; loop: visibility + IntersectionObserver; preview: none (relies on `capture().paused`); cloud motion: rebase
- **Actors and ownership.** page lifecycle
- **Effects.** worker re-render on every hide/show
- **Invalid, duplicate, stale or concurrent risks.** preview is a page-lifetime singleton with no suspend; every hide/show withdraws the refined frame (by design) (PRA-F-22)
- **Status evidence.** D: R0021 retirement only · I: distributed · V: unit + partial native
- **Work orders.** R0021 (retirement only)
- **Accepted evidence.** `tests/real-sky/cp9-page-lifecycle.test.mjs` pass; R0021 native non-persisted navigation only ("No restore was obtained in any run")
- **Tests.** `tests/real-sky/cp9-page-lifecycle.test.mjs`
- **Unknowns.** bfcache
- **Findings.** [PRA-F-22](docs/audit/post-rlgwo/FINDINGS.md#pra-f-22)

<a id="ism-sky-031"></a>
### ISM-SKY-031 — Diagnostic telemetry state (debugMotion history, qaState)

Original audit: **new (NEW-D-05; OM-05 adds sticky acquisition flags)** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **DWE / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Diagnostics used as qualification evidence.
- **Sources.** `src/native/index.html` `_motHist` ~L3629-3646 (≤61), `qaState` ~L3539-3624 (storage probe ~L3587; `autoDetectStatus` ~L3586), `_autoDetectStatus` ~L3794-3796; `real-sky/native-host-hooks.js` ~L58-67
- **State dimensions.** bounded history; per-call recomputation; boot-only acquisition flags
- **Actors and ownership.** `&debugMotion=1` (1 Hz), QA drivers
- **Invalid, duplicate, stale or concurrent risks.** in the generated app star telemetry always reports `starΔ 0.000`/`starAnim OFF` (the stub empties `.stars`); `qaState()` writes a storage probe; `autoDetectStatus` can stick at `pending` when a newer generation supersedes boot (OM-05) (PRA-F-11, PRA-F-15)
- **Status evidence.** D: AGENTS/DESIGN describe the source implementation · I: implicit · V: partial
- **Accepted evidence.** r001d-* (lifecycle only)
- **Tests.** `tests/r001d-*.cjs`
- **Findings.** [PRA-F-11](docs/audit/post-rlgwo/FINDINGS.md#pra-f-11), [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

## Moon pipeline (`ISM-MOON`)

<a id="ism-moon-001"></a>
### ISM-MOON-001 — Legacy lunar texture/canvas fallback (dormant generated owner)

Original audit: **N11** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Legacy lunar texture/canvas fallback (dormant generated owner)
- **Sources.** `src/native/index.html` `loadMoonMaps` ~L1892-1907, `renderMoonCalendarFallback` ~L1911-1951, `renderMoonPBR` L1953-1954
- **State dimensions.** `_mAlb/_mNrm`, `_pbrReady`, `_pbrPending`, `_pbrFailed`, `_moonFallbackReady`
- **Invalid, duplicate, stale or concurrent risks.** callbacks test the live runtime slot, so after a wrapper construction failure the legacy path decodes and renders every minute into a hidden `.mphoto` (wasted work); `_pbrFailed` is the only surface-failed input to light eligibility (ISM-MOON-020)
- **Status evidence.** D: comments only · I: as original catalogue · V: VM harness `tests/r0022-lunar-consumers.cjs` exercises this legacy path
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** VM harness `tests/r0022-lunar-consumers.cjs` exercises this legacy path
- **Unknowns.** not re-proved in this audit
- **Findings.** [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13)

<a id="ism-moon-002"></a>
### ISM-MOON-002 — Native lunar geometry production and consumption receipts

Original audit: **N12** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Moon geometry stamps and the receipt of what `applyTheme` consumed.
- **Sources.** `src/native/index.html` `moonGeometryIdentity`/`moonGeometryObservation` ~L2026-2039, `nativeLunarSnapshot`/`renderMoon` ~L2061-2090, `_lastMoonPaint`/`applyTheme` ~L3326-3338, `SalahMoonHost.capture/publish/fallback` ~L4167-4184, minute cadence L3494
- **State dimensions.** `moonSky` + stamp `_epochMin/_min/_context`; `lastMoonMin`; `_lastMoonPaint{status, stage, fresh, observation}`
- **Guards.** observation fresh only if epoch minute, minute and context `[lat,lon,tz]` match
- **Actors and ownership.** `render`
- **Effects.** Moon transforms
- **Invariants.** `applyTheme` seals its receipt at the attempt
- **Invalid, duplicate, stale or concurrent risks.** `render` calls `renderMoon` (L3494) before prayer DOM writes (L3499-3518), not isolated (PRA-F-01); `tz` in the context re-keys on adoption (OM-01)
- **Status evidence.** D: comments + R001D certificate · I: partly explicit · V: unit
- **Work orders.** none since f71fef6c (R001D, R0022 before)
- **Accepted evidence.** `tests/r0022-lunar-consumers.cjs` 24/26 (failures are star-wash cases)
- **Tests.** `tests/r0022-lunar-consumers.cjs`
- **Unknowns.** native pixel/mask alignment
- **Findings.** [PRA-F-01](docs/audit/post-rlgwo/FINDINGS.md#pra-f-01), [PRA-F-08](docs/audit/post-rlgwo/FINDINGS.md#pra-f-08)

<a id="ism-moon-003"></a>
### ISM-MOON-003 — Lunar host accepted / pending / waiting-preview / presentation transaction

Original audit: **R19** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Host authority over the accepted lunar surface and what is displayed.
- **Sources.** `moon/src/moon-native.mjs` state ~L13-16, `capture`…`matches` ~L18-48, `adopt`/`presentation` ~L75-91 (preview adoption L89), `poll` ~L124-144, worker admission ~L193-227, `surface`/`state`/`detailEnabled` ~L274-283; `moon/src/moon-precision.mjs`
- **State dimensions.** `accepted`; `pending`; `waitingPreview`; `epoch`/`serial`; `clock`; `profileMode`; `status.status`; DOM `.mphoto`, `moon-ready`, `mask-on`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | scope/clock/pause change | — | `clear`: epoch++, cancel, fallback |
  | worker preview | current id/scope/scene | stored as `waitingPreview`; adopted only by a read-time `presentation()` |
  | result | `empirical-adaptive` | adopt |
  | stale/duplicate id | — | rejected |

- **Guards.** identity fences
- **Actors and ownership.** native host, worker
- **Effects.** lunar surface
- **Invariants.** accepted is host authority
- **Failure and recovery.** `failed` retains accepted only while it still matches
- **Invalid, duplicate, stale or concurrent risks.** getters `surface()`, `state`, `detailEnabled` adopt and publish (`qaState().moonTruth` reads them) (PRA-F-15)
- **Status evidence.** D: comments · I: partly explicit · V: unit
- **Work orders.** R0021 (captured detail handle)
- **Accepted evidence.** `moon/tests/host.test.cjs` (lane E: `moon/tests` 133/133)
- **Tests.** `moon/tests/host.test.cjs` (L94 asserts surface adoption)
- **Observed facts.** integrator read L89, L275-277
- **Hypotheses.** reveal lag ≤ one render tick
- **Unknowns.** native timing
- **Findings.** [PRA-F-15](docs/audit/post-rlgwo/FINDINGS.md#pra-f-15)

<a id="ism-moon-004"></a>
### ISM-MOON-004 — Lunar runtime installation, worker source, bounded retry and deadlines

Original audit: **R20** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / PEX / EEV** · Historical disposition: *partly resolved*

- **Scope and decision.** Worker start, failure and retry for the lunar runtime.
- **Sources.** `moon/src/moon-native.mjs` `closeWorker`/`failed` ~L55-70, deadlines ~L143 (240 s) and ~L230 (120 s), `start` ~L182-232, `installWorkerSource` ~L251-260, `retry` L282, deferred start ~L291; `tools/build_moon.py` ~L129-131
- **State dimensions.** `MOON_WORKER_SOURCE`; `startFrame`; `worker`/`url`; `ready`; `deadline`; `retryCount` 0..3 (never reset); `status.errors` (≤8); `disposed`
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `installWorkerSource(src)` | length + SHA pin | pin; start via double rAF |
  | `failed` | — | serial++, revoke head, close worker |
  | `retry()` | not disposed, no worker, source, `retryCount<3` | start — called by no product code |

- **Guards.** pins
- **Actors and ownership.** host wrapper
- **Effects.** worker lifetime
- **Failure and recovery.** every worker failure terminal for the page lifetime (PRA-F-12)
- **Invalid, duplicate, stale or concurrent risks.** 240 s render deadline vs 169 s observed Firefox run; refinement tail throws on an empty slot (PRA-F-13)
- **Status evidence.** D: comments + R0021 ES21-06/11 · I: bounds explicit, recovery owner absent · V: unit + driver-driven native
- **Work orders.** R0021 (try/catch unwind, `disposed` getter)
- **Accepted evidence.** host.test.cjs, native-instance-retirement ES21-06; R0021 `moon-asset-failure` cell (retries driven by the QA driver)
- **Tests.** `moon/tests/host.test.cjs`, `moon/tests/native-instance-retirement.test.cjs`
- **Unknowns.** field failure incidence
- **Findings.** [PRA-F-12](docs/audit/post-rlgwo/FINDINGS.md#pra-f-12), [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13)

<a id="ism-moon-005"></a>
### ISM-MOON-005 — One-shot initial-head eligibility and irreversible retirement

Original audit: **R21** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md), [G](docs/audit/post-rlgwo/lanes/G-omission-pass.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Whether the head-time initial Moon may be admitted.
- **Sources.** `moon/src/moon-native.mjs` ~L15, ~L50, `takeInitialHead` ~L92-107, `initialPresentation` ~L108-123, `finishInitialDocument` ~L279
- **State dimensions.** `initialHeadEligible` (true → false); `status.firstInitial`, `initialRejected`, `initialError` (sticky)
- **Guards.** generation 0, rate 1, unpaused, calendar profile, same scope, time continuity ≤ 1000 ms, receiver SHA, equal profile
- **Actors and ownership.** native host
- **Effects.** initial V5 tier
- **Invariants.** any non-initial `clear` revokes
- **Failure and recovery.** a transient initial-render exception permanently disables the initial V5 tier (PRA-F-12)
- **Status evidence.** D: comments · I: partly explicit · V: unit
- **Work orders.** none
- **Accepted evidence.** host.test.cjs ~L75, ~L114, ~L125
- **Tests.** `moon/tests/host.test.cjs`
- **Findings.** [PRA-F-08](docs/audit/post-rlgwo/FINDINGS.md#pra-f-08), [PRA-F-12](docs/audit/post-rlgwo/FINDINGS.md#pra-f-12)

<a id="ism-moon-006"></a>
### ISM-MOON-006 — Offline chunk DOM/script transport lease

Original audit: **R22** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Offline chunk DOM/script transport lease
- **Sources.** `moon/src/moon-native.mjs` `offlineTransport` ~L145-181; generated `moon/file-data/*.js`
- **State dimensions.** `at`, `seen`, `chunkScript`, `nextTimer`, `stopOffline`
- **Invalid, duplicate, stale or concurrent risks.** inert embedded nodes retained so a retry can replay them
- **Status evidence.** D: comments only · I: as original catalogue · V: host.test.cjs ~L35-L264
- **Work orders.** none
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** host.test.cjs ~L35-L264
- **Unknowns.** not re-proved in this audit

<a id="ism-moon-007"></a>
### ISM-MOON-007 — Lunar top worker boot, newest-job pump and cancellation

Original audit: **R23** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Worker-side job pump.
- **Sources.** `moon/src/moon-worker.mjs` `read`/`boot` ~L4-17, `pump` ~L18-36, handler ~L62-75
- **State dimensions.** `enginePromise`, `latest`, `running`, `serial`, `offlineParts`
- **Actors and ownership.** worker
- **Invariants.** no lost wake-up (`finally` ~L35)
- **Failure and recovery.** any unhandled rejection → `boot-error` → host `failed`
- **Invalid, duplicate, stale or concurrent risks.** terminal (PRA-F-12)
- **Status evidence.** D: comments · I: implicit · V: unit
- **Work orders.** none
- **Accepted evidence.** `tests/real-sky/moon-worker-fixture.test.mjs` pass
- **Tests.** `tests/real-sky/moon-worker-fixture.test.mjs`
- **Observed facts.** `fetch(url,{cache:'force-cache'})` at L6 (integrator check)
- **Findings.** [PRA-F-12](docs/audit/post-rlgwo/FINDINGS.md#pra-f-12)

<a id="ism-moon-008"></a>
### ISM-MOON-008 — Lunar shard RPC bridge promises and sticky failure

Original audit: **R24** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Lunar shard RPC bridge promises and sticky failure
- **Sources.** `moon/src/moon-pool.mjs` ~L6-27
- **State dimensions.** `failure` sticky for any non-AbortError
- **Invalid, duplicate, stale or concurrent risks.** no per-RPC timeout; recovery boundary is a new worker, which nothing triggers (PRA-F-12)
- **Status evidence.** D: comments only · I: as original catalogue · V: `moon/tests/pool.test.cjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `moon/tests/pool.test.cjs`
- **Unknowns.** not re-proved in this audit
- **Findings.** [PRA-F-12](docs/audit/post-rlgwo/FINDINGS.md#pra-f-12)

<a id="ism-moon-009"></a>
### ISM-MOON-009 — Lunar pool row ownership, sparse reuse and join barrier

Original audit: **R25** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Lunar pool row ownership, sparse reuse and join barrier
- **Sources.** `moon/src/moon-pool.mjs` ~L28-98
- **State dimensions.** `allSettled` barrier ~L59; `this.material` ≈ 3.5 MB retained per pool
- **Invalid, duplicate, stale or concurrent risks.** barrier traced, no defect
- **Status evidence.** D: comments only · I: as original catalogue · V: `moon/tests/pool.test.cjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `moon/tests/pool.test.cjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-moon-010"></a>
### ISM-MOON-010 — Lunar engine exclusive execution, asset admission and caches

Original audit: **R26** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Lunar engine exclusive execution, asset admission and caches
- **Sources.** `moon/src/moon-engine.mjs` ~L19-52, ~L63-131
- **State dimensions.** `active` guard; camera/lighting caches
- **Invalid, duplicate, stale or concurrent risks.** qualification SD-F02 (stale `cameraKey` after allocation refusal) unreachable while engine errors are terminal
- **Status evidence.** D: comments only · I: as original catalogue · V: `kernel.test.cjs`, `quality.test.cjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `kernel.test.cjs`, `quality.test.cjs`
- **Unknowns.** not re-proved in this audit

<a id="ism-moon-011"></a>
### ISM-MOON-011 — Lunar cooperative MessageChannel yield

Original audit: **R27** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Lunar cooperative MessageChannel yield
- **Sources.** `moon/src/moon-engine.mjs` ~L57-62
- **State dimensions.** one module channel, FIFO
- **Invalid, duplicate, stale or concurrent risks.** worker termination abandons continuations (benign)
- **Status evidence.** D: comments only · I: as original catalogue · V: indirect only
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** indirect only
- **Unknowns.** not re-proved in this audit

<a id="ism-moon-012"></a>
### ISM-MOON-012 — Lunar adaptive refinement and final quality admission

Original audit: **R28** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / EEV / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Finite refinement policy and final admission.
- **Sources.** `moon/src/moon-quality.mjs` ~L9-45; host gate `moon-native.mjs` ~L222
- **State dimensions.** quality status incl. `limit-reached`
- **Guards.** `empirical-adaptive`
- **Actors and ownership.** worker, host
- **Effects.** accepted quality
- **Invariants.** labelled outcomes
- **Failure and recovery.** `limit-reached` treated as `failed` (terminal)
- **Invalid, duplicate, stale or concurrent risks.** near-continuous refinement at 1× (model estimate, PRA-F-26)
- **Status evidence.** D: comments · I: explicit finite policy · V: unit
- **Work orders.** none
- **Accepted evidence.** `moon/tests/quality.test.cjs` (31 s case passed)
- **Tests.** `moon/tests/quality.test.cjs`
- **Findings.** [PRA-F-26](docs/audit/post-rlgwo/FINDINGS.md#pra-f-26)

<a id="ism-moon-013"></a>
### ISM-MOON-013 — Lunar detail adoption, projection cache and DOM visibility owner

Original audit: **R29** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / HRS / HRS** · Historical disposition: *resolved and independently verified*

- **Scope and decision.** Device-resolution lunar foreground.
- **Sources.** `moon/src/moon-detail.mjs` ~L43-141 (pinned); handle `moon/src/moon-native.mjs` ~L245
- **State dimensions.** one `projected` entry, one `prepared` per frame, `last` frame/key/cloud; handle {live, retired}
- **Guards.** handle refuses `adopt` after retirement
- **Actors and ownership.** host
- **Effects.** detail canvas
- **Invariants.** an old dispose never touches a successor
- **Failure and recovery.** `compose` can throw (`Moon detail viewport budget`, `Unsupported lunar cloud filter`) into the sky compositor
- **Status evidence.** D: comments + R0021 10.11 · I: RF01 fixed · V: tests + native + review
- **Work orders.** R0021 (runtime-owned handle)
- **Accepted evidence.** native-instance-retirement ES21-07; `tests/real-sky/moon-projection-cache.test.mjs`; R0021 native cells
- **Tests.** `moon/tests/native-instance-retirement.test.cjs`

<a id="ism-moon-014"></a>
### ISM-MOON-014 — Admitted initial lunar receiver and canonical render closure

Original audit: **R30** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Admitted initial lunar receiver and canonical render closure
- **Sources.** `moon/src/moon-initial.mjs` ~L9-69; `moon-initial-compact.mjs`; boot `tools/build_moon.py` ~L118
- **State dimensions.** `SalahMoonInitial` | undefined on decode failure
- **Invalid, duplicate, stale or concurrent risks.** decode failure makes the head compose throw, so the whole first paint records an error (PRA-F-13)
- **Status evidence.** D: comments only · I: as original catalogue · V: `initial.test.cjs`, `compact-codec.test.cjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `initial.test.cjs`, `compact-codec.test.cjs`
- **Unknowns.** not re-proved in this audit
- **Findings.** [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13)

<a id="ism-moon-015"></a>
### ISM-MOON-015 — Lunar C/WASM retained kernel state, frame arena and source witness

Original audit: **R37** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / IMS / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Lunar C/WASM retained kernel state, frame arena and source witness
- **Sources.** `moon/src/moon_kernel.c` ~L19-28, ~L77-96, ~L198-318
- **State dimensions.** four shard instances per worker, each ≤ 512 MiB ceiling, non-shrinking
- **Invalid, duplicate, stale or concurrent risks.** no native memory census (PRA-F-26)
- **Status evidence.** D: comments only · I: as original catalogue · V: `kernel.test.cjs`
- **Work orders.** none (files unchanged f71fef6c → 363c3e53)
- **Accepted evidence.** unit tests in the full `tests/real-sky` run (372/372, lane F)
- **Tests.** `kernel.test.cjs`
- **Unknowns.** not re-proved in this audit
- **Findings.** [PRA-F-26](docs/audit/post-rlgwo/FINDINGS.md#pra-f-26)

<a id="ism-moon-016"></a>
### ISM-MOON-016 — Moon wrapper admission, construction unwind and replay refusal

Original audit: **new (NEW-E-01; carries the RF01 resolution)** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **EIV / HRS / HRS** · Historical disposition: *new*

- **Scope and decision.** Whether a host wrapper evaluation may construct a runtime, and what remains after construction throws.
- **Sources.** `moon/src/moon-install-guard.mjs` ~L6; `moon/src/moon-native.mjs` ~L8, ~L245, try/registration/catch ~L246-300 (slot clear L298)
- **State dimensions.** no runtime → constructing → registered → disposed; construction-failed → cleaned (slot null); replay-refused
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | wrapper eval | slot empty or disposed | construct |
  | wrapper eval | live runtime | throw before any unit runs |
  | throw inside try | — | clear interval/rAF/listener, close worker, release detail if held, clear slot only if still registered, rethrow |

- **Guards.** install guard
- **Actors and ownership.** generated host wrapper
- **Effects.** global slot
- **Invariants.** at most one live runtime/detail pair
- **Failure and recovery.** rethrow skips `SalahMoonHead` and `SalahPrepareFirstPaint` and makes the refinement tail throw (PRA-F-13)
- **Invalid, duplicate, stale or concurrent risks.** empty Moon slot after construction failure (PRA-F-13)
- **Status evidence.** D: R0021 ES21-04..07 · I: RF01 fixed by refusal policy (not safe replacement) · V: native candidate PASS / control FAIL + mutants + review
- **Work orders.** R0021 (issue 33; 33e323c1, dcc8206b, de68e848, 145b7ba9; merge 65f7c75a into the R0021 line)
- **Accepted evidence.** native-instance-retirement (12 cases, re-run by lane E); mutants m9/m20 killed; native `moon-replay`/`moon-construction` cells Chromium + Firefox; delta review G
- **Tests.** `moon/tests/native-instance-retirement.test.cjs`
- **Observed facts.** integrator read L294-300
- **Unknowns.** a natural (non-injected) construction failure
- **Findings.** [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13)

<a id="ism-moon-017"></a>
### ISM-MOON-017 — Native Moon reveal gate (`moon-ready` / `mask-on`)

Original audit: **new (NEW-E-02)** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / EEV / EEV** · Historical disposition: *new*

- **Scope and decision.** Whether the Moon disc is visible.
- **Sources.** `src/native/index.html` `updateSkySurface` L2236-2241; CSS ~L178, ~L185
- **State dimensions.** hidden (no runtime / no presentation / no scene) ↔ revealed
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | `updateSkySurface` | `SalahMoonRuntime.surface()` non-null, `.mphoto` href, scene key | `moon-ready`; mask also needs `_skyMoonPresence>0` |

- **Guards.** as tabled
- **Actors and ownership.** `paint`, `beginSkyScene`
- **Effects.** disc visibility
- **Invariants.** legacy decode is never terrain readiness
- **Failure and recovery.** no runtime → no disc on any tree (AGENTS forbidden "empty moon slot", PRA-F-13)
- **Invalid, duplicate, stale or concurrent risks.** gate D depends on the initial V5 tier always presenting
- **Status evidence.** D: comments + R0021 §F · I: explicit · V: native for the injected failure
- **Work orders.** R0021 (recorded)
- **Accepted evidence.** R0021 native `moon-construction` cells
- **Tests.** R0021 native cells
- **Observed facts.** integrator read L2236-2241
- **Findings.** [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13)

<a id="ism-moon-018"></a>
### ISM-MOON-018 — Moon worker asset HTTP acquisition and browser-cache admission

Original audit: **new (NEW-E-03)** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Whether a cached HTTP response is used for the Moon DEM/colour assets.
- **Sources.** `moon/src/moon-worker.mjs` L6 (`fetch(url,{cache:'force-cache'})`)
- **State dimensions.** fetched-ok | HTTP error | size/truncation error
- **Guards.** `r.ok`, size
- **Actors and ownership.** worker
- **Effects.** asset bytes
- **Failure and recovery.** a heuristically cached error is returned without revalidation
- **Invalid, duplicate, stale or concurrent risks.** non-recovery even when retried (PRA-F-12)
- **Status evidence.** D: R0021 note (routed, not fixed) · I: implicit · V: native observation of the failure
- **Accepted evidence.** R0021 contract G item 4: Firefox 153 cached 404 served to every retry (cell b21), final `unavailable`
- **Tests.** R0021 b20/b21 cells
- **Hypotheses.** reload may also not recover
- **Unknowns.** Chromium behaviour; production `Cache-Control` on errors
- **Findings.** [PRA-F-12](docs/audit/post-rlgwo/FINDINGS.md#pra-f-12)

<a id="ism-moon-019"></a>
### ISM-MOON-019 — Moon page-lifecycle withdrawal and worker lifetime

Original audit: **new (NEW-E-04)** · Lane papers: [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *new*

- **Scope and decision.** Moon behaviour on visibility changes.
- **Sources.** `moon/src/moon-native.mjs` visibility ~L239, listener ~L248, `setInterval(poll,250)` ~L287
- **State dimensions.** hidden → `clear('document hidden')`; visible → `clock=null; poll()`
- **Actors and ownership.** document visibility
- **Effects.** refined surface discarded
- **Invalid, duplicate, stale or concurrent risks.** no pagehide/pageshow/freeze handler; worker, four shard workers and the 4 Hz poll live for the page; each hide/show re-runs the full adaptive pipeline (PRA-F-26)
- **Status evidence.** D: comments · I: partly explicit · V: unit
- **Accepted evidence.** host.test.cjs ~L289
- **Tests.** `moon/tests/host.test.cjs`
- **Unknowns.** bfcache freeze/restore of the Moon worker
- **Findings.** [PRA-F-26](docs/audit/post-rlgwo/FINDINGS.md#pra-f-26)

<a id="ism-moon-020"></a>
### ISM-MOON-020 — Native physical lunar-light eligibility (sky, cloud, star consumers)

Original audit: **new (NEW-E-05 + NEW-D-04)** · Lane papers: [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [E](docs/audit/post-rlgwo/lanes/E-moon.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *new*

- **Scope and decision.** Moonlight, beam, glow, star wash, cloud light and lunar optics.
- **Sources.** `src/native/index.html` `nativeLunarPresentation`/`lunarPresentation(..., _pbrFailed)` ~L2990-3003, consumers ~L3055-3203
- **State dimensions.** one eligibility object per atmosphere derivation; `surfaceFailed` × `moonUp` × `darkness` × `phaseVis`
- **Guards.** as listed
- **Actors and ownership.** `atmosphere`
- **Effects.** light consumers
- **Invariants.** no light without a physical Moon
- **Invalid, duplicate, stale or concurrent risks.** `surfaceFailed` comes from `_pbrFailed`, unreachable while a runtime exists, so eligibility does not consult the modern surface (PRA-F-13); a second producer (worker physical Moon) can diverge under `simMoon*` (PRA-F-31)
- **Status evidence.** D: R0022 certificate + comments · I: guards explicit, surface binding implicit · V: unit (legacy path)
- **Work orders.** R0022 (issue 34, before f71fef6c)
- **Accepted evidence.** `tests/r0022-lunar-consumers.cjs` (legacy runtime-absent VM path only); `r0022-baseline-balance` 30/37
- **Tests.** `tests/r0022-lunar-consumers.cjs`
- **Unknowns.** visible tint magnitude
- **Findings.** [PRA-F-13](docs/audit/post-rlgwo/FINDINGS.md#pra-f-13), [PRA-F-31](docs/audit/post-rlgwo/FINDINGS.md#pra-f-31)

## Build, deployment and qualification (`ISM-BLD`)

<a id="ism-bld-001"></a>
### ISM-BLD-001 — Native generation output publication sequence

Original audit: **C13** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Turns authored sources into root entries and bundles; a wrong output ships at the next merge to main.
- **Sources.** `tools/build_native.py` ~L1-114 (index write L83, offline write L109, `build_moon` L113); `tools/native_core_horizon.py`; `tools/native_core_spectral_cache.py`; `tools/native_star_bootstrap.py`
- **State dimensions.** input identity (vendor digests, authored sources); write phase (core copy → notices → worker → `native-sky.js` → star bootstrap → data → config/builder → `index.html` → CSS → `offline.html` → Moon → report); exit code
- **Transitions.**

  | Event | Guard | Effect |
  |---|---|---|
  | clean input | — | complete, rc 0; second run byte-identical |
  | transform digest drift | — | fails before that file; earlier core files already written |
  | Moon-stage failure | — | rc 1 with root entries unexpanded (lane F probe C) |
  | hand-edited generated file | — | silently overwritten |

- **Guards.** digest guards (`ValueError`); `assert` guards `build_native.py` L70, `native_star_bootstrap.py` L14, L18, L26 (removed under `python -O`); exact-count guard L79; unguarded `replace(...,1)` ~L72-82
- **Actors and ownership.** executor
- **Effects.** generated tree
- **Invariants.** generated = build(authored) (holds at baseline)
- **Failure and recovery.** no rollback or staging; recovery is a full re-run
- **Invalid, duplicate, stale or concurrent risks.** partial states and silent no-op replacements (PRA-F-19)
- **Status evidence.** D: AGENTS + R0027 rebuild protocol · I: partly explicit · V: transform tests; no registered whole-tree parity test
- **Work orders.** R0027 (issue 69: spectral transform added)
- **Accepted evidence.** `tests/real-sky/native_spectral_cache_build_test.py` 8 OK; build-twice parity (lane F probe: 0 diffs over 509 files; integrator re-run at hand-back)
- **Tests.** `tests/real-sky/native_spectral_cache_build_test.py`, `native_horizon_build_test.py`
- **Observed facts.** integrator confirmed write order and assert lines
- **Hypotheses.** anchor drift at L72-74 yields a 'successful' build with hooks missing
- **Unknowns.** whether any executor ran with `-O`
- **Findings.** [PRA-F-19](docs/audit/post-rlgwo/FINDINGS.md#pra-f-19)

<a id="ism-bld-002"></a>
### ISM-BLD-002 — Moon generation preflight and expansion

Original audit: **C14** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Validation and expansion of Moon outputs into the entries.
- **Sources.** `tools/build_moon.py` ~L57-151; `tools/compact_receivers.py`
- **State dimensions.** preflight (entries, assets, WASM, initial receiver); write order worker → chunks → host → compact → entries → `BUILD.json`
- **Guards.** duplicate expansion rejected (~L67-68); identity checks ~L80-92
- **Actors and ownership.** native builder
- **Effects.** Moon outputs
- **Invalid, duplicate, stale or concurrent risks.** `moon/file-data/` never cleaned, so a stale extra chunk survives (lane F probe B); `BUILD.json` has no file inventory (PRA-F-19)
- **Status evidence.** D: AGENTS Moon section · I: partly explicit · V: guard tests
- **Work orders.** R0021 (HOST_UNITS gained `moon-install-guard.mjs`)
- **Accepted evidence.** `tests/real-sky/moon_build_guard_test.py` 8 OK
- **Tests.** `tests/real-sky/moon_build_guard_test.py`, `moon/tests/test_build.py`
- **Findings.** [PRA-F-19](docs/audit/post-rlgwo/FINDINGS.md#pra-f-19)

<a id="ism-bld-003"></a>
### ISM-BLD-003 — R0017 Pages payload qualification workflow and retained receipt

Original audit: **C24** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / EEV / IMS** · Historical disposition: *no longer applicable*

- **Scope and decision.** Whether the published payload stays within the qualified bound.
- **Sources.** `.github/workflows/r0017-pages-payload.yml`; `tools/verify_r0017_pages_payload.py` (APPROVED, ALLOWED ~L11-23; bound ~L106)
- **State dimensions.** trigger {pull_request to main} × job guard {PR 62}
- **Guards.** PR number
- **Actors and ownership.** GitHub Actions
- **Effects.** none on later PRs
- **Invalid, duplicate, stale or concurrent risks.** payload growth unmeasured (PRA-F-07)
- **Status evidence.** D: R0017 · I: explicit but inert · V: not exercised since PR 62
- **Work orders.** none after PR 62 (R0017)
- **Accepted evidence.** `.github/workflows/r0017-pages-payload.yml` L14 `if: github.event.pull_request.number == 62`
- **Observed facts.** estimate re-derived by the integrator: 0.898 GB at 06772824 (PR 62), 1.771 GB at f71fef6c, 1.910 GB at 363c3e53 (9,686 files)
- **Unknowns.** GitHub's enforcement behaviour
- **Findings.** [PRA-F-07](docs/audit/post-rlgwo/FINDINGS.md#pra-f-07)

<a id="ism-bld-004"></a>
### ISM-BLD-004 — Pages deployment from main (a commit to main is a deploy)

Original audit: **new (NEW-F-02)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** What reaches users after a merge.
- **Sources.** GitHub service `pages build and deployment` (legacy Jekyll, branch `main`, path `/`); `_config.yml`
- **State dimensions.** merged commit → build → built | startup_failure → served
- **Guards.** none repo-owned
- **Actors and ownership.** GitHub service
- **Effects.** public site
- **Failure and recovery.** service retries (`294d2d37` had two startup failures)
- **Invalid, duplicate, stale or concurrent risks.** no pre-deploy gate (PRA-F-09)
- **Status evidence.** D: AGENTS/README · I: external · V: post-hoc readback in certificates
- **Accepted evidence.** latest Pages build `363c3e53` `built` (integrator `gh api`); lane F public byte readback of four files
- **Findings.** [PRA-F-07](docs/audit/post-rlgwo/FINDINGS.md#pra-f-07), [PRA-F-09](docs/audit/post-rlgwo/FINDINGS.md#pra-f-09)

<a id="ism-bld-005"></a>
### ISM-BLD-005 — RLGWO delivery workflow (campaign governance)

Original audit: **new (NEW-F-03)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Candidate → exact-tree review → owner approval → ordinary merge → Pages → public readback → certificate → closure.
- **Sources.** issue certificates (e.g. 6814244464, 6828374683); `docs/state-contracts/R0015.md` §7 root gates
- **State dimensions.** per work order: candidate, reviewed, approved, merged, deployed, read back, certified, closed
- **Guards.** human/agent process
- **Actors and ownership.** owner, agents
- **Effects.** closure state
- **Failure and recovery.** R0015 auto-closed by a merge keyword and reopened (6816192574); R0017 certificate withdrawn (6703510170); R000D post-closure correction (6792330574)
- **Invalid, duplicate, stale or concurrent risks.** authoritative state lives in issue comments while contracts can say otherwise (`R0015.md` L221, L335, L450 `wholeContractComplete` remains false vs certificate 6828391831) (PRA-F-27)
- **Status evidence.** D: per-WO contracts · I: process only · V: review records
- **Work orders.** all certificate-bearing work orders
- **Accepted evidence.** FINAL-CERTIFICATE comments (12 spot-checked by the integrator)
- **Findings.** [PRA-F-27](docs/audit/post-rlgwo/FINDINGS.md#pra-f-27)

<a id="ism-bld-006"></a>
### ISM-BLD-006 — Installer-bytes delivery routes and README pin ↔ docs-receipt coupling

Original audit: **new (NEW-F-04; also covers the delivery-route omission FND-F-11)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Which installer bytes users run and what an installer change obliges.
- **Sources.** `README.md` L59, L63 (unpinned `main` pipe routes), L92-117 (pinned `a4c617eb` review-first route); builder command ~L429-445; `tools/qualification/installer_preview_docs.cjs` L18-20
- **State dimensions.** route {main pipe (unpinned), pinned commit, builder command}; pin values
- **Guards.** hash pins
- **Actors and ownership.** users, owner
- **Invalid, duplicate, stale or concurrent risks.** any installer change requires re-pinning README, which invalidates the docs receipt (PRA-F-28)
- **Status evidence.** D: README · I: implicit · V: receipt pins
- **Work orders.** R0015, R0016
- **Accepted evidence.** `tools/qualification/installer_preview_docs.cjs` L18-20 pins; README L92-117
- **Findings.** [PRA-F-28](docs/audit/post-rlgwo/FINDINGS.md#pra-f-28)

<a id="ism-bld-007"></a>
### ISM-BLD-007 — Registered regression suites and the known-failure baseline

Original audit: **new (NEW-F-05; carries EF01)** · Lane papers: [A](docs/audit/post-rlgwo/lanes/A-prayer-time.md), [D](docs/audit/post-rlgwo/lanes/D-sky-rendering.md), [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **DWE / IMS / PEX** · Historical disposition: *new*

- **Scope and decision.** Which instruments count as evidence and which failures are 'known'.
- **Sources.** `tools/cp9/run_native_regressions.py` ~L22-29, ~L372-392; `tests/rlgwo-docs-contract.cjs`; known-failure prose in `R0003.md` ~L364, `R000F.md` ~L349, `R0021.md` ~L449, `R0026.md` ~L310, `R0027.md` ~L341
- **State dimensions.** per instrument: green | red-known | red-new; failing-set comparison
- **Guards.** prose lists
- **Actors and ownership.** executors
- **Effects.** qualification claims
- **Invalid, duplicate, stale or concurrent risks.** no machine-readable expected-failure manifest; a new failure inside an already-red command is masked (PRA-F-06)
- **Status evidence.** D: prose only · I: implicit · V: differential use
- **Work orders.** R0017 (issue 23, 7214a2c8)
- **Accepted evidence.** integrator runs at 10 commits (REPORT §Instruments)
- **Tests.** `node --test tests/*.test.cjs tests/*.test.mjs` 959/955/0/4
- **Observed facts.** see REPORT instrument table
- **Findings.** [PRA-F-06](docs/audit/post-rlgwo/FINDINGS.md#pra-f-06)

<a id="ism-bld-008"></a>
### ISM-BLD-008 — Work-order-branch qualification workflows

Original audit: **new (NEW-F-06)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **IMS / IMS / UNK** · Historical disposition: *new*

- **Scope and decision.** Lifecycle of the campaign's CI harnesses.
- **Sources.** `.github/workflows/*.yml` `on:` blocks
- **State dimensions.** trigger × branch
- **Actors and ownership.** GitHub Actions
- **Invalid, duplicate, stale or concurrent risks.** inert except as dispatchable re-qualification harnesses; Actions also lists three workflows no longer in the tree (lane F)
- **Status evidence.** D: none · I: implicit · V: not examined
- **Work orders.** R0007, R000B, R0013, R0015, R0016, R0017
- **Accepted evidence.** integrator trigger census: 32 files; 30 `push` (named branches), 6 `workflow_dispatch`, 1 `pull_request` (PR 62-gated); none on `push` to main
- **Findings.** [PRA-F-09](docs/audit/post-rlgwo/FINDINGS.md#pra-f-09)

<a id="ism-bld-009"></a>
### ISM-BLD-009 — Evidence receipts bound to source hashes

Original audit: **new (NEW-F-07)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / PEX / PEX** · Historical disposition: *new*

- **Scope and decision.** Receipts that name the exact bytes they measured.
- **Sources.** as evidence; re-pin protocol `R0027.md` ~L262-275
- **State dimensions.** pin value per receipt
- **Guards.** sha256 equality
- **Actors and ownership.** executors
- **Invariants.** a receipt names the bytes it measured
- **Invalid, duplicate, stale or concurrent risks.** stale pins become permanent known failures (`r0021-reveal` byte pin; docs-contract digest) (PRA-F-06)
- **Status evidence.** D: R0027 protocol · I: partly explicit · V: pins
- **Work orders.** R0017, R0021, R0027
- **Accepted evidence.** pins in `installer_preview_docs.cjs`, `rlgwo-docs-contract.cjs` ~L270, `tests/native-script-contract.js`, `tools/build_moon.py` ~L15-16
- **Findings.** [PRA-F-06](docs/audit/post-rlgwo/FINDINGS.md#pra-f-06)

<a id="ism-bld-010"></a>
### ISM-BLD-010 — Frozen v1 verification

Original audit: **new (NEW-F-01)** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md), [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **DWE / EEV / EEV** · Historical disposition: *new*

- **Scope and decision.** Proof that v1 bytes are unchanged and servable.
- **Sources.** `tools/verify_v1.py` ~L18-92 (`--check-pages` ~L54, ~L65); `docs/V1_PRESERVATION.md` L93
- **State dimensions.** mode {default, check-root, check-pages, negative-control}
- **Guards.** byte digests
- **Actors and ownership.** executors
- **Invariants.** v1 bytes unchanged (`git diff f71fef6c 363c3e53 -- v1` empty)
- **Invalid, duplicate, stale or concurrent risks.** documented recipe requires a check that fails at baseline (PRA-F-18)
- **Status evidence.** D: recipe stale · I: explicit · V: negative control
- **Work orders.** R0017 (`_config.yml` added, 02ab7a93)
- **Accepted evidence.** `python tools/verify_v1.py` PASS (integrator); `--check-pages` prints "FAIL: New Jekyll configuration requires V1 inclusion review"
- **Tests.** `tools/verify_v1.py --negative-control`
- **Findings.** [PRA-F-18](docs/audit/post-rlgwo/FINDINGS.md#pra-f-18)

## Frozen v1 compatibility snapshot (`ISM-V1`)

<a id="ism-v1-001"></a>
### ISM-V1-001 — Frozen v1 one-time root configuration import

Original audit: **C15** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / PEX / PEX** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Frozen v1 one-time root configuration import (frozen compatibility snapshot).
- **Sources.** `v1/config.js`
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, `tests/v1_storage.cjs` 10/10
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; `tests/v1_storage.cjs` 10/10
- **Tests.** `tests/v1_storage.cjs` 10/10
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-002"></a>
### ISM-V1-002 — Frozen v1 configuration apply and boot without generation ownership

Original audit: **C16** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Frozen v1 configuration apply and boot without generation ownership (frozen compatibility snapshot).
- **Sources.** `v1/index.html` ~L2166ff
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Invalid, duplicate, stale or concurrent risks.** CF07: location changes do not invalidate earlier data or settings work
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)
- **Findings.** [PRA-F-18](docs/audit/post-rlgwo/FINDINGS.md#pra-f-18)

<a id="ism-v1-003"></a>
### ISM-V1-003 — Frozen v1 prayer cache, retry, tomorrow and rollover

Original audit: **C17** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / PEX / IMS** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Frozen v1 prayer cache, retry, tomorrow and rollover (frozen compatibility snapshot).
- **Sources.** `v1/index.html` ~L743ff
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-004"></a>
### ISM-V1-004 — Frozen v1 weather current/forecast acquisition

Original audit: **C18** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / PEX / IMS** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Frozen v1 weather current/forecast acquisition (frozen compatibility snapshot).
- **Sources.** `v1/index.html` ~L771ff
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-005"></a>
### ISM-V1-005 — Frozen v1 radar manifest, tile and freshness acquisition

Original audit: **C19** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Frozen v1 radar manifest, tile and freshness acquisition (frozen compatibility snapshot).
- **Sources.** `v1/index.html` ~L816ff
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-006"></a>
### ISM-V1-006 — Frozen v1 modal editing, lookup, GPS and Reset

Original audit: **C20** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Frozen v1 modal editing, lookup, GPS and Reset (frozen compatibility snapshot).
- **Sources.** `v1/index.html` ~L2302-2451
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Invalid, duplicate, stale or concurrent risks.** CF07; CF08: `_resetLocal` ~L2421-2428 ignores the `clearLocal` result and says "Local settings cleared."
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)
- **Findings.** [PRA-F-18](docs/audit/post-rlgwo/FINDINGS.md#pra-f-18)

<a id="ism-v1-007"></a>
### ISM-V1-007 — Frozen v1 real/simulated clock anchor compatibility variant

Original audit: **C21** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / PEX / IMS** · Historical disposition: *implemented but not fully verified*

- **Scope and decision.** Frozen v1 real/simulated clock anchor compatibility variant (frozen compatibility snapshot).
- **Sources.** `v1/index.html`
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-008"></a>
### ISM-V1-008 — Frozen v1 Moon texture readiness and pending render cache

Original audit: **C22** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Frozen v1 Moon texture readiness and pending render cache (frozen compatibility snapshot).
- **Sources.** `v1/index.html`
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

<a id="ism-v1-009"></a>
### ISM-V1-009 — Frozen v1 synthetic star catalogue and projection cadence

Original audit: **C23** · Lane papers: [C](docs/audit/post-rlgwo/lanes/C-config-builder.md) · Status D / I / V: **IMS / IMS / IMS** · Historical disposition: *still implicit or vulnerable*

- **Scope and decision.** Frozen v1 synthetic star catalogue and projection cadence (frozen compatibility snapshot).
- **Sources.** `v1/index.html`; `tools/build_native.py`
- **State dimensions.** as original catalogue
- **Invariants.** bytes frozen
- **Status evidence.** D: provenance only (`docs/V1_PRESERVATION.md`) · I: as original · V: byte verification, none behavioural
- **Work orders.** none (`v1/` byte-unchanged f71fef6c → 363c3e53; frozen by AGENTS)
- **Accepted evidence.** `tools/verify_v1.py` byte verification; none behavioural
- **Tests.** none behavioural
- **Unknowns.** v1 deployment status (`VERSION.json` says pending; Pages not contacted)

---

## Installer workflows (`ISM-INST`)

Original-audit mapping: C08 → ISM-INST-001, 002, 007; C09 → ISM-INST-003, 004; C10 → ISM-INST-006;
C11 → ISM-INST-004, 005, 006 (superseded); C12 → ISM-INST-006, 007. Lane F re-verified that
entries 001…007 still describe the baseline installer bytes (`install.sh` blob `e2e2640e`,
`install.ps1` blob `28cfdae7`; `git log e4dbf91b..363c3e53 -- install.sh install.ps1` is empty).
ISM-INST-008 was added by the post-RLGWO audit as a partial entry.

## ISM-INST-001: Invocation options and run mode (preview effect boundary)

**Scope and purpose.** Decides whether an invocation may cause any effect beyond local,
read-only discovery and console output. Preview must be offline and effect-free. Normal
mode, including `NO_OPEN`, downloads, stages, copies to the clipboard and asks for
manual confirmation.

**Authoritative sources.**
- [`install.sh`](install.sh): option validation ~L62–64; preview branch ~L840–872.
  DRY_RUN guards in `initialize_staging` ~L190, `cleanup_staging` ~L209, `copy_text`
  ~L262, `select_asset` ~L562, `download_tablissng_asset` ~L595, `validate_asset`
  ~L626, `retain_asset` ~L638, `expand_chromium_asset` ~L655, `download_preset` ~L702,
  `install_tablissng` ~L732 and `show_import_instructions` ~L785. Preview interpreter
  selection is in `firefox_discovery_python` ~L327 (Apple shim avoidance, `-B` at
  ~L382).
- [`install.ps1`](install.ps1): `param` ~L21–30; environment-default validation ~L35;
  preview branch ~L1640–1667. Every effectful helper opens with a `$DryRun` guard, for
  example `Initialize-CompilerNative` ~L58, `Initialize-StagingNative` ~L339,
  `Get-TrustedStagingParent` ~L586, `Download-Asset` ~L1335 and `Copy-Text` ~L789.
- Contract: [R0016](docs/state-contracts/R0016.md), sections "Product behavior under
  qualification" and "Current source-bound receiving". Preview limits are in the
  [R0015 Windows transactions](docs/r0015-artifact-transactions.md) contract under
  "Preview and evidence limits".
- Tests: [`tests/install-preview.py`](tests/install-preview.py),
  [`tests/install-preview.ps1`](tests/install-preview.ps1),
  [`tests/install-entry-native-composition.py`](tests/install-entry-native-composition.py),
  [`tools/qualification/installer_preview_windows_full_entry.py`](tools/qualification/installer_preview_windows_full_entry.py),
  [`tests/install-staging-readonly.py`](tests/install-staging-readonly.py).

**Independent dimensions.**
1. Mode: preview (`DRY_RUN=1` or `-DryRun`) or normal.
2. Opening: open browser pages, or `NO_OPEN` / `-NoOpen`. This dimension is orthogonal
   to mode. In normal mode, `NO_OPEN` still downloads, stages, copies and confirms.
3. Option validity: valid, or refused before discovery.
4. Install source: `github`, `store` or `ask`. The default is `github`.
5. Host: Bash on Linux or macOS; Windows PowerShell 5.1 or PowerShell 7, run either with
   `-File` or through `irm | iex` (see ISM-INST-005).

**Transitions.**

| From | Event | Guard | To |
|---|---|---|---|
| start | Bash: `DRY_RUN`/`NO_OPEN` not 0 or 1, unknown `SALAH_INSTALL_SOURCE`, or any argument | ~L62–64 | refused, exit 1, before discovery |
| start | PS: environment-derived `InstallSource` not ask/github/store | ~L35; `ValidateSet` does not check defaults | refused (throw) before discovery |
| validated | discovery completes | n/a | targets listed (ISM-INST-002) |
| listed | preview | none | per-target plan printed. Exit 0 if at least one target is eligible, otherwise exit 1 |
| listed | normal | n/a | selection prompt (ISM-INST-002), then staging (ISM-INST-004) |
| any preview state | direct call to an effectful helper | helper's own guard | refusal (Bash `return 1`; PS throw, or `$false`/`$null` for clipboard and preset) with no usable path |

**Guards and invariants.**
- Preview returns before terminal acquisition (Bash ~L840 precedes `acquire_terminal`
  ~L874) and before any prompt, staging root, native helper load, network request,
  extraction, preset rewrite, clipboard write, browser open or cleanup.
- Suppressed helpers return no usable path. Suppressed clipboard calls return failure
  (Bash `copy_text` returns 1; PS `Copy-Text` returns `$false`).
- Remote release, version and path facts, and an unresolved `ask` choice, are reported
  as unresolved, never as resolved values.

**Effects.** Preview: local reads of browser profile directories and metadata, and
console output only. Normal: everything described in ISM-INST-004 to ISM-INST-007.

**Failure and interruption.** Preview has no staging state to recover. Bash's EXIT trap
runs during preview, but `cleanup_staging` returns immediately when `DRY_RUN=1` (~L209).
PowerShell's `Clear-OwnedScratch` sits in a `finally` that only begins after the preview
`exit` (~L1699–1741).

**Observed facts.**
- In both installers, every listed staging, admission, transport, clipboard and open
  helper carries a preview guard (source above).
- R0016 records these receipts:
  - Linux preview: run 43173749709, 45 PASS across 61 phases.
  - Native macOS: run 43173749688, all 11 suites, 248 instrument rows.
  - Windows core75 and normal18: run 43171927589.
  - Windows routes8: run 43171927350.
  - Windows full20 on both hosts: run 43220592915. PS7 passed on attempt 1. PS5.1
    passed on attempt 2. PS5.1 attempt 1 is retained as adverse evidence with 0
    installer cases.
- The R0016 final root technical decision admits the premerge evidence within those
  recorded scopes.
- R0016 records limits that remain:
  - `independentHardContainment=NOT_ACQUIRED` on Windows.
  - Global transport telemetry is null. A denied connection is a separate observation
    from proof that no connection was attempted.
  - Windows full-lifecycle before/after comparisons are unequal, because of host startup,
    profile and TEMP activity. Only the held source windows are equal.
  - On Mac, a direct-transport mutant added 41 Python-cache entries, preserved as an
    adverse delta.
  - The combined Linux run 43171927513 remains FAIL 37/45, with eight
    `PRODUCT_ASSERTION_FAILED` ownership refusals. It ran the same installer bytes (see
    [R0016](docs/state-contracts/R0016.md), the "Preserved earlier native evidence" and
    successor-record limits). The 45-PASS / 61-phase result is a later run (43173749709)
    in an owned scaffold. Only the named reused subgroup of 43171927513 is credited.
  - The receiving review did not recount the 248 macOS instrument rows of run
    43173749688.
- The independent security review of the exact tree is recorded in
  [R0016](docs/state-contracts/R0016.md), "Successor receiving and merge record". It
  reports that sandboxed dry-run before/after snapshots were identical and that no stub
  was invoked.
- The same review observed host-level start-up effects in a no-op baseline too. Those
  effects come from the shell, the PowerShell host or a started interpreter, and fall
  outside the installer's no-effect statements. The review assessed macOS Python
  resolution by reasoning only and did not run Apple Bash 3.2.

**Hypotheses.**
- The unequal Windows full-lifecycle comparisons are attributed to host startup and
  profile behaviour, not to installer source. R0016's held-window design supports this
  but does not prove it for every host.

**Unknowns.**
- Whether native Windows startup, profile and module-cache effects can be excluded in
  general. This is not established. R0016 records it as a limit, not as zero effects.
- Host-wide absence of network activity during preview. This is not established.

**Hardening status.**
- Source guards: `enforced and covered by tests` (`tests/install-preview.py`,
  `tests/install-preview.ps1`; clipboard-effect, false-success and null-array mutants
  per R0016).
- Preview boundary within the recorded scopes: `independently verified` (independent
  receivers and the root technical decision cited in
  [R0016](docs/state-contracts/R0016.md); runs above).
- Host-wide zero effects and transport absence: `unresolved` (recorded limits above).
- Environment-default source validation: `enforced and covered by tests` (R0016 full20
  "resolved-source/NoOpen regressions", run 43220592915).

---

## ISM-INST-002: Discovery knowledge, target eligibility and selection

**Scope and purpose.** Decides which browser profiles may reach any effectful branch.
R0013 owns this machine. R0015 and R0016 consume its result.

**Authoritative sources.**
- [`install.sh`](install.sh): `firefox_status` ~L361, `discovery_eligibility` ~L470,
  `add_target` ~L500 (delimiter rejection), `detect_targets` ~L515, selection ~L876–910
  and dispatch re-derivation ~L922.
- [`install.ps1`](install.ps1): `Get-ChromiumExtensionStatus` ~L896, `Test-StrictJson`
  ~L942, `Get-FirefoxExtensionStatus` ~L1014, `Get-DiscoveryEligibility` ~L1091,
  `Get-Targets` ~L1102, selection ~L1670–1698 and dispatch re-derivation ~L1707.
- Contract: [R0013](docs/state-contracts/R0013.md), section "Selection, preview and
  handoff".
- Tests: [`tests/install-discovery.py`](tests/install-discovery.py),
  [`tests/install-discovery.ps1`](tests/install-discovery.ps1),
  [`tests/install-discovery-mutations.py`](tests/install-discovery-mutations.py),
  [`tests/install-entry-bash.py`](tests/install-entry-bash.py),
  [`tests/install-entry-held.ps1`](tests/install-entry-held.ps1).

**Independent dimensions.** These are kept separate, not collapsed into one status.
1. Knowledge: `known-new`, `known-neither`, `known-legacy`, `known-both` or `unknown`.
   An `unknown` carries a reason, for example `no-profile`, `profile-unavailable`,
   `metadata-absent`, `metadata-unreadable`, `metadata-encoding`, `metadata-malformed`,
   `metadata-unsupported`, `parser-unavailable`, `parser-failed` or
   `profile-path-unsupported`.
2. Legacy flag (`has_old` / `HasLegacyTabliss`). This flag overrides knowledge.
3. Derived eligibility: `eligible-known`, `unknown-held` or `legacy-refused`.
4. Selection membership: `all`, or an explicit index list. In normal mode, Bash first
   needs a readable controlling terminal (`acquire_terminal` ~L874). Without one, the
   run exits 1 before selection and before any staging.
5. Bash only: a record rejected for a delimiter or newline. It gets no index, cannot be
   selected, and is counted as held only under `all`.

**Transitions and guards.**

| Event | Bash | PowerShell |
|---|---|---|
| Legacy evidence, or `known-legacy`/`known-both` | `legacy-refused` | `legacy-refused` |
| `known-new`/`known-neither` with no legacy flag | `eligible-known` | `eligible-known` |
| Anything else | `unknown-held` | `unknown-held` |
| Empty selection | `all` | `all` |
| Malformed token, leading/trailing/double comma, or unknown index | refused, exit 1, before staging (~L882–891) | the token is silently dropped; if nothing remains, "No valid targets selected", exit 1 (~L1677–1684) |
| Duplicate index | de-duplicated | de-duplicated (membership filter) |
| Zero eligible selected targets | exit 1 before staging (~L910) | exit 1 before staging (~L1695) |
| Dispatch of each target | eligibility re-derived; held and refused targets skipped | same |

**Invariants.**
- A held or refused target never reaches staging initialization, download, extraction,
  clipboard, browser opening or preset dispatch.
- Independently eligible peers remain usable.
- Unknown is never treated as verified absence, within the scope of each detector.
  Firefox metadata failures and missing profiles become `unknown`. Chromium keeps R0013's
  existing detector scope ([R0013](docs/state-contracts/R0013.md) ~L66–70, "Chromium
  retains its existing detector scope"). A PowerShell Chromium profile whose
  `Preferences` read fails therefore still derives its knowledge from the directory
  check alone (see Observed facts).

**Observed facts.**
- One derived predicate per host serves preview, pre-staging counting and dispatch
  (source above).
- R0013 records the Windows rows as re-acquired in run 43146668695. Per `gh run view`,
  that run is on EARLIER bytes: head `ddfb872a`, with `install.ps1` blob `cf353a7f`. Its
  windows-2022 contract-host job passed on attempts 2 and 3. Its windows-2025 job failed
  in all three attempts, and the run's overall conclusion is failure.
- Bash Chromium discovery checks only the `Extensions/<id>` directories. PowerShell also
  reads `Preferences` `extensions.settings`. A locked or malformed `Preferences` read is
  silently swallowed (`install.ps1` ~L921–923). The profile then rests on the directory
  check alone, and with no ID directory it becomes `known-neither` (eligible). This is a
  limitation recorded within R0013's Chromium detector scope, not a violation of the
  scoped invariant above.
- Dispatch re-derives eligibility from the stored discovery record (Bash `TARGETS` row;
  PS target object), not from a fresh disk read. Profile changes after discovery are not
  observed.

**Hypotheses.**
- A legacy Tabliss loaded through "Load unpacked" has a path-derived ID, not the store
  ID. If so, neither detector sees it, and the profile is classified `known-neither`
  (eligible). This is untested here.

**Unknowns.**
- Whether issue 19 row 19-03's strict-selection wording is meant to bind PowerShell. The
  recorded row cites only `install.sh`. PowerShell's lenient token handling cannot
  dispatch held or refused targets.

**Hardening status.**
- Eligibility gating on both hosts: `enforced and covered by tests` (tests above; run
  43146668695; the discovery mutants recorded in [R0013](docs/state-contracts/R0013.md)).
- PowerShell strict selection: `unresolved` (divergence; see Open findings).

---

## ISM-INST-003: Staging-parent trust decision

**Scope and purpose.** Decides whether a parent directory may hold a private root. On
POSIX it decides for the scratch parent (`TMPDIR`, or `/tmp`) and the retained parent
(`HOME`). On Windows it decides for `%TEMP%` and `%USERPROFILE%` staging, and separately
for the compiler's native temporary path.

**Authoritative sources.**
- [`install.sh`](install.sh): `trusted_parent` ~L97–150 and `path_identity` ~L87.
- [`install.ps1`](install.ps1): `Get-TrustedStagingParent` ~L585, which calls
  `StageNative.RequireLocalAclVolume` ~L464 and `StageNative.Read` ~L493. Compiler
  parent: `New-StagingCompilerContext` ~L167 and `Read-CompilerPathFacts` ~L91.
- Contracts: [R0015](docs/state-contracts/R0015.md), "Installer corrections round (B1,
  B2, section B controls)"; [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Ownership boundary".
- Tests: [`tests/install-staging-parent.py`](tests/install-staging-parent.py),
  [`tests/install-linux-owner.py`](tests/install-linux-owner.py),
  [`tests/install-staging-owner.ps1`](tests/install-staging-owner.ps1),
  [`tests/install-staging-windows.ps1`](tests/install-staging-windows.ps1),
  [`tests/install-volume-policy.ps1`](tests/install-volume-policy.ps1),
  [`tests/install-volume-mutations.py`](tests/install-volume-mutations.py).

**Independent dimensions.**
1. Spelling validity. POSIX: the path is absolute, has no newline, and has no empty,
   `.` or `..` component. Windows: a drive-letter path with no control characters,
   colons or ambiguous trailing spaces or dots.
2. Link admission. POSIX only: a symlink in the supplied spelling is admitted only if it
   is root-owned and its container is root-owned and not group- or other-writable.
3. Ancestor trust. Every component must be owned by root or the user (POSIX), or by the
   user, SYSTEM, Administrators or TrustedInstaller (Windows), with no foreign
   replacement grant.
4. Final-parent rule. Self-owned and not group- or other-writable. On POSIX, a
   root-owned sticky directory is allowed for scratch only. On Windows, the owner may be
   the user, SYSTEM or Administrators, and the DACL may grant no other writer.
5. Volume. Windows only: local, NTFS, with persistent ACLs.
6. Physical identity. POSIX resolves once with `pwd -P` and re-verifies. Windows compares
   the final handle path for aliasing and leases every component.

**Transitions.** The decision is a single pass: `spelling-checked → links-checked →
resolved → ancestors-walked → final-rule → admitted | refused`. Any failure refuses, and
initialization then fails. Bash reports "Automatic staging is unavailable…" and exits 1
(~L911). PowerShell throws inside the `try` at ~L1699.

**Authorized actors and ownership.** Only the invoking user's own token. Administrators
and processes already running as the same user are outside the isolation claim (see
[R0015 Windows transactions](docs/r0015-artifact-transactions.md)).

**Invariants.**
- No fallback to a shared directory.
- On POSIX, everything after resolution inspects only the physical path.
- On Windows, the ancestor leases stay open for the whole attempt.

**Observed facts.**
- B1 and B2 are described in [R0015](docs/state-contracts/R0015.md).
- In run 43162309006, at installer SHA256 `288d8ba1…` and `4d1818f8…`:
  - Windows owner controls passed 50/50 per host, and the owner mutants were 4/4 killed.
  - Real default `USERPROFILE` and `TEMP` were admitted on windows-2022 and
    windows-2025.
  - Every default `TMPDIR` candidate was admitted on macos-15 and ubuntu-24.04.
- Run 43158222646 concluded success. Its replay of the old Bash bytes (blob `d7f8267d`)
  produced the EXPECTED failures of the macOS default-environment positives, which is
  the discriminator showing that B2 is needed.
- Delta against accepted main `3b0e6141`, from `git diff`:
  - The PowerShell staging and trust functions are textually unchanged.
  - In Bash `trusted_parent` and `verify_root`, only the field reads changed, from
    here-strings to process substitution.
  - The same R0016 change converted the other here-strings and here-documents to pipes or
    process substitution. That covers the embedded Python in `firefox_status`,
    `select_asset`, `validate_asset`, `expand_chromium_asset` and `download_preset`, the
    record reads in `detect_targets`, `download_tablissng_asset` and the selection and
    dispatch loops, and the two `cat` text blocks.
  - `discovery_path_output` and `firefox_discovery_python` are new (preview-only), not
    converted.
  - This is the Apple Bash 3.2 area. On the final bytes, it is covered natively by the
    R0016 macOS run 43173749688 suites, as recorded in the R0016 posix report:
    install-bash 26, entry-bash 25, staging-native 9, staging-parent 23, read-only 6 and
    preview 46. The R0015 job `posix (macos-15, Darwin)` in 43239081990 was never run.
- The R0015 suites were re-run on the R0016 installer bytes at head `dfff0f8f`:
  - Run 43239081990 is green on Linux and on windows-2022 and windows-2025, including
    the owner/archive controls, the default-environment gates and the standard-user
    observation. `environment-posix (macos-15)` was green on attempt 3.
  - Run 43239087955 passed the staging-parent suite on ubuntu-24.04 and macos-15.
  - Both runs are recorded in [R0016](docs/state-contracts/R0016.md), "Successor
    receiving and merge record".
- `posix (macos-15, Darwin)` in run 43239081990 never acquired a runner, and that run's
  overall conclusion is failure. The R0015 job's own macOS run is absent. The macOS
  native staging suites on the final bytes come from the R0016 run 43173749688 instead.
- The Windows staging parent (`$env:TEMP`) and the compiler parent
  (`[IO.Path]::GetTempPath()`, which prefers `TMP`) are read from different sources.
  Each is admitted independently.

**Hypotheses.**
- A root-created link to a physical name that contains a newline passes the
  supplied-spelling newline check. R0015 records this as theoretical and root-only.

**Unknowns.**
- Domain-joined, roaming and Windows 10 profiles, recorded as NOT DONE in R0015.
- macOS extended ACLs. The mode-only checks do not consider them (pre-existing, NOT
  DONE).

**Hardening status.**
- B1/B2 final-parent rules: `independently verified` for bytes `288d8ba1`/`4d1818f8`
  (run 43162309006; independent reviews of `852d026c` recorded in R0015).
- Same rules on the merged bytes: `enforced and covered by tests`. Re-run in 43239081990
  (Windows owner controls; default environments on Linux, Windows and macos-15) and
  43239087955. The macOS native staging suite was not re-run.
- Private-child owner term (`$private` / `privateAcl` require owner = user):
  `enforced in code`. R0015 records that no mutant pins it.
- Refusal-message wording ("not owned by this user"): `unresolved`. It under-describes
  the admitted owner set. This is recorded in R0015's NOT DONE follow-up list
  ([R0015](docs/state-contracts/R0015.md), "Recorded follow-ups, NOT DONE").
- The transaction contract's former "self-owned immediate parent" sentence: corrected in
  [the R0015 Windows transactions contract](docs/r0015-artifact-transactions.md) to state
  the current rule; now `documented`.

---

## ISM-INST-004: Private staging attempt (roots, identity, cleanup, interruption)

**Scope and purpose.** Governs the per-invocation pair of private roots. The scratch
root is transient and deleted after identity checks. The retained bundle root persists
for manual use. This machine also governs what cleanup may delete.

**Authoritative sources.**
- [`install.sh`](install.sh): `initialize_staging` ~L189, `verify_root` ~L152,
  `guard_owned_path` ~L165, `cleanup_staging` ~L208, `finish_installer` ~L214, and the
  traps ~L221–223. The `WORK_ROOT`, `WORK_ID`, `BUNDLE_ROOT` and `BUNDLE_ID` globals are
  set at ~L40–41.
- [`install.ps1`](install.ps1): `Initialize-Staging` ~L693, `Assert-OwnedStagingPath`
  ~L608, `Clear-OwnedScratch` ~L727, and the `try`/`finally` around dispatch
  ~L1699–1741.
- Contracts: [R0015](docs/state-contracts/R0015.md) and
  [R0015 Windows transactions](docs/r0015-artifact-transactions.md), "Manual files and
  lifetime".
- Tests: [`tests/install-bash.py`](tests/install-bash.py),
  [`tests/install-staging-native.py`](tests/install-staging-native.py) (exit, failure,
  INT and TERM boundaries), [`tests/install-mutations.py`](tests/install-mutations.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1),
  [`tests/install-staging-windows.ps1`](tests/install-staging-windows.ps1).

**Independent dimensions.**
1. Attempt status. Bash: unset, then initialized. PS `StagingAttempt.Status`:
   `initializing`, `active`, `initialization-failed` or `closed`.
2. Scratch root: absent, created and unverified, verified, or deleted or retained.
3. Retained root: absent, created and unverified, or verified. It is never deleted by
   the installer.
4. Leases (PS): ancestor and root handles, live or disposed.
5. Exit cause: normal exit, failure status, INT (130), TERM (143), or uncatchable
   termination.

**Transitions.**

| From | Event | Guard | To / effect |
|---|---|---|---|
| unset | eligible selection confirmed | trust admitted (ISM-INST-003); Bash requires DRY_RUN=0 and is idempotent (a second call re-verifies both roots, ~L191); only PS throws on re-entry (~L695) | exclusive creation (Bash `mktemp -d` under umask 077; PS `CreateDirectoryW` with a protected DACL at creation), then identity readback |
| created | identity readback fails | n/a | Bash: initialization fails, cleanup refuses deletion, and the root is retained with a warning. PS: `initialization-failed`, leases disposed, cleanup skipped and retained |
| PS `active` (inside `Initialize-Staging`) | creating the `downloads`/`presets` subdirectories fails (~L719–722) | n/a | `initialization-failed`. The already verified scratch is then retained, not deleted (safe, but it leaks) |
| verified | each write | `guard_owned_path` / `Assert-OwnedStagingPath` re-verify root identity and each component | write proceeds, or refusal |
| active | normal end or failure (Bash also INT/TERM) | Bash: the EXIT trap fires after INT/TERM is converted to an exit; PS: `finally` on normal end or a thrown error | scratch is deleted only if the root identity matches (Bash: `verify_root` then `rm -rf`; PS: every descendant private, plus identity, then `Directory.Delete`). Otherwise it is retained with a warning. The retained root is always kept |
| non-zero exit with a bundle | `finish_installer` | n/a | "Partial bundle retained; manual actions remain pending" |
| closed | cleanup invoked again | PS: the `closed` status returns early (~L730) | no-op |
| any | SIGKILL, host or window termination | no handler can run | scratch (and possibly partial candidates) remain in the temporary parent |

**Invariants.**
- Each invocation creates new roots with random names. No earlier root is ever adopted,
  reset or recursively removed.
- Cleanup deletes only the current scratch root after proving its identity.
- The retained root is never deleted by the installer.

**Observed facts.**
- Each invocation's root names are unique: `mktemp -d` templates in Bash, and the
  attempt GUID in PS (~L705–706).
- Bash `verify_root` checks the root's device, inode, owner and mode 0700, but not its
  descendants. `rm -rf` does not follow symlinks.
- PS `Clear-OwnedScratch` walks every descendant through `Get-OwnedStagingFiles` before
  deleting. It releases only the scratch root's own lease first.
- R0015 records that native Apple staging passed nine controls, including INT/TERM
  cleanup (on earlier Bash bytes).
- In run 43162309006, Windows transactions passed 28/28 and staging custody 8/8 per host.
- The R0015 suites were re-run on the R0016 bytes in run 43239081990 (attempt 3): the
  Linux posix job and both Windows jobs were green. The `posix (macos-15, Darwin)` job,
  which carries the Apple native staging and lifetime suite, never acquired a runner. The
  Apple INT/TERM evidence therefore still binds earlier Bash bytes.
- `trap` covers EXIT, INT and TERM only (~L221–223).

**Hypotheses.**
- A signal that arrives between `mktemp -d` returning and the assignment to `WORK_ROOT`
  or `BUNDLE_ROOT` leaves an unrecorded empty root. PowerShell has the analogous window
  between `New-PrivateStagingDirectory` and assignment to `StagingAttempt.Scratch`: its
  `finally` would see `initializing` and retain the root, without naming its path. This
  is untested.
- Bash probably runs the EXIT trap when it is terminated by an untrapped SIGHUP (a closed
  terminal). This is not covered by a cited test.
- PowerShell Ctrl+C probably still runs the `finally` (pipeline stop), so scratch cleanup
  would follow. No cited test covers it. A TERM-style process kill or a closed window
  runs no `finally` (see Unknowns).

**Unknowns.**
- Leakage after SIGKILL or a closed console. A kill cannot run cleanup. Leaked scratch is
  never adopted by a later run, because names are fresh, but nothing reports or removes
  it. This registry found no NOT DONE record for it in the R0015 ledger.
- Behaviour when INT arrives during the EXIT trap itself (re-entrancy during `rm -rf`).
- PowerShell interruption: no cited test exercises Ctrl+C, process termination or a
  closed console during an active attempt.

**Hardening status.**
- Freshness, confinement and identity-checked cleanup: `enforced and covered by tests`
  (`tests/install-bash.py`, `tests/install-staging-native.py`,
  `tests/install-mutations.py` predictable-root and retained-EXIT-deletion mutants; PS
  transactions and custody in run 43162309006). The Bash rows 21-04, 21-09, 21-10 and
  21-14 in issue 21 carry SATISFIED audit verdicts on earlier bytes.
- Kill-time and interrupt-window leakage: `unresolved` (documented here only).

---

## ISM-INST-005: Windows native helper compile and load

**Scope and purpose.** Decides whether the native staging helper type may be compiled
and loaded, and where the compiler may write. Every trust decision in ISM-INST-003,
ISM-INST-004 and ISM-INST-006 runs inside the loaded `SalahInstaller.StageNative` type.

**Authoritative sources.**
- [`install.ps1`](install.ps1): `Initialize-CompilerNative` ~L57 (in-memory P/Invoke
  emit), `New-StagingCompilerContext` ~L167, `Invoke-StagingCompiler` ~L262 (PS5.1
  `csc.exe` through `Diagnostics.Process`; PS7 `Add-Type`), `Clear-StagingCompilerContext`
  ~L228, and `Initialize-StagingNative` ~L338 (type check ~L341, TEMP/TMP redirect and
  restore ~L343–559).
- Contract: [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Ownership boundary"; history in [R0015](docs/state-contracts/R0015.md).
- Tests: [`tests/install-compiler-custody.ps1`](tests/install-compiler-custody.ps1),
  [`tests/install-staging-first-call.ps1`](tests/install-staging-first-call.ps1),
  [`tests/install-volume-policy.ps1`](tests/install-volume-policy.ps1).

**Independent dimensions.**
1. Session type state: whether `SalahInstaller.StageNative` and
   `SalahInstaller.CompilerNative` are already loaded in this process.
2. Compiler context status (`$script:CompilerScratch.Status`): `parent-admission`,
   `candidate`, `owned`, `compiling`, `compiled` or `closed`. Retained outcomes are
   `refused-before-create`, `retained-unproved`, `retained-compilation-failed` and
   `retained-cleanup-failed`.
3. Process environment: TEMP and TMP are redirected to the context and then restored,
   including the originally absent state.

**Transitions.**

| From | Event | Guard | To |
|---|---|---|---|
| type absent | first staging | parent and ancestors admitted, NTFS, token default owner is the user or Administrators | `owned` (exclusive private root and lease) |
| `owned` | compile | TEMP/TMP equal the context path, root empty, invocation not yet started | `compiling`, then `compiled`, then `closed` (verified deletion) |
| `compiling` | compiler failure or timeout | n/a | `retained-compilation-failed` (material kept, location reported) |
| `compiled` | cleanup proof fails | n/a | `retained-cleanup-failed` |
| creation succeeded, readback failed | n/a | n/a | `retained-unproved` |
| type present | any later staging in the same process | `-as [type]` succeeds (~L341) | compilation skipped. The existing type is used without re-verification |

**Invariants.**
- No compiler write precedes parent custody.
- A retained context is never an admitted artifact or bundle.

**Observed facts.**
- The R0015 sixth attempt (run 43028305607) and run 43162309006 report the compiler
  custody suites passing on both hosts. In run 43162309006, the helper compiled under the
  real TEMP on windows-2022 and windows-2025, and under a temporary standard user (a
  non-gating job).
- The README's primary Windows route is `irm … | iex`, which runs in the caller's
  session. A loaded type therefore persists after the run, and any later run in that
  session reuses it (~L341, ~L60–61).
- If compilation fails before `Invoke-StagingCompiler` starts, for example when
  `Add-Type -AssemblyName System.IO.Compression` throws, the context is still labelled
  `retained-compilation-failed`.

**Hypotheses.**
- After the script changes, a later `iex` run in the same session would use the trust
  predicates compiled by the earlier run, so the reused helper could be stale. A type of
  the same name defined by other code in the session would also be trusted. That code
  already runs as the same user, outside the isolation claim.
- Under `iex`, the script's `exit` statements end the hosting session. This is standard
  PowerShell semantics, not observed here.

**Unknowns.**
- Whether issue 20 (R0014) host obligations cover repeated `iex` invocation. Not
  examined.
- Cold-start compiler TEMP effects on hosts other than the qualified runners.

**Hardening status.**
- Compiler custody and environment confinement: `independently verified` for the native6
  scope (run 43028305607; the native6 receiving review in
  [R0015](docs/state-contracts/R0015.md)), and re-run green in 43162309006 on later bytes.
- Session-persistent type reuse: `unresolved` (documented here only).

---

## ISM-INST-006: Artifact admission and publication

**Scope and purpose.** Decides when downloaded or derived bytes become a ready artifact
that may be shown, copied or handed to a browser. The artifacts are the extension
ZIP/XPI, the unpacked Chromium tree and the configured preset.

**Authoritative sources.**
- [`install.sh`](install.sh): `download_tablissng_asset` ~L593, `validate_asset` ~L625,
  `retain_asset` ~L637, `expand_chromium_asset` ~L654 and `download_preset` ~L701.
- [`install.ps1`](install.ps1): `New-ArtifactRecord` ~L1182, `Download-Asset` ~L1334,
  `Test-ExtensionArchive` ~L1245, `StageNative.ReadZipCrcs` ~L429 and `Fingerprint`
  ~L412, `Publish-OwnedFile` ~L1195, `Get-AdmittedArtifact` ~L671,
  `Expand-ChromiumAsset` ~L1371, `Convert-ConfiguredPreset` ~L1453 and `Download-Preset`
  ~L1467.
- Contracts: [R0015 Windows transactions](docs/r0015-artifact-transactions.md), "One
  admission contract", "Supported archive checks" and "Preset schema and preservation".
- Tests: [`tests/install-bash.py`](tests/install-bash.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1),
  [`tests/install-archive-controls.ps1`](tests/install-archive-controls.ps1),
  [`tests/install-powershell-mutations.py`](tests/install-powershell-mutations.py).

**Independent dimensions.**
1. Record state. This is explicit in PS and implicit in Bash, where state is the file's
   location and name: a `.asset.*` or `.preset.*` partial, or the final name.
2. Byte proof: length, SHA256, ZIP CRCs, and the declared size and digest when the
   release supplies them (PS only).
3. File identity: volume and file ID in PS; root identity plus component guards in Bash.
4. Location: a scratch candidate, or a retained publication.

**PowerShell transitions** (from the contract, confirmed in source).
- Normal path: `unresolved → downloading → downloaded-unvalidated → validated →
  published → handed-off`, with `retained` at cleanup.
- Failures: `download-failed`, `validation-failed`, `publication-failed` and
  `extraction-failed` remain partial. They are never admitted.
- A same-attempt reuse whose readback has changed becomes `validation-failed`, and the
  artifact is reacquired.
- At cleanup, `published` and `handed-off` become `retained`. Any non-failed, non-retained
  record becomes `cancelled/partial-retained` (~L744–747).
- `Get-AdmittedArtifact` is the single readiness predicate. It requires a unique
  current-attempt record, current identity and unchanged bytes. For an unpacked tree it
  also requires the full file list and each file's digest.

**Bash transitions.**

| Path | Steps and outcome |
|---|---|
| Asset | Exclusive `.asset.*` partial in the scratch root; `curl`; ZIP integrity (`testzip`); rename to the final name. Failure leaves the partial in scratch, which cleanup removes |
| Same-attempt reuse | An existing final file in this attempt's fresh scratch root is revalidated before reuse (~L609–613) |
| XPI | Copied to the bundle as a partial, revalidated, then renamed. An existing bundle copy of the same name in the same attempt is reused without revalidation (~L643) |
| Chromium tree | Every member preflighted, then extracted exclusively into a new `mktemp -d` child. Failure: "partial bundle retained" |
| Preset | Partial in the bundle `presets/`; JSON validated; renamed. Failure leaves the partial in the bundle |

**Invariants.**
- No ready path before validation.
- Publication never overwrites. PS moves to a unique token name. Bash's guarded rename
  is not reached when the destination already exists.
- No cross-invocation cache adoption.
- Preview is never admitted (ISM-INST-001).

**Observed facts.**
- In run 43162309006: archive controls 9/9 and archive mutants 4/4 killed per host
  (backslash guard, digest, declared size, CRC); transaction mutations 22/22.
- R0015's native6 reviews (run 43028305607) cover 13 prerequisites and nine mutant pairs
  per host.
- On the R0016 installer bytes (head `dfff0f8f`), run 43239081990 re-ran the Windows
  transaction and owner/archive suites green on windows-2022 and windows-2025, and the
  Linux posix job green. The macOS posix job was not acquired, so Bash admission on Apple
  hosts was not re-run on these bytes.
- PowerShell shares state through `$script:` variables: `LatestRelease` (release
  metadata, fetched once per run), `WorkRoot`, `DownloadRoot` and `PresetRoot` (set by
  `Initialize-Staging`), and `StagingAttempt`. `StagingAttempt` and `LatestRelease` are
  reset to `$null` at the start of each run (~L52, ~L1140). Under `irm | iex` the
  variables live in the caller's session between runs (see ISM-INST-005).
- Bash `expand_chromium_asset` returns the directory of `sorted(manifests)[0]`, so a
  nested `a/manifest.json` sorts before a root `manifest.json`. PowerShell refuses an
  archive with more than one `manifest.json` and returns the validated manifest's
  directory.
- Bash has no declared-digest or size check and does not require an `https://` download
  URL. The R0015 Windows contract states that it does not certify the original Bash
  obligations.
- Bash `download_preset` rewrites with `str.replace('local=1', hash)` over the whole
  text. It does not validate `SALAH_WIDGET_HASH` characters, and its `read_text` and
  `write_text` normalise line endings. PowerShell rewrites only the canonical token and
  revalidates the fragment. The shipped preset contains `local=1` exactly once.

**Hypotheses.**
- A Bash `SALAH_WIDGET_HASH` containing JSON-escaped quotes could add iframe attributes
  while the result stays valid JSON. The value comes from the invoking user, or from the
  builder command the user copied. Untested.

**Unknowns.**
- Transport behaviour: timeouts, redirect scheme policy, and partial downloads during a
  slow network. R0015 records web-call timeouts as NOT DONE (section C). Bash `curl` sets
  no timeout.

**Hardening status.**
- Windows admission and publication: `independently verified` within the native6 and
  run 43162309006 scopes (R0015 ledger).
- Bash admission (rows 21-06 to 21-09): `enforced and covered by tests`
  (`tests/install-bash.py`; SATISFIED audit verdicts in issue 21 on earlier bytes).
- Bash preset rewrite scope and hash validation: `unresolved` (divergence; see Open
  findings).
- Transport hardening: `unresolved`.

---

## ISM-INST-007: Manual hand-off and retained bundle

**Scope and purpose.** Decides what the user is told and given for each eligible target,
and what the terminal summary may claim. It covers install-source resolution, clipboard
copying, page opening, acknowledgement and the retained bundle's lifetime.

**Authoritative sources.**
- [`install.sh`](install.sh): `install_tablissng` ~L731, `show_import_instructions`
  ~L784, `open_url` ~L236, `copy_text` ~L260, and the dispatch loop and summary
  ~L914–952.
- [`install.ps1`](install.ps1): `Install-TablissNG` ~L1535, `Show-ImportInstructions`
  ~L1501, `Open-TargetUrl` ~L768, `Copy-Text` ~L788, and the dispatch loop and summary
  ~L1704–1737.
- Contracts: [R0016](docs/state-contracts/R0016.md), "Product behavior under
  qualification"; [R0015 Windows transactions](docs/r0015-artifact-transactions.md),
  "Manual files and lifetime".
- Tests: [`tests/install-powershell-routes.ps1`](tests/install-powershell-routes.ps1),
  [`tests/install-entry-bash.py`](tests/install-entry-bash.py),
  [`tests/install-powershell-transactions.ps1`](tests/install-powershell-transactions.ps1).

**Independent dimensions.**
1. Resolved source per target: `store`, or `github`. `ask` is resolved by a prompt.
2. Artifact availability (ISM-INST-006).
3. Clipboard outcome: copied, or failed (best-effort).
4. Opening: opened, or `NO_OPEN`/`-NoOpen` printing the URL.
5. Acknowledgement: received, or input ended.
6. Preset: staged once per run, with a retry for the next target after a failure.
7. Terminal status: manual action pending, or nothing staged.

**Transitions.**

| Event | Bash | PowerShell |
|---|---|---|
| `ask` with an invalid choice | refused, exit 1 (~L738) | any input other than `2` selects GitHub (~L1544) |
| `store` | open or print the store URL, then ask for Enter | same |
| GitHub download or validation failure | fall back to the store page and acknowledgement | the same, inside the `try` (~L1596–1600) |
| Chromium extraction failure | `expand_chromium_asset` fails, so `install_tablissng` returns 1 and the run exits 1 (~L761, ~L934); partial bundle retained | `Expand-ChromiumAsset` throws inside the same `try` (~L1563), so it falls back to the store page (~L1596–1600) and the run continues |
| Artifact admitted | print the path, try the clipboard, open the manager page, ask for Enter; `ASSET_STAGED=1` | admission re-checked; record set to `handed-off` after the clipboard attempt, then the page opened |
| Acknowledgement input ends | `read_answer` fails, exit 1, partial bundle retained | `Read-Host` behaviour depends on the host (see Hypotheses) |
| Summary with nothing staged | "No files were staged…", exit 1 (~L950) | prints the retained bundle path and exits 0 |

**Invariants.**
- Enter is a user acknowledgement. It never proves that a browser installed or imported
  anything.
- The retained bundle is never deleted, and is never a later run's cache.
- The dashboard-replacement warning is always shown before an import.

**Observed facts.**
- R0016 records routes8 (run 43171927350): explicit store, ask-to-store, ask-to-GitHub
  and default ask-to-GitHub, in both browser families, on both hosts, with zero fallback
  rows. The fallback scope rests on the root-admitted original18/behavior15 reuse.
- `-NoOpen` and `NO_OPEN=1` change only opening (source ~L239 and ~L769).
- In PS, the final `Read-Host` (~L1595) is inside the same `try` as the download and
  hand-off.
- In Bash, an empty explicit `SALAH_WIDGET_PRESET_URL` disables preset staging
  (`${VAR-default}`, ~L24). PowerShell treats an empty variable as unset and uses the
  default URL (~L23).

**Hypotheses.**
- In a non-interactive PowerShell host, the hand-off `Read-Host` throws. The `catch` then
  prints a GitHub fallback warning and opens the store page after the asset was already
  handed off, and the next `Read-Host` ends the run. Traced in source; not executed.

**Unknowns.**
- Whether any test covers PS acknowledgement failure after a hand-off. None was found in
  the cited suites.

**Hardening status.**
- Hand-off re-admission, `NoOpen` semantics and truthful pending wording:
  `enforced and covered by tests` (routes8 run 43171927350; normal18 run 43171927589;
  full20 normal2 run 43220592915).
- Exit-status parity and the non-interactive acknowledgement path: `unresolved`
  (divergence; see Open findings).

---

<a id="ism-inst-008"></a>
## ISM-INST-008: Release metadata and asset selection

Original audit: **new (FND-F-11 omission; R0014 issue 20 behaviour)** · Lane papers: [F](docs/audit/post-rlgwo/lanes/F-installers-build-workflows.md) · Status D / I / V: **PEX / UNK / UNK** · Historical disposition: *new*

- **Scope and decision.** Which TablissNG release asset an installer selects. Partial entry: transitions not traced.
- **Sources.** `install.ps1` `$script:LatestRelease` L1140, `Get-LatestRelease` L1141-1150 (`/releases/latest`), `Select-TablissNgAsset` L1154; `install.sh` `select_asset` L560 (`/releases/latest` L566); `docs/state-contracts/R0013.md` ~L146-151
- **State dimensions.** release metadata {unfetched, fetched once per run}; selected tier — not traced
- **Guards.** not traced
- **Actors and ownership.** installers
- **Effects.** download URL (ISM-INST-006)
- **Invalid, duplicate, stale or concurrent risks.** not assessed
- **Status evidence.** D: R0013 preservation note · I: not examined · V: not examined
- **Work orders.** R0014 (issue 20, PR 48 docs); R0013 preservation constraint
- **Accepted evidence.** none examined in this audit
- **Tests.** not identified
- **Observed facts.** sources located by the integrator
- **Unknowns.** tier order; behaviour on missing or renamed assets; GitHub API failures

---

## Open findings

This section covers the installer entries. Repository-wide documentary findings are in
[FINDINGS.md](docs/audit/post-rlgwo/FINDINGS.md).

Classification: (a) material acceptance blocker requiring correction; (b) documented and
verified, no change needed; (c) material, but implementation or verification incomplete;
(d) non-blocking, or out of scope for later work.

**(a) Blockers.** None.

**(b) Documented and verified, no change needed.**

| Finding | Entry |
|---|---|
| Preview guards and the whole-entry early return on both hosts, within R0016's recorded scope | 001 |
| Eligibility gating before staging and at dispatch | 002 |
| B1/B2 staging-parent rules; re-run on the merged bytes except the macOS native staging suite | 003 |
| Identity-checked scratch cleanup, and retained bundles through exit, failure, INT and TERM | 004 |
| Windows artifact admission and publication with readback | 006 |
| Transaction contract's final-parent owner rule, now corrected | 003 |

**(c) Material, but implementation or verification incomplete.**

| Finding | Entry |
|---|---|
| Host-wide zero effects and transport absence in preview are not established: no hard containment, null telemetry, and host start-up effects outside the installer's statements | 001 |
| Session-persistent `StageNative` reuse under `irm \| iex` (possibly stale predicates) | 005 |
| `posix (macos-15, Darwin)` not acquired in run 43239081990, so Apple native staging, lifetime and admission were not re-run on the merged bytes | 003, 004, 006 |

**(d) Non-blocking, or out of scope for later work.**

| Finding | Entry |
|---|---|
| PowerShell drops malformed or unknown selection tokens instead of refusing them (Bash refuses) | 002 |
| No mutant pins the private-child owner term; the refusal text under-describes the admitted owner set (recorded NOT DONE in R0015) | 003 |
| Newline check only on the supplied spelling (recorded as theoretical in R0015) | 003 |
| Kill-time or closed-console scratch leakage, and the interrupt window before a root is recorded (no prior NOT DONE record found) | 004 |
| Bash preset rewrite replaces `local=1` across the whole text, does not validate `SALAH_WIDGET_HASH` and normalises line endings; outside the Windows transaction contract | 006 |
| Bash publishes with a rename after validating the partial, without a post-rename readback. Same inode in the private root; issue 21 row 21-07 requires validation before publication | 006 |
| Transport timeouts and redirect policy (recorded NOT DONE in R0015) | 006 |
| PS non-interactive acknowledgement can trigger a store fallback after a hand-off; PS exits 0 when nothing was staged (Bash exits 1); empty preset URL differs between hosts | 007 |
| README sentence "Preview creates, overwrites and deletes no files or directories" is stronger than the host-level evidence. Two examples are the PowerShell host's own start-up profile writes, and Bash discovery running `python3` from PATH, whose start-up the installer does not control. A wording change would need a new R0016 documentation receipt, because `tools/qualification/installer_preview_docs.cjs` pins the README SHA256 and that sentence. It therefore ties to rows 22-14 and R0016-A06 | 001 |

### Final focused sweep (2026-11-12, merged main `e4dbf91b`)

The merged `install.sh` and `install.ps1` were re-read for five transition classes.

1. A refused, held or unknown target reaching staging or download. Not found. Staging
   needs at least one eligible selected target (Bash ~L910–911; PS ~L1695–1700). Each
   dispatch re-derives eligibility and skips held and refused targets before any
   install or preset call (Bash ~L922–931; PS ~L1707–1719).
2. Cleanup acting on a path whose identity was not verified. Not found.
   - Bash `cleanup_staging` deletes only after `verify_root` matches the recorded
     identity (~L210). Bash does not identity-check descendants, but `rm -rf` follows no
     links inside the 0700 root.
   - PS `Clear-OwnedScratch` (~L733–740) and `Clear-StagingCompilerContext` (~L234–252)
     verify the root and every descendant first.
3. A preview path reaching staging, network, clipboard or open. Not found. Both
   installers exit at the preview branch (Bash ~L871; PS ~L1666) before terminal
   acquisition or staging, and every effectful helper is guarded.
4. An artifact used before its admission completed. Not found.
   - Bash consumers receive a path only after validation and rename.
   - PS hand-off re-checks with `Get-AdmittedArtifact` (~L1509, ~L1560, ~L1564).
5. Publication without readback. Not found against an accepted guarantee.
   - PS `Publish-OwnedFile` reads back both the copy and the published file (~L1209,
     ~L1213).
   - Bash validates the partial and renames it without a post-rename readback, which
     is classified (d) above.

No transition was traced end to end that violates an accepted staging, ownership,
transactional-publication or preview no-effect guarantee on the merged bytes.
