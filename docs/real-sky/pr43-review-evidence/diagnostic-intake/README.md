# Independent PR43 review bundle

Start with `PR43_Independent_Review.md`. Send `PR43_Revision_Prompt.txt` plus this bundle to the DAG execution coordinator.

The review requests changes for a P1 script-delivery/core-boot coupling and a P2 late-font layout cache race. It does not claim a full runtime rerun or a repair of the existing lunar atmospheric spotlight.

## Included evidence

- `probe-results.json`, `probe-run.log`: independently executed Chromium 144.0.7559.96 diagnostics.
- `probes/browser_probes.py`: reproducible source-excerpt / structural browser tests.
- `source-excerpts/`: manually transcribed native functions from the connected reviewed source; comments omitted.
- `localhost-probe-environment-limit.log`: the initial local-HTTP navigation failed under the environment's administrator policy. The final diagnostics use in-memory documents instead, not a policy bypass.
- `MANIFEST.json`: checksums of bundle contents, excluding the manifest itself.

No font files, owner browser data, credentials, V5 asset archive or full repository checkout are included.

## Run

Use an isolated test environment with Python, Playwright, an installed Chromium/Chrome executable, and an installed controlled test font:

```sh
python probes/browser_probes.py --chromium /path/to/chromium --font-local "DejaVu Sans Mono"
```

On the real checkout, bind the functions directly to authored source:

```sh
python probes/browser_probes.py --native-source /path/to/salah_widget/src/native/index.html --chromium /path/to/chromium --font-local "Courier New"
```

The font argument names an already installed font; there is no download or font installation. The test registers it under the target family solely inside its disposable document. It deliberately does not measure real Fraunces rendering.

The expected assertions describe the **reviewed defective behaviour**, including the negative cache-invalidation control. Corrected code may intentionally make those diagnostic assertions fail. Preserve original receipts and author proper repaired-consumer regression tests; do not edit the evidence to manufacture a green result.

The script rewrites `probe-results.json` and `probe-run.log` only when the caller redirects output there. Run copies when preserving these retained results. The structural loading test uses synthetic filler and deterministic boundary stubs; it is not a cold-network performance benchmark or complete widget rendering.
