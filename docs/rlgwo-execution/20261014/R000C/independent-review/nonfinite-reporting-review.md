# Independent reporter-only successor review

The reporter repair is justified and does not weaken the native or pixel gates. One still-uncompleted reduced-motion control may use the pinned successor. This is a decision about a bounded acquisition repair, not C16 qualification.

Reviewed at repository HEAD `7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69`, branch `codex/r000c-close-20261014`. The successor driver is `76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce`; its case packet is `268d820ff632135eb86ed92f3650b619cac71440eef2e282605d00dcd4749f67`. The prior exact host-wait version remains in `../fixture-v4/`.

`verify_nonfinite_reporting.py` independently compared both complete driver ASTs after excluding the added `math` import and the two serialization helpers. Everything else is identical, including `check`, all browser inputs, readiness, passive recovery, original boundaries and two 30-second host waits. The packet differs only in its driver digest, and every current source pin matches.

The isolated helper controls confirm that native Python NaN/+Infinity/-Infinity are written as explicit `$nativeNonFiniteNumber` tagged objects in a fresh dictionary/list tree. Finite values, null, booleans and literal strings such as `"Infinity"` remain unchanged. Original in-memory values passed to `check()` are unchanged. An injected required `raw.temp` NaN still fails the original `temperatureAdmitted` check before and after serialization. These synthetic reporter controls are explicitly separate from acquired native observations.

The failed acquisition `../native/firefox-reduced-host-wait/` retains its input, FAIL results, original 1.560-second partial video and traceback. Its recorded file sizes and hashes match the inventory; no receipt or initial observation file exists. It reached neither required watch and receives zero native/pixel/watch credit. The lost NaN path is unknown. Neither this reporting exception nor the successful serialization control establishes a product, CSS, renderer or capture cause.

The next acquisition must retain the same reduced case, headed native video, boundary observation, host waits, ordinary weather retry, actual 1× clock, assertions and predeclared intervals. Keep every earlier failed watch and the aborted attempt separately visible. Enumerate any successor tagged field paths without treating tags as valid weather measurements or substituting expected null/zero values. C16 remains pending actual readable reduced-motion evidence; C18 delivery/closure remains pending.

Machine evidence: `nonfinite-reporting-check.json`, with derived synthetic controls in `nonfinite-serialized-control.json` and `nonfinite-required-field-control.json`.
