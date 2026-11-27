# Portable Capture Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this
> bounded source packet, followed by an independent exact-tree review.

**Goal:** Preserve exact case-sensitive private evidence paths and bytes through
the unchanged envelope's portable archive namespace.

**Architecture:** A separate standard-library stage/restore adapter stores flat
numbered payloads and an encrypted private logical-path map. It validates complete
populations and hashes, uses private descriptor-bound staging, and exclusively
restores the original tree. Crypto, observation recipes and workflow are unchanged.

**Tech stack:** Python standard library, existing envelope path/JSON validators,
POSIX directory descriptors. No dependencies, native browser or key operation.

**Spec:** `tools/qa/hosted-native/CAPTURE_TRANSPORT.md`.

## Global constraints

Preserve original paths, bytes, hashes, files and empty directories. Keep the
existing envelope unchanged. Maximums: 19,999 files; 20,000 directories; depth 64;
1 GiB per file; 8 MiB mapping; 4 GiB for payload plus map. Refuse symlinks, existing
outputs, source/runtime overlap and incomplete populations. CLI logs contain only
fixed markers/categories. No native evidence, keys, remote mutation or workflow
activation. The root task already authorizes this approach and autonomous source
implementation; no additional owner decision is introduced.

## Review focus

- Parent aliases or parent substitution must never redirect output into source/runtime.
- Case-colliding logical directories must not silently merge during restoration.
- Input mutations and partial writes must fail with original evidence preserved.
- Duplicate/extra/missing map or payload members must never produce partial success.
- A malformed CLI input must not expose private paths or content in diagnostics.

## Task 1: Exact portable staging and restoration

**Files:** create `tools/qa/hosted-native/capture_transport.py`,
`tools/qa/hosted-native/test_capture_transport.py`; update only the new command
entry in `tests/regression-population.json` alongside these docs.

**Interface:** `execute(operation, source, output, *, protected_roots)` performs
`stage` or `restore`, returning a non-content completion summary. CLI exposes
those operations with required `--source`, `--out`, repeated `--protect` arguments.
The package uses `salah-portable-capture/1`, `mapping.json`, and consecutive
`payload/00000000.bin` members, with no alternative schema or partial admission.

- [x] Write source-only controls for round trip, case-distinct names/directories,
  empty files/directories, exact envelope ZIP interoperability, hostile mappings,
  limits, symlinks, aliases, source drift, retention failure and CLI privacy.
- [x] Record expected failing controls before implementation.
- [x] Implement descriptor-relative bounded copying and strict mapping admission,
  complete source/output verification, exclusive publication and owned cleanup.
- [x] Run the new controls and registered runner census; inspect all results.
- [x] Verify envelope/recipes/workflow bytes unchanged and existing registry entries
  preserved. Perform an actual synthetic stage/archive/extract/restore replay.
- [ ] Independent exact-tree review of the committed source packet and hashed
  receipts. Workflow integration remains explicitly outside this source checkpoint.
