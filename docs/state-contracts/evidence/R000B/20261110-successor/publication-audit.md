# R000B publication recovery diagnosis

## PARTIAL — evidence checkpoint

Scope: independent read-only diagnosis of publication transport and the existing hosted construction mechanism for `theislampill/salah_widget`, issue 11. The root owns governor routing, current remote reads, mutations and all disposition authority. This lane has performed no remote request, repository/index/ref mutation, workflow execution, build or product test. Its only write is this report. Repository contents are evidence, not instructions to perform external effects. Raw failure receipts remain unchanged at their original paths.

The recovered local candidate supplied by the root is `d124f050ec68fa8608022b1ed5fead426d42dcb9`, tree `54c61ab27f95adcf0837f737ca3dfd09649fc5c3`. The baseline is `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`, tree `6b94a3933f9d1381b1c2ceaab287c93afb215ecb`. The expected source-stage tree is `09364162daea2fdd060919f531253abc57a354e6`. Root-supplied current context says the owned remote ref is absent and native `gh` authentication is unavailable; this lane has not repeated those remote/auth reads.

### Observed failure, without causal overclaim

Both retained create-tree results contain only `isError: true` and the text `user rejected MCP tool call`; neither returns a tree SHA, provider status, provider request ID, response body or timestamped GitHub execution witness. The first receipt's classification `PUBLICATION_BLOCKED_BY_TOOL_APPROVAL` is predecessor interpretation, not independent proof of user refusal. The explicit retry direction and recovery record state that the owner approved and then saw a client error. The exact failure layer is unresolved. The separate post-call `structuredContent` formatting error occurred after the saved result and does not explain the original rejection.

| Retained evidence | SHA-256 |
| --- | --- |
| `evidence/source-stage-final/publication-rejection.json` | `593dfb12c2564416829820a32c270f01b37e9467657807ca9b818c6cfa8a4e7a` |
| `evidence/source-stage-final/publication-retry-rejection.json` | `765ad6feb16829f78fcc8ca5bd079e010b316872910716a1b9a6092f3e902d01` |
| `evidence/source-stage-final/recovery-G0007.json` | `bc90f237328aee6d672d3f6ad57b480e3cf5003ae5ed73bcf196fdff02f9a7f3` |
| `evidence/source-stage-final/receipt.json` | `10f5127e77455882cb6985b3446d1023b7662d3edeee0d0f850f489d156af62a` |
| `evidence/source-stage-split/plan.json` | `a1420dea0b41ca51adaa8a3d4bacb20db49ff5aae1327a2199605b7bdcc1ab05` |

All evidence paths in this table are relative to `/workspace/scratch/15b8fb6ac4c2/`.

### Measured transport and mechanism facts

The original prepared request was 4,595,887 serialized bytes and covered 358 source/evidence paths. The frozen split plan has 33 requests, a self-imposed normal cap of 131,072 bytes and three single-blob exceptions of 149,009, 387,424 and 388,271 serialized bytes. Its first request is 4,892 bytes and modifies the workflow. This cap is a local packing policy, not a proved connector/provider limit. The prior independent review established exact tree equivalence, but seven SHA entries depend on inline objects first introduced in the same request. The user now forbids oversized create-tree and content-bearing batches, so this frozen mixed-content plan is retained evidence, not an executable recovery route.

The exposed connector schema supports one complete blob per `github_create_blob`, SHA-only tree elements through `github_create_tree`, a commit object through `github_create_commit`, and an expected-head checked ordinary ref update. No create-blob chunk-upload/append operation is exposed. Current tool documentation does not declare a numeric content-envelope limit. A small SHA-only tree is useful only after all named blob objects are already available remotely.

The existing workflow is push-only on the exact owned branch. Its assemble job requests `contents: write`; it checks out the triggering SHA, runs the canonical builder and V1 verifier, verifies sealed inputs and four generated hashes, creates an ordinary generated child when needed, and pushes the owned branch. The native jobs depend on that assembled candidate output. There is no workflow-dispatch path in this file, and the assembler itself rejects any event other than `push`.

The source stage deliberately retains baseline generated files. It is an incomplete runtime candidate until the four generated outputs and exact full tree are read back. A workflow declaration requesting write permission is not evidence that installation/token permissions and branch rules will allow the push. The retained hosted v4 PASS is explicitly a mechanism/packet review, not a live execution result.

### Immediate next read prerequisites

