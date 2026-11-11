# Independent review: R0007 font gate, candidate a71d7df0 (tree fda7f538)
Model: Sonnet 5.5 (claude-sonnet-5-5)

**Verdict: PASS_WITH_FINDINGS** for source, generated outputs, tests and scope. The Firefox pixel claim (blank removed) is NOT independently confirmed: my browser method could not discriminate.

## 1 Identity and scope
- HEAD a71d7df097db029a90518491e2ccc15c6307e13a, tree fda7f53837c1db96261a042b37e87d8e505ae154. Confirmed.
- `git diff --stat 1e3610d9 a71d7df0`: 36 files. 24 paths are on main since merge-base eebba178 (.github workflows, tools/qualification/*, smoke.html, widget-fixture.html, r0017-smoke-icon.svg ...). The other 12 are all explained by B-E: src/native/index.html, index.html, offline.html, moon/BUILD.json, tests/native-script-contract.js, tests/r0007-font-gate.test.cjs, tests/r0007-font-use.test.cjs, tests/r0017-transport.cjs, tests/rlgwo/R0007-native-request.json, tests/test_r0007_font_ingress.py, tools/cp9/r0007_font_ingress.py, docs/state-contracts/R0007.md. No unexplained path.
- v1/ untouched; `python tools/verify_v1.py` -> PASS: frozen V1 payload and anchored manifest.
- Whole src/native/index.html diff read (46 lines): only the font changes (link id, two custom-property stacks, `html.webfonts body`, date dialog to var(--font-*), WEBFONT_FACES/requestWebfonts block). Prayer-selector code untouched.

## 2 Source gate
- Race: the link's inline onload sets media=all before the later addEventListener handler; if load already happened, `link.media==="all"` triggers at once; `_webfontsRequested` guards double calls. Stylesheet never loads -> nothing requested, fallback stays. `document.fonts` missing or load() throwing -> returns, fallback. Rejected/empty set -> never activates, no retry.
- Every font-family in CSS: Inter/Fraunces named only in `html.webfonts body`; others are system-ui, monospace or var(--font-*). JS: only canvas `ctx.font` using getComputedStyle(cn).fontFamily (resolved; follows the gate); cnFontChanged resets the fit cache on activation. No inline family styles.
- "No visible UI uses Inter 500": true by grep. The only weight 500 is `.left .until-time` (monospace). Inter-family weights are 400 (inherited), 600 (.p b, .tm, dt, .date-unavailable, .staletag), 700 (`.p.on b`, resolves to the 600 face as before). Fraunces 600 for .cn/.nt/.until-prayer/dialog h2. The 3 requested faces cover them.
- Settled look equals old CSS (same families/stacks; computed style confirmed below).
- Notes: (a) users with Inter/Fraunces installed locally and no Google CSS (offline/blocked) previously got the local font, now system-ui/Georgia. (b) Date dialog fallback stack is now the body stack (adds -apple-system/"Segoe UI"; heading Georgia,"Times New Roman",serif) instead of Inter,system-ui,sans-serif / Fraunces,Georgia,serif: visible only before activation or if fonts fail. (c) load() requests only subsets covering U+0020; non-Latin glyphs still load on demand under the block period (doc admits this).

## 3 Generated outputs
`python tools/build_native.py` completed (stage complete-native-and-moon, indexSha256 5a200d9a...); `git status --porcelain` empty afterwards: byte-for-byte reproducible. sha256(src/native/index.html)=e059305e..., sha256(index.html)=5a200d9a..., matching the rebound test literals.

## 4 Tests
- tests/r0007-font-gate.test.cjs at candidate: 5 pass / 0 fail. Against 1e3610d9 source (temporary detached worktree, removed): 0 pass / 5 fail.
- It uses the REAL authored text: slices the shipped block between the "Optional web typography" and "Size the present-prayer name" markers plus the real cnFontChanged, runs it in node:vm against synthetic document/FontFaceSet/link doubles, and parses the real `<style>`. Tests ordering/policy of shipped code, not pixels or a real FontFaceSet. Not a re-implementation.
- `node --test tests/*.test.cjs tests/*.test.mjs` (28 files): candidate tests 646, pass 642, fail 0, skipped 0, todo 4. Old 1e3610d9 (gate test removed): tests 641, pass 637, fail 0.
- `node tests/r0017-transport.cjs`: PASS results at candidate (I read the tail only). `node --test tests/r0007-font-use.test.cjs`: 3 pass.
- `python -m pytest tests/test_r0007_font_ingress.py`: candidate 33 failed / 41 passed; old 32 failed / 39 passed. Failures sampled are `ModuleNotFoundError: No module named 'playwright'` (not installed here); the extra failure is a newly added test of the same kind. Behaviour of the py change is UNKNOWN from my runs.
- Changed existing assertions: font-use test replaces two literal Inter/Fraunces family checks with checks that the dialog uses var(--font-body)/var(--font-display): legitimate rebind (gate test separately forbids direct families). r0017-transport and native-script-contract: parent commit/sha and allowlist entries rebound to new digests, which I verified equal sha256 of src/native/index.html and index.html. Identity rebinds, not weakenings (hash pins prove "this exact source", not behaviour).

## 5 Browser observation (Firefox 153 headed, local server, CSS delayed ~3 s, fonts ~1.5 s, href rewritten in served copy, no request routing)
- Playwright page.screenshot cannot sample the loading window: it blocks while fonts load (gaps 6.4 s candidate, 7.2 s old, spanning the whole CSS+font period). The requested screenshot loop cannot discriminate; not reported as a pass.
- Fallback: OS-level screen capture (3-6 ms/frame) of the headed window. Not reliable: window position/occlusion varied between runs (some captured other desktop applications; discarded and deleted). I trust only one run: old page, 3429 frames, row-text measure ~2849 steady, then 35 consecutive frames with measure < 300 at t=4436-4536 ms right after the CSS was sent (4407 ms) = about a 100 ms blank; text back before fonts arrived (5942 ms). Candidate attempts were invalid (static region from before navigation), so I have NO valid candidate frame sequence. Required counts (>=4 candidate, >=3 old) NOT met.
- DOM facts, candidate (all runs): before activation `.cn` = `Georgia, "Times New Roman", serif`, `.times` = `system-ui, -apple-system, "Segoe UI", sans-serif`, html class empty; at the end `.cn` = `"Fraunces", Georgia, ...`, `.times` = `"Inter", system-ui, ...`, class `webfonts`; loaded FontFaces: Fraunces 400 700, Inter 400, Inter 600 (latin range). Console errors: none. Old page: Fraunces/Inter named from the start, class empty (consistent with the cause claim).

## 6 Docs
New R0007.md section matches what I saw and states its limits (CI not re-run, one machine, 24 intervals stay historical, no native acceptance, subset residual). "fails 5/5 before, passes 5/5 now" confirmed. "288-test affected cohort" and "Firefox 153 = CI build" UNKNOWN. No claim stronger than its evidence found.

## Findings
1. note: offline/blocked-CSS users with locally installed Inter/Fraunces lose them (src/native/index.html:20-23, 3207).
2. note: date dialog fallback stacks changed (src/native/index.html:443,446).
3. note: non-latin-subset glyphs still load later under the block period (documented).
4. should-fix (evidence): no independent proof of the visual fix; only one old-page 100 ms blank observed, none valid for candidate. Needs video or a reliable capture, not Playwright screenshots.
5. note: Python ingress tests cannot run without python playwright; UNKNOWN for tests/test_r0007_font_ingress.py and tools/cp9/r0007_font_ingress.py:308.

No blocker found. UNKNOWN: candidate no-blank in my capture, python tests, 288 cohort, CI.
