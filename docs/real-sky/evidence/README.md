# Candidate evidence index

These observations bind runtime tree
`9f7146f0735bb5d999bada4680ca15393cf3b9457c66ff6ce32855c54134bb7a`.
They support a **PARTIAL Draft candidate**, not merge, release, or universal
platform/visual qualification. See [the ledger](../DAG_LEDGER.json) and
[qualification decisions](../QUALIFICATION.md).

`MANIFEST.json` records each retained artifact's SHA-256, original byte count and
stored byte count. Large logs/JSON/profiles are losslessly gzip-compressed with a
zero timestamp; `originalSha256` verifies decompression. It authenticates the
stored observations, not their correctness. `README.md` and the manifest itself
are explanatory/index files outside that payload inventory. Paths under the
manifest's `source` field describe the local acquisition workspace, not a second
product tree. Platform record references point to the exact stored raw artifact,
including its gzip hash where applicable.

| Evidence | Scope and disposition |
|---|---|
| `intake.json`, `archive-recheck.log` | ZIP CRC and manifests/source inventories; source/main reconciliation |
| `runtime-identity.json`, `build.json`, `final-audit.json` | Exact served bytes, two deterministic builds, final source/evidence checks |
| `environment.json` | Python, Node and explicitly selected browser executables |
| `integration.tap`, `candidate-tool-tests.log` | 109 JS and 16 Python candidate controls pass |
| `archive-tool-tests.log` | 22 historical handoff/identity/qualification tool tests pass; not current product evidence |
| `native/` | 881 pass, eight historical comparison failures, four TODOs, five explicit removed-producer exclusions |
| `science/` | Node 22.16: 305 pass; Python: 116 pass, one existing seal-fixture skip; immutable source unchanged |
| `mutations/` | Six isolated lifecycle/asset mutants detected |
| `performance/`, `sandbox/` | Final Chromium sandbox-enabled five-trial conditions, material/composition probes and actual-entry command receipts. All 20 candidate trials pass 250 ms limits (148.6 ms heartbeat, 106.8 ms dialog maxima). |
| `chromium/` | Combined-runtime scenes, seasonal matrix, lifecycle, source/metadata controls, numerical oracles, profile, resources, rates, smoke and real-time motion observations. Acquired before explicitly enabling the process sandbox. |
| `firefox/`, `webkit-scenes/`, `webkit-lifecycle/` | Explicit-engine scene, lifecycle and CP9 native-control observations |
| `platform/`, `platform-records.json` | Actual HTTP and local offline-file entries in all three engines; controlled fixtures and separate unmodified live providers are distinguished. Chromium records are from the final sandbox-enabled run. |
| `platform-acceptance.json` | Fail-closed join: PARTIAL, prerequisites/review pending and 13 incomplete platform checks |
| `pixels/`, `sandbox/composition/cloud-joined.png` | Scene crops, live motion start/end/video, actual-entry crops and full-frame composition |
| `diagnostics/` | Preserved encoding/rate/collector RED tests, first performance miss, Node 24 oracle failure, WebKit Blob-worker routing failure and Chromium BFCache test-wait failure |

`diagnostics/performance-before-explicit-sandbox.json` preserves the earlier
isolated trial rather than silently replacing its launch scope. The final
Chromium records include `chromiumSandboxRequested: true` and the actual relevant
command-line flag list (`securityFlags: []`). Firefox/WebKit have their own
engine identity; no silent Chromium substitution occurred.

The WebKit lifecycle RED record was interrupted after repeated worker-startup
failures and retains its RUNNING envelope with completed failing cases. A
catch-all test route had aborted local Blob-worker URLs. The final four-line
route correction allows local Blob/data requests and all 19 original cases pass.
No broader product or harness rewrite is attributed to that result.

The early native runner's `scope` string incorrectly says the archive-pinned
historical control commits are main ancestors. They are not. The corrected
runner and qualification document state the actual scope; the raw outcomes are
unchanged. Eight comparisons remain FAIL rather than being excluded to obtain
green. Node 24's original-archive numerical failure also remains visible.

