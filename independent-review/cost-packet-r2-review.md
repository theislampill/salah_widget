The revised passive cost packet is **NOT ADMITTED for acquisition**. All 44 acquisition inputs and nine control pins match request `033ade0eadd7a2f61b06e65e6613c4022686ea90451a37b59c99663fa4af76fe`. Product integrated-r3 remains frozen; this return grants no browser lease or cost PASS.

Four narrow findings remain:

1. **Cleanup can fail while an owner passes.** `analyse_cost_v2.py:88` checks `browserClosed` but not stopped Playwright, verified owned cleanup or remaining identities. The valid synthetic batch with failed cleanup still returns owner PASS. Require all cleanup facts before numeric verdicts and make batch/exit disposition agree.
2. **Process history is overwritten.** `run_cost_v2.py:190,206,214` retains only the latest descendant snapshot. A previously seen process can disappear from that tree while remaining alive. Keep the cumulative PID/create-time/executable map and resolve those exact identities during bounded cleanup. No real orphan or process operation was observed here.
3. **Slow end-crossing calls are censored.** `analyse_cost_v2.py:133` includes only calls that finish inside the five-second interval. A synthetic final B call of 1.0 ms is excluded while A's 0.1 ms call is kept; all four rounds then pass despite a start-owned p95 delta of 0.9 ms against the 0.25 ms allowance. Include full duration for every actual call starting within the exact interval; retain the 250 ms end-readback cap and crossing diagnostics.
4. **Noise can become a definitive failure.** `analyse_cost_v2.py:159` chooses FAIL before unexplained same-side spread. One noisy B round produces 0.9 ms spread and FAIL. The adopted protocol requires INCOMPLETE pending explanation. Preserve descriptive breaches and the one explained-repeat ceiling; a stable repeatable breach must still fail.

Root's three proposed repairs address findings 1–3 conceptually. Add finding 4 in the same disposable tooling repair. Changed bytes still need exact targeted verification before admission.

The earlier repairs are supported: paired comparisons catch the prior pooling failure; runtime/input/raw/served custody checks, fixed fonts and fail-closed network, finite deadlines, readiness-before-warmup state matching, expanded retained-root/source ownership, RAF receiver preservation and owner-aware observation uncertainty are present. The original budgets and startup/steady separation remain unchanged.

Independent checks: all 53 pins match; 13 supplied offline controls and recorder/API adapter controls pass; 11 script parts, 114 insertions and 52 function occurrences have parsed source/overlay and exact insertion-removal checks. The pinned Root host log reports 48/48 tests with the real recorder and inserted scopes. These checks do not establish native performance or heap-wide absence of leaks.

Synthetic finding evidence: `cost-packet-r2-offline-controls.json` SHA `b9876ae33311c8b72f4894128bcb85cf03d070f3cc429ba8ae05017f3e3fcfba`; `cost-packet-r2-noise-control.json` SHA `59417b6d221999388a7b2b251d4fbea19a4a1a47d0ef681b0644b96646ce5e47`.

Next: preserve r2, repair only the named disposable tooling and targeted controls, and return revised pins. No product mutation, browser run, process enumeration/termination or native cost sample was performed by this reviewer. S1, uncovered startup costs, sparse owners and whole structural/preservation qualification remain open.
