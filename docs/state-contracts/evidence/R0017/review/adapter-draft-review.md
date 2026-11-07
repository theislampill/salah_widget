# R0017 independent adapter draft review

## Final scoped disposition: PASS — adapter slice only

This is a read-only review of the adapter increment while root continues evaluator work. **All three material adapter findings are resolved at the authored-profile follow-up hashes below; no open material adapter finding remains in this reviewed slice.** The current-source downgrade, omitted historical input, and omitted current authored input were preserved as red evidence, corrected by the adapter author, and independently checked. The governing shared-contract SHA-256 is `adde2470bba5f276ddae71f0c5a2fad9485854604bbd733c87723583e04b578a`. This is not candidate-wide acceptance or frozen-commit review. Earlier findings, hashes and checkpoints remain as chronology; the final authored-profile follow-up and its source hash table supersede the preceding checkpoints.

## Review boundary

Observed base: `f71fef6ccf7e4efcb57b5a26688d2360461a3253`, tree `79aedcac840d624b5ea423922314f0832dc3f750`, branch `pro/r0017-explicit-regression-lifecycle-20261106`.

I inspected the complete shared script contract, Node extraction adapter, subset config/settings fixture, whole-runtime VM fixture, browser wrapper, added adapter controls, changed transport controls, preference/storage caller adjustments, particle-selector adjustment, actual native boot and first-document functions, and direct native-inline-runtime consumers. I also inspected completed source-bound evidence and exact-history logs. I did not edit repository source or run a broad suite.

The recorded draft hashes are in `adapter-review-evidence/draft-source-manifest.json`. They intentionally precede the pending shared-contract repair. All observed tracked changes were within tests and the evaluator; no tracked changes outside the expected evaluator scope were present. Directly inspected product inputs `index.html`, `config.js`, `builder.html`, `src/native/index.html`, and `tools/build_native.py` were unchanged by this adapter increment. This is not a regenerated-runtime or browser qualification claim.

## Finding ADAPTER-01 — current document can downgrade to a historical layout

**Status:** resolved in final re-review below. **Original severity:** material. **Relevant requirements:** ES17-07/08/11, complete prerequisite admission, and truthful historical applicability.

At shared contract SHA-256 `26a0abddcd19a5fadf497deac061cefd58ac7599354be598baa1010a94e7d399`, `admitScripts()` selects its strict split-Moon profile by whether either Moon script role remains in the input. Its retained layout allowlist is otherwise accepted structurally.

A bounded read-only probe used the actual checked-out `index.html` and removed script blocks in memory only:

| Input | Observed admission |
|---|---|
| Healthy current source, six scripts | Accepted as `split-moon`, with all three pinned prerequisite bodies. |
| Same current source, both Moon prerequisite scripts removed | Incorrectly accepted as `retained-document`, four scripts; actual native owner unchanged. |
| Same current source, first-paint and both Moon prerequisite scripts removed | Incorrectly accepted as `retained-document`, three scripts and no prerequisite bodies; actual native owner unchanged. |

The first two missing-one-script negatives do not cover simultaneous loss. The wrapper and Node extractor both use this contract, so the defect affects their shared setup admission. It can turn an incomplete current source into a valid-looking legacy input without independently establishing historical provenance.

Evidence: `adapter-review-evidence/historical-profile-downgrade-probe.json`, observed 2026-11-07T03:47:18.132Z. Contract, Node adapter, and input source hashes were identical before and after the probe. This probe did not execute product code or a browser.

**Required correction:** Current full documents must retain the current required profile. Historical layouts must be admitted from independent, explicit historical source identity or an equally discriminating contract, not the absence of current prerequisite tags. Keep exact genuine historical inputs usable, and keep any complete-document synthetic structural fixture separately named and scoped. Add both simultaneous-loss negatives to Node and actual-wrapper controls. A fixed literal synthetic-fixture pin is acceptable only with explicit parent/transformation provenance and `runtimeQualified:false`; it must not be learned from its submitted body.

## Other inspected changes

### First-document state and actual boot

