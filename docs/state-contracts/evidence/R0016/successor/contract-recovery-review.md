Report state: FINAL

# R0016 contract recovery review

Bounded read-only audit of source and evidence at `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`; no installer/test execution, source changes, remote mutation, or qualification/merge/closure authority. The complete 46-row mapping appears below. This is a source/evidence review, not a new execution receipt.

## Actionable recovered findings

### CR-01 — Advertised PowerShell environment option bypasses validation (source-derived product defect; not executed)

`install.ps1:25-26` attaches `ValidateSet` to `InstallSource` but obtains its default from the documented `SALAH_INSTALL_SOURCE` environment override. There is no subsequent explicit membership check before discovery or preview. PowerShell validates supplied parameter arguments, not default values: Microsoft documents this for both [5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_functions_advanced_parameters?view=powershell-5.1#parameter-and-variable-validation-attributes) and [7.6](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_functions_advanced_parameters?view=powershell-7.6#parameter-and-variable-validation-attributes). Consequently, an invalid nonempty environment override with `-InstallSource` omitted is inferred to reach the generic GitHub preview path at `install.ps1:1642-1644` and the normal GitHub route at `1529-1551`. Bash independently checks the resolved environment value at `install.sh:63`.

This misses the malformed-option refusal in 22-01/22-05, P10 and README:140-142. The wrapper's only bad-option case sets an explicit parameter (`tests/install-preview.ps1:571-572`); the exact-file fixture always supplies `-InstallSource`, including the invalid case (`tests/install-entry-native-coverage.py:246-249`). Those tests cannot discriminate the advertised environment-default route. Root should preserve a bounded actual-source RED before any correction; preserve valid explicit/default routes and no-effect failure observations. This review has not executed the hypothesis and claims no observed native failure.

### CR-02 — Combined preview and NoOpen prints opens that normal NoOpen suppresses (source-derived wording discrepancy)

Both scripts allow the combination, but their entry preview branches ignore `NO_OPEN` / `NoOpen`. `install.sh:788,794` and `install.ps1:1643,1648` promise planned browser opens; the real dispatch helpers suppress every open at `install.sh:208-210` and `install.ps1:762-764`. The combination is absent from the new preview matrix. This does not demonstrate a no-effect escape; it is a bounded mismatch between the intended-action plan (22-01/22-11) and selected normal-mode behavior (22-07/22-12). Root should confirm the selected-action wording with a bounded controlled combined-switch observation before changing source. This is narrower than the no-effect security boundary and must not be described as a demonstrated side-effect escape.

### CR-03 — Current ledger does not yet represent the actual received frontier

All 46 current rows share generic evidence text still saying the 63-row supplemental acquisition is pending root receiving, while the same file's `scopedCurrentPowerShell` and `current63-root-receiving.json` record its independent receipt. `docs/state-contracts/R0016.md:51` says native results remain pending, while `native1/README.md` and `native1/summary.json` retain actual failures. The historical `priorEvidenceProjection` is intentionally historical and should remain intact; current fields need explicit latest source/fixture/case associations and failure classifications before final qualification. This is evidence maintenance, not a discovered product-effect escape or permission to replace failed receipts.

## Recovered scope

The current and historical matrices have the same 46 IDs: 14 original requirements, six residual acceptance rows, 15 branch rows and 11 effect rows. These are overlapping views, not 46 independent tests. The full original issue, both historical comments and interruption comment were read from `recovery/github-recovery.json`.

The retained spec is absent from the current tree but was recovered read-only from Git object `845e4ab9f26efec6278682e72a64e656f807bb39:docs/rlgwo-execution/20261008/REMAINING_RLGWOs/R0016.md`; SHA256 `1b8a1181679911e282472826c89630b402f46ed2644c69b25fac52679287d901`. Its substantive author text agrees with historical comment 6074576487; differences are publication link expansion and the evidence-commit placeholder. The coordinator paragraph refines document-delivery ordering only; it does not waive native, integration, owner-approval or public-delivery acceptance.

## Dependency boundary

Read-only Git diff against dependency `bf566111fe530b5de2c7c63ca4586e83d5f4b965` confirms only three R0016 usage-comment additions per installer, with executable text unchanged. R0013 remains discovery/eligibility/terminal owner; R0015 remains staging/compiler/artifact/retention owner. Their native receipts are narrow reusable interface evidence, not R0016 whole-preview, full USERPROFILE, current-helper or variant-normal qualification. R0015 explicitly records this limit at `docs/state-contracts/R0015.md:125`.


## Source identity and receipt credit

The frozen candidate is commit `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`, tree `988d6191b24c6f64b6c71014a0077be1e48c4327`. Compared with the engineering dependency `bf566111fe530b5de2c7c63ca4586e83d5f4b965`, the installer changes are exactly three comment additions each; README replaces the short preview paragraph with the complete subsection. Authored and generated builder files are byte-identical, including the main-branch normal installer command and README pointer.

| File | SHA256 independently read from this checkout |
| --- | --- |
| `install.sh` | `9e0facbed4053dddbf676c58e4a07515371cdd7f35ad4d85164486d2c71fdb9c` |
| `install.ps1` | `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e` |
| `README.md` | `247584157214f155ad9c621a4d03ef1a65a072d6a8bff6ce32cc8ffe4390d8cf` |
| `src/native/builder.html` and `builder.html` | `66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e` |
| `tests/install-preview.py` | `5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760` |
| `tests/install-preview.ps1` | `1cb7eeea0f8e72ffb3ca8ef8492778dabef4d009474f26cfe5601c24f658094b` |
| `tests/install-preview-acquire-timed.ps1` | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` |
| `tests/install-entry-native-coverage.py` | `5f86fd9c3f93381b2f5aa43be26e6a0bb1a4e1d6b2293576a25b831dba2736f1` |
| `tests/install-entry-coverage-support.py` | `52a268b0de8c6055f8265faa7bdef115a78ba29fba2b4f008aba43be6b793c4a` |
| `tests/install-preview-native-controls.py` | `4bb3d2e046a626758b991eaf6237aff7fab891434fe33d2ed1ce1799264bbda0` |
| `current-acceptance-matrix.json` | `e6e44825754640802cf045f6fefd9501e2c719228bad2788706ea03f25b4a96b` |
| `historical-matrix.json` | `828638072d532c8e2e2167248c89d3ad19e707addac7db65e4742e4112e61dac` |

The last two files are under `docs/state-contracts/evidence/R0016/`. The complete original obligation texts and historical statuses remain authoritative data there; the table below supplies current source/test associations rather than replacing those texts.

### Permissible evidence reuse

- **R0013:** `docs/state-contracts/R0013.md:239-283` and `evidence/R0013/native-attempt-4/review-bindings-and-complete-denominator.json` retain actual Apple/Linux Bash and both Windows native discovery/entry evidence. They do not establish R0016's added containment, full-profile, compiler-helper or mutant-survival observations. The older PowerShell source hash is different. Reuse a named unchanged interface and actual case, not the R0013 disposition as a blanket assertion.
- **R0015:** `docs/state-contracts/R0015.md:109-129` and `evidence/R0015/native-attempt-6/whole-contract-matrix.json` retain actual native compiler/staging/security/lifetime evidence and four selected Windows normal/NoOpen full-file entries. Current R0016 executable text matches the dependency. Those four entries do not become the R0016 28-entry matrix or its 18 base/variant normal entries per host.
- **R0014:** Original deterministic selector/object and minimum-host obligations remain in `tests/install-powershell.ps1` and the retained 18-case component receipts. The eight newer route cases supplement them. No selector precedence/object rewrite is needed for R0016.
- **R0016 scoped receipts:** The current matrix binds Linux Bash 43/43 to the exact `5a3a...` test and `9e0f...` source. `current63-root-receiving.json` and `reviews/current63-receiving.json` bind Linux PowerShell 7.6.6's 63/63 to `1cb7...`/`b579...`; `reviews/current63-matrix-scope.json` assigns partial supplemental evidence to 34 obligations and none to 12. This is not native Windows or 46-row closure. Earlier 59/60-case observations remain at their original bindings.
- **Historical delivery:** The October raw/Pages readback remains valid historical evidence for its old bytes. It does not deliver changed README or the current executable stack. The existing engineering pin to `d96f878...` has its own source-download readback; accepted main and the builder's main-branch command are distinct consumers.

No false transfer of whole qualification was found in the explicit R0013/R0015/R0016 dependency prose. The concrete risks are current-ledger staleness (CR-03), failing native evidence being called merely pending, or treating the newly received full-file PS5.1 result as proof for separate core/mutant comparisons.

## Complete 46-row mapping

Abbreviations below are exact repository files: **B**=`install.sh`; **P**=`install.ps1`; **BT**=`tests/install-preview.py`; **PT**=`tests/install-preview.ps1`; **BE**=`tests/install-entry-bash.py`; **WE**=`tests/install-entry-native-coverage.py`; **WC**=`tests/install-preview-native-controls.py`; **RT**=`tests/install-powershell-routes.ps1`. Line numbers refer to frozen `65c995e1` bytes. “Scoped support” means source plus the retained Linux Bash/supplemental PS evidence described above, without current native or whole-row acceptance.

### Original requirements — 14/14

| ID | Retained obligation | Current source and discriminators | Current credit / specific remaining work |
| --- | --- | --- | --- |
| 22-01 | Options/platform before effects; eligible local plan; no terminal/staging; refusals/unresolved alternatives | B:55-64,752-803; P:19-30,1609-1658; BT:570-664,823-839; PT:559-572; WE:246-250,354-365 | Early boundary present and scoped support; CR-01 default-option hole, CR-02 combined-switch wording; actual native current matrix remains required. |
| 22-02 | Offline metadata/provider/download/availability prohibition; no cache authority | B:481-545; P:1133-1171,1326-1361; BT:331-386,455-568; PT:98-118,478-511 | Direct guards precede caches; separate denied transport from zero attempted transport. Apple targeted telemetry and Windows actual source-call/snapshot results remain separately bounded. |
| 22-03 | Every effect helper guarded, including cleanup; suppressed copy false | B:158-244,481-736; P:52-743,761-789,1133-1594; BT:706-759; PT:64-72,384-397,514-556 | Twelve Bash helper cases; 33 actual PS helper names/37 cases include new compiler custody. Native healthy core acquisition unresolved; existing failures remain failed. |
| 22-04 | No pretend artifact/path; callers stop before extraction/copy/fallback | B:516-545,562-580,628-661,713-714; P:1327,1364,1460,1494,1528; BT:752-758; PT:388-397 | Source suppression and return-shape controls present; no bypass of actual caller guards needed. Native effects and useful normal consumer evidence remain distinct. |
| 22-05 | Complete fresh/cache/source/installed/preset/refusal branches | BE:257-261; BT:823-842; PT:559-572; WE:15,192-250 | Existing fresh class and newer always-cached sentinels are distinct. All named rows retained; CR-01 adds an omitted invalid environment-default subcase. |
| 22-06 | Independent names/modes/bytes snapshots plus effect/transport observation, separate harness state | BT:136-163,331-386; PT:33-50,315-384; WE:105-118,252-313,353-357; entry support:66-126,221-267 | No filename whitelist in complete USERPROFILE. Native core snapshot failures are not erased by host-only activity or a coarser full-entry snapshot PASS. |
| 22-07 | Useful normal and NoOpen exact downloads/staging/configuration/copy/manual consumers | B:205-244,660-736,803-881; P:761-789,1493-1594,1687-1729; BT:762-784; WE:325-353; WC:319-424,487-506 | R0015 normal interface is reusable with explicit binding. R0016 exact native base/eight-variant normal survival remains unestablished when core healthy prerequisites fail. |
| 22-08 | Causal eager/cache/copy/EXIT-cleanup mutants with healthy positives | BT:787-880; PT:425-472,575-608; WC:171-239,487-506 | Six Bash mechanisms/eight PS pairs include actual clipboard attempt. Native failure before named oracle or failed healthy partner earns no mutation credit. |
| 22-09 | Actual Apple Bash3.2/Linux and native PS5.1/supported7 full-file qualification | BT:230-280,331-357; WE:24-29,395-410; native1 evidence | Historical real hosts retained; current extended Apple bootstrap incomplete, Windows core/variant native gates unresolved. No host substitution. |
| 22-10 | Compose R13 terminal/discovery, R14 host/selector, R15 staging/lifetime | B:158-192,391-480,773-803; P:52-743,1083-1171,1632-1688; compiler-interface review | Comment-only R16 delta verified. Reuse exact interface receipts; do not redo siblings or turn draft prerequisite branches into accepted-main integration. |
| 22-11 | Honest would/unresolved/refusal/replacement/manual-pending wording | B:773-800,874-881; P:1632-1654,1719-1726; BT:639-661; PT:399-413; WE:349,358-365 | Primary wording present; CR-02 combined NoOpen plan mismatch. No browser install/import completion was observed or claimed. |
| 22-12 | Script usage + README/builder policy consistency and NoOpen distinction | B:6-12; P:5-11; README:86-151; builder source:370-390 | Missing prose has been authored; malformed-option text now present. Local rendered/copy-context review and final delivery remain open; CR-01 contradicts the broad refusal sentence. |
| 22-13 | Preserve configuration/manual boundary/card/permissions; only wrapper amendment superseded | builder source:204-219,377-390; README:71-81; B:645-656; P:1391-1489; WE:342-344 | Only older outer wrapper constraint is superseded; 325x530 card, geolocation, encoding and manual boundary remain binding. No geometry change requested. Native current configured-preset consumer/final preservation review remain required. |
| 22-14 | Exact final public script/document/generated-command byte identity | README:57-64,91-124,149-151; builder source:370-390; historical distribution evidence | Final integration/public delivery gate, not a native helper gate. Current commit/tree, advertised raw/Pages/GitHub rendered and copied-command consumers require authorized readback. |

### Residual acceptances — 6/6

| ID | Retained obligation | Current source/test association | Current credit / remaining work |
| --- | --- | --- | --- |
| R0016-A01 | Actual Apple entire-entry preview/effect/snapshot/no-artifact/no-prompt classes | BT:230-280,331-386,570-664,823-839; BE:257-261 | Full extended Apple acquisition remains open; unchanged original native cases may be rebound individually. |
| R0016-A02 | Apple no-terminal/refusal and normal/NoOpen actual consumer separation | B:773-803; BT:666-703,762-784,830-845; BE:262-274 | R13/R15 named actual normal receipts may be imported with source/fixture/input identity; new containment/refusal/interruption observations cannot be inferred. |
| R0016-A03 | Apple parse-valid eager/cache/copy/cleanup mutants and healthy controls | BT:787-880 | Actual Apple causal pairs remain open; terminal bootstrap failure is not a product or mutation result. |
| R0016-A04 | Exact Linux/Windows historical source/fixture/input/environment association | historical matrix; R13 native4 and R15 native6 bindings; current63 receipt/scope map | Preserve old observations and rebind only unchanged relevant interfaces. Changed PS compiler source cannot inherit an old complete-file receipt. |
| R0016-A05 | Complete precise preview/NoOpen README and builder agreement | README:86-151; B:6-12; P:5-11; builder source:370-390 | Static text and authored/generated agreement present. CR-01/02 deserve bounded confirmation; actual rendered/readable copied-command context remains open. |
| R0016-A06 | Authorized final raw/Pages/GitHub delivered bytes and rendering | final delivery/readback certificate, not yet supplied | Separate final integration/owner merge/public exposure gate; no fresh native rerun follows from documentation-only changes. |

### Branch matrix — 15/15

| ID | Branch/control | Current source/test association | Current credit / remaining work |
| --- | --- | --- | --- |
| P01 | Fresh GitHub Chromium/Firefox | B:785-789; P:1641-1644; BE:257-258; WE:216-225,247-250 | Maintained entry fixtures provide true fresh classes; newer helper/wrapper fixtures always seed cache. Bind actual native case evidence accordingly. |
| P02 | Cached assets/metadata/unpacked/preset | B:483,518,580,629; P:1134,1147,1327,1364,1460; BT:282-329,722-759; PT:268-313; WE:228-233 | Guards and malformed/current-owned sentinels covered; full-entry legacy cache directory alone does not exercise current artifact admission shortcuts. Native core still required. |
| P03 | Store preview | B:788; P:1643; BT:824-825; PT:560-563; WE source parameter | Scoped plan/no-effect support; combined NoOpen wording is CR-02. |
| P04 | Ask preview | B:787; P:1642; BT:647-648,824-825; PT:406,560-563; WE:363 | Unresolved alternative preserved; exact native zero-prompt/no-effect observation remains separate. |
| P05 | Already installed | B:785; P:1641; BT:827-829; PT:565-567; WE:219 | Existing installation bypasses asset plan; preset/manual warning retained. No browser-import completion proof. |
| P06 | Missing preset | B:792-793; P:1646-1647; BT:653-654,833; PT:413,569-570; WE:247,365 | Explicit missing-preset paths tested, no helper artifact supplied; native PS return/output and source binding remain required. |
| P07 | Mixed legacy/eligible | B:779-784; P:1636-1640; BT:827-829; PT:565-567; WE:223 | Eligible peer plans survive and legacy remains refused; no global target success inference. |
| P08 | Legacy only | B:779-780,798; P:1637,1652; BT:830-832; PT:565-567; WE:218,358-359 | Explicit nonzero refusal; exact native snapshots and no-effect observation required. |
| P09 | Zero target | B:752-757; P:1612-1615; BT:830-832; PT:565-567; WE:216,358-359 | Early explicit refusal; not a successful empty plan. |
| P10 | Malformed options | B:62-64; P:25-26; BT:834-836; PT:571-572; WE:247-249 | Explicit PS parameter test present; invalid environment-derived default omitted (CR-01). |
| P11 | Unknown mixed/only, malformed/missing/unreadable metadata/parser | B:284-397,470-476,779-781; P:1006-1091,1638; BT:827-839; PT:565-567; WE:314-324 | Keep actual native sharing32/readable-peer pair distinct from parser-only/unreadable-directory simulations; mixed-known peer wrapper remains separate from unreadable-only full entry. |
| P12 | Failure, EXIT and signals | B:177-192; P:222-255,720-743,1727-1729; BT:666-703,840-842; PT:520-521,538 | Actual Bash post-trap failure/INT/TERM and PS cleanup contexts covered in design. Native results remain host-specific; no artificial fallthrough beyond preview exit needed. |
| N01 | Normal GitHub | B:679-710; P:1548-1587; BT:762-784; WE:325-353 | Inherited exact normal consumers can be reused; current native R16 variants require their own useful normal controls. |
| N02 | Normal NoOpen | B:208-210; P:762-764; BT:845; BE:269; WE:348; WC:487-506 | Only open calls disappear; retain downloads/configured outputs/clipboard/manual prompts. Failed core pair blocks variant credit even when base normal passes. |
| N03 | Normal store/ask/fallback | B:660-685; P:1527-1551,1588-1592; BE:266-268; RT; original PS18 components | Eight route cases supplement original selector/fallback contract. Use exact native route receipts; no need to repeat unrelated predecessor work. |

### Effect matrix — 11/11

Every row retains the shared contract: zero preview effect, no usable artifact, false suppressed copy, and diagnostics separated from success values where that return contract applies.

| ID | Current guarded owners | Discriminators / current gap |
| --- | --- | --- |
| initialize | B:158-174; P:52-53,86-87,132-133,145-146,161-162,256-258,332-334,556-687 | BT helper initialize + eager mutation; PT:514-537 including actual compiler helper calls. Native current first-guard/held-context observations still required. |
| cleanup-and-exit | B:177-192; P:222-255,720-743,1727-1729 | BT interrupted/error/trap and cleanup mutation; PT compiled/failed non-null context + cleanup pair. Existing host-change failures receive no success credit. |
| clipboard | B:229-244; P:781-789 | Exact false/empty return tests plus actual clipboard-attempt mutant; normal exact copied paths at WE:340. False-success mutation alone is insufficient. |
| browser-open | B:205-227; P:761-779 | BT/PT direct open; WE:348 and variant normals. No real browser launch; CR-02 addresses combined-mode wording only. |
| metadata-selector | B:481-514; P:1133-1171 | PT preloaded release sentinel and direct selector suppression; retain R14 selected-original-object/tier tests. No cache metadata authority under preview. |
| download-cache | B:516-545; P:1326-1361 | Current-owned cache sentinels and early-return mutant; root entry bypasses artifact helpers. Native returned-path/oracle credit separate from unchanged old cache. |
| validate-retain | B:548-576; P:601-684,1174-1210 | BT validate/retain; PT digest/ownership/admission/publication. No invented preview-ready predicate and no reimplementation of R15. |
| extract | B:579-625; P:1237-1323,1363-1389 | BT malformed cached archive; PT archive-validation/extraction/unpacked-cache guards before bytes parsed. Native remains required. |
| preset-write | B:628-657; P:1459-1489 | Cached/malformed and missing-preset suppression, normal canonical configured preset at WE:342-344. Sentinel bytes are not canonical positive bytes. |
| manual-install-fallback | B:660-710; P:1527-1594 | Direct guarded ask helper, entry store/ask plans and RT actual normal choices; no preview confirmations/fallback opens. |
| manual-import | B:713-736; P:1493-1524 | Direct helper/entry suppression plus normal path admission/clipboard/manual warnings. Browser installation/import remains outside observed completion. |

## Native acceptance frontier versus final lifecycle gates

### Native acceptance still to resolve

1. Preserve the original Linux acquisition failures: missing Bubblewrap in run 43036427882, then package acquisition failure before the unchanged collector in run 43047681007. Neither supplies preview product observations. Existing exact Linux Bash43 evidence is still scoped evidence and must not be erased.
2. Preserve the original Apple pre-preview terminal bootstrap timeout and focused same-profile/host-control diagnostic. No successful extended native preview, no-effect/mutant or terminal teardown outcome follows from a child marker written before exit. Correct the instrument only from a measured discriminator; keep actual Apple Bash3.2, containment and original subject budget.
3. Preserve actual Windows core subject-change results. The precise PS5.1 versus PS7 fields need their respective original receiver reports; they are not interchangeable. A host-only baseline identifies activity without installer execution, not the writer or operation for every product-window delta.
4. Admit PS5.1's actual full-entry result only at its own observed scope. The parallel original receiver's PARTIAL report currently records 14/14 full-entry rows passing, while all 67 core product children fail and the variant companion refuses prerequisites. That report is not independently re-executed or finally accepted by this reviewer. A full USERPROFILE comparison and the separate subject snapshot have different field inventories; neither overrides the other.
5. Preserve 18 base/eight-variant normal entries per Windows host as a separate requirement. The companion correctly requires healthy same-host core prerequisites. There is no basis to credit eight mutant pairs merely because the code contains intended changes or existing R15 normal entries pass.
6. Before final qualification, root should obtain bounded actual-source confirmation of CR-01 and CR-02, then invalidate/requalify only affected entry/wording paths if repaired. Neither finding justifies rewriting R0013/R0015.

The independently assigned detailed original receivers own `/tmp/r0016-successor-20261111/recovery/posix-originals-review.md` and `/tmp/r0016-successor-20261111/recovery/windows-originals-review.md`. Their final byte/case decisions should supersede provisional observations from the interruption comment. This report deliberately supplies contract associations rather than duplicating their full artifact receiving.

### Final integration, owner merge and public delivery

These are separate from native test acceptance and do not become new product failures:

- Reconcile then-current prerequisite source, campaign integration order, accepted main, all source/test/fixture/evidence hashes, and the complete 46-row disposition. Preserve R0013 33/R0015 51 ledgers and their own remaining gates; do not mark them complete by dependency consumption.
- Obtain separately attributed final exact-candidate review. Recovered receipt/source review is bounded and does not confer release or closure authority.
- Complete local rendered README and builder copied-command context review. The original spec explicitly permits accurate documentation to be reviewed/delivered before unrelated native proof under existing authority; documentation is not forced into a duplicate native campaign.
- Root owns exact required owner merge approval and accepted-main integration. Current published engineering branch, draft prerequisite PRs and current task authorization are not themselves those readbacks.
- Bind actual merged/advertised raw scripts, Pages/GitHub rendered instructions and generated builder command to the reviewed final target. Retained prior public bytes and current pinned-source downloads remain individually attributed.
- Only after every mandatory row and required delivery is supported: truthful complete certificate/evidence comment, then deliberate manual issue closure with actual readback. No automatic closing PR keyword.

## Review conclusion and limits

The 46-row contract is present, coherent and recoverable; no row was dropped. The recovered early preview branch plus local helper guards compose the actual R0013/R0015 interfaces without duplicated staging/discovery implementations. The review found one concrete high-confidence validation defect inferred from source plus the language contract (CR-01), one bounded selected-action wording discrepancy (CR-02), and a current-ledger reconciliation need (CR-03). Both product findings require root's controlled confirmation; this worker ran no tests.

No claim is made that the observed native runtime/cache writes are caused by installer source. No failing receipt is relabeled, no missing native observation is supplied by another host, and no new whole-contract/native/merge/delivery/closure verdict is conferred. The root must reread the exact source and independently received evidence before action.

Final source identity readback: reviewed source/README hashes unchanged.
