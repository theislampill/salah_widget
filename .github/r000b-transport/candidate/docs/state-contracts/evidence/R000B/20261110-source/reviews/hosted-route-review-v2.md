# R000B hosted preparation route — correction review v2

State: FINAL

Verdict: GAP. H1 and H3 are closed in the reviewed revision. H2 is substantially corrected, but rename-aware `--name-only` accounting leaves a protected-deletion gap. The actual source-stage manifest also remains pending, and three explicitly identified R000B test paths require exact allowlist additions before that manifest can pass. These are bounded preparation findings; this report grants no permission, product PASS, readiness, acceptance, integration, merge, deployment, or lifecycle authority.

## Identity, evidence, and scope

- Model self-report: ChatGPT, GPT-6 Astra Pro; not independently attested.
- contextreuse=bounded-v1-followup: this review uses this same reviewer's own prior findings and the parent's correction description. It does not claim a fresh independent context. otherreviewvisibility=no.
- Controller context supplied by the parent: R000B, phase 1. Baseline remains `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`.
- Inspected only the two pinned route files and the expressly authorized small assembly test file. The root `AGENTS.md` and normal builder hashes remain identical to those read during v1. Mutable product implementation, native driver internals, and other review reports were not inspected. No final manifest exists yet and none was assessed.
- Ran the authorized test file with `python -B tests/weather-no-timetable-assembly.test.py -v`: eight tests passed in 0.017 seconds. Its only fixture writes were in its disposable temporary Git directory; no repository source or script was modified and bytecode writes were disabled.
- Read-only Git object checks independently returned `commit` for the baseline and tree `6b94a3933f9d1381b1c2ceaab287c93afb215ecb`, matching the new constants. No fetch, build, browser, workflow run, installation, branch operation, or external mutation was performed.
- Wrote only this report as the retained review artifact. The v1 report is preserved.

Current reviewed files:

