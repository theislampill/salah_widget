# R0016 integration glue: independent bounded review

## Outcome

No remaining integration-glue defect was found in the final supplied candidate bound by `candidate-bindings.json` SHA-256 `efc95f3b6274f00d67a7704577614002c5d6a3726aa8ee371537bce6b53873d4`.

One concrete stale-source-pin defect was found in the initially supplied Windows full-entry collector `6167f9f672a1349fa790f726f55a984fe9a4ffb8da546eabedf2422dd9febfa9`. The parent corrected it in `652848809fc581452e4bf48e2895786cd3c780e60e0a2c3091e2969d7b856616`. Independent inert boundary checks retain the original rejection, accept the intended source with the corrected binding, and reject both the old and an unrelated source hash.

This is source/control-flow and inert-check evidence for the explicitly scoped acquisition-only integration. It is not formal audit readiness, native qualification, acceptance, publication authority, or closure. The pending normal/cache discriminator, actual native runs, and final documentation source-pin/render work remain open. No skipped workflow receives qualification credit.

## G01: stale common pin in outer normal-result receiver — corrected

The product adapter correctly introduced its own new `PREVIEW_SOURCE_SHA` and stopped copying that constant from the immutable common module. The common file remained SHA-256 `4600bac181dcac5fe7f72467c6018800666284d7087cf98f8b9bf5a449910821`, whose historical pin is `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4`.

However, the original outer collector loaded that common file into `composition` and passed the entire common module into the AST-selected `require_normal_input_postcondition` receiver. It simultaneously supplied `SOURCE_HASH_BEFORE` from its new installer INPUTS pin, `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a`.

The unchanged receiver at fixture line 304 explicitly requires:

```python
require(SOURCE_HASH_BEFORE == composition.PREVIEW_SOURCE_SHA,
    'Normal input postcondition requires the reviewed complete source')
```

Thus a successful positive/no-open observation would still be rejected during outer receiving once it reached this guard. This was an actual cross-module pin mismatch, not a defect in the exported common helper implementations.

The corrected outer collector at lines 436–440 supplies a small `SimpleNamespace` containing exactly the four `composition` attributes read by that receiver:

- `PREVIEW_SOURCE_SHA`, bound to the current `INPUTS['install.ps1'][1]`.
- The unchanged common `require_positive_confinement` function.
- The unchanged common `validate_rows` function.
- The unchanged common `ROW_FIELDS` object.

The support object and `SOURCE_HASH_BEFORE` binding remain unchanged. The receiver body and comparison are not altered. The common module is not mutated.

### Exact inert witness

The witness evaluates the exact original/corrected outer binding ASTs and executes only the exact source-pin guard AST. Other functions are identity sentinels and are never called. This is deliberately a pin-boundary check, not a complete normal-observation or native test.

| Binding | Supplied source hash | Guard result |
| --- | --- | --- |
| Original collector `6167…` | Current `07671…` | Rejected with the exact source-pin error |
| Corrected collector `6528…` | Current `07671…` | Accepted by this pin guard |
| Corrected collector `6528…` | Historical `7fbe…` | Rejected |
| Corrected collector `6528…` | Unrelated all-zero digest | Rejected |

The corrected namespace preserves helper, ROW_FIELDS and support identity. The immutable common pin remains unchanged. `source-pin-witness.json` retains all bindings and outcomes. `outer-before-correction.py` retains the exact `6167…` bytes; they were recovered by reversing only the new binding in the supplied successor and verified against the original supplied full SHA-256.

## Product/common/diagnostic pin propagation

Product support `70a6ce6193206d757783a3fb4ba2bc32462677d1980818c75a1e60e6bbb56a99` defines the current installer pin locally. The export loop still copies the same functions/constants except `PREVIEW_SOURCE_SHA`. AST dependency traversal shows the common module's old pin is referenced only by its own `prepare_pair`; that function is neither exported nor reachable through any exported common function. The product adapter defines its own `prepare_pair` using the new pin.

The main fixture imports `install-entry-product-support.py` as `composition`, so its own path-budget and normal postcondition checks use the current product pin. The diagnostic file remains exactly `08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5`. Both common and diagnostic files are identical to the retained R0016 versions. The newly corrected outer namespace accounts for the only stale pin path found in this review.

The full-entry collector's INPUTS map binds current installer, main fixture, and product support bytes. All other listed inputs retain their prior exact identities. Across full-entry, core, and routes collectors, all 25 declared input-pin entries matched the supplied proposed files or exact unchanged trial-merge object bytes.

## POSIX collector dispatch and receipt handling

Collector SHA-256: `3c7dd018fb3bd06df24da17e96fcedc620be3440caa0996c242efa73d68fc926`.

The complete collector diff adds only these dispatches:

| Test | Exact enclosing conditions |
| --- | --- |
| `install-staging-parent` | OS is Linux or Darwin; phase is r0015 or r0016 |
| `install-staging-readonly` | POSIX branch; OS is Darwin and phase is r0016 |

Both receive the actual repository `install.sh` path. No r0013 or Windows dispatch is added. The parent test is the exact accepted-main file, SHA-256 `b73b21a0224cbb7ef4e3208abdad283c545cbdb5bbde0f50c7071b47a21b763f`; the read-only control remains the previously reviewed `cdf573290a502eb7681d78c5196ca9c2fbdc700fc8e17654870fd15e4fef88a8`.

