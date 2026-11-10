# R0007 Git pack publication helper — independent review

status: FINAL
disposition: GAP-REVISE
requested_model: gpt-6-astra
actual_model_identity: GPT-6 Astra Pro (governing session declaration; separate backend identifier not exposed)
authoring_context_reuse: no
other_reviewer_output_seen: no
authority: findings only; no readiness, publication approval, acceptance, lifecycle, release, or closure authority

packet_sha256: a2edbe76df05e3d7b2ba8470a37c19c8f28587c1fce3d94c9298d66191826f84

| Production file | SHA-256 |
| --- | --- |
| `prepare_payload.py` | `42e5c247d8c72555532df356943a41257db903c9b524775489e1567a9482896a` |
| `templates/materialize.py` | `d17689992e2d392e8489018a58cc402676627d076515f99cd311eaee56b8e8d7` |
| `templates/r0007-materialize.yml` | `cea1f7925de6e02b929163f0780b4f79960fd4e6f9d1fb4fe61eda957bb65574` |

This is an independent review of the explicitly expanded normal-Git-push effect. No earlier blob-only PASS was carried forward as qualification of this new effect. The packet, design/plan/handoff, actual production code, direct diff, and hash-bound local controls were assessed as evidence, not authority. No subagent, live GitHub operation, browser/server, target change, or helper change was performed. Own findings and the disposable local witness are confined to this directory.

## Final disposition

**GAP-REVISE. One confirmed credential-file boundary defect requires reconciliation before use.** The inherited Git tracing environment can cause the authenticated push process to write its credential into a trace file, even though the helper's own receipts, argv, askpass file, and Git config omit that credential. A held-out real local Git push reproduced this behavior and still returned the helper's verified-success state.

The examined tree, ancestry, single-ref advertisement guard, normal push, and uncertain-result mechanisms otherwise support the intended bounded design. The supplied 23-control result was reused after inspecting its implementation and immutable evidence. No repeated full campaign or large real-target pack was run. The new evidence is one concrete credential-boundary failure plus read-only verification of the actual target/known ancestors.

This FINAL marker completes this child's finding record for the exact packet. It establishes no readiness, hosted-publication success, native acceptance, integration approval, lifecycle transition, or audit closure.

## Review identity, census, and evidence boundary

- Requested model identifier: `gpt-6-astra`.
- Actual identity available to this reviewer: the governing session declares **GPT-6 Astra Pro**. A separate backend model identifier/host attestation is not exposed in the allowed tools. No `list_agents` call was made. Parent-owned routing metadata must supply any stronger model attestation required by governance.
- `authoring_context_reuse: no`. This reviewer authored none of the packet's production helper, plan, design, handoff, or controls.
- `other_reviewer_output_seen: no`. No other reviewer's report or disposition was consulted. The packet's author handoff was read because the commission explicitly required it, and its claims were checked against code/evidence.
- All **100 packet-listed files**, including **70 selected local fixture receipts**, matched their bound byte counts and SHA-256 values. The frozen packet itself matched the supplied digest.
- `DESIGN.md`, `PLAN.md`, `HANDOFF.md`, all three production files, all three control files, and the final producer/log were inspected. All 672 lines and 17 hunks of `helper-changes.diff` were mechanically reconciled against the preserved originals and exact new files; the complete new production code was read directly.
- The 70 selected JSON receipts were parsed and classified. This census does not expand the packet to every unlisted disposable Git object database or imply a fresh hosted test.

## Finding P1 — Git Trace2 can persist the authenticated push credential

