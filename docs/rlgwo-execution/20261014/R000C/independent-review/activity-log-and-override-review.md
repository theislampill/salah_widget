# Independent native inactivity finding and bounded override diagnostic

The new native log establishes an inactive refresh-driver transition for the exact headed fixture at startup. One separately bound 20-second diagnostic using only the documented top-level activity preference is justified. This is not C16 qualification or permission to replace the failed watches.

## Completed diagnostic

`../native/firefox-headed-activity-probe/` used the unchanged reviewed visibility probe and original reduced input. The separate logging manifest is SHA256 `34af56eeb8b999438bd8fb4fcb5fb1ae7af097b6ddd6ac35b66ae8c42f385bc4`. I independently verified all eight emitted log files, including zero-byte children, against its byte counts and hashes. Probe/driver/packet/source/runtime/binary identities remain consistent. The acquisition correctly retains FAIL with no qualification checks or watches.

The decisive original is `../native-activity-logs/refresh.log.child-6.moz_log`, SHA256 `5dd6dfccf72db98960c8c6301774c29683387de0befeec06ee6de4655712835d`. At lines 84–92, process 33140's Main Thread records the exact fixture URL from the native receipt, followed by BrowsingContext `20135295b00` active 0 and BrowserChild `20135241800` visible **and preserving layers**. Refresh driver `20135098400` is then removed from timer `2013b66ed00` and added to `2013502c3c0`, which is explicitly logged as an inactive timer. A second exact-URL ComputeActiveness record reports prior state 0.

This is a contiguous, source-supported native transition. The visible/preserving-layers branch returns BrowsingContext activeness, false here; it does not take the Playwright-patched invisible-BrowserChild branch whose forced-active return required caution in the prereview. The subsequent state and labeled timer transfer corroborate the result, rather than treating the first logged old-state integer as a return value.

The child log ends in a truncated buffered startup line. It does not prove a complete native tick series or activity throughout the later 20 seconds. The passive trace separately has 21 visible/unpaused samples and observed render times 602, 1376, 3226, 7233 and 15482 ms. The known inactive-timer mechanism is consistent with those gaps, but this is not an exact callback-to-frame association or proof of the cause of earlier headless missing pixels.

The original native video is SHA256 `78c0cf54086c184cceab7c0cca5e687e0b31d83ac666f98aa0479ea3580e6272`, 543 frames through 21.68 seconds. I independently decoded all frame hashes and timestamps and reconciled them against the retained index. Every frame is nominated low-information; independently extracted originals at 10.00 and 21.68 seconds are visibly blank. No healthy pixel or watch claim is made.

## Concrete successor inspected

I read `../activity_override_probe.py`, SHA256 `af609107a12d81ee3cdd2c93a3d211412758bf44273b07877bd745f0c1a7f98e`. It pins the existing visibility probe, wraps the existing browser-options provider and adds exactly `firefox_user_prefs = {"layout.testing.top-level-always-active": true}` to the fresh isolated Firefox launch. It rejects a different engine or pre-existing preference dictionary. It then executes the same probe, including original READY, 21 passive reads over 20 host seconds and deliberate early termination. Product, browser binary, case input, reduced-motion preference, clock and recorder are unchanged. This is an explicit test-profile activity override, not a claim that the headed environment retains all default settings.

The matched Firefox source documents this preference for testing automation. It targets precisely the observed native activity criterion and returns true before the inactive BrowsingContext/preserving-layers result. It does not itself modify the CSS reduced-motion preference or widget weather logic. The proposed `sync` logging modifier addresses the observed buffered-log truncation; it is an observation change with potential timing overhead, not acceptance evidence.

Run this one diagnostic with separately recorded actual subprocess `MOZ_LOG` and `MOZ_LOG_FILE` values, retaining every emitted log and the complete native original. The wrapper's descriptive `nativeLogging` string is intended configuration, not environment readback by itself. Keep all prior inputs, logs, blank originals and failed intervals intact.

The diagnostic succeeds only if the exact fixture's native log records the preference branch, actual last-render progression resumes, and original native pixels show a readable complete card. A preference value alone is not success. Even a successful diagnostic is shorter than the required control and earns zero C16 credit. A subsequent candidate must disclose the isolated activity override, preserve genuine reduced-motion behavior and satisfy the complete original predeclared interval without tail selection. That qualification decision remains separate. No general preference sweep, new recording mode or full case replay is justified here.

Machine reconciliation: `activity-log-probe-check.json`; original independent extractions: `firefox-headed-activity-probe/R000C-night-reduced/`.