`r0011-fixture.cjs` now extracts the actual `_skyInitialDocument` declaration and actual `finishInitialSkyDocument()` function. It does not synthesize a default Boolean to make boot pass. The new controls check a true initial value, actual retirement before unresolved-location acquisition, changed source initializer propagation, and missing/ambiguous declaration rejection.

The actual native `boot()` retires the one-use initial handoff before its two-frame/message-task await. For unresolved coordinates it retires before awaiting coarse acquisition. The subset fixture keeps the real boot/apply/settings functions and records provider/render boundaries explicitly. Preference tests add only the wait needed before inspecting/resolving the actual prayer launch. The storage test adds the missing `finishInitialDocument` method to its already-declared Moon boundary double and asserts the actual call. Existing product expectations were not softened.

### RAF and MessageChannel plumbing

The whole-runtime fixture holds only the final `boot();` entrypoint. It adds fixture-owned frame IDs, cancellation, message ports, a task queue, and bounded completion driving so the real nested RAF/message continuation can settle. It preserves exact rejected values, including falsy rejection reasons, and throws an explicit incomplete-fixture error on exhausted turns. Frames/tasks do not advance a claimed browser wall clock.

The subset environment delivers its owned frame and message callbacks on bounded host turns. It still retains independent controlled timers. This is suitable source/scheduling evidence for the inspected callers, not proof that a browser presented a frame or met a startup deadline.

### Shared source contract and wrapper

Node and the browser wrapper import the same pure source contract. They compute actual prerequisite body digests independently of the allowed pinned digests. Current named prerequisite changes, duplicate/missing individual owners, unknown scripts, a wrong native owner, and first-paint identity mismatch have explicit setup failures. ADAPTER-01 is the remaining gap in the inspected draft's complete-document profile selection.

The wrapper loads the pure contract before fetching/admitting product source. It then installs the private Map-backed storage getter, fixed Date and fetch/Response/json transport before `DOMParser`. Product script body equality is checked across wrapping; the separate weather bridge stays labelled and hashed. Missing contract, wrong document anchors and wrong owner source must fail before any product parsing or real storage access. The fixture retains real-storage sentinels, ownership guards, request admission, no transport fallback, distinct healthy/reject/hang/bootstrap-error modes, and the retained WASM-only CSP capability. Existing source tests deliberately stop at the parser boundary; they do not requalify native browser execution of the new split layout.

### Particle selector repair

`r0025-lifecycle.cjs` changes the recording DOM selector from `.wfx .drop` to the exact combined selector `.wfx .drop,.wfx .flake` used by the current owner. Its permission, column-selection, clear-state and stale-weather assertions remain. No product particle behavior was changed.

### Real guard mutation remains distinguishable from setup failure

The unchanged `r0001-date-sinks.cjs` still executes actual config/model/render code through the repaired native extractor. Each CE/AH/preview mutant runs through its healthy setup and nonempty six-row renderer before the original safety oracle is required to reject the unencoded sink. It also asserts that raw SVG reached the targeted sink and preserves the other sink where applicable. Therefore its recorded mutant successes are actual product-guard discriminators, not a pass obtained by failing extraction or boot. This is a recording-DOM source proof, not browser script execution or exploitability evidence.

## Completed evidence inspected

`adapter-evidence/candidate-consumers.json` records nineteen affected commands at its stated older draft hashes, all exit zero. This is evidence for that bound draft, not automatic evidence for the forthcoming profile repair. At initial inspection, its first appearance-count receipt reported zero line cases because output has a warning prefix followed by JSON. The complete unchanged raw `r0018-appearance-candidate.log` contains seventeen PASS result records; the receipt needs the actual seventeen-case interpretation without changing or rerunning the source assertion.

Relevant source-bound recorded positives include date sinks 13/13 with the three actual guard mutants, date selection 22/22, preferences 9/9, storage 18/18, lifecycle 11/11, deadline 13/13, smoke storage/accounting 35/35, transport 29/29 at the older wrapper, particle lifecycle 16/16, and retained intent/reset/clipboard/effects/radio/weather/cloud consumers. Added document-marker controls have their own preserved red evidence; later wrapper counts must be taken from their own refreshed receipt.

