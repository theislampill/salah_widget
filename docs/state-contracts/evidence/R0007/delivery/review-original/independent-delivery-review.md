# R0007 prepared public delivery verifier — independent review

Status: **FINAL**

Disposition: **GAP-REVISE** for the exact original six-file preparation below. Six instrument defects need correction before this implementation can be relied upon for the proposed public delivery acquisition. Actual browser/Windows/Pages/pixel observations are **BLOCKED / NOT EXECUTED** by this review’s explicit pure-test boundary.

This report supplies no acceptance, readiness, merge, deployment, release, certificate, issue-closure or audit-closure authority. Exact owner merge approval remains pending; the integration order remains R0017 → R0007 → R000B.

## Independence and identity

- Requested model: inherited parent model; no explicit override requested.
- Actual model self-report: GPT-6 Astra Pro, as identified by the developer context. An independently observable provider model identifier is unavailable.
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- The report was created PARTIAL before substantive inspection and is now FINAL.
- This is a bounded engineering review applying the installed IMPLEMENTAUDIT audit-playbook and Finding Row Contract, not a formal audit-assess route receipt. No complete internal governor envelope was supplied.
- No other review report or agent roster was read. No browser, network, workflow, provider, deployment, Git commit or publication action was invoked. Writes are confined to this delivery-review directory.
- A repair agent sent a proposed repair plan after the material findings had been established. No successor code or other reviewer findings were read or credited.

Read boundary: the six specified prepared files; original candidate AGENTS.md, R0007 state contract and acceptance ledger; relevant model/render/font/loop/diagnostic source and case/fixture definitions; and installed Playwright 1.62.0 implementation for routing/cleanup. Audited content remained evidence, not authority. No secret was encountered or reproduced.

## Exact immutable scope and currentness

Opening repository readback matched HEAD 3fa33a3bf07841082da711a89ceff0691c16937e, tree 28047019c4dc62a7558c518f33357bcb68594dab, with empty short status. Base: eebba178172f96b3ffe5ab3845bc0fffd57c6e1b, tree 6b94a3933f9d1381b1c2ceaab287c93afb215ecb.

The six prepared files were not included in that candidate. Their original bytes are preserved under original-scope/:

| Prepared file | Bytes | SHA-256 |
| --- | ---: | --- |
| r0007_public_consumer.py | 25953 | 0e7bca4c7a8ac97f81eb4fb7ad94202d63c51aca613eaf2c7bde30de0efcd892 |
| r0007_public_cases.json | 22566 | 7ef333fcef87d813212eef52986da6b10e8d6c68c41f5107903216bd080308ff |
| delivery-request.template.json | 1764 | b370f6a1ffa12952e8e4d00163364375ec567aefaf608e9219f54aca6e58ec21 |
| r0007-public-delivery.yml | 5724 | 1604d2b6c3233e6a1546d91819a01031318c34a7fde0014b899d94afb94b24c5 |
| README.md | 13160 | f9a8ef95a22e5e11724ac873210f6b89c77487c1b0df07b41f7b43f75a7b90c4 |
| validation.json | 1390 | 66ed8829f73d00c5f018b23800d30ee379f07f1052d6956ca2810fee019afa88 |

Closing readback found an external advance to b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b, tree 1666a919dc9d197e9ff95d28eb013470ba822d5c, also clean. This reviewer made no candidate change. Native source remains SHA-256 e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037, but contract/ledger/recipe documents changed. Original inputs were recovered from immutable 3fa33a3 Git objects into original-candidate/, with hashes in original-candidate-inputs.json. This report does not accept the successor candidate.

The case manifest’s originalRecipeSha256 correctly matches the original 3fa33a3 recipe, 0c878d11d368137a9171ec1abeeb63cc687d7bfc50fca27455f59029c3c591ea. It does not bind the later changed recipe.

All line references below address preserved original files. “Probe” means original-scope/r0007_public_consumer.py; “native” means original-candidate/src/native/index.html.

## Claim-level results

