# R0007 publication helper successor — independent review

status: FINAL
disposition: GAP-REVISE
model_identity: GPT-6 Astra Pro (developer-provided identity)
authoring_context_reuse: no
other_reviewer_output_seen: no
authority: findings only; no publication, acceptance, release, or closure authority

## Frozen review inputs

| File | SHA-256 |
| --- | --- |
| `publication-bootstrap/prepare_payload.py` | `fc85ff2ce1f65b677e2d955ecf0a4c1489cd84f0b94dfd73dd026f9594952b81` |
| `publication-bootstrap/templates/materialize.py` | `5c40102037ab6adc3a73ca27a80974eb71e3223a450ef04ffaea129dc9ffd55a` |
| `publication-bootstrap/templates/r0007-materialize.yml` | `77a56129d289e98083c2ea4b0fca42de10efc64ecae1d3bdd955456c332b3730` |

All three supplied hashes matched at review entry and again at finalization. The review covers the successor's UTF-8 byte identity, bounded diagnostic redaction, unchanged blob-only effect implementation, and expected seed-parent ancestry/currentness. Actual HTTP 422 causation remains unknown. I used my own earlier reviews and the preserved original program bytes. I did not read other reviewer outputs or an author reasoning report. The successor was authored by a different agent; I made no implementation change.

No real API call, browser, workflow, active source/index/ref mutation, or actual payload preparation was performed. Findings, a byte-identical copy of the supplied test file, test receipts, and independent pure tests are confined to this review directory. Only the supplied `TransportTests` were rerun: the copied suite's Git-fixture `SeedTests` were not executed. Independent ancestry checks evaluated the actual guard code against in-memory Git replies, supplemented by read-only inspection of the real declared parent commit.

## Disposition and substantive result

The UTF-8 transport branch preserves byte identity locally, the binary fallback remains lossless, and the successor's parent/base distinction supports the intended forward seed without loosening the cumulative four-file seed boundary. I found no new ref/commit endpoint, token-export path, redirected upload, workflow-permission expansion, or force operation in the three frozen files.

One confirmed security/privacy defect remains in the new error-receipt logic: an API message can copy a source fragment into the retained artifact. The redactor substitutes only the complete source content of small uploads; it does not sanitize partial echoes, and it does not inspect source text at all for uploads larger than 65,536 bytes. That is directly relevant to the large-blob use case and conflicts with the intended source-free diagnostic contract exercised by the supplied tests. The scope of this finding is retained diagnostic content; no real secret or actual remote response was used to demonstrate it.

**GAP-REVISE** is the code-level disposition for these hashes. It is not a claim that UTF-8 caused, or will resolve, the hosted refusal. Root owns any repair, new immutable binding, further review, and decision about authorized effects.

## Finding F-S1 — Partial and large-source echoes survive diagnostic redaction

