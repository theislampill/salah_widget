# Combined-source documentation pin proposal

## Proposed change

The private proposal updates both README installer examples to immutable source commit `a4c617ebeedfb507c0cb7a472683cce47ad62522` and updates the documentation producer to admit the resulting README plus the accepted builder/config bytes. Only `README.md` and `tools/qualification/installer_preview_docs.cjs` are proposed for change.

The basis commit's tree was independently read as `7f7aca595593db5014dd0932476c35a85eb8ba0c`. Every source read used that immutable commit, or the specifically identified accepted-main commit; mutable worktree HEAD was not used for source identities.

No installer, builder, config, workflow, browser, native process, CI job, Git branch/index or remote publication was changed or executed. This proposal has no acceptance, release or closure authority.

## Exact proposed objects

| Proposed file | Bytes | SHA-256 |
| --- | ---: | --- |
| `README.md` | 45,556 | `b5df3f58f87368077798c205ac6cd682dee09ac2492e1f89d0dd6f6ec940923d` |
| `tools/qualification/installer_preview_docs.cjs` | 7,238 | `34ee696999b70115e7ef3154d54b02200cb1fe9d0486017ede877451ac806f15` |

`proposal.diff` is the complete diff against the immutable combined-source files. `source-bindings.json` records source and proposed byte lengths, SHA-256 values and Git blob identities.

### README

Exactly four 40-character commit values are replaced: two occurrences of the interim Bash pin `dc4c251d81ccb0796e70ff0516661204277232cb` and two occurrences of the interim PowerShell pin `81c698bea3bfa3e2a5abee2e92fe6bb0c82a80bb`.

The accepted-main wording is retained, including its separate Bash and PowerShell descriptions. Both descriptions and both command assignments now use the same combined-source commit. All other prose, commands, mode descriptions, manual-action instructions, byte-preserving Windows download guidance, preview promises and normal/NoOpen distinctions remain byte-for-byte unchanged. The resulting README therefore contains four current-pin occurrences, not the historical renderer's three.

The pinned installer objects in that source commit are:

| Source file | Bytes | SHA-256 |
| --- | ---: | --- |
| `install.sh` | 46,460 | `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f` |
| `install.ps1` | 111,249 | `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a` |

Later commits that change only harnesses or documentation do not invalidate these immutable source links. A later installer change would require a separate source-pin decision; it is outside this proposal.

### Documentation producer

The proposed producer changes only input and README-pin admission:

1. Replace the old required README SHA-256 with the proposed README identity.
2. Add exact builder and config SHA-256 guards beside the existing README guard.
3. Count the combined source commit in rendered README text and require exactly four occurrences.
4. Require absence of the two replaced accepted-main pins as well as the two already historical R0016 pins.

The result schema, output filenames, HTML styling, browser acquisition, routes, local/external request handling, screenshots, policy checks, builder-command checks, source-stability checks and browser cleanup remain unchanged. No renderer or installer claim is broadened.

## Required accepted builder/config inputs

The actual combined commit contains these authored files:

| Input | Bytes | SHA-256 | Git blob |
| --- | ---: | --- | --- |
| `src/native/builder.html` | 36,147 | `873e8dedfd4380d5bb8271945b23d73dc5afd3b5c8b848f67017cc4aaa41fd9f` | `5a3c9718f906800643b32ad477d5bae0c0ee14a1` |
| `src/native/config.js` | 29,516 | `719efed90a9173a7ca42216b0131631a2e0e219e5e45d8567e791784f425ed80` | `d281b8d8282c44c8d47e5e1fd9ba440a8432085e` |

Both were compared directly with accepted-main commit `3b0e614114ef066de40db117d0e85c0031cf3e30` and are byte-identical. Neither equals the historical documentation run's input: that run used builder `66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e` and config `91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81`.

Source inspection confirms the current builder still exposes the elements and functions used by the unchanged producer: `#install`, `#pv`, `installCmd`, `snippet`, `hash`, and `window.SalahConfig`. Its non-Windows install-command branch still targets `/main/install.sh`. This is a static compatibility observation; actual loading, text and pixels require the new render.

