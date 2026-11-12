# R0016 source-free Windows entry driver — bounded diagnosis and candidate 3

## Disposition

**The original diagnostic remains FAIL. Candidate 3 is a two-file scratch proposal awaiting independent review and native qualification.** It explicitly enters the owned Utility module on the held route and records both sides of strict native file-fact comparisons. It does not normalize paths, relax equality, omit snapshot fields, change the installer, or grant product acceptance.

The original failure artifacts were re-received after runtime restoration. Their complete bytes, extracted members, metadata, and full lifecycle inventories remain in this packet. No archived program, PowerShell host, installer, or native product matrix was executed in this lane.

## Original evidence and exact source association

Actual GitHub API records identify run `43140174110`, attempt 1, at commit `20f5db018ff6f7b41ff0c8c41fad90aeaeb142e5`, with two failed native jobs. Each downloaded ZIP matches its exact API size and SHA-256; ZIP and complete gzip CRC checks passed. Only regular files and directories were extracted, with no traversal, duplicate normalized name, link, or special member admitted.

| Host | Artifact ID | ZIP bytes | ZIP SHA-256 | TAR members / regular files |
| --- | ---: | ---: | --- | ---: |
| PowerShell 7.6.6 | 13909521234 | 275,096 | `dcd1fa790c86ef683fed64f12426de51def1d8d48e2db4d1d6fc337aad9eb37a` | 162 / 85 |
| Windows PowerShell 5.1 | 13909127960 | 177,876 | `291a2ff5d69e3cd9b89350d6e202f195ca9b6c4044e259ac1a58ea9c7e603a1d` | 142 / 70 |

TAR.GZ hashes are respectively `9b8f89658f7ff60a6d097c593bbcb4301df95242102df6091c9d1e88a10c66bf` and `6787af6f29798a9172ab866b01b581f911828166d9bab69f7dbc500ec40e4ec8`. All 155 original regular files are retained; nothing was excluded by filename. The two original inventories preserve member paths, types, sizes, modes, timestamps, and hashes.

The eight restored published candidate-2 inputs were compared byte-for-byte against the retained inputs in both original native artifacts. All agree. `input-custody.json` records every original input identity and restored source path. The new proposal was authored from those restored source files; the archived copies were read only as data.

## Actual first-pair failures

### PowerShell 7.6.6: the owned Utility startup was never entered

The original direct neutral child, PID 960, has exit 0, genuine PID/nonce ready and ACK files, empty stderr, and the two expected output lines. Its full receipt has no error.

The held child, PID 1840, also exits 0. Its before/after invocation signals and acknowledgements are complete; its result reports `fallthrough`, `entryExit=0`, no preparation error, no source exception, and an established deny guard. The complete held-before and held-after inventories are exactly equal, and events/stderr files are empty. These are retained raw observations, not a qualified composition result.

The controller correctly rejects the held receipt with **`Original Utility ready/ACK was not independently completed`**. The original artifact lacks all five corresponding held startup files: `ready`, `profile-ack`, `bootstrap-phases.txt`, `control/module-inputs.json`, and `control/full-at-original-ready.json`. The held receipt has no `originalReadyAcknowledged` or startup inventory. `neutralComparison` remains null and the remaining nine diagnostic cases were not run.

The source explains that missing path. The held driver uses `New-Object` and `ConvertFrom-Json` during its own preparation, has no explicit import of the private Utility module, and installs its local guard `Write-Host` before invoking the source-free body. The actual held probe identifies the native Utility module. Consequently the body does not trigger the private wrapper's `Write-Host` autoload path that the direct neutral used. The wrapper's original startup handshake is therefore absent. The parent's separate original-ready polling/ACK loop already exists and is unchanged; this is not a missing-parent-ACK-loop defect.

### Windows PowerShell 5.1: the missing evidence is the parent readback

The top-level failed row is labeled `fallthrough` and names a held fixture, but the actual failure occurs earlier in **direct neutral post-exit proof validation**. The direct child, PID 5864, exits 0, has genuine ready/ACK evidence, empty stderr, and the two expected output lines. Its retained direct receipt records **`AssertionError: Unbound actual read module/assembly file`**. The held child never starts, and the top-level `directNeutral` remains null because the validator raised before returning its value.

All four child-reported command bindings contain module and assembly file facts. The rejecting expression compares each complete child fact with a fresh `c.fact(path)` result. The original producer did not retain that parent result, the failing command/field name, or the differing values. Thus the native record establishes an equality rejection but **does not establish which field differed or why**. Path spelling, length, hash, or another readback discrepancy must not be selected by conjecture. Candidate 3 leaves that equality unchanged and adds the missing evidence.

## Two-file proposal

| File | New bytes | New SHA-256 |
| --- | ---: | --- |
| `tests/install-entry-driver-diagnostic.py` | 49,138 | `c5f0d9cf62f4557ef8f838a08dc4c402f791076842b0c69e84bfb773020e458c` |
| `tests/install-entry-held.ps1` | 8,262 | `742b42edd3828ec98dc25f717fdbacbd3e68ed877139c90e358d43f7c5142ca2` |