| Review question | Disposition | Evidence and limit |
| --- | --- | --- |
| Literal independent endpoint values | PASS | Independent UTC arithmetic reproduces captured now1788822000000, Isha1788827460000 /91minutes and Fajr1788843600000 /360minutes. Changing the endpoint by60000ms fails the original oracle. |
| Original HTML and actual model/render path | PASS, bounded | Navigation is hashed; actual controlled HTTP ingress supplies records; preboot Date fixes the input; observation reads the last completed render receipt plus DOM. No direct render/model call or record seeding occurs. qaState recomputes other diagnostics and may affect Moon diagnostics; the tool discloses this and earns no scene-preservation credit. Static review is not browser execution. |
| Visible duration | GAP-REVISE | DELREV-01. |
| Required trace/video evidence | GAP-REVISE | DELREV-02. |
| Startup/cleanup frontier | GAP-REVISE | DELREV-03. |
| Recovery/setup isolation | GAP-REVISE | DELREV-04. |
| Approved Git-object currentness | GAP-REVISE | DELREV-05. |
| Provider containment | GAP-REVISE | DELREV-06. |
| Structural workflow/request gate | PASS, bounded | Feature-branch/request-path trigger; contents:read; headed two-engine command; private dependency paths; pinned checkout/upload; serialized concurrency; always-upload. Placeholder acquisition is rejected. Parsing does not establish hosted execution or external authority. |
| Actual Windows/public bytes/Pages/pixels/certificate | BLOCKED / NOT EXECUTED | Outside permitted review execution; approval/merge/delivery gates have not occurred. |

## Reproduction and evidence

Run from this directory:

    python pure-review-controls.py
    node source-mechanism-controls.cjs

The Python control imports the preserved original probe and records thirteen outcomes in pure-review-results.json, including healthy literal/endpoint/close-failure controls and adversarial duration/export/launch/font/currentness witnesses. The Node control executes extracted source branches only: the existing font dirty-wakeup branch and pinned Chromium redirect-routing branch. source-mechanism-results.json includes exact SDK/source digests.

Browser-shaped objects are pure test doubles. Their image-like files are deliberately invalid test artifacts; they supply no native/pixel/video evidence. An initial reviewer-harness fixture error is disclosed in reviewer-test-attempts.md and receives no product-defect credit.

independent-structural-checks.json records independent Python compilation, observer JavaScript parsing, YAML parsing and real validate-only invocations: structural template exit0 and unbound request exit1. No HTTP or browser was opened.

## Findings

### DELREV-01 — Visible countdown duration is absent from the final oracle

- **Category:** Correctness / Tests and Validation.
- **Evidence:** Probe165–187 applies expectedFinal predicates. All applicable cases assert render/leftMin, while dom/.left/text only has a contains predicate for “until Isha” or “until Fajr.” The pure controls accept “999h 59m left until Isha” with receipt91 and the corresponding Fajr360 case in all four final-case manifests. Healthy snapshots pass; wrong epochs fail.
- **Impact:** A formatter/render binding defect can earn successful consumer assertions while the user sees a false countdown. README claims that DOM agrees with the elapsed result exceed this oracle.
- **Effort:** Small.
- **Risk:** P1 false positive; low repair risk.
- **Confidence:** HIGH, directly reproduced against the exact assertion function.
- **Fix sketch / implementation route:** Assert independent literal actual duration-node text (“1h 31m” or “6h 0m”) and required labels, retaining separate receipt checks.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** Case manifest; probe assert_expected; native3325–3327; ledger7.03,7.09,A04,ES07-11,A09.
- **Acceptance criteria:** Healthy visible literals pass; correct receipt plus incorrect/missing duration fails in every final case.
- **Verification:** Pure adversarial controls, then actual delivery evidence after approval/merge/Pages.
- **Rollback / Plan Closure:** Preserve the failing duration witness; close only against an independently reviewed successor digest.
- **Rejected/deferred rationale:** Not deferred. Later pixel review does not make the current DOM oracle sufficient.
- **Remaining risk:** Correct text does not prove readability or pixels.
- **Route:** DMAIC.

### DELREV-02 — Export failure or absent video can retain assertion-success status

- **Category:** Error-handling honesty / Evidence integrity.
- **Evidence:** Probe290–303 sets ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING before observation export. An exception merely writes exportFailure. No post-close required-video population/integrity check exists. The control reproduces assertion-success with exportFailure, no observations, and no video. Main383 derives exit solely from these statuses.
- **Impact:** A zero-exit acquisition can lack the original observations/video needed for independent presentation and source-association review. This is a missing rejection path, not a claim that Playwright normally drops video.
- **Effort:** Small to medium.
- **Risk:** P1 lost evidence / false-success classification; moderate ordering risk around finalization.
- **Confidence:** HIGH.
- **Fix sketch / implementation route:** Required export failure must terminalize FAILED_OR_UNVERIFIED. Finalize context/video, then inventory/hash/validate required screenshots, receipts and usable video while retaining original failed artifacts. Keep actual pixel acceptance separate.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** Probe acquire_case finally/main aggregation; README35,50,73; state-contract intact-artifact requirement.
- **Acceptance criteria:** Export failure, absent/truncated video or required checkpoint artifact cannot return evidence-complete success; healthy export remains valid.
- **Verification:** Pure export/artifact fault injection; later authorized native video inspection.
- **Rollback / Plan Closure:** Retain every failed attempt; never manufacture replacement pixels or relabel a non-run.
- **Rejected/deferred rationale:** Not deferred. Independent-pixels-pending is an appropriate limit, not a remedy for missing evidence.
- **Remaining risk:** Existence/digests alone do not prove meaningful video or readable output.
- **Route:** DMAIC.

