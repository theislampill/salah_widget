# FINAL — adverse PS5.1 full20 original received

## Finding

Run **43220592915**, attempt **1**, at `a89bbb3ddac639cc787ba08d030e8b2539057387` stopped at **c00 / github / owned-parent-acl-setup**. The ACL setup `powershell.exe -NoProfile -EncodedCommand …` invocation did not complete its `subprocess.run(..., capture_output=True, timeout=60)` operation within 60 seconds. Its captured stdout is empty; stderr is exactly **11 bytes, `#< CLIXML\r\n`**, with no XML error or progress body. The smallest demonstrated failure is an **ACL bootstrap acquisition/capture timeout**. No particular PowerShell operation or environmental cause is identified.

The outer Python harness exited **1** after **60.5 seconds**, with `timedOut=false`, `error=null`, observed terminal, and completed Job closure. Its independent deadline was **6,550 seconds**. The original receiver correctly rejected the nonzero outer terminal and retained `FULL_ENTRY_NOT_ADMITTED`. This is not an outer deadline failure.

**Zero installer launches and zero scenario passes are credited.** The sole result row is `BOOTSTRAP_BLOCKED`, explicitly recording `installerExecuted=false`. Nineteen later scenarios are unattempted. The source catches this ACL-bootstrap failure before copied case inputs, the host-only warmup, or actual product launch; the scenario loop then stops. No normal-preparation verdict follows from this run.

## Identity and original custody

Requested / actual model: `gpt-6-astra` / `gpt-6-astra` (self-report). Authoring-context reuse: **no**; other-current-reviewer visibility: **no**. Root continuity supplied: **G0027**. Authority: bounded technical evidence receiving only.

Base: `3b0e614114ef066de40db117d0e85c0031cf3e30`.

Head: `a89bbb3ddac639cc787ba08d030e8b2539057387`; tree: `efa716f4c8f1fe61c1a5a85b48bd97e813305d16`.

| Original | Independently verified value |
|---|---|
| Artifact | 13945063071; run/head association as supplied in the original metadata receipt |
| ZIP | 150,750 bytes; SHA-256 `e6c4a2a5c8b505a5166acaf17321ddbc6b7c56b758256a55cd1a740e3d1a7fdc` |
| ZIP member | Exactly `installer-full-entry-evidence.tar.gz`; CRC valid |
| TAR | 150,704 bytes; SHA-256 `3a3f1de0474631b0fc8a7734b33656b3071c74ad20f1aa28301bf1db5b5e43c6` |
| Membership | 76 unique safe directory/regular-file members; 36 regular files |
| Extracted bytes | Every regular file equals its original TAR bytes; complete extracted regular-file membership equals the TAR and supplied inventory |

All **fourteen copied roles** equal their immutable Git bytes and original-source facts. All **twelve launched input roles** match the immutable outer collector pins. Report instrument hashes, source/preset facts, original plan, raw stdout envelope, report file hash, and failed row join. The product is unchanged at 111,249 bytes / SHA-256 `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a`; the new composition harness is 72,501 bytes / SHA-256 `0b787803e3536393c4963eb9884c81eddc1a1198508877a600d7b51e4c64f85f`.

The exact ACL command embedded in the timeout error was safely parsed and Base64-decoded as data. Its UTF-16LE payload equals the `code` literal inside immutable `protect_parents`; the decoded UTF-8 content hash is `e8909e96483e18242cd7f74840739e6d461d9226d68d50d24805520e78464435`. No decoded code was executed.

## Failure evidence and limits

| Evidence | What it establishes |
|---|---|
| Nested timeout error and exact source join | The setup/capture operation hit its declared 60-second bound |
| Empty setup stdout; 11-byte setup stderr SHA-256 `3e2f777239e8875796a6a61feebd144090ede865f96db1df16a9bbcefd597d90` | Only a CLIXML preamble was captured; there is no diagnostic body to interpret |
| No `parent-acl-before.json` or `parent-acl-after.json` | No complete initial or final ACL snapshot was acquired |
| No direct launch, full input inventory, readiness, effect log, module fixture, fixture ZIP, or host-only-control evidence | No later case boundary or installer launch is evidenced |
| Only c00 exists under the case fixture | The remaining nineteen scenarios were not attempted |
| Original outer launch/process/raw-stream facts | Actual outer PID 7008, exit 1, no outer timeout, completed capture/Job lifecycle |

The inner ACL helper has **no retained PID, actual exit code, separate launch/terminal receipt, stage trace, or actual child-environment receipt**. Since its acquisition uses redirected pipes, this artifact cannot distinguish an unfinished PowerShell child from an unfinished pipe/capture condition. It also cannot locate the wait in startup, module loading, ACL reads, JSON serialization, ACL writes, or another operation. In particular, the evidence does not establish an ACL access denial, a failed `Set-Acl`, a completed ACL mutation, or an external ancestor ACL change.

The retained ACL-host analysis cache is 8,197 bytes / SHA-256 `bd600c22ee9b1e24ae59a7e5ec7b8973764ee8ad78182fcd0706a22efbc1fe67`. Its existence is retained as an observation; it supplies no before/after cache comparison or causal attribution.

The raw version capture and its zero-exit process receipt establish Windows PowerShell **5.1.20348.5773**, Desktop, Win32NT, 64-bit. Native executable bytes are not archived; their content hashes remain original Windows observations.

## Narrow comparison and corrective recommendation

The **4,948-byte `protect_parents` function is byte-identical** to the source used by successful native diagnostic **43216080799** (`12904a880c38b749db2d7c79ec1e7cebde2e04e2`); function SHA-256 is `7cecba4e024c2d79b16fb9560ab3dc703fcd3c1cd076e67a6b0317a27e04a766`. Its 60-second limit is unchanged. Captured PowerShell/Python path/size/hash facts and raw native version are the same.

The earlier warm20 positive/NoOpen cases retain complete before/after ACL journals. Independent receiving confirms the five owned ACL entries have the required owner-only protected FullControl rule and observed external ancestor SDDL remains unchanged. Their 840-byte stderr contains three completed module-preparation progress records, not errors. That earlier completion does not explain the present preamble-only timeout. Actual ACL child environments and live process state cannot be compared from the failed artifact.

**No concrete source or environment correction is established.** A single exact-candidate PS5.1-only re-execution with the same deadline is technically informative if preserved as a distinct attempt: recurrence establishes another timeout at this boundary; success establishes a different observed outcome. Neither outcome identifies the cause of attempt 1, and a later success must not overwrite this adverse receipt.

If this exact boundary recurs, the next minimal correction should add bounded ACL acquisition observability: actual command/environment and PID/terminal receipts, direct-file stdout/stderr capture, and flushed stage markers around initial ACL observation/serialization and owned ACL changes. Keep the ACL readback rules and case predicates intact. The present evidence gives no basis to weaken ACL requirements, increase the deadline, or modify normal JSON/no-gather preparation as a response to this failure.

## Review artifacts

`analysis.json` retains original adverse row/outer process, exact encoded command, source facts, raw stream facts, absence checks, prior ACL comparison, explicit limits, and zero-credit denominator. `archive-inventory.json` binds every original file. `acl-setup-decoded.ps1` is a read-only source-review copy. `checks.json` records 18,241 checks and the exact review boundary. `receive.py` reproduces this read-only receipt; `manifest.json` binds the review deliverables.

No shared repository or audit mutation, PowerShell/installer execution, publication, acceptance, or closure occurred.
