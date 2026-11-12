# Independent Windows carrier route review — candidate 1

Report state: FINAL. Disposition: **GAP-REVISE**.

This disposition covers the new Python acquisition route and its GitHub workflow as a bounded, source-free ten-control qualification instrument. It grants no installer, native execution, whole-contract, publication, dispatch, or lifecycle acceptance. No PowerShell, installer, native Windows process, or workflow ran during this review. The previously reviewed standalone carrier's bounded code disposition and the separately blocked Windows receiver remain separate records.

## Independence and authority

Reviewer: `/root/independent_review`. Requested model: inherited parent model; no override requested. Actual model: host-declared GPT-6 Astra Pro; a more specific provider deployment identifier is not exposed. `authoring_context_reuse: no`.

I did not author the route, workflow, carrier, recovered producer/libraries, or helper. I inspected actual source before reading the route author's report. The four counterexamples below were constructed and replayed before reading the author's independently found child-arguments adverse. All writes and replay fixtures are within my own `/tmp/r0016-third-20261111/work/independent_review` directory. I made no shared-source or Git changes and exercised no publication or execution authority.

## Exact packet received

Original packet: `/tmp/r0016-third-20261111/work/windows_recovery/rootroute/frozen-route-1`.

The manifest SHA256 is `a03942c6717af7f0be6cb9ef0432e0762313e576e661f2c2fc4d73f4f06f2885`. I verified all **11 payloads, 75,682 bytes**, then copied them into `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/packet` before running tests that create fixtures beside themselves.

| Input | Bytes | SHA256 |
| --- | ---: | --- |
| Proposed `installer_preview_windows_carrier.py` | 20,475 | `5736a88cbb2cb5a6e869961c2feec8434573efb487376b10d394afc3496152f0` |
| Proposed `installer-preview-windows-carrier.yml` | 3,697 | `889a51a968a2a2291d3117ada06e0e7b084164fca8d6a7f8b0977f910b7ea4b2` |
| Unchanged `installer_preview_host_probe.py` | 16,807 | `6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df` |
| Author report | 8,788 | `0ff66855c847a77bbacf4ab9ad1729cce73d8a8136fa5c4db08f408c7c105555` |

The route refers to the previously reviewed exact carrier `733ff1ebc15b6e83e319313c33cbf67a888763a27388155d52ebe0e7c0497e04`, producer `e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916`, acquisition library `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1`, and window library `05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83`. It does not import the blocked receiver `851cf29917ed0ced30e7ebd1195f49de430b6f5bdf02d7fbc1643ce8af9889df`.

Receipt: `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/receipt.json`, SHA256 `57c1ba9341e44e58551c55564577aefcf44449b6b51e9ea89edca03f0ff8e622`.

## Concrete finding WRT-01 — child command arguments are not admitted

**Severity: P2.** In `validate_controls`, the raw launch receipt is read and its host, nativeFile, PID, nonce, and budget are checked. The nativeFile field must equal the verified retained embedded-driver path and the process receipt's nativeFile. The validator never checks the raw launch's `arguments` field. The outer process command is correctly checked; this gap concerns the inner child command.

The actual full `validate_acquisition` API accepted each of the following internally contradictory synthetic receipts after I refreshed the raw launch file fact, complete report fact, and outer stdout capture fact:

| Case | Mutation to one child raw launch | Expected | Actual |
| --- | --- | --- | --- |
| Healthy baseline | All ten commands bind the retained driver | Accept | Accept |
| Carrier missing arguments | Delete `arguments` from one carrier launch | Reject | Accept |
| Carrier wrong command | Set arguments to `-NoProfile -Command "Write-Output wrong-entry"` | Reject | Accept |
| Guard missing arguments | Delete `arguments` from one guard launch | Reject | Accept |
| Guard wrong command | Set arguments to `-NoProfile -Command "Write-Output wrong-entry"` | Reject | Accept |

The actual argument strings are fixture data; none was executed. The unchanged nativeFile assertion is insufficient to join a claimed driver to the command recorded in the same receipt. The defect permits false acceptance of contradictory evidence; this review does not claim that the maintained launcher actually issued a wrong command in a native run.

