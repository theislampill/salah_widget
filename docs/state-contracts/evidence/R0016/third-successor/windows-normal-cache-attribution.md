# R0016 — bounded c10/c11 profile attribution

**Disposition: attribution bounded; all four original normal rows remain adverse.** The evidence distinguishes a PS7 startup-profile change from a PS5.1 module-analysis-cache creation. It does not identify each writer in the product processes or qualify a new candidate. No native execution, shared-source edit, Git operation, remote mutation, cache exclusion, or result waiver was performed.

## Identity and exact scope

The primary evidence is native run **43165073655**, PS7.6.6 artifact **13919044745**, `native-after-acl/ps766/files/installer-evidence/f/e77c549b3d0eb9eee/{c10,c11}`. The original ZIP is 4,303,737 bytes, SHA256 `8ec846771c95174f93b70164e231e8b825c974c01e28b0cf3958b3e284c6b7be`. The supplemental PS5.1 evidence supplied by root is artifact **13920679003**, fixture `e6aacf524684fb06d/{c10,c11}`.

Both artifacts declare source commit **af0b2f35abf731c777005f241f9c5fb5d35aaff3**. Their retained `install.ps1` is 110,645 bytes, SHA256 `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4`. The PS7 harness is `tests/install-entry-native-composition.py`, SHA256 `5b6a18dfb2f4470839a8049760c09067617ab07f69b200362a73f5aeba124fae`. Findings concern these retained bytes; they do not qualify the concurrently changing d5027db/3b0e614 integration.

`observations.json` contains every derived row difference, original errors, timing, commands, host identities, and selected source-free member identities. `input-hashes.json` binds the read inputs. `SHA256SUMS` binds this report and its supporting files. `derive_attribution.py` reads JSON/bytes and parses a bounded documented cache format; it imports or executes no archived source.

## What the raw evidence establishes

For all four normal rows, the complete profile after host-only warmup equals the profile before product launch and at readiness. All three full-input inventories retain two agreeing passes. All processes exit naturally with integer zero; the qualification failures are preserved.

| Native row | Changes after ready, through observed exit | Original failure |
|---|---|---|
| PS7 c10 positive, 2.390 s | Eight expected new bundle paths; no removals; root mtime; startup-profile bytes 66,520 → 191,476, SHA and mtime changed | `USERPROFILE changed outside the one validated new bundle` |
| PS7 c11 no-open, 2.297 s | Eight expected new bundle paths; no removals; root mtime; startup-profile bytes 66,532 → 191,420, SHA and mtime changed | Same |
| PS5.1 c10 positive, 27.437 s | Eight expected bundle paths; root mtime; `analysisCache/.` absent → file, 8,911 bytes | Undeclared owned analysis-cache input fields changed |
| PS5.1 c11 no-open, 25.937 s | Eight expected bundle paths; root mtime; `analysisCache/.` absent → file, 8,911 bytes | Same |

For PS7 the startup-profile file is `AppData/Local/Microsoft/PowerShell/StartupProfileData-NonInteractive`; its inode, creation time, mode, security, and link count remain unchanged. Only size/hash/mtime change. `analysisCache` stays absent. For PS5.1 the separate `analysisCache` role changes every absent-to-file field; there is no corresponding startup-profile change in these product profiles. Both hosts also retain `subject/temp` mtime changes before-ready and ready-after; those are not silently folded into profile results.

The product source explicitly creates a direct `USERPROFILE/SalahWidgetBundle-*` child (`install.ps1:691–718`). The harness explicitly allows only that validated child and the profile root's mtime change (`install-entry-coverage-support.py:106–127`); it allows no existing descendant change. Therefore the root mtime is an already-declared consequence compatible with observed bundle creation, while the cache changes violate the existing predicates. This does not prove that no transient writes occurred between snapshots.

The ready barrier follows Utility-wrapper import, fixture setup, and spy export, then precedes return from that import (`install-entry-native-composition.py:42–126, 210–232`). The adapter labels ready→exit as `entryDelta` (`:270–276`); that is a temporal label, not a writer attribution. The normal path has no held product invocation (`:553–564`). c11's absence of open effects and the log-only `Start-Process` spy also make actual browser launch unnecessary for these effects.

## Independent source-free evidence and mechanism

The original source-free run **43152365236** was reread directly from the retained ZIP/TAR bytes, with its ZIP hashes checked. Its genuine `-NoProfile -File` neutral source prints two fixed markers and does not acquire the installer. The retained neutral observations are copied under `sourcefree-selected/` without altering originals.

* **PS7, 0.937 s:** startup directories appear before ready; the startup-profile file appears only ready→postexit. The current c10/c11 host-only warmups also create that file after ready without running the installer.
* **PS5.1, 20.797 s:** `analysisCache/.` becomes a 9,019-byte file before ready; ready→postexit has no changes. Current normal-row warmups last only 0.375/0.390 s. A short successful warmup is therefore not evidence that a later 26–27 s process will avoid delayed cache persistence.