`adapter-evidence/exact-history-consumers.json` and its raw logs preserve three newly available exact-history outcomes:

- `r0018-timetable-contrast`: exit zero, eleven PASS results against exact `ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d:index.html`, whose pinned SHA-256 is retained in the log.
- `r0023-metadata`: exit zero, 31/31, including the actual `fd2972ba64225fe9d6848e92497e6d0ed20ea624` older consumer and byte-preserving saved-record read.
- `r0021-reveal --cp8-snapshot-only`: exit one, declared/executed 15, **14 pass and one fail**. The failing case is `moon PBR shader and embedded payloads retain exact accepted bytes`, after the exact historical input became available. This is an observed assertion failure, not missing setup, an excluded synthetic producer, or permission to change an accepted product guard.

No `r0022-baseline-balance` run was included in that receipt. Its pinned historical inputs and material/compositor expectations must retain their own final disposition. The five inherited synthetic-star exclusions retain the concrete partial coverage and residuals in `star-replacement-map.md`; no fixture change makes those five observations passing replacements.

## Gates recorded before final re-review

ADAPTER-01 must be resolved and independently checked. Refreshed focused evidence must bind the final shared contract/wrapper bytes and preserve genuine historical source admission, Node/browser simultaneous-loss rejection, and the real guard control. After that, a scoped adapter review may pass while genuine product/history failures remain non-PASS in the evaluator. The final immutable candidate still requires separate review of the complete change and its actual evidence.

## Draft source hashes

These record the inspected draft, not the pending corrected profile.

| Path | SHA-256 |
|---|---|
| `tests/native-script-contract.js` | `26a0abddcd19a5fadf497deac061cefd58ac7599354be598baa1010a94e7d399` |
| `tests/native-inline-runtime.cjs` | `a87ad8b2156a76a097020072cddb4752ccbc04409db720813e201accf0ebae1e` |
| `tests/r000f-fixture.cjs` | `740e9f3476466c978aa4bc12491bd71a3a3f3010f4b5a5a40360fa1f30d66aa2` |
| `tests/r0011-fixture.cjs` | `bcb1d8f4bff8ea97746253768c70b9fb756bc2258c94713c80cbb29a26d692fd` |
| `tests/r001d-harness.cjs` | `7c83c45ed757bdf7e5ae72cf0992a2aeeedbef65bf407e1a88b929deef44cf32` |
| `tests/widget-fixture.html` | `6dd9d693708e9df3df5632d3675ea266c697a717f45a10756c473ff8ab50abe4` |
| `tests/r0017-transport.cjs` | `b7909f5cfa3e84241076e560d542ad4af1b3ba0f08b8887b425a1c87815389a5` |
| `tests/r0010-preferences.cjs` | `5345a1037c3442188f4f1ad977c0f7daab1f6dd33fda9147aa6d6f7601df091c` |
| `tests/r0011-storage.cjs` | `9c09b1a3a1420a3571b3ade8b3fff5bf0cd0b8d5a043ec6230a0aeccdd018f1d` |
| `tests/r0025-lifecycle.cjs` | `b7744212576e8a6ff671d7443f79b93f0046a0a05273bd1d89df43019f317cc2` |
| `tests/r0017-adapters.test.cjs` | `fc13d93868c7371953c3acb4e311d14e45f3056170836012a7715d5e5bcdc076` |
| `tests/moon-fixture-anchors.test.cjs` | `79456cf5582d2c0d1133c0bf412a8b95991c1d2564fac5a441222a9d30eaa964` |
| `tests/r0001-date-sinks.cjs` | `69a764ec0126941a46bf92c0a30467e3f8c01d5371464dd9d95f15c5340a2e64` |
| `tests/r0001-browser-fixture.cjs` | `6533cd947ceaa9209af4b185a50a1a0721098e86ee10f957d9c0546ec59f4f46` |
| `tests/r0009-calendar-harness.cjs` | `2ea4e5231a347c378199b8f502e0fc532e3d602fea69ada9a0a4327195ce144c` |
| `tests/r0017-contract.cjs` | `99bb97328b77c8aa7019989bc50e102ec1e13da6a0fd9f12396c7003d8f71dd3` |
| `tests/r001d-lifecycle.cjs` | `5a751be6e5be97429f47345ada66f1442a7c3db8d71f2cd298a04fd922dd8f38` |
| `tests/r001f-deadline.cjs` | `c7462e9c01b5a2b9c1e12628a3c0832d18ac4da4d2c79cbe3485ebec7470d57c` |
| `tests/r0021-reveal.cjs` | `c66a0b967fd2de957c656f33ad32d9b84099ed7e3ce7f4c0841ac780918f76ca` |
| `tests/r0022-baseline-balance.cjs` | `6ddc11e8291b77e5532688ddec6a296b1ec3840dad8c0817d9779d3ddd847e79` |
| `tests/r0023-metadata.cjs` | `34bc3a071dbebf807ef8503396fa6279b39f7d3a2121b3fa8fc35653f41a0ce8` |
| `tests/r0018-timetable-contrast.cjs` | `6d25bbafd0d7755e91a19113ab062a5ed8a56bd182a40346e7fbb8860855fdb0` |
| `index.html` | `b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298` |
| `config.js` | `91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81` |
| `builder.html` | `66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e` |
| `src/native/index.html` | `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` |

