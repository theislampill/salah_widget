# Independent native Mac product receipt

Disposition: **PASS for receipt integrity and the retained native Mac product observations, with the measurement gaps below preserved.** This is not whole-R0016 acceptance, publication approval, or issue closure. No archived code was executed, and this reviewer changed no shared source or external state.

## Original artifact and source custody

Run **43124486557**, attempt **1**, completed on the owner branch at commit **`f8d3db2d6d6d84f63bf8d79cf52c6977558cb105`**, tree **`1b606fc515e5391d6b54ed4bdbaeb88475bcf9b5`**. The original run and artifact API bodies join the exact workflow `.github/workflows/installer-preview-macos-native.yml`, head, run, artifact ID and digest. Their success labels were not used as substitutes for the retained product observations.

| Retained input | Identity |
|---|---|
| Artifact | `13903125749`, `r0016-native-Darwin-43124486557-1` |
| Original ZIP | 1,357,988 bytes; SHA256 `c9a1ec04d1db303a2210b93c417eff1facd6aecee40e3dd7445f1eebc4195b4c` |
| Original inner TAR.GZ | 1,457,024 bytes; SHA256 `55ffb56be7d6c343ada38c840aa5b52de33158c5eab2ef074f5fa17589dc99e0` |
| Actual frozen installer | 44,673 bytes; SHA256 `d19ed5d90e1faf0d9ac66415814a3a68e28c6ae61730acd4eaef1b9588830cc5` |
| Recorded preview fixture | 59,830 bytes in published source; SHA256 `0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00` |
| Published native collector | SHA256 `9732e7687ced927be21bdca8f9fae08e29c7104d0119fe435ea74dcc86a1a46f` |
| Published native workflow | SHA256 `eaaea01410c8ed9a3733a110c756edd33d7c045afd6987f929b59f5429b89e62` |

The original ZIP CRC and API digest match. All **3,339 TAR members** were inventoried: **1,490 regular files, 1,842 directories and seven symlinks**. Regular payloads total 6,458,493 bytes. Every regular member was independently hashed and compared with its extracted copy. No duplicate, traversal or unexpected special member was accepted. Symlinks were retained only as metadata; no archive links or code were executed.

All **34 source hashes claimed by the native collector** match exact Git blobs at the published commit. The frozen installer retained inside the original fixture also matches the independently reviewed C2 product byte for byte. The recorded fixture hash matches the reviewed C2 fixture and published Git blob. The native runner did not separately retain its executable fixture file, so that part of the binding uses its in-run hash and exact published source; the product bytes themselves are retained.

The main `install-preview.json`, its original stdout file, and the fixture's `results.json` are byte-identical. Their original raw classification is **46 PASS, zero PRODUCT_ASSERTION_FAILED, zero BOOTSTRAP_BLOCKED**. These are instrument rows, not a claim that the separate 46 overlapping contract obligations have all closed.

## Native environment and full command groups

The original acquisition records identify **Darwin 24.6.0, macOS 15.8.2, arm64, Apple `/bin/bash` 3.2.57, UID 501/GID 20, APFS**, image `20261104.0514.1`. Host facts from `uname`, `sw_vers`, `stat`, filesystem and volume acquisition all returned zero. The observer ran Homebrew Python **3.15.2** at `/opt/homebrew/opt/python@3.15/bin/python3.15`; this observer is distinct from the Apple Python selected by product discovery.

All nine original command groups have an actual zero terminal status, an empty retained stderr stream, a parsed original stdout receipt identical to the collector's saved JSON, and successful fixture copying. Each completed below its original 240-second collector budget. These overlapping groups are reported separately:

| Native group | Retained rows | Elapsed collector interval |
|---|---:|---:|
| Bash component/guard cases | 26 | 6.824684 s |
| Complete entry/plain/PTY cases | 25 | 7.106626 s |
| Discovery parser/builder/caller cases | 76 | 9.999106 s |
| Native detector cases | 12 | 1.590534 s |
| Discovery mutation campaign | 13: healthy receipt plus 12 mutants | 14.240611 s |
| Original mutation pairs | 8 | 12.298970 s |
| Builder cases | 4 | 0.302690 s |
| Native staging cases | 9 | 5.002479 s |
| R0016 preview campaign | 46 | 19.885197 s |

The R0016 result retains **one bootstrap, 12 helpers, 18 entry cases, seven interface cases, two normal controls and six causal mutations**. Every earlier 45-row case name and kind remains in its original relative order. The sole additional row is `whole-entry literal zero-target refusal`.

