# R0007 Git trace boundary Andon

Report state: **FINAL — bounded diagnosis and recommendations only**  
Entry: direct, explicit cord pull by `/root`, ordinary R0007 executor.  
Return: `/root`. No child routing, repair, release, acceptance, or closure authority is exercised.

## Finding and scope

**The frozen helper has a demonstrated credential-to-file boundary failure in its authenticated Git environment.** An inherited Trace2 target and environment-variable selector survive `child_env()`. `publish_intermediate()` subsequently adds `R0007_PUSH_TOKEN` to that environment. Git writes the selected value to the inherited trace target. A successful push, a clean structured receipt, a clean Git configuration file, and removal of the askpass script can all coexist with this failure. [S1, S2, S4–S8]

This is a local implementation defect with a repeatable mechanism in the publication subprocess boundary. Its scope is broader than one output filename: the same design trusts ambient diagnostic controls whenever it places the credential in a Git process environment. The evidence does not establish a production credential exposure, a remote incident, a defect in the governor, or failure of unrelated R0007 product behavior.

The caller's stated authority covers its R0007 implementation, tests, documentation, and own-branch publication. Exact merge approval remains owner-only. The caller already prohibited hosted execution of the new helper until accepted repair and review; this report recommends retaining that restriction. It neither grants permission nor registers canonical audit state.

## Exact inputs and evidence identity

All paths in the following table are relative to `/workspace/scratch/8726e3e6def5/analysis-r0007/`. Hashes are SHA-256 of the actual bytes read. The original witness and helper were not changed or rerun by this diagnostic task.

| ID | Path | SHA-256 |
| --- | --- | --- |
| S1 | `publication-pack/templates/materialize.py` | `d17689992e2d392e8489018a58cc402676627d076515f99cd311eaee56b8e8d7` |
| S2 | `publication-pack-review/test_trace_boundary.py` | `b828725da99221ede94c38a0b2f7a1112187b63f3b8f7b7260a98a47e589fae2` |
| S3 | `publication-pack-review/trace-boundary.log` | `314f789c4adce630c666245f91cea504a1c132fc468e026ad6bbf9b2dc70dc0f` |
| S4 | `publication-pack-review/fixtures/trace-boundary-r8k7p3jj/witness.json` | `3ed37b0d8212786f27f8ddfd4a59db991ffcab95ce3c716310b7faa508557393` |
| S5 | `publication-pack-review/fixtures/trace-boundary-r8k7p3jj/evidence/git-trace2.jsonl` | `2c5cfef34b575ac571272638d2e10174da1bfeff32fd46c1626cd59da1e41b63` |
| S6 | `publication-pack-review/fixtures/trace-boundary-r8k7p3jj/evidence/push-result.json` | `51b7344aac64ca953b71b771f99a0a72caaa61f9416ce1f7c5a77e7a5451069f` |
| S7 | `publication-pack-review/fixtures/trace-boundary-r8k7p3jj/evidence/push-private/guard-receipt.json` | `b21e1761426aa7d753426de209aa3c885ccb573c9af561c11e19278828d8c7e4` |
| S8 | `publication-pack-review/fixtures/trace-boundary-r8k7p3jj/work/.git/config` | `e5439b002cf9442bc8c033a1cb4fcc6eee951ee00d283d79ac8fed872c154b72` |
| P1 | `publication-trace-andon/git-trace2-config-probe.py` | `8fe211b9853ba5737d63c88127e561796d8df3db648f87ddbb2197e13b1719e9` |
| P2 | `publication-trace-andon/git-trace2-config-probe-result.json` | `a1c3cf3ec1dafc4155b6364bedfde772fa7bc3cbaaa8d851df8dfa64a06c21ff` |

The applied instruction source was `audit-andon` version 0.4.0 at `/home/agent/.codex/skills/remote-skills/skill-6a85962852508191a70c4b0eedbd1928/SKILL.md`, SHA-256 `d774154be7940f88e6402b9d7299f36792e0a636c9023f68fe88b062e2604ff9`. The prior five-line PARTIAL report was SHA-256 `8917dbd47bad8f15bea54564beafca682158c9ded6cf4d3ce3efdd88b9ce7db5`; only the authorized report and bounded nonsecret support files in its directory were written.

### Demonstrated original case

