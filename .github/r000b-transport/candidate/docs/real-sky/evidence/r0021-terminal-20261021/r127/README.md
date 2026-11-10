# r127 — attempt-owned file asset transport

**The demonstrated r122 product race is repaired and independently qualified at its affected scope. R0021 is not yet merge-qualified.** The original [r122 failure](../r122/README.md) is retained unchanged.

`moon/src/moon-native.mjs` now owns each file chunk callback on its exact loading script. The callback requires that script to be `document.currentScript`, still be the active script, and still belong to the same live worker. Cancellation removes the callback, script, listener and queued continuation. Generated chunks in `tools/build_moon.py` dispatch through their own current script. A dispatched old script cannot call a newly installed global callback or contaminate a retry. Ordering and duplicate rejection remain explicit; worker decoding, compressed digest, byte counts and current-source validation are unchanged.

Three actual generated-script controls failed before the correction: execution after failed-worker cleanup, an old chunk executing during a new retry, and disposal with a queued continuation. All pass afterward, including legitimate current chunks and complete final refinement. The affected host suite passes 58 tests; build guards pass eight and asset checks pass two. Both canonical builds are byte-identical. All 68 chunk payloads are unchanged apart from the dispatch wrapper; 200 protected scientific/source pins match. Both generated entry artifacts are regenerated.

The existing native file-index transport was exercised once per engine with one malformed base64 payload delivered to the real worker decoder. Chromium 148 and Firefox 150 both retained current initial content after the real `atob` failure, terminated failed worker ownership, cleared pending work and reached current admitted final refinement after one explicit retry. Final projected maxima are 0.07717132568359375 and 0.0867919921875 respectively, below the unchanged 0.5 gate, with zero unsettled receivers and no unexpected page errors. Original failure/final card pixels were independently inspected. These file-entry checks did not enable settings controls and do not qualify S1, callback cost or continuous presentation.

- [Source/build/method review](independent-review/file-transport-r127-source-preflight-review-r1.json)
- [Native result and pixel review](independent-review/file-transport-r127-native-result-review-r1.json)
- [Publication manifest and original/projected hashes](PUBLICATION.json)
- [Chromium result](native/file-atob-r127/chromium/results.json), [Firefox result](native/file-atob-r127/firefox/results.json)

Runtime: `1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b` (142 files). Predecessor runtime: `3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821`; 72 runtime paths change, including 68 chunk wrappers. HTTP scientific data and numerical/appearance contracts are preserved.

Reproduce source controls with `node --test moon/tests/host.test.cjs`, `python tests/real-sky/moon_build_guard_test.py`, and `python moon/tests/test_build.py`. Native methods and commands are included beneath this directory; `${WORK_ROOT}`, `${REPO_ROOT}`, `${QA_TOOLCHAIN}`, `${BROWSER_CACHE}`, `${TOOL_CACHE}`, `${STDLIB_PYTHON}` and `${SYSTEM_ROOT}` follow [the existing path roles](../NATIVE_PATH_ROLES.md). The additional `${TEST_TEMP}` role denotes temporary test-directory provenance in retained build-guard logs; it is neither a published directory nor a runnable path. Original file hashes bind the retained unprojected evidence. Personal profiles and credentials are excluded.
