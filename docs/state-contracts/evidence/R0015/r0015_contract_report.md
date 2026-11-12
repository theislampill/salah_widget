# R0015 read-only contract, recovery and security audit

Date: 2026-11-11. Reviewer: `/root/r0015_contract`. Source pin: `theislampill/salah_widget@dbf3370f39d569936ae74ad795638525b53ccd98`. This is an intake/contract report, not an implementation acceptance, native test execution, merge approval or closure certificate. Root is the sole shared-installer writer. No installer, shared README, branch or GitHub object was changed by this audit.

## Decision-relevant findings

**FACT / PASS (scoped historical reuse):** The current Bash and PowerShell installers and six installer test files are byte-identical to the exact source/fixtures recorded by the October native acceptance. All sixteen published retained receipts were reacquired from the immutable accepted evidence commit and independently matched against every `CUSTODY.json` SHA-256. The verification is in `recovery/r0015_contract_inputs/custody_rebind_verification.json`; raw receipt bytes are in `recovery/r0015_contract_inputs/receipts/`. This is fresh byte verification of historical executions, not a fresh native run.

**FACT / GAP:** Original parent rows `21-03` (actual Apple/Bash 3.2/BSD utility/filesystem qualification), `21-05` (isolated foreign-UID retained-HOME admission), and `21-15` (complete README lifecycle prose) remain required. They are explicitly retained by [October residual specification 6074575663](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6074575663), lines 48, 151–215 in the recovered copy. No Apple waiver/deferral was found in the full live issue body or all three comments. Retained Apple evidence is explicitly BLOCKED; this report does not claim to have exhausted the root agent's current host-discovery options.

**FACT / GAP:** Current `install.ps1` still contains all CF01/CF02/CF03 mechanisms. An existing download filename is enough for success (345–360); replacement deletes the old unpacked directory before extraction (363–380); malformed preset JSON is warned about then returned (394–409). These are source-confirmed defects, not newly executed native failures.

**FACT / scope:** The November amendment adds Windows transaction requirements while preserving original Bash acceptance. Existing Bash private roots, confinement, validation, cleanup and retention should be received and rebound, not rewritten. The new record should provide one R0015 artifact admission contract consumed by R0013, with R0016 guarding every effect. [Amendment 6700332793](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6700332793), recovered lines 25–29, 69–83, 125–137.

The companion JSON is `recovery/r0015_contract_matrix.json`: 17 original rows, 9 binding residual children, 18 November ES rows and 7 terminal obligations. PASS below means the stated baseline/historical scope only; changed final source or caller boundaries require affected requalification. GAP means missing implementation or proof. BLOCKED on Apple rows means the retained native acquisition/proof gap, not permission to stop other authorized work.

## Read set, authority and custody

Read completely: `recovery/contract/prompts/11_R0015_EXECUTE.md` (786 lines), `specifications/R0015_FULL.md` (708 lines), `contracts/COMMON_EXECUTION_CONTRACT.md` (139 lines), live issue #21 body, and all three live comments `6073056099`, `6074575663`, `6700332793`. A literal-content check confirmed that the full specification is contained in the execution prompt and the common contract is contained in the full specification. The source-bound CF01/02/03, C11/C12, C08/C09/C10 records and ten-owner crosswalk were read.

Live issue readback: OPEN; three comments; latest update 2026-11-07T01:27:38Z. Recovered copies and metadata live under `recovery/r0015_contract_inputs/`. The current source files and canonical preset were fetched through `github_fetch` at the exact immutable main SHA, then compared with the shallow checkout using read-only `git show`.

The current commission's operational continuation supersedes the old planning-only/PR-only stopping clauses, while technical criteria and valid owner exceptions remain. It requires whole-owner reconciliation before exact merge approval, actual merge/delivery, certificate and completed issue-state readback. Root retains governance and external-action control; this report cannot mint those receipts. Prompt lines 13–23 and 64–74; common contract lines 12–34, 85–119, 123–135.

Repository/evidence text was treated as evidence rather than executable authority. No secret material was sought or printed. No instruction-injection text requiring separate escalation was identified in the reviewed contract/source slice; this is not a repository-wide prompt-injection scan.

### Exact source and receipt identities

