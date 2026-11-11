# R0007 publication bootstrap — independent cold code review

## Scoped disposition

**GAP-REVISE — the seed-coherence check should use literal, rename-disabled path enumeration before this artifact is described as proving “exact base plus four files.”** This is a small, bounded correction to the reviewed template. The review did not discover an explicit commit, ref update, deployment, protection change, or credential-export operation in the materializer. The overall two-stage design can preserve a coherent baseline seed and later publish a coherent target tree, provided the external seed/finalization steps satisfy the conditions below.

This disposition concerns the publication transport code at the hashes recorded here. It does not qualify the R0007 implementation, grant publication or merge authority, certify actual GitHub capabilities, close an audit, or accept any native/browser evidence. The final corrected target commit and real payload were deliberately not constructed or qualified during this review.

## Scope and method

I read the three assigned implementation files directly, plus the actual builder and its local Python helper closure, repository attributes, the baseline R0017 workflow, the current R0007 native workflow, and repository `AGENTS.md`. I did not read the author's README, reports, parent notes, or another reviewer's findings. File-name listings were used only to understand the changed-path and executable-input surface.

All repository operations were read-only and used `git --no-optional-locks`. I did not run a builder, upload, network request, workflow, browser, real payload preparation, commit, index mutation, or ref mutation. The only persistent file written by this review is this report. Small Python checks compiled the two reviewed programs in memory and exercised the upload helper with a fully mocked opener and in-memory receipts.

## Findings

### R1 — Seed delta is not enumerated literally (required bounded revision)

`templates/materialize.py:161–165` requires a single parent equal to the accepted base and compares the set returned by `git diff --name-only base HEAD` with the four reserved seed paths. That command does not disable rename detection, and `.splitlines()` is not an unambiguous Git pathname decoder. A detected rename can name its destination without separately naming the removed source. Consequently, equality of that set does not establish the stated invariant that all baseline paths remain unchanged and only four new paths were added.

The preparer already uses the stronger pattern for target changes at `prepare_payload.py:66`: `--no-renames -z`. Apply the same principle to the materializer's seed comparison, for example `git diff --no-renames --name-only -z base HEAD`, with NUL parsing. An independently computed and verified exact seed tree is also sufficient. The changed-name proof should not depend on the runner's rename configuration.

There is no observed malformed seed in this review. The proposed connector operation of starting from the exact base tree and adding only the four prepared blobs is coherent. This finding concerns the runtime assertion's advertised strength, especially if connector construction or subsequent seed handling is incorrect. A later reconstruction failure cannot retroactively establish coherence of a seed ref that has already been published.

### R2 — Arbitrary pathname support is narrower than `safe_path` suggests (low severity)

`safe_path` rejects absolute paths, traversal, empty components, backslashes, and `.git` components. The main check also rejects duplicate paths and reserved seed paths. These are useful protections. Calls use argument arrays, and no shell interpolates a manifest path or manifest command.

However, the helper accepts control characters and Git pathspec syntax such as `:(glob)**`. `git add ... -- paths` and `git ls-files ... -- path` still interpret pathspec magic after `--`; the separator prevents option parsing, not pathspec interpretation. In-memory checks confirmed acceptance of a NUL-containing string, a newline-containing string, and `:(glob)**`. NUL cannot be a valid tracked Git pathname and would fail later, rather than cause an upload. Several `.splitlines()` reads also do not support arbitrary newline-bearing paths.

The observed R0007 changed names are ordinary paths, so this is not an identified defect in that particular candidate. The final full-tree comparison also prevents accidentally staged extra content from being accepted as the target. Still, either constrain this purpose-built transport to ordinary path names explicitly, or use literal pathspecs and NUL-safe parsing throughout the relevant Git operations. Do not describe `safe_path` alone as a general arbitrary-path security boundary.

### R3 — Executable trust is required; the ordinary job token is not a blob-only capability

The workflow requests normal `contents: write`. The materializer's own HTTP implementation is much narrower: its only request constructor uses a fixed repository and fixed `POST /git/blobs` endpoint. It refuses redirects, does not select a URL or command from the manifest, performs no retry after an uncertain transport result, and never invokes a ref or commit endpoint.

