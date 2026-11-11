Report state: FINAL

Disposition: GAP-REVISE

# R0016 focused diagnostic independent review

## Review identity and boundary

- Requested model: inherited parent configuration; no model override was requested in the review dispatch. Actual model self-report: GPT-6 Astra Pro. This is a self-report, not an external runtime attestation.
- authoring_context_reuse: no
- other-reviewer visibility: none
- Review role: independent read-only evidence; no mutation, publication, qualification, or closure authority.
- Native installer, PTY, and APT subjects executed by this reviewer: none.
- Source HEAD verified: `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`.
- Source tree verified: `988d6191b24c6f64b6c71014a0077be1e48c4327`.
- Base dependency verified as an ancestor: `bf566111fe530b5de2c7c63ca4586e83d5f4b965`.
- Tracked repository status was clean during initial identity acquisition.

## Exact packet under review

| Input | Actual SHA-256 | Packet match |
| --- | --- | --- |
| `diagnostic-review-packet-1.json` | `7028bdda9d901101fac71b18c336ad9a7e8bff6e724a1c1f59b80a1cbcac1cf6` | Packet itself |
| `diagnostic-review-packet-2.json` | `0185be1206f1b2274bd30898f2b66c28325e4cc97981f84f4d10bc4771ae13c4` | Expanded packet |
| `installer_preview_pty_drain_probe.py` | `7b43268c901434c312ab1d2fb409c9d022225bc9792c2b2311fb6db9878873bf` | Yes |
| `installer_preview_linux_prerequisites.py` | `d21875e36073e6c610155da47ff29aec348c9ce540dbdd51d8cede5ab12e0d9a` | Yes |
| `installer-preview-recovery.yml` | `5d00a09e97cbc8d9fcfa57ee93ff90d0db253f11fd2d578fd568ce2cda2dbc4c` | Yes, packet 2 |
| Original `tests/install-preview.py` | `5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760` | Matches the probe pin |
| Original `.github/workflows/installer-preview-posix.yml` | `6289af8be948c1083965143dd09f635bc4e478c08cc025d667a411b423d217a4` | Reference input |
| Original `tools/qualification/installer_native.py` | `9732e7687ced927be21bdca8f9fae08e29c7104d0119fe435ea74dcc86a1a46f` | Reference input |
| Applicable repository `AGENTS.md` | `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` | Read |

All proposal digests were rechecked unchanged at the end of this first review. These hashes, rather than later contents at the same paths, delimit this disposition.

## Review conclusion

The original child, sentinel, fixture environment, Darwin policy function, and 30-second subject ceiling are pinned to the original harness bytes. The result oracle rejects the bounded false-success variants tested here. The proposed Linux source selection directly excludes the failed mirror list and uses official Ubuntu archive/security sources with the Ubuntu archive keyring. The workflow preserves exact-commit checkout, gates qualification on prerequisite success, retains failed attempt evidence, and leaves the actual Linux suite's network/filesystem containment requirements unchanged.

Two material gaps prevent a PASS for publication of these exact proposal bytes: fallback cleanup can itself leave the direct subject stopped, and Linux preparation still loads unrelated host APT configuration/hooks. Neither gap authorizes broader execution, containment relaxation, fake native proof, source-effect suppression, or a merge. No Windows proposal is included in this review.

## Finding D1 — Failed fallback census leaves the direct subject stopped

| Field | Finding |
| --- | --- |
| Category | Process lifecycle / diagnostic cleanup |
| Location | `installer_preview_pty_drain_probe.py:403–444`, specifically `SIGSTOP` at 410 and exception return at 440–444; caller at 481–507 |
| Evidence | After the first census proves the live direct parent, `force_cleanup` stops it. If the second census raises, the exception handler records the error and returns without resuming, terminating, or reaping that parent. The inert oracle `fallbackCensusFailureAfterStop` records one `SIGSTOP`, no terminal action, `subjectStillStopped: true`, and `subjectReturncode: null`. `run_case` subsequently records incomplete acquisition and suppresses the next case, but has no further direct-parent cleanup step. |
| Impact | A diagnostic-created stopped process and its inherited descriptors can survive the probe. This is a reproducible lifecycle gap even though result classification remains fail-closed. A one-second census timeout is sufficient to enter the branch. |
| Effort | Small, localized fallback cleanup change plus inert failure-path checks. |
| Risk | Medium implementation risk: descendants must not be signalled from stale census PIDs after the ancestry anchor is lost. |
| Confidence | HIGH for the control-flow defect and inert reproduction. No claim that this error occurred on macOS. |
| Fix sketch / smallest countermeasure | Ensure every path after an owned direct-parent `SIGSTOP` makes a bounded, ownership-safe attempt to release or terminate and reap that still-owned direct `Popen` child. Do not guess or signal unverified descendant PIDs. Preserve incomplete classification when descendant termination cannot be proved, retain the terminal-action receipt, and suppress later subjects. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root maintainer; proposed PTY diagnostic only. |
| Acceptance criteria | Census timeout, malformed census, stop-confirmation failure, and child-cleanup errors cannot silently return while leaving the direct subject stopped. Direct-parent actions remain bounded by the existing cleanup allowance. No stale descendant/group signalling is introduced. Unproven descendant state cannot produce a success or authorize another subject. |
| Verification | Pure inert process/OS/census doubles in `recovery/diagnostic-independent-static-evidence/static_oracle_review.py`; result in `static-oracle-results.json`. Rereview changed bytes and rerun bounded doubles before any native observation. |
| Rollback / Plan Closure | Withdraw or replace this unpublished helper. Close this row only against a new digest and retained failure-path evidence; no repository or native mutation was performed by this reviewer. |
| Rejected/deferred rationale | Not rejected. This is distinct from an unavoidable unkillable kernel task: the reproduced live subject is left stopped because the program omits a terminal action. |
| Remaining risk | A terminal action attempt cannot itself prove all descendants exited; actual native capture stability remains a separate requirement. |
| Route | DMAIC |

