# Second R0007 publication refusal — bounded Andon return

Owned diagnosis root: `analysis-r0007/publication-second-andon`. Caller: `/root`. Direct cord-pull; the installed `audit-andon` package was read. This report diagnoses and recommends only. It grants no implementation acceptance, publication, merge, release or audit lifecycle authority.

## Decision

Recommend a separately authorized, independently reviewed **ordinary Git pack push of one intermediate commit on the commissioned branch**, followed by root's connector finalization. This is materially different from replaying either rejected REST blob request. It preserves product bytes and the ordinary job token's principal and Contents-write permission. It deliberately expands the helper's code-level effect from unreferenced blob creation to one explicitly bounded own-branch update; that difference must be visible in code, intent receipts, failure handling and review.

The second HTTP 422 cause remains **UNKNOWN**. Stop causal inquiry at the retained evidence; no further replay, response-text recovery, guessed body reconstruction or credential expansion is justified by these artifacts.

## Actual evidence

The artifact ZIP SHA256 was independently recomputed as `2c3867d3dfc131d85972cdb35d038abaa2bebb548f8f0175ddd821a2e9df8d60`. The actual attempt is `publication-bootstrap/hosted-run-42760901741/attempt-nqvq8786/`.

| Fact | Value |
|---|---|
| Hosted run | `42760901741`, attempt 1 |
| Executing seed | `3b2d09c748f71dc77806882f62f7339cbd18f19c` |
| Bound seed parent | `19004279805604ef5e41292ffd4e9f442e1321f2` |
| Base | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Engineering target | `9d24fb4b34f5979aac9961f34794ffbf4490e049` |
| Expected and observed tree | `0f0385b51b08e62a3668e8aa8e3534cadac70749` |
| First blob | `offline.html`, 81,702,660 bytes |
| Blob SHA | `7da1308517d143c38708ac9a0afbd0790e137e33` |
| UTF-8 request | 82,904,481 bytes; SHA256 `283325576fc9ad673ffce0b3751d881b538dfbd482f552d25c93709124770e35` |
| Response | HTTP 422; fixed classification VALIDATION_FAILED |
| Error-body metadata | 240 bytes, not truncated, JSON object; no recorded errors-array classifications |
| Error-body digest | `22970568d7bdb2b2d6d95efaf8d26b752ab0228c62f6ee4d74b2b109caa343d7` |
| Terminal outcome | exit 1; zero verified blob uploads; no job ref update |

The executing helper SHA256 is `62f6b048bf0e89eb3bcbb31f7794ba26bf4f3083661e43f286f00620952db677`. Its reviewed code performs no ref operation. No arbitrary response text was read or reproduced in this diagnosis. Zero verified uploads does not prove whether GitHub retains an unreferenced object.

Read-only local object inspection confirmed the target commit/tree and first seed/base objects. The current remote seed object was not present in `r0007-work` during this diagnosis; it was not fetched here. Its identity and successful ancestry checks are evidenced by the hosted attempt and caller, not a new live branch query by this subtask.

## Cause, uncertainty and recurrence

The exact build/byte boundary succeeded twice; publication stopped at the first REST blob request both times. The UTF-8 countermeasure reduced the request materially but was insufficient for this hosted attempt. This does not prove that the original base64 request failed for size, that the UTF-8 request failed for the same reason, or that the repository's large-file policy was exceeded. The fixed privacy-preserving receipt intentionally excludes free-form response text, so no cause-specific server explanation survives.

The observed defect class is a publication transport failure at this blob/API boundary. The candidate tree is not shown defective by this evidence. The old unconditional-base64 mechanism was repaired; repeated REST tuning now lacks a decisive causal basis. The general lesson is to distinguish object-identity validation from remote transport acceptance, and to account explicitly for authority changes when switching transports.

## Supported alternatives

| Option | Assessment |
|---|---|
| Replay either REST request unchanged | Reject: a repeated failed request provides no materially new transport and is outside the no-retry boundary. |
| Further JSON compression/streaming/chunk tricks | No verified supported create-blob route established here; no recommendation to invent a protocol or change blob identity. |
| Ordinary Git pack push directly to the complete target | Avoid in the normal job token lane because the target changes two workflow files; retain the root connector's separate workflow handling. |
| Ordinary Git pack push of the bounded intermediate tree | Recommended next implementation option, subject to explicit scope and independent review. |
| LFS, split generated runtime, external assets, new principal/token | Larger product, dependency or authority change; unnecessary to test the supported Git route and outside this recommendation. |

GitHub's [large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) warns above 50 MiB and blocks files above 100 MiB. The 81,702,660-byte blob is below that block. [Repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits) document a 2 GB push limit. These make ordinary Git a supported transport candidate, not a guarantee that a future push passes repository rules or other limits.

