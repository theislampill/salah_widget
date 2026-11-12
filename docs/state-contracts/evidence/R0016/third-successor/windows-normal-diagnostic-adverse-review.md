# Independent review: private normal-profile diagnostic

Disposition: **BLOCKED — nested evidence association gaps in the diagnostic receiver.** The private variants preserve the original strict product checks, but the new receiver can classify inconsistent nested evidence as a complete `DIAGNOSTIC_ONLY` result. Correct the receiver before publishing this exact runner for the proposed acquisition. No native result, qualification or closure is granted by this review.

## Exact reviewed packet

- Packet: `/tmp/r0016-third-20261111/work/profile_attribution_g17/proposal/`.
- `SHA256SUMS`: 2683 bytes; SHA-256 `2130513fbaf97068fea806d6a50f568bcc1fa67dfbaf731f9e3e52a426580543`.
- All 25 listed payloads and all 14 declared source-map inputs independently match their sizes/digests. Exact copies are retained under `author-packet/`; `packet-verification.json` records the checks.
- New runner: `proposed/tools/qualification/installer_preview_windows_normal_profile_diagnostic.py`, 25262 bytes; SHA-256 `717f8c5c1d2470de665eceda0d5edfe1dc4a5a909eedb543091361806c64bf92`.
- Product source: `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a`.
- Inherited composition fixture: `a453230b3527bdc5a81dcf7279d9af2aad14b32c07756a4700c97eab2ce24646`.
- Product support: `70a6ce6193206d757783a3fb4ba2bc32462677d1980818c75a1e60e6bbb56a99`.
- Immutable common: `4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821`.

## Blocking finding: incomplete nested raw/readiness binding

`receive_mode` calls the inherited `validate_direct_terminal` for each product and source-free receipt. That function establishes terminal/cleanup structure and checks that stdout/stderr facts are dictionaries; it does not rehash those raw files. The new receiver verifies the outer controller captures but does not verify the nested raw facts against their exact owned paths and bytes.

The receiver also validates that `observation.readinessNonce` is a unique 32-hex string without binding it to the product receipt's nonce, ready token, PID and actual ready/ACK facts. Finally, it compares the warmup `fullReady` against the loaded warm-ready inventory but omits the corresponding product receipt `fullReady` equality check.

An inert synthetic packet exercised the exact candidate receiver, exact inherited terminal predicate, real JSON/file-fact readers and original complete inventory validator. Its baseline has original FAIL rows and an original controller exit 1; acceptance remains diagnostic-only. Four separate mutations were nevertheless accepted:

| Counterexample | Exact adverse change | Candidate result |
|---|---|---|
| Product raw capture missing | Delete `c10/entry-profile-window/stdout.raw`; retain its declared fact | `DIAGNOSTIC_ONLY` |
| Warmup raw capture changed | Replace `c10/host-only-control/stderr.raw`; retain its zero-byte fact | `DIAGNOSTIC_ONLY` |
| Product nonce misassociated | Change `profileWindow.nonce` to another 32-hex token while observation nonce and actual ready token remain unchanged | `DIAGNOSTIC_ONLY` |
| Product ready inventory detached | Set `profileWindow.fullReady` to null while the loaded full-at-ready inventory and observation remain intact | `DIAGNOSTIC_ONLY` |

In the JSON-mutating cases, the report, envelope and outer raw capture facts were refreshed consistently; therefore rejection was not masked by an unrelated stale outer hash. The nested association was the variable under test. All synthetic packets are explicitly test data, not native observations. The candidate continued to return `qualificationAccepted:false`, so these counterexamples do not allege invented qualification credit. They do contradict the README's promised incomplete disposition for inconsistent raw/embedded receipts and weaken the cache attribution boundary.

### Minimal correction for review

Keep the source variants, original comparisons and diagnostic-only disposition unchanged. In the new receiver:

1. Verify both nested stdout/stderr facts against the precise expected owned files for both warmup and product, including size and SHA-256.
2. Bind the recorded environment nonce, receipt nonce, PID, ready token and actual ready/ACK file facts; bind the product observation nonce to that same receipt. Refuse missing, replayed or inconsistent evidence.
3. Require the product receipt's `fullReady` to equal the independently loaded product-ready inventory, as already required for warmup.