## Containment and readiness evidence

All retained R0016 sandbox profiles are identical. They deny network operations and file writes outside the owned fixture, allow the exact terminal devices required by the reviewed native adapter, and deny actual `open`, `pbcopy` and `osascript` execution. The subject fixture still uses `PATH=/usr/bin:/bin`. The published preview function removes subject `PYTHONDONTWRITEBYTECODE`, leaving bytecode suppression to the product's `-B` invocation. No PATH mask or host-policy relaxation was introduced.

The original kernel control, PID **23749**, records a successful owned write, two outside-write denials and TCP/UDP denials, each denied call reporting errno 1. The command-denial control retains its `mkdir` attempt, denial diagnostic and unchanged subject snapshot. The missing-readiness and wrong-nonce controls both retain the intended `BOOTSTRAP_BLOCKED` outcome; their failure is not converted into product qualification.

The separate native PTY control retains the exact sentinel bytes `native terminal control\r\n`. Child **23755** exited zero, was reaped, and its master was closed. Ownership was not lost, no cleanup signal was sent, and no error was recorded. Its retained monotonic elapsed time is **0.001524917 seconds**, within the 25-second natural-completion deadline and 30-second outer ceiling.

The bootstrap's targeted log query is an explicit **ACQUISITION_GAP**: two completed 1,020-byte stdout acquisitions, empty stderr, and no network-denial message attributable to PID 23749. Both retained captures match their recorded lengths and SHA256. This differs from the earlier source-free Python diagnostic's log result; the earlier result cannot be imported into this run.

## Healthy preview observations and the repaired behavior

All **37 healthy helper/entry/interface observations** join their original observation files, raw stdout/stderr files, readiness PID records, empty effect event streams, and unchanged snapshots. Global native `transportAttempts` remains **null**, never a manufactured zero. The actual pipe case retains both outer and installer Bash readiness identities.

Every one of those 37 healthy stderr captures is free of the Apple cache-error patterns that exposed the prior defect. The GitHub, store, ask, NoOpen GitHub, NoOpen store, advertised pipe and missing-preset captures all contain a useful `Would prepare Firefox / r0016-known.` plan. Mixed unknown and parser-unavailable cases keep Firefox held while preserving the independently eligible Chromium peer. The result therefore does not depend on declaring all Firefox discovery unavailable.

The no-profile outcomes remain distinct:

| Case | Actual retained result |
|---|---|
| Ambient applications, no profiles | Exit 1; three application-only targets held; `0 eligible, 3 held, 0 refused`; exact held diagnostics and eligibility refusal; no useful-plan/success claim |
| Literal absence | Exit 1; no discovery rows after the detection heading; exact `No supported browser profiles or installs were detected` error |

The ambient no-profile case retains the original discovery spies unchanged. The literal absence case adds only the six exact browser executable lookups reviewed in C2. Its instrumentation does not deny the physical developer Python path.

All 12 direct helper probes retain their intended result contracts: suppressed artifact helpers return no usable path and fail, clipboard suppression returns failure, cleanup is an empty no-op, and the opening helper returns only its dry-run diagnostic. Their driver prefixes match the exact frozen product source.

The actual post-trap failure, INT and TERM cases retain exit **97, 130 and 143**, respectively. Their PID/nonce boundary records agree with readiness, and the actual EXIT/INT/TERM traps are present. The captures claim no completed preview or install, and their subject snapshots remain equal.

## Snapshots, normal controls and negative preservation

The artifact contains **46 original snapshot pairs**. Forty-five pairs are equal; the only unequal pair is the intentionally faulty direct-transport mutant. Every final snapshot was reconciled against the original TAR member names, modes, kinds, content hashes and link metadata. The one documented observer mode restoration is preserved: unreadable metadata is observed as mode 000 during the subject and restored to 600 afterward using the parent's held descriptor. That restoration is an observer action, not a preview write attributed to the installer.

The contained real normal caller exits zero and retains **28 effect events**, including four browser openings. NoOpen exits zero and retains **24 effect events**, with zero browser openings. Both still reach metadata, download, staging, clipboard and cleanup calls; both consume the menu and two later confirmations through a real pipe/PTY. Their retained bundles contain the configured preset, Firefox XPI and Chromium unpacked manifest, while owned download scratch is absent afterward. Six mutant normal companions also complete zero with 24 NoOpen events each. These are controlled manual-install preparation observations; they do not prove a real browser installation or import.

