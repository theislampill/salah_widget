# R0040 capture final-state retention

`retain_r0040_capture.cjs` executes the unchanged, pinned original
`tools/qa/r0040/capture.cjs` with its eight original arguments. It adds a separate
private request/error/cleanup journal and a terminal admission receipt. The
original `capture.json`, original assertions, browser clock, frame sampler,
screenshots, PNG files, renderer cost measurements and cleanup order remain
unchanged. No option-oracle completion rule is used for capture.

The original writes `capture.json` before its nested context/browser/server
cleanup. A readable original report therefore does not establish successful
cleanup or absence of a late page or request failure. This successor preserves
the report and separately records the terminal state. It does not convert a
failed original into success or confer native cadence or human acceptance.

## Source and preparation admission

| Bound source | SHA-256 |
|---|---|
| Capture retention wrapper | `d252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f` |
| Guarded preparation entry | `4ba6328ee9fe96aec4a96109c58d0d67e0d3e434756829fbe247816bcd001f68` |
| Original capture driver, 9,794 bytes | `19a766ccacf0ac784f46961a5cd0079390f10a34d14825ef5ac7b28adbd33e26` |
| Full preflight manifest | `267f2fd8ac130c049430ffdaa0fd50b72457c60084b49360346748cc940f6b73` |
| Exact documented preparation recipe | `9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730` |
| Reviewed generic retention source used only for namespace/continuation guards | `5e4418ac9d5cda410404462d2f8051959eac53e59d4e7304ac68dc33e39d1328` |

Use the separate
[`r0040_capture_prepare.py` entry](R0040_CAPTURE_PREPARATION.md) first. Admission
requires its actual outer exit zero, original `PREPARED` receipt, supplemental
successful child-process receipt, both complete patch stages and all six final
historical files. The capture wrapper binds the preparation entry's source hash,
the extracted recipe and manifest hashes, the original receipt hash and all
input/output paths. The coordinator must independently check the preparation
entry's actual exit: its receipt's `returncode` describes the guarded recipe
child, and cannot certify the enclosing entry process.

Before importing any original driver, historical helper or Playwright module,
the native CLI verifies the current nonroot network namespace and admitted
isolation receipt. It then verifies the actual immutable research HEAD and all
12 declared research input hashes; all six patched historical file hashes,
sizes and Git blob identities and their exact population; genuine clean main
HEAD; the generated inventory and all 116 members; and the 177-file main runtime
manifest. It rechecks source after preparation without modifying any input.
The complete manifest records the six preimages and both patch-stage postimages.

The native cell is limited to Chromium, `bday`, `moderate`, `M1`, common
dispersion, and cleared `R0040_OPTIONS`. The source pins remain:

| Capture pin | SHA-256 |
|---|---|
| Main product | `88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1` |
| Patched geometry | `95185755b16cd8773b9cb23a70787dd7492d8068e90f754567c845c401cccfe8` |
| Patched renderer | `f6f6b2b7a979af480e8aaba515292e266927e4bf22d6495840b6916d502c12cc` |

The admitted cwd is the immutable research checkout. Capture and supplemental
evidence directories must both be fresh, separate and outside the source inputs.
The coordinator keeps disposable sources outside its enclosing private capture.

## Native invocation

Run only after coordinator isolation and preparation admission:

```sh
env -u R0040_OPTIONS R0040_DISPERSION=common \
  "$NODE" "$HOSTED_NATIVE/retain_r0040_capture.cjs" \
  --driver "$RESEARCH/tools/qa/r0040/capture.cjs" \
  --manifest "$CAPTURE_MANIFEST" \
  --prepared "$CAPTURE_NEW_WORK/receipts/prepared.json" \
  --preparation-process "$CAPTURE_PRIVATE_PREPARATION/process.json" \
  --evidence "$CAPTURE_PRIVATE_FINAL_STATE" \
  -- "$PLAYWRIGHT_MODULE" "$CAPTURE_NEW_WORK/historical" "$CLEAN_MAIN" \
     "$CAPTURE_PRIVATE_ORIGINAL" chromium bday moderate M1
```

`SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT` must name the coordinator's admitted
receipt for the current namespace and UID. Keep the existing explicit reviewed
Playwright module and cleared loader environment. The wrapper does not launch
an alternate engine, change launch flags or retry a failed scene. The proposed
outer 180-second capture process-group bound remains with the coordinator.

## What is retained and what is changed

`events.jsonl` records request observation, attempted and completed route actions,
route exceptions, browser request completion/failure, page errors and crashes,
page-operation exceptions, original driver error output, and context/browser/server cleanup.
It retains the actual source and isolation custody separately. Original scene
log objects are read again at process exit, including changes made during
cleanup. An uncaught-exception monitor records fatal diagnostics without
installing an exception handler or changing Node's fatal behavior.
Browser disconnection before the original `browser.close()` call is recorded as
unexpected and fails supplemental admission. Disconnection during that close is
recorded as expected; page crash always remains a failure, including during cleanup.

The original catch-all route must be installed before page creation and the
original service-worker block must remain. An attempted external `continue` is
vetoed before the actual call and an abort is attempted. The final status names
this **prevented external continuation**; it does not assert an observed network
escape. Route bypass/removal methods are refused. Original known fixture routes
and normal unknown-request aborts retain their behavior. Expected request aborts
are recorded without treating their resulting browser request failure as a
successful external continuation or an unexpected network failure.

The raw CDP session is returned to the original driver, with its original raw
page argument. No wrapper callback is attached to `Page.screencastFrame`; no
additional per-frame copy, hash, acknowledgement or fsync is introduced. The
original driver alone writes PNGs during capture. The supplemental wrapper reads
and hashes the existing PNG files after the original process has finished its
asynchronous work. It never rewrites, deletes or duplicates them.

This remains **instrumented** acquisition. Host request/error/close serialization
and synchronous journal writes add overhead; wrapper promise boundaries can also
affect scheduling. Original timing and cost measurements retain their original
values and algorithms, with this provenance attached separately. They are not
represented as an uninstrumented timing replication. There is no per-frame crash
durability claim beyond the original PNG writer's behavior.

`final-admission.json`, protocol `r0040-capture-final-admission/1`, includes:

- Original report hash, existing PNG names/sizes/hashes and original process
  exit status, without replacing the report or its measurements.
- Complete retained request actions and final browser states, page errors,
  final original scene log and context/browser/server close states.
- Original driver diagnostics, supplemental failures, veto disposition,
  supplemental exit status and admission issues.
- `timingClass: instrumented-host-retention`,
  `nativeQualification: NOT_VERIFIED`, `humanAcceptance: OUTSTANDING`.

`ADMITTED_FOR_OFFLINE_VERIFICATION` requires original exit zero, expected report
identity/source metadata, completed cleanup and request state, no unexpected
late failures, and successful retention. A failed or incomplete supplemental
admission leaves every original result intact. Its `FAILED` disposition concerns
acquisition/admission; it is not a replacement product conclusion.

The actual terminal child status takes precedence over any readable artifact:

| Child status | Meaning |
|---|---|
| `0` | Original process and supplemental final admission completed; offline lossless verification is still required |
| `86` | External continuation was prevented; retain the guard stop even if original cleanup or retention also fails |
| Other positive original status | Preserved original failure |
| `1` after original zero | Supplemental late-state, identity, retention or finalization failure |
| Signal/outer timeout | Incomplete capture; retain original partial PNGs and all journal/stream prefixes |

The final receipt is fsynced under an exclusive `.pending` name, closed and then
published with an exclusive hard link as the final operation. The pending name
is retained. Final journal/receipt fsync failure cannot produce a fresh admitted
receipt and sets actual nonzero status, with `86` retaining precedence. The
coordinator must still inspect actual process and isolation outcomes. If the
outer process kills the child, no terminal receipt is expected; its absence
cannot be repaired by an earlier original `capture.json`.