1. Use the root's in-flight immutable-object probes to reconcile whether any exact tree/blob already exists after the ambiguous calls. Owned-ref absence alone does not resolve orphan immutable objects.
2. Obtain repository/branch/ruleset and Actions-enablement evidence through supported read endpoints, retaining unsupported/denied reads as gaps rather than weakening protections.
3. Confirm actual native Git write authentication before selecting native Git; public reads and `gh`-unavailable state do not establish authenticated push capability.
4. Independently compare the 358 source blob manifest, four generated blobs, declared input closure and baseline/full/source trees against current recovered objects. Do not substitute a remembered review disposition for fresh identity binding.

This checkpoint does not propose a mutation yet. Remaining work in this bounded lane is local object/manifest verification, precise hosted-permission/protection analysis, documented API-size semantics, and conditional next-action/recovery prerequisites.

## FINAL — bounded audit-Andon return to `/root`

### Entry, authority ceiling and effect account

After the partial checkpoint, `/root` explicitly pulled the audit-Andon cord around publication observations o26/o27 and supplied the actual caller, engineering/own-branch publication ceiling, facts and prohibitions. I read the actual `audit-andon` v0.4.0 package at `e1/skill-6a85962852508191a70c4b0eedbd1928`. This is its allowed **direct-entry bounded cord-pull**, returned to the actual caller. It is not an assertion that the governor package resolver succeeded, a new IMPLEMENTAUDIT run, a canonical L4 registration or a continuity receipt. No child was routed.

This final section adds: independent local object/hash/tree verification; official Git/GitHub documentation reads; a streamed bundle size/hash measurement; the explicitly requested R0007 analogue's read-only job/log lookup and inspection of its already-downloaded ZIP. I did not download another archive, execute repository scripts, import the bundle, build, run product tests, change a transport plan, mutate source/index/refs, publish objects, trigger a workflow or communicate externally. The sole filesystem write remains this report. The earlier partial section is preserved as a historical checkpoint; its statement that no remote request had then occurred is superseded only by these subsequent official-documentation and R0007 read-only evidence reads.

### 1. Classification and causal account

**Classification:** publication-transport abnormality with unresolved original client/tool causation, a demonstrated absence of native push authentication in the caller's environment, and a confirmed incompatibility between the old source-stage-ref mechanism and the user's current coherent-branch constraint. This is not evidence of a product-byte transport corruption or a real owner refusal.

| Proposition | Evidence class and bounded conclusion |
| --- | --- |
| Original and retry create-tree calls returned a generic rejection | Directly observed in preserved raw receipts. No GitHub HTTP status, provider request ID or returned object identity exists in either receipt. The failing boundary cannot be narrowed beyond the client/tool/approval/provider chain. |
| The owner refused publication | Unsupported and contradicted by the supplied owner account of approval followed by a client error. Preserve the raw wording; do not turn it into an authority revocation. |
| The 4,595,887-byte request exceeded a client limit | Plausible volume-related hypothesis, not established cause. No measured connector limit or HTTP 413 exists in the receipts. |
| Native Git can publish because GitHub reads work | Falsified for the currently tested native route by the caller's actual noninteractive push dry-run exit 128, inability to obtain a password, unauthenticated `gh`, and absent credential helper. Connector authentication and local Git authentication are different capabilities. |
| Publication partially succeeded | Root reports fresh GitHub 404s for source tree `09364162…`, full tree `54c61ab2…`, and commit `d124f050…`; no owned ref and no R000B run. Those scoped readbacks do not prove every referenced blob is absent. Individual immutable blobs may remain after a failed tree request. |
| Current branch protections are absent | Root's repository-rulesets result `[]` narrows one control family. It does not independently prove absence of classic branch protection, inherited rules not included by the call, Actions restrictions, or an installation's missing write scope. |
| Existing source-stage ref is coherent | False under the user's current requirement. Independent reconstruction confirms that all 358 authored/evidence changes coexist there with baseline versions of exactly four changed generated files. Publishing that as a runnable branch exposes a mixed source/generated candidate until a later child is published. A warning label does not remove the mismatch. |
| The frozen candidate is the next acceptable publication candidate | Not established. Root now reports a separate concrete synthetic-present lease gap requiring a narrow source repair. This report binds the old candidate for recovery only. The repaired candidate requires new exact source/full/bundle identities and affected review; old values must not be relabelled as its evidence. |

Further causal questioning of the original generic rejection would not change the immediate route decision without new provider/client telemetry. The useful discriminator is an attributable response to one small, complete immutable-object operation plus exact object readback, or provider-side request/error metadata for the earlier operation. A small success would establish that operation's capability, not retroactively prove that size caused the prior failure. A small failure with the same generic text would leave the failure layer unresolved and argue for connector/client escalation rather than more payload repacking.

