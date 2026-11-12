PARTIAL

# Independent PS5.1 warm-JSON diagnostic review

**Disposition: GAP-REVISE — one bounded acquisition compatibility defect.** No installer, native Windows process, workflow, remote mutation or publication was executed. Native warm-JSON outcome remains prospective. This is technical evidence, with no acceptance or closure authority.

Requested model: **gpt-6-astra**. Actual model: **gpt-6-astra**, self-report. `authoring_context_reuse=no`; `other_reviewer_visibility=no`. I authored none of this patch and did not consume another current reviewer’s verdict or the root’s authoring notes.

Exact packet: `/workspace/scratch/0dd4b9b6a244/reviews/ps51-warm-json-packet-001`.

Manifest SHA256: **`6f1883a15a90a6e86d625067a5468c16e742c413a89d0c0ff2d85122a2fa29b8`**.

Base/head: `9c05df0b7546a7c897c6e1ab5b197f0087b5c2e4`. Tree: `62e81ff8b568ac405f25cb5648579fb1ee19caf7`. All9 manifest members’ hashes/lengths verify; both baseline files reproduce immutable9c05 objects. Candidate diagnostic SHA256 is `da069289d2cd3797b7108b4e4ee09bb15cf8431e1602cd1d3129487cf6f0576e`.

## Required correction: native assembly spelling is treated as canonical spelling

The generated source-free body at diagnostic line41 records the raw `.NET Assembly.Location`. `receive_mode` line309 immediately sends that value through `outer.checked_path`, whose exact pinned implementation requires the incoming string to equal `Path.resolve(strict=True)` literally. Independently, `receive_warm_context` line94 requires the raw context spelling to equal the canonical parent `file_fact.path`.

A legitimate native spelling such as `Microsoft.Net` paired with filesystem canonical `Microsoft.NET` is therefore rejected before the assembly facts can be associated. Even simply resolving the path at line309 would leave the second literal-equality rejection at line94. The exact checked-path function and context receiver both rejected this deterministic counterexample in the independent controls.

This is a source/receiver compatibility finding, **not a claim that ConvertFrom-Json has already produced this spelling on the prospective run**. The supplied original normal-only diagnostic artifacts contain no native read-command metadata. The root identified a prior native Test-Path assembly spelling observation and the already-pinned strict implementation for handling it; I inspected that implementation’s actual source. No path equivalence is inferred by case folding.

**Minimal repair:** reuse the existing `tests/install-entry-driver-diagnostic.py::record_probe_file_binding` mechanism, retaining the raw child assembly fact, canonical parent fact, actual raw/canonical device-and-inode identity, stable before/after metadata, content readback and resolution agreement. Admit the context only after that proof succeeds. Keep raw spelling and canonical fact as separate fields. Preserve rejection of reparse/link ancestors, changed assembly bytes, distinct files and unstable metadata. Do not lowercase paths, weaken general `outer.checked_path`, or modify product comparators.

Add focused controls for a valid raw/canonical spelling association and rejection of same-spelling/different-file, different-content, unstable-identity and failed-proof substitutions. Native acquisition still supplies the actual assembly identity facts.

## Independently supported properties

The117 recorded checks are inert source/data/adverse controls, not product qualification:

- All14 inherited source/instrument pins reproduce immutable9c05; candidate and baseline pin dictionaries are identical. Both installer source and existing acquisition/Job bounds remain unchanged.
- All four derived harness hashes and lengths reproduce the packet’s derivation facts. Every inherited `require(...)` assertion and every function other than `_case_impl` has identical AST. New cache captures are outside the declared observed input roles; no role, cache path, timestamp, security field or comparator is excluded.
- PS5.1 retains warm20 and adds warm-json, each with positive/no-open cases: four expected entries. Warm20’s generated PowerShell body remains semantically identical. PS7’s existing default/no-gather mode definitions remain unchanged, while this workflow deliberately selects PS5.1.
- The packet’s9 tests independently pass on the candidate. The same tests against baseline produce the expected8 failures for absent new receiver functions. The independently reproduced green log exactly matches the packet green hash.
- Actual retained native inventories use the expected `analysisCache`, path `.`, lowercase `file`/`absent` schema. Upstream full-row validation remains intact. Actual final PS5.1 caches are8917 bytes and their original bytes are admitted against their exact row hashes; equal-length corruption is rejected. Actual PS7 absent-cache rows admit no invented byte capture. Historical earlier738-byte captures were not retained by the old instrument and were not fabricated.
- The exact new cache-loop AST was executed using original PS5.1 result rows and clearly marked synthetic phase fixtures. Both `positive` and `no-open` retain their original `host=ps51`, `pass_=false` and exact undeclared `analysisCache` byte/time/hash error. The loop’s `cache_row` variable does not overwrite the original `row`. A truncated single phase is rejected.
- PID, nonce, mode, command type/name/module, native-utility environment, cache path, parsed result, assembly facts and context framing substitutions are rejected. Duplicate markers/JSON keys, malformed UTF-8 and original failure relabeling are rejected.

The source-free body discovers a cmdlet, parses one fixed harmless JSON object, checks the result, hashes the selected assembly, emits diagnostic context and sleeps20 seconds. It contains no installer invocation, download, browser, clipboard, staging or removal call. Its normal fixture flag remains0 and existing effect-spy and lifecycle checks remain in place. Actual native command resolution and execution are prospective; inert checks establish no native warm-up success.

The retained original status facts remain PS5.1 warm20 FAIL, PS7 default FAIL and PS7 no-gather PASS, all classified `DIAGNOSTIC_ONLY`. No result supplies full20 acceptance.

## Evidence files

`controls.json` records all117 checks, original status facts, derivations, the exact original-row retention results and the two path-compatibility counterexamples. SHA256: `df854882a4fbe75b7e314962692574779cf6fdacd42c0b9f361b47d7a2784de0`.

`review.py` reproduces the read-only review controls; its generated/pinned inputs and independent unit logs are confined to this assigned scratch directory. The packet, shared repository, original artifacts and audit state remain unmodified.

FINAL