The Chromium/Firefox lifecycle invalid-input case exposed two non-finite prayer
diagnostics through the browser protocol. The original report bytes are retained
as `diagnostics/*-lifecycle-original.raw.txt.gz`. The structured lifecycle reports
represent those values as `null` plus their original JSON pointers and `nan`
labels in `serialization`; no assertion, measurement or outcome changed. The
report writer now uses this strict-JSON representation for future runs. This is
a serialization of the recorded observations, not a new browser execution.

## Commands and environment

Commands execute from the repository root. The receipts retain the full local
argv, output and exit code. Qualification used Node **22.16.0**, Python **3.11.9**,
Playwright **1.57.0**, NumPy **2.3.5**, and Pillow **12.2.0**. The official Windows
Node ZIP SHA-256 was
`21c2d9735c80b8f86dab19305aa6a9f6f59bbc808f68de3eef09d5832e3bfbbd`,
verified against the official SHASUMS. Explicit browser versions are Chromium
148.0.7778.96, Firefox 150.0.2 and Windows-host Playwright WebKit 26.0.

The following reproduce the executed checks; receipts retain the exact
invocations. Output paths are shortened to `$out`.
In PowerShell, `$out` is an external evidence directory; put Node 22.16.0 first
on PATH and set `PYTHONUTF8=1`. Select `SALAH_BROWSER` and its existing
`SALAH_BROWSER_EXECUTABLE` for each engine; never silently substitute one.

```text
python tools/build_native.py
python tools/build_native.py
node --test --test-reporter=tap --test-concurrency=1 <all tests/real-sky/*.test.mjs files>
python -B -m unittest discover -s tests/real-sky -p *_test.py
python tools/cp9/run_native_regressions.py --output $out/native
python tools/cp9/run_scientific_regressions.py --output $out/science
python tools/cp9/native_lifecycle_mutations.py --output $out/mutations
python tools/cp9/qualify_candidate.py --output $out/chromium --groups oracles profile memory material composition presentation motion live-watch scenes seasonal lifecycle native-controls controls responsiveness rates smoke platform
python tools/cp9/qualify_candidate.py --output $out/firefox --groups scenes lifecycle native-controls
python tools/cp9/qualify_candidate.py --output $out/webkit --groups scenes lifecycle native-controls
python tools/cp9/platform_widget_check.py --output $out/firefox-platform
python tools/cp9/platform_widget_check.py --output $out/webkit-platform
python tools/cp9/qualify_candidate.py --output $out/final-sandbox --groups performance platform material composition
```

The integration command's file list is expanded by `qualify_candidate.py` when
using `--groups integration`; PowerShell does not reliably expand the literal
glob for Node. The native runner emits all 28 exact subcommands in its receipt.
Scientific tests/builders run in a disposable copy of the retained oracle.
Loaded performance uses five trials per condition and runs with **no concurrent
browser or solver campaign**. Baseline controls are reported separately.

`qualify_candidate.py` returns 2 when its executable commands return zero but
mandatory qualification remains incomplete, and 1 on an execution failure.
It never infers DAG closure from a successful launch or command. The native
historical comparison suite returns nonzero for the retained failures. The
platform collector also remains PARTIAL until all observations, prerequisite
closure and independent review bind the same final runtime.

To inspect a compressed observation without modifying it:

```python
import gzip, hashlib, json
from pathlib import Path
root = Path("docs/real-sky/evidence")
manifest = json.loads((root / "MANIFEST.json").read_text())
for row in manifest["files"]:
    data = (root / row["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row["sha256"]
    original = gzip.decompress(data) if row["gzip"] else data
    assert hashlib.sha256(original).hexdigest() == row["originalSha256"]
```

Counts are correlated checks. Stored pixels and videos support only their
observed scenes and timing; they do not establish every optical, accessibility,
device, scientific calibration or visual-panel gate.
