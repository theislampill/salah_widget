# R0013 implementation handoff

## Outcome and custody

R0013 installer/discovery implementation is frozen and returned to root. This worker made no commit, push, remote mutation, real-home installation or real browser/clipboard action. The final immutable source/fixture observation is `r0013-source-freeze-2.json`; the first snapshot is retained as `r0013-source-freeze-1.json`. Root owns subsequent integration, fresh independent review, native evidence, source pinning and complete acceptance. This report is evidence, not closure authority.

Final installer SHA-256 values:

- `install.sh`: `609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22`
- `install.ps1`: `a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4`

The full recovered original/amended contract remains in `r0013_contract_report.md` and `r0013_contract_matrix.json`: twelve original parent rows, seven residual children and fourteen ES13 rows. `r0013_implementation_matrix.json` adds a scoped local implementation overlay without replacing that denominator.

## Changes and source boundaries

- Bash `firefox_status` at `install.sh:281` emits one explicit seven-field knowledge record. Unsupported shapes, missing/read-failing/malformed/invalid-encoding/insufficient metadata are unknown. JSON parsing rejects duplicate keys and NaN/Infinity constants. Percent escaping prevents match text from shifting fields or emitting ASCII terminal controls. No-Python text matches remain hints and never certify absence.
- PowerShell `Test-StrictJson` at `install.ps1:239` validates contiguous strict JSON tokens, object/array state, complete root consumption and decoded duplicate property names before host conversion. Its key sets also reject case-insensitive ambiguity in the downstream PowerShell object. It has no compiler, subprocess, external package or filesystem/network effect. `Get-FirefoxExtensionStatus` at line310 returns knowledge plus bounded reason/evidence/source, guards singleton-array unwrapping and keeps old positive fields.
- Bash `add_target` at line418 preserves the original thirteen fields and appends four knowledge/source fields. All five real reads migrate together. PowerShell `Get-Targets` at line389 projects the corresponding four properties. Existing profile/browser identity and positive flags remain.
- `discovery_eligibility` at Bash388 and `Get-DiscoveryEligibility` at PS378 derive one rule: legacy hint first => refused; known-new/neither => eligible; all other states => held. Menu, early preview, pre-initialization selection and dispatch use it. Initialization is after selected counts at Bash837 / PS723. Unknown-only selection fails before effects; mixed safe peers remain usable; neither all nor explicit selection overrides a hold.
- Both Bash profile producers read NUL-delimited find output internally and exclude newline/carriage-return paths before emitting the retained line protocol. The actual RED showed that the old producer could turn a newline-containing name into a duplicate existing safe sibling. Pipe-corrupt target records are also refused. Names with spaces, Unicode and literal backslashes remain supported.
- Existing terminal FD3, private Bash staging, stdout-path/cache, selector, asset/preset and manual-handoff functions remain. `r0013-preserved-functions.json` binds32 unchanged critical function/document blocks, including the earned R0014 Windows review guidance. The new PS final heading states manual action pending.

C08 is the discovery/selection owner. R0015 receives only eligible-known targets before initialization and owns C11/C12 artifact admission and staging. R0013 does not introduce a second artifact-ready predicate. R0016 receives the same eligible target record and owns the broader no-effect helper/entry qualification. C09/C10 Bash custody/admission remain preserved.

## Actual RED and corrections

| Reproduction | Observed result | Receipt |
| --- | --- | --- |
| Original discovery baseline | Bash2/37 healthy,35 failures; PS1/28 healthy,27 failures | `r0013-bash-red.json`, `r0013-powershell-red.stdout` |
| Identity-less addon review | Bash40/46, PS31/37;6 named failures each while supported fields/empty controls pass | `r0013-insufficient-bash-red.json`, `r0013-insufficient-ps-red.json` |
| Newline profile alias | Both producer families fail with one healthy empty-parser control | `r0013-newline-red.json` |
| PS singleton root-array unwrapping |2 failures,2 valid-object controls pass | `r0013-singleton-array-fixture-red.json` |
| Strict syntax / duplicate-key review | Bash57/64,7 failures; PS44/56,12 failures; real duplicate-key mixed caller reaches extra effects before repair | `r0013-strict-bash-red.json`, `r0013-strict-powershell-red-retry.json` |

Independent reviewer receipts under `r0013-review/` separately demonstrated that duplicate addons could hide legacy and reach real contained entry actions. The repair addresses those causes. The first strict PS launch failed before process startup because the workspace was full; it is infrastructure failure, not product evidence. Root restored capacity by removing its verified canceled-clone temporary pack; `capacity-recovery.json` records that action. The retry above is the actual RED.