## Finding D2 — Source overrides do not isolate unrelated APT configuration

| Field | Finding |
| --- | --- |
| Category | Prerequisite acquisition / configuration boundary |
| Location | `installer_preview_linux_prerequisites.py:38–45,68–93` |
| Evidence | The helper records source-list identities and overrides `sourcelist`, `sourceparts`, lists, cache, retries, and timeouts. It does not set an early isolated `APT_CONFIG`, exclude host `apt.conf`/`apt.conf.d`, retain effective configuration, or constrain host update/dpkg hooks. `subprocess.run` inherits the process environment, and `sudo ... apt-get` loads the root-side host APT configuration. The official Ubuntu Noble APT configuration contract confirms this load order and hook execution. |
| Impact | The narrow acquisition can run unrelated host-configured shell hooks as root or inherit acquisition/security settings not represented by the recorded source identities. Therefore exact official source URIs and a private cache do not establish the requested absence of unrelated configuration effects. This is an exposure in the proposal; no such hook execution was observed on the target runner. |
| Effort | Small to moderate: add a per-run early APT configuration and bind it to each APT invocation. |
| Risk | Low to medium: preserve required package installation behavior and signature verification while excluding unrelated host APT hooks; do not change the installer or qualification harness. |
| Confidence | HIGH for configuration inheritance; native target hook population and effects remain UNKNOWN. |
| Fix sketch / smallest countermeasure | Supply and retain an early per-run `APT_CONFIG` that excludes host main/fragments, applies explicit secure acquisition settings, and is passed through `sudo` explicitly. Apply the same configuration to update, policy, and install. Late `-o`/`-c` values alone must not be represented as preventing earlier config loading. Retain the exact config digest and resulting command bindings. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root maintainer; proposed Linux prerequisite helper only. |
| Acceptance criteria | Static/inert checks establish that all APT invocations use the recorded early configuration, the official URI/keyring selection remains exact, unrelated host hooks cannot enter through main/fragments or inherited `APT_CONFIG`, and any update/install/verification failure returns nonzero with `complete: false`. The unchanged Linux containment suite remains the only qualification route. |
| Verification | Source/argv inspection plus Ubuntu Noble `apt.conf(5)` sections DESCRIPTION, DIRECTORIES, HOW APT CALLS DPKG, and Debug::RunScripts: <https://manpages.ubuntu.com/manpages/noble/man5/apt.conf.5.html>, accessed 2026-11-11. No APT command was executed. |
| Rollback / Plan Closure | Withdraw or replace this unpublished helper. Close against a revised digest and a retained inert configuration/argv witness before native acquisition. |
| Rejected/deferred rationale | Not rejected. This row does not allege that default Ubuntu signature verification is disabled or that the official repository route is incorrect. It addresses the unbounded inherited configuration surface. |
| Remaining risk | Package installation necessarily changes the disposable runner's package state and may invoke package-owned maintainer scripts. Those intended prerequisite effects are separate from unrelated APT configuration hooks. Native repository availability and functional containment remain unproved. |
| Route | DMAIC |

## Verified properties and bounded observations

### PTY source identity and acceptance

- `extract` rejects changed harness bytes before subject launch, verifies the original literal snippet digest `8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904`, and checks the original `sandbox_run` default against 30 seconds. The exact original sentinel is the 23-byte `native terminal control` plus newline.
- A separate AST reconstruction in the review oracle removes diagnostic calls from the generated wrapper and obtains the exact original AST. No PTY child operation is replaced or skipped. The parent drain, retained capture, phase markers, and cleanup are the added diagnostic operations.
- The pinned `darwin_profile` function is reused. Its network denial, general write denial, owned writable subtree, terminal allowances, and process-execution denials remain intact for `same-profile`. The separate host control is explicitly labelled and is limited to the original terminal child; it is not substituted for the sandboxed observation.
- A successful result requires complete original terminal JSON, no stderr, exact normalized sentinel bytes, one ordered parent drain/wait/close/completion/cleanup sequence, the actual successful wait receipt for the identified child, child operation receipts, stable captures, no cleanup kill, and completion before the original deadline. The synthetic positive witness and 12 negatives are strictly oracle checks, not platform outcomes.
- Negative variants rejected: timeout, late completion, missing child receipt, wrong waited child, unreaped child, cleanup signal, malformed phase capture, unstable capture, extra stdout, stderr, partial sentinel, and extra PTY bytes.
- Fallback descendant signalling is ordinarily anchored to a stopped owned parent; known descendant PIDs are not signalled after that anchor is killed. There is no global process/group sweep. D1 concerns the missing terminal handling on an exceptional branch.
- Incomplete capture suppresses the next PTY case. The archived original is never replayed by the proposed helper. `--inspect-only` cannot qualify a native platform, and non-Darwin execution without that flag exits unsupported.