| Required field | Finding |
| --- | --- |
| Finding title | Source fragments can be retained in HTTP error diagnostics |
| Category | Security / Privacy; Tests / Validation |
| Evidence | `templates/materialize.py:98–114` creates `source_text` and `encoded_content` only when `len(content) <= 65536`, then substitutes only those whole values. Lines 116–130 retain free-form message/documentation and selected error strings. `review_checks.py:81–92` and `independent-checks.log` contain two held-out failing witnesses. |
| Impact | A 422 or other HTTP error can place source text in an uploaded Actions evidence artifact. The current 81,702,660-byte offline-HTML class bypasses source-content substitution entirely. A partial echo also bypasses substitution for a small blob. The existing exact-token replacement is not disproved by this finding. |
| Effort | Small, bounded diagnostic-policy correction plus the held-out tests. |
| Risk | Moderate privacy/contract risk; the output is length-limited, but an API-controlled diagnostic string is still untrusted data. Actual occurrence in the hosted failure is unknown because that response body was not retained. |
| Confidence | HIGH for the reproduced code behavior. No claim that GitHub actually echoed source in run 42754815319. |
| Fix sketch / implementation route | Stop retaining unrestricted source-bearing diagnostic strings. A narrow route is to retain HTTP status, bounded body metadata/hash, and explicitly allowed diagnostic classifications/field values, while omitting or hashing free-form strings that cannot be established as safe. If source-aware redaction is retained, it must handle partial echoes and the large-blob path rather than only whole small bodies. Apply the policy to every retained string field, not only `message`. Preserve useful typed failure metadata and the no-retry behavior. |
| Repair class | product-or-skill defect (publication-helper diagnostic handling) |
| Owner/source | `publication-bootstrap/templates/materialize.py::http_error_details`; associated transport boundary tests. |
| Acceptance criteria | Both held-out privacy checks pass with the frozen synthetic inputs; full-small-source and exact-token redaction still pass; ordinary safe validation classification remains available; response reading stays bounded; HTTP failures remain terminal and attributable; endpoint, credentials, blob identity checks, and no-ref effect ceiling remain unchanged. |
| Verification | `PYTHONDONTWRITEBYTECODE=1 python3 /workspace/scratch/8726e3e6def5/analysis-r0007/publication-review-successor/review_checks.py`. Current result: 4 tests, 2 failures, with the two privacy witnesses failing and the positive redaction/ancestry checks passing. The supplied 9 pure transport tests independently reproduced as green. |
| Rollback / Plan Closure | Preserve these frozen bytes and failing witnesses. Root owns implementation, re-review of changed hashes, and any formal closure. Omitting unsafe diagnostic text can reduce exposure while retaining the existing HTTP status and body hash; it does not itself establish successful publication. |
| Rejected/deferred rationale | Not deferred in this disposition. The source-free diagnostic claim is part of this successor and the failure is reproducible without external effects. |
| Remaining risk | A future remote refusal may still lack enough safe detail to establish its cause. Useful diagnosis must not be obtained by silently broadening the evidence content contract. |
| Route | DMAIC; return to the owning parent for bounded repair and independent reconciliation. |

The witness uses only the obvious synthetic marker `SYNTHETIC_PRIVATE_SOURCE_FRAGMENT_739`. One test inserts it into an input larger than 65,536 bytes; the other inserts it between unrelated prefix/suffix bytes in a small input. In both cases a synthetic HTTP message echoes only the marker, and the helper retains it under `httpError.message`. The complete-small-input positive control is correctly redacted, which distinguishes the gap from a broken test setup or blanket failure of the helper.

## Claim-level assessment

### UTF-8 identity: supported locally

`materialize.py:139–155` now independently checks length, SHA-256, and Git's blob SHA before constructing a request. Strict UTF-8 decoding either succeeds and re-encodes to exactly the input bytes, or the input takes the base64 branch. The JSON encoder uses `ensure_ascii=False`; JSON escaping does not change the decoded string bytes. The supplied pure tests exercise BOM, Arabic, emoji, quotes, backslashes, CRLF, lone CR, tab, NUL, invalid UTF-8, wrong input identity, and wrong returned blob identity. I reproduced all nine transport tests successfully with every request opener mocked.

This proves local request construction and failure discrimination for those fixtures. It does not prove GitHub accepts the large request. The provided measurement file explicitly identifies itself as `fakeTransportOnly: true` and `remoteEffects: NONE`; its mock HTTP 201 rows are not remote success evidence.

### Actual hosted failure: attributable status, unknown cause

The retained hosted artifact records run `42754815319`, attempt `1`, seed `19004279805604ef5e41292ffd4e9f442e1321f2`, expected target commit `b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b`, and matching expected/observed target tree `1666a919dc9d197e9ff95d28eb013470ba822d5c`. Its first upload receipt records `offline.html`, 81,702,660 bytes, blob `7da1308517d143c38708ac9a0afbd0790e137e33`, and HTTP 422. The summary has zero verified uploads and exit code 1; the launcher producer also records exit code 1. The reviewed original helper has no job ref-update operation.

Those artifacts support exact reconstruction followed by a refused first upload. They do not establish the reason for refusal. The supplied local measurement records 82,904,481 bytes for the UTF-8 JSON request versus 108,936,917 for the former base64 request. This is a size reduction in the recorded mock measurement, not proof that request size caused the 422. I did not regenerate that real 81 MB request during this review.

### Expected-parent ancestry: supported within the bounded chain

`prepare_payload.py:51–76` binds a full `expectedSeedParent` that must be an available commit. It accepts the reconstruction base itself or a first seed whose sole parent is that base and whose complete base-relative delta is exactly the four bootstrap paths. Lines 88–95 place that parent in the hash-bound manifest.