The original recipe's nested `finally` blocks are unchanged. If the recipe itself
replaces an internal exception with a later cleanup exception, the wrapper does
not rewrite its control flow. It retains all observable page-operation, route,
cleanup and driver diagnostics; it does not claim access to an internal error
the original never exposes.

## Verification after private retrieval

The acquisition wrapper requires no additional hosted Python packages. After
retrieval, run the unchanged original verifier with the pinned revised inputs:

```sh
"$PYTHON_WITH_PILLOW_AND_CRYPTOGRAPHY" \
  "$RESEARCH/tools/qa/r0040/lossless_pack.py" cell \
  "$CAPTURE_PRIVATE_ORIGINAL/capture.json" \
  --pins "$RESEARCH/tools/qa/r0040/pins-revised.json"
```

The final-state receipt never certifies frame cadence, complete image inventory,
native clock alignment, effective-rate assertions, image identity, geometry,
visibility or visual acceptance. Those remain the unchanged verifier and later
owner review's responsibilities. In particular, supplemental PNG enumeration
does not replace the verifier's ordered image/capture inventory checks.

## Offline controls and central integration handoff

```sh
node --test tools/qa/hosted-native/r0040_capture_retention_controls.cjs
```

The **16** controls execute the unchanged original driver with bounded dependency
doubles. They cover complete cleanup, the original source assertion, errors
after report publication, late page crash, unexpected browser disconnection,
fatal server error, failed route fulfillment, late browser request failure,
exact report preservation, continuation veto and exit
precedence, final fsync failure, partial PNG retention on timeout, source drift,
route-before-page ordering, raw CDP identity, absence of added per-frame fsync or
PNG copies, and isolation refusal before imports. The synthetic PNGs and browser
objects are explicit source controls and provide no native rendering evidence.

An additional run can use the actual prepared helper, profile, geometry,
renderer and genuine main for the successful original-driver control:

```sh
R0040_CAPTURE_HISTORY_CONTROL="$CAPTURE_NEW_WORK/historical" \
R0040_CAPTURE_MAIN_CONTROL="$CLEAN_MAIN" \
  node --test tools/qa/hosted-native/r0040_capture_retention_controls.cjs
```

This still uses a bounded browser double. The actual `verifySources` admission
was separately exercised against complete prepared inputs, then source/receipt
drift, failed/timed-out preparation, incomplete stages, a wrong cell and an
options override. Its private receipt must remain distinct from native results.

The registry includes `hosted-native-r0040-capture-retention-controls` with argv
`node --test --test-reporter=tap tools/qa/hosted-native/r0040_capture_retention_controls.cjs`,
protocol `auto` (16 TAP cases), and `covers` containing that control file.
The ordinary offline command's complete executed input closure is:

```text
tools/qa/hosted-native/r0040_capture_retention_controls.cjs
tools/qa/hosted-native/retain_r0040_capture.cjs
tools/qa/hosted-native/retain_r0040.cjs
tools/qa/hosted-native/retention-pins.json
tools/qa/r0040/capture.cjs
tests/r0002-ordinary.json
```

The native CLI additionally consumes `r0040_capture_prepare.py`, the preflight
manifest, actual preparation/isolation receipts and the manifest-bound prepared
sources. Its role is documented here. Selected inputs have no duplicate
module/exclusion classifications; the capture driver's former native-recipe
exclusion is replaced by its executed input role above. Its native CLI and
unchanged verification requirements remain documented here. The separate
preparation command and complete closure are registered too. Central wiring is
in [LANES.md](LANES.md): it requires actual child exit zero plus the original and
final reports and preserves `ADMITTED_FOR_OFFLINE_VERIFICATION` separately from
the unchanged offline verifier. It does not modify common source preparation.