- S2 binds S1 to `d17689992e2d392e8489018a58cc402676627d076515f99cd311eaee56b8e8d7`, builds a local bare-Git fixture, uses a synthetic credential, and patches the remote to a local file URI. It does not use a network endpoint. The test invokes the publication function directly, so it demonstrates that function's boundary; it is not a full hosted workflow or native acceptance run. [S2:20–76]
- S4 and S6 report `REMOTE_REF_VERIFIED_INTERMEDIATE`, `refUpdated: true`, one push attempt, exit code zero, and an accepted guard. The recorded expected intermediate and remote readback both equal `2257c2c5fdad42e11db6c9964032ae8712059dfd`. This diagnosis did not perform an additional ref operation. [S4, S6, S7]
- S5 is 44,881 bytes and 162 JSONL events. A read-only comparison with the synthetic value declared in S2 found seven occurrences, each in a `def_param` event whose `param` is `R0007_PUSH_TOKEN`. Event lines are 62, 70, 82, 104, 113, 119, and 131. Only path, event type, parameter name, counts, and hashes are reported; the value and raw trace lines are not reproduced. [S2, S5]
- The same comparison found no synthetic credential in S6, S7, or S8. S6 reports successful askpass removal. S3 retains the failed assertion that the trace must not persist the credential. These clean artifacts therefore do not establish a clean process-to-file boundary. [S3, S6–S8]
- The original witness records Git 2.52.0. The local transport does not need to consume an authentication credential for the bug to occur: the credential's presence in the process environment is sufficient. No actual credential or remote endpoint was used in the witness. [S2, S4]

### Bounded related-configuration probe

P1 executed only `/usr/bin/git version` with an explicitly constructed environment and a public, nonsecret diagnostic marker. It created no repository, ran no ref operation, and used no network. Its configuration files, trace outputs, and result are confined to this report directory. P2 binds their paths and hashes.

| Probe condition | Observed result |
| --- | --- |
| Global `trace2.envVars` plus `trace2.normalTarget`, `trace2.eventTarget`, and `trace2.perfTarget`; no inherited `GIT_TRACE*` variables | All three target files were created and contained the selected nonsecret marker. |
| Same global configuration, with `GIT_TRACE2=0`, `GIT_TRACE2_EVENT=0`, and `GIT_TRACE2_PERF=0` | None of the three target files was created. |
| Same unused configuration file, but `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1` | None of the three target files was created. |

The probe addressed `/usr/bin/git`, SHA-256 `356db14e102d68a1a37d8a1ac577dfd678d45d46e92f468bef8b7154e7bfdc60`, reporting **Git 2.47.3**. This differs from the original witness's Git 2.52.0. The probe establishes a concrete equivalent global-configuration mechanism on that addressed binary; it does not establish version-independent precedence or substitute for verification using the successor's actual execution Git. [P1, P2]

No other reviewer reports or agent inventory were inspected. The evidence contained no prompt-injection instruction requiring action; source comments and fixture content were treated as data.

## Causal account and local-versus-systemic disposition

1. **Immediate cause:** `child_env()` copies the entire inherited environment and removes only `R0007_UPLOAD_TOKEN` and `R0007_PUSH_TOKEN`. It leaves the inherited trace destination and selector intact. [S1:48–54]
2. **Exposure step:** the push-specific environment is built from that result and receives `R0007_PUSH_TOKEN` immediately before the Git subprocess. The original witness chooses that exact variable for Trace2 emission. [S1:290–297; S2:57–62]
3. **Why output protections missed it:** the helper hashes captured stdout/stderr and writes structured metadata, but an independently configured trace destination is another output channel. Neither those hashes nor the pre-push authorization receipt control that channel. [S1:287–318; S5–S7]
4. **Why cleanup does not repair the event:** removing the token from the Python environment dictionary after subprocess completion and unlinking askpass do not remove bytes already written by Git. In the witness, both normal completion and askpass cleanup occurred after persistence. [S1:306–330; S5, S6]
5. **Why removing one environment key is insufficient:** equivalent global Trace2 configuration can select an environment value and enable normal, event, or performance targets. The current names-only configuration preflight rejects hooks, credentials, URL rewriting, and HTTP extra headers but does not reject `trace2.*`. [S1:254–265; P1, P2]

Further causal expansion would not change the immediate decision. The appropriate repair boundary is authenticated Git diagnostics and their effective environment/configuration, while preserving the existing one-ref guard, forward-child condition, TLS checks, remote readback, and uncertainty accounting.

The mechanism can recur wherever this helper or a copied version adds a secret to an ambiently configured Git process. That is a mechanism-level lesson, not evidence that every caller, owner, or checker is defective. The supplied record supports neither a production blast-radius estimate nor a claim that an attacker controlled the original runtime. Existing reviewer coverage outside these inputs was not inspected.

## Countermeasure options

### Option A — bounded, fail-closed diagnostic boundary

This is the smallest sufficient repair scope recommended for the current case, subject to successor verification:

- Centralize the authenticated Git environment policy before a credential is added. Remove inherited `GIT_TRACE*` controls as a family, not only `GIT_TRACE2_EVENT`; explicitly account for the separate `GIT_CURL_VERBOSE` switch. Set the three Trace2 target controls to disabled values if that policy is chosen, and do not reintroduce inherited selectors or targets later.
- Close the configuration equivalent. A small fail-closed approach is to extend the existing names-only effective-configuration check to refuse the `trace2.*` namespace before credential use, covering included configuration as actually resolved. An alternative is to make effective tracing targets unconditionally disabled in the authenticated environment and prove their precedence against all supported configuration sources. The former makes ambient diagnostic configuration an explicit preflight refusal and requires less dependence on precedence assumptions.
- Apply the same effective environment/configuration policy to preflight and push, so the checked settings are the settings used when the token is present. Keep token-free inspection token-free, and preserve the existing captured-output treatment, guard, exact remote/ref, TLS restrictions, one attempt, and uncertainty handling.

The family-level treatment of `GIT_TRACE_CURL`, `GIT_TRACE_REDACT`, legacy trace controls, and `GIT_CURL_VERBOSE` is preventative boundary coverage. This task did not demonstrate credential leakage through each of those switches and makes no claim about their default redaction behavior. Git configuration injection variables and included files need to be resolved under the chosen policy; their source precedence was not exhaustively probed here.

### Option B — explicit authenticated environment and configuration isolation

Construct a documented allowlist for authenticated Git, retain only the runtime variables it actually requires, then add the controlled askpass/token settings. Isolate system/global Git configuration or supply reviewed configuration explicitly; preserve any required local checks under the same effective policy. Disable diagnostics as a defense even within that controlled environment.

This creates a clearer long-term invariant than a growing exclusion list, but it is a larger compatibility change. The author must show that executable lookup, authentication prompting, required transport/certificate behavior, and Git checks still work. It should not be expanded into a redesign of unrelated builder behavior merely to resolve this witness.

### Inadequate responses

Receipt-only redaction, checking only `.git/config`, deleting the trace after use, removing only the single demonstrated event target, relying on askpass unlinking, or declaring success because the ref updated do not close the demonstrated file boundary. A repair that merely suppresses the test's assertion or discards the witness is also inadequate.

## Escalation recommendation

Return the issue to `/root` as a **credential-boundary defect requiring local repair and independent successor review before credentialed hosted execution**. Preserve the original frozen packet and failing witness, and bind a separately identified successor to its own hashes. The caller has already reported using that separation; this diagnosis did not inspect or accept the successor.

No additional user approval is needed merely to perform the already authorized local repair/tests/docs. This report does not authorize a hosted run, publication, or merge; the caller retains its existing authority limits and the owner retains exact merge approval. Because the evidence uses only a synthetic credential and a local remote, it does not justify asserting an actual compromise or requesting credential rotation on its own. If separately discovered evidence shows a real credential entered this trace path, actual incident handling and retention decisions belong to the caller/owner.

## Follow-up evidence obligations

The repair owner and independent reviewer should obtain the following before recommending that the caller resume the credentialed path:

1. **Preserved RED and exact successor identity.** Keep S1–S8 unchanged, identify the successor helper, manifest, and relevant tests by hash, and demonstrate that the original witness fails for the frozen original while the equivalent check is satisfied by the successor. Do not relabel an old successful result as a successor result.
2. **Positive credential-boundary control.** Run a local bare-Git push with a fresh synthetic marker through the successor's credential-bearing path. Observe the exact single intended update and verify that the marker is absent from all declared trace destinations, logs, structured receipts, generated credential helpers, and Git configuration. This must show that the intended push path ran; a preflight refusal alone cannot substitute for the normal positive case.
3. **Ambient-diagnostics cases.** Cover the demonstrated event target/selector, normal and performance Trace2 targets, and equivalent global configuration. Cover system/global/includes or injected configuration to the extent the successor permits those sources. A forbidden configuration may produce a recorded preflight refusal with no credential-bearing subprocess and no ref update; allowed configuration must not persist the marker. The source/target combination should match the declared policy rather than enumerate unrelated exploit families.
4. **Actual runtime binding.** Repeat the relevant checks with the Git binary/version selected by the execution environment. The original 2.52.0 witness and this 2.47.3 diagnostic probe are separate evidence, not interchangeable validation. Record resolved executable/version and relevant effective policy without exposing values of unrelated environment variables or configuration secrets.
5. **Preserved publication controls.** Demonstrate the normal exact one-ref path and retain meaningful checks for guard refusal, TLS restrictions, and uncertain outcomes. Limit reruns to changed behavior and the concrete controls at risk; this diagnosis does not require a new broad exploit campaign or changes to unrelated product tests.
6. **Independent conclusion and caller decision.** The reviewer should state precisely which file-boundary claims the evidence supports and any remaining limitations. `/root` owns acceptance, currentness, and the decision to resume within its commission. Neither this FINAL diagnostic report nor any probe result supplies PASS, AUDIT_COMPLETE, release, or closure authority.

A durable prevention rule for this helper is: **adding a secret to a subprocess environment also requires controlling that process's independent logging destinations and selectors**. Retain one real failing witness and its successor regression as the local learning artifact; broader organizational conclusions need broader evidence.