### 2. Fresh local candidate and manifest verification

An inline read-only verifier used committed Git objects rather than executing the preparation scripts. It compared every receipt entry's path/mode/blob, byte length and SHA-256; recomputed Git blob IDs; checked all 366 manifest inputs and four generated outputs; compared the complete baseline/candidate path-and-mode delta against all 362 approved paths; and independently encoded Git trees in memory. Results:

| Binding | Independent result |
| --- | --- |
| Recovered HEAD | `d124f050ec68fa8608022b1ed5fead426d42dcb9` |
| Reconstructed baseline tree | `6b94a3933f9d1381b1c2ceaab287c93afb215ecb` |
| Reconstructed source-stage tree | `09364162daea2fdd060919f531253abc57a354e6` |
| Reconstructed full candidate tree | `54c61ab27f95adcf0837f737ca3dfd09649fc5c3` |
| Source paths / distinct blobs | 358 / 328 |
| Distinct source blobs already present in baseline | 2; therefore 326 are new relative to baseline, before any remote-object reconciliation |
| Distinct source-blob bytes | 3,856,244 |
| Approved changed paths / manifest input hashes | 362 / 366 |
| Source-to-full differences | Only `index.html`, `offline.html`, `real-sky/native-sky.js`, `moon/BUILD.json` |
| Binding errors | None in the inspected frozen object population |

The committed workflow, assembler, assembly tests and integration document match their hosted-v4 mechanism hashes. All 33 frozen split-request lengths and hashes match their plan; their total serialized bytes are 4,029,482, with 326 content entries and 32 SHA entries. This does not remove the seven same-request availability dependencies already recorded by the transport reviewer, establish a provider limit, or authorize the now-prohibited mixed-content requests.

| Generated path | Complete blob bytes | Git blob ID |
| --- | ---: | --- |
| `index.html` | 1,593,444 | `005234fc929a9b27d9f4ed34ae810962aa25195e` |
| `offline.html` | 81,706,965 | `1eb07e867861d1369a508e4142e06c2af937c006` |
| `real-sky/native-sky.js` | 396,323 | `771d07a5cc08c70330a6a722343703a42c41715a` |
| `moon/BUILD.json` | 4,146 | `a2d323162e279c6aea2bc43cddc79837d1542d10` |

Their SHA-256 values match the original receipt and hosted-v4 report. The manifest's internal hashes prove equality to its frozen inputs, not independent acceptance of its authority. The external reviewed manifest digest, exact delta, unchanged baseline, executable dependencies, final tree, and later remote readback remain necessary parts of the provenance chain. This lane did not repeat the prior 142-file runtime/M2 semantic review or qualify a new source repair.

### 3. Known size limits versus unknown transport limits

| Quantity | Meaning |
| --- | --- |
| Original source request: 4,595,887 bytes | Actual local serialized body; failed with generic tool result. |
| Split policy: 131,072 bytes | Author-selected normal packing cap, not a proved service limit. Three larger single-entry bodies were 149,009 / 387,424 / 388,271 bytes. |
| All-358-path SHA-only source request: 70,261 bytes | Independently measured compact JSON, useful only if every named blob already exists remotely. Smaller bottom-up SHA-only trees can further reduce each call. No such new request was written or sent. |
| Largest source blob: 379,714 bytes | `src/native/index.html`; separate complete blob transmission still has an unqualified client-envelope limit. |
| Complete `offline.html` UTF-8 create-blob JSON: 82,908,925 bytes | Independently measured connector-shaped compact JSON. A source-only success cannot qualify this materially larger transmission. |
| GitHub recursive tree read: 100,000 entries / 7 MB | Documented **GET response** limit, not a create-tree request allowance. Use nonrecursive subtree reads if truncated. |
| GitHub blob read: up to 100 MB | Documented under **Get a blob**. It does not prove that this connector accepts an 82.9 MB create-blob envelope. |

