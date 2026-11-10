# R0007 complete-input identity rebind and native reanchor — FINAL

**Disposition: PASS for this exact bounded test-input rebind and native-input reanchor.** No new concrete finding requires revision. The two new retained identities match the accepted source and the declared legacy transformation; admission code and prior records are preserved. Actual clean candidate binding accepts 31 cases and 147 native source files, all identical in case values/file hashes to the accepted 226 packet. This review supplies no native readiness, pixel acceptance, dispatch, integration or issue-closure authority.

## Identity, independence and execution boundary

- model_requested: `gpt-6-astra`
- model_actual: GPT-6 Astra Pro (self-report from the active developer identity; an independently inspectable backend model identifier is not exposed)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- candidate_commit: `e46f9dae61b2990a2b5dd5007feaa8342bd0b748`
- candidate_tree: `6934f644f150dd2d41edb872b528b99fcd51f29b`
- immediate_prior_commit: `9d24fb4b34f5979aac9961f34794ffbf4490e049`
- immediate_prior_tree: `0f0385b51b08e62a3668e8aa8e3534cadac70749`
- accepted_native_input_commit: `226c5e8fb1badc7244ca3fa4e0ce8d5f726972e5`
- accepted_native_input_tree: `d42f5ba6290aee94c677202cc64fba3024f427d5`
- accepted_product_source_commit: `5e946fe18a31750cf528bd58210ce79182dcf1e1`
- accepted_product_source_tree: `6e9eced1194d2463f5090fcdb086e771e1100916`
- native_executed: no

The retained private clone is `/workspace/scratch/8726e3e6def5/analysis-r0007/qualification-review-e46f9da/candidate`. It is a clean detached local clone of the exact candidate, with a sparse source-only checkout. The baseline control inputs under `prior-inputs` are exact Git exports from the immediate prior commit. All 27 selected candidate inputs and all 12 baseline inputs were compared against exact Git objects and their recorded SHA-256 values again at completion. No later target working-tree changes are credited.

Only source files, exact Git objects and this reviewer's own prior bindings/reviews were used. Author reports, author failure/green summaries, other reviewers' reports and Andon reports were not read. A complete diff path census verified that only the two named executable files changed outside `docs/`; the other 23 paths were classified by path only, without reading their report contents. No subagent or agent-list tool was used. The task brief's claims were treated as hypotheses and independently reproduced.

All writes stayed inside the declared review directory. No target repository file, index or ref was changed. No browser, server, network, remote write, hosted workflow, producer or native main was invoked. The affected Node suites use contained VM/provider/DOM doubles; their test runners execute local tests only. The repository AGENTS and requested audit playbook/Finding Row Contract were already read in the preceding bounded review. This remains plain engineering review, without formal audit-assess authority.

## Exact executable delta

`source-delta.patch` retains the Git diff. `structural-preservation.json` verifies both transformations mechanically:

- Removing the exact ten inserted lines from the candidate script contract yields the complete prior file byte-for-byte. Those lines add two explicit identity records and their comment.
- Reversing only the new transport parent commit/hash and retained expected hash yields the complete prior transport test byte-for-byte.

The seven other fixture/test owners used by the affected controls are unchanged. No assertion removal, changed parser branch, changed script layout, altered prerequisite digest or new fallback occurs.

| Executable file | Prior SHA-256 | Candidate SHA-256 |
|---|---|---|
| `tests/native-script-contract.js` | `adde2470bba5f276ddae71f0c5a2fad9485854604bbd733c87723583e04b578a` | `68f2480c6e340b512855e2ba99b16612fb0a6376e86b142707f3c41006ae1f64` |
| `tests/r0017-transport.cjs` | `48676a026db9c336229575e4dfcec121f8b6802b469eede53024f8e90db08f98` | `1d6833c403c97f0a2fdd288a725c2fbbf5587592bebae4346ceb50e696cca179` |

## Complete identity and provenance checks