| Item | SHA-256 / identity | Scope |
| --- | --- | --- |
| Current `install.sh` | `9c3fd523bbd77f3080097ddbd142b7e966795befd008daa36fbfb9f8f1ca1cee` | Identical to historical accepted Bash source |
| Current `install.ps1` | `d4d0cd3efef8a1b22f66d4317e464cfe9af667db59b2bddb2f70ebf12a278215` | Identical to historical parser/selector/preview source; no transaction qualification |
| Canonical preset | `9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f` | Actual field/iframe schema binding |
| Historical `CUSTODY.json` | `3dc4fe696dd6b6bdc825d4338038a1a013c1a98972194a7ca62006c1b69ef407` | 16 fetched receipt hashes all match |
| Historical helper receipt | `dca1b3c9ae2e252c337bbdcaa9181e845a2f8c14924c1be728ed5e91a30e954e` | 26 Bash helper cases |
| Historical peer-DAC receipt | `0bdb778da97010e7f3845a6903bc13583e25e7e003f628fab5bf1a9d3e229b84` | 49 distinct-UID operations |
| Historical applicability | `16e281a1aa38236804936d6a78013230128fe65f3ac6d4572375b79120dd255a` | Explicit native scopes and Apple absence |

Six test files whose current bytes also match historical binding: `tests/install-bash.py`, `tests/install-entry-bash.py`, `tests/install-entry-native.py`, `tests/install-powershell.ps1`, `tests/install-powershell-guards.ps1`, and `tests/install-mutations.py`. Exact hashes are in the verification JSON. Historical evidence source is [native-rebind.json](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/native-rebind.json) and [CUSTODY.json](https://github.com/theislampill/salah_widget/blob/b879573c298f19189d1f2392108b8b9f3b2cda0b/docs/rlgwo-audit/20261008/workers/E/retained-install/CUSTODY.json).

## Historical reproductions and accepted native evidence

The original overwrite witness used `fd2972ba64225fe9d6848e92497e6d0ed20ea624` and candidate `9d9c43649748555afbe09e3ca49bc47db2d7e7bb`, both with installer SHA-256 `89d919e365846ec5e3b31a0ed4a41f95e3364659336c04ab1f066abcd1173e63`; extracted LF `download_preset` hash `e47e541250c0a6cd61840f0c82337507dd8a59703fd0e18c61ba3f7cd6efcde2`. A fixture prepared the predictable preset as a symlink to its own sentinel. The exact initializer/helper followed it, wrote harmless configured JSON, returned exit 0 and left the symlink intact. Scope was WSL Ubuntu on **DrvFS**, local `file://` curl, no second UID, no normal wizard or browser. It establishes an installer-user-writable overwrite primitive only. Original issue recovered lines 15–76.

The repaired Bash controls use private scratch under trusted TMPDIR and a separate retained HOME bundle. The accepted canary proves unchanged victim and old symlink while valid configured JSON is produced in the new root. Other accepted controls cover component confinement, preflight before any archive output, same-attempt cache reuse, fresh next-attempt roots, cleanup identity refusal and retained bundles. Accepted audit [6073056099](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6073056099), recovered lines 54–70.

| Historical execution | Accepted observation | Limits retained |
| --- | --- | --- |
| WSL2 Linux kernel 6.6.87.2, Bash 5.2.21, native `/tmp` ext2/ext3 | 26 helper cases; 23 actual-entry cases; 28 normal versus 24 NO_OPEN effects | Not DrvFS; not Apple; not current execution |
| Distinct native Linux UID1000 owner / UID65534 peer | 49 operations: 30 EACCES(13), 19 allowed positive/reachability controls; no supplementary groups/caps; sentinels unchanged | Proves created-root DAC, not same-UID isolation or separately isolated foreign-HOME admission |
| Original owner exit and fresh UID1000 consumer | Both exit 0; retained manifest/preset/payload/XPI bytes and identities readable after source exit | Later readback reports `fixtureExists=false`, cause unknown; no reboot, permanent liveness or real-browser loading claim |
| Windows PS 5.1.26100.9444 / PS 7.6.6 | Exact-file parser and selector/component 18 cases each; direct-entry total 24 | Existing R0014/R0016 scope, not new Windows staging/transaction/security acceptance |
| Apple `/bin/bash` 3.2, BSD stat/mktemp, native filesystem | Not observed in accepted applicability | Linux PLATFORM=mac mocks and alternative shells do not close this cell |

Historical mutations retain real behavioral detection: cached-status-stdout, mapfile restoration, stdin-human-read, eager staging, retained deletion, symlink admission, archive-parent member and preview cleanup. Syntax passed before fixture failures. The original audit also records a separate predictable-root mutant whose processes complete but roots repeat, detecting freshness without treating a bootstrap failure as evidence. `receipts/bash-mutations-archived-source.json`; accepted audit lines 67 and 115–116.

Current baseline failure reported separately by root: `python tests/install-bash.py` has only the wrong-owner-HOME control failing. The unchanged source and historical confounded fixture mean it must be diagnosed as a fixture/environment question before assigning a product regression. The required replacement discriminator is specified below; no baseline failure has been converted to PASS in this intake.

## Current source defects and smallest bounded countermeasure

### PowerShell source-confirmed gaps

1. **CF01 / admission and reuse:** `Download-Asset` creates a reusable tag directory with `-Force`, returns any `Test-Path` destination, and writes directly to that destination (`install.ps1:345–360`). There is no validation/attempt/source binding; URL/id/size changes under the same sanitized filename alias. **Countermeasure:** create one fresh attempt boundary, download an exclusive partial, check reliable expected size when supplied and actual archive structure, record admitted bytes, publish only after success, and reuse only the same validated identity with current regular-file readback. No persistent cache database is needed.

2. **CF02 / destructive replacement:** `Expand-ChromiumAsset` removes the old directory at 367–369; `Expand-Archive -Force` precedes a filename-only manifest search at 371–380. **Countermeasure:** validate the input through the single admission owner; create a fresh empty owned extraction directory; preflight supported archive members and output confinement before writes; validate the intended manifest as JSON/required shape; return the new path only after admission. Do not delete the predecessor after success either. Rename/move does not by itself justify universal atomicity/crash-consistency claims.

3. **CF03 / malformed preset success:** inner parse catch warns but line 409 returns the preset. `Show-ImportInstructions` then copies/prints paths and opens the new tab; even null receives generic “select the file above” guidance (`417–442`, main `606–607`). **Countermeasure:** parse/shape/target/fragment validation is an actual success gate; fail coherently with no ready path and no path-specific import guidance. Keep the normal valid preset useful and the dashboard-replacement warning.

4. **Confinement/custody:** predictable `$env:TEMP/SalahWidgetInstaller` and `New-Item -Force` (`41–46`) supply no invocation ownership or reparse isolation. Download, extraction and preset consumers likewise lack such guards. **Countermeasure:** fresh exclusive roots and attempt-local identity; reject or isolate foreign/preexisting/reparse/escaping paths before effects; guard current ownership before write/publication/cleanup. Use a separate retained manual bundle outside ephemeral scratch; cleanup never recursively resets a preexisting tree.

5. **Configuration/Unicode:** `.Replace("local=1", $WidgetHash)` changes every occurrence (`399`); reads at 399/404 omit explicit UTF-8 decoding. The latter is a **source-observed risk requiring native Unicode discrimination**, not a fresh measured corruption claim. Serialize parsed JSON with supported PS5.1 behavior, preserve Unicode data/path and exact encoded fragment meaning, and never text-convert binary archives.

6. **Caller eligibility:** current target objects expose only old boolean flags (`268–300`); pre-staging check `580–584` excludes legacy only. Unknown-held state is absent. This is the R0013 producer dependency, not authority for a second R0015 discovery implementation.

### Exact preset contract

At pinned `presets/salah-widget.tablissng.json:2–9`:

- `widget/orpul7IDXSSP` has `id="orpul7IDXSSP"`, `key="widget/html"`, order 2 and display metadata.
- `data/orpul7IDXSSP.input` is the HTML iframe string.
- Intended `src` is `https://theislampill.github.io/salah_widget/#local=1`.
- The same iframe carries title, referrerpolicy, geolocation permission, 325×530 styling and scrolling behavior.

The bounded implementation should bind this canonical widget/data relationship and require exactly the intended iframe/URL target before changing its fragment. A dynamic equivalent may identify the supported `widget/html` record and corresponding data id, but must reject ambiguity/missing payload rather than selecting an arbitrary unrelated iframe. Preserve every unrelated JSON field, optional field, string containing `local=1`, Unicode and encoded hostile-looking literal label. Do not execute payload strings. Reparse serialized output and verify the exact intended fragment after the serializer/URL boundary. This is staged-preset shape proof, not a guarantee that every browser imports it.

### Bash preservation and source limitations

Bash trusted-root and output chains (`80–189`, `421–563`) are exactly the accepted source. Its global raw replacement at `554` remains a source fact; generic schema/target precision is not established by the old simple configured-preset positive. The November increment explicitly prefers the PowerShell extension and forbids broad reimplementation of earned Bash staging. Any Bash change therefore needs a demonstrated same-owner interface necessity, affected scope binding and corresponding requalification. There is no new demonstrated Bash security regression in this report.

## Required owner interfaces

| Interface | Producer and consumer | Required boundary |
| --- | --- | --- |
| Eligible target | R0013 discovery/selection → R0015 transaction | Explicit Status `known-new/known-legacy/known-both/known-neither/unknown`, bounded reason, identity/evidence/matches; separate Eligibility `eligible-known/legacy-refused/unknown-held/not-applicable-no-profile`. Only eligible-known can stage; known-both refuses; mixed populations still process independently safe targets. |
| Admitted artifact | R0015 helpers → R0013 install/import/path consumers | One admission owner. Nonempty string means admitted current bytes or a coherent typed result migrated across every caller. R0013 does not reimplement existence/readiness logic. |
| Private same-attempt cache | R0015 owned root → R0013 stdout path contract | One fresh verified DOWNLOAD_ROOT per attempt; first/second asset call exact same path/bytes, no repeat acquisition; diagnostics remain separate; next attempt fresh; old retained bundle not cache. |
| Preview | R0016 guard → all R0015 entry/helper/cleanup paths | Guard before any new root creation/probing, download/cache shortcut, extract, rewrite, retained-copy, clipboard/open or cleanup. No pretend usable path sent to normal extraction. |
| Apple native fixture | R0013 platform + reviewed helper/entry adapter → R0015 A01–A04 | Actual Apple Bash3.2/native utility/volume provenance, effect interception and pre/post snapshots; entire upstream issue need not be a circular interface prerequisite. Commission's serial-order receipt remains root-owned. |
| PS parser/selector | R0014 → R0015 | Preserve exact-file PS5.1/supported7 encoding and selector object/priority/fallback contract; filename/signed-name preference is not cryptographic authenticity. |
| README/shared tests | Root integrator | One writer; lifetime/preview/selection/encoding text remains coherent. No scientific/runtime generator work is necessary for root installer/test/docs-only changes. |

R0013 [amendment 6700319084](https://github.com/theislampill/salah_widget/issues/19#issuecomment-6700319084), recovered lines 32–75 and 101–113, establishes this exact eligibility separation. R0016 source-preservation sites are Bash `155–177,202–241,386–388,421–566,618–619,678–700` and PS `44–46,65–93,303–318,345–418,444–445,540–560`; preview returns before terminal/staging. Its accepted Linux/Windows zero-effect receipts are available in the custody set. Actual Apple preview remains a distinct evidence gap and is not transferred from Windows/Linux.

## Native foreign-owner discriminator (21-05 / A05–A07)

The binding recipe is October residual comment recovered lines 108–110 and 190–192. Use an authorized disposable existing privileged native Linux environment. Do not change actual HOME, accounts, real profiles or broad host permissions. Root-owned mode0755 reachable, nonsymlink ancestors are permitted by the source. Subject UID1000 has its own TMPDIR mode0700. Negative HOME is root-owned mode0755: reachable and not group/world writable, so mode cannot explain rejection. The exact source initializer must reject at the final retained-parent ownership predicate before any mktemp/download/output, with unchanged sentinels. The matched positive changes HOME owner to subject UID with the same mode and common trusted ancestors, produces mode0700 private roots, performs a guarded retained write, cleans scratch and permits fresh owner consumption.

For the mutation, remove **only** terminal HOME self-owner admission and run the actual `trusted_parent "$HOME" home` helper. The mutant must return the foreign parent whereas original refuses. Do not use subsequent mktemp failure as the mutant oracle: ordinary DAC on UID0/mode0755 HOME can still prevent creation and conceal the missing admission. This missing predicate-specific evidence is separate from already accepted peer-DAC49.

## Complete original matrix

| ID | Status / disposition | Mandatory result | Current observation / next discriminator |
| --- | --- | --- | --- |
| 21-01 | PASS | Create fresh private scratch and a separate retained HOME bundle only after platform, input and eligible-target checks; never admit the predictable old tree. | Recheck only changed R0013 eligibility/caller boundary on the eventual integrated candidate. |
| 21-02 | PASS | Verify parent and ancestor ownership, modes, symlinks and physical identity using the native stat/id/-O/-L contract; unusual mounts fail closed. | Preserve native stat forms and fail-closed unusual-mount behavior; separate 21-03 and 21-05. |
| 21-03 | BLOCKED | Qualify the actual macOS BSD stat/mktemp, Apple Bash 3.2 and filesystem staging branch. | Acquire authorized actual Apple host/adapter; run A01-A04 with native filesystem provenance. Current host availability is root-owned, not determined by this report. |
| 21-04 | PASS | Confine all outputs and cleanup to verified roots; reject symlink components, nonregular outputs, empty/dot/parent components and prefix lookalikes. | Preserve current guards; affected native integration only if source/interface changes. |
| 21-05 | GAP | Separately discriminate wrong-UID retained-parent admission from writable-mode refusal. | UID1000 negative HOME UID0/mode0755 with root-owned0755 reachable ancestors and UID1000 TMPDIR0700; matched HOME UID1000 positive; terminal self-owner-only mutant tested at trusted_parent return. |
| 21-06 | PASS | Preserve the exact hostile old preset symlink and victim while producing valid configured JSON in a fresh owned bundle. | Preserve healthy JSON and hostile old tree; no need to rerun unchanged original witness solely for count. |
| 21-07 | PASS | Keep the asset/preset write chain closed: owned fresh partial, validation before publication, exact configuration, no usable artifact on malformed input. | Do not transfer this Bash acceptance to PowerShell transactions or cryptographic authenticity. |
| 21-08 | PASS | Preflight all archive members before extraction; reject absolute paths, traversal and links, then extract into a new empty child and return a valid in-root manifest directory. | Preserve traversal/absolute/backslash/link/malformed/missing-manifest controls and earlier-marker refusal. |
| 21-09 | PASS | Retain legitimate same-attempt cache reuse but create new private roots on each invocation and retire old shared-cache admission. | R0013 owns stdout bytes; R0015 owns one admitted private root per attempt. Do not turn retained bundle into cross-run cache. |
| 21-10 | PASS | Retain completed or explicitly partial manual bundles through exit, failure and interrupt; cleanup removes only unchanged owned scratch. | Never adopt retained-bundle deletion on exit, interrupt, failed retry, or successful replacement. |
| 21-11 | PASS | Prove retained filesystem consumption after source exit and a fresh consumer; keep it distinct from printed paths, later liveness, reboot and browser installation. | Keep time-bound filesystem-consumption claim; no reboot, current liveness or installed-browser claim. |
| 21-12 | PASS | Support the cross-user boundary with native Linux filesystem semantics, distinct UIDs and reachable positive controls; do not claim same-UID isolation. | Preserve accepted native DAC scope; not DrvFS, same-UID isolation, Apple or Windows proof. |
| 21-13 | PASS | Keep dry-run outside both staging roots and all write, acquisition, extraction and cleanup paths; never return imaginary artifacts. | Guard every new effect before root creation/probing, cache shortcut, extraction, rewrite and cleanup. |
| 21-14 | PASS | Use predictable-root, symlink-admission and retained-EXIT-deletion mutants to discriminate freshness, confinement and lifetime separately. | Retain real-consumer falsifiers and healthy original. Bootstrap/parse errors do not count as guard discrimination. |
| 21-15 | GAP | Disclose retained HOME bundle lifetime, keep-unpacked instructions, optional manual preset/XPI removal, partial retention and retired cross-run cache behavior in README. | Add accurate shared README lifecycle paragraph; independent rendered/prose and delivered-byte review (A08-A09). |
| 21-16 | PASS | Preserve exact configuration, manual dashboard warning, card and permission contracts; apply only the supplied outer-wrapper amendment. | Preserve card/permissions/encoded configuration/manual dashboard warning. Revalidate changed PS targeted update without changing geometry. |
| 21-17 | GAP | Bind the delivered public script/document and generated-command source bytes to the exact reviewed target. | After approved integration, read back only affected public script/docs and copied-command consumer bytes; preserve unchanged runtime scope. |

## Binding October residual children

| Child | Parent | Status | Required result |
| --- | --- | --- | --- |
| R0015-A01 | 21-03 | BLOCKED | Actual Apple root/owner/mode/identity, stable same-attempt/distinct new attempt |
| R0015-A02 | 21-03 | BLOCKED | Actual Apple confined writes/extraction and unchanged hostile sentinels |
| R0015-A03 | 21-03 | BLOCKED | Apple exit/failure/INT130/TERM143 and fresh retained file consumption |
| R0015-A04 | 21-03 | BLOCKED | Apple native guard/lifetime mutants matched with healthy positives |
| R0015-A05 | 21-05 | GAP | UID1000 subject rejects reachable UID0 HOME0755 before any staging effects |
| R0015-A06 | 21-05 | GAP | Matched self-owned HOME0755 succeeds; native roots0700/scratch cleanup/retained readback |
| R0015-A07 | 21-05 | GAP | Remove only terminal HOME owner guard; actual helper wrongly admits foreign HOME |
| R0015-A08 | 21-15 | GAP | Rendered README truthfully documents precise manual/cache/partial lifecycle |
| R0015-A09 | 21-15 | GAP | Affected public docs/scripts bytes and rendering match approved final candidate |

## November ES15 matrix

| ID | Baseline status | Required result | Actual source / next discriminator |
| --- | --- | --- | --- |
| ES15-01 | GAP | Failed partial download never reused as ready merely because file exists | Actual failing downloader writes a partial then throws; second call must not return it. Use distinct owned candidate and admit only completed validated bytes. |
| ES15-02 | GAP | Healthy validated candidate returns one actual owned path, no diagnostic contamination | Healthy valid archive returns exactly one regular owned admitted path; diagnostics stay off success pipeline; actual helper plus caller tested. |
| ES15-03 | GAP | Same-attempt same validated identity reuses exact bytes/path without repeat download | Same attempt+asset identity+actual digest/readback returns exact path with zero second acquisition; preserve useful positive. |
| ES15-04 | GAP | Changed/cross-run/unverified artifact cannot inherit readiness by filename | Fresh attempt roots/receipts; changed URL/id/size/name identity and cross-run unknown file cannot inherit admission; no blanket old-cache deletion. |
| ES15-05 | GAP | Replacement failure leaves old usable sentinel/manifest unchanged | Fail download/extraction/manifest/publication at actual functions; prior sentinel,manifest,payload remain byte-identical and accessible. |
| ES15-06 | GAP | Replacement success publishes a new admitted path without deleting old manual bundle | Always new unique owned extraction path; publish only after validation; retain predecessor on success too. Enter is no release proof. |
| ES15-07 | GAP | Malformed/traversal/unsupported archive gives no ready path or outside mutation | Preflight all members; reject absolute/traversal/unsupported links and ambiguous Windows destinations before extraction; malformed JSON manifest no path; unchanged outside sentinel; valid nested archive positive. |
| ES15-08 | GAP | Malformed preset is failure, not successful import pathname | Malformed/empty/wrong-shape/missing intended widget => null/throw coherent failure and no ready guidance; valid companion accepted. |
| ES15-09 | GAP | Intended iframe fragment changes exactly; unrelated JSON fields/text survive | Parse JSON; bind widget/orpul7IDXSSP id/key to data/orpul7IDXSSP.input; alter only intended iframe src fragment; preserve unrelated local=1 strings, Unicode, encoded hostile-looking labels and optional fields; serialize/reparse. |
| ES15-10 | GAP | Foreign/reparse/escaping destinations refused or safely isolated before effect | Fresh exclusive owned root/candidates; canonical component boundary and reparse checks; foreign/preexisting paths refused or isolated, never deleted to reset. |
| ES15-11 | GAP | Interrupt/failure cleanup touches owned scratch only | Record failed/cancelled states; cleanup only verified current scratch. Changed root identity/reparse/foreign sentinels and old manual bundles survive. |
| ES15-12 | GAP | Actual install/import callers require admitted result, not existence/printed success | Use one R0015 admission contract; all real callers consume it, no duplicate readiness predicate. No path copying/import selection on malformed/unadmitted results; healthy/fallback controls useful. |
| ES15-13 | GAP | Unknown-held/legacy-refused targets cannot reach staging automatically | Consume R0013 Status/Reason and Eligibility eligible-known before staging; unknown-held/legacy-refused/known-both held; mixed known targets still work. |
| ES15-14 | PASS | Dry-run zero effects includes creation/cache shortcut/extraction/rewrite/cleanup | Preservation PASS at baseline only; new transaction helpers/cleanup require affected native zero-effects verification, including cache hits and failure paths. |
| ES15-15 | GAP | Exact source works on actual claimed PS5.1/7 hosts; Unicode data/paths retained | Run exact candidate file actual claimed Windows hosts/filesystem with Unicode paths/data; binary never text-converted. Linux pwsh/Python cannot close NTFS/PS5.1 criterion. |
| ES15-16 | GAP | Downloaded/staged/handed-off/installed remain distinct in wording/evidence | Report partial/downloaded/validated/staged/handed-off separately; never infer installed from Enter or printed path; document retention/recovery. |
| ES15-17 | PASS | Original Bash/private-root/lifetime obligations preserved; unresolved parent rows visible | Baseline preservation only.21-03,21-05,21-15 remain binding; rebind affected integrated candidate and preserve R0013/R0016 interfaces. |
| ES15-18 | GAP | Final-tree review, native scope, manifests, rollback and public instructions agree | Complete source-linked map (C11/C12;preserveC08/C09/C10), source/fixture/evidence manifest, independent exact-tree security review, rollback, approved merge and actual public guidance readback. |

All ES15 technical locators are [6700332793](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6700332793), recovered lines 100–119, with detailed prose at 33–83. Exact source/consumer lines and source-vs-inference classifications are retained per row in the JSON. ES15-14 and ES15-17 PASS are baseline preservation only and cannot substitute for final candidate controls.

## Focused verification sequence for the root integrator

1. Finish receiving the R0013 eligibility producer and commission ordering/approved reordering receipt. Freeze the actual source identity before transaction edits.
2. Preserve the three original PowerShell RED schedules with actual extracted production functions and intercepted external calls: partial-write then failure/retry; predecessor sentinel then extraction/manifest failure; malformed preset through actual import caller. Pair each with a genuinely valid positive.
3. Implement only the owned-candidate/admission/extraction/preset/caller changes needed above. Keep one local attempt record and one admission API, no service/cache database or old-bundle migration.
4. Exercise changed identity/cross-run unknown file, byte readback mismatch, preexisting/reparse/escape paths, archive preflight, successful nondestructive replacement, interruption and cleanup identity changes. Mutations restore each actual defect and must fail its intended caller/sentinel assertion with a healthy original.
5. Run exact candidate native Windows PS5.1 and supported7 helper/caller/filesystem evidence; preserve native host/filesystem/version/source/fixture identities and Unicode. Linux pwsh may assist parsing/design but is not NTFS/PS5.1 qualification. Acquire actual Apple A01–A04 and native Linux A05–A07 separately.
6. Rebind unchanged Bash proofs without needless duplicate suites. Rerun only affected discovery/path/cache/preview/cleanup consumers on the final tree. Preserve the recorded baseline failure and distinguish its fixture diagnosis.
7. Complete README lifecycle facts, source-linked C11/C12 map, independent exact-tree review and affected distribution readback. No whole-parent closure while any mandatory native/source/delivery row is unresolved.

## Closure and remaining authority

| Gate | Required result | Current boundary |
| --- | --- | --- |
| G15-ORDER | Verify R0013 approved merge/delivery/whole closure or actual owner-approved disjoint reordering | Root-owned prerequisite; no receipt asserted by this child |
| G15-STATE | One source-linked state/refactor map and exact source/fixture/evidence manifest | C11/C12 owned; C08/C09/C10 preserved; bounded local state with actual callers |
| G15-REVIEW | Separately attributed exact-candidate security/native/consumer review | This intake audit is not final candidate acceptance |
| G15-APPROVAL | Exact owner-approved head/base/tree before merge | Commission is not blanket exact-candidate approval |
| G15-DELIVERY | Approved merge readback and affected public script/docs/copy-command delivery | Source hashes alone are not public delivery or installation |
| G15-CERTIFICATE | Full original+residual+ES certificate posted/read back then deliberate completed issue closure | Issue21 readback open; no mutation by this child |
| G15-LIFECYCLE | Formal governor currentness/lifecycle gate honored independently | Root controls governor; report confers no mutation/acceptance authority |

No final-tree review, exact merge approval, actual merge, delivery, acceptance certificate, issue closure or formal governor lifecycle effect is asserted here. Safe root engineering/fixture work remains possible; this report is not a terminal external-blocker return.

