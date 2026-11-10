# Independent R0007 Git trace repair review

status: FINAL
disposition: PASS — bounded successor diagnostic-boundary repair
requested_model: gpt-6-astra
actual_model_identity: GPT-6 Astra Pro (governing session declaration; separate backend identifier not exposed)
authoring_context_reuse: no
other_reviewer_output_seen: no
authority: findings only; no readiness, publication, acceptance, lifecycle, release, or closure authority

## Disposition and exact scope

**PASS for the commissioned two-hunk successor repair.** The original P1 credential-file witness now passes against the exact successor with only its helper path and expected digest changed. A real disposable local Git push still reaches the exact intermediate commit, while the requested Trace2 file is absent and the synthetic credential is absent from the structured receipt and repository configuration. No new gap was found in this bounded scope.

The original FINAL GAP-REVISE report, SHA-256 `b498f78445a670d4239fcf75b76fe5643f4f54748f4ce96ff436a26e5f1e01f2`, remains valid historical evidence for the predecessor. Its original failure, witness, and raw local fixtures were preserved unchanged. This successor finding establishes repair of the demonstrated diagnostic boundary at the digest below; it supplies no hosted-publication success or audit closure.

| Frozen input | SHA-256 |
| --- | --- |
| `FROZEN-PACKET.json` | `d19054f3a0c19f0a38c08d6b6b9fa01da0a26666bfbf14a34d59a1a05ed2eed6` |
| `prepare_payload.py` | `42e5c247d8c72555532df356943a41257db903c9b524775489e1567a9482896a` |
| `templates/materialize.py` | `a8f29b539550f7664a67856c55637cdc18ea9fcf7c59cffc65660e05ca19bc83` |
| `templates/r0007-materialize.yml` | `cea1f7925de6e02b929163f0780b4f79960fd4e6f9d1fb4fe61eda957bb65574` |
| Author `tests/test_trace_boundary.py` | `01123e1272acb496e1e1b1f6cf4de9c54eeb31584432a4b2af35069e676ef861` |

All **198 packet-listed files** matched their recorded byte lengths and SHA-256 values. The production predecessor in `baseline/` matched the previously reviewed digests. The packet includes other-review/Andon provenance paths; those bytes were hashed opaquely for manifest integrity, and their contents were neither decoded nor inspected. No other reviewer's reasoning or disposition was used. No author reasoning report was needed. The separate model backend identifier is unavailable to this reviewer; stronger attestation remains parent-owned routing metadata.

## Exact change and credential timing

Direct comparison establishes precisely two production hunks in `materialize.py`; the preparer and workflow are byte-identical to their reviewed predecessors. The three pre-existing control sources are also byte-identical. The complete supplied diff contains those two hunks and the new 156-line trace test; its contents reconcile to the actual files.

1. `child_env()` now builds a fresh environment that excludes every key beginning `GIT_TRACE` and the exact key `GIT_CURL_VERBOSE`. It continues to remove both publication-token variables and enforce literal pathspecs. The prefix includes the demonstrated event, normal, performance, environment-enumeration, curl, and trace-redaction controls. The parent environment is not modified.
2. The existing names-only, include-aware effective Git configuration check now refuses any lowercased name beginning `trace2.`. It runs before askpass creation, token attachment, or the push attempt. The existing fixed refusal class is retained; raw configuration values are not added to evidence.

The actual push still obtains its environment from `child_env()` and adds `R0007_PUSH_TOKEN` only afterward. Commit checks, configuration inspection, TLS checks, and readback remain credential-free. Effective tracing configuration may create a diagnostic file during those earlier Git calls, but those children lack the publication credential. The successor's configuration controls demonstrate that distinction: four configuration cases leave token-free trace files and stop before push. Credential confinement is the reviewed claim.

This change preserves existing configuration and hooks. It filters diagnostic environment settings only in controlled child copies and refuses effective tracing configuration without rewriting it. The configuration check includes included global configuration and environment-injected configuration names. The injected-count case is a refusal-policy control: it did not activate a trace sink in the predecessor on the observed Git 2.52.0, so it is not counted as a reproduced credential leak.

## Independent original witness: before and after

The original witness was copied into this review directory. Mechanical reverse replacement proved that **only** its helper-directory literal and expected helper SHA-256 changed. `witness-rebinding.diff` records the two substitutions; no assertion, environment setting, fixture setup, or publication call changed.

| Observation | Original witness | Rebound successor witness |
| --- | --- | --- |
| Helper digest prefix | `d17689992e2d` | `a8f29b539550` |
| Test result | One test, one failure | One test, exit 0 |
| Helper result | `REMOTE_REF_VERIFIED_INTERMEDIATE` | `REMOTE_REF_VERIFIED_INTERMEDIATE` |
| Local remote commit | Exact intermediate | Exact intermediate |
| Synthetic credential persisted in trace | Yes | No |
| Credential in structured receipt / Git config | No / No | No / No |
| Production endpoint or real credential | Neither | Neither |