`materialize.py:210–258` validates the parent field, rechecks the declared first seed's parent/delta, and requires the actual seed's sole parent to equal the manifest declaration. It still compares the actual seed cumulatively against the original reconstruction base, so successive bootstrap bytes cannot conceal an unrelated runtime change. The checks remain rename-disabled and NUL-delimited. They occur before patch application and builder execution.

The workflow's only revision is checkout depth 2 to 3. For the specifically admitted `base → first seed → successor seed` chain, that provides the objects needed for both parent checks and base reconstruction. This is deliberately not an arbitrary-length seed-retry chain.

I independently checked the actual declared parent using read-only Git operations: `19004279805604ef5e41292ffd4e9f442e1321f2` is a commit, its sole parent is `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`, and the rename-disabled NUL-delimited base-relative change set is exactly the four seed paths. The pure guard matrix covered eleven states: valid initial/forward seeds; wrong immediate parent; unrelated/merge/non-bootstrap prior seeds; extra/missing cumulative paths; a non-commit parent; base upload rejection; and base dry reconstruction. All behaved as expected.

These checks establish allowed ancestry and reconstruction identity, not live remote branch currentness. Root still must bind the actual new seed and use an operation that enforces the expected head for final publication. The new helper performs no remote ref query or ref update.

### Effect and credential bounds: preserved

The request still targets only `https://api.github.com/repos/theislampill/salah_widget/git/blobs` with POST. Redirects are refused and a failed or uncertain upload does not retry or switch endpoints. Workflow paths remain deferred to the connector, and all uploads occur after exact candidate-tree and per-blob checks. The child environment still removes the upload token and forces literal Git pathspecs. Checkout still disables persisted credentials; the workflow still requests ordinary `contents: write`, with unchanged timeouts and artifact retention.

Ordinary Contents write remains broader than the helper's code-level endpoint restriction. The unchanged executable-input trust qualification from the earlier review still applies. No new capability restriction is inferred from the new diagnostics or parent field.

## Evidence and verification record

| Evidence | Use and limitation |
| --- | --- |
| `publication-bootstrap/hosted-run-42754815319/attempt-3luhvrw2/summary.json` | Actual run/attempt, seed, target-tree equality, failed terminal status, zero verified uploads. |
| `publication-bootstrap/hosted-run-42754815319/attempt-3luhvrw2/upload-001.json` | Actual first-blob size/identity and HTTP 422; response body absent. |
| `publication-bootstrap/hosted-run-42754815319/launcher-producer.json` | Actual launcher exit code 1. |
| `publication-repair/transport-measurement-b20e3aa.json` | Read as explicitly mocked local measurement; no remote success inference. |
| `publication-repair/test_publication_transport.py` | Read in full; byte-identical copy rerun for `TransportTests` only. |
| `transport-reproduction.log` | Independent reproduction: 9 supplied pure transport tests passed. |
| `review_checks.py` and `independent-checks.log` | Independent positive controls, eleven-state actual-code ancestry matrix, and two held-out redaction failures. |
| `review-evidence.json` | Local frozen-file hashes and read-only real-parent metadata captured by this reviewer. |

The preserved original files match the exact three hashes from my previous revised review. I read the actual three-file diff and complete successor code. The supplied historical red/green test logs were inspected as producer evidence, not substituted for the independent rerun. No author reasoning report or other reviewer disposition was consulted.

A nested-JSON diagnostic probe in this runtime retained HTTP 422 and `HTTP_ERROR_STOPPED` with one request; it did not establish an additional terminalization finding. That observation is not a general proof for every possible malformed response. Optional testing stopped after the confirmed redaction gap and the requested identity/ancestry boundaries were discriminated.

## Remaining parent-owned decisions

Repair or explicitly reconcile F-S1, then rebind and review any changed helper hash. Bind the real corrected candidate and the intended new seed parent; preserve the existing evidence about the failed run without claiming its unknown cause. A successful future hosted result must be assessed on its own terminal producer, run/attempt, manifest, target tree, and blob receipts. The final connector tree/commit/ref transaction, permissions, independent R0017/R000B threads, and integration order remain outside this child's mutation authority.

This FINAL marker means the requested review is finished for the frozen three-file input. It does not establish publication readiness, implementation acceptance, native qualification, merge approval, or audit closure.
