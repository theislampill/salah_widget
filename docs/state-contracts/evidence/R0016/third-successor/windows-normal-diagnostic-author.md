# Focused correction — normal-profile diagnostic associations

**Disposition: private correction prepared for focused independent rereview. No native acquisition or qualification is claimed.** The original `717f8c5c…` proposal and the independent review remain unchanged. Only the demonstrated nested association checks and the explicitly authorized current outer-module binding are corrected.

## Exact delta

The corrected runner is `proposed/tools/qualification/installer_preview_windows_normal_profile_diagnostic.py`, **27,093 bytes**, SHA256 **`0dbaa611c5c178983f79f24cdf25b1a5e33dee66f13201025d571baa5e42cb77`**. `receiver-correction.diff` is the complete textual delta from the original 25,262-byte runner, SHA256 `717f8c5c1d2470de665eceda0d5edfe1dc4a5a909eedb543091361806c64bf92`.

Only `receive_mode` changes among existing functions. One new function, `bind_nested_evidence`, is added. The other source change is the literal outer-module size/hash pin. Every other function remains AST-identical; the three harness variants and all inherited strict product comparators remain byte-identical to the original proposal.

The new binding checks use evidence already acquired:

1. Both nested stdout/stderr facts must match the exact expected owned raw files, including their size and SHA256, for both product and warmup.
2. The receipt's positive integer PID and 32-hex nonce determine its ready token. Its environment nonce must agree. The product observation nonce and direct-launch environment must agree with the same receipt.
3. Ready and ACK paths must be distinct and owned by that case. Their declared facts must match those exact environment paths and actual bytes. The bytes must decode to the expected PID/nonce token using the existing UTF-8/BOM-compatible convention. Re-reading also checks bytes/hash against the verified fact.
4. All four product/warmup nonces within a mode must be distinct. PID reuse remains permitted; no never-reused-PID rule was introduced.
5. Product `profileWindow.fullReady` must equal the independently loaded product-ready inventory, matching the existing warmup check.

There are no new native telemetry requirements, cache exclusions, effect suppression, state normalizations, acquisition variants, or disposition changes. Complete original FAIL/exit1 results remain FAIL inside `DIAGNOSTIC_ONLY`; `qualificationAccepted` remains false.

## Current outer-module binding

Root supplied published base **a4c617ebeedfb507c0cb7a472683cce47ad62522**, tree **7f7aca595593db5014dd0932476c35a85eb8ba0c**. The supplied current outer module is **45,698 bytes**, SHA256 **`652848809fc581452e4bf48e2895786cd3c780e60e0a2c3091e2969d7b856616`**. Its exact copy, the diagnostic literal pin, `input-manifest.json`, and `source-map.json` now agree. The historical outer file was not written into the repository.

Independent structural comparison found only the unused `validate_report` function and `INPUTS` constant changed relative to historical `d81c0b49…`. Every other function/class and constant is AST-identical, covering the generic builders/readers used by the diagnostic and their transitive helpers. `INPUTS` retains the same role keys and updates only the installer and product-support facts to the already declared prospective identities. The current outer input facts agree with the diagnostic's manifest. See `outer-binding-verification.json`.

Installer `07671cb9…`, fixture `a453230b…`, product support `70a6ce61…`, immutable common/source-free files, and all three derived harness hashes are unchanged.

## Exact reviewer witnesses: red then green

`test_receiver_associations.py` reads the hash-bound original `independent_checks.py`. It reuses the reviewer's exact inert fixture constructor and four original mutation bodies in fresh owned replay folders. Each JSON mutation refreshes the report/envelope/outer capture facts through the original `refresh()` function, so a stale outer hash does not mask the variable under test. The original process/network-denying audit hook is retained. These are synthetic data, not native observations.

| Original reviewer counterexample | Repin-only receiver, before repair | Corrected receiver |
|---|---|---|
| Missing product stdout raw, retained fact | Accepted | Refused: missing expected file |
| Changed warmup stderr raw, retained zero-byte fact | Accepted | Refused: file size/hash differs |
| Product receipt nonce detached from observation/token | Accepted | Refused: nested nonce differs |
| Product receipt fullReady null, valid independent inventory | Accepted | Refused: product full-ready receipt differs |

Seven additional mutations exercise the remaining expressly requested binding edges: detached PID, detached environment nonce, detached observation nonce, ready bytes with refreshed valid facts, ACK bytes with refreshed valid facts, ready fact redirected to ACK, and a warmup that reuses the product nonce while retaining internally consistent tokens/files. All seven were accepted before the repair and refused afterward.

The complete original FAIL/exit1 packet remains successfully received both before and after every adverse series; its original booleans/errors remain unchanged and qualification remains false. Red exits **1** with **0/4** original witnesses refused. Green exits **0** with **4/4** original witnesses and **11/11** total association mutations refused. Exact outputs and source identities are retained in `red-receiver-results.json`, `green-receiver-results.json`, and `terminal-evidence.json`.

The seven original author inert tests also pass after the correction. They retain exact input-pin, fixed six-entry scope, unchanged derivation/comparator, full-delta, FAIL semantics, and incomplete-terminal checks. The non-Windows CLI gate still rejects before any child launch. No PowerShell process, installer, native probe, workflow, network operation, shared source edit, or Git operation was performed.

## Rereview packet

`reviewer-originals/` preserves the complete review and exact probes/results. `original/` preserves the original runner and the repin-only stage used for red. `replays/` preserves the synthetic replay inputs. `SHA256SUMS` binds every regular deliverable; `integrity-verification.json` confirms the original frozen proposal still matches its original manifest and the unchanged derived/inherited files retain their exact bytes.

The next authority step is root's focused independent rereview. Native compatibility, no-gather behavior, and whether the 20-second warmup changes the later cache outcome remain untested hypotheses.