## Observed verification

| Verification | Result | Scope / receipt |
| --- | --- | --- |
| Final Bash discovery |76/76 PASS, process exit0 | actual parser/builders/contained entry, `r0013-bash-final3.json` |
| Final PS discovery |68/68 PASS, process exit0 | Linux PS7.6.6 supplemental, `r0013-powershell-final3.json` |
| Bash semantic mutants |12/12 detected plus exact healthy ledger, exit0 | `r0013-bash-discovery-mutants-final3.json` |
| PS semantic mutants |11/11 detected plus exact healthy ledger, exit0 | `r0013-powershell-discovery-mutants-final3.json` |
| Final PS preservation components |18/18 PASS, exit0; exact-file parser/ASCII/selector/object identity/callers | `r0013-preserved-powershell-components3.txt`, Linux supplemental only |
| Retained Bash whole pipe/PTY |23/23 PASS on earlier candidate before strict parser increment and root interception hardening | `r0013-preserved-bash-entry.json` |
| Retained Bash helper |25/26; sole known wrong-owner-home premise failure retained, process exit1 | `r0013-preserved-bash-helper.json` |
| Syntax / Python AST | Bash syntax exit0; all changed Python files parse | worker command output, source freeze2 |

Every new semantic mutant must parse, fail its specifically named behavior assertions and retain three healthy controls: supported empty, supported new and complex valid JSON. Covered faults include catch/missing-to-absence, dropping builder knowledge, default-all unknown admission, both becoming safe-new, no-Python absence promotion, held-summary omission, structured-stream contamination, insufficient identities, newline aliasing, singleton-root unwrapping, duplicate keys, non-JSON constants, strict-validator bypass and trailing separators. The strict JSON controls also cover nested arrays/objects, numbers/literals, valid escapes, malformed numbers, missing separators, multiple roots and invalid escapes.

The new Bash fixture's no-Python mixed positive is an actual preview with an independent eligible Chromium target; it does not claim normal staging without Python, which remains an existing staging dependency.

## Changed-file custody

Worker implementation/fixtures: `install.sh`, `install.ps1`, `tests/install-discovery.py`, `tests/install-discovery.ps1`, `tests/install-discovery-mutations.py`, `tests/install-bash.py`, `tests/install-entry-bash.py`, `tests/install-entry-native.py`, `tests/install-entry.ps1`, `tests/install-mutations.py`. Worker documentation: `README.md`, `docs/state-contracts/R0013.md`.

Healthy retained Firefox fixtures now explicitly create addons[]. Bash fixture portability uses SALAH_TEST_BASH (default /bin/bash), physical temporary roots and platform-specific profile locations. Native Windows entry accepts INSTALL_TEST_PS7 and its adjacent Modules. Actual native receipt acquisition remains separate.

Root subsequently and explicitly owns the case-filter change in install-bash.py, stronger nonce/readiness/snapshot instrumentation and case filter in install-entry-bash.py, and named adverse/paired-control repair in install-mutations.py. Those root changes are reflected in the observed freeze2 hashes, but the final joined fixture/native qualification is root's next step. Earlier worker runs must not be presented as qualification of later fixture bytes. Root confirmed attribution and is requalifying an immutable instrumented snapshot.

## Remaining gates and limits

- Actual Apple /bin/bash3.2 detector and whole-entry evidence remains required. No actual owner Apple deferral was recovered from the complete live issue records.
- Actual native Windows PowerShell5.1 and supported Windows PowerShell7.6.6 evidence remains required for the changed parser/builders/entry. Linux PS7 evidence is supplemental only.
- The unchanged wrong-owner-home case assumes /tmp is foreign-owned; the local premise is false. Its failure remains recorded. R0015 owns the isolated native UID proof without permission/ancestry confounders.
- README Bash reviewed-source placeholder must be replaced by the exact candidate source commit during root packaging. Root will commit installer/tests first and then pin that source in a documentation follow-up. Earned R0014 Windows guidance remains unchanged. Root also owns merging the separate accepted weather-only README delta from main.
- Native/current source/test receipt binding, independent review, whole original denominator, campaign predecessors, exact approval, integration and served-byte delivery remain open. No publication, merge or issue closure is claimed by this worker.

Installer and discovery writes are frozen; custody returned to root. No outstanding worker process remains.
