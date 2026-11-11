# R0013 actual Apple run 2 diagnosis

Reviewer: `/root/r0013_review`. **Two fixture/oracle defects explain the reported Apple failures. No installer change is warranted by the inspected evidence.** Native Apple qualification remains failed until corrected fixtures execute on Apple again.

Run `42975927615` reports commit `eda44916bd107a64c687efd82de4e5c141be4fd1`, tree `5fb3ea5ab0c08521868a9bad7d7a0c3b992f4302`, unchanged Bash `609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22`. The received archive SHA256 is `2cc25081d17018de3a681b859acdfe80692061e485f89d903b27ccf285794c9d` and matches the receiving receipt. Host acquisition records actual macOS15.8.2 arm64, `/bin/bash`3.2.57, UID501/GID20, with every acquisition command exit0. This diagnosis uses Apple evidence, not Linux substitution.

## Important: ambient absolute browser executables escape fixture isolation

The actual installer `find_exe` checks `command -v "$c"` before `[ -x "$c" ]`. The entry harness intercepts `command -v` for bare browser names only; its separate `[` wrapper rejects `/Applications/*`. Therefore an absolute installed application succeeds at the first lookup and never reaches the mask.

The archived healthy full-entry menu is Chrome Default at1, ambient Edge without a profile at2, and fixture Firefox at3. The failed explicit `1,2` case correctly retains only a Chromium asset, then the test wrongly expects a Firefox XPI. Discovery fixtures without Chrome profiles receive two ambient held rows before Firefox. Their actual summaries remain conservative and accurate; expected fixture counts and indices are wrong.

**Smallest correction:** extend only the external `command -v` browser exclusion to `/Applications/*`, retaining the current executable-test interception. Do not replace the real detector or complete-file entry. Keep exact held/refused counts and useful-peer effects. Add an absolute-browser-lookup boundary control with a normal utility lookup control, and assert selected fixture identity/reason in explicit-selection cases.

A material false-green limitation also exists: `actual explicit unknown refuses before staging` passes, but fixed index2 refers to ambient Edge/no-profile instead of the intended malformed Firefox profile. That reported PASS does not qualify the intended identity claim.

### Exact failed cases caused by this fixture inventory

- Original entry: `pipe explicit indices` — `Firefox manual asset not retained`.
- Discovery: `actual all mixed selection keeps useful known peer`.
- Discovery: `actual explicit known target stays useful`.
- Discovery: `actual unknown only refuses before staging`.
- Discovery: `actual known both refuses before staging`.
- Discovery: `actual missing metadata is held`.
- Discovery: `actual no profile is held`.
- Discovery: `actual wrong shape preserves independent peer`.
- Discovery: `preview mixed keeps knowledge without effects`.
- Discovery: `preview unknown only has no success or effects`.
- Discovery: `no Python mixed preview keeps independent Chromium peer`.
- Discovery: `actual existing new target remains useful with unknown peer`.
- Discovery: `actual insufficient identity held with known peer`.
- Discovery: `actual duplicate keys cannot hide legacy from selection`.

The discovery mutation suite reports one failed row, `exact-source paired controls and assertions`. Its archived healthy baseline has14/21 reported passes and seven failures from the same inventory contamination. **No discovery mutants executed**; the driver correctly refused to credit them against an unhealthy baseline.

## Important: empty-array mutant oracle mistakes exit0 for survival

Both native family mutants remove exactly one empty-array guard from the actual detector. Archived source hashes match their receipts and both scripts parse. Each healthy peer produces `COUNT=1`, its exact no-profile fallback row and no stderr. Each mutant produces no stdout, no count/rows and the specific diagnostic `profiles[@]: unbound variable`, while its recorded exit is0.

The fixture at `empty_array_mutant` requires a nonzero exit as well as the diagnostic, so it calls this observed result loss a surviving mutant. The two failed cases are:

- `chromium native Bash3.2 empty-array nounset mutant`
- `firefox native Bash3.2 empty-array nounset mutant`

**Smallest correction:** preserve actual-native applicability, parse validity and the exact healthy peer; require the named `profiles[@]` diagnostic plus missing result/sentinel and failure of the exact expected output. Retain exit0 honestly as an observation. An unchanged-source control must not earn mutation credit. Do not accept a generic stderr failure or alter the installer trap based solely on an intentionally broken mutant.

## Receipt totals and next gate

| Suite | Reported pass/rows |
| --- | --- |
| `install-bash` | 26/26 |
| `install-entry-bash` | 23/24 |
| `install-discovery` | 63/76 |
| `install-detectors` | 10/12 |
| `install-discovery-mutations` | 0/1 |
| `install-original-mutations` | 8/8 |
| `install-builder` | 4/4 |

These totals describe the received receipts; the explicit-unknown alias limits one reported PASS as explained above. Preserve the raw run2 artifacts, make fixture-only corrections under assigned custody, and rerun the affected suites on actual Apple with exact source/test hashes. Unaffected observations remain available for scoped reuse. Windows diagnosis is parent-owned.

Only selected regular archive members were read, with no bulk extraction or symlink traversal. No source/test, branch, governor or remote state was changed.
