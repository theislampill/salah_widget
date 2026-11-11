Report state: FINAL

# Original Windows PS5.1 artifact receiving — R0016

## Decision and authority

**Preserve the original core FAIL and native-controls PROVENANCE_BLOCKED. Admit the 14 full-entry rows only for their measured, narrower scope.** The received PS5.1 evidence does not justify R0016 acceptance, a merge, issue closure, a full-contract completion claim, or a speculative installer repair.

The decisive distinction is that every core product process changes two timestamps, whereas the full-entry harness does not record timestamps for its separate TEMP/discovery subject. Its complete USERPROFILE window is metadata-sensitive and passes. Neither result should be substituted for the other.

This worker performed read-only artifact/source inspection and independent consistency calculations. No installer, PowerShell/native test, product suite, remote effect, commit, push, merge, or subagent execution occurred. The only written file is this report. Root retains shared-source ownership. The 46-row R0016 contract and the R0013/R0015 denominators remain unaltered; this is not a row-closure certificate.

## Evidence roots and received identities

- `E` means the exact absolute artifact root `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13867274335/contents/installer-evidence`.
- `S` means the exact inspected source root `/tmp/r0016-successor-20261111/salah_widget`.
- Commission and complete issue/comments were read from `/tmp/r0016-successor-20261111/recovery/github-recovery.json`; SHA256 `7d6f1992a2e9795584e7521227825da0300c9d41b38fd1442a9bcf9ceb15b48d`. `S/AGENTS.md` was read. External/repository prose was treated as task evidence, not fresh action authority.
- Received ZIP `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13867274335.zip`: **4,718,119 bytes**, computed SHA256 **`742acd89027366b8ce8651f2703c8e34c532be1176b1cf5e995671b3258dcd19`**, exactly the commissioned digest. The extracted artifact contains 2,718 files.
- The continuity comment associates it with original run `43036427882`, PS5.1 job `130576351421`, artifact `13867274335`. This association is supplied by the retained GitHub recovery packet; this worker performed no fresh network retrieval.
- `E/result.json` reports commit `3d091c3515c6258e4983ea71d2426be399881936`, tree `2e57dcac25c52f3fd968006bfd3ddacb5d7073bb`, phase `r0016`, overall/qualification status `FAIL`, diagnostic acquisition `COMPLETE`.
- Inspected local HEAD was `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`. All seven relevant source/test/collector files below match the original collector hashes exactly. The frozen original installer also matches. This is exact-byte reuse for these files, not proof of unrelated tree contents or later changes by another writer.

