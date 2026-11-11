Report state: FINAL

# R0016 original POSIX evidence review

State history: created as PARTIAL, incrementally populated, finalized only after evidence and source review completed.

Scope: bounded read-only investigation of the original focused Linux and macOS diagnostic artifacts. No tests, source modifications, commits, pushes, or remote actions are authorized to this investigator. This report alone does not authorize mutation or closure.

## Inputs verified

- Checkout: `/tmp/r0016-successor-20261111/salah_widget`; root `AGENTS.md` read.
- Linux original ZIP: `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13867114561.zip`; SHA256 `b19980cfc580f6faf0da8c8684b84a95e7094041fb2720cd427fca5053bb5e66` (locally recomputed and matched).
- Darwin original ZIP: `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13868376534.zip`; SHA256 `128e0cdcc9c465f2dc0b5dac3505339e2127c4911898578442db345c1b7f5b68` (locally recomputed and matched).
- Required source identity independently checked with read-only `git rev-parse`: commit `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`, tree `988d6191b24c6f64b6c71014a0077be1e48c4327`. Original Darwin `metadata/git-identity.stdout.raw` records the same identity.

## Findings

### Linux: containment-prerequisite acquisition failed before product qualification

Let `LINUX` denote `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13867114561/contents/installer-evidence`.

- `LINUX/runner-preparation/apt-update.stdout.txt` lines 6–25 records failed Ubuntu mirror attempts; lines 2–5 records successful Microsoft package-index transfers. This is evidence of a specific failed acquisition route, not proof that all runner networking was absent.
- `LINUX/runner-preparation/apt-update.stderr.txt` lines 1–5 records temporary resolution failure for `azure.archive.ubuntu.com` and use of ignored/old index data.
- `LINUX/runner-preparation/apt-install.stdout.txt` lines 4–8 selects a new Bubblewrap install; lines 10–15 fails acquiring `bubblewrap` version `0.9.0-1ubuntu0.3`, amd64.
- `LINUX/runner-preparation/apt-install.stderr.txt` lines 1–2 identifies the failed `.deb` URI through `mirror+file:/etc/apt/apt-mirrors.txt` and the same resolver error. These raw streams do not record a numerical process exit status.
- `.github/workflows/installer-preview-posix.yml` lines 37–59 provisions Bubblewrap before the qualification step at lines 60–63. The archive contains only the four preparation streams; it contains neither `prerequisites.json` nor qualification output.

Classification: runner prerequisite acquisition failure. No original Linux product test failure or successful containment qualification is evidenced by this artifact. Retain the Bubblewrap/namespace requirement.

### Darwin: terminal bootstrap lifecycle stalls in both containment and host control

Let `DARWIN` denote `/tmp/r0016-successor-20261111/recovery/artifacts/r0016-13868376534/contents/installer-evidence`.

- Original `result.json` records Darwin arm64, kernel `24.6.0`, macOS `15.8.2`, Python `3.15.2` at `/opt/homebrew/opt/python@3.15/bin/python3.15`, commit/tree matching this checkout, and **zero product rows executed**.
- `metadata/bash-version.stdout.raw` line 1 identifies `/bin/bash` as Apple Bash `3.2.57(1)-release (arm64-apple-darwin24)`. The diagnostic cases themselves launch Python; that version record does not qualify Bash installer behavior.
- Both `same-profile/phases.raw.jsonl` and `host-control/phases.raw.jsonl` have 13 entries. Line 4 is parent `waitpid.before`. Lines 8, 10, and 12 are the child's `tty.open.after`, `tty.write.after`, and `tty.close.after`; line 13 is `child.exit.before` with `exitCode: 0`. There is no observed `waitpid.after`, printed terminal result, or completed subject.
- Same-profile parent/child PIDs are 1237/1238; host-control PIDs are 1584/1586. Both result records report `TIMEOUT` after about 30.003 seconds. Both stdout and stderr are zero bytes. The successful open/write/close markers exclude those instrumented intervals as the observed stall.
- Both cleanup records remain incomplete. Each parent was verified then stopped (`T<s`); the child remained `?<Es` across TERM and KILL attempts. `directChildReturncode` remains null. Do not treat the child exit-before marker as an exit receipt, `?<Es` as a reaped child, or the archived capture hashes as proof that producer processes had terminated.
- Frozen `terminal-probe.original.py` lines 12–13 blocks in `waitpid(pid,0)` before closing the PTY master. It never reads that master. Frozen instrumented lines 33–34 bracket the child immediately before `os._exit(0)` and lines 39–41 bracket parent wait. An undrained PTY/exit interaction is a concrete hypothesis, not an identified internal blocked syscall.

Classification: harness/bootstrap acquisition remains incomplete. The matching unsandboxed host control means a sandbox-only explanation is unsupported. No observed installer product failure and no basis to weaken the native sandbox, replace Apple Bash 3.2, or increase the subject timeout.

