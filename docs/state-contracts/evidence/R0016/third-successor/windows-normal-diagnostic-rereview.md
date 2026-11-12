# Windows normal-profile diagnostic corrected packet: independent engineering rereview

**Status: COMPLETE — bounded engineering rereview; no new finding within the assigned correction scope.**

The corrected receiver refuses the four original inconsistent packets and the additional tested association inconsistencies. The retained native receipts expose the fields and token bytes used by the correction. Every complete original FAIL/exit1 baseline remains `DIAGNOSTIC_ONLY` with `qualificationAccepted=false`, and retains the original row booleans and errors.

This report addresses the frozen correction and its compatibility with retained evidence. It provides no native qualification, acquisition permission, currentness decision, audit disposition, readiness, acceptance, or closure. Root owns the workflow review and shared source writes.

## Frozen inputs and independent execution

| Input | Exact identity |
|---|---|
| Corrected packet `SHA256SUMS` | `7f73e438542bc986a4449fe565963db86fb9bd281673dc09f72342925c7fb6f6` |
| Corrected diagnostic runner | 27,093 bytes; `0dbaa611c5c178983f79f24cdf25b1a5e33dee66f13201025d571baa5e42cb77` |
| Original independent report | `0b64e2b5b90efaae392f8c1b707b2394dfacbadd37c1e79264c34f1c57e1f787` |
| Original independent witness script | `3ad7695646f517a8b73425331a5230d3a25284e498701c90e6b181e65e878474` |
| Current outer helper retained in corrected packet | 45,698 bytes; `652848809fc581452e4bf48e2895786cd3c780e60e0a2c3091e2969d7b856616` |
| Root-supplied published base/tree | `a4c617ebeedfb507c0cb7a472683cce47ad62522` / `7f7aca595593db5014dd0932476c35a85eb8ba0c` |

All **194** files listed in the corrected packet manifest matched their declared SHA256 values. The original witness in the correction packet matches the independently retained original witness byte for byte. The corrected packet's outer helper matches the repository working copy read during this review.

The fresh independent command was:

```text
python independent_rereview.py > execution.stdout 2> execution.stderr
```

It exited **0**, reported **91 successful checks**, and left stderr empty. The seven original author inert tests also passed. `independent_rereview.py`, `independent-results.json`, `red-results.json`, `green-results.json`, `retained-native-bindings.json`, `author-inert-tests.txt`, and the execution captures retain the checks and exact outcomes. The independent command ran once, without a failed attempt or candidate correction. It refuses to overwrite existing replay directories.

## Findings and dispositions

| Item | Evidence | Impact | Narrow countermeasure | Disposition |
|---|---|---|---|---|
| Original missing product raw capture | The original witness's exact removal of `entry-profile-window/stdout.raw` is accepted by the repin-only runner and refused by the corrected runner with a missing-file error. | Previously, the receiver could describe a complete nested capture whose actual file was absent. | Verify the declared stdout/stderr facts against each exact owned capture path. | Addressed by the reviewed correction. |
| Original changed warmup raw capture | The exact changed warmup stderr witness is accepted before correction and refused with `File path/size/SHA differs` afterward. A separate missing warmup stdout control is also refused. | Previously, warmup evidence could contradict retained raw bytes. | Apply the same exact raw-fact binding to both product and warmup. | Addressed by the reviewed correction. |
| Original detached nonce and readiness associations | The exact detached receipt nonce witness and 11 additional readiness/path/environment controls are refused; the earlier runner accepts them. | Previously, nested identity, tokens, launch environment, or owned path could disagree without refusal. | Bind receipt PID/nonce, observation nonce, launch environment, owned ready/ACK paths and actual bytes; require four distinct nonces per mode. | Addressed for the tested association edges. |
| Original detached product `fullReady` | The exact null product `fullReady` witness is accepted before correction and refused with `Product full-ready receipt differs` afterward. | Previously, an original product receipt could disagree with the independently loaded ready inventory. | Require exact equality with the separately loaded product-ready inventory. | Addressed by the reviewed correction. |
| Retained historical warmup inventories | The eight retained c10/c11 receipts contain the new binding fields, but the four historical warmup receipts have no `fullReady`; the original harness did not supply `full_root` for warmup. The diagnostic's unchanged derivation supplies `root` and adds full before/after inventories. | Historical fullentry artifacts do not constitute a complete run of the six-entry diagnostic. The diagnostic's new warmup full inventories and timing remain prospective. | Keep this distinction in any later native disposition; collect the already planned diagnostic evidence through its authorized execution path. No additional author change is identified here. | Compatibility limitation retained; no correction-specific blocker found. |

The additional readiness/path/environment controls are: detached PID; detached environment nonce with launch kept consistent; detached observation nonce; wrong ready bytes with a refreshed valid fact; wrong ACK bytes with a refreshed valid fact; ready fact redirected to ACK; ready and ACK declared as the same file; ready path outside its case while retaining valid bytes; direct launch environment differing from its receipt; warmup nonce replaying its product nonce; and warmup nonce replaying another case's warmup nonce. These controls exercise the new association checks without changing product predicates or introducing acquisition variants.

## Original witnesses, negative controls, and positive controls

The independent script executes the original witness script's exact fixture-construction prefix and exact four mutation bodies, taken from the hash-bound original file. It refreshes the report, envelope, capture facts, and process receipt through the original `refresh()` function. A stale outer digest therefore does not mask the association under examination. All test data under `red/` and `green/` are synthetic and are not native observations.