Successor fixture: `fixtures/trace-boundary-sp_v09i_`. Its expected and observed intermediate are both `f574be5d84e29e1205cd015187c034a20cf513eb`. The `evidence/git-trace2.jsonl` path is absent. The held-out test and producer output are preserved in `test_trace_boundary.py`, `trace-boundary-producer.json`, and `trace-boundary.log`.

The rebound test SHA-256 is `639d2f90cfc1fdbba4860f9f7c37892b0606d2f6e1bf96f7460c3753bbfacb44`; its original is `b828725da99221ede94c38a0b2f7a1112187b63f3b8f7b7260a98a47e589fae2`. The new log SHA-256 is `c29ae20e938d9a15aa182b71eda3f33beb30ceb4b0be1f553a65f3aae22663f7`. This is a positive real local push, which rules out an always-refusing implementation as the explanation for the held-out result.

## Author evidence independently assessed and reused

The complete new trace control source and the exact 31-test producer/log were inspected. All eight trace result records in the final log match the corresponding packet-bound witness JSON. Each is bound to the successor helper digest and Git 2.52.0.

| Control group | Cases | Observed behavior |
| --- | --- | --- |
| Inherited event, normal, and performance trace environment | 3 | One successful push each; exact intermediate readback; no trace file; no credential persistence; parent environment/configuration unchanged |
| Global event, normal, and performance `trace2.*` targets | 3 | Refusal before push; zero attempts; remote remains seed; configuration unchanged; no credential persistence |
| Included global trace configuration | 1 | Refusal before push; zero attempts; remote remains seed; included/configuration files unchanged; no credential persistence |
| Environment-injected `trace2.*` configuration names | 1 | Refusal before push; zero attempts; remote remains seed; no credential persistence |

The controls scan all files in their disposable fixture for the synthetic credential, inspect structured receipts, verify configuration/parent-environment preservation, and distinguish successful sanitized-environment pushes from configuration refusal. Historical records retain the original four-case RED and the expanded eight-case RED: eleven leak records across those two runs and one non-leaking injected-count refusal-policy failure. Repeated scenarios are not counted as additional distinct leaks.

The unchanged clean positive receipt also remains successful: one push, accepted advertisement guard, exit zero, exact intermediate readback, and askpass removal. Its path is `test-runs-push/test_single_ref_push_updates_exact_intermediate_and_verifies_readback-stm_lh3e/evidence/push-result.json`. This supports continued operation in an ordinary environment independently of the negative configuration controls.

The author producer binds 31 tests, exit zero, helper digest `a8f29b...`, and trace-test digest `01123e...`. Its log digest is `f341efe9b049957c39b89b02c8cc1781f683ff688edb871c06db353b7e522999`. The previously inspected 23 guarded-push, authentication, tree, ancestry, and uncertainty controls are unchanged and were reused. This reviewer executed only the rebound held-out witness, not the full author campaign.

## Carry-forward boundary and remaining limits

Applicable prior findings on the fixed repository/ref, exact known seed ancestry, depth four, complete intermediate-tree identity, sole-parent commit, six-path finalization boundary, one normal guarded push, no force/retry, uncertain client outcomes, and askpass cleanup carry forward through exact unchanged code and the supplied controls. The two hunks do not expand endpoint, principal, permissions, ref, or mutation capability. A normal job Contents-write token remains broader than the helper's explicit effect ceiling.

This is a focused assessment of inherited Git diagnostics and effective `trace2.*` configuration. It does not establish security against arbitrary hostile runner code, concurrent configuration mutation, or independent operating-system instrumentation. No concrete unresolved risk in the commissioned boundary warranted another control campaign.

The latest fully identified engineering input from the original review was target `e46f9dae61b2990a2b5dd5007feaa8342bd0b748`, tree `6934f644f150dd2d41edb872b528b99fcd51f29b`. This successor review neither rebinds a later engineering target nor asserts working-tree cleanliness. Final payload preparation, clean target identity, exact actual-target dry reconstruction, current live owned-ref verification, hosted authentication/policy/large-pack behavior, post-effect reconciliation, and connector finalization remain root-owned. Earlier REST HTTP 422 causes remain unknown.

All new writes and disposable Git effects were confined to `publication-pack-successor-review`. No reviewed source, active candidate, real remote/ref, browser/server, network endpoint, or other review output was mutated. No subagent or `list_agents` call was used. `review-evidence.json` binds the inputs, source comparison, producer evidence, witness before/after, and reviewer artifacts. The bounded review is complete; no additional optional testing or repair was performed.