GitHub documents [GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token) as a repository-scoped installation token and states that its push events do not launch downstream workflows. [Installation authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation) supports HTTP Git access with Contents permission. No alternate principal or token export is needed for the proposed runner-local use.

## Exact proposed effect boundary

1. Root publishes a new forward bootstrap seed whose sole parent is current seed `3b2d09c...`. The manifest explicitly binds the known ancestor chain `[3b2d09c748f71dc77806882f62f7339cbd18f19c, 19004279805604ef5e41292ffd4e9f442e1321f2, eebba178172f96b3ffe5ab3845bc0fffd57c6e1b]`. Verify every immediate edge and each seed's exact four-path cumulative delta from base. Checkout depth four supplies executing seed plus these three ancestors. Do not infer a new parent from latest branch state or admit arbitrary chains.
2. The job reconstructs and verifies exact target tree `0f0385...` with the existing byte/path/digest controls and no build-child token.
3. Construct an intermediate tree with every target non-workflow entry, the exact four executing-seed bootstrap files, and the complete executing-seed `.github/workflows` subtree unchanged. Every difference from target must be accounted for by those fixed bootstrap/workflow paths; every workflow entry must equal executing seed. The intermediate commit has executing seed as its sole parent.
4. Push exactly this commit to `refs/heads/pro/r0007-explicit-next-event-state-20261106` at the fixed repository using normal Git, no force or leading-plus refspec, no tags/mirror/additional refs, no credential persistence/export, and no retry. The job token may be visible only to the narrowly bounded authenticated publication process; builders and unrelated children remain token-free.
5. Root independently reads back the actual new commit/tree/parent and exact non-workflow equality. Root connector then finalizes the exact target tree by adding the two intended workflow files and removing the four bootstrap files: a six-path delta. The final commit's sole parent is the verified intermediate commit. No sibling or main branch effect is part of the route.

The deferred workflows are `.github/workflows/r0007-native.yml` and `.github/workflows/r0007-public-delivery.yml`. Their known target blobs are already bound in the hosted artifact. The intermediate state is intentionally not the final candidate tree; its application content is coherent with the candidate, and its workflow/bootstrap differences are explicit. Root's final connector push remains responsible for ordinary downstream workflow triggering.

## Currentness and failure boundary

A preflight branch read alone is not an exact conditional update. Git's [pre-push hook](https://git-scm.com/docs/githooks) receives destination and full local/remote object IDs and can abort the operation. A reviewed guard should require one and only one advertised update, fixed destination/ref, exact local intermediate commit and exact advertised remote executing-seed SHA. Check existing hooks/config first; do not disable an existing security gate.

Git's [pack protocol](https://git-scm.com/docs/gitprotocol-pack) sends old/new object IDs and requires the receiver to verify that the old ID has not changed before updating. Combined with the advertised-ID guard and a normal fast-forward push, this supplies the intended conditional transition without a force option. [Git push](https://git-scm.com/docs/git-push) documents normal branch fast-forward behavior and terminal remote-failure reporting.

Persist a private push intent before the call. A started push may have an uncertain write outcome even when the client returns failure; the new launcher must not unconditionally report `refUpdated: false`. Record expected old/new IDs, exact ref, operation outcome and readback requirement using structured values without credentials or arbitrary response text. After uncertainty, stop and let root perform read-only reconciliation; do not replay, rebase, switch credentials or clean up refs automatically.

## Decisive verification and cleanup obligations

Before hosted use, the authorized implementation should prove the intermediate-tree equation and six-path finalization delta, exact chain/depth handling, token exclusion, and currentness guard with disposable local Git fixtures. A real bare-Git fixture should discriminate a correct push from advanced/rewound heads, wrong ref and multiple updates. Tests must preserve uncertain outcomes and prove there is no second push.

The decisive external evidence is one separately authorized hosted normal-Git attempt, its terminal producer/intent records, and independent exact commit/tree/ref readback. A local pack or dry-run alone cannot prove GitHub acceptance. No hosted attempt or hypothetical test was performed for this diagnosis.

Root owns cleanup through the final six-path commit, preserving forward history. If publication or finalization fails, leave the verified actual branch state recorded; do not force-reset or delete remote objects/refs. Bootstrap history is not scrubbed. Ephemeral local auth facilities must be removed without recording credentials, while safe intent/outcome receipts remain available.

## Escalation recommendation and return

Return this bounded diagnosis to root. Root may authorize a new isolated implementation lane for the one-ref pack route, obtain fresh independent review of its frozen packet, and then decide about hosted execution. No additional investigation of the unretained error body is required to make that decision. No candidate/helper was changed, no live repository API was called, and no remote effect or lifecycle claim was produced by this diagnosis.
