# R000B F02 / SR-01 repaired source review

## PARTIAL — frozen repair under independent review

This is a source-only review of the frozen overlay on `d124f050ec68fa8608022b1ed5fead426d42dcb9` / tree `54c61ab27f95adcf0837f737ca3dfd09649fc5c3`. It does not establish native pixels, generated qualification, final candidate acceptance or whole-contract closure.

The inspected authored source SHA-256 is `fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327`. The inspected `tests/weather-no-timetable-handoff.test.cjs` SHA-256 is `f1669a82fa40691e0179372b282a41a9e369147887cec8f89c6f88ad58b23110`. Only those two repository files are dirty. All preflight inputs and original artifact digests are recorded in `source-f02-preflight.json`.

The repair places the consumed present-evidence identity/lease check before the same-record shortcut and adds evidence identity, render code and condition state to cloud receipt deduplication. No change to admission, TTL, model, painter, motion, effects or native lifecycle is present in the source diff.

Independent current execution of the handoff and native-weather-withdrawal suites completed with **53 pass / 0 fail / 0 skipped / 0 TODO**; raw log: `source-f02-current-tests.log`. This is execution through controlled source/DOM/clock/canvas boundaries, not browser execution. Existing test names are correlated with the root's run and are not independent experiments merely because rerun here.

Remaining: independently rerun the original scenario with corrected expectations, exercise same-record expiry/replacement and async publication orderings, verify semantic receipt deduplication, then bind the final disposition to unchanged input hashes. Original `source-lease-probe.cjs`, output and SR-01 report remain untouched.

---

## FINAL — PASS for the bounded SR-01 source remedy

**Final check: 2026-11-10T05:53:04.090436+00:00.** The frozen source remedy resolves both demonstrated manifestations of SR-01 under the reviewed source/consumer boundaries. No further source finding was demonstrated. This is a PASS for the **SR-01 source remedy in this exact dirty overlay**, returned to root for adjudication. It is not final-candidate, native-pixel, generated-output, delivery, B01–B18/ES0B-wide, or whole-RLGWO acceptance.

### Identity and change boundary

| Input | Exact identity |
|---|---|
| Underlying commit / tree | `d124f050ec68fa8608022b1ed5fead426d42dcb9` / `54c61ab27f95adcf0837f737ca3dfd09649fc5c3` |
| Repaired `src/native/index.html` SHA-256 | `fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327` |
| Repaired handoff test SHA-256 | `f1669a82fa40691e0179372b282a41a9e369147887cec8f89c6f88ad58b23110` |
| Pre-repair authored source SHA-256 | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |
| Frozen authored diff SHA-256 | `f7c6f338ecccd7542752c040025cc16ba3636427feabb4436730f44f312253c3` |
| Frozen test diff SHA-256 | `81cfdcaa3eae2f1c5e9ab730bfd03706580435e157199681a85dff56660ace88` |

HEAD and tree remained unchanged. Repository status at the beginning and end consists of exactly the authored source and handoff test modifications. `git diff --check` exited 0. This reviewer changed neither repository file. The root's prospective scope document was read as the assigned boundary; it did not override the original behavior obligations or confer independent acceptance authority.

The production delta is limited to `cloudAuthorityMatches()` and `publishCloudAuthority()`. The admission, source/receipt thresholds, prayer model, existing retry/request mechanism, cloud painter/motion arithmetic, weather-effect policy and native publication/lifecycle implementations have no new edit in this repair.

### Independent current executions

Two types of fresh execution were performed:

| Evidence | Result | Meaning |
|---|---:|---|
| Existing `weather-no-timetable-handoff.test.cjs` plus `real-sky/native-weather-withdrawal.test.mjs` | 53 pass, 0 fail, 0 skipped, 0 TODO | Fresh execution of affected existing fixtures/oracles, including ordinary healthy A→B and native source publication joins. These are the same test family used elsewhere and are not 53 independent experiments. |
| New reviewer-owned `source-f02-independent.cjs` | 37 pass, 0 fail | 35 repaired-source schedules plus two old-source discriminators, covering original failures, boundaries, positive preservation, semantic deduplication and actual async publication owners. No repository test was modified. |

Commands executed with Node v24.22.1:

```text
node --test tests/weather-no-timetable-handoff.test.cjs tests/real-sky/native-weather-withdrawal.test.mjs
node /workspace/scratch/d9a9ea2be931/recovery/source-f02-independent.cjs
```

