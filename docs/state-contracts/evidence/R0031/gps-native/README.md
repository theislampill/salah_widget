# R0031 settings GPS native evidence (owner decision D-31-3 = A; R31-07 / R31-13 settings cells)

Recipe: `node tools/qa/run_r0031_native.cjs --cells gps --root <tree> --out <fresh dir> --engines <engine>
[--variants never,reject,absent,granted,denied,prompt] [--reset 0] --playwright <global playwright package>`.
Global Playwright 1.60.0; zone Asia/Riyadh; clock installed (running) at 2026-09-07T09:00Z; geolocation stubbed
(one fix 51.5/-0.12, 20 m); `navigator.permissions.query` overridden per variant; GeoJS, ipinfo, Nominatim,
Zippopotam, BigDataCloud and Aladhan fulfilled from fixtures; Open-Meteo, RainViewer and fonts answered 503; anything
else aborted. WebKit was run in four shorter invocations (tool time limit); the cells are the same.

| Tree | Engine | gps-never | gps-reject | gps-absent | gps-granted | gps-denied | gps-prompt | reset-gps-never |
|---|---|---|---|---|---|---|---|---|
| candidate | Chromium 148 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| candidate | Firefox 150 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| candidate | WebKit 26.4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| main `cd0d53c4` | Chromium | **FAIL** | PASS | PASS | PASS | PASS | PASS | **FAIL** |
| main `cd0d53c4` | Firefox | **FAIL** | – | – | PASS | – | – | **FAIL** |
| main `cd0d53c4` | WebKit | **FAIL** | – | – | – | – | – | **FAIL** |

Each candidate cell: form 51.50000/-0.12000, status sequence exactly "Requesting browser location…" then one
"Browser position · accuracy 20 m · …" (sampled every 100 ms for 3 s; no flicker; with the API absent the request
status is already replaced at the first sample), `qaState().config.geolocationPermissionState` "unknown" for
never/reject/absent and the resolved state otherwise, one geolocation call. reset-gps-never: the pending Reset ends
when the fix is adopted and, after close and the held detection's release, the fix is the configuration and saved.
On main the never-settling query keeps the fix unpublished and the Reset pending ("–" = not run on main).

R0030 recipe on the candidate (`r0030-*.json`; `tools/qa/run_r0030_native.cjs --main <main tree>`): all eight
behaviour cells PASS in each engine. Pixel control (325×530 card; healthy scenes closed, open, completed Reset,
session-only warning): Firefox 0 differing pixels everywhere (main-vs-main and main-vs-candidate). Chromium and
WebKit show differences of max channel delta 1–2 that also appear between two main runs (`r0030-r30-mm.json` serves
main in both positions: reset-complete 2 px Δ1 main-vs-main); one earlier Chromium candidate run showed 53 px Δ5 in
session-only that did not recur in two later candidate runs. Read as within run-to-run noise; this is not an
identity claim. The changed function runs only on a pin click, which none of the pixel scenes performs.
