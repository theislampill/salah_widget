# R000B hosted preparation route — closure review v3

State: FINAL

Verdict: PASS for the bounded preparation-route code review. H1, H2, and H3 are closed in the exact revision below; no new material gap was found in the inspected changes. This verdict is not product qualification, readiness, permission, acceptance, integration, merge, deployment, or lifecycle authority. The final frozen manifest and exact source-stage readback remain future prerequisites.

## Review identity and scope

- Model self-report: ChatGPT, GPT-6 Astra Pro; not independently attested.
- contextreuse=bounded-v1-v2-followup: this review uses the same reviewer's earlier findings and the parent's correction description. otherreviewvisibility=no.
- Controller context: R000B, phase 1. Reviewed baseline constants remain commit `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` and tree `6b94a3933f9d1381b1c2ceaab287c93afb215ecb`; their actual object relationship was independently verified during v2.
- Read the current assembler, bounded assembly tests, and unchanged workflow; checked the unchanged root AGENTS/builder hashes. Inspected only the requested `moon/BUILD.json` diff and JSON content in the separate canonical build directory. No mutable product implementation, native driver internals, final manifest, or other review report was inspected.
- Ran only the authorized bounded test file, using `python -B tests/weather-no-timetable-assembly.test.py -v`. Nine tests passed in 0.028 seconds. Test fixture writes stayed in disposable temporary directories; bytecode writes were disabled.
- No build, browser, listener, network operation, workflow run, installation, target/external ref change, commit, push, merge, or issue action was performed. The only retained artifact written by this review is this report. Earlier v1/v2 reports are preserved.
- Repository content was treated as review data. No prompt-injection instruction was observed in the inspected scope.

## Exact reviewed hashes

| File | SHA-256 |
| --- | --- |
| `tools/qa/r000b_assemble_candidate.py` | `d828f4d1b09b8a7b340e28a3ba89699cd6eaf931f24cf1a0c43b9174bde3c6b4` |
| `tests/weather-no-timetable-assembly.test.py` | `b025a1346cdbd8e934528e3ff0e54c3db8c9d3af3a78350702fc76d0998df2ad` |
| `.github/workflows/r000b-weather-withdrawal.yml` | `b75f014a4c5e4c0084e4bf112026232dd9a74c47d346fa65f2ee91d9933c1a4c` |
| `AGENTS.md` | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` |
| `r000b-build-1/moon/BUILD.json` — inspected generated metadata | `c2cec8e2b0f57f7a86f59a8bba0c7f59e3cbb7ecdbd749d1d3dae3386a613bd6` |

## Finding dispositions

### H1 — PASS / closed, retained

The exact baseline dictionary check remains at assembler lines 88–89. The exact commit-object fetch/readback and tree comparison remain at lines 159–164. The output at line 209 is the fixed baseline constant, so a manifest cannot introduce a multiline output assignment or select a different baseline. The negative controls for wrong identity, wrong tree, extra fields, and output-injection values all passed again.

### H2 — PASS / closed

The new `changed_paths` helper at assembler lines 39–41 explicitly disables rename detection. Every authorization-oriented delta now uses this helper: source-stage comparison at line 165, post-build changes at line 176, the initially empty index check at line 179, and exact staged-set comparison at line 185. A rename is therefore accounted for as both its old and new path; a protected deletion cannot disappear behind an allowed destination.

The ninth test, at test-file lines 78–102, is a meaningful actual-Git counterexample and regression control. It enables rename detection in a disposable repository, creates a protected file, moves identical bytes to an allowed test path, and confirms the old `--name-only` operation reports only the allowed destination. It then confirms `changed_paths` returns both paths and that the resulting set fails the allowlist predicate. That test passed in this review.

The three previously pending paths are now admitted explicitly at assembler lines 66–68:

- `tests/real-sky/native-weather-withdrawal.test.mjs`
- `tests/weather-withdrawal-authority.test.cjs`
- `tests/weather-withdrawal-mutations.test.cjs`

Their actual changed bytes still require frozen input hashes through lines 98–99, and actual non-generated deltas must exactly equal the reviewed inventory at lines 165–167. The required authored/builder input set, safe-path checks, fixed baseline, and pre/post-build input verification remain intact. No additional source ownership expansion was introduced by these exact test-path additions.

### H3 — PASS / closed, retained and extended to the fourth output

The manifest requires the exact generated-path set at lines 90–91. The assembler verifies generated working-file hashes, the staged Git tree, the actual committed HEAD, and the final candidate commit at lines 175, 187, 197, and 203. The direct Git-blob mismatch test passed again. All of these checks consume the manifest's complete generated map, so they also protect the newly declared metadata file.

## Fourth generated output: bounded and supported by actual build evidence

`GENERATED` at assembler line 25 now consists exactly of `index.html`, `offline.html`, `real-sky/native-sky.js`, and `moon/BUILD.json`. The omission/addition control at test-file lines 68–76 explicitly rejects a manifest that omits `moon/BUILD.json`, and continues to reject an undeclared extra output.

The requested canonical-build diff shows exactly one JSON leaf changed in `moon/BUILD.json`: `source["src/native/index.html"]`, from `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` to `67acbca548a6285e78119c45872fea412db67cfa1f8b640b56d681071a18f195`. A parsed JSON comparison independently found no other structural/value change. The original metadata blob has SHA-256 `04d3551f68df714310db8b93daaf626ebda9bdc53e79347e4c31be3bbb049d62`; the inspected built file has the hash recorded above.

This supports declaring the builder-produced source-hash record as a fourth generated output. It does not authorize edits to Moon source, assets, or other generated outputs. The final manifest must contain the frozen expected digest for all four outputs, and hosted generation must match it before any candidate output is emitted. This review did not rerun the canonical builder or independently hash the uninspected source implementation.

## Unchanged route boundaries and future prerequisites

The workflow hash is unchanged from v2. The owned-repository/ref restrictions, ordinary non-forced push, stale-source rejection, source-parent check, exact remote candidate readback, isolated Ubuntu native jobs, disabled native checkout credentials, five native matrix cases, expected-manifest arguments, and failure artifact preservation remain intact. There is no automatic merge, issue reconciliation, deployment, or other-branch action in the inspected code. No credential value is explicitly logged. Assembly success remains labeled `ASSEMBLED_PENDING_QUALIFICATION`.

The known fail-closed full-rerun behavior is unchanged: replaying an original source-stage run after its generated child advanced the remote ref rejects that mismatch. The earlier bounded retry guidance remains applicable; no stale-ref relaxation is needed for this closure.

No code-level blocker remains from H1/H2/H3 in the reviewed revision. Before relying on the route's result, the controller must still freeze and verify the actual generated/native manifests, retain the exact source-stage parent/tree/delta readback and all four expected output hashes, and verify the resulting hosted candidate/readback. Native screenshots, motion, withdrawal and hidden-expiry results, subsequent R0017/R0007 integration order, and exact owner approval remain separate evidence and authority requirements. None is claimed by this review.