Both commands exited 0. Logs, structured observations, code, frozen diffs and all source/helper identities are retained beside this report. The new probe shares the reviewed authored-runtime fixture for contained DOM/clock/transport setup, but defines its own scenarios and assertions. Its native tests execute the actual foreground capture and solar-mask publication classes, actual host hooks, the actual preview owner, and exact refined compose/clear/failure source slices. Browser canvas readback, image decode, numerical-sky output and scheduling are controlled boundaries. The alpha sentinel is not a browser pixel and the test counters are not native timing evidence.

### Original counterexamples, now discriminated

The reviewer did not rewrite or rerun the old contrary artifact in place. The new probe reconstructs both original schedules with corrected expected outcomes and also runs them against the old source read directly from the immutable underlying commit.

**Original expiry schedule:** a real clear SIM record remains fixed while an admitted 1-second wet/rain fixture publishes the fallback cloud deck `[0.9, 0.85, 0.3]`. At the exact lease end, the pure guard now refuses that old receipt. The actual no-model render and painter then leave coverage and targets `[0, 0, 0]`, readiness false, density zero and zero current raster fills. The underlying clear SIM record remains selected; the current consumed code is 0 and its receipt identifies `withdrawn-unavailable` coverage with the reason `complete atmosphere unavailable`. This correctly separates a supported clear underlying model from withdrawn observation-derived cloud material.

**Original replacement schedule:** a fresh admitted dry fixture replaces the old wet fixture while the model record stays identical. The complete render publishes a new receipt bound to the new evidence and code 0. The old receipt is rejected. Coverage follows the existing one-step 0.08 easing rule to `[0.8280000000000001, 0.782, 0.27599999999999997]`, with targets `[0, 0, 0]`; population and motion axes remain unchanged at the held monotonic instant.

Against the old source, those same controls fail at the specifically named assertions:

- `independent original expiry oracle: consumed evidence revoked` (`true !== false`);
- `independent original replacement oracle: new consumed evidence identity`.

Only the expected assertion type and named consumer assertion were accepted as discrimination. No syntax/setup rejection was counted as an old-source failure.

### Boundary, preservation and async controls

The 37 reviewer controls include:

- **999/1000/1001 ms, each with and without a real prayer model:** the old receipt remains valid at 999 ms and is refused at 1000/1001 ms. Actual foreground capture retains supported material before expiry and clears readiness/coverage/targets/density/raw raster at and after expiry. The pure final guard does not mutate state, raster or request counts. Capture withdrawal preserves the population and accumulated axes.
- **Unchanged current evidence in both capture-before-render and render-before-capture orders, model present and model absent:** the active receipt object and supported coverage remain stable. The no-model warm-retention policy is preserved.
- **Ordinary model-only healthy A→B refresh in both orders:** both independently admitted records remain eligible, capture-first retains the still-current A deck, and the complete render consumes B with exactly one 0.08 easing step. The resulting coverage remains `[0.9104, 0.888, 0.592]`; population and held axes are preserved, and B publication rejects A's old receipt.
- **Fresh same-record wet and dry replacements, model present and absent:** complete publication binds the newly admitted evidence even when the condition remains wet. Without a model the replacement is withheld; genuine prayer admission followed by ordinary complete publication recovers current coverage. Repeated unchanged complete publication keeps the new receipt stable.
- **Ancillary decision changes:** expiration of surrounding/nearby information and admission of a forecast change the candidate decision without changing its cloud authority inputs. Complete rendering retains the active cloud receipt; it does not churn simply because the whole decision object changed.
- **Fourteen actual pending-decode schedules:** preview and refined owners each exercise unchanged model/no-model, expired model/no-model, freshly published wet/dry evidence, and fresh replacement without a model. Supported old captures publish only when their receipt remains valid. Expired/replaced old receipts cannot publish as the active consumption; the owner publishes the current successor and its diagnostic receipt matches the actual active publication. Re-resolving the obsolete promise adds no draw.
- **Actual refined same-byte reuse:** a fresh wet publication acquires a new receipt while its cloud sentinel bytes remain unchanged. The reuse path updates consumed provenance without an unnecessary raster draw; the old receipt remains invalid.

The actual painter may continue its existing bounded phase integration when real elapsed time advances, including while a deck is empty. The repair does not reset phases. The held-time controls distinguish preservation from simply forcing the entire painter to stop.

### Assessment of the receipt identity fields

The added evidence identity check is necessary. A model record alone is not the complete authority when a separate present observation supplied the effective condition and fallback cloud layers. Checking the originally consumed evidence before either record branch closes the demonstrated hole without lending it the replacement's lease or changing any TTL.