## Re-review checkpoint — ADAPTER-01 corrected; ADAPTER-02 found

At shared contract SHA-256 `f68892db2c285e9dd3a17b0fc6109dc3b1a28c405b6efc547878a455bb82f630`, complete documents default to the required current split layout; retained documents require literal whole-source SHA-256 entries with explicit provenance/layout. Node computes the full-source hash, and the browser passes its already-computed fetched-byte hash. The synthetic legacy shell has its own structural-control profile, parent hash and transformation description. Current semantic native-body mutations remain admissible, since the current native body's entire hash is not pinned.

My independent `profile-fix-independent-probe.json` confirms that both simultaneous-loss inputs now reject, healthy current source and a current semantic initializer mutation admit, and the exact fd2972, ed5e7af and 47c0fa documents plus the separately labelled legacy structural fixture admit. All six source/input files hashed in that probe were stable. The author's focused receipts independently show adapter controls 13/13, wrapper controls 32/32, actual date-sink controls 13/13, and exact-history metadata 31/31 at this profile-bound draft.

**ADAPTER-02 — available selected historical input omitted.** `r0022-baseline-balance.cjs` explicitly calls `load({source: acceptedNative})` inside its scene comparisons. Its accepted native input is `18ff14860ff41c084b1db5f396bb62aa9c22b1be:index.html`, SHA-256 `ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee`. That exact object is available and matches the test's independent pin. Its real layout is `config,first-paint,native,sky,moon-file,moon-host`, but it was absent from the new retained map and the independent probe rejected it as `SETUP_INCOMPLETE`. This is a setup compatibility omission, not a failure of its scientific/material assertions. The author was asked to add only this exact provenance/profile and record cheap extraction proof, without running the full balance scene campaign or widening the normal test glob's hidden history dependencies.

The other balance prerequisite `8b83df029966c203a503ab217d121c48b8ee6e8a:index.html` remains unavailable in the inspected repository; its arc-source comparison cannot be invented or substituted. It is not the same issue as rejecting the available 18ff input.

Additional actual guard-mutant receipts (`adapter-evidence/adapter-mutations.json`) retain independent setup admission before running unchanged sink assertions: CE removes its encoding guard and produces five assertion failures; AH produces five; preview produces one. All three exit one, with no `SETUP_INCOMPLETE`, and protected product files remain unchanged. Disposable wrong-script, non-driving-frame, and old-selector counterfactuals also produce nonzero outcomes in actual consumers. These are useful discriminators, not justification for suppressing the retained PBR history failure.

## Pre-joined re-review — ADAPTER-01 and ADAPTER-02 resolved

**Scoped PASS** binds the adapter files in `adapter-evidence/adapter-freeze-manifest.json`, with final shared contract SHA-256 `fe8d0db668c85fe2c6281763f342636c44a0b354a45ef594ca0c2a6765aac627`. The sole change after the first profile correction was the explicit literal retained entry for exact 18ff input. No new hidden historical dependency was added to the normal test glob.

