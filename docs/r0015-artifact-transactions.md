# Windows installer artifact transactions

This is the source-linked contract for the R0015 Windows transaction addition in
[`install.ps1`](../install.ps1). It implements the
[November #21 amendment](https://github.com/theislampill/salah_widget/issues/21#issuecomment-6700332793).
It does not certify browser installation, upstream authenticity, or the still
separate original R0015 Bash/host obligations.

## Manual files and lifetime

After an eligible target is selected, a cold Windows process first establishes
a private compiler workspace. The actual staging attempt then has separate
scratch and retained roots:

| Root | Purpose | Lifetime |
| --- | --- | --- |
| `native temporary directory\SalahWidgetCompiler-<random id>` | Compiler input and output, after physical-parent, identity and ACL admission | Successful compilation removes only this verified private workspace. A compiler failure or failed cleanup proof retains it and reports its actual location; it is never an admitted download or manual bundle. |
| `%TEMP%\SalahWidgetAttempt-<random attempt id>` | Download and rewrite candidates that have no ready status | The wizard attempts to remove only its own verified scratch root in `finally`. If custody or descendant checks fail, it retains the material and reports the skipped cleanup. |
| `%USERPROFILE%\SalahWidgetBundle-<random attempt id>` | Admitted ZIP/XPI downloads, preset JSON, and unpacked extension candidates | Retained for manual browser operations. The wizard never deletes an earlier bundle. |

Keep an unpacked extension directory for as long as a browser uses it through
**Load unpacked**. Pressing Enter only acknowledges the manual step; it does not
show that installation succeeded or that the browser released an older directory.
After verifying a successful import/install, a user may manually remove an
unneeded preset or XPI. A failed extraction or publication can also leave partial
material inside the new private retained root. Partial material is not offered as
ready output and is not adopted by a later invocation.

Each invocation starts fresh. Same-attempt reuse applies only to the exact
admitted asset source and bytes. Old shared caches and retained bundles are not a
new invocation's download cache.

## Ownership boundary

`Initialize-StagingNative` and the narrow native wrappers are guarded before
assembly loading, native identity acquisition or path probing. Production
staging requires Windows and a local NTFS volume with persistent ACLs.
An unsupported host or unprovable boundary produces an error; it does not fall
back to a shared directory.

The first native interop declarations use in-memory reflection emit, before any
CodeDOM compilation. `New-StagingCompilerContext` checks the reported filesystem,
physical ancestry, owner and permissions, takes no-delete-sharing directory
leases, and exclusively creates its protected current-user workspace. Only then
does `Initialize-StagingNative` set both process `TEMP` and `TMP` to that workspace
and call the guarded `Invoke-StagingCompiler` helper. Both variables are restored
in `finally`, including their originally absent state.

On Windows PowerShell 5.1, the helper invokes the host Framework `csc.exe` through
`Diagnostics.Process`, with its working directory, child `TEMP`/`TMP`, exclusive
source file and raw diagnostic files confined to that held workspace. It checks
the exact UTF-8 source bytes through a held read handle. A successful terminal
compiler exit and complete diagnostic capture precede DLL admission: the output
must be a regular single-link file with the expected owner and restricted write
access, at most16 MiB, and its identity is checked again while a handle denies
concurrent writes and deletion. The admitted bytes are loaded into memory and
must contain the required staging type. On supported PowerShell 7, the same
helper retains the actual `Add-Type -TypeDefinition` path in the admitted context.

The compiler context captures the token's default owner, restricted to the user
or Administrators. Compiler output admission and descendant cleanup may accept
that captured owner as well as the user, while still requiring the full foreign
write-access predicate, current identity and non-reparse/single-link checks.
Ordinary staging-artifact ownership rules are unchanged. Cleanup retains the
ancestor leases through deletion; any failed custody proof retains the workspace.
A failed compiler invocation also keeps its owned workspace for diagnosis without
granting artifact readiness.

Both the compiler boundary and `StageNative.RequireLocalAclVolume` require a
successful filesystem-name query that reports NTFS. The existing file-identity
scheme uses `BY_HANDLE_FILE_INFORMATION`; Microsoft documents that its 64-bit
identifier is not guaranteed unique on ReFS. Other filesystem names and unknown
names are therefore refused rather than treated as qualified NTFS identities.
See [Microsoft's structure documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information).

`Get-TrustedStagingParent` requires a self-owned immediate parent with no
untrusted write grant and checks every physical ancestor without accepting
reparse points. Earlier ancestors may be owned by the current user, System,
Administrators, or the locally resolved TrustedInstaller servicing principal.
They must not grant a foreign principal replacement, attribute, ACL or ownership
authority. Harmless explicit create-file/create-directory rights on an ancestor
are allowed; current-user ownership is not required everywhere. This ancestry
boundary also protects the retained path after process-held leases are released.
Directory leases remain open during the attempt.
`New-PrivateStagingDirectory` and `New-PrivateStagingFile` use
exclusive Win32 creation with a protected current-user security descriptor
supplied **at creation**. Existing paths are not adopted, reset or recursively
removed. Native readback records volume/file identity, owner and access control.

`Assert-OwnedStagingPath` checks the current attempt's root identity and each
existing component before artifact operations. Regular files must be private,
non-reparse disk files with a single link. These checks do not isolate an
administrator or another process already acting as the same user.

The publication path uses a non-overwriting move after a private retained-volume
copy and byte readback. This is an exclusive publication operation, not a claim
of crash-consistent transactions or universal filesystem atomicity.

## One admission contract

`New-ArtifactRecord` creates a small invocation-local record containing attempt
identity, source identity, candidate path, expected size/digest where supplied,
actual validation and byte identity, state and failure reason. The normal path is:

`unresolved -> downloading -> downloaded-unvalidated -> validated -> published -> handed-off -> retained`

Failures remain failed/partial candidates. A filename, a successful download
return, or an unchecked state label does not grant readiness.

`Get-AdmittedArtifact(Path, Kind)` is the single readiness predicate used by the
public helpers and actual install/import handoffs. It requires the matching
current-attempt record, a published/handoff state, current native identity and
unchanged bytes. For an unpacked bundle, it reads back the recorded output tree
and member identities/digests. Diagnostics use host/warning output; public
artifact helpers return one admitted string path or null/throw.

| Public operation | Enforced behavior |
| --- | --- |
| `Download-Asset` | Download into a distinct scratch candidate; verify expected size and declared SHA256 when supplied; validate the supported archive and manifest; publish an independently read-back retained file. |
| Same source reuse | `Get-AdmittedArtifact` must still accept the exact bytes and file identity. Changed or unverified material is reacquired or refused. |
| `Expand-ChromiumAsset` | Require an admitted archive; create a new retained candidate; validate every member before member output; extract exclusively; read back the complete output and return the manifest directory. |
| `Download-Preset` | Parse supported strict UTF-8 JSON, require the actual canonical widget and a singular iframe, update only its configured field, revalidate, then publish. |
| `Show-ImportInstructions` | Recheck admission before offering or copying a path. Missing or rejected presets produce truthful recovery instructions without a selectable-file claim. |
| `Install-TablissNG` | Recheck the admitted archive or unpacked result before the manual browser handoff. Browser completion remains manual. |
| `Clear-OwnedScratch` | Verify current scratch custody and all descendants; close only the scratch root's own lease before deletion, keep ancestor and retained-root leases until that deletion completes, then dispose the remaining leases; retain all manual bundles. |

R0013 continues to own `Get-DiscoveryEligibility` and the unknown-held /
legacy-refused gates before initialization and dispatch. R0014 retains release
selector precedence and selected-object identity. R0015 adds no discovery
scanner or second eligibility predicate.

## Supported archive checks

`StageNative.ReadZipCrcs` and `Test-ExtensionArchive` support single-disk,
non-ZIP64 ZIP/XPI archives using stored or deflated members. They check the
central/local records, matching member names, non-overlapping layout, declared
lengths, descriptors and each member's CRC. Archive bytes are never converted
through text encoding.

Before creating the first extracted member, the entire archive must pass path,
attribute, size, content and manifest checks. Absolute/traversal paths, alternate
separators, ADS/colon names, Windows reserved names, trailing spaces/dots,
case aliases, duplicate destinations, file/directory collisions, links,
reparse attributes and special files are refused. Healthy Unicode names and
interior spaces remain supported.

The bounded format accepts at most 128 MiB of compressed archive bytes, 10,000
members, 128 MiB per member, and 512 MiB of total expanded data. The single
extension manifest is at most 1 MiB and must be strict JSON with the supported
extension fields. Unsupported archives receive no ready path.

These checks bind and validate the delivered bytes. CRC and SHA256 do not prove
publisher authenticity, extension signing, safety of extension behavior or
successful browser installation. A signed-looking asset filename remains a
selector hint.

## Preset schema and preservation

The supported canonical relationship is:

- `widget/orpul7IDXSSP.id = "orpul7IDXSSP"`
- `widget/orpul7IDXSSP.key = "widget/html"`
- `data/orpul7IDXSSP.input` contains the singular supported widget iframe.

Its source is the configured fragment of
`https://theislampill.github.io/salah_widget/`. `Test-StrictJson`, preserved from
R0013, rejects malformed grammar and ambiguous duplicate/case-colliding object
keys. Strict UTF-8 decoding rejects invalid bytes. Presets are bounded to 16 MiB.

`Get-PresetInputToken` identifies the canonical JSON string token after parsing.
`Convert-ConfiguredPreset` changes only the intended iframe source through the
XML attribute and JSON string serializer boundaries, with DTDs prohibited and
external resolvers disabled. It then reparses and checks the exact resulting
fragment. All JSON text outside that one string token is preserved. Unrelated
`local=1` text, optional values, large integer representations and timestamp
strings do not pass through a whole-document serializer. Existing title,
referrer, geolocation and 325-by-530 dimensions remain part of the iframe.

A missing/ambiguous widget, malformed input, failed fragment check or unsupported
shape yields no ready import path. Parse/shape/fragment success establishes a
staged preset, not guaranteed browser import. Importing replaces the current
TablissNG dashboard; the wizard retains that warning.

## Preview and evidence limits

`-DryRun` exits at the existing whole-entry preview boundary. Every effectful
staging/admission helper also guards direct calls. Preview loads no staging
native helper, creates no root, returns no warm-cache ready path, acquires no
download, extracts/rewrites nothing, opens/copies nothing and performs no cleanup
or lease disposal.

[`tests/install-powershell-transactions.ps1`](../tests/install-powershell-transactions.ps1)
executes the actual production transaction functions and install/import callers
with controlled external transport, clipboard, browser and prompt boundaries.
By default it uses the actual native filesystem APIs. Its explicit POSIX adapter
is only a supplemental functional control and is forbidden on Windows runs; it
does not qualify Windows ACLs or directory leases. The selector and discovery
fixtures have separately labeled artifact-admission adapters so their original
consumer claims do not masquerade as R0015 byte/custody evidence.

Native Windows PS5.1 and supported PS7 receipts, exact source/test hashes, failure
and named mutation controls, and final-tree review must be read together before
acceptance. Original R0015 Bash, foreign-HOME, Apple-host and public-document
residuals remain independently tracked by #21. This document alone grants no
acceptance, merge or issue-closure authority.