The patched `tools/build_native.py` executes before final target-tree verification. Removing `R0007_UPLOAD_TOKEN` from child environments reduces accidental exposure; it is not a sandbox against hostile same-user executable code. The parent materializer still possesses the token, and a broad job permission cannot be narrowed merely by a comment or a child-environment deletion. The statement that the job creates only the intended blobs therefore depends on the reviewed executable inputs and normal runner trust, not on a GitHub capability restricted to blob creation.

For the actual code inspected here, this qualification is supported rather than merely assumed: `build_native.py`, `build_moon.py`, `native_core_horizon.py`, `native_star_bootstrap.py`, and `compact_receivers.py` are byte-identical to accepted base `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`. The inspected closure contains local reads, deterministic transformations, and generated-file writes; I found no network, shell-command, commit, or ref operation in it. The base tree has no symlink or gitlink entries. The inspected attributes contain no external filter or diff commands.

Once a final reviewed manifest is sealed, the existing workflow-manifest digest, materializer digest, patch digest, exact base tree, clean seed check, and indexed patch application already form a transitive source-input identity chain before builder execution. I do not require an unrelated sandbox redesign for this specific unchanged builder. Before relying on this review for a newly prepared candidate, verify that its executable helper closure remains unchanged and that it does not add Python modules/packages that shadow those imports. Any such change requires a fresh executable-input review; post-build target-tree equality would be too late to establish an effect ceiling for unreviewed code.

### R4 — Actual publication currentness and connector capability are outside these files

The preparer requires an explicit full target SHA equal to a clean source HEAD on the commissioned branch, and requires the supplied base to be an ancestor. It excludes the temporary seed files from both base and target. These checks properly prevent binding a visibly unfinished working tree.

The preparer's `--base` option can override the default accepted base. The materializer validates the supplied base's tree identity, but does not independently enforce that it is the commissioned accepted base. Similarly, `targetCommit` is a provenance label in the runner: the runner reconstructs and proves `targetTree`, not the original local commit object. These are acceptable design choices only if the final manifest is independently checked against the intended base and corrected target before any seed write.

Neither script implements the proposed connector finalization or its expected-seed compare-and-swap. This review cannot establish that the available connector exposes that operation, that its token can write the seed/final workflow files, or that the job token can transport the large blob. A non-forced ref update must not be silently represented as an expected-head compare-and-swap unless the chosen API actually enforces the expected head.

The materializer does not query the current branch head before uploading. Historical reruns can therefore store the same unreferenced blobs after the branch has moved. That does not publish the target and is bounded by this script's fixed endpoint. The external finalizer must nevertheless reject stale seeds and stale run evidence before any ref mutation.

## Positive code-level findings

- **Coherence of reconstruction:** the candidate index starts from the exact base. The source patch is checked and applied to that separate index, the actual native builder runs, only declared changed paths are staged, and unrelated tracked/untracked changes cause failure. The resulting full Git tree must equal the immutable target tree before any upload. Each retained changed file is then checked for mode, Git blob identity, byte length, and SHA-256. The separate index excludes the four temporary seed paths from the candidate.
- **Bounded upload implementation:** deleted paths are not uploaded; paths under `.github/workflows/` are deferred to the connector. The largest candidate blob is attempted first. Each upload stores a producer receipt before contacting GitHub and records completion or uncertainty. A returned SHA must equal the expected content-addressed blob ID. A failure stops subsequent uploads.
- **No hidden ref publication in the materializer:** its Git commands manipulate the disposable working tree, separate index, and local object database. None creates a commit, updates a ref, pushes, merges, deploys, or changes repository permissions. The only explicit remote repository mutation in this Python program is blob creation.
- **Credential/log treatment:** checkout is pinned by action commit, checks out `github.sha`, and disables persisted credentials. The upload token is attached only to the materializer step, removed from subprocess environments, and used only in an Authorization header in the reviewed code. HTTP failures retain status rather than response bodies or request headers. The inspected builder prints deterministic summary data. Raw producer logs and ordinary Actions artifacts are additional intended workflow outputs; “only blobs” describes repository Git Database effects, not the absence of all Actions artifact/log storage.
- **Workflow separation:** the baseline R0017 workflow triggers on pull requests to main and is guarded to PR 62; it is not a seed-push deployer. The currently inspected R0007 native workflow is a separate branch-push qualification workflow with `contents: read`; it is not in the baseline seed. No reviewed workflow defines deployment or protection changes.

## Small checks actually performed