| Input | Independently established SHA-256 | Provenance |
|---|---|---|
| Authored `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` | Actual 5e Git blob and exact current candidate bytes |
| Generated parent `index.html` | `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9` | Actual 5e Git blob and exact current candidate bytes |
| Derived legacy structural input | `c60eef46e0feeb4fcbc2daa34ec7069af470326648d8cf53943ee42a21865308` | Independently reconstructed from that exact generated parent |

The independent reconstruction finds exactly one complete `moon-initial-code` tag and one complete `moon-refinement-code` tag, removes each once, then inserts the literal file-protocol flag and `moon/moon-host.js` tag immediately before the unique closing body tag. All other bytes remain unchanged. The resulting complete document has the declared c60 identity. Its native script body is exactly the parent's native body. The transport test's actual emitted digest, parent commit, parent hash and transformation description match that reconstruction.

The legacy record explicitly describes a **derived structural control**, with parent provenance and `runtimeQualified:false`; it does not claim that the derived document was committed as `index.html` or that a legacy Moon runtime was executed. The transport positive still reaches the deliberately stopped parser boundary. The authored input is independently pinned to the actual source blob. These are explicit reviewed identities, not hashes learned from an untrusted input at admission time.

The candidate retains all six old identity records with every value unchanged; its retained set now has eight records. Every split prerequisite pin is unchanged. The exported parser, admission, setup-guard and error function source strings are identical to the prior module, as is the literal Moon file flag. The insertion-only source check also rules out additional top-level code changes.

The independent probe requires the actual unmodified admission module to compute decisions using real per-script and complete-source hashes. Both exact new inputs are admitted with the declared profile and provenance; the prior module rejects them as `SETUP_INCOMPLETE`. A single appended newline or a one-byte title alteration cannot reuse either new identity. Mutating the legacy flag or host remains rejected. Generated semantic mutants continue to use the existing split profile, while substituting an invalid native owner remains rejected. Thus the identity set expands by precisely two documents, with the previous structural boundaries preserved.

The probe exposes private constant maps only in a separate inspection copy to compare their values. All admission tests run the unmodified actual modules. `identity-boundary-probe.cjs` and `identity-probe-bindings.json` retain the reconstruction and checks.

## Independently reproduced controls and original failures

| Suite / command | Exact prior result | Exact candidate result |
|---|---|---|
| `node --test --test-reporter=tap tests/r0017-adapters.test.cjs` | 10 pass, 1 fail; exit 1 | 11/11 pass; exit 0 |
| `node --test --test-reporter=tap tests/hotfix-prayer-weather.test.cjs` | 0 pass, 21 fail; exit 1 | 21/21 pass; exit 0 |
| `node tests/r0017-transport.cjs` | 31 pass, 1 fail; exit 1 | 32/32 pass; exit 0 |
| `node --test --test-reporter=tap identity-boundary-probe.cjs` | Not applicable | 8/8 independent groups pass; exit 0 |
| `python verify-native-reanchor.py` | Accepted 226 packet used for comparison | Actual e46 binding and validation pass; exit 0 |

The original three prior-suite failures were reproduced from exact baseline inputs, not copied from author evidence. Adapters/hotfix failures report the stale complete-input admission boundary (`SETUP_INCOMPLETE: Unreviewed widget script anchors`); the transport positive retains the old structural literal and fails its explicit rebind assertion. Their original outputs are retained as `prior-adapters.log`, `prior-hotfix.log` and `prior-transport.log`. The corresponding candidate logs preserve all 64 passing controls, including the original missing/duplicate/changed prerequisite, downgrade, wrong-owner, unknown-script, missing-contract and legacy mutation negatives. No existing test was weakened or removed.

The initial independent probe failed before its eight checks because Node's default synchronous child-output buffer was smaller than the generated HTML. That reviewer-infrastructure failure is retained in `identity-boundary-probe.initial-enobufs.log`, with the original probe and run metadata. Only the review probe was corrected to use a bounded 4 MiB local-Git buffer and concise read-error handling; no candidate byte changed. The corrected eight checks pass. This infrastructure failure is not counted as either a candidate defect or a successful control.

