# R0007 Git pack helper — frozen author handoff

## Outcome and scope

The new helper implementation is ready for independent review at its local helper scope. The final focused producer run passed **23 of 23 controls** with exit code 0. This packet does not authorize hosted execution, establish native acceptance, or close publication.

The owned implementation is isolated under `analysis-r0007/publication-pack`. The three historical REST helper files remain byte-identical to the preserved originals. No active candidate, active branch, remote repository or browser was changed. All push tests used disposable local bare Git repositories. No final payload was prepared against an actual candidate.

## Selected behavior

The preparer accepts a full immutable clean target SHA and binds its exact tree, patch, changed blob identities and the explicit three-ancestor chain. Defaults bind the next executing seed to parent `3b2d09c748f71dc77806882f62f7339cbd18f19c`, whose parent is `19004279805604ef5e41292ffd4e9f442e1321f2`, whose parent is base `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`. Each prior/executing seed must retain exactly the four cumulative bootstrap paths relative to base. The workflow fetch depth is four.

After reconstruction verifies the exact target tree and file identities, the materializer builds an intermediate tree containing all exact target non-workflow content plus the executing seed's exact four bootstrap files and complete workflow subtree. It proves the complete tree equation, subtree equality and exact six-path difference to the final target. The intermediate commit has the executing seed as its sole parent.

The only production push destination is `https://github.com/theislampill/salah_widget.git`; the only allowed ref is `refs/heads/pro/r0007-explicit-next-event-state-20261106`. Publication uses one explicit SHA-to-ref normal push. A credential-free preflight checks the expected executing seed. A private pre-push guard independently checks the advertised old SHA, exact new SHA, exact remote/ref and one update. Existing hook, credential/rewrite configuration or disabled TLS verification causes refusal; the helper does not replace an existing pre-push gate. Production has no local-remote override.

The workflow supplies the normal job credential to the materializer process. Builder and ordinary Git subprocess environments remove both token variables. The authenticated push process tree alone receives the dedicated push credential variable. A token-free askpass script answers only exact fixed HTTPS repository prompts; redirects are disabled and credential path matching is enabled. No credential is put in the Git URL, argv, configuration, script bytes, receipt or raw command log. Synthetic tests exercise the exact Git credential prompt behavior.

Before the push call, the helper persists intent and an unknown write outcome. It records push output only as byte counts and digests, plus fixed status classes; arbitrary Git response text is not retained. A timeout, rejected command, unavailable readback or other unverified result remains `PUSH_UNCERTAIN` with `refUpdated: null`. There is one push call and no retry. Verified success requires exit 0, an accepted private guard receipt and a matching credential-free remote readback. The workflow launcher itself reports an unknown effect and directs inspection to attempt receipts.

## Evidence

`final-tests.json` records the exact command and timestamps. `final-tests.log` has SHA256 `b11b486abd43e5a2cad8eb7130939edb14d67faa1243b6b2afab18dd5ca18edc` and reports 23 tests, all passing.

| Controls | Count | Concrete coverage |
| --- | ---: | --- |
| Push boundary | 15 | Real bare-Git single-ref success; advanced/rewound heads; a rewind between preflight and real push; wrong/multiple updates; exact remote/new/old/ref guard; preserved existing hooks/config; synthetic credential exclusion; completed write followed by client timeout, unknown outcome and no replay |
| Chain and trees | 6 | Exact three ancestors; wrong parent/edge and extra runtime path refusal; complete target-product/seed-workflow preservation; exact six-path finalization; unplanned workflow refusal; preparer and actual depth-four fixture reconstruction, including two deferred workflow entries |
| Authentication boundary | 2 | Real local `git credential fill` produces exact intended prompts; other host/path/scheme/arbitrary prompts receive no credential |

Original failing evidence remains in `tree-red.*`, `push-red.*`, `auth-red.*` and `workflow-receipt-red.*`; no failure record was overwritten. Earlier passing evidence remains in `tree-green-1.*` and `combined-green-attempt-1.*`. Python sources/tests parsed successfully; YAML parsed with Contents-write only, depth four and persisted checkout credentials disabled. The tests are author-side controls, not an independent assessment.

`helper-changes.diff` compares only the three new production helper files with their preserved historical inputs. `frozen-source-hashes.json` records the exact source/test/design/plan hashes. `FROZEN-PACKET.json` binds the handoff, sources, tests, producer records, original helpers and selected local fixture receipts; disposable Git object databases are retained for inspection but are not reviewer inputs in that manifest.

## Frozen production files

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `prepare_payload.py` | 7994 | `42e5c247d8c72555532df356943a41257db903c9b524775489e1567a9482896a` |
| `templates/materialize.py` | 26474 | `d17689992e2d392e8489018a58cc402676627d076515f99cd311eaee56b8e8d7` |
| `templates/r0007-materialize.yml` | 2303 | `cea1f7925de6e02b929163f0780b4f79960fd4e6f9d1fb4fe61eda957bb65574` |

## Remaining boundaries and root-owned steps

No live GitHub push or actual large pack transport was exercised here. Local tests establish the bounded mechanics; hosted authentication, repository policy and the real pack remain untested at this author scope. Both prior REST 422 causes remain unknown; the Git route is a materially different supported transport countermeasure, not a retrospective causal explanation.

Root reported clean candidate `e46f9dae61b2990a2b5dd5007feaa8342bd0b748`, tree `6934f644f150dd2d41edb872b528b99fcd51f29b`, with separate candidate review active. This is context from root, not this packet's final target binding. Root may advance it for evidence. The preparer must be called later with the selected full immutable target, after fresh independent helper review. Root owns the actual target dry rebuild and all external effects.

Credential-free readback can be unavailable. Any uncertain attempt requires root's independent current-state reconciliation; no unchanged retry or automatic replay is authorized by this helper. The private intent/guard/outcome files persist; the askpass program is removed, and the disposable checkout's installed guard is left in place so a subsequent invocation cannot silently reuse the lane. The artifact contains no exported job credential.

After independently verifying the intermediate remote commit/tree, root's connector finalization must be a sole-parent commit over that intermediate, with the exact target tree and exactly these six paths: add `.github/workflows/r0007-native.yml` and `.github/workflows/r0007-public-delivery.yml`; remove `.github/workflows/r0007-materialize.yml`, `.github/r0007-bootstrap/materialize.py`, `.github/r0007-bootstrap/manifest.json` and `.github/r0007-bootstrap/source.patch`. The two target workflow blobs are reported in the structured summary. Root reports those existing remote blobs already verified; this lane did not upload or verify them remotely. Bootstrap files remain in prior branch history after removal from the final tree.

The author has stopped writes at this packet. Independent review, hosted use, finalization and acceptance/closure remain with root under the user's existing authority.
