# T03 current documentation original receiving

**Status: FINAL — scoped PASS.** The original local-documentation archive, existing 47-check receipt, exact source revisions, and retained GitHub artifact/run records are joined. The independent data-only checker returned **exit 0: 71/71 checks**, consisting of **47/47 recomputed existing checks plus 24/24 additional source/provenance checks**. All three original PNGs were directly inspected in this receiving turn.

This completes the assigned T03 evidence join. It does not grant technical acceptance, public-delivery acceptance, issue closure, or authority over the complete obligation ledger.

## Identity and source boundary

| Object | Identity |
|---|---|
| Reviewer requested / actual | `gpt-6-astra` / `gpt-6-astra`, runtime self-report |
| Context | Continuation of the independent POSIX receiver; the existing historical 47-check receipt was explicitly supplied for this task |
| Root continuity supplied | `G0023`, receipt prefix `b372af20`; not re-established by this child |
| Accepted base | `3b0e614114ef066de40db117d0e85c0031cf3e30` |
| Requested head / tree | `9c05df0b7546a7c897c6e1ab5b197f0087b5c2e4` / `62e81ff8b568ac405f25cb5648579fb1ee19caf7` |
| Rendering commit / tree | `8a360f549a7d9ff291b91d2e62e848c72b78d38d` / `42a95457b7cfb17b4fc8ed9fe600d130f50390dc` |
| README installer pin | `a4c617ebeedfb507c0cb7a472683cce47ad62522` |

Immutable Git objects establish that README, authored builder/config, renderer, and documentation workflow are byte-identical between the rendering commit and requested head. Both pinned installers also equal the rendering and target-head bytes. Base, rendering commit, and installer pin are verified ancestors of the target. No working-tree changes affect these documentation inputs. Windows diagnostic changes are outside this receipt.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `README.md` | 45,556 | `b5df3f58f87368077798c205ac6cd682dee09ac2492e1f89d0dd6f6ec940923d` |
| `src/native/builder.html` | 36,147 | `873e8dedfd4380d5bb8271945b23d73dc5afd3b5c8b848f67017cc4aaa41fd9f` |
| `src/native/config.js` | 29,516 | `719efed90a9173a7ca42216b0131631a2e0e219e5e45d8567e791784f425ed80` |
| Documentation renderer | 7,238 | `34ee696999b70115e7ef3154d54b02200cb1fe9d0486017ede877451ac806f15` |

Input manifests, render result, stdout, prior receiving receipt, and immutable source agree. Authored builder/config are also byte-identical to accepted main and the target's generated root copies. Full source, workflow, installer, and Git identity records are in `source-bindings.json` and `provenance.json`.

## Actual retained GitHub association

`api/docs-api.json` contains the GitHub artifact object itself:

- Artifact **13922503861**, named `r0016-doc-context-43173749679-1`.
- `workflow_run.id` **43173749679**, branch `pro/r0016-effect-free-preview-20261111`, head **8a360f549a7d9ff291b91d2e62e848c72b78d38d**.
- ZIP size **906,459 bytes**, digest **`cd59428f8da84b5a4ecb92e0441410ad077bcd1105d12ba6e39e001e63a15156`**.
- Artifact and archive-download URLs contain the same artifact identifier.

The original ZIP matches those bytes/digest, the provenance join, and the prior receiving receipt. ZIP CRC, all **14 unique canonical regular payload names**, and every payload's exact bytes/digest pass. The original PNGs each decode as **1280 × 1000** and match their recorded hashes. The source workflow's checkout uses `${{ github.sha }}` and its artifact naming expression agrees with this actual artifact object.

The provenance join's independent-receipt hash matches the supplied 47-check JSON exactly: **`b44233da8d97f4efbd5c39bfc75e98defd7a5c7535146821de103c445fd9e39f`**. Retained refs identify accepted main and the requested target. This closes the formerly separate local-receiving/API association using original records, rather than relying solely on the join's `apiArtifactAssociationVerified` boolean.

**Freshness limit:** these are retained API snapshots. This child made no live API request and makes no new remote-currentness or job-status claim.

## Recomputed rendering and direct visual observations

All 47 original named checks were independently recomputed in their original order. They cover custody, source associations, complete HTML/DOM text, four immutable installer-pin occurrences, exact Bash and PowerShell preview calls, the full Windows download command, offline policy, normal builder command, bounded snippet dimensions, runtime/error records, and PNG identities.

The retained render result records Chromium **151.0.7922.34**, Node **v22.23.4**, `complete=true`, `browserClosed=true`, empty page errors, and empty renderer stderr. The retained lockfile agrees with the workflow's Playwright **1.62.1** and Marked **17.0.5**. No renderer, dependency installer, or browser was run during this receiving task.

| Original screenshot | Directly observed | Preserved limit |
|---|---|---|
| `readme-review-route.png` | Review-first heading, immutable pin, Bash download/read/preview/normal sequence, manual dashboard-replacement warning, terminal requirements, and Windows byte-preservation wording are legible. | One fixed viewport; not full-document pixel coverage. |
| `readme-preview-policy.png` | Offline/no-effect/no-prompt/unresolved/refusal policy and NoOpen normal-mode distinction are legible. | The long Windows acquisition line is horizontally clipped. Its full command is independently present in retained HTML/DOM. |
| `builder-install-context.png` | Install widget button and installation-wizard caption are legible with location/method and embed controls. | Widget region is blank and gets no widget runtime/pixel credit; this is not complete layout coverage. |

The actual captured builder command uses published `main/install.sh`, carries settings, and includes neither `DRY_RUN` nor `NO_OPEN`. The retained embed snippet/style is **325 × 530**. These are authored-builder/documentation observations, not public deployment parity.

## Remaining limits and usable outputs

The renderer records six request attempts, including GeoJS and ipinfo. Its exact source fulfills only the local README/builder/config routes and aborts other requests. Those attempts remain in the evidence. This is not an installer no-network experiment. The blank widget, clipped screenshot line, local-only rendering, and lack of served-main/raw/Pages/GitHub delivery readback remain explicit limits.

`checks.json`, `legacy47-recomputed.json`, `original-inventory.json`, `source-bindings.json`, `provenance.json`, and `visual-review.json` contain the complete derived check/source/provenance data. `check_docs.py` reproduces the data-only receiving; `execution.json` and `deliverables-manifest.json` bind the executed checker and outputs. The original 14 payload files are retained beneath `original/`.

Writes were confined to this receiving directory. There were no repository/audit-state mutations, external messages, native reruns, site launches, or closure actions. No further render is required by this source/provenance join because the admitted rendering inputs remain identical.
