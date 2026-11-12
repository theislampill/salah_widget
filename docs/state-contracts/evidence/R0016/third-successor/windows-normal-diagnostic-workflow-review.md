# Bounded review: Windows normal profile diagnostic workflow

## Finding

No workflow integration defect was found in the supplied candidate. The workflow invokes the corrected diagnostic runner with compatible arguments, checks out every pinned dependency from the triggering commit, and retains the existing exact PowerShell acquisition and C-profile preparation. This is a static engineering review of the workflow boundary; diagnostic receiver semantics are delegated to the separate review requested by the parent.

| Candidate | Bytes | SHA-256 |
|---|---:|---|
| Workflow | 4886 | `607e91973fe68158b67d4ae9837cc0f1da29b519b653533011194a226379dcb3` |
| Corrected diagnostic runner | 27093 | `0dbaa611c5c178983f79f24cdf25b1a5e33dee66f13201025d571baa5e42cb77` |
| Accepted full-entry workflow comparison | 5523 | `85ee6d81a9ab041cc745ebe776ada0159817587e0692724943997e1255c120a4` |

## Source and dependency compatibility

All 14 runner `INPUTS` entries match immutable Git object bytes from combined commit `a4c617ebeedfb507c0cb7a472683cce47ad62522`. Sparse checkout contains exactly those 14 paths plus the new runner, with no omissions or duplicates. The 12 inherited outer inputs match the corrected full-entry collector's `INPUTS`; the host probe matches its separate `HELPER_SHA` constant. The outer collector itself is pinned at SHA-256 `652848809fc581452e4bf48e2895786cd3c780e60e0a2c3091e2969d7b856616`.

The two matrix values `ps51` and `ps766` match the runner parser. The runner maps `ps766` to its internal `ps7` host and schedules `default` and `no-gather`, each with `positive` and `no-open` scenarios. `ps51` schedules `warm20` with those same two scenarios. This is six normal entries across two native jobs, rather than six entries per job. The acquisition step is byte-identical to the accepted full-entry workflow, including its Python-only transfer, exact PowerShell 7.6.6 archive SHA-256 verification, exclusive archive/runtime creation, and executable export. The runner separately retains the pinned executable check.

Checkout uses `${{ github.sha }}`, and the same value is passed through `--source-commit`. The preparation step retains the native 64-bit Python and canonical C-drive USERPROFILE requirements; its only command change is the diagnostic archive basename. All run steps use `cmd` and propagate their command exit status. The three diagnostic execution arguments and archive-only argument shape match the runner parser and its respective branches.

## Trigger, lifetime, and evidence behavior

The workflow triggers only for the new workflow or new diagnostic runner on `pro/r0016-effect-free-preview-20261111`. It retains read-only repository permissions, no persisted checkout credentials, separate concurrency identity, no cancellation of in-progress runs, and no `continue-on-error`. Unlike the full-entry workflow's acquisition-only skip, this diagnostic has no job-level skip condition. That is compatible with collecting this bounded diagnostic on a marked acquisition commit without granting full-entry credit.

Both Windows jobs have a 30-minute workflow bound. Runner mode limits remain 480 seconds with a 60-second version phase. The PS7 plan's bounded native phases total at most 17 minutes before setup/copy/archive overhead; this is a scheduling bound, not a guarantee of completion or filesystem/network confinement.

Archive and upload steps both use `always()`. The archive command selects the runner's `--archive-only` branch and the C-profile output parent established by the preparation step. Static inspection of `archive_root` confirms exactly one owned `r16d-` root, canonical path checking through the pinned outer helper, a new absolute sibling archive destination, `lstat`-based traversal, and explicit symlink/reparse recording without recursive traversal through those entries. Upload names include host, run ID, and attempt, and missing artifacts are errors. `always()` schedules an evidence attempt; it cannot guarantee a complete archive after an unrecoverable runner/job interruption.

The runner continues to label successful acquisition `DIAGNOSTIC_ONLY` with `qualificationAccepted=False`. The workflow neither relabels the underlying original results nor supplies qualification credit. Narrow path filters intentionally do not schedule this diagnostic for unrelated later dependency-only edits; its exact dependency guards would reject changed inputs if subsequently invoked without corresponding pin updates.

## Verification and limits

The independent checker parsed YAML, compared the candidate against the immutable accepted workflow, verified the 14 dependency objects, checked both matrix routes through the exact extracted pure `modes` function, compiled the two workflow Python one-liners inertly, and compiled the runner without execution. All checks passed.

The first reviewer probe contained an incorrect assumption that the outer helper pin lived inside `outer.INPUTS`. Inspection showed the accepted separate `HELPER_SHA` binding; the probe was corrected to verify both bindings, and the unchanged candidates passed. This reviewer-probe error is retained in `checks.json` and did not lead to a source change.

No Windows or PowerShell execution, download, CI trigger, browser use, Git mutation, shared edit, receiver requalification, publication, or closure occurred. Native collection and the independent diagnostic receiver review remain prospective/separate.
