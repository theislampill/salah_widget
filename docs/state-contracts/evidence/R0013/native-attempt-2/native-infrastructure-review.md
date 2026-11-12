# R0013 native infrastructure repair review

Reviewer: `/root/r0013_review`. **No new Critical, Important or Minor blocker was identified in the bounded infrastructure delta.** This is not a native product or whole-contract qualification.

## Exact inspected files

| File | SHA256 |
| --- | --- |
| `install.sh` | `609ecb0bb6924eccee5c311b77f0d513f0e78c3462c7fa5b15b1fd38694a5b22` |
| `install.ps1` | `a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4` |
| `.github/workflows/installer-native.yml` | `812739272e7119072939362f108e9ddd15972c50510e8f97ebb21265c60241e6` |
| `tools/qualification/installer_native.py` | `1cca4b4692e5836c405f19569826029a2156bad6cf0fcd229f5ba52596ebcfd9` |
| `tests/install-native-receipts.py` | `e56367e4295605c63bab6bb9a3ed50e2af96d06d018bfcadda39f0ef678d9103` |

The diff is against published commit `74558cdc596b815a6e24271d4253785a6f519b42`. Both installers retain the exact reviewed hashes. The only reviewed execution changes are the runner label, archive transport and copied-environment key lookup.

## Retained attempt and repair assessment

- Linux logs contain seven suite PASS/exit0 messages, followed by artifact rejection of an intentional LF filename. Full detailed Linux receipts were not received, so this review does not infer their content or count this as final Linux acceptance.
- The macOS annotation reports an unsupported runner configuration; no product execution is credited. Changing to `macos-15` preserves the collector's actual-Darwin and Apple `/bin/bash`3.2 gates. The new runner must still execute successfully.
- Windows preserves an exact-source `INCOMPLETE` result with an empty commands array and a traceback for `env["SystemRoot"]`. The uppercase `SYSTEMROOT` lookup addresses that copied-dictionary failure before fixtures. `IMAGEVERSION` fallback restores host image reporting; runtime version and PASS requirements are unchanged.
- Both workflow branches package the evidence directory with the same Python command and `dereference=False`, then upload the single archive basename. The packaging retains names and symlinks; `always()` allows incomplete evidence to survive without overriding earlier test failure.

## Independent bounded controls

Four controls passed using the exact workflow command and actual collector AST expressions:

1. The POSIX and Windows packaging bodies are identical.
2. A filename containing LF, CR, pipe and Unicode plus a relative symlink survived archive creation and round-trip extraction with identical data, name and symlink target. The link was stored rather than followed.
3. Missing evidence fails nonzero and creates no success archive.
4. The actual host/image expressions accept uppercase `SYSTEMROOT`, `INSTALL_TEST_PS7` and `IMAGEVERSION` dictionary keys without entering the collector or pretending to run on Windows.

The probe report is `native-infra-probe.json`; original attempt evidence and all inspected files are hashed in the JSON companion. No full suite was duplicated and no installer was executed for this infrastructure pass.

## Gates retained

The infrastructure commit/tree still needs immutable binding. Complete hosted Linux/Apple/Windows receipts, actual host/fixture/entry/mutation scope, final README source pins and rendered/public delivery remain pending. The full original12 + hierarchical residual7 + ES14 denominator, campaign ordering, exact owner approval, integration, certificate and completed closure gates remain unchanged.

No source, shared file, index, branch, governor or remote state was changed by this reviewer.