### Source correspondence and containment requirements

- Live `tests/install-preview.py`, `install.sh`, and `install.ps1` are byte-for-byte equal to the original Darwin frozen copies and the diagnostic's expected input digests. This verifies correspondence; it does not run or qualify them.
- Native terminal bootstrap is `tests/install-preview.py` lines 508–531. The parent blocks at line 521 and closes the unread master only at line 522. The diagnostic preserves the operation structure; its manifest reports `markerRemovalRestoresOriginalAst: true` and one `pty.fork`, one `os.waitpid`, one terminal write, two closes, and two alternative `_exit` calls.
- `tests/install-preview.py` lines 331–355 requires `unshare` plus Bubblewrap on Linux and `/usr/bin/sandbox-exec` on Darwin, with no uncontained fallback. Darwin policy at lines 210–227 permits the controlled terminal devices while denying network, outside writes, and native opener/clipboard helpers. The original same-profile markers establish return from the terminal open/write/close calls under that policy; they do not establish completed reaping.
- `tools/qualification/installer_native.py` lines 182–216 selects `/bin/bash` and rejects Darwin if its version is not 3.2. Keep this check. Bash version acquisition succeeded in the diagnostic; Bash installer execution did not occur in either PTY case.
- `.github/workflows/installer-preview-posix.yml` lines 7–9 triggers only for that workflow and `installer_preview_posix_probe.py`. Its Linux prerequisite acquisition is therefore not automatically reached by a `tests/install-preview.py` change. `.github/workflows/installer-native.yml` lines 9–16 includes the harness path and lines 38–61 runs qualification directly after checkout with no corresponding Bubblewrap acquisition. Any acquisition repair must be wired into the actual workflow selected by the repair, rather than relying on an untriggered focused workflow.

### Corroboration, with its limit stated

The Ruby project's original [bug #20682](https://bugs.ruby-lang.org/issues/20682) documents a matching native C reproduction: opening `/dev/tty` retains the controlling-terminal reference; exiting can then wait for unread PTY output, leaving an `?Es` child while parent `waitpid` blocks. It also reports a read-before-wait discriminator. This strongly supports the output-drain hypothesis. It is **not** a stack trace from our Darwin 24.6.0 run. Linked Apple source pages were unavailable to this investigation, so exact kernel-build attribution remains unverified. Retrieval reference: `turn816380708view0`, relevant source lines 109–141, 182–219, and 365–383.

## Narrow next diagnostics and conditional repair

### Linux acquisition

1. Before measured installer effects, retain the runner's public APT source/mirror selections, resolver results for the actual configured hosts, selected Bubblewrap package policy, and individual command exit statuses. Do not expose embedded credentials if a configured URI contains any. The original error identifies resolution of `azure.archive.ubuntu.com`, while fallback-looking archive/security names appear in stdout; it does not independently prove why each fallback failed.
2. Check and record whether a usable `bwrap` and `unshare` already exist; if acquisition is necessary, restore an authenticated official package route or use a prepared runner with recorded prerequisite identities. Preserve package metadata authenticity and binary/version bindings. APT's suggestion to use `--fix-missing` is not evidence that the required executable can be omitted.
3. The decision-changing result is successful, identity-recorded prerequisite acquisition followed by the **unchanged containment bootstrap** actually launching and establishing namespace, filesystem and transport denials. Installation success alone is not containment qualification. No retry count or timeout increase is proposed; respond to the observed resolver/package-route condition.

### Darwin terminal lifecycle

1. Keep the same native macOS host class, `/bin/bash` 3.2 gate, exact sandbox policy, known sentinel, original child open/write/close/exit sequence, and existing subject ceiling. Add a diagnostic variant whose only material operation change is that the parent drains the PTY master while observing child completion, rather than blocking in `waitpid` with unread output. Capture raw master bytes and successful byte counts; use readiness/nonblocking reads and nonblocking child-status observation so each state is distinguishable. This is a diagnostic proposal; no such run was executed here.
2. Require the original sentinel to be observed, the exact child to be reaped with status 0, terminal JSON to be complete, and all owned processes/captures to become terminal. Normalize the native terminal newline only for the assertion while preserving raw bytes. A read result without child reaping is incomplete. Closing the master early or deleting the terminal write could hide the defect and would not satisfy the original capability probe.
3. **Decision-changing discriminator:** if the unchanged child and policy complete promptly when the parent reads the original sentinel, and the archived original ends at exit-before/wait-before, parent PTY-drain ordering is the operative harness defect. The narrow conditional repair belongs in the bootstrap's parent PTY lifecycle in `tests/install-preview.py`, not in either installer. Re-run the actual contained bootstrap and intended native qualification with source/tree bindings after repair.
4. If the variant reads the complete sentinel yet still fails to reap, the drain hypothesis is insufficient. Retain the before/after read/reap markers and sample the verified owned child/parent's wait channels or stacks on the same native host before destructive cleanup. This distinguishes another exit-state wait from interpreter behavior without changing policy, shell, or timer to obtain a pass.
5. Preserve complete cleanup as a separate gate. The current diagnostic freezes its parent, sends TERM/KILL to the child, and refuses to terminate that parent while the child remains live (`installer_preview_posix_probe.py` lines 303–355). In the hypothesized PTY dependency, the stopped parent continues to own the unread master and cannot drain or close it. Its `6`-second cleanup allowance was not exhausted: the returned elapsed values were about 0.537 and 0.585 seconds. Increasing that allowance does not repair the dependency. A replacement diagnostic must provide an owned PTY drain/close and child-reaping path while retaining verified process identity; otherwise it must remain explicitly acquisition-incomplete.

