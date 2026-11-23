# R0038 R38-X1 — R28-L13 discriminator at two Node versions (evidence record)

Work order R0038 (issue 105), acceptance row R38-X1; ledger entry R28-L13 in `tests/expected-failures.json`.
Contract text: `docs/state-contracts/R0038.md` section 7.2. Executed 2026-11-22 local time (the run timestamps in
`env.txt` are UTC, 2026-11-23T01:05Z to 01:08Z). Retained evidence, excluded from the Pages build (R002B).

## What was run

`python tools/cp9/run_scientific_regressions.py --output <dir>` in a fresh clone at `06b6e93b` (clean tree before
and after, `clone-status-after.txt` empty), Windows, Python 3.11.9, `TMP`/`TEMP`/`TMPDIR` under scratch. The runner
finds Node as bare `node` on `PATH`, copies `vendor/real-sky` to a temporary directory and hashes the source before
and after (`oracleUnchanged`). Two runs per Node version, driven by `driver/run_one.sh`:

| Run | `node --version` in the run shell and in `results.json` | scientific-js | `diffuse-off is bit-identical to all 12 captured CP6 cases` | scientific-python | runner |
|---|---|---|---|---|---|
| `control-1`, `control-2` | v24.14.0 (system Node, the gate's pinned version) | 305 tests, 304 pass, 1 fail | not ok: actual `8d6a35c4bf8d563a5d26c9829eca7cd3027fa8affc5abc83aa1d2fcbe0416517`, expected `8b6af133990f531c1561dfb397062d65e71eae56bb0d589a1eb993c6c0f042ee` | 117 run, OK, 1 skip | exit 1, `FAIL`, `oracleUnchanged: true` |
| `v22-1`, `v22-2` | v22.16.0 (portable runtime, prepended to `PATH` in the run shell only) | 305 tests, 305 pass | ok | 117 run, OK, 1 skip | exit 0, `PASS`, `oracleUnchanged: true` |

The skip is the vendor seal test `test_symlinks_never_pull_external_bytes_into_archive` ("host cannot create
symlinks"), declared as R28-L14. `cross-run-comparison.json` is computed from the four `outcomes.txt` files: the same
305 case names in every run, and exactly one case whose outcome differs, the one above. An independent reviewer
(separate context, own download and clone) ran each configuration once and got the same counts and digests.

## Runtime identity

- Source: `https://nodejs.org/dist/v22.16.0/node-v22.16.0-win-x64.zip`, 35,466,975 bytes, SHA-256
  `21c2d9735c80b8f86dab19305aa6a9f6f59bbc808f68de3eef09d5832e3bfbbd`. That equals the line in the official
  `SHASUMS256.txt` (`download/SHASUMS256.txt.excerpt`) and `nodeZipSha256` in `docs/real-sky/evidence/environment.json`.
  The hash was checked before extraction by both executors. The zip and the extracted runtime are not committed and
  were not retained; this record does not re-hash them.
- `SHASUMS256.txt.sig` verifies as a good signature over `SHASUMS256.txt` by RSA key
  `C0D6248439F1D5604AAFFB4021D900FFDB233756` (`download/signature-and-hash-check.txt`). The first executor used it
  as a Node.js release key; this record did not re-check the Node.js release-key roster. The signature was
  re-verified offline for this record with a scratch keyring built from the same key file. The key is not certified in a
  local web of trust (gpg reports `[unknown]`), so the hash match to the repository-recorded value is the stronger
  identity check. The `.asc` line "not a detached signature ... NOT verified" comes from passing a clearsigned file
  as if it were detached and is harmless: the `.sig` check covers the same file.
- What v22.16.0 is: the Node version in the CP9 import's qualification environment receipt
  (`docs/real-sky/evidence/environment.json`, `docs/real-sky/QUALIFICATION.md`) and in the archive's own start note.
  It is not a vendor-declared pin. Nothing in `vendor/real-sky` names the runtime that captured the CP6 fixtures,
  so that runtime remains unknown.

## Limits

- The responsible runtime component (V8 `Math`, ICU, `Date` or other) is not isolated.
- Nothing follows about browser-shipped bundles, which run on the browser's own engine.
- Linux at v22.16.0 was not run. The Linux half rests on R002A (red at v24.14.0 with the same digest).
- The runs were not network-blocked. By reading its source, the runner makes no network request (no `http`,
  `socket`, `urllib` or `requests`).
- Under the active ledger entry, running the full registered runner at Node v22.16.0 reports R28-L13 as an
  unexpected pass (FAIL). That is expected.

## Files and redaction

- `runs/<run>/`: `env.txt`, `stdout.txt`, `exit.txt`, `outcomes.txt`, `clone-status-after.txt`; `runner/results.json`,
  `scientific-python.log`, `viewer-build.log`, and `scientific-js.excerpt.txt` (the TAP summary and the first failing
  block). The full `scientific-js.log` is kept for `control-1` and `v22-1` only. The repeats are byte-identical in
  their outcomes, and their original logs are pinned by digest in `ORIGINALS.sha256`.
- `driver/run_one.sh`: the driver as run.
- `ORIGINALS.sha256`: SHA-256 and size of every original, unredacted file, including the four downloaded signature
  and key files, which are not committed.
- Redaction: local absolute paths were replaced by `<REDACTED:SCRATCH>` (the executor's scratch root),
  `<REDACTED:PYTHON311-DIR>` and `<REDACTED:SYSTEM-NODE-DIR>` (the directory holding the system `node`). The release
  signer's e-mail address in the gpg output became `<REDACTED:EMAIL>`. Per-file counts are in `REDACTIONS.json`.
  The committed copies are also normalised to LF line endings. Nothing else was changed, so these copies differ from
  the digests in `ORIGINALS.sha256` by design.

## Reproduce

1. Download only the zip and `SHASUMS256.txt` (optionally `.sig`) from `https://nodejs.org/dist/v22.16.0/`. Check
   `sha256(zip) == 21c2d973…bbfd` against both `SHASUMS256.txt` and `environment.json` before extracting. Extract
   into an empty scratch directory. Run no installer and no `npm`.
2. Make a fresh clone at the commit under test and confirm it is clean.
3. In one shell, set `TMP`/`TEMP`/`TMPDIR` to scratch and run
   `python tools/cp9/run_scientific_regressions.py --output <new dir>` with system Node (control). Then, in a
   shell whose `PATH` begins with the extracted `node-v22.16.0-win-x64` directory, confirm that `node --version`
   prints v22.16.0 and run the same command into another new directory.
4. Compare `results.json` (`status`, `node`, `oracleUnchanged`) and the `diffuse-off` line of
   `scientific-js.log`. `driver/run_one.sh <label> system|v22` performs step 3 in Git Bash once its scratch root
   is set.