All six other inputs remain exact. `candidate-inputs.json` lists all eight identities, and `candidate.patch` is the complete two-file diff.

The held driver now derives the exact manifest path from the already mapped owned subject root: its parent contains `modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1`. It imports that explicit manifest after the existing spec/input checks and definition-only probe load, and before installing the recovered source guards. This avoids reliance on a later command-name autoload. The import uses local scope without `-Force`, so it does not deliberately repeat an already loaded wrapper. The module bytes, manifest, and probe remain prepared inputs in the full retained inventories; the unchanged wrapper carries the startup probe and PID/nonce ready/ACK protocol.

This preparation change applies to the held driver's existing scopes, including a future product-preview caller: the owned wrapper is now explicitly imported instead of being entered only if command resolution happens to select it. It does not change the genuine direct `-File` launch, wrapper module bytes, guard definitions, typed parameters, normal/NoOpen controls, source-free bodies, deadlines, or cleanup implementation. The product branch remains unqualified; the new held-driver bytes need the separate source-free diagnostic before product admission.

The diagnostic controller now saves `control/read-file-bindings-<phase>.json` for each actual proof phase. Each comparison preserves the original child fact, fresh parent fact, exact equality result, differing field names and both values, and any parent read exception. The journal binds phase, PID, nonce, source, and probe. A failed read or mismatch is recorded before the existing rejection is raised. There is no path normalization, case folding, missing-field default, exception-to-PASS conversion, or altered byte/hash criterion. A journal write failure also fails the diagnostic; when it coincides with a read/binding failure, both error descriptions are retained in the raised failure.

The original readiness checks were moved unchanged into a small callable receiver so they can be exercised with inert owned files. `validate_terminal` still calls those checks and still requires the startup inventory plus both invocation gates. All other pre-existing controller function ASTs are unchanged except the two callers needed for these changes.

## Full lifecycle evidence retained

`lifecycle-deltas.json` retains every differing physical row with its full before/after values. No field or cache-named path is filtered.

| Original host / interval | Differing rows |
| --- | ---: |
| PS5.1 direct prelaunch → ready | 5 |
| PS5.1 direct ready → post-exit | 0 |
| PS7 direct prelaunch → ready | 6 |
| PS7 direct ready → post-exit | 2 |
| PS7 held prelaunch → before invocation | 6 |
| PS7 held before → after invocation | 0 |
| PS7 held after invocation → post-exit | 2 |

The original startup additions and post-exit `StartupProfileData-NonInteractive` observations remain in the complete native files and these deltas. The missing held startup phase is not manufactured. The whole held-before/held-after equality remains unfiltered in candidate 3. No full prepared-clone equality waiver or new product input-association claim is introduced.

## Verification actually performed

`python -B receive_originals.py` completed with exit 0 for both originals. It performs bounded archive/data receiving only.

The focused test was written before the repair. `python -B test_bounded_repair.py before` returned exit 1: six expected evidence-retention failures and nine passing readiness controls. The original equality predicate already rejected mismatches, but it did not write the child/parent comparison evidence. Those original results are retained in `tests-before.json`.

After the change, `python -B test_bounded_repair.py after` returned exit 0 with **15/15 passing inert controls**. They cover an equal fact; exact path, byte-count and hash mismatches; missing-file and reparse refusals; a genuine ready/ACK; missing/false acknowledgement; wrong PID; replayed nonce; stale ACK bytes; forged ACK fact; missing ready file; and rejection of the actual original incomplete PS7 receipt. The Windows readback is an explicit data double because this lane is not on that native host; the acknowledgement files are real owned inert files. Only selected pure receiver function definitions are compiled, never a whole archived module or native launcher.

`static-review.json` records Python syntax checks, the exact two-file diff, unchanged remaining input bytes, placement of the explicit owned import before guard installation, and preservation of full snapshot/gate checks. This is static evidence, not a PowerShell parser/runtime test. No full project/native/product suite was run: that would exceed this explicitly bounded source-free authoring lane and could execute installer code. No historical driver review or native PASS is claimed for these new bytes.

## Smallest next native discriminator

After independent review, the root can publish these two input changes through the reviewed source-free route and rerun its existing PS5.1/7.6.6 diagnostic once. Keep the existing first-neutral-pair stop condition and execution/time limits: at most eleven diagnostic executions plus the separate cold version probe. On PS7, first require the newly observed original Utility startup probe, ready/ACK and full startup inventory, then both invocation gates and complete unfiltered held equality. Only a valid neutral pair allows the remaining five semantic cases and four guard controls to continue.

On PS5.1, a renewed strict rejection can be a useful diagnostic outcome: receive the exact new child/parent comparison journal and use its actual differing field values to determine the next correction. It is not a product PASS, and this proposal does not predict that PS5.1 will be admitted. Preserve both failed originals and all new startup/post-exit deltas. Do not dispatch the twenty-case product matrix until the exact new driver is qualified and the other product prerequisites are satisfied.

The root remains the sole shared-source writer and publisher. This lane made no installer/shared/branch/policy/ACL changes, no remote mutation, and no native dispatch.
