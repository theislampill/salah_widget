# PS7 normal-control compiler ancestry diagnosis

**FINAL diagnosis: the observed PS7 failure is an owned-route location error against the unchanged compiler ancestry contract.** The actual entries refuse the excluded owner of `D:\` before compiler scratch creation. Move the new exclusive qualification root below the actual ambient `C:` user profile, preserve existing ancestor ACLs, and shorten the route basename before retrying: the otherwise identical layout produces a separate calculated Framework output-path risk above 260 characters.

This is read-only source/artifact diagnosis, not native requalification. I authored the original core route and do not claim independent approval of that original implementation. Root independently reviewed and published it. I executed no PowerShell, installer, or Windows API during this diagnosis; PS51's active run was not touched.

## Original artifact and actual failure

Run: **43126071549**, source commit `0607afd5885ccb6bba0db8f95173f63f65824d22`.

| Evidence | Bytes | SHA256 |
| --- | ---: | --- |
| Original PS766 ZIP | 8,174,419 | `af5bce9714672dc9586882220c434d11ac7193362364e7406b7f0982ee9555d5` |
| Inner `installer-core-evidence.tar.gz` | 8,626,353 | `e4cf8bd17c0a716d1840750bb6b4ee2a1a2a30f9e09d1ed8471ddf1ae41de405` |
| Actual `control/install.ps1` | 110,645 | `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4` |

The ZIP contains that one TAR. I read 22 selected regular records directly from the TAR and verified their complete bytes against root's extracted files. Selected records include the source, maintained entry and core2 receiver, route plan/result, both outer process receipts, the native companion receipt, both entries' original stdout/stderr/effects/readiness, before/after ancestor ACL records, and the raw core results. The TAR contains 5,908 members. This is selected-record receiving, not a fresh claim that every native core predicate has been independently revalidated.

The raw core results contain **75 rows marked PASS**; the outer core process exits 0. The companion's outer process exits 1 with `BASELINE_NORMAL_FAILED`. Its one paired baseline record contains actual `positive` and `no-open` entries, both with integer exit 1, readiness established, unchanged subject snapshots, and only the expected selection-prompt event. The eight mutation companions did not run after the baseline failure. These observations remain separate: 75 acquired core rows do not supply normal/mutation survival credit.

Both original entry stderr files identify `install.ps1:197` and the same compiler-ancestor refusal. Their SHA256 is `7522c4e62b5688ec9f461f309a9a597e27d0f4a0010ba25d9b76636fc4f5e6b6`. The source selected two eligible targets before entering staging, so this is not an entry bootstrap or browser-discovery refusal.

## Why the D: ancestor is determinative

`New-StagingCompilerContext` obtains the native temporary path, enumerates its ancestors beginning with the drive root, and requires `TrustedAncestor` for each leased directory. `Read-CompilerPathFacts` initializes that field from owner membership in the current token SID, SYSTEM `S-1-5-18`, Administrators `S-1-5-32-544`, and the resolved TrustedInstaller SID, then applies the unchanged ACE restrictions.

Both entries' `parent-acl-after.json` record `D:\` owner **`S-1-5-20`**, outside that set. The root's SDDL equals its respective before-setup SDDL, so fixture parent protection did not alter the drive ACL. The drive is the first ancestor tested. A newly protected grandchild below it cannot make that first owner membership true. This establishes the source-linked reason for the observed line-197 refusal without modifying any production guard.

The after-ACL file hashes are:

- Positive: `19a6015c4411a6f3115d57ed25e307b06f362a376b1791b0b9b162db6d79a145`.
- NoOpen: `41d9296c199263338c6b4ee6165315802e385f1e6290f8879dae6f86f7551096`.

The original selected case records are under root's extracted path:

`/tmp/r0016-third-20261111/work/root-windows-core-native/ps766/installer-evidence/companion/state/temp/companion-output/p-37e2731f69db4c44/c/0/t/salah native entry-u8pt5u5m/`

Own selected copies and their complete archive-member bindings are retained in `selected-records/` and `receiving.json` beside this report.

## R0015 comparison and its limits

I read the original R0015 native6 source from Git commit `d96f87825f02077da7f6afe742d30aecfd1fc005`. Its SHA256 is `ab2d8470367a539a9c6605717a11edc1bf019681d7ec5a65ef0a54e83a67f88e`. These current functions compare **byte-identical**, including masks, principal rules, owner admission, and refusal behavior:

| Function | Exact function-text SHA256 |
| --- | --- |
| `Read-CompilerPathFacts` | `c7c0d8a0bb3825713142c9ad4451b44efb74367de5b66b5924402ec24af8b88c` |
| `Open-CompilerDirectoryLease` | `73026c57fdf1bfce5dc6af067c23dffe289aec66a6d26ff5c58bf7b9ea9246e3` |
| `New-StagingCompilerContext` | `3fed5a1da6e7fb6874684a828610fddd0b797be648669e842561e51c1d3d1a11` |

The retained native6 summary for run **43028305607** records the selected complete-file normal/NoOpen qualification as passed. The summary SHA256 is `0ef50d4e6eb45459342afa73af6118d2ec2efd5db1bd0f90fcac9b78ef91b478`; its independent review projection is `246d5c3e66f3ca72bf0f052fe226a36a2498024be0360a0724f97f3580e7e73d`. The underlying original Windows ZIP is identified there as artifact `13861137478`, SHA256 `76815f2a6a27ecaf3db65f64acc0deb844bbe391230255f2607e6c3192ce505e`, inner TAR `98484f9cb545402e272ec29b04315e15e9296bdff53b91e5544c149b6842a37d`.

That original ZIP is not present in the current locally available evidence, and the compact summary does not contain the complete-file fixture root. **I do not assert an observed original R0015 C: fixture path.** It does identify the successful original PS7 executable on `D:\a\_temp\installer-pwsh7\pwsh.exe`; an executable location on D: alone is not the current compiler-temp ancestry defect. No runtime relocation is required by this diagnosis.

## Countermeasure and concrete follow-on path bound

The route should resolve the actual ambient `USERPROFILE` before setting owned child environments, require the intended C: profile location, create only a fresh exclusive route child below it, and keep the core/companion TEMP and TMP paths within that child. The existing per-case setup continues to protect only newly owned fixture parents. Existing profile/drive ancestor ACLs and source/test admission rules remain unchanged. Archive discovery and output must select the same new parent; otherwise preservation would look in the previous D: parent.

The path change alone adds **10 characters** to the observed layout (`D:\a\_temp` to `C:\Users\runneradmin`). The exact source's PS5.1 compiler branch creates `compiler.stdout.bin` and `compiler.stderr.bin` inside its generated compiler root. The following are arithmetic projections from retained actual PS7 fixture names, using the original fixed-width route and compiler nonces; the PS51 projection changes only the host case label:

| Layout projected under C: profile | Compiler root length | Each compiler diagnostic path length |
| --- | ---: | ---: |
| PS7 positive naming | 242 | 262 |
| PS51 positive naming | 243 | 263 |
| PS7 NoOpen naming | 241 | 261 |
| PS51 NoOpen naming | 242 | 262 |

This is a prospective path-length boundary, **not** a native result and **not** the cause of the original PS7 failure. The current source uses those explicit diagnostic filenames in the Framework branch, and R0015 preserves prior long bare-path failures; the C: retry should not introduce this avoidable boundary. A 26-character reduction in the fresh route basename reduces the PS51 diagnostic projections to **237/236**, without changing any original subject, payload, mutation, or product assertion. Root has chosen that narrow follow-up for separate exact review.

## Evidence files and disposition

- `receiving.json`: 14,991 bytes, SHA256 `deb204d9571bf2a3c8b4482e89a24849fb3f2724d3b73844337393d4734c9b8a`.
- `diagnosis.json`: 4,301 bytes, SHA256 `dd54899b2af52162d6ef61844e6b3afb1a02175e0cfe228d5e103ab4c61a6595`.

The observed root cause is confirmed in the bounded source/artifact scope. Current normal and mutation-companion acceptance remains failed/unacquired. Corrected native success, current C: ancestor admission, and any later product qualification require new actual observations. The original PS51 run remains untouched.
