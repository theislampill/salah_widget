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

Pages publishes the repository root through Jekyll. There is no `_config.yml`
exclusion or custom deployment workflow. V1's public files have ordinary names
and no front matter. Jekyll copies such static files into the same subdirectories
([static files](https://jekyllrb.com/docs/static-files/),
[directory structure](https://jekyllrb.com/docs/structure/)); none matches Pages'
default exclusions. `.gitattributes` is intentionally excluded as a dotfile.
No deployment setting or framework change is necessary. The verifier checks these
local inclusion prerequisites; it does not execute GitHub's hosted build. Public
artifact inclusion is the pending post-merge check below.

## Focused validation

```powershell
python tools/verify_v1.py --check-root --check-pages --negative-control
node tests/v1_storage.cjs
python tests/v1_browser.py --chromium <installed-chrome.exe> --output <outside-repo-evidence>
```

The first command uses only Python's standard library. The browser command uses
the already-installed Playwright and Pillow; no new packages or framework were
installed. Omit `--check-root` after deliberately changing the root renderer:
ordinary `python tools/verify_v1.py` must still pass.

The Windows browser fixture serves a disposable Pages-shaped layout. Both iframe
forms use `330×534`, border radius `28px`, `allow="geolocation"`, no-referrer and
no scrolling. Only `src` changes between `/salah_widget/#local=1` and
`/salah_widget/v1/#local=1`. Internal card remains `325×530`.

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

## Pending post-merge deployment smoke

Only after an owner-authorized merge and successful Pages deployment:

1. Confirm the deployment SHA contains this snapshot. Fetch `/salah_widget/v1/`,
   `v1/config.js`, `v1/VERSION.json` and `v1/MANIFEST.sha256` with no-cache requests.
   Compare each body with the reviewed frozen payload/manifest; expect HTTP 200.
2. Open the README iframe in the actual embedding host. Check local dependency
   requests remain under `/v1/`, settings open/save/reload, dates/prayer rows and
   countdown work, geolocation grant/denial stay usable, and footer is unclipped.
3. Confirm root still serves the expected current version. Repeat V1 hashes after
   later renderer deployments. Run `python tools/verify_v1.py` after their builds.

The public V1 URL has not been claimed or tested as deployed by this PR.