Adding the two explicit guards prevents an otherwise valid README from being paired silently with a different builder/config. The existing end-of-run stability check still verifies all three admitted inputs are unchanged.

## Workflow and rendering verification

The immutable combined-source documentation workflow is 2,836 bytes, SHA-256 `9fdb1d0bd81499640797ca1b13e79aa52299498773e163240292ddd90f385617`. No workflow edit is proposed.

Its existing push filters include both proposed files. Its sparse checkout already includes README, the authored builder/config and the producer. A normal documentation commit without `[r0016-acquisition-only]` in its commit message will satisfy the existing job condition. The existing workflow remains the intended rendering route; no CI job was started here.

The next rendering/receiving pass should establish all of the following against the newly published documentation commit:

- Exact README/producer/workflow bytes from that commit, with README target `a4c617ebeedfb507c0cb7a472683cce47ad62522` and the installer source hashes above. The rendering commit and pinned installer source commit are expected to be different objects.
- `inputs.json` and `result.json` agree on the three input identities in this proposal: README `b5df3f58…`, builder `873e8ded…`, config `719efed9…`, including exact byte lengths.
- The complete original stdout/stderr, dependency acquisition logs and lockfile, rendered HTML, visible text, result and three PNGs are retained. Existing output names are `readme-review-route.png`, `readme-preview-policy.png` and `builder-install-context.png`.
- Actual rendered README text has `pinnedOccurrences: 4`; every other existing README policy check is true; all replaced/historical pin strings are absent. Complete commands must be verified from original HTML/DOM text as well as their screenshot context, since long command lines can extend beyond a viewport.
- Actual builder facts retain the normal published-main install command and exclude DRY_RUN/NO_OPEN from that command. Review the captured install-button context and preserve the current actual `snippet`, `hash`, preview style and body facts.
- The result is complete, the browser is confirmed closed, page errors are empty, and the source-stability checks pass. Review the actual request record together with the unchanged routing code; do not impose the historical request list on a different accepted builder/config.
- The screenshots are visually reviewed for the requested documentation/builder context. This remains local rendered documentation evidence, not served-main parity, an installer execution, or native widget/physics visual acceptance.

No actual rendering result is available from this proposal. The existing workflow's acquisition-only skip and every historical success remain insufficient to satisfy this new-input render.

## Inert checks performed

`node --check` accepts the proposed producer. The producer was not launched.

Seven bounded VM checks exercise only extracted identity-guard and README-text predicate lines with supplied objects/raw Markdown:

| Check | Expected observation |
| --- | --- |
| Proposed README plus exact accepted builder/config | Accepted by input guards |
| Interim combined README identity | Rejected |
| Historical builder identity | Rejected |
| Historical config identity | Rejected |
| Raw proposed text with four pins and unchanged policy | Passes text-predicate preconditions |
| One current pin removed | Rejected |
| A replaced accepted-main pin reintroduced | Rejected |

All seven observations matched expectations. These are inert code/predicate checks; raw Markdown is not a rendered DOM, and none is evidence of browser layout or native behavior. `inert-checks.json` records this scope explicitly.

## Historical receipt preservation

The prior docs run was `43148106890`, attempt 1, source commit `51e9fdddb646373cf41b5f028b1abbb0d043b3f2`, tree `f220ef4d20d77cd9976bcfb862f37b806916925b`. Its received evidence remains untouched under `/tmp/r0016-third-20261111/work/acceptance_reconcile_restored/docs-native-receiving`.

That receipt binds the older README `b59a5bb5…`, builder `66f1cd86…`, config `91a37863…`, three pin occurrences, and producer `fe45d9d2…`. It remains historical evidence for those exact inputs. The proposed README and both accepted authored UI inputs differ; no previous rendering qualification is transferred. A compact historical-reference record retains the relevant original file hashes without editing that receipt or its verifier.

## Scope of the handoff

The root owns review, any application of these two private files, publication, CI/render execution and independent receiving. This handoff proposes no installer change and makes no readiness, acceptance or closure claim.