| File in S | SHA256 (collector and inspected bytes agree) |
| --- | --- |
| `install.ps1` | `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e` |
| `tests/install-preview.ps1` | `1cb7eeea0f8e72ffb3ca8ef8492778dabef4d009474f26cfe5601c24f658094b` |
| `tests/install-preview-acquire-timed.ps1` | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` |
| `tests/install-preview-native-controls.py` | `4bb3d2e046a626758b991eaf6237aff7fab891434fe33d2ed1ce1799264bbda0` |
| `tests/install-entry-native-coverage.py` | `5f86fd9c3f93381b2f5aa43be26e6a0bb1a4e1d6b2293576a25b831dba2736f1` |
| `tests/install-entry-coverage-support.py` | `52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a` |
| `tests/install-native-receipts.py` | `c9c5cc6e6ad8e037b232e53167af766948c48bad0fd4e263369989c6475b57c5` |

The recorded native host is Windows Server 2022 (`Windows-2022Server-10.0.20348-SP0`), image `20261101.353.1`, Python 3.12.10 AMD64, Windows PowerShell **5.1.20348.5773**, executable `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`. Core launch sidecars bind the absolute host, PID, native driver path, command, start/exit timing and budget. Full-entry profile receipts bind command, actual PID and nonce. These are retained CI/runtime identities; no independent host-executable digest or hardware attestation is claimed.

## 1. Core preview: actual failure and attribution boundary

`E/ps51-install-preview.json` has 63 top-level rows: four fixture interception controls PASS, 37 helper rows FAIL, 14 whole-source wrapper rows FAIL, and eight aggregate mutation pairs FAIL. Flattening the eight healthy/mutant pairs gives **67 actual product children**, in addition to the four fixture controls. All 67 product children and all 67 preceding baseline children exit 0, report completed capture, and do not time out. Product process durations are 23.410–25.036 seconds; baseline durations are 23.294–23.561 seconds; the recorded per-child budget is 60 seconds. Raising a timeout would not discriminate these failures.

Every product before/after snapshot differs in **exactly** these two fields:

| Subject-relative path | Changed field | Frequency | Unchanged fields relevant to the finding |
| --- | --- | --- | --- |
| `/temp` | `lastWriteUtc` | 67 / 67 | Names, attributes, SDDL and remaining recorded fields |
| `/user-profile/AppData/Local/Microsoft/Windows/PowerShell/StartupProfileData-NonInteractive` | `lastWriteUtc` | 67 / 67 | **File hash**, names, attributes, SDDL and remaining recorded fields |

No product-window path was added or removed, and no product-window file hash, ACL/SDDL, or attribute field changed. This PS5.1 result must not be described as the previously reported PS7 hash-changing observation. The startup-file hash remains identical across each PS5.1 product window.

All 67 preceding baseline windows also change state. They create the Microsoft/Windows/PowerShell startup-profile hierarchy and its file, change TEMP metadata, and show varying additional directory timestamp changes. The retained harness sets `mode='baseline'`, runs the same driver, checks a terminal `baseline:true, installerExecuted:false` record, then deletes those control files before the product run (`S/tests/install-preview.ps1:315–339`; driver baseline branch at 173–178). That baseline does **not** mean a bare native host: it includes the PowerShell host, driver setup, source parsing/breakpoint preparation, recorder writes to the separate control root, and parent observation.

The supported cause of core failure is **non-quiescent subject state across the recorded native process windows**. The common state changes are consistent with host/driver/observer activity and also occur in the source-unevaluated baseline route. The retained data does not identify the process or syscall responsible for either timestamp, does not reveal a transient TEMP filename, and does not locate the changes relative to core pre-source readiness. Therefore the test's error text “Installer changed subject USERPROFILE/TEMP names, attributes or bytes” is a valid gate rejection but is not by itself a writer attribution.

No changed path is excluded, no timestamps are normalized away, and no FAIL is reclassified as PASS. An installer guard repair is not justified solely by these observations. Source-triggered compiler/Add-Type effects would remain installer effects if demonstrated; they are not to be excused as generic host startup.

### Core raw custody and readiness

For all 67 product rows and 67 baseline rows, the raw `.before.json` and `.after.json` files equal the corresponding structured receipt arrays. The 134 `.launch.json` files agree on PID, host and driver path. All 67 retained `host-control/case.json` specs agree with row source hashes; all source variants hash to the recorded values. All 67 `host-control/preview-ready` files match their case nonce, all event sidecars match the recorded attempts, and all 62 available terminal observations equal `host-control/child-result.json`. The five denied-effect mutant children intentionally have no terminal result and retain their source event instead. No consistency discrepancy was found. The collector-normalized core JSON and fixture `results.json` are semantically identical. The retained `preview-child.ps1` equals the here-string generated by the exact inspected test.

`process.readiness:false` is **not** evidence that core readiness was missing. The imported acquisition helper checks `R0016_ACQUIRE_READY` (`ready.txt`), while this core driver uses `spec.readiness` (`preview-ready`). Core admission separately verifies the latter nonce (`S/tests/install-preview.ps1:349–353`; `S/tests/install-preview-acquire-timed.ps1:114–116,136–150`). The core marker contains a nonce, not a PID; PID association comes from the case's launch receipt. Do not conflate the two readiness APIs.

There is a custody limitation worth preserving: the harness removes baseline readiness/result/events and overwrites its `case.json` before launching the product (`S/tests/install-preview.ps1:337–338`). Baseline snapshot/launch/capture sidecars remain, but its separate source-free terminal assertion and baseline-mode spec are not retained for independent raw rereading. The matched test source describes the baseline branch; a future diagnostic should preserve each launch's actual mode, nonce and terminal record separately.

## 2. Interception controls, mutants and native companion

The four dedicated control children support the narrow source-call interception claim: allowed outside-subject method write and loopback transport execute; their denied counterparts record the source attempt and prevent the target effect. This is not an operating-system sandbox. The core explicitly reports `independentHardContainment: NOT_ACQUIRED` and scopes itself to the enumerated source method/cmdlet calls, guards, contexts and snapshots. The wrapper is not a fresh installer `-File` process.

| Retained mutant | Observed mutant-specific evidence | Paired status |
| --- | --- | --- |
| `eager-staging` | Recorded source-call `IO.Directory::CreateDirectory` at entry | Uncredited: healthy fails |
| `cleanup-in-preview` | Recorded source-call `Dispose`, owner `Clear-OwnedScratch` | Uncredited: healthy fails |
| `cached-path-return` | Terminal result returns one nonempty cached path; common snapshot failure precedes return-value assertion | Uncredited: healthy fails |
| `copy-success-when-suppressed` | Terminal result returns Boolean `true`; common snapshot failure precedes return-value assertion | Uncredited: healthy fails |
| `copy-null-array-truthiness` | Terminal result records `[false]`, `nullReturnCount:1`; common snapshot failure precedes return-value assertion | Uncredited: healthy fails |
| `clipboard-attempt-during-preview` | Recorded source-call `Set-Clipboard` | Uncredited: healthy fails |
| `native-api-load-before-guard` | Recorded source-call `Add-Type` | Uncredited: healthy fails |
| `swallowed-direct-transport` | Recorded source-call `Connect` | Uncredited: healthy fails |

Five mutant children fail on the recorded attempt before the state oracle; the other three fail on the common timestamp gate. All eight corresponding healthy runs fail on the timestamp gate. These observations retain useful targeted RED evidence, but **zero of the eight pairs establishes healthy-to-mutant discrimination**, and no pair gains normal/NoOpen survival credit.

`E/ps51-preview-native-controls.json` is `PROVENANCE_BLOCKED`, exit 2, `nativeExecution:false`, `results:[]`, `allRequiredNativeSurvivalEstablished:false`, error **“Prior discriminator did not pass: eager-staging”**. The companion correctly refuses the failed producer prerequisite (`S/tests/install-preview-native-controls.py:203–217`). Its `custodyUnchanged:false` is not an observed source rewrite: the code uses false when no completed custody plan exists (`:519–521`), and independently inspected source bytes still match. The companion performed no native entry execution. The base full-entry positives below cannot be substituted for each retained mutant's missing native survival.

## 3. Full-entry PASS: independently supported scope

`E/install-entry-native-coverage.json` reports all 14 selected cases passing, from a fresh native `powershell.exe -NoProfile -File <exact install.ps1>` process for each case. The source SHA256, test SHA256, support SHA256 and preset SHA256 agree with the recorded inputs. The exact measured case ledger is:

| Case | PID | Process exit | PID/nonce ready | Effect count | Measured result |
| --- | ---: | ---: | --- | ---: | --- |
| `github` | 7652 | 0 | true | 0 | Unchanged preview/refusal state |
| `cached` | 1056 | 0 | true | 0 | Unchanged preview/refusal state |
| `store` | 8072 | 0 | true | 0 | Unchanged preview/refusal state |
| `ask` | 6408 | 0 | true | 0 | Unchanged preview/refusal state |
| `installed` | 2632 | 0 | true | 0 | Unchanged preview/refusal state |
| `mixed` | 3652 | 0 | true | 0 | Unchanged preview/refusal state |
| `legacy` | 3896 | 1 | true | 0 | Unchanged preview/refusal state |
| `none` | 1552 | 1 | true | 0 | Unchanged preview/refusal state |
| `missing-preset` | 6032 | 0 | true | 0 | Unchanged preview/refusal state |
| `bad-option` | 3996 | 1 | false | 0 | Argument refusal before readiness; before/after state unchanged |
| `positive` | 2520 | 0 | true | 15 | Validated retained fixture bundle |
| `no-open` | 2976 | 0 | true | 11 | Validated retained fixture bundle |
| `readable` | 7364 | 0 | true | 0 | Unchanged preview/refusal state |
| `unreadable` | 760 | 1 | true | 0 | Unchanged preview/refusal state |

For every case, the structured profile receipt, raw before/at-ready/after sidecars, ready token, stdout/stderr hashes, subject before/after records, and baseline-to-entry profile handoff reconcile. There were 16 checked raw associations per case and no discrepancies. All host-only baselines finish in 0.359–0.391 seconds; actual ready entries take 23.625–25.203 seconds (unreadable: 24.469 seconds), and malformed option exits in 0.281 seconds.

**Complete USERPROFILE:** every case first runs a separate, source-free `host-only.ps1` in its owned profile. That baseline adds `AppData` and `AppData/Roaming` and changes the profile root timestamp; these changes remain explicit in the baseline receipt. The actual entry starts from that retained post-baseline state, and its before-profile equals the baseline after-profile. All 13 cases reaching readiness have exact `before == atReady`; all 12 preview/refusal cases have exact `before == after`, including malformed option. The malformed option appropriately lacks readiness because parameter binding rejects it before module interception; its complete pre/post profile state still matches. This is an observed prepared-profile entry result, not proof of untouched cold-profile startup neutrality.

The profile observer includes root identity, timestamps, attributes, security, every descendant and file hash (`S/tests/install-entry-coverage-support.py:66–96`). Preview comparisons have no path-name or metadata exemption. Normal comparison admits only the explicitly validated new bundle and the resulting root mtime change; it retains the raw value and requires all other metadata and descendants unchanged (`:106–126`). That normal allowance is appropriate to an effectful positive control and must not be imported into preview.

**Separate TEMP/discovery subject:** the harness redirects TEMP, TMP, LOCALAPPDATA, APPDATA and ProgramFiles to `subject/*`, while USERPROFILE/HOME points to `host-home`. Its `snapshot(subject)` uses descendant relative path, `st_mode`, and file hash; it omits subject-root identity, timestamps and general ACL/security fields (`S/tests/install-entry-native-coverage.py:105–113,197–207`). The special unreadable held-file observer has richer identity, but does not upgrade the entire subject inventory. Thus these 14 PASS rows **do not decide whether TEMP or discovery-directory timestamps changed**, and cannot satisfy the stronger core metadata comparator by substitution. This is a measurement gap, not an invented full-entry timestamp failure.

The full-entry spies intercept the actual named download/metadata/clipboard/open calls, and state proves their expected owned outputs. They do not establish a global transport/kernel sandbox against arbitrary hostile code. Preserving the exact current source and its reachable calls remains part of this bounded result.

### Normal and NoOpen controls

Both normal controls use the real installer staging/configuration flow with fixture assets, while network responses, clipboard and browser calls go to spies. Each records three prompts, one metadata request for the expected release URL, three downloads (Chromium, Firefox, preset), and four clipboard calls pointing to the actual unpacked directory, XPI and configured preset (preset copied twice). Normal has four manager/new-tab opens; NoOpen has none. Their totals are **15** and **11**. Historic 21/17 counts are not the acceptance threshold; the semantic operations and exact arguments are present.

Each retained ZIP and XPI is byte-identical to its case's local fixture ZIP; the manifest bytes are `{"manifest_version":3,"name":"Fixture","version":"1.0"}`. Both configured preset objects differ from the canonical fixture only in `data/orpul7IDXSSP.input`. Their iframe points to `https://theislampill.github.io/salah_widget/#lat=24.47&lon=39.61&method=4`, retaining title, `no-referrer`, geolocation permission, 325×530 style and scrolling setting. Each normal profile gains exactly the expected bundle inventory. This establishes actual contained staging and configured manual-consumer capability, not browser extension installation, XPI authenticity, real clipboard behavior, or remote release availability.

### Actual unreadable metadata control

The readable and unreadable rows have the same metadata SHA256 `f1781b70ed7dcc84cb0a9ddaec2af491dcd7b2f8b796dab3bdf60db992b35afa`. The readable child PID 7364 reads the target and peer and exits 0. The unreadable child PID 760, bound to its own readiness nonce, observes target existence and a readable peer, but target read throws `System.IO.IOException`, native code 32; the installer holds the unknown target and exits 1 with no eligible target. Restoration compares the held file's bytes, identity, attributes, timestamps and security, then records the same digest after release. This is native Windows handle-share refusal, not a fabricated read error or a changed-ACL surrogate.

## 4. Supported conclusions and smallest next discriminator

| Question | What this receipt supports | What remains unknown |
| --- | --- | --- |
| Did core children fail from launch timeout? | No: all 67 product children completed within budget | No larger budget is indicated by this evidence |
| Did the core subject change? | Yes: exactly the two product-window timestamps identified above | Named writer, syscall, transient TEMP operation and phase relative to source readiness |
| Is a healthy installer write demonstrated? | No direct healthy source-call write is recorded; baseline route also changes state | Host versus driver versus observer contribution; absence of unobserved effects is not proved |
| Did recording itself execute operations? | Fixture setup, control-file writes, source parsing, module/guard preparation and snapshots are visible in retained source | Whether any observed subject timestamp is caused by that machinery |
| Does full-entry PASS overturn core FAIL? | No; it independently proves its 14 recorded source/spy/state cases | TEMP/discovery metadata fields omitted by its subject observer |
| Are mutant sensitivity and native survival complete? | No; five attempted effects and three altered returns remain useful observations | All eight discriminating healthy pairs and all eight native normal/NoOpen variant survivals |

**Smallest next acquisition:** use the separately reviewed source-free Windows diagnostic, after the observer's own environment is assigned to owned roots **before that runtime starts**. Keep its script, workflow and environment preparation identities. Compare an observer-only inventory window, a minimal native host child, and the same source-free core driver preparation under the same declared paths and environment, with distinct per-launch mode/spec/nonce/result records. A cold/warm pair is useful to distinguish initial hierarchy creation from the repeated timestamp rewrite; it is an experimental comparison, not an arbitrary retry policy.

Retain complete before/readiness/after inventory for USERPROFILE **and TEMP/discovery**, including the root, all timestamps, hashes, attributes and ACL/security. Keep recorder outputs outside those measured subjects. Include observer identity and its preparation receipt so observer startup is not silently attributed to a later child. The current core readiness markers cannot retrospectively provide a mid-window state they never captured.

If writer attribution is needed after that source-free comparison, acquire a declared process-correlated native event trace for the two actual changed paths with recorder overhead and limitations preserved. A filesystem timestamp alone does not identify a PID or deleted transient file. Do not increase budgets, exclude the startup cache, ignore TEMP metadata, or patch installer guards merely to make the existing result green. The original failures and measured full-entry pass remain retained regardless of the next diagnostic's outcome. Any later correction requires its own exact-byte independent review and affected qualification; this report supplies no execution or publication authority.

## 5. Exact receipt hashes

All following paths resolve under the absolute `E` root stated above. Their SHA256 values were calculated directly from the received bytes.

| Evidence path relative to E | SHA256 |
| --- | --- |
| `result.json` | `bc5987a90a8e4d13e38bfb08e793aad3cca321c3b096bfe16cbdd68393a957f0` |
| `ps51-install-preview.json` | `dae2249efc1c751559fd8cdf88de7790f78a62448afe3029a223eef7950bb1bd` |
| `ps51-install-preview-fixture/results.json` | `cce3b8f26750e4d4a68c5f858c9fd78e93131dd13cfc5deac78235b7de0d7e51` |
| `ps51-preview-native-controls.json` | `728fb676ea0fde3f8e4166559c8f69a59904fa3c3fd8184de2f4758f6fb1dfcb` |
| `install-entry-native-coverage.json` | `b4376a8be355fbbe298228e1d9a414eff5eb00b36f783858006ccfe5083df0fa` |
| `ps51-install-preview-fixture/actual-source.ps1` | `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e` |
| `ps51-install-preview-fixture/preview-child.ps1` | `af329ef1e97eb57d6e7d36875a6c752203f00f87a42e3c3bfe76434e22b46961` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/preview.before.json` | `e72e81d71f11a8c9ee76b09b82c8cc374731064869e481e6b1dbf016245a616d` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/preview.after.json` | `f059a5a70b270cdd1f3874b4d1e0af40498d72b8f4b2436c47caba4660fa525d` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/preview.launch.json` | `926f7e6f762d74637ca3a0cd974e89185396adb2dfdea5e1ac338d62bef4e5e1` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-baseline.before.json` | `f970bf57821f76e759d03ffb1234fa65a637d42044a1005ae9e7a4d04fff13b3` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-baseline.after.json` | `fb1ababa7780f2856b1853c2e6b2c2e3c6ef22c34b94f5566fa91536d86042c7` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-baseline.launch.json` | `bd98c641a4df23ca5545d4ad3818f337f2e17fb5e95acec9dbae850d758d364b` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-control/case.json` | `fe81ed5233be9d41c7a4f31abe92d9ebdcc3edbd8b1734c2c5baec887093f1a9` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-control/preview-ready` | `5716a62956de1f3d4c21b17b250852b940fb212bc5523a15b9f25c04b7b3f092` |
| `ps51-install-preview-fixture/helper-compiler-native-api-load-unicode-ص/host-control/child-result.json` | `979e08529253f4c0027030a577bab892cb72f9357df991d272c39fac94c20721` |
| `install-entry-native-coverage-fixture/ps51-github/entry-profile-window/profile-window.json` | `05c50c482d879a5d86321f861742c2b40681afc7412ea746c5de8edd3647073e` |
| `install-entry-native-coverage-fixture/ps51-github/host-only-control/profile-window.json` | `635d867b429474bbe0ebc0e17986a890c2fe5aa21a9b88edb9857349283c9c3c` |
| `install-entry-native-coverage-fixture/ps51-positive/entry-profile-window/profile-window.json` | `d8b80d0b819b27546f6abceaa9ff263a6f0abe3aa013f3860d17f4f24f99f2f3` |
| `install-entry-native-coverage-fixture/ps51-no-open/entry-profile-window/profile-window.json` | `ada56821745d1e5dbfa334491953d3400611cdf966b4b6dc096093cc71a7b506` |
| `install-entry-native-coverage-fixture/ps51-unreadable/unreadable-child-proof.json` | `f9d915fa45e8ff70a38380301d2d3032f01b28c7597b1c4ba3ee59e9d7b8bce3` |

### Retained variant identities

Each path below is `E/ps51-install-preview-fixture/mutants/<name>/install.ps1`. Each recorded and received hash agrees. Base source for every variant is `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e`.

| Name | SHA256 |
| --- | --- |
| `eager-staging` | `7429903e6fe513c0aae740c7fc8bbf8d7d0d4321416834e86a819a8a5b1c0f66` |
| `cleanup-in-preview` | `20146e54893ae47fd95d6cfee29af43f8b7d56b0401dd5636da1f07209af2245` |
| `cached-path-return` | `b1ee45c52f268797984b1676d98000fa2fb8ff0f89d583d7ee341db62d50d4e7` |
| `copy-success-when-suppressed` | `ca3914c03350d39376cea74284e33d3a7d4a73351fde844ce2877bb1cd2f1c34` |
| `copy-null-array-truthiness` | `2876c844de75bd8228edbfbcc48125d4387d080b9832363abe8fe934daeff552` |
| `clipboard-attempt-during-preview` | `04961e9d20e13196777b483bb01dc9d9b7d58759eb81462460760fd1d8df42ba` |
| `native-api-load-before-guard` | `42d3e7cc15b583c51bee039648d3c276300ce708b20665f557b0b9700a053f5a` |
| `swallowed-direct-transport` | `108c73dbe35f7a2c99831ff5300511dce147defb42aa30769a9b0227dae41df1` |

The representative core case path above binds product PID 4052 to `preview-child.ps1`, start `2026-11-11T14:26:13.4311616Z`, observed exit `2026-11-11T14:26:37.0002918Z`; complete sidecars retain the other 66 product and 67 baseline process identities. Full-entry PIDs are listed in the ledger. The report preserves the scope differences rather than inventing a single whole-contract native PASS.

Report state: FINAL