Independent result: `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/independent-inner-command-binding.json`, **3,915 bytes**, SHA256 `e523d216e4f6f5c5bbae8727cefaa244aa11e1f2606099e9a98de39fa3b71092`.

Every complete synthetic case is retained under `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/packet/validation/cases/independent-<case-name>`. The result JSON records exact report paths and hashes. For example, the carrier wrong-command report SHA256 is `d64c07968d1d45175afa1936243c8499675a6c4fd324d123f133c1703d7f6016`; the guard wrong-command report SHA256 is `6551cc01d4ba6e188312fe70a146a58c607b1eac48035557ccc36929e5accaa0`.

Required bounded revision: compare every carrier and guard raw launch's arguments against the exact maintained command constructor for the verified retained driver, rejecting absent, non-string, or different arguments. Preserve the healthy case and all four rejected-case discriminators. This does not require changing the previously reviewed PowerShell inputs or adding installer execution.

## Other reviewed boundaries

The exact helper and route construct a 600-second outer process acquisition, with a suspended process assigned to a kill-on-close Job Object before resume. The terminal validator requires integer zero exit, explicit true exit observation/assignment/closure, false timeout, null error, exact outer command, positive integer PID, and finite elapsed time no greater than 600 seconds. It verifies direct stdout/stderr file facts before parsing one complete JSON object. Duplicate keys, trailing objects, nonfinite JSON values, Boolean numeric substitutes, and incomplete capture facts are rejected by exercised checks. Job Object management supplies process lifetime control; it is not a filesystem or network sandbox.

The route's original and retained input associations require the exact four unique roles, owned paths, lengths, and SHA256 values. Report and envelope host, fixture, version, expected-host selector, and input associations are joined. Ten unique named control cases are required, with owned distinct case paths, host/PID/nonce association, typed child terminal fields, 60-second budgets, and both drains. The WRT-01 omission is the concrete remaining command association gap found in this review.

The unchanged helper prepares an allowlisted environment before startup, including owned home, temporary, AppData, cache, and module locations and explicit telemetry/first-run settings. The route requests the default gather behavior (`False` for the helper's no-gather option), rejects the added gather override, and sets the update-check opt-out before startup. No execution-policy override is added. Full outer-state snapshots remain evidence and are not made equal through exclusions or reclassification.

The workflow has two Windows 2022 jobs, `ps51` and `ps766`; the latter maps to carrier expected-host `ps7`. Its selected release ZIP URL and declared SHA256 `02fe458be20493fbdf43f61ea20610b811ee6c738ab1676c61b9cfcd1a33c860` are bound in the source. This review did not download the runtime. Its non-cone sparse checkout names exactly two Python and four PowerShell files and omits installer source. Checkout and upload actions are pinned, credentials are not persisted, and Git autocrlf is disabled. Acquisition and launch run through cmd/Python before the selected PowerShell host. The always-run archive/upload path preserves the owned root; the archive implementation adds each entry explicitly without descending symlink/reparse targets. A real inert archive fixture verified preservation of ordinary bytes and absence of followed link-target bytes.

## Fresh independent verification

The private packet's Python suite completed: **44 tests passed**. Raw stderr is `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/independent-tests.stderr.txt`, SHA256 `5e00e1f8c5f79cb30cb468d95fb2e13ea53931bc5c6a06505b4e25c25e63f344`.

The private packet's static checker completed: **17 checks passed**. Result is `/tmp/r0016-third-20261111/work/independent_review/windows-route-candidate1/independent-static.stdout.txt`, SHA256 `4b00f158de432b24fed567d7a9850ed0399e48026fe3dfc9beaf2f9c129a2d19`. These checks include exact helper and referenced core packet identity, syntax/data structure, environment wiring, workflow selection, pinning, and archive wiring. They provide no PowerShell parser, Windows execution, or GitHub execution credit.

The additional full-validator replay comprised one accepted healthy case and four wrongly accepted adverses. Existing passing tests therefore do not resolve WRT-01. No additional decision-changing gap was established in this bounded review. Candidate 1 remains **FINAL GAP-REVISE**; a replacement requires exact-byte re-review. Native product cases relabeled: **zero**.