Both Python files parsed successfully. The mocked upload tests produced these outcomes without any filesystem receipts or network activity:

| Case | Observed outcome |
| --- | --- |
| HTTP response with expected blob SHA | Returned `VERIFIED_BLOB_STORED_NO_REF_UPDATE` |
| Response with a different blob SHA | Raised and retained `UPLOAD_UNVERIFIED_STOPPED` |
| Simulated HTTP 403 | Raised and retained `HTTP_ERROR_STOPPED` |
| Simulated uncertain transport failure | Raised and retained `UPLOAD_UNVERIFIED_STOPPED` |
| Redirect handling | Refused the redirect |
| Child environment with a fake token | Token omitted from child environment |

For every mocked upload, the start/final receipts retained `refUpdated: false`, and the fake token did not occur in their JSON. These tests validate local branch behavior only; they are not remote API evidence or a real reconstruction test.

Using the supplied 81,702,660-byte candidate size, this implementation would construct 108,936,880 base64 characters and a 108,936,917-byte JSON request body. The route bypasses the stated connector request-size bottleneck because the runner sends it directly. No test here establishes that GitHub accepts that request, that repository settings permit the workflow, or that the runner finishes within its timeout. An unavailable capability must remain a stopped result, not a reason to expand permissions or export credentials.

## Conditions before effects and before finalization

Before seed publication: resolve R1; seal the corrected clean target commit; prepare the manifest from that exact commit and intended accepted base; verify all four output bytes/modes and their digest relationships; inspect the final changed-path/executable-input set; and perform the planned disposable reconstruction of the real payload. Verify the connector's actual workflow-file permissions without changing protections or granting new permissions. Seed construction must use the exact accepted base plus the four prepared additions and must not overwrite an unexpected existing owner-branch head.

Before final ref publication: require a successful terminal producer from the intended seed/run/attempt, manifest digest, target tree, and complete expected non-workflow blob set. Include final workflow blobs through the connector's existing permissions. Verify the assembled complete tree equals the sealed target tree and excludes all bootstrap files. Create the final commit with the expected seed as parent and use an operation that enforces the expected seed at the one owner-branch ref update. Preserve the independent R0017 and R000B branches and the stated integration order. The finalizer's concrete API transaction remains outside this review.

## Hash-bound reviewed files

The three assigned transport files were rehashed after inspection and were unchanged from the initial read:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `prepare_payload.py` | 5,886 | `da75ad3c7d00663433e8d8f1ceb2c945d6eb2b078311f1f8db506d6e2c6967ae` |
| `templates/materialize.py` | 13,347 | `397dc0aff21bcb58a94f5566c4d7a89a0b039862622590e4efc40da1201cfeda` |
| `templates/r0007-materialize.yml` | 2,270 | `8bfc4bc26b191051c84ff11fdd13153df1266909c9dc8a44dd69ecda31b1ec8d` |

Supporting executable/configuration files actually inspected:

| Repository file | SHA-256 | Comparison |
| --- | --- | --- |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` | Exact accepted base |
| `tools/build_moon.py` | `d83f27dbadecd2ac5e8b5eb478baeea0fcae4efbd2d366efdd071139ac6f2765` | Exact accepted base |
| `tools/native_core_horizon.py` | `535b2068aa6e7aed0f854782364729e25f1ebc3d8c42ea4dea23863d1821d8de` | Exact accepted base |
| `tools/native_star_bootstrap.py` | `55929e326235a7457cc384501042ef28b2600d1915c1a7e96b843a069c0d278e` | Exact accepted base |
| `tools/compact_receivers.py` | `0d4d571f228e1fd3ccc23484e56eda21954e911cd599490bd7434a5e4ebf9255` | Exact accepted base |
| `.gitattributes` | `503d0cf3d58768cccc9bfcd80bbd509f3a0527e72b2ca494d5f354f0fc8b99b0` | Exact accepted base |
| `.github/workflows/r0017-pages-payload.yml` | `2da004b4c0c93ab335ae3d4c74a9b4be96dab932ab9797ca7a3e7f93b4a0cbf3` | Exact accepted base |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` | Current inspected working file; final binding pending |

Any change to the assigned transport files invalidates the corresponding hash-bound review until its delta is assessed. This report is a bounded independent finding record for root reconciliation, not an acceptance or closure record.
