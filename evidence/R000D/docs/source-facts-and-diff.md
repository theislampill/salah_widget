# R000D documentation facts

The candidate is a focused clarification in README.md and DESIGN.md, based on
production main `06772824a159cd2bc42a1d9f79a3fb22fa46e49d`. The current main already
documents the deadlines and retry cadence; the additional text connects those
facts to partial-body stalls, admission, the actual consumer, and operation IDs.
No public setting, diagnostic field, provider promise or runtime behavior is added.

| Required fact | Existing source at the pinned main | Documentation |
| --- | --- | --- |
| Weather headers and JSON body share 10,000 ms | src/native/index.html:1325, 1332-1355, 1366 | README Weather auto-retry paragraph |
| Manifest headers/body share 10,000 ms; Image has a separate 10,000 ms | src/native/index.html:1325, 1403-1429, 1437-1456 | README Weather auto-retry paragraph |
| Approximately 20 seconds of combined radar application wait under runnable JavaScript | Same two attempts, with finishAttempt before the Image attempt | README bounded-wait qualification |
| Weather eligibility 60 seconds, radar 600 seconds, existing poll approximately 30 seconds | src/native/index.html:1362, 1393, 1434, 3444 | README retry/next-opportunity text |
| Eligible current plus hourly track permits the existing 15-minute shortcut | src/native/index.html:1361 | README retry paragraph |
| Abort is best effort; independent settlement and absolute deadline checks remain | src/native/index.html:1021-1033, 1335-1354 | README application-bound and suspended-JavaScript limits |
| Timeout cannot renew accepted weather/cache/source/receipt timestamps | src/native/index.html:1370-1387; timeout returns before admission | New README clarification |
| Expired current is unavailable; forecast and radar cannot replace current temperature | selectedWeather/weatherEligibility and current header consumer; radarPrecipNow returns zero | Existing truthfulness text and new README clarification |
| Model estimates remain distinct from observations | DESIGN owner H5/H8 policy; weatherDecision and header provenance | New README clarification; existing model policy retained |
| Diagnostic is latest attempt, guarded by owned generation/operation | src/native/index.html:1326-1328 | New DESIGN diagnostic explanation |
| received is settlement, not admission or recovered rendering | wxFetchJson finish precedes fetchWeather admission; wxRadarSample precedes radar installation | Existing and new DESIGN diagnostic explanation |
| Radar sample is unitless, no rainfall/lightning authority | src/native/index.html:1389-1401, 1459-1460 | New DESIGN diagnostic explanation |

The native receipts separately bind request arrival, delivered headers and partial
body bytes, actual monotonic deadlines, slot release, existing-poll replacement,
admitted state and rendered consumers. They use controlled synthetic provider data;
they are not provider availability or observed local precipitation claims. Normal
abort rejection is distinguished from the explicitly scoped ignored-signal case.

The exact documentation candidate must be independently reviewed and merged with
owner approval. Post-merge document bytes and unchanged runtime/public consumer
must then be read back before the final certificate or completed issue closure.