| Control group | Repin-only receiver | Corrected receiver |
|---|---:|---:|
| Four exact original inconsistent packets | 4 accepted | 4 refused |
| Twelve additional inconsistent packets | 12 accepted | 12 refused |
| Valid UTF-8 BOM on both ready and ACK, with matching facts | Accepted | Accepted |
| Reused PID with independent nonce and corresponding tokens/facts | Accepted | Accepted |
| Complete original FAIL/exit1 before and after each additional control | Original FAIL retained | Original FAIL retained |

There are **16 negative association controls** in total. Each corrected refusal has a recorded error consistent with the changed association. Positive controls confirm that the patch does not impose permanent PID uniqueness or reject the existing UTF-8/BOM convention. Every accepted control remains diagnostic-only and preserves qualification rejection.

The original status checker remains unchanged. The author tests also verify refusal of inconsistent FAIL/PASS/envelope/exit combinations and incomplete Job lifecycle receipts. A successful execution of this inert verifier means that the controls behaved as expected; it does not convert an original product failure into a passing product result.

## Retained native compatibility and token semantics

Read-only inspection covered PS5.1 and PS7.6.6 positive/no-open cases, c10 and c11, under:

```text
work/candidate_receiving_restored/native-after-acl/{ps51,ps766}/files/installer-evidence/f/*/
```

All **eight product/warmup receipts** have a positive integer PID, a 32-lowercase-hex nonce, the matching environment nonce, `ready=true`, the expected `readyToken`, raw stdout/stderr facts, and ready/ACK facts. The **32 referenced raw or token files** match their declared byte counts and SHA256 values. Ready and ACK are distinct owned paths. All four nonces in each host's two inspected cases are distinct.

Every inspected ready/ACK file consists of the exact UTF-8 bytes for `str(pid) + "\t" + nonce`, without a BOM or trailing newline. This matches the fixture's PowerShell `[IO.File]::WriteAllText` token writer and Python UTF-8 ACK writer. The new receiver's `utf-8-sig` decoding therefore agrees with observed bytes and its existing direct acquisition reader. An independent synthetic BOM-positive control confirms the explicitly retained BOM allowance.

For all four product receipts, `fullReady` equals the independently loaded `entry-profile-window/full-at-ready.json`; the standalone receipt equals the report's `profileWindow`; its nonce equals the observation nonce; and `direct-launch-inputs.json` equals the report's launch data and has the same environment as the receipt. Each historical warmup receipt likewise equals the report's `hostOnlyBaseline`.

The independent script also invokes the **actual corrected `bind_nested_evidence` function** on copies of these eight receipts. It first verifies the original Windows path/fact associations using `PureWindowsPath`, then translates only ready/ACK environment paths and the four fact paths in memory to the local extracted evidence locations. The original token and capture bytes remain unchanged. All eight invocations succeed. This demonstrates field and byte compatibility with retained native evidence; it does not execute or emulate Windows path resolution, launch a process, or receive a complete future diagnostic packet.

The historical original failures remain intact:

| Retained host/cases | Original adverse result |
|---|---|
| PS5.1 c10 and c11 | `analysisCache` changed undeclared owned input fields. |
| PS7.6.6 c10 and c11 | `USERPROFILE` changed outside the one validated new bundle. |

No inference is made that no-gather will prevent the PS7 write, that the 20-second warmup will materialize the PS5.1 cache early enough, or that a default outcome will reproduce. Those questions require the authorized native diagnostic and its original strict outcomes.

## Scope, comparators, outer binding, and lifetime

Independent AST comparison confirms the diagnostic changes only the `INPUTS` outer-helper pin and `receive_mode`, and adds `bind_nested_evidence`. Every other function and other top-level construct is AST-identical. The inherited proposal files other than the explicitly repinned outer helper are byte-identical. The three derived harnesses remain byte-identical to their original frozen versions.

The scope therefore remains exactly six genuine normal entries: PS7 default positive/no-open, PS7 no-gather positive/no-open, and PS5.1 warm20 positive/no-open. No cache exclusions, product effect suppression, state normalizations, new scenarios, or product comparator changes were introduced. The strict normal pre-ready profile, retained-bundle/effect, full-profile, and complete-input comparisons remain in their inherited harness.

The outer helper changes only `INPUTS` and `validate_report` relative to its historical version. All other function/class definitions, constants, and top-level constructs are AST-identical. The diagnostic does not call `validate_report`; its generic builders, readers, fact verifier, selected direct receiver, and phase helper remain unchanged. The current outer pins agree with the diagnostic's declared installer and product-support inputs, as verified by the passing input-pin test.

The diagnostic's main acquisition, archiving, platform guard, mode deadline, and custody logic are unchanged. The fixed six-entry plan, 480-second outer mode bound, inherited 60-second child bound, suspended/assigned Job carrier, exact genuine `-NoProfile -File` commands, source-free control body, and failure disposition retain their prior definitions. This review does not requalify Windows timing, Job operation, filesystem/network containment, or archive workflow behavior. Root reviews the workflow separately.

## Execution boundary and handoff

Only local Python source/data checks and reviewer-owned file creation ran. The replay installs a process/network-denying audit hook. No PowerShell, installer, native probe, network probe, workflow, publication, Git mutation, source author correction, or additional agent was used. All reviewer output is confined to `work/windows_diagnostic_rereview_g19`.

The report began `PARTIAL` and is now terminal for the assigned engineering rereview. `SHA256SUMS` binds the final report, independent verifier, execution captures, results, and synthetic replay files. Root may assess this evidence within its existing authority; no broader authority is asserted here.