The existing collector handles both tests' `results`/Boolean-pass receipt forms. A parent-test privilege-blocked row has a false pass flag and cannot become collector PASS. The read-only control's reported fixture is copied through the existing bounded fixture-retention path, preserving its scripts, raw streams and per-run observations. No receipt predicate or aggregate success rule was weakened. The source-hash inventory already includes both new test names through `tests/install*`.

## Workflow changes

YAML structure comparisons confirmed exactly the intended modifications; after removing each new path entry or job condition, the workflow structures equal their R0016 originals.

- Linux 22 workflow `3832d2adc7fd37bc2b789b543c70d1d2d19712eafcde679ae24436dade9cbf42` adds `tests/install-staging-parent.py` to push paths.
- macOS workflow `9b2ab2aabd7c6f9b9c4ef32398f57803aaaf448e90f85432b9aeea9466d98ab9` adds both `tests/install-staging-parent.py` and `tests/install-staging-readonly.py` to push paths.
- Both already retain the new files through the non-cone `/tests/install*` sparse-checkout pattern. Runner, platform/phase arguments, steps and evidence upload remain unchanged.
- Full-entry workflow `85ee6d81a9ab041cc745ebe776ada0159817587e0692724943997e1255c120a4` adds only the explicit acquisition-marker condition to the Windows job. Its ps51/ps766 matrix, exact twenty-case command, filters and retained-evidence steps remain unchanged.
- Documentation workflow `9fdb1d0bd81499640797ca1b13e79aa52299498773e163240292ddd90f385617` adds the same condition to its render job. Its existing rendering and input filters remain unchanged.

The two conditions are:

```yaml
if: ${{ !contains(github.event.head_commit.message, '[r0016-acquisition-only]') }}
```

The explicit acquisition-only integration commit suppresses those two jobs and yields no full-entry/render qualification. A later unmarked commit meeting the existing source/fixture paths runs the normal full-entry matrix; a later unmarked commit meeting the README/renderer/workflow paths runs documentation rendering. A README-only commit does not newly trigger full-entry, because that workflow's unchanged path list does not include README. No other job has been made conditional on this marker by the supplied changes.

## Published core and route collectors

The parent supplied `/tmp/r0016-third-20261111/work/combined-candidate/core-reviewed-original.py` as the exact published core from commit `be35bcf33c87bc60d4701e32945fa58298d64f2a`. This review independently verified 38,792 bytes, SHA-256 `555e606be5d55bf65862473b65790e96c5bcf81cacdc8bce6d0968e652f30834`, and Git blob ID `87b3d6d098499dbcb2a4868ae56444e737999414`. Remote acquisition provenance was supplied by the parent; this reviewer did not refetch it.

Proposed core `ac6b8c9e5cf2c3d2a542d325584c872597eed84171b782e7b1ddf107e07f3ff2` differs from those exact bytes only in the installer source pin. The extra changes visible against older d502 are already present in the supplied published core; no fresh behavioral change is hidden in the proposed repin. This does not transfer that collector's historical qualification to the new installer.

Routes collector `381b9103f45a8f64c5c39d7c61b5c43a6acc31c35a149b08bc030b96ad282924` differs from the retained R0016 version only in the installer source pin.

## Fixture publication and README

Main fixture `a453230b3527bdc5a81dcf7279d9af2aad14b32c07756a4700c97eab2ce24646` changes only the two Firefox metadata writes to canonical byte writes. Product support retains the reviewed atomic ACK publication while adding the product pin isolation described above.

The newly included `tests/install-entry-input-publication.py` is byte-identical to the retained author test: 6,243 bytes, SHA-256 `35d170b71e037854b73d431d06b32bafd29dfd7a353dfcd93eb6539b950bc4eb`. An independent inert execution against the currently proposed main/support returned **7 passed, 0 failed**. It tests exact AST slices with deterministic newline/interleaving behavior; it is not native Windows sharing-mode evidence.

README `01e6969d92438c40e088802cba6d8ea2b6f35373cd96a732434e54832273e526` equals the exact trial-merge README after selecting the accepted-main side of both conflicts. There are no other deletions or additions in that resolution. The retained Bash and PowerShell commit pins are interim accepted-main values; the parent explicitly plans to bind the actual integrated source commit in a subsequent documentation commit and update/render the documentation producer before acceptance. That future work is not satisfied by this review or by the acquisition-only skip.

## Evidence and limits

- All 16 final candidate bindings match their file bytes and SHA-256 values.
- All 25 declared collector input-pin entries match their actual inputs.
- All 9 proposed Python files parse and compile without executing their top-level code.
- The stale-pin red observation, corrected positive, and two wrong-source negatives are retained.
- The copied publication test's 7/0 inert result is retained.
- No installer, PowerShell process, native host probe, workflow, browser render, publication or Git mutation was executed by this review.
- Work was written only within the assigned review directory. No formal audit disposition, native PASS, acceptance, release readiness, or closure is conferred.

The original installer semantic report and its manifest remain separate and unchanged. This report addresses only the additional integration glue and the correction discovered here.
