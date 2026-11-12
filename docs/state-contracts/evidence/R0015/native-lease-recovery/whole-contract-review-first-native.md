# Independent R0015 engineering and whole-contract review

## Disposition

The inspected candidate is **not ready for whole-contract acceptance**. Actual Windows execution exposes a failed live-directory lease guarantee on both supported PowerShell host families. Normal complete-file setup also remains unqualified because four normal/NoOpen cases reject an ancestor before staging. The latter is plausibly a fixture ACL premise problem; the present receipt does not identify the failing ancestor.

This is an ordinary, separately attributed engineering review by `/root/r0013_review`. It does not authorize merge, reorder the campaign, decide governor currentness, or close an issue. A later remediation is a new candidate and needs bounded review.

## Exact inspected candidate

- Commit: `00a08b69661b5c09e1b6890da032e88265802b9b`; tree: `4f582b1754c43e023ac413423f532ac19bc29d19`.
- PowerShell source SHA256: `a2b36da7c4b07f52cb22cff1fdeaa1e9cffd60f5f95188d8b7f65ce9fa4fa8f8`.
- Bash source SHA256: `609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22`.
- The merged PowerShell file differs from frozen R15 `6e2af0` only inside the inherited R13 Firefox status function; that function equals published R13 `f2161ed6` exactly.

## Findings

### Important: R15-NATIVE-01 — held directory lease permits rename

`StageNative.OpenDirectory` opens with `READ_CONTROL | FILE_READ_ATTRIBUTES` (`0x20080`) and read/write sharing (`3`). In both native PS5.1.20348.5773 and PS7.6.6, the actual custody fixture calls `Initialize-Staging`, then `Directory.Move` before disposing any lease. The rename succeeds. Both raw archives retain `live-lease/temp/attempt-renamed`; the original attempt pathname is absent. This contradicts the intended identity-stability guarantee.

The changed-root cleanup guard separately refuses a replaced identity, and no foreign-user exploit is demonstrated by this same-SID test. The required remedy is nevertheless a native mechanism correction, with held-rename refusal and successful rename after release paired with healthy initialization/cleanup. The original failures must remain retained. Root has delegated narrow source custody for that remedy.

### Important: R15-NATIVE-02 — normal complete-file utility remains unqualified

Both hosts acquire their actual full-file wrappers, discover two eligible targets, and record a selection prompt. Positive and NoOpen then reject an ancestor before staging or download. Subject snapshots remain equal. Thus preview acquisition succeeds in this run, while useful full-file normal setup is still unproved.

The fixture protects only TEMP and host-home leaves. Exact CPython v3.12.10 source shows that `tempfile.mkdtemp` uses Windows mode0700, installing SYSTEM/Admin/OWNER RIGHTS ACEs at the outer fixture root; production treats OWNER RIGHTS as an untrusted principal. This provides a concrete fixture-policy explanation, but the archived receipt lacks native owner/SDDL/readback for the failing component. Record every ancestor and establish supported explicit current-SID ACLs only within the newly owned fixture root and descendants, while preserving production guards.

### Open observation, without a defect verdict

`Initialize-StagingNative` runs `Add-Type` before `Get-TrustedStagingParent`. Existing custody tests preload the type and do not settle whether PS5.1 creates transient compiler files in untrusted TEMP before admission. The separate ASCII fresh-process watcher probe controls TEMP and TMP, verifies actual temp resolution, cold type, PID/nonce, and a known create/delete event, then pauses before the first actual parent check to drain events. Native execution is pending. A Linux parser check is not Windows evidence.

## Supported engineering conclusions

The implementation uses a single invocation-local admission predicate. It binds source identity, native file identity and validated bytes; same-attempt reuse rechecks those facts. Private candidate creation precedes writes. Publication copies to a distinct private retained-volume partial, checks bytes, and performs a non-overwriting move. New unpacked candidates preserve old manual bundles on success or failure. ZIP validation preflights all members before output; strict JSON/UTF-8 and exact canonical preset keys constrain the configured rewrite to one input string token. Actual install/import callers consult admission before offering a usable path. Manual completion, authenticity and long-term browser liveness are not inferred from staged files.

Required-key casing defects were exposed and corrected before this candidate. Both actual Windows transaction suites now pass 28 cases, including the new caller negatives. The independent 26-case actual format probe supports detailed archive/manifest boundary reasoning, with its non-native scope explicit. No additional Critical or Minor finding is added.

## Evidence and limits