### DELREV-03 — No-handle launch failure is treated as cleaned up, permitting repeated starts

- **Category:** Cleanup / Resource and execution frontier.
- **Evidence:** Handles initialize None at195. If launch204 raises before returning,310–315 executes no close calls and sets ownedCleanupReturned=true from an empty error list. The pure control reproduces true with zero closes. Main369–375 then permits further same-engine cases.
- **Impact:** Unknown startup cleanup becomes positive cleanup evidence; repeated setup failures are attempted as later cases. No real leaked process is asserted.
- **Effort:** Medium.
- **Risk:** P1 control-plane inference; moderate partial-start/finalization repair risk.
- **Confidence:** HIGH for classification and retry eligibility; real OS leakage untested.
- **Fix sketch / implementation route:** Track setup stages and cleanup evidence. A no-handle failure stays cleanup-unknown unless a qualified SDK guarantee or process witness establishes disposal. Stop later starts on unknown cleanup; after established engine setup failure, classify remaining same-engine cells unattempted rather than repeatedly launching.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** Probe startup/finally/main frontier; original R0007 qualification-mechanism contract.
- **Acceptance criteria:** No-handle errors cannot falsely claim owned close; unknown cleanup stops launches; healthy returned-owner closes pass; injected close failures stop the frontier.
- **Verification:** Pure startup/close/launch-count sequence controls, followed only later by separately authorized process verification.
- **Rollback / Plan Closure:** Preserve partial-start receipts. Never replace absent evidence with unconditional success.
- **Rejected/deferred rationale:** Not deferred. Pinned Playwright internally attempts startup cleanup, mitigating ordinary errors, but the probe does not distinguish those paths. SDK cleanup itself includes swallowed close/kill errors; the current blanket “owned SDK close calls” receipt is unsupported.
- **Remaining risk:** Returned SDK close is still not an independent OS process census, as the probe correctly discloses.
- **Route:** DMAIC.

### DELREV-04 — Font completion can provide the recovery wakeup being qualified

- **Category:** Async isolation / Recovery qualification.
- **Evidence:** Probe253 waits for current data/receipt/rows;271 captures unavailable;273–276 releases next data;278–281 waits for adoption and250ms. It never settles stylesheet/font registration or existing dirty work before release. Native3207 sets _renderDirty on font completion;3700 redraws a frozen clock when dirty. The pure recovery case succeeds with both snapshots’ fonts still loading. The exact source-branch control yields zero frozen renders without wakeup and one after cnFontChanged.
- **Impact:** An unrelated font redraw can mask a missing next-day dirty wakeup. Evidence may show eventual recovery but cannot attribute it to accepted-next scheduling; typography can also remain unstable.
- **Effort:** Medium.
- **Risk:** P1 confounded acceptance; moderate risk of substituting a fixed delay or target-polling setup.
- **Confidence:** HIGH for the missing barrier and alternate dirty source. No native mutant was run.
- **Fix sketch / implementation route:** Before release, establish genuine stylesheet registration and relevant font load/error completion plus an observable settled native-loop boundary. Preserve source, clocks, timers and rAF. Do not call render, assign dirty state, advance time or wait for the expected target as setup. If private dirty state cannot be proved without modifying HTML, retain that limit and require separate qualified discrimination.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** Probe recovery; native7–11,3199–3227,3683–3700; ledger7.07,A05,ES07-06. The original state contract already names this confounder in its existing native recipe.
- **Acceptance criteria:** Delayed fonts cannot turn a missing-wakeup negative into recovery credit; healthy same-epoch recovery remains native. Setup, eventual-state and first-presented-frame claims stay distinct.
- **Verification:** Pure sequence checks; later authorized native healthy/negative acquisition retaining setup evidence.
- **Rollback / Plan Closure:** Retain confounded captures; repair evaluator ownership without changing product oracles or protected owners.
- **Rejected/deferred rationale:** Not deferred. Disclaiming earliest-frame proof does not remove wakeup causality requirements.
- **Remaining risk:** Other asynchronous dirty sources and the diagnostic Moon getter require appropriately bounded claims.
- **Route:** DMAIC.

### DELREV-05 — Actual approved head/base objects are not checked

