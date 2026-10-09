# Exact bounded native check for R001A

Prepared fixture: `native-radio-fixture.cjs`. It reuses the current production builder and both original `r001a-radio.cjs` mutations. Healthy radio/default-action/update functions and original expectations are unchanged. It contains only per-document storage, a null coarse-location response, snapshot instrumentation and a blank preview response to prevent Moon terrain work. It never copies, installs, submits owner locations or clears owner storage. No browser has been run by F.

Primary command, after creating a fresh owned evidence directory:

```powershell
& 'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe' 'C:\Users\theis\Documents\Codex\pr42-rlgwo-closure-20261008\workers\F\native-radio-fixture.cjs' '<new-primary-owned-evidence-directory>'
```

The server prints exact `healthy`, `arrows` and `tabindex` URLs. Use the primary's existing native browser driver in an isolated context. No solver is served. Capture `window.__radioFixture.snapshot()` before and after each native key. The snapshot retains checked/active/tabIndex/focus, revision, emitted snippet/hash/allow, viewport, fonts, browser and source identity.

Required healthy sequence at 375×800 and one desktop viewport:

1. Initial portable mode has exactly one checked, active and `tabIndex=0` radio. The other is unchecked/inactive/−1. Find the preceding enabled visible tab stop in DOM order, focus it, then press **native Tab**: focus enters the selected portable radio. The local hash flag is absent and preview geolocation delegation is absent.
2. From portable press **ArrowRight → local**, **ArrowRight → portable**, **ArrowLeft → local**, **ArrowUp → portable**, **ArrowDown → local**. Each step focuses its selected radio, keeps exactly one selected tab stop, updates the actual `embedMode`, sets/removes `local=1` in both emitted code and preview hash, sets/removes `allow=geolocation`, and advances the preview revision exactly once. Wrapping is required.
3. Press native **Tab** to leave the group; native **Shift+Tab** returns to the selected local radio. Both keys preserve mode, hashes and revision. Press native **Enter**, then native **Space** (including keyup): each activation updates the existing application exactly once without an extra keydown update. The VM explicitly cannot prove these default actions.
4. Click the other radio and call the existing `setMode` separately; each leaves checked/active/tabIndex/output synchronized. Temporarily disable one button, call `setMode` for it and press an arrow on the enabled radio: selection remains on the enabled one. With neither enabled there is no checked or tabbable radio and an arrow is safe. These are disposable DOM controls, not source changes.
5. Reopen a healthy document and enter the group with native Tab. Capture a crop of `.modebtns` while the selected button matches `:focus-visible`; inspect the actual 2px focus outline at both viewports. Capture full builder bounds too. Record the snippet's current 325×530 dimensions, as preserved by the original R001A test; this check does not adjudicate the separately authorized production iframe wrapper.

Two native negative controls, fresh documents using the server's mutant URLs:

- `arrows`: the identical first **ArrowRight** assertion must fail because selection/focus/output stay portable. A script/bootstrap exception or missing terminal is not detection.
- `tabindex`: the identical first **ArrowRight** assertion must fail because the checked local radio retains `tabIndex=-1` while portable retains `0`. All other healthy assertions remain unchanged; do not omit the tabIndex assertion.

The corresponding fresh VM results already passed 8/8 cases and caught both mutants with the original behavior assertion. Native keys plus the two focus crops are the missing R001A proof. The contained preview verifies its emitted URL/allow/snippet, not the separate widget's rendered sky.