Rerun these four counterexamples expecting refusal, while retaining successful receiving of a complete original FAIL/exit1 packet. These checks use evidence already acquired; they add no native telemetry requirement or comparator exclusions. This reviewer authored no candidate correction.

## Checks that passed

**Scope and derivation.** The fixed plan is six genuine normal entries: PS7 default positive/no-open, PS7 no-gather positive/no-open, and PS5.1 warm20 positive/no-open. Each mode has separate state/control/output trees. The three exact runtime derivations reproduce the frozen derived files. Only `_case_impl` changes; every other top-level AST node and every other function's source bytes remain identical. Existing assertion ASTs remain unchanged. Added behavior is limited to the declared prelaunch flag, literal source-free 20-second sleep and full source-free before/ready/after inventories.

**Strict product predicates.** The normal pre-ready profile equality, retained-bundle/effect checks, full profile comparison and full-input postcondition remain unchanged and called by the inherited fixture. The complete cache/ACL/metadata fields remain in the inventory/difference path. All ten product-support function bodies match the previously reviewed `11eb9944…` helper; its change to `70a6ce61…` is the separate candidate source pin and removal of the old common-pin import. The immutable common/source-free modules retain their exact original bytes. The source-free control body contains no installer invocation and retains `INSTALL_FIXTURE_NORMAL=0`.

**Failure semantics.** Complete original FAIL rows require envelope/report FAIL and controller integer exit 1; mismatches are refused. The default mode's original error and boolean are retained, and a natural default failure does not become a product pass. Missing/unstable inventories and timeout controls are rejected. Even a fully received six-entry diagnostic keeps `qualificationAccepted:false`; no full20/native acceptance follows.

**Source and launch binding.** Fourteen inherited files are pinned and copied, runner and derived bytes are retained, and source/instrument identities are checked in the report. The old `d81c0b49…` outer helper retains historical product pins, but the diagnostic calls its generic builders/readers with the separately pinned candidate inputs; it does not invoke that old outer main/full20 report validator. This is a deliberate bounded reuse, not an unnoticed source-pin replacement. Original and copied input facts are checked before mode launches and at termination. Selected host/runtime dependency facts are retained across modes, within the documented PS5.1 dependency limitation.

**Lifetime and paths.** The unchanged host helper creates suspended controllers, assigns their Job before resume and closes the kill-on-close Job. Each mode has a 480-second controller deadline; inherited children retain 60 seconds and cleanup. The receiver requires complete outer launch/terminal/capture observations and unchanged genuine `-NoProfile -File` product commands. The C: profile requirement, fresh canonical child and 48 UTF-16-unit diagnostic-root cap remain. Inert evaluation of the exact normal path-budget function produced maximum source-owned paths of 200 units for the documented runner parent and 206 units at the declared root cap, below the unchanged 240-unit bound. No Windows timing or compatibility outcome is inferred.

**Failure archive.** The archive function retained an INCOMPLETE result and exact adverse binary capture in an inert test. A symlink was retained as link metadata without reading the external target. Every owned member is traversed; there are no cache exclusions. The parent will supply the workflow's success/failure archive invocation separately; no workflow was included or reviewed here.

## Verification and boundaries

The seven author inert tests passed in this reviewer's copied packet. Sixteen independent controls passed, including the four acceptance counterexamples as confirmed adverse findings. The native-platform CLI guard returned exit 2 on this non-Windows host before dependency loading or child launch. Exact outputs are in `executions.json`; detailed controls and counterexamples are in `independent-results.json` and `independent_checks.py`.

An audit hook in the independent test rejects process creation and network access. Only local Python source/data checks and archive operations ran. No PowerShell/native probe, installer, shared source mutation, remote operation, publication or additional agent was used. The synthetic fixtures are preserved solely for reproducibility.

The first independent test attempt constructed a 49-unit synthetic root while intending to test the 48-unit cap and stopped at its local assertion. The review-only string was corrected to 48 units; the next run completed with exit 0. Candidate bytes and requirements were unchanged.

Earlier native cache failures remain historical evidence. Whether no-gather prevents the PS7 post-ready write and whether a 20-second source-free warmup materializes the PS5.1 cache remain untested hypotheses. A non-reproducing default remains inconclusive, and later product writes remain original strict failures. This review confers no acquisition authority, currentness, readiness, acceptance or closure.