The original plain/PTY entry campaign retains its refusal cases: no controlling terminal, PTY EOF, invalid token, unknown index and legacy-only selection all exit unsuccessfully before effects. Their original event files and readiness records agree with the receipts, and no retained-install completion claim appears.

All six R0016 mutant files were reconstructed independently from the exact product bytes and the source-declared single mutation. Their intended failures remain causal:

| Mutant | Retained discriminator |
|---|---|
| Eager initialization | Actual intercepted `mkdir` attempt |
| Preview cleanup | Actual intercepted removal attempt |
| Cached path return | Suppressed helper reports success and returns the cached path |
| Suppressed-copy false success | Suppressed helper reports success |
| Clipboard attempt | Four actual intercepted clipboard command attempts |
| Swallowed direct transport | Exact PID-matched native network-denial event despite zero process exit |

For the direct-transport mutant, stderr names subject PID **28430**. Its separate complete native log capture is **1,013,953 bytes**, SHA256 **`61f39d2be83a74c0ad0474d3ca21d220a690ec218565da8763c1235cfaa154b6`**. Recomputing attribution from the original capture yields exactly the retained `Python(28430) deny(1) network-outbound remote:*:9` event. The subject exited zero and emitted no command-spy transport event; the targeted native evidence therefore supplies the intended independent negative discriminator.

That mutant also retains **two denied xcrun cache-write diagnostics** and an unequal snapshot: **15 directories and 26 files** were added under its owned `HOME/Library/Caches/com.apple.python` tree. These are actual additional mutant effects, not erased host noise and not healthy-product behavior. The targeted network record still establishes the reported transport rejection boundary before the snapshot assertion. Its normal companion remains healthy because the injected behavior is dry-run guarded.

All **eight original mutation pairs** retain syntax success, a zero-exit healthy companion, the required named adverse assertion, and fixture exit 1 for the mutant. Their original raw receipts and mutant bytes match their recorded hashes. All **12 discovery mutants** retain the exact required failed-case sets and all three healthy controls. The separate healthy discovery mutation baseline contains its source-selected **21 cases**; the full discovery command group separately contains 76. Neither denominator is substituted for the other.

## Measurement gaps and bounded disposition

The following limits remain material to truthful use of this evidence:

* **Global attempt telemetry is unavailable.** Healthy null transport fields, empty command events and unchanged snapshots do not prove that every possible syscall attempt was absent. The bootstrap targeted-log gap remains a gap. The direct-mutant PID-matched result is a separate, narrow positive observation.
* **Snapshot scope is explicit.** The retained preview snapshots cover fixture names, kinds, modes, file bytes and links. They do not record timestamps, transient write-and-restore activity, all host state, or all runtime caches outside that fixture. The independent outside-write control is represented by its actual denial readout and in-run assertion; its separate outside directory is not included in the copied fixture archive.
* **Lifecycle detail varies by instrument.** The native bootstrap PTY has explicit monotonic timing, reap, ownership and close evidence. The collector records all nine terminal status/time intervals. The ordinary product cases use reviewed 30-second subprocess budgets, normal companions use 60 seconds, and the inherited PTY loop has a 20-second budget. Individual product-case monotonic terminal timestamps and a complete surviving-process-tree census are not retained. No claim of complete process-tree residue absence is made from suite completion alone.
* **Captures are retained text representations.** Product subprocess output is decoded by the harness, and collector output is decoded as UTF-8 with replacement. Native log receipt metadata correctly describes its re-encoded UTF-8 representation. Archive hashes prove these exact retained bytes, not universal identity with original kernel pipe bytes.
* **The physical Apple interpreter is not directly recorded in this product run.** Reviewed source selection, fixed PATH, useful Firefox parsing and the absence of retained cache errors support the repaired behavior. They do not supply a newly observed physical executable hash. The earlier five-case source-free Python comparison retains its own separate host/run binding.

All **354 independent data checks passed** after resolving the reviewer's initial mistaken assumption that the discovery-mutant healthy subset had the full campaign's denominator. The exact source defines that subset as 21; no product, fixture or original evidence was changed. Verification code and all comparisons are retained in `verify_received.py` and `verification.json`; original archive metadata is in `archive-receipt.json`, and source joins are in `published-source-receipt.json`.

This receipt supports the current-source native Apple observations described above and preserves the prior failures and negative controls. Hosted Linux, Windows, cross-platform integration, delivered/merged bytes, owner approval and all remaining whole-contract gates retain their own separate status.
