# Preserved pre-overhaul widget

`v1/` preserves the production application served at the root when this snapshot
was taken. It is a compatibility copy, not a renderer candidate. The root runtime
is unchanged by this PR. Merge, deployment and release approval are out of scope.

## Source and deployment identity

- Source/main commit: `fd2972ba64225fe9d6848e92497e6d0ed20ea624`.
- Source tree: `c5382ee6cb32e71992da963f56b00c2eaa091d1c`.
- Observed at `2026-10-07T06:48:27.863780+00:00` (UTC).
- Pages API: legacy build, `main`, source `/`, HTTPS enforced.
- Successful Pages build: `1049380309`, commit above, completed
  `2026-06-17T00:35:36Z`.
- Successful deployment: `5087774417`, same commit.
- [Successful publishing run](https://github.com/theislampill/salah_widget/actions/runs/27657616486):
  build job records `jekyll-build-pages:v1.0.13`, Jekyll build, artifact upload and
  Pages deploy. Old text logs have expired (HTTP 410); job/build/deployment metadata
  remains available. No inference from the newest main commit alone was used.

HTTP 200 bodies fetched with identity encoding matched the pinned Git blobs:

| Production file | Bytes | SHA-256 |
|---|---:|---|
| `index.html` | 267280 | `446453b522f56f5f1bc0afd1a3abd09b73756754fa58a6b3b0ff09ce953a2eec` |
| `config.js` | 17516 | `fc8d80f3cd1baa31b3ace7e9e9cefad7add69695deaa042402bb4d78c293734f` |

No deployment transformation was observed in either runtime file. The production
intake receipt is in [v1/evidence/production.json](v1/evidence/production.json).
PRs #38, #39 and #40 are not implementation donors. No V5 archives were inspected.

## Payload and adaptations

Only two application files are needed: `index.html` → `v1/index.html` and
`config.js` → `v1/config.js`. Original comments, embedded Moon image data and
attribution are retained. The pinned tree contains no LICENSE/NOTICE file.
The builder, installers, presets, research and development files are not runtime
dependencies and are not copied into V1.

Every runtime adaptation is V1-local:

1. Prayer cache prefix `salah:` → `salah_widget:v1:prayer:`.
2. Weather cache prefix `salahwx:` → `salah_widget:v1:weather:`.
3. Settings key `salah_widget:config:v1` → `salah_widget:v1:config:v1`.
4. Temporary storage probe `__sw_probe__` → `__sw_v1_probe__`.
5. On the first local/preferLocal load without V1 settings, import valid schema-1
   root settings once. Root storage is read-only. An import marker is written even
   for missing/invalid root settings, preventing later root changes from reseeding
   V1. Reset retains the marker; caches are not imported. Existing V1 settings win.

The config file's original shared-builder comments describe its historical role;
this frozen copy now belongs exclusively to V1. Original root config remains
shared by the root widget and builder. No root storage is renamed or deleted.

Namespaces prevent normal root/V1 writers from colliding. They are not a security
boundary against arbitrary same-origin code. Third-party storage partitioning,
blocked storage or quota errors can prevent import/persistence; existing session,
coarse-location and manual-settings fallbacks remain. An import validates schema
1 and fields, not the provenance of an arbitrary future root writer. Clearing all
site data externally also clears the import marker.

`VERSION.json` records source/deployment, mapping, payload hashes, adaptations,
dependencies and limitations. `MANIFEST.sha256` hashes both runtime files and
`VERSION.json`, excluding itself. The verifier anchors the manifest hash outside
V1. Checkout-only `.gitattributes` preserves bytes across platforms and is not a
public runtime asset. No circular or self-hash claims are made.

## Dependency and Pages inclusion checks

The only local load is relative `config.js`, resolving to `/salah_widget/v1/config.js`.
CSS, JavaScript, SVG filters and lunar image data are inline. There are no local
imports, workers, dynamic local fetches, `<base>`, service workers, Cache API,
IndexedDB or cookies. Social links remain absolute external links.

Aladhan, Open-Meteo, RainViewer (including its returned radar tile host), GeoJS,
ipinfo, Nominatim, Zippopotam and Google Fonts remain external and mutable.
Provider responses, availability, terms and font bytes are **not frozen**.
Browser geolocation still depends on permissions, embedding policy and support.

Pages publishes the repository root through Jekyll (legacy build from `main`, `/`).
V1's public files have ordinary names and no front matter. Jekyll copies such
static files into the same subdirectories
([static files](https://jekyllrb.com/docs/static-files/),
[directory structure](https://jekyllrb.com/docs/structure/)); none matches Pages'
default exclusions. `.gitattributes` is intentionally excluded as a dotfile.

*Updated by R0037.* This section originally said there was no `_config.yml`.
That was true when V1 was preserved. R0017 added a root `_config.yml` in
`02ab7a93` (2026-10-14). It excludes only
`docs/rlgwo-execution/20261014/R000C/native`. A Jekyll configuration can drop V1
through an `exclude` (or equivalent) entry, so every configuration needs a
recorded V1 inclusion review. `python tools/verify_v1.py --check-pages` passes
only when there is no Jekyll configuration file, when `.nojekyll` is present, or
when exactly one configuration file (`_config.yml`, `_config.yaml` or
`_config.toml`) has a SHA-256 listed in `REVIEWED_JEKYLL_CONFIGS` in the verifier
and the listed evidence is JSON that names `v1/index.html`, `v1/config.js`,
`v1/VERSION.json` and `v1/MANIFEST.sha256` with the tree's SHA-256. Any other
state fails and names the file and digest. An edit to the configuration fails until the same change records a review.

The current `_config.yml` (SHA-256 `0f846f7e…`, blob `0700f748`) is admitted on the
measured deployed Pages artifact of merge `06772824`, which has the same blob.
That measurement lists `v1/index.html`, `v1/config.js`, `v1/VERSION.json` and
`v1/MANIFEST.sha256` with sizes and SHA-256 equal to the frozen tree. The
retained copy and cross-checks are in
[docs/state-contracts/evidence/R0037/config-0f846f7e/](state-contracts/evidence/R0037/config-0f846f7e/provenance.json).
The rule for admitting a later configuration is in
[R0037](state-contracts/R0037.md#admitting-a-jekyll-configuration). The check is an
inclusion preflight. It does not execute GitHub's hosted build or read the public site.

## Focused validation

```powershell
python tools/verify_v1.py --check-pages --negative-control
python tests/test_verify_v1_pages.py
node tests/v1_storage.cjs
python tests/v1_browser.py --chromium <installed-chrome.exe> --output <outside-repo-evidence>
```

The first two commands use only Python's standard library. The browser command uses
the already-installed Playwright and Pillow; no new packages or framework were
installed.

`--check-root` asserts that the root `index.html` and `config.js` still equal the
pre-overhaul production bytes. It was meaningful only before the root overhaul.
The overhaul deliberately changed both files, so `--check-root` now fails by
design. It is not part of the current recipe (corrected by R0037; the recipe
used to include it). Ordinary `python tools/verify_v1.py` must still pass.

The Windows browser fixture serves a disposable Pages-shaped layout. Both iframe
forms use `330×534`, border radius `28px`, `allow="geolocation"`, no-referrer and
no scrolling. Only `src` changes between `/salah_widget/#local=1` and
`/salah_widget/v1/#local=1`. Internal card remains `325×530`.

That fixture measured a `325×530` card inside a 5×4 px margin. The V1 card box
is `325×530` (`v1/index.html`: global `box-sizing:border-box`; `.c` sets
`width:325px;height:530px;border-radius:28px` and `box-shadow:0 18px 50px #0008`).
In a `330×534` wrapper, part of that shadow shows in the margin and in the
rounded-corner cut-outs; a `325×530` wrapper clips it. The two sizes are therefore
not pixel-identical for V1 (R0037 measurement). Which size the README V1 snippet
should use is an open owner decision (R0037 decision gate DG2); until then it
stays `330×534`.

Provider responses and observer coordinates are controlled fixtures. Browser time,
timezone, viewport, DPR and reduced-motion preference are controlled. Google Fonts
responses are acquired once, cached outside the repo and replayed identically for
both paths; exact font hashes accompany the captures. This is not live weather,
prayer-service accuracy, physical GPS or Tabliss-specific storage qualification.

Results and screenshots: [v1/evidence/VALIDATION.md](v1/evidence/VALIDATION.md).
The negative controls modify only disposable copies: a changed frozen file must
fail verification; replacing root index/config must leave V1 pixels unchanged.
No expensive CP9/V5 campaign is run. Existing legacy appearance (including shadows
and renderer approximations) is intentionally retained.

Non-V1 changes are limited to this documentation, README iframe usage, the AGENTS
preservation rule, the hash verifier and focused storage/browser tests/evidence.
No root runtime or deployment configuration changes are included.

## Combining with the renderer PRs

Git merge-tree checks against PR #39 at
`1977217cc2ac26fcc436b991aff498d306a0cd26` and PR #40 at
`890d5bdbc1244ad90e1113a86d60b25214daa7b0` found **no merge conflicts**.
Both calculated trees retain the complete V1 tree byte-for-byte and retain the
respective renderer's root index/config blobs. This was an object-only calculation;
neither branch nor any worktree was merged or changed.

Read-only inspection of their existing builders shows explicit writes to root,
`real-sky/` and `moon/`; neither traverses, regenerates or removes `v1/`. Their
source/generator ownership stays unchanged. The V1-local attributes override
broader root text rules. No renderer build/campaign was rerun. Future builder or
Pages workflow changes must retain V1 and run its verifier; these checks do not
approve either renderer's release or close its existing qualification obligations.

## Public deployment record

The `VERSION.json` limitation "Public V1 deployment is pending…" is frozen
historical text. It cannot be edited without a V1 byte change. This section
supersedes it. Retained evidence that V1 was served:

- 2026-10-08, deployed `c1a480c`: HTTP 200 and SHA-256 equality for the V1 files
  ([final-v49 public readback](real-sky/evidence/startup-cloud-20261007/final-v49/public-readback.json)).
- 2026-10-14, before `_config.yml`: the public `/salah_widget/v1/` loaded with the
  expected source SHA-256 and a 325×530 card
  ([R0007 consumer readback](rlgwo-execution/20261014/R0007/qualification/public-consumer-before/readback.json)).
- 2026-10-14, merge `06772824` (with the current `_config.yml`): the deployed Pages
  artifact contained all four V1 public files byte-identical to the tree. A
  public readback at 23:41 UTC returned `v1/index.html` with HTTP 200 and the
  expected SHA-256. Both are retained under
  [docs/state-contracts/evidence/R0037/config-0f846f7e/](state-contracts/evidence/R0037/config-0f846f7e/provenance.json).

No public V1 readback after 2026-10-14 is retained. Repeat this smoke after
deployments that may affect V1:

1. Confirm the deployment SHA contains this snapshot. Fetch `/salah_widget/v1/`,
   `v1/config.js`, `v1/VERSION.json` and `v1/MANIFEST.sha256` with no-cache requests.
   Compare each body with the reviewed frozen payload/manifest; expect HTTP 200.
2. Open the README iframe in the actual embedding host. Check local dependency
   requests remain under `/v1/`, settings open/save/reload, dates/prayer rows and
   countdown work, geolocation grant/denial stay usable, and footer is unclipped.
3. Confirm root still serves the expected current version. Repeat V1 hashes after
   later renderer deployments. Run `python tools/verify_v1.py` after their builds.

The original preservation PR did not claim or test the public V1 URL. The record
above was added later (R0037).

## Known limitations of the frozen copy

V1 is a frozen compatibility copy. It is not maintained and is not re-engineered.
The audits found the defects below. They are documented here, not repaired.
Repairing any of them changes V1 bytes and needs explicit owner authority and a
separate work order (R0037 decision gate DG1). Where a root work order is named,
the current version at the root URL has corrected behaviour for the same
mechanism. That work order changed only the root runtime, never V1.

If V1 misbehaves, reload the page, or open settings and save again. You can also
switch to the current version: change the iframe `src` to
`https://theislampill.github.io/salah_widget/#local=1`.

| Area (registry entry) | What can go wrong in V1 | Where (frozen source) | Root work order for the same mechanism |
|---|---|---|---|
| Settings import ([ISM-V1-001](../IMPLICIT_STATES.md#ism-v1-001)) | Root settings are imported once. The import marker is written first, so a storage failure after that write prevents any later import. This is intended: it also stops later root changes from reseeding V1. The import checks the schema, not who wrote the root record. | `v1/config.js` `loadLocal` L140-L164 | — |
| Location change (CF07, [ISM-V1-002](../IMPLICIT_STATES.md#ism-v1-002)) | Saving a new location or pressing Reset does not cancel or fence prayer, weather, radar, search or GPS work already in flight. A late result can be written under the newer location's globals or cache key. | `v1/index.html` `applyConfig` L2166-L2181, `resetForNewLocation` L2157-L2163 | R0003 |
| Prayer times ([ISM-V1-003](../IMPLICIT_STATES.md#ism-v1-003)) | Requests have no timeout or abort. A completion is not checked against the requested date, location or owner. The cache key is read after the await. | `v1/index.html` `cacheKey`/`saveCache` L735-L742, `fetchTimings` L743-L757 | R0002, R0003, R0006 |
| Weather ([ISM-V1-004](../IMPLICIT_STATES.md#ism-v1-004)) | Requests have no timeout. The busy and freshness flags are not tied to a location. A latitude or longitude of exactly 0 is treated as missing. | `v1/index.html` `fetchWeather` L771-L802 (guard L773) | R0003, R000D, R001E |
| Radar ([ISM-V1-005](../IMPLICIT_STATES.md#ism-v1-005)) | Freshness is the time the tile was received, not the radar frame time. Reset does not invalidate a pending request. Zero coordinates suppress radar. | `v1/index.html` `fetchRadar` L816-L841 (receipt time L837) | R000B, R000D, R001E |
| Settings Reset (CF08, [ISM-V1-006](../IMPLICIT_STATES.md#ism-v1-006)) | Reset says "Local settings cleared." even when the browser refused to remove the saved record. The record survives and is restored on reload. Stale search or GPS completions can overwrite a newer draft. | `v1/index.html` `_resetLocal` L2421-L2428 ignores the result of `v1/config.js` `clearLocal` L172-L178 | R0011, R000F, R0026 |
| Clock ([ISM-V1-007](../IMPLICIT_STATES.md#ism-v1-007)) | An invalid timezone falls back to the browser's local clock instead of failing. The clock follows a monotonic anchor with no wall-clock correction, for example after sleep. | `v1/index.html` `partsInTz` L704-L713, `simNow` L723 | R0008, R0020 |
| Moon texture ([ISM-V1-008](../IMPLICIT_STATES.md#ism-v1-008)) | A texture that fails to load has no failure state (no `onerror`), so the Moon stays pending. Recovery is a reload. | `v1/index.html` texture `grab` ~L956-L958 | — (the root uses a different Moon pipeline) |
| Stars ([ISM-V1-009](../IMPLICIT_STATES.md#ism-v1-009)) | The star field is a seeded synthetic decoration, not an astronomical catalogue. | `v1/index.html` star catalogue ~L1084-L1166 | — |
| Coarse location (CF09; root entry ISM-WX-010) | The lookup deadline is cleared when response headers arrive. A body that never completes leaves detection pending, and the fallback provider never starts. | `v1/config.js` `coarseDetect` L209 | R001F |

Evidence classes. CF07 and CF09 are demonstrated by source trace and, for CF09, a
mocked scheduler in the original audit. No production failure was measured. CF08
is demonstrated with an injected storage fault in a VM probe, kept as the
limitation witness `tests/v1_limitations.test.cjs`. A natural trigger (a
storage that fails removals but still serves reads) is not established. The other
rows restate the original audit's catalogue; R0037 re-read each against the cited
lines. The last column names where the root addressed the same mechanism. It is
not a V1 fix.