| Evidence | Observed scope |
| --- | --- |
| Native Windows components / guards | 18/18 and 10/10 on each host |
| Native Windows discovery | 78/78 on each host; merged exact R13 function |
| Native discovery mutation controls | PS5.1 13 discriminating mutants and useful baseline; PS7 14; PS5.1 root-array-only survivor remains non-PASS applicability |
| Native transaction controls | 28/28 each, no POSIX adapter, Unicode paths/data |
| Native custody controls | 7/8 each; live-root rename fails |
| Native full-file entry | 20/24; four normal/NoOpen failures; exact raw readiness/phase and subject snapshots checked |
| Supplemental transaction mutants | Eight exact named failures with useful paired positives; native foreign cleanup explicitly blocked locally |
| Added failure stages | Actual publication collision after retained copy, second-member extraction failure, and zero writer calls before complete late-member preflight; supplemental pending native run |
| Independent receiving | 427 archive/blob/receipt consistency checks; 23 immutable source/instrument/doc bindings; these are artifact checks, not extra product executions |

Original ZIP and TAR are retained unchanged. No adversarial symlink tree was bulk extracted; only bounded top-level regular receipts were materialized, and deeper regular members were read in memory. The native TAR SHA256 is `7e4fa4d73e2bef57ea9007838ddda1a437b287aedd9db00c85451f37e869d910`.

## Complete obligation denominator

All 17 original parent rows, 9 residual children, 18 November ES rows and 7 terminal gates remain in scope: **51 total**. The map below records the present independent evidence frontier; none of these labels is a lifecycle closure verdict.