The independent final probe is `adapter-review-evidence/final-profile-independent-probe.json`. It invokes the actual Node extraction helper, independently inspects the returned profile/provenance, and compiles admitted script bodies without executing product code. Its nine cases all have the expected outcome:

- Healthy current source admits as `split-moon`.
- Removing both Moon prerequisites rejects with `SETUP_INCOMPLETE`.
- Removing first-paint and both Moon prerequisites also rejects with `SETUP_INCOMPLETE`.
- The one explicitly pinned legacy structural control admits with its distinct structural-control profile and provenance.
- A current semantic native-body mutation remains admitted; full current native bytes have not been pinned in a way that would turn product-guard mutants into setup failures.
- Exact fd2972, ed5e7af, 47c0fa and 18ff `index.html` inputs each admit in their named retained historical profile and compile. Their source SHA-256 identities and extracted runtime hashes are retained per row.

All **27 reviewed source files** were unchanged across the final probe, and all eleven adapter hashes matched the author's freeze manifest. The probe completed in 0.229105944 seconds and exited zero; this is not a product or browser performance measure. HEAD remained `f71fef6ccf7e4efcb57b5a26688d2360461a3253`. No observed tracked changes were outside the expected evaluator/tests/documentation scope.

Fresh final author controls, whose complete raw logs I inspected, are:

| Receipt | Result | Scope |
|---|---|---|
| `final-focused-adapters.log` | 13/13 TAP, zero failures/cancellations/skips/TODO | Native extraction, individual and simultaneous prerequisite loss, first-document source ownership, actual boot scheduling, retained structural snippets. |
| `final-transport.log` | 32/32 result records, exit zero | Actual wrapper up to its deliberately stopped parser, including simultaneous loss rejection before storage hooks and retained structural provenance. |
| `final-date-sinks.log` | 13/13 result records, exit zero | Actual config/model/render sinks, including CE/AH/preview product-guard discriminators after valid setup. |
| `accepted-native-profile-green.log` | Exact 18ff source admitted and compiled | Extraction-only recovery of the available selected historical input; no whole balance scene or product execution. |
| `diff-check.log` | Exit zero | Adapter diff whitespace check only. |

The final transport log directly records the final contract, wrapper and current-source SHA-256 identities. The earlier three external product-guard counterfactual receipts retain the intended assertion failures after successful setup; final date-sink controls reconfirm the corresponding guards under the final adapter contract. The parent may now bind its joined source execution to this frozen adapter slice.

### Residuals remain explicit

This PASS does not change the real `r0021-reveal` PBR byte-preservation assertion failure, does not supply the unavailable 8b83 balance prerequisite, and does not execute or certify the balance scene campaign. It also does not turn the five synthetic-star exclusions into passing replacement observations. Source/VM scheduling and transport controls retain their declared browser, pixels, live-motion, provider, delivery and performance limits. The earlier accepted smoke closure remains preserved; a final immutable candidate-wide review and truthful joined runner outcome remain separate.

## Pre-joined adapter SHA-256 identities

These superseded the earlier draft adapter hashes at the pre-joined checkpoint. They are subsequently superseded by the authored-profile follow-up below. The complete 27-file before/after records are in that checkpoint's independent probe.