## Interpretation traps excluded by the original records

- `terminalIoObserved: false` is the diagnostic's combined predicate, requiring process success, child reaping, parsed terminal JSON and terminal markers. It is not evidence that `/dev/tty` open/write was denied.
- Empty stdout caused the recorded JSON parse error after the timeout. That parse error is downstream of the lifecycle stall.
- `rawCaptureMechanism: Direct regular files; no pipe EOF/drain dependency` describes the outer stdout/stderr capture. It does not drain the nested PTY master inside the extracted subject.
- A `child.exit.before` marker with exitCode 0 records intent immediately before `_exit`; it is not an observed exit status.
- Same-profile and host-control concordance does not establish that every native containment control passes. It does make weakening the sandbox an unsupported first intervention.
- No interpreter comparison was performed. Python 3.15.2 is bound in the evidence, but these records do not establish an interpreter-version defect.
- Historical original artifacts remain acquisition-incomplete; a later successful repair cannot retroactively turn them into product qualification passes.

## Digest index

All hashes below were recomputed from recovered bytes. Paths are relative to the `LINUX` or `DARWIN` roots defined above unless prefixed with `repo:`.

| Evidence | SHA256 |
| --- | --- |
| LINUX/runner-preparation/apt-install.stderr.txt | `6f95528caf7e02bd6174679931f3362c075c58efebca91be010ab23e92914f84` |
| LINUX/runner-preparation/apt-install.stdout.txt | `b719f921e13376c0c69e872c0a16fa592763e9ac3adbcc8e15b493d3708c2f2c` |
| LINUX/runner-preparation/apt-update.stderr.txt | `903d7338a9b64a202746e3fa93ef90e5b4b66cb8d80d81b14c6de82a87cbb36a` |
| LINUX/runner-preparation/apt-update.stdout.txt | `13a88ea57d70c334e75572673d145093457a712c74e878ddf191db2b75a53b52` |
| DARWIN/frozen/terminal-probe.original.py | `8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904` |
| DARWIN/frozen/terminal-probe.instrumented.py | `f006977235f1ea27b2043c83a0877295c3c8a99241c031c7a6679b5417f7946e` |
| DARWIN/same-profile/phases.raw.jsonl | `9450c7ddff205e13e4aad0b0a5d3c22844afe96f87cca2650e6a51fa629da52b` |
| DARWIN/host-control/phases.raw.jsonl | `48c4bca3c97d4b09c2a14a2b6d67f9b919372dbe6725211a2565cb55921a53c5` |
| DARWIN/same-profile/result.json | `0f7eacc95f7c370c21764d545c0eaf8214163318f1144c834d45d9a9bc375d61` |
| DARWIN/host-control/result.json | `44789b7cd51045638b6e029a9320f760349e30505f58d3c89e300c277db7377b` |
| DARWIN/metadata/bash-version.stdout.raw | `c88869c8cc06c4173d23a07807307d46ee0a83ad4aa3ab6a346c483f2856f5d2` |
| DARWIN/result.json | `86506deb4592a138382f74c584aefa9f517d89dd43933d82bf9f6e5fd0598c9d` |
| repo:tests/install-preview.py | `5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760` |
| repo:tools/qualification/installer_preview_posix_probe.py | `7e36b03ec69e82d780303da8c59853f811837c532c389a1bf759ad9d6d7cc207` |
| repo:.github/workflows/installer-preview-posix.yml | `6289af8be948c1083965143dd09f635bc4e478c08cc025d667a411b423d217a4` |

## Investigator completion

Read-only evidence/source review is complete. No tests or diagnostic subjects were executed; no source files, Git references, or remote state were changed by this investigator. Only this authorized report was written. No credentials were encountered in the selected reviewed evidence. This report conveys bounded findings and recommendations, not mutation, qualification, release, or closure authority.

Report state: FINAL
