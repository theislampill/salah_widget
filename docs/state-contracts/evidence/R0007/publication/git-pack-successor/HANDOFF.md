# R0007 Git pack successor — frozen author handoff

## Result and authority

The bounded trace-boundary repair is ready for independent successor review. The final local producer ran **31 tests, all passing**: the original 23 boundary controls plus eight new diagnostic controls. This is author-side implementation evidence, not independent acceptance or permission for hosted use.

Root commissioned this separate directory after confirming finding P1 and accepted Option A of the bounded Andon recommendation. The exact independent review and diagnosis were consumed and copied unchanged to `review/review.md` and `review/andon-report.md`. Their findings supplied evidence; root's explicit commission supplied implementation authority. No new reviewer was spawned by this author.

All writes stayed under `analysis-r0007/publication-pack-successor`, including disposable local Git fixtures. The original `publication-pack/FROZEN-PACKET.json` remains SHA256 `a2edbe76df05e3d7b2ba8470a37c19c8f28587c1fce3d94c9298d66191826f84`; all 100 bound original files reverified unchanged. The original review/test/log and Andon report also match their preserved copies. No active candidate, real remote, hosted workflow, credentials, or actual final payload was used or changed.

## Concrete defect and minimal correction

The original helper removed the credential variables from ordinary child environments, then added the push credential to a copied environment that still carried Git diagnostic targets/selectors. Real Git could independently write that credential to a Trace2 file even while the exact ref update and structured receipt were correct. Equivalent global Trace2 configuration reproduced the same file escape.

Only `templates/materialize.py` changes in production:

- `child_env()` excludes the inherited `GIT_TRACE*` family and separate `GIT_CURL_VERBOSE` switch from controlled subprocess environments. It still removes both job/push token variables; only the existing authenticated push path attaches its dedicated credential later. The parent environment is not changed.
- The existing names-only effective configuration check now also refuses every `trace2.*` key before credential attachment. `git config --includes --name-only --list` resolves the checked names, including supported included/injected sources. Existing config files and hooks are retained. This policy rejects diagnostic configuration rather than changing it or depending on override precedence.

No trace evidence is scrubbed or deleted as a repair. The existing raw-output hashing and fixed refusal classes remain. The normal one-ref push, private advertisement guard, exact seed/tree/ancestry, TLS checks, remote readback, one attempt and uncertain-outcome handling are unchanged. The preparer, workflow and original three control files are byte-identical to the frozen originals. `scope-verification.json` records that every materializer AST node outside `child_env` and `publish_intermediate` is unchanged.

## RED and GREEN evidence

`trace-red.*` preserves the initial four failures against the byte-identical original helper: the reviewer's event environment scenario and all three global Trace2 targets persisted the synthetic credential. The tested source at that point is preserved in `baseline/test_trace_boundary-red-v1.py`.

`trace-expanded-red.*` preserves the expanded eight-case run against that same original helper. Seven cases demonstrated credential persistence. The injected `GIT_CONFIG_COUNT` case did not activate a trace on this Git runtime; it failed the required fail-closed policy because the original helper admitted and performed the push. This case is configuration-policy coverage, not an eighth demonstrated credential leak. Its tested source is preserved in `baseline/test_trace_boundary-red-v2.py` and is byte-identical to the final trace control.

| New control | Original result | Successor result |
| --- | --- | --- |
| Trace2 event environment | Credential persisted during successful local push | Exact local push verified; no trace file or credential persistence |
| Trace2 normal environment | Credential persisted during successful local push | Exact local push verified; no trace file or credential persistence |
| Trace2 performance environment | Credential persisted during successful local push | Exact local push verified; no trace file or credential persistence |
| Global event target | Credential persisted during successful local push | Refused before push; zero attempts; config/ref unchanged |
| Global normal target | Credential persisted during successful local push | Refused before push; zero attempts; config/ref unchanged |
| Global performance target | Credential persisted during successful local push | Refused before push; zero attempts; config/ref unchanged |
| Included global event configuration | Credential persisted during successful local push | Refused before push; zero attempts; config/ref unchanged |
| Injected configuration count | Trace inactive; push incorrectly admitted under chosen policy | Refused before push; zero attempts; config/ref unchanged |

Global/included diagnostic configuration can create a trace during token-free inspection before refusal. In the GREEN fixtures those files contain no synthetic credential and remain retained; the claim is credential confinement, not absence of all trace files. Each trace control scans every regular file in its disposable fixture for the synthetic marker, checks structured receipts and verifies preserved config/parent environment. The three environment cases explicitly exercise successful credential-bearing publication, so an always-refusing implementation cannot pass.

The original 23 controls were rerun unchanged. They retain the real clean-environment positive push, advanced/rewound/wrong/multiple-ref refusal, existing hook/config refusal, exact target/seed workflow preservation, depth-four ancestry and reconstruction, credential prompts/exclusion, and completed-write-then-timeout uncertainty with no replay.

`final-tests.json` binds the command, timestamps, helper and trace-test digests. `final-tests.log` SHA256 is `f341efe9b049957c39b89b02c8cc1781f683ff688edb871c06db353b7e522999`; it reports 31 tests in 3.507 seconds and exit 0. No optional broad campaign was run after this result.

## Actual runtime and limits

The new real-Git witnesses used `/usr/local/bin/git`, Git **2.52.0**, executable SHA256 `8a2ae22e7898e163330a96319b541f92ed6f90fc87576414f72c5a89aa1dc352`. Per-case witnesses bind that runtime. The diagnosis's separate Git 2.47.3 probe is not counted as successor validation.

All test endpoints were local disposable bare repositories; production endpoint/ref remain fixed with no runtime override. No live GitHub authentication, policy, pack transfer or actual large target was tested. No claim is made about arbitrary hostile runner code or exhaustive Git diagnostic behavior across all future versions. The tested effective configuration routes are direct global, included global and `GIT_CONFIG_COUNT`; the common names-only refusal is not restricted to those origins. System-wide and every alternative injection syntax were not separately exercised.

Root still owns independent successor review, eventual explicit immutable target selection, actual target preparation/dry reconstruction, hosted operation and independent reconciliation of any uncertain write. The exact six-path connector finalization remains unchanged. Both previous REST 422 causes remain unknown. This repair supplies no broader credential/principal authority and no native, integration, merge or lifecycle conclusion.

## Exact deliverables

`successor-changes.diff` contains the bounded production change and added trace control. `source-hashes.json` records exact source/test/diff identities. `FROZEN-PACKET.json` binds this report, sources, controls, input copies, producer records, selected fixture receipts and retained synthetic trace/config evidence. Disposable Git object databases remain available but are not separately included in that manifest.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `prepare_payload.py` | 7994 | `42e5c247d8c72555532df356943a41257db903c9b524775489e1567a9482896a` |
| `templates/materialize.py` | 26702 | `a8f29b539550f7664a67856c55637cdc18ea9fcf7c59cffc65660e05ca19bc83` |
| `templates/r0007-materialize.yml` | 2303 | `cea1f7925de6e02b929163f0780b4f79960fd4e6f9d1fb4fe61eda957bb65574` |
| `tests/test_trace_boundary.py` | 8289 | `01123e1272acb496e1e1b1f6cf4de9c54eeb31584432a4b2af35069e676ef861` |
| `successor-changes.diff` | 10371 | `8c80228010934cb14ce37a967fd5d66094ab4fa165636fd2532f855c4f5d8035` |

The author stops writes at the frozen successor packet. Root owns the next independent review and any decision to resume within the existing commission.