| Path | SHA-256 |
|---|---|
| `tests/native-script-contract.js` | `fe8d0db668c85fe2c6281763f342636c44a0b354a45ef594ca0c2a6765aac627` |
| `tests/native-inline-runtime.cjs` | `f73ee21f6e745f0e4a60ea8732caaefa5e2e367be1048affba5abed81258c5db` |
| `tests/r000f-fixture.cjs` | `740e9f3476466c978aa4bc12491bd71a3a3f3010f4b5a5a40360fa1f30d66aa2` |
| `tests/r0011-fixture.cjs` | `bcb1d8f4bff8ea97746253768c70b9fb756bc2258c94713c80cbb29a26d692fd` |
| `tests/r001d-harness.cjs` | `7c83c45ed757bdf7e5ae72cf0992a2aeeedbef65bf407e1a88b929deef44cf32` |
| `tests/widget-fixture.html` | `2975111135aac3197dda912de7d06c2452e42d22e304736b82cf3c686a975ac6` |
| `tests/r0017-transport.cjs` | `48676a026db9c336229575e4dfcec121f8b6802b469eede53024f8e90db08f98` |
| `tests/r0010-preferences.cjs` | `5345a1037c3442188f4f1ad977c0f7daab1f6dd33fda9147aa6d6f7601df091c` |
| `tests/r0011-storage.cjs` | `9c09b1a3a1420a3571b3ade8b3fff5bf0cd0b8d5a043ec6230a0aeccdd018f1d` |
| `tests/r0025-lifecycle.cjs` | `b7744212576e8a6ff671d7443f79b93f0046a0a05273bd1d89df43019f317cc2` |
| `tests/r0017-adapters.test.cjs` | `8af39ab967aa3cf636fc434664a45e95557e6e0c41c43de3d77be9428575ee7a` |

## Pre-joined review evidence SHA-256 identities

| Artifact | SHA-256 |
|---|---|
| `adapter-review-evidence/historical-profile-downgrade-probe.json` | `92492c164cd0821d1d74b60f1044893becd8054add2c41ba5206b7d61cc64bf8` |
| `adapter-review-evidence/profile-fix-independent-probe.json` | `5c50a65e58d409d36910690f7af87d498ff8fbc8c1fa8bbc5b2bf64ac8d43734` |
| `adapter-review-evidence/final-profile-independent-probe.json` | `2cbff76ac27985a93f2ced6d412fabf4bc0d660845f44a8667ff11c603b87231` |
| `adapter-evidence/adapter-freeze-manifest.json` | `618dbb02b218df3f15240bad2983e6700bd113b103397100a9217c34ee858e0f` |
| `adapter-evidence/adapter-mutations.json` | `1f1bac43b9759e03137b5825fc0566ab7d67d98adfdb6acba7e6b218ff63bed0` |
| `adapter-evidence/final-focused-adapters.log` | `9c8ffe829db871c1e21426f86ac4bcc5738f0cfa7320543d70be7d09cdf7d365` |
| `adapter-evidence/final-transport.log` | `358a89332d9fedf17c1acae68c8886c9b849a399736c166325db89640309d4e0` |
| `adapter-evidence/final-date-sinks.log` | `cb9cbda227a427bf7861f0387d968bb690a329a8de5bcfc25a7aa20cad71af55` |
| `adapter-evidence/accepted-native-profile-red.log` | `762697fcb2f377a23767a027d993de259fa6a30342817876747369f3a86dc497` |
| `adapter-evidence/accepted-native-profile-green.log` | `cd08fc909ac66f53270abb5289084b5cb2fe712f227fc7bea2c1a23ec3235e28` |


## Finding ADAPTER-03 — actual authored native input omitted

**Status:** resolved in the following independent re-review. **Original severity:** material setup compatibility omission.

The parent reported that its completed joined run `joinedrun29` reached all 21 existing hotfix cases but each was refused at setup on current authored `src/native/index.html`. I did not rerun that joined population. The separate focused red receipt `adapter-evidence/authored-profile-red.log` independently preserves the original `SETUP_INCOMPLETE` failure when the exact authored-input positive was added before the repair; the other fourteen controls passed, including the stripped-generated lookalike rejection.

I read the actual `tests/hotfix-prayer-weather.test.cjs` caller. Its default `sourcePath` is `src/native/index.html`; every one of its 21 cases obtains the real VM through `make()` and `r001d-harness.cjs:load`. Complete-source extraction happens before the test's state/function substitutions through `h.run(...)`. The test does not first mutate the full authored document and then expect generic authored admission. Therefore an explicit identity for the actual authored input is sufficient for the existing caller and does not require a permissive generic two-script profile.

The author's repair adds one literal entry for SHA-256 `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad`, named `current-authored-native`, with `kind: current-authored-source`, commit `f71fef6ccf7e4efcb57b5a26688d2360461a3253`, path `src/native/index.html`, and exact layout `config,native`. It adds two source controls: the exact authored owner is returned byte for byte and altered authored bytes are refused; the generated document stripped to the same two script roles is refused. It does not introduce a generic two-script fallback, derive a pin from submitted untrusted bytes, or pin the current generated native body's semantic contents.

