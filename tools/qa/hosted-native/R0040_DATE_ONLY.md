# R0040 Date-only clock diagnostic

`r0040_dateonly.cjs` is a separate diagnostic acquisition entry for the original
Chromium/bday/moderate/M1/common capture on genuine main. It keeps the original
capture driver, eight positional arguments, source/weather assertions, CDP
sampler, renderer cost measurements, reports and lossless verifier unchanged.
Its acquisition status is `ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION`.
That status does not establish cadence, pixel fidelity, human acceptance or a
production treatment. The original full-clock observations remain unchanged.

This packet was reconstructed after a workspace loss. The public historical
helper was recovered byte for byte. The new wrapper and controls have a new
source identity and require fresh independent review; a previous review of
lost local files cannot qualify this reconstruction.

## Exact single-seam transformation

The fixture `fixtures/r0040-precip-eval-original.txt` contains the exact public
historical helper from commit `4029d2f67f5a880c8ad889443bb7557d96022c45`:
17,990 bytes, SHA-256
`a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7`.
Its 136 CRLF line endings are preserved by the adjacent `-text` attribute.
It contains no private capture material.

The wrapper verifies that entire original body before replacing its one
full-clock install/pause/resume line in memory. The replacement accepts only
the original running scene and installs a Date proxy before navigation. Date
starts at the requested synthetic epoch and advances at 1x with that document's
unchanged `performance.now()`. Date construction with arguments, function calls,
parsing, UTC conversion and native prototype behavior remain available.

The replacement never calls Playwright's clock installation, pause, resume or
fast-forward APIs. It leaves timer, rAF, performance object, `performance.now`
and `performance.timeOrigin` references unchanged. The helper's other bytes,
routes, fixtures, scene calculations and exported functions remain intact.
Reversal must reproduce every original byte. Receipts record the original and
transformed helper hashes, installer-function hash, byte counts and one changed
seam. The prepared historical file on disk is not rewritten.

The entry requires the unchanged capture-retention body at SHA-256
`d252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f`.
That entry already checks the original driver, guarded preparation and every
declared source. The Date-only entry also requires the actual outer preparation
entry's integer exit zero, no timeout or retention error, exact argv/cwd and
preparer identity. The existing current nonroot namespace receipt is checked
before any original helper, driver or browser-module import. A failed source or
preparation check cannot select another helper.

## Startup clock proof and retained failures

After the actual helper opens the scene, the wrapper obtains one bounded startup
proof: before/after snapshots, one timer callback and two rAF callbacks. Each
snapshot records the unchanged function identities, time origin, a native
performance bracket, `Date.now()` and a Date construction. Admission recomputes
the 1x Date relationship from those brackets in the same document. It does not
subtract worker clocks, assign a presentation timestamp, or qualify frame rate.
The probe records raw data before validating it. Malformed/partial proof remains
`INCOMPLETE`; evaluation failure or host timeout remains `UNAVAILABLE`.

The capture driver receives its context only when `openScene()` returns. If the
new installation or startup proof fails after context acquisition, the wrapper
closes that context before rethrowing the identical primary error. A secondary
cleanup error is retained separately. Browser/server cleanup still occurs in
the unchanged original driver. No missing proof or cleanup fault produces an
admitted final receipt. Original exceptions and a prevented-continuation exit86
retain their precedence.

The final private receipt and terminal journal event bind the diagnostic source
identity and complete clock proof. Existing request/page/crash/disconnect,
cleanup and retention checks still apply. The original `capture.json` is never
rewritten. A final journal/receipt write or fsync failure yields an actual
nonzero process status; a partial readable event cannot confer admission.
SIGTERM/SIGKILL retain whatever original PNGs and journal prefix were obtained,
without inventing terminal evidence.

This instrumentation has cost. Date reads perform an additional native
performance-clock calculation, and the startup callback proof adds work before
capture. Existing host retention performs serialization and fsync. The timing
class is `instrumented-date-only-clock`. No new CDP frame listener, per-frame
copy or per-frame fsync is added. The unchanged lossless verifier must assess
the retrieved acquisition independently, followed by the existing human and
owner gates.

## Native entry and source controls

```sh
R0040_DISPERSION=common node tools/qa/hosted-native/r0040_dateonly.cjs \
  --driver /research/tools/qa/r0040/capture.cjs \
  --manifest /orchestration/docs/state-contracts/evidence/R0040/native-capture-preflight.json \
  --prepared /task/work/r0040-capture/receipts/prepared.json \
  --preparation-process /task/capture/r0040-preparation/process.json \
  --preparation-entry /task/capture/r0040-preparation-entry.json \
  --evidence /task/capture/dateonly-retention -- \
  /dependencies/node_modules/playwright /task/work/r0040-capture/historical \
  /task/work/prepared/trees/main /task/capture/dateonly \
  chromium bday moderate M1
```

This command additionally needs the coordinator's admitted current namespace
receipt and cleared `R0040_OPTIONS`. The example names private destinations; it
is not a standalone authorization or a record of native execution.

`hosted-native-r0040-dateonly-controls` runs 13 Node TAP cases. They exercise the
actual pinned driver and transformed actual helper with bounded page, HTTP and
CDP doubles; the native clock proof itself runs in a synthetic VM boundary.
Controls cover exact reversal, Date semantics/reference preservation, malformed
raw proof, actual outer-entry failure/retention rejection, failed-open cleanup,
primary/secondary errors, late page/request/lifecycle faults, veto86, durability,
timeout prefixes and source drift. They launch no browser. All executed helper,
fixture and original-driver inputs are listed in the registry; the entry's
native role is documented here, without a duplicate exclusion classification.