| File | SHA-256 |
| --- | --- |
| `.github/workflows/r000b-weather-withdrawal.yml` | `b75f014a4c5e4c0084e4bf112026232dd9a74c47d346fa65f2ee91d9933c1a4c` |
| `tools/qa/r000b_assemble_candidate.py` | `f5543431d37364287d5a94db3f892b6b00aad56ca24f5ed11693c2db88547835` |
| `tests/weather-no-timetable-assembly.test.py` | `08a5c7a4a65f51788616b7fb40d8c9cd1e2f3524b2c177de3fd9904740e7dd16` |
| `AGENTS.md` | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` |

## Per-finding disposition

### H1 — PASS / closed: exact baseline identity and safe job outputs

Assembler lines 80–81 now require exact equality with a dictionary containing the fixed baseline commit and tree. JSON values with wrong types, additional fields, incorrect SHAs, or embedded newlines cannot equal that dictionary. Lines 151–156 verify that the pinned commit object exists, fetch only that exact commit if needed, and check the actual tree against the fixed constant. Line 201 emits `BASELINE_COMMIT`, rather than untrusted manifest content, to `GITHUB_OUTPUT`.

The independent local object/tree readback matches the pins. The authorized tests reject the newline-output payload, another valid-looking commit, null/numeric commits, wrong tree, and extra baseline fields. This closes both the direct job-output injection and the unverified-baseline identity defect. Future predecessor reconciliation still requires an explicit review of changed pins; no moving `main` selection was introduced.

### H2 — GAP / partly closed: strong inventory checks, with one rename-accounting hole

The correction now requires the owner and builder input set (lines 26–31 and 84–85), rejects unsafe/unapproved change paths (lines 56–95), and requires an input hash for each approved source/test/doc path except the manifest itself. The manifest is bound as a whole by the recorded SHA-256. The source-stage delta must equal the reviewed approved inventory after excluding the fixed generated set (lines 157–159). These checks substantially close the sparse-input and pre-existing protected-path mutation problem.

Excluding exactly the three generated files from source-delta equality is reasonable here: the normal builder must still regenerate them, their declared SHA-256 values are checked, and the actual staged/committed blobs are now verified. This allows a later coherent evidence-only source stage to retain the known generated children without silently widening the protected source set.

**Remaining risk.** Line 157 obtains the source delta using `git diff --name-only` without disabling rename detection. A rename can be represented by its destination name, so a protected path moved to an allowed R000B evidence or test path can omit the protected original name from this inventory. A protected file not otherwise needed by the normal builder or V1 verification is the meaningful case: the destination can be approved and hashed while the original deletion is not assessed by `allowed_change`. The exact reviewed baseline tree does not remove that accounting problem. The eight tests test manifest admission and blob hashing, but do not test this Git-diff rename case. No additional reproduction fixture was created during this review.

**Countermeasure.** Use `--no-renames` for the authorization-oriented source delta so additions and deletions both appear as paths. Apply the same explicit policy to the builder/staged changed-path checks, or parse a NUL-delimited name-status result that includes both rename endpoints. The simple `--no-renames` option is sufficient for the identified hidden-deletion risk; no larger framework is required. A bounded test should exercise a protected-file rename to an otherwise allowed destination and require rejection.

After this change, retain the final manifest/source-stage readback showing the actual approved delta and hashes. This report does not assess that pending artifact.

### H3 — PASS / closed: exact generated blobs checked before publication and outputs

The new streaming `verify_git_files` at lines 105–111 hashes Git object contents directly. It is applied to the staged tree before committing (line 179), to `HEAD` before push (line 189), and to the candidate commit before job outputs for both changed and unchanged builds (line 195). Together with the existing parent check, owned-ref checks, ordinary non-forced push, remote-ref equality, and clean checkout check, this binds the declared generated hashes to the actual candidate blobs.

The authorized blob test establishes different worktree and stored-tree bytes, confirms worktree verification alone passes, confirms the mismatched Git blob is rejected, and confirms the correct stored-blob digest is accepted. This addresses the actual pre-stage byte-binding gap from v1.

## Workflow corrections

The native workflow now contains five matrix entries: baseline default, candidate default, candidate reduced, candidate full, and candidate default with controlled-hidden expiry. The hidden entry adds `--hidden-expiry` through a Bash argument array and has a distinct artifact name including visibility (lines 65–68, 92–101, and 106). The matrix values are fixed and arguments remain quoted; no shell-evaluation or output-injection path was introduced.

The workflow passes `--expected-manifest` for the selected baseline/candidate product (line 99). Candidate checkout remains bound to the successful assembly output; the baseline checkout remains bound to the fixed baseline output. Native checkouts disable persisted credentials, jobs request separate Ubuntu runners, and evidence remains runner-local and uploaded on failure.

These are PASS at the workflow-contract level. They establish which arguments and checkouts are selected. They do not attest the uninspected driver implementation, the as-yet-unwritten native pin files, actual hidden-expiry behavior, pixels, motion, or qualification results. The final driver/native manifests must record and enforce the actual product identity before those results can be used as evidence.

## Known execution prerequisites and unchanged boundaries

The parent identified three actually authored R000B test paths that are not admitted by the current allowlist:

- `tests/weather-withdrawal-authority.test.cjs`
- `tests/weather-withdrawal-mutations.test.cjs`
- `tests/real-sky/native-weather-withdrawal.test.mjs`

The current validator correctly rejects a manifest listing them. Adding those exact paths, with their frozen hashes in the manifest and exact delta readback, is a required bounded follow-up before publication. It is an execution prerequisite, not a present authority bypass. The explicitly listed host-composition and preview-host test paths are already admitted, and their changed bytes must be included in the input inventory.

The route continues to preserve the original boundaries: publication is restricted to the owned branch, remote advancement fails closed, only one ordinary generated child is created when needed, no other branch push or automatic merge/issue/deployment action appears, and completion status remains `ASSEMBLED_PENDING_QUALIFICATION`. No credential value is explicitly logged in the inspected code. The full-rerun limitation described in v1 is unchanged: replaying the original source-stage run after its child was published rejects the now-advanced ref. No broadening of stale-ref checks is recommended.

The remaining blocking preparation work is the rename-accounting correction, the three exact path additions, and the final frozen manifest/source-stage evidence. Runtime qualification and owner/integration approval remain separate. No prompt-injection instruction was observed in the inspected scope.
