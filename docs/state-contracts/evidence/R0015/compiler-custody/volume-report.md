# R0015 NTFS-only volume admission: bounded replay

## Result and evidence boundary

**PASS for the supplemental policy correction and its causal mutation controls. Native Windows qualification remains BLOCKED pending actual PowerShell 5.1 and PowerShell 7.6.6 receipts.** The original failing evidence is preserved unchanged. This packet changes only scratch fixtures and evidence; installer ownership stays with the root.

Microsoft documents that the 64-bit identifier returned by `BY_HANDLE_FILE_INFORMATION` is not guaranteed unique on ReFS, whose identifiers are 128 bits. This supports restricting the existing 64-bit identity design to NTFS. It does not establish an NTFS flaw, an observed ReFS collision, or an exploit. Primary reference: [Microsoft Learn, BY_HANDLE_FILE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information), `nFileIndexLow` and `Remarks`.

## Exact inputs

| Input | SHA256 |
|---|---|
| Original source, `source-358bf.ps1` | `358bf1da1bf385b74e0ce2019e81d8018797fedecbe0ece186027872213602e1` |
| Corrected source, `source-7e695.ps1` | `7e6950359b6f28e165e02793e56cb1842db092403fd09abea9f0f9c595ba5114` |
| Original fixture, `install-volume-policy.initial.ps1` | `22e9391bc411fd6b304887e5d7d22db5bb567d3ab3fa561653279f855cda8062` |
| Final fixture, `install-volume-policy.ps1` | `dc671aa0365d6fb318fbf838472a8c8512931ddf371e2c3527433bcb22f41e7d` |
| Mutant driver, `replay-mutants.py` | `b81ad6f98a5eca19c2e52594215d6fbc5dbe1c262e1b94939fb9a7e5faba60ba` |

The original fixture was recovered byte-for-byte and its hash matches the original RED receipt. The final fixture adds only input-source/test stability admission; `fixture-custody-only.patch` records that derivative. `ntfs-only-source.patch` records root's two-site change, including each filesystem-name buffer and comparison. The production file still matches the corrected snapshot after all executions.

## Actual source boundary

In corrected source, `New-StagingCompilerContext` requests a 32-character filesystem name and checks ordinal-ignore-case NTFS at lines 142–145 before its first directory lease or private allocation. `StageNative.RequireLocalAclVolume` does the same at lines 346–349 after its existing local-drive/API/persistent-ACL gates. No identity algorithm, permission mask, lease-sharing rule, discovery, artifact-admission, or selector decision is changed by this correction.

The fixture extracts the actual C# literal through the installer AST and retains both the literal and the derived source in `control/`. Only the `GetVolumeInformationW` declaration becomes a response adapter; the normalized C# policy body must remain exactly equal to the extracted policy. On native Windows the adapter performs a real native volume query before supplying the reported response. The actual compiler-context function is imported from the AST; its native API type is adapted, and the first directory lease throws a distinct stop marker. That marker proves the volume gate was passed while keeping all counterfactual calls before directory creation.

Local Linux additionally adapts only native SID, drive and Windows-path reads. Those replacements are individually declared in each receipt. They are not native Windows evidence. On native Windows the fixture first runs **unadapted actual `Initialize-Staging` on actual NTFS**, records private scratch/retained identities, and invokes actual cleanup. This healthy native row cannot be credited locally.

## RED, GREEN and causal controls

| Execution | Actual observation | Receipt SHA256 |
|---|---|---|
| Original source / original fixture | Both boundaries accept ReFS, empty name and OtherFS; six useful healthy/refusal controls pass | `ab4efde203d524c3ec69a73f8fed93319723311d1c7317a49d5e3604a529972f` |
| Original source / final fixture | Same six failures and six useful controls reproduced | `8f5960b45b905e834c9ab0b9a19be913933bf122646783c06cb8c7da7d823d8c` |
| Corrected source / final fixture | All 12 policy rows pass; native positive explicitly BLOCKED | `0e7854be5ba717b9b579bb8aaae02edb5a236a14a2f68245e8d0b66041b85706` |
| Two single-guard mutants | Each removes one NTFS comparison only; exactly that boundary's three unsupported-name cases fail; six NTFS/no-ACL/query-failure controls pass in each run | `b52417bfa34a0ddadd19fdb20fffcfcab2abc423592e8bedfe72d8a50317fb75` |

The C# mutant is `3e625e7a04f33485039409a8a3291087d75e6f636aca2ae8a5f2146fd498465b`; the compiler-context mutant is `508ffaa43653db5d3c6d1bedc4da7480ac935635b12265be6dfd37ca5fe820ac`. Each actual source parses through the fixture. Both mutants request the filesystem buffer and make one API call per case. The opposite boundary continues to refuse unsupported responses, tying each failure to its own missing comparison. No malformed mutant, blanket refusal, compilation failure or native skip earns a mutant hit.

## Native collector contract

Run each native shell with:

```text
-NoLogo -NoProfile -NonInteractive -File tests/install-volume-policy.ps1 -SourceFile <exact install.ps1> -OutputRoot <owned disposable fixture parent>
```

Use a **180-second process cap** including host startup. The fixture starts no subprocesses and contains no wait loops; local complete execution took about 1.2 seconds. The cap is an acquisition allowance, not a measured Windows duration. Preserve stdout/stderr and the fresh `r0015-volume-policy-<GUID>` subtree beneath `OutputRoot`. Stdout and `<fixture>/results.json` contain the same structured result. Expected native success is exit 0, `nativeWindows: true`, the supplied source/test hashes unchanged, successful actual NTFS positive, and all **13 rows** `pass: true`. A non-Windows native row is `pass: null`/`BLOCKED_NATIVE_HOST`; a local top-level policy PASS never substitutes for that native row.

Optional native mutation replay uses `replay-mutants.py --source <source> --fixture <fixture> --pwsh <native executable> --output-root <fresh nonexistent path> --timeout-seconds 180` with a 390-second parent cap. It preserves both derived source files and raw child receipts. The expected child exit 1 earns credit only when exactly the named three unsupported-name assertions fail and all six paired useful controls pass. The driver does not edit its supplied source or fixture.

## Remaining scope

Actual Windows 5.1/7 native NTFS positives and native response-boundary observations remain required. No unsupported filesystem is exercised by these controlled responses. Compiler scratch custody, first-call output confinement, and the separate prior PS7 transaction acquisition failure remain their own evidence obligations. This report supplies bounded test evidence only and does not grant acceptance, publication or closure authority.