The exposed create-blob schema accepts an entire UTF-8/base64 blob, with no append/chunk-upload protocol. Its documentation and the create-tree documentation do not provide a numeric connector/client body ceiling. [GitHub Git blobs](https://docs.github.com/en/rest/git/blobs) and [GitHub Git trees](https://docs.github.com/en/rest/git/trees) support those method/limit distinctions. Runtime file fragments must never be substituted for the complete generated blob or referenced using the original complete blob's ID.

### 4. R0007 analogue: actual failure and limits of analogy

At the caller's request I inspected run `42760901741`, job `129646081917`, and the already-downloaded `analysis-r0007/publication-bootstrap/r0007-materialization-42760901741-1.zip` under `/workspace/scratch/8726e3e6def5/`. The archive is 411,195 bytes and SHA-256 `2c3867d3dfc131d85972cdb35d038abaa2bebb548f8f0175ddd821a2e9df8d60`, matching the actual Actions job log's artifact digest. The raw archive remains unchanged.

The job log records `Contents: write` and `Metadata: read`. The materializer reconstructed its exact target tree before the first upload. `attempt-nqvq8786/upload-001.json` records:

- `offline.html`, 81,702,660 bytes; expected/local Git blob `7da1308517d143c38708ac9a0afbd0790e137e33`.
- UTF-8 request size 82,904,481; HTTP **422**; `HTTP_ERROR_STOPPED`.
- The 240-byte error body was consumed but retained only as a fixed class plus digest (`22970568d7bdb2b2d6d95efaf8d26b752ab0228c62f6ee4d74b2b109caa343d7`), with no precise provider reason recoverable from this receipt.
- Summary: zero verified uploads, no ref update, and two workflow blobs explicitly reserved for the connector.

The upload receipt SHA-256 is `e74cb47076a531cbac9a1d246a51b99021ed803afc2642c882cf007cd7aa4081`; summary SHA-256 is `960acdda2d7d079d6c3034fa43a2f9f134e69f0d7775a5610d3024fdf732eef3`.

**It is not a workflow-permission rejection witness.** No workflow blob upload or candidate ref operation was reached. It is an attributable failure of the large REST-blob route in the same repository/environment class; its exact 422 cause remains unknown. It materially weakens a recommendation to repeat an 81 MB hosted REST-blob upload as the primary R000B countermeasure. It also shows that removing the interactive client envelope alone does not establish successful full-blob publication.

### 5. Hosted route permissions, source provenance and branch completeness

The existing R000B workflow only handles an owned-branch `push`. Its `--publish` assembler additionally requires the actual checkout to equal `GITHUB_SHA`, the exact repository/ref, and the owned remote head to equal the source before assembly and push. It cannot be reused unchanged as a publisher of an unrelated unattached source object or dispatched manually. Environment-value spoofing is not an acceptable adaptation.

Its build/validation path **without `--publish`** remains useful in an isolated runner after verified candidate import. That reuses the reviewed builder, V1 check, input closure and four-output seal while leaving new publication effects outside the old mechanism. It supplies neither a ref effect nor a qualification result by itself.

Required distinctions before a hosted action is selected:

1. **Connector publication rights:** actual repository contents-write capability and workflow-write capability for a final tree that adds `.github/workflows/r000b-weather-withdrawal.yml`. The latter is a real added path versus baseline. Do not substitute authenticated-user collaborator level for the installed connector's permissions.
2. **Actions execution rights:** repository Actions enablement, permitted action pins, event eligibility and runner availability. Job-level `contents: write` requests permissions; a prior mechanism review is not an execution witness. An actual run's token-permission log provides better evidence of its granted scope.
3. **Ref rules:** exact branch rules, classic protection where readable, and current-head/absence checks for every scoped staging/final ref. The connector documents that managed installations exclude administration access, so a denied protection/settings read is an access gap, not evidence of unrestricted operation. No rule changes or bypasses are recommended.
4. **Workflow-file boundary:** contents-write alone must not be assumed to permit introducing or deleting root `.github/workflows` files. GitHub distinguishes Workflows write permission, while that permission is not a configurable `GITHUB_TOKEN` scope. Any connector-owned final workflow change must remain with that authorized actor. The R0007 analogue does not establish a native full-tree push exception.
5. **Follow-on execution:** a push made with `GITHUB_TOKEN` does not normally start another push workflow. The existing R000B native matrix is safe from relying on that recursion because it consumes its assembler output within the same run. A new bootstrap must not assume its later push starts the qualification workflow; retain the actual run ID/event/head and use a supported authorized trigger path.

Official references: [workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions), [Actions settings reads](https://docs.github.com/en/rest/actions/permissions), [reference permissions](https://docs.github.com/en/rest/git/refs), [workflow-file modification scope](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents), and [GITHUB_TOKEN event behavior](https://docs.github.com/en/actions/concepts/security/github_token). These documents describe general semantics; no live setting or mutation success is inferred from them.

### 6. Minimal countermeasure recommendation

**Prefer a native Git publication only when its authentication actually exists. It does not currently exist in the caller's tested environment.** The old source-stage ref must not be published under the current coherent-branch requirement. Individual complete source blobs plus SHA-only trees are mechanically valid, but they leave the large generated blob problem unresolved. The measured bundle route is therefore the smallest promising alternative, conditional on a bounded staging capability and review of the narrow bootstrap effect.

Read-only streaming of `git -c pack.threads=1 bundle create - HEAD ^eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` under Git 2.52.0 produced:

| Bundle property | Observed value |
| --- | --- |
| Bytes | 681,064 |
| SHA-256 | `f80f086550fdb9e4e1f2069f517b91330b873095a60c172816ad73f3891f54c4` |
| Base64 text length, before JSON overhead | 908,088 |
| Header prerequisite | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Header tip | `d124f050ec68fa8608022b1ed5fead426d42dcb9 HEAD` |
| Included candidate history above baseline | Four commits, ending at the exact frozen full candidate |

The bundle existed only as a streamed byte sequence; this lane did not save or import it. Git documents revision-exclusion bundles as thin packs using existing prerequisite objects. It is a complete Git transport artifact relative to the verified baseline, not truncated generated output. A fresh baseline-only import and object verification are still required; a check in the already-complete source repository cannot establish transfer completeness. See [git-bundle](https://git-scm.com/docs/git-bundle).

The bounded route recommendation is:

1. After the narrow source repair and affected review, freeze a **new** complete candidate and reproducible bundle; bind baseline prerequisite, target commit/tree, all parts and whole bundle hashes, approved delta, manifest, four generated blobs and builder inputs. Check import in a disposable baseline-only repository before any branch exposure.
2. If a single complete bundle blob is beyond the observed client capability, transmit small complete transport-part blobs separately and attach them through small SHA-only trees. These may be data files under an approved staging namespace; they must never replace runtime source/generated paths. Reassembly must verify the complete bundle before import. The 681,064-byte measurement is not proof that a 908,088-byte encoded call is accepted.
3. Publish only a **coherent baseline staging tree** plus the bounded inert transport data and small reviewed construction workflow. Verify the baseline runtime remains byte-identical and the complete payload manifest is present before the staging ref effect. Root must explicitly select an already-authorized owned staging scope; this diagnosis grants no new branch authority.
4. In the runner, import the verified bundle, verify the exact candidate commit/full tree and all generated/input bindings, and reuse the reviewed assembler's verification path without `--publish` as appropriate. Do not let an unverified payload or moving branch supply executable bytes.
5. Resolve the final object-transfer capability without an 81 MB REST blob assumption or an unverified workflow-write assumption. One small Git-native option is an ordinary fast-forward **carrier commit on the coherent staging branch** that leaves its root runtime and root workflows unchanged and references the already-verified complete candidate tree under one inert data subtree. Native Git then transfers the complete referenced objects through its pack protocol. The carrier's sole parent must be the expected staging head; the imported candidate is referenced as a tree, not introduced as a parent containing new executable workflows. The actual candidate workflow is data at this stage; it is not installed as a root workflow by `GITHUB_TOKEN`. This is a recommendation to inspect, not an implemented or qualified mechanism. Confirm that no runtime/build/deploy consumer follows the chosen data namespace and that the push contains no root-workflow delta.
6. Once exact remote full-tree/object availability is read back, the authorized connector can create the final candidate commit pointing to that exact full tree and create/update only the selected final owned ref. The final tree contains no carrier path or bundle fragments. If the same owned branch carries staging and final publication, the new commit must descend from the actual carrier head so the transition is an ordinary fast-forward. A separately authorized absent final branch can instead use its reviewed parent. Bind any new remote commit's actual parent/tree and provenance to the frozen local candidate; do not claim its commit SHA equals the local SHA unless it actually does. Final workflow publication remains an authorized connector effect. No runnable candidate ref should ever point at a source-only or partially generated tree.

This avoids introducing a new builder, patch format, generated-file split scheme, broad ref choreography or automatic main mutation. It does add a narrow transport wrapper and a staging effect, so the root must review those exact bytes and capabilities before using it. If the authorized staging scope cannot meet these conditions, the remaining minimal escalation is access to a supported authenticated Git transport, not weakening coherence or permission checks.

### 7. Exact next evidence and mutation prerequisites

**Read/prepare first:** retain the caller's fresh object/ref/ruleset/auth receipts; reconcile any known immutable blobs by exact SHA; finish the narrow source repair; freeze the revised candidate and updated manifest; qualify bundle import from only the exact baseline; inspect the proposed staging namespace against all runtime/builder/workflow consumers; inspect current branch/ruleset/Actions capabilities; and review the wrapper's complete effect list. A correct object ID or successful old review does not replace those current checks.

Useful supported read locators, scoped to the selected repository/branch, are `GET /repos/theislampill/salah_widget`, `GET /repos/theislampill/salah_widget/rules/branches/{encoded-branch}`, `GET /repos/theislampill/salah_widget/git/ref/heads/{branch}`, and the repository workflow/runs collections. Repository Actions permission and classic protection reads require administration access and may be unavailable through the connector; preserve that exact result and use an attributable actual runner/push result for the remaining capability observation. Do not probe other accounts or secrets.

**Before any object write:** bind one exact immutable object/body/hash, complete bytes and size, expected Git ID, authorized repository, and a readback locator. Avoid content-bearing tree batches and same-request dependency assumptions. Small SHA-only trees may only name already-confirmed objects and exact preceding base trees.

**Before any staging ref write:** the entire visible tree must remain a coherent baseline plus approved inert transport files; the manifest/bundle must already be complete; root workflows and their effective permissions must be reviewed; the expected current head or create-only absence must be fresh. No force update is recommended.

**Before the final candidate ref write:** confirm exact full tree and generated blob identities remotely; identify an actual commit object with the intended parent(s); verify connector workflow permission for that transition; use create-only behavior for an absent branch or an ordinary expected-head checked fast-forward for an existing branch; and retain the original response before formatting it. The existence of a tree alone does not prove a commit, branch or workflow result.

**After effects:** independently read actual ref, commit, full tree, four generated blobs, workflow run/event/head and retained verification receipt. Qualification, predecessor acceptance, exact merge approval, deployment and issue closure remain the caller's separate gates.

### 8. Ambiguous-result recovery and durable follow-up

For a missing/failed object response, preserve the raw response and body digest and read the deterministic expected blob/tree ID. If it exists and is exact, reuse it rather than blindly recreating dependent state. If it is absent through the supported exact read, root may decide whether the same bounded operation is warranted; no generic rejection text is treated as a real owner refusal. Do not infer that absence of a ref implies absence of immutable objects.

Commit creation may involve provider-generated timestamps, so record the actual returned commit identity and reconcile by its exact tree/parents/message if its response is lost. An uncertain ref operation requires a fresh ref and ancestry/tree read. An unexpected legitimate head ends the stale-head attempt; it does not authorize force, deletion or rollback of another actor's work. An uncertain hosted push requires both runner artifacts and remote ref/object readback. Runner success, a local generated commit or `published: true` without readback cannot establish delivery.

**Local versus systemic disposition:** the original payload/transport choice and stale source-stage-ref assumption are local process problems. The two generic MCP results indicate an observability deficiency at the client/connector boundary; they do not prove a platform outage or universal service defect. The R0007 large-blob 422 is a second attributable transport failure class, but it is a different boundary and must not be conflated with the generic R000B rejection. No product source repair is justified by these transport facts alone; the separately reported lease finding remains independently owned.

**Minimal durable countermeasure:** keep a preflight record that separates packet mathematical validity, actual object availability, client capability, authentication, branch coherence and external effect receipts. Retain the raw result before any preview access, distinguish client/generic errors from HTTP failures, and require a full-tree coherence check before every runnable candidate ref. This is a scoped checklist/checker recommendation, not a new broad audit framework.

**Escalation recommendation:** return to `/root` for route selection and exact scope/capability review. If a small supported immutable-object operation still produces the generic client error, escalate the preserved request digest, timestamp and raw result to the connector/client owner through an authorized channel. If no legitimate native or hosted Git transport can publish the objects, request the missing supported authentication/capability; do not request approval again for already-authorized engineering, mislabel the owner as refusing, bypass rules, or reinterpret a staging partial as complete. This lane sends no such external message and grants no action authority.

**Follow-up evidence obligation:** the caller should retain the revised bundle/import proof, exact staging and final-tree manifests, effective permission/rule observations, every immutable-object/ref/run receipt, and any failure-body metadata that can distinguish provider validation from size/authentication/client errors without reproducing credentials or source echoes. The bounded diagnosis ends here; publication, readiness, acceptance, currentness, lifecycle and closure remain unresolved by this report.
