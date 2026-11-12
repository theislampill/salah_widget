# Focused review: native Apple Bash diagnostic assertion

## Finding

The proposed change is a defensible correction of one false assertion. It replaces only the expected stderr substring `here-document` with `cannot create temp file for here document:`. The original and candidate ASTs are identical after normalizing that single string constant. All other rejection conditions remain unchanged. No installer source changes are involved.

The retained native helper observations already show each single-site revert failing for the intended reason. The first raw diagnostic reports source line 114 and the second line 117. Both say `cannot create temp file for here document: Operation not permitted`; both have exit 1, no timeout, empty stdout, and equal full before/after subject snapshots. The old hyphenated string does not appear in either error. The positive `/tmp` and physical `/private/tmp` helper cases pass the exact existing admission predicate. The real write-denial control and source-custody result are also recorded as passing.

## Exact bindings

| Input | Bytes | SHA-256 |
|---|---:|---|
| Archived ZIP | 1443968 | `4d3b1de17cba74604d6160062b329c571daf8b5e8ae36069f59eaf8d0c63a844` |
| Combined installer | 46460 | `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f` |
| Original helper test | 7604 | `cdf573290a502eb7681d78c5196ca9c2fbdc700fc8e17654870fd15e4fef88a8` |
| Proposed helper test | 7633 | `eea155f5a6c6dd0a72b05c2614932e8a8c7d7b16ab9946ed4631cca6cc7dbc17` |

The source commit is `a4c617ebeedfb507c0cb7a472683cce47ad62522`, tree `7f7aca595593db5014dd0932476c35a85eb8ba0c`. Installer and original helper bytes were read from those immutable Git objects, compared with the collector and helper bindings, and checked against the author's original copy. The proposed test is the exact supplied candidate.

The reported native host is macOS 15.8.2 arm64, Apple `/bin/bash` 3.2.57, using `/usr/bin/sandbox-exec`. Host identities and binary hashes are preserved in `bindings.json` as receipt assertions. Run 43171927398 / artifact 13922960795 provenance was supplied by the parent; this bounded review verified the local artifact bytes and internal bindings, without making a live API request.

## Independent verification

The 1,443,968-byte ZIP contains one `installer-evidence.tar.gz`. Twenty-five relevant regular files were compared byte for byte with the existing extraction; no extraction or external execution was performed. Ten raw binary stdout/stderr files match their report hashes and decoded report strings. Each per-observation JSON matches its aggregate observation.

The helper subject scripts match the exact combined installer prefix and expected helper command. Each negative script restores exactly one of the two six-space B2 read sites. The sandbox policy bytes match the recorded hash and deny all file writes except data writes to `/dev/null`, and deny network access. Native command records use the expected sandbox and Apple shell.

The exact `admission_ok` function and exact mutation-acceptance expression were extracted through AST selection from both original and candidate source. They were evaluated inertly against the retained two native mutant observations and six independent corruptions per observation:

| Case for each mutant | Original predicate | Candidate predicate |
|---|---:|---:|
| Actual native observation | false | true |
| Empty diagnostic | false | false |
| Unrelated denial text | false | false |
| Exit zero | false | false |
| Missing exit (`None`) | false | false |
| Timeout | false | false |
| Changed subject tree | false | false |

All 14 checks match their expected result. The Python source compiles without executing its module. The independent selector identifies the `record` call by its exact single-site label; it does not reuse the author's initially incorrect selector.

## Evidence boundary

The original native helper result remains `[true, true, true, false, false, true]`. Its collector `status` and `qualification_status` remain `FAIL`. This report does not rewrite that artifact, convert the historical aggregate to a pass, or qualify the candidate test hash natively. It establishes the cause of these two assertion failures and the bounded behavior of the proposed predicate correction. Broader macOS receipt acceptance, installer/full-entry qualification, publication, and closure remain outside this review. No native installer, browser, CI, Git mutation, or shared source write was performed.

No additional assertion change is supported by this finding. Retained English wording is now tied to the observed required Apple Bash platform; a different native diagnostic would still require a fresh review rather than silently passing.
