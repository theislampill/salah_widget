Report state: FINAL

Disposition: PASS

# R0016 focused POSIX diagnostic independent rereview — packet 6

## Meaning of this disposition

PASS applies only to the bounded static/oracle review of the exact packet 6 additions identified below. D1, D2, and D3 are addressed in these bytes. No remaining concrete gap was found in the requested PTY diagnostic, Linux prerequisite-acquisition, or focused workflow scope.

This review supplies evidence to the maintainer. It does not execute or qualify native macOS/Linux subjects, authorize publication or merge, close R0016, or reinterpret the retained original failures as successes. Native repository availability, actual APT completion, native PTY behavior, and the unchanged Linux qualification suite still require their own authentic receipts. Windows is excluded.

## Reviewer identity and independence

- Requested model: inherited parent configuration; no model override was requested. Actual model self-report: GPT-6 Astra Pro; this is not an external runtime attestation.
- authoring_context_reuse: no. The first review was cold. This rereview consumed its own findings, new exact proposal bytes, and maintainer revision/dispatch notices; no authoring working notes were used as evidence.
- other-reviewer visibility: none. No other reviewer report contents were read.
- Native/installer/PTY/APT subjects executed by this reviewer: zero. The retained Python oracles launch no child processes. Filesystem effects are confined to reviewer reports and the separate scratch oracle directory.
- Role: independent evidence only; no repository, mutation, publication, or closure authority.

## Exact source and proposal bindings

The source HEAD and tree were rechecked, tracked repository status remained clean, and the original harness/orchestrator hashes remained unchanged during final rereview.