| Required field | Finding |
| --- | --- |
| Finding title | Inherited tracing can write the push credential to a file outside the helper's structured diagnostic path |
| Category | Security / Privacy; Tests / Validation |
| Evidence | `templates/materialize.py:48–54` copies the ambient environment; `:254–265` refuses selected hook/auth/rewrite/TLS settings but not tracing; `:290–297` attaches `R0007_PUSH_TOKEN` to that inherited push environment. `test_trace_boundary.py`, `trace-boundary.log`, and `fixtures/trace-boundary-r8k7p3jj/witness.json` reproduce the gap using real local Git 2.52.0. |
| Impact | A pre-existing diagnostic configuration can export the normal job credential into a trace file. If that target is under the evidence directory, the normal artifact step can retain it. The helper still reports verified publication because the ref operation itself succeeds. This is credential persistence even when the helper's own JSON and `.git/config` remain clean. |
| Effort | Small, bounded credential-environment/preflight hardening plus the held-out control; no change to the product or Git pack design is required. |
| Risk / priority | HIGH credential confidentiality impact; P1 for the advertised no-token-file boundary. The witness establishes an admitted configuration defect, not that the actual hosted job currently has tracing enabled or that a real credential has leaked. |
| Confidence | HIGH. The synthetic credential was found in the real Git Trace2 file after an otherwise successful single-ref local push. No network or real credential was involved. |
| Fix sketch / implementation route | Before credential attachment, refuse or safely isolate inherited Git diagnostic/tracing controls that can persist environment or authentication data. Cover the demonstrated `GIT_TRACE2_EVENT` plus `GIT_TRACE2_ENV_VARS` path and equivalent Git configuration sources, rather than checking only the helper's stdout/stderr or removing the credential afterward. Preserve pre-existing configuration and hooks; do not silently overwrite security controls. Use fixed, value-free refusal evidence. |
| Repair class | product-or-skill defect — publication-helper credential confinement |
| Owner/source | `child_env` / `publish_intermediate` in `templates/materialize.py`, with a focused credential-file control. |
| Acceptance criteria | The held-out tracing scenario, rebound only to the successor digest, either refuses before credential attachment or completes without persisting the synthetic credential; a separate clean-environment single-ref positive case still succeeds; tracing/config refusal preserves existing configuration; no credential reaches argv, script bytes, builder/readback environments, raw persistent diagnostics, or structured receipts; single-push/uncertainty and exact ref/tree guards remain unchanged. |
| Verification | `PYTHONDONTWRITEBYTECODE=1 python3 /workspace/scratch/8726e3e6def5/analysis-r0007/publication-pack-review/test_trace_boundary.py`. Frozen result: one test, one failure. The witness returns `REMOTE_REF_VERIFIED_INTERMEDIATE`, `refUpdated: true`, and `syntheticCredentialPersisted: true`; the trace remains retained locally. |
| Rollback / Plan Closure | Preserve the frozen packet and original synthetic failure. Root owns the bounded repair and independent successor review. This finding does not authorize any hosted retry or change in principal/permissions. |
| Rejected/deferred rationale | Not deferred: the defect is inside the explicitly requested credential-file boundary and is reproducible without hostile code, changed helper bytes, a network endpoint, or a real credential. |
| Remaining risk | A remediation must account for diagnostic configuration origins, not merely this one literal variable combination. The review does not claim an exhaustive proof against arbitrary hostile runner code. |
| Route | DMAIC / dispatch-review; return the exact witness and source owner to root. |

### Exact witness and discrimination

The fixture sets only a local bare repository as the in-memory test destination. The production module's fixed remote is patched in the test process exactly as the supplied local controls do; there is no production remote override. The real Git subprocess receives `GIT_TRACE2_EVENT` pointing to the fixture evidence directory and `GIT_TRACE2_ENV_VARS=R0007_PUSH_TOKEN`. All token material in the test is explicitly synthetic and has no authority.

The helper's advertisement guard accepts the exact update, Git performs the normal local push, and readback matches the intermediate commit. The resulting trace file contains the synthetic credential. The helper's structured result and `.git/config` do **not** contain it. This distinguishes the defect from the already-covered argv/config/JSON paths and explains why the existing clean-environment credential control passes while this witness fails. The raw local failure and trace were retained; credential values are not reproduced in this report.

## Verified actual inputs

Read-only object inspection in the target checkout established the following, recorded in `actual-inputs.json`:

| Input | Observed identity / property |
| --- | --- |
| Engineering target | Commit `e46f9dae61b2990a2b5dd5007feaa8342bd0b748`; tree `6934f644f150dd2d41edb872b528b99fcd51f29b` |
| Reconstruction base | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` is an ancestor of that target |
| Immediate prior seed | `3b2d09c748f71dc77806882f62f7339cbd18f19c` has sole parent `19004279805604ef5e41292ffd4e9f442e1321f2` |
| Earlier prior seed | `19004279805604ef5e41292ffd4e9f442e1321f2` has sole parent `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Both prior seeds | Exact rename-disabled, NUL-delimited cumulative base-relative delta: the four bootstrap paths |
| Target workflow changes | Exactly `.github/workflows/r0007-native.yml` and `.github/workflows/r0007-public-delivery.yml`; both ordinary `100644` blobs |
| Other target workflow | Baseline R0017 workflow remains the same blob `b670871f0776d9a9ff26a73addfcb6277405be79` |
| Reserved bootstrap paths in target | Absent |
| Target offline blob | 81,702,660 bytes |
| Builder/import closure and attributes | `build_native.py`, `build_moon.py`, `native_core_horizon.py`, `native_star_bootstrap.py`, `compact_receivers.py`, and `.gitattributes` are byte-identical to the accepted base; their hashes are retained in `actual-inputs.json` |

The target has 263 changed paths relative to base. Its changed tool paths are under `tools/cp9/` and `tools/qualification/`; no changed direct builder/import-helper file was observed. These are immutable-object checks, not a claim about the cleanliness of a later working tree. No final real target payload or dry rebuild was prepared by this reviewer. Root may add evidence and must bind/rebuild the selected final commit separately.

## Claim-level assessment of the new mechanism

### Repository/ref and effect expansion

The expansion from unreferenced REST blobs to a normal owned-ref push is explicit in the code, CLI, manifest schema, and workflow. `REMOTE` and `REF` are production constants. No CLI or manifest parameter selects a different endpoint. The manifest's effect list must equal the one fixed ref, and its finalization-path list must equal the six fixed paths. User authority for that isolated branch is supplied by root; the helper does not gain authority from its own manifest.

The push command contains one explicit full-SHA-to-full-ref refspec, no force prefix/option, no mirror/all/delete option, disabled automatic tag following, and disabled submodule pushes. This does not give a claim about arbitrary server-side behavior or a token cryptographically restricted to that branch: the ordinary job Contents-write capability remains broader than the helper's code boundary.

### Seed ancestry and complete intermediate tree

The preparer binds exactly two prior seeds followed by the reconstruction base, validates every supplied commit/edge, and requires the same four-path cumulative delta for each prior seed. The materializer repeats those checks, validates the executing seed as a sole child of the immediate prior seed, and binds publication to `GITHUB_SHA` and run attempt `1`. Depth four supplies the specifically admitted chain. The explicit immutable fixture overrides do not alter the fixed production destination.

The candidate is rebuilt with a separate index and must equal the full target tree before publication processing. Each changed blob is checked for mode, Git object ID, length, and SHA-256. `build_intermediate` then enumerates complete target and seed trees, creates the expected target-product/seed-workflow union in another index, compares the entire resulting entry map, checks the workflow-subtree ID, and requires exactly six differences from the final target. It does not merely test a selected sample of product files. The intermediate commit is created with the executing seed as its sole parent and that relationship is checked again before push.

For the actual observed inputs, finalization means the two target workflow additions plus removal of the four bootstrap files. Final connector commit/ref creation is outside this implementation and this review; it must independently produce the exact target tree over the verified intermediate.

### Advertised update and normal receiver currentness

The credential-free preflight requires the remote ref to equal the executing seed. The installed pre-push script is separately bound to a private intent digest and checks the actual push advertisement: exact remote name/location, exactly one update, exact new local identifier and object ID, exact destination ref, and exact old advertised object ID. It bounds input to 4,096 bytes and persists only fixed acceptance/refusal classes with exclusive creation. A changed intent, wrong ref, second update, rewind, advance, or remote mismatch causes refusal.

This advertisement check is necessary in addition to normal fast-forward behavior: a rewind could otherwise permit a valid fast-forward from an unintended old value. The supplied real-Git race control covers that window between preflight and advertisement. After advertisement, the command remains a normal Git push with its advertised old object ID, so the receiver's update check remains active; there is no force mechanism added by this helper. This review did not exercise the live GitHub receiver or add a separate after-advertisement race campaign.

