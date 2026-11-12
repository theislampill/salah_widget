# Independent Mac product candidate 1 review

Disposition: NEEDS_REVISION / bounded GAP. Do not qualify or publish this candidate for native product execution on this receiving recommendation.

Frozen candidate manifest: 0a9e7e9606bbad8b28042e4de95ce43496ea074d4a84979b85d039591934db9f. Product SHA256 4e23351028798372ffa32afc800f2b606ed02096e09907902dc2ab42eb42f766. Fixture SHA256 0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00. Every manifest entry independently matches.

## Blocking finding: newline-bearing command output changes path identity

The resolver rejects CR/LF only after ordinary command substitution has discarded trailing newline bytes. This affects xcode-select output, leaf readlink targets, and both pwd physical-path captures. A path can therefore be changed into a different executable/directory before the guard inspects it.

The exact helper was executed unmodified under local Bash with a bounded inert xcode-select/command lookup and actual filesystem/symlink operations in this reviewer’s scratch. Twenty-one independent cases produced eighteen expected outcomes and three adverse witnesses:

1. Selected developer output containing the valid directory plus two newline bytes was accepted despite the one-path contract.
2. An actual leaf symlink whose target ends in newline was resolved as its distinct clean sibling executable path. The returned executable was not the symlink target.
3. An actual physical parent directory ending in newline was resolved as its distinct clean sibling directory, and that sibling’s python3 was returned.

All three unexpectedly returned 0 with a usable path. This is an observed local shell/path identity error, not a native Apple result or an allegation of a successful global effect. The 40-link bound, cycles, out-of-root target, shim identity, missing capability, nonexecutable, ordinary observed symlink layout, normal/Linux/custom selection controls all behaved as expected.

Required bounded correction: preserve complete command output and exit status for all four path-producing callsites, remove only the command’s required single output delimiter, reject empty/remaining CR/LF before consuming the value, and repeat these witnesses. Do not hide the error by adjusting PATH, the existing Applications test spy, host policy, or native acceptance predicates.

## Scope checks already established

Removing only the declared resolver insertion and reverting only the parser invocation change exactly reproduces the original product source SHA256 87318d40dd4c91b1623ce7a5a9935f449850b8850e01e4b6cc2bc976b5f51bd7. The actual Python metadata parser body and all other product bytes are preserved. The fixture DENIALS literal is byte-identical. Existing test-registration tail is byte-identical after removing the one new Darwin-only literal-absence registration; no original case/negative is removed. Detailed fixture/oracle review continues against successor candidate 2, whose fixture is unchanged.

## Evidence

- source-receipt.json: frozen packet and all file bindings.
- scope-checks.json: product reconstruction and fixture preservation checks.
- helper.exact.sh: exact extracted reviewed function.
- probe_resolver.py: independent witness driver. Its first execution created the retained resolver-fixture; reruns require a new owned fixture root to preserve these original witnesses.
- resolver-receipt.json: all 21 case outcomes and three adverse original outputs.

This report makes no native Apple, whole-contract acceptance, merge, publication, or closure claim. No shared source files were edited by this lane.