| Input | Exact identity |
| --- | --- |
| Source HEAD | `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5` |
| Source tree | `988d6191b24c6f64b6c71014a0077be1e48c4327` |
| Base dependency, verified ancestor in first review | `bf566111fe530b5de2c7c63ca4586e83d5f4b965` |
| Packet 6 SHA-256 | `e101403f1ea927b5928d80bdcb0334c848720296dcc677f123d42717013764de` |
| `installer_preview_pty_drain_probe.py` SHA-256 | `ef66ff4be4142038f518cae85a978b0287520bc112ab1d0e1a35e329a6f54325` |
| `installer_preview_linux_prerequisites.py` SHA-256 | `4ddf713e6ae1a8112f0c96fd756e9dc143109dbecd3faa32afa3d1e43d4d54c4` |
| `installer-preview-recovery.yml` SHA-256 | `a7b2ffb55033afeb403471216e3d5966e1631a2eeffcb35ba84c3331081282fc` |
| Original `tests/install-preview.py` SHA-256 | `5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760` |
| Original `tools/qualification/installer_native.py` SHA-256 | `9732e7687ced927be21bdca8f9fae08e29c7104d0119fe435ea74dcc86a1a46f` |
| Applicable repository `AGENTS.md` SHA-256, read in first review | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` |

The two Python helpers are unchanged from packet 3. The archive oracle reverified all three packet 6 bindings. Later files at the same paths are outside this disposition unless their digests match.

## Finding dispositions

### D1 — Owned direct-parent rescue after failed cleanup census: addressed

| Field | Disposition |
| --- | --- |
| Category | Process lifecycle / diagnostic cleanup |
| Location / evidence | PTY helper lines 440–470 now record a direct-parent rescue after a census/cleanup exception. The owned unreaped `Popen` child receives a kill attempt; kill failure leads to `SIGCONT` plus termination; remaining cleanup time bounds the wait. The independent inert checks cover failure after stop, initial census failure, kill failure, and unproved terminal status. |
| Impact of original defect | The packet 2 helper could leave its own subject stopped after a second-census failure. The original inert negative witness remains retained. |
| Smallest countermeasure realized | Bounded direct-parent rescue without guessing descendant PIDs, plus an explicit terminal-status receipt. |
| Effort / risk / confidence | Small change; medium lifecycle risk; HIGH confidence in the verified control flow. |
| Repair class / owner | instrument/acceptance defect; root maintainer, diagnostic helper. |
| Acceptance / verification | All four inert paths attempt the direct-parent terminal action, no unverified descendant signal is emitted, and fallback `complete` remains false when ancestry/descendant proof is missing. The uncertain-status case remains incomplete. Existing 30-second subject and six-second cleanup allowances are unchanged. |
| Rollback / plan closure | Original packet 2 defect remains a historical GAP. This row is addressed only for the packet 6 helper digest; a revert or changed digest requires reassessment. |
| Rejected/deferred rationale | Not rejected; repaired and statically verified. |
| Remaining risk | A signal attempt cannot prove native kernel termination. Unproved descendant/capture state must remain incomplete and suppress the next case, as the retained caller does. |
| Route | DMAIC |

### D2 — Unrelated APT configuration inheritance: addressed

| Field | Disposition |
| --- | --- |
| Category | Prerequisite acquisition / configuration boundary |
| Location / evidence | Linux helper lines 87–111 create an owned empty configuration-parts directory and an early `APT_CONFIG`; source, source-parts, main, trusted-parts, lists, cache, TLS, expiry, and signature settings are recorded. Update/install explicitly use `sudo -n env APT_CONFIG=...`; policy/config-dump use the same file. |
| Impact of original defect | Packet 2's source overrides still permitted unrelated host APT configuration/hooks. |
| Smallest countermeasure realized | Isolated early configuration, explicitly passed after sudo, retained with its hash and a captured effective-config command. |
| Effort / risk / confidence | Small to moderate change; low to medium acquisition risk; HIGH confidence in static configuration/argv binding. |
| Repair class / owner | instrument/acceptance defect; root maintainer, Linux prerequisite helper. |
| Acceptance / verification | Three inert main-function cases verify the success command sequence, exact early-config binding, official source/keyring strings, security settings, update failure, and update timeout. Failure/timeout returns nonzero, retains command streams/hashes, leaves `complete: false`, and never reaches install. No APT command executes in these checks. |
| Rollback / plan closure | Packet 2 remains historically deficient. D2 is addressed only at the pinned revised helper digest. |
| Rejected/deferred rationale | Not rejected; repaired and statically verified. |
| Remaining risk | Actual acquisition, package-managed installation effects, and functional containment remain native evidence obligations. Package-owned maintainer scripts and ordinary package-state changes are intended preparation effects, separate from unrelated host APT hooks. |
| Route | DMAIC |

Ubuntu Noble's primary `apt.conf(5)` reference documents early environment configuration, later main/parts loading, and shell hooks; that contract informed the review, not a claim that any target-host hook ran. Reference: <https://manpages.ubuntu.com/manpages/noble/man5/apt.conf.5.html>, accessed 2026-11-11.

### D3 — Archive inventory and retained bytes can differ: addressed

| Field | Disposition |
| --- | --- |
| Category | Evidence acquisition / archive consistency |
| Location / evidence | Workflow lines 62–65 now read a source file once, write that exact `raw` buffer into the retained file, and hash/size the same buffer. The packet 5 witness retained a 16-byte inventory for a 47-byte copy after an inert producer append; the packet 6 witness retains and hashes the same 16 bytes while the later source becomes 47 bytes. |
| Impact of original defect | A continuing producer after incomplete acquisition could cause a manifest mismatch and undermine the retained error evidence. |
| Smallest countermeasure realized | One observed byte buffer supplies both the retained capture and its inventory entry. |
| Effort / risk / confidence | One local export change; low risk; HIGH confidence from the exact-workflow AST witness. |
| Repair class / owner | instrument/acceptance defect; root maintainer, Linux workflow preservation step. |
| Acceptance / verification | The late-append witness produces matching retained bytes/digest/length. The collector never traverses the three omitted APT directories, rejects unexpected symlink/directory inputs, and retains a separate product-fixture marker byte-for-byte inside the tar archive. No child or native subject executes. |
| Rollback / plan closure | Packet 5's negative witness remains retained. D3 is addressed only at the packet 6 workflow digest; reverting to a second path read reopens it. |
| Rejected/deferred rationale | Not rejected; repaired and verified with the same failure mechanism. |
| Remaining risk | A coherent retained buffer after incomplete acquisition is a bounded snapshot, not proof that the producer finished or that the full stream was captured. Preparation completeness remains false when the command did not complete. |
| Route | DMAIC |

## Retained acceptance properties

### PTY diagnostic

The revised helper still binds the original harness SHA-256, original terminal literal SHA-256 `8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904`, original 24-byte sentinel, fixture environment AST, and original Darwin policy function. Independent AST reconstruction continues to recover the exact original operations after removing diagnostic calls. The parent drain is the functional normal-path change. The original child `/dev/tty` open/write/close/exit sequence is retained.

The same-profile policy keeps the pinned network/filesystem/process restrictions. The explicitly labelled host control is a separate observation of the original terminal child. Neither control runs an installer. The original 30-second subject ceiling remains exact; a later cleanup allowance cannot turn a timeout into success.

The result oracle continues to require exact normalized sentinel bytes, complete original terminal JSON, empty stderr, actual successful child wait/reap, ordered parent and child operation evidence, stable captures, no cleanup kill, and subject completion before the original deadline. All 12 retained negative variants are rejected. Incomplete owned-process cleanup suppresses the second case. The archived original is bound and never replayed by this program.

### Linux acquisition and workflow

The acquisition source file selects the official Ubuntu archive/security HTTPS URLs, noble suites, amd64, main/universe, and the installed Ubuntu archive keyring through `Signed-By`. Fresh lists/cache and the isolated configuration exclude the previous failed Azure mirror route. Updates fail on acquisition errors, retries are disabled, and timeouts are bounded. All started command observations remain available as top-level raw streams and structured receipts. Incomplete acquisition returns nonzero and prevents the later qualification step.

The workflow retains exact `${{ github.sha }}` checkout, pinned action identities, no persisted checkout credentials, the named own-branch/path trigger, and `cancel-in-progress: false`. The Linux sparse checkout includes the original installer/test/builder inputs and the original orchestrator. It invokes the unchanged Linux suite, whose bwrap, network-namespace, seccomp, and read-only filesystem requirements remain intact. macOS checks out the original preview harness and diagnostic helper and executes only the two PTY controls. Windows is absent from this workflow and its trigger paths.

The revised Linux export copies every top-level regular preparation file, records exact byte/digest inventory entries, and omits only `apt-lists`, `apt-cache`, and `empty-config-parts`. It records those omissions and rejects unexpected symlinks/types/directories. This resolves the earlier recursive-copy risk from APT-owned directory permissions. Downloaded package indexes/cache contents are not represented as retained signature bundles. The enclosing product `installer-evidence` tar operation remains unchanged; no product fixture/snapshot exclusion was introduced. Both jobs keep unconditional preservation/upload steps and distinct run/attempt artifact names.

## Evidence index and preserved history

All paths below are under `/tmp/r0016-successor-20261111/recovery/`.

| Evidence | SHA-256 |
| --- | --- |
| `proposed/diagnostic-independent-review-packet-2.md` — original FINAL GAP-REVISE | `61de4bbd65c08071d4eaad9f1cd97b1bb985dd95fd25253975ae82c0216ae741` |
| `diagnostic-independent-static-evidence/static_oracle_review.py` — original D1 negative/oracle checks | `d38ab6dbe7f643d1b3cf484a812aa0a847a45dcf94527627e33cebd239be05b1` |
| `diagnostic-independent-static-evidence/static-oracle-results.json` | `2854a8403eab4c01245311c31346544b85cef5213e025794c3e69ebc3f119b7c` |
| `diagnostic-independent-static-evidence/static_oracle_review_packet3.py` — unchanged revised helpers | `f18b1733926fc608dddd8e336860a0c3ec963932bced3c3b274050fbad761f63` |
| `diagnostic-independent-static-evidence/static-oracle-results-packet3.json` | `dfd581b17a387ebc339a2539f84e54124ef63937394537f04b1dd70f402d4fb2` |
| `diagnostic-independent-static-evidence/archive_oracle_packet5.py` — D3 negative | `44e4947a2d2ded7e7fa5da3306ccd7ea1dc962f63874bfcfd8b0c238113fb87e` |
| `diagnostic-independent-static-evidence/archive-oracle-results-packet5.json` | `4d248cb6383ce2685ee63e6499509c87eae766eb5b9132bc3e8e7a0e6c41d21c` |
| `diagnostic-independent-static-evidence/archive_oracle_packet6.py` — revised archive checks | `c3788b87ebf5baea05023a1cd0a977a48fda36904835d5998a2b5e73a02e3364` |
| `diagnostic-independent-static-evidence/archive-oracle-results-packet6.json` | `81da891ab91f671b9cc41e5e5ba6d2987279c1d8cedd5ae42e3d3df487f3321a` |

The packet 6 archive oracle verifies all three final proposal hashes before exercising the exact preservation snippet.

The original macOS artifact/result/phase hashes and Linux mirror-failure streams remain bound in the preserved packet 2 report. Those failures stay negative. This PASS does not convert an intended child-exit marker into a completed exit, identify a kernel syscall from a timeout, or use Linux as evidence of macOS behavior.

Repository and external contents were treated as data. No credential or prompt-injection instruction requiring escalation was encountered in the reviewed scope. The work stops at the exact-source static review boundary.