### Linux acquisition and workflow

- The source file selects only `https://archive.ubuntu.com/ubuntu` for `noble`/`noble-updates` and `https://security.ubuntu.com/ubuntu` for `noble-security`, with amd64, main/universe, and `Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg`. The helper checks Ubuntu noble and x86_64 before acquisition. `sourceparts=-` excludes the previous mirror source-list route. D2 concerns separate configuration files/hooks.
- Fresh per-run lists and cache prevent reuse of the failed mirror's stale list directory. Update uses `APT::Update::Error-Mode=any`, no retries, HTTPS timeout, and bounded outer commands. Failed commands retain raw stdout/stderr and hashes, leave `complete: false`, and return nonzero. An outer timeout explicitly states that privileged completion is unverified and does not authorize retry.
- Packet 2's workflow triggers only on the own branch and the two helper paths or its own workflow path. It checks out `${{ github.sha }}` using the pinned checkout action, depth 1, and no persisted credentials. The Linux sparse checkout includes the original installers, tests, preset/native-builder inputs, original orchestrator, and prerequisite helper. The macOS sparse checkout includes only the original preview harness and diagnostic helper.
- Linux qualification is a later ordinary step, so failed preparation prevents its execution. It invokes the unchanged `installer_native.py --expected-os Linux --phase r0016`; the original suite still requires unshare, bwrap, network namespace isolation, seccomp transport denial, and the read-only host bind with an owned writable fixture. No prerequisite fallback weakens those requirements.
- Both jobs use `always()` preservation/upload steps, archive bytes without dereferencing symlinks, and retain distinct run/attempt artifact names. Linux preservation includes preparation output even when qualification never starts. macOS executes only the two diagnostic controls. Windows changes are outside its trigger list and scope.
- `cancel-in-progress: false` avoids a newer push cancelling a retained acquisition mid-run. This review does not certify scheduler state, future workflow runs, platform results, or later source changes.

## Original retained evidence checked

Only receipts needed to confirm the diagnostic premise were read; no prior authoring notes or other reviewer reports were consumed.

| Evidence | SHA-256 / observation |
| --- | --- |
| macOS archive `r0016-13868376534.zip` | `128e0cdcc9c465f2dc0b5dac3505339e2127c4911898578442db345c1b7f5b68` |
| macOS top-level `result.json` | `86506deb4592a138382f74c584aefa9f517d89dd43933d82bf9f6e5fd0598c9d`; `DIAGNOSTIC_ACQUISITION_INCOMPLETE`, source commit/tree match, zero product rows |
| macOS same-profile phases | `9450c7ddff205e13e4aad0b0a5d3c22844afe96f87cca2650e6a51fa629da52b`; parent wait begins; child reaches intended exit marker; no successful wait completion |
| macOS host-control phases | `48c4bca3c97d4b09c2a14a2b6d67f9b919372dbe6725211a2565cb55921a53c5`; same bounded phase pattern |
| Original terminal snippet | `8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904`; matches proposed pin |
| Linux original update stderr | `903d7338a9b64a202746e3fa93ef90e5b4b66cb8d80d81b14c6de82a87cbb36a`; failed `mirror+file` route resolving `azure.archive.ubuntu.com` |
| Linux original install stderr | `6f95528caf7e02bd6174679931f3362c075c58efebca91be010ab23e92914f84`; bubblewrap acquisition failed through that route |

These original negative receipts remain negative. Child `exit.before` does not prove an actual exit, timeout does not identify a kernel syscall, and Linux observations cannot establish native macOS behavior.

## Review evidence and limits

| Evidence file | SHA-256 |
| --- | --- |
| `recovery/diagnostic-independent-static-evidence/static_oracle_review.py` | `d38ab6dbe7f643d1b3cf484a812aa0a847a45dcf94527627e33cebd239be05b1` |
| `recovery/diagnostic-independent-static-evidence/static-oracle-results.json` | `2854a8403eab4c01245311c31346544b85cef5213e025794c3e69ebc3f119b7c` |

The oracle performed Python parsing, digest checks, AST reconstruction, pure result assessment, and cleanup with inert doubles. It launched no child process, PTY, installer, APT, or native subject. Repository/external content was treated as data; no prompt-injection instruction or credential requiring disclosure was encountered in the reviewed scope. The only reviewer writes were this report and the separate static evidence directory. Terminal disposition is evidence for maintainer revision, not publication or closure authority.