The only source deltas since the preceding pre-joined checkpoint are `tests/native-script-contract.js` and `tests/r0017-adapters.test.cjs`. The actual hotfix consumer and authored/generated product inputs remain unchanged.

## Final authored-profile follow-up — scoped PASS

The new independent receipt is `adapter-review-evidence/authored-profile-independent-probe.json`; its retained probe source and process receipt are adjacent. The probe calls the actual Node helper, independently checks the shared contract's profile/provenance, and compiles admitted native bodies with `vm.Script`. It executes no product script, browser, renderer, scene campaign or joined regression population.

| Input class | Observed result |
|---|---|
| Exact current authored input | Admitted as `current-authored-native`; exact native owner returned and compiled; distinct authored provenance. |
| Authored input with an unreviewed appended comment | Refused with `SETUP_INCOMPLETE`; the literal input identity is required. |
| Current generated source | Admitted as `split-moon`; actual native owner returned byte for byte. |
| Current generated source with both Moon prerequisites removed | Refused with `SETUP_INCOMPLETE`; ADAPTER-01 remains closed. |
| Current generated source with first-paint and both Moon prerequisites removed | Refused with `SETUP_INCOMPLETE`; ADAPTER-01 remains closed. |
| Current generated source stripped to only `config,native` | Refused with `SETUP_INCOMPLETE`; matching the authored layout does not confer authored provenance. |
| Current generated native semantic initializer mutation | Admitted as `split-moon`; behavioral mutants are still able to reach their oracle. |
| Explicitly pinned legacy structural fixture | Admitted with its distinct structural-control profile; `runtimeQualified:false`. |
| Exact fd2972, ed5e7af, 47c0fa and 18ff historical documents | Each admitted in its explicit historical profile and compiled; all independently pinned source hashes match. |

All twelve probe cases have the expected outcome: eight admit/compile and four refuse setup. All **28 reviewed source files** were stable before and after the probe, including the added hotfix consumer; all author's stated final source hashes match. The other 25 previously reviewed files are unchanged from the pre-joined checkpoint. HEAD remained `f71fef6ccf7e4efcb57b5a26688d2360461a3253`. The serial process exited zero in 0.45938800099975197 seconds under a 20-second bound; this duration is only probe metadata, not a product performance claim.

The author's completed `adapter-evidence/authored-profile-verification.json` and full log identities were checked against actual log bytes and outcome records:

| Receipt | Observed result | Review implication |
|---|---|---|
| `authored-profile-green.log` | 15/15 TAP, no failures/cancellations/skips/TODO | New authored controls and all prior focused admission/scheduler controls pass at the new shared contract. |
| `authored-hotfix-green.log` | Original 21/21 TAP, no failures/cancellations/skips/TODO | The unchanged real hotfix caller is restored on its actual authored input. |
| `authored-profile-transport.log` | 32/32, exit zero | Actual wrapper source, final contract and product hashes are recorded; both simultaneous-removal controls still fail setup before hooks. |
| `authored-profile-date-sinks.log` | 13/13, exit zero | Actual config/model/render safe sinks and all three in-suite guard discriminators remain live. |
| `authored-profile-ce-mutant.log` | Exit one; `setupAdmitted:true`; five original CE safety assertions fail | Current generated product-guard mutation still reaches behavioral failure, without a setup rejection masking it. |

The source-specific authored pin deliberately requires explicit review/rebinding for a future authored-byte change or another `SALAH_HOTFIX_SOURCE` input. That maintenance boundary is visible setup incompleteness, not a behavioral PASS. Current existing tests make their semantic substitutions after extraction; current generated guard mutants remain independently admitted.

The parent's original joined red is retained. This focused repair does not retroactively turn that joined run into a PASS and does not adjudicate the parent's remaining runner parsing/TAP work. The real `r0021-reveal` PBR byte-preservation failure, unavailable 8b83 balance prerequisite, unexecuted balance scene comparisons, five synthetic-star replacement residuals, and all source/VM/browser/provider/performance scope limits above remain unchanged.