| Row | Evidence frontier | Remaining gate |
| --- | --- | --- |
| 21-01 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-02 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-03 | Actual Apple R15 residual receiving still required by this reviewer | Receive exact Apple staging/identity/filesystem/signal/mutant evidence at the R15 final candidate; no Linux-as-Apple credit. |
| 21-04 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-05 | Dedicated foreign-owner admission proof remains open in this review | Require reachable UID0 HOME0755 / subjectUID1000 negative, same-object/mode matched self-owner positive, and terminal-owner-only mutant with intended failure and useful positive. |
| 21-06 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-07 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-08 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-09 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-10 | Lifetime source and bounded native Windows consumer support; original signal scope remains | Resolve live lease finding; receive final Apple normal/failure/INT130/TERM143 and fresh consumer evidence; do not infer browser installation or forever/reboot liveness. |
| 21-11 | Lifetime source and bounded native Windows consumer support; original signal scope remains | Resolve live lease finding; receive final Apple normal/failure/INT130/TERM143 and fresh consumer evidence; do not infer browser installation or forever/reboot liveness. |
| 21-12 | Historical Linux DAC scope preserved, not newly adjudicated here | Root must retain/read exact native distinct-UID reachable controls and source binding. This is separate from foreign-HOME admission and from Windows native ACLs. |
| 21-13 | Bash source preserved; native preservation evidence is scoped | Rebind final integrated source and affected gates; do not substitute Windows tests for original Bash/native obligations. |
| 21-14 | Named original mutation obligation remains visible | Receive the affected final R15 original native mutants and healthy controls, including signal/lifetime paths; retain original failure evidence. |
| 21-15 | Documentation incomplete for final acceptance | Finalize and render README with retained HOME/USERPROFILE lifetime, keep-unpacked rule, optional manual preset/XPI removal, partial retention and retired cross-run cache. Re-read source-linked claims. |
| 21-16 | Configuration/manual semantics supported at inspected scope | Keep original 325x530/permission/title/referrer/approved wrapper semantics and source-exact generated commands through final docs/integration. |
| 21-17 | Public delivery gate open | Read back approved public script/docs/rendered copy-command bytes and final merge; engineering branch availability is not approved delivery. |
| R0015-A01 | Actual Apple R15 residual receiving still required by this reviewer | Receive exact Apple staging/identity/filesystem/signal/mutant evidence at the R15 final candidate; no Linux-as-Apple credit. |
| R0015-A02 | Actual Apple R15 residual receiving still required by this reviewer | Receive exact Apple staging/identity/filesystem/signal/mutant evidence at the R15 final candidate; no Linux-as-Apple credit. |
| R0015-A03 | Actual Apple R15 residual receiving still required by this reviewer | Receive exact Apple staging/identity/filesystem/signal/mutant evidence at the R15 final candidate; no Linux-as-Apple credit. |
| R0015-A04 | Actual Apple R15 residual receiving still required by this reviewer | Receive exact Apple staging/identity/filesystem/signal/mutant evidence at the R15 final candidate; no Linux-as-Apple credit. |
| R0015-A05 | Dedicated foreign-owner admission proof remains open in this review | Require reachable UID0 HOME0755 / subjectUID1000 negative, same-object/mode matched self-owner positive, and terminal-owner-only mutant with intended failure and useful positive. |
| R0015-A06 | Dedicated foreign-owner admission proof remains open in this review | Require reachable UID0 HOME0755 / subjectUID1000 negative, same-object/mode matched self-owner positive, and terminal-owner-only mutant with intended failure and useful positive. |
| R0015-A07 | Dedicated foreign-owner admission proof remains open in this review | Require reachable UID0 HOME0755 / subjectUID1000 negative, same-object/mode matched self-owner positive, and terminal-owner-only mutant with intended failure and useful positive. |
| R0015-A08 | Documentation incomplete for final acceptance | Finalize and render README with retained HOME/USERPROFILE lifetime, keep-unpacked rule, optional manual preset/XPI removal, partial retention and retired cross-run cache. Re-read source-linked claims. |
| R0015-A09 | Public delivery gate open | Read back approved public script/docs/rendered copy-command bytes and final merge; engineering branch availability is not approved delivery. |
| ES15-01 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-02 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-03 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-04 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-05 | Native replacement controls plus supplemental actual failure stages | Execute these specific failure-stage controls on both Windows hosts; preserve complete raw failed partial and old sentinel/manifest evidence. |
| ES15-06 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-07 | Native unsafe archive/caller support plus independent format corpus | Run expanded native/late-preflight discriminators as appropriate to final changes; preserve raw unsupported candidates and no-output evidence. POSIX pure-format probes are not ACL proof. |
| ES15-08 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-09 | Direct native function/caller support on both Windows hosts | Requalify affected final source after native lease correction; run named mechanisms natively and bind final whole-file useful consumers. |
| ES15-10 | Blocked by demonstrated native lease guarantee; other custody cases pass | Resolve R15-NATIVE-01 with actual native held/refused and released/successful rename paired controls, preserve current ancestry/admission/refusal behavior; independently observe first-call compiler effects. |
| ES15-11 | Bounded native cleanup support; lease and first-call boundary open | Repair/requalify actual lease semantics; native foreign-root cleanup mutant and cancellation/failure contract; do not use warm native type fixtures to settle first-call writes. |
| ES15-12 | Actual helper consumers pass; complete-file normal consumers fail | Establish/read back supported disposable fixture ancestry without weakening production checks; then require useful real -File normal and NoOpen handoffs at final source. |
| ES15-13 | Affected merged discovery source and native controls support eligibility join | Preserve prerequisite currentness and whole R13 campaign/order gates; rerun only affected final join risk after source changes. |
| ES15-14 | Native preview/helper scope supports zero effects | Maintain no native-helper load / new-root / cache shortcut / rewriting / cleanup in dry-run; final changed native-helper guards and full source/currentness binding remain required. |
| ES15-15 | Actual Windows host execution acquired, with explicit failures | Qualify corrected exact source/tests on both actual Windows hosts and normal consumers; supplemental LinuxPS7 cannot close failures. |
| ES15-16 | Source wording and scoped caller output reviewed | Final README and public rendered/source readback must state partial/manual recovery and preserve truthful wording at actual full-file normal/failure outcomes. |
| ES15-17 | Entire original denominator retained, not replaced by ES Windows slice | Receive unresolved original Apple/foreign-HOME/README/public delivery evidence and then-current R13/R16 interface preservation. |
| ES15-18 | Independent review in progress; candidate is not ready | Final corrected candidate review, native manifests, rollback/source-map agreement and approved public instructions; no author or reviewer broad readiness conclusion substitutes for evidence. |
| G15-ORDER | Root/owner gate open in this report | R0013 approved merge/delivery/whole closure or actual entitled-owner-approved disjoint reordering. |
| G15-STATE | Source map exists; final revision pending | Update final source/test/evidence manifest, source-linked map and rollback/currentness with native outcomes, retaining all REDs. |
| G15-REVIEW | Independent attributed engineering review delivered, not final acceptance | Review the corrected exact commit/tree and all affected native evidence; root decides formal route/currentness. |
| G15-APPROVAL | Owner gate open | Obtain the entitled owner's exact candidate approval at the permitted campaign boundary. |
| G15-DELIVERY | Root delivery gate open | Perform only the authorized exact merge, then read back public source/docs/copy commands and final tree. |
| G15-CERTIFICATE | Root certificate gate open | Produce and read back truthful full original/residual/ES certificate after all gates, then deliberate issue closure. |
| G15-LIFECYCLE | Root formal gate; reviewer has no authority | Root must honor independently established formal currentness/authority/lifecycle requirements. |

## Declined judgments

No conclusion is given about a foreign-user exploit, first-call CodeDOM writes without native observation, the exact failing ancestor without ACL readback, unreceived R15 original Linux/Apple residual evidence, browser installation or publisher authenticity, same-UID/admin isolation, or final campaign/approval/merge/public delivery authority.

The accompanying JSON retains every full requirement, its evidence and remaining discriminator, precise source bindings and related report digests.
