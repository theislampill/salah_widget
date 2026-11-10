# Receiving adapters

The original integration ZIP and extracted package remain unchanged. These diffs
record receiving-only corrections; none changes terrain, material, profile,
worker numerics, preimages, branch pin, postimages or deterministic-build gates.

- `installer-worktree.patch`: the installer excluded `.git` directories but tried
  to inventory the root `.git` pointer file of linked worktrees. Exclude only
  verified receiver metadata; a `.git` payload remains rejected. `--package`
  permits the patched installer to read the original sealed package externally.
- `installer-fixtures-windows.patch`: fixture manifest keys use POSIX separators,
  expected fixture bytes use explicit LF, and unavailable Windows symlink
  creation is reported as SKIP. Added a real linked-worktree application and an
  unlisted `.git` payload rejection control. Original run: 10 passed/10 failed;
  corrected fixtures and installer: 20 passed/2 explicit privilege skips.
- `browser-navigation.patch`: the supplied runner aborted its own `file:` entry
  through its foreign-host filter. Admit only files beneath the receiving root;
  use real local HTTP requests in navigation mode. Browser sandbox and web
  security are unchanged. The original failed receipt is retained.

For reproduction, copy the package installer/tests or browser runner to an
external working folder, apply the corresponding reviewed diff, and pass the
receiving repository with `--repo`/`--root`. Pass the original package to the
installer with `--package`. Preserve the original package for verification.
These are qualification tools, not additional runtime implementations.