### Governing adapter source identities

These identities supersede all earlier adapter hash tables for this scoped PASS. Every other reviewed input's exact hash and size is present in the 28-file before/after receipt.

| Path | SHA-256 |
|---|---|
| `tests/native-script-contract.js` | `adde2470bba5f276ddae71f0c5a2fad9485854604bbd733c87723583e04b578a` |
| `tests/native-inline-runtime.cjs` | `f73ee21f6e745f0e4a60ea8732caaefa5e2e367be1048affba5abed81258c5db` |
| `tests/r000f-fixture.cjs` | `740e9f3476466c978aa4bc12491bd71a3a3f3010f4b5a5a40360fa1f30d66aa2` |
| `tests/r0011-fixture.cjs` | `bcb1d8f4bff8ea97746253768c70b9fb756bc2258c94713c80cbb29a26d692fd` |
| `tests/r001d-harness.cjs` | `7c83c45ed757bdf7e5ae72cf0992a2aeeedbef65bf407e1a88b929deef44cf32` |
| `tests/widget-fixture.html` | `2975111135aac3197dda912de7d06c2452e42d22e304736b82cf3c686a975ac6` |
| `tests/r0017-transport.cjs` | `48676a026db9c336229575e4dfcec121f8b6802b469eede53024f8e90db08f98` |
| `tests/r0010-preferences.cjs` | `5345a1037c3442188f4f1ad977c0f7daab1f6dd33fda9147aa6d6f7601df091c` |
| `tests/r0011-storage.cjs` | `9c09b1a3a1420a3571b3ade8b3fff5bf0cd0b8d5a043ec6230a0aeccdd018f1d` |
| `tests/r0025-lifecycle.cjs` | `b7744212576e8a6ff671d7443f79b93f0046a0a05273bd1d89df43019f317cc2` |
| `tests/r0017-adapters.test.cjs` | `ca4be8789b0beb127a2e3d226dd952face79ae8412f13d8b927f9236c9faaef8` |
| `tests/hotfix-prayer-weather.test.cjs` | `1b96aa5ec5ed88c5386eccaeabd38ea07a50f91461da412247b4ddd3e21f07d1` |
| `src/native/index.html` | `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` |
| `index.html` | `b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298` |

### Authored follow-up evidence identities

| Artifact | SHA-256 |
|---|---|
| `adapter-review-evidence/authored-profile-independent-probe.cjs` | `2c3066440998d70fa931bfefa21ac176a38df02b3b6cedda0b00d84b55f8a9fd` |
| `adapter-review-evidence/authored-profile-independent-probe.json` | `f23d70f3e15f62c1c15e114da96c9dbf8f4e63df37cbe55eb5680d7287a075d4` |
| `adapter-review-evidence/authored-profile-independent-probe.run.json` | `30ce06a6acc8f86cc1aa33e33a0d96aa38894314a71c624d40f908753d08b4cc` |
| `adapter-evidence/authored-profile-verification.json` | `523e4f25873aeee84b43ff26b6a536d7ffc509c96b931668f8d877c7aef27b86` |
| `adapter-evidence/authored-profile-red.log` | `65a1f874d6783975cbcc54d42dff31cf04dd9e61b2e5ccf97c307c95998d4752` |
| `adapter-evidence/authored-profile-green.log` | `a6073489b3b1533e8a7c4dddd62a2fae3138125e96d565d1e2788bfc7ccfad94` |
| `adapter-evidence/authored-hotfix-green.log` | `5e6bdb494cd996992a52aed19027c0e64b65777c798f220ce748bd804bd9aaf3` |
| `adapter-evidence/authored-profile-transport.log` | `12e0ca70602f038d59fa8f69227c979565bbd30edf49eacf3a64dbbd6983b379` |
| `adapter-evidence/authored-profile-date-sinks.log` | `cb9cbda227a427bf7861f0387d968bb690a329a8de5bcfc25a7aa20cad71af55` |
| `adapter-evidence/authored-profile-ce-mutant.log` | `3834c91accddc2f28166111d8583f900e874af13564e755202d7331cdd9b5111` |