The PS5.1 cache payloads were fully parsed as `PSMODULECACHE` version 1, consuming every byte. Current and prior neutral caches each have five module-path entries: fixture Utility `.psm1`/`.psd1`, and AWSPowerShell 5.0.327 `ImportGuard.ps1`, `AWSPowerShellCompleters.psm1`, and `AWSPowerShellLegacyAliases.psm1` under `C:\Program Files\WindowsPowerShell\Modules`. This is content-level support for module analysis, not evidence that the AWS modules executed. These external discovery entries remain adverse evidence, not an allowed-input assumption.

Exact PowerShell v7.6.6 source resolves to commit **f260eb9c31ec72c5282f98e5ea24d9be4f8d7536**. [ConsoleHost.cs](https://github.com/PowerShell/PowerShell/blob/f260eb9c31ec72c5282f98e5ea24d9be4f8d7536/src/Microsoft.PowerShell.ConsoleHost/host/msh/ConsoleHost.cs) sets a profile root at lines 148–159 and starts the noninteractive profile at line 329. [AnalysisCache.cs](https://github.com/PowerShell/PowerShell/blob/f260eb9c31ec72c5282f98e5ea24d9be4f8d7536/src/System.Management.Automation/engine/Modules/AnalysisCache.cs) separately selects `PSModuleAnalysisCachePath` at 1085–1092 and queues serialization after a 10-second delay plus repeated 3-second stability checks at 665–695. Its format at 805–827 matches the fully parsed payloads. This source supports a delayed-module-cache hypothesis; it is not a binary/source binding for closed-source Windows PowerShell 5.1.

The representative [.NET 10.0.0 multicore JIT source](https://github.com/dotnet/runtime/blob/v10.0.0/src/coreclr/vm/multicorejit.cpp) both writes on `StopProfile` (912–934) and has a Windows delayed writer (832–869). Its [configuration declaration](https://github.com/dotnet/runtime/blob/v10.0.0/src/coreclr/inc/clrconfigvalues.h) declares a 12-second default write delay and `MultiCoreJitNoProfileGather` at 341–343. This is a mechanism reference, not proof that the artifact's complete native runtime dependency tuple equals this source version.

Consequently, installer execution is **not necessary** for either class of effect. The current evidence still cannot assign the exact product-run writes to a PID/stack, distinguish every workload-induced runtime write from background work, or prove no unobserved transient effects. No filename-based subtraction is justified.

## Smallest useful next native discriminator

**PS7: calibrated configuration, retaining default evidence.** Reuse the already-reviewed source-free host probe's fixed default/no-gather cold/warm controls on the exact admitted executable and runtime dependencies. Change only the declared prelaunch `COMPlus_MultiCoreJitNoProfileGather=1` variable for its paired mode. Retain all profile/input paths, both snapshot passes, PID/nonce handshakes, effective environment, raw captures, and final process exit. A usable result requires the default control to reproduce the post-ready startup-profile difference and the no-gather control to remove it; otherwise report the experiment inconclusive. Only then acquire c10/c11 under that explicitly scoped configuration and require the existing full comparisons. Preserve the original default failures. Do not claim ordinary default invocation passed or that the setting is supported on PS5.1 merely because the source names it.

**PS5.1: one delayed neutral control.** Use the current genuine source-free `-File` control and identical Utility wrapper, cache path, native modules, and prelaunch environment. After the existing ready/ACK barrier, hold the neutral process for a fixed **16 seconds**, then take one parent-observed full held inventory at a PID/nonce checkpoint before allowing natural exit. Preserve the original ready and final postexit inventories. If the previously absent cache appears during that source-free hold, the installer is unnecessary for this delayed write under the current wrapper; if absent, this discriminator has not reproduced the proposed mechanism. The first implementation correction to test would then be a bounded completed source-free cache preparation before the product baseline, followed by the unchanged complete normal predicates. Preparation success alone cannot qualify the product: any later cache change must still fail. Do not set its path to `NUL`, exempt the role, or suppress the failure.

**Do not make `PowerShell.Exiting` the qualification boundary.** [LocalConnection.cs](https://github.com/PowerShell/PowerShell/blob/f260eb9c31ec72c5282f98e5ea24d9be4f8d7536/src/System.Management.Automation/engine/hostifaces/LocalConnection.cs) raises the event during runspace closure at 843–844, before other teardown. It provides no ordering guarantee against the independent analysis-cache task or the native JIT timer. An optional exit-event checkpoint can add temporal evidence only if its handler completion is acknowledged and its own effects retained; it cannot replace full postexit observation or prove writer causality.
