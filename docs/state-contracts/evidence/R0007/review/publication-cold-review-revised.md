# R0007 publication bootstrap — independent revision review

## Scoped disposition

**PASS — limited to the revised publication templates and the correction of the original seed-enumeration and pathname findings at the hashes below.** The required R1 correction is present and mechanically adequate. The targeted R2 pathspec and ASCII-control issues are also addressed. I found no new effect, credential, or identity regression introduced by this narrow revision.

The final corrected candidate has not been bound or dry-reconstructed in this review. Actual connector/workflow permissions, large-blob API transport, the final tree assembly, and the expected-seed ref transaction remain unverified prerequisites. This report supplies independent code findings for root reconciliation; it grants no publication, merge, acceptance, or audit-closure authority.

## Exact reviewed revision

I independently reread both changed Python files and rehashed the workflow template. To establish the change boundary, I reversed only the reported edits in memory and computed SHA-256 over the resulting text. Those reconstructed originals matched the exact hashes from the first review:

- Materializer original: `397dc0aff21bcb58a94f5566c4d7a89a0b039862622590e4efc40da1201cfeda`.
- Preparer original: `da75ad3c7d00663433e8d8f1ceb2c945d6eb2b078311f1f8db506d6e2c6967ae`.

That confirms the inspected revision consists only of the seed-diff change, ASCII-control rejection, materializer literal-pathspec environment setting, and preparer literal-pathspec environment setting/import. The workflow template is byte-identical to the first review.

| File | Bytes | Reviewed SHA-256 |
| --- | ---: | --- |
| `prepare_payload.py` | 5,981 | `d4c9328546107b3bd8d2e0f4ed07a6604ed7271d9027576a0765afcbf291b6a7` |
| `templates/materialize.py` | 13,502 | `a7540a232b8a8463b21b6b4248c74cdc51381519156f5b23e7271b13682fe526` |
| `templates/r0007-materialize.yml` | 2,270 | `8bfc4bc26b191051c84ff11fdd13153df1266909c9dc8a44dd69ecda31b1ec8d` |

## Findings on the corrections

### R1 — Required seed guard corrected

`materialize.py:163–167` now enumerates the base-to-seed delta using `git diff --no-renames --name-only -z` and splits on NUL. Rename detection can no longer hide the removed source behind a destination name, and newline-bearing names cannot be divided into separate apparent paths. Empty trailing records are discarded. The existing checks still require exactly the four reserved names and a single parent equal to the manifest base.

Together with the preparer's existing requirement that the four seed paths are absent from both base and target, this supplies the intended changed-path proof for a correctly prepared seed. The external connector must still construct and verify that seed from the intended accepted base and exact prepared bytes.

### R2 — Pathspec interpretation and ASCII controls corrected

`materialize.py:46–49` now rejects all ASCII control characters and DEL. The existing absolute-path, traversal, backslash, empty-component, `.git`, duplicate-name, and reserved-path checks remain intact.

`child_env` now forces `GIT_LITERAL_PATHSPECS=1` while preserving removal of `R0007_UPLOAD_TOKEN`. Every actual materializer Git invocation either obtains that environment directly or receives the candidate-index environment derived from it. Thus names such as `:(glob)**` are treated as literal names rather than selectors. The setting also reaches the fixed command runner used for indexed patch application and staging.

The preparer's Git helper independently forces the same setting in a copied environment. Its standalone `merge-base --is-ancestor` call takes validated commit IDs and no pathname arguments, so it does not require pathspec handling. The helper does not modify the preparer's parent environment.

Some Git-output readers still use text quoting or line-oriented decoding, so this purpose-built tool should not be advertised as supporting every possible legal Git filename. That broader feature is unnecessary for the observed ordinary R0007 paths; the original pathspec-expansion and ASCII-control concerns are addressed.

## Verification actually performed

All checks were local and read-only except writing this report. I did not prepare a real payload, run a builder, mutate a checkout/index/ref, upload, contact the network, invoke a workflow, or launch a browser.

| Check | Result |
| --- | --- |
| Python AST parse of both revised programs | Passed |
| Reverse only the declared edits and compare original hashes | Both exact original hashes reproduced |
| All 32 ASCII controls plus DEL inserted into a pathname | All 33 rejected |
| Ordinary names and prior traversal/absolute-path cases | Expected acceptance/rejection retained |
| Child environment with fake token and inherited literal setting of `0` | Token omitted; literal setting forced to `1` |
| Mocked preparer Git invocation | Literal setting forced to `1`; parent environment unchanged |
| Real read-only `git --no-optional-locks ls-files` with literal environment | Ordinary tracked path returned; `:(glob)**` did not expand |
| In-memory evaluation of the actual seed-delta expression | Exact four names matched; an extra removed runtime path and a newline-bearing extra path were rejected by set inequality; required flags were asserted |

The original review's mocked upload success/failure coverage remains applicable because the upload implementation is byte-identical. I did not repeat remote-capability claims or convert local helper checks into reconstruction evidence.

## Conditions retained from the first review

The normal `contents: write` job permission remains broader than the Python program's fixed blob endpoint. Its bounded behavior depends on trusted reviewed executable inputs. The earlier inspection found the builder and its Python helper closure identical to the accepted baseline; the final sealed candidate still needs its executable-input comparison, including absence of newly introduced import-shadowing modules.

Before any seed publication, bind the clean corrected target and intended accepted base; verify the four prepared files and digest relationships; and complete the planned disposable reconstruction of that real payload. The seed operation must respect actual connector permissions and an unexpected existing branch head must stop the operation.

Before the final owner-branch update, bind successful terminal evidence to the expected seed, run/attempt, manifest, full target tree, and complete blob set. Verify the connector-assembled tree, bootstrap-file removal, and final commit parent. The chosen ref operation must enforce the expected seed, and the independent R0017/R000B branches and integration order must remain intact. None of those future effects is claimed completed here.

The original report remains retained as the record of the earlier hashes. This revised disposition applies only to the three hashes in this report.