Raw command arguments, working directories, exit codes and durations are retained in `affected-control-runs.json`, `independent-probe-runs.json`, `initial-independent-probe-runs.json` and the original logs. `identity-command.log` retains exact Git identity output.

## Actual clean native reanchor and exact binding membership

`verify-native-reanchor.py` imports the exact candidate launcher and driver without running either native main. It calls `clean_identity`, `select_cases`, `bind_packet` and `validate_cases` against the clean retained candidate. The result is **31 selected cases, 22 healthy before 9 mutants, 147 committed source files, `PREPARED_NOT_EXECUTED`**. Every selected case value and every one of the 147 source hashes equals the accepted 226 packet exactly. Only candidate identity/provenance metadata is reanchored to e46.

The requested membership question is answered from both actual packets:

| Changed shared file | In accepted 226 native source binding? | In actual e46 native source binding? |
|---|---|---|
| `tests/native-script-contract.js` | No | No |
| `tests/r0017-transport.cjs` | No | No |

Their absence is an observed property of the current binding, not an assumption based on their names. Their candidate digests are bound separately by this review's input manifest. This test-input rebind therefore changes no listed native acquisition source byte. The report does not treat source-binding membership as a universal claim about every possible consumer of the repository.

Twenty-one protected/native-helper/test objects equal both the immediate prior and accepted 226 objects. Thirteen product/generated/shared identities also equal accepted 5e directly, covering the full `src`, generated entries, config, builder/build tool, `real-sky`, `moon`, `vendor`, `v1`, shared prayer fixture, shared browser runtime and runtime-identity helper. Directory identity covers all tracked descendants. See `protected-identities.json` and `native-reanchor-verification.json`.

| Native input | Unchanged SHA-256 |
|---|---|
| `tools/qualification/r0007_native.py` | `d57416ad259713887ecfe913eed1ed509abbe589ccfe4bd5fae2a4a3722c156e` |
| `tools/cp9/r0007_browser.py` | `ac626e916160ef1359bdddf022483ac5d0602626e29439253fd4ddb253c2a48e` |
| `tools/cp9/r0007_font_observer.js` | `ca8fcb547fca54e5edd8ba40c896497c6cda75b38acc7a6e4df276a2eeb21d1b` |
| `tests/rlgwo/R0007-next-event-recipes.json` | `63899d8bdb86ec9576edf66ce73777eef5c05e03ee58f691d0ed776cc985941e` |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` |

The prior 24 qualification, 16 five-predicate font/barrier and 5 selector results are reused at verified unchanged source/test identities. The native driver, collector, observer, workflow, 31-case packet, clocks, ingress, deadlines and oracles are unchanged. No native campaign or unrelated source suite was rerun. The existing serial two-engine plan remains 31 cases per engine, with unchanged resource/time limits.

## Findings, limits and handoff

**New findings: none; PASS at this exact source/input qualification scope.** No Finding Row requiring repair is opened. The original setup failures are explained by explicit stale complete-input identities, and the narrowly reviewed rebind resolves them while preserving negative controls and history. This review does not reopen or claim to complete the R0017 owner, and does not confer merge authority from a shared test-file change.

The legacy transformation check is source/transport evidence only. VM controls do not establish native browser script loading, provider behavior, physical rendering, fonts or pixels. The native binder establishes committed inputs and source hashes; it does not establish successful execution, teardown, first eligible/visible recovery or preserved presentation. Required Windows two-engine native qualification and independent original pixel/video review remain pending. Earlier exact-scope QR-B20-01/02 closures remain supported by unchanged instrumentation bytes; no broader acceptance is inferred.

Required merge order remains **R0017 → R0007 → R000B**, with preceding accepted-main reconciliation and exact owner head/base/tree approval. Publication, readiness, certification, delivery and issue-closure gates remain separate and binding. This PASS applies only to `e46f9dae61b2990a2b5dd5007feaa8342bd0b748` / `6934f644f150dd2d41edb872b528b99fcd51f29b` and the stated bounded review scope.
