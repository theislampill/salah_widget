# R0021 qualified implementation archive

## What is preserved

The [Git bundle](qualified-implementation.bundle) contains the complete, locally committed bounded Moon correction, generated runtime, three added controls and its qualification evidence. The [exact binary-capable patch](implementation.patch) is a second review surface; it represents all 18 files in that commit.

| Object | Identity |
| --- | --- |
| Archived commit | `2df6a75474f3b0fce2ba72cbf94a7640569bcf2f` |
| Archived tree | `99238730f8dcc37eb66ac9a21cc261fc6067628f` |
| Required parent | `feddf007e537a38972056d7d56243321884ab41f` |
| Runtime SHA-256 | `d82bcbd724cee5c0eae3d42c6fdb543150b00541ee73079fb26656bdf41542af` |
| Bundle bytes / SHA-256 | 25,722 / `f24d9fad07a8c75b9f73f67565fd0b623ba908435e72823d9bbd663288e0e10f` |
| Patch bytes / SHA-256 | 82,097 / `c399a7f8039a9e1e4db7b2f52bd1116068d46b0090c56ac784e34eeb515c646c` |

`git bundle verify` succeeded against the required parent before publication. The archived commit is inside this file, not an applied GitHub branch commit. The PR branch's runnable files remain r26. This evidence checkpoint must not be presented as the new runtime being deployed or applied to the branch.

The exact candidate has 95 affected passing tests, two deterministic canonical builds and separate read-only source/build review. See [QUALIFICATION.json](../r0021-empty-surface-20261018/QUALIFICATION.json), [REVIEWERS.json](REVIEWERS.json) and the [recovery report](../../R0021_PRO_RECOVERY.md). These results do not certify native timing, continuous appearance, all callback costs or release readiness.

## Why code publication is pending

The local Git client could not authenticate to GitHub. The available GitHub connector requires complete file content and its IPC frame is limited to 67,108,864 bytes. The generated offline entry alone is 81,693,080 bytes. The attempted blob submission was rejected before execution with an 82,895,057-byte frame. No partial runtime was published, no credential was obtained, and no alternate workflow was installed.

Applying this archive requires an authenticated Git environment. It does not require another implementation, a Codex run or a new PR.

## Apply without overwriting this checkpoint

Use an isolated clean checkout of the current `codex/r0021-startup-completion` branch. Read current repository instructions. Fetch the current remote branch and main, and inspect any intervening changes before proceeding. Do not reset the remote branch to the archived commit: that would discard the later documentation checkpoint.

Verify the downloaded bundle and patch against the hashes above. Verify the bundle prerequisite and import its objects without moving a branch:

```bash
git bundle verify docs/real-sky/evidence/r0021-pro-recovery-20261018/qualified-implementation.bundle
git bundle unbundle docs/real-sky/evidence/r0021-pro-recovery-20261018/qualified-implementation.bundle
```

Before restoring files, compare their current Git blobs with the six parent entries in [ARCHIVE.json](ARCHIVE.json). If any differ, or any other runtime owner/data/build input changed since the parent, stop automatic application and assess that actual delta. Existing qualification must not silently transfer over newer work.

If those currentness checks hold, restore exactly the six source/test/generated files from the imported commit, preserving the documentation already on the branch:

```bash
git restore --source=2df6a75474f3b0fce2ba72cbf94a7640569bcf2f --staged --worktree -- moon/src/moon-native.mjs moon/tests/host.test.cjs index.html offline.html moon/moon-host.js moon/BUILD.json
git diff --cached --check
git diff --cached --stat
```

Compare the six staged blobs with the archived entries in ARCHIVE.json and all 142 runtime files with the candidate [runtime inventory](../r0021-empty-surface-20261018/runtime.json). The inventory defines its canonical digest algorithm. The 12 qualification files in that directory must remain byte-identical to the archived commit.

Create an ordinary reviewable commit on the current PR branch and push normally, after checking that the remote head has not advanced. Do not force-push. Independently read back the resulting remote head, parent, tree and generated runtime identity. The resulting commit/tree will differ from the archived commit/tree because this documentation checkpoint is retained; the six candidate files and qualified runtime must match exactly.

No production merge is authorised by these instructions. Native acceptance gaps remain as recorded in the recovery report. The owner must approve a genuinely qualified exact head and base before the production sequence.

