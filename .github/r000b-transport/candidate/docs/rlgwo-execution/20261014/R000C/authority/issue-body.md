<!-- salah-widget-audit-20260907:SW-012 -->
# R000C: Reject malformed weather measurements without coercing missing values into observations

**Repository-local identity:** `R000C` in `theislampill/salah_widget`; existing tracker [#12](https://github.com/theislampill/salah_widget/issues/12). The SW identifier is historical draft provenance.


Campaign draft alias: SW-012. Proposed priority P2; product defect. W007 owns value/shape admission at the weather boundary. Source age is [R000B](https://github.com/theislampill/salah_widget/issues/11), request ownership is [R0003](https://github.com/theislampill/salah_widget/issues/3), bounded lifetime is [R000D](https://github.com/theislampill/salah_widget/issues/13), and coordinate dispatch is [R001E](https://github.com/theislampill/salah_widget/issues/30). This order does not authorize implementation or publication.

## Why the current boundary is insufficient

The preserved controlled run on main `fd2972ba64225fe9d6848e92497e6d0ed20ea624` and candidate `9d9c43649748555afbe09e3ca49bc47db2d7e7bb` found two independently useful RED cases. A well-shaped success payload containing `temperature_2m:null` installed and cached `temp:0`. Separately, a deliberately malformed HTTP 500 weather-shaped body installed code 999, temperature 0, precipitation string `"Infinity"`, NaN site elevation and NaN hourly epoch, and the actual gate classified the result as thunder. The second is adversarial data, not an observed provider incident. The first does not depend on HTTP failure or exotic values.

The code uses `Math.round(cu.temperature_2m)` before distinguishing missing from numeric data; `Math.round(null)` is zero. It does not check `r.ok` before `r.json()`. Presence of `current.weather_code` is sufficient to replace current weather, the elevation uses unary coercion, and hourly arrays are accepted individually as `h[k]||[]`. Consumers then give unsupported code 999 thunder semantics because `wxClass` treats high codes broadly, and unary coercion promotes string Infinity into precipitation evidence. Cached objects bypass even the weak network shape gate.

The exact repair sites are [`loadWx` and `fetchWeather`](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/index.html#L767-L801), [`wxAt`/`syncWeather`](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/index.html#L842-L866), [weather drivers](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/index.html#L869-L898), and [precipitation consumption](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/index.html#L1432-L1451). There is no `loadWeatherCache` function in the bound source; that prior description meant `loadWx`. [Candidate acquisition](https://github.com/theislampill/salah_widget/blob/9d9c43649748555afbe09e3ca49bc47db2d7e7bb/index.html#L775-L815) retains these paths.

Counterevidence matters: HTTP 400 `{error:true,reason:"bad request"}` left `weather=null,lastWxAt=0,wxBusy=false`. This is not a claim that every provider error becomes weather. A current clear code remains clear in normal real time even if the hourly track predicts thunder; the saved advancing-mode control alone adopted forecast code 95. Preserve that distinction.

## Reproduction a cold executor can build

Re-anchor an authorized checkout with `git --no-optional-locks rev-parse --show-toplevel`, `rev-parse HEAD`, `status --short` and `diff fd2972ba64225fe9d6848e92497e6d0ed20ea624 -- index.html tests/smoke.html README.md`. Resolve incompatible changes in these exact functions before editing; preserve unrelated dirty files. The unmerged candidate is evidence, not a merge prescription.

Use an isolated source-executing fixture with `Date.now()=Date.parse("2026-09-07T21:00:00Z")`, `lat=24.47,lon=39.61,units="c",tz="UTC",SIM.wx=null,ADVANCING=false`, storage map and controlled fetch. Keep the real timezone declarations. A successful baseline response is status 200, `ok:true`, with:

```js
{
  elevation: 100,
  current: {
    time: "2026-09-07T21:00", interval: 900,
    weather_code: 95, temperature_2m: 20, apparent_temperature: 19,
    relative_humidity_2m: 90, dew_point_2m: 18,
    wind_speed_10m: 2, wind_direction_10m: 180, wind_gusts_10m: 4,
    cloud_cover: 95, precipitation: 2, is_day: 1
  },
  hourly: {
    time: ["2026-09-07T21:00", "2026-09-07T22:00"],
    temperature_2m: [20,19], weather_code: [95,3],
    wind_direction_10m: [180,180], precipitation: [2,0]
  }
}
```

Change only `current.temperature_2m` to null. Historical expected RED is `weather.temp===0` and parsed `salahwx:24.47|39.61|c` cache `w.temp===0`. A separate fixture returns `ok:false,status:500` and:

```js
{
  elevation: "invalid",
  current: {
    weather_code: 999, temperature_2m: null,
    precipitation: "Infinity"
  },
  hourly: {time:["invalid"]}
}
```

Historical observed output is `accepted:true,temp:0,rawCode:999,condition:"thunder",lastWxAt:1788814800000,siteElev:"NaN",trackEpoch:"NaN"`. Assert the installed record, persisted record, track and actual gate; checking only that a parser threw misses the consumer fault. No network provider, private script or full archive is needed for these inputs. The preserved run used Node VM doubles, not browser rendering.

## Ordered repair with explicit partial-data semantics

1. **Validate the transport envelope before mutation.** At the existing fetch boundary reject non-OK HTTP status, malformed JSON, null/non-object root and provider `error:true`. Do not set elevation, current record, track or accepted timestamp before this gate. Preserve a prior valid record only under [R000B](https://github.com/theislampill/salah_widget/issues/11) validity; rejecting a payload must not renew it. Let [R000D](https://github.com/theislampill/salah_widget/issues/13) own timeout/error cleanup, including a JSON body that never resolves.

2. **Normalize values without coercing observations.** Use a small local numeric-admission function only for the known requested fields: `null`/`undefined` remain unavailable; present measurements require `typeof value==="number" && Number.isFinite(value)`. Strings, booleans, arrays and objects are not numerical weather observations. Round temperature only after admission, so genuine numeric zero remains zero and missing temperature remains null. Finite negative temperatures are valid; do not apply a generic nonnegative rule.

   Admit an integer weather code only from the requested WMO domain `0,1,2,3,45,48,51,53,55,56,57,61,63,65,66,67,71,73,75,77,80,81,82,85,86,95,96,99`; unsupported code makes that current block unavailable rather than dispatching broad range-based thunder logic. For optional quantities, enforce their consumer bounds: humidity and cloud fractions in percent 0–100, direction 0–360, precipitation/wind/gust/visibility nonnegative, and `is_day` exactly 0 or 1 when present. Finite elevation may be negative; an invalid elevation must not replace the prior finite site value/default. Temperature, apparent temperature and dew point have no invented universal climate cutoffs.

   An absent optional measurement is null; an invalid optional measurement is also unavailable with an admission reason. It must not authorize its physical effect. Thus a valid code 95 with invalid/missing precipitation can remain a raw model code but cannot use that missing amount to preserve thunder. Do not silently replace missing precipitation with a recorded “0 mm observation.” The existing fallback behavior for decorative wind/haze is distinct from stored measurements.

3. **Carry units and source metadata as request context.** Preserve request-bound Celsius/Fahrenheit and `wind_speed_unit=ms` when installing values. If a payload advertises unit metadata contradicting the request, reject the affected block rather than relabel numbers; a missing optional units object is not grounds to reject the historical supported fixture because the request already names the units. Do not turn snowfall or other source fields into additional millimetre precipitation proof: the existing gate consumes `precipitation`. Keep the current time string, interval and captured request zone for [R000B](https://github.com/theislampill/salah_widget/issues/11); this structural owner must not invent an epoch/freshness guarantee. Calendar validity and explicit-zone conversion retain [R0008](https://github.com/theislampill/salah_widget/issues/8)'s contract via the existing shared temporal owner.

4. **Stage current and track independently, commit each valid portion deliberately.** Build normalized objects in locals. A rejected hourly block need not discard valid current conditions; a valid forecast track does not repair an invalid current block and cannot become current weather in real time. Require a nonempty time array whose converted epochs are finite, calendar-valid, strictly ordered and unambiguous under the temporal contract. Require weather-code and temperature arrays aligned to that length; do not silently truncate or sort timestamps. For optional requested arrays, absence becomes an array of nulls of that length; a present non-array or wrong-length array rejects the track, while an invalid optional element becomes null. Missing endpoint values may use the existing available-neighbor interpolation, but two null endpoints stay null, including temperature. Keep categorical codes stepped, never interpolated.

   Update `wxAt`'s final temperature rounding and wind interpolation so optional absence cannot create a recorded 0° temperature or a fabricated measured north wind. Use the existing decorative fallback only at its consumer. Do not expand the forecast range or change the established endpoint-hold behavior; time freshness for real current data is a separate issue.

5. **Use the same normalized-record rules in `loadWx`.** Preserve the existing `salahwx:lat|lon|units` key and readable `{w,ts}` envelope. Validate a cached normalized weather record before assigning it; raw cached `temp:null` is not converted to zero. Malformed JSON/record metadata becomes a cache miss without deleting unrelated storage or preventing the next fetch. Accept structurally valid legacy main/candidate cache values as structurally valid; only [R000B](https://github.com/theislampill/salah_widget/issues/11) can determine whether missing source-time metadata removes current authority. A numeric zero already saved by older coercion is indistinguishable from genuine 0°: do not invent retrospective provenance or invalidate every legitimate zero.

6. **Make the commit point owned.** [R0003](https://github.com/theislampill/salah_widget/issues/3) supplies captured coordinates, unit, zone, cache identity and attempt/generation ownership. After asynchronous parsing/validation, verify ownership before installing any portion or persisting the captured cache key. This owner must not independently read mutable global configuration at completion or create a second generation counter. Batch the admitted current record and its timestamp/metadata as one commit so a cache consumer never sees half-normalized authority.

The intended intermediate state is “parsed local candidates, live state unchanged,” followed by “owned valid current and/or valid track committed.” There is no useful partial state in which elevation becomes NaN before current validation fails.

## Controls that distinguish a repair from a stricter-looking parser

Add acquisition fixtures to [the existing smoke owner](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/tests/smoke.html), or a narrow dependency-free source fixture if the current browser harness cannot inject before startup. The file currently tests the pure gate and SIM scenes; those do not exercise fetch/cache admission. Any helper must be called by actual `fetchWeather`/`loadWx`, with an integration case proving reachability.

| Required future input | Required final-tree state |
|---|---|
| Healthy baseline; only temp changed to null, undefined, then numeric 0 | Null/absent temperature stays unavailable in state/cache/render; true 0 displays 0° |
| Negative finite Celsius and Fahrenheit temperatures | Valid values preserved; units remain request-bound |
| Malformed HTTP 500 lookalike above; normal HTTP 400 envelope | No new weather/track/elevation/accepted timestamp; busy eventually released by its owner |
| Status 200 with code 999 or string `"95"` | No unsupported authoritative current block |
| Status 200 valid code with precip `"Infinity"`, NaN, Infinity, −1, then 0 | Invalid values unavailable; no rain authority from them; true zero remains valid dry evidence |
| Current valid/hourly malformed, then current invalid/hourly valid | Valid portion survives; no forecast-as-current substitution |
| Mismatched time/value lengths; invalid/gap/unresolved-fold time; duplicate/decreasing epoch | No usable track installed; future source-age qualification cannot rely on it |
| Optional absent arrays, null endpoints, one valid interpolation neighbor | No NaN geometry/driver or null-to-zero temperature; valid neighbor behavior retained |
| Malformed cached object, then healthy fetch; valid old zero-valued cache | Cache miss recovers; genuine zero remains compatible, subject to freshness qualification |
| Old configuration response completes after new configuration | No install/persist under the new owner; stale finally cannot clear the new attempt |
| Current clear 0 plus hourly thunder 95 | Real-time remains current; ADVANCING positive control uses the forecast track |

In isolated mutation checks, restore `Math.round(null)` and require the minimal null fixture to fail; remove the HTTP gate and require the 500 fixture to fail; bypass cache normalization and require malformed cache to fail; reintroduce `h[k]||[]` and require the alignment/null-endpoint cases to fail. These are future checks, not executed results.

Use a disposable browser origin to render null temperature, genuine zero, malformed precipitation and healthy wet controls. Capture the header chip and actual `data-fx`; no `NaN°`, fabricated 0°, rain/thunder from invalid values, clipped footer or change to 325×530 layout. Preserve existing SIM weather, moon opacity and motion behavior; do not assert those from a parser result.

## Alternatives, integration and completion boundary

Checking `r.ok` alone repairs the adversarial 500 path but misses null temperature, status-200 malformed data and poisoned cache. Rejecting an entire response for every absent optional field breaks supported partial payloads and useful current weather because the historical fixture omits several requested fields. Coercing numeric strings broadens the trust boundary and recreates the Infinity path. A provider-wide schema package or generated validator adds a dependency and cross-provider obligations without helping these known consumers. The small known-field normalizer with explicit partial blocks is the chosen route.

Coordinate shared `fetchWeather`/`loadWx` edits serially with [R0003](https://github.com/theislampill/salah_widget/issues/3), [R000B](https://github.com/theislampill/salah_widget/issues/11), [R000D](https://github.com/theislampill/salah_widget/issues/13) and [R001E](https://github.com/theislampill/salah_widget/issues/30). Admission qualifies freshness under the existing relationship; it does not absorb source age or deadline ownership. No new typed edge or write domain is proposed. [README](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/README.md) needs only the exposed unavailable-value behavior; use the shared docs integrator. Builder/config units, installers and preset remain compatible; no generated artifact is expected.

Rollback normalization, cache reader and null-aware consumer changes together if a supported payload fails. Preserve unavailable values while reconciling the precise fixture; never “recover” by manufacturing measurements. Stop on incompatible request/temporal interfaces or disputed unit semantics rather than silently broadening acceptance. DONE requires final integrated RED→GREEN and controls, exact-tree review of admission/cache/consumer reachability, and an evidence comment before manual closure. Use non-closing `Implements #N`. Public repair needs matching served source and relevant UI readback; otherwise it is local and not deployed.

Supplementary preserved companion: `basis/finding-records/SW-012.json`, SHA256 `a51af5aeece94b61ff60f7f456c53f73526be7c3d7f130e73b3265dbf0e58a4b`. All GREEN, browser and mutation cases above remain future requirements.

Identity provenance: first repository-local allocation batch; existing GitHub object order was used to assign distinct monotonic hex-4 IDs. Closed/held IDs are not reused. Issue number is not implementation priority.