The extended deduplication key is sufficient for the inspected current consumer dependencies:

- Existing record identity covers the admitted model measurements under the existing source-owned read-only record convention.
- Existing target/generation, lane, scene and mode fields cover ownership and selected-clock contracts.
- **Present-evidence identity** distinguishes separately admitted sources, including wet→wet replacement where all visible values happen to match. It also distinguishes evidence expiration/removal.
- **Render code and condition state** directly identify the material/classification and receipt wording being consumed. Keeping these inexpensive semantic checks is appropriate; no demonstrated healthy-path churn results.

No additional whole-decision identity requirement is warranted by this repair. Weather decisions also contain forecast, nearby and approach information that does not supply cloud coverage/tint. The independent ancillary-information controls show why a new decision object alone should not force a new cloud receipt. Physical particle/effect consumption has its separate receipt and is not silently absorbed by this key. Future cloud inputs added outside the currently bound record/evidence/classification must extend their owner contract at that time.

The different-record branch still repeats the same present-evidence condition after the new common precheck. That is logically redundant but harmless and preserves the previously inspected handoff expression. It is not a correctness finding or a reason to broaden this bounded repair.

### SR-01 disposition

| Required finding field | Final source disposition |
|---|---|
| Priority / owner | Original P2, R000B native cloud-publication consumer at N09→N15/N13 |
| Original evidence | Unchanged `source-audit.md`, original probe and original output; both current independent old-source controls reproduce the named defects |
| Countermeasure | Common consumed-evidence identity/eligibility guard plus semantic receipt deduplication |
| Verification | Original scenarios now pass; old source fails named assertions; 35 independent repaired-source schedules, two old-source discriminators and 53 affected suite tests pass |
| Consequence after repair | Expired same-record present authority is rejected; actual new same-record publication acquires its own receipt; supported ordinary authority and easing remain preserved |
| Source disposition | **Resolved within this exact frozen source overlay; bounded remedy PASS** |
| Residual risk | No native rendered observation, generated rebuild/parity, browser engine qualification, deployment or whole-obligation acceptance was performed here |

Root retains final disposition and any subsequent mutation/integration authority. This report does not alter R0007, R000D, R0021, R0024 or R0025 ownership, establish whole-RLGWO completion, or re-certify unaffected historical rows. Generated files still require the separately planned canonical rebuild and qualification against these repaired authored bytes.

### Evidence identity register and preservation

All artifact paths below are relative to `/workspace/scratch/d9a9ea2be931/recovery/`.

| Artifact | SHA-256 |
|---|---|
| `source-f02-preflight.json` | `52f1229f9f1ca03b5cf07539d657611f31c689236680761561965e37d2aa0688` |
| `source-f02-current-tests.log` | `36da79d2458514d530903217e1a775a5163eb03bc6ef8524fc88d6c4de7c6b5f` |
| `source-f02-independent.cjs` | `56d2978d057f2e30126972411144a04cd6a420fb4b4f1f15d66c3f1555b3c322` |
| `source-f02-independent.json` | `556b7e9c6a435f5fbeb778fb8a051e029a06c49c7a576e5eeb66a12bf6d6d53d` |
| `source-f02-independent.log` | `2caf689b926428a9f24fc062293f1e5e550f2ddda0afe95baf581c728a1da6e5` |
| `source-f02-authored.diff` | `f7c6f338ecccd7542752c040025cc16ba3636427feabb4436730f44f312253c3` |
| `source-f02-tests.diff` | `81cfdcaa3eae2f1c5e9ab730bfd03706580435e157199681a85dff56660ace88` |
| `source-f02-final-identities.json` | `ded77503fd9ff9d5a0b37698e06c498b78595bba0f417f11767d04be0f4681cf` |

`source-f02-final-identities.json` records the final time, underlying commit/tree, exact dirty-file list, Node version, complete relevant input hashes, artifact hashes and comparison results. All eight frozen source/test/helper/module inputs matched their preflight hashes. All four original review/probe/read-set artifacts matched their preflight hashes. In particular, the original contrary probe remains `c0500e9cab8cfb39e09037f6de51ab37594f14181d2c17492249f02a1c3fcbc6` and its original output remains `439876f6713c6ebaa458e2d12860781160cc374ab3e3234e85dedfae00f1f4be`.

No repository source/test/documentation modification, Git mutation, shared browser use, network mutation, release or publication was performed by this reviewer.