- **Category:** Currentness / Request and merge identity.
- **Evidence:** Probe80–86 checks SHA syntax and equality of declared trees. verify_git98–110 checks merged objects/FETCH_HEAD/blobs, never approval.headSha or approval.baseSha. A pure Git seam supplies approved-head actual tree e… while request declares d…; verification returns normally without querying either approval identity.
- **Impact:** Correct served-byte checks can be attributed to a mistyped or unrelated approved head/base. External authority remains necessary, but this independently checkable discrepancy is missed.
- **Effort:** Medium.
- **Risk:** P2 approval/currentness attribution; repair must honor the actually approved merge strategy.
- **Confidence:** HIGH; contrary-object witness and queried-command boundary are retained.
- **Fix sketch / implementation route:** Resolve actual approved-head tree and compare it to the qualified/merged tree. Verify approved base/ancestry/topology under an explicit supported merge method. Require those immutable objects before acquisition. Preserve external pre/post-main and Pages gates.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** validate/verify_git/request/workflow object gate; AUTH-01,MERGE-01,INT-01.
- **Acceptance criteria:** Wrong/missing approved-head object, incompatible base/ancestry or undeclared merge method fails before HTTP/browser; justified topology passes.
- **Verification:** Pure object-lookup/topology controls; later actual Git/PR/approval/Pages readbacks remain necessary.
- **Rollback / Plan Closure:** Keep template unbound until real approval. Do not rewrite expected identity merely to fit arbitrary main.
- **Rejected/deferred rationale:** Not deferred. The request is not expected to authenticate human intent; named Git objects must nevertheless support its attribution.
- **Remaining risk:** Local checks cannot recreate approval authenticity or continuing Pages success.
- **Route:** DMAIC.

### DELREV-06 — Redirects can bypass the external-request containment boundary

- **Category:** Security boundary / Provider side effects.
- **Evidence:** Probe232–237 continues allowed site/font requests. Installed Playwright1.62.0 coreBundle.js36042–36048 automatically emits Fetch.continueRequest for redirectedFrom without a user route. The extracted-branch control creates a route for the initial request but none for its redirect, which is continued. The probe’s response collection checks config only and cannot prevent destination contact.
- **Impact:** An admitted asset/font redirect can contact an unknown/provider URL outside the allowlist. Unconditional pre-contact containment is therefore unsupported. No real redirect/provider request was made in this review.
- **Effort:** Medium.
- **Risk:** P1 containment gap; moderate transport-timing/representation repair risk.
- **Confidence:** HIGH for Chromium, grounded in the exact pinned SDK and pure branch execution.
- **Fix sketch / implementation route:** Enforce a no-redirect transport or equivalent network boundary. One bounded option: fetch(max_redirects=0), reject3xx, fulfill exact unchanged bytes, and describe that transport honestly. A response listener alone is too late. Block service workers explicitly if route interception is the safety boundary, or separately qualify their routing.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** Probe route_request/context; README ingress promise. SDK coreBundle.js SHA-2563258d1cf334c6afc95f22aa9c292436cb976b391e0437f1359c83b84f0cb9d66; extracted branch SHA-256b8c91cb7f1d057baa236b357d52ad88e6c33c58adcf97531b01511e0bb253c43.
- **Acceptance criteria:** Allowed assets cannot redirect into unknown/provider destination contact; unexpected redirects fail with evidence; healthy content preserves exact approved bytes/source association.
- **Verification:** Pure routing controls and a later authorized isolated native discriminator; no live provider request is required.
- **Rollback / Plan Closure:** Stop acquisition if containment cannot be established; do not continue requests to obtain successful pixels.
- **Rejected/deferred rationale:** Not deferred. Current source has no service-worker registration, so service-worker bypass is related hardening, not a separately claimed observed failure.
- **Remaining risk:** Both engines’ workers, request paths, redirects and finalization require qualification.
- **Route:** DMAIC.

## Intended boundaries and residuals

These are dismissed observations, not additional findings:

- Fixed Date/frozen simTime are intended controlled event inputs. Evidence would invalidate this disposition if promoted to real-time motion or live-provider incidence.
- Four default cases per engine and optional offline behavior are explicitly narrower than the full native/DST/preservation denominator. A subset exit0 must not become whole-owner acceptance; omitted mandatory certificate rows would change this disposition.
- Owner/merge/Pages status strings appropriately record external evidence rather than authenticate it. DELREV-05 concerns independently checkable Git identity. Post-acquisition current-main/Pages readbacks remain real external gates.
- Separate screenshot association and independent first-visible-pixel review are appropriate. This report gives no pixel, lunar, motion, readability, first-frame, Windows, deployment or closure PASS.

The owning root may revise the tool, retain original failures, and request an exact-successor review. An implementer’s repair statement does not close a finding. Rebind after accepted R0017 integration and preserve the pending exact owner head/base/tree decision. Actual acquisition follows only after approval, approved merge, successful normal Pages delivery and currentness readbacks.

No successor implementation is covered by this FINAL report.
