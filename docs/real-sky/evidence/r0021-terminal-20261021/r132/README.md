# r132 — final relevant source regression

The serial canonical Node invocation returned **846 PASS, four existing TODOs, zero failures** (850 total). The exact 65 test-file inputs, hashes and command are retained in [RESULT.json](RESULT.json), with the complete [original log](canonical-node.txt). The TODOs retain their original R0003, R000D, R0024 and native browser-fixture scopes; they are not new passes.

The subsequent separate `native-head-handoff.cjs` invocation failed before any semantic control: r127 added fields and earlier tests to the reused host fixture, so the old whole-return extraction literal no longer matched. The original overall `FAILED` receipt and [extraction error](head-handoff.txt) remain unchanged.

The reviewed three-line test-adapter correction stops extraction before the first test and injects context at the still-unique short return prefix. All six semantic cases and assertions remain byte-identical. The corrected invocation returned [six passes](head-handoff-corrected.txt); frozen V1 and native entry order also pass, bound by [CORRECTION.json](CORRECTION.json). This file is outside the earlier canonical invocation, so no replay of those 850 tests is implied or necessary. Product runtime remains unchanged.

[Independent review](../reviews/candidate-tests-r132-fixture-review-r1.json) confirms the exact correction and retained failure. r127's affected host/build/asset tests and two identical canonical builds transfer through unchanged inputs. These are source/build checks, not callback, physical-pixel, deployment or merge qualification.
