# CP8.3 native regression scope

The expanded runner executes the current supplied-snapshot contracts without inventing missing Git history. Original historical/synthetic test bodies remain available; `--cp8-snapshot-only` exclusions are explicit. These exclusions are not passes.

## Applicable current runs

| Command group | Passing cases |
|---|---:|
| `native-test-glob` | 410 |
| `r0001-date-sinks` | 13 |
| `r0007-countdown` | 23 |
| `r0008-timezone` | 37 |
| `r0009-date-selection` | 22 |
| `r000f-intent` | 21 |
| `r000f-reset` | 9 |
| `r0010-preferences` | 9 |
| `r0011-storage` | 18 |
| `r0012-clipboard` | 11 |
| `r0012-effects` | 3 |
| `r0017-cloud-visibility` | 20 |
| `r0017-contract` | 35 |
| `r0017-transport` | 14 |
| `r0017-weather` | 6 |
| `r0018-appearance` | 17 |
| `r0019-date-disclosure` | 16 |
| `r001a-radio` | 8 |
| `r001d-lifecycle` | 11 |
| `r001f-deadline` | 13 |
| `r0020-clock` | 44 |
| `r0021-reveal` | 14 |
| `r0022-lunar-consumers` | 24 |
| `r0023-metadata` | 26 |
| `r0025-continuity` | 9 |
| `r0025-lifecycle` | 16 |

Total: **849 passing cases across 26 commands**. Test cases may contain multiple assertions or related fixtures; this is not a count of independent project requirements.

## Entire historical scripts not run in the qualified subset

`r0018-timetable-contrast.cjs`: Requires unsupplied historical commit fd2972ba64225fe9d6848e92497e6d0ed20ea624; current pinned-baseline preservation is checked separately.

`r0022-baseline-balance.cjs`: Requires unsupplied historical commits fd2972ba64225fe9d6848e92497e6d0ed20ea624 and 8b83df029966c203a503ab217d121c48b8ee6e8a; CP8 does not reacquire or substitute them.

## Individual cases explicitly excluded

`r0021-reveal`: SKIP_EXPLICIT ordinary held star positions remain stable across a healthy render — removed synthetic-array producer; actual catalogue sink lifecycle tested separately

`r0021-reveal`: SKIP_EXPLICIT first accepted target cannot retain the unresolved-coordinate projection — removed synthetic-array producer; actual first accepted catalogue tested separately

`r0021-reveal`: SKIP_EXPLICIT same-day explicit preview anchor correction reprojects accepted stars — removed synthetic-array producer; actual catalogue seeks tested separately

`r0021-reveal`: SKIP_EXPLICIT moon PBR shader and embedded payloads retain exact accepted bytes — unsupplied historical commit 47c0fa0c6e32618f22b43b6a18717908b0de5f5e; supplied 2057503 PBR comparison runs in native-preservation tests

`r0022-lunar-consumers`: SKIP_SUPERSEDED glints release wash with held star projection — real catalogue/physical compositor replaces synthetic arrays; see CP8 tests

`r0022-lunar-consumers`: SKIP_SUPERSEDED ordinary render refreshes star appearance while held projection stays fixed — real catalogue/physical compositor replaces synthetic arrays; see CP8 tests

`r0023-metadata`: SKIP_HISTORICAL actual older consumer degrades a saved browser position to a configured site — requires fd2972ba64225fe9d6848e92497e6d0ed20ea624

`r0023-metadata`: SKIP_HISTORICAL later preference saves preserve private origin and fix while the older state stays manual — requires fd2972ba64225fe9d6848e92497e6d0ed20ea624

`r0023-metadata`: SKIP_HISTORICAL legacy browser record remains unchanged on read and conservatively migrates on explicit save — requires fd2972ba64225fe9d6848e92497e6d0ed20ea624

`r0023-metadata`: SKIP_HISTORICAL older preference rewrite remains usable with explicitly unknown acquisition evidence — requires fd2972ba64225fe9d6848e92497e6d0ed20ea624

`r0023-metadata`: SKIP_HISTORICAL manual place and coarse saved representations preserve their established source states — requires fd2972ba64225fe9d6848e92497e6d0ed20ea624

## Four inherited TODO placeholders

R0003 join: obsolete acquisition cannot install/persist or clear successor attempt

R000D join: unresolving JSON and image bodies settle within accepted deadline

R0024 join: fresh current model eligibility remains positive while final live strong-particle permission is withheld

native/browser qualification: fixture chip/data-fx, zero-axis consumer, layout/moon/motion pixel evidence

These placeholders are left intact; no RLGWO closure credit is inferred from them. The new CP8 lifecycle/asset, actual-widget, current-pin preservation, material/foreground and calendar/settings controls have their own results.

## Fixture-only repairs

`tools/adapt_native_tests.py` deterministically applies ten reviewed test/harness-file changes from the immutable baseline. It adds the missing real lunar declaration, models the standard DOM replacement method, retains the CLOCK-only producer boundary, recognises the exact extra integration script in the wrapper and declares the historical/synthetic subset explicitly. The native application’s prayer/calendar/settings/weather/PBR owners are not changed to make these tests pass.

The original expanded failures and subsequent successful run are retained under `evidence/cp83/`. Final fresh results are in the matching external verification evidence.
