# R000B F02 successor output and expected-manifest identity review

## Verdict and authority

**FINAL — PASS within the requested source/generated/successor-manifest identity scope.** The current generated outputs carry the exact F02 authored-source change, the successor expected manifest and its 142-file inventory describe the current inspected bytes, and the copied outputs match the retained canonical-build and preservation receipts. I found no new product identity discrepancy in this scope.

This is an independent read-only review by `/root/source_recovery_review`. It does not grant native qualification, a final immutable-candidate verdict, whole RLGWO acceptance, release, publication, or closure authority. Root retains those decisions. I made no repository, source, test, document, Git, network, or browser mutation. Reviewer scripts and reports were written only in the commissioned scratch evidence directory.

**Required handoff:** the successor manifest is correctly bound as a scratch artifact, but the workflow's canonical candidate-manifest path was still bound to the old product at the last inspection. Before a native run, root must deliberately supply/package the successor manifest at the path the driver actually consumes. Merely archiving it as evidence does not change that route. This is an outstanding integration step, not a defect in the inspected successor manifest.

## Exact subject and inspection boundary

Repository: `/workspace/scratch/15b8fb6ac4c2/r000b-work`.

| Identity | Exact value |
| --- | --- |
| Engineering base commit | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` |
| Engineering base tree | `6b94a3933f9d1381b1c2ceaab287c93afb215ecb` |
| Inspected HEAD | `d124f050ec68fa8608022b1ed5fead426d42dcb9` |
| Inspected HEAD tree | `54c61ab27f95adcf0837f737ca3dfd09649fc5c3` |
| Frozen current `src/native/index.html` SHA-256 | `fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327` |
| Frozen current `tests/weather-no-timetable-handoff.test.cjs` SHA-256 | `f1669a82fa40691e0179372b282a41a9e369147887cec8f89c6f88ad58b23110` |
| Successor expected-manifest SHA-256 | `3f7053e0c4108297be5c91db98732f8c1ec1c07f9bc3984dae196e478958790b` |
| Successor runtime-inventory SHA-256 | `551abca75e52a893fb9b90abef1a190e72287addca7dfcb632b1d5a65a1946ac` |
| Successor runtime tree SHA-256 | `04ab5ba61f1351a8e4c4b459904c79ba51bcb2ccf19478302bdbfcc3950970f8` |

The independent main identity computation completed at `2026-11-10T06:02:56.546603+00:00`; the final inventory of review evidence was recorded at `2026-11-10T06:04:54.839126+00:00`. At those observations the five dirty product/test files were `index.html`, `offline.html`, `moon/BUILD.json`, `src/native/index.html`, and `tests/weather-no-timetable-handoff.test.cjs`. Root subsequently reported adding the successor evidence package to repository documentation. This review does not assert an immutable full tree including those later documentation writes.

A narrow handoff recheck at `2026-11-10T06:07:37.908737+00:00` confirmed HEAD, both frozen authored/test hashes, and the still-old canonical candidate-manifest hash. That check is retained separately rather than rewriting the earlier identity observations.

The prior F02 behavioral source review remains in `/workspace/scratch/d9a9ea2be931/recovery/source-f02-review.md`. Its bounded SR-01 disposition is not expanded by this identity review. Original SR-01 probe, red output, and earlier review artifacts were preserved.

## 1. Canonical generated outputs match the retained build

I independently hashed the current output bytes, calculated their Git blob identities, compared the committed preimages, and compared the retained build-output and copy-preflight records.

| Output | Bytes | Current SHA-256 | Git blob identity |
| --- | ---: | --- | --- |
| `index.html` | 1,593,846 | `e8da0b7646ad4c3b04e1571739dcc295c605cca8e46af59c11d5f1fefd120657` | `b9f317d663be9e2f9983bc815d5825ce44a1ece8` |
| `offline.html` | 81,707,367 | `b215ce9b5977f880ebfe87e626fe08963e36cdacd3f5f860b7aa2dc3f5af10a7` | `c36de2ef7e3e2667e4dd4f44eeb09f9a0f600f14` |
| `real-sky/native-sky.js` | 396,323 | `426754834c6c116c4521ad5067bb1e37a9845830fc07ebbb62dd22fcdc757d66` | `771d07a5cc08c70330a6a722343703a42c41715a` |
| `moon/BUILD.json` | 4,146 | `2dbc98959742fd3d65f7c4bbcc7de45ded790b0fe0c48ef0fb4efe5d668b2747` | `05031b6577bbcda2b9a67081f6b9ce5ecb463e30` |

All four match the retained canonical output records. Only index, offline, and Moon BUILD changed. The native sky bundle is byte-identical to committed HEAD; its absence from the preserved *dirty-file* set is expected, and does not mean the current file failed a comparison.

The inspected canonical-build receipt records `python tools/build_native.py`, exit 0, with a completion log reporting `physical: true`, `nativeBundleBytes: 396323`, `dataBundleBytes: 9807339`, the successor index SHA above, and stage `complete-native-and-moon`. I independently matched the raw log bytes to its recorded SHA-256 `0370c02e73d605f158ee151bf13d2d0fdab3850e7fcf9f7e7c83a01e064bb47e`.

The same receipt records a successful frozen-V1 verification and a successful protected-path diff. Their raw logs also matched their recorded hashes. These are retained root execution receipts; I did not rerun the builder or claim to have observed its deleted worktree directly.

### Exact F02 propagation, beyond matching receipts

I extracted the old and current authored block beginning at `function cloudAuthorityMatches(` and ending immediately before `function rememberWeatherEffects(`. Replacing the current block with the committed old block reconstructs the entire committed old authored source exactly.

For **each entire generated HTML file**, the current authored block occurs exactly once. Replacing that one occurrence with the old block reconstructs the entire corresponding committed old generated file byte-for-byte. This establishes that the F02 owner block was propagated exactly and that all remaining bytes in both generated files are unchanged. It is stronger than checking that a source substring is present or trusting the build summary.

The JSON value of `moon/BUILD.json` differs only in `source["src/native/index.html"]`, which changes from the recovered pre-F02 authored hash to the frozen F02 authored hash. Native bundle bytes, other source entries, maps, and other generated content did not acquire an unrelated delta in the inspected outputs.

### Removed build checkout and surviving bytes

The disposable checkout was already removed when this review examined the preservation route. The retained `/tmp/r000b-successor-build-preserved/preservation.json` identifies its former path, the same HEAD, and all four dirty files: authored source plus index, offline, and Moon BUILD. Its SHA-256 is `547935dac431fe19ce8907e25d89dd3e70f5f8b69155df345a65bfebe3d15269`.

I independently read all four surviving files and verified that each matches the current corresponding file and the preservation record. No lost dirty output was demonstrated. The residual limitation is that the removed checkout cannot itself be reinspected; conclusions about its execution rely on the surviving bytes and retained command/log records. The exact whole-file delta checks above independently constrain what was copied.

## 2. Successor manifest describes the current product and harness

Successor manifest: `/workspace/scratch/d9a9ea2be931/recovery/r000b-native-candidate-f02.json`.

Successor inventory: `/workspace/scratch/d9a9ea2be931/recovery/r000b-native-candidate-f02-runtime-inventory.json`.

The manifest uses schema `r000b-native-expected/v1` and label `R000B-successor-F02-source-verified-native-pending`. I read the actual `tools/cp9/runtime_identity.py` rule and independently enumerated and hashed its runtime set: the top-level product/config/builder files, all real-sky files, and Moon runtime files excluding its source/tests directories. The independently constructed 142-path set, byte sizes, per-file SHA-256 values, sorted digest input, and final runtime digest match the fresh inventory and expected manifest exactly.

There are no added or missing runtime paths relative to the committed v2 inventory. Exactly three runtime leaves differ: `index.html`, `offline.html`, and `moon/BUILD.json`. The old runtime tree is `8958c9089e353f43115cb0cb8aa8d0883c9d0e413d76ab4a9e6a6c2d02123305`; the successor is `04ab5ba61f1351a8e4c4b459904c79ba51bcb2ccf19478302bdbfcc3950970f8`.

All eight `authoredSources` entries and all five `fixtureSources` entries independently match their actual current file sizes and hashes. Of those thirteen entries, only `src/native/index.html` changes from the old expected manifest. The other entries bind the authored config, native host hooks/composition/refined host/preview host, canonical builder, shared script admission helper, R000B fixture and native driver, R000C native helper, browser-runtime helper, and runtime-identity helper. The complete values are retained in `source-f02-output-identities.json`; I checked actual bytes rather than accepting the manifest's claims.

### Script ordering and admission

I independently parsed all six generated index script entries, then ran the actual shared `parseScripts` / `admitScripts` helper against those bytes without executing the product. It accepted profile `split-moon`, selected native index 3, and accepted the unchanged three prerequisite pins.

| Index | Role | Change from old manifest |
| ---: | --- | --- |
| 0 | External config | Unchanged |
| 1 | First-paint prerequisite | Unchanged |
| 2 | Moon initial prerequisite | Unchanged |
| 3 | Native inline runtime | SHA-256 changes to `4e60aa2adc183d6edf32e95a2444a8575f2b67f7ee19b382fab718d3891b6fff`; 314,007 characters |
| 4 | Moon refine prerequisite | Unchanged |
| 5 | External native-sky bundle | Unchanged |

The old native inline body was 313,605 characters with SHA-256 `4551996101c060154280adb5ae2fcfd7fdf9a2ad14752d6063759f8e8ccb9277`. There is no unrelated script reordering, prerequisite repin, or new script entry.

Relative to the committed current candidate manifest, the successor manifest changes only its label, runtime tree, index hash, script-body entry 3, and the authored native-index entry. All other fields remain equal.

## 3. Old manifest history remains distinct; the workflow still needs the successor binding

I read the manifests from committed HEAD with `git show`, compared the current working copies, and inspected both archived native-manifest generations. This keeps historical evidence separate from the new product identity.

| Manifest | SHA-256 | Observed relationship |
| --- | --- | --- |
| Committed baseline | `87da9be549e0dd137d556ac07844432e5eb93544eb5a784cc371f10f89fe06b5` | Baseline authored identity and repaired native driver |
| Committed candidate | `a2560df1fa38878e26e20ca27747ddc5db209d55532e98745121dde153aca3d0` | Recovered pre-F02 source and old runtime tree |
| Archived v2 candidate | `a2560df1fa38878e26e20ca27747ddc5db209d55532e98745121dde153aca3d0` | Exact same bytes as committed candidate |
| Archived v1 candidate | `84dcf2ca03192ddd3f72daf8b20b5d8cbea0c5eedfc606a58136b2ad0d919a07` | Same old product identity but earlier driver hash; historical evidence only |
| Fresh F02 candidate | `3f7053e0c4108297be5c91db98732f8c1ec1c07f9bc3984dae196e478958790b` | Correct inspected successor product, source, and current helper/fixture identities |

At the final handoff observation, `/workspace/scratch/15b8fb6ac4c2/r000b-work/docs/state-contracts/r000b-native-candidate.json` still had the old `a2560df1…` identity. The workflow `/workspace/scratch/15b8fb6ac4c2/r000b-work/.github/workflows/r000b-weather-withdrawal.yml` still passes `candidate/docs/state-contracts/r000b-native-$R000B_PRODUCT.json` as `--expected-manifest`. The native driver's strict identity checks should reject the successor product with that old candidate manifest; relaxing those checks would defeat the intended binding.

| Handoff field | Required disposition |
| --- | --- |
| Priority | Required before any successor native execution through that workflow |
| Owner | Root/integration owner |
| Path | Canonical candidate-manifest argument consumed by `run_r000b_withdrawal.py` |
| Evidence | Actual workflow argument plus old canonical manifest hash, independently rechecked at 06:07:37 UTC |
| Consequence | An unchanged workflow route still supplies the wrong expected product identity |
| Countermeasure | Deliberately bind the verified successor manifest at the consumed path or explicitly supply its verified path in the authorized native execution route |
| Check | Verify the manifest actually consumed has the successor identity, and that the native driver's exact runtime/source/helper/script preflight accepts it without a bypass |
| Residual risk | Later product, helper, fixture, manifest, or workflow changes require fresh exact-currentness evidence; this scratch review does not seal a later full candidate |

This integration item was sent to root before finalizing the report. I did not alter the workflow or canonical manifest.

## 4. Protected paths and frozen V1 are preserved

The independent current comparison against inspected HEAD returned no changes in `v1`, `vendor`, `real-sky/native-sky.js`, `tools/build_native.py`, or `tools/build_moon.py`; no untracked V1/vendor files were observed. The retained canonical-build protected check also records exit 0.

I separately read the frozen V1 anchor and payload identities, checked the exact expected file set and its preservation attributes, and verified the anchor/version cross-references. The manifest SHA-256 is `aa4bfcbc54f838e93d8ab41e58845efd753fcea80e8ebef3a784acf304e6a4cb`. The V1 index, config, and VERSION files match the anchored hashes and sizes. This is a fresh byte-identity inspection; I did not regenerate V1 or replay the unchanged verification suite.

## 5. Retained cohort receipts: valid counts, bounded meaning

I checked `generated-cohorts/results.json`, verified the SHA-256 of all ten referenced raw logs, and read their TAP or custom JSON outcomes. The retained commands all report exit 0. Together they record **312 successful tests/cases, zero failures, and four existing R000C TODOs**. Those TODOs remain separate from successful cases.

| Retained cohort | Successful | TODO |
| --- | ---: | ---: |
| R000B remaining | 57 | 0 |
| R000C weather | 121 | 4 |
| R0024 weather | 63 | 0 |
| R0024 cloud expiry | 9 | 0 |
| R000B sky withdrawal | 9 | 0 |
| R0025 continuity | 9 | 0 |
| R0025 lifecycle | 16 | 0 |
| Native composition | 14 | 0 |
| Native head handoff | 6 | 0 |
| Native startup handoff | 8 | 0 |

These are retained root execution results, not new independent executions by this reviewer. Their test boundaries differ. Six logs explicitly print the successor generated index hash. The sky-withdrawal and composition cohorts exercise actual source/module boundaries; native head handoff reads authored source slices. The startup harness defaults to generated `index.html` and supports an explicit source override. Accordingly, this review does not label all 312 cases as full generated-runtime or native executions.

My first receipt-reader attempt expected custom JSON in a single-line form and stopped on the pretty-printed head-handoff result. I preserved that script and failed output. The corrected reader accepts the actual whole JSON object and verifies all six named cases have `passed: true`; the correction did not change product code, a test oracle, or any underlying log. The successful reader output is retained separately. No cohort was rerun to improve counts or conceal that reviewer parsing error.

## 6. Read set and review artifacts

The current review read the actual generated outputs and source block; committed old output/source preimages; current and archived baseline/candidate manifests and v2 inventory; the new manifest and inventory; actual authored/helper/fixture files named by the new manifest; the shared script-admission helper; runtime identity and canonical build rules; protected/V1 anchors; the workflow's expected-manifest route; relevant cohort input routes; all ten retained cohort logs; canonical command logs; copy-preflight records; and the four preserved dirty build files. Prior behavioral source review findings were not substituted for these current byte checks.

Primary evidence directory: `/workspace/scratch/d9a9ea2be931/recovery`.

| Artifact | SHA-256 |
| --- | --- |
| `source-f02-output-identities.py` | `fe55351d1765044e5d67e38b75c3724d2eca7af0c89fed75d23e450600078e50` |
| `source-f02-output-identities.json` | `77e0e0c6a5ed6055f4fb330eab73633aa903e121bc683d5f1621da7745daca0c` |
| `source-f02-output-identities.log` | `ab131af60f4bc6ad295d97b7616474f89e64b0619b1bdf6a54539dc94263550c` |
| `source-f02-output-identities-attempt1.py` | `30178052a18882263c205a822f68f02a1b579d14f43784a8d0db06e1c9d6eb1d` |
| `source-f02-output-identities-attempt1.log` | `5fe76c864b3b240edfba3d264d26abe3da423edd4bcfce62eab8fd6664948455` |
| `source-f02-output-script-admission.json` | `e470a73422c53011367f35b37bf5d615b85a733272216c74470e58286f3eb31c` |
| `source-f02-output-v1-identities.json` | `4c12405c3b436057b97634fd0233ca433de789aaa42065dc0dd1c0e3d10842e6` |
| `source-f02-output-manifest-history.json` | `02633b68fdf8c8271d6010ba7d973aad56a49889498f4c9212803b71acdb8dfc` |
| `source-f02-output-final-identities.json` | `9fc342e60ba53e837c6aca0d734c09bb91a58056698323c3ce1f0bc0ce948cff` |
| `generated-copy-preflight.json` | `0d4d74ffac29f9983e355debfda116bfa1ddaef55f94ace87750a23a370977e5` |
| `build-successor/commands.json` | `13115a67dfd964869e8657e4a433529cace0700358155cb9c7f34b1600cfa9ff` |
| `build-successor/outputs.json` | `9b85986979652ad41322f7f9b78ec32d22f879a4d838e85e2d2ebecf39edfa12` |
| `generated-cohorts/results.json` | `a9b520a672fc57f37d0210ccd446a3db51a04b2992c2a50a8c682b7f732508ce` |

`source-f02-output-handoff-identities.json` records the final narrow source/test/HEAD/canonical-manifest/workflow recheck. The source behavioral report and its independent reruns remain separate evidence for the earlier F02 source decision.

## Remaining authority and evidence boundaries

The verified successor files and scratch manifest are suitable inputs for root's next authorized integration/native qualification steps. This review does not establish that the workflow has been rebound, that a later repository evidence package is byte-complete, or that a final commit has been sealed.

No actual rendered native evidence was executed by this reviewer. Native pixels, true raster clearing, actual hidden/resume execution, reduced-motion presentation, elapsed motion/cost, screenshots, and the remaining B01–B18 / ES0B-01–15 product obligations must continue to use their required native and whole-contract evidence. The independent source and byte-identity results do not take over R0007, R000D, R0021, R0024, or R0025 authority. Final currentness, native acceptance, and whole-contract closure remain with root under the existing commission.