### Uncertainty and one attempt

The intent/guard files and `PUSH_UNCERTAIN` record precede the push. There is one push subprocess call and no retry loop. A timeout, process failure, nonzero result, unavailable readback, or missing/invalid accepted guard cannot become verified success. After an attempted push, uncertain state uses `refUpdated: null`, not false. Verified success requires exit zero, an accepted guard receipt, and a matching credential-free remote readback.

The supplied completed-write-then-client-timeout control uses a real local push before injecting timeout and unavailable readback. Its frozen receipt stays uncertain with one attempt while the bare repository actually contains the new commit. The workflow launcher also uses unknown effect on abnormal termination. Existing publication receipts and the installed one-use hook prevent silent replay in the same lane.

### Credentials, configuration, hooks, and cleanup

The fixed askpass script contains no credential and responds only to the exact repository's HTTPS username/password prompts. Its real `git credential fill` control and wrong-host/path/scheme controls are adequate evidence for that prompt shape. Builders and ordinary Git/readback subprocess environments remove both token variables; only the authenticated push process tree receives the dedicated push variable. The push explicitly disables HTTP redirects and enables credential path matching.

Existing pre-push hooks, hooks-path settings, credential providers, URL rewrites, auth extra headers, or disabled TLS verification cause refusal without overwriting them. Exclusive file creation protects the new guard/intent paths. The askpass file is removed in `finally`, with cleanup success recorded. The installed guard is intentionally retained in the disposable checkout as a replay barrier; existing hooks/config are not replaced. Arbitrary push stdout/stderr is reduced to counts and hashes in the helper's own receipts.

Those protections do not cover the independent Git trace-file sink demonstrated by P1. The job credential therefore cannot yet be described as confined from persistent diagnostics for every configuration the helper admits.

## Evidence reuse and checks performed

The packet's `final-tests.json` binds the exact 23-test invocation and exit code zero; `final-tests.log` matches SHA-256 `b11b486abd43e5a2cad8eb7130939edb14d67faa1243b6b2afab18dd5ca18edc`. The inspected controls are 15 push/guard/config/uncertainty controls, six tree/ancestry controls, and two authentication controls. Positive real-Git controls prevent an always-refusing implementation from satisfying only negative cases. The observed result categories in the 70 selected receipts include refused-before-push, guard refusal/acceptance, verified intermediate, uncertain completed write, and dry tree reconstruction; historical and repeated receipts were not counted as additional independent test cases.

This review reused that bounded exact evidence instead of rerunning the 23-test campaign. Additional work was limited to the decision-changing Trace2 witness, the actual immutable-input checks, full packet hashing, complete diff reconciliation, and direct source/control-flow inspection. No production HTTPS endpoint was invoked. The local witness used Git 2.52.0; no claim is made that this constitutes hosted GitHub authentication or large-pack evidence.

Durable reviewer-owned evidence:

- `test_trace_boundary.py` — independent synthetic local-Git witness.
- `trace-boundary.log` — original failed producer output, retained unchanged.
- `fixtures/trace-boundary-r8k7p3jj/witness.json` — scoped result and discrimination metadata.
- The same fixture's `evidence/push-result.json`, private guard/intent, and synthetic Trace2 output — retained raw local evidence.
- `actual-inputs.json` — exact target/ancestor/workflow/builder identity observations.
- `review-evidence.json` — packet/file binding, census, artifact hashes, and review limitations.

## Residual limits and handoff

P1 requires bounded repair and independent successor assessment before relying on the no-credential-file claim. The previous REST 422 causes remain unknown, and this different transport is not evidence of their cause. The real GitHub authentication, policy, pack transfer, and resulting ref state are untested here. Credential-free preflight/readback can be unavailable and must remain a stop/uncertain condition rather than prompting a broader credential route.

Root separately owns final target preparation and exact dry reconstruction, current remote-ref verification before effects, any hosted operation, uncertain-outcome reconciliation, exact six-path connector finalization, and preservation of the R0017 → R0007 → R000B integration order. No sibling/main branch effect or merge approval is supplied by this report.

The concrete new defect is preserved and the requested bounded review is complete. No optional broader testing or helper repair was performed.
