# Raw evidence custody

This branch is evidence-only and must not be merged into the GitHub Pages branch.
The documentation PR contains only README.md and DESIGN.md.

Large JSON receipts are published as lossless gzip files. The payload manifest
records the original and published byte counts and SHA-256 hashes. Decompressing
each gzip must reproduce the exact original hash. The original uncompressed files
remain in the isolated local evidence worktree. Native PNGs, original Chromium
recordings, retained historical failures, commands, fixture snapshots and raw test
failures are published without image or video transformation.

Per-attempt `execution-manifest.json` and `executed-fixture/` identify the actual
executed fixture. `fixture-provenance.json` records initial intake, while
`qualification/fixture-current.json` and its cumulative patch describe the final
issue-specific adaptation. They do not retroactively change prior attempt inputs.

Pre/post-teardown reports preserve observations even if cleanup fails. A process
exit or teardown return is separate from native acceptance. The failed original
Firefox manifest-header attempt has no final receipt and is not counted as a
passing case. Existing Firefox recording failures are retained as failures;
fresh Firefox qualification uses native screenshots and source-bound render
observations, without claiming a continuous Firefox screencast.
